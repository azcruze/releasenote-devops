"""WSGI entry point used by Gunicorn (wsgi:app) and `flask --app wsgi`.
Named wsgi.py (not app.py) because the `app/` package would shadow app.py."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
