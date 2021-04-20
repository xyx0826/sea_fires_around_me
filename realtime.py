# realtime.py: pulls fire information from
#              Seattle Fire Real-Time 911.

from datetime import datetime, timedelta
from enum import Enum
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

import requests

from geocoder import Geocoder
from incident import Incident

# The Real-Time 911 endpoint.
REALTIME_ENDPOINT = "http://www2.seattle.gov/fire/" \
                    "realtime911/getRecsForDatePub.asp"


class IncidentColumn(Enum):
    """
    Incident columns.
    """
    INVALID = 0
    DATETIME = 1
    ID = 2
    LEVEL = 3
    UNITS = 4
    LOCATION = 5
    TYPE = 6


class IncidentRow:
    """
    Represents a row of incident.
    """
    def __init__(self,
                 dt: str, id: str, lvl: str,
                 units: str, loc: str, typ: str) -> None:
        self.datetime = dt
        self.id = id
        self.level = lvl
        self.units = units
        self.loc = loc
        self.typ = typ


class RealTimeParser(HTMLParser):
    """
    A parser for the Real-Time 911 dispatch page.
    """
    def __init__(self) -> None:
        """
        Creates a new parser.
        """
        self._next_td = IncidentColumn.INVALID
        self._rows = []
        self._cache = []
        super().__init__()

    def _handle_row(self, attrs: "List[Tuple[str, Optional[str]]]") -> None:
        """
        Handles a new table row.
        If valid, signals the parser to start reading columns.

        Args:
            attrs (List[Tuple[str, Optional[str]]]): Row element attributes.
        """
        for attr in attrs:
            if attr[0] == "id" and attr[1].startswith("row_"):
                # Valid column header
                self._next_td = IncidentColumn.DATETIME

    def _handle_cell(self, attrs: "List[Tuple[str, Optional[str]]]") -> None:
        """
        Handles a new table cell.
        If the incident is inactive, signals the parser to
        skip over remaining columns.

        Args:
            attrs (List[Tuple[str, Optional[str]]]): Cell element attributes.
        """
        for attr in attrs:
            if attr[0] == "class" and attr[1] != "active":
                # Closed incident, ignore
                self._next_td = IncidentColumn.INVALID

    def handle_starttag(self,
                        tag: str,
                        attrs: "List[Tuple[str, Optional[str]]]") -> None:
        """
        Handles an opening tag.
        Dispatches new table rows and cells to handlers.

        Args:
            tag (str): The opening tag.
            attrs (List[Tuple[str, Optional[str]]]): Attributes for the tag.
        """
        if tag == "tr":
            # Might be a new row
            self._handle_row(attrs)
        elif tag == "td" and self._next_td != IncidentColumn.INVALID:
            # Might be a new cell
            self._handle_cell(attrs)

    def handle_endtag(self, tag: str) -> None:
        """
        Handles a closing tag.
        Pushes saved columns onto the row list as a new incident row.

        Args:
            tag (str): The closing tag.
        """
        if tag == "tr" and self._next_td != IncidentColumn.INVALID:
            # End of row
            if len(self._cache) < 6:
                dt, id, units, loc, typ = self._cache
                lvl = 0
            else:
                dt, id, lvl, units, loc, typ = self._cache
            row = IncidentRow(dt, id, lvl, units, loc, typ)
            self._rows.append(row)
            self._next_td = IncidentColumn.INVALID
            self._cache.clear()

    def handle_data(self, data: str) -> None:
        """
        Handles data in tags.
        Pushes valid column texts onto the cache.

        Args:
            data (str): Data.
        """
        if self._next_td == IncidentColumn.INVALID:
            return

        if not data.strip():
            # Empty content, maybe <tr>
            return

        self._cache.append(data)
        if self._next_td != IncidentColumn.TYPE:
            self._next_td = IncidentColumn(self._next_td.value + 1)

    def feed(self, feed: str) -> None:
        """
        Feeds a new HTML page to the parser.
        Clears previously read rows.

        Args:
            feed (str): A new HTML page.
        """
        self._rows.clear()
        super().feed(feed)

    def get_rows(self) -> "List[IncidentRow]":
        """
        Gets all read rows.

        Returns:
            List[IncidentRow]: A list of all read rows.
        """
        return self._rows.copy()


class RealTime:
    """
    A real-time 911 dispatch monitor.
    """
    def __init__(self,
                 origin_lat: float, origin_lon: float,
                 mapquest_api_key: str) -> None:
        """
        Creates a new monitor.

        Args:
            origin_lat (float): The origin latitude.
            origin_lon (float): The origin longitude.
            mapquest_api_key (str): The MapQuest API key for geocoding.
        """
        self._ses = requests.Session()
        self._parser = RealTimeParser()
        self._coder = Geocoder(mapquest_api_key)
        self._origin = (origin_lat, origin_lon)
        self._incidents = {}  # type: Dict[str, Incident]

        self._ses.headers.update({
            "User-Agent": "SFD Feed Watcher "
            "(https://github.com/xyx0826/sea_fires_around_me)"
        })

    def _get_two_day_rows(self) -> "List[IncidentRow]":
        """
        Gets all incident rows from today and yesterday
        to deal with midnight jumps.

        Returns:
            List[IncidentRow]: A list of all active incident rows.
        """
        r = self._ses.get(REALTIME_ENDPOINT, params={
            "action": "Today"
        })
        self._parser.feed(r.text)
        rows = self._parser.get_rows()

        yesterday = datetime.today() - timedelta(days=1)
        r = self._ses.get(REALTIME_ENDPOINT, params={
            "incDate": yesterday.strftime("%m/%d/%Y")
        })
        self._parser.feed(r.text)
        yesterday_rows = self._parser.get_rows()
        if len(yesterday_rows) > 0:
            rows.append(yesterday_rows)
        return rows

    def _add_incident(self, row: IncidentRow) -> None:
        """
        Adds a new incident and prints a message.

        Args:
            row (IncidentRow): The new incident.
        """
        latlon = self._coder.geocode(row.loc)
        inc = Incident(row.id, row.datetime, row.loc, latlon, row.typ)
        dist = inc.get_dist_to(self._origin)
        dire = inc.get_direction_to(self._origin)
        print(f"Incident of type {inc.get_type()} is opened "
              f"at {inc.get_addr()}, {dist:.2f} km {dire}.")
        self._incidents[row.id] = inc

    def _update_incident(self, row: IncidentRow) -> None:
        """
        Updates an open incident.

        Args:
            row (IncidentRow): The incident to update.
        """
        inc = self._incidents[row.id]
        for unit in row.units.split(" "):
            inc.add_unit(unit)
        inc.update_type(row.typ)

    def _remove_incident(self, inc_id: str) -> None:
        """
        Removes a resolved incident and prints a message.

        Args:
            inc_id (str): The ID of the resolved incident.
        """
        inc = self._incidents[inc_id]
        addr = inc.get_addr()
        mins = inc.get_time_since().total_seconds() / 60
        print(f"Incident at {addr} is now resolved after {int(mins)} minutes.")
        del self._incidents[inc_id]

    def update(self) -> None:
        """
        Checks if there are incidents to update.
        """
        rows = self._get_two_day_rows()

        # Add new rows
        for row in rows:
            if row.id not in self._incidents.keys():
                self._add_incident(row)

        # Update existing rows
        updated_rows = [r for r in rows if r.id in self._incidents.keys()]
        for updated_row in updated_rows:
            self._update_incident(updated_row)

        # Remove deleted rows
        active_ids = [r.id for r in rows]
        for inc_id in list(self._incidents):
            if inc_id not in active_ids:
                self._remove_incident(inc_id)
