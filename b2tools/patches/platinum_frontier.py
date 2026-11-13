"""Platinum's Battle Frontier, its core's data (notes/PLATINUM_FRONTIER.md). Platinum's build list only, after battle_tower.

apply_code:
- The Exchange Service Corner (Platinum's ScrCmd_PokeMartFrontier, two counters) on Black 2's BP shop screen (ov036
  ShopUI_LoadBPShopItems, shops 253 and 254, which take the BP from the Subway's purse, the Frontier's BP here): Black 2's
  lists BP_SHOP_ITEMS_TMS (18 rows) and BP_SHOP_ITEMS_NORMAL (42 rows) and their counts become Platinum's right counter
  (15 TMs) and left counter (26 items), each at Platinum's BP price (overlay 7's itemToBpPrice). Both read from Platinum's
  dump by b2tools/platinum_frontier_data.py, which checks them against the decomp. A TM is the Black 2 item that teaches
  Platinum's move (tm_audit.pearl_item: Platinum's TM list is Pearl's); every other item has the same number in both.
  Black 2's own two BP lists are the PWT's, whose Battle Park Platinum doesn't have (its Battle Frontier stands there).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

OV036 = 0x0217F600                       # (patches/fairy.py's: overlay 36's load address)
ROWS = {'tms': 18, 'normal': 42}         # BP_SHOP_ITEM_COUNTS { 42, 18 }: NORMAL first
SHOP_ITEM = '<HxxI'                      # ShopItem { u16 item; u32 price; }
FIRST_NORMAL = struct.pack('<HxxI', 46, 1) + struct.pack('<HxxI', 49, 1)     # Black 2's: Protein 1 BP, Calcium 1 BP


def lists():
    """{'tms': [(Black 2 item, BP)], 'normal': [...]}: Platinum's right and left counters."""
    import platinum_frontier_data, tm_audit
    m, prices = platinum_frontier_data.marts()
    return {'tms': [(tm_audit.pearl_item(i), prices[i]) for i in m['right']],
            'normal': [(tm_audit.pearl_item(i), prices[i]) for i in m['left']]}


def apply_code(code):
    import decomp
    path = os.path.join(code, 'arm9_ov036.bin')
    ov = bytearray(open(path, 'rb').read())
    counts = decomp.symbol('BP_SHOP_ITEM_COUNTS', code)
    tables = {'tms': decomp.symbol('BP_SHOP_ITEMS_TMS', code), 'normal': decomp.symbol('BP_SHOP_ITEMS_NORMAL', code)}
    assert counts and all(tables.values()), 'platinum_frontier: this decomp has no BP shop symbols'
    assert bytes(ov[counts - OV036:counts - OV036 + 2]) == bytes([ROWS['normal'], ROWS['tms']]), \
        f'platinum_frontier: BP_SHOP_ITEM_COUNTS is {ov[counts - OV036:counts - OV036 + 2].hex()}'
    at = tables['normal'] - OV036
    assert bytes(ov[at:at + 16]) == FIRST_NORMAL, f'platinum_frontier: BP_SHOP_ITEMS_NORMAL starts {ov[at:at + 16].hex()}'
    new = lists()
    for key, rows in new.items():
        assert len(rows) <= ROWS[key], (key, len(rows))
        at = tables[key] - OV036
        for i, (item, bp) in enumerate(rows):
            struct.pack_into(SHOP_ITEM, ov, at + 8 * i, item, bp)
    ov[counts - OV036] = len(new['normal'])
    ov[counts - OV036 + 1] = len(new['tms'])
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(ov)
    os.replace(path + '.tmp', path)
    return f'platinum_frontier: the Exchange Service Corner on the BP shop: {len(new["tms"])} TMs, {len(new["normal"])} items'


if __name__ == '__main__':
    for k, rows in lists().items():
        print(k, rows)
