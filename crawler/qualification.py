from crawler.extraction.patterns import normalize
from crawler.reporting.store import PasswordStore

# Rules specific to THIS target (stated on its homepage, visible only via raw
# HTML source since a JS snippet removes them from the rendered page):
#   - The worked example itself is explicitly not one of the eight.
#   - Passwords whose only source is an HTTP response header are declared
#     "staging placeholders" and are not qualified.
_WORKED_EXAMPLE = normalize("VISUALPING{0000deadbeef0000}")


def qualified_passwords(store: PasswordStore) -> list[str]:
    qualified = []
    for key in store.unique_passwords():
        if key == _WORKED_EXAMPLE:
            continue
        if all(hit.method == "header" for hit in store.hits_for(key)):
            continue
        qualified.append(key)
    return qualified
