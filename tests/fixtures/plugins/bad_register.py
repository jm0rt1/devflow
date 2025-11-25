"""Sample bad plugin that raises an error during registration.

This plugin is used to test failure isolation in the plugin system.
It should fail to register, but not crash the CLI or affect other plugins.
"""

from __future__ import annotations

from typing import Any


def register(registry: Any, app: Any) -> None:
    """Attempt to register but fail.

    This intentionally raises an exception to test failure isolation.
    """
    raise RuntimeError("This plugin intentionally fails to register!")
