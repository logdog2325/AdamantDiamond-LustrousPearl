"""Pearl's Vs. Seeker and all its rematches (DECISIONS 2026-10-19; notes/TRAINERS.md "Rematches"): the table for the
decomp's src/pearlb2/resident/vs_seeker.c, gPearlB2VsSeeker: the two works, the five level flags and Pearl's 240-record
rematch table from Pearl's own ROM (the Vs. Seeker's gVsSeekerRematchData: base, levels 1-5; 0xffff no Trainer at that
level, 0 the end), in Black 2's Trainer ids (data/pearl_story_ids.json "trainers"). Records of Pearl's unused Trainers
(no Black 2 id) are left out; the table's Trainers are installed by patches/pearl_trainers.py.

    build_rom.py ... pearl_trainers ... vs_seeker
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402

PEARL_ROM = version.WORLD_DUMP
# ROM offset of the table in Pearl (USA), found by Tristan's record; in Platinum (Rev 1) by its first three (pokeplatinum vs_seeker.c)
TABLE_ROM, TABLE_RECORDS = 0x1796c8 if version.PLATINUM else 0x16483c, 240
NONE, END = 0xffff, 0
ITEM = 443
LEVEL_FLAGS = (0x97F, 0x980, 0x981, 0x982, 0x983)   # Pearl's FLAG_UNLOCKED_VS_SEEKER_LVL_1..5


def records():
    d = open(PEARL_ROM, 'rb').read()
    return [struct.unpack_from('<6H', d, TABLE_ROM + 12 * i) for i in range(TABLE_RECORDS)]


def tier_ids(ids):
    """Pearl's Trainers that only a rematch uses: the levels' ids except the base Trainer's own (bases on no map, and
    their rematches, stay out: b2tools/pearl_ids.py gives these their Black 2 ids). ids: the registry's "trainers"."""
    out = []
    for r in records():
        if str(r[0]) in ids:
            out += [t for t in r[1:] if t not in (NONE, END) and t != r[0]]
    return sorted(set(out))


def table():
    reg = json.load(open(version.data_path('pearl_story_ids.json')))
    t, flags = reg['trainers'], reg['flags']
    new = reg['new']
    rows = []
    for r in records():
        if str(r[0]) not in t:
            continue
        rows.append([x if x in (NONE, END) else t[str(x)]['b2'] for x in r])
    lf = [0] + [flags[f'0x{f:04X}']['b2'] for f in LEVEL_FLAGS]
    blob = struct.pack('<2H', int(new['PVAR_VS_SEEKER_BATTERY']['b2'], 16), int(new['PVAR_VS_SEEKER_STEPS']['b2'], 16))
    blob += struct.pack('<6H', *lf) + struct.pack('<2H', len(rows), 0)
    blob += b''.join(struct.pack('<6H', *r) for r in rows)
    return blob, f'{len(rows)} rematch records'


def apply(files):
    """The item (a/0/2/4 443): a key item with "Use" in the Bag that can be put on the Y button, as Pearl's."""
    import narcio
    entries = narcio.load(files, 24)
    d = bytearray(entries[ITEM])
    flags = struct.unpack_from('<H', d, 8)[0]
    struct.pack_into('<H', d, 8, flags | 0x20 | 0x40)                # important, registrable
    d[10] = 25                                                       # field use: shows "Use" (exp_share.py's value)
    entries[ITEM] = bytes(d)
    narcio.save(files, 24, entries)
    return 'vs_seeker: item 443 usable from the Bag and the Y button'


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2VsSeeker', code)
    if slot is None:
        return 'vs_seeker: no gPearlB2VsSeeker in this decomp'
    blob, summary = table()
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:
        resident.write(code, old, blob)
        base = old
    else:
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    return f'vs_seeker: {summary}, {len(blob)} B at {base:#x}'


# ---- global 3000 with Pearl's rematch: `python3 vs_seeker.py --sources` writes src/field_scripts/1239_global_3000.s
SCRIPT_SRC = os.path.join(ROOT, 'src', 'field_scripts', '1239_global_3000.s')
DECOMP = os.path.join(ROOT, 'external', 'pokebw2')
ANCHOR = """    VMJumpIf CMP_STACK, L_0D5F
    TrainerGetFieldAction 0x8020, 0x8010
"""
REMATCH_CHECK = """    VMJumpIf CMP_STACK, L_0D5F
    // PearlB2: Pearl's rematch (pokeplatinum scripts_battles.s Battles_TryRematch): a defeated Trainer who spins
    // answers with the Trainer of its level (resident/vs_seeker.c; 0: none, the usual line)
    FieldCommand 351
    .byte 0xA3
    .2byte 0x8011
    .2byte 0x8020
    .2byte 0x8027
    WorkCmpConst 0x8027, 0
    VMJumpIf CMP_NE, L_PearlRematch
    TrainerGetFieldAction 0x8020, 0x8010
"""
REMATCH = """
// PearlB2: Battles_Rematch: both of a double need two Pokémon, the rematch's own line (types 25-27:
// patches/pearl_trainers.py), the battle against the level's Trainer, whose flag it sets
L_PearlRematch:
    TrainerGetBattleType_008A 0x8027, 0x8025
    WorkCmpConst 0x8025, 0
    VMJumpIf CMP_EQ, L_PearlRematchGo
    PokePartyGetCount 0x8026, 2
    WorkCmpConst 0x8026, 2
    VMJumpIf CMP_GE, L_PearlRematchGo
    VMCall L_0E9F
    VMJump L_0E54

L_PearlRematchGo:
    TrainerBGMPlayPush 0x8020
    TrainerGetMessageTypes 0x8021, 0x8022, 0x8023
    WorkSetConst 0x8024, 25
    WorkCmpConst 0x8021, 3
    VMJumpIf CMP_NE, L_PearlRematch2
    WorkSetConst 0x8024, 26
L_PearlRematch2:
    WorkCmpConst 0x8021, 7
    VMJumpIf CMP_NE, L_PearlRematch3
    WorkSetConst 0x8024, 27
L_PearlRematch3:
    TrainerSayMessage 0x8020, 0x8024, 0x8011
    ActorMsgClose
    FieldCommand 351
    .byte 0xA4
    .2byte 0x8011
    CallTrainerBattle 0x8027, 0, 0
    TrainerBattleIsVictory 0x8010
    WorkCmpConst 0x8010, 1
    VMJumpIf CMP_EQ, L_PearlRematchWon
    CallTrainerLose
L_PearlRematchWon:
    CallTrainerBattleEnd
    TrainerFlagSet 0x8027
    VMJump L_0E54
"""


def sources():
    s = open(os.path.join(DECOMP, 'res', 'field', 'scripts', 'global_3000.s'), encoding='utf-8').read()
    assert s.count(ANCHOR) == 1, 'global_3000.s: the talk script changed'
    s = s.replace(ANCHOR, REMATCH_CHECK)
    head = ("// Global scripts 3000-6999 (a/0/5/6 entry 1239): Black 2's Trainer script, pokebw2 res/field/scripts/global_3000.s,\n"
            "// with Pearl's rematch added (b2tools/patches/vs_seeker.py --sources writes this file).\n")
    return head + s.rstrip('\n') + '\n' + REMATCH


if __name__ == '__main__':
    if '--sources' in sys.argv:
        open(SCRIPT_SRC, 'w', encoding='utf-8').write(sources())
    ids = json.load(open(version.data_path('pearl_story_ids.json')))['trainers']
    print(len(tier_ids(ids)), 'rematch-only Trainers;', table()[1] if '--table' in sys.argv else '')
