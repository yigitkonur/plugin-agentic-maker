import hashlib
import json
import os
import re
import tempfile
import time

from agentic_maker.envelope import CliError

STATE_DIR = ".agentic-maker"


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def project_root(arg=None):
    return os.path.abspath(arg or os.getcwd())


def state_dir(root):
    return os.path.join(root, STATE_DIR)


def runs_dir(root):
    return os.path.join(state_dir(root), "runs")


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise CliError("not_found", "file_not_found", "no such file: %s" % path)
    except ValueError as e:
        raise CliError("validation", "invalid_json", "%s is not valid JSON: %s" % (path, e))


def write_json(path, data):
    """Atomic write: a reader (or a hook) never sees half a file."""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def newest_mtime(paths, skip=(".git", "__pycache__", STATE_DIR, "node_modules")):
    """Newest modification time under the given files/directories (0 if none exist)."""
    newest = 0.0
    for p in paths:
        if os.path.isfile(p):
            newest = max(newest, os.path.getmtime(p))
        elif os.path.isdir(p):
            for dp, dns, fns in os.walk(p):
                dns[:] = [d for d in dns if d not in skip]
                for fn in fns:
                    try:
                        newest = max(newest, os.path.getmtime(os.path.join(dp, fn)))
                    except OSError:
                        pass
    return newest


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def norm_ws(text):
    return re.sub(r"\s+", " ", text or "").strip()
