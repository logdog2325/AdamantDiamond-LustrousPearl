# Platinum's Distortion World: the engine

Step 7, first piece (plat-dw-core, 2026-11-07). True wall walking, as Platinum does it (the user's decision of
2026-11-01). The maps, the story inside and the registry are the second piece's (plat-dw-world): see "For plat-dw-world".
Not in public snapshots (Platinum isn't announced).

## What is built
- **The tables:** `b2tools/platinum_dw_data.py` reads Platinum's dump: `fielddata/tornworld/tw_arc.narc` (the floors'
  offsets; per floor the platforms, jump points, camera triggers, ghost props), `tw_arc_attr.narc` (the platforms'
  grids) and overlay 9's own data (the floor connections, the 32 moving platforms, the 22 elevator paths), found by one
  known row each and read whole. It writes `data/platinum/distortion_world.json` (both coordinate frames) and the
  engine's tables (`blob()`, 4,488 B; the grids as runs). `--check`: the dump equals pokeplatinum's archives; 6 faces,
  20 jump points, 26 camera triggers; every jump lands on its platform.
- **The rules:** `src/pearlb2/plat_dw/dw_core.c` (decomp), Platinum's functions one by one, with their names in the
  comments: the platform manager and its quirks (HasFloatingPlatformAtCoords counts any platform while a kind is
  given), the grids, the step tables per face, the collision (grid, other people, water, double jumps), the move choice
  on a face (turn, walk, run, surf, bump; the moving direction counts on walls and the ceiling), every distortion
  action's step (105-116, 121-132, the floor's walks and runs, the 3-tile double jump), the jump points' jump
  (JumpOnFloatingPlatform), the camera triggers and their 16-step lerp (DoCameraTransition, CameraTransitionTask), the
  sprite's rotation (the map object rotator), the elevators (DistWorldElevatorPlatform_*) and the floor's change.
- **The field:** `src/pearlb2/plat_dw/dw_field.c`, overlay 377, gimmick 69 (`src/pearlb2/gimmick_itcm.c`). See "How
  it runs".
- **The patch:** `b2tools/patches/platinum_dw.py` (Platinum builds only): the ten zones get gimmick 69, the tables go
  into overlay 377's pool. **List it after platinum_gyms.**
- **The harness:** `b2tools/platinum_dw_check.py` (see "The harness").

## Coordinates
Platinum's floors share one world: each floor's land is drawn at its offsets (tw_arc member 0: offsetTileX,
offsetAltitude, offsetTileZ), and its tables and event files use that world's tiles. Black 2 has a map per zone at the
origin, so the engine's tables are in **each floor's own tiles: Platinum's less the floor's offset**
(x - offsetTileX, y - offsetAltitude, z - offsetTileZ; y is the height in tiles). The JSON keeps both (`bounds`,
`bounds_local`).

| Floor | Zone | Offset (x, alt, z) | Faces |
|---|---|---|---|
| 1F | 699 | 21, 288, 10 | none |
| B1F | 700 | 0, 256, 35 | west wall |
| B2F | 701 | 15, 224, 0 | west wall, 4 floor platforms (the floating islands) |
| B3F | 702 | 47, 192, 21 | west wall |
| B4F | 703 | 57, 160, 34 | east wall, ceiling (with water) |
| B5F | 705 | 57, 128, 34 | none |
| B6F | 706 | 56, 114, 38 | none |
| B7F | 707 | 74, 64, 32 | none |
| Giratina's room | 708 | 0, 0, 0 | none |
| Turnback Cave room | 709 | 70, 64, 30 | east wall |

## How it runs
- **The player's decision** (`field_player_grid.c` FieldPlayerGrid_UpdateMovement): its call of
  FieldPlayerGrid_DecideCommand goes to the resident PearlB2_DWDecideCommand (`src/pearlb2/resident/plat_dw_hooks.c`),
  which hands it to the overlay while gimmick 69 runs. For a held direction: the camera trigger, then the jump point
  (Platinum's DistWorld_HandlePlayerMoved). A jump takes the input. On a face (platform), the core's move; on the land,
  Black 2's own walking.
- **Our action commands** (`fldmmdl_acmd.c` FieldAcmdTCB_RunCmds): its FldAct_ExecAcmd call goes to the resident
  PearlB2_ExecAcmd. Commands 0x100 + Platinum's action number, and 0x1f0 the jump, run in the overlay a frame at a time.
  So the player is busy for the field while one runs, as with Black 2's own.
- **Each frame** (the gimmick's update): the camera lerp as Black 2's pitch and yaw, the distance, the sprite's rotation
  on the player's billboard (BlActScene_SetActorRotation).
- **After a step** (the gimmick's step check): an elevator standing on the tile rides, as a field event.
- **The floor's change** (the elevator's change-maps point): the next zone without a warp, from Black 2's own pieces for
  walking across a matrix (Field_SwapZoneByMatrix: people, events, music, weather, camera bounds, place name, zone
  scripts) and the new floor's chunks (FieldG3DMapper_FreeMap, SetupLoadZoneMapTypeData, FieldG3DMapper_CreateMap). The
  player is rebased into the new floor's tiles first.
- **Saved:** the platform, the camera trigger's angles and the elevator flags, in gimmick 69's saved work (128 B, of
  Platinum's DistWorldPersistedData). A battle or a saved game comes back on the same face.

## The camera
Platinum puts the eye at (sin yaw cos x, sin -x, cos yaw cos x) from the player (camera.c); Black 2 at
(sin yaw |cos p|, sin p, cos yaw |cos p|) (field_camera.c FieldCameraApply_TransRot). So **Black 2's pitch is minus
Platinum's x**, the yaw the same, no roll (every trigger's roll is 0). The base is x -10750 (-59.1 degrees), distance
0x29AEC1, field of view 1473 + 192 (but in Giratina's room).

**B4F's sign question, settled from the data:** its two ceiling angles (55, 240) and (60, 220) give Platinum x +3330
and +4610 (+18.3 and +25.3 degrees): the eye below the player. Black 2's pitch is then 0xF2FE and 0xEDFE, negative: the
eye below as well. Black 2's |cos p| clamp (0x200) never acts: every angle stays within 60 degrees of level. For all 8
angles of the 26 triggers, Platinum's eye and Black 2's point the same way within 0.06 degrees
(`platinum_dw_check.py --camera`, with the DS's own sine table from Black 2's arm9).

## The harness
`python3 b2tools/platinum_dw_check.py` (about 1 minute). It compiles **Platinum's own C**, copied word for word from
pokeplatinum (`b2tools/platinum_dw_host/extract.py`: 290 functions and tables of ov9_02249960.c, player_move.c,
unk_020655F4.c, map_object*.c, map_tile_behavior.c), and **the overlay's dw_core.c** for the Mac, and runs routes on
both, frame by frame. A frame compares: the position, the tile, both directions, the jump's drawn offset, the face
(state), the platform, the floor, the camera's angles and whether it moves, the sprite's rotation, the action, an
elevator's shake, the elevator flags. Platinum's frames are taken off the floor's offset first.

Routes come from the tables: onto each face by each jump point that leads there; across the faces by a breadth-first
search over the tiles Platinum lets you stand on, and face to face by their jump points; off by each jump point back;
over the land to every camera trigger, pressing its way; each double jump of the floor platforms; surfing on the B4F
ceiling's water; every elevator standing on a first visit; each route again running.

**Result (2026-11-07): 111 routes, 19,051 frames, all the same.** 94 jumps, 20 elevator rides.

| Floor | Jump points | Camera triggers | Planes reached | Also |
|---|---|---|---|---|
| B1F | 4/4 | 4/4 | land, west wall | |
| B2F | 4/4 | 4/4 | land, west wall, floor platforms 0 and 3 | 24 double jumps |
| B3F | 4/4 | 6/6 | land, west wall | |
| B4F | 4/4 | 6/6 | land, east wall, ceiling | surfing on the ceiling |
| Giratina's room | | 2/2 | land | |
| Turnback Cave room | 4/4 | 4/4 | land, east wall | |
| 1F, B1F-B7F | | | | every elevator that stands on a first visit, up and down; B3F's two-floor ride (paths 8 then 9) |

What the harness does not prove: the land between the platforms is free in both sides (on the DS it is Black 2's own
walking), and Black 2's field itself (the hooks, the action commands, the camera, the billboard, the zone swap) is not
in it: see "What only the ROM can show".

Platinum quirks the harness keeps (both sides do them):
- HasFloatingPlatformAtCoords returns TRUE for any platform at the tile while the current kind is valid.
- After every jump the height calculation stays off (JumpOnFloatingPlatform tests a u16 index for < 0).
- TickJumpOnFloatingPlatformMovementAnimation reads one past sFloatingPlatformJumpOffsets on the last step and zeroes
  it at once (harmless; extract.py pads the copy for the sanitizers).

## Sizes
- Overlay 377: 14,240 B (the tables' pool 5,120 B of it) at 0x021EEC80 (the gimmick overlays' address), ending
  0x021F2420. The room there ends at overlay 146 (0x021F59E0): 13,760 B left.
  `pearlb2_overlays.py` stops a build whose overlays 374, 375 or 377 pass it.
- Resident: the two hooks, about 100 B.
- Field heap: the engine's work, about 2.4 KB (the current platform's grid is 2 KB, as Platinum's), and the floor below's
  mapper (its chunk buffers, as many as the zone's map type has).

## Not built, or not as Platinum (say so to the user)
- **Two floors drawn at once:** built (2026-11-07), not proved offline. The floor below gets its own mapper and matrix,
  its chunks at the floors' offset (FieldG3DMapper_SetOriginOffset, as the Battle Subway moves its map), bound to this
  floor's map textures (not loaded into VRAM twice; its texture animations don't run), streamed after the player each
  frame and drawn after the map in both passes: fieldmap.c's two FieldG3D_RenderFieldmap calls come to the resident
  PearlB2_RenderFieldmap (same size). The floor swap reloads both. Its memory needs the ROM.
- **The floor swap's look:** built Platinum's way (no warp), but only the ROM shows whether Black 2 swaps the chunks and
  people without a flash. If it can't, the fallback is a warp at the same point (a cut). (Seen on screen since build 3:
  no black frame.)
- **The props and the waterfalls:** built by plat-dw-world (see "The world").
- **The landing dust** after a jump: Black 2's ledge dust (FldeffKemuri) at the player's feet, not turned to the face
  as Platinum's ov5_021F3678 turns it. The sounds are stand-ins (Black 2's ledge landing, the gears' hum for the
  elevator). (plat-dw-rom: Platinum's own sounds now, SUTYA2 and FW089, when the sound heap has room.)
- **The Distortion World sprite** of the player (OBJ_EVENT_GFX_DIST_WORLD_PLAYER_M/F): not switched to (step 6's
  sprites).
- **Clip planes:** Platinum's near 150 and far 1700 are not set: the zones' camera setup row decides (plat-dw-world).
  (Set each frame since plat-dw-world.)
- **The sprite's rotation:** Platinum rotates the texture inside the billboard; Black 2 rotates the billboard about its
  origin. Same angle; the pivot and the direction need the ROM. (plat-dw-rom: DwField_SpritePivot puts the picture where
  Platinum's is; seen on the walls and the ceiling.)

## The world (plat-dw-world, 2026-11-07)
Overlay 9's world on top of the engine: `src/pearlb2/plat_dw/dw_world.c` (decomp branch pearlb2-plat-dw-world), its tables
`b2tools/platinum_dw_world.py` (from the dump; `--check` against pokeplatinum's C: 45 people, 45 events, 38 command lists, 4
simple props, 14 boulder falls) as a file of a/2/9/5 the gimmick reads into the heap (9,092 B: too big for the overlay's
room), the props' models appended there too (`patches/platinum_dw.py`: 25 models, 5 animations, Giratina Origin's model and
sheet). Sizes: overlay 377 grows about 8.4 KB (dw_world.o 7,915 B, dw_field.o +532 B): about 22.7 KB of the 27.5 KB to
overlay 146 (the build's pearlb2_overlays check confirms it). The resident hooks +192 B (the extension row).

- **The people** (sMapObjectEvents): `gen4_extract` gives each floor an event file of its own (534-543) with its Platinum
  events less the floor's offset and overlay 9's people (each local id once, always spawned; the Turnback room's Griseous Orb
  ball keeps its flag, 1490). On a fresh entry (Black 2 clears the gimmick's work on a warp) the template whose condition holds
  places each (CheckFlagConditionForObjectEvent: the progress, the puzzle flags, the shadows, Cyrus's appearance), none
  deletes it; a person a script adds (ActorAdd) is placed by its table: its height (no height calculation), its rotation on a
  face (B2F's Cynthia on the wall, 90 degrees). After a battle or a saved game they stay as they were (the saved work's
  `placed` bits). Cynthia rides the 1F and B6F elevators with the player and becomes the next floor's 128 (B1F's event file
  has her for that).
- **The events at a tile** (sMapEvents, HandleEventAt) after a step, as a field event: a zone script (chained, waited for), the
  progress, the shadow flags, the puzzle flags, a person added or deleted, B2F's moving platforms (the shake, the ride with
  the player, the landing on the new face), the player's distortion jump between them (action command 0x100 + 117-120),
  Giratina's shadow (its model flies its path, its cry), the Giratina room's platforms (ghost groups 1-3 one by one, the
  camera's turn), Giratina's arrival (added, it comes down 160 units). Other people's distortion actions get their own run
  (B2F: Cynthia on the wall beside the player).
- **The teleports:** B7F (15, 1, 25) up, progress >= 10, its script 2; the Giratina room (15, 1, 25) down, its script 4.
- **The waterfalls** (CascadeDown, CascadeUp, run by a held right at x 47, z 42-45: B4F's y 10, B5F's y 0): the fall 664
  units at Platinum's steps, the floor's change at 336 (down) or 320 (up) units (the engine's swap, no warp), the camera's
  orbit (245, 239 over 72 steps at 20 tiles down, back over 32 at 36; up: 55, 240 at 20 tiles), the sprite's turns and bob,
  the landing tile fixed and its face found (B5F's water: the land; B4F: the ceiling), then the move away (two slow steps west;
  up: the ceiling's walk west). B5F's first elevator stands after the fall.
- **The props**, drawn after the map in the second pass (Platinum draws its field effects there), this floor's and the one
  below's: the moving platforms and elevators that stand (their flags), the riding one at the elevator's place, B2F's moved
  ones; the ghost props (the floating platforms bob and fade a step a frame, the vines and rocks run their animation with the
  fade; their triggers hide and show groups; a fresh floor takes its default groups); the portals and B5F's waterfall (their
  conditions, their animations looped); Giratina's shadow; the Giratina room's Giratina (Platinum's own billboard model and
  128 x 64 sheet at its actor's place: Black 2's walkers are 64 x 64 and its free model codes are taken). Opacity is the
  model's alpha (NNS_G3dMdlSetMdlAlphaAll) for each draw, as Platinum's SetPropOpacity.
- **The camera's clip planes:** Platinum's near 150 and far 1700, each frame (the eye is 667 units away).
- **Script commands** (extension row 0x20-0x3f, notes/EXT_COMMAND.md): 0x20 DoDWWarp (resident), 0x21 GetPlayer3DPos
  (Platinum's world tiles), 0x22 and 0x23 the 1F shadow (sGiratinaShadowExternal), 0x24 the camera's reset.
- **The maps:** the ten floors convert as rooms (their land at the floor's own origin, heights 16 = 1 tile, as the engine's
  tables); `zone_flags` gives them Black 2's battle background 11 (Shauntal's dark purple-blue: the nearest of Black 2's 21 to
  Platinum's dark void; a decision for the user) and no surf song (Platinum's flag); their light is Platinum's own (area 74:
  arealight 1, indoor, clearing to black). Offline looks (Black 2's room camera, not the Distortion World's):
  work/agents/plat-dw-world/shots/dw_floors.png.
- **The story:** row 9b of story_flow.json (33 beats, 0 findings; `--next` against chapter 9's start B: 0, start B now carries
  B4F's two shadow flags).

### Not built, or not as Platinum (the world)
(plat-dw-finish, 2026-11-07, updated this list: see "The finish" below for what it built.)
- ~~The boulder puzzle's falls~~: built (plat-dw-finish).
- ~~The lake trio's hints on B5F~~: built (plat-dw-finish).
- Giratina's arrival: its sprite's darkening and brightening built (plat-dw-finish); ~~the sky's darkening isn't drawn~~ (the
  sky is drawn since plat-dw-rom, its darkening with it).
- ~~The sky (the 2D background, its rotating clouds, darker the lower the floor): not built~~: built by plat-dw-rom in the 3D
  (dw_sky.c: the sky and its 9 turning clouds, the 13 darkness levels); plat-dw3 gave the fogged land its see-through (see
  "The last differences"). The fog and the edge colours: built (plat-dw-finish).
- The waterfalls: ~~Black 2's surf actor stays as it draws it~~: built by plat-dw-rom (MountTCB: Platinum's angles, orbit and
  fix), at the billboards' scale since plat-dw3. The climb's last two actions (Platinum's 151 and 147) aren't the engine's:
  only the ceiling walk west.
- The floor below's people (Platinum adds the next floor's objects too), and B1F's event adding B2F's Cynthia (she stands
  there by her condition when the player arrives). On B5F a boulder that fell stays drawn on B6F (it is still B5F's actor);
  after a ride up from B6F the boulders down there aren't drawn from B5F.
- ~~Black 2 clears the gimmick's work on every warp~~: so does Platinum (plat-dw-finish found it: "The finish", the state
  across warps). Nothing to keep.
- ~~DoDWWarp: the screen stays black for 90 frames~~: Platinum's swirl built by plat-dw-rom (dw_warp.c; overlay 382 since
  plat-dw3); the black stand-in only without its files.
- ~~Sounds: stand-ins~~: Platinum's own built by plat-dw-rom (loaded per scene; the stand-ins only when the sound heap is short).
- ~~The lake trio's Distortion World renderers (264-267) and Giratina Origin's two-frame sheet animation: a still frame~~:
  built by plat-dw-rom; Giratina's checked against Platinum's sequence file by plat-dw3.
- **Offline only:** the C is compiled per file against main's tree (no build: the disk), not linked; every import is a global
  of arm9's link map. The combined build links it.

## For plat-dw-world
- Convert each floor's land with its matrix's block (0, 0) at Black 2's origin and heights as in Platinum's land data:
  the engine's tables are in that frame. **Subtract the floor's offset from Platinum's event coordinates** (people,
  warps, triggers: they are in the shared world; `pl_Warp 699, 55, 40` lands at 1F's (34, 30)).
- All ten zones should share one area (texture set): the floor swap only reloads chunks.
- The world's hooks in the engine: `PlatDW_CheckStep` is where Platinum's HandleEventAt and the B7F and Giratina room
  teleports go; `DwSystem_HandlePlayerMoved` is where the ghost prop triggers and the waterfalls go. The saved work has
  room for the boulder puzzle flags and the ghost prop groups (`DwSaved`).
- The B4F camera trigger at local (49, 11, 32) is above the ceiling (y 10): no face reaches it. Platinum's data as is.
- 14,368 B left in the gimmick room for the world's code.

## What only the ROM can show
For the combined test (Platinum build with platinum_dw listed). Local tiles; `TEST_START` at the zone.
1. **B1F (700):** start (15, 1, 14). Walk left: at (14, 1, 14) the camera turns (yaw 45, pitch 20) over 16 frames,
   smoothly. At (12, 1, 14) press left: the jump onto the wall (18 frames, an arc, the sprite turning 90 degrees).
   Film: the wall drawn from that angle (FieldChunk_CheckBBox not culling it), the sprite's feet on the wall and its head
   away from it. Walk up and along to (11, 2, 22), press down: back onto the floor at (12, 1, 23), facing right; walk
   right: the camera back to its base at (14, 1, 23).
2. **B2F (701):** start (18, 1, 23); left onto the wall at (16, 1, 23); up to the top (15, 9, 15); press down: the jump
   onto the floating island (state floor). Film the island underfoot.
3. **B3F (702):** start (12, 1, 28); onto the wall at (10, 1, 28); along to (8, 2, 39); down off it.
4. **B4F (703), the camera past level:** start (46, 1, 22); right onto the east wall at (48, 1, 22); up the wall to
   (49, 8, 27): the camera goes to (55, 240): **the eye below the player**; at (49, 9, 27) press up: onto the ceiling.
   Film: the ceiling drawn above the eye, the sprite upside down (180 degrees), nothing flipped or mirrored, no clipping
   of the floor or the ceiling (near 150 / far 1700 are the zone's own). Walk the ceiling's water with Surf if the
   world gives it.
5. **Turnback Cave room (709):** start (46, 1, 25); right onto the east wall at (48, 1, 25); along to (49, 1, 36); down.
6. **Elevators:** 1F (699) step onto (19, 1, 44) from the west: the shake, the ride down at 4 units a frame, and at
   16 tiles down the zone changes to B1F (700) with no warp: film for a black frame, a missing floor, people popping, the
   music, the place name. The player ends at B1F (40, 1, 19). Then B1F (33, 1, 10) to B2F, B2F (50, 1, 31) to B3F, B3F
   (49, 1, 22) down two floors to B5F (one ride), B6F to B7F (50 tiles).
7. **Saved state:** save on the B1F wall, reload: the player on the wall, rotated, the camera as it was. A battle on a
   face if the world has one.
8. **Memory:** the elevator's zone swap reloads chunks: watch for a heap error on the swap and after five rides.
9. **The floor below:** on 1F, B1F and each floor with one below, the next floor drawn under this one at its place
   (B1F under 1F: 21 tiles west, 32 down and 25 south of 1F's own origin). Film: it lines up with the elevator's ride (the
   platform arrives where the floor below shows it), no texture garbage (it borrows this floor's textures), no
   flicker, the frame rate, and after the ride the new floor below. Watch the heap.
10. **Landing dust:** a puff at the player's feet after each jump point's landing, on walls too (not turned to the face).
11. **Pearl and Diamond:** the two hooks pass through when gimmick 69 isn't running: walking, running, ledges, the
   Snowpoint Gym's ice, Iron Island's lifts as before.

### The world (plat-dw-world): what to film
Platinum build with platinum_dw after platinum_gyms; the start: story_flow.json row 9b's "start" (`TEST_START=699,34,30`:
chapter 9's state at the distorted pillar's YES). Local tiles.
12. **The way in** (zone 265, Spear Pillar Distorted, Cynthia, YES): the black screen holds about 90 frames with the warp
    sound, then 1F (34, 30) fades in. 1F's first scene: Cynthia appears beside the player (ActorAdd 128: on the ground, not
    floating), looks around, Giratina's shadow flies past to the east with its cry (the model drawn, its animation), she
    walks off. Film: her height, the shadow's path and size, no leftover shadow after the scene.
13. **1F's portal and props:** the portal at (34, 1, 29) turning (its animation), the elevator at (19, 1, 42) drawn where it
    stands; talk to Cynthia at (18, 42); step on (19, 1, 42): "the slab moves if you step on it" once; the ride down with
    Cynthia beside the player (she shakes with the platform, rides down, is B1F's at the bottom), the platform model riding
    under the player, on B1F the frame scene (she jumps away west and south: three distortion jumps).
14. **B1F (15, 1, 23):** Mesprit's cry, it flies north and goes. **B2F:** Cynthia on the west wall at (15, 9, 20), turned 90
    degrees; talk to her from below the wall (y 8) and from beside it: both answers; "let's split up": she walks along the
    wall while the player does too (two distortion actions at once). B2F's moving platforms: step on (18, 1, 36): the platform
    shakes, carries the player 8 tiles north, the player jumps off north, the platform goes back; the same at each of the 24
    events' tiles; the floating islands' ghost platforms bob.
15. **B3F (18, 1, 20):** Cyrus walks up 7 tiles, YES/NO, walks back. **The ghost props** on B3F and B4F (49 and 24 of them):
    walking their triggers' tiles makes groups of rocks and vines grow or sink (the animation and the fade together, a
    sound), the floating platforms fade a step a frame. Film: no flicker between props of different groups, the alpha.
16. **B4F's shadows:** (8, 1, 23) and (41, 1, 22): the shadow flies its path (48 units a frame, 64 and 72 steps), once each.
17. **The waterfalls:** B4F, surf east at x 47, z 42-45 (y 10): the player turns to fall (90 degrees over 32 frames), falls,
    the camera orbits to (245, 239) and back, the floor changes to B5F partway with no black frame, the player lands on B5F's
    water and moves two slow steps west; B5F's first elevator stands. B5F, surf east at the same x, z (y 0): the climb (8
    units a frame), the camera to (55, 240), B4F's ceiling under the player, upside down, then a walk west on the ceiling.
    Film: the surf Pokémon (not turned with the player: Platinum turns it), the frames around the floor's change.
18. **B6F**: Cynthia at (29, 1, 42): "a giant puzzle". The boulders: film list 24-26 (plat-dw-finish).
19. **B7F** (a start there: TEST_SET with PVAR_4055=7 and Cynthia's passenger ride, or after B6F once the boulders work): the
    frame scene; (11, 1, 44): Cyrus walks to Cynthia; his battle; Cynthia heals; walk up at (15, 1, 25): the teleport to the
    Giratina room (15, 25). **The Giratina room:** (15, 1, 24) the cry and the first shadow (scale 0.25, west to east);
    (15, 1, 23) the platforms appear group by group with the camera's turn; (15, 1, 17) the second shadow; (15, 1, 14)
    Giratina comes down 160 units over its place (its model, Platinum's 128 x 64 picture, drawn at the invisible actor);
    talk: the battle is Giratina's **Origin Forme** (watch its form in battle: Black 2 may keep the Altered Forme without the
    Griseous Orb), catch it; Cyrus and Cynthia's scene with the camera 5 tiles south and back at the Distortion World's own
    angle; the portal at (15, 1, 12) turns; YES: Sendoff Spring (32, 17).
20. **The Turnback room (709):** from Turnback Cave's portal: the player at (46, 45); the portal at (46, 1, 44) turns; the
    Griseous Orb's ball at (19, 1, 25) (flag 1490); the portal's YES: back to Turnback Cave (11, 15).
21. **Memory and the heap:** the props' models load on entering (this floor's and the one below's kinds); watch the field heap
    after five elevator rides and both waterfalls, and VRAM for the props' textures.
22. **Pearl and Diamond:** extension row 0x20-0x3f is new in the resident section; nothing of theirs uses it.

## The finish (plat-dw-finish, 2026-11-07)
Step 7, third piece: what "Not built" listed. Decomp branch pearlb2-plat-dw-finish (a sparse worktree: the full checkout is
443 MB and the disk had 2.5 GB), compiled file by file against main's tree, not linked.

### The boulder puzzle (B5F and B6F)
- **How Platinum does it:** its Strength push (overlay 5 ov5_021DFB54.c) asks overlay 9 twice. ov5_021DFF1C: a boulder whose
  next tile is blocked (any collision bit but the walk range) is pushed anyway when that tile is a fall location
  (DistWorld_WillBoulderBeAtFallLocation over sBoulderFallLocations). ov5_021DFFBC: when the push has ended, a boulder on a
  fall location falls (DistWorldFallingBoulder_New, _Tick) before the push's task ends. B5F's three holes send a boulder to
  B6F (8 units a frame to B6F's floor, the boulder B6F's "outside" one); B6F's three right pits take any boulder if theirs is
  empty (down and on 2 units a frame for 8 frames, down 4 for 4, the boulder the pit's own local id, a 7-frame shake, the
  lake trio's script 5, 7 or 6, then three in: FLAG_DISTORTION_WORLD_PUZZLE_FINISHED); a wrong pit drops it 40 frames
  further and it is back on B5F.
- **Here:** two same-size calls in Black 2's push (ov036 field_player_grid_event.c): FieldPlayerGrid_CheckStrengthRockPushEvent's
  ActorRouteCollCheckOneTileInDir goes to the resident PearlB2_RockPushCollCheck, EventStrengthRockPush_Callback's
  FldAct_CheckAcmdEnd of the boulder to PearlB2_RockPushAcmdEnd (src/pearlb2/resident/plat_dw_hooks.c). Outside gimmick 69
  they are Black 2's own. While it runs: dw_core.c's DwBoulder_PushCollision drops the blocking bits for a fall location;
  after the push (both the boulder's and the player's actions ended, as Platinum waits for both) DwFallingBoulder_New and
  _Tick run a frame at a time while the push's event waits (dw_world.c DwWorld_BoulderPushEnd: the boulder's actor, its
  local id changed in a pit with ChangeActorUID, the lake trio's script called from the push's event, the flag; a wrong
  pit's boulder deleted). Black 2's own hole fill (fillsHole) never runs in the Distortion World: no tile there converts to
  Black 2's Strength hole class (pearl_chunk.BEHAVIOURS has no 0x1d).
- **Kept across the floors:** Platinum keeps B6F's objects as the floor below's while B5F is the floor (and B6F's while the
  player is on B6F), so a boulder that fell lies where it landed, one tile on from B6F's template. Black 2 loads a floor's
  people afresh on each elevator ride, so the saved work keeps B6F's three boulders' tiles (DwSaved.boulderTiles: set when
  one lands from B5F and after each push on B6F, cleared when it goes into a pit) and the floor's fresh load places them
  there. B5F's boulders go back to their places when B5F is loaded again, as Platinum's do (it deletes the floor above's
  objects).
- **The harness:** `python3 b2tools/platinum_dw_check.py --boulder` (platinum_dw_host/boulder.sh, about 20 s) compiles
  Platinum's own C (extract.py --boulder: sBoulderFallLocations, FindBoulderFallLocationFlag,
  DistWorld_WillBoulderBeAtFallLocation, DistWorld_IsBoulderAtFallLocation, DistWorldFallingBoulder_New/_Tick/_TickToB6F/
  _TickToCorrectPit/_TickToWrongPit, the persisted flag functions, MapObject_SetPosDirFromVec, MapObject_MovePosInDir, and
  overlay 5's push test ov5_021DFF1C, word for word) beside dw_core.c, with the fall table the overlay reads (the world's
  tables). **Result: 887,808 pushes** (every tile around B4F to B7F, each direction, 12 sets of collision bits) **the same;
  1,344 falls** (each of the 14 fall locations, pushed from each side, each boulder, the pits' flags each way) **the same in
  61,968 frames** (place, tile, last tile, the shake, local id, floor, the puzzle flags, the script, the sound, deleted, the
  finished flag); the story's way through (three boulders off B5F, each into its own pit: scripts 5, 7, 6, the puzzle
  finished). A changed constant in dw_core.c shows as mismatches (checked).
- What the harness doesn't cover: Black 2's push itself (its 16-frame walk of the boulder, its collision bits on the converted
  maps) is Black 2's, as everywhere; the field side (the actor, the script in the push's event) needs the ROM.

### The lake trio's boulder hints (B5F)
EventCmdShowUxieBoulderTuto, _Azelf_, _Mesprit_ in dw_world.c, as Platinum: the trio's B5F person (131-133, under the floor)
added where B5F's table puts it, its cry, it rises by its sprite's offset (2 units a frame, 4 below the last tile) to 17, 13 or
9 tiles; Uxie goes 2 tiles north, hovers three times (Platinum's 8-step bob), comes back; Azelf runs its actions list;
Mesprit runs its own (the "top" or "bottom" list by the player's row, z 67) while the player turns to follow it; each goes
down faster and faster (0x200 more a frame to 2 units) and is gone, its "seen" and "in B6F" flags set. The lists are
Platinum's numbers, Black 2's action commands of the same numbers (pearl_movement.json: all exact).

### The state across warps: Platinum resets it too
The brief asked to keep the elevator, puzzle and ghost-group state across the B7F and Giratina room warps. Platinum doesn't
keep it: every floor's OnTransition script runs InitPersistedMapFeaturesForDistortionWorld (pokeplatinum
res/field/scripts/scripts_distortion_world_*.s; it memsets the persisted data: persisted_map_features_init.c), and any warp
clears the persisted map features first (field_map_change.c FieldMapChange_UpdateGameData: PersistedMapFeatures_Init when
not noWarp). Overlay 9 then runs InitPersistedData: the elevators B4F_1 and B5F_1, or all of them entering B7F (that case
exists because B7F is entered by a warp from the Giratina room), the puzzle by FLAG_DISTORTION_WORLD_PUZZLE_FINISHED, the
camera at its base, no platform; the ghost groups at the floor's defaults. Black 2's reset on a warp (ov035
GameData_SetGimmickByZone) and the gimmick's fresh start are that, row for row (dw_core.c DwSystem_InitialMovingFlags,
dw_world.c DwWorld_Create). The elevators' floor changes are no warp in either game: the state stays. So nothing changes.

### The look
- **Built:** Platinum's fog (InitFog: on, colour and alpha, slope 0x200, offset 0x7600, black at alpha 16, its density
  rising evenly to 88 in 32 steps of 2) and edge colours (InitEdgeColors: dark grey RGB 4, 4, 4; the Giratina shadow's
  RGB 4, 3, 7), set each frame (Black 2's light writes the fog's colour, the area load its edge table); the fog off at the
  gimmick's end. Giratina's arrival (EventCmdPlayGiratinaArrival): Giratina added black (its 16 colours tinted to black,
  CalculateTintedColor, into its sheet's palette in VRAM through the V-blank transfer, as DistWorld_ApplyGiratinaSpritePalette),
  it comes down while the sky's darkness counts (12 levels at 8/90 a frame: it times the descent though the sky isn't drawn),
  brightens over 90 frames, a 30-frame wait.
- **Not built then, and why** (all of it built later by plat-dw-rom: see "The ROM-only parts: decisions"; what was still left,
  plat-dw3: "The last differences"):
  - **The sky** (InitSkyBackground: a BG layer on the main screen behind the 3D, Platinum's tw_arc_etc tiles, palette and
    screen, the 3D blended over it; InitSkyClouds: 8 affine OBJ clouds turning; the darkness by floor and Giratina's sky).
    Black 2's field uses its main-screen BG layers for its message windows (field_msgbg.c: two layers, sys->bg and bg2) and
    its own blending; which layer and VRAM a sky can take needs the ROM, and the clouds need Black 2's 2D sprite system
    (resources, cells, animations) in the overlay, which has about 1.5 KB left (below). A way: free the overlay's tables pool
    (5 KB: read the tables from a/2/9/5 into the heap like the world's), then the sky on the free BG layer at the ROM test.
  - **The surf mount in the waterfalls** (DistWorldSurfMountRenderer: turned and orbited with the player). Black 2's surf
    Pokémon is a 3D object of field effect 3 (ov036 fldeff_namipoke.c), turned by its direction in FldeffNamipoke_PlaceObjects
    each frame; turning it needs its transform set after that and before its draw, an order of Black 2's field loop to see
    in game.
  - **Giratina's two-frame picture and the lake trio's own renderers (264-267):** Platinum animates them through its
    billboard's texture animation; the files and the frames' layout in the sheet weren't traced (the files patches/platinum_dw.py
    appends are the model and one sheet).
  - **Platinum's own sounds** (SYUWA, SYUWA2, SYUWA3, FW089, FW089B, FW463, MEKI, MEKI2, GIRA, KUSARI, UG_008) and **DoDWWarp's
    swirl.** The data side is sinnoh_music's: pearl_music.trim and SDAT entries for each, from Platinum's archive. The C side
    is the question: Black 2 plays a sound only when its sequence, bank and waves are in the sound heap. GFL_SndBGMStack_Preload
    loads them but frees the playing song's entry first (snd_bgm_stack.c), so in the field it would stop the music; adding
    them to the field's always-loaded sound group costs sound heap all the time (58 KB free was measured with Twinleaf's
    song). Which one fits needs the ROM's sound heap. The swirl would be a field effect: Platinum's title demo swirl models
    drawn for the 90 frames DoDWWarp waits. Neither is built: the stand-ins stay.
- **Sizes:** overlay 377 grows 3,764 B (dw_core.o 6,152 -> 7,322, dw_world.o 7,915 -> 10,257, dw_field.o 3,390 -> 3,642): of
  the 5,340 B there were before overlay 146, about 1,576 B are left (the build's pearlb2_overlays check is the proof). The
  resident section grows 88 B (plat_dw_hooks.o 300 -> 388). ov036's field_player_grid_event.o is the same size, section by
  section; its relocations differ only in the two calls' targets. The gimmick's saved work: 40 of 128 bytes.

### What only the ROM can show (plat-dw-finish)
Platinum build with platinum_dw after platinum_gyms. Local tiles.
23. **The trio's hints (B5F, 705):** step on (29, 1, 19) or (30, 1, 19): Uxie's cry, it rises out of the floor to 2 tiles
    above it, goes 2 tiles north, bobs three times, comes back, sinks faster and faster, gone. (43, 1, 33) or (43, 1, 34):
    Azelf, its actions. (23, 1, 33) or (23, 1, 34): Mesprit circles, the player turns to follow it. Film: the trio's height
    (from under the floor), no flicker when it is added, each hint once.
24. **The boulders off B5F:** with Strength on, push the boulder at (18, 1, 34) east onto (19, 34) (a hole), the one at
    (41, 1, 33) west onto (40, 33), the one at (29, 1, 22) south onto (29, 23): the push goes though the tile is blocked; the
    boulder falls 14 tiles in 28 frames with a landing sound and lies on B6F, drawn under B5F's hole. Film: the fall, the
    boulder on the floor below, no stray collision on B5F after.
25. **The pits (B6F, 706):** ride down: the boulders lie at (20, 30), (41, 29), (30, 19) (where they landed, not the
    template's tiles). Push one onto (12, 29), (40, 30) or (29, 22): it slides into the pit, shakes, the trio's script (the cry,
    it warps out); after the third, FLAG_DISTORTION_WORLD_PUZZLE_FINISHED: Cynthia's talk shows the stepping stones and the
    elevator to B7F. A wrong pit, (19, 29), (23, 29), (44, 30), (49, 30), (29, 14), (29, 15), (29, 18), (29, 19): the boulder drops
    out of sight and is back at its place on B5F after a ride up.
26. **Kept places:** on B6F push a boulder a tile, ride up to B5F and back down: it is where it was pushed.
27. **Fog and edges:** the far land fading to black, outlines dark grey (Giratina's shadow's bluish); the fog gone after
    leaving through a portal.
28. **Giratina's arrival (the Giratina room):** Giratina appears black, comes down (about 6 s), brightens to its colours over
    3 s, then 1 s; its colours right after the battle too (the palette back to its own).
29. **Pearl and Diamond:** Strength pushes everywhere (Iron Island, Mt. Coronet, Victory Road, Black 2's holes in its own
    caves if any are left): the two resident calls are Black 2's own when gimmick 69 isn't running.

## On the ROM (plat-dw-rom, 2026-11-08)
The first combined build couldn't enter the Distortion World (plat-test: "An error has occurred" after Spear Pillar's YES,
black screens on direct starts; the game stopped in GFL_HeapAllocate under DwWorld_Create). plat-dw-rom made it fit, then
played it on screen. Decomp branch pearlb2-plat-dw-rom, branch plat-dw-rom.

### The memory
- **Where the field heap went.** Black 2 sizes the field heap by the zone's map type (fieldmap.c MAP_CONFIGS heapSize less
  0xF000: 1,210,312 B for type 16, the rooms'). Each map type also fixes the chunks' buffers: type 16 gives each of a mapper's
  4 chunks 110,600 B (its biggest chunk file, read whole: field_g3d_map.c FieldChunk_Create, FieldChunk_BeginLoad). The
  Distortion World draws two floors, so two mappers: 8 x 110,600 = 885 KB of the heap in chunk buffers. With Black 2's own
  field, the world's tables (9 KB), the engine and the props, 5 KB were left when the world's tables asked for 9 KB.
- **The fix: buffers the size of the floor's chunks** (dw_field.c FitChunkBuffers). The Distortion World's chunk files are
  12-70 KB (B4F's biggest, 70,444 B). Each mapper's 4 buffers are now its floor's biggest file, in the streamer's 0x800 steps
  (its first read is 0x800 bytes), from the archive's own table (GFL_ArcSysGetDataLength), so a bigger map can't overrun
  them. The field's own map is made again in PlatDW_Init (load phase 4; its chunks are first read in
  FieldRoutine_MapSpawnFinish), the floor below's when it loads, both again at each floor's change.
- **Per floor, as Platinum** (FreeUnusedPropRenderers): the props of this floor and the one below only; a kind no longer used
  is freed at the floor's change, with its textures' VRAM (the props never freed their VRAM before).
- **The engine's tables** left overlay 377's 5 KB pool for a file of a/2/9/5 read into the heap (4.5 KB of heap): the
  overlay's room went from 1,376 B to 5,536 B before this piece's code (3,104 B left after it).
- **Margins** (field heap free, biggest free block, after the floor's load): table in the report / below.
- Not used: heaps 80 (the field's particles, a child of the field heap) and 112 (the field menu) belong to Black 2's
  field; HEAPID_USER's free 110 KB is what apps opened from the field allocate; the fix needed none of them.

### Found on screen, fixed
- **The land's double jumps** (TILE_BEHAVIOR_JUMP_<dir>_TWICE: 224 tiles on the ten floors) were walls in Black 2's
  collision: 1F's elevator could not be reached. They are now in the engine's tables (version 2, DwLandJump) and
  dw_field.c's decision jumps them as Platinum's PlayerAvatar_WillJumpTwice (MOVEMENT_ACTION_JUMP_DISTORTION_WORLD_*, the
  floor platforms' jump), the landing sound and the height followed again after.
- **Ground with no plate**: Platinum keeps the walker's height where its BDHC has no plate; the converter gave such tiles
  height 0 where the model draws nothing (the elevator areas, landings: the platforms are props). The player dropped 16
  units after the double jump onto 1F's elevator area and the elevator (at y 1) never started; the floors' people stood 16
  low (plat-test's 196 height faults). pearl_chunk.py: on the Distortion World's chunks such a tile takes the height of the
  nearest plated tile of its chunk (Pearl and Diamond: no such chunks).
- **The camera's boundary**: sinnoh_rooms gives every room one that stops the camera at its south edge; Platinum's camera
  follows the player anywhere. platinum_dw.py clears it for the ten zones.
- **Surf on a wall or the ceiling** (B4F's ceiling water, the waterfalls' start) was not wired: the engine's surfing flag
  was never set on the ROM. Built Platinum's way: A against the water in the face's own directions runs the water's
  script (FieldMoves_CanUseSurfDistortionWorld); its surf command comes to the overlay through a same-size call
  (ov033 s00C5_CallSurf -> resident PearlB2_SurfTCB_Create; Black 2's own when not on a face): the mount at the water's tile,
  the hop (Platinum's MOVEMENT_ACTION_133/137/141 + dir, new in the core: sub_02066F88's 8 frames and low jump), Black 2's
  surf form. The dismount: a step onto land (ov5_021E032C), the same hop. Black 2's own surf exit reads the floor's tiles,
  so it waits while the player is on a face (fieldmap_event.c CheckSurfExitEvent's FieldPlayer_GetExState ->
  PearlB2_SurfExitExState, same size). The mount is drawn as DistWorldSurfMountRenderer draws it: upside down on the
  ceiling (sFixedRotAngles), at the player's place + (0, 8, 0) + the fix + the orbit x 20 + the bob, Black 2's model's own
  offset turned with it.
- **The floor below's rocks and blocks**: they are the land's buildings, which only the field's own mapper had loaded
  (FieldPropSystem_LoadArea); the floor below showed its bare land, and at an elevator's floor change B1F's blocks popped
  in. Its chunks now take this floor's prop system (the floors share their area), unlinked before either map is freed
  (Black 2 unlinks props only when a chunk moves). Compiled; **needs a rebuild to check**.

### Margins (the field heap after the floor's load)
Before: 5,168 B free when the world's tables asked for 9,112 (every floor: 8 x 110,600 B of chunk buffers).
Measured after (build 3): 1F 435,600 B free (biggest block 435,556), after its arrival scene the same; B1F 492,360 on a
start there, 486,360 after the ride from 1F (biggest 436,788); B2F 492,180 after the ride from B1F. The other floors'
buffers (4 x their own biggest chunk + 4 x the floor below's, in 0x800 steps): B3F 475,136 B, B4F 466,944, B5F 360,448,
B6F 319,488, B7F 139,264, the Giratina room 65,536, the Turnback room 188,416 (1F 360,448): the least room is B3F's,
about 320 KB free by the same count (to measure on screen). No heap error on 2 floor changes.

### On screen (build 3, a start at 1F 34,30; no Spear Pillar start yet: the disk)
- 1F (rows 12, 13): the arrival scene (Cynthia beside the player, on the ground; Giratina's shadow across; she walks
  off); the land's double jump to the elevator area (height kept 16); Cynthia's "the slab moves" line; the elevator ride
  with Cynthia to B1F, the zone's change halfway with no black frame, no heap error; B1F's frame scene.
- B1F (rows 1, 5, 6): the camera's turn at (14,1,14), the jump onto the west wall, up, down and along it, the jump back
  at (11,2,22) and (11,2,13), the camera back; the double jumps along rows 19 and 22; Mesprit's cry, its fade-in (the
  trio's renderer) and its flight north; the elevator (33,1,10) to B2F, the change with no black frame.
- Not yet on screen: B2F's wall and islands onward, the waterfalls and the ceiling's surf, B5F-B7F, the Giratina room,
  the Turnback room, the save on a wall, Spear Pillar's way in.

### Issues left
- At an elevator's floor change the passenger (Cynthia) was missing for one frame (she is the new floor's 128 only from
  the next frame: DwWorld_AfterSwap spawns her after Black 2's people are reloaded). Fixed (compiled, not yet seen): the
  passenger as she was is kept (local id 0xfe, hidden from Black 2's floor change) and moved with the platform until the
  new floor's 128 has drawn a frame, then deleted.
- The floor below's buildings (fixed, not yet seen).
- Spear Pillar's SYUWA2 loads above the song there; if the Distortion World's song is loaded above it at the warp, it stays
  in the sound heap under that song (a few KB) until the song stack drops below it (PearlB2_PlatSoundsDrop only drops a
  level that is still the top one).

### The ROM-only parts: decisions
- **Giratina's two-frame picture**: built (its sheet's two textures, 10 frames each, giratina_origin.bin). Not yet seen.
- **The lake trio's renderers**: built: B1F's Mesprit fades in over 31 frames (seen on screen), B6F's three bob 8 units
  over 32 frames (Platinum's table; not yet seen).
- **The surf Pokémon in the waterfalls**: built with surf on the faces (see above): Platinum's angles, orbit and fix,
  stepped as CmdRunDataCascadeDown/_Up step them. Not yet seen.
- **Platinum's own sounds**: built (compiled; needs a build). Measured: the Distortion World leaves 202,420 of the sound
  heap's 643,008 B free with its song. Platinum's 13 sounds there and at Spear Pillar (SYUWA, SYUWA2, SYUWA3, FW089,
  FW089B, FW089_2, FW463, MEKI, MEKI2, GIRA, KUSARI, SUTYA2, UG_008) all play from BANK_SE_FIELD over WAVE_ARC_BASIC and
  WAVE_ARC_SE_FIELD (520 KB); trimmed to what each plays (pearl_music.trim) they are 1-17 KB each, about 106 KB in all.
  All kept loaded would leave about 96 KB, less than a pushed song needs (up to 161 KB), so they load per scene:
  patches/platinum_dw.py PLAT_SOUNDS adds the 13 to the sound archive (each its own trimmed bank and wave archive, the
  player and priorities of the Black 2 sound it stands in for) and writes their ids and sizes into the resident section
  (gPearlB2PlatSoundSeq, _Size). resident/plat_dw_hooks.c PearlB2_PlatSound loads one when first played, above the song
  (NNS_SndHeapSaveState once, NNS_SndArcLoadSeqEx), only while 165 KB stay free after it and no song is loading; else
  the Black 2 stand-in plays. They are dropped (NNS_SndHeapLoadState) when an elevator ride ends and at the field's end;
  Black 2's song stack dropping below their level takes them too. The C plays them where Platinum does (the elevators'
  FW089 hum, the moving platforms' FW089B, the waterfalls' FW463, the vines' MEKI and MEKI2, the land rocks' FW089_2,
  the ghost props' SYUWA3, the landings' SUTYA2, the boulders' UG_008, Giratina's GIRA, the swirl's SYUWA2); the
  scripts' Platinum sound commands of these (pearl_story.py PLAT_SE) are pl_PlatSound n (ext 0x25). To see and hear: each
  scene's sound (not Black 2's stand-in), and no song cut short when Cyrus's or an encounter's theme starts after one.
- **The sky and clouds**: built (compiled; needs a build): src/pearlb2/plat_dw/dw_sky.c draws them in the 3D, as Black 2's
  field_3dbg.c draws its weather backgrounds (quads at a distance from the camera through its projection, the size of the
  screen there). Black 2's field uses all four main-screen BG layers (BG0 the 3D, BG1 and BG2 the message windows, BG3 the
  place name), so Platinum's BG2 sky has no layer. The sky's screen is one tile across each row, so its texture is one
  8 x 256 column repeated across (1 KB, not the 48 KB first estimated); the quad is just inside the far plane (254/256 of
  1700 units). The clouds are the 9 of sSkyCloudsTemplates (cloud 1's cell is no template's), each OAM of their cells a
  quad (11 quads, mirrored halves as their flips), nearer in Platinum's sprite order (the first template frontmost), turned
  about their middles at Platinum's speeds (sSkyCloudsRotAngleDeltas by SkyKind, eased 0x200 a frame) and by their angle
  plus offset as NNS_G2dRotZ turns a cell (clockwise on the screen, as their orbit goes), the outer four 2x. 7.75 KB of
  texture VRAM, 192 B of palette VRAM. The darkness: 0-12 by the player's height in Platinum's world
  (RecalculateSkyBackgroundDarkness), or the Giratina room's (12 once Giratina has come; its arrival's ramp; the clouds'
  kind 1 after Cyrus's battle, 2 from the arrival); the build makes the 13 levels' palettes (CalculateTintedColor toward
  RGB 4,4,8 and 6,6,8), sent to VRAM when the level changes. The sky takes Platinum's clear polygon ID 63, so the land's
  edges are marked against it as in Platinum. What differs: Platinum's fog makes the far land see-through over the sky (its
  3D layer is alpha-blended over BG2); here the sky is in the 3D, so the far land darkens to the fog's black instead. To
  see: the sky behind every floor (no black past the land), the clouds' turn and their direction against Platinum's, the
  darkness changing floor by floor, the Giratina room's arrival (the clouds backward, the sky darkening), the elevators'
  and waterfalls' floor changes with no jump in the clouds, no VRAM shortage (dw_sky.c draws nothing if its VRAM can't
  be had).
- **DoDWWarp's swirl**: built (compiled; needs a build), in the field: Black 2's field has a render mode for its
  encounter effects (fieldmap.c FieldRenderPhase2_EncountEffect: the map and everything on it not drawn, the effect's
  render function in their place; ov149 encounter_effect_model.c draws its models so), and src/pearlb2/plat_dw/dw_warp.c
  draws Platinum's swirl that way: its title demo's model and animations (demo/title/titledemo.narc 16, 18 and 17, looped;
  a/2/9/5 101-103), Platinum's camera (160 units over it, 22 degrees narrowing by Platinum's steps, near 0, far 300,
  a W-buffer), light (0, -1, 0 at RGB 28,28,28), black clear colour, no fog, no edges, and timing (a 16-frame fade in,
  SYUWA2 15 frames into the 86-frame run, a 20-frame fade out, the main screen only: the sub screen stays black as the
  script's fade left it; Platinum's sub screen is blank). DoDWWarp (resident) loads overlay 377 for it where no gimmick
  runs (Spear Pillar has none, so the gimmick overlays' address is free) and unloads it before the script's Warp. Without
  the files or their VRAM the stand-in runs (90 black frames, the sound). To see: the swirl after "We have to hurry!", its
  zoom, the fade, the warp to 1F after it; nothing of Spear Pillar drawn over it (the message window is closed by then).
- **Overlay 377's room**: the sky and the swirl took it to its end: it now ends at 0x21F59C0 (overlay 146, the encounter
  cut-in, starts at 0x21F59E0); dw_sky.c and dw_warp.c are compiled for size (#pragma optimize_for_size). About 44 bytes of
  code or data more fit before the next 32-byte step.

### On screen (build 4, 2026-11-08: main 9882a3e merged, a Spear Pillar start, then B4F's)
- **Spear Pillar's way in**: Cynthia's YES, "We have to hurry!", the fade, Platinum's swirl (the title demo's hole in the
  pillar's floor, the zoom into the vortex, the 16-frame fade in and the fade out), then 1F and its arrival scene (her lines,
  Giratina's shadow). The ReturnToField after DoDWWarp was a second FieldOpen on the open field (overlay 35 loaded twice:
  GFL_OvlCheckMemoryCollision's assert, as plat-tower found at the Frontier); pearl_story.py drops it (ca93cf3).
- **The sky and clouds** behind 1F, B1F, B4F and B5F, the clouds turning, the sky lighter on the lower floors.
- **The 1F elevator to B1F with Cynthia**: she is there in every frame across the floor change (counted frame by frame).
- **Platinum's sounds** (read from the resident section's flags): SYUWA2 at the swirl, SUTYA2 at a landing, FW089 for the
  elevator, FW463 at the waterfall, loaded from the archive and dropped when the ride ends.
- **The pop at a floor change** is the next floor's props: when B1F becomes this floor, B2F becomes the floor below and its
  moving platforms (kinds 4-6) load and appear. No Distortion World chunk has props (the rocks and platforms are all the
  world's props), so build 3's guess (the land's buildings) was wrong; Platinum's floor change loads the new floor below the
  same way.
- **B4F**: a start at (46, 22) under the ceiling hides the player from the base camera; walking east through (42, 22) turns
  the camera to (30, 220) as Platinum's trigger does. The east wall, the climb, the camera to (55, 240) below the player at
  (49, 8, 27), onto the ceiling upside down; Surf on the ceiling's water (the field move's cut-in, the hop); the waterfall
  down to B5F (the floor change with no black frame, the landing, two slow steps west) and the waterfall up to B4F's
  ceiling. The shadow at (41, 22) flies past.
- **B5F**: Azelf's hint starts at (43, 34) (a floating rock hides the player from the base camera there).
- **Found**: the floors ran at 20 frames a second (24 frames a step; 16 at Spear Pillar): turning off either the floor
  below's draw or the props' brings it to 30, the sky changes nothing. The props are now culled out of view
  (GFL_G3DSysDrawObjBBoxCull, e4f78874f1).
- **Found**: the surf Pokémon sat apart from the player in the falls and on the ceiling. From Platinum's C: the mount's place
  is DistWorldSurfMountRenderer_AnimTick's (as ours, but the bob is +y on the ceiling too, and a waterfall's sprite offset is
  added to the mount as well), and Platinum turns the player's picture inside its billboard (DistWorldMapObjectRotator: a
  texture animation, about the picture's middle) where Black 2 turns the billboard about its feet: on the ceiling the picture
  hung a whole height under the feet. DwField_SpritePivot puts every turned person's billboard back where Platinum's picture
  is (7e6eeb74e3).
- **Found**: B5F's boulder at (41, 33) doesn't move west onto its hole with Strength on (the push event doesn't start): to
  look into on the next ROM.
- **Build 5** (the lead's combined Platinum build, rom_platinum, a clean base): walking on B4F takes 16 frames a step again
  (30 frames a second); the surf Pokémon sits with the player on the ceiling and in the waterfall.
- **Builds 5-7 in the test clone** (romt_platinum: cp -c of the base, test starts in it): B7F's Cyrus scene and his battle
  (progress 10), Cynthia's heal, the teleport at (15, 25) into the Giratina room (the fade, the room's lighter sky and
  faster clouds), the room's cry and first shadow and its platforms appearing (progress 11).
- **Found, fixed (96ca47d1eb)**: B5F's boulders didn't move with Strength on. Black 2 finds the boulder in front within
  1/4096 of the player's height; the land carries Platinum's plate fractions (16.0037 on B5F) and the world's boulders stand
  at whole heights (Platinum matches by tile). The front-actor search allows half a tile while the Distortion World runs
  (ov036 FieldPlayerGrid_FindFrontActor -> resident PearlB2_FindFrontActorByGPos, same size; Black 2's own otherwise). Seen:
  the boulder at (29, 22) pushed south falls through its hole to B6F's floor (y -13).
- **Found, fixed (28cc6b685f, aab4a6120a)**: tile events reached by the overlay's own actions never ran (the Giratina room's
  second shadow at 17 and Giratina at 14, reached by the platforms' jumps; a face's steps the same): PlatDW_CheckStep waited
  for Black 2's move observer, which ends only Black 2's steps. A new tile with the action over counts too, as Platinum's
  DistWorld_HandlePlayerPositionChanged runs on every change of place.
- **Build 8** (romt_platinum, --clean, decomp 8af6989eb3, the Giratina room start): the room's events in order (the first
  shadow at 24 and the platforms, progress 11; the second shadow at 17, 12; the arrival at 14, 13), Giratina's Origin Forme
  battle, the scene after it (progress 14), the portal at (15, 1, 12) turning, its YES ("leapt into the portal") to Sendoff
  Spring (32, 17) and Cynthia's scene there, no fog after the portal.
- **Found, fixed (8af6989eb3, on screen in build 8)**: after the battle the portal wasn't there and couldn't be used.
  Platinum runs a map's OnLoad (INIT_SCRIPT_ON_LOAD, fieldmap.c state RESET) before its Distortion World makes the floor's
  objects (state LOAD); the Giratina room's OnLoad sets the progress to 14 after the battle, so the portal's simple prop
  (progress 14 or more), the invisible portal person at (15, 13) (script 3) and Cynthia's words at (15, 15) (script 6)
  appear. Black 2 runs the field's load scripts (FieldRoutine_MapSpawnFinish) after the gimmick's init, and the floor's people
  were only reconciled there. Now the first update (only the field's routine updates the gimmick, after the load scripts)
  settles: a person not there whose condition holds is spawned from the event file (SpawnZoneNPCByUID: the spawn flag still
  hides one) and placed (AddMapObjectFromEvent's way), and the simple props' conditions are read again.
- **Found, fixed compile-only (093e14ee7b, for the next build)**: after the battle Cynthia stood at (15, 20), not (15, 17):
  she lost the first of her two jumps north (JumpDistortionWorldNorth 2: 3 tiles each, MovementAction_Jump_Step1). Platinum's
  AddDistortionWorldMapObject places the person in its command; here PlaceAdded places it on the next update, and
  SetActorWPosAll frees the command the script gave meanwhile, which the action list counted as the first jump done. The
  command is set again after the placing. To see: Cynthia lands at (15, 17) after the battle (tracked frame by frame with
  dwplay TRACK129: the command went 373 -> 255 the frame after it was set).
- **Overlay 377 is full**: with 093e14ee7b it ends at 0x21F59E0, overlay 146's start (pearlb2_overlays.py allows equal). The
  next fix there needs room first: dw_core.c is the one file not compiled for size (it is also the harness's, so a guarded
  `#pragma optimize_for_size` for MWCC only).
- Not seen in build 8: the landing dust (the Giratina room's walk north is all steps, no jump point's landing).

### Compiled since build 3, to check on the next build (plat-dw-rom)
1. The floor below's buildings (ride 1F to B1F: no pop at the change).
2. Cynthia through the elevators' floor change (no missing frame; one Cynthia after the ride).
3. Spear Pillar's way in: the swirl (above), then 1F.
4. The sky and clouds on every floor (above).
5. Platinum's sounds in each scene (above).
6. Then the rest of the film list: B2F onward (see "On screen").

### Builds 9 and 10 (plat-dw-rom, 2026-11-08 evening)
Decomp pearlb2-plat-dw-rom; test tree work/agents/plat-dw-rom/romt_platinum (--clean, in place). Shots in
work/agents/plat-dw-rom/shots/b9.
- **Overlay 377's room**: dw_core.c is compiled for size on MWCC (`#pragma optimize_for_size on` inside `#ifdef __MWERKS__`;
  the harness's clang build of the same file is unchanged): its code 7,280 -> 6,924 B. The link map (arm9.o.xMAP
  OV377_BSS_END) put the overlay's end at 0x21F5880, 352 B before overlay 146 (0x21F59E0). After this evening's three fixes it
  ends at 0x21F5920: **192 B left**. The next room, if needed: move the trio hints' and cascades' tables (about 300 B of
  dw_world.o's rodata) into the world tables file, or dw_warp.c (824 B, used only at Spear Pillar) into an overlay of its own.
  The harness after the change: 111 routes, 0 differ; --boulder 0 mismatches; --camera the worst 0.060 degrees.
- **Seen on screen, build 9** (the Giratina room start, 15,25): the room's events, Giratina's battle, the scene after it:
  **Cynthia lands at (15, 17)** with her two jumps north (093e14ee7b works; gr_after_113-146), Cyrus walking up the
  platforms, the camera south and back, the portal turning. B5F (705): the boulder at (41, 33) pushed west and the one at
  (18, 34) pushed east both fall through their holes to B6F's floor (y -13: b5f_west_fall_40, b5f_east_fall_40); the tile
  where the boulder stood is free after, the hole blocked. **Mesprit's hint** at (23, 33): it rises, circles the hole, the
  player turns with it, it sinks into the hole and is gone. The double jump at (20, 39). B5F's first elevator (21, 43) up to
  B4F.
- **Found, fixed (55148cc4da, built in build 10; the up ride not yet seen again)**: from the floor's change to the ride's end
  the new floor's own copy of the riding elevator was drawn as well (it stands once its flag is set at the change). On B5F's
  ride up to B4F the copy was above the player and hid him for about 40 frames (b5f_up_ride_dup_150). Platinum's
  ChangeMaps moves the riding platform's animator to the new floor (its template's destIndex), and
  InitMovingPlatformPropsForMapEx skips a platform that has one; DwWorld_AfterSwap now does the same.
- **Found, fixed (2a4c44e08d, seen in build 10)**: an elevator's ride ended on the other end's elevator and rode straight back
  (B5F (30, 33) down to B6F, then up again): the ride's end counted as a step (the tile events after the overlay's actions,
  28cc6b685f). The last checked tile is now the ride's end, as Platinum's EndMovement only sets the place. Build 10: B5F to
  B6F, the player stays on B6F (31, 29); the ride's frames clean, no black frame.
- **Found, fixed compile-only (b64a534b92, needs a build)**: turning on an elevator rode it (B6F's arrival faces the wall
  south; pressing up turns first, and the turn's end started the ride up). Platinum's Field_ProcessStep runs only after a walk
  (input->movement: AVATAR_MOVE_STATE_MOVING); Black 2's own step check is the same (fieldmap_event.c stepped:
  PLAYER_MOVE_STATUS_MOVE). PlatDW_CheckStep now asks for that. Without it no floor whose elevator arrival faces a wall can
  be left (B6F: the only way north is past its elevator).
- **Seen on screen, build 10**: B6F after the ride: the boulder from (29, 22) lies at (30, 19) (its kept place), Cynthia at
  (29, 42), the pits' people. **B1F's west wall with the pivot fix** (dwb1 start): the camera's turn, the jump onto the wall
  (the sprite turning over the jump, the landing dust), the walk along it, the jump back down at (11, 2, 22) to (12, 1, 23)
  (the sprite turning upright in the air, the dust). On the wall the picture stands with its feet to the wall, the shadow and
  the dust below it, flat, as Platinum draws them (its shadow and dust are not turned either: ov5_021F134C.c).
- **A save on a wall** (B1F, (11, 2, 22)): saved from the menu, then Continue in a new process: the player is back on the
  wall at (11, 2, 22), turned, the camera turned as before the save, "Distortion World" shown; walking on the wall works
  (b1f_wall_after_continue). (DeSmuME: the save is written ~900 frames after "saved the game"; a soft reset in the same
  process shows no CONTINUE, a new process with the written battery does.)
- **Stopped at 2.25 GB free** (the rule: no builds under 2.3 GB). Not yet seen: the up ride after 55148cc4da; B6F's pits,
  kept places after a push and the trio's bob (they need b64a534b92 built: B6F can't be left northward without it); B2F's wall
  and Cynthia; B3F's wall, Cyrus and the ghost props; the Turnback room.

### Builds 11 and 12 (plat-dw-rom, 2026-11-08 night)
Main 45694bc merged (version.SOLID_AT_BDHC), decomp at plat-test's 1d7c37c64e, gen re-run (pearl_story 0 problems).
- **SOLID_AT_BDHC in the Distortion World**, offline: every floor's chunks converted with it off and on (pearl_chunk.convert,
  both ways): 4,443 solid tiles change height (3,899 of them B2F's void; the others rocks' tops 23-40 units, or no ground,
  now the floor's 16), no walkable tile, and none of the tiles the world uses on solid ground (B5F's holes, B6F's pits, the
  Giratina room's 15,13). On screen the floors walk as before (B2F, B3F, B5F, B6F, the Turnback room: the walker's height,
  the camera, the people's heights unchanged).
- **On screen, build 11** (shots/b9):
  - **B6F after b64a534b92**: on the elevator's arrival (31, 29), facing the wall, pressing up turns without riding; the
    walk north, the double jump (31, 26) to (31, 24). With the trio "in B6F" (a test poke of the puzzle flags, dwplay
    PUZZLE: no hint is on the way from the boulder's island to B6F's elevator) Uxie, Mesprit and Azelf hover at (26, 22),
    (12, 26) and (40, 33) and bob (Uxie filmed: 32 frames, no flicker). **Uxie's pit**: the boulder from (30, 19) pushed south
    to (30, 22), then west into (29, 22): it drops into the pit, shakes, "Uxie: Piih!", Uxie flies off north and is gone, the
    boulder stays in the pit (b6f_uxie_pit_30, b6f_uxie_leaves_128). **Kept place**: after the push to (30, 22), a ride up to
    B5F and down again: the boulder is at (30, 22). The ride B6F up to B5F: no copy of the platform above the player
    (b6f_up_ride_88).
  - **B5F's up ride (21, 43) to B4F after 55148cc4da**: the player in view on the platform the whole ride
    (b5f_up_ride_fixed_150; compare b5f_up_ride_dup_150).
  - **B2F**: the jump onto the west wall at (16, 1, 23), the climb to (15, 9, 21) beside Cynthia, her talk ("Let's split
    up") and her walk down the wall to (15, 8, 20), the walk along the wall's top to (15, 9, 15), the jump onto the floating
    island (b2f_island_jump_56).
  - **Found, fixed (8275b704d2, seen in build 12)**: B2F's Cynthia stood upright on the wall, overlapping the player beside
    her (b2f_cynthia_upright_33): Place turns a person when the floor loads, before its picture exists (BLACT_NONE). The turn
    is now set each frame. Build 12: she lies on the wall turned 90 degrees like the player, and stays turned while she walks
    down it after her talk (b2f_cynthia_turned_04, b2f_cynthia_walks_turned_116). Her place after the talk, (15, 8, 20), is
    off the wall's drawn path (Platinum's own template for progress 5).
  - **B3F**: through the camera trigger (14, 1, 28) (a start at 12, 28 is past it: the camera stays at its base there, as in
    Platinum), the jump onto the west wall at (10, 1, 28), along it to (8, 2, 39), down. **Cyrus** at (18, 1, 20): he walks up
    behind the player, his talk with YES, walks back down and goes; the ghost platform at (18, 16) fades in when the player steps
    north onto (18, 21) (b3f_ghost_fade_08, b3f_cyrus_32). North of the double jump (18, 14) the player stands on the empty
    place of B3F's elevator (18, 10): it stands there only after the ride from B2F (flag 2), so a direct start shows the walker
    over the void (b3f_no_elevator_38): a test start's state, not a fault.
  - **The Turnback room** (709): the arrival at (46, 45); the camera trigger (46, 1, 37) turning the camera to (30, 220); the jump
    onto the east wall at (48, 1, 37), along it to (49, 1, 24), down to (47, 1, 25), the camera back to its base at (46, 25); the
    portal's YES: "leapt into the portal", Turnback Cave (11, 15) with Giratina at its altar (turnback_cave_after_portal_140).
  - **To compare with Platinum**: the Turnback room's portal (46, 1, 44) sits at the south rim of the room's square pit; from
    the base camera only a faint glow of it shows above the player's head, from the turned camera its light shows inside the
    pit (turnback_camera_portal_glow_30). Its place and model are Platinum's; whether Platinum's base camera shows more of it
    needs Platinum on screen. On the east wall's last tile the turned picture reaches past the wall model's end
    (turnback_east_wall_end_56): the picture is centred on the walker's place, as Platinum's turned billboard is.
- **The puzzle's finish** (build 12 code, a B5F start): the middle boulder pushed off B5F for real; the other two falls (seen
  for real in build 9) set by a test poke of the puzzle flags (Mesprit's and Azelf's "outside", the trio "in B6F"), so those two
  boulders lie at B6F's templates (19, 30) and (42, 29), not a tile on. **Azelf's pit**: (42, 29) pushed west twice, then
  south into (40, 30): it drops, "Azelf: Piiuw!", Azelf flies off (b6f_azelf_pit_14, b6f_azelf_leaves_92). **Mesprit's**:
  (19, 30) pushed west seven tiles, then north into (12, 29): "Mesprit: Piih!", Mesprit goes (b6f_mesprit_pit_12). Then Uxie's:
  all three in their pits (puzzle flags 0x1c0), and Cynthia's talk at (29, 42) (progress 7): she walks to B6F's elevator
  (28, 46) (b6f_cynthia_to_elevator_165). The ride down with her to B7F (11, 1, 54), 50 tiles, no black frame.
- **Found, fixed (a235492975, build 13)**: on that ride Cynthia turned from facing down to facing up at the floor's change
  (b6f_ride_cynthia_10, b7f_ride_cynthia_turned_60): the new floor's 128 comes from the event file facing its template's way,
  where Platinum's ChangeMaps keeps the same map object. And her tile stayed 33 up after the ride (set at the change,
  mid-ride; the player's front check matches by tile): Platinum's EndMovement sets her Y to the player's. Both fixed; seen in
  build 14 (a B6F start with progress 7 and PFLAG_09AD, env dwb6): she keeps facing right through the change and ends at
  (10, 1, 52).
- **Found, fixed (cbc01c6ad2, build 14)**: at an elevator's floor change the view jumped about 10 pixels (B6F to B7F, logged
  frame by frame: the camera's target 28 units over the player before the change, 4 after). Black 2's camera follows the
  player's height 6 frames late, as Platinum's camera history does (24 units at the rides' 4 a frame); SwapFloor turned the
  delay off at the change. Platinum's floors share one world, so its history needs no move; here the player is moved into
  the new floor's tiles, and now the delay's stored places are moved by the same height. Build 14: the target stays 28 over
  the player across the change, every frame filmed with no jump (b7f_change_no_jump_14).
- Overlay 377 now ends at 0x21F59C0: 32 B left before overlay 146. The next fix there needs room first (see above).
- Not seen: the Griseous Orb's ball at (19, 1, 25) (it is there: ACTORS shows uid 129, model 110); a wrong pit; B2F's talk from
  below the wall.

### The last round (plat-dw-rom, 2026-11-08 night, builds 15 and 16)
- **Overlay 377's room**: overlay 9's small tables moved out of the overlay into the world's file (a/2/9/5 98:
  b2tools/platinum_dw_world.py consts_blob, include/pearlb2/plat_dw.h DwWorldConsts, header offset 5, constsOffset): the four
  camera triggers (the Giratina room's platforms, the waterfalls' three), the platforms' bob, the trio's hover and bob,
  Giratina's palette, 1F's Giratina shadow template, and the hint lists (Azelf's, Mesprit's two, the player's), 368 B.
  The section's bytes are the overlay's old rodata, byte for byte (compared against the built arm9_ov377.bin at the link
  map's addresses). DwWorld_Create points wr->k at them and refuses a file without them. The harness after: 111 routes,
  0 differ; --boulder 0 mismatches; platinum_dw_world.py --check: the dump agrees with pokeplatinum's C. Overlay 377 ended at
  0x21F58A0 after the move (320 B free); with the talk fix below it ends at 0x21F58E0: **256 B before overlay 146**.
- **On screen, build 15** (decomp 7e7560b6d3: the tables from the file):
  - **A wrong pit**: on B6F Mesprit's boulder (at its template, 19, 30) pushed north into (19, 29): it sinks into the pit
    and is gone (b6f_wrong_pit_22); the puzzle flags show it back on B5F (Mesprit's "in B5F" set, "outside" clear). After a
    ride up, B5F has it at its own place (18, 34). As Platinum (TickToWrongPit: 40 frames more down, then deleted, B5F's).
  - **The Griseous Orb** (the Turnback room, a start at 17, 25): the ball at (19, 25); A from (18, 25): "AAAAAAA found a
    Griseous Orb!", "AAAAAAA put the Griseous Orb in the ITEMS Pocket." (turnback_orb_found_30); the Bag's Items pocket has
    item 112 (the Griseous Orb), flag 1490 set, the ball gone. Then the whole way back to the portal (the land's double
    jumps along row 43, x = 33 north, the jump east at (33, 28), the east wall from (48, 25) to (49, 36) and down), its YES
    to Turnback Cave (11, 15), Giratina's battle there (its altar: talk, the battle, "Giratina disappeared..."), the cave's
    portal (A at the altar, YES) back into the room (46, 45): the ball isn't there (only the portal's person).
  - The trio bobbing on B6F, the boulders, the rides: as before with the tables read from the file.
- **Found, fixed (b7b4aa93f7, build 16)**: Cynthia's talk from below B2F's wall didn't start. Platinum's
  Field_DistortionInteract takes the tile in front from the face's step in the moving direction
  (PlayerAvatar_GetFacingDistortionWorldPos); Black 2's FindActorForInteraction takes it from the sprite's facing, which the
  face turns (from (15, 8, 20) pressing up it looked at (14, 8, 20)). fieldmap_event.c's call now goes to the resident
  PearlB2_FindFrontActorByGPos (same size; the Strength push's already did), which asks the overlay's faceFront hook while the
  Distortion World runs (nothing changes on the land) and matches within half a tile's height. The resident section grows
  32 B (0x220B320). Build 16: from (15, 8, 20) pressing up, A: Cynthia's talk, then the player steps aside along the wall
  and she comes down beside him, both turned (b2f_talk_from_below_116).
- **The moved tables on screen, build 16**: Azelf's hint at (43, 33) (its list: up, north, back, down and gone; the puzzle
  flags "seen" and "in B6F" set: b5f_azelf_hint_34); 1F's arrival scene with Giratina's shadow flying west to east from the
  file's template (f1_shadow_from_file_319); B6F's trio bob and the rides in build 15.
- **The Turnback portal against Platinum's data**: its place is Platinum's (VecFx32_SetPosFromMapCoords and
  MAP_OBJECT_COORD_CENTER_TO_FX32 of the template's tile, as TileCenter), its offset is Platinum's
  sPropInitialPosOffsetByKind[PROP_KIND_PORTAL] (0, -14, +8 units: the model sits 6 units under the floor at the tile's south
  edge), its model is the dump's file (field effect 148), it is drawn after the map with the depth test as Platinum's field
  effects (DistWorldSimpleProp_AnimRender), and the camera's direction is Platinum's (the harness: every angle within 0.06
  degrees). It stands at the south rim of the room's square pit (the land's model, Platinum's), just under the floor: from
  the base camera, south and above, the floor of the player's tile and the rim hide most of it, so Platinum's base camera
  shows the same faint glow. The Giratina room's portal shows whole because nothing stands between it and the camera there. No fix.

## The test ROM's fixes (plat-dwplay, 2026-11-09)
The user played the Spear Pillar test ROM in melonDS (software renderer, threaded, JIT off, DS mode, direct boot): the
sprites looked "downgraded" everywhere in the Distortion World, and the game hung for good on an elevator. Decomp
pearlb2 32454a0d2a, dw_field.c.

### The hang: a NULL free at the first floor change
- **Cause:** the floor below's mapper (LoadBelow: FieldG3DMapper_Create) makes a prop system of its own
  (FieldPropSystem_Create: an uncleared block; it sets the handles, resources and instances, not the bundle or the
  textures). It never loads an area (its chunks take this floor's prop system). Freeing the mapper (FreeBelow: every
  floor change, and the gimmick's end) ran Black 2's FieldPropSystem_Free, whose FieldPropSystem_FreeResBundle calls
  GFL_HeapFree(resBundle) unchecked: GFL_HeapFree(NULL). GFL_HeapFreeCore reads the block header 0x1C bytes before the
  pointer, at 0xFFFFFFE4: no protection region covers it (crt0's INITi_InitRegion: the BIOS region is 0xFFFF0000-0xFFFF7FFF),
  so the DS takes a data abort and stops for good. melonDS emulates the protection unit; DeSmuME doesn't (its read gave a
  wrong magic and the free returned quietly), so every DeSmuME ride worked.
- **Seen in DeSmuME** (execution hooks on the functions, the 11:02 test ROM): at the 1F ride's floor change
  FieldPropSystem_FreeResBundle runs on the floor below's prop system (field heap, resBundle 0, textureResource 0) and
  GFL_HeapFreeCore is called with r0 = 0 from GFL_HeapFree. DeSmuME can't show it as a hang (no protection unit, and no
  setting of its turns one on: its advanced bus timing is already its default and changes nothing here); the hooks show
  the call melonDS stops on.
- **Fix:** FreeBelow takes that prop system out of the mapper before FieldG3DMapper_Free and frees its block itself (it
  owns nothing else). Black 2 never frees a prop system that didn't load an area, so its own code needs no change.
- Also hit by the same path, so also fixed: leaving the field anywhere in the Distortion World (a battle, the Bag, a
  warp: PlatDW_End -> FreeBelow) and the waterfalls' floor changes.

### The sprites: the billboards scaled by the views' ratio
- **Cause:** ApplyCamera puts Platinum's camera on (667 units, field of view 1473 + 192, Giratina's room 1473); Black 2's
  billboards are sized for the zone's own camera (the Distortion World's zones: camera row 46, 237 units, field of view
  3640). On screen a sprite drew at 86.2 / 107.3 = 0.80 of its size, rows of texels dropped by the nearest-neighbour
  minification.
- **Fix:** the people's billboard scene (Black 2's scale 7) and the field effects' (8: the shadows, the landing dust)
  are scaled each frame by (667 x tan(the camera's field of view)) / (the zone's camera's distance x tan(its field of
  view)): 1.245, Giratina's room 1.099. The zone's camera is read from its row of ARCID_FIELD_CAMERA_DEFAULT at the
  gimmick's start (FieldCamera_ReadDefaults: right after a Continue or a battle too). Platinum's view of the world stays
  as it is; a texel is a pixel again, as everywhere else in the game. The scales go back to Black 2's at the gimmick's
  end. DwField_SpritePivot takes the scene's scale already.
- Overlay 377: +244 B of code; it now ends exactly at overlay 146's start (0x21F59E0): **no room left**.

### On screen (DeSmuME, the v2 test ROM, 2026-11-09 evening; decomp 32454a0d2a)
work/agents/plat-dwplay (the agent folder; shots in v2/, b1/, b4/, gr/, comparisons at 4x in cmp/).
- **The rides:** Spear Pillar's YES, the swirl, 1F's arrival scene, the walk and double jumps to the slab, Cynthia's line,
  the ride to B1F (40, 1, 19) with her, B1F's frame scene; then B1F's elevator back up to 1F (19, 1, 44). Hooked: no
  GFL_HeapFreeCore of a pointer outside main RAM in 223 frees (the first ride) and 99 (the second), and Black 2's
  FieldPropSystem_Free not called at either floor change. The Bag opened and closed on 1F (the field's end and start:
  PlatDW_End -> FreeBelow): 1156 frees, none outside RAM; the sprites at full size after it.
- **The sprites:** the people's scene 8.73 (7 x 1.247), the effects' 9.98; the Giratina room 7.71 (x 1.101). The player
  on 1F, on B1F's west wall (turned 90 degrees), on B4F's ceiling (upside down) and in the Giratina room is the size of
  the overworld's (Celestic) at 4x, every row of texels there (cmp/f1_before_after_celestic_4x.png,
  b1f_wall_vs_celestic_4x.png, b4f_ceiling_vs_celestic_4x.png, giratina_room_vs_celestic_4x.png); Cynthia beside him
  at the slab, both with their shadows (f1_slab_cynthia_4x.png). DwField_SpritePivot follows the new scale (the wall and
  ceiling pictures sit on their faces as before).
- **Left as it is, to decide:** the surf Pokémon (a 3D model, not a billboard) keeps its size, so the rider is 1.245
  times bigger against it than in Black 2's own surfing; on B4F's ceiling the bigger rider hides most of the mount
  (cmp/b4f_surf_ratio1_vs_fix_4x.png: the old scale left, the new right). Scaling the mount's model by the same ratio
  (in MountTCB, and on the land too) would keep Black 2's proportions, but overlay 377 has no room: first move dw_warp.c
  (Spear Pillar's swirl, 824 B) to an overlay of its own, or ScaleBillboards to the resident section. Likewise not
  scaled: the "!" bubble (a 3D model 22 units over a person, so it sits lower on a bigger sprite) and the trio's rise out
  of the floor (they start their sprite's height under it: a bigger sprite shows a little sooner). Not looked at here:
  Cyrus, the trio, a "!".

### The test player's memory (2026-11-09)
The Mac ran out of memory twice during this work (41 GB). The cause: DeSmuME's memory hooks (py-desmume
register_read and register_write) keep an entry per watched byte: a hook over 16 MB took the emulator to 1.99 GB, and the
first, over about 3.6 GB of addresses (the protection unit's unmapped ranges), grew without bound. The agent's copy of
dwplay.py (work/agents/plat-dwplay/tools) now refuses a hook over 64 KB, and its film writes each kept frame to disk
(OUT/film_NNNN.png, renamed by SHEET) with only names in memory and its move log capped; every run goes through
work/agents/memwatch.sh 3000. Measured peaks: 172 MB (a boot), 277 MB (a ride with execution hooks), 1.33 GB (the
build_rom --clean, through memwatch 6000).


### v2 still stopped in melonDS: Giratina's shadow freed as if it had textures (v3)
- **Seen by the lead** (melonDS's ARM9 GDB stub on the frozen v2, work/agents/plat-dwplay/gdb_snap.sh and gdb_snap.txt):
  abort mode at the BIOS's dead loop (0xFFFF0104; the abort handler itself aborted, sp_abt 0), lr_abt 0x2049548: the
  instruction at GFL_G3DResFreeTexData+0xC, `ldrh r1, [r4, #0x10]` with r4 = 0. NNS_G3dGetTex returned NULL (r1 and r2:
  the 'BTX0' and 'BMD0' signatures it compared): the resource is alive and its data loaded, but its file has no TEX0
  block. r6 = 0x22fb79c (the DwWorldRun) and r5 = 20: FreeProp(wr, 20), Giratina's shadow; lr_irq was inside FreeProp.
- **Cause:** the shadow's model has no textures of its own. LoadProp's GFL_G3DResUploadTexData checks for that (it
  returns FALSE); FreeProp called GFL_G3DResFreeTexData unconditionally, which reads the texture block's flags at
  NULL + 0x10. The arrival scene on 1F loads the shadow; the first floor change (the 1F ride) frees it (SyncProps): v2
  got past v1's NULL free (FreeBelow comes first in SwapFloor) and stopped here, in DwWorld_AfterSwap. Every Distortion
  World field end with the shadow loaded did the same (PlatDW_End -> DwWorld_Free -> FreeProps).
- **Found in DeSmuME too** (the v2 ROM, the 1F ride): execution hooks (dwplay EXECR) on FreeProp, LoadProp and the G3D
  frees: FreeProp(20) -> GFL_G3DResFreeTexData(0x2307340, data 0x23304b4), a file whose header lists no TEX0.
- **Fix** (decomp 63ed4b4e1f): FreeProp frees texture data only for a file that has some (NNS_G3dGetTex not NULL). Overlay
  377 +16 B: it still ends at 0x21F59E0 (the data section's padding took it).
- **The checks** (work/agents/plat-dwplay/tools/dwplay.py CHECKS, for the next rides): execution hooks at GFL_HeapFree,
  GFL_G3DResFree, GFL_G3DResFreeTexData, GFL_G3DMdlFree, GFL_G3DAnmFree and GFL_G3DActorFree that flag a pointer outside
  main RAM, a resource freed again (magic 0x48be), and a GFL_G3DResFreeTexData of a dead resource, of NULL data or of a
  file with no TEX0. On v2's 1F ride they flag exactly this call (1 of 122). DeSmuME's memory hooks can't find a NULL plus
  a small offset: they report DTCM accesses by their offset in the same range (every stack access lands in 0x18-0x34),
  so only execution hooks at chosen functions are reliable.
- **On v3** (DeSmuME, the checks on throughout): Spear Pillar's YES, the swirl, 1F's arrival scene with the shadow, the
  walk and the 1F ride to B1F: 1,609 frees, none flagged. The Bag opened and closed on 1F with the shadow still loaded
  (PlatDW_End frees it: FreeProp(20) ran): 1,410 frees, none flagged, the field back as before. B1F's elevator (33, 1, 10)
  down to B2F (18, 1, 45) from a B1F start: 97 frees, none flagged.


### v3 in melonDS: the rides fine; the shadow on a wall and 1F's portal (v4)
- **The player's shadow on a wall** (the user: "hanging in space when you're walking sideways on the wall"). Black 2's
  shadow (fldeff_shadow.c) lies flat at the actor's place, so under a picture turned onto a wall it hung about a
  half-height below the face (it hung the same way before the billboard scale: the scale didn't move it).
  **Platinum has none there:** its Distortion World dresses the player as OBJ_EVENT_GFX_DIST_WORLD_PLAYER_M/F
  (ov9_02249960.c InitPlayer), whose render details have no shadow (object_event_gfx_data.c: hasShadow FALSE), on the land
  as on the faces; Cynthia and the others keep theirs (their sprites have one). **Fix** (decomp 2c61661ba6): the player's
  movement flag 0x8000 (Black 2's own "no shadow", fldeff_shadow.c) set each frame in the Distortion World, cleared at
  the gimmick's end (the actor outlives the field). The billboard scales are shifts now and their reset at the end
  went (the scenes go with the field): overlay 377 is 40 B smaller than v3's.
- **1F's portal flickering with a black bar** (the user: on every view of it; v3's melonDS shot: a bright core, a dark
  band, a purple arc). PROP_KIND_PORTAL, data/mmodel/fldeff.narc 0x94: one 32 x 32-unit quad, texture yabu_ana01 (64 x 64
  A3I5: an opaque white core, a translucent purple ring), material alpha 31, polygon ID 0, back faces culled, fog on, no
  translucent depth update; drawn as Platinum draws it (DistWorldSimpleProp_AnimRender: no SetPropOpacity, its own ID).
  **Its joint animation (0xC1, 241 frames)** holds a constant translation (0, 12.57, -7.18) and a rotation that stands
  the quad up 55 degrees and spins it about its own normal: the normal stays (0, 0.573, 0.819) on every frame (facing the
  camera, 0.92), so it never turns its back. With Platinum's offset (0, -14, +8) the disc's middle is at (552, 22.6, 472.8)
  local: **on the cliff slope** that rises north of the arrival row (y 18 to 30 over z 476 to 468, normal
  (0, 0.555, 0.832), 56.3 degrees): parallel within 1.3 degrees and 0.2 to 0.6 units behind its face. The DS's Z-buffer
  step there is about 0.08 units (15-bit z/w at 670 units, near 150), so the two fight in melonDS (an accurate DS
  renderer): the flicker, and the band where the dark slope wins; the top of the disc clears the slope (the purple arc).
  DeSmuME's depth hides it whole. Ruled out: the polygon/vertex RAM (the lead's melonDS reading: DISP3DCNT 0x6b9, no
  overflow), fog (8/127 at most in view), a translucent ID clash (the land there is opaque PLTT16), the box test (its box
  isn't flat), edge marking and anti-aliasing (translucent pixels take neither). Platinum's field sets the 3D up the same
  way (easy3d.c: toon, anti-aliasing, alpha blending; InitFog and InitEdgeColors; G3_RequestSwapBuffers(AUTO, gBufferMode)
  with camera.c's Z for a perspective camera); our clear is Black 2's (black, alpha 31, ID 0) under the opaque sky quad
  (ID 63), Platinum's black at alpha 0 (ID 63) over BG2: not at play here.
  **Fix, a deliberate departure from Platinum's exact offset** (the lead's approval, 2026-11-09): the portal drawn 2 units
  along its normal, (0, +1.15, +1.64) on top of Platinum's (0, -14, +8), because at Platinum's own place it depth-fights
  the 56.3-degree slope it stands on (0.2 to 0.6 units behind the face, at 670 units from the eye). Data only:
  b2tools/platinum_dw_world.py PORTAL_LIFT, added when the world file is packed; the JSON keeps Platinum's offset, so
  `platinum_dw_world.py --check` still compares it with pokeplatinum's C (ok). The model is shared, so **the Giratina
  room's and the Turnback room's portals move by the same 2 units** (the Turnback one looked buried the same way).
- **v4** (2026-11-09 night: decomp 2c61661ba6, PearlB2 plat-dwfix 7e96e9b; --clean, a Spear Pillar start, SHA1 6c24392b;
  on the Desktop as Griseous_Platinum_DW_test_from_Spear_Pillar_v4.nds). In DeSmuME (work/agents/plat-dwplay/cmp): 1F's
  portal now shows whole beside the arrival point, the swirl glowing at the cliff's foot, from the arrival (33, 30) and
  from (30, 30) (portal_v3_vs_v4_4x.png, portal_v4_three_views.png; v3 showed a sliver); whether melonDS still flickers
  is the user's to see. No shadow under the player on 1F or walking sideways on B1F's west wall at (11, 3, 20-22)
  (wall_shadow_v3user_vs_v4_4x.png: the user's v3 shot left). The 1F ride to B1F with the free checks on: 238 frees, none
  flagged. Not checked: the Giratina room's portal (a start there needs a quick build, and build_rom wants 2 GB free;
  1.7 GB were).

## The last differences (plat-dw3, 2026-11-11)
Decomp branch pearlb2-plat-dw3. The brief's list was plat-dw-finish's "Not built" list; plat-dw-rom built most of it after
(above). What was really left, and what this piece did:

### Room in overlay 377: the way in has its own overlay (382)
- Overlay 377 ended 32 B before overlay 146. Its tables pool was already gone (plat-dw-rom: a/2/9/5).
- dw_warp.c (Spear Pillar's swirl, 818 B) calls nothing of overlay 377's (its imports: arm9, the field, the resident
  section), and runs where no gimmick does. It is now overlay 382 (src/pearlb2/plat_dw_warp/), at the gimmick overlays'
  address like 377: DoDWWarp loads 382 instead of 377 (resident plat_dw_hooks.c), unloads it before the Warp, as before.
- The wiring: the decomp's configure.py and tools/pearlb2/link_overlays.py (OV382, AFTER(OV084, OV085)), include
  pearlb2/plat_dw.h PLATDWWARP_OVERLAY_ID; PearlB2's b2tools/pearlb2_overlays.py (382 in the ROM's table and in the gimmick
  room's check) and patches/platinum_dw.py (gPlatDWWarp written into arm9_ov382.bin: 382 and 377 share an address, so the
  address alone can't say which binary holds it).

### The surf Pokémon at the billboards' scale
- plat-dwplay scaled the people's billboards by the views' ratio (1.245; the Giratina room 1.099) so a texel is a pixel at
  Platinum's camera, but not the surf Pokémon (a 3D model): the rider was 1.245 times too big for the mount.
- Now MountTCB (dw_field.c) scales the whole rig by the same ratio about the rider's feet (its billboard's place, the
  actor's place and draw offsets, as namipoke reads them): the Pokémon and, when it shows, its wake, their places and sizes.
  Everywhere while surfing: the land's water (Black 2's own placement), B4F's ceiling and the waterfalls (Platinum's pose,
  plat-dw-rom). In the hop on and off (namipoke's mode 0) the Pokémon is scaled at its own place, so it doesn't slide.
  Once a field frame (the gimmick's update, then FieldEffects_Update, then MountTCB): never scaled twice.
- Not scaled: the bob's height (1-4 units, both rider and mount move by it) and the splashes (field effect 8: not used in
  the Distortion World's water as far as the scripts go).

### The sky: no BG layer; the backdrop does the 2D sky's one job
- **No layer is free.** Black 2's field: BG0 the 3D, BG1 the talk windows (field_msgbg.c MSGBG_BG), BG2 the system
  windows (MSGBG_BG2: YES/NO, lists, item messages, with BLDCNT's blend), BG3 the place name (field_place_name.c). Each holds
  things drawn in front of the 3D, and a sky must be behind it: one layer can't be both. Taking BG2 the way Black 2's face-up
  does (fld_faceup.c: MsgBGPrinter_ReleaseSysFrame, RequestSysFrame) would lose the sky while any system window shows; BG3
  would lose it while the place name shows. Platinum has a spare layer (its field's BG2, the flash layer); Black 2 has none.
- **What a 2D sky does that the 3D sky can't:** Platinum blends its 3D over the BG2 sky (G2_SetBlendAlpha(BG0, BG1 | BG2 |
  OBJ | BD, 0, 16)). Its fog (alpha 16, density 2 a step: 62 of 128 from depth 0x7800, about 1,030 units from the eye at
  near 150 and far 1,700) leaves the far land at alpha 23 of 31, so about 23% of the sky shows through it. The floor below
  is all that far (the view ray reaches it at about 1,260 units). With the sky in the 3D, those pixels cover the sky's quad
  and nothing showed through: the floor below was darker and not blue-tinted.
- **Done:** the backdrop (BG palette 0's colour 0; never seen itself, the sky's quad covers the screen) is the sky's colour 1
  at the darkness level, and BD a second blend target, both set each frame (dw_sky.c DwSky_Update; Black 2's blends and the
  place name's palette write over them), put back at the gimmick's end. The 3D's see-through pixels (only the fogged ones:
  the sky, the clouds and every translucent prop over opaque land stay at alpha 31) blend with it as Platinum's do with
  BG2. Exact where Platinum's sky behind is colour 1: its top 136 lines (screen rows 0-16 are tile 1, colour 1 alone,
  tw_arc_etc 0-2). Where it is the gradient (the bottom 56 lines: colours 1 to 7, checkered in rows 17-22) or a cloud, the
  fogged land takes colour 1 instead: at most 23% of the difference.
- Screen fades are the master brightness (gfl/fade.c), which comes after the blend: unchanged.

### Checked offline, no change needed
- **Giratina's two-frame picture** (plat-dw-rom's GiratinaFrame): Platinum's frame sequence giratina_origin.bin is 2
  entries, start frames 0 and 10, textures 0 and 1, palettes 0 and 1 (billboard_gfx_sequence.h's layout). Its sheet
  (mmodel.narc 393) has textures giratinaorigin.1 and .2 and palettes giraori.1 and .2; both palettes' dictionary entries
  point at the same 32 bytes, so switching the texture alone is Platinum's picture. The loop is 20 frames, as ours.
- **The lake trio's renderers**: as plat-dw-rom built them (B1F Mesprit's fade, B6F's bob); seen in builds 10-11.
- **The '!' bubble**: built after the merge (decomp 89bb3e2824, below "The '!' at Platinum's place").
- **The trio's rise on B5F**: the trio starts under the floor and rises through it; its picture is 1.245 times taller
  (about 36 units, not 29), so its top shows about 2 frames sooner (4 units a frame) and goes about 2 frames later on the
  way down. The heights it rises to are Platinum's (17, 13, 9 tiles). On the list.

### For the combined test (plat-dw3)
30. **Surf on B4F's ceiling** (703, the ceiling's water by (49, 9, 27) and on): the Pokémon under the upside-down rider is
    in proportion with it (as on Black 2's own water, not 0.8 of it; compare plat-dwplay's cmp/b4f_surf_ratio1_vs_fix_4x.png).
    The hop on and off: no jump in the Pokémon's size or place at the hop's start or end.
31. **The waterfalls** (B4F x 47, z 42-45, y 10 down; B5F y 0 up): the rig in proportion through the fall, the orbit and the
    floor's change; after the landing on B5F's water, the two slow steps west with the wake behind (in proportion, no wake
    on the faces).
32. **The floor below through the fog** (1F's (34, 30) arrival, looking at B1F below; B4F at (46, 22) under the ceiling):
    the far land and the floor below a little blue (the sky's colour through about a quarter), not just darker. The sky
    itself, the clouds and the near land as before. The place name's banner on entering, and its fade: as before.
33. **The '!'** (decomp 89bb3e2824) on 1F's arrival scene (the player and Cynthia notice the shadow), B6F after the puzzle
    (Cynthia at (29, 1, 42)), the Giratina room after the battle (both notice Cyrus): its bottom at the top of the head (not
    over the face), half the picture's width, the hop as before; in the Giratina room a little smaller (its narrower view).
    Outside the Distortion World (any trainer's '!', Pearl and Diamond): Black 2's own, unchanged.
34. **The trio's rise on B5F** (705: Uxie at (29, 1, 19), Azelf at (43, 1, 33), Mesprit at (23, 1, 33); flags: the puzzle's
    "seen" bits clear, a B5F start): the picture comes up through the floor with no pop on its first frame and sinks the
    same way.
35. **The way in** from Spear Pillar (now overlay 382): Cynthia's YES, "We have to hurry!", the swirl, 1F. No "An error has
    occurred" (overlay 382 is loaded where no gimmick runs; GFL_OvlCheckMemoryCollision would assert otherwise).

### The '!' at Platinum's place (plat-dw3, after the merge; decomp 89bb3e2824)
- **Black 2's** (ov036 fldeff_gyoe.c): a 16-unit quad (arc 74 file 50, its box y 0 to 16), its bottom 22 units over the feet
  in the camera's up, plus a hop (6, then 2 less a frame: up to 12 units). At Platinum's camera it sat 19.7 pixels over the
  feet of a 32-pixel picture: over the face.
- **Platinum's** (ov5_021F5A10.c): the same 16-unit quad (fldeff.narc 85, box y 0 to 16) and the same hop, at the map
  object's place + (0, 32, 1): the top of its people's 32-unit quads (mmodel.narc 421, box y 0 to 32). So its bottom sits on
  the head, and it is half the picture's width. Both games' quads have no billboard node; Platinum's people and its '!' are
  in one plane, so that relation is the one to keep.
- **Here:** our people are Black 2's 32-pixel pictures, a texel a pixel at Platinum's camera (ViewSize / 3 units tall, in the
  camera's up). Platinum's numbers are taken at that scale, s = ViewSize / 96 (1.12; the Giratina room 0.99): the bottom at
  s (32 + hop) in the camera's up, the quad s times its size. Black 2's fldeff_gyoe.c keeps its size: its offset's turn
  (FldeffGyoe_RotateByCamera's MTX_MultVec33) and its draw (FldeffGyoe_DrawTask's GFL_G3DSysDrawObjBBoxCull) call the resident
  PearlB2_GyoeMultVec33 and PearlB2_GyoeDraw, which are Black 2's while gPearlB2DWBubbleScale is 0. Overlay 377 sets it each
  frame (ApplyCamera) and clears it at the gimmick's end, so only the Distortion World differs (Pearl's and Diamond's
  behaviour is unchanged; the decomp is shared, so their code has the two new call targets). Platinum's z + 1 isn't taken:
  Black 2 draws the bubble moved toward the camera instead (its depth offset), as before.
- Sizes: the resident section +112 B, overlay 377 +32 B (it ends at 0x21F57E0: 512 B before overlay 146). decomp.py changed:
  only FldeffGyoe_DrawTask and FldeffGyoe_RotateByCamera differ in ov036 (their call targets); the layout check passes.


## Rows 31, 33 and 34 on screen (plat-dw4, 2026-11-12; decomp c119aa3105, eff8c48668, 6eb195689e)
The final 1.0 build failed rows 31 and 33 and couldn't run row 34 (plat-dw3). Tested with test starts in plat-rel's
rom_platinum (the release code), DeSmuME, RAM reads; pictures in work/agents/plat-dw4/.

### Row 33, the '!': no bug
- RAM during 1F's arrival scene: the player at (33, 1, 30), wPos (536, 16, 488); Cynthia at (34, 1, 32), (552, 16, 520).
  Every draw offset 0 for both.
- At rest both bubbles' bottoms sit 32 px over the feet: the top of each 32-pixel frame. That is Platinum's place (the
  object's place + 32: the top of its 32-unit quad; the DW player's own model, mmodel.narc 439 hero_rote, is the same
  32 x 32 quad from the feet up). plat-dw3's frame caught the player's '!' at the top of its hop (+12 px): his starts 4
  frames after Cynthia's (Platinum's Delay4), so the two hop at different times.
- What still differs is the art: Lucas (Platinum's pixels, moved down 1 in Black 2's box) starts at row 8 of 32, so his
  '!' floats about 11 px over his beret (Platinum: row 7). Cynthia here is Black 2's own sprite (row 1-2), so hers sits on
  her hair; Platinum's Cynthia (mmodel.narc 117 champion) starts at row 5-6, a few pixels higher.
- Picture: row33_1f_hop_and_rest_4x.png (left the hop, right at rest; green: the frame tops).

### Row 31, B5F's water: the doubled rider was Black 2's reflection
- Cause: our water is Black 2's (pearl_chunk: WATER_SEA and WATER_RIVER -> class 0x3d, flags 0x56; 0x40 = reflective).
  Black 2 draws a reflecting actor's picture flipped, 12 units south and 33 under the water (fldeff_reflect.c). The DW's
  floors are rooms for people_depth (slope 255), and that upright depth put the sunk copy in front of the rider and the
  mount: on B5F it covered his lower half and the mount. Facing west the copy was there too, under the mount's tail.
- Platinum has none there: its DW surf player (OBJ_EVENT_GFX_DIST_WORLD_PLAYER_M_SURF) has hasReflection FALSE, and the
  DW's water is TILE_BEHAVIOR_WATER_SEA, which reflects nobody (TileBehavior_HasReflectiveSurface).
- Proved with a RAM write of Black 2's own "reflection hidden" flag (actor flag 0x4000, which fishing uses): the copy goes
  and the rider sits on the mount (row31_b5f_reflection_before_after_4x.png: before down, left; after down, left).
- Ordinary Sinnoh water (Route 208, 383 (400-403, 718-720), overworld, flat depth): the rider looks normal facing down and
  left (row31_r208_ordinary_water_4x.png, r208/r208open.png). So it is ours, not Black 2's normal look.
- Fix, first (c119aa3105): flag 0x4000 on every actor each frame while the DW runs. Then (the lead: the same doubled rider
  surfing south in Victory Road B1F, all versions) a rule in the resident in its place (eff8c48668, narrowed in
  6eb195689e): fldeff_reflect.c's test of that flag calls PearlB2_ReflectionHidden (same size; resident/people_depth.c).
  TRUE for everyone while the Distortion World runs (PearlB2_DWActive: its hooks are set), as Platinum has none there; and
  where the people stand upright (slope not 0: every room and cave) for the player on Surf only (the surf form's object
  code). Walkers keep Black 2's reflections there, and the overworld (slope 0) keeps them all: Black 2's water is the look
  (the user's art direction). The mount is a 3D model with no reflection.
- So the room-type zones with river water keep their walkers' reflections (the Great Marsh's six areas, Pal Park, Amity
  Square, the Battle Tower's multi arena), as gen 4 shows them (TileBehavior_HasReflectiveSurface counts WATER_RIVER).
  Gen 4's sea-water caves show none; ours show a walker's beside the water, Black 2's look.

### Row 31, the wake: ours
- The ceiling's surf (DwSurfTCB) turns the wake off (no wake on the faces). The fall to B5F keeps that task, and nothing
  turned it on again on B5F's water. Black 2's own waterfall turns it off at its start and on at its end.
- Platinum draws no wake at all (gen 4: dist_world_surf_mount_renderer.c has only the mount). Ours keeps Black 2's on the
  land's water, as everywhere else in the game.
- Fix (dw_field.c PlatDW_Update): each frame while surfing, the wake on only on the land (DW_STATE_ACTIVE) outside a
  waterfall (no pose). This also turns it off on the ceiling after a battle there (Black 2's form change made a task with
  the wake on). Not seen on screen yet (it needs the new build and the B4F ceiling's fall).

### Row 34, the lake trio's rise on B5F
- Starts that reach the hints: Azelf dwb5w (705, 42, 33), a step right; Mesprit dwb5e (705, 17, 34), then up, right, up,
  up, right x5, down, down (to (23, 33)); Uxie a new start (705, 29, 18), a step down. Each region has its own way in on
  Platinum's B5F: Azelf's from the waterfall, Mesprit's from B4F's elevator to (21, 43), Uxie's from B3F's to (39, 9).
- Seen (release code): all three come up through the floor smoothly, no pop on the first frame (row34_b5f_azelf_rise_3x.png).
  Azelf sinks smoothly (row34_b5f_azelf_sink_3x.png). Mesprit's head (its top 6 rows) was still over the pit's edge when
  it was deleted: a pop at the end (row34_b5f_mesprit_sink_end_4x.png).
- Cause 1: the trio's codes (4629-4631) carry Pearl's float, wPosOffsetY 24 in their records (pearl_npc_sprites FLOAT_Y).
  Platinum's lake trio renderer sets (0, 24, 0) once at its start (ov5_021ECB34), but the B5F hint then sets its own
  sprite offset (MapObject_SetSpritePosOffset), which replaces it. Black 2 adds the record's offset on top, so ours rose
  24 units higher than Platinum's. With the float off (a RAM write) Mesprit sinks out smoothly
  (row34_b5f_mesprit_sink_end_nofloat_4x.png). Fix: the hint's actor gets model offset 0 (dw_world.c TrioHint).
- Cause 2: Black 2 draws these codes as walking Pokémon (field_rail_loader.c RailActorAnim_UpdateWalkOffset). That draw
  rebuilds the actor's offset every frame: x 2 units by the facing, z 2 north, y kept only over 1.5 units. Uxie's moves to
  its boulder and back (Platinum's sprite offset z) were lost: RAM showed its offset z at -2 all through the hover, so it
  hovered 2 tiles south of its boulder. Fix: those moves go in its place (TrioMoveZ), the y stays in the offset.
- Left as Black 2's: the walking draw's own 2-unit x/z shift for these codes.
- B1F's Mesprit and B6F's three (eff8c48668, the lead's go): the same codes floated 24 units over Platinum's, whose DW
  renderers for 264-267 set no float. Now their record's offset is 0 each frame (dw_world.c TrioRenderers, by code
  0x1215-0x1217). B6F's bob (Platinum's ov5_021EC9E8: the jump offset from a 16-step table, 0 to 8 units) was ours to fix
  too: the walking draw rewrote its values of 1.5 units or less (to 0, or 1.5 on its own step frames), so the "another
  writer" check failed and the bob stuck. Now the bob goes into the offset 2 units higher (always kept) and the record's
  offset is -2. Another writer is an offset over 1.5 units that isn't ours: the warp out once its boulder is in (Black 2's
  rise, 16 units a frame), which then starts from the trio's place (record offset 0), as Platinum's warp replaces the bob.
  Not filmed.

### Sizes and checks
- Overlay 377 ends at 0x21F58E0 (after eff8c48668): 256 B before overlay 146. The resident section +64 B (6eb195689e).
  decomp.py check: layout kept. version_check: ok (no digest moves: the decomp's C isn't in it).

### On screen after the next build (the checklist)
1. A cave surf facing south, Pearl and Platinum: Victory Road B1F (361), from (4, 28) surf to (4, 30)-(4, 31). The rider on
   the mount, no flipped copy; facing west as before.
2. A walker's reflection still shows in a room: the Great Marsh Area 1 (585), stand at (40, 58), river water south at
   (40, 59).
3. An overworld reflection: Route 208 (383), stand at (398, 721) (water south at (398, 722)); surfing at (403, 718) facing
   south as before.
4. The DW's B5F: dwb5w (705, 42, 33), a step right (Azelf's hint), right to (44, 33), surf: no copy facing down or left;
   the wake behind when moving.
5. The DW's waterfall: dwb4 (703, 46, 22), the ceiling's surf, the fall at x 47: no wake on the ceiling or in the fall, the
   wake on B5F's water after it.
6. B5F's hints, all three 24 units lower than the release: Uxie (705, 29, 18, a step down) goes 2 tiles north over its
   boulder (29, 22), hovers, comes back, sinks; Mesprit (dwb5e, up, right, up, up, right x5, down, down) sinks out with no
   pop; Azelf (dwb5w, a step right) as before.
7. B1F's Mesprit (the event at (15, 1, 23)) fades in 24 units lower than the release, and flies off.
8. B6F's trio on their boulders (puzzle flags by RAM: dwplay PUZZLE): the bob 0-8 units, never stuck; a boulder into its
   pit: the warp out from the trio's place.
- The new code is not on screen yet: the test starts reuse the release code. Rows 31 (reflection, wake) and 34 (Uxie's
  move, Mesprit's sink) need the next build.

## The softlock after B5F's waterfall climb (plat-dw5, 2026-11-12; decomp 23a3647cca, 64cede9e30)
Found on screen in release6: on B5F, surfing east into the waterfall at (47, 0, 42-45) climbs to B4F's ceiling (the climb
itself right), the walk west ends at (46, 10, 43), and then every key only turns the player: a softlock. Never seen
before: the earlier rows saw the climb, not the moves after it.

### The cause
The climb's end (dw_world.c Cascade_Callback, EventCmdCascade*_FinishCascading) left out two things every other way onto
the ceiling sets:
- **No current platform.** It called DwSystem_FindAndPrepareNewCurrentPlatform, Platinum's public
  DistWorld_FindAndPrepareNewCurrentFloatingPlatform, which looks for a platform of the *current* one's kind. The floor's
  change partway (DwSystem_ChangeFloor) had just cleared it, so the kind was none and nothing was found. Platinum calls the
  static FindAndPrepareNewCurrentFloatingPlatform with FLOATING_PLATFORM_KIND_INVALID there: any kind (ov9_02249960.c 8707,
  8410 going down). With no platform every tile reads DW_ATTR_INVALID, so every step collides and DwSystem_DecideMove
  gives the ceiling's bump (the walk on the spot) in every direction.
- **The face surf flag off.** sys->surfing is ours (Platinum's surf is the avatar's state, which the climb keeps). Only
  DwSurfTCB (A at the ceiling's water) and PlatDW_Init set it; on B5F's land it is FALSE. With the platform but not the
  flag, every water tile still bumps, and the dismount onto land can't start.
- Also: Platinum's finder persists the index (SetPersistedCurrentFloatingPlatformIndex); ours had saved "none" at the
  floor's change, so a game saved on the ceiling after the climb would come back with no platform.

RAM in release6 (sDW 0x021F58C0; DwSystem at +8: platform +0x12, state +0x14, surfing +0x15): on B5F before the climb,
platform none, state 1, surfing 0; right after it, in one run from B5F (45, 47): floor B4F, platform 2 of 2 (none), state 5
(ceiling), surfing 0, saved platform 2.

### The fix
- 23a3647cca: DwSystem_FindAndPreparePlatformAt (dw_core.c: FindAndPrepare with any kind, Platinum's KIND_INVALID) at the
  climb's and the fall's end; sys->surfing = TRUE on the ceiling, FALSE on B5F's water (Black 2's own surf there, as
  PlatDW_Init's rule); PlatDW_Update keeps the saved platform equal to the current one each frame (Platinum persists it at
  every change).
- 64cede9e30 (separate: the same finder, found offline): a moving platform's ride with the player ends on the platform of
  any kind at the tile, as EventCmdMovePlatform_EndMovement (KIND_INVALID, 6638). B2F's four islands are floor platforms
  covering the whole y 9 plane: the rides from an island down to the land ((34, 9, 36), (13, 9, 38)) kept the island's
  floor state on the land, where every way bumps (a softlock in the host test), and the rides up onto an island ((34, 1,
  33), (16, 1, 38)) left the land's state (Black 2's walking on the island). Rides land to land or island to island are as
  before. Not seen on screen.
- Checks: decomp.py build (ninja, layout kept); overlay 377 +32 B, ends 0x021F5900 (224 B before overlay 146; sDW now
  0x021F58E0); version_check ok; the harness's B4F routes (25, all the same). A host test (dw_core.c with the tables)
  gives the climb's end as it was: a bump all four ways; with the platform only, or the flag only: still bumps; with both:
  the ceiling's walks.
- On release6 with the fix's values written to RAM (test only: the ceiling's grid, platform 1, surfing 1) from the stuck
  state: the player surfs upside down on the ceiling, 2 tiles west, 3 up, 3 east, 4 down to (47, 10, 42), passing behind
  the hanging vines near z 46 (the 3D props nearer the camera); holding east there falls down the waterfall to B5F
  (47, 0, 42), walks west to (45, 0, 42), and Black 2's surf then goes north.

### On screen after the next build
1. From B5F (45, 0, 47) surfing: up to z 43, east: the climb, the walk west to (46, 10, 43); then each way moves on the
   ceiling's water (no bump), the mount upside down under the player, no wake.
2. On the ceiling: onto the land at (44-45, 10, 27-36) (the dismount), A at the water again (the face surf), back on.
3. Back to (47, 10, 42-45), east: the fall to B5F, the two steps west, Black 2's surf moves (the wake back).
4. A save on the ceiling after the climb, a reset: the game continues on the ceiling, surfing, and moves.
5. B2F (64cede9e30): from an island, the ride down at (34, 9, 36) to the land, the jump north, then the land walks; the
   ride up at (34, 1, 33) onto the island, then the island's walks and jumps.

### On screen on release7 (plat-dw5, 2026-11-12; decomp 64cede9e30, rom7 from final/'s states)
The lead saw rows 1, 3 and 4 pass (after the climb platform 1, state 5, surfing 1; every way moves; the fall with no black
frame; a save on the ceiling, a reset, Continue: the same). The rest, by dwplay (sDW 0x021F58E0):
- **Row 5, B2F's rides: FAIL, a softlock older than these fixes.** From (18, 1, 23) a step south onto (18, 1, 25): the
  platform comes, the jump south (3 tiles, to 28), the ride 8 south to (18, 1, 36), and at once the ride back north
  (36 is the other way's event tile), the jump to 25, and south again: 22 moves in 1,300 frames, the event never idle,
  the keys ignored (work/agents/plat-dw5/row5_b2f_ride_pingpong_2x.png). The cause: PlatDW_CheckStep also counts "a new
  tile, the action over" as a step (plat-dw-rom, for the jumps between platforms), so the tile a world event leaves the
  player on starts that tile's event. Platinum checks tile events only after the player's own steps (Field_ProcessStep,
  field_control.c 706); an event's movements (a ride's end, MapObject_SetX/Y/Z; LocalMapObj_SetAnimationCode) aren't
  steps. The elevators already set lastTile at their end for the same reason. The island rides loop the same way
  ((16, 1, 38) up ends on (13, 9, 38), the way down's tile), so 64cede9e30 can't be seen until this is fixed. **Fix to
  make** (not built): in PlatDW_Update, while an event runs (GSYS_GetEventRunningFlag), lastTile follows the player's
  tile, so a world event's end (a ride, the cascade, a script) is no step. The face jumps stay steps (they are actions,
  not events).
- **Row 7, B1F's Mesprit: PASS.** b1p_boot (15, 1, 14), PVAR_4055 3: west to (12, 1, 14), left onto the wall (11, 2, 13),
  left along it to (11, 2, 22), down off it to (12, 1, 23), east to (15, 1, 23): "Mesprit: Pyuh!", it fades in over the
  void up and left of the player, hovers, flies north and fades behind the vines; the field idle after
  (row7_b1f_mesprit_fadein_hover_flight_2x.png). Its height can't be compared with the release on one ROM; nothing
  overlaps.
- **Row 8, B6F's trio: not done.** b6_boot has the puzzle finished (PFLAG_09AD, puzzle flags 0x1dc0): the three boulders
  lie in their pits (actors 144-146 at y -1: (12, 28), (40, 31), (28, 22)) and the trio are gone
  (row8_b6f_puzzle_done_start_2x.png). The trio on their boulders and the push into the last pit need a start before the
  puzzle's end (two boulders in, the third on B6F) and the time to push it there.
- **Row 2 (the ceiling's dismount, the face surf again): not done** (time; no release7 ceiling state here).

### The rides' loop fixed, and the final build (the lead, 2026-11-12)
- Decomp 9ea478209b (dw_field.c PlatDW_Update): while an event runs (Field_IsEventRunning), lastTile follows the player's
  tile, so the tile a ride, the waterfalls or a script leave him on is no step. (Black 2 sets the grid place at a move's
  start, and a ride ends many frames before its event does, so the step check never sees an event's end tile as new.)
  Overlay 377 +64 B (sDW now 0x021F5920; 160 B left before overlay 146); ninja, the layout check and version_check ok.
- The final build (release8, main fec3170, decomp 9ea478209b; work/agents/plat-rel/plat11.sh), on screen: B2F's ride from
  (18, 1, 25) south stops at (18, 1, 36) and the field is idle; a step off south, a step back onto (18, 1, 36) rides north
  to (18, 1, 25) and stops; a step west and back onto (18, 1, 25) rides south again. The climb from B5F (45, 0, 43) to
  B4F's ceiling (platform 1, state 5, surfing 1), the moves there, and east at (47, 10, 43) the fall to B5F (403 frames,
  none black or white) and Black 2's surf after it. On release7 (the same ceiling code): a save on the ceiling after the
  climb, Continue: the same values, every way moves.
- Still not seen on screen: row 8 (B6F's trio on their boulders), row 2 (the ceiling's dismount and its face surf again),
  the island rides (64cede9e30's own rows: (34, 9, 36), (13, 9, 38), (34, 1, 33), (16, 1, 38)).

## Rows 2, 5 and 8 on screen (the lead, 2026-11-13; decomp 76db7ad82b)
The three rows not yet seen (the user: "Yes, check them"), first on release8 (decomp 9ea478209b), then on release9 with two
fixes (work/agents/plat-rel/plat12.sh; the rechecks work/agents/plat-final/recheck9.sh; frames kept in
work/agents/plat-final/evidence_r8 and evidence_r9). sDW is now 0x021F5940.

### Row 2, B4F's ceiling: the dismount and the face surf; a pop at each surf form change, fixed
- From the climb (B5F (45, 0, 43) east), the ceiling's water south (screen down is z-, screen up z+, 16 frames a tile):
  at z 37 to 36 the hop onto the land (surfing 0), the walk on to z 30; back to z 36, A against the water: "Dialga used
  Surf!", the hop on (surfing 1), the water's moves. Every way moves; nothing sticks.
- **Found on release8:** the rider drawn a whole height off the ceiling for one game frame (two DS frames at 30 a second)
  three times: 3 frames into the hop off, at the first step after it, and in the hop on. The actor's offsets were right in
  those frames (the hop's arc 3 to 6 to 0, the outer offset 34.92 throughout). The cause: Black 2 places a person's
  billboard from the actor's offsets in the actors' update (FldActSys_Update), before the gimmicks; the surf's form changes
  (Dismount_Callback's FieldPlayer_FinishFormChange and ChangeToNormalForm: ExStateChangeFunc_NONE, and the surf's own
  StepFormChange) zero the outer offset, where DwField_SpritePivot keeps the turned picture's place, so that frame's
  billboard was placed without the pivot: on the ceiling a whole height under the feet.
- **Fix (dw_field.c):** ApplyRotation and MountTCB place the player's billboard again (Black 2's func_ov036_0218ee08, the
  actor's place with all its offsets) right after they set the pivot, so the frame's billboard always has it. Overlay 377
  unchanged in size (alignment).
- **On release9:** the hop off (110 frames, every frame), the hop on (458 frames, the cut-in's 86 without the player) and
  the water's moves: no pop (work/agents/plat-final/tools/popfind.py: the beret's height frame by frame; the same check
  finds release8's three). The climb, B2F's west wall: as before. A press of A right after walking into the water does
  nothing until the bump's walk on the spot ends (as Black 2's own checks), then works.

### Row 5, B2F's island rides: the island snapped back over the player, fixed
- (16, 1, 38) rides up: platform 16 comes down 8 tiles, the player jumps 3 west onto it at (13, 1, 38), it rises 8 with
  him to (13, 9, 38) (platform 2, state 2: 64cede9e30's finder); no loop (9ea478209b). (13, 9, 38) rides down to (16, 1,
  38) (platform 5, state 1), then the land's walks.
- **Found on release8:** as the rise began the island jumped back to its own place in one frame, over the player, who was
  hidden under it for the rest of the ride and while walking on the island, and the ride left it 8 tiles above its place
  (the next ride starting from there). The cause: MOVE_PLATFORM's shake set the platform's y offset to the shake alone
  (off->y = vib, then 0), where Platinum's is initialPlatformY + vibrationYDelta (EventCmdMovePlatform_Vibrate): harmless
  for the land rides (they move in z), wrong for the island rides' second leg, which starts 8 tiles off.
- **Fix (dw_world.c):** the run keeps the platform's offset when the command begins (DwEventRun.base, the unused delta
  renamed) and shakes about it. Overlay 377 +32 B (128 B left before overlay 146).
- **On release9:** the ride up with the player on the island the whole way and at the top; the ride down; the land ride
  (18, 1, 25) to (18, 1, 36) as before. Platinum also shakes the player's sprite with a platform he rides; ours doesn't
  (as before).

### Row 8, B6F's trio: passed on release8 (the same code in release9)
- A start on B5F at (30, 1, 34) with the puzzle flags 0xFC38 (the three boulders on B6F, the hints seen, the trio in B6F;
  dwplay PUZZLE before the ride), the elevator down: Mesprit (12, 26), Uxie (26, 22) and Azelf (40, 33) hover, each its
  drawn offset 2 to 10 units and back over 32 frames, never stuck. Uxie's boulder (30, 18) pushed south to (30, 22) and
  west into (29, 22): it drops in, "Uxie: Piih!", Uxie flies off north and is gone; Mesprit and Azelf still bob.
