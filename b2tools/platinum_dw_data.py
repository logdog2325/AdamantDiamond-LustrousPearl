"""The Distortion World's tables, read from Platinum's dump (notes/PLATINUM_DW.md).

    PEARL_VERSION=platinum python3 b2tools/platinum_dw_data.py          writes data/platinum/distortion_world.json, prints a summary
    PEARL_VERSION=platinum python3 b2tools/platinum_dw_data.py --check  also checks the dump against pokeplatinum's own copies
    python3 b2tools/platinum_dw_data.py --blob OUT                      the engine's tables (blob()), for the harness
    python3 b2tools/platinum_dw_data.py --narcs DIR                     Platinum's tw_arc.narc and tw_arc_attr.narc, for its side

What Platinum keeps where (overlay 9, src/overlay009/ov9_02249960.c in pokeplatinum):
- fielddata/tornworld/tw_arc.narc: member 0 the floors' offsets (DistWorldMapInfo: map header, file, offsetTileX,
  offsetAltitude, offsetTileZ); members 1-10 a floor each: the platform templates (DistWorldFloatingPlatformTemplate:
  kind, attribute file, bounds), the jump points (DistWorldFloatingPlatformJumpPointTemplate), the camera triggers
  (DistWorldCameraAngleTemplate) and the ghost props (DistWorldGhostPropHeader, templates, triggers).
- fielddata/tornworld/tw_arc_attr.narc: 12 grids of 32 x 32 u16, a platform's collision (bit 15) and tile behaviour
  (low byte), read at [vertical + horizontal * 32] (GetCurrentFloatingPlatformTileAttributes).
- overlay 9's own data: sDistWorldMapConnectionList (which floor is above and below), sMovingPlatformsMapTemplates
  (the elevators and moving platforms per floor) and sElevatorPlatformPaths (where an elevator goes, and where the zone
  changes on the way). Found by one known row each, then read whole from the dump.

Coordinates. Platinum's floors share one world: a floor's land is drawn at its offsets (LandDataManager_
DistortionWorldSetOffsets), and every table above is in that world's tiles (x, y = height in tiles, z). Black 2 has a
map per zone at the origin, so the engine's tables (blob) are in each floor's own tiles: Platinum's less the floor's
offsets (x - offsetTileX, y - offsetAltitude, z - offsetTileZ). The JSON keeps both. The zone's land and events must
use the same frame (notes/PLATINUM_DW.md "Coordinates").
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom, narc_members  # noqa: E402

PLATINUM_DUMP = os.path.join(ROOT, 'roms', 'platinum.nds')
DECOMP = os.path.join(ROOT, 'external', 'pokeplatinum')
OV9 = 9
OV9_RAM = 0x02249960
MAP_HEADER_INVALID = 593            # MAP_HEADER_COUNT, overlay 9's "none"
FIRST_NEW = 559                     # Platinum's first new map header; Black 2 zone = 685 + id - 559
PLATFORM_FLAG_INVALID = 11          # DIST_WORLD_PLATFORM_FLAG_INVALID
ELEVATOR_PATH_INVALID = 22          # ELEVATOR_PLATFORM_PATH_INVALID
NAMES = {573: '1F', 574: 'B1F', 575: 'B2F', 576: 'B3F', 577: 'B4F', 579: 'B5F', 580: 'B6F', 581: 'B7F',
         582: 'GIRATINA_ROOM', 583: 'TURNBACK_CAVE_ROOM'}
KINDS = ('floor', 'west_wall', 'east_wall', 'ceiling')     # FloatingPlatformKind; 4 = none (the land)
DIRS = ('up', 'down', 'left', 'right')                     # FaceDirection
ELEVATOR_DIRS = ('up', 'down', 'none')                     # MovingPlatformElevatorDirection

ATTR_COLLISION = 0x8000
ATTR_BEHAVIOR = 0xff


def b2_zone(map_header):
    return 685 + map_header - FIRST_NEW


def overlay(rom, n):
    off, _ = struct.unpack_from('<II', rom.data, 0x50)
    idn, ram, size, bss, s, e, fid, flags = struct.unpack_from('<8I', rom.data, off + 32 * n)
    assert idn == n and not (flags & 0x01000000), f'overlay {n}: compressed or misread'
    st, en = rom.fat[fid]
    return ram, rom.data[st:en]


def _bounds(v):
    return {'x': v[0], 'y': v[1], 'z': v[2], 'sx': v[3], 'sy': v[4], 'sz': v[5]}


def _find_one(blob, pat, what):
    i = blob.find(pat)
    assert i >= 0, f'overlay 9: {what} not found'
    assert blob.find(pat, i + 1) < 0, f'overlay 9: {what} found twice'
    return i


def read_ov9_tables(rom):
    ram, o = overlay(rom, OV9)
    assert ram == OV9_RAM, f'overlay 9 at {ram:#x}'

    def ptr(p):
        assert ram <= p < ram + len(o), f'{p:#x} is not in overlay 9'
        return p - ram

    # sDistWorldMapConnectionList: {currID, prevID, nextID}, B1F's row is 574, 573, 575
    i = _find_one(o, struct.pack('<3I', 574, 573, 575), 'the map connections') - 12
    connections = []
    for k in range(len(NAMES)):
        cur, prev, nxt = struct.unpack_from('<3I', o, i + 12 * k)
        connections.append({'map': cur, 'prev': prev, 'next': nxt})
    assert sorted(c['map'] for c in connections) == sorted(NAMES)

    # sElevatorPlatformPaths: 22 rows of 32 bytes; row 0 is 1F's way down
    i = _find_one(o, struct.pack('<HH6h3iHH', 0, ELEVATOR_PATH_INVALID, 0, -32, 0, 0, -16, 0, 0, -4 * 4096, 0, 0,
                                 PLATFORM_FLAG_INVALID), 'elevator path 0')
    paths = []
    for k in range(ELEVATOR_PATH_INVALID):
        idx, nxt, fx, fy, fz, cx, cy, cz, dx, dy, dz, fset, fclear = struct.unpack_from('<HH6h3iHH', o, i + 32 * k)
        assert idx == k, f'elevator path {k}: index {idx}'
        paths.append({'index': idx, 'next': None if nxt == ELEVATOR_PATH_INVALID else nxt,
                      'final': [fx, fy, fz], 'change_maps': [cx, cy, cz], 'delta': [dx, dy, dz],
                      'flag_set': None if fset == PLATFORM_FLAG_INVALID else fset,
                      'flag_clear': None if fclear == PLATFORM_FLAG_INVALID else fclear})

    # sMovingPlatformsMapTemplates: 8 rows {mapHeaderID, pointer to a NULL-ended list of template pointers}
    rows = None
    for at in range(0, len(o) - 64, 4):
        mh, p = struct.unpack_from('<II', o, at)
        if mh == 573 and ram <= p < ram + len(o):
            ids = [struct.unpack_from('<I', o, at + 8 * k)[0] for k in range(8)]
            first, = struct.unpack_from('<I', o, ptr(p))
            # (other tables have the same rows; this one's first template is 1F's elevator at (0x28, 0x121, 0x36))
            if (ids == [573, 574, 575, 576, 577, 579, 580, 581] and ram <= first < ram + len(o) and
                    struct.unpack_from('<H3h', o, ptr(first)) == (0, 0x28, 0x121, 0x36)):
                assert rows is None, 'overlay 9: two moving platform tables'
                rows = at
    assert rows is not None, 'overlay 9: the moving platform table not found'
    moving = {}
    for k in range(8):
        mh, lst = struct.unpack_from('<II', o, rows + 8 * k)
        out = []
        q = ptr(lst)
        while True:
            t, = struct.unpack_from('<I', o, q)
            if t == 0:
                break
            idx, x, y, z, path, edir, dest, kind, flag = struct.unpack_from('<H3hHHIII', o, ptr(t))
            out.append({'index': idx, 'x': x, 'y': y, 'z': z,
                        'path': None if path == ELEVATOR_PATH_INVALID else path, 'elevator_dir': edir,
                        'dest': dest, 'prop_kind': kind,
                        'flag': None if flag == PLATFORM_FLAG_INVALID else flag})
            q += 4
        moving[mh] = out
    return connections, paths, moving


def read_tables(rom=None):
    rom = rom or Rom(PLATINUM_DUMP)
    arc = narc_members(rom.read('fielddata/tornworld/tw_arc.narc'))
    attr = narc_members(rom.read('fielddata/tornworld/tw_arc_attr.narc'))
    assert all(len(a) == 2048 for a in attr), 'tw_arc_attr: a grid is not 32 x 32'
    grids = [list(struct.unpack('<1024H', a)) for a in attr]
    count, = struct.unpack_from('<i', arc[0], 0)
    infos = [struct.unpack_from('<IHhhh', arc[0], 4 + 12 * k) for k in range(count)]
    connections, paths, moving = read_ov9_tables(rom)
    conn = {c['map']: c for c in connections}
    floors = []
    for mh, fidx, ox, oalt, oz in infos:
        d = arc[fidx + 1]                                   # FindMapFileIndex: mapFileIndex + 1
        _, plat_size, jump_size, cam_size, ghost_size = struct.unpack_from('<5i', d, 0)
        p = 20
        platforms, jumps, cams = [], [], []
        if plat_size:
            n, = struct.unpack_from('<i', d, p)
            assert plat_size == 4 + 20 * n
            for k in range(n):
                kind, aid, *b, tv, th = struct.unpack_from('<hH6hHH', d, p + 4 + 20 * k)
                platforms.append({'kind': kind, 'attr': aid, 'bounds': _bounds(b), 'tiles_vertical': tv,
                                  'tiles_horizontal': th})
        p += plat_size
        if jump_size:
            n, = struct.unpack_from('<i', d, p)
            assert jump_size == 4 + 40 * n
            for k in range(n):
                (handler, pdir, dummy, *rest) = struct.unpack_from('<Hhi6h5hHHhhH', d, p + 4 + 40 * k)
                b = rest[:6]
                dx, dy, dz, rot, steps, axis, inverted, final_dir, kind, plat = rest[6:]
                jumps.append({'handler': handler, 'dir': pdir, 'bounds': _bounds(b), 'disp': [dx, dy, dz],
                              'rotation': rot, 'steps': steps, 'axis': axis, 'inverted': inverted,
                              'final_dir': final_dir, 'kind': kind, 'platform': None if plat == 0xffff else plat})
        p += jump_size
        if cam_size:
            n, = struct.unpack_from('<i', d, p)
            assert cam_size == 4 + 24 * n
            for k in range(n):
                *b, ax, ay, az, pdir, steps = struct.unpack_from('<6hHHHhi', d, p + 4 + 24 * k)
                cams.append({'bounds': _bounds(b), 'angle': [ax, ay, az], 'dir': pdir, 'steps': steps})
        p += cam_size
        ghost = None
        if ghost_size:
            nt, ntr, vis = struct.unpack_from('<iiI', d, p)
            assert ghost_size == 12 + 12 * nt + 20 * ntr
            tpl = [dict(zip(('group', 'kind', 'x', 'y', 'z'), struct.unpack_from('<IH3h', d, p + 12 + 12 * k)))
                   for k in range(nt)]
            q = p + 12 + 12 * nt
            trig = []
            for k in range(ntr):
                g, tdir, show, *b = struct.unpack_from('<Ihh6h', d, q + 20 * k)
                trig.append({'group': g, 'dir': tdir, 'show': show, 'bounds': _bounds(b)})
            ghost = {'default_visible': vis, 'templates': tpl, 'triggers': trig}
        p += ghost_size
        assert p == len(d), f'tw_arc member {fidx + 1}: {len(d) - p} bytes left'
        c = conn[mh]
        floors.append({'map': mh, 'name': NAMES[mh], 'zone': b2_zone(mh), 'file': fidx + 1,
                       'offset': [ox, oalt, oz],
                       'prev': None if c['prev'] == MAP_HEADER_INVALID else c['prev'],
                       'next': None if c['next'] == MAP_HEADER_INVALID else c['next'],
                       'platforms': platforms, 'jumps': jumps, 'cameras': cams, 'ghost_props': ghost,
                       'moving_platforms': moving.get(mh, [])})
    return {'floors': floors, 'elevator_paths': paths, 'grids': grids}


def platform_region(p):
    """The (vertical, horizontal) sizes of a platform's bounds in its grid, as GetCurrentFloatingPlatformTileAttributes
    reads it: a floor by x and z, a wall by y and z, the ceiling by x and z."""
    b = p['bounds']
    v = b['sx'] if p['kind'] in (0, 3) else b['sy']
    return v + 1, b['sz'] + 1


def grid_index(p, x, y, z):
    """The grid index Platinum reads for a tile in a platform's bounds (GetCurrentFloatingPlatformTileAttributes)."""
    b = p['bounds']
    kind = p['kind']
    if kind == 0:
        v, h = x - b['x'], z - b['z']
    elif kind == 1:
        v, h = b['sy'] - (y - b['y']), z - b['z']
    elif kind == 2:
        v, h = y - b['y'], z - b['z']
    else:
        v, h = b['sx'] - (x - b['x']), z - b['z']
    return v + h * p['tiles_vertical']


def local(floor, b):
    ox, oy, oz = floor['offset']
    return {**b, 'x': b['x'] - ox, 'y': b['y'] - oy, 'z': b['z'] - oz}


# The engine's tables, in each floor's own tiles (include/pearlb2/plat_dw.h has the same layout)
MAGIC = b'PDW1'
HEADER = '<4sHHIIHH'           # magic, floor count, version, floor table, paths, path count, pad
FLOOR = '<HH3hHHHHHHHIIIII'    # zone, map, offset x/alt/z, land jump count, prev, next (floor index), counts x4, offsets
                               # x4, (plat-dw-rom) the land jumps' offset
LAND_JUMP = '<hhH'             # (plat-dw-rom) x, z, dir of a land tile Platinum jumps twice over (TILE_BEHAVIOR_JUMP_*_TWICE)
PLATFORM = '<hH6hHHI'          # kind, attr, bounds, stride (vertical size), run count, offset of the grid's runs
JUMP = '<Hh6h3hhhHHhhH'        # handler, dir, bounds, disp, rotation, steps, axis, inverted, final dir, kind, platform
CAMERA = '<6hHHHhi'            # bounds, angle x/y/z, dir, steps
MOVING = '<H3hHHIII'           # Platinum's DistWorldMovingPlatformTemplate, the position local
PATH = '<HH6h3iHH'             # Platinum's DistWorldElevatorPlatformPath
VERSION = 2                    # (plat-dw-rom) 2: the land's double jumps


# (plat-dw-rom) TILE_BEHAVIOR_JUMP_NORTH_TWICE .. _EAST_TWICE (map_tile_behaviors.h) as the engine's directions (up, down,
# left, right)
JUMP_TWICE_DIRS = {0x5a: 0, 0x5b: 1, 0x5c: 2, 0x5d: 3}


def land_jumps(floor):
    """(plat-dw-rom) The floor's land tiles with a double jump (Platinum's PlayerAvatar_WillJumpTwice: the tile ahead's
    behaviour is TILE_BEHAVIOR_JUMP_<dir>_TWICE), in its own tiles (its land's matrix block 0, 0 at the origin, as the
    engine's tables): [(x, z, dir)]. From gen4_land's chunks (work/platinum/land) by the floor's matrix
    (work/platinum/matrices, the zone's Platinum matrix in data/platinum/sinnoh_world.json); none when those aren't made yet."""
    work = os.path.join(ROOT, 'work', 'platinum')
    world = json.load(open(os.path.join(ROOT, 'data', 'platinum', 'sinnoh_world.json')))
    mid = next((z['pearl_matrix'] for z in world['rooms']['zones'].values() if z['b2_zone'] == floor['zone']), None)
    path = os.path.join(work, 'matrices', f'{mid}.json')
    if mid is None or not os.path.exists(path):
        return []
    out = []
    for cz, row in enumerate(json.load(open(path))['maps']):
        for cx, lid in enumerate(row):
            land = os.path.join(work, 'land', f'{lid}.json')
            if lid == 0xffff or not os.path.exists(land):
                continue
            beh = json.load(open(land))['behaviour']
            for z in range(32):
                for x in range(32):
                    if beh[z][x] in JUMP_TWICE_DIRS:
                        out.append((cx * 32 + x, cz * 32 + z, JUMP_TWICE_DIRS[beh[z][x]]))
    return out


def runs(cells):
    """A platform's grid region as runs of (count, value): the engine expands it into a buffer when the platform
    becomes the current one, as Platinum reads the platform's grid file then (LoadFloatingPlatformTerrainAttributes)."""
    out = []
    for c in cells:
        if out and out[-1][1] == c and out[-1][0] < 0xffff:
            out[-1][0] += 1
        else:
            out.append([1, c])
    return out


def blob(tables=None):
    t = tables or read_tables()
    floors = t['floors']
    index = {f['map']: k for k, f in enumerate(floors)}
    head = struct.calcsize(HEADER)
    floor_size = struct.calcsize(FLOOR)
    out = bytearray(head + floor_size * len(floors))
    floor_rows = []

    def align():
        out.extend(b'\0' * (-len(out) % 4))

    for f in floors:
        ox, oy, oz = f['offset']
        # the platforms, each with its grid region as Platinum reads it (vertical + horizontal * stride)
        grid_rows = []
        for p in f['platforms']:
            v, h = platform_region(p)
            g = t['grids'][p['attr']]
            cells = []
            for hh in range(h):
                for vv in range(v):
                    cells.append(g[vv + hh * p['tiles_vertical']])
            grid_rows.append((p, v, cells))
        align()
        plat_off = len(out)
        out.extend(b'\0' * (struct.calcsize(PLATFORM) * len(grid_rows)))
        cell_offsets = []
        for p, v, cells in grid_rows:
            align()
            cell_offsets.append((len(out), len(runs(cells))))
            for n, value in runs(cells):
                out.extend(struct.pack('<HH', n, value))
        for k, (p, v, cells) in enumerate(grid_rows):
            b = local(f, p['bounds'])
            struct.pack_into(PLATFORM, out, plat_off + struct.calcsize(PLATFORM) * k, p['kind'], p['attr'],
                             b['x'], b['y'], b['z'], b['sx'], b['sy'], b['sz'], v, cell_offsets[k][1],
                             cell_offsets[k][0])
        align()
        jump_off = len(out)
        for j in f['jumps']:
            b = local(f, j['bounds'])
            out.extend(struct.pack(JUMP, j['handler'], j['dir'], b['x'], b['y'], b['z'], b['sx'], b['sy'], b['sz'],
                                   *j['disp'], j['rotation'], j['steps'], j['axis'], j['inverted'], j['final_dir'],
                                   j['kind'], 0xffff if j['platform'] is None else j['platform']))
        align()
        cam_off = len(out)
        for c in f['cameras']:
            b = local(f, c['bounds'])
            out.extend(struct.pack(CAMERA, b['x'], b['y'], b['z'], b['sx'], b['sy'], b['sz'], *c['angle'], c['dir'],
                                   c['steps']))
        align()
        mov_off = len(out)
        for m in f['moving_platforms']:
            out.extend(struct.pack(MOVING, m['index'], m['x'] - ox, m['y'] - oy, m['z'] - oz,
                                   ELEVATOR_PATH_INVALID if m['path'] is None else m['path'], m['elevator_dir'],
                                   m['dest'], m['prop_kind'],
                                   PLATFORM_FLAG_INVALID if m['flag'] is None else m['flag']))
        align()
        land_off = len(out)
        jumps2 = land_jumps(f)
        for x, z, d in jumps2:
            out.extend(struct.pack(LAND_JUMP, x, z, d))
        floor_rows.append(struct.pack(FLOOR, f['zone'], f['map'], ox, oy, oz, len(jumps2),
                                      0xffff if f['prev'] is None else index[f['prev']],
                                      0xffff if f['next'] is None else index[f['next']],
                                      len(f['platforms']), len(f['jumps']), len(f['cameras']),
                                      len(f['moving_platforms']), plat_off, jump_off, cam_off, mov_off, land_off))
    align()
    path_off = len(out)
    for p in t['elevator_paths']:
        out.extend(struct.pack(PATH, p['index'], ELEVATOR_PATH_INVALID if p['next'] is None else p['next'],
                               *p['final'], *p['change_maps'], *p['delta'],
                               PLATFORM_FLAG_INVALID if p['flag_set'] is None else p['flag_set'],
                               PLATFORM_FLAG_INVALID if p['flag_clear'] is None else p['flag_clear']))
    struct.pack_into(HEADER, out, 0, MAGIC, len(floors), VERSION, head, path_off, len(t['elevator_paths']), 0)
    for k, row in enumerate(floor_rows):
        out[head + floor_size * k:head + floor_size * (k + 1)] = row
    return bytes(out)


def check(tables):
    """The dump against pokeplatinum's own copies of the archives, and the counts the audit gives."""
    rom = Rom(PLATINUM_DUMP)
    for path in ('fielddata/tornworld/tw_arc.narc', 'fielddata/tornworld/tw_arc_attr.narc'):
        own = open(os.path.join(DECOMP, 'res', 'prebuilt', path), 'rb').read()
        assert own == rom.read(path), f'{path}: the dump and pokeplatinum differ'
    faces = sum(1 for f in tables['floors'] for p in f['platforms'] if p['kind'] != 0)
    jumps = sum(len(f['jumps']) for f in tables['floors'])
    cams = sum(len(f['cameras']) for f in tables['floors'])
    assert (faces, jumps, cams) == (6, 20, 26), (faces, jumps, cams)
    # every jump lands where a platform (or the land) is: its platform's bounds hold the landing tile
    for f in tables['floors']:
        for j in f['jumps']:
            b = j['bounds']
            land = (b['x'] + j['disp'][0], b['y'] + j['disp'][1], b['z'] + j['disp'][2])
            if j['platform'] is not None:
                p = f['platforms'][j['platform']]
                pb = p['bounds']
                assert p['kind'] == j['kind'], (f['name'], j)
                assert (pb['x'] <= land[0] <= pb['x'] + pb['sx'] and pb['y'] <= land[1] <= pb['y'] + pb['sy'] and
                        pb['z'] <= land[2] <= pb['z'] + pb['sz']), (f['name'], j, land)
    return f'{faces} faces, {jumps} jump points, {cams} camera triggers; the dump equals pokeplatinum\'s archives'


def main():
    if '--narcs' in sys.argv:
        out = sys.argv[sys.argv.index('--narcs') + 1]
        rom = Rom(PLATINUM_DUMP)
        for name in ('tw_arc.narc', 'tw_arc_attr.narc'):
            open(os.path.join(out, name), 'wb').write(rom.read('fielddata/tornworld/' + name))
        return
    if '--blob' in sys.argv:
        out = sys.argv[sys.argv.index('--blob') + 1]
        data = blob()
        open(out, 'wb').write(data)
        print(f'{out}: {len(data)} bytes')
        return
    import version
    t = read_tables()
    floors = []
    for f in t['floors']:
        g = {**f}
        g['platforms'] = [{**p, 'bounds_local': local(f, p['bounds']),
                           'grid': [t['grids'][p['attr']][grid_index(p, x, y, z)]
                                    for z in range(p['bounds']['z'], p['bounds']['z'] + p['bounds']['sz'] + 1)
                                    for y in range(p['bounds']['y'], p['bounds']['y'] + p['bounds']['sy'] + 1)
                                    for x in range(p['bounds']['x'], p['bounds']['x'] + p['bounds']['sx'] + 1)]}
                          for p in f['platforms']]
        g['jumps'] = [{**j, 'bounds_local': local(f, j['bounds'])} for j in f['jumps']]
        g['cameras'] = [{**c, 'bounds_local': local(f, c['bounds'])} for c in f['cameras']]
        floors.append(g)
    out = {'note': 'Generated by b2tools/platinum_dw_data.py from Platinum\'s dump: don\'t edit. Bounds in Platinum\'s '
                   'shared world (bounds) and in the floor\'s own tiles (bounds_local = less the floor\'s offset). A '
                   'platform\'s grid lists its tiles z, then y, then x, each Platinum\'s u16 (bit 15 collision, low '
                   'byte the tile behaviour).',
           'floors': floors, 'elevator_paths': t['elevator_paths']}
    path = version.data_out('distortion_world.json')
    with open(path, 'w') as fh:
        json.dump(out, fh, indent=1)
    data = blob(t)
    print(f'{path}: {len(t["floors"])} floors; engine tables {len(data)} bytes')
    if '--check' in sys.argv:
        print(check(t))


if __name__ == '__main__':
    main()
