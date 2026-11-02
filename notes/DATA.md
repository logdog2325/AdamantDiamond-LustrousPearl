# Phase 1: Pearl's data (started 2026-10-18)

Source order (user, 2026-10-18): **pokediamond first; pokeplatinum only for what pokediamond leaves out**, recorded
per item below.

## Readers
| Tool | Reads | Layout from |
|---|---|---|
| `b2tools/gen4rom.py` | the dump's file system and NARCs | DS formats |
| `b2tools/gen4_extract.py` | zone table, 245 matrices, 512 event files, 183 Pearl encounter files -> `work/pearl/` JSON | zone table: pokediamond `include/map_header.h` (the table sits in arm9 at ROM 0xf2dbc, found by Jubilife's entry); NPCs: pokediamond `struct ObjectEvent` (`include/map_object.h`); warps, signs, triggers and encounter files: pokeplatinum `tools/jsoncnv/event.py` / `encounter.py` (pokediamond has no layout for them). Names: pokediamond constants |
| `b2tools/gen4_script.py` | all 1,051 script files (531 scripts, 519 level scripts, 1 empty) -> `work/pearl/scripts/NNNN.txt`; command table `b2tools/data/gen4_script_cmds.json` (`--table` rebuilds it) | pokediamond only: 687 commands from its C, 25 from its asm, 9 by hand from its handlers (argument count depends on a value: GetSetStrength/Flash/Defog, UnionGroup, Unk0235/0237/023E/027C, Unk0289); **0 from Platinum** |
| `b2tools/gen4_land.py` | 578 map chunks -> `work/pearl/land/NNN.json` (collision, tile behaviour, placed buildings) + `.nsbmd` terrain model + raw `.bdhc` heights | pokediamond has none (gap): pokeplatinum `docs/maps/file_format_specifications.md`; section sizes checked per chunk |
| `b2tools/gen4_trainers.py` | 850 trainers (class, items, AI, parties with items/moves) -> `work/pearl/trainers.json` | pokediamond `trdata.json.txt` / `trpoke.json.txt` templates; **matches pokediamond's trdata.json for all 850** (class, species, levels) |
| `b2tools/tm_audit.py` | Pearl's TM/HM moves vs Black 2's | pokediamond `itemtool.c`, pokebw2 `pml_item.c` |

Checks passed:
- Scripts: every file decodes with no unknown opcode and no unexplained byte; 607 opcodes are used. 3,968 bytes in 106
  files are never reached (mostly the extra `End` after a `GoTo`, plus unused scripts and movements); they decode
  cleanly and are marked "unreferenced". Twinleaf (file 978, text bank 498) and Route 201 (file 392, bank 415) read
  correctly against pokediamond's text (`files/msgdata/msg/narc_NNNN.gmm` = msg NARC member NNNN).
- Script command sizes differ from Platinum at 14 used opcodes (4 real Diamond/Pearl differences, e.g. 0x125
  FirstBattle; 10 where Platinum's numbering shifts from 0x2C4): Platinum's numbers must never be used for Pearl.
- Every event and encounter file parses to its last byte (no leftovers, no short reads).
- Route 201: Starly/Bidoof Lv 2-3; Twinleaf's 4 doors lead to the player's, the rival's and the two other houses.
- Pearl vs Diamond tables: Pearl-only Glameow, Purugly, Misdreavus, Slowpoke, Spheal, Sealeo, Bagon, Pinsir, Stantler,
  Houndoom, Bonsly/Sudowoodo, Dustox/Cascoon; Diamond-only Stunky, Skuntank, Murkrow, Larvitar, Aron, Mime Jr.,
  Scyther, Seel, Kecleon... (the known exclusives), so the Pearl tables are read from the right file.

- Twinleaf (chunk 0): the collision grid shows the 4 houses, the square and the north/south exits; 4 house models
  and 4 others placed. 3,391 placed buildings across all chunks.

Findings:
- **Height data (BDHC) is a Diamond/Pearl-specific layout**: it does not match Platinum's documented BDHC (here the two
  games really differ), and pokediamond's loader is still assembly. Kept raw; heights for Black 2 are taken from the
  terrain models (HoennB2 built its heights itself). **Decoded 2026-10-25** (gen4_land.read_bdhc_dp, for the
  bridges): points and normals as VecFx32, plates as TRIANGLES (three point ids, a normal, fx32 d), a lookup grid;
  568 of Pearl's 578 chunks read (the 10 that don't are unused). It now gives the converter the second level under
  bridges (notes/WORLD.md "Bridges: two levels").
- **Pearl already gives the snowy north its own area**: Route 216, Route 217, Acuity Lakefront and Snowpoint use area
  14; Twinleaf and Route 201 use area 6. All are on matrix 0. That is exactly the split the seasons plan needs
  (PLAN.md section 4).
- In the overworld matrix the north sits at rows 6-12 (Route 216 at row 12); the nearest southern zones (Route 211,
  Celestic) are at row 16, with Mt. Coronet's cells between.

## TMs and HMs (by move)
`python3 b2tools/tm_audit.py` (full table). Of Pearl's 100:
- **73** teach the same move under the same number in Black 2.
- **2** have another number: HM07 Waterfall is Black 2's HM05; HM06 Rock Smash is Black 2's TM94.
- **25 have no Black 2 TM/HM**: TM01 Focus Punch, TM03 Water Pulse, TM09 Bullet Seed, TM19 Giga Drain, TM23 Iron Tail,
  TM34 Shock Wave, TM43 Secret Power, TM47 Steel Wing, TM48 Skill Swap, TM49 Snatch, TM51 Roost, TM55 Brine,
  TM58 Endure, TM59 Dragon Pulse, TM60 Drain Punch, TM62 Silver Wind, TM67 Recycle, TM72 Avalanche, TM76 Stealth Rock,
  TM78 Captivate, TM79 Dark Pulse, TM82 Sleep Talk, TM83 Natural Gift, **HM05 Defog**, **HM08 Rock Climb**.
- Defog and Rock Climb are field moves in Pearl (Defog clears fog, for example on northern Route 210; Rock Climb
  walls appear on several routes and in Mt. Coronet). Black 2 has neither. Which uses are required for the story is
  checked once the scripts and collision are read [to check]. Decision: START_HERE question 9.
- Every TM gift, TM item ball and Mart TM in Pearl's scripts gets mapped by move once the scripts are read.

## Still to do in Phase 1
- Scripts open points: command names are pokediamond's (`Unk002C` is Message), movement steps are raw numbers, and
  text is checked against pokediamond's English (same as Pearl's? check Pearl's own msg.narc). Next: list every
  TM/item gift and item ball from the scripts, mapped by move.
- Trainers: read and checked; next is the conversion to Black 2's trainer format (HoennB2 `patches/trainers.py`).
- Marts: pokediamond `arm9/src/scrcmd_mart.c` (partly unnamed symbols).
- Pokédex text and place names: pokediamond `.gmm` banks.
- Special encounters (Honey trees, Great Marsh, Trophy Garden, Feebas): pokediamond `files/arc/encdata_ex/` (binary);
  Platinum's `tools/jsoncnv/encdata_ex_*.py` give the layouts (gap in pokediamond).

## File numbers outside Pearl's ranges (a/0/5/6 scripts, a/0/0/3 text)
Pearl's zone files: scripts 1290-1849, text 676-1235 (pearl_story FIRST_SCRIPT_FILE / FIRST_TEXT_FILE, ranked over
all of Pearl's files). Black 2's globals rewritten by PearlB2 keep their numbers (1231-1289). Given by the lead:
| scripts | text | what |
|---|---|---|
| 1900 | 1300 | the Grand Underground, all 19 zones (notes/UNDERGROUND.md) |
| 1901 | 1301 | Pal Park / Ramanas Park |
| - | 1236 | field moves (the tms agent) |
| 1282 | 413 | Super Contests' reception (global scripts 10785-10794; Black 2's own there have no callers; notes/CONTESTS.md) |

## Black 2 save blocks PearlB2 reuses (registry)
A block of a Black 2 feature PearlB2 drops, taken whole or in part. Before taking one: list every reader of the block
in the decomp (its accessors, the block id, any whole-save copy), and none that can still run may touch the bytes
taken; old saves must still load (the block keeps its size; a magic number tells PearlB2's data from Black 2's).
| Block (save_control.h) | Black 2's feature | Bytes taken | PearlB2 use | Readers that still run |
|---|---|---|---|---|
| 0x46 SAVE_BLOCK_FUNFEST | Funfest missions (Entralink) | see notes/POKETCH.md | the Pokétch (DECISIONS 2026-10-26) | see notes/POKETCH.md |
| 0x47 SAVE_BLOCK_POKEWOOD (PokewoodSave, 0x3E4 B) | Pokéstar Studios (zones kept, no way in) | 0x28-0x3E3 (from `records` to the end: 956 B; the four flag lists and the slots, 0x00-0x27, stay Black 2's) | Pal Park's stock and Catching Show (PalParkStock, include/pearlb2/palpark.h: magic 'PPRK', six Black 2 boxed Pokémon and their show data) | the trainer card's stars (ov012 trcard_sys.c TrainerCard_CountStars: flag list 0, bytes 0x00-0x07 only). Everything else that reads the block is Pokéstar's own (ov023 event_pokewood.c, ov062 pokewood_system/setup/scrcmd_pokewood.c, ov136 gimmick_pokewood_poster.c, ov322-ov325 pkwd_*: only Pokéstar's zones and scripts start them) or Join Avenue's store script (ov012 scrcmd_join_avenue_store.c, the level points at 0x348: only Join Avenue's scripts). Checked 2026-10-26 against decomp pearlb2 bf2429b4c5 (every module is C but the Wi-Fi/JPEG libraries). Old saves: the bytes hold Pokéstar's initial records (score -9999), no magic: an empty stock |
| 0x2A SAVE_BLOCK_MUSICAL (MusicalSave, 0x2A4 B) | the Pokémon Musical (2026-11-01: replaced by Super Contests) | 0x1B0-0x1EB (60 B; the rest stays Black 2's, 0x1EC-0x200 the Poffin Case's last 3 slots, next row; 0x201-0x257 free: 87 B; the prop bits and counters from 0x258 stay) | ContestSave, include/pearlb2/contest_app.h: magic 'CNST', the Fashion Case (4 bits per Accessory, a bit per backdrop), the Master Ranks won | only the Musical's scripts wrote here. Still callable: the Battle Recorder's Musical tab reads the photo's date (ov271 br_core MusicalSave_HasShot, ov269: head of the block, untouched), ov065 and memory link read prop bits (+0x258 on, untouched). Old saves and new games: no magic, set up on first use |
| 0x3C SAVE_BLOCK_SYMBOL (AreaNPCSave, 0x850 B) | the Entree Forest's Pokémon (Entralink, gone with the C-Gear) | 0x000-0x847 (2,120 B; `checksum` and `seed` at 0x84C stay the forest's, `unk848`/`deepestArea` are not touched) | PearlB2WildSave, include/pearlb2/wild.h: magic 'WILD', Pearl's daily number, the swarm's switch, 21 honey trees (6 B each), 118 berry patches (12 B each): 1,548 B | none that can run. Every reader goes through symbol_save.c's functions: the Entree Forest's own script commands (ov012 scrcmd_entree_forest.c, symbol_map.c, symbol_save_field.c; ov033 entree_forest.c: only the forest's zones 280-288 and its gates run them, and no way leads there: zone flag 15 is 0 everywhere, the C-Gear is gone) and Game Sync's arrivals (ov199 gsync_state.c's SymbolSave_AddPokemon: its call now goes to PearlB2_Wild_NoForestAdd, it would have written into the block). No midnight or save-time code touches the block; Black 2 only saves, loads and CRCs it whole. Checked 2026-11-01 against decomp pearlb2 890422c107. Old saves and new games: the bytes are the forest's encrypted zeros, no magic: set up on first use (Pearl's new-game Berries, a new daily number) |
| 0x3C SAVE_BLOCK_SYMBOL, the tail | the same | 0x700-0x83E (319 B of the free 0x700-0x847; PearlB2WildSave ends at 0x612, the C checks both sizes at compile time) | PearlB2SecretBaseSave, include/pearlb2/secret_base.h: magic 'SBAS', the base's entrance, Flags, 15 placed goods, 16 boulders, PC 200 + Bag 40 goods (notes/SECRET_BASES.md) | none that can run: the row above, checked again 2026-11-01 against decomp pearlb2 f76647bc21. Old saves and new games: no magic, set up empty on first use |
| Four pieces, 100 slots of 7 B (the Poffin Case, 2026-11-01; decomp src/pearlb2/resident/poffin.c) | 0x3C +0x614-0x6FF: magic 'OPFF', then 33 slots (after PearlB2WildSave, ends 0x612; before Secret Bases, 0x700). DREAM_RADAR DreamRadarSave +9 (`padding09`, to 0xF0): 33. RESH_ZEK ReshZekSave's Pokémon area: 31. 0x2A SAVE_BLOCK_MUSICAL +0x1EC: 3 | 700 B | Poffin Case. Blocks keep their sizes; without the magic every piece is someone else's bytes and the Case reads empty | Dream Radar: ov332 and new_game use only seed, received and read flags, nobody reads the padding. Resh/Zek: only ov165 plist_demo (DNA Splicers: no Kyurem or Splicers in Sinnoh, unreachable). 0x3C and the Musical: as the rows around this one. City state in the Resh/Zek block stays |
