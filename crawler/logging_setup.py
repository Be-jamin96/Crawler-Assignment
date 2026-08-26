import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once, at process start. Safe to call more than once."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
