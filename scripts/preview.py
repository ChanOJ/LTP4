#!/usr/bin/env python3
"""Serve site/ locally with the headers of the CDN edge rules (CSP, charset, wasm type).

    python3 scripts/preview.py [port]

The Content-Security-Policy is read from infra/main.tf (local.csp), so the preview shows
what the CSP of the public site allows (the Flash intro under Ruffle, in particular).
Stdlib only; for local use, never deployed.
"""
import functools
import http.server
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def csp():
    tf = (REPO / "infra" / "main.tf").read_text(encoding="utf-8")
    block = re.search(r"csp = join\(\"; \", \[(.*?)\]\)", tf, re.S).group(1)
    return "; ".join(re.findall(r'"([^"]+)"', block))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".html": "text/html; charset=iso-8859-1", ".wasm": "application/wasm"}

    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


CSP = csp()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3227
    handler = functools.partial(Handler, directory=str(REPO / "site"))
    print("http://localhost:%d/  (CSP: %s)" % (port, CSP), flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
