"""Can the National Pokédex be completed? Offline, per version (notes/POSTGAME_DEX.md; no ROM, no emulator).

    PEARL_VERSION=v python3 b2tools/postgame_dex_check.py [--today] [--list] [--json OUT]

Every source a build has, each read the way its patch or generator makes it, then every evolution and Day Care egg, until
nothing changes; species 1-493 with no source are printed by group. Exit 1 when one is missing: of the game's goal (482:
Pearl's and Platinum's count without the 11 mythicals, pearl_story.inc pl_DexNationalCaughtNoMythical), or of all 493.
--today leaves out what the post-game work adds (postdex, 2026-11-09), for the numbers before it (Pearl 48, Diamond 47,
Platinum 11 species missing).

Sources (each the build's):
- wild tables: every installed zone of the version's sinnoh_world.json through its zones.json and encounter files, as
  patches/sinnoh_encounters.py writes them: grass by morning, day and night (src/code/time_encounters.c picks the table),
  surf, the three rods. Swarm, Poké Radar and GBA-slot fields are not in the tables.
- the post-game slots (data/postgame_dex.json through patches/wild.py postgame_blob: the other version's slots, the Radar's
  four), and wild.py's honey trees, the 28 swarms, the Great Marsh's daily lists, Feebas; the Trophy Garden's 16
  (pearl_story.inc); the roamers (patches/roamers.py: Platinum's birds too).
- the world scripts (work/<world>/scripts): LegendaryBattle, WildBattle, GiveMon, GiveEgg; the starters; Spear Pillar's
  version legendary and the other one (version.POSTGAME_LEGEND); Platinum's Shaymin (StartFatefulEncounter) and the
  deliveryman's Regigigas; the deliveryman's Manaphy Egg and event Pokémon (data/event_gifts.json).
- the Grand Underground as ug_data.encounter_lists makes the C table (the other column at stage 6), its grottos' starters;
  the fossils: the grottos' (ug_data.grotto_items) and the daily balls (data "fossil_items" and the other version's,
  underground_scripts.other_fossil_defines); the Mining Museum revives all seven (fossil_data).
- Pal Park: b2tools/ramanas.py rooms(version.RAMANAS_ROOMS) (Giratina's Distortion Room can't be caught).
- in-game trades: npc_trade_data.trades().
- evolution: Black 2's table (pokebw2 a/0/1/9, data/trade_evos.json's methods, zone_effects' places); an item method only
  with the item from a source (balls, hidden items, Marts, script gifts, the Underground's balls and grottos, Black 2's
  Pickup, wild held items of a species from a wild source: Black 2's personal data, the six of sinnoh_encounters
  HELD_SPECIES from the dump).
- breeding: Black 2's Day Care (Solaceon); Ditto from a source; the baby by its chain; the nine incense babies with their
  incense from a source (else the next stage); Nidoran and Volbeat / Illumise both ways; Phione from Manaphy with Ditto.
"""
import collections, glob, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402

V = version.VERSION
TODAY = '--today' in sys.argv
NAT = range(1, 494)
MYTHICALS = (151, 249, 250, 251, 385, 386, 489, 490, 491, 492, 493)   # pearl_story.inc pl_DexNationalCaughtNoMythical
B2F = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'b2_us', 'files')
GEN = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'include', 'generated', 'constants')
WORLD = 'platinum' if version.PLATINUM else 'pearl'
WILD_METHODS = ('grass', 'morning', 'day', 'night', 'surf', 'old', 'good', 'super')
TROPHY_GARDEN = (133, 438, 440, 52, 173, 35, 174, 311, 39, 132 if version.PLATINUM else 137, 351, 312, 439, 183, 113, 298)
STARTERS = (387, 390, 393)
FOSSIL_SPECIES = {'ROOT_FOSSIL': 345, 'CLAW_FOSSIL': 347, 'HELIX_FOSSIL': 138, 'DOME_FOSSIL': 140, 'OLD_AMBER': 142,
                  'ARMOR_FOSSIL': 410, 'SKULL_FOSSIL': 408}
INCENSE = {298: (183, 'SEA_INCENSE'), 360: (202, 'LAX_INCENSE'), 406: (315, 'ROSE_INCENSE'), 433: (358, 'PURE_INCENSE'),
           438: (185, 'ROCK_INCENSE'), 439: (122, 'ODD_INCENSE'), 440: (113, 'LUCK_INCENSE'), 446: (143, 'FULL_INCENSE'),
           458: (226, 'WAVE_INCENSE')}
ITEM_METHODS = {6, 8, 17, 18, 19, 20}   # EVO_METHOD_TRADE_WITH_ITEM, ITEM, ITEM_MALE, ITEM_FEMALE, HELD_ITEM_DAY / NIGHT
UNDISCOVERED = 15
DITTO, MANAPHY, PHIONE = 132, 490, 489


def consts(name, prefix):
    out = {}
    for line in open(os.path.join(GEN, name)):
        m = re.match(rf'#define ({prefix}\w+) (\d+)\b', line)
        if m:
            out.setdefault(m.group(1), int(m.group(2)))
    return out


SPECIES = consts('species.h', 'SPECIES_')
ITEMS = consts('items.h', 'ITEM_')
NAME = {}
for k, v in sorted(SPECIES.items(), key=lambda kv: kv[1]):
    NAME.setdefault(v, k[8:].replace('_', ' ').title())


def sid(x):
    return x if isinstance(x, int) else SPECIES.get(x, 0)


class Sources:
    def __init__(self):
        self.species = collections.defaultdict(set)
        self.items = collections.defaultdict(set)

    def add(self, s, where):
        s = sid(s)
        if 1 <= s <= 493:
            self.species[s].add(where)

    def item(self, it, where):
        if it:
            self.items[it].add(where)


# ---------------------------------------------------------------------------------------------- the wild tables
def wild_tables(src, raw):
    """The build's tables (and, in raw, every field of the files: Radar, swarm, GBA)."""
    import sinnoh_encounters as se
    world = json.load(open(version.data_path('sinnoh_world.json')))
    zj = json.load(open(os.path.join(version.WORK, 'zones.json')))
    zones = {int(k): z['name'] for k, z in world['zones'].items()}
    zones.update({int(k): z['name'] for k, z in world['rooms']['zones'].items()})
    for zid, zname in zones.items():
        n = zj[zid]['encounters']
        if n is None:
            continue
        e = se.pearl_file(n)
        if e['land_rate']:
            for per in ('morning', 'day', 'night'):
                for s in se.grass_slots(e, per):
                    src.add(s[0], (zname, per))
            for g in ('swarms', 'radar', 'ruby', 'sapphire', 'emerald', 'firered', 'leafgreen'):
                for s in e[g]:
                    raw[sid(s)].add((zname, g))
        for key, rate, m in (('surf_encounters', 'surf_rate', 'surf'), ('old_rod_encounters', 'old_rod_rate', 'old'),
                             ('good_rod_encounters', 'good_rod_rate', 'good'),
                             ('super_rod_encounters', 'super_rod_rate', 'super')):
            if e[rate]:
                for s in e[key]:
                    src.add(s['species'], (zname, m))


def postgame_slots(src):
    if TODAY:
        return
    d = json.load(open(os.path.join(ROOT, 'data', 'postgame_dex.json')))[V]
    rows = (d['exclusives'] if version.POSTGAME_OTHER else []) + d['radar']
    for zone, group, slot, own, other, form in rows:
        src.add(other, (zone, f'post-game {group} slot {slot} (for {own[8:].title()})'))


def wild_extras(src):
    import wild
    ex = wild.encdata_ex()
    u32s = lambda b: struct.unpack('<%dI' % (len(b) // 4), b)
    for g, m in enumerate(wild.HONEY_MEMBERS):
        for s in u32s(ex[m]):
            src.add(s, ('honey tree', 'ABC'[g]))
    src.add(u32s(ex[wild.FEEBAS_SPECIES])[0], ('Mt. Coronet B1F', 'Feebas'))
    for m in (wild.MARSH_NATIONAL, wild.MARSH_LOCAL):
        for s in u32s(ex[m]):
            src.add(s, ('Great Marsh', 'daily'))
    zj = {z['id']: z for z in json.load(open(os.path.join(version.WORK, 'zones.json')))}
    for m in wild.SWARM_MAPS:
        e = json.load(open(os.path.join(version.WORK, 'encounters', f'{zj[m]["encounters"]:03d}.json')))
        for s in e['swarms']:
            src.add(s, (zj[m]['name'], 'swarm'))
    for s in TROPHY_GARDEN:
        src.add(s, ('Trophy Garden', 'daily'))
    import roamers
    for s in (roamers.SPECIES_MESPRIT, roamers.SPECIES_CRESSELIA):
        src.add(s, ('roamer', ''))
    if version.PLATINUM:
        for s in (roamers.SPECIES_MOLTRES, roamers.SPECIES_ZAPDOS, roamers.SPECIES_ARTICUNO):
            src.add(s, ('roamer (Oak)', ''))


# ---------------------------------------------------------------------------------------------- scripts, gifts
def scripts(src):
    for p in sorted(glob.glob(os.path.join(ROOT, 'work', WORLD, 'scripts', '*.txt'))):
        head = open(p).readline()
        zone = head.split(':')[1].split('(')[0].strip() if ':' in head else os.path.basename(p)
        text = open(p).read()
        for m in re.finditer(r'^\s+(LegendaryBattle|WildBattle|GiveMon|GiveEgg)\s+(0x[0-9A-F]+|\d+),', text, re.M):
            src.add(int(m.group(2), 0), (zone, m.group(1)))
        for m in re.finditer(r'SetVar VAR_0x800[0-9], (0x[0-9A-F]+|\d+)', text):    # item gifts (GiveItem VAR_0x8004)
            src.item(_b2_item(int(m.group(1), 0)), (zone, 'script'))
        for m in re.finditer(r'GiveItem (0x[0-9A-F]+|\d+),', text):
            src.item(_b2_item(int(m.group(1), 0)), (zone, 'script'))
    for s in STARTERS:
        src.add(s, ('starter', 'one of three'))
    if not version.PLATINUM:                        # (Spear Pillar's script picks it by the version: 484 / 483)
        src.add(484 if V == 'pearl' else 483, ('Spear Pillar', 'the version\'s legendary'))
    if not TODAY and version.POSTGAME_LEGEND:
        src.add(version.POSTGAME_LEGEND[0], ('Spear Pillar', 'the other version\'s legendary (post-game)'))
        src.item(ITEMS['ITEM_' + version.POSTGAME_LEGEND[2]], ('Spear Pillar', 'the other Orb'))
    if version.PLATINUM:
        src.add(492, ('Flower Paradise', 'StartFatefulEncounter'))
        src.add(486, ('deliveryman', 'event Regigigas'))
    src.add(490, ('deliveryman', 'the Manaphy Egg'))
    if not TODAY:
        import event_gifts
        for g in event_gifts.gifts()[0]:
            src.add(g['species'], ('deliveryman', g['event']))


_B2_ITEM = None


def _b2_item(n):
    global _B2_ITEM
    import pearl_items
    return pearl_items.b2_item(n)


def items(src):
    import pearl_items
    ball = os.path.join(ROOT, 'work', WORLD, 'scripts', f'{pearl_items.BALL_FILE:04d}.txt')
    if os.path.exists(ball):
        for m in re.finditer(r'SetVar VAR_0x8008, (0x[0-9A-F]+|\d+)', open(ball).read()):
            src.item(_b2_item(int(m.group(1), 0)), ('item ball', ''))
    for h in pearl_items.hidden_items().values():
        src.item(_b2_item(h['item']), ('hidden item', ''))
    for l in pearl_items.mart_lists():
        for i in l:
            src.item(_b2_item(i), ('Mart', ''))
    for l in pearl_items.mart_special():
        for i in l:
            src.item(_b2_item(i), ('Mart', ''))
    # Black 2's Pickup (pokebw2 src/ov166/event_battle_return.c sPickupItems, sPickupRareItems)
    pick = open(os.path.join(ROOT, 'external', 'pokebw2', 'src', 'ov166', 'event_battle_return.c')).read()
    for block in re.findall(r'sPickup(?:Rare)?Items\[\d+\] = \{(.*?)\};', pick, re.S):
        for n in re.findall(r'(ITEM_\w+)', block):
            src.item(ITEMS[n], ('Pickup', ''))


# ---------------------------------------------------------------------------------------------- the Underground, Pal Park
def underground(src):
    import ug_data
    col = ug_data.bdsp()
    if TODAY:
        import ug_data as u
        recs, entries, rares = _lists_today(u, col)
    else:
        recs, entries, rares = ug_data.encounter_lists(col)
    for s, stage_where, w in entries:
        src.add(s, ('Hideaway', f'stage {stage_where & 15}'))
    for s, w in rares:
        src.add(s, ('Hideaway', 'rare'))
    d = ug_data.data()
    for h in d['hideaways']:
        for s in h['grotto']['starters']:
            src.add('SPECIES_' + s, (h['key'], 'Hidden Grotto'))
        for it in h['items']:
            if not it[0].startswith('move:') and 'ITEM_' + it[0] in ITEMS:
                src.item(ITEMS['ITEM_' + it[0]], ('Hideaway ball', ''))
    gi = ug_data.grotto_items(d)
    for row in gi['a'] + gi['b']:
        for it in row:
            if it in FOSSIL_SPECIES:
                src.add(FOSSIL_SPECIES[it], ('Mining Museum', f'{it} (grottos)'))
            if 'ITEM_' + it in ITEMS:
                src.item(ITEMS['ITEM_' + it], ('grotto', ''))
    for it in d['fossil_items']:
        src.add(FOSSIL_SPECIES[it], ('Mining Museum', f'{it} (daily balls)'))
    other = version.POSTGAME_OTHER
    if other and not TODAY:
        fossil = gi['version_fossil'][ug_data.COLUMN_OF[other]]
        src.add(FOSSIL_SPECIES[fossil], ('Mining Museum', f'{fossil} (daily balls, post-game)'))


def _lists_today(u, col):
    """ug_data.encounter_lists without the other column (the lists before postdex)."""
    import importlib
    saved = u.postgame_column
    u.postgame_column = lambda: None
    try:
        return u.encounter_lists(col)
    finally:
        u.postgame_column = saved


def pal_park(src):
    import ramanas
    ver = ramanas.version()
    if TODAY:
        ver = {'sp+bd': 'sp', 'bd+sp': 'bd'}.get(ver, ver)
    for r in ramanas.rooms(ver):
        for m in r['mons']:
            if not m['no_capture']:
                src.add(m['species'], ('Pal Park', r['name']))


def trades(src):
    import npc_trade_data
    for t in npc_trade_data.trades():
        src.add(t['species'], ('in-game trade', t['nickname']))


# ---------------------------------------------------------------------------------------------- evolution and breeding
def closure(src):
    import narcio
    evo = narcio.load(B2F, 19)
    per = narcio.load(B2F, 16)
    import sinnoh_encounters as se
    from gen4rom import Rom, narc_members
    held = {}
    for sp in NAT:
        held[sp] = [i for i in struct.unpack_from('<3H', per[sp], 0x0C) if i]
    dump = narc_members(Rom(version.SOURCE_DUMP).read(version.PERSONAL_NARC))
    for sp in se.HELD_SPECIES:                     # (the six whose held items come from the dump)
        held[sp] = [i for i in struct.unpack_from('<2H', dump[sp], 12) if i]
    evos = collections.defaultdict(list)
    pre = {}
    for sp in NAT:
        w = struct.unpack('<21H', evo[sp][:42])
        for i in range(7):
            m, p, t = w[3 * i:3 * i + 3]
            if m and t and t <= 493:
                evos[sp].append((m, p, t))
                pre.setdefault(t, sp)

    def base(sp):
        while sp in pre:
            sp = pre[sp]
        return sp
    have = dict.fromkeys(src.species, 'source')
    wild = set(have)                                # (a species met in the wild holds its items)
    changed = True
    while changed:
        changed = False
        avail_items = set(src.items)
        for sp in wild:
            avail_items.update(held.get(sp, []))
        for sp in list(have):
            for m, p, t in evos.get(sp, []):
                if t in have or (m in ITEM_METHODS and p not in avail_items):
                    continue
                have[t] = f'evolves from {NAME[sp]}'
                changed = True
        ditto = DITTO in have
        for sp in list(have):
            if sp in (PHIONE, MANAPHY):
                if ditto and PHIONE not in have:
                    have[PHIONE] = 'bred from Manaphy and Ditto'
                    changed = True
                continue
            g, eggs = per[sp][0x12], (per[sp][0x16], per[sp][0x17])
            if UNDISCOVERED in eggs or sp == DITTO or ((g in (0, 255) or 13 in eggs) and not ditto):
                continue
            b = base(sp)
            kids = {b}
            if b in INCENSE:
                nxt, inc = INCENSE[b]
                kids = {nxt} | ({b} if ITEMS['ITEM_' + inc] in avail_items else set())
            if b in (29, 32):
                kids |= {29, 32}
            if b in (313, 314):
                kids |= {313, 314}
            for k in kids:
                if k not in have:
                    have[k] = f'bred from {NAME[sp]}'
                    changed = True
    return have


# ---------------------------------------------------------------------------------------------- main
def run():
    src = Sources()
    raw = collections.defaultdict(set)
    wild_tables(src, raw)
    postgame_slots(src)
    wild_extras(src)
    scripts(src)
    items(src)
    underground(src)
    pal_park(src)
    trades(src)
    have = closure(src)
    missing = [s for s in NAT if s not in have]
    return src, raw, have, missing


def group(s, raw):
    tags = sorted({g for _, g in raw.get(s, ())} & {'radar', 'ruby', 'sapphire', 'emerald', 'firered', 'leafgreen', 'swarms'})
    if s in (151, 251, 385, 386):
        return 'events only'
    if 'radar' in tags:
        return 'Poké Radar'
    if any(t in tags for t in ('ruby', 'sapphire', 'emerald', 'firered', 'leafgreen')):
        return 'GBA slot'
    return 'other (the other version, a breed or evolution of one of these)'


def main():
    src, raw, have, missing = run()
    goal = [s for s in missing if s not in MYTHICALS]
    print(f'postgame_dex_check ({V}{", --today" if TODAY else ""}): {493 - len(missing)} of 493 species obtainable, '
          f'{482 - len(goal)} of the game\'s 482')
    by = collections.defaultdict(list)
    for s in missing:
        by[group(s, raw)].append(s)
    for g, ss in sorted(by.items()):
        print(f'  missing, {g}: {len(ss)}: ' + ', '.join(f'{NAME[s]} ({s})' for s in ss))
    if '--list' in sys.argv:
        for s in NAT:
            print(f'{s:3d} {NAME[s]:12s} {have.get(s, "MISSING")}: {sorted(src.species.get(s, ()))[:3]}')
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        json.dump({'version': V, 'today': TODAY, 'missing': missing,
                   'how': {str(k): v for k, v in have.items()},
                   'sources': {str(k): sorted(map(list, v)) for k, v in src.species.items()}}, open(out, 'w'), indent=1)
    if goal or (missing and not TODAY):
        print('  FAIL' if not TODAY else '  (today: the numbers before the post-game work)')
        return 1 if not TODAY else 0
    print('  ok: every species can be caught or made')
    return 0


if __name__ == '__main__':
    sys.exit(main())
