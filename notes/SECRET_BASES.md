# Pearl's Secret Bases (2026-11-01; played 2026-11-02)

Guide: HoennB2 notes/PEARL_LESSONS_SECRET_BASES.md. Sources: Pearl's dump, pokediamond; Platinum's `src/underground/` as the reading guide.
Choices and why: notes/DECISIONS.md 2026-11-01.

## What the player does
- **Digger Drill:** in the tunnels, Bag -> Explorer Kit -> Use opens DIGGER DRILL / GOODS / GO UP / CLOSE. Facing a wall (the tile and both tiles beside it solid, not a Hideaway's hole): Pearl's "used!", "Discovered a small cavern!", the hole shows, then make here / move here. NO closes the hole.
- **Moving:** a new base sends the placed goods back to the PC and makes new boulders, as Pearl's SecretBases_CreateBase.
- **The hole:** walk into it, answer, go in. **Out:** walk down from (15, 23) into (15, 24).
- **PC** (facing it from (15, 13) or (16, 13)): DECORATE (DECORATE, PUT AWAY, MOVE GOODS), STORE GOODS, RECEIVE GOODS, CHECK FLAGS, EXIT.
- **Goods:** Veilstone 4F (Pearl's two lists and prices), gifts (Hearthome, Battle Tower, the Underground Man: Pearl's scripts), eight traders in the tunnels (money). A on a TV, shelf, globe and so on says Pearl's record line.

## How it is built
| Part | Where |
|---|---|
| Hooks, rules, script ops | decomp `src/pearlb2/resident/secret_base.c`, `include/pearlb2/secret_base.h` (self-contained) |
| Same-size calls | `ov036/fieldmap.c` (LoadArea), `field_buildmodel.c` (LoadResBundle), `field_map_chunk_wb.c`, `_gc.c` (InstantiateProps), `underground_itcm.c` (the Kit's script), `resident/hideaway.c` (a visit), `gimmick_itcm.c` (row 64, terrain row), `resident/ext_cmd.c` (row 0xE0), `ov012/script_sys.c` (global 10735's text) |
| Data | `b2tools/secret_base_data.py` (all from the dump), `data/secret_bases.json` (the choices) |
| Script, text | `b2tools/secret_base_scripts.py` writes `src/field_scripts/1281_secret_bases.s` (global 10735-10742), `src/text/script/1310_secret_bases.txt` |
| Build | `b2tools/patches/secret_bases.py`, after `ramanas_park` |
| Check | `python3 b2tools/secret_base_check.py` |

- The room's contents come from the save at each field open: props added to the chunk's, solid tiles by a terrain layer, only the models in use loaded (the pack holds 135, a bundle holds 127). So every change closes and opens the field.
- Art: Pearl's models and textures as they are (the check compares every texture and palette with the model's own), and Pearl's `data/ug_base_cur.nsbmd` as the cursor. No new pixels.
- Zones 670-684 are reserved; 670 is used. Area record 409 is appended to a/0/1/3. Works 0x8050-0x8057 are scratch.

Area records: Black 2 clamps at AREA_COUNT, so record 409 needs `area_data.c`'s PearlB2 value (0x1a1), or the room falls back to area 0. A good's description is line T_DESC + good - 1 (Pearl's bank). "Goods Set n/m" waits for a key before the list, whose description would replace it. The hole's prop stands a unit off the wall: Pearl's quad sits in the wall's creases, which cut through it under Black 2's depth. The drill's YES/NO is Black 2's own menu: it ignores keys until its text is drawn.
