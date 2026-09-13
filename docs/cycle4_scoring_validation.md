\# Cycle 4 — Compatibility Scoring Validation



\## Objective



Validate the compatibility scoring logic and check whether the artist and

genre weights behave as expected.



The Cycle 4 ML1 task is to validate scoring against real/test Spotify

accounts with manually verified expected overlap and to perform sanity

checks on the scoring weights.



\## Scoring Model



The MVP compatibility score combines two components:



\- Artist overlap: 60%

\- Genre similarity: 40%



Artist overlap is calculated using Jaccard similarity.



Genre similarity is calculated using cosine similarity.



The final compatibility score is calculated as:



&#x20;   score = 0.60 × artist\_overlap + 0.40 × genre\_similarity



The score is represented on a 0–1 scale by the scoring engine and can be

converted to a 0–100 compatibility score by the service/API layer.



\## Controlled Weight Sanity Checks



Controlled tests were performed to verify that the 60/40 weighting behaves

as intended.



\### Test 1 — Artist similarity only



Input:



\- Artist overlap = 1.0

\- Genre similarity = 0.0



Calculation:



&#x20;   0.60 × 1.0 + 0.40 × 0.0 = 0.60



Result:



&#x20;   Artist-only score = 0.60



\### Test 2 — Genre similarity only



Input:



\- Artist overlap = 0.0

\- Genre similarity = 1.0



Calculation:



&#x20;   0.60 × 0.0 + 0.40 × 1.0 = 0.40



Result:



&#x20;   Genre-only score = 0.40



\### Test 3 — Both components at maximum



Input:



\- Artist overlap = 1.0

\- Genre similarity = 1.0



Calculation:



&#x20;   0.60 × 1.0 + 0.40 × 1.0 = 1.00



Result:



&#x20;   Maximum score = 1.00



\### Controlled Weight Finding



The results confirm that artist overlap has a larger influence on the final

compatibility score than genre similarity.



A completely matching artist profile contributes 0.60 to the score, while a

completely matching genre profile contributes 0.40.



This matches the intended 60% artist and 40% genre weighting.



\## Adaptive Weight Sanity Checks



The scoring engine also adjusts the weights when genre metadata is

incomplete.



The adaptive weighting uses the lower genre coverage between the two users

as the pair coverage.



\### Test 1 — Full genre coverage



Input:



\- User A genre coverage = 1.0

\- User B genre coverage = 1.0



Result:



&#x20;   Artist weight = 0.60

&#x20;   Genre weight = 0.40



This preserves the normal 60/40 weighting.



\### Test 2 — No genre coverage



Input:



\- User A genre coverage = 0.0

\- User B genre coverage = 0.0



Result:



&#x20;   Artist weight = 1.00

&#x20;   Genre weight = 0.00



This prevents unavailable genre information from reducing the score.



\### Test 3 — 50% genre coverage



Input:



\- User A genre coverage = 0.5

\- User B genre coverage = 0.5



Result:



&#x20;   Artist weight = 0.80

&#x20;   Genre weight = 0.20



The genre contribution is reduced because only half of the genre metadata is

available.



\### Adaptive Weight Finding



The adaptive weighting behaves as intended.



When genre information is incomplete, the system reduces the contribution of

genre similarity and shifts the weight toward artist overlap. This prevents

missing genre metadata from having an unnecessarily large effect on the

compatibility score.



\## Automated Test Validation



The compatibility-engine automated tests were executed successfully.



\### Scoring tests



&#x20;   21 passed



\### Service tests



&#x20;   6 passed



\### Total compatibility-engine tests



&#x20;   27 passed



The tests cover the scoring calculations, score breakdown, recomputation,

stored scores, and service behavior.



\## Real Spotify Account Validation



The Cycle 4 requirement includes validation using real/test Spotify accounts

with manually verified expected overlap.



Two Spotify test accounts are currently available:



\- User 1: Simran Dhindsa

\- User 2: Muskan Katoch



Both users are present in the Wavelength PostgreSQL database and both have

Spotify access and refresh tokens stored.



\### Current Real-Data Status



Real Spotify account validation is currently pending because the

`POST /music/sync` endpoint is returning an `Internal Server Error`.



Therefore, real Spotify profile data has not yet been successfully populated

through the current ingestion endpoint for this validation.



No real-account score comparison is being claimed until the Spotify data is

successfully available in the database.



\## Manual Validation Table



The following table will be completed once the Spotify profiles are available

from the database.



| User Pair | Shared Artists | Artist Jaccard | Genre Similarity | Expected Score | API Score | Difference |

|-----------|----------------|----------------|------------------|----------------|----------|------------|

| Simran / Muskan | TBD | TBD | TBD | TBD | TBD | TBD |



Expected score will be calculated manually using:



&#x20;   Expected score =

&#x20;       0.60 × Artist Jaccard

&#x20;       + 0.40 × Genre Similarity



The manually calculated score will then be compared with the score returned by

the compatibility service/API.



\## D10–D11 Validation Status



\### D10 — Cross-validation of scoring



Controlled scoring and weight behavior have been successfully validated.



Real Spotify account cross-validation remains pending because the current

music ingestion endpoint is returning an Internal Server Error.



\### D11 — Real/test account comparison



Two real/test Spotify accounts have been prepared for comparison:



\- Simran Dhindsa

\- Muskan Katoch



The database contains both users and their Spotify credentials. The final

comparison will be performed after their Spotify music profiles are available

in the database.



\## D12 — Weight Sanity Findings



The controlled tests confirm that the intended scoring behavior is correct.



The standard scoring weights are:



\- Artist overlap = 60%

\- Genre similarity = 40%



The tests confirmed:



\- Artist-only similarity produces a score of 0.60.

\- Genre-only similarity produces a score of 0.40.

\- Full similarity in both components produces a score of 1.00.

\- Full genre coverage preserves the 60/40 weighting.

\- No genre coverage shifts the weights to 100% artist and 0% genre.

\- 50% genre coverage produces 80% artist and 20% genre weighting.



Therefore, artist similarity has the stronger influence on the compatibility

score, as intended, while incomplete genre metadata is handled through

adaptive weighting.



\## Final Status



\### Completed



\- Compatibility scoring implementation validated.

\- Artist Jaccard similarity validated through automated tests.

\- Genre cosine similarity validated through automated tests.

\- 60/40 artist/genre weighting validated.

\- Adaptive weighting behavior validated.

\- Compatibility-engine scoring tests passed.

\- Compatibility-engine service tests passed.

\- D12 weight sanity findings documented.



\### Pending



\- Successful Spotify music synchronization.

\- Extraction of real Spotify profile data from the database.

\- Manual verification of artist overlap for the two test users.

\- Manual calculation of expected real-account scores.

\- Comparison of expected scores against API scores.



The real-account validation will be added to this document once the

music-ingestion endpoint is working successfully.

