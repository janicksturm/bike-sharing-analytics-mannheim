# Spatial-Temporal Demand Modeling for Bike Sharing Systems

> **Note:** This project is currently a work in progress.

This project focuses on modeling and visualizing the spatial-temporal demand for bike-sharing systems, specifically focused on the NextBike network in Mannheim. It combines an automated data pipeline, a REST API backend, and an interactive React dashboard to explore station status, occupancy, and distribution in real time.

## Features

- **Automated Data Pipeline**: A continuous background job that fetches live snapshot data every 30 minutes from the Mannheim Open Data portal
- **REST API**: A FastAPI backend that serves KPI metrics and station data to the frontend via endpoints.
- **Interactive Dashboard**: A React + TypeScript SPA with page-based routing (Status, Prediction) and a modern dark-themed UI.
- **Geospatial Visualization**: Interactive Leaflet maps to visualize station locations, bike availability, and occupancy rates.
- **KPI Monitoring**: Real-time tracking of total bikes, available-to-rent count, empty stations, and average occupancy — with snapshot-over-snapshot deltas.
- **Station Ranking**: A horizontal bar chart ranking stations by bike count with color-coded availability indicators.

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

4. **Install frontend dependencies**:
   ```bash
   cd dashboard
   npm install
   ```

## Usage

### 1. Data Collection Pipeline

To start collecting data snapshots, run the main data pipeline script. This script will run continuously, fetching data every 30 minutes and saving it to the `data/` directory.

```bash
python main.py
```

### 2. API Server

Start the FastAPI backend to serve data to the dashboard:

```bash
uvicorn script.api.app:app --reload
```

The API will be available at `http://localhost:8000`.

### 3. Dashboard (Dev)

In a separate terminal, start the React development server:

```bash
cd dashboard
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

### 4. Docker (Production Setup)

The recommended way to run the full stack is with **Docker Compose**. This spins up three isolated containers (pipeline, API, dashboard) that share the `data/` directory.

1. **Start all services**:
   ```bash
   docker compose up -d --build
   ```

2. **Access the application**:
   - **Dashboard**: `http://localhost:3000`
   - **API**: `http://localhost:8000`
   - *(The pipeline runs automatically in the background)*

3. **Stop the services**:
   ```bash
   docker compose down
   ```