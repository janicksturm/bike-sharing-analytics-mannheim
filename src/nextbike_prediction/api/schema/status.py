from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StatusResponse(BaseModel):
    snapshot_time: datetime
    total_bikes: int
    total_bikes_delta: Optional[float] = None
    empty_stations: int
    empty_stations_delta: Optional[float] = None
    avg_occupancy: float
    avg_occupancy_delta: Optional[float] = None

    model_config = {
        "from_attributes": True
    }