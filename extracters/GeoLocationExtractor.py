# import abstract base class
from extracters.abc_extractor import ABCExtractor

# import necessary modules
from typing import Any, Dict, Set
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import (
    GeocoderTimedOut,
    GeocoderUnavailable,
    GeocoderServiceError,
)

# setup logging
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Geopy geocoder (Nominatim)
geolocator = Nominatim(user_agent="najah_ir_project")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2)

# Fallback geopoint (An-Najah University / Nablus approx coords)
AL_NAJAH_POINT = {"lat": 32.221, "lon": 35.254}


class GeoLocationExtractor(ABCExtractor):
    """
    Extractor that attempts to geocode the given text
    into a single georeference object (place with coordinates).

    The extract() method returns:
        - a set with one dict on success
        - an empty set() if geocoding fails

    Args:
        text: place name / location string to geocode
        lang: language code (currently unused). The parameter is retained
              to comply with the ABCExtractor interface and to allow future
              language-specific enhancements if needed.
    """

    def extract(self, text: str, lang: str) -> Set[Dict[str, Any]]:
        # Validate input
        self._validate_text(text)

        # Perform geocoding
        try:
            loc = geocode(text)

            if not loc:
                logger.debug(f"[geocode] No result for place: '{text}'")
                return set()

            # Build the georeference object
            geo_ref: Dict[str, Any] = {
                "placeName": text,
                "coordinates": {
                    "lat": float(loc.latitude),
                    "lon": float(loc.longitude),
                },
            }

            # This is what you’ll put under "geoReferences": [...]
            return {geo_ref}

        # Handle geocoding exceptions
        except GeocoderTimedOut:
            # Log timeout warning
            logger.warning(f"[geocode] Timeout while geocoding '{text}'")
            return set()

        except GeocoderUnavailable:
            # Log unavailability error
            logger.error(f"[geocode] Geocoder unavailable for '{text}'")
            return set()

        except GeocoderServiceError as e:
            # Log service error
            logger.error(f"[geocode] Service error for '{text}': {e}")
            return set()

        except Exception as e:
            logger.exception(f"[geocode] Unexpected error for '{text}': {e}")
            return set()

    @staticmethod
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
