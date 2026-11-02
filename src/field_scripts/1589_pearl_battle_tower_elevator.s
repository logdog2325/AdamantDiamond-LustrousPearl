// MAP_BATTLE_TOWER_ELEVATOR: Pearl script file 359, text bank 18. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-4: Pearl's; 5: after a Warp, 6: after a Warp; 7: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P359_S1
    ScriptEntry P359_S2
    ScriptEntry P359_S3
    ScriptEntry P359_S4
    ScriptEntry W358_02E9_S
    ScriptEntry W364_0229_S
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P359_S1:
P359_0012:
    pl_CompareVarToValue PVAR_40DB, 0
    pl_CallIf 5, P359_0021
    pl_End

P359_0021:
    pl_HidePoketch
    pl_Return

P359_0025:
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 4  // the rest of this Pearl script runs there (continuation 4)
    pl_Warp 617, 2, 1, 1  // Pearl map 328 (MAP_BATTLE_TOWER_CORRIDOR_MULTI)
    pl_ReleaseAll
    pl_End

P359_0075:
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 4  // the rest of this Pearl script runs there (continuation 4)
    pl_Warp 618, 8, 3, 1  // Pearl map 329 (MAP_BATTLE_TOWER_CORRIDOR_WIFI)
    pl_ReleaseAll
    pl_End

P359_00C5:
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 11  // the rest of this Pearl script runs there (continuation 11)
    pl_Warp 621, 8, 2, 1  // Pearl map 493 (MAP_BATTLE_TOWER_PARTNER_ROOM)
    pl_ReleaseAll
    pl_End

P359_00ED:
    pl_Call P359_0143
    pl_elevator_ride  // PlayElevatorAnimation PVAR_4000, 3
    pl_Call P359_014F
    pl_Return

P359_S2:
P359_0101:
    pl_LockAll
    pl_SetVarFromValue PVAR_4000, 0
    pl_Call P359_00ED
    pl_GoTo P359_0025

P359_S3:
P359_0117:
    pl_LockAll
    pl_SetVarFromValue PVAR_4000, 0
    pl_Call P359_00ED
    pl_GoTo P359_0075

P359_S4:
P359_012D:
    pl_LockAll
    pl_SetVarFromValue PVAR_4000, 1
    pl_Call P359_00ED
    pl_GoTo P359_00C5

P359_0143:
    pl_ApplyMovement PL_PLAYER, P359_0178
    pl_WaitMovement
    pl_Return

P359_014F:
    pl_ApplyMovement 0, P359_0184
    pl_ApplyMovement PL_PLAYER, P359_01A0
    pl_WaitMovement
    pl_Return

    .balign 4, 0
P359_0178:
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 1, 1  // FACE_SOUTH
    MoveEnd

    .balign 4, 0
P359_0184:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 2, 1  // FACE_WEST
    Move 14, 1  // WALK_NORMAL_WEST
    Move 1, 1  // FACE_SOUTH
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P359_01A0:
    Move 63, 2  // DELAY_8
    Move 61, 1  // DELAY_2
    Move 13, 2  // WALK_NORMAL_SOUTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

// ---- continuation 5: after the Warp at 358:02E9 (MAP_BATTLE_TOWER_LOBBY)
W358_02E9_S:
W358_02E9_02F5:
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_ReleaseAll
    pl_End

// ---- continuation 6: after the Warp at 364:0229 (MAP_BATTLE_TOWER_PARTNER_ROOM)
W364_0229_S:
W364_0229_0235:
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_ReleaseAll
    pl_End

PearlNoScript:
    VMHalt

PearlArrive:                      // arriving by a script warp with nothing after it: fade in, release
    FadeInBlack
    FadeWait
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0
