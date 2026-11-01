from pathlib import Path
from math import ceil

import pandas as pd
from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "Fifa.csv"

app = Flask(__name__)


NUMERIC_COLUMNS = [
    "Age",
    "Overall_Rating",
    "Future Potential",
    "Value Per M$",
    "Total_Stats Score",
]
TABLE_COLUMNS = [
    "Name",
    "Country",
    "Position",
    "Age",
    "Overall_Rating",
    "Future Potential",
    "Team",
    "Value Per M$",
    "Total_Stats Score",
]
TABLE_PAGE_SIZE = 100


def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH)
    data.columns = data.columns.str.strip()

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
        data[column] = data[column].fillna(data[column].median())

    for column in ["Name", "Country", "Position", "Team"]:
        data[column] = data[column].fillna("Unknown").astype(str).str.strip()

    return data


df = load_data()


def get_filtered_data() -> pd.DataFrame:
    data = df

    for column, query_key in {
        "Country": "country",
        "Team": "team",
        "Position": "position",
    }.items():
        value = request.args.get(query_key, "").strip()
        if value:
            data = data[data[column] == value]

    search = request.args.get("search", "").strip().lower()
    if search:
        searchable = data["Name"].str.lower().str.contains(search, regex=False)
        searchable |= data["Country"].str.lower().str.contains(search, regex=False)
        searchable |= data["Team"].str.lower().str.contains(search, regex=False)
        searchable |= data["Position"].str.lower().str.contains(search, regex=False)
        data = data[searchable]

    range_filters = {
        "Age": ("min_age", "max_age"),
        "Overall_Rating": ("min_overall", "max_overall"),
    }
    for column, (min_key, max_key) in range_filters.items():
        minimum = request.args.get(min_key, type=float)
        maximum = request.args.get(max_key, type=float)
        if minimum is not None:
            data = data[data[column] >= minimum]
        if maximum is not None:
            data = data[data[column] <= maximum]

    return data


def rounded_number(value: float, digits: int = 1) -> float:
    return round(float(value), digits) if pd.notna(value) else 0


def build_dashboard_payload(data: pd.DataFrame, page: int = 1) -> dict:
    if data.empty:
        return {
            "summary": {
                "players": 0,
                "countries": 0,
                "teams": 0,
                "avg_overall": 0,
                "avg_age": 0,
                "avg_value": 0,
                "max_value": 0,
                "top_value_player": "—",
                "top_player": "—",
            },
            "charts": {
                "positions": {"labels": [], "data": []},
                "countries": {"labels": [], "data": []},
                "teams": {"labels": [], "data": []},
                "ratings": {"labels": [], "data": []},
                "ages": {"labels": [], "data": []},
                "market_values": {"labels": [], "data": []},
                "team_values": {"labels": [], "data": []},
                "country_values": {"labels": [], "data": []},
            },
            "players": [],
            "total_rows": 0,
            "page": 0,
            "page_size": TABLE_PAGE_SIZE,
            "total_pages": 0,
        }

    top_player = data.sort_values(
        ["Overall_Rating", "Future Potential", "Total_Stats Score"],
        ascending=False,
    ).iloc[0]

    position_counts = data["Position"].value_counts().sort_values(ascending=False)
    country_counts = data["Country"].value_counts().head(10)

    team_performance = (
        data.groupby("Team", as_index=False)
        .agg(avg_rating=("Overall_Rating", "mean"), players=("Name", "size"))
        .sort_values(["avg_rating", "players"], ascending=[False, False])
        .head(10)
    )

    rating_bins = [0, 49, 59, 69, 79, 89, 100]
    rating_labels = ["< 50", "50–59", "60–69", "70–79", "80–89", "90+"]
    rating_distribution = (
        pd.cut(
            data["Overall_Rating"],
            bins=rating_bins,
            labels=rating_labels,
            include_lowest=True,
        )
        .value_counts()
        .reindex(rating_labels, fill_value=0)
    )

    age_performance = data.groupby("Age")["Overall_Rating"].mean().round(1)
    market_value_leaders = data.sort_values(
        ["Value Per M$", "Overall_Rating"], ascending=False
    ).head(10)
    team_values = (
        data.groupby("Team", as_index=False)
        .agg(total_value=("Value Per M$", "sum"), players=("Name", "size"))
        .sort_values(["total_value", "players"], ascending=[False, False])
        .head(10)
    )
    country_values = (
        data.groupby("Country", as_index=False)
        .agg(total_value=("Value Per M$", "sum"), players=("Name", "size"))
        .sort_values(["total_value", "players"], ascending=[False, False])
        .head(10)
    )
    sorted_players = data.sort_values(
        ["Overall_Rating", "Future Potential"], ascending=False
    )
    total_rows = len(sorted_players)
    total_pages = ceil(total_rows / TABLE_PAGE_SIZE)
    current_page = min(max(page, 1), total_pages)
    start_index = (current_page - 1) * TABLE_PAGE_SIZE
    table_data = sorted_players.iloc[
        start_index : start_index + TABLE_PAGE_SIZE
    ][TABLE_COLUMNS].copy()
    table_data["Value Per M$"] = table_data["Value Per M$"].round(2)

    return {
        "summary": {
            "players": int(len(data)),
            "countries": int(data["Country"].nunique()),
            "teams": int(data["Team"].nunique()),
            "avg_overall": rounded_number(data["Overall_Rating"].mean()),
            "avg_age": rounded_number(data["Age"].mean()),
            "avg_value": rounded_number(data["Value Per M$"].mean(), 2),
            "max_value": rounded_number(data["Value Per M$"].max(), 2),
            "top_value_player": str(market_value_leaders.iloc[0]["Name"]),
            "top_player": str(top_player["Name"]),
        },
        "charts": {
            "positions": {
                "labels": position_counts.index.tolist(),
                "data": position_counts.astype(int).tolist(),
            },
            "countries": {
                "labels": country_counts.index.tolist(),
                "data": country_counts.astype(int).tolist(),
            },
            "teams": {
                "labels": team_performance["Team"].tolist(),
                "data": team_performance["avg_rating"].round(1).tolist(),
            },
            "ratings": {
                "labels": rating_distribution.index.tolist(),
                "data": rating_distribution.astype(int).tolist(),
            },
            "ages": {
                "labels": [str(age) for age in age_performance.index.tolist()],
                "data": age_performance.tolist(),
            },
            "market_values": {
                "labels": market_value_leaders["Name"].tolist(),
                "data": market_value_leaders["Value Per M$"].round(2).tolist(),
            },
            "team_values": {
                "labels": team_values["Team"].tolist(),
                "data": team_values["total_value"].round(2).tolist(),
            },
            "country_values": {
                "labels": country_values["Country"].tolist(),
                "data": country_values["total_value"].round(2).tolist(),
            },
        },
        "players": table_data.to_dict(orient="records"),
        "total_rows": int(total_rows),
        "page": int(current_page),
        "page_size": TABLE_PAGE_SIZE,
        "total_pages": int(total_pages),
    }


@app.route("/")
def dashboard():
    filter_options = {
        "countries": sorted(df["Country"].unique().tolist()),
        "teams": sorted(df["Team"].unique().tolist()),
        "positions": sorted(df["Position"].unique().tolist()),
        "age_min": int(df["Age"].min()),
        "age_max": int(df["Age"].max()),
        "overall_min": int(df["Overall_Rating"].min()),
        "overall_max": int(df["Overall_Rating"].max()),
    }
    return render_template(
        "dashboard.html",
        filter_options=filter_options,
        dataset_rows=len(df),
    )


@app.route("/api/dashboard")
def dashboard_data():
    page = request.args.get("page", default=1, type=int) or 1
    return jsonify(build_dashboard_payload(get_filtered_data(), page=page))


if __name__ == "__main__":
    app.run(debug=True)
