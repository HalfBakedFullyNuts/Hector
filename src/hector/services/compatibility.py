"""Blood type compatibility scoring (T-604).

Scores donor/request blood-type fit; higher is better.
"""

from hector.models.dog_profile import BloodType

UNIVERSAL_DONOR_SCORE = 100
EXACT_MATCH_SCORE = 75
ANY_TYPE_SCORE = 50
UNKNOWN_DOG_SCORE = 25
INCOMPATIBLE_SCORE = 0


def compatibility_score(dog_type: "BloodType | None | str", needed: "BloodType | None | str") -> int:
    """Return an integer fit score for a dog/request blood-type pair."""
    # StrEnum members compare equal to their string values, so accept both.
    if dog_type == BloodType.DEA_1_1_NEGATIVE:
        # Universal donor matches every request (spec T-604)
        return UNIVERSAL_DONOR_SCORE

    if needed is None:
        # Clinic accepts any blood type
        return ANY_TYPE_SCORE

    if dog_type is None:
        # Dog's blood type unknown: weak but nonzero signal
        return UNKNOWN_DOG_SCORE

    if dog_type == needed:
        return EXACT_MATCH_SCORE

    return INCOMPATIBLE_SCORE
