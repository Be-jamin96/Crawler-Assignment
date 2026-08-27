"""Spy-ops visual theme: dark background, phosphor-green text, per-state node colors."""

import dearpygui.dearpygui as dpg

from crawler.events import NodeState

BACKGROUND = (10, 14, 10, 255)
PANEL_BACKGROUND = (16, 20, 16, 255)
TEXT_PRIMARY = (120, 255, 140, 255)
TEXT_DIM = (70, 140, 80, 255)
ACCENT = (255, 200, 60, 255)
DANGER = (220, 40, 40, 255)

NODE_COLORS = {
    NodeState.DISCOVERED: (90, 160, 220, 255),  # recon blue
    NodeState.PROCESSING: (255, 165, 0, 255),  # active orange
    NodeState.PROCESSED: (60, 200, 90, 255),  # cleared green
    NodeState.FAILED: (200, 40, 40, 255),  # compromised red
    NodeState.PASSWORD_FOUND: (255, 215, 0, 255),  # gold — high-value target
}

_node_themes: dict[NodeState, int] = {}


def setup_global_theme() -> None:
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BACKGROUND)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, PANEL_BACKGROUND)
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT_PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (20, 60, 30, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (30, 90, 45, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (18, 28, 18, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (20, 60, 30, 255))
    dpg.bind_theme(global_theme)


def node_theme(state: NodeState) -> int:
    """Return a cached theme id (background color) for a node lifecycle state, creating it on first use."""
    if state not in _node_themes:
        with dpg.theme() as theme_id:
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, NODE_COLORS[state])
                dpg.add_theme_color(dpg.mvThemeCol_Border, (255, 255, 255, 80))
        _node_themes[state] = theme_id
    return _node_themes[state]
