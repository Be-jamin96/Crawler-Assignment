"""Lifecycle events emitted by the crawler for optional real-time observers (e.g. a GUI).

The crawler has no dependency on any observer — `event_bus` is a plain,
thread-safe `queue.Queue`, and every emit site is a no-op when it's `None`.
"""

import queue
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from crawler.models import AssetType, PasswordHit


class NodeState(str, Enum):
    DISCOVERED = "discovered"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    PASSWORD_FOUND = "password_found"


class NodeEvent(BaseModel):
    url: str
    type: AssetType
    state: NodeState
    parent: Optional[str] = None
    hit: Optional[PasswordHit] = None


EventBus = "queue.Queue[NodeEvent]"


def emit(event_bus: Optional[queue.Queue], event: NodeEvent) -> None:
    if event_bus is not None:
        event_bus.put_nowait(event)
