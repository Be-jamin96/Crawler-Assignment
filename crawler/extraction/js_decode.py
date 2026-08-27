import logging
import re

from crawler.extraction.patterns import find_passwords
from crawler.models import AssetType, PasswordHit

logger = logging.getLogger(__name__)

# Matches JS array literals of >= 15 comma-separated integers — the shape used
# by e.g. `String.fromCharCode.apply(null, [86, 73, 83, ...])` to obfuscate a
# password as character codes instead of a literal string.
_CHAR_CODE_ARRAY = re.compile(r"\[\s*\d+(?:\s*,\s*\d+){14,}\s*\]")


def scan_char_code_arrays(
    text: str, source_url: str, payload_type: AssetType
) -> list[PasswordHit]:
    """Find JS numeric-array literals, decode them as char codes, and check
    the decoded text for a password (e.g. a `String.fromCharCode(...)` beacon)."""
    hits: list[PasswordHit] = []

    for match in _CHAR_CODE_ARRAY.finditer(text):
        numbers = [int(n) for n in re.findall(r"\d+", match.group(0))]
        if any(n > 0x10FFFF for n in numbers):
            continue
        try:
            decoded = "".join(chr(n) for n in numbers)
        except ValueError:
            continue

        passwords = find_passwords(decoded)
        for p in passwords:
            logger.info(
                "Password found: %s via method=js_char_code_array location=decoded_array url=%s",
                p,
                source_url,
            )
            hits.append(
                PasswordHit(
                    password=p,
                    source_url=source_url,
                    method="js_char_code_array",
                    location="decoded_array",
                    payload_type=payload_type,
                )
            )

    return hits
