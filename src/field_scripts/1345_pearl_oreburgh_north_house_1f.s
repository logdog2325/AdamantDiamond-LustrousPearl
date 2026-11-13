// MAP_OREBURGH_NORTH_HOUSE_1F: Pearl script file 58, text bank 67. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-2: Pearl's; no warp continuations; 3: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P58_S1
    ScriptEntry P58_S2
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P58_S1:
P58_000A:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_0085
    pl_GoToIf 1, P58_00B3
    pl_msg_talk 0
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P58_0037
    pl_GoTo P58_00A8

P58_0037:
    pl_CloseMessage
// FadeScreen 6, 1, 0, 0x0: Black 2's party select fades itself
    pl_WaitFadeScreen
    pl_ChoosePokemonMenu  // OpenPartyMenuForTrade: Black 2's party select (CallPokeSelect)
    pl_GetSelectedPartySlot PVAR_800C  // the slot, 255 when cancelled (as Platinum)
// RestoreOverworld: Black 2's party select reopened the field itself
// FadeScreen 6, 1, 1, 0x0: Black 2's party select fades itself
    pl_WaitFadeScreen
    pl_CompareVarToValue PVAR_800C, 255
    pl_GoToIf 1, P58_00A8
// InitNPCTrade 0: Kazza (species 63) for species 66 (the commands below name it)
    pl_SetVarFromVar PVAR_8004, PVAR_800C
    pl_GetPartyMonSpecies PVAR_8004, PVAR_8005
    pl_SetVarFromValue PVAR_800C, 66  // GetNPCTradeRequestedSpecies: trade 0 wants species 66
    pl_CompareVarToVar PVAR_8005, PVAR_800C
    pl_GoToIf 5, P58_009B
    pl_StartNPCTrade 0, PVAR_8004  // Kazza (species 63) for species 66: Black 2's trade event and demo
// FinishNPCTrade: nothing to free (the trade event frees its own)
    pl_SetFlag PFLAG_0085
    pl_msg_talk 1
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P58_009B:
// FinishNPCTrade: nothing to free (the trade event frees its own)
    pl_msg_talk 2
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P58_00A8:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 3
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P58_00B3:
    pl_msg_talk 4
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P58_S2:
P58_00BE:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_msg_talk 5
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
