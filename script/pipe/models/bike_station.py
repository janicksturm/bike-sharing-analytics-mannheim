from pydantic import BaseModel

class BikeStation(BaseModel):
    uid: int
    lat: str
    lng: str
    name: str
    bikes: int
    bike_racks: int | None
    free_racks: int