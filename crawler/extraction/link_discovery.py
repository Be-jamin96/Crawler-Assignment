import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.extraction.css_links import extract_css_url_refs
from crawler.models import QueuePayload

logger = logging.getLogger(__name__)

_META_REFRESH_URL = re.compile(r"url\s*=\s*['\"]?([^'\";]+)", re.IGNORECASE)


def _from_srcset(srcset: str, page_url: str) -> list[str]:
    """Parse a srcset attribute ('a.jpg 1x, b.jpg 2x') into resolved URLs."""
    urls = []
    for candidate in srcset.split(","):
        candidate = candidate.strip()
        if not candidate:
            continue
        url_part = candidate.split()[0]
        urls.append(urljoin(page_url, url_part))
    return urls


def extract_page_links(soup: BeautifulSoup, page_url: str) -> list[QueuePayload]:
    urls = [urljoin(page_url, a["href"]) for a in soup.find_all("a", href=True)]
    return [QueuePayload(url=u, type="page", parent=page_url) for u in urls]


def extract_script_links(soup: BeautifulSoup, page_url: str) -> list[QueuePayload]:
    urls = [urljoin(page_url, s["src"]) for s in soup.find_all("script", src=True)]
    return [QueuePayload(url=u, type="script", parent=page_url) for u in urls]


def extract_css_links(soup: BeautifulSoup, page_url: str) -> list[QueuePayload]:
    urls = [
        urljoin(page_url, link["href"])
        for link in soup.find_all("link", rel="stylesheet", href=True)
    ]
    return [QueuePayload(url=u, type="css", parent=page_url) for u in urls]


def extract_image_links(soup: BeautifulSoup, page_url: str) -> list[QueuePayload]:
    payloads = []

    for img in soup.find_all("img"):
        if img.get("src"):
            payloads.append(
                QueuePayload(
                    url=urljoin(page_url, img["src"]), type="image", parent=page_url
                )
            )
        if img.get("srcset"):
            for u in _from_srcset(img["srcset"], page_url):
                payloads.append(QueuePayload(url=u, type="image", parent=page_url))

    for source in soup.find_all("source"):
        if source.get("src"):
            payloads.append(
                QueuePayload(
                    url=urljoin(page_url, source["src"]), type="image", parent=page_url
                )
            )
        if source.get("srcset"):
            for u in _from_srcset(source["srcset"], page_url):
                payloads.append(QueuePayload(url=u, type="image", parent=page_url))

    return payloads


def extract_misc_links(soup: BeautifulSoup, page_url: str) -> list[QueuePayload]:
    payloads = []

    for iframe in soup.find_all("iframe", src=True):
        payloads.append(
            QueuePayload(
                url=urljoin(page_url, iframe["src"]), type="page", parent=page_url
            )
        )

    for link in soup.find_all("link", href=True):
        rel = " ".join(link.get("rel", [])).lower()
        if "icon" in rel or "manifest" in rel:
            payloads.append(
                QueuePayload(
                    url=urljoin(page_url, link["href"]), type="image", parent=page_url
                )
            )
        elif "alternate" in rel:
            payloads.append(
                QueuePayload(
                    url=urljoin(page_url, link["href"]), type="page", parent=page_url
                )
            )

    for meta in soup.find_all("meta", attrs={"http-equiv": True}):
        if meta.get("http-equiv", "").lower() != "refresh":
            continue
        content = meta.get("content", "")
        match = _META_REFRESH_URL.search(content)
        if match:
            payloads.append(
                QueuePayload(
                    url=urljoin(page_url, match.group(1).strip()),
                    type="page",
                    parent=page_url,
                )
            )

    return payloads


def extract_inline_style_css_links(
    soup: BeautifulSoup, page_url: str
) -> list[QueuePayload]:
    payloads = []
    for style_tag in soup.find_all("style"):
        css_text = style_tag.string or ""
        payloads.extend(extract_css_url_refs(css_text, page_url))
    return payloads


def extract_all_links(soup: BeautifulSoup, page_url: str) -> list[QueuePayload]:
    payloads = (
        extract_page_links(soup, page_url)
        + extract_script_links(soup, page_url)
        + extract_css_links(soup, page_url)
        + extract_image_links(soup, page_url)
        + extract_misc_links(soup, page_url)
        + extract_inline_style_css_links(soup, page_url)
    )

    seen = set()
    deduped = []
    for p in payloads:
        key = (p.url, p.type)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    logger.debug(
        "extract_all_links: %d unique link(s) discovered on %s", len(deduped), page_url
    )
    return deduped
