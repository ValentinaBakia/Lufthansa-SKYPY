"""Crew-pairing validation service."""

from collections.abc import Iterable

from skypy.models import Crew, CrewRole, Flight, Roster, Violation, ViolationCode
from skypy.services.rules.resting_rules import has_required_rest_between
from skypy.services.uitls.flight_neighbors import get_flight_neighbors


class FlightPairing:
    """Validate whether one flight has a complete and legal crew pair.

    Example:
        violations = FlightPairing('FL001', roster, crew_list).validate()
    """

    def __init__(
        self,
        flight: Flight,
        crew_members: Iterable[Crew],
        neighbor_flights_by_crew_id: dict[str, tuple[Flight | None, Flight | None]],
    ) -> None:
        self._flight = flight  # target flight for the pairing check
        self._crew_members = list(crew_members)  # Assigned or candidate crew members
        # For each crew_id, stores the previous and next Flight objects around the target self._flight.
        self._neighbor_flights_by_crew_id = neighbor_flights_by_crew_id

    def validate(self) -> list[Violation]:
        """Return pairing violations; an empty list means the pairing is valid."""
        role_violations = self._validate_roles(self._crew_members)
        if role_violations:
            return role_violations

        violations: list[Violation] = []
        for crew_member in self._crew_members:
            # For each crew member check if the flight distance is within the max allowed range.
            if self._flight.distance_miles > crew_member.max_range_miles:
                violations.append(
                    self._violation(
                        crew_id=crew_member.crew_id,
                        code=ViolationCode.RANGE_CERTIFICATION,
                        description=(
                            f'Range Certification: {crew_member.crew_id} is not certified for '
                            f'{self._flight.distance_miles} miles'
                        ),
                    )
                )
            # check if the crew member has the required rest between flights.
            if not self._has_valid_rest(crew_member):
                violations.append(
                    self._violation(
                        crew_id=crew_member.crew_id,
                        code=ViolationCode.DYNAMIC_REST,
                        description=(
                            f'Dynamic Rest: {crew_member.crew_id} does not have enough rest '
                            f'around {self._flight.flight_id}'
                        ),
                    )
                )

        return violations

    def _validate_roles(self, crew_members: list[Crew]) -> list[Violation]:
        captains = [crew for crew in crew_members if crew.role is CrewRole.CAPTAIN]
        first_officers = [crew for crew in crew_members if crew.role is CrewRole.FIRST_OFFICER]

        if not captains or not first_officers:
            missing_roles = []
            if not captains:
                missing_roles.append('Captain')
            if not first_officers:
                missing_roles.append('FirstOfficer')
            return [
                self._violation(
                    crew_id=None,
                    code=ViolationCode.INCOMPLETE_PAIRING,
                    description=f'Incomplete Pairing: missing {", ".join(missing_roles)}',
                )
            ]

        if len(captains) != 1:
            return [
                self._violation(
                    crew_id=None,
                    code=ViolationCode.INVALID_PAIRING,
                    description='Invalid Pairing: exactly one Captain is required',
                )
            ]

        return []

    def _has_valid_rest(self, crew_member: Crew) -> bool:
        previous_flight, next_flight = self._neighbor_flights_by_crew_id[crew_member.crew_id]
        return _has_valid_rest_with_neighbors(self._flight, previous_flight, next_flight)

    def _violation(self, crew_id: str | None, code: ViolationCode, description: str) -> Violation:
        return Violation(
            crew_id=crew_id,
            flight_id=self._flight.flight_id,
            description=description,
            code=code,
        )


def validate_pairing(flight_id: str, roster: Roster, crew_list: Iterable[Crew]) -> list[Violation]:
    """Validate flight pairing thats already in the Roster."""
    flight = roster.get_flight(flight_id)
    crew_by_id = {crew.crew_id: crew for crew in crew_list}
    crew_members: list[Crew] = []
    neighbor_flights_by_crew_id: dict[str, tuple[Flight | None, Flight | None]] = {}

    for crew_id in roster.get_flight_crew(flight_id):
        crew_member = crew_by_id.get(crew_id)
        if crew_member is None:
            raise ValueError(f'unknown crew member assigned: {crew_id}')
        crew_members.append(crew_member)
        neighbor_flights_by_crew_id[crew_id] = get_flight_neighbors(
            roster, flight, crew_member, flight_is_assigned=True
        )

    return FlightPairing(
        flight=flight,
        crew_members=crew_members,
        neighbor_flights_by_crew_id=neighbor_flights_by_crew_id,
    ).validate()


def validate_pairing_candidate(
    flight: Flight, captain: Crew, first_officer: Crew, roster: Roster
) -> list[Violation]:
    """Validate the pairing of the 2 candidates Captain and First Officer before assignment."""
    neighbor_flights_by_crew_id = {
        captain.crew_id: get_flight_neighbors(roster, flight, captain, flight_is_assigned=False),
        first_officer.crew_id: get_flight_neighbors(
            roster, flight, first_officer, flight_is_assigned=False
        ),
    }
    return FlightPairing(
        flight=flight,
        crew_members=[captain, first_officer],
        neighbor_flights_by_crew_id=neighbor_flights_by_crew_id,
    ).validate()


def _has_valid_rest_with_neighbors(
    flight: Flight, previous_flight: Flight | None, next_flight: Flight | None
) -> bool:
    """Return whether a flight satisfies the rest rules against his previous and next neighbour."""
    if previous_flight is not None and not has_required_rest_between(previous_flight, flight):
        return False

    if next_flight is not None and not has_required_rest_between(flight, next_flight):
        return False

    return True
