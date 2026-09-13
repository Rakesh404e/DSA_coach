"""Local development HTTP server for Test-Case Triage Coach.

Runs the real LangGraph graph and Python execution sandbox locally
without requiring an active AWS deployment or credentials.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from triage_coach.handler import lambda_handler


class TriageDevHandler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "healthy", "service": "triage-coach-local"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        event = {
            "httpMethod": "POST",
            "path": self.path,
            "body": post_body,
            "headers": dict(self.headers),
        }

        try:
            result = lambda_handler(event, None)
            status_code = result.get("statusCode", 200)
            body_str = result.get("body", "{}")
        except Exception as err:
            status_code = 500
            body_str = json.dumps({"error": str(err)})

        self.send_response(status_code)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body_str.encode("utf-8"))

    def log_message(self, format, *args):
        sys.stderr.write(f"[LocalDevServer] {args[0]} - {args[1]}\n")


def run(port: int = 8000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, TriageDevHandler)
    print(f"Local Triage Dev Server running at http://127.0.0.1:{port}/triage")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local server...")
        httpd.server_close()


if __name__ == "__main__":
    run()
