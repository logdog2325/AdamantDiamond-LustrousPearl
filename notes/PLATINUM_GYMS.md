# Platinum's changed Gyms (step 4, 2026-11-02, plat-gyms)

Platinum changed four Gyms. Three need code: the Eterna clock, Veilstone's bags and tire stacks, Hearthome's dark rooms.
Snowpoint only changed its ground. Everything else in these Gyms (Leaders, Trainers, badges, TMs, scripts) comes from
Platinum's own data through the usual pipeline.

## How it is built
- **Code: overlay 374** (decomp `src/pearlb2/plat_gyms/`, `include/pearlb2/plat_gyms.h`). It sits where Black 2's own
  gimmick overlays load (AFTER(OV084, OV085), 0x021EEC80). A zone has one gimmick, so while ours runs none of Black 2's
  is there. `gimmick_itcm.c`'s rows got an overlay id (as Black 2's GIMMICK_OVERLAY_INFO): the dispatcher loads it
  before the gimmick's init and unloads it after its end. Size 0x2D40 with its pool (Black 2's own gimmick overlays reach
  0x6D60 there). The resident pool is untouched.
- **Gimmicks 65 (Eterna), 66 (Veilstone), 67 (Hearthome)**. Only a Platinum build gives a zone one
  (`patches/platinum_gyms.py`, after `veilstone_gym` in the patch list). Pearl and Diamond: nothing changes.
- **Data**: `b2tools/platinum_gym_data.py` reads Platinum's tables from the dump by their contents (overlay 8's
  gym_features.c tables, overlay 5's renderer tables, the models and animations from build_model.narc and
  mmodel/fldeff.narc). The patch writes them into overlay 374's own pool (1,808 of 2,048 bytes) and appends 30 models
  and animations to a/2/9/5 after Sunyshore's gears.
- **Scripts**: `pearl_story.py` handlers for InitPersistedMapFeaturesForEternaGym, AdvanceEternaGymClock (macro
  `pl_AdvanceEternaGymClock` in pearl_story.inc), and Platinum's sense of InitPersistedMapFeaturesForHearthomeGym and
  ...VeilstoneGym.
- **Pearl's Hearthome lifts are off for Platinum** (`pearl_gimmicks.HEARTHOME_GYM`, a version row): no gimmick 59 rows, no
  lift prop, no lift plates in Platinum's rooms 88-91.

## The Eterna Gym (zone 67, Black 2 102)
- The two hands (build models 537, 536) turn at the clock's centre, 12 and 13 units up. Five states: 7:25, 6:15, 9:15,
  0:45, 0:30. Each state's paths are walkable at Platinum's BDHC height (16, 24-32 over the centre); the rest of the clock
  is solid. The converted room has the flower beds' shape there, so the gimmick's terrain layer replaces it.
- The fountains (field effect 111, animations 166/167) block z 19 until they drain: the right one after the second
  Trainer, the left one after the third.
- The hour hand's jump: holding toward the state's jump tile jumps two tiles across it (Black 2's ACMD_JUMP_2).
- AdvanceEternaGymClock: the camera goes to the centre, the hands turn two minutes a frame, then the camera comes back.
  After the second and third Trainer it goes to the fountain, which drains, and the script shows "The fountain's water
  level dropped!" (the zone's line 12) and waits for A or B. The request work PVAR_GIMMICK_REQUEST: 1 turn, 2 the line,
  3 back, 0 done.
- Platinum keeps the clock's state in its own var (0x404B, written only by its C). Here the state is the Gym's
  VAR_ETERNA_GYM_TRAINERS_BEATEN (0x40AE, set just before each Trainer's AdvanceEternaGymClock), and 4 with the Forest
  Badge. The clock's paths only let the Trainers be fought in order, so the two agree.

## The Veilstone Gym (zone 133, Black 2 183)
- 9 punching bags and 11 tire stacks (field effects 113 and 114, 112 when a stack falls; animations 182-190, 195, 196,
  168). Walking into a bag kicks it. It slides along Platinum's tile table until it stops, knocking over a tire stack in
  its way. A bag that can't move sways. A long slide takes the camera along.
- Bags and standing stacks make their tiles solid. Their places are kept for the visit (a battle keeps them; leaving
  resets them, as Platinum).
- They are drawn at Platinum's floor + 6 (its BDHC), so the bags hang from the room's rails.

## The Hearthome Gym (zones 88-91, Black 2 128-131)
- The fog: near-black, density 109 of 127 (119 in trainer room 2, 91 after the Relic Badge). Black 2's field fog, set
  every frame (its field light sets the fog colour when it changes).
- Each person carries a candle light (field effect 115, drawn without fog; its flicker 199), two tiles ahead, shorter at a
  wall or a person.
- Trainer rooms: on entering, one door is picked at random. Its mark (116-123) goes on a random allowed tile. The other
  doors' warps lead back to the entrance room's warp 1. The pick lasts the visit.
- A Trainer not yet beaten within two tiles ahead of the player walks up to battle (Black 2's Trainer walk-up script),
  besides Trainers seeing the player as usual. A beaten Trainer wanders around where it stands.
- The Leader's room: Fantina, the bollards (removed after the win by the room's on-load script), the shortcut warp panel
  to the entrance room.

## The Snowpoint Gym (zone 167, Black 2 225)
`b2tools/snowpoint_ice_check.py` plays the ice offline with gimmick 61's rules on the converted ground. Candice is
reached in both versions: Pearl in 67 moves (11 snowballs broken), Platinum in 34 (8 broken). The one-way tiles are the
same; Platinum has 19 snowballs in other places.

## What differs from Platinum, and why
- Sounds: Platinum's have no Black 2 equals; the patch's SOUNDS are guesses (the clock's tick, its stop, the fountain, the
  kick, the slide, the stop, a stack falling).
- The player's sprite in the Gym: the table's slot (playerCode) stays 0, the player's own sprite. Step 6 checked
  Platinum's 210 and 211: they are the player's own walking sheets (player_m/f_nsbtx), with no candle in them; the
  candle is the light. What Platinum does differently is draw the player without fog (gFogIgnoredModels). Black 2 has no
  such switch per person; whether its fog darkens the player here is on the combined-ROM list (notes/PLATINUM_SPRITES.md).
- Hearthome's clue mark: Platinum puts it 3 units under its BDHC height, 1 under the drawn floor. Here it is 1 over the
  converted floor, so Black 2 shows it.
- Hearthome's "!" bubble: Platinum draws it without fog in this Gym (ov5_021F5AA4). Black 2's bubble is drawn as usual.
- Hearthome's beaten Trainers: Platinum makes them wander 2 x 2 around where they stand. Here they keep their own range,
  re-centred on where they stand.
- Eterna's Trainers' facing after their battle (SetObjectEventDir on an object from a var): as in Pearl's build, left out.

## Found, for other pieces
- **Veilstone Gym ground (plat-world's heights):** the converted room puts 122 walkable tiles at 74-77 units: the
  ceiling rails ('sen', 'lambert20') are taken as the ground, where Platinum's BDHC says 0. The player would walk on the
  rails. The same fault is in 29 Platinum room chunks (Pearl: 11), among them the Contest Hall 241/242, Amity Square
  408/409, Victory Road 1F 384. The heights need a world-wide rule (a walkable tile's surface far above the BDHC is not
  ground). Fixed 2026-11-07 (plat-heights, version.GROUND_AT_BDHC; notes/MAP_LOOK.md "Heights at the BDHC"): the Gym's
  floor is -2 on every tile, the rails' tiles too (the drawn floor, 2 under BDHC's 0, as the rest of the room); the bags
  hang at 6 as before. `b2tools/heights_check.py`: 0 faults in Platinum's rooms and overworld.
- Hearthome Gym rooms on translated nodes: chunk 229 (the entrance room, shapes 5-10, one set 176 units west) and 230
  (trainer room 1, shapes 0 and 8). The renders draw them in the wrong place (room 1's left floor black) and the layers
  fix judges them there. No holes the fixes open in the four Gyms' chunks (`pearl_seams_check.py --holes --rooms`).
- The entrance room's Gym Guide is drawn over the statue in front of him ((h), 45 px): people depth.

## The 13 warp findings
All Platinum's design; `platinum_events.py` lists them as notes now (GYM_DESIGN):
- Eterna's zone 68 is the leftover DP Gym room: its only way in, warp 1 at (11, 0), is in the wall.
- Hearthome's entrance room: (11, 7) and (12, 7) are walled in.
- Hearthome's rooms: every bottom door leads back to the entrance room's door; the top doors lead on (the wrong ones back
  to the entrance, at run time).
