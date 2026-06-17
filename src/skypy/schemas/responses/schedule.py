"""Schedule response serialization."""

from marshmallow import Schema, fields

from skypy.schemas.responses.roster import CrewRosterEntrySchema, dump_complete_roster
from skypy.state.schedule_store import ScheduleSnapshot


class UnassignedFlightResponseSchema(Schema):
    """Serialize one unassigned flight."""

    flight_id = fields.Str(required=True)
    reason = fields.Str(required=True)


class ScheduleResponseSchema(Schema):
    """Serialize the POST /schedule response."""

    roster = fields.Dict(
        keys=fields.Str(),
        values=fields.Nested(CrewRosterEntrySchema()),
        required=True,
    )
    unassigned = fields.List(fields.Nested(UnassignedFlightResponseSchema), required=True)

    def dump(self, data, *args, **kwargs):
        """Serialize one POST /schedule payload."""
        if isinstance(data, ScheduleSnapshot):
            payload = {
                'roster': dump_complete_roster(
                    data.roster, data.crew_members, data.layover_costs
                ),
                'unassigned': [
                    {'flight_id': flight.flight_id, 'reason': flight.reason}
                    for flight in data.unassigned_flights
                ],
            }
            return super().dump(payload, *args, **kwargs)

        payload = {
            'roster': dump_complete_roster(
                data['roster'], data['crew_members'], data['layover_costs']
            ),
            'unassigned': [
                {'flight_id': flight.flight_id, 'reason': flight.reason}
                for flight in data['unassigned']
            ],
        }
        return super().dump(payload, *args, **kwargs)
