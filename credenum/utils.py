import stat
from pathlib import Path


def permission_flags(path: Path) -> list[str]:
    """Flag files readable by users other than their owner."""
    flags = []
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except (OSError, PermissionError):
        return flags
    if mode & 0o077:
        flags.append(f"world/group-readable (mode {oct(mode)})")
    return flags
