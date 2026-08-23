"""Geo-aware listing helpers for donation requests (T-1004)."""

from hector.models.donation_request import BloodDonationRequest
from hector.schemas.donation_request import DonationRequestWithDistance
from hector.services.geo import distance_km

GEO_WINDOW_LIMIT = 500


def build_geo_page(
    requests: list[BloodDonationRequest],
    lat: float,
    lng: float,
    limit: int,
    offset: int,
) -> list[DonationRequestWithDistance]:
    """Attach distances, filter/sort nearest-first, and paginate."""
    scored: list[tuple[float, DonationRequestWithDistance]] = []
    for req in requests:
        clinic = req.clinic
        assert clinic is not None, "request must carry its clinic"
        if clinic.latitude is None or clinic.longitude is None:
            continue

        item = DonationRequestWithDistance.model_validate(req)
        item.distance_km = round(distance_km(lat, lng, clinic.latitude, clinic.longitude), 1)
        scored.append((item.distance_km, item))

    scored.sort(key=lambda pair: pair[0])
    return [item for _, item in scored[offset : offset + limit]]
