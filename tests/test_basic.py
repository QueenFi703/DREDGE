"""Basic tests for the dredge package."""

import dredge


def test_version():
    """Test that the version is correctly set."""
    assert dredge.__version__ == "0.1.0"


def test_import():
    """Test that the package can be imported."""
    assert dredge is not None
