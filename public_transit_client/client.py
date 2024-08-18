import logging
from datetime import datetime
from typing import List, Optional

import requests
from requests import Response

from public_transit_client.model import (
    SearchType,
    Stop,
    Coordinate,
    Departure,
    Connection,
    StopConnection,
    DistanceToStop,
    TimeType,
    APIError
)

LOG = logging.getLogger(__name__)


class PublicTransitClientException(Exception):
    def __init__(self, api_error: APIError):
        self.api_error = api_error
        super().__init__(f"API Error {api_error.status}: {api_error.message}")


class PublicTransitClient:

    def __init__(self, host: str):
        self.host = host

    def _send_get_request(self, endpoint: str, params: Optional[dict] = None):
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

    def search_stops(self, query: str, limit: int = 10, search_type: SearchType = SearchType.CONTAINS) -> List[Stop]:
        params = {
            "query": query,
            "limit": limit,
            "searchType": search_type.name
        }
        data = self._send_get_request("/schedule/stops/autocomplete", params)
        return [Stop(**stop) for stop in data]

    def nearest_stops(self, coordinate: Coordinate, limit: int = 10, max_distance: int = 1000) -> List[DistanceToStop]:
        params = {
            "latitude": coordinate.latitude,
            "longitude": coordinate.longitude,
            "limit": limit,
            "maxDistance": max_distance,
        }
        data = self._send_get_request("/schedule/stops/nearest", params)
        return [DistanceToStop(**stop) for stop in data]

    def get_stop(self, stop_id: str) -> Stop | None:
        data = self._send_get_request(f"/schedule/stops/{stop_id}")
        return Stop(**data) if data else None

    def get_next_departures(self, stop: str | Stop, departure: datetime | None = None, limit: int = 10,
                            until: datetime | None = None) -> List[Departure]:
        stop_id = stop.id if isinstance(stop, Stop) else stop
        params = {"limit": limit}
        if departure:
            params["departureDateTime"] = departure.strftime('%Y-%m-%dT%H:%M:%S')
        if until:
            params["untilDateTime"] = until.strftime('%Y-%m-%dT%H:%M:%S')

        data = self._send_get_request(f"/schedule/stops/{stop_id}/departures", params)
        return [Departure(**dep) for dep in data]

    def get_connections(self, from_stop: str | Stop, to_stop: str | Stop, time: datetime | None = None,
                        time_type: TimeType = TimeType.DEPARTURE, max_walking_duration: int | None = None,
                        max_transfer_number: int | None = None, max_travel_time: int | None = None,
                        min_transfer_time: int | None = None) -> List[Connection]:
        params = self._build_params_dict(
            from_stop,
            to_stop,
            time=time,
            time_type=time_type,
            max_walking_duration=max_walking_duration,
            max_transfer_number=max_transfer_number,
            max_travel_time=max_travel_time,
            min_transfer_time=min_transfer_time,
        )
        data = self._send_get_request("/routing/connections", params)
        return [Connection(**conn) for conn in data]

    def get_isolines(self, from_stop: str | Stop, time: datetime | None = None,
                     time_type: TimeType = TimeType.DEPARTURE, max_walking_duration: int | None = None,
                     max_transfer_number: int | None = None, max_travel_time: int | None = None,
                     min_transfer_time: int | None = None, return_connections: bool = False) -> List[StopConnection]:
        params = self._build_params_dict(
            from_stop,
            time=time,
            time_type=time_type,
            max_walking_duration=max_walking_duration,
            max_transfer_number=max_transfer_number,
            max_travel_time=max_travel_time,
            min_transfer_time=min_transfer_time,
        )

        if return_connections:
            params["returnConnections"] = "true"

        data = self._send_get_request("/routing/isolines", params)
        return [StopConnection(**stop_conn) for stop_conn in data]

    @staticmethod
    def _build_params_dict(from_stop: str | Stop, to_stop: str | Stop | None = None, time: datetime | None = None,
                           time_type: TimeType | None = None, max_walking_duration: int | None = None,
                           max_transfer_number: int | None = None, max_travel_time: int | None = None,
                           min_transfer_time: int | None = None) -> dict:
        params = {
            "sourceStopId": from_stop.id if isinstance(from_stop, Stop) else from_stop,
            "dateTime": (datetime.now() if time is None else time).strftime('%Y-%m-%dT%H:%M:%S')
        }
        if to_stop:
            params["targetStopId"] = to_stop.id if isinstance(to_stop, Stop) else to_stop
        if time_type:
            params["timeType"] = time_type.value
        if max_walking_duration is not None:
            params["maxWalkingDuration"] = max_walking_duration
        if max_transfer_number is not None:
            params["maxTransferNumber"] = max_transfer_number
        if max_travel_time is not None:
            params["maxTravelTime"] = max_travel_time
        if min_transfer_time is not None:
            params["minTransferTime"] = min_transfer_time

        return params
