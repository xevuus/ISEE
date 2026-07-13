from pathlib import Path

from credenum.utils import permission_flags

# Relative path -> (why it's worth flagging, how to fix it). This is a
# checklist of files that, by convention, tools store plaintext or
# lightly-encoded credentials in. Existence alone is worth reporting; we
# don't need to parse content to know these are worth a human's attention.
KNOWN_CRED_FILES = {
    ".bash_history": (
        "shell history - may contain passwords typed on the command line",
        "Avoid typing secrets directly on the command line -- prefer prompts, config "
        "files, or env vars. Consider HISTCONTROL=ignorespace and a leading space "
        "before sensitive commands.",
    ),
    ".zsh_history": (
        "shell history - may contain passwords typed on the command line",
        "Same fix as .bash_history: avoid typing secrets on the command line; use "
        "HIST_IGNORE_SPACE and a leading space before sensitive commands.",
    ),
    ".mysql_history": (
        "MySQL client history - may contain connection passwords",
        "Use `mysql --defaults-extra-file=<file>` or the [client] password= section "
        "of ~/.my.cnf (chmod 600) instead of passing -p<password> on the command line.",
    ),
    ".psql_history": (
        "Postgres client history",
        "Use a chmod 600 ~/.pgpass file or the PGPASSWORD env var for a session "
        "instead of typing passwords at the psql prompt.",
    ),
    ".netrc": (
        "plaintext credentials for automatic FTP/HTTP login",
        "chmod 600 this file. Prefer a credential helper over a long-lived plaintext "
        "password wherever the tool supports one.",
    ),
    ".git-credentials": (
        "plaintext git remote credentials (credential.helper=store)",
        "chmod 600 this file, or switch to `git credential-manager` / an OS "
        "keychain-backed credential helper instead of credential.helper=store.",
    ),
    ".npmrc": (
        "may contain an npm auth token",
        "If the token is real, revoke it with `npm token revoke`, then inject a "
        "fresh one via the NPM_TOKEN env var at publish time instead of storing it here.",
    ),
    ".pypirc": (
        "PyPI upload credentials",
        "chmod 600 this file. Prefer a project-scoped API token over an "
        "account-wide password, or use trusted publishing (OIDC) instead.",
    ),
    ".pgpass": (
        "Postgres password file",
        "chmod 600 this file -- Postgres will refuse to use it otherwise.",
    ),
    ".docker/config.json": (
        "Docker registry auth (base64-encoded, not encrypted)",
        "Use a docker-credential-* helper (e.g. credential-desktop, "
        "credential-ecr-login) instead of storing base64 auth directly in this file.",
    ),
    ".aws/credentials": (
        "AWS access key + secret key, plaintext",
        "chmod 600 this file. Prefer short-lived credentials via AWS SSO / IAM roles "
        "over long-lived access keys, and rotate any keys found here.",
    ),
    ".kube/config": (
        "Kubernetes cluster credentials/tokens",
        "chmod 600 this file. Prefer short-lived exec-based auth (e.g. "
        "`aws eks get-token`, OIDC) over long-lived embedded tokens.",
    ),
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
        for rel_path, (reason, remediation) in KNOWN_CRED_FILES.items():
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
                "remediation": remediation,
                "size_bytes": size,
                "permission_flags": permission_flags(path),
            })

    return findings
