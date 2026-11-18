from decimal import Decimal

import pytest

from apps.core.exceptions import ApiError
from apps.shipping.models import ShippingZone
from apps.shipping.services import get_zone_for_municipality, normalize_municipality

NOT_COVERED = "Solo enviamos a Cali, Palmira, Jamundí y Yumbo."


@pytest.mark.django_db
def test_seed_zones_present_with_fees():
    fees = {z.municipality: z.fee for z in ShippingZone.objects.all()}
    assert fees == {
        "Cali": Decimal("5000"),
        "Palmira": Decimal("10000"),
        "Jamundí": Decimal("10000"),
        "Yumbo": Decimal("10000"),
    }
    assert all(z.is_active for z in ShippingZone.objects.all())


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  JAMUNDI ", "jamundi"),
        ("jamundí", "jamundi"),
        ("Jamundí", "jamundi"),
        ("  Cali   ", "cali"),
        ("Santa   Rosa", "santa rosa"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize_municipality(raw, expected):
    assert normalize_municipality(raw) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Cali", "Cali"),
        ("  CALI ", "Cali"),
        ("palmira", "Palmira"),
        ("  JAMUNDI ", "Jamundí"),
        ("jamundí", "Jamundí"),
        ("yUmBo", "Yumbo"),
    ],
)
def test_get_zone_matches_ignoring_case_accents_and_spaces(raw, expected):
    zone = get_zone_for_municipality(municipality=raw)
    assert zone.municipality == expected


@pytest.mark.django_db
def test_get_zone_returns_fee():
    assert get_zone_for_municipality(municipality="Cali").fee == Decimal("5000")


@pytest.mark.django_db
@pytest.mark.parametrize("raw", ["Bogotá", "", "   "])
def test_uncovered_municipality_raises(raw):
    with pytest.raises(ApiError) as exc_info:
        get_zone_for_municipality(municipality=raw)
    error = exc_info.value
    assert error.get_codes() == "municipality_not_covered"
    assert str(error.detail) == NOT_COVERED
    assert error.fields == {"municipality": [NOT_COVERED]}


@pytest.mark.django_db
def test_inactive_zone_raises():
    ShippingZone.objects.filter(municipality="Yumbo").update(is_active=False)
    with pytest.raises(ApiError) as exc_info:
        get_zone_for_municipality(municipality="Yumbo")
    assert exc_info.value.get_codes() == "municipality_not_covered"
