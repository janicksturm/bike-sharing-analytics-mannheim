import os
import requests
from datetime import datetime

URL = "https://mannheim.opendatasoft.com/api/explore/v2.1/catalog/datasets/free_bike_status/exports/parquet?lang=de&timezone=Europe%2FBerlin"
SAVE_DIR = "data/raw"

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

    print(f"Parquet saved: {file_path}")

    return file_path, timestamp