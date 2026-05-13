from script.pipe.fetch_data import download_file
from script.pipe.data_utils import convert_to_geojson
import time

def run_pipeline():
    try:
        parquet_path, timestamp = download_file()
        convert_to_geojson(parquet_path, timestamp)
    except Exception as e:
        print(f"Error: {e}")


# run every 30 minutes
if __name__ == "__main__":
    while True:
        run_pipeline()
        time.sleep(1800)