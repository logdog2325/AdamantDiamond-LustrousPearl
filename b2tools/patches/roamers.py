"""Pearl's roaming Pokémon, Mesprit and Cresselia, and the Trophy Garden's daily Pokémon (2026-10-26; notes/ENCOUNTERS.md
"Roamers"). List it after sinnoh_pokedex (it reads town_map's places and the built wild tables, as the AREA page).

The code is the decomp's src/pearlb2/resident/roamers.c (Black 2's own roamer save, encounter and flee AI, with Pearl's
release, moves, after-battle update, AREA page and Pokétch API added; its comment has Pearl's rules). This patch gives
it gPearlB2Roamers (NULL: Black 2's behaviour, nothing roams):
- the zone of each of Pearl's 29 roaming places (pokediamond's UNK_020F7460 order: Routes 201-222, Valley Windworks
  and Fuego Ironworks outside), from data/sinnoh_world.json;
- each place's spot on the Pokédex's AREA page (the habitat index sinnoh_pokedex gives the zone: its town_map record's
  first record) and its kinds (walking 0x01 / surfing 0x08, from the zone's built wild tables);
- what releases each roamer, the flags Pearl's scenes set (src/include/pearl.h): Mesprit, Verity Cavern's
  FLAG_HIDE_VERITY_CAVERN_MESPRIT (0x1FD) once Spear Pillar is over (VAR_SPEAR_PILLAR_STATE 0x4098 >= 4: the scene sets
  0x1FD right before its CreateRoamer 0; the new game sets it too and Spear Pillar clears it); Cresselia, Fullmoon
  Island's FLAG_MET_CRESSELIA (0x11F, right after its CreateRoamer 1);
- the Trophy Garden's zone and the two works Mr. Backlot's script sets (PVAR_TROPHY_GARDEN_1/2: species, 0 = none).

Platinum (plat-trades, 2026-11-07): five roamers, and gPearlB2RoamersExt (resident/roamers.c PearlB2RoamersExt) besides:
Mesprit and Cresselia (Lv 50) in Black 2's two slots, Oak's Moltres, Zapdos and Articuno (Lv 60) in three more (save block
0x41); which slot each of the scripts' numbers is (Platinum's ROAMING_SLOT_*); Platinum's own release flags, by name in its
registry (data/platinum/pearl_story_ids.json): Cresselia FLAG_MET_CRESSELIA (Fullmoon Island sets it right after its
ActivateRoamingPokemon), the birds FLAG_ACTIVATED_ROAMING_LEGENDARY_BIRDS (Oak, right after the three), Mesprit none
(Platinum's new game sets FLAG_HIDE_VERITY_CAVERN_MESPRIT already, so no flag marks Verity Cavern's scene: its
ActivateRoamingPokemon, extension 0xA8, releases it; Pearl's flag id there, 559, is Platinum's
FLAG_HIDE_ETERNA_CITY_GALACTIC_GRUNTS); and Platinum's VAR_ROAMING_*_STATE works, which a KO (2) or a catch (1) sets, as
Platinum's roamer_after_battle.c does (its Hall of Fame and Oak read them). Every flag and work is resolved by its Gen 4
name in the version's registry (Pearl's give the ids its 1.0 had). The places and neighbours are the same 29 in both games
(the test checks Platinum's against its dump).

    PEARL_VERSION=platinum python3 b2tools/patches/roamers.py test     the offline test of the release rows and slots
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402
sys.path.insert(0, HERE)

# Pearl's roaming places, by Pearl map id (pokediamond arm9/asm/unk_020603B0.s UNK_020F7460)
PEARL_PLACES = (342, 343, 344, 345, 346, 347, 349, 350, 353, 354, 356, 362, 363, 365, 366,
                367, 371, 373, 380, 382, 383, 385, 388, 391, 467, 392, 395, 200, 204)
# (flag, work, minimum) per Black 2 slot, 0 Mesprit, 1 Cresselia, by their Gen 4 names in the version's registry
# (version.data_path('pearl_story_ids.json')): Pearl's 1.0 rows (559, 0x4069 >= 4; 361), and Platinum's own (above)
RELEASE = {'pearl': (('FLAG_HIDE_VERITY_CAVERN_MESPRIT', 'VAR_SPEAR_PILLAR_STATE', 4), ('FLAG_MET_CRESSELIA', None, 0)),
           'diamond': (('FLAG_HIDE_VERITY_CAVERN_MESPRIT', 'VAR_SPEAR_PILLAR_STATE', 4), ('FLAG_MET_CRESSELIA', None, 0)),
           'platinum': ((None, None, 0), ('FLAG_MET_CRESSELIA', None, 0))}
# More slots (gPearlB2RoamersExt): (species, level, the scripts' slot, release flag, state var) per slot, by Gen 4 names.
# Platinum's from pokeplatinum roaming_pokemon.c RoamingPokemon_ActivateSlot and its scripts (verity_cavern,
# fullmoon_island_forest, eterna_city_south_house, pokemon_league_hall_of_fame). Pearl and Diamond: none (their two slots).
SPECIES_MESPRIT, SPECIES_CRESSELIA, SPECIES_MOLTRES, SPECIES_ZAPDOS, SPECIES_ARTICUNO = 481, 488, 146, 145, 144
EXT_SLOTS = {'pearl': (), 'diamond': (),
             'platinum': ((SPECIES_MESPRIT, 50, 0, None, 'VAR_ROAMING_MESPRIT_STATE'),
                          (SPECIES_CRESSELIA, 50, 1, 'FLAG_MET_CRESSELIA', 'VAR_ROAMING_CRESSELIA_STATE'),
                          (SPECIES_MOLTRES, 60, 3, 'FLAG_ACTIVATED_ROAMING_LEGENDARY_BIRDS', 'VAR_ROAMING_MOLTRES_STATE'),
                          (SPECIES_ZAPDOS, 60, 4, 'FLAG_ACTIVATED_ROAMING_LEGENDARY_BIRDS', 'VAR_ROAMING_ZAPDOS_STATE'),
                          (SPECIES_ARTICUNO, 60, 5, 'FLAG_ACTIVATED_ROAMING_LEGENDARY_BIRDS', 'VAR_ROAMING_ARTICUNO_STATE'))}
SLOTS_MAX, GAME_SLOTS, NONE = 5, 6, 0xFF         # resident/roamers.c ROAM_SLOTS_MAX, ROAM_GAME_SLOTS, ROAM_NONE
EXT_SIZE = 44
TROPHY_GARDEN = 'MAP_TROPHY_GARDEN'
TROPHY_WORKS = ('PVAR_TROPHY_GARDEN_1', 'PVAR_TROPHY_GARDEN_2')
# Chapter 9b's ids for the Trophy Garden's works (pearl.h after its merge has them; until then these)
TROPHY_WORKS_9B = {'PVAR_TROPHY_GARDEN_1': 0x40F5, 'PVAR_TROPHY_GARDEN_2': 0x40F6}
LAND, WATER = 0x01, 0x08
STATE = {}                                       # apply() -> apply_code()


def pearl_ids():
    """{name: value} of the version's pearl.h PFLAG_/PVAR_ defines (src/include/pearl.h; Platinum's src/include/platinum)."""
    out = {}
    header = os.path.join(ROOT, 'src', 'include', 'platinum' if version.PLATINUM else '', 'pearl.h')
    for m in re.finditer(r'^#define (P(?:FLAG|VAR)_\w+)\s+(0x[0-9A-Fa-f]+|\d+)', open(header).read(), re.M):
        out[m.group(1)] = int(m.group(2), 0)
    return out


def gen4_ids():
    """{Gen 4 flag or var name: its Black 2 id} of the version's registry (data[/platinum]/pearl_story_ids.json)."""
    reg = json.load(open(version.data_path('pearl_story_ids.json')))
    out = {}
    for kind in ('flags', 'vars'):
        for v in reg[kind].values():
            if v.get('name'):
                b2 = v['b2']
                out[v['name']] = int(b2, 16) if isinstance(b2, str) else b2
    return out


def release_rows():
    """[(flag, work, minimum)] of the two Black 2 slots, as Black 2 ids (0: none)."""
    ids = gen4_ids()
    return [(ids[f] if f else 0, ids[w] if w else 0, n) for f, w, n in RELEASE[version.VERSION]]


def ext_blob():
    """gPearlB2RoamersExt (resident/roamers.c PearlB2RoamersExt, 44 B), or None for a version with only two slots."""
    slots = EXT_SLOTS[version.VERSION]
    if not slots:
        return None
    ids = gen4_ids()
    n = len(slots)
    assert 2 < n <= SLOTS_MAX, n
    pad = lambda xs, k, fill=0: list(xs) + [fill] * (k - len(xs))
    game = [NONE] * GAME_SLOTS
    for k, s in enumerate(slots):
        game[s[2]] = k
    blob = struct.pack('<H5H5B6Bx5H5H', n, *pad([s[0] for s in slots], SLOTS_MAX), *pad([s[1] for s in slots], SLOTS_MAX),
                       *game, *pad([ids[s[3]] if s[3] else 0 for s in slots], SLOTS_MAX),
                       *pad([ids[s[4]] if s[4] else 0 for s in slots], SLOTS_MAX))
    assert len(blob) == EXT_SIZE, len(blob)
    return blob


def table(files):
    """The gPearlB2Roamers blob (resident/roamers.c PearlB2Roamers) and a summary."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('sinnoh_pokedex_roam', os.path.join(HERE, 'sinnoh_pokedex.py'))
    dex = importlib.util.module_from_spec(spec); spec.loader.exec_module(dex)
    world = json.load(open(version.data_path('sinnoh_world.json')))
    zones = [world['zones'][str(p)]['b2_zone'] for p in PEARL_PLACES]
    tm = dex._tm()
    f21 = tm.read_file21(files)
    recs, ztab = f21['records'], f21['zone_table']
    rzones = [r[0] for r in recs]
    bits = dex.zone_bits(files, ztab)
    places, kinds = [], []
    for z in zones:
        rec = ztab[z] if z < len(ztab) else 0xFF
        places.append(0xFF if rec == 0xFF else rzones.index(rzones[rec]))
        k = 0
        for b in bits.get(z, {}).values():
            k |= b & (LAND | WATER)
        kinds.append(k or LAND)
    ids = pearl_ids()
    rel = release_rows()
    rooms = world['rooms']['zones']
    tg = next(v['b2_zone'] for v in rooms.values() if v['name'] == TROPHY_GARDEN)
    works = [ids.get(w, TROPHY_WORKS_9B[w]) for w in TROPHY_WORKS]
    blob = struct.pack('<H29H29B29B', len(PEARL_PLACES), *zones, *places, *kinds)
    blob += struct.pack('<2H2H2H', rel[0][0], rel[1][0], rel[0][1], rel[1][1], rel[0][2], rel[1][2])
    blob += struct.pack('<3H', tg, *works)
    assert len(blob) == 136, len(blob)
    missing = [i for i, p in enumerate(places) if p == 0xFF]
    return blob, (f'{len(zones)} places (zones {zones[0]}..{zones[-1]}; AREA page spots for '
                  f'{len(zones) - len(missing)}{", none for " + str(missing) if missing else ""}; '
                  f'{sum(1 for k in kinds if k & WATER)} with surfing), release flags '
                  f'{[hex(r[0]) for r in rel]}, Trophy Garden zone {tg} works {[hex(w) for w in works]}')


def apply(files):
    STATE['blob'], STATE['summary'] = table(files)
    STATE['ext'] = ext_blob()
    if STATE['ext']:
        STATE['summary'] += f'; {len(EXT_SLOTS[version.VERSION])} slots (gPearlB2RoamersExt {len(STATE["ext"])} B)'
    return 'roamers: ' + STATE['summary']


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2Roamers', code)
    if slot is None:
        return 'roamers: no gPearlB2Roamers in this decomp: nothing roams'
    blob = STATE['blob']
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:                                      # a quick non-clean build: the table is there, rewrite it in place
        assert struct.unpack('<H', resident.read(code, old, 2))[0] == len(PEARL_PLACES), 'gPearlB2Roamers: not the table'
        resident.write(code, old, blob)
        base = old
    else:                                        # the table in PearlB2's resident section (b2tools/resident.py)
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    ext = STATE.get('ext')
    if ext:                                      # (plat-trades) Platinum's five slots
        eslot = decomp.symbol('gPearlB2RoamersExt', code)
        assert eslot is not None, 'roamers: the decomp has no gPearlB2RoamersExt (src/pearlb2/resident/roamers.c)'
        eold = struct.unpack('<I', resident.read(code, eslot, 4))[0]
        if eold:
            assert struct.unpack('<H', resident.read(code, eold, 2))[0] == len(EXT_SLOTS[version.VERSION]), \
                'gPearlB2RoamersExt: not the table'
            resident.write(code, eold, ext)
        else:
            ebase, _, _ = resident.install(code, lambda b: (ext, {}))
            resident.write(code, eslot, struct.pack('<I', ebase))
    return f'roamers: table {len(blob)} B at {base:#x} (gPearlB2Roamers {slot:#x}); {STATE["summary"]}'


# ---------------------------------------------------------------------------------------------------------- the test
ROUTE_NAMES = ('MAP_ROUTE_201', 'MAP_ROUTE_202', 'MAP_ROUTE_203', 'MAP_ROUTE_204_SOUTH', 'MAP_ROUTE_204_NORTH',
               'MAP_ROUTE_205_SOUTH', 'MAP_ROUTE_205_NORTH', 'MAP_ROUTE_206', 'MAP_ROUTE_207', 'MAP_ROUTE_208',
               'MAP_ROUTE_209', 'MAP_ROUTE_210_SOUTH', 'MAP_ROUTE_210_NORTH', 'MAP_ROUTE_211_WEST', 'MAP_ROUTE_211_EAST',
               'MAP_ROUTE_212_NORTH', 'MAP_ROUTE_212_SOUTH', 'MAP_ROUTE_213', 'MAP_ROUTE_214', 'MAP_ROUTE_215',
               'MAP_ROUTE_216', 'MAP_ROUTE_217', 'MAP_ROUTE_218', 'MAP_ROUTE_219', 'MAP_ROUTE_220', 'MAP_ROUTE_221',
               'MAP_ROUTE_222', 'MAP_VALLEY_WINDWORKS_EXTERIOR', 'MAP_FUEGO_IRONWORKS_EXTERIOR')


def _c_neighbours():
    """resident/roamers.c's sNeighbours, as [(count, [places])]."""
    src = open(os.path.join(ROOT, 'external', 'pokebw2', 'src', 'pearlb2', 'resident', 'roamers.c')).read()
    body = src[src.index('sNeighbours[ROAM_PLACES][6] = {'):]
    body = body[body.index('{') + 1:body.index('};')]
    rows = [[int(x) for x in r.split(',') if x.strip()] for r in re.findall(r'\{\s*([\d,\s]+)\}', body)]
    return [(r[0], r[1:1 + r[0]]) for r in rows]


def _dump_tables():
    """Platinum's RoamingPokemonRoutes (29 ints) and sNearbyRoutes (29 x {u16 count, u16[5]}), found in its dump."""
    from gen4rom import Rom
    d = Rom(version.WORLD_DUMP).data
    pat = struct.pack('<29i', *PEARL_PLACES)
    routes = [m.start() for m in re.finditer(re.escape(pat), d)]
    first = struct.pack('<12H', 2, 1, 23, 0xFFFF, 0xFFFF, 0xFFFF, 5, 0, 2, 3, 22, 23)   # Route 201's, Route 202's
    near = [m.start() for m in re.finditer(re.escape(first), d)]
    assert len(routes) == 1 and len(near) == 1, f'routes {routes}, neighbours {near} in {version.WORLD_DUMP}'
    out = []
    for k in range(len(PEARL_PLACES)):
        c, *adj = struct.unpack_from('<6H', d, near[0] + 12 * k)
        out.append((c, list(adj[:c])))
    return out


def _script(name):
    return open(os.path.join(ROOT, 'external', 'pokeplatinum', 'res', 'field', 'scripts', f'scripts_{name}.s')).read()


def test():
    problems = []
    ids = gen4_ids()
    rel = release_rows()
    print(f'{version.NAME}: release rows {[(hex(f), hex(w), n) for f, w, n in rel]}')
    world = json.load(open(version.data_path('sinnoh_world.json')))
    zones = [world['zones'][str(p)] for p in PEARL_PLACES]
    for z, want in zip(zones, ROUTE_NAMES):
        if z['name'] != want:
            problems.append(f'place {want}: {z["name"]} in sinnoh_world.json')
    if _c_neighbours() != [(c, v) for c, v in _c_neighbours()]:
        problems.append('sNeighbours: unreadable')
    if version.PLATINUM:
        near = _dump_tables()
        if near != _c_neighbours():
            problems.append('Platinum\'s sNearbyRoutes (the dump) differs from resident/roamers.c sNeighbours')
        reg = json.load(open(version.data_path('pearl_story_ids.json')))
        old = next((v['name'] for v in reg['flags'].values() if v['b2'] == 559), None)
        print(f'  Pearl\'s Mesprit flag 559 in Platinum: {old}')
        slots = EXT_SLOTS[version.VERSION]
        ext = ext_blob()
        n, *rest = struct.unpack('<H5H5B6Bx5H5H', ext)
        species, levels, game = rest[0:5], rest[5:10], rest[10:16]
        flags, works = rest[16:21], rest[21:26]
        if n != len(slots) or list(species[:n]) != [s[0] for s in slots] or list(levels[:n]) != [s[1] for s in slots]:
            problems.append(f'ext: read back {n} {species} {levels}')
        # the decomp's RoamingPokemon_ActivateSlot: each slot's species and level
        src = open(os.path.join(ROOT, 'external', 'pokeplatinum', 'src', 'roaming_pokemon.c')).read()
        cases = dict((m.group(1), (m.group(2), int(m.group(3))))
                     for m in re.finditer(r'case ROAMING_SLOT_(\w+):\s*species = SPECIES_(\w+);\s*level = (\d+);', src))
        order = [l.strip()[len('ROAMING_SLOT_'):] for l in open(os.path.join(
            ROOT, 'external', 'pokeplatinum', 'generated', 'roaming_slots.txt')) if l.strip() != 'ROAMING_SLOT_MAX']
        dex = {'MESPRIT': 481, 'CRESSELIA': 488, 'DARKRAI': 491, 'MOLTRES': 146, 'ZAPDOS': 145, 'ARTICUNO': 144}
        for k, (sp, lv, gs, fl, st) in enumerate(slots):
            name = order[gs]
            if cases.get(name) is None or dex[cases[name][0]] != sp or cases[name][1] != lv:
                problems.append(f'slot {k}: species {sp} Lv {lv} as game slot {gs} ({name}), the decomp {cases.get(name)}')
            if game[gs] != k:
                problems.append(f'game slot {gs}: {game[gs]}, not {k}')
            if works[k] != ids[st]:
                problems.append(f'slot {k}: state work {works[k]:#x}, {st} is {ids[st]:#x}')
            print(f'  slot {k}: {name.title()} Lv {lv}, the scripts\' slot {gs}, released by '
                  f'{fl or "its ActivateRoamingPokemon only"} ({flags[k]}), state {st} = {works[k]:#x}')
        if game[2] != NONE:
            problems.append('Darkrai\'s game slot 2 has a slot')
        # each release flag: set by its scene right after the scene's ActivateRoamingPokemon, never by the new game
        newgame = _script('init_new_game')
        for fl, scene, slot_names in (('FLAG_MET_CRESSELIA', 'fullmoon_island_forest', ('CRESSELIA',)),
                                      ('FLAG_ACTIVATED_ROAMING_LEGENDARY_BIRDS', 'eterna_city_south_house',
                                       ('MOLTRES', 'ZAPDOS', 'ARTICUNO'))):
            t = _script(scene)
            set_at = t.find(f'SetFlag {fl}')
            acts = [t.find(f'ActivateRoamingPokemon ROAMING_SLOT_{s}') for s in slot_names]
            if set_at < 0 or min(acts) < 0 or max(acts) > set_at:
                problems.append(f'{fl}: not set right after {scene}\'s ActivateRoamingPokemon')
            if f'SetFlag {fl}' in newgame:
                problems.append(f'{fl}: the new game sets it')
        if 'SetFlag FLAG_HIDE_VERITY_CAVERN_MESPRIT' not in newgame:
            problems.append('Platinum\'s new game no longer sets FLAG_HIDE_VERITY_CAVERN_MESPRIT: Mesprit could have a flag')
        hof = _script('pokemon_league_hall_of_fame')
        for st in ('VAR_ROAMING_MESPRIT_STATE', 'VAR_ROAMING_CRESSELIA_STATE', 'VAR_ROAMING_MOLTRES_STATE',
                   'VAR_ROAMING_ZAPDOS_STATE', 'VAR_ROAMING_ARTICUNO_STATE'):
            if f'CallIfEq {st}, ROAMER_STATE_DEFEATED' not in hof:
                problems.append(f'the Hall of Fame does not read {st}')
    print(f'{len(problems)} problems')
    for p in problems:
        print('  ' + p)
    return not problems


if __name__ == '__main__':
    if sys.argv[1:] == ['test']:
        sys.exit(0 if test() else 1)
