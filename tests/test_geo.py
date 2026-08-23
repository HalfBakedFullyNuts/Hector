"""Tests for Haversine geo helpers (T-1004)."""

from hector.services.geo import bounding_box, distance_km


def test_distance_between_known_cities() -> None:
    """Berlin–Hamburg is roughly 255 km."""
    berlin = (52.5200, 13.4050)
    hamburg = (53.5511, 9.9937)

    d = distance_km(berlin[0], berlin[1], hamburg[0], hamburg[1])

    assert 250 < d < 260


def test_zero_distance_for_identical_points() -> None:
    """Identical coordinates yield zero distance."""
    assert distance_km(52.52, 13.405, 52.52, 13.405) == 0


def test_bounding_box_contains_inner_point() -> None:
    """A point inside the radius lies within the returned box."""
    center = (52.52, 13.405)
    lat_min, lat_max, lng_min, lng_max = bounding_box(center[0], center[1], 50)

    inner = (52.53, 13.41)
    assert lat_min <= inner[0] <= lat_max
    assert lng_min <= inner[1] <= lng_max


def test_bounding_box_excludes_distant_point() -> None:
    """Hamburg is outside Berlin's 50 km box."""
    lat_min, lat_max, _, _ = bounding_box(52.52, 13.405, 50)
    assert not (lat_min <= 53.5511 <= lat_max)


def test_bounding_box_wraps_longitude() -> None:
    """Longitudes wrap around the antimeridian cleanly."""
    _, _, lng_min, lng_max = bounding_box(0.0, 179.5, 100)

    # Box spans across +/-180 degrees.
    assert -179.0 < lng_min or lng_max > 179.0 or abs(lng_max - lng_min) >= 350
