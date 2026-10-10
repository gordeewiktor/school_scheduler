import pytest

from config.env import (
    EnvironmentConfigurationError,
    parse_bool,
    parse_int,
    parse_list,
    required,
)


class TestRequired:
    def test_returns_the_value_when_set(self, monkeypatch):
        monkeypatch.setenv("SOME_VAR", "a-value")
        assert required("SOME_VAR") == "a-value"

    def test_raises_when_unset(self, monkeypatch):
        monkeypatch.delenv("SOME_VAR", raising=False)
        with pytest.raises(EnvironmentConfigurationError, match="SOME_VAR"):
            required("SOME_VAR")

    def test_raises_when_blank(self, monkeypatch):
        monkeypatch.setenv("SOME_VAR", "")
        with pytest.raises(EnvironmentConfigurationError):
            required("SOME_VAR")

    def test_raises_when_whitespace_only(self, monkeypatch):
        monkeypatch.setenv("SOME_VAR", "   ")
        with pytest.raises(EnvironmentConfigurationError, match="SOME_VAR"):
            required("SOME_VAR")

    def test_includes_the_hint_in_the_error(self, monkeypatch):
        monkeypatch.delenv("SOME_VAR", raising=False)
        with pytest.raises(EnvironmentConfigurationError, match="see the docs"):
            required("SOME_VAR", hint="see the docs")


class TestParseBool:
    @pytest.mark.parametrize("raw", ["true", "True", "TRUE", "1", "yes", "YES", "on"])
    def test_recognizes_true_values(self, monkeypatch, raw):
        monkeypatch.setenv("FLAG", raw)
        assert parse_bool("FLAG", default=False) is True

    @pytest.mark.parametrize("raw", ["false", "False", "FALSE", "0", "no", "NO", "off"])
    def test_recognizes_false_values(self, monkeypatch, raw):
        monkeypatch.setenv("FLAG", raw)
        assert parse_bool("FLAG", default=True) is False

    def test_the_string_false_is_not_truthy(self, monkeypatch):
        # The exact bug this function exists to avoid:
        # bool(os.environ.get("FLAG")) would be True for "False".
        monkeypatch.setenv("FLAG", "False")
        assert parse_bool("FLAG", default=True) is False

    def test_uses_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("FLAG", raising=False)
        assert parse_bool("FLAG", default=True) is True
        assert parse_bool("FLAG", default=False) is False

    def test_uses_default_when_blank(self, monkeypatch):
        monkeypatch.setenv("FLAG", "   ")
        assert parse_bool("FLAG", default=True) is True

    def test_trims_whitespace(self, monkeypatch):
        monkeypatch.setenv("FLAG", "  true  ")
        assert parse_bool("FLAG", default=False) is True

    def test_raises_on_an_unrecognized_value(self, monkeypatch):
        monkeypatch.setenv("FLAG", "maybe")
        with pytest.raises(EnvironmentConfigurationError, match="FLAG"):
            parse_bool("FLAG", default=False)


class TestParseList:
    def test_splits_on_commas_and_trims_whitespace(self, monkeypatch):
        monkeypatch.setenv("HOSTS", "example.com, www.example.com ,api.example.com")
        assert parse_list("HOSTS") == ["example.com", "www.example.com", "api.example.com"]

    def test_drops_empty_entries_from_trailing_commas(self, monkeypatch):
        monkeypatch.setenv("HOSTS", "example.com,, ,")
        assert parse_list("HOSTS") == ["example.com"]

    def test_returns_empty_list_when_unset_and_no_default(self, monkeypatch):
        monkeypatch.delenv("HOSTS", raising=False)
        assert parse_list("HOSTS") == []

    def test_uses_the_given_default_string_when_unset(self, monkeypatch):
        monkeypatch.delenv("HOSTS", raising=False)
        assert parse_list("HOSTS", default="localhost,127.0.0.1") == ["localhost", "127.0.0.1"]

    def test_an_explicitly_empty_value_overrides_the_default(self, monkeypatch):
        monkeypatch.setenv("HOSTS", "")
        assert parse_list("HOSTS", default="localhost,127.0.0.1") == []


class TestParseInt:
    def test_uses_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("COUNT", raising=False)
        assert parse_int("COUNT", default=3600) == 3600

    def test_uses_default_when_blank(self, monkeypatch):
        monkeypatch.setenv("COUNT", "   ")
        assert parse_int("COUNT", default=3600) == 3600

    def test_parses_a_valid_override(self, monkeypatch):
        monkeypatch.setenv("COUNT", "86400")
        assert parse_int("COUNT", default=3600) == 86400

    def test_accepts_zero(self, monkeypatch):
        monkeypatch.setenv("COUNT", "0")
        assert parse_int("COUNT", default=3600, minimum=0) == 0

    def test_trims_whitespace(self, monkeypatch):
        monkeypatch.setenv("COUNT", "  120  ")
        assert parse_int("COUNT", default=0) == 120

    def test_raises_a_clean_error_on_an_invalid_string(self, monkeypatch):
        monkeypatch.setenv("COUNT", "not-a-number")
        with pytest.raises(EnvironmentConfigurationError, match="COUNT"):
            parse_int("COUNT", default=0)

    def test_raises_on_a_value_below_the_minimum(self, monkeypatch):
        monkeypatch.setenv("COUNT", "-10")
        with pytest.raises(EnvironmentConfigurationError, match="COUNT"):
            parse_int("COUNT", default=0, minimum=0)

    def test_no_minimum_means_negative_values_are_allowed(self, monkeypatch):
        monkeypatch.setenv("COUNT", "-10")
        assert parse_int("COUNT", default=0) == -10
