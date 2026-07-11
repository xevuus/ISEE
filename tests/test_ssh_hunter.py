import os

from credenum.ssh_hunter import find_ssh_keys


def test_finds_key_by_known_filename(tmp_path):
    (tmp_path / "id_rsa").write_text("not actually a real key\n")

    findings = find_ssh_keys(str(tmp_path))

    assert len(findings) == 1
    assert findings[0]["matched_by"] == "filename"


def test_finds_renamed_key_by_content(tmp_path):
    key_file = tmp_path / "backup.txt"
    key_file.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nfakefakefakekeydata\n")

    findings = find_ssh_keys(str(tmp_path))

    assert len(findings) == 1
    assert findings[0]["matched_by"] == "content"


def test_flags_world_readable_key(tmp_path):
    key_file = tmp_path / "id_ed25519"
    key_file.write_text("fake key\n")
    os.chmod(key_file, 0o644)  # owner rw, but group+other can read too

    findings = find_ssh_keys(str(tmp_path))

    assert len(findings[0]["permission_flags"]) == 1


def test_does_not_flag_correctly_permissioned_key(tmp_path):
    key_file = tmp_path / "id_ed25519"
    key_file.write_text("fake key\n")
    os.chmod(key_file, 0o600)  # owner-only, the correct mode for a key

    findings = find_ssh_keys(str(tmp_path))

    assert findings[0]["permission_flags"] == []


def test_ordinary_file_is_not_flagged(tmp_path):
    (tmp_path / "notes.txt").write_text("just some notes, nothing sensitive\n")

    findings = find_ssh_keys(str(tmp_path))

    assert findings == []
