"""Platinum's Pokédex, checked offline (step 6, the Pokédex piece; 2026-11-07, plat-dex). No ROM, no emulator.

    PEARL_VERSION=platinum python3 b2tools/platinum_dex_check.py [--areas FILE]
    PEARL_VERSION=v python3 b2tools/platinum_dex_check.py --text       the text only, for any version (1.0.1: Pearl's and
                                                                         Diamond's entries against their own dumps)

What it checks, each the way the build makes it (the patches' own functions on scratch copies; nothing of the tree or
of a build is written):
- the list: patches/sinnoh_dex.py's two archive files (a/0/1/6 file 709, a/0/9/7 file 4) on copies of Black 2's: the
  210 Sinnoh numbers in Platinum's order (pokeplatinum res/pokemon/sinnoh_pokedex.json), Victini the hidden #000, every
  other species 999 (no Unova number left); the sort file ends Victini + the 210. Its apply_code on a copy of arm9.bin:
  the "regional Pokédex complete" literals 210 and the exclusions (Keldeo, Meloetta, Genesect, Victini: none Sinnoh's),
  so PokeDexIsComplete 2 = all 210 seen (Platinum's LOCAL_DEX_GOAL, no exclusions).
- the text: the system text as patches/sinnoh_names.py packs it (data/text_overrides with platinum/ over it, packed by
  pokebw2's own packer on a scratch clone, read back): for species 1-493 the entry, every alternate form's entry, the
  category, height and weight equal Platinum's dump (slots 616, 621, 620, 619; Giratina's Altered Forme from 715 and
  714, its Origin Forme = Black 2's form 1 from 620 and 619); every entry fits Black 2's entry window (3 rows of at
  most 222 px in font 0: ov296 zukan_info.c's 28-tile window from x = 2) and passes text_check's codes and characters.
- the areas: the AREA page's places as patches/sinnoh_pokedex.py's habitat makes them, from the wild tables
  patches/sinnoh_encounters.py converts (every installed zone of data/platinum/sinnoh_world.json), town_map's zone
  table and Platinum's special lists (AREA_SPECIAL): every zone with a wild table has a place; every regional species
  in a wild table has places; our morning/day/night places equal Platinum's zukan_enc lists (categories 0-2, 5-7);
  the Battle Zone's places are there; the HABITAT list fits (57 places, 30 a page). --areas FILE writes each species'
  places, tab separated.
- the National Pokédex: Rowan's lab script (the generated work/platinum/src/field_scripts/1682_pearl_sandgem_rowans_lab.s)
  gives it through pl_SetNationalDex after pl_CheckLocalDexCompletedOrChampion (the game clear, or all 210 seen).

Exit status 1 when a check fails.
"""
import json, os, re, shutil, struct, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402

PLAT = os.path.join(ROOT, 'external', 'pokeplatinum')
PB2 = os.path.join(ROOT, 'external', 'pokebw2')
B2_FILES = os.path.join(PB2, 'build', 'b2_us', 'files')
B2_CODE = os.path.join(PB2, 'build', 'b2_us', 'build')
# The Battle Zone's places with wild Pokémon (the Fight Area and the Survival Area have none, in Platinum too)
BATTLE_ZONE = ('RESORT_AREA', 'STARK_MOUNTAIN_EXTERIOR', 'STARK_MOUNTAIN_INTERIOR_1',
               'ROUTE_225', 'ROUTE_226', 'ROUTE_227', 'ROUTE_228', 'ROUTE_229', 'ROUTE_230')
# Places where our wild tables and Platinum's area lists differ, known and kept: the Ruin Maniac Cave's last stage
# (Platinum's Maniac Tunnel, map section 67) has no area of its own on the map, and town_map's zone table reaches
# Route 214 through its warps (Pearl's build the same); Platinum shows the Ruin Maniac Cave
KNOWN = {(449, 'ROUTE_214')}


# ------------------------------------------------------------------------------------------------- the list

def species_numbers():
    out = {}
    for line in open(os.path.join(PB2, 'build', 'include', 'generated', 'constants', 'species.h')):
        m = re.match(r'#define (SPECIES_\w+)\s+(\d+)\s*$', line)
        if m: out.setdefault(m.group(1), int(m.group(2)))
    return out


def check_list(bad):
    import narcio, sinnoh_dex as sd
    from b2files import arc_path
    order = sd.sinnoh_order()
    names = json.load(open(os.path.join(PLAT, 'res', 'pokemon', 'sinnoh_pokedex.json')))
    num = species_numbers()
    want = [num[n] for n in names[1:]]
    if order != want:
        bad.append(f'list: the dump\'s order differs from pokeplatinum\'s at {[i + 1 for i, (a, b) in enumerate(zip(order, want)) if a != b][:5]}')
    if len(order) != 210 or len(set(order)) != 210:
        bad.append(f'list: {len(order)} entries, {len(set(order))} different')
    with tempfile.TemporaryDirectory(dir=os.path.join(ROOT, 'work')) as t:
        for a in (sd.ARC_PERSONAL, sd.ARC_SORT):
            rel = os.path.relpath(arc_path(B2_FILES, a), B2_FILES)
            os.makedirs(os.path.dirname(os.path.join(t, rel)), exist_ok=True)
            shutil.copyfile(arc_path(B2_FILES, a), os.path.join(t, rel))
        sd.apply(t)
        table = narcio.load(t, sd.ARC_PERSONAL)[sd.FILE_REGIONAL]
        table = struct.unpack(f'<{len(table) // 2}H', table)
        sort = narcio.load(t, sd.ARC_SORT)[sd.FILE_REGIONAL_ORDER]
        sort = struct.unpack(f'<{len(sort) // 2}H', sort)
        shutil.copyfile(os.path.join(B2_CODE, 'arm9.bin'), os.path.join(t, 'arm9.bin'))
        sd.apply_code(t)
        arm9 = open(os.path.join(t, 'arm9.bin'), 'rb').read()
    for n, s in enumerate(order, 1):
        if table[s] != n:
            bad.append(f'list: species {s} has number {table[s]}, not {n}')
    if table[sd.VICTINI] != 0:
        bad.append(f'list: Victini has {table[sd.VICTINI]}, not the hidden 0')
    left = [s for s in range(1, len(table)) if s not in set(order) | {sd.VICTINI} and table[s] != sd.NONE]
    if left:
        bad.append(f'list: {len(left)} species outside Sinnoh keep a number: {left[:8]}')
    if list(sort[-211:]) != [sd.VICTINI] + order:
        bad.append('list: the sort file does not end Victini + the 210')
    lits = [struct.unpack_from('<I', arm9, a - sd.ARM9)[0] for a in sd.COMPLETE_LITERALS]
    ex = list(struct.unpack_from('<4H', arm9, sd.EXCLUSIONS - sd.ARM9))
    if lits != [210, 210]:
        bad.append(f'complete: the literals are {lits}, not 210')
    if ex != [647, 648, 649, 494] or set(ex) & set(order):
        bad.append(f'complete: exclusions {ex}')
    counted = sum(1 for s in range(1, 650) if table[s] != sd.NONE)
    return (f'list: 210 in Platinum\'s order (#1 {order[0]}, #210 {order[-1]}), Victini #000, {len(table) - counted - 1} '
            f'other species 999; complete = {lits[0]} seen, exclusions {ex}; the regional counts count {counted} species '
            f'(the 210 and Victini, which the completion leaves out)')


# ------------------------------------------------------------------------------------------------- the text

def check_text(bad):
    import gen4_text, pokebw2_mod, sinnoh_names, sinnoh_pokedex as spx, text_check
    entries, cats, heights, weights = (gen4_text.bank(n) for n in (spx.ENTRY_BANK, spx.CATEGORY_BANK, spx.HEIGHT_BANK,
                                                                   spx.WEIGHT_BANK))
    gh, gw = (gen4_text.bank(spx.GIRA_HEIGHT_BANK), gen4_text.bank(spx.GIRA_WEIGHT_BANK)) if version.PLATINUM else (None, None)
    tree, _, _, _ = sinnoh_names.system_text_tree('plat_dex_check')
    try:
        packed = pokebw2_mod.pack_text(tree, 'system')['a/0/0/2']
        sys.path.insert(0, PB2)
        from tools.data.narc import read_narc
        from tools.text import text_data
        files, num = read_narc(packed), text_check.text_bank_numbers(tree)

        def bank(name):
            return [l for l in text_data.unpack_file(files[num['TEXT_BANK_' + name]]).split('\n')[:-1]
                    if not l.startswith('\\pad{')]
        pe, pc, ph, pw = bank('POKEDEX_ENTRIES'), bank('SPECIES_CATEGORIES'), bank('POKEDEX_HEIGHTS'), bank('POKEDEX_WEIGHTS')
        dirs = spx.species_dirs()
        n_forms = rows3 = 0
        widest = (0, 0)
        font = text_check.font()
        for n in range(1, 494):
            dex = json.load(open(os.path.join(tree, 'res', 'pokemon', dirs[n], 'data.json'), encoding='utf-8'))['pokedex']
            want = spx.dex_line(entries[n])
            if dex['entry'] != want:
                bad.append(f'entry {n}: {dex["entry"][:40]!r} is not {version.NAME}\'s {want[:40]!r}')
            if pe[n] != want.replace('\n', '\\n'):
                bad.append(f'entry {n}: the packed line {pe[n][:40]!r} is not the data\'s')
            for i, f in enumerate(dex.get('forms', [])):
                n_forms += 1
                if f['entry'] != want:
                    bad.append(f'entry {n} form {i + 1}: {f["entry"][:40]!r} is not {version.NAME}\'s')
            line = want.replace('\n', '\\n')
            for kind, msg in text_check.line_problems(line, limit=spx.ENTRY_FIT, rows=spx.ENTRY_ROWS):
                bad.append(f'entry {n}: {kind}: {msg}')
            rows = want.split('\n')
            rows3 += len(rows) == 3
            widest = max(widest, (max(font.width(r) for r in rows), n))
            pairs = [('category', pc[n], cats[n]), ('category', dex['category'], cats[n])]
            if n == spx.GIRATINA and version.PLATINUM:
                pairs += [('Altered height', dex['height'], gh[n]), ('Altered weight', dex['weight'], gw[n]),
                          ('Origin height', dex['forms'][0]['height'], heights[n]),
                          ('Origin weight', dex['forms'][0]['weight'], weights[n])]
            else:
                pairs += [('height', ph[n], heights[n]), ('weight', pw[n], weights[n])]
            for what, got, plat in pairs:
                if spx.norm_dex(got) != spx.norm_dex(plat):
                    bad.append(f'{what} {n}: {got!r}, {version.NAME} {plat!r}')
            for what, got in (('category', pc[n]), ('height', ph[n]), ('weight', pw[n])):
                for kind, msg in text_check.line_problems(got, limit=120 if what == 'category' else 104, rows=1):
                    bad.append(f'{what} {n}: {kind}: {msg}')
    finally:
        shutil.move(tree, os.path.expanduser(f'~/.Trash/pokebw2_mod_plat_dex_check_{time.strftime("%H%M%S")}'))
    return (f'text: 493 entries, {n_forms} form entries, categories, heights and weights as {version.NAME}\'s dump; '
            f'{rows3} entries take 3 rows; widest row {widest[0]} px (species {widest[1]}) of {spx.ENTRY_FIT}')


# ------------------------------------------------------------------------------------------------- the areas

def area_data():
    """What sinnoh_pokedex.habitat makes, from sources: (locs, zones, ztab, zb, hab, slot_of, installed rooms)."""
    import town_map as tm, sinnoh_encounters as enc, sinnoh_pokedex as spx
    world = json.load(open(version.data_path('sinnoh_world.json')))
    pz = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    zones = [(int(k), v['b2_zone']) for k, v in world['zones'].items()]
    rooms = world['rooms']
    for k, v in rooms['zones'].items():                  # (sinnoh_encounters.sinnoh_zones: a room once sinnoh_rooms installs it)
        if rooms['matrices'].get(str(v.get('pearl_matrix')), {}).get('b2_matrix') is not None:
            zones.append((int(k), v['b2_zone']))
    locs = tm.locations(); locs = locs + [tm.dummy_record(locs)] * (spx.NREC - len(locs))
    ztab, _ = tm.zone_table([None] * (max(b for _, b in zones) + 1), locs)
    zb, wild = {}, {}
    for pid, b2 in zones:
        n = pz[pid]['encounters']
        if n is None: continue
        data = b''.join(enc.convert(enc.pearl_file(n), p, k == enc.ROD_TABLE)[0] for k, p in enumerate(enc.TIME_TABLES))
        wild[b2] = (pid, spx.table_bits(data))
        if ztab[b2] != 0xFF:
            zb[b2] = wild[b2][1]
    rzones = [l['zone'] for l in locs]
    specials = spx.special_bits(tm, locs) if spx.AREA_SPECIAL else None
    hab, slot_of = spx.place_bits(zb, ztab, rzones, specials)
    return locs, pz, ztab, wild, zb, hab, slot_of, specials


def built_habitat(locs, ztab, zb):
    """sinnoh_pokedex.habitat itself, on scratch copies of a/1/7/6, a/1/5/7 and a/2/9/6, with town_map's file 21 and
    the zones' wild tables given from sources (what town_map and sinnoh_encounters would have built): ({species: [bits
    per habitat index]} read back from a/1/7/6, the HABITAT list's pages read back from a/2/9/6, its message)."""
    import narcio, town_map as tm, sinnoh_pokedex as spx
    from b2files import arc_path
    blob, lay, _, zt, _ = tm.data_file([None] * len(ztab))
    assert zt == ztab
    recs = [struct.unpack_from('<27H', blob, tm.REC * k) for k in range(lay['n'])]
    saved = tm.read_file21, spx._tm, spx.zone_bits, spx._zt_off
    tm.read_file21 = lambda files: dict(records=recs, zone_table=ztab)
    spx._tm, spx.zone_bits, spx._zt_off = (lambda: tm), (lambda files, z: zb), (lambda files, t: lay['zt_off'])
    t = tempfile.mkdtemp(dir=os.path.join(ROOT, 'work'))
    try:
        for a in (spx.ARC_HABITAT, spx.ARC_DEX_GFX, spx.ARC_HLIST):
            rel = os.path.relpath(arc_path(B2_FILES, a), B2_FILES)
            os.makedirs(os.path.dirname(os.path.join(t, rel)), exist_ok=True)
            shutil.copyfile(arc_path(B2_FILES, a), os.path.join(t, rel))
        msg = spx.habitat(t)                       # (its own asserts: sizes, 57 places, 30 a page)
        hab = {}
        for i, d in enumerate(narcio.load(t, spx.ARC_HABITAT)[:649]):
            if d[1] == 0:
                hab[i + 1] = list(d[2:2 + spx.NREC])
        pages = [p for p in narcio.load(t, spx.ARC_HLIST) if struct.unpack_from('<H', p, 8)[0]]
    finally:
        tm.read_file21, spx._tm, spx.zone_bits, spx._zt_off = saved
        shutil.move(t, os.path.expanduser(f'~/.Trash/plat_dex_check_files_{time.strftime("%H%M%S")}'))
    return hab, pages, msg


def check_areas(bad, out_file=None):
    import town_map as tm, sinnoh_dex as sd, sinnoh_pokedex as spx
    locs, pz, ztab, wild, zb, _, slot_of, specials = area_data()
    hab, pages, msg = built_habitat(locs, ztab, zb)
    order = sd.sinnoh_order()
    dirs = spx.species_dirs()
    for b2, (pid, _) in wild.items():
        if ztab[b2] == 0xFF:
            bad.append(f'areas: {pz[pid]["name"]} has a wild table and no place on the map')
    in_tables = set()
    for _, bits in wild.values():
        in_tables |= set(bits)
    places = {s: {i for i, b in enumerate(v) if b} for s, v in hab.items()}
    for s in order:
        if s in in_tables and not places.get(s):
            bad.append(f'areas: Sinnoh #{order.index(s) + 1} {dirs[s]} is in a wild table and has no place')
    # against Platinum's own lists: morning, day, night, and the specials it shows before the National Pokédex
    rec = tm.area_records(locs)
    differ = []
    for s in range(1, 494):
        cats = (0, 1, 2, 5, 6, 7) + (tm.AREA_SPECIAL if spx.AREA_SPECIAL else ())
        theirs = {slot_of[rec[('dungeon' if c < 5 else 'field', p)]] for c in cats for p in tm.area_list(s, c)}
        for i in sorted(theirs ^ places.get(s, set())):
            if (s, locs[i]['key']) not in KNOWN:
                differ.append((s, locs[i]['key'], 'Platinum only' if i in theirs else 'ours only'))
    bad += [f'areas: {dirs[s]} at {k}: {w}' for s, k, w in differ]
    bz = {locs[i]['key'] for s in places for i in places[s]} & set(BATTLE_ZONE)
    if bz != set(BATTLE_ZONE):
        bad.append(f'areas: Battle Zone places without Pokémon: {sorted(set(BATTLE_ZONE) - bz)}')
    if len(pages) > spx.HLIST_PLACES:
        bad.append(f'HABITAT list: {len(pages)} places > {spx.HLIST_PLACES}')
    most = max(struct.unpack_from('<H', p, 8)[0] for p in pages)
    regional_placed = sum(1 for s in order if places.get(s))
    no_area = [s for s in order if not places.get(s)]
    n_special = sum(len(v) for v in (specials or {}).values())
    if out_file:
        with open(out_file, 'w', encoding='utf-8') as f:
            for s in range(1, 494):
                if places.get(s):
                    f.write(f'{s}\t{dirs[s]}\t{order.index(s) + 1 if s in order else ""}\t'
                            f'{", ".join(locs[i]["key"] for i in sorted(places[s]))}\n')
    return (f'areas: {len(wild)} zones with wild tables, all placed; {regional_placed} of the 210 have places (every one '
            f'in a wild table or a special list; {len(no_area)} in neither show "Area Unknown", as in Platinum before the National Pokédex); the '
            f'places equal Platinum\'s lists (morning, day, night, special) but {sorted(KNOWN)}; {n_special} special '
            f'places of {len(specials or {})} species (honey trees, the Great Marsh, Feebas); Battle Zone: {len(bz)} '
            f'places; HABITAT list {len(pages)} places (most {most} a page). The patch said: {msg}')


# ------------------------------------------------------------------------------------------------- the National Pokédex

def check_national(bad):
    p = os.path.join(version.WORK, 'src', 'field_scripts', '1682_pearl_sandgem_rowans_lab.s')
    if not os.path.exists(p):
        bad.append(f'national: {p} is not generated (PEARL_VERSION=platinum python3 b2tools/pearl_story.py all)')
        return 'national: not checked'
    s = open(p, encoding='utf-8').read()
    gate, give = s.count('pl_CheckLocalDexCompletedOrChampion'), s.count('pl_SetNationalDex')
    if not gate or give != 1:
        bad.append(f'national: Rowan\'s lab has {gate} champion gates and {give} pl_SetNationalDex')
    inc = open(os.path.join(ROOT, 'src', 'include', 'pearl_story.inc'), encoding='utf-8').read()
    if not re.search(r'\.macro pl_SetNationalDex\s*(//[^\n]*)?\n\s*PokeDexGiveNational', inc):
        bad.append('national: pl_SetNationalDex is not PokeDexGiveNational')
    return (f'national: Rowan\'s lab gives it (pl_SetNationalDex = PokeDexGiveNational) behind {gate} '
            f'pl_CheckLocalDexCompletedOrChampion gates (the game clear, or PokeDexIsComplete 2)')


def main(argv):
    if '--text' in argv:                # (any version: the packed entries against its own dump; 1.0.1, v101-seams)
        bad = []
        print(check_text(bad), flush=True)
        print('\n'.join(bad[:60]) or f'platinum_dex_check --text ({version.VERSION}): ok')
        return 1 if bad else 0
    if not version.PLATINUM:
        raise SystemExit('run with PEARL_VERSION=platinum (or --text, for any version)')
    out_file = argv[argv.index('--areas') + 1] if '--areas' in argv else None
    bad = []
    for step in (check_list, check_text, lambda b: check_areas(b, out_file), check_national):
        print(step(bad), flush=True)
    print('\n'.join(bad[:60]) + (f'\n... {len(bad) - 60} more' if len(bad) > 60 else '') if bad else
          'platinum_dex_check: ok')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
