// MAP_BATTLE_TOWER_CORRIDOR_WIFI: Pearl script file 361, text bank 18. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-3: Pearl's; 4: after a Warp; 5: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P361_S1
    ScriptEntry P361_S2
    ScriptEntry P361_S3
    ScriptEntry W359_0081_S
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P361_S1:
P361_000E:
    pl_CompareVarToValue PVAR_40DD, 0
    pl_GoToIf 1, P361_0048
    pl_SetVarFromValue PVAR_4000, 0  // GetCurNetID: no link
    pl_CompareVarToValue PVAR_4000, 1
    pl_GoToIf 1, P361_004A
    pl_TowerPlayerCode PVAR_4000  // Pearl tower function 55: the player's sprite
    pl_SetVarFromVar PVAR_4020, PVAR_4000
    pl_TowerPartnerCode PVAR_4000  // Pearl tower function 55
    pl_SetVarFromVar PVAR_4021, PVAR_4000

P361_0048:
    pl_End

P361_004A:
    pl_TowerPlayerCode PVAR_4000  // Pearl tower function 55: the player's sprite
    pl_SetVarFromVar PVAR_4021, PVAR_4000
    pl_TowerPartnerCode PVAR_4000  // Pearl tower function 55
    pl_SetVarFromVar PVAR_4020, PVAR_4000
    pl_End

P361_S2:
P361_0068:
    pl_CompareVarToValue PVAR_40DD, 0
    pl_CallIf 5, P361_007F
    pl_TowerActorVisible 2, 0  // Pearl HideObject 2 (no actor command)
    pl_TowerActorVisible 3, 0  // Pearl HideObject 3 (no actor command)
    pl_End

P361_007F:
    pl_TowerActorVisible PL_PLAYER, 0  // Pearl HideObject 255 (no actor command)
    pl_stub MoveCamera  // Pearl 0x06B Unk006B 8, 0, 0: not translated yet
    pl_Return

P361_S3:
P361_008D:
    pl_LockAll
    pl_Call P361_00C9
    pl_Call P361_012B
    pl_Call P361_014F
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 6  // the rest of this Pearl script runs there (continuation 6)
    pl_Warp 620, 7, 5, 0  // Pearl map 331 (MAP_BATTLE_TOWER_ARENA_WIFI)
    pl_ReleaseAll
    pl_End

P361_00C9:
    pl_LoadDoorAnimation 77, 3, 2  // the door at cell (0,0) tile (3,2)
    pl_LoadDoorAnimation 78, 14, 2  // the door at cell (0,0) tile (14,2)
    pl_PlayDoorOpenAnimation 77
    pl_PlayDoorOpenAnimation 78
    pl_WaitForAnimation 77
    pl_WaitForAnimation 78
    pl_ApplyMovement 0, P361_0174
    pl_ApplyMovement 1, P361_0174
    pl_WaitMovement
    pl_ShowObject 2  // Pearl ShowObject 2
    pl_ShowObject 3  // Pearl ShowObject 3
    pl_ApplyMovement 2, P361_0180
    pl_ApplyMovement 3, P361_0180
    pl_WaitMovement
    pl_PlayDoorCloseAnimation 77
    pl_PlayDoorCloseAnimation 78
    pl_WaitForAnimation 77
    pl_WaitForAnimation 78
    pl_UnloadAnimation 77
    pl_UnloadAnimation 78
    pl_Return

P361_012B:
    pl_ApplyMovement 0, P361_01AC
    pl_ApplyMovement 2, P361_0188
    pl_ApplyMovement 1, P361_01CC
    pl_ApplyMovement 3, P361_0194
    pl_WaitMovement
    pl_Return

P361_014F:
    pl_ApplyMovement 0, P361_01EC
    pl_ApplyMovement 1, P361_01EC
    pl_ApplyMovement 2, P361_01A0
    pl_ApplyMovement 3, P361_01A0
    pl_WaitMovement
    pl_Return

    .balign 4, 0
P361_0174:
    Move 13, 3  // WALK_NORMAL_SOUTH
    Move 0, 1  // FACE_NORTH
    MoveEnd

    .balign 4, 0
P361_0180:
    Move 13, 2  // WALK_NORMAL_SOUTH
    MoveEnd

    .balign 4, 0
P361_0188:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 15, 5  // WALK_NORMAL_EAST
    MoveEnd

    .balign 4, 0
P361_0194:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 14, 5  // WALK_NORMAL_WEST
    MoveEnd

    .balign 4, 0
P361_01A0:
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P361_01AC:
    Move 15, 5  // WALK_NORMAL_EAST
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 63, 1  // DELAY_8
    Move 3, 1  // FACE_EAST
    Move 62, 1  // DELAY_4
    Move 0, 1  // FACE_NORTH
    Move 62, 1  // DELAY_4
    MoveEnd

    .balign 4, 0
P361_01CC:
    Move 14, 5  // WALK_NORMAL_WEST
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 63, 1  // DELAY_8
    Move 2, 1  // FACE_WEST
    Move 62, 1  // DELAY_4
    Move 0, 1  // FACE_NORTH
    Move 62, 1  // DELAY_4
    MoveEnd

    .balign 4, 0
P361_01EC:
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

// ---- continuation 4: after the Warp at 359:0081 (MAP_BATTLE_TOWER_ELEVATOR)
W359_0081_S:
W359_0081_008D:
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
