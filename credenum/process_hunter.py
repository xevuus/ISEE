import re
from pathlib import Path

# Command-line flags that classically carry a plaintext credential.
# `-p` glued directly to a value (no space) is the infamous mysql/psql
# client pattern: `mysql -uroot -pSuperSecret123`. We deliberately require
# no space and no following '-', so a normal "-p 8080"-style port flag
# doesn't match -- though this is still a heuristic, not a guarantee.
CMDLINE_PATTERNS = {
    "CLI password flag": re.compile(r"(?i)--?(?:password|pass|pwd)[= ]\S+"),
    "mysql-style glued -p": re.compile(r"(?<!\S)-p(?!\s|$|-)\S+"),
}

# Environment variable *names* that conventionally hold secrets. We match
# the key, not the value -- env vars are already "key=value" by nature,
# so unlike file scanning we don't need content-shape regexes at all.
ENV_KEY_MARKERS = re.compile(r"(?i)(pass|secret|token|key|credential)")

# Real, well-known env vars that happen to contain a marker substring
# (TOKEN, KEY, ...) but hold session/session-plumbing data, not
# credentials. Found by running the scanner and reading what came back --
# this list only grows by observing real false positives, there's no way
# to predict every desktop environment's naming conventions up front.
KNOWN_BENIGN_ENV_KEYS = {
    "XDG_ACTIVATION_TOKEN",  # Wayland/X11 window-focus handoff token
    "GNOME_KEYRING_CONTROL",  # path to the keyring daemon's socket, not a secret itself
}


def _read_proc_entries(pid_dir: Path, name: str) -> list[str]:
    """cmdline and environ are both NUL-separated blobs of bytes --
    same parsing logic works for either file."""
    try:
        raw = (pid_dir / name).read_bytes()
    except (OSError, PermissionError):
        # PermissionError is expected and common here: Linux only lets
        # you read another process's environ if you own it (or are
        # root). That's the kernel enforcing a real security boundary,
        # not a bug in our scan.
        return []
    return [p.decode(errors="ignore") for p in raw.split(b"\x00") if p]


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _is_suspicious_env_key(key: str) -> bool:
    """Pure decision logic, deliberately separated from the /proc-reading
    loop below. It takes a plain string and returns a bool -- no
    filesystem access, no live process state -- which means a test can
    call it directly with made-up keys instead of needing a real,
    running process with that exact environment variable set."""
    if key in KNOWN_BENIGN_ENV_KEYS:
        return False
    return bool(ENV_KEY_MARKERS.search(key))


def find_process_secrets() -> list[dict]:
    findings = []

    try:
        pid_dirs = [p for p in Path("/proc").iterdir() if p.name.isdigit()]
    except (OSError, PermissionError):
        return findings

    for pid_dir in pid_dirs:
        pid = pid_dir.name
        args = _read_proc_entries(pid_dir, "cmdline")
        if not args:
            # Either the process exited between listing and reading
            # (processes come and go constantly), or it's a kernel
            # thread with no cmdline at all -- both are fine to skip.
            continue
        process_name = args[0]
        cmdline = " ".join(args)

        for label, pattern in CMDLINE_PATTERNS.items():
            match = pattern.search(cmdline)
            if match:
                findings.append({
                    "pid": pid,
                    "source": "cmdline",
                    "type": label,
                    "match": _redact(match.group(0)),
                    "process": process_name,
                })

        for entry in _read_proc_entries(pid_dir, "environ"):
            key, sep, value = entry.partition("=")
            if sep and value and _is_suspicious_env_key(key):
                findings.append({
                    "pid": pid,
                    "source": "environ",
                    "type": key,
                    "match": _redact(value),
                    "process": process_name,
                })

    return findings
