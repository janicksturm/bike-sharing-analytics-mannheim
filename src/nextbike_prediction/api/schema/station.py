from pydantic import BaseModel

class StationResponse(BaseModel):
    uid: int
    name: str
    lat: float
    lng: float
    bike_racks: int | None

    model_config = {
        "from_attributes": True
    }