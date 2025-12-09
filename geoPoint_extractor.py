from typing import Any, Dict, Optional
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


# Geopy geocoder (Nominatim)
geolocator = Nominatim(user_agent="najah_ir_project")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2)

# Fallback geopoint (An-Najah University / Nablus approx coords)
AL_NAJAH_POINT = {"lat": 32.221, "lon": 35.254}

def geocode_place(name: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a single place name into a structured georeference object.
    This is used for each element in the `georeferences` array.
    """
    try:
        loc = geocode(name)
    except Exception:
        return None

    if not loc:
        return None

    raw = loc.raw or {}
    address = raw.get("address", {})
    country_code = None
    if isinstance(address, dict):
        country_code = address.get("country_code")

    country = country_code.upper() if country_code else None

    return {
        "name": name,
        "country": country,
        # this `location` field is the geo_point we store per reference
        "location": {
            "lat": float(loc.latitude),
            "lon": float(loc.longitude),
        },
        "confidence": 1.0  # static for now; can be tuned later
    }


def build_geopoint_from_origin() -> Dict[str, float]:
    """
    Build the single `geopoint` field used as the document's origin/affiliation
    location.

    For now we keep it simple and set everything to An-Najah University
    coordinates, since the majority of the repository is associated with
    An-Najah. Later you can extend this to:
      - infer author hometown from last name
      - or use publisher/affiliation fields if available.
    """
    return AL_NAJAH_POINT.copy()


