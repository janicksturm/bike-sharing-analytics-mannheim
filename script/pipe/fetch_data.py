import os
import requests
import pandas as pd
from datetime import datetime

URL = "https://mannheim.opendatasoft.com/api/explore/v2.1/catalog/datasets/free_bike_status/exports/parquet?lang=de&timezone=Europe%2FBerlin"
SAVE_DIR = "data/raw"

REQUIRED_COLUMNS = {"uid", "lat", "lng", "name", "bikes", "free_racks"}

def download_file():
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

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        os.remove(file_path)
        raise RuntimeError(f"Downloaded file is missing required columns: {missing}")

    print(f"Parquet saved: {file_path} ({len(df)} rows, {len(df.columns)} cols)")

    return file_path, timestamp