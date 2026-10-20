"""agentic-maker command line. One envelope on stdout, diagnostics on stderr, an exit code that names the outcome."""
import argparse
import json
import os
import re
import sys
import traceback

from agentic_maker import __version__
from agentic_maker import check as check_mod
from agentic_maker import detect as detect_mod
from agentic_maker import doctor as doctor_mod
from agentic_maker import evalemit as evalemit_mod
from agentic_maker import probe_cli as probe_cli_mod
from agentic_maker import probe_mcp as probe_mcp_mod
from agentic_maker import ledger as ledger_mod
from agentic_maker import runner as runner_mod
from agentic_maker import scenario as sc_mod
from agentic_maker import trace as trace_mod
from agentic_maker.common import project_root, read_json, write_json
from agentic_maker.envelope import CliError, Output

EXIT_TABLE = """exit codes:
  0 success   1 crash (unexpected)   2 usage   3 not_found   4 auth   5 conflict
  6 validation (a check failed: nothing passed)   7 transient (retry may help)
  8 partial (ran, but not everything passed or completed; the result says what)
     the envelope then has "status": "partial" and a "reason"; "ok" stays true because the command itself ran
output: one JSON envelope on stdout when piped or with --json (--human forces text);
        diagnostics on stderr; never prompts. Global flags: --json --human --root DIR"""


TOP_EXAMPLES = """examples:
  agentic-maker doctor                          what works here, what degrades
  agentic-maker detect .                        find the CLIs, MCP servers and skills in a project
  agentic-maker probe cli ./bin/mytool          run a CLI the way an agent would and report
  agentic-maker probe mcp "python3 /abs/server.py"        list tools, measure the budget
  agentic-maker run .agentic-maker/scenarios/x.md --dry-run   plan a fresh-agent run before spending
  agentic-maker <command> --help                options, example and exit codes of one command"""


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CliError("usage", "bad_arguments", message, suggestion="%s --help" % self.prog)


def _p(sub, name, help_, epilog=""):
    return sub.add_parser(name, help=help_, description=help_, epilog=epilog + "\n\n" + EXIT_TABLE,
                          formatter_class=argparse.RawDescriptionHelpFormatter)


def build():
    top = _Parser(prog="agentic-maker", description="Design agent-facing tools and test them by derailment.",
                  epilog=TOP_EXAMPLES + "\n\n" + EXIT_TABLE, formatter_class=argparse.RawDescriptionHelpFormatter)
    top.add_argument("--version", action="version", version="agentic-maker " + __version__)
    top.add_argument("--json", action="store_true", help="force the JSON envelope (default when stdout is not a terminal)")
    top.add_argument("--human", action="store_true", help="force readable text")
    top.add_argument("--root", metavar="DIR", help="project root (default: the nearest directory with .agentic-maker, .git or .claude-plugin)")
    sub = top.add_subparsers(dest="cmd", metavar="<command>", parser_class=_Parser)

    _p(sub, "doctor", "Report what is installed, what works and what degrades. Read-only; never launches agy.",
       "example:\n  agentic-maker doctor --json | jq .result.ready_for")

    r = _p(sub, "run", "Run one scenario in a fresh agent and keep the whole record (trace, env, receipts input).",
           "examples:\n  agentic-maker run .agentic-maker/scenarios/add-json.md --dry-run\n"
           "  agentic-maker run .agentic-maker/scenarios/add-json.md --session \"$CLAUDE_SESSION_ID\"\n"
           "  agentic-maker run s.md --runner existing --from ~/.claude/projects/<cwd>/<session>.jsonl")
    r.add_argument("scenario", help="scenario file, or just its name when it lives in .agentic-maker/scenarios/")
    r.add_argument("--runner", choices=["headless", "existing"], default=None, help="default: the scenario's `runner`")
    r.add_argument("--from", dest="from_file", help="existing: the stream-json file or session transcript to ingest")
    r.add_argument("--workspace", help="existing: directory whose files the receipts should check")
    r.add_argument("--run-id", help="group takes under this run id (default: timestamp-scenario)")
    r.add_argument("--session", help="orchestrator session id: records the trace in that session's ledger")
    r.add_argument("--dry-run", action="store_true", help="print the plan, cost ceiling and command; launch nothing")
    r.add_argument("--prepare", action="store_true",
                   help="live (herdr) rounds: seed the workspace and print the exact `agent start` arguments and prompt; launches nothing")
    r.add_argument("--workspace-dir", help="with --prepare: seed this dedicated scratch directory (emptied each time) instead of a new temp dir, so the trust dialog is answered once")
    r.add_argument("--self-annotate", action="store_true",
                   help="ask the worker to tag its own [STUCK]/[GUESSED]/[BROKE]/[NICE] moments (cheap, but biased: it changes what the worker does)")

    ee = _p(sub, "eval-emit", "Write a scenario as a `claude plugin eval` case (trigger check, receipts as graders, fixtures as a scaffold script): derailment finds, the eval guards in CI.",
            "example:\n  agentic-maker eval-emit release-notes --out evals\nthen: claude plugin eval <plugin dir> --scaffold --case release-notes --runs 1")
    ee.add_argument("scenario", help="scenario file or name")
    ee.add_argument("--out", default="evals", help="eval directory (default evals/, relative to the root)")

    n = _p(sub, "normalize", "Turn a record into trace.norm.jsonl and trace.md with [n] evidence references.",
           "example:\n  agentic-maker normalize .agentic-maker/runs/<run>/<scenario>/01")
    n.add_argument("source", help="a take directory, or a stream-json / session JSONL file")
    n.add_argument("--out", help="output directory (default: the take directory, or next to the file)")

    pr = _p(sub, "probe", "Black-box audit of a surface: run it the way an agent would and report what comes back.",
            "examples:\n  agentic-maker probe cli ./target/debug/mycli\n  agentic-maker probe mcp \"python3 /abs/server.py\"\n  agentic-maker probe cli-diff help-v1.txt help-v2.txt")
    psub = pr.add_subparsers(dest="what", metavar="<surface>", parser_class=_Parser)
    pc = _p(psub, "cli", "Audit a CLI: help, version, an invalid command, JSON purity, exit codes, hangs, secrets, destructive commands. "
            "Runs only --help, --version, one invalid command and the commands you declare safe; each in an empty temp dir, stdin closed, with a timeout.",
            "examples:\n  agentic-maker probe cli ./target/debug/mycli --safe-cmds safe.txt\n  agentic-maker probe cli gh --subcommands subs.txt --human\n"
            "safe.txt: one set of arguments per line, e.g. `get missing --json  # expect-exit 3`")
    pc.add_argument("binary", help="path or name of the executable (a crate or package name is not a path)")
    pc.add_argument("--safe-cmds", help="file of read-only argument lists the audit may run (one per line, `# expect-exit N` optional)")
    pc.add_argument("--safe", action="append", default=[], metavar="ARGS",
                    help="one read-only argument list the audit may run, no file needed; repeatable (e.g. --safe 'list --json' --safe 'get 1 --json  # expect-exit 0')")
    pc.add_argument("--subcommands", help="file of subcommands whose --help to check (one per line)")
    pc.add_argument("--sub", action="append", default=[], metavar="SUBCOMMAND", help="one subcommand whose --help to check; repeatable")
    pc.add_argument("--timeout", type=int, default=10, help="seconds per invocation (default 10)")
    pm = _p(psub, "mcp", "Connect to an MCP server (stdio command or unauthenticated Streamable HTTP URL), read its real tools/list and measure the budget "
            "and the definition quality. Sends only initialize, tools/list (and prompts/list, resources/list when advertised) plus tools/call for tools you declare read-only with --call.",
            "examples:\n  agentic-maker probe mcp \"python3 /abs/path/server.py\" --budget\n  agentic-maker probe mcp http://127.0.0.1:8000/mcp --call 'get_user={\"id\":\"1\"}'\n"
            "  agentic-maker probe mcp .mcp.json --server docs\nA server that needs OAuth is reported as not measured (use mcpc or the MCP Inspector).")
    pm.add_argument("target", help="a command line, an http(s) URL, or an .mcp.json file (with --server)")
    pm.add_argument("--budget", action="store_true", help="accepted so a command line can say what it is for; the budget is always computed")
    pm.add_argument("--full", action="store_true", help="include the per-tool table (omitted by default: the 5 largest definitions are in budget.largest)")
    pm.add_argument("--call", action="append", default=[], metavar="NAME=JSON", help="call this tool with these arguments (declare read-only tools only); repeatable")
    pm.add_argument("--server", help="server name when the target is an .mcp.json with several")
    pm.add_argument("--cwd", help="working directory for a stdio server (default: an empty temp dir)")
    pm.add_argument("--env", action="append", default=[], metavar="NAME[=V]", help="environment variable for a stdio server; repeatable. NAME alone passes on your own value, so a secret never sits on the command line (an .mcp.json target also carries its own env)")
    pm.add_argument("--timeout", type=int, default=20, help="seconds per request (default 20)")
    pm.add_argument("--description-chars", type=int, default=400, help="flag descriptions over N characters (default 400)")
    pm.add_argument("--schema-chars", type=int, default=2000, help="flag input schemas over N characters (default 2000)")
    pm.add_argument("--response-chars", type=int, default=4000, help="flag --call responses over N characters (default 4000)")
    pm.add_argument("--tool-threshold", type=int, default=20, help="flag more than N tools (default 20)")
    pd = _p(psub, "cli-diff", "Compare two saved help snapshots (runs nothing): added/removed commands and flags, likely breaking changes.",
            "example:\n  agentic-maker probe cli-diff help-v1.txt help-v2.txt")
    pd.add_argument("old")
    pd.add_argument("new")

    dt = _p(sub, "detect", "Find the agent-facing surfaces in a project (skills, plugins, MCP servers, CLIs, scripts). Locates only.",
            "example:\n  agentic-maker detect . --kind cli mcp")
    dt.add_argument("path", nargs="?", default=".")
    dt.add_argument("--kind", nargs="*", choices=["skill", "plugin", "mcp", "cli"], help="limit to these kinds")
    sc = _p(sub, "scan", "Locate one kind with more evidence lines than detect (5 per candidate, and for mcp the risky patterns); e.g. scan mcp finds the tool registrations.",
            "example:\n  agentic-maker scan mcp src")
    sc.add_argument("kind", choices=["skill", "plugin", "mcp", "cli"])
    sc.add_argument("path", nargs="?", default=".")

    c = _p(sub, "check", "Deterministic gates: receipts, findings, diff, nice.",
           "examples:\n  agentic-maker check receipts .agentic-maker/runs/<run>/<scenario>/01\n  agentic-maker check findings f1.json --trace <take>/trace.norm.jsonl")
    csub = c.add_subparsers(dest="what", metavar="<gate>", parser_class=_Parser)
    cr = _p(csub, "receipts", "Did the run leave the world as the scenario's Receipts say? (anti-self-report). Receipts of kind `cmd` run through /bin/sh in the workspace: `--list` shows them without running anything.",
            "example:\n  agentic-maker check receipts .agentic-maker/runs/<run>/<scenario>/01")
    cr.add_argument("take_dir", help="a take directory under .agentic-maker/runs/<run>/<scenario>/NN")
    cr.add_argument("--workspace", help="check this directory instead of the recorded workspace")
    cr.add_argument("--list", action="store_true", help="print the receipts (including every `cmd` that would run) and run nothing")
    cf = _p(csub, "findings", "Verify the reader's findings: quotes verbatim in cited events, fields valid, ids unique.",
            "example:\n  agentic-maker check findings findings/f1.json --trace <take>/trace.norm.jsonl")
    cf.add_argument("findings")
    cf.add_argument("--trace", required=True, help="the take's trace.norm.jsonl")
    cf.add_argument("--out", help="also write {verified_ids: [...]} here")
    cd = _p(csub, "diff", "Did the applied edit fix the cause, or only add a rule beside the unchanged cause?",
            "example:\n  agentic-maker check diff --findings f1.json --finding F2 --session \"$CLAUDE_SESSION_ID\"")
    cd.add_argument("--findings", required=True, help="the verified findings file")
    cd.add_argument("--finding", required=True, help="finding id")
    cd.add_argument("--session", help="the orchestrator session: judge the edit against the copy `ledger fix` kept (this fix only, no git needed)")
    cd.add_argument("--base", default="HEAD", help="without --session: the git revision to diff against (default HEAD; cumulative across rounds)")
    cd.add_argument("--justify", help="record why a flagged edit is nevertheless right (turns a flag into ok)")
    cp = _p(csub, "predicate", "Judge the findings' rerun_predicates against a NEW trace (did the fix change the behaviour?).",
            "example:\n  agentic-maker check predicate --findings f1.json --trace <new take>/trace.norm.jsonl")
    cp.add_argument("--findings", required=True)
    cp.add_argument("--trace", required=True, help="the new take's trace.norm.jsonl")
    cp.add_argument("--finding", nargs="*", help="only these ids")
    cn = _p(csub, "nice", "Did an edit delete text that a [NICE] behaviour depended on?",
            "example:\n  agentic-maker check nice --findings f1.json")
    cn.add_argument("--findings", required=True)

    lg = _p(sub, "ledger", "The derail run ledger: state that survives compaction, and the Stop gate.",
            "examples:\n  agentic-maker ledger init --session \"$CLAUDE_SESSION_ID\" --target skills/my-skill\n  agentic-maker ledger status --session \"$CLAUDE_SESSION_ID\"")
    lsub = lg.add_subparsers(dest="what", metavar="<action>", parser_class=_Parser)
    li = _p(lsub, "init", "Open a ledger for this orchestrator session.",
            "example:\n  agentic-maker ledger init --session \"$CLAUDE_SESSION_ID\" --target skills/my-skill")
    li.add_argument("--session", required=True, help="the orchestrator's session id (${CLAUDE_SESSION_ID}); the Stop gate keys on it")
    li.add_argument("--target", nargs="+", required=True, help="files or directories the fixes will edit")
    li.add_argument("--run-id", help="name of the run directory (default: a timestamp); an existing id is refused")
    li.add_argument("--budget-usd", type=float, default=10.0, help="ceiling for the workers' recorded cost; `run --session` refuses to start another run once it is spent (readers are not metered) (default 10)")
    li.add_argument("--rounds", type=int, default=5, help="fix-and-rerun rounds: `ledger fix` refuses once this many are used (default 5)")
    li.add_argument("--ttl-hours", type=float, default=6.0, help="after this long the Stop gate stops blocking (default 6)")
    li.add_argument("--force", action="store_true", help="replace this session's open ledger pointer (the old run directory is kept)")
    ls = _p(lsub, "status", "Show the ledger.", "example:\n  agentic-maker ledger status --session \"$CLAUDE_SESSION_ID\"")
    ls.add_argument("--session")
    ls.add_argument("--run-id")
    lt = _p(lsub, "trace", "Record a completed take (done automatically by `run --session`).",
            "example:\n  agentic-maker ledger trace .agentic-maker/runs/<run>/<scenario>/01 --session \"$CLAUDE_SESSION_ID\"")
    lt.add_argument("take_dir", help="a completed take directory")
    lt.add_argument("--session", required=True)
    lf = _p(lsub, "fix", "Mark verified findings as being fixed. Refuses ids that did not verify.",
            "example:\n  agentic-maker ledger fix F1 F2 --session \"$CLAUDE_SESSION_ID\" --findings f1.json --trace <take>/trace.norm.jsonl")
    lf.add_argument("ids", nargs="+")
    lf.add_argument("--session", required=True)
    lf.add_argument("--findings", required=True)
    lf.add_argument("--trace", required=True)
    lss = _p(lsub, "set-status", "Set framing|running|reading|fixing|awaiting_user (awaiting_user lets the Stop gate pass).",
             "example:\n  agentic-maker ledger set-status awaiting_user --session \"$CLAUDE_SESSION_ID\" --reason \"asked the user which scenario\"")
    lss.add_argument("status")
    lss.add_argument("--session", required=True)
    lss.add_argument("--reason")
    la = _p(lsub, "abandon", "Stop the loop; the Stop gate passes from now on.",
            "example:\n  agentic-maker ledger abandon --session \"$CLAUDE_SESSION_ID\" --reason \"the user stopped the loop\"")
    la.add_argument("--session", required=True)
    la.add_argument("--reason", required=True)
    lc = _p(lsub, "close", "Close the loop with an honest outcome.",
            "example:\n  agentic-maker ledger close --session \"$CLAUDE_SESSION_ID\" --outcome unverified --reason \"the rerun was not possible\"")
    lc.add_argument("--session", required=True)
    lc.add_argument("--outcome", choices=["clean", "open", "unverified"], required=True)
    lc.add_argument("--reason", required=True)
    _p(lsub, "gate", "Stop-hook entry point: reads the hook JSON on stdin (waits at most 2 s for it), prints a block decision or nothing. Always exits 0.",
       "example:\n  echo '{\"session_id\": \"x\"}' | agentic-maker ledger gate")
    return top


def _split_globals(argv):
    force_json = force_human = False
    root = None
    out, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            force_json = True
        elif a == "--human":
            force_human = True
        elif a == "--root" and i + 1 < len(argv):
            root = argv[i + 1]
            i += 1
        elif a.startswith("--root="):
            root = a.split("=", 1)[1]
        else:
            out.append(a)
        i += 1
    return out, force_json, force_human, root


def _scenario_path(root, s):
    """A scenario is a path, or just its name: `release-notes` means .agentic-maker/scenarios/release-notes.md."""
    p = s if os.path.isabs(s) else os.path.join(root, s)
    if os.path.exists(p):
        return p
    named = os.path.join(root, ".agentic-maker", "scenarios", s if s.endswith(".md") else s + ".md")
    return named if os.path.exists(named) else p


def dispatch(args, root, out):
    cmd = args.cmd
    if cmd == "doctor":
        res = doctor_mod.run()
        human = "python %s | claude %s | ready_for: %s\n%s" % (
            res["python"], (res["tools"]["claude"]["version"] or "missing"),
            ", ".join(k for k, v in res["ready_for"].items() if v) or "nothing",
            "\n".join("degrades: " + d for d in res["degrades"]))
        nxt = [{"command": "agentic-maker run <scenario> --dry-run", "why": "preview a scenario's plan and cost ceiling"}]
        if res["degrades"] and not res["ready_for"]["headless_runs"]:
            return out.partial(res, "headless runs are not available on this machine", nxt, human)
        return out.ok(res, nxt, human)

    if cmd == "run":
        sc = sc_mod.parse(_scenario_path(root, args.scenario))
        runner = args.runner or sc["meta"]["runner"]
        a = {"run_id": args.run_id, "dry_run": args.dry_run, "from_file": args.from_file, "workspace": args.workspace,
             "self_annotate": args.self_annotate, "workspace_dir": args.workspace_dir}
        if args.prepare:
            if args.dry_run:
                raise CliError("usage", "prepare_has_no_dry_run", "--prepare writes a scratch workspace and a take directory, so --dry-run cannot preview it",
                               suggestion="agentic-maker run %s --dry-run  (the plan and cost ceiling), then --prepare without --dry-run" % args.scenario)
            res, warns = runner_mod.prepare_live(root, sc, a)
            return out.ok(res, [{"command": "herdr tab create --cwd %s --label derail --no-focus" % res["workspace"], "why": "then follow skills/derail/references/runners/herdr.md; one herdr command per reply"}], json.dumps(res, indent=2), warnings=warns)
        if args.session and runner == "headless" and not args.dry_run:
            ledger_mod.refuse_if_over_budget(root, args.session)
        if runner == "headless":
            res, warns, code = runner_mod.run_headless(root, sc, a)
        elif runner == "existing":
            res, warns, code = runner_mod.run_existing(root, sc, a)
        else:
            raise CliError("usage", "runner_unsupported", "runner %r is not implemented in this version" % runner,
                           suggestion="use headless or existing; the herdr runner is driven by the agent through herdr-conductor rules, see skills/derail/references/runners/herdr.md")
        if res.get("dry_run"):
            return out.ok(res, [{"command": "agentic-maker run %s" % args.scenario, "why": "launch it for real"}], json.dumps(res, indent=2), warnings=warns)
        if args.session:
            try:
                ledger_mod.record_trace(root, args.session, res["take_dir"])
            except CliError as e:
                warns = warns + ["not recorded in a ledger: " + e.message]
        nxt = [{"command": "agentic-maker check receipts %s" % res["take_dir"], "why": "what the run left on disk (the agent's own report is only a claim)"},
               {"delegate": "trace-reader", "input": res["trace_md"], "why": "give the reader trace.md plus receipts.json; it returns findings as JSON"}]
        human = "%s: %s, %d events, %d tool calls (%d errors), $%s, isolated=%s\n  trace: %s" % (
            res["run_id"], res["status"], res["events"], res["tool_calls"], res["tool_errors"], res.get("cost_usd", "-"), res.get("isolated"), res["trace_md"])
        if code == 8:
            return out.partial(res, "the run ended as %s, not completed; the trace was kept" % res["status"], nxt, human, warns)
        return out.ok(res, nxt, human, warnings=warns)

    if cmd == "eval-emit":
        sc = sc_mod.parse(_scenario_path(root, args.scenario))
        res = evalemit_mod.emit(root, sc, args.out if os.path.isabs(args.out) else os.path.join(root, args.out))
        return out.ok(res, [{"command": res["run_with"], "why": "run the emitted case (needs Claude Code 2.1.269 or later)"}],
                      "wrote %s: %s" % (res["case_dir"], ", ".join(res["written"])), warnings=(res["warnings"] + (["not expressible as eval graders: %s" % "; ".join(res["receipts_not_expressible"])] if res["receipts_not_expressible"] else [])) or None)
    if cmd == "normalize":
        src = args.source if os.path.isabs(args.source) else os.path.join(root, args.source)
        if os.path.isdir(src):
            f = os.path.join(src, "stream.jsonl")
            outdir = args.out or src
        else:
            f, outdir = src, (args.out or os.path.dirname(src))
        recs, stats = trace_mod.normalize_file(f)
        norm, md = trace_mod.write_outputs(recs, stats, f, outdir)
        res = dict(stats, trace_md=md, trace_norm=norm)
        warns = []
        if stats["unparsed"] or stats["unknown"]:
            warns.append("unparsed lines: %d, unknown event types: %s" % (stats["unparsed"], json.dumps(stats["unknown"])))
        return out.ok(res, [{"delegate": "trace-reader", "input": md, "why": "the reader cites events as [n]"}],
                      "%d events -> %s" % (stats["events"], md), warnings=warns)

    if cmd == "probe":
        return dispatch_probe(args, root, out)
    if cmd in ("detect", "scan"):
        base = args.path if os.path.isabs(args.path) else os.path.join(root, args.path)
        only = None
        if os.path.isfile(base):
            base, only = os.path.dirname(base), os.path.basename(base)
        if not os.path.isdir(base):
            raise CliError("not_found", "path_not_found", "no such directory or file: %s" % base)
        rules = detect_mod.load_rules(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "surfaces.tsv"))
        kinds = [args.kind] if cmd == "scan" else (args.kind or None)
        res = detect_mod.detect(os.path.abspath(base), rules, kinds, evidence=(5 if cmd == "scan" else 2), only=only)
        if cmd == "scan" and args.kind == "mcp":
            res["mcp"] = detect_mod.mcp_signals(os.path.abspath(base), only=only)
        detect_mod.run_hints(res["root"], res["candidates"])
        nxt = []
        kinds_found = set(res["by_kind"])
        runs = [c["run"] for c in res["candidates"] if c.get("run")]
        for r in runs[:2]:
            if r["build"] and not r["built"]:
                nxt.append({"command": (r["build"] if r["in"] == "." else "cd %s && %s" % (r["in"], r["build"])), "why": "the CLI is not built yet; the probe needs the binary path, not the crate name"})
            nxt.append({"command": "agentic-maker probe cli %s" % r["binary"], "why": "audit this CLI by running it the way an agent would"})
        if "cli" in kinds_found and not runs:
            nxt.append({"command": "agentic-maker probe cli <binary> --safe-cmds <file>", "why": "audit a CLI candidate by running it"})
        if "mcp" in kinds_found:
            nxt.append({"command": "agentic-maker probe mcp <command or url> --budget", "why": "measure a real MCP server's tools"})
        if "skill" in kinds_found or "plugin" in kinds_found:
            nxt.append({"command": "/agentic-maker:derail <path>", "why": "test a skill or plugin with a fresh agent"})
        human = "%d candidate(s) in %d files: %s" % (len(res["candidates"]), res["files_scanned"], json.dumps(res["by_kind"])) + "".join(
            "\n  %s/%s  %s" % (c["kind"], c["ecosystem"], c["path"]) for c in res["candidates"][:40])
        return out.ok(res, nxt, human, warnings=(["file limit reached: the scan is partial"] if res["truncated"] else None))
    if cmd == "check":
        return dispatch_check(args, root, out)
    if cmd == "ledger":
        return dispatch_ledger(args, root, out)
    raise CliError("usage", "no_command", "choose a command", suggestion="agentic-maker --help")


def _read_lines(path, root, what):
    p = path if os.path.isabs(path) else os.path.join(root, path)
    if not os.path.isfile(p):
        raise CliError("not_found", "file_not_found", "%s file not found: %s" % (what, p))
    return [ln.strip() for ln in open(p, encoding="utf-8") if ln.strip() and not ln.lstrip().startswith("#")]


def dispatch_probe(args, root, out):
    w = args.what
    if w == "cli":
        subs = (_read_lines(args.subcommands, root, "subcommands") if args.subcommands else []) + list(args.sub) or None
        safe = (_read_lines(args.safe_cmds, root, "safe-cmds") if args.safe_cmds else []) + [a.strip() for a in args.safe if a.strip()]
        safe = safe or None
        res = probe_cli_mod.finalize(probe_cli_mod.probe(args.binary, subs, safe, args.timeout))
        if safe is None:
            res["limits"].insert(0, "no --safe-cmds were declared: only help, version and one invalid command were run, so stdout purity and exit codes of real commands are unchecked")
        lines = ["# CLI audit: %s" % res["binary"], "", "kind: %s | executed %d command(s) | findings: %s" % (res["kind"], len(res["executed"]), json.dumps(res["summary"]["by_severity"]))]
        for f in res["findings"]:
            lines.append("- [%s] %s: %s (fix: %s)" % (f["severity"], f["check"], f["why_it_matters"], f["fix"]))
        lines += ["", "executed:"] + ["  " + e for e in res["executed"]] + (["not executed:"] + ["  " + e for e in res["not_executed"]] if res["not_executed"] else [])
        nxt = []
        if safe is None:
            picks = " ".join('--safe "%s"' % c for c in res["suggested_safe"]) or '--safe "<read-only args>"'
            nxt.append({"command": "agentic-maker probe cli %s %s" % (args.binary, picks),
                        "why": "declare read-only commands (add arguments for %s) so JSON purity and exit codes are checked" % (", ".join(res["read_commands_needing_arguments"]) or "commands that need them")})
        if res["findings"]:
            return out.partial(res, "%d finding(s) in the CLI contract" % len(res["findings"]), nxt, "\n".join(lines))
        return out.ok(res, nxt, "\n".join(lines))
    if w == "cli-diff":
        a = args.old if os.path.isabs(args.old) else os.path.join(root, args.old)
        b = args.new if os.path.isabs(args.new) else os.path.join(root, args.new)
        for f in (a, b):
            if not os.path.isfile(f):
                raise CliError("not_found", "snapshot_not_found", "snapshot not found: %s" % f)
        res = probe_cli_mod.diff_help(open(a, encoding="utf-8", errors="replace").read(), open(b, encoding="utf-8", errors="replace").read())
        human = "\n".join(["added commands: %s" % res["commands_added"], "removed commands: %s" % res["commands_removed"],
                            "added flags: %s" % res["flags_added"], "removed flags: %s" % res["flags_removed"]] + ["BREAKING: " + x for x in res["likely_breaking"]])
        if res["likely_breaking"]:
            return out.partial(res, "%d likely breaking change(s)" % len(res["likely_breaking"]), [], human)
        return out.ok(res, [], human)
    if w == "mcp":
        env_pairs = {}
        for kv in args.env:
            k, _, v = kv.partition("=")
            if not _:
                if k not in os.environ:
                    raise CliError("not_found", "env_not_set", "--env %s: that variable is not set in your environment" % k,
                                   suggestion="export %s first, or pass %s=value (a secret on the command line lands in shell history)" % (k, k))
                v = os.environ[k]
            env_pairs[k] = v
        target = args.target
        if not re.match(r"^https?://", target) and os.path.exists(os.path.join(root, target)) and target.endswith(".json"):
            target = os.path.join(root, target)
        res = probe_mcp_mod.finalize(probe_mcp_mod.probe(
            target, {"description_chars": args.description_chars, "schema_chars": args.schema_chars, "response_chars": args.response_chars,
                     "tool_threshold": args.tool_threshold}, args.call, args.timeout, args.cwd, env_pairs, args.server))
        b = res["budget"]
        if not args.full:
            res["tools_omitted"] = len(res.pop("tools"))        # keep the envelope small: it is read by a model (O8 applies to us)
            res["note"] = "per-tool rows omitted; rerun with --full to include them"
        lines = ["# MCP audit: %s (%s)" % (res["server"]["name"], res["transport"]),
                 "tools: %d | definitions: %d chars, ~%d tokens (chars/4, heuristic) | avg ~%s/tool | findings: %s" % (
                     b["tools"], b["definition_chars"], b["est_tokens"], b["avg_tokens_per_tool"], json.dumps(res["summary"]["by_severity"]))]
        lines += ["- [%s] %s: %s (fix: %s)" % (f["severity"], f["id"], f["why_it_matters"], f["fix"]) for f in res["findings"]]
        nxt = [] if args.call else [{"command": "agentic-maker probe mcp %s --call '<read_only_tool>={}'" % args.target, "why": "measure a real response of a read-only tool (size, isError)"}]
        if res["findings"]:
            return out.partial(res, "%d finding(s) on the MCP surface" % len(res["findings"]), nxt, "\n".join(lines))
        return out.ok(res, nxt, "\n".join(lines))
    raise CliError("usage", "no_surface", "choose a surface: cli|cli-diff|mcp", suggestion="agentic-maker probe --help")


def _finding_file(findings_path, fid):
    data = read_json(findings_path)
    for f in (data.get("findings") if isinstance(data, dict) else data) or []:
        if isinstance(f, dict) and f.get("id") == fid:
            return (f.get("controlling_text") or {}).get("file") or ""
    raise CliError("not_found", "finding_not_found", "no finding %r in %s" % (fid, findings_path))


def dispatch_check(args, root, out):
    w = args.what
    if w == "receipts":
        td = args.take_dir if os.path.isabs(args.take_dir) else os.path.join(root, args.take_dir)
        if args.list:
            specs = check_mod.list_receipts(td)
            return out.ok({"take_dir": os.path.abspath(td), "total": len(specs), "receipts": specs},
                          [{"command": "agentic-maker check receipts %s" % td, "why": "run them (cmd receipts execute through /bin/sh in the workspace)"}],
                          "%d receipt(s)" % len(specs) + "".join("\n  %s: %s" % (r["kind"], r["spec"]) for r in specs))
        res = check_mod.check_receipts(td, args.workspace)
        human = "%d/%d receipts passed" % (res["passed"], res["total"]) + "".join("\n  FAIL %s: %s" % (r["line"] if "line" in r else r["kind"] + ": " + r["spec"], r["detail"]) for r in res["receipts"] if not r["ok"])
        if res["total"] == 0:
            return out.partial(res, "the scenario has no Receipts: nothing was checked, completion rests on the agent's own report", [], human)
        if res["failed"] == 0:
            return out.ok(res, [], human)
        if res["passed"] == 0:
            raise CliError("validation", "no_receipt_passed", "0 of %d receipts passed" % res["total"], details=res)
        return out.partial(res, "%d of %d receipts failed" % (res["failed"], res["total"]), [], human)
    if w == "findings":
        res = check_mod.check_findings(args.findings, args.trace, root)
        if args.out:
            write_json(args.out, {"verified_ids": res["verified_ids"]})
        nxt = [{"command": "agentic-maker ledger fix %s --session <id> --findings %s --trace %s" % (" ".join(res["verified_ids"]), args.findings, args.trace),
                "why": "only verified findings may be fixed"}] if res["verified_ids"] else []
        human = "%d verified, %d rejected" % (res["verified"], res["rejected"]) + "".join(
            "\n  REJECT %s: %s" % (r["id"], "; ".join(r["problems"])) for r in res["results"] if not r["verified"])
        if res["total"] == 0 or res["rejected"] == 0:
            return out.ok(res, nxt, human)
        if res["verified"] == 0:
            raise CliError("validation", "no_finding_verified", "none of %d findings verified" % res["total"], details=res,
                           suggestion="the reader must quote the trace verbatim and cite existing [n] events")
        return out.partial(res, "%d of %d findings were rejected" % (res["rejected"], res["total"]), nxt, human)
    if w == "diff":
        snap = None
        if args.session:
            led, _ = ledger_mod.load(root, session=args.session)
            fnd = _finding_file(args.findings, args.finding)
            entries = (led.get("snapshots") or {}).get(args.finding) or []
            match = [e for e in entries if os.path.realpath(e["file"]) == os.path.realpath(fnd if os.path.isabs(fnd) else os.path.join(root, fnd))]
            if not match:
                raise CliError("not_found", "no_snapshot", "`ledger fix` kept no copy of %s for finding %s" % (fnd, args.finding),
                               suggestion="run `agentic-maker ledger fix %s --session %s --findings %s --trace <norm>` before editing" % (args.finding, args.session, args.findings))
            snap = match[-1]["snapshot"]
        res = check_mod.check_diff(args.findings, args.finding, root, args.base, args.justify, snap)
        if res["verdict"] == "flag":
            raise CliError("validation", "patch_by_rule", res["reason"], details=res,
                           suggestion="rewrite or delete the quoted controlling text; if a rule truly is the fix, rerun with --justify \"<why>\"")
        if res["verdict"] == "no_change":
            raise CliError("validation", "no_change", res["reason"], details=res, suggestion="apply the fix first")
        return out.ok(res, [], "%s: %s" % (res["verdict"], res.get("reason") or res.get("note", "")))
    if w == "predicate":
        res = check_mod.check_predicates(args.findings, args.trace, args.finding)
        human = "%d passed, %d failed, %d need a judge" % (res["passed"], res["failed"], res["needs_judgement"]) + "".join(
            "\n  %s %s: %s" % ({True: "PASS", False: "FAIL", None: "JUDGE"}[r["passed"]], r["id"], r["detail"]) for r in res["results"])
        if res["total"] == 0:
            return out.ok(res, [], human, warnings=["the findings carry no rerun predicate: there is nothing to judge a fix by"])
        if res["passed"] == res["total"]:
            return out.ok(res, [], human)
        if res["passed"] == 0:
            raise CliError("validation", "predicates_not_met", "no rerun predicate passed", details=res,
                           suggestion="the controlling text still misleads: reread the new trace for the same drift")
        return out.partial(res, "%d of %d predicates not (yet) met" % (res["total"] - res["passed"], res["total"]), [], human)
    if w == "nice":
        res = check_mod.check_nice(args.findings, root)
        if res["removed"]:
            raise CliError("validation", "nice_removed", "%d [NICE] behaviour(s) lost their supporting text" % len(res["removed"]), details=res,
                           suggestion="restore the text, or set superseded_by on the nice item with the finding that replaces it")
        return out.ok(res, [], "%d nice item(s) intact" % len(res["nice"]))
    raise CliError("usage", "no_gate", "choose a gate: receipts|findings|diff|predicate|nice", suggestion="agentic-maker check --help")


def dispatch_ledger(args, root, out):
    w = args.what
    if w == "init":
        led = ledger_mod.init(root, args.session, args.target, args.run_id, args.budget_usd, args.rounds, args.ttl_hours, args.force)
        return out.ok(led, [{"command": "agentic-maker run <scenario> --session %s --run-id %s" % (args.session, led["run_id"]), "why": "first take"}],
                      "ledger %s opened for session %s" % (led["run_id"], args.session))
    if w == "status":
        led, p = ledger_mod.load(root, args.session, args.run_id)
        return out.ok(dict(led, ledger_file=p), [], "%s: %s, %d trace(s), $%s spent of $%s" % (led["run_id"], led["status"], len(led["traces"]), led["spent_usd"], led["budget_usd_total"]))
    if w == "trace":
        led = ledger_mod.record_trace(root, args.session, args.take_dir)
        return out.ok({"run_id": led["run_id"], "status": led["status"], "traces": len(led["traces"])}, [], "recorded")
    if w == "fix":
        chk = check_mod.check_findings(args.findings, args.trace, root)
        led = ledger_mod.fix(root, args.session, args.ids, set(chk["verified_ids"]),
                             args.trace if os.path.isabs(args.trace) else os.path.join(root, args.trace), args.findings)
        return out.ok({"run_id": led["run_id"], "status": led["status"], "findings": led["findings"]},
                      [{"command": "agentic-maker check diff --findings %s --finding %s --session %s" % (args.findings, args.ids[0], args.session), "why": "after the edit, check it fixed the cause"},
                       {"command": "agentic-maker run <scenario> --session %s" % args.session, "why": "a fresh run is the only proof"}],
                      "fixing: %s" % ", ".join(args.ids))
    if w == "set-status":
        led = ledger_mod.set_status(root, args.session, args.status, args.reason)
        return out.ok({"run_id": led["run_id"], "status": led["status"]}, [], led["status"])
    if w in ("abandon", "close"):
        led = ledger_mod.finish(root, args.session, w, args.reason, getattr(args, "outcome", None))
        return out.ok({"run_id": led["run_id"], "status": led["status"], "outcome": led.get("outcome")}, [], "%s -> %s" % (w, led["status"]))
    raise CliError("usage", "no_action", "choose an action", suggestion="agentic-maker ledger --help")


def _read_stdin(deadline_s):
    """The hook payload, read until EOF or until nothing arrives for deadline_s seconds (a caller with an open, silent pipe must not hang us)."""
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    import select
    fd, chunks = sys.stdin.fileno(), []
    while True:
        try:
            ready = select.select([fd], [], [], deadline_s)[0]
        except (OSError, ValueError):
            break
        if not ready:
            break
        data = os.read(fd, 65536)
        if not data:
            break
        chunks.append(data)
    return b"".join(chunks).decode("utf-8", "replace")


def main(argv):
    argv, fj, fh, root_arg = _split_globals(list(argv))
    if argv[:2] == ["ledger", "gate"] and not {"-h", "--help"} & set(argv):
        code, text = ledger_mod.gate(_read_stdin(2.0))
        if text:
            sys.stdout.write(text + "\n")
        return code  # always 0: a hook must never trap the agent
    out = Output(force_json=fj, force_human=fh)
    try:
        root = project_root(root_arg)
        args = build().parse_args(argv)
        if not args.cmd:
            if sys.stdout.isatty() and not fj:
                build().print_help()
                return 0
            raise CliError("usage", "no_command", "choose a command", suggestion="agentic-maker --help")
        return dispatch(args, root, out)
    except CliError as e:
        return out.fail(e)
    except KeyboardInterrupt:
        return out.fail(CliError("internal", "interrupted", "interrupted before it finished", suggestion="run it again", retryable=True, exit_code=130))
    except Exception as e:  # never a traceback on stdout
        if os.environ.get("AGENTIC_MAKER_DEBUG"):
            traceback.print_exc()
        return out.fail(CliError("internal", "unexpected", "%s: %s" % (type(e).__name__, e),
                                 suggestion="rerun with AGENTIC_MAKER_DEBUG=1 and report the traceback"))
