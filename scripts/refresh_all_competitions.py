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


ALIASES = {
    "minutes_played": ["minutes_played", "minutes"],
    "goals": ["goals", "goals_scored"],
    "assists": ["assists"],
    "total_shots": ["total_shots", "shots"],
    "xg": ["xg", "expected_goals"],
    "xa": ["xa", "expected_assists"],
    "shots_on_target": ["shots_on_target"],
    "successful_dribbles": ["successful_dribbles"],
    "big_chances_missed": ["big_chances_missed"],
    "touches_opposition_box": [
        "touches_opposition_box",
        "touches_in_opposition_box",
    ],
    "touches": ["touches"],
    "chances_created": [
        "chances_created",
        "key_passes",
    ],
    "tackles": ["tackles"],
    "tackles_won": ["tackles_won"],
    "interceptions": ["interceptions"],
    "recoveries": ["recoveries"],
    "blocks": ["blocks"],
    "clearances": ["clearances"],
    "duels_won": ["duels_won"],
    "duels_lost": ["duels_lost"],
    "dispossessed": ["dispossessed"],
}


def git_value(repo, args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            text=True,
        ).strip()
    except Exception:
        return None


def season_label(folder_name):
    m = re.fullmatch(r"(\d{4})-(\d{4})", folder_name)

    if not m:
        return folder_name

    return f"{m.group(1)}/{m.group(2)[-2:]}"


def normalise_player_id(df):
    if "player_id" not in df.columns and "id" in df.columns:
        df = df.rename(columns={"id": "player_id"})

    return df


def canonicalise_stats(df):
    df = normalise_player_id(df.copy())

    for target, candidates in ALIASES.items():
        if target in df.columns:
            continue

        found = None

        for candidate in candidates:
            if candidate in df.columns:
                found = candidate
                break

        if found is not None:
            df[target] = df[found]
        else:
            df[target] = np.nan

    for col in RAW_COLUMNS:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    return df


def read_player_master(season_root, tournament_root):
    candidates = []

    root_players = season_root / "players.csv"

    if root_players.exists():
        candidates.append(root_players)

    for p in tournament_root.glob("*/players.csv"):
        candidates.append(p)

    frames = []

    for file in candidates:
        try:
            df = pd.read_csv(file)
        except Exception:
            continue

        df = normalise_player_id(df)

        if "player_id" not in df.columns:
            continue

        if "player_code" not in df.columns and "code" in df.columns:
            df["player_code"] = df["code"]

        frames.append(df)

    if not frames:
        return pd.DataFrame(
            columns=[
                "player_id",
                "player_code",
                "web_name",
                "first_name",
                "second_name",
                "position",
                "team_code",
            ]
        )

    players = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    players = players.drop_duplicates(
        "player_id",
        keep="last",
    )

    wanted = [
        "player_id",
        "player_code",
        "web_name",
        "first_name",
        "second_name",
        "position",
        "team_code",
    ]

    for col in wanted:
        if col not in players.columns:
            players[col] = np.nan

    return players[wanted]


def finished_mask(df):
    if "finished" not in df.columns:
        return pd.Series(True, index=df.index)

    values = (
        df["finished"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return values.isin(
        ["true", "1", "yes", "y"]
    )


def process_competition(
    season_root,
    competition_dir,
    season_name,
):
    gw_dirs = []

    for folder in competition_dir.iterdir():
        if not folder.is_dir():
            continue

        m = re.fullmatch(r"GW(\d+)", folder.name)

        if m:
            gw_dirs.append(
                (int(m.group(1)), folder)
            )

    gw_dirs.sort(
        key=lambda x: x[0]
    )

    stat_frames = []
    match_frames = []

    latest_bucket = None

    for bucket, folder in gw_dirs:
        stats_file = folder / "playermatchstats.csv"

        if stats_file.exists():
            try:
                s = pd.read_csv(stats_file)
            except Exception:
                s = pd.DataFrame()

            if not s.empty:
                s = canonicalise_stats(s)

                if "player_id" in s.columns:
                    s["_bucket"] = bucket
                    stat_frames.append(s)
                    latest_bucket = bucket

        matches_file = folder / "matches.csv"

        if matches_file.exists():
            try:
                m = pd.read_csv(matches_file)
            except Exception:
                m = pd.DataFrame()

            if not m.empty:
                m["_bucket"] = bucket
                match_frames.append(m)

    if not stat_frames:
        return None, None

    stats = pd.concat(
        stat_frames,
        ignore_index=True,
        sort=False,
    )

    if "match_id" in stats.columns:
        stats = (
            stats
            .sort_values("_bucket")
            .drop_duplicates(
                ["player_id", "match_id"],
                keep="last",
            )
        )

    players = read_player_master(
        season_root,
        competition_dir,
    )

    totals = (
        stats
        .groupby(
            "player_id",
            as_index=False,
        )[RAW_COLUMNS]
        .sum(min_count=1)
    )

    result = totals.merge(
        players,
        on="player_id",
        how="left",
    )

    result["season"] = season_name
    result["competition"] = competition_dir.name

    identifiers = [
        "season",
        "competition",
        "player_id",
        "player_code",
        "web_name",
        "first_name",
        "second_name",
        "position",
        "team_code",
    ]

    result = result[
        identifiers + RAW_COLUMNS
    ]

    detailed_matches = None

    if "match_id" in stats.columns:
        positive_minutes = stats.loc[
            pd.to_numeric(
                stats["minutes_played"],
                errors="coerce",
            ).fillna(0) > 0
        ]

        detailed_matches = int(
            positive_minutes["match_id"].nunique()
        )

    finished_matches = None

    if match_frames:
        matches = pd.concat(
            match_frames,
            ignore_index=True,
            sort=False,
        )

        if "match_id" in matches.columns:
            matches = (
                matches
                .sort_values("_bucket")
                .drop_duplicates(
                    "match_id",
                    keep="last",
                )
            )

            matches = matches.loc[
                finished_mask(matches)
            ]

            finished_matches = int(
                matches["match_id"].nunique()
            )

    coverage_pct = None

    if (
        finished_matches is not None
        and finished_matches > 0
        and detailed_matches is not None
    ):
        coverage_pct = round(
            min(
                100.0,
                detailed_matches
                / finished_matches
                * 100,
            ),
            1,
        )

    metadata = {
        "season": season_name,
        "competition": competition_dir.name,
        "latest_source_bucket": latest_bucket,
        "finished_matches": finished_matches,
        "matches_with_player_stats": detailed_matches,
        "coverage_pct": coverage_pct,
        "players": int(len(result)),
    }

    return result, metadata


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source-dir",
        required=True,
    )

    parser.add_argument(
        "--output",
        default="all_competitions_player_stats.csv",
    )

    parser.add_argument(
        "--metadata",
        default="all_competitions_metadata.json",
    )

    args = parser.parse_args()

    source_repo = Path(
        args.source_dir
    ).resolve()

    data_root = source_repo / "data"

    if not data_root.exists():
        raise FileNotFoundError(
            f"No data directory found at {data_root}"
        )

    season_dirs = []

    for path in data_root.iterdir():
        if (
            path.is_dir()
            and re.fullmatch(
                r"\d{4}-\d{4}",
                path.name,
            )
            and (
                path
                / "By Tournament"
            ).exists()
        ):
            season_dirs.append(path)

    season_dirs.sort(
        key=lambda p: p.name
    )

    if not season_dirs:
        raise RuntimeError(
            "No seasons with 'By Tournament' data were found."
        )

    all_frames = []
    metadata_rows = []

    print("Seasons found:")

    for season_dir in season_dirs:
        print(
            " -",
            season_dir.name,
        )

        label = season_label(
            season_dir.name
        )

        tournament_root = (
            season_dir
            / "By Tournament"
        )

        competition_dirs = sorted(
            [
                p
                for p in tournament_root.iterdir()
                if p.is_dir()
            ],
            key=lambda p: p.name,
        )

        for competition_dir in competition_dirs:
            print(
                f"   {label} · {competition_dir.name} ...",
                end=" ",
                flush=True,
            )

            frame, meta = process_competition(
                season_dir,
                competition_dir,
                label,
            )

            if frame is None:
                print("no player-match data")
                continue

            all_frames.append(frame)
            metadata_rows.append(meta)

            coverage = meta.get(
                "coverage_pct"
            )

            coverage_text = (
                "unknown coverage"
                if coverage is None
                else f"{coverage:.1f}% match coverage"
            )

            print(
                f"{len(frame)} players · {coverage_text}"
            )

    if not all_frames:
        raise RuntimeError(
            "No tournament player data could be built."
        )

    combined = pd.concat(
        all_frames,
        ignore_index=True,
        sort=False,
    )

    combined.to_csv(
        args.output,
        index=False,
    )

    source_commit = git_value(
        source_repo,
        ["rev-parse", "HEAD"],
    )

    source_updated_at = git_value(
        source_repo,
        [
            "log",
            "-1",
            "--format=%cI",
        ],
    )

    metadata = {
        "source": "olbauday/FPL-Core-Insights",
        "source_commit": source_commit,
        "source_updated_at": source_updated_at,
        "competitions": metadata_rows,
    }

    Path(args.metadata).write_text(
        json.dumps(
            metadata,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print(
        f"Player/competition rows: {len(combined):,}"
    )
    print(
        f"Seasons: {combined['season'].nunique()}"
    )
    print(
        f"Competitions: {combined['competition'].nunique()}"
    )
    print(
        f"Saved: {args.output}"
    )
    print(
        f"Metadata: {args.metadata}"
    )

    print()
    print("Competitions present:")

    for competition in sorted(
        combined["competition"]
        .dropna()
        .unique()
    ):
        print(
            " -",
            competition,
        )


if __name__ == "__main__":
    main()
