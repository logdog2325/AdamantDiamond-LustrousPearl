"""Pokémon from Unova (Rowan's sixth question, PFLAG_UNOVA; the user 2026-11-23, notes/DECISIONS.md; notes/UNOVA.md): the
build's half. The plan is data/unova.json, its slots and teams b2tools/unova.py (checked by `python3 b2tools/unova.py
--check`); the game's half is the decomp's src/pearlb2/resident/unova.c. List this patch after sinnoh_encounters,
pearl_shops, pearl_trainers, fairy, sinnoh_pokedex and wild (it reads what they wrote):

- a/1/2/7: one file appended after the 318 tables (UNOVA_FILE): the slot edits by table (u16 start[184], then 6-byte
  edits {u8 group | 0x80 late, u8 slot, u16 own, u16 new}) and the HABITAT list's pages with the Gen 5 Pokémon
  (u32 offsets, then a/2/9/6's pages, each with its place's Gen 5 Pokémon after Sinnoh's);
- a/0/9/2: the Unova parties of the Gym Leaders, the Elite Four and Cynthia (unova.teams), appended: the same record
  (a/0/9/1: class, size, kind of party), the same levels, difficulty and held items, four moves each;
- a/1/7/6: the AREA page of every Gen 5 Pokémon the option places (its places with the option on and after the
  Champion; resident/unova.c shows "area unknown" without the option, and before the Champion for the other version's
  side of a pair);
- a/2/8/2 list file 78 (shop 72): Veilstone Dept. Store 2F's vitamins (list 11's) and the eight stones the Unova families
  need (Sun, Moon, Shiny, Dusk, Fire, Water, Thunder, Leaf); the clerk's script opens it with the option on
  (src/include/pearl_story.inc pl_PokeMartSpecial);
- apply_code: gPearlB2Unova (the flag, the file, the trainers, the late species) in the resident pool.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import version  # noqa: E402

ARC_ENC, ARC_PARTY, ARC_HABITAT, ARC_HLIST, ARC_SHOP, ARC_SHOP_COUNT = 127, 92, 176, 296, 282, 283
FIRST_TABLE, TABLES = 135, 183                  # sinnoh_encounters: a/1/2/7 135 + Pearl file N
UNOVA_FILE = FIRST_TABLE + TABLES               # 318: the edits and pages (appended after the tables)
GROUP = {'grass': 0, 'surf': 1, 'super': 2, 'good': 3}
LATE = 0x80
KIND_BIT = {'grass': 0x01, 'surf': 0x08, 'super': 0x20, 'good': 0x20}   # the AREA page's walking / surfing / fishing
HABITAT_SIZE, SEASON_SIZE, NREC = 345, 86, 85
HLIST_MAX = 30
SHOP_FROM, SHOP_UNOVA = 11, 72                  # Veilstone 2F's vitamins clerk -> shop 72 (list file 78, empty in Black 2)
STONES = ('ITEM_SUN_STONE', 'ITEM_MOON_STONE', 'ITEM_SHINY_STONE', 'ITEM_DUSK_STONE', 'ITEM_FIRE_STONE',
          'ITEM_WATER_STONE', 'ITEM_THUNDERSTONE', 'ITEM_LEAF_STONE')
STATE = {}
CONSTANTS = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'include', 'generated', 'constants')


def plan_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location('unova_plan', os.path.join(ROOT, 'b2tools', 'unova.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _patch_module(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f'unova_{name}', os.path.join(HERE, f'{name}.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def constants(kind):
    import re
    return {k: int(v) for k, v in re.findall(r'#define\s+(\w+)\s+(\d+)', open(os.path.join(CONSTANTS, f'{kind}.h')).read())}


def flag_id():
    import re
    p = os.path.join(ROOT, 'src', 'include', 'platinum' if version.PLATINUM else '', 'pearl.h')
    m = re.search(r'^#define\s+PFLAG_UNOVA\s+(\d+)', open(p).read(), re.M)
    assert m, f'PFLAG_UNOVA missing from {p} (b2tools/pearl_ids.py)'
    return int(m.group(1))


# ---- the slot edits ------------------------------------------------------------------------------------------------
def edit_blob(U):
    """(index + edits bytes, {a/1/2/7 file: [edit]}, the summary)."""
    es, notes = U.edits(version.VERSION)
    bad = [n for n in notes if not n.startswith('(fewer)')]
    assert not bad, f'unova: the plan has findings ({len(bad)}): {bad[:3]}'
    by = {}
    for e in es:
        by.setdefault(FIRST_TABLE + e['n'], []).append(e)
    index, rows = [], b''
    for f in range(FIRST_TABLE, FIRST_TABLE + TABLES):
        index.append(len(rows) // 6)
        for e in sorted(by.get(f, []), key=lambda e: (e['late'], GROUP[e['group']], e['slot'])):
            rows += struct.pack('<BBHH', GROUP[e['group']] | (LATE if e['late'] else 0), e['slot'], e['own'], e['new'])
    index.append(len(rows) // 6)
    assert max(b - a for a, b in zip(index, index[1:])) <= 48, 'resident/unova.c UNOVA_MAX_EDITS'
    head = struct.pack(f'<{TABLES + 1}H', *index)
    return head, rows, by, f'{len(es)} edits ({sum(1 for e in es if e["late"])} after the Champion) in {len(by)} tables'


# ---- the Pokédex ---------------------------------------------------------------------------------------------------
def unova_cells(files, by, tm, ztab, slot_of):
    """{species: [bits per habitat index]} of the Gen 5 Pokémon the edits place (with the late ones)."""
    import zoneheaders
    headers, _ = zoneheaders.load(files)
    hab = {}
    for z, h in enumerate(headers):
        f = h['encounters']
        if f not in by or z >= len(ztab) or ztab[z] == 0xFF:
            continue
        k = slot_of[ztab[z]]
        for e in by[f]:
            sid = e['new'] & 0x7FF
            if 494 <= sid <= 649:
                hab.setdefault(sid, [0] * NREC)[k] |= KIND_BIT[e['group']]
    return hab


def habitat(files, by):
    """a/1/7/6 for the Gen 5 Pokémon and the HABITAT list's pages with them: (pages blob, summary)."""
    import narcio
    sp = _patch_module('sinnoh_pokedex')
    tm = sp._tm()
    f21 = tm.read_file21(files)
    recs, ztab = f21['records'], f21['zone_table']
    rzones = [r[0] for r in recs]
    locs = tm.locations()
    locs = locs + [tm.dummy_record(locs)] * (NREC - len(locs))
    zb = sp.zone_bits(files, ztab)
    wild_hab, slot_of = sp.place_bits(zb, ztab, rzones)
    hab = unova_cells(files, by, tm, ztab, slot_of)
    # the AREA page
    entries = narcio.load(files, ARC_HABITAT)
    for sid, cells in hab.items():
        d = bytearray(entries[sid - 1])
        assert len(d) == HABITAT_SIZE, f'a/1/7/6 {sid - 1}: {len(d)} B'
        d[0] = 1
        for s in range(4):
            d[1 + SEASON_SIZE * s] = 0
            d[2 + SEASON_SIZE * s:2 + SEASON_SIZE * s + NREC] = bytes(cells)
        entries[sid - 1] = bytes(d)
    narcio.save(files, ARC_HABITAT, entries)
    # the HABITAT list: Sinnoh's pages as sinnoh_pokedex wrote them, each with its place's Gen 5 Pokémon after
    pages_now = narcio.load(files, ARC_HLIST)
    _, places, groups, _ = sp.hlist_pages(tm, locs, wild_hab, slot_of)
    want = {}
    for p, g in enumerate(places):
        want[p] = {}
        for sid in sorted(hab):
            b = 0
            for k in groups[g]:
                b |= hab[sid][k]
            if b:
                want[p][sid] = b
    pages_of = {}
    for p, w in want.items():
        for sid in w:
            pages_of[sid] = pages_of.get(sid, 0) + 1
    out, over, added, dropped = [], [], 0, []
    for p, g in enumerate(places):
        page = pages_now[p]
        count = struct.unpack_from('<H', page, 8)[0]
        native = page[10:10 + 28 * count]
        w = dict(want[p])
        # a page holds 30: the Gen 5 Pokémon other pages list too go first, those on the most pages first (Mt. Coronet)
        while count + len(w) > HLIST_MAX:
            cands = [sid for sid in w if pages_of[sid] > 1]
            if not cands:
                over.append((g, count + len(w)))
                break
            sid = max(cands, key=lambda x: (pages_of[x], x))
            del w[sid]
            pages_of[sid] -= 1
            dropped.append(f'{g}: {sid}')
        extra = [struct.pack('<H', sid) + bytes([int(bool(b & 0x07)), int(bool(b & 0x18)), int(bool(b & 0x60))]) * 4
                 + bytes(14) for sid, b in sorted(w.items())]
        added += len(extra)
        out.append(page[:8] + struct.pack('<H', count + len(extra)) + native + b''.join(extra))
    assert not over, f'HABITAT list pages over {HLIST_MAX} Pokémon with Unova: {over}'
    STATE['hlist_dropped'] = dropped
    offsets, blob = [], b''
    base = 4 * (len(out) + 1)
    for pg in out:
        offsets.append(base + len(blob))
        blob += pg + bytes(-len(pg) % 4)
    offsets.append(base + len(blob))
    return (struct.pack(f'<{len(offsets)}I', *offsets) + blob, len(out),
            f'AREA page: {len(hab)} Gen 5 Pokémon; HABITAT list: {len(out)} pages, {added} Gen 5 entries'
            + (f' (full pages leave out ones listed elsewhere: {dropped})' if dropped else ''))


# ---- the teams -----------------------------------------------------------------------------------------------------
def pack_party(party, sp, it, mv):
    from struct import Struct
    MON = Struct('<4BHH')                       # the decomp's tools/data/trainer_data.py MON
    has_items = {'item' in m for m in party}
    has_moves = {'moves' in m for m in party}
    assert len(has_items) == 1 and len(has_moves) == 1
    out = b''
    for m in party:
        out += MON.pack(m['difficulty'], m['gender'] | m['ability'] << 4, m['level'], 0, sp[m['species']], m['form'])
        if True in has_items:
            out += struct.pack('<H', it[m['item']])
        if True in has_moves:
            mvs = [mv[x] for x in m['moves']]
            out += struct.pack('<4H', *mvs, *[0] * (4 - len(mvs)))
    return out


def teams(files, U):
    """Append the Unova parties to a/0/9/2: ([(Black 2 trainer, party file)], summary)."""
    import narcio
    ids = json.load(open(version.data_path('pearl_story_ids.json')))['trainers']
    sp, it, mv = constants('species'), constants('items'), constants('moves')
    parties = narcio.load(files, ARC_PARTY)
    pairs, names = [], []
    mine = [pack_party(new, sp, it, mv) for t, (old, new) in U.teams(version.VERSION).items()]
    first = len(parties)
    if parties[-len(mine):] == mine:            # (a quick non-clean build: they are there)
        first -= len(mine)
    for t, (old, new) in U.teams(version.VERSION).items():
        b2 = ids[str(t)]['b2']
        assert parties[b2] == pack_party(old, sp, it, mv), f'a/0/9/2 {b2} is not Pearl trainer {t}\'s party'
        pairs.append((b2, first + len(pairs)))
        names.append(U.plan()['teams'][t]['name'])
    narcio.save(files, ARC_PARTY, parties[:first] + mine)
    return pairs, f'{len(pairs)} Unova parties at a/0/9/2 {first}-{first + len(pairs) - 1} ({", ".join(names)})'


# ---- the stones ----------------------------------------------------------------------------------------------------
def shop(files):
    import narcio
    it = constants('items')
    lists, counts = narcio.load(files, ARC_SHOP), narcio.load(files, ARC_SHOP_COUNT)
    src = lists[SHOP_FROM + 6]
    n = counts[0][SHOP_FROM + 6]
    items = list(struct.unpack(f'<{n}H', src[:2 * n])) + [it[s] for s in STONES]
    lists[SHOP_UNOVA + 6] = struct.pack(f'<{len(items)}H', *items)
    c = bytearray(counts[0])
    c[SHOP_UNOVA + 6] = len(items)
    counts[0] = bytes(c)
    narcio.save(files, ARC_SHOP, lists)
    narcio.save(files, ARC_SHOP_COUNT, counts)
    return f'shop {SHOP_UNOVA} (list file {SHOP_UNOVA + 6}): list {SHOP_FROM}\'s {n} + {len(STONES)} stones'


def late_species(U):
    """Species only the late edits place (the other version's side of a pair): their AREA page waits for the Champion."""
    es, _ = U.edits(version.VERSION)
    early = {e['new'] & 0x7FF for e in es if not e['late']}
    return sorted({e['new'] & 0x7FF for e in es if e['late']} - early)


def apply(files):
    import narcio
    U = plan_module()
    head, rows, by, s1 = edit_blob(U)
    pages, npages, s2 = habitat(files, by)
    edits_off = len(head)
    pages_off = (edits_off + len(rows) + 3) & ~3
    data = head + rows + bytes(pages_off - edits_off - len(rows)) + pages
    enc = narcio.load(files, ARC_ENC)
    assert len(enc) in (UNOVA_FILE, UNOVA_FILE + 1), f'a/1/2/7 has {len(enc)} files (expected {UNOVA_FILE})'
    enc = enc[:UNOVA_FILE] + [data]
    narcio.save(files, ARC_ENC, enc)
    pairs, s3 = teams(files, U)
    s4 = shop(files)
    late = late_species(U)
    cfg = struct.pack('<8H2I', flag_id(), ARC_ENC, UNOVA_FILE, FIRST_TABLE, TABLES, npages, len(pairs), len(late),
                      edits_off, pages_off)
    cfg += b''.join(struct.pack('<HH', a, b) for a, b in pairs) + struct.pack(f'<{len(late)}H', *late)
    STATE['blob'] = cfg + bytes(-len(cfg) % 4)
    return (f'unova: flag {flag_id()}; a/1/2/7 {UNOVA_FILE} {len(data)} B: {s1}; {s2}; {s3}; {s4}; '
            f'{len(late)} species after the Champion')


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2Unova', code)
    if slot is None:
        return 'unova: no gPearlB2Unova in this decomp: nothing installed'
    blob = STATE['blob']
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:
        resident.write(code, old, blob)
        base = old
    else:
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    return f'unova: config {len(blob)} B at {base:#x} (gPearlB2Unova {slot:#x})'
