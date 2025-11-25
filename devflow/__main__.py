"""
Allow running devflow as a module: python -m devflow

This enables the CLI to be invoked via `python -m devflow` in addition
to the console_scripts entry point `devflow`.
"""

import sys

from devflow.cli import main

if __name__ == "__main__":
    sys.exit(main())
