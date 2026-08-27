"""Right-hand panel: a live grid of the crawl's URLs, colored by NodeState.

Dear PyGui's node_editor only supports drag-to-pan (unreliable over VNC) and
has no zoom at all, so a fast/wide crawl quickly outruns the visible area
with no way to see the rest. This uses a plain child window with real
horizontal + vertical scrollbars and manually-positioned boxes instead —
no edges, but dependable navigation. (Full URLs and history live in the
Activity Log below this panel.)
"""

import dearpygui.dearpygui as dpg

from crawler.events import NodeEvent, NodeState
from gui.theme import node_theme

_BOX_WIDTH = 150
_BOX_HEIGHT = 46
_COL_GAP = 14
_ROW_GAP = 8
_TEXT_COLOR = (10, 10, 10, 255)  # dark text reads on every state's bright background


class GraphView:
    def __init__(self) -> None:
        self._canvas_tag: str = ""
        self._box_tag_by_url: dict[str, str] = {}
        self._status_text_tag_by_url: dict[str, str] = {}
        self._next_row_by_depth: dict[int, int] = {}
        self._depth_by_url: dict[str, int] = {}

    def build(self, parent: str, height: int = -1) -> None:
        self._canvas_tag = parent
        dpg.add_child_window(
            tag=parent, height=height, horizontal_scrollbar=True, border=False
        )

    def reset(self) -> None:
        dpg.delete_item(self._canvas_tag, children_only=True)
        self._box_tag_by_url.clear()
        self._status_text_tag_by_url.clear()
        self._next_row_by_depth.clear()
        self._depth_by_url.clear()

    def apply(self, event: NodeEvent) -> None:
        if event.url not in self._box_tag_by_url:
            self._create_box(event)
        else:
            self._recolor_box(event)

    def _create_box(self, event: NodeEvent) -> None:
        box_tag = f"node_box::{event.url}"
        status_tag = f"node_status::{event.url}"

        depth = self._resolve_depth(event)
        row = self._next_row_by_depth.get(depth, 0)
        self._next_row_by_depth[depth] = row + 1
        pos = [depth * (_BOX_WIDTH + _COL_GAP), row * (_BOX_HEIGHT + _ROW_GAP)]

        label = _short_label(event.url, max_len=20)
        with dpg.child_window(
            tag=box_tag,
            parent=self._canvas_tag,
            pos=pos,
            width=_BOX_WIDTH,
            height=_BOX_HEIGHT,
            border=True,
            no_scrollbar=True,
        ):
            dpg.add_text(label, color=_TEXT_COLOR)
            dpg.add_text(
                f"[{event.type[:3]}] {event.state.value}",
                tag=status_tag,
                color=_TEXT_COLOR,
            )

        self._box_tag_by_url[event.url] = box_tag
        self._status_text_tag_by_url[event.url] = status_tag
        dpg.bind_item_theme(box_tag, node_theme(event.state))

    def _recolor_box(self, event: NodeEvent) -> None:
        box_tag = self._box_tag_by_url[event.url]
        status_tag = self._status_text_tag_by_url[event.url]
        # A password-found box keeps its gold highlight even if later re-processed.
        if event.state != NodeState.PASSWORD_FOUND and dpg.get_item_theme(
            box_tag
        ) == node_theme(NodeState.PASSWORD_FOUND):
            return
        dpg.set_value(status_tag, f"[{event.type[:3]}] {event.state.value}")
        dpg.bind_item_theme(box_tag, node_theme(event.state))

    def _resolve_depth(self, event: NodeEvent) -> int:
        if event.parent is not None and event.parent in self._depth_by_url:
            depth = self._depth_by_url[event.parent] + 1
        else:
            depth = 0
        self._depth_by_url[event.url] = depth
        return depth


def _short_label(url: str, max_len: int = 34) -> str:
    trimmed = url.split("://", 1)[-1]
    return trimmed if len(trimmed) <= max_len else trimmed[: max_len - 1] + "…"
