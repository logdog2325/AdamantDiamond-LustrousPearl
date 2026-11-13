"""Platinum's Battle Hall data, read from the dump and checked against the decomp (notes/PLATINUM_FRONTIER.md "The Battle Hall").

    python3 b2tools/platinum_hall_data.py check            every table against the decomp; prints a summary
    python3 b2tools/platinum_hall_data.py --table FILE     gPlatHallTable's bytes (include/pearlb2/plat_hall.h PlatHallTable)
    python3 b2tools/platinum_hall_data.py --personal FILE  the harness's copy of Platinum's personal abilities

The Hall's rules (pokeplatinum src/overlay104/battle_hall_helpers.c) draw from these tables:
- sets(): battle/b_pl_stage/pl_bsdpm.narc, 478 sets of 16 bytes (FrontierPokemonBase); set 0 is all zeros (the Doubles' unused
  second slot reads it).
- opponents(), opponent_types(): sBattleHallPotentialOpponents and sBattleHallPotentialOpponentTypes, set n + 1's species and the
  two types the type grid matches it by.
- class tables: sHallTrainerClassesByRank (10 x 8) and sHallTrainerClassesBySelectedType (18 x 4), Platinum's class ids.
- trainer_classes(): the class of Frontier Trainers 0-299 (sFrontierTrainerClasses: the decomp generates it from
  res/trainers/frontier/data, up to the Tower's partners; the dump's pl_btdtr holds the same in each Trainer's first u16).
- name_flags(): whether a Trainer's name starts with I or J (or has one fifth): Platinum's AI test for Argenta misreads the
  current Trainer's name as her id in the 7th and 8th battle of a round (hall_rules.c ArgentaProbe).
- set_abilities(): the two abilities of each set's species and form, from Platinum's personal data (Pokemon_CalcAbility picks one by
  the personality's low bit after the Hall changes the personality).
Every code table is found in the dump by its bytes (overlay 104 is stored uncompressed), so the tables are the dump's own.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import platinum_frontier_data as pfd  # noqa: E402
from gen4rom import narc_members  # noqa: E402

PLATINUM = pfd.PLATINUM
SETS = 'battle/b_pl_stage/pl_bsdpm.narc'
PERSONAL = 'poketool/personal/pl_personal.narc'
HELPERS = 'src/overlay104/battle_hall_helpers.c'
MAGIC = 0x4C4C4148                      # 'HALL'
SET_COUNT, TRAINER_COUNT, RANKS, TYPES = 478, 300, 10, 18   # sFrontierTrainerClasses: Trainers 0-299 (frontierproc stops at Cheryl)
# Pokemon_GetFormNarcIndex: a form's personal entry
FORM_BASE = {386: 495, 413: 498, 487: 500, 492: 501, 479: 502}


def _types():
    return {n.strip(): i for i, n in enumerate(l for l in open(os.path.join(PLATINUM, 'generated', 'pokemon_types.txt')) if l.strip())}


def _table(name):
    text = pfd._source(HELPERS)
    m = re.search(r'static const u16 ' + name + r'\[[^=]*=\s*\{(.*?)\n\};', text, re.S)
    assert m, name
    return m.group(1)


def opponents():
    sp = pfd.consts('species')
    return [sp[n] for n in re.findall(r'\b(SPECIES_\w+)', _table('sBattleHallPotentialOpponents'))]


def opponent_types():
    ty = _types()
    return [(ty[a], ty[b]) for a, b in re.findall(r'\{\s*(TYPE_\w+),\s*(TYPE_\w+)\s*\}', _table('sBattleHallPotentialOpponentTypes'))]


def classes_by_rank():
    cl = pfd.consts('trainer_classes')
    rows = re.findall(r'\{([^{}]*)\}', _table('sHallTrainerClassesByRank'))
    return [[cl[n] for n in re.findall(r'\b(TRAINER_CLASS_\w+)', r)] for r in rows]


def classes_by_type():
    cl = pfd.consts('trainer_classes')
    rows = re.findall(r'\{([^{}]*)\}', _table('sHallTrainerClassesBySelectedType'))
    return [[cl[n] for n in re.findall(r'\b(TRAINER_CLASS_\w+)', r)] for r in rows]


def trainer_classes():
    """The class of each Frontier Trainer the Hall draws from (0-299), from the dump (pl_btdtr: class, count, sets)."""
    return [c for c, _ in pfd.trainers()][:TRAINER_COUNT]


def trainer_classes_decomp():
    """The same from the decomp's Trainer files (what its build writes into frontier_trainer_classes.h)."""
    cl = pfd.consts('trainer_classes')
    d = os.path.join(pfd.FRONTIER, 'data')
    return [cl[json.load(open(os.path.join(d, n + '.json')))['class']] for n in pfd.trainer_order()][:TRAINER_COUNT]


def sets():
    return narc_members(pfd.rom().read(SETS))


def personal_index(species, form):
    return FORM_BASE[species] + form if form and species in FORM_BASE else species


def set_abilities():
    per = narc_members(pfd.rom().read(PERSONAL))
    out = []
    for s in sets():
        species, form = struct.unpack_from('<H', s, 0)[0], struct.unpack_from('<H', s, 14)[0]
        p = per[personal_index(species, form)]
        out.append((p[0x16], p[0x17]))
    return out


def _gen4_codes():
    import gen4_text
    inv = {}
    for k, v in gen4_text.CHARS.items():
        inv.setdefault(v, k)
    return inv


def name_codes(name):
    """A Frontier Trainer's name as FrontierTrainer.trainerName holds it (String_ToChars: up to 7 characters and 0xffff, the rest
    0 from MI_CpuClear8): Gen 4 character codes."""
    inv = _gen4_codes()
    codes = [inv.get(c, 0x1DE) for c in name][:7] + [0xFFFF]
    return codes + [0] * (8 - len(codes))


def name_flags():
    """Each Hall Trainer's PLAT_HALL_NAME_* bits: its name's first or fifth character is Gen 4 code 307 or 308 (I, J)."""
    out = []
    for n in pfd.names()[:TRAINER_COUNT]:
        c = name_codes(n)
        out.append((1 if c[0] in (307, 308) else 0) | (2 if c[4] in (307, 308) else 0))
    return out


def names_blob():
    """The harness's copy of the Frontier Trainers' names as Gen 4 codes: u16 count, then 8 u16 each."""
    names = pfd.names()
    return struct.pack('<H', len(names)) + b''.join(struct.pack('<8H', *name_codes(n)) for n in names)


def table(brain_bgm=0, brain_win_bgm=0):
    """PlatHallTable (include/pearlb2/plat_hall.h), as the C reads it. brain_bgm, brain_win_bgm: Argenta's battle and victory
    songs, Black 2 sequence ids (patches/platinum_hall.py gives the ones patches/battle_music.py installed; 0: Black 2's)."""
    op, ot, cr, ct, tc, st = opponents(), opponent_types(), classes_by_rank(), classes_by_type(), trainer_classes(), sets()
    assert len(op) == len(ot) and len(st) == SET_COUNT and len(tc) == TRAINER_COUNT, (len(op), len(ot), len(st), len(tc))
    assert len(cr) == RANKS and all(len(r) == 8 for r in cr) and len(ct) == TYPES and all(len(r) == 4 for r in ct)
    assert max(tc + sum(cr, []) + sum(ct, [])) < 256
    out = struct.pack('<IHHHH', MAGIC, len(st), len(op), len(tc), 0)
    out += b''.join(st)
    out += b''.join(bytes(a) for a in set_abilities())
    out += struct.pack(f'<{len(op)}H', *op)
    out += b''.join(bytes(t) for t in ot)
    out += bytes(tc) + bytes(sum(cr, [])) + bytes(sum(ct, [])) + bytes(name_flags())
    out += struct.pack('<HH', brain_bgm, brain_win_bgm)     # brainBgm, brainWinBgm: Argenta's songs
    while len(out) % 4:
        out += b'\0'
    return out


def check(verbose=True):
    problems = []
    op, ot = opponents(), opponent_types()
    if len(op) != len(ot):
        problems.append(f'{len(op)} opponents, {len(ot)} type rows')
    st = sets()
    if len(st) != SET_COUNT or st[0] != bytes(16):
        problems.append(f'{len(st)} sets; set 0 {st[0].hex()}')
    for i, sp in enumerate(op):           # set i + 1 is opponent i's
        if struct.unpack_from('<H', st[i + 1], 0)[0] != sp:
            problems.append(f'set {i + 1} is species {struct.unpack_from("<H", st[i + 1], 0)[0]}, the list says {sp}')
    if trainer_classes() != trainer_classes_decomp():
        problems.append('the Frontier Trainers\' classes differ between the dump and the decomp')
    found = {
        'opponents': pfd._find(struct.pack(f'<{len(op)}H', *op)),
        'opponent types': pfd._find(b''.join(struct.pack('<HH', a, b) for a, b in ot)),
        'classes by rank': pfd._find(b''.join(struct.pack('<8H', *r) for r in classes_by_rank())),
        'classes by type': pfd._find(b''.join(struct.pack('<4H', *r) for r in classes_by_type())),
        'Frontier Trainers\' classes': pfd._find(struct.pack(f'<{TRAINER_COUNT}H', *trainer_classes())),
    }
    for k, v in found.items():
        if len(v) != 1:
            problems.append(f'{k}: found {len(v)} times in the dump ({v[:4]})')
    if verbose:
        print(f'{len(st)} sets, {len(op)} opponents ({len(set(op))} species), {TRAINER_COUNT} Trainers\' classes, '
              f'{len(set_abilities())} ability pairs; tables found in the dump at ' +
              ', '.join(f'{k} {v[0] if v else "-"}' for k, v in found.items()))
        print(f'gPlatHallTable: {len(table())} bytes')
    return problems


def personal_blob():
    """The harness's Platinum personal abilities: u16 count, then abilities 1 and 2 of every personal entry (forms after 495)."""
    per = narc_members(pfd.rom().read(PERSONAL))
    return struct.pack('<H', len(per)) + b''.join(bytes((p[0x16], p[0x17])) for p in per)


def main(argv):
    if argv[:1] == ['--names']:
        open(argv[1], 'wb').write(names_blob())
        return 0
    if argv[:1] == ['--personal']:
        open(argv[1], 'wb').write(personal_blob())
        return 0
    if argv[:1] == ['--table']:
        open(argv[1], 'wb').write(table())
        print(f'{argv[1]}: {len(table())} bytes')
        return 0
    if argv[:1] == ['check']:
        p = check()
        for x in p:
            print('PROBLEM', x)
        print(f'{len(p)} problems')
        return 1 if p else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
