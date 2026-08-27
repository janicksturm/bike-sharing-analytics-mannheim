from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, select, func
from sqlalchemy.orm import Session

from src.nextbike_prediction.models.metrics import calculate_empty_rate, get_latest_snapshot, get_previous_snapshot, get_total_bikes, get_avg_occupancy
from src.nextbike_prediction.api.schema.station import StationResponse
from src.nextbike_prediction.api.schema.status import StatusResponse
from src.nextbike_prediction.api.schema.recommendation import RecommendationResponse
from src.nextbike_prediction.api.schema.local_request import LocationRequest
from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.api.dependencies import get_db
from src.nextbike_prediction.services.recommendation_service import RecommendationService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}

@app.get("/status", response_model=StatusResponse)
def get_latest_station_status(db:Session = Depends(get_db)):
    """Fetch the latest station status 

    Return is a single row with the following fields:
    - snapshot_time: timestamp of the latest snapshot
    - total_bikes: total number of bikes available across all stations
    - empty_stations: total number of stations with no bikes available
    - avg_occupancy: average occupancy rate across all stations (bikes / (bikes + free_racks)), excluding stations with no bikes and no free racks
    """
    result = {}

    latest_ts = get_latest_snapshot(db)
    result["snapshot_time"] = latest_ts
    result["total_bikes"] = get_total_bikes(db, latest_ts)
    result["empty_stations"] = calculate_empty_rate(db, latest_ts)
    result["avg_occupancy"] = get_avg_occupancy(db, latest_ts)

    prev_ts = get_previous_snapshot(db, latest_ts) if latest_ts else None
    if prev_ts is not None:
        prev_bikes = get_total_bikes(db, prev_ts)
        prev_empty = calculate_empty_rate(db, prev_ts)
        prev_occ = get_avg_occupancy(db, prev_ts)
        result["total_bikes_delta"] = (result["total_bikes"] or 0) - (prev_bikes or 0)
        result["empty_stations_delta"] = (result["empty_stations"] or 0) - (prev_empty or 0)
        result["avg_occupancy_delta"] = round(
            (result["avg_occupancy"] or 0.0) - (prev_occ or 0.0), 1
        )

    return result

@app.get("/stations", response_model=list[StationResponse])
def get_stations(db: Session = Depends(get_db)):
    """Fetch all stations with their latest live status."""
    latest_ts = db.scalar(
        select(func.max(StationStatus.timestamp))
    )

    if latest_ts is None:
        raise HTTPException(status_code=404, detail="No station status data available.")

    statement = (
        select(
            Station.uid,
            Station.name,
            Station.lat,
            Station.lng,
            Station.bike_racks,
            StationStatus.bikes,
            StationStatus.free_racks,
            case(
                (
                    StationStatus.bikes + StationStatus.free_racks > 0,
                    StationStatus.bikes * 100.0
                    / (StationStatus.bikes + StationStatus.free_racks),
                ),
                else_=None,
            ).label("occupancy_pct"),
        )
        .outerjoin(
            StationStatus,
            (Station.uid == StationStatus.uid) & (StationStatus.timestamp == latest_ts),
        )
        .order_by(Station.uid)
    )

    rows = db.execute(statement).all()
    return [
        StationResponse(
            uid=row.uid,
            name=row.name,
            lat=row.lat,
            lng=row.lng,
            bike_racks=row.bike_racks,
            bikes=row.bikes,
            free_racks=row.free_racks,
            occupancy_pct=round(float(row.occupancy_pct), 1) if row.occupancy_pct is not None else None,
        )
        for row in rows
    ]

@app.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(body: LocationRequest, db: Session = Depends(get_db)):
    """GPS-based: lat/lng → Top-5 station recommendations.

    Scores nearby stations by combining bike availability, historical reliability,
    walking distance, and recent demand trend. Results are logged to the database
    for future analytics and ML model training.
    """
    try:
        service = RecommendationService(db)
        return service.get_recommendations_for_location(
            body.lat, body.lng, top_n=5, exclude_uid=body.exclude_uid
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
