from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

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
    target_popularity: float = 0.5      # 0.0–1.0 (normalised; 0.75 = mainstream)
    preferred_decade: int = 2010        # e.g. 2020, 2010, 2000, 1990
    preferred_mood_tags: str = ""       # comma-separated tags e.g. "nostalgic,warm"
    preferred_context: str = ""         # workout / study / party / commute / chill / focus
    allow_explicit: int = 1             # 1 = explicit OK, 0 = clean only


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
    "target_popularity": 0.40,
    "preferred_decade": 2020,
    "preferred_mood_tags": "focused,calm",
    "preferred_context": "study",
    "allow_explicit": 0,
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
    "target_popularity": 0.65,
    "preferred_decade": 2010,
    "preferred_mood_tags": "aggressive,empowering",
    "preferred_context": "workout",
    "allow_explicit": 1,
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
    "target_popularity": 0.55,
    "preferred_decade": 2020,
    "preferred_mood_tags": "sensual,intimate",
    "preferred_context": "chill",
    "allow_explicit": 0,
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
    int_cols = {"id", "tempo_bpm", "mode", "popularity", "release_decade", "explicit"}

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

    # --- Popularity proximity (max +1.0) ---
    pop_pts = 1.0 * (1 - abs(song.get("popularity", 50) / 100.0 - user_prefs.get("target_popularity", 0.5)))
    score += pop_pts
    reasons.append(f"Popularity ({song.get('popularity', 50)} vs target {user_prefs.get('target_popularity', 0.5)*100:.0f}): +{pop_pts:.2f}")

    # --- Release decade (max +1.5) ---
    decade_diff = abs(int(song.get("release_decade", 2010)) - int(user_prefs.get("preferred_decade", 2010))) // 10
    if decade_diff == 0:
        decade_pts = 1.5
    elif decade_diff == 1:
        decade_pts = 0.75
    elif decade_diff == 2:
        decade_pts = 0.25
    else:
        decade_pts = 0.0
    score += decade_pts
    reasons.append(f"Decade ({song.get('release_decade', 2010)} vs {user_prefs.get('preferred_decade', 2010)}, diff={decade_diff*10}yr): +{decade_pts:.2f}")

    # --- Mood tags (max +1.5 — 0.5 per matching tag) ---
    song_tags = set(t.strip() for t in str(song.get("mood_tags", "")).split(",") if t.strip())
    user_tags = set(t.strip() for t in str(user_prefs.get("preferred_mood_tags", "")).split(",") if t.strip())
    matched_tags = song_tags & user_tags
    tag_pts = min(0.5 * len(matched_tags), 1.5)
    score += tag_pts
    reasons.append(f"Mood tags (matched {len(matched_tags)}: {matched_tags or 'none'}): +{tag_pts:.2f}")

    # --- Context match (max +1.0) ---
    if song.get("context") == user_prefs.get("preferred_context"):
        ctx_pts = 1.0
        reasons.append(f"Context match '{song['context']}': +1.00")
    else:
        ctx_pts = 0.0
        reasons.append(f"Context mismatch ('{song.get('context')}' vs '{user_prefs.get('preferred_context')}'): +0.00")
    score += ctx_pts

    # --- Explicit penalty (−1.0 if user wants clean but song is explicit) ---
    if int(user_prefs.get("allow_explicit", 1)) == 0 and int(song.get("explicit", 0)) == 1:
        expl_pts = -1.0
        reasons.append(f"Explicit penalty (user clean-only): -1.00")
    else:
        expl_pts = 0.0
        # no reason line needed when no penalty
    score += expl_pts

    return round(score, 3), reasons


# ---------------------------------------------------------------------------
# Ranking strategies — Strategy pattern
#
# Each strategy implements one method:
#   rank(songs, user_prefs, k) -> List[(song_dict, score, explanation)]
#
# To add a new strategy: subclass RankingStrategy and implement rank().
# To switch strategies in main.py: change ACTIVE_STRATEGY = <YourStrategy>()
# ---------------------------------------------------------------------------

class RankingStrategy(ABC):
    """Abstract base for all ranking strategies."""
    name: str = "Base"

    @abstractmethod
    def rank(
        self,
        songs: List[Dict],
        user_prefs: Dict,
        k: int,
    ) -> List[Tuple[Dict, float, str]]:
        ...


class BalancedStrategy(RankingStrategy):
    """
    Default balanced ranking.
    Every scoring dimension contributes to one total score.
    Songs are sorted purely by that total, highest first.
    Tiebreak: tempo proximity when user_prefs carries 'target_bpm'.
    """
    name = "Balanced"

    def rank(self, songs, user_prefs, k):
        scored = []
        target_bpm = user_prefs.get("target_bpm")
        for song in songs:
            score, reasons = score_song(user_prefs, song)
            scored.append((song, score, " | ".join(reasons)))
        scored.sort(key=lambda x: (
            -x[1],
            abs(float(x[0].get("tempo_bpm", 0)) - target_bpm) if target_bpm else 0,
        ))
        return scored[:k]


class GenreFirstStrategy(RankingStrategy):
    """
    Genre-First ranking.
    Songs that match the user's favorite genre are always shown before
    songs that don't, regardless of total score.
    Within each group, songs are sorted by total score descending.

    Use this when genre identity is the listener's hard requirement
    (e.g., "only show me rock songs, best ones first").
    """
    name = "Genre-First"

    def rank(self, songs, user_prefs, k):
        scored = []
        for song in songs:
            score, reasons = score_song(user_prefs, song)
            genre_match = 1 if song.get("genre") == user_prefs.get("favorite_genre") else 0
            scored.append((song, score, " | ".join(reasons), genre_match))
        # Primary: genre match (1 before 0); secondary: score descending
        scored.sort(key=lambda x: (-x[3], -x[1]))
        return [(s, sc, ex) for s, sc, ex, _ in scored[:k]]


class MoodFirstStrategy(RankingStrategy):
    """
    Mood-First ranking.
    Songs that match the user's favorite mood always appear before
    songs that don't, regardless of total score.
    Within each group, songs are sorted by total score descending.

    Use this when emotional context is the listener's priority
    (e.g., "I need sad songs right now — best sad songs first").
    """
    name = "Mood-First"

    def rank(self, songs, user_prefs, k):
        scored = []
        for song in songs:
            score, reasons = score_song(user_prefs, song)
            mood_match = 1 if song.get("mood") == user_prefs.get("favorite_mood") else 0
            scored.append((song, score, " | ".join(reasons), mood_match))
        # Primary: mood match (1 before 0); secondary: score descending
        scored.sort(key=lambda x: (-x[3], -x[1]))
        return [(s, sc, ex) for s, sc, ex, _ in scored[:k]]


class EnergyFocusedStrategy(RankingStrategy):
    """
    Energy-Focused ranking.
    Applies a 3× multiplier to the energy proximity component on top of
    the base score, so songs whose energy closely matches the user's target
    rise to the top even when genre/mood don't match.

    Original energy component: 2.0 × (1 − |song − target|)
    Boosted energy component:  6.0 × (1 − |song − target|)   (+4.0 extra max)
    All other components are unchanged.

    Use this for activity-driven playlists (workouts, wind-down sessions)
    where physical intensity matters more than genre or mood label.
    """
    name = "Energy-Focused"
    ENERGY_EXTRA_WEIGHT = 4.0  # added on top of the base 2.0 pts already in score

    def rank(self, songs, user_prefs, k):
        scored = []
        for song in songs:
            base_score, reasons = score_song(user_prefs, song)
            energy_diff = abs(float(song.get("energy", 0.5)) - user_prefs.get("target_energy", 0.5))
            extra = round(self.ENERGY_EXTRA_WEIGHT * (1 - energy_diff), 3)
            boosted = round(base_score + extra, 3)
            explanation = " | ".join(reasons) + f" | [Energy Boost: +{extra:.2f}]"
            scored.append((song, boosted, explanation))
        scored.sort(key=lambda x: -x[1])
        return scored[:k]


class DiversityPenaltyStrategy(RankingStrategy):
    """
    Wraps any base strategy and adds a greedy diversity re-ranking pass.

    How it works
    ------------
    1. The base strategy scores every song in the full catalog.
    2. Songs are then selected one at a time (greedy):
       - Before each pick, every remaining candidate has its score
         temporarily adjusted by subtracting penalties for any artist
         or genre already present in the result list so far.
       - The candidate with the highest *adjusted* score is picked next.
       - Its artist and genre are recorded, then the loop continues.
    3. This means the 2nd song from the same artist takes a -2.0 hit,
       and the 2nd song from the same genre takes a -1.0 hit, so they
       only rank above other candidates if they are genuinely much better.

    Both penalties are cumulative: a song whose artist AND genre are
    already represented loses both penalties simultaneously.

    Parameters
    ----------
    base_strategy   : any RankingStrategy (default: BalancedStrategy)
    artist_penalty  : score deducted per repeated artist  (default 2.0)
    genre_penalty   : score deducted per repeated genre   (default 1.0)
    """

    def __init__(
        self,
        base_strategy: Optional[RankingStrategy] = None,
        artist_penalty: float = 2.0,
        genre_penalty: float = 1.0,
    ):
        self.base = base_strategy if base_strategy is not None else BalancedStrategy()
        self.artist_penalty = artist_penalty
        self.genre_penalty = genre_penalty
        self.name = f"Diversity({self.base.name})"

    def rank(self, songs, user_prefs, k):
        # Score the full catalog — no k limit here; we need the whole pool
        all_scored = self.base.rank(songs, user_prefs, len(songs))

        results = []
        seen_artists: set = set()
        seen_genres: set = set()
        candidates = list(all_scored)  # list of (song_dict, score, explanation)

        while len(results) < k and candidates:
            # Apply diversity penalties to every remaining candidate
            adjusted = []
            for song, score, explanation in candidates:
                penalty = 0.0
                notes = []
                if song.get("artist") in seen_artists:
                    penalty += self.artist_penalty
                    notes.append(f"artist repeat -{self.artist_penalty:.1f}")
                if song.get("genre") in seen_genres:
                    penalty += self.genre_penalty
                    notes.append(f"genre repeat -{self.genre_penalty:.1f}")
                adj_score = round(score - penalty, 3)
                adj_expl = explanation + (f" | [Diversity penalty: {', '.join(notes)}]" if notes else "")
                adjusted.append((song, adj_score, adj_expl))

            # Pick the highest adjusted-score candidate
            adjusted.sort(key=lambda x: -x[1])
            best_song, best_score, best_expl = adjusted[0]
            results.append((best_song, best_score, best_expl))

            # Record the picked song's artist and genre
            seen_artists.add(best_song.get("artist"))
            seen_genres.add(best_song.get("genre"))

            # Remove the picked song from the candidate pool
            picked_title = best_song.get("title")
            candidates = [(s, sc, ex) for s, sc, ex in candidates
                          if s.get("title") != picked_title]

        return results


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    strategy: Optional[RankingStrategy] = None) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song and returns the top-k results.

    Delegates ranking to a RankingStrategy instance.
    If no strategy is supplied, BalancedStrategy (original behaviour) is used.

    Returns:
        List of (song_dict, score, explanation_string) tuples, best first.
    """
    if strategy is None:
        strategy = BalancedStrategy()
    return strategy.rank(songs, user_prefs, k)
