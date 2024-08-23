from datetime import datetime, date

import pytest

from public_transit_client.client import (
    PublicTransitClient,
    PublicTransitClientException,
)
from public_transit_client.model import (
    Connection,
    Coordinate,
    StopConnection,
    TimeType,
    QueryConfig,
    TransportMode,
    RouterInfo,
    ScheduleInfo,
)

HOST = "http://localhost:8080"


@pytest.fixture(scope="module")
def client():
    return PublicTransitClient(host=HOST)


@pytest.mark.integration
def test_get_schedule_info(client):
    schedule_info = client.get_schedule_info()
    assert isinstance(schedule_info, ScheduleInfo)
    assert schedule_info.has_accessibility is False
    assert schedule_info.has_bikes is False
    assert schedule_info.has_travel_modes is True
    start_date = date(2007, 1, 1)
    end_date = date(2010, 12, 31)
    assert schedule_info.schedule_validity.start_date == start_date
    assert schedule_info.schedule_validity.end_date == end_date


@pytest.mark.integration
def test_get_router_info(client):
    router_info = client.get_router_info()
    assert isinstance(router_info, RouterInfo)
    assert router_info.supports_accessibility is False
    assert router_info.supports_bikes is False
    assert router_info.supports_travel_modes is True
    assert router_info.supports_max_travel_time is True
    assert router_info.supports_min_transfer_duration is True
    assert router_info.supports_max_num_transfers is True
    assert router_info.supports_max_walking_duration is True


@pytest.mark.integration
def test_get_connections(client):
    from_stop = "NANAA"
    to_stop = "BULLFROG"
    departure_time = datetime(2008, 6, 1)
    connections = client.get_connections(
        source=from_stop,
        target=to_stop,
        time=departure_time,
        time_type=TimeType.DEPARTURE,
    )

    assert isinstance(connections, list)
    assert len(connections) > 0
    assert all(isinstance(connection, Connection) for connection in connections)
    assert connections[0].from_stop.id == from_stop
    assert connections[0].to_stop.id == to_stop


@pytest.mark.integration
def test_get_connections_invalid_stop(client):
    from_stop = "INVALID_STOP"
    to_stop = "BULLFROG"
    departure_time = datetime(2008, 6, 1)

    with pytest.raises(PublicTransitClientException) as exc_info:
        client.get_connections(
            source=from_stop,
            target=to_stop,
            time=departure_time,
            time_type=TimeType.DEPARTURE,
        )

    assert exc_info.value.api_error.status == 404
    assert "'INVALID_STOP' was not found" in exc_info.value.api_error.message


@pytest.mark.integration
def test_get_connections_negative_walking_duration(client):
    from_stop = "NANAA"
    to_stop = "BULLFROG"
    departure_time = datetime(2008, 6, 1)

    with pytest.raises(PublicTransitClientException) as exc_info:
        client.get_connections(
            source=from_stop,
            target=to_stop,
            time=departure_time,
            time_type=TimeType.DEPARTURE,
            query_config=QueryConfig(max_walking_duration=-1),
        )

    assert exc_info.value.api_error.status == 400
    assert (
        "Max walking duration must be greater than or equal to 0"
        in exc_info.value.api_error.message
    )


@pytest.mark.integration
def test_get_connections_unsupported_accessibility(client):
    from_stop = "NANAA"
    to_stop = "BULLFROG"
    departure_time = datetime(2008, 6, 1)

    with pytest.raises(PublicTransitClientException) as exc_info:
        client.get_connections(
            source=from_stop,
            target=to_stop,
            time=departure_time,
            time_type=TimeType.DEPARTURE,
            query_config=QueryConfig(accessibility=True),
        )

    assert exc_info.value.api_error.status == 400
    assert (
        "Wheelchair Accessible routing is not supported by the router of this service."
        in exc_info.value.api_error.message
    )


@pytest.mark.integration
def test_get_isolines(client):
    from_stop = "NANAA"
    departure_time = datetime(2008, 6, 1)
    isolines = client.get_isolines(
        source=from_stop,
        time=departure_time,
        time_type=TimeType.DEPARTURE,
        query_config=QueryConfig(
            max_walking_duration=10,
            max_transfer_number=1,
            travel_modes=[TransportMode.BUS, TransportMode.TRAM],
        ),
        return_connections=True,
    )

    assert isinstance(isolines, list)
    assert len(isolines) > 0
    assert all(
        isinstance(stop_connection, StopConnection) for stop_connection in isolines
    )


@pytest.mark.integration
def test_get_isolines_not_available_travel_modes(client):
    from_stop = "NANAA"
    departure_time = datetime(2008, 6, 1)
    isolines = client.get_isolines(
        source=from_stop,
        time=departure_time,
        time_type=TimeType.DEPARTURE,
        query_config=QueryConfig(
            max_walking_duration=10,
            max_transfer_number=1,
            travel_modes=[TransportMode.TRAM, TransportMode.AERIAL_LIFT],
        ),
        return_connections=True,
    )

    assert isinstance(isolines, list)
    assert len(isolines) == 0


@pytest.mark.integration
def test_get_isolines_invalid_stop(client):
    from_stop = "INVALID_STOP"
    departure_time = datetime(2008, 6, 1)

    with pytest.raises(PublicTransitClientException) as exc_info:
        client.get_isolines(
            source=from_stop,
            time=departure_time,
            time_type=TimeType.DEPARTURE,
            query_config=QueryConfig(
                max_walking_duration=10,
                max_transfer_number=1,
            ),
            return_connections=True,
        )

    assert exc_info.value.api_error.status == 404
    assert "'INVALID_STOP' was not found" in exc_info.value.api_error.message


@pytest.mark.integration
def test_nearest_stops_invalid_coordinate(client):
    invalid_coordinate = Coordinate(latitude=999.0, longitude=999.0)

    with pytest.raises(PublicTransitClientException) as exc_info:
        client.nearest_stops(coordinate=invalid_coordinate, limit=5, max_distance=500)

    assert exc_info.value.api_error.status == 400
    assert (
        "Latitude must be between -90 and 90 degrees"
        in exc_info.value.api_error.message
    )
