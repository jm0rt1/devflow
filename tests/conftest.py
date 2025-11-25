"""Pytest configuration for devflow tests."""

import sys
from pathlib import Path

# Add the package to the path for testing
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))
