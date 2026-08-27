"""Left-side panel: mission parameters (credentials, start URL, proxy) + Launch button."""

import os
from typing import Callable

import dearpygui.dearpygui as dpg
from dotenv import load_dotenv

from crawler.config import CrawlerConfig

# Pre-fill fields from .env (same VP_* vars crawler.config.load_config() reads)
# so values can be typed into VNC's clipboard-less GUI just once, in .env,
# instead of retyped into the form every launch.
load_dotenv()

_USERNAME_TAG = "form_username"
_PASSWORD_TAG = "form_password"
_START_URL_TAG = "form_start_url"
_PROXY_TAG = "form_proxy"
_WORKER_COUNT_TAG = "form_worker_count"
_REQUEST_DELAY_TAG = "form_request_delay"
_LAUNCH_BUTTON_TAG = "form_launch_button"
_STATUS_TAG = "form_status"


class CredentialsForm:
    def __init__(self, on_launch: Callable[[CrawlerConfig], None]) -> None:
        self._on_launch = on_launch

    def build(self, parent: str) -> None:
        with dpg.child_window(tag=parent, width=340, height=300, border=False):
            dpg.add_text("MISSION PARAMETERS", color=(255, 215, 0, 255))
            dpg.add_separator()
            dpg.add_input_text(
                label="Username",
                tag=_USERNAME_TAG,
                default_value=os.environ.get("VP_USERNAME", ""),
            )
            dpg.add_input_text(
                label="Password",
                tag=_PASSWORD_TAG,
                password=True,
                default_value=os.environ.get("VP_PASSWORD", ""),
            )
            dpg.add_input_text(
                label="Start URL",
                tag=_START_URL_TAG,
                default_value=os.environ.get("VP_START_URL", ""),
            )
            dpg.add_input_text(
                label="Proxy (geo-block retry only)",
                tag=_PROXY_TAG,
                default_value=os.environ.get("VP_REGION_PROXY", ""),
            )
            dpg.add_input_int(
                label="Workers",
                tag=_WORKER_COUNT_TAG,
                default_value=20,
                min_value=1,
                max_value=100,
            )
            dpg.add_slider_float(
                label="Delay (s)",
                tag=_REQUEST_DELAY_TAG,
                default_value=0.0,
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
            )
            dpg.add_button(
                label="LAUNCH CRAWL",
                tag=_LAUNCH_BUTTON_TAG,
                callback=self._handle_launch,
            )
            dpg.add_text("", tag=_STATUS_TAG, color=(220, 40, 40, 255))

    def set_running(self, running: bool) -> None:
        dpg.configure_item(
            _LAUNCH_BUTTON_TAG,
            enabled=not running,
            label="CRAWL IN PROGRESS…" if running else "LAUNCH CRAWL",
        )

    def set_status(self, message: str) -> None:
        dpg.set_value(_STATUS_TAG, message)

    def _handle_launch(self) -> None:
        start_url = dpg.get_value(_START_URL_TAG).strip()
        username = dpg.get_value(_USERNAME_TAG).strip()
        password = dpg.get_value(_PASSWORD_TAG)
        proxy = dpg.get_value(_PROXY_TAG).strip() or None
        worker_count = dpg.get_value(_WORKER_COUNT_TAG)
        request_delay = dpg.get_value(_REQUEST_DELAY_TAG)

        if not username or not password or not start_url:
            self.set_status("Username, password, and start URL are required.")
            return

        self.set_status("")
        config = CrawlerConfig(
            username=username,
            password=password,
            start_url=start_url,
            worker_count=worker_count,
            region_proxy=proxy,
            request_delay=request_delay,
        )
        self._on_launch(config)
