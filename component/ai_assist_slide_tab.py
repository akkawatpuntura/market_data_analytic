import json
from pathlib import Path
import solara
from .openrouter_client import OpenRouterClient, OpenRouterConfig


# Local palette (kept minimal to avoid coupling)
COLORS = {
    "border": "#e2e8f0",
    "background": "#ffffff",
}


def _extract_code_block(text: str) -> str:
    # If the model wrapped content in a code block, extract the first block
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            content = parts[1]
            content = content.split("\n", 1)[1] if "\n" in content else content
            return content.strip()
    return text.strip()


def _split_slidev(md: str) -> tuple[dict, list[str]]:
    """Return (frontmatter, slides) from Slidev markdown. Best-effort parser."""
    fm = {}
    body = md
    if md.startswith("---\n"):
        try:
            end = md.index("\n---\n", 4)
            fm_text = md[4:end]
            body = md[end + 5 :]
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
        except ValueError:
            body = md
    slides = []
    current = []
    for line in body.splitlines():
        if line.strip() == "---":
            slides.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    if current:
        slides.append("\n".join(current).strip())
    slides = [s for s in slides if s]
    return fm, slides


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


ROOT_DIR = Path(__file__).resolve().parents[1]
SLIDEV_DIR = Path(__file__).resolve().parent / "slidev"
ASSET_DIR = ROOT_DIR / "asset"
DATASET_DIR = ASSET_DIR / "dataset"
GENERATED_DIR = ASSET_DIR / "generated" / "ai_slides"


def _dataset_sort_key(path: Path) -> tuple[int, str]:
    """Sort dataset files by their numeric prefix and name."""
    name = path.name
    try:
        number_part = name.split(" ", 2)[1]
        order = int(number_part)
    except (IndexError, ValueError):
        order = 999
    return order, name


def _write_slidev_slides(content: str) -> None:
    """Persist generated slides to the Slidev workspace."""
    SLIDEV_DIR.mkdir(parents=True, exist_ok=True)
    (SLIDEV_DIR / "slides.md").write_text(content, encoding="utf-8")


def _gather_context() -> str:
    """Collect all context files and format them for the prompt."""
    base = DATASET_DIR
    files: list[tuple[str, str]] = []

    highlights = base / "highlights.md"
    if highlights.exists():
        files.append(("highlights.md", _load_text(highlights)))

    dataset_files = sorted(base.glob("Dataset *.txt"), key=_dataset_sort_key)
    for dataset_path in dataset_files:
        files.append((dataset_path.name, _load_text(dataset_path)))

    parts = ["<CONTEXT_FILES>"]
    for name, content in files:
        if content:
            parts.append(f"[[FILE: {name}]]\n{content}\n[[/FILE]]")
    parts.append("</CONTEXT_FILES>")
    return "\n\n".join(parts)


PROMPT_TEMPLATES: list[tuple[str, str]] = [
    (
        "Market Survey Summary",
        "5-6 slide of market survey summary covering market size, growth trend and regional base analysis.",
    ),
    (
        "Competitive Analysis",
        "3-4 slide of concise competitive landscape presentation that profiles top fishing-net vendsors, differentiators, pricing signals, recent moves, and recommended response actions.",
    ),
    (
        "Customer Segmentation & Requirement",
        "3-4 slide of customer segmentation briefing that defines priority buyer personas, procurement criteria, and advisory talking points for each segment.",
    ),
    (
        "Product Performance & Tech Adoption",
        "Assemble a performance and technology adoption update showing product line momentum, material innovations, digital enablement trends, and operational KPIs to monitor.",
    ),
]


@solara.component
def TabAIAssistSlide():
    default_prompt = PROMPT_TEMPLATES[0][1] if PROMPT_TEMPLATES else "Generate an executive-ready slide deck."
    prompt = solara.use_reactive(default_prompt)
    slides_md = solara.use_reactive("")
    slides = solara.use_reactive([])  # list[str]
    frontmatter = solara.use_reactive({})
    idx = solara.use_reactive(0)
    error_text = solara.use_reactive("")
    loading = solara.use_reactive(False)

    def generate():
        error_text.set("")
        loading.set(True)
        try:
            cfg = OpenRouterConfig.load()
            client = OpenRouterClient(cfg)
            system = (
                """You design concise Slidev markdown decks for business reviews.
                Return ONLY valid `slides.md` content with `---` separators, no explanations.
                Frontmatter must set `theme: apple-basic` with lightweight styling.

                Deck structure (Up to user prompt):
                1. **Cover** — title, subtitle, date.
                2. **Key Metrics** — 2–3 compact metric cards plus 1 short highlight.
                3. **Insights** — bulleted insights with 2 simple metric cards.
                4. **Thank You** — data sources + small card reading 'End of Presentation' (bottom-right).

                Design rules:

                * Style only with simple Tailwind utilities on `<div>`, `<span>`, `<ul>`, `<li>`, `<p>`.
                * Avoid `<table>`, complex grids, absolute positioning, or heavy layouts.
                * Keep text concise to prevent overflow.
                * Maximize space don leave to much space on top and left
                * Cite sources in a single small footer line per slide.
                * Palette: soft gray/white background, blue accents, subtle red highlights.
                * If required, perform web search for rich, professional content.
                * No Mermaid, scripts, or external assets."""

            )
            context_block = _gather_context()
            result = client.chat_json(
                [
                    {"role": "system", "content": system},
                    {"role": "system", "content": context_block},
                    {"role": "user", "content": prompt.value},
                ],
                temperature=0.4,
            )
            content = result.get("text") if isinstance(result, dict) else str(result)
            content = _extract_code_block(content)
            slides_md.set(content)
            fm, sl = _split_slidev(content)
            frontmatter.set(fm)
            slides.set(sl)
            idx.set(0)
            # Also write to slidev/slides.md for live Slidev usage
            try:
                _write_slidev_slides(content)
            except Exception as write_err:
                # Do not fail generation if file write fails; show as warning
                error_text.set(f"Generated, but failed to write slidev/slides.md: {write_err}")
        except Exception as e:
            error_text.set(str(e))
        finally:
            loading.set(False)

    def save_slides():
        try:
            GENERATED_DIR.mkdir(parents=True, exist_ok=True)
            path = GENERATED_DIR / "slides.md"
            path.write_text(slides_md.value or "", encoding="utf-8")
            _write_slidev_slides(slides_md.value or "")
        except Exception as e:
            error_text.set(str(e))

    with solara.ColumnsResponsive(default=[12], large=[4, 8]):
        with solara.Column(gap="8px", style={"display": "flex", "flex-direction": "column"}):
            solara.HTML("h3", "AI Assist")
            solara.InputTextArea("Describe the slides you want", value=prompt, rows=3, continuous_update=False)
            with solara.Row(gap="8px"):
                solara.Button("Generate", on_click=generate, color="primary")
                if loading.value:
                    solara.ProgressLinear(True)
            if error_text.value:
                solara.Error(error_text.value)

            solara.HTML("h4", "Prompt Shortcuts")
            with solara.Row(gap="6px", style={"flex-wrap": "wrap"}):
                for label, template in PROMPT_TEMPLATES:
                    solara.Button(
                        label,
                        on_click=lambda template=template: prompt.set(template),
                        outlined=True,
                        color="primary",
                    )

        with solara.Column(gap="12px", style={"height": "60vh", "display": "flex", "flex-direction": "column"}):
            solara.HTML("h4", "Slide Preview")
            solara.HTML(
                "div",
                'Slides served via <a href="https://marketslide.a.pinggy.link" target="_blank" style="color: #2563eb; text-decoration: underline;">marketslide.a.pinggy.link</a>',
                style={
                    "font-size": "0.82rem",
                    "color": "#1e293b",
                },
            )
            solara.HTML(
                "iframe",
                attributes={
                    "src": "https://marketslide.a.pinggy.link",
                    "width": "100%",
                    "height": "80%",
                    "frameborder": "0",
                    "allowfullscreen": "true",
                },
                style={
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "8px",
                    "flex": 1,
                },
            )


__all__ = ["TabAIAssistSlide"]
