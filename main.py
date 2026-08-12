import time
from datetime import datetime, timezone

from src.nextbike_prediction.pipe.service.fetch_data import get_data_as_objects
from src.nextbike_prediction.database.create_database import create_database
from src.nextbike_prediction.database.connection import SessionFactory

from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus

URL = "https://mannheim.opendatasoft.com/api/explore/v2.1/catalog/datasets/free_bike_status/exports/json"

def run_pipeline():
    try:
        data = get_data_as_objects(url=URL)

        timestamp = datetime.now(timezone.utc)

        with SessionFactory() as session:
            for station in data:
                if session.get(Station, station.uid) is None:
                    new_station = Station(
                        uid=station.uid,
                        name=station.name,
                        lat=station.lat,
                        lng=station.lng,
                        bike_racks=station.bike_racks,
                    )
                    session.add(new_station)

                status = StationStatus(
                    uid=station.uid,
                    timestamp=timestamp,
                    bikes=station.bikes,
                    free_racks=station.free_racks,
                    )
                session.add(status)
            session.commit()
        print(f"Saved snapshot at {timestamp.isoformat()} with {len(data)} stations")

    except Exception as e:
        print(f"Pipeline Error: {e}")
        session.rollback()
        raise

def pipeline_loop():
    while True:
        run_pipeline()
        time.sleep(1800)

if __name__ == "__main__":
    create_database()
    pipeline_loop()