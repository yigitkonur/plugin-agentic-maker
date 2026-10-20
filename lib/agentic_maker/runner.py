"""Launch one fresh agent on a scenario and keep everything it did.

headless: `claude -p` in the verified clean-room recipe (--restricted --strict-mcp-config --plugin-dir ...).
existing: ingest a record that already exists (no launch).
"""
import json
import os
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import uuid

from agentic_maker import scenario as sc_mod
from agentic_maker import trace as trace_mod
from agentic_maker.common import read_json, runs_dir, sha256_file, slug, write_json
from agentic_maker.envelope import CliError

PASS_PREFIXES = ("CLAUDE_CODE_", "ANTHROPIC_", "CLAUDE_CONFIG_DIR", "CLOUD_ML_", "AWS_", "GOOGLE_", "VERTEX_")
PASS_NAMES = ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TERM", "TZ")
DEFAULT_TOOLS = {
    "skill": ["Read", "Glob", "Grep", "Skill", "Bash", "Write", "Edit", "Agent"],
    "plugin": ["Read", "Glob", "Grep", "Skill", "Bash", "Write", "Edit", "Agent"],
    "cli": ["Read", "Glob", "Grep", "Bash"],
    "mcp": ["Read", "Glob", "Grep"],
}
DEFAULT_ALLOWED = {
    "skill": ["Read", "Glob", "Grep", "Skill", "Agent"],
    "plugin": ["Read", "Glob", "Grep", "Skill", "Agent"],
    "cli": ["Read", "Glob", "Grep"],
    "mcp": ["Read", "Glob", "Grep"],
}
STATUS_BY_SUBTYPE = {"success": "completed", "error_max_turns": "max_turns", "error_max_budget_usd": "budget"}
WORKSPACE_MARK = ".am-workspace"
PROMPT_INDEX = 2  # position of the prompt in the command list
SELF_ANNOTATE = """

As you work, flag only the moments where the provided text changes your path:
- [STUCK] if it leaves you unable to continue; name the missing or conflicting instruction
- [GUESSED] if you had to invent a decision the text should have made explicit; point to the section that should have answered it
- [BROKE] if following it led to a command or pattern that failed; include the command and the instruction that led you there
- [NICE] if a specific sentence, example or routing cue saved you from a mistake"""


def clean_env(meta, extra=None):
    """A short allowlist: what claude itself needs, the scenario's `env:` names, and nothing from herdr."""
    env, names = {}, []
    for k, v in os.environ.items():
        if k == "ANTHROPIC_MODEL" or k.startswith("HERDR_"):
            continue
        if k in PASS_NAMES or k.startswith(PASS_PREFIXES) or k in (meta.get("env") or []):
            env[k] = v
            names.append(k)
    for k, v in (extra or {}).items():
        env[k] = v
        names.append(k)
    return env, sorted(set(names))


def _abs(root, p):
    return p if os.path.isabs(p) else os.path.abspath(os.path.join(root, p))


def _wrapper_plugin(skill_dir, run_dir, name):
    w = os.path.join(run_dir, "wrapper")
    shutil.rmtree(w, ignore_errors=True)
    os.makedirs(os.path.join(w, ".claude-plugin"))
    os.makedirs(os.path.join(w, "skills"))
    write_json(os.path.join(w, ".claude-plugin", "plugin.json"),
               {"name": name, "version": "0.0.0", "description": "generated wrapper around a loose skill directory"})
    # a copy, not a symlink: --restricted confines file tools to the working and --add-dir directories
    shutil.copytree(skill_dir, os.path.join(w, "skills", os.path.basename(skill_dir.rstrip("/"))),
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".agentic-maker"))
    return w


def plan(root, sc, args, run_dir):
    """Resolve how the target is exposed and build the command. Only side effect: the wrapper dir."""
    meta = sc["meta"]
    kind = meta["kind"]
    target = str(meta["target"])
    prompt = sc["sections"]["prompt"] + (SELF_ANNOTATE if args.get("self_annotate") else "")
    cmd = [args["claude"], "-p", prompt, "--restricted", "--strict-mcp-config"]
    exposure, warnings, path_dirs = {}, [], []
    allowed = list(meta["allowed_tools"] if meta["allowed_tools"] is not None else DEFAULT_ALLOWED[kind])
    tools = list(meta["tools"] if meta["tools"] is not None else DEFAULT_TOOLS[kind])
    if kind in ("skill", "plugin"):
        t = _abs(root, target)
        if not os.path.isdir(t):
            raise CliError("not_found", "target_not_found", "target directory not found: %s" % t)
        if os.path.exists(os.path.join(t, ".claude-plugin", "plugin.json")):
            plugin_dir, wrapped = t, False
        elif os.path.exists(os.path.join(t, "SKILL.md")):
            wname = str(meta.get("wrapper_name") or "target")
            plugin_dir, wrapped = _wrapper_plugin(t, run_dir, wname), True
            warnings.append("target is a loose skill directory: it is loaded through a generated wrapper plugin named %r, "
                            "so the worker sees %r:<skill>" % (wname, wname))
        else:
            raise CliError("validation", "target_kind", "%s has neither .claude-plugin/plugin.json nor SKILL.md" % t,
                           suggestion="point `target:` at a plugin directory or a skill directory")
        # --restricted confines Read/Glob/Grep to the working directory; a skill must be able to read its own
        # references and scripts, exactly as it can after a normal install (M0 E9)
        cmd += ["--plugin-dir", plugin_dir, "--add-dir", plugin_dir]
        exposure = {"plugin_dir": plugin_dir, "wrapped_loose_skill": wrapped, "target": t}
    elif kind == "cli":
        binp = _abs(root, str(meta.get("bin") or target.split(":", 1)[-1]))
        if not os.path.exists(binp):
            raise CliError("not_found", "bin_not_found", "CLI binary not found: %s" % binp,
                           suggestion="set `bin:` to the built executable (a crate or package name is not a path); `build:` says how to produce it")
        name = str(meta.get("bin_name") or os.path.basename(binp))
        exposure = {"bin": binp, "bin_name": name}
        path_dirs.append((binp, name))
        allowed += ["Bash(%s)" % name, "Bash(%s *)" % name]
    else:  # mcp
        if target.startswith("mcp-stdio:"):
            argv = shlex.split(target.split(":", 1)[1])
            cfg = os.path.join(run_dir, "mcp.json")
            write_json(cfg, {"mcpServers": {"target": {"command": argv[0], "args": argv[1:]}}})
            servers = ["target"]
        else:
            cfg = _abs(root, str(meta.get("mcp_config") or target.split(":", 1)[-1]))
            if not os.path.exists(cfg):
                raise CliError("not_found", "mcp_config_not_found", "MCP config not found: %s" % cfg)
            servers = list((read_json(cfg).get("mcpServers") or {}).keys())
        cmd += ["--mcp-config", cfg]
        allowed += ["mcp__%s" % s for s in servers]
        exposure = {"mcp_config": cfg, "servers": servers}
    cmd += ["--tools", ",".join(tools), "--allowedTools"] + allowed
    cmd += ["--permission-mode", str(meta["permission_mode"]),
            "--output-format", "stream-json", "--verbose", "--include-hook-events",
            "--session-id", args["session_id"], "--max-turns", str(meta["max_turns"]),
            "--max-budget-usd", str(meta["budget_usd"]), "--model", str(meta["model"])]
    return cmd, exposure, warnings, path_dirs, {"tools": tools, "allowed_tools": allowed}


def seed_workspace(root, sc, ws):
    copies, shell = sc_mod.fixture_steps(sc)
    for src, dest in copies:
        s = _abs(root, src)
        d = os.path.join(ws, dest or os.path.basename(s.rstrip("/")))
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks=True)
        elif os.path.exists(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
        else:
            raise CliError("not_found", "fixture_not_found", "fixture source not found: %s" % s)
    if shell.strip():
        r = subprocess.run(["/bin/sh", "-e", "-c", shell], cwd=ws, env={"PATH": os.environ.get("PATH", ""), "HOME": ws},
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise CliError("validation", "fixture_script_failed",
                           "fixture script exited %d: %s" % (r.returncode, (r.stderr or r.stdout).strip()[:300]))
    manifest = {}
    for dp, _, fns in os.walk(ws):
        for fn in fns:
            p = os.path.join(dp, fn)
            if not os.path.islink(p):
                manifest[os.path.relpath(p, ws)] = sha256_file(p)
    return manifest


def contamination(stream_path, kept_plugin_names):
    """The init event is the contamination report: what the worker could see."""
    init, hooks = None, 0
    with open(stream_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if not isinstance(ev, dict):
                continue
            if ev.get("type") == "system" and ev.get("subtype") == "init" and init is None:
                init = ev
            if ev.get("type") == "system" and ev.get("subtype") == "hook_started":
                hooks += 1
    if init is None:
        return {"known": False, "note": "no init event in the record: what the agent could see is unknown"}
    plugins = [{"name": p.get("name"), "source": p.get("source")} for p in init.get("plugins", [])]
    foreign = [p["name"] for p in plugins
               if p["name"] not in kept_plugin_names and not str(p.get("source", "")).endswith("@builtin")]
    return {
        "known": True, "model": init.get("model"), "claude_code_version": init.get("claude_code_version"),
        "permission_mode": init.get("permissionMode"), "api_key_source": init.get("apiKeySource"),
        "tools": init.get("tools"), "skills": init.get("skills"), "agents": init.get("agents"),
        "plugins": plugins, "mcp_servers": init.get("mcp_servers"), "hook_events": hooks,
        "foreign_plugins": foreign, "isolated": (not foreign and hooks == 0), "session_id": init.get("session_id"),
    }


def next_take_dir(root, run_id, scenario_name):
    base = os.path.join(runs_dir(root), run_id, slug(scenario_name))
    os.makedirs(base, exist_ok=True)
    n = len([d for d in os.listdir(base) if d.isdigit()]) + 1
    take = os.path.join(base, "%02d" % n)
    os.makedirs(take)
    return take


def _kill(proc):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except OSError:
            pass
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def run_headless(root, sc, args):
    meta = sc["meta"]
    claude = shutil.which(os.environ.get("AGENTIC_MAKER_CLAUDE", "claude"))
    if not claude:
        raise CliError("not_found", "claude_not_found", "`claude` was not found on PATH",
                       suggestion="install Claude Code, or use --runner existing --from <record> to analyse a run you already have",
                       next_actions=[{"command": "agentic-maker doctor", "why": "see what is available and what degrades"}])
    args = dict(args, claude=claude, session_id=args.get("session_id") or str(uuid.uuid4()))
    run_id = args.get("run_id") or "%s-%s" % (time.strftime("%Y%m%d-%H%M%S"), slug(meta["name"]))
    scratch = tempfile.mkdtemp(prefix="am-plan-")
    est = {"runner": "headless", "model": meta["model"], "max_turns": meta["max_turns"], "timeout_s": meta["timeout_s"],
           "max_budget_usd": meta["budget_usd"],
           "note": "the budget is a client-side estimate that can overshoot slightly; subscription auth has no per-token bill but uses plan limits"}
    try:
        cmd, exposure, warnings, path_dirs, toolset = plan(root, sc, args, scratch)
        warnings = warnings + sc_mod.target_name_warnings(sc)
        if args.get("dry_run"):
            shown = [("<prompt>" if i == PROMPT_INDEX else c) for i, c in enumerate(cmd)]
            return ({"dry_run": True, "plan": est, "exposure": exposure, "tools": toolset, "command": shown, "run_id": run_id},
                    warnings, 0)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    take = next_take_dir(root, run_id, meta["name"])
    cmd, exposure, _, path_dirs, toolset = plan(root, sc, args, take)
    ws = os.path.realpath(tempfile.mkdtemp(prefix="am-ws-"))
    manifest = seed_workspace(root, sc, ws)
    extra_env = {}
    if path_dirs:
        bindir = os.path.join(ws, ".am-bin")
        os.makedirs(bindir)
        for binp, name in path_dirs:
            os.symlink(binp, os.path.join(bindir, name))
        extra_env["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")
    env, env_names = clean_env(meta, extra_env)
    with open(os.path.join(take, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(cmd[PROMPT_INDEX] + "\n")
    stream_p, err_p = os.path.join(take, "stream.jsonl"), os.path.join(take, "stderr.txt")
    started, timed_out = time.time(), False
    with open(stream_p, "w", encoding="utf-8") as out, open(err_p, "w", encoding="utf-8") as err:
        proc = subprocess.Popen(cmd, cwd=ws, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
        try:
            rc = proc.wait(timeout=int(meta["timeout_s"]))
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill(proc)
            rc = proc.returncode
    finished = time.time()
    plugin_names = set()
    if exposure.get("plugin_dir"):
        try:
            plugin_names.add(read_json(os.path.join(exposure["plugin_dir"], ".claude-plugin", "plugin.json")).get("name"))
        except CliError:
            pass
    cont = contamination(stream_p, plugin_names)
    try:
        recs, stats = trace_mod.normalize_file(stream_p)
    except CliError as e:
        err_txt = open(err_p, encoding="utf-8", errors="replace").read().strip()[:400]
        raise CliError("dependency_failed", "worker_produced_no_trace",
                       "the worker exited %s without a usable record. stderr: %s" % (rc, err_txt or "(empty)"),
                       suggestion="agentic-maker doctor; then rerun with --dry-run to inspect the command",
                       details={"take_dir": take})
    norm, md = trace_mod.write_outputs(recs, stats, stream_p, take)
    last = [r for r in recs if r["kind"] == "result"]
    status = "timeout" if timed_out else (STATUS_BY_SUBTYPE.get(last[-1]["name"], "error") if last else "error")
    write_json(os.path.join(take, "run.json"), {
        "run_id": run_id, "scenario": meta["name"], "scenario_file": sc["path"], "kind": meta["kind"], "runner": "headless",
        "started_at_epoch": started, "finished_at_epoch": finished, "status": status, "claude_exit": rc,
        "session_id": args["session_id"], "workspace": ws, "seed_manifest": manifest, "self_annotated": bool(args.get("self_annotate")),
        "command": [("<prompt in prompt.txt>" if i == PROMPT_INDEX else c) for i, c in enumerate(cmd)],
        "exposure": exposure, "env_names": env_names, "toolset": toolset, "stats": stats})
    write_json(os.path.join(take, "env.json"), cont)
    result = {
        "run_id": run_id, "take_dir": take, "status": status, "claude_exit": rc, "session_id": args["session_id"],
        "workspace": ws, "cost_usd": stats["cost_usd"], "turns": stats["turns"], "events": stats["events"],
        "tool_calls": stats["tool_calls"], "tool_errors": stats["tool_errors"], "permission_denials": stats["permission_denials"],
        "trace_md": md, "trace_norm": norm, "env_json": os.path.join(take, "env.json"),
        "isolated": cont.get("isolated"), "foreign_plugins": cont.get("foreign_plugins"),
        "unparsed": stats["unparsed"], "unknown_event_types": stats["unknown"], "plan": est,
    }
    return result, warnings, (0 if status == "completed" else 8)


def _epoch(ts):
    import calendar
    try:
        return calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) + (float(ts[19:23]) if ts[19:20] == "." and ts[19:23].replace(".", "").isdigit() else 0.0)
    except (TypeError, ValueError):
        return None


def _prepared_manifest(root, workspace):
    """A live round's workspace was seeded by `run --prepare`; reuse its manifest so `unchanged` and `no-extra-files` work."""
    if not workspace:
        return {}
    base = runs_dir(root)
    for dp, _, fns in os.walk(base):
        if "run.json" in fns:
            try:
                r = read_json(os.path.join(dp, "run.json"))
            except CliError:
                continue
            if r.get("runner") == "herdr" and r.get("workspace") and os.path.realpath(r["workspace"]) == os.path.realpath(workspace):
                return r.get("seed_manifest") or {}
    return {}


def run_existing(root, sc, args):
    src = args.get("from_file")
    if not src:
        raise CliError("usage", "from_required", "--runner existing needs --from <record file>",
                       suggestion="pass a Claude stream-json file or a session transcript JSONL")
    src = _abs(root, src)
    if not os.path.isfile(src):
        raise CliError("not_found", "record_not_found", "no such record: %s" % src)
    meta = sc["meta"]
    run_id = args.get("run_id") or "%s-%s" % (time.strftime("%Y%m%d-%H%M%S"), slug(meta["name"]))
    take = next_take_dir(root, run_id, meta["name"])
    dst = os.path.join(take, "stream.jsonl")
    shutil.copy2(src, dst)
    recs, stats = trace_mod.normalize_file(dst)
    norm, md = trace_mod.write_outputs(recs, stats, dst, take)
    cont = contamination(dst, set())
    write_json(os.path.join(take, "env.json"), cont)
    stamps = [e for e in (_epoch(r.get("t")) for r in recs) if e]
    started = min(stamps) if stamps else os.path.getmtime(src) - 1
    finished = max(stamps) if stamps else os.path.getmtime(src)
    write_json(os.path.join(take, "run.json"), {
        "run_id": run_id, "scenario": meta["name"], "scenario_file": sc["path"], "kind": meta["kind"], "runner": "existing",
        "status": "ingested", "source": src, "workspace": args.get("workspace"),
        "seed_manifest": _prepared_manifest(root, args.get("workspace")), "stats": stats,
        "started_at_epoch": started, "finished_at_epoch": finished})
    result = {"run_id": run_id, "take_dir": take, "status": "ingested", "source": src, "events": stats["events"],
              "tool_calls": stats["tool_calls"], "tool_errors": stats["tool_errors"], "trace_md": md, "trace_norm": norm,
              "env_json": os.path.join(take, "env.json"), "isolated": cont.get("isolated"), "unparsed": stats["unparsed"],
              "unknown_event_types": stats["unknown"]}
    return result, sc_mod.target_name_warnings(sc), 0


def prepare_live(root, sc, args):
    """Everything a live (herdr) round needs except the agent itself: a take directory, a seeded workspace, the
    wrapper plugin, and the exact arguments for `herdr agent start ... -- <args>`. Nothing is launched here."""
    meta = sc["meta"]
    claude = shutil.which(os.environ.get("AGENTIC_MAKER_CLAUDE", "claude")) or "claude"
    args = dict(args, claude=claude, session_id=args.get("session_id") or str(uuid.uuid4()))
    run_id = args.get("run_id") or "%s-%s" % (time.strftime("%Y%m%d-%H%M%S"), slug(meta["name"]))
    take = next_take_dir(root, run_id, meta["name"])
    cmd, exposure, warnings, path_dirs, toolset = plan(root, sc, args, take)
    if args.get("workspace_dir"):
        # a stable directory: the trust dialog is answered once, not once per round. It is emptied and reseeded every time,
        # so it must be new, empty, or one this command made before (the marker); never a directory that holds anything else.
        ws = os.path.realpath(_abs(root, args["workspace_dir"]))
        home, proj = os.path.realpath(os.path.expanduser("~")), os.path.realpath(root)
        contains = lambda inner: inner == ws or inner.startswith(ws.rstrip(os.sep) + os.sep)
        if contains(home) or contains(proj) or len(ws) < 12:
            raise CliError("validation", "workspace_dir_unsafe", "refusing to empty %s: it holds your home directory or this project" % ws,
                           suggestion="pass a dedicated scratch directory that does not exist yet")
        if os.path.exists(ws):
            held = os.listdir(ws) if os.path.isdir(ws) else ["(a file)"]
            if held and WORKSPACE_MARK not in held:
                raise CliError("conflict", "workspace_dir_not_ours", "%s is not empty and was not made by `run --prepare`; it would be emptied" % ws,
                               suggestion="pass a directory that does not exist yet, or an empty one")
            shutil.rmtree(ws)
        os.makedirs(ws)
    else:
        ws = os.path.realpath(tempfile.mkdtemp(prefix="am-ws-"))
    manifest = seed_workspace(root, sc, ws)
    if args.get("workspace_dir"):
        with open(os.path.join(ws, WORKSPACE_MARK), "w") as f:
            f.write("made by agentic-maker run --prepare; emptied and reseeded on every --prepare\n")
    if path_dirs:
        bindir = os.path.join(ws, ".am-bin")
        os.makedirs(bindir)
        for binp, name in path_dirs:
            os.symlink(binp, os.path.join(bindir, name))
    prompt_file = os.path.join(take, "prompt.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(cmd[PROMPT_INDEX] + "\n")
    # arguments after `claude`: drop `-p <prompt>` (interactive agent) and the headless-only output flags
    skip_with_value = {"--output-format", "--max-turns", "--max-budget-usd"}
    tail = cmd[3:]            # drop: claude, -p, <prompt>
    out_args, k = [], 0
    while k < len(tail):
        a = tail[k]
        if a in skip_with_value:
            k += 2
        elif a in ("--verbose", "--include-hook-events"):
            k += 1
        else:
            out_args.append(a)
            k += 1
    write_json(os.path.join(take, "run.json"), {
        "run_id": run_id, "scenario": meta["name"], "scenario_file": sc["path"], "kind": meta["kind"], "runner": "herdr",
        "status": "prepared", "workspace": ws, "seed_manifest": manifest, "exposure": exposure, "toolset": toolset,
        "started_at_epoch": time.time(), "finished_at_epoch": None})
    return {"run_id": run_id, "take_dir": take, "workspace": ws, "prompt_file": prompt_file, "prompt": cmd[PROMPT_INDEX],
            "claude_args": out_args, "session_id": args["session_id"],
            "transcript": "find ~/.claude/projects -name '%s.jsonl'" % args["session_id"], "note": "the worker runs in a herdr pane, so herdr sets its own HERDR_* variables there; that is normal for a live round",
            "after": "the worker is started with --session-id, so its transcript is <session_id>.jsonl under ~/.claude/projects/ (a --restricted worker does not report agent_session to herdr); ingest it with: run <scenario> --runner existing --from <that file> --workspace <workspace>"}, warnings
