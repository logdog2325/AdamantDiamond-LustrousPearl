"""Pokémon from Unova (Rowan's sixth question, PFLAG_UNOVA; the user 2026-11-23, notes/DECISIONS.md; notes/UNOVA.md): the
plan in data/unova.json -> each version's slot edits, checked against the rules.

    python3 b2tools/unova.py [--report] [VERSION ...]   the edits by area (all three versions without a VERSION)
    python3 b2tools/unova.py --check                    the rules (exit 1 on a finding)
    python3 b2tools/unova.py --md                       the lists as Markdown (the guide's page, the report)

The rules (the user's, as Hoenn's): Gen 5 only, no legendary or mythical (494, 638-649), no fossil (564-567), no Zorua or
Zoroark, a Unova starter only in its one 1 % slot; 1-3 kinds an area, about a quarter of each kind of encounter (grass
and caves 20-28 %, surfing up to 30 %, Good Rod about 20 %, Super Rod 15-20 %); the Old Rod never changes; every Sinnoh
Pokémon keeps at least one slot in each group it had, at every time of day; no slot the game changes by itself is used
(the swarm's 0-1, the time of day's 2-3, the Great Marsh's and the Trophy Garden's 6-7, the post-game's slots of
data/postgame_dex.json). A new Pokémon keeps its slot's levels. Water groups may move a Sinnoh Pokémon whose only slot a
Unova kind takes into a smaller slot of a Pokémon that has two (a "move": the sea's Wingull 30 % -> 4 %), so that the sea
gets its quarter too.

Edits (what the build writes, decomp src/pearlb2/resident/unova.c applies when the zone's table loads): (zone, group,
slot, own, new, late): group 0 grass (and its dark-grass copy), 1 surf, 2 Super Rod (the time-of-day tables' fishing
group), 3 Good Rod (table 3's rippling-fishing group); own and new = species | form << 11; late = only after the
Champion (Black 2's game clear, flag 2400): Pearl's and Diamond's other side of a version pair, in one more slot.
"""
import fnmatch, functools, itertools, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]

PLAN = os.path.join(ROOT, 'data', 'unova.json')
POKEMON = os.path.join(ROOT, 'external', 'pokebw2', 'res', 'pokemon')
VERSIONS = ('pearl', 'diamond', 'platinum')
GROUPS = ('grass', 'surf', 'super', 'good')              # edit group numbers 0-3 (resident/unova.c UNOVA_GROUP_*)
ODDS = {'grass': [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1], 'surf': [60, 30, 5, 4, 1],
        'good': [40, 40, 15, 4, 1], 'super': [40, 40, 15, 4, 1]}
TARGET = {'grass': 24, 'surf': 30, 'good': 20, 'super': 19}
RANGE = {'grass': (18, 28), 'surf': (4, 35), 'good': (15, 25), 'super': (5, 20)}
CHECK_RANGE = {'grass': (1, 28), 'surf': (1, 35), 'good': (1, 25), 'super': (1, 20)}   # (fewer free slots: post-game)
KEY = {'grass': None, 'surf': 'surf_encounters', 'good': 'good_rod_encounters', 'super': 'super_rod_encounters'}
RATE = {'grass': 'land_rate', 'surf': 'surf_rate', 'good': 'good_rod_rate', 'super': 'super_rod_rate'}
PERIODS = ('morning', 'day', 'night')
SWARM, TIMED, DAILY = (0, 1), (2, 3), (6, 7)      # the swarm's (swarm_zones()), time of day's, daily
DAILY_ZONES = ('MAP_GREAT_MARSH_AREA_*', 'MAP_TROPHY_GARDEN')
STARTERS = set(range(495, 504))
DENY = {494, 564, 565, 566, 567, 570, 571} | set(range(638, 650))
GAME_CLEAR = 2400
MOVE_COST, SLOT_COST = 2.5, 0.5
LATE_MAX = 5                    # the other side's slot after the Champion: a small one
FLOOR = 9                       # a common kind's least share of its group (%)
BALANCE_COST = 1.5
RATE_COST = 3                   # a Sinnoh Pokémon's rate change, relative to its old rate
GAIN_MAX = 5                    # a Sinnoh Pokémon gains at most this; one of 15 % or more keeps 60 % of its rate or
DROP_MAX = 10                   # loses at most DROP_MAX points, a smaller one keeps half its rate
KEEP_BIG = 0.6
DROP_SMALL = 4                  # ... or loses at most 4 points (Pelipper 5 % -> 1 %)
SPREAD_COST = 1.0


# ---- data ------------------------------------------------------------------------------------------------------------
@functools.lru_cache(None)
def species_ids():
    import sinnoh_encounters as se
    return se.species_ids()


@functools.lru_cache(None)
def species_names():
    return {v: k for k, v in species_ids().items()}


def key_of(name, form=0):
    name = name if name.startswith('SPECIES_') else 'SPECIES_' + name
    return species_ids()[name] | form << 11


def spec(token):
    """'NAME' / 'NAME:form' -> key."""
    name, _, form = token.partition(':')
    return key_of(name, int(form or 0))


def name_of(key, short=True):
    n = species_names()[key & 0x7FF][8:]
    n = n.title().replace('_', ' ') if short else n
    if key & 0x7FF == 550:
        n += ' (Blue)' if key >> 11 == 1 else ' (Red)'
    elif key >> 11 and key & 0x7FF in (422, 423):
        n += ' (East)'
    return n


@functools.lru_cache(None)
def evolutions():
    """{species id: [(method, param, into id)]}: Black 2's table with data/trade_evos.json's in-game ones."""
    out = {}
    ids = species_ids()
    for name, sid in ids.items():
        p = os.path.join(POKEMON, name[8:].lower(), 'data.json')
        if sid == 0 or sid > 649 or not os.path.exists(p):
            continue
        out[sid] = [(e['method'], e['param'], ids[e['species']]) for e in json.load(open(p)).get('evolutions') or []]
    trade = json.load(open(os.path.join(ROOT, 'data', 'trade_evos.json')))['evolutions']
    for name, rows in trade.items():
        out[ids[name]] = [(m, p, ids[s]) for m, p, s in rows]
    return out


@functools.lru_cache(None)
def parents():
    out = {}
    for sid, rows in evolutions().items():
        for m, p, into in rows:
            out.setdefault(into, (sid, m, p))
    return out


@functools.lru_cache(None)
def own_evolutions():
    """{species id: [(method, param, into id)]}: Black 2's own table (a trade stays a trade)."""
    out = {}
    for name, sid in species_ids().items():
        p = os.path.join(POKEMON, name[8:].lower(), 'data.json')
        if 0 < sid <= 649 and os.path.exists(p):
            out[sid] = [(e['method'], e['param'], species_ids()[e['species']])
                        for e in json.load(open(p)).get('evolutions') or []]
    return out


def stage_at(base, level):
    """The family's last stage a Pokémon of `base` reaches by levelling to `level` (Black 2's level evolutions only)."""
    sid = base
    while True:
        nxt = [(p, into) for m, p, into in own_evolutions().get(sid, []) if m == 'EVO_METHOD_LEVEL' and p <= level]
        if not nxt:
            return sid
        sid = nxt[0][1]


def legal_min(sid):
    """The lowest level a wild `sid` makes sense at: a level evolution's level, else its parent's."""
    p = parents().get(sid)
    if p is None:
        return 1
    parent, method, param = p
    return max(legal_min(parent), param if method == 'EVO_METHOD_LEVEL' else legal_min(parent) + 1)


def family_base(sid):
    while sid in parents():
        sid = parents()[sid][0]
    return sid


@functools.lru_cache(None)
def plan():
    return json.load(open(PLAN, encoding='utf-8'))


def world_zones(v):
    p = os.path.join(ROOT, 'data', 'platinum', 'sinnoh_world.json') if v == 'platinum' else \
        os.path.join(ROOT, 'data', 'sinnoh_world.json')
    w = json.load(open(p))
    zones = {int(k): z['name'] for k, z in w['zones'].items()}
    zones.update({int(k): z['name'] for k, z in w['rooms']['zones'].items()})
    return zones


@functools.lru_cache(None)
def tables(v):
    """{zone name: (pearl file n, {group: {period: [(key, min, max)]}})} of the version's zones with wild Pokémon."""
    import sinnoh_encounters as se
    zj = json.load(open(os.path.join(ROOT, 'work', v, 'zones.json')))
    out = {}
    for zid, name in sorted(world_zones(v).items()):
        n = zj[zid]['encounters']
        if n is None:
            continue
        enc = json.load(open(os.path.join(ROOT, 'work', v, 'encounters', f'{n:03d}.json')))
        groups = {}
        for g in GROUPS:
            if not enc[RATE[g]]:
                continue
            if g == 'grass':
                groups[g] = {per: [(key_of(s[0], s[1]), s[2], s[3]) for s in se.grass_slots(enc, per)] for per in PERIODS}
            else:
                rows = [(key_of(s[0], s[1]), s[2], s[3]) for s in se.water_slots(enc, KEY[g])]
                groups[g] = {per: rows for per in PERIODS}
        if groups:
            out[name] = (n, groups)
    return out


@functools.lru_cache(None)
def postgame_slots(v):
    """{(zone, group): {slot}} the post-game list changes (data/postgame_dex.json)."""
    d = json.load(open(os.path.join(ROOT, 'data', 'postgame_dex.json')))[v]
    out = {}
    for zone, group, slot, *_ in d['exclusives'] + d['radar']:
        out.setdefault((zone, group), set()).add(slot)
    return out


def area_plan(zone):
    short = zone[4:] if zone.startswith('MAP_') else zone
    hits = [k for k in plan()['areas'] if fnmatch.fnmatchcase(short, k)]
    return hits


# ---- the kinds ---------------------------------------------------------------------------------------------------------
def kinds(tokens, v):
    """[(token, base key or None, rare, pair side)] of an area group's tokens for version v; @ = a pair: Pearl the first,
    Diamond the second, Platinum both (two kinds)."""
    pairs = plan()['pairs']
    out = []
    for t in tokens:
        rare = t.endswith('*')
        t = t.rstrip('*')
        if t.startswith('@'):
            white = t[1:]
            black = pairs[white]
            sides = {'pearl': [(white, black)], 'diamond': [(black, white)], 'platinum': [(white, None), (black, None)]}[v]
            for own, other in sides:
                out.append(dict(token=t, own=own, other=other, rare=rare))
        else:
            out.append(dict(token=t, own=t, other=None, rare=rare))
    return out


def resolve(token, level):
    """The species key a kind token puts in a slot whose lowest level is `level`."""
    family = token.startswith('~')
    t = token.lstrip('~')
    k = spec(t)
    if family:
        return stage_at(k & 0x7FF, level) | (k >> 11) << 11
    return k


# ---- the slots ---------------------------------------------------------------------------------------------------------
def rates(slots, odds, U, moves):
    """{native key: % of its group} after U and the moves."""
    out = {}
    for i, (k, _, _) in enumerate(slots):
        if i in U:
            continue
        k = moves.get(i, k)
        out[k] = out.get(k, 0) + odds[i]
    return out


def lost_keys(rows, U, moves):
    """Sinnoh Pokémon (keys) with no slot left at some time of day after U and the moves."""
    out = set()
    for per, slots in rows.items():
        new = [moves.get(i, k) if i not in U else None for i, (k, _, _) in enumerate(slots)]
        out |= {k for k, _, _ in slots} - set(new)
    return out


def allocate(group, rows, allowed, need, target=None, ks=None):
    """(U, moves) for one group: U the slots the Unova kinds take, moves {slot: native key} for a Sinnoh Pokémon moved
    into the smaller slot of one that keeps another (its only slot taken). rows = {period: [(key, min, max)]}."""
    odds = ODDS[group]
    target = TARGET[group] if target is None else target
    lo, hi = RANGE[group]
    best = None
    allowed = sorted(allowed)
    for r in range(need, min(len(allowed), 6) + 1):
        for U in itertools.combinations(allowed, r):
            s = sum(odds[i] for i in U)
            if s > hi:
                continue
            moves = {}
            for key in sorted(lost_keys(rows, U, {})):
                cands = []
                for j in allowed:
                    if j in U or j in moves:
                        continue
                    trial = {**moves, j: key}
                    if not (lost_keys(rows, U, trial) & ({rows['day'][j][0]} | set(trial.values()))):
                        cands.append((odds[j], j))
                if not cands:
                    moves = None
                    break
                moves[max(cands)[1]] = key
            if moves is None or lost_keys(rows, U, moves):
                continue
            score = abs(s - target) + MOVE_COST * len(moves) + SLOT_COST * len(U)
            # Sinnoh's own Pokémon near their old rates (the quarter comes out of the large shares); none gains more
            # than GAIN_MAX points (a moved Staryu 15 % -> 40 % is out)
            before, after = rates(rows['day'], odds, set(), {}), rates(rows['day'], odds, set(U), moves)
            if any(after.get(k, 0) > o + GAIN_MAX or after.get(k, 0) < (min(o - DROP_MAX, KEEP_BIG * o) if o >= 15 else min(o / 2, o - DROP_SMALL))
                   for k, o in before.items()):
                continue
            score += sum(RATE_COST * abs(after.get(k, 0) - o) / max(o, 5) for k, o in before.items())
            if ks and len(ks) > 1:              # each common kind at least FLOOR %, and near each other (a rare one gets
                got = [sum(odds[x] for x in sl)                       # the smallest slot)
                       for i, sl in share(list(U), ks, odds).items() if not ks[i]['rare']]
                score += BALANCE_COST * sum(max(0, FLOOR - g_) for g_ in got)
                if got:
                    score += SPREAD_COST * max(0, max(got) - min(got) - 5)
            if s < lo:
                score += 50
            cand = (score, U, tuple(sorted(moves.items())))
            if best is None or cand < best:
                best = cand
    if best is None:
        return None
    return list(best[1]), dict(best[2])


def share(U, kinds_, odds):
    """{kind index: [slots]}: rare kinds the smallest slots, the rest by largest slot to the kind with the least."""
    order = sorted(U, key=lambda i: (-odds[i], i))
    out = {i: [] for i in range(len(kinds_))}
    rares = [i for i, k in enumerate(kinds_) if k['rare']]
    commons = [i for i, k in enumerate(kinds_) if not k['rare']]
    for i in rares:
        if len(order) > len(commons):
            out[i].append(order.pop())
    for s in order:
        pick = min(commons or rares, key=lambda i: (sum(odds[x] for x in out[i]), i))
        out[pick].append(s)
    return out


@functools.lru_cache(None)
def swarm_zones():
    """The zones of Pearl's daily swarm (patches/wild.py SWARM_MAPS, every version): their grass slots 0-1 change."""
    import wild
    names = {z['id']: z['name'] for z in json.load(open(os.path.join(ROOT, 'work', 'pearl', 'zones.json')))}
    return {names[i] for i in wild.SWARM_MAPS}


def keeps_other(rows, j, taken):
    """Slot j's Sinnoh Pokémon has another slot (not in taken) at every time of day."""
    return all(any(slots[i][0] == slots[j][0] for i in range(len(slots)) if i != j and i not in taken)
               for slots in rows.values())


@functools.lru_cache(None)
def edits(v):
    """(edits, notes) of version v: edits [dict(zone, n, group, slot, own, new, late, level, kind)]; notes [str]."""
    p = plan()
    out, notes = [], []
    starters = {area: s for s, area in p['starters'].items()}
    unchanged = p.get('unchanged', {})
    pg = postgame_slots(v)
    for zone, (n, groups) in tables(v).items():
        hits = area_plan(zone)
        if len(hits) != 1:
            notes.append(f'{v} {zone}: {"no plan" if not hits else "several plans: " + ", ".join(hits)}')
            continue
        ap = p['areas'][hits[0]]
        for g in GROUPS:
            if g not in groups:
                if g in ap and not any(c in hits[0] for c in '*?['):
                    notes.append(f'{v} {zone}: the plan has {g} but the table has none')
                continue
            if any(fnmatch.fnmatchcase(f'{zone[4:]}:{g}', u) and v in r['versions'] for u, r in unchanged.items()):
                continue
            if g not in ap:
                notes.append(f'{v} {zone}: no {g} kinds in the plan')
                continue
            rows = groups[g]
            odds = ODDS[g]
            allowed = set(range(len(odds))) - pg.get((zone, g), set())
            if g == 'grass':
                allowed -= set(TIMED)
                if zone in swarm_zones():
                    allowed -= set(SWARM)
                if any(fnmatch.fnmatchcase(zone, z) for z in DAILY_ZONES):
                    allowed -= set(DAILY)
            day = rows['day']
            taken = set()
            # the starter's 1 % slot (grass only)
            st = starters.get(zone[4:])
            if st and g == 'grass':
                for j in (11, 10):
                    if j in allowed and keeps_other(rows, j, {10, 11}):
                        out.append(dict(zone=zone, n=n, group=g, slot=j, own=day[j][0], new=spec(st), late=False,
                                        level=day[j][1], kind='starter'))
                        allowed.discard(j)
                        taken.add(j)
                        break
                else:
                    notes.append(f'{v} {zone}: no 1 % slot for {st}')
            ks = kinds(ap[g], v)
            got = allocate(g, rows, allowed, len(ks), ks=ks)
            while got is None and len({k['token'] for k in ks}) > 1 and v != 'platinum':
                last = ks[-1]['token']           # fewer kinds where the free slots are too few (the last ones go)
                ks = [k for k in ks if k['token'] != last]
                notes.append(f'(fewer) {v} {zone} {g}: without {last}')
                got = allocate(g, rows, allowed, len(ks), ks=ks)
            if got is None and v == 'platinum' and any(k['token'].startswith('@') for k in ks):
                # Platinum has both sides of a pair: where the area has no room for both, the side of its file's parity
                seen, keep = set(), []
                for k in ks:
                    if k['token'].startswith('@'):
                        if k['token'] in seen:
                            continue
                        seen.add(k['token'])
                        side = [x for x in ks if x['token'] == k['token']][n % 2]
                        keep.append(side)
                    else:
                        keep.append(k)
                ks = keep
                got = allocate(g, rows, allowed, len(ks), ks=ks)
            while got is None and len({k['token'] for k in ks}) > 1:
                last = ks[-1]['token']
                ks = [k for k in ks if k['token'] != last]
                notes.append(f'(fewer) {v} {zone} {g}: without {last}')
                got = allocate(g, rows, allowed, len(ks), ks=ks)
            if got is None:
                notes.append(f'{v} {zone} {g}: no slots for {[k["token"] for k in ks]}')
                continue
            U, moves = got
            by_kind = share(U, ks, odds)
            for ki, slots in by_kind.items():
                k = ks[ki]
                if not slots:
                    notes.append(f'{v} {zone} {g}: {k["own"]} got no slot')
                for j in slots:
                    out.append(dict(zone=zone, n=n, group=g, slot=j, own=day[j][0], new=resolve(k['own'], day[j][1]),
                                    late=False, level=day[j][1], kind=k['token']))
            for j, key in moves.items():
                out.append(dict(zone=zone, n=n, group=g, slot=j, own=day[j][0], new=key, late=False, level=day[j][1],
                                kind='move'))
            # after the Champion: the other side of each pair in one more slot (Pearl, Diamond)
            taken |= set(U) | set(moves)
            for ki, k in enumerate(ks):
                if not k['other']:
                    continue
                free = [j for j in sorted(allowed - taken) if odds[j] <= LATE_MAX and keeps_other(rows, j, taken)]
                if free:
                    j = min(free, key=lambda j: (odds[j], -j))
                    taken.add(j)
                    out.append(dict(zone=zone, n=n, group=g, slot=j, own=day[j][0], new=resolve(k['other'], day[j][1]),
                                    late=True, level=day[j][1], kind='@' + k['other']))
                else:      # its own smallest slot (its other slots and the other areas keep it)
                    j = min(by_kind[ki], key=lambda j: (odds[j], -j))
                    out.append(dict(zone=zone, n=n, group=g, slot=j, own=resolve(k['own'], day[j][1]),
                                    new=resolve(k['other'], day[j][1]), late=True, level=day[j][1], kind='@' + k['other']))
    for zone in plan()['areas']:
        if not any(fnmatch.fnmatchcase(z[4:], zone) for z in tables(v)):
            notes.append(f'{v}: plan area {zone} matches no zone')
    return out, notes


# ---- the rules -----------------------------------------------------------------------------------------------------------
def apply_rows(rows, es, late):
    """The rows of one period after the edits (late ones too when `late`)."""
    rows = list(rows)
    for e in es:
        if e['late'] and not late:
            continue
        if rows[e['slot']][0] == e['own']:
            rows[e['slot']] = (e['new'],) + tuple(rows[e['slot']][1:])
    return rows


def check(v):
    """Findings of version v (empty = the rules hold)."""
    es, notes = edits(v)
    out = [n for n in notes if not n.startswith('(fewer)')]
    pg = postgame_slots(v)
    by = {}
    for e in es:
        by.setdefault((e['zone'], e['group']), []).append(e)
    reached = set()
    for (zone, g), group_edits in sorted(by.items()):
        rows = tables(v)[zone][1][g]
        odds = ODDS[g]
        slots_used = [e['slot'] for e in group_edits]
        if len(slots_used) != len(set(slots_used)) and not all(e['late'] for e in group_edits):
            dup = [s for s in slots_used if slots_used.count(s) > 1]
            if any(not e['late'] for e in group_edits if e['slot'] in dup and
                   sum(1 for x in group_edits if x['slot'] == e['slot'] and not x['late']) > 1):
                out.append(f'{v} {zone} {g}: a slot edited twice')
        for e in group_edits:
            sid = e['new'] & 0x7FF
            if e['kind'] == 'move':
                continue
            if not 495 <= sid <= 649:
                out.append(f'{v} {zone} {g}: {name_of(e["new"])} is not a Gen 5 Pokémon')
            if sid in DENY:
                out.append(f'{v} {zone} {g}: {name_of(e["new"])} is not allowed')
            if sid in STARTERS and not (e['kind'] == 'starter' and odds[e['slot']] == 1):
                out.append(f'{v} {zone} {g}: the starter {name_of(e["new"])} outside its 1 % slot')
            if g == 'grass' and (e['slot'] in TIMED or e['slot'] in SWARM and zone in swarm_zones()):
                out.append(f'{v} {zone}: slot {e["slot"]} is the swarm\'s or the time of day\'s')
            if e['slot'] in pg.get((zone, g), ()):
                out.append(f'{v} {zone} {g}: slot {e["slot"]} is the post-game\'s')
            if e['level'] < legal_min(sid):
                out.append(f'{v} {zone} {g}: {name_of(e["new"])} at level {e["level"]} (it evolves at {legal_min(sid)})')
            reached.add(sid)
        for late in (False, True):
            share_ = 0
            for per, slots in rows.items():
                new = apply_rows(slots, group_edits, late)
                for key in {k for k, _, _ in slots}:
                    if not any(k == key for k, _, _ in new):
                        out.append(f'{v} {zone} {g} {per}{" after the Champion" if late else ""}: {name_of(key)} lost')
                if per == 'day':
                    share_ = sum(odds[i] for i, (k, _, _) in enumerate(new) if 495 <= k & 0x7FF <= 649)
            lo, hi = CHECK_RANGE[g]
            low = any(fnmatch.fnmatchcase(f'{zone[4:]}:{g}', u) and v in r['versions']
                      for u, r in plan().get('low', {}).items())
            if not late and not low and not lo <= share_ <= hi + 1:
                out.append(f'{v} {zone} {g}: Unova share {share_} %')
    # every family evolvable: the stones are sold with the option (data/unova.json "shop"), the rest level or friendship
    return out, reached


# ---- the teams -----------------------------------------------------------------------------------------------------------
MOVES = os.path.join(ROOT, 'external', 'pokebw2', 'res', 'moves')
TEAM_VERSIONS = {'pearl': 'dp', 'diamond': 'dp', 'platinum': 'platinum'}


@functools.lru_cache(None)
def move_data(move):
    p = os.path.join(MOVES, move[5:].lower(), 'data.json')
    return json.load(open(p)) if os.path.exists(p) else None


@functools.lru_cache(None)
def tm_moves():
    """Black 2's TM/HM labels -> moves (src/system/pml_item.c TM_MOVE_LIST: TM01-TM92, HM01-HM06, TM93-TM95)."""
    import tm_audit
    m = tm_audit.b2_moves()
    out = {f'TM{n + 1:02d}': m[n] for n in range(92)}
    out.update({f'HM{n + 1:02d}': m[92 + n] for n in range(6)})
    out.update({f'TM{93 + n}': m[98 + n] for n in range(3)})
    return out


def species_data(sid):
    return json.load(open(os.path.join(POKEMON, species_names()[sid][8:].lower(), 'data.json')))


def power(move):
    d = move_data(move)
    if not d or d['category'] == 'MOVE_CATEGORY_STATUS':
        return 0
    return (d['power'] or 0) * min(d['accuracy'] or 100, 100) / 100


DENY_MOVES = {'MOVE_HORN_DRILL', 'MOVE_GUILLOTINE', 'MOVE_FISSURE', 'MOVE_SHEER_COLD', 'MOVE_SOLAR_BEAM', 'MOVE_HYPER_BEAM',
              'MOVE_GIGA_IMPACT', 'MOVE_SELF_DESTRUCT', 'MOVE_EXPLOSION', 'MOVE_HEAL_BLOCK', 'MOVE_WONDER_ROOM',
              'MOVE_MAGIC_ROOM', 'MOVE_TELEKINESIS', 'MOVE_GUARD_SPLIT', 'MOVE_POWER_SPLIT', 'MOVE_ENTRAINMENT',
              'MOVE_RAGE_POWDER', 'MOVE_UPROAR', 'MOVE_DREAM_EATER', 'MOVE_SKILL_SWAP', 'MOVE_FLAIL', 'MOVE_SKY_DROP',
              'MOVE_FRUSTRATION', 'MOVE_RETURN', 'MOVE_FLING', 'MOVE_NATURAL_GIFT', 'MOVE_SECRET_POWER',
              'MOVE_ROCK_CLIMB', 'MOVE_FUTURE_SIGHT', 'MOVE_LAST_RESORT', 'MOVE_SKY_ATTACK', 'MOVE_SWAGGER',
              'MOVE_SANDSTORM', 'MOVE_HAIL', 'MOVE_RAIN_DANCE', 'MOVE_SUNNY_DAY', 'MOVE_ACID_ARMOR', 'MOVE_HARDEN',
              'MOVE_TACKLE', 'MOVE_SCRATCH', 'MOVE_POUND', 'MOVE_COSMIC_POWER', 'MOVE_COTTON_SPORE', 'MOVE_CLEAR_SMOG',
              'MOVE_ECHOED_VOICE', 'MOVE_HEADBUTT', 'MOVE_SPLASH', 'MOVE_CHARM', 'MOVE_SCARY_FACE', 'MOVE_DIZZY_PUNCH',
              'MOVE_HELPING_HAND', 'MOVE_GRAVITY', 'MOVE_FOLLOW_ME', 'MOVE_ALLY_SWITCH'}


def power_cap(level):
    return 60 if level < 20 else 80 if level < 35 else 100 if level < 50 else 120


def moveset(species, level):
    """Four moves for a Leader's, an Elite Four member's or the Champion's Pokémon: its best attack of its own type and
    a second attack (another type where it has one), from what it learns by levelling up to `level` or by TM, no
    stronger than the level allows (power_cap); then the last moves it learned by levelling, as Black 2's default does.
    Never a one-hit KO, a recharge move, Solar Beam or a move that does nothing in a single battle (DENY_MOVES)."""
    sid = species_ids()['SPECIES_' + species]
    d = species_data(sid)
    types = set(d['types'])
    learned = []
    for lv, m in d['learnset']['by_level']:
        if lv <= level:
            if m in learned:
                learned.remove(m)
            learned.append(m)
    tms = [tm_moves()[t] for t in d['learnset'].get('by_tm', []) if t in tm_moves()]
    cap = power_cap(level)
    ok = lambda m: m not in DENY_MOVES and move_data(m) is not None
    attacks = [m for m in dict.fromkeys(learned[::-1] + tms) if ok(m) and 0 < (move_data(m)['power'] or 0) <= cap]
    stab = sorted((m for m in attacks if move_data(m)['type'] in types), key=lambda m: -power(m))
    picks = stab[:1]
    second = sorted((m for m in attacks if m not in picks and
                     (not picks or move_data(m)['type'] != move_data(picks[0])['type'])), key=lambda m: -power(m))
    picks += second[:1] or stab[1:2]
    for m in learned[::-1]:
        if len(picks) >= 4:
            break
        if ok(m) and m not in picks:
            picks.append(m)
    for m in sorted(attacks, key=lambda m: -power(m)):
        if len(picks) >= 4:
            break
        if m not in picks:
            picks.append(m)
    return picks[:4]


def trainer_file(v, t):
    base = os.path.join(ROOT, 'work', 'platinum' if v == 'platinum' else 'pearl', 'b2_trainers', 'data')
    return json.load(open(os.path.join(base, f'{int(t):03d}.json')))


def teams(v):
    """{pearl trainer id: (old party, new party)} of version v (new party: the trainer's JSON party with the swaps)."""
    pairs = plan()['pairs']
    out = {}
    for t, e in plan()['teams'].items():
        if t.startswith('_'):
            continue
        old = trainer_file(v, t)['party']
        if 'full' in e:                     # a whole team (Cynthia's B/W one): Sinnoh levels by species, the rest in order
            spare = [m for m in old if m['species'][8:] not in {f['species'] for f in e['full']}]
            new = []
            for f in e['full']:
                same = next((m for m in old if m['species'][8:] == f['species']), None)
                src = same or spare.pop(0)
                m = dict(src, species='SPECIES_' + f['species'], form=0, gender=f['gender'], ability=f['ability'],
                         moves=['MOVE_' + x for x in f['moves']])
                if 'item' in src:
                    m['item'] = 'ITEM_NONE'
                new.append(m)
            out[t] = (old, new)
            continue
        swaps = e[TEAM_VERSIONS[v]]
        new = [dict(m) for m in old]
        for i, kind in swaps.items():
            i = int(i)
            if kind.startswith('@'):
                kind = kind[1:] if v != 'diamond' else pairs[kind[1:]]
            m = new[i]
            m['species'] = 'SPECIES_' + kind
            m['form'], m['gender'], m['ability'] = 0, 0, 0
            if 'moves' in m:
                m['moves'] = ['MOVE_' + x[5:] if x.startswith('MOVE_') else x for x in moveset(kind, m['level'])]
        out[t] = (old, new)
    return out


def check_teams(v):
    out = []
    for t, (old, new) in teams(v).items():
        name = plan()['teams'][t]['name']
        assert len(old) == len(new)
        if 'full' in plan()['teams'][t]:
            ratio = {}
            for m in new:
                d = species_data(species_ids()[m['species']])
                g = d['gender_ratio']
                if m['gender'] == 1 and g in (254, 'GENDER_RATIO_FEMALE_ONLY', 255, 'GENDER_RATIO_GENDERLESS') or \
                        m['gender'] == 2 and g in (0, 'GENDER_RATIO_MALE_ONLY', 255, 'GENDER_RATIO_GENDERLESS'):
                    out.append(f'{v} {name}: {m["species"]} cannot be gender {m["gender"]}')
                ab = d['abilities'][m['ability'] - 1] if m['ability'] in (1, 2) else None
                if not ab or ab == 'ABILITY_NONE':
                    out.append(f'{v} {name}: {m["species"]} has no ability {m["ability"]}')
                for x in m['moves']:
                    if not move_data(x):
                        out.append(f'{v} {name}: {m["species"]} move {x} unknown')
                if m.get('item', 'ITEM_NONE') != 'ITEM_NONE':
                    out.append(f'{v} {name}: {m["species"]} holds {m["item"]}')
            if max(m['level'] for m in new) != new[-1]['level'] or new[-1]['level'] != old[-1]['level']:
                out.append(f'{v} {name}: the ace is not the highest at her Sinnoh ace level')
            if sorted(m['level'] for m in new) != sorted(m['level'] for m in old):
                out.append(f'{v} {name}: not her Sinnoh levels')
            continue
        for a, b in zip(old, new):
            if a['species'] == b['species']:
                continue
            sid = species_ids()[b['species']]
            if not 495 <= sid <= 649 or sid in DENY:
                out.append(f'{v} {name}: {b["species"]} is not an allowed Gen 5 Pokémon')
            if b['level'] < legal_min(sid):
                out.append(f'{v} {name}: {b["species"]} at level {b["level"]} (it evolves at {legal_min(sid)})')
            if a.get('item', 'ITEM_NONE') != b.get('item', 'ITEM_NONE') or a['level'] != b['level'] or \
                    a['difficulty'] != b['difficulty']:
                out.append(f'{v} {name}: {b["species"]} does not keep its slot\'s level, difficulty or item')
            for m in b.get('moves', []):
                if not move_data(m):
                    out.append(f'{v} {name}: {b["species"]} move {m} unknown')
            if 'moves' in a and len(b['moves']) == 0:
                out.append(f'{v} {name}: {b["species"]} has no moves')
        if old[-1]['species'] != new[-1]['species']:
            out.append(f'{v} {name}: the ace changed')
    return out


# ---- evolutions -------------------------------------------------------------------------------------------------------
SHOP_STONES = {'ITEM_SUN_STONE', 'ITEM_MOON_STONE', 'ITEM_SHINY_STONE', 'ITEM_DUSK_STONE', 'ITEM_FIRE_STONE',
               'ITEM_WATER_STONE', 'ITEM_THUNDERSTONE', 'ITEM_LEAF_STONE'}   # Veilstone 2F with the option (unova_option.py)


def check_evolutions(v, placed):
    """Every family the option places can finish evolving in Sinnoh: by level, friendship, a stone the option sells, or
    the other species in the party (Karrablast and Shelmet); Black 2's trade methods are data/trade_evos.json's."""
    out = []
    todo, seen = list(placed), set()
    while todo:
        sid = todo.pop()
        if sid in seen:
            continue
        seen.add(sid)
        ways = {}
        for m, param, into in evolutions().get(sid, []):
            if m.startswith('EVO_METHOD_TRADE'):
                continue                         # (kept beside the in-game way for a real trade)
            ok = ('LEVEL' in m or 'FRIENDSHIP' in m or (m == 'EVO_METHOD_ITEM' and param in SHOP_STONES) or
                  (m == 'EVO_METHOD_SPECIES_IN_PARTY' and species_ids().get(param) in placed | seen))
            ways.setdefault(into, []).append((ok, m, param))
        for into, w in ways.items():
            if not any(ok for ok, _, _ in w):
                out.append(f'{v}: {name_of(sid)} -> {name_of(into)} needs ' + ' or '.join(f'{m} {p}' for _, m, p in w))
            todo.append(into)
    return out


# ---- the report ----------------------------------------------------------------------------------------------------------
def area_rows(v):
    """[(zone, group, [(name, %, levels, late)])] for the report."""
    es, _ = edits(v)
    rows = {}
    for e in es:
        if e['kind'] == 'move':
            continue
        odds = ODDS[e['group']][e['slot']]
        k = (e['zone'], e['group'])
        d = rows.setdefault(k, {})
        nm = name_of(e['new']) + (' (after the Champion)' if e['late'] else '')
        d.setdefault(nm, [0, e['level']])[0] += odds
    out = []
    for (zone, g), d in rows.items():
        out.append((zone, g, sorted(((n, p, lv) for n, (p, lv) in d.items()), key=lambda r: -r[1])))
    return out


def report(versions):
    for v in versions:
        es, notes = edits(v)
        print(f'== {v}: {len(es)} edits ({sum(1 for e in es if e["late"])} after the Champion, '
              f'{sum(1 for e in es if e["kind"] == "move")} moves)')
        cur = None
        for zone, g, kinds_ in area_rows(v):
            if zone != cur:
                cur = zone
                print(f'  {zone[4:]}')
            moved = [e for e in es if e['zone'] == zone and e['group'] == g and e['kind'] == 'move']
            mv = ('; moves ' + ', '.join(f'{name_of(e["new"])} -> {ODDS[g][e["slot"]]} %' for e in moved)) if moved else ''
            print(f'    {g:6s} ' + ', '.join(f'{n} {p} %' for n, p, _ in kinds_) + mv)
        for n in notes:
            print('  NOTE', n)


def markdown(v):
    es, _ = edits(v)
    lines = []
    cur = None
    label = {'grass': 'Grass / cave', 'surf': 'Surfing', 'good': 'Good Rod', 'super': 'Super Rod'}
    for zone, g, kinds_ in area_rows(v):
        if zone != cur:
            cur = zone
            lines.append(f'| {zone[4:].replace("_", " ").title()} | | |')
        lines.append(f'| | {label[g]} | ' + ', '.join(f'{n} {p} %' for n, p, _ in kinds_) + ' |')
    return lines


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    vs = [a for a in args if a in VERSIONS] or list(VERSIONS)
    if '--check' in sys.argv:
        bad = 0
        allr = {}
        for v in vs:
            out, reached = check(v)
            out += check_teams(v)
            out += check_evolutions(v, set(reached))
            allr[v] = reached
            for f in out:
                print(f)
            bad += len(out)
            print(f'{v}: {len(edits(v)[0])} edits, {len(reached)} Unova species, {len(out)} findings')
        sys.exit(1 if bad else 0)
    elif '--md' in sys.argv:
        for v in vs:
            print('\n'.join(markdown(v)))
    else:
        report(vs)
