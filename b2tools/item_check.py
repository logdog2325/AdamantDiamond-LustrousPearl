"""Offline check of Pearl's items in the world (no ROM, no emulator): notes/OPEN_CONTENT.md "Items, TMs, shops".

    python3 item_check.py [--list]         --list prints every finding's item too

1. The counts: every ball object and hidden BG event of Pearl's data is installed by pearl_events.entities in a zone
   with a generated script file; each ball a person with Black 2's item-ball sprite and script 7000+n, each hidden item
   a sign of condition 2 and script 8000+n.
2. The flags: a ball's flag is Pearl's flag through the registry, in Black 2's item-ball flags (1100-1499) and shared
   only by balls of one script; a hidden item's flag is 2820 + n (the decomp's rule; Platinum's 256-283: pearl_items.hidden_flag).
3. The scripts: src/field_scripts/1240, 1241 and their text are what pearl_items.py writes now, and they assemble.
4. Reachable: from the player's room, through the walkable tiles (Pearl's collision: water counts, as Surf), every warp
   that can be set off, every Warp of Pearl's scripts (as warp_check.py) and every Rock Climb lane, the player gets
   next to every ball and hidden item (a ball is talked to and a hidden item found from the next tile).
5. The items: each exists in Black 2 under Pearl's name, or is listed under "substitutions".
6. The zones: at most 64 people (Black 2's actor pool less the player and the follower), 30 sprites.
7. The shops: Pearl's lists -> shop lists (patches/pearl_shops.py), every clerk's list number in range, no clerk left
   on the old stand-in.
"""
import collections, glob, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402
sys.path.insert(0, os.path.join(HERE, 'patches'))
import pearl_events, pearl_ids, pearl_items, pearl_story, scripts as scripts_patch, warp_check  # noqa: E402
import pearl_shops, sinnoh_story  # noqa: E402
from patches import sinnoh_events  # noqa: E402

ITEM_BALL_CODE = 110
ACTOR_LIMIT = 62                          # ov012 FldActSys_Create(heap, 64), the player and the follower take two
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))
LEDGES = {0x38: (1, 0), 0x39: (-1, 0), 0x3a: (0, -1), 0x3b: (0, 1)}     # Pearl's JUMP_EAST / WEST / NORTH / SOUTH
PASS = {0x13, 0xd7, 0xd8, 0xd9, 0xda}   # solid tiles a field move or the Bike crosses: waterfalls, bike ramps and slopes
MANY_ZONES = ('MAP_GREAT_MARSH_AREA_',)
# Pearl's items Black 2 has under another name on the same id. The Mail: Pearl's 12 designs are Black 2's 12 Mail slots
# (137-148), usable as Mail, not Pearl's designs. The rest: spelling
SPELLED = {'X Defend': 'X Defense', 'Grass Mail': 'Greet Mail', 'Flame Mail': 'Favored Mail', 'Bubble Mail': 'RSVP Mail',
           'Bloom Mail': 'Thanks Mail', 'Tunnel Mail': 'Inquiry Mail', 'Steel Mail': 'Like Mail', 'Heart Mail': 'Reply Mail',
           'Snow Mail': 'BridgeMail S', 'Space Mail': 'BridgeMail D', 'Air Mail': 'BridgeMail T'}
# Items the graph can't connect, on Pearl's own tiles (the check's question is whether the port broke something)
ACCEPT_REACH = {7203: "Victory Road 2F's west ring has no warp, and its walls and one 0xD7 tile (10,10) are Pearl's tiles: "
                      "how Pearl gets there isn't modelled (BDHC heights: notes/OPEN_CONTENT.md Map details)"}


def b2_names():
    """{Black 2 item id: name} from the decomp's res/items (its item order: the a/0/2/4 records' names in text)."""
    root = os.path.join(ROOT, 'external', 'pokebw2')
    sys.path.insert(0, os.path.join(HERE))
    out = {}
    names = os.path.join(root, 'build', 'include', 'generated', 'constants', 'items.h')
    order = {}
    if os.path.exists(names):
        for m in re.finditer(r'#define ITEM_(\w+)\s+(\d+)', open(names).read()):
            order[m.group(1).lower()] = int(m.group(2))
    for p in glob.glob(os.path.join(root, 'res', 'items', '*', 'data.json')):
        key = os.path.basename(os.path.dirname(p))
        if key in order:
            out[order[key]] = json.load(open(p)).get('name')
    return out


class World:
    """The whole game's tiles as one graph: (place, x, z); place 'O' = the overworld (matrix 0), else a Black 2 zone."""

    def __init__(self):
        self.W = W = warp_check.Warps('offline')
        W.any_over = None
        self.over = {b2 for b2, pid in self.W.pid_of.items() if self.W.zones[pid]['matrix'] == 0}
        self.any_over = W.any_over = next(iter(self.over))
        self.exits = collections.defaultdict(list)     # (place, x, z) of the tile a warp fires from -> arrival nodes
        for b2, ws in self.W.warps.items():
            for i, w in enumerate(ws):
                if w['x'] >= warp_check.OFF_MAP or w['dest_warp'] == sinnoh_events.INERT:
                    continue
                x, z = self.W.at(w)
                dz, dw = w['dest_zone'], w['dest_warp']
                a = self.W.arrival(dz, dw) if dw != sinnoh_events.DEST_NEXT_ZONE else None
                if a is None or dz not in self.W.pid_of:
                    continue
                # (a warp is set off from its own tile or the next one: how, warp_check.py checks)
                for s in [(x, z)] + [(x + dx, z + dz) for dx, dz in SIDES]:
                    self.exits[(self.place(b2),) + s].append((self.place(dz),) + a)

    def place(self, b2):
        if b2 in self.over:
            return 'O'
        pid = self.W.pid_of[b2]
        z = self.W.zones[pid]
        if z['name'].startswith(MANY_ZONES):    # (one map, a zone a part: walked across)
            return next(k for k, v in self.W.pid_of.items() if self.W.zones[v]['matrix'] == z['matrix']
                        and self.W.zones[v]['name'].startswith(MANY_ZONES))
        return b2

    def walkable(self, place, x, z):
        return self.W.walkable(self.any_over if place == 'O' else place, x, z)

    def reached(self):
        """Every tile connected to the player's room: the game's graph, but undirected (a ledge or a warp counts both ways):
        the balls stand where Pearl has them, on Pearl's collision, so this asks whether the world connects them,
        not in which story order they can be got (Strength rocks, Rock Smash, Pearl's one-way ledges)."""
        W = self.W
        starts = []
        twin = W.b2_of[next(i for i, z in enumerate(W.zones) if z['name'] == 'MAP_TWINLEAF_RIVAL_HOUSE_2F')]
        starts.append((twin, 4, 6))
        # Pearl's scripts' warps: boats, the Great Marsh, the League. A zone they name counts as entered: at the tile they
        # name, else (a var) at each warp of the zone
        script_warps = re.compile(r'\bWarp (0x[0-9A-Fa-f]+|\d+), \w+, (\w+), (\w+), ')
        for f in os.listdir(os.path.join(version.WORLD_WORK, 'scripts')):
            for m in script_warps.finditer(open(os.path.join(version.WORLD_WORK, 'scripts', f)).read()):
                b2 = W.b2_of.get(int(m.group(1), 0))
                if b2 is None:
                    continue
                if m.group(2)[0].isdigit() and m.group(3)[0].isdigit():
                    starts.append((self.place(b2), int(m.group(2), 0), int(m.group(3), 0)))
                else:
                    starts += [(self.place(b2),) + W.at(w) for w in W.warps.get(b2, ()) if w['x'] < warp_check.OFF_MAP]
        ships = re.compile(r'\bShipAnimation \w+, \w+, (0x[0-9A-Fa-f]+|\d+), (0x[0-9A-Fa-f]+|\d+), (0x[0-9A-Fa-f]+|\d+)')
        for f in os.listdir(os.path.join(version.WORLD_WORK, 'scripts')):
            for m in ships.finditer(open(os.path.join(version.WORLD_WORK, 'scripts', f)).read()):
                b2 = W.b2_of.get(int(m.group(1), 0))
                if b2 is not None:
                    starts.append((self.place(b2), int(m.group(2), 0), int(m.group(3), 0)))
        back = collections.defaultdict(list)            # a warp's way back: from its arrival to where it fires
        for n, arrivals in self.exits.items():
            for a in arrivals:
                back[a].append(n)
        climbs = collections.defaultdict(list)
        for pid, b2 in W.b2_of.items():
            for r in pearl_events.rock_climb_ends(W.zones[pid]['name']):
                climbs[(self.place(b2),) + tuple(r['stand'])].append((self.place(b2),) + tuple(r['land']))
        seen, todo = set(), [s for s in starts if self.walkable(*s)]
        todo += [(p, x + dx, z + dz) for p, x, z in starts if not self.walkable(p, x, z) for dx, dz in SIDES
                 if self.walkable(p, x + dx, z + dz)]
        while todo:
            n = todo.pop()
            if n in seen:
                continue
            seen.add(n)
            place, x, z = n
            for dx, dz in SIDES:
                q = (place, x + dx, z + dz)
                if q in seen:
                    continue
                if self.walkable(*q):
                    todo.append(q)
                    continue
                t = W.tile(W.any_over if place == 'O' else place, *q[1:])
                if t is None:
                    continue
                if t[0] in PASS:
                    todo.append(q)
                elif t[0] in LEDGES and LEDGES[t[0]] in ((dx, dz), (-dx, -dz)):      # over a ledge (see reached())
                    land = (place, q[1] + dx, q[2] + dz)
                    if self.walkable(*land):
                        todo.append(land)
            for a in self.exits.get(n, ()):
                # (an arrival on a mat the converter made solid steps out to the tile beside it)
                todo.extend([a] if self.walkable(*a) else [(a[0], a[1] + dx, a[2] + dz) for dx, dz in SIDES
                                                           if self.walkable(a[0], a[1] + dx, a[2] + dz)])
            todo.extend(a for a in climbs.get(n, ()) if a not in seen)
            todo.extend(a for a in back.get(n, ()) if a not in seen and self.walkable(*a))
        return seen


def main(argv):
    pd = pearl_story.PearlData()
    ids = pearl_ids.Ids()
    heights = pearl_events.Heights()
    bad = collections.Counter()
    lines = []

    def report(kind, msg):
        bad[kind] += 1
        lines.append(f'({kind}) {msg}')

    gen_s, _ = sinnoh_story.generated()
    rows = pearl_items.world()
    print(f"Pearl's data: {sum(r['kind'] == 'ball' for r in rows)} ball objects "
          f"({len({r['script'] for r in rows if r['kind'] == 'ball'})} scripts), "
          f"{sum(r['kind'] == 'hidden' for r in rows)} hidden BG events "
          f"({len({r['script'] for r in rows if r['kind'] == 'hidden'})} scripts); "
          f"{len(pearl_items.hidden_items())} records in Pearl's hidden-item table")

    # every zone that uses each events file (rows are per events file)
    zones_of = collections.defaultdict(list)
    for z in pd.zones:
        zones_of[z['events']].append(z)
    installed = collections.Counter()
    actors, sprites = {}, {}
    for events, zs in zones_of.items():
        ev = pd.events(zs[0])
        if not any(pearl_events.script_kind(o['script']) == 'item' for o in ev['object_events']) and \
           not any(pearl_events.script_kind(b['script']) == 'hidden' for b in ev['bg_events']):
            continue
        live = [z for z in zs if pd.b2_zone.get(z['id']) is not None and pd.script_file(z) in gen_s]
        if not live:
            for o in ev['object_events']:
                if pearl_events.item_ball(zs[0], o):
                    report('zone', f'{zs[0]["name"]}: ball object {o["id"]}: its zone is not installed')
            for b in ev['bg_events']:
                if pearl_events.script_kind(b['script']) == 'hidden':
                    report('zone', f'{zs[0]["name"]}: hidden item at ({b["x"]},{b["z"]}): its zone is not installed')
            continue
        z = live[0]
        npcs, signs, _, _ = pearl_events.entities(pd, z, ids, heights, lambda s: sinnoh_story.script_id(pd, ids, s))
        actors[z['name']] = len(npcs)
        sprites[z['name']] = len({n['model'] for n in npcs})
        for o in ev['object_events']:
            if not pearl_events.item_ball(z, o):
                continue
            match = [n for n in npcs if n['uid'] == o['id'] and n['script'] == o['script']]
            if len(match) != 1 or match[0]['model'] != ITEM_BALL_CODE or match[0]['flag'] != ids.flag_value(o['hidden_flag']):
                report('install', f'{z["name"]}: ball object {o["id"]} script {o["script"]}: {match}')
            else:
                installed['ball'] += 1
            if heights.at(z, o['x'], o['z'], near=o['y'] * 16) is None:
                report('height', f'{z["name"]}: ball object {o["id"]} at ({o["x"]},{o["z"]}): no map height')
        for b in ev['bg_events']:
            if pearl_events.script_kind(b['script']) != 'hidden':
                continue
            match = [s for s in signs if s['script'] == b['script'] and s['x'] == b['x'] and s['z'] == b['z']]
            if len(match) != 1 or match[0]['cond'] != 2:
                report('install', f'{z["name"]}: hidden item script {b["script"]}: {match}')
            else:
                installed['hidden'] += 1
            if heights.sign_y(z, b['x'], b['z'], b['player_facing_dir']) is None:
                report('height', f'{z["name"]}: hidden item at ({b["x"]},{b["z"]}): no map height')
    print(f'installed: {installed["ball"]} balls, {installed["hidden"]} hidden items')

    # flags
    by_flag = collections.defaultdict(set)
    for r in rows:
        by_flag[r['flag']].add(r['script'])
        if r['kind'] == 'ball' and not 1100 <= r['flag'] <= 1499:
            report('flag', f'{r["zone"]} ball script {r["script"]}: flag {r["flag"]} outside 1100-1499')
        if r['kind'] == 'hidden' and r['flag'] != pearl_items.hidden_flag(r['script'] - 8000):
            report('flag', f'{r["zone"]} hidden script {r["script"]}: flag {r["flag"]} is not the field\'s (pearl_items.hidden_flag)')
    for f, s in by_flag.items():
        if len(s) > 1:
            report('flag', f'flag {f} is shared by scripts {sorted(s)}')
    print(f'flags: {len(by_flag)} (balls {min(r["flag"] for r in rows if r["kind"] == "ball")}-'
          f'{max(r["flag"] for r in rows if r["kind"] == "ball")}, hidden '
          f'{min(r["flag"] for r in rows if r["kind"] == "hidden")}-{max(r["flag"] for r in rows if r["kind"] == "hidden")})')

    # scripts
    outs, _ = pearl_items.outputs()
    for p, text in outs.items():
        if not os.path.exists(p) or open(p, encoding='utf-8').read() != text:
            report('script', f'{os.path.relpath(p, ROOT)}: out of date (python3 b2tools/pearl_items.py)')
        elif p.endswith('.s'):
            print(f'{os.path.basename(p)}: {len(scripts_patch.assemble(p))} B')

    # reachable
    W = World()
    seen = W.reached()
    unreached, by_twin, accepted = [], [], []

    def near(r):
        place = W.place(r['b2_zone'])
        return r['b2_zone'] is not None and any((place, r['x'] + dx, r['z'] + dz) in seen for dx, dz in SIDES)

    twins = collections.defaultdict(list)                # a script on two maps (the lakes' two versions, the Old
    for r in rows:                                       # Chateau's twin rooms): one flag, one item, either will do
        twins[r['script']].append(r)
    for r in rows:
        if near(r):
            continue
        if any(near(t) for t in twins[r['script']]):
            by_twin.append(f'{r["zone"]} script {r["script"]}')
            continue
        if r['script'] in ACCEPT_REACH:
            print(f'accepted, NOT proved: {r["zone"]} script {r["script"]}: {ACCEPT_REACH[r["script"]]}')
            accepted.append(r)
            continue
        unreached.append(r)
        report('reach', f'{r["zone"]} ({r["b2_zone"]}): {r["kind"]} script {r["script"]} at ({r["x"]},{r["z"]}), '
                        f'item {r["item"]}: nothing next to it can be walked to')
    print(f'reachable: {len(rows) - len(unreached) - len(accepted) - len(by_twin)} of {len(rows)} directly, '
          f'{len(by_twin)} by their twin on another map of the same place (one flag) {by_twin}, '
          f'{len(accepted)} accepted unproved, {len(unreached)} unreached')

    # items
    names = b2_names()
    import gen4_text
    pn = gen4_text.bank(344)
    subs = {}
    for it in sorted({r['item'] for r in rows} | {i for l in pearl_items.mart_lists() for i in l}
                     | {i for l in pearl_items.mart_special() for i in l}):
        b2 = pearl_items.b2_item(it)
        if b2 != it:
            subs[pn[it]] = (b2, names.get(b2))
        elif names and names.get(b2) not in (pn[it], SPELLED.get(pn[it])) and not pn[it].startswith(('TM', 'HM')):
            report('item', f'item {it}: Pearl {pn[it]!r}, Black 2 {names.get(b2)!r}')
    print(f'substitutions by move (notes/TMS.md): ' + ', '.join(f'{k} = {v[0]}' for k, v in subs.items()))
    print(f'under another name: ' + ', '.join(f'{k} = {v}' for k, v in SPELLED.items()))
    ug = {v['b2'] for k, v in json.load(open(pearl_ids.REGISTRY))['new_flags'].items() if k.startswith('PFLAG_UG_')}
    if ug & set(by_flag):
        report('flag', f'Underground flags {sorted(ug & set(by_flag))} are also Pearl items\'')

    # zones
    for z, n in actors.items():
        if n > ACTOR_LIMIT:
            report('actors', f'{z}: {n} people')
    for z, n in sprites.items():
        if n > sinnoh_story.SPRITE_LIMIT:
            report('sprites', f'{z}: {n} sprites')
    print(f'most people in a zone: {max(actors.values())}; most sprites: {max(sprites.values())}')

    # shops
    lists = pearl_shops.lists()
    print(f'shop lists: {len(lists)}, largest {max(map(len, lists.values()))} items')
    used = set()
    for p in glob.glob(os.path.join(ROOT, 'src', 'field_scripts', '*_pearl_*.s')):
        text = open(p, encoding='utf-8').read()
        for m in re.finditer(r'pl_PokeMartSpecial (\d+)', text):
            used.add(int(m.group(1)))
            if pearl_shops.FIRST_SPECIAL + int(m.group(1)) not in lists:
                report('shop', f'{os.path.basename(p)}: SpecialMart {m.group(1)} past Pearl\'s lists')
        if 'Black 2\'s normal Mart for now' in text:
            report('shop', f'{os.path.basename(p)}: a clerk on the old stand-in (regenerate the zone)')
    print(f'special lists clerks use: {sorted(used)}; no clerk in an installed zone: '
          f'{sorted(set(range(pearl_items.SPECIAL_MART_COUNT)) - used)}')

    print(f'findings: {dict(bad) or "none"}')
    for l in lines:
        print(l)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
