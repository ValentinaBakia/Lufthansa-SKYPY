"""Entry point for the Flask application."""

from skypy.app import create_app

app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
