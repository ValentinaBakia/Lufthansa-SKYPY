"""GET /roster/<crew_id> API."""

from flask import Blueprint, abort, current_app, jsonify

from skypy.schemas.responses.roster import CrewRosterResponseSchema

roster_bp = Blueprint('roster', __name__)


@roster_bp.get('/roster/<crew_id>')
def get_crew_roster(crew_id: str):
    """
    Return roster details for one crew member from the latest scheduler run.
    """
    # Read the latest data from the ScheduleStore
    snapshot = current_app.extensions['schedule_store'].get_latest()
    if snapshot is None:
        abort(404, description='no roster is available yet')

    current_roster = snapshot.roster
    current_crew_ids = {crew_member.crew_id for crew_member in snapshot.crew_members}
    if crew_id not in current_crew_ids:
        abort(404, description=f'crew_id {crew_id!r} not found')

    # Get the schedule of the provided crew_id
    schedule = current_roster.get_crew_schedule(crew_id)
    layover = snapshot.layover_costs.get(crew_id, 0.0)

    # Calculate total_horus and collect flight_ids in the same loop
    flight_ids = []
    total_minutes = 0
    for flight in schedule:
        flight_ids.append(flight.flight_id)
        total_minutes += flight.duration_minutes
    total_hours = round(total_minutes / 60, 2)

    return jsonify(
        CrewRosterResponseSchema().dump(
            {
                'crew_id': crew_id,
                'flight_ids': flight_ids,
                'total_hours': total_hours,
                'layover_cost': layover,
            }
        )
    ), 200
