"""
flesh out the parsers for different asset types (html, css, js, images) and extract any relevant information (like passwords) from them.
"""

import os
import re
from urllib.parse import urljoin
import httpx
from PIL import Image
from bs4 import BeautifulSoup
from urllib3.util import url

from SCRATCH.constants import PASSWORD_PATTERN, ASSET_TYPES

from models import QueuePayload

def regex_text_for_passwords(text: str):
    """ Regex the text for passwords and return a list of matches. """
    password_matches = re.findall(PASSWORD_PATTERN, text, re.IGNORECASE)
    return password_matches

def create_payloads_from_urls(urls: list, payload_type: ASSET_TYPES, page_url: str):
    """ Create a list of QueuePayloads from a list of URLs and a specified type. """
    return [QueuePayload(url=url, type=payload_type, parent=page_url) for url in urls]

def scrape_asset_for_passwords(response: httpx.Response):
    """ Generic helper to scrape a response for passwords using regex. Returns a list of found passwords. """
    soup = BeautifulSoup(response.text, "html.parser")

    # geo-check - This page is only visible to Germany region.
    if "geo-check" in soup.text.lower():
        print("\n\n\n\n------")
        print(f"[-] Geo-check detected in {response.url}. Skipping further processing.")
        return [], soup


    # regex the text for passwords
    passwords = regex_text_for_passwords(soup.text)
    if passwords:
        print(f"-> Found {len(passwords)} password(s) in {response.url}: {passwords}")

    return passwords, soup


def parse_html_page(response: httpx.Response, page_url: str):
    """ Parse a page and return a list of new QueuePayloads for scripts, css, and images found on the page. """

    passwords, soup = scrape_asset_for_passwords(response)

    payloads = []

    # extract the links to new pages, scripts, css, and images from the page
    extracted_page_urls = [urljoin(page_url, a_tag['href']) for a_tag in soup.find_all("a", href=True)]
    payloads.extend(create_payloads_from_urls(extracted_page_urls, "page", page_url))

    extracted_script_urls = [urljoin(page_url, script_tag['src']) for script_tag in soup.find_all("script", src=True)]
    payloads.extend(create_payloads_from_urls(extracted_script_urls, "script", page_url))

    extracted_style_urls = [urljoin(page_url, link_tag['href']) for link_tag in soup.find_all("link", rel="stylesheet", href=True)]
    payloads.extend(create_payloads_from_urls(extracted_style_urls, "css", page_url))

    extracted_image_urls = [urljoin(page_url, img_tag['src']) for img_tag in soup.find_all("img", src=True)]
    payloads.extend(create_payloads_from_urls(extracted_image_urls, "image", page_url))

    return passwords, payloads

def parse_image(response: httpx.Response, page_url: str):
    """ Download an image and use AI api to analyse it for passwords. """

    def save_image(image_response: httpx.Response, save_path: str) -> str:
        """Saves the already-downloaded (authenticated) image response to disk."""
        try:
            print(f"\n[+] Saving image from: {image_response.url}")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(image_response.content)
            print(f"    Saved successfully as: {save_path}")
            return save_path
        except Exception as e:
            print(f"    [-] Failed to save {image_response.url}: {e}")
            return None

    # todo replace this
    def scan_text(text: str, label: str) -> list:
        matches = PASSWORD_PATTERN.findall(text)
        if matches:
            for match in set(matches):
                print(f"  [FOUND] {match} ---> Method: {label}")
            return matches
        return []

    def analyze_image(file_path: str):
        passwords = []
        # Step 1: Raw Bytes & File Trailer Scan
        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        text_latin1 = raw_bytes.decode("latin-1", errors="ignore")
        passwords.extend(scan_text(text_latin1, "Raw Binary / Metadata Chunks / Trailing Data"))

        # Step 2: Pillow Structural & Pixel Analysis
        try:
            import subprocess

            result = subprocess.run(
                ["exiftool", file_path],
                capture_output=True,
                text=True
            )
            extracted_passwords = regex_text_for_passwords(result.stdout)
            if extracted_passwords:
                print(f"  [FOUND] {extracted_passwords} ---> Method: ExifTool Metadata")
                passwords.extend(extracted_passwords)

            with Image.open(file_path) as img:
                # Check PIL metadata dictionary
                extracted_passwords = regex_text_for_passwords(str(img.info))
                if extracted_passwords:
                    print(f"  [FOUND] {extracted_passwords} ---> Method: PIL Image Info Metadata")
                    passwords.extend(extracted_passwords)

                rgb_img = img.convert("RGB")
                pixels_row = list(rgb_img.getdata())
                width, height = rgb_img.size

                # Step 3A: Row-by-Row RGB to Hex / ASCII
                hex_row = "".join(f"{r:02x}{g:02x}{b:02x}" for r, g, b in pixels_row)
                extracted_passwords = regex_text_for_passwords(hex_row)
                if extracted_passwords:
                    print(f"  [FOUND] {extracted_passwords} ---> Method: Pixel RGB Hex (Row Order)")
                    passwords.extend(extracted_passwords)

                ascii_row = "".join(chr(val) for p in pixels_row for val in p)
                extracted_passwords = regex_text_for_passwords(ascii_row)
                if extracted_passwords:
                    print(f"  [FOUND] {extracted_passwords} ---> Method: Pixel RGB Bytes (Row Order)")
                    passwords.extend(extracted_passwords)

                # Step 3B: Column-by-Column RGB to Hex / ASCII
                pixels_col = [rgb_img.getpixel((x, y)) for x in range(width) for y in range(height)]

                hex_col = "".join(f"{r:02x}{g:02x}{b:02x}" for r, g, b in pixels_col)
                extracted_passwords = regex_text_for_passwords(hex_col)
                if extracted_passwords:
                    print(f"  [FOUND] {extracted_passwords} ---> Method: Pixel RGB Hex (Column Order)")
                    passwords.extend(extracted_passwords)

                ascii_col = "".join(chr(val) for p in pixels_col for val in p)
                extracted_passwords = regex_text_for_passwords(ascii_col)
                if extracted_passwords:
                    print(f"  [FOUND] {extracted_passwords} ---> Method: Pixel RGB Bytes (Column Order)")
                    passwords.extend(extracted_passwords)

                # Step 4: LSB Steganography
                lsb_bits = [bit for p in pixels_row for val in p for bit in (val & 1,)]
                lsb_bytes = bytearray()
                for i in range(0, len(lsb_bits) - 7, 8):
                    byte_val = 0
                    for bit in lsb_bits[i:i + 8]:
                        byte_val = (byte_val << 1) | bit
                    lsb_bytes.append(byte_val)

                lsb_text = lsb_bytes.decode("latin-1", errors="ignore")
                extracted_passwords = regex_text_for_passwords(lsb_text)
                if extracted_passwords:
                    print(f"  [FOUND] {extracted_passwords} ---> Method: LSB Steganography")
                    passwords.extend(extracted_passwords)

        except Exception as e:
            print(f"Error opening image: {e}")

        if not passwords:
            print("  [-] No flag matched in standard checks.")
        return passwords

    save_path = save_image(response, save_path=f"downloaded_images/{str(response.url).split('/')[-1]}")
    if save_path is None:
        return []
    return analyze_image(save_path)
