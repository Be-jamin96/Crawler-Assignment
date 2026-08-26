from crawler.models import PasswordHit


def scan_with_vision_api(file_path: str, source_url: str) -> list[PasswordHit]:
    """Placeholder for a future AI vision API call (describe/read the image,
    regex the description). Not implemented yet — requires API key handling
    that will be added separately. Intentionally excluded from the default
    strategy list in pipeline.py."""
    raise NotImplementedError("AI vision API extraction is not implemented yet")
