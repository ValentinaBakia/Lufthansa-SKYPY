"""Flask application factory."""

from flask import Flask

from skypy.errors import register_error_handlers
from skypy.routes.registry import register_blueprints
from skypy.state.schedule_store import ScheduleStore


def create_app() -> Flask:
    """Create and configure a SkyPy application instance."""
    app = Flask(__name__)
    app.extensions['schedule_store'] = ScheduleStore()
    register_error_handlers(app)
    register_blueprints(app)

    return app
