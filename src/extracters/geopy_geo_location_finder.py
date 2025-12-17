import logging

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import (
    GeocoderTimedOut,
    GeocoderUnavailable,
    GeocoderServiceError,
)

from src.extracters.abstract_classes.abc_geo_location_finder import (
    ABCGeoLocationFinder,
)
from src.dtos.geo_reference import GeoReference
from src.dtos.geo_coordinates import GeoCoordinates

logger = logging.getLogger(__name__)

# Quiet down noisy internal logging from geopy's RateLimiter during bulk runs
logging.getLogger("geopy").setLevel(logging.ERROR)


# Geocoder setup (module-level, reusable & rate-limited)
geolocator = Nominatim(user_agent="najah_ir_project", timeout=5)
geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1,
    max_retries=1,
    swallow_exceptions=True,  # do not break ingestion on geocode failures
    error_wait_seconds=1,
)


class GeopyGeoLocationFinder(ABCGeoLocationFinder):
    """
    Concrete geolocation extractor using Geopy + Nominatim.
    """

    def _geocode_single_place(self, place_name: str) -> GeoReference | None:

        try:

            loc = geocode(
                place_name,
            )

            if not loc:
                logger.debug(f"No geocode result for '{place_name}'")
                return None

            return GeoReference(
                placeName=place_name,
                coordinates=GeoCoordinates(
                    lat=float(loc.latitude),
                    lon=float(loc.longitude),
                ),
            )

        except GeocoderTimedOut:
            logger.warning(f"Timeout while geocoding '{place_name}'")
        except GeocoderUnavailable:
            logger.error("Geocoder unavailable")
        except GeocoderServiceError as e:
            logger.error(f"Geocoder service error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected geocoding error for '{place_name}': {e}")

        return None
