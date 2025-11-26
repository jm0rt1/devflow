"""Default configuration values for devflow.

These defaults are used when no configuration file is found or when
configuration values are not specified.
"""

from devflow.config.schema import DevflowConfig

# The default configuration instance
DEFAULT_CONFIG = DevflowConfig()
