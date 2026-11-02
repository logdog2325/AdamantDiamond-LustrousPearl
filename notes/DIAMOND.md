# Pokémon Diamond vs Pokémon Pearl (USA, Rev 5): every difference

**Sections 0-6 are the analysis as written before the work; section 7 says what each difference became.**

Written 2026-11-01. Read-only analysis of the user's two dumps (`~/Desktop/Pokemon - Pearl Version (USA) (Rev 5).nds`, game code APAE; `~/Desktop/Pokemon - Diamond Version (USA) (Rev 5)/...nds`, game code ADAE), the decomp in `external/pokediamond`, and our tree. No ROM was built and no emulator was run. All helper scripts and their outputs are in `work/diamond/` (list in section 6).

**How sure each line is.** Every table says where its facts come from:

| Tag | Meaning |
|---|---|
| **dump** | Read from the bytes of the two ROMs by a script in `work/diamond/`. A reader can repeat it. |
| **decomp** | Read in `external/pokediamond`. Its two build targets have the same SHA-1 as these two dumps, so its `.ifdef` sites should be the complete list of compile-time differences; I also checked that on the dumps (section 2.1). |
| **inferred** | Follows from the code or data but I did not see it run. |
| **UNVERIFIED** | Could not be settled; the reason is given. |

## 0. The answer in one page

**The two games are one program with a few switches.** Of the ROM's 67,108,864 bytes, every differing byte lies in only these places (proved by `rom_blocks.py`): the header (7 bytes), the file-name and file tables (4,860), the main code `arm9` (8,329), the overlay table (2), 18 code overlays (88,692 bytes in overlay 6, which merely shifts after two small edits, plus 190 in the other 17), the banner and icon (101), and one data file, `poketool/personal*/personal.narc` (24). The other 338 of 360 files are byte-identical, and they already hold both versions' data: both encounter tables, both Pokédex area tables, both title logos, both Pokédex text banks. The code only chooses.

**Counts**

| What | Count |
|---|---|
| Zones whose wild Pokémon differ | **24** encounter files, one zone each (20 zone groups: the five Lost Tower floors count as one), **127** differing slots (61 merged rows in 1.2) |
| Species that are wild-available in only one game (any table, including Poké Radar) | **13** Diamond-only, **14** Pearl-only (1.3) |
| Pokédex area lists that differ | 83 lists for 31 species (37 rows in 1.5); consistent with the encounter tables |
| Code switch sites | **39 compile-time** (32 `.ifdef`/`#ifdef` blocks + 5 `mov #GAME_VERSION` + `main.c` + `scrcmd.c`), found in **27 distinct places** of the ROM, plus **14 run-time** reads of `gGameVersion` (2.2) |
| Script version checks | **6** `GetGameVersion` commands in **4** script files (all 1,051 scripts decoded), steering **22** message lines and the legendary, Orb, ground and book (section 3) |
| Whole text banks that differ | 1 pair: Pokédex entries, bank 615 (Diamond) vs 616 (Pearl): 156 of 494 entries differ |
| Data files that differ | 1: `personal.narc` (6 species, held items only) |

**The five differences a player notices most (in the order a player meets them)**

| # | What | Diamond | Pearl |
|---|---|---|---|
| 1 | The legendary: title screen, Spear Pillar scene and cry, the Eterna statue, the book in Celestic | Dialga (time) | Palkia (space) |
| 2 | Wild Pokémon, from Route 206 on | Stunky / Skuntank, Mr. Mime, Mime Jr., Seel / Dewgong, Scyther, Murkrow, Silcoon | Geodude, Glameow / Purugly, Sudowoodo, Bonsly, Spheal / Sealeo, Pinsir, Misdreavus, Cascoon (full list 1.2) |
| 3 | 156 Pokédex entries are worded differently (all 75 new Sinnoh species among them) | bank 615 | bank 616 |
| 4 | The orb at the top of the Spear Pillar | Adamant Orb | Lustrous Orb |
| 5 | Electabuzz line / Magmar line held items | Electabuzz holds Electirizer 50 %, Magmar holds Magmarizer 5 % | Electabuzz Electirizer 5 %, Magmar Magmarizer 50 % |

**Everything a player meets, in play order** (each row points to the section with the detail)

| Meeting | Diamond | Pearl | Detail |
|---|---|---|---|
| DS menu icon and banner | blue Poké Ball, "Pokémon Diamond" | pink Poké Ball, "Pokémon Pearl" | 4.6 |
| Title screen | "Pokémon Diamond Version" logo, Dialga model, blue-white background, Dialga cry | "Pokémon Pearl Version" logo, Palkia model, pink-white background, Palkia cry | 2.2 rows A1-A4, 4.4 |
| New game: Rowan's intro | blue-grey backgrounds; rival names offered: Barry, Damion, Tyson, Markus | pink backgrounds; Clint, Ralph, Lewis, Tommy | 2.2 B1-B3 |
| Name entry, "default name" | list starts with "Diamond" (boy: 18 names, girl: 18 names); rival's default "Pearl" | starts with "Pearl"; rival's default "Diamond" | 2.2 C1-C3 |
| Options screen heading | POKéMON DIAMOND | POKéMON PEARL | 2.2 D1 |
| First routes (201-205) | same except the Poké Radar patches: Route 201 Nidoran♀ (10 %) / Nidoran♂ (1 %), Route 205 north Hoppip / Skiploom | Nidoran♂ / Nidoran♀; Route 205 Slowpoke | 1.2 |
| Route 206 onwards | Stunky | Geodude | 1.2 |
| Eterna Forest, Floaroma honey trees | Silcoon, Beautifly, Murkrow at night | Cascoon, Dustox, Misdreavus at night | 1.2, 1.4 |
| Pokédex entries (every one you open) | 156 of 494 worded differently | | 3.6.1 |
| Eterna statue | "DIA..." inscription, Dialga's text | "PAL..." inscription | 3.4 |
| Underground (digging) | Skull Fossil, more Fire / Thunder / Sun Stones, Prism Sphere favoured | Armor Fossil, more Water / Leaf / Moon Stones, Pale Sphere favoured | 2.2 G1 |
| Routes 209 and 210 (Lost Tower: night) | Mime Jr. in the morning grass; Murkrow at night in the Lost Tower; Radar: Tauros / Miltank swapped | Bonsly; Misdreavus; Radar: Miltank / Tauros swapped | 1.2 |
| Routes 214, 218, 221, 222 | Stunky, Mr. Mime, Skuntank; Mightyena (Radar) | Sudowoodo, Glameow, Purugly; Houndoom (Radar) | 1.2 |
| Routes 225, 226, 229, 230 | Skuntank (225); Seel / Dewgong (surf, 226 and 230); Scyther, Roselia (229); Beautifly (230) | Roselia (225); Spheal / Sealeo (surf); Pinsir, Purugly (229); Dustox (230) | 1.2 |
| Celestic Town, the elder's old book; Sandgem partner's hint | Palkia page (the other legend); hint "DIALGA may have reappeared" | Dialga page; "PALKIA" | 3.4 |
| Spear Pillar | Dialga Lv 47, Adamant Orb, Diamond ground chunks, Diamond camera | Palkia Lv 47, Lustrous Orb, Pearl ground chunks, Pearl camera | 3.2, 3.3 |
| Holding an Electabuzz / Magmar | as above | as above | 4.1 |
| Pal Park | "...migrated to the Pokémon Diamond Game Card" | "...Pearl Game Card" | 2.2 H1-H5 |
| Credits | first heading "Pokémon Diamond" | "Pokémon Pearl" | 2.2 D2 |
| Any Pokémon you catch or receive | Met game = Diamond (10) | Pearl (11) | 2.2 I1 |

---


## 1. Wild Pokémon

### 1.1 How the two games pick their tables (dump + decomp)

| Fact | Evidence |
|---|---|
| Both ROMs carry both tables, `fielddata/encountdata/d_enc_data.narc` (NARC 37) and `p_enc_data.narc` (NARC 143). Each has 183 files of 424 bytes, and each NARC is byte-identical in the two ROMs. | `enc_diff.py` |
| The code picks one: arm9 `sub_02034CB4` loads the wild table of the zone with `mov r1,#0x25` (Diamond, d_enc_data) or `mov r1,#0x8F` (Pearl, p_enc_data), at 0x02034CD8. | dump (the first differing word of arm9 after the secure area), decomp `unk_02034A28.s:416` |
| The zone header table (559 headers) is identical in both ROMs, so zone → encounter file is the same. 154 zones use 154 different files, one zone each; the other 29 files belong to no zone. `map_header.c` writes the file as `ENCDATA(dia, pea)`, but both arguments are the same number in every header, so the macro changes nothing. | `hdr_diff.py`, decomp `map_header.c:20` |
| 24 of the 183 files differ between d_enc_data and p_enc_data, and all 24 belong to a zone. | `enc_diff.py`, `enc_diff2.py` |
| A file holds: grass rate; 12 grass slots (level, species) with chances 20/20/10/10/10/10/5/5/4/4/1/1 %; 2 swarm species; 2 day and 2 night species; 4 Poké Radar species; form rates; 5 × 2 GBA dual-slot species (Ruby, Sapphire, Emerald, FireRed, LeafGreen); surf (rate, 5 slots 60/30/5/4/1 %); Old, Good and Super Rod (rate, 5 slots each). Decoded with `gen4_extract.read_encounters`, which consumes all 424 bytes of every file. | dump |
| **Which slot is replaced by what:** swarm (the day's swarm zone only) replaces slots 0-1; time of day replaces slots 2-3 (the base table is the morning table, 04:00-09:59; the day array applies 10:00-19:59, the night array 20:00-03:59); the Poké Radar replaces 4, 5, 10, 11 and only inside a Radar patch; a GBA cartridge in slot 2 replaces 8-9 (after the National Pokédex, per Platinum). | hours: decomp `gf_rtc.c`; slot positions: pokeplatinum `wild_encounters.c`, the same file layout in Diamond/Pearl; **inferred** for DP, and `notes/ENCOUNTERS.md` (written from the DP assembly) agrees |

### 1.2 Every difference, zone by zone

Read: "Diamond" and "Pearl" are the species that sit in that slot of the zone's table in that game. Levels are the same in both games in every row (a row shows the level of the slot, so only the species change). "Poké Radar patches only" means the species can only be met inside a Radar patch; "GBA dual-slot" means it replaces the slot only while a GBA cartridge of that game is in slot 2.

| # | Zone | Table | Slot kind | Where in the table | Diamond | Pearl |
|---|---|---|---|---|---|---|
| 1 | Eterna Forest (inside) | file 8 | Grass | slot 1 (20%) | Silcoon Lv10 | Cascoon Lv10 |
| 2 | Eterna Forest (inside) | file 8 | Grass | slots 10, 11 (1/1%) | Beautifly Lv12 | Dustox Lv12 |
| 3 | Eterna Forest (inside) | file 8 | Night table | slot 2 (10%), slot 3 (10%) | Murkrow | Misdreavus |
| 4 | Fuego Ironworks (outside) | file 9 | Poke Radar patches only | slots 4, 5 (10% each) | Aron | Hoppip |
| 5 | Fuego Ironworks (outside) | file 9 | Poke Radar patches only | slots 10, 11 (1% each) | Aron | Skiploom |
| 6 | Valor Lakefront | file 138 | Poke Radar patches only | slots 4, 5 (10% each) | Nidorina | Nidorino |
| 7 | Valor Lakefront | file 138 | Poke Radar patches only | slots 10, 11 (1% each) | Nidorino | Nidorina |
| 8 | Route 201 | file 140 | Poke Radar patches only | slots 4, 5 (10% each) | Nidoran♀ | Nidoran♂ |
| 9 | Route 201 | file 140 | Poke Radar patches only | slots 10, 11 (1% each) | Nidoran♂ | Nidoran♀ |
| 10 | Route 205 (north part) | file 146 | Poke Radar patches only | slots 4, 5 (10% each) | Hoppip | Slowpoke |
| 11 | Route 205 (north part) | file 146 | Poke Radar patches only | slots 10, 11 (1% each) | Skiploom | Slowpoke |
| 12 | Route 206 | file 147 | Grass | slot 1 (20%) | Stunky Lv14 | Geodude Lv14 |
| 13 | Route 206 | file 147 | Grass | slot 9 (4%) | Stunky Lv15 | Geodude Lv15 |
| 14 | Route 206 | file 147 | Grass | slot 11 (1%) | Stunky Lv16 | Geodude Lv16 |
| 15 | Route 206 | file 147 | GBA dual-slot | slot 9 (4%); carts: Ruby, Sapphire, FireRed, LeafGreen | Stunky | Geodude |
| 16 | Route 207 | file 148 | Poke Radar patches only | slots 4, 5 (10% each) | Larvitar | Stantler |
| 17 | Route 207 | file 148 | Poke Radar patches only | slots 10, 11 (1% each) | Larvitar | Stantler |
| 18 | Route 209 | file 150 | Grass | slots 2, 3, 9, 11 (10/10/4/1%) [slots 2, 3 are the morning table; by day they are Staravia + Bibarel, at night Gastly + Zubat, equal in both games] | Mime Jr. Lv16 | Bonsly Lv16 |
| 19 | Route 209 | file 150 | Poke Radar patches only | slots 4, 5 (10% each) | Tauros | Miltank |
| 20 | Route 209 | file 150 | Poke Radar patches only | slots 10, 11 (1% each) | Miltank | Tauros |
| 21 | Route 209 | file 150 | GBA dual-slot | slot 9 (4%); carts: Ruby, Sapphire, Emerald, FireRed | Mime Jr. | Bonsly |
| 22 | Lost Tower 1F, 2F, 3F, 4F, 5F (Route 209) | files 151-155 | Night table | night slots 2, 3 (10% each), identical on all five floors | Murkrow | Misdreavus |
| 23 | Route 210 (north part) | file 157 | Poke Radar patches only | slots 4, 5 (10% each) | Kecleon | Bagon |
| 24 | Route 210 (north part) | file 157 | Poke Radar patches only | slots 10, 11 (1% each) | Kecleon | Bagon |
| 25 | Route 210 (south part) | file 156 | Grass | slots 2, 3 (10/10%) [slots 2, 3 are the morning table; by day they are Ponyta + Ponyta, at night Kricketune + Kricketune, equal in both games] | Mime Jr. Lv18 | Bonsly Lv18 |
| 26 | Route 210 (south part) | file 156 | Grass | slots 9, 11 (4/1%) | Mime Jr. Lv20 | Bonsly Lv20 |
| 27 | Route 210 (south part) | file 156 | Poke Radar patches only | slots 4, 5 (10% each) | Tauros | Miltank |
| 28 | Route 210 (south part) | file 156 | Poke Radar patches only | slots 10, 11 (1% each) | Miltank | Tauros |
| 29 | Route 210 (south part) | file 156 | GBA dual-slot | slot 9 (4%); carts: Sapphire, FireRed, LeafGreen | Mime Jr. | Bonsly |
| 30 | Route 214 | file 163 | Grass | slot 4 (10%) | Stunky Lv23 | Sudowoodo Lv23 |
| 31 | Route 214 | file 163 | Grass | slots 8, 10 (4/1%) | Stunky Lv24 | Sudowoodo Lv24 |
| 32 | Route 214 | file 163 | Poke Radar patches only | slots 4, 5 (10% each) | Mightyena | Houndoom |
| 33 | Route 214 | file 163 | Poke Radar patches only | slots 10, 11 (1% each) | Mightyena | Houndoom |
| 34 | Route 214 | file 163 | GBA dual-slot | slot 8 (4%); carts: Ruby, Sapphire, FireRed | Stunky | Sudowoodo |
| 35 | Route 215 | file 164 | Poke Radar patches only | slots 4, 5 (10% each) | Mightyena | Houndoom |
| 36 | Route 215 | file 164 | Poke Radar patches only | slots 10, 11 (1% each) | Mightyena | Houndoom |
| 37 | Route 218 | file 167 | Grass | slot 4 (10%) | Mr. Mime Lv29 | Glameow Lv29 |
| 38 | Route 218 | file 167 | Grass | slots 8, 10 (4/1%) | Mr. Mime Lv30 | Glameow Lv30 |
| 39 | Route 218 | file 167 | GBA dual-slot | slot 8 (4%); carts: Ruby, Sapphire, Emerald, FireRed, LeafGreen | Mr. Mime | Glameow |
| 40 | Route 221 | file 169 | Grass | slot 1 (20%) | Stunky Lv28 | Gastrodon Lv28 |
| 41 | Route 221 | file 169 | Grass | slot 4 (10%) | Skuntank Lv29 | Sudowoodo Lv29 |
| 42 | Route 221 | file 169 | Grass | slots 8, 10 (4/1%) | Skuntank Lv30 | Sudowoodo Lv30 |
| 43 | Route 221 | file 169 | Poke Radar patches only | slots 4, 5 (10% each) | Nidorina | Nidorino |
| 44 | Route 221 | file 169 | Poke Radar patches only | slots 10, 11 (1% each) | Nidorino | Nidorina |
| 45 | Route 221 | file 169 | GBA dual-slot | slot 8 (4%); carts: Ruby, Sapphire, Emerald, FireRed, LeafGreen | Skuntank | Sudowoodo |
| 46 | Route 222 | file 170 | Grass | slot 1 (20%) | Gastrodon Lv40 | Glameow Lv40 |
| 47 | Route 222 | file 170 | Grass | slot 4 (10%) | Mr. Mime Lv41 | Purugly Lv41 |
| 48 | Route 222 | file 170 | Grass | slots 8, 10 (4/1%) | Mr. Mime Lv42 | Purugly Lv42 |
| 49 | Route 222 | file 170 | GBA dual-slot | slot 8 (4%); carts: Ruby, Sapphire, Emerald, FireRed, LeafGreen | Mr. Mime | Purugly |
| 50 | Route 225 | file 172 | Grass | slot 5 (10%) | Skuntank Lv51 | Roselia Lv51 |
| 51 | Route 226 | file 181 | Surf | slot 1 (30%) | Seel Lv35-45 | Spheal Lv35-45 |
| 52 | Route 226 | file 181 | Surf | slot 3 (4%) | Dewgong Lv40-55 | Sealeo Lv40-55 |
| 53 | Route 226 | file 181 | Surf | slot 4 (1%) | Dewgong Lv40-55 | Sealeo Lv40-55 |
| 54 | Route 229 | file 175 | Grass | slot 4 (10%) | Illumise Lv50 | Volbeat Lv50 |
| 55 | Route 229 | file 175 | Grass | slot 5 (10%) | Roselia Lv50 | Purugly Lv50 |
| 56 | Route 229 | file 175 | Grass | slot 6 (5%) | Scyther Lv52 | Pinsir Lv52 |
| 57 | Route 229 | file 175 | Grass | slot 7 (5%) | Volbeat Lv50 | Illumise Lv50 |
| 58 | Route 230 | file 182 | Grass | slot 3 (10%), and the 2nd entry of the day and night tables: every time of day | Beautifly Lv51 | Dustox Lv51 |
| 59 | Route 230 | file 182 | Surf | slot 1 (30%) | Seel Lv35-45 | Spheal Lv35-45 |
| 60 | Route 230 | file 182 | Surf | slot 3 (4%) | Dewgong Lv40-55 | Sealeo Lv40-55 |
| 61 | Route 230 | file 182 | Surf | slot 4 (1%) | Dewgong Lv40-55 | Sealeo Lv40-55 |

**What the table shows at a glance**

- Only grass, surf, Radar and dual-slot species differ. **No rod table differs** (Old, Good and Super Rod are identical in all 183 files), no rate or level differs, no `swarms`, `unown_table` or form-rate field differs.
- Eterna Forest, Routes 206, 209, 210, 214, 218, 221, 222, 225, 229, 230 and the Lost Tower change their regular grass; Routes 226 and 230 change the surf table; Routes 201, 205 north, 207, 209, 210, 214, 215, 221, Valor Lakefront and Fuego Ironworks change only the Poké Radar slots.
- The two Nidoran-line and Tauros/Miltank Radar rows swap the same two species between 10 % and 1 % slots: the pair is available in both games, only the odds of each differ.

### 1.3 Which species are exclusive to one game (every table, dump)

"Exclusive" = a species that occurs in at least one wild table of one game (grass, day, night, swarm, Poké Radar, dual-slot, surf, any rod) and in no table of the other game. `enc_report.py` builds both species sets from all 183 files of each NARC. All other species are either in neither game's tables or in both.

| Diamond only (13) | How it is met | Pearl only (14) | How it is met |
|---|---|---|---|
| Stunky | Routes 206, 214, 221 grass; dual-slot | Sudowoodo | Routes 214, 221 grass; dual-slot |
| Skuntank | Routes 221, 225 grass; dual-slot | Glameow | Routes 218, 222 grass; dual-slot |
| Mr. Mime | Routes 218, 222 grass; dual-slot | Purugly | Routes 222, 229 grass; dual-slot |
| Mime Jr. | Routes 209, 210 south grass: morning slots 2-3, plus the 4 % and 1 % slots all day; dual-slot | Bonsly | the same slots as Mime Jr. |
| Scyther | Route 229 grass (5 % slot) | Pinsir | Route 229 grass (5 % slot) |
| Seel | Routes 226, 230 surf (30 %) | Spheal | Routes 226, 230 surf (30 %) |
| Dewgong | Routes 226, 230 surf (4 % and 1 %) | Sealeo | Routes 226, 230 surf (4 % and 1 %) |
| Murkrow | Eterna Forest and Lost Tower 1F-5F, night only | Misdreavus | Eterna Forest and Lost Tower 1F-5F, night only |
| Silcoon | Eterna Forest grass (20 %); honey trees | Cascoon | Eterna Forest grass (20 %); honey trees |
| Aron | Fuego Ironworks, Poké Radar only | Dustox | Eterna Forest (1 % slots), Route 230 (10 %, all day) |
| Kecleon | Route 210 north, Radar only | Bagon | Route 210 north, Radar only |
| Larvitar | Route 207, Radar only | Stantler | Route 207, Radar only |
| Mightyena | Routes 214, 215, Radar only | Houndoom | Routes 214, 215, Radar only |
| | | Slowpoke | Route 205 north, Radar only |

Not exclusive, although they are in the tables above: **Beautifly** (Diamond's counterpart of Dustox at Eterna Forest and Route 230 is also on Route 224 in both games; Pearl has it only there), Gastrodon, Geodude, Illumise, Volbeat, Hoppip and Skiploom (Diamond: Route 205 north Radar; Pearl: Fuego Ironworks Radar), Miltank, Tauros, Nidoran♀, Nidoran♂, Nidorina, Nidorino: each is in both games, only its place, slot or odds change.

### 1.4 Sources that are not in the encounter files

| Source | What differs | Where (dump) |
|---|---|---|
| **Honey trees** | The common tree's second species: **Silcoon** in Diamond, **Cascoon** in Pearl. The other five (Wurmple, Combee, Burmy, Cherubi, Aipom), the rare tree (Combee, Burmy, Cherubi, Aipom, Heracross, Wurmple) and the Munchlax tree are identical. | `arc/encdata_ex.narc` (NARC 106, 12 members, identical in both ROMs). A table of three words in overlay 5, `ov05_021FC644` (0x021FC644), says which three members a tree type uses: Diamond `{2, 3, 4}`, Pearl `{5, 6, 7}`. Members 2 and 5 differ in one species (second entry: Silcoon, species 266 = 0x010A, against Cascoon, 268 = 0x010C); 3 = 6 and 4 = 7 are equal (`s3_roamer.py`). |
| Swarms | nothing: the species of every file's `swarms` field and the route picking are identical | `enc_diff2.py` |
| Great Marsh daily Pokémon, Feebas | nothing: `encdata_ex` members 0, 1 (Feebas), 9, 10 (Marsh lists) are in the identical NARC, and no code site that picks them is among the 27 differing places (2.3) | `s3_roamer.py`, section 2 |
| Roamers (Mesprit, Cresselia), static legendaries other than Dialga/Palkia, gift Pokémon, in-game trades | nothing (scripts and data identical; no version check) | section 3.5 |
| **Dialga / Palkia** (Level 47, Spear Pillar) | Dialga in Diamond, Palkia in Pearl | section 3.3 |

### 1.5 The Pokédex area data (`zukan_enc`) says the same thing

`application/zukanlist/zkn_data/zukan_enc_diamond.narc` (NARC 139) and `zukan_enc_pearl.narc` (NARC 140) each hold 4,954 members, identical in both ROMs. The code of overlay 16 (the Pokédex: `ov16_021DBD30`, `ov16_021DBDE4`, `ov16_021DBE0C`) picks 139 or 140 (three `.ifdef DIAMOND` sites, 0x021DBD8A, 0x021DBDF4, 0x021DBE1C). **83 of the 4,954 members differ; all of them are per-species area lists, none is one of the shared members 0-5 (place and field geometry).**

Layout (dump, matches `b2tools/patches/town_map.py`): members 0-3 are the 21 "places" (caves, lakes, Great Marsh ...) and 50 "fields" (routes, towns) of the area map; from member 4 on, `4 + 495 × category + species number` is the list of place or field numbers where a species is shown, for 10 categories: 0, 1, 2 = places by morning / day / night; 3 = places "special" without the National Pokédex and 4 = with it; 5, 6, 7 = fields by morning / day / night; 8 and 9 = fields "special" without / with the National Pokédex. The special lists hold honey trees and the Poké Radar and dual-slot species (`ov16_021E3FC4` picks 3/8 or 4/9 with `Pokedex_GetNatDexFlag`). The category meanings are **inferred** from which species fall in which list (for example Wurmple's honey trees in 3/4 and 8/9, Hippopotas's Ruin Maniac Cave only in 4).

| No. | Pokémon | Pokédex area list | Shown only in Diamond | Shown only in Pearl |
|---|---|---|---|---|
| 79 | Slowpoke | fields: special, National Dex | - | Route 205 north |
| 86 | Seel | fields, all times of day | Route 226, Route 230 | - |
| 87 | Dewgong | fields, all times of day | Route 226, Route 230 | - |
| 122 | Mr. Mime | fields, all times of day | Route 218, Route 222 | - |
| 123 | Scyther | fields, all times of day | Route 229 | - |
| 127 | Pinsir | fields, all times of day | - | Route 229 |
| 185 | Sudowoodo | fields, all times of day | - | Route 214, Route 221 |
| 187 | Hoppip | fields: special, National Dex | Route 205 north | Fuego Ironworks Exterior |
| 188 | Skiploom | fields: special, National Dex | Route 205 north | Fuego Ironworks Exterior |
| 198 | Murkrow | places: night | Eterna Forest Interior, Route 209 Lost Tower 1F | - |
| 200 | Misdreavus | places: night | - | Eterna Forest Interior, Route 209 Lost Tower 1F |
| 229 | Houndoom | fields: special, National Dex | - | Route 214, Route 215 |
| 234 | Stantler | fields: special, National Dex | - | Route 207 |
| 246 | Larvitar | fields: special, National Dex | Route 207 | - |
| 262 | Mightyena | fields: special, National Dex | Route 214, Route 215 | - |
| 266 | Silcoon | fields, special (honey trees) | Eterna Forest Exterior, Fuego Ironworks Exterior, Route 205 north, Route 205 south, Route 206, Route 207, Route 208, Route 209, Route 210 north, Route 210 south, Route 211 east, Route 212 north, Route 212 south, Route 213, Route 214, Route 215, Route 218, Route 221, Route 222, Valley Windworks Exterior | - |
| 266 | Silcoon | places, all times of day | Eterna Forest Interior | - |
| 266 | Silcoon | places, special (honey tree / marsh) | Floaroma Meadow | - |
| 267 | Beautifly | places, all times of day | Eterna Forest Interior | - |
| 267 | Beautifly | fields, all times of day | Route 230 | - |
| 268 | Cascoon | fields, special (honey trees) | - | Eterna Forest Exterior, Fuego Ironworks Exterior, Route 205 north, Route 205 south, Route 206, Route 207, Route 208, Route 209, Route 210 north, Route 210 south, Route 211 east, Route 212 north, Route 212 south, Route 213, Route 214, Route 215, Route 218, Route 221, Route 222, Valley Windworks Exterior |
| 268 | Cascoon | places, all times of day | - | Eterna Forest Interior |
| 268 | Cascoon | places, special (honey tree / marsh) | - | Floaroma Meadow |
| 269 | Dustox | places, all times of day | - | Eterna Forest Interior |
| 269 | Dustox | fields, all times of day | - | Route 230 |
| 304 | Aron | fields: special, National Dex | Fuego Ironworks Exterior | - |
| 315 | Roselia | fields, all times of day | Route 229 | - |
| 352 | Kecleon | fields: special, National Dex | Route 210 north | - |
| 363 | Spheal | fields, all times of day | - | Route 226, Route 230 |
| 364 | Sealeo | fields, all times of day | - | Route 226, Route 230 |
| 371 | Bagon | fields: special, National Dex | - | Route 210 north |
| 431 | Glameow | fields, all times of day | - | Route 218, Route 222 |
| 432 | Purugly | fields, all times of day | - | Route 222, Route 229 |
| 434 | Stunky | fields, all times of day | Route 206, Route 214, Route 221 | - |
| 435 | Skuntank | fields, all times of day | Route 221, Route 225 | - |
| 438 | Bonsly | fields, all times of day | - | Route 209, Route 210 south |
| 439 | Mime Jr. | fields, all times of day | Route 209, Route 210 south | - |

**Cross-check (dump):** the 31 species whose area list differs are exactly the species whose wild availability differs in 1.2/1.4, except that a species whose odds only move between slots (Gastrodon, Geodude, Illumise, Volbeat, Miltank, Tauros, Nidoran♀♂, Nidorina, Nidorino) keeps the same area list in both games. No Pokédex difference exists that the encounter tables do not explain, and no species has a list that the tables do not explain.

### 1.6 What is the same in both games

Every other wild table (159 of 183 files), all rod tables, all land rates and levels, all swarm species and their routes, the Great Marsh, Feebas, the roamers, the Pokédex place geometry (`zukan_enc` members 0-5), the Pal Park area lists and everything about Poké Radar chains, Honey Tree rules and encounter rates.

---


## 2. Every code switch

### 2.1 How the code differs, and why this list is complete (dump)

How the build makes the two games: `GAME_VERSION=DIAMOND` or `PEARL` (Makefile `make diamond` / `make pearl`). It does five things (`config.mk`, `Makefile`, `filesystem.mk`):

| Switch of the build | Diamond | Pearl |
|---|---|---|
| Assembler and compiler define | `-DDIAMOND`, so `GAME_VERSION` = `VERSION_DIAMOND` = 10 (`include/config.h:9-24`) | `-DPEARL`, `GAME_VERSION` = `VERSION_PEARL` = 11 |
| NitroFS file list | `poketool/personal/personal.narc` | the same slot is `poketool/personal_pearl/personal.narc` (`filesystem.mk:271-273`; `filesystem.c:11`) |
| ROM header | title `POKEMON D`, game code `ADA` + `E`, secure-area CRC 0x5931 | `POKEMON P`, `APA` + `E`, 0x014C (`config.mk:9-35`) |
| Banner | `pokediamond.us.bsf` (text "Pokémon Diamond") and `graphics/icon.png` | `pokepearl.us.bsf` ("Pokémon Pearl"), `graphics/icon_pearl.png` |
| Code | the `.ifdef DIAMOND` / `.ifdef PEARL` sites below | |

**Proof that nothing else differs.** Checks made on the two dumps (`rom_blocks.py`, `code_diff.py`, `sync_diff.py`, `small_classify.py`; section 6.2):

| Check | Result |
|---|---|
| The two dumps equal the decomp's two targets | Diamond SHA-1 `a46233d8...2e` = `pokediamond.us.sha1`; Pearl `99083bf1...9ac` = `pokepearl.us.sha1` |
| Every differing ROM byte, by owner | header 7, file-name table 4,847 + file table 13, arm9 8,329, overlay table 2, banner 101, `personal_pearl/personal.narc` 24, overlay 6: 88,692, overlay 5: 87, overlay 16: 49, overlay 83: 12, overlay 12: 8, overlay 48: 7, overlays 18, 63, 81: 4 each, overlays 7, 8, 11, 17, 62, 64: 2 each, overlays 54, 80, 84: 1 each. **No byte outside these regions differs** (arm7 is identical; no padding differs). |
| arm9 after the secure area (0x800 on) | Re-aligning the two images with branch targets masked leaves 291 mismatch regions: **253** single words that are pointers or call targets that merely moved (+8 into the file-name strings, +12 into the shifted overlay 6, or the moved system-call stubs); **17** larger blocks (pointer tables, the NARC file-name strings, whose pool is ordered differently because Pearl's `personal_pearl` string is longer, and the default-name function, which gains one instruction so its branch offsets move); and **21** words that are real: the sites E1 (0x02034CD8), F1 (0x0203EBDA), I4 (0x02064ED2) and I5 (0x020ECAC0), 5 pointers to overlay 6 functions (0x02049654, 0x0205DAC8, 0x020641A8, 0x02064280, 0x0208A2F8), and 12 ARM call sites of the moved system-call stubs (a 13th, a Thumb `bl` at 0x02079A02, is masked out of this comparison). |
| arm9 secure area (0x000-0x7FF, 2,036 bytes differ) | The Nitro SDK's system-call stubs (`SVC_*`) sit at different offsets and the rest of the 2 KB is random-looking filler. The decomp labels four stubs in Diamond's blob (`SVC_GetCRC16` at 0x020000C8, `SVC_Sqrt` 0x0200019E, `SVC_CpuSet` 0x020002FE, `SVC_WaitByLoop`) and fifteen in Pearl's (`SVC_GetCRC16` at 0x02000580, `SVC_Sqrt` 0x020004AC, `SVC_WaitByLoop` 0x0200050A, `SVC_CpuSet` 0x020006B2 ...); the rest of Diamond's is unlabelled data (`secure.s`, "TODO: Disassemble"). I confirmed in both dumps that `0E DF 70 47` (`swi 14; bx lr`) is at 0x02000580 in Pearl and at 0x020000C8 in Diamond. **13 call sites in arm9** (12 ARM `blx`, 1 Thumb `bl`; to `SVC_Sqrt`, `SVC_WaitByLoop`, `SVC_CpuSet`) **and 2 in overlay 83** (to `SVC_GetCRC16`, 0x0223488C and 0x02234944) call those stubs, so their call targets differ. |
| Overlay 6 | Real changes only in three places: `0x02239F48-0x0223A028` and `0x0223B574-0x0223B6AC` (camera and light of the Spear Pillar scene) and two `#GAME_VERSION` bytes (`0x02248C0C`, `0x02248C66`). Everything else is the code after them moved by 12 bytes (Pearl's is 12 bytes longer; its static-init pointers in the overlay table move from `0x02252228/2C` to `0x02252234/38`). |
| Overlays 7, 8, 11, 12, 17, 48, 62, 64, 81 and most of 5 and 63 | Only pointers into arm9's file-name strings (+8) and calls into the shifted overlay 6 (+12). Not behaviour. |

### 2.2 The switch sites, grouped by what they do

Kind: **C** = compile-time, the two ROMs hold different bytes at that address (decomp `.ifdef` or `GAME_VERSION`); **R** = run-time, both ROMs hold the same bytes and read `gGameVersion` (a word in arm9 data: 10 in Diamond, 11 in Pearl, `main.c:51`, 0x020ECAC0). Addresses are RAM addresses of the dump; "decomp" gives file and line.

**A. Title screen and opening movie (overlay 63, kind R)** : `ov63_021D74E0.s:901, 1914, 2132, 2274`. Plain words: which pictures, palettes, 3D model and camera the title uses.

| # | What it does | Diamond | Pearl |
|---|---|---|---|
| A1 | `ov63_021D7C18`: the 3D legend on the lower screen. Loads its model and texture animation from `demo/title/titledemo.narc` (NARC 48) | members **6** (model, 51,572 B) and **19** (texture animation) = Dialga | members **5** (65,584 B) and **18** = Palkia |
| A2 | `ov63_021D83A8`: the upper screen's logo picture and colours | graphics member 1 with palettes 2, 9, 13: "Pokémon Diamond Version" logo, blue-white | graphics member 3 with palettes 4, 10, 14: "Pokémon Pearl Version" logo, pink-white (rendered and looked at: `title_render.py`; the two NCGRs and the palettes are different bytes) |
| A3 | `ov63_021D85D8`: a background of the opening movie, from `demo/title/op_demo.narc` (NARC 128): graphics, palette, screen | members 11, 10, 12 | members 8, 7, 9. **The two sets are byte-identical** (`op_demo` 7 = 10, 8 = 11, 9 = 12), so nothing visible differs. |
| A4 | `ov63_021D86E0`: camera position, target, clipping and light direction for the 3D legend: two full sets of about 20 fixed-point numbers | Diamond's set (Dialga) | Pearl's set (Palkia) |

**B. New game: Rowan's intro (overlay 59, kind R)** : `ov59_Intro.c:772, 877, 2442`; `ov59` is byte-identical in the two ROMs.

| # | What it does | Diamond | Pearl |
|---|---|---|---|
| B1 | `ov59_CreateListWithText`: the four rival names offered on the "New name!" list, text bank 341 | messages 37-40: Barry, Damion, Tyson, Markus | messages 41-44: Clint, Ralph, Lewis, Tommy |
| B2 | `ov59_MasterController`: the same split when you pick one (copies that name to the rival) | list `ov59_021D9F40` | list `ov59_021D9F68` |
| B3 | `ov59_LoadInitialTilemap`: colours of the intro's two backgrounds (`demo/intro/intro.narc`) | members 1 and 24: blue-grey (first colours `#bdcde6`, `#b4c5de`, ...) | members 2 and 25: pink (`#e6c5de`, `#e6bdd5`, ...). The graphics and the other 44 members are the same. |

**C. Default names (arm9 `sub_020777D4`, kind C)** : `unk_020772F0.s:1299, 1314, 1339`. Plain words: what name the game fills in when the player or rival picks no name. Text bank 376.

| # | Name | Diamond | Pearl |
|---|---|---|---|
| C1 | player, boy | one of messages 0-17: **"Diamond"**, Ash, Nic, ... Mark | messages 44-61: **"Pearl"**, Ash, Nic, ... Mark |
| C2 | player, girl | messages 18-35: **"Diamond"**, Karla, ... Maggie | messages 62-79: **"Pearl"**, Karla, ... Maggie |
| C3 | the rival (naming type 3; **inferred** from Platinum's numbering) | message 88 "Pearl" | message 89 "Diamond" |

**D. Screens that name the game**

| # | What it does | Where | Diamond | Pearl | Kind |
|---|---|---|---|---|---|
| D1 | OPTIONS heading under the title, `ReadMsgDataIntoString(gGameVersion - 9)` on bank 206 | overlay 60, `ov60_021D7D18` (`overlay_60.s:1022`) | "POKéMON DIAMOND" (msg 1) | "POKéMON PEARL" (msg 2) | R |
| D2 | first heading of the credits, bank 493 | overlay 84, table word `ov84_021DA764` (0x021DA764) | 0 = "Pokémon Diamond" | 1 = "Pokémon Pearl" | C |
| D3 | the DS menu: icon, banner text, ROM title | ROM header and banner (2.1, 4.6) | blue icon, "Pokémon Diamond", `POKEMON D` | pink icon, "Pokémon Pearl", `POKEMON P` | C |

**E. Wild Pokémon, Pokédex and data files**

| # | What it does | Where | Diamond | Pearl | Kind |
|---|---|---|---|---|---|
| E1 | Which wild-table NARC every zone uses (section 1) | arm9 `sub_02034CB4`, byte at 0x02034CD8 | NARC id 0x25 (d_enc_data) | 0x8F (p_enc_data) | C |
| E2 | Which three tables the honey trees use (1.4) | overlay 5, `ov05_021FC644`, 0x021FC644 | members 2, 3, 4 of encdata_ex | 5, 6, 7 | C |
| E3 | Which Pokédex area NARC (three loaders; 1.5) | overlay 16, 0x021DBD8A, 0x021DBDF4, 0x021DBE1C | NARC 139 `zukan_enc_diamond` | NARC 140 `zukan_enc_pearl` | C |
| E4 | Which Pokédex entry text (3.6.1) | overlay 16, `ov16_021DBC48`, 0x021DBC62-0x021DBC98 | bank 0x267 = 615 | bank 0x268 = 616 | C |
| E5 | Which personal-data file (the Pokémon's base stats table) | arm9 file-name table (`filesystem.c:11`): the string `poketool/personal/personal.narc` (Diamond, near 0x02105268) or `poketool/personal_pearl/personal.narc` (Pearl, near 0x02105484) | `poketool/personal/personal.narc` | `poketool/personal_pearl/personal.narc`. The two files differ in 24 bytes: the held items of 6 species (4.1). | C |

**F. Dialga, Palkia and the Spear Pillar**

| # | What it does | Where | Diamond | Pearl | Kind |
|---|---|---|---|---|---|
| F1 | Script command `GetGameVersion` (opcode 0x0246) returns the version to a script variable (section 3: 6 uses) | arm9 `ScrCmd_GetGameVersion`, `scrcmd.c:3952`, byte at 0x0203EBDA | 10 | 11 | C |
| F2 | The Spear Pillar ground: zone 220's header says land matrix 22; the game replaces it by 23 in Pearl | arm9 `MapHeader_GetMatrixId` (~0x0203475A): `if (matrix == 22 && gGameVersion == VERSION_PEARL) matrix = 23` (`map_header.c:663-670`; same bytes in both ROMs) | matrix 22 (land chunks 352-355) | matrix 23 (chunks 356-359) | R |
| F3 | The 3D summoning scene (script command 0x020D `SpearPillarSequence`, stage table 0x0224F174): camera angle, clipping distance and two light-direction sets | overlay 6, `0x02239F48-0x0223A028`, `0x0223B574-0x0223B6AC` (`overlay_06.s:1212-1274, 4188-4214, 4321-4357`) | 11 pool constants plus immediates, e.g. camera distance 0x000C8A55, angle 0x22A2, near clip 0x2000, far clip 0x7D0000 (list in 3.2) | the other set: 0x000D5052, 0x19A3, near 0xE000, far 0x7EF000 | C |

The numbers of F3 are listed in section 3.2. That they belong to the summoning scene follows from the call chain: **inferred**, the scene was not run.

**G. The Underground (overlay 18, kind C)** : `overlay_18.s:3035-3060`; the function `ov18_0223AE88` (0x0223AE88).

Overlay 18 is the Underground: it loads `ug_trap.narc`, `ug_fossil.narc`, `ug_parts.narc` and `underg_radar.narc` and reads text bank 569 (the names of what can be dug up). `ov18_0223AE88` returns the **chance weight** of one buried object from the 85-entry table at 0x02250B30 (20 bytes per entry). The sum over the table (`ov18_0223AED4`) and a subtract-until-negative pick (`ov18_0223AEFC`) make it a weighted random draw (**proven** from the code). Each entry holds four weights: Diamond reads the u16 at +4 (before the National Pokédex) or +8 (after), Pearl the u16 at +6 or +10. The entry's object number at +0xE is the index into bank 569's names (**inferred**; the names match the weights below). When a save flag is set (`sub_02025C38() != 0`, meaning not traced: **UNVERIFIED**), Diamond adds +33 to object 6 and +66 to object 1 (the large and the small Prism Sphere) and Pearl does the same for objects 7 and 2 (the Pale Spheres). The sizes (4 × 4 and 6 × 6 squares) are read from the entry's two shape bytes at +0xC and +0xD (**inferred**).

All 85 entries are the same in both games except where the table's two columns differ. The entries that give a different chance in the two games (before the National Pokédex / after it; **the Diamond column is the Diamond game's, the Pearl column the Pearl game's**):

| Object (entry) | Diamond | Pearl |
|---|---|---|
| Prism Sphere, small (4 × 4) | 30 / 27 | 22 / 20 |
| Pale Sphere, small (4 × 4) | 22 / 20 | 30 / 27 |
| Red Sphere, small (4 × 4) | 166 / 122 | 192 / 150 |
| Blue Sphere, small (4 × 4) | 192 / 150 | 166 / 122 |
| Prism Sphere, large (6 × 6) | 15 / 13 | 13 / 10 |
| Pale Sphere, large (6 × 6) | 13 / 10 | 15 / 13 |
| Red Sphere, large (6 × 6) | 83 / 61 | 96 / 75 |
| Blue Sphere, large (6 × 6) | 96 / 75 | 83 / 61 |
| Sun Stone | 4 / 15 | 1 / 3 |
| Moon Stone (two shapes) | 1 / 1 and 1 / 2 | 2 / 8 and 2 / 7 |
| Thunderstone | 4 / 30 | 1 / 5 |
| Fire Stone | 4 / 30 | 1 / 5 |
| Water Stone | 1 / 5 | 4 / 30 |
| Leaf Stone (two shapes) | 1 / 3 and 1 / 2 | 2 / 15 and 2 / 15 |
| Helix Fossil (4 shapes) | 0 / 3 each | 0 / 1 each |
| Dome Fossil | 0 / 1 | 0 / 13 |
| Claw Fossil (4 shapes) | 0 / 3 each | 0 / 1 each |
| Root Fossil (4 shapes) | 0 / 1 each | 0 / 3 each |
| Red Shard | 10 / 12 | 15 / 22 |
| Blue Shard | 15 / 25 | 10 / 15 |
| Yellow Shard | 15 / 22 | 10 / 12 |
| Green Shard | 10 / 12 | 15 / 22 |
| **Armor Fossil** | **0 / 0 (never)** | **25 / 12** |
| **Skull Fossil** | **25 / 12** | **0 / 0 (never)** |
| Light Clay | 1 / 5 | 1 / 2 |
| Iron Ball | 1 / 2 | 1 / 5 |
| Icy Rock | 2 / 11 | 1 / 5 |
| Smooth Rock | 1 / 5 | 2 / 11 |
| Heat Rock | 2 / 11 | 1 / 5 |
| Damp Rock | 1 / 5 | 2 / 11 |

Not different: Oval Stone, Odd Keystone, Star Piece, Hard Stone, Everstone, Old Amber, Rare Bone, Revive, Max Revive, Heart Scale, all 16 plates and every other entry (traps and goods). The weights are the game's draw weights; one "Helix / Claw / Root Fossil" entry exists per shape, which is why four rows share a number. **Skull Fossil (Cranidos) is Diamond's version fossil and Armor Fossil (Shieldon) is Pearl's**; the table gives them to one game each.

**H. Pal Park (overlay 83, kind C)** : `overlay_83.s:11569, 18711, 19202, 26904`, plus one R site (`:6543`).

| # | What it does | Where | Diamond | Pearl |
|---|---|---|---|---|
| H1 | Checks the GBA save's field at +0x48 for this DS game's bit; if missing, returns code 1 (meaning **inferred**: "this save may not be moved to this game") | `ov83_022332B4`, 0x022332F0 | bit 10 (0x400) | bit 11 (0x800) |
| H2 | The "Make Pokémon migrate to the Pokémon ... Game Card?" confirmation, bank 403 | `ov83_02236804`, 0x0223692E | message 34 | message 35 |
| H3 | "Six Pokémon safely migrated to the Pokémon ... Game Card." | `ov83_02236804`, 0x02236D30 | message 29 | message 30 |
| H4 | "Saving data on Pokémon {Ruby / Sapphire / Emerald / FireRed / LeafGreen} and Pokémon ...", five messages | table `ov83_0223B288` (0x0223B28C...) | messages 20, 18, 22, 24, 26 (Sapphire, Ruby, Emerald, FireRed, LeafGreen + "Diamond") | messages 21, 19, 23, 25, 27 (... + "Pearl") |
| H5 | Pal Park start-up passes the running version to `sub_02016438` (R) | `ov83_02230954`, `overlay_83.s:6543` | 10 | 11 |
| H6 | Two calls to `SVC_GetCRC16` (the stub moved, 2.1) | 0x0223488C, 0x02234944 | target 0x020000C8 | target 0x02000580 |

**I. The player's own version written into records (kinds C and R)**. Plain words: the game stamps its own version into data other players or the Pokédex of another game will see.

| # | What it does | Where | Diamond | Pearl | Kind |
|---|---|---|---|---|---|
| I1 | Every Pokémon you catch, hatch, receive or generate gets its "Met game" field set to the running game's version | arm9 `pokemon.c:291` and `:3156` | 10 | 11 | R |
| I2 | A mail letter's "author's game" | arm9 `mail.c:20` | 10 | 11 | R |
| I3 | The trainer record built for link features: version at +0xB8 | arm9 `sub_02066840` (`unk_02066840.s:39`) | 10 | 11 | R |
| I4 | Records built for another player, with the constant `GAME_VERSION` | arm9 `unk_02064E90.s:36` (0x02064ED2); overlay 6 `overlay_06.s:31435, 31472` (0x02248C0C, 0x02248C66); overlay 54 `overlay_54.s:3738` (0x021D91F6); overlay 80 `overlay_80.s:13626` (0x02234316) | 10 | 11 | C |
| I5 | The variable itself | arm9 `main.c:51`, 0x020ECAC0 | 10 | 11 | C |
| I6 | The Battle Frontier record shows the author's game from a stored bit (bank 17 messages 22 "DIAMOND" / 23 "PEARL"): who writes the bit is **UNVERIFIED** | arm9 `unk_0202A1E0.c:400` | | | R |

The features behind I3 and I4 (Union Room, Wi-Fi, the Global Terminal-like record of overlay 80, a save block the decomp calls "SafariZone") are **inferred** from what the functions copy (name, trainer ID, gender, version, language, a Pokémon); I did not trace which menu calls them.

**J. The ROM itself (kind C)**

| # | What | Diamond | Pearl |
|---|---|---|---|
| J1 | Header title, offset 0x00 | `POKEMON D` | `POKEMON P` |
| J2 | Game code, 0x0C | `ADAE` | `APAE` |
| J3 | Header: file-name table size (0x44), secure-area CRC (0x6C), header CRC (0x15E) | 5,503 bytes, 0x5931, 0xCA37 | 5,529 bytes, 0x014C, 0xA80C |
| J4 | The file name and file tables: Pearl has the extra directory `poketool/personal_pearl/`, so `personal.narc` has file id 328 instead of 326 and `pms.narc` / `wotbl.narc` move down one id; the data stays at the same ROM offset | | |
| J5 | Overlay table entry of overlay 6: static-init pointers | 0x02252228, 0x0225222C | 0x02252234, 0x02252238 |
| J6 | Banner (2.1): 101 bytes: CRC, six language titles, 5 palette entries of the icon | "Pokémon Diamond / Nintendo", blue ball | "Pokémon Pearl / Nintendo", pink ball |
| J7 | arm9 secure area and its stubs | 2.1 | |

### 2.3 Counts

| Count | Value | How counted |
|---|---|---|
| `.ifdef DIAMOND / PEARL` and `#ifdef PEARL` blocks in arm9 and overlays | 32 | arm9: `secure.s` 1, `unk_02034A28.s` 1, `unk_020772F0.s` 3, `filesystem.c` 1; overlay 5: 1; overlay 6: 11; overlay 16: 5; overlay 18: 4; overlay 83: 4; overlay 84: 1 |
| `GAME_VERSION` uses | 7 | five `mov #GAME_VERSION` (arm9, overlays 6 ×2, 54, 80), `main.c` (the variable), `scrcmd.c` (the script command); `map_header.c`'s `ENCDATA` macro (154 headers) and `config.h` do not change any byte |
| **Compile-time sites** | **39** | 32 + 7; they form **27 places in the ROM** (arm9 9, overlay 5: 1, overlay 6: 5, overlay 16: 4, overlay 18: 1, overlay 54: 1, overlay 80: 1, overlay 83: 4, overlay 84: 1) |
| **Run-time sites** (`gGameVersion` or `VERSION_` read) | **14** | arm9: `unk_02066840.s`, `mail.c`, `pokemon.c` ×2, `map_header.c:668`; overlay 59 ×3; overlay 60 ×1; overlay 63 ×4; overlay 83 ×1 |
| Script commands | 6 (4 files) | section 3 |

**The same sites by what the switch changes** (so a reader can see which are only constants)

| The switch picks | Sites |
|---|---|
| Which file or NARC member to load | E1 (wild-table NARC), E2 (honey tables), E3 (Pokédex area NARC, three loaders), E5 (personal file), A1-A3 (title models, logo art and palettes, opening-movie set), B3 (intro palettes) |
| Which text bank or message to show | B1-B2 (rival names), C1-C3 (default names), D1 (Options heading), D2 (credits), E4 (Pokédex entries, bank 615 / 616), H2-H4 (Pal Park lines) |
| A plain number (version value, camera, light, bit, weight column) | F1 (10 / 11), F2 (matrix 22 / 23), F3 (camera and light constants), A4 (title camera and light), G (Underground weight columns), H1 (bit), H5, I1-I5 (version stamps) |
| Layout of the ROM itself | J1-J7 (header, file tables, banner, secure area, overlay table) |

---


## 3. Field scripts and the text they show

Everything marked **proven** was read from the two dumps (Pearl `APAE`, Diamond `ADAE`, both Rev 5) by the helper scripts listed in 3.10 and section 6. Anything inferred or not traced is marked **inferred** or **UNVERIFIED** and collected in 3.8.

### 3.0 What the dumps say about scripts and text (proven)

| Fact | Evidence |
|---|---|
| The field scripts are the same bytes in both games. `fielddata/script/scr_seq_release.narc` (1,051 script files) is identical, so every version difference is decided while the script runs. | `s3_verify.py`: byte-identical. |
| So are the text (`msgdata/msg.narc`, 624 banks, 30,211 messages), the zone events (`zone_event_release.narc`), the map matrices, land data, area data, items, trainers and the zone header table (all 559 headers equal, `hdr_diff.py`). | `s3_verify.py`, `hdr_diff.py`. |
| A script learns the game from one command, **GetGameVersion = opcode 0x0246 (582)**, handler `ScrCmd_GetGameVersion` (pokediamond `arm9/src/scrcmd.c:3952`). It stores 10 for Diamond and 11 for Pearl. | The handler, found through `gScriptCmdTable` (0x020F355C, entry 582) in each arm9, ends in `mov r1,#0x0b` (Pearl) / `mov r1,#0x0a` (Diamond). `s3_getver.py`. |
| In decoded scripts, `CompareVarToValue v, 0xA` + `GoToIf 1` / `CallIf 1` means "if Diamond"; `... 0xB` means "if Pearl". Condition 1 is "equal" (table `sScriptConditionTable` at 0x020F34E8: row 1 = 0,1,0). | decomp `arm9/asm/unk_02038C78.s`; `scrcmd.c` `ScrCmd_GoToIf`. |
| All 1,051 files decode with 0 unexplained bytes (`b2tools/gen4_script.py` run on the Pearl dump; the fresh decode equals `work/pearl/scripts/*.txt` byte for byte). Only **4** files contain GetGameVersion, **6** commands in total. No other script command compares against 10/11 (the other `CompareVarToValue ... 0xA/0xB` lines are unrelated numbers). | `grep -c GetGameVersion` over the decode. |

Reading key used below: **D** = Diamond, **P** = Pearl. "msg N" = message number N of the text bank named. "State" = the value of VAR_0x4098 (Spear Pillar progress).

### 3.1 The six version checks (the complete list)

| # | Script file | Zone (id), text bank | Command at | What it does | Diamond | Pearl |
|---|---|---|---|---|---|---|
| 1 | 230 (`scripts` of zone 220) | MAP_MOUNT_CORONET_SPEAR_PILLAR (220), bank 220. Level script 690, `OnTransition` runs script_1 when you enter the zone | `@008C` (subroutine L_0086) | Chooses the overworld sprite of the legendary: sets VAR_0x4021 | 0x9A = 154 = Dialga's sprite | 0x9B = 155 = Palkia's sprite (script `SetVar` at `@009D`) |
| 2 | 230 | same | `@00A5` (L_00A5) | Hides one of the two Orb item balls (both lie on tile 31,10; see 3.3) | sets flag 0x401: hides the Lustrous Orb ball, the **Adamant Orb** ball stays | sets flag 0x3FF: hides the Adamant Orb ball, the **Lustrous Orb** ball stays |
| 3 | 230 | same | `@01E8` (L_01E8, "pair selector") | Subroutine called from 18 places in the Spear Pillar scenes with two values in VAR_0x8005 / VAR_0x8006; leaves the version's one in VAR_0x8004 (D takes 0x8005, P takes 0x8006). Used to choose text lines and the species. 17 of the 18 calls give different values (3.3) | first value | second value |
| 4 | 69 (zone 65's scripts) | MAP_ETERNA (65), bank 78. Runs from the sign event at tile (327,525) (script_18) = the statue | `@039A` | Which inscription is read on the statue | msg 27 | msg 28 |
| 5 | 1017 | MAP_CELESTIC_CYNTHIA_GRANDPARENTS_HOUSE (445), bank 529. The elder (object 1, script_2) after flag 0x15E | `@0063` (L_0060) | Which picture and which page of the old book | picture of species 484 (**Palkia**), msg 4 | picture of species 483 (**Dialga**), msg 5 |
| 6 | 977 (global scripts with id 10300 and up, text bank 496) | Run by the partner trainer (Dawn if you are a boy, Lucas if a girl) in MAP_SANDGEM (418) object 4 at (168,845) and MAP_SANDGEM_ROWANS_LAB (422) object 3 at (7,14) | `@0261` (L_025E) | Buffer 1 gets a species name for the hint "the professor thinks X may have reappeared at the Spear Pillar" (msg 0 for Dawn, msg 14 for Lucas) | DIALGA (`Unk00DA 1, 0x1E3`) | PALKIA (`Unk00DA 1, 0x1E4`) |

Conditions of #6 (proven from the decode): runs only when the Sinnoh Pokédex is not complete, flag 0x145 is set (the Celestic elder has shown the book), flag 0x15F is clear (the legendary is not caught) and VAR_0x4098 equals 5 (the legendary may be fought again). Otherwise the partner says an unrelated line (msg 1/15 Celestic hint, msg 13/27 congratulations).

### 3.2 Things that change without a version command

| What | Where (proven) | Diamond | Pearl |
|---|---|---|---|
| The two Orb item balls | Spear Pillar events file 217 (zone 220): object 12 (`script` 7253, hidden flag 0x3FF) and object 13 (`script` 7254, hidden flag 0x401), both graphics 87, both at tile (31,10). Script 7253 = global file 370 entry 254 = `SetVar VAR_0x8008, 0x87` (item 135, **Adamant Orb**, 1); 7254 = entry 255 = item 136, **Lustrous Orb**. Both go on into the common item-ball script (entry 256). Flags 0x3FF/0x401 are used by nothing else. | Adamant Orb ball only (object 13 hidden) | Lustrous Orb ball only (object 12 hidden) |
| The legendary's overworld figure | Spear Pillar object 5 (graphics id 102, hidden flag 0x1E2, script 1): 102 is the first of the "variable graphics" ids (OBJ_EVENT_GFX_VAR_1 in pokeplatinum, so VAR_0x4021). **Inferred** from Platinum's table; PearlB2's own note says the same (data/pearl_sprite_map.json "154"). | Dialga | Palkia |
| The ground of the Spear Pillar | arm9 `MapHeader_GetMatrixId` at 0x0203475A (same bytes in both ROMs: `cmp r0,#0x16 ... ldr gGameVersion ... cmp r1,#0x0b ... mov r0,#0x17`): zone 220's header says matrix 22; in Pearl the game swaps it for matrix 23 (the header of zone 221 "MAP_MOUNT_CORONET_UNUSED_2" shows matrix 23). Matrix 22 = land chunks 352-355, matrix 23 = chunks 356-359; all four pairs differ in model, collision and chunk data (`s3_matrix.py`; sizes e.g. 25,020 vs 25,280 B). | matrix 22 (chunks 352-355) | matrix 23 (chunks 356-359) |
| The 3D summoning scene (camera angle, clip planes, light directions) | ov06 `SpearPillarSequence` (0x022456E8, called by script command 0x020D) uses the stage table at 0x0224F174 (ov06_02239F80, ...). 11 literal-pool constants differ (Diamond/Pearl): 0x1701/0x10C1, 0x000C8A55/0x000D5052, 0x002280EF/0x001BFFBD, 0x000CA424/0x000AA361, 0x00268C50/0x0025DFDC, 0x22A2/0x19A3, 0xF49F/0xE667, 0x80B5/0x760B, 0x29BA8/0x85A8, 0x37294/0x156B1, 0xB6876/0x99919, plus some immediate operands (the `.ifdef DIAMOND` blocks at `overlay_06.s` lines 1212-1274, 4188-4214, 4321-4357). Every constant above was found at the stated place in the right dump (`s3_ov06_const.py`); that they belong to this scene is **inferred** from the call chain. | Diamond's constants | Pearl's constants |

### 3.3 The Spear Pillar scenes, line by line

Script file 230. Triggers are coordinate events keyed on VAR_0x4098 ("state"). 18 calls of the pair selector; 17 differ.

| Script (trigger) | Offset | What is chosen | Diamond | Pearl |
|---|---|---|---|---|
| script_4 (tiles x 29-33, z 35; state 1): the boss summons the legendary with the Red Chain | `@0333` | speech (bank 220) | msg 3: commands "DIALGA, the mythical Pokémon, and the master of time" | msg 4: "PALKIA, ... the master of space and dimensions" |
| script_4 | `@0397` | speech | msg 5: "Can you feel time distorting? Only I can choose to stop it." | msg 6: "Feel the dimensions distorting... Only I can stop it." |
| script_4 | `@0494` | speech | msg 7: "DIALGA, the ancient deity of time" | msg 8: "PALKIA, the ancient deity of space and the dimensions" |
| script_4 | `@04B6` | species of the cry (PlayCry) | 483 Dialga | 484 Palkia |
| script_4 | `@04CE` | cry text | msg 9 "DIALGA: Gugyugubah!" | msg 10 "PALKIA: Gagyagyaah!" |
| script_5 (tiles x 30-32, z 32; state 2): the boss, Mars and Jupiter, the lake trio | `@0AD8` | boss reacts to the legendary | msg 23 (DIALGA) | msg 24 (PALKIA) |
| script_5 | `@0BE5` | the boss's farewell (the only pair whose wording differs beyond the name) | msg 30: "The most important thing... What shines the brightest..." | msg 31: "The most beautiful thing... Joy that shines the brightest..." |
| script_5 | `@0D87` | Rowan before the battle | msg 36 (DIALGA, "master of time") | msg 37 (PALKIA, "master of space and the dimensions") |
| script_8 (talk to Rowan at tile 29,36; this speech only while state is 3, otherwise a plain line, msg 45) | `@11CB` | the same Rowan speech | msg 36 | msg 37 |
| script_9 (tiles x 29-33, z 31; state 3) | `@0E69` | pair 38 / 38: **same text in both** | msg 38 | msg 38 |
| script_10 (tiles x 30-32, z 26; state 3): the first battle | `@0EA2` | cry species | 483 | 484 |
| script_10 | `@0EBA` | cry text | msg 32 | msg 33 |
| script_10 | `@0ED6` | **LegendaryBattle VAR_0x8004, 0x2F**: the wild battle, level 0x2F = 47 | Dialga Lv 47 | Palkia Lv 47 |
| script_10 | `@0F22` | text if it is not caught ("returned to the world from which it came") | msg 34 (DIALGA) | msg 35 (PALKIA) |
| script_14 (tiles x 29-33, z 26; state 5): the rematch | `@1209` | cry species | 483 | 484 |
| script_14 | `@1221` | cry text | msg 32 | msg 33 |
| script_14 | `@123D` | LegendaryBattle, level 47 | Dialga | Palkia |
| script_14 | `@128D` | text if not caught | msg 34 | msg 35 |

After the battle both versions do the same thing: flag 0x15F is set when the legendary is caught, state 4 is set and flag 0x15E is set (script_10 `@0FEC`, `@0FF8`; script_14 `@1262`), which opens the Celestic elder's book. The scripts' other text (grunts, Mars, Jupiter, Rowan, the Azure Flute lines) is identical.

Message pairs that differ (bank 220): 3/4, 5/6, 7/8, 9/10, 23/24, 30/31, 32/33, 34/35, 36/37 (nine pairs; 38/38 is equal). Together with Eterna 27/28 and Celestic 4/5 that is 22 version-dependent messages in the field scripts, plus the species name that Dawn/Lucas insert.

### 3.4 The other places

| Place | Diamond shows | Pearl shows | Source |
|---|---|---|---|
| Eterna City: the Pokémon statue (sign at tile 327,525, bank 78) | msg 27: "...creation of DIA... giver of time ... the blessing of DIA..." (Dialga) | msg 28: "...birth of PAL... creator of parallel dimensions ... rifts in space ... the blessing of PAL..." (Palkia) | file 69 script_18 `@039A` |
| Celestic Town, the elder in Cynthia's grandparents' house, after flag 0x15E (bank 529) | the book page for **Palkia**: picture of species 484 + msg 4 ("PALKIA, the Pokémon that binds the spatial dimensions") | the book page for **Dialga**: picture of 483 + msg 5 ("DIALGA, the guardian Pokémon of time") | file 1017 `@0063..@00A6`; then both set flag 0x145 and say msg 6. Note it is the *other* legend than the one on the cover |
| Sandgem Town and Rowan's Lab, the partner trainer (bank 496) | "...the professor thinks DIALGA may have reappeared at the Spear Pillar" (msg 0 Dawn / msg 14 Lucas) | the same line with PALKIA | file 977 `@025E` |
| Spear Pillar, the top (31,10) | Adamant Orb | Lustrous Orb | 3.2 |
| Spear Pillar, the scene | Dialga | Palkia | 3.3 |

### 3.5 Checked and NOT version-dependent in the scripts (proven unless noted)

- **In-game trades:** the NPC trade commands (`NPCTradeInit`, script 0x0226 and the trade table in the identical NARCs) contain no version test; no trade script calls GetGameVersion. All Pokémon created by the game record "Met game" = the running game's version (pokediamond `arm9/src/pokemon.c:291` and `:3156` store `gGameVersion`), so gifts, trades and wild catches show Diamond or Pearl as the origin. Whether the NPC-trade code overwrites that field was not traced (**UNVERIFIED**).
- **Gift and event Pokémon:** only four script files call GetGameVersion (3.1), so no gift script branches on the version (starter, Eevee, Togepi egg, Riolu egg, fossils, Happiny, Porygon, Drifloon, Spiritomb and the rest are the same in both games). The same holds for every legendary other than Dialga/Palkia (Uxie, Mesprit, Azelf, Giratina, Heatran, Regigigas, Darkrai, Cresselia, Arceus, Shaymin, Manaphy).
- **Trainers, NPC lines, shops, Gyms, Pokémon League, Hall of Fame:** no version branch (scripts, trainer files and text are identical, and no other script reads the version).
- **Game completion, birthday, National Dex checks** (`CheckGameCompleted`, `CheckBirthday`, `CheckSinnohDexComplete`) are not version tests.
- **`GetGBACartridgeVersion`** (the dual-slot GBA check for Ruby/Sapphire/Emerald/FireRed/LeafGreen) is about the cartridge in slot 2, not the DS game.

### 3.6 Text that differs or names a game

#### 3.6.1 Whole text banks that differ (proven)

| Bank | What | Diamond | Pearl | Chosen by |
|---|---|---|---|---|
| 615 / 616 (494 messages each) | **Pokédex entries**, message number = National Dex number | bank 615 | bank 616 | ov16 `0x021DBC6C`: Diamond has `ldr r0,=0x267` (615), Pearl `mov r0,#0x9a; lsl r0,r0,#2` = 0x268 (616) (`s3_ov16.py`); the same code sits in both ROMs' decomp as `.ifdef DIAMOND`. |

**156 of 494 entries differ** (`s3_dex_diff.json`: 72 below no. 387, 75 Sinnoh-new species 387-461, 9 above; every one is reworded, Fearow no. 22 only slightly):
22 Fearow; 25-26 Pikachu, Raichu; 35-36 Clefairy, Clefable; 41-42 Zubat, Golbat; 47 Parasect; 54-55 Psyduck, Golduck; 63-68 Abra line, Machop line; 72-78 Tentacool, Tentacruel, Geodude line, Ponyta, Rapidash; 92-95 Gastly line, Onix; 113 Chansey; 118-119 Goldeen, Seaking; 122 Mr. Mime; 129-130 Magikarp, Gyarados; 143 Snorlax; 163-164 Hoothoot, Noctowl; 169 Crobat; 172-173 Pichu, Cleffa; 183-185 Marill, Azumarill, Sudowoodo; 190 Aipom; 194-195 Wooper, Quagsire; 198 Murkrow; 200-201 Misdreavus, Unown; 203 Girafarig; 208 Steelix; 214-215 Heracross, Sneasel; 223-224 Remoraid, Octillery; 226 Mantine; 242 Blissey; 265-269 Wurmple line; 278-279 Wingull, Pelipper; 298 Azurill; 307-308 Meditite, Medicham; 315 Roselia; 339-340 Barboach, Whiscash; 349-350 Feebas, Milotic; 358 Chimecho; and **every Sinnoh-new species 387-461** (Turtwig to Weavile, 75 entries); 480-484 Uxie, Mesprit, Azelf, Dialga, Palkia; 490-493 Manaphy, Darkrai, Shaymin, Arceus. Banks 619 (weights), 620 (heights), 621 (categories) are single banks, the same in both. No other pair of text banks in the dump looks like a version split (`s3_bank_pairs.py`).

#### 3.6.2 Text picked by code, not by scripts (proven from the code and the dump bytes unless marked)

| Where | Text | Diamond | Pearl | How chosen |
|---|---|---|---|---|
| Intro: the rival's name list (ov59 `ov59_Intro.c:772-777` and `:2442-2450`, bank 341) | msg 36 "New name!" + 4 names | msgs 37-40: Barry, Damion, Tyson, Markus | msgs 41-44: Clint, Ralph, Lewis, Tommy | runtime `gGameVersion == VERSION_DIAMOND` (ov59 is byte-identical in both ROMs) |
| Intro: the colour palette of the two backgrounds | `intro.narc` palettes | `main_background_diamond.NCLR` / `sub_background_diamond.NCLR` | `..._pearl.NCLR` | `ov59_Intro.c:877-883` (section 4.4 covers the art) |
| Name entry: the name used when the player enters nothing (arm9 `unk_020772F0.s` `sub_020777D4`, bank 376) | default name | player boy: random of msgs 0-17 (msg 0 = "Diamond", then 17 boy names); girl: random of msgs 18-35 (msg 18 = "Diamond", 17 girl names); rival (type 3, **inferred** from Platinum's numbering): msg 88 ("Pearl") | boy msgs 44-61 (starts "Pearl"); girl 62-79 (starts "Pearl"); rival: msg 89 ("Diamond") | `.ifdef` offsets +0x00/+0x12/0x58 vs +0x2c/+0x3e/0x59, bytes confirmed in both arm9s (`s3_name_default.py`). Bank 376 also holds msgs 37-43 (Barry, Damion, Tyson, Markus, "Pearl", Lucas, Dawn) and 81-87 (Lewis, Clint, Ralph, Tommy, "Diamond", Lucas, Dawn): their user is not one of the three version sites (**UNVERIFIED**) |
| OPTIONS screen heading (ov60, bank 206) | game name | msg 1 "POKéMON DIAMOND" | msg 2 "POKéMON PEARL" | `ReadMsgDataIntoString(gGameVersion - 9)` in ov60 (`overlay_60.s:1022-1029`) |
| Credits first heading (ov84, bank 493) | game name | msg 0 "Pokémon Diamond" | msg 1 "Pokémon Pearl" | table `ov84_021DA764` first short: 0 vs 1 (dump bytes at 0x021DA764) |
| Pal Park migration (ov83, bank 403, loaded with `0x193`) | "Saving data on Pokémon {Ruby/Sapphire/Emerald/FireRed/LeafGreen} and Pokémon Diamond/Pearl..." | msgs 18, 20, 22, 24, 26 | msgs 19, 21, 23, 25, 27 | table `ov83_0223B288` |
| Pal Park migration, end and confirm | "Six Pokémon safely migrated to the Pokémon Diamond/Pearl Game Card"; "Make Pokémon migrate to the Pokémon Diamond/Pearl Game Card?" | msgs 29 and 34 | msgs 30 and 35 | `mov r1,#0x1d/#0x1e` and `mov r0,#0x22/#0x23` in ov83 |
| Battle Frontier friend record (arm9 `unk_0202A1E0.c:400`, bank 17) | which game the record's author played | msg 22 "DIAMOND" (stored value 0) | msg 23 "PEARL" (stored 1) | index `22 + stored bit`; this is the author's game, not the running one. Who writes the bit: **UNVERIFIED** |

#### 3.6.3 Text that only names a game or is not reachable (identical in both ROMs, no version choice)

| Bank:msg | Text | Note |
|---|---|---|
| 298:110-113, 310:44-45 | "Diamond", "Pearl", "Emerald", "Sapphire" in a debug "Create Pokémon" menu and a debug name list | debug leftovers; not picked by a version test (**UNVERIFIED** whether reachable) |
| 315:10-11, 315:18 | "...the launch of Pokémon Diamond and Pokémon Pearl!", "end of the demo version" | trial-version leftovers; the same text in both |
| 167:16 | "The Diamond Dust Girl!" (Snowpoint Gym sign) | a joke on Candice, not the game |
| 190:3, 404:27 | "Adamant" (a nature) | not the Orb |
| 343-347:88-89 | Pearl, Big Pearl (items) | items, not the game |
| 343-347:135-136 | Adamant Orb, Lustrous Orb (names, descriptions, plurals) | the same in both; only the item ball differs (3.2) |
| 362/363:483-484 | DIALGA, PALKIA (species names) | same in both |
| 616:483 vs 615:483 | Dialga's Pokédex entry | covered by 3.6.1 |

### 3.7 PearlB2 today: what is already switchable and what is hard-coded Pearl

| Item | State | File:line |
|---|---|---|
| GetGameVersion in translated scripts | **Hard-coded Pearl**: always `WorkSetConst var, 11`. Because the translator keeps both branches and tests the value at run time, changing 11 to `10 if version.DIAMOND else 11` makes every script check in 3.1 and 3.3 work for Diamond with no other script change | `b2tools/pearl_story.py:3067-3069` |
| Spear Pillar ground model | **Hard-coded to Diamond's layout in the Pearl build**: `pearl_matrix` 22 (chunks 352-355). Pearl's real matrix is 23 (chunks 356-359). Diamond needs 22, Pearl needs 23 | `data/sinnoh_world.json:2411` (zone 220); `rooms.chunks` holds only 352-355. `notes/PLAN.md:153-154` already says matrix 22 is Diamond's |
| Dialga's overworld figure | Entry exists with Black 2's code 4632, never drawn from Pearl's frames; only Palkia, Uxie, Mesprit, Azelf are built | `data/pearl_sprite_map.json:2222-2234` (154) and `:2235-2247` (155); `b2tools/patches/pearl_npc_sprites.py:118-119` (`POKEMON` lacks Dialga) |
| Orb item balls | Follow from the 3.1 check; flags 0x3FF/0x401 are registered as b2 1137/1139 | `data/pearl_story_ids.json` (`0x03FF`, `0x0401`) |
| The Orb "collected" record (`Unk02A2`) | translated to nothing in both games | `b2tools/pearl_story.py:1520-1524` |
| Spear Pillar summoning 3D scene (camera, lights) | PearlB2 plays only "white flashes"; the per-version constants in 3.2 are not used, so no switch needed unless the scene is ported | `b2tools/pearl_story.py:3826-3831` |
| Celestic elder's book | Translated with both branches (Dialga/Palkia pictures are stubs, "not translated yet"). **The note is wrong**: it says the elder shows Palkia's picture; in Pearl she shows Dialga (Palkia is Diamond's) | `notes/STORY_HANDOFFS.md:180`; `work/pearl/b2_scripts/1017_celestic_cynthia_grandparents_house.s:48-72` |
| Pokédex entries | Already switchable: bank 615 for Diamond, 616 for Pearl | `b2tools/patches/sinnoh_pokedex.py:113` |
| Credits heading | Already switchable (line 0 Diamond, 1 Pearl) | `b2tools/pearl_credits.py:41` |
| Pokédex area data (zukan_enc) in the town map | Already switchable | `b2tools/patches/town_map.py:195` |
| Rival's default name | One fixed default, Barry (Diamond's first name). Pearl's own list is Clint, Ralph, Lewis, Tommy; PearlB2 does not offer either list | `data/text_overrides/pearl_intro.json:21` ("GameStart_Text_Hugh"), `b2tools/patches/pearl_intro.py:2,17,32` |
| Diamond-only zones | Guarded | `b2tools/allocate_sinnoh.py:503` |

### 3.8 UNVERIFIED and inferred

| Item | Why |
|---|---|
| Object 5's graphics id 102 = variable 0x4021 | inferred from pokeplatinum's `OBJ_EVENT_GFX_VAR_n` order (101 + n) and from Spear Pillar setting 0x4020 for the partner and 0x4021 for the legend; the DP object-graphics code was not read |
| ov06 constants belong to the summoning scene | the call chain `SpearPillarSequence` -> stage table 0x0224F174 is read from the decomp; the scene was not run |
| Naming type 3 = the rival | taken from Platinum's `NAMING_SCREEN_TYPE_*` numbering; the caller was not traced |
| Who uses bank 376 msgs 37-43 and 81-87 | the three version sites are proven; these two ranges have no version test of their own |
| Who writes bank 17's stored version bit | the reader (`unk_0202A1E0.c:400`) is proven, the writer was not traced |
| Whether NPC trade code overwrites "Met game" | not traced |
| Debug banks 298 and 310 | assumed unreachable in retail |
| Whether the Celestic book page is deliberately the other legend | the dump says so; it is data, not a bug |
| The Spear Pillar scenes' exact triggers per state | read from the coordinate events and states; the scenes were not played |

### 3.9 Where the other findings of the script and text trace went

| Finding | Now in |
|---|---|
| Honey-tree species lists differ (overlay 5, `ov05_021FC644`) | 1.4, 2.2 E2 |
| Encounter-table NARC chosen in arm9 `sub_02034CB4` | 1.1, 2.2 E1 |
| Title and opening (overlay 63, four version tests) | 2.2 A1-A4, 4.4 |
| Code that writes or reads its own version | 2.2 I1-I5 |
| Overlay 18's version columns: **identified** as the Underground's digging-game draw weights | 2.2 G |
| Pointer and branch-only differences in overlays 5, 7, 8, 11, 12, 17, 48, 62, 63, 64, 81 | 2.1 |

### 3.10 How to reproduce (all read-only, `python3 -I`, helper files in `work/diamond/`)

| Script | Output |
|---|---|
| `s3_verify.py` | identical NARCs |
| `s3_getver.py` | handler bytes of GetGameVersion in both arm9s |
| `s3_pairs.py` (output saved in `s3_pairs_out.txt`) | the 18 pair-selector calls of file 230 |
| `s3_text.py BANK [ID...]` | print any message of the text bank (decoded from the Pearl dump; equal in the Diamond dump) |
| `s3_scan_text.py`, `s3_scan_text2.py` (output `s3_text_hits.txt`, `s3_text_hits.json`) | every message that names a game, Dialga/Palkia or an Orb |
| `s3_bank_pairs.py`, `s3_dex_banks.py`, `s3_dex_diff.py` (output `s3_dex_diff.json`) | the 615/616 Pokédex split |
| `s3_ov16.py` | the Pokédex bank switch in both ROMs |
| `s3_name_default.py`, `s3_matrix.py`, `s3_ov06_const.py`, `s3_roamer.py` | the naming defaults, the Spear Pillar matrix swap, the summoning-scene constants, the honey tables |


---

## 4. Trainers, items, text, pictures, the ROM's face

**The rule for this section.** 338 of the 360 files in each ROM's NitroFS are byte-identical (the 22 others are: the personal table, which has two names, the banner, the overlay table, arm9 and 18 overlays). So anything not named in section 2 or 3 is **shared**. Where a picture or text exists "for both versions" it exists in both ROMs and the code picks.

### 4.1 Pokémon data

| What | Diamond | Pearl | Evidence |
|---|---|---|---|
| Held items of 6 species (`personal.narc`, bytes 12-15 of members 125, 126, 239, 240, 466, 467; item 1 is the common slot, 50 % when met in the wild; item 2 the rare slot, 5 %) | Electabuzz, Elekid, Electivire: **Electirizer 50 %**. Magmar, Magby, Magmortar: **Magmarizer 5 %** | Electabuzz, Elekid, Electivire: Electirizer 5 %. Magmar, Magby, Magmortar: **Magmarizer 50 %** | dump: `personal_diff.py`. The two files differ in exactly these 24 bytes. Odds: decomp `pokemon.c:78, 3160-3185` |
| Every other field of all 501 members (stats, types, abilities, TM/HM bits, egg groups, ...) | same | same | dump (the other 495 members and all other bytes are equal) |
| Learnsets (`wotbl.narc`), evolutions (`evo.narc`), growth, moves (`waza_tbl.narc`), Pokémon pictures, cries | same | same | dump (identical files) |

### 4.2 Trainers

All trainer data is identical: `poketool/trainer/trdata.narc` (850 trainers), `trpoke.narc`, the trainer names (text bank 559), their pictures and classes. No trainer has a version check; the Gym Leaders, the Elite Four, Cynthia and the rivals are the same in both games. (No script and no code site of section 2 tests the version for a battle.)

### 4.3 Items, shops, TMs, moves

| What | State |
|---|---|
| Item data (`itemtool/itemdata/item_data.narc`), icons, descriptions, prices | identical. The **Adamant Orb (135) and Lustrous Orb (136)** exist in both games with the same names, descriptions and effect (the item table is the same file). Which one lies on the Spear Pillar floor differs (3.2). |
| Shops, Poké Marts, the Jubilife and Veilstone department stores, the Game Corner | identical (the lists are in arm9 and scripts, with no differing bytes) |
| TMs, HMs, move tutors, move data | identical |
| Plates (Underground) | the same 16 plates exist; their chances are equal (2.2 G) |

### 4.4 Title screen, opening movie and pictures (dump)

| Picture | File and member | Both ROMs hold | Diamond shows | Pearl shows |
|---|---|---|---|---|
| Upper-screen logo: "Pokémon Diamond Version" / "Pokémon Pearl Version" (the Pokémon logo in yellow with a white version name) | `demo/title/titledemo.narc` (NARC 48): graphics members 1 / 3 with palettes 2 / 4 and screen member 0 | both | member 1 + 2 | member 3 + 4 |
| Upper-screen background colour | the same NARC, palettes 9 / 10 and 13 / 14 | both | 9 and 13: white fading to blue-grey (`#eeeef6`, `#dedee6`, ... `#4a5283`) | 10 and 14: white fading to pink-mauve (`#f6eef6`, `#e6dee6`, ... `#62527b`) |
| Lower-screen legend, 3D model and texture animation | same NARC, models 5 (Palkia, 65,584 B) and 6 (Dialga, 51,572 B), animations 18 and 19 | both | 6 and 19: Dialga | 5 and 18: Palkia |
| Camera and light of that model | overlay 63 `ov63_021D86E0`: two sets of numbers | both sets in the code | Dialga's | Palkia's |
| Opening movie (`demo/title/op_demo.narc`, 74 members) | NARC 128 | both | one background set (members 11, 10, 12) | another (8, 7, 9); **the two sets are byte-identical**, so the movie is the same in both games |
| Intro (Rowan, Lucas / Dawn, Barry pictures; `demo/intro/intro.narc`, 48 members) | NARC `demo/intro/intro` | identical file | the same pictures in both; background palettes `main_background_diamond.NCLR` (member 1) and `sub_background_diamond.NCLR` (member 24): blue-grey | `main_background_pearl.NCLR` (2) and `sub_background_pearl.NCLR` (25): pink (`graphics_rules.mk:154-161, 5443-5450`) |
| Spear Pillar ground | matrices 22 (chunks 352-355) and 23 (chunks 356-359) | both | 22 | 23 |
| Dialga and Palkia overworld figures at the Spear Pillar | field-object models 133 (`sppoke4`, Dialga) and 134 (`sppoke5`, Palkia) | both | Dialga | Palkia |
| `data/t3_fl_p.nsbtx` and its siblings `t3_fl_b`, `_r`, `_y` | the four flower textures of Floaroma Meadow (`ov05_021DBEF4.s:292-312`: "t3_fl_p.1" etc.): pink / blue / red / yellow flowers | identical, in both | used | used. **Not version data**: "p" means pink, not Pearl. |
| Pokédex, battle and menu pictures, Pokémon sprites and icons, trainer pictures, the map, the Pokétch, trainer card | many NARCs | identical | | no difference (no code site selects them) |

I rendered the two title logos from the dump (`title_render.py`; PNG not kept): member 1 with palette 2 and screen 0 reads "Pokémon Diamond Version" and member 3 with palette 4 "Pokémon Pearl Version".

### 4.5 Text

| What | State |
|---|---|
| All 624 text banks (30,211 messages) | identical in both ROMs; Diamond and Pearl differ only in which messages the code or script picks |
| **Banks 615 and 616: the Pokédex entries (494 messages each, the message number is the National Dex number)** | the only pair of banks that is a version split. Diamond uses 615, Pearl 616 (E4). **156 entries differ:** 72 below No. 387, all 75 Sinnoh species 387-461, 9 above. Full list in 3.6.1. |
| Messages picked by a script (22, plus a species name) | 3.1-3.4 |
| Messages picked by code (rival list, default names, options, credits, Pal Park) | 3.6.2 and 2.2 |
| Messages that name the other game but are not picked by a version test | 3.6.3 |
| The Underground treasure names (bank 569), item names | identical |

### 4.6 The ROM's face: header, banner, DS menu icon

| What | Diamond (ADAE) | Pearl (APAE) | Evidence |
|---|---|---|---|
| Header title (0x00, 12 bytes) | `POKEMON D` | `POKEMON P` | dump |
| Game code (0x0C) | `ADAE` | `APAE` | dump |
| Maker code, revision, size | `01`, 5, 64 MiB | same | dump |
| Banner text (all six language slots hold the English text) | "Pokémon Diamond" / "Nintendo" | "Pokémon Pearl" / "Nintendo" | dump: `hdr_ovt_banner.py` |
| Banner icon | the Poké Ball is blue (palette entries 1-5: `#004a94`, `#105aac`, `#2073c5`, `#3194de`, `#5abdff`); the tiles are the same | pink (`#de4a94`, `#e66aa4`, `#ee8bbd`, `#f6a4d5`, `#ffcdee`) | dump (`graphics/icon.png` vs `icon_pearl.png` in the decomp) |
| Banner CRC-16 | 0x048B | 0x48E0 | dump |
| Secure-area CRC, header CRC | 0x5931, 0xCA37 | 0x014C, 0xA80C | dump |

**Where PearlB2 stands on each:** `rom_identity.py` already writes the banner, the header and the icon for the build's version (section 5).

---


## 5. What PearlB2 must switch for Diamond

Audited against the tree at commit `dea48a8` (2026-11-01), read-only. Every file:line below was read, not guessed.
Evidence tags: **[dump]** proven from the two dumps, **[decomp]** read in external/pokediamond, **[tree]** read in our
files, **UNVERIFIED** could not be settled (the reason is given).

Status words used in the tables:

| Word | Meaning |
|---|---|
| SWITCHABLE | already asks `b2tools/version.py`; nothing to do but test |
| HAS BD/DIAMOND SIDE | the data for Diamond is in the tree, but nothing selects it from the build version |
| HARD-CODED PEARL | Pearl is baked in; Diamond needs a change |
| HARMLESS | reads Pearl's dump, but the thing it reads is byte-identical in the Diamond dump, so nothing to do |
| SILENT WRONG | a Diamond build would not stop; it would quietly produce Pearl's (or a half) result |

### 5.0 The short list (most dangerous first)

| # | What | Where | Status |
|---|---|---|---|
| 1 | `PEARL_VERSION=diamond` makes the Underground ship **Shining Pearl's** Pokémon lists: the list version is the data key `"version": "sp"`, not the build version | `data/underground.json:3`, read at `b2tools/ug_data.py:146`, `b2tools/patches/underground.py:129`, `b2tools/underground_check.py:190` | SILENT WRONG |
| 2 | `PEARL_VERSION=diamond` makes Ramanas Park ship **7 rooms** (the 'both' rooms only: no Kanto, Squall, Johto or Rainbow), and `PEARL_VERSION=bd` (what the notes say) is **refused** by version.py | `b2tools/ramanas.py:61`, `b2tools/version.py:15-17`, `notes/RAMANAS_PARK.md:51`, `notes/RESUME.md:134` [tested: `PEARL_VERSION=diamond ramanas.py show` lists 7 rooms; `PEARL_VERSION=bd` stops with "expected one of pearl, diamond"] | SILENT WRONG |
| 3 | The converted story scripts have the game version baked in as the number 11 (Pearl). 6 version checks in the dump's scripts, 8 in our converted scripts | `b2tools/pearl_story.py:3067-3069`; sites in 5.4 | HARD-CODED PEARL |
| 4 | The wild-Pokémon extractor refuses a Diamond dump and always reads `p_enc_data` | `b2tools/gen4_extract.py:134-137, 153`; `work/diamond/encounters/` does not exist | HARD-CODED PEARL |
| 5 | Honey-tree Pokémon groups: Pearl's members 5, 6, 7 of `encdata_ex`; Diamond's are 2, 3, 4 [dump: the ov05 table at 0x021FC644 reads 5,6,7 in Pearl and 2,3,4 in Diamond] | `b2tools/patches/wild.py:31` | HARD-CODED PEARL |
| 6 | Swarm species are read from `work/pearl/encounters` (Pearl's), not the version's | `b2tools/patches/wild.py:75, 90` | HARD-CODED PEARL |
| 7 | Spear Pillar is built from matrix 22. pokediamond swaps it to matrix 23 **in Pearl** at run time (`arm9/src/map_header.c:668`); the header table is the same in both dumps [dump: 559 headers identical]. So today's **Pearl** build uses the Diamond Spear Pillar layout, and Diamond would be right by accident | `data/sinnoh_world.json:2411` (`"pearl_matrix": 22`, zone 220) and `:4438` (`rooms.matrices["22"]`, nothing for 23); `b2tools/allocate_sinnoh.py:321` (`mid = z['matrix']`, the raw header value) | HARD-CODED (a probable bug in the Pearl build too; UNVERIFIED on screen) |
| 8 | Dialga's overworld picture at Spear Pillar is Black 2's own; only Palkia gets Pearl's pixels | `b2tools/patches/pearl_npc_sprites.py:118` (`POKEMON` has Palkia, not Dialga) | HARD-CODED PEARL |
| 9 | The intro's suggested rival name is "Barry". pokediamond offers Barry/Damion/Tyson/Markus in **Diamond** and Clint/Ralph/Lewis/Tommy in **Pearl** [decomp: `ov59_Intro.c:772, 877, 2442`, lists at `:214-239`] | `data/text_overrides/pearl_intro.json:21` (`GameStart_Text_Hugh`) | HARD-CODED (a Pearl-side question too) |
| 10 | The Diamond dump is not in `roms/`; `version.SOURCE_DUMP` points at `roms/diamond.nds`, which does not exist | `b2tools/version.py:28`; 11 files use `SOURCE_DUMP` (5.2) | MISSING FILE |
| 11 | The grottos' item list hard-codes the **Armor Fossil** (Pearl's version fossil); Diamond's is the **Skull Fossil** (2.2 G) | `data/underground.json:77-78` (`"a"` list, first entry of the second group), `notes/UNDERGROUND.md:156` | HARD-CODED PEARL |
| 12 | The Pal Park migration screen hard-codes **Pearl's** message lines: "Six Pokémon safely migrated to the Pokémon Pearl Game Card" (bank 403 line 30) and the saving line `TEXT_SAVING_FIRST + game + 1` (the Pearl one of each Diamond / Pearl pair). A Diamond build needs lines 29 and `18 + 2 × game` (2.2 H). `pal_park.py` ports all 46 lines and only renames the game, and `notes/PAL_PARK_MIGRATION.md:106-109` says "nothing here depends on the version", which is wrong for these lines | `external/pokebw2_pearlb2/src/pearlb2/palpark/migrate_app.c:72-73, 84-85, 911, 932`; `b2tools/patches/pal_park.py:44-48` | HARD-CODED PEARL |

### 5.1 `b2tools/version.py`: what it exports and who uses it

`PEARL_VERSION` is read once, at `version.py:15`; anything but `pearl` or `diamond` (or empty) stops the process
(`:16-17`). The module says nothing else may read it (`:6`); `ramanas.py:61` breaks that rule (see 5.7).

| Export (line) | Pearl / Diamond value | Used by | Status |
|---|---|---|---|
| `VERSIONS` (14) | `('pearl','diamond')` | nobody | unused |
| `VERSION` (15) | `pearl` / `diamond` | `patches/sinnoh_encounters.py:78`, `patches/town_map.py:80`, `patches/pearl_title.py:36` | SWITCHABLE |
| `DIAMOND` (18) | bool | `allocate_sinnoh.py:503`, `patches/sinnoh_pokedex.py:113`, `patches/town_map.py:195`, `pearl_credits.py:41` | SWITCHABLE |
| `NAME` (20) | `Pearl` / `Diamond` | `rom_identity.py:90` | SWITCHABLE |
| `TITLE` (23) | `Lustrous Pearl` / `Adamant Diamond` | `rom_identity.py:28, 59, 90` | SWITCHABLE |
| `PUBLIC_NAME` (24) | `Pokémon Lustrous Pearl` / `Pokémon Adamant Diamond` | `pearl_credits.py:58`, `rom_identity.py:10` (doc) | SWITCHABLE |
| `RELEASE_STEM` (25) | `Pokemon_Lustrous_Pearl` / `Pokemon_Adamant_Diamond` | **nobody** (release_vNN.sh hard-codes `Pokemon_Pearl_NDS_v$V`) | unused |
| `HEADER_TITLE` (26) | `POKEMON LP` / `POKEMON AD` | `rom_identity.py:76, 77, 118` | SWITCHABLE |
| `SOURCE_GAME_CODE` (27) | `APAE` / `ADAE` | **nobody** (`gen4_extract.py:137` hard-codes `APAE`) | unused |
| `SOURCE_DUMP` (28) | `roms/pearl.nds` / `roms/diamond.nds` | 11 files (5.2) | SWITCHABLE, but `roms/diamond.nds` missing |
| `ENCOUNTER_NARC` (29-30) | `p_enc_data.narc` / `d_enc_data.narc` | **nobody** (`gen4_extract.py:153` hard-codes `p_enc_data`) | unused |
| `build_dir(default)` (33-39) | `work/rom` / `work/rom_diamond` | `build_rom.py:24` | SWITCHABLE, but an explicit `PEARL_BUILD_DIR` skips the `_diamond` suffix and the ROM is always named `pearl.nds` (5.9) |
| `game_names(text)` (42-45) | "Pokémon Pearl" -> "Pokémon Lustrous Pearl", "Pokémon Diamond" -> "Pokémon Adamant Diamond" | `pearl_credits.py:57`, `patches/pal_park.py:48` | SWITCHABLE for the name; the choice of Pal Park lines is hard-coded (5.0 row 12) |

Missing from version.py, needed for Diamond: the game-version number (pokediamond `VERSION_DIAMOND` 10,
`VERSION_PEARL` 11; `config.h:9-10`), a map of the build version to the BDSP list key (`pearl`->`sp`,
`diamond`->`bd`), and the ROM file name (`pearl.nds`/`diamond.nds`).

### 5.2 Every user of `version.py` (all import forms, scanned with `work/diamond/s5_scan2.py`)

| File | Line(s) | Uses | Status |
|---|---|---|---|
| `b2tools/build_rom.py` | 20, 24 | `build_dir` | SWITCHABLE |
| `b2tools/allocate_sinnoh.py` | 503 | `DIAMOND` (lets zones 661-662 be allocated) | SWITCHABLE |
| `b2tools/pearl_credits.py` | 40-41, 57-58 | `DIAMOND`, `game_names`, `PUBLIC_NAME` | SWITCHABLE |
| `b2tools/pearl_trainer_pics.py` | 37, 97, 138 | `SOURCE_DUMP` | SWITCHABLE (needs the file) |
| `b2tools/rom_identity.py` | 24, 28, 36, 59, 76-77, 90, 118 | `TITLE`, `HEADER_TITLE`, `NAME`, `SOURCE_DUMP` | SWITCHABLE (needs the file) |
| `b2tools/patches/pal_park.py` | 44, 48 | `game_names` | SWITCHABLE |
| `b2tools/patches/pearl_amity_sprites.py` | 45, 48 | `SOURCE_DUMP` | SWITCHABLE |
| `b2tools/patches/pearl_intro_art.py` | 92, 94 | `SOURCE_DUMP` | SWITCHABLE |
| `b2tools/patches/pearl_npc_sprites.py` | 280, 283 | `SOURCE_DUMP` | SWITCHABLE |
| `b2tools/patches/pearl_partner_backs.py` | 97, 99 | `SOURCE_DUMP` | SWITCHABLE |
| `b2tools/patches/pearl_player_sprites.py` | 56, 58, 325, 327 | `SOURCE_DUMP` | SWITCHABLE |
| `b2tools/patches/pearl_title.py` | 26, 36, 103 | `VERSION`, `SOURCE_DUMP` | SWITCHABLE |
| `b2tools/patches/sinnoh_dex.py` | 31, 44 | `SOURCE_DUMP` (reads `poketool/shinzukan.narc`, identical in both) | SWITCHABLE |
| `b2tools/patches/sinnoh_encounters.py` | 71, 78 | `VERSION` (reads `work/<version>/`) | SWITCHABLE, but the producer is not (row 4 above) |
| `b2tools/patches/sinnoh_pokedex.py` | 113 | `DIAMOND` (entry bank 615 Diamond / 616 Pearl) | SWITCHABLE |
| `b2tools/patches/town_map.py` | 72, 80, 98, 195-196 | `VERSION`, `SOURCE_DUMP`, `DIAMOND` (`zukan_enc_diamond.narc` / `zukan_enc_pearl.narc`; members 0-3 are equal in both [dump]) | SWITCHABLE |
| `b2tools/patches/trainer_card.py` | 49, 88, 148 | `SOURCE_DUMP` | SWITCHABLE |
| `b2tools/title_art.py` | 33-44 | its **own** stand-in `_Version`, not version.py (Sapphire's values; only `DATA = data/title` matters) | HARMLESS |

Count: 17 real PearlB2 importers of version.py, plus `title_art.py` with its stand-in.

**HoennB2 leftovers that import version.py and call functions it does not have** (they would fail with
`AttributeError` if run for Pearl; none is in the usual patch list [tree: notes/RESUME.md:181-186]): `check_exits.py:23`
(`overlay_file`, `door_alias`), `outdoor_check.py:165, 685, 1087` (`load_json`, `plan_path`, `EMERALD`),
`rooms_check.py:51`, `scene_walks.py:56`, `script_check.py:49` (`ASM_DEFINES`, `overlay`, `room_in_version`),
`patches/encounters.py:5`, `patches/fixed_weather.py:37`, `patches/text.py:8`, `patches/trainers.py:33`;
`patches/title.py` uses `title_art.version.TABLE['legendary']`, also Hoenn. 9 files import it; leave them alone or
delete them in a clean-up; they are not a Diamond blocker.

### 5.3 Hard-coded Pearl dump and `work/pearl` paths

The two dumps differ in only these places [dump, from `work/diamond/diff.json`]: `poketool/personal*/personal.narc`,
the code, the banner, the header. So a tool that reads **any other file** of `roms/pearl.nds` gets exactly what it
would get from the Diamond dump. That is why most hard-coded `roms/pearl.nds` reads are HARMLESS.

| Pattern | Count | Verdict |
|---|---|---|
| `roms/pearl.nds` read in `b2tools/` (42 files: `gen4_*.py`, `pearl_*.py`, `patches/{sinnoh_world, sinnoh_rooms, sinnoh_reskin, pearl_trainers, pal_park, poketch, wild, season_weather, ...}`, `allocate_sinnoh.py:169`, `ramanas.py:614`, `tm_audit.py:180`, `gen4_text.py:43` ...) | 42 | HARMLESS except the rows below |
| `work/pearl/...` read in `b2tools/` | 57 files | HARMLESS (maps, matrices, land, events, scripts, trainers, zone table are the same in both) except `encounters/` (rows below) |
| arm9 addresses written as `0x02xxxxxx` in the tools that read the dump's code | 18 tools checked with `work/diamond/s5_overlap.py` | none falls on or next to a hunk where the dumps differ [dump] |
| Tables found by content (`pearl_gimmicks.py:104-120` asserts one match; `pearl_veilstone_gym.py:23`) | 2 | HARMLESS: Diamond's overlay 6 is shifted, content search still finds them |

The ones that are **not** harmless:

| File:line | What it reads | Why Diamond differs | Change |
|---|---|---|---|
| `b2tools/gen4_extract.py:134-135` | default ROM `roms/pearl.nds`, output `work/pearl` | Diamond's encounters must land in `work/diamond/` | default to `version.SOURCE_DUMP`, output `work/<VERSION>` |
| `b2tools/gen4_extract.py:137` | `assert rom.code == 'APAE'` | stops on a Diamond dump (`ADAE`) | `assert rom.code == version.SOURCE_GAME_CODE` |
| `b2tools/gen4_extract.py:153` | `fielddata/encountdata/p_enc_data.narc` | Diamond reads `d_enc_data.narc`: 24 of its 183 files differ from p_enc_data [dump]; same 424-byte layout, and `read_encounters` parses all 183 Diamond files with no assertion [tested: `work/diamond/s5_enc_parse.py`] | use `version.ENCOUNTER_NARC` |
| `b2tools/tm_audit.py:180` | `poketool/personal_pearl/personal.narc` | the Diamond ROM has only `poketool/personal/personal.narc` [dump]; the 6 swapped members (125, 126, 239, 240, 466, 467) differ only in held-item slots, and our tools use this file only for TM/HM bits (`pearl_tms.py` via `tm_audit.pearl_personal`) | pick the path by version (either file gives the same TM bits; verified in the dumps: the 6 members differ only in bytes 12-15, the held-item slots, `personal_diff.py`) |
| `b2tools/patches/wild.py:75, 90` | `work/pearl/zones.json`, `work/pearl/encounters/NNN.json` (swarm species) | encounters are version data | `work/<version>` as `sinnoh_encounters.py:78` already does |
| `b2tools/encounters_check.py:5-6, 25` | checks the build against `work/pearl` | same | `work/<version>` |

Notes for the extractor: `sinnoh_encounters.py:276` also needs `work/<version>/zones.json` (identical to Pearl's [dump]), so
a Diamond run only needs `encounters/` and a copy of `zones.json`. `work/diamond/` already holds the analysis files
files; the extractor would add `encounters/`, `zones.json`, `matrices/`, `events/` there. Writing only
`encounters/` + `zones.json` keeps it small.

The Pokémon held items (Electirizer / Magmarizer swap) are **not imported by any tool in our tree**: no patch
writes held items into Black 2's personal data [tree: grep `held` in `b2tools/patches` finds only comments in
`fairy.py:445` and `trade_evos.py:3`]. `trade_evos.py:3` says the items will come "once the item-ball pass is in".
Whichever version's wild Electabuzz/Magmar line should hold the Electrizer/Magmarizer is therefore still open for
both versions; the data for it is `personal.narc` members 125, 126, 239, 240, 466, 467 of each dump.

### 5.4 Story scripts, text and sprites that branch on the game version

The dump's field scripts are identical in both ROMs [dump], and the game version is a script command
(`GetGameVersion`, 0x0246, `pokediamond arm9/src/scrcmd.c:3952`). Our converter turns it into a constant.

| Piece | File:line | What it does | Change |
|---|---|---|---|
| The converter | `b2tools/pearl_story.py:3067-3069` | `WorkSetConst <var>, 11  // GetGameVersion: Pearl` | emit `PEARLB2_GAME_VERSION` and define it per version in the assembler options at `b2tools/patches/scripts.py:22-28` (`-D BLACK2` is there); Pearl stays 11 so its ROM does not change |
| Raw sites in the dump (script file:line of the disassembly) | `work/pearl/scripts/0069.txt:354`, `0230.txt:41, 50, 142`, `0977.txt:190`, `1017.txt:40` | 6 version checks [dump] | |
| Converted sites in our tree (8: script 977 is shared by two zones, and Spear Pillar's 0x01E8 subroutine is copied into a warp continuation) | `src/field_scripts/1356_pearl_eterna.s:375`; `1502_pearl_mount_coronet_spear_pillar.s:87, 96, 189, 1413`; `1677_pearl_sandgem.s:953`; `1682_pearl_sandgem_rowans_lab.s:1149`; `1708_pearl_celestic_cynthia_grandparents_house.s:50` | see below | same macro |

What branches, from our converted scripts [tree]:

| Script | Branch on version 10 (Diamond) | Branch on 11 (Pearl) |
|---|---|---|
| Eterna `1356:375` (script 69, `P69_S18`) | system message 27 | system message 28 |
| Spear Pillar `1502:87-103` | dynamic sprite var 0x4021 = 4632 (Dialga) | = 4633 (Palkia) |
| Spear Pillar `1502:96-107` | sets `PFLAG_0401` (Lustrous Orb ball marked taken, Adamant Orb ball stays) | sets `PFLAG_03FF` (Adamant Orb ball marked taken, Lustrous Orb stays); flags `src/include/pearl.h:807, 809` |
| Spear Pillar `1502:189`, `:1413` | var 0x8004 = 0x8005 (first value) | = 0x8006 (second value) |
| Sandgem `1677:953` and Rowan's Lab `1682:1149` (script 977) | buffers species 483 (Dialga) | buffers species 484 (Palkia) |
| Cynthia's grandparents `1708:50` | shows Palkia (preview 484, book text 4) | shows Dialga (preview 483, book text 5): each version's grandmother reads out the *other* legendary |

Both versions' **text lines are already in our text files**: `src/text/script/0859_pearl_mount_coronet_spear_pillar.txt`
has Dialga's and Palkia's lines (e.g. `_Text_007`/`_008`, `_023`/`_024`, `_036`/`_037`), and
`1027_pearl_celestic_cynthia_grandparents_house.txt:5-6` has both books. No Dialga/Palkia text needs writing.

Other Pearl hard-codes in the story tooling [tree]:

| File:line | Item | Status |
|---|---|---|
| `b2tools/patches/pearl_npc_sprites.py:118-119` | `POKEMON = [('Palkia',155,134,'sppoke5'), ('Uxie',...), ...]`: Pearl's pixels for the story legendaries. Dialga is `('Dialga', 154, 133, 'sppoke4')` [dump: mmodel member 133 holds texture `sppoke4`, 134 `sppoke5`]. Without it Diamond's Spear Pillar shows Black 2's Dialga (code 4632) | HARD-CODED PEARL |
| `data/pearl_sprite_map.json` entries `154` (Dialga, SPRITE_SPPOKE4, code 4632) and `155` (Palkia, code 4633); `"count": 0`, `"zones": {}`; the note at `:2233` says "Pearl never takes" the Dialga branch | already mapped | HAS DIAMOND SIDE |
| `b2tools/pearl_story.py:3694-3700` (`StartLegendaryBattle`) | a plain wild battle; species comes from the script | SWITCHABLE |
| `b2tools/pearl_story.py:1522-1526` (`TrySetUnusedCollectedOrbFlag`) | nothing in Black 2 | HARMLESS |
| `data/battle_music.json:57` | wild music by species, lists Dialga and Palkia | SWITCHABLE |
| `b2tools/patches/test_team.py:28` | test-only party with both | HARMLESS |
| `data/pearl_text_edits.json`, `script_text_overrides.json`, `pearl_script_patches.json` | no Diamond/Palkia/Dialga text [tree: checked] | HARMLESS |
| `data/text_overrides/pearl_credits.json` | carries **both** "Pokémon Adamant Diamond" and "Pokémon Lustrous Pearl" lines; `pearl_credits.py:41` picks line 0 or 1 | SWITCHABLE |
| `b2tools/patches/pal_park.py:25, 46-48` | Pearl's bank 403 through `game_names` | SWITCHABLE for the name only; which lines the screen shows is hard-coded Pearl (5.0 row 12) |
| `data/text_overrides/pearl_intro.json:21` | `GameStart_Text_Hugh = "Barry"`. The intro in Black 2 has one suggested name; Pearl's real list is Clint, Ralph, Lewis, Tommy (bank 341 lines 41-44), Diamond's Barry, Damion, Tyson, Markus (lines 37-40) [decomp] | HARD-CODED; decide what each version suggests |
| intro backgrounds (`main_background_pearl.NCLR`, `sub_background_pearl.NCLR`, Diamond's `_diamond`) | not used: no tool of ours mentions them; our intro keeps Black 2's backgrounds | nothing to switch (UNVERIFIED whether you want Pearl-pink / Diamond-blue tints) |
| `op_demo.narc` (opening movie) | not used: Black 2's opening movie is skipped (`pearl_title.py:69`) | nothing to switch |
| `data/t3_fl_p.nsbtx` | the pink flower carpet texture, not "Pearl" (`pokediamond ov05_021DBEF4.s:292`); `pearl_chunk.py:29-35` only skips `t3_fl*` as ground | HARMLESS |

### 5.5 Wild Pokémon, honey trees, swarms, Pokédex

| Piece | File:line | Status |
|---|---|---|
| Encounter tables 135-317 from `work/<version>/encounters/NNN.json` | `patches/sinnoh_encounters.py:78, 167-168, 276-281` | SWITCHABLE once `work/diamond/encounters/` exists (row 4) |
| Poké Radar, dual-slot GBA, swarm fields in the 183 files | not installed in either version (`notes/ENCOUNTERS.md:45`, `notes/OPEN_CONTENT.md:67`) | nothing to switch; swarm species do ship through `wild.py` (below) |
| Honey groups | `patches/wild.py:31` `HONEY_MEMBERS = (5, 6, 7)` | HARD-CODED PEARL: Diamond (2, 3, 4) |
| Swarm species and zones | `patches/wild.py:75, 90` | HARD-CODED PEARL (reads `work/pearl`) |
| Feebas (members 0-1), Great Marsh daily Pokémon (members 9-10) | `patches/wild.py:30, 32` | **no difference** [dump]: the NARC is identical in both dumps and the only place where the choice of an `encdata_ex` member differs by version is the honey-tree table (2.2 E2); no differing code site touches Feebas or the Great Marsh lists |
| Pokédex habitat/area page | built from our wild tables (`patches/sinnoh_pokedex.py` reads "the built wild tables"; `src/code/dex_area.c`) | SWITCHABLE; `zukan_enc_*` members 0-3 (places) equal [dump]; 83 of 4954 members differ (the per-species area data), which no tool of ours reads |
| Pokédex entries | `patches/sinnoh_pokedex.py:113` bank 615 Diamond / 616 Pearl | SWITCHABLE |
| Sinnoh regional list, Pal Park's `ppark.narc`, `shinzukan.narc` | read from the dump (`sinnoh_dex.py:44`, `pal_park.py:28`) | HARMLESS (files identical) |
| Trade evolutions (Electirizer, Magmarizer) | `data/trade_evos.json:131-144` | same data both versions |

### 5.6 The title, the ROM header, the banner

| Piece | File:line | Pearl side | Diamond side | Status |
|---|---|---|---|---|
| Top-screen logo and crystal strip | `patches/pearl_title.py:87` | `data/title/logo.png`, `strip.png` | `data/title/diamond/logo.png`, `strip.png` (both written by `python3 title_lustrous.py use C`, `title_lustrous.py:455-462`; `data/title/CHOSEN` = `lustrous C`) | HAS DIAMOND SIDE, picked by `VERSION_TITLE['art']` (`pearl_title.py:35-37`) |
| Bottom-screen legendary: 3D model + texture animation from `demo/title/titledemo.narc` | `pearl_title.py:35-37, 103` | members 5 (`title_air`, Palkia) + 18 | members 6 (`title_iar`, Dialga) + 19 | SWITCHABLE (needs `roms/diamond.nds`; the file is identical in both dumps, so `roms/pearl.nds` would also do) |
| Title cry on Start | `pearl_title.py:63` | species 484 | species 483 | SWITCHABLE |
| Camera on the legendary | `pearl_title.py:44-45` (`170 20 40` looking at `0 20 0`) | tuned by eye for Palkia (2026-10-20) | **shared with Dialga, never looked at** (`pearl_title.py:33-34`; `title_lustrous.py:396-408`: "Dialga has never been rendered") | OPEN (UNVERIFIED: needs a Diamond title shot in an emulator; read-only task) |
| Logo colours, words | `title_lustrous.py:27-45` (`THEMES`, `WORDS`: `LUSTROUS PEARL` / `ADAMANT DIAMOND`) | pearl | diamond | HAS DIAMOND SIDE |
| Old Pearl-only logo drafts | `title_art.py:864-869` (`PEARL_DRAFTS`), `data/title/drafts/` | old Pearl drafts | none | obsolete, unused by the build |
| ROM header title | `version.py:26`, `rom_identity.py:76` | `POKEMON LP` | `POKEMON AD` | SWITCHABLE |
| Game code | `rom_identity.py:6, 119` | `IREO` kept (Black 2's code and its link rules read it) | `IREO` too | shared: a Pearl and a Diamond build have the same game code and link id (`patches/link.py`, GGID 0x4842) |
| DS menu banner text | `rom_identity.py:28, 59` | `Pokémon / Lustrous Pearl / Fan project` | `Pokémon / Adamant Diamond / Fan project` | SWITCHABLE |
| DS menu icon | `rom_identity.py:34-40` reads the version's dump | Pearl's Poké Ball on pink | Diamond's own icon (the banners differ in 101 bytes [dump]) | SWITCHABLE (needs `roms/diamond.nds`) |
| Scratch state shared between builds | `pearl_title.py:47, 110, 115` writes `work/world/pearl_title_files` | | | RISK: `work/world/` is not per version; two builds at once would overwrite each other's `pearl_title_files`, `music.json`, `fly.json`, `heights_*.json` (31 patches and tools use `work/world`). Build one at a time, or make `work/world` per version |

### 5.7 Ramanas Park (the "bd" data)

Data is complete for both; the selection is broken.

| Item | File:line | Status |
|---|---|---|
| Version key, default `"sp"` | `data/ramanas_park.json:3` | HAS BD SIDE; not tied to the build version |
| Room version tags: Discovery `:129` both; Kanto `:186` sp; **Johto `:247` bd**; Soul `:306` both; Distortion `:362` both; **Rainbow `:406` bd**; Squall `:442` sp; Oceanic `:478`, Tectonic `:526`, Stratospheric `:574`, Genome `:622` both | `data/ramanas_park.json` | HAS BD SIDE |
| Version-dependent prerequisites: Oceanic/Tectonic/Stratospheric/Genome require `kanto`+`soul` (sp) or `johto`+`soul` (bd); Rainbow requires `johto`+`soul`; Johto requires `discovery` | `data/ramanas_park.json:488-492, 536-540, 585-589, 632-636`; `ramanas.py:119-122` | HAS BD SIDE |
| Zones: sp rooms 652-660 (Kanto 653, Squall 656); bd uses Johto **661**, Rainbow **662** and leaves 653 and 656 unused | `data/ramanas_park.json` `rooms[*].zone`; reserved by `allocate_sinnoh.py:104-110`; asserted at `:503` | RESERVED, ready |
| Slates: 120-128 for the nine sp/both rooms, **Johto 131** (`data/ramanas_park.json:252`), **Rainbow 132** (`:411`), shards S 129 / L 130 | the C range already covers 120-132: `external/pokebw2/include/pearlb2.h:151-154` (`FIRST_ITEM 120`, `COUNT 13`) | RESERVED, ready; `ramanas_park.py:212` creates the item records for **every** version's slates |
| Flags: Raikou, Entei, Suicune, Ho-Oh caught = 1068-1071 | `b2tools/pearl_ids.py:118-127` (`NEW_FLAGS`), `src/include/pearl.h:1367-1370` | RESERVED, ready |
| The selector | `b2tools/ramanas.py:60-61`: `os.environ.get('PEARL_VERSION') or data['version']` | **BROKEN**: `diamond` matches no room tag (`:115-116`), so 'sp' and 'bd' rooms both drop out silently; `bd` is rejected by `version.py:16-17`. `notes/RAMANAS_PARK.md:51` and `ramanas.py:9-10` document `PEARL_VERSION=bd` |
| Callers | `patches/ramanas_park.py:115` (`ver = rp.version(d)`), `ramanas.py:127, 343, 830-835, 860` (`check()` tests both) | follow the selector |
| Per-room Pokémon, moves, BDSP movesets table | `ramanas.py rooms(ver)` -> `ramanas_itcm.c` table via `apply_code` | follows the selector |
| Fix | `version()` should return `{'pearl':'sp','diamond':'bd'}[version.VERSION]` and drop the env read; fix the two notes | |

Not verified: whether the Johto/Rainbow rooms' looks, music and pedestal sprites (Raikou 243, Entei 244, Suicune 245?, Ho-Oh 250
in the resolved output) have been looked at in game; the data has them, no build ever used them (the notes say "in the data,
not built", `notes/RAMANAS_PARK.md:49`). UNVERIFIED.

### 5.8 The Underground (the "bd" data)

| Item | File:line | Status |
|---|---|---|
| Source lists for both versions | `data/underground_sources/serebii_sp.json`, `serebii_bd.json`, `bulbapedia_hideaways.json`, `kaphotics_ugspecial.tsv`; read at `b2tools/underground_lists.py:81, 106-118` | HAS BD SIDE |
| Built data: 18 Hideaways, 809 entries: **638 in both, 90 Shining-Pearl-only, 81 Brilliant-Diamond-only**, no entry has a different stage in the two; 77 rare-spawn rows, **38 with different weights between versions** [tree: counted from `data/underground_pokemon.json`] | each entry carries `sp` and `bd` stage keys (null = not in that version) and each rare carries `sp`/`bd` weights | HAS BD SIDE |
| The selector `"version": "sp"` | `data/underground.json:3`; read at `b2tools/ug_data.py:146` (`version or data()['version']`), `b2tools/patches/underground.py:129-130` (grotto rare list), `b2tools/underground_check.py:190` | **HARD-CODED PEARL**: a Diamond build ships the `sp` lists. `underground_lists.py:10` says "patches/underground.py VERSION picks one", but no such constant exists |
| Grottos: "both versions the same" | `patches/underground.py:126` | shared |
| Zones 633-651, files 1900 (script) / 1300 (text) | `data/underground.json:5-6` | version-independent |
| Fix | `ug_data.data()['version']` should come from the build version (`pearl`->`sp`, `diamond`->`bd`); `underground_check.py` should test both | |

### 5.9 Reserved ids, build glue, docs

| Reservation | Where it is made | State |
|---|---|---|
| Zones 661-662 (Johto, Rainbow rooms) | `allocate_sinnoh.py:104-110` (`DIAMOND_ONLY`), assertion `:503` | ready |
| Zones 663-664 | Turnback Cave (2), not Diamond | n/a |
| Items 131, 132 (Johto, Rainbow slates) | `data/ramanas_park.json:252, 411`; C range `pearlb2.h:151-154` | ready |
| Flags 1068-1071 | `pearl_ids.py:118-127`, `pearl.h:1367-1370` | ready |
| Build output name | `build_rom.py:10, 234`: always `<dir>/pearl.nds` | HARD-CODED PEARL: name it `<version>.nds` |
| Build dir | `version.py:33-39`: `_diamond` suffix only when `PEARL_BUILD_DIR` is unset; the usual test command (`notes/RESUME.md:181`) sets it, so a Diamond build there would overwrite the Pearl test ROM | RISK |
| Release script | `b2tools/release_kit/release_vNN.sh:15-18` hard-codes `work/rom/pearl.nds` and `Pokemon_Pearl_NDS_v$V`; its build step is a placeholder (`:15`, "TODO(Pearl): the full patch list") | HARD-CODED PEARL |
| Test scripts | `b2tools/hwtest/title_tune.sh:10` (`work/rom_title/pearl.nds`), other `hwtest` scripts take the ROM path as an argument | test-only |
| How a Diamond build is invoked | there is no Makefile or patch-list file; the list is in the notes (`notes/RESUME.md:181-186`). It would be `PEARL_VERSION=diamond python3 b2tools/build_rom.py --clean <the same list>` | no glue yet |
| Docs that say something untrue today | `notes/RAMANAS_PARK.md:51`, `notes/RESUME.md:134` (`PEARL_VERSION=bd`); `ramanas.py:9-10`; `underground_lists.py:10` ("patches/underground.py VERSION") | fix with 5.7 / 5.8 |
| Dump check | the Diamond dump's SHA-1 is `a46233d8b79a69ea87aa295a0efad5237d02841e` = `external/pokediamond/pokediamond.us.sha1` [dump], and the Pearl dump's is `99083bf1...` = `pokepearl.us.sha1` | the decomp reproduces both dumps, so `.ifdef` sites are the full list of code differences |
| Disk | `roms/pearl.nds` is 64 MiB; `cp -c` of the Diamond dump into `roms/diamond.nds` costs no space on APFS (the volume has ~7 GB free) | |
| Git | `roms/`, `work/`, `external/`, `tools/` are git-ignored; only `b2tools/`, `data/`, `src/`, `notes/` change | |

### 5.10 Order of work

1. Put the Diamond dump at `roms/diamond.nds` (`cp -c`; SHA-1 above). Nothing else needs it before step 5.
2. `version.py`: add `GAME_VERSION` (11 / 10), the BDSP key (`sp` / `bd`) and the ROM file name; keep Pearl output unchanged.
3. Make `ramanas.py:60-61`, `ug_data.py:146`, `patches/underground.py:129` and `underground_check.py:190` use that key; fix the three notes that say `PEARL_VERSION=bd`. Test: `PEARL_VERSION=diamond python3 b2tools/ramanas.py show` must list nine rooms with Johto 661 and Rainbow 662.
4. `gen4_extract.py`: version-aware (ROM, code check, `ENCOUNTER_NARC`, output dir); write `work/diamond/encounters/` and `zones.json`. Then `wild.py:31, 75, 90` and `encounters_check.py:25` to `work/<version>` and `HONEY_MEMBERS` by version.
5. `pearl_story.py:3067-3069` to a macro, `scripts.py:22-28` defines it; regenerate the 5 script files (8 sites). Prove Pearl's ROM is byte-identical (SHA-1) before and after.
6. Spear Pillar: matrix 23 for Pearl, 22 for Diamond. Needs a second room-matrix entry (chunks 356-359; matrices 22 and 23 differ in their props [tree: `work/pearl/land/352-359.json`]) and a Pearl-side rebuild, so Pearl's SHA-1 will change on purpose; decide with the user.
7. `pearl_npc_sprites.py:118`: add `('Dialga', 154, 133, 'sppoke4')`.
8. `tm_audit.py:180`: path by version.
9. Rival's suggested name (`pearl_intro.json:21`): ask the user (Barry for Diamond, Clint for Pearl as the games have it, or Barry for both as today).
10. Build-glue: ROM named by version, `build_dir` honours the version also with `PEARL_BUILD_DIR`, release script and `RELEASE_STEM`.
11. Title: a Diamond title build, look at Dialga, tune the camera (`pearl_title.py:44-45`).
12. Then the content that only the dump diff shows (sections 1, 2 and 4 of this note): the Electirizer/Magmarizer held items (4.1), the Skull Fossil in the grotto items (row 11 of 5.0), the Pal Park lines (row 12), and the Diamond column of the Underground's digging weights if digging is ever built (2.2 G).

### 5.11 Unverified

- Whether Pearl's current Spear Pillar (matrix 22) looks different on screen from the Pearl game's (matrix 23): the data differ [tree], no one has compared the pictures.
- Dialga's title camera, and every Diamond-only picture: no emulator in this task.
- Whether `Johto`/`Rainbow` rooms work in game: never built.
- The ov59 rival-name lists come from the decomp, not read back from the dump.

Files made for this section (all under `work/diamond/`): `sec5_project.md`, `s5_scan2.py` (users of version.py),
`s5_overlap.py` (arm9 constants vs differing hunks), `s5_sppoke.py` (mmodel 133/134), `s5_encount.py` and
`s5_enc_parse.py` (d_enc_data vs p_enc_data), `s5_zukan.py` (zukan_enc members).

### 5.12 The code switches of section 2, one by one, against PearlB2

| Section 2 group | PearlB2 counterpart | State | What to do |
|---|---|---|---|
| A1-A2 title logo, model, texture animation | `b2tools/patches/pearl_title.py:35-37` (`VERSION_TITLE`: Diamond = `data/title/diamond`, model 6, animation 19), `title_lustrous.py` | HAS DIAMOND SIDE | needs `roms/diamond.nds` only for the model; the dump `titledemo.narc` is identical in both ROMs |
| A3 op_demo background | not used (Black 2's opening movie is skipped, `pearl_title.py:69`) | nothing | the two sets are byte-identical anyway |
| A4 title camera and light of the legend | `pearl_title.py:44-45` (tuned for Palkia; Dialga shares it) | OPEN | Diamond's own numbers are in the Diamond branch of `ov63_021D86E0`; they are in the DS game's units, so whether they carry to Black 2's title camera is **UNVERIFIED** |
| B1-B2 rival names | `data/text_overrides/pearl_intro.json:21` ("Barry") | HARD-CODED | choose: Barry (as today), or Diamond: Barry, Damion, Tyson, Markus / Pearl: Clint, Ralph, Lewis, Tommy |
| B3 intro background colours | not used (Black 2's intro keeps its backgrounds) | nothing | optional: Diamond blue-grey / Pearl pink tint |
| C1-C3 default names | none of our tools sets default names (Black 2's naming screen is used) | n/a | nothing, unless the user wants "Diamond" / "Pearl" as suggestions |
| D1 Options heading | Black 2's options screen has no game name | n/a | nothing |
| D2 credits heading | `b2tools/pearl_credits.py:41` | SWITCHABLE | done |
| D3 banner, icon, header | `b2tools/rom_identity.py` | SWITCHABLE | needs `roms/diamond.nds` for the icon |
| E1 wild tables | `gen4_extract.py:134-137, 153` | HARD-CODED PEARL | 5.3 |
| E2 honey trees | `patches/wild.py:31` | HARD-CODED PEARL | members 2, 3, 4 for Diamond |
| E3 Pokédex area geometry | `patches/town_map.py:195` | SWITCHABLE | members 0-3 are equal anyway |
| E4 Pokédex entry text | `patches/sinnoh_pokedex.py:113` | SWITCHABLE | done (bank 615 / 616) |
| E5 personal data / held items | `tm_audit.py:180`; no held items are written at all today | HARD-CODED PEARL | add the version's file and, when held items are built, 4.1's six rows |
| F1 `GetGameVersion` | `b2tools/pearl_story.py:3067-3069` | HARD-CODED PEARL | 5.4 |
| F2 Spear Pillar matrix | `data/sinnoh_world.json:2411` | HARD-CODED (22, which is Diamond's) | 5.0 row 7 |
| F3 summoning scene camera | not ported (flashes only) | nothing | only if the scene is ported |
| G Underground digging weights | not ported: PearlB2's Underground is the BDSP-style Grand Underground (`notes/UNDERGROUND.md`) | nothing | the version-specific part left is the Armor / Skull Fossil in the grotto items (5.0 row 11) |
| H Pal Park messages | `migrate_app.c:72-73, 84-85, 911, 932` | HARD-CODED PEARL | 5.0 row 12 |
| I1-I6 "Met game" and version stamps | Black 2 stamps its own version into Pokémon and records | n/a | nothing |
| J1-J7 | `rom_identity.py`, `version.py` | SWITCHABLE | header title, banner, icon |


---

## 6. Everything I could not settle, and how to reproduce

### 6.1 UNVERIFIED and inferred (all sections)

| Item | Why it is open |
|---|---|
| Slot positions of swarm / Radar / dual-slot in Diamond/Pearl, and the National Pokédex rule for dual slots (1.1) | Read from Platinum's `wild_encounters.c`; the DP file layout is the same and `notes/ENCOUNTERS.md` (written from DP's assembly) agrees, but I did not re-read DP's overlay 6 for it |
| Meaning of the ten Pokédex area categories (1.5) | Inferred from which species fall in which list; consistent with every one of the 83 differences |
| Overlay 18 is the Underground's digging game and its table holds draw weights (2.2 G) | The NARCs it loads (`ug_trap`, `ug_fossil`, `ug_parts`, `underg_radar`), the text bank 569 names and the weighted-draw loop are proven; the mapping of the entry's object number to a name and the sphere sizes are inferred; the flag tested by `sub_02025C38` was not traced |
| What the records of I3 / I4 and the GBA mask of H1 feed (Union Room, Wi-Fi, Global Terminal, Pal Park) | Function names in the decomp are placeholders (`sub_02066840`, `ov80_02234288`, the "SafariZone" save); I describe what the code copies, not the menu |
| The rival's default name is naming type 3 (C3) | Taken from Platinum's naming-screen numbering; the caller was not traced |
| The Spear Pillar scene constants (F3) belong to the summoning scene | The call chain `SpearPillarSequence` → stage table 0x0224F174 is read from the decomp; the scene was not run |
| Graphics id 102 at the Spear Pillar is the legendary figure (variable 0x4021) | Inferred from Platinum's numbering and PearlB2's own map |
| Who writes the Frontier record's version bit (I6); whether NPC-trade code overwrites "Met game"; debug banks 298 and 310 | Not traced; likely not reachable in the retail game |
| Everything on screen | I did not run any ROM or emulator (the task was read-only). The title logo is the one picture I rendered from the dump |
| How Dialga looks under PearlB2's title camera | Needs a Diamond build and an emulator |
| Whether the Johto / Rainbow Ramanas rooms work | Never built |
| The exact sizes of the ov63 camera sets (A4) | Not decoded into units; PearlB2 would have to tune a Dialga camera by eye as it did for Palkia |

### 6.2 Files that reproduce this (all in `work/diamond/`, run with `python3 -I`)

| File | What it shows |
|---|---|
| `b2tools/compare_dumps.py`, output `diff.json` | 338 of 360 files identical; the differing ones |
| `rom_blocks.py` | every differing ROM byte mapped to its owner (2.1) |
| `code_diff.py`, `small_hunks.py`, `small_classify.py`, `sync_diff.py` (`sync_arm9.json`, `sync_ov06.json`), `arm9_classify.py`, `align2.py` | word-level diffs of arm9 and each overlay, classified as pointer, branch, or real |
| `hdr_diff.py`, `hdr_ovt_banner.py`, `ovl_table.py` | map headers equal; header, overlay table and banner diffs |
| `enc_diff.py`, `enc_diff2.py`, `enc_report.py` (`enc_diff_rows.json`, `enc_species_sets.json`), `gen_part1b.py` (`part1_table.md`) | 1.1-1.3 |
| `zk_dump.py`, `zk_dump2.py`, `zk_diff.py` (`zk_diff.json`), `gen_part1c.py` | 1.5 |
| `personal_diff.py` | 4.1 |
| `intro_pal.py`, `pal_look.py`, `titledemo_members.py`, `title_render.py` | 4.4, 4.6 |
| `s3_*.py` (the script and text trace) and `s5_*.py` (the audit of our tree), with their outputs | sections 3 and 5 |
| `assemble.py` with `part_head.md`, `part1.md`, `part2.md`, `part4.md`, `part6.md`, `sec3_scripts.md`, `sec5_project.md` | the pieces this note is assembled from (`python3 -I assemble.py` rewrites `notes/DIAMOND.md`) |

### 6.3 Things this note does not claim

- No claim about Platinum, Heart Gold or any other game.
- No claim about behaviour that depends on the Wi-Fi Connection, which no longer exists.
- The "plain words" of the code sites are my reading of the decomp's assembly. Where a decomp function has a placeholder name I say so instead of guessing the feature.

---

## 7. What was built (2026-11-01, offline: no ROM built, no emulator run)

`python3 b2tools/version_check.py` proves it: three runs of what the patches and generators make (this tree as Pearl, as Diamond, the base commit as Pearl), 1,147 digests. Pearl against the base: only the four Spear Pillar chunks and their heights move. Diamond against Pearl: only what the table below says; anything else stops the check.

    PEARL_VERSION=diamond python3 b2tools/gen4_extract.py      # once per tree: work/diamond (the build stops and says so otherwise)
    cd b2tools && PEARL_VERSION=diamond PEARL_BUILD_DIR=<dir> python3 build_rom.py --clean <the list in RESUME.md Commands>   # -> <dir>_diamond/diamond.nds

| Difference (section) | Where now | Note |
|---|---|---|
| Version plumbing (5.1) | `version.py`: GAME_VERSION, BDSP, ROM_NAME, WORK, PERSONAL_NARC, MET_GAME, HELD_ITEMS_FROM_DUMP, land_id, sources, check_inputs | `build_rom` stops at once without the version's dump or tables. Any PEARL_BUILD_DIR gets `_diamond` |
| Underground, Ramanas Park (5.7, 5.8) | `version.BDSP`; the data's `version` keys are gone | Ramanas's generated script and text have a Diamond copy in `src/*/diamond/`; `patches/ramanas_park.py` stops on the wrong one |
| Scripts (3, 5.4) | `PEARLB2_GAME_VERSION`, by `patches/scripts.py`; 8 sites in 5 files | Dialga, Adamant Orb, statue, book, 22 lines, Sandgem hint: all were already in the scripts as branches |
| Summoning scene camera, lights (F3) | nothing to switch | our scene plays flashes, not that scene (`pl_SpearPillarSequence`) |
| Spear Pillar's map (F2) | `version.land_id`, at every reader of land files | heights differ on 20 of 4,096 tiles, none under an event, so no script changes; materials the same, so no texture set changes. Diamond's own map has two people on pillar tiles, (29, 35) and (29, 36), and so does the real game: the events are shared |
| Wild tables (1) | `gen4_extract.py`, `patches/wild.py`, `encounters_check.py` | the dumps differ in 24 files; 17 differ here, the other 7 only in Radar and dual-slot species, which no build installs |
| Honey trees, swarms (1.4) | `patches/wild.py` | ov05 read in both dumps: (5, 6, 7) and (2, 3, 4). Swarms are the same species |
| Pokédex (1.5, 3.6.1) | entries by bank; area pages from the built tables | no change was needed |
| Held items (4.1) | `sinnoh_encounters.held_items`, from the version's dump | Diamond only (see DECISIONS). Black 2's Electabuzz and Magmar hold nothing |
| Digging weights, Skull Fossil (G) | `data/underground_digging.json` (`underground_digging.py`, read from both dumps) | digging is not built, so nothing reads it yet |
| Grotto fossil (5.0 row 11) | `data/underground.json` `version_fossil` | |
| Pal Park (H) | `patches/pal_park.py` VERSION_LINES | Diamond's words on the lines the C shows; no C changed. H1's GBA bit check was not ported in either version |
| Intro, names, Options (B, C, D1) | nothing to switch | see DECISIONS |
| Credits (D2) | already switched | |
| Met game (I1) | `rom_identity.stamp_met_game`, by `patches/pearl_title.py` | in place, asserted; `game_version` itself stays 23 for Black 2's demos and mail. See DECISIONS for the ability rule |
| Other stamps (I2-I4) | unchanged | link and Wi-Fi records say Black 2 in both versions |
| Dialga's overworld picture | `patches/pearl_npc_sprites.py`, Diamond only | the dump's two frames, pixel for pixel; 64 x 64 and the same lowest row (62) as Black 2's sheet |
| Title (A, J) | `data/title/diamond/`, `title_lustrous.py`, `pearl_title.py` | its own camera (TITLE.md). Header `POKEMON AD`, game code IREO, Diamond's icon |
| Release (5.9) | `build_rom.py`, `release_kit/release_vNN.sh`, `hwtest/title_tune.sh` | |

Checked here that section 5 had right: the matrix swap, the 24 files, the honey tables, the digging table, the Skull and Armor weights, the zones file (equal in both dumps). Still only inferred: everything on screen.

