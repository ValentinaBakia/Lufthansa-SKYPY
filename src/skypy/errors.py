"""Application errors and their JSON HTTP handlers."""

from flask import Flask, jsonify
from werkzeug.exceptions import BadRequest, HTTPException, NotFound


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for HTTP exceptions."""

    @app.errorhandler(BadRequest)
    def handle_bad_request(error: BadRequest):
        return jsonify({'error': error.description}), 400

    @app.errorhandler(NotFound)
    def handle_not_found(error: NotFound):
        return jsonify({'error': error.description}), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return jsonify({'error': error.description}), error.code
