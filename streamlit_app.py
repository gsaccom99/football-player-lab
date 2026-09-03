import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="Football Player Lab",
    layout="wide"
)

st.title("⚽ Football Player Lab")

st.write(
    "Compare Premier League player-seasons using totals, per-90, "
    "per-touch and efficiency metrics."
)


# =========================================================
# SEASON FILES
# =========================================================

SEASON_FILES = {
    "2026/27": "premier_league_2026_27.csv",
    "2025/26": "premier_league_2025_26.csv",
    "2024/25": "premier_league_2024_25.csv",
    "2023/24": "premier_league_2023_24.csv",
    "2022/23": "premier_league_2022_23.csv",
    "2021/22": "premier_league_2021_22.csv",
}


NUMERIC_COLUMNS = [
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


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def rate(numerator, denominator, multiplier=1):

    num = pd.to_numeric(
        numerator,
        errors="coerce"
    ).astype(float)

    den = pd.to_numeric(
        denominator,
        errors="coerce"
    ).astype(float)

    den = den.replace(
        0,
        float("nan")
    )

    return (
        num
        / den
        * multiplier
    )


@st.cache_data
def load_season(season):

    df = pd.read_csv(
        SEASON_FILES[season]
    ).copy()

    for col in NUMERIC_COLUMNS:

        if col not in df.columns:
            df[col] = pd.NA

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df["season"] = season

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
            90
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
            100
        )


    # =====================================================
    # EFFICIENCY
    # =====================================================

    df["shot_accuracy_pct"] = rate(
        df["shots_on_target"],
        shots,
        100
    )

    df["goal_conversion_pct"] = rate(
        df["goals"],
        shots,
        100
    )

    df["xG_per_shot"] = rate(
        df["xg"],
        shots
    )

    df["tackle_success_pct"] = rate(
        df["tackles_won"],
        df["tackles"],
        100
    )

    df["duel_win_pct"] = rate(
        df["duels_won"],
        (
            df["duels_won"]
            + df["duels_lost"]
        ),
        100
    )

    df["goals_minus_xG"] = (
        df["goals"]
        - df["xg"]
    )

    df["goals_minus_xG_per_90"] = rate(
        df["goals_minus_xG"],
        mins,
        90
    )

    df["goals_minus_xG_per_100_touches"] = rate(
        df["goals_minus_xG"],
        touches,
        100
    )

    return df


# =========================================================
# LOAD ALL SIX SEASONS
# =========================================================

DATA = {
    season: load_season(season)
    for season in SEASON_FILES
}


def has_data(frame, column):

    return (
        column in frame.columns
        and
        frame[column].notna().any()
    )


def players_for(season):

    return sorted(
        DATA[season]["web_name"]
        .dropna()
        .astype(str)
        .unique()
    )


def preferred_index(
    options,
    preferred_names
):

    for name in preferred_names:

        if name in options:
            return options.index(name)

    return 0


def player_row(
    season,
    player
):

    return DATA[season][
        DATA[season]["web_name"]
        .astype(str)
        == player
    ].iloc[0]


def profile_label(profile):

    return (
        f'{profile["player"]} · '
        f'{profile["season"]}'
    )


def season_max_minutes(season):

    value = pd.to_numeric(
        DATA[season]["minutes_played"],
        errors="coerce"
    ).max()

    if pd.isna(value):
        return 0.0

    return float(value)


def peer_min_minutes(
    season,
    percentage
):

    return (
        season_max_minutes(season)
        * percentage
        / 100
    )


# =========================================================
# PLAYER-SEASON SELECTION
# =========================================================

st.header(
    "Compare player-seasons"
)

st.caption(
    "Each slot has its own season. Choose different players "
    "across different seasons, or choose the same player in "
    "several seasons to compare different versions of him."
)


compare_count = st.radio(
    "Number of profiles",
    [2, 3],
    horizontal=True
)


slot_columns = st.columns(
    compare_count
)


default_seasons = [
    "2025/26",
    "2025/26",
    "2024/25"
]


default_players = [

    [
        "Haaland",
        "Erling Haaland"
    ],

    [
        "Gyökeres",
        "Viktor Gyökeres"
    ],

    [
        "Salah",
        "Mohamed Salah"
    ]
]


profiles = []


for i in range(compare_count):

    with slot_columns[i]:

        season_options = list(
            SEASON_FILES.keys()
        )

        season_default = (
            default_seasons[i]
        )

        season_index = (

            season_options.index(
                season_default
            )

            if season_default
            in season_options

            else 0
        )


        season = st.selectbox(

            f"Season {i + 1}",

            season_options,

            index=season_index,

            key=f"profile_season_{i}"
        )


        options = players_for(
            season
        )


        p_index = preferred_index(
            options,
            default_players[i]
        )


        player = st.selectbox(

            f"Player {i + 1}",

            options,

            index=p_index,

            key=(
                f"profile_player_"
                f"{i}_{season}"
            )
        )


        row = player_row(
            season,
            player
        )


        profiles.append(
            {
                "season":
                    season,

                "player":
                    player,

                "row":
                    row,

                "position":
                    str(
                        row["position"]
                    )
            }
        )


# =========================================================
# SAMPLE SIZE
# =========================================================

sample_pct = st.slider(

    "Minimum sample for peer groups "
    "(% of season maximum minutes)",

    min_value=0,

    max_value=100,

    value=25,

    step=5
)


selected_seasons = list(
    dict.fromkeys(
        p["season"]
        for p in profiles
    )
)


threshold_text = []


for season in selected_seasons:

    threshold_text.append(
        (
            f"{season}: "
            f"{peer_min_minutes(season, sample_pct):.0f}+ min"
        )
    )


st.caption(
    "Peer-group thresholds — "
    + " · ".join(
        threshold_text
    )
)


# =========================================================
# DATA AVAILABILITY NOTES
# =========================================================

notes = []


if "2021/22" in selected_seasons:

    notes.append(
        "2021/22 has no xG, xA or opposition-box-touch "
        "data in our source."
    )


if any(
    season in {
        "2022/23",
        "2023/24",
        "2024/25"
    }
    for season in selected_seasons
):

    notes.append(
        "Opposition-box touches are unavailable in our "
        "historical source for 2022/23–2024/25."
    )


if notes:

    st.info(
        " ".join(notes)
    )


# =========================================================
# TABLE HELPERS
# =========================================================

def fmt(
    value,
    decimals=2,
    integer=False
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


def make_table(specs):

    rows = []


    for (
        label,
        column,
        decimals,
        integer
    ) in specs:

        values = []


        for profile in profiles:

            row = profile["row"]

            value = (
                row[column]

                if column
                in row.index

                else pd.NA
            )

            values.append(
                value
            )


        if all(
            pd.isna(v)
            for v in values
        ):

            continue


        result = {
            "Metric": label
        }


        for (
            profile,
            value
        ) in zip(
            profiles,
            values
        ):

            result[
                profile_label(
                    profile
                )
            ] = fmt(
                value,
                decimals=decimals,
                integer=integer
            )


        rows.append(
            result
        )


    return pd.DataFrame(
        rows
    )


# =========================================================
# TABLE METRICS
# =========================================================

OVERVIEW = [

    (
        "Minutes",
        "minutes_played",
        0,
        True
    ),

    (
        "Goals",
        "goals",
        0,
        True
    ),

    (
        "Assists",
        "assists",
        0,
        True
    ),

    (
        "Goal involvements",
        "goal_involvements",
        0,
        True
    ),

    (
        "xG",
        "xg",
        2,
        False
    ),

    (
        "xA",
        "xa",
        2,
        False
    ),

    (
        "Goals − xG",
        "goals_minus_xG",
        2,
        False
    ),

    (
        "Shots",
        "total_shots",
        0,
        True
    ),

    (
        "Shots on target",
        "shots_on_target",
        0,
        True
    ),

    (
        "Shot accuracy %",
        "shot_accuracy_pct",
        1,
        False
    ),

    (
        "Goal conversion %",
        "goal_conversion_pct",
        1,
        False
    ),

    (
        "xG / shot",
        "xG_per_shot",
        2,
        False
    ),

    (
        "Chances created",
        "chances_created",
        0,
        True
    ),

    (
        "Successful dribbles",
        "successful_dribbles",
        0,
        True
    ),

    (
        "Touches",
        "touches",
        0,
        True
    ),

    (
        "Touches in opposition box",
        "touches_opposition_box",
        0,
        True
    ),

    (
        "Dispossessed",
        "dispossessed",
        0,
        True
    ),

    (
        "Tackles",
        "tackles",
        0,
        True
    ),

    (
        "Tackles won",
        "tackles_won",
        0,
        True
    ),

    (
        "Tackle success %",
        "tackle_success_pct",
        1,
        False
    ),

    (
        "Interceptions",
        "interceptions",
        0,
        True
    ),

    (
        "Recoveries",
        "recoveries",
        0,
        True
    ),

    (
        "Blocks",
        "blocks",
        0,
        True
    ),

    (
        "Clearances",
        "clearances",
        0,
        True
    ),

    (
        "Duels won",
        "duels_won",
        0,
        True
    ),

    (
        "Duel win %",
        "duel_win_pct",
        1,
        False
    )
]


PER90_TABLE = [

    (
        "Goals / 90",
        "goals_per_90",
        2,
        False
    ),

    (
        "Assists / 90",
        "assists_per_90",
        2,
        False
    ),

    (
        "G+A / 90",
        "GI_per_90",
        2,
        False
    ),

    (
        "xG / 90",
        "xG_per_90",
        2,
        False
    ),

    (
        "xA / 90",
        "xA_per_90",
        2,
        False
    ),

    (
        "xG+xA / 90",
        "xGI_per_90",
        2,
        False
    ),

    (
        "Goals − xG / 90",
        "goals_minus_xG_per_90",
        2,
        False
    ),

    (
        "Shots / 90",
        "shots_per_90",
        2,
        False
    ),

    (
        "Shots on target / 90",
        "shots_on_target_per_90",
        2,
        False
    ),

    (
        "Chances created / 90",
        "chances_created_per_90",
        2,
        False
    ),

    (
        "Dribbles / 90",
        "dribbles_per_90",
        2,
        False
    ),

    (
        "Touches / 90",
        "touches_per_90",
        2,
        False
    ),

    (
        "Box touches / 90",
        "box_touches_per_90",
        2,
        False
    ),

    (
        "Dispossessed / 90",
        "dispossessed_per_90",
        2,
        False
    ),

    (
        "Tackles / 90",
        "tackles_per_90",
        2,
        False
    ),

    (
        "Tackles won / 90",
        "tackles_won_per_90",
        2,
        False
    ),

    (
        "Interceptions / 90",
        "interceptions_per_90",
        2,
        False
    ),

    (
        "Recoveries / 90",
        "recoveries_per_90",
        2,
        False
    ),

    (
        "Blocks / 90",
        "blocks_per_90",
        2,
        False
    ),

    (
        "Clearances / 90",
        "clearances_per_90",
        2,
        False
    ),

    (
        "Duels won / 90",
        "duels_won_per_90",
        2,
        False
    )
]


PER_TOUCH_TABLE = [

    (
        "Goals / 100 touches",
        "goals_per_100_touches",
        2,
        False
    ),

    (
        "Assists / 100 touches",
        "assists_per_100_touches",
        2,
        False
    ),

    (
        "G+A / 100 touches",
        "GI_per_100_touches",
        2,
        False
    ),

    (
        "xG / 100 touches",
        "xG_per_100_touches",
        2,
        False
    ),

    (
        "xA / 100 touches",
        "xA_per_100_touches",
        2,
        False
    ),

    (
        "xG+xA / 100 touches",
        "xGI_per_100_touches",
        2,
        False
    ),

    (
        "Goals − xG / 100 touches",
        "goals_minus_xG_per_100_touches",
        2,
        False
    ),

    (
        "Shots / 100 touches",
        "shots_per_100_touches",
        2,
        False
    ),

    (
        "Shots on target / 100 touches",
        "shots_on_target_per_100_touches",
        2,
        False
    ),

    (
        "Chances created / 100 touches",
        "chances_created_per_100_touches",
        2,
        False
    ),

    (
        "Dribbles / 100 touches",
        "dribbles_per_100_touches",
        2,
        False
    ),

    (
        "Box touches / 100 touches",
        "box_touches_per_100_touches",
        2,
        False
    ),

    (
        "Dispossessed / 100 touches",
        "dispossessed_per_100_touches",
        2,
        False
    )
]


# =========================================================
# COMPARISON TABLES
# =========================================================

st.header(
    "Comparison"
)


tab_overview, tab_per90, tab_touch = st.tabs(
    [
        "Overview",
        "Per 90",
        "Per 100 touches"
    ]
)


with tab_overview:

    st.dataframe(
        make_table(
            OVERVIEW
        ),
        hide_index=True,
        width="stretch"
    )


with tab_per90:

    st.dataframe(
        make_table(
            PER90_TABLE
        ),
        hide_index=True,
        width="stretch"
    )


with tab_touch:

    st.dataframe(
        make_table(
            PER_TOUCH_TABLE
        ),
        hide_index=True,
        width="stretch"
    )


# =========================================================
# MASTER METRIC CATALOGUE
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
        "duel_win_pct"
}


def metric_common_to_selected_seasons(
    column
):

    return all(
        has_data(
            DATA[season],
            column
        )
        for season
        in selected_seasons
    )


COMMON_METRICS = {

    label: column

    for (
        label,
        column
    ) in METRICS.items()

    if metric_common_to_selected_seasons(
        column
    )
}


# =========================================================
# CROSS-SEASON SCATTER
# =========================================================

st.header(
    "Cross-season player landscape"
)


st.caption(
    "The background includes qualified players from every "
    "season selected above. Selected player-seasons are highlighted. "
    "Metrics unavailable in any selected season are hidden."
)


metric_labels = list(
    COMMON_METRICS
)


if not metric_labels:

    st.warning(
        "No common metrics are available for the selected seasons."
    )


else:

    preferred_x = (
        "Touches / 90"
    )

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


    x_default = (

        metric_labels.index(
            preferred_x
        )

        if preferred_x
        in metric_labels

        else 0
    )


    y_default = (

        metric_labels.index(
            preferred_y
        )

        if preferred_y
        in metric_labels

        else min(
            1,
            len(metric_labels) - 1
        )
    )


    sc1, sc2, sc3 = st.columns(
        3
    )


    with sc1:

        x_label = st.selectbox(

            "X-axis",

            metric_labels,

            index=x_default,

            key="cross_x"
        )


    with sc2:

        y_label = st.selectbox(

            "Y-axis",

            metric_labels,

            index=y_default,

            key="cross_y"
        )


    positions = sorted(
        {
            str(pos)

            for season
            in selected_seasons

            for pos
            in DATA[season][
                "position"
            ]
            .dropna()
            .unique()
        }
    )


    default_position = (
        profiles[0]["position"]
    )


    position_options = [
        "All positions",
        *positions
    ]


    with sc3:

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

            key="cross_position"
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


    landscape_frames = []


    for season in selected_seasons:

        frame = DATA[
            season
        ].copy()


        frame = frame[
            frame[
                "minutes_played"
            ]
            >= peer_min_minutes(
                season,
                sample_pct
            )
        ].copy()


        if (
            position_filter
            != "All positions"
        ):

            frame = frame[
                frame[
                    "position"
                ]
                .astype(str)
                == position_filter
            ].copy()


        max_minutes = (
            season_max_minutes(
                season
            )
        )


        if max_minutes > 0:

            frame[
                "season_minutes_share"
            ] = (
                frame[
                    "minutes_played"
                ]
                / max_minutes
                * 100
            )

        else:

            frame[
                "season_minutes_share"
            ] = 0


        frame[
            "hover_name"
        ] = (
            frame[
                "web_name"
            ]
            .astype(str)
            + " · "
            + season
        )


        landscape_frames.append(
            frame
        )


    landscape = pd.concat(
        landscape_frames,
        ignore_index=True
    )


    landscape = landscape.dropna(
        subset=[
            x_col,
            y_col
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
            "assists"
        ],

        size="season_minutes_share",

        color="season",

        labels={
            x_col:
                x_label,

            y_col:
                y_label,

            "season":
                "Season",

            "season_minutes_share":
                "Season minutes %"
        }
    )


    # Highlight selected player-seasons

    for profile in profiles:

        if (
            position_filter
            != "All positions"

            and

            profile["position"]
            != position_filter
        ):

            continue


        row = profile["row"]

        xv = row[
            x_col
        ]

        yv = row[
            y_col
        ]


        if (
            pd.isna(xv)
            or
            pd.isna(yv)
        ):

            continue


        fig_scatter.add_trace(

            go.Scatter(

                x=[xv],

                y=[yv],

                mode="markers+text",

                text=[
                    profile_label(
                        profile
                    )
                ],

                textposition="top center",

                marker=dict(
                    size=18,
                    symbol="diamond"
                ),

                name=profile_label(
                    profile
                )
            )
        )


    st.plotly_chart(
        fig_scatter,
        width="stretch"
    )


# =========================================================
# CROSS-SEASON RADAR
# =========================================================

st.header(
    "Cross-season player profile radar"
)


st.caption(
    "Each player-season is ranked against players in its own "
    "season and its own position. Further out always means better."
)


radar_mode = st.radio(

    "Radar normalisation",

    [
        "Per 100 touches",
        "Per 90"
    ],

    horizontal=True
)


# =========================================================
# RADAR METRIC CATALOGUE
# =========================================================

if radar_mode == "Per 100 touches":

    RADAR_CANDIDATES = {

        "Goals":
            "goals_per_100_touches",

        "Assists":
            "assists_per_100_touches",

        "Goal involvements":
            "GI_per_100_touches",

        "xG":
            "xG_per_100_touches",

        "xA":
            "xA_per_100_touches",

        "xG+xA":
            "xGI_per_100_touches",

        "Shots":
            "shots_per_100_touches",

        "Shots on target":
            "shots_on_target_per_100_touches",

        "Chances created":
            "chances_created_per_100_touches",

        "Dribbles":
            "dribbles_per_100_touches",

        "Box touches":
            "box_touches_per_100_touches",

        "Ball security":
            "dispossessed_per_100_touches",

        "Touches / 90":
            "touches_per_90",

        "Shot accuracy %":
            "shot_accuracy_pct",

        "Goal conversion %":
            "goal_conversion_pct",

        "xG / shot":
            "xG_per_shot",

        "Goals − xG":
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
            "duel_win_pct"
    }


else:

    RADAR_CANDIDATES = {

        "Goals":
            "goals_per_90",

        "Assists":
            "assists_per_90",

        "Goal involvements":
            "GI_per_90",

        "xG":
            "xG_per_90",

        "xA":
            "xA_per_90",

        "xG+xA":
            "xGI_per_90",

        "Shots":
            "shots_per_90",

        "Shots on target":
            "shots_on_target_per_90",

        "Chances created":
            "chances_created_per_90",

        "Dribbles":
            "dribbles_per_90",

        "Box touches":
            "box_touches_per_90",

        "Ball security":
            "dispossessed_per_90",

        "Touches":
            "touches_per_90",

        "Shot accuracy %":
            "shot_accuracy_pct",

        "Goal conversion %":
            "goal_conversion_pct",

        "xG / shot":
            "xG_per_shot",

        "Goals − xG":
            "goals_minus_xG_per_90",

        "Tackles":
            "tackles_per_90",

        "Tackles won":
            "tackles_won_per_90",

        "Tackle success %":
            "tackle_success_pct",

        "Interceptions":
            "interceptions_per_90",

        "Recoveries":
            "recoveries_per_90",

        "Blocks":
            "blocks_per_90",

        "Clearances":
            "clearances_per_90",

        "Duels won":
            "duels_won_per_90",

        "Duel win %":
            "duel_win_pct"
    }


# Only offer radar metrics that exist
# in EVERY selected season.

RADAR = {

    label: column

    for (
        label,
        column
    ) in RADAR_CANDIDATES.items()

    if metric_common_to_selected_seasons(
        column
    )
}


# =========================================================
# LOWER = BETTER METRICS
# =========================================================

LOWER_IS_BETTER = {
    "Ball security"
}


# =========================================================
# DEFAULT RADAR METRICS
# =========================================================

preferred_radar = [

    "Goals",
    "xG",
    "Assists",
    "xA",
    "Shots",
    "Chances created",
    "Dribbles",
    "Box touches"
]


default_radar = [

    metric

    for metric
    in preferred_radar

    if metric in RADAR
]


for metric in RADAR:

    if len(
        default_radar
    ) >= 6:

        break

    if (
        metric
        not in default_radar
    ):

        default_radar.append(
            metric
        )


selected_radar = st.multiselect(

    "Choose radar metrics",

    list(
        RADAR
    ),

    default=default_radar,

    max_selections=12
)


if radar_mode == "Per 100 touches":

    st.caption(
        "Attacking/on-ball rates use per 100 touches. "
        "Defensive actions stay per 90 because a player's "
        "own touches are not a sensible defensive-opportunity denominator."
    )


# =========================================================
# BUILD RADAR
# =========================================================

if len(
    selected_radar
) < 3:

    st.warning(
        "Choose at least three radar metrics."
    )


else:

    fig_radar = go.Figure()


    for profile in profiles:

        season = (
            profile["season"]
        )

        row = (
            profile["row"]
        )

        position = (
            profile["position"]
        )


        frame = DATA[
            season
        ]


        threshold = (
            peer_min_minutes(
                season,
                sample_pct
            )
        )


        peers = frame[

            (
                frame[
                    "position"
                ]
                .astype(str)
                == position
            )

            &

            (
                frame[
                    "minutes_played"
                ]
                >= threshold
            )

        ].copy()


        percentiles = []

        actual_values = []


        for label in selected_radar:

            column = (
                RADAR[
                    label
                ]
            )


            value = row[
                column
            ]


            peer_values = pd.to_numeric(

                peers[
                    column
                ],

                errors="coerce"

            ).dropna()


            if (
                pd.isna(value)
                or
                peer_values.empty
            ):

                percentile = 0.0

                actual_value = (
                    float("nan")
                )


            else:

                value = float(
                    value
                )

                actual_value = (
                    value
                )


                equal = (
                    peer_values
                    == value
                ).sum()


                if (
                    label
                    in LOWER_IS_BETTER
                ):

                    better = (
                        peer_values
                        > value
                    ).sum()


                else:

                    better = (
                        peer_values
                        < value
                    ).sum()


                percentile = (

                    (
                        better
                        + 0.5
                        * equal
                    )

                    / len(
                        peer_values
                    )

                    * 100
                )


            percentiles.append(
                percentile
            )

            actual_values.append(
                actual_value
            )


        fig_radar.add_trace(

            go.Scatterpolar(

                r=percentiles,

                theta=selected_radar,

                fill="toself",

                name=profile_label(
                    profile
                ),

                customdata=actual_values,

                hovertemplate=(

                    "%{theta}"

                    "<br>Percentile: "
                    "%{r:.0f}"

                    "<br>Actual value: "
                    "%{customdata:.2f}"

                    "<extra>"
                    "%{fullData.name}"
                    "</extra>"
                )
            )
        )


    fig_radar.update_layout(

        polar=dict(

            radialaxis=dict(

                visible=True,

                range=[
                    0,
                    100
                ],

                tickvals=[
                    20,
                    40,
                    60,
                    80,
                    100
                ]
            )
        ),

        showlegend=True,

        height=720
    )


    st.plotly_chart(
        fig_radar,
        width="stretch"
    )


# =========================================================
# HOW TO USE
# =========================================================

st.divider()

st.subheader(
    "Cross-season and multi-season comparison"
)

st.write(
    "For a cross-player comparison, choose different players and "
    "different seasons in the profile slots. For a multi-season "
    "comparison of one player, choose that player in two or three "
    "slots and give each slot a different season. The comparison "
    "tables, scatter plot and radar all update together."
)