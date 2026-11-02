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
| 0x20-0x3F | the Underground | its agent adds its row |
| 0x40-0x5F | Pal Park | its agent adds its row |
| 0x60-0x7F | honey trees, swarms, berry patches (lead 2026-11-01) | `PearlB2_Ext_Wild` (src/pearlb2/resident/wild.c): notes/ENCOUNTERS.md |
| 0x80-0x9F | the Battle Tower | `PearlB2_Ext_Tower` (src/pearlb2/resident/tower.c, notes/BATTLE_ZONE.md) |
| 0xA0-0xBF | the smaller finishes of the base game | `PearlB2_Ext_Leftovers` (src/pearlb2/resident/leftovers.c): 0xA0 first-battle rules, value; 0xA1 Vs. Seeker check, var result, var steps; 0xA2 its Trainers' answer, var result; 0xA3 the Trainer to rematch, actor, base Trainer, var; 0xA4 stop the spin, actor; 0xA5 Unown forms seen, var; 0xA6 a person's movement in the zone's template, uid, move code |
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
