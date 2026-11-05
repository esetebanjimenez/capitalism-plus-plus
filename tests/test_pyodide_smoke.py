"""Pyodide smoke (web/README.md). Skips unless node and the pinned pyodide are installed."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def test_bundle_contains_package_and_db(tmp_path):
    import zipfile

    out = tmp_path / "capitalism.zip"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "pyodide_bundle.py"), str(out)], check=True
    )
    names = set(zipfile.ZipFile(out).namelist())
    assert "capitalism/sim.py" in names
    assert "capitalism/data/capitalism.db" in names


@pytest.mark.skipif(
    shutil.which("node") is None or not (WEB / "node_modules" / "pyodide").exists(),
    reason="node or web/node_modules/pyodide not installed (npm install --prefix web)",
)
def test_sim_runs_under_pyodide():
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "pyodide_bundle.py")], check=True, cwd=ROOT
    )
    r = subprocess.run(
        ["node", str(WEB / "smoke.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS capitalism" in r.stdout
    # Same seed, same state under Pyodide as under CPython.
    from capitalism.scenario import bread_town, build_bread_chain

    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    sim.advance_days(10)
    assert f"hash {sim.state_hash()[:16]}" in r.stdout
