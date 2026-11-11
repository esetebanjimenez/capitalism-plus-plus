#!/usr/bin/env python3
"""Parse a Capitalism Plus .SAV file and extract game state for comparison.

Reads the section-tagged binary format written by save_game_file (0x1db44)
as documented in analysis/CAPPLUS/notes/save_format.md.

Key I/O discovery: the game's file I/O layer uses a "chunked" mode where
every write_blob call prepends a 2-byte LE size prefix before the data.
write_short and write_int32 do NOT get prefixes.

Usage:
  python scripts/parse_sav.py path/to/save.SAV
  python scripts/parse_sav.py path/to/save.SAV --compare  # compare against sim
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Low-level I/O (mirrors the game's read_short / read_int32 / read_blob)
# ---------------------------------------------------------------------------

class BinaryReader:
    __slots__ = ("data", "pos")

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def read_raw(self, n: int) -> bytes:
        """Read exactly n bytes (no prefix)."""
        chunk = self.data[self.pos : self.pos + n]
        if len(chunk) < n:
            raise EOFError(f"wanted {n} bytes at 0x{self.pos:X}, got {len(chunk)}")
        self.pos += n
        return chunk

    def read_short(self) -> int:
        return struct.unpack_from("<h", self.read_raw(2))[0]

    def read_ushort(self) -> int:
        return struct.unpack_from("<H", self.read_raw(2))[0]

    def read_int32(self) -> int:
        return struct.unpack_from("<i", self.read_raw(4))[0]

    def read_uint32(self) -> int:
        return struct.unpack_from("<I", self.read_raw(4))[0]

    def read_float(self) -> float:
        return struct.unpack_from("<f", self.read_raw(4))[0]

    # -- Prefixed blob I/O (the game's chunked write_blob mode) --

    def read_blob(self, expected: int = 0) -> bytes:
        """Read a size-prefixed blob: 2-byte LE size + data.

        When the actual data exceeds 65535, the writer truncates the prefix
        to 0x0000.  The game's reader falls back to the caller's requested
        size in that case.  We mirror that: if prefix == 0 and expected > 0,
        use expected.
        """
        prefix = self.read_ushort()
        size = prefix if prefix > 0 else expected
        if size == 0:
            return b""
        return self.read_raw(size)

    def skip_blob(self, expected: int = 0) -> int:
        """Skip a size-prefixed blob, return the data size."""
        prefix = self.read_ushort()
        size = prefix if prefix > 0 else expected
        self.pos += size
        return size

    def skip(self, n: int) -> None:
        self.pos += n

    def seek_back(self, n: int) -> None:
        self.pos -= n

    def remaining(self) -> int:
        return len(self.data) - self.pos

    # -- DynArr / DynArrB with prefixed sub-blobs --

    def read_dynarr_header(self) -> tuple[int, int, int]:
        """Read a DynArr: prefixed 0x1D header blob, return (count, elem_size, data_bytes)."""
        hdr = self.read_blob()  # prefixed: expect 0x1D bytes
        count = struct.unpack_from("<I", hdr, 0x0C)[0]
        elem_size = struct.unpack_from("<I", hdr, 0x10)[0]
        return count, elem_size, count * elem_size

    def skip_dynarr(self) -> None:
        count, _elem_size, data_bytes = self.read_dynarr_header()
        if count > 0:
            self.skip_blob(expected=data_bytes)

    def read_dynarrb_header(self) -> tuple[int, int, int, int]:
        """Read a DynArrB: prefixed 0x2C header blob, return (count, elem_size, data_bytes, free_count)."""
        hdr = self.read_blob()  # prefixed: expect 0x2C bytes
        count = struct.unpack_from("<I", hdr, 0x0C)[0]
        elem_size = struct.unpack_from("<I", hdr, 0x10)[0]
        free_cap = struct.unpack_from("<I", hdr, 0x24)[0]
        return count, elem_size, count * elem_size, free_cap

    def skip_dynarrb(self) -> None:
        count, _elem_size, data_bytes, free_count = self.read_dynarrb_header()
        if count > 0:
            self.skip_blob(expected=data_bytes)
        if free_count > 0:
            self.skip_blob(expected=free_count * 4)

    def read_cstring(self, buf: bytes, offset: int, max_len: int) -> str:
        end = buf.find(b"\x00", offset, offset + max_len)
        if end < 0:
            end = offset + max_len
        return buf[offset:end].decode("ascii", errors="replace")


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class SaveHeader:
    scenario_id: int = 0
    flag_byte: int = 0
    day_serial: int = 0
    corp_name: str = ""
    ai_type: int = 0
    years_played: int = 0
    score1: int = 0
    score2: int = 0
    wealth: float = 0.0
    net_worth: float = 0.0
    scenario_name: str = ""


@dataclass
class GameDate:
    raw: bytes = b""
    day_serial: int = 0
    year: int = 0
    month: int = 0
    day: int = 0


@dataclass
class Corporation:
    slot: int = 0
    corp_type: int = 0
    name: str = ""
    cash: float = 0.0
    net_worth: float = 0.0
    reputation: float = 0.0


@dataclass
class Town:
    index: int = 0
    name: str = ""
    population: float = 0.0
    gnp_per_capita: float = 0.0
    unemployment: float = 0.0
    labor_cost: float = 0.0
    labor_quality: float = 0.0
    consumer_spending: float = 0.0
    econ_climate: int = 0


@dataclass
class SaveState:
    header: SaveHeader = field(default_factory=SaveHeader)
    version_tag: int = 0
    is_design_mode: bool = False
    game_date: GameDate = field(default_factory=GameDate)
    num_products: int = 0
    num_classes: int = 0
    num_corp_slots: int = 0
    corporations: list[Corporation] = field(default_factory=list)
    towns: list[Town] = field(default_factory=list)
    sections_seen: list[int] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Header parser
# ---------------------------------------------------------------------------

def parse_header(r: BinaryReader) -> SaveHeader:
    blob = r.read_blob()  # prefixed: expect 0x6D bytes
    h = SaveHeader()
    h.scenario_id = struct.unpack_from("<h", blob, 0x0D)[0]
    h.flag_byte = blob[0x0F]
    h.day_serial = struct.unpack_from("<i", blob, 0x10)[0]
    h.corp_name = r.read_cstring(blob, 0x14, 30)
    h.ai_type = blob[0x33]
    h.years_played = struct.unpack_from("<i", blob, 0x34)[0]
    h.score1 = struct.unpack_from("<h", blob, 0x38)[0]
    h.score2 = struct.unpack_from("<h", blob, 0x3A)[0]
    h.wealth = struct.unpack_from("<f", blob, 0x3C)[0]
    h.net_worth = struct.unpack_from("<f", blob, 0x40)[0]
    h.scenario_name = r.read_cstring(blob, 0x44, len(blob) - 0x44)
    return h


# ---------------------------------------------------------------------------
# Section parsers
# ---------------------------------------------------------------------------

def parse_game_date(r: BinaryReader) -> GameDate:
    """Tag 0x1005: g_game_date — prefixed blob (expect 0x41 bytes)."""
    blob = r.read_blob()
    gd = GameDate(raw=blob)
    gd.day_serial = struct.unpack_from("<i", blob, 0x04)[0]
    gd.day = struct.unpack_from("<i", blob, 0x08)[0]
    gd.month = struct.unpack_from("<i", blob, 0x0C)[0]
    gd.year = struct.unpack_from("<i", blob, 0x10)[0]
    return gd


def parse_group_a(r: BinaryReader, state: SaveState) -> None:
    """Parse Group A: tags 0x1001-0x1008."""
    expected = [0x1001, 0x1002, 0x1003, 0x1004, 0x1005, 0x1006, 0x1007, 0x1008]
    for exp_tag in expected:
        if debug:
            print(f"  [A] reading tag at 0x{r.pos:X}, expect 0x{exp_tag:04X}")
        tag = r.read_short()
        if tag != exp_tag:
            raise ValueError(f"expected tag 0x{exp_tag:04X}, got 0x{tag:04X} at 0x{r.pos - 2:X}")
        state.sections_seen.append(tag)

        if tag == 0x1001:  # g_cfg: write_int32 (no prefix)
            r.read_int32()
        elif tag == 0x1002:  # interest_rate: write_blob(0x2C) → prefixed
            r.skip_blob()
        elif tag == 0x1003:  # DAT_000b2409: 2 shorts + blob(4) + dynarr + short
            r.read_short()
            r.read_short()
            r.skip_blob()  # 4-byte blob (prefixed)
            r.skip_dynarr()
            r.read_short()
        elif tag == 0x1004:  # DAT_000b1c5c: dynarr
            r.skip_dynarr()
        elif tag == 0x1005:  # g_game_date: blob(0x41) → prefixed
            state.game_date = parse_game_date(r)
        elif tag == 0x1006:  # town_subsys: 5 shorts + blob(w*h*8) + short
            _s1 = r.read_short()
            s2 = r.read_short()  # width
            s3 = r.read_short()  # height
            _s4 = r.read_short()
            _s5 = r.read_short()
            grid_size = s2 * s3 * 8
            r.skip_blob(expected=grid_size)
            r.read_short()
        elif tag == 0x1007:  # g_window: DAT_000b267e array + blob(0x54)
            # FUN_00087a94 writes N elements: blob(0xC) + short each.
            # Then conditionally writes blob(0x54).
            # Detect end of loop by peeking at the prefix: 0x0C = element, otherwise final blob.
            while True:
                prefix = r.read_ushort()
                if prefix == 0x0C:
                    r.skip(0x0C)
                    r.read_short()
                else:
                    r.skip(prefix)  # final blob (0x54 bytes)
                    break
        elif tag == 0x1008:  # DAT_000b2452: dynarr
            r.skip_dynarr()


def parse_group_b(r: BinaryReader, state: SaveState) -> None:
    """Parse Group B: tags 0x100B-0x1011."""
    expected = [0x100B, 0x100C, 0x100D, 0x100E, 0x100F, 0x1010, 0x1011]
    for exp_tag in expected:
        if debug:
            print(f"  [B] reading tag at 0x{r.pos:X}, expect 0x{exp_tag:04X}")
        tag = r.read_short()
        if tag != exp_tag:
            raise ValueError(f"expected tag 0x{exp_tag:04X}, got 0x{tag:04X} at 0x{r.pos - 2:X}")
        state.sections_seen.append(tag)

        if tag == 0x100B:
            # product_system: two prefixed blobs.
            # First: num_products * 0x14A bytes, second: num_classes * 0x3A bytes
            prod_size = r.skip_blob()
            class_size = r.skip_blob()
            if prod_size % 0x14A == 0:
                state.num_products = prod_size // 0x14A
            if class_size % 0x3A == 0:
                state.num_classes = class_size // 0x3A

        elif tag == 0x100C:
            pass  # firm_templates: NOOP

        elif tag == 0x100D:
            # counters: blob(8) + short(count) + count*int32
            r.skip_blob()  # 8-byte blob (prefixed)
            count_or_tag = r.read_short()
            if count_or_tag == 0x100E:
                r.seek_back(2)
            else:
                for _ in range(count_or_tag):
                    r.read_int32()

        elif tag == 0x100E:
            pass  # NOOP

        elif tag == 0x100F:
            # person_types: short + blob(count*0x6E) → prefixed blob
            _field = r.read_short()
            r.skip_blob()  # person data (prefixed — size gives exact byte count)

        elif tag == 0x1010:
            # DAT_000b1c53: write_short only
            r.read_short()

        elif tag == 0x1011:
            # DAT_000b1c2f: blob(count*0xD) + dynarr
            r.skip_blob()  # prefixed blob
            r.skip_dynarr()


def _deobfuscate_name(blob: bytes, offset: int = 0x32, length: int = 0x14) -> str:
    name_bytes = bytearray(blob[offset : offset + length])
    for i in range(length):
        name_bytes[i] = (name_bytes[i] + (i * -2)) & 0xFF
    return name_bytes.split(b"\x00")[0].decode("ascii", errors="replace")


def parse_corporations(r: BinaryReader, state: SaveState) -> list[Corporation]:
    """Parse the g_firms section (tag 0x101A).

    Per-corp layout: type(short) then for non-empty:
      blob(0x83B) + blob(slots*4) + blob(0x214) + blob(0x4D)
    All types have total object size 0x88C, so type-specific = 0x88C-0x83F = 0x4D.
    """
    corps: list[Corporation] = []
    r.read_short()  # s1
    r.read_short()  # s2
    r.read_short()  # s3
    count = r.read_short()
    state.num_corp_slots = count

    for i in range(1, count + 1):
        corp_type = r.read_short()
        if corp_type == 0:
            continue
        base = r.read_blob(expected=0x83B)
        r.skip_blob()  # slot data: num_corp_slots * 4
        r.skip_blob()  # strategy: 0x214
        r.skip_blob()  # type-specific: 0x4D
        if len(base) >= 0x18E:
            name = r.read_cstring(base, 0x02, 48)
            corps.append(Corporation(
                slot=i, corp_type=corp_type, name=name,
                cash=struct.unpack_from("<f", base, 0x186)[0],
                net_worth=struct.unpack_from("<f", base, 0x18A)[0],
                reputation=0.0,
            ))
    return corps


def parse_towns(r: BinaryReader, state: SaveState) -> list[Town]:
    """Parse the town_manager section (tag 0x101B)."""
    towns: list[Town] = []
    r.read_short()
    r.read_short()
    r.read_int32()
    count = r.read_short()

    for i in range(count):
        base = r.read_blob()  # 0x173 base struct (prefixed)
        name = base[2:32].split(b"\x00")[0].decode("ascii", errors="replace")
        population = struct.unpack_from("<f", base, 0x2d)[0]
        gnp_per_capita = struct.unpack_from("<f", base, 0x31)[0]
        unemployment = struct.unpack_from("<f", base, 0x47)[0]
        labor_cost = struct.unpack_from("<f", base, 0x3b)[0]
        labor_quality = struct.unpack_from("<f", base, 0x43)[0]
        consumer_spending = struct.unpack_from("<f", base, 0x3f)[0]
        econ_climate = struct.unpack_from("<h", base, 0x39)[0]
        towns.append(Town(
            index=i, name=name, population=population,
            gnp_per_capita=gnp_per_capita, unemployment=unemployment,
            labor_cost=labor_cost, labor_quality=labor_quality,
            consumer_spending=consumer_spending, econ_climate=econ_climate,
        ))
        r.skip_blob()  # product demands: num_products * 2 bytes (prefixed)
        r.skip_blob()  # per-corp town data: num_corp_slots * 0x1A bytes (prefixed)

    r.skip_dynarrb()  # town list dynarrb
    return towns


# ---------------------------------------------------------------------------
# Group C parser
# ---------------------------------------------------------------------------

def parse_group_c(r: BinaryReader, state: SaveState) -> None:
    """Parse Group C: tags 0x1015-0x101D."""
    expected = [0x1015, 0x1016, 0x1017, 0x1018, 0x1019, 0x101A, 0x101B, 0x101C, 0x101D]
    for exp_tag in expected:
        if debug:
            print(f"  [C] reading tag at 0x{r.pos:X}, expect 0x{exp_tag:04X}")
        tag = r.read_short()
        if tag != exp_tag:
            raise ValueError(f"expected tag 0x{exp_tag:04X}, got 0x{tag:04X} at 0x{r.pos - 2:X}")
        state.sections_seen.append(tag)

        if tag == 0x1015:
            # g_item_array: dynarrb + 3 shorts
            r.skip_dynarrb()
            r.read_short()
            r.read_short()
            r.read_short()

        elif tag == 0x1016:
            r.skip_dynarrb()

        elif tag == 0x1017:
            # g_job_array: short(count) + short(next_id) + per-job data
            # Per-job: short(type) + prefixed blob(0x24) + vtable-dispatch
            # Complex variable-size → scan for next tag
            _count = r.read_short()
            _next_id = r.read_short()
            search = struct.pack("<h", 0x1018)
            idx = r.data.find(search, r.pos)
            if idx >= 0:
                r.pos = idx
            else:
                raise ValueError("cannot find tag 0x1018 after job_array")

        elif tag == 0x1018:
            # g_firm_array: 3 shorts + per-firm variable data
            # Vtable-dispatch → scan for next tag
            r.read_short()
            r.read_short()
            r.read_short()
            search = struct.pack("<h", 0x1019)
            idx = r.data.find(search, r.pos)
            if idx >= 0:
                r.pos = idx
            else:
                raise ValueError("cannot find tag 0x1019 after firm_array")

        elif tag == 0x1019:
            r.skip_dynarrb()

        elif tag == 0x101A:
            state.corporations = parse_corporations(r, state)

        elif tag == 0x101B:
            state.towns = parse_towns(r, state)

        elif tag == 0x101C:
            # persons: short + dynarrb
            r.read_short()
            r.skip_dynarrb()

        elif tag == 0x101D:
            r.skip_dynarr()


# ---------------------------------------------------------------------------
# Top-level parser
# ---------------------------------------------------------------------------

debug = False

def parse_sav(path: Path) -> SaveState:
    data = path.read_bytes()
    r = BinaryReader(data)
    state = SaveState()

    # 1. Header: prefixed blob (expect 0x6D bytes)
    state.header = parse_header(r)

    # 2. Version tag (write_short — no prefix)
    state.version_tag = r.read_short()
    state.is_design_mode = (state.version_tag == -100)

    # 3. g_app: prefixed blob (expect 0x2E1 bytes)
    r.skip_blob()

    # 4. Section groups — order depends on mode
    if state.is_design_mode:
        parse_group_a(r, state)
        parse_group_b(r, state)
    else:
        parse_group_b(r, state)
        parse_group_a(r, state)

    # 5. Always Group C last
    parse_group_c(r, state)

    return state


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_state(state: SaveState) -> None:
    h = state.header
    print(f"=== Save Header ===")
    print(f"  Scenario: {h.scenario_name} (id={h.scenario_id})")
    print(f"  Corporation: {h.corp_name}")
    print(f"  Day serial: {h.day_serial}")
    print(f"  Years played: {h.years_played}")
    print(f"  Scores: {h.score1}, {h.score2}")
    print(f"  Wealth: {h.wealth:.2f}")
    print(f"  Net worth: {h.net_worth:.2f}")
    print(f"  AI type: {h.ai_type}")
    print()
    print(f"=== Format ===")
    print(f"  Version tag: {state.version_tag} ({'design' if state.is_design_mode else 'normal'})")
    print(f"  Products: {state.num_products}, Classes: {state.num_classes}")
    print(f"  Corp slots: {state.num_corp_slots}")
    print(f"  Sections parsed: {[f'0x{t:04X}' for t in state.sections_seen]}")
    print()

    if state.game_date.raw:
        gd = state.game_date
        print(f"=== Game Date ===")
        print(f"  Day serial: {gd.day_serial}")
        print(f"  Year: {gd.year}, Month: {gd.month}, Day: {gd.day}")
        print()

    if state.corporations:
        print(f"=== Corporations ({len(state.corporations)}) ===")
        type_names = {1: "Player", 2: "Hired", 3: "AI", 4: "Government"}
        for c in state.corporations:
            tname = type_names.get(c.corp_type, f"type={c.corp_type}")
            print(f"  [{c.slot}] {c.name} ({tname}) cash={c.cash:.2f} nw={c.net_worth:.2f}")
        print()

    if state.towns:
        print(f"=== Towns ({len(state.towns)}) ===")
        for t in state.towns:
            gnp_total = t.population * t.gnp_per_capita
            print(f"  [{t.index}] {t.name}")
            print(f"       pop={t.population:,.0f}  GNP/cap={t.gnp_per_capita:,.0f}  GNP={gnp_total:,.0f}")
            print(f"       unemp={t.unemployment:.1f}%  labor_cost={t.labor_cost:.0f}  labor_qual={t.labor_quality:.0f}")
            print(f"       consumer={t.consumer_spending:.0f}  econ_climate={5 - t.econ_climate}")
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse Capitalism Plus .SAV file")
    ap.add_argument("sav_file", type=Path, help="Path to .SAV file")
    ap.add_argument("--compare", action="store_true", help="Compare against sim (NYI)")
    ap.add_argument("--debug", action="store_true", help="Print parse offsets")
    args = ap.parse_args(argv)

    if not args.sav_file.exists():
        print(f"SAV file not found: {args.sav_file}", file=sys.stderr)
        return 1

    global debug
    debug = args.debug
    try:
        state = parse_sav(args.sav_file)
    except (ValueError, EOFError, struct.error) as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    print_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
