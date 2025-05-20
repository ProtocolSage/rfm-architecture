"""Streamlit dashboard for visualising `~/.rfm_ui_metrics.json`."""
from __future__ import annotations

import json
import pathlib
import datetime
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from typing import List, Dict, Any, Optional, Tuple

# Set page config
st.set_page_config(
    page_title="RFM UI Performance Telemetry",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Path to metrics data
DATA_PATH = pathlib.Path.home() / ".rfm_ui_metrics.json"

@st.cache_data(show_spinner=False, ttl=60)  # Cache for 60 seconds
def load_data() -> pd.DataFrame:
    """Load metrics data from file."""
    rows: list[dict[str, Any]] = []
    if DATA_PATH.exists():
        with DATA_PATH.open() as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    # Create empty DataFrame if no data
    if not rows:
        return pd.DataFrame(columns=["timestamp", "operation", "ms", "ram", "cpu"])
    
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    
    # Convert timestamp to datetime
    if "timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    
    return df

def format_date_range(df: pd.DataFrame) -> str:
    """Format date range string from DataFrame."""
    if df.empty or "datetime" not in df.columns:
        return "No data available"
    
    min_date = df["datetime"].min().strftime("%Y-%m-%d %H:%M")
    max_date = df["datetime"].max().strftime("%Y-%m-%d %H:%M")
    return f"{min_date} to {max_date}"

def render_summary_metrics(df: pd.DataFrame) -> None:
    """Render summary metrics in the dashboard."""
    if df.empty:
        st.warning("No telemetry data available.")
        return
    
    # Basic metrics
    total_records = len(df)
    unique_operations = df["operation"].nunique()
    date_range = format_date_range(df)
    
    # Performance metrics
    avg_ms = df["ms"].mean()
    p95_ms = df["ms"].quantile(0.95)
    max_ms = df["ms"].max()
    
    # Memory usage
    avg_ram = df["ram"].mean() if "ram" in df.columns else 0
    max_ram = df["ram"].max() if "ram" in df.columns else 0
    
    # Layout with columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", f"{total_records:,}")
        st.metric("Date Range", date_range)
    
    with col2:
        st.metric("Avg Frame Time", f"{avg_ms:.2f} ms")
        st.metric("95th Percentile", f"{p95_ms:.2f} ms")
    
    with col3:
        st.metric("Avg Memory Usage", f"{avg_ram:.1f} MB")
        st.metric("Max Memory Usage", f"{max_ram:.1f} MB")

def render_frame_time_histogram(df: pd.DataFrame) -> None:
    """Render frame time histogram."""
    if df.empty or "ms" not in df.columns:
        return
    
    st.subheader("Frame Time Distribution")
    
    # Create histogram chart
    chart = alt.Chart(df).mark_bar(
        opacity=0.8,
        color="#4287f5"
    ).encode(
        x=alt.X("ms:Q", bin=alt.Bin(maxbins=40), title="Frame Time (ms)"),
        y=alt.Y("count():Q", title="Frequency"),
        tooltip=["count():Q", alt.Tooltip("ms:Q", bin=alt.Bin(maxbins=40))]
    ).properties(
        height=250
    )
    
    # Add mean line
    mean_line = alt.Chart(pd.DataFrame({'mean': [df["ms"].mean()]})).mark_rule(
        color='red',
        strokeWidth=2
    ).encode(
        x='mean:Q'
    )
    
    # Render chart
    st.altair_chart(chart + mean_line, use_container_width=True)
    
    # Add percentile badges
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Minimum", f"{df['ms'].min():.2f} ms")
    col2.metric("Median", f"{df['ms'].median():.2f} ms")
    col3.metric("95th Percentile", f"{df['ms'].quantile(0.95):.2f} ms")
    col4.metric("Maximum", f"{df['ms'].max():.2f} ms")

def render_operation_analysis(df: pd.DataFrame) -> None:
    """Render operation performance analysis."""
    if df.empty or "operation" not in df.columns:
        return
    
    st.subheader("Operation Performance Analysis")
    
    # Group by operation
    op_stats = df.groupby("operation").agg({
        "ms": ["count", "mean", "min", "max", lambda x: np.percentile(x, 95)],
        "ram": ["mean", "max"] if "ram" in df.columns else []
    }).reset_index()
    
    # Flatten columns
    op_stats.columns = [
        "_".join(col).strip("_") for col in op_stats.columns.values
    ]
    
    # Rename columns
    rename_dict = {
        "ms_count": "Count",
        "ms_mean": "Avg Time (ms)",
        "ms_min": "Min Time (ms)",
        "ms_max": "Max Time (ms)",
        "ms_<lambda_0>": "95% (ms)",
    }
    
    if "ram_mean" in op_stats.columns:
        rename_dict.update({
            "ram_mean": "Avg RAM (MB)",
            "ram_max": "Max RAM (MB)"
        })
    
    op_stats = op_stats.rename(columns=rename_dict)
    
    # Format numeric columns
    for col in op_stats.columns:
        if col != "operation" and op_stats[col].dtype in [np.float64, np.int64]:
            if "Time" in col:
                op_stats[col] = op_stats[col].apply(lambda x: f"{x:.2f}")
            elif "RAM" in col:
                op_stats[col] = op_stats[col].apply(lambda x: f"{x:.1f}")
            else:
                op_stats[col] = op_stats[col].apply(lambda x: f"{x:,}")
    
    # Create expandable dataframe
    with st.expander("Operation Statistics Table", expanded=False):
        st.dataframe(
            op_stats.sort_values("Avg Time (ms)", ascending=False),
            use_container_width=True
        )
    
    # Create chart of average times by operation
    if len(op_stats) > 0:
        # Convert back to numeric for chart
        chart_data = df.groupby("operation").agg({
            "ms": ["mean", lambda x: np.percentile(x, 95)],
        }).reset_index()
        
        chart_data.columns = ["operation", "avg_ms", "p95_ms"]
        
        # Sort by average time
        chart_data = chart_data.sort_values("avg_ms", ascending=False).head(10)
        
        # Create chart
        base = alt.Chart(chart_data).encode(
            x=alt.X("operation:N", title="Operation", sort="-y")
        )
        
        # Bar chart for average
        bars = base.mark_bar(color="#4287f5", opacity=0.8).encode(
            y=alt.Y("avg_ms:Q", title="Average Time (ms)"),
            tooltip=["operation", "avg_ms:Q", "p95_ms:Q"]
        )
        
        # Error bars for 95th percentile
        error_bars = base.mark_errorbar(color="red").encode(
            y=alt.Y("avg_ms:Q", title="Average Time (ms)"),
            y2="p95_ms:Q"
        )
        
        chart = (bars + error_bars).properties(
            title="Top 10 Operations by Average Time",
            height=350
        )
        
        st.altair_chart(chart, use_container_width=True)

def render_timeline(df: pd.DataFrame) -> None:
    """Render performance timeline."""
    if df.empty or "datetime" not in df.columns:
        return
    
    st.subheader("Performance Timeline")
    
    # Create time series chart
    chart = alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(color="#4287f5")
    ).encode(
        x=alt.X("datetime:T", title="Time"),
        y=alt.Y("ms:Q", title="Frame Time (ms)"),
        tooltip=["datetime:T", "ms:Q", "operation:N"]
    ).properties(
        height=300
    )
    
    # Add rolling average
    if len(df) > 10:
        # Calculate rolling average
        df_rolling = df.sort_values("datetime").copy()
        df_rolling["rolling_avg"] = df_rolling["ms"].rolling(10).mean()
        
        # Create rolling average line
        rolling_line = alt.Chart(df_rolling.dropna()).mark_line(
            color="red",
            strokeWidth=2
        ).encode(
            x="datetime:T",
            y="rolling_avg:Q"
        )
        
        chart += rolling_line
    
    st.altair_chart(chart, use_container_width=True)

def render_hotspots(df: pd.DataFrame) -> None:
    """Render performance hotspots analysis."""
    if df.empty:
        return
    
    st.subheader("Performance Hotspots")
    
    # Define threshold for hotspots (ms)
    threshold = st.slider(
        "Hotspot Threshold (ms)",
        min_value=int(df["ms"].min()),
        max_value=int(df["ms"].max()),
        value=int(df["ms"].quantile(0.95)),
    )
    
    # Find hotspots
    hotspots = df[df["ms"] >= threshold].sort_values("ms", ascending=False)
    
    if len(hotspots) == 0:
        st.info(f"No operations exceeded {threshold} ms")
        return
    
    # Display hotspots
    st.write(f"Found {len(hotspots)} operations exceeding {threshold} ms")
    
    # Format hotspot data for display
    display_cols = ["datetime", "operation", "ms"]
    if "ram" in hotspots.columns:
        display_cols.append("ram")
    
    # Format the dataframe
    hotspot_df = hotspots[display_cols].copy()
    hotspot_df["ms"] = hotspot_df["ms"].apply(lambda x: f"{x:.2f}")
    if "ram" in hotspot_df.columns:
        hotspot_df["ram"] = hotspot_df["ram"].apply(lambda x: f"{x:.1f}")
    
    # Rename columns
    rename_dict = {
        "datetime": "Timestamp",
        "operation": "Operation",
        "ms": "Time (ms)",
        "ram": "Memory (MB)"
    }
    hotspot_df = hotspot_df.rename(columns=rename_dict)
    
    # Show dataframe
    st.dataframe(hotspot_df, use_container_width=True)

def main():
    """Main dashboard function."""
    st.title("📊 RFM UI Performance Telemetry")
    
    # Load data
    df = load_data()
    
    # Display data info
    if df.empty:
        st.warning("No telemetry data found at: " + str(DATA_PATH))
        st.info("Open the Premium UI and interact with it to generate telemetry data.")
        return
    
    # Add sidebar controls
    with st.sidebar:
        st.header("Dashboard Controls")
        
        # Date range filter if data has dates
        if "datetime" in df.columns:
            min_date = df["datetime"].min().date()
            max_date = df["datetime"].max().date()
            
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                # Add one day to end_date to include it in the filter
                end_date = end_date + datetime.timedelta(days=1)
                df = df[(df["datetime"] >= pd.Timestamp(start_date)) & 
                         (df["datetime"] < pd.Timestamp(end_date))]
        
        # Operation filter
        if "operation" in df.columns:
            operations = st.multiselect(
                "Filter Operations",
                options=sorted(df["operation"].unique()),
                default=[]
            )
            
            if operations:
                df = df[df["operation"].isin(operations)]
        
        # Add refresh button
        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Render dashboard sections
    render_summary_metrics(df)
    render_frame_time_histogram(df)
    
    # Create tabs for detailed analysis
    tab1, tab2, tab3 = st.tabs(["Operation Analysis", "Timeline", "Hotspots"])
    
    with tab1:
        render_operation_analysis(df)
    
    with tab2:
        render_timeline(df)
    
    with tab3:
        render_hotspots(df)
    
    # Add footer
    st.markdown("---")
    st.caption(f"Data source: {DATA_PATH}")
    st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()