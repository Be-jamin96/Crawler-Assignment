import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

REQUIRED_ENV_VARS = ("VP_USERNAME", "VP_PASSWORD", "VP_START_URL")


@dataclass(frozen=True)
class CrawlerConfig:
    username: str
    password: str
    start_url: str
    depth_cutoff: int = 50
    pagination_cutoff: int = 5
    worker_count: int = 20
    max_processed: int = 1000
    request_timeout: float = 10.0
    download_dir: str = "downloaded_images"
    log_level: str = "INFO"
    # Polite delay (seconds), randomized between 0 and this value and applied
    # before each request — slows the crawl down so its live GUI view reads
    # smoothly instead of finishing instantly. 0 disables it.
    request_delay: float = 0.0
    # Optional proxy (e.g. "http://user:pass@host:port") used only to retry
    # requests that come back geo-blocked. If unset, geo-blocked pages are
    # skipped and flagged in the final report instead of fetched.
    region_proxy: Optional[str] = None


def load_config() -> CrawlerConfig:
    """Load configuration from a local .env file (if present) and the environment."""
    load_dotenv()

    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            f"{', '.join(missing)}. Copy .env.example to .env and fill them in."
        )

    return CrawlerConfig(
        username=os.environ["VP_USERNAME"],
        password=os.environ["VP_PASSWORD"],
        start_url=os.environ["VP_START_URL"],
        log_level=os.environ.get("VP_LOG_LEVEL", "INFO"),
        region_proxy=os.environ.get("VP_REGION_PROXY") or None,
    )
