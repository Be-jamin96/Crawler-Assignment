import asyncio
import logging

from crawler.config import load_config
from crawler.engine.crawl import run_crawl
from crawler.logging_setup import configure_logging
from crawler.qualification import qualified_passwords

logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    configure_logging(config.log_level)

    logger.info("Starting crawl at %s", config.start_url)
    store, geo_blocks = await run_crawl(config)

    print(store.report())

    qualified = qualified_passwords(store)
    print(f"\n{len(qualified)}/8 qualified passwords found (excludes the worked example and header-only placeholders):")
    for p in qualified:
        print(f"  {p}")

    geo_report = geo_blocks.report()
    if geo_report:
        print(f"\n{geo_report}")


if __name__ == "__main__":
    asyncio.run(main())
