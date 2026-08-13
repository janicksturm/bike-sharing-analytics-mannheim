from datetime import datetime

from pydantic import BaseModel

class StationStatusResponse(BaseModel):
    uid: int
    timestamp: datetime
    bikes: int
    free_racks: int

    model_config = {
        "from_attributes": True
    }