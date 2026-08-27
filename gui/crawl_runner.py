"""Runs a crawl on a background thread and streams NodeEvents to the GUI thread."""

import asyncio
import queue
import threading
from typing import Optional

from crawler.config import CrawlerConfig
from crawler.engine.crawl import run_crawl
from crawler.events import NodeEvent
from crawler.reporting.geo_blocks import GeoBlockRegistry
from crawler.reporting.store import PasswordStore


class CrawlRunner:
    """Owns at most one in-flight crawl. Not reentrant — check `is_running` before starting another."""

    def __init__(self) -> None:
        self.event_bus: "queue.Queue[NodeEvent]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self.result: Optional[tuple[PasswordStore, GeoBlockRegistry]] = None
        self.error: Optional[Exception] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, config: CrawlerConfig) -> None:
        if self.is_running:
            raise RuntimeError("A crawl is already running")

        self.result = None
        self.error = None

        def _run() -> None:
            try:
                self.result = asyncio.run(run_crawl(config, event_bus=self.event_bus))
            except Exception as e:  # surfaced to the GUI thread via `error`
                self.error = e

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def drain_events(self, max_events: int = 500) -> list[NodeEvent]:
        """Non-blocking drain, called once per GUI frame."""
        events = []
        for _ in range(max_events):
            try:
                events.append(self.event_bus.get_nowait())
            except queue.Empty:
                break
        return events
