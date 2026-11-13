# Why Sinnoh's maps look rough, and the fixes (2026-10-19)

**Status (2026-10-19, decided; DECISIONS.md):** the normal build now does this by default, in `patches/sinnoh_reskin.py`
(no extra patch: the usual patch list, `sinnoh_reskin` after `sinnoh_world`):
- **Spring and summer: Pearl's own textures and colours.** Autumn and winter: Pearl's own art with its seasonal
  textures (grass, trees, tall grass, paths, lawns, flowers, ...) recoloured to Black 2's colours for the season
  (`transfer`, with the `c0`, `refs`, edge, shadow and flower handling below); never Black 2's textures. Rock, water
  and town textures stay Pearl's all year. The snowy north (Routes 216-217, Acuity, Snowpoint) is winter all year.
- **All the other fixes on**: zone fog removed, outdoor light tables, lamps, material colours (sections 2c-2f).
- **The camera: Black 2's camera tilted to Pearl's 59 degrees, the default since 2026-10-26** (the user's choice from the three-way comparison, work/agents/camera/shots/3col_*.png; Pearl's own camera: `MAPLOOK_FIXES=default,camera`; section 1d).
So the problems of sections 1a-1c and 3 (re-skin bugs) are gone in spring and summer because no texture is changed
there, and fixed in autumn and winter. Details of the build: "What the build does now" below.

The user played Chapter 2 and said the maps "look a little bit rough still": **(1) jagged or blocky edges** (paths,
cliffs, ledges, shorelines, around buildings), **(2) washed-out colours** (pale, minty, flat; trees like dark teal
blobs, where Pearl has richer greens), **(3) grainy or wrong textures**. Evidence: the lead's two DeSmuME shots of
Route 202 (`work/play_ch2b/after_tr1.png`, `r202a.png`, since moved to the Trash), Black 2's code (pokebw2), Pearl's
code (pokediamond, pokeplatinum for gaps), the user's Pearl dump and the built ROM's files (`work/rom_lead/files`),
offline renders. No emulator was used.

**The short answer: almost all of it comes from the re-skin (`patches/sinnoh_reskin.py`) and from Black 2 settings
the Sinnoh zones and areas inherited from the Unova zones they replace, not from Pearl's models.** At midday Black 2's
light saturates to white on Pearl's materials, so the screen shows the texture colours exactly: the ground in the
Route 202 shot is (16,27,21), (16,26,21), (17,27,22) in 5-bit colour, the very colours of Black 2's summer
`grass01ax`; the trees are (1,13,13) and (1,15,14), the re-skin's tree palette.

| Symptom | Main causes | Fix (`MAPLOOK_FIXES` names, `b2tools/maplook.py`) |
|---|---|---|
| 1 Jagged edges | bright Pearl-green 1-pixel lines left by a recolour bug; path/lawn/beach edges with sand and grass swapped; tree shadows removed; Black 2's camera magnifies Pearl's pixel art unevenly | `c0`, `transfer`, `refs`; `camera` (experimental) |
| 2 Washed out | Black 2's summer palette itself (a decision); trees recoloured onto 8 dark teal colours; zone fog inherited by Sandgem and others; other light tables in two areas; lamps nearly black | `transfer`, `refs`, `fog`, `light`, `lamps`, `material`; **a decision for the user** |
| 3 Grainy / wrong | bigger Black 2 textures cut into seams by Pearl's texture coordinates; see-through Black 2 textures on opaque Pearl floors (holes in Jubilife's plaza); flower tiles on Pearl-green squares | `mismatch`, `transfer`, `c0` |

Offline before/after: `python3 b2tools/maplook_check.py render 14` (Route 202), `render 0` (Twinleaf), `render 7`
(Sandgem), `render 15` (Jubilife plaza): four rows (spring, summer, autumn, winter) of Pearl's own textures | before
(the 2026-10-18 re-skin) | now (the build's default) in `work/maplook/chunkN_seasons.png` (the four are there now,
about 1.6 MB; trash them when done). `python3 b2tools/maplook_check.py specks` counts the colour-0 specks (before:
3,088-4,504 per area set over the four seasons; now 16, flower petals kept on purpose).

---

## 1. Jagged or blocky edges

### 1a. Bright Pearl-green lines along every edge (a recolour bug)
- **Cause**: `recolour.ramp_recolour(..., keep_first=True)` never recolours palette entry 0, assuming it is the
  transparent colour. On opaque textures (colour-0-transparent flag off) entry 0 is a visible colour, so those texels
  keep Pearl's colour while everything around them turns Black 2's.
- **Evidence**: per 32x32 tile, `nsandp` (path edge) keeps 94 texels of Pearl's grass green (10,31,18), `lgreenp`
  (lawn edge) 94, `nectgr` (tall grass) 30 of 256 in (2,28,15), `tshadow` (ground under trees) 48 in (8,30,16), the
  shore tiles `hamabe` 210 and `asahamabe` 210 in Pearl's sea blue, `beachp` 47. They sit exactly on the edge rows of
  the art, so they draw a bright staircase line along paths, lawns, tall grass and shores. In the `r202a` shot: 851
  pixels of (80,248,144) and 970 of (16,224,120), the brightest colours on screen. All area sets: 720-1126 such texels
  each (`maplook_check.py specks`).
- **Fix `c0`**: entry 0 is recoloured too unless every texture drawn with that palette has colour 0 transparent
  (`sinnoh_reskin.reskin_sets`). Now: none in spring and summer (Pearl's own sets), 8 per autumn or winter set (flower
  petals, kept on purpose, see 3c).

### 1b. Path, lawn and beach edges: sand and grass swapped
- **Cause**: the "derive" edge tiles (`nsandp`, `lgreenp`, `beachp`, ...) mix sand and grass in one palette. The ramp
  recolour ranks all 16 palette entries by brightness (used or not) against the Black 2 edge texture's colours, which
  also mix sand and grass. The ranks interleave: Pearl's sand became mint with sand-coloured dots, Pearl's lighter
  grass rim became a brown zigzag.
- **Evidence**: decoded `nsandp` (summer): Pearl's sand (31,28,19) (548 texels) -> (16,27,19) mint; the rim
  (23,30,19) -> (24,22,13) brown. On screen every path has a hard triple outline (mint dotted band, brown zigzag,
  bright green line from 1a) where Pearl blends sand softly into grass (render `chunk14`).
- **Fix `transfer`** (`recolour.transfer_recolour`): each Pearl colour is matched to an anchor of the same kind
  (`colour_class`: grass, sand/bark/cream, water, grey) and takes that anchor's Black 2 colour, made as much lighter or
  darker as the Pearl colour is (Black 2's hue, Pearl's shading). Anchors: each side's most used colour per kind, the
  ground's own grass (Pearl `ngrass` -> its Black 2 texture), and for an edge `Xp` the middle `X` it surrounds (nsand,
  lgreen, beach), so an edge meets the ground and its middle in exactly the colours drawn there.

### 1c. Tree shadows removed
- **Cause/evidence**: `tshadow` (Pearl's dark ground under every tree, (7,23,13)) was ramped onto `grass01ax`, whose
  9 colours are all light: the darkest became (16,26,21), plain ground. Pearl's trees stand in a dark ring that hides
  the scalloped bottom of the canopy; ours stand on bright mint, so every canopy bottom is a hard staircase.
- **Fix `transfer`**: the shadow keeps its 0.74 brightness ratio to the grass: (12,21,16) in summer.

### 1d. Black 2's camera magnifies Pearl's pixel art unevenly
- **Cause**: Pearl's field camera (pokeplatinum `src/overlay005/field_camera.c` default; Pearl the same): distance
  667, 59 degrees down, vertical half-angle 8.09 degrees: almost flat, 1 texel = 1 pixel everywhere. Black 2's camera
  0 (`a/0/5/9`, record 0, used by 61 of the 66 overworld zones): distance 237, 53.2 degrees, half-angle 20 degrees.
- **Evidence (geometry)**: Black 2 draws a texel 1.1 pixels wide at the player, 1.35 at the bottom of the screen, 0.76
  at the top (vertically 0.4-1.3); Pearl 0.9-1.1. Texel rows and columns are doubled irregularly near the bottom
  (blocky outlines) and dropped near the top (grainy, shimmering while walking). Black 2's own maps share this, but
  its art is soft, while Pearl's is outlined pixel art.
- **Fix `camera` (EXPERIMENTAL, off unless named)**: appends a camera record with Pearl's numbers (zoom 667, pitch
  0x29FE, half-angle 0x05C1, near 150, far 1024) and points the 66 overworld zones' default camera at it. Untested:
  the size of Black 2's sprites under it (about 9 % smaller), scripted camera moves, camera boundaries (see "Other").
- **In game (2026-10-25, the camera test build; sheets in work/agents/camera/shots)**: the rooms too now, behind the
  same switch (data only): each room zone gets its own Pearl zone's camera (maplook.PEARL_CAMERAS, Pearl's 16 field
  cameras; Pearl's orthographic room camera 4 becomes a perspective camera at Pearl's 1563.5 / 50.1 / 3.52 degrees:
  Black 2's field camera is always perspective, fieldmap.c creates it so, and its records have no projection field;
  a true orthographic camera would need C), and sinnoh_rooms sizes the room's camera boundary with it (Pearl's room
  camera sees 119 units below the player, Black 2's camera 0 85). Found and fixed on the way: with Pearl's near plane
  (150) Black 2's people lost their depth margin (fieldmap.c GetObjectProjectionMatrixOffset scales with 1/near:
  ~9 units at camera 0, 0.2 at near 150): legs cut in Jubilife, the player cut at the waist on the Cycling Road;
  near = 8 (d / 667)^2 (maplook.PEOPLE_NEAR) keeps camera 0's depth precision at the player and makes them whole.
  `patches/camera_switch.py` (test only) switches a built ROM between the two cameras in a quick non-clean build.
  Still broken with Pearl's camera: scripted pans (pearl_story.py CAM_ANGLE gives EvCameraMoveTo Black 2's camera
  numbers: Lake Verity's pan jumps 2.2x closer; with the zone's Pearl camera numbers it is smooth, tested as a demo);
  in rooms, people right in front of a counter lose the top of their cap (margin 1.4 units at the room camera's
  distance); rooms show more black beyond their west/east/north edges (wider view, as in Pearl).
- **Third camera `tilt`** (user 2026-10-25, after the first sheets: Black 2's camera preferred, "bigger people, more
  3D"; `MAPLOOK_FIXES=default,tilt`, also a camera_switch mode): Black 2's camera 0 exactly (237, half-angle 20, near
  1, far 1024) with Pearl's pitch: 59 degrees on the overworld, each room its own Pearl camera's (most rooms 50.1, a
  little flatter than camera 0's 53.2). People keep their size and are never cut (camera 0's near plane); the roof at
  the Cycling Road's north door shows the cap, the Veilstone planter trees the head; Lake Verity's pan snaps 1.4
  degrees as it starts (no zoom jump); the Windworks' wide black wall tops stay (they come from the distance, not the
  pitch). Clean build and camera_switch give identical headers. Sheets: work/agents/camera/shots/3col_*.png.

### Checked and not a cause
- Edge marking (outlines between different polygon IDs): on in both games; Pearl's overworld map polygons are ID 0
  like Black 2's (a few bridges and the Cycling Road use 9-20) and Black 2's edge table 0 draws those in (4,4,4) or
  (8,8,8), Pearl in (4,4,4). Anti-aliasing: on in both (`FieldG3D_InitCallback`, Platinum `Easy3D_Init`). Materials'
  polygon settings (light 0, fog bit, alpha) are the same in both games' map models.
- 1-pixel cracks (HoennB2 lesson 14): none in the two shots. Black 2 clears the screen to the sky colour (16,24,30) by
  day, so a crack would show as light-blue dots, most likely at chunk borders and on water.

## 2. Washed-out colours, teal blobs

### 2a. Black 2's summer palette (a decision, not a bug)
- Black 2's summer ground is a pale blue-green: `grass01ax` (16-18, 26-30, 21-23); its summer trees are teal. Pearl's
  ground is (10,31,18), its trees olive with brown trunks. Spring in Black 2 is yellow-green (19-24, 27-31, 15-16),
  autumn yellow and orange, winter pale. The re-skin follows the 2026-10-18 decision "Pearl's map shapes and buildings,
  re-skinned with Black 2's textures", so the user saw Black 2's summer.
- **No code change makes summer Pearl-green while keeping that decision.** See "Decisions for the user".

### 2b. Trees: recoloured onto 8 dark colours
- **Cause/evidence**: every Pearl tree atlas (`tree01`, `tree2_01`, `conttree_t/_b`, ...) was ramped onto the colours
  of `ki03bx` alone: 8 dark teals, (1,12,12) to (3,18,17). Pearl's trees span (6,6,4) outlines to (26,22,10) highlights,
  with brown trunks; squeezed into that narrow dark ramp they lose highlights, trunks and outline: flat dark blobs.
  Black 2 draws its own trees from `ki03bx` plus `ki03dx` (light tops) and `ki03ax` (trunks, browns).
- **Fix `refs` + `transfer`**: all of an entry's listed Black 2 textures count (the main one first, the others for
  kinds it lacks; translucent shadow decals like `ki02c` and the ground under tall grass left out), all trees of an
  area share one set of anchors, and the transfer keeps Pearl's shading: trees get Black 2's teal (spring/summer),
  orange (autumn) or icy (winter) colour with Pearl's highlights, trunks and outlines.

### 2c. Haze: zone fog inherited from Unova zone ids
- **Cause**: Black 2 fogs a zone in clear weather if its id is in the zone fog table (`a/0/8/0` file 29;
  `GetZoneFogIndex`, src/system/zonedata.c; `weather_sunny.c` turns it on). The Sinnoh zones kept the entries of the
  Unova zones whose ids they took: Sandgem (458, fog 27), Solaceon (233) and Veilstone (120, fog 24), Valor Lakefront
  (461, 27), Route 224 (108, 13), Route 231 (504, 17), and 76 room/cave zones.
- **Evidence**: fog 27 = offset 0x7F3F, shift 7, Black 2's default linear fog table. With camera 0 (near 1, far
  1024, Z buffer) that offset is about 144 units from the eye; the ground on screen is 198-347 units away, which gives
  fog densities 44-64 of 127: **35-50 % of every pixel in Sandgem is blended toward the fog colour, the light table's
  sky colour (16,24,30) by day**, a pale blue-mint haze. Pearl has no zone fog.
- **Fix `fog`**: removes the fog-table entries of every Sinnoh zone (82 of 102 entries).

### 2d. Light tables inherited by two areas
- **Cause**: `sinnoh_world` writes only the pack, texture set and exterior byte of each area record; the light table
  (one per season), edge table and actor colours stay the original Black 2 area's: 140-143 for most, **148-151 for
  Hearthome and Route 208** (Pearl area 9, records 14-17, also edge marking off and actor colours 0), 144-147 for
  Routes 209-211E and 215, Solaceon, Celestic (area 10). Table 149's light 0 points upward from 18:00 (the ground gets
  no direct light: dark orange evenings) and is cyan at night; 144-147 differ from 140-143 only in lights 1-3.
- Tables 140-143 are Pearl's own: light 0's colours and directions and the material colours per time of day are
  Pearl's `data/area00light.txt` (outdoor) values (e.g. midday light (24,22,20), diffuse 16, ambient (10,12,12),
  specular 18, emission 14 against Pearl's (24,24,20), 16, (10,12,12), 18, 14). 140-142 are identical, 143 (winter)
  differs.
- **Fix `light`**: tables 140-143 by season, edge table 0, actor colours 1 on every overworld area record (8 records
  change).

### 2e. Material colours (time of day)
- **Cause**: Pearl's map models take diffuse/ambient/specular/emission from the area light, changing over the day
  (pokediamond `ov05_021DB5EC`, called by the land-data loader, clears material flags 0x40/0x80/0x200/0x400;
  pokeplatinum `AreaLight_UseGlobalModelAttributes`, land_data.c). In Black 2 every map material uses its own fixed
  colours (all flags set: diffuse 25, ambient 31, specular 0, emission 0; `field_g3d_map.c` never switches them).
- **Evidence**: at midday both saturate to white (no difference, matches the shot). Mornings, evenings and nights
  differ, e.g. at night ours is about (18,18,26)/31 brightness, Pearl's (15,15,22).
- **Fix `material`**: clears those four flags in the overworld chunk models and the Sinnoh building packs (same size,
  in place; unlit materials keep their own colour), so Black 2's tables 140-143 drive them exactly as Pearl's area
  light does (`FieldLight_FlushCore` sets the global material colours every time they change).

### 2f. Lamps and lit signs nearly black, windows bluish
- **Cause**: Pearl's light 3 is a constant white and its light 2 the windows' night glow (yellow-orange at night).
  Black 2's tables 140-143 have light 3 = (6,5,4) by day and light 2 = the sky colour. Materials lit only by light 3
  draw at about 19 %: on the map Jubilife's `c1_o02b` (landmark), Canalave's `c2_light_a`, Hearthome's `c5_light`; in
  the building models 37 materials (Pokémon Center `light_a`, the fountain, gym and shop lights). 51 building
  materials (house windows `h_mado`, `Light`) use light 2: bluish by day, purple at night instead of glowing.
- **Fix `lamps`**: light-3-only materials drawn unlit at 25/31 (Pearl shows them at about 80 % by day); building
  materials on light 2 moved to Black 2's light 1 (its own warm night glow: (17,12,5) at night, (16,7,0) at dusk).

## 3. Grainy, stretched or wrong textures

### 3a. Bigger Black 2 textures cut into seams
- **Cause**: a swapped texture keeps Pearl's texture coordinates, in texels. Pearl's restart every polygon (every 1-2
  tiles), which is invisible for Pearl's 16x16 tiles but not for a bigger Black 2 texture.
- **Evidence**: the ground (`ngrass` 16x16 -> `grass01ax` 64x64): the texel offset of the ground polygons mod 64 is 0,
  16, 32 or 48, all mixed (Route 202, Twinleaf, Sandgem). Black 2's striped grass is cut into 16-texel blocks that do
  not line up: the noisy patchwork in the shots. Same for 43 other swaps where Black 2's texture is bigger (cliffs
  `criffp`, the sea, puddles, Floaroma's flower ground, road edges and walls in Eterna, Hearthome and Pastoria, the
  Cycling Road), and `g1_treea/b` (16x32 shrubs -> 32x32 Black 2 shrub: half a shrub is shown).
- **Fix `mismatch`**: where the Black 2 texture is bigger in either direction, Pearl's own texture is kept and
  recoloured (transfer) with that Black 2 texture's colours. The ground keeps Black 2's colour without its stripes.

### 3b. See-through Black 2 textures on opaque Pearl floors
- **Evidence**: Jubilife's plaza floor `c1_g1` -> `out07_yuka03`, an A3I5 cut-out Black 2 draws over another floor:
  951 of 1024 texels see-through, so the plaza shows the clear colour, light-blue diamonds all over it (render
  `chunk15`). Also `puddle_b`, `h_kage`, the snow ring `fenter` (north) and five slope textures (8 texels each).
- **Fix `mismatch`**: these are recoloured Pearl textures too.

### 3c. Flowers on Pearl-green squares
- `nhana`, `shana` were kept as Pearl's art (the recolour would turn petals green): a bright Pearl-green square
  around every flower patch on the paler ground. **Fix `transfer`**: only their grass colours take the ground's
  colour; petals stay Pearl's.

### 3d. Also
- The colour-0 specks inside tall grass (1a) and the camera's minification at the top of the screen (1d).

---

## What the build does now

| File | What |
|---|---|
| `b2tools/patches/sinnoh_reskin.py` | `apply()`: the texture sets by `MAPLOOK_FIXES` (default `pearl_art`: Pearl's sets in spring/summer, recoloured Pearl art in autumn/winter, the north winter all year), then `maplook.apply_world_fixes` on the files `sinnoh_world` wrote; `reskin_sets(fixes)` builds the sets (no fixes = the 2026-10-18 style, byte for byte what the earlier builds had) |
| `b2tools/maplook.py` (new) | the fixes and `MAPLOOK_FIXES`: `fog`, `light`, `lamps`, `material`, the experimental `camera`; the texture fix names |
| `b2tools/recolour.py` | new functions only: `colour_counts`, `colour_class`, `anchors`, `anchor_pairs`, `transfer_recolour` |
| `b2tools/maplook_check.py` (new) | offline renders (Pearl / before / now, four seasons) and the colour-0 speck count |

Build: the usual patch list, unchanged (notes/RESUME.md):

    cd b2tools && PEARL_BUILD_DIR=... python3 build_rom.py --clean antipiracy sinnoh_world sinnoh_reskin sinnoh_rooms \
      sinnoh_events sinnoh_names sinnoh_encounters sinnoh_music scripts ...

`sinnoh_reskin` must come after `sinnoh_world` (as it does); it removes the fog of the room zones too (by zone id from
data/sinnoh_world.json), so its place relative to `sinnoh_rooms` does not matter. Running it again on the same files
(a build without --clean) changes nothing more.

`MAPLOOK_FIXES` (environment): unset = `pearl_art,fog,light,lamps,material`; `default,camera` = that plus Pearl's
camera (the test build); `none` = the 2026-10-18 re-skin with no fixes (comparisons); any list of names picks exactly
those (`c0,refs,transfer,mismatch` = the Black 2-texture style with its fixes, as first proposed).

The recolour (autumn, winter, the north): each Pearl colour pairs with an anchor of the same kind (grass, sand/bark,
water, grey) and takes the anchor's Black 2 colour at Pearl's relative brightness. Anchors: the ground's grass (Pearl
`ngrass`'s most used colour -> its Black 2 texture's), for an edge `Xp` the middle `X` it surrounds (Pearl's own colour
when the middle is not recoloured: beaches, gravel), then per kind the most used colour of Pearl's textures and of the
Black 2 texture they map to (the main one first: the trees' bodies, the tall grass's leaves), Pearl's main kind
pairing with Black 2's main kind when Black 2 has none of it (green leaves on Black 2's orange autumn trees). All
trees of an area share one set of anchors. Flowers: only their grass colours change.

Checked offline on copies of the built files: 354 textures recoloured in autumn (all areas), 497 kept; spring and
summer sets are exactly Pearl's; the north's four sets are identical; colour-0 specks 16 (petals); largest map chunk
unchanged (99,884 B); fog entries 102 -> 20; 8 area records changed (light, edge, actor colours); 2363 map and 888
building materials relit; camera record 45 only with `camera`. Not checked in game.

## How to test in game (one emulator at a time)

Black 2's season is the DS clock's month: January, May, September spring; February, June, October summer; March,
July, November autumn; April, August, December winter (`src/system/season.c`). Midday first, then evening and night.
Compare with the renders (`maplook_check.py render`) and with "before" shots of an older build.

1. **Route 202** (zone 321, Pearl chunk 14), the tall grass below the first ledge (the `r202a` spot), in **summer**:
   it should look like Pearl: olive trees with brown trunks and a dark shadow ring, sand paths fading softly into
   bright green grass, vivid tall grass, no bright green lines, no stripes in the ground. Then the same spot in
   **autumn** (yellow ground, brown trees with orange highlights, olive tall grass) and **winter** (pale ground, teal
   trees with Pearl's shading): edges still soft, no bright green specks, shadows under the trees.
2. **Route 202, north end** near the first trainer (the `after_tr1` spot): the L-shaped path and the flower patches
   (in autumn/winter the flowers sit on the season's grass, no green squares).
3. **Twinleaf** (zone 427, chunk 0): the cross-shaped sand path, the two flower beds, the pond; summer = Pearl.
4. **Sandgem** (zone 458, chunk 7): the beach in the south-east, in clear weather. No pale blue haze over the screen
   (the fog fix; it was there in every season), a cream beach with a soft edge.
5. **Jubilife plaza** (chunk 15): the diamond floor whole (no light-blue holes), the landmark (`c1_o02b`) lit, in
   every season (town textures stay Pearl's).
6. **Evening and night** (about 18:30 and 22:00) on Route 202 or Twinleaf: Pearl's orange evening and blue night
   (`material`), house windows glowing at night (`lamps`). Hearthome (Pearl area 9) is where the light tables changed
   most (no more dark-orange evenings), when the story gets there.
7. **North** (Route 216/217, Snowpoint), later in the story: winter in every month.
8. **Camera test build** (`MAPLOOK_FIXES=default,camera`, a separate PEARL_BUILD_DIR): Route 202 and Twinleaf for
   pixel sharpness, the player and NPC sprite size, a scripted camera move (Rowan's lab, Dawn's tour), walking to the
   edges of a town; screenshots for the user before it goes in.

## Decisions (taken 2026-10-19)

1. Summer colours: option C, adjusted by the user: Pearl's own colours and textures in spring and summer; Black 2's
   autumn and winter colours on Pearl's art; the north winter all year. Done (default).
2. All fixes on (colour-0 specks, path edges, tree shadows, zone fog, light tables, lamps and material colours,
   seams, Jubilife's plaza, flowers). Done (default; seams, plaza holes and specks cannot occur since no Black 2 texture
   is used).
3. Camera: Pearl's camera in a test build first (`MAPLOOK_FIXES=default,camera`), screenshots to the user before it
   goes in.

## Other things found on the way (not changed)
- Inherited camera settings: Routes 215 (camera 3), 216 (40) and 217-219 (25) use other Black 2 cameras than the rest
  (camera 0); 56 of the 66 overworld zones keep a Unova camera boundary (`cam_bound` 0, 13, 46, ... 443), which can
  stop the camera at Unova coordinates. `sinnoh_rooms` sets 0xFFFF (none) for rooms; `sinnoh_world` does not.
- Overworld area records keep Black 2's texture animation ids (SRT 0/36/37/38, pattern 0); `sinnoh_rooms` sets 0xFF.
  They target Black 2 material names, so probably harmless, but they load animation files for nothing.
- Rooms: Black 2's edge table 0 draws polygon IDs 48-63 in light/mid grey (24 and 16); Pearl's indoor table is black
  for ID 0 and (4,4,4) for the rest. Pearl's furniture uses IDs 48 and 56, so its outlines in rooms will be lighter
  than Pearl's. Rooms also take a Black 2 interior light table instead of Pearl's constant `area01light`.
  (Fixed 2026-10-20: "The world pass" below.)

## Flashing lines, flicker, stairs: HoennB2's fixes (its lead, 2026-10-19; for the world pass)
The user saw flashing lines and flashing trees (and other glitches) in PearlB2. HoennB2 fixed the same (files under
~/Documents/GitHub/HoennB2, read-only for us):
- **Flashing lines = 1-pixel cracks** along polygon edges inside a surface (T-junctions, even plain shared edges),
  worst at chunk borders, shown by melonDS/hardware (DeSmuME hides most). Fixes: re-split ground so no vertex lies on
  another triangle's edge (terrain/tjunction.py); an under-floor 4 units below the ground so a crack shows ground
  colour (world.py UNDERFLOOR, terrain/ground.py *_under); rooms: a floor twin under the floor; caves: seam_cover;
  water: a second coplanar sheet with different edges + a water floor 4 below, a ground strip under bank tops, one
  polygon ID for all translucent water (terrain/water.py, nsbmd_fix.py water_materials); cut ground out over water
  BEFORE re-splitting. Checker: water_seams_check.py. Budget: every layer adds triangles; the chunk buffer is
  110,600 B with no length check (world.py chunk_fit drops extra layers in a full cell).
- **Flicker = z-fighting** of surfaces under ~2 units apart (decals, windows on roofs, rugs, overlapping furniture,
  tree cards in front of cliffs). Rule: at least 2 units between layers (exterior_layers.py MIN_GAP 2.0;
  models_interior.py LAYER 2; tree cards moved forward until 2 clear). Checkers: exterior_check.py layer_pairs,
  rooms_check.py (f), caves_check (f). Coplanar copies with identical texels don't fight.
- Pearl's models were made for the DS, but Black 2 draws them with its own camera (closer, wider: 1d above) and
  depth range, so gaps Pearl never showed can appear: the world pass measures our chunks with these checkers' rules
  (port the checks to work/pearl geometry) and looks in melonDS.
- Hardware-only: reads outside ARM9 protection regions (watcher: `WATCH=1 python3 ...`), texture-pattern animations
  with missing frames (anim_tex_check.py), a scripted fade-out + same-tile map change + fade-in left the screen black on
  melonDS (use Black 2's own sequences).
- **Stairs**: the warp tile is the first tile of the flight, a type-2 warp on a SOLID tile with a 45-degree collision
  plane (slope codes 8/14/11/16 rise N/S/E/W, 0 at the approach edge), the model's foot on the approach edge, walls cut
  round the model; one warp per tile; the warp's dir steps an ARRIVING player (measured: 0 and 1 north, 2 south,
  3 west, 4 east). PearlB2 2026-10-19: one side-entered warp per Pearl stairs (sinnoh_events); 2026-10-20: the
  slope plane is on each flight (below, "The world pass").


## The world pass (2026-10-20): cracks, flicker, stairs, rooms' look, seasons, room cameras
User reports: "lots of visual bugs", flashing lines and flashing trees, ledges flickering in and out, stairs you don't
visibly go down, Oreburgh Gym's colours, rocks and metal fences turning beige in autumn/winter, Lake Verity not in
autumn, the black lower half of the screen at Oreburgh Gym's door and in Oreburgh Mine B2F.

**Tools** (new): `b2tools/pearl_mesh.py` (Pearl's map/building models as polygons and back: every display list
decoded and re-encoded, unchanged models round-trip to the same geometry, sizes -0.6 %), `b2tools/pearl_model_fix.py`
(the fixes), `b2tools/pearl_seams_check.py` (the measures: `python3 b2tools/pearl_seams_check.py [--fixed]
[--world|--rooms] [--json=OUT] [CHUNK ...]`), `b2tools/pearl_render.py` (offline DS-style renders with Pearl's
textures, vertex colours and lights; `--flicker 1` paints the pixels whose colour depends on draw order under
Black 2's depth precision, `--cracks PX` shrinks every polygon PX pixels as a stand-in for the DS's 1-pixel cracks;
`--fixed 1` = the model the build installs).

**Causes, measured over the 494 installed chunks (175 overworld, 319 rooms/caves)**
- Flicker: Black 2's camera 0 draws with the Z-buffer (a/0/5/9 record 0, swapMode 0) and near plane 1; the DS keeps
  z/w to 1/16384, so one depth step is ~1.7 units at the player and ~3.7 at the top of the screen (Pearl's camera:
  near 150, distance 667: ~0.1 unit). Pearl's models keep layers 0.5-0.9 apart: every tree's flat base 0.91 over its
  shadow ground (tshadow), neighbouring trees' cards in one plane overlapping 8 units, a row's end tree 0.02 in front
  of the continuous-row card, ledges (allpeak) 0.5 over the grass, shadow decals on cliffs, bridges and cave walls,
  building shadows (h_kage, 1.0 over the building's base) and furniture shades (0.5). 24,657 overlapping pairs
  closer than 2 units (trees 70 %), plus 151,960 units^2 of coplanar overlap with other texels across chunk borders
  (mostly trees drawn by both chunks).
- Cracks: Pearl's ground (and its opaque water) has nothing under it: 50,857 T-junctions; 94 % of the edges inside
  flat ground (4.85 of 5.15 million units, both sides, 2-unit samples) with nothing 1-16 units below, so a DS crack
  shows the clear colour (sky blue outdoors, black indoors).
- Oreburgh Gym's colours: the gym is unlit, lit by its baked vertex colours: its blue-grey cobbles are Pearl's own
  (an offline render with Pearl's textures matches the in-game shot; shots/oreburgh_gym_before_after_pearl.png).
  What differed in rooms: Black 2's interior light table 132 (light 2 = the sky colour, (17,29,31) by day: furniture
  and lit walls tinted cyan), the materials' own colours instead of Pearl's global ones, outline colours from Black 2's
  table 1 (IDs 48-63 in light greys) instead of Pearl's (black / (4,4,4)), and the black lower half (no camera
  boundary).
- Autumn rocks/fences: Pearl's `imped` atlas (fence, boulder, bush, pebbles) is marked seasonal (iwa01): its greys
  took Black 2's autumn/winter rock colours (beige).
- Lake Verity: outdoor maps built as rooms (Pearl's area data says "outdoor light": lakes, Eterna Forest, Floaroma
  Meadow, Battle Park, Mt. Coronet's sides, Great Marsh, Amity Square, Pal Park, Trophy Garden; Spear Pillar is
  exterior) had one non-seasonal area record with the interior light table.
- Black lower half: room zones had no camera boundary (cam_bound 0xFFFF) and Black 2's camera sees 85 units of floor
  below the player; Black 2's rooms keep their camera inside with a boundary rectangle (a/1/0/9).

**Fixes (all default; MAP_FIXES=none turns the model fixes off for comparisons)**
- `pearl_chunk.fix_model` (every chunk, in sinnoh_world and sinnoh_rooms), pearl_model_fix: (1) layers: overlapping
  same-facing pieces get 2.25 units apart along their normal, moved toward Black 2's camera (along its view
  direction, so they stay put on screen): tree cards by their own world column (single trees 2.25 or 4.5 forward,
  odd 32-unit columns in front, continuous-row cards stay: Pearl reuses filler chunks at many matrix cells, so the
  rule must not depend on the neighbours), decals lying wholly on a surface move off it, a big ground piece (4 tiles
  or more) never moves against a neighbour chunk's or a bigger one, bent decals move as one piece; (2) under-floor:
  a copy of the flat ground 4 units lower in its own material, cut back where the camera could see past a free edge
  (ray tests toward the camera's 9 corner/centre directions) and left out where another surface lies within 2.25 of
  it; (3) T-junction splits of the ground at every ground vertex inside an edge, the neighbours' too. Budget: a chunk
  stays under 100,000 B (CHUNK_BUDGET; the splits go first, then the under-floor; only chunk 123 gave its splits back).
- Building packs (pearl_model_fix.fix_pack, sinnoh_world and sinnoh_rooms): shadows, shades, steps and plates less
  than 2.25 over a model's base move up (toward the camera) off the ground it stands on.
- Stairs (lead's decision 2026-10-20, pokeplatinum sub_02057368): Pearl's 0x5e/0x5f tile is the foot (walkable now);
  the flight (x+1 / x-1, solid) gets Black 2's 45-degree plane (slope 11 rises east, 16 west), 0 at the foot's edge,
  up or down from Pearl's stair model over the flight (stair_u*/stair_d*) or the map's own steps (caves): 133 feet,
  65 up, 68 down. heights_rooms.json gives the flight the foot's height (the warp, on the flight: sinnoh_events).
- Rooms (sinnoh_rooms + maplook): Pearl's area data picks the light: indoor rooms and caves get a light table made of
  Pearl's constant area01light (a/0/6/0 entry 200: light 0 (23,23,25), light 2 (4,4,16), diffuse 16, ambient 14,
  specular 20, emission 16) and Pearl's indoor outlines (a/0/1/5 entry 9: ID group 0 black, the rest (4,4,4));
  outdoor ones Black 2's 140-143 (Pearl's day cycle) and Pearl's outdoor outlines (entry 8: all (4,4,4)); the room
  models' lit materials take the table's colours as Pearl's do ('material'); opaque polygon IDs 56-63 move to unused
  IDs of group 6 (Black 2 forces group 7's outline to (16,16,16)). The 10 outdoor room areas are seasonal: free
  seasonal area groups 90, 94, 102, 110, 114, 122, 130, 138, 142, 154 (work/world/room_season_groups.json), their
  sets from sinnoh_reskin.reskin_sets (the north, Pearl area 14, winter all year). Every room zone gets a camera
  boundary (52 distinct, appended to a/1/0/9): the target stops where the screen's bottom row reaches the map's
  south edge (geometry), x and north free.
- Seasons: `imped` recolours only its grass colours (sinnoh_reskin.GRASS_ONLY), like the flowers.

**Results** (pearl_seams_check, final code): T-junctions 50,857 -> 625; flat interior edges unbacked 94 % -> 8.6 %
(4.85 -> 0.92 million units; the rest along cut-back free edges and crowded spots); overlapping pairs under 2 units
24,657 -> 819 (left: shadow decals bent over bridge and cliff edges, the Cycling Road's ramps where they touch the
ground, a few cross-border pieces of reused filler chunks); border overlaps with other texels 151,960 -> 13,649
units^2 (coplanar ground drawn by both chunks: puddle edges, Route 206/207's lm13/lm14, tshadow/ngrass; not
moved). Largest chunk 96,020 B (was 69,228; limit 110,600). Build time: sinnoh_world + sinnoh_rooms ~10 min more.
Proofs: work/agents/visuals/shots/ (r202_flicker_before_after, r202_cracks_before_after, gym_cracks_before_after,
center_light_edges_before_after, oreburgh_gym_before_after_pearl, mine_b2f_before_after, stairs_up/down_ingame,
oreburgh_seasons_after, oreburgh_winter_ingame, lake_verity_seasons).

**For melonDS** (DeSmuME hides most of this): Route 202's first ledge row (row 823, x 168-197) and its tree rows:
ledges solid, tree bottoms and overlapping canopies steady, no light-blue lines across grass and paths while walking
(also on chunk borders x = 160/192, z = 800); Twinleaf/Sandgem's edge forests (filler chunk 173); Sandgem's beach and
the sea; Jubilife's plaza; Oreburgh's building shadows, boulders and fences; Oreburgh Gym (door view, floor lines);
Oreburgh Mine B2F (18, 29); stairs: Twinleaf house, Oreburgh's north house 1F<->2F; Lake Verity in autumn (DS clock
in March, July or November) and winter.


## Doors that open (2026-10-20)
User: "we need the doors to open like doors with a black space behind it" (HoennB2 did the same, its dark doorways).
- **Pearl** (pokediamond ov05_021F650C, 20 door models; pokeplatinum ov5_021D431C.c, map_prop_animation.c): a door
  is its own prop in front of its building, never part of the building's model. Walking into a door tile (0x69),
  Pearl finds the door prop by model id and plays its animations from arc/bm_anime.narc (list per model in
  arc/bm_anime_list.narc): entry 0 opens, 1 closes (hinged doors: door_op/door_cl, the plate turns 90 degrees inwards
  about its hinge in 8 frames; 2 and 3 are the same swing in 6 frames, for coming out); the Center's/Mart's glass
  slides (15 frames), the Gyms' double glass (10), the mansion's double door (9), the elevator door changes texture
  frames (BTP0). Behind every door Pearl's building has its own recess: dark in the houses, Gyms and most buildings,
  Pearl's grey (pcwall's (115,123,132)) in the Pokemon Centers and Marts.
- **Black 2** (pokebw2 field_buildmodel.c, event_entrance_effect.c, scrcmd_buildmodel.c): a door is a prop whose info
  record has a door type (1/2/3/13/14/15) and its animations (controller 2 = dynamic, 1 per command, BCA0/BTP0 files
  right after the record's header); going in or coming out, the game takes the first door prop within 32 (x) / 48 (z)
  units of the door tile out of the chunk (a handle) and plays animation 0, then 1, with the type's sounds (type 1:
  1669/1670, the house door; type 2: 1671, the automatic door). A door placed as its own prop is found the same way as
  one Black 2 adds to a building record (the search filters on the prop's type).
- **Done** (`b2tools/pearl_doors.py`, hooked in `pearl_buildings.build_pack`): every Pearl door model in an area's
  building pack (overworld and rooms) gets a Black 2 door record with Pearl's own going-in animations (entry 0/1;
  coming out uses the same swing, 8 frames instead of Pearl's 6); hinged doors type 1, sliding/elevator type 2. The
  door props stay where Pearl puts them, Pearl's recesses stay behind them: nothing new is drawn. The elevator door's
  texture frames go into the pack's texture set (`extra_textures`). Pearl's scripted door animations (pl_LoadDoorAnimation
  ..., already translated to Black 2's BM handle commands: Twinleaf, Sandgem, the GTS) should now play too (not
  tested in game: they found no door before).
- **Check** `python3 b2tools/pearl_doors.py check [--render --shots=DIR]`: 169 Pearl door warps in the installed zones,
  each with exactly one door prop in Black 2's search box (0 without, 0 with two); 0 other warps open a door (2
  accepted: the Center 2F's Union Room mat, whose door Pearl's desk scripts open); 176 door props (162 at a warp, the
  rest scripted or decoration); 19 door models with records (two animations each, nodes matching the model).
  --render (pearl_render, Black 2's camera): the open doorway's darkness and the dark gap round the CLOSED door.
- **Pearl's own dark gap**: Pearl's door plates are about 1.6 units narrower and 0.5 lower than their openings (Twinleaf:
  plate 20 x 29 in a 21.6 x 30.1 opening), so a thin dark line shows round every closed door, in Pearl too (offline,
  Pearl's camera head-on: 7-45 px per door); Black 2's closer, wider camera shows it a little bigger (15-76 px from two
  tiles south). Left as Pearl's art.
- **Sizes**: door records add 372-732 B per door model per pack: 57.6 KB over all packs (overworld +30.7 KB, largest
  overworld pack 169 KB with the signs, Twinleaf/Sandgem/Jubilife's pack 70; Black 2's own largest is 223 KB; room
  packs largest 188 KB, Black 2's 330 KB), the elevator's frames +3.5 KB of interior texture sets. Every pack is read
  whole into the field heap, so staying under Black 2's own largest keeps its heap budget. Reserves: a/2/2/6 35 %,
  a/2/2/5 under that (build_rom's list).
- **Tested** (DeSmuME, work/agents/doors/shots, Oreburgh): the middle house's door swings open into Pearl's dark
  recess and the player walks in; coming out the door opens, the player walks out, the door closes (house_*); the
  Center's and Mart's glass slides open going in and coming out (center_*, mart_*), onto Pearl's grey recess (see
  below); closed doors from three tiles south (*_closed_3_tiles_south). The Gym door was not filmed: in a fresh test
  start Pearl's counterpart stands in it (TEST_SET=PFLAG_019A hides him). `story_play.py REC<name>,<dir>,<n>,<k>`
  keeps a frame every k frames through a warp.
- **Open (the user's call)**: the Centers' and Marts' glass doors (p_door) open onto Pearl's own grey
  recess (pcwall (115,123,132): ~135/255 in the renders, not black); the Gyms' onto a half-dark one. Pearl looks like
  that; making them black would change Pearl's art (the recess faces to a dark texel, as HoennB2's dark quad).

## Buildings' colours: black signs and bands, bluish walls (2026-10-20)
User (melonDS, Sandgem's Center): "the pokemon centers shouldnt look like this have there colors match perals there
shouldnt be black lines on top and the pokeball shouldnt be black the gyms and pokemarts also look like this".
- **Black signs, bands, glass**: Pearl lights its signs, roof bands, the Centers' and Marts' glass doors, the Gym's
  windows and door with light 3 only (a constant white (31,31,31)). 'lamps' (2026-10-19) made them unlit with a grey
  diffuse, but their shapes carry normals, and the GX computes a vertex's colour at every NORMAL command as the
  material's EMISSION plus the enabled lights (GBATEK "DS 3D Polygon Light Parameters"; melonDS and our DeSmuME
  harness alike): emission 0, no light, black. 159 building materials in the overworld packs drew black (37 materials
  in Pearl's models; `python3 b2tools/building_look.py check FILES` counts them in a build). Black 2's own Center
  does it with emission: pc_01's sign material has emission (31,31,31). Now: unlit with the emission set (building
  models: their own ambient, Pearl's colour under its white light 3, full colour for the Center's sign; map lamps: 25).
- **Walls bluer than Pearl's**: Pearl draws its props with their own material colours (pokeplatinum map_prop.c,
  NNS_G3dRenderObjInit: no flags changed; pokediamond ov05_021DB5EC clears them for the land models only), as Black 2
  does its own buildings. 'material' had put the 729 lit building materials on the field light's colours (a south
  wall (24,25,24) by day instead of Pearl's warm (19,19,16)). Now 'material' is for the map models only.
- **Outlines**: Black 2's edge table 0 outlined building polygon ID groups 2-7 in (8,8,8)-(24,24,24); the overworld
  areas now take Pearl's outdoor outlines (all (4,4,4), as the outdoor rooms) and building IDs 56-63 move to group 6
  (Black 2 draws group 7 in (16,16,16) whatever the table says).
- Proofs (work/agents/doors/shots): look_before_center/mart/gym.png and look_after_*.png (DeSmuME, Oreburgh, by day),
  look_offline_pearl_before_now.png (b2tools/building_look.py render 4 5 8: Pearl's look under Pearl's light and
  camera / before / now, with the GX's lighting).


## People drawn into furniture (2026-10-20)
(The sinking of counters and tables below is off since 2026-11-01: see "The upright depth" at the end of this file.)
User (melonDS, twice): back from Lake Verity "your head is still in the kitchen counter like partially clipping into
it". Pearl's script puts the player at (2,6) facing up in MAP_TWINLEAF_RIVAL_HOUSE_1F (Black 2 zone 520, chunk 185);
the counter is row 5. HoennB2 had the same (its notes/INTERIORS.md "Indoor check"); ported here.
- **Cause.** Black 2 draws a person as a camera-facing quad that leans back from the feet with the camera (camera 0,
  the room templates' camera: at h units up it stands 1.307 h north) and draws it with the projection's m[3][2] +
  m[2][2] * 0x136 (fieldmap.c GetObjectProjectionMatrixOffset; 0x1ee in caves and outdoor rooms): with near 1 / far
  1024 a person passes the depth test against geometry up to 3.65 % nearer the camera (8.7 units at the player). The
  DS keeps z/w to 1/16384 (one step 1.7 units there), so on hardware and melonDS anything within a step of that can
  cover them; DeSmuME draws people over ~1 unit more (HoennB2 measured 0.959): why the opening's DeSmuME frame was
  clean. Pearl's counters are 16 high over the floor with their front on the tile edge, 8 units north of the feet:
  9.1 units in front of the head's plane, so the counter top cuts across the head. Pearl's own camera (far, near
  plane 150) never showed it. Same for Pearl's tables (13 high props, a tile edge), the Centers' Wi-Fi counters, the
  Contest Hall's reception, the Department Store's, Game Corner's, ... (every room with a block whose front reaches a
  walkable tile).
- **Checker** `b2tools/pearl_rooms_view.py` (HoennB2 rooms_view kinds m and n, for Pearl's rooms): every room zone as
  sinnoh_rooms builds it (each chunk through pearl_chunk.fix_model, the props from the room packs, Pearl's textures
  for the alpha test), Black 2's camera 0 (eye 189.73 up / 142.05 south of the player, the zone's camera boundary
  too: the opening's DeSmuME frame matched the unbounded camera exactly, so both are checked), the player (Lucas
  231, Dawn 240) on every walkable tile reachable from the warps facing north and south, Pearl's objects seen from
  the camera on them and with the player 6 rows north .. 3 south. `--model hw` (default: k 0.9635 less one depth
  step, melonDS/hardware), `exact`, `desmume` (0.959); `--fixed 0` = before the fix; `--render OUT ZONE X,Z DIR`
  draws the room from the game camera with its people (matches the opening's DeSmuME frame of zone 520).
- **Fix** (pearl_model_fix "people drawn into furniture", hooked in pearl_chunk.fix_model for room chunks and in
  fix_building for every prop; sinnoh_rooms moves the props that rest on a sunk block with it,
  pearl_chunk.people_props_moved): a block (room-model parts not taller than 30 units, in materials with no taller
  polygon (walls), joined by corners or boxes 2.25 apart; a prop model whole) that stands more than PEOPLE_MARGIN
  (5.5 units; 9.5 in caves and outdoor rooms) in front of a person's quad where it covers the sprite's silhouette
  sinks (its top toward its base) and pulls its south side back by equal amounts, 0.25 steps, the smallest that
  clears every person, at most 35 % / 45 % of its height / depth and 4 units each (counted from Pearl's own shape:
  the layers fix had raised the Contest counter's top 4.5); its top and front 4-unit bands move rigidly (decals and
  the layers' 2.25 gaps kept), the rest stretches linearly. Props: one amount per model from all its room
  placements (the same table looks the same everywhere). Left as Pearl's: pieces taller than 24 (shelves, fridges,
  TVs, plants: their front covers the top of the head of someone right in front, Black 2's own look), blocks that
  need more than the caps, people standing inside a piece (Pearl's collision lets them: see "left"). Runs last in
  fix_model (on the model as the cracks/flicker fixes leave it). PEOPLE_FIX=none turns it off.
- **What changed**: 64 room-model blocks in 57 chunks (Pearl's 16-high counters: 2.75 lower and 2.75 back, top
  14 -> 11.25 over a -2 floor; the Centers' counters 0.75, Wi-Fi counters 1.5-1.75, the Contest reception counters
  (raised 4.5 by the layers fix) back to 2 under Pearl's top and 3.4 behind its edge); 24 prop models (tables
  1.75-3.5, the sink 2.75, boxes 3.25-3.5, bins 2-2.5, the camera, gravestones; pearl_model_fix.people_props()
  lists them; 12 more (the Mart's shelves, sofas, the Center's flowers, ...) need more than the caps and are left).
- **Counts** (`python3 b2tools/pearl_rooms_view.py [--fixed 0] [--model desmume]`, all 376 room zones; findings =
  people/tiles): hw model buildings player 1221 -> 600, NPCs 206 -> 145 (sprite pixels over 30: 786 -> 250 and 88
  -> 56); DeSmuME model player 387 -> 343, NPCs 133 -> 83; caves and outdoor rooms unchanged (191 / 13, trees and
  rock walls: taller than 24). Logs: work/agents/furniture/logs/{before,after}_{hw,dsm}.txt.
- **Beds solid** (user's decision 2026-10-20: "Make those bed tiles solid so you can't walk into beds"): Pearl's
  collision leaves a bed's middle row and its sides walkable (bed_h01, Pearl's only bed model: 31 x 40 units, half
  a tile off the grid, 23 placements in 13 room chunks; Pearl marks 2 of the tiles it covers), so people stood in
  the beds. pearl_chunk.bed_tiles: every tile the bed's raised parts reach into by more than 2 units (the body's
  width) is solid in the converted collision (pearl_chunk.convert; sinnoh_events.Planner.tile, so scene_check and
  warp_check see it; the people fix and pearl_rooms_view too), except a tile with a warp, object (person, item),
  trigger or sign/inspect event of any zone using the chunk, or one whose wall would cut off a tile reachable from
  the zone's warps: 130 tiles made solid, 16 left walkable and listed (`python3 -c "import pearl_chunk;
  print(pearl_chunk.bed_tiles(182))"` in b2tools): chunk 182 (10 zones: Canalave's inn, Snowbound Lodge, ...):
  (8,6)/(8,7) hold the Lodge's rest-in-bed scripts (Pearl's player faces (8,7) from (8,6)), so (8,6)-(8,7) and
  (9,6)-(9,7) (its only way in) stay; chunk 202 (Oreburgh's north and northwest houses 3F): the people lying in the
  beds (4,11), (4,12), (13,11) and the tiles beside them (5,11), (14,11); chunk 500 (Galactic HQ 2F): its
  rest-in-bed scripts at (40,4)-(40,5), (44,4)-(44,5) and (9,4), (13,4)-(13,5) next to them. BED_FIX=none: Pearl's
  collision. Checks: pearl_rooms_view bed findings 153 -> 44 (all on those kept tiles; player 791 -> 682);
  scene_check --all and warp_check offline identical with and without (scene_check's 44 lines are older ones).
  In game (DeSmuME, full build, start in the player's house 2F): two steps left from (4,10) into the bed are refused,
  the player stays at (4,10) beside it (work/agents/furniture/shots/bed_2f_step_left_ingame.png; Pearl's collision
  had (3,10) walkable).
- **Left** (after, hw, buildings): beds (see above, the kept tiles); lifts and
  gym platforms 93 (the League's lift, Cynthia's room, Canalave/Sunyshore Gym platforms and switches); slivers of 10
  px or less 211 (mostly Dawn's hat touching the back wall of the first row facing south: Pearl's back walls stand 6
  units behind the row's edge, Black 2's 12); the League lobby's flat seats over the feet (44); a few tall shelves
  and wall panels behind NPCs.
- Proofs (offline, the hw model, 256x192): work/agents/furniture/shots/*_offline_before.png / *_offline_after.png
  (counter_2_6 = the report, center_1f_8_6, center_b1f_wifi_6_6, table_tv1f_17_12, contest_lobby_4_6). In game
  (DeSmuME, work/agents/furniture/rom/pearl.nds, TEST_START 520,2,6 and 525,8,6): counter_2_6_ingame.png (the
  player at (2,6) facing up after Mom's line: the whole head in front of the lowered counter) and
  center_8_6_ingame.png (Sandgem's Center: the player in front of the counter, the nurse behind it, the flowers
  still on it). RAM (NNS_G3dGlb camPos/camTarget): eye - target = (0, 185.73, 142.05) as modelled; at (2,6) the
  target is held at z 91 by the zone's camera boundary (at the Center it is the player's tile).

## Seasons: grass, leaves and snow (2026-10-20)
User: "can we make it so the color of the grass also changes with the seasons it looks kinda off when it doesnt",
"Trees change, grass doesn't" (first at Lake Verity, then "all grass"), and Black 2's autumn leaves and winter snow.
Done the way HoennB2's seasons2 did it (its notes/SEASONS.md "Snow, autumn leaves and the grass", commit bc573c8).
- **What the game really shows** (DeSmuME, a build with the same season code as the user's ROM, test start at Lake
  Verity, the DS date set): Lake Verity's and the overworld's sets switch as built; by day in autumn the ground is
  yellow, the trees orange, the tall grass olive (work/agents/seasons/shots/diag_lakefront_autumn_day.png). It reads
  as "grass doesn't change" in two cases: **winter**, where Black 2's grass colour is a pale grey-green close to
  summer's (Black 2 itself: HoennB2 measured the same; its winter look comes from snow patches and snowfall), and
  **night** (the user's melonDS clock is 22:40 on 22 November), where the ground goes grey and the tall grass stays
  green (diag_lakefront_autumn_night.png, diag_lakefront_spring_night.png). The user's save (Desktop, 10:04) has the
  options word 0x0201: made before Rowan's questions, so seasons are **off** for it (spring all year).
- **Grass that really stayed Pearl-green**: Pearl art kept all year that has grass in it: gravel fringes (blueglayp),
  mountain paths (ckado), Hearthome's bricks (c5_base_*), Celestic's plaza (c07_base_*), berry soil (plant2), the
  Great Marsh's mud, plants and rails (numa_*, dun11_rale_*), and the north's bushes (imped: no green anchor there).
  sinnoh_reskin now recolours their grass colours only (recolour.grass_recolour, recolour.is_grass: green 4 above red
  and blue), stone, brick, soil and water stay Pearl's. `python3 b2tools/season_grass_check.py [FILES]` lists every
  grass texture left in Pearl's colours per area set and season (13 overworld areas + 10 outdoor rooms; autumn and
  winter, the north in all four): the 2026-10-20 build had 110, now 0 (offline and in the build).
- **Snow patches and autumn leaves** (patches/season_decals.py, after sinnoh_rooms): HoennB2's rules on every
  overworld chunk outside the north: kisetu_yuki snow patches (1 or 2 tiles, Black 2's own art, clear but in winter),
  ochiba_h leaf clusters next to trees (Black 2's autumn kisetu_hana), Route 20's falling-leaf ribbons (_ha01, data/
  season_ribbons.json from HoennB2) over wooded chunks, animated by Route 20's srt 47 on the autumn records; level
  plain grass, lawn or sand path only, nothing over the tile, 2.25 units up. New materials and shapes in the chunk
  models (add_shapes); a chunk keeps them only under 104,000 B. Seasons off: all clear.
- **Snowfall and Pearl's north** (patches/season_weather.py + src/code/season_weather.c, after season_choice):
  GetWeatherAll's first call answers every Sinnoh zone: winter (seasons on) outdoors snows on Black 2's Route 6 days
  (weather 1 on 11-16 days, 5 = heavy, Hail in battle, on 6-9 days a winter month); the north keeps Pearl's own
  weather all year (Route 216 and Acuity Lakefront heavy snow, Route 217 blizzard, Snowpoint light snow, Pearl's
  day-by-day table for 216, Acuity Lakefront and Snowpoint, Mt. Coronet's sides snow); every other Sinnoh zone its
  header's (none). No Sinnoh zone takes the Unova zone's calendar weather any more: Sandgem had Lentimas Town's
  sandstorm on about half the days (17 in October), seasons on or off; two rooms had Unova's rain indoors.
- Black 2 has no falling-leaves weather (weathers 0-14; a/0/5/5 holds flakes, streaks, rain, sand and sparkles); its
  falling leaves are Route 20's map ribbons, ported above.
- Build (work/agents/seasons/build.log): 3151 snow patches, 696 leaf clusters, 1767 ribbon triangles in 128 overworld
  chunks (largest chunk 99,096 B); 70 outdoor zones snow in winter, 8 north headers, 3 north zones by Pearl's day.
  In game (DeSmuME, test start at Lake Verity, one boot per date; work/agents/seasons/shots/): 10 November:
  lake_verity_autumn, lakefront_autumn, route201_autumn_leaves (leaf clusters), twinleaf_autumn_falling_leaves;
  1 December (a Route 6 heavy-snow day): lake_verity_winter_snowfall, lakefront_winter_snowfall,
  route201_winter_snow_patches; RAM: weather 5 at Lake Verity, the Lakefront and Route 201 in winter, 0 in autumn.
  (A savestate loaded later runs on the host's clock: October = summer, so the next warp switches to Pearl's own
  look. Test a season in one boot run.)
- Left: decals in the outdoor areas built as rooms (lakes, Eterna Forest, ...: colours and snowfall only), Pearl's
  other weathers (rain on Routes 212 and 215, fog on Route 210, ash, sandstorm: headers still clear), snow footprints.


## The stair walk and tree depth (2026-10-20, polish)
User (melonDS, v3 = 5d13b29): "when you go downstairs your head kinda briefly clips into it ... also some trees still
flicker slightly".
- **Stairs: what covered the head.** Black 2's stair warp (RAM, `story_play.py REC...` now logs the player's position
  and the camera every frame: OUT/<name>.json): leaving, the player walks from the foot's centre onto the flight's
  centre (16 frames), the feet on the flight's 45-degree plane (8 units down at the centre of a down flight), the
  camera catching up while the screen fades; arriving, the player stands on the flight's centre while it fades in,
  then walks off. Pearl's stair models were made for Pearl's far camera: the raised rim round a down flight's opening
  (stair_d01/02, 9 units over the floor, 8-12 north of the feet) cuts the top of the head as the player sinks (2F of
  the player's house: also in DeSmuME), the railing of an up flight
  (stair_u01/02, its top ~14 over the arriving player's feet, 8-12 north) the head's upper side on arrival (1F). They
  are behind the player in the world; only the sprite's depth test (people pass up to 3.65 % nearer, less a depth
  step on melonDS) puts them in front.
- **Checker** `python3 b2tools/pearl_rooms_view.py --kinds s [--model hw|desmume] [ZONE ...]`: every zone's stairs
  with a warp (pearl_chunk.stairs_of / stair_walk: the converter's own planes), the player along the walk leaving
  and arriving. Before: 168 of 336 walks (every walk on Pearl's 4 stair models, 84 placements; 0 on the caves' own
  steps) hw, 167 DeSmuME.
- **Fix** (pearl_model_fix "the player drawn into stairs", in fix_building, so every room pack): the parts of
  stair_u01/u02/d01/d02 that stand in front of the walker's quad move AWAY from the camera along its view direction
  (each point stays where it is on screen: Pearl's look unchanged) until the sprite passes in front at every walk
  position of all placements, 0.25 steps + one: u01 6.5, d01 4.25, u02 7.5, d02 5.0 units at most; every corner at a
  moved point moves with it (no tears). STAIR_FIX=none (or PEOPLE_FIX=none): off. Warps, arrivals and the planes
  unchanged. After (hw, all zones, run before the extra step): 14 of 336 walks, none a head in a stair model but
  1-row slivers (13-17 px) in Galactic HQ 4F/B1F (the extra step cleared 4F; B1F's camera is held by the zone's
  boundary), the door mat over the feet at the foot's edge of 2 stairs whose plane lies 2.1 units low there (ov036's
  offset table has no nearer value: the player's house 1F, the Great Marsh entrance 1F), window02 on the wall behind
  the Poketch Company's foot (a prop behind, Black 2's own look). Logs: work/agents/polish/logs/stairs_*.
- **Trees: depth precision.** `python3 b2tools/pearl_seams_check.py --depth --fixed [CHUNK ...]` (new): every layer
  pair under 8 units apart, its gap along each screen row's ray against one depth step of camera 0 there (w^2 / 32800
  at view depth w; rows 33.2-73.2 degrees down, the eye 189.73 over the ground under the point): ratio under 1 = the
  two can round to one depth value (flicker as the camera moves). The world pass's 2.25 gap gives tree cards only 0.77
  of a step at the screen's top row near the ground. Fix (pearl_model_fix TREE_GAP 3.25): tree parts' levels 0 (row
  cards) / 3.25 / 6.5 by column (>= 1.1 steps at every row); separate(): a tree pair whose front part can't go far
  enough has the one behind come forward past it (Pearl's canopy tops lie ~6.2 apart). Opening areas (Twinleaf,
  Route 201, Verity Lakefront, Sandgem, Route 202, Lake Verity, filler 173): 604 pairs (65,708 units^2, all trees)
  -> 73 (17,714). All 494 chunks: trees 7,683 (767,285 units^2) -> 486 (257,421); all layers 9,016 -> 1,820. Left:
  mostly a tree drawn by two chunks across a border, moved differently by each chunk's own pairs (gap 1.1), and
  ground decals (not trees). Offline (melonDS depth model): work/agents/polish/shots/trees_chunk0_flicker_before_after.png
  (Twinleaf's east forest at the top of the screen: 13 order-dependent pixels -> 0). Logs: work/agents/polish/logs/trees_*.
- **Tested** (DeSmuME, work/agents/polish/rom/pearl.nds, TEST_START 521,8,4, one walk 2F -> 1F, `REC` 150 frames;
  the same motion in RAM as before): work/agents/polish/shots/stairs_2f_sunk / stairs_1f_arrival / stairs_1f_walkoff
  _before_after_ingame.png (top v3, bottom now): the head whole in front of the rim and the railing, the stair models
  as Pearl's. For melonDS: the player's house stairs both ways, and trees at the top of the screen on Route 201/202
  and round Twinleaf/Sandgem while walking.


## Rooms: black floors and black gaps (2026-10-25)
User: "why does gardenias gym look all messed up?" (Chapter 3's frames of the Eterna Gym, Pearl MAP_ETERNA_GYM, Black 2
zone 103, chunk 294): black floor between and around the trees, black gaps along the edges, a cloudy sky at the top.
The lead added two Chapter 3 frames: Valley Windworks inside (zone 271, chunk 304: a black column between the rooms, a
black wedge left of the desks, black below the room's south edge at the exit) and Galactic Eterna Building 4F (zone
115, chunk 280: a black square in the back wall).
- **The Gym's floor: the display-list writer.** Pearl's Gym grass (`ngrass`, lit by light 0) carries vertex colours
  (288 corners (0,0,0), 48 (31,31,31)) and a normal at every corner; Pearl sends COLOR then NORMAL for each corner, and
  the GX colours a corner by the LAST of the two (the lights win; GBATEK). `pearl_mesh.encode_groups` sent a NORMAL
  only when it changed: after the first COLOR change the normal stayed (0,1,0), so no NORMAL followed and the grass
  took Pearl's unused black vertex colour. Evidence: in DeSmuME (Chapter 3's build, in the Gym) the four lit floor
  materials found in RAM: lights off, untextured, both faces: the grass stayed black (polygons there, drawn black); the
  built chunk's display list has `BEGIN COLOR TEXCOORD VTX...` runs without a NORMAL; the offline render with the GX's
  colour source per corner (pearl_render now) reproduces the in-game frame (shots/t_gym.png), Pearl's own data renders
  green. All 578 land models and the 1113 land + building models: no vertex with a normal takes a COLOR's colour in
  Pearl's own display lists; re-encoded, only chunk 294 did (193 grass polygons, 270 of its reachable tiles black).
- **Fix** (pearl_mesh.encode_groups): after a COLOR the NORMAL is sent again. Every other model encodes byte for byte
  as before (compared over all 1113 models: only 294 changes).
- **The sky is Pearl's.** The Gym's north wall is a painted sky backdrop (`gym04_d`, 64 units high, in Pearl's model);
  Pearl's camera 9 for this Gym (distance 357.6, 40.6 degrees, half-angle 15: pokediamond ov05_021F6608) shows more of
  it than ours (shots/pearl_look_gym_*.png). Kept.
- **Windworks and Galactic 4F: Pearl's black wall tops.** Pearl draws the tops of its inner walls with an untextured
  material in vertex colour (0,0,0) (Windworks: 17 polygons at 46 units, the partitions at x 4-5 and 17-18; 90 of the
  319 room chunks, 751 polygons). Pearl's room camera 4 is orthographic (1563.5 away, 50 degrees, half-angle 3.5): a
  1-tile wall top is a thin black band, seen straight on. Black 2's camera 0 is perspective, closer and wider: the
  same tops come out about 1.5 times wider, and the ones beside the player lean into wedges (shots/
  windworks_*_pearl_vs_ours.png, galactic4f_*). The square in Galactic 4F's back wall is the top of the stairwell's
  wall block, black in Pearl too. Below the Windworks exit mat: the mat sits in a notch of the south wall; the camera
  boundary (sinnoh_rooms) stops the screen at the mat's south edge, so the bottom row shows black beside the mat
  (outside the room), as Black 2's own rooms do at their doors. No geometry or texture is missing: nothing changed.
  Making them look as in Pearl would need Pearl's own room camera (MAP_LOOK 1d, a decision for the user).
- **Windworks: the player behind a generator** (the music agent's frame, player (12,5), grunt (12,4)): the generator
  (build model 314 `machine_l04`, 49 units high) stands on tiles (11-12, 6-7), exactly the tiles Pearl's collision
  blocks (its twin on 9-10): no off-by-one, not wider than its tiles. It is SOUTH of the player, between the camera
  and the player, so it hides the player's body in Pearl's look as well (pearl_rooms_view's furniture cases are
  geometry behind a person drawn over them; this is geometry in front). Black 2's camera and the people's depth margin
  show head and shoulders, about as Pearl's orthographic camera does (shots/windworks_12_5_generator_pearl_vs_ours.png,
  Pearl's look on top). Nothing changed.
- **Check** `python3 b2tools/room_look_check.py [--files DIR] [ZONE ...]` (all 376 room zones; ~6 min after a
  3-min warm-up): `tex` (a material's texture or palette missing from the area's set or the prop pack's set),
  `dark` (lit polygons coloured by a COLOR), `floor` (a reachable tile whose floor Pearl draws and ours not),
  `hole` (a tile Pearl's model covers that the installed room leaves empty). `--pair OUT ZONE X,Z [--people]`:
  Pearl's look (Pearl's models and camera) over ours. On the installed files of a build (a/0/0/8 etc.):
  before (Chapter 3's build of 2026-10-25) dark 193 polygons, floor 269 tiles (both the Eterna Gym only), hole 0,
  tex 0; after (this fix) all 0. Both: tex_pearl 5 (`dun_allpeak` in Mt. Coronet South 1F/2F, North 1F room 1 and
  Wayward Cave B1F names a palette `dun_apeak` that Pearl's own set 42 lacks (it has `apeak`): Pearl's data, left).
  Only chunk 294's model differs between the two builds' a/0/0/8 (46 other chunks differ in collision only: Chapter
  3's floor mats).
- **Tested** (DeSmuME, work/agents/rooms/rom/pearl.nds, TEST_START 103,16,27 then a quick rebuild with 271,12,5;
  the Gym's and the Windworks' scripts generated for the test only): the Gym's grass, sand path and tree shadows
  drawn from the entrance, the middle and Gardenia's platform. Proofs (work/agents/rooms/shots, 256x384, Pearl's look
  on top): gym_entrance_pearl_vs_ingame, gym_gardenia_pearl_vs_ingame, gym_before_after_ingame (Chapter 3's frame
  over now), windworks_19_8 / 12_15 / 12_5_generator_pearl_vs_ingame, galactic4f_11_8_pearl_vs_ours_offline,
  gym_ram_experiment_*.png (DeSmuME RAM edits on the before build: the floor materials only / untextured).

## Rooms: the void past the edge (2026-10-25)
Chapter 4b's frame (work/agents/ch4b/shots/GFX_daycare_sky_grass_east_of_room.png, Solaceon Day Care, Pearl
MAP_SOLACEON_DAYCARE, Black 2 zone 549, chunk 194, player on the mat (9,11)): "east of the right wall an outdoor blue
sky with clouds and a green diamond grass floor, where Pearl shows black void".
- **The Day Care: Pearl's own room.** The wall right of the player is the partition at x 11 (z 2-7, with Pearl's
  black wall top and a poster), not the east wall: the room goes on to x 17. Tiles x 12-16, z 3-11 are walkable (Pearl's
  collision) and form the Day Care's Pokémon corner: floor `grow_04` (green, a yellow diamond on each tile), walls
  `grow_05` (painted sky with white clouds), in Pearl's model and Pearl's texture set 21. Pearl's own look from the
  mat (room_look_check --pair, Pearl's orthographic camera 4) shows the same corner: shots/daycare_9_11_pair_offline,
  daycare_14_8_pair_offline (work/agents/rooms2). Past x 17 both games draw nothing (black). Nothing changed. What
  differs from (14, 8): Black 2's perspective camera shows the east wall's inner face (the sky mural) as a slanted
  band; Pearl's orthographic camera sees side walls edge-on (`beyond` below).
- **What Black 2 draws past a room's edge: the clear colour.** Black 2 clears the screen with the light table's 6th
  colour, opaque (field_light.c FieldLight_FlushCore: G3X_SetClearColor(materials[5], 31, ...)); Pearl clears to black
  with alpha 0 over a black backdrop (pokeplatinum easy3d.c Easy3D_SetupEngine; fieldmap.c loads BG colour 0 = 0x0000).
  Indoor rooms take Pearl's indoor light table, whose clear colour is black. The 19 room zones on Pearl's day cycle
  (areas 8, 12, 14, 44, 49, 51-54: the lakes, Eterna Forest, Floaroma Meadow, Mt. Coronet's mountainsides, Amity
  Square, Pal Park, Trophy Garden, the Great Marsh, Battle Park, the moon islands, Sendoff Spring) took Black 2's
  outdoor tables 140-143, which clear to the sky colour (16,24,30) by day, (31,24,15) in the evening, (8,3,18) at
  night: wherever Black 2's wider camera saw past the map's edge it drew sky where Pearl's void is black.
- **Fix** (maplook.outdoor_room_lights, sinnoh_rooms, part of 'light'): those areas' records (and their four seasonal
  records) use copies of 140-143 with the clear colour black (4 tables appended to a/0/6/0, 3,120 B of the 16 KB
  reserve). Lights, materials, fog colour unchanged. Cracks in these rooms show black, as in Pearl.
- **Check** room_look_check kinds `sky`, `model`, `beyond` (from every reachable tile at the end of its row or column,
  one ray per 8x8 pixels; `--kinds`, `--ray-step`): `sky` = nothing drawn and the room's light table clears to a
  colour that is not black; `model` = ours draws a surface where Pearl's own look meets nothing and no surface of
  Pearl's is within 5 units (geometry ours has and Pearl's room has not); `beyond` (a note) = Pearl's own geometry
  Pearl's camera never shows: off its screen from every reachable tile, or edge-on. Before (Chapter 4b's build,
  its ROM's a/0/0/8 etc.): sky in 3 zones, Mt. Coronet North Mountainside (210, zone 277: 678,080 px over all 140
  edge tiles' screens), Mt. Coronet South Mountainside (211, zone 278: 78,592 px) and Lake Valor Galactic (314, zone
  431: 9,664 px); the other 16 day-cycle zones are closed in by trees and cliffs. After (this build's files, every
  kind, all 379 room zones, ~40 min): sky 0, tex/dark/floor/hole 0, tex_pearl 5 (as before); model 128 px (2
  single rays on the edge of a plant the furniture fix pulled toward the camera: not void); beyond 76 zones (cliffs
  and trees past the lakes' and outdoor rooms' shores, cave walls, the west walls' inner faces in houses and
  gatehouses): Pearl's art seen by Black 2's wider camera, left (Pearl's own camera: MAP_LOOK 1d, the user's
  decision). Offline proof: shots/mount_coronet_north_mountainside_10_15_void_sky_before_black_after_offline,
  coronet_north_mountainside_10_15_pair_offline (Pearl's look on top: Pearl's void is there too).
- **Node translations** (found on the way): pearl_mesh reads a land model's vertices without its node's translation.
  Two Pearl land models draw on translated nodes: chunk 410 (Amity Square's south-west quarter: the whole model on a
  node 576 units north; its raw vertices sit one chunk south) and chunk 417 (Floaroma Meadow: six small shapes on
  nodes 528-632 east and 904-936 north, outside the map). The DS applies the node (the game draws them right), the
  offline tools did not: room_look_check and pearl_render now add the translation (pearl_mesh.shape_translations;
  without it Amity Square's quarter looked empty and the check reported 1.9 million px of sky there). Not changed in
  the conversion: chunk 410's tile heights match the translated model (452 tiles), but pearl_chunk.fix_model
  (under-floor cut-back against neighbours, layers) and sinnoh_rooms' camera boundary (south extent 1,515 instead of
  939; no effect: the camera never gets that far south) work on the untranslated vertices. The check finds no
  model/void problem in Amity Square.
- **Tested** (DeSmuME, work/agents/rooms2/rom/pearl.nds; the Day Care is not translated in this tree, so TEST_START
  548,8,10 in Solaceon's Center, out of the door and into the Day Care's): the mat (9,11) gives Chapter 4b's frame
  again; the player walks onto the green floor at (14,8) and (15,4) (it is the room), the east wall's inner face (the
  sky mural) and black past it. A quick rebuild with TEST_START 421,46,52: Lake Verity on the new outdoor-room table,
  lit as before (no void in view there). Proofs (work/agents/rooms2/shots, Pearl's look on top):
  daycare_9_11_pearl_vs_ingame, daycare_14_8_pearl_vs_ingame, daycare_15_4_ingame, verity_46_52_ingame.
  Not seen in game: the void in the three sky zones (none is translated yet, test_story_start needs a translated
  zone): for melonDS, Mt. Coronet North Mountainside's west end (10,15) by day: black past the snow, not sky blue.

## People's and objects' sprites (2026-10-25, the world sprite pass)
- The PWT's Gym Leader sheets had a white X for the back view and the steps toward the camera: b2tools/frame_check.py
  checks every person's frames; patches/pearl_pwt_frames fills each X with a copy of the sheet's own front frame (the
  user: no generated pixels).
- Pearl's own pictures, pixel for pixel, for the Rock Smash rock (code 186), Moss Rock (371), Ice Rock (188), bollard
  (189, was an orange traffic cone) and Cut tree (108, Black 2's Cut needs that code): patches/pearl_npc_sprites
  OBJECTS. Hearthome's street lamps are Pearl's own (map model, texture c5_light): not a stand-in.
- **Strength boulders: Pearl's own 1 x 1 boulder (2026-10-26, DECISIONS; before: Black 2's 3D 2 x 2 one).** Pearl's
  boulder (SPRITE_ROCK 84, mmodel 82 'rock', 16 x 16) is code 109, Black 2's own unused 1 x 1 Strength rock
  (OBJ_CODE_STRENGTH_ROCK, type "none" in Black 2, no zone or script places it): its a/0/4/7 record takes code 101's
  (a Black 1 Sage nothing names, 7 frames) and 101's sheet gets Pearl's boulder on every frame (patches/pearl_npc_sprites).
  No C change: Black 2's Strength takes 109 as a boulder (ov012 IsNPCStrengthRock) and reads the footprint from the
  record (ov036 StrengthRockSpaceCheck, ov012 CheckBlockedCollPathToPosition / CheckAreaOverActor); the push sound
  stays Black 2's (SEQ_SE_FLD_03; Pearl SE_DP_UG_023); Pearl has no boulder holes. Black 2's own 2 x 2 boulders (8195
  outdoors, 8197 caves) are unchanged for any Unova zone. `python3 b2tools/boulder_check.py` checks all 55 (13 zones):
  Pearl's pushes on Pearl's map against Black 2's on the converted chunks, 1 x 1 and the old 2 x 2.


## Black 2's water and grass on Pearl's shapes (2026-10-26)
Reported: Fullmoon Island's pond and Verity Cavern's water flat light blue, Pal Park's and Route 210 N's ground flat
mint (80,248,144). **Pearl's own look**, not a conversion loss: Pearl's puddle_b/puddle (and the caverns' plane under
puddlep_dun's see-through water texels) are one colour each, the mint is Pearl's ngrass at noon (Pearl's light
saturates to white too; Sandgem's grass is the same colour); the installed spring/summer sets are byte for byte
Pearl's, and Pearl's only runtime map texture changes (data/fld_anime0-10: sea, rhana, asasea, hamabe, asahamabe,
t3_fl_b/p/r/y.1, dun_sea, lakep.1) touch none of them. The user then chose Black 2's water and Black 2's grass ground
(offline before/after: work/agents/looks/shots/water_preview_sheet.png, grass_preview_sheet.png).
- **b2tools/b2_look.py** (MAPLOOK_FIXES `b2_water`, `b2_grass`, both default), run last in pearl_chunk.fix_model:
  Pearl's water materials take Black 2's records and names (sea: sea_mizu1 under sea_mizu1_1 at 16/31; ponds and
  lakes: mizu_sita2, the cloud reflection, under ike01 at 12/31; caves: d0_miz under d0_miz2), world-aligned texture
  coordinates at Black 2's density and offsets; a missing layer is a copy 2.5 units above (surface) or below (base);
  the lakes' l_lake props (Verity, Valor, Acuity) move into their chunk models (b2_look.placed_props) so the area's
  SRT animates them. Outdoors ngrass binds Black 2's grass01ax (64 x 64, one texel a unit) of the season.
- Animation: Black 2 scrolls water by material name with the area's SRT file (a/0/6/8): every overworld area record
  names file 0 'area_ita_00' (maplook.water_srt; areas 9, 12, 17 had Unova's 36-38), outdoor rooms with water file
  0, caves with water file 3 'in00_dun_ita' (sinnoh_rooms). Black 2's SRT object per chunk holds 51 materials:
  b2_look adds none past 50.
- Texture sets: every outdoor set (overworld and outdoor rooms, each season; the north: winter) gets grass01ax,
  sea_mizu1, mizu_sita2, ike01 from Black 2's season set (2-5), cave sets with water d0_miz and d0_miz2 (set 296)
  (b2_look.add_textures; ~45 KB per set now, Black 2's own go to 98 KB). Spring and summer: Pearl's art with grass in
  it (path, lawn, beach and puddle edges, tree shadows, flowers' grass, bare patches) takes Black 2's grass colours
  (sinnoh_reskin.b2_grass_rims, grass colours only); autumn and winter did already. The trees and the tall grass
  stay Pearl's in spring and summer (the user).
- Kept Pearl's: shores and edges (puddlep*, lakep.1, hamabe, beachp, seaside3: Fullmoon's pond keeps a pale rim,
  Route 219's surf band is lighter than Black 2's sea), the indoor rooms' grass (the Eterna Gym).
- pearl_mesh.write_model (a model with materials and shapes added or re-bound; every land model round-trips byte for
  byte) and pearl_render's A3I5/A5I3 alpha (it overflowed: every translucent texel decoded at ~14 %).

## Seasons after Black 2's grass (2026-11-01)
The user: "seasons aren't as visible as they were in previous updates". Offline (work/agents/looks2/season_sheet.py: every
chunk as the build makes it, Black 2's tilted camera, midday; shots/seasons_before_after.png, seasons_north_before_after.png).
- **Cause: 3cca6f6, the ground.** Before it spring and summer drew Pearl's vivid mint (10,31,18), so yellow autumn and pale
  winter stood out. Black 2's own grounds lie close: spring (20,28,16), summer (17,27,22), autumn (28,28,16), winter
  (23,27,19), spring and winter nearly alike. Mean screen difference (0-255) before -> 3cca6f6: Twinleaf spring-autumn 22.5
  -> 11.3, spring-winter 20.0 -> 12.2; Route 201 39.5 -> 27.7, 35.4 -> 27.2; Route 203 40.3 -> 29.8, 37.0 -> 30.0. Spring
  and summer differ now (about 10; identical before). No earlier commit is stronger than 8a946c3 .. 3cca6f6^ (no season,
  texture-set or decal code changed between them). Not the cause: the decals (the same 2,994 snow, 685 leaf, 1,715 ribbon
  in the build logs before and after; only chunk 164 over the limit, as before), autumn's SRT 47 (it has the water tracks).
- **Bug: the north was green.** b2_look bound the north's ngrass to Aspertia's winter grass01ax, so Snowpoint, Routes
  216/217, Acuity Lakefront and Mt. Coronet's mountainsides (Pearl area 14) had green ground all year. Now Black 2's snow
  grass01ax (a/0/1/4 set 45, Icirrus; b2_look.grass_set).
- **Winter's ground is snow everywhere (the user's choice among the sheets, 2026-11-01):** b2_look.grass_set gives every
  outdoor map that grass01ax in winter. Pearl's art with grass in it follows (sinnoh_reskin + recolour.grass_over: path and lawn edges, tree
  shadows, bare patches, flowers' grass take the snow at Pearl's relative brightness; stone and sand keep Black 2's winter
  colours; the trees and tall grass keep theirs, Black 2's winter colours). Difference now: Twinleaf spring-winter 26.4,
  Route 201 41.8, Route 203 41.9, above their old values. Snow patches stay (they show on paths; on the white ground hardly).
- **Decals:** `ochiba_h` is Black 2's kisetu_hana of each season (patches/season_decals: pink and white blossoms, white
  flowers, autumn's leaves, frost), on grass only; denser (P_LEAF 0.45 next to trees, P_LEAF_OPEN 0.05 elsewhere; P_SNOW
  0.14 / 0.40 / 0.60). A full chunk thins its clusters and snow (every 2nd, 4th, 8th) instead of having none. Sweep over the
  156 overworld chunks outside the north (estimated sizes): 3,853 snow, 1,480 clusters, 1,715 ribbon triangles kept; chunks
  164, 165 and 171 have no room for any (they still change ground and trees); largest 104,056 B (limit 110,600).
- **Left as it is:** spring-autumn in towns stays about 11 (Black 2's lime and yellow differ in red only; the user: no autumn
  tint, Black 2's grass colours stay). Spring and summer trees and tall grass are the same (DECISIONS 2026-10-25).
- **Seasons off** = spring all year (season_choice.c): Black 2's spring ground, now with its blossoms beside trees, all year;
  the spring column of the sheet. To see in game.
- Not in game yet (one combined build): for melonDS, winter (DS clock December) at Twinleaf and Snowpoint, spring blossoms
  and summer flowers on Route 201.

## The clear colour outdoors and under weather (2026-11-01)
Black 2 clears the screen with each light table's 6th colour; Pearl to black. The overworld kept 140-143's sky blue past
map edges and through 1-px cracks (Celestic's south cliff, Route 222's gatehouse, the Victory Road entrance), and every
weather swaps in a whole table of a/0/6/1 with its own clear colour (Turnback Cave's sky-blue void under the mist: table 1
clears to the day's sky). Now maplook.outdoor_light gives the overworld the outdoor rooms' copies of 140-143 clearing to
black, and maplook.weather_lights_black clears all ten weather tables to black. Battles read only those tables' lights
and material colours (field_light_status.c). Lights, fog colour and outlines unchanged. For melonDS: a black crack shows
more than a blue one on bright ground, as in Pearl (the under-floor still backs most edges).

## Sprite pass 2 (2026-11-01)
- **Fly:** patches/pearl_player_sprites.apply_fly: Black 2's take-off and landing scenes (a/1/1/6 models 58, 66, 138, 142,
  textures fly_hero.N / fly_heroine.N, 32 x 32) take Pearl's frames of the same pose (sphero: standing, crouched, ball
  out, ball high; the landing's back views: Pearl's walking back stand), pixel for pixel, the palette in place. Black 2's HM cut-in
  (effect 3) shows only the Pokemon: the "HM cut-in with Nate" reports were Fly's scene. Offline:
  work/agents/looks2/shots/sprites_pass2_offline.png.
- **Vent:** Pearl's venthole (mmodel 161) on code 143. **Snowball:** Pearl's whole frame (mmodel 381, r09_o01.1) on code
  144's one-frame billboard. In Pearl it is one card tilted to the camera; Black 2's billboard stands upright, the picture the same. No break frames.

## Checked, no change (2026-11-01; Pearl's own look)
- Vista Lighthouse deck's shaft top: Pearl's own black top of the lift block, wider under Black 2's camera
  (work/agents/looks2/shots/pair_deck.png, Pearl's look on top). Victory Road 2F's black east of the boulders is in
  Pearl's look too (pair_vr2f.png). Galactic HQ: one offline pair only, at B1F (16,12), near the map's edge (pair_hqb1.png):
  nothing drawn past the room in either look, more of the room in Black 2's wider view; not compared across the HQ. Only
  Pearl's own room camera would show less of these voids (the user's camera decision 2026-10-26).
- Route 210 North's thin beige bridge: Pearl's own 'nbridge' deck (one tile wide), the same stripe under Pearl's camera
  (work/agents/looks2/shots/r210_overview.png).
- The roof at north doors: on the door tile Pearl's camera shows only the cap too (work/agents/camera/shots/3col_1_*.png).
- Trees along Valor Lakefront's row (718, 760-762): Pearl's trees cover the player's legs there too (offline,
  shots/trees_valor_tilt_vs_pearl.png: an approximate person card). The lakes' arrivals and Acuity's south row were not compared.

## Polygon load (the user, 2026-11-01: "frames drop when approaching Valley Windworks")
Black 2 draws a 2 x 2 window of chunks round the player, each chunk whole (per chunk bounding-box cull, no finer), and each
placed prop if its box is on screen. Black 2's own chunks: median 417 polygons, largest 2,133. Route 205 South's and its
neighbours' cliffs are among the heaviest of Sinnoh, and the first the story reaches: Pearl's own 3,475 polygons in the window
(5, 18) (chunks 42, 37, 33, 35), 3,175 in (5, 19) and 2,697 + 1,066 for the 9 windmills etc. in (6, 19), and the model fixes
added ~60 % (T-junction splits ~40 %, the under-floor ~18 %): 5,912, 5,702 and 4,522 + 1,066. Top-six window of the whole overworld
at the point the user was (only Sunyshore, Route 213 and Route 225 are heavier). Not the windmills: their joint animations
aren't installed (plain props, 103 polygons each). Not limits: actors, chunk sizes (78 KB), SRT. No polygon can be culled
ahead: each is in some camera view from a walkable tile, and north faces are only ~15 % (b2tools has no finer check).
Fix: pearl_chunk.CHUNK_POLYS: an overworld chunk with over 1,000 polygons gives its T-junction splits back (the under-floor
stays, so a crack on flat ground shows grass there, not the sky). DeSmuME has no geometry timing: the frame rate itself is for
melonDS. Pearl's windmills don't turn here (their BCA isn't installed): not this bug.

## Solid plant pots and the trash can (the user, 2026-11-01: "some trash cans look distorted")
dustbox01 (build model 86; 19 room zones: Jubilife Pokétch Co. 3F, Old Chateau, Grand Lake rooms, Eterna, Floaroma's flower
shop ...) shares plant01_mat with the plant pots plant01 and plant02 (85, 522). pearl_model_fix.is_tree took 'plant' for tree
cards, so base_shift moved each wall 3.25 or 6.5 units along its normal by which side of x 0 it lies on: the can came out
lopsided, 23 units across for its 16. SOLID_PLANTS keeps those materials out (work/agents/fixes/shots/dust_*_poketch3f.png).


## The upright depth (2026-11-01): people drawn into furniture, the whole game's rooms
The user kept seeing heads clipped into furniture. The cause (section "People drawn into furniture") is that a person is
tested at ONE depth, their feet's less a margin, while on screen their head is level with what stands behind them. A
bigger margin can't fix that without showing people through what is in front of them, so people's depth now stands up.
- **The change.** Each person's own projection matrix: only z changes (m[1][2] = m[3][2] * sin(pitch) * slope / H, H the
  eye's horizontal distance to the feet, and m[3][2] so the feet pass MARGIN + one depth step nearer than they are), which
  is the z of a plane standing straight up at the feet. x, y and w stay, so no sprite pixel moves. What is behind the feet
  in the world stays behind, what is in front stays in front, whatever its height. Decomp: src/pearlb2/resident/
  people_depth.c (BlActScene_Draw with the matrix per actor), called from FieldRenderPhase2_Fieldmap in place of
  BlActSys_Draw for the people and the grass quads, and PearlB2_ObjectProjectionMatrixOffset (notes the zone) in place of
  GetObjectProjectionMatrixOffset; fieldmap.c's size unchanged (only call targets differ). Shadows and footprints stay
  Black 2's. Grass quads stand 2 units north of the walker and must keep covering the legs, so they get the same lean
  and 7 units more margin: ahead of the walker by 2-5 units over the whole screen (computed, not filmed).
- **Reflections keep Black 2's depth (2026-11-12, decomp 4f3acc4961).** Black 2's reflection (fldeff_reflect.c) is the
  actor's picture flipped upside down (flipT), 12 units south and 33 under its water, in the people's scene. Stood upright
  it came nearer than the shore: on Victory Road B1F a copy of the player showed on the dry ledge at the water's edge, and
  on the dry ground for about 10 frames of the jump off Surf (and a surfer looked doubled, which the rule for the surfer
  in PearlB2_ReflectionHidden had answered). DrawUpright now skips flipped pictures: they keep Black 2's matrix, and
  the land in front hides them as on the routes. The converted water's opaque floor 4 units under its surface
  (terrain/water.py) hides them too, so rooms show no walkers' reflections, as the routes never have (a decision for the
  user: notes/DECISIONS.md 2026-11-12). Seen on screen: Victory Road B1F at the water's edge, the surf south, the jump off.
- **The switch: data/people_depth.json** (patches/people_depth.py makes the table, gPearlB2PeopleDepth; NULL or slope 0 =
  Black 2's drawing): slope by Pearl map type, overworld, single Pearl zones by name; margin_16ths; furniture_fix;
  solid_tiles. Diamond shares it. **New in the build's list: people_depth.** Taking it out: leave the patch out and set
  furniture_fix to true (the old counters come back).
- **Furniture back to Pearl's shapes** (furniture_fix false: pearl_model_fix.people_off): with the upright depth the sinking
  adds nothing (with it: NPCs 9, player 36, should-stay-hidden 60 NPCs; without: 10, 34, 39). Stair models too: the stair
  walk (`--kinds s`) has 0 findings of 336 walks with Pearl's stair models.
- **Solid tiles**: Canalave Gym's two statues, (14,25) and (18,25), walkable in Pearl (solid_tiles, through
  pearl_chunk.bed_solid). Their inspect events stay on those tiles (read from beside them: not tested). warp_check offline: no findings; scene_check
  --all: none in that Gym.
- **Checker** (pearl_rooms_view.py): new count `h`, should stay hidden: the first surface along a pixel more than 4 units
  south of the feet, above floor level, yet the sprite passes (with the depth step in its favour; NPCs also with the camera up
  to 9 rows south, where a k margin is largest). --upright, --margin, --offset, --offset1, --sweep, --jobs; defaults
  as the build. Default zone list leaves out the Underground (Black 2 zones 633-651; in Pearl's room list only
  MAP_UNDERGROUND, zone 633: the user, no furniture and nobody but the player): not measured, in no total below, and its
  slope is 0. An agent tree now reads the lead's sprite sheets (it fell back to Black 2's: 8013 player findings, wrong).
- **Candidates** (403 zones, hw; player and NPC findings = tiles or people with 6+ px; the Floaroma Meadow and Great Marsh
  apart because their ~1400 tiles only swap classes: feet among flowers, a row of marsh plant, 14-17 px):

  | candidate | NPC | NPC heads | player | player heads | hidden NPC (20+ px) | hidden player (20+ px) | meadow, marsh m / h |
  |---|---|---|---|---|---|---|---|
  | flat 0x136 / 0x1ee, furniture fix (before) | 167 | 79 | 490 | 238 | 15 (7) | 2 (0) | 1533 / 1054 |
  | flat 0x1ee everywhere | 61 | 30 | 158 | 82 | 124 (37) | 4 (2) | 1533 / 1054 |
  | flat 0x260 everywhere | 38 | 20 | 109 | 31 | 182 (85) | 39 (11) | 361 / 1055 |
  | upright, k of 0x136 | 8 | 0 | 11 | 5 | 82 (11) | 121 (36) | 0 / 1417 |
  | upright, margin 5.5 | 10 | 0 | 36 | 20 | 31 (5) | 50 (29) | 1414 / 0 |
  | **upright, margin 6 (chosen)** | 10 | 0 | 34 | 20 | 39 (6) | 62 (29) | 0 / 1414 |
  | upright, margin 7 | 5 | 0 | 7 | 5 | 71 (7) | 139 (36) | 0 / 1417 |
  | upright 7/8 slope, margin 6 | 10 | 0 | 89 | 58 | 10 (0) | 2 (0) | 1414 / 0 |

  The offset alone never gets there: 0x260 still cuts 20 NPC heads and already shows 85 NPCs through furniture. A constant
  margin (not k * distance) keeps people high on the screen from gaining 12 units. Totals `python3 pearl_rooms_view.py`:
  before npc 170 (heads 79), player 2020 (heads 240), hidden 15 / 1056; now npc 10 (heads 2, the lab's trio, below), player 32
  (heads 20), hidden 39 / 1474 (1414 of them meadow and marsh). The lead's 2026-11-01 run with the Underground: npc 170, player
  2014. Logs: work/agents/heads/logs (sw4/, after_hw.txt).
- **Saturn's lab stays flat** (zones in the json, slope 0): the render showed Uxie over the lid of its containment unit: a lid
  right over a person is behind an upright plane, and the user's decision of 2026-10-26 keeps their heads under the lids. The
  checker now counts that kind too, `o`, a surface within 4 units of the feet in z and 20+ over them: 56 NPCs, 818 player
  tiles (660 of them the Marsh's and Meadow's trees, 11 px at most). The large ones are what the fix means to do (a person flush
  against a wall or door, drawn over it: Canalave Gym's back row 146 px, the Centers' 2F doors) or look the same in renders
  before and after (HQ's sliding door halves in their walls, Gym guides beside statues). Only a few were looked at by eye, so
  look for any other person meant to be inside something.
- **Left, and why**: player heads 20: back-row tiles at door frames and wall recesses, 7-48 px, a band of 1-2 rows (Old Chateau
  2F's 5 doors 48 px, looked at; Contest Hall lobby and Mansion lobby 29 px; the rest by their rows and positions). NPCs 10: the
  lab's trio (above), Rowan at Spear Pillar's (29,36) on a solid tile by a column (the script moves him before adding him), people
  in beds and at a table (Pearl's, feet only), Oreburgh North House 3F's worker at (2,11) (a solid tile outside that floor's model
  in Pearl's data). Should stay hidden 20+ px, NPCs 6: HQ 4F_1's obj 1 and the card key prop 56, Hearthome Gym's guide and statue 44,
  Floaroma Meadow house's tv 41, Sandgem's and Floaroma's Mart (9,6) and the shelf 37 (only with the camera far south). Player 29:
  the same door frames. Battle Tower lobby's object_bt 14 px. The overworld stays flat (slope 0): the checker doesn't cover it;
  "overworld" in the json turns it on to try. Floaroma's flower shop frame (work/agents/fixes/shots/tc1.png, the player at (10,5)):
  the body behind the pot is right, the pot stands in front, and those pixels don't change. The woman at the counter: no finding now.
- **Not proven yet (all offline)**: the two objects compile and fieldmap.o's functions keep their sizes; nothing has been linked
  or run, so the layout check, the C on a DS and every number above (a model of melonDS's depth, not melonDS) wait for the combined
  ROM. To watch there: fog (a sprite's fog comes from its depth, so a head may fog less than the feet in fog zones, up to ~30 units
  of depth), tall grass over the legs, the exclamation mark and emotes.
- Proofs (offline, hw model): work/agents/heads/shots/{mart,eterna2f,counter,fs_10_5}_{before,after}.png; lab_upright_regression.png
  (why the lab stays flat).
## The windmills (2026-11-01; "a long grey wedge" south of Valley Windworks' door)
Nothing is wrong with the model: it's Pearl's, tower and pixels. The wedge is a rotor blade, seen edge-on. Valley Windworks' nine
windmills (chunk 36, models d2_s01, d2_s01a, d2_s01b) have a rotor on its own joint, turned by a BCA we don't install, so they
stand at frame 0, one blade up and north. From Black 2's close camera (eye 186 up, 142 south of the player) the one 6.5 tiles
south of the door has its hub at the bottom of the screen and that blade reaching up over the player: a wireframe from those
numbers reproduces the frame (work/agents/known/wind_sim_cam0.png). pearl_model_fix.windmill_pose turns the rotor 25 degrees round
its hub at build time, the player at the door then uncovered (35 % -> 0 %; work/agents/known/wind_pose.py). Left: 2-5 tiles north of
a windmill a blade or the tower still crosses the view, in any pose: that is this camera with a 130-unit-tall model nearby. Only
Pearl's far camera or the blades turning would change that.


## Platinum's ground (2026-11-02; Platinum step 3, overworld ground and texture sets)
Platinum's overworld against Pearl's, by Pearl's land numbers (work/platinum/land against work/pearl/land, matrix 0):
- 142 of the 176 overworld land slots have another terrain model; 41 also changed tiles. More than 30 tiles: Twinleaf 0,
  Route 212 South 90 and 91, Acuity Lakefront 100, 102, 103, Route 229 134, Route 230 138, Fight Area 132 and 133, Survival
  Area 166, Resort Area 142, and Stark Mountain's outside 172 (step 4). Small: Jubilife 17 (26 tiles), Acuity Lakefront 101
  (16), the League 113 (6), Route 227 170 (5) and 171, Sunyshore 96, Floaroma 32, Pastoria 81 and 82, Eterna 44, Veilstone
  78, Route 228 139 (1 to 4 each). New slot 578: a filler chunk in place of Pearl's 176 in 50 cells of the Battle Zone's
  mountains (palms in place of round trees).
- What the "retouched" models are (each polygon matched by position, then compared): 99,833 polygons the same; 9,241 the
  same shape with another texture (cliff faces criffp -> Platinum's regional criffp2 to criffp5, criffp_a13, Celestic's
  c07_criffp; shore rock seaside3 -> seaside3_2; tree01 -> tree04_2 in the south); 8,944 added and 7,531 removed (the
  places above, the snow patches, the Battle Zone's palms); 1,374 with other vertex colours or normals, 716 with other
  texture coordinates. Platinum's texture sets also redraw many textures under the same names (set 6: 39 textures' pixels,
  46 palettes): Jubilife's roads, fences and plaza in grey, greener tall grass, darker rocks, trees shaded in two tones.
- Snow: Twinleaf, Routes 201 and 202, Verity Lakefront and Lake Verity have Platinum's snow patches (s_snow, s_snow02-04,
  s_sonwp), 1 unit over the grass, and Twinleaf's 44 snow tiles have their own behaviour, 0xa9 SNOW_WITH_SHADOWS
  (footprints and a snow step in Platinum). They are Platinum's own art: kept, in every season (see "For the user").
- The Battle Zone's trees are palms (tree3_01, tree3_02, conttree3_2) where Pearl has round ones (tree2_01, conttree2_*).
- The Fight Area's north end is the Battle Frontier's gate, with two pools (bf_lake, sea tiles, flat light blue).

**The proof's seams: the cause.** pearl_model_fix.separate keeps layers 2.25 apart. Its decal rule looks at one pair of
polygons, decides which of the two lies wholly over the other, and moves that one's whole piece (same material, same
plane, joined at corners). Platinum's snow polygons are bigger than the grass tiles under them, so a grass tile lies wholly
under a snow polygon and the rule took the grass for the decal: the whole lawn (123 polygons, 95,000 units^2) went 1.25
down, then by its pairs the path 1.5 and the path's edges 2.25. Pieces moved by different amounts part along the edges they
share: thin lines of the clear colour (black outdoors since 2026-11-01) along every lawn and path edge, and moved ground gets
no under-floor. The white patches are the snow itself. In the Survival Area a second case: Platinum's grass pieces overlap
in slivers (one texture in one plane, drawn twice), and the rule lifted a 2,800 units^2 piece 4.5 units: black lines round
the rock ring west of the Center. Offline, `world_look.py` reproduces the proof's frame (work/agents/plat-world/shots/
t_twinleaf_autumn_before_after.png: the proof's base code on top).

**The fix (version.GROUND_STAYS, Platinum only).** A big ground piece (4 tiles or more) moves only against a bigger one,
whichever polygon lies over the other: against a smaller piece, ground or not, the smaller one moves; one ground texture drawn
twice in one plane stays as it is; of two level ground pieces the smaller one is on top. Now in Twinleaf only the snow moves
(up, 2.25 or 4.5 over the grass); its ground stays where Platinum drew it. Pearl and Diamond keep the older rule: with the
switch on, 148 of their 526 chunks would come out differently (the under-floor's second try, below, in most; the layers in 19:
ground that sinks or rises a little, Route 212 North's grass 0.2, Route 215's lawns 1.25, a sea 1.25 that b2_look replaces
anyway, cave and room floors, Canalave Gym's floor), and their 1.0 output must not change. (1.0.1 turns it on for them:
"1.0.1: the map rows for Pearl and Diamond" at the end.)
- The under-floor (same switch): where its copy 4 units down comes within 2.25 of a surface that lies between it and the
  ground (a backing layer), a second try 8 down. Platinum's Twinleaf path lies 3 units under its lawn edges with a sand quad
  under it, which had crowded the edges' copies out: unbacked edges there 1,372 units -> 316 (Pearl's own Twinleaf 308). The
  extra copies fight only with other hidden layers (chunks 88 and 89: the same 6 and 3 visible fighting pairs either way).
- Heights: the snow patches were taken for ground, 1 unit over Platinum's BDHC; pearl_chunk.SKIP_MATERIALS leaves them out.
  Behaviour 0xa9 is Black 2's snow (class 0x0e, flag 8: snow footprints, no slowing; ov012 field_actor_tool.c).
- **Winter only (the user, 2026-11-03):** the snow patches (s_snow, s_snow02, s_snow04, s_sonwp) and the snow on Platinum's
  trees there (tree04_2 = tree01 with 150 of its 4,096 texels white) show only in winter. sinnoh_reskin.reskin_sets clears the
  patches' texels in the spring, summer and autumn sets (nsbtx.clear) and gives tree04_2 tree01's texels there
  (nsbtx.copy_texels); overworld and outdoor rooms (Lake Verity, area 62) both go through it. Their 0xa9 tiles read as
  plain ground, which is what Pearl has under all 44 in Twinleaf and 20 at Lake Verity, so summer grass leaves no
  footprints and gives no snow battle background. Seasons off is spring all year, so they never show. Offline: Twinleaf in four seasons
  (summer's trees match Pearl's own), the sets' texels checked per season, season_grass_check 0, version_check ok.
- **Check: `pearl_seams_check.py --holes`** (new): every chunk's opaque polygons (trees and water left out) seen along the
  build's camera (59 degrees, from the south), Pearl's raw model against the installed one, 2 px a unit: a pixel the raw
  model covers and the installed one leaves open is a seam the fixes made. The proof's code: Twinleaf 216 units^2, the Survival
  Area 16.5; now 0 and 0. The whole overworld: Platinum 528.5 units^2 (chunk count not recorded), Pearl's own 583.8 in 24 (cliff
  and slope pieces the layers rule moves, a few chunk edges; Route 211 West's cliff by the water, 47 in both, the largest: a
  thin black line). Platinum-only and small: Route 204 North 31 (23 units^2, a dotted line on a cliff corner where Platinum's
  criffp2 meets criffp), 63, 89, 133 (the gate's steep faces). Rooms (step 4): Platinum 3,232.8 units^2 in 47 chunks, Pearl
  564.0 in 12. The largest: Veilstone Store B1F 587 (1,288, a new room), Veilstone Dept. Store 1F 248 (317), the Battle Castle
  594 (187), the Cycling Road gatehouse 283 (152), the Lost Tower 285-287 (140 each), Eterna's Route 206 gatehouse 220 (102),
  the caverns 520, 529, 538 (48.5 each), the Distortion World's floors (step 7); 13 of the 47 are on translated nodes (below),
  where the fixes judge the wrong place (`--holes --rooms` lists them).

**Material names (the land reader).** Platinum names some new materials by its exporter's default: 'file1Material' for the
palm tree3_01, 'file3Material' tree3_02, 'file4Material' the palm rows, 'a' for a shadow h_kage in Pastoria; in rooms the
Eterna Gym's 'fgds', 'qq', 's', 'ss' (trees and their shadow), the Frontier's 'lambert46-48' (bf_tree*), chairs' and
counters' shadows. Pearl always puts the texture's name in the material's, and the tools tell trees, shadows and snow from
the ground by the material's name: the palms' crowns were ground, 30-54 units over the walkable tiles under them (walls on
Route 229 and in the Fight Area), and they weren't tree cards for the layers fix. gen4_land.named_materials gives such a
material its texture's name in front ('tree3_01_file1Ma'), the dictionary written anew: 41 materials in 24 of Platinum's land
files; Pearl's land files come out byte for byte as before.

**Heights the reader missed.** gen4_land.read_bdhc_dp took a Platinum BDHC of exactly 32 points for Pearl's layout (its first
count, 0x20, is Pearl's header size) and returned nothing: Sendoff Spring 444, Route 214 152, rooms 385, 436, 468, 477 (found
by the events piece). It now falls back to Platinum's layout when Pearl's gives nothing; every other file reads as before.

**Gatehouses 2 units lower (the events piece's finding): Platinum's own floor.** Platinum rebuilt the gatehouses of slots 219
(the Route 208, 209, 213, 215 and 218 gatehouses), 220 (Eterna's Route 206 gate), 283 (the Cycling Road's) and its new 591 and
596 (the Battle Park's and Route 212's / 225's) with new textures (set 49: floor03, phouse_03, gate_exit1, ...): Pearl's carpet
strip, raised to 0, is gone and the floor is flat at -2 (Pearl's own floor level beside the carpet). Both games' BDHC say 0.
The converter puts people on the floor the model draws, as on Pearl's own -2 floor, so they stand 2 lower than in Pearl. Where
Platinum kept the floor, heights are Pearl's tile for tile: 218 (Amity Square's two gates, ROUTE_206_ETERNA_GATEHOUSE), 419,
420; 418 (Oreburgh Gate 1F) differs on 6 tiles where Platinum changed the model. (In Platinum's own game its people stand 2
units over the new floor.)

**Heights at the BDHC (2026-11-07, plat-heights; version.GROUND_AT_BDHC, Platinum only).** The converter took a tile's
highest upward-facing surface as its ground. In the Veilstone Gym that was the ceiling rails ('sen', 'lambert20', 74-77
units), over 122 walkable tiles whose floor is drawn at -2 (BDHC 0): the player would have walked on the rails.
Platinum's walker stands on its BDHC (pokeplatinum terrain_collision_manager.c GetHeight), so now the drawn surface is
the ground only where it lies within 4 units (pearl_chunk.GROUND_MATCH) of a BDHC plate there. Elsewhere
(pearl_chunk.bdhc_ground):
- over every plate (something overhead): the drawn surface nearest the highest plate that has one, else the plate. The
  Veilstone Gym's floor under the rails is -2 again, like the rest of its floor. Also the caves' new light shafts at
  their exits ('dun_light', 17 over the floor, 2 to 4 tiles in each of 30 cave chunks), the Pokémon Centers' screens and
  desks, the League lobby's walls, the Game Corner's sign, the E4 rooms' door frames, the Battle Tower's and the Battle
  Frontier's overhangs, the Survival Area house's stair, Floaroma's and Hearthome's arches, Route 212 North's fence, the
  Fight Area gate's roof.
- under every plate (the walking level not drawn): the plate. The lakes' water is a prop (l_lake) over the lake bed, so
  surfers stood 16 units under it; the lake caverns' walk-on pools are drawn 32 under the floor (they were walls); Amity
  Square's ponds, Sendoff Spring's water, Route 224's sea. Not in the Gyms (pearl_chunk.gym_chunks): there the floors
  over the model are their gimmicks' (Pastoria's water, Canalave's floors, Sunyshore's walkways, the Eterna clock).
- no plate on the tile: the nearest tiles' plates (Gen 4 keeps the height the walker came with). Fantina's tile in the
  Leader room has none, under the back wall drawn at 62: she stood on the wall. A walkable tile with no drawn surface
  and no plate takes the plane of a neighbour that is on a plate (the top of the Contest Hall's stairs was a 32-unit
  wall at 0).
- solid tiles a person stands on too (the Battle Tower's attendants, berry plants); other solid tiles keep the drawn
  surface. Not in the Underground: Gen 4 reads no heights there.
stairs_of and people_tiles (the people fix's feet) take the same rule. The layers fix is not involved: the heights read
the raw model (apicula, which applies the translated nodes), never the fixed one.
**Check: `b2tools/heights_check.py`** (new). It converts every chunk as the build does, walks every zone map with Gen
4's rules from its warps and people (the 20-unit step on the BDHC, ledges, Rock Climb, Surf), and compares each place
someone stands with the converted layer nearest that level (5 units: the match plus the plane's error). Platinum before:
3,727 places in 101 chunks (549 too high, 3,178 too low); after: 0. What is left is explained (stairs, mats, bridges,
beds, bump warps, the Gyms' moving floors, one person standing in a wall). The rule changes 9,725 tiles in 219 of
Platinum's 602 chunks (14 of them solid tiles people stand on); most are where nobody walks (the Contest Hall's seats,
the mountains). Pearl's and Diamond's 1.0 maps had the rule off; 1.0.1 turns it on (heights_check 0 for both;
notes/V1_0_1.md). Also: pearl_chunk.surface asks only the triangles whose box holds the point (an index per list), and
plane_record's lookups are cached: the same output (every Pearl chunk compared with the old code), 4-10 times faster.

**Seasons.** A texture that shares a seasonal texture's palette must be seasonal too, or the palette keeps its summer colours:
Platinum's tree04_2 shares tree01's palette, so the round trees of Pearl areas 6, 7, 8 and 15 (Twinleaf to Jubilife, Oreburgh,
Eterna and Floaroma, Canalave) and of Floaroma Meadow and the lakes stayed green in autumn and winter; the Battle Zone's palms, not listed, took the ground's colour (grey in winter).
data/texture_map.json has Platinum's seasonal textures now: tree04_2 as tree01, tree3_01 and tree3_02 as tree2_01,
conttree3_2 as conttree2_b (Pearl's sets never name them: Pearl and Diamond unchanged). `PEARL_VERSION=platinum python3
b2tools/season_grass_check.py`: 16 grass textures left in Platinum's colours (areas 6, 7, 8, 15, rooms 8 and 62) -> 0.

**Water.** The Fight Area's pools (bf_lake) take Black 2's pond water (b2_look.PEARL_WATER); their shore bf_lakep.1 stays
Platinum's, as Pearl's shores do.

**The 74 texture sets** (Pearl 58): every one used is Platinum's own. Platinum's models name Platinum's textures (criffp2,
s_snow, tree04_2, the palms, c1_lamp01, l02_base, bf_*, ...), which Pearl's sets lack (they would draw white), and the user's
rule is Platinum's art pixel for pixel. The look the user chose is not in the sets but in the layers over them, as for Pearl:
Black 2's grass and water (b2_look), the seasons' recolour (sinnoh_reskin), the Gen 4 trees and buildings (Platinum's).
| Sets | Used by | Decision |
|---|---|---|
| 6-15, 17-19 (13) | the overworld's areas (14: the north, winter all year) | Platinum's, re-skinned for the seasons; none byte-identical to Pearl's (Platinum added its new cliffs, snow and snowy tree to each and redrew 29-47 textures) |
| 8, 12, 14 | also outdoor rooms (lakes, Eterna Forest, Mt. Coronet's sides) | the same |
| 2, 5, 20-39, 41-43, 45-62, 64-73 (53) | rooms and caves only | Platinum's (step 4's pieces); 16 are byte-identical to Pearl's |
| 0, 1, 3, 4, 16, 40, 44, 63 (8) | no installed area | not installed; 5 byte-identical to Pearl's |
None stays Pearl's: where a set is identical it makes no difference, and everywhere else Pearl's would miss textures.

**Buildings.** The overworld's chunks place 36 models that differ from Pearl's: 28 retouched (houses, Centers' signs, Pastoria's
and Sunyshore's houses, the Fight Area's t6_h01) and 8 new (538 c09_s02, 544 t7_s02, 556 c11_o01, 557 t6_s01, 584 d16_o01,
585 d16_o02, 586 t7_s03, 587 d32_s06). All have resource ids and are in their areas' packs (data/platinum/sinnoh_world.json);
every building slot keeps Pearl's model name, so the fixes keyed by name (l_lake 311, the windmills, the solid pots) still
find theirs.

**Left as they are.**
- Acuity Lakefront has two new Rock Climb walls (chunk 102: (22, 14-17) N/S; chunk 103: (4-7, 8) E/W): walls by collision,
  climbed by the events' data (the events piece writes Platinum's own data/platinum/pearl_rock_climb.json).
- 0x2d FORBIDS_EXPLORATION_KIT (Eterna 44 (19, 29), Veilstone 78 (13, 17)): plain floor, as before.
- Platinum's Twinleaf path lies 3 units under its lawn edges with a backing quad under it (13 against 16): the under-floor
  copy would come within 2.25 of that quad, so it is left out there (unbacked edges 1,372 units against Pearl's 308; a crack
  there shows the quad's sand or nothing). The T-junction splits of chunk 0 are given back in both games (over 1,000
  polygons).
- The Fight Area's gate to the Battle Frontier (chunk 133): its roof overhangs the two tiles in front of its door warps,
  (14, 8) and (15, 8), 60 units over Platinum's BDHC, so they converted as a wall and the door couldn't be reached. Since
  2026-11-07 they stand on the BDHC (GROUND_AT_BDHC, "Heights at the BDHC" above). The door leads to the Frontier (step 8).
- Node translations: 43 of Platinum's land files draw shapes on translated nodes (Pearl: 2, chunks 410 and 417). On the
  overworld only chunk 71 (Route 215: one grass polygon 3 units down); the rest are rooms (gatehouses 218, 220, 283, Hearthome
  Gym rooms 478-502, ...). The heights (apicula) apply them; pearl_mesh, the fixes and the renders don't (as for Pearl's two):
  the layers fix and the under-floor judge those shapes where they aren't. For step 4's pieces.
- Hole spots the fixes open in Pearl too (cliff and slope pieces moved by the layers rule, chunk edges): the same list in
  both versions, give or take a few chunks (below).

**For the user.** (1) Platinum's snow patches show all year with seasons on, as in Platinum (its game has no seasons): on
Black 2's summer grass in summer. They could follow the seasons instead (only in autumn and winter, or only in winter).
(2) The ground rule and the under-floor's second try would help Pearl and Diamond too (the same kind of steps, Route 211 West's
line). 1.0.1 turns them on (the brief of 2026-11-07): see the end of this file.

**Tools.** `b2tools/world_look.py` (new): a place as the build installs it, from the player's camera, any season
(`sheet OUT CHUNK TX,TZ 13`: summer and winter; `top CHUNK SEASON OUT`: the chunk from above); run from an older tree (copy it
into its b2tools) for "before". Pictures of the 8 places, before (the proof's code) over after, summer and winter:
work/agents/plat-world/shots/*_before_after.png; four seasons: twinleaf_4seasons_after.png, survival_area_4seasons_after.png.
Its renderer drops polygons that reach behind the camera, so the screen's bottom row can show black specks: not the game.

**For the combined ROM (melonDS)**: the plat-world report's checklist (each place, where to stand, what to look at).

## Platinum's rooms and caves (2026-11-07; Platinum step 4, the plat-caves piece)
The fixes on shapes drawn on translated nodes (`version.NODE_SHIFT`) and six more layer rules for Platinum's rooms
(`GROUND_STAYS`, with plat-rooms' `SELF_PAIRS_STAY`): notes/PLATINUM_CAVES.md, with the holes before and after for every
room and overworld chunk. Pictures and checks now always draw a shape where the DS does (`pearl_rooms_view`, `room_look.py`,
`pearl_seams_check`). `b2tools/room_look.py` renders a room or cave as the build installs it, in any season.

## A texture with two palettes (2026-11-07; the plat-fixes piece)
sinnoh_reskin rebuilds the autumn and winter sets from the materials' (texture, palette) pairs, and it kept one palette a
texture: the first chunk's. Platinum draws some textures with a second palette in some chunks: criffp and wcliff with
criff on most routes, with criffp and wcriff on Routes 225-230 and Stark Mountain; conttree_t and _b with conttree in
Floaroma Meadow and at Lake Verity. Those palettes were missing, so the rocks and paths drew pink with white specks and
green fringes in autumn and winter (the lead's shots: work/agents/plat-caves/shots/stark_ext_14_*.png). With
`version.EVERY_PALETTE` (Platinum) every palette a chunk names goes into the set, with the season's recolour as any other
palette (nsbtx.merge adds a palette alone for it). Stark Mountain now looks as Pearl's does: its rocks, path and lava the
same all year, its grass patch the season's. Pearl's and Diamond's seasonal sets lack no palette and keep the released
way (byte for byte the same, checked for the overworld and the outdoor rooms). Check: `PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py palettes`.

## 1.0.1: the map rows for Pearl and Diamond (2026-11-07, v101-world)
`GROUND_AT_BDHC` and `GROUND_STAYS` are on for Pearl and Diamond; `SELF_PAIRS_STAY` and `NODE_SHIFT` stay Platinum's (the
first changes none of their chunks, the second fixes no hole). The numbers, the renders and the checklist: notes/V1_0_1.md
"The ground fix" and "1.0.1 checklist".
- **The holes check has a blind spot.** `pearl_seams_check --holes` draws each chunk from due south, in a parallel view, at
  59 degrees for every chunk (the rooms' camera is 53.2). A gap between two faces that the real camera sees from the side
  can be covered there by the face behind it. The Contest Hall lobby (240) scores 18 -> 0, yet `room_look.py` shows its
  back wall's two seams solid black where 1.0 has them dotted (plat-caves' sliver rule: with `EDGE_SLIVER` off they are
  dotted again). Valor Lakefront's new corner line (157) scores 0 too. Judge a layer rule by renders as well, from a few
  camera spots.
- **Platinum has the same lines**: its lobby is Pearl's model with the same rules (work/agents/v101-world/shots/
  contest_lobby_240_wall_seams.png, "Platinum now"), and its chunk 63 has the same corner (plat-caves: 5.8 -> 6.8).
- **Chunk 63's cause**, for whoever fixes the rule: the decal rule (pearl_model_fix.separate) moves a whole piece when one of
  its polygons lies under a polygon of another piece. `GROUND_STAYS` stops that only for big ground pieces (4 tiles or
  more of ground). On Route 210 North a 993-unit^2 cliff piece went back 1.32 as the decal of a 172-unit^2 shadow, once
  the sliver rule had left their sliver pair alone. Extending the guard to any bigger piece would change Platinum's
  output, so 1.0.1 doesn't. (Done later, for all three versions: the next section.)

## 1.0.1: the seams seen from the side (2026-11-07, v101-seams; all three versions)
1.0.1's ground fix (`GROUND_STAYS` with plat-caves' rules) made three places worse than 1.0 in Pearl and Diamond, and
Platinum had the same: Route 210 North's cliff corner (chunk 63), the Contest Hall lobby's back wall (240) and Valor
Lakefront's cliff corner (157). The holes check scored the first low and missed the other two.

**The check now sees from the build's own camera: `pearl_seams_check.py --holes --views`.** The old view looks along one
ray (59 degrees, due south) in a parallel view. The layers fix moves a piece along Black 2's view direction (`VIEW`, 53.2
degrees), so seen along that ray a moved piece stays where it was, and the gap it opens at its edge shows only from the
side. The DS camera is a perspective one that follows the player: a place can come to any part of the screen, where the
rays come in up to 25.8 degrees left and right and 20 up and down. So now:
- every chunk is seen along nine rays (the screen's corners, the middles of its sides, its middle) at the pitch the build
  gives its zones (maplook 'tilt': 59.06 on the overworld, each room its own Pearl camera's, 50.1 in most buildings);
- with the DS's back-face culling (every Pearl land material draws its front side only);
- a hole counts only where the camera can show it along that ray: the camera's target (the player's feet) must be within
  4 tiles of a tile the player can stand on (Pearl's collision of the chunk and its neighbours; `seen()`). Without this
  the screen's bottom rays saw the lobby's back wall from behind the wall, and Valor Lakefront's corner from inside the
  forest;
- a hole counts on the tile it is on; a chunk scores its worst ray; `--json=OUT` keeps every tile and ray;
  `--compare OLD.json NEW.json [--places]` lists the chunks worse or better by more than 1 unit^2 (4 pixels of the check,
  about one DS pixel) in the worst ray or in any one ray, and with `--places` the tiles.
The old view is unchanged; its numbers are the ones above this section. The runs: work/agents/v101-seams/tools/
(holes_run.py runs the check in any tree with a cache keyed by the models' bytes; run_all.sh in parts of under 10
minutes; place.sh renders a place in 1.0, main before and after).

**Three guards (`version.SEAM_GUARDS`, on for all three versions; pearl_model_fix's DECAL_PIECES, SLIVER_TREES and
SLOPES_HELD, under `GROUND_STAYS`).**
- **The decal rule** moves the piece of the polygon that lies wholly over or under the other. Now a bigger piece that
  faces the camera never goes as the decal of a smaller one; the smaller one moves (`GROUND_STAYS` did this for big ground
  pieces only). The lobby's back wall (1,804 units^2) went back 1.81 under the 512 units^2 band over each door: the two
  solid lines. Route 210 North's cliff (993) went back 1.32 under a 172 units^2 shadow: the corner's line. Side faces (the
  camera sees them edge-on) keep the old rule: flipped there, it also cleared Route 211 West's last short piece, but
  Veilstone Dept. Store's shelves kept more layers too close (`pearl_seams_check`'s fighting pairs: 1F 39 -> 55, 3F 4 -> 7,
  4F 4 -> 10), a flicker risk.
- **The sliver rule** (an overlap less than a unit wide along an edge stays) holds for a tree against anything that isn't
  a tree too. At Valor Lakefront a neighbour chunk's tree card overlapped the cliff's foot strip in a sliver 0.5 units wide
  (2.2 units^2), and the whole strip (993 units^2) went 3.8 back: 1.0's long line along the foot, and with the slope-follow
  rule 1.0.1's corner line.
- **A small polygon held by the floor.** When a piece moves a unit or more (`LIFT`), a small polygon that would follow one
  of its corners (`FOLLOW_SMALL`) stays where an unmoved polygon of the moved piece's plane holds that corner by an edge:
  the floor beside a lifted mat holds the wall's foot. Found by the new check: Turnback Cave's Giratina room (chunk 449),
  where the entrance mat went up 2.25 and the wall's foot beside it twisted after it (two short black marks by the
  entrance; 1.0 had none; a speck of a pixel or two is left). Smaller moves follow as before; they keep small gaps closed
  (Platinum's Route 212 South, chunk 88). A wider guard (slopes never following a decal lifted off the floor) cleared the
  entrance completely but opened Sendoff Spring's shore (chunks 443 and 444), so it was left out.

**Results** (the new check over every chunk; worst rays summed, units^2; the runs' JSON in work/agents/v101-seams/runs/):
| | 1.0 (5c90f60) | main before (5fc0d88) | after | old check: 1.0, main, after |
|---|---|---|---|---|
| Pearl, 526 chunks | 11,041.8 | 1,421.0 | 1,021.2 | 1,147.2, 272.2, 282.5 |
| Diamond, 526 chunks | 11,041.8 | | 1,021.2 | 1,147.2, -, 282.5 |
| Platinum, 602 chunks | | 2,824.5 | 2,425.2 | 559.5, 572.8 |
- Pearl after against main: 8 chunks better (Route 204 North 31, Route 210 North 63, Route 212 North 87, Route 214 154,
  Valor Lakefront 157, Route 227 171, the lobby 240, Oreburgh Gate B1F 420), none worse, no tile worse; 10 chunks' models
  change. Against 1.0: 51 better; 5 still have one ray worse, as main has them (`FOLLOW` 0.9's slopes): Route 219 8,
  Veilstone 80, Snowpoint 105, Route 225 163 (behind trees), Turnback Cave 449 (a speck): notes/V1_0_1.md.
- Diamond: Pearl's numbers chunk for chunk (its own Spear Pillar slots: 0 before and after).
- Platinum after against main: 8 better, none worse by its worst ray; one tile, Route 211 West's lower bridge corner,
  1.75 units^2 more in the middle ray (the chunk 103 -> 7.5). 12 chunks' models change.
- The old check rises by the lobby's 18 units^2 (Pearl, Diamond and Platinum): the panel over each door now moves
  forward, and from 59 degrees (the old view; the lobby's camera is 50.1, and the panels are seen from 46 degrees or less
  from any tile the player can stand on) its lower edge shows the doorway's black. No line in the renders.
- Close layers (`pearl_seams_check`'s fighting pairs, under 2 units apart: a flicker risk) on the changed chunks: Pearl
  199 -> 197, Platinum 286 -> 214. Four Pearl chunks get one pair more (a tree card left in a sliver over a cliff), and
  Platinum's Route 225 164 six (17 -> 23: a shadow chip moved instead of the palms behind it, now near the cliff and the
  bridge).

**Renders** (`world_look.py`, `room_look.py`; each picture is 1.0 | main before (5fc0d88) | after, summer, from a tile the
player can stand on; work/agents/v101-seams/shots/, made by tools/place.sh): the_three_places.png (the three, after
clean); r210n_63_*.png; contest_lobby_240_*.png (three spots); valor_lakefront_157_*.png (from the path east of the
corner, and from the forest as v101-world looked); turnback_giratina_449_*.png; and the most changed chunks: the
Underground 563, Route 227 171, Galactic HQ B2F 504, Route 211 West 47, Route 212 North 86 (two long lines in 1.0), Route
224 118, Route 214 154, Route 205 North 43, Old Chateau 2F room 3 494, Sendoff Spring 443, Oreburgh Mine B1F 313,
Snowpoint 105, Route 209 75, the League 114; and the five with a ray worse than 1.0: r8_8_24_15.png, c80_22_27.png,
snowpoint_105_27_18.png, route225_163_*.png. Platinum's: platinum_*.png (main | after). Looked at, each: after is clean or
as main, except the specks named above. Two things in every version, 1.0 too (not this piece's): a black line across the
water at Route 224's south edge and the League (118, 114, at a chunk border), and the void past the League's west edge
when the camera stands at (31, 30) of chunk 114.

`room_look.py` now draws a room at the pitch the build gives its zone (it drew every room at the template's 53.2).

## The filler's altitudes (2026-11-09; Celestic Town's south edge drew black)
Seen in 1.0.1's test (v101-fold): standing at Celestic's south edge (456-457, 539-540), the top screen's bottom 17-38
rows were black. Cause: Pearl's matrices give every cell an altitude and Pearl draws the cell's model that many
half-tiles up (pokeplatinum land_data.c LandDataManager_CalculateRenderingPosition: y = altitude * 8). Only filler
cells (no zone; Pearl's chunks 173-178) use it: 299 of matrix 0 at 1 to 26 (8 to 208 units) and the Great Marsh's 14
tree cells (matrix 240) at 2. Black 2 draws every chunk at y 0 (ov012 field_g3d_map.c), and the converter ignored the
altitudes, so every raised filler cell sat low. South of Celestic (cell (14, 17)) chunk 175 is a flat cliff-top plane,
16 above the town's ground (112) at altitude 16; at 0 the camera looked over the cliff past it onto no chunk.
The open sea (174, flat) is at altitude 1 in 98 cells: 8, the routes' own sea level; at 0 it lay a step below.
Fix: b2tools/filler_heights.py, run by pearl_paths after the paths' chunks: one copy of a chunk per altitude it is
shown at, its model moved up (19 copies, 313 cells); the Spring Path's closed cover (Pearl's code draws it at altitude
2) is raised in pearl_paths. On screen (work/agents/filler/shots): Celestic's south edge shows the cliff top, no black;
Eterna's north edge, Route 216's snowfield, Sunyshore's sea to the north and the Spring Path's cover beside Route 214
look whole. In 1.0.1 (the user, 2026-11-09: "Fold into 1.0.1").
