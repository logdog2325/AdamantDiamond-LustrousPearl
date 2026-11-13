# Platinum's script stubs (plat-stubs, 2026-11-08)

Goal: no field-script command a Platinum player reaches stays a stub. Offline work (no ROM built, nothing played): plat-test
checks it on screen after the merge (checklist below).

## How the stubs were counted
`PEARL_VERSION=platinum python3 b2tools/pearl_story.py all` writes Platinum's zone scripts (work/platinum/src/field_scripts);
each command it can't translate is a `pl_stub NAME` line. work/agents/plat-stubs/collect_stubs.py translates every zone the
world installs (the 69 that keep Pearl's file too) and lists the stub lines by command and zone; make_table.py classifies
them into work/agents/plat-stubs/STUBS.md. Pearl's hand-written files (the Underground, the Pokémon Centers' link rooms) are
not generated and not counted. Sixteen `pl_stub` lines are the `#else` of Platinum's story songs (PlayMusic, SetBGM of
version.STORY_SONGS): a build with sinnoh_music never takes them.

Before: 895 stub lines (172 commands). After: 742 (144 commands). 153 handled.

## What is handled
Rows of version.py turned on for Platinum (block v101-story; Pearl's handlers, checked against Platinum's own commands):
- **DEOXYS_FORMS**: Veilstone's four meteorites. Platinum's 0x262 CheckPartyHasSpecies2 species, var and 0x263 ChangeDeoxysForm
  are the same commands as Pearl's (pokeplatinum scrcmd.c), the same forms 0-3.
- **UNDERGROUND_GIFTS**: Hearthome's goods man, the four Crystals (the same four records, the same lines).
- **GAME_CORNER_CLOSED, MOVED_PEOPLE**: Platinum's Game Corner is Pearl's map (land 196: the same rows 10 and 11) with the same
  people; the coin clerk (object 0) stands at the closed line, (4, 10), and with a Coin Case (Veilstone's southeast house)
  gives TM64 Explosion.
- **STORE_TMS**: Platinum's prize TMs that nothing else gives (its prize list, scrcmd_game_corner_prize.c, against every
  script, item ball, hidden item and Mart): TM44 Rest 3,000, TM108 Endure (TM58) 2,000, TM75 Swords Dance 1,500 at
  Veilstone Dept. Store 3F's left counter (list 12, after TM70); TM10 Hidden Power 2,000, TM74 Gyro Ball 3,000, TM68 Giga
  Impact 7,500 at the right counter (list 13, after TM15). Prices are Platinum's item data (pearl_shops.pearl_price).
- **TOWER_TROPHIES**: Teala's Bronze, Silver and Gold Trophies, on Platinum's rule: the Single record streak only
  (sub_0206BDBC: STAT_TOWER_RECORD_STREAK_SINGLE = the Frontier core's record 0, the Subway's single mode), not Pearl's best
  of any room. pearl_story.inc pl_TowerTrophyStreak.
- **ACCESSORY_SHOP**: Floaroma's flower shop with Platinum's own 22 rows (the dump's overlay 7: the same Accessories 50-71 for
  other Berries and counts, from one Cheri Berry for the Red Flower to 100 Belue Berries for the Photo Board) and lines (its
  flower shop bank keeps Pearl's line numbers).
- **POKETCH_APP_GIFTS** (23, 24): the Stopwatch and the Alarm Clock, which only Platinum's Mystery Gift gives, from the Poké
  Mart deliveryman after his six gifts (PL_DELIVERY_GIFTS 8 for Platinum; his line 19, "received the Pokétch app ...!").
  The Matchup Checker stays the Great Marsh's.

New handlers (pearl_story.py and pearl_story.inc, blocks "plat-stubs"; Platinum only):
- **The Frontier's four lobbies' save** (Factory, Hall, Castle, Arcade): the Tower's handlers (TOWER_ONLY_HANDLERS: CheckSaveType,
  the save window, the banned-species line) there too. As stubs, CheckSaveType kept the last Yes (0) and the common save
  said "It is impossible to save": the challenge couldn't start.
- **The Battle Castle's CP fanfare** after each win (SEQ_PL_FRO, then WaitFanfare): a stub there hangs. version.STORY_FANFARES
  installs it (sinnoh_music); a build without it plays Black 2's item jingle.
- **TryRevertPokemonForm** (the Frontier lobbies, the Tower, the Solaceon Day Care): a Rotom in an appliance back to form 0
  (Black 2's PokePartyChangeRotomForme), Shaymin to its Land Forme. Giratina keeps its Griseous Orb (no script command for a
  held item; Giratina is banned from the facilities). In the Tower the Subway keeps the picks, so tower function 53 answers
  255 and nothing reverts there.
- **The Frontier records machines**: ShowListMenuRememberCursor is Black 2's list menu (it was never shown: the Hall's letter
  list went round for ever); the Hall's species list answers EXIT (the records screen has no Black 2 counterpart). (plat-fix2, 2026-11-11: now the species
  with a record and their records as a message: notes/PLATINUM_FRONTIER.md "The last differences".)
  (plat-records, 2026-11-08) The Tower's, Factory's, Castle's and Arcade's machines show their records as messages
  (notes/PLATINUM_FRONTIER.md "The Frontier's records machines").
- **The Battle Hall's record keeper** (GetBattleHallRecordKeeperStats): the total of the Single records (the Hall's own
  records, pl_HallRecords 1), Platinum's 47 milestones (from the decomp, checked in the dump), the BP, the four words.
- **The Battle Tower's Stats Judge** (JudgeStats): Black 2's PokePartyGetIV (the same stat order), the highest stat's line,
  Platinum's coin toss between equal ones.
- **The Battle Frontier's scratch-off cards**: no touch screen; each card's prize comes out at Platinum's own odds (two Dittos,
  three, two and two of three prizes in nine cells, three scratched: 18 of 84 picks win, a quarter the Nugget, else three of
  a Berry of its 23, from the dump's overlay 111).
- Nothing to do in Black 2: CheckHeapMemory (a debug assert), WaitForTransition before a Frontier scene's warp, Eterna's 0x331
  / 0x332 (people kept drawn through a camera pan), SaveExtraData, CheckIsMiscSaveInit (1), 0x258 / 0x259 (the save's player
  task), GetOverworldWeather on Route 213 (0: its rain sound has no Black 2 sound), Dummy316.

## Decisions (pick closest to Platinum; the user away)
- Platinum's Game Corner stays closed as Pearl's 1.0.1; its six prize TMs nothing else gives are on sale at Veilstone 3F at
  Platinum's prices; TM64's clerk at the closed line. Its four held-item prizes (Silk Scarf, Wide Lens, Zoom Lens, Metronome:
  no other script, ball, hidden item or Mart in Platinum) weren't sold anywhere at first (TMs only, as Pearl's 1.0.1); since
  2026-11-11 (the user: "yes") they are, at Veilstone 2F's battle-item counter at Platinum's prices (`version.STORE_ITEMS`).
- The Tower's trophies count the Single record (Platinum's rule), not the best of any room (Pearl's).
- The Stopwatch and the Alarm Clock come from the deliveryman after the Secret Key (Platinum's own source is its Mystery Gift).
- The scratch-off cards run without their screen at Platinum's odds (the player's picks don't change the odds: the cells lie
  in random places).
- Rotom keeps its appliance form in the Battle Tower (the Subway's picks aren't known to the script); Giratina keeps its
  Griseous Orb in the Day Care.

## Left (STUBS.md has every line)
Link and Wi-Fi (closed), the TV's interviews and shows, sounds Black 2 has none for (silent, no waits), closed places (the Game
Corner's slots and coins, the Prize Exchange, the Great Marsh's tram and binoculars), the lead's 1.0.1 list (the Loto, the
size contest, Vista Lighthouse's binoculars) and other stubs Pearl's 1.0.1 has too, Ball Capsule seals, the Frontier records
screen, the Canalave Library's TV.

For the lead:
- The Game Corner's coin clerk sells Coins for money, and AddCoins is a stub: 1,000 or 10,000 taken, no Coins (Pearl and
  Diamond 1.0.1 the same). A line or a closed counter would be kinder.
- MoveHearthomeGymDPLift and a PlaySE stay in Pearl's question rooms (Platinum's zones 93, 95): Platinum's own gym is plat-gyms';
  its leader room has old warps into these rooms at (1, 17), (3, 17), (5, 17). Not checked whether a player can reach them.
- item_check.py stops on a KeyError for Platinum (an item row without a Black 2 zone): not from this work.

## Checks (offline)
- `PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py`: every chapter, 0 findings.
- Every Platinum zone file (413) assembles and decodes with b2_script_check at its levels, 0 problems
  (work/agents/plat-stubs/check_scripts.py); the Castle's rooms, the Hall and the Tower's lobby also with the story songs
  defined (PEARL_MUSIC_EVENTS).
- `python3 b2tools/version_check.py`: ok (Pearl and Diamond unchanged).

## For plat-test (on screen)
1. Veilstone, a meteorite (Platinum's tiles (729, 616), (731, 622), (732, 628), (730, 629)) with a Deoxys in the party: the cry, the line, Deoxys in the new form
   (summary); without one: the plain line.
2. Hearthome, Mr. Goods at (470, 705) (after his other goods): one Crystal a talk, four in all, in the Underground PC.
3. Veilstone Game Corner: the coin clerk at (4, 10) behind the counter's line, facing down; with a Coin Case: the bonus-round
   line, TM64. Without one: the no-Coin-Case line.
4. Veilstone Dept. Store 3F: left counter ends TM44, TM108, TM75 (3,000, 2,000, 1,500); right counter ends TM10, TM74, TM68
   (2,000, 3,000, 7,500). The TM names and prices on Black 2's shop screen.
5. Floaroma flower shop: greeting, the list of 22 (the Red Flower first), the description line (Berry, how many), buying with
   enough and too few Berries, a full Fashion Case.
6. A Poké Mart after the Hall of Fame, the deliveryman: after the Secret Key, the Stopwatch, then the Alarm Clock (one a
   talk, the app name in the line); the apps in the Pokétch.
7. Battle Tower lobby: Teala at (16, 6) shows after a 20-win Single streak; the Bronze Trophy, its line, the goods in the PC.
8. Battle Tower lobby: the Stats Judge at (24, 7): pick a Pokémon, the overall line, the best stat's line.
9. Each Frontier lobby (Factory, Hall, Castle, Arcade): the attendant's save before a challenge ("saved the game"), then the
   challenge starts; with too few eligible Pokémon, the line with the number.
10. Battle Castle: win a battle: the CP line, the fanfare, the script goes on (no hang).
11. Battle Hall: the record keeper at (8, 8) (BP at 10 total wins, the numbers in his lines); the records machine: the letter list shows,
    a letter goes back to the list, EXIT leaves.
12. Battle Frontier, the scratch-off cards (the north-west booth's attendant, (45, 37)): 1 BP, the fade, sometimes a Nugget or three Berries, else "Please visit again".
13. A Heat Rotom into the Arcade, Castle or Hall: it comes back as plain Rotom (its move replaced); the Solaceon Day Care the same.
14. Eterna: Barry's scene by the Galactic building (the camera pans east): nobody vanishes.
