"""Bottom-right panel: a plain scrolling log of every event, in order.

The node graph is pannable but not zoomable, so a fast crawl can outrun the
visible viewport. This panel is the reliable way to see everything that
happened, regardless of where the graph is currently scrolled to.
"""

import dearpygui.dearpygui as dpg

from crawler.events import NodeEvent, NodeState
from gui.theme import NODE_COLORS

_LOG_TAG = "activity_log"
_MAX_LINES = 500


class ActivityLog:
    def __init__(self) -> None:
        self._line_count = 0

    def build(self, parent: str, height: int) -> None:
        with dpg.child_window(tag=parent, height=height, border=False):
            dpg.add_text("ACTIVITY LOG", color=(255, 215, 0, 255))
            dpg.add_separator()
            dpg.add_child_window(tag=_LOG_TAG, border=False)

    def reset(self) -> None:
        self._line_count = 0
        dpg.delete_item(_LOG_TAG, children_only=True)

    def apply(self, event: NodeEvent) -> None:
        dpg.add_text(
            f"[{event.state.value.upper():<15}] {event.url}",
            color=NODE_COLORS[event.state],
            parent=_LOG_TAG,
        )
        self._line_count += 1

        if self._line_count > _MAX_LINES:
            oldest = dpg.get_item_children(_LOG_TAG, slot=1)[0]
            dpg.delete_item(oldest)
            self._line_count -= 1

        dpg.set_y_scroll(_LOG_TAG, dpg.get_y_scroll_max(_LOG_TAG))
