"""Black-box audit of a CLI an agent will drive: run it the way an agent would and look at what comes back.

Safety by construction: the only invocations are `--help`, `--version`, one invalid subcommand, and the
commands the user declared safe. Every run is in an empty temp directory, with a minimal environment, stdin
closed, a timeout, and its own process group. A script that does not read its arguments is not run at all
(`--help` on it would just run it); that decision is made from a static read of the file.
"""
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import time

from agentic_maker.envelope import CliError

STANDARD_FLAGS = ["--json", "--output", "--quiet", "--yes", "--dry-run", "--force", "--no-input", "--timeout"]
BYPASS_FLAGS = ["--yes", "--force", "--no-input", "--non-interactive", "-y"]
SECRET_FLAG = re.compile(r"--(password|passwd|token|secret|api-?key|apikey)\b(?![-_]?(file|stdin|env))", re.I)
FILE_FLAG = re.compile(r"--(token|password|secret|api-?key)[-_](file|stdin|env)|--password-stdin", re.I)
EXAMPLES = re.compile(r"(^|\s)examples?:", re.I | re.M)
EXIT_DOCS = re.compile(r"exit (code|status)|returns?\s+[0-9]|exit codes", re.I)
DESTRUCTIVE_WORD = re.compile(r"\b(delete|remove|destroy|drop|purge|wipe|reset|uninstall)\b", re.I)
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
ARG_HANDLING = re.compile(r'case\s+"?\$\{?1|getopts|argparse|click\.|typer|sys\.argv|process\.argv|\$\{?@\}?|"\$#"|os\.Args|std::env::args|clap::|cobra\.|docopt|commander|yargs', re.I)
JSON_FLAGS = ("--json", "--format=json", "-o=json")
ERR_CLASS_MIN = ("class", "message")


def _env(tmp):
    return {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "TERM": "dumb", "LANG": os.environ.get("LANG", "C.UTF-8"), "TMPDIR": tmp}


def _run(argv, tmp, timeout):
    t0 = time.time()
    p = subprocess.Popen(argv, cwd=tmp, env=_env(tmp), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True)
    timed_out = False
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(p.pid, sig)
            except OSError:
                pass
            try:
                out, err = p.communicate(timeout=3)
                break
            except subprocess.TimeoutExpired:
                continue
        else:
            out, err = b"", b""
    return {"argv": argv, "exit": None if timed_out else p.returncode, "timed_out": timed_out,
            "stdout": out.decode("utf-8", "replace")[:200000], "stderr": err.decode("utf-8", "replace")[:200000],
            "ms": int((time.time() - t0) * 1000)}


def _classify(path):
    with open(path, "rb") as f:
        head = f.read(4)
    if head[:2] == b"#!":
        return "script"
    if head in (b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce"):
        return "binary"
    return "unknown"


def _fmt(r):
    return "%s -> exit %s%s" % (" ".join(shlex.quote(a) for a in r["argv"][1:]) or "(no args)", r["exit"], " (timed out)" if r["timed_out"] else "")


def _finding(fid, check, severity, status, why, fix, evidence=None, rule=None):
    return {"id": fid, "check": check, "severity": severity, "status": status, "why_it_matters": why, "fix": fix,
            "evidence": evidence, "rule": rule}


def _is_json(text):
    try:
        json.loads(text)
        return True
    except ValueError:
        return False


def probe(binary, subcommands=None, safe_cmds=None, timeout=10):
    path = binary if os.sep in binary else shutil.which(binary)
    if not path or not os.path.exists(path):
        raise CliError("not_found", "cli_not_found", "CLI not found: %s" % binary,
                       suggestion="pass a path to the built executable (a crate or package name is not a path)")
    path = os.path.abspath(path)
    if not os.access(path, os.X_OK):
        raise CliError("validation", "not_executable", "%s is not executable" % path, suggestion="chmod +x, or build it first")
    kind = _classify(path)
    executed, not_executed, findings, outputs, runs = [], [], [], {}, []
    gate_open = True
    if kind in ("script", "unknown"):
        text = open(path, encoding="utf-8", errors="replace").read(200000)
        if "--help" not in text and not ARG_HANDLING.search(text):
            gate_open = False
            not_executed.append("%s --help: the script neither mentions --help nor reads its arguments, so running it would just run it" % os.path.basename(path))
    tmp = tempfile.mkdtemp(prefix="am-probe-")
    try:
        def go(args, label):
            if not gate_open and label != "declared":
                return None
            r = _run([path] + args, tmp, timeout)
            executed.append(_fmt(r))
            runs.append(r)
            return r

        help_r = go(["--help"], "help")
        ver_r = go(["--version"], "version")
        bogus_r = go(["__agentic_maker_probe_no_such_command__"], "bogus")
        help_text = (help_r["stdout"] + "\n" + help_r["stderr"]) if help_r else ""
        sub_rows = []
        for line in subcommands or []:
            r = go(shlex.split(line) + ["--help"], "sub")
            if r:
                help_text += "\n" + r["stdout"] + "\n" + r["stderr"]
                sub_rows.append({"subcommand": line, "help_exit": r["exit"],
                                 "examples": bool(EXAMPLES.search(r["stdout"] + r["stderr"])),
                                 "exit_codes": bool(EXIT_DOCS.search(r["stdout"] + r["stderr"]))})

        # ---- discoverability
        if help_r is None:
            findings.append(_finding("help.unknown", "help", "High", "skip",
                                     "An agent cannot learn the interface without running it, and this file does not describe itself.",
                                     "make the script answer --help without side effects", {"reason": not_executed[0]}, "cli/discovery-and-help.md"))
        else:
            if help_r["timed_out"]:
                findings.append(_finding("help.hangs", "help", "Critical", "fail", "An agent that runs --help blocks until its own timeout.",
                                         "--help must print and exit without prompting or reading stdin", {"run": _fmt(help_r)}, "cli/discovery-and-help.md"))
            elif help_r["exit"] != 0:
                findings.append(_finding("help.exit", "help", "High", "fail", "A nonzero exit from --help reads as failure; the agent may not read the text.",
                                         "exit 0 after printing help", {"run": _fmt(help_r)}, "cli/discovery-and-help.md"))
            if not EXAMPLES.search(help_text):
                findings.append(_finding("help.examples", "help", "Medium", "fail", "Without an example the agent has to guess the argument shapes.",
                                         "add an Examples: section with one real invocation per command", {"run": _fmt(help_r)}, "cli/discovery-and-help.md"))
            if not EXIT_DOCS.search(help_text):
                findings.append(_finding("help.exit_codes", "help", "Medium", "fail", "The agent cannot tell a retryable failure from a permanent one.",
                                         "document the exit codes (0 success, 2 usage, 3 not found, 4 auth, 5 conflict, 6 validation, 7 transient, 8 partial)",
                                         {"run": _fmt(help_r)}, "cli/exit-codes.md"))
            missing = [f for f in STANDARD_FLAGS if f not in help_text]
            outputs["standard_flags"] = {f: (f in help_text) for f in STANDARD_FLAGS}
            if "--json" in missing and not any(f in help_text for f in ("--format", "--output", "-o ")):
                findings.append(_finding("help.json_flag", "output", "High", "fail", "No documented machine-readable output; the agent will parse prose.",
                                         "add --json (a single JSON envelope on stdout)", {"missing_flags": missing}, "cli/envelope-and-errors.md"))
        if ver_r is not None and (ver_r["exit"] != 0 or ver_r["timed_out"]):
            findings.append(_finding("version.missing", "version", "Low", "fail", "The agent cannot report or pin which version it drove.",
                                     "add --version printing one line and exiting 0", {"run": _fmt(ver_r), "stdout": ver_r["stdout"][:120]}, "cli/discovery-and-help.md"))

        # ---- errors: an invalid command must be a usage error (exit 2) with a message
        if bogus_r is not None:
            if bogus_r["timed_out"]:
                findings.append(_finding("usage.hangs", "errors", "Critical", "fail", "An unknown command makes the CLI wait; the agent blocks.",
                                         "reject unknown commands immediately with exit 2", {"run": _fmt(bogus_r)}, "cli/exit-codes.md"))
            elif bogus_r["exit"] == 0:
                findings.append(_finding("usage.silent_success", "errors", "High", "fail", "A typo looks like success; the agent moves on with nothing done.",
                                         "exit 2 with a usage message for unknown commands", {"run": _fmt(bogus_r)}, "cli/exit-codes.md"))
            elif bogus_r["exit"] != 2:
                findings.append(_finding("usage.exit_code", "errors", "Medium", "fail",
                                         "A usage error that shares exit 1 with every other failure cannot be told apart from a crash.",
                                         "use exit 2 for usage errors and keep 1 for unexpected failures", {"run": _fmt(bogus_r)}, "cli/exit-codes.md"))

        # ---- declared safe commands
        ran_safe = 0
        for line in safe_cmds or []:
            m = re.match(r"^(.*?)(?:\s+#\s*expect-exit\s+(\d+))?\s*$", line)
            args_s, want = m.group(1), m.group(2)
            args = shlex.split(args_s)
            r = go(args, "declared")
            if r is None:
                continue
            ran_safe += 1
            wants_json = any(a in JSON_FLAGS for a in args) or (("--format" in args or "--output" in args or "-o" in args) and "json" in args)
            if r["timed_out"]:
                findings.append(_finding("hang.%s" % ran_safe, "non_interactive", "Critical", "fail",
                                         "A command that waits for a terminal blocks the agent for good.",
                                         "never prompt when stdin is not a terminal: fail fast and name the flag that answers the question",
                                         {"run": _fmt(r)}, "cli/non-interactive.md"))
                continue
            if wants_json:
                body = r["stdout"].strip()
                if r["exit"] == 0:
                    if not body or not _is_json(body):
                        findings.append(_finding("json.pure.%d" % ran_safe, "output", "High", "fail",
                                                 "The agent cannot parse stdout, so it falls back to scraping text.",
                                                 "write exactly one JSON document to stdout; move banners and progress to stderr",
                                                 {"run": _fmt(r), "stdout_head": body[:140]}, "cli/envelope-and-errors.md"))
                    elif r["stderr"].strip().startswith("{"):
                        findings.append(_finding("json.stderr.%d" % ran_safe, "output", "Medium", "fail", "JSON on stderr splits the contract across two streams.",
                                                 "stderr is for human diagnostics only", {"run": _fmt(r)}, "cli/streams-and-jsonl.md"))
                else:
                    if not body or not _is_json(body):
                        findings.append(_finding("json.error.%d" % ran_safe, "errors", "High", "fail",
                                                 "In --json mode a failure still has to be machine-readable, or the agent cannot see the class or the fix.",
                                                 "emit the error envelope {ok:false, error:{class,message,retryable,suggestion}} on stdout",
                                                 {"run": _fmt(r), "stdout_head": body[:140]}, "cli/envelope-and-errors.md"))
                    else:
                        env = json.loads(body)
                        err = env.get("error") if isinstance(env, dict) else None
                        if not isinstance(err, dict) or not all(k in err for k in ERR_CLASS_MIN):
                            findings.append(_finding("json.error_shape.%d" % ran_safe, "errors", "Medium", "fail", "An error without a class and a message is not actionable.",
                                                     "include class, message, retryable and a suggestion", {"run": _fmt(r)}, "cli/error-classes.md"))
            if want is not None and str(r["exit"]) != want:
                findings.append(_finding("exit.%d" % ran_safe, "exit_codes", "Medium", "fail", "The exit code does not name the failure class.",
                                         "return the documented code for this failure", {"run": _fmt(r), "expected": int(want)}, "cli/exit-codes.md"))
            elif want is None and r["exit"] not in (0, 2, 3, 4, 5, 6, 7, 8):
                findings.append(_finding("exit.%d" % ran_safe, "exit_codes", "Medium", "fail", "Exit %s is outside the documented 0-8 classes." % r["exit"],
                                         "map failures to the documented classes", {"run": _fmt(r)}, "cli/exit-codes.md"))

        # ---- cross-cutting signals from everything that ran
        ansi_runs = [_fmt(r) for r in runs if ANSI.search(r["stdout"])]
        if ansi_runs:
            findings.append(_finding("ansi.stdout", "output", "Medium", "fail",
                                     "Colour escape codes in piped output end up inside the values the agent parses.",
                                     "colour only when stdout is a terminal; honour NO_COLOR; never in --json output",
                                     {"runs": ansi_runs[:3]}, "cli/quiet-mode.md"))
        if SECRET_FLAG.search(help_text) and not FILE_FLAG.search(help_text):
            findings.append(_finding("secret.argv", "security", "High", "fail",
                                     "A secret passed as an argument lands in shell history, process listings and the agent's transcript.",
                                     "read secrets from a file, stdin or an environment variable; document --token-file or --password-stdin",
                                     {"help_mentions": SECRET_FLAG.search(help_text).group(0)}, "cli/auth-and-secrets.md"))
        if DESTRUCTIVE_WORD.search(help_text):
            if not any(b in help_text for b in BYPASS_FLAGS):
                findings.append(_finding("destructive.no_bypass", "safety", "High", "fail",
                                         "A destructive command with no non-interactive switch either hangs the agent on a prompt or runs with no guard.",
                                         "add --yes/--force for the prompt and make the command fail with exit 2, naming the flag, when it cannot ask",
                                         {"help_mentions": DESTRUCTIVE_WORD.search(help_text).group(0)}, "cli/non-interactive.md"))
            if "--dry-run" not in help_text:
                findings.append(_finding("destructive.no_dry_run", "safety", "Medium", "fail", "The agent cannot preview a destructive change before making it.",
                                         "add --dry-run that prints the plan and changes nothing", {"help_mentions": DESTRUCTIVE_WORD.search(help_text).group(0)}, "cli/dry-run.md"))
        sug = suggest_safe(help_text) if help_text else {"suggested_safe": [], "read_commands_needing_arguments": []}
        return {"binary": path, "kind": kind, "help_excerpt": "\n".join(help_text.splitlines()[:60]), "executed": executed, **sug, "not_executed": not_executed + (
                    ["destructive-looking commands in the help are never run: only declared safe commands are"] if DESTRUCTIVE_WORD.search(help_text) else []),
                "findings": findings, "subcommands": sub_rows, "documentation": outputs}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def finalize(result):
    """Add the summary and strip the raw runs. A finding is the product, not an error."""
    sev = {}
    for f in result["findings"]:
        sev[f["severity"]] = sev.get(f["severity"], 0) + 1
    result["summary"] = {"findings": len(result["findings"]), "by_severity": sev, "executed": len(result["executed"])}
    result["limits"] = ["a black-box probe of read-only commands; it does not prove the CLI is agent-ready",
                        "flag detection is text-based and can miss unusual help formats",
                        "commands not listed as safe were not run"]
    return result


def extract_commands(t, with_lines=False):
    """Names listed under a Commands:/Subcommands:/Available Commands: heading. A new unindented heading ends the list."""
    out, inside = {}, False
    for ln in t.splitlines():
        if re.match(r"^\s*(Commands|Subcommands|Available Commands):\s*$", ln):
            inside = True
            continue
        if not inside or not ln.strip():
            continue
        if not ln[0].isspace():
            inside = False
            continue
        if ln.lstrip().startswith("-"):
            continue
        m = re.match(r"^\s+([A-Za-z0-9][A-Za-z0-9:_-]+)([\s,]|$)", ln)
        if m:
            out[m.group(1)] = ln.strip()
    return out if with_lines else sorted(out)


READ_VERB = re.compile(r"^(list|ls|get|show|status|describe|version|whoami|search|view|inspect|info|cat|read|find|query|check|diff|log|logs)$", re.I)


def suggest_safe(help_text):
    """Read-only commands that need no positional argument, from the help text alone. Nothing here is run."""
    ok, needs_args = [], []
    for name, line in extract_commands(help_text, True).items():
        if not READ_VERB.match(name) or DESTRUCTIVE_WORD.search(line):
            continue
        (needs_args if re.search(r"[<\[]", line.split("  ")[0]) else ok).append(name)
    flag = " --json" if "--json" in help_text else ""
    return {"suggested_safe": [n + flag for n in ok], "read_commands_needing_arguments": needs_args}


def diff_help(old_text, new_text):
    """Compare two help snapshots (no CLI is run). Breaking = removed command, removed flag, changed usage line."""
    flag = re.compile(r"--[A-Za-z0-9][A-Za-z0-9_-]*")

    def flags(t):
        return sorted(set(flag.findall(t)))

    commands = extract_commands

    def usage(t):
        return sorted(set(re.sub(r"\s+", " ", ln.strip()) for ln in t.splitlines() if re.match(r"^\s*Usage:", ln, re.I)))

    of, nf, oc, nc, ou, nu = flags(old_text), flags(new_text), commands(old_text), commands(new_text), usage(old_text), usage(new_text)
    res = {"commands_added": sorted(set(nc) - set(oc)), "commands_removed": sorted(set(oc) - set(nc)),
           "flags_added": sorted(set(nf) - set(of)), "flags_removed": sorted(set(of) - set(nf))}
    breaking = ["Removed command: %s" % c for c in res["commands_removed"]] + ["Removed flag: %s" % f for f in res["flags_removed"]]
    if ou != nu:
        breaking.append("Usage line changed; inspect the command grammar for positional or required-flag changes")
    res["likely_breaking"] = breaking
    res["limits"] = ["command extraction is heuristic and works best with Commands:/Subcommands: sections",
                     "aliases, hidden commands and per-command flag scopes are invisible unless they appear in the snapshot",
                     "it cannot prove runtime compatibility; pair it with real stdout/stderr and exit-code checks"]
    return res
