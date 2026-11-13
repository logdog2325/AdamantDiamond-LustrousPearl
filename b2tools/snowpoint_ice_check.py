"""The Snowpoint Gym's ice played offline on the version's converted ground (2026-11-02, plat-gyms; the ch6b agent's
icegym.py, gone, did this for Pearl): can the player reach Candice with gimmick 61's rules?

    python3 b2tools/snowpoint_ice_check.py                 Pearl's Gym
    PEARL_VERSION=platinum python3 b2tools/snowpoint_ice_check.py      Platinum's (its changed ground, its 19 snowballs)

The rules are the decomp's src/pearlb2/snowpoint_gym_itcm.c (Pearl's, pokediamond sub_020560A0 / ov05_021E6904): on ice
(behaviour 0x20) the player slides a tile at a time at a speed 0-3; before each tile the ground a quarter tile ahead
(the tile's own plane, as Black 2 samples it) against the player's height: downhill +1 (at most 3), uphill -1, and
uphill at 0 (or uphill into anything in the way) one step back, after which the slide stops; at speed 1 or more a
snowball in the way breaks (and is gone for the visit); the slide stops at anything in the way and on the first tile
that isn't ice; the one-way tiles 0x49 / 0x4A block moves up-down / left-right into and out of them. People and the
other snowballs block. The ground is the converted model's (pearl_chunk: each tile's plane under its centre), so the
check is of the ground the build installs. Prints the tiles reached, the snowballs that must break, and whether a tile
next to Candice is reached (exit 1 if not).
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'patches'))
import version  # noqa: E402

ZONE = 'MAP_SNOWPOINT_GYM'
ICE = 0x20
SNOWBALL = 0x76
AHEAD = 4.0
FLAT = 1 / 32
SPEED_MAX = 3
DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
MAX_STATES = 2_000_000


def load():
    import pearl_chunk, snowpoint_gym
    zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    z = next(z for z in zones if z['name'] == ZONE)
    m = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', f"{z['matrix']:03d}.json")))
    chunk = m['maps'][0][0]
    land = json.load(open(os.path.join(version.WORLD_WORK, 'land', f'{version.land_id(chunk):03d}.json')))
    ev = json.load(open(os.path.join(version.WORLD_WORK, 'events', f"{z['events']:03d}.json")))
    tris = pearl_chunk.chunk_triangles(chunk)
    planes = {}
    for tz in range(32):
        for tx in range(32):
            s = pearl_chunk.surface(tris, tx * 16 - 256 + 8, tz * 16 - 256 + 8)
            if s is not None:
                planes[(tx, tz)] = s
    (_, blocks), = snowpoint_gym.zones()
    oneway = {(x, zz): a for x, zz, a in blocks}
    balls = [(o['x'], o['z']) for o in ev['object_events'] if o['graphics_id'] == SNOWBALL]
    people = {(o['x'], o['z']): o['graphics_id'] for o in ev['object_events'] if o['graphics_id'] != SNOWBALL}
    entry = next((w['x'], w['z']) for w in ev['warp_events'])
    return dict(chunk=chunk, land=land, planes=planes, oneway=oneway, balls=balls, people=people, entry=entry)


class Gym:
    def __init__(self, g):
        self.g = g
        self.balls = {b: i for i, b in enumerate(g['balls'])}

    def solid(self, x, z):
        return not (0 <= x < 32 and 0 <= z < 32) or self.g['land']['collision'][z][x] or (x, z) in self.g['people']

    def ice(self, x, z):
        return self.g['land']['behaviour'][z][x] == ICE

    def oneway(self, x, z, nx, nz, d):
        axis = 1 if DIRS[d][0] == 0 else 2
        return bool(self.g['oneway'].get((x, z), 0) & axis or self.g['oneway'].get((nx, nz), 0) & axis)

    def blocked(self, x, z, nx, nz, d, broken):
        b = self.balls.get((nx, nz))
        return self.solid(nx, nz) or self.oneway(x, z, nx, nz, d) or (b is not None and not broken >> b & 1)

    def slope(self, x, z, d):
        """+1 the ground a quarter tile ahead is higher, -1 lower, 0 flat (or no ground)."""
        s = self.g['planes'].get((x, z))
        if s is None:
            return 0
        (h, (nx, ny, nz)), (dx, dz) = s, DIRS[d]
        ahead = h - (nx * dx * AHEAD + nz * dz * AHEAD) / ny
        return 1 if ahead > h + FLAT else -1 if ahead < h - FLAT else 0

    def slide(self, x, z, d, broken):
        """Where a new slide from ice tile (x, z) the way d ends, and the snowballs broken: (x, z, broken)."""
        dx, dz = DIRS[d]
        speed = 0
        for _ in range(64):
            nx, nz = x + dx, z + dz
            if speed >= 1 and (nx, nz) in self.balls:
                broken |= 1 << self.balls[(nx, nz)]
            sl = self.slope(x, z, d)
            if self.blocked(x, z, nx, nz, d, broken):
                if sl > 0:
                    return self.step_back(x, z, d, broken)
                return x, z, broken
            if sl > 0:
                if speed == 0:
                    return self.step_back(x, z, d, broken)
                speed -= 1
            elif sl < 0 and speed < SPEED_MAX:
                speed += 1
            x, z = nx, nz
            if not self.ice(x, z):
                return x, z, broken
        raise AssertionError(f'a slide from ({x}, {z}) {d} does not end')

    def step_back(self, x, z, d, broken):
        back = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}[d]
        bx, bz = x + DIRS[back][0], z + DIRS[back][1]
        if self.blocked(x, z, bx, bz, back, broken):
            return x, z, broken
        return bx, bz, broken

    def moves(self, x, z, broken):
        for d, (dx, dz) in DIRS.items():
            nx, nz = x + dx, z + dz
            if self.ice(x, z):                      # standing on ice after a stop: the step is a new slide
                if not self.blocked(x, z, nx, nz, d, broken) or self.slope(x, z, d) > 0:
                    yield self.slide(x, z, d, broken)
                continue
            if self.blocked(x, z, nx, nz, d, broken):
                continue
            if self.ice(nx, nz):
                yield self.slide(nx, nz, d, broken)
            else:
                yield nx, nz, broken


def main():
    g = load()
    gym = Gym(g)
    candice = next(xz for xz, gfx in g['people'].items() if gfx == 131)   # OBJ_EVENT_GFX_CANDICE (both games' 131)
    goal = {(candice[0] + dx, candice[1] + dz) for dx, dz in DIRS.values()}
    start = (g['entry'][0], g['entry'][1] - 1, 0)          # one step in from the door mat
    seen, todo, reached = {start: None}, collections.deque([start]), None
    while todo:
        s = todo.popleft()
        if (s[0], s[1]) in goal:
            reached = s
            break
        for n in gym.moves(*s):
            if n not in seen:
                seen[n] = s
                todo.append(n)
        assert len(seen) < MAX_STATES, 'too many states'
    tiles = {(x, z) for x, z, _ in seen}
    print(f'{version.NAME}: chunk {g["chunk"]}, {len(g["balls"])} snowballs, {sum(map(gym.ice, *zip(*tiles)))} ice tiles '
          f'reached of {sum(gym.ice(x, z) for z in range(32) for x in range(32))}, {len(tiles)} tiles, {len(seen)} states')
    slopes = collections.Counter(gym.slope(x, z, d) for (x, z) in g['planes'] if gym.ice(x, z) for d in DIRS)
    print('  ice slopes (downhill, flat, uphill):', slopes[-1], slopes[0], slopes[1])
    if reached is None:
        print(f'  Candice at {candice}: NOT reached')
        return 1
    path, s = [], reached
    while s is not None:
        path.append(s)
        s = seen[s]
    path.reverse()
    broken = [g['balls'][i] for i in range(len(g['balls'])) if reached[2] >> i & 1]
    print(f'  Candice at {candice}: reached in {len(path) - 1} moves, at {reached[:2]}; snowballs broken on the way: {broken}')
    print('  path:', ' '.join(f'({x},{z})' for x, z, _ in path))
    return 0


if __name__ == '__main__':
    sys.exit(main())
