// MAP_FULLMOON_ISLAND_INTERIOR: Pearl script file 274, text bank 243. Written by b2tools/pearl_story.py:
// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).
// Scripts 1-2: Pearl's; no warp continuations; 3: PearlArrive
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry P274_S1
    ScriptEntry P274_S2
    ScriptEntry PearlArrive
    ScriptEntriesEnd

P274_S1:
P274_000A:
    pl_End

P274_S2:
P274_000C:
    pl_LockAll
    pl_PlaySE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_WaitSE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    MsgWinCloseAll  // (as Black 2's own uses: its window needs the message window gone)
    CallPokemonPreview 488, 0, 1, 0  // ShowPokemonPic
// WaitABPress: Black 2's Pokémon window waits itself
// RemovePokemonPreview: Black 2's window closed itself
    pl_PlayCry 488
    pl_GetPlayerDir PVAR_800C
    pl_CompareVarToValue PVAR_800C, 0
    pl_CallIf 1, P274_0069
// ReleaseObject 0: nothing in Black 2 (Black 2 pauses all actors (LockAll) only)
    pl_FlickerObject 0, 6, 8
// LockObject 0: nothing in Black 2 (Black 2 pauses all actors (LockAll) only)
    pl_SetFlag PFLAG_026D
    pl_RemoveObject 0, PFLAG_026D
    pl_ClearFlag PFLAG_0436
    pl_AddObjectAt 1, 0, 0  // at its SetObjectEventPos
    pl_stub ActivateRoamingPokemon  // Pearl 0x21C CreateRoamer 1: not translated yet
    pl_SetFlag PFLAG_011F
    pl_msg_sys 0
    pl_WaitButton
    pl_CloseMessage
    pl_ReleaseAll
    pl_End

P274_0069:
    pl_SetObjectEventPosLater 0, 1, 16, 0, 14, 0  // SetObjectEventPos 1 (the live actor; and where AddObject puts it)
    pl_ApplyMovement 0, P274_0080
    pl_WaitMovement
    pl_Return

    .balign 4, 0
P274_0080:
    Move 71, 1  // LOCK_DIR
    Move 12, 1  // WALK_NORMAL_NORTH
    Move 72, 1  // UNLOCK_DIR
    MoveEnd

PearlNoScript:
    VMHalt

PearlArrive:                      // arriving by a script warp with nothing after it: fade in, release
    FadeInBlack
    FadeWait
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0
