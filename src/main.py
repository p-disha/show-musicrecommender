"""
Command line runner for the Music Recommender Simulation.

Runs six user profiles — three standard and three adversarial — and prints
ranked top-5 recommendations with per-song scores and scoring reasons.
"""

import re
from pathlib import Path
from tabulate import tabulate
from recommender import (
    load_songs, recommend_songs,
    BalancedStrategy, GenreFirstStrategy, MoodFirstStrategy, EnergyFocusedStrategy,
    DiversityPenaltyStrategy,
)

# ---------------------------------------------------------------------------
# Switch ranking strategy here — one line change to try a different mode:
#
#   BalancedStrategy()                          — default, total score wins
#   GenreFirstStrategy()                        — genre-matched songs always first
#   MoodFirstStrategy()                         — mood-matched songs always first
#   EnergyFocusedStrategy()                     — energy proximity dominates (3x weight)
#   DiversityPenaltyStrategy()                  — wraps Balanced + diversity re-ranking
#   DiversityPenaltyStrategy(GenreFirstStrategy(),
#       artist_penalty=3.0, genre_penalty=1.5)  — Genre-First with custom penalties
# ---------------------------------------------------------------------------
ACTIVE_STRATEGY = DiversityPenaltyStrategy()

CSV_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

DIVIDER = "=" * 72

# ---------------------------------------------------------------------------
# Standard profiles
# ---------------------------------------------------------------------------

HIGH_ENERGY_POP = {
    "_label":                  "High-Energy Pop",
    "favorite_genre":          "pop",
    "favorite_mood":           "happy",
    "target_energy":           0.88,
    "target_valence":          0.82,
    "target_acousticness":     0.08,
    "target_instrumentalness": 0.02,
    "target_loudness_norm":    0.85,
    "preferred_mode":          1,
    "target_popularity":       0.75,
    "preferred_decade":        2020,
    "preferred_mood_tags":     "uplifting,bright",
    "preferred_context":       "party",
    "allow_explicit":          0,
}

CHILL_LOFI = {
    "_label":                  "Chill Lofi",
    "favorite_genre":          "lofi",
    "favorite_mood":           "chill",
    "target_energy":           0.38,
    "target_valence":          0.58,
    "target_acousticness":     0.80,
    "target_instrumentalness": 0.70,
    "target_loudness_norm":    0.33,
    "preferred_mode":          0,
    "target_popularity":       0.40,
    "preferred_decade":        2020,
    "preferred_mood_tags":     "focused,calm",
    "preferred_context":       "study",
    "allow_explicit":          0,
}

DEEP_INTENSE_ROCK = {
    "_label":                  "Deep Intense Rock",
    "favorite_genre":          "rock",
    "favorite_mood":           "intense",
    "target_energy":           0.91,
    "target_valence":          0.48,
    "target_acousticness":     0.10,
    "target_instrumentalness": 0.04,
    "target_loudness_norm":    0.85,
    "preferred_mode":          0,
    "target_popularity":       0.60,
    "preferred_decade":        2010,
    "preferred_mood_tags":     "aggressive,empowering",
    "preferred_context":       "workout",
    "allow_explicit":          1,
}

# ---------------------------------------------------------------------------
# Adversarial / edge-case profiles
# ---------------------------------------------------------------------------

# Edge case 1: contradictory emotional signals
# High energy (0.92) demands intensity, but sad mood + low valence (0.25)
# pulls toward slow, melancholic tracks. Tests whether energy or mood wins.
HIGH_ENERGY_SAD = {
    "_label":                  "ADVERSARIAL — High Energy + Sad Mood",
    "favorite_genre":          "blues",
    "favorite_mood":           "sad",
    "target_energy":           0.92,
    "target_valence":          0.25,
    "target_acousticness":     0.70,
    "target_instrumentalness": 0.15,
    "target_loudness_norm":    0.85,
    "preferred_mode":          0,
    "target_popularity":       0.40,
    "preferred_decade":        2000,
    "preferred_mood_tags":     "melancholic,longing",
    "preferred_context":       "chill",
    "allow_explicit":          0,
}

# Edge case 2: genre not in the catalog at all
# No song in songs.csv has genre "k-pop", so genre_match always scores 0.
# Tests whether the numeric features alone produce a sensible fallback ranking.
GHOST_GENRE = {
    "_label":                  "ADVERSARIAL — Genre Not in Catalog (k-pop)",
    "favorite_genre":          "k-pop",
    "favorite_mood":           "happy",
    "target_energy":           0.80,
    "target_valence":          0.85,
    "target_acousticness":     0.15,
    "target_instrumentalness": 0.02,
    "target_loudness_norm":    0.72,
    "preferred_mode":          1,
    "target_popularity":       0.80,
    "preferred_decade":        2020,
    "preferred_mood_tags":     "uplifting,bright",
    "preferred_context":       "party",
    "allow_explicit":          0,
}

# Edge case 3: perfectly neutral — all numeric targets at 0.5, no strong mood
# or genre. Tests whether the system just returns the most "average" songs
# and whether scores cluster too tightly to produce a meaningful ranking.
ALL_NEUTRAL = {
    "_label":                  "ADVERSARIAL — Perfectly Neutral (all 0.5)",
    "favorite_genre":          "ambient",
    "favorite_mood":           "relaxed",
    "target_energy":           0.50,
    "target_valence":          0.50,
    "target_acousticness":     0.50,
    "target_instrumentalness": 0.50,
    "target_loudness_norm":    0.50,
    "preferred_mode":          1,
    "target_popularity":       0.50,
    "preferred_decade":        2010,
    "preferred_mood_tags":     "calm,relaxed",
    "preferred_context":       "chill",
    "allow_explicit":          0,
}


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _parse_reason(reason: str):
    """
    Split one reason string into a (label, points) pair for table display.

    Handles three formats produced by score_song / strategies:
      "Mood match 'happy': +3.0"          -> ("Mood match 'happy'",        "+3.00")
      "[Diversity penalty: genre -1.0]"   -> ("Diversity penalty",         "genre -1.0")
      "[Energy Boost: +2.40]"             -> ("Energy Boost",              "+2.40")
    """
    reason = reason.strip()
    # Bracket annotations from strategy wrappers
    if reason.startswith("[") and reason.endswith("]"):
        inner = reason[1:-1]
        idx = inner.find(":")
        if idx != -1:
            return inner[:idx].strip(), inner[idx + 1:].strip()
        return inner, "—"
    # Normal scored component: "Label (detail): +N.NN"
    m = re.match(r"^(.*?):\s*([+-]\d+\.\d+)$", reason)
    if m:
        return m.group(1).strip(), f"{float(m.group(2)):+.2f}"
    return reason, "—"


def print_profile(user_prefs: dict, strategy_name: str = "Balanced") -> None:
    """Print a two-column profile summary table."""
    label = user_prefs.get("_label", "User Profile")
    mode_str = "Major" if user_prefs["preferred_mode"] == 1 else "Minor"
    rows = [
        ("Profile",  label),
        ("Strategy", strategy_name),
        ("Genre",    user_prefs["favorite_genre"]),
        ("Mood",     user_prefs["favorite_mood"]),
        ("Energy",   user_prefs["target_energy"]),
        ("Valence",  user_prefs["target_valence"]),
        ("Acousticness", user_prefs["target_acousticness"]),
        ("Mode",     mode_str),
        ("Context",  user_prefs.get("preferred_context", "—")),
        ("Decade",   user_prefs.get("preferred_decade", "—")),
    ]
    print(f"\n{DIVIDER}")
    print(tabulate(rows, tablefmt="simple", colalign=("right", "left")))
    print(DIVIDER)


def print_recommendations(recommendations: list) -> None:
    """
    Print two tables per run:
      1. A compact summary of all top-k songs.
      2. A per-song scoring breakdown showing every reason and its points.
    """
    # ── Summary table ────────────────────────────────────────────────────────
    summary_rows = [
        (
            f"#{rank}",
            song["title"],
            song["artist"],
            song["genre"],
            song["mood"],
            f"{score:.2f} / 16.00",
        )
        for rank, (song, score, _) in enumerate(recommendations, start=1)
    ]
    print(f"\n  TOP {len(recommendations)} RECOMMENDATIONS\n")
    print(tabulate(
        summary_rows,
        headers=["#", "Title", "Artist", "Genre", "Mood", "Score"],
        tablefmt="grid",
        colalign=("center", "left", "left", "left", "left", "right"),
    ))

    # ── Per-song scoring breakdown ────────────────────────────────────────────
    print("\n  SCORING BREAKDOWN\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        header_line = f"  #{rank}  {song['title']}  --  {song['artist']}   ({score:.2f} / 16.00)"
        print(header_line)
        reasons = [r for r in explanation.split(" | ") if r.strip()]
        breakdown_rows = [_parse_reason(r) for r in reasons]
        print(tabulate(
            breakdown_rows,
            headers=["Component / Detail", "Points"],
            tablefmt="simple",
            colalign=("left", "right"),
            disable_numparse=True,
        ))
        print()


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main() -> None:
    """Load catalog, run all profiles, and print top-5 results for each."""
    songs = load_songs(CSV_PATH)
    print(f"\nCatalog ready: {len(songs)} songs loaded.\n")

    profiles = [
        HIGH_ENERGY_POP,
        CHILL_LOFI,
        DEEP_INTENSE_ROCK,
        HIGH_ENERGY_SAD,
        GHOST_GENRE,
        ALL_NEUTRAL,
    ]

    for prefs in profiles:
        # Strip internal label key before passing to recommender
        user_prefs = {k: v for k, v in prefs.items() if k != "_label"}
        recommendations = recommend_songs(user_prefs, songs, k=5, strategy=ACTIVE_STRATEGY)
        print_profile(prefs, strategy_name=ACTIVE_STRATEGY.name)
        print_recommendations(recommendations)
        print(DIVIDER)


if __name__ == "__main__":
    main()
