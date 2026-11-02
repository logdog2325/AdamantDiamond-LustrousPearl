"""Pearl's honey trees, daily swarm, Feebas and the Great Marsh's daily Pokémon (notes/ENCOUNTERS.md "Honey trees, swarms,
Feebas, the Great Marsh"). List it after sinnoh_encounters.

The code is the decomp's src/pearlb2/resident/wild.c (its comments have Pearl's rules). This patch gives it gPearlB2Wild
(NULL: Black 2's behaviour), read from the dump and data/sinnoh_world.json:
- the dump's arc/encdata_ex (pokeplatinum res/field/encounters/encdata_ex.order): member 0 Feebas, 1 its tiles (Pearl's
  count of chunks, tiles per chunk, then u16 z * 32 + x), 2-4 Diamond's and 5-7 Pearl's honey groups, 9 / 10 the Great
  Marsh's day with / without the National Dex;
- the honey trees' zones (pokediamond ov05_021FC650, the same order as pearl_events.HONEY_TREE_MAPS);
- Pearl's 28 swarm zones (pokediamond ov06_02251340) and each file's two swarm species;
- flag 2400, Pearl's National Dex here (DECISIONS 2026-10-26).
Diamond's version: HONEY_MEMBERS (its encounter files have its own swarm species).

And Pearl's berry patches (decomp src/pearlb2/resident/berry.c, notes/ENCOUNTERS.md "Berry patches"), gPearlB2Berry:
- the dump's itemtool/itemdata/nuts_data.narc: each Berry's hours a stage, moisture drain, base yield;
- Pearl's new game (overlay 52, offset 0x218 in the dump: 118 x (item, yield), found by its shape: pokeplatinum game_start.c
  sBerryInitTable is the same kind of table with Platinum's values);
- the pictures: one a/0/4/8 sheet each, appended (no record in the object table: the C reads the template's), from
  data/mmodel/mmodel.narc (the sprout seed00_a, then seedNN_a/b/c: growing, blooming, fruit, first sway frame) and
  fldeff.narc 77/76/75 (the soil rings: dry, damp, wet). Layout: 0 blank, 1-3 the ring alone, 4-6 the sprout, then
  (Berry * 3 + stage) * 3 + moisture, each ring under the plant (Pearl draws the ring flat on the ground; the
  picture is its ring on the billboard, flattened).
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import version  # noqa: E402

HONEY_MEMBERS = {'pearl': (5, 6, 7), 'diamond': (2, 3, 4)}[version.VERSION]   # ov05_021FC644 in each dump (notes/DIAMOND.md 1.4)
FEEBAS_SPECIES, FEEBAS_TILES = 0, 1
MARSH_NATIONAL, MARSH_LOCAL = 9, 10
HONEY_MAPS = (0x15B, 0x15D, 0x15E, 0x161, 0x162, 0x164, 0x16A, 0x16B, 0x16E, 0x16F, 0x173, 0x175, 0x17C, 0x17E,
              0x184, 0x188, 0x18B, 0xC8, 0xCA, 0xCC, 0x100)
SWARM_MAPS = (0x156, 0x157, 0x158, 0x15E, 0x161, 0x162, 0x164, 0x175, 0x17C, 0x17E, 0x17F, 0x181, 0x184, 0x188, 0x18B,
              0x18F, 0x190, 0x1D5, 0x193, 0x196, 0x197, 0x1D7, 0x138, 0x13B, 0x13E, 0xC8, 0xCB, 0xCC)
MARSH_NAMES = [f'MAP_GREAT_MARSH_AREA_{n}' for n in range(1, 7)]
FEEBAS_NAME = 'MAP_MOUNT_CORONET_B1F'
GAME_CLEAR_FLAG = 2400
BLOB_SIZE = 6 + 2 * 21 + 2 * 18 + 2 * 28 + 4 * 28 + 2 * 6 + 2 * 64 + 2 * 528
STATE = {}
BERRIES = 64
PATCHES = 118
FIRST_BERRY_ITEM = 149
INIT_OVERLAY, INIT_OFFSET = 52, 0x218
TEMPLATE_CODE = 208                              # a one-frame 32 x 32 billboard (Rowan's briefcase: its record only)
SPROUT_MMODEL = 95
# Pearl's Berries' mmodel files: seed01 96-98, then from 171 on three a Berry (checked by name, below)
GROUND_MODELS = (77, 76, 75)                     # dry, damp, wet (pokeplatinum berry_patch_effects.c: moisture 0, 1, 2)
FLOOR_ROW = 30                                   # the plant's foot in the 32 x 32 frame: where Black 2's people stand
RING_ROWS = 10                                   # Pearl's 16 x 16 ring, flattened: seen from the field's camera


def encdata_ex():
    import gen4rom
    return gen4rom.narc_members(gen4rom.Rom(os.path.join(ROOT, 'roms', 'pearl.nds')).read('arc/encdata_ex.narc'))


def _zones():
    world = json.load(open(os.path.join(ROOT, 'data', 'sinnoh_world.json')))
    out = {int(k): v['b2_zone'] for k, v in world['zones'].items()}
    by_name = {}
    for k, v in world['rooms']['zones'].items():
        out[int(k)] = v['b2_zone']
        by_name[v['name']] = v['b2_zone']
    return out, by_name


def table():
    """The gPearlB2Wild blob (resident/wild.c PearlB2Wild) and a summary."""
    import sinnoh_encounters as enc
    ex = encdata_ex()
    zones, by_name = _zones()
    pearl_zones = {z['id']: z for z in json.load(open(os.path.join(version.WORK, 'zones.json')))}
    u32s = lambda b: struct.unpack('<%dI' % (len(b) // 4), b)

    feebas = u32s(ex[FEEBAS_SPECIES])[0]
    chunks, *tiles_per = struct.unpack_from('<3I', ex[FEEBAS_TILES])
    assert chunks == 2 and sum(tiles_per) == 528, (chunks, tiles_per)
    tiles = struct.unpack_from('<528H', ex[FEEBAS_TILES], 12)
    honey = [u32s(ex[m]) for m in HONEY_MEMBERS]
    assert all(len(g) == 6 for g in honey)
    marsh = [u32s(ex[MARSH_NATIONAL]), u32s(ex[MARSH_LOCAL])]
    assert all(len(g) == 32 for g in marsh)

    honey_zones = [zones[m] for m in HONEY_MAPS]
    swarm_zones, swarm_species = [], []
    for m in SWARM_MAPS:
        e = json.load(open(os.path.join(version.WORK, 'encounters', f'{pearl_zones[m]["encounters"]:03d}.json')))
        swarm_species.append([enc.species_id(s) for s in e['swarms']])
        swarm_zones.append(zones.get(m, 0xFFFF))
    marsh_zones = [by_name[n] for n in MARSH_NAMES]

    blob = struct.pack('<3H', GAME_CLEAR_FLAG, by_name[FEEBAS_NAME], feebas)
    blob += struct.pack('<21H', *honey_zones)
    for g in honey:
        blob += struct.pack('<6H', *g)
    blob += struct.pack('<28H', *swarm_zones)
    for pair in swarm_species:
        blob += struct.pack('<2H', *pair)
    blob += struct.pack('<6H', *marsh_zones)
    for g in marsh:
        blob += struct.pack('<32H', *g)
    blob += struct.pack('<528H', *tiles)
    assert len(blob) == BLOB_SIZE, len(blob)
    missing = [hex(m) for m, z in zip(SWARM_MAPS, swarm_zones) if z == 0xFFFF]
    return blob, (f'21 trees, 28 swarms ({"no zone: " + str(missing) if missing else "all with zones"}), Feebas zone '
                  f'{by_name[FEEBAS_NAME]}, marsh zones {marsh_zones}')


def _rom():
    import gen4rom
    return gen4rom.Rom(os.path.join(ROOT, 'roms', 'pearl.nds'))


def new_game_patches(rom):
    """[(Berry number, yield)] x 118 of Pearl's new game."""
    d = rom.data
    ovt = struct.unpack_from('<I', d, 0x50)[0]
    fid = struct.unpack_from('<I', d, ovt + 32 * INIT_OVERLAY + 24)[0]
    start, _ = rom.fat[fid]
    rows = [struct.unpack_from('<HH', d, start + INIT_OFFSET + 4 * i) for i in range(PATCHES)]
    assert all(FIRST_BERRY_ITEM <= it < FIRST_BERRY_ITEM + BERRIES and 1 <= y <= 5 for it, y in rows), rows[:4]
    return [(it - FIRST_BERRY_ITEM + 1, y) for it, y in rows]


def _texture(t, want=None):
    """(w, h, 4 bpp indices, 16 BGR555 colours) of a texture in a BTX0 / BMD0's TEX0."""
    import sprites
    t0 = t.find(b'TEX0')
    tex = t[t0:]
    pals = dict(sprites._dict(tex, struct.unpack_from('<I', tex, 0x34)[0]))
    paldata = struct.unpack_from('<I', tex, 0x38)[0]
    for name, ent in sprites._dict(tex, struct.unpack_from('<H', tex, 0xE)[0]):
        if want is not None and name != want:
            continue
        p = struct.unpack_from('<I', ent, 0)[0]
        fmt, w, h = p >> 26 & 7, 8 << (p >> 20 & 7), 8 << (p >> 23 & 7)
        assert fmt == 3, (name, fmt)
        off = struct.unpack_from('<I', tex, 0x14)[0] + ((p & 0xffff) << 3)
        pix = sprites.unpack4(tex[off:off + w * h // 2], w * h)
        po = paldata + (struct.unpack_from('<H', pals[name + '_pl'], 0)[0] << 3)
        n = min(16, (len(tex) - po) // 2)
        return w, h, pix, list(struct.unpack_from(f'<{n}H', tex, po)) + [0] * (16 - n)
    raise KeyError(want)


def _dist(a, b):
    return sum((((a >> s) & 31) - ((b >> s) & 31)) ** 2 for s in (0, 5, 10))


def _picture(plant, ring):
    """A 32 x 32 frame and its 16 colours: Pearl's ring flattened on the floor, the plant over it."""
    pal = [0]
    out = bytearray(32 * 32)

    def colour(c):
        if c in pal[1:]:
            return pal.index(c, 1)
        if len(pal) < 16:
            pal.append(c)
            return len(pal) - 1
        return min(range(1, 16), key=lambda i: _dist(pal[i], c))
    if plant:                                    # the plant's own colours first: they stay exact
        w, h, pix, cols = plant
        for v in sorted(set(pix)):
            if v:
                colour(cols[v])
    if ring:
        w, h, pix, cols = ring
        top = FLOOR_ROW + 2 - RING_ROWS
        for row in range(RING_ROWS):
            src = row * h // RING_ROWS
            for x in range(w):
                v = pix[src * w + x]
                if v:
                    out[(top + row) * 32 + 8 + x] = colour(cols[v])
    if plant:
        w, h, pix, cols = plant
        foot = max(i // w for i, v in enumerate(pix) if v)
        dy = FLOOR_ROW - foot
        for i, v in enumerate(pix):
            if v:
                y, x = i // w + dy, i % w + (32 - w) // 2
                if 0 <= y < 32:
                    out[y * 32 + x] = colour(cols[v])
    return bytes(out), pal + [0] * (16 - len(pal))


def berry_pictures(rom, template):
    """The sheets, in the C's order (resident/berry.c Patch_Picture)."""
    import gen4rom, sprites
    mm = gen4rom.narc_members(rom.read('data/mmodel/mmodel.narc'))
    fe = gen4rom.narc_members(rom.read('data/mmodel/fldeff.narc'))
    rings = [_texture(fe[m]) for m in GROUND_MODELS]
    def sheet(plant, ring):
        pix, pal = _picture(plant, ring)
        return sprites.btx_encode(template, [pix], pal)
    out = [sheet(None, None)]
    out += [sheet(None, r) for r in rings]
    sprout = _texture(mm[SPROUT_MMODEL], 'seed00_a.1')
    out += [sheet(sprout, r) for r in rings]
    for b in range(BERRIES):
        for k, stage in enumerate('abc'):
            name = f'seed{b + 1:02d}_{stage}.1'
            plant = _texture(mm[96 + k if b == 0 else 171 + (b - 1) * 3 + k], name)
            out += [sheet(plant, r) for r in rings]
    return out


def berry_table(rom, first_sheet):
    import gen4rom, sprites
    nuts = gen4rom.narc_members(rom.read('itemtool/itemdata/nuts_data.narc'))
    assert len(nuts) == BERRIES
    yields = [n[3] for n in nuts]                # pokeplatinum berry_data.h BerryData: size u16, firmness, base yield,
    hours = [n[4] for n in nuts]                 # stage duration, moisture drain
    drain = [n[5] for n in nuts]
    init = new_game_patches(rom)
    blob = struct.pack('<HH', sprites.obj_record(TEMPLATE_CODE), first_sheet)
    blob += bytes(hours) + bytes(drain) + bytes(yields)
    blob += bytes(b for b, _ in init) + bytes(y for _, y in init)
    return blob


def apply(files):
    import narcio, sprites
    STATE['blob'], STATE['summary'] = table()
    rom = _rom()
    table_ = sprites.ow_table(files)
    sheet, _ = sprites.ow_sheet_of(files, TEMPLATE_CODE, table_)
    sheets = narcio.load(files, sprites.ARC_OW_SHEETS)
    pics = berry_pictures(rom, sheets[sheet])
    if len(sheets) >= len(pics) and sheets[-len(pics)] == pics[0] and sheets[-1] == pics[-1]:
        first = len(sheets) - len(pics)          # a quick non-clean build: they are there
    else:
        first = len(sheets)
        sheets = list(sheets) + pics
        narcio.save(files, sprites.ARC_OW_SHEETS, sheets)
    STATE['berry'] = berry_table(rom, first)
    return f'wild: {STATE["summary"]}; {len(pics)} berry pictures, sheets {first}..{first + len(pics) - 1}'


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2Wild', code)
    if slot is None:
        return 'wild: no gPearlB2Wild in this decomp: nothing installed'
    blob = STATE['blob']
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:                                      # a quick non-clean build: the table is there, rewrite it in place
        resident.write(code, old, blob)
        base = old
    else:
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    out = f'wild: table {len(blob)} B at {base:#x} (gPearlB2Wild {slot:#x}); {STATE["summary"]}'
    slot = decomp.symbol('gPearlB2Berry', code)
    if slot is None:
        return out + '; no gPearlB2Berry in this decomp: no berry patches'
    blob = STATE['berry']
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:
        resident.write(code, old, blob)
        base = old
    else:
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    return out + f'; berries {len(blob)} B at {base:#x}'


if __name__ == '__main__':
    blob, summary = table()
    print(len(blob), summary)
