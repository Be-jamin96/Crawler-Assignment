import logging

from crawler.models import GeoBlock

logger = logging.getLogger(__name__)


class GeoBlockRegistry:
    def __init__(self) -> None:
        self._blocks: dict[str, GeoBlock] = {}

    def add(self, block: GeoBlock) -> None:
        if block.page_url in self._blocks:
            return
        self._blocks[block.page_url] = block
        logger.warning("Geo-blocked page skipped (no proxy configured): %s requires region=%s", block.page_url, block.required_region)

    def all(self) -> list[GeoBlock]:
        return list(self._blocks.values())

    def report(self) -> str:
        if not self._blocks:
            return ""
        lines = ["Geo-blocked page(s) skipped — set VP_REGION_PROXY to a proxy in the required region to access them:"]
        for block in self._blocks.values():
            lines.append(f"  {block.page_url}  (requires region: {block.required_region})")
        return "\n".join(lines)
