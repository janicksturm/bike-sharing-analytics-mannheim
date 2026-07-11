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

def _get_data():
    try:
        return PreProcessingService.load_all_data()
    except Exception:
        return None

@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}

@app.get("/status")
def get_status():
    try:
        kpis = KpiService(_get_data())
        status = kpis.get_status()
        return status
    except ValueError as e:
        return {"error": str(e)}

@app.get("/stations")
def get_stations():
    try:
        service = LocationService(_get_data())
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
