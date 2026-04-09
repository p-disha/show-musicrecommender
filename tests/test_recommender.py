from src.recommender import Song, UserProfile, Recommender


def make_song(id, title, genre, mood, energy, valence, acousticness,
              tempo_bpm=100, danceability=0.6, instrumentalness=0.05,
              speechiness=0.05, liveness=0.10, loudness_norm=0.5, mode=1):
    return Song(
        id=id, title=title, artist="Test Artist",
        genre=genre, mood=mood, energy=energy,
        tempo_bpm=tempo_bpm, valence=valence,
        danceability=danceability, acousticness=acousticness,
        instrumentalness=instrumentalness, speechiness=speechiness,
        liveness=liveness, loudness_norm=loudness_norm, mode=mode,
    )


def make_user(**overrides):
    defaults = dict(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        target_valence=0.8,
        target_acousticness=0.2,
        target_instrumentalness=0.02,
        target_speechiness=0.06,
        target_loudness_norm=0.7,
        preferred_mode=1,
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


def make_small_recommender() -> Recommender:
    songs = [
        make_song(id=1, title="Test Pop Track", genre="pop",
                  mood="happy", energy=0.8, valence=0.9, acousticness=0.2),
        make_song(id=2, title="Chill Lofi Loop", genre="lofi",
                  mood="chill", energy=0.4, valence=0.6, acousticness=0.9),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = make_user()
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # The pop/happy/high-energy song must outscore the lofi/chill song
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_recommend_top_song_beats_second():
    """Score of rank-1 must be >= score of rank-2."""
    from dataclasses import asdict
    from src.recommender import score_song

    user = make_user()
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    score_first, _ = score_song(asdict(user), asdict(results[0]))
    score_second, _ = score_song(asdict(user), asdict(results[1]))
    assert score_first >= score_second


def test_explain_recommendation_returns_non_empty_string():
    user = make_user()
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])

    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_explain_contains_mood_and_genre():
    """Explanation must mention both mood and genre outcomes."""
    user = make_user()
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])

    assert "Mood" in explanation
    assert "Genre" in explanation


def test_score_song_mood_match_adds_three_points():
    """A mood match must contribute exactly +3.0 to the score."""
    from dataclasses import asdict
    from src.recommender import score_song

    user = make_user(favorite_mood="happy", favorite_genre="__none__")
    song = make_song(id=99, title="X", genre="other", mood="happy",
                     energy=0.8, valence=0.8, acousticness=0.2)
    no_match_song = make_song(id=100, title="Y", genre="other", mood="chill",
                               energy=0.8, valence=0.8, acousticness=0.2)

    score_match, _ = score_song(asdict(user), asdict(song))
    score_no_match, _ = score_song(asdict(user), asdict(no_match_song))
    assert round(score_match - score_no_match, 6) == 3.0


def test_score_song_genre_match_adds_two_points():
    """A genre match must contribute exactly +2.0 to the score."""
    from dataclasses import asdict
    from src.recommender import score_song

    user = make_user(favorite_genre="pop", favorite_mood="__none__")
    song_match = make_song(id=1, title="A", genre="pop", mood="other",
                            energy=0.8, valence=0.8, acousticness=0.2)
    song_no_match = make_song(id=2, title="B", genre="rock", mood="other",
                               energy=0.8, valence=0.8, acousticness=0.2)

    score_match, _ = score_song(asdict(user), asdict(song_match))
    score_no_match, _ = score_song(asdict(user), asdict(song_no_match))
    assert round(score_match - score_no_match, 6) == 2.0


def test_score_song_returns_tuple_of_float_and_list():
    """score_song must return (float, list)."""
    from dataclasses import asdict
    from src.recommender import score_song

    user = make_user()
    song = make_song(id=1, title="T", genre="pop", mood="happy",
                     energy=0.8, valence=0.8, acousticness=0.2)
    result = score_song(asdict(user), asdict(song))

    assert isinstance(result, tuple) and len(result) == 2
    score, reasons = result
    assert isinstance(score, float)
    assert isinstance(reasons, list)
    assert len(reasons) > 0
