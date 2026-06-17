"""Schedule endpoint request validation."""

from marshmallow import EXCLUDE, Schema, fields, post_load, validate

from skypy.models import Crew, Flight
from skypy.models.crew import CrewRole
from skypy.models.flight import FlightPriority


class FlightRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    flight_id = fields.Str(required=True, validate=validate.Length(min=1))
    origin = fields.Str(required=True, validate=validate.Length(min=1))
    destination = fields.Str(required=True, validate=validate.Length(min=1))
    departure = fields.DateTime(required=True)
    arrival = fields.DateTime(required=True)
    distance_miles = fields.Int(required=True, validate=validate.Range(min=1))
    priority = fields.Enum(FlightPriority, by_value=True, required=True)

    @post_load
    def build_flight(self, data: dict[str, object], **kwargs) -> Flight:
        return Flight(**data)


class CrewRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    crew_id = fields.Str(required=True, validate=validate.Length(min=1))
    home_base = fields.Str(required=True, validate=validate.Length(min=1))
    max_range_miles = fields.Int(required=True, validate=validate.Range(min=1))
    role = fields.Enum(CrewRole, by_value=True, required=True)
    hourly_cost = fields.Float(
        required=True,
        validate=validate.Range(min=0, min_inclusive=False),
    )

    @post_load
    def build_crew_member(self, data: dict[str, object], **kwargs) -> Crew:
        return Crew(**data)


class ScheduleRequestSchema(Schema):
    """Validate the POST /schedule request body."""

    class Meta:
        unknown = EXCLUDE

    flights = fields.List(
        fields.Nested(FlightRequestSchema),
        required=True,
        validate=validate.Length(min=1),
    )
    crew = fields.List(
        fields.Nested(CrewRequestSchema),
        required=True,
        validate=validate.Length(min=1),
    )
