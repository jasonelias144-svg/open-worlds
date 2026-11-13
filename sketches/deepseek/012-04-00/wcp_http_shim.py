"""
wcp_http_shim.py — Expose any Python WorldProtocol as a WCP/0.1 HTTP server.

This is the bridge. Any in-process Python entity becomes a network
entity with ten lines. Any implementation in any language must
match this wire format.

    server = WorldProtocolServer(entity, host="127.0.0.1", port=8080)
    server.serve_in_thread()   # for tests
    server.serve_forever()     # for production
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from multiverse_c3 import Act, Petition, Admission, Refusal, Route, Ack


def _manifest_dict(m) -> dict:
    return {
        "entity_id": m.entity_id, "name": m.name,
        "protocol_version": m.protocol_version,
        "law_url": m.law_url, "act_endpoint": m.act_endpoint,
        "log_endpoint": m.log_endpoint,
        "sub_registry_endpoint": m.sub_registry_endpoint,
    }


def _response_dict(r) -> dict:
    if isinstance(r, Admission):
        return {"kind": "admission",
                "entity_id": r.entity_id, "timestamp": r.timestamp}
    if isinstance(r, Refusal):
        return {"kind": "refusal", "reason": r.reason}
    if isinstance(r, Route):
        return {"kind": "route",
                "target_manifest": _manifest_dict(r.target_manifest),
                "reason": r.reason}
    if isinstance(r, Ack):
        return {"kind": "ack",
                "entity_id": r.entity_id, "timestamp": r.timestamp}
    raise TypeError(type(r).__name__)


def _log_entry_dict(e) -> dict:
    return {"timestamp": e.timestamp, "kind": e.kind,
            "actor_token": e.actor_token, "data": e.data}


class WorldProtocolServer:
    """Expose any WorldProtocol as WCP/0.1 HTTP."""

    def __init__(self, entity: Any, host: str = "127.0.0.1",
                 port: int = 8080):
        self.entity = entity
        self.host = host
        self.port = port
        self._httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def _make_handler(self):
        entity = self.entity

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status: int, payload: dict):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass  # silence

            def do_GET(self):
                try:
                    url = urlparse(self.path)
                    if url.path == "/manifest":
                        self._send(200, _manifest_dict(entity.manifest()))
                    elif url.path == "/log":
                        qs = parse_qs(url.query)
                        since = qs.get("since", [None])[0]
                        entries = entity.log_since(since)
                        self._send(200, {
                            "entries": [_log_entry_dict(e) for e in entries],
                        })
                    else:
                        self._send(404, {"error": "not found"})
                except Exception as e:
                    self._send(500, {"error": str(e)})

            def do_POST(self):
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    if self.path == "/petition":
                        p = Petition(
                            petitioner_token=body["petitioner_token"],
                            petitioner_name=body["petitioner_name"],
                            passport_admissions=tuple(
                                tuple(x) for x in body.get(
                                    "passport_admissions", [])),
                            message=body["message"],
                            target=body.get("target"),
                        )
                        r = entity.petition(p)
                        self._send(200, _response_dict(r))
                    elif self.path == "/act":
                        a = Act(
                            actor_token=body["actor_token"],
                            type=body["type"],
                            payload=body["payload"],
                        )
                        r = entity.act(a)
                        self._send(200, _response_dict(r))
                    else:
                        self._send(404, {"error": "not found"})
                except (KeyError, ValueError) as e:
                    self._send(400, {"error": str(e)})
                except Exception as e:
                    self._send(500, {"error": str(e)})

        return Handler

    def serve_forever(self):
        self._httpd = HTTPServer(
            (self.host, self.port), self._make_handler())
        self._httpd.serve_forever()

    def serve_in_thread(self):
        self._httpd = HTTPServer(
            (self.host, self.port), self._make_handler())
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
