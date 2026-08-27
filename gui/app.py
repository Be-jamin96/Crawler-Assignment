"""Top-level GUI wiring: window layout + frame loop. No crawler logic lives here."""

import logging
import time

import dearpygui.dearpygui as dpg

from crawler.config import CrawlerConfig
from crawler.logging_setup import configure_logging
from gui.activity_log import ActivityLog
from gui.crawl_runner import CrawlRunner
from gui.credentials_form import CredentialsForm
from gui.graph_view import GraphView
from gui.password_panel import PasswordPanel
from gui.theme import setup_global_theme

logger = logging.getLogger(__name__)

_LEFT_COLUMN_TAG = "left_column"
_RIGHT_COLUMN_TAG = "right_column"
_FORM_PANEL_TAG = "form_panel"
_PASSWORD_PANEL_TAG = "password_panel"
_GRAPH_PANEL_TAG = "graph_panel"
_LOG_PANEL_TAG = "log_panel"

_TARGET_FPS = 30


class App:
    def __init__(self) -> None:
        self._runner = CrawlRunner()
        self._graph = GraphView()
        self._passwords = PasswordPanel()
        self._log = ActivityLog()
        self._form = CredentialsForm(on_launch=self._launch_crawl)

    def _launch_crawl(self, config: CrawlerConfig) -> None:
        self._graph.reset()
        self._passwords.reset()
        self._log.reset()
        self._form.set_running(True)
        self._runner.start(config)

    def _poll(self) -> None:
        for event in self._runner.drain_events():
            self._graph.apply(event)
            self._passwords.apply(event)
            self._log.apply(event)

        if (
            self._form is not None
            and not self._runner.is_running
            and self._runner.result is not None
        ):
            store, geo_blocks = self._runner.result
            self._passwords.show_final_summary(store)
            geo_report = geo_blocks.report()
            self._form.set_status(geo_report if geo_report else "Crawl complete.")
            self._form.set_running(False)
            self._runner.result = None  # avoid re-showing the summary every frame
        elif self._runner.error is not None:
            self._form.set_status(f"Crawl failed: {self._runner.error}")
            self._form.set_running(False)
            self._runner.error = None

    def run(self) -> None:
        configure_logging("INFO")

        dpg.create_context()
        dpg.create_viewport(title="SIGNAL RECON — Crawler Ops", width=1400, height=850)
        setup_global_theme()

        with dpg.window(tag="root", label="Signal Recon"):
            with dpg.group(horizontal=True):
                with dpg.group(tag=_LEFT_COLUMN_TAG, width=340):
                    self._form.build(_FORM_PANEL_TAG)
                    self._passwords.build(_PASSWORD_PANEL_TAG)
                with dpg.group(tag=_RIGHT_COLUMN_TAG):
                    self._graph.build(_GRAPH_PANEL_TAG, height=-200)
                    self._log.build(_LOG_PANEL_TAG, height=190)

        dpg.set_primary_window("root", True)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        frame_interval = 1.0 / _TARGET_FPS
        while dpg.is_dearpygui_running():
            frame_start = time.perf_counter()
            self._poll()
            dpg.render_dearpygui_frame()
            elapsed = time.perf_counter() - frame_start
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)

        dpg.destroy_context()


def run() -> None:
    App().run()
