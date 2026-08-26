"""
A modified version of the base_crawler that I can run without crashing a site or sprawling too many pages
"""

import asyncio
import httpx
from typing import Set

from models import QueuePayload


def dispatch_processing(payload: QueuePayload, response: httpx.Response) -> list[QueuePayload]:
    """Placeholder for processing logic based on payload type."""
    print(f"-> Extracting links from {payload.type}: {payload.url}")

    new_payloads = []
    if payload.type == "page":
        # Manual new payload for demonstration purposes
        new_payloads.append(QueuePayload(url="https://beautiful-soup-4.readthedocs.io/en/latest/", type="css", parent=payload.url))
        pass
    elif payload.type in ["script", "css"]:
        # Manual new payload for demonstration purposes
        new_payloads.append(QueuePayload(url="https://beautiful-soup-4.readthedocs.io/en/latest/#searching-the-tree", type="script", parent=payload.url))
        pass

    return new_payloads


async def worker(name: int, queue: asyncio.Queue, visited: Set[str], client: httpx.AsyncClient, state: dict,
                 stop_event: asyncio.Event):
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
            response = await client.get(payload.url, follow_redirects=True, timeout=10.0)

            if response.status_code == 200:
                state["processed"] += 1
                print(f"- [{state['processed']}/3] Successfully processed: {payload.url}")

                # Check if we hit our limit
                if state["processed"] >= 3:
                    print("Target of 3 items reached! Signaling workers to stop...")
                    stop_event.set()
                    queue.task_done()
                    break

                # Otherwise, process and queue up new payloads
                new_payloads = dispatch_processing(payload, response)
                for new_p in new_payloads:
                    if new_p.url not in visited and not stop_event.is_set():
                        visited.add(new_p.url)
                        await queue.put(new_p)
            else:
                print(f"[Worker {name}] Failed {payload.url} with status: {response.status_code}")

        except httpx.RequestError as e:
            print(f"[Worker {name}] Network error for {payload.url}: {e}")
        except Exception as e:
            print(f"[Worker {name}] Unexpected error for {payload.url}: {e}")
        finally:
            queue.task_done()


async def main():
    start_url = "https://docs.nav2.org/rolling/configuration_and_development/first_time_robot_setup_guide/odom/setup_odom/"

    queue = asyncio.Queue()
    visited: Set[str] = set()
    stop_event = asyncio.Event()
    state = {"processed": 0}  # Tracks successful fetches

    initial_payload = QueuePayload(url=start_url, type="page")
    visited.add(start_url)
    await queue.put(initial_payload)

    # Scale workers down to 5 for a lightweight test
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(limits=limits, headers={"User-Agent": "TestCrawler/1.0"}) as client:
        workers = [
            asyncio.create_task(worker(i, queue, visited, client, state, stop_event))
            for i in range(5)
        ]

        # Wait until the stop_event is triggered by the worker hitting 3 items
        await stop_event.wait()

        # Cleanly cancel all active workers
        for w in workers:
            w.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

    print(f"Test complete! Successfully processed {state['processed']} items.")


if __name__ == "__main__":
    asyncio.run(main())