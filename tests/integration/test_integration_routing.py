from datetime import datetime

import pytest

from public_transit_client.client import (
    PublicTransitClient,
    PublicTransitClientException,
)
from public_transit_client.model import Connection, Coordinate, StopConnection, TimeType, QueryConfig

HOST = "http://localhost:8080"


@pytest.fixture(scope="module")
def client():
    return PublicTransitClient(host=HOST)


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
        ),
        return_connections=True,
    )

    assert isinstance(isolines, list)
    assert len(isolines) > 0
    assert all(
        isinstance(stop_connection, StopConnection) for stop_connection in isolines
    )


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
