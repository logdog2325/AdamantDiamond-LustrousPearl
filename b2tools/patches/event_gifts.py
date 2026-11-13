"""The deliveryman's event Pokémon (the user, 2026-11-09; notes/POSTGAME_DEX.md): Mew, Celebi, Jirachi and Deoxys after his
other gifts, copies of real Gen 4-era events (data/event_gifts.json), in every version (version.EVENT_GIFTS).

The decomp's extension 0xA9 (src/pearlb2/resident/leftovers.c EventGift_Give: index, var result) makes the index-th card's
Pokémon the way Black 2 makes a Mystery Gift Pokémon (ov012 CreateMysteryGiftPokemon: the fateful mark, the met data) and
puts it in the party; src/include/pearl_story.inc pl_DeliveryGive calls it for gifts PL_DELIVERY_EVENTS.. (Pearl and Diamond
7-10, Platinum 8-11). This patch writes the cards: gPearlB2EventGifts = {u16 count, u16 0, MysteryGift cards[count]}, each
0xCC bytes as patches/platinum_regigigas.py's card (MysteryGift, include/save/mystery_gift.h, its MysteryGiftPokemon at the
start), in the resident pool. No table: the command gives nothing (result 0).

    python3 b2tools/patches/event_gifts.py      print the cards' fields
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402

DATA = os.path.join(ROOT, 'data', 'event_gifts.json')
GIFT_SIZE, KIND_AT = 0xCC, 0xB3
GEN = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'include', 'generated', 'constants')
# pearl_story.inc pl_DeliveryEventSpecies names the gifts in this order: the data must be the same
SCRIPT_ORDER = ('SPECIES_MEW', 'SPECIES_CELEBI', 'SPECIES_JIRACHI', 'SPECIES_DEOXYS')


def _consts(name, prefix):
    out = {}
    for line in open(os.path.join(GEN, name)):
        m = re.match(rf'#define ({prefix}\w+) (\d+)\b', line)
        if m:
            out.setdefault(m.group(1), int(m.group(2)))
    return out


def gifts():
    d = json.load(open(DATA, encoding='utf-8'))
    g = d['gifts']
    names = tuple(x['species'] for x in g)
    assert names == SCRIPT_ORDER, f'event_gifts.json: {names}, the script names {SCRIPT_ORDER}'
    assert tuple(n[8:] for n in names) == version.EVENT_GIFTS, f'version.EVENT_GIFTS {version.EVENT_GIFTS}'
    return g, d['ribbon_bits']


def card(gift, bits):
    """The 0xCC-byte card, its date left 0 (the C writes the day it is received)."""
    species = _consts('species.h', 'SPECIES_')
    items = _consts('items.h', 'ITEM_')
    moves = _consts('moves.h', 'MOVE_')
    ribbons = 0
    for r in gift['ribbons']:
        ribbons |= 1 << bits[r]
    g = bytearray(GIFT_SIZE)
    struct.pack_into('<IIIHHH4HHBB', g, 0, gift['id'], version.MET_GAME, 0, ribbons, items[gift['ball']],
                     items[gift['item']] if gift['item'] else 0, *[moves[m] for m in gift['moves']],
                     species[gift['species']], 0, 0)
    struct.pack_into('<11H', g, 0x1E, 0xFFFF, *([0] * 10))       # no nickname: the species' name (the terminator first)
    struct.pack_into('<BBBB', g, 0x34, 0xFF, 0xFF, 0, 0)          # nature, gender at random; ability slot 0; shiny: any
    struct.pack_into('<HHB', g, 0x38, 0, gift['place'], gift['level'])   # egg place, met place, met level
    g[0x43:0x49] = b'\xff' * 6                                    # IVs at random
    ot = gift['ot']
    assert 0 < len(ot) <= 7 and ot.isascii(), ot
    struct.pack_into('<8H', g, 0x4A, *([ord(c) for c in ot] + [0xFFFF] + [0] * (7 - len(ot))))
    struct.pack_into('<BBB', g, 0x5A, gift['ot_gender'], gift['level'], 0)    # OT's gender, level, not an Egg
    g[KIND_AT] = 1                                                # a Pokémon gift
    return bytes(g)


def blob():
    g, bits = gifts()
    return struct.pack('<HH', len(g), 0) + b''.join(card(x, bits) for x in g), len(g)


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2EventGifts', code)
    if slot is None:
        return 'event_gifts: the decomp has no gPearlB2EventGifts (resident/leftovers.c): no event Pokémon'
    data, n = blob()
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:                                      # a quick non-clean build: the table is there, rewrite it in place
        resident.write(code, old, data)
        base = old
    else:
        base, end, _ = resident.install(code, lambda b: (data, {}))
        resident.write(code, slot, struct.pack('<I', base))
    names = ', '.join(x['species'][8:].title() for x in gifts()[0])
    return f'event_gifts: {n} event Pokémon ({names}) for extension 0xA9, {len(data)} B at {base:#x}'


if __name__ == '__main__':
    g, bits = gifts()
    for x in g:
        c = card(x, bits)
        print(x['species'], x['event'], f'Lv {x["level"]} OT {x["ot"]} {x["id"]:05d}', len(c), c[:0x20].hex())
