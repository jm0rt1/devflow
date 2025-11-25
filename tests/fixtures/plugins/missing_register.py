"""Sample plugin missing the register function.

This plugin is used to test that the loader properly handles
modules that don't provide the required register function.
"""

from __future__ import annotations


def some_other_function() -> None:
    """This is not the register function the loader is looking for."""
    pass
