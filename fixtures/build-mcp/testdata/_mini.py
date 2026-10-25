"""A tiny MCP server loop (stdio and plain HTTP POST) for the audit fixtures. Standard library only."""
import json
import sys

PROTOCOL = "2025-06-18"


def handle(msg, spec):
    """Return a JSON-RPC response dict, or None for a notification."""
    method, mid = msg.get("method"), msg.get("id")
    if mid is None:
        return None
    if method == "initialize":
        res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": spec["name"], "version": "0.1.0"}}
        if spec.get("instructions"):
            res["instructions"] = spec["instructions"]
        return {"jsonrpc": "2.0", "id": mid, "result": res}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": spec["tools"]}}
    if method == "tools/call":
        p = msg.get("params") or {}
        fn = spec["handlers"].get(p.get("name"))
        if not fn:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "Unknown tool: %s" % p.get("name")}}
        return {"jsonrpc": "2.0", "id": mid, "result": fn(p.get("arguments") or {})}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found: %s" % method}}


def serve_stdio(spec):
    if spec.get("banner"):
        sys.stdout.write(spec["banner"] + "\n")      # planted defect in the seeded server: not protocol
        sys.stdout.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        resp = handle(msg, spec)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def serve_http(spec, port):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            msg = json.loads(self.rfile.read(n) or b"{}")
            resp = handle(msg, spec)
            if resp is None:
                self.send_response(202)
                self.end_headers()
                return
            body = json.dumps(resp).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if msg.get("method") == "initialize":
                self.send_header("Mcp-Session-Id", "fixture-session-1")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    HTTPServer(("127.0.0.1", port), H).serve_forever()


def main(spec):
    if "--http" in sys.argv:
        serve_http(spec, int(sys.argv[sys.argv.index("--http") + 1]))
    else:
        serve_stdio(spec)
