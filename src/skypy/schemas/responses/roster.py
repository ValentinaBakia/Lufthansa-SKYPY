"""Crew-roster response serialization."""

from collections.abc import Iterable

from marshmallow import Schema, fields

from skypy.models.crew import Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster


class CrewRosterEntrySchema(Schema):
    """Serialize one crew member entry inside the full roster."""

    role = fields.Str(required=True)
    flights = fields.List(fields.Str(), required=True)
    total_hours = fields.Float(required=True)
    layover_cost = fields.Float(required=True)


class CrewRosterResponseSchema(Schema):
    """Serialize one GET /roster response."""

    crew_id = fields.Str(required=True)
    flight_ids = fields.List(fields.Str(), required=True)
    total_hours = fields.Float(required=True)
    layover_cost = fields.Float(required=True)


def dump_complete_roster(
    roster: Roster, crew_members: Iterable[Crew], layover_costs: dict[str, float]
) -> dict[str, dict[str, object]]:
    """Serialize the full roster keyed by crew member id."""
    schema = CrewRosterEntrySchema()
    roster_payload: dict[str, dict[str, object]] = {}

    for crew_member in crew_members:
        schedule = roster.get_crew_schedule(crew_member.crew_id)
        roster_payload[crew_member.crew_id] = schema.dump(
            {
                'role': crew_member.role.value,
                'flights': [flight.flight_id for flight in schedule],
                'total_hours': _total_hours(schedule),
                'layover_cost': layover_costs.get(crew_member.crew_id, 0.0),
            }
        )

    return roster_payload


def _total_hours(schedule: list[Flight]) -> float:
    """Return the total scheduled hours for one crew member."""
    return round(sum(flight.duration_minutes for flight in schedule) / 60, 2)
