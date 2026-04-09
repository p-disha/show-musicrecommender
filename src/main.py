"""
Command line runner for the Music Recommender Simulation.

Runs six user profiles — three standard and three adversarial — and prints
ranked top-5 recommendations with per-song scores and scoring reasons.
"""

from pathlib import Path
from recommender import load_songs, recommend_songs

CSV_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

DIVIDER     = "=" * 60
SUBDIVISION = "-" * 60

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
}


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_profile(user_prefs: dict) -> None:
    """Print a formatted summary of the active user taste profile."""
    label = user_prefs.get("_label", "User Profile")
    print(f"\n{DIVIDER}")
    print(f"  PROFILE : {label}")
    print(DIVIDER)
    print(f"  Genre        : {user_prefs['favorite_genre']}")
    print(f"  Mood         : {user_prefs['favorite_mood']}")
    print(f"  Energy       : {user_prefs['target_energy']}")
    print(f"  Valence      : {user_prefs['target_valence']}")
    print(f"  Acousticness : {user_prefs['target_acousticness']}")
    print(f"  Mode         : {'Major' if user_prefs['preferred_mode'] == 1 else 'Minor'}")
    print(DIVIDER)


def print_recommendations(recommendations: list) -> None:
    """Print ranked recommendations with per-song scores and scoring reasons."""
    print(f"\n  TOP {len(recommendations)} RECOMMENDATIONS")
    print(DIVIDER)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"  #{rank}  {song['title']}  --  {song['artist']}")
        print(f"       Genre: {song['genre']}  |  Mood: {song['mood']}  |  Score: {score:.2f} / 11.00")
        print(SUBDIVISION)
        for reason in explanation.split(" | "):
            print(f"       {reason}")
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
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_profile(prefs)
        print_recommendations(recommendations)
        print(DIVIDER)


if __name__ == "__main__":
    main()
