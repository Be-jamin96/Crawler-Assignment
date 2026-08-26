from pydantic import BaseModel
from typing import Optional

from SCRATCH.constants import ASSET_TYPES


class QueuePayload(BaseModel):
    url: str
    type: ASSET_TYPES
    parent: Optional[str] = None
    depth: Optional[int] = None # only optional because we added this late and want to make it back-compatible with previous tests