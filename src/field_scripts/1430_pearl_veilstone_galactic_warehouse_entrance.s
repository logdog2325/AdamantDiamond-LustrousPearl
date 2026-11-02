// MAP_VEILSTONE_GALACTIC_WAREHOUSE_ENTRANCE: Pearl script file 143, text bank 146. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-2: Pearl's; no warp continuations; 3: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P143_S1
    ScriptEntry P143_S2
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P143_S1:
P143_000A:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_015E
    pl_GoToIf 1, P143_0058
    pl_CompareVarToValue PVAR_40D3, 2
    pl_GoToIf 4, P143_004D
    pl_CompareVarToValue PVAR_40B2, 2
    pl_GoToIf 4, P143_0042
    pl_msg_talk 0
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P143_0042:
    pl_msg_talk 1
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P143_004D:
    pl_msg_talk 2
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P143_0058:
    pl_msg_talk 3
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P143_S2:
P143_0063:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckItem 463, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P143_008B
    pl_msg_sys 4
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P143_008B:
    pl_msg_sys 5
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P143_00AE
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P143_00EA
    pl_End

P143_00AE:
    pl_SetFlag PFLAG_010E
    pl_RemoveItem 463, 1, PVAR_800C
    pl_BufferPlayerName 0
    pl_msg_sys 6
    pl_WaitButton
    pl_WaitSE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_PlaySE SEQ_SE_OPEN1  // Pearl SEQ_SE_DP_DOOR10
    pl_ApplyMovement 3, P143_00F0
    pl_ApplyMovement 4, P143_00F8
    pl_WaitMovement
    pl_RemoveObject 3, PFLAG_0246
    pl_RemoveObject 4, PFLAG_0246
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P143_00EA:
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

    .balign 4, 0
P143_00F0:
    Move 18, 1  // WALK_FAST_WEST
    MoveEnd

    .balign 4, 0
P143_00F8:
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
