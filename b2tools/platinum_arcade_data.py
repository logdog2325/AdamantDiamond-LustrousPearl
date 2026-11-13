"""Platinum's Battle Arcade data, checked against the dump and Black 2 (notes/PLATINUM_FRONTIER.md "The Battle Arcade").

    python3 b2tools/platinum_arcade_data.py check
    python3 b2tools/platinum_arcade_data.py --personal FILE     the harness's copy of Platinum's personal data and experience tables

The Arcade's rules (src/pokebw2/src/pearlb2/plat_arcade/arcade_rules.c) keep its tables as the decomp's source has them; `check`
finds each one in the dump's own code (overlay 104, the Frontier's, and overlay 108, the game board's: both stored uncompressed),
and checks arcade_rules.c has the same numbers:
- battle_arcade_helpers.c: sBattleArcadeOpponentPools, sBonus1BP, sBonus3BP;
- battle_arcade.c: sRouletteSpeedByRound, the performance's three tables, the item and Berry pools, BattleArcade_GetEarnedBP's two;
- the board (applications/frontier/battle_arcade/main.c): sCursorMoveFrames, sEffectAvailabilityByRound and ...ByBattle (bit
  fields: a byte an effect, bit 0 the first round or battle), sCategoryWeights, sCategoryTierPerformanceThresholds.
And that every item the Arcade names has the same number in Black 2 (the decomp's generated/items.txt), so the rules' ids are
Black 2's too; and that the DS's division routine (_s32_div_f, its remainder by zero 0: arcade_rules.c DSMod) is the same bytes
in Platinum's code and in Black 2's.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import platinum_frontier_data as pfd  # noqa: E402
from gen4rom import narc_members  # noqa: E402

PLATINUM = pfd.PLATINUM
B2 = os.path.join(ROOT, 'external', 'pokebw2')
OURS = os.path.join(ROOT, 'src', 'pokebw2', 'src', 'pearlb2', 'plat_arcade', 'arcade_rules.c')
HELPERS = 'src/overlay104/battle_arcade_helpers.c'
ARCADE = 'src/overlay104/battle_arcade.c'
BOARD = 'src/applications/frontier/battle_arcade/main.c'
PERSONAL = 'poketool/personal/pl_personal.narc'
GROWTH = 'poketool/personal/pl_growtbl.narc'
FRONTIER_OVERLAY, BOARD_OVERLAY = 104, 108
B2_DIV = 0x0208d65c, 0x20c                      # _s32_div_f in Black 2's arm9 (config/b2_us/arm9/symbols.txt)
EFFECTS = 32


# The board's panels on the field (src/pearlb2/plat_arcade/arcade_field.c): 32 lines of the room's text, by effect, that name them.
# Platinum's panels are pictures (the app's sprites, a picture an effect), not words; these are short names of what each does (its
# scene's lines say it in full), at most 9 characters so four fit across the window (60 pixels a panel).
BOARD_NAMES = (
    'Foe HP-', 'Foe PSN', 'Foe PAR', 'Foe BRN', 'Foe SLP', 'Foe FRZ', 'Foe Berry', 'Foe Item', 'Foe Lv+3',
    'Own HP-', 'Own PSN', 'Own PAR', 'Own BRN', 'Own SLP', 'Own FRZ', 'Own Berry', 'Own Item', 'Own Lv+3',
    'Sun', 'Rain', 'Sandstorm', 'Hail', 'Fog', 'Trick Rm',
    'Speed Up', 'Slow Down', 'Random', 'Swap', '1 BP', 'Skip', 'No Event', '3 BP',
)
assert len(BOARD_NAMES) == EFFECTS and max(len(n) for n in BOARD_NAMES) <= 9


def _consts(path):
    return {n.split('=')[0].strip(): i for i, n in enumerate(l.strip() for l in open(path) if l.strip() and not l.startswith('#'))}


def _src(path):
    return open(os.path.join(PLATINUM, path)).read()


def _numbers(body, extra=None):
    """The numbers of a C table's body (items, Frontier Trainers and the given names resolved)."""
    items = _consts(os.path.join(PLATINUM, 'generated', 'items.txt'))
    order = [l.strip() for l in open(os.path.join(PLATINUM, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    trainers = {f'FRONTIER_TRAINER_{n.upper()}': i for i, n in enumerate(order)}
    names = dict(items, **trainers, **(extra or {}))
    body = re.sub(r'/\*.*?\*/', '', re.sub(r'//[^\n]*', '', body))
    out = []
    for tok in re.findall(r'\w+', body):
        if tok.isdigit():
            out.append(int(tok))
        elif tok in names:
            out.append(names[tok])
    return out


def _table(text, name):
    m = re.search(r'\b' + name + r'(?:\[[^\]]*\])*\s*=\s*\{(.*?)\}\s*;', text, re.S)
    assert m, name
    return m.group(1)


def _bitfield_rows(body):
    """sEffectAvailabilityBy*: a byte a row, bit 0 the first column."""
    rows = re.findall(r'\{([^{}]*)\}', re.sub(r'//[^\n]*', '', body))
    return [sum(int(v) << i for i, v in enumerate(re.findall(r'\d+', r))) for r in rows]


def platinum_tables():
    """{name: (numbers, struct format)} from the decomp's source."""
    h, a, b = _src(HELPERS), _src(ARCADE), _src(BOARD)
    out = {}
    out['sBattleArcadeOpponentPools'] = (_numbers(_table(h, 'sBattleArcadeOpponentPools')), '<H')
    for n in ('sBonus1BP', 'sBonus3BP'):
        out[n] = (_numbers(_table(h, n)), '<B')
    out['sRouletteSpeedByRound'] = (_numbers(_table(a, 'sRouletteSpeedByRound')), '<B')
    for n in ('sPerformanceByNumWithStatus', 'sPerformanceByNumFainted', 'sPerformanceByTurnsElapsed', 'sBPPerRoundSolo',
              'sBPPerRoundWifi'):
        out[n] = (_numbers(_table(a, n)), '<B')
    for n in ('sItemPoolTier1', 'sItemPoolTier2', 'sItemPoolTier3', 'sBerryPoolTier1', 'sBerryPoolTier2', 'sBerryPoolTier3'):
        out[n] = (_numbers(_table(a, n)), '<H')
    out['sCursorMoveFrames'] = (_numbers(_table(b, 'sCursorMoveFrames')), '<B')
    out['sEffectAvailabilityByRound'] = (_bitfield_rows(_table(b, 'sEffectAvailabilityByRound')), '<B')
    out['sEffectAvailabilityByBattle'] = (_bitfield_rows(_table(b, 'sEffectAvailabilityByBattle')), '<B')
    out['sCategoryWeights'] = (_numbers(_table(b, 'sCategoryWeights')), '<B')
    out['sCategoryTierPerformanceThresholds'] = (_numbers(_table(b, 'sCategoryTierPerformanceThresholds')), '<B')
    return out


def our_tables():
    """The same tables as arcade_rules.c has them."""
    t = open(OURS).read()
    defs = {n: int(v) for n, v in re.findall(r'#define (TRAINER_\w+) (\d+)', t)}
    out = {'sBattleArcadeOpponentPools': _numbers(_table(t, 'sOpponentPools'), defs)}
    same = ('sBonus1BP', 'sBonus3BP', 'sRouletteSpeedByRound', 'sPerformanceByNumWithStatus', 'sPerformanceByNumFainted',
            'sPerformanceByTurnsElapsed', 'sBPPerRoundSolo', 'sBPPerRoundWifi', 'sItemPoolTier1', 'sItemPoolTier2', 'sItemPoolTier3',
            'sBerryPoolTier1', 'sBerryPoolTier2', 'sBerryPoolTier3', 'sCategoryWeights', 'sCategoryTierPerformanceThresholds')
    for n in same:
        out[n] = [int(x, 0) for x in re.findall(r'\b(0x[0-9a-f]+|\d+)\b', re.sub(r'/\*.*?\*/', '', _table(t, n)))]
    # (ours keeps the first column of sCursorMoveFrames, Platinum's second is all 0; the bit fields as their bytes)
    frames = [int(x) for x in re.findall(r'\d+', _table(t, 'sCursorMoveFrames'))]
    out['sCursorMoveFrames'] = [v for f in frames for v in (f, 0)]
    for n in ('sEffectAvailabilityByRound', 'sEffectAvailabilityByBattle'):
        out[n] = [int(x, 16) for x in re.findall(r'0x([0-9a-f]+)', re.sub(r'//[^\n]*', '', _table(t, n)))]
    return out


def overlay(n):
    """An overlay's file from the dump's overlay table (y9), and whether it is stored compressed."""
    d = pfd.rom().data
    ovt_off, ovt_len = struct.unpack_from('<II', d, 0x50)
    for i in range(ovt_len // 32):
        oid, ram, size, bss, s0, s1, fid, flags = struct.unpack_from('<8I', d, ovt_off + 32 * i)
        if oid == n:
            return pfd.rom().read(fid), bool(flags >> 24 & 1)
    raise KeyError(n)


def check(verbose=True):
    problems = []
    plat, ours = platinum_tables(), our_tables()
    code = {FRONTIER_OVERLAY: overlay(FRONTIER_OVERLAY), BOARD_OVERLAY: overlay(BOARD_OVERLAY)}
    for n, (c, packed) in code.items():
        if packed:
            problems.append(f'overlay {n} is compressed: its tables can\'t be found by their bytes')
    for name, (values, fmt) in plat.items():
        where = BOARD_OVERLAY if name.startswith(('sCursor', 'sEffect', 'sCategory')) else FRONTIER_OVERLAY
        blob = b''.join(struct.pack(fmt, v) for v in values)
        at = code[where][0].find(blob)
        if at < 0:
            problems.append(f'{name}: not in overlay {where}')
        if ours.get(name) != values:
            problems.append(f'{name}: arcade_rules.c has {ours.get(name)}, the decomp {values}')
        if verbose:
            print(f'{name}: {len(values)} numbers, in overlay {where} at {at:#x}, arcade_rules.c '
                  f'{"the same" if ours.get(name) == values else "DIFFERENT"}')
    plat_items = [l.strip() for l in open(os.path.join(PLATINUM, 'generated', 'items.txt')) if l.strip() and not l.startswith('#')]
    b2 = [l.strip() for l in open(os.path.join(B2, 'generated', 'items.txt')) if l.strip() and not l.startswith('#')]
    norm = lambda s: s.split('=')[0].strip().replace('ITEM_', '').replace('_', '').lower()
    ids = sorted(set(sum((plat[n][0] for n in plat if n.startswith(('sItemPool', 'sBerryPool'))), [])))
    bad = [(i, plat_items[i], b2[i]) for i in ids if norm(plat_items[i]) != norm(b2[i])]
    problems += [f'item {i}: Platinum {p}, Black 2 {b}' for i, p, b in bad]
    if verbose:
        print(f'{len(ids)} items: {len(ids) - len(bad)} the same number in Black 2')
    arm9 = open(os.path.join(B2, 'build', 'b2_us', 'build', 'arm9.bin'), 'rb').read()
    div = arm9[B2_DIV[0] - 0x02004000:B2_DIV[0] - 0x02004000 + B2_DIV[1]]
    at = pfd.rom().data.find(div)
    if at < 0:
        problems.append('_s32_div_f: Black 2\'s bytes are not in Platinum\'s dump')
    if verbose:
        print(f'_s32_div_f: Black 2\'s {len(div)} bytes in Platinum\'s dump at {at:#x} (a remainder by zero is 0 on both)')
    return problems


def personal_blob():
    """The harness's Platinum personal data: u16 count, then for every personal entry (forms after 495) its six base stats, two
    types, two abilities and growth rate (11 bytes); then the eight experience tables (101 u32 each)."""
    per = narc_members(pfd.rom().read(PERSONAL))
    out = struct.pack('<H', len(per))
    for p in per:
        out += bytes(p[0:6]) + bytes((p[6], p[7], p[0x16], p[0x17], p[0x13]))
    for g in narc_members(pfd.rom().read(GROWTH)):
        out += g[:404]
    return out


def main(argv):
    if argv[:1] == ['--personal']:
        open(argv[1], 'wb').write(personal_blob())
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
