from datetime import datetime

import pytest

from skypy.models import Crew, CrewRole, Flight, FlightPriority, Roster, ViolationCode
from skypy.services.pairing import validate_pairing
from skypy.services.rules.roster_validator import validate_roster


def make_flight(
    flight_id: str,
    departure: datetime,
    arrival: datetime,
    *,
    origin: str = 'FRA',
    destination: str = 'MUC',
    distance_miles: int = 500,
    priority: FlightPriority = FlightPriority.HIGH,
) -> Flight:
    return Flight(
        flight_id=flight_id,
        origin=origin,
        destination=destination,
        departure=departure,
        arrival=arrival,
        distance_miles=distance_miles,
        priority=priority,
    )


def make_crew(
    crew_id: str,
    *,
    role: CrewRole,
    max_range_miles: int = 4000,
    home_base: str = 'FRA',
    hourly_cost: float = 100.0,
) -> Crew:
    return Crew(
        crew_id=crew_id,
        home_base=home_base,
        max_range_miles=max_range_miles,
        role=role,
        hourly_cost=hourly_cost,
    )


# Test validate_roster crew range limit
def test_range_limit_rejects_flight_missing_certification() -> None:
    crew_member = make_crew('C001', role=CrewRole.CAPTAIN, max_range_miles=2000)
    flight = make_flight(
        'FL001',
        datetime(2026, 6, 18, 8, 0),
        datetime(2026, 6, 18, 11, 0),
        distance_miles=3500,
    )
    roster = Roster([flight])
    roster.assign(flight.flight_id, crew_member.crew_id)

    violations = validate_roster(roster, [flight], [crew_member])

    assert len(violations) == 1
    violation = violations[0]
    assert violation.crew_id == 'C001'
    assert violation.flight_id == 'FL001'
    assert violation.code is ViolationCode.RANGE_CERTIFICATION
    assert violation.description == 'Range Certification: Flight exceeds crew maximum range'


# Test validate_roster resting rules: short flight requires 60min rest and any lower value is rejected.
def test_dynamic_rest_short_flight() -> None:
    crew_member = make_crew('C001', role=CrewRole.CAPTAIN)
    first_flight = make_flight(
        'FL001',
        datetime(2026, 6, 18, 8, 0),
        datetime(2026, 6, 18, 10, 59),
        destination='MUC',
    )
    accepted_next = make_flight(
        'FL002',
        datetime(2026, 6, 18, 11, 59),
        datetime(2026, 6, 18, 13, 0),
        origin='MUC',
        destination='BER',
    )
    rejected_next = make_flight(
        'FL003',
        datetime(2026, 6, 18, 11, 58),
        datetime(2026, 6, 18, 13, 0),
        origin='MUC',
        destination='BER',
    )

    accepted_roster = Roster([first_flight, accepted_next])
    accepted_roster.assign(first_flight.flight_id, crew_member.crew_id)
    accepted_roster.assign(accepted_next.flight_id, crew_member.crew_id)
    assert validate_roster(accepted_roster, [first_flight, accepted_next], [crew_member]) == []

    rejected_roster = Roster([first_flight, rejected_next])
    rejected_roster.assign(first_flight.flight_id, crew_member.crew_id)
    rejected_roster.assign(rejected_next.flight_id, crew_member.crew_id)
    violations = validate_roster(rejected_roster, [first_flight, rejected_next], [crew_member])

    assert len(violations) == 1
    violation = violations[0]
    assert violation.code is ViolationCode.DYNAMIC_REST
    assert violation.flight_id == 'FL003'
    assert violation.description == 'Dynamic Rest: requires 60 minutes after FL001'


# Test validate_roster resting rules: long flight requires 180min rest and any lower value is rejected.


def test_dynamic_rest_long_flight_accepts_120_minutes_but_rejects_119_minutes() -> None:
    crew_member = make_crew('C001', role=CrewRole.CAPTAIN)
    first_flight = make_flight(
        'FL010',
        datetime(2026, 6, 18, 8, 0),
        datetime(2026, 6, 18, 11, 0),
        destination='MUC',
    )
    accepted_next = make_flight(
        'FL011',
        datetime(2026, 6, 18, 13, 0),
        datetime(2026, 6, 18, 14, 0),
        origin='MUC',
        destination='BER',
    )
    rejected_next = make_flight(
        'FL012',
        datetime(2026, 6, 18, 12, 59),
        datetime(2026, 6, 18, 14, 0),
        origin='MUC',
        destination='BER',
    )

    accepted_roster = Roster([first_flight, accepted_next])
    accepted_roster.assign(first_flight.flight_id, crew_member.crew_id)
    accepted_roster.assign(accepted_next.flight_id, crew_member.crew_id)
    assert validate_roster(accepted_roster, [first_flight, accepted_next], [crew_member]) == []

    rejected_roster = Roster([first_flight, rejected_next])
    rejected_roster.assign(first_flight.flight_id, crew_member.crew_id)
    rejected_roster.assign(rejected_next.flight_id, crew_member.crew_id)
    violations = validate_roster(rejected_roster, [first_flight, rejected_next], [crew_member])

    assert len(violations) == 1
    violation = violations[0]
    assert violation.code is ViolationCode.DYNAMIC_REST
    assert violation.flight_id == 'FL012'
    assert violation.description == 'Dynamic Rest: requires 120 minutes after FL010'


# Test validate_pairing rules: A flight with 2 Captains but no FirstOfficer is rejected.


def test_pairing_validation_fails_with_two_captains_and_no_first_officer() -> None:
    flight = make_flight(
        'FL020',
        datetime(2026, 6, 18, 8, 0),
        datetime(2026, 6, 18, 10, 0),
    )
    captain_one = make_crew('C001', role=CrewRole.CAPTAIN)
    captain_two = make_crew('C002', role=CrewRole.CAPTAIN)
    roster = Roster([flight])
    roster.assign(flight.flight_id, captain_one.crew_id)
    roster.assign(flight.flight_id, captain_two.crew_id)

    violations = validate_pairing(flight.flight_id, roster, [captain_one, captain_two])

    assert len(violations) == 1
    violation = violations[0]
    assert violation.crew_id is None
    assert violation.flight_id == 'FL020'
    assert violation.code is ViolationCode.INCOMPLETE_PAIRING
    assert violation.description == 'Incomplete Pairing: missing FirstOfficer'


# Test Roster assigne method: you cant assign the same crew member twice to the same flight
def test_conflict_guard_rejects_assigning_same_crew_member_twice() -> None:
    flight = make_flight(
        'FL030',
        datetime(2026, 6, 18, 8, 0),
        datetime(2026, 6, 18, 10, 0),
    )
    roster = Roster([flight])

    roster.assign('FL030', 'C001')

    with pytest.raises(ValueError) as error:
        roster.assign('FL030', 'C001')

    assert str(error.value) == "crew member 'C001' is already assigned to flight 'FL030'"
