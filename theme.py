# -*- coding: utf-8 -*-
"""
theme.py — QuickClick 暗色主题配色
"""

# 暗色极简
DARK_THEME = {
    "bg": "#121212",
    "card_bg": "#1a1a1a",
    "card_border": "#2a2a2a",
    "text_title": "#f0f0f0",
    "text_body": "#e0e0e0",
    "text_hint": "#888888",
    "accent": "#2563eb",
    "accent_dark": "#2a6bc4",
    "red": "#dc2626",
    "red_dark": "#b91c1c",
    "gray": "#888888",
    "gray_dark": "#666666",
    "btn_ghost_bg": "#252525",
    "btn_ghost_hover": "#2a2a2a",
    "radio_active_bg": "#1e3a5f",
    "radio_active_fg": "#3b82d4",
    "check_fill": "#3b82d4",
    "input_bg": "#222222",
    "input_border": "#333333",
    "macro_highlight": "#3b82d4",
    "status_text": "#666666",
}


def get_theme(name: str = "dark") -> dict:
    """返回主题配色（目前只有暗色）"""
    return DARK_THEME
