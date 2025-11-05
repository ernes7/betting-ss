"""Theme configuration for Streamlit dashboard.

Customize colors, fonts, and styles in one place.
"""

# Color Palette - Dark Vibe
COLORS = {
    # Background
    "background": "#202A25",  # Gunmetal - main background
    "background_dark": "#1a1a1a",  # Darker variant for depth

    # Primary & Secondary
    "primary": "#5F4BB6",  # Iris purple
    "secondary": "#86A5D9",  # Vista Blue

    # Accent colors
    "success": "#38ef7d",
    "success_gradient_start": "#11998e",
    "success_gradient_end": "#38ef7d",

    "danger": "#f45c43",
    "danger_gradient_start": "#eb3349",
    "danger_gradient_end": "#f45c43",

    "warning": "#ffd700",

    # Text colors
    "text_primary": "white",
    "text_secondary": "rgba(255, 255, 255, 0.8)",
    "text_muted": "rgba(255, 255, 255, 0.6)",

    # Glass morphism - adjusted for dark background
    "glass_bg": "rgba(95, 75, 182, 0.15)",  # Primary color with opacity
    "glass_bg_light": "rgba(134, 165, 217, 0.2)",  # Secondary color with opacity
    "glass_border": "rgba(255, 255, 255, 0.1)",
    "glass_border_strong": "rgba(255, 255, 255, 0.15)",

    # Filter dock specific
    "dock_bg": "rgba(95, 75, 182, 0.2)",
    "dock_border": "rgba(134, 165, 217, 0.3)",
}

# Typography
FONTS = {
    # Font families
    "main_family": "Inconsolata",
    "title_family": "Momo Signature",

    # Font URLs
    "main_url": "https://fonts.googleapis.com/css2?family=Inconsolata:wght@300;400;500;600;700&display=swap",
    "title_url": "https://fonts.googleapis.com/css2?family=Momo+Signature&display=swap",

    # Font sizes
    "hero_title": "3rem",
    "hero_subtitle": "1.2rem",
    "section_title": "1.5rem",
    "metric_value": "2.5rem",
    "metric_value_large": "2.5rem",
    "metric_label": "0.9rem",
    "card_title": "1.2rem",
    "body": "1rem",
    "small": "0.8rem",
}

# Spacing
SPACING = {
    "card_padding": "25px",
    "section_padding": "20px",
    "border_radius": "20px",
    "border_radius_small": "15px",
    "border_radius_pill": "50px",
}


def get_custom_css() -> str:
    """Generate custom CSS with theme variables.

    Returns:
        CSS string with glassmorphism styles and theme colors
    """
    return f"""
    <style>
        /* Import Google Fonts */
        @import url('{FONTS["main_url"]}');
        @import url('{FONTS["title_url"]}');

        /* Global Styles */
        * {{
            font-family: '{FONTS["main_family"]}', monospace;
        }}

        /* Main Background - Solid Dark Color */
        .stApp {{
            background: {COLORS["background_dark"]};
        }}

        /* Remove sidebar completely */
        [data-testid="stSidebar"] {{
            display: none;
        }}

        /* Glass Card */
        .glass-card {{
            background: {COLORS["glass_bg"]};
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: {SPACING["border_radius"]};
            border: 1px solid {COLORS["glass_border"]};
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            padding: {SPACING["card_padding"]};
            margin: 10px 0;
        }}

        /* Filter Dock - Floating Top Bar */
        .filter-dock {{
            background: {COLORS["dock_bg"]};
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: {SPACING["border_radius_pill"]};
            border: 2px solid {COLORS["dock_border"]};
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            padding: 15px 30px;
            margin: 20px auto;
            max-width: 900px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
        }}

        /* Metric Cards */
        .metric-card {{
            background: {COLORS["glass_bg_light"]};
            backdrop-filter: blur(10px);
            border-radius: {SPACING["border_radius_small"]};
            padding: {SPACING["section_padding"]};
            border: 1px solid {COLORS["glass_border_strong"]};
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }}

        /* Hit/Miss/Pending Badges */
        .badge-hit {{
            background: linear-gradient(135deg, {COLORS["success_gradient_start"]} 0%, {COLORS["success_gradient_end"]} 100%);
            color: white;
            padding: 5px 15px;
            border-radius: {SPACING["border_radius_pill"]};
            font-weight: 600;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(17, 153, 142, 0.4);
        }}

        .badge-miss {{
            background: linear-gradient(135deg, {COLORS["danger_gradient_start"]} 0%, {COLORS["danger_gradient_end"]} 100%);
            color: white;
            padding: 5px 15px;
            border-radius: {SPACING["border_radius_pill"]};
            font-weight: 600;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(235, 51, 73, 0.4);
        }}

        .badge-pending {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
            color: white;
            padding: 5px 15px;
            border-radius: {SPACING["border_radius_pill"]};
            font-weight: 600;
            display: inline-block;
        }}

        /* Prediction Card */
        .prediction-card {{
            background: {COLORS["glass_bg"]};
            backdrop-filter: blur(15px);
            border-radius: {SPACING["border_radius"]};
            padding: {SPACING["card_padding"]};
            margin: 15px 0;
            border: 1px solid {COLORS["glass_border_strong"]};
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }}

        .prediction-card-hit {{
            border-left: 5px solid {COLORS["success_gradient_end"]};
        }}

        .prediction-card-miss {{
            border-left: 5px solid {COLORS["danger_gradient_end"]};
        }}

        .prediction-card-pending {{
            border-left: 5px solid {COLORS["primary"]};
        }}

        /* Custom metric styling */
        div[data-testid="stMetricValue"] {{
            font-size: {FONTS["metric_value"]};
            font-weight: 700;
            color: {COLORS["text_primary"]};
        }}

        div[data-testid="stMetricLabel"] {{
            color: {COLORS["text_secondary"]};
            font-size: {FONTS["metric_label"]};
            font-weight: 500;
        }}

        /* Headers - Use title font */
        h1, h2, h3 {{
            color: {COLORS["text_primary"]} !important;
            font-weight: 700 !important;
            font-family: '{FONTS["title_family"]}', cursive !important;
        }}

        /* Expander - Floating Card Style */
        .streamlit-expanderHeader {{
            background: {COLORS["glass_bg"]};
            border-radius: 12px;
            color: {COLORS["text_primary"]} !important;
            font-weight: 600;
            border: 1px solid {COLORS["glass_border"]};
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            padding: 12px 16px;
            margin: 8px 0;
            transition: all 0.3s ease;
        }}

        .streamlit-expanderHeader:hover {{
            background: {COLORS["glass_bg_light"]};
            border-color: {COLORS["secondary"]};
            box-shadow: 0 6px 20px rgba(134, 165, 217, 0.2);
            transform: translateY(-2px);
        }}

        /* Expander content area */
        div[data-testid="stExpander"] > div:last-child {{
            background: {COLORS["glass_bg"]};
            border: 1px solid {COLORS["glass_border"]};
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 16px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }}

        /* Small text styling */
        small {{
            color: {COLORS["text_secondary"]};
            font-size: 0.85rem;
        }}

        /* Square Card - Grid Layout */
        .square-card {{
            background: {COLORS["glass_bg"]};
            backdrop-filter: blur(10px);
            border-radius: {SPACING["border_radius_small"]};
            border: 1px solid {COLORS["glass_border"]};
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            padding: 20px;
            margin: 0 8px 16px 8px;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .square-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(134, 165, 217, 0.3);
            border-color: {COLORS["secondary"]};
        }}

        .square-card-analyzed {{
            border-left: 3px solid {COLORS["primary"]};
        }}

        .square-card-pending {{
            border-left: 3px solid {COLORS["glass_border_strong"]};
            opacity: 0.8;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 8px;
            border-bottom: 1px solid {COLORS["glass_border"]};
        }}

        .card-date {{
            font-size: 0.85rem;
            color: {COLORS["text_secondary"]};
            font-weight: 500;
        }}

        .card-profit {{
            font-size: 1.3rem;
            font-weight: 700;
        }}

        .card-matchup {{
            text-align: center;
            padding: 8px 0;
        }}

        .matchup-text {{
            font-size: 1rem;
            font-weight: 600;
            color: {COLORS["text_primary"]};
            line-height: 1.2;
        }}

        .card-stats {{
            display: flex;
            justify-content: space-between;
            gap: 8px;
            padding: 12px 0;
            border-top: 1px solid {COLORS["glass_border"]};
            border-bottom: 1px solid {COLORS["glass_border"]};
        }}

        .stat-item {{
            flex: 1;
            text-align: center;
        }}

        .stat-label {{
            font-size: 0.7rem;
            color: {COLORS["text_muted"]};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}

        .stat-value {{
            font-size: 0.95rem;
            font-weight: 700;
            color: {COLORS["text_primary"]};
        }}

        .card-bets {{
            margin-top: 8px;
            font-size: 0.75rem;
        }}

        .bet-item {{
            display: flex;
            align-items: flex-start;
            gap: 6px;
            margin-bottom: 4px;
            color: {COLORS["text_secondary"]};
            line-height: 1.3;
        }}

        .bet-icon {{
            display: inline-block;
            width: 16px;
            height: 16px;
            line-height: 16px;
            text-align: center;
            border-radius: 3px;
            font-size: 0.7rem;
            font-weight: 700;
            flex-shrink: 0;
        }}

        .bet-won {{
            background: {COLORS["success"]};
            color: white;
        }}

        .bet-lost {{
            background: {COLORS["danger"]};
            color: white;
        }}

        .bet-pending {{
            background: {COLORS["glass_border_strong"]};
            color: {COLORS["text_muted"]};
        }}

        .bet-more {{
            font-size: 0.7rem;
            color: {COLORS["text_muted"]};
            text-align: center;
            margin-top: 6px;
            font-style: italic;
        }}

        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Buttons - Primary color */
        .stButton > button {{
            background: {COLORS["primary"]};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 8px 16px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .stButton > button:hover {{
            background: {COLORS["secondary"]};
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(95, 75, 182, 0.4);
        }}

        /* Select boxes - Dark theme */
        .stSelectbox > div > div {{
            background: {COLORS["glass_bg"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["glass_border"]};
        }}
    </style>
    """
