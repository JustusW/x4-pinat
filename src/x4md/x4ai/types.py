"""Typed base classes for AI-script nodes."""

from __future__ import annotations

from x4md.core import XmlElement


class AINode(XmlElement):
    """Base class for AI-script nodes."""


class OrderChildNode(AINode):
    """Base class for nodes that may appear inside an order."""


class InterruptNode(AINode):
    """Base class for interrupt-related nodes."""
