"""The aide in Rowan's lab who switches the Pokémon from Unova on and off (the user, 2026-11-23: an older save, made
before Rowan asked the sixth question, gets them through him; notes/UNOVA.md). PFLAG_UNOVA is the flag Rowan's question
sets (b2tools/pearl_ids.py NEW_FLAGS, patches/pearl_intro.py); the Pokémon you caught stay with you either way.

The pieces go in through b2tools/ramanas.py's hooks for Pearl zones (pearl_story's extra entries, pearl_events'
people), after postgame_legend's, so no other extra-entry numbering moves:
- zone_extras: 'unova_aide' (his talk script) in Rowan's lab;
- extra_people: the aide (uid UID, Pearl's SPRITE_ASSISTANTM, the lab's other aide's), at SPOT facing east;
- extra_code: his script. Off: he tells of the discovery and asks; YES sets the flag. On: he asks whether only Sinnoh's
  own Pokémon should appear again; YES clears it. The next zone loaded has the tables of the answer; a Gym Leader's,
  the Elite Four's and Cynthia's teams follow at once.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ZONE = 'MAP_SANDGEM_ROWANS_LAB'
UID = 100                                   # after the lab's 5 objects (0-4)
SPOT = (3, 9)                               # the lab's west side, off the walk from the door to Rowan
FACING = 3                                  # east
GFX = 29                                    # Pearl's SPRITE_ASSISTANTM (data/pearl_sprite_map.json; the lab's object 1)
FLAG = 'PFLAG_UNOVA'
TEXT = {
    'off_ask': 'Hi! I help the Professor with\\nhis research.\\rPokémon from faraway Unova\\nhave been seen all over Sinnoh!'
               '\\rWould you like to meet them\\non your journey?',
    'off_yes': 'Great! Look for them in tall grass,\\nin caves and on the water.\\rThe Professor would love to hear\\n'
               'what you find!',
    'off_no': 'Oh, all right. Come back and see me\\nif you change your mind.',
    'on_ask': 'Pokémon from faraway Unova live\\nall over Sinnoh now.\\rShould only Sinnoh’s own Pokémon\\nappear again?',
    'on_yes': 'All right! Only Sinnoh’s own\\nPokémon from now on.\\rThe Pokémon you’ve caught stay\\nwith you, of course!',
    'on_no': 'Happy hunting, then!',
}


def zone_extras(zone_name):
    return ['unova_aide'] if zone_name == ZONE else []


def extra_people(zone_name, ids):
    if not zone_extras(zone_name):
        return []
    return [dict(id=UID, graphics_id=GFX, movement_type=0, trainer_type=0, hidden_flag=0, script=ids['unova_aide'],
                 initial_dir=FACING, data=[0, 0, 0], movement_range_x=0, movement_range_z=0, x=SPOT[0], z=SPOT[1], y=0)]


def extra_code(job, pd, zone, ids):
    if not zone_extras(zone['name']):
        return []
    import ramanas
    L = lambda k: job.line_text(('unova', k), TEXT[k])
    c = ramanas.Code('UA')
    on, yes_on, yes_off = c.label('on'), c.label('stop'), c.label('start')
    c('', 'RamanasExtra_unova_aide:          // (unova) the aide: Pokémon from Unova on and off (b2tools/unova_aide.py)',
      '    pl_LockAll', '    pl_FacePlayer')
    c.jump_if_flag(FLAG, 1, on)
    c(f'    pl_msg_talk {L("off_ask")}', '    YesNoWin PL_TMP', '    WorkCmpConst PL_TMP, 0',
      f'    VMJumpIf CMP_EQ, {yes_off}')
    c.msg_end(L('off_no'), talk=True)
    c.at(yes_off)
    c(f'    FlagSet {FLAG}')
    c.msg_end(L('off_yes'), talk=True)
    c.at(on)
    c(f'    pl_msg_talk {L("on_ask")}', '    YesNoWin PL_TMP', '    WorkCmpConst PL_TMP, 0',
      f'    VMJumpIf CMP_EQ, {yes_on}')
    c.msg_end(L('on_no'), talk=True)
    c.at(yes_on)
    c(f'    FlagReset {FLAG}')
    c.msg_end(L('on_yes'), talk=True)
    return c.out
