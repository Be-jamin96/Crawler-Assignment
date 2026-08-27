# Crawler Assignment

A password-hunting web crawler with two ways to run it:

- **Backend (headless CLI)** — `crawler/`: crawls a target, extracts credentials from pages/scripts/CSS/images, prints a final report.
- **Frontend (GUI)** — `gui/`: a real-time "spy ops" dashboard — a live node graph of the crawl (color-coded by state), a live found-passwords list, and a form to launch a crawl with your own credentials/proxy.

The two are decoupled: `gui/` imports `crawler/`, never the reverse. The crawler works identically with or without the GUI attached.

# Getting started: 
I would highly recommend setting the .env variables first - this will save you hassle with the copy/paste restricted GUI and will be necessary regardless of setup. Simply create a copy of `.env.example` as `.env` and complete the required fields locally in your own editor.

## Running with Docker (recommended)

Requires Docker and Docker Compose.

### Frontend (GUI)

Dear PyGui needs a real display, so the GUI runs against a virtual X display + VNC server (`novnc` service) that you view in a browser — no local display or Python setup needed.

```bash
docker compose up
```

Then open **http://localhost:6080/vnc.html** in a browser (the plain `http://localhost:6080/` root is just a directory listing — use the `/vnc.html` path) and click **Connect**. You'll see the GUI running inside the container. Fill in the mission parameters and click **LAUNCH CRAWL** — nodes will appear on the right in real time as pages/scripts/images are discovered, colored by state:

> **Can't paste into the form (including the proxy field)?** VNC doesn't share your host clipboard, so pasting into these fields doesn't work — typing does, but it's painful for something like a proxy URL with embedded credentials. Avoid it entirely: edit `.env` locally in your own editor (real copy-paste), then either restart the GUI container to pick it up —
> ```bash
> docker compose restart gui
> ```
> — or just set it before the first `docker compose up`. Username, password, start URL, and proxy are pre-filled from `VP_USERNAME`/`VP_PASSWORD`/`VP_START_URL`/`VP_REGION_PROXY` automatically; you never have to type into the VNC window at all unless you want a one-off override.

| Color | State |
|---|---|
| Blue | Discovered (queued) |
| Orange | Processing (fetching) |
| Green | Processed |
| Gold | Password found |
| Red | Failed |

Found passwords appear on the left as they're discovered, with a final qualified-passwords summary once the crawl completes. The node graph (top right) is pannable (click-drag the background) but **not zoomable** — Dear PyGui's node editor doesn't support zoom — so on a fast or wide crawl it will outrun the visible area. The **Activity Log** underneath it is the reliable way to see everything: a plain scrolling, auto-following list of every URL and state change, in order, regardless of where the graph is panned to.

**On sluggishness:** the Docker path renders into a virtual display and streams it to your browser over VNC — there's no way around some added latency/CPU cost compared to a real window, especially if `novnc`'s image is running under CPU emulation (e.g. the amd64-only image on Apple Silicon). The frame rate is capped at 30fps to keep this reasonable. For the smoothest experience, run the GUI natively instead (see below) — Docker exists so it also runs identically on a machine with no local Python/display setup, not because it's the best experience.

**Delay (s) slider:** the crawler is fast enough to finish before the graph is interesting to watch. This slider (0–1, in seconds) adds a random delay — between 0 and the slider value — before each request, the same way you'd randomize delays through a proxy to avoid hammering a site in a suspicious lockstep pattern. Set it to 0 for a fast headless-style run, or turn it up to slow the crawl down and watch nodes light up one at a time. It only affects the GUI-launched crawl (`CrawlerConfig.request_delay`); the headless CLI defaults to 0 (no delay).

> Note: on a cold `up`, the GUI container waits for novnc's virtual display to finish starting before launching (see `docker/entrypoint.sh`) — this can take longer than usual under CPU emulation (e.g. running the amd64-only `novnc` image on Apple Silicon), so give it up to ~30–60s on first start before it renders.

To stop: `docker compose down`.

### Backend (headless CLI)

Runs the same crawler without any GUI, reading credentials from `.env`:

```bash
cp .env.example .env   # fill in VP_USERNAME, VP_PASSWORD, VP_START_URL
docker compose run --rm crawler
```

This prints the password report, qualified-passwords summary, and any geo-blocked pages to stdout — identical to running `python -m crawler.main` locally.

## Running without Docker

```bash
pip install -r requirements.txt
```

**GUI:**
```bash
cp .env.example .env   # optional — pre-fills the form's credential fields
python -m gui
```

**Headless CLI:**
```bash
cp .env.example .env   # fill in credentials
python -m crawler.main
```

(Image OCR extraction also requires the `tesseract-ocr` system package to be installed locally; the Docker image installs this for you.)

## Proxy scope

The proxy field (GUI form or `VP_REGION_PROXY` env var) is only used to retry pages that come back **geo-blocked** (HTTP 403 with a region restriction) — it does not route the rest of the crawl's traffic. Geo-blocked pages encountered without a proxy configured are skipped and listed in the final report instead.

## Project layout

```
crawler/            # headless crawler engine (backend)
  main.py           # CLI entrypoint
  config.py         # CrawlerConfig + load_config() (.env)
  events.py         # NodeEvent/NodeState — optional real-time hooks the GUI subscribes to
  engine/           # queue/worker loop, dispatch, guards, geo-block handling
  extraction/       # password/link discovery (text, images, JS, CSS)
  reporting/        # PasswordStore, GeoBlockRegistry
gui/                 # real-time GUI (frontend) — imports crawler, never the reverse
  app.py            # window layout + frame loop
  crawl_runner.py   # runs a crawl on a background thread, bridges events to the GUI
  graph_view.py     # live (pannable, not zoomable) node graph
  activity_log.py   # scrolling text log of every event — the reliable "see everything" view
  password_panel.py # live found-passwords list
  credentials_form.py
  theme.py
Dockerfile           # shared image for both `gui` and `crawler` services
docker/entrypoint.sh  # waits for the X display (if any) before running the container's command
docker-compose.yml    # gui + novnc (virtual display/VNC) + crawler (headless) services
```
