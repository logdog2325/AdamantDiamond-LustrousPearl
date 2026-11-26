# Pokémon from Unova (Rowan's sixth question)

The user, 2026-11-23: "the same choices as Hoenn" (HoennB2's other-regions option, its notes/OTHER_REGIONS_PLAN.md), for
Lustrous Pearl, Adamant Diamond and Griseous Platinum, released as Pearl/Diamond 1.1 and Griseous Platinum 1.1. The
choices are in notes/DECISIONS.md (2026-11-23). Sinnoh already mixes Generations 1-4, so the option means Gen 5 only.

## What it does

| Piece | Where |
|---|---|
| The question | Rowan's sixth, asked last (system text 54 line 39, `data/text_overrides/pearl_intro.json` GameStart_Text_Empty_18; "six questions", the seasons no longer "Last"); `b2tools/patches/pearl_intro.py` QUESTIONS: YES sets PFLAG_UNOVA (Pearl and Diamond 1075, Platinum 2432; `b2tools/pearl_ids.py` NEW_FLAGS). Mashing A = YES |
| Older saves | the aide in Rowan's lab (Sandgem), the west side (3, 9), Pearl's assistant sprite: `b2tools/unova_aide.py`, through ramanas.py's hooks after postgame_legend's (pearl_story extra entry `RamanasExtra_unova_aide`, pearl_events' extra people). On / off; the Pokémon caught stay |
| The plan | `data/unova.json`: the kinds of every area (fnmatch keys: every zone with wild Pokémon matches one), the version pairs, the starters' places, the places left as they are ("unchanged") or lower ("low"), the teams |
| The slots | `b2tools/unova.py`: picks each version's slots from the plan (about a quarter of each kind of encounter: grass 24 %, surfing 30 %, Good Rod 20 %, Super Rod 19 %), checks the rules (`--check`), prints the lists (`--report`, `--md`) |
| The build | `b2tools/patches/unova_option.py` (after wild): a/1/2/7 file 318 = the edits by table + the HABITAT list's pages with the Gen 5 Pokémon; a/0/9/2 the 13 Unova parties (appended); a/1/7/6 the Gen 5 Pokémon's AREA pages; a/2/8/2 list file 78 (shop 72) = Veilstone 2F's vitamins + 8 stones; gPearlB2Unova (84 B) in the resident pool |
| The game | decomp `src/pearlb2/resident/unova.c`: EncData_Load's read (ov012, a same-size call) applies the zone's edits as its table loads, so grass, surf, the time of day's tables and both rods follow; TrainerData_ReadParty (arm9) reads a Unova party; PearlB2_Roamers_ReadHabitat calls PearlB2_Unova_Habitat (AREA: "area unknown" with the option off, and for the other side of a pair before the Champion); ov302 zukan_common.c's five page reads take the Unova pages |
| The shop | `src/include/pearl_story.inc` pl_PokeMartSpecial: SpecialMart 11 (Veilstone 2F's vitamins clerk) opens shop 72 with the flag |

## The rules (unova.py --check, all three versions)

- Gen 5 only (494-649), never Victini, the legendaries (638-649), the fossils (564-567), Zorua or Zoroark; a Unova
  starter only in its one 1 % grass slot.
- A new Pokémon takes a slot and keeps its levels. A `~FAMILY` kind takes the last stage Black 2's level evolutions reach
  at the slot's lowest level (Roggenrola's family is Boldore at 36: Black 2's trade stays a trade); a named one is checked
  against the level it evolves at.
- Every Sinnoh Pokémon keeps a slot in every group it had, at every time of day; none gains more than 5 points; one of
  15 % or more keeps 60 % of its rate or loses at most 10 points, a smaller one keeps half or loses at most 4. Where that
  leaves little room the share is lower: the sea's surfing gets Frillish 4-5 % (Tentacool's 60 % and Wingull's 30 % are
  single slots).
- No slot the game changes by itself: the swarm's 0-1 in the swarm routes, the time of day's 2-3, the Great Marsh's and
  the Trophy Garden's 6-7, the post-game list's slots (data/postgame_dex.json). A Sinnoh Pokémon whose only slot a Unova
  kind takes moves into a smaller slot of one that has two ("moves" in --report).
- Version pairs (Pearl White's side, Diamond Black's): Petilil / Cottonee, Solosis / Gothita, Vullaby / Rufflet, Throh /
  Sawk, Basculin Blue- / Red-Striped. Platinum has both (an area too small for both: the side of its file's parity).
  After the Champion Pearl and Diamond get the other side in one more small slot (or the own side's smallest).
- Every family placed can finish evolving: level, friendship, Karrablast + Shelmet in the party (both in Eterna Forest),
  Boldore / Gurdurr at 35 (data/trade_evos.json), the stones at Veilstone 2F.
- Teams: each new Pokémon keeps the old one's level, difficulty and held item, the ace stays; four moves of its own
  (`moveset`: its best attack of its type and a second one, by levelling or TM, no stronger than the level allows, no
  one-hit KO, recharge move or Solar Beam).

## Limits

- Routes 226 and 230 surfing (Pearl, Diamond) and Pastoria and Route 213 surfing (Platinum) stay as they are; Route 229's
  grass in Pearl and Diamond gets 8 % (the post-game's four slots). `data/unova.json` "unchanged" and "low" say why.
- The HABITAT list's pages hold 30 Pokémon: Mt. Coronet's page (and Platinum's Route 205) leave out Unova Pokémon other
  pages list too (the build log names them).
- A Unova Pokémon has no walking sprite: the next party Pokémon follows.
- Saves: switching the option changes the next zone's table; the zone the player stands in keeps the one it loaded.

## Tests

The list from the lead's first message (2026-11-23): the question (A, B, mashing), the tables in every state (off = today's
byte for byte; on, before and after the Champion), each encounter kind, two Leaders and Cynthia on and off, a catch before
the National Pokédex (the registration screen, the Pokédex's counts, Rowan's rating), an old 1.0.2 save with the aide,
the bad-read watcher, new-game smoke tests per answer, a forced loss, save and Continue. Results: notes/NEXT_RELEASE.md.
