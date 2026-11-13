// MAP_JUBLIFE_TV_2F: Pearl script file 12, text bank 26. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-3: Pearl's; no warp continuations; 4: PearlArrive; 99: Pearl 10158
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P12_S1
    ScriptEntry P12_S2
    ScriptEntry P12_S3
    ScriptEntry PearlArrive
    ScriptEntry PearlElevatorInit
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlProxy_10158
    ScriptEntriesEnd

P12_S3:
P12_000E:
    pl_stub CheckTVInterviewEligible  // Pearl 0x238 Unk0238 9, 16384: not translated yet
    pl_CompareVarToValue PVAR_4000, 0
    pl_GoToIf 1, P12_0027
    pl_ClearFlag PFLAG_0233
    pl_End

P12_0027:
    pl_SetFlag PFLAG_0233
    pl_End

P12_S1:
P12_002D:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 0
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P12_S2:
P12_0040:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_013D
    pl_GoToIf 1, P12_00A0
    pl_GetPlayerStarterSpecies PVAR_800C
    pl_CompareVarToValue PVAR_800C, 387
    pl_CallIf 1, P12_00B0
    pl_CompareVarToValue PVAR_800C, 390
    pl_CallIf 1, P12_00B8
    pl_CompareVarToValue PVAR_800C, 393
    pl_CallIf 1, P12_00C0
    pl_SetVarFromVar PVAR_410A, PVAR_8004
    pl_BufferAccessoryArticle 0, PVAR_8004  // Pearl GetFashionNameWithArticle
    pl_msg_talk 1
    pl_SetVarFromValue PVAR_8005, 1
    VMCall C205_16_S16  // CallCommonScript 2015 (Pearl file 205 script 16)
    pl_SetFlag PFLAG_013D
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P12_00A0:
    pl_BufferAccessoryWord 0, PVAR_410A  // Pearl BufferAccessoryName
    pl_msg_talk 3  // Pearl bank 26 line 2, an Accessory by word
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P12_00B0:
    pl_SetVarFromValue PVAR_8004, 92
    pl_Return

P12_00B8:
    pl_SetVarFromValue PVAR_8004, 93
    pl_Return

P12_00C0:
    pl_SetVarFromValue PVAR_8004, 94
    pl_Return

PearlProxy_10158:                  // Pearl global script 10158 (run by this zone's events)
    VMCall T1042_9_S9
    VMHalt

PearlElevatorInit:                // zone init (after Pearl's): an elevator (ELEVATOR_FLOORS_ABOVE)
    WorkSetConst PVAR_40CE, 2  // this floor's floors above (an elevator reads it)
    VMHalt

// ---- Pearl global script 205:16 (a subroutine here)
C205_16_S16:
C205_16_0906:
    pl_Call C205_16_0922
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 4  // Pearl bank 199 line 31, an Accessory by word
    pl_WaitButton
    pl_ReturnCommonScript
    VMReturn  // End: the sub-script ends

C205_16_0922:
    pl_PlayFanfare SEQ_ME_ACCE  // Pearl SEQ_ACCE
    pl_AddAccessory PVAR_8004, PVAR_8005  // Pearl AddAccessory (the Fashion Case)
    pl_BufferAccessoryWord 0, PVAR_8004  // Pearl BufferAccessoryName
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 5  // Pearl bank 199 line 25, an Accessory by word
    pl_WaitFanfare
    pl_BufferPlayerName 0
    pl_BufferAccessoryWord 1, PVAR_8004  // Pearl BufferAccessoryName
    pl_Return

// ---- Pearl global script 1042:9 (a subroutine here)
T1042_9_S9:
T1042_9_0096:
    pl_SetVarFromValue PVAR_8000, 9
    pl_GoTo T1042_9_00D2

T1042_9_00D2:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_stub CheckTVInterviewEligible  // Pearl 0x238 Unk0238 32768, 32780: not translated yet
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T1042_9_0214
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 6  // Pearl bank 562 line 0
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T1042_9_0107
    pl_GoTo T1042_9_021F

T1042_9_0107:
    pl_stub CallTVInterview  // Pearl 0x237 Unk0237 0, 32768, 32772, 32773: not translated yet
    pl_stub MessageFromBank  // PVAR_8004, PVAR_8005
    pl_CompareVarToValue PVAR_8000, 10
    pl_GoToIf 1, T1042_9_0165
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    pl_CloseMessage
    pl_stub ChooseCustomMessageWord  // Pearl 0x243 Unk0243 0, 32780, 32772: not translated yet
// ReturnToField: the field stayed open (ChooseCustomMessageWord: no Black 2 screen ran)
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T1042_9_021F
    pl_stub CallTVInterview  // Pearl 0x237 Unk0237 1, 32768, 32772, 32773: not translated yet
    pl_GoTo T1042_9_0214

T1042_9_0165:
    ListMenu_AnchorTopRight 31, 1, 0, 1, PVAR_8004  // Pearl InitLocalTextListMenu 1, 1, 0, 1, PVAR_8004
    ListMenuAdd 7, 65535, 1  // Pearl AddListMenuEntry 16, 1
    ListMenuAdd 8, 65535, 2  // Pearl AddListMenuEntry 17, 2
    ListMenuAdd 9, 65535, 3  // Pearl AddListMenuEntry 18, 3
    ListMenuAdd 10, 65535, 4  // Pearl AddListMenuEntry 19, 4
    ListMenuAdd 11, 65535, 5  // Pearl AddListMenuEntry 20, 5
    ListMenuAdd 12, 65535, 6  // Pearl AddListMenuEntry 21, 6
    ListMenuAdd 13, 65535, 7  // Pearl AddListMenuEntry 22, 7
    ListMenuAdd 14, 65535, 8  // Pearl AddListMenuEntry 23, 8
    ListMenuAdd 15, 65535, 9  // Pearl AddListMenuEntry 24, 9
    ListMenuAdd 16, 65535, 10  // Pearl AddListMenuEntry 25, 10
    ListMenuAdd 17, 65535, 11  // Pearl AddListMenuEntry 26, 11
    ListMenuAdd 18, 65535, 12  // Pearl AddListMenuEntry 27, 12
    ListMenuAdd 19, 65535, 13  // Pearl AddListMenuEntry 28, 13
    ListMenuAdd 20, 65535, 14  // Pearl AddListMenuEntry 29, 14
    ListMenuAdd 21, 65535, 15  // Pearl AddListMenuEntry 30, 15
    ListMenuAdd 22, 65535, 16  // Pearl AddListMenuEntry 31, 16
    ListMenuAdd 23, 65535, 17  // Pearl AddListMenuEntry 32, 17
    ListMenuShow
    pl_CompareVarToValue PVAR_8004, 65534
    pl_GoToIf 1, T1042_9_021F
    pl_stub CallTVInterview  // Pearl 0x237 Unk0237 1, 32768, 32772, 32773: not translated yet
    pl_GoTo T1042_9_0214

T1042_9_0214:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 24  // Pearl bank 562 line 2
    pl_WaitButton
    pl_GoTo T1042_9_022A

T1042_9_021F:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 25  // Pearl bank 562 line 1
    pl_WaitButton
    pl_GoTo T1042_9_022A

T1042_9_022A:
    pl_CloseMessage
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

PearlNoScript:
    VMHalt

PearlArrive:                      // arriving by a script warp with nothing after it: fade in, release
    FadeInBlack
    FadeWait
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0
