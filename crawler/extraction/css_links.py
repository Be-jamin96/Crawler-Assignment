import logging
import re
from urllib.parse import urljoin

from crawler.models import QueuePayload

logger = logging.getLogger(__name__)

_URL_REF_PATTERN = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", re.IGNORECASE)
_IMPORT_PATTERN = re.compile(r"@import\s+(?:url\(\s*)?['\"]?([^'\")\s;]+)['\"]?\s*\)?", re.IGNORECASE)


def extract_css_url_refs(css_text: str, css_url: str) -> list[QueuePayload]:
    """Extract url(...) and @import references from CSS text (fetched .css files or inline <style> blocks)."""
    payloads: list[QueuePayload] = []

    for match in _URL_REF_PATTERN.finditer(css_text):
        ref = match.group(1).strip()
        if ref.startswith("data:"):
            continue
        resolved = urljoin(css_url, ref)
        payloads.append(QueuePayload(url=resolved, type="image", parent=css_url))

    for match in _IMPORT_PATTERN.finditer(css_text):
        ref = match.group(1).strip()
        resolved = urljoin(css_url, ref)
        payloads.append(QueuePayload(url=resolved, type="css", parent=css_url))

    logger.debug("extract_css_url_refs: found %d url()/@import ref(s) in %s", len(payloads), css_url)
    return payloads
