"""Small local server for the VANTA request form. Uses only Python's standard library."""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_DIR = ROOT / "data"
DB_PATH = Path(os.environ.get("VANTA_DB_PATH", str(DB_DIR / "vanta_requests.sqlite3")))
MAX_BODY = 12_000
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def init_db():
    DB_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            service TEXT NOT NULL,
            details TEXT NOT NULL,
            authorized INTEGER NOT NULL,
            privacy_consent INTEGER NOT NULL
        )""")


class Handler(BaseHTTPRequestHandler):
    server_version = "VANTA/1.0"

    def send_json(self, status, payload):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        data = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/api/requests":
            self.send_json(404, {"error": "Not found."})
            return
        if self.headers.get_content_type() != "application/json":
            self.send_json(415, {"error": "Please submit the request form."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self.send_json(413, {"error": "Request is empty or too large."})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "Request could not be read."})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "Request could not be read."})
            return

        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        phone = str(payload.get("phone", "")).strip()
        service = str(payload.get("service", "")).strip()
        details = str(payload.get("details", "")).strip()
        authorized = payload.get("authorization") == "on"
        privacy = payload.get("privacy") == "on"
        if not (1 <= len(name) <= 100 and EMAIL_RE.match(email) and len(email) <= 254):
            self.send_json(400, {"error": "Enter a valid name and email address."})
            return
        if len(phone) > 30 or not (1 <= len(service) <= 120) or not (1 <= len(details) <= 1500):
            self.send_json(400, {"error": "Check the service, phone, and description fields."})
            return
        if not authorized or not privacy:
            self.send_json(400, {"error": "Please confirm authorization and read the privacy note."})
            return
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""INSERT INTO requests
                (created_at, name, email, phone, service, details, authorized, privacy_consent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now(timezone.utc).isoformat(), name, email, phone, service, details, 1, 1))
        self.send_json(201, {"ok": True})

    def log_message(self, fmt, *args):
        # Avoid writing submitted form contents or client addresses to the console.
        if args and str(args[0]).startswith("\"GET "):
            return


if __name__ == "__main__":
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    print(f"VANTA preview running at http://{host}:{port}")
    print(f"Private request database: {DB_PATH}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
