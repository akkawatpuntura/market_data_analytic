"""Small wrapper around the OpenRouter chat API with optional web search."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "asset" / "config" / "openrouter_config.json"


@dataclass
class OpenRouterConfig:
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openai/gpt-5"
    referer: Optional[str] = None
    title: Optional[str] = None
    web_search: Optional[Dict[str, Any]] = None

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "OpenRouterConfig":
        if not path.exists():
            raise FileNotFoundError(f"OpenRouter config not found at {path}")
        data = json.loads(path.read_text())
        return cls(
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", cls.base_url),
            model=data.get("model", cls.model),
            referer=data.get("referer"),
            title=data.get("title"),
            web_search=data.get("web_search"),
        )


class OpenRouterClient:
    def __init__(self, config: Optional[OpenRouterConfig] = None) -> None:
        self.config = config or OpenRouterConfig.load()
        self.session = requests.Session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        # OpenRouter recommends these headers for attribution.
        if self.config.referer:
            headers["HTTP-Referer"] = self.config.referer
        if self.config.title:
            headers["X-Title"] = self.config.title

        self.session.headers.update(headers)

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        web_search: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call OpenRouter chat completions and parse the response defensively."""
        url = f"{self.config.base_url}/chat/completions"

        normalized_messages: List[Dict[str, str]] = []
        for message in messages:
            normalized_messages.append(
                {
                    "role": message.get("role", "user"),
                    "content": message.get("content", ""),
                }
            )

        effective_web_search = web_search if web_search is not None else self.config.web_search

        def build_payload(*, messages_payload=None, input_payload=None, prompt_payload=None) -> Dict[str, Any]:
            """Create the request body while reusing shared knobs like max tokens."""
            body: Dict[str, Any] = {
                "model": self.config.model,
                "temperature": temperature,
            }
            if messages_payload is not None:
                body["messages"] = messages_payload
            if input_payload is not None:
                body["input"] = input_payload
            if prompt_payload is not None:
                body["prompt"] = prompt_payload
            if max_tokens is not None:
                body["max_tokens"] = max_tokens
            if effective_web_search:
                body.setdefault("extra_body", {})["web_search"] = effective_web_search
            return body

        payload = build_payload(messages_payload=normalized_messages)
        resp = self.session.post(url, data=json.dumps(payload), timeout=60)
        try:
            data = resp.json()
        except Exception:
            data = None

        if resp.status_code >= 400:
            alt_input = "\n".join(f"{m['role']}: {m['content']}" for m in normalized_messages)
            alt_payload = build_payload(input_payload=alt_input)
            alt_resp = self.session.post(url, data=json.dumps(alt_payload), timeout=60)
            try:
                alt_data = alt_resp.json()
            except Exception:
                alt_data = None

            if alt_resp.status_code >= 400:
                alt2_url = f"{self.config.base_url}/completions"
                alt2_payload = build_payload(prompt_payload=alt_input)
                alt2_resp = self.session.post(alt2_url, data=json.dumps(alt2_payload), timeout=60)
                try:
                    alt2_data = alt2_resp.json()
                except Exception:
                    alt2_data = None

                texts = [
                    f"chat/completions(messages) -> {resp.status_code}: {getattr(data, 'text', resp.text) if data is None else json.dumps(data)}",
                    f"chat/completions(input) -> {alt_resp.status_code}: {getattr(alt_data, 'text', alt_resp.text) if alt_data is None else json.dumps(alt_data)}",
                    f"completions(prompt) -> {alt2_resp.status_code}: {getattr(alt2_data, 'text', alt2_resp.text) if alt2_data is None else json.dumps(alt2_data)}",
                ]
                raise requests.HTTPError("; ".join(texts), response=alt2_resp)

            data = alt_data
            resp = alt_resp

        message = None
        try:
            message = data["choices"][0]["message"]
        except Exception:
            try:
                text = data["choices"][0]["text"]
                try:
                    return json.loads(text)
                except Exception:
                    return {"text": text}
            except Exception:
                return data

        content = message.get("content") if isinstance(message, dict) else None
        if not content:
            return {"text": ""}

        try:
            return json.loads(content)
        except Exception:
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                return json.loads(content[start:end])
            except Exception:
                return {"text": content}

    def list_models(self) -> Dict[str, Any]:
        """Attempt to list available models using the standard endpoints."""
        urls = [
            f"{self.config.base_url}/models",
            f"{self.config.base_url}/v1/models",
        ]
        last = None
        for url in urls:
            r = self.session.get(url, timeout=30)
            last = r
            try:
                if r.status_code < 400:
                    return r.json()
            except Exception:
                pass
        text = ""
        try:
            text = last.text  # type: ignore[assignment]
        except Exception:
            text = ""
        raise requests.HTTPError(f"Failed to list models: {last.status_code if last else 'n/a'} {text}")
