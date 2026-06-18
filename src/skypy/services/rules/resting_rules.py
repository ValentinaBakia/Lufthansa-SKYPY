"""Dynamic rest rules for consecutive crew assignments."""

from datetime import timedelta

from skypy.models.flight import Flight

SHORT_FLIGHT_LIMIT = timedelta(minutes=180)
SHORT_FLIGHT_REST = timedelta(minutes=60)
LONG_FLIGHT_REST = timedelta(minutes=120)


def required_rest_after(flight: Flight) -> timedelta:
    """Return the rest required after a flight."""
    flight_duration = flight.arrival - flight.departure
    if flight_duration < SHORT_FLIGHT_LIMIT:
        return SHORT_FLIGHT_REST
    return LONG_FLIGHT_REST


def has_required_rest_between(previous_flight: Flight, next_flight: Flight) -> bool:
    """Return whether the gap between two consecutive flights satisfies rest rules."""
    actual_rest = next_flight.departure - previous_flight.arrival
    return actual_rest >= required_rest_after(previous_flight)
