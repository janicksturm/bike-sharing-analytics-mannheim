import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from requests import Session

from nextbike_prediction.services.preprocessing_service import PreProcessingService
from src.nextbike_prediction.api.schema.station import StationResponse
from src.nextbike_prediction.api.schema.local_request import LocationRequest
from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.services.kpi_service import KpiService
from src.nextbike_prediction.services.location_service import LocationService
from src.nextbike_prediction.services.recommendation_service import RecommendationService

from src.nextbike_prediction.api.dependencies import get_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_DATA_CACHE: dict = {"df": None, "ts": 0.0}
_CACHE_TTL_SECONDS = 300

def _get_data():
    now = time.time()
    if _DATA_CACHE["df"] is not None and (now - _DATA_CACHE["ts"]) < _CACHE_TTL_SECONDS:
        return _DATA_CACHE["df"]
    try:
        df = PreProcessingService.load_all_data()
        _DATA_CACHE["df"] = df
        _DATA_CACHE["ts"] = now
        return df
    except Exception:
        return None

@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}

@app.get("/status")
def get_status():
    df = _get_data()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not available")
    try:
        kpis = KpiService(df)
        return kpis.get_status()
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stations", response_model=list[StationResponse])
def get_stations(db: Session = Depends(get_db)):
    """Fetch all stations from the database."""
    statement = select(Station)

    return db.scalars(statement).all()

@app.post("/recommendations")
def get_recommendations(body: LocationRequest):
    """GPS-based: lat/lng → Top-5 station recommendations."""
    df = _get_data()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not available")
    try:
        service = RecommendationService(df)
        return service.get_recommendations_for_location(body.lat, body.lng, top_n=5, exclude_uid=body.exclude_uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
