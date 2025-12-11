# geopy_geolocation_extractor.py

import logging
from typing import Any, Dict

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import (
    GeocoderTimedOut,
    GeocoderUnavailable,
    GeocoderServiceError,
)

from extracters.abstract_classes.abc_geo_location_finder import (
    ABCGeoLocationFinder,
)


logger = logging.getLogger(__name__)


# Geocoder setup (module-level, reusable & rate-limited)
geolocator = Nominatim(user_agent="najah_ir_project")
geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1,
    max_retries=2,
    swallow_exceptions=False,
)


class GeopyGeoLocationFinder(ABCGeoLocationFinder):
    """
    Concrete geolocation extractor using Geopy + Nominatim.
    """

    def _geocode_single_place(self, place_name: str) -> Dict[str, Any] | None:

        try:

            loc = geocode(
                place_name,
            )

            if not loc:
                logger.debug(f"No geocode result for '{place_name}'")
                return None

            return {
                "placeName": place_name,
                "coordinates": {
                    "lat": float(loc.latitude),
                    "lon": float(loc.longitude),
                },
            }

        except GeocoderTimedOut:
            logger.warning(f"Timeout while geocoding '{place_name}'")
        except GeocoderUnavailable:
            logger.error("Geocoder unavailable")
        except GeocoderServiceError as e:
            logger.error(f"Geocoder service error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected geocoding error for '{place_name}': {e}")

        return None
