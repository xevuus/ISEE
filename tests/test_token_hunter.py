from credenum.token_hunter import _looks_like_placeholder, find_tokens


# Testing the pure helper directly, with no filesystem involved at all --
# this is the fastest, most precise kind of test: given this exact input,
# assert this exact output. It's also exactly what would have caught the
# real "your-api-key-here" vs "your_api_key_here" bug before it shipped.
def test_placeholder_detection_handles_dashes_and_underscores():
    assert _looks_like_placeholder("your-api-key-here")
    assert _looks_like_placeholder("your_api_key_here")
    assert _looks_like_placeholder("CHANGEME")
    assert not _looks_like_placeholder("Kp9x2Rmq7Vt4Ln8W")


# `tmp_path` is a pytest built-in fixture: pytest sees this parameter
# name, creates a fresh temp directory, and passes it in as a Path.
# pytest deletes it automatically afterward -- no cleanup code needed.
def test_find_tokens_ignores_placeholder_secrets(tmp_path):
    config = tmp_path / "config.env"
    config.write_text('API_KEY="your-api-key-here"\n')

    findings = find_tokens(str(tmp_path))

    assert findings == []


def test_find_tokens_flags_real_looking_aws_key(tmp_path):
    config = tmp_path / "config.env"
    config.write_text("AWS_ACCESS_KEY_ID=AKIAABCDEFGHIJKLMNOP\n")

    findings = find_tokens(str(tmp_path))

    assert len(findings) == 1
    assert findings[0]["type"] == "AWS Access Key ID"
    # the real key must never appear in full in the output
    assert "AKIAABCDEFGHIJKLMNOP" not in findings[0]["match"]


def test_find_tokens_skips_binary_files(tmp_path):
    binary_file = tmp_path / "data.bin"
    binary_file.write_bytes(b"AKIAABCDEFGHIJKLMNOP\x00\x01\x02garbage")

    findings = find_tokens(str(tmp_path))

    assert findings == []
