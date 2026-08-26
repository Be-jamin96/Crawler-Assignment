"""
Naturally ensure we have a working regex for the VISUALPING{...} pattern
"""

import re
pattern = r"VISUALPING\{([0-9a-f]{16})\}"

test_string = "Hello<somethi!#VISUALPINGtestmissingVISUALPING{0000deadbeef0000}some_other_textVISUALPING{0000deadbeef00}more_text "

# run the regex
matches = re.findall(pattern, test_string, re.IGNORECASE)

print(matches)
for match in matches:
    print(match) # 0000deadbeef0000


# later check for page count
pattern=r"page=(\d+)"
test_string = "http://example.com/search?page=42&query=python"
page_matches = re.findall(pattern, test_string)
for match in page_matches:
    print(f"Page number found: {match}")  # Should print: Page number found: 42