#include "pearlb2.h"
#include "pearlb2/plat_factory.h"
#include "types.h"
#include "gfl/overlay.h"
#include "gfl/std.h"
#include "system/vm.h"

// PearlB2: the resident side of Platinum's Battle Factory (plat-factory 2026-11-07; include/pearlb2/plat_factory.h): the
// Frontier's Factory row (ops 0x20-0x3f of sub-command 0x93, src/pearlb2/resident/plat_frontier.c). The Factory's code and
// rules are overlay 378, at Pal Park's address: loaded here, run, unloaded before the op returns (an op that starts a screen
// or the battle gives the script an event of Black 2's own, so nothing of the overlay runs after). If it can't load, the
// arguments' length is unknown: the script stops, as for an unknown sub-command.

#if PEARLB2

BOOL PearlB2_Frontier_Factory(VM *vm, FieldScriptEnv *env, u32 op) {
    BOOL result;

    if (op >= PLATFACTORY_OP_COUNT || !GFL_OvlLoad(PLATFACTORY_OVERLAY_ID)) {
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    result = PlatFactory_Op(vm, env, op);
    GFL_OvlUnload(PLATFACTORY_OVERLAY_ID);
    return result;
}

#endif
