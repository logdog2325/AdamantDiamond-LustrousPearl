"""Platinum's Battle Arcade, its data (plat-arcade 2026-11-07; the decomp's include/pearlb2/plat_arcade.h; notes/PLATINUM_FRONTIER.md
"The Battle Arcade"). Platinum's build list only, after battle_tower, platinum_frontier and platinum_castle (if listed).

apply (files):
- The lobby's regulation (BA_LOBBY_FUNC_SELECT_POKEMON: Platinum's party menu in PARTY_MENU_MODE_BATTLE_CASTLE, the Castle's own
  mode): three of the party, any level (the Arcade makes a Pokémon above 50 Level 50), not the same species twice, the same item
  allowed, Black 2's Subway file's banned species kept (Platinum's sBattleFrontierBanlist and Black 2's own legendaries), no banned
  item. It is the Castle's lobby file (platinum_castle.entry_regulation(..., 3)): shared when platinum_castle made it already, else
  appended.
apply_code (code):
- gPlatArcadeTable in overlay 381's .data (src/pearlb2/plat_arcade/arcade_field.c): its magic (a Platinum build's Arcade is on),
  the regulation's file, Dahlia's battle and victory songs (SEQ_PL_BA_BRAIN, SEQ_PL_WINBRAIN once installed: 0, the Subway's
  songs, until then). Empty (Pearl, Diamond, or a build without this patch), no Arcade challenge starts.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

OVERLAY = 381
MAGIC = 0x44435241                      # 'ARCD' (PLATARCADE_TABLE_MAGIC)
_files = {}


def brain_songs(offline=False):
    """Dahlia's battle and victory songs: Black 2's ids of Platinum's SEQ_PL_BA_BRAIN and SEQ_PL_WINBRAIN, which patches/battle_music.py
    installs (earlier in the build list), the same source as the other facilities' tables (platinum_castle.songs, plat-frontier-
    rooms); 0, 0 (the Subway's) offline or before that is in."""
    import platinum_castle as C
    if not hasattr(C, 'songs'):
        return getattr(C, 'BRAIN_BGM', 0), getattr(C, 'BRAIN_WIN_BGM', 0)
    if offline:
        return 0, 0
    ids = C.songs()
    if ids is None:
        raise SystemExit('platinum_arcade: SEQ_PL_BA_BRAIN and SEQ_PL_WINBRAIN are not installed: put battle_music before '
                         'platinum_arcade')
    return tuple(ids)


def apply(files):
    import narcio, version
    import platinum_factory as F
    import platinum_castle as C
    if not version.PLATINUM:
        return 'platinum_arcade: Platinum only (nothing)'
    arc = narcio.load(files, F.REGULATION_ARC)
    reg = C.entry_regulation(arc[F.BASE_REGULATION], 3)
    for i, f in enumerate(arc):
        if f == reg:
            _files['entry'] = i
            return f'platinum_arcade: the lobby\'s regulation, a/1/0/6 file {i} (the Castle\'s lobby\'s)'
    _files['entry'] = len(arc)
    narcio.save(files, F.REGULATION_ARC, arc + [reg])
    return f'platinum_arcade: the lobby\'s regulation, a/1/0/6 file {len(arc)} (appended)'


def table(offline=False):
    assert _files, 'platinum_arcade: apply (the regulation) runs before apply_code'
    bgm, win = brain_songs(offline)
    return struct.pack('<IHHHH', MAGIC, _files['entry'], bgm, win, 0)


def apply_code(code):
    import decomp, version
    if not version.PLATINUM:
        return 'platinum_arcade: Platinum only (nothing)'
    slot = decomp.symbol('gPlatArcadeTable', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if slot is None or start is None:
        raise SystemExit(f'platinum_arcade: the decomp has no overlay {OVERLAY} (src/pearlb2/plat_arcade/*.c)')
    from platinum_tutors import _write
    blob = table()
    _write(os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin'), slot - start, blob)
    return f'platinum_arcade: gPlatArcadeTable {slot:#x} = {blob.hex()} (the regulation {_files["entry"]}, the songs)'


if __name__ == '__main__':          # offline: the regulation from Black 2's own arc, alone and after the Castle's
    from gen4rom import Rom, narc_members
    import platinum_factory as F
    import platinum_castle as C
    arc = list(narc_members(Rom(os.path.join(ROOT, 'roms', 'black2_original.nds')).read('a/1/0/6')))
    reg = C.entry_regulation(arc[F.BASE_REGULATION], 3)
    with_castle = arc + [reg, C.entry_regulation(arc[F.BASE_REGULATION], 2)]
    found = [i for i, f in enumerate(with_castle) if f == reg]
    print(f'alone: appended as file {len(arc)}; after the Castle\'s: file {found[0]} (the Castle\'s lobby\'s three)')
    print(f'count {reg[2]}, {reg[3]}; level {reg[4]}, {reg[5]}; same species/item {reg[8]}, {reg[9]}')
    _files['entry'] = found[0]
    print('gPlatArcadeTable:', table(offline=True).hex(), '(12 bytes: sizeof(PlatArcadeTable); the songs 0 offline)')
