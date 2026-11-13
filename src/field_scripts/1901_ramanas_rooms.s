// The slate rooms of Ramanas Park in Pal Park (notes/RAMANAS_PARK.md). Written by b2tools/ramanas.py from
// data/ramanas_park.json: do not edit; rerun `python3 b2tools/ramanas.py`.
// Version sp+bd. Room i: entries 1-4 Discovery Room (zone 652), 5-8 Kanto Room (zone 653), 9-12 Johto Room (zone 661), 13-16 Soul Room (zone 654), 17-20 Distortion Room (zone 655), 21-24 Rainbow Room (zone 662), 25-28 Squall Room (zone 656), 29-32 Oceanic Room (zone 657), 33-36 Tectonic Room (zone 658), 37-40 Stratospheric Room (zone 659), 41-44 Genome Room (zone 660)
// (pedestal, zone init, name on arrival, the Catching Show block).
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

#define PL_RAMANAS_PARK_ZONE 366   // MAP_PAL_PARK
#define PL_RAMANAS_PARK_ARRIVE 8   // its file's PearlArrive

    ScriptEntry RP_Pedestal_0
    ScriptEntry RP_Init_0
    ScriptEntry RP_Name_0
    ScriptEntry RP_Closed_0
    ScriptEntry RP_Pedestal_1
    ScriptEntry RP_Init_1
    ScriptEntry RP_Name_1
    ScriptEntry RP_Closed_1
    ScriptEntry RP_Pedestal_2
    ScriptEntry RP_Init_2
    ScriptEntry RP_Name_2
    ScriptEntry RP_Closed_2
    ScriptEntry RP_Pedestal_3
    ScriptEntry RP_Init_3
    ScriptEntry RP_Name_3
    ScriptEntry RP_Closed_3
    ScriptEntry RP_Pedestal_4
    ScriptEntry RP_Init_4
    ScriptEntry RP_Name_4
    ScriptEntry RP_Closed_4
    ScriptEntry RP_Pedestal_5
    ScriptEntry RP_Init_5
    ScriptEntry RP_Name_5
    ScriptEntry RP_Closed_5
    ScriptEntry RP_Pedestal_6
    ScriptEntry RP_Init_6
    ScriptEntry RP_Name_6
    ScriptEntry RP_Closed_6
    ScriptEntry RP_Pedestal_7
    ScriptEntry RP_Init_7
    ScriptEntry RP_Name_7
    ScriptEntry RP_Closed_7
    ScriptEntry RP_Pedestal_8
    ScriptEntry RP_Init_8
    ScriptEntry RP_Name_8
    ScriptEntry RP_Closed_8
    ScriptEntry RP_Pedestal_9
    ScriptEntry RP_Init_9
    ScriptEntry RP_Name_9
    ScriptEntry RP_Closed_9
    ScriptEntry RP_Pedestal_10
    ScriptEntry RP_Init_10
    ScriptEntry RP_Name_10
    ScriptEntry RP_Closed_10
    ScriptEntriesEnd

RP_Pedestal_0:
    pl_LockAll
    FlagGet 902, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_1notdone
    FlagGet 1054, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_1notdone
    FlagGet 1055, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_1notdone
    pl_msg_sys 0
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_1notdone:
    ItemCheckAmount 120, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_2have
    pl_msg_sys 1
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_2have:
    pl_msg_sys 2
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_3end
    WorkSetConst 0x8052, 0
    FlagGet 902, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_5
    WorkAdd 0x8052, 1
.LRP_5:
    FlagGet 1054, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_6
    WorkAdd 0x8052, 1
.LRP_6:
    FlagGet 1055, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_7
    WorkAdd 0x8052, 1
.LRP_7:
    Random 0x8053, 0x8052
    FlagGet 902, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_8
    WorkSetConst 0x8051, 0
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_4chosen
    WorkSub 0x8053, 1
.LRP_8:
    FlagGet 1054, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_9
    WorkSetConst 0x8051, 1
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_4chosen
    WorkSub 0x8053, 1
.LRP_9:
    FlagGet 1055, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_10
    WorkSetConst 0x8051, 2
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_4chosen
    WorkSub 0x8053, 1
.LRP_10:
.LRP_4chosen:
    pl_CloseMessage
    ItemSub 120, 1, 0x8050
    pl_msg_sys 3
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_11
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 377, 0
    PVWait
    CallWildBattleEx 377, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_0
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_12
    FlagSet 902
.LRP_12:
    pl_ReleaseAll
    VMHalt
.LRP_11:
    WorkCmpConst 0x8051, 1
    VMJumpIf CMP_NE, .LRP_13
    FlagReset 49
    ActorAdd 2
    FadeInWhite
    FadeWait
    PVPlay 378, 0
    PVWait
    CallWildBattleEx 378, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_0
    ActorDelete 2
    FlagSet 49
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_14
    FlagSet 1054
.LRP_14:
    pl_ReleaseAll
    VMHalt
.LRP_13:
    WorkCmpConst 0x8051, 2
    VMJumpIf CMP_NE, .LRP_15
    FlagReset 50
    ActorAdd 3
    FadeInWhite
    FadeWait
    PVPlay 379, 0
    PVWait
    CallWildBattleEx 379, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_0
    ActorDelete 3
    FlagSet 50
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_16
    FlagSet 1055
.LRP_16:
    pl_ReleaseAll
    VMHalt
.LRP_15:
.LRP_3end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_0:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_0:
    FlagSet 48
    FlagSet 49
    FlagSet 50
    VMHalt

RP_Name_0:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 4, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_0:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 30, 0, 38, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_1:
    pl_LockAll
    FlagGet 1056, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_17notdone
    FlagGet 1057, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_17notdone
    FlagGet 1058, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_17notdone
    pl_msg_sys 6
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_17notdone:
    ItemCheckAmount 121, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_18have
    pl_msg_sys 7
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_18have:
    pl_msg_sys 8
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_19end
    WorkSetConst 0x8052, 0
    FlagGet 1056, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_21
    WorkAdd 0x8052, 1
.LRP_21:
    FlagGet 1057, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_22
    WorkAdd 0x8052, 1
.LRP_22:
    FlagGet 1058, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_23
    WorkAdd 0x8052, 1
.LRP_23:
    Random 0x8053, 0x8052
    FlagGet 1056, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_24
    WorkSetConst 0x8051, 0
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_20chosen
    WorkSub 0x8053, 1
.LRP_24:
    FlagGet 1057, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_25
    WorkSetConst 0x8051, 1
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_20chosen
    WorkSub 0x8053, 1
.LRP_25:
    FlagGet 1058, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_26
    WorkSetConst 0x8051, 2
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_20chosen
    WorkSub 0x8053, 1
.LRP_26:
.LRP_20chosen:
    pl_CloseMessage
    ItemSub 121, 1, 0x8050
    pl_msg_sys 9
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_27
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 144, 0
    PVWait
    CallWildBattleEx 144, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_1
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_28
    FlagSet 1056
.LRP_28:
    pl_ReleaseAll
    VMHalt
.LRP_27:
    WorkCmpConst 0x8051, 1
    VMJumpIf CMP_NE, .LRP_29
    FlagReset 49
    ActorAdd 2
    FadeInWhite
    FadeWait
    PVPlay 145, 0
    PVWait
    CallWildBattleEx 145, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_1
    ActorDelete 2
    FlagSet 49
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_30
    FlagSet 1057
.LRP_30:
    pl_ReleaseAll
    VMHalt
.LRP_29:
    WorkCmpConst 0x8051, 2
    VMJumpIf CMP_NE, .LRP_31
    FlagReset 50
    ActorAdd 3
    FadeInWhite
    FadeWait
    PVPlay 146, 0
    PVWait
    CallWildBattleEx 146, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_1
    ActorDelete 3
    FlagSet 50
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_32
    FlagSet 1058
.LRP_32:
    pl_ReleaseAll
    VMHalt
.LRP_31:
.LRP_19end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_1:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_1:
    FlagSet 48
    FlagSet 49
    FlagSet 50
    VMHalt

RP_Name_1:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 10, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_1:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 34, 0, 38, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_2:
    pl_LockAll
    FlagGet 1068, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_33notdone
    FlagGet 1069, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_33notdone
    FlagGet 1070, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_33notdone
    pl_msg_sys 11
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_33notdone:
    ItemCheckAmount 131, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_34have
    pl_msg_sys 12
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_34have:
    pl_msg_sys 13
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_35end
    WorkSetConst 0x8052, 0
    FlagGet 1068, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_37
    WorkAdd 0x8052, 1
.LRP_37:
    FlagGet 1069, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_38
    WorkAdd 0x8052, 1
.LRP_38:
    FlagGet 1070, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_39
    WorkAdd 0x8052, 1
.LRP_39:
    Random 0x8053, 0x8052
    FlagGet 1068, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_40
    WorkSetConst 0x8051, 0
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_36chosen
    WorkSub 0x8053, 1
.LRP_40:
    FlagGet 1069, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_41
    WorkSetConst 0x8051, 1
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_36chosen
    WorkSub 0x8053, 1
.LRP_41:
    FlagGet 1070, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_42
    WorkSetConst 0x8051, 2
    WorkCmpConst 0x8053, 0
    VMJumpIf CMP_EQ, .LRP_36chosen
    WorkSub 0x8053, 1
.LRP_42:
.LRP_36chosen:
    pl_CloseMessage
    ItemSub 131, 1, 0x8050
    pl_msg_sys 14
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_43
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 243, 0
    PVWait
    CallWildBattleEx 243, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_2
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_44
    FlagSet 1068
.LRP_44:
    pl_ReleaseAll
    VMHalt
.LRP_43:
    WorkCmpConst 0x8051, 1
    VMJumpIf CMP_NE, .LRP_45
    FlagReset 49
    ActorAdd 2
    FadeInWhite
    FadeWait
    PVPlay 244, 0
    PVWait
    CallWildBattleEx 244, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_2
    ActorDelete 2
    FlagSet 49
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_46
    FlagSet 1069
.LRP_46:
    pl_ReleaseAll
    VMHalt
.LRP_45:
    WorkCmpConst 0x8051, 2
    VMJumpIf CMP_NE, .LRP_47
    FlagReset 50
    ActorAdd 3
    FadeInWhite
    FadeWait
    PVPlay 245, 0
    PVWait
    CallWildBattleEx 245, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_2
    ActorDelete 3
    FlagSet 50
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_48
    FlagSet 1070
.LRP_48:
    pl_ReleaseAll
    VMHalt
.LRP_47:
.LRP_35end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_2:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_2:
    FlagSet 48
    FlagSet 49
    FlagSet 50
    VMHalt

RP_Name_2:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 15, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_2:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 30, 0, 25, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_3:
    pl_LockAll
    FlagGet 1059, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_49notdone
    FlagGet 1060, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_49notdone
    pl_msg_sys 16
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_49notdone:
    ItemCheckAmount 122, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_50have
    pl_msg_sys 17
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_50have:
    pl_msg_sys 18
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_51end
    pl_CloseMessage
    pl_msg_sys 19
    ListMenu_AnchorTopRight 31, 1, 0, 1, 0x8051
    FlagGet 1059, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_53
    WordSetPokeSpecies 0, 380
    ListMenuAdd 20, 65535, 0
.LRP_53:
    FlagGet 1060, 0x8057
    WorkCmpConst 0x8057, 1
    VMJumpIf CMP_EQ, .LRP_54
    WordSetPokeSpecies 0, 381
    ListMenuAdd 20, 65535, 1
.LRP_54:
    ListMenuShow
    WorkCmpConst 0x8051, 2
    VMJumpIf CMP_GE, .LRP_51end
.LRP_52chosen:
    pl_CloseMessage
    ItemSub 122, 1, 0x8050
    pl_msg_sys 21
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_55
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 380, 0
    PVWait
    CallWildBattleEx 380, 70, 0, 1
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_3
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_56
    FlagSet 1059
    pl_msg_sys 22
    pl_WaitButton
    pl_CloseMessage
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 204
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
    FlagGet 1059, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_57
    FlagGet 1060, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_57
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 225
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
.LRP_57:
.LRP_56:
    pl_ReleaseAll
    VMHalt
.LRP_55:
    WorkCmpConst 0x8051, 1
    VMJumpIf CMP_NE, .LRP_58
    FlagReset 49
    ActorAdd 2
    FadeInWhite
    FadeWait
    PVPlay 381, 0
    PVWait
    CallWildBattleEx 381, 70, 0, 1
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_3
    ActorDelete 2
    FlagSet 49
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_59
    FlagSet 1060
    pl_msg_sys 22
    pl_WaitButton
    pl_CloseMessage
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 205
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
    FlagGet 1059, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_60
    FlagGet 1060, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_60
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 225
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
.LRP_60:
.LRP_59:
    pl_ReleaseAll
    VMHalt
.LRP_58:
.LRP_51end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_3:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_3:
    FlagSet 48
    FlagSet 49
    VMHalt

RP_Name_3:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 23, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_3:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 27, 0, 36, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_4:
    pl_LockAll
    FlagGet 1066, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_61notdone
    pl_msg_sys 24
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_61notdone:
    ItemCheckAmount 123, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_62have
    pl_msg_sys 25
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_62have:
    pl_msg_sys 26
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_63end
    WorkSetConst 0x8051, 0
.LRP_64chosen:
    pl_CloseMessage
    ItemSub 123, 1, 0x8050
    pl_msg_sys 27
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_65
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 487, 0
    PVWait
    CallWildBattleEx 487, 100, 1, 1
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_4
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 2
    VMJumpIf CMP_NE, .LRP_66
    FlagSet 1066
    pl_msg_sys 28
    pl_WaitButton
    pl_CloseMessage
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 112
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
.LRP_66:
    pl_ReleaseAll
    VMHalt
.LRP_65:
.LRP_63end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_4:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_4:
    FlagSet 48
    VMHalt

RP_Name_4:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 29, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_4:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 30, 0, 13, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_5:
    pl_LockAll
    FlagGet 1071, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_67notdone
    pl_msg_sys 30
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_67notdone:
    ItemCheckAmount 132, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_68have
    pl_msg_sys 31
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_68have:
    pl_msg_sys 32
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_69end
    WorkSetConst 0x8051, 0
.LRP_70chosen:
    pl_CloseMessage
    ItemSub 132, 1, 0x8050
    pl_msg_sys 33
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_71
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 250, 0
    PVWait
    CallWildBattleEx 250, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_5
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_72
    FlagSet 1071
.LRP_72:
    pl_ReleaseAll
    VMHalt
.LRP_71:
.LRP_69end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_5:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_5:
    FlagSet 48
    VMHalt

RP_Name_5:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 34, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_5:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 44, 0, 32, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_6:
    pl_LockAll
    FlagGet 1061, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_73notdone
    pl_msg_sys 35
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_73notdone:
    ItemCheckAmount 124, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_74have
    pl_msg_sys 36
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_74have:
    pl_msg_sys 37
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_75end
    WorkSetConst 0x8051, 0
.LRP_76chosen:
    pl_CloseMessage
    ItemSub 124, 1, 0x8050
    pl_msg_sys 38
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_77
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 249, 0
    PVWait
    CallWildBattleEx 249, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_6
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_78
    FlagSet 1061
.LRP_78:
    pl_ReleaseAll
    VMHalt
.LRP_77:
.LRP_75end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_6:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_6:
    FlagSet 48
    VMHalt

RP_Name_6:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 39, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_6:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 23, 0, 25, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_7:
    pl_LockAll
    FlagGet 1062, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_79notdone
    pl_msg_sys 40
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_79notdone:
    ItemCheckAmount 125, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_80have
    pl_msg_sys 41
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_80have:
    pl_msg_sys 42
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_81end
    WorkSetConst 0x8051, 0
.LRP_82chosen:
    pl_CloseMessage
    ItemSub 125, 1, 0x8050
    pl_msg_sys 43
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_83
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 382, 0
    PVWait
    CallWildBattleEx 382, 70, 0, 1
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_7
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_84
    FlagSet 1062
    pl_msg_sys 44
    pl_WaitButton
    pl_CloseMessage
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 208
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 209
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 210
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
.LRP_84:
    pl_ReleaseAll
    VMHalt
.LRP_83:
.LRP_81end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_7:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_7:
    FlagSet 48
    VMHalt

RP_Name_7:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 45, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_7:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 27, 0, 25, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_8:
    pl_LockAll
    FlagGet 1063, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_85notdone
    pl_msg_sys 46
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_85notdone:
    ItemCheckAmount 126, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_86have
    pl_msg_sys 47
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_86have:
    pl_msg_sys 48
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_87end
    WorkSetConst 0x8051, 0
.LRP_88chosen:
    pl_CloseMessage
    ItemSub 126, 1, 0x8050
    pl_msg_sys 49
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_89
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 383, 0
    PVWait
    CallWildBattleEx 383, 70, 0, 1
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_8
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_90
    FlagSet 1063
    pl_msg_sys 50
    pl_WaitButton
    pl_CloseMessage
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 201
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 203
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 202
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
.LRP_90:
    pl_ReleaseAll
    VMHalt
.LRP_89:
.LRP_87end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_8:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_8:
    FlagSet 48
    VMHalt

RP_Name_8:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 51, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_8:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 33, 0, 12, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_9:
    pl_LockAll
    FlagGet 1064, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_91notdone
    pl_msg_sys 52
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_91notdone:
    ItemCheckAmount 127, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_92have
    pl_msg_sys 53
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_92have:
    pl_msg_sys 54
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_93end
    WorkSetConst 0x8051, 0
.LRP_94chosen:
    pl_CloseMessage
    ItemSub 127, 1, 0x8050
    pl_msg_sys 55
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_95
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 384, 0
    PVWait
    CallWildBattleEx 384, 70, 0, 1
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_9
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_96
    FlagSet 1064
    pl_msg_sys 56
    pl_WaitButton
    pl_CloseMessage
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 212
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, 211
    WorkSetConst 0x8001, 1
    RTCallGlobal 2801
    VMStackPop 0x8001
    VMStackPop 0x8000
.LRP_96:
    pl_ReleaseAll
    VMHalt
.LRP_95:
.LRP_93end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_9:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_9:
    FlagSet 48
    VMHalt

RP_Name_9:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 57, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_9:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 37, 0, 12, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Pedestal_10:
    pl_LockAll
    FlagGet 1065, 0x8057
    WorkCmpConst 0x8057, 0
    VMJumpIf CMP_EQ, .LRP_97notdone
    pl_msg_sys 58
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_97notdone:
    ItemCheckAmount 128, 1, 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_EQ, .LRP_98have
    pl_msg_sys 59
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_98have:
    pl_msg_sys 60
    YesNoWin 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_99end
    WorkSetConst 0x8051, 0
.LRP_100chosen:
    pl_CloseMessage
    ItemSub 128, 1, 0x8050
    pl_msg_sys 61
    pl_WaitButton
    pl_CloseMessage
    ActorCmdExec PL_PLAYER, RP_MovStepBack
    ActorCmdWait
    FadeOutWhite
    FadeWait
    WorkCmpConst 0x8051, 0
    VMJumpIf CMP_NE, .LRP_101
    FlagReset 48
    ActorAdd 1
    FadeInWhite
    FadeWait
    PVPlay 150, 0
    PVWait
    CallWildBattleEx 150, 70, 0, 9
    WildBattleIsVictory 0x8050
    WorkCmpConst 0x8050, 1
    VMJumpIf CMP_NE, .LRP_lost_10
    ActorDelete 1
    FlagSet 48
    CallWildBattleEnd
    WildBattleGetResult 0x8050
    WorkCmpConst 0x8050, 0
    VMJumpIf CMP_NE, .LRP_102
    FlagSet 1065
.LRP_102:
    pl_ReleaseAll
    VMHalt
.LRP_101:
.LRP_99end:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt
.LRP_lost_10:
    WorkSetConst 0x40B1, 0
    CallWildLose
    VMHalt

RP_Init_10:
    FlagSet 48
    VMHalt

RP_Name_10:
    ActorsPauseAll
    WorkSetConst 0x401D, 1
    SEPlay SEQ_SE_MESSAGE
    InfoMsg 62, 2
    VMSleep 60
    InfoMsgClose_0039
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

RP_Closed_10:
    pl_LockAll
    pl_msg_sys 5
    pl_WaitButton
    pl_CloseMessage
    FadeOutBlack
    FadeWait
    RTReserveScript PL_RAMANAS_PARK_ARRIVE
    MapChangeCore PL_RAMANAS_PARK_ZONE, 41, 0, 12, 1
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0
RP_MovStepBack:
    Move 0x0D, 1
    Move 0x00, 1
    MoveEnd
    .balign 4, 0

