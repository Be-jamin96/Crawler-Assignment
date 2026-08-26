from typing import Literal

PASSWORD_PATTERN = r"VISUALPING\{([0-9a-f]{16})\}"
PAGINATION_PATTERN = r"page=(\d+)"
DEPTH_CUTOFF = 50
PAGINATION_CUTOFF = 5

ASSET_TYPES = Literal["page", "script", "css", "image"]

# Credentials and Target provided by Visualping
USERNAME = "ben.meunier"
PASSWORD = ""
START_URL = ""