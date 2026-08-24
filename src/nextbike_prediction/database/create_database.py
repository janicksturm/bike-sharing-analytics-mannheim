
from .models.base import Base
from .connection import engine
from .models.station import Station
from .models.station_status import StationStatus
from .models.station_metrics import StationMetrics


def create_database() -> None:
    Base.metadata.create_all(bind=engine)