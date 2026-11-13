# Griseous Platinum: the National Pokédex in the post-game (plan, 2026-11-09)

Platinum's part of the user's request of 2026-11-09 ("the dex is completable in the post game for all three versions
all the version exclusives become available after you become the champion"). Pearl's and Diamond's findings and the
shared mechanism are notes/POSTGAME_DEX.md (public; it never names Platinum). **Research and plan only**: nothing built
or changed. Keep this file out of public snapshots, as every Platinum note.

## 0. Built (2026-11-09, postdex; the user approved notes/POSTGAME_DEX.md's recommendations, "Platinum gets the parts it lacks")
- The Radar's four: the shared C (decomp `resident/wild.c` PearlB2_Wild_PostGameSlots), Platinum's 24 entries in
  `data/postgame_dex.json` (version.POSTGAME_OTHER None: no exclusive entries), `patches/wild.py` installs them (196 B).
- The four mythicals: decomp extension 0xA9 (`resident/leftovers.c`), `patches/event_gifts.py` + `data/event_gifts.json`
  (the same four cards; Met game Platinum's), `pearl_story.inc` PL_DELIVERY_EVENTS 8 (gifts 8-11 after the Alarm Clock,
  PL_DELIVERY_GIFTS 12). The event Regigigas (0xBF, platinum_regigigas.py) is untouched.
- Platinum's 13 Marts regenerated into work/platinum/src (git-ignored: a Platinum build or `PEARL_VERSION=platinum python3
  b2tools/pearl_story.py zones <the 13 Marts>` makes them). **Add `event_gifts` to Platinum's patch list** (after `wild`;
  the list lives in the Platinum agents' scripts, e.g. work/agents/plat-test/combined.sh).
- Ramanas Park, the Hideaways, the fossils, Spear Pillar: unchanged ('both', its own post-game Dialga and Palkia).
- The swarm places stay Pearl's 28 (the lead's call, 2026-11-09).
- Found in Pearl's test (2026-11-09): the Rainbow Room's doorway (entrance_both (44, 31), its front tile in the chunk
  below) stood on the cliff top: `ramanas.chunk` now takes the front tile's height from the chunk below's BDHC. The
  same doorway is Platinum's: its Pal Park chunk changes too (not seen on screen in Platinum).
- `PEARL_VERSION=platinum python3 b2tools/postgame_dex_check.py`: 482 -> 493 of 493, 475 -> 482 of 482. pearl_story's
  report: 481 zone files, 0 with problems; the regenerated Marts pass the build's per-zone checks.


| | Griseous Platinum |
|---|---|
| Species 1-493 a player can't get today, by any in-game means | **11** |
| ... version exclusives (Diamond's or Pearl's) | **0** |
| ... Poké Radar only | 7 |
| ... GBA slot only | 0 |
| ... morning or night only | 0 (11 species are morning- or night-only in its tables: the clock picks them) |
| ... events only | 4 |
| ... other | 0 |
| The game's own goal (caught, without the 11 mythicals; pokeplatinum sExcludedMonsNational = Pearl's list) | 475 of 482 |

The audit is the one of notes/POSTGAME_DEX.md section 2, run with `PEARL_VERSION=platinum` on Platinum's own data:
`data/platinum/sinnoh_world.json` (66 zones, 432 rooms), `work/platinum/zones.json` and `encounters/` (Pearl's slot
numbers), `work/platinum/scripts`, the Underground's "both" column, all 11 Pal Park rooms, both fossils.

## 2. What Platinum already gives (why no exclusive is missing)
- **Both BDSP columns** in the Hideaways (`ug_data.entry_stage(e, 'both')`: the earlier stage of the two), both
  versions' rares.
- **All 11 Pal Park rooms** (`version.BDSP = 'both'`, `ramanas.py` entrance_both): the Kanto birds, the Johto beasts,
  Lugia, Ho-Oh, Kyogre, Groudon, Rayquaza, Mewtwo, the Latis, the Regis.
- **Both fossils** (Armor and Skull in the grottos) and the five daily ones from Champion.
- **Dialga and Palkia** after the Hall of Fame (scripts 1071 / 1072, Lv 70), Giratina (the Distortion World / Turnback
  Cave), the roaming birds from Oak (`patches/roamers.py`, Lv 60), the three Regis through the deliveryman's event
  Regigigas, Heatran, Regigigas, Rotom (the Old Chateau; its forms with the Secret Key), Shaymin (StartFatefulEncounter), Darkrai, Arceus, the Manaphy
  Egg (Phione with Ditto: the Trophy Garden and the Hideaways).
- Diamond's and Pearl's wild exclusives come from the Hideaways' two columns (Murkrow, Misdreavus at stage 1, Stunky
  at 2, Glameow at 4, Seel, Spheal, Pinsir at 6, ...) and a few from Platinum's own tables (Scyther, Electabuzz,
  Magmar).
- Evolution items: every one has a source (balls, hidden items, Oak's Up-Grade, Iron Island's Metal Coat, Pickup's
  King's Rock and Prism Scale, wild held items: Dragon Scale on Horsea, Seadra and the Dratini line).

## 3. What is missing

| Group | Species | Platinum's own place |
|---|---|---|
| Poké Radar only (7) | Stantler, Smeargle, Swellow, Loudred; Taillow, Whismur (breeding), Exploud (evolving) | Route 207; Route 208 and Route 212 North; Route 213; Mt. Coronet's north and south mountainsides |
| Events only (4) | Mew, Celebi, Jirachi, Deoxys | none (Pal Park's GBA migration can bring them) |

So for Platinum the user's "all the version exclusives" is already true; what keeps its Pokédex from being complete is
the closed Poké Radar (7) and the four events.

## 4. Platinum's part of the plan

### 4.1 The Radar-only four (the shared slot list)
The same C as Pearl's and Diamond's (notes/POSTGAME_DEX.md 4.3: `PearlB2_Wild_PostGameSlots` in the decomp's
`resident/wild.c`, called from `resident/roamers.c` PearlB2_Roamers_GenWilds; flag 2400; a slot that holds its own
species becomes the new one half the time). Platinum's list has **no exclusive entries** (version row
POSTGAME_EXCLUSIVES None) and **24 Radar entries** (slots 4, 5, 10, 11; generated from `work/platinum/encounters`):

| Zone | Own species in slots 4 / 5 / 10 / 11 (day table) | Becomes |
|---|---|---|
| Route 207 | Ponyta, Machop, Ponyta, Geodude | Stantler |
| Route 208 | Roselia, Bibarel, Roselia, Bibarel | Smeargle |
| Route 212 North | Roselia, Staravia, Roselia, Marill | Smeargle |
| Route 213 | Wingull, Shellos, Buizel, Shellos | Swellow |
| Mt. Coronet north / south mountainside | Machoke, Medicham, Absol, Chingling | Loudred |

192 B of the resident pool. Slots 4-5 and 10-11 have no time-of-day change, so the day table's species are the ones
to match.

### 4.2 Events
The deliveryman (`pearl_story.inc` pl_DeliveryGive, Platinum's PL_DELIVERY_GIFTS 8) gives Mew, Celebi, Jirachi and
Deoxys after the Alarm Clock: gifts 8-11. The maker is the event Regigigas's (`patches/platinum_regigigas.py`,
extension 0xBF, Black 2's Mystery Gift maker) made into a table of event Pokémon, so Pearl and Diamond use the same C
with their own rows (Pearl's note 4.9 describes it without Platinum). Each copied from a real Gen 4-era distribution.

### 4.3 Nothing else
No Hideaway, Pal Park, fossil or legendary change: Platinum's rows for those (POSTGAME_EXCLUSIVES, RAMANAS_ROOMS,
POSTGAME_LEGEND) stay as Platinum has them today ('both', 11 rooms, its own post-game Dialga and Palkia).

## 5. Found on the way (no Pokédex effect)
The swarm table (`patches/wild.py` SWARM_MAPS, decomp `resident/wild.c` WILD_SWARMS 28) is Pearl's 28 places in every
version. Platinum's own 22 (pokeplatinum `src/overlay006/swarm.c` sSwarmMapIdTable) are all among them, but Platinum's
build also swarms on 6 places Platinum never does (Route 213, Route 216, Lake Verity (Galactic), Lake Valor, Lake
Acuity (Galactic), Fuego Ironworks: whatever Platinum's files hold there, e.g. Snover / Sneasel, Starly / Bidoof,
Magmar / Magnemite), and its 22 come 22 days in 28. Every Platinum swarm species is catchable either way. Exact
Platinum: a version row for the swarm places (22) and `daily % count` from the table (wild.c reads WILD_SWARMS today).

## 6. Checks
- Offline: `PEARL_VERSION=platinum python3 b2tools/postgame_dex_check.py` (notes/POSTGAME_DEX.md 6.1) gives today's 11,
  then the user's leave-out list after; the resident blob read back (24 entries); `version_check.py`: Platinum's
  other output unchanged; `platinum_dex_check.py` still passes.
- On screen: none if Pearl's Route 206 run passes (the same code; only data differs). If the user wants one: Route 207
  with flag 2400, a logged walk: Stantler (~11 %).

## 7. For the user (Platinum)
1. **Poké Radar-only species.** (a) Recommended: Stantler, Smeargle, Swellow and Loudred at Platinum's own Radar
   places after the Champion, half the time in the Radar's slots; the Radar stays closed. (b) Every Radar species at
   its Radar slots (91 species). (c) None: 7 short.
2. **Mew, Celebi, Jirachi, Deoxys.** (a) Recommended: from the deliveryman after his other gifts, each a real Gen 4-era
   event (which ones: the user's pick, or the project lists candidates). (b) Pal Park's GBA migration only. (c) Leave
   them out (the game's 482 doesn't count them).
3. **The swarm places.** (a) Recommended: Platinum's own 22 (a data row; no Pokédex change). (b) Leave Pearl's 28.
