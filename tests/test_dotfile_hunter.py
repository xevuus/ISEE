from credenum.dotfile_hunter import find_dotfiles


def test_finds_known_credential_file_in_home_dir(tmp_path):
    home = tmp_path / "alice"
    home.mkdir()
    (home / ".bash_history").write_text("mysql -uroot -pSuperSecret123\n")

    findings = find_dotfiles(str(tmp_path))

    assert len(findings) == 1
    assert findings[0]["path"].endswith(".bash_history")


def test_finds_nested_known_path(tmp_path):
    home = tmp_path / "alice"
    (home / ".aws").mkdir(parents=True)
    (home / ".aws" / "credentials").write_text("[default]\naws_access_key_id=AKIA...\n")

    findings = find_dotfiles(str(tmp_path))

    assert len(findings) == 1
    assert ".aws/credentials" in findings[0]["path"]


def test_home_dir_with_no_known_files_yields_nothing(tmp_path):
    home = tmp_path / "alice"
    home.mkdir()
    (home / "notes.txt").write_text("shopping list\n")

    findings = find_dotfiles(str(tmp_path))

    assert findings == []


def test_root_itself_treated_as_a_home_dir(tmp_path):
    # --root can point directly at a home dir (e.g. `--root ~`), not just
    # a parent directory containing many home dirs (e.g. `--root /home`).
    (tmp_path / ".netrc").write_text("machine example.com login bob password hunter2\n")

    findings = find_dotfiles(str(tmp_path))

    assert len(findings) == 1
