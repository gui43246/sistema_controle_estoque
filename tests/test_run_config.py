"""Tests for development and production server mode decisions."""

import pytest

from run import resolve_debug_mode


@pytest.mark.parametrize("value", [None, "", "0", "false", "off"])
def test_debug_is_disabled_by_default_or_false_values(value):
    assert resolve_debug_mode("development", value) is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on"])
def test_debug_accepts_explicit_true_values_in_development(value):
    assert resolve_debug_mode("development", value) is True


def test_debug_is_rejected_in_production():
    with pytest.raises(RuntimeError, match="FLASK_DEBUG"):
        resolve_debug_mode("production", "1")


def test_debug_remains_disabled_in_production():
    assert resolve_debug_mode("production", "0") is False
