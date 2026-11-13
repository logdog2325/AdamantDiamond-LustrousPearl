# Platinum's Battle Frontier (step 8)

Started 2026-11-07 with the core (plat-frontier-core). This note is the Frontier's home: what is built, how it runs, how it is
checked, and the plan for the four facilities. The brief is work/agents/FRONTIER_BRIEF.md; the audit's numbers are in
notes/PORT_AUDIT.md "The Battle Frontier".

## What the core is
- The Frontier's script language, read and translated into Black 2 field scripts.
- The shared records, the BP, the Exchange Service Corner.
- The Frontier's zones, the gate and the Tower's lobby, generated and checked.
- The Battle Tower on Platinum's own data, running end to end through its scenes.

Status: everything below runs offline. Nothing was built or played: the lead tests it on the combined ROM (the checklist at the
end). The new C (`plat_frontier.c`) is written and type-checked but not compiled for the DS; **the Tower doesn't need it**.

## The script language
Platinum runs the Frontier's battle rooms as 2D scenes (overlay 104), with their own scripts: 204 commands
(`include/data/scripts/frscrcmd.h`), 174 of them used in the reachable code (the audit counted 169).

`b2tools/frontier_script.py` reads them from the dump (`frontier/script/fr_script.narc`, 11 files):
- the command table comes from the decomp's macros (`asm/macros/frscrcmd.inc`), cached in `b2tools/data/frontier_script_cmds.json`;
- a file is entry offsets ended by 0xFD13, then commands (u16 opcode, u8/u16/s32 arguments) and data lists, each ended by 0xFD13:
  movement lists, objects' pictures (FrontierScrCmd_22), objects placed (FrontierScrCmd_24: local id, look, direction, pixel x
  and y, drawn), door sprites (2A, 2C);
- `check`: every file decodes fully (code, data, the compiler's leftover End after a GoTo, alignment); the 6,919 commands equal the
  decomp's sources in order, and every `_XXXX` label of the sources sits at its address. The two unused files equal the
  decomp's binaries byte for byte.

## How a scene runs here
`b2tools/frontier_translate.py` turns each scene script into a **Platinum field-script file**, command for command, using the
field commands Platinum's own field scripts use for the same jobs. pearl_story then translates that file like any other
Platinum script (its block "plat-frontier"). So messages, menus, the Tower's functions, fades, sounds, saves and movements
go through the handlers that already work for the rest of Platinum.

- **Host rooms.** A scene runs in a field room, as scripts of that zone's file. The Tower's four scenes run in the rooms Platinum
  still carries from Pearl (our zones 617-620; HOSTS in frontier_translate.py). Each room says where the scene's pixel grid sits
  on its tiles, which room person stands for each scene object, which people take their look from a var, and where its doors
  are. The origins were found from the rooms' own people, who stand where the scenes draw them.
- **Staging.** A placement row becomes SetPosition and Show or Hide on the room's person. A look held in a var is copied into
  the person's VAR_OBJ_GFX_ID first. Movement lists convert code for code; WarpIn and WarpOut are SetVisible and SetInvisible.
  Door sprites become the room's door animations.
- **Starting, changing and ending.** Platinum's `LaunchBattleFrontierScene` warps to the scene's room with RTReserveScript, as
  Gen 4's Warp is translated. In a scene file the same opcode carries markers: ChangeScript (warp to the next room, at an entry),
  ChangeSceneWithinScript (the script goes on in the new room), ExitFrontier (back to the field script that started the chain,
  after its ReturnToField). Each room gets one entry per place a scene starts there, after its other extra entries.
- **ExitFrontier.** The code after the starting field script's ReturnToField is copied into the room as `FrontierReturn_k`.
  With one live starting place it is a plain jump. With more, the start sets a return site and the exit asks for it
  (`pl_FrontierSetReturn`, `pl_FrontierGetReturn`: the C core). The Tower's Wi-Fi start is closed (CLOSED_SITES), so each
  Tower room has one, and no C is needed.
- **ExitFrontier in a picture room** (plat-frontier-flow, 2026-11-08). Platinum's picture scenes run over the lobby's field, so
  their `FrontierReturn_k` is a fade-in that must run in the lobby: in a picture room FrontierExit fades out, reserves
  `FrontierReturn_k` (an entry of the lobby's file, key ('return', k)) and warps to the tile in front of the lobby's attendant,
  facing it (`_fr_lobby_place`: Platinum's WalkBackInvisibly* puts the player back there before LaunchBattleFrontierScene). The
  lobby's own frame scripts (the challenge's end, "We hope to see you again") run after it. A Multi challenge's attendant stands
  beside, so its player would come back one tile off (the wireless Multi is closed). The Tower keeps its rooms' copy: its
  code has Platinum's own Warp to the lobby. Before this, a retire, a loss or the 7-win end left the player in the room.
- **A scene change inside a subroutine** (plat-frontier-flow, 2026-11-08). Platinum keeps the script's call frames over
  ChangeSceneWithinScript, so a subroutine that changes the scene returns to its caller in the new room; ours ends the script
  at the warp. So a subroutine with a within change (`_fr_wsubs`, through the subroutines it calls) is translated once per
  call stack (`FrTr` units `FrCall_<file>_<sub>_<return addresses>`), each copy's change reserves its own continuation
  (`FrontierWithin_<file>_<addr>_<return addresses>`, keys ('within', file, addr, ctx) from `_fr_contexts`), and that
  continuation's Return jumps to the caller's code from the return address, translated in the new room too
  (`FrRet_<file>_<addr>`); a Call made there goes to a copy of its own (`FrSub_`), so the callee's Return stays a Return.
  Only the Factory's and the Castle's after-battle subroutines (both results) have one. Before this, the player stood free in
  the corridor after every Factory and Castle battle.
- **Vars.** 0x8000-0x800C keep their numbers. 0x800D-0x8013 become works 0x8058-0x805E (`FR_VAR_800D`.., pearl_story.inc). A var
  that holds a local id for ApplyMovement gets the room's object ids.
- **Frame tables.** A host room's own frame table (the scripts Pearl's rooms ran) is dropped in Platinum (pearl_events'
  "plat-frontier" block): the scenes start from the warp's reserved script. Its zone-init and resume scripts stay (the
  stand-in's look, the player hidden).

What each command becomes is printed by `python3 b2tools/frontier_translate.py report`. For the Tower's four scenes:

| Platinum | Here | Why |
|---|---|---|
| FrontierScrCmd_22, 23, 2A, 2B, 2C, 2F | nothing | pictures and door sprites: the room's people and doors are on the map |
| FrontierScrCmd_70 + its question | the answer is No | the Vs. Recorder: not in Black 2 here (as the Battle Video machines) |
| FrontierScrCmd_71, 6D | 0 | the same |
| InitNewBattleRecording, FreeBattleRecording | nothing | the same |
| FrontierScrCmd_3F | nothing | the battle's transition and song: the Subway's battle start plays its own |
| PlayFrontierBrainEncounterEffect | nothing | Palmer's cut-in: Black 2 has no such screen (approximation) |
| FrontierScrCmd_85 | PrintBattleTowerIntroMessage | the opponent's line |
| FrontierScrCmd_72, 73 | TrySaveGame | the save |
| BattleTower_StartBattle | CallBattleTowerFunction 42 | the field's battle (Black 2's Subway battle) |
| ShowYesNoMenu (cursor on No) | Black 2's yes/no menu | its cursor starts on Yes (approximation) |
| Wireless-only commands | nothing | the wireless Multi is closed |

## Data
`b2tools/platinum_frontier_data.py check` reads everything from the dump and checks it against the decomp:
- 315 Frontier Trainers (`battle/b_pl_tower/pl_btdtr.narc`) and 951 sets (`pl_btdpm.narc`) equal `res/trainers/frontier`.
  A Trainer's count leaves out a final set 0, the decomp's padding row.
- Names (Platinum's bank 21, slot 16) and three lines each (bank 614, slot 684).
- The Tower's room ranges, the class-to-sprite table, the two Exchange counters and their BP prices, found in the dump's code
  by their bytes.

**Platinum's Tower rules equal Pearl's**: the same room ranges, the same Palmer ids (305, 306), the same BP awards (3, 3, 4, 4,
5, 5, 7; Palmer 20), the same IV steps, the same partners in the same order (300-304), the same 41 prizes at the same prices.
So PearlB2's Tower code already does Platinum's rules; only the Trainers, their sets, names and lines change.

## The harness
`b2tools/platinum_frontier_host/run.sh` (via `b2tools/platinum_frontier_check.py`) compiles Platinum's own Tower C (copied from
pokeplatinum by extract.py) next to the code the ROM runs (PearlB2's `PearlB2_TowerDrawTrainerNo`, Black 2's round draw, BP,
team picks and IVs, copied from pokebw2). Both take their random numbers from Platinum's challenge generator, seeded the same.

Result with 1,000 seeds: 30,000 rounds (280,000 opponents: single, double, multi, rooms 0-9) drawn the same; 80 BP awards the
same (1-20 rounds won, each mode, with and without Palmer); the IVs of 400 Trainer ids the same; 92,700 teams picked the same
(the sets, the 50-try item rule, the team's trainer id). Both use the same random numbers in the same count.

One difference that stays: on the DS, Black 2's own generator gives the numbers, not Platinum's per-challenge seed. The rules
are the same; the stream isn't kept between challenges as Platinum's is.

## The Battle Tower
- `patches/battle_tower.py`: Platinum's own Trainers 0-306 (the Tower's: 300, the partners, Palmer's two teams), sets, names
  and lines. 307-314 are the other facilities' Brains: their Black 2 classes and sprites come with their pieces.
- Its zones: the lobby (443), elevator (616), the four rooms (617-620) and the salon (621), generated from Platinum's scripts and
  the four scenes. The elevator starts the corridor scene; the corridor changes to the battle room; the battle room's exit warps
  to the lobby in front of the right attendant (Platinum's (15, 6) or (11, 6)).
- `tower_script.py`: Platinum's lobby positions for a saved challenge (Platinum only); Tower functions 53, 58 and 59 (53: the
  chosen slot, asked only to revert a form, and Giratina and Shaymin are banned from the Subway; 58 and 59 set fields nothing
  reads).

## BP and the Exchange Service Corner
BP is Black 2's Subway purse, as in Pearl's Tower. `patches/platinum_frontier.py` (Platinum's build list, after battle_tower)
puts Platinum's two counters on Black 2's BP shop screen: the right counter's 15 TMs (shop 253), the left counter's 26 items
(shop 254), at Platinum's BP prices. Black 2's own BP lists are the PWT's, whose Battle Park Platinum doesn't have.
`PokeMartFrontier` becomes `pl_PokeMartFrontier` (pearl_story.inc).

## The core's C (not compiled yet)
Disk was under 3 GB, so there is no decomp tree for this piece. The C is in this repo as text, mirroring the decomp's paths:
`src/pokebw2/include/pearlb2/plat_frontier.h`, `src/pokebw2/src/pearlb2/resident/plat_frontier.c`, and changed copies of
`tower.h` and `tower.c` (one enum row, one switch case). Copy `src/pokebw2/` over a decomp tree to use it. Both files pass
clang's syntax and type check against the decomp's own headers (`compile_flags.txt`, GNU C); they were not built with mwcc.

- **The command.** Sub-command 0x93 of the Tower's row (`EXT_TOWER_FRONTIER`), then an op byte, then its arguments. Ops 0x00-0x1F
  the core; 0x20, 0x40, 0x60, 0x80 the Factory, Hall, Castle and Arcade. `b2_script_check.py` knows the core's ops.
- **The core's ops.** 0x00 set the return site, 0x01 get it; 0x02-0x05 the records (get, set, add up to 9,999, keep the best);
  0x06 a facility's streak flag; 0x07 keep or give back a scene manager var over a scene change.
- **The records.** Platinum's own BattleFrontierStats (112 u16, its ids). Ids 0-9 (the Tower) read Black 2's Subway records.
- **The save.** Save block 0x3A's Wi-Fi Subway players (7 x 240 B), read only by the closed Wi-Fi train and the Wi-Fi download
  app (notes/DATA.md registry). Magic 'FRNT', the records, the streak flags, then 1,444 B for each facility's challenge saved
  part-way (Platinum's union).

## Checks
- `python3 b2tools/platinum_frontier_check.py`: the language, the data, the harness. All pass.
- `PEARL_VERSION=platinum python3 b2tools/pearl_story.py zones` for the 14 zones (the Tower's 7, the Frontier's 6, the Fight Area):
  every file assembles and passes b2_script_check at its levels.
- `python3 b2tools/version_check.py`: ok (Pearl and Diamond unchanged).

## For the combined ROM
Build Platinum with `platinum_frontier` after `battle_tower` in its list. No new C is needed for these.
1. Fight Area (448), the gate's door at (654-655, 423): walk in under the roof overhang, into the gate (686).
2. The gate: talk to the receptionist; the menu's Battle Points line explains BP. Walk out to the Frontier (685).
3. The Frontier (685): the Exchange Service Corner. The right counter lists 15 TMs (TM06 Toxic 32 BP .. TM26 Earthquake 80 BP),
   the left 26 items (Protein 1 BP .. Rare Candy 48 BP). Buy one: the BP drop by the price. The BP window shows the right count.
4. The Tower's lobby (443) from the Frontier: Platinum's people, the single attendant at (15, 5), the multi at (11, 5).
5. A Single challenge: pick three, save, the elevator (616) rides up.
6. The corridor (617): the door at (2, 2) opens, the attendant walks out (2, 1) -> (2, 4), the player follows to (2, 3), both
   walk to one of four doors and vanish, the screen fades. Look for anyone standing in the doorway before the door opens.
7. The battle room (619): the player's stand-in walks from (7, 10) to (4, 6); the opponent walks in from (7, 3) to (10, 6),
   says the line, the two step together, the battle starts with Platinum's Trainers (names and lines are Platinum's).
8. After a win: the heal, the menu (continue, rest, retire). Seven wins: the BP line and the fanfare (3 BP for the first room).
9. Rest: the save, the reset; Continue in the lobby in front of the single attendant; the challenge resumes.
10. A loss or retire: back to the lobby at (15, 6) facing the attendant.
11. A Multi challenge: the salon (621), a partner, the multi corridor (618) with both doors, the multi battle room (620).
12. Room 3's seventh battle in Single: Palmer (Silver), 20 BP.

## Not done the way Platinum does it
- The Vs. Recorder: not asked, nothing recorded (Black 2's recorder isn't wired here).
- Palmer's cut-in before the battle: Black 2 has no such screen; the Subway's transition plays.
- Platinum's yes/no menus that start on No start on Yes.
- The random numbers come from Black 2's generator, not Platinum's per-challenge seed (the rules are proven the same).
- The records board (`OpenFrontierRecordsApp`): Black 2 has no such screen. Since plat-records (2026-11-08) the Tower's,
  Factory's, Castle's and Arcade's machines show their records as messages ("The Frontier's records machines", below);
  the Hall's is still a stub (its species list answers EXIT).
- The Brains of the other facilities (307-314) aren't installed: they need Black 2 classes and sprites (their pieces).
- The Frontier's reporter, the scratch-off cards and TV interviews stay stubs, as in the rest of Platinum.

## The Battle Factory (plat-factory, 2026-11-07)
Rent three of six, swap one after each win, seven battles a round, Thorton at the 21st and 49th Single battles. Status: the
rules run offline and are proven the same as Platinum's; the game side is C as text, linked as overlay 378 since
plat-frontier-rooms, which also built the rooms, the scene's translation and Thorton ("The picture rooms"). Nothing of it was
played.

### The rules (proven)
`src/pokebw2/src/pearlb2/plat_factory/factory_rules.c` (include/pearlb2/plat_factory.h) is Platinum's own, function for
function: battle_factory.c, battle_factory_helpers.c, frontier_opponents.c (sets made into Pokémon), CallBattleFactoryFunction,
DeleteActiveBattleFactoryStreak, and the records of battle_frontier_stats.c and battle_frontier_save.c. It covers:
- the round's 14 Trainers by round (Thorton: Silver at the 21st, Gold at the 49th Single battle, Frontier Trainers 309, 310);
- the six rentals by round and trade count (the last ones from the next pool after 7, 14, 21, 28, 35 swaps), Level 50 and
  Open Level (its own pools; Lv. 100), the last two moved to random places;
- each opponent's Pokémon (none of the species or items of either party), their IVs by the Trainer's pool;
- each Pokémon as Platinum makes it: trainer id, a personality of the set's nature that isn't shiny, EVs 510 / flags (255
  at most), ability by the personality's low bit, Frustration's friendship;
- the swap (the beaten opponent's Pokémon into the player's slot, the trade count), the streak and battle counts, the round's
  end (records, the streak flag, the next round), a loss, the save before a rest and the challenge resumed from it;
- the Battle Points (5, 5, 5, 5, 7, 7, 8, 9 by round; Thorton's battles 20), the AI flags by round, the hints (the opponent's
  species and moves, the most common type).
Random numbers: Platinum's LCRNG on the challenge's own state (seeded from Black 2's at the start). The draws Platinum makes
when it turns a set into a Pokémon at its level (a trainer id that isn't shiny, random IVs it then overwrites) are made too,
in the same places, so every number after them is Platinum's.

**The harness.** `b2tools/platinum_factory_host/run.sh` (step 4 of `platinum_frontier_check.py`) compiles Platinum's own C,
copied word for word from pokeplatinum by `extract.py`, beside factory_rules.c as the overlay has it. Both draw from the same
LCRNG state; after every step the state must be the same too. Result, 300 seeds: 12,000 rounds started (Single and Double,
Level 50 and Open, rounds 0-9, trade counts across every upgrade step), 58,564 battles, 31,688 swaps, 511 Thorton battles,
3,868 rests resumed, 8,350 losses, 26,098,473 checks, 0 different. Battle Points seen: 5, 7, 8, 9 and 20. Mutations (a pool's
range, the trainer id's draw order, Thorton's 20 BP, a skipped swap of the rentals, the IV draws, the record's rule) are all
caught. The common type is checked in Platinum's numbers and in Black 2's (no Mystery type: the same type wins).

### The game side (C as text, not compiled)
- **Overlay 378** (`src/pearlb2/plat_factory/factory.c`), at Pal Park's address like 376: the resident
  `PearlB2_Frontier_Factory` (`resident/plat_factory_ext.c`, the core's Factory row in plat_frontier.c) loads it for one op
  and unloads it. An op that runs a screen or the battle gives the script an event of Black 2's own (overlay 12), whose data
  is in the challenge's work or on the event heap. Claim: `link_overlays.py` needs `PLATFACTORY = 378` at Pal Park's address
  (AFTER(PKTMEM)) with src/pearlb2/plat_factory/*.c, and `pearlb2_overlays.py` its id (LAST 378).
- **The ops** (notes/EXT_COMMAND.md, pearl_story.inc `pl_Factory*`, b2_script_check knows them): init, the round,
  CallBattleFactoryFunction, the rental screen and result, the swap screens and results, the picked rentals into the party, the
  next opponent, the swap, the next party, the battle and after it, won, the Trainer's line, free, the streak deletion.
- **The screens: Black 2's battle-entry party screen** (EventBtlInstPokeSelect_Create, the Subway's and Trial House's), no new
  screen. Rental: the six rentals as a party at the challenge's level, three to pick; its summary pages show moves, ability and
  item. Swap: two screens, the player's three (one to give, B for none), then the beaten opponent's three (one to take).
  Their regulations are two new files of a/1/0/6 (`patches/platinum_factory.py`: Black 2's file 20 with the counts, no level
  rule, no clause, nothing banned).
- **The battle**: Black 2's Trial House battle (SetupTrialHouseBattle) with the three rentals against the Factory Trainer
  (name, class and line from the Subway's Trainer archive, which holds Platinum's Frontier Trainers), his Pokémon as the rules
  made them; Open Level makes both parties again at Lv. 100 (the Trial House sets 50); Platinum's AI flags by round; the
  Brain's song from the build's table (`gPlatFactoryTable.brainBgm`).
- **The save**: the challenge's work (Platinum's BattleFactorySave first, 88 B, then the running challenge: 896 B of the 1,444 B)
  in the core save's challenge area; the records are the core's Platinum stats (ids 10-33) and streak flags (facility 0).
- Checked: the four C files (factory.c, factory_rules.c, plat_factory_ext.c, plat_frontier.c) pass clang's GNU C type check
  against the decomp's headers with -Wall (`compile_flags.txt` plus `-std=gnu99 -D__thumb -I<tree>/src/pokebw2/include
  -DPEARLB2=1`). The regulations: `python3 b2tools/patches/platinum_factory.py` builds both from Black 2's own arc.

### Built since (plat-frontier-rooms, 2026-11-07)
- The rooms, the scene's translation, Thorton and the link of overlay 378: "The picture rooms" below.
- **Not as Platinum, by design:** the rental screen can be left with B (the script opens it again); the swap is two screens;
  the opponent's line is Black 2's balloon; the rentals' Original Trainer and met place are Black 2's facility Pokémon's;
  Platinum's swap record (RECORD_BATTLE_FACTORY_TRADES) has no Black 2 counterpart; the multi challenges are closed (as the
  Tower's); the corridor's moving floor and the battle room's colour changes are picture effects (functions 30-32) with no
  field equivalent.

### For the combined ROM (once the rooms and scenes are in)
1. Enter: the Frontier (685), the Factory's door at (77, 34-35): the lobby (688), the single attendant; Level 50 and Open
   Level are offered; the save; the walk north into the corridor.
2. Renting: the corridor's attendant line, then Black 2's party screen with six rentals at Lv. 50 (Open: Lv. 100). Their
   summaries show Platinum's sets. Pick three and confirm; B brings the screen back.
3. A battle: the battle room, the opponent walks in, his line in a balloon, a Single battle with the three rentals (Lv. 50
   both sides), his Pokémon none of the rentals' species or items.
4. A swap: after a win the hint (species, moves or common type by round), "swap?", Yes: the player's three (pick one), the
   beaten opponent's three (pick one); the next battle's party has it. No or B: no swap.
5. A 7-win streak: the 7th win, the BP line and fanfare: 5 BP for round 1 (Single or Double); the lobby; the record and
   streak flag kept (Continue: round 2's rentals are from the second pool).
6. Thorton: Single, 21st battle (round 3's last): the "Factory Head" scene (his walk, the particles have no field form), his
   class and picture, Platinum's Silver team at the round's pool, 20 BP; Gold at the 49th.
7. Rest after a win: the save, the reset, Continue in the lobby: the challenge resumes at the next battle with the same party.
8. A loss: back to the lobby, the streak ended (the records keep the best).

## The plan for the four facilities
Each piece adds its row of Frontier ops (0x20 Factory, 0x40 Hall, 0x60 Castle, 0x80 Arcade), its host rooms in HOSTS, its
facility commands in frontier_translate.py, and its rules as host-tested C in its own overlay (the resident pool is nearly full).
Numbers below are what `frontier_translate.py report` still lists for each script.

| Piece | Script | Commands left (uses) | Rooms Black 2 needs | Rules to prove |
|---|---|---|---|---|
| plat-factory | factory, 999 commands | 28 kinds (167): CallBattleFactoryFunction 99, BufferSpeciesName 12, BufferMoveName 5 | corridor and battle room (frontier_bg pictures as field rooms), the rental and swap screens (Black 2's team select where it fits) | the rentals for a seed, the swaps, the opponents' teams |
| plat-hall | hall, 864 commands | 26 kinds (140): CallBattleHallFunction 57, particles 36 | corridor and battle room, the 17-type grid | the type grid's ranks, the opponents by type and rank |
| plat-castle | castle, 1,263 commands | 26 kinds (151): CallBattleCastleFunction 100 | corridor, battle room, scene 13, its two screens | CP costs and awards, carried HP and PP |
| plat-arcade | arcade, 2,196 commands | 26 kinds (346): CallBattleArcadeFunction 246, SetItemDrawFlag 32, particles 19 | corridor and battle room, the roulette | the roulette table and its 32 effects |

Shared work for them, in this order:
1. **Host rooms.** None of the four has a field room. Build each from Platinum's own pictures (`resource/eng/frontier_graphic/
   frontier_bg.narc`) as a field room, or play the scene on the scene player. Then add its HOSTS row (origin, objects, doors,
   arrival) and check the staging with scene_check.
2. **Each facility's function command** (Call...Function fn, arg1, arg2, var) as one Frontier op that switches on fn, as
   tower_script.py maps the Tower's.
3. **Particles** (Hall and Arcade): Black 2's field effects or nothing; list the choice.
4. **The Brains**: their Black 2 classes (ask the lead for ids), the 10 free walker codes (notes/PLATINUM_SPRITES.md), their
   battle themes (plat-music's note), then their Trainers 307-314 into a/2/1/2.
5. **Records**: the facilities write Platinum's stats through ops 0x02-0x05 and streak flags through 0x06; the lobby's
   `Delete...Streak` commands clear a flag.
6. **The records board** (`OpenFrontierRecordsApp`): a text stand-in from the records, or a screen. Done as messages
   (plat-records, "The Frontier's records machines"), the Hall's left out.

Pieces can start after the core is merged. Up to three can run at a time; they share only frontier_translate.py's HOSTS and the
op rows, so each adds its own rows.

## The Battle Hall (plat-hall, 2026-11-07)
One Pokémon (two of the same species in a Double), the 17-type grid, a rank of 1-10 for each type, opponents drawn by type and
rank, their level from the player's, the streak, BP, and Argenta at the 50th and 170th battle of a Single streak.

### What is built, and where
- **The rules**: `src/pokebw2/src/pearlb2/plat_hall/hall_rules.c` (decomp path `src/pearlb2/plat_hall/`), header
  `src/pokebw2/include/pearlb2/plat_hall.h`. Platinum's `battle_hall.c`, `battle_hall_helpers.c`, `battle_hall_save.c`,
  `battle_hall_win_records.c` and `frontier_opponents.c`, step for step, with Platinum's LCRNG (one per challenge, seeded once
  from Black 2's generator). It needs nothing of Black 2, so the harness compiles it as it is.
- **The tables**: `gPlatHallTable` (11,280 B), made by `b2tools/platinum_hall_data.py` from the dump: the 478 Hall sets
  (`battle/b_pl_stage/pl_bsdpm.narc`), the 477 opponents and their two types, the class tables by rank (10 x 8) and by type
  (18 x 4), the classes of Frontier Trainers 0-299, each set's two abilities (by species and form), and which Trainers' names
  start with I or J (below). Each code table is found in the dump by its bytes (overlay 104 is stored uncompressed).
  `patches/platinum_hall.py` writes it into the overlay's .data (Platinum's build list, after platinum_frontier).
- **The field side**: `plat_hall/hall_field.c`: the ops, the save, the party, the battle, the type list, the lobby.
- **The overlay**: 379 (`PLATHALL`; 378 is left for plat-factory), at Black 2's gimmick overlays' address. The op loads it,
  runs, unloads it (as plat-tutors' 376), so it costs no memory between ops. No zone of the Hall has a gimmick, so the room
  is free; if something is there, `GFL_OvlLoad` refuses and the script stops (a check for the combined ROM). Size: text
  7,270 B, rodata 104 B, data 11,300 B (mwcc's objects): it ends near 0x021F3700, below overlay 377's end (0x021F53E0).
- **The resident side**: `resident/plat_hall_ext.c` (96 B of code, one pointer): the core's row for the Hall
  (`plat_frontier.c sFacilityOps[1] = PearlB2_Ext_Hall`), and the battle's setup kept between the start and the cleanup.
- **The work**: `PlatHallWork` (Platinum's BattleHall struct, what the rules use, plus its BattleHallSave) lives in the core's
  challenge union (`PearlB2FrontierSave.challenge`), so it survives the overlay's unloading and the warps between rooms.

### The ops (sub-command 0x93, op byte 0x40-0x4e; 0x4f-0x5f stay free for the Hall)
| Op | Macro (pearl_story.inc "plat-hall") | Platinum |
|---|---|---|
| 0x40 | pl_HallInit resuming, type, slot1, slot2 | InitBattleHall |
| 0x41 | pl_HallFunction fn, arg1, arg2, var | CallBattleHallFunction (BH_FUNC_*) |
| 0x42 | pl_HallSetupNextOpponent | BattleHall_SetupNextOpponent |
| 0x43 | pl_HallFree | FreeBattleHall |
| 0x44 | pl_HallStartBattle | BattleHall_StartBattle (Black 2's Subway battle event, our setup) |
| 0x45 | pl_HallCleanupBattle | BattleHall_CleanupBattle |
| 0x46 | pl_HallCheckWonBattle var | BattleHall_CheckWonBattle |
| 0x47 | pl_HallUpdateWinRecord var | BattleHall_UpdateWinRecord |
| 0x48 | pl_HallTrainerWord word, slot, line | BattleHall_PrintTrainerIntro (the line into a word; the script prints it) |
| 0x49 | pl_HallTypeList summaryLine | OpenBattleHallApp's grid, as list rows |
| 0x4a | pl_HallTypeCheck cell, var | the app's pick rules |
| 0x4b | pl_HallTypeWords cell, typeWord, rankWord | the app's "Will you battle the X-type, Rank N Pokémon?" |
| 0x4c | pl_HallSetCell cell | BattleHall_GetTypeSelectionAppResult |
| 0x4d | pl_HallLobbyFunction fn, arg, var | CallBattleHallLobbyFunction 0-3 |
| 0x4e | pl_HallRecords what, var | GetNumSpeciesWithBattleHallRecords, GetBattleHallTotalSinglesRecord, CheckIfBattleHallStreakIs50 |
`b2_script_check.py` knows their lengths.

### The type grid
Black 2's script list menu, built by op 0x49 inside the script's own InitLocalTextListMenu/ShowListMenu: the grid's 17 types in
the grid's order (Normal, Fire, Water, Electric, Grass, Ice, Fighting, Poison, Ground, Flying, Psychic, Bug, Rock, Ghost,
Dragon, Dark, Steel), each "Name  N" with its rank as Platinum's grid shows it (stored + 1, at most 10), then a summary row
(a line of the zone's text; the script opens Black 2's summary of the entered Pokémon). The result is the grid's cell, as the
app's. Op 0x4a gives the app's rules: a type at the full rank can't be picked (Platinum buzzes); in a Single, when the next
battle is the 50th or 170th, it answers 2, and the script shows Platinum's own "Hall Matron approaching" and "Will you battle
against the Hall Matron?" lines (both in the scene's bank) before the battle, as the app does. No new screen.
Not kept: the grid's picture (the 4 x 5 cards) and the Pokémon's sprite on the top screen; the information is the same.
(plat-fix3, 2026-11-12) The fades around it: Platinum's scene fades to black (FadeScreenOut, CloseMessage), opens the app
(OpenBattleHallApp, its own screen, which fades itself in and out) and fades in after it (FadeScreenIn, after the
engine-layer toggle and the base level). The list is on the field here, so it was drawn under the black: both screens
black for the whole grid and its question (plat-fix2's final checks, work/agents/plat-fix2/final/hall_type_grid_black_screen.png).
Now the handler (pearl_story.py h_fr_hall_app) fades the room in before the list and out after the cell is set, as the
Arcade's board: black, the room with the list, black, the room (Platinum: black, the app, black, the room). Regenerated
MAP_BATTLE_HALL_CORRIDOR and MAP_BATTLE_HALL_BATTLE_ROOM (zones 721, 722): only those four lines in each file, the texts the
same; both assemble and pass b2_script_check. To see on screen: a Single challenge from the lobby (zone 689); in the
battle room (722) after "Please choose the type of Pokémon you will battle." the screen goes black and comes back with the
room and the type list at the top right; pick a type: "Will you battle the X-type, Rank N Pokémon?" and YES/NO over the
room; NO and B give the list again, still visible; YES: black, then the room as the opponent walks in. The same before each
battle of the round.

### Proven offline (`python3 b2tools/platinum_hall_check.py`)
1. `platinum_hall_data.py check`: 478 sets (set n + 1 is opponent n's species), 477 opponents, the tables found in the dump at
   0x3cc234 (opponents), 0x3cc5ee (types), 0x3cbf3c (by rank), 0x3cbeac (by type), 0x3cbfdc (Frontier classes): 0 problems.
2. `platinum_hall_host/run.sh`: Platinum's own C (extract.py copies it out of pokeplatinum: the Hall's five files' functions,
   `BattleHall_SetupBattle` whole, the Trainer loader, the shiny test) beside ours, with the same random numbers:
   - the tables: ours (from the dump) against Platinum's compiled ones (from the decomp's source and Trainer files);
   - 2,000 seeds x 4 challenges (Single and Double, fresh and resumed, streak flags on and off, ranks and records as a player
     has them): 59,832 battles, 89,481 opponents' Pokémon (species, form, item, moves, OT id, personality, IVs, EVs,
     ability, friendship, nature, level), the AI flags, 52,683 rank-ups, 3,405 rounds with their BP, 7,149 losses, the win
     records, Argenta 198 times; every field of the work, the save and the records compared after every step, and the random
     state (the same count of numbers);
   - sweeps: the opponents' level for levels 1-100, ranks 0-10 and every count of types fought (both modes); the next
     opponent for every cell, rank 0-10, battle 0-9 and round 0-18 (Argenta 374 times).
   Result: 5,618,932 checks, 0 differences. A changed IV row shows up at once (tried).
   (plat-arcade, 2026-11-07) The harness's Pokémon setup now draws the random numbers Platinum's Pokemon_InitWith draws, and
   hall_rules.c makes them (PlatHall_MakeOpponents): before, both left them out, and the opponents after a challenge's first
   battle were not Platinum's. "The Frontier's shared Pokémon setup" below.
3. Compiled with Black 2's mwcc against main's decomp headers, one file at a time (`work/agents/plat-hall/cc.sh`):
   hall_rules.c, hall_field.c, resident/plat_hall_ext.c, resident/plat_frontier.c (with the row): no errors.
   `symcheck.py`: every import is in main's link map, except OVERLAY_379_ID (the link makes it). One soft-float call Black 2
   lacks (`_fneq`, a float `!=`) became a double compare (exact for floats; `_f2d`, `_dneq` are there).
4. The macros assemble (scripts.assemble) and `b2_script_check.walk` reads all 15 ops to their End.

### Platinum's behaviour kept, that looks like a slip
- **The AI test for Argenta.** `BattleHall_SetupBattle` passes the battle's offset (currentBattle * 2) where the battle number
  belongs, and `BattleHall_GetAIMask` doubles it again: it reads trainerIDs[currentBattle * 4]. For battles 6-10 that is past
  the array, in `opponents[0]` (loaded with the current Trainer just before): battle 7 reads the Trainer's name's first
  character. Argenta's ids, 307 and 308, are the Gen 4 codes of I and J, so the 7th battle of every Single round against a
  Trainer whose name starts with I or J (21 of the 300) gets the full AI. Argenta's own battles get the AI of the chosen type's
  rank. Kept (hall_rules.c ArgentaProbe, the table's nameFlags); the harness proves it against the original.
- **A resumed challenge's Pokémon indices** pass through a u8 (BattleHall_Init): above 255 they lose their high byte, which only
  changes the "not fought yet this round" test after a resume. Kept.
- **Doubles** field two of the same set (the first; the second slot's set is loaded, drawing its numbers, and not used). Kept.

### The battle
`MakeBattle` (hall_field.c): the party healed (Party_HealAllMembers), Black 2's single or double Trainer setup, the entered
Pokémon as they are (no level change), the Frontier Trainer from the Subway's archive (patches/battle_tower.py wrote
Platinum's there), our AI flags (Platinum's three are Black 2's first three), the opponent's Pokémon from the rules as Black 2's
BSubwayPokemon at the rules' level (BtlInst_MakeParty), `BtlSetup_PostProcessTrialHouse` (the Subway's music), then Black 2's
`EventBSubwayBattleCall_Create` (overlay 12, as the Subway's own battles). The cleanup reads `setup->result`.

### Not done the way Platinum does it (or not done)
- **The rooms, the scene's translation, Argenta, the win records and the link of overlay 379**: built since (plat-frontier-rooms):
  "The picture rooms" below.
- **The particles** (battle_hall.spa, 26 emitters of 18 kinds: HALL_EMITTER_UNK_0-20, the spotlights and confetti of the battle
  room) and the scene's camera pans (FrontierScrCmd_4E) and big-screen sprite (FrontierScrCmd_45, 46): not mapped; they
  belong to the rooms. Black 2's own field effects were not matched yet.
- The Multi (wireless and Wi-Fi) is closed, as the Tower's. The lobby's party screen (BH_LOBBY_FUNC_SELECT_POKEMON) is the
  translator's: Black 2's Subway select or two single picks with the same-species rule.
- Black 2's own species (above 493) can't enter (the Hall has no sets for their types; Platinum never had them).
- Platinum's Brain cut-in, the Vs. Recorder, the TV segment: as the core's Tower.

### What the link must check (the lead, main's decomp)
- Copy `src/pokebw2/` over the decomp tree: `include/pearlb2/plat_hall.h`, `src/pearlb2/plat_hall/{hall_rules,hall_field}.c`,
  `src/pearlb2/resident/plat_hall_ext.c`, `src/pearlb2/resident/plat_frontier.c` (one row).
- `tools/pearlb2/link_overlays.py`: `PLATHALL = 379` at `AFTER(OV084, OV085)` (as PLATDW), `--plathall` objects; an empty 378
  if plat-factory's isn't there (the overlay table is by id; `pearlb2_overlays.py` now refuses a gap). `configure.py`:
  `"plathall": "src/pearlb2/plat_hall/*.c"` in the three PearlB2 places.
- `OVERLAY_379_ID`, `OV379_TEXT_START`, `gPlatHallTable` in the link; overlay 379 ends below overlay 146's start
  (pearlb2_overlays.py checks it); the layout check passes.
- `EventBSubwayBattleCall_Create`, `BtlInst_MakeRomTrainer`, `BtlInst_LoadTrainerData`, `BtlInst_MakeParty`,
  `BtlSetup_PostProcessTrialHouse` are overlay 12's: loaded in the field (the Subway's scripts call them the same way).

### For the combined ROM (once the rooms exist)
1. The Hall's lobby (MAP_BATTLE_HALL), the Single attendant: "Battle Hall" needs one Pokémon of level 30+ (a party of Lv. 29s
   is refused); a Double needs two of the same species.
2. Choosing a type: the list shows 17 types in the grid's order, each with "1" at first; the summary row opens the Pokémon's
   summary; pick Fire: "Will you battle the Fire-type, Rank 1 Pokémon?" Yes.
3. A battle: the Trainer is a Platinum Frontier Trainer (Platinum's name), one Pokémon of the chosen type at a level near the
   player's (a Lv. 50 Pokémon, rank 1, no other type fought: Lv. 29); Black 2's Subway music; the player's Pokémon keeps its level; after the
   battle the held item is back.
4. A rank up: win, pick the grid again: Fire shows "2". Ten wins: "You have cleared your tenth Battle Hall match", BP 1 (the
   first round's), the save.
5. Argenta: a save at a 49-win Single streak (records 34/35 = 40 and a round in progress, or play), the 50th battle: the
   "Hall Matron approaching" lines after the type is chosen, Argenta (her class and sprite once installed), her Pokémon from
   the player's species' group at the player's level, IVs 31; win: 20 BP.
6. Look for: the overlay loading in each Hall zone (a stop there means something sits at the gimmick address), the list's
   width with long type names, the battle's background (the zone's).

## The Battle Castle (plat-castle, 2026-11-07)
Three Pokémon whose HP, PP, status and held items carry from battle to battle; Castle Points (CP) earned by how well each battle
went and spent on healing, rented items, the opponent's information and rank ups; opponents by round; the streak and BP; Darach,
the Castle Valet, at the 21st and 49th battle of a Single streak. Status: the rules run offline and are proven the same as
Platinum's (its challenge and its two screens' own state machines); the game side is C compiled file by file; the lobby
translates; the corridor and battle room, the scene's translation into them and Darach's class, sprite, Trainers and songs are not
built (they wait for plat-frontier-rooms). Nothing of it was played.

### What is built, and where
- **The rules**: `src/pokebw2/src/pearlb2/plat_castle/castle_rules.c` (decomp path `src/pearlb2/plat_castle/`), header
  `src/pokebw2/include/pearlb2/plat_castle.h`. Platinum's battle_castle.c, battle_castle_helpers.c, battle_castle_save.c,
  frscrcmd_battle_castle.c (CallBattleCastleFunction, the CP commands), scrcmd_battle_castle.c (the streak's deletion) and
  frontier_opponents.c, step for step, with Platinum's LCRNG (one per challenge, seeded once from Black 2's generator). The two
  screens' purchases are `PlatCastle_Ask` (the checks Platinum's screen makes before its yes/no) and `PlatCastle_Buy` (the checks
  after the yes, then the purchase). The castle's party, the sets and the records come through calls the field gives (the
  harness gives its own), so the harness compiles the file as it is.
- **The tables** stay in castle_rules.c as the decomp's source has them (the round's Trainers, the BP, the rentals and their CP,
  the heal and rank-up costs): `platinum_castle_data.py check` finds each in the dump by its bytes and compares; the 61 items the
  Castle names have the same numbers in Black 2.
- **The field side**: `plat_castle/castle_field.c`, overlay 380 (`PLATCASTLE`), at Black 2's gimmick overlays' address, loaded for
  one op and unloaded (as the Hall's 379). No zone of the Castle may have a gimmick; if something sits there, `GFL_OvlLoad` refuses
  and the script stops (a check for the combined ROM). Size (mwcc's objects): text 10,810 B, rodata 418 B, data 38 B, bss 4 B:
  it ends near 0x021F1700, below overlay 146's start (0x021F59E0).
- **The resident side**: `resident/plat_castle_ext.c` (172 B of code, one pointer): the core's row for the Castle
  (`plat_frontier.c sFacilityOps[2] = PearlB2_Ext_Castle`), the battle's setup kept between the start and the cleanup, and
  `PearlB2_Castle_StoreParties` (below).
- **The work**: `PlatCastleWork` (Platinum's BattleCastleSave first, then the running challenge and the castle's three Pokémon
  as Black 2 party Pokémon, 1,072 B) in the core's challenge union, so it lives through the overlay's unloading and the warps.
- **The castle's party**: copies of the three field Pokémon, held items taken, Level 50 at most (Platinum's playersParty); the
  field party isn't touched (the lobby heals it before the challenge, as Platinum's). A rest saves its HP, PP, status and items
  into the BattleCastleSave and a resume makes the party again from the field party with them, as Platinum's.
- **The opponents' Pokémon**: kept as made (PlatCastleMon); the party Pokémon are made from them (Black 2's BtlInst_MakeParty) at
  Level 50, five up or down by the level change (the experience of Level 55 or 45, stats again), when a screen shows them or the
  battle starts.
- **patches/platinum_castle.py** (Platinum's build list, after battle_tower, platinum_frontier and platinum_factory): three
  regulations of a/1/0/6 (the self screen's one of three, the Factory's swap one when it is there; the lobby's three and two:
  Black 2's Subway file with no level rule, not the same species twice, the same item allowed, its banned species, which are
  Platinum's sBattleFrontierBanlist and Black 2's own legendaries) and `gPlatCastleTable` in overlay 380's .data (those files,
  Darach's songs: 0 until plat-music installs SEQ_PL_BA_BRAIN and SEQ_PL_WINBRAIN). Empty, no Castle challenge starts.

### Carried HP and PP: the battle's end
Black 2 writes the player's party as it left a battle back into the battle's setup only for wild and Trainer battles
(ov167 btl_main.c BtlMain_StorePartiesToSetup, `battleType <= 1`). A facility battle (2: the Subway's, the Trial House's, ours)
gets nothing back: the Hall and the Factory heal before every battle and don't need it; the Castle does. So BtlMain_ProcMain's call
of BtlMain_StorePartiesToSetup goes to the resident `PearlB2_Castle_StoreParties` (a call of the same size: rule 1 of
DECOMP_WORKFLOW.md): the original, then, for the Castle's own setup only (the pointer kept from the start op), Black 2's own copy
(`PokeCon_StoreClientSrcPartyInOrder`, `PokeParty_Copy` into `setup->party[0]`), without Black 2's giving back of held items (a
Trainer battle's): as Platinum, an item used up is gone. The cleanup op copies that party into the castle's. Every other battle is
as before. The decomp change is `src/pokebw2/plat-castle_decomp.diff` (btl_main.c, pearlb2.h's prototype): `git apply` in the decomp;
compiled with mwcc, BtlMain_ProcMain keeps its 0x98 bytes and every instruction but the call's target; btl_main.o keeps its size.

### The ops (sub-command 0x93, op byte 0x60-0x79; 0x7a-0x7f stay free for the Castle)
| Op | Macro (pearl_story.inc "plat-castle") | Platinum |
|---|---|---|
| 0x60 | pl_CastleInit resuming, type, s1, s2, s3 | InitBattleCastle (its last var is the link's) |
| 0x61 | pl_CastleLoadRound resuming | LoadTrainersForRound |
| 0x62 | pl_CastleFunction fn, arg1, arg2, var | CallBattleCastleFunction (BC_FUNC_*) |
| 0x63 | pl_CastleFree | FreeBattleCastle |
| 0x64, 0x65 | pl_CastleSetupFirstOpponent, pl_CastleSetupNextOpponent | BattleCastle_SetupFirstOpponent, _SetupNextOpponent |
| 0x66 | pl_CastleBattle | BattleCastle_StartBattle (Black 2's Subway battle event, the castle's party) |
| 0x67 | pl_CastleCleanupBattle | BattleCastle_CleanupBattle (the party back as it left) |
| 0x68 | pl_CastleCheckWonBattle var | BattleCastle_CheckWonBattle |
| 0x69 | pl_CastleTrainerWord word, slot, line | BattleCastle_PrintTrainerIntro (the line into a word; the script prints it) |
| 0x6A-0x6C | pl_CastleGetCP type, var; pl_CastleSpendCP type, cp; pl_CastleReceiveCP type, cp | GetCurrentCastlePoints, SpendCastlePoints, ReceiveCastlePoints |
| 0x6D | pl_CastleLobbyFunction fn, arg, var | CallBattleCastleLobbyFunction 0-3 |
| 0x6E | pl_CastleDeleteStreak type | DeleteActiveBattleCastleStreak |
| 0x6F, 0x70 | pl_CastleSelfScreen; pl_CastleSelfPick var | OpenBattleCastleSelfApp's Pokémon: Black 2's battle-entry party screen |
| 0x71, 0x72 | pl_CastleAsk kind, slot, arg, var; pl_CastleBuy kind, slot, arg, var | the screens' purchases (PLATCASTLE_BUY_*, answers PLATCASTLE_RESULT_*) |
| 0x73 | pl_CastleRentalList items | OpenItemSelectScreen's rows: the rank's rows, each with its CP |
| 0x74 | pl_CastleOpponentList line | the opponent screen's three (a line for one not identified) |
| 0x75 | pl_CastleMonWords side, slot, what | the summary and moves panels' names and numbers as words |
| 0x76 | pl_CastleInfo what, slot, var | the ranks, what was bought, the level change, the party's count |
| 0x77 | pl_CastleCPWord word | the CP window's number |
| 0x78, 0x79 | pl_CastleLobbySelect type; pl_CastleSelectedSlots v1, v2, v3 | CallBattleCastleLobbyFunction 4, GetBattleCastleSelectedSlots |
`b2_script_check.py` knows their lengths; all 26 assemble and the checker walks them to their end.

### The two screens (`src/include/pearl_castle_screens.inc`)
Black 2 has no screens like Platinum's. What they are here:
- **The self screen**: Black 2's battle-entry party screen on the castle's three (HP bars, status, held items, its summary pages)
  picks the Pokémon (B leaves); then Black 2's list menus with Platinum's entries and descriptions: HEAL (RESTORE HP 10 CP, RESTORE
  PP 8, RESTORE ALL 12, RANK UP 100/100), RENTAL (BERRIES, ITEMS, RANK UP 100/150; the rows the rental rank allows with their CP),
  SUMMARY and MOVES (one line each, the panels' values as words), CANCEL.
- **The opponent screen**: a list menu of the opponent's three (a line for one not identified), then CHECK (1 CP), LEVEL (+5 1 CP,
  -5 15 CP), SUMMARY (stats 2 CP, moves 5 CP at information rank 2, RANK UP 50), CANCEL.
- Every answer shows Platinum's own line for it and goes back where Platinum's screen goes (the state machines' WAIT_* states); the
  rank at its top buzzes. `pl_CastleScreensCode` emits both as two subroutines, CastleSelfScreen and CastleOpponentScreen, for the
  scene's translation to call where Platinum opens the screens. The room's script sets `CASTLE_SELF`, `CASTLE_OPP` (the first line
  of each screen's text bank in the zone's text) and `CASTLE_LINES` (three lines of the Castle's own: an unidentified Pokémon's
  row, the summary panel, the moves panel). Assembled with test values (2,246 B), b2_script_check walks all 393 commands.
- No new screen. Not kept: the screens' pictures (the emblem, the Pokémon's sprites and their animations, the CP header, the grey
  of an entry the rank doesn't allow: its message says so when picked); the summary and moves panels are one line each.

### Proven offline (`python3 b2tools/platinum_castle_check.py`)
1. `platinum_castle_data.py check`: the 11 tables found in the dump and equal in castle_rules.c; 61 items the same numbers in Black 2.
2. `platinum_castle_host/run.sh`: Platinum's own C (extract.py copies it out of pokeplatinum: the Castle's battle_castle.c,
   battle_castle_helpers.c, battle_castle_save.c, the scene's commands of frscrcmd_battle_castle.c through a stand-in for the scene's
   context, the lobby's streak deletion, frontier_opponents.c, the records' functions, item_use_pokemon.c's item effects, and the two
   screens' State_MainAppFlow with every function their purchases run through) beside castle_rules.c, with the same random numbers
   and the same choices. A Pokémon model both sides share (a level from its experience, PP from moves and PP Ups, HP moved with
   the maximum as Platinum's Pokemon_CalcLevelAndStats does). 2,000 seeds: 8,000 challenges, 33,631 battles (29,595 won, 4,036
   lost; 15,714 Pokémon fainted and revived), 2,471 rounds (10,567 BP), 281 Darach battles, 1,335 passes, 1,482 rests resumed,
   1,493 retires; 27,573 visits to the self screen and 26,932 to the opponent screen, 50,876 purchases made, 2,656 rank ups; 490,193
   CP earned. Every field of the castle, the castle's party, the opponents (as made, at their levels), the battle's setup (the party
   as it is, the opponents, the Trainer, the AI), the saved challenge and the records compared after every step, the random state
   too, and for each purchase the lines Platinum's screen showed and the cost it named against our answers: 27,093,729 checks,
   0 different. Every outcome of every purchase was reached (the run prints them).
3. Mutations caught (each alone, 200 seeds): a heal cost, the level-down cost, the PP bonus, Darach's 20 BP, a rank-up cost, the
   item list's size by rank, the level change's toggle, the revive's 1 HP, an IV step, the challenge's starting 10 CP, the AI's
   rounds, the PP rule's edge, Darach's streak, the resume's PP.
4. Compiled with Black 2's mwcc against main's decomp headers, one file at a time (`work/agents/plat-castle/cc.sh`): castle_rules.c,
   castle_field.c, resident/plat_castle_ext.c, resident/plat_frontier.c (with the row), and btl_main.c with the change: no errors.
   `symcheck.py`: every import is in main's link map, except OVERLAY_380_ID (the link's) and the Factory's and the Hall's rows (theirs).
5. The lobby: pearl_story translates MAP_BATTLE_CASTLE's Castle commands (CallBattleCastleLobbyFunction, GetBattleCastleSelected-
   Slots, DeleteActiveBattleCastleStreak; block "plat-castle"); the file assembles and passes b2_script_check.

### Platinum's behaviour kept, that looks like a slip
- **A resumed challenge's first battle earns the PP bonus.** Init clears the PP the battle starts with, and only the next
  battle's preparation sets them; after a resume the first battle's "PP used" is negative: 8 CP for using 5 or fewer. Kept.
- **The opponents loaded on a resume** have IVs Platinum never sets (an uninitialised array); they decide only whether their making
  draws two numbers, and they are made again before any battle. Both sides use 0 (the harness's one edit to Platinum's text).
- **Darach in the second Trainer row**: a Single round before Darach's also puts him in the 14th place (the link partner's
  opponent row, never fought). Kept, as it draws no number.

### Not done the way Platinum does it (or not done)
- **The rooms, the scene's translation, Darach and the link of overlay 380**: built since (plat-frontier-rooms): "The picture
  rooms" below (scene 13 isn't: only unreferenced code of the Castle's script changes to it).
- **Darach**: installed since (plat-frontier-rooms): class 239, Trainers 313 and 314, walker 120, the Brain songs ("The Brains"
  under "The picture rooms").
- **Held items after a battle**: as Black 2's battle leaves them (one used up is gone, as Platinum; Knock Off and Trick as Black 2
  writes the party back).
- **Status after a battle**: Black 2's party status (one value; badly poisoned comes back as poison). The CP rule asks only
  "any status", so the CP are the same.
- **The CP window** is a line, not a window beside the menu. Platinum's game record of CP received has no Black 2 counterpart.
- **The Multi** (wireless and Wi-Fi) is closed, as the other facilities'.
- Black 2's own species (above 493) can't enter: the lobby's regulation bans Black 2's legendaries and the eligibility check
  counts only Platinum's species (as the Hall's).
- Platinum's yes/no menus that start on No start on Yes (the core's note).

### What the link must check (the lead, main's decomp)
- Copy `src/pokebw2/` over the decomp tree: `include/pearlb2/plat_castle.h`, `src/pearlb2/plat_castle/{castle_rules,castle_field}.c`,
  `src/pearlb2/resident/plat_castle_ext.c`, `src/pearlb2/resident/plat_frontier.c` (one row, one include); then
  `git apply plat-castle_decomp.diff` (ov167 btl_main.c's call, pearlb2.h's prototype).
- `tools/pearlb2/link_overlays.py`: `PLATCASTLE = 380` at `AFTER(OV084, OV085)` (as PLATHALL and PLATDW), `--platcastle` objects
  `src/pearlb2/plat_castle/*.c`; `configure.py`: `"platcastle": "src/pearlb2/plat_castle/*.c"` in the three PearlB2 places.
  pearlb2_overlays.py knows 380 (its gimmick-address check covers it).
- `OVERLAY_380_ID`, `OV380_TEXT_START`, `gPlatCastleTable` in the link; overlay 380 ends below overlay 146's start; the layout
  check passes; `decomp.py changed` lists BtlMain_ProcMain (the call's target) and nothing else of Black 2's.
- The overlay 12 functions the field side calls (EventBSubwayBattleCall_Create, EventBtlInstPokeSelect_Create, BtlInst_*) are
  loaded in the field, as for the Hall and the Factory.

### For the combined ROM (once the rooms and the scene are in)
1. Entering: the Castle's lobby (MAP_BATTLE_CASTLE), the Single attendant: Info and Single/Double; a party of three of the same
   species is refused ("identical Pokémon"), Mewtwo can't be picked; pick three, the heal and the save, the walk to the corridor.
   First time: Darach's long welcome; his items taken (the castle's three hold nothing); 10 CP.
2. The castle's menu: the CP shown; HEAL/RENTAL/SUMMARY/MOVES on the self screen, CHECK/LEVEL/SUMMARY on the opponent screen.
3. A battle with carried HP: let a Pokémon lose HP and use PP, win; back in the menu its HP and PP are what the battle left (the
   self screen's party screen shows them), a fainted one is back at 1 HP, every status is gone. The CP earned line: e.g. three
   standing at full HP, no status, 5 PP used or fewer: 3x3 + 3x3 + 3 + 8 = 29 CP. Lose a held Berry in battle: it's gone after.
4. Spending CP on each kind: RESTORE HP (10 CP) on a hurt Pokémon: full HP, CP down 10; on a full one: "no benefit", no CP spent.
   RESTORE PP before the healing rank 2: "too low in healing rank". RANK UP (100 CP) then RESTORE PP (8 CP). A Berry (Cheri 2 CP),
   an item at rental rank 2 (King's Rock 10 CP); renting onto a held item asks to switch. CHECK an opponent (1 CP): its species in
   the list; LEVEL +5 (1 CP): Lv. 55 in the list, and 7 more CP after a win; LEVEL -5 (15 CP); SUMMARY (2 CP): the stats line;
   MOVES before information rank 2: refused; RANK UP (50 CP), then MOVES (5 CP). Not enough CP: Platinum's line, nothing spent.
5. A rank up: the healing rank's RANK UP at 1 -> 2 (100 CP): "gained the ability to restore PP!", RESTORE PP opens; the rental
   rank at 2 -> 3 (150 CP): the lists grow to 32 Berries and 27 items; a rank at its top buzzes. A loss puts every rank back to 1.
6. The pass (from the 4th round, not before Darach): 50 CP, the battle skipped, the streak and battle count up, no CP earned.
7. Darach: a Single streak at 20 (records 71 = 20 and a round started, or play): "the Castle Valet approaching" before the 21st,
   Darach's intro, his Silver team at Level 50 with the full AI; win: 20 BP and the Silver Print line; Gold at the 49th. Needs his
   class, sprite, Trainers 313/314 and lines installed (above).
8. Rest after a win: the save, the reset, Continue in the lobby: the challenge resumes with each Pokémon's HP, PP, status and item
   as saved.
9. Look for: the overlay loading in each Castle zone (a stop there means something sits at the gimmick address), the list menus'
   width with long item names and CP, the summary and moves lines' fit in the message box.

## The picture rooms (plat-frontier-rooms, 2026-11-07)
The Factory, Hall, Castle and Arcade draw their corridors and battle rooms as 2D scenes: a background of Platinum's
(`resource/eng/frontier_graphic/frontier_bg.narc`) with sprites over it, no zone, no map. Here each is a Black 2 field room, one
mechanism for all eight (`b2tools/frontier_rooms.py`), and the Factory's, Hall's and Castle's scenes run in them. Nothing was built
or played: the combined ROM's list is at the end.

### One way from a picture to a room
- **The picture**: the scene's layers from Platinum's dump as the DS shows them (frontier_graphics.c: BG3, and BG2 when the scene
  keeps it shown, back to front: the Factory corridor's moving floor behind the corridor, the Castle battle room's curtains in
  front; the Hall's lights and the Arcade's screen effects start hidden and stay out). Transparent pixels show the backdrop, black.
  The Factory's floor layer runs 512 rows under the corridor's 192: the room keeps the corridor's part.
- **The textures**: 32 x 32 blocks; each distinct block is one texture, 16 colours when it has at most 16, else 256, with its own
  palette; all-black blocks are left out (the room's void is black too). One set per facility (its two rooms share it):
  Factory 83 KB (89 textures), Hall 68 KB, Castle 94 KB, Arcade 79 KB. `frontier_rooms.py check` decodes every block back: the
  same pixels as Platinum's, all eight rooms, 0 problems.
- **The model**: one flat quad per block at height -4 (`PICTURE_Y`), a material per texture: unlit, vertex colour white (the texels as they
  are), clamped, both faces, polygon id 0 (Pearl's indoor outlines). Position scale 64 (a land model's 32 can't reach +256).
  Its box holds its quads (`fit_box`; the template's box made Black 2 leave the Hall's battle room out past its first screen).
  Why 4 under the land: Black 2 draws a person 2 units under the land at this pitch (Field_CalcActorYOffset), and under so
  steep a camera a sprite lies almost flat, so a picture at 0 covered every person's lower half (the Arcade's battle room:
  all but a line of their heads; found 2026-11-08 by plat-test, people lifted 2 units in RAM showed whole).
- **The land**: Black 2's flat tiles at 0; floor where the scene's people stand and walk (a flow analysis of the scene's
  placements and moves), wall elsewhere.
- **The place**: picture pixel (px, py) is world (px + 8 + 16 AX, py + 8 + 16 AZ). Platinum stores a scene object at (x - 8,
  y - 16) and draws its shadow at +8, +14: the sprite is centred on (x, y - 16), feet at y - 2. Seen from above, Black 2 draws a
  person centred on its tile, feet 14 units south. So an object at (x, y) is the tile ((x + 16 AX) / 16, (y - 16 + 16 AZ) / 16):
  frontier_translate's `origin`. Every room has AX 0, AZ 1.
- **The camera** (a/0/5/9, appended): Black 2's camera 0 (20-degree half-angle, bound to the player, 4 units up), pitched 87
  degrees, at 260 units; W-buffered. Black 2 puts the eye no steeper than 82.8 degrees over the bound player (field_camera.c
  TransRot: cos(pitch) at least 0x200), so the view is 82.9 degrees (measured in RAM), about a texel a pixel on the picture at
  -4. Platinum's scene camera follows its object 0 (the hidden player): the screen's top-left is (x - 120, y - 112). The real
  player stands hidden on the tile under that screen's centre. Black 2 moves only the target by a camera record's offset, not
  the eye, so an offset across turns the view about the vertical (the Castle corridor's 8 units east: 14 degrees, seen in RAM):
  across, the centre goes to the nearer tile's (the Castle corridor: 8 px west of Platinum's). Along the view an offset only
  steepens it a little and stays (the Arcade battle room's 12 south: 85.5 degrees). A scene that walks its object 0 pans the
  camera the same way here (the Hall's battle room).
- **The people's looks**: Black 2 takes a person's VAR_OBJ_GFX_ID look when it makes them, at the zone's load; a scene sets
  its looks in the room (the Arcade corridor's 0x4020-0x4022, 0 at the warp), so frontier_translate makes each person drawn from
  a look slot again (ActorDelete, ActorAdd) where the scene places its objects (FrontierScrCmd_24), as Platinum makes them there
  (2026-11-08, plat-test: the Arcade corridor's attendant and the player's stand-in walked unseen; with the looks set before
  the warp in RAM they showed).
- **The zones**: pseudo map ids 593-600 after Platinum's 593, on zones 719-726 by the Platinum block's rule (allocate_sinnoh
  `FRONTIER_ROOMS_BLOCK`, Platinum only; notes/ZONE_TABLE.md). `patches/platinum_frontier_rooms.py` (Platinum's list, after
  sinnoh_music) installs chunks, matrices, one area per facility (appended: 409-412 before the Secret Base's, under
  AREA_COUNT 0x1a1) with an empty building pack, the cameras, an entity file per room, and each header: its lobby's (music,
  place, weather, flags, battle background), map type 16, the lobby as parent. The Castle's scene 13 (battle_castle_unknown,
  the stairs) gets no room: only unreferenced code of the Castle's script changes to it.

| Zone | Room | Picture | Camera's tile (target offset) | People (local ids) |
|---|---|---|---|---|
| 719 | Factory corridor | 256 x 192 + the moving floor | (8, 7) | 3 attendant, 4 player's look, 5 side attendant, 98, 99 |
| 720 | Factory battle room | 256 x 192 | (8, 7) | the same |
| 721 | Hall corridor | 116 x 192 | (8, 7) | 3 attendant, 10 player's look, 11 maid, 98, 99 |
| 722 | Hall battle room | 256 x 400 | (8, 8), panning down | the same |
| 723 | Castle corridor | 231 x 192 (of 512) | (17, 7) (+8 east) | 3, 6 Darach's butlers, 4 player's look, 5 Caitlin, 7, 98, 99 |
| 724 | Castle battle room | 256 x 240 + curtains | (8, 9) | the same |
| 725 | Arcade corridor | 181 x 161 | (8, 8) | 19 (the crowd, attendants, opponents) |
| 726 | Arcade battle room | 256 x 304 | (8, 18) (+12 south) | the same |

`frontier_rooms.py render` writes each room through its camera beside Platinum's own screen for the same camera
(work/agents/plat-frontier-rooms/rooms/): the eight match, the people's outlines where the scene places them.

### The scenes in the rooms
- `frontier_translate.HOSTS` gets a row per picture room (`PICTURE_HOSTED`: the Factory, Hall and Castle; (plat-arcade) the
  Arcade's too now, so its lobby warps to the corridor: "The Battle Arcade", "The scene in its rooms"). A room's people are every object its script file places, by
  their local ids (the person's uid is the local id), so a file's two scenes stage the same way in their two rooms. Each person
  stands on a parking tile no camera place shows until its scene puts it (SetPosition, Show, Hide before the fade-in).
- Looks: a person drawn from a var takes a look slot (VAR_OBJ_GFX_ID n). GetPlayerObjEventGfx sets the slot by the player's
  gender (Platinum's 0 or 97, Black 2's 231 or 240); a var set to a number (the attendants' 231/232) sets its slots there; the
  opponents' vars the facility ops fill with Black 2 codes (PearlB2_TowerObjCode) are copied when the person appears.
- The facility commands travel as they are: opcode 840 + the frontier opcode, its arguments, past Platinum's 840 field
  commands (frontier_translate `CARRIER_BASE`). pearl_story's block "plat-frontier-rooms" grows its table by them (FR_ + the
  name) and turns them into the facilities' ops: the Factory as its section's mapping, the Hall's and the Castle's as their
  tables. Field commands where Platinum's field has one (BufferSpeciesName, BufferMoveName, BufferItemName, GiveBattlePoints,
  IncrementTrainerScore); the wireless Multi's nothing (a SendCommMessage's result 1).
- The Hall's type grid (OpenBattleHallApp): a list menu of the 17 types with their ranks and a SUMMARY row (Platinum's party
  menu line), pl_HallTypeCheck's rules: a full rank buzzes, Argenta next shows the scene's own lines 32 and 31 and a yes/no,
  else line 24 ("Will you battle the X-type, Rank N Pokémon?") and a yes/no; then pl_HallSetCell.
- The Castle's screens: the room's file gets pearl_castle_screens.inc's two subroutines with Platinum's two screen banks and
  three lines of the Castle's own (an unidentified row, the summary panel, the moves panel) in its text.
- The lobbies: the Factory's DeleteActiveBattleFactoryStreak, the Hall's lobby functions, its records and its party screen
  (Black 2's party list, once; a Double asks a second of the same species).
- `PEARL_VERSION=platinum python3 b2tools/frontier_rooms.py scripts`: the eight rooms and four lobbies written, assembled and
  checked as sinnoh_story installs them (b2_script_check at the map scripts' levels, lines, entries, people): every file
  passes. The Tower's eight zones too (unchanged: the synthesized Tower files are byte for byte the same).

### The Brains
- Classes: Black 2's spare classes are all Pearl's, so Platinum's four Brains have classes past Black 2's 236: Hall Matron 236,
  Factory Head 237, Arcade Star 238, Castle Valet 239 (`version.NEW_TRAINER_CLASSES`, `data/platinum/pearl_trainer_classes.json`).
  Palmer stays on 198. The decomp's `resident/trainer_class.c` answers tr_tool.c's three class readers from
  `gPearlB2TrainerClassExt` (patches/pearl_trainers.py; NULL in Pearl and Diamond: Black 2's behaviour). Their names are lines
  236-239 of system text 383 and 485. No prize money: a facility battle pays none, as Platinum's.
- Battle pictures: Platinum's own, frame 0, sprites 234-237. Frontier Trainers 307-314: patches/battle_tower.py (a/2/1/2 file 315
  added).
- Walkers: Thorton 113, Argenta 114, Darach 120, Dahlia 124 (Platinum's mmodel 378-381, pixel for pixel); Caitlin, in the
  Castle's corridor, 209 (mmodel 382 'princess').
- Songs: SEQ_PL_BA_BRAIN and SEQ_PL_WINBRAIN, installed by battle_music on classes 198 and 236-239; the Factory's, Hall's and
  Castle's tables take their ids at build time.
- The Hall's win records: Black 2's extra save block 4 (the C-Gear's skin, unused in Sinnoh; notes/DATA.md registry): magic
  'HWIN', 2 x 495 u16. Op 0x47 loads it, updates the record and, when it rose, writes the block with the whole save and answers
  1, as Platinum; the scene's own save runs only on 0. Op 0x4e loads it to count.

### The link (overlays 378-380)
The Factory (378, at Pal Park's address: PB2END after it, it ends below Pal Park's), the Hall (379) and the Castle (380, both at the
gimmick overlays' address, ending below overlay 146) link in plat-frontier-rooms' decomp (pearlb2-plat-frontier-rooms: link_overlays.py,
configure.py; plat-castle_decomp.diff applied: `decomp.py changed` adds only BtlMain_ProcMain and the three class readers to
main's list). `decomp.py check` passes. The Factory's factory_rules.c didn't include pearlb2.h, so PEARLB2 0 compiled it and the
vanilla link failed on PlatFactory_SpeciesTypes: it includes it now (plat-factory's code).

### Not done the way Platinum does it
- The pictures' effects: the Factory corridor's moving floor (it doesn't scroll), the Hall's lights and big screen (the player's
  Pokémon on it), the shakes (FrontierScrCmd_4C), the particles (spotlights, confetti, sparks): no field form here; dropped and
  counted in `frontier_translate.py report`.
- The camera is 3 degrees off straight down: the picture's far edge is about 2 % narrower than its near one.
- The Hall's SUMMARY row opens the grid again (Black 2 has no field command for a Pokémon's summary).
- The Hall's party screen is Black 2's party list, one pick at a time (a Double's second pick must be the first's species).
- The Castle's CP windows: their numbers go into a word the screens' lines show.
- (plat-arcade) The Arcade's scenes are hosted now (its commands: "The Battle Arcade").

### For the combined ROM
Build Platinum with `platinum_frontier_rooms` after `sinnoh_music` and `platinum_factory platinum_hall platinum_castle` after
`platinum_frontier`.
1. **Factory corridor (719)**, from the Factory's lobby (688): the picture fills the screen as Platinum's (the corridor in the
   middle, the floor strip in its gap); the attendant at (8, 5) faces down; the player's look (the player's own sprite, boy or
   girl) walks up from (8, 12) to (8, 6); the side attendant walks in from (6, 11). No one stands in view before the fade-in.
   Look for flicker between the sprites and the floor, and a sprite cut by the floor.
2. **Renting**: Black 2's party screen with six rentals; B brings it back.
3. **Factory battle room (720)**: the player's look walks from (8, 12) to (4, 8), the opponent from the door (8, 4) to (12, 8),
   his line in a balloon, the battle. Thorton at the 21st Single battle: walker 113, class "Factory Head", his picture, the Brain
   songs.
4. **Hall corridor (721) and battle room (722)**: the walk in; the type list (17 rows, ranks, SUMMARY); "Will you battle the
   Fire-type, Rank 1 Pokémon?"; the camera pans down the stage with the hidden player; the opponent's line in the message
   window. Argenta at the 50th Single battle: "Excuse me!..." then her walker 114.
5. **Castle corridor (723) and battle room (724)**: the picture square on the screen (no turn), 8 px west of Platinum's framing;
   Caitlin (209) and the butlers; the self screen's menus; Darach at the Castle's Brain battle: walker 120, class 239.
6. **Each room**: the people's feet on the floor's painted spots (a few pixels off is the 2-pixel feet rule), no stray person in
   view, the black void around the picture, the edges outlined black (Pearl's indoor), the room's music the lobby's.
7. **Arcade rooms (725, 726)**: (plat-arcade) reached from the Arcade's lobby now: "The Battle Arcade", "For the combined ROM".
8. **Win records**: as the Brains' note (a Hall win saves once; Continue; the record keeper counts).

## The Battle Arcade (plat-arcade, 2026-11-07)
Three Pokémon at Level 50 at most; before every battle the game board: 16 panels drawn from 32 effects, a cursor running over
them at the board's speed, stopped by the player; the effect lands on the opponent's party, the player's, the battle's field or
the board itself; opponents by round; the streak and BP; Dahlia, the Arcade Star, at the 21st and 49th battle of a Single
streak. Status: the rules run offline and are proven the same as Platinum's (its challenge, its scene commands and its game
board's app, frame by frame); the game side is C compiled file by file; the lobby and the scene translate (the scene into
plat-frontier-rooms' two picture rooms, zones 725 and 726); overlay 381's link is a diff for the lead. Nothing of it was played.

### What is built, and where
- **The rules**: `src/pokebw2/src/pearlb2/plat_arcade/arcade_rules.c` (decomp path `src/pearlb2/plat_arcade/`), header
  `src/pokebw2/include/pearlb2/plat_arcade.h`. Platinum's battle_arcade.c, battle_arcade_helpers.c, battle_arcade_save.c,
  frscrcmd_battle_arcade.c (CallBattleArcadeFunction, the board's arguments, the battle's cleanup), scrcmd_battle_arcade.c (the
  streak's deletion), frontier_opponents.c, and the board's own decisions from applications/frontier/battle_arcade/main.c (the
  random number, the starting panel, the 16 panels, the cursor, the 30 seconds, the stop), step for step, with Platinum's LCRNG
  (one per challenge, seeded once from Black 2's generator). The parties, the sets and the records come through calls each side
  gives (plat_arcade.h), so the harness compiles the file as it is.
- **The tables** stay in arcade_rules.c as the decomp's source has them; `platinum_arcade_data.py check` finds each in the dump's
  own code (overlay 104, the Frontier's; overlay 108, the board's; both stored uncompressed) and compares: the opponent pools, the
  free BP, the board's speed by round, the performance's three tables, the item and Berry pools, the BP by round, the cursor's
  frames by speed, the effects by round and by battle (bit fields: a byte an effect), the kinds' weights and the tiers' thresholds.
  The 56 items they name have the same numbers in Black 2.
- **The field side**: `plat_arcade/arcade_field.c`, overlay 381 (`PLATARCADE`), at Black 2's gimmick overlays' address, loaded
  for one op and unloaded (as the Hall's 379 and the Castle's 380). No zone of the Arcade may have a gimmick. Size (mwcc's
  objects): text 10,922 B, rodata 390 B, data 34 B, bss 4 B (about the Castle's 380: it ends below overlay 146's start).
- **The resident side**: `resident/plat_arcade_ext.c` (452 B of code, 8 B of data): the core's row (`plat_frontier.c
  sFacilityOps[3] = PearlB2_Ext_Arcade`), the board's op, the battle's setup and start effect kept across the battle, both
  parties as they left the battle (`PearlB2_Arcade_StoreParties`, from the Castle's hook), and the battle start's Trick Room
  (`PearlB2_Arcade_AfterSwitchIn`, from ov167).
- **The work**: `PlatArcadeWork` (Platinum's BattleArcadeSave first, then the running challenge, the board, the player's three as
  Black 2 party Pokémon and the opponent's three as their sets plus what the board changed: 1,292 B of the 1,444 B) in the core's
  challenge union, so it lives through the overlay's unloading and the warps.
- **The player's party**: copies of the three field Pokémon, held items taken, Level 50 at most (Platinum's playersParty); the
  field party isn't touched (Platinum's isn't either: its RESTORE_HELD_ITEMS is never called). The effects change the copies;
  the battle copies them, then the rules heal them (BattleArcade_SetupBattle); after it they keep the held items as the battle
  left them and the stats they had when the board opened.
- **The opponent's party**: each Pokémon as its set was made (PlatArcadeMon) plus its HP, status, item and level
  (PlatArcadeOpponent); Black 2's BtlInst_MakeParty makes a party Pokémon of it when a value needs one (its stats, its level from
  its experience) and for the battle.
- **patches/platinum_arcade.py** (Platinum's build list, after battle_tower, platinum_frontier and platinum_castle): the lobby's
  regulation (the Castle's lobby file of three: Platinum's Arcade opens the party menu in the Castle's mode; shared when
  platinum_castle made it, else appended) and `gPlatArcadeTable` in overlay 381's .data (its file, Dahlia's two songs). Empty, no
  Arcade challenge starts.

### The game board
Black 2 has no such screen. What it is here: **a window of the 16 panels on the field** (the top of the screen, 30 x 8 tiles),
each panel the name of its effect (32 lines of the room's text, `platinum_arcade_data.BOARD_NAMES`: Platinum's panels are
pictures, these are short names, at most 54 pixels of the 56 a panel has), the cursor a panel drawn white on dark. It runs as a
field event at Platinum's timing, frame for frame (the field's events run 30 times a second, as Platinum's app): 10 frames, the
panels count 3, 2, 1 (24 frames each, a sound each), the names and the cursor appear, the cursor moves every sCursorMoveFrames
frames of the board's speed (or to a random panel after the Random effect) with a sound, until A or a touch stops it or 30 seconds
pass; then every panel shows the effect for 30 frames. Every decision is arcade_rules.c's (`PlatArcade_RouletteTick` once a frame),
so the panels, the cursor and the effect are Platinum's for a stop on the same frame. The window is Black 2's money window
(FieldMsgBG_CreateMoneyWin, the BP window's); the event lives in overlay 381, which Black 2's own GameEvent_CreateOverlayDelegate
loads for as long as the board runs and unloads after (the op itself is the resident's). Why this and not a list menu: a list
can't show the 16 panels at once nor move its cursor on its own; the board's choice is a timing, and the window keeps it.
Not kept: the panels' pictures and their turning animation (the count is printed), the Pokémon and item sprites beside the board,
the bottom screen's STOP button (A stops it too; Platinum's only stop is the touch). Sounds (Platinum's -> Black 2's, from
pearl_story's map where it has one): WIN_OPEN2 -> SEQ_SE_OPEN2 [guess], UG_020 -> DECIDE2, BUTTON3 and BUTTON9 -> DECIDE1,
PIRORIRO2 -> DECIDE2 [guess].

### The effects in the battle
- The opponent's and the player's (HP, poison, paralysis, burn, sleep, freeze, a Berry, an item, three levels): on the parties
  before the battle, as Platinum's. Black 2's party status is one value: a sleeping Pokémon's turns are drawn by Black 2's battle
  (Platinum's 2-5 turns are drawn too, so the numbers after are Platinum's, but not used). The Ally Level Up comes back down after
  the battle, as Platinum's.
- Sun, rain, sandstorm, hail: the battle's starting weather, which Black 2 keeps for the whole battle as Platinum's *_PERM
  (BtlFieldEnv.weather: BtlServerFlow_StartBattle's ServerControl_ChangeWeather with 0xff turns).
- Fog: Pearl's fog (resident/leftovers.c: every move's accuracy x 3/5, Platinum's deep fog x 6/10), set for the battle by a new
  `PearlB2_SetBattleFog` (plat-arcade_decomp.diff). Not kept, as Pearl's own: "The fog is deep..." and Platinum's Cloud Nine
  exception (Black 2 has no fog in battle).
- Trick Room: five turns from the battle's start, before the abilities on entry (Platinum's FIELD_CONDITION_TRICK_ROOM_INIT), set
  by `PearlB2_Arcade_AfterSwitchIn` with Black 2's own field effect (ServerControl_FieldEffectCore, Trick Room's handler's effect
  and turns); Black 2's "The twisted dimensions returned to normal!" ends it. Not kept: Platinum's Trick Room animation and "The
  dimensions became distorted!" (Black 2's battle text has no line for it without a Pokémon, and a new shared line would change
  Pearl's and Diamond's text; the room's own line before the battle says it).
- The swap: the player fights with the opponent's three and the opponent with the player's; after it the player's own keep their
  items as the opponent's side left them (Platinum's: dto->parties[BATTLER_ENEMY_1]).
- Speed up, slow down, random cursor: the board's state (saved with a rest). The two BP panels: the scene gives the BP (1 or 3).
  No battle: the scene skips it (no cleanup: the last performance stays, as Platinum's). No event: nothing.

### The battle's ends (the decomp: `src/pokebw2/plat-arcade_decomp.diff`)
- **The parties as they left**: the Castle's hook (ov167 btl_main.c's BtlMain_StorePartiesToSetup call -> resident
  PearlB2_Castle_StoreParties, plat-castle_decomp.diff) now also calls `PearlB2_Arcade_StoreParties` (a plat-arcade block in
  resident/plat_castle_ext.c): for the Arcade's battle only, both clients' parties as they left (Black 2's own copy, in order,
  without its giving back of held items) into setup->party[0] and [1]. No change to Black 2's file beyond the Castle's.
- **Trick Room**: ov167 btl_server_flow.c BtlServerFlow_StartBattle's ServerControl_AfterSwitchIn call goes to the resident
  PearlB2_Arcade_AfterSwitchIn (a call of the same size: compiled with mwcc, btl_server_flow.o's .text is byte for byte the same,
  one relocation's target differs).
- **Fog**: resident/leftovers.c gets `PearlB2_SetBattleFog` (its sBattleFog). pearlb2.h gets both prototypes.
- **The turns** (the performance): Black 2's setup->unkD2 (BtlMain_StoreResultStats' GetTurnCounter: the turns ended, as
  Platinum's totalTurnsElapsed counts them).

### The ops (sub-command 0x93, op byte 0x80-0x8F; 0x90-0x9F stay free for the Arcade)
| Op | Macro (pearl_story.inc "plat-arcade") | Platinum |
|---|---|---|
| 0x80 | pl_ArcadeInit resuming, type, s1, s2, s3 | InitBattleArcade (its last var is the link's) |
| 0x81 | pl_ArcadeLoadRound resuming | BattleArcade_LoadTrainersForRound |
| 0x82 | pl_ArcadeFunction fn, arg1, arg2, var | CallBattleArcadeFunction (BA_FUNC_*; SET_NAME_OF_AFFECTED_TRAINER: word arg1, slot arg2) |
| 0x83 | pl_ArcadeFree | FreeBattleArcade |
| 0x84, 0x85 | pl_ArcadeSetupFirstOpponent, pl_ArcadeSetupNextOpponent | BattleArcade_SetupFirstOpponent, _SetupNextOpponent |
| 0x86 | pl_ArcadeBattle | BattleArcade_StartBattle (Black 2's Subway battle event, the board's effects) |
| 0x87 | pl_ArcadeCleanupBattle | BattleArcade_CleanupBattle |
| 0x88 | pl_ArcadeCheckWonBattle var | BattleArcade_CheckWonBattle |
| 0x89 | pl_ArcadeTrainerWord word, slot, line | BattleArcade_PrintTrainerInfo (the line into a word; the script prints it) |
| 0x8A | pl_ArcadeApplyEffect | ApplyArcadeEffect |
| 0x8B | pl_ArcadeBoard first | OpenBattleArcadeApp (the board; then BA_FUNC_GET_ACTIVE_EFFECT has its effect) |
| 0x8C | pl_ArcadeLobbyFunction fn, arg, var | CallBattleArcadeLobbyFunction 0-3 |
| 0x8D | pl_ArcadeDeleteStreak type | DeleteActiveBattleArcadeStreak |
| 0x8E, 0x8F | pl_ArcadeLobbySelect type; pl_ArcadeSelectedSlots v1, v2, v3 | CallBattleArcadeLobbyFunction 4, GetBattleArcadeSelectedSlots |
`b2_script_check.py` knows their lengths; all 16 assemble and the checker walks them to their end.

### Proven offline (`python3 b2tools/platinum_arcade_check.py`)
1. `platinum_arcade_data.py check`: the 20 tables found in overlays 104 and 108 and equal in arcade_rules.c; 56 items the same
   numbers in Black 2; Black 2's `_s32_div_f` (524 B) found in Platinum's dump (below).
2. `platinum_arcade_host/run.sh`: Platinum's own C (extract.py copies it out of pokeplatinum: battle_arcade.c's rules, helpers,
   save, the scene's commands, the lobby's streak deletion, frontier_opponents.c, the records, Party_HealAllMembers, and the board's
   app: BattleArcadeApp_Init, _Main and _Exit with every state and the functions they decide through, its drawing stubbed) beside
   arcade_rules.c, with the same random numbers and the same choices. A Pokémon model both sides share, from Platinum's own
   personal data and experience tables (base stats by form, types, abilities, growth, natures, Shedinja). The board runs frame by
   frame on both sides: Platinum's app through its fade, its turning panels and its cursor, ours through RouletteOpen and Tick; the
   stop is touched on a frame the harness picks (or never: the 30 seconds), the cursor and the random state compared every frame.
   - sweeps: LowerHP's double (maxHP x 1.2, truncated) against ours (maxHP x 6 / 5) for every maxHP 0-65535; the cursor's frames
     for every speed; boards for every round 0-15, battle 0-30 and 9998-10000, performances 0-30, every speed, random cursor on
     and off;
   - 2,000 seeds: 12,000 challenges, 39,910 battles (33,217 won, 6,693 lost), 88 skipped by the board, 1,572 rounds (4,405 BP),
     Dahlia's battles, 3,141 rests resumed, 3,735 retires; 48,602 boards (9,658,240 cursor frames, 5,806 stopped by the 30
     seconds, 6,331 with the random cursor, 1,620 kinds with no effect), every one of the 32 effects drawn and applied, 156 swaps,
     288 free BP. Every field of the arcade, both parties, the battle's two sides and its AI, weather and Trainer, the saved
     challenge and the records compared after every step: 48,250,989 checks, 0 different.
3. Mutations caught (each alone, 200 seeds): a kind's weight, LowerHP's rule, the IV draws of the Pokémon's making, its whole
   draw, the sleep's turns, the swap's items, a turns score, Dahlia's 20 BP, the speed by round, a cursor speed, a round's and a
   battle's availability bit, a tier threshold, a Berry, the poison immunity, the freeze's first slot, the level up and down, the
   stats put back, the random cursor's panel, the 30 seconds, the weather's reset, the random cursor's hand-over, the saved speed,
   the opponent's heal, the AI's rounds, the opponent's items taken, the remainder by zero.
4. Compiled with Black 2's mwcc against main's decomp headers, one file at a time (`work/agents/plat-arcade/cc.sh`; again after
   plat-frontier-rooms, with main's pearlb2.h as it is now): arcade_rules.c, arcade_field.c, resident/plat_arcade_ext.c,
   resident/plat_frontier.c (the row), resident/plat_castle_ext.c (the block), plat_hall/hall_rules.c (the block), and with
   plat-arcade_decomp.diff btl_server_flow.c and leftovers.c: no errors (leftovers.c's one warning is older). `symcheck.py`: 538
   imports, all in main's link map but the linker's overlay ids (OVERLAY_380_ID is there, in a form the script doesn't read;
   OVERLAY_381_ID is the link's). Both diffs pass `git apply --check` in main's decomp.
5. The lobby: pearl_story translates MAP_BATTLE_ARCADE's Arcade commands (CallBattleArcadeLobbyFunction, GetBattleArcadeSelected-
   Slots, DeleteActiveBattleArcadeStreak; block "plat-arcade"); the file assembles and its 121 scripts pass b2_script_check.
6. The scene: `PEARL_VERSION=platinum python3 b2tools/frontier_rooms.py scripts MAP_BATTLE_ARCADE_CORRIDOR
   MAP_BATTLE_ARCADE_BATTLE_ROOM`: the corridor 1,896 commands, the battle room 1,820, 25 stubs each (below); both assemble and
   pass b2_script_check.

### Platinum's behaviour kept, that looks like a slip
- **A remainder by zero.** The board draws a kind of effect for each panel, then a random place among that kind's effects:
  `LCRNG_Next() % numEffectsInCategory`. In rounds 1 and 5 the field's kind has no effect, and its weight isn't 0. The DS's
  division routine (`_s32_div_f`, the same 524 bytes in Platinum's dump and Black 2's arm9) gives 0 for a remainder by zero, so
  the panel goes to the first effect of the next kind (the board's bonuses). arcade_rules.c does the same explicitly (DSMod); the
  harness's one edit to Platinum's text makes the host do the DS's (a host gives the dividend or traps).
- **A resumed challenge's opponents** are made from opponentMons Platinum never loads (LoadTrainersAndMonsFromSave fills a local
  copy): three empty Pokémon until the menu's Continue makes the next ones; and the four Pokémon it loads from the save draw their
  numbers with IVs Platinum never sets (as the Castle's: 0 here and in the harness).
- **The first battle's board** uses the tier of performance 0 (no battle yet): the player's kind is the likeliest (75%).
- **No battle** keeps the last battle's performance for the next board.

### The scene in its rooms (pearl_story.py and frontier_translate.py, blocks "plat-arcade")
The Arcade's scene runs in plat-frontier-rooms' picture rooms: the corridor (zone 725, MAP_BATTLE_ARCADE_CORRIDOR) and the battle
room (zone 726, MAP_BATTLE_ARCADE_BATTLE_ROOM). frontier_translate carries the Arcade's commands (PICTURE_HOSTED gets 'ARCADE');
pearl_story's handlers turn them into the ops:
- InitBattleArcade a, b, c, d, e, var -> pl_ArcadeInit a, b, c, d, e (the var is the link's); BattleArcade_LoadTrainersForRound ->
  pl_ArcadeLoadRound; CallBattleArcadeFunction -> pl_ArcadeFunction (the sprites', backgrounds', palettes' and emitter's functions
  do nothing in arcade_field.c); BattleArcade_SetupFirst/NextOpponent, _StartBattle, _CleanupBattle, _CheckWonBattle,
  ApplyArcadeEffect, FreeBattleArcade -> their ops.
- BattleArcade_PrintTrainerInfo n -> pl_ArcadeTrainerWord 0, n, 0, then a line of word 0 (the core's word line).
- OpenBattleArcadeApp -> pl_ArcadeBoard with the first of 32 lines appended to the room's text (BOARD_NAMES, in a run). Platinum's
  scene has faded to black before it and the app fades its own screens: here the room fades in under the window, and out after.
- SetItemDrawFlag (the items beside the board: sprites): nothing. AddToRecordValue RECORD_UNK_067 (the free BP into a Game Record,
  only in this scene): nothing, as IncrementGameRecord (Black 2 keeps its own records); GiveBattlePoints gives the BP.
- Sounds: the free BP's SEQ_PL_DON2 is followed by WaitFanfare, so a stub could hang: Black 2's SEQ_ME_ITEM [guess] plays.
  Stubs left (25 a room, each harmless: their waits are stubs too): the effects' SEQ_SE_PL_FR03, FR04, FR05 (with the particles)
  and the swap's SEQ_SE_DP_Z_SEARCH (no Black 2 sound chosen), the Wi-Fi selector's ChangeScript (the Multi is closed),
  CheckHeapMemory.

### Not done the way Platinum does it (or not done)
- **The particles** (battle_arcade_1.spa, battle_arcade_2.spa; 19 CreateParticleSystemEmitter, BA_FUNC_CREATE_EMITTER): the
  effects' sparkles (12 emitters a pair: ARCADE_EMITTERS_UNK_0-11 for the weather, fog and Trick Room; 24-47 for the effects on a
  side, by VAR_0x8005/8006) and Dahlia's entrance (ARCADE_2_EMITTER_UNK_0, 1). Black 2's field has no particle system like
  Platinum's frontier one; its field effects (the Gym's sparkles, the dowsing flash) don't match these. None is drawn; listed for
  the rooms.
- **The board's pictures** (the 16 panels' icons, the effect's big picture on the battle room's screen: BA_FUNC_SET_EFFECT_BACKGROUND,
  32 pictures in frontier_bg) and the Pokémon and item sprites beside it: not drawn (the names say the same).
- **Sleep's turns** are Black 2's battle's (its party status has none). **Fog** is Pearl's (no lines, no Cloud Nine exception).
  **Trick Room** has no animation nor its line in battle.
- **Dahlia**: her class (238), sprite (walker 124), Trainers 311/312 and songs are plat-frontier-rooms' (in main);
  patches/platinum_arcade.py reads the songs' installed ids from platinum_castle.songs (battle_music before it; 0 offline).
- **The Multi** (wireless and Wi-Fi) is closed, as the other facilities'. Black 2's own species (above 493) can't enter.
- Platinum's yes/no menus that start on No start on Yes (the core's note).

### What the link must check (the lead, main's decomp)
- Copy `src/pokebw2/` over the decomp tree: `include/pearlb2/plat_arcade.h`, `src/pearlb2/plat_arcade/{arcade_rules,arcade_field}.c`,
  `src/pearlb2/resident/plat_arcade_ext.c`, `src/pearlb2/resident/plat_frontier.c` (one row, one include),
  `src/pearlb2/resident/plat_castle_ext.c` (one block, one include); then `git apply plat-arcade_decomp.diff` (with
  plat-castle_decomp.diff: they touch pearlb2.h in different places).
- The link: `git apply src/pokebw2/plat-arcade_link.diff` in the decomp (made against main's decomp after plat-frontier-rooms;
  `git apply --check` passes). `tools/pearlb2/link_overlays.py`: `PLATARCADE = 381`, `--platarcade`, the overlay after
  `platcastle` in the list, `OV381 : ORIGIN = AFTER(OV084, OV085) > build/arm9_ov381.bin` and its section block (as the Castle's
  380); `configure.py`: `"platarcade"` in overlay_objects, `("platarcade", "src/pearlb2/plat_arcade/*.c")`, its objects in the
  overlays' list and variables, `--platarcade $platarcade` in the link rule. Tried on a copy: link_overlays.py writes OV381's
  MEMORY line, `OVERLAY_381_ID = 381`, the .ov381 section and `-overlay OV381` with the two objects. `pearlb2_overlays.py` knows
  381 (its gimmick-address check covers it); 378-380 are linked before it (the table is by id).
- The room: the gimmick overlays' address starts after OV084 (0x21EEC80) and overlay 146 starts at 0x21F59E0: 28,000 B. Overlay
  381 is about 11,350 B (mwcc's objects). The resident section grows by about 0.5 KB (plat_arcade_ext.c).
- `OVERLAY_381_ID`, `OV381_TEXT_START`, `gPlatArcadeTable` in the link; the layout check passes; `decomp.py changed` lists
  BtlServerFlow_StartBattle (the call's target) and, with the Castle's, BtlMain_ProcMain.
- Platinum's build list: `platinum_arcade` after `platinum_castle` (and so after battle_music, for Dahlia's songs).

### For the combined ROM (overlay 381 linked, patches/platinum_arcade.py in the build list)
1. Entering: the Arcade's lobby (MAP_BATTLE_ARCADE), the Single attendant: Info and Single/Double; two of the same species are
   refused, Mewtwo can't be picked; pick three, the save, the walk to the corridor (zone 725) and the battle room (zone 726). "First,
   I'll need to hold on to any items": the three hold nothing in battle (the field party keeps its items).
2. The board: the room fades in, the window at the top, 3, 2, 1 in every panel (24 frames each), then 16 names and a dark panel
   running left to right, top to bottom; A stops it (or a touch, or 30 seconds); every panel shows the effect for a moment; the
   window closes and the room fades out. Look for: the names' fit (Sandstorm the widest), the cursor's colour (white on dark), no
   flicker, the sounds, the room under the window (nothing drawn where the board's pictures were).
3. Effects of each kind (round 1 has poison, paralysis, burn and a Berry on either side, speed, random cursor, no event; later
   rounds the rest):
   - the opponent's: Foe PSN, the opponent's three poisoned in battle (a Steel or Poison type not: if all three are, "a lucky
     break" line); Foe Lv+3: Lv. 53 in battle; Foe Berry: each holds the Berry;
   - the player's: Own HP- (about 80% HP in battle), Own SLP (one asleep), Own Lv+3 (Lv. 53 in battle, Lv. 50 again after);
   - the field's (round 2 on): Sun, Rain, Sandstorm, Hail from the battle's start for the whole battle; Fog (round 4): moves miss
     more; Trick Room (round 4): the slower moves first for five turns, then "The twisted dimensions returned to normal!";
   - the board's: Speed Up (the next board faster), Random (the next board's cursor jumps), Swap (round 5: the player battles with
     the opponent's three), 1 BP and 3 BP (the BP window; Black 2's item jingle, then the script goes on), Skip (round 5: no
     battle, the streak goes up).
4. A streak: seven wins: "You have cleared your seventh battle!", 2 BP for round 1; Continue in the lobby: round 2's board offers
   the weather; the board's speed starts at 3 again each round (round 5: 4, round 8: 5).
5. Rest after a win: the save, the reset, Continue: the menu, then the next battle with the same held items and board speed.
6. Dahlia: a Single streak at 20 (records 95 = 20 and a round started, or play): "the Arcade Star approaching", her intro, her
   battle with the full AI and her songs; 20 BP. Needs her class, sprite, Trainers 311/312 and lines installed (plat-frontier-rooms).
7. Look for: overlay 381 loading in each Arcade zone (a stop there means something sits at the gimmick address), the board's window
   over the room, the battle's weather, the swap's parties.

## The Frontier's shared Pokémon setup (plat-arcade, 2026-11-07)
Platinum makes every opponent's Pokémon, in every facility, with `FrontierPokemon_InitPokemon` (frontier_opponents.c), which calls
pokemon.c's `Pokemon_InitWith` with the set's personality, OTID_NOT_SHINY and the IVs as one number. That draws the game-wide
LCRNG: a trainer id until it isn't shiny with the personality (2 numbers a try), then, for IVs of 32 or more as one number (every
facility's: the lowest is 3 each), two numbers for random IVs. Both values are overwritten after (the set's trainer id, its IVs),
but every draw after them depends on them.
- **The Tower**: no difference. Its rules draw from its own generator (unk_02049D08.c BattleTower_GetRandom: the challenge's
  state, sub_0206BFF0; LCRNG_Next only for the Wi-Fi mode 6, closed), never the LCRNG these draws move; the Tower harness's
  LCRNG_Next aborts if called and never is.
- **The Factory**: no difference. Its harness models FrontierPokemon_InitPokemon with these draws (platinum_factory_host/sim.c)
  and factory_rules.c makes them (InitPokemonRandom).
- **The Castle**: no difference. Its harness's Pokemon_InitWith draws them (platinum_castle_host/sim.c) under Platinum's own
  FrontierPokemon_InitPokemon, and castle_rules.c makes them (InitPokemonRandom).
- **The Hall: fixed.** Its harness's Pokemon_InitWith drew nothing, and hall_rules.c made no such draws: both agreed with each
  other, not with Platinum. With the harness drawing as Platinum's code does (platinum_hall_host/sim.c, block plat-arcade) and
  hall_rules.c unchanged, 200 seeds gave 130,613 differences (the next opponents' Trainers and Pokémon). hall_rules.c now draws them
  where BattleHall_SetupBattle makes each Pokémon (PlatHall_MakeOpponents, block plat-arcade): 2,000 seeds, 5,618,932 checks, 0
  differences. The Hall's opponents after the first battle of a challenge change on the DS (they are now Platinum's).
- **The Arcade**: made from the start (InitPokemonRandom; the harness's model draws them; a mutation without them is caught).
- **The Factory's opponent sprite** (plat-frontier-rooms' question): factory.c passes `trainer->trainerId` of Black 2's
  BSubwayTrainer to PearlB2_TowerObjCode, which takes a class. It is right: BtlInst_MakeRomTrainer (ov012 fld_btl_inst_tool.c) puts
  the Trainer file's first value, the class, in that field (`trainer->trainerId = trainerData[0]`; the id + 1 goes in unk00), as
  castle_field.c reads it too (`dest->trainerClass = trainer->trainerId`), and the slot is Platinum's (currentBattle + slot x 7,
  BattleFactory_GetNextOpponentObjectID). No change.

## The Tower lobby's results machines (plat-records, 2026-11-08)
Gen 4's `OpenBattleTowerRecordsApp isRankingsScreen, resultsType` (pokeplatinum scripts_battle_tower.s BattleTower_ResultsMachine;
Pearl's file 358 the same) opens the records app (pokeplatinum applications/frontier/tower_records.c). With isRankingsScreen
FALSE it shows the player's own results. Ours gave BSubwayCmd_Tool 111: Black 2's records screen (overlay 141), a list of
other players' records. Now it shows the same rows as a message, in the app's own words. All three versions (one command).

- **Where.** pearl_story.py `h_tower_records` (block "plat-records") adds eleven lines to the lobby's text and gives
  `pl_TowerResults rankings, type, first` (pearl_story.inc, block "plat-records"). With rankings not 0 (the Wi-Fi leaders
  machine, after 0x1E4 found leaders: never, the Wi-Fi rooms are closed) Black 2's leaders screen stays.
- **The words.** The records app's bank 17 (pokediamond narc_0017.gmm, pokeplatinum battle_tower_records_app.json): lines 0-21
  are the same in Pearl, Diamond and Platinum, so each version reads its own dump and gets the same text. The rows' colors are
  the app's palette, dropped. A two-row name ("Single\nRecord") is one row here.
- **The numbers.** Black 2's Battle Subway keeps the Tower's results (its score block, by play mode; the Tower's 0 Single,
  1 Double, 2 Multi, 3 link Multi, 4 Wi-Fi are Black 2's modes 0-4). Each room: the latest streak (BSubwayCmd_Tool 6,
  BSubwayScoreData_GetStreak, set at a loss and after seven wins), the longest (the Frontier core's record 2 x mode,
  pl_FrontierStatGet: BSubwayScoreData_GetMaxStreak; no Black 2 command reads it by mode), and PREV or CURRENT: CURRENT while
  the mode has a stage (BSubwayCmd_Tool 38, BSubwayScoreData_HasStage: set when a challenge starts, raised after seven wins,
  cleared at a loss and at a disqualification), as Platinum's streak flag (WifiBattleTowerRecord bit 8 + mode: set after seven
  wins, cleared at a loss). The Wi-Fi rank: BSubwayCmd_Tool 27 (BSubwayScoreData_GetWifiRank, 1 from a new game). Every number
  the app shows is kept; none is left out.
- **What each shows** (pages of Black 2's two-row window; {be00} scrolls one row, {be01} clears; text line numbers: Pearl's
  lobby 128-138, Platinum's 144-154):

| Machine (type) | Message 1 | Message 2 |
|---|---|---|
| Single and Double (0) | Battle Room Results / Single Record, then PREV (or CURRENT) Win streak: N / RECORD Win streak: N | Double Record / PREV (or CURRENT) Win streak: N, then RECORD Win streak: N |
| Multi (1) | Multi Battle Room Results / Multi Record, the same two rows (mode 2) | Link Record, the same (mode 3: the wireless Multi, closed: 0) |
| Wi-Fi (2) | Wi-Fi Battle Room Results / Current Rank, then RANK N | Wi-Fi Record, the same two rows (mode 4: closed, 0) |

  Source lines (bank 17): titles 0, 1, 2; room names 3, 6 / 4, 7 / 5, 8; PREV 9, CURRENT 10, RECORD 11, RANK 12; "Win streak:
  N" 13 (buffer 0 the latest, 1 the longest); the rank's number 14.
- **The machines.** Pearl's lobby has four: the Single and Double results at (9, 5), the Multi results at (5, 5), the Wi-Fi
  results at (13, 5), the Wi-Fi leaders at (17, 5); each read facing north from the tile below. Platinum
  keeps only the Wi-Fi results (17, 5) and the leaders (21, 5): its Single and Multi results scripts are unused leftovers of
  Pearl. Platinum's machine at (13, 5) is the Frontier's records machine (global 10450: `OpenFrontierRecordsApp` for the
  Tower): "The Frontier's records machines", below.
- **Checks.** `PEARL_VERSION=platinum python3 b2tools/pearl_story.py all`: 482 zones, 0 with problems. Pearl's lobby
  (`python3 b2tools/pearl_story.py zones MAP_BATTLE_TOWER_LOBBY`) and Platinum's assemble and pass b2_script_check at their
  map scripts' levels; the bytes decode to the commands above (modes 0-4, records 0-8, the eleven lines); every line fits
  (139 px at most of 224, two rows a page: text_check.line_problems). version_check ok (the lobby's script and text: 1.0.1 rows).

Not done the way Platinum does it:
- A message, not the app's screen (Black 2 has no such screen). PREV or CURRENT is a line of its own for each case (four
  lines for each two-room machine).
- After a disqualification (reset without saving), Platinum sets the latest streak to 0; Black 2 keeps the streak saved at
  the last loss or seven wins (its function 7 only clears the stage). So that case showed PREV with the older number.
  Since plat-fix2 (2026-11-11, Platinum: version.TOWER_DISQUALIFY_ZERO) the latest streak is 0 there too, as Platinum's:
  "The last differences" below. Pearl and Diamond keep Black 2's rule for now.

### For the combined ROM (zone 443, the Tower lobby)
1. Pearl and Diamond: stand at (9, 6) facing north and read (9, 5). Fresh save: "Battle Room Results / Single Record", then
   "PREV Win streak: 0", "RECORD Win streak: 0"; then "Double Record", the same. No fade to black, no other screen; the window
   closes on A and the player can walk.
2. Pearl: (5, 5) from (5, 6): "Multi Battle Room Results / Multi Record", then "Link Record" (0 and 0). (13, 5) from (13, 6):
   "Wi-Fi Battle Room Results / Current Rank", "RANK 1", then "Wi-Fi Record" (0 and 0).
3. Pearl: (17, 5) from (17, 6): "There doesn't appear to be any data yet..." (the leaders machine, unchanged).
4. Platinum: (17, 5) from (17, 6): the Wi-Fi results, as item 2's; (21, 5) from (21, 6): "There doesn't appear to be any data
   yet...".
5. After a Single challenge's seven wins (back in the lobby): the Single row says "CURRENT Win streak: 7" and "RECORD Win
   streak: 7". After a loss in the next set's third battle: "PREV Win streak: 9", "RECORD Win streak: 9". The Double row stays 0.
6. A Multi challenge with a partner: the Multi machine's Multi row moves the same way (Platinum: no placed machine shows it).

## The Frontier's records machines (plat-records, 2026-11-08)
Platinum's records machine in each lobby (global scripts 10450-10455, pokeplatinum scripts_battle_frontier_records.s) asks
"Which record would you like to see?" (SINGLE, DOUBLE, MULTI, CANCEL) and opens `OpenFrontierRecordsApp challengeType,
facility, species` (applications/frontier/records/main.c DisplayRecords): the facility's own records for that type. It was a
stub (fade out, nothing, fade in). Now the same rows show as messages, then the question comes back. Platinum only.

- **Where.** pearl_story.py block "plat-records" (after "plat-stubs"): `h_frontier_records` reads which facility the machine's
  entry sets (its SetVarFromValue of the facility var), adds that facility's lines to the zone's text and gives
  `pl_FrontierRecords kind, type, first` (pearl_story.inc, block "plat-records"). The screen's fade-out (before the Call), its
  ReturnToField and its fade-in are dropped (`_frontier_records_drops`): the message is on the field. The menu's answer (the
  type) is read when the machine runs.
- **The words.** The app's bank 627 (pokeplatinum battle_frontier_records.json), by line: 21-25 the facilities, 26-28 Single,
  Double, Multi Record, 29 PREV, 30 CURRENT, 31 RECORD, 32 Multi w/Trainer, 33 Multi w/friend, 34 Level 50, 35 Open Level, 36
  Rental/Trade, 38 and 42 "Win streak: N", 40 a number, 41 "N CP", 43 "Games cleared: N". The app's column titles become row
  words ("Rental/Trade N"); "Castle Points" (37), the CP column's title, is left out ("N CP" has the unit).
- **The numbers.** The Frontier core's records (pl_FrontierStatGet: Platinum's BattleFrontierStats ids; the Tower's 0-9 are
  Black 2's Subway records) and the facilities' streak flags (pl_FrontierStreakFlag, Platinum's bits), which factory_rules.c,
  castle_rules.c and arcade_rules.c write as Platinum's battle_factory.c, battle_castle.c and battle_arcade.c do. CURRENT when
  the flag is set, else PREV, as the app. Checked in the assembled bytes:

| Facility (machine) | Type t | Rows (stat ids) | PREV or CURRENT |
|---|---|---|---|
| Tower (lobby 443, (13, 5)) | Single, Double | PREV/CURRENT Win streak (Black 2's latest, mode t), RECORD Win streak (stat 2t) | the mode's stage (BSubwayCmd_Tool 38) |
| Tower | Multi | Multi w/Trainer (mode 2: stats 4, 5), Multi w/friend (mode 3: 6, 7; the wireless Multi, closed) | the same |
| Factory (688, (22, 6)) | each | Level 50, then Open Level (o 0, 1): Win streak 11+8t+4o and Rental/Trade 13+8t+4o; RECORD 10+8t+4o and 12+8t+4o | flag bit 4o+t |
| Castle (690, (6, 8)) | each | Win streak 71+8t and N CP 72+8t; RECORD 70+8t and N CP 74+8t | flag bit t |
| Arcade (691, (16, 5)) | each | Games cleared 95+2t; RECORD Games cleared 94+2t | flag bit t |

- **The Hall** (689, (7, 8)): left out. Its records are a species' (the app: "{species}'s record", the latest streak if the
  species is the latest one, and the species' record from BattleHallWinRecords). The machine's species list
  (ShowBattleHallRecordMonSelectionMenu) answers EXIT here (plat-stubs), so its OpenFrontierRecordsApp is never reached, and
  no script command reads a species' record (PlatHall_GetRecordForSpecies has no op): it needs C (a species list and a
  record op). Its copy stays a counted stub with its fades.
  Since plat-fix2 (2026-11-11, version.HALL_RECORDS_MACHINE) it works: "The last differences" below.
- **Checks.** `PEARL_VERSION=platinum python3 b2tools/pearl_story.py all`: 482 zones, 0 with problems. The five lobbies (443,
  688-691) assemble and pass b2_script_check at their map scripts' levels; the bytes give the stat ids and bits above and show
  every added line; every line fits (158 px at most of 224, two rows a page). version_check ok (Pearl and Diamond unchanged).

Not done the way Platinum does it:
- Messages, not the app's screen; a column title is a word before its number. PREV or CURRENT is a line of its own (two
  copies of each message).
- The Hall's records (above).

### For the combined ROM (Platinum; each machine read facing north from the tile below)
1. The Tower lobby (443), (13, 5): pick SINGLE. "Battle Tower / Single Record", then "PREV Win streak: 0", "RECORD Win
   streak: 0"; A: back to "Which record would you like to see?" and the menu. MULTI: "Battle Tower / Multi Record", "Multi
   w/Trainer", the two rows; then "Multi w/friend", the two rows (0). CANCEL leaves. No fade to black at any point.
2. After seven Tower Single wins: SINGLE shows "CURRENT Win streak: 7", "RECORD Win streak: 7"; DOUBLE stays 0.
3. The Factory (688), (22, 6): SINGLE: "Battle Factory / Single Record", then "Level 50 / PREV Win streak: N", "Rental/Trade N",
   "RECORD Win streak: N / Rental/Trade N", then "Open Level" the same. After a Level 50 Single challenge won twice, one
   trade, lost in the third battle: Level 50's "PREV Win streak: 2", "Rental/Trade 1"; Open Level stays 0.
4. The Castle (690), (6, 8): DOUBLE: "Battle Castle / Double Record", then "PREV Win streak: N / N CP", "RECORD Win streak: N /
   N CP". After a Double challenge: the CP it ended with.
5. The Arcade (691), (16, 5): MULTI: "Battle Arcade / Multi Record", "PREV Games cleared: N", "RECORD Games cleared: N".
6. The Hall (689), (7, 8): the letters, then the species with a record (plat-fix2: "The last differences", its checklist).

## The last differences (plat-fix2, 2026-11-11)
The lead's list of what still differed from Platinum before Platinum 1.0. Offline (no ROM built); the checklist is at the end.

### The two opponents' lines (version.LINK_STARTS_CANCEL, TOWER_INTRO_ONE_A)
- **What Platinum does.** The 30-frame lines (PrintTrainerIntro, then WaitTime 30, no A) are only in the Multi with a friend
  (BF_FUNC_IS_MULTIPLAYER_CHALLENGE and the Hall's, Castle's and Arcade's: the wireless and Wi-Fi Multi; the Tower's link
  Multi). A Double challenge has one opponent and its line waits for A; the Tower's Multi with a partner waits for A at each
  of its two lines. Ours do the same, so nothing reachable waited for an A where Platinum doesn't.
- **What was wrong.** The two-opponent path was reachable through a hole: the Multi attendant's "launch wireless" Yes went
  to StartBattleClient / StartBattleServer, which were stubs, so the result var kept the Yes (0 = connected) and a Multi
  challenge started with no partner (the four lobbies; also the Tower's link Multi, the Poffin house, the Contest Hall and
  the League's 2F). Now (Platinum, LINK_STARTS_CANCEL) both answer COMM_CLUB_RET_CANCEL (1), as when a player backs out of
  the search with nobody there: back to "join a group or become the leader", then EXIT. The 30-frame lines stay as they
  are (the balloon takes an A, then 30 frames): nothing reaches them now, as the wireless Multi is closed.
- **The Tower's line asked for two A's.** PrintBattleTowerIntroMessage (BSubwayCmd_Tool 352, Black 2's EventBSubwayTrainerMsg)
  waits for A itself, and the WaitABPress after it asked again, as plat-test found for the four facilities. Dropped for
  Platinum (TOWER_INTRO_ONE_A): the single room's line (zone 619's file 1592, both copies) and the multi room's two (file 1593,
  four copies). Black 2's own Subway script has no wait after tool 352.
- **Pearl and Diamond** have the same two gaps (their Poffin house, Contest Hall and League 2F stubs; their Tower rooms'
  second A). Their output must not change now: both rows are off for them, for a later release.

### The Galactic HQ lab's player at (8, 8)
Not a look fault. (8, 8) is a solid tile: Platinum's own collision makes the containment unit's block x 7-9, z 8-10 solid
(Uxie stands at (8, 10) inside it). plat-test's start (env/9s.env, TEST_START=507,8,8) put the player there, inside the
unit's back; no script moves the player there (the room's scripts only turn the player on the spot and walk one step north
from (8, 13)). From the nearest reachable tile north of the unit, (8, 7), the player is whole (pearl_rooms_view's model:
0 hidden pixels); from (7, 8) or (9, 8) the player does not stand either (solid). Nothing changed.

### The Battle Tower after a reset without saving (version.TOWER_DISQUALIFY_ZERO)
- **Platinum's rule.** The lobby's frame script finds a challenge that was saved when it started but not when it stopped
  (BT_FUNC_UNK_04: the "saved properly" flag clear), says "didn't save before quitting" and calls BT_FUNC_UNK_14
  (unk_02049D08.c sub_0204A064): the mode's streak flag (WifiBattleTowerRecord bit 8 + mode) goes, its room number is 0,
  its latest streak (BattleFrontierStats_GetTowerLatestStreakIndex) is 0, and the challenge seed moves on (sub_0206C02C).
  The record (the longest streak) stays.
- **Ours before.** Tower function 14 was Black 2's BSubwayCmd_Tool 7 (func_ov033_0217b86c): the round and the stage reset
  (so no streak goes on, and PREV shows), but the latest streak kept the value saved at the last loss or seven wins.
- **Now (Platinum).** `pl_TowerDisqualify var` (pearl_story.inc), the Frontier core's op 0x08 (FRONTIER_OP_TOWER_DISQUALIFY,
  src/pokebw2: include/pearlb2/plat_frontier.h and src/pearlb2/resident/plat_frontier.c, also in plat-fix2_decomp.diff):
  the round, the stage and the latest streak (BSubwayScoreData_SetStreak 0) of the play mode, which goes in var as before
  (the lobby checks 4, Wi-Fi, for its demotion line). tower_script.py gives it for function 14 when the row is on.
- **Not as Platinum.** The challenge seed: Black 2's generator draws the opponents (as the core says above).
- **Pearl and Diamond.** Their lobby runs the same function 14 after the same line, so Pearl's own rule is most likely
  Platinum's (pokediamond doesn't decompile it: not proven). They keep Black 2's rule now (the op is Platinum's core), for a
  later Pearl release: the row and an op in Pearl's tower.c would do it.
- **Checked.** The lobby (zone 443, file 1588) regenerated: the one line changes (BSubwayCmd_Tool 7 -> pl_TowerDisqualify
  PVAR_800C), it assembles and decodes (b2_script_check knows op 0x08: 2 argument bytes); plat_frontier.c passes clang's
  type check against the decomp's headers (`-D__thumb -std=gnu99` with compile_flags.txt; the decomp's own copy needs the
  same flags). Compiled with mwcc in the decomp (pearlb2-plat-fix2 a6eee78c57, on 89bb3e2824): below.

### The Battle Hall's records machine (version.HALL_RECORDS_MACHINE)
- **Platinum** (scripts_battle_frontier_records.s FrontierRecords_BattleHallMenus): SINGLE, DOUBLE, MULTI; then "<species> is on
  a challenge now!" (a streak going) or "Which Pokémon's record would you like to see?"; the letters (ABC .. YZ, EXIT); then
  ShowBattleHallRecordMonSelectionMenu (ov5_021F6454.c): the species of those letters with a record of the type, in its
  alphabetical lists (zukan_data.narc members 18-26: every species 1-493 once), then EXIT; a species opens the records screen
  (DisplayBattleHallRecord): "Battle Hall / <type> Record", "<species>'s record", PREV "Win streak: N" (the latest streak if
  the species is the type's latest, else 0), RECORD "Win streak: N" (the species' win record). The Hall's screen shows PREV
  only, never CURRENT. Back to the species list ("Which Pokémon's record...").
- **Ours.** The letters as before; the species list is Black 2's list menu (pearl_story h_hall_record_mons_list):
  `pl_HallRecordList type, letters` (op 0x4F, hall_field.c AddRecordRows) appends the species of the group with a record of the
  type, in Platinum's order (the nine lists read from the dump, sAlphaSpecies), then EXIT (menu entries line 12, value
  MENU_CANCEL, as B). Black 2's script list holds 32 rows: a longer list (STU has 97 species) gets a list of its own size. A
  species shows its record as a message (`pl_HallRecordShow type, species, first`, op 0x50 PLATHALL_OP_SPECIES_RECORD for the
  two numbers): "Battle Hall / Single Record", then "<species>'s record / PREV Win streak: N", then "RECORD Win streak: N"
  (bank 627 lines 24, 26-28, 39, 29, 31, 38; the zone's lines 151-153). The screen's fades are dropped, as the others'.
- **Not as Platinum.** A message, not the screen (Black 2 has none). The letters' and the species list's cursor and scroll
  aren't kept (Black 2's list menu opens at the top; ShowListMenuRememberCursor's approximation, plat-stubs). The Multi has
  no records here (the wireless Multi is closed: the win records keep Single and Double), so MULTI lists EXIT only, as a
  Platinum player's who never played a wireless Multi.
- **Checked.** The Hall's lobby (689, file 1854) regenerated: the species list and the records' message in place of the
  stub; it assembles and decodes (b2_script_check: ops 0x4F, 4 bytes; 0x50, 8); the three lines fit (133 px at most of 224,
  two rows a page). hall_field.c passes clang's type check with the decomp's headers (`-D__thumb -std=gnu99`); every function
  it calls is in symbols.txt (InitListMenuOptionHeap, AppendListMenuOption: ov036; ListMenuCore_FreeOptionList,
  ListMenuCore_GetFirstFreeIndex: main). Overlay 379 (19,040 B, 8,928 B left before overlay 146) grows by about 1.3 KB (the
  table 1,006 B).
- **Compiled** (the decomp's branch pearlb2-plat-fix2, in external/pokebw2_plat-dw3, from 89bb3e2824: a6eee78c57 the Tower's op,
  c2b0227997 the Hall's ops; the diff applied as it was, nothing had moved since 4d8a31fddf): ninja's incremental build has no
  warnings; `decomp.py check`: layout kept (48,572 symbols); every import of hall_field.o, plat_frontier.o and plat_hall_ext.o
  is in the link map (OVERLAY_379_ID comes from the link); overlay 379 is 20,480 B (was 19,040), 7,488 B before overlay 146;
  version_check ok. Not run on a DS yet.
- **The decomp.** `src/pokebw2/plat-fix2_decomp.diff` (applies to pearlb2 4d8a31fddf: `git apply` checked) has the four files:
  include/pearlb2/plat_frontier.h, src/pearlb2/resident/plat_frontier.c (the Tower's op 0x08), include/pearlb2/plat_hall.h,
  src/pearlb2/plat_hall/hall_field.c (ops 0x4F, 0x50). The copies under src/pokebw2/ are those files with the change (the
  Hall's two were synced to the decomp first: they were older than its pearlb2).

### The Frontier gate's roof at (48, 52): a decision for the user (nothing changed)
- **What it is.** The gate's door on the Frontier side is the warp (48-49, 52) under the north edge of the gate's octagonal
  roof (Platinum's model). The player arrives on the door tile and steps to (48, 51). Offline, Platinum's look against ours
  (`room_look_check.py --pair OUT 559 48,Z --people --dir 0`: Platinum's data and its camera on top, ours below;
  work/agents/plat-fix2/shots/frontier_gate_*.png): on (48, 52) Platinum shows the top of the hair over the roof's red crest,
  ours nothing; on (48, 51) Platinum shows the head and shoulders, ours the hair; on (48, 50) both show the whole player.
  So ours hides the player one step longer than Platinum, as plat-test saw ("two steps").
- **Why: the camera, not this place.** Platinum's Frontier camera (CAMERA_TYPE_ZOOMED_IN: 515 units away, 54.7 degrees, a
  10.5-degree view) is almost orthographic. Ours is Black 2's camera 0 at the same pitch (the user's camera, 2026-10-26: Black 2's
  distance, zoom and sprite size): 237 units away with a 40-degree view, so the rays to the sprite above the screen's centre
  are up to ~7 degrees flatter and pass under the roof's edge; Black 2's people are also 28 units for 32 px where Pearl's and
  Platinum's are 32. Every north door under a deep roof does the same (notes/MAP_LOOK.md "The roof at north doors": the door
  tile shows only the cap in Pearl's look too). The roof is in front of the player in the world, so no depth rule helps:
  only the camera or the people's size would.
- **For the user.** (a) Keep it (one step more under the roof than Platinum at north doors, like the rest of the game), or
  (b) the Frontier with Platinum's own camera numbers (maplook's `camera` fix for one zone: against the rule of whole-world
  fixes and the 2026-10-26 camera decision), or (c) bigger people everywhere (32 units: 14% larger on screen). Nothing was
  changed: (a) unless the user says otherwise.

### For the combined ROM (plat-fix2)
1. The link's starts (LINK_STARTS_CANCEL). The Factory (688), the Multi attendant at (23, 6): MULTI, a level, the save, then
   JOIN GROUP, "launch wireless" YES: back to "join a group or become the leader" (no Multi starts, no corridor); BECOME
   LEADER the same; EXIT ends ("We hope to see you again"). The same at the Hall's (689) Multi attendant (6, 10), the Castle's
   (690) (5, 10), the Arcade's (691) (15, 5), and the Tower lobby's (443) Multi attendant (11, 5) on its "with a friend" path.
2. One A (TOWER_INTRO_ONE_A). A Tower Single challenge, room 619: the opponent's balloon closes on one A and the two step
   together at once (before: a second A). A Multi challenge with a partner, room 620: each opponent's balloon one A.
3. The reset rule (TOWER_DISQUALIFY_ZERO). A Single challenge: win a set of seven (the records machine at (13, 5): "CURRENT Win
   streak: 7"), start the next set, win two, turn the power off without saving, Continue: in the lobby "didn't save before
   quitting"; then (13, 5) SINGLE: "PREV Win streak: 0" (before: 7) and "RECORD Win streak: 7" (or 9 if the two were
   saved by a rest: the record is the record).
4. The Hall's records machine (HALL_RECORDS_MACHINE), the Hall lobby (689), (7, 8) read from (7, 9). No records: SINGLE, any
   letter: a list with EXIT only; EXIT and B go back to the letters; the letters' EXIT goes back to SINGLE/DOUBLE/MULTI. After
   a Single challenge with, say, Pikachu (two wins, then a loss): SINGLE, "Which Pokémon's record would you like to see?",
   PQR: "Pikachu", "EXIT"; Pikachu: "Battle Hall / Single Record", then "Pikachu's record / PREV Win streak: 2", then
   "RECORD Win streak: 2"; A: back to "Which Pokémon's record...?" and the list. While a streak is going (a challenge saved
   by a rest): "Pikachu is on a challenge now!" before the letters. DOUBLE lists Double records only; MULTI EXIT only.
   Look at the list window: at the right edge, names whole; with more than six rows it scrolls.
5. No change, nothing to test for plat-fix2: the Galactic HQ lab's (8, 8) (a solid tile), the Frontier gate's roof (a
   decision for the user), the follower (not found: the place and a frame are needed).
