#include "pearlb2.h"
#include "pearlb2/plat_frontier.h"
#include "pearlb2/plat_hall.h"
#include "types.h"
#include "gfl/overlay.h"
#include "gfl/std.h"
#include "system/vm.h"

// PearlB2: the resident side of Platinum's Battle Hall (include/pearlb2/plat_hall.h, plat-hall 2026-11-07). The core's row for
// the Hall (resident/plat_frontier.c sFacilityOps: ops 0x40-0x5f) comes here. The Hall's code and tables are overlay 379
// (PLATHALL_OVERLAY_ID, src/pearlb2/plat_hall/*.c), at the address of Black 2's gimmick overlays (no zone of the Hall has a
// gimmick): loaded here, run, unloaded before the op returns. If it can't load (something else is there), the arguments'
// length is unknown: the script stops, as for an unknown op. The battle's setup lives from the start op to the cleanup op,
// across the battle, while the overlay is unloaded: its pointer is kept here.

#if PEARLB2

static BtlSetup *sHallBattle;

BtlSetup *PearlB2_Hall_SetBattle(BtlSetup *setup) {
    BtlSetup *before = sHallBattle;

    sHallBattle = setup;
    return before;
}

BOOL PearlB2_Ext_Hall(VM *vm, FieldScriptEnv *env, u32 op) {
    BOOL result;

    if (op >= PLATHALL_OP_COUNT || !GFL_OvlLoad(PLATHALL_OVERLAY_ID)) {
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    result = PlatHall_Op(vm, env, op);
    GFL_OvlUnload(PLATHALL_OVERLAY_ID);
    return result;
}

#endif
