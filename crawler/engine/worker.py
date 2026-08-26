import asyncio
import logging
from typing import Optional

import httpx

from crawler.config import CrawlerConfig
from crawler.engine.dispatch import dispatch_payload
from crawler.engine.geo import detect_geo_block
from crawler.engine.guards import is_depth_exceeded, is_pagination_trap
from crawler.models import GeoBlock, QueuePayload
from crawler.reporting.geo_blocks import GeoBlockRegistry
from crawler.reporting.store import PasswordStore

logger = logging.getLogger(__name__)


async def worker(
    worker_id: int,
    queue: "asyncio.Queue[QueuePayload]",
    visited: set[str],
    client: httpx.AsyncClient,
    state: dict,
    stop_event: asyncio.Event,
    password_store: PasswordStore,
    config: CrawlerConfig,
    proxy_client: Optional[httpx.AsyncClient] = None,
    geo_blocks: Optional[GeoBlockRegistry] = None,
) -> None:
    while not stop_event.is_set():
        try:
            payload: QueuePayload = await asyncio.wait_for(queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        try:
            if stop_event.is_set():
                break

            if payload.url in visited:
                continue

            # Claim immediately so other workers skip it while we process it.
            visited.add(payload.url)

            if is_depth_exceeded(payload, config) or is_pagination_trap(payload.url, config):
                continue

            logger.info("[worker %d] Fetching %s: %s", worker_id, payload.type, payload.url)
            response = await client.get(payload.url, follow_redirects=True, timeout=config.request_timeout)

            if response.status_code != 200:
                required_region = detect_geo_block(response)
                if required_region is not None:
                    if proxy_client is not None:
                        logger.info("[worker %d] Geo-blocked (%s), retrying via proxy: %s", worker_id, required_region, payload.url)
                        response = await proxy_client.get(payload.url, follow_redirects=True, timeout=config.request_timeout)
                        if response.status_code != 200:
                            logger.error("[worker %d] Proxy retry still failed (%d) for %s", worker_id, response.status_code, payload.url)
                            visited.discard(payload.url)
                            continue
                        # fall through to normal 200-path processing below
                    else:
                        if geo_blocks is not None:
                            geo_blocks.add(GeoBlock(page_url=payload.url, required_region=required_region))
                        visited.discard(payload.url)
                        continue
                else:
                    logger.warning("[worker %d] Failed %s with status %d", worker_id, payload.url, response.status_code)
                    visited.discard(payload.url)
                    continue

            state["processed"] += 1
            logger.info("[worker %d] Processed %d/%d: %s", worker_id, state["processed"], config.max_processed, payload.url)

            if state["processed"] >= config.max_processed:
                logger.info("Processed-item cap (%d) reached, signaling workers to stop", config.max_processed)
                stop_event.set()
                break

            hits, new_payloads = await dispatch_payload(payload, response, config)
            password_store.add_all(hits)

            for new_payload in new_payloads:
                new_payload.depth = (payload.depth or 0) + 1
                if new_payload.url not in visited and not stop_event.is_set():
                    await queue.put(new_payload)

        except httpx.RequestError as e:
            logger.error("[worker %d] Network error for %s: %s", worker_id, payload.url, e)
            visited.discard(payload.url)
        except Exception as e:
            logger.error("[worker %d] Unexpected error for %s: %s", worker_id, payload.url, e, exc_info=True)
            visited.discard(payload.url)
        finally:
            queue.task_done()
