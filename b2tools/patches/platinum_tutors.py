"""Platinum's party commands' data (plat-tutors, 2026-11-07; the decomp's include/pearlb2/plat_party.h): the shard tutors'
table and Dr. Footstep's footprint types, and the work for the last battle's turn count. Platinum's build only.

apply_code(code)
- gPlatPartyTable, in overlay 376's .data (code/arm9_ov376.bin): Platinum's 38 tutor moves with their Shards and tutors,
  the 505 species-and-form masks, the 494 footprint types (b2tools/platinum_party_data.py blob(), from the Platinum
  dump). The overlay answers a tutor's question (ext sub-commands 0xb0, 0xb1) and a footprint's (0xb2) from it.
- gPearlB2TurnsWork, in the resident section's .data: Black 2 work 0x40FD, the one Platinum's VAR_TOTAL_TURNS_LAST_BATTLE
  has here (data/platinum/pearl_story_ids.json). After a won Trainer battle the battle's turn count + 1 goes there, as
  Platinum's battle end writes it (the Pokémon Mansion's five-maid knockout).
Pearl and Diamond (v101-story, 1.0.1: version.PARTY_COMMANDS): the same table with Dr. Footstep's footprints from their own
dump and no tutor move (no shard tutors: a tutor answers "can't"); no turn count is written (no maid battles). Before 1.0.1
they wrote nothing (a footprint answered "none"). The ribbon and contest-condition sub-commands (0xb3-0xb5) need no data.
List it anywhere after the code is copied (the overlays are in every build from pearlb2_overlays.py, before any patch); in
Pearl's and Diamond's build list it comes after `pearl_tms` (notes/RESUME.md "Commands").
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402

OVERLAY = 376
TURNS_VAR = 'VAR_TOTAL_TURNS_LAST_BATTLE'


def turns_work():
    """Black 2's work for Platinum's VAR_TOTAL_TURNS_LAST_BATTLE (data/platinum/pearl_story_ids.json)."""
    ids = json.load(open(version.data_path('pearl_story_ids.json')))
    works = [int(v['b2'], 16) for v in ids['vars'].values() if v.get('name') == TURNS_VAR]
    assert len(works) == 1, f'{TURNS_VAR}: {len(works)} Black 2 works in pearl_story_ids.json'
    return works[0]


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
    if not version.PARTY_COMMANDS:
        return f'platinum_tutors: {version.VERSION} has no party commands (nothing)'
    import decomp, resident
    import platinum_party_data as P
    slot = decomp.symbol('gPlatPartyTable', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if not version.PLATINUM:             # (v101-story) Pearl's and Diamond's footprints; no tutors, no turn count
        if slot is None or start is None:
            raise SystemExit('platinum_tutors: the decomp has no overlay 376 (src/pearlb2/plat_party/plat_party.c)')
        blob = P.blob()
        _write(os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin'), slot - start, blob)
        return (f'platinum_tutors: gPlatPartyTable {slot:#x} ({len(blob)} B: {version.NAME}\'s {P.FOOTPRINTS} footprints, '
                f'no tutor move) in overlay {OVERLAY}')
    turns = decomp.symbol('gPearlB2TurnsWork', code)
    if slot is None or start is None or turns is None:
        raise SystemExit('platinum_tutors: the decomp has no overlay 376 (src/pearlb2/plat_party/plat_party.c) or no '
                         'gPearlB2TurnsWork (src/pearlb2/resident/plat_party_ext.c)')
    blob = P.blob()
    _write(os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin'), slot - start, blob)
    work = turns_work()
    assert resident.read(code, turns, 2) in (bytes(2), struct.pack('<H', work)), f'gPearlB2TurnsWork at {turns:#x}: set'
    resident.write(code, turns, struct.pack('<H', work))
    return (f'platinum_tutors: gPlatPartyTable {slot:#x} ({len(blob)} B: {P.MOVES} tutor moves, {P.MOVESETS} masks, '
            f'{P.FOOTPRINTS} footprints) in overlay {OVERLAY}; gPearlB2TurnsWork {turns:#x} = {work:#06x}')


if __name__ == '__main__':
    import platinum_party_data as P
    print(len(P.blob()), 'B of table;', f'the turn count into work {turns_work():#x}' if version.PLATINUM else 'no turn count')
