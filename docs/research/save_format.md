# Capitalism Plus Save File Format

Reverse-engineered from `load_game_file` (0x1dbf6) and the section-tagged
loader chain in `capplus_decompiled.c`.

## File Identity

A save game lives in the **GAMESET** folder under the game root.  Each scenario
or save has a base name (e.g. `1STD`) and a set of companion files:

| Extension | Purpose                                  |
|-----------|------------------------------------------|
| `.SET`    | Scenario definition (dBASE III tables)    |
| `.II2`    | Product resource archive (graphics etc.)  |
| `.II`     | Save stream v1 (sequential, no tags)      |
| `.IP`     | Unknown (small)                           |
| `.PLA`    | Player save (single-player)               |
| `.PLP`    | Player save (multiplayer variant)         |
| `.PLO`    | Player options / overlay                  |
| `.PIC`    | Scenario preview picture                  |

The save stream loaded by `load_game_file` uses the section-tagged format
described below. Active save games are written when the player saves.

### SET file format

The `.SET` file is a custom archive of **dBASE III** tables:
- 2-byte section count (LE int16)
- For each section: 9-byte name (null-padded) + 4-byte offset (LE int32)
- Each section at its offset IS a standard dBASE III file (.dbf)

Sections: RICH, ITEMCLAS, FIRMJOB, JOB, RAW, GROUP, PERSON, METHOD,
FARMPROD, HEADER, TOWN, FIRM, ITEMPAE, ITEM, FARMLIVE, FARMCROP.

### II2 file format

The `.II2` file is a product-indexed resource archive:
- 2-byte product count (LE int16)
- For each product: 9-byte name + 4-byte data offset
- Product data blocks at those offsets (~14KB each, likely graphics)

## I/O Primitives

All values are **little-endian** (Watcom x86).

| Primitive       | C function    | Format                  |
|-----------------|---------------|-------------------------|
| `write_short`   | `0x0008f698`  | 2 bytes, int16 LE       |
| `read_short`    | `0x0008f709`  | 2 bytes → int16 LE      |
| `write_int32`   | `0x0008f844`  | 4 bytes, int32 LE       |
| `read_int32`    | `0x0008f8ac`  | 4 bytes → int32 LE      |
| `write_blob`    | `0x0008f505`  | **2-byte LE size prefix** + N bytes |
| `read_blob`     | `0x0008f58f`  | **2-byte LE size prefix** + N bytes |
| `save_dynarr`   | `0x0008de82`  | 0x1D hdr + data         |
| `load_dynarr`   | `0x0008decb`  | 0x1D hdr + data         |
| `save_dynarrb`  | `0x0008e350`  | 0x2C hdr + data + free  |
| `load_dynarrb`  | `0x0008e3b5`  | 0x2C hdr + data + free  |

### Blob Size Prefix Protocol

The game's file I/O layer has a **chunked mode** (flag at offset +0x2A in the
file object, set to 1 for save files).  When active, `write_blob` and
`read_blob` prepend/read a **2-byte LE size prefix** before the actual data.
`write_short`, `read_short`, `write_int32`, `read_int32` do **NOT** get
prefixes — they are raw.

**Large blob overflow:** For blobs > 65535 bytes, the 2-byte prefix truncates
to the low 16 bits.  The reader detects `prefix == 0` (or `prefix > requested`)
and falls back to the caller's requested size.  Example: the town_subsys grid
blob (240×198×8 = 380,160 bytes) writes prefix `0x0000`; the reader uses the
caller's `w*h*8` parameter.

### DynArr (simple) — 0x1D header

```
offset  size  field
0x00    4     capacity (max_count)
0x04    4     growth
0x08    4     current_idx
0x0C    4     count
0x10    4     elem_size
0x14    4     (reserved)
0x18    1     (flags)
0x19    4     data_ptr (ignored on load; reallocated)
```
Followed by `count * elem_size` bytes of element data.

### DynArrB (with free list) — 0x2C header

Same as DynArr plus:
```
0x1D    3     (padding/reserved)
0x20    4     free_list_ptr (ignored on load)
0x24    4     free_list_capacity  ← used for I/O size!
0x28    4     free_list_count
```
Followed by `count * elem_size` bytes of element data,
then **`free_list_capacity * 4`** bytes of free-list indices.
(Note: the save/load functions use offset 0x24 (capacity), NOT 0x28 (count),
for the free-list blob size.)

## Top-Level Structure

```
1.  Header blob:  prefixed 0x6D (109) bytes — save slot metadata
2.  Version tag:  read_short (no prefix) → must be 100 (normal) or -100 (design mode)
3.  g_app blob:   prefixed 0x2E1 (737) bytes — application/UI state
4.  Section groups (tagged):
      - Group A: tags 0x1001–0x1008 (global scalars)
      - Group B: tags 0x100B–0x1011 (catalog arrays)
      - Group C: tags 0x1015–0x101D (entity arrays)
    Group order depends on flags:
      normal game:   B, A, C
      design mode:   A, B, C
    Then always group C.
```

## Save Slot Header (0x6D = 109 bytes)

Located at offset +0x0D in the slot struct:
- `+0x0D` (2 bytes): game speed / scenario id
- `+0x0F` (1 byte): flag byte
- `+0x10` (4 bytes): day_serial (int32)
- `+0x14` (30 bytes): corporation name (null-terminated string)
- `+0x33` (1 byte): AI type
- `+0x34` (4 bytes): years played
- `+0x38` (2 bytes): score field 1
- `+0x3A` (2 bytes): score field 2
- `+0x3C` (4 bytes): float — wealth or revenue
- `+0x40` (4 bytes): float — net worth
- `+0x44` (30+ bytes): scenario name

## Section Group A — Global Scalars (tags 0x1001–0x1008)

| Tag    | Global            | Address      | Loader          | Size/Format |
|--------|-------------------|--------------|-----------------|-------------|
| 0x1001 | g_cfg             | `0xb1c7d`   | read_int32 + op | int32 read, then config restore |
| 0x1002 | interest_rate     | `0xb23d9`   | read_blob       | 0x2C (44) bytes |
| 0x1003 | DAT_000b2409      | `0xb2409`   | complex         | short+byte+4-byte blob+dynarr+short |
| 0x1004 | DAT_000b1c5c      | `0xb1c5c`   | special         | eec0-style loader |
| 0x1005 | g_game_date       | `0xb255c`   | read_blob       | 0x41 (65) bytes |
| 0x1006 | town_subsys       | `0xb259d`   | complex         | town grid data |
| 0x1007 | g_window          | `0xb2613`   | complex         | DAT_000b267e array(blob(0xC)+short) + blob(0x54) |
| 0x1008 | DAT_000b2452      | `0xb2452`   | load_dynarr     | 0x1D hdr + data |

## Section Group B — Catalog Arrays (tags 0x100B–0x1011)

| Tag    | Global            | Address      | Loader          | Size/Format |
|--------|-------------------|--------------|-----------------|-------------|
| 0x100B | product_system    | `0xb182b`   | special         | product catalog |
| 0x100C | firm_templates    | `0xb1990`   | special         | firm type templates |
| 0x100D | counters          | `0xb1a1d`   | special         | global counters array |
| 0x100E | (no address)      | —            | FUN_0001edc8    | unknown small block |
| 0x100F | person_types      | `0xb1b87`   | special         | person type defs |
| 0x1010 | DAT_000b1c53      | `0xb1c53`   | special         | unknown |
| 0x1011 | DAT_000b1c2f      | `0xb1c2f`   | special         | via FUN_000748fd |

## Section Group C — Entity Arrays (tags 0x1015–0x101D)

| Tag    | Global            | Address      | Loader           | Size/Format |
|--------|-------------------|--------------|------------------|-------------|
| 0x1015 | g_item_array      | `0xb1888`   | dynarrb + extras | items + 3 shorts |
| 0x1016 | DAT_000b190f      | `0xb190f`   | save_dynarrb     | product link data |
| 0x1017 | g_job_array       | `0xb1960`   | per-element      | short count + short next_id + per-job(type+0x24 hdr + vtable load) |
| 0x1018 | g_firm_array      | `0xb19bd`   | per-element      | 3 shorts + per-firm(0x17D base + conditional + vtable load) |
| 0x1019 | DAT_000b19ed      | `0xb19ed`   | save_dynarrb     | another array |
| 0x101A | g_firms           | `0xb1a7b`   | per-element      | 4 shorts + per-corp(0x83B base + ptr data + vtable load) |
| 0x101B | town_manager      | `0xb1ace`   | per-element      | 2 shorts + int32 + short count + per-town(0x173 + 2 arrays) |
| 0x101C | persons           | `0xb1bce`   | per-element      | short + dynarrb |
| 0x101D | DAT_000b1bfc      | `0xb1bfc`   | load_dynarr      | 0x1D hdr + data |

## Key Structure Sizes

| Structure       | Base size | Notes |
|-----------------|-----------|-------|
| Save header     | 0x6D (109)| Slot metadata |
| g_app           | 0x2E1 (737)| Application state |
| interest_rate   | 0x2C (44) | Interest rate object |
| g_game_date     | 0x41 (65) | Calendar/date state |
| g_window        | 0x54 (84) | Window/UI state |
| Town            | 0x173 (371)| Per-town base, plus variable arrays |
| Corporation     | 0x83B (2107)| Per-corp base, plus ptr at +0xD2 (DAT_000b199c*4 bytes) |
| Firm (map)      | 0x17D (381)| Per-firm on map |
| Job             | 0x24 (36) | Per-job base header, plus type-specific extension |

## Corporation Load Detail

Each corporation in g_firms:
1. Read type short (0 = empty slot → skip)
2. Create corp of that type (types 1-3: FUN_0002ccd0, type 4: FUN_0003555c)
3. Read blob(0x83B) — base struct (prefixed)
4. De-obfuscate name: bytes at +0x32..+0x45 XOR'd with `i*-2`
5. Read blob(DAT_000b199c * 4) — slot data at +0xD2 (prefixed)
6. Read blob(0x214) — strategy object at +0x17E (prefixed)
7. Call vtable[0x1C] for type-specific load (competitor_load)

Vtable pointers (at offset 0x83B in corp object):
- Types 1-3: vtable at FUN_0002d804 (data address)
- Type 4 (Government): vtable at FUN_0003553c (data address)

All corp types have total object size 0x88C (FUN_00034d34 returns 0x88C for
types 1-4). Type-specific data = 0x88C - 0x83F = **0x4D (77) bytes** at
offset 0x83F, saved/loaded by FUN_0001f70a (save) / FUN_0001f74e (load).

### Corporation Base Struct Fields (0x83B bytes)

| Offset | Type  | Field           | Notes |
|--------|-------|-----------------|-------|
| 0x00   | short | corp_type       | 1=Player, 2=Hired, 3=AI, 4=Government |
| 0x02   | char[48] | name         | Null-terminated ASCII |
| 0x32   | byte[20] | obfuscated_name | XOR'd with i*2 (encode) / i*-2 (decode) |
| 0xD2   | ptr   | slot_data       | Points to DAT_000b199c * 4 bytes |
| 0x17E  | ptr   | strategy        | Points to 0x214-byte strategy object |
| 0x186  | float | cash            | Confirmed: group_post_revenue uses +0x186 |
| 0x18A  | float | net_worth       | Confirmed: header+0x3C copies from +0x18A |

## Town Load Detail

Each town:
1. Allocate 0x173 bytes
2. Read 0x173 bytes (base struct)
3. Read `DAT_000b182f * 2` bytes into pointer at +0x4B (product demands)
4. Read `DAT_000b199c * 0x1A` bytes into pointer at +0x4F (per-corp town data)

### Town Base Struct Fields (0x173 bytes)

Complete mapping confirmed from init (FUN_0004b0be), display (FUN_0004bf8a),
population growth (FUN_0004b4de), and ring init (FUN_0004b2f6).

| Offset | Size | Type       | Field              | Notes |
|--------|------|------------|--------------------|-------|
| 0x00   | 2    | short      | town_id            | Index into SET TOWN table |
| 0x02   | 21   | char[21]   | name               | Null-terminated, space-padded |
| 0x17   | 2    | short      | x                  | Map column coordinate |
| 0x19   | 2    | short      | y                  | Map row coordinate |
| 0x1B   | 2    | short      | stagger_slot       | 1-based monthly processing order |
| 0x1D   | 1    | byte       | level_lock         | 0 = can level up; nonzero = locked |
| 0x1E   | 2    | short      | level              | Computed: level² × 160000 ≤ population |
| 0x20   | 2    | short      | env_factor[0]      | Random −3..+3 (init: FUN_0004b160) |
| 0x22   | 2    | short      | env_factor[1]      | Random −3..+3 |
| 0x24   | 2    | short      | env_factor[2]      | Random −3..+3 |
| 0x26   | 2    | short      | prev_env_factor[0] | Copy of env_factor at period start |
| 0x28   | 2    | short      | prev_env_factor[1] | Copy of env_factor at period start |
| 0x2A   | 2    | short      | prev_env_factor[2] | Copy of env_factor at period start |
| 0x2C   | 1    | byte       | tier_marker        | 3 in normal mode; from SET in design |
| 0x2D   | 4    | float      | population         | "City Population" |
| 0x31   | 4    | float      | gnp_per_capita     | 20000.0 at game start (normal) |
| 0x35   | 4    | float      | (unknown)          | 0.0 at game start |
| 0x39   | 2    | short      | econ_climate       | Displayed as 5 − value; baseline 2 |
| 0x3B   | 4    | float      | labor_cost         | Baseline 100.0 |
| 0x3F   | 4    | float      | consumer_spending  | Baseline 100.0 |
| 0x43   | 4    | float      | labor_quality      | Baseline 100.0 |
| 0x47   | 4    | float      | unemployment       | Percentage, e.g. 2.02 |
| 0x4B   | 4    | ptr        | product_demands    | Saved separately: num_products × 2 |
| 0x4F   | 4    | ptr        | per_corp_data      | Saved separately: num_corps × 0x1A |
| 0x53   | 48   | float[12]  | pop_ring           | Monthly population snapshots |
| 0x83   | 48   | float[12]  | gnp_ring           | Monthly GNP (pop × gnp_pc) |
| 0xB3   | 48   | float[12]  | gnp_ring2          | Second GNP metric |
| 0xE3   | 48   | float[12]  | pop_growth_ring    | Population growth chart data |
| 0x113  | 48   | float[12]  | gnp_growth_ring    | GNP growth chart data |
| 0x143  | 48   | float[12]  | unemployment_ring  | Monthly unemployment history |
|        |      |            |                    | **Total: 0x173 (371) bytes** |

## Verification Approach

Save-to-save comparison (avoids RNG seed problem):
1. Parse save A (earlier) and save B (later) from the same game
2. Load save A's state into the sim (towns, corps, calendar, economy)
3. Advance sim from A's day_serial to B's day_serial
4. Compare sim's output against B's parsed values
5. Key comparables: town population/GNP/unemployment/indices,
   corporation cash/net_worth, calendar date
