"""Phase 1 reader: a Gen 4 game's zones, matrices, events and wild Pokémon, from the dump to JSON.

    python3 gen4_extract.py [ROM] [OUT_DIR]      defaults: the version's dump and work/<version> (PEARL_VERSION=diamond:
                                                 roms/diamond.nds, work/diamond; PEARL_VERSION=platinum: roms/platinum.nds,
                                                 work/platinum)

Formats follow pokediamond's MapHeader (include/map_header.h) and pokeplatinum's packers
(tools/jsoncnv/map_matrix.py, event.py, encounter.py), read in reverse; the JSON keys are Platinum's, so the files can
be compared with external/pokeplatinum/res/field/*. Names (zones, species) come from pokediamond's constants.
Read-only: nothing is written to the ROM.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom, narc_members  # noqa: E402
import version  # noqa: E402

DIAMOND = os.path.join(ROOT, 'external', 'pokediamond')
PLATINUM = os.path.join(ROOT, 'external', 'pokeplatinum')
HEADER_SIZE = 24


def constants(path, prefix):
    """{value: name} for '#define PREFIX_NAME value' lines (first name wins)."""
    names = {}
    for m in re.finditer(rf'#define\s+({prefix}\w+)\s+(0x[0-9a-fA-F]+|\d+)', open(path, encoding='utf-8').read()):
        names.setdefault(int(m.group(2), 0), m.group(1))
    return names


def zone_names():
    """(names, decomp names) of every zone, by zone number. Pearl's constant names; Platinum's 559 first zones are the same
    places under the same numbers, so they keep Pearl's name (data/*.json and the tools name zones that way), and Platinum's
    decomp's name goes in the second list; its 34 new zones take that name with MAP_HEADER_ cut to MAP_."""
    pearl = constants(os.path.join(DIAMOND, 'include', 'constants', 'maps.h'), 'MAP_')
    pearl = [pearl[i] for i in range(len(pearl))]
    if not version.PLATINUM:
        return pearl, None
    path = os.path.join(PLATINUM, 'generated', 'map_headers.txt')
    theirs = [l.strip().replace('MAP_HEADER_', 'MAP_', 1) for l in open(path) if l.strip()][:version.ZONE_COUNT]
    assert len(theirs) == version.ZONE_COUNT and len(pearl) == 559, f'{path}: {len(theirs)} names, Pearl {len(pearl)}'
    return pearl + theirs[len(pearl):], theirs


def species_names():
    """{species number: constant}. Platinum's list is the same numbers (a Rotom form or Giratina Origin is a form, not a species)."""
    return constants(os.path.join(DIAMOND, 'include', 'constants', 'species.h'), 'SPECIES_')


def find_header_table(arm9, zone_count):
    """Offset of the map header table in arm9: entry 3 (Jubilife) uses matrix 0, scripts 2 and events 2, and every
    entry's matrix id is below 245 (pokediamond arm9/src/map_header.c), or below 289 in Platinum."""
    probe = struct.pack('<BBHH', 6, 0, 0, 2)
    matrices = 289 if version.PLATINUM else 245
    start = 0
    while True:
        i = arm9.find(probe, start)
        if i < 0:
            raise SystemExit('map header table not found')
        base = i - 3 * HEADER_SIZE
        ok = base >= 0 and all(struct.unpack_from('<H', arm9, base + z * HEADER_SIZE + 2)[0] < matrices
                               for z in range(zone_count))
        if ok and struct.unpack_from('<H', arm9, base + 3 * HEADER_SIZE + 16)[0] == 2:
            return base
        start = i + 1


def read_header_flags(z, f):
    """The fields that differ in the two games' header (pokeplatinum include/map_header.h): Platinum packs the place's text id
    and banner window into one u16 and map type, battle background and the permissions into another (7 + 5 + 4 bits, with a
    run bit Pearl doesn't have); Pearl has bytes."""
    if not version.PLATINUM:
        return {'mapsec': f[10], 'weather': f[11], 'camera': f[12], 'map_type': f[13], 'battle_bg': f[14] & 15,
                'bike': bool(f[14] & 16), 'escape_rope': bool(f[14] & 64), 'fly': bool(f[14] & 128)}
    bits = f[13] | f[14] << 8
    # weather in Pearl's numbers: Platinum's day-by-day columns start at 32, Pearl's at 24; its 23-30 are new area effects (Eterna Forest's
    # canopy, the dark of Mt. Coronet and Solaceon Ruins, ...) Pearl's zones don't have: 0 there, the effect kept as "pl_weather"
    w = f[11] - 8 if f[11] >= 32 else 0 if 23 <= f[11] <= 30 else f[11]
    return {'mapsec': f[10] & 0xff, 'label_window': f[10] >> 8, 'weather': w, 'pl_weather': f[11], 'camera': f[12], 'map_type': bits & 0x7f,
            'battle_bg': bits >> 7 & 31, 'bike': bool(bits >> 12 & 1), 'running': bool(bits >> 13 & 1),
            'escape_rope': bool(bits >> 14 & 1), 'fly': bool(bits >> 15 & 1)}


def read_headers(rom, names, decomp_names=None):
    arm9_off, _, _, arm9_size = struct.unpack_from('<4I', rom.data, 0x20)
    arm9 = rom.data[arm9_off:arm9_off + arm9_size]
    base = find_header_table(arm9, len(names))
    zones = []
    for z in range(len(names)):
        f = struct.unpack_from('<BBHHHHHHHHHBBBB', arm9, base + z * HEADER_SIZE)
        zones.append({
            'id': z, 'name': names[z], 'area': f[0], 'move_models': f[1], 'matrix': f[2], 'scripts': f[3],
            'level_scripts': f[4], 'text_bank': f[5], 'music_day': f[6], 'music_night': f[7],
            'encounters': None if f[8] == 0xffff else f[8], 'events': f[9], **read_header_flags(z, f)})
        if decomp_names:
            zones[-1]['pl_name'] = decomp_names[z]
    return arm9_off + base, zones


def read_matrix(m):
    w, h, has_hdr, has_alt, nl = m[:5]
    p = 5 + nl
    grid = lambda vals: [list(vals[r * w:(r + 1) * w]) for r in range(h)]
    out = {'name': m[5:p].decode('ascii'), 'width': w, 'height': h, 'headers': [], 'altitudes': []}
    if has_hdr:
        out['headers'] = grid(struct.unpack_from(f'<{w * h}H', m, p)); p += 2 * w * h
    if has_alt:
        out['altitudes'] = grid(m[p:p + w * h]); p += w * h
    out['maps'] = grid(struct.unpack_from(f'<{w * h}H', m, p))
    return out


def read_events(e):
    p = 0
    def count():
        nonlocal p
        n, = struct.unpack_from('<I', e, p); p += 4
        return n
    bg = []
    for _ in range(count()):
        s, t, x, z, y, d = struct.unpack_from('<HHiiiH', e, p); p += 20
        bg.append({'script': s, 'type': t, 'x': x, 'z': z, 'y': y, 'player_facing_dir': d})
    obj = []
    for _ in range(count()):
        f = struct.unpack_from('<14Hi', e, p); p += 32
        obj.append({'id': f[0], 'graphics_id': f[1], 'movement_type': f[2], 'trainer_type': f[3], 'hidden_flag': f[4],
                    'script': f[5], 'initial_dir': f[6], 'data': list(f[7:10]), 'movement_range_x': f[10],
                    'movement_range_z': f[11], 'x': f[12], 'z': f[13], 'y': f[14] // 0x10000})
    warps = []
    for _ in range(count()):
        x, z, dest, dest_warp = struct.unpack_from('<4H', e, p); p += 12
        warps.append({'x': x, 'z': z, 'dest_header_id': dest, 'dest_warp_id': dest_warp})
    coords = []
    for _ in range(count()):
        f = struct.unpack_from('<8H', e, p); p += 16
        coords.append(dict(zip(['script', 'x', 'z', 'width', 'length', 'y', 'value', 'var'], f)))
    assert p == len(e), f'event file: {len(e) - p} bytes left'
    return {'bg_events': bg, 'object_events': obj, 'warp_events': warps, 'coord_events': coords}


def read_encounters(d, species):
    sp = lambda v: species.get(v, v)
    u32 = lambda o: struct.unpack_from('<I', d, o)[0]
    out = {'land_rate': u32(0), 'land_encounters': [{'level': u32(4 + 8 * i), 'species': sp(u32(8 + 8 * i))}
                                                    for i in range(12)]}
    p = 100
    for key in ['swarms', 'day', 'night']:
        out[key] = [sp(u32(p)), sp(u32(p + 4))]; p += 8
    out['radar'] = [sp(u32(p + 4 * i)) for i in range(4)]; p += 16
    for key in ['rate_form0', 'rate_form1', 'rate_form2', 'rate_form3', 'rate_form4', 'unown_table']:
        out[key] = u32(p); p += 4
    for key in ['ruby', 'sapphire', 'emerald', 'firered', 'leafgreen']:
        out[key] = [sp(u32(p)), sp(u32(p + 4))]; p += 8
    def water():
        nonlocal p
        rows = []
        for _ in range(5):
            hi, lo, _, s = struct.unpack_from('<BBHI', d, p); p += 8
            rows.append({'level_max': hi, 'level_min': lo, 'species': sp(s)})
        return rows
    out['surf_rate'] = u32(p); p += 4
    out['surf_encounters'] = water()
    p += 44
    for rod in ['old', 'good', 'super']:
        out[f'{rod}_rod_rate'] = u32(p); p += 4
        out[f'{rod}_rod_encounters'] = water()
    assert p == len(d), f'encounter file: {len(d) - p} bytes left'
    return out


def main():
    rom_path = sys.argv[1] if len(sys.argv) > 1 else version.SOURCE_DUMP
    out_dir = sys.argv[2] if len(sys.argv) > 2 else version.WORK
    rom = Rom(rom_path)
    assert rom.code == version.SOURCE_GAME_CODE, f'expected {version.NAME} ({version.SOURCE_GAME_CODE}), got {rom.code}'
    species = species_names()
    table_off, zones = read_headers(rom, *zone_names())
    land = None
    if version.PLATINUM:    # the tools name files by Pearl's numbers (platinum_maps.py): each number as a slot, its own one kept as "dump"
        slots = {k: version.of_slot(a) for k, a in (('matrix', 'matrices'), ('events', 'events'), ('scripts', 'scripts'), ('level_scripts', 'scripts'),
                                                     ('text_bank', 'banks'))}
        land = version.of_slot('land')
        for z in zones:
            z['dump'] = {k: z[k] for k in slots}
            z.update({k: slots[k][z[k]] for k in slots})
    os.makedirs(os.path.join(out_dir, 'matrices'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'events'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'encounters'), exist_ok=True)
    dump = lambda path, obj: json.dump(obj, open(os.path.join(out_dir, path), 'w'), indent=1)
    dump('zones.json', zones)
    mats = version.slotted('matrices', narc_members(rom.read('fielddata/mapmatrix/map_matrix.narc')))
    for i, m in enumerate(mats):
        if m:
            mat = read_matrix(m)
            if land:
                mat['maps'] = [[land[c] if c != 0xffff else c for c in row] for row in mat['maps']]
            dump(f'matrices/{i:03d}.json', mat)
    events = version.slotted('events', narc_members(rom.read(version.ARCHIVE['events'])))
    for i, e in enumerate(events):
        if e:
            dump(f'events/{i:03d}.json', read_events(e))
    # ---- plat-dw-world (2026-11-07): the Distortion World's floors get event files of their own, past the dump's: their
    # events in the floor's own tiles and overlay 9's people (b2tools/platinum_dw_world.py zone_events)
    if version.PLATINUM:
        import platinum_dw_world
        world = platinum_dw_world.read(rom)
        dw_floors = {f['map']: f for f in platinum_dw_world.dwd.read_tables(rom)['floors']}
        for k, z in enumerate(z for z in zones if z['id'] in dw_floors):
            n = len(events) + k
            dump(f'events/{n:03d}.json', platinum_dw_world.zone_events(z['id'], read_events(events[z['events']]) if
                                                                       events[z['events']] else
                                                                       {'bg_events': [], 'object_events': [],
                                                                        'warp_events': [], 'coord_events': []},
                                                                       world, dw_floors))
            z['events'] = n
        dump('zones.json', zones)
    # ---- end plat-dw-world
    encs = narc_members(rom.read(version.ENCOUNTER_NARC))
    for i, d in enumerate(encs):
        dump(f'encounters/{i:03d}.json', read_encounters(d, species))
    print(f'{rom.title} {rom.code} rev {rom.revision}: header table at ROM 0x{table_off:x}; {len(zones)} zones, '
          f'{len(mats)} matrices, {len(events)} event files, {len(encs)} encounter files -> {out_dir}')


if __name__ == '__main__':
    main()
