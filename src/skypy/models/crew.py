from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class CrewRole(StrEnum):
    """Crew roles supported by the rostering system."""

    CAPTAIN = 'Captain'
    FIRST_OFFICER = 'FirstOfficer'


@dataclass(frozen=True, slots=True)
class Crew:
    """A crew member available for assignment."""

    crew_id: str
    home_base: str
    max_range_miles: int
    role: CrewRole
    hourly_cost: float

    def __post_init__(self) -> None:
        """Reject invalid crew members at the domain boundary."""
        for field_name in ('crew_id', 'home_base'):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{field_name} must be a non-empty string')

        if type(self.max_range_miles) is not int or self.max_range_miles <= 0:
            raise ValueError('max_range_miles must be a positive integer')
        if not isinstance(self.role, CrewRole):
            raise ValueError('role must be exactly "Captain" or "FirstOfficer"')
        if (
            type(self.hourly_cost) is not float
            or not isfinite(self.hourly_cost)
            or self.hourly_cost <= 0
        ):
            raise ValueError('hourly_cost must be a positive float')
