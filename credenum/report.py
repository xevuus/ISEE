import json
from dataclasses import asdict, dataclass

from credenum.dotfile_hunter import find_dotfiles
from credenum.process_hunter import find_process_secrets
from credenum.ssh_hunter import find_ssh_keys
from credenum.token_hunter import find_tokens

# A dataclass is a class whose only job is to hold data. Writing
# `@dataclass` generates __init__, __repr__, and __eq__ for us based on
# the fields below -- no need to hand-write `def __init__(self, ...)`.
# It's the "structured record" version of the loose dicts each hunter
# returns internally.
@dataclass
class Finding:
    category: str    # "SSH_KEY" | "CRED_FILE" | "TOKEN" | "PROCESS"
    severity: str     # "HIGH" | "MEDIUM"
    location: str     # a file path, or "pid 1234 [environ]" for process findings
    detail: str


def build_report(root: str, include_process: bool = True) -> list[Finding]:
    """Run every hunter and normalize their differently-shaped results
    into one common Finding shape, so the rest of the program doesn't
    need to know each hunter's internal dict layout.

    include_process exists because find_process_secrets() always reads
    the real, live /proc -- unlike the other hunters, it isn't scoped by
    `root`. That makes it the one part of the report that can't be
    pointed at an isolated test directory, so callers who need a fully
    deterministic result (tests, CI) need a way to leave it out.
    """
    findings: list[Finding] = []

    for f in find_ssh_keys(root):
        severity = "HIGH" if f["permission_flags"] else "MEDIUM"
        detail = f"matched by {f['matched_by']}"
        if f["permission_flags"]:
            detail += " - " + ", ".join(f["permission_flags"])
        findings.append(Finding("SSH_KEY", severity, f["path"], detail))

    for f in find_dotfiles(root):
        severity = "HIGH" if f["permission_flags"] else "MEDIUM"
        findings.append(Finding("CRED_FILE", severity, f["path"], f["reason"]))

    for f in find_tokens(root):
        detail = f"{f['type']}: {f['match']}"
        findings.append(Finding("TOKEN", "HIGH", f"{f['path']}:{f['line']}", detail))

    for f in (find_process_secrets() if include_process else []):
        # environ findings are higher-confidence: a credential-shaped key
        # WITH a non-empty value already set in a live process's actual
        # environment. cmdline findings (the -p flag heuristics) are
        # noisier -- e.g. some non-credential tool's own "-p" flag --
        # so they're rated lower until a human confirms them.
        severity = "HIGH" if f["source"] == "environ" else "MEDIUM"
        location = f"pid {f['pid']} [{f['source']}]"
        detail = f"{f['type']}: {f['match']} (process: {f['process']})"
        findings.append(Finding("PROCESS", severity, location, detail))

    # Group HIGH severity first, then by category, so the report reads
    # worst-first instead of "whichever hunter happened to run first".
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    findings.sort(key=lambda x: (severity_order.get(x.severity, 9), x.category, x.location))
    return findings


def render_text(findings: list[Finding]) -> str:
    if not findings:
        return "No findings."

    lines = []
    for f in findings:
        lines.append(f"[{f.severity:6}] [{f.category:9}] {f.location}")
        lines.append(f"           -> {f.detail}")
    lines.append(f"\n{len(findings)} total finding(s).")
    return "\n".join(lines)


def render_json(findings: list[Finding]) -> str:
    return json.dumps([asdict(f) for f in findings], indent=2)
