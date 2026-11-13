"""Every converted walkable tile's height against the version's own BDHC (offline; 2026-11-07, Platinum step 4).

    python3 b2tools/heights_check.py                       Pearl (PEARL_VERSION=platinum: Platinum): every installed chunk
    python3 b2tools/heights_check.py --rooms | --world     the rooms' chunks or the overworld's only
    python3 b2tools/heights_check.py --chunks 234,241      these chunks (their maps are still walked whole)
    python3 b2tools/heights_check.py --list                every difference, the explained ones too
    python3 b2tools/heights_check.py --json OUT            the table as JSON
    python3 b2tools/heights_check.py --jobs N              N processes (default 1)

The source game's height (pokeplatinum terrain_collision_manager.c GetHeight, overlay005/bdhc.c CalculateObjectHeight;
Pearl's BDHC follows the same rule, gen4_land.read_bdhc_dp): a walker takes, of the BDHC plates over its x, z, the one
nearest its own height, and a step of 20 units or more is a wall. Black 2's (ov036 FieldG3DMapper_GetTerrain): of the
chunk's terrain layers, the valid one nearest the walker's height.

What is compared. The chunks are converted as sinnoh_world and sinnoh_rooms convert them (pearl_chunk.convert in the first
cell that holds them, with its neighbours; outdoors the entrance mats as bump warps; MAP_FIXES=none: the model fixes change
the drawing, not the terrain). Each zone map is walked with the source game's rules: from its warps (an arriving player
takes the plate nearest height 0) and its people (the plate nearest their event height); the 20-unit step on the BDHC; a
tile with no plate keeps the walker's height; ledges, Rock Climb, waterfalls, slides, escalators and bike slopes cross any
height; water is entered (Surf). Every tile and level reached, and every person's tile at the person's level, is a place
someone stands. There the converted layer nearest that level must be within SAME units of it (most rooms draw their floor
2 under the BDHC, and the converter stands people on the drawn floor). A place over SAME is
- HIGH: the converted ground over the level (the Veilstone Gym's ceiling rails taken for the floor), or
- LOW: under it (a floor taken too low: the lakes' bed under their water),
- WALL: a wall in the conversion where the source game walks (listed, not a height fault; a person on a tile solid in
  both games is compared at the solid cell's height, where Black 2 draws them),
unless it is explained: stairs, warp mats, bridges' decks, lift plates, beds, bump warps, climbs and slides, furniture
solid by behaviour, slopes (a sloped plate the converted plane follows within SLOPE_SAME), the Gyms' floors under the BDHC
(their gimmicks move them: Pastoria's water, Canalave's floors, Sunyshore's walkways, the Eterna clock), maps Gen 4 reads
no heights on (FLAT_MAPS), and the rows checked by hand (EXPLAINED). Exit 1 if a HIGH or LOW is left unexplained.

Before and after (2026-11-07): Platinum 6,084 faults in 98 chunks -> 0 (pearl_chunk.bdhc_ground, version.GROUND_AT_BDHC).
Pearl 3,019 faults in 49 chunks (its 1.0 maps), Diamond 3,020 in 50 -> 0 and 0 (1.0.1: the rule on for them too; notes/V1_0_1.md).
"""
import collections, json, os, struct, sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
os.environ.setdefault('MAP_FIXES', 'none')
import version  # noqa: E402
from version import land_id  # noqa: E402
import pearl_chunk  # noqa: E402
from gen4_land import bdhc_dp_heights  # noqa: E402

PEARL = version.WORLD_WORK
SAME = 5                    # the converted level within this of the source game's: the same (pearl_chunk.GROUND_MATCH
#                             and the Black 2 plane's MAX_ERR)
SLOPE_SAME = 8              # on a sloped plate (or beside one) the plane may miss by this much
STEP = 20                   # both games: a step of 20 units or more is a wall
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
JUMPS = {0x38: (1, 0), 0x39: (-1, 0), 0x3a: (0, -1), 0x3b: (0, 1),             # pokeplatinum map_tile_behaviors.h
         0x5a: (0, -1), 0x5b: (0, 1), 0x5c: (-1, 0), 0x5d: (1, 0)}             # (and the "twice" ones)
FREE = {0x13, 0x40, 0x41, 0x42, 0x43, 0x4b, 0x4c, 0x6a, 0x6b, 0xd7, 0xd8, 0xd9, 0xda}   # waterfall, slides, Rock Climb,
#                                                                         escalators, bike ramps and slopes: any height
GIMMICK_FLOOR = {0x56, 0x57, 0x58, 0x59}   # Pastoria Gym's grounds, DYNAMIC_HEIGHT_COLLISION: the Gyms' C moves them
FLAT_MAPS = pearl_chunk.FLAT_MAPS   # Gen 4 reads no heights there (the Underground); patches/underground.py
# Places checked by hand: {version: {chunk: (tiles or None for the whole chunk, why)}}. Kept short; each row says why
# the difference is right.
EXPLAINED = {
    # Oreburgh's north house 3F: the man at (2, 11) stands in the room's west wall, where no plate is: Gen 4 keeps his
    # event height (16), Black 2 puts him on the tile's (0). The same in both games' data.
    v: {202: ({(2, 11)}, 'person in a wall')} for v in ('pearl', 'diamond', 'platinum')}


def _json(*p):
    return json.load(open(os.path.join(*p)))


def jobs():
    """[(kind, chunk, neighbours, solid behaviours)] as the build converts them (sinnoh_world, sinnoh_rooms)."""
    world = _json(version.data_path('sinnoh_world.json'))
    m0 = _json(PEARL, 'matrices', '000.json')
    first = {}
    for z, row in enumerate(m0['maps']):
        for x, c in enumerate(row):
            if c != 0xffff: first.setdefault(c, (x, z))
    out = [('world', int(c), pearl_chunk.neighbours(m0, *first[int(c)]), tuple(pearl_chunk.ENTRANCES))
           for c in world['chunks']]
    where = {}
    for mid in world['rooms']['matrices']:
        m = _json(PEARL, 'matrices', f'{int(mid):03d}.json')
        for z in range(m['height']):
            for x in range(m['width']):
                c = m['maps'][z][x]
                if c != 0xffff and str(c) in world['rooms']['chunks']: where.setdefault(c, (m, x, z))
    out += [('room', int(c), pearl_chunk.neighbours(*where[int(c)]), ()) for c in world['rooms']['chunks']]
    return out


_TABLES = []
# Each chunk's result is kept (CACHE, git-ignored), keyed by the code and land files it comes from, so a run cut short by
# the watchdog goes on where it stopped and a second run takes seconds.
CACHE = os.path.join(version.WORLD_WORK, 'heights_check')
CODE = ('pearl_chunk.py', 'gen4_land.py', 'version.py', 'pearl_gimmicks.py')   # (and convert_chunk_now's own source)


def code_key():
    """The code the chunks are converted with, and the data it reads besides the land files (the world's tables, the
    zones' events: person_tiles, gym_chunks, the lifts, the people's depth rows). Read once, before the workers start."""
    import glob, hashlib, inspect
    h = hashlib.sha1(inspect.getsource(convert_chunk_now).encode())
    for f in CODE:
        h.update(open(os.path.join(HERE, f), 'rb').read())
    data = [version.data_path('sinnoh_world.json'), os.path.join(ROOT, 'data', 'people_depth.json'),
            os.path.join(PEARL, 'zones.json')] + sorted(glob.glob(os.path.join(PEARL, 'events', '*.json')))
    for p in data:
        st = os.stat(p)
        h.update(f'{p} {st.st_size} {st.st_mtime_ns}'.encode())
    return h.hexdigest()


def _key(job):
    import hashlib
    kind, c, around, solid_beh, code = job
    h = hashlib.sha1(repr((version.VERSION, kind, c, sorted(around.items()), sorted(solid_beh), code)).encode())
    for k in [c] + sorted(around.values()):
        for ext in ('json', 'bdhc', 'nsbmd'):
            st = os.stat(os.path.join(pearl_chunk.LAND, f'{land_id(k):03d}.{ext}'))
            h.update(f'{st.st_size} {st.st_mtime_ns}'.encode())
    return h.hexdigest()[:20]


def convert_chunk(job):
    """convert_chunk_now's result, from CACHE when the same code and files made it."""
    path = os.path.join(CACHE, f'{job[1]:04d}_{_key(job)}.json')
    if os.path.exists(path):
        return _json(path)
    out = convert_chunk_now(job)
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(path + '.part', 'w'))
    os.replace(path + '.part', path)
    return out


def convert_chunk_now(job):
    """One chunk (a worker): {'c', 'kind', 'tiles': [[collision, behaviour, [plates], [[height, solid], per layer]]],
    'explain': {tile: kind}}; tiles in row order (tz * 32 + tx)."""
    kind, c, around, solid_beh = job[:4]
    if not _TABLES: _TABLES.append(pearl_chunk.tables())
    slopes, offsets = _TABLES[0]
    data, rep = pearl_chunk.convert(c, slopes, offsets, around, set(solid_beh))
    magic, layers, _ = pearl_chunk.terrains(data)
    land = _json(pearl_chunk.LAND, f'{land_id(c):03d}.json')
    b = pearl_chunk.bdhc(c)
    tiles = []
    for tz in range(32):
        for tx in range(32):
            x, z = tx * 16 - 256 + 8, tz * 16 - 256 + 8
            hs = []
            for t in layers:
                a, bb, fl = struct.unpack_from('<HHI', t, 4 + 8 * (tz * 32 + tx))
                hs.append([round(pearl_chunk.plane_y(slopes, offsets, a, bb, x, z), 2), (fl >> 16) & 1])
            plates = [[round(y, 2), round(abs(n[1]), 3)] for y, n in bdhc_dp_heights(b, x, z)] if b else []
            tiles.append([land['collision'][tz][tx], land['behaviour'][tz][tx], plates, hs])
    explain = {}
    for tx, tz, _ in rep['stairs']:
        explain[f'{tx},{tz}'] = 'stairs'
        for dx in (-1, 1):
            if 0 <= tx + dx < 32: explain.setdefault(f'{tx + dx},{tz}', 'stairs')
    for t in rep['mats']: explain.setdefault(f'{t[0]},{t[1]}', 'warp mat')
    for t in rep['decks']: explain.setdefault(f'{t[0]},{t[1]}', 'bridge')
    for (tx, tz) in pearl_chunk.two_levels(c): explain.setdefault(f'{tx},{tz}', 'bridge')
    for (tx, tz) in pearl_chunk.lift_plate(c): explain.setdefault(f'{tx},{tz}', 'lift plate')
    for (tx, tz) in pearl_chunk.bed_solid(c): explain.setdefault(f'{tx},{tz}', 'bed')
    for tz in range(32):
        for tx in range(32):
            if land['behaviour'][tz][tx] in solid_beh: explain.setdefault(f'{tx},{tz}', 'bump warp')
    return {'c': c, 'kind': kind, 'magic': magic, 'tiles': tiles, 'explain': explain}


class Maps:
    """The zone maps (matrices) of the installed zones, their people and warps, by global tile."""

    def __init__(self):
        world = _json(version.data_path('sinnoh_world.json'))
        zones = _json(PEARL, 'zones.json')
        self.maps = collections.defaultdict(lambda: {'warps': [], 'people': []})
        installed = [(int(k), 0) for k in world['zones']] + \
                    [(int(k), r['pearl_matrix']) for k, r in world['rooms']['zones'].items()]
        self.names = collections.defaultdict(set)
        self.cell_name = {}                       # (matrix, cx, cz): the zone of a cell (the overworld's headers)
        m0 = _json(PEARL, 'matrices', '000.json')
        for cz, row in enumerate(m0['headers']):
            for cx, h in enumerate(row):
                if h: self.cell_name[(0, cx, cz)] = zones[h]['name']
        for pid, mid in installed:
            z = zones[pid]
            ev = _json(PEARL, 'events', f"{z['events']:03d}.json")
            m = self.maps[mid]
            m['warps'] += [(w['x'], w['z']) for w in ev['warp_events']]
            m['people'] += [(o['x'], o['z'], o['y'] * 16, pid, o['id']) for o in ev['object_events']]
            self.names[mid].add(z['name'])
        self.matrix = {mid: _json(PEARL, 'matrices', f'{mid:03d}.json') for mid in self.maps}


def walk(mid, matrix, info, warps, people):
    """{(chunk, tx, tz): set of BDHC levels} where someone stands on zone map `mid` (the source game's rules, above),
    and {(chunk, tx, tz): [(level, pid, object id)]} of its people."""
    def at(x, z):
        cx, cz = x // 32, z // 32
        if x < 0 or z < 0 or cx >= matrix['width'] or cz >= matrix['height']: return None
        c = matrix['maps'][cz][cx]
        if c == 0xffff or c not in info: return None
        return c, x % 32, z % 32, info[c]['tiles'][(z % 32) * 32 + x % 32]

    def nearest(plates, y):
        return min((p[0] for p in plates), key=lambda h: abs(h - y)) if plates else y

    seen, todo = set(), []
    for x, z in warps:              # (an arriving player is made at height 0, then takes the plate nearest it:
        t = at(x, z)                # pokeplatinum PlayerAvatar_New, MapObject_RecalculatePositionHeight)
        if t is not None: todo.append((x, z, nearest(t[3][2], 0.0)))
    persons = collections.defaultdict(list)
    for x, z, y, pid, oid in people:
        t = at(x, z)
        if t is None: continue
        lv = nearest(t[3][2], y)
        persons[t[:3]].append((lv, pid, oid))
        todo.append((x, z, lv))
    reached = collections.defaultdict(set)
    while todo:
        x, z, y = todo.pop()
        key = (x, z, round(y))
        if key in seen: continue
        seen.add(key)
        t = at(x, z)
        if t is None: continue
        reached[t[:3]].add(y)
        here = t[3][1]
        for dx, dz in DIRS:
            n = at(x + dx, z + dz)
            if n is None: continue
            col, beh, plates, _ = n[3]
            if beh in JUMPS and JUMPS[beh] == (dx, dz):          # a ledge: over it, any height
                far = 2 if beh < 0x5a else 3
                m = at(x + dx * far, z + dz * far)
                if m is not None and not m[3][0]:
                    for p in (m[3][2] or [[y]]): todo.append((x + dx * far, z + dz * far, p[0]))
                continue
            if col: continue
            if beh in FREE or here in FREE:
                for p in (plates or [[y]]): todo.append((x + dx, z + dz, p[0]))
                continue
            y2 = nearest(plates, y)
            if abs(y2 - y) < STEP: todo.append((x + dx, z + dz, y2))
    return reached, persons


def compare(info, reached, persons, simple=False):
    """[row] of every place someone stands: {c, x, z, level, height (the converted layer nearest), d, kind, why}.
    simple: a map whose heights Gen 4 doesn't read (FLAT_MAPS)."""
    rows = []
    gyms = pearl_chunk.gym_chunks()
    places = collections.defaultdict(set)
    for k, ys in reached.items(): places[k] |= {round(y, 2) for y in ys}
    for k, ps in persons.items(): places[k] |= {round(p[0], 2) for p in ps}
    for (c, tx, tz), ys in sorted(places.items()):
        col, beh, plates, hs = info[c]['tiles'][tz * 32 + tx]
        for y in sorted(ys):
            valid = [h for h, solid in hs if not solid]
            row = {'c': c, 'x': tx, 'z': tz, 'level': y, 'beh': beh, 'plates': [p[0] for p in plates],
                   'layers': [h for h, _ in hs], 'person': [p[1:] for p in persons.get((c, tx, tz), []) if round(p[0], 2) == y]}
            if not valid and col and row['person']:    # (a person on a tile solid in both games: drawn at the solid
                valid = [h for h, _ in hs]             # cell's height; a warp there is a bump warp, at the walker's)
            if not valid:                              # (a warp on a tile solid in both: a bump warp, no stand)
                row.update(kind='ok' if col else 'WALL', d=None, height=None)
            else:
                h = min(valid, key=lambda v: abs(v - y))
                d = round(h - y, 2)
                row.update(height=h, d=d, kind='ok' if abs(d) <= SAME else 'HIGH' if d > 0 else 'LOW')
            if row['kind'] != 'ok':
                row['why'] = why(info, c, tx, tz, row, gyms, simple)
            rows.append(row)
    return rows


def why(info, c, tx, tz, row, gyms, simple=False):
    """The explanation of a difference, or None."""
    if simple: return 'flat map'
    own = EXPLAINED.get(version.VERSION, {}).get(c)
    if own and (own[0] is None or (tx, tz) in own[0]): return own[1]
    ex = info[c]['explain'].get(f'{tx},{tz}')
    if ex: return ex
    beh = row['beh']
    if beh in GIMMICK_FLOOR or (c in gyms and beh in pearl_chunk.BRIDGES): return 'gym floor'
    if c in gyms and row['kind'] == 'LOW': return 'gym floor'
    if beh in FREE: return 'climb or slide'
    if row['kind'] == 'WALL':
        cls = pearl_chunk.BEHAVIOURS.get(beh)
        return 'solid by behaviour' if cls and cls[1] & 1 else None
    plates = info[c]['tiles'][tz * 32 + tx][2]
    sloped = any(p[1] < 0.999 for p in plates)
    for dx, dz in DIRS:
        if 0 <= tx + dx < 32 and 0 <= tz + dz < 32:
            sloped = sloped or any(p[1] < 0.999 for p in info[c]['tiles'][(tz + dz) * 32 + tx + dx][2])
    if sloped and abs(row['d']) <= SLOPE_SAME: return 'slope'
    return None


def main(argv):
    want_kind = 'room' if '--rooms' in argv else 'world' if '--world' in argv else None
    only = set(map(int, argv[argv.index('--chunks') + 1].split(','))) if '--chunks' in argv else None
    out_json = argv[argv.index('--json') + 1] if '--json' in argv else None
    listing = '--list' in argv
    jobs_n = int(argv[argv.index('--jobs') + 1]) if '--jobs' in argv else 1
    M = Maps()
    js = jobs()
    kind_of = {j[1]: j[0] for j in js}
    need = set()
    for mid, matrix in M.matrix.items():
        cs = {c for row in matrix['maps'] for c in row if c != 0xffff and c in kind_of}
        if only is not None and not cs & only: continue
        if want_kind and not any(kind_of[c] == want_kind for c in cs): continue
        need |= cs
    code = code_key()
    js = [j + (code,) for j in js if j[1] in need]
    info = {}
    if jobs_n <= 1:
        for j in js:
            r = convert_chunk(j)
            info[r['c']] = r
    else:
        with ProcessPoolExecutor(jobs_n) as ex:
            for r in ex.map(convert_chunk, js, chunksize=1):
                info[r['c']] = r
    rows = []
    for mid, matrix in sorted(M.matrix.items()):
        cs = {c for row in matrix['maps'] for c in row if c != 0xffff}
        if not cs & set(info): continue
        reached, persons = walk(mid, matrix, info, M.maps[mid]['warps'], M.maps[mid]['people'])
        for r in compare(info, reached, persons, bool(M.names[mid] & FLAT_MAPS)):
            r['map'] = mid
            rows.append(r)
    # a chunk in several maps: each place once (its first map's row)
    uniq = {}
    for r in rows:
        uniq.setdefault((r['c'], r['x'], r['z'], r['level']), r)
    rows = [r for r in uniq.values() if (only is None or r['c'] in only) and (want_kind is None or kind_of[r['c']] == want_kind)]
    bad = [r for r in rows if r['kind'] in ('HIGH', 'LOW') and not r.get('why')]
    walls = [r for r in rows if r['kind'] == 'WALL']
    explained = [r for r in rows if r['kind'] != 'ok' and r.get('why')]
    names = {}
    for mid, ns in sorted(M.names.items()):
        for cz, row in enumerate(M.matrix[mid]['maps']):
            for cx, c in enumerate(row):
                if c != 0xffff:
                    names.setdefault(c, M.cell_name.get((mid, cx, cz), sorted(ns)[0]).replace('MAP_', ''))
    by = collections.Counter((r['c'], r['kind']) for r in bad)
    print(f'{version.NAME}: {len(rows)} places where someone stands, in {len({r["c"] for r in rows})} chunks '
          f'({len(info)} converted).')
    print(f'  faults: {len(bad)} in {len({r["c"] for r in bad})} chunks '
          f'(HIGH {sum(r["kind"] == "HIGH" for r in bad)}, LOW {sum(r["kind"] == "LOW" for r in bad)}); '
          f'explained {len(explained)} ({dict(collections.Counter(r["why"] for r in explained))}); '
          f'walls where the source walks {len(walls)} (unexplained {sum(not r.get("why") for r in walls)})')
    for (c, kind), n in sorted(by.items()):
        ex = [r for r in bad if r['c'] == c and r['kind'] == kind]
        ds = sorted({round(r['d']) for r in ex})
        tiles = ' '.join(f'({r["x"]},{r["z"]})' for r in ex[:6]) + (' ...' if len(ex) > 6 else '')
        print(f'  {kind_of[c]} {c} {names.get(c, "?")}: {kind} {n} tiles, by {ds[0]}..{ds[-1]}: {tiles}')
    if listing:
        for r in sorted(explained + walls, key=lambda r: (r['c'], r['z'], r['x'])):
            print(f'  ({r["why"] or "unexplained"}) {r["kind"]} {r["c"]} ({r["x"]},{r["z"]}) level {r["level"]} '
                  f'height {r["height"]} plates {r["plates"]} layers {r["layers"]}')
    if out_json:
        json.dump(rows, open(out_json, 'w'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
