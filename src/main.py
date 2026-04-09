"""
Command line runner for the Music Recommender Simulation.
"""

from pathlib import Path
from recommender import load_songs, recommend_songs

CSV_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

DIVIDER     = "=" * 60
SUBDIVISION = "-" * 60


def print_profile(user_prefs: dict) -> None:
    """Print a formatted summary of the active user taste profile."""
    print(DIVIDER)
    print("  USER PROFILE")
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
        # Header row
        print(f"  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Genre: {song['genre']}  |  Mood: {song['mood']}  |  Score: {score:.2f} / 11.00")
        print(SUBDIVISION)

        # One reason per line, indented
        for reason in explanation.split(" | "):
            print(f"       {reason}")

        print()


def main() -> None:
    """Load catalog, score all songs against the user profile, and print top-k results."""
    songs = load_songs(CSV_PATH)

    user_prefs = {
        "favorite_genre":          "pop",
        "favorite_mood":           "happy",
        "target_energy":           0.80,
        "target_valence":          0.80,
        "target_acousticness":     0.20,
        "target_instrumentalness": 0.02,
        "target_loudness_norm":    0.70,
        "preferred_mode":          1,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print_profile(user_prefs)
    print_recommendations(recommendations)
    print(DIVIDER)


if __name__ == "__main__":
    main()
