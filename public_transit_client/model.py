from datetime import datetime
from enum import Enum
from itertools import pairwise

from geopy import distance  # type: ignore
from pydantic import BaseModel, Field, field_validator


class SearchType(Enum):
    EXACT = "EXACT"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"


class LegType(Enum):
    WALK = "WALK"
    ROUTE = "ROUTE"


class TimeType(Enum):
    DEPARTURE = "DEPARTURE"
    ARRIVAL = "ARRIVAL"


class Coordinate(BaseModel):
    latitude: float
    longitude: float

    def distance_to(self, other: "Coordinate") -> float:
        return float(
            distance.distance(
                (self.latitude, self.longitude),
                (other.latitude, other.longitude),
            ).meters  # type: ignore
        )

    def to_tuple(self) -> tuple[float, float]:
        return self.latitude, self.longitude


class Stop(BaseModel):
    id: str
    name: str
    coordinate: Coordinate = Field(alias="coordinates")


class Route(BaseModel):
    id: str
    name: str
    short_name: str = Field(alias="shortName")
    transport_mode: str = Field(alias="transportMode")


class StopTime(BaseModel):
    stop: Stop
    arrival_time: datetime = Field(alias="arrivalTime")
    departure_time: datetime = Field(alias="departureTime")


class Trip(BaseModel):
    head_sign: str = Field(alias="headSign")
    route: Route
    stop_times: list[StopTime] = Field(alias="stopTimes")

    @staticmethod
    @field_validator("stop_times", mode="before")
    def set_stop_times_not_none(v: list[StopTime] | None) -> list[StopTime]:
        return v or []


class Departure(BaseModel):
    stop_time: StopTime = Field(alias="stopTime")
    trip: Trip


class Leg(BaseModel):
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
        return (self.arrival_time - self.departure_time).seconds

    @property
    def distance(self) -> float:
        return self.from_coordinate.distance_to(self.to_coordinate)

    @property
    def is_walk(self) -> bool:
        return self.type == LegType.WALK

    @property
    def is_route(self) -> bool:
        return self.type == LegType.ROUTE

    @property
    def num_stops(self) -> int:
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
    legs: list[Leg]

    @staticmethod
    @field_validator("legs")
    def legs_not_empty(v: list[Leg]) -> list[Leg]:
        if not v:
            raise ValueError("legs must not be empty")
        return v

    @property
    def first_leg(self) -> Leg:
        return self.legs[0]

    @property
    def last_leg(self) -> Leg:
        return self.legs[-1]

    @property
    def first_route_leg(self) -> Leg | None:
        for leg in self.legs:
            if leg.is_route:
                return leg

        return None

    @property
    def last_route_leg(self) -> Leg | None:
        for leg in reversed(self.legs):
            if leg.is_route:
                return leg

        return None

    @property
    def first_stop(self) -> Stop | None:
        first_route_leg = self.first_route_leg
        return first_route_leg.from_stop if first_route_leg else None

    @property
    def last_stop(self) -> Stop | None:
        last_route_leg = self.last_route_leg
        return last_route_leg.to_stop if last_route_leg else None

    @property
    def departure_time(self) -> datetime:
        return self.first_leg.departure_time

    @property
    def arrival_time(self) -> datetime:
        return self.last_leg.arrival_time

    @property
    def from_coordinate(self) -> Coordinate:
        return self.first_leg.from_coordinate

    @property
    def to_coordinate(self) -> Coordinate:
        return self.last_leg.to_coordinate

    @property
    def from_stop(self) -> Stop | None:
        return self.first_leg.from_stop

    @property
    def to_stop(self) -> Stop | None:
        return self.last_leg.to_stop

    @property
    def duration(self) -> int:
        return (self.arrival_time - self.departure_time).seconds

    @property
    def travel_duration(self) -> int:
        return sum(leg.duration for leg in self.legs)

    @property
    def travel_distance(self) -> float:
        return sum(leg.distance for leg in self.legs)

    @property
    def bee_line_distance(self) -> float:
        return self.from_coordinate.distance_to(self.to_coordinate)

    @property
    def walk_distance(self) -> float:
        return sum(leg.distance for leg in self.legs if leg.is_walk)

    @property
    def route_distance(self) -> float:
        return sum(leg.distance for leg in self.legs if leg.is_route)

    @property
    def walk_duration(self) -> int:
        return sum(leg.duration for leg in self.legs if leg.is_walk)

    @property
    def route_duration(self) -> int:
        return sum(leg.duration for leg in self.legs if leg.is_route)

    @property
    def num_transfers(self) -> int:
        return sum(1 for leg in self.legs if leg.is_route) - 1

    @property
    def num_same_station_transfers(self) -> int:
        return sum(
            1
            for prev_leg, current_leg in pairwise(self.legs)
            if prev_leg.is_route and current_leg.is_route
        )

    @property
    def num_stops(self) -> int:
        return sum(leg.num_stops for leg in self.legs if leg.is_route)

    @property
    def multi_date(self) -> bool:
        return self.departure_time.date() != self.arrival_time.date()


class StopConnection(BaseModel):
    stop: Stop
    connecting_leg: Leg = Field(alias="connectingLeg")
    connection: Connection | None = None


class DistanceToStop(BaseModel):
    stop: Stop
    distance: float
