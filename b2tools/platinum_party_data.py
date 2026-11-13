"""Platinum's party tables that its party commands read (plat-tutors, 2026-11-07), from the user's Platinum dump: what the
decomp's overlay 376 (src/pearlb2/plat_party/plat_party.c, include/pearlb2/plat_party.h) and the generator's "plat-tutors"
block (pearl_story.py) need.

    PEARL_VERSION=platinum python3 b2tools/platinum_party_data.py         prints the tables' summary
    PEARL_VERSION=platinum python3 b2tools/platinum_party_data.py test    the offline test (below)

- The shard tutors (pokeplatinum src/overlay005/scrcmd_move_tutor.c, include/tutor_movesets.h): sTeachableMoves, 38
  moves of 12 bytes (the move, its red, blue, yellow and green Shards, the tutor: 0 Route 212, 1 the Survival Area, 2
  Snowpoint), and right after it sSpeciesLearnsetsByTutor, 505 masks of 5 bytes (a bit a move; species 1-493, then the 12
  forms of constants/forms.h).
- Dr. Footstep (overlay005/footprint_type.c): sFootprintTypes, species 0-493, (type, has a print) as two u16.
- The ribbons (src/ribbon.c sRibbonDataTable): 80 of 12 bytes (Platinum's MON_DATA field, sprite, palette, name line in
  bank RIBBON_NAMES_BANK, description). b2_param() turns the field into Black 2's PKM_PARAM (decomp
  include/constants/pokemon.h): Platinum's 25-52 (the Sinnoh Champion .. Premier ribbons) are Black 2's numbers, 78-109
  (Hoenn's) one lower, 123-142 (Sinnoh's contest ribbons) PKM_PARAM_RIBBON_G4_COOL on.
Every table is found by its contents and each search must match once (as platinum_gym_data.py does).

blob() is the table the overlay reads (PlatPartyTable, 3,328 B), which patches/platinum_tutors.py writes into its file.

(v101-story, 2026-11-07) Pearl and Diamond (1.0.1, version.PARTY_COMMANDS): the ribbons and Dr. Footstep's footprints come
from the version's own dump the same way (pokediamond: the ribbons in arm9, src/unk_0207FC5C.c UNK_020FB788, the same 12-byte
rows and MON_DATA numbers; the footprints in overlay 5, asm/ov05_021F61DC.s ov05_021FCA00, the same (type, print) pairs; the
names in the same bank 484). They have no shard tutors: their blob has no tutor move and no mask (the overlay then answers
"can't", as before), only the footprints. `python3 b2tools/platinum_party_data.py test` checks Pearl's against pokediamond.

The test (no ROM build): the dump's masks against the decomp's res/pokemon/*/data.json tutor lists for every species
and form, the footprint types against their footprint rows, the ribbon names against src/ribbon.c's order, and a Python
copy of the overlay's rule (tutor_answer) on a few Pokémon by hand: Platinum's own examples.
"""
import functools, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

PLATINUM_SRC = os.path.join(ROOT, 'external', 'pokeplatinum')
MOVES, MASK, MOVESETS, SPECIES, FOOTPRINTS = 38, 5, 505, 493, 494       # include/pearlb2/plat_party.h
TABLE_SIZE = 3328
PRINT = 0x80
LOCATIONS = ('Route 212', 'the Survival Area', 'Snowpoint')            # generated/tutor_locations.txt
ROUTE_212, SURVIVAL_AREA, SNOWPOINT = 0, 1, 2
SHARDS = (72, 73, 74, 75)                                              # ITEM_RED_SHARD .. GREEN (the same in Black 2)
MENU_BANK, SHARD_LINES, TIMES_LINE, EXIT_LINE = 321, (273, 274, 275, 276), 277, 5   # menu_entries.json
RIBBON_NAMES_BANK = 484
RIBBONS = 80
# pokeplatinum constants/forms.h, Pokemon_ReadMovesetMaskByte: (species, form) -> moveset
SPECIES_DEOXYS, SPECIES_WORMADAM, SPECIES_GIRATINA, SPECIES_SHAYMIN, SPECIES_ROTOM = 386, 413, 487, 492, 479
FORMS = {(SPECIES_DEOXYS, 1): 494, (SPECIES_DEOXYS, 2): 495, (SPECIES_DEOXYS, 3): 496,
         (SPECIES_WORMADAM, 1): 497, (SPECIES_WORMADAM, 2): 498, (SPECIES_GIRATINA, 1): 499, (SPECIES_SHAYMIN, 1): 500,
         (SPECIES_ROTOM, 1): 501, (SPECIES_ROTOM, 2): 502, (SPECIES_ROTOM, 3): 503, (SPECIES_ROTOM, 4): 504,
         (SPECIES_ROTOM, 5): 505}
FORM_DIRS = ('deoxys/forms/attack', 'deoxys/forms/defense', 'deoxys/forms/speed', 'wormadam/forms/sandy',
             'wormadam/forms/trash', 'giratina/forms/origin', 'shaymin/forms/sky', 'rotom/forms/heat', 'rotom/forms/wash',
             'rotom/forms/frost', 'rotom/forms/fan', 'rotom/forms/mow')     # speciesproc.c alt_forms_with_data
# Black 2's PKM_PARAM ranges for Platinum's MON_DATA ribbon fields (plat_party.c sRibbonRanges)
RIBBON_FIELDS = ((25, 52, 0x19), (78, 109, 0x4D), (123, 142, 0x78))
if not version.PLATINUM:             # (v101-story) Pearl's MON_DATA numbers: the Sinnoh contest ribbons are 122-141 (Platinum
    RIBBON_FIELDS = ((25, 52, 0x19), (78, 109, 0x4D), (122, 141, 0x78))   # adds a field before them: pokediamond's
                                     # include/constants/pokemon.h MON_DATA_SUPER_COOL_RIBBON 122, Platinum's 123)
CONTEST_COOL = 0x13                                                     # PKM_PARAM_CONTEST_COOL (Platinum's MON_DATA_COOL)


@functools.lru_cache(None)
def rom():
    from gen4rom import Rom
    return Rom(version.SOURCE_DUMP)      # (v101-story: the version's own dump; Platinum's WORLD_DUMP is the same file)


TUTORS = version.PLATINUM            # (v101-story) only Platinum has the shard tutors


def _find(pat, what):
    d = rom().data
    hits = [m.start() for m in re.finditer(re.escape(pat), d)]
    assert len(hits) == 1, f'{what}: {len(hits)} matches in the {version.NAME} dump'
    return hits[0]


@functools.lru_cache(None)
def tutor_moves():
    """[(move, (red, blue, yellow, green), location)] of sTeachableMoves, in Platinum's order (the tutor index)."""
    assert TUTORS, f'{version.NAME} has no shard tutors'
    d = rom().data
    # Dive (291) 2/4/2/0 at Route 212, Mud-Slap (189) 4/4/0/0 at the Survival Area: the table's first two
    o = _find(struct.pack('<H4BxxI', 291, 2, 4, 2, 0, ROUTE_212) + struct.pack('<H4BxxI', 189, 4, 4, 0, 0, SURVIVAL_AREA),
              'sTeachableMoves')
    out = []
    for k in range(MOVES):
        move, r, b, y, g, pad, loc = struct.unpack_from('<H4BHI', d, o + 12 * k)
        assert pad == 0 and loc in (0, 1, 2) and 0 < move <= 467, f'sTeachableMoves[{k}]: {move} {loc}'
        out.append((move, (r, b, y, g), loc))
    return tuple(out), o


@functools.lru_cache(None)
def masks():
    """sSpeciesLearnsetsByTutor: MOVESETS masks of MASK bytes, right after sTeachableMoves."""
    moves, o = tutor_moves()
    d = rom().data
    start = o + 12 * MOVES
    return tuple(d[start + MASK * k: start + MASK * (k + 1)] for k in range(MOVESETS))


@functools.lru_cache(None)
def footprints():
    """[(type, has a print)] of sFootprintTypes, species 0-493."""
    d = rom().data
    # species 0-7 (pokeplatinum res/pokemon/*/data.json "footprint"): (none, no print) for 0, then Bulbasaur and Ivysaur
    # (cute, print), Venusaur (tough, print), Charmander (cute, print), Charmeleon and Charizard (tough, print),
    # Squirtle (cute, print)
    o = _find(struct.pack('<16H', 0, 0, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1), 'sFootprintTypes')
    out = [struct.unpack_from('<HH', d, o + 4 * k) for k in range(FOOTPRINTS)]
    assert all(t <= 5 and p <= 1 for t, p in out), 'sFootprintTypes: a type past FOOTPRINT_TYPE_SILENT'
    return tuple(out)


@functools.lru_cache(None)
def ribbons():
    """[(Platinum MON_DATA field, name line)] of sRibbonDataTable (ribbon ids 0-79)."""
    d = rom().data
    # RIBBON_HOENN_CHAMPION (MON_DATA_CHAMPION_RIBBON 98), then the Hoenn Cool ribbons (78, 79, 80): names 0-3
    o = _find(struct.pack('<IHHHH', 98, 72, 0, 0, 80) + struct.pack('<IHHHH', 78, 73, 0, 1, 81), 'sRibbonDataTable')
    out = []
    for k in range(RIBBONS):
        field, sprite, palette, name, desc = struct.unpack_from('<IHHHH', d, o + 12 * k)
        assert b2_param(field) is not None, f'ribbon {k}: MON_DATA {field} is no ribbon this knows'
        out.append((field, name))
    return tuple(out)


def b2_param(field):
    """Black 2's PKM_PARAM for one of Platinum's MON_DATA ribbon fields (None: not one)."""
    for lo, hi, b2 in RIBBON_FIELDS:
        if lo <= field <= hi:
            return b2 + field - lo
    return None


def ribbon_param(ribbon):
    """Black 2's PKM_PARAM of Platinum's ribbon id."""
    return b2_param(ribbons()[ribbon][0])


def ribbon_name_line(ribbon):
    return ribbons()[ribbon][1]


def location_moves(location):
    """[(tutor index, move, costs)] of a tutor's moves, in Platinum's order (its menu's)."""
    return [(i, m, c) for i, (m, c, loc) in enumerate(tutor_moves()[0]) if loc == location]


def blob():
    """PlatPartyTable (include/pearlb2/plat_party.h) for the overlay's gPlatPartyTable. (v101-story) Pearl and Diamond: no
    tutor move (moveCount 0: every tutor question answers "can't"), the footprints at their fixed place."""
    if not TUTORS:
        out = bytes(4 + 8 * MOVES + MASK * MOVESETS)        # (PlatPartyTutorMove: 8 bytes)
        out += bytes(t | (PRINT if p else 0) for t, p in footprints())
        out += bytes(TABLE_SIZE - len(out))
        assert len(out) == TABLE_SIZE, len(out)
        return out
    moves = tutor_moves()[0]
    out = struct.pack('<HH', MOVES, MOVESETS)
    for move, cost, loc in moves:
        out += struct.pack('<H4BBx', move, *cost, loc)
    out += b''.join(masks())
    out += bytes(t | (PRINT if p else 0) for t, p in footprints())
    out += bytes(TABLE_SIZE - len(out))
    assert len(out) == TABLE_SIZE, len(out)
    return out


# ---- the overlay's rule in Python (plat_party.c TutorMove, Moveset), for the test ----------------------------------------
def moveset(species, form, egg=False):
    if species == 0 or species > SPECIES or egg:
        return 0
    return FORMS.get((species, form), species)


def tutor_answer(species, form, known, index, egg=False):
    """0 can't learn tutor move index, 1 can, 2 knows it already (as the overlay answers)."""
    ms = moveset(species, form, egg)
    if not ms or index >= MOVES:
        return 0
    if not (masks()[ms - 1][index // 8] >> (index % 8)) & 1:
        return 0
    return 2 if tutor_moves()[0][index][0] in known else 1


def tutor_any(species, form, known, location):
    return int(any(tutor_answer(species, form, known, i) == 1 for i, m, c in location_moves(location)))


# ---- the offline test ----------------------------------------------------------------------------------------------------
def _decomp_names(kind):
    return [l.strip() for l in open(os.path.join(PLATINUM_SRC, 'generated', f'{kind}.txt')) if l.strip()]


def test_pearl():
    """(v101-story) Pearl's or Diamond's tables against pokediamond: the footprints (overlay 5's ov05_021FCA00 rows), the
    ribbons' MON_DATA fields and names (src/unk_0207FC5C.c, include/constants/pokemon.h's MON_DATA order, ribbon.h's ids),
    and the blob's layout (the footprints where the overlay reads them)."""
    dia = os.path.join(ROOT, 'external', 'pokediamond')
    rows = re.findall(r'\.short (0x[0-9A-Fa-f]+), (0x[0-9A-Fa-f]+) ; (SPECIES_\w+)',
                      open(os.path.join(dia, 'arm9', 'overlays', '05', 'asm', 'ov05_021F61DC.s')).read())
    assert len(rows) == FOOTPRINTS, len(rows)
    want = tuple((int(t, 16), int(p, 16)) for t, p, sp in rows)
    bad = [i for i in range(FOOTPRINTS) if footprints()[i] != want[i]]
    assert not bad, f'footprints differ from pokediamond for species {bad[:10]}'
    src = open(os.path.join(dia, 'arm9', 'src', 'unk_0207FC5C.c')).read()
    order = re.findall(r'\{ (MON_DATA_\w+), +\d+, +\d+, (RIBBON_\w+),', src)
    assert len(order) == RIBBONS, len(order)
    enum = open(os.path.join(dia, 'include', 'constants', 'pokemon.h')).read()
    fields = {m.group(1): int(m.group(2), 0) for m in re.finditer(r'#define (MON_DATA_\w+)\s+(\d+|0x[0-9A-Fa-f]+)', enum)}
    if not fields:                       # (an enum, not defines: count the names in order)
        body = enum[enum.index('MON_DATA_PERSONALITY'):]
        names = re.findall(r'(MON_DATA_\w+)', body)
        fields = {n: i for i, n in enumerate(dict.fromkeys(names))}
    assert [f for f, n in ribbons()] == [fields[f] for f, r in order], 'ribbon fields differ from pokediamond'
    assert len({ribbon_param(r) for r in range(RIBBONS)}) == RIBBONS, 'two ribbons on one Black 2 parameter'
    b = blob()
    at = 4 + 8 * MOVES + MASK * MOVESETS
    assert b[:4] == bytes(4) and b[at:at + FOOTPRINTS] == bytes(t | (PRINT if p else 0) for t, p in want)
    import gen4_text
    rnames = gen4_text.bank(RIBBON_NAMES_BANK)
    print(f'platinum_party_data test ({version.NAME}): {FOOTPRINTS} footprints and {RIBBONS} ribbons equal pokediamond\'s; '
          f'no tutor in the blob; ribbons {", ".join(f"{r} {rnames[ribbon_name_line(r)]} -> {ribbon_param(r):#x}" for r in (24, 59, 65, 66, 69))}'
)


def test():
    if not TUTORS:
        return test_pearl()
    moves = _decomp_names('moves')
    species = _decomp_names('species')
    tutors = json.load(open(os.path.join(PLATINUM_SRC, 'res', 'pokemon', 'move_tutors.json')))
    table = tutor_moves()[0]
    locs = _decomp_names('tutor_locations')
    assert [moves[m] for m, c, l in table] == [t['move'] for t in tutors], 'sTeachableMoves: moves differ'
    assert [c for m, c, l in table] == [(t['redCost'], t['blueCost'], t['yellowCost'], t['greenCost']) for t in tutors]
    assert [locs[l] for m, c, l in table] == [t['location'] for t in tutors]
    names = [t['move'] for t in tutors]

    def json_mask(path):
        d = json.load(open(path))
        m = [0] * MASK
        for mv in d['learnset'].get('by_tutor', []):
            if mv in names:
                k = names.index(mv)
                m[k // 8] |= 1 << (k % 8)
        return bytes(m)
    dirs = [species[i][len('SPECIES_'):].lower() for i in range(1, SPECIES + 1)] + list(FORM_DIRS)
    bad = [i + 1 for i, d in enumerate(dirs)
           if masks()[i] != json_mask(os.path.join(PLATINUM_SRC, 'res', 'pokemon', d, 'data.json'))]
    assert not bad, f'masks differ from the decomp for movesets {bad[:10]}'
    types = ['FOOTPRINT_TYPE_NONE', 'FOOTPRINT_TYPE_CUTE', 'FOOTPRINT_TYPE_TOUGH', 'FOOTPRINT_TYPE_SCARY',
             'FOOTPRINT_TYPE_SLOW', 'FOOTPRINT_TYPE_SILENT']
    fbad = []
    for i in range(1, FOOTPRINTS):
        f = json.load(open(os.path.join(PLATINUM_SRC, 'res', 'pokemon', dirs[i - 1], 'data.json')))['footprint']
        want = (types.index(f['type']), int(f['has'] or species[i] == 'SPECIES_SPIRITOMB'))
        if footprints()[i] != want:
            fbad.append(i)
    assert not fbad and footprints()[0] == (0, 0), f'footprints differ for species {fbad[:10]}'
    import gen4_text
    rnames = gen4_text.bank(RIBBON_NAMES_BANK)
    src = open(os.path.join(PLATINUM_SRC, 'src', 'ribbon.c')).read()
    order = re.findall(r'\.monDataParam = (MON_DATA_\w+),', src)
    params = _decomp_names('pokemon_data_params')
    assert [params[f] for f, n in ribbons()] == order, 'sRibbonDataTable: fields differ from src/ribbon.c'
    assert len({ribbon_param(r) for r in range(RIBBONS)}) == RIBBONS, 'two ribbons on one Black 2 parameter'
    # Platinum's own examples, by hand (Bulbapedia's Platinum tutor lists agree): (species, form, known moves) -> answers
    idx = {moves[m]: i for i, (m, c, l) in enumerate(table)}
    cases = [
        ((25, 0, ()), 'MOVE_THUNDER_PUNCH', 1),            # Pikachu learns ThunderPunch at Route 212
        ((25, 0, (moves.index('MOVE_THUNDER_PUNCH'),)), 'MOVE_THUNDER_PUNCH', 2),   # knows it already
        ((25, 0, ()), 'MOVE_FIRE_PUNCH', 0),               # not Fire Punch
        ((6, 0, ()), 'MOVE_FIRE_PUNCH', 1),                # Charizard: Fire Punch
        ((129, 0, ()), 'MOVE_DIVE', 0),                    # Magikarp: no tutor move at all
        ((479, 0, ()), 'MOVE_THUNDER_PUNCH', 0),           # Rotom (plain) has no ThunderPunch ...
        ((479, 0, ()), 'MOVE_SIGNAL_BEAM', 1),             # ... but Signal Beam (Snowpoint)
        ((487, 0, ()), 'MOVE_OUTRAGE', 1),                 # Giratina: Outrage
        ((493, 0, ()), 'MOVE_DIVE', 1),                    # Arceus: Dive
        ((129, 0, ()), 'MOVE_BOUNCE', 1),                  # Magikarp's one tutor move: Bounce (the Survival Area)
        ((494, 0, ()), 'MOVE_DIVE', 0),                    # Victini: Black 2's species, no mask (not Deoxys's)
        ((1, 0, ()), 'MOVE_SEED_BOMB', 1),                 # Bulbasaur: Seed Bomb
    ]
    for (sp, form, known), mv, want in cases:
        got = tutor_answer(sp, form, known, idx[mv])
        assert got == want, f'{species[sp] if sp < len(species) else sp} form {form} {mv}: {got}, Platinum {want}'
    # forms with masks of their own: each form's answer is its own data.json's, not the species'
    forms_own = 0
    for (sp, form), ms in FORMS.items():
        assert moveset(sp, form) == ms
        if masks()[ms - 1] != masks()[sp - 1]:          # Deoxys's three forms, Wormadam's two, Shaymin's Sky Forme
            assert any(tutor_answer(sp, form, (), i) != tutor_answer(sp, 0, (), i) for i in range(MOVES))
            forms_own += 1
    assert forms_own == 6, forms_own
    assert tutor_answer(386, 1, (), idx['MOVE_DIVE']) == ((masks()[493][idx['MOVE_DIVE'] // 8] >> (idx['MOVE_DIVE'] % 8)) & 1)
    rotom_heat = json_mask(os.path.join(PLATINUM_SRC, 'res', 'pokemon', 'rotom/forms/heat', 'data.json'))
    for i in range(MOVES):
        assert tutor_answer(479, 1, (), i) == (rotom_heat[i // 8] >> (i % 8)) & 1
    assert tutor_answer(25, 0, (), idx['MOVE_THUNDER_PUNCH'], egg=True) == 0
    assert tutor_any(129, 0, (), ROUTE_212) == 0 and tutor_any(25, 0, (), ROUTE_212) == 1
    print(f'platinum_party_data test: {MOVES} tutor moves, {MOVESETS} masks, {FOOTPRINTS} footprints and {RIBBONS} ribbons '
          f'equal the decomp\'s; {len(cases)} hand cases, the 12 forms and Rotom-Heat\'s 38 answers as Platinum\'s rule')
    print('  ribbons:', ', '.join(f'{r} {rnames[ribbon_name_line(r)]} -> {ribbon_param(r):#x}' for r in (24, 59, 65, 66, 67, 68, 69)))


def main():
    if sys.argv[1:] == ['test']:
        test()
        return
    if not TUTORS:
        print(f'{version.NAME}: no shard tutors; {FOOTPRINTS} footprints, {RIBBONS} ribbons, table blob {len(blob())} B')
        return
    for loc in range(3):
        print(f'{LOCATIONS[loc]}:', ', '.join(f'{i}:{m} {"/".join(map(str, c))}' for i, m, c in location_moves(loc)))
    print(f'masks at {tutor_moves()[1] + 12 * MOVES:#x}, table blob {len(blob())} B')


if __name__ == '__main__':
    main()
