"""Structured representation of a scheduling-rule violation."""

from dataclasses import dataclass
from enum import StrEnum


class ViolationCode(StrEnum):
    RANGE_CERTIFICATION = 'range_certification'
    HOME_BASE_START = 'home_base_start'
    ROUTE_CONTINUITY = 'route_continuity'
    DYNAMIC_REST = 'dynamic_rest'


@dataclass(frozen=True, slots=True)
class Violation:
    """Dataclass used to represent a violation of a roster rule."""

    crew_id: str
    flight_id: str
    description: str
    code: ViolationCode
