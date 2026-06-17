"""POST /schedule endpoint."""

from flask import Blueprint, abort, current_app, jsonify, request
from marshmallow import ValidationError

from skypy.io.serializers import write_roster_output
from skypy.schemas.requests import ScheduleRequestSchema
from skypy.schemas.responses import ScheduleResponseSchema
from skypy.services.costs import calculate_layover_costs
from skypy.services.scheduler import generate_schedule
from skypy.state.schedule_store import ScheduleSnapshot

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.post('/schedule')
def schedule():
    """Run the scheduler for the provided flights and crew."""
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description='request body must be JSON')
    try:
        validated = ScheduleRequestSchema().load(payload)
        flights = validated['flights']
        crew_members = validated['crew']
    except ValidationError as error:
        abort(400, description=error.normalized_messages())
    except ValueError as error:
        abort(400, description=str(error))

    roster, unassigned_flights = generate_schedule(flights, crew_members)
    layover_costs, total_layover_cost = calculate_layover_costs(roster, flights, crew_members)

    # After generating the schedule, save it as a snapshot to the ScheduleStore
    # so that it can be used by other routes to read the information.
    snapshot = ScheduleSnapshot(
        roster=roster,
        flights=tuple(flights),
        crew_members=tuple(crew_members),
        unassigned_flights=tuple(unassigned_flights),
        layover_costs=layover_costs,
        total_layover_cost=total_layover_cost,
    )
    current_app.extensions['schedule_store'].save(snapshot=snapshot)
    response_body = ScheduleResponseSchema().dump(snapshot)

    # Before returning the response, export the roster to a json
    write_roster_output(snapshot.total_layover_cost, response_body)

    return jsonify(response_body), 200
