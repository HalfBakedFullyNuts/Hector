"""Haversine distance and bounding-box math (T-1004)."""

import math

EARTH_RADIUS_KM = 6371.0


def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    assert -90 <= lat1 <= 90 and -90 <= lat2 <= 90, "latitudes out of range"
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(
    lat: float,
    lng: float,
    radius_km: float,
) -> tuple[float, float, float, float]:
    """Return (lat_min, lat_max, lng_min, lng_max) enclosing the radius."""
    assert radius_km > 0, "radius must be positive"
    d_lat = math.degrees(radius_km / EARTH_RADIUS_KM)

    cos_lat = max(math.cos(math.radians(lat)), 1e-12)
    d_lng = math.degrees(radius_km / (EARTH_RADIUS_KM * cos_lat))

    lat_min = max(-90.0, lat - d_lat)
    lat_max = min(90.0, lat + d_lat)
    lng_min = ((lng - d_lng + 180.0) % 360.0) - 180.0
    lng_max = ((lng + d_lng + 180.0) % 360.0) - 180.0
    return lat_min, lat_max, lng_min, lng_max
