from datetime import datetime

from pydantic import BaseModel


class StatusResponse(BaseModel):
    snapshot_time: datetime
    total_bikes: int
    available_to_rent: int
    empty_stations: int
    avg_occupancy: float

    model_config = {
        "from_attributes": True
    }