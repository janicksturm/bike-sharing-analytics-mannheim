import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from script.services.preprocessing_service import PreProcessingService
from script.services.kpi_service import KpiService
from script.services.location_service import LocationService
from script.services.recommendation_service import RecommendationService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class LocationRequest(BaseModel):
    lat: float
    lng: float

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

@app.get("/stations")
def get_stations():
    df = _get_data()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not available")
    try:
        service = LocationService(df)
        return {"stations": service.get_stations()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations")
def get_recommendations(body: LocationRequest):
    """GPS-based: lat/lng → Top-5 station recommendations."""
    df = _get_data()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not available")
    try:
        service = RecommendationService(df)
        return service.get_recommendations_for_location(body.lat, body.lng, top_n=5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
