"""Connect to an MCP server the way a client does and measure what an agent would be given.

Transports: stdio (a command line) and unauthenticated Streamable HTTP (a URL). A server that needs OAuth is
reported as not measured and routed to a client built for it (mcpc / MCP Inspector). Only `initialize`,
`tools/list` (and `prompts/list`, `resources/list` when advertised) are sent, plus `tools/call` for the tools
the user declared read-only with --call. Budget numbers are chars/4 over the JSON of the real definitions:
a labelled heuristic, not a tokenizer.
"""
import difflib
import json
import os
import queue
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request

from agentic_maker import __version__
from agentic_maker.envelope import CliError

PROTOCOL = "2025-06-18"
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
DESTRUCTIVE_NAME = re.compile(r"(delete|remove|drop|destroy|purge|wipe|reset|truncate|revoke|terminate)", re.I)
VERBS = set("""get list search find fetch read show describe query lookup check count create add insert make new post send
update set edit modify change rename move patch put upload write save delete remove drop destroy purge cancel archive
run execute start stop restart deploy build open close apply approve reject validate verify export import sync
publish subscribe notify submit review merge tag assign generate summarize translate convert analyze download
login logout connect disconnect enable disable invite grant revoke fork clone ping""".split())
DEFAULTS = {"description_chars": 400, "schema_chars": 2000, "response_chars": 4000, "tool_threshold": 20}


class _Stdio(object):
    def __init__(self, argv, cwd, env):
        self.p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  start_new_session=True, bufsize=0)
        self.q, self.noise, self.errtxt, self.dead = queue.Queue(), [], [], False
        threading.Thread(target=self._read_out, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _read_out(self):
        for raw in iter(self.p.stdout.readline, b""):
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                if isinstance(msg, dict) and msg.get("jsonrpc") == "2.0":
                    self.q.put(msg)
                    continue
            except ValueError:
                pass
            self.noise.append(line[:200])
        self.dead = True
        self.q.put(None)

    def _read_err(self):
        for raw in iter(self.p.stderr.readline, b""):
            if len(self.errtxt) < 40:
                self.errtxt.append(raw.decode("utf-8", "replace").rstrip()[:200])

    def send(self, obj):
        try:
            self.p.stdin.write((json.dumps(obj) + "\n").encode())
            self.p.stdin.flush()
        except (BrokenPipeError, OSError):
            self.dead = True

    def request(self, rid, method, params, timeout):
        self.send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        end = time.time() + timeout
        while time.time() < end:
            try:
                msg = self.q.get(timeout=max(0.05, end - time.time()))
            except queue.Empty:
                break
            if msg is None:
                raise CliError("dependency_failed", "server_exited", "the server exited before answering %s" % method,
                               suggestion="read details.stderr: a missing module, secret or wrong working directory is the usual cause; fix it, then run the probe again",
                               details={"stderr": self.errtxt[-5:], "stdout_noise": self.noise[:3]}, retryable=False)
            if msg.get("method") and msg.get("id") is not None:      # a request from the server: refuse politely, never hang
                self.send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "client supports no server requests"}})
                continue
            if msg.get("id") == rid:
                return msg
        raise CliError("timeout", "server_timeout", "no answer to %s within %ss" % (method, timeout),
                       suggestion="the server may need a build, a secret or a different working directory; try --cwd / --env")

    def close(self):
        try:
            self.p.stdin.close()
        except OSError:
            pass
        for sig in (None, signal.SIGTERM, signal.SIGKILL):
            try:
                if sig:
                    os.killpg(self.p.pid, sig)
                self.p.wait(timeout=2)
                return
            except (subprocess.TimeoutExpired, OSError):
                continue


class _Http(object):
    def __init__(self, url):
        self.url, self.session, self.noise, self.errtxt = url, None, [], []

    def _post(self, obj, timeout):
        data = json.dumps(obj).encode()
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            h["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, data=data, headers=h, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                self.session = r.headers.get("Mcp-Session-Id") or self.session
                body = r.read().decode("utf-8", "replace")
                ctype = r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise CliError("auth", "server_requires_auth", "the server answered HTTP %d: it needs authentication" % e.code,
                               suggestion="authenticated servers are not measured here; use mcpc or the MCP Inspector CLI, or capture tools/list and give it to `probe mcp --from-file`")
            raise CliError("dependency_failed", "http_error", "HTTP %d from %s" % (e.code, self.url))
        except (urllib.error.URLError, OSError) as e:
            raise CliError("network", "connect_failed", "cannot reach %s: %s" % (self.url, e))
        if "text/event-stream" in ctype:
            msgs = [json.loads(ln[5:].strip()) for ln in body.splitlines() if ln.startswith("data:") and ln[5:].strip().startswith("{")]
        else:
            msgs = [json.loads(body)] if body.strip() else []
        return msgs

    def send(self, obj):
        try:
            self._post(obj, 10)
        except CliError:
            pass

    def request(self, rid, method, params, timeout):
        for m in self._post({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}, timeout):
            if m.get("id") == rid:
                return m
        raise CliError("dependency_failed", "no_response", "no JSON-RPC response to %s" % method)

    def close(self):
        pass


def _depth(schema, d=0):
    if not isinstance(schema, dict):
        return d
    kids = []
    if isinstance(schema.get("properties"), dict):
        kids += list(schema["properties"].values())
    if isinstance(schema.get("items"), dict):
        kids.append(schema["items"])
    for k in ("oneOf", "anyOf", "allOf"):
        kids += [x for x in schema.get(k, []) if isinstance(x, dict)]
    return max([_depth(c, d + 1) for c in kids] or [d])


def _count_params(schema):
    props = schema.get("properties") if isinstance(schema, dict) else None
    return len(props) if isinstance(props, dict) else 0


def _f(fid, check, severity, why, fix, evidence=None, rule=None):
    return {"id": fid, "check": check, "severity": severity, "status": "fail", "why_it_matters": why, "fix": fix, "evidence": evidence, "rule": rule}


def analyze(tools, instructions, thresholds):
    findings, rows = [], []
    n = len(tools)
    if n > 40:
        findings.append(_f("tools.count", "budget", "High", "At this many tools the definitions alone crowd the task and the agent picks wrongly.", "adopt progressive discovery or merge into intent-level tools", {"tools": n}, "mcp/patterns-progressive-discovery.md"))
    elif n > thresholds["tool_threshold"] + 10:
        findings.append(_f("tools.count", "budget", "Medium", "A warning-size tool list: every definition is paid for on every turn.", "merge or prune toward about 20 active tools", {"tools": n}, "decisions/tool-count.md"))
    elif n > thresholds["tool_threshold"]:
        findings.append(_f("tools.count", "budget", "Low", "Past the comfortable range of about 20 active tools (a diagnostic cue, not a verdict).", "check whether tools can be merged around intents", {"tools": n}, "decisions/tool-count.md"))
    if n >= 10 and not instructions:
        findings.append(_f("instructions.missing", "discovery", "Low", "Server-level guidance would tell the agent how the tools fit together.", "add server instructions: a few lines on the usual call order", None, "mcp/descriptions-structure-and-length.md"))
    names = {}
    for t in tools:
        names.setdefault(t.get("name"), 0)
        names[t.get("name")] += 1
    for nm, c in names.items():
        if c > 1:
            findings.append(_f("name.duplicate.%s" % nm, "intent", "High", "Two tools with one name: the agent cannot choose.", "give each tool a unique name", {"name": nm, "count": c}, "mcp/design-intent-based-tools.md"))
    descs = [(t.get("name"), t.get("description") or "") for t in tools]
    parent = {nm: nm for nm, _ in descs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            a, b = descs[i], descs[j]
            if a[1] and b[1] and (a[1] == b[1] or (len(a[1]) > 12 and difflib.SequenceMatcher(None, a[1], b[1]).ratio() > 0.9)):
                parent[find(a[0])] = find(b[0])
    clusters = {}
    for nm, _ in descs:
        clusters.setdefault(find(nm), []).append(nm)
    for root_name, members in sorted(clusters.items()):
        if len(members) > 1:
            findings.append(_f("boundary.%s" % members[0], "intent", "Medium",
                               "%d tools with near-identical descriptions (M7): the agent alternates or picks the wrong one." % len(members),
                               "merge them into one tool with a parameter, or state in each description what it does that the others do not",
                               {"tools": members[:12], "count": len(members)}, "mcp/descriptions-names-and-routing.md"))
    any_ann = any(t.get("annotations") for t in tools)
    if tools and not any_ann:
        findings.append(_f("annotations.none", "safety", "Medium", "Without read-only and destructive hints a client cannot gate dangerous calls.", "add readOnlyHint / destructiveHint / idempotentHint to every tool", {"tools": n}, "mcp/security/least-privilege-and-confirmation.md"))
    total_chars = 0
    for t in tools:
        name, desc = t.get("name") or "", t.get("description")
        schema = t.get("inputSchema") or {}
        d_chars, s_chars = len(desc or ""), len(json.dumps(schema, separators=(",", ":")))
        t_chars = len(json.dumps(t, separators=(",", ":"), ensure_ascii=False))
        total_chars += t_chars
        req = len(schema.get("required") or []) if isinstance(schema, dict) else 0
        depth = _depth(schema)
        row = {"name": name, "description_chars": d_chars, "schema_chars": s_chars, "definition_chars": t_chars,
               "est_tokens": (t_chars + 3) // 4, "params": _count_params(schema), "required": req, "depth": depth,
               "annotations": sorted((t.get("annotations") or {}).keys())}
        rows.append(row)
        if not NAME_RE.match(name):
            findings.append(_f("name.unsafe.%s" % name, "contract", "Medium", "Names outside [a-z][a-z0-9_]* (up to 64) break some clients and models.", "use lowercase snake_case, starting with a letter", {"name": name}, "mcp/schemas-coercion-and-portability.md"))
        if not desc:
            findings.append(_f("description.missing.%s" % name, "discovery", "High", "A tool without a description is a name the agent has to guess at.", "write one sentence: Verb + Resource, then when to use it", {"tool": name}, "mcp/descriptions-structure-and-length.md"))
        else:
            if d_chars > 800:
                findings.append(_f("description.long.%s" % name, "budget", "Medium", "Descriptions above about 200 tokens are paid for on every turn and bury the point.", "target about 100 tokens; move long examples into parameter descriptions", {"tool": name, "chars": d_chars}, "mcp/descriptions-structure-and-length.md"))
            elif d_chars > thresholds["description_chars"]:
                findings.append(_f("description.long.%s" % name, "budget", "Low", "Over the description-length cue.", "shorten", {"tool": name, "chars": d_chars}, "mcp/descriptions-structure-and-length.md"))
            if d_chars < 25:
                findings.append(_f("description.thin.%s" % name, "discovery", "Medium", "A description this short cannot say what the tool does or when to pick it over its neighbours.", "write one sentence: Verb + Resource, then when to use it and what it returns", {"tool": name, "chars": d_chars, "description": desc}, "mcp/descriptions-structure-and-length.md"))
            first = re.findall(r"[A-Za-z]+", desc)[:5]
            if first and first[0].lower() not in VERBS and not any(w.lower() in VERBS for w in first[:3]):
                findings.append(_f("description.verb.%s" % name, "discovery", "Low", "Descriptions that open with Verb + Resource are matched to the task more reliably.", "start with the action", {"tool": name, "starts": " ".join(first)}, "mcp/descriptions-structure-and-length.md"))
        if req > 6 or row["params"] > 8:
            findings.append(_f("schema.wide.%s" % name, "contract", "Medium", "Wide schemas make models drop or invent arguments.", "flatten and cut to about 6 required parameters; split the tool", {"tool": name, "params": row["params"], "required": req}, "mcp/schemas-flat-and-sized.md"))
        if depth > 2:
            findings.append(_f("schema.deep.%s" % name, "contract", "Medium", "Nested objects are where models make structural mistakes.", "flatten to at most two levels", {"tool": name, "depth": depth}, "mcp/schemas-flat-and-sized.md"))
        if isinstance(schema, dict) and any(k in schema for k in ("oneOf", "anyOf", "allOf")):
            findings.append(_f("schema.combinator.%s" % name, "contract", "Medium", "oneOf/anyOf at the top of an input schema is poorly supported by models and clients.", "split into separate tools or use optional fields", {"tool": name}, "mcp/schemas-flat-and-sized.md"))
        if s_chars > thresholds["schema_chars"]:
            findings.append(_f("schema.size.%s" % name, "budget", "Low", "A large input schema is paid for on every turn.", "trim descriptions and optional fields", {"tool": name, "chars": s_chars}, "mcp/budget-tool-definitions.md"))
        big_enum = [k for k, v in (schema.get("properties") or {}).items() if isinstance(v, dict) and len(v.get("enum") or []) > 10]
        if big_enum:
            findings.append(_f("schema.enum.%s" % name, "contract", "Low", "Enums over about 10 values are unreliable; list the values in the description and validate on the server.", "shorten the enum or validate server-side", {"tool": name, "params": big_enum}, "mcp/schemas-flat-and-sized.md"))
        undocumented = [k for k, v in (schema.get("properties") or {}).items() if isinstance(v, dict) and not v.get("description")]
        if undocumented and row["params"] > 1:
            findings.append(_f("schema.undocumented.%s" % name, "discovery", "Low", "Parameters without a description are guessed.", "describe each parameter with an example value", {"tool": name, "params": undocumented[:6]}, "mcp/descriptions-schema-split-and-examples.md"))
        if DESTRUCTIVE_NAME.search(name) and (t.get("annotations") or {}).get("destructiveHint") is not True:
            findings.append(_f("destructive.unmarked.%s" % name, "safety", "High", "A destructive-looking tool with no destructiveHint lets a client run it without a gate.", "set destructiveHint: true and say in the description that it needs confirmation", {"tool": name, "annotations": t.get("annotations")}, "mcp/security/least-privilege-and-confirmation.md"))
    return findings, rows, total_chars


def _split_target(target):
    if re.match(r"^https?://", target):
        return "http", target
    if os.path.isfile(target) and target.endswith(".json"):
        return "config", target
    return "stdio", target


def probe(target, thresholds=None, calls=None, timeout=20, cwd=None, env_pairs=None, server_name=None):
    th = dict(DEFAULTS, **(thresholds or {}))
    kind, spec = _split_target(target)
    if kind == "config":
        cfg = json.load(open(spec, encoding="utf-8"))
        servers = cfg.get("mcpServers") or {}
        if not servers:
            raise CliError("validation", "no_servers", "%s has no mcpServers" % spec)
        name = server_name or sorted(servers)[0]
        if name not in servers:
            raise CliError("not_found", "server_not_in_config", "no server %r in %s (have: %s)" % (name, spec, ", ".join(sorted(servers))))
        s = servers[name]
        if s.get("url"):
            kind, spec = "http", s["url"]
        else:
            argv = [s["command"]] + list(s.get("args") or [])
            kind, spec = "stdio", " ".join(shlex.quote(a) for a in argv)
            env_pairs = dict(s.get("env") or {}, **(env_pairs or {}))
    executed, not_executed, findings = [], [], []
    workdir = cwd or tempfile.mkdtemp(prefix="am-mcp-")
    own_dir = cwd is None
    client = None
    try:
        if kind == "http":
            client = _Http(spec)
            transport = "streamable-http"
        else:
            argv = shlex.split(spec)
            argv = [os.path.abspath(a) if (i > 0 or os.sep in a) and not os.path.isabs(a) and os.path.exists(a) else a for i, a in enumerate(argv)]   # the server runs in a temp dir
            if not argv or not shutil.which(argv[0]) and not os.path.exists(argv[0]):
                raise CliError("not_found", "server_command_not_found", "cannot run: %s" % spec,
                               suggestion="give the full command (for example `python3 /abs/path/server.py`); build it first if it needs a build")
            env = {"PATH": os.environ.get("PATH", ""), "HOME": workdir, "TMPDIR": workdir, "LANG": os.environ.get("LANG", "C.UTF-8")}
            env.update({k: str(v) for k, v in (env_pairs or {}).items()})
            client = _Stdio(argv, workdir, env)
            transport = "stdio"
        rid = [0]

        def req(method, params=None, t=None):
            rid[0] += 1
            msg = client.request(rid[0], method, params or {}, t or timeout)
            executed.append(method)
            return msg

        init = req("initialize", {"protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "agentic-maker", "version": __version__}})
        if "error" in init:
            raise CliError("dependency_failed", "initialize_failed", "initialize failed: %s" % json.dumps(init["error"])[:200])
        info = init.get("result") or {}
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools, cursor, pages = [], None, 0
        while True:
            r = req("tools/list", {"cursor": cursor} if cursor else {})
            if "error" in r:
                raise CliError("dependency_failed", "tools_list_failed", "tools/list failed: %s" % json.dumps(r["error"])[:200])
            tools += (r.get("result") or {}).get("tools") or []
            cursor = (r.get("result") or {}).get("nextCursor")
            pages += 1
            if not cursor or pages > 20:
                break
        caps = info.get("capabilities") or {}
        extra = {}
        for cap, method in (("prompts", "prompts/list"), ("resources", "resources/list")):
            if cap in caps:
                try:
                    rr = req(method)
                    extra[cap] = len((rr.get("result") or {}).get(cap) or [])
                except CliError:
                    extra[cap] = None
        call_rows = []
        by_name = {t.get("name"): t for t in tools}
        for spec_c in calls or []:
            nm, _, js = spec_c.partition("=")
            try:
                args = json.loads(js) if js else {}
            except ValueError:
                raise CliError("usage", "bad_call", "--call expects NAME=JSON, got %r" % spec_c)
            if nm not in by_name:
                not_executed.append("tools/call %s: no such tool" % nm)
                continue
            ro = (by_name[nm].get("annotations") or {}).get("readOnlyHint")
            rr = req("tools/call", {"name": nm, "arguments": args})
            res = rr.get("result") or {}
            text = "".join(c.get("text", "") for c in (res.get("content") or []) if isinstance(c, dict))
            call_rows.append({"tool": nm, "args": args, "is_error": bool(res.get("isError")), "protocol_error": "error" in rr,
                              "response_chars": len(json.dumps(res, separators=(",", ":"))), "text_head": text[:100], "declared_read_only": bool(ro)})
            c = call_rows[-1]
            if c["response_chars"] > th["response_chars"]:
                findings.append(_f("response.big.%s" % nm, "budget", "High" if c["response_chars"] > 4 * th["response_chars"] else "Medium",
                                   "A response this large crowds out the task (O8) and costs tokens on every call.", "cap and paginate; add a concise mode; signal truncation",
                                   {"tool": nm, "chars": c["response_chars"], "est_tokens": (c["response_chars"] + 3) // 4}, "mcp/budget-response-size.md"))
            if c["is_error"] and not re.search(r"expected|must |should|try |valid|use |missing|required|not found|one of|call |no such|unknown", text, re.I):
                findings.append(_f("response.error_does_not_teach.%s" % nm, "errors", "Medium", "An error that names no field, no expected value and no next call leaves the agent to repeat the same call (C5).",
                                   "say which argument was wrong, what was expected and which call to make next", {"tool": nm, "text_head": text[:100]}, "mcp/errors-framing-and-recovery.md"))
            if not c["is_error"] and re.match(r"^\s*(error|failed|failure|exception)\b", text, re.I):
                findings.append(_f("response.error_as_success.%s" % nm, "errors", "High", "A failure reported with isError false reads as success; the agent moves on with nothing done.",
                                   "set isError: true and make the message say what to change", {"tool": nm, "text_head": text[:100]}, "mcp/errors-protocol-vs-tool.md"))
        noise = list(getattr(client, "noise", []))
        if noise:
            findings.append(_f("stdio.pollution", "contract", "Critical", "Anything on stdout that is not a protocol message can corrupt the stream; some clients drop the connection.",
                               "log to stderr only; stdout carries nothing but JSON-RPC", {"first_lines": noise[:3], "lines": len(noise)}, "mcp/ops-stdio-hygiene.md"))
        f2, rows, total_chars = analyze(tools, info.get("instructions"), th)
        findings = f2 + findings
        if own_dir:
            pass
        return {
            "target": spec, "transport": transport,
            "server": {"name": (info.get("serverInfo") or {}).get("name"), "version": (info.get("serverInfo") or {}).get("version"),
                       "protocolVersion": info.get("protocolVersion"), "capabilities": sorted(caps), "has_instructions": bool(info.get("instructions"))},
            "executed": executed, "not_executed": not_executed + ["tools/call for any tool not passed with --call: only declared read-only tools are called"],
            "prompts_resources": extra,
            "budget": {"tools": len(tools), "definition_chars": total_chars, "est_tokens": (total_chars + 3) // 4,
                       "avg_tokens_per_tool": round(((total_chars + 3) // 4) / max(1, len(tools)), 1), "method": "chars/4 over the JSON of tools/list (heuristic, not a tokenizer)",
                       "thresholds": th, "largest": sorted(rows, key=lambda r: -r["definition_chars"])[:5]},
            "tools": rows, "calls": call_rows, "findings": findings,
            "limits": ["measures the definitions and the responses of the tools you declared; it does not prove the server is agent-ready",
                       "token numbers are chars/4, a rough heuristic", "authenticated servers are not measured here"],
        }
    finally:
        if client:
            client.close()
        if own_dir:
            shutil.rmtree(workdir, ignore_errors=True)


def finalize(result):
    sev = {}
    for f in result["findings"]:
        sev[f["severity"]] = sev.get(f["severity"], 0) + 1
    result["summary"] = {"findings": len(result["findings"]), "by_severity": sev, "tools": result["budget"]["tools"],
                         "est_tokens": result["budget"]["est_tokens"]}
    return result
