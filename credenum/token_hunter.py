import os
import re
from pathlib import Path

# Directories that are either huge, irrelevant, or full of noise (compiled
# deps, virtualenvs, git internals). Skipping them early keeps the scan
# fast and cuts false positives from library code that isn't "yours".
SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "site-packages"}

MAX_FILE_SIZE = 2_000_000  # 2MB - past this, it's a log/data file, not a config

# Each pattern trades recall for precision differently. Patterns with a
# fixed, branded prefix (AKIA, ghp_, xox...) are near-zero false positive --
# nobody accidentally writes "AKIA" followed by 16 characters. The generic
# "key = value" pattern at the bottom is the opposite: high recall, but
# noisier, because lots of things look like "secret: <some string>".
TOKEN_PATTERNS = {
    "AWS Access Key ID": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub Token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b"),
    "Slack Token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,48}\b"),
    "Google API Key": re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    "Generic assigned secret": re.compile(
        r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]([A-Za-z0-9_\-/+]{12,})['\"]"
    ),
}


# Substrings that show up constantly in documentation/example code where
# a real secret would go, but a real secret never would (nobody's live
# AWS key literally contains the word "example"). Checking for these
# catches the "your_token_here" class of false positive without needing
# anything fancier like entropy analysis.
PLACEHOLDER_MARKERS = (
    "your_", "_here", "example", "xxxx", "changeme", "placeholder",
    "sample", "dummy", "todo", "insert_", "replace_me", "fake", "<", ">",
)

# Provider-specific revoke instructions, keyed by the same label used in
# TOKEN_PATTERNS -- we can't tell whether a match is a real, live secret
# or a harmless test fixture, so the advice always leads with "if real".
TOKEN_REMEDIATION = {
    "AWS Access Key ID": (
        "If real, deactivate/rotate this key immediately in IAM > Security "
        "Credentials, then remove it from this file and use env vars or a "
        "secrets manager instead."
    ),
    "GitHub Token": (
        "If real, revoke it at github.com/settings/tokens, then remove it from "
        "this file -- inject a fresh token via CI secrets instead."
    ),
    "Slack Token": (
        "If real, revoke it in the Slack app's OAuth & Permissions settings, "
        "then remove it from this file."
    ),
    "Google API Key": (
        "If real, delete/regenerate it in Google Cloud Console > APIs & Services "
        "> Credentials, and restrict the replacement key by IP or referrer."
    ),
    "JWT": (
        "If still valid, treat it as compromised -- revoke the underlying "
        "session/refresh token if possible, and avoid storing live JWTs in files."
    ),
    "Generic assigned secret": (
        "If real, rotate it at the source system, then remove it from this "
        "file -- use an environment variable or secrets manager reference instead."
    ),
}


def _looks_like_placeholder(value: str) -> bool:
    # Normalize dashes to underscores so "your-api-key-here" and
    # "your_api_key_here" both match the same marker list -- otherwise
    # we'd need to write every marker twice.
    lowered = value.lower().replace("-", "_")
    return any(marker.replace("-", "_") in lowered for marker in PLACEHOLDER_MARKERS)


def _secret_value(label: str, match: re.Match) -> str:
    # The generic pattern has two capture groups -- (key name) and
    # (the actual value) -- because we need to redact/filter only the
    # value, not the literal word "token" that appears right next to it.
    # The branded patterns (AKIA..., ghp_..., etc) have no groups, so the
    # whole match *is* the value.
    if match.lastindex:
        return match.group(match.lastindex)
    return match.group(0)


def _is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
    except (OSError, PermissionError):
        return True
    return b"\x00" in chunk


def _redact(value: str) -> str:
    # Never print a live secret in full -- even in your own scan output,
    # it can end up in shell history, a log file, or a screen-shared
    # terminal. Show just enough to identify it, not enough to use it.
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def find_tokens(root: str) -> list[dict]:
    findings = []

    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        # Mutating dirnames in place tells os.walk not to descend into
        # these -- filtering the results afterward would still pay the
        # cost of walking into them first.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for name in filenames:
            path = Path(dirpath) / name

            try:
                if path.is_symlink():
                    continue
                size = path.stat().st_size
                if size == 0 or size > MAX_FILE_SIZE:
                    continue
            except (OSError, PermissionError):
                continue

            if _is_probably_binary(path):
                continue

            try:
                with path.open("r", errors="ignore") as fh:
                    for lineno, line in enumerate(fh, start=1):
                        for label, pattern in TOKEN_PATTERNS.items():
                            match = pattern.search(line)
                            if not match:
                                continue
                            value = _secret_value(label, match)
                            if _looks_like_placeholder(value):
                                continue
                            findings.append({
                                "path": str(path),
                                "line": lineno,
                                "type": label,
                                "match": _redact(match.group(0)),
                                "remediation": TOKEN_REMEDIATION[label],
                            })
            except (OSError, PermissionError):
                continue

    return findings
