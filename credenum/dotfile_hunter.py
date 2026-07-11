from pathlib import Path

from credenum.utils import permission_flags

# Relative path -> why it's worth flagging. This is a checklist of files
# that, by convention, tools store plaintext or lightly-encoded credentials
# in. Existence alone is worth reporting; we don't need to parse content
# to know these are worth a human's attention.
KNOWN_CRED_FILES = {
    ".bash_history": "shell history - may contain passwords typed on the command line",
    ".zsh_history": "shell history - may contain passwords typed on the command line",
    ".mysql_history": "MySQL client history - may contain connection passwords",
    ".psql_history": "Postgres client history",
    ".netrc": "plaintext credentials for automatic FTP/HTTP login",
    ".git-credentials": "plaintext git remote credentials (credential.helper=store)",
    ".npmrc": "may contain an npm auth token",
    ".pypirc": "PyPI upload credentials",
    ".pgpass": "Postgres password file",
    ".docker/config.json": "Docker registry auth (base64-encoded, not encrypted)",
    ".aws/credentials": "AWS access key + secret key, plaintext",
    ".kube/config": "Kubernetes cluster credentials/tokens",
}


def _candidate_home_dirs(root: str) -> list[Path]:
    root_path = Path(root)
    homes = []

    if root_path.is_dir():
        # If root itself looks like a home dir (has a known file directly
        # in it), include it -- lets `--root ~` work, not just `--root /home`.
        homes.append(root_path)
        try:
            homes.extend(p for p in root_path.iterdir() if p.is_dir())
        except (OSError, PermissionError):
            pass

    return homes


def find_dotfiles(root: str) -> list[dict]:
    findings = []
    seen = set()

    for home in _candidate_home_dirs(root):
        for rel_path, reason in KNOWN_CRED_FILES.items():
            path = home / rel_path
            if path in seen:
                continue
            seen.add(path)

            try:
                if not path.is_file():
                    continue
                size = path.stat().st_size
            except (OSError, PermissionError):
                continue

            findings.append({
                "path": str(path),
                "reason": reason,
                "size_bytes": size,
                "permission_flags": permission_flags(path),
            })

    return findings
