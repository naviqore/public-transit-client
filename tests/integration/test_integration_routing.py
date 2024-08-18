from datetime import datetime

import pytest

from public_transit_client.client import PublicTransitClient
from public_transit_client.model import TimeType, Connection, StopConnection

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
        from_stop=from_stop,
        to_stop=to_stop,
        time=departure_time,
        time_type=TimeType.DEPARTURE
    )

    assert isinstance(connections, list)
    assert len(connections) > 0
    assert all(isinstance(connection, Connection) for connection in connections)
    assert connections[0].fromStop.id == from_stop
    assert connections[0].toStop.id == to_stop


@pytest.mark.integration
def test_get_isolines(client):
    from_stop = "NANAA"
    departure_time = datetime(2008, 6, 1)
    isolines = client.get_isolines(
        from_stop=from_stop,
        time=departure_time,
        time_type=TimeType.DEPARTURE,
        max_walking_duration=10,
        max_transfer_number=1,
        return_connections=True
    )

    assert isinstance(isolines, list)
    assert len(isolines) > 0
    assert all(isinstance(stop_connection, StopConnection) for stop_connection in isolines)
