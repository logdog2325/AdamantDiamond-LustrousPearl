// MAP_ROUTE_206_CYCLING_ROAD_GATEHOUSE: Pearl script file 401, text bank 424. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-4: Pearl's; no warp continuations; 5: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P401_S1
    ScriptEntry P401_S2
    ScriptEntry P401_S3
    ScriptEntry P401_S4
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P401_S1:
P401_0012:
    pl_CheckItem 450, 1, PVAR_40EC
    pl_End

P401_S2:
P401_001C:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 2
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P401_S3:
P401_002F:
    pl_LockAll
    pl_ApplyMovement 0, P401_0050
    pl_WaitMovement
    pl_msg_sys 1
    pl_CloseMessage
    pl_ApplyMovement PL_PLAYER, P401_0058
    pl_WaitMovement
    pl_ReleaseAll
    pl_End

P401_S4:
P401_0060:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_012B
    pl_GoToIf 1, P401_0095
    pl_SetVarFromValue PVAR_8004, 96
    pl_BufferAccessoryWord 0, PVAR_8004  // Pearl BufferAccessoryName
    pl_msg_talk 3
    pl_SetVarFromValue PVAR_8005, 1
    VMCall C205_16_S16  // CallCommonScript 2015 (Pearl file 205 script 16)
    pl_SetFlag PFLAG_012B
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P401_0095:
    pl_msg_talk 4
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

    .balign 4, 0
P401_0050:
    Move 75, 1  // EMOTE_EXCLAMATION_MARK
    MoveEnd

    .balign 4, 0
P401_0058:
    Move 13, 1  // WALK_NORMAL_SOUTH
    MoveEnd

// ---- Pearl global script 205:16 (a subroutine here)
C205_16_S16:
C205_16_0906:
    pl_Call C205_16_0922
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 5  // Pearl bank 199 line 31, an Accessory by word
    pl_WaitButton
    pl_ReturnCommonScript
    VMReturn  // End: the sub-script ends

C205_16_0922:
    pl_PlayFanfare SEQ_ME_ACCE  // Pearl SEQ_ACCE
    pl_AddAccessory PVAR_8004, PVAR_8005  // Pearl AddAccessory (the Fashion Case)
    pl_BufferAccessoryWord 0, PVAR_8004  // Pearl BufferAccessoryName
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 6  // Pearl bank 199 line 25, an Accessory by word
    pl_WaitFanfare
    pl_BufferPlayerName 0
    pl_BufferAccessoryWord 1, PVAR_8004  // Pearl BufferAccessoryName
    pl_Return

PearlNoScript:
    VMHalt

PearlArrive:                      // arriving by a script warp with nothing after it: fade in, release
    FadeInBlack
    FadeWait
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0
