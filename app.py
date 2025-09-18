from pathlib import Path

import pandas as pd
import solara

from component.ai_assist_slide_tab import TabAIAssistSlide


# Palette
COLORS = {
    "primary": "#2563eb",
    "accent": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "background": "#ffffff",
    "surface": "#f8fafc",
    "text": "#1e293b",
    "text_secondary": "#64748b",
    "border": "#e2e8f0",
}


DATA_DIR = Path("asset/dataset")
FILE_MARKET = DATA_DIR / "Dataset 1 Market Size Progression (2020-2034).txt"
FILE_REGION = DATA_DIR / "Dataset 2 Regional Market Analysis.txt"
FILE_AQUA = DATA_DIR / "Dataset 3 Aquaculture vs Capture Fisheries Production.txt"

def _read_csv(path: Path) -> pd.DataFrame:
    # Robust read for .txt CSVs with possible header comments (#) and quoted fields
    return pd.read_csv(path, engine="python", comment="#")


def _get_value_by_year(df: pd.DataFrame, year: int, column: str) -> float:
    match = df.loc[df["year"] == year]
    if match.empty or pd.isna(match.iloc[0][column]):
        return float("nan")
    return float(match.iloc[0][column])


@solara.component
def MetricCard(title: str, value: str, subtitle: str = "", trend: str = "", color: str = COLORS["primary"]):
    with solara.Column(
        gap="4px",
        style={
            "background": COLORS["background"],
            "border": f"1px solid {COLORS['border']}",
            "border-radius": "12px",
            "padding": "8px",
            "flex": "1",
            "min-width": "140px",
            "width": "100%",
            "box-shadow": "0 1px 3px 0 rgba(0, 0, 0, 0.06)",
        }
    ):
        solara.HTML(
            "div",
            title,
            style={
                "font-size": "0.75rem",
                "font-weight": "600",
                "color": COLORS["text_secondary"],
                "text-transform": "uppercase",
                "letter-spacing": "0.04em",
                "margin-bottom": "2px",
            },
        )
        with solara.Row(gap="4px", style={"align-items": "baseline", "margin-bottom": "2px"}):
            solara.HTML(
                "div",
                value,
                style={"font-size": "1.5rem", "font-weight": "800", "color": color},
            )
            if trend:
                solara.HTML(
                    "span",
                    trend,
                    style={
                        "font-size": "0.8rem",
                        "color": (COLORS["accent"] if trend.strip().startswith("+") else COLORS["danger"]),
                        "font-weight": "600",
                    },
                )
        if subtitle:
            solara.HTML("div", subtitle, style={"font-size": "0.8rem", "color": COLORS["text_secondary"]})


@solara.component
def HighlightsSection(title: str, items: list[str]):
    with solara.Card(style={
        "padding": "10px 12px",
        "border-radius": "12px",
        "border": f"1px solid {COLORS['border']}",
        "background": COLORS["surface"],
    }):
        solara.HTML("div", title, style={
            "font-size": "0.9rem",
            "font-weight": "700",
            "color": COLORS["text"],
            "text-transform": "uppercase",
            "letter-spacing": "0.04em",
            "margin-bottom": "6px",
        })
        for it in items:
            solara.HTML("div", f"• {it}", style={
                "font-size": "0.95rem",
                "color": COLORS["text"],
                "margin": "2px 0",
            })


@solara.component
def TabMarketSize():
    df = _read_csv(FILE_MARKET)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Coerce numeric based on updated schema (values in billions already)
    for c in [
        "total_market_usd_billions",
        "fishing_nets_usd_billions",
        "aquaculture_cages_usd_billions",
        "annual_growth_rate_percent",
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Use 2024 as the base year if present, otherwise the minimum available year
    all_years = df["year"].tolist()
    min_year, max_year = int(df["year"].min()), int(df["year"].max())
    base_year = 2024 if 2024 in all_years else min_year
    proj_year = 2034 if 2034 in all_years else max_year

    base_total = _get_value_by_year(df, base_year, "total_market_usd_billions")
    proj_total = _get_value_by_year(df, proj_year, "total_market_usd_billions")

    # Growth from base_year to proj_year
    if pd.isna(base_total) or base_total == 0 or pd.isna(proj_total):
        growth = 0.0
    else:
        growth = (proj_total / base_total - 1.0) * 100.0

    # Average annual growth
    avg_cagr = float(df["annual_growth_rate_percent"].mean()) if "annual_growth_rate_percent" in df.columns else 0.0

    # Layout: metrics (left) and chart (right) responsive
    with solara.ColumnsResponsive(default=[12, 12], large=[4, 8]):
        # Left: KPI cards and highlights
        with solara.Column(gap="8px", style={"width": "100%"}):
            with solara.ColumnsResponsive(default=[12], large=[12], gutters=False, gutters_dense=False):
                with solara.ColumnsResponsive(default=[6, 6], large=[6, 6]):
                    MetricCard(
                        title=f"{base_year} Market Size",
                        value=f"${(0.0 if pd.isna(base_total) else base_total):.2f}B",
                        subtitle="Base year total",
                    )
                    MetricCard(
                        title=f"{proj_year} Market Size",
                        value=f"${(0.0 if pd.isna(proj_total) else proj_total):.2f}B",
                        subtitle="Projected total",
                        trend=f"{growth:+.1f}%",
                        color=COLORS["accent"],
                    )
                with solara.Column(gap="0px", style={"width": "100%"}):
                    MetricCard(
                        title="Avg Growth",
                        value=f"{avg_cagr:.1f}%",
                        subtitle="Annual growth rate",
                        color=COLORS["warning"],
                    )

            HighlightsSection(
                title="Highlights",
                items=[
                    "2025 market at $2.1B; 2030 projection $2.9B",
                    "CAGR 6.7% with ~38% growth over 5 years",
                    "Peak annual growth in 2023 at 7.14%",
                ],
            )

        # Right: Chart
        with solara.Card(style={
            "padding": "0",
            "border-radius": "12px",
            "overflow": "hidden",
            "height": "clamp(360px, 60vh, 700px)",
            "width": "100%",
        }):
            years = [str(y) for y in df["year"].tolist()]
            fishing_nets = df["fishing_nets_usd_billions"].round(2).tolist()
            aquaculture_cages = df["aquaculture_cages_usd_billions"].round(2).tolist()
            total = df["total_market_usd_billions"].round(2).tolist()

            options = {
                "title": {"text": f"Market Size Progression ({min_year}-{max_year})"},
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["Fishing Nets", "Aquaculture Cages", "Total"], "bottom": 0},
                "grid": {"left": "3%", "right": "4%", "bottom": 60, "containLabel": True},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}B"}},
                "dataZoom": [{"type": "inside"}, {"type": "slider", "bottom": 30}],
                "series": [
                    {
                        "name": "Fishing Nets",
                        "type": "line",
                        "stack": "market",
                        "data": fishing_nets,
                        "smooth": True,
                        "areaStyle": {"opacity": 0.25},
                    },
                    {
                        "name": "Aquaculture Cages",
                        "type": "line",
                        "stack": "market",
                        "data": aquaculture_cages,
                        "smooth": True,
                        "areaStyle": {"opacity": 0.25},
                    },
                    {
                        "name": "Total",
                        "type": "line",
                        "data": total,
                        "smooth": True,
                        "symbol": "none",
                        "lineStyle": {"width": 2, "type": "dashed"},
                        "markPoint": {
                            "data": [
                                {
                                    "coord": [str(base_year), base_total if not pd.isna(base_total) else 0.0],
                                    "value": f"${(0.0 if pd.isna(base_total) else base_total):.2f}B",
                                    "itemStyle": {"color": "#2563eb"}
                                },
                                {
                                    "coord": [str(proj_year), proj_total if not pd.isna(proj_total) else 0.0],
                                    "value": f"${(0.0 if pd.isna(proj_total) else proj_total):.2f}B",
                                    "itemStyle": {"color": "#10b981"}
                                }
                            ],
                            "symbolSize": 30,
                            "label": {
                                "show": True,
                                "position": "top",
                                "fontSize": 14,
                                "fontWeight": "bold"
                            }
                        }
                    },
                ],
            }

            solara.FigureEcharts(option=options, responsive=True)


@solara.component
def TabRegionalAnalysis():
    df = _read_csv(FILE_REGION)

    # Normalize column names (updated schema) and coerce numeric
    df.columns = [c.strip().lower() for c in df.columns]
    num_cols = [
        "market_share_percent_2024",
        "cagr_2025_2030_percent",
        "market_value_2024_usd_millions",
        "projected_value_2030_usd_millions",
    ]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    top_region = df.sort_values("market_share_percent_2024", ascending=False).iloc[0]
    total_2024 = float(df["market_value_2024_usd_millions"].sum())
    total_2030 = float(df["projected_value_2030_usd_millions"].sum())
    overall_growth = (total_2030 / total_2024 - 1.0) * 100.0 if total_2024 else 0.0

    with solara.Column(gap="8px"):
        with solara.ColumnsResponsive(default=[12], medium=[8,4]):
            with solara.ColumnsResponsive(default=[6,6], medium=[4, 4, 4]):
                MetricCard(
                    title="Top Region",
                    value=top_region["region"],
                    subtitle=f"Share {top_region['market_share_percent_2024']:.1f}%",
                    color=COLORS["primary"],
                )
                MetricCard(
                    title="Market 2030",
                    value=f"${total_2030/1000:.2f}B",
                    subtitle="Projected total",
                    trend=f"{overall_growth:+.1f}%",
                    color=COLORS["accent"],
                )
                MetricCard(
                    title="Market 2024",
                    value=f"${total_2024/1000:.2f}B",
                    subtitle="Aggregate",
                )

            HighlightsSection(
                title="Highlights",
                items=[
                    "Asia-Pacific leads with 43% share (2024)",
                    "Africa fastest growing at 9.2% CAGR",
                    "NA 22.5% and Europe 18.7% with sustainability focus",
                ],
            )

        # Charts
        regions = df["region"].tolist()
        shares = df["market_share_percent_2024"].tolist()
        cagr = df["cagr_2025_2030_percent"].tolist()
        
        # Define consistent color palette for regions - pastel style
        region_colors = ["#a7c4e8", "#b8e5d1", "#f5d29c", "#f4a5a5", "#d4a7e8", "#9dd4e8"]

        options_share = {
            "title": {"text": "Regional Market Share (2024)"},
            "tooltip": {"trigger": "item", "formatter": "{b}: {c}% ({d}%)"},
            "legend": {"orient": "vertical", "right": "right", "bottom": "bottom"},
            "color": region_colors,
            "series": [{
                "name": "Market Share",
                "type": "pie",
                "radius": "70%",
                "center": ["50%", "50%"],
                "data": [{"value": share, "name": region} for region, share in zip(regions, shares)],
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }],
        }

        options_cagr = {
            "title": {"text": "CAGR by Region (2025-2030)"},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": 40, "containLabel": True},
            "xAxis": {"type": "category", "data": regions},
            "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
            "series": [{
                "name": "CAGR", 
                "type": "bar", 
                "data": [
                    {
                        "value": value, 
                        "itemStyle": {"color": region_colors[i % len(region_colors)]}
                    } 
                    for i, value in enumerate(cagr)
                ]
            }],
        }

        with solara.ColumnsResponsive(default=[12], medium=[6, 6]):
            with solara.Card(style={"padding": "0", "border-radius": "12px", "overflow": "hidden"}):
                solara.FigureEcharts(option=options_share, responsive=True)
            with solara.Card(style={"padding": "0", "border-radius": "12px", "overflow": "hidden"}):
                solara.FigureEcharts(option=options_cagr, responsive=True)


@solara.component
def TabAquacultureVsCapture():
    df = _read_csv(FILE_AQUA)
    df.columns = [c.strip().lower() for c in df.columns]
    # Updated schema: values are in USD millions and include total and category metrics
    num_cols = [
        "aquaculture_net_demand_usd_millions",
        "capture_fisheries_net_demand_usd_millions",
        "gill_nets_market_share_percent",
        "drift_nets_growth_rate_percent",
        "total_fishing_nets_market_usd_millions",
    ]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    latest = df.sort_values("year").iloc[-1]

    latest_total = float(latest["total_fishing_nets_market_usd_millions"])
    latest_aqua = float(latest["aquaculture_net_demand_usd_millions"])
    aqua_share = (latest_aqua / latest_total * 100.0) if latest_total else 0.0

    with solara.Column(gap="8px"):
        with solara.ColumnsResponsive(default=[12], medium=[2,4,6]):
            with solara.ColumnsResponsive(default=[6,6], medium=[12]):
                MetricCard(
                    title=f"Aquaculture Share {int(latest['year'])}",
                    value=f"{aqua_share:.1f}%",
                    subtitle="Of total net demand",
                    color=COLORS["accent"],
                )
                MetricCard(
                    title=f"Total Market {int(latest['year'])}",
                    value=f"${latest_total/1000:.2f}B",
                    subtitle="Fishing nets market",
                )
                MetricCard(
                    title="Gill Nets Share",
                    value=f"{latest['gill_nets_market_share_percent']:.1f}%",
                    subtitle="Revenue share",
                    color=COLORS["warning"],
                )

            HighlightsSection(
                title="Highlights",
                items=[
                    "Aquaculture growing 13.7% annually; overtakes by 2030",
                    "2024: Aquaculture $828M vs Capture $1,222M",
                    "2030: Aquaculture $1,790M vs Capture $1,210M",
                    "Gill nets 32% share; drift nets 8.7% CAGR",
                ],
            )

            with solara.Card():
                years = [str(int(y)) for y in df["year"].tolist()]
                aqua = df["aquaculture_net_demand_usd_millions"].round(0).tolist()
                capture = df["capture_fisheries_net_demand_usd_millions"].round(0).tolist()

                options = {
                    "title": {"text": "Aquaculture vs Capture Net Demand ($M)"},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Aquaculture", "Capture"], "bottom": 0},
                    "grid": {"left": "3%", "right": "4%", "bottom": 40, "containLabel": True},
                    "xAxis": {"type": "category", "data": years},
                    "yAxis": {"type": "value", "axisLabel": {"formatter": "${value}"}},
                    "series": [
                        {"name": "Aquaculture", "type": "line", "data": aqua, "smooth": True},
                        {"name": "Capture", "type": "line", "data": capture, "smooth": True},
                    ],
                }
                solara.FigureEcharts(option=options, responsive=True)


@solara.component
def Page():
    with solara.Column(
        style={
            "background": COLORS["surface"],
            "min-height": "100vh",
            "padding": "0",
        }
    ):
        with solara.Column(
            style={
                "background": COLORS["background"],
                "padding": "12px",
                "border-bottom": f"1px solid {COLORS['border']}",
            }
        ):
            solara.HTML(
                "h1",
                "Fishing Net Market Data Analytic",
                style={"margin": 0, "color": COLORS["text"], "font-weight": 800},
            )

        with solara.Column(style={"padding": "12px"}):
            with solara.lab.Tabs():
                with solara.lab.Tab("📈 Market Size"):
                    TabMarketSize()
                with solara.lab.Tab("🌍 Regional Analysis"):
                    TabRegionalAnalysis()
                with solara.lab.Tab("🐟 Production Mix"):
                    TabAquacultureVsCapture()
                with solara.lab.Tab("🧠 AI Assist Slide"):
                    TabAIAssistSlide()


# Run with: solara run app_three_datasets_fixed_highlight.py --port 8765

routes = [solara.Route(path="/", component=Page, label="Dashboard")]
