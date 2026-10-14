from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app_helpers import install_player_search

install_player_search()


# =========================================================
# PAGE
# =========================================================

st.title("🌍 Europe — Big Five Player Lab")

st.write(
    "Compare players across the Premier League, La Liga, Bundesliga, "
    "Serie A and Ligue 1 — using individual seasons or pooled multi-season periods."
)

st.info(
    "This European dataset comes from Understat and therefore focuses on "
    "attacking and expected-goals metrics. Your main Premier League page "
    "still contains the richer touches, per-touch and defensive data."
)


# =========================================================
# LOAD DATA
# =========================================================

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "understat_big5_2021_26.csv"
)


@st.cache_data
def load_data():

    df = pd.read_csv(DATA_FILE)

    numeric = [
        "player_id",
        "matches",
        "minutes",
        "goals",
        "assists",
        "xg",
        "xa",
        "np_goals",
        "np_xg",
        "shots",
        "chances_created",
        "xg_chain",
        "xg_buildup",
    ]

    for col in numeric:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    return df


DATA = load_data()


# =========================================================
# CONSTANTS
# =========================================================

LEAGUES = [
    "Premier League",
    "La Liga",
    "Bundesliga",
    "Serie A",
    "Ligue 1",
]


SEASONS = sorted(
    DATA["season"].dropna().unique(),
    key=lambda x: int(str(x)[:4]),
    reverse=True,
)


SUM_COLUMNS = [
    "matches",
    "minutes",
    "goals",
    "assists",
    "xg",
    "xa",
    "np_goals",
    "np_xg",
    "shots",
    "chances_created",
    "xg_chain",
    "xg_buildup",
]


ROLE_NAMES = {
    "F": "Forward",
    "M": "Midfielder",
    "D": "Defender",
    "GK": "Goalkeeper",
    "Unknown": "Unknown",
}


# =========================================================
# HELPERS
# =========================================================

def ordered_seasons(seasons):

    return sorted(
        seasons,
        key=lambda x: int(str(x)[:4]),
    )


def period_label(seasons):

    seasons = ordered_seasons(
        seasons
    )

    if len(seasons) == 1:

        return seasons[0]

    return " + ".join(
        seasons
    )


def primary_position(position):

    if pd.isna(position):

        return "Unknown"

    tokens = (
        str(position)
        .replace(",", " ")
        .split()
    )

    for token in tokens:

        if token in {
            "GK",
            "F",
            "M",
            "D",
        }:

            return token

    return "Unknown"


def rate(
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
            float("nan"),
        )
    )

    return (
        num
        / den
        * multiplier
    )


def add_metrics(df):

    df = df.copy()

    mins = df["minutes"]
    shots = df["shots"]

    df["goals_per_90"] = rate(
        df["goals"],
        mins,
        90,
    )

    df["assists_per_90"] = rate(
        df["assists"],
        mins,
        90,
    )

    df["goal_involvements"] = (
        df["goals"]
        + df["assists"]
    )

    df["gi_per_90"] = rate(
        df["goal_involvements"],
        mins,
        90,
    )

    df["xg_per_90"] = rate(
        df["xg"],
        mins,
        90,
    )

    df["xa_per_90"] = rate(
        df["xa"],
        mins,
        90,
    )

    df["xgi"] = (
        df["xg"]
        + df["xa"]
    )

    df["xgi_per_90"] = rate(
        df["xgi"],
        mins,
        90,
    )

    df["np_goals_per_90"] = rate(
        df["np_goals"],
        mins,
        90,
    )

    df["npxg_per_90"] = rate(
        df["np_xg"],
        mins,
        90,
    )

    df["shots_per_90"] = rate(
        df["shots"],
        mins,
        90,
    )

    df["chances_created_per_90"] = rate(
        df["chances_created"],
        mins,
        90,
    )

    df["xg_chain_per_90"] = rate(
        df["xg_chain"],
        mins,
        90,
    )

    df["xg_buildup_per_90"] = rate(
        df["xg_buildup"],
        mins,
        90,
    )

    df["goal_conversion_pct"] = rate(
        df["goals"],
        shots,
        100,
    )

    df["xg_per_shot"] = rate(
        df["xg"],
        shots,
    )

    df["goals_minus_xg"] = (
        df["goals"]
        - df["xg"]
    )

    df["goals_minus_xg_per_90"] = rate(
        df["goals_minus_xg"],
        mins,
        90,
    )

    df["np_goals_minus_npxg"] = (
        df["np_goals"]
        - df["np_xg"]
    )

    df["np_goals_minus_npxg_per_90"] = rate(
        df["np_goals_minus_npxg"],
        mins,
        90,
    )

    return df


def aggregate_players(
    leagues,
    seasons,
):

    subset = DATA.loc[
        DATA["competition"].isin(
            leagues
        )
        & DATA["season"].isin(
            seasons
        )
    ].copy()

    if subset.empty:

        return pd.DataFrame()


    keys = [
        "player_id",
        "player_name",
    ]


    totals = (
        subset
        .groupby(
            keys,
            as_index=False,
            dropna=False,
        )[SUM_COLUMNS]
        .sum(
            min_count=1
        )
    )


    teams = (
        subset
        .groupby(
            keys,
            as_index=False,
            dropna=False,
        )["team_name"]
        .agg(
            lambda values:
            " / ".join(
                sorted(
                    set(
                        values
                        .dropna()
                        .astype(str)
                    )
                )
            )
        )
    )


    main_position = (
        subset
        .sort_values(
            "minutes",
            ascending=False,
        )
        .drop_duplicates(
            keys
        )[
            keys
            + ["position"]
        ]
    )


    season_count = (
        subset
        .loc[
            subset["minutes"]
            .fillna(0)
            > 0
        ]
        .groupby(
            keys,
            as_index=False,
            dropna=False,
        )["season"]
        .nunique()
        .rename(
            columns={
                "season":
                    "seasons_represented"
            }
        )
    )


    result = (
        totals
        .merge(
            teams,
            on=keys,
            how="left",
        )
        .merge(
            main_position,
            on=keys,
            how="left",
        )
        .merge(
            season_count,
            on=keys,
            how="left",
        )
    )


    result[
        "seasons_represented"
    ] = (
        result[
            "seasons_represented"
        ]
        .fillna(0)
    )


    result["role"] = (
        result["position"]
        .apply(
            primary_position
        )
    )


    return add_metrics(
        result
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
):

    if pd.isna(value):

        return float("nan")

    peer_values = (
        pd.to_numeric(
            peers,
            errors="coerce",
        )
        .dropna()
    )

    if peer_values.empty:

        return float("nan")

    value = float(
        value
    )

    below = (
        peer_values
        < value
    ).sum()

    equal = (
        peer_values
        == value
    ).sum()

    return (
        (
            below
            + 0.5
            * equal
        )
        / len(peer_values)
        * 100
    )


def profile_name(profile):

    return (
        f'{profile["player"]} · '
        f'{profile["league"]} · '
        f'{profile["period"]}'
    )


# =========================================================
# PLAYER SELECTION
# =========================================================

st.header(
    "Compare players"
)


compare_count = st.radio(
    "Number of profiles",
    [
        2,
        3,
    ],
    horizontal=True,
)


default_leagues = [
    "Premier League",
    "Bundesliga",
    "La Liga",
]


default_players = [
    [
        "Erling Haaland",
        "Haaland",
    ],
    [
        "Harry Kane",
        "Kane",
    ],
    [
        "Kylian Mbappé",
        "Mbappé",
    ],
]


columns = st.columns(
    compare_count
)


profiles = []


for i in range(
    compare_count
):

    with columns[i]:

        league = st.selectbox(
            f"League {i + 1}",
            LEAGUES,
            index=LEAGUES.index(
                default_leagues[i]
            ),
            key=f"europe_league_{i}",
        )


        seasons = st.multiselect(
            f"Season(s) {i + 1}",
            SEASONS,
            default=[
                "2025/26"
            ],
            key=f"europe_seasons_{i}",
        )


        if not seasons:

            st.warning(
                "Choose at least one season."
            )

            st.stop()


        period_df = aggregate_players(
            [
                league
            ],
            seasons,
        )


        player_options = sorted(
            period_df[
                "player_name"
            ]
            .dropna()
            .astype(str)
            .unique()
        )


        default_index = 0

        for preferred in (
            default_players[i]
        ):

            if preferred in player_options:

                default_index = (
                    player_options.index(
                        preferred
                    )
                )

                break


        player = st.selectbox(
            f"Player {i + 1}",
            player_options,
            index=default_index,
            key=(
                f"europe_player_{i}_"
                f"{league}_"
                f"{'-'.join(seasons)}"
            ),
        )


        row = period_df.loc[
            period_df[
                "player_name"
            ]
            == player
        ].iloc[0]


        profiles.append(
            {
                "league":
                    league,

                "seasons":
                    seasons,

                "period":
                    period_label(
                        seasons
                    ),

                "player":
                    player,

                "row":
                    row,

                "role":
                    row[
                        "role"
                    ],

                "period_df":
                    period_df,
            }
        )


        st.caption(
            f'{ROLE_NAMES.get(row["role"], row["role"])} · '
            f'{int(row["seasons_represented"])} of '
            f'{len(seasons)} selected seasons · '
            f'{fmt(row["minutes"], integer=True)} minutes'
        )


# =========================================================
# PEER GROUP OPTIONS
# =========================================================

st.header(
    "Comparison population"
)


peer_col1, peer_col2 = st.columns(
    2
)


with peer_col1:

    peer_scope = st.radio(
        "Radar / percentile peers",
        [
            "Same league",
            "All Big Five",
        ],
        horizontal=True,
    )


with peer_col2:

    require_all_seasons = st.checkbox(
        "Require peers to appear in every selected season",
        value=True,
    )


minimum_pct = st.slider(
    "Minimum minutes (% of maximum minutes in each peer period)",
    0,
    100,
    25,
    5,
)


def get_peer_pool(profile):

    if (
        peer_scope
        == "Same league"
    ):

        leagues = [
            profile[
                "league"
            ]
        ]

    else:

        leagues = LEAGUES


    peers = aggregate_players(
        leagues,
        profile[
            "seasons"
        ],
    )


    peers = peers.loc[
        peers["role"]
        == profile["role"]
    ].copy()


    if require_all_seasons:

        peers = peers.loc[
            peers[
                "seasons_represented"
            ]
            >= len(
                profile[
                    "seasons"
                ]
            )
        ].copy()


    if not peers.empty:

        max_minutes = (
            peers[
                "minutes"
            ]
            .max()
        )

        threshold = (
            max_minutes
            * minimum_pct
            / 100
        )

        peers = peers.loc[
            peers[
                "minutes"
            ]
            >= threshold
        ].copy()


    return peers


# =========================================================
# COMPARISON TABLES
# =========================================================

st.header(
    "Comparison"
)


TOTAL_METRICS = [
    (
        "Seasons represented",
        "seasons_represented",
        0,
        True,
    ),
    (
        "Matches",
        "matches",
        0,
        True,
    ),
    (
        "Minutes",
        "minutes",
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
        "Non-penalty goals",
        "np_goals",
        0,
        True,
    ),
    (
        "Non-penalty xG",
        "np_xg",
        2,
        False,
    ),
    (
        "Shots",
        "shots",
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
        "xGChain",
        "xg_chain",
        2,
        False,
    ),
    (
        "xGBuildup",
        "xg_buildup",
        2,
        False,
    ),
]


PER90_METRICS = [
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
        "gi_per_90",
        2,
        False,
    ),
    (
        "xG / 90",
        "xg_per_90",
        2,
        False,
    ),
    (
        "xA / 90",
        "xa_per_90",
        2,
        False,
    ),
    (
        "xG+xA / 90",
        "xgi_per_90",
        2,
        False,
    ),
    (
        "Non-penalty goals / 90",
        "np_goals_per_90",
        2,
        False,
    ),
    (
        "Non-penalty xG / 90",
        "npxg_per_90",
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
        "Chances created / 90",
        "chances_created_per_90",
        2,
        False,
    ),
    (
        "xGChain / 90",
        "xg_chain_per_90",
        2,
        False,
    ),
    (
        "xGBuildup / 90",
        "xg_buildup_per_90",
        2,
        False,
    ),
]


EFFICIENCY_METRICS = [
    (
        "Goal conversion %",
        "goal_conversion_pct",
        1,
        False,
    ),
    (
        "xG / shot",
        "xg_per_shot",
        3,
        False,
    ),
    (
        "Goals − xG",
        "goals_minus_xg",
        2,
        False,
    ),
    (
        "Goals − xG / 90",
        "goals_minus_xg_per_90",
        2,
        False,
    ),
    (
        "NP goals − NPxG",
        "np_goals_minus_npxg",
        2,
        False,
    ),
    (
        "NP goals − NPxG / 90",
        "np_goals_minus_npxg_per_90",
        2,
        False,
    ),
]


def comparison_table(
    metrics
):

    result = []

    for (
        label,
        column,
        decimals,
        integer,
    ) in metrics:

        item = {
            "Metric":
                label
        }

        for profile in profiles:

            item[
                profile_name(
                    profile
                )
            ] = fmt(
                profile[
                    "row"
                ][
                    column
                ],
                decimals,
                integer,
            )

        result.append(
            item
        )

    return pd.DataFrame(
        result
    )


tab1, tab2, tab3 = st.tabs(
    [
        "Totals",
        "Per 90",
        "Efficiency",
    ]
)


with tab1:

    st.dataframe(
        comparison_table(
            TOTAL_METRICS
        ),
        hide_index=True,
        width="stretch",
    )


with tab2:

    st.dataframe(
        comparison_table(
            PER90_METRICS
        ),
        hide_index=True,
        width="stretch",
    )


with tab3:

    st.dataframe(
        comparison_table(
            EFFICIENCY_METRICS
        ),
        hide_index=True,
        width="stretch",
    )


# =========================================================
# SCATTER
# =========================================================

st.header(
    "European player landscape"
)


SCATTER_METRICS = {
    "Goals / 90":
        "goals_per_90",

    "Assists / 90":
        "assists_per_90",

    "G+A / 90":
        "gi_per_90",

    "xG / 90":
        "xg_per_90",

    "xA / 90":
        "xa_per_90",

    "xG+xA / 90":
        "xgi_per_90",

    "Non-penalty xG / 90":
        "npxg_per_90",

    "Shots / 90":
        "shots_per_90",

    "Chances created / 90":
        "chances_created_per_90",

    "xGChain / 90":
        "xg_chain_per_90",

    "xGBuildup / 90":
        "xg_buildup_per_90",

    "Goal conversion %":
        "goal_conversion_pct",

    "xG / shot":
        "xg_per_shot",

    "Goals − xG / 90":
        "goals_minus_xg_per_90",
}


scatter_cols = st.columns(
    3
)


labels = list(
    SCATTER_METRICS
)


with scatter_cols[0]:

    x_label = st.selectbox(
        "X-axis",
        labels,
        index=labels.index(
            "xG / 90"
        ),
    )


with scatter_cols[1]:

    y_label = st.selectbox(
        "Y-axis",
        labels,
        index=labels.index(
            "Goals / 90"
        ),
    )


with scatter_cols[2]:

    role_filter = st.selectbox(
        "Position",
        [
            "All",
            "Forward",
            "Midfielder",
            "Defender",
            "Goalkeeper",
        ],
        index=1,
    )


x_col = (
    SCATTER_METRICS[
        x_label
    ]
)

y_col = (
    SCATTER_METRICS[
        y_label
    ]
)


landscape_parts = []


seen_contexts = set()


for profile in profiles:

    context = (
        tuple(
            sorted(
                LEAGUES
                if peer_scope
                == "All Big Five"
                else [
                    profile[
                        "league"
                    ]
                ]
            )
        ),
        tuple(
            ordered_seasons(
                profile[
                    "seasons"
                ]
            )
        ),
    )


    if context in seen_contexts:

        continue


    seen_contexts.add(
        context
    )


    leagues = list(
        context[0]
    )

    seasons = list(
        context[1]
    )


    frame = aggregate_players(
        leagues,
        seasons,
    )


    if require_all_seasons:

        frame = frame.loc[
            frame[
                "seasons_represented"
            ]
            >= len(
                seasons
            )
        ].copy()


    if not frame.empty:

        max_minutes = (
            frame[
                "minutes"
            ]
            .max()
        )

        frame = frame.loc[
            frame[
                "minutes"
            ]
            >= (
                max_minutes
                * minimum_pct
                / 100
            )
        ].copy()


    frame[
        "context"
    ] = (
        (
            "Big Five"
            if len(leagues) == 5
            else leagues[0]
        )
        + " · "
        + period_label(
            seasons
        )
    )


    landscape_parts.append(
        frame
    )


if landscape_parts:

    landscape = pd.concat(
        landscape_parts,
        ignore_index=True,
    )


    if role_filter != "All":

        role_code = {
            "Forward": "F",
            "Midfielder": "M",
            "Defender": "D",
            "Goalkeeper": "GK",
        }[
            role_filter
        ]

        landscape = (
            landscape.loc[
                landscape[
                    "role"
                ]
                == role_code
            ]
            .copy()
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
        color="context",
        size="minutes",
        size_max=18,
        hover_name="player_name",
        hover_data=[
            "team_name",
            "minutes",
            "goals",
            "assists",
            "xg",
            "xa",
        ],
        labels={
            x_col:
                x_label,

            y_col:
                y_label,

            "context":
                "Population",
        },
    )


    for profile in profiles:

        row = profile[
            "row"
        ]

        if (
            role_filter
            != "All"
            and ROLE_NAMES.get(
                profile[
                    "role"
                ]
            )
            != role_filter
        ):

            continue


        if (
            pd.isna(
                row[
                    x_col
                ]
            )
            or pd.isna(
                row[
                    y_col
                ]
            )
        ):

            continue


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
                    profile[
                        "player"
                    ]
                ],
                textposition="top center",
                marker=dict(
                    size=20,
                    symbol="diamond",
                    line=dict(
                        width=2
                    ),
                ),
                name=profile_name(
                    profile
                ),
            )
        )


    st.plotly_chart(
        fig_scatter,
        width="stretch",
    )


# =========================================================
# RADAR
# =========================================================

st.header(
    "European player profile radar"
)


st.caption(
    "The radar shows percentile rank, not raw values. "
    "Each player is ranked against positional peers from his selected "
    "period using the comparison population chosen above."
)


RADAR_METRICS = {
    "Goals / 90":
        "goals_per_90",

    "Assists / 90":
        "assists_per_90",

    "xG / 90":
        "xg_per_90",

    "xA / 90":
        "xa_per_90",

    "Non-penalty xG / 90":
        "npxg_per_90",

    "Shots / 90":
        "shots_per_90",

    "Chances created / 90":
        "chances_created_per_90",

    "xGChain / 90":
        "xg_chain_per_90",

    "xGBuildup / 90":
        "xg_buildup_per_90",

    "Goal conversion %":
        "goal_conversion_pct",

    "xG / shot":
        "xg_per_shot",

    "Goals − xG / 90":
        "goals_minus_xg_per_90",
}


default_radar = [
    "Goals / 90",
    "xG / 90",
    "Assists / 90",
    "xA / 90",
    "Shots / 90",
    "Chances created / 90",
]


selected_radar = st.multiselect(
    "Choose radar metrics",
    list(
        RADAR_METRICS
    ),
    default=default_radar,
    max_selections=10,
)


if len(
    selected_radar
) < 3:

    st.warning(
        "Choose at least three radar metrics."
    )


else:

    fig_radar = go.Figure()

    raw_values_table = {
        "Metric":
            selected_radar
    }

    percentile_table = {
        "Metric":
            selected_radar
    }


    for profile in profiles:

        peers = get_peer_pool(
            profile
        )

        row = profile[
            "row"
        ]

        actual_values = []

        percentile_values = []


        for label in selected_radar:

            column = (
                RADAR_METRICS[
                    label
                ]
            )

            value = row[
                column
            ]

            percentile = percentile_rank(
                value,
                peers[
                    column
                ],
            )


            actual_values.append(
                value
            )

            percentile_values.append(
                percentile
            )


        name = profile_name(
            profile
        )


        raw_values_table[
            name
        ] = [
            fmt(
                value,
                2,
                False,
            )
            for value
            in actual_values
        ]


        percentile_table[
            name
        ] = [
            (
                "—"
                if pd.isna(value)
                else f"{value:.0f}"
            )
            for value
            in percentile_values
        ]


        fig_radar.add_trace(
            go.Scatterpolar(
                r=percentile_values,
                theta=selected_radar,
                fill="toself",
                name=name,
                customdata=actual_values,
                hovertemplate=(
                    "<b>%{theta}</b>"
                    "<br>Percentile: %{r:.0f}"
                    "<br>Actual: %{customdata:.2f}"
                    "<extra>%{fullData.name}</extra>"
                ),
            )
        )


    fig_radar.update_layout(
        title=dict(
            text=(
                "Position-relative percentile radar"
                f" · {peer_scope}"
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
            "Raw values",
            "Radar percentiles",
        ]
    )


    with raw_tab:

        st.dataframe(
            pd.DataFrame(
                raw_values_table
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
# NOTES
# =========================================================

st.divider()


with st.expander(
    "How European multi-season comparisons work"
):

    st.markdown(
        """
- Select one season for a normal single-season comparison.
- Select several seasons to pool them into one larger sample.
- Raw totals are **added first**, then per-90 and efficiency statistics are recalculated.
- Seasonal per-90 figures are **not simply averaged**.
- You can compare different players, leagues and periods simultaneously.
- **Same league** percentiles compare each player with positional peers from his own competition.
- **All Big Five** percentiles compare him with positional peers across England, Spain, Germany, Italy and France.
- The **require every selected season** option prevents a three-season peer group being filled with players who only appeared during one of those seasons.
- Understat does not provide the touch and defensive data used by the richer Premier League page, so this Europe page deliberately does not invent those metrics.
"""
    )
