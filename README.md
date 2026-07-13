# ISEE (`credenum`)

A Linux credential enumeration CLI. Hunts down SSH keys, known credential files, secrets embedded in file contents, and secrets exposed via running processes — the kind of local credential-hunting a post-exploitation recon tool (LinPEAS, LaZagne) does, in a small, readable Python codebase.

> **Use responsibly.** Run this only against systems and accounts you own or are explicitly authorized to test (your own machine, an authorized pentest engagement, a CTF box). Findings can include real, sensitive credentials — handle the output accordingly.

## What it finds

| Category | Examples | How |
|---|---|---|
| SSH keys | `id_rsa`, `id_ed25519`, renamed private keys | Filename match, or content sniffing for a `PRIVATE KEY` PEM header. Flags world/group-readable permissions. |
| Credential files | `.netrc`, `.git-credentials`, `.aws/credentials`, `.docker/config.json`, `.kube/config`, shell history, etc. | Checklist of known sensitive paths relative to each home directory. |
| Tokens / API keys | AWS keys, GitHub/Slack/Google tokens, JWTs, generic assigned secrets | Regex over file contents, with binary/noisy-directory skipping and placeholder filtering (`your-api-key-here` doesn't get flagged). |
| Process / environment secrets | Passwords passed as CLI flags, credential-shaped environment variables | Reads `/proc/<pid>/cmdline` and `/proc/<pid>/environ` directly. |

Every finding is redacted before being printed or written to JSON — you get enough to identify it, never the full value.

## Install

Requires Python 3.9+.

```bash
git clone https://github.com/xevuus/ISEE.git
cd ISEE
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
credenum --root ~                  # scan your home directory
credenum --root /home              # scan every home directory under /home (default)
credenum --format json             # plain JSON output, for scripts/CI
credenum --skip-process            # skip live /proc scanning (faster, deterministic)
credenum --help                    # see all flags
```

Exit code is `0` if nothing was found, `1` if there were findings — so `credenum` can gate a script or CI pipeline:

```bash
if ! credenum --root ~ --skip-process; then
    echo "credentials found on disk"
fi
```

## Development

```bash
pip install -e ".[dev]"   # adds pytest
python -m pytest          # run the test suite
```

## Project layout

```
credenum/
  ssh_hunter.py       # SSH private key detection
  dotfile_hunter.py   # known credential-file checklist
  token_hunter.py     # regex-based secret scanning in file contents
  process_hunter.py   # /proc-based process & environment scanning
  report.py           # normalizes hunter output into a unified, colored report
  cli.py              # entry point: argument parsing, banner, dispatch
tests/                # pytest suite, one file per hunter plus the CLI
```
