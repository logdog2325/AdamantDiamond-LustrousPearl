# PearlB2's extension command (2026-10-26)

Black 2's field scripts can't call new code: the command table (decomp `src/ov012/scrcmd_vm.c`, `EVCMD_TABLE`) has a
fixed size. So one entry of it, command **0x15F** (`s015F_Nop`, which no Black 2 script uses: no `Cmd_015F` in the
decomp's res/), points at PearlB2's dispatcher, and every new script command PearlB2 needs is a sub-command of it
(lead's decision, 2026-10-26).

## In a script
```
    FieldCommand 351        // 0x15F
    .byte <sub-command>
    <the sub-command's own arguments>
```
`src/include/pearl_story.inc` has `pl_ext sub` for the first two lines; each module's macros add their arguments.
Arguments are read byte by byte (Black 2's VM_Read16), so any byte alignment works. A value-or-var argument is
`ScriptReadAny` (a number, or the value of the var it names, ids from 0x4000), a var argument is `ScriptReadVar`.

## The code
- Decomp `src/pearlb2/ext_cmd_itcm.c` (ITCM, always loaded): `PearlB2_ScrCmd_Ext` reads the sub-command byte; its top
  three bits pick the module's row, the module gets the low five bits. An empty row, or a sub-command its module
  doesn't know, stops the script (`VM_Halt`): its arguments' length is unknown.
- `include/pearlb2/ext_cmd.h`: the ranges and the handler type `BOOL handler(VM *vm, FieldScriptEnv *env, u32 sub)`.
  A handler returns what a script command returns: FALSE goes on with the next command, TRUE makes the script wait a
  frame, or until the native callback it set with `VM_SetNativeCallback` returns TRUE.
- `src/ov012/scrcmd_vm.c`: entry 0x15F of `EVCMD_TABLE` = `PearlB2_ScrCmd_Ext` (`#if PEARLB2`, `s015F_Nop` under
  `#else`; a pointer for a pointer, nothing moves).

## Ranges
| Sub-commands | Module | Handler |
|---|---|---|
| 0x00-0x1F | the Pokétch | `PearlB2_Ext_Poketch` (src/pearlb2/poketch_itcm.c) |
| 0x20-0x3F | Platinum's Distortion World (plat-dw-world; the Underground never took the row) | `PearlB2_Ext_DistWorld` (src/pearlb2/resident/plat_dw_hooks.c): 0x20 DoDWWarp (resident; (plat-dw-rom) Platinum's swirl drawn in the field by dw_warp.c, overlay 382 since plat-dw3 (it was 377's), which it loads where no gimmick runs, about 124 frames; without the swirl's files the stand-in: the warp sound, 90 frames on the black screen); 0x21 GetPlayer3DPos var x, var y, var z (Platinum's world tiles), 0x22 the 1F shadow, index; 0x23 its end; 0x24 the camera's reset: the overlay's (dw_world.c) while it runs, else plain answers; (plat-dw-rom) 0x25 pl_PlatSound n (value or var): one of Platinum's own sounds (include/pearlb2.h PLATSND_*, loaded into the sound heap above the song for the scene, b2tools/patches/platinum_dw.py PLAT_SOUNDS; resident, no stand-in: nothing plays without the data); macros in pearl_story.inc block "plat-dw-world" |
| 0x40-0x5F | Pal Park | its agent adds its row |
| 0x60-0x7F | honey trees, swarms, berry patches (lead 2026-11-01) | `PearlB2_Ext_Wild` (src/pearlb2/resident/wild.c): notes/ENCOUNTERS.md |
| 0x80-0x9F | the Battle Tower | `PearlB2_Ext_Tower` (src/pearlb2/resident/tower.c, notes/BATTLE_ZONE.md). (1.0.1, v101-story) 0x91 var: the longest win streak of any room; 0x92 op, trophy, var: Pearl's Bronze, Silver or Gold Trophy given (op 0 asks, 1 marks it; bits 24-26 of the subway's score flags, which Black 2 never uses); pearl_story.inc pl_TowerTrophy is Pearl's 0x1DF on them. (plat-frontier-core, 2026-11-07) 0x93: Platinum's Battle Frontier, then one op byte and the op's arguments (`PearlB2_Ext_Frontier`, src/pearlb2/resident/plat_frontier.c, include/pearlb2/plat_frontier.h; notes/PLATINUM_FRONTIER.md): ops 0x00-0x1F the core (0x00 set the return site, value; 0x01 get it, var; 0x02 a record, stat, var; 0x03 set, stat, value; 0x04 add, stat, value; 0x05 keep the best, record stat, latest stat; 0x06 a streak flag, facility, op, bit, var; 0x07 a scene var, op, n, var), 0x20 the Factory, 0x40 the Hall, 0x60 the Castle, 0x80 the Arcade; macros in pearl_story.inc block "plat-frontier". (plat-factory, 2026-11-07) The Factory's row, ops 0x20-0x30 (`PearlB2_Frontier_Factory`, src/pearlb2/resident/plat_factory_ext.c, loads overlay 378 for one op: src/pearlb2/plat_factory/factory.c, include/pearlb2/plat_factory.h): 0x20 init (resuming, type, open level), 0x21 the round (resuming), 0x22 CallBattleFactoryFunction (fn, arg1, arg2, var), 0x23 the rental screen, 0x24 its result (var), 0x25 a swap screen (stage), 0x26 its result (stage), 0x27 the rentals picked into the party, 0x28 the next opponent, 0x29 the swap, 0x2A the next opponent's party, 0x2B the battle, 0x2C after it, 0x2D won (var), 0x2E the Trainer's line (index, actor), 0x2F free, 0x30 the lobby's streak deletion (type, open level); 0x31-0x3F free; macros pl_Factory* in pearl_story.inc block "plat-factory". (plat-hall, 2026-11-07) Ops 0x40-0x4E: the Battle Hall (decomp include/pearlb2/plat_hall.h PLATHALL_OP_*, src/pearlb2/plat_hall/hall_field.c through resident/plat_hall_ext.c; macros pearl_story.inc block "plat-hall"; notes/PLATINUM_FRONTIER.md "The Battle Hall"); 0x4F-0x5F stay free for the Hall. (plat-castle, 2026-11-07) Ops 0x60-0x79: the Battle Castle (decomp include/pearlb2/plat_castle.h PLATCASTLE_OP_*, src/pearlb2/plat_castle/castle_field.c, overlay 380, through resident/plat_castle_ext.c `PearlB2_Ext_Castle`; macros pl_Castle* in pearl_story.inc block "plat-castle"; notes/PLATINUM_FRONTIER.md "The Battle Castle"): 0x60 init (resuming, type, slot 1-3), 0x61 the round (resuming), 0x62 CallBattleCastleFunction (fn, arg1, arg2, var), 0x63 free, 0x64 the first opponent, 0x65 the next opponent, 0x66 the battle, 0x67 after it, 0x68 won (var), 0x69 the Trainer's line into a word (word, slot, line), 0x6A-0x6C the CP (get: type, var; spend and receive: type, CP), 0x6D the lobby's function (fn, arg, var), 0x6E the lobby's streak deletion (type), 0x6F the self screen's party screen, 0x70 its pick (var), 0x71 a purchase's question (kind, slot, arg, var), 0x72 the purchase (kind, slot, arg, var), 0x73 the rental list (items), 0x74 the opponent list (line), 0x75 a Pokémon's words (side, slot, what), 0x76 the screens' information (what, slot, var), 0x77 the CP into a word (word), 0x78 the lobby's party screen (type), 0x79 its slots (var, var, var); 0x7A-0x7F stay free for the Castle. (plat-arcade, 2026-11-07) Ops 0x80-0x8F: the Battle Arcade (decomp include/pearlb2/plat_arcade.h PLATARCADE_OP_*, src/pearlb2/plat_arcade/arcade_field.c, overlay 381, through resident/plat_arcade_ext.c `PearlB2_Ext_Arcade`; macros pl_Arcade* in pearl_story.inc block "plat-arcade"; notes/PLATINUM_FRONTIER.md "The Battle Arcade"): 0x80 init (resuming, type, slot 1-3), 0x81 the round (resuming), 0x82 CallBattleArcadeFunction (fn, arg1, arg2, var), 0x83 free, 0x84 the first opponent, 0x85 the next opponent, 0x86 the battle, 0x87 after it, 0x88 won (var), 0x89 the Trainer's line into a word (word, slot, line), 0x8A the board's effect applied, 0x8B the game board (first line: the room's 32 lines naming the effects), 0x8C the lobby's function (fn, arg, var), 0x8D the lobby's streak deletion (type), 0x8E the lobby's party screen (type), 0x8F its slots (var, var, var); 0x90-0x9F stay free for the Arcade. 0x94-0x9F free |
| 0xA0-0xBF | the smaller finishes of the base game | `PearlB2_Ext_Leftovers` (src/pearlb2/resident/leftovers.c): 0xA0 first-battle rules, value; 0xA1 Vs. Seeker check, var result, var steps; 0xA2 its Trainers' answer, var result; 0xA3 the Trainer to rematch, actor, base Trainer, var; 0xA4 stop the spin, actor; 0xA5 Unown forms seen, var; 0xA6 a person's movement in the zone's template, uid, move code; 0xA7 (plat-trades, 2026-11-07: Gen 4's StartNPCTrade, `PearlB2_NpcTrade_Start` in resident/npc_trade.c, include/pearlb2/npc_trade.h) trade, party slot: Black 2's trade event and demo with the Pokémon made by Gen 4's rules from the table patches/npc_trades.py writes (the script waits; no table: nothing traded); 0xA8 (plat-trades: Gen 4's ActivateRoamingPokemon, `PearlB2_Roamers_Activate` in resident/roamers.c) the game's roamer slot (Platinum's ROAMING_SLOT_*), released now (both value-or-var; macros in pearl_story.inc block "plat-trades"); 0xA9 (postdex, 2026-11-09: notes/POSTGAME_DEX.md) the deliveryman's event Pokémon, index, var result (value-or-var index into gPearlB2EventGifts, patches/event_gifts.py from data/event_gifts.json: Black 2's Mystery Gift maker CreateMysteryGiftPokemon into the party; result 1 given, 0 no room or no table; pearl_story.inc pl_DeliveryGive); 0xB0-0xB6 (plat-tutors, 2026-11-07: Platinum's party commands, `PearlB2_Ext_PlatParty` in resident/plat_party_ext.c, their code overlay 376 at Pal Park's address, loaded for the one command: src/pearlb2/plat_party/, include/pearlb2/plat_party.h; macros in pearl_story.inc block "plat-tutors"): 0xB0 a shard tutor move, slot, Platinum's tutor index, var (0 can't, 1 can, 2 knows it); 0xB1 any move of a tutor left, slot, tutor location, var; 0xB2 the footprint, var print, var type, slot; 0xB3 a contest condition or one of Platinum's ribbons, var, slot, Black 2 PKM_PARAM; 0xB4 a ribbon given, slot, PKM_PARAM; 0xB5 Platinum's ribbons in the party, var; 0xB6 a line of the script's own text into a word buffer, word, line (all value-or-var arguments; the tutor and footprint tables only a Platinum build fills, patches/platinum_tutors.py); 0xBF (Platinum only: patches/platinum_regigigas.py wraps the row) the deliveryman's event Regigigas into the party, var result; 0xBE and 0xBD (Platinum only: patches/platinum_postgame.py wraps the row again, plat-ch12) Platinum's StartFatefulEncounter, species, level (a static wild battle whose Pokémon has the fateful-encounter mark: Flower Paradise's Shaymin) and GetRotomFormsInSave, var (a bit for each Rotom form in the party, the Day Care and the boxes) |
| 0xC0-0xDF | Contests, Poffins | their agents add their rows |
| 0xE0-0xFF | Pearl's Secret Bases | `PearlB2_Ext_SecretBase` (src/pearlb2/resident/secret_base.c, notes/SECRET_BASES.md): one value-or-var argument each; results in works 0x8050-0x8053 |

## The Pokétch's sub-commands (notes/POKETCH.md)
| Sub | Macro (Platinum's names, as the other pl_ macros) | Arguments | Pearl's command (pokediamond's name) |
|---|---|---|---|
| 0x00 | `pl_EnablePoketch` | - | 0x131 GivePoketch: the Pokétch given; the bottom screen fades to it (the script waits) |
| 0x01 | `pl_CheckPoketchEnabled var` | var | 0x132 CheckPoketch: var = 1 if given |
| 0x02 | `pl_RegisterPoketchApp app` | value or var | 0x133 UnlockPoketchApp (the Pedometer also starts counting) |
| 0x03 | `pl_CheckPoketchAppRegistered app, var` | value or var, var | 0x134 CheckPoketchApp: var = 1 if registered |
| 0x04 | `pl_HidePoketch` | - | 0x265: Pearl's flag 0x97C set (no Pokétch from the next bottom-screen start) |
| 0x05 | `pl_ShowPoketch` | - | 0x266: flag 0x97C cleared |

## Wild Pokémon and berries' sub-commands (notes/ENCOUNTERS.md)
| Sub | Macro | Arguments | Pearl's command |
|---|---|---|---|
| 0x60 | `pl_GetHoneyTreeStatus var` | var | 0x128 CheckHoneyTree: 1 bare, 2 slathered, 3 a Pokémon may be there |
| 0x61 | `pl_SlatherHoneyTree` | - | 0x127 UpdateHoneyTree |
| 0x62 | `pl_StartHoneyTreeBattle` | var, var: species and level; the macro then calls the battle | 0x129 HoneyTreeBattle |
| 0x63 | `pl_StopHoneyTreeShaking` | - | 0x12A StopHoneyTreeAnimation (nothing: the tree doesn't shake yet) |
| 0x64 | `pl_EnableSwarms` | - | 0x21B |
| 0x65 | `pl_GetSwarmInfo zone, species` | var, var: the day's Black 2 zone and first species | 0xE3 GetSwarmInfo |
| 0x66 | `pl_GetBerry field, var` | 0x8011, byte, var | 0x17D-0x181: 0 stage, 1 Berry item, 2 mulch item, 3 moisture, 4 yield |
| 0x67 | `pl_SetBerryMulch item` | 0x8011, value or var | 0x182 |
| 0x68 | `pl_PlantBerry item` | 0x8011, value or var | 0x183 |
| 0x69 | `pl_WaterBerry` | 0x8011 | 0x184 0 |
| 0x6A | `pl_HarvestBerry` | 0x8011 | 0x185 |
| 0x6B | `pl_BufferBerryName n, item` | byte, value or var | 0x17B |
| 0x6C | `pl_OpenBerryBag pocket` | byte (Black 2's pocket); the macro opens the Bag | 0x178 |
| 0x6D | `pl_CheckBerriesInBag var` | var | 0x17A CheckPocketNotEmpty 4 |
