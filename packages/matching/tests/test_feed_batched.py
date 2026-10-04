from unittest.mock import patch

from matching.feed import build_ranked_feed
from shared.models import Block, CompatibilityScore, User, UserMusicProfile


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.ops = []

    def set(self, key, value, ex=None):
        self.ops.append((key, value))

    def execute(self):
        for key, value in self.ops:
            self.redis.data[key] = str(value)
        self.ops = []


class FakeRedis:
    def __init__(self):
        self.data = {}

    def mget(self, keys):
        return [self.data.get(key) for key in keys]

    def pipeline(self):
        return FakePipeline(self)


def _artists(ids):
    return {
        "items": [
            {"id": f"artist-{i}", "name": f"Artist {i}", "genres": ["pop"]}
            for i in ids
        ]
    }


def _make_user(db, name, artist_ids, lat=31.10, lon=77.17):
    user = User(
        email=f"{name}@example.com",
        display_name=name,
        latitude=lat,
        longitude=lon,
        max_distance_km=100.0,
    )
    db.add(user)
    db.commit()
    db.add(
        UserMusicProfile(
            user_id=user.id,
            top_artists=_artists(artist_ids),
            top_tracks={"items": []},
            recently_played={"items": []},
            top_genres={},
            time_window="6m",
            is_stale=False,
        )
    )
    db.commit()
    return user


def _setup(db):
    me = _make_user(db, "me", range(6))
    close = _make_user(db, "close", range(6), lat=31.11, lon=77.18)
    stranger = _make_user(db, "stranger", range(100, 106), lat=31.12, lon=77.19)
    blocked = _make_user(db, "blocked", range(6), lat=31.11, lon=77.17)
    far = _make_user(db, "far", range(6), lat=40.0, lon=-74.0)
    db.add(Block(blocker_id=me.id, blocked_user_id=blocked.id))
    db.commit()
    return me, close, stranger, blocked, far


def test_cold_feed_ranks_filters_and_persists_scores(db_session):
    me, close, stranger, blocked, far = _setup(db_session)
    candidates = db_session.query(User).filter(User.id != me.id).all()

    feed = build_ranked_feed(db_session, FakeRedis(), me, candidates)

    assert [c.user_id for c in feed] == [close.id, stranger.id]
    assert feed[0].score > feed[1].score
    assert db_session.query(CompatibilityScore).count() == 2


def test_warm_feed_does_not_rescore(db_session):
    me, *_ = _setup(db_session)
    candidates = db_session.query(User).filter(User.id != me.id).all()
    redis = FakeRedis()

    first = build_ranked_feed(db_session, redis, me, candidates)

    with patch("matching.feed.score_profiles") as scorer:
        second = build_ranked_feed(db_session, redis, me, candidates)

    scorer.assert_not_called()
    assert second == first
    assert db_session.query(CompatibilityScore).count() == 2


def test_stored_scores_used_when_redis_is_empty(db_session):
    me, *_ = _setup(db_session)
    candidates = db_session.query(User).filter(User.id != me.id).all()

    first = build_ranked_feed(db_session, FakeRedis(), me, candidates)

    with patch("matching.feed.score_profiles") as scorer:
        second = build_ranked_feed(db_session, FakeRedis(), me, candidates)

    scorer.assert_not_called()
    assert second == first


def test_candidate_without_profile_is_skipped(db_session):
    me = _make_user(db_session, "me2", range(6))
    ghost = User(
        email="ghost@example.com",
        display_name="ghost",
        latitude=31.11,
        longitude=77.18,
    )
    db_session.add(ghost)
    db_session.commit()

    assert build_ranked_feed(db_session, FakeRedis(), me, [ghost]) == []