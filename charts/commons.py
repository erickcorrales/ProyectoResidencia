
# charts/commons.py
import altair as alt
import calendar

MONTH_NAME = list(calendar.month_name)[1:]

def base_text_style():
    return {
        "font": "Inter, Segoe UI, Roboto, Arial",
        "color": "#f3f4f6"
    }

def default_theme():
    alt.themes.enable('none')
