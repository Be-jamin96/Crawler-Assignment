"""
Start putting together a basic crawler that can be used to crawl a website and extract links to other pages, scripts, css, and images.
The crawler will use asyncio and httpx for asynchronous HTTP requests.
"""
import asyncio
import httpx
from pydantic import BaseModel
from typing import Optional, Literal, Set


class QueuePayload(BaseModel):
    url: str
    type: Literal["page", "script", "css", "image"]
    parent: Optional[str] = None


def dispatch_processing(payload: QueuePayload, response: httpx.Response) -> list[QueuePayload]:
    """Placeholder for processing logic based on payload type."""
    print(f"Processing {payload.type}: {payload.url} (parent: {payload.parent})")

    new_payloads = []
    if payload.type == "page":
        pass
    elif payload.type in ["script", "css"]:
        pass
    elif payload.type == "image":
        pass

    return new_payloads


async def worker(name: int, queue: asyncio.Queue, visited: Set[str], client: httpx.AsyncClient):
    """Async worker to process URLs from the queue."""
    while True:
        payload: QueuePayload = await queue.get()

        try:
            print(f"[Worker {name}] Fetching: {payload.url}")
            response = await client.get(payload.url, follow_redirects=True, timeout=10.0)

            if response.status_code == 200:
                print(f"[Worker {name}] Success ({response.status_code}): {payload.url}")
                new_payloads = dispatch_processing(payload, response)

                # Store new payloads if not already visited
                for new_p in new_payloads:
                    if new_p.url not in visited:
                        visited.add(new_p.url)
                        await queue.put(new_p)
            else:
                print(f"[Worker {name}] Failed {payload.url} with status: {response.status_code}")
                # TODO if we fail to fetch the url, we can try adding it back to the queue for retrying later?
                # will want to consider a retry limit to avoid infinite loops - perhaps a retry count in the QueuePayload model

        except httpx.RequestError as e:
            print(f"[Worker {name}] Network error for {payload.url}: {e}")
        except Exception as e:
            print(f"[Worker {name}] Unexpected error for {payload.url}: {e}")
        finally:
            queue.task_done()


async def main():
    start_url = "https://docs.nav2.org/setup_guides/odom/setup_odom_gz.html"

    queue = asyncio.Queue()
    visited: Set[str] = set()

    # Initialize start payload and mark as visited
    initial_payload = QueuePayload(url=start_url, type="page")
    visited.add(start_url)
    await queue.put(initial_payload)

    # Create a single shared AsyncClient for connection pooling
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(limits=limits, headers={"User-Agent": "BaselineCrawler/1.0"}) as client:
        # Create 20 worker tasks, passing the shared client
        workers = [
            asyncio.create_task(worker(i, queue, visited, client))
            for i in range(20)
        ]

        # Wait until all items in the queue are processed
        await queue.join()

        # Cleanly cancel workers once the queue is empty
        for w in workers:
            w.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

    print("Crawling complete!")


if __name__ == "__main__":
    asyncio.run(main())