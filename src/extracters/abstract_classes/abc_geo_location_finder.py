from abc import ABC, abstractmethod
from typing import Any, Dict, List

from dtos.geo_reference import GeoReference


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

    def extract_from_places(self, places: List[str]) -> List[GeoReference]:
        """
        Template method:
        - loops over place names
        - delegates single-place geocoding to implementation
        - guarantees clean output structure
        """
        geo_refs: List[Dict[str, Any]] = []

        for place in places:
            if not place or not place.strip():
                continue

            result = self._geocode_single_place(place.strip())
            if result:
                geo_refs.append(result)

        return geo_refs
