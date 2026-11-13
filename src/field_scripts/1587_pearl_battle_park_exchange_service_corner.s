// MAP_BATTLE_PARK_EXCHANGE_SERVICE_CORNER: Pearl script file 356, text bank 282. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-9: Pearl's; no warp continuations; 10: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P356_S1
    ScriptEntry P356_S2
    ScriptEntry P356_S3
    ScriptEntry P356_S4
    ScriptEntry P356_S5
    ScriptEntry P356_S6
    ScriptEntry P356_S7
    ScriptEntry P356_S8
    ScriptEntry P356_S9
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P356_S1:
P356_0024:
    pl_SetVarFromValue PVAR_4000, 0
    pl_SetVarFromValue PVAR_4001, 26
    pl_GoTo P356_0048

P356_S2:
P356_0036:
    pl_SetVarFromValue PVAR_4000, 1
    pl_SetVarFromValue PVAR_4001, 15
    pl_GoTo P356_0048

P356_0048:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_TowerBpWindow 9, 6  // ShowBattlePoints 21, 1: Black 2's money window
    pl_msg_talk 0

P356_0057:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 1
    pl_Call P356_0131
    pl_CompareVarToValue PVAR_800C, 65534
    pl_GoToIf 1, P356_00F4
    pl_CompareVarToVar PVAR_800C, PVAR_4001
    pl_GoToIf 1, P356_00F4
    pl_SetVarFromVar PVAR_4003, PVAR_800C
    pl_TowerExchange PVAR_4000, PVAR_4003, PVAR_8000, PVAR_8001
    pl_CompareVarToValue PVAR_4000, 0
    pl_CallIf 1, P356_0101
    pl_CompareVarToValue PVAR_4000, 1
    pl_CallIf 1, P356_010B
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P356_0057
    pl_TowerBpCheck PVAR_8001, PVAR_800C  // CheckBattlePoints
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P356_011A
    pl_CanFitItem PVAR_8000, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P356_0123
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 3
    pl_AddItem PVAR_8000, 1, PVAR_800C
    pl_TowerBpSub PVAR_8001
    pl_TowerBpWindow 9, 6  // UpdateBPDisplay
    pl_GoTo P356_0057

P356_00F4:
    pl_msg_talk 6
    pl_WaitButton
    pl_CloseMessage
    MoneyWinClose  // HideBattlePoints
    pl_ReleaseAll
    pl_End

P356_0101:
    pl_BufferItemName 0, PVAR_8000
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 2
    pl_Return

P356_010B:
    pl_BufferItemName 0, PVAR_8000
    pl_BufferTMHMMoveName 1, PVAR_8000
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 7
    pl_Return

P356_011A:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 4
    pl_GoTo P356_0057

P356_0123:
    pl_BufferItemName 0, PVAR_8000
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 5
    pl_GoTo P356_0057

P356_0131:
    pl_SetVarFromValue PVAR_8008, 0
    pl_SetVarFromValue PVAR_8009, 0
    ListMenu_AnchorTopRight 31, 1, 0, 1, PVAR_800C  // Pearl InitGlobalTextListMenu 1, 1, 0, 1, PVAR_800C

P356_0145:
    pl_TowerExchange PVAR_4000, PVAR_8008, PVAR_8000, PVAR_8001
    pl_BufferItemName 0, PVAR_8000
    pl_BufferNumber 1, PVAR_8001, 3  // BufferVarPaddingDigits
    ListMenuAdd 15, 65535, PVAR_8008  // Pearl AddListMenuEntry 231, PVAR_8008
    pl_AddVar PVAR_8008, 1
    pl_CompareVarToVar PVAR_8008, PVAR_4001
    pl_GoToIf 0, P356_0145
    ListMenuAdd 16, 65535, PVAR_8008  // Pearl AddListMenuEntry 232, PVAR_8008
    ListMenuShow
    pl_Return

P356_S3:
P356_0182:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 8
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P356_S4:
P356_0195:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 9
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P356_S5:
P356_01A8:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 10
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P356_S6:
P356_01BB:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 13
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P356_S7:
P356_01CE:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 14
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P356_S8:
P356_S9:
P356_01E1:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_msg_talk 11
    pl_msg_talk 12
    pl_WaitButton
    pl_CloseMessage
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
