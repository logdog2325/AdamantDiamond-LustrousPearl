# Platinum's story: handoffs between chapters

The shape of notes/STORY_HANDOFFS.md, for Platinum's chapters (notes/PLATINUM_CHAPTERS.md). Each chapter agent adds,
in its own section, what another chapter must know: a flag or var it sets that another chapter's zone reads, a scene it
left for the owner of another zone (a "foreign beat"), what the next chapter's test start needs, a generator change
others should use. Read the sections of the chapters before yours first. One section per chapter; never edit another
chapter's section.

Story order offline: `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py N --next` runs chapter N's beats
(data/platinum/story_flow.json) from its test start and compares its end with chapter N+1's start.

## Chapter 1 (plat-ch1, 2026-11-07)
- **Story order offline, both ways:** `PEARL_VERSION=platinum python3 b2tools/platinum_flow_compare.py 1` (also `90`, or `all`)
  plays each beat as Platinum's own scripts do (the dump) and as the generated files do, follows every branch it can't decide, and
  reports where the two end differently (saved flags and vars, zone, Trainers battled by Platinum's number). Beats:
  data/platinum/beats/<N>.json, or a chapter's row of data/platinum/story_flow.json (read as they are: talk N is the person
  with local id N). Chapter 1's 20 beats and chapter 90's 36 pass. Run it after `pearl_story.py chapter N`.
- **What chapter 1 leaves** (both sides agree; chapter 2's TEST_SET has all of it now, PFLAG_0087 added by the lead):
  PVAR_40F9 1, PVAR_40A5 1, PVAR_40A4 7 (Twinleaf's on-transition turns 6 into 7 when the player leaves home), PVAR_4070 2,
  PVAR_40E6 1, PVAR_40A3 1, PVAR_4086 4, PVAR_4082 1, PVAR_4095 1, PVAR_4071 2, PVAR_40A6 1; PFLAG_0087, PFLAG_008F, PFLAG_0090,
  PFLAG_00EA, PFLAG_0172, PFLAG_0176-0179, PFLAG_017D, PFLAG_0196, PFLAG_0199, PFLAG_01F2, PFLAG_02C4, PFLAG_0993 and the new
  game's flags; Black 2's 2402 (Pokédex), 2403 (Running Shoes).
- **Later chapters' scenes in chapter 1's zones** (plat-ch1 regenerates these zones; the owners test them there):
  - Chapter 8: Lake Verity (our MAP_LAKE_VERITY = Platinum's LAKE_VERITY_LOW_WATER): Rowan (object 0, hide PFLAG_0175) and the
    assistant (object 1, PFLAG_0194) appear after Lake Valor; Canalave's script clears their flags (scripts_canalave_city.s).
    Their talk scripts (ProfRowan, Counterpart) are in the generated file.
  - Rowan in his lab is shown and hidden from other zones: Oreburgh Gym (chapter 2) and Canalave Gym (chapter 7) set
    FLAG_HIDE_SANDGEM_TOWN_LAB_PROF_ROWAN, Jubilife (chapter 3) and Lake Acuity (chapter 8) clear it.
  - Chapter 9/10: the lab's OnFrame_ReturnedFromDistortionWorld (script 15) runs when VAR_SANDGEM_TOWN_LAB_STATE (PVAR_40A6) is 2
    (Sendoff Spring sets it); Sunyshore's on-transition hides the lab's counterpart at 2 and 3.
  - Chapter 11: Mom's post-game scene (player's 1F OnFrame_Postgame, script 11) runs when VAR_PLAYER_HOUSE_POSTGAME_STATE is 1
    (the Hall of Fame sets it); the National Pokédex and the Poké Radar (item 431) in the lab.
- **Generator changes others will see when they regenerate** (pearl_story.py, block "plat-ch1"; pearl_story.inc; Pearl's output
  unchanged, version_check ok):
  - Platinum's first battle (StartFirstBattle with a Trainer): pl_StartFirstTrainerBattle is Black 2's own first battle now
    (CallTrainerBattle flags 1: no loss text, no money lost, no black-out; CallTrainerBattleEnd win or lose), CheckWonBattle after
    it only reads the result (pl_CheckWonFirstBattle), and the loss branch's ReturnToField and FadeScreen in are dropped. Before,
    a loss showed Black 2's "out of usable Pokémon" text, took money, and faded in white. Only Route 201 uses it.
  - A dynamic sprite var compared with a graphics id (CompareVarToValue on 0x4020-0x402F) compares with that id's Black 2 code,
    the value SetVarFromValue wrote. Users: the Centers' daily Trainers (file 1138) and the Battleground (file 1027, chapter 11).
  - A Trainer battled by a var (StartTrainerBattle VAR): the SetVarFromValue that fills that var takes the Trainer's Black 2 id
    (PTRAINER_n). Users: the daily Trainers, the Pokémon Mansion's Liam and Celeste (file 419), the Battleground (1027).
  - For chapter 11: the Battleground's leader rematches, Platinum trainers 853-860, have no Black 2 id in the registry (stubs
    "SetVarFromValue (trainer n for a battle: no Black 2 id)"); 861-865 do.

## Chapter 2 (plat-ch2, 2026-11-07)
- **Chapter 3's Jubilife beats run in chapter 2's zone.** plat-ch2 regenerates MAP_JUBLIFE
  (`PEARL_VERSION=platinum python3 b2tools/pearl_story.py chapter 2`); chapter 3 tests them there:
  - the Galactic scene (Jubilife script 4, trigger (173-175, 743), VAR_JUBILIFE_CITY_STATE PVAR_4077 == 3): Rowan,
    the counterpart and two grunts, the tag battle (partner PTRAINER_613-618 by gender and starter, grunts PTRAINER_414,
    415), then the Fashion Case; it sets PVAR_4077 = 4, PVAR_4076 = 2, PVAR_4079 = 3 and hides the clowns (PFLAG_01F5,
    PFLAG_0238) and the collector (PFLAG_018B);
  - Looker and the Pal Pad (Jubilife script 28, trigger (188, 757-760), VAR_JUBILIFE_LOOKER_PAL_PAD_STATE PVAR_4076 == 1):
    Looker is placed at (179, the player's z). He used to be placed a level under the ground (y 1 on ground 2: Black 2
    neither draws nor talks to a person off the player's level); now y 2 (pearl_story grid_y, below).
- **What chapter 2 leaves for them** (Roark's Gym script, Platinum's own order): PVAR_4077 = 3, PVAR_4076 = 1,
  PVAR_4079 = 2 (Barry's scene leaving Oreburgh makes it 3), PVAR_40F0 = 1 (the Global Terminal opens),
  the counterpart, Rowan and the grunts shown in Jubilife (PFLAG_017A, PFLAG_019D, PFLAG_019C cleared), Rowan gone from
  his lab (PFLAG_0198 set), the Center B1F's blockade gone (PFLAG_023F set), the Coal Badge, TM76 (Stealth Rock), HM06.
- **Chapter 3's test start against chapter 2's end** (`platinum_flow_check.py 2 --next`):
  - its TEST_LINES reset PFLAG_01F6 and keep PFLAG_01F7 set: in that start the Pokétch Co. president stands in Jubilife
    at (174, 771) and not in his company. In the story the president's scene removes him from Jubilife (PFLAG_01F6 set)
    and puts him in the Pokétch Co. 1F (PFLAG_01F7 cleared). For chapter 3's start: drop `FlagReset PFLAG_01F6`, add
    `FlagReset PFLAG_01F7`;
  - it leaves PFLAG_0181 (Looker hidden) clear: Looker stands at (186, 756) when that start loads, and the Pal Pad scene
    then adds him a second time. In the story the president's scene hides him. Add PFLAG_0181 to its TEST_SET;
  - it has no Pokétch: add `pl_EnablePoketch;pl_RegisterPoketchApp 0;pl_RegisterPoketchApp 1;pl_RegisterPoketchApp 3;pl_RegisterPoketchApp 4`
    to its TEST_LINES (the president's four apps), and PFLAG_00F3 (FLAG_RECEIVED_POKETCH);
  - smaller ones it may want: the Vs. Recorder (item 465) and five Poké Balls (item 4) in TEST_ITEMS; PFLAG_0093
    (FLAG_RECEIVED_HM06), PFLAG_00ED-00EF (the coupons), PFLAG_00F1 (Barry at the Trainers' School), PFLAG_008A,
    PFLAG_010C, PFLAG_010D, PFLAG_09CF.
- **Generator changes others will see when they regenerate** (pearl_story.py, Platinum only; Pearl's output unchanged):
  - grid_y (a person placed by a script): Platinum's own converted heights (work/platinum/heights, from
    `platinum_events.py --heights`) instead of the last Pearl build's work/world (whose chunk numbers are Pearl's: a
    Platinum-only room read nothing, a changed one Pearl's old ground), and a tile held in a var takes the height of the
    person's own event tile. The same heights the build gives the zone's own people. Fixes Looker in Jubilife (y 1 -> 2),
    Barry on Route 207 (y 0 -> 5, chapter 4) and Barry in Solaceon (y 7 -> 2, chapter 5). Placements that move, by zone
    (`pearl_story.py all` before and after): Amity Square 21 (chapter 4: object 5's SetPosition, y one step up or down), the
    Resort Area south-west house 16 (chapter 11: y 0 -> -1, its floor is at -2), Eterna's Galactic building 1F 2
    (chapter 3: y 0 -> -1, the same), the League lobby 1F 1 (chapter 10: y -1 -> 9, see below), Mt. Coronet's unused room
    1, the Battle Frontier 1 and the Battle Hall 4 (step 8). cam_point (the free camera's target) and SetBgEventPos read
    the same heights: the Galactic HQ hall's camera moves to its floor (0 -> 62 units, plat-rooms' scene), Mt. Coronet's
    unused room's to 48.
  - For chapter 10 (not changed here): MAP_POKEMON_LEAGUE_LOBBY_1F's doorway tiles (10-13, 0-3, chunk 207) convert at
    144 units while the lobby is at -2 to -6, so the guard at (11, 3) (object 0) is installed at 144 by the zone's own
    events too. Worth a look in the combined ROM.
  - ShowMenuMultiColumn (0x048) = Black 2's list menu, one column. It was a stub (Pearl's 1.0 has it): the Trainers'
    School blackboard never showed its menu and went round its first lesson for ever. Also used by nothing else.
  - SetMenuXOriginSide (0x33A, Unk02CF): nothing (Black 2's list menus here open at the right edge already); 20 zones
    lose that stub (Hearthome's Poffin house and contest lobby, the League lobbies, Floaroma Meadow, Fuego Ironworks,
    the Battle Tower, Route 207, the Route 210 café, the Berry Master's house, the Frontier, Veilstone Store B1F, Rotom's
    room).
  - AddCameraOverrideObject / RemoveCameraOverrideObject (0x308, 0x309): nothing. In Platinum the camera doesn't follow
    that object (no Camera_TrackTarget), so the view stays on the player, as the translation shows it. Only Route 202's
    Poké Radar scene (chapter 11's) uses them.

## Chapter 3 (plat-ch3, 2026-11-07)
- **Story order offline:** `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py 3 --next` (40 beats in
  data/platinum/story_flow.json "3", 0 findings). The flow check reads a few more things now (marked "plat-ch3"): a test
  start's `pl_EnablePoketch` and `pl_RegisterPoketchApp n`, `pl_GetItemQuantity`, and in a beat's "set": "party" (the
  party's size; default six), "dir" (the way the player faces, for GetPlayerDir), "fateful" (an event Pokémon's slot) and
  "ghost". The same row runs in `platinum_flow_compare.py 3`: its 156 problems are that tool's (as on chapter 2's row):
  VAR_NUM_PLATES_OBTAINED forks on Platinum's side only, the lost-battle states it keeps, the 48-state cut. One difference
  is ours on purpose: the Valley Windworks door opens and the player walks in after the Works Key (the user's choice for
  Pearl, 2026-11-01), where Platinum leaves the player outside the open door.
- **Chapter 3's Jubilife beats (chapter 2's zone)** play from chapter 2's generated file as it is: Looker and the Pal Pad
  (script 28) and the grunts' tag battle (script 4). Nothing else is needed from plat-ch2. One change reaches MAP_JUBLIFE
  when it is regenerated: Looker appears facing east at (179, z), as Platinum's SetObjectEventDir says, not south (the
  generator change below).
- **Generator changes others will see when they regenerate** (pearl_story.py block "plat-ch3", pearl_story.inc block
  "plat-ch3"; Platinum only, Pearl's output unchanged, version_check ok):
  - AddObject after a SetObjectEventDir of the same object in its block: the person appears facing that way (before, its
    event's way; the Dir turned no actor, the object wasn't there yet). 30 AddObjects in 26 zones: Jubilife, Canalave,
    Pastoria, Veilstone, the Galactic Warehouse, Sunyshore, Mt. Coronet south 2F and its unused room 2, Valor Lakefront,
    Route 213, Celestic and its ruins, the Villa, and chapter 3's.
  - SetObjectEventDir on an object held in a var turns the live actor, when every value the file puts in the var is an
    object of the zone (the Eterna Gym's Trainers after their battle). Only the Eterna Gym uses it.
  - GetItemQuantity (Mr. Fuego), FindPartySlotWithFatefulEncounterSpecies (Floaroma's Gracidea), CheckShouldShowGhost (the
    Old Chateau's old man, 10 %, and girl, 25 %, in their zone inits; their frame scenes then play): script now, no stubs.
  - Platinum's movement 0x99 (a "!" emote) is Black 2's "!" (75). Kept as 153 before, which is another Black 2 action:
    Cheryl in Eterna Forest. Platinum's other new codes (0x6A, 0x6B, 0x75-0x77) are only in the Distortion World (step 7).
- **What chapter 3 leaves** (the flow check's end state): the Forest Badge (badge 1), HM01 (420), TM86 (413), the Works
  Key (438), the Bicycle (450), the Explorer Kit (428), the Fashion Case (435, PFLAG_00F2), a Togepi Egg; PVAR_4077 = 4,
  PVAR_4076 = 2, PVAR_4079 = 3 (Jubilife), PVAR_4089 = 2, PVAR_40CF = 3 (the Windworks' outside on-transition turns
  Mars's 2 into 3), PVAR_411E = 2, PVAR_40E9 = 1, PVAR_40B1 = 2, PVAR_407A = 5, PVAR_411D = 1, PVAR_40AE = 3, and
  PVAR_4114 = 0 once the player has the Bicycle and the Kit and walks into Eterna (1 only between the two); PFLAG_0081
  (FLAG_TEAM_GALACTIC_LEFT_ETERNA_BUILDING), PFLAG_01FD (Eterna's and the building's grunts gone), PFLAG_0198 cleared
  (Rowan back in his lab), PFLAG_01A1, PFLAG_01A2 (Floaroma's and Route 205's grunts gone), PFLAG_01F8 and PFLAG_01F9 (the
  girl with her papa), PFLAG_0180 (Cynthia gone), PFLAG_0192 and PFLAG_0200 cleared (the bike shop's owner and Clefairy
  back), PFLAG_01FE cleared (the Eterna Center's Buneary), PFLAG_01FC cleared then set again when Gardenia's Old Chateau
  talk is done.
- **Chapter 4's test start, against this chapter's end** (`platinum_flow_check.py 3 --next`):
  - its TEST_LINES reset PFLAG_01F6 and keep PFLAG_01F7 set: the Pokétch Co. president stands in Jubilife, not in his
    company (chapter 3's start had the same; fixed there): drop `FlagReset PFLAG_01F6`, add `FlagReset PFLAG_01F7`;
  - it has PVAR_4114 = 1 (Eterna's exits blocked); the story leaves 0 with both items. Harmless outside Eterna, and
    Eterna's on-transition sets 0 again;
  - its PVAR_40CF = 2: the story leaves 3 (only Floaroma's school kid and Center read it, as >= 2);
  - it lacks what chapter 2 gave chapter 3 (the Pokétch: `pl_EnablePoketch;pl_RegisterPoketchApp 0;...1;...3;...4` and
    PFLAG_00F3; PFLAG_0181, PFLAG_0093, PFLAG_00ED-00EF) and chapter 3's side ones (PFLAG_00F2 and item 435, PFLAG_010F the
    Windworks door, PFLAG_0091, PFLAG_008B, PFLAG_00A0). 2480 (FLAG_FIRST_ARRIVAL_ETERNA_CITY) is Black 2's to set on arrival.
- **For chapter 90's Centers (plat-ch1's zones):** Eterna's Center 1F reads PFLAG_0081 and shows its Buneary when Jupiter's
  scene clears PFLAG_01FE; Floaroma's reads PVAR_40CF >= 2. Chapter 3's scenes set them (Platinum's own scripts both sides).
- **For chapter 12:** the Gracidea (Floaroma's beauty, object 3) needs a party Shaymin with Black 2's fateful-encounter
  param (PKM_PARAM_FATEFUL_ENCOUNTER 0x6d) set: Route 224's Shaymin (Oak's Letter) must have it. Rotom's Room (behind the
  Galactic building 1F's wall) is chapter 12's: the wall reads the Secret Key, the distribution event 3 and PFLAG_0081.
- **No other foreign beats.** Chapter 3's zones run no other chapter's scene.

## Chapter 4 (plat-ch4, 2026-11-07)
- **The Cycling Road gates check the Bicycle now.** Platinum's gates ask whether the player rides it (CheckPlayerOnBike);
  Pearl's ask whether it is in the Bag. The command was a stub, so the var kept its last value and a gate turned the
  player back or let them through by chance. Now it is Black 2's PlayerGetExState (1 = cycling; pearl_story.py block
  "plat-ch4"). Both gates use it:
  - the south gate (MAP_ROUTE_206_CYCLING_ROAD_GATEHOUSE, Platinum's file 401), this chapter's: from the south on foot,
    "open only to cyclists" and a step back south; riding, through;
  - the north gate (MAP_ETERNA_ROUTE_206_GATEHOUSE, file 85, Platinum's route_206_cycling_road_north_gate), chapter 3's
    zone: from Eterna on foot, "only bicycles" and a step back north; riding, through. This is the story's way from
    Eterna to chapter 4. plat-ch3 (or the lead after the merge) regenerates chapter 3 to get it.
- **SetPlayerBike** (0x0C8) is Black 2's form change now (PlayerSetSpecialSequence: 1 off the Bicycle, 2 on it), only when
  the player isn't in that form already. Platinum gets the player off the Bicycle before a partner walks along. Black 2
  refuses the Bicycle while a partner follows, but a partner could start following a player already on it. Zones that
  change when their chapters regenerate: Eterna Forest interior (chapter 3, Cheryl), Iron Island B2F room 2 (chapter 7,
  Riley), Victory Road 1F back 2 (chapter 10, Marley), Stark Mountain interior 2 (chapter 11, Buck). Each still passes
  b2_script_check offline. Platinum only: Pearl's scripts don't change (its Mira, Cheryl, Riley, Buck and Marley keep
  the stub, as in 1.0).
- **SetCyclingBGM**: nothing to do. Black 2 plays the bike song while the player cycles (patches/zone_flags).
- **HM badges** (the shared piece, here because the Relic Badge is this chapter's): patches/platinum_field_moves.py, a
  Platinum-only code patch at build time. Surf needs the Fen Badge (3) and Defog the Relic Badge (4), as in Platinum;
  Pearl's rule was Surf = Relic, Defog = Fen. The other six are the same in both games. Add `platinum_field_moves` to
  Platinum's patch list after `platinum_regigigas`. For test starts: Surf needs `pl_GiveBadge 3` in a Platinum build
  (chapter 7's start on has it; chapters 5 and 6 can't surf, as in Platinum), Defog `pl_GiveBadge 4`.
- **What chapter 4 leaves** (its 19 beats, `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py 4 --next`:
  0 findings; chapter 5's test start has all of it): the Relic Badge (badge 4), TM65 (item 392, PFLAG_007D), Fantina
  beaten (PTRAINER_318) and the Gym's eight Trainers flagged, PVAR_407B = 2 (Barry's Route 209 gatehouse battle done,
  PTRAINER_471 for Turtwig), PFLAG_0206 (the Route 209 blockade gone), PFLAG_0207 (Barry gone from the gatehouse), the
  Vs. Seeker (443) and PFLAG_097F (FLAG_UNLOCKED_VS_SEEKER_LVL_1), the Dowsing Machine app (6), PVAR_408C = 1 and
  PFLAG_01CC (Route 207's counterpart done), PVAR_4096 = 1 and PFLAG_01AB (Cyrus gone from Mt. Coronet), PVAR_40F6 = 1,
  PFLAG_023C, PFLAG_023D (Keira's scene done), PVAR_40D1 = 1 (the Gym's first visit).
- **Chapter 5's test start, against this chapter's end:**
  - its TEST_LINES reset PFLAG_029C (FLAG_HIDE_HEARTHOME_CITY_GYM_BOLLARDS). In the story Fantina's win leaves it set
    (the leader room's on-load script removes the bollards and sets it; a loss clears it). Harmless in chapter 5 (it
    doesn't go back to the Gym): drop `FlagReset PFLAG_029C`;
  - side things this chapter's talks leave that it lacks, if wanted: the Poffin Case (449, PFLAG_008D), the Odd Keystone
    (111, PFLAG_013F), the Contest Hall's first visit (PVAR_40F7 = 1, PFLAG_0978, PFLAG_0208, PFLAG_0209), Fantina gone
    from the lobby and the Gym Guide from the Gym's door (PFLAG_0190, PFLAG_018D), Mira (PFLAG_00E0, PFLAG_00E4,
    PFLAG_01E4, PVAR_4091 = 2), Bebe met (PFLAG_097E).
- **Flag 0x98D is not Fantina's in Platinum.** It is FLAG_DUMMY_0x098D there (Pearl's "Fantina is back", from the
  Celestic mural; Platinum's Celestic Ruins still set it). Platinum's Fantina stands in her leader room with no hide
  flag. What keeps the player out of the Gym is the Gym Guide at its door (PFLAG_018D clear), until Fantina's talk in
  the Contest Hall lobby hides him. A test start in the Gym: set PFLAG_018D.
- **No foreign beats.** No other chapter's scene runs in this chapter's zones, and none of this chapter's runs elsewhere.

## Chapter 5 (plat-ch5, 2026-11-07)
- **Chapter 5's beats** are row "5" of data/platinum/story_flow.json (30 beats, both tools read it):
  `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py 5` (0 findings) and `platinum_flow_compare.py 5` (every beat
  ends the same on both sides). The row's `"compare": {"won_only": true, "carry": "saved"}` keeps flow_compare on the story's
  path in a long chapter (below); `must` entries may start with `!` (must stay clear).
- **Tool changes others can use** (blocks marked plat-ch5; chapters 1, 2 and 90 give the same results):
  - both tools run item balls (Platinum's visible items 7000-7326 = Black 2's global file 1240, entry for entry) and give the
    ball's flag through the person talked to (VAR_LAST_TALKED on Platinum's side, pl_RemoveTalkedObject on Black 2's);
    flow_check runs pl_CheckItemIsPlate as the macro does.
  - flow_compare: GetItemNameWithIndefArticle only buffers a name (before, it wiped VAR_0x8004: every gift looked like a plate);
    a story_flow row's numbered next beat is recognised (no false "not the next beat"); the next start's `FlagReset` lines
    count; options in a row's or beats file's `"compare"`: `won_only` (no lost-battle paths), `carry: "saved"` (Trainers
    compared beat by beat, the distinct saved states carried on, and a beat's `must` picks the story's own end states,
    even an unchanged one such as talking to the Psyduck without the SecretPotion).
- **Defog and the Lost Tower (needs chapter 4's badge swap):** Platinum's Lost Tower 3F-5F lie under deep fog (weather 14; the
  build gives them Black 2's mist through pearl_defog.fog_zones). The 5F old ladies give the Spell Tag and the Cleanse Tag only
  after Defog was used on 5F (FLAG_USED_DEFOG_IN_ROUTE_209_LOST_TOWER_5F, PFLAG_007B). The Defog script now sets that flag on 5F
  (version.DEFOG_ZONE_FLAGS, pearl_defog.zone_flag_lines; Pearl's and Diamond's sources unchanged). Platinum's Defog takes the
  Relic Badge, which chapter 5's start has: with Pearl's Fen Badge rule the ladies wait for chapter 6. plat-ch4's swap
  (Defog = Relic) is what makes it chapter 5's. **The lead:** `PEARL_VERSION=platinum python3 b2tools/patches/pearl_defog.py
  --sources` writes work/platinum/src/field_scripts/1243_global_10000.s and its text before a Platinum build (pearl_defog's
  apply checks them; main's work/platinum had neither).
- **Later chapters' scenes in chapter 5's zones** (plat-ch5 regenerates these zones; the owners test them there):
  - Chapter 7: Route 210 South's Psyduck block and Cynthia's Old Charm (`Psyduck`, needs ITEM_SECRETPOTION;
    FLAG_HIDE_ROUTE_210_SOUTH_PSYDUCK, FLAG_HIDE_ROUTE_210_SOUTH_CYNTHIA, FLAG_USED_SECRETPOTION).
  - Chapter 8: Lake Acuity clears FLAG_HIDE_VEILSTONE_CITY_GRUNT_M_STORAGE_KEY (the grunt at (721, 593)); Route 217 hides
    Maylene (FLAG_HIDE_VEILSTONE_CITY_GYM_MAYLENE) and Acuity Lakefront shows her again; Snowpoint's Gym hides the Veilstone
    grunts (FLAG_HIDE_VEILSTONE_GALACTIC_GRUNTS).
  - Chapter 9: the Storage Key grunt (Veilstone script 13: FLAG_VEILSTONE_CITY_GRUNT_DROPPED_STORAGE_KEY, Looker added at
    (723, 601)), Looker's YES (VAR_VEILSTONE_CITY_GALACTIC_WAREHOUSE_STATE 3, FLAG_AGREED_WITH_LOOKER_TO_ENTER_HIDEOUT), then in
    the warehouse `CoordEvent_LookerOpenDoor` at (8-9, 8) (state 3 -> 4, FLAG_USED_STORAGE_KEY, the two HQ doors removed:
    FLAG_HIDE_VEILSTONE_CITY_GALACTIC_WAREHOUSE_GALACTIC_HQ_DOOR). Veilstone's on-transition then puts Looker at the Galactic
    building (717, 593): that tile converts at 80 units (the building's raised front), the person's own tile at 16, so he stands
    on the plaza's level there; worth a look in the combined ROM.
  - Chapter 6: Pastoria hides the warehouse's Looker (FLAG_HIDE_VEILSTONE_CITY_GALACTIC_WAREHOUSE_LOOKER). Chapter 11: Stark
    Mountain brings Looker back to the Game Corner (FLAG_HIDE_GAME_CORNER_LOOKER); the Hall of Fame shows the Day Care's Gym
    Guide and Rowan in Veilstone Store B1F.
- **What chapter 5 leaves for chapter 6** (both sides agree): PVAR_4073 1 (Solaceon), PVAR_40F5 1 (Wake's scene), PVAR_407D 1
  (the warehouse guards), PVAR_411A 2, **PVAR_411F 2** (the warehouse), PVAR_407C 1 (VAR_PASTORIA_CITY_STATE, set in the
  warehouse); set: PFLAG_021E, PFLAG_0191, PFLAG_01A3, PFLAG_01A8 (the assistant gone), PFLAG_01A9, PFLAG_01BF, PFLAG_028A; clear:
  PFLAG_020D (Looker waits in the warehouse); the Cobble Badge, TM110 (Maylene's TM60), HM02, TM119 (HM05 Defog), the Good Rod.
- **Chapter 6's test start against chapter 5's end** (`platinum_flow_check.py 5 --next`): its TEST_SET has chapter 9's Storage Key
  scenes and one NO answer. For chapter 6's start: drop PFLAG_009B, PFLAG_0155, PFLAG_010E, PFLAG_0228, PFLAG_020D (chapter 9;
  PFLAG_020D is set by Pastoria's own scene) and PFLAG_00E8 (the hiker's NO); PVAR_411F=2, not 4; drop `FlagReset PFLAG_01A8`
  from its TEST_LINES (it shows the assistant at the warehouse again, whose talk starts the tag battle a second time). Smaller:
  the gift flags (PFLAG_009D TM60, PFLAG_00A2 Good Rod, PFLAG_00C7, PFLAG_00CC, PFLAG_00CD, PFLAG_00D2, PFLAG_0458, PFLAG_04E2),
  or the givers give again.
- **PFLAG_029C** (FLAG_HIDE_HEARTHOME_CITY_GYM_BOLLARDS): chapter 5's start no longer resets it (plat-ch4 found it wrong). The
  starts of chapters 6-12 in notes/PLATINUM_CHAPTERS.md still have `FlagReset PFLAG_029C`: their owners should drop it too.
- **Chapter 5's start against chapter 4's end** (`platinum_flow_check.py 4 --next`: 0 findings): it now has chapter 4's side items
  (the Odd Keystone, the Poffin Case, their flags, PFLAG_007D, the Contest Hall's visit, PFLAG_018D, PFLAG_0190, Bebe met) and
  the Pokétch in its TEST_LINES (`pl_EnablePoketch`, apps 0, 1, 3, 4 and 6). No test start from chapter 3 on gives the Pokétch
  (chapter 2's handoff); PFLAG_00F3 is left out of chapter 5's TEST_SET so chapter 4's end still matches it. Chapter 3's apps
  beyond the president's four, if any, aren't in it.

## Chapter 6 (plat-ch6, 2026-11-07)
- **Chapter 6's beats** are row "6" of data/platinum/story_flow.json (23 beats): `PEARL_VERSION=platinum python3
  b2tools/platinum_flow_check.py 6` (0 findings) and `platinum_flow_compare.py 6` (every beat ends the same on both sides; what
  it still lists is chapter 7's start, below). Its test start is checked against chapter 5's end: `platinum_flow_check.py 5
  --next`, 0 findings (chapter 9's Storage Key flags and the hiker's NO dropped, PVAR_411F=2, PFLAG_01A8 kept set,
  `FlagReset PFLAG_020D`: the new game hides the warehouse's Looker and chapter 5 shows him).
- **The chase, all in this chapter's zones:** the Gym (VAR_PASTORIA_CITY_STATE 3) -> out of the Gym (frame script 19: 4) -> the
  "bomb" at (610, 810) or a talk to Wake (5: the grunt moves to (637, 812)) -> his "stop chasing me" (FLAG_TALKED_TO_PASTORIA_CITY_GRUNT_M)
  -> Route 213's on-transition shows its grunt (Fen Badge and that flag) at (654, 812), first talk sends him to (683, 833), the
  second brings Looker (FLAG_ROUTE_213_GRUNT_M_LEFT; the hotel lobby's Looker and Valor Lakefront's grunt shown) -> Valor
  Lakefront's grunt: first talk sends him to (723, 769), the second is his battle (PTRAINER_847), then Cynthia and Barry and the
  SecretPotion (state 6). Chapter 5's warehouse only sets state 1; nothing of the chase is in chapter 5's zones.
- **What chapter 6 leaves** (both sides agree): the Fen Badge (3), TM55 Brine (TM107, item 516) and PFLAG_009C, the SecretPotion
  (464), PVAR_407C = 6; Barry's battle (PTRAINER_474 for Turtwig), Wake (PTRAINER_316) and his six Trainers, the Valor grunt
  (PTRAINER_847); set: PFLAG_020C (Pastoria's grunt gone), PFLAG_0102, PFLAG_0103, PFLAG_0104, PFLAG_0106, PFLAG_0118,
  PFLAG_00FD, PFLAG_01A9, PFLAG_0211, PFLAG_021A, PFLAG_021B, PFLAG_020D (Pastoria hides the warehouse's Looker again),
  PFLAG_017E (Pastoria's on-transition hides Route 212's blockade); clear: PFLAG_020F (Wake back in his Gym), PFLAG_0156 (the
  Croagunk scene again).
- **Chapter 7's start against chapter 6's end** (`platinum_flow_check.py 6 --next`, 6 findings): the same as chapter 6's had: drop
  PFLAG_009B, PFLAG_00E8, PFLAG_010E, PFLAG_0155, PFLAG_0228 (chapter 9's scenes, the hiker's NO), PVAR_411F=2 not 4; and drop
  any `FlagReset PFLAG_01A8`. It also lacks: chapter 4's and 5's side items and flags (chapter 6's start in
  notes/PLATINUM_CHAPTERS.md has them all: copy its TEST_SET, TEST_ITEMS and the Pokétch lines), and this chapter's PFLAG_009C,
  PFLAG_00FD, PFLAG_0103, PFLAG_0106, PFLAG_0118, PFLAG_017E, PFLAG_020C (and the side flags PFLAG_0078, PFLAG_00FB, PFLAG_00CA,
  TM92 item 419, if wanted).
- **Other chapters' scenes in chapter 6's zones** (plat-ch6 regenerates these zones; the owners test them there):
  - Chapter 7: Route 210 South's Psyduck needs the SecretPotion (464), given here.
  - Chapter 8: Valor Cavern sets FLAG_GALACTIC_LEFT_LAKE_VALOR; Valor Lakefront's on-transition and on-load then switch its lake
    warps (SetWarpEventPos 3, 4 for the drained lake instead of 5, 6). Walk into the lake entrance after chapter 8's scene.
  - Chapter 9/10: Sandgem's lab sets VAR_VALOR_LAKEFRONT_BLOCK_SUNYSHORE_STATE 1 and hides the collector
    (FLAG_HIDE_VALOR_LAKEFRONT_COLLECTOR); until then the step trigger at (724, 789-791) turns the player back from Route 222.
    Canalave's library 3F hides the lakefront's cameramen (FLAG_HIDE_VALOR_LAKEFRONT_CAMERAMEN).
- **Generator changes others will see when they regenerate** (pearl_story.py block "plat-ch6", pearl_story.inc block "plat-ch6";
  Platinum only, Pearl's output unchanged):
  - CheckHasSeenSpecies = Black 2's PokeDexIsRegist 0 (the Mansion office's Manaphy book; was a stub).
  - CheckPartyCombeeGenderCount = a party loop on PokePartyGetParam (species, sex) and PokePartyIsEgg (Pastoria's Macho Brace;
    was a stub [Pearl too]).
  - DrawPokemonPreview now marks the species seen (PokeDexRegist 0 after Black 2's preview, as Platinum's and Pearl's command do).
    Besides the Mansion office's Manaphy, it changes chapter 8's Verity Cavern (Mesprit, file 1577) and chapter 12's Fullmoon
    Island (Cresselia, file 1524): one line each. Pearl's 1.0 shows those pictures without the Pokédex entry (a 1.0.1 item).
- **Tool changes** (platinum_flow_compare.py block "plat-ch6"): badges are kept (GiveBadge, CheckBadgeAcquired, a test start's
  `pl_GiveBadge n`), and Black 2's RTCGetTime makes both the hour and the minute unknown. Chapters 1, 5 and 90 give the same
  results; 2 and 4 the same problems with fewer forked end states. scene_check.py: two ACCEPT rows (Pastoria's after-Gym jump,
  the Mansion's hidden knockout maids).

## Chapter 7 (plat-ch7, 2026-11-07)
- **Chapter 7's beats** are row "7" of data/platinum/story_flow.json (35 beats): `PEARL_VERSION=platinum python3
  b2tools/platinum_flow_check.py 7` (0 findings) and `platinum_flow_compare.py 7` (every beat the same on both sides). The
  row uses `"set": {"party": 5}` (plat-ch3's) for Riley's Egg after a full party.
- **Tool changes others can use** (platinum_flow_compare.py, marked plat-ch7; chapters 1-5 and 90 give the same results):
  Platinum's PlayBoatCutscene ends at its map (Eldritch's boat, the Snowpoint ship: chapter 8 and 11), as a Warp; a battle
  after SetHasPartner names the partner (VAR_PARTNER_TRAINER_ID) as Black 2's pl_StartTagBattle does (Riley; also Mira,
  Cheryl, Marley, Buck when their beats battle Trainers).
- **Generator changes others will see when they regenerate** (pearl_story.py block "plat-ch7", pearl_story.inc block
  "plat-ch7"; Platinum only, Pearl's output unchanged, version_check ok):
  - ReturnToField after an app that didn't run (every command since the scene's last fade or message a stub, or
    StartLibraryTV, or a result read) opens nothing. Black 2's FieldOpen on an open field waits for ever (pokebw2
    field_event.c EventFieldOpen_Callback waits for the proc manager to be idle), so those scripts hung; the fade-in after
    it is a black one now, not the starter screen's white. Files that change when regenerated: Jublife TV 2F, 3F and the
    gallery, the GTS, the Pokétch Co. 1F (chapter 2); the Oreburgh and Eterna trade houses (chapters 2, 3: the in-game
    trades, stubs as Pearl's 1.0); the Fan Club, the Amity Square gatehouses, the Poffin house, the Contest Hall lobby
    (chapter 4); the Route 214 gatehouse and the Route 212 shard house (chapter 6); the Global Terminal 2F/3F; the Union
    Room and the Frontier's closed scenes (steps 8 on). **Pearl's 1.0 has the same hang** (the Move Deleter after a
    Pokémon is chosen, the Jublife TV boards, the trades): for the lead (1.0.1?), Pearl's output wasn't changed here.
  - The Move Deleter (Canalave's east house): GetPartyMonMoveCount = PokePartyGetMoveCount; SelectPartyMonMove +
    GetSelectedPartyMonMove = Black 2's CallPokeMoveReplace with no new move (its forget-HM mode; it fades and reopens the
    field itself, so Platinum's fades and ReturnToField around it are dropped); BufferPartyMoveName; ClearPartyMonMoveSlot =
    PokePartyLearnMove slot, 0. These five register only if no other block did first (plat-ch6's shard tutor uses
    GetPartyMonMoveCount too). **For plat-ch6:** if OpenSummaryScreenTeachMove gets a handler, the ReturnToField after it
    goes back to a FieldOpen (the rule above only covers stubs): drop it where the new screen reopens the field itself, as
    poke_select_fades does.
  - The library's explosion scene: StartLibraryTV (the TV's footage of Lake Valor, a full-screen picture for 240 frames) has
    no Black 2 screen and stays a counted stub; after it the free camera is put on the player (7, 7) again and walks to the
    table, as Platinum's (PL_CAMERA_AT_PLAYER, keyed by Platinum's address: not in Pearl's file).
- **Registry** (data/platinum/pearl_story_ids.json, src/include/platinum/pearl.h; pearl_ids.py SYSTEM_SAME, Platinum only):
  FLAG_FIRST_ARRIVAL_CANALAVE_CITY (PFLAG_09B8) is Black 2's Canalave arrival flag 2478 and FLAG_FIRST_ARRIVAL_SUNYSHORE_CITY
  (PFLAG_09BE) Sunyshore's 2485 (town_map.fly_flags), as Eterna's was. Before, free flags nothing set: the Celestic elder at
  home never said her after-Canalave line, and **chapter 10's** Sunyshore checks (the counterpart's talk, the Sandgem lab's
  CheckShouldRatePokedex/arrived-in-Sunyshore branches) would never see the arrival. A test start past a town's first visit
  sets its number (2478, 2485) in TEST_SET, as the starts do with the others.
- **Chapter 7's scenes in other chapters' zones** (their owners regenerate them; checked here with the files as they are):
  - Chapter 5's Route 210 South: the Psyduck with the SecretPotion and Cynthia's Old Charm (`Psyduck`, person 19, from
    (561, 588) facing north): plays as generated (flow_check beat 1, scene_check of the zone clean).
  - Chapter 1's Sandgem lab: Byron's win sets FLAG_HIDE_SANDGEM_TOWN_LAB_PROF_ROWAN (PFLAG_0198). Chapter 1's Lake Verity and
    chapter 8's Lake Acuity: Canalave's after-explosion scene clears FLAG_HIDE_LAKE_VERITY_LOW_WATER_PROF_ROWAN /
    _COUNTERPART (PFLAG_0175, PFLAG_0194) and FLAG_HIDE_LAKE_ACUITY_LOW_WATER_RIVAL (PFLAG_0293).
  - Chapter 6's Valor Lakefront: the library sets FLAG_LAKE_VALOR_EXPLODED (PFLAG_00A8) and
    FLAG_HIDE_VALOR_LAKEFRONT_CAMERAMEN (PFLAG_01AE); Canalave's on-transition hides Celestic's Cynthia (PFLAG_01BD).
- **Later chapters' scenes in chapter 7's zones** (plat-ch7 regenerates these zones; the owners test them there):
  - Chapter 8: Lake Verity's scene hides Mt. Coronet north 1F room 1's two grunts (FLAG_HIDE_MT_CORONET_1F_NORTH_ROOM_1_GRUNTS_M,
    PFLAG_029A). Chapter 9: the Galactic HQ shows the grunt there (FLAG_HIDE_MT_CORONET_1F_NORTH_ROOM_1_GRUNT_F, PFLAG_0295)
    and Sendoff Spring hides her again.
  - Chapter 8: Grandma Wilma's Draco Meteor (Route 210 North, behind Rock Climb: the Icicle Badge).
  - Chapter 10/11: the Hall of Fame shows Lucian in the library 1F (PFLAG_0186); the National Pokédex shows Byron in the Iron
    Island house (Metal Coat); Stark Mountain's arrest brings Cynthia to the Celestic ruins' painting
    (FLAG_ARRESTED_CHARON_STARK_MOUNTAIN); Iron Island B3F's on-transition/on-load switch the Iron Ruins' warp with the event
    Regigigas (plat-rooms' piece, in the generated file).
  - Chapter 12: the Celestic elder's research after the game (FLAG_UNLOCKED_DIALGA_PALKIA_SPEAR_PILLAR, PFLAG_0145); the
    library 2F hiker (VAR_ARCEUS_EVENT_STATE); Eldritch's boat to Fullmoon and Newmoon Island (the menu's entries:
    FLAG_TALKED_TO_CANALAVE_CITY_SAILOR_ELDRITCH_HOUSE_LITTLE_BOY, FLAG_TRAVELED_TO_NEWMOON_ISLAND, VAR_LUNAR_WING_EVENT_STATE);
    the Harbor Inn's Darkrai (VAR_DARKRAI_EVENT_STATE; its PlaySE and 2B5 are stubs as Pearl's 1.0).
- **What chapter 7 leaves** (flow_check's end state against its start): the Mine Badge (badge 5); HM03 (422), HM04 (423),
  TM91 (418), TM77 (404), TM48 as TM104 (513), the Old Rod (445), the Riolu Egg in the party (the Old Charm, 439, is given
  and handed over); PVAR_4074 = 2 (Celestic), PVAR_40F1 = 1 (its elder), PVAR_4105 = 1 (the Canalave gatehouse), PVAR_4078 = 5
  after the explosion and 6 at the next Canalave arrival, PVAR_40B2 = 2 (the library), PVAR_4092 = 2 (Riley), PVAR_403F = 609
  (Riley's id, left in the partner var as in Platinum); set: PFLAG_0084, PFLAG_0092, PFLAG_00A6, PFLAG_00A7, PFLAG_00A8,
  PFLAG_00C6, PFLAG_00C9, PFLAG_00E1, PFLAG_00E5, PFLAG_0107, PFLAG_0198, PFLAG_01AC, PFLAG_01AE, PFLAG_01AF, PFLAG_01B0,
  PFLAG_01E5, PFLAG_01E7, PFLAG_0214, PFLAG_021C, PFLAG_0299, PFLAG_0980, PFLAG_098D, PFLAG_09DA, PFLAG_09E9; cleared:
  PFLAG_0175, PFLAG_0194, PFLAG_0293 (chapter 8's lake people shown), PFLAG_01C3 (the elder shown at home); shown and
  hidden again within the chapter, so set at both ends as the new game sets them: PFLAG_01B1-01B8, PFLAG_01BD, PFLAG_029B,
  PFLAG_0229, PFLAG_02CC; Trainers beaten: Barry (477 for Turtwig), Byron (250) and his Gym's seven, the Celestic grunt
  (416), Cyrus (913), the Iron Island grunts (835, 836).
- **Chapter 8's test start against this chapter's end** (`platinum_flow_check.py 7 --next`, `platinum_flow_compare.py 7`):
  - drop the chapter 9 Storage Key flags and the hiker's NO it inherited (PFLAG_009B, PFLAG_010E, PFLAG_0155, PFLAG_0228,
    PFLAG_00E8) and PVAR_411F=4 (2); drop PFLAG_0145 (FLAG_UNLOCKED_DIALGA_PALKIA_SPEAR_PILLAR: the elder sets it after the
    Hall of Fame); `FlagReset PFLAG_01F7`, not 01F6 (chapter 3's handoff: the president in his company);
  - add PFLAG_00A7 (the ruins' painting examined: without it the painting brings Cyrus and his battle back), PFLAG_0980,
    PFLAG_01BD (or Celestic shows Cynthia again), the gift flags (PFLAG_0084, PFLAG_0092, PFLAG_00C6, PFLAG_00C9, PFLAG_00E1,
    PFLAG_00E5) and the earlier chapters' side ones chapter 7's start has now (PFLAG_007D, PFLAG_008D, PFLAG_009D, PFLAG_00A1,
    PFLAG_00A2, PFLAG_00C7, PFLAG_00CC, PFLAG_00CD, PFLAG_00D2, PFLAG_0116, PFLAG_013F, PFLAG_018D, PFLAG_0190, PFLAG_01A8,
    PFLAG_0208, PFLAG_0209, PFLAG_0458, PFLAG_04E2, PFLAG_0978, PFLAG_097E, PVAR_40F7=1, the Pokétch lines; chapter 6's
    PFLAG_009C, PFLAG_00FD, PFLAG_0103, PFLAG_0106, PFLAG_0118, PFLAG_017E, PFLAG_020C, PFLAG_0078, PFLAG_00FB, PFLAG_00CA,
    TM92 as 419), and keep 2478 (Canalave visited: the elder's line, Fly; the check lists it as PFLAG_09B8 that
    no script of this chapter sets: Black 2's code sets it on arriving in Canalave);
  - PVAR_4078=5 is right for a start outside Canalave (the next arrival makes it 6).
- **Chapter 7's start against chapter 6's end** (`platinum_flow_check.py 6 --next`: 1 finding, on purpose): it takes
  chapter 6's start (chapters 4 and 5's side items and flags, the Pokétch, no chapter 9 Storage Key flags or hiker's NO,
  PVAR_411F=2, PFLAG_01A8 set) and chapter 6's end (the Fen Badge, TM55 as 516, the SecretPotion 464, TM92 as 419,
  PVAR_407C=6, PFLAG_009C, PFLAG_00FD, PFLAG_0103, PFLAG_0106, PFLAG_0118, PFLAG_017E, PFLAG_020C, PFLAG_020D, PFLAG_0078,
  PFLAG_00FB, PFLAG_00CA, ...; FlagReset PFLAG_0156, PFLAG_020F). The finding: chapter 7's start keeps PFLAG_01F6 set and
  resets PFLAG_01F7 (the Pokétch Co. president in his company, as chapter 3's handoff says the story leaves him); the
  starts of chapters 4-6 still have `FlagReset PFLAG_01F6` and put him in Jubilife. Chapter 6's beaten Trainers aren't in
  the start (no start sets defeat flags).

## Chapter 8 (plat-ch8, 2026-11-07)
- **Chapter 8's beats** are row "8" of data/platinum/story_flow.json (52 beats): `PEARL_VERSION=platinum python3
  b2tools/platinum_flow_check.py 8` (0 findings). Platinum's own order, from its scripts: Lake Valor (drained) and Saturn in
  Valor Cavern; Lake Verity (Galactic) and Mars; Mt. Coronet north 1F room 1 (the grunts gone), B1F, north 1F room 2; Route
  216; Route 217 (Maylene, HM08 in a ball); Acuity Lakefront (Barry: "you can't climb without the Snowpoint Gym Badge");
  Snowpoint and Candice; back at Acuity Lakefront, Rock Climb up to Lake Acuity (Galactic): Jupiter and Barry.
- **Warp beats (flow_check, block "plat-ch8"):** `{"zone", "warp": [x, z], "to": ZONE}` runs the zone's map scripts and checks
  that the first warp still on that tile (after their SetWarpEventPos) leads to ZONE; "expect": "off", "must" and "needs" as
  for the other beats. Chapter 8 uses it for the lakes' stacked warps. Any chapter can use it (Turnback Cave, the Ruin
  Maniac's cave, the Iceberg Ruins' door).
- **Camera (pearl_story.py block "plat-ch8"):** Acuity Lakefront's Barry (Platinum's file 385) is in CAMERA_PLAN_FILES: the
  free camera pans north 6 to Barry and back from each trigger tile (310 or 311, 244). Before, its AddFreeCamera was a stub
  and the camera stayed on the player while Barry spoke 7 tiles north. Platinum only; no other zone changes.
- **Plates a person gives (pearl_story.py block "plat-ch8", after h_plate):** Platinum's give-item script (scripts_common,
  in every zone file that gives an item) asks CheckItemIsPlate and shows the next of the eight engraving lines
  (VAR_NUM_PLATES_OBTAINED PVAR_4115 counts them). In zone files it was approximated as 0 (Pearl's 1.0 rule; only the item
  balls and hidden items ran the check), so a Plate a person gives showed no engraving and didn't count, and the balls'
  Plates then showed the lines one step early. Platinum runs pl_CheckItemIsPlate everywhere now; for any other item it is 0
  as before. 91 Platinum zone files change one line each when their chapters regenerate (`pearl_story.py all` against
  main's work/platinum: nothing else differs but Acuity Lakefront's camera); all chapters' zone files still pass
  b2_script_check, flow_check 2-5 and flow_compare 1, 5, 90 give what they gave. Behaviour changes only where a person gives a
  Plate: Route 217's hiker (the Icicle Plate, chapter 8) and Oreburgh Mine B1F's hiker (the Flame Plate, the Arceus event;
  chapter 2's zone, regenerated by its owner or the lead). Pearl and Diamond unchanged.
- **Chapter 8's beats in other chapters' zones** (their owners regenerate them; chapter 8 checked them from the generated
  files as they are on main):
  - Chapter 6, Valor Lakefront: the cameramen hidden (PFLAG_01AE, chapter 7's library scene); its map scripts move warps 5, 6
    away while FLAG_GALACTIC_LEFT_LAKE_VALOR (PFLAG_015E) is clear, so (717, 760-761) lead to the drained lake (our
    MAP_LAKE_VALOR_GALACTIC) until Sendoff Spring sets it (chapter 9). Keep those SetWarpEventPos lines.
  - Chapter 1, Verity Lakefront: its map scripts switch on FLAG_DEFEATED_COMMANDER_SATURN_VALOR_CAVERN (PFLAG_013E): before
    Saturn, (80-81, 843) lead to our MAP_LAKE_VERITY (Platinum's low-water lake: Rowan and the assistant ask "how was Lake
    Valor?", PFLAG_0175 and PFLAG_0194 clear); after, to MAP_LAKE_VERITY_GALACTIC (Mars). Jupiter's scene hides both pairs
    (PFLAG_0175, PFLAG_0194, PFLAG_028C, PFLAG_028D) and shows Rowan in his lab again (PFLAG_0198 cleared).
  - Chapter 7, Mt. Coronet north 1F room 1: Mars's scene hides the two grunts on the way to B1F
    (FLAG_HIDE_MT_CORONET_1F_NORTH_ROOM_1_GRUNTS_M, PFLAG_029A). Chapter 8 needs from chapter 7: the library 3F scene's
    PFLAG_00A8 (the explosion; Jupiter's scene clears it) and PFLAG_01AE; Canalave's after-explosion scene clearing PFLAG_0175,
    PFLAG_0194 and PFLAG_0293 (chapter 8's TEST_LINES reset them).
  - Chapter 5, Veilstone: Route 217's Maylene hides the Gym's Maylene (PFLAG_0298 set); Acuity Lakefront's on-transition with
    the Icicle Badge shows her again (PFLAG_0298 clear) and hides the Snowpoint Center's (PFLAG_0234 set); Candice's win sets
    FLAG_HIDE_VEILSTONE_GALACTIC_GRUNTS (PFLAG_01BF, set already by chapter 5's tag battle); Jupiter's scene shows the Storage
    Key grunt (PFLAG_0223 cleared).
  - Chapter 90, Snowpoint Pokémon Center 1F: Maylene (object 4, PFLAG_0234) is there from Route 217 until the player walks
    into Acuity Lakefront with the Icicle Badge.
- **For chapter 10:** the caverns' trio (our zones) wait for the Sandgem lab's scene, which clears FLAG_HIDE_VERITY_CAVERN_MESPRIT,
  ..._VALOR_CAVERN_AZELF, ..._ACUITY_CAVERN_UXIE (PFLAG_01DF, PFLAG_01E0, PFLAG_01E1; the new game sets them). Azelf and Uxie:
  StartLegendaryBattle is Black 2's wild battle (no legendary rules); a win without a catch and a run both show "disappeared"
  (CheckDidNotCapture). Mesprit flees and roams: ActivateRoamingPokemon is a stub (roamers: the lead's cross-chapter list).
  A catch sets FLAG_CAUGHT_AZELF (PFLAG_0126) or FLAG_CAUGHT_UXIE (PFLAG_0127); the Hall of Fame shows the ones not caught
  again (chapter 10's scene).
- **For chapter 11:** Mt. Coronet north 1F room 2 (our zone): without an event Regigigas in the party its map scripts move
  warp 3 away, so (15, 16) leads to the Iceberg Ruins' entrance room (MT_CORONET_ICEBERG_RUINS); with it, warp 2 goes and the
  door leads to Regice's room (checked offline without; the deliveryman's Regigigas test is in "For the combined ROM").
  Snowpoint's temple guard lets the player in after the Hall of Fame with the National Pokédex (Candice comes:
  VAR_SNOWPOINT_CITY_STATE PVAR_407F 0 -> 1); the sailor's ship to the Fight Area (PlayBoatCutscene, Black 2's boat demo) and
  Cynthia's first-time scene (FLAG_SAILED_TO_BATTLE_ZONE) are post-game too.
- **What chapter 8 leaves** (flow_check's end state): the Icicle Badge (badge 6), TM72 (item 522 = TM113 Avalanche,
  PFLAG_009E), HM08 (item 529 = TM120 Rock Climb, ball flag PFLAG_0497), the Icicle Plate (302, PFLAG_00DE; PVAR_4115 1, its engraving), the Spell Tag
  (247, PFLAG_013B, PFLAG_025F); Saturn (PTRAINER_408), Mars (405), Candice (319) and her six Trainers (268-271, 827, 828:
  the last two use the moved flags) beaten; PFLAG_013E, PFLAG_0984, PFLAG_01BC (Saturn and Lake Valor's grunts gone); PFLAG_00BA,
  PFLAG_098E, PFLAG_01C0, PFLAG_029A (Mars); PVAR_4097 1 (Rowan's notice at Lake Verity); PVAR_40A8 1, PFLAG_0297
  (Maylene's walk); PVAR_4084 1, PFLAG_01AA (Barry at Acuity Lakefront); PFLAG_0234 set, PFLAG_0298 clear (Maylene back in
  Veilstone); PVAR_40D3 2, PFLAG_098F, PFLAG_01BA, PFLAG_01B9, PFLAG_0175, PFLAG_0194, PFLAG_028C, PFLAG_028D set, PFLAG_0223,
  PFLAG_0198, PFLAG_00A8 clear (Jupiter); the lakes' TM balls (TM25 PFLAG_04E6, TM38 PFLAG_04E5, TM14 PFLAG_04E7).
- **Chapter 9's test start against this end** (`platinum_flow_check.py 8 --next`, 2 findings, both in chapter 9's start):
  - it sets PFLAG_0298 (FLAG_HIDE_VEILSTONE_CITY_GYM_MAYLENE): the story leaves it clear (Acuity Lakefront with the Icicle
    Badge brings Maylene back to her Gym). Drop it;
  - it sets PVAR_407F=1 (VAR_SNOWPOINT_CITY_STATE): only the temple guard's post-game scene sets it. Drop it;
  - its TEST_LINES have `FlagReset PFLAG_01F3` (FLAG_HIDE_SNOWPOINT_CITY_CANDICE): the new game sets it and nothing in the
    story clears it before the temple scene. Drop the reset (Candice would stand in the street at (366, 208));
  - it lacks PFLAG_013E (Saturn beaten): without it Verity Lakefront leads back to the low-water lake. Add it;
  - smaller ones it lacks: PFLAG_0234 (the Snowpoint Center's Maylene gone), PFLAG_009E (TM72 given: Candice gives it again),
    PFLAG_0497 (the HM08 ball), PFLAG_00DE, item 302 and PVAR_4115=1 (the Plates' engraving count), PFLAG_013B, PFLAG_025F and item 247, PFLAG_00B8, the lakes' balls'
    flags, the beaten Trainers' flags.
- **Chapter 8's start against chapter 7's end:** chapter 7's row isn't on main yet; checked by hand against chapter 7's
  section and Platinum's scripts (the library 3F scene, Canalave's after-explosion scene, Byron, Riley). The start gets
  Byron's TM91 flag (PFLAG_0092) and Riley's (PFLAG_00E1, PFLAG_00E5: the Riolu Egg given; the Battleground and the Battle
  Tower salon read it). Chapter 7's side gifts (TM48 PFLAG_00C9, TM77 PFLAG_00C6, the Old Rod PFLAG_0084, Celestic's glasses,
  the Metal Coat) are left out. When chapter 7's row is merged, run `platinum_flow_check.py 7 --next`.

## Chapter 9 (plat-ch9, 2026-11-07)
- **Chapter 9's beats** are row "9" of data/platinum/story_flow.json (80 beats): `PEARL_VERSION=platinum python3
  b2tools/platinum_flow_check.py 9` (0 findings) and `platinum_flow_compare.py 9` (every beat ends the same on both sides; what
  it still lists is chapter 10's start, below, and the YES path's arrival in the Distortion World's 1F, step 7). The row has two
  parts: from test start A (Veilstone) to Cynthia at the distorted Spear Pillar, then `{"restart": "B"}` and the beats from
  test start B (Sendoff Spring, after the Distortion World).
- **Tool changes others can use** (blocks and lines marked plat-ch9; flow_check 2-6 and 8 give 0 findings as before,
  flow_compare 1, 5, 6, 8 and 90 the same output as main's tool):
  - flow_check: a beat `{"restart": "B"}` makes the state the chapter's second test start, the lines after
    `**Test start B**` in its section of notes/PLATINUM_CHAPTERS.md (its tile checked and its file assembled, as the first
    start's); `--end` prints the chapter's end state as a test start (TEST_ITEMS, TEST_SET, TEST_LINES over the new game's
    own state: `FlagReset` for the new game's flags the story clears, `pl_SetTrainerFlag PTRAINER_n` for beaten Trainers,
    the badges, the Pokétch and its apps, `pl_SetHiddenLocation n`); a start's TEST_LINES may have `pl_SetTrainerFlag` and
    `pl_SetHiddenLocation`; the macros pl_CheckHasTwoAliveMons (a party of two or more: "party" in a beat's set) and
    pl_SpearPillarSequence (its polls report "over") run as the build's do.
  - flow_compare: the same restart beats; Platinum's CheckGameCompleted reads FLAG_GAME_COMPLETED (0x964), which the
    translation reads as Black 2's 2400 (before, Platinum's side forked on it at Spear Pillar's on-transition).
- **Chapter 9's start A against chapter 8's end** (`platinum_flow_check.py 8 --next`): the start is chapter 8's end state
  (flow_check's), with chapter 8's two findings fixed (PFLAG_0298 and PVAR_407F dropped, no `FlagReset PFLAG_01F3`) and
  chapter 8's smaller ones added (PFLAG_013E, PFLAG_0234, PFLAG_009E, PFLAG_0497, PFLAG_00DE, item 302, PVAR_4115=1,
  PFLAG_013B, PFLAG_025F, item 247, PFLAG_00B8, the lakes' balls, the nine beaten Trainers as `pl_SetTrainerFlag`). Dropped
  as the earlier handoffs say: chapter 9's own Storage Key flags (PFLAG_009B, PFLAG_0155, PFLAG_010E, PFLAG_0228;
  PVAR_411F=2), the hiker's NO (PFLAG_00E8), PFLAG_0145 (post-game). `8 --next` still lists 59 findings, all of one kind:
  chapter 6's and 7's end that chapter 8's start on main doesn't carry yet (plat-ch6's and plat-ch7's handoffs): the
  Pokétch and its apps, the side gifts and their flags (PFLAG_0078, 007D, 0084, 008D, 009C, 009D, 00A1, 00A2, 00A7, 00C6, 00C7,
  00C9, 00CA, 00CC, 00CD, 00D2, 00FB, 00FD, 0103, 0106, 0116, 0118, 013F, 017E, 018D, 0190, 01A8, 01B3, 01B5, 01BD, 0208, 0209,
  020C, 0458, 04E2, 0978, 097E, 0980, PVAR_40F7=1, PVAR_40CF=3, items 75, 111, 224, 390, 393, 404, 419, 445, 449, 513, 515),
  `FlagReset PFLAG_01F7` instead of 01F6. When chapter 7 is merged and chapter 8's start gets them, `8 --next` gives 0.
  plat-ch9's work/agents/plat-ch9/tools/start9.py writes both starts from the flow check (`--write`).
- **Chapter 9's beats in other chapters' zones** (their owners regenerate them; checked here from the files as they are):
  - Chapter 5's Veilstone and the warehouse: the Storage Key grunt (person 23, shown by Lake Acuity's scene), Looker and the
    hideout's YES (PVAR_411F 3, PFLAG_009B, PFLAG_0155), the warehouse's step trigger at (8-9, 8) (PVAR_411F 4, PFLAG_010E,
    PFLAG_0228, PFLAG_028A, PFLAG_020D): all play from chapter 5's generated files.
  - Chapter 7's Mt. Coronet north 1F room 1: the HQ's button shows the grunt there (person 15, PFLAG_0295 cleared), Sendoff
    Spring hides her again.
  - Chapter 6's Valor Lakefront: Sendoff Spring sets FLAG_GALACTIC_LEFT_LAKE_VALOR (PFLAG_015E): (717, 760) leads to the
    lake again (warp beat checked).
  - Chapter 1's Sandgem lab (chapter 10's scene): Sendoff Spring sets VAR_SANDGEM_TOWN_LAB_STATE (PVAR_40A6) 2, which runs
    the lab's OnFrame_ReturnedFromDistortionWorld (frame script 15; beat 80, marked chapter 10).
- **The step 7 handoff: the Distortion World** (not built here, the user's order; the warp is Platinum's, not redirected):
  - **The way in.** MAP_MOUNT_CORONET_UNUSED_2 (Platinum's SPEAR_PILLAR_DISTORTED, Black 2 zone 265). Its frame script 1
    (VAR_SPEAR_PILLAR_DISTORTED_STATE PVAR_40C3 == 1, set by Spear Pillar's Cyrus scene) and Cynthia's talk (person 0) ask
    "Are you ready?"; YES runs SpearPillarDistorted_EnterDistortionWorld: the message, a fade out, **`DoDWWarp`** (a marked
    stub in the generated file: `pl_stub DoDWWarp  // STEP 7 ...`; Platinum's FieldSystem_StartDWWarp, the warp effect, an app
    the script waits for), ReturnToField, `SetPartyGiratinaForm 1` (now Black 2's PokePartySetForme: each party Giratina to the
    Origin Forme), then `Warp MAP_DISTORTION_WORLD_1F, 55, 40, DIR_SOUTH`: generated as `RTReserveScript 6` and
    `pl_Warp 699, 55, 40, 1`. Zone 699 is installed as a converted map (data/platinum/worklist.json) and its generated file
    (1864_pearl_distortion_world_1f.s) holds that continuation (W1070_0116_S: the fade in). Step 7 replaces the stub with
    its warp effect and builds the zone; the entry needs nothing else.
  - **The way back before the end:** the 1F portal (DistortionWorld1F_ReturnToSpearPillar: `SetPartyGiratinaForm 0`, Warp
    SPEAR_PILLAR_DISTORTED (31, 33) south); the distorted pillar's warp 0 (31, 53) leads to Mt. Coronet 6F's warp 2.
  - **What Platinum sets inside, in order** (scripts_distortion_world_*.s and overlay 9, read only):
    VAR_DISTORTION_WORLD_PROGRESS (PVAR_4055): 1 ENTERED_1F (1F's frame script), 2 JUMPED_ON_1F_ELEVATOR (C), 3 ENTERED_B1F,
    4 SAW_B1F_MESPRIT (C), 5 TALKED_TO_B2F_CYNTHIA, 6 TALKED_TO_B3F_CYRUS, 7 FINISHED_BOULDER_PUZZLE (B6F), 8 ENTERED_B7F,
    9 LISTENED_TO_CYNTHIA_CYRUS (C; a lost battle with Cyrus sets it back to 9), 10 WON_CYRUS_BATTLE, 11-13 the Giratina room's two shadows and Giratina's arrival (C), 14
    BATTLED_GIRATINA (the Giratina room's on-load after the battle); FLAG_DISTORTION_WORLD_STEPPING_STONES (PFLAG_0977, B6F);
    FLAG_DISTORTION_WORLD_PUZZLE_FINISHED (PFLAG_09AD, C: the three boulders in B6F's pits). Set by C only, and with no Black 2
    id in the registry yet: VAR_DISTORTION_WORLD_CYRUS_APPEARANCE (PVAR_405B = 1, Cyrus rode the B4F elevator) and
    FLAG_DISTORTION_WORLD_GIRATINA_SHADOW_1, _2 (PFLAG_09AE, 09AF, B4F's shadows); the save's persisted map features (moving
    platforms, boulders) are overlay 9's. Battles: Cyrus in B7F (TRAINER_GALACTIC_BOSS_CYRUS_DISTORTION_WORLD = PTRAINER_404,
    Lv 48); Giratina (StartGiratinaOriginBattle 487, Lv 47): caught, FLAG_CAUGHT_GIRATINA (PFLAG_0121) and
    FLAG_HIDE_TURNBACK_CAVE_GIRATINA_ROOM_GIRATINA (PFLAG_0250) set, FLAG_HIDE_TURNBACK_CAVE_GIRATINA_ROOM_ITEM (PFLAG_0278)
    cleared; beaten or fled from, none of the three (Giratina waits in Turnback Cave, chapter 12). The portal then:
    `EnableHiddenLocation HIDDEN_LOCATION_SPRING_PATH` (= `pl_SetHiddenLocation 2`, Black 2's map replacement),
    VAR_EXITED_DISTORTION_WORLD_STATE (PVAR_40AA) = 1, `Warp MAP_SENDOFF_SPRING, 32, 17, DIR_SOUTH` (Black 2 zone 381).
  - **Start B** (notes/PLATINUM_CHAPTERS.md, chapter 9) is exactly that end, on the caught path: part 1's end state from the
    flow check plus the list above (the C-only three left out: no ids). When step 7 is built, its last beat should leave start
    B's state; compare with `platinum_flow_check.py 9`'s state at the restart beat.
- **Generator changes others will see when they regenerate** (pearl_story.py block "plat-ch9", pearl_story.inc block
  "plat-ch9"; Platinum only, Pearl's output unchanged): CheckPartyHasHeldItem (a party loop on the held item: Mt. Coronet
  6F's Dialga and Palkia stairs take an Orb a Pokémon holds, chapter 12), SetPartyGiratinaForm (Black 2's PokePartySetForme),
  SetSpeciesSeen (PokeDexRegist 0: Spear Pillar's Dialga and Palkia), 2FB (Spear Pillar's cutscene: its lines in the field),
  2B5 (a comment, see below), DoDWWarp (the marked stub). `pearl_story.py all` against main's generator: besides chapter 9's
  four files only these change: MAP_TURNBACK_CAVE_GIRATINA_ROOM (chapter 12: SetPartyGiratinaForm 1 is Black 2's now),
  MAP_DISTORTION_WORLD_1F and MAP_DISTORTION_WORLD_TURNBACK_CAVE_ROOM (step 7: their portals' SetPartyGiratinaForm 0),
  MAP_CANALAVE_HARBOR_INN (chapter 12: its 2B5 stub is a comment now; both do nothing). Each still passes b2_script_check.
- **2B5 (Sendoff Spring, the Harbor Inn):** Platinum sets the save's exit location (where an Escape Rope or Dig leads) to the
  Spring Path, since the player came by a script warp. Black 2 has no command for it: it remembers its escape point when the
  player walks from the overworld into a cave (ov035 GameData_SetEscapeRopeZone). Sendoff Spring has no Escape Rope; in
  Turnback Cave's rooms that allow one, it leads to the last cave entrance until the player has walked out by the Spring Path
  once. It would need C (a script command for the escape point); listed as cosmetic.
- **For chapter 10** (its start against this end: `platinum_flow_check.py 9 --next`, 8 findings): drop PFLAG_00E8,
  PFLAG_0145, PFLAG_0182 (the HQ's button shows the painting's shards), PFLAG_0298, PVAR_407F=1, PVAR_410D=1 (the button
  sets 0), PVAR_4114=1; and `FlagReset PFLAG_01F7`, not 01F6 (the Pokétch Co. president in his company, chapter 3's handoff).
  It also lacks most of what chapters 6-9 leave; `platinum_flow_check.py 9 --end` prints chapter 9's whole end (start B and
  part 2) as a test start to begin from: the Black Flute (68), the Galactic Key (440), the Master Ball (1); Saturn, both
  Cyruses (the HQ's and the Distortion World's), Mars, Jupiter and the Spear Pillar grunts beaten; the HQ's doors and
  people; PFLAG_015E, PVAR_40A6=2, PVAR_40AA=2, `pl_SetHiddenLocation 2` (the Spring Path).
- **For chapter 12:** Mt. Coronet 6F (this chapter's zone) switches its four stacked warps by FLAG_SPEAR_PILLAR_IS_DISTORTED,
  VAR_EXITED_DISTORTION_WORLD_STATE >= 2, FLAG_UNLOCKED_DIALGA_PALKIA_SPEAR_PILLAR and the Adamant or Lustrous Orb in the
  Bag or held (now both). Spear Pillar's on-transition sets VAR_HALL_OF_ORIGIN_STATE 1 after the Hall of Fame with the
  National Pokédex, the Azure Flute and the deliveryman's third gift. Sendoff Spring's Cynthia stays until the Hall of Fame
  hides her (FLAG_HIDE_SENDOFF_SPRING_CYNTHIA); its on-transition shows Turnback Cave's Griseous Orb when Giratina is caught.

## Chapter 10 (plat-ch10, 2026-11-07)
- **Chapter 10's beats** are row "10" of data/platinum/story_flow.json (47 beats): `PEARL_VERSION=platinum python3
  b2tools/platinum_flow_check.py 10` (0 findings) and `platinum_flow_compare.py 10` (every beat ends the same on both sides; what
  it still lists is chapter 11's start, below). Platinum's own order: Rowan's lab scene after the Distortion World; Valor
  Lakefront open; Route 222; Sunyshore: Flint at the gate (a frame script on arrival), Flint at the Gym's door, Volkner on the
  lighthouse deck, Flint steps aside; the Gym (Pearl's gears: Platinum's gear tables are in its dump byte for byte), Volkner;
  Barry and Jasmine on the north beach (HM07); Route 223, Victory Road; the lobby: Barry's battle, the guard; the Elite Four,
  Cynthia, the corridor, the Hall of Fame.
- **The heights** (found here, done on main by the lead): work/platinum/heights was older than the heights fix, so script
  placements used old heights (9,755 tiles in 221 chunks). With `platinum_events.py --heights` the League lobby 1F's doorway
  (chunk 207, (9-13, 0-3)) is 0, not 144: the guard at (11, 3) stands on the floor (the zone's events and his SetObjectEventPos
  to (12, 3), y 0). heights_check on chunk 207: 0 faults. Chapter 2's note about him is closed.
- **Chapter 10's scenes in other chapters' zones** (their owners regenerate them; checked here from the generated files):
  - Chapter 1, Sandgem lab: the on-transition puts Rowan at (7, 14) and the counterpart at (6, 14) while
    VAR_SANDGEM_TOWN_LAB_STATE (PVAR_40A6) is 2 or 3; frame script 15 (state 2): VAR_EXITED_DISTORTION_WORLD_STATE 2 -> 3,
    FLAG_HIDE_VALOR_LAKEFRONT_COLLECTOR (PFLAG_027D) set, VAR_VALOR_LAKEFRONT_BLOCK_SUNYSHORE_STATE (PVAR_4112) 1, the trio's
    hide flags cleared (PFLAG_01DF, PFLAG_01E0, PFLAG_01E1), state 3. Sunyshore's on-transition then hides the lab's
    counterpart (PFLAG_0199) and sets state 4.
  - Chapter 6, Valor Lakefront: the step trigger at (724, 789-791) is off and the collector gone once PVAR_4112 is 1.
  - Chapter 8, the caverns: Azelf and Uxie can be battled after the lab scene; a catch sets FLAG_CAUGHT_AZELF / _UXIE
    (PFLAG_0126, PFLAG_0127), the Hall of Fame shows the uncaught ones again. Mesprit's roaming stays a stub (the lead's list).
- **Chapter 10's test start** (notes/PLATINUM_CHAPTERS.md), checked by hand against chapter 9's section and Platinum's scripts
  (chapter 9's row isn't on main), and with the flow check against chapters 7's and 8's ends (end_vs_start in
  work/agents/plat-ch10/tools): chapter 8's corrections (no PFLAG_0298, no PVAR_407F=1, no `FlagReset PFLAG_01F3`, PFLAG_013E
  and chapter 8's side flags and items); no `FlagReset PFLAG_01A8` (chapter 6's); chapter 7's end (its side flags and items,
  the Pokétch with apps 0, 1, 3, 4, 6, `FlagReset PFLAG_01F7` in place of `FlagReset PFLAG_01F6`, PVAR_4078=6, Canalave's
  PFLAG_01B3, PFLAG_01B5, PFLAG_01BD and Pastoria's PFLAG_020C set, not reset); chapter 9's Storage Key grunt removed
  (PFLAG_0223 set, not reset). **When chapter 9's row is on main:** `platinum_flow_check.py 9 --next`; chapter 9's own side
  flags and items (the HQ's and Mt. Coronet's) aren't in it yet. Chapter 8's start lacks `FlagReset PFLAG_01F7` (chapter 7's
  end); chapter 9's start has the same faults chapter 8's handoff lists.
- **For chapter 11** (`platinum_flow_check.py 10 --next`, 8 findings, all in chapter 11's start):
  - Marley (Victory Road 1F back 2, our zone): its start has FLAG_TRAVELED_WITH_MARLEY (PFLAG_00E6), PFLAG_01E6 and
    VAR_VICTORY_ROAD_1F_ROOM_2_FOLLOWER_MARLEY_STATE (PVAR_4090) 2. The back rooms are post-game: Victory Road 1F's collector
    stands on their warp at (45, 33) until the on-transition hides him (FLAG_GAME_COMPLETED and the National Pokédex). So
    Marley is chapter 11's beat in chapter 10's zone; its start may keep them only if chapter 11 plays her part first.
    plat-ch10 regenerates MAP_VICTORY_ROAD_1F_BACK_2 (her three triggers: SetPlayerBike is plat-ch4's form change, SetHasPartner
    Black 2's pairing; the generated file passes b2_script_check; scene_check finds only Platinum's own paths from starts the
    scene isn't made for);
  - PFLAG_023A, PFLAG_023B (the corridor's Cynthia and Rowan hidden): the corridor's scene clears them, Cynthia's room sets
    them again before it; harmless either way;
  - PFLAG_0298, PVAR_407F=1: chapter 8's corrections (Maylene is back in her Gym; only the temple guard's scene sets the var);
  - PVAR_409E=1 (VAR_STARK_MOUNTAIN_ROOM_3_STATE): the Hall of Fame sets it only after FLAG_TALKED_TO_BATTLEGROUND_BUCK.
  - What chapter 10 leaves that its start lacks: the Beacon Badge's TM57 (PFLAG_00B6), HM07 (PFLAG_009A, item 424), TM56
    (PFLAG_00CE, item 383), Cynthia beaten (PFLAG_00B4, the E4 flags: the lobby's on-transition clears those on entry), the
    guard moved (PFLAG_00AF), Barry's battle (PVAR_40EF 1), Flint and Volkner (PFLAG_0239, PFLAG_0162, PFLAG_0281), Jasmine's
    scene (PVAR_407E 3, PFLAG_0255), PVAR_40A6=4, PVAR_40F4=1, the Hall of Fame's flags (PFLAG_0982, PVAR_410F 1, PFLAG_02A0),
    and chapters 7's and 8's side flags (above).
- **Generator changes others will see when they regenerate** (pearl_story.py block "plat-ch10", pearl_story.inc block
  "plat-ch10"; Platinum only, Pearl's output unchanged): FindPartySlotWithNature = a party loop on Black 2's
  PokePartyGetParam nature (0x70) and PokePartyIsEgg (it was a stub [Pearl too]: the Pokétch developer gave his apps by
  chance). Only Sunyshore's east house uses it.
- **Tool changes** (marked "plat-ch10"; chapters 2-8 give what they gave): platinum_flow_check: a beat's "set" may give
  "nature_slot" (FindPartySlotWithNature's answer, default 255) and "caught": 0 (a legendary not caught; default caught);
  pl_CheckWonWildBattle wins; pl_ClearGame sets FLAG_GAME_COMPLETED (PFLAG_0964) and ends the beat as a zone change; a frame or
  step scene on a map-local var that ends by leaving the zone (a Warp, the game clear) isn't reported as playing again.
  platinum_flow_compare: ClearGame on both sides sets FLAG_GAME_COMPLETED and arrives in the player's room.

## Chapter 11 (plat-ch11, 2026-11-07)
- **Chapter 11's beats** are row "11" of data/platinum/story_flow.json (85 beats; work/agents/plat-ch11/tools/beats11.py writes it):
  `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py 11` (0 findings) and `platinum_flow_compare.py 11` (every beat
  ends the same on both sides; what it lists is the tool's limits: the deliveryman's map script, global 10200, isn't run and
  Platinum's side is its Mystery Gift; the ruins' dot commands; the collector's on-transition order; the next start).
  Chapter 10's end against this start: `platinum_flow_check.py 10 --next`, one finding on purpose (FLAG_FIRST_ARRIVAL_SUNYSHORE_CITY,
  2485 here: Black 2's code sets it on arriving, no script does).
- **Marley is this chapter's** (plat-ch10's finding): Victory Road 1F's collector stands on the back rooms' warp (45, 33) until
  the on-transition hides him (game clear and the National Pokédex). Beats 3-9 play her part in chapter 10's zones from their
  generated files as they are (her two triggers in MAP_VICTORY_ROAD_1F_BACK_2, FLAG_TRAVELED_WITH_MARLEY, the way out to Route
  224). Nothing is needed from plat-ch10. The Battleground's Marley needs her flag.
- **Registry** (data/platinum/pearl_story_ids.json, src/include/platinum/pearl.h; pearl_ids.py block "plat-ch11", Platinum only):
  - New ids: the Battleground's Leaders 853-860 -> 880-887 (the index files them as variants; the Battleground battles them by a
    var), Barry's Fight Area partner teams 923-925 -> 889-891 (the tag battle's partner by the starter: it was a stub, the
    Fight Area's scene stopped at the battle).
  - Riley's Battleground team (861) shared Black 2 trainer 816 with Barry's Route 201 team for a player who chose Chimchar
    (852): one record for both, so whichever installed last was both. 861 is 888 now; 852 keeps 816 (chapter 1's file doesn't
    change). The dummies 785 and 786 (no script or table battles them) had 814 and 815, which Barry's 850 and 851 got again:
    they have no id now.
  - Why: the pool of ids past 813 didn't leave out the ones already taken. It does now, and the tool stops if two Trainers share
    an id or one goes past 892 (the moved defeat flags are 2561-2639: ids 814-892). **One id is left (892).** A chapter that
    needs more Trainers past 813 needs more moved flags first (patches/platinum_trainer_flags.py, a free flag range).
- **Generator changes others will see when they regenerate** (pearl_story.py block "plat-ch11", pearl_story.inc block "plat-ch11";
  Platinum only, Pearl's output unchanged): GetRandomBattlegroundTrainers (0x2F4) is `pl_GetRandomBattlegroundTrainers`, Platinum's
  draws as Black 2 codes (the vars fill dynamic sprites); CompareVarToValue on a var the file fills only from a dynamic sprite var
  (SetVarFromVar) compares with the graphics' Black 2 code, as plat-ch1's rule does for the sprite vars themselves.
  `pearl_story.py all` against main's work/platinum: only the Battleground (MAP_SURVIVAL_AREA_WEST_HOUSE) and the Fight Area change.
- **Tool changes** (marked "plat-ch11"; chapters 2-8 and 10 give what they gave): platinum_flow_check reads Black 2's FlagGet n
  (CheckGameCompleted: 2400) by its pearl.h name; the National Pokédex as "NATDEX" (pl_SetNationalDex, also in a start's
  TEST_LINES; compared with the next start); `pl_CheckLocalDexCompleted(OrChampion)` (the champion rule; "localdex" in a beat's
  set); RTCGetWeekDay ("weekday", default 1: a weekday); `pl_GetLeagueVictories` ("league_wins", default 1 after the game clear);
  the Battleground's draw (its first three Leaders and the first other Trainer); a Trainer put in a var and battled by it; the
  party's legendaries ("PARTY:species", caught unless "caught": 0, plat-ch10's rule), the three Regis for Regigigas, the
  deliveryman's six gifts as pearl_story.inc gives them ("PARTY:486F" the event Regigigas; "party" < 6 for the Egg and Regigigas),
  the Regi ruins' dots; a person's global script by the file's PearlProxy_n (the deliveryman's 10201).
  platinum_flow_compare: the National Pokédex on both sides (Platinum's 0x22D set/get, the generated pl_SetNationalDex /
  pl_GetNationalDex), CheckGameCompleted and the generated FlagGet 2400 as FLAG_GAME_COMPLETED, a start's 2400, 2478, 2480 and
  2485 as Platinum's flags (pearl_ids SYSTEM_SAME), the Battleground's draw and its copied sprite var. Chapter 7 now lists two more
  "next start" lines (Canalave's arrival, 2478, which Black 2's code sets) and chapter 10 one other; chapter 5 is the same.
- **This chapter's scenes in other chapters' zones** (their owners regenerate them; checked here from the generated files as they are):
  - Chapter 1, Sandgem lab: Rowan's talk takes the champion rule (pl_CheckLocalDexCompletedOrChampion), Oak's scene, the
    National Pokédex, the Poké Radar (item 431); with VAR_FIGHT_AREA_STATE 2 (the tag battle first) Oak's scene hides the Fight
    Area's blockade too.
  - Chapter 8, Snowpoint: the SS Spiral's sailor (game clear) sails to the Fight Area (623, 434) facing east, Cynthia's farewell
    the first time (FLAG_SAILED_TO_BATTLE_ZONE, PFLAG_0157); the temple guard's step trigger (366, 198) brings Candice with the game
    clear and the National Pokédex (VAR_SNOWPOINT_CITY_STATE PVAR_407F 1), and Snowpoint's on-transition hides her after.
  - Chapter 10, Victory Road 1F and its back rooms: the collector and Marley (above).
  - Chapter 7, Iron Island B3F, and chapter 8, Mt. Coronet north 1F room 2: with the event Regigigas in the party their map scripts
    move the entrance room's warp away, so the ruins' doors lead to Registeel's and Regice's rooms (beats 60 and 69). Route 228
    (this chapter's) does the same for Regirock.
  - Every Mart: the deliveryman (the shared piece): his fifth gift is the event Regigigas.
- **Later chapters' scenes that read this chapter's flags:** Charon's arrest (FLAG_ARRESTED_CHARON_STARK_MOUNTAIN, PFLAG_00D6)
  switches the League to the Elite Four's and Cynthia's rematch teams (chapter 10's rooms; 866-870 have ids), shows Looker in the
  Veilstone Game Corner (FLAG_HIDE_GAME_CORNER_LOOKER, PFLAG_01A3 cleared: chapter 5's zone), brings Cynthia to the Celestic ruins'
  painting (chapter 7's zone), and opens the Battleground. Buck leaving the Battleground (FLAG_BUCK_LEFT_BATTLEGROUND, PFLAG_00E7)
  puts him in the Battle Tower's salon (step 8). Buck's Battleground talk (FLAG_TALKED_TO_BATTLEGROUND_BUCK, PFLAG_0125) lets the
  Hall of Fame show Heatran again if it wasn't caught (chapter 10's scene).
- **For chapter 12** (`platinum_flow_check.py 11 --next`, 4 findings, all in chapter 12's start): it sets PFLAG_01F7 (the
  Pokétch Co. president hidden in his company; its TEST_LINES reset PFLAG_01F6 instead: use `FlagReset PFLAG_01F7`, as chapters
  10's and 11's starts do), PFLAG_0298 (chapter 8's correction: Maylene is back in her Gym), PFLAG_023A and PFLAG_023B (the
  corridor's Cynthia and Rowan: harmless). It lacks Black 2's Fight Area arrival 2488 (this chapter goes there; 2487 and 2496 are
  there). PVAR_DELIVERY: this chapter ends at 5 (the event Regigigas given); the Secret Key, the sixth, is chapter 12's.
- **Waits for others:** the Survival Area north house's shard tutor (plat-tutors); the Ribbon Syndicate 1F's ribbons (Gorgeous,
  Royal, Gorgeous Royal: GetPartyMonRibbon, SetPartyMonRibbon, CountPartyRibbons, a C piece with plat-tutors' small commands; its
  2F, the spa, isn't installed, as in Pearl's 1.0, and the elevator's trip there is a stub); Route 226's trade (the lead's
  cross-chapter list); step 8: the Fight Area's gate at (654-655, 423) to BATTLE_FRONTIER_GATE_TO_FIGHT_AREA, the Villa's two
  Frontier pieces, the Battle Tower's Buck.

## Chapter 12 (plat-ch12, 2026-11-07)
- **Chapter 12's beats** are row "12" of data/platinum/story_flow.json (55 beats; work/agents/plat-ch12/tools/beats12.py writes it):
  `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py 12` (0 findings) and `platinum_flow_compare.py 12` (all 48 beats
  that run a script end the same on both sides; its 50 problems are each on both sides: the tool doesn't run the deliveryman's
  gifts, the Pokémon caught or the Azure Flute's event). Two starts: A (Canalave) and B (Turnback Cave's Giratina room, Giratina not
  caught in the Distortion World), `{"restart": "B"}` before the last two beats.
- **The start** is chapter 11's end (`platinum_flow_check.py 11 --end`; work/agents/plat-ch12/tools/start12.py writes both starts),
  less PFLAG_0145 (FLAG_UNLOCKED_DIALGA_PALKIA_SPEAR_PILLAR: the Celestic elder sets it after the Hall of Fame, this chapter's beat;
  chapters 10's and 11's starts have it early, harmless there), plus the National Pokédex, the Spring Path (`MapReplaceSetEvent 7,
  1, 0`) and Black 2's arrival flags 2487, 2488, 2496. `platinum_flow_check.py 11 --next`: 0 findings.
- **Generator changes others will see when they regenerate** (pearl_story.py block "plat-ch12", pearl_story.inc block "plat-ch12";
  Platinum only, Pearl's output unchanged). A command another block gave a handler first keeps it.
  - StartFatefulEncounter (0x318) = `pl_StartFatefulEncounter`, PearlB2 extension 0xBE (patches/platinum_postgame.py): Black 2's
    static wild battle with PKM_PARAM_FATEFUL_ENCOUNTER set on the wild Pokémon, which a catch keeps. Flower Paradise's Shaymin, so
    Floaroma's Gracidea (chapter 3's FindPartySlotWithFatefulEncounterSpecies) is given. It was a stub: no battle at all.
  - Rotom's forms, on Black 2's own commands: GetRotomFormsInSave = extension 0xBD (party, Day Care and boxes, as Platinum; it
    replaces plat-rooms' "every form 0"), GetPartyRotomCountAndFirst (a party loop), SetRotomForm = PokePartyChangeRotomForme (the
    same move rule, as Black 2's own appliance script, global 10315), GetPartyMonForm2 = PokePartyGetForme, GetPartyMonMove =
    PokePartyGetMove, CountRepeatedSpeciesInParty = PokePartyGetCountBySpecies, FindPartySlotWithSpecies = PokePartyFindBySpecies,
    OpenSummaryScreenTeachMove + GetSummarySelectedMoveSlot = CallPokeMoveReplace (the forget-a-move screen; 4 when none chosen).
  - The party select and the forget-a-move screen written with a CloseMessage after the fade-out (FadeScreen, WaitFadeScreen,
    CloseMessage, the app, its result, ReturnToField, FadeScreen): the fades and the ReturnToField are dropped, as plat-ch7's rule
    does without the CloseMessage. In Rotom's Room the ReturnToField was a FieldOpen on an open field: a hang with two Rotom.
  - What changes on `pearl_story.py all` besides this chapter's Flower Paradise and Rotom's Room: the three shard tutors (chapter
    6's Route 212 house, chapter 8's Snowpoint northeast house, chapter 11's Survival Area north house) get the real forget-a-move
    screen and GetPartyMonMove (their tutor commands stay stubs: plat-tutors), and chapter 5's Solaceon seal house its
    FindPartySlotWithSpecies. Each still passes b2_script_check.
  - pearl_story.inc, the deliveryman (shared): Oak's Letter also sets VAR_SHAYMIN_EVENT_STATE (PVAR_4057) 0 -> 1, as Platinum's
    Mystery Gift does (scrcmd_mystery_gift.c InitShayminEvent): Route 224's on-transition makes it 2 and Marley's step trigger at
    (903, 496-498) comes, and she thanks Shaymin in Oak's scene. Without it Marley never appeared.
  - pearl_story.inc, the Trophy Garden (chapter 6's Mr. Backlot, shared): Platinum's tenth daily Pokémon is Ditto, Pearl's Porygon
    (decomp encounters_trophy_garden.json daily_encounters).
- **New patch for Platinum's list:** `platinum_postgame` after `platinum_regigigas` (it wraps sExtModules' leftovers row again and
  hands every other sub-command to the regigigas wrapper). 568 bytes in the resident pool. Offline: `PEARL_VERSION=platinum python3
  b2tools/patches/platinum_postgame.py` compiles and links it against the decomp's link map. b2_script_check knows 0xBD (2 bytes)
  and 0xBE (4).
- **Tool changes** (marked "plat-ch12"): platinum_flow_check: `Flow.ch12_op`, the interpreter's last rows (pl_CheckDistributionEvent
  by PVAR_DELIVERY; StartFatefulEncounter's "PARTY:<species>F"; the time of day "time"; one party Rotom and its form; "moves",
  "has_move", "move_slot", "menu" in a beat's set). Black 2's party commands there answer only when the state or the beat knows,
  so chapters 2-11 give what they gave (checked: the same output as main's tool but for chapter 11's Oak's Letter, which now also
  sets PVAR_4057). scene_check: three ACCEPT rows (Rotom's Room's two notebooks on tables, Fullmoon's and Newmoon's dock bollards and
  Pal Park's gate worker behind the counter: the last two the same in Pearl's 1.0).
- **This chapter's scenes in other chapters' zones** (their owners regenerate them; checked here from the generated files):
  - Every Mart: the deliveryman's sixth gift, the Secret Key (PVAR_DELIVERY 5 -> 6).
  - Chapter 7: the Celestic elder's research (PFLAG_0145); Eldritch's house (the son's nightmare, PVAR_4106 1 -> 2 -> 3, the Lunar
    Wing), Eldritch's boat in Canalave (talk 16: Fullmoon Island), the Harbor Inn's Darkrai dream (frames 2 and 3,
    VAR_DARKRAI_EVENT_STATE 1 -> 2 -> 3) and Canalave's frame 23 after it (state 4).
  - Chapter 9: Mt. Coronet 4F room 1's Adamant and Lustrous Orbs (57, 2), (61, 2); Mt. Coronet 6F's stairs (7, 5) to Dialga's,
    then Palkia's, then the normal pillar.
  - Chapter 3: Eterna's Galactic building 1F's wall (1, 5): the Secret Key, distribution event 3 and PFLAG_0081; Floaroma's beauty
    (object 3): the Gracidea with the fateful Shaymin.
  - Chapter 4: the Old Chateau 2F room 2's TV at night: Rotom (Lv 20), for Rotom's Room.
- **The roamers** (the lead's cross-chapter list; ActivateRoamingPokemon stays a stub, as Pearl's 1.0): patches/roamers.py reads
  Pearl's src/include/pearl.h in a Platinum build too. Cresselia's release flag there, Black 2 flag 361, is Platinum's
  FLAG_MET_CRESSELIA as well, so she roams after Fullmoon Island. Mesprit's, 559, is Platinum's FLAG_HIDE_ETERNA_CITY_GALACTIC_GRUNTS
  (Platinum's Verity Cavern Mesprit is FLAG_HIDE_VERITY_CAVERN_MESPRIT, PFLAG_01DF = 531, after the Distortion World). Oak's three
  birds (Eterna's south house: FLAG_ACTIVATED_ROAMING_LEGENDARY_BIRDS) need three more slots: Black 2's EncountSave has two.
- **Step 7 (the Distortion World):** Turnback Cave's Giratina room portal (its sign at (11, 14), YES) warps to zone 709, the
  Distortion World's Turnback Cave room, as Platinum does (the same rule as Spear Pillar's entry, the lead's call). Zone 709 has no
  events: its portal back (DistortionWorldTurnbackCaveRoom_Portal, script 2, which warps to the Giratina room (11, 15)) and the
  Griseous Orb live in overlay 9's data, not in the event files, so step 7 must build them. Until then the room is a dead end.
- **Waits for others:** plat-tutors (the shard tutors' own commands); the roamers (above); step 6, the appliances' own models
  (Platinum's mmodel 400-404; Black 2's Rotom form walkers stand in).

## Shared piece: Platinum's party commands (plat-tutors, 2026-11-07)
- **What is real now** (pearl_story.py and pearl_story.inc blocks "plat-tutors", PearlB2 extension 0xB0-0xB6, decomp overlay 376,
  patches/platinum_tutors.py; notes/EXT_COMMAND.md): the three shard tutors (CheckHasLearnableTutorMoves,
  ShowMoveTutorMoveSelectionMenu, CheckCanAffordMove, PayShardCost, ResetMoveSlot; their Shard lists' ShowShardCost and
  CloseShardCostWindow), GetPartyMonContestStat, GetPartyMonRibbon, SetPartyMonRibbon, CountPartyRibbons, BufferRibbonName,
  GetPartyMonFootprintType, GetPartyMonEVTotal (Black 2's PokePartyGetEVTotal). The tutors' forget-a-move screen and move read
  are plat-ch12's handlers. The last won Trainer battle's turn count + 1 goes into Black 2 work 0x40FD
  (VAR_TOTAL_TURNS_LAST_BATTLE) at the battle's end, in C: the Pokémon Mansion's lobby needs no regeneration.
- **The tutor's question** right before his move list now uses the plain window (Black 2's list menu shows an entry's
  description, here the move's Shards, only there). After the list the plain window stays open, so the next person's line
  closes it first (MsgWinCloseAll, from the window dataflow).
- **Zones regenerated in plat-tutors' tree** (their owners: regenerate after merging, or take these): chapter 6's
  MAP_ROUTE_212_SHARD_WEATHER_TM_HOUSE, MAP_PASTORIA_SCARF_GUY_HOUSE, MAP_ROUTE_213_FOOTSTEP_HOUSE; chapter 8's
  MAP_SNOWPOINT_NORTHEAST_HOUSE; chapter 10's MAP_SUNYSHORE_JULIA_HOUSE, MAP_SUNYSHORE_MARKET; chapter 11's
  MAP_SURVIVAL_AREA_NORTH_HOUSE, MAP_RESORT_AREA_RIBBON_SYNDICATE_1F. All pass b2_script_check at their levels.
- **Still stubs there** (not this piece): Snowpoint's tough words (CheckAllToughWordsUnlocked, TryBufferAndUnlockRandomToughWord),
  Julia's custom words (ChooseCustomMessageWord, BufferCustomMessageWord), SetPartyMonRibbon's TV news (Black 2's TV has no
  such show).

## Step 6: music, title, credits (plat-music, 2026-11-07)
- **The scenes that waited for Platinum's songs now play them** (pearl_story.py block "plat-music"; notes/MUSIC.md "Platinum"):
  Looker's theme (SetBGM 1200: chapter 2's Jubilife, 5's Veilstone, 6's Route 213, 9's Mt. Coronet 2F, 11's Stark Mountain 3),
  the Villa's piano, audio system and music box (chapter 11's Resort Area southwest house), Spear Pillar's cutscene songs
  (chapter 9), the Poké Radar's song (chapter 11's Route 202 demonstration), the Battle Hall's BP fanfare (step 8's zone: its
  WaitFanfare had no fanfare to wait for), the Game Corner's coins (Black 2's cash register). Still counted stubs, as listed:
  PlaySE 1480 (SEQ_SE_PL_KUSARI, Spear Pillar's chains) and 1490 (SEQ_SE_PL_SYUWA: Turnback Cave's portal, the Distortion
  World's): no Black 2 sound; Platinum's own would need C.
- **Regenerate** the 14 zones (or `all`): MAP_JUBLIFE, MAP_VEILSTONE, MAP_VEILSTONE_GAME_CORNER, MAP_MOUNT_CORONET_SPEAR_PILLAR,
  MAP_MOUNT_CORONET_SOUTH_2F, MAP_STARK_MOUNTAIN_INTERIOR_3, MAP_TURNBACK_CAVE_GIRATINA_ROOM, MAP_ROUTE_202, MAP_ROUTE_213,
  MAP_RESORT_AREA_SOUTHWEST_HOUSE, MAP_BATTLE_HALL, MAP_DISTORTION_WORLD_1F, MAP_DISTORTION_WORLD_GIRATINA_ROOM,
  MAP_DISTORTION_WORLD_TURNBACK_CAVE_ROOM. Only their sound lines change; each passes b2_script_check with and without the ids.
- **For step 7:** the Distortion World plays SEQ_PL_D_GIRATINA (installed: its zones' headers); Platinum plays no surf song
  there (zone_flags' surf_bgm bit for those zones); its portal sound is the SYUWA stub above.
- **For step 8:** the Frontier's zone songs are installed (BF_*); the Brains' battle and victory songs (SEQ_PL_BA_BRAIN,
  WINBRAIN) and the scripts' SEQ_PL_EYEBRAIN, DON2, FRO, BF_CASTLE02 convert but aren't installed; data/battle_music.json
  "_versions_doc" says where they go (the Brains need Black 2 classes of their own first).

## Shared piece: in-game trades, fossil restoring, roamers (plat-trades, 2026-11-07)
- **What is real now** (pearl_story.py and pearl_story.inc blocks "plat-trades"; version rows NPC_TRADES, FOSSIL_RESTORER,
  ROAMER_COMMAND: Platinum on, Pearl and Diamond off until 1.0.1; PearlB2 extension 0xA7, 0xA8; notes/EXT_COMMAND.md):
  - The four trades (Oreburgh's Kazza, Eterna's Charap, Snowpoint's Gaspar, Route 226's Foppa). OpenPartyMenuForTrade is
    Black 2's party select (its fades and ReturnToField dropped, as for the other party selects); GetNPCTradeRequestedSpecies
    a constant from the dump's table (b2tools/npc_trade_data.py); StartNPCTrade is extension 0xA7: Black 2's own trade event
    and demo (decomp resident/npc_trade.c), the Pokémon made by Platinum's rules (patches/npc_trades.py's table). Platinum adds
    no trade of its own: its fld_trade.narc has the same four as Pearl's.
  - The Mining Museum's fossil restorer: GetFossilCount, GetSpeciesFromFossil, FindFossilAtThreshold on Black 2's item
    commands over the dump's seven fossils (b2tools/fossil_data.py; Armor and Skull both). Its fossil menu, whose entries
    Platinum adds by a line in a var, is written out for each of the seven (Black 2's ListMenuAdd takes a fixed line).
  - ActivateRoamingPokemon is extension 0xA8. Platinum's five roamers: Mesprit, Cresselia and Oak's three birds (decomp
    resident/roamers.c, patches/roamers.py; the birds' slots in save block 0x41, notes/DATA.md). Release flags are Platinum's
    own; a KO or a catch sets VAR_ROAMING_*_STATE (the Hall of Fame and Oak read them). The Marking Map has six slots.
- **Zones regenerated in plat-trades' tree** (their owners: regenerate after merging, or take these): chapter 2's
  MAP_OREBURGH_NORTH_HOUSE_1F and MAP_OREBURGH_MINING_MUSEUM, chapter 3's MAP_ETERNA_CONDOMINIUMS_1F, chapter 8's
  MAP_SNOWPOINT_NORTHWEST_HOUSE and MAP_VERITY_CAVERN, chapter 11's MAP_ROUTE_226_HOUSE, chapter 12's
  MAP_FULLMOON_ISLAND_INTERIOR and MAP_ETERNA_OAK_HOUSE. All pass b2_script_check; flow_check 2, 3, 8, 10, 11, 12 give 0
  findings as before. No other generated file of main's work/platinum has these commands (grep), so nothing else changes.
- **Still stubs there** (not this piece): Route 226's TurnOnPokedexLanguageDetection (the Meister's Pokédex upgrade; Black 2's
  Pokédex has no such switch), Eterna condominiums 1F's CheckIsPartyMonOutsider and 2B8.

## Shared piece: every chapter's test start from the chapter before's end (plat-starts, 2026-11-07)
- **The starts** (notes/PLATINUM_CHAPTERS.md "How to test the whole story": the env lines in test order, what a start carries
  and leaves out). Each is the chapter before's own end from `platinum_flow_check.py N --end`, chained from chapter 1's new
  game (work/agents/plat-starts/tools/starts.py). `platinum_flow_check.py N --next`, N = 1-11: 0 findings but three on purpose
  (Black 2's arrivals in Eterna 2480, Canalave 2478 and Sunyshore 2485: its code sets them, no script does);
  `platinum_flow_check.py`: 0 findings for chapters 1-12. The `--next` lists in the chapter sections above are done: the
  Pokétch Co. president in his company (`FlagReset PFLAG_01F7`) in chapters 4-6; chapter 9's Storage Key flags, the hiker's
  NO and PFLAG_0145 gone from the earlier chapters' starts; PFLAG_00A7 in chapter 8's; PFLAG_0298, PVAR_407F, PVAR_410D,
  PVAR_4114 and PVAR_40CF as the story leaves them; Snowpoint's arrival (2486) in chapter 9's.
- **Left out on purpose:** side gifts and beaten Trainers no later chapter's beats read (none read any): TMs, held items,
  Plates, balls, Berries and their givers' FLAG_RECEIVED_* / FLAG_OBTAINED_* flags, so the givers give again; the day's flags
  (FLAG_DAILY_*); chapter 3's side Rotom (FLAG_CAUGHT_OLD_CHATEAU_ROTOM: chapter 12 catches the TV's Rotom). Key items, HMs
  and their flags stay. A chapter that comes to read one of the left-out things: say so here, and it goes in the starts.
- **Chapter 1's row** (data/platinum/story_flow.json "1", from data/platinum/beats/1.json): `platinum_flow_check.py 1 --next`
  runs now. Two step triggers begin a tile before their scripts' first case, as in Platinum (Route 201's "Barry follows" at
  x 109, the script knows 110-113; Sandgem's assistant at z 842, the script knows 843-848): those beats stand on a tile the
  script knows.
- **Other rows changed (small):** chapter 4: the south gate's frame script (coming from the Cycling Road: forced cycling) and
  its exit trigger (cleared). Before, chapter 4's end kept FLAG_FORCE_BIKING_IN_GATE for every later start. Chapter 5: the
  warehouse's inner door must leave FLAG_USED_STORAGE_KEY clear (no Storage Key yet), for flow_compare's sake.
- **Tool changes** (marked plat-starts):
  - platinum_flow_check: `--end` writes the National Pokédex (`pl_SetNationalDex`); `--starts` prints every start as one env
    line in test order; a chapter's section is `## Chapter N` and a word break, so chapter 90's own start is read too.
  - platinum_flow_compare, on story_flow rows: the next start is compared with the chapter's own end (before the later
    chapters' beats its row runs, as flow_check), and with the end state nearest it, not the first one; a warp beat is the
    arrival in its zone (its map scripts run, as in flow_check); a beat's PVAR_ "set" answers a menu or a check, as in
    flow_check; on the Bicycle or not (CheckPlayerOnBike, PlayerGetExState) forks both ways; a row without "compare" options
    takes `won_only` and `carry: "saved"` (rows 2-4 had none: the lost battles' states filled the 48 kept); the side gifts,
    day's flags and Rotom the starts leave out are notes. Problems, main's tool and starts -> now: chapter 2 8 -> 0, 3 133 -> 0,
    4 60 -> 23, 5 22 -> 0, 6 4 -> 0, 7 108 -> 2, 8 108 -> 2, 9 70 -> 0, 10 2 -> 2, 11 40 -> 36, 12 50 -> 48; 1 and 90 still 0.
- **flow_compare's problems left** (its limits, not the story's):
  - chapters 7 and 10: Black 2's arrivals in Canalave and Sunyshore, as flow_check's findings.
  - chapter 4: from the Contest Hall lobby on, Platinum's side forks into more end states than Black 2's (16 against 4) with
    the same flags and vars; the next start lacks flags the zones' arrival scripts set on every visit, which flow_check doesn't
    run (the contest stage's contestants 0x201-0x205, the lobby's reporter 0x213, Route 206's first arrival 0x9E6).
  - chapter 8: the Pokémon Centers' daily Trainer 2 hidden (0x184): the Centers' global init, on every visit.
  - chapters 11 and 12: their owners' lists above (the deliveryman's map script and Mystery Gift, the Regi ruins' dots and
    catches, the legendaries caught, the Azure Flute's event, Victory Road's collector).

## Step 7, the Distortion World's world (plat-dw-world, 2026-11-07)
- **Its beats** are row "9b" of data/platinum/story_flow.json (33 beats; work/agents/plat-dw-world/tools/beats9b.py writes it
  and its start): `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py 9b --next` (0 findings; its end against
  chapter 9's start B: 0). Its start is chapter 9's state at the distorted pillar's YES (its beats up to the restart), on 1F
  (Black 2 zone 699, (34, 30)). Chapters 2-12 still give 0. Two of its beats are chapter 12's (the Turnback room's ball and
  portal).
- **Chapter 9's start B** (notes/PLATINUM_CHAPTERS.md) now carries PFLAG_09AE and PFLAG_09AF, which have Black 2 numbers now
  (2427, 2428); PVAR_405B is 0x4163 (it stays 0 on the story's way: Cyrus rides B4F's elevator only in a scene the boulder
  piece will need). Chapter 9's beat 64's text says the way in is real now.
- **Tool changes** (marked "plat-dw-world"): platinum_flow_check: a beat {"zone", "dw": [x, y, z]} is overlay 9's event at a
  tile of the floor's own tiles (its flag condition, then its commands); a talk beat in a Distortion World floor needs the
  person's condition; "dw_sets" is what the engine's C sets before a beat (the boulders); the macros pl_DWGetPlayer3DPos,
  ActorAdd/ActorDelete, CallWildBattleEx, pl_GetBattleResult; rows sort as 9, 9b, 10; row 9b's --next is chapter 9's start B.
  b2_script_check knows extension 0x20-0x24. pearl_ids: PLATINUM_C_FLAGS / _VARS; an item ball the registry has keeps its flag
  when a new one meets it. gen4_extract (Platinum): the ten floors' own event files 534-543.
- **Generator changes others will see** (pearl_story.py block "plat-dw-world", Platinum only): a Warp into a Distortion World
  floor is in its own tiles: chapter 9's MAP_MOUNT_CORONET_UNUSED_2 (pl_Warp 699, 34, 30; DoDWWarp = pl_DWWarp) and chapter 12's
  MAP_TURNBACK_CAVE_GIRATINA_ROOM (pl_Warp 709, 46, 45) change; both pass b2_script_check. Regenerate them with the ten floors.
- **For chapter 12:** the Turnback room's portal back (its invisible person, script 2: Turnback Cave's Giratina room (11, 15))
  and the Griseous Orb's ball (19, 25; flag 1490) are in the room's event file now (from overlay 9's table).
- **Not built** (notes/PLATINUM_DW.md "Not built, or not as Platinum (the world)"): the boulder puzzle's falls block the story
  at B6F until built; the lake trio's hints, the sky, fog and edges, the surf mount's turns, Platinum's own sounds.
