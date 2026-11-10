#!/usr/bin/env python3
"""Parse a Capitalism Plus .SET file and compare product data against our rules DB.

The SET file is a custom archive of dBASE III tables, one per section.
Sections: RICH, ITEMCLAS, FIRMJOB, JOB, RAW, GROUP, PERSON, METHOD,
          FARMPROD, HEADER, TOWN, FIRM, ITEMPAE, ITEM, FARMLIVE, FARMCROP.

Usage:
  python scripts/parse_set.py [path-to-set-file]
  python scripts/parse_set.py --compare   # compare against capitalism.db
"""

from __future__ import annotations

import argparse
import sqlite3
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "src" / "capitalism" / "data" / "capitalism.db"
DEFAULT_SET = Path(r"D:\capitalism plus\CAPPLUS\GAMESET\1STD.SET")


def read_set_index(data: bytes) -> list[tuple[str, int]]:
    count = struct.unpack_from("<H", data, 0)[0]
    sections: list[tuple[str, int]] = []
    for i in range(count):
        off = 2 + i * 13
        name = data[off : off + 9].split(b"\x00")[0].decode("ascii")
        offset = struct.unpack_from("<I", data, off + 9)[0]
        sections.append((name, offset))
    return sections


def parse_dbf_section(data: bytes, section_offset: int, section_end: int) -> list[dict[str, str]]:
    base = section_offset
    _version = data[base]
    rec_count = struct.unpack_from("<I", data, base + 4)[0]
    header_size = struct.unpack_from("<H", data, base + 8)[0]
    rec_size = struct.unpack_from("<H", data, base + 10)[0]

    fields: list[tuple[str, str, int, int]] = []
    pos = base + 32
    while pos < base + header_size - 1:
        if data[pos] == 0x0D:
            break
        fname = data[pos : pos + 11].split(b"\x00")[0].decode("ascii")
        ftype = chr(data[pos + 11])
        flen = data[pos + 16]
        fdec = data[pos + 17]
        fields.append((fname, ftype, flen, fdec))
        pos += 32

    data_start = base + header_size
    records: list[dict[str, str]] = []
    for i in range(rec_count):
        roff = data_start + i * rec_size
        if roff + rec_size > section_end:
            break
        row: dict[str, str] = {}
        fpos = 1  # skip delete flag byte
        for fname, ftype, flen, fdec in fields:
            raw = data[roff + fpos : roff + fpos + flen]
            val = raw.decode("ascii", errors="ignore").strip()
            row[fname] = val
            fpos += flen
        records.append(row)
    return records


def parse_set(path: Path) -> dict[str, list[dict[str, str]]]:
    data = path.read_bytes()
    sections = read_set_index(data)
    result: dict[str, list[dict[str, str]]] = {}
    for i, (name, offset) in enumerate(sections):
        end = sections[i + 1][1] if i + 1 < len(sections) else len(data)
        try:
            records = parse_dbf_section(data, offset, end)
            result[name] = records
        except Exception as e:
            print(f"  Warning: could not parse {name}: {e}", file=sys.stderr)
    return result


def dump_section(name: str, records: list[dict[str, str]]) -> None:
    if not records:
        print(f"  (empty)")
        return
    fields = list(records[0].keys())
    print(f"  Fields: {', '.join(fields)}")
    print(f"  Records: {len(records)}")
    for i, rec in enumerate(records[:3]):
        vals = [f"{k}={v!r}" for k, v in rec.items() if v]
        print(f"    [{i}] {', '.join(vals)}")
    if len(records) > 3:
        print(f"    ... ({len(records) - 3} more)")


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "").replace("-", "")


def compare_products(set_items: list[dict[str, str]], db_path: Path) -> tuple[int, int]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    db_products_by_name: dict[str, dict] = {}
    for r in con.execute("SELECT * FROM products ORDER BY id"):
        row = dict(r)
        key = _normalize_name(row["name"])
        db_products_by_name[key] = row

    ok = 0
    mismatch = 0
    matched_db: set[str] = set()

    print(f"\n{'='*70}")
    print(f"Product comparison: SET ({len(set_items)} items) vs DB ({len(db_products_by_name)} items)")
    print(f"{'='*70}\n")

    field_map = {
        "base_price": ("PRICE", float),
        "demand_per_1000": ("DEMAND", float),
        "luxury": ("LUXURY", int),
        "necessity": ("NECESSITY", int),
        "w_price": ("PRICE_CN", float),
        "w_quality": ("QUALITY_CN", float),
        "w_brand": ("BRAND_CN", float),
        "tech_importance": ("TECH_IMPT", float),
        "spending_usd": ("SPENDING", float),
    }

    for item in set_items:
        code = item.get("CODE", "").strip()
        name = item.get("NAME", "").strip()
        if not name:
            continue
        key = _normalize_name(name)
        db_row = db_products_by_name.get(key)
        if db_row is None:
            print(f"  MISSING in DB: {code:10s} ({name})")
            mismatch += 1
            continue
        matched_db.add(key)

        diffs: list[str] = []
        for db_field, (set_field, conv) in field_map.items():
            set_val_str = item.get(set_field, "").strip()
            if not set_val_str:
                continue
            try:
                set_val = conv(set_val_str)
            except ValueError:
                continue
            db_val = db_row.get(db_field)
            if db_val is None:
                continue
            if abs(float(set_val) - float(db_val)) > 0.01:
                diffs.append(f"{db_field}: SET={set_val} DB={db_val}")

        if diffs:
            print(f"  DIFF {code:10s} ({name}): {'; '.join(diffs)}")
            mismatch += 1
        else:
            ok += 1

    for key, row in sorted(db_products_by_name.items()):
        if key not in matched_db:
            print(f"  EXTRA in DB: {row['code']} ({row['name']})")
            mismatch += 1

    return ok, mismatch


def compare_firms(set_firms: list[dict[str, str]], db_path: Path) -> tuple[int, int]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    db_firms = {
        r["id"]: dict(r)
        for r in con.execute("SELECT * FROM firm_types ORDER BY id")
    }
    ok = 0
    mismatch = 0

    print(f"\n{'='*70}")
    print(f"Firm type comparison: SET ({len(set_firms)} types) vs DB ({len(db_firms)} types)")
    print(f"{'='*70}\n")

    for i, firm in enumerate(set_firms):
        code = firm.get("CODE", "").strip()
        name = firm.get("NAME", "").strip()
        firm_id = i + 1
        db_row = db_firms.get(firm_id)
        if db_row is None:
            print(f"  MISSING in DB: firm #{firm_id} {name}")
            mismatch += 1
            continue

        diffs: list[str] = []
        set_setup = firm.get("SETUP_COST", "").strip()
        if set_setup:
            try:
                set_cost = float(set_setup) * 1000
                db_cost = db_row.get("setup_cost", 0)
                if db_cost and abs(set_cost - float(db_cost)) > 1:
                    diffs.append(f"setup_cost: SET={set_cost:.0f} DB={db_cost}")
            except ValueError:
                pass

        set_expense = firm.get("EXPENSE", "").strip()
        if set_expense:
            try:
                set_oh = float(set_expense) * 1000
                db_oh = db_row.get("overhead_month", 0)
                if db_oh and abs(set_oh - float(db_oh)) > 1:
                    diffs.append(f"overhead: SET={set_oh:.0f} DB={db_oh}")
            except ValueError:
                pass

        if diffs:
            print(f"  DIFF firm #{firm_id} {name}: {'; '.join(diffs)}")
            mismatch += 1
        else:
            ok += 1

    return ok, mismatch


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse Capitalism Plus .SET file")
    ap.add_argument("set_file", nargs="?", type=Path, default=DEFAULT_SET)
    ap.add_argument("--compare", action="store_true", help="Compare against capitalism.db")
    ap.add_argument("--dump", action="store_true", help="Dump all sections")
    args = ap.parse_args(argv)

    if not args.set_file.exists():
        print(f"SET file not found: {args.set_file}", file=sys.stderr)
        return 1

    print(f"Parsing: {args.set_file}")
    sections = parse_set(args.set_file)
    print(f"Sections: {', '.join(sections.keys())}")

    if args.dump:
        for name, records in sections.items():
            print(f"\n--- {name} ---")
            dump_section(name, records)

    if args.compare:
        if not DB.exists():
            print(f"Database not found: {DB}", file=sys.stderr)
            return 1

        total_ok = 0
        total_mismatch = 0

        if "ITEM" in sections:
            ok, mis = compare_products(sections["ITEM"], DB)
            total_ok += ok
            total_mismatch += mis

        if "FIRM" in sections:
            ok, mis = compare_firms(sections["FIRM"], DB)
            total_ok += ok
            total_mismatch += mis

        print(f"\n{'='*70}")
        print(f"Total: {total_ok} matched, {total_mismatch} differences")
        print(f"{'='*70}")
        return 1 if total_mismatch > 0 else 0

    if not args.dump and not args.compare:
        for name, records in sections.items():
            print(f"\n--- {name} ---")
            dump_section(name, records)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
