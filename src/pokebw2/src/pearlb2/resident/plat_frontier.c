#include "pearlb2.h"
#include "pearlb2/plat_frontier.h"
#include "pearlb2/plat_factory.h"  // plat-factory
#include "pearlb2/plat_hall.h"     // (plat-hall)
#include "pearlb2/plat_castle.h"   // (plat-castle)
#include "pearlb2/plat_arcade.h"   // (plat-arcade)
#include "types.h"
#include "field/field_script.h"
#include "gfl/std.h"
#include "save/bsubway_save.h"
#include "save/save_control.h"
#include "system/game_data.h"
#include "system/vm.h"

// Platinum's Battle Frontier, its core (PearlB2's notes/PLATINUM_FRONTIER.md; include/pearlb2/plat_frontier.h). Reached
// through the Battle Tower's row of the extension command (resident/tower.c, EXT_TOWER_FRONTIER), then an op byte.

#if PEARLB2

typedef char FrontierCheckSaveSize[sizeof(PearlB2FrontierSave) <= sizeof(((BSubwayWifiData *)0)->players) ? 1 : -1];

// The facilities' ops, rows 0x20-0x9f: each piece sets its row (plat-factory, plat-hall, plat-castle, plat-arcade)
static const PearlB2FrontierHandler sFacilityOps[FRONTIER_FACILITIES] = {
    PearlB2_Frontier_Factory,           // plat-factory: src/pearlb2/resident/plat_factory_ext.c, overlay 378
    PearlB2_Ext_Hall,           // (plat-hall) ops 0x40-0x5f: resident/plat_hall_ext.c
    PearlB2_Ext_Castle,         // (plat-castle) ops 0x60-0x7f: resident/plat_castle_ext.c, overlay 380
    PearlB2_Ext_Arcade,         // (plat-arcade) ops 0x80-0x9f: resident/plat_arcade_ext.c, overlay 381
};

// Kept in RAM, as Platinum's scene manager keeps them: where ExitFrontier goes back to, and the manager's vars over a
// scene change. A reset during a challenge resumes in the lobby (the Tower's own resume), as Platinum's does.
static u16 sReturnSite;
static u16 sSceneVars[8];

PearlB2FrontierSave *PearlB2_Frontier_GetSave(SaveControl *save) {
    BSubwayWifiData *wifi = SaveControl_GetBlockPtr(save, SAVE_BLOCK_BSUBWAY_3A);
    PearlB2FrontierSave *frontier = (PearlB2FrontierSave *)wifi->players;

    if (frontier->magic != PLAT_FRONTIER_MAGIC) {
        MI_CpuFill8(frontier, 0, sizeof(PearlB2FrontierSave));
        frontier->magic = PLAT_FRONTIER_MAGIC;
    }
    return frontier;
}

// The Tower's records are Black 2's Battle Subway's (its score block, by play mode: 0 single, 1 double, 2 multi, 3 the
// wireless multi, 4 Wi-Fi), so the Frontier's records board and the Tower's own agree; even ids the record, odd the latest
u16 PearlB2_Frontier_GetStat(SaveControl *save, u32 stat) {
    BSubwayScoreData *score;

    if (stat >= PLAT_FRONTIER_STATS) {
        return 0;
    }
    if (stat < PLAT_FRONTIER_TOWER_STATS) {
        score = SaveControl_GetBlockPtr(save, SAVE_BLOCK_BSUBWAY_SCORE);
        return (stat & 1) ? BSubwayScoreData_GetStreak(score, stat / 2) : BSubwayScoreData_GetMaxStreak(score, stat / 2);
    }
    return PearlB2_Frontier_GetSave(save)->stats[stat];
}

void PearlB2_Frontier_SetStat(SaveControl *save, u32 stat, u16 value) {
    if (stat < PLAT_FRONTIER_TOWER_STATS || stat >= PLAT_FRONTIER_STATS) {
        return;                     // (the Tower's: Black 2's Subway writes them itself)
    }
    if (value > PLAT_FRONTIER_STAT_MAX) {
        value = PLAT_FRONTIER_STAT_MAX;
    }
    PearlB2_Frontier_GetSave(save)->stats[stat] = value;
}

static BOOL Frontier_Core(VM *vm, FieldScriptEnv *env, u32 op) {
    SaveControl *save = GameData_GetSaveControl(FieldScriptEnv_GetGameData(env));
    u16 a, b, c;
    u16 *var;
    u8 *flags;

    switch (op) {
    case FRONTIER_OP_SET_RETURN:
        sReturnSite = ScriptReadAny(vm, env);
        break;
    case FRONTIER_OP_GET_RETURN:
        var = ScriptReadVar(vm, env);
        *var = sReturnSite;
        break;
    case FRONTIER_OP_STAT_GET:
        a = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = PearlB2_Frontier_GetStat(save, a);
        break;
    case FRONTIER_OP_STAT_SET:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        PearlB2_Frontier_SetStat(save, a, b);
        break;
    case FRONTIER_OP_STAT_ADD:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = PearlB2_Frontier_GetStat(save, a);
        PearlB2_Frontier_SetStat(save, a, c + b > PLAT_FRONTIER_STAT_MAX ? PLAT_FRONTIER_STAT_MAX : c + b);
        break;
    case FRONTIER_OP_STAT_BEST:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        if (PearlB2_Frontier_GetStat(save, b) > PearlB2_Frontier_GetStat(save, a)) {
            PearlB2_Frontier_SetStat(save, a, PearlB2_Frontier_GetStat(save, b));
        }
        break;
    case FRONTIER_OP_STREAK_FLAG:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = 0;
        if (a < FRONTIER_FACILITIES && c < 8) {
            flags = &PearlB2_Frontier_GetSave(save)->streakFlags[a];
            if (b == 1) {
                *flags |= 1 << c;
            } else if (b == 2) {
                *flags &= ~(1 << c);
            }
            *var = (*flags >> c) & 1;
        }
        break;
    case FRONTIER_OP_SCENE_VAR:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        if (b < 8) {
            if (a == 0) {
                sSceneVars[b] = *var;
            } else {
                *var = sSceneVars[b];
            }
        }
        break;
    case FRONTIER_OP_TOWER_DISQUALIFY: {
        // (plat-fix2) Platinum's BT_FUNC_UNK_14 (pokeplatinum unk_02049D08.c sub_0204A064), after a reset without saving:
        // the streak flag (bit 8 + mode) goes, the room number is 0, the latest streak is 0. Black 2's BSubwayCmd_Tool 7
        // (func_ov033_0217b86c) does the first two (the round and the stage) but keeps the latest streak saved at the last
        // loss or seven wins. Platinum's challenge seed (sub_0206C02C) has no counterpart: Black 2's generator draws.
        BSubwayPlayData *play = SaveControl_GetBlockPtr(save, SAVE_BLOCK_BSUBWAY_PLAY);
        BSubwayScoreData *score = SaveControl_GetBlockPtr(save, SAVE_BLOCK_BSUBWAY_SCORE);
        u8 mode;

        var = ScriptReadVar(vm, env);
        mode = BSubwayPlayData_GetData(play, BSUBWAY_PLAY_MODE, NULL);
        BSubwayPlayData_ResetRound(play);
        BSubwayScoreData_ResetStage(score, mode);
        BSubwayScoreData_SetStreak(score, mode, 0);
        *var = mode;
        break;
    }
    default:
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    return FALSE;
}

BOOL PearlB2_Ext_Frontier(VM *vm, FieldScriptEnv *env) {
    u32 op = VM_Read8(vm);
    PearlB2FrontierHandler handler;

    if (op < 0x20) {
        return Frontier_Core(vm, env, op);
    }
    handler = (op - 0x20) / 0x20 < FRONTIER_FACILITIES ? sFacilityOps[(op - 0x20) / 0x20] : NULL;
    if (handler != NULL) {
        return handler(vm, env, op & 0x1f);
    }
    GFL_ASSERT(FALSE);
    VM_Halt(vm);
    return TRUE;
}

#endif
