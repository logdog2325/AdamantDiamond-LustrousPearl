# Griseous Platinum: the day-1 audit

Written 2026-11-02, from `notes/NEXT_REGION_BRIEF.md`. The proof ROM was built with all 69 patches of the build list and played once, from the title to Twinleaf Town. The plan and the user's decisions are in `notes/PLATINUM.md`; what differs zone by zone is in `notes/PLATINUM_WORKLIST.md`. Numbers are measured from the dumps, the decomps and the proof ROM unless marked as an estimate. Pearl's finished build is the base, so "as is" means Pearl's result stands.

## The answers

### ROM space
Measured on the proof ROM: **360.0 MiB used of the cartridge's 512 MiB, 152.0 MiB free.** Pearl's 1.0 uses 359.6 MiB, so Platinum adds 0.4 MiB so far, 446 KiB of it in the sound archive. Archives keep their fixed sizes (`RESERVE` in `build_rom.py`), so growth inside one shows as a reserve filling, not as ROM size. The Distortion World's tables and the Frontier's data are small next to 152 MiB: space is not a limit.

### Zones
34 new zones (559-592), appended after Pearl's 559, whose numbers Platinum keeps.

- 30 are real: Battle Frontier 6, Distortion World 10, Regi ruins 6, Spear Pillar states 2, Global Terminal 2F and 3F, Rotom's Room, Veilstone Store B1F, Galactic HQ hall, Wi-Fi Plaza entrance.
- 4 are unused placeholders: 561, 570, 572, 578. Nothing warps there, they have no events, and they run the empty script.
- Reserved: **685-718**, one per new zone, `685 + id - 559`. No released number moves, and Pearl and Diamond don't grow their header file for them. Zone 221 (a Mount Coronet room Pearl has no warp to) takes zone 265, freed by the Battle Park's gatehouse. The Battle Park's other zones, 441 and 442, are free in Platinum.

### Trainers
- Black 2's ids 1-813, less the ones its code touches, leave 666, plus 3 (`REMATCH_EXTRA`) = 669. Pearl uses all of them.
- Platinum needs **738**: 583 battled or partner Trainers, plus rematch-only tiers (the same 240-record table, at ROM 0x1796c8), plus the 3 starters' first-battle Barrys. 69 go past 813 (to 882).
- Why it can't just grow: a defeat flag is id + 1520, so ids past 813 land on flags Pearl's registry uses.
- **Decided (the user): the flags move in code; no Trainer is cut.** `patches/platinum_trainer_flags.py`: ids past 813 use flags from 2561, which are free (79 of them). Only Platinum's build runs it, so Pearl's and Diamond's code doesn't change.
- Trainer records (a/0/9/1, a/0/9/2) are searched by file number, so they grow freely. Black 2's message table is indexed by id too.

### What Black 2 already has
| Thing | In Black 2? | Evidence | Left to do |
|---|---|---|---|
| Giratina Origin | Yes | `res/pokemon/giratina`: 2 forms; `ov167/handler_common.c:39` and `item_handlers.c` on the Griseous Orb | `SetPartyGiratinaForm` (5 uses) and the form revert commands: small |
| Griseous Orb | Yes | item 112, same number | Give it where Platinum does |
| Rotom's forms | Yes | 6 forms; `PML_PkmChangeRotomForme` (same move table as Platinum's), script `PokePartyChangeRotomForme`, Black 2's own appliance scene `global_10315` | Map Platinum's 3 commands onto it; Rotom's Room |
| Shaymin Sky, Gracidea | Yes | 2 forms; item 466, same number; `ov012/shaymin_form.c`, shortcut, `ov166/event_battle_return.c` | Nothing to port |
| Move tutors | Partly | Black 2 has tutor commands (`MoveTutorCheckParty`, `MoveTutorGetMoveID`, `MoveTutorCallPokeSelect`) and a tutor screen with its own move list and BP-style cost | Platinum's 38 shard moves, its learner bits and shard payment are data and script work; 9 commands to map |
| Griseous Orb's Giratina in Hall of Origin etc. | n/a | | Story |

### Scripts: the new commands
Platinum has **840 commands, not 839** (one constant is misspelled in its decomp's list, so the count was off). Below 0x2C3 they're Pearl's, with 3 changed layouts checked against the macros. Pearl's last 13 moved to the end of the table, under Pearl's names. The new ones are 119 net (120 rows, one filling Pearl's ScopeMode slot); 115 are used, in **324 of 55,776** places. All layouts come from Platinum's C and decode 1,122 of 1,124 files fully (25 stray bytes in 2 files).

| Group | Commands | Uses | How |
|---|---|---|---|
| Frontier | 23 | 48 | New: step 8's rules |
| Distortion World | 9 | 35 | New: step 7 |
| Tutors, shards | 9 | 26 | Maps to Black 2's tutor commands, plus a shard cost |
| Text buffers | 5 | 36 | Maps to `WordSet*`; floor number needs the same approximation as Pearl's |
| Records | 2 | 35 | Maps to Black 2's records |
| Forms, Rotom, Giratina | 8 | 30 | Maps to Black 2's form code |
| Ruins, Regigigas | 2 | 12 | Small new code or script |
| Villa, furniture, TV segments | 5 | 11 | New, small; TV segments can be dropped as Pearl's are |
| Gyms (Eterna's clock) | 2 | 6 | Gimmick, like Veilstone's |
| Amity, Scratch-off, IV judge, library, menus, save, Wi-Fi | 14 | 21 | Mostly small; Wi-Fi stays closed; scratch-off cards need a screen or a text stand-in |
| Other | 36 | 62 | One handler each, mostly a line or two |

After Pearl's handlers the generator translates 97.5% of commands (each once): see "How far each has got".

### The Distortion World (step 7: the engine built, the maps and story next)
**2026-11-07, plat-dw-core:** the engine is built and proved offline: `notes/PLATINUM_DW.md` (the tables, the rules, overlay
377, the harness: 111 routes, 19,051 frames the same as Platinum's own C; the B4F camera's sign settled). What follows is
the audit as it was.

Read from `src/overlay009/ov9_02249960.c` and its hooks, and pokebw2's field. Nothing was run. **Nothing found makes true walls impossible.**

**How Platinum does it.** There's no gravity. The player's object really moves in 3D with height calculation off; wall steps add a fixed vector per frame (`sub_02066934`). Input is remapped per face by four step tables (`player_move.c`). The camera never rolls: trigger tiles lerp yaw and pitch over 16 steps. Which face you're on comes from platform templates (bounds, kind, attr file); collision comes from `tw_arc_attr`, not the land data. Plane changes are data "jump points" (bounds, direction, displacement, rotation). The sprite rotates by a texture animation.

**How little wall there is.** Six wall or ceiling faces, all flat and axis-aligned: B1F, B2F, B3F west, B4F east and ceiling, the Turnback room east. 20 jump points, 26 camera triggers. B5F to B7F and 1F have none.

**What Black 2 assumes.** Steps on XZ and a height snap (`FldAct_MoveWPosInDir`, `CheckRecalcActorY`), though `FldAct_SetHeightCalcDisabled` already turns the snap off. Terrain sampled by XZ. A camera with pitch, yaw and zoom but no roll, which is enough because Platinum never rolls. `BlActScene_Draw` already has a per-actor rotation. All of this is in C in the decomp.

**What it takes (estimates).** A wall mode on the grid, not rails: rails can't express a vertical line (`RailMath_RailToWorldNoCurve`). A wall core of 900-1,300 lines of C, about 12 hook redirects (`PlayerMoveCollCheck`, the walk commands, `GetTileTypeAtPosByActor`), a 300-500 line converter for `tw_arc` and `tw_arc_attr`. The whole place: 6,000-8,000 lines of C plus Platinum's 4,142 lines of tables, mostly generated. First-floor prototype: B1F's one west wall, its 4 jump points and 4 camera triggers.

**Unknowns.** Whether the angles map with a sign change (B4F's camera goes past horizontal). Whether walls draw right from those angles (`FieldChunk_CheckBBox`). Two floors drawn at once (two mappers look possible; fallback, bake the next floor as props). Live floor swap in elevators. Memory.

Nothing done now blocks it: its zones are reserved, its commands decode, its data is read as it is.

### The Battle Frontier (step 8: the core built)
**2026-11-07, plat-frontier-core:** the script language read and translated, the data checked, the Tower's rules proven the
same as Platinum's on the host, the Tower on Platinum's data through its four scenes, the zones generated: notes/PLATINUM_FRONTIER.md
(with the plan for the Factory, Hall, Castle and Arcade). What follows is the audit as it was.

Read from `src/overlay104`, `res/field/frontier_scripts`, `res/trainers/frontier`. 37,644 lines of C (rules 19,666, screens 16,549, field commands 1,429), and 11,183 lines of scripts in its own language of 204 commands (169 used). `notes/PLATINUM.md` said 22,234 and 13 scripts: corrected.

| Facility | Rules | Screens Black 2 lacks | New code, estimate |
|---|---|---|---|
| Factory | rent 3 of 6, swap | Rental and swap | 600-800 rules, 150-250 with Black 2's team select |
| Hall | one Pokémon, 17 types, rank by type | Type grid | 700-900, 350-500 |
| Castle | carried HP and PP, CP spending | Both Castle screens | 700-900, 1,500-2,100 |
| Arcade | roulette, 32 effects | Roulette | 950-1,250, 350-550 |
| Tower | same as ours, new data | None | 50-150 lines |

- **Reuse from our Tower:** `battle_tower.py`, `tower_script.py`, `resident/tower.c` (`PearlB2_TowerDrawTrainerNo`, `Tower_CheckParty`, `Tower_MakePartners`), `ov012/event_bsubway.c`.
- **Reuse from HoennB2 (logic, not addresses):** its Factory's setup, party and team select, and `frontier_core`'s records; Pike's carried HP; Palace's battle hook.
- **New:** rules as host-simulated C, as Contests are; a translator of the frontier scripts' flow to field scripts; the rooms (Platinum draws them as 2D scenes, so they'd become field rooms built from its pictures, or the scene player, about 5,400 lines); Black 2's Subway plugin has 11 zone slots with 7 used, and 12 are needed.
- **Fix before it's forgotten:** `patches/battle_tower.py` reads `battle/b_tower/`, Pearl's old copy, which Platinum still carries. It needs `battle/b_pl_tower/`, 315 trainers.
- **Order:** Factory first, end to end; then Hall, Arcade, Castle. About 6,200-8,700 lines in all, 1.2-1.7 Contests (estimate).

### Gym order and chapters
Corrected in `notes/PLATINUM.md` from the scripts: Roark, Gardenia, Fantina, Maylene, Wake, Byron, Candice, Volkner. It agrees with what was written from memory.

### Pearl or Diamond, where they split
Platinum's code paths follow Diamond; its content doesn't clearly follow either (`work/platinum/base_game.py` in the main tree). Pearl stays the base by default.

| Split | Result |
|---|---|
| Wild tables (24 files, 127 fields) | Mixed: Pearl 30, Diamond 14, neither 83. Platinum's own tables replace them |
| Honey trees, swarms | Diamond's side (Pearl's labelled unused in its code): members 2, 3, 4 |
| Personal data | Platinum carries a byte-identical Diamond `personal.narc`, unused; it reads `pl_personal` |
| Summoning camera | Diamond's constants; Pearl's aren't in the binary. Our scene plays flashes, so nothing to do |
| Rival's names | Diamond's side in the dump; not shown in our intro |
| Pokédex text | Bank 616 slot holds Platinum's own; of 494 lines 277 match Diamond's and 275 Pearl's. Platinum's replaces both |
| Spear Pillar maps | Rebuilt: 39-51 tiles differ from either per chunk. Platinum's own |
| Spear Pillar scripts, 22 version lines | Platinum's own text and scripts replace them |
| Title | Platinum replaces it (draft) |
| Met game, game version | Platinum's own, 12 |
| Fossil, hideaways, Ramanas | Both, by the user's decision |

### What's left, in shares
The 60% holds, slightly better on the pipeline and slightly worse on the world. Measured against Pearl, 468 installed zones: 47 need nothing; 292 have some map difference, but 284 of the 908 land cells are only retouched terrain models; 302 have changed events; 259 changed scripts; 261 new text. Readers, generators and numbers are done ahead of the plan's share, about 3 points. The world's retouched models need converting regardless. **About 62% (judgment, plus or minus 10), still about 7 days with the Frontier.**

## How far each has got
Readable means read from the dump; generated, written by our tools; installed, in the proof ROM; seen, on screen in the one test.

| What | Readable | Generated | Installed | Seen in game |
|---|---|---|---|---|
| Zone scripts | 1,124 script files; 1,122 decode fully | 498 zones: 385 converted, 113 keep Pearl's files. 97.5% of commands translated; 1,311 stubbed (each counted once), of 381 kinds | 474 zones (107 objects left out) | 3 zones: the bedroom (Platinum's TV show; Barry comes up), 1F (Mom), Twinleaf |
| Zone text | 24,196 messages | 1,963 new lines in 261 zones | 487 text files | Intro, bedroom, 1F, Twinleaf's place name |
| Wild tables | 183 | 183 | 183, in 146 zones | None (no grass walked) |
| Trainers and teams | 928 records, equal to the decomp | 927 Trainers, 1,878 Pokémon; 738 ids allocated (69 past 813) | 670: what the installed zones and the Vs. Seeker use. 21 are past 813, on flags from 2561 | None |
| Script battles | n/a | In the 385 converted files: 119 Trainer, 16 tag, 15 wild, 21 honey tree, 3 first battles | With their zones | None |
| Doubles and partners | 28 double Trainers, 4 tag partners | Yes | With their zones | None |
| Intro | Bank 389, Buneary, both pictures | Yes | Yes | Yes: title, Rowan, Buneary, 5 questions, boy/girl choice, Barry |
| Lucas and Dawn | Overworld, fronts, backs | Yes | Yes | Overworld and intro art. Battle pictures not reached |

**What the proof showed.** Works: the title's logo and banner, Platinum's intro (Rowan, Buneary, Rowan's five questions), Platinum's Lucas and Dawn on the boy/girl choice and on the field, Barry's Platinum picture, Platinum's opening in the bedroom (the TV show, Barry running up), Mom on 1F, the stairs and the door, Twinleaf's place name. Broken: Twinleaf's one changed ground cell (the worklist's `ground_big`) shows thin black seams and white patches on the grass, so the other changed cells will too until step 3's ground piece. The title's Giratina is framed too close, its camera still to tune (the draft, as decided). Not reached: battles, wild Pokémon, the starter.

## Every patch
| Patch | What it does | Platinum | Ran in the proof build | Note |
|---|---|---|---|---|
| antipiracy | Black 2's anti-piracy reactions made harmless (battle_crash, 2026-10-13; Discord: crashes in battles, the May  | as is | yes | code only |
| battle_music | Pearl's battle music (user 2026-10-25, notes/DECISIONS.md; notes/MUSIC.md "Battle music"): the trainer eye-con | rework | yes | Pearl's themes by class; add the Frontier Brains and Platinum's songs |
| battle_tower | Pearl's Battle Tower on Black 2's Battle Subway (notes/BATTLE_ZONE.md) | rework | yes | Pearl's Tower for now, from Pearl's dump (`TOWER_DUMP` row); Platinum's `battle/b_pl_tower/`, 315 trainers, comes with the Frontier |
| boat_demos | Black 2's boat cutscenes without Unova (PearlB2, 2026-10-25: HoennB2's boats agent's patch of 2026-10-07, take | as is | yes | Unova out of the boat scenes |
| camera_switch | TEST ONLY (the camera comparison, 2026-10-25): switch a built ROM between Pearl's field cameras and Black 2's  | as is | not in the list | test only |
| capture_demo | Pearl's catching tutorial on Route 202 (Pearl StartCatchingTutorial 0x126, translated as Black 2's CallCapture | as is | yes | same tutorial; check after the chapter |
| contests | Pearl's Super Contests (notes/CONTESTS.md): they replace the Musical at Hearthome's counters, in both versions | as is | yes | Pearl's rules, screens and text (the zones' lobbies follow the worklist) |
| encounters | Assemble src/encounters/NNNN_*.s with the decomp's encounter macros and put each into a/1/2/7 as entry NNNN (s | not used | not in the list | HoennB2-era, not in the build list |
| exp_share | Gen 6 Exp | as is | yes | code; the gate's flag stays |
| fairy | The Fairy type (Gen 6 rules) and the physical/special split, HoennB2's fairy_core (2026-10-08) ported to Pearl | as is | yes | data over all species |
| fairy_ui | Fairy type: the screens and icons (HoennB2's fairy_ui, 2026-10-08; notes/FAIRY_SCOPE.md section 2, notes/FAIRY | as is | yes | screens |
| fixed_weather | Sapphire's fixed weather (data/hoenn_weather.json; user decision 2026-10-07, weather agent) | not used | not in the list | not in the build list |
| followers | The following Pokémon (user 2026-10-26: "make it a Rowan question to have them follow you all game"; plan: wor | as is | yes | its table covers every species; new forms to check |
| game_clear | Black 2's game clear for Sinnoh: the Hall of Fame's ending places, Pearl's staff credits and Sinnoh photos (ch | version row | yes | credits roll laid out for Pearl's 216 lines; Platinum has 237 |
| hm_free | HMs not required (decision 2026-10-06; notes/RESEARCH_EXPSHARE_HM.md) | not used | not in the list | not in the build list |
| hoenn_season | Hoenn has no seasons: Black 2's season is always summer | not used | not in the list | not in the build list |
| link | Link play between Pokémon Pearl NDS and the Hoenn remakes (Sapphire, Ruby and Emerald NDS): friend trades and  | version row | yes | game id for trades; decide when link is tested |
| music_choice | Rowan's music question: Sinnoh's songs or Unova's (user's choice 2026-10-18, notes/DECISIONS.md: Sinnoh's song | as is | yes | the question |
| musical | The Pokémon Musical at Hearthome's Contest Hall counters (2026-10-25, the user: "for contests use musicals"; D | not used | not in the list | replaced by contests |
| pal_park | Pal Park's migration from the GBA games and Catching Show (notes/PAL_PARK_MIGRATION.md): the data the decomp's | version row | yes | done: the bank's third-game lines |
| pastoria_gym | The Pastoria Gym's water puzzle (Pearl's Crasher Wake gym; chapter 5a, 2026-10-25) | rework | yes | check against Platinum's Pastoria Gym (worklist) |
| pearl_alt_music | Pearl's alternate zone music after story events (pokediamond arm9/src/unk_0205EC84.c sub_0205EF20, pokeplatinu | rework | yes | its flags and zones are Pearl's; Platinum has more |
| pearl_amity_sprites | Pearl's own overworld Pokémon (Amity Square, 2026-10-25; the user: "open Amity Square with the Pokémon followi | rework | yes | Amity Square has 16 people, not 25; Platinum's Pokémon list |
| pearl_centers | Sinnoh's Pokémon Centers: ONE shared 2F for all 17 (the trading floor) and the way back down to the right town | as is | yes | the shared 2F |
| pearl_defog | Pearl's fog and Defog (notes/TMS.md "Defog"; the user's choice 2026-10-18 question 9: Defog works as a field m | as is | yes | lines by bank |
| pearl_e4_doors | The Elite Four rooms' doors (chapter 8, 2026-10-26; the lead: "Pearl's 3D door objects come back, closed until | rework | yes | six League rooms changed ground |
| pearl_intro | Pearl's intro instead of Black 2's (Professor Rowan): the text is data/text_overrides/pearl_intro.json (Rowan' | version row | yes | done: Buneary from the ball; the speech is the same |
| pearl_intro_art | Pearl's people in Black 2's intro (user 2026-10-18: "use these pictures of lucas and dawn in the intro and swa | version row | yes | done: the art folder, solid crop, Rowan's members |
| pearl_npc_sprites | Pearl's own overworld sprites for people who had Black 2 stand-ins (user 2026-10-19: "give rowan his sprite an | rework | yes | Pearl's people sheets for now (Pearl's dump); Platinum's: 56 more sheets, Looker, the outfits |
| pearl_partner_backs | Pearl's battle partners seen from behind, with their own backs (user 2026-10-25: named Diamond/Pearl character | rework | yes | Platinum's partners; the counterpart Lucas and Dawn use Platinum's |
| pearl_paths | Pearl's hidden paths (the Spring Path, the Seabreak Path) as Black 2 map replacements: b2tools/pearl_hidden_pa | as is | yes | Spring and Seabreak Paths; check the worklist |
| pearl_platforms | Pearl's moving platforms (2026-10-25, the ch6a agent): the Canalave Gym's floors and 24 platforms and Iron Isl | rework | yes | Hearthome's lifts go with its new Gym; Canalave and Iron Island stay |
| pearl_player_sprites | Lucas and Dawn, Pearl's own player sprites, instead of Nate and Rosa (user 2026-10-18: "use lucass and dawns d | version row | yes | done: same members in the dump; backs from trbgra |
| pearl_pwt_frames | The PWT's Sinnoh Gym Leaders and Jasmine: no white X | as is | yes | Black 2's sheets |
| pearl_rods | Pearl's three fishing rods (user 2026-10-18: "Three real rods": Old, Good and Super Rod as in Pearl, reusing H | as is | yes | code |
| pearl_shops | Pearl's shops (notes/OPEN_CONTENT.md, b2tools/pearl_items.py reads the tables from the dump) | rework | yes | Pearl's 25 lists for now; Platinum's stock to read |
| pearl_starters | Pearl's starters on Black 2's starter screen (overlay 316, `callPoke3Select`), for Lake Verity's briefcase (no | as is | yes | same three |
| pearl_text | Pearl's script text (notes/STORY.md): src/text/script/NNNN_pearl_*.txt (written by b2tools/pearl_story.py) int | as is | yes | installs what the generator wrote |
| pearl_title | Pokémon Lustrous Pearl's title screen (notes/TITLE.md; user's choices: a Sapphire/Ruby/Emerald-style top scree | version row | yes | draft title; Giratina's camera on screen |
| pearl_tms | Pearl's TMs: TM96-TM120 for the 25 TM/HM moves of Pearl that Black 2 has no TM for, and Pearl's learners (note | rework | yes | learners from pl_personal; same TMs |
| pearl_trainer_pics | Pearl's own trainer pictures for the 46 Pearl classes Black 2 does not have (b2tools/pearl_trainer_pics.py; no | version row | yes | done: 5-file reader, verified; Frontier Brains added |
| pearl_trainers | Pearl's trainers in Black 2 (notes/TRAINERS.md "Installed"): the battled and partner trainers of the installed | version row | yes | done with ids past 813, platinum_trainer_flags |
| people_depth | People drawn into furniture: the upright depth (notes/MAP_LOOK.md "The upright depth", the decomp's src/pearlb | as is | yes | by actor |
| platinum_trainer_flags | Platinum's Trainers past Black 2's 813 (the user, 2026-11-02: the defeat flags move, no Trainer is cut; notes/ | new | yes | Platinum only: defeat flags of ids past 813 |
| poketch | Pearl's Pokétch on the bottom screen in place of the C-Gear (notes/POKETCH.md; decisions 2026-10-26) | rework | yes | Platinum's apps and art; the Calculator knows Platinum's 210 (plat-fixes: the regional dex table) |
| pwt | Black 2's Pokémon World Tournament in the Battle Park (notes/BATTLE_ZONE.md; after HoennB2's patches/pwt.py an | version row | yes | Platinum has no Battle Park (`PARK` row): the PWT's door waits for the Frontier |
| ramanas_park | Ramanas Park in Pearl's Pal Park (notes/RAMANAS_PARK.md, data/ramanas_park.json, b2tools/ramanas.py) | version row | yes | done: all 11 rooms; doors on screen |
| roamers | Pearl's roaming Pokémon, Mesprit and Cresselia, and the Trophy Garden's daily Pokémon (2026-10-26; notes/ENCOU | rework | yes | Platinum's roamers (its zone table) |
| scripts | Assemble src/field_scripts/NNNN_*.s with pokebw2's field-script macros (clang, as pokebw2's own build does) an | version row | yes | done: src/include/platinum first |
| season_choice | Rowan's seasons question (user 2026-10-19: "one Rowan question should be about whether or not you want seasons | as is | yes | question |
| season_decals | Black 2's autumn leaves and winter snow patches on Sinnoh's overworld (user 2026-10-20: "blowing autumn leaves | version row | yes | changed chunks |
| season_weather | Sinnoh's weather by season (user 2026-10-20: "snow during the winter"; notes/MAP_LOOK.md "Seasons: grass and w | version row | yes | done: Platinum's weather numbers and its day table (10 days differ) |
| secret_bases | Pearl's Secret Bases (notes/SECRET_BASES.md; decomp src/pearlb2/resident/secret_base.c) | as is | yes | Pearl's data |
| sinnoh_dex | The regional Pokédex is Pearl's Sinnoh Pokédex (2026-10-20; HoennB2's patches/hoenn_dex.py, its v15.3 hotfix,  | version row | yes | done: the dump's 210, Platinum's goal (no exclusions) |
| sinnoh_encounters | Pearl's wild Pokémon in Black 2's encounter tables (a/1/2/7) and the Sinnoh zones' headers (notes/ENCOUNTERS.m | version row | yes | done: Platinum's 183 tables |
| sinnoh_events | Every Sinnoh zone's events (a/1/2/6, appended), from Pearl's events (work/pearl/events) | as is | yes | by Pearl's numbers |
| sinnoh_music | Sinnoh's music (user's choice: Sinnoh's songs by default; the start-of-game choice of Black 2's music comes wi | rework | yes | Platinum's songs: 21 new, same converter |
| sinnoh_names | Sinnoh's place names (the banner when entering a place, the town map, the trainer card) and every Sinnoh zone' | version row | yes | new place names |
| sinnoh_pokedex | Black 2's Pokédex as Pearl's Sinnoh Pokédex (2026-10-20; HoennB2's patches/hoenn_pokedex.py ported) | rework | yes | 210 regional, Platinum's entries |
| sinnoh_reskin | Sinnoh's overworld textures and map look (notes/MAP_LOOK.md) | rework | yes | Platinum's texture sets, 74 against 58 |
| sinnoh_respawn | Where you wake up after a black-out, and where Teleport / Escape Rope's town is: Sinnoh's Pokémon Centers and  | as is | yes | Centers |
| sinnoh_rooms | Sinnoh's rooms, caves and separate outdoor maps (every Pearl zone reached through warps from the overworld; nu | as is | yes | by Pearl's numbers; new rooms take new areas |
| sinnoh_story | Pearl's story in its zones (notes/STORY.md): for every Pearl zone whose script file has been translated (src/f | as is | yes | installs what the generator wrote |
| sinnoh_world | Sinnoh's overworld as Black 2's matrix 0 (notes/WORLD.md; numbers in data/sinnoh_world.json, allocate_sinnoh.p | as is | yes | by Pearl's numbers |
| snowpoint_gym | Pearl's ice in the Snowpoint Gym (2026-10-26, the ch6b agent): the speed by the slope, the slow step back, the | rework | yes | Platinum's gym ground differs |
| sprite_switch | Birch's 4th question picks the character sprite style (user decision 2026-10-11, notes/DECISIONS.md; notes/FAI | not used | not in the list | HoennB2-era |
| sunyshore_gym | The Sunyshore Gym's gears (Pearl's Volkner gym; chapter 8, 2026-10-26) as Black 2's gimmick 62 (the decomp's s | as is | yes | check after the chapter |
| test_fairy | TEST ONLY (never in a release build): a party and wild Pokémon for checking the Fairy type in game (notes/FAIR | as is | not in the list | test |
| test_firstlight | TEST ONLY (never in a release): can Black 2 draw a Pearl map model as it is? Puts Pearl's Twinleaf model (land | as is | not in the list | test |
| test_partner_battle | TEST ONLY (never in a release build): a multi battle with a partner as soon as a test game arrives, to see the | as is | not in the list | test |
| test_story_start | TEST ONLY (never in a release build): in a STORY build (sinnoh_story), start a new game somewhere else with a  | as is | not in the list | test |
| test_team | TEST ONLY (never in a release build): a Level 100 legendary team from the start of a new game, so story tests  | as is | not in the list | test |
| test_trainer_pic | TEST ONLY (never in a release build): one converted Pearl trainer picture in a real battle (notes/TRAINERS.md  | as is | not in the list | test |
| test_twinleaf | TEST ONLY (never in a release): Twinleaf and the Route 201 chunk north of it, converted the real way, shown in | as is | not in the list | test |
| test_wildmon | TEST ONLY (never in a release build): a new game starts with a Pokémon, so wild battles can start in tests (a  | as is | not in the list | test |
| text | Rebuild the text archives (a/0/0/2 system, a/0/0/3 script messages) from the decomp's text sources with ours o | as is | not in the list | packer |
| title | Pokémon Sapphire's title screen (notes/RESEARCH_TITLE.md, option A; formats in b2tools/title_art.py) | version row | not in the list | draft; FILL to tune |
| town_map | Sinnoh town map (2026-10-20; HoennB2's town_map.py, its Hoenn town map, ported to Pearl; HoennB2 notes/TOWN_MA | version row | yes | done: tables found in overlay 80 and arm9; the Frontier in the Battle Park's place; art check |
| trade_evos | Trade evolutions made in-game (HoennB2's trade_evos, 2026-10-07; PearlB2: always on, the user 2026-10-18 and 2 | as is | yes | data |
| trainer_card | The trainer card with Pearl's player and Sinnoh's Gym Leaders (user 2026-10-20: "we need to update the trainer | version row | yes | pictures through the 5-file reader; the badge case is Pearl's art for now |
| trainers | Sapphire's trainers (converter/gen_trainers.py; notes/STORY_PORTING.md "Trainers") | not used | not in the list | HoennB2-era |
| underground | The Grand Underground (notes/UNDERGROUND.md; DECISIONS 2026-10-19, the lead's answers 2026-10-26): Pearl's Und | version row | yes | done: both columns |
| veilstone_gym | The Veilstone Gym's sliding wall panels (Pearl's Maylene gym; 2026-11-01) as Black 2's gimmick 60 (the decomp' | rework | yes | Platinum's own Gym, punching bags and tire stacks (`GYM_KIND` row): skipped until step 4 |
| vs_seeker | Pearl's Vs | version row | yes | done: table at 0x1796c8 |
| wild | Pearl's honey trees, daily swarm, Feebas and the Great Marsh's daily Pokémon (notes/ENCOUNTERS.md "Honey trees | version row | yes | done: Diamond's honey members; the new game's Berry table from overlay 57 (`INIT_TABLE` row) |
| zone_effects | Black 2's zone-keyed effects off on every zone Sinnoh uses, and its location evolutions at Pearl's places (not | version row | yes | new zones |
| zone_flags | The zone header's flags word (u16 at 0x1E) of every Sinnoh zone and room from Pearl's own map header, and the  | version row | yes | done: Platinum's header word and place names |

| HoennB2 patch we lack | What it is for | Platinum |
|---|---|---|
| area2_buildings | Exterior building pack 0 (the Hoenn overworld's one pack, area 2) and its texture set (a/1/7/4 entry 0) | covered by sinnoh_world |
| berries | Berry planting (user goal 2026-10-18; notes/BERRY_PLANTING.md): Gen 3's berry trees (pokeemerald / pokeruby sr | Gen 3 trees; Pearl has its own (pearl_events) |
| boulder_1x1 | Hoenn's Strength boulder: one tile, like Sapphire's (caves_east, 2026-10-06; notes/CAVES.md "Strength boulders | P: pearl_npc_sprites |
| centers | Pokémon Center respawn records (centers agent): Black 2's ov012 RESPAWN_ZONE_INFO for Hoenn's Centers | P: sinnoh_respawn |
| dive | Dive in Hoenn (dive agent, 2026-10-06; notes/DIVE.md) | not in Sinnoh |
| emerald_mech | Pokémon Emerald NDS mechanics (emerald_mech, 2026-10-12; notes/EMERALD.md "Phase 4") | not for this region |
| emerald_postgame | Pokémon Emerald NDS post-game: the abnormal weather's look (emerald_ch12_13, 2026-10-12; notes/EMERALD_STORY.m | not for this region |
| emerald_rayquaza_scene | Emerald's Rayquaza cutscene (emerald_art, 2026-10-12; notes/EMERALD_STORY.md section 8) | not for this region |
| emerald_rematch | Pokémon Emerald NDS: Emerald's rematches (emerald_rematch, 2026-10-18; notes/EMERALD_REMATCH.md) | P: vs_seeker |
| encounter_rules | Encounter rate rules for Hoenn (decision 2026-10-06; notes/RESEARCH_ENCOUNTERS.md) | P: sinnoh_encounters |
| escape_rope | Escape Rope and Dig in Hoenn: remember the exit when you walk from Hoenn's outdoors into a cave or building (D | P: overworld on matrix 0 |
| feebas | Route 119's Feebas (user 2026-11-01; gen_docs' wild pages say it): the fishing spots were never built, so Feeb | P: wild |
| frontier_area | The Frontier code area (frontier_palace_arena, 2026-10-12; notes/FRONTIER.md "Code space"): a shared helper fo | reference for step 8 |
| frontier_core | The Battle Frontier's shared systems (frontier_core, 2026-10-12; notes/FRONTIER.md) | reference for step 8 |
| frontier_factory_dome | Pokémon Emerald NDS: the Battle Factory and the Battle Dome (frontier_factory_dome, 2026-10-12; notes/FRONTIER | reference: Factory (step 8) |
| frontier_palace_arena | The Battle Palace and the Battle Arena (frontier_palace_arena, 2026-10-12; notes/FRONTIER_PALACE_ARENA.md) | reference: battle hooks (step 8) |
| frontier_pike | Emerald's Battle Pike (frontier_pike, 2026-10-12; notes/FRONTIER_PIKE.md) | reference: carried HP (step 8) |
| frontier_pyramid | Emerald's Battle Pyramid (frontier_pyramid, 2026-10-12; notes/FRONTIER_PYRAMID.md) | not for this region |
| hoenn_dex | The regional Pokédex is Hoenn's (dex_fix, 2026-10-08; v15.3 hotfix) | P: sinnoh_dex |
| hoenn_intro | Sapphire's intro instead of Black 2's (user request 2026-10-06: "cut out the black 2 intro, it's jarring") | P: pearl_intro |
| hoenn_music | Hoenn's soundtrack on Black 2's instruments, chosen in the intro: Birch's third question, Hoenn or Unova music | P: music_choice |
| hoenn_pokedex | Black 2's Pokédex as Sapphire's / Ruby's Hoenn Pokédex (hoenn_pokedex, v16; notes/POKEDEX.md) | P: sinnoh_pokedex |
| hoenn_textures | Hoenn's map texture set: Black 2's area 2 summer set (a/0/1/4 entry 3, the one our terrain was built from) plu | P: sinnoh_reskin |
| hoenn_world | Install the Hoenn overworld built by b2tools/world.py (work/world/): chunks appended to a/0/0/8 from first_chu | P: sinnoh_world |
| interiors | Install interior zones from data/interiors/<zone>.json (notes/INTERIORS.md) | P: sinnoh_rooms |
| met_names | Met locations above Black 2's 154 place names: Pokémon traded from Pokémon Pearl NDS (the sister project Pearl | P: sinnoh_names; Platinum's new places need rows |
| new_tms | Real TMs for the Gen 3 TM moves Black 2 has no TM for (new_tms, 2026-10-18; notes/RESUME.md item 16) | P: pearl_tms |
| npc_check | Build step: the people-sprite budget of every Hoenn zone (b2tools/npc_check.py, notes/NPC_LIMIT.md) | P: b2tools/npc_check.py |
| objects3d | Sapphire's large objects as Black 2 3D field objects (missing_objects, 2026-10-08; b2tools/models_objects.py) | not needed so far; check Platinum's props |
| opening | Sapphire's opening (notes/OPENING.md): a new game starts in the moving truck instead of Aspertia City | P: newgame.inc |
| pokenav | The PokéNav's data (notes/POKENAV.md): its code is C in the decomp (src/hoennb2/pokenav/, overlay 345, and src | not for this region |
| rods | The Old Rod and the Good Rod (rods_fix, 2026-10-12; Discord bug report: the Old Rod has no Use or Register opt | P: pearl_rods |
| rotating_gates | Gen 3's rotating gates (th_p6, 2026-10-19; notes/TRICK_HOUSE.md "P6"): Trick House Puzzle 6, faithful per vers | not for this region |
| save_compat | PKHeX-compatible Emerald saves (save_compat, 2026-10-18; notes/SAVE_PKHEX.md) | not asked |
| secret_bases_late | Secret Bases: gimmick 30 in the base zones (a/1/0/2 file 0: u32 zone, u32 gimmick pairs), which loads overlay  | P: secret_bases |
| shops | Sapphire's Poké Mart item lists (data/hoenn_shops.json, made by b2tools/shops_data.py) into Black 2's shop lis | P: pearl_shops |
| special_zones | Black 2 code and tables that name Unova zone ids which Hoenn's maps and rooms now use (special_zones, 2026-10- | P: zone_effects |
| sprites | Install the edited character sprites in src/sprites/ (formats: b2tools/sprites.py) | P: pearl_player_sprites |
| standalone | Hoenn's warp-only outdoor maps (b2tools/world.py build_standalone, data/hoenn_standalone.json), after hoenn_wo | P: sinnoh_rooms |
| starters | Hoenn's starters on Black 2's starter screen (overlay 316, `callPoke3Select`) | P: pearl_starters |
| story | Story objects of the chapter agents (notes/STORY_PORTING.md "Story objects"): NPCs, signs and step triggers th | P: generator |
| test_cave_kit | TEST ONLY (caves_east, 2026-10-06): a field-move kit for cave tests | test |
| test_chunk0_roundtrip | TEST ONLY: Nuvema's terrain (chunk 0 model) replaced by the same terrain re-written through apicula (DAE) and  | test |
| test_door_to_nuvema | TEST ONLY: the player's front-door mat in Aspertia (zone 428, warp 0) leads to Nuvema Town (zone 389) instead, | test |
| test_music_kit | TEST ONLY: the music test kit (music_check, notes/MUSIC.md "Tests") | test |
| test_sweep_kit | TEST ONLY (sweep_caves, 2026-10-07): test_cave_kit's field-move kit WITHOUT replacing Littleroot's other scrip | test |
| test_trade_evos | TEST ONLY (trade_evos agent): Littleroot's town sign (stand at (183,366), face north) gives, with an empty par | test |
| trades | The version's in-game trades on Black 2's own in-game trade system (chapter Ch1 wrote it for Rustboro's trade) | needed: Platinum's in-game trades (InitNPCTrade is a stub) |
| trainer_hill | Emerald's Trainer Hill (battle_tents, 2026-10-18; notes/BATTLE_TENTS.md) | not for this region |
| weather | Kyogre's weather (chapter Ch10, ch10 agent 2026-10-07; src/field_scripts/common/legendary_weather.inc has the  | not for this region |

## The brief's inventory
Status for Platinum, with Pearl's work as the base. "Done" means inherited or generated and read by the build; only the items in the proof have been seen on screen.

### World and maps
| Item | Status |
|---|---|
| Zone headers | Done by `sinnoh_world`, `sinnoh_rooms`, for shared and new zones |
| Header flags word | Done: `zone_flags` with Platinum's word, Distortion World's background needs a Black 2 one (to do) |
| Other header words | Done by the same |
| Zone-keyed effects | Inherited; new zones to check (to do) |
| Code naming Unova zones | Inherited; new zones take 685+, which no code names |
| Escape Rope, Dig | Inherited |
| Texture look and seasons | To do: Platinum has 74 sets against 58 (`sinnoh_reskin`), step 3 |
| Seasonal weather | Inherited |
| Lighting | Inherited; new rooms to check |
| Geometry | Inherited; changed cells to check |
| Stairs, warp rules | Inherited; `warp_check` to run on Platinum |
| Doors | Inherited; new doors to do |
| Signs | Inherited |
| People in furniture | Inherited; 302 zones' events to check |

### People and objects
| Item | Status |
|---|---|
| Player: overworld, battle back, intro | Platinum's own: done for the proof. Trainer card avatars, icons: to do (`trainer_card`) |
| Rival, counterpart, professor, mom | Rowan done (same picture). Barry through the new reader. Others to check (`pearl_npc_sprites`) |
| Object stand-ins | Inherited |
| Villain team | Inherited (Pearl's own pictures through the reader) |
| 32 sprites per zone | `npc_check` to run |
| Placeholder frames | Inherited |
| Generic stand-ins | Inherited; 56 new sheets to map |
| Field objects | Inherited |
| Strength boulders | Inherited; `boulder_check` to run |
| Trainer classes, pictures | Done: 50 pictures; the 4 Frontier Brains on frame 0 |
| Large 3D objects | Not applicable so far |

### Menus and apps
| Item | Status |
|---|---|
| Regional Pokédex list | Done: the dump's 210 (crash avoided by construction); check on screen |
| Pokédex text, area, habitat | Done offline (2026-11-07, plat-dex): Platinum's entries, areas with its special lists; check on screen |
| Town Map | Tables read; art check to do |
| Trainer Card | Reader done; to do on screen |
| C-Gear -> Pokétch | Inherited; Platinum's apps to do |
| Met locations | New place names to do |
| Bag, Exp. Share | Inherited |
| Title, intro, questions | Intro done; title draft |
| Hall of Fame, game clear | Inherited; credits layout to do |
| Unova-only features | Inherited decisions |

### Battles, Pokémon and items
Trainers: generated, with teams and AI from the dump; encounter tables: generated (183); rods, TMs: inherited with Platinum's learners to do; Poké Mart stock: Platinum's own tables (plat-fixes); roamers: to do; in-game trades: to do; Fairy: inherited; catching tutorial: inherited.

### Story systems
Generator, `scene_check`, `warp_check`, `test_story_start`, `story_play`: inherited and read Platinum's numbers. To run on Platinum chapter by chapter.

### Sound and text
Music: Pearl's songs by zone; Platinum's 21 songs and changed zones to do. Text: read from Platinum's bank with Pearl's edits following by words; 0 of Pearl's edits failed to find their line.

### Save and link
Save: a new version, no Pearl save to carry. Link: `link` patch's game id to decide when tested.

## The new Lucas and Dawn
| What Black 2 draws | Comes from | Note |
|---|---|---|
| Overworld (walk, run, bike, surf, ball, fish, save, Pokétch, Center) | `data/mmodel/mmodel.narc` 90-93, 155-156, 159-160, 166-167, 363-368 | Same members and frame shape as Pearl's, so the same map onto Black 2's nine sheets. Pixel for pixel, 1 row down as Pearl's |
| Battle fronts | `trfgra.narc` member 5c + 0..3 | Frame: the cell the first animation starts on. Verified: 92 classes equal the decomp's PNG directly, 12 after placing the cell by its OAM offsets; Castle Valet's overlapping OAMs are the one left unchecked |
| Battle backs | `trbgra.narc` backs 0, 1 | 5 of 8 cells (0, 1, 2, 3, 7) because Black 2's 256 x 128 texture holds five; 4-6 are the arm settling, a few pixels off 3. Ball leaves at tick 40, so the wind-up keeps its proportions in 40 ticks instead of 60 |
| Animated fronts | Frame 0 now (decided) | 25 classes animate. Black 2 can take it through its parts texture; later |
| Intro | `art_sources/intro/platinum/` | Row in `pearl_intro_art`; the build stops if missing |

**The art's fit.** Lucas 360 x 620 has a faint halo: visible 260 x 562. As Pearl's code crops by any alpha he'd be 124 x 213 with 89 x 193 visible. With solid crop and the 212 cap: **98 x 212**. Dawn 1200 x 1888: **124 x 195**, width-limited by the pointing arm. Ratio 0.92, Pearl's pair 0.925.

**Intro pictures against Pearl's** (`demo/intro/intro.narc`, 50 members against 48): Rowan's picture and colours identical at 19/20. Differ: background tiles and palettes, small walking frames, Barry's picture, and members 42-44, 46-48. Black 2's intro draws only Rowan and the rival from this archive, so its backgrounds are Black 2's in every version. The dump's are used where the intro shows them.

## The intro against Pearl's
| Part | Result |
|---|---|
| Rowan's speech | Bank 389 against Pearl's 341: 45 lines, all equal except 3 rival-name choices, which our intro doesn't offer |
| Order of steps | The same: hello, music starts, name, info, inhabited, Poké Ball, the Pokémon, alongside, about you, boy or girl, name, friend, farewell |
| The Pokémon from the ball | **Buneary** (Pearl: Munchlax): `pearl_intro` row, sprite and cry |
| Music | `SEQ_OPENING` in both |
| Pictures | As above |
| TV screen after it | Both dumps have one (`ov59_TV`, `tv_app.c`) with different text. Pearl's build doesn't show it; so not in Platinum's either |
| New game | Same flow: the bedroom's TV report, Barry, Mom. Platinum's flags from its own script (`InitNewGame`) |
| First battle | Barry on Route 201 by the starter (ids 850-852, Lv 5), not wild Starly: `pl_StartFirstTrainerBattle`, with Pearl's first-battle rules |
| Opening zones | Twinleaf: ground changed; 4 of 15 lines new. 2F: 1 line. Route 201: 54 of 63 lines new. Lake Verity: 7 of 12. All from Platinum's scripts |

## Steps 2-6 as pieces agents can take in parallel
Each piece starts from `notes/PLATINUM_WORKLIST.md` and `data/platinum/worklist.json`, works offline in its own tree, and merges for one combined test (the user's rule). Sizes are measured; times aren't given. Pieces in the same step don't touch the same files unless the row says so.

### Step 2: dialogue
| Piece | Size | Files |
|---|---|---|
| Zone text check: 1,963 new lines in 261 zones already generate; check widths, speakers, buffers, codes with no Black 2 equal | 261 zones | `gen4_text.py`, `pearl_story.py` text path, `data/pearl_speakers.json` |
| System text: items (3 new), place names, Pokédex categories, Trainer names and classes | banks 392, 556, 558-559 slots | `sinnoh_names.py`, `data/text_overrides/`, `pearl_trainers.py` |

#### Step 2 done (2026-11-02, the plat-text tree)
The check is `PEARL_VERSION=platinum python3 b2tools/text_check.py [--scripts] [--speakers]` (its docstring has the
rules). It translates every installed zone (451; the Frontier's and the Distortion World's are left as generated) and
checks every line: 17,502 lines, 7,479 of them not in Pearl's files. Result: 0 problems. 46 buffer gaps are Pearl's
own (the same lines in Pearl's 1.0 build), listed by the check and below.
- **Widths.** No line is wider than Black 2's own widest row (224 px), with every buffer at its longest value. The
  windows show 232 px; the sign window 223. No page has more than 2 rows. No message passes 1,280 characters.
- **Codes.** Every Gen 4 code has a Black 2 one, or a reason it goes: `{SIZE}` (big letters: normal size), the yes/no
  icon, `{WAIT}` (a sound cue: the scripts play the sound). Buffer kinds Black 2 lacks become kind 0100, which Black 2's
  field text treats the same.
- **The 22 version lines.** Spear Pillar, Sandgem, Rowan's lab, Eterna and Cynthia's grandparents come from Platinum's
  own scripts, so they show Platinum's text. Spear Pillar's one version test takes Platinum's line (version 12).
- **System text.** Items 465-467 and the Griseous Orb: Black 2's names and descriptions equal Platinum's. Pokédex
  categories: Platinum's equal Pearl's. Trainers: names from Platinum's dump; 1,958 messages fit (battle lines 240 px).
  Class names stay as Pearl's build shows them; Platinum's new classes are the Maid (Black 2 has it) and the Frontier
  Brains (step 8).

Lines fixed by hand, and why:
| Where | What | Why |
|---|---|---|
| `data/platinum/pearl_text_edits.json` | Solaceon Ruins B1F 0-2, Solaceon Center 2, Solaceon 2, Oreburgh Gate 0: "Hidden Machine" -> "Technical Machine" | The user's TM rule (notes/TMS.md): Defog and Rock Smash are TMs here. Platinum moved Defog to Solaceon and rewrote the Gate line, so Pearl's edits found no line |
| same | Sandgem, Rowan's lab (bank 496: 2, 16): "every kind" -> "so many kinds" | The National Pokédex at Champion; Platinum rewrote the line's end |
| `data/platinum/pearl_buffer_fills.json` | Canalave line 1: the rival's name filled before the line | Gen 4 kept the name from his battle script; Black 2 starts each script with empty words. Pearl's 1.0 shows ": Yeah, yeah..." here |
| `data/platinum/pearl_speakers.json` | 18 zones' rows | Pearl's rows moved to Platinum's lines and objects; new rows where a talk script goes on after its person leaves (Route 201's starter scene, Valor Lakefront, Veilstone, Route 213) or another person speaks (Snowpoint, the Mansion, Galactic HQ); the Villa's two-speaker lines in the plain window |
| `data/text_overrides/platinum/town_map.json` | 7 Town Map lines | 6 Platinum rewrote; 1 loses its last line break |

Rules added (Platinum only; Pearl's and Diamond's output unchanged): a message's last line break goes (9 lines showed an
empty third row); a speaker not installed yet (Looker) uses the plain window; new buffer commands: the Hidden Power
type (`CalcHiddenPowerType`, `BufferTypeName`: Black 2's own commands), a Trainer's name and the Villa's prices
written into the line (Black 2 has no word for a Trainer, and its numbers stop at 65,535), the elevators' floor (for a
window Black 2 lacks). Place names: Platinum's own (Cafe -> Café) and its 14 new sections on lines 266-279; line 265
stays the Grand Underground's (notes/LINK.md needs the new lines for HoennB2).

Pearl's own gaps, left as in 1.0 (buffers of features Black 2 lacks, or filled by an earlier script in Gen 4), in 13
zones: the Union Room groups (Jublife), Jublife Condominiums 4F's first line, the TV's PC nickname (Jublife TV 1F),
the appearance lady (Oreburgh Center), the move deleter's move name (Canalave), the Underground Man's goods (Eterna),
the Contest Hall's entry number (Hearthome), the trendy saying (Snowpoint), Julia's stories and ribbon (Sunyshore),
the size contest (Route 222), the Pal Park gate's game names and record holder (Route 221), the Day Care's level line
and the seal house (Solaceon).

### Step 3: towns and routes
| Piece | Size | Files |
|---|---|---|
| Overworld ground: Route 212 south, Route 229, Route 230, Acuity Lakefront, Twinleaf, Fight, Survival, Resort Areas: 13 big and about 50 small cells | 8 places | hand fixes keyed by chunk in `pearl_chunk.py`, `b2_look.py`, `pearl_seams_check.py` |
| Texture sets: 74 against Pearl's 58, 284 cells with retouched models | all areas | `sinnoh_reskin.py`, `maplook.py`, `data/texture_map.json` |
| Town events and signs: 302 zones changed events; doors, signs, people depth | outdoors first | `pearl_events.py`, `pearl_doors.py`, `pearl_signs.py`, `data/people_depth.json` |

### Step 4: rooms, Gyms and caves
| Piece | Size | Files |
|---|---|---|
| Hearthome Gym (rebuilt) | 15 big cells | `pearl_platforms.py` (its lifts go), new gimmick if the quiz doors need one |
| Eterna Gym with its clock; Galactic building, 4 floors; Rotom's Room | 6 big, 2 commands | gimmick like `veilstone_gym.py`, `sinnoh_rooms` |
| Veilstone Gym: Platinum's own, punching bags and tire stacks (pokeplatinum `overlay008/gym_features.c`); the build skips Pearl's panels by the `GYM_KIND` row | 1 big, 1 gimmick | `pearl_veilstone_gym.py`, `patches/veilstone_gym.py`, decomp `resident/veilstone_gym.c` |
| Snowpoint Gym's changed ground | 1 big | `snowpoint_gym.py` |
| Pokémon League: 6 rooms, Hall of Fame | 6 big | `pearl_e4_doors.py`, `game_clear.py` |
| Great Marsh, 6 pieces; Amity Square, 4 pieces | 10 big | `wild.py`, `pearl_amity_sprites.py` |
| Spear Pillar's 2 new states and 2 rebuilt; Stark Mountain; lake caverns | 8 big | scene work in `pearl_story.py` |
| Regi ruins 6, Veilstone B1F, HQ hall, Global Terminal floors | 10 new zones | `allocate_sinnoh.py` rows are in; `ActivateRegiRuinsDot` |
| Villa (3 to 17 objects) and furniture | 5 commands | new small script code |

### Step 5: chapter by chapter
One agent a chapter, Platinum's order (notes/PLATINUM.md). Each takes its zones' scripts (259 changed), wild tables (146 differ) and Trainers, with a test start. Chapters' zone lists need redoing in `data/story_chapters.json` first, by one agent. Across chapters:

| Piece | Size | Files |
|---|---|---|
| Trainer flags past 813 and their battles | 69 ids | `platinum_trainer_flags.py`, `pearl_trainers.py` |
| Double battles (28, Pearl 23) and tag battles (4, Pearl 3) | 6 new | `pearl_story.py`, trainer data |
| Stubbed commands: 1,311 once each, of which Union Room, TV and contests are Pearl's too | `report.txt` | `pearl_story.py` |
| Tutors and shards | 9 commands, 38 moves | new handlers, `data/` table |
| Forms: Rotom, Giratina, Shaymin | 8 commands | handlers onto Black 2's code |
| Mart stock, in-game trades, roamers | 3 tables | `pearl_shops.py`, new trades, `roamers.py` |

### Step 6: sprites, Pokédex, music, title
| Piece | Size | Files |
|---|---|---|
| People's sheets: 56 new overworld, 74 changed | 130 sheets | `pearl_npc_sprites.py`, `data/pearl_sprite_map.json` |
| Trainer pictures: card avatars, leader pennants, animated fronts later | 25 classes animate | `trainer_card.py`, `pearl_trainer_pics.py` |
| Pokédex: 210, entries, heights and Giratina's, areas | bank slots, `zukan_enc_platinum` | `sinnoh_dex.py`, `sinnoh_pokedex.py`, `town_map.py` |
| Music: 21 songs, 3 zones' themes, battle themes for the Brains | same converter | `sinnoh_music.py`, `battle_music.py`, `pearl_alt_music.py` |
| Title and credits | draft, 237 lines | `title_lustrous.py`, `pearl_title.py`, `pearl_credits.py` |

#### Step 6: the Pokédex done (2026-11-07, the plat-dex tree)
The check is `PEARL_VERSION=platinum python3 b2tools/platinum_dex_check.py` (its docstring has the rules). It runs the
patches' own functions on scratch copies. Result: ok.
- **The list.** The dump's 210 in pokeplatinum's order, Victini the hidden #000, every other species 999. "Complete" is
  all 210 seen, as Platinum's LOCAL_DEX_GOAL (nothing excluded).
- **The text.** Platinum's own entries (slot 616 = its TEXT_BANK_SPECIES_POKEDEX_ENTRY_EN): 219 species differ from the
  shared files, in `data/text_overrides/platinum/pokedex.json` (`PEARL_VERSION=platinum python3
  b2tools/patches/sinnoh_pokedex.py --text`). Every alternate form shows its species' entry, as Platinum's one entry.
  Categories, heights and weights equal Black 2's. Giratina: Platinum's base banks hold the Origin Forme's numbers and
  slots 714/715 the Altered Forme's; they equal Black 2's form 1 and base. All 493 fit the entry window (3 rows, the
  widest 192 px of 222).
- **The areas.** The AREA page shows the wild tables' places (as Pearl's build), plus Platinum's "special" lists before
  the National Pokédex: honey trees, the Great Marsh's daily Pokémon, Feebas (`sinnoh_pokedex.AREA_SPECIAL`, a version
  row; Pearl and Diamond off). The result equals Platinum's own lists, but for Hippopotas: the Maniac Tunnel shows on
  Route 214 (Pearl's build the same). Not shown: the places Platinum adds with the National Pokédex (the Trophy Garden,
  the Great Marsh after it, three more; 55 species), since Black 2's area data has one table for both modes. The
  HABITAT list keeps the wild tables only (a/2/9/6 has no room for the specials).
- **The National Pokédex.** Rowan's lab gives it after the Hall of Fame, as Pearl's build.
- **Open, outside this piece.** The professors' ratings (Rowan's lab and the PC) use Pearl's tiers and line numbers:
  Platinum's Rowan has 12 tiers up to 210 on lines 6-17, its Oak the same tiers as Pearl's on lines 22-42
  (`pearl_story.py` h_dex_rating, `pearl_story.inc` pl_LoadPokedexRating*, `src/field_scripts/1260`, text 1051). The
  Pokétch Calculator knows Sinnoh numbers 1-151 only (`include/pearlb2/poketch.h` PEARLB2_SINNOH_DEX_ENTRIES 152,
  `patches/poketch.py`). Diamond's 1.0 shows Pearl's 156 differing entries: there is no
  `data/text_overrides/diamond/pokedex.json` (`PEARL_VERSION=diamond python3 b2tools/patches/sinnoh_pokedex.py --text`
  would make it).

#### plat-fixes (2026-11-07, the plat-fixes tree)
The check is `PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py` (ratings, poketch, marts; its docstring
has the rules). Result: ok.
- **The ratings.** Platinum's Rowan has 12 tiers up to 210 seen, nothing left out of the count (lines 6-17; all 210:
  line 4 after the first visit to Eterna, else 5); its Oak has Pearl's tiers on lines 22-42; the PC's lines are 43 and
  44 (`version.DEX_RATING`, `pearl_story.inc` pl_LoadPokedexRatingLocalPlatinum, `src/field_scripts/platinum/1260_*.s`,
  `src/text/script/platinum/1051_rowan_rating.txt` = Platinum's bank 335). The check runs the macros for every count
  against pokeplatinum's C, and checks every call's lines against the bank.
- **The Calculator.** It reads the regional dex table (a/0/1/6 file 709, which sinnoh_dex writes per version) up to
  the config's count (151, Platinum's 210). Decomp branch `pearlb2-plat-fixes`: `calculator.c`, `poketch.h`.
- **The seasons' palettes.** sinnoh_reskin kept one palette a texture when it rebuilt the autumn and winter sets. Platinum
  draws criffp, wcliff and conttree_t/_b with a second palette in some chunks (Routes 225-230, Stark Mountain, Floaroma
  Meadow, Lake Verity's area): those drew pink with white specks and green fringes. `version.EVERY_PALETTE` (Platinum)
  puts in every palette a chunk names. Pearl's and Diamond's sets are byte for byte the same (they have none).
- **The Marts.** Platinum's own tables from its arm9: the badge list and lists 0-18 equal Pearl's; list 19 is new
  (Veilstone Dept. Store B1F's berries, list file 25). Its TMs had wrong prices (Pearl's item table read Platinum's item
  data: TM38 cost 2,000): now Platinum's (its own table, found in its arm9). All 74 items sold cost what Platinum asks.
