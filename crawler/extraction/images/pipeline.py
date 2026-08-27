import logging
import os
from urllib.parse import urlparse

import httpx

from crawler.config import CrawlerConfig
from crawler.extraction.images.exif_scan import scan_exif
from crawler.extraction.images.ocr_scan import scan_ocr
from crawler.extraction.images.pixel_scan import scan_all_pixel_strategies
from crawler.models import PasswordHit

logger = logging.getLogger(__name__)


def _save_image(response: httpx.Response, download_dir: str) -> str | None:
    filename = os.path.basename(urlparse(str(response.url)).path) or "unnamed"
    save_path = os.path.join(download_dir, filename)
    try:
        os.makedirs(download_dir, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)
        logger.debug("Saved image %s -> %s", response.url, save_path)
        return save_path
    except OSError as e:
        logger.error("Failed to save image %s: %s", response.url, e)
        return None


# AI vision API is a stub (crawler.extraction.images.vision_stub) — deliberately
# not included here until API key handling is added.
_STRATEGIES = [
    ("exiftool", scan_exif),
    ("ocr", scan_ocr),
    ("pixel_scan", scan_all_pixel_strategies),
]


async def parse_image(
    response: httpx.Response, page_url: str, config: CrawlerConfig
) -> list[PasswordHit]:
    """Download the image and run each analysis strategy independently, so one
    failing strategy (e.g. exiftool missing) can't suppress the others' results."""
    save_path = _save_image(response, config.download_dir)
    if save_path is None:
        return []

    source_url = str(response.url)
    hits: list[PasswordHit] = []

    for name, strategy in _STRATEGIES:
        try:
            hits.extend(strategy(save_path, source_url))
        except Exception as e:
            logger.error(
                "Image strategy '%s' failed for %s: %s",
                name,
                save_path,
                e,
                exc_info=True,
            )

    logger.info("parse_image complete for %s: %d total hit(s)", save_path, len(hits))
    return hits
