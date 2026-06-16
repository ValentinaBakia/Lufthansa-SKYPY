from collections.abc import Iterable
from datetime import timedelta

from skypy.models import Crew, Flight, Roster, Violation, ViolationCode


class RosterValidator:
    """Operational crew schedule validator"""

    SHORT_FLIGHT_LIMIT_MINUTES = 180
    SHORT_FLIGHT_REST_MINUTES = 60
    LONG_FLIGHT_REST_MINUTES = 120

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

            required_rest_minutes = self._required_rest_minutes(previous_flight)
            actual_rest = next_flight.departure - previous_flight.arrival
            if actual_rest < timedelta(minutes=required_rest_minutes):
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

    @classmethod
    def _required_rest_minutes(cls, previous_flight: Flight) -> int:
        """
        Return required rest based on the previous flight's duration.
        The rules is that after a short flight (<3h) the crew needs at least 1h of rest,
        after a long flight (>=3h) the crew needs at least 2h of rest.
        """
        previous_flight_duration = previous_flight.arrival - previous_flight.departure
        if previous_flight_duration < timedelta(minutes=cls.SHORT_FLIGHT_LIMIT_MINUTES):
            return cls.SHORT_FLIGHT_REST_MINUTES
        return cls.LONG_FLIGHT_REST_MINUTES


def validate_roster(
    roster: Roster, flights: Iterable[Flight], crew_list: Iterable[Crew]
) -> list[Violation]:
    """Validate a roster using the public function required by the assignment."""
    return RosterValidator(crew_list).validate(roster)
