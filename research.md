# Research Notes — Music Recommender Simulation

This file documents every research topic investigated during the development of this project, in the order topics were explored. Each section records what was asked, what was found, and how the finding was applied to the code.

---

## 1. How Major Streaming Platforms Predict What You Will Like

### Question
How do real platforms like Spotify, YouTube Music, and Apple Music decide what to recommend? What data do they use, and what are the two main approaches?

### Findings

**Collaborative Filtering**
Learns from the behavior of millions of users — skips, replays, playlist additions, listen duration, and explicit ratings. The core idea: if you and another user have listened to many of the same songs, that user's next favorite is a candidate for your next recommendation. Netflix's famous prize competition was built around this idea. Spotify's "Discover Weekly" is primarily collaborative: it maps your listening history against a giant user-similarity graph and surfaces songs your closest musical "neighbors" love but you haven't heard yet.

Strength: discovers unexpected connections across genres and moods. Weakness: the "cold start" problem — a brand-new user with no history gets no useful signal. Also cannot explain recommendations in plain language.

**Content-Based Filtering**
Analyzes the audio and metadata attributes of songs directly — tempo, energy, loudness, danceability, key, mode, genre, mood. Spotify's Audio Features API exposes exactly these attributes. The system computes a similarity score between a song's attributes and a user's taste profile (derived from what they have already liked). Pandora's Music Genome Project is the most famous content-based system: human analysts tag every song on ~450 attributes.

Strength: works immediately for new users (no history needed). Fully explainable — every recommendation can be justified by specific attribute matches. Weakness: "filter bubble" risk — if you only receive songs similar to what you already like, you never discover music outside your established taste.

**How real platforms combine both**
Most production systems use a hybrid: collaborative filtering generates a large candidate pool, and content-based filtering re-ranks or filters that pool. YouTube adds reinforcement signals (watch time, like/dislike) on top. Apple Music layers in editorial curation. This simulation focuses purely on the content-based tier.

**Main data types used by streaming platforms**
- Audio signal features: energy, tempo, loudness, spectral centroid, MFCC coefficients
- Metadata: genre, artist, release year, explicit flag
- Derived/tagged: mood, danceability, acousticness, instrumentalness, liveness, speechiness, valence
- Behavioral: play count, skip rate, save rate, playlist adds, shares

### Applied to this project
This research set the scope: the simulation is content-based only, using audio feature proximity scoring rather than user-history modeling. All features in `data/songs.csv` are drawn from the types real platforms measure.

---

## 2. Feature Selection — Which Song Attributes Best Capture Musical "Vibe"

### Question
Given the initial `data/songs.csv` (10 songs, 10 columns), which features most effectively separate different listening contexts? Do the proposed features match personal intuition about musical vibe?

### Findings

**Most discriminating features for vibe**

| Feature | Why it matters | Catalog spread |
|---|---|---|
| Energy | Single strongest axis — separates workout from sleep music entirely | 0.22 – 0.97 (widest) |
| Valence | Emotional brightness — separates happy from sad at the same energy level | 0.20 – 0.88 |
| Acousticness | Instrument texture — separates organic/warm from electronic/cold | 0.02 – 0.98 |
| Genre | Human-curated taste category — captures cultural context no numeric feature can | Categorical |
| Mood | Explicit listening intent — the label a listener reaches for ("I want chill music") | Categorical |
| Tempo (BPM) | Physical pacing — matters for exercise and dance contexts | 60 – 168 |
| Mode (major/minor) | Emotional tone — minor = melancholic, major = uplifting | Binary |
| Instrumentalness | Vocal vs. instrumental preference — highly personal | 0.01 – 0.97 |
| Loudness | Separates metal from rock at similar energy levels | 0.18 – 0.96 |

**Features collected but not directly scored**
- `danceability` — highly correlated with energy+tempo; adds little independent signal in a small catalog
- `speechiness` — valuable for separating rap/hip-hop from instrumental genres; not scored in v1
- `liveness` — useful for live album vs. studio preference; not scored in v1

**Personal intuition check**
Energy + mood together capture what a listener means when they say "I need something to study to" (low energy, focused mood) vs. "I need pump-up music" (high energy, intense mood). Valence refines within a mood — a "chill" song can feel optimistic (high valence) or melancholic (low valence). Acousticness captures the warmth/texture axis that separates a lofi beat from an EDM track even at similar energy.

### Applied to this project
The initial 10 features were expanded to 15 in `data/songs.csv` by adding `danceability`, `acousticness`, `instrumentalness`, `speechiness`, `liveness`, `loudness_norm`, and `mode`. The scoring algorithm uses energy, valence, acousticness, instrumentalness, and loudness_norm as proximity-scored dimensions.

---

## 3. Algorithm Recipe Design — Scoring Rules and Weight Strategy

### Question
How should a simple math-based scoring rule work? Should genre be worth more than mood? Why do we need both a Scoring Rule and a Ranking Rule?

### Findings

**Why both rules are needed**
- The *Scoring Rule* turns a single (user, song) pair into a number. It answers: "how good is this song for this user?"
- The *Ranking Rule* uses those numbers to build a sorted list. It answers: "which of all these songs should come first?" These are separate concerns. A scoring rule that assigns equal scores to many songs is useless without a tiebreak in the ranking rule. A ranking rule applied to poorly designed scores still produces poor results.

**Mood vs. Genre — which deserves more weight?**
Mood deserves more because it encodes the listener's *current intent*, not just their long-term taste identity. A rock fan studying at 2am is not looking for rock — they are looking for something quiet and focused. Genre is a taste identity signal; mood is a context signal. Context is stronger in the moment. Assigned: Mood +3.0, Genre +2.0.

**Proximity formula for numeric features**
The formula `points = max_weight × (1 − |song_value − target_value|)` was chosen over alternatives because:
- It awards partial credit (not just full-or-nothing)
- A perfect match always earns `max_weight`
- A maximally opposite value earns exactly 0 (never negative for primary features)
- It is linear and easy to reason about

**Final point budget (original, max 11.0)**

| Component | Max points | Rationale |
|---|---|---|
| Mood match | +3.0 | Strongest listening context signal |
| Genre match | +2.0 | Taste identity |
| Energy proximity | max +2.0 | Widest catalog spread → most discriminating |
| Valence proximity | max +1.5 | Emotional brightness within mood |
| Acousticness proximity | max +1.0 | Instrument texture preference |
| Mode match | +0.5 | Minor/major emotional alignment |
| Instrumentalness proximity | max +0.5 | Vocal vs. instrumental feel |
| Loudness proximity | max +0.5 | Intensity texture |

**Ranking rule**
Sort by total score descending. Tiebreak: `tempo_bpm` proximity if the user profile specifies a `target_bpm`.

### Applied to this project
This recipe was implemented in `score_song()` in `src/recommender.py`. The tiebreak was implemented in `recommend_songs()`.

---

## 4. Dataset Expansion — Adding Songs and Numeric Features

### Question
What 5–10 additional songs should be added to the catalog? What new numeric features (danceability, acousticness, etc.) add meaningful signal?

### Findings

**New songs added (10 → 20)**
Five new features were added to complement the original set: `danceability`, `acousticness`, `instrumentalness`, `speechiness`, `liveness`. These required adding a `loudness_norm` column and a `mode` column (major = 1, minor = 0). Ten new songs were added spanning genres not previously represented: `r&b`, `hip-hop`, `metal`, `classical`, `country`, `reggae`, `blues`, `edm`, `folk`, `soul`.

**Catalog distribution after expansion**
- 17 unique genres — but 15 of them have only 1 song
- 15 unique moods — but 11 of them have only 1 song
- Energy distribution: 55% of songs have energy ≤ 0.55 (skews low-mid)
- Mode: 70% major, 30% minor

This distribution was documented as a known bias because it structurally disadvantages users whose preferred genre or mood is underrepresented.

### Applied to this project
`data/songs.csv` was expanded from 10 to 20 rows and from 10 to 15 columns. `load_songs()` in `src/recommender.py` was updated to cast numeric columns to `float` or `int`.

---

## 5. User Profile Design and Adversarial Test Cases

### Question
How should a taste profile be structured? Can a single profile differentiate "intense rock" from "chill lofi"? What adversarial / edge-case profiles stress-test the system?

### Findings

**Profile structure**
A `UserProfile` needs both categorical preferences (genre, mood, mode) and numeric targets (energy, valence, acousticness, etc.) to fully specify a listening context. A profile with only genre and mood cannot distinguish a slow, acoustic folk song from an electronic ambient track — both might be labeled "chill." The numeric dimensions are what make the differentiation possible.

**Differentiation test — Intense Rock vs. Chill Lofi**
These two profiles sit at opposite extremes of nearly every dimension:

| Preference | Chill Lofi | Intense Rock |
|---|---|---|
| Energy target | 0.38 | 0.91 |
| Acousticness target | 0.80 | 0.10 |
| Mood | chill | intense |
| Genre | lofi | rock |
| Mode | minor | minor |

The system cleanly separates them: no song appears in both top-5 lists.

**Three adversarial profiles designed to expose weaknesses**

1. **High-Energy Sad** (`energy=0.92`, `mood=sad`): Contradictory signals — high energy pulls toward intense tracks but sad mood pulls toward slow melancholic ones. Exposes the categorical dominance problem: the only "sad" song in the catalog wins regardless of its energy=0.38.

2. **Ghost Genre** (`genre="k-pop"`): Genre not present in catalog at all. Tests graceful fallback — the system should still rank by mood + numeric features and not crash or return an empty list.

3. **All Neutral** (`all numeric targets = 0.50`): Tests whether scores cluster so tightly the ranking becomes arbitrary. Revealed that the top-5 scores at ranks 3–5 were within 0.09 of each other.

### Applied to this project
Three standard profiles and three adversarial profiles were defined in `src/main.py`. All six are run on every execution.

---

## 6. Data Flow Architecture and Mermaid.js Visualization

### Question
What is the full data flow from CSV file to ranked output? How can this be visualized as a flowchart?

### Findings

The data flow has four stages:
1. `load_songs(csv_path)` — reads CSV, casts numeric types, returns `List[Dict]`
2. Per-song loop — for each of 20 songs, calls `score_song(user_prefs, song)`
3. `score_song()` — applies categorical + proximity rules, returns `(score, reasons)`
4. `recommend_songs()` — sorts all scored songs, slices top-k

A Mermaid.js flowchart was generated to represent this and embedded in `README.md`. Mermaid supports flowcharts, sequence diagrams, and entity-relationship diagrams using a Markdown-like syntax that renders in GitHub.

### Applied to this project
The flowchart is embedded in the "How The System Works" section of `README.md`.

---

## 7. Filter Bubbles and Catalog Bias Analysis

### Question
What biases exist in the current scoring logic? What patterns emerge when examining the catalog distribution against the scoring formula?

### Findings

**Bias 1 — Catalog density bias compounded by categorical label dominance**
Mood (+3.0) and genre (+2.0) together account for 45% of the maximum score (5.0 of 11.0). Because 15 of 17 genres and 11 of 15 moods have only 1 song, users with rare preferences can earn the full categorical bonus from at most one song. The filter bubble is not a flaw in the algorithm — it is a catalog scarcity problem amplified by heavy categorical weighting.

**Bias 2 — Genre single-string lock**
Genre is matched as a case-sensitive exact string. `"metal"` scores zero against a `"rock"` preference even though the genres share nearly all audio attributes. Iron Collapse (metal, angry, energy=0.97) ranked fourth for the Deep Intense Rock profile — below two lofi songs — because it earned zero genre points. No amount of weight adjustment can fix this without changing the representation.

**Bias 3 — Energy distribution skew**
55% of the catalog has energy ≤ 0.55. Users targeting energy > 0.80 have only 5 songs capable of earning near-perfect energy proximity scores. Their top-5 will always contain songs that "miss" on energy.

**Bias 4 — Mode imbalance**
70% major / 30% minor means a minor-mode user earns the +0.5 mode bonus on only 6 songs vs. 14 for a major-mode user.

**Demonstrated by adversarial profile**
High-Energy-Sad: `target_energy = 0.92`, `mood = "sad"`. Empty Glass Blues (energy=0.38, the only sad song) ranked #1. Its 3.0 mood + 2.0 genre = 5.0 pts could not be overcome by any energy penalty because the maximum energy contribution is 2.0 pts. The math makes it structurally impossible for any other song to beat a dual categorical match.

### Applied to this project
This analysis was documented in `model_card.md` section 6 (Limitations and Bias) and in `reflection.md`.

---

## 8. Weight Sensitivity Analysis — Energy ×2, Genre ÷2

### Question
If energy is doubled (max +4.0) and genre is halved (+1.0), does the system produce better results for the cases where genre string-lock was identified as the problem?

### Findings

**Changes tested**

| Feature | Original | Experimental |
|---|---|---|
| Genre match | +2.0 | +1.0 |
| Energy proximity | max +2.0 | max +4.0 |
| Max total | 11.0 | 12.0 |

**Results across 6 profiles**
- Deep Intense Rock: Iron Collapse rose from #4 → #3. Genuine improvement.
- All Neutral: mid-energy songs rose; energy=0.28 ambient song fell. Improvement.
- High-Energy Sad: Empty Glass Blues still #1. No change — mood dominance persists.
- Other three profiles: order changed slightly but quality neither better nor worse.

**Verdict: Reverted.**
The experiment produced two genuine improvements but exposed that the root cause of the adversarial case is not energy under-weighting — it is that a single song holds a monopoly on the "sad" mood label. Doubling energy cannot overcome a 5.0-point categorical advantage when no competing sad song exists. The correct fix is partial genre credit for related genres, not a weight shift.

### Applied to this project
Experiment documented in `README.md` "Experiments You Tried" section. Changes were reverted to the original weights.

---

## 9. Extended Attributes Research — New Dataset Features

### Question
What 5+ complex attributes would meaningfully improve recommendation quality beyond the original 15 columns?

### Findings

Five new attributes were identified and added:

**1. Popularity (0–100)**
Measures how mainstream a song is. A user who prefers niche/indie music (low target_popularity) should be penalized when a mainstream hit is surfaced, and vice versa. Scored as proximity: `1.0 × (1 − |song_popularity/100 − user_target_popularity|)`.

**2. Release Decade (1970–2020)**
Era preference is a real dimension of taste — some listeners specifically want 90s nostalgia music; others want only current releases. Scored with graduated decay: exact decade match = +1.5, one decade off = +0.75, two decades = +0.25, further = 0. This rewards era alignment without harshly penalizing adjacent eras.

**3. Mood Tags (comma-separated detailed labels)**
Finer-grained emotional descriptors beyond the single `mood` label. Examples: `"nostalgic,warm"`, `"aggressive,empowering"`, `"dreamy,contemplative"`. Scored at +0.5 per matching tag, capped at +1.5 (3 tags). This provides partial credit for songs that share some but not all emotional dimensions with the user's preference.

**4. Context (listening situation)**
Primary use case label: `workout`, `study`, `party`, `commute`, `chill`, `focus`. A binary match adds +1.0. This captures the practical situation a listener is in — two songs can share the same mood and genre but serve completely different activities.

**5. Explicit (0/1)**
A binary filter. If the user sets `allow_explicit=0` and the song is explicit, a −1.0 penalty is applied. This is not a preference dimension but a hard constraint expressed as a score penalty.

**New maximum score: 16.0 points** (up from 11.0)

### Applied to this project
All 5 columns were added to `data/songs.csv`. `UserProfile` dataclass was extended with 5 new fields (with defaults for backward compatibility). `score_song()` was extended with 5 new scoring blocks. All 6 profile dicts in `main.py` and all 3 profile dicts in `recommender.py` were updated with the new fields.

---

## 10. Software Design Patterns — Strategy Pattern for Ranking

### Question
How can the code be structured so a user can switch between different ranking modes (Genre-First, Mood-First, Energy-Focused) without modifying the core scoring logic? What design pattern fits this problem?

### Findings

**The Strategy Pattern**
A behavioral design pattern where a family of algorithms is encapsulated behind a common interface, making them interchangeable. The caller does not need to know which concrete algorithm is in use — it just calls `strategy.rank(...)`.

Structure:
- `RankingStrategy` (abstract base class) — defines the interface: `rank(songs, user_prefs, k)`
- Concrete strategies — each implements `rank()` differently
- `recommend_songs()` — accepts a `strategy` parameter; defaults to `BalancedStrategy()`
- `main.py` — sets `ACTIVE_STRATEGY = SomeStrategy()` in one place; all profiles use it

Why this pattern fits here:
- All ranking strategies share the same inputs (`songs`, `user_prefs`, `k`) and output (`List[(song, score, explanation)]`)
- Adding a new strategy requires writing one new class, not touching existing code
- Strategies can wrap other strategies (the `DiversityPenaltyStrategy` wraps any base strategy)

**Four strategies implemented**

| Strategy | How it ranks |
|---|---|
| `BalancedStrategy` | Pure total score descending. Default behavior. |
| `GenreFirstStrategy` | Genre-matched songs always appear before genre-mismatched songs. Within each group, sorted by score. |
| `MoodFirstStrategy` | Mood-matched songs always appear first. Within each group, sorted by score. |
| `EnergyFocusedStrategy` | Applies a 3× extra multiplier on the energy proximity component on top of the base score. |

**Divergence demonstration**
For a `pop/intense` user profile:
- `GenreFirstStrategy` → rank #2 is Sunrise City (pop/happy) — genre wins, mood ignored for ordering
- `MoodFirstStrategy` → rank #2 is Storm Runner (rock/intense) — mood wins, genre ignored for ordering

### Applied to this project
All four strategies implemented as classes in `src/recommender.py`. `recommend_songs()` accepts `strategy=` parameter. `main.py` exposes `ACTIVE_STRATEGY` as a single-line switch.

---

## 11. Diversity in Recommendation Systems — Diversity Penalty Research

### Question
How do recommender systems prevent returning too many results from the same artist or genre? What algorithmic approaches exist?

### Findings

**The repetition problem**
Without a diversity mechanism, content-based systems naturally converge: if three lofi songs each score 10.5, 10.3, and 10.1, all three appear in the top-5. The user receives a playlist of nearly identical songs. Real platforms (Spotify, YouTube) apply explicit diversity rules in their final ranking pass.

**Common approaches**

1. **Hard constraints**: "No more than N songs from the same artist per playlist." Simple but binary — a great song gets blocked even if it's the #2 best match overall.

2. **Greedy re-ranking with soft penalties**: Score all songs first, then build the result list one pick at a time. When a song is added, future candidates from the same artist or genre have their scores reduced by a penalty. This is softer than a hard block — a repeat-artist song can still appear if it is far enough ahead in score.

3. **Maximum Marginal Relevance (MMR)**: A formal algorithm that balances relevance (score against the user profile) and diversity (distance from songs already selected). Used in document retrieval and adapted for music.

4. **Intent-aware diversification**: Cluster songs by attribute (genre, mood, energy range) and ensure each cluster is represented in the top-k. More complex but produces more balanced playlists.

**Chosen approach: Greedy re-ranking with soft penalties**
Selected because it:
- Is easy to understand and debug
- Wraps any existing strategy without modifying scoring
- Shows the penalty in the output explanation, making it transparent
- Allows the penalty magnitude to be tuned

**Penalty values chosen**
- Artist repeat: −2.0 (significant — same artist twice in a playlist is clearly unwanted)
- Genre repeat: −1.0 (moderate — same genre twice is less bad, sometimes intentional)

### Applied to this project
`DiversityPenaltyStrategy` implemented in `src/recommender.py`. It wraps any base strategy: `DiversityPenaltyStrategy(base_strategy=EnergyFocusedStrategy(), artist_penalty=3.0)`. The penalty notes appear in the scoring breakdown output. `main.py` defaults to `DiversityPenaltyStrategy()`.

**Observed effect (Chill Lofi profile)**
Without diversity: top-3 = Midnight Coding (lofi/LoRoom), Library Rain (lofi/Paper Lanterns), Focus Flow (lofi/LoRoom)
With diversity: Focus Flow drops to #4 because it accrues −2.0 (artist repeat: LoRoom) + −1.0 (genre repeat: lofi) = −3.0 adjusted penalty, allowing Spacewalk Thoughts (ambient/Orbit Bloom) to take #3.

---

## 12. Output Formatting — tabulate Library Research

### Question
How can terminal output be reformatted from plain print statements into readable tables? How should the scoring reasons be incorporated into a tabular format?

### Findings

**tabulate library**
`tabulate` is a Python library for formatting tabular data as ASCII or Unicode tables. Key parameters used:
- `tablefmt="grid"` — ASCII box-drawing using `+`, `-`, `|` (safe on all terminals)
- `tablefmt="simple"` — minimal column separators, no outer border (cleaner for breakdowns)
- `colalign=("left", "right")` — aligns label left, points right
- `disable_numparse=True` — prevents tabulate from stripping `+` signs by converting strings like `"+3.00"` to float `3.0`

**Two-table output structure designed**
1. **Summary table** — compact, one row per song: rank, title, artist, genre, mood, score. Gives a quick overview without scrolling.
2. **Scoring breakdown** — one `simple` table per song: component/detail label vs. points. Shows every reason with right-aligned points.

**Parsing reason strings**
A `_parse_reason(reason)` helper splits each reason string into `(label, points)` using the regex `r"^(.*?):\s*([+-]\d+\.\d+)$"`. Bracket annotations from strategy wrappers (`[Diversity penalty: ...]`, `[Energy Boost: +X]`) are handled as a special case by stripping the outer brackets and splitting on the first colon.

**Windows encoding issue encountered**
`tablefmt="rounded_outline"` uses Unicode box-drawing characters (`╭`, `╰`, `─`) that are unrenderable on Windows terminals using the `cp1252` codec. Replaced with `"grid"` (pure ASCII) to ensure cross-platform compatibility.

### Applied to this project
`print_profile()` and `print_recommendations()` in `src/main.py` were rewritten to use tabulate. `_parse_reason()` was added as a private helper. The `SUBDIVISION` constant was removed; `DIVIDER` width was updated to 72 characters to match the wider table format.
