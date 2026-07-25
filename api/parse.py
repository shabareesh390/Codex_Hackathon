from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from backend.api.parse import parse_file


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        payload = self._read_json()
        try:
            transactions = parse_file(payload["file"].encode("utf-8"), payload.get("source", "bank"), payload.get("filename"))
            self._send_json(200, [tx.to_dict() for tx in transactions])
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})

    def do_OPTIONS(self) -> None:
        self._send_json(204, {})

    def _read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(body or "{}")

    def _send_json(self, status: int, payload: object) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if status != 204:
            self.wfile.write(json.dumps(payload).encode("utf-8"))
