from pydantic import BaseModel


class StationResponse(BaseModel):
    uid: int
    name: str
    lat: float
    lng: float
    bike_racks: int | None
    bikes: int | None = None
    free_racks: int | None = None
    occupancy_pct: float | None = None

    model_config = {
        "from_attributes": True
    }