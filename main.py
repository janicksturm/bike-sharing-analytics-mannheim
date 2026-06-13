import time

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

if __name__ == "__main__":
    pipeline_loop()
