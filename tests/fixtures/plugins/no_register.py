"""Invalid plugin without a register function.

This is used to test error handling for improperly structured plugins.
"""


def some_other_function():
    """This plugin doesn't have a register function."""
    pass
