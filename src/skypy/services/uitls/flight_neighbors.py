"""Helpers for locating adjacent flights in a crew schedule."""

from skypy.models import Crew, Flight, Roster


def get_flight_neighbors(
    roster: Roster, flight: Flight, crew_member: Crew, flight_is_assigned: bool
) -> tuple[Flight | None, Flight | None]:
    """
    Return the flights surrounding a current or candidate flight for one crew member.
    `flight_is_assigned` True, means that the flight is already set in the scheduled,
    the opposite means the flight is a candidate to be set.
    """
    schedule = roster.get_crew_schedule(crew_member.crew_id)
    index = _schedule_index(
        schedule, flight, flight_is_assigned=flight_is_assigned, crew_member=crew_member
    )
    return _neighbors_at_index(schedule, index, flight_is_assigned=flight_is_assigned)


def _schedule_index(
    schedule: list[Flight], flight: Flight, flight_is_assigned: bool, crew_member: Crew
) -> int:
    """Return the current or to be inserted index of a flight within a schedule."""
    if flight_is_assigned:
        # Get the flight index from the crew's schedule
        flight_index = None
        for index, scheduled_flight in enumerate(schedule):
            if scheduled_flight.flight_id == flight.flight_id:
                flight_index = index
                break

        if flight_index is None:
            raise ValueError(
                f'flight {flight.flight_id!r} is not assigned to {crew_member.crew_id!r}'
            )
        return flight_index

    # At this point this is a candidate flight, get the posible index it could be iserted in the schedule
    for index, scheduled_flight in enumerate(schedule):
        if flight.departure < scheduled_flight.departure:
            return index

    return len(schedule)


def _neighbors_at_index(
    schedule: list[Flight], index: int, flight_is_assigned: bool
) -> tuple[Flight | None, Flight | None]:
    """Return the previous and next flights around a schedule position.

    Example:
        If `schedule` is `[A, TARGET, B]`, `index=1`, and `flight_is_assigned=True`,
        this returns `(A, B)`.

        If `schedule` is `[A, B]`, `index=1`, and `flight_is_assigned=False`,
        the target flight would be inserted as `[A, TARGET, B]`, so this also
        returns `(A, B)`.
    """

    previous_flight = schedule[index - 1] if index > 0 else None
    next_index = index + 1 if flight_is_assigned else index
    next_flight = schedule[next_index] if next_index < len(schedule) else None
    return previous_flight, next_flight
