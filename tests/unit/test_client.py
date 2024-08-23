from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from requests import Response

from public_transit_client.client import (
    PublicTransitClient,
    PublicTransitClientException,
)
from public_transit_client.model import (
    Connection,
    Coordinate,
    Departure,
    SearchType,
    Stop,
    StopConnection,
)


@pytest.fixture(scope="module")
def client():
    return PublicTransitClient(host="http://fakehost")


@pytest.mark.unit
def mock_response(status=200, json_data=None):
    mock_resp = Mock(spec=Response)
    mock_resp.status_code = status
    mock_resp.json.return_value = json_data
    return mock_resp


@pytest.mark.unit
def test_send_get_request_success(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(status=200, json_data={"key": "value"})

        response = client._send_get_request("/fake_endpoint")

        assert response == {"key": "value"}
        mock_get.assert_called_once_with("http://fakehost/fake_endpoint", params=None)


@pytest.mark.unit
def test_send_get_request_error(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(
            status=404,
            json_data={
                "timestamp": "2024-08-18T17:34:03.820509687",
                "status": 404,
                "error": "Not Found",
                "path": "/schedule/stops/NOT_EXISTING",
                "message": "The requested stop with ID 'NOT_EXISTING' was not found.",
            },
        )

        with pytest.raises(PublicTransitClientException) as exc_info:
            client._send_get_request("/fake_endpoint")

        assert (
            "API Error 404: The requested stop with ID 'NOT_EXISTING' was not found."
            in str(exc_info.value)
        )
        mock_get.assert_called_once_with("http://fakehost/fake_endpoint", params=None)


@pytest.mark.unit
def test_search_stops(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(
            status=200,
            json_data=[
                {
                    "id": "1",
                    "name": "Stop 1",
                    "coordinates": {"latitude": 36.0, "longitude": -116.0},
                }
            ],
        )

        stops = client.search_stops(query="e", limit=5, search_type=SearchType.CONTAINS)

        assert isinstance(stops, list)
        assert len(stops) == 1
        assert stops[0].id == "1"
        assert isinstance(stops[0], Stop)


@pytest.mark.unit
def test_nearest_stops(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(
            status=200,
            json_data=[
                {
                    "stop": {
                        "id": "1",
                        "name": "Stop 1",
                        "coordinates": {"latitude": 36.0, "longitude": -116.0},
                    },
                    "distance": 500,
                }
            ],
        )

        coordinate = Coordinate(latitude=36, longitude=-116)
        stops = client.nearest_stops(
            coordinate=coordinate, limit=3, max_distance=100000
        )

        assert isinstance(stops, list)
        assert len(stops) == 1
        assert stops[0].distance == 500
        assert isinstance(stops[0].stop, Stop)


@pytest.mark.unit
def test_get_stop(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(
            status=200,
            json_data={
                "id": "NANAA",
                "name": "Stop NANAA",
                "coordinates": {"latitude": 36.0, "longitude": -116.0},
            },
        )

        stop = client.get_stop(stop_id="NANAA")

        assert stop is not None
        assert stop.id == "NANAA"
        assert isinstance(stop, Stop)


@pytest.mark.unit
def test_get_next_departures(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(
            status=200,
            json_data=[
                {
                    "stopTime": {
                        "stop": {
                            "id": "1",
                            "name": "Stop 1",
                            "coordinates": {"latitude": 36.0, "longitude": -116.0},
                        },
                        "arrivalTime": "2024-08-18T17:34:03",
                        "departureTime": "2024-08-18T17:45:00",
                    },
                    "trip": {
                        "headSign": "Head Sign",
                        "route": {
                            "id": "1",
                            "name": "Route 1",
                            "shortName": "R1",
                            "transportMode": "BUS",
                            "transportModeDescription": "More Bus Details",
                        },
                        "stopTimes": [],
                        "bikesAllowed": True,
                        "wheelchairAccessible": True,
                    },
                }
            ],
        )

        departures = client.get_next_departures(
            stop="NANAA", departure=datetime(2024, 8, 18, 17, 0)
        )

        assert isinstance(departures, list)
        assert len(departures) == 1
        assert isinstance(departures[0], Departure)


@pytest.mark.unit
def test_get_connections(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(
            status=200,
            json_data=[
                {
                    "legs": [
                        {
                            "from": {"latitude": 36.0, "longitude": -116.0},
                            "to": {"latitude": 37.0, "longitude": -117.0},
                            "type": "ROUTE",
                            "departureTime": "2024-08-18T17:34:03",
                            "arrivalTime": "2024-08-18T18:00:00",
                        }
                    ]
                }
            ],
        )

        connections = client.get_connections(
            source="NANAA", target="BULLFROG", time=datetime(2024, 8, 18, 17, 0)
        )

        assert isinstance(connections, list)
        assert len(connections) == 1
        assert isinstance(connections[0], Connection)


@pytest.mark.unit
def test_get_isolines(client):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(
            status=200,
            json_data=[
                {
                    "stop": {
                        "id": "1",
                        "name": "Stop 1",
                        "coordinates": {"latitude": 36.0, "longitude": -116.0},
                    },
                    "connectingLeg": {
                        "from": {"latitude": 36.0, "longitude": -116.0},
                        "to": {"latitude": 37.0, "longitude": -117.0},
                        "type": "ROUTE",
                        "departureTime": "2024-08-18T17:34:03",
                        "arrivalTime": "2024-08-18T18:00:00",
                    },
                }
            ],
        )

        isolines = client.get_isolines(
            source="NANAA",
            time=datetime(2024, 8, 18, 17, 0),
            return_connections=True,
        )

        assert isinstance(isolines, list)
        assert len(isolines) == 1
        assert isinstance(isolines[0], StopConnection)
