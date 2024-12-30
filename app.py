import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import altair as alt
from streamlit_folium import st_folium
from datetime import datetime
from folium import plugins

# ========================================== Session State Initialization ==========================================
# Initialize session state for map synchronization
if "map_center" not in st.session_state:
    st.session_state.map_center = [23.12303, 119.9416977]  # Default center coordinates
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 10  # Default zoom level
if "last_map" not in st.session_state:
    st.session_state.last_map = None  # To track which map was last updated

# Initialize session state for date selection mode and selected dates
if "date_filter_mode" not in st.session_state:
    st.session_state.date_filter_mode = "Date Range"  # Default mode
if "selected_date_range" not in st.session_state:
    st.session_state.selected_date_range = []
if "selected_specific_date" not in st.session_state:
    st.session_state.selected_specific_date = None

# Initialize session state for date selection mode and selected dates for dengue spraying
if 'spraying_date_filter_mode' not in st.session_state:
    st.session_state.spraying_date_filter_mode = 'Date Range'  # Default mode
if 'spraying_selected_date_range' not in st.session_state:
    st.session_state.spraying_selected_date_range = []
if 'spraying_selected_specific_date' not in st.session_state:
    st.session_state.spraying_selected_specific_date = None

# ========================================== Page Configuration ==========================================
st.set_page_config(layout="wide")

# ========================================== Data Loading ==========================================
@st.cache_data
def load_data():
    data = pd.read_csv("data/dengue_fever_cases_by_area.csv")
    dengue_spraying = pd.read_csv("data/dengue_spray_count_by_area.csv")
    return data, dengue_spraying

data, dengue_spraying = load_data()

# ========================================== Sidebar ==========================================
st.sidebar.title("Taiwan City Dengue Fever Cases Filter")
st.sidebar.markdown("Use the filters below to customize the dengue fever cases and spraying heatmaps.")

# Checkbox to enable map synchronization
enable_sync = st.sidebar.checkbox("Enable Map Synchronization", value=True)

# Year filter
years = ["Total"] + sorted(data["year"].dropna().unique())
selected_year = st.sidebar.selectbox("Select Year", years)

# Heatmap radius selector
radius = st.sidebar.slider("Select Heatmap Radius", min_value=1, max_value=50, value=25)

# Neighborhood filter
neighborhoods = ["All"] + sorted(data["neighborhood"].dropna().unique())
selected_neighborhoods = st.sidebar.multiselect("Select Neighborhoods", neighborhoods, default=["All"])

# Checkbox to filter heatmap by selected neighborhoods
filter_heatmap_by_neighborhood = st.sidebar.checkbox("Filter Heatmap by Selected Neighborhoods", value=False)

# Sort option for the bar chart
sort_options = ["Ascending", "Descending"]
sort_order = st.sidebar.radio("Sort Order for Neighborhood Cases", sort_options, index=1)

# Number of neighborhoods to display
num_neighborhoods = st.sidebar.number_input(
    "Number of Neighborhoods to Display",
    min_value=1,
    max_value=len(neighborhoods) - 1,
    value=min(20, len(neighborhoods) - 1),
)

# Date filter mode selector for dengue cases (existing)
date_filter_mode = st.sidebar.radio("Filter Dengue Cases by Date", ("Date Range", "Specific Date", "7-Day Window"), index=0)

# Date filter mode selector for dengue spraying
spraying_date_filter_mode = st.sidebar.radio("Filter Dengue Spraying by Date", ("Date Range", "Specific Date"), index=0)

# Convert date columns to datetime
data["diagnosis_date"] = pd.to_datetime(data["diagnosis_date"], errors="coerce")
dengue_spraying["date"] = pd.to_datetime(dengue_spraying["date"], errors="coerce")

# Determine min and max dates for date picker
min_date_cases = data["diagnosis_date"].min()
max_date_cases = data["diagnosis_date"].max()
min_date_spraying = dengue_spraying["date"].min()
max_date_spraying = dengue_spraying["date"].max()

min_date = min(min_date_cases, min_date_spraying)
max_date = max(max_date_cases, max_date_spraying)

# Handle date selection based on filter mode for dengue cases
if date_filter_mode == "Date Range":
    if not st.session_state.selected_date_range:
        st.session_state.selected_date_range = [
            min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now(),
            max_date.to_pydatetime() if pd.notnull(max_date) else datetime.now(),
        ]

    time_slider = st.sidebar.slider(
        "Select Date Range",
        min_value=min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now(),
        max_value=max_date.to_pydatetime() if pd.notnull(max_date) else datetime.now(),
        value=(
            st.session_state.selected_date_range[0],
            st.session_state.selected_date_range[1],
        ),
        format="YYYY-MM-DD",
    )

    st.session_state.selected_date_range = list(time_slider)

    if st.sidebar.button("Reset Date Range"):
        st.session_state.selected_date_range = [
            min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now(),
            max_date.to_pydatetime() if pd.notnull(max_date) else datetime.now(),
        ]
        time_slider = st.sidebar.slider(
            "Select Date Range",
            min_value=(min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now()),
            max_value=(max_date.to_pydatetime() if pd.notnull(max_date) else datetime.now()),
            value=(
                st.session_state.selected_date_range[0],
                st.session_state.selected_date_range[1],
            ),
            format="YYYY-MM-DD",
        )

    start_date, end_date = st.session_state.selected_date_range
    specific_date = None
elif date_filter_mode == "Specific Date":
    if not st.session_state.selected_specific_date:
        st.session_state.selected_specific_date = (
            min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now()
        )

    specific_date = st.sidebar.date_input(
        "Select Specific Date",
        value=st.session_state.selected_specific_date,
        min_value=min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now(),
        max_value=max_date.to_pydatetime() if pd.notnull(max_date) else datetime.now(),
        key="specific_date_picker",
    )

    st.session_state.selected_specific_date = specific_date

    if st.sidebar.button("Reset Specific Date"):
        st.session_state.selected_specific_date = (
            min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now()
        )
        specific_date = st.sidebar.date_input(
            "Select Specific Date",
            value=st.session_state.selected_specific_date,
            min_value=(min_date.to_pydatetime() if pd.notnull(min_date) else datetime.now()),
            max_value=(max_date.to_pydatetime() if pd.notnull(max_date) else datetime.now()),
            key="specific_date_picker_reset",
        )

    start_date = end_date = specific_date
    specific_date = specific_date

# Handle date selection based on filter mode for dengue spraying
if spraying_date_filter_mode == "Date Range":
    if not st.session_state.spraying_selected_date_range:
        st.session_state.spraying_selected_date_range = [
            min_date_spraying.to_pydatetime() if pd.notnull(min_date_spraying) else datetime.now(),
            max_date_spraying.to_pydatetime() if pd.notnull(max_date_spraying) else datetime.now(),
        ]

    spraying_time_slider = st.sidebar.slider(
        "Select Spraying Date Range",
        min_value=min_date_spraying.to_pydatetime() if pd.notnull(min_date_spraying) else datetime.now(),
        max_value=max_date_spraying.to_pydatetime() if pd.notnull(max_date_spraying) else datetime.now(),
        value=(
            st.session_state.spraying_selected_date_range[0],
            st.session_state.spraying_selected_date_range[1],
        ),
        format="YYYY-MM-DD",
        key="spraying_time_slider"
    )

    st.session_state.spraying_selected_date_range = list(spraying_time_slider)

    if st.sidebar.button("Reset Spraying Date Range"):
        st.session_state.spraying_selected_date_range = [
            min_date_spraying.to_pydatetime() if pd.notnull(min_date_spraying) else datetime.now(),
            max_date_spraying.to_pydatetime() if pd.notnull(max_date_spraying) else datetime.now(),
        ]

    spraying_start_date, spraying_end_date = st.session_state.spraying_selected_date_range
    spraying_specific_date = None
else:
    if not st.session_state.spraying_selected_specific_date:
        st.session_state.spraying_selected_specific_date = (
            min_date_spraying.to_pydatetime() if pd.notnull(min_date_spraying) else datetime.now()
        )

    spraying_specific_date = st.sidebar.date_input(
        "Select Spraying Specific Date",
        value=st.session_state.spraying_selected_specific_date,
        min_value=min_date_spraying.to_pydatetime() if pd.notnull(min_date_spraying) else datetime.now(),
        max_value=max_date_spraying.to_pydatetime() if pd.notnull(max_date_spraying) else datetime.now(),
        key="spraying_specific_date_picker",
    )

    st.session_state.spraying_selected_specific_date = spraying_specific_date

    if st.sidebar.button("Reset Spraying Specific Date"):
        st.session_state.spraying_selected_specific_date = (
            min_date_spraying.to_pydatetime() if pd.notnull(min_date_spraying) else datetime.now()
        )

    spraying_start_date = spraying_end_date = spraying_specific_date
    spraying_specific_date = spraying_specific_date

# Now handle 7-Day Window after spraying dates are set
if date_filter_mode == "7-Day Window":
    if spraying_date_filter_mode == "Date Range":
        end_date = pd.Timestamp(spraying_end_date)
    else:
        end_date = pd.Timestamp(spraying_specific_date)
    start_date = end_date - pd.Timedelta(days=6)
    specific_date = None

# ========================================== Helper Functions ==========================================
def create_spraying_markers(data):
    """Create markers for spraying locations with custom icons"""
    markers = []
    for _, row in data.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
            popup_text = f"Spraying Count: {row['spray_count']}<br>Date: {row['date']}"
            icon = folium.Icon(color='blue', icon='tint', prefix='fa')
            marker = folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup_text,
                icon=icon
            )
            markers.append(marker)
    return markers
def create_heatmap_map(data, map_type="cases", radius=25, include_spray_markers=False, spray_data=None):
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        control_scale=True,
    )

    if map_type == "cases":
        # Ensure data types are correct
        heat_data = data[["latitude", "longitude", "cases"]].astype({
            "latitude": float,
            "longitude": float,
            "cases": float
        }).dropna().values.tolist()
        
        HeatMap(
            heat_data,
            radius=radius,
            gradient={0.0: "lime", 0.4: "cyan", 0.6: "yellow", 0.8: "blue", 1.0: "red"},
            min_opacity=0.4,
            max_opacity=0.8,
        ).add_to(m)
        
        if include_spray_markers and spray_data is not None:
            for marker in create_spraying_markers(spray_data):
                marker.add_to(m)

    elif map_type == "spraying":
        # Ensure data types are correct
        heat_data = data[["latitude", "longitude", "spray_count"]].astype({
            "latitude": float,
            "longitude": float,
            "spray_count": float
        }).dropna().values.tolist()
        
        HeatMap(
            heat_data,
            radius=radius,
            gradient={0.0: "lime", 0.4: "cyan", 0.6: "yellow", 0.8: "blue", 1.0: "red"},
            min_opacity=0.4,
            max_opacity=0.8,
        ).add_to(m)

    return m

def handle_map_sync(map_output, current_map_id):
    if map_output and map_output.get("center") and map_output.get("zoom") is not None:
        if enable_sync:
            if st.session_state.last_map != current_map_id:
                st.session_state.map_center = [
                    map_output["center"]["lat"],
                    map_output["center"]["lng"],
                ]
                st.session_state.map_zoom = map_output["zoom"]
                st.session_state.last_map = current_map_id

# ========================================== Main Panel ==========================================
st.title("Taiwan City Dengue Fever Cases and Spraying Heatmaps")

if start_date and end_date:
    # Filter dengue fever cases
    if selected_year != "Total":
        filtered_cases = data[data["year"] == selected_year]
    else:
        filtered_cases = data.copy()

    if date_filter_mode in ["Date Range", "7-Day Window"]:
        # Convert dates to Timestamp for comparison
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        filtered_cases = filtered_cases[
            (filtered_cases["diagnosis_date"] >= start_date) & 
            (filtered_cases["diagnosis_date"] <= end_date)
        ]
    else:
        filtered_cases = filtered_cases[filtered_cases["diagnosis_date"].dt.date == start_date]

    if "All" not in selected_neighborhoods and filter_heatmap_by_neighborhood:
        filtered_cases = filtered_cases[filtered_cases["neighborhood"].isin(selected_neighborhoods)]

    # Filter dengue spraying data based on spraying date filters
    if spraying_start_date and spraying_end_date:
        if spraying_date_filter_mode == "Date Range":
            filtered_spraying = dengue_spraying[
                (dengue_spraying["date"] >= spraying_start_date) & (dengue_spraying["date"] <= spraying_end_date)
            ]
        else:
            filtered_spraying = dengue_spraying[dengue_spraying["date"].dt.date == spraying_start_date]
    else:
        # Default to original spraying data if no dates are selected
        filtered_spraying = dengue_spraying.copy()

    # Apply other filters to dengue spraying data
    if "All" not in selected_neighborhoods and filter_heatmap_by_neighborhood:
        filtered_spraying = filtered_spraying[filtered_spraying["neighborhood"].isin(selected_neighborhoods)]

    # Create columns for side-by-side heatmaps
    col1, col2 = st.columns(2)

    # Dengue Fever Cases Heatmap
    with col1:
        st.subheader("Dengue Fever Cases Heatmap")
        if not filtered_cases.empty:
            filtered_cases = filtered_cases.dropna(subset=["latitude", "longitude", "cases"])
            if not filtered_cases.empty:
                m1 = create_heatmap_map(filtered_cases, map_type="cases", radius=radius)
                map1 = st_folium(m1, width=800, height=600)
                handle_map_sync(map1, "map1")
            else:
                st.warning("No valid dengue cases data available after removing rows with missing location or case values.")
        else:
            st.warning("No dengue cases data available for the selected filters.")

    # Dengue Spraying Heatmap
    with col2:
        st.subheader("Dengue Spraying Heatmap")
        if not filtered_spraying.empty:
            filtered_spraying = filtered_spraying.dropna(subset=["latitude", "longitude", "spray_count"])
            if not filtered_spraying.empty:
                m2 = create_heatmap_map(filtered_spraying, map_type="spraying", radius=radius)
                map2 = st_folium(m2, width=800, height=600)
                handle_map_sync(map2, "map2")
            else:
                st.warning("No valid dengue spraying data available after removing rows with missing location or spray count values.")
        else:
            st.warning("No dengue spraying data available for the selected filters.")

    # Dengue Fever Cases by Neighborhood
    st.subheader("Dengue Fever Cases by Neighborhood")
    city_cases = filtered_cases.groupby("neighborhood")["cases"].sum().reset_index()
    city_cases = city_cases.sort_values(by="cases", ascending=(sort_order == "Ascending")).head(num_neighborhoods)

    bar_chart = (
        alt.Chart(city_cases)
        .mark_bar()
        .encode(
            x=alt.X("neighborhood", sort=None, title="Neighborhood"),
            y=alt.Y("cases", title="Cases"),
            color=alt.Color("cases", scale=alt.Scale(scheme="blues")),
        )
        .properties(width=800, height=400)
        .configure_axisX(labelAngle=-45)
        .interactive()
    )

    st.altair_chart(bar_chart, use_container_width=True)

    # Spraying Timeline Chart (Interactive, x-axis zoom only)
    st.subheader("Spraying Timeline Chart")

    spraying_timeline_data = dengue_spraying.groupby("date")["spray_count"].sum().reset_index()
    
    # Create x-axis zoom selection
    zoom = alt.selection_interval(
        bind='scales',
        encodings=['x']  # Only allow zooming on x-axis
    )

    timeline_chart = (
        alt.Chart(spraying_timeline_data)
        .mark_bar()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("spray_count:Q", title="Total Spray Count"),
            tooltip=["date:T", "spray_count:Q"],
        )
        .properties(width=800, height=400)
        .add_params(zoom)  # Add zoom selection
    )

    # Dengue Fever Timeline Chart (Interactive, x-axis zoom only)
    st.subheader("Dengue Fever Cases Timeline Chart")

    dengue_timeline_data = data.groupby("diagnosis_date")["cases"].sum().reset_index()

    dengue_timeline_chart = (
        alt.Chart(dengue_timeline_data)
        .mark_bar(color="orange")
        .encode(
            x=alt.X("diagnosis_date:T", title="Date"),
            y=alt.Y("cases:Q", title="Total Cases"),
            tooltip=["diagnosis_date:T", "cases:Q"],
        )
        .properties(width=800, height=400)
        .add_params(zoom)  # Share the same zoom selection
    )

    # Combine charts with shared x-axis scale
    combined_chart = alt.vconcat(timeline_chart, dengue_timeline_chart).resolve_scale(x='shared')

    st.altair_chart(combined_chart, use_container_width=True)

    # Add new section for before/after comparison
    st.header("Spraying Effect Analysis")
    st.markdown("Compare dengue cases distribution before and after spraying")

    if spraying_date_filter_mode == "Specific Date":
        effect_col1, effect_col2 = st.columns(2)
        
        # Convert specific date to timestamp for calculations
        spray_date = pd.Timestamp(spraying_specific_date)
        
        with effect_col1:
            st.subheader("7 Days After Spraying")
            # Get cases for 7 days after spraying
            after_start = spray_date
            after_end = after_start + pd.Timedelta(days=6)
            
            after_cases = data[
                (data["diagnosis_date"] >= after_start) &
                (data["diagnosis_date"] <= after_end)
            ]
            
            if not after_cases.empty:
                m_after = create_heatmap_map(
                    after_cases, 
                    map_type="cases", 
                    radius=radius,
                    include_spray_markers=True,
                    spray_data=filtered_spraying
                )
                map_after = st_folium(m_after, width=800, height=600, key="map_after")
                handle_map_sync(map_after, "map_after")
                st.info(f"Showing cases from {after_start.date()} to {after_end.date()}")
            else:
                st.warning("No cases data available for the period after spraying.")

        with effect_col2:
            st.subheader("7 Days Before Spraying")
            # Get cases for 7 days before spraying
            before_end = spray_date - pd.Timedelta(days=1)
            before_start = before_end - pd.Timedelta(days=6)
            
            before_cases = data[
                (data["diagnosis_date"] >= before_start) &
                (data["diagnosis_date"] <= before_end)
            ]
            
            if not before_cases.empty:
                m_before = create_heatmap_map(before_cases, map_type="cases", radius=radius)
                map_before = st_folium(m_before, width=800, height=600, key="map_before")
                handle_map_sync(map_before, "map_before")
                st.info(f"Showing cases from {before_start.date()} to {before_end.date()}")
            else:
                st.warning("No cases data available for the period before spraying.")

        # Add statistics about the effect
        st.subheader("Effect Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            before_count = before_cases['cases'].sum()
            st.metric("Total Cases (7 days before)", before_count)
        
        with col2:
            after_count = after_cases['cases'].sum()
            st.metric("Total Cases (7 days after)", after_count)
            
        with col3:
            effect = before_count - after_count
            delta_percentage = ((after_count - before_count) / before_count * 100) if before_count != 0 else 0
            st.metric("Change in Cases", effect, f"{delta_percentage:.1f}%")
    else:
        st.warning("Please select a specific date for spraying to view the before/after analysis.")

else:
    st.warning("Please select a valid date filter.")
