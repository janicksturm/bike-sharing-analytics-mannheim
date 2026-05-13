from script.pipe.fetch_data import download_file
import time

def run_pipeline():
    try:
        download_file()
    except Exception as e:
        print(f"Error: {e}")


# run every 30 minutes
if __name__ == "__main__":
    while True:
        run_pipeline()
        time.sleep(1800)