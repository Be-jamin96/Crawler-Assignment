"""
Explore using beautiful soup documentation examples for parsing a web page.
"""

import asyncio
from bs4 import BeautifulSoup
import httpx

async def fetch_and_parse(url):
  print(f"Fetching: {url}")

  # 1. Open an async HTTP client session
  async with httpx.AsyncClient() as client:
    # 2. 'await' the network request (non-blocking)
    response = await client.get(url)

    if response.status_code == 200:
      print("Successfully downloaded! Parsing HTML...")

      # 3. Pass response.text into BeautifulSoup
      soup = BeautifulSoup(response.text, "html.parser")

      # 4. Extract some basic info to prove it worked
      title = soup.title.string if soup.title else "No title"
      print(f"-> Page Title: {title}")

      # 5. Find all links on the page (for demonstration)
      print("-> First 3 links found on the page:")
      for a_tag in soup.find_all("a", href=True)[:3]:
        print(f"   - {a_tag['href']}")

      # 6. Find all images on the page (for demonstration)
      print("-> First 3 images found on the page:")
      for img_tag in soup.find_all("img", src=True)[:3]:
        print(f"   - {img_tag['src']}")

      # 7. Find all scripts on the page (for demonstration)
      print("-> First 3 scripts found on the page:")
      for script_tag in soup.find_all("script", src=True)[:3]:
        print(f"   - {script_tag['src']}")

      # 8. Find all stylesheets on the page (for demonstration)
      print("-> First 3 stylesheets found on the page:")
      for link_tag in soup.find_all("link", rel="stylesheet", href=True)[:3]:
        print(f"   - {link_tag['href']}")


    else:
      print(f"Failed with status code: {response.status_code}")


async def main():
  target_url = "https://beautiful-soup-4.readthedocs.io/en/latest/#searching-the-tree"
  await fetch_and_parse(target_url)

# Run the async event loop
if __name__ == "__main__":
  asyncio.run(main())