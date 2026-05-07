# Spatial-Temporal Demand Modeling for Bike Sharing Systems

This project focuses on modeling and visualizing the spatial-temporal demand for bike-sharing systems, specifically focused on the NextBike network in Mannheim. It includes an automated data pipeline to collect system snapshots over time and an interactive dashboard to explore station status, occupancy, and distribution.

## Features

- **Automated Data Pipeline**: A continuous background job (`main.py`) that fetches live snapshot data from the NextBike API every 30 minutes and stores it in optimized formats (Parquet/GeoJSON).
- **Interactive Dashboard**: A Streamlit-based web application (`app.py`) providing insights into the bike-sharing network.
- **Geospatial Visualization**: Interactive maps built with Folium to visualize station locations, bike availability, and occupancy rates.
- **KPI Monitoring**: Tracking of total bikes, available bikes, empty stations, and average occupancy across the network.

## Tech Stack

- **Python**
- **Streamlit** (Dashboard UI)
- **Pandas / GeoPandas** (Data manipulation & spatial analysis)
- **Folium / Streamlit-Folium** (Interactive maps)
- **Plotly** (Charts and graphs)
- **PyArrow / Fastparquet** (Efficient data storage)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/janicksturm/bike-sharing-analytics-mannheim.git
   cd bike-sharing-analytics-mannheim
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Data Collection Pipeline

To start collecting data snapshots, run the main data pipeline script. This script will run continuously, fetching data every 30 minutes and saving it to the `data/` directory.

```bash
python main.py
```

### 2. Dashboard

To view the interactive dashboard, run the Streamlit app. This will start a local web server and open the dashboard in your default browser.

```bash
streamlit run app.py
```