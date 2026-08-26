import logging
import re
from urllib.parse import urljoin

from crawler.models import QueuePayload

logger = logging.getLogger(__name__)

# Matches JS object literal fields like `path: "/docs/foo/"` or `href: '/bar'`
# — the shape used to build DOM-injected navigation (e.g. document.createElement('a'))
# that never appears as a literal <a href> in the HTML source.
_JS_PATH_FIELD = re.compile(r"""\b(?:path|href|url)\s*:\s*["']([^"']+)["']""")


def extract_js_link_refs(js_text: str, script_url: str) -> list[QueuePayload]:
    """Extract site-relative path references from JS object literals — catches
    links a real browser would follow after JS runs but that never exist as
    an <a href> in the static HTML source."""
    payloads = []
    for match in _JS_PATH_FIELD.finditer(js_text):
        ref = match.group(1).strip()
        if not ref.startswith("/") and not ref.startswith("http"):
            continue
        resolved = urljoin(script_url, ref)
        payloads.append(QueuePayload(url=resolved, type="page", parent=script_url))

    if payloads:
        logger.debug("extract_js_link_refs: found %d JS-embedded link ref(s) in %s", len(payloads), script_url)
    return payloads
