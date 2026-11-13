"""The other version's legendary at Spear Pillar after the Hall of Fame (the user, 2026-11-09; notes/POSTGAME_DEX.md 4.8):
version.POSTGAME_LEGEND = (species, level, Orb): Dialga Lv 47 and the Adamant Orb in Lustrous Pearl, Palkia Lv 47 and the
Lustrous Orb in Adamant Diamond, None elsewhere (Platinum has both after its Hall of Fame already).

It stands where the version's own legendary stood (Pearl's Spear Pillar object 5, (31, 21)) once the game is cleared
(flag 2400) and the version's own legendary is caught (Pearl's PFLAG_015F, which its two battles set on a catch), until it
is caught. Its battle is the version's own battle's (Pearl's script 14: the cry and the zone's own line, the same wild
battle at Lv 47); knocked out, it "returned to the world from which it came" (the zone's line) and stands there again the
next time the player comes; caught, it leaves the other Orb (Black 2's item-get).

The pieces go in through b2tools/ramanas.py's hooks for Pearl zones (pearl_story's extra entries, pearl_events' people
and zone inits), so no other extra-entry numbering moves:
- zone_extras: 'legend_init' (a zone init after Pearl's: the person shown or hidden by PFLAG_PG_LEGEND_HIDDEN) and
  'legend' (its talk script);
- extra_people: the person (uid UID, Pearl's OBJ_EVENT_GFX_DIALGA / _PALKIA = Black 2's 4632 / 4633);
- extra_triggers: the battle's step trigger, Pearl's own row for its legendary after the Hall of Fame (x 29-33, z 26),
  while it stands there (map-local work SHOWN_WORK = 1), as Pearl starts its own legendary's battle;
- zone_inits: the zone-init entry;
- extra_code: both entries' code.
Saved flags (b2tools/pearl_ids.py NEW_FLAGS): PFLAG_PG_LEGEND_HIDDEN (the person's), PFLAG_PG_LEGEND_CAUGHT.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import version  # noqa: E402

ZONE = 'MAP_MOUNT_CORONET_SPEAR_PILLAR'
UID = 100                                   # after Pearl's 14 objects (0-13)
SPOT = (31, 21)                             # Pearl's object 5 (the version's own legendary, OBJ_EVENT_GFX_VAR_1)
FACING = 1                                  # south, as object 5
GFX = {483: 154, 484: 155}                  # Pearl's OBJ_EVENT_GFX_DIALGA / _PALKIA (data/pearl_sprite_map.json)
CRY_LINE = {483: 32, 484: 33}               # Spear Pillar's bank 220: "Dialga: Gugyugubah!" / "Palkia: Gagyagyaah!"
GONE_LINE = {483: 34, 484: 35}              # "... returned to the world from which it came..."
OWN_CAUGHT = 'PFLAG_015F'                   # Pearl's flag: the version's own legendary caught (script 230)
GAME_CLEAR = 'PFLAG_0964'                   # Black 2's 2400
HIDDEN, CAUGHT = 'PFLAG_PG_LEGEND_HIDDEN', 'PFLAG_PG_LEGEND_CAUGHT'
ITEMS = {'ADAMANT_ORB': 135, 'LUSTROUS_ORB': 136}
T0, T7 = 0x8050, 0x8057                     # script temps (ramanas.T)
SHOWN_WORK = 0x401D                         # map-local (Black 2 clears 0x4000-0x401F on a zone change; Pearl's 13 take
                                            # 0x4010-0x401C): 1 while it stands here, the step trigger's condition
TRIGGER = (29, 26, 5, 1)                    # (x, z, w, h): Pearl's own row for its legendary after the Hall of Fame
                                            # (script 14's coord event), walked over on the way up to the altar


def active():
    return bool(version.POSTGAME_LEGEND)


def zone_extras(zone_name):
    return ['legend_init', 'legend'] if active() and zone_name == ZONE else []


def extra_people(zone_name, ids):
    if not zone_extras(zone_name):
        return []
    import ramanas
    species = version.POSTGAME_LEGEND[0]
    return [dict(id=UID, graphics_id=GFX[species], movement_type=0, trainer_type=0, hidden_flag=0,
                 b2_flag=ramanas.pearl_flag(HIDDEN), script=ids['legend'], initial_dir=FACING, data=[0, 0, 0],
                 movement_range_x=0, movement_range_z=0, x=SPOT[0], z=SPOT[1], y=0)]


def zone_inits(zone_name, ids):
    return [ids['legend_init']] if zone_extras(zone_name) else []


def extra_triggers(zone_name, ids):
    """The battle's step trigger (as Pearl's own legendary's after the Hall of Fame: a row the player walks over; a talk
    would reach Pearl's own legendary's object instead while that one stands on the same tile): [{script, x, z, w, h,
    work, value}]."""
    if not zone_extras(zone_name):
        return []
    x, z, w, h = TRIGGER
    return [dict(script=ids['legend'], x=x, z=z, w=w, h=h, work=SHOWN_WORK, value=1)]


def defines(job, bank):
    """The Pearl and Diamond values by the build's PEARLB2_GAME_VERSION: the zone's file is shared by both versions (a
    Diamond build takes Pearl's src/ files), so the code names PG_LEGEND, PG_LEVEL, PG_ORB, PG_CRY_LINE and PG_GONE_LINE."""
    out, first = ['// (postdex) the other version\'s legendary by the build (version.POSTGAME_LEGEND_BY)'], True
    for v in version.VERSIONS:
        row = version.POSTGAME_LEGEND_BY[v]
        if not row:
            continue
        species, level, orb = row
        out += [f'#{"if" if first else "elif"} PEARLB2_GAME_VERSION == {version.GAME_VERSION_BY[v]}     // {v}',
                f'#define PG_LEGEND {species}', f'#define PG_LEVEL {level}', f'#define PG_ORB {ITEMS[orb]}',
                f'#define PG_CRY_LINE {job.line_for(bank, CRY_LINE[species])}',
                f'#define PG_GONE_LINE {job.line_for(bank, GONE_LINE[species])}']
        first = False
    return out + ['#endif']


def extra_code(job, pd, zone, ids):
    if not zone_extras(zone['name']):
        return []
    import ramanas
    flag = ramanas.pearl_flag
    hidden, caught, clear, own = flag(HIDDEN), flag(CAUGHT), flag(GAME_CLEAR), flag(OWN_CAUGHT)
    bank = zone['text_bank']
    species, level = 'PG_LEGEND', 'PG_LEVEL'
    c = ramanas.Code('PG')
    c('', *defines(job, bank))
    got = c.label('caught')
    c('', 'RamanasExtra_legend_init:         // (postdex) zone init: the other version\'s legendary stands here after the '
          'Hall of Fame', '                                  // once this version\'s own is caught, until it is caught '
          '(b2tools/postgame_legend.py)',
      f'    FlagSet {hidden}', f'    WorkSetConst 0x{SHOWN_WORK:04X}, 0')
    end = c.label('init_end')
    c.jump_if_flag(clear, 0, end)
    c.jump_if_flag(own, 0, end)
    c.jump_if_flag(caught, 1, end)
    c(f'    FlagReset {hidden}', f'    WorkSetConst 0x{SHOWN_WORK:04X}, 1')
    c.at(end)
    c('    VMHalt')
    lost, done = c.label('lost'), c.label('done')
    c('', 'RamanasExtra_legend:              // (postdex) the other version\'s legendary (version.POSTGAME_LEGEND)',
      '    pl_LockAll',
      f'    WorkSetConst 0x{SHOWN_WORK:04X}, 0',                   # (the trigger fires once a visit)
      f'    pl_PlayCry {species}',
      '    pl_msg_sys PG_CRY_LINE',
      '    pl_WaitABPress',
      '    pl_WaitCry',
      '    pl_CloseMessage',
      f'    CallWildBattle {species}, {level}, 0',
      f'    WildBattleIsVictory 0x{T0:04X}', f'    WorkCmpConst 0x{T0:04X}, 1', f'    VMJumpIf CMP_NE, {lost}',
      f'    ActorDelete {UID}', f'    FlagSet {hidden}', '    CallWildBattleEnd',
      f'    WildBattleGetResult 0x{T0:04X}',
      f'    WorkCmpConst 0x{T0:04X}, 0', f'    VMJumpIf CMP_EQ, {got}',          # (0: caught)
      '    pl_msg_sys PG_GONE_LINE', '    pl_WaitButton', '    pl_CloseMessage',
      f'    VMJump {done}')
    c.at(got)
    c(f'    FlagSet {caught}')
    c.give('PG_ORB')
    c.at(done)
    c('    pl_ReleaseAll', '    VMHalt')
    c.at(lost)
    c('    CallWildLose', '    VMHalt')
    return c.out
