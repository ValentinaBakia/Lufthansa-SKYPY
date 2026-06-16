"""Crew-pairing validation service."""

from collections.abc import Iterable

from skypy.models import Crew, CrewRole, Roster, Violation, ViolationCode
from skypy.services.rules.resting_rules import has_required_rest_between


class FlightPairing:
    """Validate whether one flight has a complete and legal crew pair.

    Example:
        violations = FlightPairing('FL001', roster, crew_list).validate()
    """

    def __init__(self, flight_id: str, roster: Roster, crew_list: Iterable[Crew]) -> None:
        self._flight = roster.get_flight(flight_id)
        self._roster = roster
        self._crew_by_id = {crew.crew_id: crew for crew in crew_list}

    def validate(self) -> list[Violation]:
        """Return pairing violations; an empty list means the pairing is valid."""
        crew_members = self._assigned_crew_members()

        role_violations = self._validate_roles(crew_members)
        if role_violations:
            return role_violations

        violations: list[Violation] = []
        for crew_member in crew_members:
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

    def _assigned_crew_members(self) -> list[Crew]:
        crew_members: list[Crew] = []

        for crew_id in self._roster.get_flight_crew(self._flight.flight_id):
            crew_member = self._crew_by_id.get(crew_id)
            if crew_member is None:
                raise ValueError(f'unknown crew member assigned: {crew_id}')
            crew_members.append(crew_member)

        return crew_members

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
        schedule = self._roster.get_crew_schedule(crew_member.crew_id)
        flight_index = next(
            (
                index
                for index, flight in enumerate(schedule)
                if flight.flight_id == self._flight.flight_id
            ),
            None,
        )
        if flight_index is None:
            raise ValueError(
                f'flight {self._flight.flight_id!r} is not assigned to {crew_member.crew_id!r}'
            )

        if flight_index > 0:
            previous_flight = schedule[flight_index - 1]
            if not has_required_rest_between(previous_flight, self._flight):
                return False

        if flight_index < len(schedule) - 1:
            next_flight = schedule[flight_index + 1]
            if not has_required_rest_between(self._flight, next_flight):
                return False

        return True

    def _violation(self, crew_id: str | None, code: ViolationCode, description: str) -> Violation:
        return Violation(
            crew_id=crew_id,
            flight_id=self._flight.flight_id,
            description=description,
            code=code,
        )


def validate_pairing(flight_id: str, roster: Roster, crew_list: Iterable[Crew]) -> list[Violation]:
    """Validate flight pairing."""
    return FlightPairing(flight_id, roster, crew_list).validate()
