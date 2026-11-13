// MAP_ROUTE_212_NORTH: Pearl script file 418, text bank 438. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-10: Pearl's; no warp continuations; 11: PearlArrive; 108: Pearl 2008, 49: Pearl 2027, 54: Pearl 2800, 92: Pearl 10000
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P418_S1
    ScriptEntry P418_S2
    ScriptEntry P418_S3
    ScriptEntry P418_S4
    ScriptEntry P418_S5
    ScriptEntry P418_S6
    ScriptEntry P418_S7
    ScriptEntry P418_S8
    ScriptEntry P418_S9
    ScriptEntry P418_S10
    ScriptEntry PearlArrive
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
    ScriptEntry PearlProxy_2027
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlNoScript
    ScriptEntry PearlProxy_2800
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
    ScriptEntry PearlProxy_10000
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
    ScriptEntry PearlProxy_2008
    ScriptEntriesEnd

P418_S10:
P418_002A:
    pl_GetTimeOfDay PVAR_4000
    pl_CompareVarToValue PVAR_4000, 0
    pl_GoToIf 1, P418_0071
    pl_CompareVarToValue PVAR_4000, 1
    pl_GoToIf 1, P418_0071
    pl_CompareVarToValue PVAR_4000, 2
    pl_GoToIf 1, P418_0071
    pl_CompareVarToValue PVAR_4000, 3
    pl_GoToIf 1, P418_0093
    pl_CompareVarToValue PVAR_4000, 4
    pl_GoToIf 1, P418_0093
    pl_End

P418_0071:
    pl_ClearFlag PFLAG_027E
    pl_ClearFlag PFLAG_0280
    pl_ClearFlag PFLAG_0282
    pl_ClearFlag PFLAG_0284
    pl_SetFlag PFLAG_027F
    pl_SetFlag PFLAG_0281
    pl_SetFlag PFLAG_0283
    pl_SetFlag PFLAG_0285
    pl_End

P418_0093:
    pl_ClearFlag PFLAG_027F
    pl_ClearFlag PFLAG_0281
    pl_ClearFlag PFLAG_0283
    pl_ClearFlag PFLAG_0285
    pl_SetFlag PFLAG_027E
    pl_SetFlag PFLAG_0280
    pl_SetFlag PFLAG_0282
    pl_SetFlag PFLAG_0284
    pl_End

P418_S1:
P418_00B5:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 0
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P418_S2:
P418_00C8:
    pl_sign 6, 3  // Pearl sign type 1
// SetSignpostCommand: done by pl_sign
// WaitForSignpostDone: done by pl_sign
    WorkSetConst PVAR_800C, 0  // GetSignpostInput: Black 2's sign closes on A/B
// CallCommonScript 2000 (Pearl closes the sign; X opens the menu): done by pl_sign
    pl_End

P418_S3:
P418_00DF:
    pl_sign 7, 2  // Pearl sign type 2
// SetSignpostCommand: done by pl_sign
// WaitForSignpostDone: done by pl_sign
    WorkSetConst PVAR_800C, 0  // GetSignpostInput: Black 2's sign closes on A/B
// CallCommonScript 2000 (Pearl closes the sign; X opens the menu): done by pl_sign
    pl_End

P418_S4:
P418_00F6:
// DrawSignpostTextBox type 3 (the window opens with the next sign message)
// SetSignpostCommand: done by pl_sign
// WaitForSignpostDone: done by pl_sign
    pl_sign 8, 0  // Pearl sign type 3
// CallCommonScript 2000 (Pearl closes the sign; X opens the menu): done by pl_sign
    pl_End

P418_S5:
P418_010B:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 1
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P418_S6:
P418_011E:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 2
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P418_S7:
P418_0131:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 3
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P418_S8:
P418_0144:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 4
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P418_S9:
P418_0157:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 5
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

PearlProxy_2008:                  // Pearl global script 2008 (run by this zone's events)
    VMCall C205_9_S9
    VMHalt

PearlProxy_2027:                  // Pearl global script 2027 (run by this zone's events)
    VMCall T205_28_S28
    VMHalt

PearlProxy_2800:                  // Pearl global script 2800 (run by this zone's events)
    VMCall T378_1_S1
    VMHalt

PearlProxy_10000:                  // Pearl global script 10000 (run by this zone's events)
    VMCall T375_1_S1
    VMHalt

// ---- Pearl global script 205:9 (a subroutine here)
C205_9_S9:
C205_9_0571:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_CheckItem 94, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 5, C205_9_05B9
    pl_GetHoneyTreeStatus PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, C205_9_05E6
    pl_CompareVarToValue PVAR_800C, 2
    pl_GoToIf 1, C205_9_05F1
    pl_CompareVarToValue PVAR_800C, 3
    pl_GoToIf 1, C205_9_067B
    VMReturn  // End: the sub-script ends

C205_9_05B9:
    pl_GetHoneyTreeStatus PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, C205_9_05FC
    pl_CompareVarToValue PVAR_800C, 2
    pl_GoToIf 1, C205_9_0605
    pl_CompareVarToValue PVAR_800C, 3
    pl_GoToIf 1, C205_9_067B
    VMReturn  // End: the sub-script ends

C205_9_05E6:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 9  // Pearl bank 199 line 46
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

C205_9_05F1:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 10  // Pearl bank 199 line 48
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

C205_9_05FC:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 11  // Pearl bank 199 line 47
    pl_GoTo C205_9_0642

C205_9_0605:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 12  // Pearl bank 199 line 49
    pl_GoTo C205_9_0642

C205_9_0629:
    pl_CheckItem 94, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 5, C205_9_0642
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

C205_9_0642:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 13  // Pearl bank 199 line 50
    pl_ShowYesNoMenu PVAR_800C
    pl_CloseMessage
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, C205_9_065C
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

C205_9_065C:
    pl_RemoveItem 94, 1, PVAR_800C
// IncrementTrainerScore2 1: nothing in Black 2 (Pearl's trainer-card score (Black 2 keeps its own records))
    pl_SlatherHoneyTree
    pl_WaitTime 10, PVAR_800C
    pl_msg_sys 14  // Pearl bank 199 line 51
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

C205_9_067B:
    pl_StartHoneyTreeBattle
    pl_CheckWonBattle PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, C205_9_0696
    pl_StopHoneyTreeShaking
    pl_GoTo C205_9_0629

C205_9_0696:
    pl_BlackOutFromBattle
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

// ---- Pearl global script 205:28 (a subroutine here)
T205_28_S28:
T205_28_1222:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 15  // Pearl bank 199 line 67
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

// ---- Pearl global script 378:1 (a subroutine here)
T378_1_S1:
T378_1_0012:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_GetBerry 1, PVAR_8000  // GetBerryItemID
    pl_GetBerry 4, PVAR_8001  // GetBerryYield
    pl_GetBerry 0, PVAR_800C  // GetBerryGrowthStage
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, T378_1_033E
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, T378_1_0082
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, T378_1_00B9
    pl_CompareVarToValue PVAR_8008, 3
    pl_GoToIf 1, T378_1_00EE
    pl_CompareVarToValue PVAR_8008, 4
    pl_GoToIf 1, T378_1_0123
    pl_CompareVarToValue PVAR_8008, 5
    pl_GoToIf 1, T378_1_021B
    pl_GoTo T378_1_033E

T378_1_0082:
    pl_Call T378_1_0158
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_00A6
    WordSetItemNameWithArticle 0, PVAR_8000
// CapitalizeFirstChar: nothing in Black 2
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 16  // Pearl bank 350 line 13
    pl_GoTo T378_1_01F2

T378_1_00A6:
    WordSetItemNameWithArticle 0, PVAR_8000
// CapitalizeFirstChar: nothing in Black 2
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 17  // Pearl bank 350 line 31
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_00B9:
    pl_Call T378_1_0158
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_00DC
    pl_BufferBerryName 0, PVAR_8000  // Pearl's count PVAR_8001: its name has one form
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 18  // Pearl bank 350 line 14
    pl_GoTo T378_1_01F2

T378_1_00DC:
    pl_BufferBerryName 0, PVAR_8000  // Pearl's count PVAR_8001: its name has one form
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 19  // Pearl bank 350 line 32
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_00EE:
    pl_Call T378_1_0158
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_0111
    pl_BufferBerryName 0, PVAR_8000  // Pearl's count PVAR_8001: its name has one form
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 20  // Pearl bank 350 line 15
    pl_GoTo T378_1_01F2

T378_1_0111:
    pl_BufferBerryName 0, PVAR_8000  // Pearl's count PVAR_8001: its name has one form
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 21  // Pearl bank 350 line 33
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_0123:
    pl_Call T378_1_0158
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_0146
    pl_BufferBerryName 0, PVAR_8000  // Pearl's count PVAR_8001: its name has one form
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 22  // Pearl bank 350 line 16
    pl_GoTo T378_1_01F2

T378_1_0146:
    pl_BufferBerryName 0, PVAR_8000  // Pearl's count PVAR_8001: its name has one form
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 23  // Pearl bank 350 line 34
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_0158:
    pl_GetPlayerDir PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 5, T378_1_0186
    pl_CheckItem 448, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_0186
    pl_SetVarFromValue PVAR_800C, 1
    pl_Return

T378_1_0186:
    pl_SetVarFromValue PVAR_800C, 0
    pl_Return

T378_1_018E:
    pl_CheckItem 95, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_01EA
    pl_CheckItem 96, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_01EA
    pl_CheckItem 97, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_01EA
    pl_CheckItem 98, 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_01EA
    pl_SetVarFromValue PVAR_800C, 0
    pl_Return

T378_1_01EA:
    pl_SetVarFromValue PVAR_800C, 1
    pl_Return

T378_1_01F2:
    pl_msg_talk 24  // Pearl bank 350 line 17
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_053A
    pl_CloseMessage
    pl_WaterBerry
    pl_msg_talk 25  // Pearl bank 350 line 20
    pl_WaitButton
// SetBerryWateringState 1: nothing to end
    pl_GoTo T378_1_053A

T378_1_021B:
    pl_BufferNumber 1, PVAR_8001
    pl_CompareVarToValue PVAR_8001, 1
    pl_GoToIf 2, T378_1_023B
    WordSetItemNameWithArticle 0, PVAR_8000
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 26  // Pearl bank 350 line 35
    pl_GoTo T378_1_0243

T378_1_023B:
    pl_BufferItemName 0, PVAR_8000  // GetItemNamePlural
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 27  // Pearl bank 350 line 21

T378_1_0243:
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_02F7
    pl_CanFitItem PVAR_8000, PVAR_8001, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_02CF
    pl_BufferNumber 1, PVAR_8001
    pl_CompareVarToValue PVAR_8001, 1
    pl_GoToIf 2, T378_1_0289
    pl_BufferItemName 0, PVAR_8000
    pl_msg_talk 28  // Pearl bank 350 line 37
    pl_GoTo T378_1_0291

T378_1_0289:
    pl_BufferItemName 0, PVAR_8000  // GetItemNamePlural
    pl_msg_talk 29  // Pearl bank 350 line 25

T378_1_0291:
    pl_PlayFanfare SEQ_ME_KINOMI  // Pearl SEQ_KINOMI
    pl_WaitFanfare
    pl_HarvestBerry
    pl_BufferPlayerName 0
    pl_CompareVarToValue PVAR_8001, 1
    pl_GoToIf 2, T378_1_02B4
    pl_BufferItemName 1, PVAR_8000
    pl_GoTo T378_1_02B9

T378_1_02B4:
    pl_BufferItemName 1, PVAR_8000  // GetItemNamePlural

T378_1_02B9:
    pl_GetItemPocket PVAR_8000, PVAR_800C
    pl_BufferPocketName 3, PVAR_800C
    pl_msg_talk 30  // Pearl bank 350 line 27
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_02CF:
    pl_CompareVarToValue PVAR_8001, 1
    pl_GoToIf 2, T378_1_02E7
    pl_BufferItemName 0, PVAR_8000
    pl_GoTo T378_1_02EC

T378_1_02E7:
    pl_BufferItemName 0, PVAR_8000  // GetItemNamePlural

T378_1_02EC:
    pl_msg_talk 31  // Pearl bank 350 line 26
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_02F7:
    pl_Call T378_1_0158
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_0310
    pl_GoTo T378_1_01F2

T378_1_0310:
    pl_BufferPlayerName 0
    pl_CompareVarToValue PVAR_8001, 1
    pl_GoToIf 2, T378_1_032E
    pl_BufferItemName 1, PVAR_8000
    pl_msg_talk 32  // Pearl bank 350 line 36
    pl_GoTo T378_1_0336

T378_1_032E:
    pl_BufferItemName 1, PVAR_8000  // GetItemNamePlural
    pl_msg_talk 33  // Pearl bank 350 line 24

T378_1_0336:
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_033E:
    pl_GetBerry 2, PVAR_800C  // GetBerryMulchType
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_0374
    pl_CheckBerriesInBag PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_054B
    pl_GetBerry 2, PVAR_800C  // GetBerryMulchType
    pl_BufferItemName 0, PVAR_800C
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 34  // Pearl bank 350 line 1
    pl_GoTo T378_1_04DA

T378_1_0374:
    pl_GetPlayerDir PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 5, T378_1_0540
    pl_Call T378_1_018E
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_03B4
    pl_CheckBerriesInBag PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_0540
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 35  // Pearl bank 350 line 0
    pl_GoTo T378_1_04DA

T378_1_03B4:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 35  // Pearl bank 350 line 0
    pl_CheckBerriesInBag PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_0413
    ListMenu_AnchorTopRight 31, 1, 0, 1, PVAR_800C  // Pearl InitLocalTextMenu 1, 1, 0, 1, PVAR_800C
    ListMenuAdd 36, 65535, 0  // Pearl AddMenuEntryImm 2, 0
    ListMenuAdd 37, 65535, 1  // Pearl AddMenuEntryImm 3, 1
    ListMenuAdd 38, 65535, 2  // Pearl AddMenuEntryImm 4, 2
    ListMenuShow
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, T378_1_042D
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, T378_1_04EE
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, T378_1_053A
    pl_GoTo T378_1_053A

T378_1_0413:
    pl_msg_talk 39  // Pearl bank 350 line 5
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_042D
    pl_GoTo T378_1_053A

T378_1_042D:
    pl_CloseMessage
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    pl_OpenBerryBag 0
// RestoreOverworld: Black 2's CallPlaceSelect reopened the field itself
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_GetBagSelection PVAR_8005
    pl_SetVarFromVar PVAR_8008, PVAR_8005
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, T378_1_053C
    pl_CompareVarToValue PVAR_8008, 95
    pl_GoToIf 1, T378_1_049D
    pl_CompareVarToValue PVAR_8008, 96
    pl_GoToIf 1, T378_1_049D
    pl_CompareVarToValue PVAR_8008, 97
    pl_GoToIf 1, T378_1_049D
    pl_CompareVarToValue PVAR_8008, 98
    pl_GoToIf 1, T378_1_049D
    pl_GoTo T378_1_053C

T378_1_049D:
    pl_RemoveItem PVAR_8005, 1, PVAR_8004
    pl_SetBerryMulch PVAR_8005
    pl_CheckBerriesInBag PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_04CA
    pl_BufferItemName 0, PVAR_8005
    pl_msg_talk 40  // Pearl bank 350 line 11
    pl_GoTo T378_1_04DA

T378_1_04CA:
    pl_BufferItemName 0, PVAR_8005
    pl_msg_talk 41  // Pearl bank 350 line 30
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_04DA:
    pl_msg_talk 42  // Pearl bank 350 line 8
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, T378_1_053A

T378_1_04EE:
    pl_CloseMessage
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    pl_OpenBerryBag 3
// RestoreOverworld: Black 2's CallPlaceSelect reopened the field itself
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_GetBagSelection PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T378_1_053C
    pl_BufferItemName 0, PVAR_800C
    pl_msg_talk 43  // Pearl bank 350 line 12
    pl_WaitButton
    pl_RemoveItem PVAR_800C, 1, PVAR_8004
    pl_PlantBerry PVAR_800C
    pl_GoTo T378_1_053A

T378_1_053A:
    pl_CloseMessage

T378_1_053C:
    pl_ReleaseAll
    VMReturn  // End: the sub-script ends

T378_1_0540:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 44  // Pearl bank 350 line 28
    pl_WaitButton
    pl_GoTo T378_1_053A

T378_1_054B:
    pl_GetBerry 2, PVAR_800C  // GetBerryMulchType
    pl_BufferItemName 0, PVAR_800C
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 45  // Pearl bank 350 line 29
    pl_WaitButton
    pl_GoTo T378_1_053A

// ---- Pearl global script 375:1 (a subroutine here)
T375_1_S1:
T375_1_0042:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    PokePartyHasMoveAny PVAR_800C, 15  // FindPartySlotWithMove: the slot, 6 = none (the same in both games)
    pl_CompareVarToValue PVAR_800C, 6
    pl_GoToIf 1, T375_1_008E
    pl_CheckBadgeAcquired 1, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T375_1_008E
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 46  // Pearl bank 334 line 0
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, T375_1_009D
    pl_CloseMessage
    pl_GoTo T375_1_055B

T375_1_008E:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 47  // Pearl bank 334 line 2
    pl_WaitButton
    pl_CloseMessage
    pl_GoTo T375_1_055B

T375_1_009D:
    PokePartyHasMoveAny PVAR_800C, 15  // FindPartySlotWithMove: the slot, 6 = none (the same in both games)
    pl_SetVarFromVar PVAR_8004, PVAR_800C
    pl_BufferPartyMonNickname 0, PVAR_800C
    pl_msg_sys 48  // Pearl bank 334 line 1
    pl_CloseMessage
    pl_PlayHMCutIn PVAR_8004
// StartDestroyObstacleAnimation 0: no animation in Black 2
    pl_SetVarFromValue PVAR_8005, 1  // the animation is "over" at once (the script waits for it)
    pl_WaitTime 7, PVAR_800C
    pl_RemoveObject PVAR_800D, 0
    WorkSetConst PVAR_8004, 367  // GetCurrentMapID: Pearl map 367
// CreateJournalEvent 19, 32772, 0, 0, 0: nothing in Black 2 (Black 2 has no journal)

T375_1_00D7:
    pl_WaitTime 1, PVAR_800C
    pl_CompareVarToValue PVAR_8005, 0
    pl_GoToIf 1, T375_1_00D7
    pl_GoTo T375_1_055B

T375_1_055B:
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
