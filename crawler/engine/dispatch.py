import logging

import httpx
from bs4 import BeautifulSoup

from crawler.config import CrawlerConfig
from crawler.extraction.css_links import extract_css_url_refs
from crawler.extraction.images.pipeline import parse_image
from crawler.extraction.js_links import extract_js_link_refs
from crawler.extraction.link_discovery import extract_all_links
from crawler.extraction.text_scan import scan_headers_and_cookies, scan_response_all
from crawler.models import PasswordHit, QueuePayload

logger = logging.getLogger(__name__)


async def dispatch_payload(
    payload: QueuePayload,
    response: httpx.Response,
    config: CrawlerConfig,
) -> tuple[list[PasswordHit], list[QueuePayload]]:
    logger.debug("Dispatching %s payload: %s", payload.type, payload.url)

    if payload.type == "page":
        soup = BeautifulSoup(response.text, "html.parser")
        hits = scan_response_all(response, payload.type, soup=soup)
        new_payloads = extract_all_links(soup, payload.url)
        return hits, new_payloads

    if payload.type == "script":
        hits = scan_response_all(response, payload.type)
        new_payloads = extract_js_link_refs(response.text, payload.url)
        return hits, new_payloads

    if payload.type == "css":
        hits = scan_response_all(response, payload.type)
        new_payloads = extract_css_url_refs(response.text, payload.url)
        return hits, new_payloads

    if payload.type == "image":
        # Don't decode binary image content as text (scan_raw_source) — pixel_scan
        # handles raw-byte scanning with a correctly-labeled latin-1 decode instead.
        header_hits = scan_headers_and_cookies(response, payload.type)
        image_hits = await parse_image(response, payload.url, config)
        return header_hits + image_hits, []

    logger.warning("Unknown payload type %s for %s", payload.type, payload.url)
    return [], []
