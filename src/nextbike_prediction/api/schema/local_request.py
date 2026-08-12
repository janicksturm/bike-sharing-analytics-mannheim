from pydantic import BaseModel

from typing import Optional

class LocationRequest(BaseModel):
    lat: float
    lng: float
    exclude_uid: Optional[int] = None