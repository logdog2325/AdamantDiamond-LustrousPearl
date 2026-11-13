"""Platinum's Battle Factory, its data (plat-factory 2026-11-07; notes/PLATINUM_FRONTIER.md "The Battle Factory"). Platinum's
build list only, after battle_tower and platinum_frontier.

apply (files):
- Two regulations for Black 2's battle-entry party screen (a/1/0/6, appended after Black 2's 38): the rental screen, three of
  six, and the swap's two screens, one of three. Each is Black 2's file 20 (the Subway's single train) with the counts the
  Factory needs and no level rule (Open Level's rentals are Level 100), no clause and no banned species or item: Platinum's
  rentals are never the same species or item twice anyway (factory_rules.c SelectPokemonFromPool), and a rental the Subway
  bans must still be picked.
apply_code (code):
- gPlatFactoryTable in overlay 378's .data (src/pearlb2/plat_factory/factory.c): the two regulations' files and the
  Brain's battle song: Platinum's SEQ_PL_BA_BRAIN, as patches/battle_music.py installed it (plat-frontier-rooms; it runs
  earlier in the build list). Thorton's victory song is battle_music's too: Black 2 picks it by the first opponent's class
  (his class 237 -> SEQ_PL_WINBRAIN, data/battle_music.json "versions").
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))

REGULATION_ARC = 106
BASE_REGULATION = 20                    # the Subway's single train: 3 Pokémon, Level 50 (cap)
REGULATION_SIZE = 0xBC
OVERLAY = 378
BRAIN_SONG = 'SEQ_PL_BA_BRAIN'          # (plat-frontier-rooms) Platinum's BATTLE_FRONTIER_BRAIN, installed by battle_music
_files = {}


def regulation(base, count):
    """Black 2's regulation `base` (0xBC bytes, include/battle/regulation.h) with exactly `count` Pokémon, no level rule,
    the same species and item allowed, nothing banned and nothing required."""
    r = bytearray(base)
    assert len(r) == REGULATION_SIZE, len(r)
    r[2] = r[3] = count                 # minCount, maxCount
    r[4] = r[5] = 0                     # level, levelMode
    r[6:8] = bytes(2)                   # maxLevelTotal
    r[8] = r[9] = 1                     # allowSameSpecies, allowSameItem
    r[10:10 + 0x52 + 0x4C] = bytes(0x52 + 0x4C)     # bannedSpecies, bannedItems
    r[0xA8:0xAB] = bytes(3)             # requiredSpecies, requiredForm
    return bytes(r)


def regulations(arc):
    """The rental screen's and the swap screen's regulations, from the arc's own file 20."""
    return regulation(arc[BASE_REGULATION], 3), regulation(arc[BASE_REGULATION], 1)


def apply(files):
    import narcio, version
    if not version.PLATINUM:
        return 'platinum_factory: Platinum only (nothing)'
    arc = narcio.load(files, REGULATION_ARC)
    rent, swap = regulations(arc)
    _files['rent'], _files['swap'] = len(arc), len(arc) + 1
    arc += [rent, swap]
    narcio.save(files, REGULATION_ARC, arc)
    return f'platinum_factory: regulations {_files["rent"]} (three of six) and {_files["swap"]} (one of three) in a/1/0/6'


def apply_code(code):
    import decomp, version
    if not version.PLATINUM:
        return 'platinum_factory: Platinum only (nothing)'
    assert _files, 'platinum_factory: apply (the regulations) runs before apply_code'
    slot = decomp.symbol('gPlatFactoryTable', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if slot is None or start is None:
        raise SystemExit('platinum_factory: the decomp has no overlay 378 (src/pearlb2/plat_factory/factory.c)')
    from platinum_tutors import _write
    import battle_music
    bgm = battle_music.song_id(BRAIN_SONG)
    if bgm is None:
        raise SystemExit(f'platinum_factory: {BRAIN_SONG} is not installed: put battle_music before platinum_factory')
    blob = struct.pack('<4H', _files['rent'], _files['swap'], bgm, 0)
    _write(os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin'), slot - start, blob)
    return (f'platinum_factory: gPlatFactoryTable {slot:#x} = regulations {_files["rent"]}, {_files["swap"]}, '
            f'song {bgm} ({BRAIN_SONG})')


if __name__ == '__main__':          # offline: the two regulations from Black 2's own arc
    from gen4rom import Rom, narc_members
    arc = narc_members(Rom(os.path.join(ROOT, 'roms', 'black2_original.nds')).read('a/1/0/6'))
    rent, swap = regulations(arc)
    for name, r in (('rent', rent), ('swap', swap)):
        print(name, 'count', r[2], r[3], 'level', r[4], r[5], 'same species/item', r[8], r[9], 'banned',
              sum(r[10:10 + 0x52 + 0x4C]), 'required', r[0xA8:0xAB].hex(), 'rest as file 20:',
              r[0xAB:] == arc[BASE_REGULATION][0xAB:] and r[:2] == arc[BASE_REGULATION][:2])
    print(f'files {len(arc)}, {len(arc) + 1} after Black 2\'s {len(arc)}')
