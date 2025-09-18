# Fishing Net Market Dashboard

Interactive Solara dashboard and Slidev generator for exploring fishing net market data and producing executive slide decks.

## Dashboard Examples

The dashboard provides comprehensive market analysis across multiple views:

### 📈 Market Size
![Market Size Dashboard](asset/example_image/1.%20Market%20Size.png)
*Market progression analysis with growth metrics and trend visualization*

### 🌍 Regional Analysis  
![Regional Analysis Dashboard](asset/example_image/2.%20Regional%20Analysis.png)
*Regional market share breakdown with CAGR comparisons*

### 🐟 Production Mix
![Production Mix Dashboard](asset/example_image/3.%20Production%20Mix.png)
*Aquaculture vs capture fisheries analysis*

### 🧠 AI Assist Slide
![AI Assist Dashboard](asset/example_image/4.%20AI%20Assist%20Slide.png)
*AI-powered slide generation with live Slidev preview*

## Project Structure

```
.
├── app.py                         # Main Solara entry point
├── asset/
│   ├── config/openrouter_config.json   # OpenRouter credentials and defaults
│   ├── dataset/                         # All market research datasets
│   └── generated/ai_slides/             # Saved AI-produced Slidev decks
├── component/
│   ├── __init__.py
│   ├── ai_assist_slide_tab.py      # Solara component for AI slide generation
│   ├── openrouter_client.py        # Lightweight OpenRouter client wrapper
│   └── slidev/                     # Slidev workspace (slides.md, package.json, etc.)
└── no_relate/                      # Archived experiments and legacy scripts
```

## Prerequisites

- Python ≥ 3.10 (3.10 recommended)
- Node.js ≥ 18 (needed for Slidev preview)
- OpenRouter API key with access to the `openai/gpt-5` model (or update the config for another model)

### Python environment

Create and activate a virtual environment (example using `python -m venv`):

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # Install Solara + runtime deps
```

> If you prefer `uv`, use `uv venv` / `uv sync` instead.

### Configure OpenRouter

Edit `asset/config/openrouter_config.json` and set your real API key. Optionally tweak `model`, `referer`, `title`, or `web_search` settings.

## Running the dashboard

From the project root:

```bash
solara run app.py --reload
```

Or run everything through FastAPI/Uvicorn (this also exposes the Slidev proxy):

```bash
uvicorn serve:app --reload --port 8765
```

The default tab loads the AI slide assistant (Slidev prompt generator) alongside the market dashboard tabs.

## Generating Slidev decks

1. Start the Solara app.
2. Go to the “AI Assist” tab.
3. Adjust the prompt or pick one of the shortcuts.
4. Click **Generate**.
5. The resulting deck is written to:
   - `component/slidev/slides.md` (live preview)
   - `asset/generated/ai_slides/slides.md` (latest saved copy)

### Live Slidev preview

In another terminal:

```bash
cd component/slidev
npm install   # first time only
npx slidev slides.md --port 3030
```

**Important**: The Slidev workspace uses downgraded versions (Slidev 51.0.2 and Vite 6.0.8) to avoid iframe embedding issues that exist in newer versions.

For deployment, the slides are served through separate pinggy.io tunnels:
- Dashboard: Your main pinggy.io URL  
- Slides: `https://marketslide.a.pinggy.link`

The AI Assist tab embeds slides directly from the pinggy.io tunnel for seamless preview.

## Dataset updates

Place new or revised files inside `asset/dataset/`. The AI prompt automatically includes:

- `highlights.md`
- Every file that matches `Dataset *.txt`

## Tests & utilities

The `no_relate/` folder contains archived scripts (e.g., older dashboards, API tests). They’re kept for reference but aren’t part of the main app.

## Git usage

Typical flow:

```bash
git init
git add .
git commit -m "Initial Solara dashboard"
git remote add origin <repository-url>
git push -u origin main
```

## License

Add your preferred license here.
