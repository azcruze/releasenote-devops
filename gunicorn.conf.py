"""Gunicorn settings. Nginx is the only public listener; Gunicorn binds to loopback."""
bind = "127.0.0.1:8000"
workers = 2            # SQLite (WAL mode) handles light concurrent access from 2 workers
threads = 2
timeout = 30
graceful_timeout = 20
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
