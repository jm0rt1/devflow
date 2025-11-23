"""devflow - A Python-native project operations CLI."""
import contextlib

__version__ = "0.1.0"

with contextlib.suppress(ImportError):
    from devflow._version import __version__ as __version__  # noqa: F401
