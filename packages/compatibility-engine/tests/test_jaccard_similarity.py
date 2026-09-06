from compatibility_engine.similarity import jaccard_similarity


def test_identical_users():
    user_a = ["Karan Aujla", "Diljit Dosanjh"]
    user_b = ["Karan Aujla", "Diljit Dosanjh"]
    result = jaccard_similarity(user_a, user_b)
    assert result == 1.0


def test_no_common_artists():
    user_a = ["Karan Aujla", "Diljit Dosanjh"]
    user_b = ["Arijit Singh", "A.R. Rahman"]
    result = jaccard_similarity(user_a, user_b)
    assert result == 0.0


def test_partial_overlap():
    user_a = ["Karan Aujla", "Diljit Dosanjh", "Amrinder Gill"]
    user_b = ["Karan Aujla", "Diljit Dosanjh", "Arijit Singh"]
    result = jaccard_similarity(user_a, user_b)
    assert result == 0.5


def test_empty_lists():
    result = jaccard_similarity([], [])
    assert result == 0.0
