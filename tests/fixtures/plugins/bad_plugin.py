"""Bad plugin for testing error handling.

This plugin intentionally has issues to test graceful failure.
"""


def register(registry, app):
    """This register function will raise an error."""
    raise RuntimeError("This is a deliberately broken plugin!")
