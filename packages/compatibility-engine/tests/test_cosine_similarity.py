import pytest

from compatibility_engine.similarity import cosine_similarity


def test_identical_vectors():
    a = {"pop": 0.6, "rock": 0.4}
    b = {"pop": 0.6, "rock": 0.4}
    assert cosine_similarity(a, b) == pytest.approx(1.0)


def test_completely_different_vectors():
    a = {"pop": 1.0}
    b = {"metal": 1.0}
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_partially_overlapping_vectors():
    a = {"pop": 0.6, "rock": 0.4}
    b = {"pop": 0.5, "jazz": 0.5}
    score = cosine_similarity(a, b)
    assert 0.0 < score < 1.0


def test_empty_vector():
    a = {}
    b = {"pop": 1.0}
    assert cosine_similarity(a, b) == 0.0
