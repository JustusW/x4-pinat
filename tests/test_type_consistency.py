"""Tests for verifying inheritance chains and type consistency across the codebase.

This test suite uses introspection to validate that all node classes follow
correct inheritance patterns without making hard-coded assumptions about
which nodes should have which base classes.
"""

import inspect
import unittest
from typing import get_args, get_origin

import x4md
from x4md.core import XmlElement
from x4md.md.types import ActionNode, ConditionNode, CueChildNode, MDNode, ParamNode
from x4md.x4ai.types import AINode, InterruptNode, OrderChildNode


class TypeConsistencyTests(unittest.TestCase):
    """Validate type consistency and inheritance across all exported nodes."""

    def test_all_node_classes_inherit_from_xml_element(self) -> None:
        """All node classes should inherit from XmlElement."""
        # Get all exported classes from x4md
        all_exports = [getattr(x4md, name) for name in dir(x4md) if not name.startswith("_")]
        node_classes = [
            obj for obj in all_exports
            if inspect.isclass(obj) and issubclass(obj, XmlElement) and obj != XmlElement
        ]

        # Every node class should have XmlElement in its MRO
        for cls in node_classes:
            with self.subTest(cls=cls.__name__):
                self.assertTrue(
                    issubclass(cls, XmlElement),
                    f"{cls.__name__} should inherit from XmlElement"
                )

    def test_node_base_classes_follow_hierarchy(self) -> None:
        """Node base classes should follow expected inheritance hierarchy.

        Expected hierarchy:
        - MDNode -> CueChildNode -> ActionNode
        - MDNode -> ConditionNode
        - MDNode -> ParamNode
        - AINode -> OrderChildNode
        - AINode -> InterruptNode
        """
        # Verify MD hierarchy
        self.assertTrue(issubclass(ActionNode, CueChildNode))
        self.assertTrue(issubclass(CueChildNode, MDNode))
        self.assertTrue(issubclass(ConditionNode, MDNode))
        self.assertTrue(issubclass(ParamNode, MDNode))

        # Verify AI hierarchy
        self.assertTrue(issubclass(OrderChildNode, AINode))
        self.assertTrue(issubclass(InterruptNode, AINode))

        # Verify separation between MD and AI
        self.assertFalse(issubclass(ActionNode, AINode))
        self.assertFalse(issubclass(ConditionNode, AINode))
        self.assertFalse(issubclass(OrderChildNode, MDNode))

    def test_md_nodes_do_not_use_ai_base_classes(self) -> None:
        """MD package nodes should not inherit from AI-specific base classes."""
        import x4md.md.actions as actions_mod
        import x4md.md.conditions as conditions_mod
        import x4md.md.document as document_mod

        ai_bases = (OrderChildNode, InterruptNode, AINode)

        for module in [actions_mod, conditions_mod, document_mod]:
            module_classes = [
                obj for name, obj in inspect.getmembers(module, inspect.isclass)
                if obj.__module__ == module.__name__ and issubclass(obj, XmlElement)
            ]

            for cls in module_classes:
                with self.subTest(cls=cls.__name__, module=module.__name__):
                    for ai_base in ai_bases:
                        self.assertFalse(
                            issubclass(cls, ai_base) and cls != ai_base,
                            f"MD node {cls.__name__} should not inherit from AI base {ai_base.__name__}"
                        )

    def test_ai_nodes_do_not_use_md_action_condition_bases(self) -> None:
        """AI package nodes should not inherit from MD-specific action/condition bases."""
        import x4md.x4ai.nodes as ai_nodes_mod

        md_bases = (ActionNode, ConditionNode, CueChildNode, ParamNode)

        module_classes = [
            obj for name, obj in inspect.getmembers(ai_nodes_mod, inspect.isclass)
            if obj.__module__ == ai_nodes_mod.__name__ and issubclass(obj, XmlElement)
        ]

        for cls in module_classes:
            with self.subTest(cls=cls.__name__):
                for md_base in md_bases:
                    self.assertFalse(
                        issubclass(cls, md_base) and cls != md_base,
                        f"AI node {cls.__name__} should not inherit from MD base {md_base.__name__}"
                    )

    def test_action_nodes_inherit_from_action_base(self) -> None:
        """Action nodes should inherit from ActionNode (which extends CueChildNode)."""
        import x4md.md.actions as actions_mod

        action_classes = [
            obj for name, obj in inspect.getmembers(actions_mod, inspect.isclass)
            if obj.__module__ == actions_mod.__name__
            and issubclass(obj, XmlElement)
            and obj not in (ActionNode, CueChildNode, MDNode, XmlElement, ParamNode)
        ]

        for cls in action_classes:
            with self.subTest(cls=cls.__name__):
                # Actions should inherit from ActionNode or ParamNode
                self.assertTrue(
                    issubclass(cls, ActionNode) or issubclass(cls, ParamNode),
                    f"{cls.__name__} in actions module should inherit from ActionNode or ParamNode"
                )

    def test_concrete_nodes_can_render(self) -> None:
        """Concrete node classes should be able to render to XML strings."""
        # Base classes that are abstract
        abstract_bases = {XmlElement, MDNode, AINode, ActionNode, ConditionNode,
                         CueChildNode, ParamNode, OrderChildNode, InterruptNode}

        all_exports = [getattr(x4md, name) for name in dir(x4md) if not name.startswith("_")]
        concrete_nodes = [
            obj for obj in all_exports
            if inspect.isclass(obj)
            and issubclass(obj, XmlElement)
            and obj not in abstract_bases
        ]

        for cls in concrete_nodes:
            with self.subTest(cls=cls.__name__):
                # Concrete nodes should have __init__ defined
                self.assertTrue(
                    '__init__' in cls.__dict__ or any('__init__' in base.__dict__ for base in cls.__mro__[1:]),
                    f"{cls.__name__} should have constructor"
                )

    def test_node_init_signatures_use_type_hints(self) -> None:
        """Node __init__ methods should have proper type hints for static analysis."""
        all_exports = [getattr(x4md, name) for name in dir(x4md) if not name.startswith("_")]
        node_classes = [
            obj for obj in all_exports
            if inspect.isclass(obj)
            and issubclass(obj, XmlElement)
            and obj not in (XmlElement, MDNode, AINode, ActionNode, ConditionNode,
                          CueChildNode, ParamNode, OrderChildNode, InterruptNode)
        ]

        for cls in node_classes:
            with self.subTest(cls=cls.__name__):
                init_sig = inspect.signature(cls.__init__)

                # Check that parameters have annotations (except self)
                for param_name, param in init_sig.parameters.items():
                    if param_name == 'self':
                        continue

                    # Variadic args (*args, **kwargs, *children) may not have annotations
                    if param.kind in (inspect.Parameter.VAR_POSITIONAL,
                                     inspect.Parameter.VAR_KEYWORD):
                        continue

                    self.assertIsNot(
                        param.annotation, inspect.Parameter.empty,
                        f"{cls.__name__}.__init__ parameter '{param_name}' should have type hint"
                    )

    def test_cue_child_nodes_include_document_children(self) -> None:
        """Document module should define concrete CueChildNode subclasses."""
        import x4md.md.document as doc_mod

        # Find concrete cue children in document module (not base classes)
        concrete_cue_children = [
            obj for name, obj in inspect.getmembers(doc_mod, inspect.isclass)
            if issubclass(obj, CueChildNode)
            and obj not in (CueChildNode, ActionNode)  # Exclude base classes
            and obj.__module__ == 'x4md.md.document'
        ]

        # After the OnAbort migration, Delay is the only non-container
        # ``CueChildNode`` concrete class in ``document.py`` (``Cue``
        # and ``Library`` are containers rather than leaves). We keep
        # the assertion at >= 1 so the test fails loudly if Delay ever
        # disappears, while not rejecting future additions.
        class_names = {cls.__name__ for cls in concrete_cue_children}
        self.assertIn(
            'Delay', class_names,
            "Delay should remain in x4md.md.document as the cue-level "
            "<delay> is declared in md.xsd.",
        )
        self.assertNotIn(
            'OnAbort', class_names,
            "OnAbort was moved to x4md.x4ai.nodes: md.xsd has no "
            "<on_abort> element, so keeping it in x4md.md would "
            "silently produce schema-invalid MD scripts.",
        )

    def test_order_child_nodes_are_in_ai_package(self) -> None:
        """Nodes inheriting from OrderChildNode should be in x4ai package."""
        import x4md.x4ai.nodes as ai_nodes_mod

        order_child_classes = [
            obj for name, obj in inspect.getmembers(ai_nodes_mod, inspect.isclass)
            if issubclass(obj, OrderChildNode) and obj != OrderChildNode
        ]

        # Should find multiple AI nodes
        self.assertGreater(
            len(order_child_classes), 5,
            "Should find multiple OrderChildNode subclasses in AI package"
        )

        # Verify they're in AI nodes module
        for cls in order_child_classes:
            with self.subTest(cls=cls.__name__):
                self.assertEqual(
                    cls.__module__, 'x4md.x4ai.nodes',
                    f"{cls.__name__} should be defined in x4ai.nodes module"
                )

    def test_no_duplicate_class_names_across_packages(self) -> None:
        """Class names should be unique across MD and AI packages (except intentional aliases)."""
        import x4md.md.actions as md_actions
        import x4md.md.conditions as md_conditions
        import x4md.md.document as md_doc
        import x4md.x4ai.nodes as ai_nodes

        all_modules = [md_actions, md_conditions, md_doc, ai_nodes]
        class_names = {}

        for module in all_modules:
            module_classes = [
                (name, obj) for name, obj in inspect.getmembers(module, inspect.isclass)
                if obj.__module__ == module.__name__
            ]

            for name, cls in module_classes:
                if name in class_names:
                    # CreateOrder is intentionally duplicated (MD vs AI)
                    if name == 'CreateOrder':
                        continue

                    self.fail(
                        f"Duplicate class name '{name}' found in {cls.__module__} "
                        f"and {class_names[name].__module__}"
                    )

                class_names[name] = cls


if __name__ == '__main__':
    unittest.main()
