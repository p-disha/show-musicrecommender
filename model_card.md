# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatcher 1.0**

A content-based music recommender that matches songs to a listener's taste profile using audio features and genre/mood preferences.

---

## 2. Goal / Task

VibeMatcher tries to answer one question: given what a user likes, which songs in the catalog feel most like a match?

It does not predict what a user will click on. It does not learn from listening history. It simply scores every song against a taste profile and returns the top results. It is designed for classroom exploration of how recommender systems work, not for production use.

**Intended use:** Learning, experimentation, and demonstration of content-based filtering concepts.

**Not intended for:** Real music apps, personalization at scale, replacing platforms like Spotify or Apple Music, or any use where the catalog is not manually curated and reviewed.

---

## 3. How the Model Works

Every song in the catalog gets a score between 0 and 11. Higher score = better match.

The score has two parts:

**Fixed bonuses (yes or no):**
- Mood matches the user's favorite mood → +3.0 points
- Genre matches the user's favorite genre → +2.0 points
- Key mode (major/minor) matches the user's preference → +0.5 points

**Proximity scores (partial credit based on closeness):**
- Energy: up to +2.0 points. The closer the song's energy to the user's target, the more points.
- Valence (emotional brightness): up to +1.5 points
- Acousticness: up to +1.0 points
- Instrumentalness: up to +0.5 points
- Loudness: up to +0.5 points

For proximity scores, the formula is: `max_points × (1 - |song_value - target_value|)`. A perfect match gives the full points; the further away, the fewer points earned.

Songs are then ranked from highest to lowest score. If two songs tie, the one whose tempo is closer to the user's target BPM wins.

---

## 4. Data

The catalog has **20 songs** stored in a CSV file (`data/songs.csv`).

Each song has 15 attributes: title, artist, genre, mood, energy, tempo (BPM), valence, danceability, acousticness, instrumentalness, speechiness, liveness, loudness, and key mode (major or minor).

**What's in the catalog:**
- 17 different genres (pop, lofi, rock, r&b, jazz, metal, classical, hip-hop, edm, blues, folk, country, reggae, ambient, synthwave, soul, indie pop)
- 15 different moods (happy, chill, intense, romantic, relaxed, moody, focused, confident, peaceful, angry, nostalgic, uplifting, dreamy, euphoric, sad)

**Limits:**
- Most genres and moods have only 1 song. If your favorite genre is "jazz," there is exactly one jazz song you can match.
- The catalog skews toward mid-energy songs (55% have energy ≤ 0.55). High-energy users have fewer strong matches.
- 70% of songs are in a major key, so minor-key preferences are at a structural disadvantage.
- The catalog was hand-crafted for this project — it does not represent real listening trends or demographics.

---

## 5. Strengths

The system works well when the user's genre and mood preferences are well-represented in the catalog.

- The **Chill Lofi** profile returns clearly appropriate results (quiet, slow, acoustic tracks) and separates cleanly from the high-energy profiles. Lofi has 3 songs, chill has 3 songs — enough variety to produce a real top-5 list.
- The **High-Energy Pop** profile returns Sunrise City and Gym Hero at the top, which is exactly what a pop/happy/energetic listener would expect. The mood and genre bonuses work as intended here.
- The **numeric proximity tier** degrades gracefully. When a user's genre is not in the catalog at all (the ghost-genre k-pop test), the system still returns musically coherent results by relying on energy, valence, and mood alone — no crashes, no empty results.
- The scoring explanation output (showing why each song earned its points) makes it easy to see whether a result makes sense. This transparency is something black-box systems like collaborative filters cannot offer.

---

## 6. Limitations and Bias

The most significant bias is **catalog density bias compounded by categorical label dominance**. Mood and genre are binary exact matches worth a combined 5.0 out of 11.0 possible points. This means users whose preferences match rare labels are structurally disadvantaged compared to users with common ones.

In the 20-song catalog, 15 out of 17 genres and 11 out of 15 moods have only one representative song. A "lofi/chill" user can earn the full mood+genre bonus from two songs (Midnight Coding and Library Rain). A "classical/peaceful" user can earn it from exactly one. This creates a filter bubble: the system keeps surfacing the same single song for minority-taste users because there is no competition.

The adversarial High-Energy-Sad profile showed this most clearly. Empty Glass Blues (the only "sad" song) ranked first despite having energy=0.38, far from the user's target of 0.92. Its 3.0-point mood bonus was simply too large to overcome. The algorithm is not broken — the catalog is just too thin.

A second bias is the **genre string lock**: genre matching is exact string equality. "Metal" does not match "rock." Iron Collapse (metal, intense, energy=0.97) ranked fourth for a rock/intense user because it earned zero genre points, even though most listeners would consider it a reasonable fit.

---

## 7. Evaluation

Six user profiles were tested — three standard and three adversarial — by running `python src/main.py` against the 20-song catalog and inspecting the ranked top-5 outputs with per-feature score breakdowns.

**Standard profiles:**
- **High-Energy Pop** (pop/happy, energy=0.88, valence=0.82) — returned Sunrise City and Gym Hero at the top, which matched intuition. Both songs earned mood+genre bonuses and had high energy and valence scores close to target.
- **Chill Lofi** (lofi/chill, energy=0.38, valence=0.58, acousticness=0.80) — returned Midnight Coding and Library Rain as clear top-2, both earning the full mood+genre match. The high acousticness weight helped filter out electronic/synth songs effectively.
- **Deep Intense Rock** (rock/intense, energy=0.91, valence=0.48, acousticness=0.10) — Storm Runner ranked first with a near-perfect energy match and genre+mood bonus. Surprisingly, Iron Collapse (metal, intense, energy=0.97) ranked fourth rather than second, because the genre string "metal" did not match "rock" and earned zero genre points — a binary matching failure.

**Adversarial profiles:**
- **High-Energy Sad** (blues/sad, energy=0.92) — the most revealing test. Empty Glass Blues ranked first despite having energy=0.38, the opposite of what the profile targets. Its 3.0-point mood match alone outweighed any energy penalty, because the maximum energy proximity score is only 2.0 points. This confirmed that when the catalog has only one song for a given mood, that song will always surface at the top regardless of how poorly its other attributes match.
- **Ghost Genre** (k-pop/happy, genre not in catalog) — with zero genre matches available, the ranking fell back entirely on mood and numeric features. Happy-mood pop songs surfaced first, which was a reasonable and graceful fallback. No errors or crashes occurred.
- **All Neutral** (ambient/relaxed, all numeric targets=0.50) — recommendations clustered tightly in score (spread of ~0.8 pts across top 5), since proximity scores for mid-range targets reward near-average songs equally. The ambient/relaxed genre+mood combination had no exact catalog match, so ranking was driven purely by numeric closeness to 0.5 across all features.

A **weight-shift experiment** was also run: energy weight was doubled (2.0 → 4.0) and genre weight was halved (2.0 → 1.0). Two results improved (Iron Collapse moved up one rank; the neutral profile spread out slightly), but the adversarial mood-dominance problem was unchanged. The experiment was reverted because it caused regressions in the standard profiles without fixing the root issue.

**What surprised me:** Iron Collapse ranking below lofi songs for a rock/intense user was the sharpest insight. A song that intuitively belongs in a hard-rock playlist lost to quiet acoustic tracks because the algorithm has no concept of genre relationships. "Metal" and "rock" are just different strings.

---

## 8. Ideas for Improvement

**1. Genre families instead of exact string matching.**
Group genres into families (e.g., rock, metal, punk → "hard rock family"). A song in the same family as the user's preference could earn partial credit (e.g., +1.0 instead of +2.0). This would fix the Iron Collapse problem and make the system much more musically aware.

**2. Expand the catalog with balanced coverage.**
The filter bubble problem is mostly a data problem. Adding 3–5 songs per genre and mood would immediately improve recommendations for minority-taste users. Even a catalog of 100 songs with intentional balance would make a big difference.

**3. Add a diversity rule to the ranking step.**
Right now the top-5 can include songs that are nearly identical to each other (same genre, same mood, very close audio features). A simple rule — like "no two consecutive results can share the same genre" — would make the output feel less repetitive and more like a real playlist.

---

## 9. Personal Reflection

**Biggest learning moment:** The Iron Collapse result. I had assumed that doubling the energy weight would fix the rock profile — if energy matters more, surely the high-energy metal song would rank higher. It didn't help much, because the problem was never the weights. It was that "metal" and "rock" are different strings and the algorithm has no idea they're related. That taught me that adding more math to a flawed representation does not fix the flaw. You have to fix the representation first.

**Using AI tools:** AI tools helped a lot with the scaffolding — generating the scoring formula structure, suggesting adversarial test cases I wouldn't have thought of, and explaining the difference between `.sort()` and `sorted()` clearly. But I had to double-check the output every time. In one case, the suggested main.py used old key names (`genre`, `mood`, `energy`) that didn't match the updated `UserProfile` dataclass (`favorite_genre`, `favorite_mood`, `target_energy`). The code looked correct but crashed immediately. The lesson: AI suggestions are a first draft, not a final answer. Reading the code before running it matters.

**What surprised me about simple algorithms:** The results actually feel like recommendations. When I ran the Chill Lofi profile, the top songs were genuinely calm and acoustic. When I ran High-Energy Pop, the output felt like a workout playlist. None of that required machine learning — just a few addition and subtraction operations. What makes it feel real is that the features (energy, valence, acousticness) are genuinely good proxies for musical vibe. The algorithm is simple; the feature engineering is doing most of the work.

**What I'd try next:** I'd implement genre families (partial credit for related genres) because that's the one fix that would immediately make the most profiles noticeably better. After that, I'd want to try a small collaborative filter on top — even something as simple as "users who liked this song also liked..." — to see how much it improves over pure content-based scoring. The two approaches seem complementary: content-based handles new users well; collaborative handles catalog gaps well.
