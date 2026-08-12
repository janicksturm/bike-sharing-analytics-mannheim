from datetime import datetime

from pydantic import BaseModel

class StationStatusResponse(BaseModel):
    timestamp: datetime
    bikes: int
    free_racks: int

    model_config = {
        "from_attributes": True
    }