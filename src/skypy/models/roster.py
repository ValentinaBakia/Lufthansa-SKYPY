"""Roster domain model for flight-to-crew assignments."""

from collections.abc import Iterable

from skypy.models.flight import Flight


class Roster:
    """Track assignements of flights to crew members."""

    def __init__(self, flights: Iterable[Flight]) -> None:
        # _assignments hold the crew members assigned to each flight in this shape:
        # {'flight_id': ['crew_id1', 'crew_id2', ...], ...}
        self._assignments: dict[str, list[str]] = {}
        # same as _assignments but reversed, to get assigned flights to crew member but its id.
        self._crew_flights: dict[str, list[str]] = {}
        self._flight_by_id: dict[str, Flight] = {}

        for flight in flights:
            if flight.flight_id in self._flight_by_id:
                raise ValueError(f'duplicate flight_id: {flight.flight_id!r}')
            self._flight_by_id[flight.flight_id] = flight

    def assign(self, flight_id: str, crew_id: str) -> None:
        """Assign a crew member to a flight."""
        if flight_id not in self._flight_by_id:
            raise ValueError(f'flight {flight_id!r} does not exist')
        if not isinstance(crew_id, str) or not crew_id.strip():
            raise ValueError('crew_id must be a non-empty string')

        assigned_crew = self._assignments.setdefault(flight_id, [])
        if crew_id in assigned_crew:
            raise ValueError(f'crew member {crew_id!r} is already assigned to flight {flight_id!r}')

        assigned_crew.append(crew_id)
        self._crew_flights.setdefault(crew_id, []).append(flight_id)

    def get_flight(self, flight_id: str) -> Flight:
        """Return the flight tracked by this roster."""
        if flight_id not in self._flight_by_id:
            raise ValueError(f'flight {flight_id!r} does not exist')
        return self._flight_by_id[flight_id]

    def get_flight_crew(self, flight_id: str) -> list[str]:
        """Return the crew assigned to a flight."""
        return list(self._assignments.get(flight_id, []))

    def get_crew_schedule(self, crew_id: str) -> list[Flight]:
        """Return a crew member's assigned flights ordered by departure."""
        assigned_flight_ids = self._crew_flights.get(crew_id, [])
        schedule = [self._flight_by_id[flight_id] for flight_id in assigned_flight_ids]
        return sorted(schedule, key=lambda flight: flight.departure)
