import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


SPECIAL_TRANSLATION = str.maketrans({
    "ø": "o",
    "Ø": "O",
    "ł": "l",
    "Ł": "L",
    "ð": "d",
    "Ð": "D",
    "þ": "th",
    "Þ": "Th",
    "æ": "ae",
    "Æ": "AE",
    "œ": "oe",
    "Œ": "OE",
    "ß": "ss",
})


def ascii_alias(value):
    text = str(value).translate(SPECIAL_TRANSLATION)

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    return (
        text
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def player_search_label(value):
    """
    Keep the player's proper displayed name, but append an ASCII
    alias when useful so Streamlit's built-in search can find it.
    """

    proper = str(value)
    alias = ascii_alias(proper)

    if (
        alias
        and alias.casefold()
        != proper.casefold()
    ):
        return f"{proper}  ·  {alias}"

    return proper


def install_player_search():
    """
    Automatically make Streamlit player selectors accent-insensitive.

    The selected value remains the ORIGINAL proper player name.
    Only the displayed/searchable label gets the ASCII alias.
    """

    if not getattr(
        st.selectbox,
        "_football_player_search",
        False,
    ):

        original_selectbox = st.selectbox

        def searchable_selectbox(
            label,
            options,
            *args,
            **kwargs,
        ):
            if (
                "player"
                in str(label).casefold()
                and "format_func"
                not in kwargs
            ):
                kwargs[
                    "format_func"
                ] = player_search_label

            return original_selectbox(
                label,
                options,
                *args,
                **kwargs,
            )

        searchable_selectbox._football_player_search = True

        st.selectbox = searchable_selectbox


    if not getattr(
        st.multiselect,
        "_football_player_search",
        False,
    ):

        original_multiselect = st.multiselect

        def searchable_multiselect(
            label,
            options,
            *args,
            **kwargs,
        ):
            if (
                "player"
                in str(label).casefold()
                and "format_func"
                not in kwargs
            ):
                kwargs[
                    "format_func"
                ] = player_search_label

            return original_multiselect(
                label,
                options,
                *args,
                **kwargs,
            )

        searchable_multiselect._football_player_search = True

        st.multiselect = searchable_multiselect


def show_pl_freshness(
    metadata_file="data_freshness.json",
):
    """
    Show when the current Premier League dataset was last synced
    and the latest PL gameweek found in the source repository.
    """

    path = Path(metadata_file)

    if not path.exists():
        st.warning(
            "⚠️ 2026/27 data freshness is not yet recorded."
        )
        return


    try:
        meta = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        st.warning(
            "⚠️ Could not read the 2026/27 data-freshness record."
        )
        return


    gw = meta.get(
        "latest_gameweek",
        "?"
    )

    updated = meta.get(
        "source_updated_at"
    )

    matches = meta.get(
        "matches"
    )

    players = meta.get(
        "players"
    )


    date_text = "unknown date"

    age_days = None


    if updated:

        try:
            dt = datetime.fromisoformat(
                updated.replace(
                    "Z",
                    "+00:00",
                )
            )

            if dt.tzinfo is None:
                dt = dt.replace(
                    tzinfo=timezone.utc
                )

            date_text = dt.strftime(
                "%d %b %Y"
            )

            age_days = (
                datetime.now(
                    timezone.utc
                )
                - dt.astimezone(
                    timezone.utc
                )
            ).total_seconds() / 86400

        except Exception:
            date_text = str(
                updated
            )


    detail = (
        f"**2026/27 Premier League data:** "
        f"through **GW{gw}** · source updated **{date_text}**"
    )


    extras = []

    if matches is not None:
        extras.append(
            f"{matches} matches"
        )

    if players is not None:
        extras.append(
            f"{players} players"
        )

    if extras:
        detail += (
            " · "
            + " · ".join(
                extras
            )
        )


    if (
        age_days is not None
        and age_days > 10
    ):
        st.warning(
            "⚠️ "
            + detail
            + " — this may be stale."
        )

    else:
        st.info(
            "✅ "
            + detail
        )
