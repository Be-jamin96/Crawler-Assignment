import re

import httpx

_GEO_BLOCK_PATTERN = re.compile(r"only visible to ([A-Za-z ]+?) region", re.IGNORECASE)


def detect_geo_block(response: httpx.Response) -> str | None:
    """If a response looks like this target's regional-availability block,
    return the required region name; otherwise None."""
    if response.status_code != 403:
        return None
    match = _GEO_BLOCK_PATTERN.search(response.text)
    return match.group(1).strip() if match else None
