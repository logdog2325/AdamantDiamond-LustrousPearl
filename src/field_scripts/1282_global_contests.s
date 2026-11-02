// Global scripts 10785-10787 (a/0/5/6 entry 1282; no Black 2 script calls the file's own): Pearl's three Contest counters,
// Pearl's scripts_contests (pokeplatinum res/field/scripts as the guide). Text: a/0/0/3 file 413 (src/text/script/0413_contests.txt,
// from b2tools/contest_data.py, Pearl's bank 203). Link play is cut: the link counter says so. Pearl's walks to the door, the
// hall scene with its four contestants and flashes (Pearl's walking NPCs) are left out: the receptionist sends the player in
// and the stage starts (notes/CONTESTS.md). Called by RTCallGlobal: each entry ends in VMReturn after FinishAllEvents' work.
// Works 0x8058-0x805D: script-local, kept across calls; the Secret Bases keep 0x8050-0x8057.
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"
#include "pearl_contests_lines.inc"

#define W_RANK 0x8058
#define W_TYPE 0x8059
#define W_MODE 0x805A
#define W_SLOT 0x805B
#define W_RES 0x805C
#define W_MENU 0x805D
#define MODE_OFFICIAL 2
#define MODE_PRACTICE_VISUAL 3
#define MODE_PRACTICE_DANCE 4
#define MODE_PRACTICE_ACTING 5

    ScriptEntry Contests_Official
    ScriptEntry Contests_Link
    ScriptEntry Contests_Practice
    ScriptEntry Poffins_Counter
    ScriptEntry Poffins_CaseFromBag
    ScriptEntriesEnd

// ---- the official counter ------------------------------------------------------------------------------------------
Contests_Official:
    pl_PlaySE SEQ_SE_MESSAGE
    pl_LockAll
    pl_FacePlayer
    WorkSetConst W_MODE, MODE_OFFICIAL
    pl_msg_talk CCL_Welcome
Contests_AskEnter:
    pl_msg_talk CCL_EnterPokemonInAContest
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_MENU
    ListMenuAdd CCL_ContestEnter, 65535, 0
    ListMenuAdd CCL_ContestInfo, 65535, 1
    ListMenuAdd CCL_ContestExit, 65535, 2
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_MENU, 0
    VMJumpIf CMP_EQ, Contests_RankMenu
    WorkCmpConst W_MENU, 1
    VMJumpIf CMP_EQ, Contests_Info
Contests_MenuExit:
    pl_msg_talk CCL_LookForwardToParticipation
    pl_WaitButton
    VMJump Contests_End

Contests_Info:
    pl_msg_talk CCL_WhatWouldYouLikeToKnow1
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_MENU
    ListMenuAdd CCL_032, 65535, 0
    ListMenuAdd CCL_033, 65535, 1
    ListMenuAdd CCL_034, 65535, 2
    ListMenuAdd CCL_035, 65535, 3
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_MENU, 0
    VMJumpIf CMP_EQ, Contests_InfoBasics
    WorkCmpConst W_MENU, 1
    VMJumpIf CMP_EQ, Contests_InfoTypes
    WorkCmpConst W_MENU, 2
    VMJumpIf CMP_EQ, Contests_InfoRanks
    VMJump Contests_AskEnter
Contests_InfoTypes:
    pl_msg_talk CCL_ExplainContestTypes
    VMJump Contests_Info
Contests_InfoRanks:
    pl_msg_talk CCL_ExplainContestRanks
    VMJump Contests_Info
Contests_InfoBasics:
    pl_msg_talk CCL_WhatWouldYouLikeToKnow2
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_MENU
    ListMenuAdd CCL_WhatsAContest, 65535, 0
    ListMenuAdd CCL_VisualCompetition, 65535, 1
    ListMenuAdd CCL_DanceCompetition, 65535, 2
    ListMenuAdd CCL_ActingCompetition, 65535, 3
    ListMenuAdd CCL_CancelCompetition, 65535, 4
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_MENU, 0
    VMJumpIf CMP_NE, .Lb1
    pl_msg_talk CCL_ExplainOfficialContest
    VMJump Contests_InfoBasics
.Lb1:
    WorkCmpConst W_MENU, 1
    VMJumpIf CMP_NE, .Lb2
    pl_msg_talk CCL_ExplainVisualContest
    VMJump Contests_InfoBasics
.Lb2:
    WorkCmpConst W_MENU, 2
    VMJumpIf CMP_NE, .Lb3
    pl_msg_talk CCL_ExplainDanceContest
    VMJump Contests_InfoBasics
.Lb3:
    WorkCmpConst W_MENU, 3
    VMJumpIf CMP_NE, Contests_Info
    pl_msg_talk CCL_ExplainActingContest
    VMJump Contests_InfoBasics

Contests_RankMenu:
    pl_msg_talk CCL_SelectRank
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_RANK
    ListMenuAdd CCL_041, 65535, 0
    ListMenuAdd CCL_042, 65535, 1
    ListMenuAdd CCL_043, 65535, 2
    ListMenuAdd CCL_044, 65535, 3
    ListMenuAdd CCL_045, 65535, 4
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_RANK, 4
    VMJumpIf CMP_GE, Contests_MenuExit
    pl_msg_talk CCL_SelectContestType
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_TYPE
    ListMenuAdd CCL_046, 65535, 0
    ListMenuAdd CCL_047, 65535, 1
    ListMenuAdd CCL_048, 65535, 2
    ListMenuAdd CCL_049, 65535, 3
    ListMenuAdd CCL_050, 65535, 4
    ListMenuAdd CCL_051, 65535, 5
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_TYPE, 5
    VMJumpIf CMP_GE, Contests_MenuExit
Contests_Choose:
    pl_msg_talk CCL_EnterWhichPokemonOfficial
    pl_msg_talk CCL_PleaseChoosePokemonOfficial
    pl_CloseMessage
    pl_ChoosePokemonMenu
    pl_GetSelectedPartySlot W_SLOT
    WorkCmpConst W_SLOT, 255
    VMJumpIf CMP_NE, .Lchosen
    pl_msg_talk CCL_CancelEntry
    YesNoWin W_RES
    MsgWinCloseAll
    WorkCmpConst W_RES, 0
    VMJumpIf CMP_EQ, Contests_MenuExit
    VMJump Contests_Choose
.Lchosen:
    pl_ContestEntry W_SLOT, W_RANK, W_TYPE, W_RES
    WorkCmpConst W_RES, 0
    VMJumpIf CMP_EQ, .Lentered
    pl_msg_talk CCL_CantEnter
    VMJump Contests_Choose
.Lentered:
    pl_BufferNumber 0, 4        // the player goes last (ENTRY_SLOT); Pearl's BufferContestRegistrationEntryNumber
    pl_msg_talk CCL_YourPokemonHasBeenAccepted
    pl_msg_talk CCL_ContestWillStart
    pl_CloseMessage
    TrainerCardGetSex W_RES
    pl_BufferPlayerName 0
    WorkCmpConst W_RES, 0
    VMJumpIf CMP_NE, .Ldress
    pl_msg_sys CCL_PlayerChangedIntoTuxedo
    VMJump .Ldressed
.Ldress:
    pl_msg_sys CCL_PlayerChangedIntoDress
.Ldressed:
    pl_msg_sys CCL_RightThisWayPlease1
    pl_CloseMessage
    VMCall Contests_RunStage
    // Pearl's GetFirstTimeVictoryAccessory, the prize of the first win of this rank and type
    WorkCmpConst W_RES, 0
    VMJumpIf CMP_NE, .Lthanks
    pl_FirstWinAccessory W_RANK, W_TYPE, W_MENU
    WorkCmpConst W_MENU, 65535
    VMJumpIf CMP_EQ, .Lthanks
    pl_msg_talk CCL_HeresYourPrize
    pl_CloseMessage
    pl_PlayFanfare SEQ_ME_ACCE
    pl_BufferPlayerName 0
    pl_BufferAccessoryWord 1, W_MENU
    pl_AddAccessory W_MENU, 1
    pl_msg_sys CCL_Received
    pl_WaitFanfare
    pl_CloseMessage
.Lthanks:
    pl_msg_talk CCL_ThankYouForParticipating
    pl_WaitButton
    VMJump Contests_End

// The stage: Pearl's song stays with the screen, the field's comes back (trap 4 of the brief)
Contests_RunStage:
    SEPlay SEQ_SE_KAIDAN
    SEWait
    BGMPush 0                               // (the event fades out, runs the screen and fades the field back in itself)
    pl_ContestRun W_SLOT, W_RANK, W_TYPE, W_MODE, W_RES
    BGMPop 0, 0
    VMReturn

// ---- the link counter: link play is cut --------------------------------------------------------------------------------
Contests_Link:
    pl_PlaySE SEQ_SE_MESSAGE
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk CCL_LinkClosed
    pl_WaitButton
    VMJump Contests_End

// ---- the practice counter ----------------------------------------------------------------------------------------------
Contests_Practice:
    pl_PlaySE SEQ_SE_MESSAGE
    pl_LockAll
    pl_FacePlayer
    WorkSetConst W_RANK, 0
    pl_msg_talk CCL_IntroductionPracticeContest
Contests_PracticeMenu:
    pl_msg_talk CCL_JoinPracticeContest
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_MENU
    ListMenuAdd CCL_Practice, 65535, 0
    ListMenuAdd CCL_Info2, 65535, 1
    ListMenuAdd CCL_Exit2, 65535, 2
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_MENU, 0
    VMJumpIf CMP_EQ, Contests_PracticeKind
    WorkCmpConst W_MENU, 1
    VMJumpIf CMP_NE, Contests_PracticeExit
    pl_msg_talk CCL_ExplainPracticeContest
    VMJump Contests_PracticeMenu
Contests_PracticeExit:
    pl_msg_talk CCL_LookForwardToNextVisit3
    pl_WaitButton
    VMJump Contests_End
Contests_PracticeKind:
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_MENU
    ListMenuAdd CCL_VisualPractice, 65535, 0
    ListMenuAdd CCL_DancePractice, 65535, 1
    ListMenuAdd CCL_ActingPractice, 65535, 2
    ListMenuAdd CCL_CancelPractice, 65535, 3
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_MENU, 3
    VMJumpIf CMP_GE, Contests_PracticeExit
    WorkSet W_MODE, W_MENU
    WorkAdd W_MODE, MODE_PRACTICE_VISUAL
    WorkSetConst W_TYPE, 0
    WorkCmpConst W_MODE, MODE_PRACTICE_DANCE
    VMJumpIf CMP_EQ, Contests_PracticeChoose
    pl_msg_talk CCL_ChallengeWhichContest
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_TYPE
    ListMenuAdd CCL_Cool, 65535, 0
    ListMenuAdd CCL_Beauty, 65535, 1
    ListMenuAdd CCL_Cute, 65535, 2
    ListMenuAdd CCL_Smart, 65535, 3
    ListMenuAdd CCL_Tough, 65535, 4
    ListMenuAdd CCL_Exit3, 65535, 5
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_TYPE, 5
    VMJumpIf CMP_GE, Contests_PracticeExit
Contests_PracticeChoose:
    pl_msg_talk CCL_EnterWhichPokemonPractice
    pl_msg_talk CCL_PleaseChoosePokemonPractice
    pl_CloseMessage
    pl_ChoosePokemonMenu
    pl_GetSelectedPartySlot W_SLOT
    WorkCmpConst W_SLOT, 255
    VMJumpIf CMP_EQ, Contests_PracticeExit
    pl_ContestEntry W_SLOT, 0, W_TYPE, W_RES
    WorkCmpConst W_RES, 0
    VMJumpIf CMP_EQ, .Lpractice
    pl_msg_talk CCL_CantEnter
    VMJump Contests_PracticeChoose
.Lpractice:
    pl_BufferNumber 0, 4        // the player goes last (ENTRY_SLOT); Pearl's BufferContestRegistrationEntryNumber
    pl_msg_talk CCL_RegisteredForPractice
    pl_msg_talk CCL_RightThisWayPlease2
    pl_CloseMessage
    VMCall Contests_RunStage
    // Pearl's Contests_AssessPracticeResults: first or second place is "popular"; try again?
    WorkCmpConst W_MODE, MODE_PRACTICE_VISUAL
    VMJumpIf CMP_NE, .Lp1
    WorkCmpConst W_RES, 1
    VMJumpIf CMP_GT, .Lp0f
    pl_msg_talk CCL_CompletedVisualPractice
    VMJump .Lpask
.Lp0f:
    pl_msg_talk CCL_FailedVisualPractice
    VMJump .Lpask
.Lp1:
    WorkCmpConst W_MODE, MODE_PRACTICE_DANCE
    VMJumpIf CMP_NE, .Lp2
    WorkCmpConst W_RES, 1
    VMJumpIf CMP_GT, .Lp1f
    pl_msg_talk CCL_CompletedDancePractice
    VMJump .Lpask
.Lp1f:
    pl_msg_talk CCL_FailedDancePractice
    VMJump .Lpask
.Lp2:
    WorkCmpConst W_RES, 1
    VMJumpIf CMP_GT, .Lp2f
    pl_msg_talk CCL_CompletedActingPractice
    VMJump .Lpask
.Lp2f:
    pl_msg_talk CCL_FailedActingPractice
.Lpask:
    YesNoWin W_RES
    MsgWinCloseAll
    WorkCmpConst W_RES, 0
    VMJumpIf CMP_EQ, .Lpractice
    pl_msg_talk CCL_182
    pl_WaitButton

// ---- Poffins: Pearl's scripts_poffin_common (the cooking counter): cooking in a group is link play, cut ------------------
#define ITEM_POFFIN_CASE_PL 449
Poffins_Counter:
    pl_PlaySE SEQ_SE_MESSAGE
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk CPL_HereYouMayCookPoffins
Poffins_Menu:
    pl_msg_talk CPL_CookAloneOrWithOthers
    ListMenu_AnchorTopRight 31, 1, 0, 1, W_MENU
    ListMenuAdd CPL_Alone, 65535, 0
    ListMenuAdd CPL_Info, 65535, 1
    ListMenuAdd CPL_Exit, 65535, 2
    ListMenuShow
    MsgWinCloseAll
    WorkCmpConst W_MENU, 0
    VMJumpIf CMP_EQ, Poffins_Alone
    WorkCmpConst W_MENU, 1
    VMJumpIf CMP_NE, Poffins_Bye
    pl_msg_talk CPL_ExplainCooking
    pl_WaitButton
    VMJump Poffins_Menu
Poffins_Bye:
    pl_msg_talk CPL_PleaseVisitAgain
    pl_WaitButton
    VMJump Contests_End
Poffins_Alone:
    ItemCheckAmount ITEM_POFFIN_CASE_PL, 1, W_RES
    WorkCmpConst W_RES, 1
    VMJumpIf CMP_EQ, .Lcase
    pl_msg_talk CPL_MustHavePoffinCase
    pl_WaitButton
    VMJump Contests_End
.Lcase:
    pl_PoffinCanCook W_RES
    WorkCmpConst W_RES, 1
    VMJumpIf CMP_NE, .Lberry
    pl_msg_talk CPL_NoBerryToCook
    VMJump Poffins_Bye
.Lberry:
    WorkCmpConst W_RES, 2
    VMJumpIf CMP_NE, .Lcook
    pl_msg_talk CPL_PoffinCaseIsFull
    VMJump Poffins_Bye
.Lcook:
    pl_CloseMessage
    BGMPush 0
    pl_PoffinCook W_RES
    BGMPop 0, 0
    VMJump Poffins_Bye

// The Case from the Bag (ov142's row, the field's common event): choose a Poffin, a Pokémon, feed it; Pearl's lines
Poffins_CaseFromBag:
    pl_LockAll
Poffins_CaseAgain:
    pl_PoffinCase W_MENU
    WorkCmpConst W_MENU, 65535
    VMJumpIf CMP_EQ, Poffins_CaseEnd
    pl_ChoosePokemonMenu
    pl_GetSelectedPartySlot W_SLOT
    WorkCmpConst W_SLOT, 255
    VMJumpIf CMP_EQ, Poffins_CaseAgain
    pl_BufferPartyMonNickname 0, W_SLOT
    pl_PoffinFeed W_MENU, W_SLOT, W_RES
    WorkCmpConst W_RES, 3
    VMJumpIf CMP_NE, .Late
    pl_msg_sys CPL_WontEat
    VMJump .Lfed
.Late:
    WorkCmpConst W_RES, 0
    VMJumpIf CMP_NE, .Lnot_liked
    pl_msg_sys CPL_LikedPoffin
    VMJump .Lfed
.Lnot_liked:
    WorkCmpConst W_RES, 1
    VMJumpIf CMP_NE, .Lneutral
    pl_msg_sys CPL_DislikedPoffin
    VMJump .Lfed
.Lneutral:
    pl_msg_sys CPL_NeutralToPoffin
.Lfed:
    pl_WaitButton
    pl_CloseMessage
    VMJump Poffins_CaseAgain

// the Bag's event starts this script itself: no caller to return to
Poffins_CaseEnd:
    pl_CloseMessage
    pl_ReleaseAll
    VMHalt

Contests_End:
    pl_CloseMessage
    pl_ReleaseAll
    VMReturn
