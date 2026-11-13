// MAP_SNOWPOINT_NORTHWEST_HOUSE: Pearl script file 174, text bank 171. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-2: Pearl's; no warp continuations; 3: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P174_S1
    ScriptEntry P174_S2
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P174_S1:
P174_000A:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_00F4
    pl_GoToIf 1, P174_0028
    pl_msg_talk 0
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P174_0028:
    pl_msg_talk 1
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P174_S2:
P174_0033:
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_LockAll
    pl_FacePlayer
    pl_CheckFlag PFLAG_00F4
    pl_GoToIf 1, P174_00DC
    pl_msg_talk 2
    pl_ShowYesNoMenu PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, P174_0060
    pl_GoTo P174_00D1

P174_0060:
    pl_CloseMessage
// FadeScreen 6, 1, 0, 0x0: Black 2's party select fades itself
    pl_WaitFadeScreen
    pl_ChoosePokemonMenu  // OpenPartyMenuForTrade: Black 2's party select (CallPokeSelect)
    pl_GetSelectedPartySlot PVAR_800C  // the slot, 255 when cancelled (as Platinum)
// RestoreOverworld: Black 2's party select reopened the field itself
// FadeScreen 6, 1, 1, 0x0: Black 2's party select fades itself
    pl_WaitFadeScreen
    pl_CompareVarToValue PVAR_800C, 255
    pl_GoToIf 1, P174_00D1
// InitNPCTrade 2: Gaspar (species 93) for species 308 (the commands below name it)
    pl_SetVarFromVar PVAR_8004, PVAR_800C
    pl_GetPartyMonSpecies PVAR_8004, PVAR_8005
    pl_SetVarFromValue PVAR_800C, 308  // GetNPCTradeRequestedSpecies: trade 2 wants species 308
    pl_CompareVarToVar PVAR_8005, PVAR_800C
    pl_GoToIf 5, P174_00C4
    pl_StartNPCTrade 2, PVAR_8004  // Gaspar (species 93) for species 308: Black 2's trade event and demo
// FinishNPCTrade: nothing to free (the trade event frees its own)
    pl_SetFlag PFLAG_00F4
    pl_msg_talk 3
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P174_00C4:
// FinishNPCTrade: nothing to free (the trade event frees its own)
    pl_msg_talk 4
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P174_00D1:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_talk 5
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P174_00DC:
    pl_msg_talk 6
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
