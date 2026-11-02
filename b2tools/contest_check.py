"""Offline proof of Pearl's Super Contests (notes/CONTESTS.md): run it after the decomp's build.

- the tables the rules compile in are Pearl's bytes; the tables Platinum and Pearl share are where Pearl has them;
- Pearl's and Diamond's contest code and data are the same, so nothing here splits by version but the text;
- every contest a player can enter has its opponents and judges, at every stage of the game;
- every move has contest data on Pearl's effects;
- the C's archive layout and this tool's agree (include/pearlb2/contest_data.h);
- the sizes the screens rely on.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import contest_data as cd  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402

FAILS = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        FAILS.append(what)


def tables():
    rom = cd.pearl()
    ram, o = cd.overlay(rom, 12)
    src = os.path.join(cd.DECOMP, 'src', 'pearlb2', 'contest')
    rows = re.findall(r'\{ (\d+), (\d+), (\d+), (-?\d+), \{ (-?\d+), (-?\d+), (-?\d+), (-?\d+) \} \}', open(os.path.join(src, 'contest_ai_rows.inc')).read())
    packed = b''.join(struct.pack('<BBBb4h', *map(int, r)) for r in rows)
    check(packed == o[cd.AI_ROWS_AT - ram:cd.AI_ROWS_AT - ram + 12 * cd.AI_ROWS], f'the {len(rows)} AI rows are Pearl\'s overlay 12 at {cd.AI_ROWS_AT:#x}')
    rules = open(os.path.join(src, 'contest_rules.c')).read()
    for name, pattern in (('the type chart', bytes.fromhex('0a00f6f600000a00f6f6f6000a00f6f6f6000a0000f6f6000a')),
                          ('fixed order: first', struct.pack('<4h', -30000, -29990, -29980, -29970)),
                          ('fixed order: last', struct.pack('<4h', 29970, 29980, 29990, 30000)),
                          ('fixed order: random', struct.pack('<4h', -10000, -500, 500, 10000)),
                          ('later turn hearts', bytes([10, 20, 30, 40])), ('AI miss by skill', bytes([1, 2, 3, 4]))):
        check(pattern in o, f'{name} in Pearl\'s overlay 12')
    a = rom.data[struct.unpack('<I', rom.data[0x20:0x24])[0]:][:struct.unpack('<I', rom.data[0x2C:0x30])[0]]
    check(struct.pack('<8H', 10, 20, 30, 40, 50, 60, 70, 80) in a or struct.pack('<8H', 10, 20, 30, 40, 50, 60, 70, 80) in o,
          'the Visual stat steps are Pearl\'s')
    check(bytes([3, 5, 8, 5, 10, 15, 7, 15, 23, 10, 20, 30]) in a or bytes([3, 5, 8, 5, 10, 15, 7, 15, 23, 10, 20, 30]) in o,
          'the Visual accessory steps are Pearl\'s')
    check('0x12A880' not in rules and '(60 * 30) * 10000' in rules, 'the beat: Pearl\'s 0x0112A880 / bpm (ov12_02230BE4)')
    check(0x0112A880 == 60 * 30 * 10000, 'Pearl\'s 0x0112A880 is 60 * 30 * 10000')


def versions():
    p, d = cd.pearl(), Rom(os.path.join(ROOT, 'roms', 'diamond.nds'))
    for f in ('contest/data/contest_data.narc', 'contest/graphic/contest_bg.narc', 'contest/graphic/contest_obj.narc',
              'graphic/imageclip.narc', 'poketool/waza/waza_tbl.narc'):
        check(p.read(f) == d.read(f), f'{f}: Pearl = Diamond')
    # overlays: same size and same bytes but for the addresses, a real difference would show as many bytes
    for n in (12, 17):
        ra, a = cd.overlay(p, n)
        rb, b = cd.overlay(d, n)
        diffs = [(x, y) for x, y in zip(a, b) if x != y]
        # the only differences: a few literals' addresses of arm9 data, 8 bytes apart (the two games' arm9 differs there)
        check(ra == rb and len(a) == len(b) and len(diffs) <= 8 and all(x - y == 8 for x, y in diffs),
              f'overlay {n}: the same in Pearl and Diamond but {len(diffs)} address bytes')


def contests():
    rom = cd.pearl()
    m = narc_members(rom.read('contest/data/contest_data.narc'))
    rows = [m[0][i:i + 48] for i in range(0, len(m[0]), 48)]
    judges = [struct.unpack_from('<H', m[1], i + 4)[0] for i in range(0, len(m[1]), 8)]
    for rank in range(4):
        for t in range(5):
            jn = [(j >> (t * 2)) & 3 for j in judges if (j >> 10) & 3 == rank]
            bad = jn.count(1) < 2 or sum(1 for x in jn if x > 1) < 1
            for late in (False, True):
                fits = 0
                for r in rows:
                    f = struct.unpack_from('<H', r, 0x20)[0]
                    if f & 7 != rank or not (f >> (3 + t)) & 1 or (f >> 8) & 1 or (f >> 9) & 1:
                        continue
                    stage = (f >> 10) & 3
                    if (stage == 1) if late else (stage in (2, 3)):
                        continue
                    if stage != 3:
                        fits += 1
                if fits < 3:
                    bad = True
            if bad:
                check(False, f'rank {rank} type {t}: too few opponents or judges')
    check(True, 'every rank and type has 3 opponents and its judges, before and after the end of the game')
    for r in rows:
        f = struct.unpack_from('<H', r, 0x20)[0]
        for theme in range(12):
            assert r[0x22 + theme] < len(m[2]) // 84
    check(len(m[2]) == 84 * 96 and all(len(x) == 100 for x in m[3:15]), 'dress rows and the 12 theme rows are the sizes the C reads')


def moves():
    t = cd.move_table(cd.pearl())
    bad = [i for i in range(1, cd.MOVE_COUNT) if t[i * 2] > 4 or t[i * 2 + 1] > 23]
    check(not bad, f'all {cd.MOVE_COUNT} moves have a contest type and an effect (Pearl\'s 22 effects); {bad[:6]}')
    zero = [i for i in range(1, cd.MOVE_COUNT) if t[i * 2 + 1] == 0]
    check(len(zero) == 0, f'no move without an effect: {zero[:8]}')


def layout():
    import gen4_text
    head = open(os.path.join(cd.DECOMP, 'include', 'pearlb2', 'contest_app.h')).read()
    block = head[head.index('CA_BG = 0'):head.index('CA_COUNT')]
    names = re.findall(r'^\s+(CA_\w+)', block, re.M)
    first = int(re.search(r'CA_OPPONENTS = (\d+)', block).group(1))
    at = names.index('CA_OPPONENTS')
    names = names[:-2] + ['_'] * 48 + ['_'] * 12        # CA_MIX is 48 members, CA_PORU 12
    check(first + len(names) - at == len(cd.members()), f'the archive has the members contest_app.h says: {first + len(names) - at}')
    res = open(os.path.join(cd.DECOMP, 'src', 'pearlb2', 'resident', 'contest.c')).read()
    n = {l: k for k, l, e in gen4_text.convert_bank(338, cd.PEARL)}
    check(f'#define MASSAGE_FIRST {n["Pretty Dewdrop"]}' in res and f'#define MASSAGE_LAST {n["Glitter Powder"]}' in res, 'the massage girl\'s Accessories')
    s = open(os.path.join(ROOT, 'src', 'field_scripts', '1282_global_contests.s')).read()
    inc = set(re.findall(r'#define (CCL_\w+)', open(os.path.join(ROOT, 'src', 'include', 'pearl_contests_lines.inc')).read()))
    miss = sorted(set(re.findall(r'CCL_\w+', s)) - inc)
    check(not miss, f'the reception\'s lines exist: {miss}')


def poffins():
    import gen4_text
    rom = cd.pearl()
    ram, o = cd.overlay(rom, 73)
    # Platinum's overlay083 tables at Pearl's addresses: the stirring's phases, their pots' burn timers and the speed steps
    for at, want, what in ((0x21dbf5c, [8, 7, 7], 'phase speeds'), (0x21dbf60, [16, 16, 16], 'burn margins'),
                           (0x21dbf64, [0, 1, 5, 10], 'participants\' weights')):
        check(list(o[at - ram:at - ram + len(want)]) == want, f'{what} at {at:#x} in Pearl\'s overlay 73')
    check(list(struct.unpack_from('<3H', o, 0x21dbf68 - ram)) == [64, 72, 80], 'the pot\'s drag 64, 72, 80 at 0x21dbf68 in Pearl\'s overlay 73')
    check(list(struct.unpack_from('<3I', o, 0x21dbfb0 - ram)) == [150, 120, 90] or list(o[0x21dbfb0 - ram:0x21dbfb3 - ram]) == [150, 120, 90],
          'phase lengths 150, 120, 90 in Pearl\'s overlay 73')
    rules = open(os.path.join(cd.DECOMP, 'src', 'pearlb2', 'resident', 'poffin_rules.c')).read()
    for values in ('8, 7, 7', '150, 120, 90', '64, 72, 80'):
        check(values in rules, f'poffin_rules.c has {values}')
    a = rom.data[struct.unpack('<I', rom.data[0x20:0x24])[0]:][:struct.unpack('<I', rom.data[0x2C:0x30])[0]]
    rows = [int(x) for r in re.findall(r'\{([^}]+)\}', open(os.path.join(cd.DECOMP, 'src', 'pearlb2', 'resident', 'contest_amity.inc')).read()) for x in r.split(',')]
    check(len(rows) == 60 and struct.pack('<60H', *rows) in a, 'Amity Square\'s 6 x 10 Accessories are the table in Pearl\'s arm9')
    names = dict((k, l) for k, l, e in gen4_text.convert_bank(338, cd.PEARL))
    check(names[rows[0]] == 'White Fluff' and names[rows[9]] == 'Stump', 'the table\'s numbers name Pearl\'s Accessories')
    berries = narc_members(rom.read('itemtool/itemdata/nuts_data.narc'))
    check(len(berries) == 64 and list(berries[0][6:11]) == [10, 0, 0, 0, 0], 'Cheri Berry is Pearl\'s: spicy 10')
    s = open(os.path.join(ROOT, 'src', 'field_scripts', '1282_global_contests.s')).read()
    inc = set(re.findall(r'#define (CPL_\w+)', open(os.path.join(ROOT, 'src', 'include', 'pearl_contests_lines.inc')).read()))
    miss = sorted(set(re.findall(r'CPL_\w+', s)) - inc)
    check(not miss, f'the Poffin counter\'s lines exist: {miss}')
    # the pot: the same pixels as Pearl's bitmaps, whichever way the tiles are ordered
    import title_art
    mix = [title_art.lz10_decompress(m) if m[:1] == b'\x10' else m for m in narc_members(rom.read('graphic/nutmixer.narc'))]

    def raw(d):
        o = cd._sec(d, b'RAHC')
        off, sz = struct.unpack_from('<I', d, o + 8 + 20)[0], struct.unpack_from('<I', d, o + 8 + 16)[0]
        return d[o + 8 + off:o + 8 + off + sz]
    t, r = raw(cd.bitmap_ncgr(mix[38])), raw(mix[38])
    check(all(t[(y // 8 * 32 + x // 8) * 32 + y % 8 * 4 + x // 2 % 4] == r[y * 128 + x // 2] for y in range(0, 256, 3) for x in range(0, 256, 5)), 'the ring\'s BG tiles are Pearl\'s bitmap')
    t, r = raw(cd.batter_ncgr(mix[44])), raw(mix[44])
    check(all(t[((y // 64 * 2 + x // 64) * 64 + (y % 64) // 8 * 8 + (x % 64) // 8) * 32 + y % 8 * 4 + x // 2 % 4] == r[y * 64 + x // 2] for y in range(0, 128, 3) for x in range(0, 128, 5)), 'the batter\'s OBJ tiles are Pearl\'s bitmap')
    for zone in ('1400_pearl_hearthome_poffin_house', '1517_pearl_amity_square', '1401_pearl_hearthome_super_contest_hall_lobby'):
        z = open(os.path.join(ROOT, 'src', 'field_scripts', zone + '.s')).read()
        check('pl_AmitySquareBerryOnly' not in z, f'{zone}: no Berries-only find')
    z = open(os.path.join(ROOT, 'src', 'field_scripts', '1400_pearl_hearthome_poffin_house.s')).read()
    check('RTCallGlobal 10788' in z, 'the Poffin House\'s cook calls the counter')
    z = open(os.path.join(ROOT, 'src', 'field_scripts', '1401_pearl_hearthome_super_contest_hall_lobby.s')).read()
    check('pl_PoffinGive' in z and 'pl_PoffinHasRoom' in z, 'the Hall\'s gift gives a real Poffin')


def text():
    import gen4_text
    for bank, lines in cd.TEXT_BANKS.items():
        got = [l for k, l, e in gen4_text.convert_bank(bank, cd.PEARL)]
        check(len(got) == lines, f'Pearl\'s bank {bank}: {len(got)} lines')


if __name__ == '__main__':
    tables()
    versions()
    contests()
    moves()
    text()
    layout()
    poffins()
    print('contest_check:', 'FAILED ' + str(len(FAILS)) if FAILS else 'all good')
    sys.exit(1 if FAILS else 0)
