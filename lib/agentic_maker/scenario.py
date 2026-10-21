"""Scenario files: flat `key: value` front matter plus four sections.

A value that starts with [ { " or is a number/true/false/null is parsed as JSON; anything else is a string.
"""
import json
import os
import re

from agentic_maker.envelope import CliError

KINDS = ("skill", "plugin", "cli", "mcp")
SECTIONS = ("prompt", "implicit constraints", "fixtures", "receipts")
DEFAULTS = {
    "harness": "claude", "runner": "headless", "isolation": "clean",
    "max_turns": 20, "timeout_s": 300, "budget_usd": 1.0, "interactive": False,
    "approvals": [], "env": [], "tools": None, "allowed_tools": None,
    "permission_mode": "dontAsk", "model": "sonnet",
}
JSONISH = re.compile(r'^(\[|\{|"|-?\d|true$|false$|null$)')


def _value(raw, path, key):
    raw = raw.strip()
    if JSONISH.match(raw):
        try:
            return json.loads(raw)
        except ValueError:
            if raw[0] in '[{"':
                raise CliError("validation", "scenario_value", "%s: value of `%s` looks like JSON but does not parse: %s" % (path, key, raw))
    # plain string: drop a trailing "  # comment"
    return re.sub(r"\s+#\s.*$", "", raw)


def parse(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise CliError("not_found", "scenario_not_found", "no such scenario file: %s" % path,
                       suggestion="scenarios live in .agentic-maker/scenarios/<name>.md")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise CliError("validation", "scenario_front_matter", "%s must start with a --- front matter block" % path)
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise CliError("validation", "scenario_front_matter", "%s: front matter is not closed with ---" % path)
    meta = dict(DEFAULTS)
    for ln in lines[1:end]:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if ":" not in ln:
            raise CliError("validation", "scenario_line", "%s: front matter line has no colon: %r" % (path, ln))
        k, v = ln.split(":", 1)
        meta[k.strip()] = _value(v, path, k.strip())
    for req in ("name", "kind", "target"):
        if meta.get(req) in (None, ""):
            raise CliError("validation", "scenario_missing", "%s: front matter needs `%s`" % (path, req))
    for k in ("name", "target", "wrapper_name", "bin", "bin_name", "model", "kind"):
        if k in meta and not isinstance(meta[k], str):
            meta[k] = str(meta[k])      # `name: 12` is a name, not a number
    if meta["kind"] not in KINDS:
        raise CliError("validation", "scenario_kind", "%s: kind must be one of %s, got %r" % (path, "|".join(KINDS), meta["kind"]))
    sections = {}
    cur = None
    for ln in lines[end + 1:]:
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m and m.group(1).strip().lower().split(" (")[0] in SECTIONS:
            cur = m.group(1).strip().lower().split(" (")[0]
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(ln)
    sec = {k: "\n".join(v).strip() for k, v in sections.items()}
    if not sec.get("prompt"):
        raise CliError("validation", "scenario_prompt", "%s: needs a non-empty `## Prompt` section" % path)
    return {"meta": meta, "sections": sec, "path": os.path.abspath(path)}


def user_only_skill(sc, root):
    """(wrapper, skill name) when the target is a loose skill whose frontmatter says `disable-model-invocation: true`: a worker cannot
    choose such a skill, only a slash command in the prompt starts it. Otherwise None."""
    meta = sc["meta"]
    if meta["kind"] != "skill" or not root:
        return None
    t = str(meta["target"])
    d = t if os.path.isabs(t) else os.path.join(root, t)
    f = os.path.join(d, "SKILL.md")
    if not os.path.isfile(f) or os.path.exists(os.path.join(d, ".claude-plugin", "plugin.json")):
        return None
    head = open(f, encoding="utf-8", errors="replace").read(4000)
    m = re.match(r"^---\s*\n(.*?)\n---", head, re.S)
    fm = m.group(1) if m else ""
    if not re.search(r"(?m)^disable-model-invocation:\s*true\s*$", fm):
        return None
    nm = re.search(r"(?m)^name:\s*(\S+)", fm)
    return str(meta.get("wrapper_name") or "target"), (nm.group(1).strip("'\"") if nm else os.path.basename(d.rstrip("/")))


def target_name_warnings(sc, root=None):
    """A prompt that names the target hides the trigger layer (T1-T3). Warn, do not block.
    A skill only the user can start is the exception: its prompt has to start it, and T1 cannot be observed for it."""
    meta, prompt = sc["meta"], sc["sections"]["prompt"].lower()
    user_only = user_only_skill(sc, root)
    if user_only:
        slash = "/%s:%s" % user_only
        if prompt.lstrip().startswith(slash.lower()):
            return ["the skill has `disable-model-invocation: true`, so the prompt starts it with %s; the run tests what happens after it starts, "
                    "and T1 (was it chosen?) cannot be observed for this skill" % slash]
        return ["the skill has `disable-model-invocation: true`: a worker cannot choose it, so a run would never use it. "
                "Start the prompt with %s, then the task in a user's words" % slash]
    t = str(meta["target"])
    names = {os.path.basename(t.rstrip("/")).lower(), str(meta["name"]).lower()}
    names |= {n for n in re.split(r"[:/]", t.lower()) if len(n) > 3}
    hits = sorted(n for n in names if n and len(n) > 3 and n in prompt)
    warns = []
    if hits and meta["kind"] in ("skill", "plugin"):
        warns.append("prompt contains %s, which names the target; a user would not, and T1 (not triggered) cannot be observed" % ", ".join(repr(h) for h in hits))
    if re.search(r"(^|\s)/[a-z][\w-]*:[\w-]+", prompt):
        warns.append("prompt invokes a slash command, which bypasses skill selection")
    return warns


def fixture_steps(sc):
    """Return (copies, shell) from the Fixtures section: `- copy: src [-> dest]` lines and one fenced sh block."""
    text = sc["sections"].get("fixtures", "")
    copies = []
    for ln in text.splitlines():
        m = re.match(r"^\s*[-*]\s*copy:\s*(.+?)(?:\s*->\s*(.+))?\s*$", ln)
        if m:
            copies.append((m.group(1).strip(), (m.group(2) or "").strip()))
    sh = re.search(r"```(?:sh|bash)\n(.*?)```", text, re.S)
    return copies, (sh.group(1) if sh else "")


def writability_warnings(sc, allowed, tools):
    """A worker that cannot write files cannot satisfy a receipt that expects one: the run ends in permission denials the reader
    would report as drift (O6, a defect of the run). Say so before the spend."""
    can_write = {"Write", "Edit", "NotebookEdit", "Bash"}
    # a tool must both exist (`tools`, the --tools list) and run without a prompt (`allowed_tools`)
    if {t.split("(")[0] for t in allowed} & {t.split("(")[0] for t in tools} & can_write:
        return []
    copies, _ = fixture_steps(sc)
    seeded = {(d or os.path.basename(s.rstrip("/"))) for s, d in copies}
    need = []
    for r in receipt_specs(sc):
        if r["kind"] in ("exists", "nonempty", "regex", "type", "json"):
            p = r["spec"].split()[0] if r["spec"].split() else ""
            if p and p not in seeded:
                need.append(p)
    if not need:
        return []
    return ["no tool that writes files is both in `tools` and in `allowed_tools` (Write, Edit or Bash), so the worker cannot create %s which the receipts expect; "
            "list the tools the task needs in both, or the run ends in permission denials that look like drift" % ", ".join(sorted(set(need)))]


def receipt_specs(sc):
    """Parse `- kind: rest` lines of the Receipts section into dicts."""
    out = []
    for ln in sc["sections"].get("receipts", "").splitlines():
        m = re.match(r"^\s*[-*]\s*([a-z][a-z-]*):\s*(.+?)\s*$", ln)
        if m:
            out.append({"kind": m.group(1), "spec": m.group(2), "line": ln.strip()})
    return out
