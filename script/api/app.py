from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from script.services.preprocessing_service import PreProcessingService
from script.services.kpi_service import KpiService
from script.services.location_service import LocationService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite Dev-Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
