"""Platinum's HM badges (2026-11-07, plat-ch4; notes/PLATINUM_CHAPTERS.md "Shared pieces", notes/TMS.md "HMs by badge").

The HM rule (a field move works with its badge) has Pearl's badges in the decomp: src/pearlb2/resident/field_moves.c
sFieldMoveBadges and its party-menu checks, include/pearlb2.h PEARLB2_BADGE_DEFOG. There Surf needs the Relic Badge (4) and
Defog the Fen Badge (3). Platinum swaps the two (pokeplatinum src/field_move_tasks.c: FieldMoves_CheckSurf BADGE_ID_FEN,
FieldMoves_CheckDefog BADGE_ID_RELIC), and the Relic Badge is its third (Fantina, chapter 4): with Pearl's rule Surf would
work from Hearthome on, two badges early, and Defog only from Pastoria. The other six are the same in both games: Rock Smash
Coal 0, Cut Forest 1, Fly Cobble 2, Strength Mine 5, Rock Climb Icicle 6 (PEARLB2_BADGE_ROCK_CLIMB), Waterfall Beacon 7
(Platinum's field_move_tasks.c checks, and the CheckBadgeAcquired lines of its scripts_field_moves.s).

This patch writes Platinum's two badges into the build's code, in the four places that hold them:
- sFieldMoveBadges (the resident section): the Surf row 4 -> 3, the Defog row 3 -> 4. PearlB2_FieldMoveSlot reads it: Black
  2's Surf at the water, Waterfall, and every script's "who can use it?" (PokePartyHasMoveAny);
- PearlB2_SurfCallCheck (the party menu's Surf): the `movs r1, #4` it passes to isBadgeObtained -> #3;
- PearlB2_DefogOffer (A under the deep fog) and PearlB2_DefogCheck (ITCM, src/pearlb2/defog_itcm.c: the party menu's Defog):
  `movs r1, #3` -> #4.
Each place is checked first: the table must be Pearl's (or already Platinum's, on a quick non-clean build), and each
immediate must be the one `movs r1, #n` of its function that sits right before a bl to isBadgeObtained.

Platinum only: a Pearl or Diamond build doesn't run it, so their code is unchanged (a patch at build time rather than a version
switch in the C, which would need a decomp tree and build of its own). List it after platinum_regigigas.

    PEARL_VERSION=platinum python3 b2tools/patches/platinum_field_moves.py [CODE_DIR]
        the offline check: reads the four places (default: the decomp's last build) and says what the patch would write
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import decomp, itcm, resident, version  # noqa: E402

MOVE_ROCK_SMASH, MOVE_CUT, MOVE_FLY, MOVE_DEFOG, MOVE_SURF, MOVE_STRENGTH, MOVE_ROCK_CLIMB, MOVE_WATERFALL = \
    249, 15, 19, 432, 57, 70, 431, 127
COAL, FOREST, COBBLE, FEN, RELIC, MINE, ICICLE, BEACON = range(8)
# move -> badge: Pearl's (pokediamond arm9/src/field_move.c FieldMove_Check*, the decomp's table) and Platinum's
PEARL = {MOVE_ROCK_SMASH: COAL, MOVE_CUT: FOREST, MOVE_FLY: COBBLE, MOVE_DEFOG: FEN, MOVE_SURF: RELIC, MOVE_STRENGTH: MINE,
         MOVE_ROCK_CLIMB: ICICLE, MOVE_WATERFALL: BEACON}
PLATINUM = {**PEARL, MOVE_SURF: FEN, MOVE_DEFOG: RELIC}
ROWS = 8                                    # sFieldMoveBadges: {u16 move, u16 badge} x 8
# the functions that pass a badge to isBadgeObtained as an immediate: (symbol, Pearl's badge, Platinum's)
IMMEDIATES = [('PearlB2_SurfCallCheck', RELIC, FEN), ('PearlB2_DefogOffer', FEN, RELIC), ('PearlB2_DefogCheck', FEN, RELIC)]


def _size(name, code):
    path = os.path.join(code, 'arm9.o.xMAP') if code and os.path.exists(os.path.join(code, 'arm9.o.xMAP')) else decomp.XMAP
    m = re.search(rf'^\s+[0-9A-F]{{8}} ([0-9A-F]{{8}}) \.\w+\s+{name}\t', open(path, errors='replace').read(), re.M)
    return int(m.group(1), 16) if m else None


def table(code):
    """(address, {move: badge}) of sFieldMoveBadges."""
    at = decomp.symbol('sFieldMoveBadges', code)
    assert at is not None and _size('sFieldMoveBadges', code) == 4 * ROWS, \
        'platinum_field_moves: the decomp has no sFieldMoveBadges of 8 rows (src/pearlb2/resident/field_moves.c)'
    rows = struct.unpack('<16H', resident.read(code, at, 4 * ROWS))
    return at, dict(zip(rows[0::2], rows[1::2]))


def immediate(code, name):
    """(address of the `movs r1, #n` before the bl to isBadgeObtained in function name, n)."""
    fn, size, target = decomp.symbol(name, code), _size(name, code), decomp.symbol('isBadgeObtained', code)
    assert fn is not None and size and target is not None, f'platinum_field_moves: no {name} / isBadgeObtained in the link'
    body = resident.read(code, fn, size)
    hits = []
    for at in range(0, size - 5, 2):
        half, = struct.unpack_from('<H', body, at)
        if half >> 8 == 0x21 and body[at + 2:at + 6] == itcm.bl(fn + at + 2, target):     # movs r1, #n; bl isBadgeObtained
            hits.append((fn + at, half & 0xFF))
    assert len(hits) == 1, f'platinum_field_moves: {name}: {len(hits)} badge arguments to isBadgeObtained, not 1'
    return hits[0]


def plan(code):
    """[(address, old bytes, new bytes, what)] for the build's code; [] when it is Platinum's already."""
    out = []
    at, have = table(code)
    if have != PLATINUM:
        assert have == PEARL, f'platinum_field_moves: sFieldMoveBadges is neither Pearl\'s nor Platinum\'s: {have}'
        assert list(have) == list(PEARL), 'platinum_field_moves: sFieldMoveBadges rows are not in Pearl\'s order'
        new = struct.pack('<16H', *[v for move in PEARL for v in (move, PLATINUM[move])])
        out.append((at, resident.read(code, at, 4 * ROWS), new, 'sFieldMoveBadges: Surf 4 -> 3, Defog 3 -> 4'))
    for name, pearl, plat in IMMEDIATES:
        where, n = immediate(code, name)
        if n == plat:
            continue
        assert n == pearl, f'platinum_field_moves: {name} checks badge {n}, neither Pearl\'s {pearl} nor Platinum\'s {plat}'
        out.append((where, struct.pack('<H', 0x2100 | n), struct.pack('<H', 0x2100 | plat),
                    f'{name}: badge {n} -> {plat}'))
    return out


def apply_code(code):
    assert version.PLATINUM, 'platinum_field_moves: a Platinum build only'
    done = plan(code)
    for where, old, new, what in done:
        assert resident.read(code, where, len(old)) == old
        resident.write(code, where, new)
    assert not plan(code), 'platinum_field_moves: the code is not Platinum\'s after the patch'
    return ('platinum_field_moves: Platinum\'s HM badges (Surf the Fen Badge, Defog the Relic Badge): '
            + ('; '.join(w for _, _, _, w in done) if done else 'already in the code'))


if __name__ == '__main__':
    code = sys.argv[1] if len(sys.argv) > 1 else decomp.CODE
    at, have = table(code)
    print(f'sFieldMoveBadges at {at:#x}: ' + ', '.join(f'{m} -> {b}' for m, b in have.items())
          + (' (Pearl\'s)' if have == PEARL else ' (Platinum\'s)' if have == PLATINUM else ' (neither)'))
    for name, pearl, plat in IMMEDIATES:
        where, n = immediate(code, name)
        print(f'{name}: movs r1, #{n} at {where:#x} (Pearl {pearl}, Platinum {plat})')
    for where, old, new, what in plan(code):
        print(f'  would write {new.hex()} over {old.hex()} at {where:#x}: {what}')
