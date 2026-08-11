import os
import requests
import pandas as pd
from datetime import datetime
from pydantic import TypeAdapter
from models import BikeStation

URL = "https://mannheim.opendatasoft.com/api/explore/v2.1/catalog/datasets/free_bike_status/exports/parquet?lang=de&timezone=Europe%2FBerlin"
SAVE_DIR = "data/raw"

def download_file():
    """Downloads the Parquet file from the specified URL and saves it locally with a timestamped filename."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    print(f"Download started: {now}")

    os.makedirs(SAVE_DIR, exist_ok=True)

    response = requests.get(URL)
    response.raise_for_status()

    file_path = os.path.join(SAVE_DIR, f"data_{timestamp}.parquet")

    with open(file_path, "wb") as f:
        f.write(response.content)

    try:
        df = pd.read_parquet(file_path)
    except Exception as exc:
        os.remove(file_path)
        raise RuntimeError(f"Downloaded file is not a valid Parquet file: {exc}") from exc

    if len(df) == 0:
        os.remove(file_path)
        raise RuntimeError("Downloaded Parquet file contains 0 rows.")

    print(f"Parquet saved: {file_path} ({len(df)} rows, {len(df.columns)} cols)")

    return file_path, timestamp

def get_data_as_json(url: str):
    """Fetches data from the specified URL and returns it as a list of BikeStation objects."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        station_data = TypeAdapter(list[BikeStation]).validate_python(response.json())

        return station_data

    except requests.Timeout:
        print("Request timed out")

    except requests.RequestException as e:
        print(f"HTTP error: {e}")

    except ValueError:
        print("Response wasn't valid JSON")