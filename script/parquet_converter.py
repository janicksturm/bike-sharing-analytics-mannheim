import pandas as pd
import geopandas as gpd

df = pd.read_parquet("data/raw/free_bike_status.parquet")

df["lat"] = df["lat"].astype(float)
df["lng"] = df["lng"].astype(float)

gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df["lng"], df["lat"]),
    crs="EPSG:4326"
)
gdf.to_file("data/geo/data.geojson", driver="GeoJSON")

print("GeoJSON created")