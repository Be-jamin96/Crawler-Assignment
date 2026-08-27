"""Left-side panel: live list of found passwords, plus a final qualified-passwords summary."""

import dearpygui.dearpygui as dpg

from crawler.events import NodeEvent
from crawler.reporting.store import PasswordStore

_LIST_TAG = "password_list"
_COUNTER_TAG = "password_counter"
_SUMMARY_TAG = "password_summary"

_EXPECTED_TOTAL = 8


class PasswordPanel:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def build(self, parent: str) -> None:
        with dpg.child_window(tag=parent, width=340, border=False):
            dpg.add_text("FOUND PASSWORDS", color=(255, 215, 0, 255))
            dpg.add_text(
                f"0/{_EXPECTED_TOTAL} found", tag=_COUNTER_TAG, color=(255, 215, 0, 255)
            )
            dpg.add_separator()
            dpg.add_child_window(tag=_LIST_TAG, height=-60, border=False)
            dpg.add_separator()
            dpg.add_text("", tag=_SUMMARY_TAG, wrap=320)

    def reset(self) -> None:
        self._seen.clear()
        dpg.delete_item(_LIST_TAG, children_only=True)
        dpg.set_value(_COUNTER_TAG, f"0/{_EXPECTED_TOTAL} found")
        dpg.set_value(_SUMMARY_TAG, "")

    def apply(self, event: NodeEvent) -> None:
        if event.hit is None:
            return
        key = event.hit.password
        if key in self._seen:
            return
        self._seen.add(key)
        dpg.set_value(_COUNTER_TAG, f"{len(self._seen)}/{_EXPECTED_TOTAL} found")
        with dpg.group(parent=_LIST_TAG):
            dpg.add_text(f"* {event.hit.password}", color=(255, 215, 0, 255))
            dpg.add_text(
                f"  via {event.hit.method} @ {event.hit.source_url}",
                color=(120, 255, 140, 180),
                wrap=320,
            )

    def show_final_summary(self, store: PasswordStore) -> None:
        qualified = store.unique_passwords()
        lines = [f"{len(qualified)}/8 qualified password(s):"]
        lines.extend(f"  {p}" for p in qualified)
        dpg.set_value(_SUMMARY_TAG, "\n".join(lines))
