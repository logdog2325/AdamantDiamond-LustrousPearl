// MAP_BATTLE_TOWER_ARENA_MULTI: Pearl script file 362, text bank 284. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-5: Pearl's; 6: after a Warp, 7: after a Warp; 8: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P362_S1
    ScriptEntry P362_S2
    ScriptEntry P362_S3
    ScriptEntry P362_S4
    ScriptEntry P362_S5
    ScriptEntry W359_0059_S
    ScriptEntry W360_0072_S
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P362_S1:
P362_0016:
    pl_CompareVarToValue PVAR_40D9, 0
    pl_GoToIf 1, P362_0035
    pl_SetFlag PFLAG_01E9
    pl_TowerPlayerCode PVAR_4000  // Pearl tower function 55: the player's sprite
    pl_SetVarFromVar PVAR_4020, PVAR_4000

P362_0035:
    pl_End

P362_S5:
P362_0037:
    pl_TowerActorVisible PL_PLAYER, 0  // Pearl HideObject 255 (no actor command)
    pl_CompareVarToValue PVAR_40D9, 3
    pl_GoToIf 1, P362_004A
    pl_End

P362_004A:
    pl_SetPosition 2, 5, 0, 6, 3
    pl_End

P362_S4:
P362_0058:
    pl_SetVarFromValue PVAR_40D9, 0
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_Call P362_015D
    pl_ReleaseAll
    pl_End

P362_0070:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 0
    pl_PlayFanfare SEQ_ME_ASA  // Pearl SEQ_ASA
    pl_WaitFanfare
    pl_HealParty
    pl_Return

P362_007D:
    pl_WaitTime 30, PVAR_800C
    pl_SetVarFromValue PVAR_40D8, 1
    BSubwayCmd_Tool 21, 0, 0, PVAR_800C  // Pearl tower function 43
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 4
    pl_GoToIf 1, P362_00D9
    pl_CompareVarToValue PVAR_8008, 5
    pl_GoToIf 1, P362_00D9
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 24  // the rest of this Pearl script runs there (continuation 24)
    pl_Warp 443, 11, 6, 0  // Pearl map 326 (MAP_BATTLE_TOWER_LOBBY)
    pl_ReleaseAll
    pl_End

P362_00D9:
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 25  // the rest of this Pearl script runs there (continuation 25)
    pl_Warp 443, 15, 6, 0  // Pearl map 326 (MAP_BATTLE_TOWER_LOBBY)
    pl_ReleaseAll
    pl_End

P362_S2:
P362_0101:
    pl_LockAll
    pl_SetVarFromValue PVAR_40D9, 3
    pl_TowerIsNull PVAR_800C  // Pearl tower function 100
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P362_007D
    pl_Call P362_0436
    pl_GoTo P362_0201

P362_S3:
P362_012C:
    pl_LockAll
    pl_SetVarFromValue PVAR_40D9, 3
    pl_TowerIsNull PVAR_800C  // Pearl tower function 100
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P362_007D
    pl_Call P362_0436
    pl_Call P362_0442
    pl_GoTo P362_02F4

P362_015D:
    BSubwayCmd_Tool 307, 0, 0, 0  // Pearl tower function 40
    pl_Call P362_0456
    BSubwayCmd_Tool 352, 0, 1, 0  // PrintBattleTowerIntroMessage
// WaitABPress: the Tower opponent's balloon waited for A itself
    pl_CloseMessage
    pl_Call P362_0478
    BSubwayCmd_Tool 309, 0, 0, 0  // Pearl tower function 42: the battle
    BSubwayCmd_Tool 332, 0, 0, PVAR_800C
    BSubwayCmd_Tool 347, 0, 0, 0
    pl_SetVarFromVar PVAR_8004, PVAR_800C
    pl_Return

P362_018C:
    BSubwayCmd_Tool 304, 0, 0, 0  // Pearl tower function 37
    pl_GoTo P362_007D

P362_019C:
    BSubwayCmd_Tool 305, 0, 0, 0  // Pearl tower function 38
    pl_GoTo P362_007D

P362_01AC:
    pl_SetVarFromValue PVAR_40D8, 2
    BSubwayCmd_Tool 306, 0, 0, 0  // Pearl tower function 39: the play block keeps the challenge
    FieldSetNextZone 443, 1, 11, 0, 6
    FlagSet 2405
    Plugin1_Cmd1002  // FreeBattleTower
    pl_msg_sys 4
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

P362_01E7:
    pl_GoTo P362_018C

P362_01EF:
    BSubwayCmd_Tool 357, 0, 0, PVAR_800C  // Pearl tower function 34
    BSubwayCmd_Tool 303, 0, 0, PVAR_800C  // Pearl tower function 35
    pl_Return

P362_0201:
    pl_Call P362_015D
    pl_CompareVarToValue PVAR_8004, 0
    pl_GoToIf 1, P362_018C
    pl_Call P362_01EF
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, P362_019C
    pl_Call P362_048C
    pl_Call P362_04A0
    pl_Call P362_0070
    pl_GoTo P362_02F4

P362_0241:
    BSubwayCmd_Tool 8, 0, 0, PVAR_8004  // Pearl tower function 33
    pl_BufferNumber 0, PVAR_8004
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 1
    ListMenu_AnchorTopRight 31, 11, 0, 0, PVAR_800C  // Pearl InitGlobalTextListMenu 21, 11, 0, 0, PVAR_800C
    ListMenuAdd 14, 65535, 0  // Pearl AddListMenuEntry 146, 0
    ListMenuAdd 15, 65535, 1  // Pearl AddListMenuEntry 147, 1
    ListMenuAdd 16, 65535, 2  // Pearl AddListMenuEntry 148, 2
    ListMenuShow
    pl_CloseMessage
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, P362_02AA
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, P362_02B8
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, P362_02D6
    pl_GoTo P362_02AA

P362_02AA:
    pl_Call P362_04B4
    pl_GoTo P362_0201

P362_02B8:
    pl_msg_sys 2
    pl_ShowYesNoMenu PVAR_800C
    pl_CloseMessage
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P362_01AC
    pl_GoTo P362_0241

P362_02D6:
    pl_msg_sys 3
    pl_ShowYesNoMenu PVAR_800C
    pl_CloseMessage
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P362_01E7
    pl_GoTo P362_0241

P362_02F4:
    BSubwayCmd_Tool 21, 0, 0, PVAR_800C  // Pearl tower function 43
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 5, P362_0241
    BSubwayCmd_Tool 358, 0, 0, PVAR_800C  // Pearl tower function 36
    pl_CompareVarToValue PVAR_800C, 20
    pl_GoToIf 1, P362_0333
    pl_CompareVarToValue PVAR_800C, 48
    pl_GoToIf 1, P362_0333
    pl_GoTo P362_0241

P362_0333:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 9
    ListMenu_AnchorTopRight 31, 11, 0, 0, PVAR_800C  // Pearl InitGlobalTextListMenu 21, 11, 0, 0, PVAR_800C
    ListMenuAdd 14, 65535, 0  // Pearl AddListMenuEntry 146, 0
    ListMenuAdd 15, 65535, 1  // Pearl AddListMenuEntry 147, 1
    ListMenuAdd 16, 65535, 2  // Pearl AddListMenuEntry 148, 2
    ListMenuShow
    pl_CloseMessage
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, P362_038F
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, P362_02B8
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, P362_02D6
    pl_GoTo P362_038F

P362_038F:
    pl_Call P362_04B4
    BSubwayCmd_Tool 307, 0, 0, 0  // Pearl tower function 40
    pl_Call P362_04C8
    BSubwayCmd_Tool 358, 0, 0, PVAR_800C  // Pearl tower function 36
    pl_CompareVarToValue PVAR_800C, 48
    pl_GoToIf 1, P362_0418
    pl_BufferPlayerName 0
    pl_BufferRivalName 1
    pl_msg_sys 10

P362_03C1:
    pl_CloseMessage
    pl_Call P362_0478
    BSubwayCmd_Tool 309, 0, 0, 0  // Pearl tower function 42: the battle
    BSubwayCmd_Tool 332, 0, 0, PVAR_800C
    BSubwayCmd_Tool 347, 0, 0, 0
    pl_SetVarFromVar PVAR_8004, PVAR_800C
    pl_CompareVarToValue PVAR_8004, 0
    pl_GoToIf 1, P362_018C
    BSubwayCmd_Tool 358, 0, 0, PVAR_800C  // Pearl tower function 36
    pl_CompareVarToValue PVAR_800C, 48
    pl_GoToIf 1, P362_0423
    pl_msg_sys 12
    BSubwayCmd_Tool 311, 1, 0, 0  // Pearl tower function 44

P362_0408:
    pl_CloseMessage
    pl_Call P362_01EF
    pl_GoTo P362_019C

P362_0418:
    pl_msg_sys 11
    pl_GoTo P362_03C1

P362_0423:
    pl_msg_sys 13
    BSubwayCmd_Tool 311, 2, 0, 0  // Pearl tower function 44
    pl_GoTo P362_0408

P362_0436:
    pl_ApplyMovement 2, P362_0500
    pl_WaitMovement
    pl_Return

P362_0442:
    pl_ApplyMovement 0, P362_057C
    pl_ApplyMovement 2, P362_059C
    pl_WaitMovement
    pl_Return

P362_0456:
    BSubwayCmd_Tool 308, 0, 0, PVAR_800C  // Pearl tower function 41
    pl_SetVarFromVar PVAR_4021, PVAR_800C
    pl_ClearFlag PFLAG_01E9
    pl_AddObject 1
    pl_ApplyMovement 1, P362_0520
    pl_WaitMovement
    pl_Return

P362_0478:
    pl_ApplyMovement 2, P362_053C
    pl_ApplyMovement 1, P362_0544
    pl_WaitMovement
    pl_Return

P362_048C:
    pl_ApplyMovement 1, P362_054C
    pl_WaitMovement
    pl_SetFlag PFLAG_01E9
    pl_RemoveObject 1, PFLAG_01E9
    pl_Return

P362_04A0:
    pl_ApplyMovement 2, P362_0570
    pl_ApplyMovement 0, P362_057C
    pl_WaitMovement
    pl_Return

P362_04B4:
    pl_ApplyMovement 2, P362_0584
    pl_ApplyMovement 0, P362_058C
    pl_WaitMovement
    pl_Return

P362_04C8:
    pl_SetVarFromValue PVAR_4021, 207  // dynamic sprite: Pearl graphics 169 -> Black 2 code
    pl_ClearFlag PFLAG_01E9
    pl_AddObject 1
    pl_ApplyMovement 1, P362_05A4
    pl_WaitMovement
    pl_Return

    .balign 4, 0
P362_0500:
    Move 62, 1  // DELAY_4
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 2, 1  // FACE_WEST
    Move 14, 3  // WALK_NORMAL_WEST
    Move 0, 1  // FACE_NORTH
    Move 12, 3  // WALK_NORMAL_NORTH
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P362_0520:
    Move 13, 1  // WALK_NORMAL_SOUTH
    Move 3, 1  // FACE_EAST
    Move 15, 3  // WALK_NORMAL_EAST
    Move 1, 1  // FACE_SOUTH
    Move 13, 3  // WALK_NORMAL_SOUTH
    Move 2, 1  // FACE_WEST
    MoveEnd

    .balign 4, 0
P362_053C:
    Move 15, 1  // WALK_NORMAL_EAST
    MoveEnd

    .balign 4, 0
P362_0544:
    Move 14, 1  // WALK_NORMAL_WEST
    MoveEnd

    .balign 4, 0
P362_054C:
    Move 3, 1  // FACE_EAST
    Move 15, 1  // WALK_NORMAL_EAST
    Move 0, 1  // FACE_NORTH
    Move 12, 3  // WALK_NORMAL_NORTH
    Move 2, 1  // FACE_WEST
    Move 14, 3  // WALK_NORMAL_WEST
    Move 0, 1  // FACE_NORTH
    Move 12, 1  // WALK_NORMAL_NORTH
    MoveEnd

    .balign 4, 0
P362_0570:
    Move 14, 1  // WALK_NORMAL_WEST
    Move 2, 1  // FACE_WEST
    MoveEnd

    .balign 4, 0
P362_057C:
    Move 15, 1  // WALK_NORMAL_EAST
    MoveEnd

    .balign 4, 0
P362_0584:
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P362_058C:
    Move 2, 1  // FACE_WEST
    Move 14, 1  // WALK_NORMAL_WEST
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P362_059C:
    Move 2, 1  // FACE_WEST
    MoveEnd

    .balign 4, 0
P362_05A4:
    Move 9, 1  // WALK_SLOW_SOUTH
    Move 3, 1  // FACE_EAST
    Move 11, 3  // WALK_SLOW_EAST
    Move 1, 1  // FACE_SOUTH
    Move 9, 3  // WALK_SLOW_SOUTH
    Move 2, 1  // FACE_WEST
    MoveEnd

// ---- continuation 6: after the Warp at 359:0059 (MAP_BATTLE_TOWER_ELEVATOR)
W359_0059_S:
W359_0059_0065:
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_ReleaseAll
    pl_End

// ---- continuation 7: after the Warp at 360:0072 (MAP_BATTLE_TOWER_CORRIDOR_MULTI)
W360_0072_S:
W360_0072_007E:
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
