"""Domain models used by the scheduling engine."""

from skypy.models.crew import Crew, CrewRole
from skypy.models.flight import Flight, FlightPriority

__all__ = ['Crew', 'CrewRole', 'Flight', 'FlightPriority']
