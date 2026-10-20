"""What is installed, what works, and what degrades. Read-only. Never launches agy."""
import os
import re
import shutil
import subprocess
import sys

TOOLS = ("claude", "python3", "git", "rg", "jq", "herdr", "codex", "agy")
NEVER_RUN = {"agy"}  # a launch can have effects the plugin cannot see (account, quota)


def _version(cmd):
    try:
        r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=10)
        out = (r.stdout or r.stderr).strip().splitlines()
        return out[0][:80] if out else None
    except Exception:
        return None


def _ok(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15).returncode == 0
    except Exception:
        return False


def _ver_tuple(s):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", s or "")
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def run():
    tools = {}
    for t in TOOLS:
        p = shutil.which(t)
        tools[t] = {"present": bool(p), "path": p, "version": (_version(t) if (p and t not in NEVER_RUN) else None),
                    "note": ("found; deliberately not launched (its wrapper can switch accounts)" if (p and t in NEVER_RUN) else None)}
    caps, degrades = {}, []
    caps["python_ok"] = sys.version_info >= (3, 9)
    claude = tools["claude"]["present"]
    if claude:
        h = subprocess.run(["claude", "--help"], capture_output=True, text=True, timeout=20)
        caps["claude_restricted_flag"] = "--restricted" in (h.stdout or "")
        caps["claude_version_ok"] = _ver_tuple(tools["claude"]["version"]) >= (2, 1, 269)
        caps["claude_plugin_eval"] = _ok(["claude", "plugin", "eval", "--help"])
        caps["claude_plugin_validate"] = _ok(["claude", "plugin", "validate", "--help"])
        if not caps["claude_restricted_flag"]:
            degrades.append("this claude has no --restricted flag: headless runs cannot be isolated, so runs are in-situ with a contamination report; run `claude update`")
        if not caps["claude_plugin_eval"]:
            degrades.append("`claude plugin eval` is unavailable: eval-emit and trigger statistics are skipped; run `claude update`")
    else:
        degrades.append("claude is not on PATH: `run --runner headless` is unavailable; `--runner existing --from <record>` and all checks still work")
    if not tools["herdr"]["present"]:
        degrades.append("herdr is not installed: live interactive rounds are unavailable; headless and existing runners are unaffected")
    if not tools["rg"]["present"]:
        degrades.append("rg is missing: scans fall back to grep/python (slower)")
    if not tools["jq"]["present"]:
        degrades.append("jq is missing: the CLI does not need it; shell snippets in the docs do")
    if tools["codex"]["present"] is False:
        degrades.append("codex is not installed: Codex rollout files can still be ingested with --runner existing")
    if tools["agy"]["present"]:
        degrades.append("agy is present but is never launched by this plugin; analyse an agy session you already ran with --runner existing")
    caps["plugin_root"] = os.environ.get("CLAUDE_PLUGIN_ROOT")
    return {"tools": tools, "capabilities": caps, "degrades": degrades,
            "python": "%d.%d.%d" % sys.version_info[:3], "ready_for": {
                "headless_runs": bool(claude and caps.get("claude_restricted_flag")),
                "existing_runs": caps["python_ok"], "live_herdr": tools["herdr"]["present"],
                "eval_emit": bool(caps.get("claude_plugin_eval"))}}
