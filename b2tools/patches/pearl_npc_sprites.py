"""Pearl's own overworld sprites for people who had Black 2 stand-ins (user 2026-10-19: "give rowan his sprite and the
moms there actual sprites from diamond and peral"). Run after pearl_player_sprites (both edit a/0/4/8).

Each Pearl sprite (the dump's data/mmodel/mmodel.narc, textures named <name>.N, 16 frames of 32 x 32: back, front,
left, right, 4 per direction: stand, step, stand, step) replaces the sheet of the Black 2 object code that
data/pearl_sprite_map.json gives its graphics id. Each of these codes is used by that one Pearl sprite only (checked
here), so nothing else changes look:
- Rowan (SPRITE_DOCTOR, mmodel 94) -> code 180, Black 2's unused white-bearded old man: 12 frames, 3 per direction
  (stand, step, step) = Pearl 0, 1, 3 of each direction (as pearl_player_sprites' walk sheet).
- Mom (SPRITE_MAMA, mmodel 119) -> code 251, Black 2's Mom: 7 frames = back stand, back step, front stand, front step,
  side stand, side step, side step (Black 2 mirrors the other side and the other step) = Pearl 0, 1, 4, 5, 8, 9, 11.
- Barry (SPRITE_RIVEL, mmodel 127) -> code 291, Black 2's Hugh (user 2026-10-19: "hughs sprite needs to be changed
  to barrys asap"): 17 frames, the 12 walking frames as Rowan's, then 5 poses only Black 2's own story plays (Pearl's
  scripts never ask for them) -> Pearl's standing frames (left, right, front x3).
- Barry's mom has no sprite of her own in Pearl: she is SPRITE_MIDDLEWOMAN1 (mmodel 15), as are Pearl's other 24
  middle-aged women, which Black 2 showed as its Pokéfan (code 26, 7 frames): all 25 now look as in Pearl.
- Rowan's briefcase at Lake Verity (SPRITE_BAG, mmodel 153 'bag', one frame) -> code 208, Black 2's gift box (user
  2026-10-20: "make the suitcase in the opening actually look like a suitcase instead of a present"): a one-frame
  32 x 32 object no Black 2 zone or script uses (HoennB2 put Birch's bag on the same sheet); Pearl's lowest row 29
  moves to 30, the box's.
- Team Galactic (user 2026-10-25: "why are the team galactic folks using team plasma sprites lets switch those over
  to their actual sprites please"), 12 frames each as Rowan's:
  - Grunts (SPRITE_GINGAM / GINGAW, mmodel 103 'gingam' / 104 'gingaw') -> codes 293 / 294, Black 2's Team Plasma
    grunts: only Unova's story places them (Plasma zones, the PWT's opening scene with Cheren); no Sinnoh zone.
  - Cyrus (SPRITE_GINGABOSS, mmodel 99 'gingaboss') -> code 94, Black 2's Grimsley (the Unova League rooms only).
  - Mars (SPRITE_GKANBU1, mmodel 100 'gkanbu1') -> code 90, Skyla's Black 1 sheet (no Black 2 zone, script or table).
  - Jupiter (SPRITE_GKANBU3, mmodel 102 'gkanbu3') -> code 102, a placeholder sheet (a cross; nothing uses it).
  - Saturn (SPRITE_GKANBU2, mmodel 101 'gkanbu2') -> code 92, Iris's Black 1 sheet (nothing uses it). His old
    stand-in 178 (Cress) stays Cress: the PWT's Unova Leaders tournament shows it (a/2/4/7 record 10), and the PWT
    goes into Sinnoh's Battle Frontier (DECISIONS 2026-10-25).
  None of these codes is in the PWT's table (a/2/4/7, checked here), Black 2's battle-facility class table
  (ov012 BtlInst_GetTrainerClassObjCode), its Union Room looks (union_view.c) or named in its C (pokebw2_latest).
- The Elite Four, the battle partners and Palmer (2026-10-25, DECISIONS: named Diamond/Pearl characters without an
  official Black 2 sprite use Pearl's own), 12 frames each as Rowan's. Their stand-ins (Cilan 85 and Chili 179, which
  the PWT's table shows; Shauntal 93; Black 2 people on shared codes 29, 32, 35, 53; Benga 304, 299, 358) gave way to
  codes of their own that no kept Black 2 zone uses: no Black 2 zone, script, table or C at all for 87, 88, 106
  (Black 1 leader sheets and an unused man), 122 and 373 (unused walking Keldeo); 289 (a Nimbasa script's only), 99,
  300 (Driftveil's), 107 (Nimbasa's) and 207 (two Unova zones'), all now Sinnoh zones:
  Aaron (SPRITE_BIGFOUR1, mmodel 113) -> 87, Bertha (BIGFOUR2, 114) -> 88, Flint (BIGFOUR3, 115) -> 106, Lucian
  (BIGFOUR4, 116) -> 122, Cheryl (SEVEN1, 120) -> 373, Riley (SEVEN2, 121) -> 289, Marley (SEVEN3, 122) -> 99, Buck
  (SEVEN4, 123) -> 107, Mira (SEVEN5, 124) -> 300, Palmer (TOWERBOSS, 148) -> 207. Each is a 12-frame walker (scene
  node 2, controller 3, 32 x 32, as the Galactic codes). Checked here as Team Galactic's: one Pearl sprite per code,
  none in the PWT's table.
- Professor Oak (SPRITE_OOKIDO 166, mmodel 145 'ookido'; Sandgem lab, Eterna, Pal Park, Route 224 after the League;
  2026-10-25, the world sprite pass) had Cedric Juniper (104) -> code 89, Black 1's Clay sheet (12 frames): no Black
  2 zone, script (res/field events and scripts), table (PWT a/2/4/7, ov012 BtlInst_GetTrainerClassObjCode,
  union_view.c) or C names it.
- The Galactic HQ door (SPRITE_GINGA_DOOR 202: one half of a sliding door, two per doorway, which Pearl's scripts slide
  aside with WalkFast and remove; mmodel 369 'ginga_door', a 16 x 32 texture with its own billboard model) -> code
  292, a one-frame 32 x 32 ball no Black 2 zone, script or table uses (Black 2's billboards are 32 x 32, 16 x 16 or
  64 x 64: fldmmdl_drawdata.c): Pearl's 16 x 32 picture in the middle columns 8-23, the width of the door's own tile,
  rows 0-31 as Pearl's. The door's colour 0 is opaque in Pearl (22 pixels: its top edge) and transparent in a Black 2
  sheet, so those pixels take a spare colour slot with the same colour. As Pearl's door (pokeplatinum
  object_event_gfx_data.c: no shadow, no reflection), code 292's record (a/0/4/7) gets shadow and reflections off.
- Pearl's field objects (lead 2026-10-25, the user's art rule; they had Black 2 stand-ins), one picture each
  (OBJECTS), on every frame of their sheet: the Rock Smash rock (SPRITE_BREAKROCK 85, mmodel 83 'breakrock') ->
  code 186, the Moss Rock (190, mmodel 168 'moss') -> 371, the Ice Rock (191, mmodel 169 'freezes') -> 188, the
  bollard (SPRITE_POLE 192, mmodel 170 'pole') -> 189: codes no Black 2 zone, script (res/field events and ActorNew),
  table (PWT, battle facilities, Union Room) or C names (186: a one-frame object; 371: a numbered test sheet; 188, 189:
  two of Black 1's Sages); and the Cut tree (SPRITE_TREE 86, mmodel 84 'tree') -> code 108, Black 2's own Cut tree,
  because the party menu's Cut needs that code in front of the player (ov012 hiden_event.c: objCode ==
  OBJ_CODE_108); its Black 2 users are Unova routes whose zones Sinnoh's maps took (route 2, 13, 16, 23, Dreamyard,
  Victory Road 18, Virbank Complex 2) and White Treehollow. Pearl's 16 x 16 rocks sit in the 32 x 32 frame where
  Black 2 draws its own one-tile rock (code 206: columns 9-22, rows 17-30, centred, standing on row 30); the 32 x 32
  tree and bollard keep their place, 1 pixel lower as the people. Pearl's palettes have 8 or 16 colours (the rest 0).
- Pearl's Strength boulder (SPRITE_ROCK 84, mmodel 82 'rock', 16 x 16, one tile; lead 2026-10-26, DECISIONS) ->
  code 109, Black 2's own 1 x 1 Strength rock (OBJ_CODE_STRENGTH_ROCK): Black 2's Strength code already takes it as a
  boulder (ov012 fldmmdl.c IsNPCStrengthRock) and reads the footprint from its record (collWidth/Height 1: ov036
  StrengthRockSpaceCheck, ov012 field_actor_tool.c CheckBlockedCollPathToPosition / CheckAreaOverActor), so no C
  change. In Black 2 its record is type "none" (invisible, no sheet) and no zone or script places it. It gets the
  record of code 101 (a Black 1 Sage, 7 frames, scene node 2, controller 2, shadow and reflection on as Pearl's
  boulder; no Black 2 zone, script, work value, table or C names 101) with uid 109, no gender, 1 x 1, and 101's sheet
  gets Pearl's boulder on every frame, placed as the Rock Smash rock. 101 itself stays unused. Black 2's own 2 x 2
  boulders (3D 8195 / 8197) are untouched.
Pearl's frames sit 1 pixel higher in the box than Black 2's (feet on row 29 / 30): moved down 1, as the player's.
Each sheet takes the Pearl sprite's 16 colours.

Platinum (2026-11-07, step 6, plat-sprites; the user 2026-11-03: Platinum's new characters use Platinum's own sprites
from the dump, pixel for pixel). A Platinum build reads data/platinum/sprite_map.json over Pearl's map, and also does
this:
- The people Platinum redrew (Platinum's mmodel.narc against Pearl's: members 0-375 are byte for byte Pearl's except the
  player's sheets, Barry 127, Palmer 148, Buneary 373 and Happiny 374): Barry and Palmer come from Platinum's dump
  (PLATINUM_REDRAWN), on their Pearl codes; Buneary and Happiny the same way in pearl_amity_sprites. Every other row
  reads Pearl's dump, whose members are the same pixels (Platinum moved the models after 375, so Pearl's numbers).
- Platinum's new people and objects (PLATINUM_PEOPLE: Looker, Charon, Croagunk, the four attendants, the game director,
  Rotom's five appliances), 16 frames each like Pearl's people, on 12-frame 32 x 32 walker codes nothing in Black 2
  names (b2tools/plat_sprites_check.py --codes lists them: no kept zone, script, table or C). Codes whose record draws
  them another way (scene node 5, 15 or 20: Black 2's turning and rail figures) get the record of an ordinary walker
  (WALKER_TEMPLATE, code 317: node 2, controller 3, shadow on), keeping their own sheet. Rotom's appliances are
  Platinum's red appliance sheets (mmodel 400-404, the ones its Rotom's Room shows; 406-410 are the plain grey ones
  nothing shows): 16 equal frames, so every frame is the same picture.
- Platinum's 3D and wide objects (PLATINUM_MODELS), as Black 2 3D-model actors (type 2, scene node 12: drawn at the
  actor's place, no turning, as Platinum draws them), each with the record of code 0x2007 (MODEL_TEMPLATE, a 1 x 1
  drawn model: pearl_e4_doors copies it too) and its model appended to a/0/4/8: the book (fldeff 79 'book02', a
  book lying on a table) and the wall before Rotom's Room (fldeff 149), byte for byte; the Galactic HQ hall's grunt
  crowds of 4 and 3 (mmodel 441 and 444: billboard models with their 128 x 32 and 64 x 32 pictures, which no Black 2
  billboard (32, 16 or 64 square) holds; their own billboard command turns them to the camera). Platinum draws the
  crowd 1 unit per pixel, as its single grunts; Black 2 draws people 28 units per 32 pixels, so as one picture the
  crowd's grunts would stand a seventh taller and wider than the single grunts among them. crowd_model gives each
  grunt of the picture (CROWD_GRUNTS: its columns) a quad of its own at Black 2's person scale on its tile: the
  same picture, texture, node and material, Black 2's people's size. The cave painting's shards (mmodel 442 and 443:
  two halves of one 64 x 32 picture lying on the floor, one per object, two tiles apart, always shown together) are
  one model on the left object (both quads, posScale 8 so the right half's x of 48 fits); the right object is Black
  2's invisible blocker 185, solid and talkable as Platinum's. Codes: 0x2000, 0x2001, 0x2006, 0x2007 and 0x2008, which no kept Black 2
  zone, script or C places (0x2003-0x2005 are Strength boulders, 0x2002 Pearl's League doors, 0x2009 and 0x200A
  Black 2's kept zones'). 0x2007 only changes its model file, so pearl_e4_doors' check of its record still holds.
Pearl's and Diamond's builds do none of this (version_check.py; plat_sprites_check.py --versions compares their
a/0/4/7 and a/0/4/8 with the base).
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import narcio, sprites  # noqa: E402
from pearl_player_sprites import MMODEL, shift, SHIFT_DOWN  # noqa: E402

# (who, Pearl graphics id, Pearl mmodel file, texture name)
PEOPLE = [('Rowan', 99, 94, 'doctor'), ('Mom', 140, 119, 'mama'), ("Barry's mom (and Pearl's middle-aged women)",
                                                                   16, 15, 'middlewoman1'),
          ('Barry', 148, 127, 'rivel'), ("Rowan's briefcase", 174, 153, 'bag'),
          ('Cyrus', 120, 99, 'gingaboss'), ('Mars', 121, 100, 'gkanbu1'), ('Saturn', 122, 101, 'gkanbu2'),
          ('Jupiter', 123, 102, 'gkanbu3'), ('Galactic grunt (M)', 124, 103, 'gingam'),
          ('Galactic grunt (F)', 125, 104, 'gingaw'),
          ('Aaron', 134, 113, 'bigfour1'), ('Bertha', 135, 114, 'bigfour2'), ('Flint', 136, 115, 'bigfour3'),
          ('Lucian', 137, 116, 'bigfour4'), ('Cheryl', 141, 120, 'seven1'), ('Riley', 142, 121, 'seven2'),
          ('Marley', 143, 122, 'seven3'), ('Buck', 144, 123, 'seven4'), ('Mira', 145, 124, 'seven5'),
          ('Palmer', 169, 148, 'towerboss'), ('Professor Oak', 166, 145, 'ookido')]
GALACTIC = {120, 121, 122, 123, 124, 125, 202}       # graphics ids whose codes must stay out of the PWT's table
NAMED = {134, 135, 136, 137, 141, 142, 143, 144, 145, 169, 166}   # the Elite Four, the partners, Palmer, Oak: the same check
# Pearl's Galactic HQ door: (who, graphics id, mmodel file, texture name), its 16 x 32 picture at (DOOR_X, 0)
DOOR = ('Galactic HQ door', 202, 369, 'ginga_door')
# Pearl's field objects: (what, graphics id, mmodel file, texture name), one picture on every frame of their code's sheet
OBJECTS = [('Rock Smash rock', 85, 83, 'breakrock'), ('Moss Rock', 190, 168, 'moss'), ('Ice Rock', 191, 169, 'freezes'),
           ('bollard', 192, 170, 'pole'), ('Cut tree', 86, 84, 'tree'), ('Underground vent', 182, 161, 'venthole')]
# Pearl's snowball (OBJ_EVENT_GFX_SNOWBALL 118, Candice's Gym; 2026-11-01) is a 3D object in Pearl, one card tilted to the
# camera (mmodel 381 / fldeff 78 'gym06_o1') with texture frames r09_o01.1-4, whole and breaking: its whole frame on code 144's
# one-frame sheet, no reflection, as Pearl's. Black 2 removes the actor when it breaks (no break frames, as before).
SNOWBALL = ('snowball', 118, 381, 'r09_o01.1')
# Pearl's Strength boulder: (what, graphics id, mmodel file, texture name), its code (Black 2's 1 x 1 Strength rock)
# and the code whose record and sheet it takes
BOULDER = ('Strength boulder', 84, 82, 'rock')
STRENGTH_ROCK, BOULDER_SHEET = 109, 101
ROCK_BOX = (9, 22, 30)                               # code 206's rock: columns 9-22, bottom row 30 (a one-tile object)
# Pearl's legendary Pokémon of the story (2026-10-26, chapter 7; the user's art rule): (who, graphics id, mmodel file,
# texture name): Pearl's two frames (a flutter, facing the player) on each frame pair of Black 2's own sheet for the
# species (6 frames: 0-1, 2-3 and 4-5 are its three ways; the same size as Pearl's), Pearl's colours, pixel for pixel
# (their lowest rows match Black 2's: Palkia's both 62). Turned up or sideways they show their front, as Pearl's do.
POKEMON = [('Palkia', 155, 134, 'sppoke5'), ('Uxie', 151, 130, 'sppoke1'), ('Mesprit', 152, 131, 'sppoke2'),
           ('Azelf', 153, 132, 'sppoke3'), ('Dialga', 154, 133, 'sppoke4')]
# Dialga shows in Adamant Diamond's Spear Pillar, and (postdex, 2026-11-09) in Lustrous Pearl's after the Hall of Fame as
# the other version's legendary (b2tools/postgame_legend.py): a Pearl build takes Pearl's own Dialga too (the dump's
# pixels, as Diamond's; Black 2's sheet before). Platinum keeps its own.
POKEMON_ONLY_IN = {'Dialga': ('diamond', 'pearl')}
# Pearl draws the lake trio 24 units above their tile, wherever they are (pokediamond ov05_021F0514.s: graphics ids
# 0x97-0x99 take the draw table ov05_021F8D1C, whose init ov05_021F1BD0 sets the sprite offset (0, 24, 0);
# pokeplatinum ov5_021ECB34, MapObject_SetSpritePosOffset): in the Galactic HQ lab they float in the containment
# units' chamber (its floor 20 units up, behind the orange glass), in the caverns over the ground. Black 2's record
# offset (FieldActorConfig.wPosOffsetY, whole units: CopyActorPosAllAdd) does the same for the billboard; its shadow
# would go up with it (fldeff_shadow.c adds the offset), Pearl's stays on the ground (its shadow takes the object's
# position): no shadow for them (2026-10-26).
FLOAT_Y = {'Uxie': 24, 'Mesprit': 24, 'Azelf': 24}
# In the Galactic HQ lab, 16 instead (user 2026-10-26: "tune the lab only so Uxie, Mesprit and Azelf's heads stay inside
# the units"): Black 2's camera is lower than Pearl's and its sprite passes geometry up to ~9 units nearer, so at 24
# their heads (Pearl's art fills rows 1-30 of 32: 25 units) show over the domes, which Pearl's look hides (offline,
# room_look_check from four tiles: heads inside from 16 down, bodies still behind the glass; work/agents/labtrio).
# The lab's objects take codes of their own (data/pearl_sprite_map.json "zone_codes": 156-158, Black 2 codes no zone,
# script, table or C names), each a copy of the species' record (its sheet, no shadow) with this offset.
ZONE_FLOAT_Y = {'MAP_VEILSTONE_GALACTIC_HEADQUARTERS_4F_BACK': 16}
# Mt. Coronet 2F's wall with the cave painting (SPRITE_T5_O01_C 203, mmodel 370, 2026-10-26, chapter 7): it stands on
# the mat to the upper mountain until the lake trio are freed (flag 0x253); Pearl's two 64 x 32 textures, the bricks
# and the painting of the three over them, as one 64 x 32 picture at the bottom of a 64 x 64 frame. Code 4637 (Black
# 2's Giratina Origin Forme walker, 6 frames of 64 x 64: no Black 2 zone, script or Pearl place shows it; Pearl's
# Giratina is the Altered Forme, 4636), every frame the same picture, no shadow or reflection (a wall).
WALL = ('cave-painting wall', 203, 370, ('t5_o01_c', 't5_o01_c_'))
DOOR_X = 8
ARC_PWT = 247                                        # a/2/4/7: the PWT's trainers, u16 x 8 records, object code at +2
# Platinum: the people Platinum redrew, by graphics id (read from Platinum's dump; same mmodel member as Pearl's)
PLATINUM_REDRAWN = {148: 'Barry', 169: 'Palmer'}
# Platinum's new people and objects: (who, graphics id, Platinum mmodel file, texture name), 16 frames each
PLATINUM_PEOPLE = [('Looker', 213, 376, 'icpo'), ('Charon', 214, 377, 'gkanbu4'), ('Croagunk', 229, 392, 'gureggru'),
                   ('Frontier attendant (singles)', 231, 394, 'bfsm'), ('Frontier attendant (multis)', 232, 395, 'bfsw1'),
                   ('Frontier attendant (booths)', 233, 396, 'bfsw2'), ('Wi-Fi Plaza attendant', 235, 398, 'wifisf'),
                   ("Rotom's microwave oven", 237, 400, 'rotomf'), ("Rotom's fan", 238, 401, 'rotoms'),
                   ("Rotom's refrigerator", 239, 402, 'rotomi'), ("Rotom's washing machine", 240, 403, 'rotomw'),
                   ("Rotom's lawn mower", 241, 404, 'rotomg'), ('game director', 242, 405, 'director'),
                   # (plat-frontier-rooms) the Frontier Brains: the Frontier's scenes set their look by graphics id
                   ('Thorton', 215, 378, 'brains1'), ('Argenta', 216, 379, 'brains2'), ('Darach', 217, 380, 'brains3'),
                   ('Dahlia', 218, 381, 'brains4'), ('Caitlin', 219, 382, 'princess')]   # (the Castle's corridor)
WALKER_TEMPLATE = 317                                # an ordinary 12-frame walker record (node 2, controller 3, shadow)
WALKER_NODES = {2, 5, 15, 20}                        # 12-frame records that become one (5, 15, 20: their record changes)
WALK12 = [d * 4 + k for d in range(4) for k in (0, 1, 3)]
# Platinum's 3D and wide objects: (what, graphics id, Platinum narc, member(s), texture name)
FLDEFF = 'data/mmodel/fldeff.narc'
PLATINUM_MODELS = [('Galactic grunts (4)', 248, MMODEL, 441, 'gset1'), ('Galactic grunts (3)', 249, MMODEL, 444, 'gset2'),
                   ("the cave painting's shards", 250, MMODEL, (442, 443), 't5_o02_c'),
                   ('book', 183, FLDEFF, 79, 'book02'), ("the wall before Rotom's Room", 262, FLDEFF, 149, 'm_dun26_38')]
MODEL_TEMPLATE = 0x2007                              # OBJ_CODE_MODEL_TR_GRASS: a 1 x 1 model record Black 2 draws
MODEL_RECORD = (2, 12, 0, 0, 0, 0, 0, 0, 2, 1, 1, 0, 0, 0)   # its bytes 2-15 (type .. offsets: sprites.ow_table)
FREE_MODELS = {0x2000, 0x2001, 0x2006, 0x2007, 0x2008}   # model codes no kept Black 2 zone, script or C places
SHARDS_POS_SCALE = 8                                 # the shards' combined model: x -16 .. 48 is -2 .. 6 at 8
SHARDS_DX = 32                                       # the right shard's object, 2 tiles east of the left one's
# The Galactic crowds (crowd_model): each grunt's (tile east of the object, first and last column of the picture). The
# pictures are copies of the grunts' own back view (mmodel 103 / 104, frame 1) at 16-pixel steps, the left pair 1 pixel
# right of where Platinum places a person, touching at one column (b2tools/plat_sprites_check.py checks it): that
# column goes to the grunt drawn in it (gset1's column 16 is the same in both, its column 63 shows the man's 5 of 6
# pixels; gset2's column 16 is the woman's).
CROWD_GRUNTS = {248: [(-3, 0, 16), (-2, 17, 32), (0, 47, 62), (1, 63, 79)], 249: [(1, 0, 15), (2, 16, 32), (4, 47, 63)]}
# Black 2 draws a person's 32 x 32 frame as a camera-facing quad 28 units wide and tall, its bottom 1.58 units under the
# feet at the field camera's 52.6 degree pitch (fieldmap.c Field_CalcActorYOffset: cos(pitch) * 4 - 4; measured in
# HoennB2, b2tools/pearl_rooms_view.py), and its frames sit 1 row lower than Platinum's (SHIFT_DOWN)
PERSON_SCALE = 28 / 32
PERSON_BOTTOM = -1.58 - SHIFT_DOWN * PERSON_SCALE
LAYOUT = {1: [0], 12: [d * 4 + k for d in range(4) for k in (0, 1, 3)],
          7: [0, 1, 4, 5, 8, 9, 11],
          # Hugh's sheet: the 12 walking frames, then 5 poses only Black 2's own story uses -> Pearl's standing frames
          17: [d * 4 + k for d in range(4) for k in (0, 1, 3)] + [8, 12, 4, 4, 4]}


def pearl_object(btx):
    """A Pearl one-picture object as a Black 2 32 x 32 frame: (indices, 16 BGR555 colours). Pearl's object palettes
    can hold fewer than 16 colours (sprites.btx_decode reads 16)."""
    import struct
    (name, w, h, off), = sprites.btx_layout(btx)[0]
    poff = sprites.btx_layout(btx)[2]
    n = min(16, (len(btx) - poff) // 2)
    pal = list(struct.unpack_from(f'<{n}H', btx, poff)) + [0] * (16 - n)
    pix = sprites.unpack4(btx[off:off + w * h // 2], w * h)
    assert max(pix) < n, name
    ys = [i // w for i, v in enumerate(pix) if v]
    xs = [i % w for i, v in enumerate(pix) if v]
    if (w, h) == (16, 16):                           # a one-tile object: where Black 2 draws its own rock (206)
        x0, x1, bottom = ROCK_BOX
        dx = round((x0 + x1) / 2 - (min(xs) + max(xs)) / 2)
        dy = bottom - max(ys)
    else:
        assert (w, h) == (32, 32), name
        dx, dy = 0, SHIFT_DOWN
    out = bytearray(32 * 32)
    for i, v in enumerate(pix):
        if v:
            x, y = i % w + dx, i // w + dy
            assert 0 <= x < 32 and 0 <= y < 32, name
            out[y * 32 + x] = v
    return bytes(out), pal


def btx_textures(btx):
    """{texture name: (w, h, 4 bpp indices, 16 BGR555 colours)} of a Pearl BTX0 whose textures each have a palette of
    their own, named texture + '_pl' (mmodel 370)."""
    t0 = btx.find(b'TEX0')
    t = btx[t0:]
    paldict, paldata = struct.unpack_from('<II', t, 0x34)
    pals = dict(sprites._dict(t, paldict))
    out = {}
    for name, ent in sprites._dict(t, struct.unpack_from('<H', t, 0xE)[0]):
        p = struct.unpack_from('<I', ent, 0)[0]
        fmt, w, h = p >> 26 & 7, 8 << (p >> 20 & 7), 8 << (p >> 23 & 7)
        assert fmt == 3, (name, fmt)
        off = t0 + struct.unpack_from('<I', t, 0x14)[0] + ((p & 0xffff) << 3)
        po = t0 + paldata + (struct.unpack_from('<H', pals[name + '_pl'], 0)[0] << 3)
        n = min(16, (len(btx) - po) // 2)
        out[name] = (w, h, sprites.unpack4(btx[off:off + w * h // 2], w * h),
                     list(struct.unpack_from(f'<{n}H', btx, po)) + [0] * (16 - n))
    return out


def pearl_wall(mm):
    """Pearl's cave-painting wall as a 64 x 64 frame: (indices, 16 BGR555 colours): the bricks (all opaque), the
    painting's opaque pixels over them (its colours after the bricks' in the palette), at the bottom of the frame."""
    _, _, mid, (bricks, painting) = WALL
    tex = btx_textures(mm[mid])
    w, h, bp, pal = tex[bricks]
    w2, h2, pp, ppal = tex[painting]
    assert (w, h, w2, h2) == (64, 32, 64, 32), (w, h, w2, h2)
    pal = list(pal)
    used = sorted(set(bp) - {0})
    nxt = max(used) + 1
    remap = {}
    for v in sorted(set(pp) - {0}):
        remap[v] = nxt
        pal[nxt] = ppal[v]
        nxt += 1
    opaque0 = nxt                                   # the bricks' colour 0 is opaque in Pearl (its texture's
    pal[opaque0] = pal[0]                           # "colour 0 transparent" bit is off; the painting's is on), as
    nxt += 1                                        # the HQ door's: its pixels take a slot of their own
    assert nxt <= 16, nxt
    out = bytearray(64 * 64)
    for i in range(w * h):
        out[(64 - h) * 64 + i] = remap[pp[i]] if pp[i] else (bp[i] or opaque0)
    return bytes(out), pal


def pearl_snowball(bmd, tex):
    """Pearl's snowball card, its whole frame: (32 x 32 indices, 16 BGR555 colours), its lowest row on the frame's row
    30 as the one-tile objects."""
    from pearl_player_sprites import model_textures
    _, texs, pals = model_textures(bmd)
    w, h, fmt, off = texs[tex]
    assert (w, h, fmt) == (32, 32, 3), (tex, w, h, fmt)
    pix = sprites.unpack4(bmd[off:off + w * h // 2], w * h)
    poff = next(pals[n] for n in (tex + '_pl', tex.rsplit('.', 1)[0] + '_pl', tex) if n in pals) if len(pals) > 1 \
        else next(iter(pals.values()))
    n = min(16, (len(bmd) - poff) // 2)              # (Pearl's object palettes can hold fewer than 16 colours)
    pal = list(struct.unpack_from(f'<{n}H', bmd, poff)) + [0] * (16 - n)
    assert max(pix) < n, tex
    bottom = max(i // w for i, v in enumerate(pix) if v)
    dy = ROCK_BOX[2] - bottom
    out = bytearray(w * h)
    for i, v in enumerate(pix):
        if v:
            y = i // w + dy
            assert 0 <= y < h, tex
            out[y * w + i % w] = v
    return bytes(out), pal


def sprite_map():
    """{graphics id (str): row}: data/pearl_sprite_map.json, with Platinum's own rows over it in a Platinum build."""
    import version
    smap = json.load(open(os.path.join(ROOT, 'data', 'pearl_sprite_map.json'), encoding='utf-8'))
    if version.PLATINUM:
        smap.update({k: v for k, v in json.load(open(os.path.join(ROOT, 'data', 'platinum', 'sprite_map.json'),
                                                     encoding='utf-8')).items() if k != '_doc'})
    return smap


def bmd_blocks(b):
    """{block magic: block bytes} of a BMD0 (MDL0, TEX0), and its header's version."""
    assert b[:4] == b'BMD0', b[:4]
    n = struct.unpack_from('<H', b, 0xE)[0]
    out = {}
    for k in range(n):
        o = struct.unpack_from('<I', b, 0x10 + 4 * k)[0]
        out[b[o:o + 4].decode()] = b[o:o + struct.unpack_from('<I', b, o + 4)[0]]
    return out, struct.unpack_from('<H', b, 6)[0]


def bmd_join(blocks, ver):
    """A BMD0 of the blocks (bytes, in order), each at a 4-aligned offset."""
    at = 0x10 + 4 * len(blocks)
    offs, body = [], b''
    for blk in blocks:
        body += bytes(-(at + len(body)) % 4)
        offs.append(at + len(body))
        body += blk
    size = at + len(body)
    return b'BMD0' + struct.pack('<HHIHH', 0xFEFF, ver, size, 0x10, len(blocks)) + struct.pack(f'<{len(blocks)}I', *offs) + body


def model_texture(bmd):
    """(name, w, h, 4 bpp indices, 16 BGR555 colours, colour 0 clear) of a BMD0's one texture."""
    blocks, _ = bmd_blocks(bmd)
    t = blocks['TEX0']
    (name, ent), = sprites._dict(t, struct.unpack_from('<H', t, 0xE)[0])
    p = struct.unpack_from('<I', ent, 0)[0]
    fmt, w, h, clear = p >> 26 & 7, 8 << (p >> 20 & 7), 8 << (p >> 23 & 7), p >> 29 & 1
    assert fmt == 3, (name, fmt)
    off = struct.unpack_from('<I', t, 0x14)[0] + ((p & 0xffff) << 3)
    paldict, paldata = struct.unpack_from('<II', t, 0x34)
    (_, pent), = sprites._dict(t, paldict)
    po = paldata + (struct.unpack_from('<H', pent, 0)[0] << 3)
    n = min(16, (len(t) - po) // 2)                  # (a model's palette can hold fewer than 16 colours)
    pal = list(struct.unpack_from(f'<{n}H', t, po)) + [0] * (16 - n)
    return name, w, h, sprites.unpack4(t[off:off + w * h // 2], w * h), pal, clear


def node_srt(model):
    """(translation, scale) of a one-node model (pearl_mesh.Model), in map units; no rotation."""
    import pearl_mesh
    d, base = model.data, model.m + 0x40
    (at, _), = pearl_mesh._ndict(d, base)
    p = base + struct.unpack_from('<I', d, at)[0]
    flag = struct.unpack_from('<H', d, p)[0]
    assert flag & 2 and not flag & 8, f'node flags {flag:#x}: a rotation'
    q, tr, sc = p + 4, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
    if not flag & 1:
        tr = tuple(v / 4096 for v in struct.unpack_from('<3i', d, q)); q += 12
    if not flag & 4:
        sc = tuple(v / 4096 for v in struct.unpack_from('<3i', d, q))
    return tr, sc


def one_block_model(mdl0, ver):
    import pearl_mesh
    return pearl_mesh.Model(bmd_join([mdl0], ver))


def shards_model(mm, left, right):
    """Platinum's two cave-painting shard models (each one quad on the floor with half of the same picture) as one model
    for the left object: the right quad SHARDS_DX east, at posScale SHARDS_POS_SCALE, the left model's node and material,
    the picture's TEX0 (the two are byte for byte the same)."""
    import pearl_mesh
    (bl, ver), (br, _) = bmd_blocks(mm[left]), bmd_blocks(mm[right])
    assert bl['TEX0'] == br['TEX0'], 'the two shards have different pictures'
    ml, mr = one_block_model(bl['MDL0'], ver), one_block_model(br['MDL0'], ver)
    (tl, sl), (tr, sr) = node_srt(ml), node_srt(mr)
    assert tl == tr and sl == (1.0, 1.0, 1.0), (tl, sl, tr, sr)
    assert len(ml.shapes) == len(mr.shapes) == 1 and len(ml.materials) == len(mr.materials) == 1
    ma, mb = ml.data[ml.mat_at[0]:ml.mat_at[0] + 44], mr.data[mr.mat_at[0]:mr.mat_at[0] + 44]
    assert ma == mb, 'the two shards have different materials'
    (kind, (ql,)), = ml.shapes[0].groups
    (kind2, (qr,)), = mr.shapes[0].groups
    assert kind == kind2 == pearl_mesh.QUADS
    def world(v, ps, s, dx=0):             # map units, without the node's translation (kept by the node)
        return [v[k] / 4096 * ps * s[k] + (dx if k == 0 else 0) for k in range(3)]
    quads = [[world(v, ml.pos_scale, sl) + list(v[3:]) for v in ql],
             [world(v, mr.pos_scale, sr, SHARDS_DX) + list(v[3:]) for v in qr]]
    # the left model at the new scale: its posScale, invPosScale (NNSG3dResMdlInfo +8, +12)
    d = bytearray(ml.data)
    struct.pack_into('<ii', d, ml.m + 28, SHARDS_POS_SCALE << 12, 4096 // SHARDS_POS_SCALE)
    m = pearl_mesh.Model(bytes(d))
    assert m.pos_scale == SHARDS_POS_SCALE
    polys = []
    for q in quads:
        poly = []
        for x, y, z, s, t, n, c in q:
            raw = [round(c_ / SHARDS_POS_SCALE * 4096) for c_ in (x, y, z)]
            assert all(-32768 <= r < 32768 for r in raw), raw
            poly.append(pearl_mesh.Vertex(*raw, s, t, n, c))
        polys.append(poly)
    m.shapes[0].groups = [(pearl_mesh.QUADS, polys)]
    out = bytearray(m.encode())
    struct.pack_into('<4H', out, m.m + 36, 8, 2, 0, 2)    # numVertex, numPolygon, numTriangle, numQuad
    blocks, _ = bmd_blocks(bytes(out))
    return bmd_join([blocks['MDL0'], bl['TEX0']], ver)


def crowd_model(bmd, grunts):
    """Platinum's Galactic crowd (one picture of 3 or 4 grunts on neighbouring tiles; Platinum draws it 1 unit per pixel,
    as its people) the way Black 2 draws people: each grunt's columns of the picture (grunts: CROWD_GRUNTS) on a quad of
    its own, PERSON_SCALE units per pixel around its tile's centre, its bottom PERSON_BOTTOM under the feet. Every pixel
    and the texture stay Platinum's; so do the model's node (its billboard command) and material."""
    import pearl_mesh
    blocks, ver = bmd_blocks(bmd)
    m = one_block_model(blocks['MDL0'], ver)
    (kind, (q,)), = m.shapes[0].groups
    xs, us = [v[0] / 4096 * m.pos_scale for v in q], [v[3] / 16 for v in q]
    x0, u0 = min(xs), us[xs.index(min(xs))]
    assert max(xs) - x0 == max(us) - min(us) and kind == pearl_mesh.QUADS, 'the crowd\'s quad is not one texel per unit'
    n, c, ps = q[0][5], q[0][6], m.pos_scale
    polys = []
    for k, a, b in grunts:
        uc = 16 * k - x0 + u0                     # the column at the tile's centre (Platinum: 1 unit per texel)
        left, right = 16 * k + (a - uc) * PERSON_SCALE, 16 * k + (b + 1 - uc) * PERSON_SCALE
        bottom, top = PERSON_BOTTOM, PERSON_BOTTOM + 32 * PERSON_SCALE
        poly = []
        for x, y, s_, t in [(left, bottom, a, 32), (right, bottom, b + 1, 32), (right, top, b + 1, 0), (left, top, a, 0)]:
            raw = [round(v / ps * 4096) for v in (x, y, 0)]
            assert all(-32768 <= r < 32768 for r in raw), raw
            poly.append(pearl_mesh.Vertex(*raw, round(s_ * 16), round(t * 16), n, c))
        polys.append(poly)
    m.shapes[0].groups = [(pearl_mesh.QUADS, polys)]
    out = bytearray(m.encode())
    struct.pack_into('<4H', out, m.m + 36, 4 * len(polys), len(polys), 0, len(polys))
    blk, _ = bmd_blocks(bytes(out))
    return bmd_join([blk['MDL0'], blocks['TEX0']], ver)


def platinum_models():
    """{graphics id: (what, BMD0 bytes)} of PLATINUM_MODELS, from Platinum's dump."""
    import version
    from gen4rom import Rom, narc_members
    rom = Rom(version.SOURCE_DUMP)
    narcs = {n: narc_members(rom.read(n)) for n in {m[2] for m in PLATINUM_MODELS}}
    out = {}
    for who, gfx, narc, member, tex in PLATINUM_MODELS:
        bmd = shards_model(narcs[narc], *member) if isinstance(member, tuple) else \
            crowd_model(narcs[narc][member], CROWD_GRUNTS[gfx]) if gfx in CROWD_GRUNTS else narcs[narc][member]
        blocks, _ = bmd_blocks(bmd)
        assert list(blocks) == ['MDL0', 'TEX0'] and model_texture(bmd)[0] == tex, (who, list(blocks))
        out[gfx] = (who, bmd)
    return out


def platinum_people():
    """[(who, graphics id, 16 frames (32 x 32 indices) in Platinum's order, 16 BGR555 colours)] of PLATINUM_PEOPLE."""
    import version
    from gen4rom import Rom, narc_members
    mm = narc_members(Rom(version.SOURCE_DUMP).read(MMODEL))
    out = []
    for who, gfx, mid, tex in PLATINUM_PEOPLE:
        fr, _, pal = sprites.btx_decode(mm[mid])
        fr = sorted(fr, key=lambda f: int(f[0].split('.')[-1]))
        assert [f[0] for f in fr] == [f'{tex}.{k}' for k in range(1, 17)], (who, [f[0] for f in fr])
        assert all((f[1], f[2]) == (32, 32) for f in fr), who
        assert all(max(i // 32 for i, v in enumerate(f[3]) if v) + SHIFT_DOWN < 32 for f in fr), f'{who}: cut off'
        out.append((who, gfx, [f[3] for f in fr], pal))
    return out


def apply_platinum(files, sheets, table, own_code, pwt):
    """Platinum's new people (PLATINUM_PEOPLE) on their walker codes, its 3D and wide objects (PLATINUM_MODELS) as model
    actors; the codes from data/platinum/sprite_map.json (own_code checks each is its graphics id's alone)."""
    from collections import Counter
    res1 = Counter(r['res1'] for r in table)
    rec = narcio.load(files, sprites.ARC_OW_TABLE)
    t = bytearray(rec[0])
    def at(code): return 4 + 28 * sprites.obj_record(code)
    walker = bytes(t[at(WALKER_TEMPLATE) + 2:at(WALKER_TEMPLATE) + 16])
    assert struct.unpack_from('<14B', walker) == (1, 2, 1, 1, 1, 0, 22, 3, 2, 1, 1, 0, 0, 0), 'code 317 changed'
    done = []
    for who, gfx, frames, pal in platinum_people():
        code = own_code(who, gfx)
        r = table[code]
        assert code < 377 and code not in pwt, f'{who}: code {code} is not a free person code'
        assert res1[r['res1']] == 1, f'{who}: sheet {r["res1"]} of code {code} is shared'
        mine = bytearray(t[at(code) + 2:at(code) + 16])
        assert mine[1] in WALKER_NODES, (who, code, mine[1])
        assert mine[:1] + mine[2:8] + mine[9:] == walker[:1] + walker[2:8] + walker[9:], f'{who}: code {code}\'s record'
        lay, _, _ = sprites.btx_layout(sheets[r['res1']])
        assert len(lay) == 12 and all((w, h) == (32, 32) for _, w, h, _ in lay), who
        sheets[r['res1']] = sprites.btx_encode(sheets[r['res1']], [shift(frames[i], SHIFT_DOWN) for i in WALK12], pal)
        note = ''
        if mine[1] != 2:
            t[at(code) + 2:at(code) + 16] = walker
            note = f'; record of {WALKER_TEMPLATE} (was scene node {mine[1]})'
        done.append(f'{who} = code {code} (sheet {r["res1"]}{note})')
    model = bytes(t[at(MODEL_TEMPLATE) + 2:at(MODEL_TEMPLATE) + 16])
    assert struct.unpack_from('<14B', model) == MODEL_RECORD, 'code 0x2007 is no longer a 1 x 1 drawn model'
    for gfx, (who, bmd) in platinum_models().items():
        code = own_code(who, gfx)
        assert code in FREE_MODELS, f'{who}: code {code:#x} is not a free model code'
        assert struct.unpack_from('<HB', t, at(code)) == (code, 2), f'{who}: code {code:#x} is not a model record'
        index = len(sheets)
        sheets.append(bmd)
        t[at(code) + 2:at(code) + 16] = model
        struct.pack_into('<5H', t, at(code) + 16, index, *(0xFFFF,) * 4)
        done.append(f'{who} = code {code:#x} (a/0/4/8 file {index}, Platinum\'s model)')
    rec[0] = bytes(t)
    narcio.save(files, sprites.ARC_OW_TABLE, rec)
    return done


def pwt_codes(files):
    """Object codes the PWT's trainer table (a/2/4/7) shows."""
    t = narcio.load(files, ARC_PWT)[0]
    return {struct.unpack_from('<H', t, 16 * i + 2)[0] for i in range(len(t) // 16)}


def pearl_door(mm):
    """Pearl's HQ door half as a Black 2 frame: (32 x 32 indices, 16 BGR555 colours). Its texture is 4 bpp 16 x 32
    with colour 0 opaque (sprites.btx_decode takes only sheets whose colour 0 is clear): colour 0's pixels move to the
    first slot the door does not use, given colour 0's colour."""
    who, _, mid, tex = DOOR
    btx = mm[mid]
    t0 = struct.unpack_from('<I', btx, 0x10)[0]
    t = btx[t0:]
    assert t[:4] == b'TEX0', who
    (name, ent), = sprites._dict(t, struct.unpack_from('<H', t, 0xE)[0])
    p = struct.unpack_from('<I', ent, 0)[0]
    fmt, w, h = p >> 26 & 7, 8 << (p >> 20 & 7), 8 << (p >> 23 & 7)
    assert (name, fmt, w, h) == (tex, 3, 16, 32), (who, name, fmt, w, h)
    off = t0 + struct.unpack_from('<I', t, 0x14)[0] + ((p & 0xffff) << 3)
    pix = sprites.unpack4(btx[off:off + w * h // 2], w * h)
    paldict, paldata = struct.unpack_from('<II', t, 0x34)
    (_, pent), = sprites._dict(t, paldict)
    pal = list(struct.unpack_from('<16H', btx, t0 + paldata + (struct.unpack_from('<H', pent, 0)[0] << 3)))
    spare = min(set(range(1, 16)) - set(pix))
    pal[spare] = pal[0]
    out = bytearray(32 * 32)
    for y in range(h):
        out[y * 32 + DOOR_X:y * 32 + DOOR_X + w] = bytes(spare if v == 0 else v for v in pix[y * w:(y + 1) * w])
    return bytes(out), pal


def apply(files):
    import version
    from gen4rom import Rom, narc_members
    smap = sprite_map()
    mm = narc_members(Rom(people_dump()).read(MMODEL))
    # Platinum: the people it redrew from its own dump (the same members; PLATINUM_REDRAWN)
    redrawn = narc_members(Rom(version.SOURCE_DUMP).read(MMODEL)) if version.PLATINUM else None
    sheets = narcio.load(files, sprites.ARC_OW_SHEETS)
    table = sprites.ow_table(files)
    pwt = pwt_codes(files)
    done = []

    def own_code(who, gfx):
        """The code of a Pearl graphics id, checked to be that id's alone (and, for Team Galactic, not the PWT's). A row
        marked "same_as" this id shares its code on purpose (Platinum's Distortion World lake trio, ids 264-267: Platinum
        draws them with the species' own texture), so it shows the same art."""
        code = smap[str(gfx)]['code']
        users = [k for k, v in smap.items() if isinstance(v, dict) and v.get('code') == code
                 and v.get('same_as') != str(gfx)]
        assert users == [str(gfx)], (who, code, users)
        assert gfx not in GALACTIC | NAMED or code not in pwt, f'{who}: code {code} is in the PWT\'s table (a/2/4/7)'
        return code

    for who, gfx, mid, tex in PEOPLE:
        code = own_code(who, gfx)
        fr, _, pal = sprites.btx_decode((redrawn if redrawn and gfx in PLATINUM_REDRAWN else mm)[mid])
        fr = sorted(fr, key=lambda f: int(f[0].split('.')[-1]) if '.' in f[0] else 0)   # (the bag: one, 'bag')
        assert len(fr) in (1, 16) and all(f[0].rsplit('.', 1)[0] == tex and (f[1], f[2]) == (32, 32) for f in fr), who
        sheet, _ = sprites.ow_sheet_of(files, code, table)
        lay, _, _ = sprites.btx_layout(sheets[sheet])
        order = LAYOUT[len(lay)]
        assert all((w, h) == (32, 32) for _, w, h, _ in lay), who
        pix = [shift(fr[i][3], SHIFT_DOWN) for i in order]
        sheets[sheet] = sprites.btx_encode(sheets[sheet], pix, pal)
        done.append(f'{who} = code {code} (sheet {sheet}, {len(lay)} frames)')
    who, gfx, _, _ = DOOR
    code = own_code(who, gfx)
    sheet, _ = sprites.ow_sheet_of(files, code, table)
    lay, _, _ = sprites.btx_layout(sheets[sheet])
    assert [(w, h) for _, w, h, _ in lay] == [(32, 32)], who
    pix, pal = pearl_door(mm)
    sheets[sheet] = sprites.btx_encode(sheets[sheet], [pix], pal)
    rec = narcio.load(files, sprites.ARC_OW_TABLE)
    t = bytearray(rec[0])
    at = 4 + 28 * sprites.obj_record(code)
    assert struct.unpack_from('<H', t, at)[0] == code, who
    t[at + 4] = t[at + 6] = 0                       # shadow, reflections (sprites.ow_table's record fields)
    rec[0] = bytes(t)
    narcio.save(files, sprites.ARC_OW_TABLE, rec)
    done.append(f'{who} = code {code} (sheet {sheet}, 1 frame; no shadow or reflection)')
    for who, gfx, mid, tex in OBJECTS:
        code = own_code(who, gfx)
        assert code not in pwt, f'{who}: code {code} is in the PWT\'s table (a/2/4/7)'
        sheet, _ = sprites.ow_sheet_of(files, code, table)
        lay, _, _ = sprites.btx_layout(sheets[sheet])
        assert all((w, h) == (32, 32) for _, w, h, _ in lay), who
        assert sprites.btx_layout(mm[mid])[0][0][0] == tex, who
        pix, pal = pearl_object(mm[mid])
        sheets[sheet] = sprites.btx_encode(sheets[sheet], [pix] * len(lay), pal)
        done.append(f'{who} = code {code} (sheet {sheet}, {len(lay)} frames)')
    who, gfx, mid, tex = SNOWBALL
    code = own_code(who, gfx)
    sheet, _ = sprites.ow_sheet_of(files, code, table)
    lay, _, _ = sprites.btx_layout(sheets[sheet])
    assert [(w, h) for _, w, h, _ in lay] == [(32, 32)], who
    pix, pal = pearl_snowball(mm[mid], tex)
    sheets[sheet] = sprites.btx_encode(sheets[sheet], [pix], pal)
    rec = narcio.load(files, sprites.ARC_OW_TABLE)
    t = bytearray(rec[0])
    at = 4 + 28 * sprites.obj_record(code)
    assert struct.unpack_from('<H', t, at)[0] == code, who
    t[at + 6] = 0                                   # reflections (Pearl: shadow, no reflection)
    rec[0] = bytes(t)
    narcio.save(files, sprites.ARC_OW_TABLE, rec)
    done.append(f'{who} = code {code} (sheet {sheet}, 1 frame; no reflection)')
    who, gfx, mid, tex = BOULDER
    code = own_code(who, gfx)
    assert code == STRENGTH_ROCK, f'{who}: code {code}, not Black 2\'s 1 x 1 Strength rock {STRENGTH_ROCK}'
    assert not any(isinstance(v, dict) and v.get('code') == BOULDER_SHEET for v in smap.values()), BOULDER_SHEET
    assert code not in pwt and BOULDER_SHEET not in pwt, who
    rec = narcio.load(files, sprites.ARC_OW_TABLE)
    t = bytearray(rec[0])
    at, src = (4 + 28 * sprites.obj_record(c) for c in (code, BOULDER_SHEET))
    # record bytes: uid 0, type 2, scene node 3, shadow 4, footprint 5, reflections 6, billboard 7, atlas 8,
    # controller 9, gender 10, collision width 11 / height 12, offsets 13-15, sheet (res1) 16
    assert struct.unpack_from('<HB', t, at) == (code, 0), f'{who}: code {code} is no longer an invisible record'
    assert struct.unpack_from('<HBBB', t, src)[:2] == (BOULDER_SHEET, 1), who
    sheet = struct.unpack_from('<H', t, src + 16)[0]
    assert [r['res1'] for r in table if r['entityType'] == 1].count(sheet) == 1, f'{who}: sheet {sheet} is shared'
    lay, _, _ = sprites.btx_layout(sheets[sheet])
    assert all((w, h) == (32, 32) for _, w, h, _ in lay), who
    assert sprites.btx_layout(mm[mid])[0][0][0] == tex, who
    pix, pal = pearl_object(mm[mid])
    sheets[sheet] = sprites.btx_encode(sheets[sheet], [pix] * len(lay), pal)
    t[at + 2:at + 28] = t[src + 2:src + 28]
    t[at + 10] = 2                                  # no gender (an object)
    assert t[at + 11] == t[at + 12] == 1 and t[at + 13:at + 16] == b'\0\0\0', f'{who}: not 1 x 1'
    rec[0] = bytes(t)
    narcio.save(files, sprites.ARC_OW_TABLE, rec)
    done.append(f'{who} = code {code} (1 x 1, the record and sheet {sheet} of code {BOULDER_SHEET}, {len(lay)} frames)')
    for who, gfx, mid, tex in POKEMON:
        if version.VERSION not in POKEMON_ONLY_IN.get(who, (version.VERSION,)):
            continue
        code = own_code(who, gfx)
        fr, _, pal = sprites.btx_decode(mm[mid])
        fr = sorted(fr, key=lambda f: int(f[0].split('.')[-1]))
        assert [f[0] for f in fr] == [f'{tex}.1', f'{tex}.2'], who
        sheet, _ = sprites.ow_sheet_of(files, code, table)
        lay, _, _ = sprites.btx_layout(sheets[sheet])
        assert len(lay) == 6 and all((w, h) == (fr[0][1], fr[0][2]) for _, w, h, _ in lay), who
        sheets[sheet] = sprites.btx_encode(sheets[sheet], [fr[0][3], fr[1][3]] * 3, pal)
        done.append(f'{who} = code {code} (sheet {sheet}, 6 frames from Pearl\'s 2)')
        if who in FLOAT_Y:
            rec = narcio.load(files, sprites.ARC_OW_TABLE)
            t = bytearray(rec[0])
            at = 4 + 28 * sprites.obj_record(code)
            assert struct.unpack_from('<H', t, at)[0] == code and t[at + 13:at + 16] in (bytes(3), bytes((0, FLOAT_Y[who], 0))), who
            t[at + 14] = FLOAT_Y[who]               # wPosOffsetY (s8, units)
            t[at + 4] = 0                           # shadow
            rec[0] = bytes(t)
            narcio.save(files, sprites.ARC_OW_TABLE, rec)
            done[-1] = done[-1][:-1] + f'; drawn {FLOAT_Y[who]} units up as Pearl\'s, no shadow)'
            for zone, zcode in smap[str(gfx)].get('zone_codes', {}).items():   # (a zone's own copy: the lab's)
                users = [k for k, v in smap.items() if isinstance(v, dict)
                         and (v.get('code') == zcode or zcode in v.get('zone_codes', {}).values())]
                assert users == [str(gfx)] and zcode not in pwt, (who, zone, zcode, users)
                zat = 4 + 28 * sprites.obj_record(zcode)
                assert struct.unpack_from('<H', t, zat)[0] == zcode, (who, zcode)
                t[zat + 2:zat + 28] = t[at + 2:at + 28]  # the species' record: its sheet, no shadow
                t[zat + 14] = ZONE_FLOAT_Y[zone]
                rec[0] = bytes(t)
                narcio.save(files, sprites.ARC_OW_TABLE, rec)
                done.append(f'{who} in {zone[4:]} = code {zcode} (the record of {code}, drawn {ZONE_FLOAT_Y[zone]} '
                            f'units up)')
    who, gfx, _, _ = WALL
    code = own_code(who, gfx)
    sheet, _ = sprites.ow_sheet_of(files, code, table)
    lay, _, _ = sprites.btx_layout(sheets[sheet])
    assert all((w, h) == (64, 64) for _, w, h, _ in lay), who
    pix, pal = pearl_wall(mm)
    sheets[sheet] = sprites.btx_encode(sheets[sheet], [pix] * len(lay), pal)
    rec = narcio.load(files, sprites.ARC_OW_TABLE)
    t = bytearray(rec[0])
    at = 4 + 28 * sprites.obj_record(code)
    assert struct.unpack_from('<H', t, at)[0] == code, who
    t[at + 4] = t[at + 6] = 0                       # shadow, reflections (a wall)
    rec[0] = bytes(t)
    narcio.save(files, sprites.ARC_OW_TABLE, rec)
    done.append(f'{who} = code {code} (sheet {sheet}, {len(lay)} frames; no shadow or reflection)')
    if version.PLATINUM:
        done[:] = [d.replace(' = code', ' (Platinum\'s art) = code', 1) if d.split(' = ')[0] in PLATINUM_REDRAWN.values()
                   else d for d in done]
        done += apply_platinum(files, sheets, table, own_code, pwt)
    narcio.save(files, sprites.ARC_OW_SHEETS, sheets)
    return 'pearl_npc_sprites: ' + '; '.join(done)


def people_dump():
    """Platinum moved 59 of Pearl's sheets and changed others: until step 6 maps its own, its people are Pearl's (the base), from Pearl's
    dump. Diamond's and Pearl's are their own."""
    import version
    return os.path.join(ROOT, 'roms', 'pearl.nds') if version.PLATINUM else version.SOURCE_DUMP
