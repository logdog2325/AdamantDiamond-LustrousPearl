// MAP_BATTLE_TOWER_PARTNER_ROOM: Pearl script file 364, text bank 286. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-10: Pearl's; 11: after a Warp, 12: after a Warp; 13: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P364_S1
    ScriptEntry P364_S2
    ScriptEntry P364_S3
    ScriptEntry P364_S4
    ScriptEntry P364_S5
    ScriptEntry P364_S6
    ScriptEntry P364_S7
    ScriptEntry P364_S8
    ScriptEntry P364_S9
    ScriptEntry P364_S10
    ScriptEntry W359_00D1_S
    ScriptEntry W364_0540_S
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P364_S7:
P364_002A:
    pl_CheckFlag PFLAG_00E3
    pl_GoToIf 0, P364_0121
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 5, P364_0057
    pl_TowerGetPartner PVAR_4009  // Pearl tower function 55
    pl_CompareVarToValue PVAR_4009, 0
    pl_GoToIf 1, P364_0121

P364_0057:
    pl_ClearFlag PFLAG_020A

P364_005B:
    pl_CheckFlag PFLAG_00E4
    pl_GoToIf 0, P364_012D
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 5, P364_0088
    pl_TowerGetPartner PVAR_4009  // Pearl tower function 55
    pl_CompareVarToValue PVAR_4009, 1
    pl_GoToIf 1, P364_012D

P364_0088:
    pl_ClearFlag PFLAG_020B

P364_008C:
    pl_CheckFlag PFLAG_00E5
    pl_GoToIf 0, P364_0139
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 5, P364_00B9
    pl_TowerGetPartner PVAR_4009  // Pearl tower function 55
    pl_CompareVarToValue PVAR_4009, 2
    pl_GoToIf 1, P364_0139

P364_00B9:
    pl_ClearFlag PFLAG_020C

P364_00BD:
    pl_CheckFlag PFLAG_00E6
    pl_GoToIf 0, P364_0145
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 5, P364_00EA
    pl_TowerGetPartner PVAR_4009  // Pearl tower function 55
    pl_CompareVarToValue PVAR_4009, 3
    pl_GoToIf 1, P364_0145

P364_00EA:
    pl_ClearFlag PFLAG_020D

P364_00EE:
    pl_CheckFlag PFLAG_00E7
    pl_GoToIf 0, P364_0151
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 5, P364_011B
    pl_TowerGetPartner PVAR_4009  // Pearl tower function 55
    pl_CompareVarToValue PVAR_4009, 4
    pl_GoToIf 1, P364_0151

P364_011B:
    pl_ClearFlag PFLAG_020E

P364_011F:
    pl_End

P364_0121:
    pl_SetFlag PFLAG_020A
    pl_GoTo P364_005B

P364_012D:
    pl_SetFlag PFLAG_020B
    pl_GoTo P364_008C

P364_0139:
    pl_SetFlag PFLAG_020C
    pl_GoTo P364_00BD

P364_0145:
    pl_SetFlag PFLAG_020D
    pl_GoTo P364_00EE

P364_0151:
    pl_SetFlag PFLAG_020E
    pl_GoTo P364_011F

P364_S8:
P364_015D:
    pl_CompareVarToValue PVAR_40DF, 1
    pl_CallIf 1, P364_0179
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 1, P364_017F
    pl_End

P364_0179:
    pl_TowerActorVisible PL_PLAYER, 0  // Pearl HideObject 255 (no actor command)
    pl_Return

P364_017F:
    pl_SetPosition 0, 8, 0, 3, 1
    pl_End

P364_S9:
P364_018D:
    pl_LockAll
    pl_SetVarFromValue PVAR_40DF, 0
    pl_Call P364_04A6
    pl_msg_sys 0
    pl_CloseMessage
    pl_TowerMakePartners  // Pearl tower function 56
    pl_ReleaseAll
    pl_End

P364_S1:
P364_01AC:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_BufferPlayerName 0
    pl_msg_talk 1
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P364_01D4
    pl_msg_talk 0
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P364_01D4:
    pl_CloseMessage
    pl_ReleaseAll
    pl_SetVarFromValue PVAR_40D8, 3
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 28  // the rest of this Pearl script runs there (continuation 28)
    pl_Warp 443, 7, 6, 0  // Pearl map 326 (MAP_BATTLE_TOWER_LOBBY)
    pl_ReleaseAll
    pl_End

P364_S10:
P364_0204:
    pl_LockAll
    pl_SetVarFromValue PVAR_40DF, 0
    pl_msg_sys 2
    pl_CloseMessage
    pl_Call P364_04E0
    pl_SetVarFromValue PVAR_40DB, 2
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 6  // the rest of this Pearl script runs there (continuation 6)
    pl_Warp 616, 3, 6, 0  // Pearl map 327 (MAP_BATTLE_TOWER_ELEVATOR)
    pl_ReleaseAll
    pl_End

P364_0245:
    pl_TowerPartnerMon PVAR_4009, 0, PVAR_8004, PVAR_8005
    pl_BufferSpeciesName 0, PVAR_8004
    pl_BufferMoveName 1, PVAR_8005
    pl_TowerPartnerMon PVAR_4009, 1, PVAR_8004, PVAR_8005
    pl_BufferSpeciesName 2, PVAR_8004
    pl_BufferMoveName 3, PVAR_8005
    pl_Return

P364_S2:
P364_0275:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 1, P364_02D2
    pl_SetVarFromValue PVAR_4009, 0
    pl_TowerPartnerMon PVAR_4009, 0, PVAR_8004, PVAR_8005
    pl_BufferSpeciesName 0, PVAR_8004  // Pearl 0x2C9
    pl_BufferMoveName 1, PVAR_8005
    pl_TowerPartnerMon PVAR_4009, 1, PVAR_8004, PVAR_8005
    pl_BufferSpeciesName 2, PVAR_8004  // Pearl 0x2C9
    pl_BufferMoveName 3, PVAR_8005
    pl_msg_talk 6
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P364_02DD

P364_02D2:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 7
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P364_02DD:
    pl_TowerSetPartner PVAR_4009  // Pearl tower function 50
    pl_SetVarFromValue PVAR_40DF, 2
    pl_msg_talk 8
    pl_CloseMessage
    pl_ReleaseAll
// LockObject 1: nothing in Black 2 (Black 2 pauses all actors (LockAll) only)
    pl_GoTo P364_055C

P364_S3:
P364_02FE:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 1, P364_0336
    pl_SetVarFromValue PVAR_4009, 1
    pl_Call P364_0245
    pl_BufferPlayerName 4
    pl_msg_talk 15
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P364_0341

P364_0336:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 16
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P364_0341:
    pl_TowerSetPartner PVAR_4009  // Pearl tower function 50
    pl_SetVarFromValue PVAR_40DF, 2
    pl_BufferPlayerName 0
    pl_msg_talk 17
    pl_CloseMessage
    pl_ReleaseAll
// LockObject 2: nothing in Black 2 (Black 2 pauses all actors (LockAll) only)
    pl_GoTo P364_05A1

P364_S4:
P364_0365:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 1, P364_039A
    pl_SetVarFromValue PVAR_4009, 2
    pl_Call P364_0245
    pl_msg_talk 3
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P364_03A5

P364_039A:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 4
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P364_03A5:
    pl_TowerSetPartner PVAR_4009  // Pearl tower function 50
    pl_SetVarFromValue PVAR_40DF, 2
    pl_msg_talk 5
    pl_CloseMessage
    pl_ReleaseAll
// LockObject 3: nothing in Black 2 (Black 2 pauses all actors (LockAll) only)
    pl_GoTo P364_05E6

P364_S5:
P364_03C6:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 1, P364_03FB
    pl_SetVarFromValue PVAR_4009, 3
    pl_Call P364_0245
    pl_msg_talk 12
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P364_0406

P364_03FB:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 13
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P364_0406:
    pl_TowerSetPartner PVAR_4009  // Pearl tower function 50
    pl_SetVarFromValue PVAR_40DF, 2
    pl_msg_talk 14
    pl_CloseMessage
    pl_ReleaseAll
// LockObject 4: nothing in Black 2 (Black 2 pauses all actors (LockAll) only)
    pl_GoTo P364_062B

P364_S6:
P364_0427:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CompareVarToValue PVAR_40DF, 2
    pl_GoToIf 1, P364_045C
    pl_SetVarFromValue PVAR_4009, 4
    pl_Call P364_0245
    pl_msg_talk 9
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P364_0467

P364_045C:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 10
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P364_0467:
    pl_TowerSetPartner PVAR_4009  // Pearl tower function 50
    pl_SetVarFromValue PVAR_40DF, 2
    pl_msg_talk 11
    pl_CloseMessage
    pl_ReleaseAll
// LockObject 5: nothing in Black 2 (Black 2 pauses all actors (LockAll) only)
    pl_GoTo P364_0670

P364_0488:
    pl_LoadDoorAnimation 77, 8, 2  // the door at cell (0,0) tile (8,2)
    pl_PlayDoorOpenAnimation 77
    pl_WaitForAnimation 77
    pl_Return

P364_049B:
    pl_PlayDoorCloseAnimation 77
    pl_WaitForAnimation 77
    pl_UnloadAnimation 77
    pl_Return

P364_04A6:
    pl_Call P364_0488
    pl_ApplyMovement 0, P364_06C8
    pl_WaitMovement
    pl_ShowObject PL_PLAYER  // Pearl ShowObject 255
    pl_ApplyMovement PL_PLAYER, P364_06B8
    pl_WaitMovement
    pl_Call P364_049B
    pl_ApplyMovement 0, P364_06D8
    pl_WaitMovement
    pl_ApplyMovement PL_PLAYER, P364_06C0
    pl_WaitMovement
    pl_Return

P364_04E0:
    pl_Call P364_0488
    pl_ApplyMovement 0, P364_0718
    pl_ApplyMovement PL_PLAYER, P364_070C
    pl_WaitMovement
    pl_Call P364_049B
    pl_Return

P364_0500:
    pl_ApplyMovement PVAR_4000, P364_0724
    pl_WaitMovement
    pl_ApplyMovement 0, P364_06E4
    pl_WaitMovement
    pl_Call P364_0488
    pl_ApplyMovement PVAR_4000, P364_072C
    pl_WaitMovement
    pl_Call P364_049B
    pl_ApplyMovement 0, P364_06F8
    pl_WaitMovement
    pl_fade_out_black  // FadeScreen 6, 1, 0, 0x0
    pl_WaitFadeScreen
    RTReserveScript 12  // the rest of this Pearl script runs there (continuation 12)
    pl_Warp 621, 8, 4, 0  // Pearl map 493 (MAP_BATTLE_TOWER_PARTNER_ROOM)
    pl_ReleaseAll
    pl_End

P364_055C:
    pl_SetVarFromValue PVAR_4000, 1
    pl_GetPlayerMapPos PVAR_8000, PVAR_8001
    pl_CompareVarToValue PVAR_8000, 12
    pl_GoToIf 1, P364_057D
    pl_GoTo P364_058F

P364_057D:
    pl_ApplyMovement 1, P364_0738
    pl_WaitMovement
    pl_GoTo P364_0500

P364_058F:
    pl_ApplyMovement 1, P364_074C
    pl_WaitMovement
    pl_GoTo P364_0500

P364_05A1:
    pl_SetVarFromValue PVAR_4000, 2
    pl_GetPlayerMapPos PVAR_8000, PVAR_8001
    pl_CompareVarToValue PVAR_8000, 4
    pl_GoToIf 1, P364_05C2
    pl_GoTo P364_05D4

P364_05C2:
    pl_ApplyMovement 2, P364_0764
    pl_WaitMovement
    pl_GoTo P364_0500

P364_05D4:
    pl_ApplyMovement 2, P364_0774
    pl_WaitMovement
    pl_GoTo P364_0500

P364_05E6:
    pl_SetVarFromValue PVAR_4000, 3
    pl_GetPlayerMapPos PVAR_8000, PVAR_8001
    pl_CompareVarToValue PVAR_8001, 7
    pl_GoToIf 1, P364_0607
    pl_GoTo P364_0619

P364_0607:
    pl_ApplyMovement 3, P364_0780
    pl_WaitMovement
    pl_GoTo P364_0500

P364_0619:
    pl_ApplyMovement 3, P364_0790
    pl_WaitMovement
    pl_GoTo P364_0500

P364_062B:
    pl_SetVarFromValue PVAR_4000, 4
    pl_GetPlayerMapPos PVAR_8000, PVAR_8001
    pl_CompareVarToValue PVAR_8001, 9
    pl_GoToIf 1, P364_064C
    pl_GoTo P364_065E

P364_064C:
    pl_ApplyMovement 4, P364_079C
    pl_WaitMovement
    pl_GoTo P364_0500

P364_065E:
    pl_ApplyMovement 4, P364_07B0
    pl_WaitMovement
    pl_GoTo P364_0500

P364_0670:
    pl_SetVarFromValue PVAR_4000, 5
    pl_GetPlayerMapPos PVAR_8000, PVAR_8001
    pl_CompareVarToValue PVAR_8000, 8
    pl_GoToIf 1, P364_0691
    pl_GoTo P364_06A3

P364_0691:
    pl_ApplyMovement 5, P364_07C4
    pl_WaitMovement
    pl_GoTo P364_0500

P364_06A3:
    pl_ApplyMovement 5, P364_07D4
    pl_WaitMovement
    pl_GoTo P364_0500

    .balign 4, 0
P364_06B8:
    Move 13, 2  // WALK_NORMAL_SOUTH
    MoveEnd

    .balign 4, 0
P364_06C0:
    Move 0, 1  // FACE_NORTH
    MoveEnd

    .balign 4, 0
P364_06C8:
    Move 13, 2  // WALK_NORMAL_SOUTH
    Move 14, 1  // WALK_NORMAL_WEST
    Move 3, 1  // FACE_EAST
    MoveEnd

    .balign 4, 0
P364_06D8:
    Move 15, 1  // WALK_NORMAL_EAST
    Move 1, 1  // FACE_SOUTH
    MoveEnd

    .balign 4, 0
P364_06E4:
    Move 1, 1  // FACE_SOUTH
    Move 71, 1  // LOCK_DIR
    Move 18, 1  // WALK_FAST_WEST
    Move 72, 1  // UNLOCK_DIR
    MoveEnd

    .balign 4, 0
P364_06F8:
    Move 71, 1  // LOCK_DIR
    Move 19, 1  // WALK_FAST_EAST
    Move 72, 1  // UNLOCK_DIR
    Move 1, 1  // FACE_SOUTH
    MoveEnd

    .balign 4, 0
P364_070C:
    Move 12, 2  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P364_0718:
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P364_0724:
    Move 0, 1  // FACE_NORTH
    MoveEnd

    .balign 4, 0
P364_072C:
    Move 16, 2  // WALK_FAST_NORTH
    Move 69, 1  // SET_INVISIBLE
    MoveEnd

    .balign 4, 0
P364_0738:
    Move 17, 1  // WALK_FAST_SOUTH
    Move 18, 3  // WALK_FAST_WEST
    Move 16, 7  // WALK_FAST_NORTH
    Move 18, 2  // WALK_FAST_WEST
    MoveEnd

    .balign 4, 0
P364_074C:
    Move 18, 1  // WALK_FAST_WEST
    Move 16, 1  // WALK_FAST_NORTH
    Move 18, 2  // WALK_FAST_WEST
    Move 16, 5  // WALK_FAST_NORTH
    Move 18, 2  // WALK_FAST_WEST
    MoveEnd

    .balign 4, 0
P364_0764:
    Move 19, 1  // WALK_FAST_EAST
    Move 16, 2  // WALK_FAST_NORTH
    Move 19, 3  // WALK_FAST_EAST
    MoveEnd

    .balign 4, 0
P364_0774:
    Move 16, 2  // WALK_FAST_NORTH
    Move 19, 4  // WALK_FAST_EAST
    MoveEnd

    .balign 4, 0
P364_0780:
    Move 18, 1  // WALK_FAST_WEST
    Move 16, 4  // WALK_FAST_NORTH
    Move 18, 2  // WALK_FAST_WEST
    MoveEnd

    .balign 4, 0
P364_0790:
    Move 16, 4  // WALK_FAST_NORTH
    Move 18, 3  // WALK_FAST_WEST
    MoveEnd

    .balign 4, 0
P364_079C:
    Move 17, 1  // WALK_FAST_SOUTH
    Move 19, 4  // WALK_FAST_EAST
    Move 16, 7  // WALK_FAST_NORTH
    Move 19, 2  // WALK_FAST_EAST
    MoveEnd

    .balign 4, 0
P364_07B0:
    Move 16, 1  // WALK_FAST_NORTH
    Move 19, 4  // WALK_FAST_EAST
    Move 16, 5  // WALK_FAST_NORTH
    Move 19, 2  // WALK_FAST_EAST
    MoveEnd

    .balign 4, 0
P364_07C4:
    Move 18, 1  // WALK_FAST_WEST
    Move 16, 5  // WALK_FAST_NORTH
    Move 19, 2  // WALK_FAST_EAST
    MoveEnd

    .balign 4, 0
P364_07D4:
    Move 19, 3  // WALK_FAST_EAST
    Move 16, 5  // WALK_FAST_NORTH
    Move 18, 2  // WALK_FAST_WEST
    MoveEnd

// ---- continuation 11: after the Warp at 359:00D1 (MAP_BATTLE_TOWER_ELEVATOR)
W359_00D1_S:
W359_00D1_00DD:
    pl_fade_in_black  // FadeScreen 6, 1, 1, 0x0
    pl_WaitFadeScreen
    pl_ReleaseAll
    pl_End

// ---- continuation 12: after the Warp at 364:0540 (MAP_BATTLE_TOWER_PARTNER_ROOM)
W364_0540_S:
W364_0540_054C:
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
