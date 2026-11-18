import unicodedata

from apps.core.exceptions import ApiError
from apps.shipping.models import ShippingZone

MUNICIPALITY_NOT_COVERED_MESSAGE = "Solo enviamos a Cali, Palmira, Jamundí y Yumbo."


def normalize_municipality(name: str) -> str:
    """Normaliza un municipio para compararlo: sin espacios extra, minúsculas y sin tildes.

    Ejemplo: "  JAMUNDI " y "jamundí" resultan ambos en "jamundi".
    """
    collapsed = " ".join((name or "").split()).casefold()
    decomposed = unicodedata.normalize("NFKD", collapsed)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def get_zone_for_municipality(*, municipality: str) -> ShippingZone:
    """Devuelve la zona de envío activa que corresponde al municipio indicado.

    Provisional para el checkout (HU-19 a HU-21); anticipa la gestión de zonas y tarifas
    de HU-26 y HU-28. Como solo hay unas pocas zonas, se compara en Python con el nombre
    normalizado. Lanza ApiError(municipality_not_covered) si no hay zona activa que coincida.
    """
    target = normalize_municipality(municipality)
    if target:
        for zone in ShippingZone.objects.filter(is_active=True):
            if normalize_municipality(zone.municipality) == target:
                return zone
    raise ApiError(
        MUNICIPALITY_NOT_COVERED_MESSAGE,
        code="municipality_not_covered",
        fields={"municipality": [MUNICIPALITY_NOT_COVERED_MESSAGE]},
    )
