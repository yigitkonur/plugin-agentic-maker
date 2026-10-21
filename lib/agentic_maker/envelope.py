"""One output contract for every command: a JSON envelope on stdout, human diagnostics on stderr,
and an exit code that names the outcome. This is the contract the plugin asks other tools to follow."""
import json
import re
import sys

SCHEMA_VERSION = 1

# exit code by name (the one canonical table)
EXIT = {
    "success": 0, "internal": 1, "usage": 2, "not_found": 3, "auth": 4,
    "conflict": 5, "validation": 6, "transient": 7, "partial": 8,
}
# error class -> exit code
CLASS_EXIT = {
    "usage": 2, "not_found": 3, "auth": 4, "conflict": 5, "validation": 6,
    "rate_limit": 7, "timeout": 7, "network": 7, "dependency_failed": 7,
    "internal": 1, "partial_success": 8,
}
RETRYABLE = {"rate_limit", "timeout", "network", "dependency_failed"}


class CliError(Exception):
    def __init__(self, cls, code, message, suggestion=None, details=None, next_actions=None, retryable=None, exit_code=None):
        Exception.__init__(self, message)
        self._exit_code = exit_code
        self.cls = cls
        self.code = code
        self.message = message
        self.suggestion = suggestion
        self.details = details
        self.next_actions = next_actions or []
        self.retryable = retryable

    @property
    def exit_code(self):
        return self._exit_code if self._exit_code is not None else CLASS_EXIT.get(self.cls, 1)


def _mark_templates(next_actions):
    """A next action whose command still holds a <placeholder> is a template, not something to run as written."""
    out = []
    for na in next_actions or []:
        na = dict(na)
        if "<" in str(na.get("command", "")):
            na["template"] = True
        out.append(na)
    return out


def _suggested_commands(suggestion):
    """A suggestion that is (or contains, in backticks) an `agentic-maker ...` command is also a next action: the model runs it, it does not retype it."""
    if not suggestion:
        return []
    text = suggestion.strip()
    cmd = None
    if text.startswith("agentic-maker "):
        cmd = text.split(";")[0].strip()
    else:
        m = re.search(r"`(agentic-maker [^`]+)`", text)
        if m:
            cmd = m.group(1).strip()
    return [{"command": cmd, "why": "suggested by the error"}] if cmd else []


class Output(object):
    """Decides JSON vs human once, then prints the envelope."""

    def __init__(self, force_json=False, force_human=False):
        if force_json:
            self.json = True
        elif force_human:
            self.json = False
        else:
            self.json = not sys.stdout.isatty()

    def ok(self, result, next_actions=None, human=None, warnings=None, exit_code=0):
        env = {"ok": True, "result": result, "schema_version": SCHEMA_VERSION,
               "next_actions": _mark_templates(next_actions)}
        if warnings:
            env["warnings"] = warnings
        self._print(env, human)
        return exit_code

    def partial(self, result, message, next_actions=None, human=None, warnings=None):
        """The command ran and produced data, but not everything succeeded: exit 8."""
        env = {"ok": True, "status": "partial", "partial": True, "reason": message, "result": result, "schema_version": SCHEMA_VERSION,
               "next_actions": _mark_templates(next_actions)}
        if warnings:
            env["warnings"] = warnings
        self._print(env, human)
        sys.stderr.write("partial: %s\n" % message)
        return EXIT["partial"]

    def fail(self, err):
        env = {
            "ok": False,
            "error": {
                "class": err.cls, "code": err.code, "message": err.message,
                "retryable": (err.cls in RETRYABLE) if err.retryable is None else err.retryable, "suggestion": err.suggestion,
            },
            "schema_version": SCHEMA_VERSION,
            "next_actions": _mark_templates(err.next_actions or _suggested_commands(err.suggestion)),
        }
        if err.details is not None:
            env["error"]["details"] = err.details
        if self.json:
            sys.stdout.write(json.dumps(env, ensure_ascii=False) + "\n")
        line = "error [%s/%s]: %s" % (err.cls, err.code, err.message)
        if err.suggestion:
            line += "\n  try: %s" % err.suggestion
        sys.stderr.write(line + "\n")
        return err.exit_code

    def _print(self, env, human):
        if self.json:
            sys.stdout.write(json.dumps(env, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write((human if human is not None else json.dumps(env, indent=2, ensure_ascii=False)) + "\n")
            for na in env.get("next_actions", []):
                sys.stdout.write("next: %s\n" % (na.get("command") or ("spawn %s on %s" % (na.get("delegate"), na.get("input")) if na.get("delegate") else na)))
