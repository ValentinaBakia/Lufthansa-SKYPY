from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum


class FlightPriority(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass(frozen=True, slots=True)
class Flight:
    """A scheduled flight that may be assigned a crew."""

    flight_id: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    distance_miles: int
    priority: FlightPriority

    def __post_init__(self) -> None:
        """Reject invalid flights at the domain boundary."""
        for field_name in ('flight_id', 'origin', 'destination'):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{field_name} must be a non-empty string')

        if not isinstance(self.departure, datetime):
            raise ValueError('departure must be a datetime')
        if not isinstance(self.arrival, datetime):
            raise ValueError('arrival must be a datetime')
        if self.arrival <= self.departure:
            raise ValueError('arrival must be after departure')
        # Used type() instead of isinstance() because that would acceot bool values.
        if type(self.distance_miles) is not int or self.distance_miles <= 0:
            raise ValueError('distance_miles must be a positive integer')
        if not isinstance(self.priority, FlightPriority):
            allowed_priorities = ', '.join(str(priority.value) for priority in FlightPriority)
            raise ValueError(f'priority must be one of: {allowed_priorities}')

    @property
    def duration_minutes(self) -> int:
        """Return the duration of the flight based on the arrival and departure time"""
        return round((self.arrival - self.departure).total_seconds() / 60)
