from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, select, func

from requests import Session


from src.nextbike_prediction.models.metrics import calculate_empty_rate, get_latest_snapshot
from src.nextbike_prediction.api.schema.station import StationResponse
from src.nextbike_prediction.api.schema.status import StatusResponse
from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.api.dependencies import get_db

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

    result["snapshot_time"] = get_latest_snapshot(db)

    result["total_bikes"] = db.scalar(
        select(
            func.sum(StationStatus.bikes)
        )
        .where(
            StationStatus.timestamp == result["snapshot_time"]
        )
    )

    result["empty_stations"] = calculate_empty_rate(db, result["snapshot_time"])

    result["avg_occupancy"] = db.scalar(
        select(
            func.avg(
                StationStatus.bikes * 100.0
                / (StationStatus.bikes + Station.bike_racks)
            )
        )
        .where(
            StationStatus.timestamp == result["snapshot_time"],
            StationStatus.bikes + Station.bike_racks > 0
        )
    )

    return result

@app.get("/stations", response_model=list[StationResponse])
def get_stations(db: Session = Depends(get_db)):
    """Fetch all stations from the database."""
    statement = select(Station)

    return db.scalars(statement).all()

# @app.post("/recommendations")
# def get_recommendations(body: LocationRequest):
#     """GPS-based: lat/lng → Top-5 station recommendations."""
#     df = _get_data()
#     if df is None:
#         raise HTTPException(status_code=503, detail="Data not available")
#     try:
#         service = RecommendationService(df)
#         return service.get_recommendations_for_location(body.lat, body.lng, top_n=5, exclude_uid=body.exclude_uid)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
