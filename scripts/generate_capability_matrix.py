"""Generate a markdown capability matrix from the current x4md exports."""

from __future__ import annotations

import argparse
import inspect
import sys
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import x4md  # noqa: E402


def _section_for_module(module_name: str) -> str:
    if module_name.startswith("x4md.md"):
        return "Mission Director"
    if module_name.startswith("x4md.x4ai"):
        return "AI Script"
    if module_name.startswith("x4md.project"):
        return "Project and Extension Files"
    if module_name.startswith("x4md.expressions"):
        return "Expressions"
    if module_name.startswith("x4md.core"):
        return "Core XML"
    return "Other"


def build_markdown() -> str:
    by_section: dict[str, set[str]] = defaultdict(set)
    for name in x4md.__all__:
        obj = getattr(x4md, name, None)
        if obj is None or not inspect.isclass(obj):
            continue
        by_section[_section_for_module(obj.__module__)].add(name)

    lines: list[str] = [
        "# X4-PINAT Capability Status (Auto-Generated)",
        "",
        "This snapshot is generated from exported class symbols in `x4md.__all__`.",
        "",
        "Last refreshed: 2026-04-21",
        "",
        "## Coverage Position",
        "",
        "- Core MD and AI generation primitives are broadly available.",
        "- Remaining gaps are mostly niche/specialized nodes outside the common scaffolding path.",
        "",
    ]

    ordered_sections = [
        "Core XML",
        "Expressions",
        "Project and Extension Files",
        "Mission Director",
        "AI Script",
        "Other",
    ]
    for section in ordered_sections:
        items = sorted(by_section.get(section, []))
        if not items:
            continue
        lines.append(f"## {section}")
        lines.append("")
        lines.append(f"- Total exported classes: {len(items)}")
        lines.append(f"- Symbols: {', '.join(f'`{item}`' for item in items)}")
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- This matrix reflects exported API surface, not semantic parity with every X4 node variant.",
            "- Use downstream mod needs to prioritize any additional node additions.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate x4md capability matrix markdown.")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "MISSING_FUNCTIONALITY.md",
        help="Target markdown file path.",
    )
    args = parser.parse_args()
    content = build_markdown()
    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote capability matrix to: {args.output}")


if __name__ == "__main__":
    main()
