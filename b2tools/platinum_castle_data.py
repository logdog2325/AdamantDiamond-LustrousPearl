"""Platinum's Battle Castle data, checked against the dump and Black 2 (notes/PLATINUM_FRONTIER.md "The Battle Castle").

    python3 b2tools/platinum_castle_data.py check

The Castle's rules (src/pokebw2/src/pearlb2/plat_castle/castle_rules.c) keep its tables as the decomp's source has them; this
checks each one is the dump's own (its bytes found in roms/platinum.nds: overlay 104 and the Castle's screens' overlay are stored
uncompressed) and that castle_rules.c has the same numbers:
- sBattleCastleOpponentPools (battle_castle_helpers.c): the Trainers each round draws from, normal and the 7th;
- sBPPerRoundSolo, sBPPerRoundWifi (battle_castle.c);
- the self screen's (self_app.c): sItemsForRent, sItemPrices, sBerriesForRent, sBerryPrices, sItemsAvailableByRank,
  sBerriesAvailableByRank, sHealingCosts, sRankUpCosts.
The opponent screen's costs are constants in its code (CP_COST_*, opponent_app.c) and the pass's 50 is in the scene's script:
the harness runs that code itself (b2tools/platinum_castle_host).
And that every item the Castle names (the rentals, the Max Potion and Max Elixir the heal uses) has the same number in Black 2
(the decomp's generated/items.txt), so the rules' ids are Black 2's too.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import platinum_frontier_data as pfd  # noqa: E402

PLATINUM = pfd.PLATINUM
B2 = os.path.join(ROOT, 'external', 'pokebw2')
OURS = os.path.join(ROOT, 'src', 'pokebw2', 'src', 'pearlb2', 'plat_castle', 'castle_rules.c')


def _consts(path):
    return {n.split('=')[0].strip(): i for i, n in enumerate(l.strip() for l in open(path) if l.strip() and not l.startswith('#'))}


def _table(path, name):
    """The numbers of a C table in a source file (constants resolved: items, the Frontier Trainers, NELEMS of a table before)."""
    text = open(path).read()
    m = re.search(r'(?:static )?const u(?:8|16) ' + name + r'\[[^=]*=\s*\{(.*?)\n?\};', text, re.S)
    assert m, (path, name)
    items = _consts(os.path.join(PLATINUM, 'generated', 'items.txt'))
    order = [l.strip() for l in open(os.path.join(PLATINUM, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    trainers = {f'FRONTIER_TRAINER_{n.upper()}': i for i, n in enumerate(order)}
    body = re.sub(r'/\*.*?\*/', '', m.group(1))
    out = []
    for tok in re.findall(r'[\w()]+', body):
        if tok.isdigit():
            out.append(int(tok))
        elif tok in items:
            out.append(items[tok])
        elif tok in trainers:
            out.append(trainers[tok])
        elif tok.startswith('NELEMS('):
            out.append(len(_table(path, tok[7:-1])))
    return out


def _ours(name):
    """castle_rules.c's table (its constants are numbers, or its own TRAINER_ defines)."""
    text = open(OURS).read()
    defs = {n: int(v) for n, v in re.findall(r'#define (TRAINER_\w+) (\d+)', text)}
    if name == 'sOpponentPools':
        m = re.search(r'\} sOpponentPools\[\] = \{(.*?)\n\};', text, re.S)
        return [defs[t] for t in re.findall(r'TRAINER_\w+', m.group(1))]
    m = re.search(r'static const u(?:8|16) ' + name + r'\[[^=]*=\s*\{(.*?)\};', text, re.S)
    assert m, name
    body = re.sub(r'/\*.*?\*/', '', m.group(1))
    out = []
    for tok in re.findall(r'[\w()]+', body):
        if tok.isdigit():
            out.append(int(tok))
        elif tok.startswith('NELEMS('):
            out.append(len(_ours(tok[7:-1])))
    return out


TABLES = (   # (name in the decomp, its file, ours, struct format)
    ('sBattleCastleOpponentPools', 'src/overlay104/battle_castle_helpers.c', 'sOpponentPools', '<H'),
    ('sBPPerRoundSolo', 'src/overlay104/battle_castle.c', 'sBPPerRoundSolo', '<B'),
    ('sBPPerRoundWifi', 'src/overlay104/battle_castle.c', 'sBPPerRoundWifi', '<B'),
    ('sItemsForRent', 'src/applications/frontier/battle_castle/self_app.c', 'sItemsForRent', '<H'),
    ('sItemPrices', 'src/applications/frontier/battle_castle/self_app.c', 'sItemPrices', '<H'),
    ('sBerriesForRent', 'src/applications/frontier/battle_castle/self_app.c', 'sBerriesForRent', '<H'),
    ('sBerryPrices', 'src/applications/frontier/battle_castle/self_app.c', 'sBerryPrices', '<H'),
    ('sItemsAvailableByRank', 'src/applications/frontier/battle_castle/self_app.c', 'sItemsAvailableByRank', '<H'),
    ('sBerriesAvailableByRank', 'src/applications/frontier/battle_castle/self_app.c', 'sBerriesAvailableByRank', '<H'),
    ('sHealingCosts', 'src/applications/frontier/battle_castle/self_app.c', 'sHealingCosts', '<H'),
    ('sRankUpCosts', 'src/applications/frontier/battle_castle/self_app.c', 'sRankUpCosts', '<H'),
)


def check(verbose=True):
    problems = []
    data = pfd.rom().data
    for name, path, ours, fmt in TABLES:
        if name == 'sBattleCastleOpponentPools':
            text = open(os.path.join(PLATINUM, path)).read()
            m = re.search(r'\} sBattleCastleOpponentPools\[\] = \{(.*?)\n\};', text, re.S)
            order = [l.strip() for l in open(os.path.join(PLATINUM, 'res', 'trainers', 'frontier', 'frontier_trainers.order'))
                     if l.strip()]
            trainers = {f'FRONTIER_TRAINER_{n.upper()}': i for i, n in enumerate(order)}
            values = [trainers[t] for t in re.findall(r'FRONTIER_TRAINER_\w+', m.group(1))]
        else:
            values = _table(os.path.join(PLATINUM, path), name)
        blob = b''.join(struct.pack(fmt, v) for v in values)
        at = data.find(blob)
        mine = _ours(ours)
        if at < 0:
            problems.append(f'{name}: not in the dump')
        if mine != values:
            problems.append(f'{name}: castle_rules.c has {mine}, the decomp {values}')
        if verbose:
            print(f'{name}: {len(values)} numbers, in the dump at {at:#x}, castle_rules.c {"the same" if mine == values else "DIFFERENT"}')
    plat = [l.strip() for l in open(os.path.join(PLATINUM, 'generated', 'items.txt')) if l.strip() and not l.startswith('#')]
    b2 = [l.strip() for l in open(os.path.join(B2, 'generated', 'items.txt')) if l.strip() and not l.startswith('#')]
    norm = lambda s: s.split('=')[0].strip().replace('ITEM_', '').replace('_', '').lower()
    ids = _ours('sItemsForRent') + _ours('sBerriesForRent') + [24, 41]     # (+ the Max Potion and Max Elixir)
    bad = [(i, plat[i], b2[i]) for i in ids if norm(plat[i]) != norm(b2[i])]
    problems += [f'item {i}: Platinum {p}, Black 2 {b}' for i, p, b in bad]
    if verbose:
        print(f'{len(ids)} items: {len(ids) - len(bad)} the same number in Black 2')
    return problems


def main(argv):
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
