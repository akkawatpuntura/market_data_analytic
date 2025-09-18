"""Components package exposing Solara views and OpenRouter client helpers."""

from .ai_assist_slide_tab import TabAIAssistSlide  # noqa: F401
from .openrouter_client import OpenRouterClient, OpenRouterConfig  # noqa: F401

__all__ = ["TabAIAssistSlide", "OpenRouterClient", "OpenRouterConfig"]
