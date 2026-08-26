import logging

from PIL import Image

from crawler.extraction.patterns import find_passwords
from crawler.models import PasswordHit

logger = logging.getLogger(__name__)


def _hits(passwords: list[str], source_url: str, method: str, location: str) -> list[PasswordHit]:
    result = [
        PasswordHit(password=p, source_url=source_url, method=method, location=location, payload_type="image")
        for p in passwords
    ]
    for hit in result:
        logger.info("Password found: %s via method=%s location=%s url=%s", hit.password, method, location, source_url)
    return result


def scan_raw_bytes(file_path: str, source_url: str) -> list[PasswordHit]:
    logger.info("Running pixel_scan.scan_raw_bytes on %s", file_path)
    with open(file_path, "rb") as f:
        raw_bytes = f.read()
    text_latin1 = raw_bytes.decode("latin-1", errors="ignore")
    return _hits(find_passwords(text_latin1), source_url, "pixel_scan", "raw bytes latin-1")


def scan_pil_info(file_path: str, source_url: str) -> list[PasswordHit]:
    logger.info("Running pixel_scan.scan_pil_info on %s", file_path)
    with Image.open(file_path) as img:
        return _hits(find_passwords(str(img.info)), source_url, "pixel_scan", "pil image.info")


def scan_pixel_dumps(file_path: str, source_url: str) -> list[PasswordHit]:
    logger.info("Running pixel_scan.scan_pixel_dumps on %s", file_path)
    hits: list[PasswordHit] = []

    with Image.open(file_path) as img:
        rgb_img = img.convert("RGB")
        pixels_row = list(rgb_img.getdata())
        width, height = rgb_img.size

        hex_row = "".join(f"{r:02x}{g:02x}{b:02x}" for r, g, b in pixels_row)
        hits.extend(_hits(find_passwords(hex_row), source_url, "pixel_scan", "row-order hex dump"))

        ascii_row = "".join(chr(val) for p in pixels_row for val in p)
        hits.extend(_hits(find_passwords(ascii_row), source_url, "pixel_scan", "row-order ascii dump"))

        pixels_col = [rgb_img.getpixel((x, y)) for x in range(width) for y in range(height)]

        hex_col = "".join(f"{r:02x}{g:02x}{b:02x}" for r, g, b in pixels_col)
        hits.extend(_hits(find_passwords(hex_col), source_url, "pixel_scan", "column-order hex dump"))

        ascii_col = "".join(chr(val) for p in pixels_col for val in p)
        hits.extend(_hits(find_passwords(ascii_col), source_url, "pixel_scan", "column-order ascii dump"))

    return hits


def scan_lsb_stego(file_path: str, source_url: str) -> list[PasswordHit]:
    logger.info("Running pixel_scan.scan_lsb_stego on %s", file_path)
    with Image.open(file_path) as img:
        rgb_img = img.convert("RGB")
        pixels_row = list(rgb_img.getdata())

    lsb_bits = [val & 1 for p in pixels_row for val in p]
    lsb_bytes = bytearray()
    for i in range(0, len(lsb_bits) - 7, 8):
        byte_val = 0
        for bit in lsb_bits[i : i + 8]:
            byte_val = (byte_val << 1) | bit
        lsb_bytes.append(byte_val)

    lsb_text = lsb_bytes.decode("latin-1", errors="ignore")
    return _hits(find_passwords(lsb_text), source_url, "pixel_scan", "lsb steganography")


def scan_all_pixel_strategies(file_path: str, source_url: str) -> list[PasswordHit]:
    """Fallback strategy bundle: raw bytes, PIL metadata, pixel dumps, LSB stego."""
    hits: list[PasswordHit] = []
    hits.extend(scan_raw_bytes(file_path, source_url))
    hits.extend(scan_pil_info(file_path, source_url))
    hits.extend(scan_pixel_dumps(file_path, source_url))
    hits.extend(scan_lsb_stego(file_path, source_url))
    return hits
