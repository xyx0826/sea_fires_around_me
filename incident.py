# incident.py: Represents an incident.

from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Tuple

# Directional adjectives.
DIRECTIONALS = [
    "southwest",    # 0b00
    "northwest",    # 0b01
    "southeast",    # 0b10
    "northeast"     # 0b11
]


class Incident:
    """
    Represents an active incident
    and provides ways to compute time and space differences.
    """
    def __init__(self,
                 id: str,
                 time: str,
                 addr: str,
                 loc: Tuple[float, float],
                 inc_type: str) -> None:
        """
        Creates a new incident.

        Args:
            id (str): The ID of the incident.
            time (str): The time string of the incident.
            addr (str): The location of the incident.
            loc (Tuple[float, float]): (lat, lon) of the incident.
            inc_type (str): The type of the incident.
        """
        self._id = id
        self._time = datetime.strptime(time, "%m/%d/%Y %I:%M:%S %p")
        self._addr = addr
        self._lat, self._lon = loc
        self._type = inc_type
        self._units = []

    def get_id(self) -> str:
        """
        Returns the ID of the incident.

        Returns:
            str: The ID of the incident.
        """
        return self._id

    def get_time(self) -> datetime:
        """
        Returns the parsed timestamp of the incident.

        Returns:
            datetime: The timestamp of the incident.
        """
        return self._time

    def get_addr(self) -> str:
        """
        Returns the address of the incident.

        Returns:
            str: The address of the incident.
        """
        return self._addr

    def get_units(self) -> "list[str]":
        """
        Returns a list of all dispatched units to the incident.

        Returns:
            list[str]: A list of all dispatched units to the incident.
        """
        return self._units.copy()

    def get_type(self) -> str:
        """
        Returns the type of the incident.

        Returns:
            str: The type of the incident.
        """
        return self._type

    def update_type(self, new_type: str) -> None:
        """
        Updates the type of the incident,
        and emits a message if the type has been changed.

        Args:
            new_type (str): The new type.
        """
        if self._type != new_type:
            print(f"Incident at {self._addr} has changed "
                  f"from {self._type} to {new_type}.")
            self._type = new_type

    def add_unit(self, unit: str) -> None:
        """
        Adds a newly dispatched unit to the incident,
        and emits a message.

        Args:
            unit (str): The newly dispatched unit.
        """
        if unit not in self._units:
            print(f"Vehicle {unit} is responding to incident at {self._addr}.")
            self._units.append(unit)

    def get_dist_to(self, origin: Tuple[float, float]) -> float:
        """
        Returns the distance between the incident location
        and the specified origin, in kilometers using the
        Haversine formula.

        Args:
            origin (Tuple[float, float]): Point B in (lat, lon) format.

        Returns:
            float: The distance in kilometers.
        """
        olat, olon = origin
        lat1, lon1, lat2, lon2 = map(
            radians, [olat, olon, self._lat, self._lon])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return c * 6371  # Earth radius (km)

    def get_direction_to(self, origin: Tuple[float, float]) -> str:
        """
        Returns the directional verb from the specified origin
        to the incident location.

        Args:
            origin (Tuple[float, float]): Point B in (lat, lon) format.

        Returns:
            str: The directional verb: [north/south][east/west].
        """
        olat, olon = origin
        is_north = self._lat > olat
        is_east = self._lon > olon
        idx = int(is_east) << 1 | int(is_north)
        return DIRECTIONALS[idx]

    def get_time_since(self) -> timedelta:
        """
        Returns the time elapsed since the creation of the incident.

        Returns:
            timedelta: Time elapsed since the creation of the incident.
        """
        return datetime.now() - self._time
