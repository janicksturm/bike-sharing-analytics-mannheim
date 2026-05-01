import os
import pandas as pd
import geopandas as gpd

GEO_DIR = "data/geo"

def convert_to_geojson(path, timestamp):
    os.makedirs(GEO_DIR, exist_ok=True)

    df = pd.read_parquet(path)

    df["lat"] = df["lat"].astype(float)
    df["lng"] = df["lng"].astype(float)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lng"], df["lat"]),
        crs="EPSG:4326"
    )

    # versioned file
    geo_path = os.path.join(GEO_DIR, f"data_{timestamp}.geojson")
    gdf.to_file(geo_path, driver="GeoJSON")

    # stable file for frontend
    latest_path = os.path.join(GEO_DIR, "latest.geojson")
    gdf.to_file(latest_path, driver="GeoJSON")

    print(f"GeoJSON saved: {geo_path}")
    print("latest.geojson updated")
