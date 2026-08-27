#!/bin/sh
# Waits for the X display named in $DISPLAY to accept TCP connections before
# running the container's command. Without this, the gui service can race
# novnc's Xvfb startup — especially under QEMU emulation (e.g. running the
# amd64-only novnc image on Apple Silicon) — and crash-loop indefinitely
# instead of settling after one retry.
set -e

if [ -n "$DISPLAY" ]; then
    HOST=$(printf '%s' "$DISPLAY" | cut -d: -f1)
    DISPLAY_NUM=$(printf '%s' "$DISPLAY" | cut -d: -f2 | cut -d. -f1)
    PORT=$((6000 + DISPLAY_NUM))

    echo "Waiting for X display ${DISPLAY} (tcp ${HOST}:${PORT})..."
    i=0
    until python3 -c "import socket; socket.create_connection(('${HOST}', ${PORT}), timeout=1)" 2>/dev/null; do
        i=$((i + 1))
        if [ "$i" -ge 120 ]; then
            echo "Gave up waiting for ${DISPLAY} after 120s" >&2
            break
        fi
        sleep 1
    done
    echo "X display is up."
fi

exec "$@"
