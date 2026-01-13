from abc import ABC, abstractmethod
from typing import List

from src.dtos.geo_reference import GeoReference


class ABCGeoLocationFinder(ABC):
    """
    Abstract base class for geolocation extraction.

    Input:
        List[str] of place names

    Output:
        List[Dict] where each dict matches ES geoReferences mapping:
        {
            "placeName": str,
            "coordinates": {
                "lat": float,
                "lon": float
            }
        }
    """

    @abstractmethod
    def _geocode_single_place(self, place_name: str) -> GeoReference | None:
        """
        Geocode a single place name into a structured geolocation object.

        This method must convert a textual place name (e.g., a city or country)
        into a dictionary that matches the Elasticsearch `geoReferences` nested
        field structure.

        Implementations are responsible for handling external geocoding services,
        errors, and fallbacks.

        Args:
            place_name: A location name extracted from the document text
                        (e.g., "Gaza", "Nablus", "Palestine").

        Returns:
            A dictionary with the following structure if geocoding succeeds:
                {
                    "placeName": str,
                    "coordinates": {
                        "lat": float,
                        "lon": float
                    }
                }

            Returns None if the place cannot be geocoded.
        """
        pass

    @abstractmethod
    def extract_from_places(self, places: List[str]) -> List[GeoReference]:
        """
        Extract structured geolocation references from a list of place names.

        Implementations should:
        - loop over place names
        - delegate single-place geocoding
        - return clean GeoReference objects
        """
        pass
