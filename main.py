import time

from script.pipe.service.fetch_data import get_data_as_json

URL = "https://mannheim.opendatasoft.com/api/explore/v2.1/catalog/datasets/free_bike_status/exports/json"

def run_pipeline():
    try:
        print(get_data_as_json(url=URL))
    except Exception as e:
        print(f"Pipeline Error: {e}")

def pipeline_loop():
    while True:
        run_pipeline()
        time.sleep(1800)

if __name__ == "__main__":
    pipeline_loop()
