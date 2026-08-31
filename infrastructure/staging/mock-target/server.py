"""Minimal HTTP target for staging acceptance — verification file + scannable responses."""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN_FILE = os.environ.get("VERIFICATION_TOKEN_FILE", "/data/verification-token.txt")
HOST = os.environ.get("MOCK_TARGET_HOST", "0.0.0.0")
PORT = int(os.environ.get("MOCK_TARGET_PORT", "80"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:
        if self.path.startswith("/.well-known/sandbox-verification.txt"):
            token = ""
            if os.path.isfile(TOKEN_FILE):
                token = open(TOKEN_FILE, encoding="utf-8").read().strip()
            self._respond(200, token or "pending", "text/plain")
            return

        if self.path.rstrip("/").endswith((".json", "api-docs")):
            self._respond(404, "not found", "text/plain")
            return

        if self.path.startswith("/http") or self.headers.get("X-Forwarded-Proto") == "http":
            self.send_response(301)
            self.send_header("Location", f"http://{self.headers.get('Host', 'mock-target')}/")
            self.end_headers()
            return

        # Intentionally missing security headers so http_headers plugin emits findings.
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Server", "mock-target/1.0")
        self.send_header("Set-Cookie", "sessionid=staging-acceptance; Path=/")
        self.end_headers()
        self.wfile.write(b"<html><body>staging acceptance target</body></html>")

    def do_TRACE(self) -> None:
        self._respond(405, "Method Not Allowed", "text/plain")

    def _respond(self, status: int, body: str, content_type: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
