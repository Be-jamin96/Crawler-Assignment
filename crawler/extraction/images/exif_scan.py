import logging
import re
import subprocess

from crawler.extraction.patterns import find_passwords
from crawler.models import PasswordHit

logger = logging.getLogger(__name__)

_EXIFTOOL_FIELD_LINE = re.compile(r"^(.+?)\s*:\s*(.*)$")


def scan_exif(file_path: str, source_url: str) -> list[PasswordHit]:
    """Run the exiftool CLI over the image and regex its output for passwords,
    attributing each hit to the specific EXIF field name it came from."""
    logger.info("Running exif_scan on %s", file_path)
    hits: list[PasswordHit] = []

    try:
        result = subprocess.run(
            ["exiftool", file_path], capture_output=True, text=True, timeout=30
        )
    except FileNotFoundError:
        logger.error("exiftool binary not found on PATH — skipping exif_scan for %s", file_path)
        return hits
    except subprocess.TimeoutExpired:
        logger.error("exiftool timed out for %s", file_path)
        return hits

    for line in result.stdout.splitlines():
        match = _EXIFTOOL_FIELD_LINE.match(line)
        field_name = match.group(1).strip() if match else "exiftool_stdout"
        passwords = find_passwords(line)
        for p in passwords:
            logger.info("Password found: %s via method=exiftool location=%s url=%s", p, field_name, source_url)
            hits.append(
                PasswordHit(password=p, source_url=source_url, method="exiftool", location=field_name, payload_type="image")
            )

    logger.info("exif_scan complete for %s: %d hit(s)", file_path, len(hits))
    return hits
