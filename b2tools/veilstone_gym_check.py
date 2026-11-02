"""Offline reach check of Pearl's Veilstone Gym panels (b2tools/pearl_veilstone_gym.py):

    python3 b2tools/veilstone_gym_check.py        map, panels, reach from the door to Maylene; exit 1 if it fails
    python3 b2tools/veilstone_gym_check.py steps  the solve as story_play.py commands, a line per push

A walk over (the 12 panel bits, the player's tile), from the Gym's door in the panels' start states: Pearl's collision
(work/pearl/land), the panels' spans of the state (ov06_022426F4), the people, and the pushes (ov06_0224249C: on a push
spot, facing the panel at its near place: the bit flips, the player walks one tile that way). Prints the shortest solve.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import pearl_veilstone_gym as g  # noqa: E402

CHUNK, ZONE = 234, 'MAP_VEILSTONE_GYM'
DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}


def load():
    collision = json.load(open(os.path.join(ROOT, 'work', 'pearl', 'land', f'{CHUNK:03d}.json')))['collision']
    zs = {z['name']: z for z in json.load(open(os.path.join(ROOT, 'work', 'pearl', 'zones.json')))}
    ev = json.load(open(os.path.join(ROOT, 'work', 'pearl', 'events', f'{zs[ZONE]["events"]:03d}.json')))
    return collision, ev


def solve():
    """The shortest way; returns (the moves [(direction, push or None)], goal state, the number of states seen)."""
    collision, ev = load()
    panels = g.panels()
    spots = {}
    for x, z, f, i in g.push_spots():
        spots.setdefault((x, z), []).append(('left' if f == 2 else 'right', i))
    people = {(o['x'], o['z']) for o in ev['object_events']}
    maylene = next(o for o in ev['object_events'] if o['id'] == 0)
    goals = {(maylene['x'] + dx, maylene['z'] + dz) for dx, dz in DIRS.values()}
    start = (tuple(p['start'] for p in panels), (12, 24))
    door = ev['warp_events'][0]
    start = (start[0], (door['x'], door['z'] - 1))
    solids = {}

    def solid(state):
        if state not in solids:
            solids[state] = g.solid(state)
        return solids[state]

    def free(state, x, z):
        return (0 <= x < 32 and 0 <= z < 32 and not collision[z][x] and (x, z) not in solid(state)
                and (x, z) not in people)

    before = {start: None}
    q = collections.deque([start])
    while q:
        cur = q.popleft()
        state, (x, z) = cur
        if (x, z) in goals:
            moves = []
            while before[cur] is not None:
                cur, d, why = before[cur]
                moves.append((d, why))
            return moves[::-1], state, len(before)
        for d, (dx, dz) in DIRS.items():
            if free(state, x + dx, z + dz):
                nxt = (state, (x + dx, z + dz))
                if nxt not in before:
                    before[nxt] = (cur, d, None)
                    q.append(nxt)
        for d, i in spots.get((x, z), []):
            p = panels[i]
            at_near = state[i] == 1 if d == 'left' else state[i] == 0
            if not at_near:
                continue
            new = state[:i] + (1 - state[i],) + state[i + 1:]
            dx, dz = DIRS[d]
            assert free(new, x + dx, z + dz), f'panel {i} from {(x, z)} {d}: the player walks into a wall'
            nxt = (new, (x + dx, z + dz))
            if nxt not in before:
                before[nxt] = (cur, d, (x, z, d, i))
                q.append(nxt)
    return None, None, len(before)


def draw(state):
    collision, ev = load()
    sol = g.solid(state)
    who = {(o['x'], o['z']): ('M' if o['id'] == 0 else 'G' if o['id'] == 1 else 'T') for o in ev['object_events']}
    spots = {(x, z) for x, z, *_ in g.push_spots()}
    print('   ' + ''.join(str(x // 10) for x in range(26)))
    print('   ' + ''.join(str(x % 10) for x in range(26)))
    for z in range(28):
        print(f'{z:2d} ' + ''.join(
            who.get((x, z)) or ('P' if (x, z) in sol else '#' if collision[z][x] else '+' if (x, z) in spots else '.')
            for x in range(26)))


def main():
    panels = g.panels()
    start = tuple(p['start'] for p in panels)
    draw(start)
    moves, state, seen = solve()
    if moves is None:
        print(f'NO WAY to Maylene ({seen} states)')
        return 1
    pushes = [why for _, why in moves if why]
    print(f'reached Maylene in {len(pushes)} pushes, {len(moves)} moves ({seen} states seen):')
    for x, z, d, i in pushes:
        print(f'  on ({x}, {z}) push {d}: panel {i} ({panels[i]["model"]})')
    if sys.argv[1:] == ['steps']:
        cmds, run = [], []

        def flush():
            for d, n in run:
                cmds.append(f'STEP{d[0].upper()}{n}')
            run.clear()
        for d, why in moves:
            if why:
                flush()
                print(' '.join(cmds) + f' {"PUSH" + d[0].upper()}:{why[3]}')
                cmds.clear()
            elif run and run[-1][0] == d:
                run[-1][1] += 1
            else:
                run.append([d, 1])
        flush()
        print(' '.join(cmds))
    draw(state)
    return 0


if __name__ == '__main__':
    sys.exit(main())
