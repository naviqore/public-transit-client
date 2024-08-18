from datetime import datetime

from requests import get, Response

from public_transit_client.model import (
    SearchType,
    Stop,
    Coordinate,
    Departure,
    Connection,
    StopConnection,
    DistanceToStop,
    TimeType,
)


class PublicTransitClient:

    def __init__(self, host: str):
        self.host = host

    def search_stops(
            self, query: str, limit: int = 10, search_type: SearchType = SearchType.CONTAINS
    ) -> list[Stop]:
        url = (
            f"{self.host}/schedule/stops/autocomplete"
            f"?query={query}&limit={limit}&searchType={search_type.name}"
        )
        response: Response = get(url)
        if response.status_code == 200:
            return [Stop(**stop) for stop in response.json()]
        else:
            return []

    def nearest_stops(
            self, coordinate: Coordinate, limit: int = 10, max_distance: int = 1000
    ) -> list[DistanceToStop]:
        url = (
            f"{self.host}/schedule/stops/nearest?latitude={coordinate.latitude}"
            f"&longitude={coordinate.longitude}&limit={limit}&maxDistance={max_distance}"
        )
        response = get(url)
        if response.status_code == 200:
            return [DistanceToStop(**stop) for stop in response.json()]
        else:
            return []

    def get_stop(self, stop_id: str) -> Stop | None:
        url = f"{self.host}/schedule/stops/{stop_id}"
        response = get(url)
        if response.status_code == 200:
            return Stop(**response.json())
        else:
            return None

    def get_next_departures(
            self,
            stop: str | Stop,
            departure: datetime | None = None,
            limit: int = 10,
            until: datetime | None = None,
    ) -> list[Departure]:
        stop_id = stop.id if isinstance(stop, Stop) else stop
        url = f"{self.host}/schedule/stops/{stop_id}/departures?limit={limit}"
        if departure is not None:
            url += f"&departureDateTime={departure.strftime('%Y-%m-%dT%H:%M:%S')}"
        if until is not None:
            url += f"&untilDateTime={until.strftime('%Y-%m-%dT%H:%M:%S')}"
        response = get(url)
        if response.status_code == 200:
            return [Departure(**departure) for departure in response.json()]
        else:
            return []

    def get_connections(
            self,
            from_stop: str | Stop,
            to_stop: str | Stop,
            time: datetime | None = None,
            time_type: TimeType = TimeType.DEPARTURE,
            max_walking_duration: int | None = None,
            max_transfer_number: int | None = None,
            max_travel_time: int | None = None,
            min_transfer_time: int | None = None,
    ) -> list[Connection]:
        query_string = self._build_query_string(
            from_stop,
            to_stop,
            time=time,
            time_type=time_type,
            max_walking_duration=max_walking_duration,
            max_transfer_number=max_transfer_number,
            max_travel_time=max_travel_time,
            min_transfer_time=min_transfer_time,
        )
        url = f"{self.host}/routing/connections?{query_string}"
        response = get(url)
        if response.status_code == 200:
            return [Connection(**connection) for connection in response.json()]
        else:
            return []

    def get_isolines(
            self,
            from_stop: str | Stop,
            time: datetime | None = None,
            time_type: TimeType = TimeType.DEPARTURE,
            max_walking_duration: int | None = None,
            max_transfer_number: int | None = None,
            max_travel_time: int | None = None,
            min_transfer_time: int | None = None,
            return_connections: bool = False,
    ) -> list[StopConnection]:
        query_string = self._build_query_string(
            from_stop,
            time=time,
            time_type=time_type,
            max_walking_duration=max_walking_duration,
            max_transfer_number=max_transfer_number,
            max_travel_time=max_travel_time,
            min_transfer_time=min_transfer_time,
        )

        url = f"{self.host}/routing/isolines?{query_string}"

        if return_connections:
            url += "&returnConnections=true"

        response = get(url)
        if response.status_code == 200:
            return [
                StopConnection(**stopConnection) for stopConnection in response.json()
            ]
        else:
            return []

    @staticmethod
    def _build_query_string(
            from_stop: str | Stop,
            to_stop: str | Stop | None = None,
            time: datetime | None = None,
            time_type: TimeType | None = None,
            max_walking_duration: int | None = None,
            max_transfer_number: int | None = None,
            max_travel_time: int | None = None,
            min_transfer_time: int | None = None,
    ) -> str:
        query_string = (
            f"sourceStopId={from_stop.id if isinstance(from_stop, Stop) else from_stop}"
        )
        if to_stop is not None:
            query_string += (
                f"&targetStopId={to_stop.id if isinstance(to_stop, Stop) else to_stop}"
            )
        date_time = datetime.now() if time is None else time
        query_string += f"&dateTime={date_time.strftime('%Y-%m-%dT%H:%M:%S')}"
        if time_type is not None:
            query_string += f"&timeType={time_type.value}"
        if max_walking_duration is not None:
            query_string += f"&maxWalkingDuration={max_walking_duration}"
        if max_transfer_number is not None:
            query_string += f"&maxTransferNumber={max_transfer_number}"
        if max_travel_time is not None:
            query_string += f"&maxTravelTime={max_travel_time}"
        if min_transfer_time is not None:
            query_string += f"&minTransferTime={min_transfer_time}"

        return query_string
