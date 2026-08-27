import logging
import re

from crawler.config import CrawlerConfig
from crawler.models import QueuePayload

logger = logging.getLogger(__name__)

PAGINATION_PATTERN = re.compile(r"page=(\d+)")


def is_depth_exceeded(payload: QueuePayload, config: CrawlerConfig) -> bool:
    if payload.depth is not None and payload.depth >= config.depth_cutoff:
        logger.info(
            "Depth cutoff reached (depth=%s) for %s", payload.depth, payload.url
        )
        return True
    return False


def is_pagination_trap(url: str, config: CrawlerConfig) -> bool:
    page_numbers = [int(m) for m in PAGINATION_PATTERN.findall(url)]
    for page_number in page_numbers:
        if page_number >= config.pagination_cutoff:
            logger.info("Pagination trap detected (page=%d) for %s", page_number, url)
            return True
    return False
