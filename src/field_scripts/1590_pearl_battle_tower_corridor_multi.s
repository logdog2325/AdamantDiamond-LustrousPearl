// MAP_BATTLE_TOWER_CORRIDOR_MULTI: Pearl script file 360, text bank 18. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-3: Pearl's; 4: after a Warp; 5: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P360_S1
    ScriptEntry P360_S2
    ScriptEntry P360_S3
    ScriptEntry W359_0031_S
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P360_S1:
P360_000E:
    pl_End

P360_S2:
P360_0010:
    pl_CompareVarToValue PVAR_40DC, 0
    pl_CallIf 5, P360_001F
    pl_End

P360_001F:
    pl_TowerActorVisible PL_PLAYER, 0  // Pearl HideObject 255 (no actor command)
    pl_Return

P360_S3:
P360_0025:
    pl_LockAll
    pl_Call P360_008E
    pl_GetRandom PVAR_800C, 4
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, P360_00F0
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, P360_010A
    pl_CompareVarToValue PVAR_8008, 3
    pl_GoToIf 1, P360_0124
    pl_GoTo P360_00D6

P360_0066:
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 7  // the rest of this Pearl script runs there (continuation 7)
    pl_Warp 619, 7, 6, 0  // Pearl map 330 (MAP_BATTLE_TOWER_ARENA_MULTI)
    pl_ReleaseAll
    pl_End

P360_008E:
    pl_LoadDoorAnimation 77, 2, 2  // the door at cell (0,0) tile (2,2)
    pl_PlayDoorOpenAnimation 77
    pl_WaitForAnimation 77
    pl_ApplyMovement 0, P360_0140
    pl_WaitMovement
    pl_ShowObject PL_PLAYER  // Pearl ShowObject 255
    pl_ApplyMovement PL_PLAYER, P360_014C
    pl_WaitMovement
    pl_PlayDoorCloseAnimation 77
    pl_WaitForAnimation 77
    pl_UnloadAnimation 77
    pl_Return

P360_00D6:
    pl_ApplyMovement 0, P360_0178
    pl_ApplyMovement PL_PLAYER, P360_0188
    pl_WaitMovement
    pl_GoTo P360_0066

P360_00F0:
    pl_ApplyMovement 0, P360_019C
    pl_ApplyMovement PL_PLAYER, P360_01AC
    pl_WaitMovement
    pl_GoTo P360_0066

P360_010A:
    pl_ApplyMovement 0, P360_01C0
    pl_ApplyMovement PL_PLAYER, P360_01D0
    pl_WaitMovement
    pl_GoTo P360_0066

P360_0124:
    pl_ApplyMovement 0, P360_01E4
    pl_ApplyMovement PL_PLAYER, P360_01F4
    pl_WaitMovement
    pl_GoTo P360_0066

    .balign 4, 0
P360_0140:
    Move 13, 3  // WALK_NORMAL_SOUTH
    Move 0, 1  // FACE_NORTH
    MoveEnd

    .balign 4, 0
P360_014C:
    Move 13, 2  // WALK_NORMAL_SOUTH
    MoveEnd

    .balign 4, 0
P360_0178:
    Move 15, 4  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P360_0188:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 15, 4  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P360_019C:
    Move 15, 8  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P360_01AC:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 15, 8  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P360_01C0:
    Move 15, 12  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P360_01D0:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 15, 12  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P360_01E4:
    Move 15, 16  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P360_01F4:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 15, 16  // WALK_NORMAL_EAST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

// ---- continuation 4: after the Warp at 359:0031 (MAP_BATTLE_TOWER_ELEVATOR)
W359_0031_S:
W359_0031_003D:
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
