"""Project/file helpers for building complete X4 extension layouts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Protocol
from xml.sax.saxutils import escape


class DocumentRenderable(Protocol):
    """Protocol for document-like objects that can render full XML text."""

    def to_document(self) -> str:
        """Render the document as a complete XML string."""


def _render_document(document: DocumentRenderable | str) -> str:
    if isinstance(document, str):
        return document
    return document.to_document()


def _xml_attr(value: object) -> str:
    return escape(str(value), {'"': "&quot;"})


@dataclass(frozen=True, slots=True)
class GeneratedFile:
    """One generated output file within an X4 extension.

    Args:
        path: Relative path inside the extension folder
        content: Final UTF-8 text content for the file

    Example:
        GeneratedFile.text("libraries/demo.xml", "<library/>")
    """

    path: Path
    content: str

    @classmethod
    def text(cls, path: str | Path, content: str) -> "GeneratedFile":
        """Create a generated file from plain text content.

        Args:
            path: Relative output path
            content: Final file text

        Example:
            GeneratedFile.text("md/demo.xml", "<mdscript/>")
        """

        return cls(Path(path), content)

    @classmethod
    def document(
        cls,
        path: str | Path,
        document: DocumentRenderable | str,
    ) -> "GeneratedFile":
        """Create a generated file from a renderable document object.

        Args:
            path: Relative output path
            document: Renderable object or raw XML string

        Example:
            GeneratedFile.document("md/demo.xml", my_script)
        """

        return cls(Path(path), _render_document(document))


@dataclass(frozen=True, slots=True)
class TranslationEntry:
    """Single t-file text entry.

    Args:
        text_id: X4 text id within the page
        text: Localized string content
    """

    text_id: int
    text: str


@dataclass(frozen=True, slots=True)
class TranslationPage:
    """Localized X4 t-file page.

    Args:
        language_id: X4 language id, for example ``44`` for English
        page_id: X4 text page id
        title: Page title shown in the XML metadata
        description: Page description shown in the XML metadata
        entries: Localized entries stored in this page
        voice: Voice flag used by X4 t-files
        file_stem: Base filename used under ``t/``

    Example:
        TranslationPage(
            language_id=44,
            page_id=77000,
            title="Demo",
            description="Demo texts",
            entries=(TranslationEntry(1001, "Demo Order"),),
        )
    """

    language_id: int
    page_id: int
    title: str
    description: str
    entries: tuple[TranslationEntry, ...]
    voice: str = "no"
    file_stem: str = "0001"

    def relative_path(self) -> Path:
        """Return the X4-relative output path for this t-file page."""

        return Path("t") / f"{self.file_stem}-l{self.language_id:03d}.xml"

    def to_document(self) -> str:
        """Render this translation page as a complete X4 t-file document."""

        lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            f'<language id="{self.language_id}">',
            (
                f'  <page id="{self.page_id}" title="{_xml_attr(self.title)}" '
                f'descr="{_xml_attr(self.description)}" voice="{_xml_attr(self.voice)}">'
            ),
        ]
        for entry in self.entries:
            lines.append(f'    <t id="{entry.text_id}">{escape(entry.text)}</t>')
        lines.extend(
            [
                "  </page>",
                "</language>",
                "",
            ]
        )
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class ContentText:
    """Localized metadata entry for content.xml.

    Args:
        language: X4 language id
        name: Localized extension name
        description: Localized extension description
        author: Localized author label
    """

    language: int
    name: str
    description: str
    author: str


@dataclass(frozen=True, slots=True)
class ContentDependency:
    """Dependency entry for content.xml.

    Args:
        id: Dependency id
        name: Optional human-readable dependency name
        optional: Whether X4 should treat the dependency as optional
    """

    id: str
    name: str | None = None
    optional: bool = True


@dataclass(frozen=True, slots=True)
class ContentLibrary:
    """Library path entry for content.xml.

    Args:
        path: Library path relative to the extension root
    """

    path: str


@dataclass(frozen=True, slots=True)
class ExtensionContent:
    """Complete content.xml metadata for an X4 extension.

    Args:
        id: Extension id
        name: Visible extension name
        description: Visible extension description
        author: Author label
        version: X4 numeric version string
        date_value: Explicit ISO date string, defaults to today
        save: X4 save-compatibility flag
        enabled: Whether the extension starts enabled
        texts: Localized metadata blocks
        dependencies: Declared dependencies
        libraries: Declared library paths

    Example:
        ExtensionContent(
            id="my_extension",
            name="My Extension",
            description="Built from Python",
            author="You",
        )
    """

    id: str
    name: str
    description: str
    author: str
    version: str = "00100"
    date_value: str | None = None
    save: int = 0
    enabled: bool = True
    texts: tuple[ContentText, ...] = ()
    dependencies: tuple[ContentDependency, ...] = ()
    libraries: tuple[ContentLibrary, ...] = ()

    def to_document(self) -> str:
        """Render ``content.xml`` as a complete document."""

        content_date = self.date_value or date.today().isoformat()
        lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            (
                f'<content id="{_xml_attr(self.id)}" name="{_xml_attr(self.name)}" '
                f'description="{_xml_attr(self.description)}" author="{_xml_attr(self.author)}" '
                f'version="{_xml_attr(self.version)}" date="{_xml_attr(content_date)}" '
                f'save="{self.save}" enabled="{1 if self.enabled else 0}">'
            ),
        ]
        for text in self.texts:
            lines.append(
                (
                    f'  <text language="{text.language}" name="{_xml_attr(text.name)}" '
                    f'description="{_xml_attr(text.description)}" author="{_xml_attr(text.author)}" />'
                )
            )
        if self.dependencies:
            lines.append("  <!-- Dependencies -->")
            for dependency in self.dependencies:
                attrs = [
                    f'id="{_xml_attr(dependency.id)}"',
                    f'optional="{str(dependency.optional).lower()}"',
                ]
                if dependency.name is not None:
                    attrs.append(f'name="{_xml_attr(dependency.name)}"')
                lines.append(f"  <dependency {' '.join(attrs)} />")
        if self.libraries:
            lines.append("  <!-- Libraries -->")
            lines.append("  <libraries>")
            for library in self.libraries:
                lines.append(f'    <library path="{_xml_attr(library.path)}" />')
            lines.append("  </libraries>")
        lines.extend(["</content>", ""])
        return "\n".join(lines)


@dataclass(slots=True)
class ExtensionProject:
    """Assemble and write a complete X4 extension folder.

    Args:
        content: Optional ``content.xml`` metadata document
        md_scripts: Mapping of filenames to MD documents
        ai_scripts: Mapping of filenames to AI documents
        translations: T-file pages to place under ``t/``
        extra_files: Arbitrary extra generated files
        folder_name: Default install folder name

    Example:
        project = ExtensionProject(
            content=my_content,
            md_scripts={"main.xml": my_md_script},
            ai_scripts={"order.demo.xml": my_ai_script},
            translations=[my_translation_page],
            folder_name="my_extension",
        )
    """

    content: ExtensionContent | None = None
    md_scripts: dict[str, DocumentRenderable | str] = field(default_factory=dict)
    ai_scripts: dict[str, DocumentRenderable | str] = field(default_factory=dict)
    translations: list[TranslationPage] = field(default_factory=list)
    extra_files: list[GeneratedFile] = field(default_factory=list)
    folder_name: str | None = None

    def file_map(self, *, include_content: bool = True) -> dict[Path, str]:
        """Build the relative output file map for this extension.

        Args:
            include_content: Whether to include ``content.xml`` in the result

        Returns:
            Mapping of relative output paths to final file text
        """

        files: dict[Path, str] = {}
        if include_content and self.content is not None:
            files[Path("content.xml")] = self.content.to_document()
        for relative_path, document in self.md_scripts.items():
            files[Path("md") / relative_path] = _render_document(document)
        for relative_path, document in self.ai_scripts.items():
            files[Path("aiscripts") / relative_path] = _render_document(document)
        for page in self.translations:
            files[page.relative_path()] = page.to_document()
        for generated_file in self.extra_files:
            files[generated_file.path] = generated_file.content
        return files

    def write(self, output_dir: str | Path, *, include_content: bool = True) -> Path:
        """Write the generated extension tree to disk.

        Args:
            output_dir: Destination folder for the generated extension
            include_content: Whether to include ``content.xml``

        Returns:
            The destination root that was written
        """

        destination_root = Path(output_dir)
        destination_root.mkdir(parents=True, exist_ok=True)
        for relative_path, content in self.file_map(include_content=include_content).items():
            destination = destination_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
        return destination_root

    def install(
        self,
        extensions_dir: str | Path,
        folder_name: str | None = None,
    ) -> Path:
        """Install the extension into an X4 ``extensions`` directory.

        Args:
            extensions_dir: X4 extensions root directory
            folder_name: Optional override for the installed folder name

        Returns:
            Full path to the installed extension folder
        """

        destination = Path(extensions_dir) / (
            folder_name or self.folder_name or (self.content.id if self.content else "extension")
        )
        self.write(destination, include_content=True)
        return destination
