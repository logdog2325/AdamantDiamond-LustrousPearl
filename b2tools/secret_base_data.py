"""Pearl's Secret Bases as data (notes/SECRET_BASES.md): everything read from the build version's dump, nothing written out by
hand. Pearl and Diamond hold the same goods, lists and traders (secret_base_check.py compares them), so nothing here splits.

    goods()           the goods table in Pearl's arm9: width, depth, collision[9], Sphere price, money, record line, National Dex
    good_models()     {good id: Pearl build model}: Pearl's area 2 list holds good id - 1 (the PCs at 0-4, the holes at 128-131)
    stock()           Veilstone 4F's two lists (pokediamond scrcmd_mart.c sDecorationMartPointers)
    traders()         the goods traders' tiles (overlay 18's vendor table: type, x, z; type 0 = goods)
    blob(...)         the C's table (include/pearlb2/secret_base.h PearlB2SecretBase)
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

DATA = os.path.join(ROOT, 'data', 'secret_bases.json')
BASE_ZONE, TUNNEL_ZONE = 670, 633       # allocate_sinnoh APPEND_BLOCKS 'Secret Bases' (670-684), 'Underground'
BASE_CHUNK = 561                        # Pearl's Secret Base cell (matrix 2's rows 0-1 and column 0)
GIMMICK = 64                            # the decomp's PEARLB2_GIMMICK_SECRET_BASE
GOOD_COUNT, GOOD_SIZE = 139, 28
GOOD_PC, GOOD_BOULDER, RES_CURSOR = 1, 6, 139
HOLE_GOODS = range(129, 133)            # Pearl's DECORATION_129..132: its base entrances, in the tunnels' pack
HOLE_MODELS = (429, 430, 431, 432)      # by Pearl's direction N, S, W, E
GAME_CLEAR_FLAG = 2400                  # Pearl's FLAG_GAME_COMPLETED (ug_data: BDSP's National Pokédex stage = Champion)
TEXT_FILE, SCRIPT_FILE = 1310, 1281     # a/0/0/3 PEARLB2_TEXT_GLOBAL_10735; a/0/5/6 SCRIPTS_GLOBAL_10735
GLOBAL_FIRST = 10735
TRADER_UID = 0x90                       # actor uids of the goods traders in the tunnels


def data():
    return json.load(open(DATA, encoding='utf-8'))


def _dump():
    return open(version.SOURCE_DUMP, 'rb').read()


def _table_offset(d):
    """The goods table: entry 1 is the first PC, 2 x 1 with the collision 1 1 0 ..., 28 bytes each, five times."""
    pat = bytes([2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    at = d.find(pat)
    while at >= 0:
        if all(d[at + 28 * k:at + 28 * k + 11] == pat for k in range(5)) and not any(d[at - 28:at]):
            return at - 28
        at = d.find(pat, at + 1)
    raise SystemExit('secret_base_data: the goods table is not in the dump')


def goods():
    d = _dump()
    at = _table_offset(d)
    out = []
    for g in range(GOOD_COUNT):
        e = d[at + g * GOOD_SIZE:at + (g + 1) * GOOD_SIZE]
        money, line = struct.unpack_from('<ii', e, 16)
        out.append(dict(id=g, width=e[0], depth=e[1], collision=list(e[2:11]), sphere=list(e[11:14]), money=money, line=line,
                        natdex=e[24], ungiftable=e[25]))
    return out


def trader_price(good, per_size):
    """A trader's money price: the middle of the good's Sphere sizes at per_size a size (Pearl's traders take Spheres, and
    digging isn't built: notes/DECISIONS.md), rounded to 100; 0 = no Sphere price, not sold."""
    lo, hi = good['sphere'][1:3]
    if not hi:
        return 0
    return round((lo + hi) / 2 * per_size / 100) * 100


def good_models():
    from gen4rom import Rom, narc_members
    rom = Rom(version.SOURCE_DUMP)
    area = narc_members(rom.read('fielddata/areadata/area_data.narc'))[2]
    bset = struct.unpack_from('<H', area, 0)[0]
    lst = narc_members(rom.read('fielddata/areadata/area_build_model/area_build.narc'))[bset]
    n = struct.unpack_from('<H', lst, 0)[0]
    models = struct.unpack_from(f'<{n}H', lst, 2)
    assert n == GOOD_COUNT - 1, n
    return {g: models[g - 1] for g in range(1, GOOD_COUNT)}


def stock():
    """Veilstone's lists: the dump must hold them as pokediamond's scrcmd_mart.c writes them."""
    d = _dump()
    out = []
    for first in ((7, 22, 25, 26, 27), (115, 116, 117, 119, 120, 121)):
        pat = struct.pack(f'<{len(first)}H', *first) + b'\xff\xff'
        assert d.count(pat) == 1, first
        out.append(list(first))
    return out


def traders():
    """Overlay 18's vendor table (x, z of the eight goods traders), found by its first entries."""
    d = _dump()
    pat = struct.pack('<9H', 0, 72, 104, 0, 424, 87, 0, 200, 185)
    assert d.count(pat) == 1
    at = d.find(pat)
    rows = [struct.unpack_from('<3H', d, at + 6 * k) for k in range(20)]
    assert [r[0] for r in rows] == [0] * 8 + [1] * 8 + [2] * 4, rows
    return [(x, z) for t, x, z in rows if t == 0]


def collision_bits(g):
    return sum(1 << i for i, c in enumerate(g['collision']) if c)


def blob(pack, hole_res, holes, scripts):
    """The C's PearlB2SecretBase."""
    cfg = data()
    assert len(holes) == 18 and len(hole_res) == 4
    out = struct.pack('<3H', BASE_ZONE, TUNNEL_ZONE, pack) + struct.pack('<4H', *hole_res)
    out += struct.pack('<2H', 1 if cfg['flags_from_hideaways'] else 0, GAME_CLEAR_FLAG)
    out += struct.pack('<4H', scripts['Kit'], scripts['Hole'], scripts['Exit'], scripts['Record'])
    out += struct.pack('<H', TRADER_UID)
    for x, z in holes:
        out += struct.pack('<2H', x, z)
    for lst in stock():
        out += bytes(lst) + bytes(8 - len(lst))
    for g in goods():
        out += struct.pack('<BBHHHBB', g['width'], g['depth'], collision_bits(g), g['money'],
                           trader_price(g, cfg['trader_price_per_size']), g['line'], g['natdex'])
    return out
