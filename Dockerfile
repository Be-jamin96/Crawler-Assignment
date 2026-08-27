FROM python:3.11-slim

# tesseract-ocr: needed by pytesseract for image OCR extraction.
# libimage-exiftool-perl: provides the `exiftool` CLI, shelled out to by
# crawler/extraction/images/exif_scan.py for EXIF metadata password extraction.
# The rest: OpenGL/X11 client libs needed by Dear PyGui's GLFW renderer when
# talking to a remote/virtual X display (see docker-compose.yml's novnc service).
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libimage-exiftool-perl \
    libgl1 \
    libglx0 \
    libegl1 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# Software OpenGL rendering: the virtual/remote X display has no real GPU,
# so force Mesa's llvmpipe software rasterizer instead of trying (and failing)
# to use hardware GL.
ENV LIBGL_ALWAYS_SOFTWARE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY crawler ./crawler
COPY gui ./gui
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "gui"]
