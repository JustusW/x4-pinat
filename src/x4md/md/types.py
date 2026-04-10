"""Typed base classes for Mission Director nodes."""

from __future__ import annotations

from x4md.core import XmlElement


class MDNode(XmlElement):
    """Base class for Mission Director nodes."""


class CueChildNode(MDNode):
    """Base class for nodes that may appear directly under a cue."""


class ConditionNode(MDNode):
    """Base class for condition and event nodes."""


class ActionNode(CueChildNode):
    """Base class for action and flow nodes."""


class ParamNode(MDNode):
    """Base class for param-like nodes."""
