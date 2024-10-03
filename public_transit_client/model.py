from datetime import date, datetime
from enum import Enum
from itertools import pairwise

from geopy import distance  # type: ignore
from pydantic import BaseModel, Field, field_validator


class SearchType(Enum):
    """Enum for specifying the type of search."""

    EXACT = "EXACT"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"


class LegType(Enum):
    """Enum for specifying the type of leg in a journey."""

    WALK = "WALK"
    ROUTE = "ROUTE"


class TimeType(Enum):
    """Enum for specifying the type of time defined in a connection query (departure or arrival)."""

    DEPARTURE = "DEPARTURE"
    ARRIVAL = "ARRIVAL"


class TransportMode(Enum):
    """Enum for specifying the mode of transport."""

    BUS = "BUS"
    TRAM = "TRAM"
    RAIL = "RAIL"
    SHIP = "SHIP"
    SUBWAY = "SUBWAY"
    AERIAL_LIFT = "AERIAL_LIFT"
    FUNICULAR = "FUNICULAR"


class APIError(BaseModel):
    """Model representing an API error.

    Attributes:
        timestamp (datetime): The time when the error occurred.
        status (int): The HTTP status code of the error.
        error (str): The error message.
        path (str): The path where the error occurred.
        message (str): A detailed message about the error.
    """

    timestamp: datetime
    status: int
    error: str
    path: str
    message: str


class ScheduleValidity(BaseModel):
    """Model representing the validity of a schedule.

    Attributes:
        start_date (date): The start date of the schedule.
        end_date (date): The end date of the schedule.
    """

    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")

    def is_date_valid(self, reference_date: date) -> bool:
        """Check if a date is within the validity range.

        Args:
            reference_date (date): The date to check.

        Returns:
            bool: True if the date is within the range, False otherwise.
        """
        return self.start_date <= reference_date <= self.end_date


class ScheduleInfo(BaseModel):
    """Model representing schedule information.

    Attributes:
        has_accessibility (bool): Indicates if the schedule has accessibility information.
        has_bikes (bool): Indicates if the schedule has bike information.
        has_travel_modes (bool): Indicates if the schedule has travel mode information.
        schedule_validity (ScheduleValidity): The validity of the schedule.
    """

    has_accessibility: bool = Field(alias="hasAccessibility")
    has_bikes: bool = Field(alias="hasBikes")
    has_travel_modes: bool = Field(alias="hasTravelModes")
    schedule_validity: ScheduleValidity = Field(alias="scheduleValidity")


class RouterInfo(BaseModel):
    """Model representing information about the router.

    Attributes:
        supports_max_num_transfers (bool): Indicates if the router supports maximum number of transfers.
        supports_max_travel_time (bool): Indicates if the router supports maximum travel time.
        supports_max_walking_duration (bool): Indicates if the router supports maximum walking duration.
        supports_min_transfer_duration (bool): Indicates if the router supports minimum transfer duration.
        supports_accessibility (bool): Indicates if the router supports accessibility.
        supports_bikes (bool): Indicates if the router supports bikes.
        supports_travel_modes (bool): Indicates if the router supports travel modes.
    """

    supports_max_num_transfers: bool = Field(alias="supportsMaxNumTransfers")
    supports_max_travel_time: bool = Field(alias="supportsMaxTravelTime")
    supports_max_walking_duration: bool = Field(alias="supportsMaxWalkingDuration")
    supports_min_transfer_duration: bool = Field(alias="supportsMinTransferDuration")
    supports_accessibility: bool = Field(alias="supportsAccessibility")
    supports_bikes: bool = Field(alias="supportsBikes")
    supports_travel_modes: bool = Field(alias="supportsTravelModes")


class QueryConfig(BaseModel):
    """Model representing configuration for a query.

    Attributes:
        max_num_transfers (int | None): The maximum number of transfers allowed.
        max_travel_time (int | None): The maximum travel time allowed.
        max_walking_duration (int | None): The maximum walking duration allowed.
        min_transfer_duration (int | None): The minimum transfer duration allowed.
        accessibility (bool | None): Indicates if accessibility is required.
        bikes (bool | None): Indicates if bikes are allowed.
        travel_modes (list[TransportMode] | None): A list of allowed travel modes.
    """

    max_num_transfers: int | None = None
    max_travel_time: int | None = None
    max_walking_duration: int | None = None
    min_transfer_duration: int | None = None
    accessibility: bool | None = None
    bikes: bool | None = None
    travel_modes: list[TransportMode] | None = None


class Coordinate(BaseModel):
    """Model representing geographical coordinates.

    Attributes:
        latitude (float): The latitude of the coordinate.
        longitude (float): The longitude of the coordinate.
    """

    latitude: float
    longitude: float

    def distance_to(self, other: "Coordinate") -> float:
        """Calculate the distance to another Coordinate.

        Args:
            other (Coordinate): The other coordinate to calculate distance to.

        Returns:
            float: The distance in meters.
        """
        return float(
            distance.distance(
                (self.latitude, self.longitude),
                (other.latitude, other.longitude),
            ).meters
        )

    def to_tuple(self) -> tuple[float, float]:
        """Convert the Coordinate to a tuple.

        Returns:
            tuple[float, float]: The coordinate as a (latitude, longitude) tuple.
        """
        return self.latitude, self.longitude


class Stop(BaseModel):
    """Model representing a public transport stop.

    Attributes:
        id (str): The unique identifier of the stop.
        name (str): The name of the stop.
        coordinate (Coordinate): The geographical coordinate of the stop.
    """

    id: str
    name: str
    coordinate: Coordinate = Field(alias="coordinates")


class Route(BaseModel):
    """Model representing a public transport route.

    Attributes:
        id (str): The unique identifier of the route.
        name (str): The name of the route.
        short_name (str): The short name of the route.
        transport_mode (TransportMode): The mode of transport (e.g., BUS, TRAIN).
        transport_mode_description (str): A more detailed description of the transport mode.
    """

    id: str
    name: str
    short_name: str = Field(alias="shortName")
    transport_mode: TransportMode = Field(alias="transportMode")
    transport_mode_description: str = Field(alias="transportModeDescription")


class StopTime(BaseModel):
    """Model representing a stop time for a particular route.

    Attributes:
        stop (Stop): The stop associated with the stop time.
        arrival_time (datetime): The arrival time at the stop.
        departure_time (datetime): The departure time from the stop.
    """

    stop: Stop
    arrival_time: datetime = Field(alias="arrivalTime")
    departure_time: datetime = Field(alias="departureTime")


class Trip(BaseModel):
    """Model representing a public transport trip.

    Attributes:
        head_sign (str): The head sign of the trip.
        route (Route): The route associated with the trip.
        stop_times (list[StopTime]): A list of stop times for the trip.
        bikes_allowed (bool): Indicates if bikes are allowed on the trip.
        wheelchair_accessible (bool): Indicates if the trip is wheelchair accessible.
    """

    head_sign: str = Field(alias="headSign")
    route: Route
    stop_times: list[StopTime] = Field(alias="stopTimes")
    bikes_allowed: bool = Field(alias="bikesAllowed")
    wheelchair_accessible: bool = Field(alias="wheelchairAccessible")

    @field_validator("stop_times", mode="before")
    def _set_stop_times_not_none(cls, v: list[StopTime] | None) -> list[StopTime]:
        return v or []


class Departure(BaseModel):
    """Model representing a departure event.

    Attributes:
        stop_time (StopTime): The stop time associated with the departure.
        trip (Trip): The trip associated with the departure.
    """

    stop_time: StopTime = Field(alias="stopTime")
    trip: Trip


class Leg(BaseModel):
    """Model representing a leg of a journey.

    Attributes:
        from_coordinate (Coordinate): The starting coordinate of the leg.
        from_stop (Stop | None): The starting stop of the leg (if applicable).
        to_coordinate (Coordinate): The ending coordinate of the leg.
        to_stop (Stop | None): The ending stop of the leg (if applicable).
        type (LegType): The type of the leg (WALK or ROUTE).
        departure_time (datetime): The departure time for the leg.
        arrival_time (datetime): The arrival time for the leg.
        trip (Trip | None): The trip associated with the leg (if applicable).
    """

    from_coordinate: Coordinate = Field(alias="from")
    from_stop: Stop | None = Field(alias="fromStop", default=None)
    to_coordinate: Coordinate = Field(alias="to")
    to_stop: Stop | None = Field(alias="toStop", default=None)
    type: LegType
    departure_time: datetime = Field(alias="departureTime")
    arrival_time: datetime = Field(alias="arrivalTime")
    trip: Trip | None = None

    @property
    def duration(self) -> int:
        """Calculate the duration of the leg in seconds.

        Returns:
            int: The duration in seconds.
        """
        return (self.arrival_time - self.departure_time).seconds

    @property
    def distance(self) -> float:
        """Calculate the distance of the leg.

        Returns:
            float: The distance in meters.
        """
        return self.from_coordinate.distance_to(self.to_coordinate)

    @property
    def is_walk(self) -> bool:
        """Check if the leg is a walking leg.

        Returns:
            bool: True if the leg is a walking leg, False otherwise.
        """
        return self.type == LegType.WALK

    @property
    def is_route(self) -> bool:
        """Check if the leg is a route leg.

        Returns:
            bool: True if the leg is a route leg, False otherwise.
        """
        return self.type == LegType.ROUTE

    @property
    def num_stops(self) -> int:
        """Calculate the number of stops between the starting and ending stops of the leg.

        Returns:
            int: The number of stops.

        Raises:
            ValueError: If from_stop or to_stop is not found in the trip.
        """
        if self.trip is None or not self.is_route:
            return 0

        # get index of from_stop and to_stop
        from_stop_index = None
        to_stop_index = None
        for i, stop_time in enumerate(self.trip.stop_times):
            if stop_time.stop == self.from_stop:
                from_stop_index = i
            if stop_time.stop == self.to_stop:
                to_stop_index = i
                break

        if from_stop_index is None or to_stop_index is None:
            raise ValueError("from_stop or to_stop not found in trip")
        return to_stop_index - from_stop_index


class Connection(BaseModel):
    """Model representing a journey connection consisting of multiple legs.

    Attributes:
        legs (list[Leg]): A list of legs that make up the connection.
    """

    legs: list[Leg]

    @field_validator("legs")
    def _legs_not_empty(cls, v: list[Leg]) -> list[Leg]:
        if not v:
            raise ValueError("legs must not be empty")
        return v

    @property
    def first_leg(self) -> Leg:
        """Get the first leg of the connection.

        Returns:
            Leg: The first leg.
        """
        return self.legs[0]

    @property
    def last_leg(self) -> Leg:
        """Get the last leg of the connection.

        Returns:
            Leg: The last leg.
        """
        return self.legs[-1]

    @property
    def first_route_leg(self) -> Leg | None:
        """Get the first route leg of the connection.

        Returns:
            Leg | None: The first route leg, or None if no route legs exist.
        """
        for leg in self.legs:
            if leg.is_route:
                return leg

        return None

    @property
    def last_route_leg(self) -> Leg | None:
        """Get the last route leg of the connection.

        Returns:
            Leg | None: The last route leg, or None if no route legs exist.
        """
        for leg in reversed(self.legs):
            if leg.is_route:
                return leg

        return None

    @property
    def first_stop(self) -> Stop | None:
        """Get the first stop of the connection.

        Returns:
            Stop | None: The first stop, or None if no stop is passed.
        """
        first_route_leg = self.first_route_leg
        return first_route_leg.from_stop if first_route_leg else None

    @property
    def last_stop(self) -> Stop | None:
        """Get the last stop of the connection.

        Returns:
            Stop | None: The last stop, or None if no stop is passed.
        """
        last_route_leg = self.last_route_leg
        return last_route_leg.to_stop if last_route_leg else None

    @property
    def departure_time(self) -> datetime:
        """Get the departure time of the connection.

        Returns:
            datetime: The departure time.
        """
        return self.first_leg.departure_time

    @property
    def arrival_time(self) -> datetime:
        """Get the arrival time of the connection.

        Returns:
            datetime: The arrival time.
        """
        return self.last_leg.arrival_time

    @property
    def from_coordinate(self) -> Coordinate:
        """Get the starting coordinate of the connection.

        Returns:
            Coordinate: The starting coordinate.
        """
        return self.first_leg.from_coordinate

    @property
    def to_coordinate(self) -> Coordinate:
        """Get the ending coordinate of the connection.

        Returns:
            Coordinate: The ending coordinate.
        """
        return self.last_leg.to_coordinate

    @property
    def from_stop(self) -> Stop | None:
        """Get the starting stop of the connection.

        Returns:
            Stop | None: The starting stop, or None if connection does not start at stop.
        """
        return self.first_leg.from_stop

    @property
    def to_stop(self) -> Stop | None:
        """Get the ending stop of the connection.

        Returns:
            Stop | None: The ending stop, or None if connection does not end at stop.
        """
        return self.last_leg.to_stop

    @property
    def duration(self) -> int:
        """Calculate the duration of the connection in seconds.

        Returns:
            int: The duration in seconds.
        """
        return (self.arrival_time - self.departure_time).seconds

    @property
    def travel_duration(self) -> int:
        """Calculate the travel duration of the connection in seconds.

        The travel duration is the sum of the duration of all legs, excluding any waiting time.

        Returns:
            int: The travel duration in seconds.
        """
        return sum(leg.duration for leg in self.legs)

    @property
    def travel_distance(self) -> float:
        """Calculate the travel distance of the connection.

        The travel distance is the sum of the distance of all legs.

        Returns:
            float: The travel distance in meters.
        """
        return sum(leg.distance for leg in self.legs)

    @property
    def bee_line_distance(self) -> float:
        """Calculate the bee line distance of the connection.

        The bee line distance is the distance between the starting and ending coordinates.

        Returns:
            float: The bee line distance in meters.
        """
        return self.from_coordinate.distance_to(self.to_coordinate)

    @property
    def walk_distance(self) -> float:
        """Calculate the walking distance of the connection.

        Returns:
            float: The total walking distance in meters.
        """
        return sum(leg.distance for leg in self.legs if leg.is_walk)

    @property
    def route_distance(self) -> float:
        """Calculate the route distance of the connection.

        Returns:
            float: The total distance travelled on route legs in meters.
        """
        return sum(leg.distance for leg in self.legs if leg.is_route)

    @property
    def walk_duration(self) -> int:
        """Calculate the walking duration of the connection in seconds.

        Returns:
            int: The total walking duration in seconds.
        """
        return sum(leg.duration for leg in self.legs if leg.is_walk)

    @property
    def route_duration(self) -> int:
        """Calculate the route duration of the connection in seconds.

        Returns:
            int: The total duration travelled on route legs in seconds.
        """
        return sum(leg.duration for leg in self.legs if leg.is_route)

    @property
    def num_transfers(self) -> int:
        """Calculate the number of transfers in the connection.

        A transfer is counted when switching from a route leg to another route leg.

        Returns:
            int: The number of transfers.
        """
        return sum(1 for leg in self.legs if leg.is_route) - 1

    @property
    def num_same_station_transfers(self) -> int:
        """Calculate the number of same station transfers in the connection.

        A same station transfer is counted when switching from a route leg to another route leg at the same stop.
        With no intermediate walking legs between the route legs.

        Returns:
            int: The number of same station transfers.
        """
        return sum(
            1
            for prev_leg, current_leg in pairwise(self.legs)
            if prev_leg.is_route and current_leg.is_route
        )

    @property
    def num_stops(self) -> int:
        """Calculate the number of stops in the connection.

        Returns:
            int: The number of stops.
        """
        return sum(leg.num_stops for leg in self.legs if leg.is_route)

    @property
    def multi_date(self) -> bool:
        """Check if the connection spans multiple dates.

        Returns:
            bool: True if the connection spans multiple dates, False otherwise.
        """
        return self.departure_time.date() != self.arrival_time.date()


class StopConnection(BaseModel):
    """Model representing a connection to a stop.

    Attributes:
        stop (Stop): The stop associated with the connection.
        connecting_leg (Leg): The leg connecting to the stop.
        connection (Connection | None): The connection to the stop.
    """

    stop: Stop
    connecting_leg: Leg = Field(alias="connectingLeg")
    connection: Connection | None = None


class DistanceToStop(BaseModel):
    """Model representing the distance to a stop.

    Attributes:
        stop (Stop): The stop.
        distance (float): The distance to the stop in meters.
    """

    stop: Stop
    distance: float
