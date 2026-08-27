import asyncio
import contextlib
import logging
import queue as queue_module
from typing import Optional

import httpx

from crawler.config import CrawlerConfig
from crawler.engine.worker import worker
from crawler.events import NodeEvent, NodeState, emit
from crawler.models import QueuePayload
from crawler.reporting.geo_blocks import GeoBlockRegistry
from crawler.reporting.store import PasswordStore

logger = logging.getLogger(__name__)


async def run_crawl(
    config: CrawlerConfig, event_bus: "Optional[queue_module.Queue[NodeEvent]]" = None
) -> tuple[PasswordStore, GeoBlockRegistry]:
    queue: "asyncio.Queue[QueuePayload]" = asyncio.Queue()
    visited: set[str] = set()
    password_store = PasswordStore()
    geo_blocks = GeoBlockRegistry()
    stop_event = asyncio.Event()
    state = {"processed": 0}

    seed = QueuePayload(url=config.start_url, type="page", depth=0)
    emit(event_bus, NodeEvent(url=seed.url, type=seed.type, state=NodeState.DISCOVERED))
    await queue.put(seed)

    auth = httpx.BasicAuth(config.username, config.password)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)

    async with contextlib.AsyncExitStack() as stack:
        client = await stack.enter_async_context(
            httpx.AsyncClient(
                auth=auth,
                limits=limits,
                headers={"User-Agent": "VisualpingCandidateCrawler/2.0"},
            )
        )

        proxy_client = None
        if config.region_proxy:
            logger.info(
                "Region proxy configured — geo-blocked pages will be retried through it"
            )
            proxy_client = await stack.enter_async_context(
                httpx.AsyncClient(
                    auth=auth,
                    proxy=config.region_proxy,
                    headers={"User-Agent": "VisualpingCandidateCrawler/2.0"},
                )
            )

        workers = [
            asyncio.create_task(
                worker(
                    i,
                    queue,
                    visited,
                    client,
                    state,
                    stop_event,
                    password_store,
                    config,
                    proxy_client,
                    geo_blocks,
                    event_bus,
                )
            )
            for i in range(config.worker_count)
        ]

        queue_task = asyncio.create_task(queue.join())
        stop_task = asyncio.create_task(stop_event.wait())

        await asyncio.wait([queue_task, stop_task], return_when=asyncio.FIRST_COMPLETED)

        stop_event.set()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    logger.info(
        "Crawl complete: processed %d items, %d unique password(s) found",
        state["processed"],
        password_store.unique_count,
    )
    return password_store, geo_blocks
