import pandas as pd
import streamlit as st
import plotly.express as px
import json


from backend import (
    load_data,
    combine_data,
    filter_data,
    get_total, 
    get_average
)


@st.cache_data
def load_lhd_geojson():
    with open(
        "nsw_lhd_boundaries.geojson",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


admissions, ed, waiting_times, asthma_hospitalisation_rates = load_data()
data = combine_data(admissions, ed, waiting_times, asthma_hospitalisation_rates)

data["value"] = pd.to_numeric(
    data["value"],
    errors="coerce"
)

st.title("EpiCentre")
st.subheader("Public Health Intelligence Dashboard")

#Adding in the 3 filters: year, lhd, indicator
selected_year = st.sidebar.selectbox(
    "Year",
    sorted(data["year"].unique(), reverse=True)
)

selected_lhd = st.sidebar.selectbox(
    "Local Hospital District",
    ["All"] + sorted(data["LHD"].unique())
)

selected_indicator = st.sidebar.selectbox(
    "Health Indicator",
    sorted(data["indicator"].unique())
)

#Connect the filters
filtered_data = filter_data(
    data,
    year=selected_year,
    lhd=selected_lhd
)

#KPI Cards for ED and Admissions
ed_total = get_total(
    filtered_data,
    "ED presentations"
)

admissions_total = get_total(
    filtered_data,
    "Hospital admissions"
)

#KPI Cards for Waiting Times 
waiting_time_avg = get_average(filtered_data, "Median ED waiting time (minutes)"
)

#Asthma KPI Card
asthma_filtered = filter_data(
    data, 
    year="2022-23",
    lhd=selected_lhd
)

asthma_avg = get_average(
    asthma_filtered, 
    "Asthma hospitalisation rate (age-standardised, per 100,000)"
)


#KPI Card Creations
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "ED Presentations",
        f"{ed_total:,.0f}"
    )

with col2:
    st.metric(
        "Hospital Admissions",
        f"{admissions_total:,.0f}"
    )

col3, col4 = st.columns(2)

with col3:
    st.metric(
        "Average ED Waiting Time",
        f"{waiting_time_avg:.1f} min"
    )

with col4:
    st.metric(
        "Asthma Hospitalisation Rate",
        f"{asthma_avg:.1f} per 100,000"
    )


#Map for Local Health District
st.subheader("NSW Local Health District Map")
lhd_geojson = load_lhd_geojson()

print([
    feature["properties"].get("lhd_name")
    for feature in lhd_geojson["features"]
])

map_data = data[
    (data["year"] == selected_year) &
    (data["indicator"] == "Median ED waiting time (minutes)")
].copy()

map_data["value"] = pd.to_numeric(
    map_data["value"],
    errors="coerce"
)

#*
map_data["map_lhd"] = (
    map_data["LHD"] + " Local Health District"
)

#

fig = px.choropleth_map(
    map_data,
    geojson=lhd_geojson,
    locations="map_lhd",
    featureidkey="properties.lhd_name",
    color="value",
    hover_name="LHD",
    hover_data={
        "value": ":.1f"
    },
    map_style="carto-positron",
    zoom=4.7,
    center={
        "lat": -32.5,
        "lon": 147.0
    },
    opacity = 0.7,
    labels={
        "value": "Waiting time (min)"
    }

)

fig.update_layout(
    margin={
        "r": 0,
        "t": 0,
        "l": 0,
        "b": 0
    }
)

st.plotly_chart(
    fig, 
    use_container_width=True
)





#Waiting Time Viz
st.subheader("ED Waiting Time Trend")

waiting_trend = data[
    data["indicator"] == "Median ED waiting time (minutes)"
].copy()


waiting_trend = (
    waiting_trend.groupby("year")["value"]
    .mean()
    .reset_index()
)

st.line_chart(
    waiting_trend,
    x='year',
    y='value'
)




# Waiting Time by LHD

st.subheader("ED Waiting Time by LHD")

waiting_lhd = data[
    (data["year"] == selected_year) &
    (data["indicator"] == "Median ED waiting time (minutes)")
].copy()


waiting_lhd = waiting_lhd.sort_values(
    "value",
    ascending=False
)

st.bar_chart(
    waiting_lhd,
    x="LHD",
    y="value"
)



# Asthma Vs LHD

st.subheader("Asthma Hospitalisation Rate by LHD")

asthma_lhd = data[
    (data["year"] == "2022-23") & 
    (
        data["indicator"] == "Asthma hospitalisation rate (age-standardised, per 100,000)"
    )
].copy()


asthma_lhd = asthma_lhd.sort_values(
    "value",
    ascending = False
)

st.bar_chart(
    asthma_lhd,
    x = "LHD",
    y="value"
)

#finding available year for chosen indicator 
# Work out available year for selected indicator
indicator_data = data[
    data["indicator"] == selected_indicator
].copy()

available_years = sorted(
    indicator_data["year"].dropna().unique(),
    reverse=True
)

if selected_year in available_years:
    visual_year = selected_year
else:
    visual_year = available_years[0]

    st.info(
        f"No {selected_indicator} data for {selected_year}. "
        f"Showing {visual_year} instead."
    )




#Map, filtering and dyanmic
st.subheader("NSW Local Health District Map")

lhd_geojson = load_lhd_geojson()

map_data = filter_data(
    data,
    year=visual_year,
    indicator=selected_indicator
)

map_data["value"] = pd.to_numeric(
    map_data["value"],
    errors="coerce"
)

map_data["map_lhd"] = (
    map_data["LHD"] + " Local Health District"
)

if map_data.empty:
    st.warning("No data available for this year and indicator.")

else:
    fig = px.choropleth_map(
        map_data,
        geojson=lhd_geojson,
        locations="map_lhd",
        featureidkey="properties.lhd_name",
        color="value",
        hover_name="LHD",
        hover_data={
            "value": True
        },
        map_style="carto-positron",
        zoom=4.7,
        center={
            "lat": -32.5,
            "lon": 147.0
        },
        opacity=0.7,
        labels={
            "value": selected_indicator
        }
    )

    fig.update_layout(
        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0
        }
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )












#other stuff
indicator_data = data[
    data["indicator"] == selected_indicator
].copy()

available_years = sorted(
    indicator_data["year"].dropna().unique(),
    reverse=True
)

if selected_year in available_years:
    visual_year = selected_year
else:
    visual_year = available_years[0]

    st.info(
        f"No {selected_indicator} data for {selected_year}. "
        f"Showing {visual_year} instead."
    )






#filtered and dynamic trend
st.subheader("Trend Over Time")

trend_data = data[
    data["indicator"] == selected_indicator
].copy()

if selected_lhd != "All":
    trend_data = trend_data[
        trend_data["LHD"] == selected_lhd
    ]

trend_data["value"] = pd.to_numeric(
    trend_data["value"],
    errors="coerce"
)

trend_data = (
    trend_data.groupby("year")["value"]
    .mean()
    .reset_index()
)

if trend_data.empty:
    st.warning("No trend data available.")

else:
    st.line_chart(
        trend_data,
        x="year",
        y="value"
    )


#comparing districts
st.subheader("LHD Comparison")

comparison_data = filter_data(
    data,
    year=selected_year,
    indicator=selected_indicator
)

comparison_data = filter_data(
    data,
    year=visual_year,
    indicator=selected_indicator
)

comparison_data = comparison_data.sort_values(
    "value",
    ascending=False
)

if comparison_data.empty:
    st.warning("No comparison data available.")

else:
    st.bar_chart(
        comparison_data,
        x="LHD",
        y="value"
    )

    if map_data.empty:
        st.warning("No data available for this year and indicator.")