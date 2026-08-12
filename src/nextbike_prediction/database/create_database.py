
from .models.base import Base
from .connection import engine
from .models.station import Station
from .models.station_status import StationStatus


def create_database() -> None:
    Base.metadata.create_all(bind=engine)


create_database()