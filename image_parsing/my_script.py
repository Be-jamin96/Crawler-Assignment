import re
from PIL import Image

PATTERN = re.compile(r"VISUALPING\{[0-9a-fA-F]{16}\}", re.IGNORECASE)


def scan_text(text: str, label: str) -> bool:
    matches = PATTERN.findall(text)
    if matches:
        for match in set(matches):
            print(f"  [FOUND] {match} ---> Method: {label}")
        return True
    return False


def analyze_image(file_path: str):
    print(
        f"\n========================================\nAnalyzing: {file_path}\n========================================")
    found = False

    # Step 1: Raw Bytes & File Trailer Scan
    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    text_latin1 = raw_bytes.decode("latin-1", errors="ignore")
    if scan_text(text_latin1, "Raw Binary / Metadata Chunks / Trailing Data"):
        found = True

    # Step 2: Pillow Structural & Pixel Analysis
    try:

        import subprocess

        result = subprocess.run(
            ["exiftool", file_path],
            capture_output=True,
            text=True
        )
        scan_text(result.stdout, "ExifTool Metadata")

        with Image.open(file_path) as img:
            # Check PIL metadata dictionary
            print(img.info)
            if scan_text(str(img.info), "PIL Image Info Metadata"):
                found = True

            rgb_img = img.convert("RGB")
            pixels_row = list(rgb_img.getdata())
            width, height = rgb_img.size

            # Step 3A: Row-by-Row RGB to Hex / ASCII
            hex_row = "".join(f"{r:02x}{g:02x}{b:02x}" for r, g, b in pixels_row)
            if scan_text(hex_row, "Pixel RGB Hex (Row Order)"):
                found = True

            ascii_row = "".join(chr(val) for p in pixels_row for val in p)
            if scan_text(ascii_row, "Pixel RGB Bytes (Row Order)"):
                found = True

            # Step 3B: Column-by-Column RGB to Hex / ASCII
            pixels_col = [rgb_img.getpixel((x, y)) for x in range(width) for y in range(height)]

            hex_col = "".join(f"{r:02x}{g:02x}{b:02x}" for r, g, b in pixels_col)
            if scan_text(hex_col, "Pixel RGB Hex (Column Order)"):
                found = True

            ascii_col = "".join(chr(val) for p in pixels_col for val in p)
            if scan_text(ascii_col, "Pixel RGB Bytes (Column Order)"):
                found = True

            # Step 4: LSB Steganography
            lsb_bits = [bit for p in pixels_row for val in p for bit in (val & 1,)]
            lsb_bytes = bytearray()
            for i in range(0, len(lsb_bits) - 7, 8):
                byte_val = 0
                for bit in lsb_bits[i:i + 8]:
                    byte_val = (byte_val << 1) | bit
                lsb_bytes.append(byte_val)

            lsb_text = lsb_bytes.decode("latin-1", errors="ignore")
            if scan_text(lsb_text, "LSB Steganography"):
                found = True

    except Exception as e:
        print(f"Error opening image: {e}")

    if not found:
        print("  [-] No flag matched in standard checks.")


# Run against local files
if __name__ == "__main__":
    image_files = ["pattern1.png", "pattern2.png", "pattern3.jpg"]
    for img_file in image_files:
        analyze_image(img_file)