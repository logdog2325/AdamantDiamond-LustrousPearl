"""Platinum's own system text where it differs from Pearl's (notes/PORT_AUDIT.md, "Step 2: dialogue"), as data rows.

    PEARL_VERSION=platinum python3 b2tools/platinum_text.py     -> data/text_overrides/platinum/town_map.json

- The Town Map's place descriptions: Pearl's lines of bank 556 are installed after Black 2's own (data/text_overrides/
  town_map.json, written by patches/town_map.py --text); 9 of Platinum's differ, 6 of them on lines a place shows
  (Route 210's fog, Veilstone and Fight Area as town and city, the Oreburgh Mine, the Battle Frontier's two), and one
  more line loses its last line break (gen4_text TRIM_LAST_NEWLINE). This writes Platinum's lines for those labels into
  data/text_overrides/platinum/, which patches/sinnoh_names.py applies over the shared file in a Platinum build only.
The rest of Platinum's system text needs no row (b2tools/text_check.py checks it): its items, Pokédex categories and
Trainer class names are Black 2's or Pearl's already, its place names come from its own dump (patches/sinnoh_names.py
place_names), and its Trainers' names and messages from its own trainer files (patches/pearl_trainers.py).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402

TOWN_MAP_OUT = os.path.join(ROOT, 'data', 'text_overrides', 'platinum', 'town_map.json')


def town_map_rows():
    """{label: Platinum's line} for the Town Map description lines Platinum changed (Pearl's own line otherwise)."""
    import gen4_text, town_map
    plat = gen4_text.bank(556)
    shared = json.load(open(os.path.join(ROOT, 'data', 'text_overrides', 'town_map.json'), encoding='utf-8'))
    shared = shared[town_map.TOWNMAP_TEXT]
    out = {}
    for n in town_map.desc_lines():
        label = f'TownMap_Text_Pearl{n:03d}'
        assert '+' + label in shared, f'{label} is not in data/text_overrides/town_map.json'
        line = gen4_text.b2_line(plat[n])
        if line != shared['+' + label]:         # (Platinum's words, or Platinum's layout: no last line break, gen4_text)
            out[label] = line
    return out


def write_town_map():
    import town_map
    rows = town_map_rows()
    doc = ("Platinum's Town Map descriptions where its words differ from Pearl's (b2tools/platinum_text.py from the user's "
           "Platinum dump, bank 556's slot, through gen4_text): they replace those lines of data/text_overrides/town_map.json "
           "in a Platinum build only (patches/sinnoh_names.py text_overrides). Regenerate: PEARL_VERSION=platinum python3 "
           "b2tools/platinum_text.py")
    os.makedirs(os.path.dirname(TOWN_MAP_OUT), exist_ok=True)
    json.dump({'_doc': doc, town_map.TOWNMAP_TEXT: rows}, open(TOWN_MAP_OUT, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1)
    return f'{len(rows)} Town Map lines -> {os.path.relpath(TOWN_MAP_OUT, ROOT)}'


if __name__ == '__main__':
    assert version.PLATINUM, 'run with PEARL_VERSION=platinum'
    print(write_town_map())
