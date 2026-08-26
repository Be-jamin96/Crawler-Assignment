import logging
import re

logger = logging.getLogger(__name__)

PASSWORD_PATTERN = re.compile(r"VISUALPING\{[0-9a-f]{16}\}", re.IGNORECASE)


def find_passwords(text: str) -> list[str]:
    """Return every full VISUALPING{...} match in text, case-insensitive, as matched."""
    if not text:
        return []
    matches = PASSWORD_PATTERN.findall(text)
    if matches:
        logger.debug("find_passwords matched %d password(s)", len(matches))
    return matches


def normalize(password: str) -> str:
    """Canonical dedupe key: uppercase VISUALPING literal, lowercase hex."""
    inner = password[password.index("{") + 1 : password.index("}")]
    return "VISUALPING{" + inner.lower() + "}"
