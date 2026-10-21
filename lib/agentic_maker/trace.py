"""Turn a harness record into one normalized trace.

Inputs understood: Claude Code `stream-json` (claude -p --output-format stream-json) and the Claude
session transcript JSONL (~/.claude/projects/<cwd>/<session>.jsonl). Output:
  trace.norm.jsonl  one record per event: n, t, role, kind, name, tool_use_id, args, text, is_error, exit, src
  trace.md          the same, compact, one `[n]` line per event: the evidence references the reader cites
Nothing is dropped silently: events that are deliberately skipped are counted under `ignored`, events the
parser does not know are counted under `unknown`, and lines that are not JSON under `unparsed`.
"""
import json
import os
import re
from collections import Counter

from agentic_maker.envelope import CliError

IGNORED = {
    "stream_event", "rate_limit_event", "api-request", "api-request-blob", "mode", "permission-mode",
    "last-prompt", "atis-latch", "ai-title", "agent-name", "queue-operation", "file-history-snapshot",
    "file-history-delta", "custom-title", "summary", "api-request-shape", "tool_progress",
}
SYSTEM_BRIEF = {"hook_started", "hook_response", "background_tasks_changed", "task_started", "task_updated",
                "task_notification", "status", "compact_boundary", "api_retry", "stop_hook_summary", "turn_duration",
                "permission_denied"}
SYSTEM_IGNORED = {"thinking_tokens", "task_progress"}
EXCERPT = 360
FULL_LIMIT = 200000


def _flat(content):
    """tool_result content -> text"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    parts.append(b.get("text", ""))
                elif b.get("type") == "image":
                    parts.append("[image]")
                else:
                    parts.append(json.dumps(b, ensure_ascii=False, separators=(",", ":")))
            else:
                parts.append(str(b))
        return "\n".join(parts)
    return json.dumps(content, ensure_ascii=False) if content is not None else ""


def _exit_of(text):
    m = re.match(r"\s*(?:Error: )?Exit code[: ]+(-?\d+)", text or "")
    return int(m.group(1)) if m else None


class _Builder(object):
    def __init__(self, src):
        self.src = src
        self.recs = []
        self.tool_names = {}
        self.agy_pending = []          # agy numbers no tool calls: a result belongs to the oldest call still waiting

    def add(self, line, role, kind, name=None, tool_use_id=None, args=None, text=None, is_error=None, t=None, exit_code=None):
        truncated = False
        if text is not None and len(text) > FULL_LIMIT:
            text, truncated = text[:FULL_LIMIT], True
        self.recs.append({
            "n": len(self.recs) + 1, "t": t, "role": role, "kind": kind, "name": name,
            "tool_use_id": tool_use_id, "args": args, "text": text, "is_error": is_error,
            "exit": exit_code, "truncated": truncated, "src": {"file": self.src, "line": line},
        })


def _codex_text(items):
    parts = []
    for it in items or []:
        if isinstance(it, dict):
            parts.append(it.get("text") if it.get("text") is not None else json.dumps(it, ensure_ascii=False))
        else:
            parts.append(str(it))
    return "\n".join(parts)


def _codex(b, line, ev, t, ignored):
    """Codex rollout files (~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl). Observed on codex-cli 0.163."""
    ty, p = ev.get("type"), ev.get("payload") or {}
    pt = p.get("type")
    if ty == "session_meta":
        b.add(line, "system", "init", name="init", t=t, args={k: p.get(k) for k in ("id", "cwd", "model", "originator", "cli_version")},
              text="codex session %s cwd=%s" % (p.get("id"), p.get("cwd")))
    elif ty == "response_item":
        if pt == "message":
            b.add(line, p.get("role") or "assistant", "text", name=("commentary" if p.get("phase") == "commentary" else None),
                  text=_codex_text(p.get("content")), t=t)
        elif pt in ("function_call", "custom_tool_call", "local_shell_call"):
            args = p.get("arguments") if p.get("arguments") is not None else p.get("input", p.get("action"))
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    args = {"input": args}
            b.tool_names[p.get("call_id")] = p.get("name") or pt
            b.add(line, "assistant", "tool_use", name=p.get("name") or pt, tool_use_id=p.get("call_id"), args=args, t=t)
        elif pt in ("function_call_output", "custom_tool_call_output"):
            out = p.get("output")
            text = out if isinstance(out, str) else _codex_text(out)
            b.add(line, "tool", "tool_result", name=b.tool_names.get(p.get("call_id")), tool_use_id=p.get("call_id"), text=text,
                  is_error=bool(re.search(r"(?i)exit code:?\s*[1-9]|error", text[:200])) if text else False, exit_code=_exit_of(text), t=t)
        elif pt == "reasoning":
            b.add(line, "assistant", "thinking", text=_codex_text(p.get("summary")), t=t)
        else:
            ignored["response_item/%s" % pt] += 1
    elif ty == "event_msg":
        if pt in ("task_started", "task_complete"):
            b.add(line, "system", "system", name=pt, t=t, text=json.dumps({k: p.get(k) for k in ("turn_id", "duration_ms", "time_to_first_token_ms") if p.get(k) is not None}))
        elif pt == "item_completed" and (p.get("item") or {}).get("type") == "CommandExecution":
            it = p["item"]                    # the one place a Codex rollout records a command's exit code
            cmd = it.get("command")
            b.add(line, "tool", "tool_result", name="CommandExecution", args={"command": cmd}, text=it.get("aggregated_output") or "",
                  is_error=(it.get("exit_code") not in (0, None)), exit_code=it.get("exit_code"), t=t)
        else:
            ignored["event_msg/%s" % pt] += 1
    else:
        ignored[ty] += 1


AGY_TYPES = {"USER_INPUT", "USER_MESSAGE", "PLANNER_RESPONSE", "ASSISTANT_STEP", "GENERIC", "TOOL_STEP", "SYSTEM_MESSAGE",
             "ERROR_MESSAGE", "ERROR", "TASK_NOTIFICATION", "CHECKPOINT"}


def _agy(b, line, ev):
    """Antigravity CLI transcript (~/.gemini/antigravity-cli/brain/<id>/.system_generated/logs/transcript_full.jsonl). Text is kept exactly as written."""
    ty, t = ev.get("type"), ev.get("created_at")
    if ty in ("USER_INPUT", "USER_MESSAGE"):
        b.agy_pending = []
        b.add(line, "user", "text", text=ev.get("content") or "", t=t)
    elif ty in ("PLANNER_RESPONSE", "ASSISTANT_STEP"):
        if (ev.get("thinking") or "").strip():
            b.add(line, "assistant", "thinking", text=ev["thinking"], t=t)
        if (ev.get("content") or "").strip():
            b.add(line, "assistant", "text", text=ev["content"], t=t)
        for i, call in enumerate(ev.get("tool_calls") or []):
            cid = "agy-%s-%d" % (ev.get("step_index"), i)
            b.agy_pending.append((cid, call.get("name")))
            b.tool_names[cid] = call.get("name")
            b.add(line, "assistant", "tool_use", name=call.get("name"), tool_use_id=cid, args=call.get("args"), t=t)
    elif ty in ("GENERIC", "TOOL_STEP"):
        cid, name = b.agy_pending.pop(0) if b.agy_pending else (None, None)
        text = ev.get("content") or ""
        m = re.search(r"exited with code (-?\d+)", text)
        code = int(m.group(1)) if m else None
        bad = ev.get("status") in ("ERROR", "INVALID") or bool(ev.get("error")) or (code not in (None, 0)) or text.startswith("Error:")
        b.add(line, "tool", "tool_result", name=name, tool_use_id=cid, text=text, is_error=bad, exit_code=code, t=t)
    else:
        b.add(line, "system", "system", name=ty.lower(), t=t, text=ev.get("content") or ev.get("error") or "")


def _message(b, line, ev, t):
    msg = ev.get("message") or {}
    role = msg.get("role") or ev.get("type")
    content = msg.get("content")
    if isinstance(content, str):
        b.add(line, role, "text", text=content, t=t)
        return
    for blk in content or []:
        ty = blk.get("type")
        if ty == "text":
            b.add(line, role, "text", text=blk.get("text", ""), t=t)
        elif ty == "thinking":
            b.add(line, role, "thinking", text=blk.get("thinking", ""), t=t)
        elif ty == "tool_use":
            b.tool_names[blk.get("id")] = blk.get("name")
            b.add(line, role, "tool_use", name=blk.get("name"), tool_use_id=blk.get("id"), args=blk.get("input"), t=t)
        elif ty == "tool_result":
            text = _flat(blk.get("content"))
            b.add(line, "tool", "tool_result", name=b.tool_names.get(blk.get("tool_use_id")),
                  tool_use_id=blk.get("tool_use_id"), text=text, is_error=bool(blk.get("is_error")),
                  exit_code=_exit_of(text), t=t)
        else:
            b.add(line, role, "other", name=ty, text=json.dumps(blk, ensure_ascii=False)[:2000], t=t)


def normalize_file(src):
    """Return (records, stats). Raises CliError when the file is unreadable or holds no events."""
    try:
        f = open(src, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise CliError("not_found", "trace_not_found", "no such trace file: %s" % src)
    b = _Builder(src)
    ignored, unknown = Counter(), Counter()
    unparsed = 0
    results = []
    costs = []
    with f:
        for line_no, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except ValueError:
                unparsed += 1
                continue
            if not isinstance(ev, dict):
                unparsed += 1
                continue
            ty, sub = ev.get("type"), ev.get("subtype")
            t = ev.get("timestamp")
            if ty in IGNORED:
                ignored[ty] += 1
            elif ty == "system" and sub in SYSTEM_IGNORED:
                ignored["system/%s" % sub] += 1
            elif ty == "system" and sub == "init":
                brief = {k: ev.get(k) for k in ("model", "claude_code_version", "cwd", "permissionMode", "apiKeySource", "session_id")}
                b.add(line_no, "system", "init", name="init", t=t, args={
                    **brief,
                    "tools": ev.get("tools"), "skills": ev.get("skills"), "agents": ev.get("agents"),
                    "mcp_servers": ev.get("mcp_servers"),
                    "plugins": [p.get("name") for p in ev.get("plugins", [])] if isinstance(ev.get("plugins"), list) else None,
                }, text="model=%s version=%s permission=%s skills=%s plugins=%s mcp=%s" % (
                    ev.get("model"), ev.get("claude_code_version"), ev.get("permissionMode"),
                    len(ev.get("skills") or []), len(ev.get("plugins") or []), len(ev.get("mcp_servers") or [])))
            elif ty == "system" and sub in SYSTEM_BRIEF:
                if sub in ("hook_started", "hook_response"):
                    out = ev.get("output") or ev.get("stdout") or ""
                    b.add(line_no, "system", "hook", name=ev.get("hook_name") or sub, t=t,
                          text="%s%s" % (sub, (" exit=%s %s" % (ev.get("exit_code"), out[:200])) if sub == "hook_response" else ""))
                else:
                    b.add(line_no, "system", "system", name=sub, t=t, text=json.dumps({k: v for k, v in ev.items() if k not in ("type", "subtype", "uuid", "session_id")}, ensure_ascii=False)[:400])
            elif ty in ("session_meta", "response_item", "event_msg", "turn_context", "world_state", "token_usage_record"):
                _codex(b, line_no, ev, t, ignored)
            elif ty in AGY_TYPES:
                _agy(b, line_no, ev)
            elif ty == "cost-state":
                costs.append(ev.get("totalCostUSD") or 0)       # Claude session transcripts keep the running cost here
            elif ty in ("assistant", "user"):
                _message(b, line_no, ev, t)
            elif ty == "attachment":
                a = ev.get("attachment") or {}
                body = a.get("content")
                body = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
                b.add(line_no, "system", "attachment", name=a.get("type"), t=t, text=(body or "")[:1500])
            elif ty == "result":
                results.append(ev)
                b.add(line_no, "system", "result", name=sub, t=t, is_error=bool(ev.get("is_error")),
                      text=ev.get("result") if isinstance(ev.get("result"), str) else json.dumps(ev.get("result")),
                      args={k: ev.get(k) for k in ("num_turns", "total_cost_usd", "duration_ms", "stop_reason", "terminal_reason")} | {"permission_denials": ev.get("permission_denials")})
            else:
                unknown["%s/%s" % (ty, sub) if sub else str(ty)] += 1
    fmt = "jsonl"
    if not b.recs and unparsed:
        # not JSON at all: a terminal capture. Keep every line as a `screen` event so it can still be cited as [n].
        fmt, unparsed = "text", 0
        with open(src, encoding="utf-8", errors="replace") as f:
            for line_no, raw in enumerate(f, 1):
                if raw.strip():
                    b.add(line_no, "screen", "screen", text=raw.rstrip("\n"))
    if not b.recs:
        raise CliError("validation", "empty_trace", "%s holds no events this parser understands" % src,
                       details={"ignored": dict(ignored), "unknown": dict(unknown), "unparsed": unparsed},
                       suggestion="pass a Claude stream-json file or a session transcript JSONL")
    stats = {
        "format": fmt, "events": len(b.recs), "unparsed": unparsed, "ignored": dict(ignored), "unknown": dict(unknown),
        "results": len(results),
        "cost_usd": round(max([r.get("total_cost_usd") or 0 for r in results] + costs or [0]), 6),
        "turns": sum((r.get("num_turns") or 0) for r in results),
        "permission_denials": sum(len(r.get("permission_denials") or []) for r in results),
        "tool_calls": sum(1 for r in b.recs if r["kind"] == "tool_use"),
        "tool_errors": sum(1 for r in b.recs if r["kind"] == "tool_result" and r["is_error"]),
        "empty_thinking_blocks": sum(1 for r in b.recs if r["kind"] == "thinking" and not (r["text"] or "").strip()),
    }
    return b.recs, stats


def _excerpt(text, limit=EXCERPT):
    t = re.sub(r"\s+", " ", text or "").strip()
    return t if len(t) <= limit else t[:limit] + " …[+%d chars]" % (len(t) - limit)


def render_md(recs, stats, src):
    lines = ["# Trace: %s" % os.path.basename(src), "",
             "events: %d · tool calls: %d · tool errors: %d · permission denials: %d · cost: $%s · unparsed lines: %d · unknown event types: %s"
             % (stats["events"], stats["tool_calls"], stats["tool_errors"], stats["permission_denials"], stats["cost_usd"],
                stats["unparsed"], json.dumps(stats["unknown"]) if stats["unknown"] else "none"),
             "Evidence references are the `[n]` numbers below; the full, untruncated text of event n is line n of trace.norm.jsonl.", ""]
    for r in recs:
        k = r["kind"]
        if k == "tool_use":
            body = "%s %s" % (r["name"], _excerpt(json.dumps(r["args"], ensure_ascii=False)))
        elif k == "tool_result":
            tag = "ERROR" if r["is_error"] else "ok"
            if r["exit"] is not None:
                tag += " exit=%s" % r["exit"]
            body = "(%s%s) %s" % (r["name"] or "?", ", " + tag, _excerpt(r["text"]))
        elif k == "init":
            body = _excerpt(r["text"], 600)
        elif k == "thinking":
            body = "(empty: thinking text is not exposed)" if not (r["text"] or "").strip() else _excerpt(r["text"])
        else:
            nm = (" %s" % r["name"]) if r["name"] else ""
            body = _excerpt(r["text"])
            k = k + nm
        lines.append("[%d] %s %s: %s" % (r["n"], r["role"], k, body))
    return "\n".join(lines) + "\n"


def write_outputs(recs, stats, src, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    norm = os.path.join(out_dir, "trace.norm.jsonl")
    with open(norm, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    md = os.path.join(out_dir, "trace.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write(render_md(recs, stats, src))
    return norm, md


def load_norm(path):
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    out[r["n"]] = r
    except FileNotFoundError:
        raise CliError("not_found", "norm_not_found", "no such normalized trace: %s" % path,
                       suggestion="agentic-maker normalize <run-dir>")
    return out
