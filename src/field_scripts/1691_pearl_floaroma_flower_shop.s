// MAP_FLOAROMA_FLOWER_SHOP: Pearl script file 999, text bank 516. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-3: Pearl's; no warp continuations; 4: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P999_S1
    ScriptEntry P999_S2
    ScriptEntry P999_S3
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P999_S1:
P999_000E:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_0AAA
    pl_GoToIf 1, P999_0059
    pl_msg_talk 0
    pl_GetRandom PVAR_8004, 5
    pl_AddVar PVAR_8004, 149
    pl_SetVarFromValue PVAR_8005, 1
    pl_CanFitItem PVAR_8004, PVAR_8005, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P999_0064
    pl_SetFlag PFLAG_0AAA
    VMCall C205_17_S17  // CallCommonScript 2016 (Pearl file 205 script 17)
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P999_0059:
    pl_msg_talk 1
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P999_0064:
    VMCall C205_18_S18  // CallCommonScript 2017 (Pearl file 205 script 18)
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P999_S2:
P999_006E:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_0080
    pl_GoToIf 1, P999_009E
    pl_msg_talk 2
    pl_SetVarFromValue PVAR_8004, 448
    pl_SetVarFromValue PVAR_8005, 1
    pl_SetFlag PFLAG_0080
    VMCall C205_17_S17  // CallCommonScript 2016 (Pearl file 205 script 17)
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P999_009E:
    pl_msg_talk 3
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P999_S3:
P999_00A9:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
// Pearl 0x257 AccessoriesShop: Pearl's berry exchange (overlay 6) in Black 2's list menu, its lines (bank 516)
    MsgWinCloseAll
    pl_msg_sys 4
    pl_WaitButton
    WorkSetConst PL_TMP3, 0  // the Accessories that fit no more
    pl_CanFitAccessory 50, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit0
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit0:
    pl_CanFitAccessory 51, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit1
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit1:
    pl_CanFitAccessory 52, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit2
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit2:
    pl_CanFitAccessory 53, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit3
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit3:
    pl_CanFitAccessory 54, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit4
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit4:
    pl_CanFitAccessory 55, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit5
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit5:
    pl_CanFitAccessory 56, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit6
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit6:
    pl_CanFitAccessory 57, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit7
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit7:
    pl_CanFitAccessory 58, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit8
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit8:
    pl_CanFitAccessory 59, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit9
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit9:
    pl_CanFitAccessory 60, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit10
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit10:
    pl_CanFitAccessory 61, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit11
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit11:
    pl_CanFitAccessory 62, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit12
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit12:
    pl_CanFitAccessory 63, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit13
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit13:
    pl_CanFitAccessory 64, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit14
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit14:
    pl_CanFitAccessory 65, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit15
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit15:
    pl_CanFitAccessory 66, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit16
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit16:
    pl_CanFitAccessory 67, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit17
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit17:
    pl_CanFitAccessory 68, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit18
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit18:
    pl_CanFitAccessory 69, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit19
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit19:
    pl_CanFitAccessory 70, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit20
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit20:
    pl_CanFitAccessory 71, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccFit21
    WorkAdd PL_TMP3, 1
P999_00B1_AccFit21:
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_EQ, P999_00B1_AccAllDone
P999_00B1_AccMenu:
    pl_msg_sys 6
    ListMenu_AnchorTopRight 31, 1, 0, 1, PVAR_8004
    ListMenuAdd 21, 20, 0  // the Red Flower: 10 of item 164
    ListMenuAdd 23, 22, 1  // the Pink Flower: 10 of item 165
    ListMenuAdd 25, 24, 2  // the White Flower: 10 of item 166
    ListMenuAdd 27, 26, 3  // the Blue Flower: 30 of item 175
    ListMenuAdd 29, 28, 4  // the Orange Flower: 15 of item 176
    ListMenuAdd 31, 30, 5  // the Yellow Flower: 15 of item 177
    ListMenuAdd 33, 32, 6  // the Googly Specs: 20 of item 178
    ListMenuAdd 35, 34, 7  // the Black Specs: 20 of item 167
    ListMenuAdd 37, 36, 8  // the Gorgeous Specs: 40 of item 168
    ListMenuAdd 39, 38, 9  // the Sweet Candy: 30 of item 166
    ListMenuAdd 41, 40, 10  // the Confetti: 30 of item 164
    ListMenuAdd 43, 42, 11  // the Colored Parasol: 50 of item 176
    ListMenuAdd 45, 44, 12  // the Old Umbrella: 50 of item 180
    ListMenuAdd 47, 46, 13  // the Spotlight: 80 of item 178
    ListMenuAdd 49, 48, 14  // the Cape: 250 of item 175
    ListMenuAdd 51, 50, 15  // the Standing Mike: 80 of item 165
    ListMenuAdd 53, 52, 16  // the Surfboard: 180 of item 167
    ListMenuAdd 55, 54, 17  // the Carpet: 100 of item 179
    ListMenuAdd 57, 56, 18  // the Retro Pipe: 120 of item 180
    ListMenuAdd 59, 58, 19  // the Fluffy Bed: 150 of item 181
    ListMenuAdd 61, 60, 20  // the Mirror Ball: 250 of item 182
    ListMenuAdd 63, 62, 21  // the Photo Board: 200 of item 183
    ListMenuAdd 19, 65535, 65534  // EXIT (B answers 65534 too)
    ListMenuShow
    WorkCmpConst PVAR_8004, 22
    VMJumpIf CMP_LT, P999_00B1_AccPick
    MsgWinCloseAll
    pl_msg_sys 11
    pl_WaitButton
    VMJump P999_00B1_AccEnd
P999_00B1_AccPick:
    WorkCmpConst PVAR_8004, 0
    VMJumpIf CMP_NE, P999_00B1_AccRow0
    MsgWinCloseAll
    pl_msg_sys 64
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 164, 10, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 50, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 164, 10, PL_TMP
    pl_AddAccessory 50, 1
    pl_msg_sys 65
    pl_WaitButton
    pl_CanFitAccessory 50, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow0:
    WorkCmpConst PVAR_8004, 1
    VMJumpIf CMP_NE, P999_00B1_AccRow1
    MsgWinCloseAll
    pl_msg_sys 66
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 165, 10, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 51, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 165, 10, PL_TMP
    pl_AddAccessory 51, 1
    pl_msg_sys 67
    pl_WaitButton
    pl_CanFitAccessory 51, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow1:
    WorkCmpConst PVAR_8004, 2
    VMJumpIf CMP_NE, P999_00B1_AccRow2
    MsgWinCloseAll
    pl_msg_sys 68
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 166, 10, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 52, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 166, 10, PL_TMP
    pl_AddAccessory 52, 1
    pl_msg_sys 69
    pl_WaitButton
    pl_CanFitAccessory 52, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow2:
    WorkCmpConst PVAR_8004, 3
    VMJumpIf CMP_NE, P999_00B1_AccRow3
    MsgWinCloseAll
    pl_msg_sys 70
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 175, 30, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 53, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 175, 30, PL_TMP
    pl_AddAccessory 53, 1
    pl_msg_sys 71
    pl_WaitButton
    pl_CanFitAccessory 53, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow3:
    WorkCmpConst PVAR_8004, 4
    VMJumpIf CMP_NE, P999_00B1_AccRow4
    MsgWinCloseAll
    pl_msg_sys 72
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 176, 15, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 54, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 176, 15, PL_TMP
    pl_AddAccessory 54, 1
    pl_msg_sys 73
    pl_WaitButton
    pl_CanFitAccessory 54, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow4:
    WorkCmpConst PVAR_8004, 5
    VMJumpIf CMP_NE, P999_00B1_AccRow5
    MsgWinCloseAll
    pl_msg_sys 74
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 177, 15, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 55, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 177, 15, PL_TMP
    pl_AddAccessory 55, 1
    pl_msg_sys 75
    pl_WaitButton
    pl_CanFitAccessory 55, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow5:
    WorkCmpConst PVAR_8004, 6
    VMJumpIf CMP_NE, P999_00B1_AccRow6
    MsgWinCloseAll
    pl_msg_sys 76
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 178, 20, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 56, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 178, 20, PL_TMP
    pl_AddAccessory 56, 1
    pl_msg_sys 77
    pl_WaitButton
    pl_CanFitAccessory 56, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow6:
    WorkCmpConst PVAR_8004, 7
    VMJumpIf CMP_NE, P999_00B1_AccRow7
    MsgWinCloseAll
    pl_msg_sys 78
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 167, 20, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 57, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 167, 20, PL_TMP
    pl_AddAccessory 57, 1
    pl_msg_sys 79
    pl_WaitButton
    pl_CanFitAccessory 57, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow7:
    WorkCmpConst PVAR_8004, 8
    VMJumpIf CMP_NE, P999_00B1_AccRow8
    MsgWinCloseAll
    pl_msg_sys 80
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 168, 40, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 58, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 168, 40, PL_TMP
    pl_AddAccessory 58, 1
    pl_msg_sys 81
    pl_WaitButton
    pl_CanFitAccessory 58, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow8:
    WorkCmpConst PVAR_8004, 9
    VMJumpIf CMP_NE, P999_00B1_AccRow9
    MsgWinCloseAll
    pl_msg_sys 82
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 166, 30, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 59, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 166, 30, PL_TMP
    pl_AddAccessory 59, 1
    pl_msg_sys 83
    pl_WaitButton
    pl_CanFitAccessory 59, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow9:
    WorkCmpConst PVAR_8004, 10
    VMJumpIf CMP_NE, P999_00B1_AccRow10
    MsgWinCloseAll
    pl_msg_sys 84
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 164, 30, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 60, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 164, 30, PL_TMP
    pl_AddAccessory 60, 1
    pl_msg_sys 85
    pl_WaitButton
    pl_CanFitAccessory 60, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow10:
    WorkCmpConst PVAR_8004, 11
    VMJumpIf CMP_NE, P999_00B1_AccRow11
    MsgWinCloseAll
    pl_msg_sys 86
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 176, 50, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 61, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 176, 50, PL_TMP
    pl_AddAccessory 61, 1
    pl_msg_sys 87
    pl_WaitButton
    pl_CanFitAccessory 61, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow11:
    WorkCmpConst PVAR_8004, 12
    VMJumpIf CMP_NE, P999_00B1_AccRow12
    MsgWinCloseAll
    pl_msg_sys 88
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 180, 50, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 62, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 180, 50, PL_TMP
    pl_AddAccessory 62, 1
    pl_msg_sys 89
    pl_WaitButton
    pl_CanFitAccessory 62, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow12:
    WorkCmpConst PVAR_8004, 13
    VMJumpIf CMP_NE, P999_00B1_AccRow13
    MsgWinCloseAll
    pl_msg_sys 90
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 178, 80, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 63, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 178, 80, PL_TMP
    pl_AddAccessory 63, 1
    pl_msg_sys 91
    pl_WaitButton
    pl_CanFitAccessory 63, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow13:
    WorkCmpConst PVAR_8004, 14
    VMJumpIf CMP_NE, P999_00B1_AccRow14
    MsgWinCloseAll
    pl_msg_sys 92
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 175, 250, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 64, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 175, 250, PL_TMP
    pl_AddAccessory 64, 1
    pl_msg_sys 93
    pl_WaitButton
    pl_CanFitAccessory 64, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow14:
    WorkCmpConst PVAR_8004, 15
    VMJumpIf CMP_NE, P999_00B1_AccRow15
    MsgWinCloseAll
    pl_msg_sys 94
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 165, 80, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 65, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 165, 80, PL_TMP
    pl_AddAccessory 65, 1
    pl_msg_sys 95
    pl_WaitButton
    pl_CanFitAccessory 65, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow15:
    WorkCmpConst PVAR_8004, 16
    VMJumpIf CMP_NE, P999_00B1_AccRow16
    MsgWinCloseAll
    pl_msg_sys 96
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 167, 180, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 66, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 167, 180, PL_TMP
    pl_AddAccessory 66, 1
    pl_msg_sys 97
    pl_WaitButton
    pl_CanFitAccessory 66, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow16:
    WorkCmpConst PVAR_8004, 17
    VMJumpIf CMP_NE, P999_00B1_AccRow17
    MsgWinCloseAll
    pl_msg_sys 98
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 179, 100, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 67, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 179, 100, PL_TMP
    pl_AddAccessory 67, 1
    pl_msg_sys 99
    pl_WaitButton
    pl_CanFitAccessory 67, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow17:
    WorkCmpConst PVAR_8004, 18
    VMJumpIf CMP_NE, P999_00B1_AccRow18
    MsgWinCloseAll
    pl_msg_sys 100
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 180, 120, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 68, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 180, 120, PL_TMP
    pl_AddAccessory 68, 1
    pl_msg_sys 101
    pl_WaitButton
    pl_CanFitAccessory 68, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow18:
    WorkCmpConst PVAR_8004, 19
    VMJumpIf CMP_NE, P999_00B1_AccRow19
    MsgWinCloseAll
    pl_msg_sys 102
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 181, 150, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 69, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 181, 150, PL_TMP
    pl_AddAccessory 69, 1
    pl_msg_sys 103
    pl_WaitButton
    pl_CanFitAccessory 69, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow19:
    WorkCmpConst PVAR_8004, 20
    VMJumpIf CMP_NE, P999_00B1_AccRow20
    MsgWinCloseAll
    pl_msg_sys 104
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 182, 250, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 70, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 182, 250, PL_TMP
    pl_AddAccessory 70, 1
    pl_msg_sys 105
    pl_WaitButton
    pl_CanFitAccessory 70, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow20:
    WorkCmpConst PVAR_8004, 21
    VMJumpIf CMP_NE, P999_00B1_AccRow21
    MsgWinCloseAll
    pl_msg_sys 106
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P999_00B1_AccMenu
    ItemCheckAmount 183, 200, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFew
    pl_CanFitAccessory 71, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, P999_00B1_AccFull
    pl_msg_sys 8
    pl_WaitButton
    ItemSub 183, 200, PL_TMP
    pl_AddAccessory 71, 1
    pl_msg_sys 107
    pl_WaitButton
    pl_CanFitAccessory 71, 1, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, P999_00B1_AccMenu
    WorkAdd PL_TMP3, 1
    WorkCmpConst PL_TMP3, 22
    VMJumpIf CMP_LT, P999_00B1_AccMenu
    pl_msg_sys 13
    pl_WaitButton
    VMJump P999_00B1_AccAllDone
P999_00B1_AccRow21:
    VMJump P999_00B1_AccMenu
P999_00B1_AccFew:
    pl_msg_sys 9
    pl_WaitButton
    VMJump P999_00B1_AccMenu
P999_00B1_AccFull:
    pl_msg_sys 10
    pl_WaitButton
    VMJump P999_00B1_AccMenu
P999_00B1_AccAllDone:
    pl_msg_sys 5
    pl_WaitButton
P999_00B1_AccEnd:
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

// ---- Pearl global script 205:17 (a subroutine here)
C205_17_0336:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 7
    pl_GoToIf 1, C205_17_03B8
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, C205_17_03AC
    pl_CompareVarToValue PVAR_8008, 4
    pl_GoToIf 1, C205_17_03AC
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, C205_17_03AC
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, C205_17_03AC
    pl_CompareVarToValue PVAR_8008, 6
    pl_GoToIf 1, C205_17_03AC
    pl_CompareVarToValue PVAR_8008, 5
    pl_GoToIf 1, C205_17_03BE
    pl_CompareVarToValue PVAR_8008, 3
    pl_GoToIf 1, C205_17_03B2
    VMReturn  // End: the sub-script ends

C205_17_03AC:
    pl_PlayFanfare SEQ_ME_ITEM  // Pearl SEQ_FANFA4
    pl_Return

C205_17_03B2:
    pl_PlayFanfare SEQ_ME_WAZA  // Pearl SEQ_WAZA
    pl_Return

C205_17_03B8:
    pl_PlayFanfare SEQ_ME_KEYITEM  // Pearl SEQ_FANFA3
    pl_Return

C205_17_03BE:
    pl_PlayFanfare SEQ_ME_ITEM  // Pearl SEQ_FANFA2
    pl_Return

C205_17_S17:
C205_17_0978:
    pl_Call C205_17_0982
    pl_ReturnCommonScript
    VMReturn  // End: the sub-script ends

C205_17_0982:
    pl_Call C205_17_0336
    pl_AddItem PVAR_8004, PVAR_8005, PVAR_800C
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 7
    pl_CallIf 1, C205_17_09F4
    pl_CompareVarToValue PVAR_800C, 7
    pl_CallIf 5, C205_17_0A05
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 108  // Pearl bank 199 line 30
    pl_WaitButton
    pl_Return

C205_17_09F4:
    pl_BufferPlayerName 0
    pl_BufferItemName 1, PVAR_8004
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 109  // Pearl bank 199 line 28
    pl_GoTo C205_17_0A2B

C205_17_0A05:
    pl_CompareVarToValue PVAR_8005, 1
    pl_GoToIf 2, C205_17_0A1D
    pl_BufferItemName 0, PVAR_8004
    pl_GoTo C205_17_0A22

C205_17_0A1D:
    pl_BufferItemName 0, PVAR_8004  // GetItemNamePlural

C205_17_0A22:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 110  // Pearl bank 199 line 25
    pl_GoTo C205_17_0A2B

C205_17_0A2B:
    pl_WaitFanfare
    WorkSetConst PVAR_800C, 0  // CheckItemIsPlate PVAR_8004
    pl_CompareVarToValue PVAR_800C, 1
    pl_CallIf 1, C205_17_1330
    pl_BufferPlayerName 0
    pl_CompareVarToValue PVAR_8005, 1
    pl_GoToIf 2, C205_17_0A5B
    pl_BufferItemName 1, PVAR_8004
    pl_GoTo C205_17_0A60

C205_17_0A5B:
    pl_BufferItemName 1, PVAR_8004  // GetItemNamePlural

C205_17_0A60:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 7
    pl_GoToIf 1, C205_17_0AE7
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, C205_17_0AD6
    pl_CompareVarToValue PVAR_8008, 4
    pl_GoToIf 1, C205_17_0B2B
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, C205_17_0B1A
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, C205_17_0B3C
    pl_CompareVarToValue PVAR_8008, 6
    pl_GoToIf 1, C205_17_0AF8
    pl_CompareVarToValue PVAR_8008, 5
    pl_GoToIf 1, C205_17_0B09
    pl_CompareVarToValue PVAR_8008, 3
    pl_GoToIf 1, C205_17_0B4D
    VMReturn  // End: the sub-script ends

C205_17_0AD6:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0AE7:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0AF8:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0B09:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0B1A:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0B2B:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0B3C:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0B4D:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo C205_17_0B5E

C205_17_0B5E:
    pl_Return

C205_17_1330:
    pl_AddVar PVAR_4115, 1
    pl_CompareVarToValue PVAR_4115, 9
    pl_CallIf 4, C205_17_13AD
    pl_CompareVarToValue PVAR_4115, 1
    pl_CallIf 1, C205_17_13B5
    pl_CompareVarToValue PVAR_4115, 2
    pl_CallIf 1, C205_17_13BA
    pl_CompareVarToValue PVAR_4115, 3
    pl_CallIf 1, C205_17_13BF
    pl_CompareVarToValue PVAR_4115, 4
    pl_CallIf 1, C205_17_13C4
    pl_CompareVarToValue PVAR_4115, 5
    pl_CallIf 1, C205_17_13C9
    pl_CompareVarToValue PVAR_4115, 6
    pl_CallIf 1, C205_17_13CE
    pl_CompareVarToValue PVAR_4115, 7
    pl_CallIf 1, C205_17_13D3
    pl_CompareVarToValue PVAR_4115, 8
    pl_CallIf 1, C205_17_13D8
    pl_Return

C205_17_13AD:
    pl_SetVarFromValue PVAR_4115, 1
    pl_Return

C205_17_13B5:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 111  // Pearl bank 199 line 110
    pl_Return

C205_17_13BA:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 112  // Pearl bank 199 line 111
    pl_Return

C205_17_13BF:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 113  // Pearl bank 199 line 112
    pl_Return

C205_17_13C4:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 114  // Pearl bank 199 line 113
    pl_Return

C205_17_13C9:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 115  // Pearl bank 199 line 114
    pl_Return

C205_17_13CE:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 116  // Pearl bank 199 line 115
    pl_Return

C205_17_13D3:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 117  // Pearl bank 199 line 116
    pl_Return

C205_17_13D8:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 118  // Pearl bank 199 line 117
    pl_Return

// ---- Pearl global script 205:18 (a subroutine here)
C205_18_S18:
C205_18_0B60:
    pl_Call C205_18_0B6A
    pl_ReturnCommonScript
    VMReturn  // End: the sub-script ends

C205_18_0B6A:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 119  // Pearl bank 199 line 27
    pl_WaitButton
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
