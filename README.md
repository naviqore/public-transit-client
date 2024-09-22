# Public Transit Client

Client to access the [Public Transit Service](https://github.com/naviqore/public-transit-service) API endpoints.

It is designed to interact seamlessly with the service, offering easy-to-use methods to query
transit information and connections.

## Installation

To install the package, you can use pip:

```sh
pip install public-transit-client
```

## Usage

Here's a basic example of how to use the client:

```python
from public_transit_client.client import PublicTransitClient

client = PublicTransitClient("http://localhost:8080")
response = client.get_stop("NANAA")
print(response)
```

See the integration tests for more examples.

## Testing

This project uses pytest for both unit and integration testing. The tests are organized into separate folders to ensure
clarity and separation of concerns.

### Unit Tests

Unit tests are designed to test individual components in isolation. To run the unit tests, simply execute:

```sh
poetry run pytest -m unit
```

### Integration Tests

Integration tests ensure that the components work together as expected in a more realistic environment. These tests
require the service to be running, usually within a Docker container.

**Step 1: Start the Docker Compose Environment**

First, start the necessary services using Docker Compose:

```sh
docker compose up -d
```

**Step 2: Run Integration Tests**

Once the services are up and running, execute the integration tests with:

```sh
poetry run pytest -m integration
```

### Coverage

To analyze the test coverage run:

```sh
poetry run pytest --cov=public_transit_client
```

## License

This project is licensed under the MIT License - see
the [LICENSE](https://github.com/naviqore/public-transit-client/blob/main/LICENSE) file for details.
