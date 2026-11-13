"""Platinum's Battle Hall's tables (plat-hall, 2026-11-07; the decomp's include/pearlb2/plat_hall.h; notes/PLATINUM_FRONTIER.md
"The Battle Hall"). Platinum's build only.

apply_code(code)
- gPlatHallTable, in overlay 379's .data (code/arm9_ov379.bin): the Hall's 478 sets (battle/b_pl_stage/pl_bsdpm.narc), its
  477 opponents and their two types, the Trainer class tables by rank and by type, the classes of Frontier Trainers 0-299, the
  abilities of each set's species and form, which Trainers' names start with I or J (b2tools/platinum_hall_data.py table():
  every code table found in Platinum's dump by its bytes). Empty (Pearl, Diamond, or a build without this patch), the Hall's
  ops answer 0 and start no battle. Its last two fields: Argenta's battle and victory songs, Platinum's SEQ_PL_BA_BRAIN and
  SEQ_PL_WINBRAIN as patches/battle_music.py installed them (plat-frontier-rooms; battle_music runs earlier in the list).
List it anywhere after the code is copied (the overlays are in every build from pearlb2_overlays.py, before any patch); in
Platinum's build list, after platinum_frontier.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402

OVERLAY = 379
BRAIN_SONGS = ('SEQ_PL_BA_BRAIN', 'SEQ_PL_WINBRAIN')     # (plat-frontier-rooms) Argenta's battle and victory songs


def _write(path, at, blob):
    data = bytearray(open(path, 'rb').read())
    assert at + len(blob) <= len(data), f'{path}: {at + len(blob)} past its {len(data)} B'
    old = bytes(data[at:at + len(blob)])
    assert old in (bytes(len(blob)), blob), f'{path} at {at:#x}: not empty'
    data[at:at + len(blob)] = blob
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(data)
    os.replace(path + '.tmp', path)


def apply_code(code):
    if not version.PLATINUM:
        return f'platinum_hall: {version.VERSION} has no Battle Hall (nothing)'
    import decomp
    import platinum_hall_data as H
    slot = decomp.symbol('gPlatHallTable', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if slot is None or start is None:
        raise SystemExit(f'platinum_hall: the decomp has no overlay {OVERLAY} (src/pearlb2/plat_hall/*.c)')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import battle_music
    songs = [battle_music.song_id(n) for n in BRAIN_SONGS]
    if None in songs:
        raise SystemExit(f'platinum_hall: {BRAIN_SONGS} are not installed: put battle_music before platinum_hall')
    blob = H.table(*songs)
    _write(os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin'), slot - start, blob)
    return (f'platinum_hall: gPlatHallTable {slot:#x} ({len(blob)} B) in overlay {OVERLAY}; Argenta\'s songs '
            f'{songs[0]}, {songs[1]} ({", ".join(BRAIN_SONGS)})')


if __name__ == '__main__':
    import platinum_hall_data as H
    print(len(H.table()), 'B of table')
