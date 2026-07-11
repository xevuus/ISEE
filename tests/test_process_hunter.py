from credenum.process_hunter import _is_suspicious_env_key


def test_flags_credential_shaped_env_keys():
    assert _is_suspicious_env_key("AWS_SECRET_ACCESS_KEY")
    assert _is_suspicious_env_key("DATABASE_PASSWORD")
    assert _is_suspicious_env_key("GITHUB_TOKEN")


def test_does_not_flag_known_benign_keys():
    # the exact false positive we hit scanning a real desktop session
    assert not _is_suspicious_env_key("XDG_ACTIVATION_TOKEN")
    assert not _is_suspicious_env_key("GNOME_KEYRING_CONTROL")


def test_does_not_flag_unrelated_env_keys():
    assert not _is_suspicious_env_key("PATH")
    assert not _is_suspicious_env_key("LANG")
    assert not _is_suspicious_env_key("HOME")
