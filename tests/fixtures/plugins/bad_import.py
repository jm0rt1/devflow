"""Sample plugin with import error.

This plugin cannot be imported due to a syntax error.
It tests that the plugin loader handles import failures gracefully.
"""

# This will raise a NameError on import
undefined_variable_reference  # noqa: F821
