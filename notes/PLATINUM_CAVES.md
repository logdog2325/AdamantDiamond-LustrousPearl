# Platinum's caves, the Great Marsh, Amity Square, Spear Pillar (step 4, the plat-caves piece)

Written 2026-11-07. Offline only: nothing here has been seen in a ROM yet. The checklist for the combined test is at the end.

## The map fixes on Platinum's rooms

### Shapes on translated nodes (`version.NODE_SHIFT`, Platinum only)
43 of Platinum's land models draw shapes on translated nodes (Pearl: 2, chunks 410 and 417). The DS adds the node's
translation to the shape's vertices; the fixes read the vertices without it, so they judged those shapes where they aren't
drawn (a gatehouse's whole room 136 units off, the Lost Tower's floors 224 units off).
- `pearl_model_fix`: `items(model, nodes=True)` adds each shape's translation (`node_shift`). `apply_shifts` keys a corner
  by where it is drawn, so corners of shapes on different nodes meet. `split`, `underfloor` and the people fix write back
  in each shape's own raw units.
- `sinnoh_rooms`: the camera boundary takes each shape where it is drawn. Before, the Lost Tower's camera box was 224
  units off to the east.
- The pictures and checks always draw shapes where the DS does (`pearl_mesh.shape_translations`): `pearl_rooms_view`
  (plat-rooms' change, kept), `room_look.py`, and `pearl_seams_check.load`. Only the fixes need the row: Pearl's and
  Diamond's chunks 410 and 417 keep their 1.0 fixes.
- Nodes that rotate or scale (the HQ hall 609, Eterna 3F 200) are still not applied (notes/PLATINUM_ROOMS.md).

### New layer rules (`version.GROUND_STAYS` and `version.SELF_PAIRS_STAY`, Platinum only)
Each one was found on a Platinum room or cave with `pearl_seams_check.py --holes` and checked again on the whole world.
- A piece never pairs with itself (plat-rooms' `SELF_PAIRS_STAY`, which I had too as SELF_STAY: one rule now, theirs).
  Platinum's gatehouse walls overlap themselves; each round pushed the wall on to 4.5 units forward.
- One texture drawn twice in one plane stays, walls as well as ground: the Lost Tower's stairwells.
- Two polygons on the same corners stay. They have the same depth at every pixel, so the one drawn first shows, as in
  Platinum. Veilstone Store 1F draws its walls' foot twice (d002 and lambert19); when one moved, the floor's edge went
  with it.
- Two planes that cross stay. Each shows where it is in front, as Platinum draws them.
- An overlap less than a unit wide along an edge stays (`EDGE_SLIVER`): the Global Terminal's trim band on its wall, and
  the caverns' floor patches over Platinum's `lm2` quads.
- A slope follows a moved piece (up to 25 degrees from it, `FOLLOW` 0.9) when it shares an edge with it, or when it is a
  small polygon (`FOLLOW_SMALL` 64 units^2) and the piece moved toward the camera. The Lost Tower's stair landings went
  up 3.5 over their shadow decals and parted from the ramps. One corner of a big polygon isn't enough: twisted, the
  polygon parts from the rest (chunk 55's platform bevel, Victory Road 2F's long wall). Nor is a small polygon's corner
  when the decal went back (a bridge's shadow on Route 215, chunks 69 and 70).
- `pearl_seams_check --holes`: a pixel at a chunk's edge that the fixed neighbours cover is no hole. Spear Pillar's dhole
  reaches 8 units into the next chunk.

### Holes (`pearl_seams_check.py --holes`)
Platinum's rooms (`--holes --rooms`, 426 chunks): **3,229.6 units^2 in 47 chunks before** (main at a696500, before this
piece and plat-rooms' self-pair rule) **and 297.0 in 17 now**. No chunk got worse. Mine, all at 0 now: the houses on
chunk 180, Sandgem's assistant 2F 188, the gatehouses 220 and 283, Veilstone Store 1F 248, the Lost Tower 285-288,
Oreburgh Mine B1F 313, Sendoff Spring 443, the caverns 520, 529 and 538, Spear Pillar's four states 354, 358, 658 and 662,
the Hall of Origin 555, the Underground 563-576, and the Contest Hall lobby 240. The Contest Hall lobby is Pearl's own
model, with the same 18 in Pearl 1.0 (notes/V1_0_1.md). Others' rooms are at 0 too: Eterna 2F 199, Store B1F 587, the HQ
hall 609, the Battle Factory 592 and Castle 594, and the Hearthome Gym rooms 229 and 230 on shifted nodes.
Left:
- Oreburgh Mine B2F 314: 2.5 (4.0 before). A line on a wall corner at (18, 14).
- The Global Terminal 1F 277: 3.0 (14.0 before). Two edges of Platinum's own `black` texture against the black clear
  colour: nothing changes on screen.
- The Battle Tower lobby 265: 42.2 (83.8). Step 8.
- The Distortion World 619-652: as before. Step 7.

The overworld (plat-world's chunks) with the same rules:
The overworld (`--holes --world`, 176 chunks): **525.6 units^2 in 24 chunks before, 262.0 in 13 now**. Chunk by chunk
(before -> now): 31 23.0 -> 0, 47 85.8 -> 3.8, 49 2.0 -> 0, 52 3.2 -> 0, 53 3.2 -> 0, 63 5.8 -> 6.8 (the one worse: a
cliff corner at (28, 22), and (29, 15)'s hole gone), 71 24.0 -> 8.0 (its grass on a translated node), 75 14.0 -> 0, 90 3.2
-> 0, 105 39.0 -> 7.2, 114 14.2 -> 0, 133 8.0 -> 0, 152 5.0 -> 0, 157 55.8 -> 0, 169 3.2 -> 0. The same as before: 13 8.0,
20 8.0, 27 56.0, 28 4.0, 29 16.0, 34 40.0, 83 8.0, 89 8.2, 170 88.0. Chunks whose fixed model changes at all: 53 of the 177 (pieces the layers fix moves, before -> now): 8 (78 -> 78), 22 (11 -> 11), 26 (23 -> 23), 28 (85 -> 80), 30 (24 -> 24), 31 (377 -> 377), 35 (130 -> 130), 43 (90 -> 89), 46 (19 -> 17), 47 (60 -> 59), 49 (169 -> 160), 50 (239 -> 236), 51 (177 -> 174), 52 (155 -> 155), 53 (98 -> 98), 54 (7 -> 5), 55 (55 -> 54), 56 (180 -> 180), 63 (87 -> 86), 64 (76 -> 76), 65 (196 -> 196), 69 (279 -> 279), 70 (216 -> 216), 71 (327 -> 313), 73 (249 -> 247), 75 (322 -> 321), 80 (115 -> 115), 87 (284 -> 284), 88 (376 -> 376), 89 (192 -> 190), 90 (294 -> 276), 91 (302 -> 302), 96 (6 -> 6), 99 (2 -> 0), 105 (193 -> 193), 111 (80 -> 80), 112 (51 -> 51), 114 (74 -> 68), 118 (34 -> 24), 133 (62 -> 60), 139 (18 -> 18), 140 (52 -> 52), 141 (46 -> 46), 152 (291 -> 290), 154 (156 -> 156), 157 (140 -> 140), 163 (45 -> 45), 164 (54 -> 54), 165 (88 -> 88), 168 (9 -> 8), 169 (24 -> 22), 171 (56 -> 56), 172 (18 -> 18). In 24 of them the same number of pieces move, a few corners differently (slopes that follow, slivers left alone). Pearl's and Diamond's: none.

Pearl and Diamond: every rule is behind a Platinum row; `version_check.py` passes.

**Later (1.0.1, v101-seams, all three versions):** the decal rule's guard now covers every piece and the sliver rule holds for
a tree against anything else (`version.SEAM_GUARDS`). Chunk 63's corner and the Contest Hall lobby's back-wall seams are
gone; the holes check also sees from the build's own camera now (`--holes --views`). Notes/MAP_LOOK.md "1.0.1: the seams
seen from the side".

## Spear Pillar's four maps
All four convert as rooms from Platinum's own land files: Pearl's slots 352-355 and 356-359, and the new 656-659 and
660-663. Holes 0. Renders: work/agents/plat-caves/shots/spear_*.png. Pearl's and Diamond's Spear Pillar are unchanged:
`version_check` digests their chunks.

| State | Zone (Black 2) | Matrix | What it is |
|---|---|---|---|
| Spear Pillar | MOUNT_CORONET_SPEAR_PILLAR (330) | 22 | the story's pillar (Cyrus, Mars, Jupiter, the tag battle with Barry, Giratina's arrival) |
| Distorted | MOUNT_CORONET_UNUSED_2 (265) | 23 | after Giratina: the rift is open, Cynthia waits to go into the Distortion World |
| Dialga | SPEAR_PILLAR_DIALGA (710) | 297 (Platinum's 280) | after the Distortion World, with the Adamant Orb: Dialga's rift |
| Palkia | SPEAR_PILLAR_PALKIA (711) | 298 (Platinum's 281) | the same with the Lustrous Orb: Palkia's rift |

What switches them is Mount Coronet 6F's map script, in its OnTransition and OnLoad. All four warps share the tile (7, 5),
and the script moves all but one away (`SetWarpEventPos`):
- FLAG_SPEAR_PILLAR_IS_DISTORTED set: warp 2, the distorted pillar. Spear Pillar's scene sets the flag when Giratina
  comes, and Sendoff Spring's script clears it.
- Else, with VAR_EXITED_DISTORTION_WORLD_STATE >= 2 and FLAG_UNLOCKED_DIALGA_PALKIA_SPEAR_PILLAR set: warp 3 (Dialga)
  when the player has the Adamant Orb (in the Bag or held), Dialga isn't caught and VAR_SPEAR_PILLAR_DIALGA_STATE is 0.
  Then warp 4 (Palkia) the same way with the Lustrous Orb.
- Otherwise warp 1, the normal pillar.

The Distortion World's entrance (step 7, not built): the distorted pillar's Cynthia ("Are you ready?", and the same after
her opening scene) runs `DoDWWarp`, `SetPartyGiratinaForm` and `Warp MAP_DISTORTION_WORLD_1F, 55, 40`. The generated script
has `pl_Warp 699, 55, 40` with the first two stubbed. The Distortion World's way back is its 1F warp 0 at (31, 53) to Mount
Coronet 6F's warp 2.

## Amity Square
- **Who may walk with you** (Platinum's own list, from its script): Pikachu, Clefairy, Psyduck, Pachirisu, Drifloon,
  Buneary, Happiny, and the nine Sinnoh starters and their evolutions. Jigglypuff, Torchic, Skitty and Shroomish come
  with the National Pokédex.
- **The starters' walkers:** Platinum's own art, pixel for pixel (mmodel 383-391), 16 frames made into Black 2's 12 as
  the Amity Pokémon are. They use codes 98, 104, 130, 131, 196, 299, 305, 313 and 316. Nothing names those codes:
  no kept Black 2 zone, script, table or C (work/agents/plat-caves/tools/free_codes.py). Rows 220-228 of
  data/platinum/sprite_map.json. `pearl_amity_sprites.walkers()` gives them to the following Pokémon too
  (patches/followers.py). Buneary and Happiny keep Pearl's art until step 6 brings Platinum's.
  Picture: work/agents/plat-caves/shots/amity_walkers_platinum.png.
- **Finds:** Platinum's own Accessory table, six pools of ten by the walking Pokémon (the starters have three pools of
  their own). It is the dump's table at ROM 0xEFF84, and pearl_story checks it against pokeplatinum's source. It runs in
  the script: Pearl's compiled table in resident/contest.c stays as it is, so the resident code is the same in every
  version.
- **The gift man** (Platinum's, at (20, 13)): a daily option of 16, nine Berries and seven Accessories, as Platinum.
- **The huts** (27 places you step in and come out somewhere else): Platinum's script, as generated. Platinum's 0x32D,
  0x338, 0x32E and 0x339 keep people drawn while its map reloads. Black 2 keeps Amity Square's 2 x 2 chunks loaded whole,
  so they are comments. The hut's sound (SEQ_SE_DP_GYURU) has no Black 2 sound yet: step 6.
- **People and items:** 16 objects (Pearl 25), from the events piece. The ground is Platinum's 4 chunks. Renders in
  summer and winter: work/agents/plat-caves/shots/amity_grid_*.png.

## The Great Marsh
- Platinum's own daily Pokémon: `encdata_ex` members 9 and 10 are read from Platinum's dump (patches/wild.py). Pearl's
  rule picks them: `(daily >> 5 * area) & 31`, the same in both games' code. Each area's own wild table is Platinum's.
- The Safari: as Pearl's build (30 Safari Balls as items, normal battles). Platinum's entrance gives the Matchup Checker
  for 5 Pokémon caught in one game. `GetCurrentSafariGameCaughtNum` now counts the party and the boxes against the count
  kept at the start (PVAR_SAFARI_START_COUNT, a new Platinum work, 0x4161).
- The trams and the binoculars stay closed, as in Pearl's build. Platinum's binoculars also show a Pokémon of today's
  Marsh. Not built.
- Renders: work/agents/plat-caves/shots/marsh_*.png.

## Stark Mountain and the lake caverns
- Stark Mountain's outside (overworld chunk 172), rooms 1-3 and the caverns 520, 529 and 538 convert from Platinum's own
  land files. Holes 0. Renders: shots/stark_*.png, cavern_verity.png.
- **Winter on Stark Mountain's outside:** its cliff tops get speckled snow and its path turns pink beside the lava. That
  is the winter recolour of Platinum's texture set 17, the same as the Survival Area's rocks (sinnoh_reskin). In winter
  everything gets snow (the user's rule), so it's left as it is: see "For the user".

## For the combined ROM
Platinum's flags and works below are given as Black 2's numbers (src/include/platinum/pearl.h).
1. **Amity Square** (Black 2 zone 367). Start in Hearthome's west gatehouse (zone 162), with a Piplup, Grotle or
   Infernape first in the party (and a Pikachu after it). Walk north onto (12, 46) and say yes. Look at:
   - the starter behind the player with Platinum's sprite, all four ways, no frame of another Pokémon, feet on the ground;
   - after 200 steps, talk to it: an Accessory from Platinum's starter pools (the Fashion Case gets it);
   - the gift man at (20, 13): a Berry or an Accessory, once a day;
   - a hut: step onto (17, 17). After the fade the player and the follower stand at another hut, and the people and
     the Drifloon are still drawn at their own heights. No sound plays there yet (step 6);
   - the plateaus and ponds for seams, summer and winter (DS clock December).
   Also the following Pokémon (Rowan's fifth question on) with a starter: Platinum's sprite outside Amity Square too.
2. **Great Marsh** (Pastoria's entrance 1F, zone 176). Pay and catch five Pokémon in one game, then walk out: the cowgirl
   gives the Matchup Checker (PFLAG_00A3 = flag 210 clear before). Catch four: nothing. The daily Pokémon on grass slots 6-7
   come from Platinum's list (another day, another one). The trams and binoculars show their closed lines.
3. **Spear Pillar** (Mount Coronet 6F, zone 323, the north stairs at (7, 5)):
   - flag 386 (FLAG_SPEAR_PILLAR_IS_DISTORTED) clear, work 0x4143 (VAR_EXITED_DISTORTION_WORLD_STATE) 0: the normal
     pillar (zone 330);
   - flag 386 set: the distorted pillar (zone 265), its two rifts north of the platform;
   - flag 386 clear, work 0x4143 = 2, flag 413 (FLAG_UNLOCKED_DIALGA_PALKIA_SPEAR_PILLAR) set, the Adamant Orb in the Bag,
     work 0x415A = 0: Dialga's (zone 710, the blue rift); with the Lustrous Orb and work 0x415B = 0: Palkia's (zone 711, the
     pink rift).
   In each, walk the platform from the stairs to the north end: no seams, the pillars on the ground, the camera inside
   the map.
4. **The rooms the fixes changed:** Eterna's Route 206 gatehouse (zone 122) and the Cycling Road's (452), the north walls'
   tops; the Lost Tower 2F-5F (459, 460, 462, 466), the stairwells, walking down; Veilstone Store 1F (186), the floor's
   east edge; the Global Terminal 1F (42); the caverns (430, 433, 438), round the raised floor patches; Victory Road 2F
   (360); Oreburgh Mine B2F (270); the Contest Hall lobby (171), the north wall's top. Look for black lines and gaps.
   In the Lost Tower and the gatehouses, check that the camera stops at the room's edges (their camera box was off
   before).
5. **Stark Mountain** (outside, zone 230; rooms 377, 379, 380): the lava pools' edges, and the outside in winter (see "For
   the user").
6. **Hearthome Gym** (plat-gyms' rooms 128 and 129): the floors on translated nodes, drawn whole.

## For the user
- Stark Mountain's outside in winter: snow next to the lava pools (shots/stark_ext_14_12.png). It could stay out of
  winter (a row in sinnoh_reskin's areas) if the user wants.
