import logging
import re

import pytesseract
from PIL import Image, ImageOps

from crawler.extraction.patterns import find_passwords
from crawler.models import PasswordHit

logger = logging.getLogger(__name__)

# Loose match: same shape as the real token but tolerant of OCR character
# confusion in the hex run (e.g. '1'/'l'/'I', '0'/'O', '5'/'S').
_LOOSE_TOKEN = re.compile(r"VISUALPING\{([0-9a-zA-Z]{16})\}", re.IGNORECASE)
_HEX_CONFUSION_FIXES = str.maketrans({"l": "1", "I": "1", "O": "0", "o": "0", "S": "5"})

# Restricting tesseract's character set to what the token can contain removes
# most of this ambiguity outright.
_WHITELIST_CONFIG = (
    "-c tessedit_char_whitelist=VISUALPINGvisualping{}0123456789abcdefABCDEF"
)


def _fuzzy_correct(text: str) -> list[str]:
    """Find near-matches for the token and correct common OCR hex-digit confusion."""
    corrected = []
    for match in _LOOSE_TOKEN.finditer(text):
        hex_part = match.group(1).translate(_HEX_CONFUSION_FIXES)
        corrected.append(f"VISUALPING{{{hex_part}}}")
    return corrected


def _hits(passwords: list[str], source_url: str, location: str) -> list[PasswordHit]:
    result = [
        PasswordHit(
            password=p,
            source_url=source_url,
            method="ocr",
            location=location,
            payload_type="image",
        )
        for p in passwords
    ]
    for hit in result:
        logger.info(
            "Password found: %s via method=ocr location=%s url=%s",
            hit.password,
            location,
            source_url,
        )
    return result


def _run_variant(
    image: Image.Image, source_url: str, label: str, config: str = ""
) -> list[PasswordHit]:
    text = pytesseract.image_to_string(image, config=config)
    passwords = find_passwords(text)
    if not passwords:
        # Fall back to fuzzy-correcting near-matches (fixes 1/l/I, 0/O, 5/S confusion).
        passwords = find_passwords(" ".join(_fuzzy_correct(text)))
        if passwords:
            label = f"{label}_fuzzy_corrected"
    return _hits(passwords, source_url, label)


def scan_ocr(file_path: str, source_url: str) -> list[PasswordHit]:
    """OCR the image for rendered/visible password text, trying a couple of
    preprocessing variants since low-contrast text can trip up raw OCR."""
    logger.info("Running ocr_scan on %s", file_path)
    hits: list[PasswordHit] = []

    try:
        with Image.open(file_path) as img:
            hits.extend(_run_variant(img, source_url, "ocr_raw"))
            hits.extend(
                _run_variant(img, source_url, "ocr_raw_whitelist", _WHITELIST_CONFIG)
            )

            grayscale = ImageOps.grayscale(img)
            hits.extend(_run_variant(grayscale, source_url, "ocr_grayscale"))
            hits.extend(
                _run_variant(
                    grayscale, source_url, "ocr_grayscale_whitelist", _WHITELIST_CONFIG
                )
            )

            threshold = grayscale.point(lambda p: 255 if p > 128 else 0)
            hits.extend(_run_variant(threshold, source_url, "ocr_threshold"))
    except pytesseract.TesseractNotFoundError:
        logger.error(
            "tesseract binary not found on PATH — skipping ocr_scan for %s", file_path
        )
    except Exception as e:
        logger.error("ocr_scan failed for %s: %s", file_path, e, exc_info=True)

    logger.info("ocr_scan complete for %s: %d hit(s)", file_path, len(hits))
    return hits
