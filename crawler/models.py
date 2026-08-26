from typing import Literal, Optional

from pydantic import BaseModel

AssetType = Literal["page", "script", "css", "image"]


class QueuePayload(BaseModel):
    url: str
    type: AssetType
    parent: Optional[str] = None
    depth: Optional[int] = None


class PasswordHit(BaseModel):
    password: str
    source_url: str
    method: str
    location: str
    payload_type: AssetType


class GeoBlock(BaseModel):
    page_url: str
    required_region: str
