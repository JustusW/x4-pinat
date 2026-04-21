"""Tests for extension project/file generation helpers."""

from __future__ import annotations

import inspect
import unittest
from shutil import rmtree
from pathlib import Path

from x4md import (
    AIScript,
    ContentDependency,
    ContentLibrary,
    ContentText,
    Cue,
    Cues,
    ExtensionContent,
    ExtensionProject,
    GeneratedFile,
    MDScript,
    Order,
    TextExpr,
    TranslationEntry,
    TranslationPage,
)


class ProjectTests(unittest.TestCase):
    """Tests for high-level extension file handling."""

    def test_project_api_uses_explicit_ide_friendly_signatures(self) -> None:
        """Public project helpers keep explicit signatures for autocomplete."""
        self.assertNotIn(
            inspect.Parameter.VAR_KEYWORD,
            {param.kind for param in inspect.signature(ExtensionProject.__init__).parameters.values()},
        )
        self.assertNotIn(
            inspect.Parameter.VAR_KEYWORD,
            {param.kind for param in inspect.signature(GeneratedFile.document).parameters.values()},
        )
        self.assertEqual(
            inspect.signature(ExtensionProject.write).parameters["include_content"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

    def test_extension_content_renders_expected_xml(self) -> None:
        content = ExtensionContent(
            id="demo_extension",
            name="Demo Extension",
            description="Demo extension description",
            author="Codex",
            version="00123",
            date_value="2026-04-21",
            texts=(
                ContentText(
                    language=44,
                    name="Demo Extension",
                    description="Demo extension description",
                    author="Codex",
                ),
            ),
            dependencies=(
                ContentDependency(id="dep.required", optional=False, name="Dependency"),
            ),
            libraries=(ContentLibrary(path="libraries/demo.xml"),),
        )

        xml = content.to_document()
        self.assertIn('<content id="demo_extension"', xml)
        self.assertIn('version="00123"', xml)
        self.assertIn('date="2026-04-21"', xml)
        self.assertIn('<text language="44" name="Demo Extension"', xml)
        self.assertIn('<dependency id="dep.required" optional="false" name="Dependency" />', xml)
        self.assertIn('<library path="libraries/demo.xml" />', xml)

    def test_extension_content_renders_dependency_without_name(self) -> None:
        content = ExtensionContent(
            id="demo_extension",
            name="Demo Extension",
            description="Demo extension description",
            author="Codex",
            dependencies=(ContentDependency(id="dep.optional"),),
        )

        xml = content.to_document()
        self.assertIn('<dependency id="dep.optional" optional="true" />', xml)

    def test_translation_page_renders_expected_xml(self) -> None:
        page = TranslationPage(
            language_id=44,
            page_id=77000,
            title="Demo",
            description="Demo texts",
            entries=(
                TranslationEntry(1001, "Order Name"),
                TranslationEntry(1002, "Order Description"),
            ),
        )

        xml = page.to_document()
        self.assertIn('<language id="44">', xml)
        self.assertIn('<page id="77000" title="Demo" descr="Demo texts"', xml)
        self.assertIn('<t id="1001">Order Name</t>', xml)
        self.assertEqual(page.relative_path(), Path("t/0001-l044.xml"))

    def test_generated_file_helpers_render_text_and_documents(self) -> None:
        text_file = GeneratedFile.text("docs/readme.txt", "hello")
        raw_xml_file = GeneratedFile.document("md/raw.xml", "<raw/>")
        xml_file = GeneratedFile.document(
            "md/demo.xml",
            MDScript(name="Demo", cues=Cues(Cue("Init"))),
        )

        self.assertEqual(text_file.path, Path("docs/readme.txt"))
        self.assertEqual(text_file.content, "hello")
        self.assertEqual(raw_xml_file.content, "<raw/>")
        self.assertEqual(xml_file.path, Path("md/demo.xml"))
        self.assertIn('<?xml version="1.0" encoding="utf-8"?>', xml_file.content)

    def test_extension_project_builds_and_writes_expected_structure(self) -> None:
        project = ExtensionProject(
            content=ExtensionContent(
                id="demo_extension",
                name="Demo Extension",
                description="Demo extension description",
                author="Codex",
                date_value="2026-04-21",
                texts=(
                    ContentText(
                        language=44,
                        name="Demo Extension",
                        description="Demo extension description",
                        author="Codex",
                    ),
                ),
            ),
            md_scripts={
                "demo.xml": MDScript(name="Demo", cues=Cues(Cue("Init"))),
            },
            ai_scripts={
                "order.demo.xml": AIScript(
                    "order.demo",
                    Order(
                        "DemoOrder",
                        name=TextExpr.ref(77000, 1001),
                    ),
                ),
            },
            translations=[
                TranslationPage(
                    language_id=44,
                    page_id=77000,
                    title="Demo",
                    description="Demo texts",
                    entries=(TranslationEntry(1001, "Demo Order"),),
                )
            ],
            extra_files=[
                GeneratedFile.text("libraries/demo.txt", "library data"),
            ],
            folder_name="demo_extension",
        )

        file_map = project.file_map()
        self.assertIn(Path("content.xml"), file_map)
        self.assertIn(Path("md/demo.xml"), file_map)
        self.assertIn(Path("aiscripts/order.demo.xml"), file_map)
        self.assertIn(Path("t/0001-l044.xml"), file_map)
        self.assertIn(Path("libraries/demo.txt"), file_map)
        self.assertNotIn(Path("content.xml"), project.file_map(include_content=False))

        temp_dir = Path.cwd() / ".tmp-project-write"
        if temp_dir.exists():
            rmtree(temp_dir, ignore_errors=True)
        try:
            written = project.write(temp_dir)
            self.assertEqual(written, temp_dir)
            self.assertTrue((temp_dir / "content.xml").exists())
            self.assertTrue((temp_dir / "md" / "demo.xml").exists())
            self.assertTrue((temp_dir / "aiscripts" / "order.demo.xml").exists())
            self.assertTrue((temp_dir / "t" / "0001-l044.xml").exists())

            install_root = temp_dir / "extensions"
            destination = project.install(install_root)
            self.assertEqual(destination, install_root / "demo_extension")
            self.assertTrue((destination / "content.xml").exists())
        finally:
            if temp_dir.exists():
                rmtree(temp_dir, ignore_errors=True)

    def test_install_falls_back_to_content_id_or_generic_folder(self) -> None:
        project_with_content = ExtensionProject(
            content=ExtensionContent(
                id="fallback_extension",
                name="Fallback",
                description="Fallback",
                author="Codex",
            )
        )
        contentless_project = ExtensionProject()

        temp_dir = Path.cwd() / ".tmp-project-write"
        if temp_dir.exists():
            rmtree(temp_dir, ignore_errors=True)
        try:
            self.assertEqual(
                project_with_content.install(temp_dir),
                temp_dir / "fallback_extension",
            )
            self.assertEqual(
                contentless_project.install(temp_dir / "other"),
                temp_dir / "other" / "extension",
            )
        finally:
            if temp_dir.exists():
                rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
