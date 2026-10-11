
import json
import pandas as pd
import streamlit as st
import plotly.express as px

from backend import (
    load_data,
    combine_data,
    filter_data,
    get_total,
    get_average
)


# Page configuration

st.set_page_config(
    page_title="EpiCentre",
    page_icon="🏥",
    layout="wide"
)



# Loading the datasets using the backend functions

@st.cache_data
def load_lhd_geojson():
    with open(
        "nsw_lhd_boundaries.geojson",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# Load all five datasets
admissions, ed, waiting_times, asthma, smoking = load_data()

data = combine_data(
    admissions,
    ed,
    waiting_times,
    asthma,
    smoking
)

data["value"] = pd.to_numeric(
    data["value"],
    errors="coerce"
)

data = data.dropna(
    subset=["year", "LHD", "indicator", "value"]
).copy()

data["year"] = data["year"].astype(str)
data["LHD"] = data["LHD"].astype(str)
data["indicator"] = data["indicator"].astype(str)


# Health indicator constants

ED = "ED presentations"
ADMISSIONS = "Hospital admissions"
WAITING = "Median ED waiting time (minutes)"
ASTHMA = (
    "Asthma hospitalisation rate "
    "(age-standardised, per 100,000)"
)
SMOKING = "Smoking prevalence"

COUNT_INDICATORS = {ED, ADMISSIONS}


# Helper functions for filtering, aggregation, and formatting

def year_start(year):
    """Extract the starting year from a reporting period."""
    return int(str(year)[:4])


def available_years(df):
    """Return reporting years in chronological order."""
    return sorted(
        df["year"].dropna().unique().tolist(),
        key=year_start
    )


def aggregate_indicator(df, indicator):
    """Aggregate values using the indicator's data type."""

    values = df.loc[
        df["indicator"] == indicator,
        "value"
    ].dropna()

    if values.empty:
        return None

    if indicator in COUNT_INDICATORS:
        return values.sum()

    # Unweighted mean for rates and waiting times
    return values.mean()


def format_kpi(value, suffix="", decimals=1):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:,.{decimals}f}{suffix}"


def latest_year_for_indicator(
    df, indicator, year, lhd="All"
):
    subset = filter_data(
        df,
        lhd=lhd,
        indicator=indicator
    )

    years = available_years(subset)

    if not years:
        return None

    if year != "All" and year in years:
        return year

    return years[-1]


def get_kpi(indicator):
    """Return a KPI and its actual reporting year."""

    year = selected_year

    if year == "All":
        year = latest_year_for_indicator(
            data,
            indicator,
            "All",
            selected_lhd
        )

    if year is None:
        return None, None

    subset = filter_data(
        data,
        year=year,
        lhd=selected_lhd,
        indicator=indicator
    )

    return aggregate_indicator(subset, indicator), year


def prepare_relationship(indicator_x, indicator_y):
    """Match two health indicators by reporting year and LHD."""

    x_data = filter_data(
        data,
        indicator=indicator_x
    ).copy()

    y_data = filter_data(
        data,
        indicator=indicator_y
    ).copy()

    x_agg = (
        "sum" if indicator_x in COUNT_INDICATORS
        else "mean"
    )

    y_agg = (
        "sum" if indicator_y in COUNT_INDICATORS
        else "mean"
    )

    x_data = (
        x_data.groupby(
            ["year", "LHD"],
            as_index=False
        )
        .agg(value=("value", x_agg))
    )

    y_data = (
        y_data.groupby(
            ["year", "LHD"],
            as_index=False
        )
        .agg(value=("value", y_agg))
    )

    merged = pd.merge(
        x_data,
        y_data,
        on=["year", "LHD"],
        suffixes=("_x", "_y")
    )

    if selected_year != "All":
        merged = merged[
            merged["year"] == selected_year
        ]

    if selected_lhd != "All":
        merged = merged[
            merged["LHD"] == selected_lhd
        ]

    return merged


# Epicenter Dashboard Title and Description

st.title("EpiCentre")
st.subheader("Public Health Intelligence Dashboard")

st.caption(
    "Exploring public health outcomes, hospital demand "
    "and regional health patterns across NSW."
)


# Side bar filters for year, LHD, and health indicator

st.sidebar.header("Dashboard Filters")

selected_year = st.sidebar.selectbox(
    "Reporting Year",
    ["All"] + list(reversed(available_years(data)))
)

selected_lhd = st.sidebar.selectbox(
    "Local Health District",
    ["All"] + sorted(data["LHD"].unique().tolist())
)

selected_indicator = st.sidebar.selectbox(
    "Health Indicator",
    sorted(data["indicator"].unique().tolist())
)

st.sidebar.divider()

st.sidebar.caption(
    "Year and LHD filters apply to KPI cards. "
    "The health indicator filter controls the "
    "map, regional analysis and trend charts."
)




# Shared filtering for all tabs

filtered_data = filter_data(
    data,
    year=selected_year,
    lhd=selected_lhd
)

ed_total, ed_year = get_kpi(ED)
admissions_total, admissions_year = get_kpi(ADMISSIONS)
waiting_avg, waiting_year = get_kpi(WAITING)
asthma_avg, asthma_year = get_kpi(ASTHMA)
smoking_avg, smoking_year = get_kpi(SMOKING)


# Determine year for dynamic charts
visual_year = latest_year_for_indicator(
    data,
    selected_indicator,
    selected_year,
    selected_lhd
)

if visual_year is not None:
    visual_data = filter_data(
        data,
        year=visual_year,
        lhd=selected_lhd,
        indicator=selected_indicator
    ).copy()
else:
    visual_data = data.iloc[0:0].copy()




# Dashboard navigation tabs

tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Overview",
    "🗺️ Regional Analysis",
    "📈 Trends",
    "🔬 Health Relationships"
])



# TAB 1: OVERVIEW


with tab1:

    st.header("NSW Health Overview")

    # KPI Cards - first row
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            f"ED Presentations ({ed_year or 'N/A'})",
            format_kpi(ed_total, decimals=0)
        )

    with col2:
        st.metric(
            f"Hospital Admissions ({admissions_year or 'N/A'})",
            format_kpi(admissions_total, decimals=0)
        )

    # KPI Cards - second row
    col3, col4 = st.columns(2)

    with col3:
        st.metric(
            f"Average ED Waiting Time ({waiting_year or 'N/A'})",
            format_kpi(waiting_avg, " min")
        )

    with col4:
        st.metric(
            f"Asthma Hospitalisation Rate ({asthma_year or 'N/A'})",
            format_kpi(asthma_avg, " per 100,000")
        )

    # Smoking KPI
    st.metric(
        f"Smoking Prevalence ({smoking_year or 'N/A'})",
        format_kpi(smoking_avg, "%")
    )

    st.caption(
        "Rates and waiting times are unweighted LHD averages. "
        "They are not official population-weighted NSW estimates. "
        "When 'All' years is selected, each KPI uses its "
        "latest available reporting year."
    )

    st.divider()

    # Dynamic choropleth map
    st.subheader("NSW Local Health District Map")

    if visual_year is None:
        st.warning("No data available for the selected indicator.")

    else:

        if selected_year != "All" and visual_year != selected_year:
            st.info(
                f"No {selected_indicator} data for "
                f"{selected_year} in the selected LHD. "
                f"Showing {visual_year} instead."
            )

        st.caption(
            f"Indicator: {selected_indicator} | "
            f"Reporting year: {visual_year}"
        )

        map_data = visual_data.copy()

        map_data["map_lhd"] = (
            map_data["LHD"] + " Local Health District"
        )

        if map_data.empty:
            st.warning("No map data available.")

        else:
            lhd_geojson = load_lhd_geojson()

            fig_map = px.choropleth_map(
                map_data,
                geojson=lhd_geojson,
                locations="map_lhd",
                featureidkey="properties.lhd_name",
                color="value",
                hover_name="LHD",
                hover_data={"value": ":.1f"},
                map_style="carto-positron",
                zoom=4.7,
                center={
                    "lat": -32.5,
                    "lon": 147.0
                },
                opacity=0.7,
                labels={"value": selected_indicator},
                title=f"{selected_indicator} — {visual_year}"
            )

            fig_map.update_layout(
                margin=dict(r=0, t=40, l=0, b=0)
            )

            st.plotly_chart(
                fig_map,
                use_container_width=True
            )


# TAB 2: REGIONAL ANALYSIS

with tab2:

    st.header("Regional Analysis")

    st.caption(
        "Compare health indicator values across "
        "NSW Local Health Districts."
    )


    # LHD Comparison Bar Chart
    

    st.subheader("Local Health District Comparison")

    if visual_year is None:
        st.warning("No comparison data available.")

    else:

        comparison_data = filter_data(
            data,
            year=visual_year,
            indicator=selected_indicator
        ).copy()

        agg_method = (
            "sum" if selected_indicator in COUNT_INDICATORS
            else "mean"
        )

        comparison_data = (
            comparison_data.groupby(
                "LHD",
                as_index=False
            )
            .agg(value=("value", agg_method))
        )

        comparison_data = comparison_data.sort_values(
            "value",
            ascending=False
        )

        if comparison_data.empty:
            st.warning("No comparison data available.")

        else:
            fig_bar = px.bar(
                comparison_data,
                x="LHD",
                y="value",
                color="LHD",
                title=(
                    f"{selected_indicator} by LHD "
                    f"— {visual_year}"
                ),
                labels={
                    "LHD": "Local Health District",
                    "value": selected_indicator
                }
            )

            fig_bar.update_layout(
                showlegend=False,
                xaxis_tickangle=-45,
                height=550
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

            if selected_lhd != "All":
                st.caption(
                    f"Showing all LHDs for comparison. "
                    f"Selected district: {selected_lhd}."
                )

    st.divider()

    # LHD Performance Heatmap
 

    st.subheader("LHD Performance Heatmap")

    heatmap_data = filter_data(
        data,
        indicator=selected_indicator
    ).copy()

    agg_method = (
        "sum" if selected_indicator in COUNT_INDICATORS
        else "mean"
    )

    heatmap_table = heatmap_data.pivot_table(
        index="LHD",
        columns="year",
        values="value",
        aggfunc=agg_method
    )

    heatmap_table = heatmap_table.reindex(
        sorted(
            heatmap_table.columns,
            key=year_start
        ),
        axis=1
    )

    if heatmap_table.empty:
        st.warning("No data available for the heatmap.")

    else:
        fig_heatmap = px.imshow(
            heatmap_table,
            labels={
                "x": "Reporting Year",
                "y": "Local Health District",
                "color": selected_indicator
            },
            color_continuous_scale="Blues",
            aspect="auto",
            title=f"{selected_indicator} Across NSW LHDs"
        )

        fig_heatmap.update_layout(
            height=650
        )

        st.plotly_chart(
            fig_heatmap,
            use_container_width=True
        )

        st.caption(
            "Darker colours represent higher indicator values. "
            "Missing records appear as blank cells. "
            "The heatmap displays all years and LHDs."
        )


# TAB 3: TRENDS

with tab3:

    st.header("Historical Health Trends")

    st.caption(
        "Explore how public health indicators change "
        "over time across NSW."
    )

    # Trend Over Time


    st.subheader("Trend Over Time")

    trend_data = filter_data(
        data,
        lhd=selected_lhd,
        indicator=selected_indicator
    ).copy()

    aggregation = (
        "sum" if selected_indicator in COUNT_INDICATORS
        else "mean"
    )

    trend_data = (
        trend_data.groupby(
            "year",
            as_index=False
        )
        .agg(value=("value", aggregation))
    )

    trend_data = trend_data.sort_values(
        "year",
        key=lambda s: s.map(year_start)
    )

    if trend_data.empty:
        st.warning("No trend data available.")

    else:
        fig_trend = px.line(
            trend_data,
            x="year",
            y="value",
            markers=True,
            title=f"{selected_indicator} Over Time",
            labels={
                "year": "Reporting Year",
                "value": selected_indicator
            }
        )

        fig_trend.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_trend,
            use_container_width=True
        )

        st.caption(
            "Historical trend displays all available years "
            "for the selected indicator and LHD."
        )

    st.divider()

    # Year-on-Year Percentage Change


    st.subheader("Year-on-Year Percentage Change")

    yoy_data = filter_data(
        data,
        indicator=selected_indicator
    ).copy()

    aggregation = (
        "sum" if selected_indicator in COUNT_INDICATORS
        else "mean"
    )

    yoy_grouped = (
        yoy_data.groupby(
            ["LHD", "year"],
            as_index=False
        )
        .agg(value=("value", aggregation))
    )

    yoy_grouped["start_year"] = (
        yoy_grouped["year"].map(year_start)
    )

    yoy_grouped = yoy_grouped.sort_values(
        ["LHD", "start_year"]
    )

    # Compare each LHD against its previous observation
    yoy_grouped["previous_value"] = (
        yoy_grouped.groupby("LHD")["value"].shift(1)
    )

    yoy_grouped["previous_year"] = (
        yoy_grouped.groupby("LHD")["start_year"].shift(1)
    )

    # Only calculate changes between consecutive years
    consecutive = (
        yoy_grouped["start_year"]
        - yoy_grouped["previous_year"] == 1
    )

    yoy_grouped["percentage_change"] = (
        (
            yoy_grouped["value"]
            - yoy_grouped["previous_value"]
        )
        / yoy_grouped["previous_value"].replace(0, float("nan"))
    ) * 100

    yoy_grouped.loc[
        ~consecutive,
        "percentage_change"
    ] = float("nan")

    # Apply selected year after calculating changes
    if selected_year != "All":
        yoy_grouped = yoy_grouped[
            yoy_grouped["year"] == selected_year
        ]

    else:
        valid_years = available_years(
            yoy_grouped.dropna(
                subset=["percentage_change"]
            )
        )

        if valid_years:
            yoy_grouped = yoy_grouped[
                yoy_grouped["year"] == valid_years[-1]
            ]

    if selected_lhd != "All":
        yoy_grouped = yoy_grouped[
            yoy_grouped["LHD"] == selected_lhd
        ]

    yoy_grouped = yoy_grouped.dropna(
        subset=["percentage_change"]
    )

    yoy_grouped = yoy_grouped.sort_values(
        "percentage_change",
        ascending=False
    )

    if yoy_grouped.empty:
        st.warning(
            "No consecutive-year percentage change data "
            "available for these filters."
        )

    else:
        yoy_year = yoy_grouped["year"].iloc[0]

        fig_yoy = px.bar(
            yoy_grouped,
            x="LHD",
            y="percentage_change",
            color="percentage_change",
            color_continuous_scale="RdYlGn_r",
            color_continuous_midpoint=0,
            title=(
                f"Year-on-Year Change in "
                f"{selected_indicator} — {yoy_year}"
            ),
            labels={
                "LHD": "Local Health District",
                "percentage_change": "Percentage Change (%)"
            }
        )

        fig_yoy.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray"
        )

        fig_yoy.update_layout(
            xaxis_tickangle=-45,
            height=550
        )

        st.plotly_chart(
            fig_yoy,
            use_container_width=True
        )

        st.caption(
            "Positive values indicate an increase; "
            "negative values indicate a decrease. "
            "For prevalence and rate indicators, these "
            "are relative percentage changes, not "
            "percentage-point differences."
        )


# TAB 4: HEALTH RELATIONSHIPS

with tab4:

    st.header("Health Indicator Relationships")

    st.caption(
        "Investigate possible associations between "
        "health outcomes and hospital activity. "
        "Only matching LHD and reporting-year records "
        "are compared."
    )

    
    # Smoking vs Asthma
    

    st.subheader(
        "Smoking Prevalence vs Asthma Hospitalisation"
    )

    smoking_asthma = prepare_relationship(
        SMOKING,
        ASTHMA
    )

    if smoking_asthma.empty:
        st.warning(
            "No matching smoking and asthma data available "
            "for the selected filters."
        )

    else:
        fig_smoking = px.scatter(
            smoking_asthma,
            x="value_x",
            y="value_y",
            color="year",
            hover_name="LHD",
            title=(
                "Smoking Prevalence vs "
                "Asthma Hospitalisation Rate"
            ),
            labels={
                "value_x": "Smoking Prevalence (%)",
                "value_y": (
                    "Asthma Hospitalisation Rate "
                    "(per 100,000)"
                ),
                "year": "Reporting Year"
            }
        )

        fig_smoking.update_traces(
            marker=dict(size=12, opacity=0.75)
        )

        st.plotly_chart(
            fig_smoking,
            use_container_width=True
        )

    st.divider()

    
    # ED Presentations vs Hospital Admissions
    

    st.subheader(
        "ED Presentations vs Hospital Admissions"
    )

    ed_admissions = prepare_relationship(
        ED,
        ADMISSIONS
    )

    if ed_admissions.empty:
        st.warning(
            "No matching ED presentations and admissions "
            "data available."
        )

    else:
        # Select a single shared reporting year
        shared_years = available_years(ed_admissions)

        if selected_year == "All":
            comparison_year = shared_years[-1]
            st.caption(
                f"Showing latest common reporting year: "
                f"{comparison_year}"
            )
        else:
            comparison_year = selected_year

        ed_admissions_chart = ed_admissions[
            ed_admissions["year"] == comparison_year
        ].copy()

        ed_admissions_chart = ed_admissions_chart.rename(
            columns={
                "value_x": ED,
                "value_y": ADMISSIONS
            }
        )

        if not ed_admissions_chart.empty:
            ed_admissions_long = ed_admissions_chart.melt(
                id_vars=["year", "LHD"],
                value_vars=[ED, ADMISSIONS],
                var_name="Health Indicator",
                value_name="Count"
            )

            fig_ed_admissions = px.bar(
                ed_admissions_long,
                x="LHD",
                y="Count",
                color="Health Indicator",
                barmode="group",
                title=(
                    "ED Presentations vs Hospital Admissions "
                    f"— {comparison_year}"
                ),
                labels={
                    "LHD": "Local Health District",
                    "Count": "Reported Count"
                }
            )

            fig_ed_admissions.update_layout(
                xaxis_tickangle=-45,
                height=550
            )

            st.plotly_chart(
                fig_ed_admissions,
                use_container_width=True
            )

        st.caption(
            "These datasets may measure different patient "
            "populations or episodes. Comparisons do not "
            "necessarily indicate direct patient conversion."
        )

    st.divider()

   
    # ED Presentations vs Waiting Times 

    st.subheader(
        "ED Presentations vs Waiting Times"
    )

    ed_waiting = prepare_relationship(
        ED,
        WAITING
    )

    if ed_waiting.empty:
        st.warning(
            "No matching ED and waiting time data available "
            "for the selected filters."
        )

    else:
        fig_ed_waiting = px.scatter(
            ed_waiting,
            x="value_x",
            y="value_y",
            color="year",
            hover_name="LHD",
            title="ED Presentations vs Waiting Times",
            labels={
                "value_x": "ED Presentations",
                "value_y": "Median ED Waiting Time (minutes)",
                "year": "Reporting Year"
            }
        )

        fig_ed_waiting.update_traces(
            marker=dict(size=12, opacity=0.75)
        )

        st.plotly_chart(
            fig_ed_waiting,
            use_container_width=True
        )

        st.caption(
            "This chart explores whether higher ED volumes "
            "are associated with longer waiting times. "
            "Correlation does not imply causation."
        )


# Dashboard footer

st.divider()

st.caption(
    "EpiCentre | NSW Public Health Intelligence Dashboard"
)
