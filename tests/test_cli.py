import sys

import pytest

from credenum.cli import main


def test_exits_zero_when_no_findings(tmp_path, monkeypatch):
    # monkeypatch temporarily replaces sys.argv for this test only,
    # then restores the original automatically when the test ends --
    # same idea as tmp_path, but for patching instead of files.
    #
    # --skip-process matters here: process scanning reads the REAL /proc
    # on whatever machine runs this test, so without skipping it, this
    # "no findings" assertion would depend on what happens to be running
    # (e.g. a browser process with flags that match our -p heuristic) --
    # not on anything this test actually controls.
    monkeypatch.setattr(
        sys, "argv", ["credenum", "--root", str(tmp_path), "--skip-process"]
    )

    # main() calls sys.exit(), which doesn't return a value like a normal
    # function -- it raises SystemExit. pytest.raises catches it so we
    # can inspect the exit code instead of the test itself crashing.
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_exits_one_when_findings_present(tmp_path, monkeypatch):
    (tmp_path / ".bash_history").write_text("mysql -uroot -pSuperSecret123\n")
    monkeypatch.setattr(sys, "argv", ["credenum", "--root", str(tmp_path)])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
