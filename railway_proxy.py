"""Key-checking reverse proxy in front of FlareSolverr, plus its supervisor.

Starts upstream FlareSolverr on 127.0.0.1:$UPSTREAM_PORT, then serves $PORT
(Railway injects it; default 8080). Refuses to boot without API_KEY.

Accepted credentials, any one:
  Authorization: Bearer <API_KEY>
  X-API-Key: <API_KEY>
  a leading path segment: /<API_KEY>/v1   (for clients that can only be given a
  base URL, such as Prowlarr and Sonarr's indexer proxy setting)
GET /health is open and answers from the upstream's own readiness reply.
"""
import hmac
import http.client
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = os.environ.get("API_KEY", "")
PORT = int(os.environ.get("PORT", "8080"))
UP_PORT = int(os.environ.get("UPSTREAM_PORT", "8191"))
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailers", "upgrade",
       "proxy-authorization", "proxy-authenticate", "host", "content-length"}

if len(KEY) < 16:
    sys.exit("[railway] API_KEY is unset or shorter than 16 characters; refusing to start an open FlareSolverr")


def ok(a, b):
    return hmac.compare_digest(a.encode(), b.encode())


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print("[proxy]", self.command, self.path.split("?")[0][:60], args[1] if len(args) > 1 else "", flush=True)

    def send(self, code, body=b"", ctype="application/json", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def authorised(self):
        auth = self.headers.get("Authorization", "")
        if auth.lower().startswith("bearer ") and ok(auth[7:].strip(), KEY):
            return True
        return ok(self.headers.get("X-API-Key", ""), KEY)

    def handle_any(self):
        path = self.path
        if path.split("?")[0] == "/health":
            try:
                c = http.client.HTTPConnection("127.0.0.1", UP_PORT, timeout=5)
                c.request("GET", "/")
                r = c.getresponse()
                body = r.read()
                return self.send(r.status, body)
            except OSError:
                return self.send(503, b'{"status":"starting"}')
        authed = self.authorised()
        if not authed and (path.startswith("/" + KEY + "/") or path == "/" + KEY):
            path = path[len(KEY) + 1:] or "/"
            authed = True
        if not authed:
            return self.send(401, b'{"error":"missing or wrong API key"}', extra={"WWW-Authenticate": "Bearer"})
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP | {"authorization", "x-api-key"}}
        try:
            c = http.client.HTTPConnection("127.0.0.1", UP_PORT, timeout=600)
            c.request(self.command, path, body=body, headers=headers)
            r = c.getresponse()
            data = r.read()
        except OSError as e:
            return self.send(502, ('{"error":"upstream unavailable: %s"}' % e).encode())
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = handle_any


def supervise(child):
    code = child.wait()
    print("[railway] upstream FlareSolverr exited with", code, flush=True)
    os._exit(code or 1)


env = dict(os.environ, PORT=str(UP_PORT), HOST="127.0.0.1")
env.pop("API_KEY", None)
child = subprocess.Popen(["/usr/local/bin/python", "-u", "/app/flaresolverr.py"], env=env)
threading.Thread(target=supervise, args=(child,), daemon=True).start()
print("[railway] proxy on :%d -> 127.0.0.1:%d, key %s..." % (PORT, UP_PORT, KEY[:4]), flush=True)
srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
srv.daemon_threads = True
srv.serve_forever()
