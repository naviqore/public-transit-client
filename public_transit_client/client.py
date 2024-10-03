import logging
from datetime import datetime
from typing import Any

import requests
from requests import Response

from public_transit_client.model import (
    APIError,
    Connection,
    Coordinate,
    Departure,
    DistanceToStop,
    QueryConfig,
    RouterInfo,
    ScheduleInfo,
    SearchType,
    Stop,
    StopConnection,
    TimeType,
)

LOG = logging.getLogger(__name__)


class PublicTransitClientException(Exception):
    """Exception raised for errors in the Public Transit Client."""

    def __init__(self, api_error: APIError):
        """Initialize the PublicTransitClientException with an APIError.

        Args:
            api_error (APIError): The error object returned by the API.
        """
        self.api_error = api_error
        super().__init__(f"API Error {api_error.status}: {api_error.message}")


class PublicTransitClient:
    """A client to interact with the public transit API."""

    def __init__(self, host: str):
        """Initialize the PublicTransitClient with the API host URL.

        Args:
            host (str): The base URL of the public transit API.
        """
        self.host = host

    def _send_get_request(self, endpoint: str, params: dict[str, Any] | None = None):
        """Sends a GET request to the API and handles the response."""
        url = f"{self.host}{endpoint}"
        LOG.debug(f"Sending GET request to {url} with params {params}")
        response = requests.get(url, params=params)
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: Response):
        """Handles the response from the API."""
        if response.status_code == 200:
            return response.json()
        else:
            try:
                error_details = APIError(**response.json())
                LOG.error(f"API error occurred: {error_details}")
                raise PublicTransitClientException(error_details)
            except ValueError:
                LOG.error(f"Non-JSON response received: {response.text}")
                response.raise_for_status()

    def get_schedule_info(self) -> ScheduleInfo:
        """Retrieve information about the schedule API."""
        data = self._send_get_request("/schedule")
        return ScheduleInfo(**data)

    def search_stops(
        self, query: str, limit: int = 10, search_type: SearchType = SearchType.CONTAINS
    ) -> list[Stop]:
        """Search for stops by a query string.

        Args:
            query (str): The search query for the stop name.
            limit (int, optional): The maximum number of stops to return. Defaults to 10.
            search_type (SearchType, optional): The type of search to perform (EXACT, CONTAINS, etc.). Defaults to CONTAINS.

        Returns:
            list[Stop]: A list of Stop objects that match the query.
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": str(limit),
            "searchType": search_type.name,
        }
        data = self._send_get_request("/schedule/stops/autocomplete", params)
        return [Stop(**stop) for stop in data]

    def nearest_stops(
        self, coordinate: Coordinate, limit: int = 10, max_distance: int = 1000
    ) -> list[DistanceToStop]:
        """Find the nearest stops to a given coordinate.

        Args:
            coordinate (Coordinate): The geographical coordinate to search from.
            limit (int, optional): The maximum number of stops to return. Defaults to 10.
            max_distance (int, optional): The maximum distance (in meters) from the coordinate to search. Defaults to 1000.

        Returns:
            list[DistanceToStop]: A list of DistanceToStop objects representing nearby stops.
        """
        params = {
            "latitude": str(coordinate.latitude),
            "longitude": str(coordinate.longitude),
            "limit": str(limit),
            "maxDistance": str(max_distance),
        }
        data = self._send_get_request("/schedule/stops/nearest", params)
        return [DistanceToStop(**stop) for stop in data]

    def get_stop(self, stop_id: str) -> Stop | None:
        """Retrieve details of a specific stop by its ID.

        Args:
            stop_id (str): The unique identifier of the stop.

        Returns:
            Stop | None: A Stop object if found, otherwise None.
        """
        data = self._send_get_request(f"/schedule/stops/{stop_id}")
        return Stop(**data) if data else None

    def get_next_departures(
        self,
        stop: str | Stop,
        departure: datetime | None = None,
        limit: int = 10,
        until: datetime | None = None,
    ) -> list[Departure]:
        """Retrieve the next departures from a specific stop.

        Args:
            stop (str | Stop): The stop ID or Stop object to get departures from.
            departure (datetime, optional): The starting time for the departures search. Defaults to None (=now).
            limit (int, optional): The maximum number of departures to return. Defaults to 10.
            until (datetime, optional): The end time for the departures search. Defaults to None.

        Returns:
            list[Departure]: A list of Departure objects.
        """
        stop_id = stop.id if isinstance(stop, Stop) else stop
        params = {"limit": str(limit)}
        if departure:
            params["departureDateTime"] = departure.strftime("%Y-%m-%dT%H:%M:%S")
        if until:
            params["untilDateTime"] = until.strftime("%Y-%m-%dT%H:%M:%S")

        data = self._send_get_request(f"/schedule/stops/{stop_id}/departures", params)
        return [Departure(**dep) for dep in data]

    def get_router_info(self) -> RouterInfo:
        """Retrieve information about the routing API."""
        data = self._send_get_request("/routing")
        return RouterInfo(**data)

    def get_connections(
        self,
        source: Stop | Coordinate | str | tuple[float, float],
        target: str | Stop | Coordinate | tuple[float, float],
        time: datetime | None = None,
        time_type: TimeType = TimeType.DEPARTURE,
        query_config: QueryConfig | None = None,
    ) -> list[Connection]:
        """Retrieve a list of possible connections between two stops and or locations.

        Args:
            source (Stop | Coordinate | str | tuple[float, float]): The starting Stop object, Coordinate object, Stop ID or
                Coordinates tuple.
            target (Stop | Coordinate | str | tuple[float, float]): The destination Stop object, Coordinate object,
                Stop ID or Coordinates tuple.
            time (datetime, optional): The time for the connection search. Defaults to None (=now).
            time_type (TimeType, optional): Whether the time is for departure or arrival. Defaults to DEPARTURE.
            query_config (QueryConfig, optional): Additional query configuration. Defaults to None.

        Returns:
            list[Connection]: A list of Connection objects representing the possible routes.
        """
        params = self._build_params_dict(
            source,
            target,
            time=time,
            time_type=time_type,
            query_config=query_config,
        )
        data = self._send_get_request("/routing/connections", params)
        return [Connection(**conn) for conn in data]

    def get_isolines(
        self,
        source: Stop | Coordinate | str | tuple[float, float],
        time: datetime | None = None,
        time_type: TimeType = TimeType.DEPARTURE,
        query_config: QueryConfig | None = None,
        return_connections: bool = False,
    ) -> list[StopConnection]:
        """Retrieve isolines (areas reachable within a certain time) from a specific stop / location.

        Args:
            source (Stop | Coordinate | str | tuple[float, float]): The starting Stop object, Coordinate object, Stop ID or
                Coordinates tuple.
            time (datetime, optional): The time for the isoline calculation. Defaults to None (=now).
            time_type (TimeType, optional): Whether the time is for departure or arrival. Defaults to DEPARTURE.
            query_config (QueryConfig, optional): Additional query configuration. Defaults to None.
            return_connections (bool, optional): Whether to return detailed connections. Defaults to False.

        Returns:
            list[StopConnection]: A list of StopConnection objects representing the reachable areas.
        """
        params = self._build_params_dict(
            source,
            time=time,
            time_type=time_type,
            query_config=query_config,
        )

        if return_connections:
            params["returnConnections"] = "true"

        data = self._send_get_request("/routing/isolines", params)
        return [StopConnection(**stop_conn) for stop_conn in data]

    @staticmethod
    def _build_params_dict(
        source: Stop | Coordinate | str | tuple[float, float],
        target: str | Stop | Coordinate | tuple[float, float] | None = None,
        time: datetime | None = None,
        time_type: TimeType | None = None,
        query_config: QueryConfig | None = None,
    ) -> dict[str, Any]:

        if isinstance(source, Stop):
            source = source.id
        elif isinstance(source, Coordinate):
            source = source.to_tuple()

        if isinstance(target, Stop):
            target = target.id
        elif isinstance(target, Coordinate):
            target = target.to_tuple()

        params: dict[str, Any] = {
            "dateTime": (datetime.now() if time is None else time).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
        }

        if isinstance(source, tuple):
            params["sourceLatitude"] = str(source[0])
            params["sourceLongitude"] = str(source[1])
        elif isinstance(source, str):
            params["sourceStopId"] = source

        if target is not None:
            if isinstance(target, tuple):
                params["targetLatitude"] = str(target[0])
                params["targetLongitude"] = str(target[1])
            elif isinstance(target, str):
                params["targetStopId"] = target

        if time_type:
            params["timeType"] = time_type.value

        if query_config is None:
            return params

        if query_config.max_walking_duration is not None:
            params["maxWalkingDuration"] = str(query_config.max_walking_duration)
        if query_config.max_num_transfers is not None:
            params["maxTransferNumber"] = str(query_config.max_num_transfers)
        if query_config.max_travel_time is not None:
            params["maxTravelTime"] = str(query_config.max_travel_time)
        if query_config.min_transfer_duration is not None:
            params["minTransferTime"] = str(query_config.min_transfer_duration)
        if query_config.accessibility is not None:
            params["wheelchairAccessible"] = str(query_config.accessibility).lower()
        if query_config.bikes is not None:
            params["bikesAllowed"] = str(query_config.bikes).lower()
        if query_config.travel_modes is not None:
            params["travelModes"] = [mode.value for mode in query_config.travel_modes]

        return params
