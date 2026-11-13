"""Pearl's shops (notes/OPEN_CONTENT.md, b2tools/pearl_items.py reads the tables from the dump).

Black 2's Mart (ov036 ShopUI_LoadPokeMartItems): shop 255 reads list file BADGE_SHOP_DAT_IDS[badges] of a/2/8/2 (u16 item
ids), { 0, 1, 1, 2, 2, 3, 3, 4, 5 }: the same steps as Pearl's ScrCmd_NormalMart (0 badges; 1-2; 3-4; 5-6; 7; 8). So list
files 0-5 become Pearl's six lists. Any other shop n reads list file n + 6, so Pearl's SpecialMart n is shop n: list
files 6-24 (Black 2's specialty lists, which no Sinnoh script calls). A list's item count is byte `file` of a/2/8/3 file
0. Run before `fairy` (which copies shop 10's list and adds the Pixie Plate and Fairy Gem: DECISIONS 2026-10-19).

Prices: Black 2's own, equal to Pearl's for everything sold except the TMs (Black 2's cost up to 90,000, being reusable).
The TMs Pearl sells get Pearl's price here, as TM96-TM120 have (patches/pearl_tms.py); a/0/2/4 records hold price / 10.
TM83 Natural Gift = TM118 is sold by move (tm_audit), with its pearl_tms price.

Pearl's Goods and Seal clerks: Black 2 has no such goods (pearl_story h_mart_goods: a closed line). Pearl's 12 Mail
designs are Black 2's 12 Mail items on the same ids (b2tools/item_check.py lists them).

Platinum (2026-11-07, plat-fixes): its own tables from its own arm9 (pearl_items.mart_normal, mart_special): the same badge
list and special lists 0-18 as Pearl's, and a 20th, Veilstone Dept. Store B1F's berries (list file 25, Black 2's shop 19).
Its TMs get Platinum's own prices (pearl_price by Platinum's item table). Every list, clerk and price against Platinum's:
`PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py marts`.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402
import narcio, pearl_items  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402

LISTS, COUNTS, ITEMS = 282, 283, 24   # a/2/8/2, a/2/8/3, a/0/2/4
FIRST_SPECIAL = 6                     # SpecialMart n: list file n + 6
MAX_ENTRIES = 45                      # ov036 ShopUIWork entries[45]
PRICE = 0                             # a/0/2/4 record: u16 price / 10
PEARL_TM01 = 328


def pearl_price(item):
    """Pearl's price of a Pearl item (itemtool/itemdata/item_data.narc, by pokediamond sItemIndexMappings column 1).
    Platinum: its own price, from pl_item_data.narc by its own table (plat-fixes, 2026-11-07: Platinum's item data
    has other numbers, Griseous Orb's among them, so Pearl's table read wrong records: TM38 cost 2,000, not 5,500)."""
    global _prices
    if '_prices' not in globals():
        rom = Rom(version.WORLD_DUMP)
        data = narc_members(rom.read(version.ARCHIVE['items']))
        if version.PLATINUM:
            rows = [r[0] for r in platinum_item_table()]
        else:
            src = open(os.path.join(ROOT, 'external', 'pokediamond', 'arm9', 'src', 'itemtool.c')).read()
            at = src.index('sItemIndexMappings[][4] = {')
            rows = re.findall(r'\{\s*(\d+),\s*\d+,\s*\d+,\s*\d+\s*\}', src[at:src.index('};', at)])
        _prices = [struct.unpack_from('<H', data[int(r)], 0)[0] for r in rows]
    return _prices[item]


PLATINUM_ITEMS = 467                  # pokeplatinum NUM_ITEMS: items 0-466


def platinum_item_table():
    """[(data, icon, palette, Gen 3 item)] by item of Platinum's own table (pokeplatinum src/item.c sItemArchiveIDs),
    found in its arm9 by its first five rows (data and Gen 3 numbers 0-4: none, Master, Ultra, Great and Poké Ball)."""
    a, _ = pearl_items.world_arm9()
    hits = [p for p in range(0, len(a) - 40, 2)
            if [struct.unpack_from('<4H', a, p + 8 * i)[k] for i in range(5) for k in (0, 3)] ==
            [i for i in range(5) for _ in (0, 3)]]
    assert len(hits) == 1, f'Platinum\'s item table: {len(hits)} places'
    return [struct.unpack_from('<4H', a, hits[0] + 8 * i) for i in range(PLATINUM_ITEMS)]


def lists():
    """{list file: [Black 2 items]} of every shop list this patch writes."""
    out = {k: [pearl_items.b2_item(i) for i in l] for k, l in enumerate(pearl_items.mart_lists())}
    out.update({FIRST_SPECIAL + n: [pearl_items.b2_item(i) for i in l] for n, l in enumerate(pearl_items.mart_special())})
    return out


def apply(files):
    arc, counts = narcio.load(files, LISTS), narcio.load(files, COUNTS)
    c = bytearray(counts[0])
    new = lists()
    for f, items in new.items():
        assert 0 < len(items) <= MAX_ENTRIES and f < len(c) and f < len(arc), (f, len(items))
        arc[f] = struct.pack(f'<{len(items)}H', *items)
        c[f] = len(items)
    counts[0] = bytes(c)
    narcio.save(files, LISTS, arc)
    narcio.save(files, COUNTS, counts)
    records = narcio.load(files, ITEMS)
    tms = 0
    for l in pearl_items.mart_special():
        for pearl in l:
            b2 = pearl_items.b2_item(pearl)
            if PEARL_TM01 <= pearl <= 427 and b2 == pearl:     # (Pearl's other TMs keep pearl_tms' record)
                r = bytearray(records[b2])
                struct.pack_into('<H', r, PRICE, pearl_price(pearl) // 10)
                records[b2] = bytes(r)
                tms += 1
    narcio.save(files, ITEMS, records)
    return f'pearl_shops: {len(new)} lists (6 badge lists, {len(new) - 6} special), {tms} TMs at ' \
           f'{"Platinum" if version.PLATINUM else "Pearl"}\'s prices'
