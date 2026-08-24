import time
from datetime import datetime, timezone

from src.nextbike_prediction.models.metrics import compute_station_metrics
from src.nextbike_prediction.pipe.service.fetch_data import get_data_as_objects
from src.nextbike_prediction.database.create_database import create_database
from src.nextbike_prediction.database.connection import SessionFactory

from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.database.models.station_metrics import StationMetrics

URL = "https://mannheim.opendatasoft.com/api/explore/v2.1/catalog/datasets/free_bike_status/exports/json"

def run_pipeline():
    try:
        data = get_data_as_objects(url=URL)

        timestamp = datetime.now(timezone.utc)

        with SessionFactory() as session:
            try:
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

                metrics = compute_station_metrics(session)
                for metric in metrics:
                    session.add(StationMetrics(
                        uid=metric["uid"],
                        timestamp=timestamp,
                        empty_rate=metric["empty_rate"],
                        avg_bikes=metric["avg_bikes"],
                        avg_occupancy=metric["avg_occupancy"],
                    ))
                session.commit()
            except Exception:
                session.rollback()
                raise

        print(f"Saved snapshot at {timestamp.isoformat()} with {len(data)} stations")

    except Exception as e:
        print(f"Pipeline Error: {e}")
        raise

def pipeline_loop():
    while True:
        run_pipeline()
        time.sleep(1800)

if __name__ == "__main__":
    create_database()
    pipeline_loop()