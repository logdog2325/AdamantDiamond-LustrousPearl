"""Pearl's and Diamond's Underground digging weights, as data (notes/DIAMOND.md 2.2 G). Digging is not built (notes/UNDERGROUND.md),
so nothing in a build reads data/underground_digging.json yet; it keeps Diamond's side, with its version tag, for when it is.

    python3 underground_digging.py       -> ../data/underground_digging.json (from both dumps; checks they hold the same table)

Overlay 18's table at 0x02250B30, 85 entries of 20 bytes: the object at +0xE (text bank 569's line, read here), its shape bytes at
+0xC, +0xD, and four u16 weights: +4 Diamond before the National Pokédex, +6 Pearl before, +8 Diamond after, +0xA Pearl after
(ov18_0223AE88 reads those by GAME_VERSION).
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom  # noqa: E402

OVERLAY, TABLE, ENTRIES, SIZE = 18, 0x02250B30, 85, 20
OUT = os.path.join(ROOT, 'data', 'underground_digging.json')


def table(path):
    rom = Rom(path)
    y9 = struct.unpack_from('<I', rom.data, 0x50)[0]
    _, ram, _, _, _, _, fid, flags = struct.unpack_from('<8I', rom.data, y9 + 32 * OVERLAY)
    assert not flags >> 24 & 1, 'overlay 18 is compressed'
    d = rom.read(fid)
    return d[TABLE - ram:TABLE - ram + ENTRIES * SIZE]


def weights(row, column):
    """A row's [before the National Pokédex, after it] in a BDSP column ('sp' Pearl's, 'bd' Diamond's, 'both' Platinum's). 'both': the two
    games' means, so neither version's stones, spheres or fossil is favoured (the user 2026-11-01, notes/PLATINUM.md section 5); a fossil
    only one game has keeps half its weight there, so the two fossils together come up as often as one does in either game."""
    w = row['weights']
    if column == 'both':
        return [(a + b + 1) // 2 for a, b in zip(w['pearl'], w['diamond'])]
    return w['pearl' if column == 'sp' else 'diamond']


def main():
    import gen4_text
    d, p = (table(os.path.join(ROOT, 'roms', f'{v}.nds')) for v in ('diamond', 'pearl'))
    assert d == p, 'the two dumps hold different tables'
    names = {i: line for i, line, _ in gen4_text.convert_bank(569, os.path.join(ROOT, 'roms', 'pearl.nds'))}
    rows = []
    for k in range(ENTRIES):
        e = d[k * SIZE:(k + 1) * SIZE]
        db, pb, da, pa = struct.unpack_from('<4H', e, 4)
        rows.append(dict(object=e[0xE], name=names.get(e[0xE]), shape=[e[0xC], e[0xD]], weights={'diamond': [db, da], 'pearl': [pb, pa]}))
    json.dump({'_doc': __doc__.split('\n\n')[0] + ' weights: [before the National Pokédex, after it].', 'objects': rows},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    open(OUT, 'a').write('\n')
    diff = [r for r in rows if r['weights']['diamond'] != r['weights']['pearl']]
    print(f'{len(rows)} objects, {len(diff)} with other weights in the two games -> {OUT}')
    for r in rows:
        if r['name'] and 'Fossil' in r['name'] and r['name'][:5] in ('Armor', 'Skull'):
            print(r['name'], r['weights'])


if __name__ == '__main__':
    main()
