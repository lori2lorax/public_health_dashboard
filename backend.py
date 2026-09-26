import streamlit as st
import pandas as pd


@st.cache_data
def load_data():
    admissions = pd.read_csv("nsw_admissions.csv")
    ed = pd.read_csv("nsw_ed_presentations.csv")
    waiting_times = pd.read_csv("nsw_waiting_time.csv")
    asthma_hospitalisation_rates = pd.read_csv("nsw_asthma_hospitalisation_rates.csv")

    return admissions, ed, waiting_times, asthma_hospitalisation_rates

def combine_data(admissions, ed, waiting_times, asthma_hospitalisation_rates):
    return pd.concat([admissions, ed, waiting_times, asthma_hospitalisation_rates], ignore_index=True)


#Filters the dataset by year, local hospital district (lhd), and health indicator
def filter_data(df, year=None, lhd=None, indicator=None):
    filtered = df.copy()

    if year:
        filtered = filtered[filtered["year"] == year]

    if lhd and lhd != "All":
        filtered = filtered[filtered["LHD"] == lhd]

    if indicator:
        filtered = filtered[filtered["indicator"] == indicator]

    return filtered


#Calculates the total value for a selected health indicator 
def get_total(df, indicator):
    filtered = df[df["indicator"] == indicator]
    return filtered["value"].sum()

#Calculates the average value for selected health indicator
def get_average(df, indicator):
    filtered = df[df["indicator"] == indicator]
    return filtered["value"].mean()

#Calculates the percentage change between years for a selected LHD and indicator
def calculate_year_change(df, lhd, indicator):
    filtered = df[
        (df["LHD"] == lhd ) &
        (df["indicator"] == indicator)
    ].copy()

    filtered = filtered.sort_values("year")

    filtered["percentage_change"] = (
        filtered["value"].pct_change() * 100
    )

    return filtered 



#Rank lhds by the selected health indicator for a chosen year
def get_lhd_ranking(df, year, indicator):
    filtered = df[
        (df["year"] == year) &
        (df["indicator"] == indicator)
    ].copy()

    ranking = (
        filtered[["LHD", "value"]]
        .sort_values("value", ascending=False)
        .reset_index(drop=True)
    )

    return ranking


#Compares ED presentations with hospital admissions by year and lhd
def compare_ed_admissions(df):
    comparison = df.pivot_table(
        index=["year", "LHD"],
        columns="indicator",
        values="value"
    ).reset_index()

    comparison["ED_to_admissions_ratio"] = (
        comparison["ED presentations"] /
        comparison["Hospital admissions"]
    )

    return comparison



if __name__ == "__main__":

    admissions, ed, waiting_times, asthma_hospitalisation_rates = load_data()

    data = combine_data(
        admissions,
        ed,
        waiting_times,
        asthma_hospitalisation_rates
    )

    print(data.head())

    # Filter data for Western Sydney in 2024-25
    test = filter_data(
        data,
        year="2024-25",
        lhd="Western Sydney"
    )

    print(test)

    # Average waiting time
    waiting_time_avg = get_average(
        test,
        "Median ED waiting time (minutes)"
    )

    print("Average waiting time:", waiting_time_avg)

    # Asthma Average and Asthma Date (Latest available year is 2022-2023)
    asthma_test = filter_data(
        data, 
        year="2022-23",
        lhd="Western Sydney"
    )

    asthma_avg = get_average(
        asthma_test, 
        "Asthma hospitalisation rate (age-standardised, per 100,000)"
    )

    print("Average asthma hospitalisation rate:", asthma_avg)


    # Total ED presentations
    ed_total = get_total(
        test,
        "ED presentations"
    )

    # Total hospital admissions
    admissions_total = get_total(
        test,
        "Hospital admissions"
    )

    print("ED total:", ed_total)
    print("Admissions total:", admissions_total)

    # Percentage change in ED presentations over time
    change_test = calculate_year_change(
        data,
        "Western Sydney",
        "ED presentations"
    )

    print(change_test)

    # Rank LHDs by ED presentations
    ranking_test = get_lhd_ranking(
        data,
        "2024-25",
        "ED presentations"
    )

    print(ranking_test)

    # Compare ED presentations with hospital admissions
    comparison_test = compare_ed_admissions(data)

    print(comparison_test.head())