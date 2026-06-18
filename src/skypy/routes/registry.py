"""Flask blueprint registration."""

from flask import Flask

from skypy.routes.report import report_bp
from skypy.routes.roster import roster_bp
from skypy.routes.schedule import schedule_bp


def register_blueprints(app: Flask) -> None:
    """Register the API blueprints on the Flask app."""
    app.register_blueprint(schedule_bp)
    app.register_blueprint(roster_bp)
    app.register_blueprint(report_bp)
