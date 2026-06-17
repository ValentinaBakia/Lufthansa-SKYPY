"""Scheduling-report response serialization."""

from marshmallow import Schema, fields


class CrewBreakdownSchema(Schema):
    """Serialize one crew item inside the report breakdown."""

    crew_id = fields.Str(required=True)
    flight_ids = fields.List(fields.Str(), required=True)
    layover_cost = fields.Float(required=True)


class ReportResponseSchema(Schema):
    """Serialize the GET /report response."""

    flights_scheduled = fields.Int(required=True)
    unassigned_count = fields.Int(required=True)
    total_layover_cost = fields.Float(required=True)
    crew_breakdown = fields.List(fields.Nested(CrewBreakdownSchema), required=True)
