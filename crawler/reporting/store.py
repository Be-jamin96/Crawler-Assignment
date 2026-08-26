import logging

from crawler.extraction.patterns import normalize
from crawler.models import PasswordHit

logger = logging.getLogger(__name__)


class PasswordStore:
    def __init__(self) -> None:
        self._by_password: dict[str, list[PasswordHit]] = {}

    def add(self, hit: PasswordHit) -> None:
        key = normalize(hit.password)
        is_new = key not in self._by_password
        self._by_password.setdefault(key, []).append(hit)
        if is_new:
            logger.info(
                "New unique password (%d total): %s first seen via method=%s location=%s url=%s",
                len(self._by_password), key, hit.method, hit.location, hit.source_url,
            )

    def add_all(self, hits: list[PasswordHit]) -> None:
        for hit in hits:
            self.add(hit)

    @property
    def unique_count(self) -> int:
        return len(self._by_password)

    def unique_passwords(self) -> list[str]:
        return list(self._by_password.keys())

    def hits_for(self, normalized_password: str) -> list[PasswordHit]:
        return list(self._by_password.get(normalized_password, []))

    def report(self) -> str:
        lines = [f"{self.unique_count} unique password(s) found:"]
        for key, hits in self._by_password.items():
            first = hits[0]
            lines.append(
                f"  {key}  (first seen: method={first.method} location={first.location} "
                f"url={first.source_url}; {len(hits)} total hit(s))"
            )
        report_text = "\n".join(lines)
        logger.info("Final report:\n%s", report_text)
        return report_text
