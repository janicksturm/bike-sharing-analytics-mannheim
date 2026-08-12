
import requests
from pydantic import TypeAdapter
from src.nextbike_prediction.pipe.models.bike_station import BikeStation

def get_data_as_objects(url: str):
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