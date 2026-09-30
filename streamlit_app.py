import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Football Player Lab",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Football Player Lab")

st.write(
    "Compare Premier League players across individual seasons "
    "or grouped multi-season samples."
)


# =========================================================
# SOURCE FILES
# =========================================================

SEASON_FILES = {
    "2026/27": "premier_league_2026_27.csv",
    "2025/26": "premier_league_2025_26.csv",
    "2024/25": "premier_league_2024_25.csv",
    "2023/24": "premier_league_2023_24.csv",
    "2022/23": "premier_league_2022_23.csv",
    "2021/22": "premier_league_2021_22.csv",
}


RAW_NUMERIC = [
    "minutes_played",
    "goals",
    "assists",
    "touches",
    "touches_opposition_box",
    "xg",
    "xa",
    "total_shots",
    "shots_on_target",
    "successful_dribbles",
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


# These are not available for every historical season.
PARTIAL_COVERAGE = [
    "xg",
    "xa",
    "touches_opposition_box",
]


# =========================================================
# CALCULATION HELPERS
# =========================================================

def rate(
    numerator,
    denominator,
    multiplier=1,
):

    num = pd.to_numeric(
        numerator,
        errors="coerce",
    ).astype(float)

    den = pd.to_numeric(
        denominator,
        errors="coerce",
    ).astype(float)

    den = den.replace(
        0,
        float("nan"),
    )

    return (
        num
        / den
        * multiplier
    )


def derive_metrics(df):

    df = df.copy()

    df["goal_involvements"] = (
        df["goals"]
        + df["assists"]
    )

    df["xgi"] = (
        df["xg"]
        + df["xa"]
    )

    mins = df["minutes_played"]
    touches = df["touches"]
    shots = df["total_shots"]


    # =====================================================
    # PER 90
    # =====================================================

    per90 = {

        "touches_per_90":
            touches,

        "goals_per_90":
            df["goals"],

        "assists_per_90":
            df["assists"],

        "GI_per_90":
            df["goal_involvements"],

        "xG_per_90":
            df["xg"],

        "xA_per_90":
            df["xa"],

        "xGI_per_90":
            df["xgi"],

        "shots_per_90":
            shots,

        "shots_on_target_per_90":
            df["shots_on_target"],

        "chances_created_per_90":
            df["chances_created"],

        "dribbles_per_90":
            df["successful_dribbles"],

        "box_touches_per_90":
            df["touches_opposition_box"],

        "dispossessed_per_90":
            df["dispossessed"],

        "tackles_per_90":
            df["tackles"],

        "tackles_won_per_90":
            df["tackles_won"],

        "interceptions_per_90":
            df["interceptions"],

        "recoveries_per_90":
            df["recoveries"],

        "blocks_per_90":
            df["blocks"],

        "clearances_per_90":
            df["clearances"],

        "duels_won_per_90":
            df["duels_won"],
    }


    for new_col, numerator in per90.items():

        df[new_col] = rate(
            numerator,
            mins,
            90,
        )


    # =====================================================
    # PER 100 TOUCHES
    # =====================================================

    per100 = {

        "goals_per_100_touches":
            df["goals"],

        "assists_per_100_touches":
            df["assists"],

        "GI_per_100_touches":
            df["goal_involvements"],

        "xG_per_100_touches":
            df["xg"],

        "xA_per_100_touches":
            df["xa"],

        "xGI_per_100_touches":
            df["xgi"],

        "shots_per_100_touches":
            shots,

        "shots_on_target_per_100_touches":
            df["shots_on_target"],

        "chances_created_per_100_touches":
            df["chances_created"],

        "dribbles_per_100_touches":
            df["successful_dribbles"],

        "box_touches_per_100_touches":
            df["touches_opposition_box"],

        "dispossessed_per_100_touches":
            df["dispossessed"],
    }


    for new_col, numerator in per100.items():

        df[new_col] = rate(
            numerator,
            touches,
            100,
        )


    # =====================================================
    # EFFICIENCY
    # =====================================================

    df["shot_accuracy_pct"] = rate(
        df["shots_on_target"],
        shots,
        100,
    )

    df["goal_conversion_pct"] = rate(
        df["goals"],
        shots,
        100,
    )

    df["xG_per_shot"] = rate(
        df["xg"],
        shots,
    )

    df["tackle_success_pct"] = rate(
        df["tackles_won"],
        df["tackles"],
        100,
    )

    df["duel_win_pct"] = rate(

        df["duels_won"],

        (
            df["duels_won"]
            + df["duels_lost"]
        ),

        100,
    )

    df["goals_minus_xG"] = (
        df["goals"]
        - df["xg"]
    )

    df["goals_minus_xG_per_90"] = rate(
        df["goals_minus_xG"],
        mins,
        90,
    )

    df["goals_minus_xG_per_100_touches"] = rate(
        df["goals_minus_xG"],
        touches,
        100,
    )

    return df


# =========================================================
# LOAD INDIVIDUAL SEASONS
# =========================================================

@st.cache_data
def load_raw_season(season):

    df = pd.read_csv(
        SEASON_FILES[season]
    ).copy()


    for col in RAW_NUMERIC:

        if col not in df.columns:
            df[col] = pd.NA

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )


    # 2021/22 has no xG/xA in our source.

    if season == "2021/22":

        df["xg"] = float("nan")
        df["xa"] = float("nan")


    # Historical source has no opposition-box touches
    # before 2025/26.

    if season in {
        "2021/22",
        "2022/23",
        "2023/24",
        "2024/25",
    }:

        df[
            "touches_opposition_box"
        ] = float("nan")


    df["season"] = season

    df["web_name"] = (
        df["web_name"]
        .astype(str)
    )

    df["position"] = (
        df["position"]
        .astype(str)
    )

    return df


# =========================================================
# MULTI-SEASON AGGREGATION
# =========================================================

def period_label(seasons):

    return " + ".join(
        seasons
    )


@st.cache_data
def aggregate_period(
    seasons_tuple
):

    seasons = list(
        seasons_tuple
    )


    frames = [

        load_raw_season(
            season
        )

        for season
        in seasons
    ]


    combined = pd.concat(
        frames,
        ignore_index=True,
    )


    # -----------------------------------------------------
    # SUM THE RAW TOTALS FIRST
    # -----------------------------------------------------

    totals = (

        combined
        .groupby(
            "web_name",
            as_index=False,
        )[RAW_NUMERIC]
        .sum(
            min_count=1
        )
    )


    # -----------------------------------------------------
    # ASSIGN DOMINANT POSITION
    #
    # If a player's listed position changed between seasons,
    # use the position in which he played most minutes.
    # -----------------------------------------------------

    pos_minutes = (

        combined
        .groupby(
            [
                "web_name",
                "position",
            ],
            as_index=False,
        )[
            "minutes_played"
        ]
        .sum(
            min_count=1
        )
        .sort_values(
            [
                "web_name",
                "minutes_played",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop_duplicates(
            "web_name"
        )[
            [
                "web_name",
                "position",
            ]
        ]
    )


    totals = totals.merge(
        pos_minutes,
        on="web_name",
        how="left",
    )


    # -----------------------------------------------------
    # COUNT HOW MANY OF THE SELECTED SEASONS EACH PLAYER
    # ACTUALLY PLAYED IN
    # -----------------------------------------------------

    represented = (

        combined.loc[
            combined[
                "minutes_played"
            ].fillna(0) > 0
        ]
        .groupby(
            "web_name"
        )[
            "season"
        ]
        .nunique()
    )


    totals[
        "seasons_represented"
    ] = (

        totals[
            "web_name"
        ]
        .map(
            represented
        )
        .fillna(0)
    )


    totals[
        "selected_season_count"
    ] = len(
        seasons
    )


    # -----------------------------------------------------
    # DON'T CREATE PARTIAL xG / xA / BOX-TOUCH SAMPLES
    #
    # If ANY season in a grouped period lacks a metric,
    # hide that metric for the whole period.
    # -----------------------------------------------------

    for col in PARTIAL_COVERAGE:

        missing_season = any(

            load_raw_season(
                season
            )[col]
            .notna()
            .sum()
            == 0

            for season
            in seasons
        )


        if missing_season:

            totals[
                col
            ] = float(
                "nan"
            )


    totals[
        "period"
    ] = period_label(
        seasons
    )


    # -----------------------------------------------------
    # ONLY NOW CALCULATE PER-90 / PER-TOUCH METRICS
    # -----------------------------------------------------

    return derive_metrics(
        totals
    )


# =========================================================
# SMALL HELPERS
# =========================================================

def player_row(
    period_df,
    player,
):

    return period_df.loc[

        period_df[
            "web_name"
        ]
        == player

    ].iloc[0]


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


def has_data(
    frame,
    column,
):

    return (

        column
        in frame.columns

        and

        frame[
            column
        ]
        .notna()
        .any()
    )


def percentile_rank(
    value,
    peer_values,
    lower_is_better=False,
):

    if pd.isna(value):

        return float(
            "nan"
        )


    peers = pd.to_numeric(
        peer_values,
        errors="coerce",
    ).dropna()


    if peers.empty:

        return float(
            "nan"
        )


    value = float(
        value
    )


    equal = (
        peers
        == value
    ).sum()


    if lower_is_better:

        better = (
            peers
            > value
        ).sum()

    else:

        better = (
            peers
            < value
        ).sum()


    return (

        (
            better
            + 0.5
            * equal
        )

        / len(
            peers
        )

        * 100
    )


# =========================================================
# PROFILE SELECTION
# =========================================================

st.header(
    "Compare player periods"
)


st.caption(
    "Choose one season for a normal season comparison, "
    "or select several seasons to create one combined player sample."
)


compare_count = st.radio(

    "Number of profiles",

    [
        2,
        3,
    ],

    horizontal=True,
)


defaults = [

    (
        [
            "2025/26"
        ],

        [
            "Haaland",
            "Erling Haaland",
        ],
    ),

    (
        [
            "2025/26"
        ],

        [
            "Gyökeres",
            "Viktor Gyökeres",
        ],
    ),

    (
        [
            "2023/24",
            "2024/25",
        ],

        [
            "Salah",
            "Mohamed Salah",
        ],
    ),
]


profiles = []

slot_columns = st.columns(
    compare_count
)


for i in range(
    compare_count
):

    with slot_columns[i]:

        chosen_seasons = st.multiselect(

            f"Season(s) {i + 1}",

            list(
                SEASON_FILES
            ),

            default=defaults[
                i
            ][0],

            key=(
                f"period_seasons_"
                f"{i}"
            ),
        )


        if not chosen_seasons:

            st.warning(
                "Choose at least one season."
            )

            st.stop()


        period_df = aggregate_period(
            tuple(
                chosen_seasons
            )
        )


        options = sorted(

            period_df[
                "web_name"
            ]
            .dropna()
            .astype(str)
            .unique()
        )


        player_index = 0


        for preferred in defaults[
            i
        ][1]:

            if preferred in options:

                player_index = (
                    options.index(
                        preferred
                    )
                )

                break


        chosen_player = st.selectbox(

            f"Player {i + 1}",

            options,

            index=player_index,

            key=(
                f"period_player_"
                f"{i}_"
                f"{'_'.join(chosen_seasons)}"
            ),
        )


        row = player_row(
            period_df,
            chosen_player,
        )


        profiles.append(

            {
                "seasons":
                    chosen_seasons,

                "period":
                    period_label(
                        chosen_seasons
                    ),

                "df":
                    period_df,

                "player":
                    chosen_player,

                "row":
                    row,

                "position":
                    str(
                        row[
                            "position"
                        ]
                    ),
            }
        )


        st.caption(

            f'{int(row["seasons_represented"])} '
            f'of {len(chosen_seasons)} selected seasons represented · '
            f'{fmt(row["minutes_played"], integer=True)} minutes'
        )


# =========================================================
# PEER SAMPLE
# =========================================================

sample_pct = st.slider(

    "Minimum sample for peer groups "
    "(% of maximum minutes in each selected period)",

    0,

    100,

    25,

    5,
)


threshold_text = []


for profile in profiles:

    max_mins = pd.to_numeric(

        profile[
            "df"
        ][
            "minutes_played"
        ],

        errors="coerce",

    ).max()


    if (
        pd.isna(max_mins)
        or max_mins <= 0
    ):

        threshold = 0

    else:

        threshold = (

            max_mins
            * sample_pct
            / 100
        )


    profile[
        "threshold"
    ] = threshold


    threshold_text.append(

        f'{profile["period"]}: '
        f'{threshold:.0f}+ min'
    )


st.caption(

    "Peer thresholds — "

    + " · ".join(
        dict.fromkeys(
            threshold_text
        )
    )
)


# =========================================================
# TABLE METRICS
# =========================================================

OVERVIEW = [

    (
        "Seasons represented",
        "seasons_represented",
        0,
        True,
    ),

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
        "Goal involvements",
        "goal_involvements",
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
        "goals_minus_xG",
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
        "Shot accuracy %",
        "shot_accuracy_pct",
        1,
        False,
    ),

    (
        "Goal conversion %",
        "goal_conversion_pct",
        1,
        False,
    ),

    (
        "xG / shot",
        "xG_per_shot",
        2,
        False,
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
        "Touches in opposition box",
        "touches_opposition_box",
        0,
        True,
    ),

    (
        "Dispossessed",
        "dispossessed",
        0,
        True,
    ),

    (
        "Tackles",
        "tackles",
        0,
        True,
    ),

    (
        "Tackles won",
        "tackles_won",
        0,
        True,
    ),

    (
        "Tackle success %",
        "tackle_success_pct",
        1,
        False,
    ),

    (
        "Interceptions",
        "interceptions",
        0,
        True,
    ),

    (
        "Recoveries",
        "recoveries",
        0,
        True,
    ),

    (
        "Blocks",
        "blocks",
        0,
        True,
    ),

    (
        "Clearances",
        "clearances",
        0,
        True,
    ),

    (
        "Duels won",
        "duels_won",
        0,
        True,
    ),

    (
        "Duel win %",
        "duel_win_pct",
        1,
        False,
    ),
]


PER90_TABLE = [

    (
        "Goals / 90",
        "goals_per_90",
        2,
        False,
    ),

    (
        "Assists / 90",
        "assists_per_90",
        2,
        False,
    ),

    (
        "G+A / 90",
        "GI_per_90",
        2,
        False,
    ),

    (
        "xG / 90",
        "xG_per_90",
        2,
        False,
    ),

    (
        "xA / 90",
        "xA_per_90",
        2,
        False,
    ),

    (
        "xG+xA / 90",
        "xGI_per_90",
        2,
        False,
    ),

    (
        "Goals − xG / 90",
        "goals_minus_xG_per_90",
        2,
        False,
    ),

    (
        "Shots / 90",
        "shots_per_90",
        2,
        False,
    ),

    (
        "Shots on target / 90",
        "shots_on_target_per_90",
        2,
        False,
    ),

    (
        "Chances created / 90",
        "chances_created_per_90",
        2,
        False,
    ),

    (
        "Dribbles / 90",
        "dribbles_per_90",
        2,
        False,
    ),

    (
        "Touches / 90",
        "touches_per_90",
        2,
        False,
    ),

    (
        "Box touches / 90",
        "box_touches_per_90",
        2,
        False,
    ),

    (
        "Dispossessed / 90",
        "dispossessed_per_90",
        2,
        False,
    ),

    (
        "Tackles / 90",
        "tackles_per_90",
        2,
        False,
    ),

    (
        "Tackles won / 90",
        "tackles_won_per_90",
        2,
        False,
    ),

    (
        "Interceptions / 90",
        "interceptions_per_90",
        2,
        False,
    ),

    (
        "Recoveries / 90",
        "recoveries_per_90",
        2,
        False,
    ),

    (
        "Blocks / 90",
        "blocks_per_90",
        2,
        False,
    ),

    (
        "Clearances / 90",
        "clearances_per_90",
        2,
        False,
    ),

    (
        "Duels won / 90",
        "duels_won_per_90",
        2,
        False,
    ),
]


PER100_TABLE = [

    (
        "Goals / 100 touches",
        "goals_per_100_touches",
        2,
        False,
    ),

    (
        "Assists / 100 touches",
        "assists_per_100_touches",
        2,
        False,
    ),

    (
        "G+A / 100 touches",
        "GI_per_100_touches",
        2,
        False,
    ),

    (
        "xG / 100 touches",
        "xG_per_100_touches",
        2,
        False,
    ),

    (
        "xA / 100 touches",
        "xA_per_100_touches",
        2,
        False,
    ),

    (
        "xG+xA / 100 touches",
        "xGI_per_100_touches",
        2,
        False,
    ),

    (
        "Goals − xG / 100 touches",
        "goals_minus_xG_per_100_touches",
        2,
        False,
    ),

    (
        "Shots / 100 touches",
        "shots_per_100_touches",
        2,
        False,
    ),

    (
        "Shots on target / 100 touches",
        "shots_on_target_per_100_touches",
        2,
        False,
    ),

    (
        "Chances created / 100 touches",
        "chances_created_per_100_touches",
        2,
        False,
    ),

    (
        "Dribbles / 100 touches",
        "dribbles_per_100_touches",
        2,
        False,
    ),

    (
        "Box touches / 100 touches",
        "box_touches_per_100_touches",
        2,
        False,
    ),

    (
        "Dispossessed / 100 touches",
        "dispossessed_per_100_touches",
        2,
        False,
    ),
]


# =========================================================
# COMPARISON TABLE
# =========================================================

def make_table(
    specs
):

    rows = []


    for (
        label,
        col,
        decimals,
        integer,
    ) in specs:

        values = [

            profile[
                "row"
            ].get(
                col,
                pd.NA,
            )

            for profile
            in profiles
        ]


        if all(

            pd.isna(
                value
            )

            for value
            in values
        ):

            continue


        item = {
            "Metric":
                label
        }


        for (
            profile,
            value,
        ) in zip(
            profiles,
            values,
        ):

            name = (

                f'{profile["player"]} · '
                f'{profile["period"]}'
            )


            item[
                name
            ] = fmt(

                value,

                decimals,

                integer,
            )


        rows.append(
            item
        )


    return pd.DataFrame(
        rows
    )


st.header(
    "Comparison"
)


tab1, tab2, tab3 = st.tabs(

    [
        "Overview",
        "Per 90",
        "Per 100 touches",
    ]
)


with tab1:

    st.dataframe(

        make_table(
            OVERVIEW
        ),

        hide_index=True,

        width="stretch",
    )


with tab2:

    st.dataframe(

        make_table(
            PER90_TABLE
        ),

        hide_index=True,

        width="stretch",
    )


with tab3:

    st.dataframe(

        make_table(
            PER100_TABLE
        ),

        hide_index=True,

        width="stretch",
    )


# =========================================================
# GENERAL METRIC LIST
# =========================================================

METRICS = {

    "Touches / 90":
        "touches_per_90",

    "Goals / 90":
        "goals_per_90",

    "Assists / 90":
        "assists_per_90",

    "G+A / 90":
        "GI_per_90",

    "xG / 90":
        "xG_per_90",

    "xA / 90":
        "xA_per_90",

    "xG+xA / 90":
        "xGI_per_90",

    "Goals / 100 touches":
        "goals_per_100_touches",

    "Assists / 100 touches":
        "assists_per_100_touches",

    "G+A / 100 touches":
        "GI_per_100_touches",

    "xG / 100 touches":
        "xG_per_100_touches",

    "xA / 100 touches":
        "xA_per_100_touches",

    "xG+xA / 100 touches":
        "xGI_per_100_touches",

    "Shots / 90":
        "shots_per_90",

    "Shots / 100 touches":
        "shots_per_100_touches",

    "Shots on target / 90":
        "shots_on_target_per_90",

    "Shots on target / 100 touches":
        "shots_on_target_per_100_touches",

    "Chances created / 90":
        "chances_created_per_90",

    "Chances created / 100 touches":
        "chances_created_per_100_touches",

    "Dribbles / 90":
        "dribbles_per_90",

    "Dribbles / 100 touches":
        "dribbles_per_100_touches",

    "Box touches / 90":
        "box_touches_per_90",

    "Box touches / 100 touches":
        "box_touches_per_100_touches",

    "Shot accuracy %":
        "shot_accuracy_pct",

    "Goal conversion %":
        "goal_conversion_pct",

    "xG / shot":
        "xG_per_shot",

    "Goals − xG / 90":
        "goals_minus_xG_per_90",

    "Goals − xG / 100 touches":
        "goals_minus_xG_per_100_touches",

    "Ball losses / 90":
        "dispossessed_per_90",

    "Ball losses / 100 touches":
        "dispossessed_per_100_touches",

    "Tackles / 90":
        "tackles_per_90",

    "Tackles won / 90":
        "tackles_won_per_90",

    "Tackle success %":
        "tackle_success_pct",

    "Interceptions / 90":
        "interceptions_per_90",

    "Recoveries / 90":
        "recoveries_per_90",

    "Blocks / 90":
        "blocks_per_90",

    "Clearances / 90":
        "clearances_per_90",

    "Duels won / 90":
        "duels_won_per_90",

    "Duel win %":
        "duel_win_pct",
}


# =========================================================
# UNIQUE PERIODS
# =========================================================

unique_periods = {}


for profile in profiles:

    unique_periods[
        tuple(
            profile[
                "seasons"
            ]
        )
    ] = profile[
        "df"
    ]


COMMON_METRICS = {

    label:
        col

    for (
        label,
        col,
    ) in METRICS.items()

    if all(

        has_data(
            period_df,
            col,
        )

        for period_df
        in unique_periods.values()
    )
}


# =========================================================
# SCATTER
# =========================================================

st.header(
    "Player landscape"
)


st.caption(
    "For grouped seasons, every background player is also "
    "aggregated across exactly the same group of seasons."
)


metric_labels = list(
    COMMON_METRICS
)


if metric_labels:

    preferred_y = (

        "xG+xA / 100 touches"

        if (
            "xG+xA / 100 touches"
            in COMMON_METRICS
        )

        else (
            "G+A / 100 touches"
        )
    )


    c1, c2, c3 = st.columns(
        3
    )


    with c1:

        x_label = st.selectbox(

            "X-axis",

            metric_labels,

            index=(

                metric_labels.index(
                    "Touches / 90"
                )

                if (
                    "Touches / 90"
                    in metric_labels
                )

                else 0
            ),
        )


    with c2:

        y_label = st.selectbox(

            "Y-axis",

            metric_labels,

            index=(

                metric_labels.index(
                    preferred_y
                )

                if preferred_y
                in metric_labels

                else min(
                    1,
                    len(
                        metric_labels
                    ) - 1,
                )
            ),
        )


    all_positions = sorted(

        {

            str(
                pos
            )

            for period_df
            in unique_periods.values()

            for pos
            in period_df[
                "position"
            ]
            .dropna()
            .unique()
        }
    )


    position_options = [

        "All positions",

        *all_positions,
    ]


    with c3:

        default_position = (
            profiles[
                0
            ][
                "position"
            ]
        )


        position_filter = st.selectbox(

            "Position filter",

            position_options,

            index=(

                position_options.index(
                    default_position
                )

                if default_position
                in position_options

                else 0
            ),
        )


    x_col = (
        COMMON_METRICS[
            x_label
        ]
    )


    y_col = (
        COMMON_METRICS[
            y_label
        ]
    )


    frames = []


    for (
        seasons_tuple,
        period_df,
    ) in unique_periods.items():

        period = period_label(
            list(
                seasons_tuple
            )
        )


        max_mins = pd.to_numeric(

            period_df[
                "minutes_played"
            ],

            errors="coerce",

        ).max()


        if (
            pd.isna(max_mins)
            or max_mins <= 0
        ):

            threshold = 0

        else:

            threshold = (

                max_mins
                * sample_pct
                / 100
            )


        frame = period_df.loc[

            period_df[
                "minutes_played"
            ]
            >= threshold

        ].copy()


        if (
            position_filter
            != "All positions"
        ):

            frame = frame.loc[

                frame[
                    "position"
                ]
                .astype(str)

                ==

                position_filter

            ].copy()


        frame[
            "period_label"
        ] = period


        if (
            pd.isna(max_mins)
            or max_mins <= 0
        ):

            frame[
                "minutes_share"
            ] = 0

        else:

            frame[
                "minutes_share"
            ] = (

                frame[
                    "minutes_played"
                ]

                / max_mins

                * 100
            )


        frame[
            "hover_name"
        ] = (

            frame[
                "web_name"
            ]

            + " · "

            + period
        )


        frames.append(
            frame
        )


    landscape = pd.concat(

        frames,

        ignore_index=True,
    )


    landscape = landscape.dropna(

        subset=[
            x_col,
            y_col,
        ]
    )


    fig_scatter = px.scatter(

        landscape,

        x=x_col,

        y=y_col,

        hover_name="hover_name",

        hover_data=[

            "position",

            "minutes_played",

            "goals",

            "assists",
        ],

        color="period_label",

        size="minutes_share",

        labels={

            x_col:
                x_label,

            y_col:
                y_label,

            "period_label":
                "Period",

            "minutes_share":
                "Period minutes %",
        },
    )


    # Highlight the selected profiles.

    for profile in profiles:

        if (

            position_filter
            != "All positions"

            and

            profile[
                "position"
            ]
            != position_filter
        ):

            continue


        row = (
            profile[
                "row"
            ]
        )


        if (

            pd.isna(
                row[
                    x_col
                ]
            )

            or

            pd.isna(
                row[
                    y_col
                ]
            )
        ):

            continue


        name = (

            f'{profile["player"]} · '
            f'{profile["period"]}'
        )


        fig_scatter.add_trace(

            go.Scatter(

                x=[
                    row[
                        x_col
                    ]
                ],

                y=[
                    row[
                        y_col
                    ]
                ],

                mode="markers+text",

                text=[
                    name
                ],

                textposition="top center",

                marker=dict(

                    size=18,

                    symbol="diamond",

                    line=dict(
                        width=2
                    ),
                ),

                name=name,
            )
        )


    st.plotly_chart(

        fig_scatter,

        width="stretch",
    )


else:

    st.warning(
        "No common metrics are available for these periods."
    )


# =========================================================
# RADAR
# =========================================================

st.header(
    "Player profile radar"
)


st.caption(
    "Each grouped player is compared with positional peers "
    "aggregated across exactly the same selected seasons."
)


radar_mode = st.radio(

    "Radar basis",

    [
        "Per 100 touches",
        "Per 90",
    ],

    horizontal=True,
)


# =========================================================
# PER TOUCH RADAR
# =========================================================

if (
    radar_mode
    == "Per 100 touches"
):

    st.info(
        "Per 100 touches mode: attacking and on-ball volume "
        "is measured per 100 touches. Defensive actions remain per 90."
    )


    RADAR_CANDIDATES = {

        "Goals / 100 touches":
            "goals_per_100_touches",

        "Assists / 100 touches":
            "assists_per_100_touches",

        "G+A / 100 touches":
            "GI_per_100_touches",

        "xG / 100 touches":
            "xG_per_100_touches",

        "xA / 100 touches":
            "xA_per_100_touches",

        "xG+xA / 100 touches":
            "xGI_per_100_touches",

        "Shots / 100 touches":
            "shots_per_100_touches",

        "Shots on target / 100 touches":
            "shots_on_target_per_100_touches",

        "Chances created / 100 touches":
            "chances_created_per_100_touches",

        "Dribbles / 100 touches":
            "dribbles_per_100_touches",

        "Box touches / 100 touches":
            "box_touches_per_100_touches",

        "Ball security (fewer losses / 100 touches)":
            "dispossessed_per_100_touches",

        "Touches / 90":
            "touches_per_90",

        "Shot accuracy %":
            "shot_accuracy_pct",

        "Goal conversion %":
            "goal_conversion_pct",

        "xG / shot":
            "xG_per_shot",

        "Goals − xG / 100 touches":
            "goals_minus_xG_per_100_touches",

        "Tackles / 90":
            "tackles_per_90",

        "Tackles won / 90":
            "tackles_won_per_90",

        "Tackle success %":
            "tackle_success_pct",

        "Interceptions / 90":
            "interceptions_per_90",

        "Recoveries / 90":
            "recoveries_per_90",

        "Blocks / 90":
            "blocks_per_90",

        "Clearances / 90":
            "clearances_per_90",

        "Duels won / 90":
            "duels_won_per_90",

        "Duel win %":
            "duel_win_pct",
    }


    preferred_radar = [

        "Goals / 100 touches",

        "xG / 100 touches",

        "Assists / 100 touches",

        "xA / 100 touches",

        "Shots / 100 touches",

        "Chances created / 100 touches",
    ]


# =========================================================
# PER 90 RADAR
# =========================================================

else:

    st.info(
        "Per 90 mode: volume metrics are measured per 90 minutes."
    )


    RADAR_CANDIDATES = {

        "Goals / 90":
            "goals_per_90",

        "Assists / 90":
            "assists_per_90",

        "G+A / 90":
            "GI_per_90",

        "xG / 90":
            "xG_per_90",

        "xA / 90":
            "xA_per_90",

        "xG+xA / 90":
            "xGI_per_90",

        "Shots / 90":
            "shots_per_90",

        "Shots on target / 90":
            "shots_on_target_per_90",

        "Chances created / 90":
            "chances_created_per_90",

        "Dribbles / 90":
            "dribbles_per_90",

        "Box touches / 90":
            "box_touches_per_90",

        "Ball security (fewer losses / 90)":
            "dispossessed_per_90",

        "Touches / 90":
            "touches_per_90",

        "Shot accuracy %":
            "shot_accuracy_pct",

        "Goal conversion %":
            "goal_conversion_pct",

        "xG / shot":
            "xG_per_shot",

        "Goals − xG / 90":
            "goals_minus_xG_per_90",

        "Tackles / 90":
            "tackles_per_90",

        "Tackles won / 90":
            "tackles_won_per_90",

        "Tackle success %":
            "tackle_success_pct",

        "Interceptions / 90":
            "interceptions_per_90",

        "Recoveries / 90":
            "recoveries_per_90",

        "Blocks / 90":
            "blocks_per_90",

        "Clearances / 90":
            "clearances_per_90",

        "Duels won / 90":
            "duels_won_per_90",

        "Duel win %":
            "duel_win_pct",
    }


    preferred_radar = [

        "Goals / 90",

        "xG / 90",

        "Assists / 90",

        "xA / 90",

        "Shots / 90",

        "Chances created / 90",
    ]


# =========================================================
# REMOVE METRICS MISSING FROM ANY SELECTED PERIOD
# =========================================================

RADAR = {

    label:
        col

    for (
        label,
        col,
    ) in RADAR_CANDIDATES.items()

    if all(

        has_data(
            period_df,
            col,
        )

        for period_df
        in unique_periods.values()
    )
}


default_radar = [

    metric

    for metric
    in preferred_radar

    if metric
    in RADAR
]


for metric in RADAR:

    if len(
        default_radar
    ) >= 6:

        break


    if metric not in default_radar:

        default_radar.append(
            metric
        )


selected_radar = st.multiselect(

    "Choose radar metrics",

    list(
        RADAR
    ),

    default=default_radar,

    max_selections=12,

    key=(
        f"radar_"
        f"{radar_mode}"
    ),
)


LOWER_IS_BETTER = {

    "dispossessed_per_90",

    "dispossessed_per_100_touches",
}


# =========================================================
# DRAW RADAR
# =========================================================

if len(
    selected_radar
) < 3:

    st.warning(
        "Choose at least three radar metrics."
    )


else:

    fig_radar = go.Figure()


    raw_table = {
        "Metric":
            selected_radar
    }


    percentile_table = {
        "Metric":
            selected_radar
    }


    for profile in profiles:

        row = (
            profile[
                "row"
            ]
        )


        period_df = (
            profile[
                "df"
            ]
        )


        peers = period_df.loc[

            (
                period_df[
                    "position"
                ]
                .astype(str)

                ==

                profile[
                    "position"
                ]
            )

            &

            (
                period_df[
                    "minutes_played"
                ]

                >=

                profile[
                    "threshold"
                ]
            )

        ].copy()


        values = []

        percentiles = []


        for metric_label in selected_radar:

            col = (
                RADAR[
                    metric_label
                ]
            )


            value = (
                row[
                    col
                ]
            )


            percentile = percentile_rank(

                value,

                peers[
                    col
                ],

                lower_is_better=(

                    col
                    in LOWER_IS_BETTER
                ),
            )


            values.append(
                value
            )


            percentiles.append(
                percentile
            )


        name = (

            f'{profile["player"]} · '
            f'{profile["period"]}'
        )


        raw_table[
            name
        ] = [

            fmt(
                value,
                2,
                False,
            )

            for value
            in values
        ]


        percentile_table[
            name
        ] = [

            (
                "—"

                if pd.isna(
                    value
                )

                else f"{value:.0f}"
            )

            for value
            in percentiles
        ]


        fig_radar.add_trace(

            go.Scatterpolar(

                r=percentiles,

                theta=selected_radar,

                fill="toself",

                name=name,

                customdata=values,

                hovertemplate=(

                    "<b>%{theta}</b>"

                    "<br>Percentile: "
                    "%{r:.0f}"

                    "<br>Actual: "
                    "%{customdata:.2f}"

                    "<extra>"
                    "%{fullData.name}"
                    "</extra>"
                ),
            )
        )


    fig_radar.update_layout(

        title=dict(

            text=(

                "Position-relative percentile radar"
                f" · {radar_mode}"
            ),

            x=0.5,
        ),

        polar=dict(

            radialaxis=dict(

                visible=True,

                range=[
                    0,
                    100,
                ],

                tickvals=[
                    20,
                    40,
                    60,
                    80,
                    100,
                ],
            )
        ),

        height=760,

        showlegend=True,
    )


    st.plotly_chart(

        fig_radar,

        width="stretch",
    )


    raw_tab, percentile_tab = st.tabs(

        [
            "Raw values used",
            "Percentiles drawn",
        ]
    )


    with raw_tab:

        st.dataframe(

            pd.DataFrame(
                raw_table
            ),

            hide_index=True,

            width="stretch",
        )


    with percentile_tab:

        st.dataframe(

            pd.DataFrame(
                percentile_table
            ),

            hide_index=True,

            width="stretch",
        )


# =========================================================
# EXPLANATION
# =========================================================

st.divider()


with st.expander(
    "How grouped seasons work"
):

    st.markdown(
        """
- Select **one season** for a normal single-season profile.
- Select **two or more seasons** for a combined multi-season profile.
- Raw totals are **summed first** and the rates are then recalculated.
- Seasonal per-90 figures are **not averaged**.
- The radar peer population uses the **same group of seasons** as the selected player.
- A player's comparison position is the position in which he played the most minutes over the selected period.
- The app tells you how many of the selected seasons the player actually appeared in.
- If one season in the group lacks xG, xA or box-touch data, that metric is hidden rather than calculated from an incomplete period.
"""
    )