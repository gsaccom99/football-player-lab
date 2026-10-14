import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


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


def safe_rate(
    numerator,
    denominator,
    multiplier=1,
):
    den = pd.to_numeric(
        denominator,
        errors="coerce",
    ).replace(
        0,
        np.nan,
    )

    num = pd.to_numeric(
        numerator,
        errors="coerce",
    )

    return (
        num
        / den
        * multiplier
    )


def git_value(
    repo,
    args,
):
    try:
        return (
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(repo),
                    *args,
                ],
                text=True,
            )
            .strip()
        )

    except Exception:
        return None


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source-dir",
        required=True,
    )

    parser.add_argument(
        "--source-season",
        default="2026-2027",
    )

    parser.add_argument(
        "--season-label",
        default="2026/27",
    )

    parser.add_argument(
        "--output",
        default="premier_league_2026_27.csv",
    )

    parser.add_argument(
        "--metadata",
        default="data_freshness.json",
    )

    args = parser.parse_args()


    source_repo = Path(
        args.source_dir
    ).resolve()

    season_root = (
        source_repo
        / "data"
        / args.source_season
    )

    tournament_root = (
        season_root
        / "By Tournament"
        / "Premier League"
    )


    if not tournament_root.exists():

        raise FileNotFoundError(
            "Could not find Premier League tournament data at:\n"
            f"{tournament_root}"
        )


    gw_sources = []


    for folder in tournament_root.glob(
        "GW*"
    ):

        match = re.fullmatch(
            r"GW(\d+)",
            folder.name,
        )

        if not match:
            continue


        gw = int(
            match.group(1)
        )


        stats_file = (
            folder
            / "playermatchstats.csv"
        )


        if not stats_file.exists():
            continue


        frame = pd.read_csv(
            stats_file
        )


        if frame.empty:
            continue


        if (
            "minutes_played"
            not in frame.columns
        ):
            continue


        minutes_total = (
            pd.to_numeric(
                frame[
                    "minutes_played"
                ],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )


        if minutes_total <= 0:
            continue


        frame[
            "_source_gw"
        ] = gw


        gw_sources.append(
            (
                gw,
                folder,
                frame,
            )
        )


    if not gw_sources:

        raise RuntimeError(
            "No populated Premier League gameweek "
            "playermatchstats.csv files were found."
        )


    gw_sources.sort(
        key=lambda item: item[0]
    )


    latest_gw = max(
        gw
        for (
            gw,
            _,
            _,
        ) in gw_sources
    )


    print(
        "Populated Premier League gameweeks:",
        [
            gw
            for (
                gw,
                _,
                _,
            ) in gw_sources
        ],
    )

    print(
        "Latest populated gameweek:",
        latest_gw,
    )


    # ======================================================
    # PLAYER-MATCH DATA
    # ======================================================

    match_frames = [
        frame
        for (
            _,
            _,
            frame,
        ) in gw_sources
    ]


    matches = pd.concat(
        match_frames,
        ignore_index=True,
    )


    # A later snapshot wins if a player/match record occurs
    # more than once.
    if all(
        col in matches.columns
        for col in [
            "player_id",
            "match_id",
        ]
    ):

        matches = (
            matches
            .sort_values(
                "_source_gw"
            )
            .drop_duplicates(
                [
                    "player_id",
                    "match_id",
                ],
                keep="last",
            )
        )


    for col in RAW_COLUMNS:

        if col not in matches.columns:
            matches[col] = np.nan

        matches[col] = pd.to_numeric(
            matches[col],
            errors="coerce",
        )


    # ======================================================
    # PLAYER NAMES / POSITIONS
    # ======================================================

    player_files = []


    master_players = (
        season_root
        / "players.csv"
    )


    if master_players.exists():
        player_files.append(
            master_players
        )


    for (
        _,
        folder,
        _,
    ) in gw_sources:

        candidate = (
            folder
            / "players.csv"
        )

        if candidate.exists():
            player_files.append(
                candidate
            )


    if not player_files:

        raise FileNotFoundError(
            "No players.csv file was found."
        )


    player_frames = []


    for file in player_files:

        p = pd.read_csv(
            file
        )

        required = {
            "player_id",
            "web_name",
            "position",
        }

        if required.issubset(
            p.columns
        ):

            player_frames.append(
                p
            )


    players = pd.concat(
        player_frames,
        ignore_index=True,
    )


    players = (
        players
        .drop_duplicates(
            "player_id",
            keep="last",
        )
    )


    name_columns = [
        col
        for col in [
            "player_id",
            "player_code",
            "first_name",
            "second_name",
            "web_name",
            "team_code",
            "position",
        ]
        if col in players.columns
    ]


    # ======================================================
    # AGGREGATE PLAYER SEASON TOTALS
    # ======================================================

    totals = (
        matches
        .groupby(
            "player_id",
            as_index=False,
        )[RAW_COLUMNS]
        .sum(
            min_count=1
        )
    )


    result = totals.merge(
        players[
            name_columns
        ],
        on="player_id",
        how="left",
    )


    # Put identifying fields first.
    identifiers = [
        col
        for col in [
            "player_code",
            "player_id",
            "first_name",
            "second_name",
            "web_name",
            "team_code",
            "position",
        ]
        if col in result.columns
    ]


    result = result[
        identifiers
        + RAW_COLUMNS
    ]


    # ======================================================
    # COMPATIBILITY / DERIVED METRICS
    # ======================================================

    mins = result[
        "minutes_played"
    ]

    touches = result[
        "touches"
    ]


    result[
        "goals_per_90"
    ] = safe_rate(
        result["goals"],
        mins,
        90,
    )

    result[
        "assists_per_90"
    ] = safe_rate(
        result["assists"],
        mins,
        90,
    )

    result[
        "shots_per_90"
    ] = safe_rate(
        result["total_shots"],
        mins,
        90,
    )

    result[
        "chances_created_per_90"
    ] = safe_rate(
        result["chances_created"],
        mins,
        90,
    )

    result[
        "box_touches_per_90"
    ] = safe_rate(
        result["touches_opposition_box"],
        mins,
        90,
    )

    result[
        "dribbles_per_90"
    ] = safe_rate(
        result["successful_dribbles"],
        mins,
        90,
    )

    result[
        "touches_per_90"
    ] = safe_rate(
        result["touches"],
        mins,
        90,
    )

    result[
        "xG_per_90"
    ] = safe_rate(
        result["xg"],
        mins,
        90,
    )

    result[
        "xA_per_90"
    ] = safe_rate(
        result["xa"],
        mins,
        90,
    )


    result[
        "goals_per_100_touches"
    ] = safe_rate(
        result["goals"],
        touches,
        100,
    )

    result[
        "assists_per_100_touches"
    ] = safe_rate(
        result["assists"],
        touches,
        100,
    )

    result[
        "xG_per_100_touches"
    ] = safe_rate(
        result["xg"],
        touches,
        100,
    )

    result[
        "xA_per_100_touches"
    ] = safe_rate(
        result["xa"],
        touches,
        100,
    )

    result[
        "xGI_per_100_touches"
    ] = safe_rate(
        (
            result["xg"]
            + result["xa"]
        ),
        touches,
        100,
    )

    result[
        "shots_per_100_touches"
    ] = safe_rate(
        result["total_shots"],
        touches,
        100,
    )

    result[
        "chances_created_per_100_touches"
    ] = safe_rate(
        result["chances_created"],
        touches,
        100,
    )

    result[
        "box_touches_per_100_touches"
    ] = safe_rate(
        result["touches_opposition_box"],
        touches,
        100,
    )


    result = result.sort_values(
        "minutes_played",
        ascending=False,
    )


    result.to_csv(
        args.output,
        index=False,
    )


    # ======================================================
    # FRESHNESS RECORD
    # ======================================================

    source_commit = git_value(
        source_repo,
        [
            "rev-parse",
            "HEAD",
        ],
    )


    source_updated_at = git_value(
        source_repo,
        [
            "log",
            "-1",
            "--format=%cI",
        ],
    )


    unique_matches = (
        int(
            matches[
                "match_id"
            ].nunique()
        )
        if "match_id"
        in matches.columns
        else None
    )


    metadata = {
        "season":
            args.season_label,

        "competition":
            "Premier League",

        "latest_gameweek":
            latest_gw,

        "gameweeks_included":
            sorted(
                {
                    int(x)
                    for x
                    in matches[
                        "_source_gw"
                    ]
                    .dropna()
                    .unique()
                }
            ),

        "matches":
            unique_matches,

        "players":
            int(
                len(
                    result
                )
            ),

        "source":
            "olbauday/FPL-Core-Insights",

        "source_commit":
            source_commit,

        "source_updated_at":
            source_updated_at,
    }


    Path(
        args.metadata
    ).write_text(
        json.dumps(
            metadata,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


    print()
    print(
        "SUCCESS"
    )

    print(
        f"Saved {len(result)} players to {args.output}"
    )

    print(
        f"Premier League data through GW{latest_gw}"
    )

    print(
        f"Unique matches: {unique_matches}"
    )

    print(
        f"Freshness metadata: {args.metadata}"
    )


if __name__ == "__main__":
    main()
