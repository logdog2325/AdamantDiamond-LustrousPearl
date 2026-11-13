#include "pearlb2.h"
#include "pearlb2/plat_arcade.h"
#include "pearlb2/plat_frontier.h"
#include "types.h"
#include "battle/btl_handler.h"
#include "battle/btl_main.h"
#include "battle/btl_pokeparam.h"
#include "battle/btl_server_flow.h"
#include "battle/btl_setup.h"
#include "field/field_script.h"
#include "gfl/overlay.h"
#include "gfl/std.h"
#include "pml/poke_party.h"
#include "system/game_event.h"
#include "system/game_system.h"
#include "system/vm.h"

// PearlB2: the resident side of Platinum's Battle Arcade (include/pearlb2/plat_arcade.h, plat-arcade 2026-11-07).
// - The core's row for the Arcade (resident/plat_frontier.c sFacilityOps: ops 0x80-0x9f) comes here. The Arcade's code and rules
//   are overlay 381 (PLATARCADE_OVERLAY_ID, src/pearlb2/plat_arcade/*.c), at the address of Black 2's gimmick overlays (no zone
//   of the Arcade has a gimmick): loaded here, run, unloaded before the op returns. If it can't load, the arguments' length is
//   unknown: the script stops, as for an unknown op.
// - The board (PLATARCADE_OP_BOARD) runs over many frames, so its code must stay in: Black 2's GameEvent_CreateOverlayDelegate
//   loads the overlay, has PlatArcade_BoardEventProvider (in it) make the board's event, runs it and unloads the overlay when it
//   ends; the script goes on after it.
// - The battle's setup lives from the start op to the cleanup op, across the battle, while the overlay is unloaded: its pointer
//   is kept here, with the battle's start effect.
// - PearlB2_Arcade_StoreParties: from the Castle's battle-end hook (resident/plat_castle_ext.c PearlB2_Castle_StoreParties, which
//   ov167 btl_main.c's BtlMain_StorePartiesToSetup call reaches). Black 2 puts the party as it left a battle into the setup only
//   for wild and Trainer battles; for the Arcade's, and only for it, both sides' parties as they left go into the setup (party 0
//   the player's side, 1 the enemy's), Black 2's own copy (PokeCon_StoreClientSrcPartyInOrder), without its giving back of held
//   items (a Trainer battle's): as Platinum, an item used up is gone. The cleanup op reads them: the performance (the player's
//   side), the held items (the player's own Pokémon: the enemy's side after the swap).
// - PearlB2_Arcade_AfterSwitchIn: ov167 btl_server_flow.c BtlServerFlow_StartBattle's ServerControl_AfterSwitchIn call comes here
//   (a call of the same size: plat-arcade_decomp.diff). For the Arcade's battle that the board gave Trick Room, Trick Room for
//   five turns first (Platinum's subscript_overworld_trick_room: FIELD_CONDITION_TRICK_ROOM_INIT, before the abilities on entry),
//   as Black 2's own move sets it (ServerControl_FieldEffectCore, Trick Room's handler's effect and turns). Black 2's battle text
//   has no line for it without a Pokémon (Platinum's "The dimensions became distorted!"): the room's line before the battle says
//   it. Every other battle is as before.

#if PEARLB2

#define FIELD_EFFECT_TRICK_ROOM 1       // constants/battle.h FIELD_CONDITION_TRICK_ROOM (move_handlers.c HandlerTrickRoom: 1, 5 turns)
#define TRICK_ROOM_TURNS 5

static BtlSetup *sArcadeBattle;
static u32 sStartEffects;

void PearlB2_Arcade_SetBattle(BtlSetup *setup, u32 startEffects) {
    sArcadeBattle = setup;
    sStartEffects = startEffects;
}

BtlSetup *PearlB2_Arcade_GetBattle(void) {
    return sArcadeBattle;
}

void PearlB2_Arcade_StoreParties(BtlMainModule *mainModule) {
    BtlSetup *setup = mainModule->setup;
    u8 clientId = mainModule->playerClientId;
    u8 enemy;

    if (sArcadeBattle == NULL || setup != sArcadeBattle || setup->battleType <= 1 || setup->party[0] == NULL ||
        setup->party[1] == NULL) {
        return;
    }
    enemy = (u8)GetOpponentClientID(mainModule, clientId, 0);
    PokeCon_StoreClientSrcPartyInOrder(&mainModule->pokeCons[1], mainModule, clientId);
    PokeParty_Copy(PokeCon_GetSrcParty(&mainModule->pokeCons[1], clientId), setup->party[0]);
    PokeCon_StoreClientSrcPartyInOrder(&mainModule->pokeCons[1], mainModule, enemy);
    PokeParty_Copy(PokeCon_GetSrcParty(&mainModule->pokeCons[1], enemy), setup->party[1]);
}

BOOL PearlB2_Arcade_AfterSwitchIn(BtlServerFlow *flow) {
    BOOL trickRoom = FALSE;

    if ((sStartEffects & PLATARCADE_START_TRICK_ROOM) && sArcadeBattle != NULL &&
        GetBattleSetup(flow->mainModule) == sArcadeBattle) {
        sStartEffects &= ~PLATARCADE_START_TRICK_ROOM;
        trickRoom = ServerControl_FieldEffectCore(flow, FIELD_EFFECT_TRICK_ROOM, SetConditionTurns(TRICK_ROOM_TURNS), FALSE);
    }
    if (ServerControl_AfterSwitchIn(flow)) {
        return TRUE;
    }
    return trickRoom;
}

static BOOL Board(VM *vm, FieldScriptEnv *env) {
    GameSystem *gsys = FieldScriptEnv_GetGameSystem(env);
    PlatArcadeBoardArgs args;

    args.firstLine = ScriptReadAny(vm, env);
    args.msgData = GetFieldScriptMsgData(env);
    if (!GFL_OvlLoad(PLATARCADE_OVERLAY_ID)) {      // (something sits at the address: the delegate's own load would fail too)
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    GFL_OvlUnload(PLATARCADE_OVERLAY_ID);
    ScriptWork_CallEvent(FieldScriptEnv_GetScriptWork(env),
                         GameEvent_CreateOverlayDelegate(gsys, PLATARCADE_OVERLAY_ID, PlatArcade_BoardEventProvider, &args));
    return TRUE;
}

BOOL PearlB2_Ext_Arcade(VM *vm, FieldScriptEnv *env, u32 op) {
    BOOL result;

    if (op == PLATARCADE_OP_BOARD) {
        return Board(vm, env);
    }
    if (op >= PLATARCADE_OP_COUNT || !GFL_OvlLoad(PLATARCADE_OVERLAY_ID)) {
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    result = PlatArcade_Op(vm, env, op);
    GFL_OvlUnload(PLATARCADE_OVERLAY_ID);
    return result;
}

#endif
