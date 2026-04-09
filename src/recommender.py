from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    instrumentalness: float
    speechiness: float
    liveness: float
    loudness_norm: float
    mode: int  # 0 = minor, 1 = major

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    target_valence: float
    target_acousticness: float
    target_instrumentalness: float
    target_speechiness: float
    target_loudness_norm: float
    preferred_mode: int  # 0 = minor, 1 = major


# ---------------------------------------------------------------------------
# Concrete taste profiles — ready to pass into recommend_songs()
# ---------------------------------------------------------------------------

CHILL_LOFI_STUDENT = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.40,
    "target_valence": 0.58,
    "target_acousticness": 0.75,
    "target_instrumentalness": 0.70,
    "target_speechiness": 0.04,
    "target_loudness_norm": 0.35,
    "preferred_mode": 0,          # minor = slightly melancholic
}

INTENSE_WORKOUT = {
    "favorite_genre": "rock",
    "favorite_mood": "intense",
    "target_energy": 0.92,
    "target_valence": 0.55,
    "target_acousticness": 0.08,
    "target_instrumentalness": 0.05,
    "target_speechiness": 0.10,
    "target_loudness_norm": 0.88,
    "preferred_mode": 0,          # minor = aggressive drive
}

LATE_NIGHT_ROMANTIC = {
    "favorite_genre": "r&b",
    "favorite_mood": "romantic",
    "target_energy": 0.54,
    "target_valence": 0.75,
    "target_acousticness": 0.50,
    "target_instrumentalness": 0.04,
    "target_speechiness": 0.07,
    "target_loudness_norm": 0.50,
    "preferred_mode": 1,          # major = warm and positive
}

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Initialise the recommender with a pre-loaded list of Song objects."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return top-k songs ranked by score against the user profile."""
        from dataclasses import asdict
        user_prefs = asdict(user)
        scored = []
        for song in self.songs:
            song_dict = asdict(song)
            score, _ = score_song(user_prefs, song_dict)
            scored.append((song, score))
        scored.sort(key=lambda x: -x[1])
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why this song was recommended."""
        from dataclasses import asdict
        _, reasons = score_song(asdict(user), asdict(song))
        return " | ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file and returns a list of dicts.
    Numeric columns are cast to float or int so math works downstream.
    Required by src/main.py
    """
    import csv

    float_cols = {
        "energy", "valence", "danceability", "acousticness",
        "instrumentalness", "speechiness", "liveness", "loudness_norm",
    }
    int_cols = {"id", "tempo_bpm", "mode"}

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col in float_cols:
                if col in row:
                    row[col] = float(row[col])
            for col in int_cols:
                if col in row:
                    row[col] = int(row[col])
            songs.append(row)

    print(f"Loaded songs: {len(songs)}")
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences using the Algorithm Recipe.

    POINT BUDGET (max 11.0 total):
      Categorical — fixed points on exact match:
        Mood match ............. +3.0  (strongest context signal)
        Genre match ............ +2.0  (taste identity)
        Mode match ............. +0.5  (minor/major emotional alignment)

      Numerical — proximity points (max × (1 - |song_val - target_val|)):
        Energy ................. max +2.0  (widest catalog spread, 0.22–0.97)
        Valence ................ max +1.5  (emotional brightness)
        Acousticness ........... max +1.0  (instrument texture preference)
        Instrumentalness ....... max +0.5  (vocal vs. instrumental feel)
        Loudness ............... max +0.5  (intensity texture)

    Returns:
        (score, reasons) where score is a float and reasons is a list of strings.
    """
    score = 0.0
    reasons = []

    # --- Categorical: Mood (3.0 pts) ---
    if song.get("mood") == user_prefs.get("favorite_mood"):
        score += 3.0
        reasons.append(f"Mood match '{song['mood']}': +3.0")
    else:
        reasons.append(f"Mood mismatch ('{song['mood']}' vs '{user_prefs.get('favorite_mood')}'): +0.0")

    # --- Categorical: Genre (2.0 pts) ---
    if song.get("genre") == user_prefs.get("favorite_genre"):
        score += 2.0
        reasons.append(f"Genre match '{song['genre']}': +2.0")
    else:
        reasons.append(f"Genre mismatch ('{song['genre']}' vs '{user_prefs.get('favorite_genre')}'): +0.0")

    # --- Categorical: Mode (0.5 pts) ---
    if int(song.get("mode", -1)) == user_prefs.get("preferred_mode"):
        score += 0.5
        reasons.append(f"Mode match ({'major' if song['mode'] else 'minor'}): +0.5")

    # --- Numerical: Energy (max 2.0 pts) ---
    energy_pts = 2.0 * (1 - abs(float(song["energy"]) - user_prefs["target_energy"]))
    score += energy_pts
    reasons.append(f"Energy ({song['energy']} vs {user_prefs['target_energy']}): +{energy_pts:.2f}")

    # --- Numerical: Valence (max 1.5 pts) ---
    valence_pts = 1.5 * (1 - abs(float(song["valence"]) - user_prefs["target_valence"]))
    score += valence_pts
    reasons.append(f"Valence ({song['valence']} vs {user_prefs['target_valence']}): +{valence_pts:.2f}")

    # --- Numerical: Acousticness (max 1.0 pts) ---
    acoustic_pts = 1.0 * (1 - abs(float(song["acousticness"]) - user_prefs["target_acousticness"]))
    score += acoustic_pts
    reasons.append(f"Acousticness ({song['acousticness']} vs {user_prefs['target_acousticness']}): +{acoustic_pts:.2f}")

    # --- Numerical: Instrumentalness (max 0.5 pts) ---
    instr_pts = 0.5 * (1 - abs(float(song["instrumentalness"]) - user_prefs["target_instrumentalness"]))
    score += instr_pts
    reasons.append(f"Instrumentalness ({song['instrumentalness']} vs {user_prefs['target_instrumentalness']}): +{instr_pts:.2f}")

    # --- Numerical: Loudness (max 0.5 pts) ---
    loud_pts = 0.5 * (1 - abs(float(song["loudness_norm"]) - user_prefs["target_loudness_norm"]))
    score += loud_pts
    reasons.append(f"Loudness ({song['loudness_norm']} vs {user_prefs['target_loudness_norm']}): +{loud_pts:.2f}")

    return round(score, 3), reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, ranks by score descending, returns top-k.

    Ranking rules:
      1. Sort all songs by score descending.
      2. Tiebreak: prefer lower |tempo_bpm - target_bpm| if user_prefs has 'target_bpm'.
      3. Return top-k as (song_dict, score, explanation_string) tuples.
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = " | ".join(reasons)
        scored.append((song, score, explanation))

    # Primary sort: score descending; secondary: tempo proximity if available
    target_bpm = user_prefs.get("target_bpm")
    scored.sort(
        key=lambda x: (
            -x[1],
            abs(float(x[0].get("tempo_bpm", 0)) - target_bpm) if target_bpm else 0
        )
    )

    return scored[:k]
