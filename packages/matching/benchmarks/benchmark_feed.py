"""Load test for /matching/feed: 500 seeded users, cold vs warm caches.

Runs against a scratch Postgres DB (name must contain 'loadtest') and
Redis db 15, never your dev data. Calls the endpoint function directly,
so HTTP/JWT overhead (a few ms) is not included.
"""

import logging
import os
import random
import time

from api.config import settings
from api.routes.matching import get_matching_feed
from redis import Redis
from shared.db import get_engine
from shared.models import Base, User, UserMusicProfile
from sqlalchemy.orm import sessionmaker

PROFILE_COUNT = 500
ARTISTS_PER_PROFILE = 20
ARTIST_POOL_SIZE = 200
BUDGET_MS = 500
SAMPLE_USERS = 5
GENRES = ["pop", "rock", "indie", "hip-hop", "electronic",
          "jazz", "classical", "metal", "r&b", "folk"]

logging.getLogger("wavelength.access").setLevel(logging.WARNING)


def scratch_url() -> str:
    url = os.getenv("LOADTEST_DATABASE_URL") or (
        settings.database_url.rsplit("/", 1)[0] + "/wavelength_loadtest"
    )
    if "loadtest" not in url.rsplit("/", 1)[1]:
        raise SystemExit(f"Refusing to run: {url} is not a loadtest database")
    return url


def artists_for(i: int) -> list[dict]:
    out = []
    for rank in range(ARTISTS_PER_PROFILE):
        a = (i * 7 + rank * 3) % ARTIST_POOL_SIZE
        out.append({
            "id": f"artist-{a}",
            "name": f"Artist {a}",
            "genres": [GENRES[a % 10], GENRES[(a + 3) % 10]],
        })
    return out


def seed(session_factory) -> list[str]:
    rng = random.Random(42)
    ids = []
    with session_factory() as db:
        for i in range(PROFILE_COUNT):
            uid = f"lt-user-{i:03d}"
            ids.append(uid)
            db.add(User(
                id=uid,
                email=f"lt-{i:03d}@example.com",
                display_name=f"LT User {i:03d}",
                latitude=31.10 + rng.uniform(-0.1, 0.1),
                longitude=77.17 + rng.uniform(-0.1, 0.1),
                max_distance_km=100.0,
            ))
            db.add(UserMusicProfile(
                user_id=uid,
                top_artists={"items": artists_for(i)},
                top_tracks={"items": []},
                recently_played={"items": []},
                top_genres={},
                time_window="6m",
                is_stale=False,
            ))
        db.commit()
    return ids


def one_request(session_factory, redis_client, user_id) -> tuple[float, int]:
    with session_factory() as db:
        user = db.get(User, user_id)
        start = time.perf_counter()
        feed = get_matching_feed(user=user, db=db, redis_client=redis_client)
        return (time.perf_counter() - start) * 1000, len(feed)


def pct(values: list[float], p: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, round(p / 100 * (len(s) - 1)))]


def report(label: str, times: list[float]) -> None:
    p95 = pct(times, 95)
    verdict = "PASS" if p95 < BUDGET_MS else "FAIL"
    print(
        f"{label:<28} n={len(times):<4} p50={pct(times, 50):8.1f}ms "
        f"p95={p95:8.1f}ms p99={pct(times, 99):8.1f}ms "
        f"max={max(times):8.1f}ms  [{verdict} vs {BUDGET_MS}ms]"
    )


def main() -> None:
    url = scratch_url()
    engine = get_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    sf = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    r = Redis.from_url("redis://localhost:6379/15", decode_responses=True)
    r.flushdb()

    print(f"Seeding {PROFILE_COUNT} users into {url.rsplit('@', 1)[-1]} ...")
    ids = seed(sf)
    sample = ids[:SAMPLE_USERS]

    # 1) Cold: no stored scores, empty Redis (first-ever feed for each user)
    cold = []
    for uid in sample:
        ms, size = one_request(sf, r, uid)
        if size == 0:
            raise SystemExit("Feed returned 0 candidates - check seeding/distance")
        cold.append(ms)
    print(f"Feed size per user: ~{size} candidates\n")
    report("cold (no stored, no redis)", cold)

    # 2) DB-warm: scores stored in Postgres, Redis flushed before each call
    db_warm = []
    for _ in range(20):
        for uid in sample:
            r.flushdb()
            db_warm.append(one_request(sf, r, uid)[0])
    report("db-warm (redis empty)", db_warm)

    # 3) Fully warm: Redis populated
    for uid in sample:
        one_request(sf, r, uid)
    warm = [one_request(sf, r, uid)[0] for _ in range(40) for uid in sample]
    report("fully warm (redis hit)", warm)

    r.flushdb()


if __name__ == "__main__":
    main()