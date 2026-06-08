import time
import threading
import uvicorn

from script.pipe.fetch_data import download_file

def run_pipeline():
    try:
        download_file()
    except Exception as e:
        print(f"Pipeline Error: {e}")

def pipeline_loop():
    while True:
        run_pipeline()
        time.sleep(1800)

def start_api():
    uvicorn.run(
        "script.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )

if __name__ == "__main__":
    pipeline_thread = threading.Thread(
        target=pipeline_loop,
        daemon=True
    )
    pipeline_thread.start()

    start_api()
