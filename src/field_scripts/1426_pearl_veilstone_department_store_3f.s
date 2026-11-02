// MAP_VEILSTONE_DEPARTMENT_STORE_3F: Pearl script file 139, text bank 142. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-6: Pearl's; no warp continuations; 7: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P139_S1
    ScriptEntry P139_S2
    ScriptEntry P139_S3
    ScriptEntry P139_S4
    ScriptEntry P139_S5
    ScriptEntry P139_S6
    ScriptEntry PearlArrive
    ScriptEntry PearlElevatorInit
    ScriptEntriesEnd

P139_S1:
P139_001A:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    WorkSetConst PVAR_800C, 0  // Unk027E: the Department Store's regulars (not counted here)
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P139_005B
    pl_msg_talk 0
    ListMenu_AnchorTopRight 31, 1, 0, 0, PVAR_800C  // Pearl InitGlobalTextMenu 1, 1, 0, 1, PVAR_800C
    ListMenuAdd 10, 65535, 1  // Pearl AddMenuEntryImm 229, 1
    ListMenuAdd 11, 65535, 0  // Pearl AddMenuEntryImm 228, 0
    ListMenuShow
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P139_00BE
    pl_GoTo P139_00B3

P139_005B:
    pl_BufferPlayerName 0
    pl_msg_talk 1
    ListMenu_AnchorTopRight 31, 1, 0, 0, PVAR_800C  // Pearl InitGlobalTextMenu 1, 1, 0, 1, PVAR_800C
    ListMenuAdd 10, 65535, 0  // Pearl AddMenuEntryImm 229, 0
    ListMenuAdd 11, 65535, 1  // Pearl AddMenuEntryImm 228, 1
    ListMenuShow
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 5, P139_00B3
    pl_GetRandom PVAR_800C, 4
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P139_00BE
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P139_00C9
    pl_CompareVarToValue PVAR_800C, 2
    pl_GoToIf 1, P139_00D4
    pl_GoTo P139_00DF

P139_00B3:
    pl_msg_talk 2
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P139_00BE:
    pl_msg_talk 3
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P139_00C9:
    pl_msg_talk 4
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P139_00D4:
    pl_msg_talk 5
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P139_00DF:
    pl_msg_talk 6
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P139_S2:
P139_00EA:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 7
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P139_S3:
P139_00FD:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 8
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P139_S4:
P139_0110:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
// CallCommonScript 2019 (Pearl's Mart greeting): Black 2's Mart menu says it
    pl_CloseMessageWithoutErasing
    pl_PokeMartSpecial 12  // Pearl SpecialMart 12
    pl_ReleaseAll
    pl_End

P139_S5:
P139_0126:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
// CallCommonScript 2019 (Pearl's Mart greeting): Black 2's Mart menu says it
    pl_CloseMessageWithoutErasing
    pl_PokeMartSpecial 13  // Pearl SpecialMart 13
    pl_ReleaseAll
    pl_End

P139_S6:
P139_013C:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_msg_sys 9
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

PearlElevatorInit:                // zone init (after Pearl's): an elevator (ELEVATOR_FLOORS_ABOVE)
    WorkSetConst PVAR_40CE, 2  // this floor's floors above (an elevator reads it)
    VMHalt

PearlNoScript:
    VMHalt

PearlArrive:                      // arriving by a script warp with nothing after it: fade in, release
    FadeInBlack
    FadeWait
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0
