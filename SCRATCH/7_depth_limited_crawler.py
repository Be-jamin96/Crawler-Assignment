"""
Another version of the crawler just to test the login credentials and access to the test-site
"""
import asyncio
import re

import httpx
from typing import Set

from SCRATCH.constants import START_URL, USERNAME, PASSWORD, PAGINATION_PATTERN, PAGINATION_CUTOFF, DEPTH_CUTOFF
from models import QueuePayload
from SCRATCH.parser_utils import parse_html_page, scrape_asset_for_passwords, parse_image


def dispatch_processing(payload: QueuePayload, response: httpx.Response) -> tuple[list[str], list[QueuePayload]]:
    """Placeholder for processing logic based on payload type."""
    print(f"-> Extracting links from {payload.type}: {payload.url}")

    passwords = []
    new_payloads = []
    if payload.type == "page":
        passwords, new_payloads = parse_html_page(response, payload.url)
    elif payload.type in ["script", "css"]:
        passwords, _ = scrape_asset_for_passwords(response)
    elif payload.type == "image":
        passwords = parse_image(response, payload.url)

    return passwords, new_payloads

def _check_pagination_threshold(url: str) -> bool:
    # Placeholder logic for detecting pagination traps
    page_matches = re.findall(PAGINATION_PATTERN, url)
    page_numbers = [int(match) for match in page_matches]
    for page_number in page_numbers:
        if page_number >= PAGINATION_CUTOFF:
            print(f"Pagination threshold reached for {url}. Detected {len(page_matches)} pagination parameters.")
            return True
    return False


async def worker(
        name: int,
        queue: asyncio.Queue,
        visited: Set[str],
        client: httpx.AsyncClient,
        state: dict,
        stop_event: asyncio.Event,
        passwords_found: Set[str]
):
    while not stop_event.is_set():
        try:
            payload: QueuePayload = await asyncio.wait_for(queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        try:
            if stop_event.is_set():
                queue.task_done()
                break

            # --- DEQUEUE-TIME CHECK & CLAIM ---
            if payload.url in visited:
                continue

            # Claim it immediately so other workers ignore it
            visited.add(payload.url)

            if payload.depth and payload.depth >= DEPTH_CUTOFF:
                print(f"[Worker {name}] Depth cutoff reached for {payload.url}.")
                continue

            if _check_pagination_threshold(payload.url):
                print(f"[Worker {name}] Pagination detected for {payload.url}.")
                continue

            print(f"[Worker {name}] Fetching: {payload.url}")
            response = await client.get(payload.url, follow_redirects=True, timeout=10.0)

            if response.status_code == 200:
                state["processed"] += 1
                print(f"- [Worker {name}][{state['processed']}/1000] Successfully processed: {payload.url}")

                if state["processed"] >= 1000:
                    print("Target of 1000 items reached! Signaling workers to stop...")
                    stop_event.set()
                    queue.task_done()
                    break

                passwords, new_payloads = dispatch_processing(payload, response)
                for new_p in new_payloads:
                    new_p.depth = payload.depth + 1 if payload.depth is not None else 1

                    # Only queue it if it hasn't been visited yet
                    if new_p.url not in visited and not stop_event.is_set():
                        await queue.put(new_p)

                passwords_found.update(passwords)

            else:
                print(f"[Worker {name}] Failed {payload.url} with status: {response.status_code}")
                visited.remove(payload.url)

        except httpx.RequestError as e:
            print(f"[Worker {name}] Network error for {payload.url}: {e}")
            if payload.url in visited:
                visited.remove(payload.url)
        except Exception as e:
            print(f"[Worker {name}] Unexpected error for {payload.url}: {e}")
            if payload.url in visited:
                visited.remove(payload.url)
        finally:
            queue.task_done()


async def main():
    queue = asyncio.Queue()
    visited: Set[str] = set()
    passwords_found: Set[str] = set()
    stop_event = asyncio.Event()
    state = {"processed": 0}

    initial_payload = QueuePayload(url=START_URL, type="page", depth=0)
    # Removed the visited.add() here so the worker can claim it
    await queue.put(initial_payload)

    auth = httpx.BasicAuth(USERNAME, PASSWORD)

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    # Testing naive header-based geo-blocking
    headers = {
        "User-Agent": "VisualpingCandidateCrawler/1.0",
        "CF-IPCountry": "DE",  # Cloudflare style
        "X-Real-IP": "82.165.169.231",  # Nginx / proxy style
        "X-Client-IP": "82.165.169.231",
    }
    async with httpx.AsyncClient(auth=auth, limits=limits, headers=headers) as client:
        workers = [
            asyncio.create_task(worker(i, queue, visited, client, state, stop_event, passwords_found))
            for i in range(20)
        ]

        # Wait for either the queue to empty OR the stop_event to be set
        queue_task = asyncio.create_task(queue.join())
        stop_task = asyncio.create_task(stop_event.wait())

        await asyncio.wait(
            [queue_task, stop_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Tell workers to stop regardless of which condition finished first
        stop_event.set()

        # Cleanly cancel all active workers
        for w in workers:
            w.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

    print(f"\nTest complete! Successfully processed {state['processed']} items.")
    print(f"{len(passwords_found)} Passwords found: {passwords_found}")


if __name__ == "__main__":
    asyncio.run(main())