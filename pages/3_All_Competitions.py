from pathlib import Path
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_helpers import install_player_search


install_player_search()


# =========================================================
# PAGE
# =========================================================

st.title("🏆 All Competitions Player Lab")

st.write(
    "Compare Premier League-listed players across the league, "
    "domestic cups and European competitions — separately or combined."
)

st.caption(
    "Competition data source: olbauday/FPL-Core-Insights. "
    "Cup and European detailed coverage can be less complete than "
    "Premier League coverage, so coverage is shown explicitly below."
)


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "all_competitions_player_stats.csv"
)

META_FILE = (
    Path(__file__).resolve().parent.parent
    / "all_competitions_metadata.json"
)


RAW_COLUMNS = [
    "minutes_played",
    "goals",
    "assists",
    "total_shots",
    "xg",
    "xa",
    "shots_on_target",
    "successful_dribbles",
    "big_chances_missed",
    "touches_opposition_box",
    "touches",
    "chances_created",
    "tackles",
    "tackles_won",
    "interceptions",
    "recoveries",
    "blocks",
    "clearances",
    "duels_won",
    "duels_lost",
    "dispossessed",
]


@st.cache_data
def load_data():
    df = pd.read_csv(
        DATA_FILE
    )

    for col in RAW_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    def stable_key(row):
        code = row.get(
            "player_code"
        )

        if pd.notna(code):
            try:
                return (
                    "code:"
                    + str(int(float(code)))
                )
            except Exception:
                return (
                    "code:"
                    + str(code)
                )

        full = (
            f'{row.get("first_name", "")} '
            f'{row.get("second_name", "")}'
        ).strip()

        if full:
            return (
                "name:"
                + full.casefold()
            )

        return (
            "web:"
            + str(
                row.get(
                    "web_name",
                    ""
                )
            ).casefold()
        )

    df["player_key"] = df.apply(
        stable_key,
        axis=1,
    )

    return df


@st.cache_data
def load_metadata():
    if not META_FILE.exists():
        return {}

    return json.loads(
        META_FILE.read_text(
            encoding="utf-8"
        )
    )


DATA = load_data()
META = load_metadata()


def season_sort_key(value):
    try:
        return int(
            str(value)[:4]
        )
    except Exception:
        return 0


SEASONS = sorted(
    DATA["season"]
    .dropna()
    .astype(str)
    .unique(),
    key=season_sort_key,
    reverse=True,
)


ALL_COMPETITIONS = sorted(
    DATA["competition"]
    .dropna()
    .astype(str)
    .unique()
)


def is_friendly(comp):
    text = str(comp).casefold()

    return (
        "friendly" in text
        or "pre-season" in text
        or "preseason" in text
    )


def is_europe(comp):
    text = str(comp).casefold()

    return any(
        term in text
        for term in [
            "champions league",
            "europa league",
            "conference league",
        ]
    )


def is_domestic_cup(comp):
    text = str(comp).casefold()

    return any(
        term in text
        for term in [
            "fa cup",
            "efl cup",
            "league cup",
            "community shield",
        ]
    )


def is_league(comp):
    return (
        str(comp).casefold()
        == "premier league"
    )


def available_competitions(seasons):
    return sorted(
        DATA.loc[
            DATA["season"].isin(
                seasons
            ),
            "competition",
        ]
        .dropna()
        .astype(str)
        .unique()
    )


def competitions_for_preset(
    preset,
    available,
):
    if preset == "League only":
        return [
            c
            for c in available
            if is_league(c)
        ]

    if preset == "Europe only":
        return [
            c
            for c in available
            if is_europe(c)
        ]

    if preset == "Domestic cups":
        return [
            c
            for c in available
            if is_domestic_cup(c)
        ]

    if preset == "All competitive":
        return [
            c
            for c in available
            if not is_friendly(c)
        ]

    return []


def safe_rate(
    numerator,
    denominator,
    multiplier=1,
):
    num = pd.to_numeric(
        numerator,
        errors="coerce",
    )

    den = (
        pd.to_numeric(
            denominator,
            errors="coerce",
        )
        .replace(
            0,
            np.nan,
        )
    )

    return (
        num
        / den
        * multiplier
    )


def add_metrics(df):
    df = df.copy()

    mins = df[
        "minutes_played"
    ]

    touches = df[
        "touches"
    ]

    df[
        "goals_per_90"
    ] = safe_rate(
        df["goals"],
        mins,
        90,
    )

    df[
        "assists_per_90"
    ] = safe_rate(
        df["assists"],
        mins,
        90,
    )

    df[
        "xg_per_90"
    ] = safe_rate(
        df["xg"],
        mins,
        90,
    )

    df[
        "xa_per_90"
    ] = safe_rate(
        df["xa"],
        mins,
        90,
    )

    df[
        "xgi_per_90"
    ] = safe_rate(
        df["xg"]
        + df["xa"],
        mins,
        90,
    )

    df[
        "shots_per_90"
    ] = safe_rate(
        df["total_shots"],
        mins,
        90,
    )

    df[
        "shots_on_target_per_90"
    ] = safe_rate(
        df["shots_on_target"],
        mins,
        90,
    )

    df[
        "chances_created_per_90"
    ] = safe_rate(
        df["chances_created"],
        mins,
        90,
    )

    df[
        "dribbles_per_90"
    ] = safe_rate(
        df["successful_dribbles"],
        mins,
        90,
    )

    df[
        "box_touches_per_90"
    ] = safe_rate(
        df["touches_opposition_box"],
        mins,
        90,
    )

    df[
        "touches_per_90"
    ] = safe_rate(
        df["touches"],
        mins,
        90,
    )

    for metric in [
        "tackles",
        "tackles_won",
        "interceptions",
        "recoveries",
        "blocks",
        "clearances",
        "duels_won",
    ]:
        df[
            f"{metric}_per_90"
        ] = safe_rate(
            df[metric],
            mins,
            90,
        )

    df[
        "goals_per_100_touches"
    ] = safe_rate(
        df["goals"],
        touches,
        100,
    )

    df[
        "assists_per_100_touches"
    ] = safe_rate(
        df["assists"],
        touches,
        100,
    )

    df[
        "xg_per_100_touches"
    ] = safe_rate(
        df["xg"],
        touches,
        100,
    )

    df[
        "xa_per_100_touches"
    ] = safe_rate(
        df["xa"],
        touches,
        100,
    )

    df[
        "xgi_per_100_touches"
    ] = safe_rate(
        df["xg"]
        + df["xa"],
        touches,
        100,
    )

    df[
        "shots_per_100_touches"
    ] = safe_rate(
        df["total_shots"],
        touches,
        100,
    )

    df[
        "shots_on_target_per_100_touches"
    ] = safe_rate(
        df["shots_on_target"],
        touches,
        100,
    )

    df[
        "chances_created_per_100_touches"
    ] = safe_rate(
        df["chances_created"],
        touches,
        100,
    )

    df[
        "dribbles_per_100_touches"
    ] = safe_rate(
        df["successful_dribbles"],
        touches,
        100,
    )

    df[
        "box_touches_per_100_touches"
    ] = safe_rate(
        df["touches_opposition_box"],
        touches,
        100,
    )

    df[
        "dispossessed_per_100_touches"
    ] = safe_rate(
        df["dispossessed"],
        touches,
        100,
    )

    df[
        "goals_minus_xg"
    ] = (
        df["goals"]
        - df["xg"]
    )

    return df


def aggregate_period(
    seasons,
    competitions,
):
    subset = DATA.loc[
        DATA["season"].isin(
            seasons
        )
        & DATA[
            "competition"
        ].isin(
            competitions
        )
    ].copy()

    if subset.empty:
        return pd.DataFrame()

    totals = (
        subset
        .groupby(
            "player_key",
            as_index=False,
        )[RAW_COLUMNS]
        .sum(
            min_count=1
        )
    )

    info = (
        subset
        .sort_values(
            "minutes_played",
            ascending=False,
        )
        .drop_duplicates(
            "player_key"
        )[
            [
                "player_key",
                "web_name",
                "first_name",
                "second_name",
                "position",
            ]
        ]
    )

    seasons_count = (
        subset.loc[
            subset[
                "minutes_played"
            ].fillna(0) > 0
        ]
        .groupby(
            "player_key"
        )["season"]
        .nunique()
        .rename(
            "seasons_represented"
        )
        .reset_index()
    )

    comps_count = (
        subset.loc[
            subset[
                "minutes_played"
            ].fillna(0) > 0
        ]
        .groupby(
            "player_key"
        )["competition"]
        .nunique()
        .rename(
            "competitions_represented"
        )
        .reset_index()
    )

    result = (
        totals
        .merge(
            info,
            on="player_key",
            how="left",
        )
        .merge(
            seasons_count,
            on="player_key",
            how="left",
        )
        .merge(
            comps_count,
            on="player_key",
            how="left",
        )
    )

    return add_metrics(
        result
    )


def player_breakdown(
    player_key,
    seasons,
    competitions,
):
    cols = [
        "season",
        "competition",
        "minutes_played",
        "goals",
        "assists",
        "xg",
        "xa",
        "touches",
    ]

    return (
        DATA.loc[
            (
                DATA[
                    "player_key"
                ]
                == player_key
            )
            & DATA[
                "season"
            ].isin(
                seasons
            )
            & DATA[
                "competition"
            ].isin(
                competitions
            ),
            cols,
        ]
        .sort_values(
            [
                "season",
                "competition",
            ]
        )
    )


def fmt(
    value,
    decimals=2,
    integer=False,
):
    if pd.isna(value):
        return "—"

    if integer:
        return (
            f"{int(round(float(value))):,}"
        )

    return (
        f"{float(value):.{decimals}f}"
    )


def percentile_rank(
    value,
    peers,
    reverse=False,
):
    if pd.isna(value):
        return np.nan

    values = (
        pd.to_numeric(
            peers,
            errors="coerce",
        )
        .dropna()
    )

    if values.empty:
        return np.nan

    value = float(value)

    if reverse:
        below = (
            values
            > value
        ).sum()
    else:
        below = (
            values
            < value
        ).sum()

    equal = (
        values
        == value
    ).sum()

    return (
        (
            below
            + 0.5
            * equal
        )
        / len(values)
        * 100
    )


def coverage_entries(
    seasons,
    competitions,
):
    entries = []

    for item in META.get(
        "competitions",
        []
    ):
        if (
            item.get("season")
            in seasons
            and item.get(
                "competition"
            )
            in competitions
        ):
            entries.append(item)

    return entries


def coverage_text(
    seasons,
    competitions,
):
    entries = coverage_entries(
        seasons,
        competitions,
    )

    pieces = []

    for item in entries:
        coverage = item.get(
            "coverage_pct"
        )

        if coverage is None:
            cov = "coverage unknown"
        else:
            cov = f"{coverage:.0f}%"

        pieces.append(
            f'{item.get("season")} '
            f'· {item.get("competition")}: '
            f'{cov}'
        )

    return " | ".join(
        pieces
    )


def short_period(profile):
    comps = profile[
        "competitions"
    ]

    if len(comps) == 1:
        comp_text = comps[0]
    else:
        comp_text = (
            f"{len(comps)} comps"
        )

    seasons = profile[
        "seasons"
    ]

    season_text = (
        seasons[0]
        if len(seasons) == 1
        else f"{len(seasons)} seasons"
    )

    return (
        f"{profile['player']} · "
        f"{season_text} · "
        f"{comp_text}"
    )


# =========================================================
# SOURCE FRESHNESS
# =========================================================

if META.get(
    "source_updated_at"
):
    source_date = str(
        META[
            "source_updated_at"
        ]
    )[:10]

    st.info(
        "Competition source last updated: "
        f"**{source_date}**"
    )


# =========================================================
# PROFILE SELECTION
# =========================================================

st.header(
    "Compare player periods"
)

profile_count = st.radio(
    "Number of profiles",
    [2, 3],
    horizontal=True,
)

profile_columns = st.columns(
    profile_count
)

profiles = []

default_players = [
    "Saka",
    "Haaland",
    "Ødegaard",
]


for i in range(
    profile_count
):
    with profile_columns[i]:

        st.subheader(
            f"Profile {i + 1}"
        )

        seasons = st.multiselect(
            f"Season(s) {i + 1}",
            SEASONS,
            default=[
                SEASONS[0]
            ],
            key=(
                f"allcomp_seasons_{i}"
            ),
        )

        if not seasons:
            st.warning(
                "Choose at least one season."
            )
            st.stop()

        available = (
            available_competitions(
                seasons
            )
        )

        preset = st.selectbox(
            f"Competition group {i + 1}",
            [
                "League only",
                "Europe only",
                "Domestic cups",
                "All competitive",
                "Custom",
            ],
            index=0,
            key=(
                f"allcomp_preset_{i}"
            ),
        )

        if preset == "Custom":
            competitions = st.multiselect(
                f"Competition(s) {i + 1}",
                available,
                default=available,
                key=(
                    f"allcomp_custom_{i}"
                ),
            )
        else:
            competitions = (
                competitions_for_preset(
                    preset,
                    available,
                )
            )

            st.caption(
                "Included: "
                + (
                    ", ".join(
                        competitions
                    )
                    if competitions
                    else "none available"
                )
            )

        if not competitions:
            st.warning(
                "No competitions are available "
                "for this selection."
            )
            st.stop()

        period_df = aggregate_period(
            seasons,
            competitions,
        )

        if period_df.empty:
            st.warning(
                "No player data available."
            )
            st.stop()

        player_options = sorted(
            period_df[
                "web_name"
            ]
            .dropna()
            .astype(str)
            .unique()
        )

        default_index = 0

        preferred = (
            default_players[i]
            if i < len(
                default_players
            )
            else None
        )

        if (
            preferred is not None
            and preferred
            in player_options
        ):
            default_index = (
                player_options.index(
                    preferred
                )
            )

        player = st.selectbox(
            f"Player {i + 1}",
            player_options,
            index=default_index,
            key=(
                f"allcomp_player_{i}_"
                + "_".join(
                    seasons
                )
                + "_"
                + str(
                    hash(
                        tuple(
                            competitions
                        )
                    )
                )
            ),
        )

        player_rows = (
            period_df.loc[
                period_df[
                    "web_name"
                ]
                == player
            ]
        )

        row = player_rows.iloc[0]

        player_key = row[
            "player_key"
        ]

        profiles.append(
            {
                "player": player,
                "player_key":
                    player_key,
                "seasons":
                    seasons,
                "competitions":
                    competitions,
                "row":
                    row,
                "period_df":
                    period_df,
            }
        )

        st.caption(
            f'{fmt(row["minutes_played"], integer=True)} mins '
            f'· {int(row["competitions_represented"])} competitions'
        )

        cov_text = coverage_text(
            seasons,
            competitions,
        )

        if cov_text:
            st.caption(
                "Detailed match coverage: "
                + cov_text
            )

        with st.expander(
            "Competition breakdown"
        ):
            breakdown = (
                player_breakdown(
                    player_key,
                    seasons,
                    competitions,
                )
            )

            st.dataframe(
                breakdown.round(2),
                hide_index=True,
                use_container_width=True,
            )


# =========================================================
# COVERAGE WARNING
# =========================================================

incomplete = []

for profile in profiles:
    for item in coverage_entries(
        profile["seasons"],
        profile[
            "competitions"
        ],
    ):
        coverage = item.get(
            "coverage_pct"
        )

        if (
            coverage is not None
            and coverage < 99.5
        ):
            incomplete.append(
                (
                    item.get("season"),
                    item.get(
                        "competition"
                    ),
                    coverage,
                )
            )

if incomplete:
    unique_incomplete = sorted(
        set(incomplete)
    )

    text = "; ".join(
        f"{season} {comp}: "
        f"{coverage:.0f}%"
        for (
            season,
            comp,
            coverage,
        )
        in unique_incomplete
    )

    st.warning(
        "Some selected competitions have incomplete "
        "detailed player-match coverage. Stats reflect "
        "the matches for which detailed player data were captured. "
        + text
    )


# =========================================================
# COMPARISON
# =========================================================

st.header(
    "Comparison"
)


TOTAL_METRICS = [
    (
        "Minutes",
        "minutes_played",
        0,
        True,
    ),
    (
        "Goals",
        "goals",
        0,
        True,
    ),
    (
        "Assists",
        "assists",
        0,
        True,
    ),
    (
        "xG",
        "xg",
        2,
        False,
    ),
    (
        "xA",
        "xa",
        2,
        False,
    ),
    (
        "Goals − xG",
        "goals_minus_xg",
        2,
        False,
    ),
    (
        "Shots",
        "total_shots",
        0,
        True,
    ),
    (
        "Shots on target",
        "shots_on_target",
        0,
        True,
    ),
    (
        "Chances created",
        "chances_created",
        0,
        True,
    ),
    (
        "Successful dribbles",
        "successful_dribbles",
        0,
        True,
    ),
    (
        "Touches",
        "touches",
        0,
        True,
    ),
    (
        "Opposition-box touches",
        "touches_opposition_box",
        0,
        True,
    ),
]


PER90_METRICS = [
    (
        "Goals / 90",
        "goals_per_90",
    ),
    (
        "Assists / 90",
        "assists_per_90",
    ),
    (
        "xG / 90",
        "xg_per_90",
    ),
    (
        "xA / 90",
        "xa_per_90",
    ),
    (
        "xG+xA / 90",
        "xgi_per_90",
    ),
    (
        "Shots / 90",
        "shots_per_90",
    ),
    (
        "Shots on target / 90",
        "shots_on_target_per_90",
    ),
    (
        "Chances created / 90",
        "chances_created_per_90",
    ),
    (
        "Dribbles / 90",
        "dribbles_per_90",
    ),
    (
        "Box touches / 90",
        "box_touches_per_90",
    ),
    (
        "Touches / 90",
        "touches_per_90",
    ),
    (
        "Tackles / 90",
        "tackles_per_90",
    ),
    (
        "Interceptions / 90",
        "interceptions_per_90",
    ),
    (
        "Recoveries / 90",
        "recoveries_per_90",
    ),
]


PER_TOUCH_METRICS = [
    (
        "Goals / 100 touches",
        "goals_per_100_touches",
    ),
    (
        "Assists / 100 touches",
        "assists_per_100_touches",
    ),
    (
        "xG / 100 touches",
        "xg_per_100_touches",
    ),
    (
        "xA / 100 touches",
        "xa_per_100_touches",
    ),
    (
        "xG+xA / 100 touches",
        "xgi_per_100_touches",
    ),
    (
        "Shots / 100 touches",
        "shots_per_100_touches",
    ),
    (
        "Shots on target / 100 touches",
        "shots_on_target_per_100_touches",
    ),
    (
        "Chances created / 100 touches",
        "chances_created_per_100_touches",
    ),
    (
        "Dribbles / 100 touches",
        "dribbles_per_100_touches",
    ),
    (
        "Box touches / 100 touches",
        "box_touches_per_100_touches",
    ),
    (
        "Dispossessed / 100 touches",
        "dispossessed_per_100_touches",
    ),
]


def comparison_table(
    metrics,
    totals=False,
):
    rows = []

    for metric in metrics:
        if totals:
            (
                label,
                column,
                decimals,
                integer,
            ) = metric
        else:
            label, column = metric
            decimals = 2
            integer = False

        item = {
            "Metric": label
        }

        for profile in profiles:
            item[
                short_period(
                    profile
                )
            ] = fmt(
                profile[
                    "row"
                ][column],
                decimals,
                integer,
            )

        rows.append(item)

    return pd.DataFrame(
        rows
    )


tab1, tab2, tab3 = st.tabs(
    [
        "Totals",
        "Per 90",
        "Per 100 touches",
    ]
)

with tab1:
    st.dataframe(
        comparison_table(
            TOTAL_METRICS,
            totals=True,
        ),
        hide_index=True,
        use_container_width=True,
    )

with tab2:
    st.dataframe(
        comparison_table(
            PER90_METRICS
        ),
        hide_index=True,
        use_container_width=True,
    )

with tab3:
    st.dataframe(
        comparison_table(
            PER_TOUCH_METRICS
        ),
        hide_index=True,
        use_container_width=True,
    )


# =========================================================
# PEER SETTINGS
# =========================================================

st.header(
    "Peer comparison"
)

min_minutes = st.number_input(
    "Minimum minutes for peer groups",
    min_value=0,
    max_value=10000,
    value=450,
    step=90,
)


# =========================================================
# SCATTER
# =========================================================

st.subheader(
    "Player landscape"
)

st.caption(
    "The background population uses Profile 1's "
    "selected seasons and competitions."
)


SCATTER_METRICS = {
    "Goals / 90":
        "goals_per_90",
    "Assists / 90":
        "assists_per_90",
    "xG / 90":
        "xg_per_90",
    "xA / 90":
        "xa_per_90",
    "xG+xA / 90":
        "xgi_per_90",
    "Shots / 90":
        "shots_per_90",
    "Chances created / 90":
        "chances_created_per_90",
    "Touches / 90":
        "touches_per_90",
    "Goals / 100 touches":
        "goals_per_100_touches",
    "xG / 100 touches":
        "xg_per_100_touches",
    "xG+xA / 100 touches":
        "xgi_per_100_touches",
    "Shots / 100 touches":
        "shots_per_100_touches",
    "Chances created / 100 touches":
        "chances_created_per_100_touches",
}


metric_names = list(
    SCATTER_METRICS.keys()
)

scatter_cols = st.columns(2)

with scatter_cols[0]:
    x_name = st.selectbox(
        "X-axis",
        metric_names,
        index=metric_names.index(
            "Touches / 90"
        ),
    )

with scatter_cols[1]:
    y_name = st.selectbox(
        "Y-axis",
        metric_names,
        index=metric_names.index(
            "xG+xA / 100 touches"
        ),
    )

x_col = SCATTER_METRICS[
    x_name
]

y_col = SCATTER_METRICS[
    y_name
]


population = (
    profiles[0][
        "period_df"
    ].copy()
)

selected_position = (
    profiles[0][
        "row"
    ]["position"]
)

population = population.loc[
    (
        population[
            "minutes_played"
        ]
        >= min_minutes
    )
    & (
        population[
            "position"
        ]
        == selected_position
    )
].copy()

population = population.dropna(
    subset=[
        x_col,
        y_col,
    ]
)

fig_scatter = px.scatter(
    population,
    x=x_col,
    y=y_col,
    size="minutes_played",
    size_max=18,
    hover_name="web_name",
    hover_data=[
        "minutes_played",
        "goals",
        "assists",
        "xg",
        "xa",
    ],
    labels={
        x_col: x_name,
        y_col: y_name,
    },
)

for profile in profiles:
    row = profile["row"]

    if (
        pd.isna(
            row[x_col]
        )
        or pd.isna(
            row[y_col]
        )
    ):
        continue

    fig_scatter.add_trace(
        go.Scatter(
            x=[
                row[x_col]
            ],
            y=[
                row[y_col]
            ],
            mode="markers+text",
            text=[
                profile["player"]
            ],
            textposition="top center",
            marker=dict(
                size=20,
                symbol="diamond",
            ),
            name=short_period(
                profile
            ),
        )
    )

st.plotly_chart(
    fig_scatter,
    use_container_width=True,
)


# =========================================================
# RADAR
# =========================================================

st.subheader(
    "Position-relative radar"
)

radar_mode = st.radio(
    "Radar normalisation",
    [
        "Per 100 touches",
        "Per 90",
    ],
    horizontal=True,
)


if (
    radar_mode
    == "Per 100 touches"
):
    RADAR_METRICS = {
        "Goals / 100 touches":
            (
                "goals_per_100_touches",
                False,
            ),
        "Assists / 100 touches":
            (
                "assists_per_100_touches",
                False,
            ),
        "xG / 100 touches":
            (
                "xg_per_100_touches",
                False,
            ),
        "xA / 100 touches":
            (
                "xa_per_100_touches",
                False,
            ),
        "Shots / 100 touches":
            (
                "shots_per_100_touches",
                False,
            ),
        "Chances created / 100 touches":
            (
                "chances_created_per_100_touches",
                False,
            ),
        "Dribbles / 100 touches":
            (
                "dribbles_per_100_touches",
                False,
            ),
        "Box touches / 100 touches":
            (
                "box_touches_per_100_touches",
                False,
            ),
        "Ball security":
            (
                "dispossessed_per_100_touches",
                True,
            ),
        "Touches / 90":
            (
                "touches_per_90",
                False,
            ),
        "Tackles / 90":
            (
                "tackles_per_90",
                False,
            ),
        "Interceptions / 90":
            (
                "interceptions_per_90",
                False,
            ),
    }

else:
    RADAR_METRICS = {
        "Goals / 90":
            (
                "goals_per_90",
                False,
            ),
        "Assists / 90":
            (
                "assists_per_90",
                False,
            ),
        "xG / 90":
            (
                "xg_per_90",
                False,
            ),
        "xA / 90":
            (
                "xa_per_90",
                False,
            ),
        "Shots / 90":
            (
                "shots_per_90",
                False,
            ),
        "Chances created / 90":
            (
                "chances_created_per_90",
                False,
            ),
        "Dribbles / 90":
            (
                "dribbles_per_90",
                False,
            ),
        "Box touches / 90":
            (
                "box_touches_per_90",
                False,
            ),
        "Touches / 90":
            (
                "touches_per_90",
                False,
            ),
        "Tackles / 90":
            (
                "tackles_per_90",
                False,
            ),
        "Interceptions / 90":
            (
                "interceptions_per_90",
                False,
            ),
        "Recoveries / 90":
            (
                "recoveries_per_90",
                False,
            ),
    }


radar_choices = list(
    RADAR_METRICS.keys()
)

default_radar = radar_choices[
    : min(
        8,
        len(radar_choices),
    )
]

selected_radar = st.multiselect(
    "Choose radar metrics",
    radar_choices,
    default=default_radar,
    max_selections=10,
)


if len(selected_radar) < 3:
    st.warning(
        "Choose at least three radar metrics."
    )

else:
    fig_radar = go.Figure()

    raw_table = {
        "Metric":
            selected_radar
    }

    pct_table = {
        "Metric":
            selected_radar
    }

    for profile in profiles:
        row = profile["row"]

        peers = (
            profile[
                "period_df"
            ]
            .loc[
                (
                    profile[
                        "period_df"
                    ][
                        "position"
                    ]
                    == row[
                        "position"
                    ]
                )
                & (
                    profile[
                        "period_df"
                    ][
                        "minutes_played"
                    ]
                    >= min_minutes
                )
            ]
            .copy()
        )

        percentiles = []
        actuals = []

        for label in selected_radar:
            column, reverse = (
                RADAR_METRICS[
                    label
                ]
            )

            actual = row[
                column
            ]

            percentile = (
                percentile_rank(
                    actual,
                    peers[
                        column
                    ],
                    reverse=reverse,
                )
            )

            actuals.append(
                actual
            )

            percentiles.append(
                percentile
            )

        name = short_period(
            profile
        )

        fig_radar.add_trace(
            go.Scatterpolar(
                r=percentiles,
                theta=selected_radar,
                fill="toself",
                name=name,
                customdata=actuals,
                hovertemplate=(
                    "<b>%{theta}</b>"
                    "<br>Percentile: %{r:.0f}"
                    "<br>Actual: %{customdata:.2f}"
                    "<extra>%{fullData.name}</extra>"
                ),
            )
        )

        raw_table[
            name
        ] = [
            fmt(x, 2)
            for x in actuals
        ]

        pct_table[
            name
        ] = [
            (
                "—"
                if pd.isna(x)
                else f"{x:.0f}"
            )
            for x in percentiles
        ]

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[
                    0,
                    100,
                ],
            )
        ),
        height=760,
        showlegend=True,
    )

    st.plotly_chart(
        fig_radar,
        use_container_width=True,
    )

    raw_tab, pct_tab = st.tabs(
        [
            "Raw values",
            "Percentiles",
        ]
    )

    with raw_tab:
        st.dataframe(
            pd.DataFrame(
                raw_table
            ),
            hide_index=True,
            use_container_width=True,
        )

    with pct_tab:
        st.dataframe(
            pd.DataFrame(
                pct_table
            ),
            hide_index=True,
            use_container_width=True,
        )


# =========================================================
# EXPLANATION
# =========================================================

with st.expander(
    "How combinations are calculated"
):
    st.markdown(
        """
When several competitions or seasons are selected, the app:

1. adds the player's raw totals across the selected matches;
2. adds the minutes and touches across those same matches;
3. recalculates per-90 and per-100-touch values from the combined totals.

It does **not** average competition-level rates.

For example, choosing **Premier League + Champions League** produces one
combined player sample containing only those two competitions.

The background peer population for each radar player uses that player's
own selected seasons and competitions, plus the minimum-minutes filter.

Cup and European detailed player-match coverage can be incomplete in the
underlying source. Where that happens, the app displays a coverage warning
rather than assuming missing matches contain zero events.
"""
    )
