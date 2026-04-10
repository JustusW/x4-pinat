"""Shared test configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def pytest_configure(config):
    """Enable type validation for all XmlElement instances during tests."""
    from x4md.core import XmlElement

    # Store original methods
    original_str = XmlElement.__str__
    original_to_xml = XmlElement.to_xml

    # Wrap to_xml to validate before rendering
    def validated_to_xml(self, **kwargs):
        self.validate_types(strict=True)
        return original_to_xml(self, **kwargs)

    def validated_str(self):
        self.validate_types(strict=True)
        return original_str(self)

    # Apply validation wrappers for all tests
    XmlElement.to_xml = validated_to_xml
    XmlElement.__str__ = validated_str
