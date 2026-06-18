from collections.abc import Iterable

from skypy.models.crew import Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster
from skypy.models.violation import Violation, ViolationCode
from skypy.services.rules.resting_rules import has_required_rest_between, required_rest_after


class RosterValidator:
    """Operational crew schedule validator"""

    def __init__(self, crew_list: Iterable[Crew]) -> None:
        self._crew = tuple(crew_list)

    def validate(self, roster: Roster) -> list[Violation]:
        """Return every operational-rule violation found in the roster."""
        violations: list[Violation] = []

        for crew_member in self._crew:
            schedule = roster.get_crew_schedule(crew_member.crew_id)

            if schedule:
                violations.extend(self._validate_range(crew_member, schedule))
                violations.extend(self._validate_home_base(crew_member, schedule))
                violations.extend(self._validate_sequence(crew_member, schedule))

        return violations

    def _validate_range(self, crew_member: Crew, schedule: list[Flight]) -> list[Violation]:
        """Check each assigned flight against the crew member's certification."""
        return [
            Violation(
                crew_id=crew_member.crew_id,
                flight_id=flight.flight_id,
                description='Range Certification: Flight exceeds crew maximum range',
                code=ViolationCode.RANGE_CERTIFICATION,
            )
            for flight in schedule
            if flight.distance_miles > crew_member.max_range_miles
        ]

    def _validate_home_base(self, crew_member: Crew, schedule: list[Flight]) -> list[Violation]:
        """Check that the crew member's first flight starts at their home base."""
        if not schedule or schedule[0].origin == crew_member.home_base:
            return []

        return [
            Violation(
                crew_id=crew_member.crew_id,
                flight_id=schedule[0].flight_id,
                description=(
                    f'Home Base Start: First flight must depart from {crew_member.home_base}'
                ),
                code=ViolationCode.HOME_BASE_START,
            )
        ]

    def _validate_sequence(self, crew_member: Crew, schedule: list[Flight]) -> list[Violation]:
        """Check route continuity and rest between consecutive flights."""
        violations: list[Violation] = []
        # scheduled holds the flights ordered by departure time, the following loop pairs the 2 consecutive flights
        # and checks if the destination mataches the previous flights's origin.
        # Next we check if the rest between 2 flights is enough based on the previous duration rules.
        for previous_flight, next_flight in zip(schedule, schedule[1:]):
            if previous_flight.destination != next_flight.origin:
                violations.append(
                    Violation(
                        crew_id=crew_member.crew_id,
                        flight_id=next_flight.flight_id,
                        description=(
                            'Route Continuity: '
                            f'{previous_flight.flight_id} arrives at '
                            f'{previous_flight.destination}, but '
                            f'{next_flight.flight_id} departs from {next_flight.origin}'
                        ),
                        code=ViolationCode.ROUTE_CONTINUITY,
                    )
                )

            required_rest = required_rest_after(previous_flight)
            if not has_required_rest_between(previous_flight, next_flight):
                required_rest_minutes = int(required_rest.total_seconds() // 60)
                violations.append(
                    Violation(
                        crew_id=crew_member.crew_id,
                        flight_id=next_flight.flight_id,
                        description=(
                            f'Dynamic Rest: requires {required_rest_minutes} minutes after '
                            f'{previous_flight.flight_id}'
                        ),
                        code=ViolationCode.DYNAMIC_REST,
                    )
                )

        return violations


def validate_roster(
    roster: Roster, flights: Iterable[Flight], crew_list: Iterable[Crew]
) -> list[Violation]:
    """Validate a roster and return every operational-rule violation."""
    return RosterValidator(crew_list).validate(roster)
