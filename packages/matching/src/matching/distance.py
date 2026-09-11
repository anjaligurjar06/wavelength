import math

EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Compute great-circle distance between two lat/lon points in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def is_within_distance(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
    max_distance_km: float,
) -> bool:
    """Return True if two points are within max_distance_km of each other.

    Returns False if either point is missing coordinates (can't filter without location).
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return False
    return haversine_distance_km(lat1, lon1, lat2, lon2) <= max_distance_km
