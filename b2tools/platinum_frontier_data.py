"""Platinum's Battle Frontier data, read from the dump and checked against the decomp (notes/PLATINUM_FRONTIER.md "Data").

    python3 b2tools/platinum_frontier_data.py check          every reader against the decomp; prints a summary
    python3 b2tools/platinum_frontier_data.py --blob FILE    the Tower's rules tables for the C (tower_rules.c), as the build puts them

Readers (all from roms/platinum.nds; the decomp is the check):
- trainers(): battle/b_pl_tower/pl_btdtr.narc, 315 Frontier Trainers: class, the sets they draw from (res/trainers/frontier/data).
  0-299 the Tower's and the facilities' common Trainers, 300-304 the Tower's partners (Cheryl, Mira, Riley, Marley, Buck),
  305-314 the Brains, silver and gold: Palmer, Argenta, Thorton, Dahlia, Darach.
- sets(): pl_btdpm.narc, 951 sets of 16 bytes (FrontierPokemonBase: species, 4 moves, EV flags, nature, item, form).
- names() and lines(): the Trainers' names (bank 21) and their three lines each (bank 614).
- tower_ranges(): sBattleTowerTrainerRangesPerRoom and sBattleTowerBossTrainerRangesPerRoom (src/unk_0204AEE8.c), the Trainers each
  room draws from, the seventh from the second table; Palmer ends rooms 3 and 7 of the singles (305, 306).
- class_objects(): sTrainerClassToObjectID, a class's field sprite.
- marts(): the Exchange Service Corner's two lists (ScrCmd_PokeMartFrontier) and their BP prices (overlay 7's itemToBpPrice).
- tower_ivs(): BattleTower_GetIVsFromTrainerID's steps.
Each table found in the dump's code by its bytes, the bytes made from the decomp's source: a found table is the dump's own.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom, narc_members  # noqa: E402

PLATINUM = os.path.join(ROOT, 'external', 'pokeplatinum')
DUMP = os.path.join(ROOT, 'roms', 'platinum.nds')
FRONTIER = os.path.join(PLATINUM, 'res', 'trainers', 'frontier')
TRAINERS, SETS = 'battle/b_pl_tower/pl_btdtr.narc', 'battle/b_pl_tower/pl_btdpm.narc'
NAME_BANK, LINE_BANK = 21, 614           # TEXT_BANK_FRONTIER_TRAINER_NAMES, _MESSAGES (Platinum's own numbers)
TRAINER_COUNT, SET_COUNT = 315, 951
PARTNER_FIRST, PALMER_SILVER, PALMER_GOLD = 300, 305, 306
BRAINS = {'tower': (305, 306), 'hall': (307, 308), 'factory': (309, 310), 'arcade': (311, 312), 'castle': (313, 314)}
_ROM = None


def rom():
    global _ROM
    if _ROM is None:
        _ROM = Rom(DUMP)
    return _ROM


def _list(name):
    return [l.strip() for l in open(os.path.join(PLATINUM, 'generated', name)) if l.strip()]


def consts(name):
    """{constant: number} of a generated list (species, moves, items, natures, trainer_classes)."""
    return {n.split('=')[0].strip(): i for i, n in enumerate(_list(name + '.txt'))}


def trainer_order():
    return [l.strip() for l in open(os.path.join(FRONTIER, 'frontier_trainers.order')) if l.strip()]


def set_order():
    return [l.strip() for l in open(os.path.join(FRONTIER, 'frontier_pokemon.order')) if l.strip()]


def trainers():
    """[(class, [set ids])] by Trainer id, from the dump. The count field leaves out the list's last entry when it is set 0
    (none_1, the decomp's padding row: frontierproc writes it but doesn't count it)."""
    out = []
    for t in narc_members(rom().read(TRAINERS)):
        cls, n = struct.unpack_from('<HH', t)
        out.append((cls, list(struct.unpack_from(f'<{n}H', t, 4))))
    return out


def trainer_files():
    """[(class, count, every u16 after the count)]: the files as they are."""
    return [struct.unpack_from('<HH', t) + (list(struct.unpack_from(f'<{(len(t) - 4) // 2}H', t, 4)),)
            for t in narc_members(rom().read(TRAINERS))]


def sets():
    """[{species, moves, evs, nature, item, form}] by set id, from the dump."""
    out = []
    for s in narc_members(rom().read(SETS)):
        sp, m0, m1, m2, m3, ev, nat, item, form = struct.unpack('<5HBBHH', s)
        out.append({'species': sp, 'moves': [m0, m1, m2, m3], 'evs': ev, 'nature': nat, 'item': item, 'form': form})
    return out


def bank_slot(n):
    """The tools' number for Platinum's bank n: its own under PEARL_VERSION=platinum's slots (gen4_text reads a Platinum dump's
    banks by Pearl's numbers then: version.slotted), else n."""
    import version
    return version.of_slot('banks')[n] if version.PLATINUM else n


def names():
    import gen4_text
    return gen4_text.bank_text(bank_slot(NAME_BANK), DUMP)


def lines():
    import gen4_text
    return gen4_text.bank_text(bank_slot(LINE_BANK), DUMP)


# ---------------------------------------------------------------- tables in the code
def _find(blob):
    """Every offset of `blob` in the dump (its code modules are stored uncompressed: platinum_party_data finds its tables the same way)."""
    d, out, at = rom().data, [], 0
    while True:
        at = d.find(blob, at)
        if at < 0:
            return out
        out.append(f'{at:#x}')
        at += 1


def _source(path):
    return open(os.path.join(PLATINUM, path)).read()


def tower_ranges():
    """{'normal': [(first, last)] x 8, 'boss': [(first, last)] x 8}: the Trainer ids, from the decomp's source."""
    text = _source('src/unk_0204AEE8.c')
    order = {('FRONTIER_TRAINER_' + n.upper()): i for i, n in enumerate(trainer_order())}
    out = {}
    for key, name in (('normal', 'sBattleTowerTrainerRangesPerRoom'), ('boss', 'sBattleTowerBossTrainerRangesPerRoom')):
        body = re.search(name + r'\[\]\[2\]\s*=\s*\{(.*?)\};', text, re.S).group(1)
        out[key] = [(order[a], order[b]) for a, b in re.findall(r'\{\s*(\w+),\s*(\w+)\s*\}', body)]
    return out


def tower_ranges_bytes(r=None):
    r = r or tower_ranges()
    return b''.join(struct.pack('<HH', a, b) for a, b in r['normal']) + \
        b''.join(struct.pack('<HH', a, b) for a, b in r['boss'])


def tower_ivs():
    """[(below this Trainer id, IV)] then the IV for the rest (BattleTower_GetIVsFromTrainerID)."""
    text = _source('src/unk_02049D08.c')
    body = re.search(r'u8 BattleTower_GetIVsFromTrainerID\(u16 battleTowerID\)\s*\{(.*?)\n\}', text, re.S).group(1)
    steps = [(int(a), int(b)) for a, b in re.findall(r'battleTowerID < (\d+)\) \{\s*ivs = MAX_IVS_SINGLE_STAT / 8 \* (\d+);', body)]
    return [(lim, 31 // 8 * k) for lim, k in steps], 31


def class_objects():
    """[(Platinum class, Platinum object gfx)] of sTrainerClassToObjectID, in order."""
    text = _source('src/unk_0204AEE8.c')
    body = re.search(r'sTrainerClassToObjectID\[\]\[2\]\s*=\s*\{(.*?)\};', text, re.S).group(1)
    cls = consts('trainer_classes')
    gfx = {n: i for i, n in enumerate(_list('object_events_gfx.txt'))}
    return [(cls[a], gfx[b]) for a, b in re.findall(r'\{\s*(\w+),\s*(\w+)\s*\}', body)]


def marts():
    """{'right': [items], 'left': [items]}, and {item: BP price} (Platinum's item numbers)."""
    text = _source('src/scrcmd.c')
    items = consts('items')
    out = {}
    for key, name in (('right', 'BattleFrontierRightExchangeServiceCorner'), ('left', 'BattleFrontierLeftExchangeServiceCorner')):
        body = re.search(r'static const u16 ' + name + r'\[\]\s*=\s*\{(.*?)\};', text, re.S).group(1)
        out[key] = [items[n] for n in re.findall(r'\b(ITEM_\w+)', body) if n in items]
    menu = _source('src/overlay007/shop_menu.c')
    body = re.search(r'itemToBpPrice\[\]\[2\]\s*=\s*\{(.*?)\};', menu, re.S).group(1)
    prices = {items[a]: int(b) for a, b in re.findall(r'\{\s*(ITEM_\w+),\s*(\d+)\s*\}', body)}
    return out, prices


# ---------------------------------------------------------------- the check
def check(verbose=True):
    problems = []
    tr, st = trainers(), sets()
    if (len(tr), len(st)) != (TRAINER_COUNT, SET_COUNT):
        problems.append(f'counts: {len(tr)} trainers, {len(st)} sets')
    cls, sp, mv, it, nat = consts('trainer_classes'), consts('species'), consts('moves'), consts('items'), consts('natures')
    sorder = set_order()
    for i, (stem, (c, n, ids)) in enumerate(zip(trainer_order(), trainer_files())):
        j = json.load(open(os.path.join(FRONTIER, 'data', stem + '.json')))
        want = [sorder.index(s) for s in j['availableSets']]
        counted = len(want) - (1 if want and want[-1] == 0 else 0)
        if c != cls[j['class']] or ids[:len(want)] != want or n != counted:
            problems.append(f'trainer {i} {stem}: dump class {c}, {n} counted of {ids}; decomp {cls[j["class"]]}, {want}')
    evkeys = ('hp', 'attack', 'defense', 'speed', 'special_attack', 'special_defense')
    for i, stem in enumerate(sorder):
        j = json.load(open(os.path.join(FRONTIER, 'pokemon', stem + '.json')))
        want = {'species': sp[j['species']], 'moves': [mv[m] for m in j['moves']],
                'evs': sum(1 << k for k, e in enumerate(evkeys) if j['evFlags'][e]), 'nature': nat[j['nature']],
                'item': it[j['item']], 'form': j['form']}
        if st[i] != want:
            problems.append(f'set {i} {stem}: dump {st[i]} decomp {want}')
    nm, ln = names(), lines()
    if len(nm) != TRAINER_COUNT or len(ln) != 3 * TRAINER_COUNT:
        problems.append(f'banks: {len(nm)} names, {len(ln)} lines')
    for i, stem in enumerate(trainer_order()):
        j = json.load(open(os.path.join(FRONTIER, 'data', stem + '.json')))
        if nm[i].strip() != j['name']:
            problems.append(f'name {i}: dump {nm[i]!r}, decomp {j["name"]!r}')
            break
    # the code's tables, found by their bytes
    found = {}
    rr = tower_ranges()
    found['tower ranges'] = _find(tower_ranges_bytes(rr))
    co = class_objects()
    found['class -> sprite'] = _find(b''.join(struct.pack('<HH', a, b) for a, b in co))
    m, prices = marts()
    found['mart right'] = _find(b''.join(struct.pack('<H', x) for x in m['right']) + struct.pack('<H', 0xFFFF))
    found['mart left'] = _find(b''.join(struct.pack('<H', x) for x in m['left']) + struct.pack('<H', 0xFFFF))
    found['BP prices'] = _find(b''.join(struct.pack('<HH', a, b) for a, b in prices.items()))
    for k, hits in found.items():
        if not hits:
            problems.append(f'{k}: found {len(hits)} times in the dump\'s code ({hits[:3]})')
    if set(m['right']) | set(m['left']) - set(prices):
        missing = (set(m['right']) | set(m['left'])) - set(prices)
        if missing:
            problems.append(f'marts: {len(missing)} items without a BP price')
    if verbose:
        print(f'{len(tr)} Trainers and {len(st)} sets in the dump = the decomp\'s res/trainers/frontier, names and lines '
              f'({len(nm)}, {len(ln)})')
        print('Tower rooms (Trainer ids), the 7th:', ', '.join(f'{a}-{b}/{c}-{d}' for (a, b), (c, d)
                                                             in zip(rr['normal'], rr['boss'])))
        for k, hits in found.items():
            print(f'  {k}: in the dump at {hits}')
        print(f'Exchange Service Corner: right {len(m["right"])} TMs, left {len(m["left"])} items; '
              f'{len(prices)} BP prices; IVs {tower_ivs()}')
    return problems


# ---------------------------------------------------------------- the C's tables
BLOB_MAGIC = b'PTWR'


def blob():
    """The Tower's rules for tower_rules.c (include/pearlb2/plat_frontier.h PearlB2TowerRules): magic, the 8 normal ranges, the
    8 seventh-Trainer ranges, Palmer's two ids, the partners' first id, the IV steps (8 limits, 8 IVs, the rest's IV)."""
    rr = tower_ranges()
    steps, rest = tower_ivs()
    assert len(steps) == 7, steps
    limits = [a for a, b in steps] + [0xFFFF]
    ivs = [b for a, b in steps] + [rest]
    return BLOB_MAGIC + tower_ranges_bytes(rr) + struct.pack('<HHH', PALMER_SILVER, PALMER_GOLD, PARTNER_FIRST) + \
        struct.pack('<H', 0) + struct.pack('<8H', *limits) + bytes(ivs)


def sets_blob():
    """The harness's copy of the Trainers and sets (b2tools/platinum_frontier_host/sim.c): u32 Trainer count, u32 set count; each
    Trainer's file as u16 length + its u16s (class, count, set ids, as in the dump); each set's 16 bytes."""
    tr = narc_members(rom().read(TRAINERS))
    st = narc_members(rom().read(SETS))
    out = struct.pack('<II', len(tr), len(st))
    for t in tr:
        out += struct.pack('<H', len(t) // 2) + t[:len(t) // 2 * 2]
    return out + b''.join(st)


def main(argv):
    if argv[:1] == ['--sets']:
        open(argv[1], 'wb').write(sets_blob())
        return 0
    if argv[:1] == ['--blob']:
        open(argv[1], 'wb').write(blob())
        print(f'{argv[1]}: {len(blob())} bytes')
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
