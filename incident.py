# incident.py: Represents an incident.

from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Tuple

DIRECTIONALS = [
    "southwest",    # 0b00
    "northwest",    # 0b01
    "southeast",    # 0b10
    "northeast"     # 0b11
]


class Incident:
    def __init__(self,
                 id: str,
                 time: str,
                 addr: str,
                 loc: Tuple[float, float],
                 inc_type: str) -> None:
        self._id = id
        self._time = datetime.strptime(time, "%m/%d/%Y %I:%M:%S %p")
        self._addr = addr
        self._lat, self._lon = loc
        self._type = inc_type
        self._units = []

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Incident):
            return self._id == o._id
        return False

    def get_id(self) -> str:
        return self._id

    def get_time(self) -> datetime:
        return self._time

    def get_addr(self) -> str:
        return self._addr

    def get_units(self) -> "list[str]":
        return self._units.copy()

    def get_type(self) -> str:
        return self._type

    def update_type(self, new_type: str) -> None:
        if self._type != new_type:
            print(f"Incident at {self._addr} has changed "
                  f"from {self._type} to {new_type}.")
            self._type = new_type

    def add_unit(self, unit) -> None:
        if unit not in self._units:
            print(f"Vehicle {unit} is responding to incident at {self._addr}.")
            self._units.append(unit)

    def get_dist_to(self, origin) -> float:
        # Haversine formula
        olat, olon = origin
        lat1, lon1, lat2, lon2 = map(
            radians, [olat, olon, self._lat, self._lon])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return c * 6371  # Earth radius (km)

    def get_direction_to(self, origin) -> str:
        olat, olon = origin
        is_north = self._lat > olat
        is_east = self._lon > olon
        idx = int(is_east) << 1 | int(is_north)
        return DIRECTIONALS[idx]

    def get_time_since(self) -> timedelta:
        return datetime.now() - self._time
