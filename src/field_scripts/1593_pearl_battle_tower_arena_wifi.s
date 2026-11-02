// MAP_BATTLE_TOWER_ARENA_WIFI: Pearl script file 363, text bank 285. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-4: Pearl's; 5: after a Warp, 6: after a Warp; 7: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P363_S1
    ScriptEntry P363_S2
    ScriptEntry P363_S3
    ScriptEntry P363_S4
    ScriptEntry W359_00A9_S
    ScriptEntry W361_00AD_S
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P363_S1:
P363_0012:
    pl_CompareVarToValue PVAR_40DE, 0
    pl_GoToIf 1, P363_0054
    pl_SetFlag PFLAG_0208
    pl_SetFlag PFLAG_0209
    pl_SetVarFromValue PVAR_4000, 0  // GetCurNetID: no link
    pl_CompareVarToValue PVAR_4000, 1
    pl_GoToIf 1, P363_0056
    pl_TowerPlayerCode PVAR_4000  // Pearl tower function 55: the player's sprite
    pl_SetVarFromVar PVAR_4020, PVAR_4000
    pl_TowerPartnerCode PVAR_4000  // Pearl tower function 55
    pl_SetVarFromVar PVAR_4021, PVAR_4000

P363_0054:
    pl_End

P363_0056:
    pl_TowerPlayerCode PVAR_4000  // Pearl tower function 55: the player's sprite
    pl_SetVarFromVar PVAR_4021, PVAR_4000
    pl_TowerPartnerCode PVAR_4000  // Pearl tower function 55
    pl_SetVarFromVar PVAR_4020, PVAR_4000
    pl_End

P363_S2:
P363_0074:
    pl_CompareVarToValue PVAR_40DE, 0
    pl_CallIf 5, P363_0090
    pl_CompareVarToValue PVAR_40DE, 3
    pl_GoToIf 1, P363_009E

P363_008E:
    pl_End

P363_0090:
    pl_TowerActorVisible PL_PLAYER, 0  // Pearl HideObject 255 (no actor command)
    pl_stub MoveCamera  // Pearl 0x06B Unk006B 8, 0, 0: not translated yet
    pl_Return

P363_009E:
    pl_SetPosition 2, 5, 0, 5, 3
    pl_SetPosition 3, 5, 0, 6, 3
    pl_GoTo P363_008E

P363_00BE:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 2
    pl_PlayFanfare SEQ_ME_ASA  // Pearl SEQ_ASA
    pl_WaitFanfare
    pl_HealParty
    pl_Return

P363_00CB:
    BSubwayCmd_Tool 21, 0, 0, PVAR_800C  // Pearl tower function 43
    pl_CompareVarToValue PVAR_800C, 3
    pl_GoToIf 1, P363_0114
    pl_WaitTime 30, PVAR_800C
    pl_SetVarFromValue PVAR_40D8, 1
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 26  // the rest of this Pearl script runs there (continuation 26)
    pl_Warp 443, 7, 6, 0  // Pearl map 326 (MAP_BATTLE_TOWER_LOBBY)
    pl_ReleaseAll
    pl_End

P363_0114:
    pl_WaitTime 30, PVAR_800C
    pl_SetVarFromValue PVAR_40D8, 1
    pl_stub ClearReceivedTempDataAllPlayers  // Pearl 0x136 Unk0136 : not translated yet
    pl_stub 135  // Pearl 0x135 Unk0135 6: not translated yet
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    pl_stub ClearReceivedTempDataAllPlayers  // Pearl 0x136 Unk0136 : not translated yet
    pl_stub 135  // Pearl 0x135 Unk0135 8: not translated yet
    pl_stub EndCommunication  // Pearl 0x150 Unk0150 : not translated yet
    RTReserveScript 27  // the rest of this Pearl script runs there (continuation 27)
    pl_Warp 443, 7, 6, 0  // Pearl map 326 (MAP_BATTLE_TOWER_LOBBY)
    pl_ReleaseAll
    pl_End

P363_S3:
P363_0156:
    pl_LockAll
    pl_SetVarFromValue PVAR_40DE, 3
    pl_Call P363_0485
    BSubwayCmd_Tool 21, 0, 0, PVAR_800C  // Pearl tower function 43
    pl_CompareVarToValue PVAR_800C, 3
    pl_GoToIf 1, P363_039B
    pl_GoTo P363_02B0

P363_S4:
P363_0181:
    pl_LockAll
    pl_SetVarFromValue PVAR_40DE, 3
    pl_Call P363_0485
    pl_Call P363_0499
    pl_GoTo P363_02E8

P363_019D:
    BSubwayCmd_Tool 307, 0, 0, 0  // Pearl tower function 40
    pl_Call P363_04BD
    pl_Call P363_0521
    BSubwayCmd_Tool 352, 0, 4, 0  // PrintBattleTowerIntroMessage
    pl_WaitABPress
    pl_CloseMessage
    pl_Call P363_052D
    BSubwayCmd_Tool 352, 1, 5, 0  // PrintBattleTowerIntroMessage
    pl_WaitABPress
    pl_CloseMessage
    pl_Call P363_04FD
    BSubwayCmd_Tool 309, 0, 0, 0  // Pearl tower function 42: the battle
    BSubwayCmd_Tool 332, 0, 0, PVAR_800C
    BSubwayCmd_Tool 347, 0, 0, 0
    pl_SetVarFromVar PVAR_8004, PVAR_800C
    pl_Return

P363_01DF:
    BSubwayCmd_Tool 307, 0, 0, 0  // Pearl tower function 40
    pl_Call P363_04BD
    pl_Call P363_0521
    BSubwayCmd_Tool 352, 0, 4, 0  // PrintBattleTowerIntroMessage
    pl_WaitTime 30, PVAR_800C
    pl_CloseMessage
    pl_Call P363_052D
    BSubwayCmd_Tool 352, 1, 5, 0  // PrintBattleTowerIntroMessage
    pl_WaitTime 30, PVAR_800C
    pl_CloseMessage
    pl_Call P363_04FD
    pl_stub ClearReceivedTempDataAllPlayers  // Pearl 0x136 Unk0136 : not translated yet
    pl_stub 135  // Pearl 0x135 Unk0135 4: not translated yet
    BSubwayCmd_Tool 309, 0, 0, 0  // Pearl tower function 42: the battle
    BSubwayCmd_Tool 332, 0, 0, PVAR_800C
    BSubwayCmd_Tool 347, 0, 0, 0
    pl_SetVarFromVar PVAR_8004, PVAR_800C
    pl_Return

P363_022F:
    BSubwayCmd_Tool 304, 0, 0, 0  // Pearl tower function 37
    pl_SetVarFromValue PVAR_4000, 0
    pl_GoTo P363_00CB

P363_0245:
    BSubwayCmd_Tool 305, 0, 0, 0  // Pearl tower function 38
    pl_SetVarFromValue PVAR_4000, 1
    pl_GoTo P363_00CB

P363_025B:
    pl_SetVarFromValue PVAR_40D8, 2
    BSubwayCmd_Tool 306, 0, 0, 0  // Pearl tower function 39: the play block keeps the challenge
    FieldSetNextZone 443, 1, 7, 0, 6
    FlagSet 2405
    Plugin1_Cmd1002  // FreeBattleTower
    pl_msg_sys 0
// ShowSavingIcon: nothing in Black 2
    SaveDataWrite PVAR_800C
// HideSavingIcon: nothing in Black 2
    pl_PlaySE SEQ_SE_SAVE  // Pearl SEQ_SE_DP_SAVE
    pl_WaitSE SEQ_SE_SAVE  // Pearl SEQ_SE_DP_SAVE
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    pl_CloseMessage
    BSubwayCmd_Tool 1, 0, 0, 0  // Pearl tower function 2
    pl_End

P363_0296:
    pl_GoTo P363_022F

P363_029E:
    BSubwayCmd_Tool 357, 0, 0, PVAR_800C  // Pearl tower function 34
    BSubwayCmd_Tool 303, 0, 0, PVAR_800C  // Pearl tower function 35
    pl_Return

P363_02B0:
    pl_Call P363_019D
    pl_CompareVarToValue PVAR_8004, 0
    pl_GoToIf 1, P363_022F
    pl_Call P363_029E
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P363_0245
    pl_Call P363_0539
    pl_Call P363_055D
    pl_Call P363_00BE

P363_02E8:
    BSubwayCmd_Tool 8, 0, 0, PVAR_8004  // Pearl tower function 33
    pl_BufferNumber 0, PVAR_8004
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 3
    ListMenu_AnchorTopRight 31, 11, 0, 0, PVAR_800C  // Pearl InitGlobalTextListMenu 21, 11, 0, 0, PVAR_800C
    ListMenuAdd 8, 65535, 0  // Pearl AddListMenuEntry 146, 0
    ListMenuAdd 9, 65535, 1  // Pearl AddListMenuEntry 147, 1
    ListMenuAdd 10, 65535, 2  // Pearl AddListMenuEntry 148, 2
    ListMenuShow
    pl_CloseMessage
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, P363_0351
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, P363_035F
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, P363_037D
    pl_GoTo P363_0351

P363_0351:
    pl_Call P363_0581
    pl_GoTo P363_02B0

P363_035F:
    pl_msg_sys 4
    pl_ShowYesNoMenu PVAR_800C
    pl_CloseMessage
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P363_025B
    pl_GoTo P363_02E8

P363_037D:
    pl_msg_sys 5
    pl_ShowYesNoMenu PVAR_800C
    pl_CloseMessage
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P363_0296
    pl_GoTo P363_02E8

P363_039B:
    pl_Call P363_01DF
    pl_CompareVarToValue PVAR_8004, 0
    pl_GoToIf 1, P363_022F
    pl_Call P363_029E
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P363_0245
    pl_Call P363_0539
    pl_Call P363_055D
    pl_Call P363_00BE

P363_03D3:
    BSubwayCmd_Tool 8, 0, 0, PVAR_8004  // Pearl tower function 33
    pl_BufferNumber 0, PVAR_8004
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 3
    ListMenu_AnchorTopRight 31, 13, 0, 0, PVAR_800C  // Pearl InitGlobalTextListMenu 21, 13, 0, 0, PVAR_800C
    ListMenuAdd 8, 65535, 0  // Pearl AddListMenuEntry 146, 0
    ListMenuAdd 10, 65535, 1  // Pearl AddListMenuEntry 148, 1
    ListMenuShow
    pl_CloseMessage
    pl_SetVarFromValue PVAR_4000, 0
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P363_044A

P363_0412:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 7
    pl_stub ClearReceivedTempDataAllPlayers  // Pearl 0x136 Unk0136 : not translated yet
    pl_stub 135  // Pearl 0x135 Unk0135 5: not translated yet
    pl_stub 1E1  // Pearl 0x1E1 Unk01E1 2, 16384: not translated yet
    pl_stub 1E2  // Pearl 0x1E2 Unk01E2 2, 16384: not translated yet
    pl_CloseMessage
    pl_SetVarFromVar PVAR_8008, PVAR_4000
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, P363_046C
    pl_Call P363_0581
    pl_GoTo P363_039B

P363_044A:
    pl_msg_sys 5
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P363_03D3
    pl_SetVarFromValue PVAR_4000, 1
    pl_GoTo P363_0412

P363_046C:
    pl_msg_sys 6
    pl_WaitTime 30, PVAR_800C
    pl_stub ClearReceivedTempDataAllPlayers  // Pearl 0x136 Unk0136 : not translated yet
    pl_stub 135  // Pearl 0x135 Unk0135 7: not translated yet
    pl_CloseMessage
    pl_GoTo P363_0296

P363_0485:
    pl_ApplyMovement 2, P363_05A8
    pl_ApplyMovement 3, P363_05BC
    pl_WaitMovement
    pl_Return

P363_0499:
    pl_ApplyMovement 0, P363_063C
    pl_ApplyMovement 1, P363_063C
    pl_ApplyMovement 2, P363_065C
    pl_ApplyMovement 3, P363_065C
    pl_WaitMovement
    pl_Return

P363_04BD:
    BSubwayCmd_Tool 308, 0, 0, PVAR_800C  // Pearl tower function 41
    pl_SetVarFromVar PVAR_4022, PVAR_800C
    BSubwayCmd_Tool 308, 1, 0, PVAR_800C  // Pearl tower function 41
    pl_SetVarFromVar PVAR_4023, PVAR_800C
    pl_ClearFlag PFLAG_0208
    pl_ClearFlag PFLAG_0209
    pl_AddObject 5
    pl_AddObject 4
    pl_ApplyMovement 5, P363_05D0
    pl_ApplyMovement 4, P363_05E4
    pl_WaitMovement
    pl_Return

P363_04FD:
    pl_ApplyMovement 2, P363_05F8
    pl_ApplyMovement 3, P363_05F8
    pl_ApplyMovement 5, P363_0600
    pl_ApplyMovement 4, P363_0600
    pl_WaitMovement
    pl_Return

P363_0521:
    pl_ApplyMovement 5, P363_0608
    pl_WaitMovement
    pl_Return

P363_052D:
    pl_ApplyMovement 4, P363_0608
    pl_WaitMovement
    pl_Return

P363_0539:
    pl_ApplyMovement 5, P363_0610
    pl_ApplyMovement 4, P363_0620
    pl_WaitMovement
    pl_SetFlag PFLAG_0208
    pl_SetFlag PFLAG_0209
    pl_RemoveObject 5, PFLAG_0208
    pl_RemoveObject 4, PFLAG_0209
    pl_Return

P363_055D:
    pl_ApplyMovement 2, P363_0630
    pl_ApplyMovement 3, P363_0630
    pl_ApplyMovement 0, P363_063C
    pl_ApplyMovement 1, P363_063C
    pl_WaitMovement
    pl_Return

P363_0581:
    pl_ApplyMovement 2, P363_0644
    pl_ApplyMovement 3, P363_0644
    pl_ApplyMovement 0, P363_064C
    pl_ApplyMovement 1, P363_064C
    pl_WaitMovement
    pl_Return

    .balign 4, 0
P363_05A8:
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 14, 3  // WALK_NORMAL_WEST
    Move 12, 3  // WALK_NORMAL_NORTH
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P363_05BC:
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 14, 4  // WALK_NORMAL_WEST
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P363_05D0:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 15, 3  // WALK_NORMAL_EAST
    Move 13, 3  // WALK_NORMAL_SOUTH
    Move 2, 1  // FACE_WEST
    MoveEnd

    .balign 4, 0
P363_05E4:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 15, 4  // WALK_NORMAL_EAST
    Move 13, 2  // WALK_NORMAL_SOUTH
    Move 2, 1  // FACE_WEST
    MoveEnd

    .balign 4, 0
P363_05F8:
    Move 15, 1  // WALK_NORMAL_EAST
    MoveEnd

    .balign 4, 0
P363_0600:
    Move 14, 1  // WALK_NORMAL_WEST
    MoveEnd

    .balign 4, 0
P363_0608:
    Move 30, 1  // WALK_ON_SPOT_SLOW_WEST
    MoveEnd

    .balign 4, 0
P363_0610:
    Move 12, 3  // WALK_NORMAL_NORTH
    Move 14, 2  // WALK_NORMAL_WEST
    Move 12, 1  // WALK_NORMAL_NORTH
    MoveEnd

    .balign 4, 0
P363_0620:
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 14, 3  // WALK_NORMAL_WEST
    Move 12, 1  // WALK_NORMAL_NORTH
    MoveEnd

    .balign 4, 0
P363_0630:
    Move 14, 1  // WALK_NORMAL_WEST
    Move 2, 1  // FACE_WEST
    MoveEnd

    .balign 4, 0
P363_063C:
    Move 15, 1  // WALK_NORMAL_EAST
    MoveEnd

    .balign 4, 0
P363_0644:
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P363_064C:
    Move 2, 1  // FACE_WEST
    Move 14, 1  // WALK_NORMAL_WEST
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P363_065C:
    Move 2, 1  // FACE_WEST
    MoveEnd

// ---- continuation 5: after the Warp at 359:00A9 (MAP_BATTLE_TOWER_ELEVATOR)
W359_00A9_S:
W359_00A9_00B5:
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_ReleaseAll
    pl_End

// ---- continuation 6: after the Warp at 361:00AD (MAP_BATTLE_TOWER_CORRIDOR_WIFI)
W361_00AD_S:
W361_00AD_00B9:
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
