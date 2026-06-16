"""Layover-cost calculation service."""

from collections.abc import Iterable

from skypy.models import Crew, Flight, Roster

LAYOVER_ALLOWANCE_HOURS = 8


def calculate_layover_costs(
    roster: Roster, flights: Iterable[Flight], crew_list: Iterable[Crew]
) -> tuple[dict[str, float], float]:
    """Return per-crew layover costs and the overall layover total."""
    layover_costs: dict[str, float] = {}
    total_layover_cost = 0.0

    for crew_member in crew_list:
        cost = _crew_layover_cost(roster, crew_member)
        if cost is None:
            continue

        layover_costs[crew_member.crew_id] = cost
        total_layover_cost += cost

    return layover_costs, total_layover_cost


def _crew_layover_cost(roster: Roster, crew_member: Crew) -> float | None:
    """
    Return one crew member's layover cost if their final assigned flight
    does not return to their home base
    """
    schedule = roster.get_crew_schedule(crew_member.crew_id)
    if not schedule:
        return None

    last_flight = schedule[-1]
    if last_flight.destination == crew_member.home_base:
        return None

    return crew_member.hourly_cost * LAYOVER_ALLOWANCE_HOURS
