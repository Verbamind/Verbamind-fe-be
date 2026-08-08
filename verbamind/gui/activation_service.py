"""Activation service — wraps activation checks for GUI startup flow."""

from verbamind.security.activation import is_activated


def check_activation() -> bool:
    return is_activated()
