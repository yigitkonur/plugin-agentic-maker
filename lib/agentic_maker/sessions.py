"""Find the record of a session that already exists, from its id.

`--from session:<id>` finds the id wherever the harnesses keep it; `--from herdr:<pane>` asks herdr which session a pane's
agent is running (`herdr agent get` reports `agent_session` for claude, codex and agy) and then finds that. Nothing is
launched and nothing is written: this only locates a file that the harness already wrote.

Where each harness keeps a session (checked on this machine, Claude Code 2.1.304, codex-cli 0.163):
  claude  <CLAUDE_CONFIG_DIR or ~/.claude>/projects/<cwd as dashes>/<id>.jsonl  (its subagents: <id>/subagents/agent-*.jsonl)
  codex   <CODEX_HOME or ~/.codex>/{sessions,archived_sessions}/**/rollout-*-<id>.jsonl; line 1 is session_meta with the id
  agy     ~/.gemini/antigravity-cli/brain/<id>/.system_generated/logs/transcript_full.jsonl
          (transcript.jsonl beside it cuts every `content` to about 4096 characters and says so in `truncated_fields`)
"""
import glob
import json
import os
import re
import shutil
import subprocess

from agentic_maker.envelope import CliError

HARNESSES = ("claude", "codex", "agy")


def _home(*parts):
    return os.path.join(os.path.expanduser("~"), *parts)


def find_claude(sid):
    base = os.environ.get("CLAUDE_CONFIG_DIR") or _home(".claude")
    hits = glob.glob(os.path.join(base, "projects", "*", "%s.jsonl" % sid))
    return (hits[0], []) if hits else (None, [])


def find_codex(sid):
    base = os.environ.get("CODEX_HOME") or _home(".codex")
    for sub in ("sessions", "archived_sessions"):
        for dp, _, fns in os.walk(os.path.join(base, sub)):
            for fn in fns:
                if fn.startswith("rollout-") and fn.endswith("-%s.jsonl" % sid):
                    return os.path.join(dp, fn), []
    for sub in ("sessions", "archived_sessions"):                    # a renamed file: the id is in the first line
        for dp, _, fns in os.walk(os.path.join(base, sub)):
            for fn in fns:
                if fn.endswith(".jsonl"):
                    p = os.path.join(dp, fn)
                    try:
                        with open(p, encoding="utf-8", errors="replace") as f:
                            first = json.loads(f.readline() or "{}")
                        if first.get("type") == "session_meta" and (first.get("payload") or {}).get("id") == sid:
                            return p, []
                    except (OSError, ValueError):
                        continue
    return None, []


def find_agy(sid):
    logs = _home(".gemini", "antigravity-cli", "brain", sid, ".system_generated", "logs")
    full, short = os.path.join(logs, "transcript_full.jsonl"), os.path.join(logs, "transcript.jsonl")
    if os.path.isfile(full):
        return full, []
    if os.path.isfile(short):
        return short, ["only transcript.jsonl exists for this agy session: its `content` fields are cut at about 4096 characters, so a quote from a long message may not verify"]
    return None, []


FINDERS = {"claude": find_claude, "codex": find_codex, "agy": find_agy}


def _harness_of(agent):
    a = (agent or "").lower()
    return {"claude": "claude", "codex": "codex", "agy": "agy", "antigravity": "agy"}.get(a)


def _herdr_json(*args):
    exe = shutil.which("herdr")
    if not exe:
        raise CliError("not_found", "herdr_missing", "`herdr` was not found on PATH, so a pane cannot be resolved to a session",
                       suggestion="agentic-maker run <scenario> --runner existing --from session:<id>   (the session id is shown in the agent's own status line)")
    r = subprocess.run([exe] + list(args), capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise CliError("not_found", "pane_not_found", "herdr could not show %s: %s" % (args[-1], (r.stdout or r.stderr).strip()[:200]),
                       suggestion="herdr agent list   (pane ids look like w5R:p6A)")
    try:
        return json.loads(r.stdout), r.stdout
    except ValueError:
        return None, r.stdout


def _walk(o, key):
    if isinstance(o, dict):
        if key in o and isinstance(o[key], (dict, str)):
            return o[key]
        for v in o.values():
            got = _walk(v, key)
            if got:
                return got
    elif isinstance(o, list):
        for v in o:
            got = _walk(v, key)
            if got:
                return got
    return None


UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def _herdr_session(pane):
    """(harness, session id, warnings) of the agent in a herdr pane."""
    data, _ = _herdr_json("agent", "get", pane)
    s = _walk(data, "agent_session")
    if isinstance(s, dict) and s.get("value"):
        return _harness_of(s.get("agent")), s["value"], []
    agent = _walk(data, "agent")
    cwd = _walk(data, "cwd")
    if isinstance(agent, dict):
        agent, cwd = agent.get("agent"), agent.get("cwd") or cwd
    if _harness_of(agent) == "codex":
        # herdr reports no session for a Codex pane here; Codex prints its id in the status line. Take an id only if a rollout of that id
        # exists and was recorded in the pane's own working directory, so a wrong session cannot be picked silently.
        _, screen = _herdr_json("agent", "read", pane, "--source", "visible", "--lines", "80")
        for sid in dict.fromkeys(UUID.findall(screen or "")):
            path, _w = find_codex(sid)
            if path:
                try:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        meta = (json.loads(f.readline() or "{}").get("payload") or {})
                except (OSError, ValueError):
                    meta = {}
                if not cwd or os.path.realpath(meta.get("cwd") or "") == os.path.realpath(cwd):
                    return "codex", sid, ["herdr reported no session for this pane; the id was read from the pane's status line and matched a Codex rollout recorded in the same directory"]
    raise CliError("not_found", "no_session_in_pane", "herdr reports no session id for %s (the agent may not be a supported one, or has not started a session)" % pane,
                   suggestion="read the id from the agent's status line and pass --from session:<id>")


def resolve(spec):
    """spec: `session:<id>`, `session:<harness>:<id>` or `herdr:<pane>`. Returns {harness, id, path, warnings}."""
    kind, _, rest = spec.partition(":")
    harness = None
    warns0 = []
    if kind == "herdr":
        harness, sid, warns0 = _herdr_session(rest)
    elif kind == "session":
        m = re.match(r"^(claude|codex|agy):(.+)$", rest)
        harness, sid = (m.group(1), m.group(2)) if m else (None, rest)
    else:
        raise CliError("usage", "bad_session_spec", "%r is not session:<id> or herdr:<pane>" % spec)
    if not re.match(r"^[A-Za-z0-9._-]+$", sid):
        raise CliError("usage", "bad_session_id", "session id %r: only letters, digits, . - and _ are allowed" % sid)
    for h in ([harness] if harness else HARNESSES):
        if h in FINDERS:
            path, warns = FINDERS[h](sid)
            if path:
                return {"harness": h, "id": sid, "path": path, "warnings": warns0 + warns}
    raise CliError("not_found", "session_not_found", "no record of session %s%s" % (sid, " for %s" % harness if harness else ""),
                   suggestion="the harness may keep it elsewhere: pass the file itself with --from <path>")
