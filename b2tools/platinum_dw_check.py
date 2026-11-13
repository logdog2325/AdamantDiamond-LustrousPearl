"""The Distortion World's engine against Platinum, floor by floor, offline (notes/PLATINUM_DW.md "The harness").

    python3 b2tools/platinum_dw_check.py [FLOOR...]     every floor with faces, or the named ones (B1F, B4F, ...)
    python3 b2tools/platinum_dw_check.py --camera       the camera only: Platinum's eye against Black 2's, every angle
    python3 b2tools/platinum_dw_check.py --boulder      (plat-dw-finish) the boulder puzzle of B5F and B6F: Platinum's push
                                                        test and falling boulder against dw_core.c (platinum_dw_host/
                                                        boulder.sh): every push near the floors, every fall, frame by frame

Routes come from Platinum's tables (b2tools/platinum_dw_data.py): onto each face by each jump point that leads there, across the
face by its grid (a breadth-first search over the tiles Platinum lets you stand on) to each jump point that leads off,
and over the land to every camera trigger of the floor, pressing its direction. b2tools/platinum_dw_host/run.sh runs them
on Platinum's own C (copied from pokeplatinum) and on the overlay's dw_core.c, and every frame must be the same. The land
is free to walk in both (on the DS it is Black 2's own); everything on a platform, the jumps and the camera is the rules'.
"""
import json, math, os, struct, subprocess, sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import platinum_dw_data as platinum_dw  # noqa: E402

STEP = {  # player_move.c sDistortionStepDirection*: by state (kind), input dir -> world delta
    0: [(0, 0, -1), (0, 0, 1), (-1, 0, 0), (1, 0, 0)],
    1: [(0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
    2: [(0, 1, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1)],
    3: [(0, 0, 1), (0, 0, -1), (-1, 0, 0), (1, 0, 0)],
    4: [(0, 0, -1), (0, 0, 1), (-1, 0, 0), (1, 0, 0)],          # the land
}
DIR_CH = 'UDLR'
TWICE = (0x5a, 0x5b, 0x5c, 0x5d)       # TILE_BEHAVIOR_JUMP_NORTH_TWICE .. EAST: by direction
# InitPersistedData's moving platform flags: B4F_1 and B5F_1, and from B7F every elevator but B3F_2's, B4F_3's, B5F_3's
INITIAL_FLAGS = (1 << 3) | (1 << 7)
INITIAL_FLAGS_B7F = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 7) | (1 << 9) | (1 << 10)
OUT = os.environ.get('DW_HOST_OUT', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'platinum_dw_host'))


def inside(b, x, y, z):
    return b['x'] <= x <= b['x'] + b['sx'] and b['y'] <= y <= b['y'] + b['sy'] and b['z'] <= z <= b['z'] + b['sz']


def attr_at(t, p, x, y, z):
    return t['grids'][p['attr']][platinum_dw.grid_index(p, x, y, z)]


def walkable(t, f, plat, x, y, z):
    p = f['platforms'][plat]
    return inside(p['bounds'], x, y, z) and not (attr_at(t, p, x, y, z) & 0x8000)


def neighbours(t, f, plat, tile):
    """The face's steps from a tile, as the rules allow them: in the bounds and free on the current platform, and on a
    floor also onto another floor platform that holds the tile (PlayerAvatar_SetMovement_DistortionFloor's look)."""
    kind = f['platforms'][plat]['kind']
    out = []
    for d, (dx, dy, dz) in enumerate(STEP[kind]):
        x, y, z = tile[0] + dx, tile[1] + dy, tile[2] + dz
        if kind == 0 and walkable(t, f, plat, x, y, z) and \
                attr_at(t, f['platforms'][plat], x, y, z) & 0xff == TWICE[d]:
            # PlayerAvatar_WillJumpTwiceDistortion: MOVEMENT_ACTION_JUMP_DISTORTION_WORLD, three tiles on
            out.append((d, plat, (tile[0] + 3 * dx, tile[1], tile[2] + 3 * dz)))
            continue
        if walkable(t, f, plat, x, y, z):
            out.append((d, plat, (x, y, z)))
        elif kind == 0 and not inside(f['platforms'][plat]['bounds'], x, y, z):
            for k, q in enumerate(f['platforms']):
                if k != plat and q['kind'] == 0 and walkable(t, f, k, x, y, z):
                    out.append((d, k, (x, y, z)))
                    break
    return out


def jump_land(j):
    b = j['bounds']
    return (b['x'] + j['disp'][0], b['y'] + j['disp'][1], b['z'] + j['disp'][2])


def platform_of(f, tile):
    for k, p in enumerate(f['platforms']):
        if inside(p['bounds'], *tile):
            return k
    return None


def search(t, f, plat, start):
    """Breadth-first over the faces from a platform's tile: the face steps, and the jumps from face to face. Returns
    {(platform, tile): tokens}."""
    seen = {(plat, start): None}
    q = deque([(plat, start)])
    paths = {}
    while q:
        node = q.popleft()
        cp, ct = node
        path = []
        n = node
        while seen[n] is not None:
            n, tok = seen[n]
            path.append(tok)
        paths[node] = ''.join(reversed(path))
        steps = [('+' + DIR_CH[d], (np, nt)) for d, np, nt in neighbours(t, f, cp, ct)]
        for j in f['jumps']:
            jt = (j['bounds']['x'], j['bounds']['y'], j['bounds']['z'])
            if jt == ct and j['platform'] is not None and inside(f['platforms'][cp]['bounds'], *jt):
                steps.append(('+' + DIR_CH[j['dir']], (j['platform'], jump_land(j))))
        for tok, nxt in steps:
            if nxt not in seen:
                seen[nxt] = (node, tok)
                q.append(nxt)
    return paths


def land_walk(frm, to):
    """Manhattan tokens on the free land (x first, then z)."""
    out = []
    dx, dz = to[0] - frm[0], to[2] - frm[2]
    out += ['+' + ('R' if dx > 0 else 'L')] * abs(dx)
    out += ['+' + ('D' if dz > 0 else 'U')] * abs(dz)
    return ''.join(out)


def press_camera(tokens, here, c):
    """Walk to a camera trigger's tile and press its direction until the player steps on: (tokens, the tile after)."""
    ct = (c['bounds']['x'], c['bounds']['y'], c['bounds']['z'])
    d = STEP[4][c['dir']]
    return tokens + land_walk(here, ct) + '+' + DIR_CH[c['dir']], (ct[0] + d[0], ct[1], ct[2] + d[2])


def face_tiles(t, f, pk):
    b = f['platforms'][pk]['bounds']
    return [(x, y, z) for x in range(b['x'], b['x'] + b['sx'] + 1) for y in range(b['y'], b['y'] + b['sy'] + 1)
            for z in range(b['z'], b['z'] + b['sz'] + 1) if walkable(t, f, pk, x, y, z)]


def routes_for(t, f):
    """Routes of one floor: (name, start tile in Platinum's world, face, tokens)."""
    out = []
    tile = lambda b: (b['bounds']['x'], b['bounds']['y'], b['bounds']['z'])
    land_cams = [c for c in f['cameras'] if platform_of(f, tile(c)) is None]
    # (a tile can be in two platforms' bounds: B2F's wall top is in a floor platform's too)
    goals = [('jump', k, pk, tile(j), j['dir']) for k, j in enumerate(f['jumps'])
             for pk, p in enumerate(f['platforms']) if inside(p['bounds'], *tile(j))]
    goals += [('camera', k, pk, tile(c), c['dir']) for k, c in enumerate(f['cameras'])
              for pk, p in enumerate(f['platforms']) if inside(p['bounds'], *tile(c))]
    entries = [(k, j) for k, j in enumerate(f['jumps']) if j['platform'] is not None and platform_of(f, tile(j)) is None]
    for ek, e in entries:
        d = STEP[4][e['dir']]
        start = (e['bounds']['x'] - 2 * d[0], e['bounds']['y'], e['bounds']['z'] - 2 * d[2])
        approach = ''.join('+' + DIR_CH[e['dir']] for _ in range(3))
        paths = search(t, f, e['platform'], jump_land(e))
        for what, k, gp, gt, gd in goals:
            if (gp, gt) not in paths:
                continue
            tokens = approach + paths[(gp, gt)] + '+' + DIR_CH[gd]
            if what == 'jump' and f['jumps'][k]['platform'] is None:
                # off onto the land: then to the camera triggers at that height, pressing their directions
                here = jump_land(f['jumps'][k])
                for c in land_cams:
                    if c['bounds']['y'] == here[1]:
                        tokens, here = press_camera(tokens, here, c)
            out.append((f"{f['name']}-in{ek}-{what}{k}-p{gp}", start, e['dir'], tokens))
    # the floor platforms' double jumps, standing on the platform (as a saved game restores it: InitPlayer): each
    # tile before one, pressing its way
    for pk, p in enumerate(f['platforms']):
        if p['kind'] != 0:
            continue
        b = p['bounds']
        for x in range(b['x'], b['x'] + b['sx'] + 1):
            for z in range(b['z'], b['z'] + b['sz'] + 1):
                if not walkable(t, f, pk, x, b['y'], z):
                    continue
                for d, (dx, dy, dz) in enumerate(STEP[0]):
                    n = (x + dx, b['y'], z + dz)
                    if inside(b, *n) and attr_at(t, p, *n) & 0xff == TWICE[d] and not attr_at(t, p, *n) & 0x8000:
                        out.append((f"{f['name']}-p{pk}-twice-{x}-{z}-{DIR_CH[d]}", (x, b['y'], z), d,
                                    '+' + DIR_CH[d] + '+' + DIR_CH[d], pk))
    # surfing on each face's water (the B4F ceiling's sea): from each water tile, across the water to every other
    for pk, p in enumerate(f['platforms']):
        water = [tl for tl in face_tiles(t, f, pk) if attr_at(t, p, *tl) & 0xff == 0x15]
        if water:
            paths = search(t, f, pk, water[0])
            far = [tl for tl in water if (pk, tl) in paths]
            for k, tl in enumerate(far[1::max(1, len(far) // 6)]):
                out.append((f"{f['name']}-p{pk}-surf{k}", water[0], 0, paths[(pk, tl)], pk, 1))
    # the elevators that stand on a fresh visit (InitPersistedData's flags): step on from the west, ride, step off
    flags = INITIAL_FLAGS_B7F if f['name'] == 'B7F' else INITIAL_FLAGS
    for k, m in enumerate(f['moving_platforms']):
        if m['elevator_dir'] in (0, 1) and (m['flag'] is None or flags & (1 << m['flag'])):
            out.append((f"{f['name']}-elevator{k}", (m['x'] - 1, m['y'], m['z']), 3, '+R+R+R'))
    # the land's camera triggers by height, each pressed twice over (so each finds the camera elsewhere once)
    for y in sorted({c['bounds']['y'] for c in land_cams}):
        group = [c for c in land_cams if c['bounds']['y'] == y]
        here = start = tile(group[0])
        tokens = ''
        for c in group + group:
            tokens, here = press_camera(tokens, here, c)
        out.append((f"{f['name']}-land-cameras-{y}", start, group[0]['dir'], tokens))
    return out


def coverage(f, trace_lines):
    """Which jump points and camera triggers the routes pressed (a token's tile before it and its direction)."""
    jumps, cams = set(), set()
    for line in trace_lines:
        if line.startswith('pre ('):
            a = line[5:line.index(')')].split(',')
            x, y, z = (int(v) for v in a)
            d = int(line.split('dir ')[1].split()[0])
            if ' map ' in line and int(line.split(' map ')[1]) != f['map']:
                continue
            for k, j in enumerate(f['jumps']):
                if j['dir'] == d and inside(platinum_dw.local(f, j['bounds']), x, y, z):
                    jumps.add(k)
            for k, c in enumerate(f['cameras']):
                if c['dir'] == d and inside(platinum_dw.local(f, c['bounds']), x, y, z):
                    cams.add(k)
    return jumps, cams


# ---- the camera: Platinum's eye against Black 2's (both with the DS's own sine table, Black 2's arm9)

def sine_table():
    arm9 = open(os.path.join(ROOT, 'external', 'pokebw2', 'extract', 'b2_us', 'arm9', 'arm9.bin'), 'rb').read()
    head = struct.pack('<4h', 0, 4096, 6, 4096)
    i = arm9.find(head)
    assert i >= 0, 'arm9: no FX_SinCosTable_'
    return struct.unpack_from('<8192h', arm9, i)


def fx_mul(a, b):
    return (a * b + 0x800) >> 12


def camera_check(t):
    tab = sine_table()
    sin = lambda a: tab[((a & 0xffff) >> 4) * 2]     # FX_SinIdx
    cos = lambda a: tab[((a & 0xffff) >> 4) * 2 + 1]
    base = (-10750) & 0xffff
    distance = 0x29AEC1
    rows = []
    worst = 0.0
    angles = {(0, 0, 0)}
    for f in t['floors']:
        for c in f['cameras']:
            angles.add(tuple(c['angle']))
    for a in sorted(angles):
        ax = (base + a[0] * 256) & 0xffff
        ay = (a[1] * 256) & 0xffff
        # camera.c Camera_AdjustPositionAroundTarget
        p = (fx_mul(fx_mul(sin(ay), distance), cos(ax)), fx_mul(sin((-ax) & 0xffff), distance),
             fx_mul(fx_mul(cos(ay), distance), cos(ax)))
        # field_camera.c FieldCameraApply_TransRot with dw_core.c's pitch = -x, yaw = y
        pitch = (0x10000 - ax) & 0xffff
        cp = cos(pitch)
        cp = -cp if cp < 0 else cp
        clamped = cp < 0x200
        cp = max(cp, 0x200)
        d = (fx_mul(sin(ay), cp), sin(pitch), fx_mul(cos(ay), cp))
        n1 = math.sqrt(sum(v * v for v in p))
        n2 = math.sqrt(sum(v * v for v in d))
        dot = sum(u * v for u, v in zip(p, d)) / (n1 * n2)
        err = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
        worst = max(worst, err)
        total = ((ax + 0x8000) & 0xffff) - 0x8000
        rows.append((a, total, pitch, err, clamped, p[1] < 0))
    return rows, worst


def main():
    t = platinum_dw.read_tables()
    if '--boulder' in sys.argv:                         # (plat-dw-finish)
        r = subprocess.run([os.path.join(HERE, 'platinum_dw_host', 'boulder.sh')] + (['-v'] if '-v' in sys.argv else []),
                           timeout=600)
        return r.returncode
    if '--camera' in sys.argv:
        rows, worst = camera_check(t)
        for a, total, pitch, err, clamped, below in rows:
            print(f'angles {a}: Platinum x {total} ({total * 360 / 65536:+.1f} deg), Black 2 pitch {pitch:#06x}; '
                  f'eye {"below" if below else "above"} the player; directions {err:.3f} deg apart'
                  f'{"; CLAMPED" if clamped else ""}')
        print(f'camera: {len(rows)} angles, the worst {worst:.3f} deg apart')
        return 0 if worst < 0.2 and not any(r[4] for r in rows) else 1
    names = [a for a in sys.argv[1:] if not a.startswith('-')]
    floors = [f for f in t['floors'] if (f['jumps'] or f['cameras'] or f['moving_platforms']) and
              (not names or f['name'] in names)]
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'routes.txt')
    all_routes = []
    with open(path, 'w') as fh:
        for f in floors:
            for name, start, face, tokens, *plat in routes_for(t, f):
                on = ' ' + ' '.join(str(v) for v in plat) if plat else ''
                # each route walking and again running (B held: the runs of every face, 121-132, and the floor's)
                for suffix, toks in (('', tokens), ('-run', tokens.lower() if 'surf' not in name else None)):
                    if toks is None:
                        continue
                    all_routes.append((f, name + suffix))
                    fh.write(f'route {name}{suffix} {f["map"]} {start[0]} {start[1]} {start[2]} {face}{on}\n'
                             f'tokens {toks}\n')
    trace = os.path.join(OUT, 'trace.txt')
    env = dict(os.environ, DW_HOST_OUT=OUT)
    r = subprocess.run([os.path.join(HERE, 'platinum_dw_host', 'run.sh'), path, trace], env=env, text=True,
                       capture_output=True, timeout=600)
    print(r.stdout + (r.stderr[-3000:] if r.returncode not in (0, 1) else ''), end='')
    lines = open(trace).read().split('\n') if os.path.exists(trace) else []
    # coverage per floor
    blocks = {}
    cur = None
    for line in lines:
        if line.startswith('== '):
            cur = line.split()[1]
            blocks[cur] = []
        elif cur:
            blocks[cur].append(line)
    for f in floors:
        mine = [ln for name, ls in blocks.items() if name.startswith(f['name'] + '-') for ln in ls]
        jumps, cams = coverage(f, mine)
        planes = sorted({ln.strip() for ln in mine if ln.strip().startswith('plane:')})
        twice = sum(1 for ln in mine if any(f' action {a} ' in ln for a in (117, 118, 119, 120)))
        rides = [ln.strip() for ln in mine if ln.strip().startswith('elevator to')]
        print(f"{f['name']}: jump points pressed {len(jumps)}/{len(f['jumps'])}, camera triggers pressed "
              f"{len(cams)}/{len(f['cameras'])}, double jumps {twice}, elevator rides {len(rides)}; planes "
              f"{', '.join(p[7:] for p in planes)}")
    return r.returncode


if __name__ == '__main__':
    sys.exit(main())
