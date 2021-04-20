# geocoding.py: Geocodes addresses using Google Maps Geocoding API.

from typing import Tuple

import requests

# MapQuest geocoding API
API_ENDPOINT = "https://www.mapquestapi.com/geocoding/v1/address"

# Suffix for Seattle addresses
ADDRESS_SUFFIX = ", Seattle, WA"


class Geocoder:
    """
    A MapQuest geocoder that converts addresses to coordinates.
    """
    def __init__(self, key: str) -> None:
        """
        Creates a new geocoder.

        Args:
            key (str): MapQuest API key.
        """
        self._key = key
        self._ses = requests.Session()

    def _make_url_params(self, addr: str) -> dict:
        """
        Creates a URL parameter dictionary for MapQuest API.

        Args:
            addr (str): The address to geocode.

        Returns:
            dict: URL parameters for the endpoint.
        """
        return {
            "key": self._key,
            "location": addr,
            "thumbMaps": False
        }

    def _send_request(self, query: dict) -> dict:
        """
        Sends a request with specified parameters to MapQuest.

        Args:
            query (dict): URL query parameters.

        Returns:
            dict: The JSON response, or None if there is an error.
        """
        r = self._ses.get(API_ENDPOINT, params=query)
        if r.status_code != 200:
            print("Mapquest request error: " + r.text)
            return None
        return r.json()

    def geocode(self, addr: str) -> Tuple[float, float]:
        """
        Geocodes the specified Seattle address to coordinates.

        Args:
            addr (str): The address to geocode.

        Returns:
            Tuple[float, float]: (lat, lon), or (0, 0) if results are invalid.
        """
        addr = addr.replace("/", "&") + ADDRESS_SUFFIX
        query = self._make_url_params(addr)
        resp = self._send_request(query)
        if resp is None:
            return (0.0, 0.0)
        results = resp["results"]
        if len(results) < 1:
            print("Mapquest didn't return any results.")
            return (0.0, 0.0)
        for result in results:
            for loc in result["locations"]:
                if loc["adminArea5"] == "Seattle":
                    return (loc["latLng"]["lat"], loc["latLng"]["lng"])
        print("Mapquest didn't return any valid locations.")
        return (0.0, 0.0)
