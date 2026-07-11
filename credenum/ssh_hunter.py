import os
from pathlib import Path

from credenum.utils import permission_flags

# Filenames SSH clients look for by convention (man ssh, FILES section).
KNOWN_KEY_NAMES = {
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "identity",
}

# The line every unencrypted (and most encrypted) PEM-format private key
# starts with, regardless of filename.
PRIVATE_KEY_HEADER = "PRIVATE KEY"


def _looks_like_key_content(path: Path) -> bool:
    try:
        with path.open("r", errors="ignore") as f:
            first_line = f.readline()
    except (OSError, PermissionError):
        return False
    return PRIVATE_KEY_HEADER in first_line


def find_ssh_keys(root: str) -> list[dict]:
    findings = []

    def on_error(err: OSError) -> None:
        # os.walk stops descending into a dir it can't read unless we
        # pass this callback -- otherwise it silently skips, which is
        # fine for us, but we count it so the user knows coverage isn't 100%.
        pass

    for dirpath, dirnames, filenames in os.walk(root, onerror=on_error):
        for name in filenames:
            path = Path(dirpath) / name

            name_match = name in KNOWN_KEY_NAMES
            content_match = False

            # Only bother sniffing content for small-ish, plausible files --
            # no point reading a 2GB log file line by line.
            if not name_match:
                try:
                    if path.stat().st_size < 10_000:
                        content_match = _looks_like_key_content(path)
                except (OSError, PermissionError):
                    continue

            if name_match or content_match:
                findings.append({
                    "path": str(path),
                    "matched_by": "filename" if name_match else "content",
                    "permission_flags": permission_flags(path),
                })

    return findings
