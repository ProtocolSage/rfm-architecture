# RFM UI Performance Dashboard

A Streamlit-based dashboard for visualizing performance metrics collected by the RFM UI.

## Overview

This dashboard provides insights into the performance of the RFM Architecture UI by analyzing telemetry data collected during usage. It visualizes metrics such as:

- Frame rendering time
- Memory usage
- CPU usage
- Performance by operation type
- Hotspots and anomalies

## Usage

Run the dashboard with:

```bash
cd tools/perf_dashboard
pip install -r requirements.txt
streamlit run app.py
```

The dashboard will automatically load telemetry data from `~/.rfm_ui_metrics.json`.

## Features

1. **Summary Metrics** - Key performance indicators at a glance
2. **Frame Time Distribution** - Histogram showing the distribution of frame times
3. **Operation Analysis** - Detailed breakdown by operation type
4. **Timeline** - Performance trends over time
5. **Hotspots** - Identification of performance outliers

## Data Source

The dashboard reads telemetry data collected by the RFM UI's performance tracker. This data is stored in JSON format at `~/.rfm_ui_metrics.json` and includes metrics for each operation performed by the UI.