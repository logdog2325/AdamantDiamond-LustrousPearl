# Platinum's people's sheets (step 6, the sprites piece)

Written 2026-11-07 by the plat-sprites piece. Offline only. What needs a ROM is in "For the combined ROM" below.
The code: `b2tools/patches/pearl_npc_sprites.py` (PLATINUM_PEOPLE, PLATINUM_MODELS, PLATINUM_REDRAWN), the codes:
`data/platinum/sprite_map.json`. The check and the pictures: `PEARL_VERSION=platinum python3 b2tools/plat_sprites_check.py`.

## What Platinum has against Pearl
- Platinum's `mmodel.narc` members 0-375 are Pearl's byte for byte, except the player's sheets and four people Platinum
  redrew: Barry (127), Palmer (148), Buneary (373), Happiny (374). Platinum moved the models after 375 (Pearl 376-413 are
  Platinum 421-...); the ones this build uses (the snowball, the League doors) are the same bytes.
- Its new sheets: Looker, Charon, the five Frontier Brains, the nine starters, Croagunk, Giratina's Origin Forme, five
  attendants, an unused Pikachu, Rotom's five appliances, the game director, five plain appliances nobody shows, the
  two grunt crowds, the two cave-painting shards, the player's Vs. Seeker and Distortion World sheets.
- Its new models: the book (fldeff 79, Pearl's too), the wall before Rotom's Room (fldeff 149), the crowds' and shards'
  billboard models (mmodel 441-445).

## What each got (Platinum build only)
| Graphics | Who | Code | From Platinum | Where (zones) |
|---|---|---|---|---|
| 148 | Barry | 291 (Pearl's) | mmodel 127, redrawn | 26 zones |
| 169 | Palmer | 207 (Pearl's) | mmodel 148, redrawn | Fight Area |
| 206 | Buneary | 363 (Pearl's) | mmodel 373, redrawn (pearl_amity_sprites) | 6 zones |
| 207 | Happiny | 376 (Pearl's) | mmodel 374, redrawn (pearl_amity_sprites) | Amity Square, Celestic |
| 213 | Looker | 317 | mmodel 376 'icpo' | 12 zones |
| 214 | Charon | 318 | mmodel 377 'gkanbu4' | 4 zones |
| 229 | Croagunk | 319 | mmodel 392 'gureggru' | Pastoria, Stark Mountain |
| 231 | Frontier attendant (singles) | 205 | mmodel 394 'bfsm' | Battle Tower lobby, the Frontier's halls |
| 232 | Frontier attendant (multis) | 132 | mmodel 395 'bfsw1' | the same |
| 233 | Frontier attendant (booths) | 151 | mmodel 396 'bfsw2' | the Frontier, its gate |
| 235 | Wi-Fi Plaza attendant | 322 | mmodel 398 'wifisf' | every Center B1F, Tower lobby, Plaza entrance |
| 237-241 | Rotom's oven, fan, fridge, washer, mower | 115, 116, 117, 125, 126 | mmodel 400-404 | Rotom's Room |
| 242 | game director | 320 | mmodel 405 'director' | Hotel Grand Lake, west room |
| 215-218 | Thorton, Argenta, Darach, Dahlia (plat-frontier-rooms) | 113, 114, 120, 124 | mmodel 378-381 'brains1'-'brains4' | the Factory's, Hall's, Castle's and Arcade's scenes (a var holds the look) |
| 219 | Caitlin (plat-frontier-rooms) | 209 | mmodel 382 'princess' | the Castle's corridor scene (its object 5) |
| 248 | grunt crowd (4) | 0x2000 (model) | mmodel 441 and its picture 411 | Galactic HQ hall |
| 249 | grunt crowd (3) | 0x2001 (model) | mmodel 444 and its picture 412 | Galactic HQ hall |
| 250 | cave-painting shards | 0x2006 (model) | mmodel 442 + 443 as one model | Mt. Coronet 2F |
| 251 | cave-painting shards (right) | 185 (invisible blocker) | drawn by 250's model | Mt. Coronet 2F |
| 183 | book | 0x2008 (model) | fldeff 79 'book02' | 7 books in 6 zones |
| 262 | wall before Rotom's Room | 0x2007 (model) | fldeff 149 | Eterna Galactic building 1F |

- People: 16 frames each, as Pearl's. Black 2's 12-frame walker takes frames 0, 1 and 3 of each way, 1 row lower (Black
  2's feet are on row 30). Platinum's 16 colours. Barry keeps Hugh's 17-frame layout (5 standing frames at the end).
- Rotom's appliances are Platinum's red appliance sheets, the ones its Rotom's Room shows. The grey ones (406-410) are
  unused in Platinum. All 16 frames are one picture.
- The codes: 317-322 are ordinary walkers nobody uses. 115-117, 125, 126, 132, 151 and 205 are 12-frame sheets whose
  record drew them as turning or rail figures (scene node 5 or 15). They get an ordinary walker's record (code 317's),
  with their own sheet. No kept Black 2 zone, script, table or C names any of them (`--codes`).
- Models: Black 2's 3D-model actors draw a model at the actor's place, as Platinum draws its 3D objects. Each gets code
  0x2007's record (a 1 x 1 drawn model; `pearl_e4_doors` copies it too) and its own model file. 0x2007 itself only
  changes its model file. 0x2000, 0x2001, 0x2006, 0x2007 and 0x2008 are free (0x2002 is the League doors, 0x2003-0x2005
  are Strength boulders, 0x2009 and 0x200A belong to kept Black 2 zones).
- Pearl's and Diamond's builds are unchanged: their a/0/4/7 and a/0/4/8 are byte for byte as before (`--versions`).

## What differs from Platinum, and why
- **The grunt crowds' size.** Platinum draws the crowd at 1 unit per pixel, as all its people. Black 2 draws people at 28
  units per 32 pixels. As one picture the crowd's grunts would be a seventh taller and wider than the single grunts
  standing among them. So each grunt of the picture gets its own quad at Black 2's person size, on its own tile. The
  picture, its texture, the model's billboard command and its material are Platinum's. The grunts touch at one column;
  that column goes to the grunt drawn in it. In the crowd of 4, one pixel of the woman on tile 0 belongs to the man
  next to her, so it is drawn with him, 2 pixels over (`hq_hall.png` shows both builds side by side).
- **The shards are one model.** Platinum has two objects, two tiles apart, each with half of one picture lying on the
  floor. They share one flag and one script. Black 2 has only five free model codes, so the left object draws both
  halves where Platinum draws them. The right object is Black 2's invisible blocker (185), solid and talkable.
- **No shadow under the shards.** Platinum draws one; Black 2's model actors have none. The crowds and the book have none
  in Platinum either.
- **The book is Platinum only.** Pearl's and Diamond's builds still leave their two books out (their output may not
  change). The same model would show them there too.
- **The Hearthome Gym's candle sprite.** There is none. Platinum's 210 and 211 are the player's own walking sheets; the
  candle is the light. The Gym table's slot stays 0 (the player keeps their sprite). Platinum also draws the player
  there without fog. Black 2 has no per-person switch for that; it would be C in the Gym code (plat-gyms' piece).

## Not converted, and why
- Caitlin (219, the Castle's corridor scene): code 209, mmodel 382 'princess' (plat-frontier-rooms). The four Brains (215-218)
  took codes 113, 114, 120 and 124 (plat-frontier-rooms, 2026-11-07); five free 12-frame codes are left: 315, 323, 324, 349, 369.
- Giratina's Origin Forme (230), the Distortion World's player and lake trio ids (258-271): step 7.
- The Wi-Fi Plaza attendant (M) 234, the unused Pikachu 236, the plain appliances 243-247: no zone uses them.
- The player's Vs. Seeker poses (256, 257) and the Diamond/Pearl player sheets (252-255, link play): player sheets,
  left alone as the brief says.

## Checked offline
- `plat_sprites_check.py`: 165 checks. Every Black 2 frame is its Platinum frame, 1 row lower; Platinum's colours;
  nothing cut off; each code and sheet its own; each record an ordinary walker; each model file Platinum's (the book,
  the wall byte for byte; the crowds and shards: Platinum's texture, node and material, the quads checked).
- `--zones`: every installed zone stays under Black 2's limits. The busiest: Battle Frontier 21 different sprites,
  Fight Area 19, Pastoria 18, Union Room and Route 209 17. The most people: Union Room 51 (limit 64).
- `platinum_events.py`: 0 problems, 0 sprites waiting. New notes: two books stand on table tiles (Galactic HQ 2F,
  Route 208's house), as in Platinum.
- `frame_check.py` (Platinum): no case on the new codes. Its 6 cases are the Resort Area's PWT leaders (codes 277-282),
  from before this piece.
- `version_check.py`: ok.

## For the combined ROM
Each line: what to look at, the zone (Black 2 zone), the tile, and what must be clear for it to show.
- Looker: Jublife (6) tile (186, 756), hide flag 385; Eterna Galactic building 1F (106) (14, 15), flag 443. Walk next to
  him: no wrong frame in any direction.
- Charon: Valley Windworks inside (271) (21, 5), flag 421; Galactic HQ 4F back (507) (7, 6), flag 670.
- Croagunk: Pastoria (113) (611, 821), flag 669.
- Frontier attendants and the Wi-Fi attendant: Battle Tower lobby (443) tiles (15, 5), (11, 5), (19, 5); any Center B1F
  (e.g. Jublife's, 581) (4, 4).
- The game director: Hotel Grand Lake west room (450) (5, 3).
- Rotom's Room (697): the five appliances at (4..12, 6), flags 699-703; the two books at (11, 9) and (13, 5).
- The book: Jublife Trainer School (43) (4, 9). It should lie flat on the table top, 14 units up. Talking to it should
  read it (it was left out before).
- The wall before Rotom's Room: Eterna Galactic building 1F (106) (1, 5), flag 710. It should fill the passage and look
  like the room's wall, with no gap or floating edge. Using the Secret Key removes it.
- The cave-painting shards: Mt. Coronet 2F (275) (6, 24) and (8, 24), flag 386 (shown after the lake trio are freed).
  One picture of rubble on the floor, centred under the painting's place (7, 23). Both halves talkable.
- The Galactic HQ hall (695), flag 601 clear (Cyrus's speech): every grunt the same size, groups and singles alike, feet
  in one line in each row, all facing the camera while it moves. If the groups stand 1-3 pixels higher or lower than
  the single grunts, PERSON_BOTTOM in pearl_npc_sprites is the number to change. Also look at the lighting: the
  crowds are models, the singles billboards.
- Barry, Palmer, Buneary, Happiny: Platinum's new art in Twinleaf (Barry), the Fight Area
  (Palmer), Hearthome (Buneary), Amity Square (Happiny, Buneary walking with the player).
- The Hearthome Gym: is the player darkened by the Gym's fog? Platinum draws the player bright there.
- `npc_check.py ROM --zone` for Battle Frontier, Fight Area, Pastoria and Union Room: texture memory (offline only
  the sheets are counted: Battle Frontier's sheets are 94 KB).

## Fan art (the user's rule, 2026-11-03)
Searched 2026-11-07, nothing downloaded. The list is in the piece's report for the user to decide. Found: two Gen 5-style
Looker recolours by SnakeMasterz (free to use, credit asked) and tebited15's Gen 5-style Barry walking sheet (free use,
Diamond/Pearl outfit). Nothing Gen 5-style for Charon, Palmer, the attendants, the director or the objects.
