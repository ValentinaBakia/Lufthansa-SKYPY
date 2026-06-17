"""GET /report endpoint."""

from flask import Blueprint, abort, current_app, jsonify

from skypy.schemas.responses import ReportResponseSchema
from skypy.services.costs import calculate_layover_costs

report_bp = Blueprint('report', __name__)


@report_bp.get('/report')
def get_report():
    """
    Return a summary of the latest scheduling run.
    """

    # Read the latest data from the ScheduleStore
    snapshot = current_app.extensions['schedule_store'].get_latest()
    if snapshot is None:
        abort(404, description='no scheduling report is available yet')

    layover_map, total_layover = calculate_layover_costs(
        snapshot.roster, snapshot.flights, snapshot.crew_members
    )
    # build the data for each crew that contains the crew_id, flight_ids and layover_cost
    breakdown = []
    for crew_member in snapshot.crew_members:
        schedule = snapshot.roster.get_crew_schedule(crew_member.crew_id)
        flight_ids = []
        for flight in schedule:
            flight_ids.append(flight.flight_id)

        breakdown.append(
            {
                'crew_id': crew_member.crew_id,
                'flight_ids': flight_ids,
                'layover_cost': layover_map.get(crew_member.crew_id, 0.0),
            }
        )

    # a flight either is scheduled or unassigned, calculate the number from this
    scheduled_flights = len(snapshot.flights) - len(snapshot.unassigned_flights)

    return jsonify(
        ReportResponseSchema().dump(
            {
                'flights_scheduled': scheduled_flights,
                'unassigned_count': len(snapshot.unassigned_flights),
                'total_layover_cost': total_layover,
                'crew_breakdown': breakdown,
            }
        )
    ), 200
