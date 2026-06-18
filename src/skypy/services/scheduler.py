"""Priority-based automatic crew scheduler."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from heapq import heapify, heappop

from skypy.models.crew import Crew, CrewRole
from skypy.models.flight import Flight
from skypy.models.roster import Roster
from skypy.services.pairing import validate_pairing_candidate
from skypy.services.uitls.flight_neighbors import get_flight_neighbors

NO_CAPTAIN_AVAILABLE = 'No Captain available'
NO_FIRST_OFFICER_AVAILABLE = 'No FirstOfficer available'
NO_VALID_PAIR_FOUND = 'No valid pair found'


@dataclass(frozen=True, slots=True)
class UnassignedFlight:
    """
    Flight_id and reason for a Flight that couldnt be assigned to a roster.
    """

    flight_id: str
    reason: str


class Scheduler:
    """Build a legal roster by staffing flights in priority order."""

    def __init__(self, flights: Iterable[Flight], crew_list: Iterable[Crew]) -> None:
        self._flights = tuple(flights)
        self._crew = tuple(crew_list)
        self._roster = Roster(self._flights)
        self._crew_by_role = {
            CrewRole.CAPTAIN: [crew for crew in self._crew if crew.role is CrewRole.CAPTAIN],
            CrewRole.FIRST_OFFICER: [
                crew for crew in self._crew if crew.role is CrewRole.FIRST_OFFICER
            ],
        }

    def generate(self) -> tuple[Roster, list[UnassignedFlight]]:
        """
        Assign the best available allowed crew pair (Captain, FirstOfficer) to each flight.
        """
        unassigned_flights: list[UnassignedFlight] = []
        flight_heap = self._build_priority_heap()

        while flight_heap:
            _, _, _, flight = heappop(flight_heap)
            self._schedule_flight(flight, unassigned_flights)

        return self._roster, unassigned_flights

    def _build_priority_heap(self) -> list[tuple[int, datetime, str, Flight]]:
        """
        Return flights ordered by priority, then departure, then flight id.
        Use flight_id as the last ordering by to avoid situations where we have two flights
        with same prio on the same departure.

        """
        heap = [
            (flight.priority.value, flight.departure, flight.flight_id, flight)
            for flight in self._flights
        ]
        # Make the list into a heap so we can pop the highest priority flight.
        heapify(heap)
        return heap

    def _schedule_flight(self, flight: Flight, unassigned_flights: list[UnassignedFlight]) -> None:
        captains = self._get_available_crew_for_flight(flight, CrewRole.CAPTAIN)
        if not captains:
            self._mark_unassigned(unassigned_flights, flight, NO_CAPTAIN_AVAILABLE)
            return

        first_officers = self._get_available_crew_for_flight(flight, CrewRole.FIRST_OFFICER)
        if not first_officers:
            self._mark_unassigned(unassigned_flights, flight, NO_FIRST_OFFICER_AVAILABLE)
            return

        for captain in captains:
            for first_officer in first_officers:
                if self._check_pair_validity(flight, captain, first_officer):
                    self._assign_pair_to_roster(flight, captain, first_officer)
                    return

        self._mark_unassigned(unassigned_flights, flight, NO_VALID_PAIR_FOUND)

    def _get_available_crew_for_flight(self, flight: Flight, role: CrewRole) -> list[Crew]:
        """
        Return crew members who can take this flight in their sequence.
        """
        return [
            crew_member
            for crew_member in self._crew_by_role[role]
            if self._has_valid_route_position(flight, crew_member)
        ]

    def _has_valid_route_position(self, flight: Flight, crew_member: Crew) -> bool:
        """
        Check the home-base and route-continuity rules.
        Basically the first flight must depart from their home base,
        and the destination of each flight must be the origin of the next one.
        """
        previous_flight, next_flight = get_flight_neighbors(
            self._roster, flight, crew_member, flight_is_assigned=False
        )

        if previous_flight is None:
            if flight.origin != crew_member.home_base:
                return False
        elif previous_flight.destination != flight.origin:
            return False

        if next_flight is not None and flight.destination != next_flight.origin:
            return False

        return True

    def _check_pair_validity(self, flight: Flight, captain: Crew, first_officer: Crew) -> bool:
        violations = validate_pairing_candidate(flight, captain, first_officer, self._roster)
        return not violations

    def _assign_pair_to_roster(self, flight: Flight, captain: Crew, first_officer: Crew) -> None:
        self._roster.assign(flight.flight_id, captain.crew_id)
        self._roster.assign(flight.flight_id, first_officer.crew_id)

    def _mark_unassigned(
        self, unassigned_flights: list[UnassignedFlight], flight: Flight, reason: str
    ) -> None:
        """
        Provided the reason why, add the flight into unassigned_flights list
        """
        unassigned_flights.append(UnassignedFlight(flight_id=flight.flight_id, reason=reason))


def generate_schedule(
    flights: Iterable[Flight], crew_list: Iterable[Crew]
) -> tuple[Roster, list[UnassignedFlight]]:
    """
    Generate a roster and list any flights that could not be set into the schedule.
    """
    return Scheduler(flights, crew_list).generate()
