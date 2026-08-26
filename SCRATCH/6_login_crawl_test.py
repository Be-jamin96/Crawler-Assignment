"""
Another version of the crawler just to test the login credentials and access to the test-site
"""
import asyncio
import httpx
from typing import Set

from SCRATCH.constants import START_URL, USERNAME, PASSWORD
from models import QueuePayload
from SCRATCH.parser_utils import parse_html_page, scrape_asset_for_passwords


def dispatch_processing(payload: QueuePayload, response: httpx.Response) -> tuple[list[str], list[QueuePayload]]:
    """Placeholder for processing logic based on payload type."""
    print(f"-> Extracting links from {payload.type}: {payload.url}")

    passwords = []
    new_payloads = []
    if payload.type == "page":
        passwords, new_payloads = parse_html_page(response, payload.url)
    elif payload.type in ["script", "css"]:
        passwords, _ = scrape_asset_for_passwords(response)

    return passwords, new_payloads


async def worker(
        name: int,
        queue: asyncio.Queue,
        visited: Set[str],
        client: httpx.AsyncClient,
        state: dict,
        stop_event: asyncio.Event,
        passwords_found: Set[str]
):
    """Async worker that respects a global stop event once the limit is reached."""
    while not stop_event.is_set():
        try:
            # Use a short timeout so workers can check the stop_event periodically
            payload: QueuePayload = await asyncio.wait_for(queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        try:
            # If stop event was triggered while waiting in the queue, skip processing
            if stop_event.is_set():
                queue.task_done()
                break

            print(f"[Worker {name}] Fetching: {payload.url}")
            #await asyncio.sleep(1.0)  # Sleep for 1 second - but this won't block other workers due to asyncio's cooperative multitasking
            response = await client.get(payload.url, follow_redirects=True, timeout=10.0)

            if response.status_code == 200:
                state["processed"] += 1
                print(f"- [{state['processed']}/1000] Successfully processed: {payload.url}")

                # Check if we hit our limit
                if state["processed"] >= 1000:
                    print("Target of 1000 items reached! Signaling workers to stop...")
                    stop_event.set()
                    queue.task_done()
                    break

                # Otherwise, process and queue up new payloads
                passwords, new_payloads = dispatch_processing(payload, response)
                for new_p in new_payloads:
                    if new_p.url not in visited and not stop_event.is_set():
                        visited.add(new_p.url)
                        await queue.put(new_p)
                for password in passwords:
                    passwords_found.add(password)

            else:
                print(f"[Worker {name}] Failed {payload.url} with status: {response.status_code}")

        except httpx.RequestError as e:
            print(f"[Worker {name}] Network error for {payload.url}: {e}")
        except Exception as e:
            print(f"[Worker {name}] Unexpected error for {payload.url}: {e}")
        finally:
            queue.task_done()


async def main():

    queue = asyncio.Queue()
    visited: Set[str] = set()
    passwords_found: Set[str] = set()
    stop_event = asyncio.Event()
    state = {"processed": 0}  # Tracks successful fetches

    initial_payload = QueuePayload(url=START_URL, type="page")
    visited.add(START_URL)
    await queue.put(initial_payload)

    auth = httpx.BasicAuth(USERNAME, PASSWORD)

    # use only 5 workers for a lightweight test
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(auth=auth, limits=limits,headers={"User-Agent": "VisualpingCandidateCrawler/1.0"}) as client:
        workers = [
            asyncio.create_task(worker(i, queue, visited, client, state, stop_event, passwords_found))
            for i in range(20)
        ]

        # Wait until the stop_event is triggered by the worker hitting 100 items
        await stop_event.wait()

        # Cleanly cancel all active workers
        for w in workers:
            w.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

    print(f"Test complete! Successfully processed {state['processed']} items.")
    print(f"{len(passwords_found)} Passwords found: {passwords_found}")


if __name__ == "__main__":
    asyncio.run(main())