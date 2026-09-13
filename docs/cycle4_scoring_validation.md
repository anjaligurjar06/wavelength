# Compatibility Score Validation & Weight Sanity Findings

## 1. Objective

The objective of D10–D11 was to validate the Compatibility Engine using real/test Spotify user accounts and check whether the generated compatibility score behaves as expected.

The validation focused on:

* Comparing the music profiles of two Spotify accounts.
* Manually verifying the actual overlap between their artists and tracks.
* Comparing the manually verified overlap with the Compatibility Engine output.
* Checking that artist similarity contributes correctly to the final score.
* Checking the behavior when genre information is unavailable.
* Verifying that missing genre data does not incorrectly create similarity.
* Documenting the weight behavior and findings in D12.

For this validation, two Spotify accounts were used.

---

## 2. Test Accounts

The validation was performed using two real/test Spotify profiles:

| Account        | User ID                                | Time Window |
| -------------- | -------------------------------------- | ----------- |
| Simran Dhindsa | `355ce34a-5153-47e0-b241-05c42b6280e4` | 6 months    |
| Sherlin        | `967d0652-3ed4-4b26-95df-22d7091b9cb6` | 6 months    |

Both profiles were successfully synchronized with the music-ingestion service.

The database showed:

### Simran Dhindsa

* Artists = 20
* Tracks = 20
* Recently Played = 20

### Sherlin

* Artists = 16
* Tracks = 20
* Recently Played = 3

---

## 3. Spotify Data Synchronization

The Spotify data was synchronized using the `/music/sync` endpoint.

The synchronization successfully stored the profiles in the `user_music_profiles` table.

The resulting database state was:

| user_id                                | time_window | is_stale |
| -------------------------------------- | ----------- | -------- |
| `355ce34a-5153-47e0-b241-05c42b6280e4` | `6m`        | `false`  |
| `967d0652-3ed4-4b26-95df-22d7091b9cb6` | `6m`        | `false`  |

This confirms that both profiles had successfully completed synchronization.

---

## 4. Profile Coverage

The synchronized profiles contained the following data:

### Simran Dhindsa

* Top artists: 20
* Top tracks: 20
* Recently played: 20

### Sherlin

* Top artists: 16
* Top tracks: 20
* Recently played: 3

Therefore, artist and track data were available for both accounts.

However, Spotify did not provide genre information for the artists in these profiles.

The stored genre data was:

```json
{
  "genres": []
}
```

for both users.

---

## 5. Manual Artist Overlap Verification

The top artist lists were manually inspected before evaluating the Compatibility Engine result.

### Simran's Artists

The manually inspected list included:

* Karan Aujla
* Amrinder Gill
* Diljit Dosanjh
* Cheema Y
* Harkirat Sangha
* Pritam
* Arjan Dhillon
* Tarsem Jassar
* ...

### Sherlin's Artists

The manually inspected list included:

* Arijit Singh
* Pritam
* Talwiinder
* KALAM INK
* Anuv Jain
* Ankit Tiwari
* Sachin-Jigar
* JENNIE
* ...

The common artist identified manually was:

**Pritam**

Therefore:

```text
Shared artists = 1
```

---

## 6. Artist Similarity

The Compatibility Engine uses Jaccard similarity for artist overlap.

The formula is:

```text
Jaccard Similarity =
Number of common artists
------------------------
Number of unique artists in both profiles
```

For these profiles:

```text
Common artists = 1
Total unique artists = 35
```

Therefore:

```text
Artist Jaccard = 1 / 35
               = 0.0286
```

The engine produced:

```text
Artist Jaccard : 0.0286
Artist %       : 2.86%
```

This matches the manually verified overlap.

Therefore, the artist similarity calculation is behaving correctly for this test.

---

## 7. Track Overlap Verification

The top-track lists were also compared.

The manual verification showed:

```text
Shared tracks = 0
```

The Compatibility Engine returned:

```text
Track Jaccard : 0.0000
Track %       : 0.00%
```

Therefore, the engine correctly reported no track similarity.

Importantly, the absence of shared tracks did not artificially increase the compatibility score.

---

## 8. Genre Similarity

Genre information was checked for both users.

The database contained:

```json
{
  "genres": []
}
```

for both profiles.

Therefore, there was no usable genre information available for the Compatibility Engine.

The engine returned:

```text
Genre cosine = 0.0000
```

This is expected because there are no genre vectors to compare.

The engine therefore did not create artificial genre similarity.

---

## 9. Genre Coverage

The Compatibility Engine calculates genre coverage based on the fraction of artists for which genre metadata is available.

For both users:

```text
Simran genre coverage = 0.0000
Sherlin genre coverage = 0.0000
```

Therefore:

```text
coverage_a = 0.0
coverage_b = 0.0
```

The pair coverage is:

```text
min(0.0, 0.0) = 0.0
```

This indicates that genre information is completely unavailable for this pair.

---

## 10. Adaptive Weight Behavior

The Compatibility Engine uses adaptive weights to handle missing genre information.

The normal MVP weights are:

```text
Artist weight = 0.60
Genre weight  = 0.40
```

However, when genre coverage is missing, the genre contribution is reduced.

The adaptive weighting logic uses the minimum genre coverage of the two users.

For this pair:

```text
coverage_a = 0.0
coverage_b = 0.0

pair_coverage = min(0.0, 0.0)
              = 0.0
```

Therefore:

```text
Genre weight = 0.40 × 0.0
             = 0.00

Artist weight = 1.00 - 0.00
              = 1.00
```

The actual result was:

```text
Artist weight: 1.00
Genre weight : 0.00
```

This is the expected behavior.

Since there is no reliable genre data, the engine relies entirely on artist similarity rather than treating missing genre data as similarity.

---

## 11. Final Compatibility Score

The adaptive composite score is calculated using:

```text
Final Score =
Artist Weight × Artist Similarity
+
Genre Weight × Genre Similarity
```

For this test:

```text
Artist weight = 1.00
Artist similarity = 0.0286

Genre weight = 0.00
Genre similarity = 0.0000
```

Therefore:

```text
Final Score =
1.00 × 0.0286
+
0.00 × 0.0000

= 0.0286
```

The Compatibility Engine produced:

```text
Final Compatibility Score = 0.0286
Score = 2.86 / 100
```

---

## 12. Manual vs Engine Comparison

| Metric                   |     Manual Verification | Engine Result |
| ------------------------ | ----------------------: | ------------: |
| Shared artists           |                       1 |             1 |
| Artist Jaccard           |                  0.0286 |        0.0286 |
| Artist percentage        |                   2.86% |         2.86% |
| Shared tracks            |                       0 |             0 |
| Track Jaccard            |                  0.0000 |        0.0000 |
| Genre data               |                   Empty |         Empty |
| Genre similarity         |           Not available |        0.0000 |
| Genre coverage – Simran  |                     0.0 |           0.0 |
| Genre coverage – Sherlin |                     0.0 |           0.0 |
| Artist weight            |           Expected 1.00 |          1.00 |
| Genre weight             |           Expected 0.00 |          0.00 |
| Final score              |      Expected low score |        0.0286 |
| Final percentage         | Expected low similarity |      2.86/100 |

The manually verified overlap is consistent with the Compatibility Engine output.

---

## 13. Weight Sanity Testing

In addition to real Spotify data validation, the scoring functions were tested directly to verify the intended weight behavior.

The Compatibility Engine currently uses:

```text
ARTIST_WEIGHT = 0.60
GENRE_WEIGHT = 0.40
```

### Artist-only Test

A test was performed where only artist similarity was present:

```text
artist_overlap = 1.0
genre_similarity = 0.0
```

The expected score was:

```text
0.60 × 1.0 + 0.40 × 0.0
= 0.60
```

The test confirmed:

```text
Artist-only score = 0.60
```

### Genre-only Test

A second test used only genre similarity:

```text
artist_overlap = 0.0
genre_similarity = 1.0
```

The expected score was:

```text
0.60 × 0.0 + 0.40 × 1.0
= 0.40
```

The test confirmed:

```text
Genre-only score = 0.40
```

Therefore:

```text
Artist-only score > Genre-only score
```

This confirms that the current scoring system gives greater importance to artist similarity.

---

## 14. Adaptive Weight Testing

The adaptive scoring tests also verified behavior when genre coverage is incomplete.

### Full Genre Coverage

For full genre coverage:

```text
coverage_a = 1.0
coverage_b = 1.0
```

the engine retains:

```text
Artist weight = 0.60
Genre weight = 0.40
```

### Low Genre Coverage

For low genre coverage, the genre weight is reduced and the artist weight increases.

For example:

```text
coverage_a = 0.25
coverage_b = 1.0
```

The pair coverage becomes:

```text
min(0.25, 1.0) = 0.25
```

The resulting tested weights were:

```text
Artist weight = 0.90
Genre weight = 0.10
```

This confirms that the engine adapts its weights based on available genre metadata.

---

## 15. Manual Genre Fallback

The engine contains a manual genre fallback mechanism.

The default fallback threshold is:

```text
0.30
```

The fallback is triggered when the pair's minimum genre coverage is below this threshold.

For the tested accounts:

```text
Simran coverage = 0.00
Sherlin coverage = 0.00
```

Therefore:

```text
pair coverage = 0.00
```

Since:

```text
0.00 < 0.30
```

the engine correctly reported:

```text
Manual genre fallback:
Needed = True
```

This is expected because there is insufficient genre metadata to produce a reliable genre-based similarity score.

---

## 16. Weight Sanity Findings

The validation produced the following findings.

### Finding 1 — Artist overlap is correctly calculated

The two tested users had one common artist:

```text
Pritam
```

The Compatibility Engine calculated:

```text
Jaccard = 0.0286
```

which matches the manually calculated value.

**Result: PASS**

---

### Finding 2 — No track overlap produces no track similarity

The users had no common tracks.

The engine returned:

```text
Track Jaccard = 0.0000
```

Therefore, no artificial track similarity was introduced.

**Result: PASS**

---

### Finding 3 — Missing genre data does not create similarity

Both profiles contained empty genre data.

The engine returned:

```text
Genre cosine = 0.0000
```

Therefore, missing genre information does not incorrectly increase the compatibility score.

**Result: PASS**

---

### Finding 4 — Adaptive weighting handles missing genres

Because both users had zero genre coverage:

```text
Artist weight = 1.00
Genre weight = 0.00
```

The engine correctly shifted the scoring weight toward the available artist data.

**Result: PASS**

---

### Finding 5 — Artist similarity has higher default importance

The scoring tests confirmed:

```text
Artist-only score = 0.60
Genre-only score = 0.40
```

Therefore, the current MVP weighting gives more importance to artists.

**Result: PASS**

---

### Finding 6 — Manual genre fallback is correctly triggered

Because genre coverage was below the configured threshold:

```text
Fallback = True
```

This indicates that the engine correctly detects insufficient genre information.

**Result: PASS**

---

## 17. Final Validation Result

The final real-account result was:

```text
==================================================
Simran <-> Sherlin
==================================================

Artists:
Simran = 20
Sherlin = 16

Tracks:
Simran = 20
Sherlin = 20

Shared artists:
Pritam

Artist Jaccard:
0.0286

Shared tracks:
None

Track Jaccard:
0.0000

Genre similarity:
0.0000

Genre coverage:
Simran = 0.0000
Sherlin = 0.0000

Adaptive weights:
Artist = 1.00
Genre  = 0.00

Final compatibility:
0.0286

Final compatibility percentage:
2.86 / 100

Manual genre fallback:
True
```

---

## 18. Conclusion

The Compatibility Engine successfully passed the initial real-account validation using two Spotify profiles.

The manually verified artist overlap matched the calculated Jaccard similarity. The engine also correctly returned zero similarity when there were no shared tracks and no usable genre metadata.

The adaptive weighting mechanism behaved as expected by shifting the entire score toward artist similarity when genre coverage was unavailable. The weight tests also confirmed that artist similarity has a stronger default contribution than genre similarity.

The validation therefore indicates that the current scoring logic is behaving consistently with the intended MVP design.

However, the current test also highlights an important limitation: Spotify genre metadata was empty for both tested accounts, so genre-based scoring could not be meaningfully validated using these accounts. The manual genre fallback correctly identified this limitation.

---

