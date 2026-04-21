"""Tests for capability matrix generation."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class CapabilityMatrixTests(unittest.TestCase):
    def test_generator_writes_expected_sections(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "scripts" / "generate_capability_matrix.py"
        output = repo_root / ".tmp-capability-matrix.md"
        try:
            completed = subprocess.run(
                [sys.executable, str(script), "--output", str(output)],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Wrote capability matrix", completed.stdout)
            content = output.read_text(encoding="utf-8")
            self.assertIn("# X4-PINAT Capability Status (Auto-Generated)", content)
            self.assertIn("## Mission Director", content)
            self.assertIn("## AI Script", content)
            self.assertIn("`FindBuyOffer`", content)
            self.assertIn("`SetCommand`", content)
        finally:
            if output.exists():
                output.unlink()


if __name__ == "__main__":
    unittest.main()
