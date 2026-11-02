// MAP_VEILSTONE_GALACTIC_HEADQUARTERS_B2F: Pearl script file 338, text bank 267. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-3: Pearl's; no warp continuations; 4: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P338_S1
    ScriptEntry P338_S2
    ScriptEntry P338_S3
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P338_S1:
P338_000E:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 0
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P338_S2:
P338_0021:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 1
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P338_S3:
P338_0034:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckItem 440, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P338_005C
    pl_msg_sys 2
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P338_005C:
    pl_msg_sys 3
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P338_007F
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P338_00B3
    pl_End

P338_007F:
    pl_BufferPlayerName 0
    pl_msg_sys 4
    pl_WaitButton
    pl_WaitSE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_PlaySE SEQ_SE_OPEN1  // Pearl SEQ_SE_DP_DOOR10
    pl_ApplyMovement 6, P338_00BC
    pl_ApplyMovement 7, P338_00C4
    pl_WaitMovement
    pl_SetFlag PFLAG_0245
    pl_RemoveObject 6, PFLAG_0245
    pl_RemoveObject 7, PFLAG_0245
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P338_00B3:
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

    .balign 4, 0
P338_00BC:
    Move 18, 1  // WALK_FAST_WEST
    MoveEnd

    .balign 4, 0
P338_00C4:
    Move 19, 1  // WALK_FAST_EAST
    MoveEnd

PearlNoScript:
    VMHalt

PearlArrive:                      // arriving by a script warp with nothing after it: fade in, release
    FadeInBlack
    FadeWait
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0
