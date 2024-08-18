import pytest

from public_transit_client.client import PublicTransitClient
from public_transit_client.model import Coordinate, SearchType, Stop

HOST = "http://localhost:8080"


@pytest.fixture(scope="module")
def client():
    return PublicTransitClient(host=HOST)


@pytest.mark.integration
def test_search_stops(client):
    stops = client.search_stops(query="e", limit=5, search_type=SearchType.CONTAINS)

    assert isinstance(stops, list)
    assert len(stops) > 0
    assert all(isinstance(stop, Stop) for stop in stops)


@pytest.mark.integration
def test_nearest_stops(client):
    coordinate = Coordinate(latitude=36, longitude=-116)
    stops = client.nearest_stops(coordinate=coordinate, limit=3, max_distance=100000)

    assert isinstance(stops, list)
    assert len(stops) > 0
    assert all(stop.distance >= 0 for stop in stops)
    assert all(isinstance(stop.stop, Stop) for stop in stops)


@pytest.mark.integration
def test_get_stop(client):
    stop_id = "NANAA"
    stop = client.get_stop(stop_id=stop_id)

    assert stop is not None
    assert isinstance(stop, Stop)
    assert stop.id == stop_id
