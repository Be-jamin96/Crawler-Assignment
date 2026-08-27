import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from crawler.extraction.js_decode import scan_char_code_arrays
from crawler.extraction.patterns import find_passwords
from crawler.models import AssetType, PasswordHit

logger = logging.getLogger(__name__)


def _hits(
    passwords: list[str],
    source_url: str,
    method: str,
    location: str,
    payload_type: AssetType,
) -> list[PasswordHit]:
    hits = [
        PasswordHit(
            password=p,
            source_url=source_url,
            method=method,
            location=location,
            payload_type=payload_type,
        )
        for p in passwords
    ]
    for hit in hits:
        logger.info(
            "Password found: %s via method=%s location=%s url=%s",
            hit.password,
            method,
            location,
            source_url,
        )
    return hits


def scan_raw_source(
    response: httpx.Response, payload_type: AssetType
) -> list[PasswordHit]:
    """Regex the unparsed response body — catches HTML comments, tag attributes,
    inline JSON/script bodies that BeautifulSoup's visible-text extraction strips."""
    source_url = str(response.url)
    passwords = find_passwords(response.text)
    logger.debug(
        "scan_raw_source: %d bytes scanned for %s", len(response.content), source_url
    )
    return _hits(passwords, source_url, "raw_source", "raw_source", payload_type)


def scan_visible_text(
    soup: BeautifulSoup, source_url: str, payload_type: AssetType
) -> list[PasswordHit]:
    passwords = find_passwords(soup.get_text())
    return _hits(passwords, source_url, "visible_text", "visible_text", payload_type)


def scan_headers_and_cookies(
    response: httpx.Response, payload_type: AssetType
) -> list[PasswordHit]:
    source_url = str(response.url)
    hits: list[PasswordHit] = []

    for header_name, header_value in response.headers.items():
        passwords = find_passwords(header_value)
        hits.extend(
            _hits(
                passwords, source_url, "header", f"header:{header_name}", payload_type
            )
        )

    for cookie_name, cookie_value in response.cookies.items():
        passwords = find_passwords(f"{cookie_name}={cookie_value}")
        hits.extend(
            _hits(
                passwords, source_url, "cookie", f"cookie:{cookie_name}", payload_type
            )
        )

    logger.debug(
        "scan_headers_and_cookies: scanned %d headers, %d cookies for %s",
        len(response.headers),
        len(response.cookies),
        source_url,
    )
    return hits


def scan_response_all(
    response: httpx.Response,
    payload_type: AssetType,
    soup: Optional[BeautifulSoup] = None,
) -> list[PasswordHit]:
    """One-stop scan: raw source + headers/cookies always, plus visible text if soup is given."""
    hits = scan_raw_source(response, payload_type)
    hits.extend(scan_headers_and_cookies(response, payload_type))
    hits.extend(scan_char_code_arrays(response.text, str(response.url), payload_type))
    if soup is not None:
        hits.extend(scan_visible_text(soup, str(response.url), payload_type))
    return hits
