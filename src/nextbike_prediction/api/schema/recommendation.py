from pydantic import BaseModel


class RecommendationItem(BaseModel):
    rank: int
    uid: int
    name: str
    lat: float
    lng: float
    bikes: int
    free_racks: int
    occupancy_pct: float
    distance_meters: float
    empty_rate: float
    demand_score: float | None
    recommendation_score: float


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]
