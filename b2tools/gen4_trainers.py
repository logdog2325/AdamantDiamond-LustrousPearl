"""Phase 1 reader: a Gen 4 game's trainers from the dump, named with pokediamond's constants, checked against the decomp's.

    python3 gen4_trainers.py [ROM] [OUT]        defaults: the version's world dump, work/<world>/trainers.json (Pearl and Diamond:
                                                roms/pearl.nds, work/pearl; PEARL_VERSION=platinum: roms/platinum.nds, work/platinum)

Layouts from pokediamond (files/poketool/trainer/trdata.json.txt, trpoke.json.txt, include/trainer_data.h):
trdata.narc: u8 type, u8 class, u8 unk2, u8 party count, u16 items[4], u32 unkC (AI flags), u32 doubleBattle;
trpoke.narc: per Pokémon u16 difficulty, u16 level, u16 species [, u16 item] [, u16 moves[4]]; Platinum adds u16 ball seal.
Names: poketool/trainer/trname (msg bank) is not read here; pokediamond's trdata.json carries them, and in Platinum
res/trainers/data/NAME.json (by the order of generated/trainers.txt), read in as "name" here.
Platinum's classes: its first 98 are Pearl's by number, spelled Pearl's way here; 98-104 (MAID, HALL_MATRON, ...) are new.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom, narc_members  # noqa: E402
from gen4_extract import constants, DIAMOND, PLATINUM  # noqa: E402
import version  # noqa: E402

TYPES = ['TRTYPE_MON', 'TRTYPE_MON_MOVES', 'TRTYPE_MON_ITEM', 'TRTYPE_MON_ITEM_MOVES']


def platinum_rows():
    """[res/trainers/data row, with its id] of Platinum's trainers, by number (0 is the empty record)."""
    out = [None]
    for l in [l for l in open(os.path.join(PLATINUM, 'generated', 'trainers.txt')) if l.startswith('TRAINER_')][1:]:
        key = l.strip()[len('TRAINER_'):].lower()
        out.append(dict(json.load(open(os.path.join(PLATINUM, 'res', 'trainers', 'data', key + '.json')))))
    return out


def platinum_classes(classes):
    """Class constants by number: Pearl's spelling where Pearl has the number, Platinum's after that."""
    names = [l.strip() for l in open(os.path.join(PLATINUM, 'generated', 'trainer_classes.txt')) if l.strip()]
    return {i: classes.get(i, n) for i, n in enumerate(names)}


def main():
    rom = Rom(sys.argv[1] if len(sys.argv) > 1 else version.WORLD_DUMP)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(version.WORLD_WORK, 'trainers.json')
    inc = os.path.join(DIAMOND, 'include', 'constants')
    species = constants(os.path.join(inc, 'species.h'), 'SPECIES_')
    items = constants(os.path.join(inc, 'items.h'), 'ITEM_')
    moves = constants(os.path.join(inc, 'moves.h'), 'MOVE_')
    classes = constants(os.path.join(inc, 'trainer_classes.h'), 'TRAINER_CLASS_')
    if version.PLATINUM:
        classes = platinum_classes(classes)
    seal = 2 if version.PLATINUM else 0
    data = narc_members(rom.read('poketool/trainer/trdata.narc'))
    pokes = narc_members(rom.read('poketool/trainer/trpoke.narc'))
    trainers = []
    for i, (d, p) in enumerate(zip(data, pokes)):
        t, cls, unk2, n = d[:4]
        its = struct.unpack_from('<4H', d, 4)
        ai, double = struct.unpack_from('<2I', d, 12)
        has_item, has_moves = t in (2, 3), t in (1, 3)
        size = 6 + 2 * has_item + 8 * has_moves + seal
        party = []
        for k in range(n):
            f = struct.unpack_from(f'<{size // 2}H', p, k * size)
            mon = {'difficulty': f[0], 'level': f[1], 'species': species.get(f[2] & 0x3ff, f[2]), 'form': f[2] >> 10}
            j = 3
            if has_item:
                mon['item'] = items.get(f[j], f[j]); j += 1
            if has_moves:
                mon['moves'] = [moves.get(m, m) for m in f[j:j + 4]]; j += 4
            if seal:
                mon['ball_seal'] = f[j]
            party.append(mon)
        trainers.append({'index': i, 'type': TYPES[t], 'class': classes.get(cls, cls), 'unk2': unk2,
                         'items': [items.get(x, x) for x in its if x], 'ai': ai, 'double': double, 'party': party})
    if version.PLATINUM:
        check_platinum(trainers, platinum_rows(), out)
        return
    json.dump(trainers, open(out, 'w'), indent=1)
    # compare with pokediamond's JSON (Diamond and Pearl share one trainer file there)
    ref = {t['index']: t for t in json.load(open(os.path.join(DIAMOND, 'files', 'poketool', 'trainer',
                                                                'trdata.json')))['trdata']}
    diff = []
    for t in trainers:
        r = ref.get(t['index'])
        if r is None:
            diff.append((t['index'], 'missing in pokediamond'))
            continue
        a = [(m['species'], m['level']) for m in t['party']]
        b = [(m['species'], m['level']) for m in r['party']]
        if a != b or t['class'] != r['class']:
            diff.append((t['index'], r['name'], a, b))
    print(f'{len(trainers)} trainers -> {out}; differences from pokediamond trdata.json: {len(diff)}')
    for x in diff[:10]:
        print('  ', x)


def check_platinum(trainers, rows, out):
    """Names from res/trainers/data, and every party and its numbers compared with that file."""
    diff = []
    for t in trainers[1:]:
        r = rows[t['index']]
        t['name'] = r['name']
        a = [(m['species'].replace('SPECIES_', ''), m['level'], m['form']) for m in t['party']]
        b = [(m['species'].replace('SPECIES_', ''), m['level'], m['form']) for m in r['party']]
        if a != b or bool(t['double']) != bool(r['double_battle']):
            diff.append((t['index'], r['name'], a, b))
    json.dump(trainers, open(out, 'w'), indent=1)
    print(f'{len(trainers)} trainers -> {out}; differences from pokeplatinum res/trainers/data: {len(diff)}')
    for x in diff[:10]:
        print('  ', x)


if __name__ == '__main__':
    main()
