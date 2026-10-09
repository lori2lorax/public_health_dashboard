import subprocess
import json
import ast
import pandas as pd

def get_api(url):
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-X", "GET",
            url,
            "-H", "accept: application/json",
            "-H", "X-SWAGGER-UI: true"
        ],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def get_reported_measure_name(summary):
    if isinstance(summary, str):
        try:
            summary = ast.literal_eval(summary)
        except:
            return None

    if isinstance(summary, dict):
        return summary.get("reported_measure_name")

    return None

def extract_unit_type(x):
    if isinstance(x, dict):
        return x.get(
            "reporting_unit_type", {}
        ).get("reporting_unit_type_name")
    return None

def extract_unit_name(x):
    if isinstance(x, dict):
        return x.get("reporting_unit_name")
    return None

datasets_url = "https://myhospitalsapi.aihw.gov.au/api/v1/datasets"

datasets_data = get_api(datasets_url)
datasets_df = pd.DataFrame(datasets_data["result"])

datasets_df["reported_measure_name"] = (
    datasets_df["reported_measure_summary"]
    .apply(get_reported_measure_name)
)

nsw_lhds = [
    "Central Coast",
    "Far West",
    "Hunter New England",
    "Illawarra Shoalhaven",
    "Mid North Coast",
    "Murrumbidgee",
    "Nepean Blue Mountains",
    "Northern NSW",
    "Northern Sydney",
    "South Eastern Sydney",
    "South Western Sydney",
    "Southern NSW",
    "Sydney",
    "Western NSW",
    "Western Sydney"
]

ed_datasets = datasets_df[
    datasets_df["data_set_name"].str.contains(
        "Number of patients presenting to the emergency department",
        case=False,
        na=False,
        regex=False
    )
    &
    datasets_df["reported_measure_name"]
    .fillna("")
    .str.lower()
    .eq("all patients")
].copy()

all_ed_years = []

for _, row in ed_datasets.iterrows():

    dataset_id = int(row["data_set_id"])

    items_url = (
        f"https://myhospitalsapi.aihw.gov.au/"
        f"api/v1/datasets/{dataset_id}/data-items"
    )

    items_data = get_api(items_url)

    if "result" not in items_data:
        continue

    items_df = pd.DataFrame(items_data["result"])

    if items_df.empty:
        continue

    items_df["unit_type"] = (
        items_df["reporting_unit_summary"]
        .apply(extract_unit_type)
    )

    items_df["unit_name"] = (
        items_df["reporting_unit_summary"]
        .apply(extract_unit_name)
    )

    nsw_df = items_df[
        (items_df["unit_type"] == "Local Hospital Network")
        &
        (items_df["unit_name"].isin(nsw_lhds))
    ].copy()

    if nsw_df.empty:
        continue

    year = (
        row["reporting_start_date"][:4]
        + "-"
        + row["reporting_end_date"][2:4]
    )

    nsw_df["year"] = year
    nsw_df["indicator"] = "ED presentations"
    nsw_df["value"] = pd.to_numeric(
        nsw_df["value"],
        errors="coerce"
    )

    nsw_df = nsw_df[
        ["year", "unit_name", "indicator", "value"]
    ].rename(columns={"unit_name": "LHD"})

    all_ed_years.append(nsw_df)

if all_ed_years:

    all_nsw_ed = pd.concat(
        all_ed_years,
        ignore_index=True
    )

    all_nsw_ed = all_nsw_ed.drop_duplicates(
        subset=["year", "LHD"]
    )

    all_nsw_ed = all_nsw_ed.sort_values(
        ["year", "LHD"]
    ).reset_index(drop=True)
    all_nsw_ed["value"] = all_nsw_ed["value"].astype(int)

    all_nsw_ed.to_csv(
        "nsw_ed_presentations.csv",
        index=False
    )

    print("\nED DATA COMPLETE")
    print("Rows:", len(all_nsw_ed))
    print("Years:", all_nsw_ed["year"].unique())
    print("LHDs:", all_nsw_ed["LHD"].nunique())
    print("Saved: nsw_ed_presentations.csv")

admission_categories = [
    "Medical (emergency)",
    "Medical (non-emergency)",
    "Surgical (emergency)",
    "Surgical (non-emergency)",
    "Other acute (emergency)",
    "Other acute (non-emergency)",
    "Childbirth",
    "Mental health",
    "Rehabilitation",
    "Palliative",
    "Other subacute and non-acute"
]

admission_datasets = datasets_df[
    datasets_df["data_set_name"].str.contains(
        "Number of admissions to hospital",
        case=False,
        na=False,
        regex=False
    )
    &
    datasets_df["reported_measure_name"].isin(
        admission_categories
    )
].copy()

all_admission_categories = []

for _, row in admission_datasets.iterrows():

    dataset_id = int(row["data_set_id"])
    category = row["reported_measure_name"]

    items_url = (
        f"https://myhospitalsapi.aihw.gov.au/"
        f"api/v1/datasets/{dataset_id}/data-items"
    )

    items_data = get_api(items_url)

    if "result" not in items_data:
        continue

    items_df = pd.DataFrame(items_data["result"])

    if items_df.empty:
        continue

    items_df["unit_type"] = (
        items_df["reporting_unit_summary"]
        .apply(extract_unit_type)
    )

    items_df["unit_name"] = (
        items_df["reporting_unit_summary"]
        .apply(extract_unit_name)
    )

    nsw_df = items_df[
        (items_df["unit_type"] == "Local Hospital Network")
        &
        (items_df["unit_name"].isin(nsw_lhds))
    ].copy()

    if nsw_df.empty:
        continue

    year = (
        row["reporting_start_date"][:4]
        + "-"
        + row["reporting_end_date"][2:4]
    )

    nsw_df["year"] = year
    nsw_df["category"] = category

    nsw_df["value"] = pd.to_numeric(
        nsw_df["value"],
        errors="coerce"
    )

    nsw_df = nsw_df[
        ["year", "unit_name", "category", "value"]
    ].rename(columns={"unit_name": "LHD"})

    all_admission_categories.append(nsw_df)

if all_admission_categories:

    admissions_raw = pd.concat(
        all_admission_categories,
        ignore_index=True
    )

    admissions_raw = admissions_raw.drop_duplicates(
        subset=["year", "LHD", "category"]
    )

    all_nsw_admissions = (
        admissions_raw
        .groupby(
            ["year", "LHD"],
            as_index=False
        )["value"]
        .sum(min_count=1)
    )

    all_nsw_admissions["indicator"] = (
        "Hospital admissions"
    )

    all_nsw_admissions = all_nsw_admissions[
        ["year", "LHD", "indicator", "value"]
    ]

    all_nsw_admissions = (
        all_nsw_admissions
        .sort_values(["year", "LHD"])
        .reset_index(drop=True)
    )
    all_nsw_admissions["value"] = all_nsw_admissions["value"].astype(int)

    all_nsw_admissions.to_csv(
        "nsw_admissions.csv",
        index=False
    )

    print("\nADMISSIONS DATA COMPLETE")
    print("Rows:", len(all_nsw_admissions))
    print(
        "Years:",
        all_nsw_admissions["year"].unique()
    )
    print(
        "LHDs:",
        all_nsw_admissions["LHD"].nunique()
    )
    print("Saved: nsw_admissions.csv")

else:
    print("\nNo NSW admissions data found.")





#search = datasets_df[
   # datasets_df["data_set_name"].str.contains(
       # "waiting",
      #  case=False,
       # na=False
  #  )
#]

#print(
   # search[
    #    ["data_set_name", "reported_measure_name"]
  #  ].drop_duplicates().to_string(index=False)
#)
