import soccerdata as sd
import pandas as pd

LEAGUES = {
    "ENG-Premier League": ("England", "Premier League"),
    "ESP-La Liga": ("Spain", "La Liga"),
    "GER-Bundesliga": ("Germany", "Bundesliga"),
    "ITA-Serie A": ("Italy", "Serie A"),
    "FRA-Ligue 1": ("France", "Ligue 1"),
}

# IMPORTANT:
# Use unambiguous season strings.
SEASONS = {
    "2021-22": "2021/22",
    "2022-23": "2022/23",
    "2023-24": "2023/24",
    "2024-25": "2024/25",
    "2025-26": "2025/26",
}

NUMERIC_COLS = [
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

all_rows = []

for season_source, season_label in SEASONS.items():

    print("\n" + "=" * 60)
    print(f"SEASON {season_label}")
    print("=" * 60)

    for league_code, (country, competition) in LEAGUES.items():

        print(f"\nDownloading {competition} {season_label}...")

        reader = sd.Understat(
            leagues=league_code,
            seasons=season_source
        )

        df = reader.read_player_season_stats().reset_index()

        df = df.rename(
            columns={
                "player": "player_name",
                "team": "team_name",
                "key_passes": "chances_created",
            }
        )

        df["country"] = country
        df["competition"] = competition
        df["season"] = season_label
        df["source"] = "Understat"

        keep = [
            "country",
            "competition",
            "season",
            "player_id",
            "player_name",
            "team_name",
            "position",
            *NUMERIC_COLS,
            "source",
        ]

        df = df[keep]

        print(f"{competition}: {len(df)} rows")

        all_rows.append(df)


# =========================================================
# COMBINE EVERYTHING
# =========================================================

raw = pd.concat(
    all_rows,
    ignore_index=True
)

keys = [
    "country",
    "competition",
    "season",
    "player_id",
    "player_name",
]


# =========================================================
# SUM PLAYER TOTALS
# =========================================================

totals = (
    raw
    .groupby(
        keys,
        as_index=False,
        dropna=False
    )[NUMERIC_COLS]
    .sum(min_count=1)
)


# =========================================================
# COMBINE TEAM NAMES FOR TRANSFERRED PLAYERS
# =========================================================

teams = (
    raw
    .groupby(
        keys,
        as_index=False,
        dropna=False
    )["team_name"]
    .agg(
        lambda x: " / ".join(
            sorted(
                set(
                    x.dropna().astype(str)
                )
            )
        )
    )
)


# =========================================================
# POSITION FROM THE CLUB WHERE PLAYER PLAYED MOST MINUTES
# =========================================================

position_source = (
    raw
    .sort_values(
        "minutes",
        ascending=False
    )
    .drop_duplicates(
        keys
    )[
        keys
        + ["position"]
    ]
)


# =========================================================
# MERGE
# =========================================================

big5 = (
    totals
    .merge(
        teams,
        on=keys,
        how="left"
    )
    .merge(
        position_source,
        on=keys,
        how="left"
    )
)

big5["source"] = "Understat"


# Nice column order
big5 = big5[
    [
        "country",
        "competition",
        "season",
        "player_id",
        "player_name",
        "team_name",
        "position",
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
        "source",
    ]
]


# =========================================================
# SAVE
# =========================================================

big5.to_csv(
    "understat_big5_2021_26.csv",
    index=False
)


print("\n" + "=" * 60)
print("SUCCESS")
print("=" * 60)

print(
    "Total player-seasons:",
    len(big5)
)

print("\nPlayer-seasons by competition and season:")

print(
    big5
    .groupby(
        [
            "season",
            "competition",
        ]
    )
    .size()
    .unstack(fill_value=0)
)

print("\nSanity check — seasons present:")
print(
    sorted(
        big5["season"].unique()
    )
)

print(
    "\nSaved as: understat_big5_2021_26.csv"
)
