"""Platinum's Battle Castle, its data (plat-castle 2026-11-07; the decomp's include/pearlb2/plat_castle.h; notes/PLATINUM_FRONTIER.md
"The Battle Castle"). Platinum's build list only, after battle_tower and platinum_frontier (and platinum_factory, if listed).

apply (files):
- The self screen's regulation for Black 2's battle-entry party screen (a/1/0/6): one of the castle's three, no level rule, no
  clause, nothing banned (platinum_factory.regulation: Black 2's file 20, the Subway's single train, with that count). The
  Factory's swap screen asks the same: the file is shared when platinum_factory made it already, else appended.
- The lobby's two (BC_LOBBY_FUNC_SELECT_POKEMON, Platinum's party menu in PARTY_MENU_MODE_BATTLE_CASTLE): three of the party
  (two for a Multi), any level (the castle makes a Pokémon above 50 Level 50), not the same species twice (Platinum's
  "identical Pokémon not permitted"), the same item allowed (the castle takes the items), file 20's banned species kept (they are
  Platinum's sBattleFrontierBanlist and Black 2's own legendaries), no banned item.
apply_code (code):
- gPlatCastleTable in overlay 380's .data (src/pearlb2/plat_castle/castle_field.c): its magic (a Platinum build's Castle is on),
  the regulations' files (the self screen's, the lobby's two), Darach's battle and victory songs (0 until SEQ_PL_BA_BRAIN and SEQ_PL_WINBRAIN are installed:
  plat-music's note; the Subway's songs play). Empty (Pearl, Diamond, or a build without this patch), no Castle challenge starts.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

OVERLAY = 380
MAGIC = 0x4C545343                      # 'CSTL' (PLATCASTLE_TABLE_MAGIC)
BRAIN_SONGS = ('SEQ_PL_BA_BRAIN', 'SEQ_PL_WINBRAIN')     # (plat-frontier-rooms) Darach's battle and victory songs, installed by
                                                         # patches/battle_music.py (earlier in the build list)
_files = {}


def pick_regulation(arc):
    """(arc, file): the one-of-three regulation, the Factory's own when it is there already."""
    import platinum_factory as F
    reg = F.regulation(arc[F.BASE_REGULATION], 1)
    for i, f in enumerate(arc):
        if f == reg:
            return arc, i
    return arc + [reg], len(arc)


def entry_regulation(base, count):
    """Black 2's regulation `base` for the lobby's party screen: exactly `count`, no level rule, not the same species twice, the
    same item allowed, its banned species kept, no banned item."""
    r = bytearray(base)
    assert len(r) == 0xBC, len(r)
    r[2] = r[3] = count                 # minCount, maxCount
    r[4] = r[5] = 0                     # level, levelMode
    r[6:8] = bytes(2)                   # maxLevelTotal
    r[8], r[9] = 0, 1                   # allowSameSpecies, allowSameItem
    r[10 + 0x52:10 + 0x52 + 0x4C] = bytes(0x4C)     # bannedItems
    return bytes(r)


def apply(files):
    import narcio, version
    import platinum_factory as F
    if not version.PLATINUM:
        return 'platinum_castle: Platinum only (nothing)'
    arc = narcio.load(files, F.REGULATION_ARC)
    before = len(arc)
    arc, _files['pick'] = pick_regulation(arc)
    shared = len(arc) == before
    _files['entry'] = (len(arc), len(arc) + 1)
    arc += [entry_regulation(arc[F.BASE_REGULATION], 3), entry_regulation(arc[F.BASE_REGULATION], 2)]
    narcio.save(files, F.REGULATION_ARC, arc)
    how = 'the Factory\'s' if shared else 'appended'
    return (f'platinum_castle: a/1/0/6 file {_files["pick"]}, one of three ({how}); '
            f'the lobby\'s {_files["entry"][0]} (three) and {_files["entry"][1]} (two)')


def songs():
    """(plat-frontier-rooms) the Black 2 ids battle_music gave Darach's two songs (0, 0 offline: the Subway's)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import battle_music
    ids = [battle_music.song_id(n) for n in BRAIN_SONGS]
    return ids if None not in ids else None


def table(bgm=(0, 0)):
    assert _files, 'platinum_castle: apply (the regulation) runs before apply_code'
    return struct.pack('<IHHHHHH', MAGIC, _files['pick'], _files['entry'][0], _files['entry'][1], bgm[0], bgm[1], 0)


def apply_code(code):
    import decomp, version
    if not version.PLATINUM:
        return 'platinum_castle: Platinum only (nothing)'
    slot = decomp.symbol('gPlatCastleTable', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if slot is None or start is None:
        raise SystemExit(f'platinum_castle: the decomp has no overlay {OVERLAY} (src/pearlb2/plat_castle/*.c)')
    from platinum_tutors import _write
    bgm = songs()
    if bgm is None:
        raise SystemExit(f'platinum_castle: {BRAIN_SONGS} are not installed: put battle_music before platinum_castle')
    blob = table(bgm)
    _write(os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin'), slot - start, blob)
    return (f'platinum_castle: gPlatCastleTable {slot:#x} = regulations {_files["pick"]}, {_files["entry"]}, songs {bgm[0]}, '
            f'{bgm[1]} ({", ".join(BRAIN_SONGS)})')


if __name__ == '__main__':          # offline: the regulation from Black 2's own arc, alone and after the Factory's two
    from gen4rom import Rom, narc_members
    import platinum_factory as F
    arc = narc_members(Rom(os.path.join(ROOT, 'roms', 'black2_original.nds')).read('a/1/0/6'))
    a, n = pick_regulation(list(arc))
    r = a[n]
    print(f'alone: file {n} of {len(a)}; count {r[2]}, {r[3]}; level {r[4]}, {r[5]}; same species/item {r[8]}, {r[9]}; '
          f'banned {sum(r[10:10 + 0x52 + 0x4C])}')
    rent, swap = F.regulations(arc)
    b, m = pick_regulation(list(arc) + [rent, swap])
    print(f'after the Factory\'s: file {m} of {len(b)} (the Factory\'s swap screen\'s: {len(arc) + 1})')
    for n in (3, 2):
        e = entry_regulation(arc[F.BASE_REGULATION], n)
        print(f'the lobby\'s ({n}): count {e[2]}, {e[3]}; level {e[4]}, {e[5]}; same species/item {e[8]}, {e[9]}; banned species '
              f'{[i for i in range(0x52 * 8) if e[10 + i // 8] >> (i % 8) & 1]}; banned items {sum(e[10 + 0x52:10 + 0x52 + 0x4C])}')
    _files['pick'] = m
    _files['entry'] = (len(b), len(b) + 1)
    print('gPlatCastleTable:', table().hex())
