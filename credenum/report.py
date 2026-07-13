import json
from collections import Counter
from dataclasses import asdict, dataclass

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from credenum.dotfile_hunter import find_dotfiles
from credenum.process_hunter import find_process_secrets
from credenum.ssh_hunter import find_ssh_keys
from credenum.token_hunter import find_tokens

# Friendlier display names, and the fixed order categories are always
# shown in (independent of which one happens to have the worst finding --
# unlike the overall `findings` sort, which is severity-first).
CATEGORY_LABELS = {
    "SSH_KEY": "SSH Keys",
    "CRED_FILE": "Credential Files",
    "TOKEN": "Tokens & API Keys",
    "PROCESS": "Process / Environment Secrets",
}

# rich markup strings: "[bold red]text[/bold red]" -- rich parses these
# the way HTML parses tags. bold red draws the eye to HIGH severity rows
# without needing to read every line of the report.
SEVERITY_STYLES = {"HIGH": "bold red", "MEDIUM": "bold yellow"}

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
    remediation: str  # a concrete, actionable fix -- not just "this is bad"


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
        findings.append(Finding("SSH_KEY", severity, f["path"], detail, f["remediation"]))

    for f in find_dotfiles(root):
        severity = "HIGH" if f["permission_flags"] else "MEDIUM"
        findings.append(Finding("CRED_FILE", severity, f["path"], f["reason"], f["remediation"]))

    for f in find_tokens(root):
        detail = f"{f['type']}: {f['match']}"
        findings.append(Finding("TOKEN", "HIGH", f"{f['path']}:{f['line']}", detail, f["remediation"]))

    for f in (find_process_secrets() if include_process else []):
        # environ findings are higher-confidence: a credential-shaped key
        # WITH a non-empty value already set in a live process's actual
        # environment. cmdline findings (the -p flag heuristics) are
        # noisier -- e.g. some non-credential tool's own "-p" flag --
        # so they're rated lower until a human confirms them.
        severity = "HIGH" if f["source"] == "environ" else "MEDIUM"
        location = f"pid {f['pid']} [{f['source']}]"
        detail = f"{f['type']}: {f['match']} (process: {f['process']})"
        findings.append(Finding("PROCESS", severity, location, detail, f["remediation"]))

    # Group HIGH severity first, then by category, so the report reads
    # worst-first instead of "whichever hunter happened to run first".
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    findings.sort(key=lambda x: (severity_order.get(x.severity, 9), x.category, x.location))
    return findings


def render_rich(findings: list[Finding], console: Console | None = None) -> None:
    """Render findings as a colored, grouped report for a human reading
    a terminal. Unlike render_json (plain, for scripts to parse), this
    prints directly instead of returning a string -- rich needs a live
    Console to know things like the terminal's width and whether color
    is even supported (it auto-detects and turns color off automatically
    when output is piped to a file, so `credenum > report.txt` stays
    readable plain text without any extra code from us).
    """
    console = console or Console()

    if not findings:
        console.print("[bold green]No findings.[/bold green]")
        return

    counts = Counter(f.severity for f in findings)
    summary_parts = []
    for severity, style in SEVERITY_STYLES.items():
        if counts.get(severity):
            summary_parts.append(f"[{style}]{severity}: {counts[severity]}[/{style}]")
    summary_parts.append(f"[bold]{len(findings)} total[/bold]")
    console.print(Panel("   ".join(summary_parts), title="Scan Summary", border_style="cyan"))

    grouped: dict[str, list[Finding]] = {}
    for f in findings:
        grouped.setdefault(f.category, []).append(f)

    for category, label in CATEGORY_LABELS.items():
        items = grouped.get(category)
        if not items:
            continue

        console.print(f"\n[bold underline]{label}[/bold underline]")

        table = Table(box=box.SIMPLE_HEAVY, header_style="bold", expand=True)
        table.add_column("Severity", width=8, no_wrap=True)
        # Paths/PIDs read badly when wrapped mid-word across lines, so we
        # truncate long ones with an ellipsis instead ("no_wrap" + the
        # "ellipsis" overflow mode) -- worse for seeing the whole path,
        # much better for scanning a report quickly. Detail/Fix text wrap
        # normally since they're prose, not a single unbreakable token.
        table.add_column("Location", ratio=3, no_wrap=True, overflow="ellipsis")
        table.add_column("Detail", ratio=3, overflow="fold")
        table.add_column("Fix", ratio=4, overflow="fold", style="dim")

        for f in items:
            style = SEVERITY_STYLES.get(f.severity)
            severity_cell = f"[{style}]{f.severity}[/{style}]" if style else f.severity
            table.add_row(severity_cell, f.location, f.detail, f.remediation)

        console.print(table)


def render_json(findings: list[Finding]) -> str:
    return json.dumps([asdict(f) for f in findings], indent=2)
