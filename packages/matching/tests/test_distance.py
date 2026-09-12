import pytest
from matching.distance import haversine_distance_km, is_within_distance


def test_same_point_is_zero_distance():
    assert haversine_distance_km(40.0, -74.0, 40.0, -74.0) == pytest.approx(0.0)


def test_known_distance_nyc_to_london():
    d = haversine_distance_km(40.7128, -74.0060, 51.5074, -0.1278)
    assert d == pytest.approx(5570, rel=0.01)


def test_is_within_distance_true():
    assert is_within_distance(40.0, -74.0, 40.01, -74.01, max_distance_km=5.0) is True


def test_is_within_distance_false():
    assert is_within_distance(40.7128, -74.0060, 51.5074, -0.1278, max_distance_km=100.0) is False


def test_is_within_distance_missing_coords_returns_false():
    assert is_within_distance(None, None, 40.0, -74.0, max_distance_km=50.0) is False
    assert is_within_distance(40.0, -74.0, None, None, max_distance_km=50.0) is False
