"""Pure environment-variable parsing helpers for config/settings.py.

Deliberately has no Django import and no side effects (no .env
loading, no settings access) so it can be unit-tested directly,
independently of Django's settings machinery.
"""

import os


class EnvironmentConfigurationError(Exception):
    """Raised when a required environment variable is missing or a
    present one can't be parsed as the type settings.py expects."""


def required(name: str, *, hint: str = "") -> str:
    """Return the named environment variable, or raise with a clear,
    actionable message if it's unset, empty, or whitespace-only."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        message = f"Required environment variable {name!r} is not set."
        if hint:
            message = f"{message} {hint}"
        raise EnvironmentConfigurationError(message)
    return value


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def parse_bool(name: str, default: bool) -> bool:
    """Parse a boolean-like environment variable safely.

    Unlike bool(os.environ.get(name)), this treats "false"/"0"/"no"/
    "off" (case-insensitively) as False — a non-empty string is not
    automatically truthy here. Raises on anything else unrecognized,
    rather than silently guessing.
    """
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise EnvironmentConfigurationError(
        f"Environment variable {name!r} must be a boolean-like value "
        f"(one of {sorted(_TRUE_VALUES | _FALSE_VALUES)}) — got {raw!r}."
    )


def parse_list(name: str, default: str = "") -> list[str]:
    """Parse a comma-separated environment variable into a list of
    trimmed, non-empty strings. Blank entries (from trailing commas,
    extra whitespace, or an unset/empty variable) are dropped."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_int(name: str, default: int, *, minimum: int | None = None) -> int:
    """Parse an integer-valued environment variable safely.

    Raises EnvironmentConfigurationError (rather than letting a raw
    ValueError escape) for a non-integer value, or one below
    `minimum` when given.
    """
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    stripped = raw.strip()
    try:
        value = int(stripped)
    except ValueError:
        raise EnvironmentConfigurationError(
            f"Environment variable {name!r} must be a whole number — got {raw!r}."
        ) from None
    if minimum is not None and value < minimum:
        raise EnvironmentConfigurationError(
            f"Environment variable {name!r} must be >= {minimum} — got {value}."
        )
    return value
