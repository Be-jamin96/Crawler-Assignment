import logging

from crawler.extraction.patterns import normalize
from crawler.models import PasswordHit

logger = logging.getLogger(__name__)

# This target's own homepage (visible only via raw HTML source, since a JS
# snippet removes the rule from the rendered page) states: the worked example
# is never one of the eight, and any password whose only source is an HTTP
# response header is a "staging placeholder" and not qualified. Both rules
# are enforced here so disqualified entries never appear in the passwords
# list — the raw hit is still kept internally so debugging/logging can still
# see it arrived, just not counted or reported as a found password.
_WORKED_EXAMPLE = normalize("VISUALPING{0000deadbeef0000}")


def _is_qualified(key: str, hits: list[PasswordHit]) -> bool:
    if key == _WORKED_EXAMPLE:
        return False
    if all(hit.method == "header" for hit in hits):
        return False
    return True


class PasswordStore:
    def __init__(self) -> None:
        self._by_password: dict[str, list[PasswordHit]] = {}

    def add(self, hit: PasswordHit) -> None:
        key = normalize(hit.password)
        hits_before = self._by_password.get(key, [])
        was_qualified = _is_qualified(key, hits_before) if hits_before else False

        self._by_password.setdefault(key, []).append(hit)
        hits_after = self._by_password[key]

        if _is_qualified(key, hits_after):
            if not was_qualified:
                logger.info(
                    "New qualified password (%d total): %s first seen via method=%s location=%s url=%s",
                    self.unique_count,
                    key,
                    hit.method,
                    hit.location,
                    hit.source_url,
                )
        else:
            logger.debug(
                "Disqualified/decoy hit recorded (not counted): %s via method=%s url=%s",
                key,
                hit.method,
                hit.source_url,
            )

    def add_all(self, hits: list[PasswordHit]) -> None:
        for hit in hits:
            self.add(hit)

    @property
    def unique_count(self) -> int:
        return len(self.unique_passwords())

    def unique_passwords(self) -> list[str]:
        return [
            key for key, hits in self._by_password.items() if _is_qualified(key, hits)
        ]

    def hits_for(self, normalized_password: str) -> list[PasswordHit]:
        """Raw hit history for a password, including disqualified/decoy hits — for debugging."""
        return list(self._by_password.get(normalized_password, []))

    def report(self) -> str:
        qualified = self.unique_passwords()
        lines = [f"{len(qualified)} unique password(s) found:"]
        for key in qualified:
            hits = self._by_password[key]
            first = hits[0]
            lines.append(
                f"  {key}  (first seen: method={first.method} location={first.location} "
                f"url={first.source_url}; {len(hits)} total hit(s))"
            )
        report_text = "\n".join(lines)
        logger.info("Final report:\n%s", report_text)
        return report_text
