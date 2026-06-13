from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from script.services.preprocessing_service import PreProcessingService
from script.services.kpi_service import KpiService

app = FastAPI()

_dfs = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite Dev-Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _get_data():
    global _dfs
    if _dfs is None:
        try:
            data = PreProcessingService.load_all_data()
        except Exception:
            data = None
        _dfs = data if data is not None else None
    return _dfs

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