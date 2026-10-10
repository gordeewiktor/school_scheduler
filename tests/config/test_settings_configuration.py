"""Integration tests for config/settings.py's environment-driven
configuration (DJANGO_ENV, SECRET_KEY, DEBUG, ALLOWED_HOSTS).

These run `manage.py check` in a subprocess with a deliberately
constructed, minimal environment (never the developer's real shell
environment or .env file) so the pass/fail behavior is fully
deterministic regardless of what's actually configured on this
machine. `manage.py check` validates settings without needing a
reachable database, so DB_* here are just well-formed strings.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

BASE_DB_ENV = {
    "DB_NAME": "irrelevant_for_check",
    "DB_USER": "irrelevant_for_check",
    "DB_PASSWORD": "irrelevant_for_check",
}


def run_check(extra_env: dict[str, str]) -> subprocess.CompletedProcess:
    env = {"PATH": __import__("os").environ["PATH"], **BASE_DB_ENV, **extra_env}
    return subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def read_setting(name: str, extra_env: dict[str, str]) -> str:
    """Run a tiny script in the same isolated-environment style as
    run_check(), printing one settings.* value so a success path can
    assert the actual parsed value, not just a zero exit code."""
    env = {"PATH": __import__("os").environ["PATH"], **BASE_DB_ENV, **extra_env}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import django, os\n"
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            f"print(getattr(settings, {name!r}))\n",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


class TestDevelopmentConfiguration:
    def test_minimal_environment_is_usable(self):
        # No DJANGO_ENV, no SECRET_KEY, no ALLOWED_HOSTS at all — must
        # still work, with safe development defaults.
        result = run_check({})
        assert result.returncode == 0, result.stderr

    def test_explicit_development_is_usable(self):
        result = run_check({"DJANGO_ENV": "development"})
        assert result.returncode == 0, result.stderr

    def test_debug_true_remains_supported_in_development(self):
        result = run_check({"DJANGO_ENV": "development", "DEBUG": "true"})
        assert result.returncode == 0, result.stderr


class TestProductionConfiguration:
    def test_fails_clearly_when_secret_key_is_missing(self):
        result = run_check({"DJANGO_ENV": "production", "ALLOWED_HOSTS": "example.com"})
        assert result.returncode != 0
        assert "SECRET_KEY" in result.stderr
        assert "ImproperlyConfigured" in result.stderr

    def test_fails_clearly_when_allowed_hosts_is_missing(self):
        result = run_check({"DJANGO_ENV": "production", "SECRET_KEY": "a" * 50})
        assert result.returncode != 0
        assert "ALLOWED_HOSTS" in result.stderr
        assert "ImproperlyConfigured" in result.stderr

    def test_fails_clearly_on_an_unrecognized_debug_value(self):
        result = run_check(
            {
                "DJANGO_ENV": "production",
                "SECRET_KEY": "a" * 50,
                "ALLOWED_HOSTS": "example.com",
                "DEBUG": "maybe",
            }
        )
        assert result.returncode != 0
        assert "DEBUG" in result.stderr

    def test_succeeds_with_all_required_settings_present(self):
        result = run_check(
            {
                "DJANGO_ENV": "production",
                "SECRET_KEY": "a" * 50,
                "ALLOWED_HOSTS": "example.com,www.example.com",
            }
        )
        assert result.returncode == 0, result.stderr

    def test_rejects_an_unrecognized_django_env_value(self):
        result = run_check({"DJANGO_ENV": "staging"})
        assert result.returncode != 0
        assert "DJANGO_ENV" in result.stderr


BASE_PRODUCTION_ENV = {
    "DJANGO_ENV": "production",
    "SECRET_KEY": "a" * 50,
    "ALLOWED_HOSTS": "example.com",
}


class TestProductionRejectsDebugTrue:
    def test_debug_false_works_with_other_settings_valid(self):
        result = run_check({**BASE_PRODUCTION_ENV, "DEBUG": "false"})
        assert result.returncode == 0, result.stderr

    def test_debug_true_fails_clearly_even_if_explicitly_set(self):
        result = run_check({**BASE_PRODUCTION_ENV, "DEBUG": "true"})
        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr
        assert "DEBUG" in result.stderr
        assert "production" in result.stderr

    def test_debug_defaults_to_false_and_works_when_unset(self):
        # DJANGO_ENV=production with no DEBUG at all must still work —
        # the default (not IS_PRODUCTION) already makes this False.
        result = run_check(BASE_PRODUCTION_ENV)
        assert result.returncode == 0, result.stderr


class TestSecureHstsSeconds:
    def test_default_is_3600_in_production(self):
        assert read_setting("SECURE_HSTS_SECONDS", BASE_PRODUCTION_ENV) == "3600"

    def test_default_is_0_in_development(self):
        assert read_setting("SECURE_HSTS_SECONDS", {}) == "0"

    def test_a_valid_override_is_honored(self):
        result = read_setting(
            "SECURE_HSTS_SECONDS", {**BASE_PRODUCTION_ENV, "SECURE_HSTS_SECONDS": "86400"}
        )
        assert result == "86400"

    def test_zero_is_accepted_as_an_explicit_override(self):
        result = read_setting(
            "SECURE_HSTS_SECONDS", {**BASE_PRODUCTION_ENV, "SECURE_HSTS_SECONDS": "0"}
        )
        assert result == "0"

    def test_an_invalid_string_fails_clearly_instead_of_a_raw_valueerror(self):
        result = run_check({**BASE_PRODUCTION_ENV, "SECURE_HSTS_SECONDS": "not-a-number"})
        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr
        assert "SECURE_HSTS_SECONDS" in result.stderr
        assert "ValueError" not in result.stderr

    def test_a_negative_value_is_rejected(self):
        result = run_check({**BASE_PRODUCTION_ENV, "SECURE_HSTS_SECONDS": "-1"})
        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr
        assert "SECURE_HSTS_SECONDS" in result.stderr

    def test_hsts_subdomains_and_preload_stay_disabled_by_default(self):
        assert read_setting("SECURE_HSTS_INCLUDE_SUBDOMAINS", BASE_PRODUCTION_ENV) == "False"
        assert read_setting("SECURE_HSTS_PRELOAD", BASE_PRODUCTION_ENV) == "False"


@pytest.mark.django_db
def test_test_suite_itself_runs_against_postgresql():
    # The real, project-wide settings module (not a subprocess) — this
    # confirms the test run this very test is part of is using
    # PostgreSQL, not SQLite or any other accidental fallback.
    from django.db import connection

    assert connection.vendor == "postgresql"
