#include "pearlb2.h"
#include "pearlb2/plat_castle.h"
#include "pearlb2/plat_arcade.h"     // (plat-arcade)
#include "pearlb2/plat_frontier.h"
#include "types.h"
#include "battle/btl_main.h"
#include "battle/btl_setup.h"
#include "gfl/overlay.h"
#include "gfl/std.h"
#include "pml/poke_party.h"
#include "system/vm.h"

// PearlB2: the resident side of Platinum's Battle Castle (include/pearlb2/plat_castle.h, plat-castle 2026-11-07).
// - The core's row for the Castle (resident/plat_frontier.c sFacilityOps: ops 0x60-0x7f) comes here. The Castle's code and rules
//   are overlay 380 (PLATCASTLE_OVERLAY_ID, src/pearlb2/plat_castle/*.c), at the address of Black 2's gimmick overlays (no zone
//   of the Castle has a gimmick): loaded here, run, unloaded before the op returns. If it can't load, the arguments' length is
//   unknown: the script stops, as for an unknown op.
// - The battle's setup lives from the start op to the cleanup op, across the battle, while the overlay is unloaded: its pointer
//   is kept here.
// - PearlB2_Castle_StoreParties: ov167 btl_main.c's call of BtlMain_StorePartiesToSetup at the battle's end comes here (a call
//   of the same size; the decomp's change is plat-castle's, in notes/PLATINUM_FRONTIER.md "The Battle Castle"). Black 2 puts
//   the player's party as it left the battle into the setup only for wild and Trainer battles (battleType 0 and 1); a facility
//   battle (2: the Subway's, the Trial House's, the Castle's) gets it back as it went in. For the Castle's battle, and only for
//   it (its setup, kept here), the party as it left goes into the setup the same way, Black 2's own copy (in the party's order,
//   PokeCon_StoreClientSrcPartyInOrder), without Black 2's giving back of held items (a Trainer battle's): as Platinum, an item
//   used up in a battle is gone. The cleanup op copies it into the castle's party: the HP, PP, status and items carry.

#if PEARLB2

static BtlSetup *sCastleBattle;

BtlSetup *PearlB2_Castle_SetBattle(BtlSetup *setup) {
    BtlSetup *before = sCastleBattle;

    sCastleBattle = setup;
    return before;
}

void PearlB2_Castle_StoreParties(BtlMainModule *mainModule) {
    BtlSetup *setup = mainModule->setup;
    u8 clientId = mainModule->playerClientId;

    BtlMain_StorePartiesToSetup(mainModule);
    if (sCastleBattle != NULL && setup == sCastleBattle && setup->battleType > 1 && setup->party[0] != NULL) {
        PokeCon_StoreClientSrcPartyInOrder(&mainModule->pokeCons[1], mainModule, clientId);
        PokeParty_Copy(PokeCon_GetSrcParty(&mainModule->pokeCons[1], clientId), setup->party[0]);
    }
    // ---- plat-arcade (2026-11-07): the Arcade's battle needs its parties back the same way (both sides: resident/plat_arcade_ext.c)
    PearlB2_Arcade_StoreParties(mainModule);
    // ---- end plat-arcade
}

BOOL PearlB2_Ext_Castle(VM *vm, FieldScriptEnv *env, u32 op) {
    BOOL result;

    if (op >= PLATCASTLE_OP_COUNT || !GFL_OvlLoad(PLATCASTLE_OVERLAY_ID)) {
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    result = PlatCastle_Op(vm, env, op);
    GFL_OvlUnload(PLATCASTLE_OVERLAY_ID);
    return result;
}

#endif
