#!/usr/bin/env python3
"""Zip the `capitalism` package (code + db) for the Pyodide smoke page.

Usage: python scripts/pyodide_bundle.py [output.zip]   (default: web/capitalism.zip)
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "capitalism"


def build(out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PKG.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                zf.write(path, path.relative_to(PKG.parent).as_posix())
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    out = Path(args[0]) if args else ROOT / "web" / "capitalism.zip"
    print(f"wrote {build(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
