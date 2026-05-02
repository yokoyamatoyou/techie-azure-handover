# -*- coding: utf-8 -*-
"""Chart helper functions for Streamlit UI with industrial-friendly styling."""
from typing import Dict

# ---------------------------------------------------------------------------
# Industrial-Friendly CSS (inject into Streamlit via st.markdown)
# 工場・作業現場向け高視認性デザイン
# ---------------------------------------------------------------------------
GLASS_CSS = """
<style>
/* Industrial-Friendly Light Theme - Apple Style */
.stApp {
  background: #FFFFFF !important;
  color: #1D1D1F !important;
}

/* Header - Clean */
header[data-testid="stHeader"], .stApp > header {
    background-color: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
}

/* Sidebar - Light Gray */
[data-testid="stSidebar"] {
  background-color: #F5F5F7 !important;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
}
[data-testid="stSidebar"] * {
  color: #1D1D1F !important;
}

/* Clean Cards - High Visibility */
.glass-card {
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 1.25rem;
  margin: 0.75rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* Text - Maximum Contrast */
h1, h2, h3, h4, h5, h6, p, li, span, div {
  color: #1D1D1F !important;
}

/* Input Fields - Clear & Accessible */
.stTextInput > div > div > input, 
.stTextArea > div > div > textarea, 
.stSelectbox > div > div > div {
  background-color: #FFFFFF !important;
  color: #1D1D1F !important;
  border: 1.5px solid rgba(0, 0, 0, 0.15) !important;
  border-radius: 8px !important;
}
.stTextInput > div > div > input:focus {
  border-color: #0071E3 !important;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12) !important;
}

/* Metrics - Large & Readable */
[data-testid="stMetricLabel"] {
  color: #6E6E73 !important;
  font-size: 0.875rem !important;
}
[data-testid="stMetricValue"] {
  color: #1D1D1F !important;
  font-weight: 600 !important;
}

/* Primary Button - Apple Blue */
.stButton > button, button[kind="primary"] {
  background: #0071E3 !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.625rem 1.25rem !important;
  font-weight: 500 !important;
  transition: all 0.2s ease;
}
.stButton > button:hover, button[kind="primary"]:hover {
  background: #005BB5 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
}
</style>
"""

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.express as px
except Exception:  # pragma: no cover - fallback when plotly is missing
    go = None
    make_subplots = None
    px = None


class SimpleFigure:
    """Minimal stand-in for plotly.graph_objects.Figure."""

    def __init__(self):
        self.data = []
        self.layout = {}

    def add_trace(self, trace):
        self.data.append(trace)

    def update_layout(self, **kwargs):
        self.layout.update(kwargs)

    def update_yaxes(self, **kwargs):
        self.layout.setdefault("yaxis", {}).update(kwargs)


class SimpleBar(dict):
    """Minimal bar trace representation."""

    def __init__(self, x=None, y=None, orientation=None, marker_color=None):
        super().__init__(x=x, y=y, orientation=orientation, marker_color=marker_color)

from .constants import COLOR_PALETTE


def create_score_gauge(score: float, title: str, color: str):
    if go is None:
        return SimpleFigure()

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
        }
    ))
    fig.update_layout(height=250)
    return fig


def create_aio_score_chart_vertical(
    data: Dict[str, Dict[str, float]], labels_map: Dict[str, str], title: str
):
    labels = [labels_map.get(k, k.title()) for k in labels_map.keys()]
    values = [data.get(k, {"score": 0}).get("score", 0) for k in labels_map.keys()]

    if go is None or make_subplots is None:
        fig = SimpleFigure()
        fig.add_trace(SimpleBar(x=values, y=labels, orientation="h", marker_color=COLOR_PALETTE["accent"]))
        fig.update_layout(title=title, xaxis_title="スコア", yaxis_title="項目", height=400)
        fig.update_yaxes(autorange="reversed")
        return fig

    fig = make_subplots()
    fig.add_trace(
        go.Bar(x=values, y=labels, orientation="h", marker_color=COLOR_PALETTE["accent"])
    )
    # Dark theme styling to match UI
    fig.update_layout(
        title=dict(text=title, font=dict(color='#1D1D1F')), 
        xaxis_title="スコア", 
        yaxis_title="項目", 
        height=400, 
        xaxis=dict(range=[0, 100], color='#1D1D1F', gridcolor='rgba(0,0,0,0.08)'),
        yaxis=dict(color='#1D1D1F'),
        margin=dict(l=180),
        font=dict(size=12, color='#1D1D1F'),
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def create_categorized_score_charts(data: Dict[str, Dict], categories: Dict[str, Dict]) -> Dict[str, any]:
    """
    Create separate charts for each category (E-E-A-T, AI Search, UX, Technical).
    
    Args:
        data: Score data with 'score' and 'advice' for each item
        categories: Dict of category_name -> {keys: [...], weight: float, description: str}
    
    Returns:
        Dict of category_name -> plotly figure
    """
    if go is None:
        return {}
    
    charts = {}
    
    # Category colors for visual distinction (Apple-style)
    category_colors = {
        "E-E-A-T評価": "#0071E3",      # Apple Blue
        "AI検索最適化": "#34C759",      # Apple Green
        "ユーザー体験": "#FF9500",      # Apple Orange
        "技術指標": "#5856D6",          # Apple Purple
    }
    
    for cat_name, cat_info in categories.items():
        keys = cat_info.get("keys", [])
        labels_map = cat_info.get("labels", {})
        weight = cat_info.get("weight", 0)
        
        labels = [labels_map.get(k, k.title()) for k in keys]
        values = [data.get(k, {"score": 0}).get("score", 0) for k in keys]
        
        color = category_colors.get(cat_name, COLOR_PALETTE["accent"])
        
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=values, 
                y=labels, 
                orientation="h", 
                marker_color=color,
                text=[f"{v:.0f}" for v in values],
                textposition='outside',
                textfont=dict(color='#1D1D1F')
            )
        )
        
        # Calculate category average
        avg_score = sum(values) / len(values) if values else 0
        
        fig.update_layout(
            title=dict(
                text=f"{cat_name} (重み: {int(weight*100)}%, 平均: {avg_score:.1f}点)",
                font=dict(color='#1D1D1F', size=14)
            ),
            xaxis=dict(range=[0, 100], color='#1D1D1F', gridcolor='rgba(0,0,0,0.08)'),
            yaxis=dict(color='#1D1D1F'),
            height=200,
            margin=dict(l=150, r=50, t=40, b=30),
            font=dict(size=11, color='#1D1D1F'),
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
        )
        fig.update_yaxes(autorange="reversed")
        
        charts[cat_name] = {
            "fig": fig,
            "avg": avg_score,
            "weight": weight,
            "items": {k: data.get(k, {}) for k in keys}
        }
    
    return charts

def create_token_pie(model_data: Dict[str, Dict], title: str = "モデル別トークン消費"):
    """
    モデル別のトークン消費内訳円グラフを作成する。
    
    Args:
        model_data (Dict): {model_name: {'input_tokens': int, 'output_tokens': int, ...}}
        title (str): グラフタイトル
    
    Returns:
        plotly.graph_objects.Figure
    """
    if not model_data:
        # データがない場合は空の図を返す（エラー回避）
        if go is None:
            return SimpleFigure()
        fig = go.Figure()
        fig.update_layout(
            title_text="データなし",
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
            font=dict(color='#1D1D1F')
        )
        return fig

    # モデル名を日本語ラベルに変換
    model_labels = {
        "gpt-4.1-mini": "標準分析",
        "gpt-4.1": "深掘り分析",
        "gpt-4o-mini": "標準分析（旧）",
        "gpt-4o-mini-search-preview": "検索連携分析（旧）",
        "gpt-4o": "詳細分析（旧）",
    }
    
    labels = []
    values = []
    
    for model_name, stats in model_data.items():
        display_name = model_labels.get(model_name, "その他")
        labels.append(display_name)
        # トークン総数（入力+出力）でグラフ化
        total = stats.get('input_tokens', 0) + stats.get('output_tokens', 0)
        values.append(total)
    
    if go is None:
        return SimpleFigure()

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker=dict(colors=[COLOR_PALETTE.get("primary"), COLOR_PALETTE.get("secondary"), COLOR_PALETTE.get("accent")]),
        textinfo='label+percent',
        hoverinfo='label+value+percent'
    )])
    
    fig.update_layout(
        title_text=title,
        showlegend=True,
        margin=dict(t=40, b=20, l=20, r=20),
        height=300,
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        font=dict(color='#1D1D1F'),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    return fig
