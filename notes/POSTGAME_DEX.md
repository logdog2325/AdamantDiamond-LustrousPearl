# The National Pokédex in the post-game: every version exclusive after the Champion (2026-11-09)

The user (2026-11-09): "can we make it so the dex is completable in the post game [...] all the version exclusives
become available after you become the champion". This note covers Lustrous Pearl and Adamant Diamond:
what each build couldn't give, and how it is given after the Hall of Fame. Sections 1-7 are the plan as written; the
user approved every recommendation (section 7) the same day. Section 0 is what was built.

## 0. Built (2026-11-09, postdex)
Everything waits on flag 2400. State: written and checked offline; one Pearl test ROM is next (section 6).

| Piece | Where | What |
|---|---|---|
| Route slots, the Radar's four | decomp `src/pearlb2/resident/wild.c` PearlB2_Wild_PostGameSlots (+ `include/pearlb2/wild.h`, one call in `resident/roamers.c` PearlB2_Roamers_GenWilds); `b2tools/postgame_dex.py --write` -> `data/postgame_dex.json`; `patches/wild.py` postgame_blob -> gPearlB2PostGame | 52 + 20 entries a build (576 B + 4); a grass or surf slot holding its own species is the other one half the time |
| Hideaways | `b2tools/ug_data.py` entry_stage / postgame_column | the other column's entries at stage 6: Pearl +81, Diamond +90 |
| Pal Park | `b2tools/ramanas.py` modes 'sp+bd' / 'bd+sp' (version.RAMANAS_ROOMS), the room files regenerated; the gate's clerk (generated into Pearl's shared gate file) has each version's rules for the four shared third-tier rooms under `#if PEARLB2_GAME_VERSION`; `ramanas.chunk`: a doorway whose front tile is in the chunk below (the Rainbow Room's, (44, 31)) takes that tile's height from that chunk's BDHC | all 11 rooms; each room keeps its own version's rule. Seen on screen: the Rainbow Room's doorway stood on the cliff top above the tile the player walks in from (it took the height of its own chunk's row 0), so the player walked into the rock face: fixed by the height rule |
| Fossil | `b2tools/underground_scripts.py` other_fossil_defines | the daily fossil balls one in six the other version's fossil (Skull in Pearl, Armor in Diamond), by PEARLB2_GAME_VERSION in the shared file |
| Spear Pillar | `b2tools/postgame_legend.py` through ramanas.py's hooks; `pearl_events.py` (an added person's own flag, zone inits and step triggers from the hooks); flags PFLAG_PG_LEGEND_HIDDEN 1073, PFLAG_PG_LEGEND_CAUGHT 1074 (`pearl_ids.py`); `patches/pearl_npc_sprites.py` repaints Dialga's sheet in Pearl too | Dialga (Pearl) / Palkia (Diamond) Lv 47 at (31, 21) after the Hall of Fame once the version's own is caught; the battle starts on Pearl's own row for its legendary after the Hall of Fame (x 29-33, z 26: a step trigger on map-local work 0x401D), as Pearl's own starts; its cry line, the same battle; caught: the Adamant / Lustrous Orb; knocked out: it is back on the next visit. A Pearl build draws it with Pearl's own Dialga (the dump's pixels, as Diamond's) |
| Event Pokémon | decomp `resident/leftovers.c` extension 0xA9; `patches/event_gifts.py` + `data/event_gifts.json`; `src/include/pearl_story.inc` (PL_DELIVERY_EVENTS 7, PL_DELIVERY_GIFTS 11), `pearl_story.py` DELIVERY_LINES; the 13 Marts regenerated | gifts 7-10 after the Pokétch apps: Mew (My Pokémon Ranch, OT Hayley 01000, Lv 50), Celebi (GameStop 2011, WIN2011 02211, Lv 50), Jirachi (GameStop 2010, GAMESTP 02270, Lv 5), Deoxys (GameStop 2008, Gamestp 06218, Lv 50), each "received <species>!" |
| Rows | `b2tools/version.py` block "postdex" | POSTGAME_OTHER, POSTGAME_RADAR, RAMANAS_ROOMS, POSTGAME_LEGEND, EVENT_GIFTS (and GAME_VERSION_BY) |
| Check | `b2tools/postgame_dex_check.py` (`--today` for the numbers before) | Pearl 445 -> 493 of 493 (439 -> 482 of 482), Diamond 446 -> 493 (440 -> 482) |

Found on the way: Adamant Diamond 1.0's slate clerk sold Lustrous Pearl's slates. The gate's script is generated into
Pearl's shared file with Pearl's nine rooms (Kanto and Squall Slates, no Johto or Rainbow Slate), and a Diamond build
uses that file, so Diamond 1.0 can't open its Johto and Rainbow Rooms (Raikou, Entei, Suicune, Ho-Oh). 1.0.1 fixed it on
its own (the slate fix: Diamond's whole clerk under `#if PEARLB2_GAME_VERSION == 10`); with all 11 rooms in both
versions this work replaces that with one clerk whose four shared third-tier rooms' rules split by version.

The build list (notes/RESUME.md "Commands") has `event_gifts` after `wild`. The deliveryman's Deoxys OT is Serebii's
spelling ("Gamestp"; its Jirachi of the same shop is "GAMESTP"): the event's own Wonder Card would settle it.

## 1. The answer in short

| | Lustrous Pearl | Adamant Diamond |
|---|---|---|
| Species 1-493 a player can't get today, by any in-game means | **48** | **47** |
| ... the other version's exclusives (our other build has them) | 37 | 36 |
| ... Poké Radar only (in no build at all) | 7 | 7 |
| ... GBA slot only | 0 (12 GBA-slot species, all in Diamond's Hideaway column: counted above) | 0 (13, all in Pearl's column) |
| ... morning or night only | 0 | 0 |
| ... events only | 4 | 4 |
| ... other (an item, a trade, ...) | 0 | 0 |
| The game's own goal: caught, without Pearl's 11 mythicals, of 482 | 439 | 440 |

**Plan**: after the Hall of Fame (flag 2400), the other version's own wild slots work half the time where that version
has them, its Hideaway column joins the Grand Underground, Pal Park gets all 11 rooms, the daily fossil balls can be
the other version's fossil, and the other version's legendary waits at Spear Pillar. The four Radar-only species go into
their Radar places the same way. With those, both builds reach 489 of 493 and the game's 482 of 482; Mew, Celebi,
Jirachi and Deoxys need the user's decision.

## 2. How the counts were made

A read-only audit script (to become `b2tools/postgame_dex_check.py`, section 6) takes every source the build has, each
the way its patch makes it, then adds every evolution and every Day Care egg until nothing changes:

- Wild tables: every installed zone of `data/sinnoh_world.json` (66 overworld zones, 404 rooms) through
  `work/<version>/zones.json` to `work/<version>/encounters/NNN.json`: the 12 grass slots, the day and night pairs in
  slots 2-3, surf and the three rods. Swarm (0-1), Poké Radar (4-5, 10-11) and GBA (8-9) fields are kept apart: they
  aren't in the build's tables.
- `patches/wild.py`'s own readers: the honey trees (`HONEY_MEMBERS`), the 28 swarms (after Barry's sister, post-game),
  the Great Marsh's two daily lists, Feebas. The Trophy Garden's 16 (`pearl_story.inc pl_AddTrophyGardenMon`). The
  roamers (Mesprit, Cresselia).
- The world scripts (`work/pearl/scripts`): every LegendaryBattle, WildBattle, GiveMon and GiveEgg; Spear Pillar's
  legendary by version; the starters (one of three); the deliveryman's Manaphy Egg (and his Member Card, Oak's Letter
  and Azure Flute, whose battles are in the scripts).
- The Grand Underground: `data/underground_pokemon.json` in the version's column (`sp` / `bd`), entries and rares; the
  grottos' starters (`data/underground.json`). The fossils: the version's own in the grottos, the five daily balls from
  Champion (`fossil_items`); the Mining Museum revives all seven (`b2tools/fossil_data.py`).
- Pal Park: `data/ramanas_park.json`'s rooms of the version (Giratina's Distortion Room can't be caught).
- In-game trades: `npc_trade_data.trades()`.
- Evolution: Black 2's table (a/0/1/9, 709 records) with `data/trade_evos.json` (trade methods as items or levels) and
  `zone_effects`' places (Magnezone, Probopass, Leafeon, Glaceon). Every item an evolution needs has a source: balls,
  hidden items, Marts, gifts (`work/pearl/scripts`: Oak's Up-Grade in Eterna, Iron Island's Metal Coat), the grottos
  and Hideaways, Black 2's Pickup (King's Rock, Prism Scale) and wild held items (Black 2's personal data, the Electabuzz
  and Magmar lines' from the dump: Dragon Scale on Horsea, Seadra and the Dratini line, Metal Coat on Magnemite and
  Bronzor, King's Rock on Poliwag and Slowbro, Electirizer and Magmarizer on their lines).
- Breeding: Black 2's Day Care (Solaceon), Ditto (Hideaways, stage 6), the baby by its chain, the nine incense babies
  (every incense is an item ball), Nidoran and Volbeat/Illumise both ways, Phione from the Manaphy Egg.

Not counted: Pal Park's GBA migration (needs a GBA game in slot 2), link trades.

**Time of day**: `sinnoh_encounters.py`'s docstring still says slots 2-3 take the day species. That is from before
2026-10-18's change: `TIME_TABLES` writes morning, day and night tables and `src/code/time_encounters.c` loads the one
of the hour, so the seven species that are morning- or night-only in each version's tables are all catchable. (The
docstring line and the "lost: morning-only / night-only" columns of notes/ENCOUNTERS.md should be updated with this work.)

## 3. What each build can't give today

### 3.1 Lustrous Pearl: 48

| Group | Species | Where Adamant Diamond has them |
|---|---|---|
| Diamond's wild tables (8) | Seel, Dewgong; Scyther, Scizor; Murkrow, Honchkrow; Stunky, Skuntank | Routes 226 and 230 surf; Route 229; Eterna Forest and the Lost Tower at night; Routes 206, 214, 221, 225 (Scizor, Honchkrow by evolution). Each is also in Diamond's Hideaway column |
| Diamond's legendary (1) | Dialga | Spear Pillar, Lv 47 |
| Diamond's fossil (2) | Cranidos, Rampardos | the Skull Fossil in the grottos |
| Diamond's Pal Park rooms (4) | Raikou, Entei, Suicune; Ho-Oh | the Johto Room, the Rainbow Room |
| Diamond's Hideaway column (22) | Caterpie, Metapod, Butterfree, Ekans, Arbok, Growlithe, Arcanine, Elekid, Electabuzz, Electivire, Gligar, Gliscor, Larvitar, Pupitar, Tyranitar, Seedot, Nuzleaf, Shiftry, Mawile, Zangoose, Solrock, Kecleon | Hideaways, almost all at stage 6 (Champion). 12 of them are GBA-slot species in Pearl's own tables (Caterpie, Metapod, Ekans, Arbok, Growlithe, Gligar, Elekid, Seedot, Nuzleaf, Mawile, Zangoose, Solrock), Larvitar and Kecleon Diamond's Poké Radar species |
| Poké Radar only (7) | Stantler (Route 207), Smeargle (Route 212 North), Swellow (Route 213), Loudred (Mt. Coronet, both mountainsides); Taillow, Whismur, Exploud by breeding and evolving | in no build |
| Events only (4) | Mew, Celebi, Jirachi, Deoxys | in no build (Pal Park's GBA migration can bring them) |

### 3.2 Adamant Diamond: 47

| Group | Species | Where Lustrous Pearl has them |
|---|---|---|
| Pearl's wild tables (5) | Pinsir; Misdreavus, Mismagius; Glameow, Purugly | Route 229; Eterna Forest and the Lost Tower at night; Routes 218, 222, 229. Each is also in Pearl's Hideaway column |
| Pearl's legendary (1) | Palkia | Spear Pillar, Lv 47 |
| Pearl's fossil (2) | Shieldon, Bastiodon | the Armor Fossil in the grottos |
| Pearl's Pal Park rooms (4) | Articuno, Zapdos, Moltres; Lugia | the Kanto Room, the Squall Room |
| Pearl's Hideaway column (24) | Weedle, Kakuna, Beedrill, Sandshrew, Sandslash, Vulpix, Ninetales, Slowpoke, Slowbro, Slowking, Magby, Magmar, Magmortar, Teddiursa, Ursaring, Lotad, Lombre, Ludicolo, Sableye, Seviper, Lunatone, Bagon, Shelgon, Salamence | Hideaways, mostly stage 6. 13 are GBA-slot species in Diamond's own tables (Weedle, Kakuna, Sandshrew, Sandslash, Vulpix, Teddiursa, Ursaring, Magby, Lotad, Lombre, Sableye, Seviper, Lunatone), Slowpoke and Bagon Pearl's Poké Radar species |
| Poké Radar only (7) | the same seven (Stantler is Pearl's Radar species: Diamond's Route 207 Radar has Larvitar) | in no build |
| Events only (4) | Mew, Celebi, Jirachi, Deoxys | in no build |

Not gaps, though notes/DIAMOND.md 1.3 lists them as exclusive: Bonsly, Mime Jr., Sudowoodo, Mr. Mime (the Trophy Garden
has Bonsly and Mime Jr. in both), Spheal, Sealeo (Pearl's Hideaways; Diamond breeds them from its Hideaways' Walrein),
Silcoon, Cascoon, Beautifly, Dustox (Wurmple evolves either way), Aron, Houndoom, Mightyena (Hideaways).

### 3.3 What is already after the Champion
Flag 2400 already opens: the Hideaways' stage 6, Pal Park's rooms, the daily Kanto and Hoenn fossil balls, the swarms
(Barry's sister), the Great Marsh's National list, the Trophy Garden (with Oak's National Pokédex), the deliveryman's
gifts (Darkrai, Shaymin, Arceus, the Manaphy Egg). So most of the plan below is data in places that are already
post-game.

## 4. The mechanism

### 4.1 The flag
**Flag 2400** = Pearl's FLAG_GAME_COMPLETED 0x964 (`src/include/pearl.h` PFLAG_0964, `b2tools/pearl_ids.py`
SYSTEM_SAME), Black 2's game clear. The Hall of Fame room sets it in `pl_ClearGame` (`src/include/pearl_story.inc`)
before CallGameClear, so the next field load sees it. Already read by the deliveryman (`pl_DeliveryWaiting`: FlagGet
2400), `wild.c`'s Great Marsh (`gameClearFlag`, `patches/wild.py` GAME_CLEAR_FLAG), the Hideaways' stage 6
(`data/underground.json` unlock), Pal Park's gate (`data/ramanas_park.json` open_flag) and Oak's National Pokédex
(`pl_CheckLocalDexCompletedOrChampion`). Verified in the source; every new piece below uses the same flag.

### 4.2 What already switches at run time
| Where | What |
|---|---|
| `src/code/time_encounters.c` (ITCM, replaces ov012 EventData_LoadEncData) | the zone's table 0, 1 or 2 by the hour, when the zone loads |
| `src/code/rods.c` | loads the zone's table 3 for the Old and Good Rod |
| decomp `src/ov036/field_encount.c` EventWildBattleCall_CreateRandom -> `resident/roamers.c` PearlB2_Roamers_GenWilds | each random grass or surf battle works on a **copy** of the zone's EncData: the Trophy Garden's slots 6-7, then `resident/wild.c` PearlB2_Wild_ReplaceSlots (the swarm's slots 0-1, the Great Marsh's 6-7, by flag 2400), then `underground_itcm.c` PearlB2_GenWilds (a Hideaway's list by stage) |
| scripts | honey trees, Pal Park's rooms, the deliveryman, the fossil balls |

Black 2 itself picks the table statically from the zone header (ov012 `field_encount_st.c` EncData_Load).

### 4.3 Routes: the other version's slots (recommended way)
Options weighed:
- **A second, post-game table per file** (a new a/1/2/7 file, EncData_Load redirected; a sibling project's research
  recommends this for its own build): new files change a/1/2/7's layout, which this project keeps fixed (savestates,
  RAM file table: `sinnoh_encounters.py` docstring). Reusing Black 2's own 135 tables only works for the ones of the
  same size and no Unova zone; fiddly. It would also cover rods, which don't differ (notes/DIAMOND.md 1.2: no rod
  table differs).
- **More tables per file**: every file changes size and EncData_Load's "1 or 4 tables" rule. No.
- **Slots replaced on the copy, in the hook that exists** (recommended): no archive changes, no ITCM, and the zone's
  tables (and the Pokédex's AREA data made from them) stay as they are.

The list, made by a generator from `work/pearl/encounters` and `work/diamond/encounters` (every installed zone, the
morning, day and night tables and surf; the rows of notes/DIAMOND.md 1.2 that aren't Radar or GBA): an entry is
**(zone, group, slot, own species, other species)**. Generated today: **52 entries per build**, the same rows each way:

| Zone | Group, slots (odds) | Pearl's -> Diamond's (a Diamond build: the other way) |
|---|---|---|
| Eterna Forest (inside) | grass 1 (20 %); 2-3 at night (10 / 10 %); 10-11 (1 / 1 %) | Cascoon -> Silcoon; Misdreavus -> Murkrow; Dustox -> Beautifly |
| Route 206 | grass 1, 9, 11 (20 / 4 / 1 %) | Geodude -> Stunky |
| Route 209, Route 210 South | grass 2-3 in the morning, 9, 11 | Bonsly -> Mime Jr. |
| Lost Tower 1F-5F | grass 2-3 at night | Misdreavus -> Murkrow |
| Route 214 | grass 4, 8, 10 (10 / 4 / 1 %) | Sudowoodo -> Stunky |
| Route 218 | grass 4, 8, 10 | Glameow -> Mr. Mime |
| Route 221 | grass 1; 4, 8, 10 | Gastrodon -> Stunky; Sudowoodo -> Skuntank |
| Route 222 | grass 1; 4, 8, 10 | Glameow -> Gastrodon; Purugly -> Mr. Mime |
| Route 225 | grass 5 | Roselia -> Skuntank |
| Route 226 | surf 1 (30 %); 3-4 (4 / 1 %) | Spheal -> Seel; Sealeo -> Dewgong |
| Route 229 | grass 4, 5, 6, 7 | Volbeat -> Illumise, Purugly -> Roselia, Pinsir -> Scyther, Illumise -> Volbeat |
| Route 230 | grass 3; surf 1; 3-4 | Dustox -> Beautifly; Spheal -> Seel; Sealeo -> Dewgong |

The C (decomp, resident section; ~120 B of code):
- `include/pearlb2/wild.h` + `src/pearlb2/resident/wild.c`: `PearlB2PostGame *gPearlB2PostGame` (NULL: nothing),
  `{u16 flag; u16 count; {u16 zone; u8 group; u8 slot; u16 own; u16 other;}[count]}` (species | form << 11, as the
  tables), and `PearlB2_Wild_PostGameSlots(EncData *copy, EncountManager *manager, u16 zoneId)`: with the flag set,
  for ENCTYPE_GRASS (copy->grass) or ENCTYPE_SURF (copy->surf), each entry of the zone whose slot **holds its own
  species** becomes the other species half the time (GFL_RandomLCAlt(2)). Matching the species is what makes it
  right for every time table (Murkrow only where the night table has Misdreavus) and after a swarm took slots 0-1.
- `resident/roamers.c` PearlB2_Roamers_GenWilds: one call after PearlB2_Wild_ReplaceSlots.
- `b2tools/patches/wild.py`: the blob (8 B an entry: 72 entries with 4.4 = 576 B of the 18 KB resident pool) and its
  pointer in apply_code, from `data/postgame_dex.json`, which a generator (`b2tools/postgame_dex.py --write`) makes
  from the two versions' encounter files, so a Pearl build doesn't need Diamond's dump. Levels stay the slot's (the
  two games' levels are equal in every row).

### 4.4 Poké Radar-only species
The same list, with entries made from the files' Radar fields for the four species no build has: **20 entries in
each build**, the slots the Radar uses (4, 5, 10, 11: 10 / 10 / 1 / 1 %), half the time after the Champion:
Route 207 (Geodude, Geodude, Machop, Geodude -> Stantler), Route 212 North (Roselia, Budew, Kricketune, Kricketune ->
Smeargle), Route 213 (Shellos, Wingull, Floatzel, Shellos -> Swellow), Mt. Coronet's north and south mountainsides
(Medicham, Machoke, Bronzong, Clefairy -> Loudred). About 11 % of that grass's battles. Taillow, Whismur and Exploud
follow by breeding and evolving. A Diamond build takes Stantler from Pearl's Route 207 (its own Route 207 Radar has
Larvitar).

### 4.5 The Grand Underground: the other column
`b2tools/ug_data.py` `entry_stage(e, column)`: the version's column as now, and an entry only in the other column at
**stage 6** (the Champion's: the existing gate). Rares stay the version's (every species of the other column has a
plain entry too). Data only, the C is unchanged; the visible Pokémon (`resident/hideaway.c`) read the same lists.
Pearl +81 entries (20 species), Diamond +90 (21), 4 B each, before the identical lists are shared. This alone covers
every Hideaway species of 3.1 and 3.2 and also the routes' exclusives (Murkrow, Stunky, Seel, Glameow, ...).

### 4.6 Pal Park: all 11 rooms
`data/ramanas_park.json` already has the "both" column: the Johto and Rainbow Rooms on their own doorways (30, 24) and
(44, 31) (`entrance_both`), their zones 661-662 (blank headers in every build: `allocate_sinnoh.APPEND_BLOCKS`), slates
131-132 and flags 1069-1072 reserved. A version row picks the rooms instead of version.BDSP (`b2tools/ramanas.py`
version(), the 9-or-11 assert in `patches/ramanas_park.py`); the room files are written again (1901 / 1301, Pearl's and
Diamond's folders). The park already opens at Champion. One choice: the third tier's rule (For the user, 6).

### 4.7 The other fossil
`data/underground.json` `fossil_items` (the two daily balls from Champion, `b2tools/underground_scripts.py`) gains
the other version's fossil (`grotto_items.version_fossil` of the other column): Skull in Pearl, Armor in Diamond. The
grottos keep the version's own. The Museum already revives all seven.

### 4.8 The other legendary
Spear Pillar (`src/field_scripts/1502_pearl_mount_coronet_spear_pillar.s`, which picks 483 / 484 by
PEARLB2_GAME_VERSION; its own legendary's battle is there twice, the scene and entry 14, both Lv 47): an extra
entry through a pearl_story hook (as Pal Park's are added), a person with the other legendary's Black 2 field sprite at
the version's own spot, shown with flag 2400 once the version's own is caught: its cry, Black 2's legendary battle,
then the other Orb (the Adamant Orb in Pearl, the Lustrous Orb in Diamond). One new caught flag (`pearl_ids`
NEW_FLAGS), a few lines of text. Version row: the species and Orb (Pearl 483 + Adamant Orb, Diamond 484 + Lustrous Orb).

### 4.9 Event Pokémon (if chosen)
The deliveryman (`pearl_story.inc` pl_DeliveryGive, PL_DELIVERY_GIFTS 7) gives Mew, Celebi, Jirachi and Deoxys after
his Pokétch apps, one a talk, each needing party room as the Manaphy Egg does: gifts 7-10. The Pokémon are made by
Black 2's own Mystery Gift maker through one new extension sub-command and a table of four records (species, level,
OT, ID, ball, item, moves, ribbon, met), copied from real Gen 4-era distributions. Deoxys's forms already change at
Veilstone's meteorites.

### 4.10 Version rows (`b2tools/version.py`; Diamond shares every line of C, the splits are data)
| Row | Pearl | Diamond |
|---|---|---|
| POSTGAME_EXCLUSIVES (whose wild slots, Hideaway column and fossil join at 2400) | 'diamond' | 'pearl' |
| POSTGAME_RADAR (species given at their Radar slots) | Stantler, Smeargle, Swellow, Loudred | the same |
| RAMANAS_ROOMS | all 11 | all 11 |
| POSTGAME_LEGEND (species, Orb) | 483, Adamant Orb | 484, Lustrous Orb |
| EVENT_GIFTS | the user's choice | the same |

An empty row gives today's output, so each piece can be checked alone (`b2tools/version_check.py`).

### 4.11 Not in scope
The Pokédex's AREA page keeps showing the wild tables only, as it does for the swarms and the Trophy Garden today (the
existing habitat hook, `resident/roamers.c` PearlB2_Roamers_ReadHabitat, could add places after 2400 later). Honey
trees stay the version's own (Silcoon and Cascoon come from Wurmple either way). The Radar stays closed.

## 5. Size
| Piece | Code | Data |
|---|---|---|
| Route and Radar slots | ~120 B C, resident section (wild.c, 1 call in roamers.c) | 576 B, resident pool |
| Hideaways | none | ~330-360 B more in the Underground table (resident pool) |
| Pal Park | none (generated files) | 2 zones, 2 slates, 4 flags, all reserved |
| Fossil | none | 1 item in the fossil balls' script |
| Spear Pillar | a script entry | 1 flag, a few text lines |
| Events (if chosen) | one sub-command | 4 records, ~4 talks of the deliveryman |

a/1/2/7, the zone tables' sizes and ITCM don't change.

## 6. How to check it
Offline (all three before any build):
1. `b2tools/postgame_dex_check.py` (new, the audit of section 2): first it must give today's numbers (Pearl 48,
   Diamond 47, the lists of 3.1 and 3.2); after the change, every version's missing list = the species the user leaves
   out (none, or the four events). Exit 1 otherwise.
2. On a built tree: the resident blob read back equals `data/postgame_dex.json`, and every entry's own species is in
   that slot of that zone's built table for at least one time table (an `encounters_check.py` addition); a/1/2/7
   byte-equal to the build before (0 differences).
3. `underground_check.py`: the version's own entries unchanged, the other column's at stage 6. `ramanas.py check` for
   both versions with 11 rooms; warp_check / scene_check for the two new doorways (notes/RAMANAS_PARK.md section 6,
   item 2, is still open for the nine). `b2_script_check` on Spear Pillar's and the deliveryman's files.
4. The decomp's "build ok" and `decomp.py check` (the layout); `version_check.py` with each row empty = today.
On screen (one Pearl ROM, each start just before the new part):
1. Route 206 grass with `TEST_SET=2400` and a strong lead: a headless walk logging each battle's species (the
   `hwtest/fish_shot.py` / `wild_shot.py` way): Stunky and Geodude both come (Stunky ~12 %); one start without 2400:
   no Stunky. Then Route 226 by Surf: Seel (~15 %). That proves the hook, the flag and both groups.
2. Pal Park: the walk past the two new doorways (every frame), into the Johto Room, the pedestal, Raikou's battle.
3. Spear Pillar after the Hall of Fame: Dialga's sprite at the spot, the cry, the battle, the Adamant Orb.
Diamond: offline only (the same code, its data checked), unless the user wants one Route 229 check.

## 7. For the user
1. **Where the exclusives appear.** (a) Recommended: where the other version has them: its route slots (half the
   time), its Hideaway column at stage 6, all 11 Pal Park rooms, its fossil in the daily fossil balls, and its
   legendary at Spear Pillar with its Orb. (b) The Hideaways, Pal Park, the fossil and the legendary only: no C, no
   route changes (every exclusive is still catchable). (c) Somewhere else (say where).
2. **In a shared slot, how often the other version's species comes.** (a) Recommended: half the time (both versions'
   Pokémon there after the Champion). (b) Always the other version's (the slot's own is then a pre-Champion species).
3. **The other legendary's level.** (a) Recommended: Lv 47, as the version's own at Spear Pillar. (b) Lv 70, as the
   other post-game legendaries.
4. **Poké Radar-only species** (Stantler, Smeargle, Swellow, Loudred; Taillow, Whismur, Exploud follow). (a)
   Recommended: these four at their own Radar places after the Champion, the Radar stays closed. (b) Every Radar
   species at its Radar slots (76 species: many routes change). (c) None: the Pokédex stays 7 short.
5. **GBA-slot species.** (a) Recommended: nothing more: all 12 (Pearl) and 13 (Diamond) come with the other Hideaway
   column. (b) Also Gen 4's real dual-slot: with a GBA game in slot 2 (DS and DS Lite only; Pal Park's cart reader is
   built), its species in slots 8-9 after the Champion.
6. **Pal Park's later rooms with 11 rooms.** (a) Recommended: each room keeps its own version's rule: in Pearl the
   Johto Room opens with the Kanto Room (the three Regis), the Rainbow Room after the Johto and Soul Rooms, and Pearl's
   own third tier stays after the Kanto and Soul Rooms (Diamond the same the other way), so a 1.0 save's open rooms stay
   open. (b) The data's "both" rule: the third tier only after the birds, the beasts and both Latis.
7. **Mew, Celebi, Jirachi, Deoxys** (the game's own goal of 482 doesn't count them). (a) Recommended: from the
   deliveryman after his other gifts, each copied from a real Gen 4-era event (which ones: the user's pick, or the
   project lists candidates). (b) Pal Park's GBA migration only. (c) Leave them out.
