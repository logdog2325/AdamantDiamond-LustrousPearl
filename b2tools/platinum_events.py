"""Platinum's people, doors, warps, signs and triggers against Pearl's, and the offline check of the events a Platinum build
installs (notes/PORT_AUDIT.md, step 3, "Town events and signs"; notes/PLATINUM_EVENTS.md is what it writes).

    PEARL_VERSION=platinum python3 b2tools/platinum_events.py --heights
        first (once, a few minutes): the version's tile heights, converted as the build does (work/platinum/heights)
    PEARL_VERSION=platinum python3 b2tools/platinum_events.py [--rooms] [--quiet]
        the check: exit 1 on a problem; writes notes/PLATINUM_EVENTS.md and data/platinum/events_waiting.json
        --rooms: also the furniture check (pearl_rooms_view) of every room where Platinum moved or added people, against
                 Pearl's findings in the same room (a few minutes)

Run after the Platinum tree's offline steps (work/platinum is git-ignored): `PEARL_VERSION=platinum python3 b2tools/X`
for X = gen4_extract.py, gen4_land.py, gen4_script.py, rock_climb.py --write, pearl_items.py, pearl_story.py all (the
zone script files the events point at), then this tool's --heights once.

How the events get to a Platinum build: every tool reads the world through version rows, so the events are Platinum's own
(work/platinum/events, Pearl's numbers by data/platinum/id_map.json) with all of Pearl's rules and fixes: people, signs
and step triggers from pearl_events.entities (sinnoh_story installs them with the zone's script file), warps from
sinnoh_events.Planner, sign models from pearl_signs, doors from pearl_doors. Where Platinum didn't change a zone the
events are byte for byte Pearl's, so Pearl's result stands. This tool changes nothing; it measures and checks.

What it checks (a problem fails the run, unless the zone is left for a later step: the Distortion World (step 7) and
the Battle Frontier with its Battle Tower (step 8) are listed apart; so are the gimmicks of step 4's rooms):
- warps: every warp of an installed zone lands on a walkable tile of a real zone, on the map, in a cell the zone owns;
  its partner leads back (to its own tile or one beside it); several warps on one tile (only the first fires);
- people: every person's sprite has a Black 2 code (data/platinum/sprite_map.json for Platinum's own ids) or is left out
  and listed; every hide flag is in the registry; every script exists in the zone's file (or is listed as waiting for
  the chapter pieces); local ids are unique; a zone shows at most 30 different sprites (sinnoh_story's rule: Black 2's
  32 billboard materials, the player's two included);
- signs: every sign event's script shows a line of the zone's text file (hidden items: their global entry exists);
- step triggers: the var is in the registry, the script exists;
- map scripts: every entry of the zone's map-script table exists; every script passes b2_script_check at its level;
- Pokémon Centers: each 1F has Black 2's heal machine prop (Pearl's machine_pc02 with a heal record, within 5 tiles of
  where the player stands at the counter) and the ball resource 0x62 (pearl_heal), or melonDS and hardware crash on
  healing (notes/NEXT_REGION_BRIEF.md);
- doors: pearl_doors.check (every door warp finds one door prop, every door model a working record);
- Pearl's fixes keyed by an object, a sign or a tile (data/pearl_closed_facilities.json, pearl_hidden_paths.OBJECTS,
  data/pearl_speakers.json, the Rock Climb starts, data/people_depth.json): each still finds what it was made for;
- the zones Platinum didn't change: what the build installs there equals, field by field, what a Pearl build installs
  (a Pearl process of this tool, --pearl-entities), so Pearl's hand fixes stand.
"""
import collections, concurrent.futures, json, os, re, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402

PEARL_WORK = os.path.join(ROOT, 'work', 'pearl')
NOTES = os.path.join(ROOT, 'notes', 'PLATINUM_EVENTS.md')
WAITING = os.path.join(ROOT, 'data', 'platinum', 'events_waiting.json')
SPRITE_LIMIT = 30                       # patches/sinnoh_story.py
HEAL_REACH = 5                          # tiles: Black 2's heal looks for the machine within 5 tiles of the player
NURSE_GFX = 26                          # OBJ_EVENT_GFX_POKECENTER_NURSE
# Zones of later steps (the brief): their events convert as the rest, their findings are listed, not failed
LATER = [('step 7: the Distortion World', re.compile(r'MAP_DISTORTION_WORLD')),
         ('step 8: the Battle Frontier', re.compile(r'MAP_BATTLE_(FRONTIER|FACTORY|HALL|CASTLE|ARCADE|TOWER)'))]
STEP4 = re.compile(r'MAP_(HEARTHOME_GYM|ETERNA_GYM|VEILSTONE_GYM|SNOWPOINT_GYM|GREAT_MARSH|MOUNT_CORONET_SPEAR_PILLAR|'
                   r'SPEAR_PILLAR|POKEMON_LEAGUE_(ENTRANCE|AARON|BERTHA|FLINT|LUCIAN|CYNTHIA|HALL_OF_FAME))')
# Step 4's Gym findings that are Platinum's own design (2026-11-02, plat-gyms; the zones by Pearl's names, which Platinum's
# rebuilt Gyms took over): (zone regex, kind, finding regex, why). They go to the notes, not to step 4's list.
GYM_DESIGN = [
    (r'MAP_ETERNA_GYM', 'warp', r'warp 0 at \(16, 29\) -> MAP_ETERNA_GYM_ENTRANCE warp 1: arrival \(11, -1\)',
     "Platinum's zone 68 is the leftover DP Gym room: its only way in, the Gym's warp 1 at (11, 0), is in the Gym's top "
     "wall, so nobody reaches it"),
    (r'MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM', 'warp pair', r'warp [02] at \((11|12), 7\)',
     "Platinum's entrance room: (11, 7) and (12, 7) are walled in (DP leftovers), nobody reaches them"),
    (r'MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_[12]|MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM', 'warp pair', r'',
     "Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at "
     "the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, "
     "src/pearlb2/plat_gyms/plat_hearthome_gym.c)"),
]

# Black 2's commands that show a line (b2_script_check.MSG_ARGS: SystemMsg(Async), ActorMsg, ParentActorMsg, MsgPlaceSign,
# ActorMsgGendered): a sign's script must reach one
MSG_OPS = {52, 53, 60, 61, 67, 72}


def later(name):
    return next((why for why, rx in LATER if rx.search(name)), None)


def b2_obj_codes():
    """{name: value} of pokebw2's generated/obj_codes.txt (values run on from 0, '= X' restarts them)."""
    out, v = {}, 0
    for line in open(os.path.join(ROOT, 'external', 'pokebw2', 'generated', 'obj_codes.txt')):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, _, val = line.partition('=')
        if val.strip():
            v = int(val.strip(), 0)
        out[name.strip()] = v
        v += 1
    return out


# ------------------------------------------------------------------------------------------------------- heights
HEIGHTS = os.path.join(version.WORLD_WORK, 'heights')   # this version's converted tile heights (--heights), git-ignored


_WORKER = {}


def _chunk_heights(job):
    """One chunk converted (a worker of write_heights): (chunk, kind, heights, low heights)."""
    c, mid, x, z, ow = job
    import pearl_chunk
    if not _WORKER:
        _WORKER['tables'] = pearl_chunk.tables()
        _WORKER['mats'] = {}
    slopes, offsets = _WORKER['tables']
    if mid not in _WORKER['mats']:
        _WORKER['mats'][mid] = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', f'{mid:03d}.json')))
    P = type('P', (), {'matrix': staticmethod(lambda m: _WORKER['mats'][m])})
    data, rep = pearl_chunk.convert(c, slopes, offsets, pearl_chunk.neighbours(P.matrix(mid), x, z),
                                    pearl_chunk.ENTRANCES if ow else ())
    return (c, 'overworld' if ow else 'rooms', {f'{tx},{tz}': y for (tx, tz), y in rep['heights'].items()},
            {f'{tx},{tz}': y for (tx, tz), y in (rep['heights_low'] or {}).items()})


def write_heights(jobs=6):
    """Every chunk of the version's world converted as sinnoh_world and sinnoh_rooms do (pearl_chunk.convert, with its
    first cell's neighbours; outdoors with the entrance mats as bump warps): its tile heights, into HEIGHTS, the same
    shapes as work/world/heights_*.json, which hold the last build's (Pearl's, in a tree that has built Pearl). Six
    processes; a chunk done is kept (HEIGHTS/partial.json), so a run cut short goes on where it stopped."""
    from patches import sinnoh_events
    P = sinnoh_events.Planner()
    world = P.world
    first = {}
    m0 = P.matrix(0)
    for z in range(m0['height']):
        for x in range(m0['width']):
            c = m0['maps'][z][x]
            if c != 0xffff and str(c) in world['chunks']:
                first.setdefault(c, (0, x, z, True))
    for r in world['rooms']['zones'].values():
        m = P.matrix(r['pearl_matrix'])
        for z in range(m['height']):
            for x in range(m['width']):
                c = m['maps'][z][x]
                if c != 0xffff and str(c) in world['rooms']['chunks']:
                    first.setdefault(c, (r['pearl_matrix'], x, z, False))
    os.makedirs(HEIGHTS, exist_ok=True)
    part = os.path.join(HEIGHTS, 'partial.json')
    done = json.load(open(part)) if os.path.exists(part) else {}
    todo = [(c,) + first[c] for c in sorted(first) if str(c) not in done]
    with concurrent.futures.ProcessPoolExecutor(jobs) as ex:
        for k, (c, kind, hs, low) in enumerate(ex.map(_chunk_heights, todo, chunksize=4)):
            done[str(c)] = [kind, hs, low]
            if k % 50 == 49:
                json.dump(done, open(part, 'w'))
    out = {k: {} for k in ('overworld', 'rooms', 'overworld_low', 'rooms_low')}
    for c, (kind, hs, low) in done.items():
        out[kind][c] = hs
        if low:
            out[kind + '_low'][c] = low
    for k, v in out.items():
        json.dump(v, open(os.path.join(HEIGHTS, f'heights_{k}.json'), 'w'))
    os.replace(part, os.path.expanduser(f'~/.Trash/platinum_heights_partial_{os.getpid()}.json')) if os.path.exists(part) else None
    print(f'{len(first)} chunks ({len(todo)} converted now) -> {HEIGHTS}')


def version_heights(pe):
    """pearl_events.Heights reading this version's converted heights (HEIGHTS) where --heights wrote them, else the last
    build's (work/world)."""
    h = pe.Heights()
    if os.path.isdir(HEIGHTS):
        h.h, h.low = {}, {}
        for name, into in (('heights_overworld.json', h.h), ('heights_rooms.json', h.h),
                           ('heights_overworld_low.json', h.low), ('heights_rooms_low.json', h.low)):
            for c, hs in json.load(open(os.path.join(HEIGHTS, name))).items():
                into[int(c)] = {tuple(map(int, k.split(','))): y for k, y in hs.items()}
    return h


# ------------------------------------------------------------------------------------------------------------ data
class World:
    def __init__(self):
        import pearl_story, pearl_ids, pearl_events, sinnoh_story
        from patches import sinnoh_events
        self.pe, self.ss, self.se = pearl_events, sinnoh_story, sinnoh_events
        self.pd = pearl_story.PearlData()
        self.ids = pearl_ids.Ids()
        self.heights = version_heights(pearl_events)
        self.gen_s, self.gen_t = sinnoh_story.generated()
        self.by_num = self.pd.zones_of_script_file()
        self.file_of = {z['id']: num for num, zs in self.by_num.items() for z in zs if num in self.gen_s}
        self.pz = json.load(open(os.path.join(PEARL_WORK, 'zones.json')))
        self.planner = sinnoh_events.Planner()
        self._pev = {}

    def pearl_events(self, zid):
        """Pearl's events of a shared zone (work/pearl), None for Platinum's new zones."""
        if zid >= len(self.pz):
            return None
        n = self.pz[zid]['events']
        if n not in self._pev:
            self._pev[n] = json.load(open(os.path.join(PEARL_WORK, 'events', f'{n:03d}.json')))
        return self._pev[n]

    def installed(self):
        return sorted(self.pd.b2_zone)


def script_entries(path):
    """[label of each ScriptEntry] of a generated (or Pearl's) zone script source, in order (entry 1 first)."""
    out, on = [], False
    for line in open(path, encoding='utf-8'):
        m = re.match(r'\s*ScriptEntry\s+(\w+)', line)
        if m:
            out.append(m.group(1)); on = True
        elif on and 'ScriptEntriesEnd' in line:
            break
    return out


def assemble_all(paths):
    """{path: binary} with pokebw2's assembler, in parallel (patches/scripts.assemble)."""
    import scripts as scripts_patch
    out = {}
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for p, b in zip(paths, ex.map(scripts_patch.assemble, paths)):
            out[p] = b
    return out


# ------------------------------------------------------------------------------------------------------- the diff
def obj_key(o):
    return (o['graphics_id'], o['x'], o['z'])


def diff_zone(pev, tev):
    """What Platinum changed in a shared zone's events. People are matched as the player sees them, not by local id
    (Platinum renumbers them): the same sprite on the same tile is the same person; then the same sprite with the same
    script (else the same local id) elsewhere has moved; the same tile with another sprite is a re-cast; the rest are
    added or removed. Warps, signs and step triggers by index: moved, new, re-aimed."""
    d = collections.defaultdict(list)
    P = [o for o in pev['object_events'] if o['script'] != 0xFFFF]      # (copies of a neighbour's objects: theirs)
    T = [o for o in tev['object_events'] if o['script'] != 0xFFFF]
    left_p, left_t = list(P), []
    for o in T:
        m = next((p for p in left_p if obj_key(p) == obj_key(o)), None)
        if m is None:
            left_t.append(o)
        else:
            left_p.remove(m)
            if (m['movement_type'], m['initial_dir']) != (o['movement_type'], o['initial_dir']):
                d['behaviour'].append((m, o))
    rest = []
    for o in left_t:
        m = next((p for p in left_p if p['graphics_id'] == o['graphics_id'] and p['script'] == o['script']), None) or \
            next((p for p in left_p if p['graphics_id'] == o['graphics_id'] and p['id'] == o['id']), None)
        if m is not None:
            left_p.remove(m)
            d['moved'].append((m, o))
        else:
            rest.append(o)
    for o in rest:
        m = next((p for p in left_p if (p['x'], p['z']) == (o['x'], o['z'])), None)
        if m is not None:
            left_p.remove(m)
            d['recast'].append((m, o))
        else:
            d['added'].append(o)
    d['removed'] = left_p
    pw, tw = pev['warp_events'], tev['warp_events']
    ptiles = {(w['x'], w['z']) for w in pw}
    for i, w in enumerate(tw):
        if i >= len(pw):
            d['warp_new'].append((i, w, None if (w['x'], w['z']) not in ptiles else 'on a tile Pearl had a warp on'))
        elif (pw[i]['x'], pw[i]['z']) != (w['x'], w['z']):
            d['warp_moved' if (w['x'], w['z']) not in ptiles else 'warp_renumbered'].append((i, pw[i], w))
        elif (pw[i]['dest_header_id'], pw[i]['dest_warp_id']) != (w['dest_header_id'], w['dest_warp_id']):
            d['warp_reaimed'].append((i, pw[i], w))
    d['warp_removed'] = [(i, w) for i, w in enumerate(pw) if i >= len(tw)]
    for kind, key in (('bg', 'bg_events'), ('trigger', 'coord_events')):
        a, b = pev[key], tev[key]
        for i, e in enumerate(b):
            if i >= len(a):
                d[f'{kind}_new'].append((i, e))
            elif (a[i]['x'], a[i]['z']) != (e['x'], e['z']):
                d[f'{kind}_moved'].append((i, a[i], e))
            elif kind == 'trigger' and (a[i]['var'], a[i]['value'], a[i]['script']) != (e['var'], e['value'], e['script']):
                d['trigger_changed'].append((i, a[i], e))
        d[f'{kind}_removed'] = [(i, e) for i, e in enumerate(a) if i >= len(b)]
    return d


# ------------------------------------------------------------------------------------------------------- the check
class Report:
    def __init__(self):
        self.problems = []                      # (zone name, kind, text): fail the run
        self.later = []                         # (step, zone name, kind, text)
        self.step4 = []                         # (zone name, kind, text): gimmicks of step 4's rooms
        self.notes = []                         # (zone name, kind, text): as Pearl, or kept on purpose
        self.waiting_scripts = []               # dicts
        self.sprites = collections.defaultdict(lambda: collections.Counter())   # gfx -> {zone: count}
        self.left_out = []                      # (zone, object id, gfx, tile, as in Pearl)
        self.sprite_counts = {}                 # zone -> different sprites

    def add(self, zone, kind, text, as_pearl=False, gimmick=False):
        why = later(zone)
        design = next((r for zn, k, rx, r in GYM_DESIGN if version.PLATINUM and k == kind and re.fullmatch(zn, zone)
                       and re.search(rx, text)), None)
        if why:
            self.later.append((why, zone, kind, text))
        elif gimmick and design:
            self.notes.append((zone, kind, text + f' (Platinum\'s design: {design})'))
        elif as_pearl:
            self.notes.append((zone, kind, text + ' (as in Pearl)'))
        elif gimmick and STEP4.search(zone):
            self.step4.append((zone, kind, text))
        else:
            self.problems.append((zone, kind, text))


def check_sprites(R):
    """data/platinum/sprite_map.json against Black 2's code names; every Platinum id an installed zone uses has a row."""
    import pearl_events
    codes = b2_obj_codes()
    rows = json.load(open(pearl_events.PLATINUM_SPRITES, encoding='utf-8'))
    for k, r in rows.items():
        if not k.isdigit():
            continue
        if r['code'] is not None and codes.get(r['b2_const']) != r['code']:
            R.add('data/platinum/sprite_map.json', 'sprite', f'{k}: code {r["code"]} is not {r["b2_const"]} '
                  f'({codes.get(r["b2_const"])})')


def check_zone(W, R, zid, binaries, pearl_files):
    """People, signs, triggers and map scripts of one installed zone, as sinnoh_story installs them."""
    pd, ids, pe = W.pd, W.ids, W.pe
    zone = pd.zones[zid]
    name = zone['name']
    ev = pd.events(zone)
    pev = W.pearl_events(zid)
    same_as_pearl = pev is not None and pev == ev
    num = W.file_of.get(zid)
    for o in ev['object_events']:
        if pe.is_sign(o):
            continue
        R.sprites[o['graphics_id']][name] += 1
        why = pe.object_skipped(o, zone)
        if why:
            had = pev is not None and any(obj_key(p) == obj_key(o) for p in pev['object_events'])
            R.left_out.append((name, o['id'], o['graphics_id'], (o['x'], o['z']), had))
    if num is None:
        n = len(ev['object_events']) + len(ev['bg_events']) + len(ev['coord_events'])
        if n:
            R.notes.append((name, 'zone', f'no script file: its {len(ev["object_events"])} people, {len(ev["bg_events"])} '
                                          f'signs and {len(ev["coord_events"])} triggers are not installed (as in Pearl: '
                                          f'{"the same events" if same_as_pearl else "Pearl installs none here either"})'))
            R.waiting_scripts.append(dict(zone=name, b2_zone=pd.b2_zone[zid], kind='zone', what='every event',
                                          why='no script file: Pearl installs no events here either'))
        return
    path = W.gen_s[num]
    labels = script_entries(path)
    binary = binaries[path]
    import b2_script_check
    nscripts = len(b2_script_check.entries(binary))
    if nscripts != len(labels):
        R.add(name, 'script file', f'{os.path.basename(path)}: {len(labels)} entries in the source, {nscripts} assembled')
    starts = b2_script_check.entries(binary)
    shows = {}

    def entry_text(k):
        if k not in shows:
            try:
                ops = b2_script_check.walk(binary, starts[k - 1])
                shows[k] = any(op in MSG_OPS for op in ops.values())
            except ValueError:
                shows[k] = None
        return shows[k]

    def waiting(kind, what, sid, b2sid, why, tile=None):
        # (as in Pearl: Pearl's events have the same reference on the same tile)
        same = pev is not None and tile is not None and any(
            (e['x'], e['z'], e['script']) == (tile[0], tile[1], sid)
            for e in pev['object_events'] + pev['bg_events'] + pev['coord_events'])
        R.waiting_scripts.append(dict(zone=name, b2_zone=pd.b2_zone[zid], kind=kind, what=what, platinum_script=sid,
                                      script=b2sid, tile=tile, why=why + (' (Pearl\'s events have it too)' if same else '')))

    def local_ok(kind, what, sid, b2sid, tile):
        """A local script id of the zone's file: exists and is not the generator's empty entry."""
        if b2sid == 0:
            return True
        if not 0 < b2sid <= nscripts:
            waiting(kind, what, sid, b2sid, f'entry {b2sid} past the file\'s {nscripts}', tile)
            R.add(name, kind, f'{what}: script {b2sid} (Platinum {sid}) past the file\'s {nscripts}')
            return False
        if labels[b2sid - 1] == 'PearlNoScript':
            waiting(kind, what, sid, b2sid, 'the converted file has no script at this entry', tile)
            return False
        return True

    def script_of(sid):
        try:
            return W.ss.script_id(pd, ids, sid), None
        except (KeyError, ValueError) as e:
            return None, str(e).strip("'")

    # people
    for o in pe.kept_objects(pd, zone):
        what = f'person {o["id"]} (gfx {o["graphics_id"]}) at {(o["x"], o["z"])}'
        flag = pe.hide_flag(pd, o) if not pe.item_ball(zone, o) else o['hidden_flag']
        if flag:
            try:
                ids.flag_value(flag)
            except KeyError as e:
                R.add(name, 'person', f'{what}: hide flag {flag:#x} not in the registry ({e})')
        kind = pe.script_kind(o['script'])
        if o['script'] == pe.COPY_SCRIPT:
            continue
        if kind == 'item':
            n = o['script'] - 7000
            if n >= pearl_files['items']:
                waiting('person', what, o['script'], o['script'], f'item ball: global file 1240 has '
                        f'{pearl_files["items"]} entries (b2tools/pearl_items.py)', (o['x'], o['z']))
            continue
        b2sid, err = script_of(o['script'])
        if err:
            waiting('person', what, o['script'], None, err, (o['x'], o['z']))
            continue
        if kind in ('local', 'global'):
            local_ok('person', what, o['script'], b2sid, (o['x'], o['z']))
    # signs (BG events, then the sign objects: pearl_events.entities' order)
    signs = [('bg', i, b) for i, b in enumerate(ev['bg_events'])] + \
            [('object', o['id'], o) for o in ev['object_events'] if pe.is_sign(o) and pe.script_kind(o['script']) != 'none']
    for src, i, b in signs:
        what = f'sign ({src} {i}) at {(b["x"], b["z"])}'
        kind = pe.script_kind(b['script'])
        if kind == 'hidden':
            if b['script'] - 8000 >= pearl_files['hidden']:
                waiting('sign', what, b['script'], b['script'], f'hidden item: global file 1241 has '
                        f'{pearl_files["hidden"]} entries, Pearl\'s table (b2tools/pearl_items.py); parked off the map until then '
                        '(pearl_events.SIGN_OFF_MAP)', (b['x'], b['z']))
            continue
        if kind == 'none':
            pb = pev and [x for x in pev['bg_events'] if (x['x'], x['z']) == (b['x'], b['z']) and x['script'] == b['script']]
            R.add(name, 'sign', f'{what}: runs no script', as_pearl=bool(pb))
            continue
        b2sid, err = script_of(b['script'])
        if err:
            waiting('sign', what, b['script'], None, err, (b['x'], b['z']))
            continue
        if not local_ok('sign', what, b['script'], b2sid, (b['x'], b['z'])):
            continue
        t = entry_text(b2sid)
        if t is None:
            R.add(name, 'sign', f'{what}: script {b2sid} does not decode')
        elif not t and b['script'] not in (pe.TOWN_MAP,):
            # (as Pearl when Pearl's zone has a sign running the same script: the Geonet globe, the TV's rankings)
            pb = pev is not None and any(x['script'] == b['script'] for x in pev['bg_events'] + pev['object_events'])
            R.add(name, 'sign', f'{what}: script {b2sid} (Platinum {b["script"]}) shows no text', as_pearl=pb)
    # step triggers
    for i, c in enumerate(ev['coord_events']):
        what = f'trigger {i} at {(c["x"], c["z"])} {c["width"]}x{c["length"]}'
        try:
            ids.var_value(c['var'])
        except KeyError:
            R.add(name, 'trigger', f'{what}: var {c["var"]:#x} not in the registry')
        b2sid, err = script_of(c['script'])
        if err:
            waiting('trigger', what, c['script'], None, err, (c['x'], c['z']))
            continue
        local_ok('trigger', what, c['script'], b2sid, (c['x'], c['z']))
    # what sinnoh_story builds (it stops the build on these)
    try:
        npcs, sgns, trigs, skipped = pe.entities(pd, zone, ids, W.heights, lambda s: W.ss.script_id(pd, ids, s))
    except Exception as e:                      # noqa: BLE001
        R.add(name, 'entities', f'pearl_events.entities fails: {type(e).__name__}: {e}')
        return
    for k, n in enumerate(m for m in npcs if m['clone']):
        n['uid'] = W.ss.CLONE_UID + k
    uids = [n['uid'] for n in npcs]
    if len(uids) != len(set(uids)):
        R.add(name, 'person', f'local ids repeat: {sorted(u for u in uids if uids.count(u) > 1)}')
    models = {n['model'] for n in npcs}
    R.sprite_counts[name] = len(models)
    if len(models) > SPRITE_LIMIT:
        R.add(name, 'sprites', f'{len(models)} different sprites (Black 2 draws {SPRITE_LIMIT}; past it people are shadows)')
    for kind, objs in (('person', npcs), ('sign', sgns), ('trigger', trigs)):
        for o in objs:
            if 0 < o['script'] < 2000 and o['script'] > nscripts:
                R.add(name, kind, f'script {o["script"]} past the file\'s {nscripts} (sinnoh_story stops here)')
    init, levels = pe.map_script_table(pd, zone, ids)
    for s in levels:
        if s > nscripts:
            R.add(name, 'map script', f'map script {s} past the file\'s {nscripts}')
        elif labels[s - 1] == 'PearlNoScript':
            waiting('map script', f'map script {s}', None, s, 'the converted file has no script at this entry')
    for p in b2_script_check.check(binary, levels):
        R.add(name, 'script file', f'{os.path.basename(path)}: {p}')
    from zones import build_entities
    try:
        e = {'signs': sgns, 'npcs': npcs, 'warps': W.planner.warps(zid)[0], 'triggers': trigs}
        build_entities(e, W.se.EMPTY, init=init)
    except (struct.error, KeyError) as ex:
        R.add(name, 'entities', f'the entity file does not pack: {ex}')
    if len(npcs) > 64 - 1:
        R.add(name, 'person', f'{len(npcs)} people: Black 2 has 64 actors, the player included')


def check_warps(W, R):
    """Every warp: lands on a walkable tile of a real zone, in a cell its zone owns; its partner leads back."""
    import warp_check
    WW = warp_check.Warps('offline')
    region, usable, overworld = WW.reachable()
    pid_of, zones = WW.pid_of, WW.zones
    mat0 = WW.pl.matrix(0)
    INERT, NEXT, OFF = W.se.INERT, W.se.DEST_NEXT_ZONE, warp_check.OFF_MAP
    pearl_pairs = pearl_warp_pairs(W)
    for b2, ws in sorted(WW.warps.items()):
        pid = pid_of[b2]
        name = zones[pid]['name']
        n_ev = len(W.pd.events(zones[pid])['warp_events'])
        on_tile = collections.defaultdict(list)
        for i, w in enumerate(ws):
            if w['x'] >= OFF:
                continue
            x, z = WW.at(w)
            if w['dest_warp'] != INERT:
                on_tile[(x, z)].append(i)
            if w['dest_warp'] in (INERT,) or i >= n_ev:
                continue                       # (arrival points, Turnback Cave's copies: turnback.extra_warps)
            dz, dw = w['dest_zone'], w['dest_warp']
            if dw == NEXT:
                continue                       # the shared Center 2F's way back down, the elevators
            where = f'warp {i} at {(x, z)}'
            if dz not in WW.warps:
                R.add(name, 'warp', f'{where} -> zone {dz}: not installed', gimmick=True)
                continue
            dname = zones[pid_of[dz]]['name']
            if dw >= len(WW.warps[dz]):
                R.add(name, 'warp', f'{where} -> {dname} warp {dw}: it has {len(WW.warps[dz])}', gimmick=True)
                continue
            d = WW.warps[dz][dw]
            if d['x'] >= OFF:
                R.add(name, 'warp', f'{where} -> {dname} warp {dw}, which is off the map (its own room is not installed)', gimmick=True)
                continue
            a = WW.arrival(dz, dw)
            ta = WW.tile(dz, *a)
            onto_mat = d['type'] == 1 and d['dest_warp'] == INERT and ta is not None and ta[0] in warp_check.pearl_chunk_ENTRANCES
            if (ta is None or ta[1]) and not onto_mat:
                R.add(name, 'warp', f'{where} -> {dname} warp {dw}: arrival {a} is {"off the map" if ta is None else "solid"}',
                      as_pearl=pearl_pairs.get((name, (x, z))) == ('bad', dname), gimmick=True)
            if zones[pid_of[dz]]['matrix'] == 0:
                cx, cz = a[0] // 32, a[1] // 32
                owner = mat0['headers'][cz][cx] if 0 <= cz < mat0['height'] and 0 <= cx < mat0['width'] else None
                if owner != pid_of[dz]:
                    oname = zones[owner]['name'] if owner is not None and owner < len(zones) else owner
                    R.add(name, 'warp', f'{where} -> {dname} warp {dw}: arrival {a} is in a cell of {oname}',
                          as_pearl=pearl_pairs.get((name, (x, z), 'cell')) == oname, gimmick=True)
            # its partner leads back: a warp on the tile it lands by (the warp itself; on an entrance mat's arrival
            # point, the mat's own; on a tile several warps share, any of them: a map script switches which is live)
            backs = [v for v in WW.warps[dz] if WW.at(v) == WW.at(d) and v['dest_warp'] != INERT and v['x'] < OFF]
            if not backs or any(v['dest_warp'] == NEXT for v in backs):
                continue
            back = backs[0]

            def leads_back(v):
                if v['dest_zone'] != b2 or v['dest_warp'] >= len(ws):
                    return False
                bx, bz = WW.at(ws[v['dest_warp']])
                return abs(bx - x) <= 1 and abs(bz - z) <= 1
            ok = any(leads_back(v) for v in backs)
            if not ok:
                bt = (zones[pid_of[back['dest_zone']]]['name'] if back['dest_zone'] in pid_of else back['dest_zone'],
                      back['dest_warp'])
                R.add(name, 'warp pair', f'{where} -> {dname} warp {dw}, whose way back leads to {bt[0]} warp {bt[1]}',
                      as_pearl=pearl_pairs.get((name, (x, z), 'pair')) == (dname, bt[0]), gimmick=True)
        moved = set()                          # warps the zone's own map script moves (pl_SetWarpEventPos)
        num = W.file_of.get(pid)
        if num is not None:
            moved = {int(m) for m in re.findall(r'pl_SetWarpEventPos (\d+),', open(W.gen_s[num], encoding='utf-8').read())}
        for (x, z), idx in on_tile.items():
            if len(idx) > 1 and not any(i >= n_ev for i in idx):
                acc = next((r for zn, k, rx, r in warp_check.ACCEPT if k == 'stack' and re.fullmatch(zn, name[4:])
                            and re.search(rx, f'{(x, z)}')), None)
                text = f'{len(idx)} warps on {(x, z)} (warps {idx}): only the first fires'
                if acc:
                    R.notes.append((name, 'warp', text + f' (kept: {acc[:80]}...)'))
                elif len([i for i in idx if i not in moved]) <= 1:
                    R.notes.append((name, 'warp', text + ': Platinum\'s own switch, its map script moves all but '
                                                         'one away (pl_SetWarpEventPos)'))
                else:
                    R.add(name, 'warp', text, as_pearl=pearl_pairs.get((name, (x, z), 'stack')) == len(idx), gimmick=True)
    return WW


def pearl_warp_pairs(W):
    """The same warp findings in Pearl's own data (so a finding Pearl has too is marked as Pearl's): run in a Pearl
    process (this module, --pearl-baseline)."""
    env = {k: v for k, v in os.environ.items() if k != 'PEARL_VERSION'}
    r = subprocess.run([sys.executable, os.path.abspath(__file__), '--pearl-baseline'], env=env, capture_output=True,
                       text=True, timeout=600)
    if r.returncode:
        raise SystemExit('Pearl baseline: ' + r.stderr[-800:])
    out = {}
    for row in json.loads(r.stdout.splitlines()[-1]):
        key = tuple(tuple(k) if isinstance(k, list) else k for k in row[0])
        out[key] = tuple(row[1]) if isinstance(row[1], list) else row[1]
    return out


def pearl_baseline():
    """[(key, value)] of Pearl's warp findings (check_warps' keys), printed as JSON for pearl_warp_pairs."""
    import warp_check
    from patches import sinnoh_events as se
    WW = warp_check.Warps('offline')
    zones, pid_of, mat0 = WW.zones, WW.pid_of, WW.pl.matrix(0)
    out = []
    for b2, ws in sorted(WW.warps.items()):
        name = zones[pid_of[b2]]['name']
        n_ev = len(json.load(open(os.path.join(version.WORLD_WORK, 'events', f"{zones[pid_of[b2]]['events']:03d}.json")))['warp_events'])
        on_tile = collections.Counter()
        for i, w in enumerate(ws):
            if w['x'] >= warp_check.OFF_MAP or w['dest_warp'] == se.INERT:
                continue
            x, z = WW.at(w)
            on_tile[(x, z)] += 1
            if i >= n_ev or w['dest_warp'] == se.DEST_NEXT_ZONE or w['dest_zone'] not in WW.warps:
                continue
            dz, dw = w['dest_zone'], w['dest_warp']
            if dw >= len(WW.warps[dz]) or WW.warps[dz][dw]['x'] >= warp_check.OFF_MAP:
                continue
            dname = zones[pid_of[dz]]['name']
            d = WW.warps[dz][dw]
            a = WW.arrival(dz, dw)
            ta = WW.tile(dz, *a)
            if ta is None or ta[1]:
                out.append(([name, [x, z]], ['bad', dname]))
            if zones[pid_of[dz]]['matrix'] == 0:
                owner = mat0['headers'][a[1] // 32][a[0] // 32]
                if owner != pid_of[dz]:
                    out.append(([name, [x, z], 'cell'], zones[owner]['name']))
            backs = [v for v in WW.warps[dz] if WW.at(v) == WW.at(d) and v['dest_warp'] != se.INERT
                     and v['x'] < warp_check.OFF_MAP]
            if not backs or any(v['dest_warp'] == se.DEST_NEXT_ZONE for v in backs):
                continue
            back = backs[0]
            ok = any(v['dest_zone'] == b2 and v['dest_warp'] < len(ws) and
                     abs(WW.at(ws[v['dest_warp']])[0] - x) <= 1 and abs(WW.at(ws[v['dest_warp']])[1] - z) <= 1 for v in backs)
            if not ok:
                bname = zones[pid_of[back['dest_zone']]]['name'] if back['dest_zone'] in pid_of else back['dest_zone']
                out.append(([name, [x, z], 'pair'], [dname, bname]))
        for t, n in on_tile.items():
            if n > 1:
                out.append(([name, list(t), 'stack'], n))
    print(json.dumps(out))


def entities_dump(W, zids):
    """{zone name: {'npcs', 'signs', 'triggers'}} as sinnoh_story builds them, scripts named version-free: a local entry
    as ('local', n), a global one as ('global', Pearl's id), a trainer as ('trainer', its Black 2 id); flags and works
    by their Black 2 numbers."""
    pd, ids, pe = W.pd, W.ids, W.pe
    inv = {v: k for k, v in pd.proxy_ids().items()}
    out = {}
    for zid in zids:
        zone = pd.zones[zid]
        if zid not in W.file_of:
            continue
        try:
            npcs, signs, trigs, _ = pe.entities(pd, zone, ids, W.heights, lambda s: W.ss.script_id(pd, ids, s))
        except Exception as e:                  # noqa: BLE001
            out[zone['name']] = {'error': str(e)}
            continue
        def name(s):
            if s in inv:
                return ['global', inv[s]]
            return ['local', s] if s < 3000 else ['global id', s]
        out[zone['name']] = {'npcs': [dict(n, script=name(n['script'])) for n in npcs],
                             'signs': [dict(n, script=name(n['script'])) for n in signs],
                             'triggers': [dict(n, script=name(n['script'])) for n in trigs]}
    return out


def pearl_entities():
    """entities_dump of every installed zone, in a Pearl process (for check_kept)."""
    W = World()
    print(json.dumps(entities_dump(W, W.installed())))


def check_kept(W, R):
    """Where Platinum didn't change a zone's events, the build installs exactly Pearl's: its people, signs and step
    triggers with every hand fix (heights, facings, sprites, flags, closed places, climbs) equal field by field to what a
    Pearl build installs, the script entries named by what they run. -> (zones compared, zones equal)."""
    env = {k: v for k, v in os.environ.items() if k != 'PEARL_VERSION'}
    r = subprocess.run([sys.executable, os.path.abspath(__file__), '--pearl-entities'], env=env, capture_output=True,
                       text=True, timeout=600)
    if r.returncode:
        raise SystemExit('Pearl entities: ' + r.stderr[-800:])
    pearl = json.loads(r.stdout.splitlines()[-1])
    same = [z for z in W.installed() if W.pearl_events(z) is not None and W.pearl_events(z) == W.pd.events(W.pd.zones[z])]
    mine = entities_dump(W, same)
    equal = 0
    for zname, e in sorted(mine.items()):
        p = pearl.get(zname)
        if p is None:
            continue
        diffs, heights_only = [], []
        # (the sign events the land makes, not the events: wall maps, honey trees, Rock Climb starts; Platinum's own map
        # can add or move them: noted, as its ground is plat-world's)
        land = lambda ss: [x for x in ss if x['script'] in (['global', g] for g in W.pe.ADDED_PROXIES)]   # noqa: E731
        la, lb = land(p.get('signs', [])), land(e.get('signs', []))
        if la != lb:
            R.notes.append((zname, 'land signs', f'its map gives {len(lb)} wall-map, honey-tree or Rock Climb sign events, '
                                                 f'Pearl\'s {len(la)}: Platinum\'s own map'))
        p = dict(p, signs=[x for x in p.get('signs', []) if x not in la])
        e = dict(e, signs=[x for x in e.get('signs', []) if x not in lb])
        for kind in ('npcs', 'signs', 'triggers'):
            a, b = p.get(kind, []), e.get(kind, [])
            if len(a) != len(b):
                diffs.append(f'{kind}: {len(a)} in Pearl, {len(b)} here')
                continue
            for i, (x, y) in enumerate(zip(a, b)):
                d = sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))
                if d == ['y']:                  # (the height of the floor under it: the converted ground, plat-world's)
                    heights_only.append(f'{kind} {i}: y {x["y"]} -> {y["y"]}')
                elif d:
                    diffs.append(f'{kind} {i}: ' + ', '.join(f'{k} {x.get(k)} -> {y.get(k)}' for k in d))
        if 'error' in e or 'error' in p:
            diffs.append(f'error: {e.get("error") or p.get("error")}')
        if diffs:
            R.add(zname, 'kept', 'the same events as Pearl\'s, installed otherwise: ' + '; '.join(diffs[:4]), gimmick=True)
        else:
            equal += 1
        if heights_only:
            R.notes.append((zname, 'floor height', 'the same events as Pearl\'s, on Platinum\'s converted floor (its ground, '
                                                   'plat-world\'s; y in 1/4096 units): ' + '; '.join(heights_only[:4])))
    return len(mine), equal


def check_centers(W, R):
    """Each Pokémon Center 1F: the heal machine prop with Black 2's heal record, near the counter, and the ball resource."""
    import pearl_heal, pearl_doors
    build = pearl_doors.pearl()['build']
    world = json.load(open(version.data_path('sinnoh_world.json')))
    rec = pearl_heal.info(0x10, build[pearl_heal.MACHINE])
    if rec is None or struct.unpack_from('<H', rec, 2)[0] != pearl_heal.HEAL_MACHINE_TYPE:
        R.add('pearl_heal', 'center', f'build model {pearl_heal.MACHINE} of this dump gets no heal record')
    res_rooms = {int(k): v for k, v in world['rooms']['building_res'].items()}
    if res_rooms.get(pearl_heal.BALL) != pearl_heal.BALL_RES:
        R.add('pearl_heal', 'center', f'the heal ball (model {pearl_heal.BALL}) is resource {res_rooms.get(pearl_heal.BALL)}, '
                                      f'not {pearl_heal.BALL_RES:#x} (data/platinum/sinnoh_world.json rooms building_res)')
    out = []
    for zid in W.installed():
        zone = W.pd.zones[zid]
        if not zone['name'].endswith('POKECENTER_1F') and zone['name'] != 'MAP_POKEMON_LEAGUE_LOBBY_1F':
            continue
        if zid not in W.pd.b2_zone or str(zid) not in world['rooms']['zones']:
            continue
        room = world['rooms']['zones'][str(zid)]
        models = world['rooms']['areas'][str(room['pearl_area'])]['models']
        m = W.planner.matrix(zone['matrix'])
        machines = []
        for cz, row in enumerate(m['maps']):
            for cx, c in enumerate(row):
                if c == 0xffff:
                    continue
                for p in W.planner.land(c)['props']:
                    if p['model'] == pearl_heal.MACHINE:
                        machines.append((cx * 32 + 16 + p['pos'][0] / 16, cz * 32 + 16 + p['pos'][2] / 16))
        nurse = [o for o in W.pd.events(zone)['object_events'] if o['graphics_id'] == NURSE_GFX]
        name = zone['name']
        if not machines:
            R.add(name, 'center', 'no heal machine prop (model 123): the heal crashes on melonDS and hardware')
            continue
        if pearl_heal.MACHINE not in models or pearl_heal.BALL not in models:
            R.add(name, 'center', f'area {room["pearl_area"]}\'s pack lacks model {pearl_heal.MACHINE} or {pearl_heal.BALL}')
        if not nurse:
            R.add(name, 'center', 'no nurse')
            continue
        n = nurse[0]
        stand = (n['x'], n['z'] + 2)             # the player at the counter, facing her
        dist = min(max(abs(mx - stand[0]), abs(mz - stand[1])) for mx, mz in machines)
        if dist > HEAL_REACH:
            R.add(name, 'center', f'heal machine {dist:.1f} tiles from the counter (Black 2 looks within {HEAL_REACH})')
        out.append((name, len(machines), round(dist, 1)))
    return out


def check_fixes(W, R):
    """Pearl's fixes keyed by an object, a sign or a tile, against Platinum's events."""
    import pearl_hidden_paths
    pd = W.pd
    by_name = {z['name']: z for z in pd.zones}
    out, moved = [], []

    def same_obj(zname, oid):
        """None when local id oid is the same person in both (the same sprite or the same script), else why not."""
        z = by_name.get(zname)
        if z is None:
            return f'{zname}: no such zone'
        pev = W.pearl_events(z['id'])
        p = next((o for o in pev['object_events'] if o['id'] == oid), None) if pev else None
        t = next((o for o in pd.events(z)['object_events'] if o['id'] == oid), None)
        if p is None or t is None:
            return f'{zname} object {oid}: {"not in Pearl" if p is None else "not in Platinum"}'
        if p['graphics_id'] != t['graphics_id'] and p['script'] != t['script']:
            return f'{zname} object {oid}: Pearl\'s is gfx {p["graphics_id"]} at {(p["x"], p["z"])} running ' \
                   f'{p["script"]}, Platinum\'s gfx {t["graphics_id"]} at {(t["x"], t["z"])} running {t["script"]}'
        if obj_key(p) != obj_key(t):
            moved.append(f'{zname} object {oid}: gfx {p["graphics_id"]} at {(p["x"], p["z"])} -> gfx '
                         f'{t["graphics_id"]} at {(t["x"], t["z"])}, script {p["script"]} -> {t["script"]}')
        return None

    closed = json.load(open(os.path.join(ROOT, 'data', 'pearl_closed_facilities.json')))
    for zname, rows in closed.items():
        if zname == '_doc':
            continue
        for r in rows:
            if 'obj' in r:
                bad = same_obj(zname, r['obj'])
            elif 'bg' in r:
                z = by_name[zname]
                pe, b = W.pearl_events(z['id']), pd.events(z)['bg_events']
                i = r['bg']
                if pe is None:                         # (a row of Platinum's own new zone: its sign must exist)
                    bad = None if i < len(b) else f'{zname} sign {i}: Platinum has {len(b)} signs'
                else:
                    a = pe['bg_events']
                    bad = None if i < len(a) and i < len(b) and (a[i]['x'], a[i]['z'], a[i]['script']) == \
                        (b[i]['x'], b[i]['z'], b[i]['script']) else f'{zname} sign {i}: not the same in Platinum'
            else:
                z = by_name[zname]
                bad = None if not any(c for c in pd.events(z)['coord_events']
                                      if c['x'] < r['x'] + r['w'] and r['x'] < c['x'] + c['width']
                                      and c['z'] < r['z'] + r['h'] and r['z'] < c['z'] + c['length']) else \
                    f'{zname}: a Platinum trigger overlaps the closed-place row at {(r["x"], r["z"])}'
            out.append(('data/pearl_closed_facilities.json', zname, bad))
            if bad:
                R.add(zname, 'fix', f'data/pearl_closed_facilities.json: {bad}')
    for (zname, oid), path in pearl_hidden_paths.OBJECTS.items():
        bad = same_obj(zname, oid)
        out.append(('pearl_hidden_paths.OBJECTS', zname, bad))
        if bad:
            R.add(zname, 'fix', f'pearl_hidden_paths.OBJECTS: {bad}')
    speakers = json.load(open(os.path.join(ROOT, 'data', 'pearl_speakers.json')))
    for zname, lines in speakers.items():
        if zname.startswith('_') or not isinstance(lines, dict) or zname not in by_name:
            continue
        z = by_name[zname]
        for line, uid in lines.items():
            if not isinstance(uid, int):
                continue
            bad = same_obj(zname, uid)
            out.append(('data/pearl_speakers.json', zname, bad))
            if bad:
                R.notes.append((zname, 'fix', f'data/pearl_speakers.json (plat-text\'s): the line\'s speaker {bad}'))
    import pearl_events                     # (Platinum's own climb starts: data/platinum/pearl_rock_climb.json)
    climb = json.load(open(pearl_events.ROCK_CLIMB))
    for zname, rows in climb.items():
        if zname.startswith('_') or zname not in by_name:
            continue
        z = by_name[zname]
        m = W.planner.matrix(z['matrix'])
        for r in rows:
            x, zz = r['bg']
            t = W.planner.tile(m, x, zz)
            bad = None if t and t[0] in (0x4B, 0x4C) else f'{zname}: Rock Climb start {(x, zz)} is behaviour {t and hex(t[0])}'
            out.append((os.path.relpath(pearl_events.ROCK_CLIMB, ROOT), zname, bad))
            if bad:
                R.add(zname, 'fix', bad)
    pc = json.load(open(os.path.join(ROOT, 'data', 'pearl_rock_climb.json')))
    for zname in sorted(set(pc) | set(climb)):
        if not zname.startswith('_') and pc.get(zname) != climb.get(zname):
            R.notes.append((zname, 'rock climb', f'Platinum\'s climb starts differ from Pearl\'s: {len(pc.get(zname, []))} -> '
                                                 f'{len(climb.get(zname, []))} ({os.path.relpath(pearl_events.ROCK_CLIMB, ROOT)})'))
    for line in climb.get('_doc', '').split('Left out (start or landing not walkable in Pearl): ')[1:]:
        R.notes.append(('rock climb', 'left out', line + ' (start or landing has no height in the dump\'s BDHC)'))
    depth = json.load(open(os.path.join(ROOT, 'data', 'people_depth.json')))
    for zname in depth['zones']:
        if zname not in by_name:
            R.add(zname, 'fix', 'data/people_depth.json names a zone Platinum lacks')
        out.append(('data/people_depth.json zones', zname, None if zname in by_name else 'missing'))
    from gen4rom import Rom, narc_members
    pl = narc_members(Rom(os.path.join(ROOT, 'roms', 'pearl.nds')).read('fielddata/land_data/land_data_release.narc'))
    tl = version.slotted('land', narc_members(Rom(version.WORLD_DUMP).read(version.ARCHIVE['land'])))
    for c, tiles in depth.get('solid_tiles', {}).items():
        c = int(c)
        a, b = pl[version.land_id(c) if not version.PLATINUM else c], tl[c]
        same = a[16:16 + 2048] == b[16:16 + 2048]
        bad = None if same else f'room chunk {c}: Platinum changed its tiles (the furniture tiles {tiles} need a look)'
        out.append(('data/people_depth.json solid_tiles', c, bad))
        if bad:
            R.add(f'chunk {c}', 'fix', 'data/people_depth.json: ' + bad)
    for m in moved:
        R.notes.append(('fix', 'same person', m + ': the fix follows it (the same local id)'))
    return out


# --------------------------------------------------------------------------------------------- the rooms' people
def rooms_view(zones, version_env):
    """{(zone, finding line)} of pearl_rooms_view for these zones, in a Pearl or Platinum process."""
    env = {k: v for k, v in os.environ.items() if k != 'PEARL_VERSION'}
    if version_env:
        env['PEARL_VERSION'] = version_env
    out = set()
    if not zones:
        return out
    r = subprocess.run([sys.executable, os.path.join(HERE, 'pearl_rooms_view.py'), '--jobs', '6', *zones], env=env,
                       capture_output=True, text=True, timeout=900, cwd=HERE)
    for line in r.stdout.splitlines():
        m = re.match(r'(\w+) \(\d+\): \((\w)\) (.*)', line)
        if m:
            out.add((m.group(1), m.group(2), m.group(3)))
    return out


def person_label(text):
    """A rooms_view finding without its numbers that move with the person (the line names the object and its tile)."""
    return re.sub(r'\(\d+ px\)', '', text)


# --------------------------------------------------------------------------------------------------------- main
def main(argv):
    if '--pearl-baseline' in argv:
        return pearl_baseline() or 0
    if '--pearl-entities' in argv:
        return pearl_entities() or 0
    if '--heights' in argv:
        return write_heights() or 0
    assert version.PLATINUM, 'run with PEARL_VERSION=platinum'
    quiet = '--quiet' in argv
    W = World()
    R = Report()
    # the global item-ball and hidden-item files the build installs (b2tools/pearl_items.py; version.sources: Platinum's
    # own in work/platinum/src when pearl_items.py ran for it)
    srcs = {os.path.basename(p)[:4]: p for p in version.sources(os.path.join(ROOT, 'src', 'field_scripts'), '.s')}
    pearl_files = {'items': len(script_entries(srcs['1240'])), 'hidden': len(script_entries(srcs['1241'])),
                   'items_path': srcs['1240'], 'hidden_path': srcs['1241']}
    if not srcs['1240'].startswith(version.WORK):
        R.add('global 1240', 'item balls', 'the item balls run Pearl\'s file 1240, whose entries are Pearl\'s balls by Pearl\'s '
              'numbers (Platinum renumbered them): run PEARL_VERSION=platinum python3 b2tools/pearl_items.py')
    check_sprites(R)
    paths = sorted({W.gen_s[n] for n in set(W.file_of.values())})
    binaries = assemble_all(paths)
    for zid in W.installed():
        check_zone(W, R, zid, binaries, pearl_files)
    WW = check_warps(W, R)
    centers = check_centers(W, R)
    fixes = check_fixes(W, R)
    kept = check_kept(W, R)
    import pearl_doors
    doors = pearl_doors.check()
    for k in ('none', 'several', 'stray', 'missing_record'):
        for x in doors[k]:
            R.add('MAP_' + x.split(' ')[0], 'door', f'{k}: {x}', gimmick=True)
    for line in doors['record_lines']:
        if not line[-1]:
            R.add('pearl_doors', 'door', f'door record of model {line[0]} is not a working Black 2 door: {line}')
    items_diff = hidden_items(W)

    # the diff against Pearl
    diffs = {}
    for zid in W.installed():
        pev = W.pearl_events(zid)
        if pev is not None and pev != W.pd.events(W.pd.zones[zid]):
            diffs[zid] = diff_zone(pev, W.pd.events(W.pd.zones[zid]))
    # people Platinum moved or added onto a tile the converted map makes solid (a wall, a counter, a sign): listed for the
    # combined test (Pearl stands some on purpose: behind counters, on tables in scenes)
    for zid, d in diffs.items():
        zone = W.pd.zones[zid]
        m = W.planner.matrix(zone['matrix'])
        for o in [o for _, o in d['moved']] + d['added'] + [o for _, o in d['recast']]:
            if W.pe.is_sign(o) or W.pe.item_ball(zone, o) or W.pe.is_berry_patch(o) or W.pe.object_skipped(o, zone) \
                    or o['graphics_id'] in (84, 85, 86):   # (boulders, rocks, trees stand on their own tiles)
                continue
            t = W.planner.tile(m, o['x'], o['z'])
            if t is None or t[1]:
                R.notes.append((zone['name'], 'person on a solid tile', f'object {o["id"]} (gfx {o["graphics_id"]}) at '
                                f'{(o["x"], o["z"])}: {"off the map" if t is None else "solid"} (moved or added by Platinum'
                                + (f'; hidden by flag {o["hidden_flag"]:#x} until its scene)' if o['hidden_flag'] else ')')))
    rooms = []
    if '--rooms' in argv:
        names = [W.pd.zones[z]['name'] for z, d in diffs.items() if W.pd.zones[z]['matrix'] != 0 and
                 (d['moved'] or d['added'] or d['recast'])]
        names += [W.pd.zones[z]['name'] for z in W.installed() if z >= version.PEARL_ZONES and not later(W.pd.zones[z]['name'])
                  and W.pd.events(W.pd.zones[z])['object_events']]     # (Platinum's new rooms: all their people are new)
        rooms_of = lambda path: {r['name'] for r in json.load(open(path))['rooms']['zones'].values()}   # noqa: E731
        mine = rooms_view([n for n in names if n in rooms_of(version.data_path('sinnoh_world.json'))], 'platinum')
        theirs = rooms_view([n for n in names if n in rooms_of(os.path.join(ROOT, 'data', 'sinnoh_world.json'))], None)
        old = {(z, k, person_label(t)) for z, k, t in theirs}
        rooms = sorted((z, k, t) for z, k, t in mine if (z, k, person_label(t)) not in old and k in 'mn')
        for z, k, t in rooms:
            R.notes.append(('MAP_' + z, 'furniture', f'({k}) {t}'))
    W.ball_count = pearl_files['items']
    write(W, R, WW, diffs, centers, fixes, items_diff, rooms, kept, doors, (pearl_files['items_path'], pearl_files['hidden_path']))
    if not quiet:
        for z, k, t in R.problems:
            print(f'PROBLEM {z}: ({k}) {t}')
    print(f'{len(W.installed())} installed zones, {len(paths)} script files; problems {len(R.problems)}, step 4 '
          f'{len(R.step4)}, later steps {len(R.later)}, notes {len(R.notes)}, scripts waiting {len(R.waiting_scripts)}; '
          f'{os.path.relpath(NOTES, ROOT)}, {os.path.relpath(WAITING, ROOT)}')
    return 1 if R.problems else 0


def hidden_items(W):
    """Platinum's hidden items whose record in Platinum's own table (its arm9, found by its shape: 8-byte records u16 item,
    u8 count, u8 range, u16 0, u16 n) differs from Pearl's record n, which file 1241 gives (b2tools/pearl_items.py reads
    Pearl's table: "Platinum keeps Pearl's hidden items until its own tables are found"). -> (table address, records,
    [(n, Pearl's (item, count), Platinum's or None)]) for the n Platinum's installed zones use."""
    import pearl_items
    from gen4rom import Rom
    d = Rom(version.WORLD_DUMP).data
    off, _, ram, size = struct.unpack_from('<4I', d, 0x20)
    a = d[off:off + size]
    best = (0, None, {})
    for start in range(0, len(a) - 8 * 100, 4):
        recs, n = {}, 0
        while start + 8 * (n + 1) <= len(a):
            item, cnt, rng, pad, k = struct.unpack_from('<HBBHH', a, start + 8 * n)
            if pad or not 0 < item < 600 or not 1 <= cnt <= 99 or rng > 12 or k in recs or k > 400:
                break
            recs[k] = (item, cnt)
            n += 1
        if n > best[0]:
            best = (n, start + ram, recs)
    n, at, plat = best
    pearl = {k: (r['item'], r['count']) for k, r in pearl_items.hidden_items().items()}
    used = {b['script'] - 8000 for z in W.installed() for b in W.pd.events(W.pd.zones[z])['bg_events']
            if W.pe.script_kind(b['script']) == 'hidden'}
    return at, n, [(k, pearl.get(k), plat.get(k)) for k in sorted(used) if pearl.get(k) != plat.get(k)]


# --------------------------------------------------------------------------------------------------------- output
def write(W, R, WW, diffs, centers, fixes, items_diff, rooms, kept, doors, pearl_files_paths):
    pd = W.pd
    import pearl_events
    rows = json.load(open(pearl_events.PLATINUM_SPRITES, encoding='utf-8'))
    pearl_map = json.load(open(os.path.join(ROOT, 'data', 'pearl_sprite_map.json')))
    changed_art = {148: 'Barry', 169: 'Palmer', 206: 'Buneary', 207: 'Happiny'}   # the same people, Platinum's new art
    sprites = []
    for g, zs in sorted(R.sprites.items()):
        r = rows.get(str(g))
        if r is not None and (r.get('stand_in') or r.get('code') is None):
            sprites.append(dict(gfx=g, name=r['pl_name'], code=r['code'], now=r['b2'], step6=r['step6'],
                                objects=sum(zs.values()), zones=dict(sorted(zs.items()))))
        elif r is None and pearl_map.get(str(g), {}).get('code', 0) is None and g not in W.pe.SIGN_GFX and g != 100:
            pm = pearl_map[str(g)]                  # (Pearl's own left-out objects: the book)
            sprites.append(dict(gfx=g, name=pm['pearl_name'], code=None, now='left out, as in Pearl',
                                step6=f'mmodel sheet of {pm["pearl_name"].split("GFX_")[-1].lower()} (Pearl: {pm.get("note", "")[:80]})',
                                objects=sum(zs.values()), zones=dict(sorted(zs.items()))))
        elif g in changed_art and r is None:   # (a row of its own: Platinum's art is in, patches/pearl_npc_sprites)
            sprites.append(dict(gfx=g, name=pearl_map[str(g)]['pearl_name'], code=pearl_map[str(g)]['code'],
                                now=f'Pearl\'s {changed_art[g]} ({pearl_map[str(g)]["b2"][:60]})',
                                step6=f'Platinum\'s new art of {changed_art[g]}', objects=sum(zs.values()),
                                zones=dict(sorted(zs.items()))))
    waiting = {'_doc': 'Written by b2tools/platinum_events.py (PEARL_VERSION=platinum); do not edit. sprites: Platinum '
                       'overworld sprites drawn with a stand-in or left out until step 6 brings Platinum\'s sheets '
                       '(data/platinum/sprite_map.json). scripts: event references (people, signs, step triggers, map '
                       'scripts) with no converted script yet, for the chapter pieces (step 5).',
               'sprites': sprites, 'scripts': R.waiting_scripts,
               'hidden_items': {'_doc': 'hidden items whose Platinum record differs from what file 1241 gives (Pearl\'s '
                                        'table): [item, count]; null = not in that table',
                                'platinum_table': f'{items_diff[0]:#x}' if items_diff[0] else None,
                                'records': items_diff[1],
                                'differ': [dict(script=8000 + n, file_1241=p, platinum=t) for n, p, t in items_diff[2]]}}
    json.dump(waiting, open(WAITING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    L = ['# Platinum\'s events: people, doors, warps, signs, triggers', '',
         'Written by `PEARL_VERSION=platinum python3 b2tools/platinum_events.py`; don\'t edit. What Platinum changed '
         'against Pearl in the installed zones\' events, and the offline check of what a Platinum build installs '
         '(the tool\'s docstring says what each check is). The lists for later pieces are in '
         '`data/platinum/events_waiting.json`.', '']
    L += [f'- Installed zones: {len(W.installed())}; with a script file: {len(W.file_of)}.',
          f'- Problems: {len(R.problems)}. Step 4\'s rooms: {len(R.step4)}. Later steps (7, 8): {len(R.later)}. '
          f'Notes: {len(R.notes)}.',
          f'- Event scripts waiting for the chapter pieces: {len(R.waiting_scripts)}. Sprites waiting for step 6: {len(sprites)}.',
          '']
    if R.problems:
        L += ['## Problems', ''] + [f'- {z}: ({k}) {t}' for z, k, t in R.problems] + ['']
    # the diff
    tot = collections.Counter()
    towns = []
    for zid, d in diffs.items():
        for k, v in d.items():
            tot[k] += len(v)
        if pd.zones[zid]['matrix'] == 0:
            n = len(d['moved']) + len(d['added']) + len(d['removed'])
            if n:
                towns.append((n, zid, d))
    L += ['## What Platinum changed', '',
          f'{len(diffs)} installed zones have other events than Pearl\'s. People (matched by sprite and tile, then by '
          f'sprite and script): {tot["moved"]} moved, {tot["recast"]} re-cast (another sprite on the same tile), '
          f'{tot["added"]} added, {tot["removed"]} removed, {tot["behaviour"]} in place with another movement or facing. Warps: {tot["warp_moved"]} moved, {tot["warp_new"]} new, '
          f'{tot["warp_reaimed"]} aimed elsewhere, {tot["warp_renumbered"]} renumbered, {tot["warp_removed"]} gone. '
          f'Signs: {tot["bg_moved"]} moved, {tot["bg_new"]} new, {tot["bg_removed"]} gone. Step triggers: '
          f'{tot["trigger_moved"]} moved, {tot["trigger_new"]} new, {tot["trigger_changed"]} changed, '
          f'{tot["trigger_removed"]} gone.', '',
          '### Outdoor zones by people moved, added or removed', '',
          '| Zone | Black 2 zone | Moved | Added | Removed | Moved (sprite: Pearl\'s tile -> Platinum\'s) |', '|---|---|---|---|---|---|']
    for n, zid, d in sorted(towns, key=lambda t: -t[0]):
        ex = '; '.join(f'{o["graphics_id"]}: {(p["x"], p["z"])} -> {(o["x"], o["z"])}' for p, o in d['moved'][:4]) + \
            (' ...' if len(d['moved']) > 4 else '')
        L.append(f'| {pd.zones[zid]["name"][4:]} | {pd.b2_zone[zid]} | {len(d["moved"])} | {len(d["added"])} | '
                 f'{len(d["removed"])} | {ex} |')
    L += ['', '### New and moved warps', '', '| Zone | Black 2 zone | Warp | Tile | Was | Leads to |', '|---|---|---|---|---|---|']
    zn = lambda h: pd.zones[h]['name'][4:] if h < len(pd.zones) else f'{h:#x}'   # noqa: E731
    for zid, d in sorted(diffs.items(), key=lambda kv: (pd.zones[kv[0]]['matrix'] != 0, pd.zones[kv[0]]['name'])):
        for i, w, why in d['warp_new']:
            L.append(f'| {pd.zones[zid]["name"][4:]} | {pd.b2_zone[zid]} | {i} (new) | {(w["x"], w["z"])} | {why or "-"} | '
                     f'{zn(w["dest_header_id"])} warp {w["dest_warp_id"]} |')
        for i, p, w in d['warp_moved'] + d['warp_renumbered']:
            L.append(f'| {pd.zones[zid]["name"][4:]} | {pd.b2_zone[zid]} | {i} | {(w["x"], w["z"])} | {(p["x"], p["z"])} | '
                     f'{zn(w["dest_header_id"])} warp {w["dest_warp_id"]} |')
        for i, p, w in d['warp_reaimed']:
            L.append(f'| {pd.zones[zid]["name"][4:]} | {pd.b2_zone[zid]} | {i} (aimed elsewhere) | {(w["x"], w["z"])} | '
                     f'{zn(p["dest_header_id"])} warp {p["dest_warp_id"]} | {zn(w["dest_header_id"])} warp {w["dest_warp_id"]} |')
    new_zone_warps = [(zid, i, w) for zid in W.installed() if zid >= version.PEARL_ZONES
                      for i, w in enumerate(pd.events(pd.zones[zid])['warp_events'])]
    L += ['', f'Platinum\'s new zones (685-718) have {len(new_zone_warps)} warps of their own, all new; their rows are in the '
          'check below.', '']
    # sprites
    L += ['## Sprites waiting for step 6', '',
          'Platinum\'s own sprites have no sheet in the build yet: each is drawn with the existing code that shows the same '
          'person, or the nearest (data/platinum/sprite_map.json), or left out. Changed art of the same people is listed '
          'too.', '', '| Graphics | Name | Drawn now as | Objects | Zones | Step 6 brings |', '|---|---|---|---|---|---|']
    if not sprites:
        L.append('| - | none: every sprite the installed zones use shows Platinum\'s own picture (step 6, '
                 'patches/pearl_npc_sprites) | | | | |')
    for s in sprites:
        zs = ', '.join(f'{k[4:]} {v}' for k, v in list(s['zones'].items())[:5]) + (' ...' if len(s['zones']) > 5 else '')
        L.append(f'| {s["gfx"]} | {s["name"].split("OBJ_EVENT_GFX_")[-1]} | {s["now"] if s["code"] is not None else "left out"} | {s["objects"]} | '
                 f'{zs} | {s["step6"]} |')
    # scripts
    by = collections.Counter((w['kind'], w['why'].split(':')[0]) for w in R.waiting_scripts)
    L += ['', '## Event scripts waiting for the chapter pieces', '',
          f'{len(R.waiting_scripts)} references (all in data/platinum/events_waiting.json), by kind and reason:', '']
    L += [f'- {k}: {why} ({n})' for (k, why), n in sorted(by.items(), key=lambda kv: -kv[1])]
    at, nrec, hd = items_diff
    L += ['', f'Item balls run {os.path.relpath(pearl_files_paths[0], ROOT)} ({W.ball_count} entries). Hidden items run '
          f'{os.path.relpath(pearl_files_paths[1], ROOT)}, made from Pearl\'s table (b2tools/pearl_items.py): '
          f'{len(hd)} of the hidden items Platinum\'s zones use get another item or count than Platinum\'s own table '
          f'gives (its arm9 at {at:#x}, {nrec} records, numbers up to {max((k for k, _, _ in hd), default=0)}); '
          'the list is in the JSON.']
    # the rest of the check
    busiest = sorted(R.sprite_counts.items(), key=lambda kv: -kv[1])[:6]
    L += ['', '## Doors and sprite counts', '',
          f'Doors (pearl_doors.check): {doors["door_warps"]} door warps, {doors["one"]} with exactly one door prop in '
          f'Black 2\'s search box; {len(doors["stray"])} other warps would open a door ({len(doors["accepted"])} accepted); '
          f'{len(doors["record_lines"])} door models, every record a working Black 2 door.', '',
          f'Different sprites per zone (Black 2 draws {SPRITE_LIMIT} besides the player\'s two): the busiest are ' +
          ', '.join(f'{z[4:]} {n}' for z, n in busiest) + '.']
    L += ['', '## Pokémon Centers', '', f'{len(centers)} Centers checked: each 1F has the heal machine prop (build model '
          f'123 with Black 2\'s heal record; the balls are resource 0x62) within {HEAL_REACH} tiles of the counter: ' +
          ', '.join(f'{n[4:]} {d}' for n, _, d in centers) + ' tiles.', '']
    L += ['## Zones Platinum didn\'t change', '', f'{kept[1]} of {kept[0]} zones whose events are Pearl\'s, byte for byte, install '
          'what a Pearl build installs, field by field (people, signs, step triggers, every hand fix; scripts named by '
          'what they run); a height that follows Platinum\'s own floor is noted below ("floor height").', '']
    L += ['## Pearl\'s fixes keyed by an object, a sign or a tile', '',
          f'{sum(1 for f in fixes if not f[2])} of {len(fixes)} still find what they were made for.']
    L += [f'- {a} {b}: {c}' for a, b, c in fixes if c]
    if R.step4:
        L += ['', '## Step 4\'s rooms', ''] + [f'- {z}: ({k}) {t}' for z, k, t in R.step4]
    if R.later:
        L += ['', '## Left for later steps', '', 'Their events convert as the rest; these findings are those steps\'.', '']
        L += [f'- {w}: {z}: ({k}) {t}' for w, z, k, t in R.later]
    if R.notes:
        L += ['', '## Notes', ''] + [f'- {z}: ({k}) {t}' for z, k, t in R.notes]
    open(NOTES, 'w', encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
