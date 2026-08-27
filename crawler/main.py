import asyncio
import logging

from crawler.config import load_config
from crawler.engine.crawl import run_crawl
from crawler.logging_setup import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    configure_logging(config.log_level)

    logger.info("Starting crawl at %s", config.start_url)
    store, geo_blocks = await run_crawl(config)

    print(store.report())
    print(f"\n{store.unique_count}/8 passwords found.")

    geo_report = geo_blocks.report()
    if geo_report:
        print(f"\n{geo_report}")


if __name__ == "__main__":
    asyncio.run(main())
