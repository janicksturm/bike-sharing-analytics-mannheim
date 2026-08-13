from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from requests import Session

from src.nextbike_prediction.api.schema.station import StationResponse
from src.nextbike_prediction.api.schema.stations_status import StationStatusResponse
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

@app.get("/status", response_model=list[StationStatusResponse])
def get_latest_station_status(db:Session = Depends(get_db)):
    """Fetch the latest station status """
    statement = (
        select(StationStatus)
        .order_by(StationStatus.timestamp.desc())
        .limit(
            select(func.count())
            .select_from(Station)
            .scalar_subquery()
        )
    )
    return db.scalars(statement).all()

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
