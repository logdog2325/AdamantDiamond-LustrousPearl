#ifndef POKEBW2_PEARLB2_PLAT_FRONTIER_H
#define POKEBW2_PEARLB2_PLAT_FRONTIER_H

// Platinum's Battle Frontier, its core (PearlB2's notes/PLATINUM_FRONTIER.md): the scenes' return to the field, the shared
// records (Platinum's BattleFrontierStats, by its own ids), the facilities' streak flags, their save. src/pearlb2/resident/
// plat_frontier.c. Script side: b2tools/frontier_translate.py and pearl_story.py's block "plat-frontier", macros in
// src/include/pearl_story.inc block "plat-frontier".
//
// In a script: PearlB2's extension command, sub-command 0x93 (the Battle Tower's row: EXT_TOWER_FRONTIER), then one byte, the
// Frontier's op, then the op's arguments (each a value or a var, read as the other sub-commands' are):
//   0x00-0x1f  the core (below)
//   0x20-0x3f  the Battle Factory (plat-factory)      0x40-0x5f  the Battle Hall (plat-hall)
//   0x60-0x7f  the Battle Castle (plat-castle)        0x80-0x9f  the Battle Arcade (plat-arcade)
// An op no piece handles stops the script (its arguments' length is unknown), as an unknown sub-command does.

#include "types.h"
#include "struct_decls.h"

enum {
    FRONTIER_OP_SET_RETURN,     // site (value or var): the field script's place ExitFrontier goes back to
    FRONTIER_OP_GET_RETURN,     // var
    FRONTIER_OP_STAT_GET,       // stat (Platinum's id), var
    FRONTIER_OP_STAT_SET,       // stat, value
    FRONTIER_OP_STAT_ADD,       // stat, value: up to 9999, as Platinum's records
    FRONTIER_OP_STAT_BEST,      // record stat, latest stat: the record becomes the latest if the latest is higher
    FRONTIER_OP_STREAK_FLAG,    // facility (0 Factory, 1 Hall, 2 Castle, 3 Arcade), op (0 get, 1 set, 2 clear), bit, var
    FRONTIER_OP_SCENE_VAR,      // op (0 keep, 1 give back), index 0-7, var: the scene manager's vars 0x8008-0x800f over a
                                // scene change (Platinum keeps them in its scene manager: RAM here too)
    FRONTIER_OP_TOWER_DISQUALIFY,   // var (plat-fix2): Platinum's BT_FUNC_UNK_14 (sub_0204A064), a Tower challenge saved but
                                // not continued: its round and room start again, its streak flag goes, its latest streak is 0;
                                // var = the play mode
    FRONTIER_OP_CORE_COUNT,
};

enum {
    FRONTIER_FACILITY_FACTORY,
    FRONTIER_FACILITY_HALL,
    FRONTIER_FACILITY_CASTLE,
    FRONTIER_FACILITY_ARCADE,
    FRONTIER_FACILITIES,
};

// Platinum's include/constants/battle_frontier_stats.h: STATS_NUM_SOLO_STATS_AND_ACTIVE_FLAGS, and its Tower's ids (0-9:
// record and latest streak of single, double, multi, link multi and Wi-Fi), which Black 2's Battle Subway keeps here
#define PLAT_FRONTIER_STATS 112
#define PLAT_FRONTIER_TOWER_STATS 10
#define PLAT_FRONTIER_STAT_MAX 9999

#define PLAT_FRONTIER_MAGIC 0x544e5246  // 'FRNT'

// The save: the Wi-Fi Battle Subway's downloaded players of save block 0x3a (BSubwayWifiData.players, 7 x 0xf0 B), which
// only the Wi-Fi train (play mode 4, closed here: the Tower's Wi-Fi desk) and the Wi-Fi download app read (PearlB2's
// notes/DATA.md, the save-block registry). Old saves and new games: no magic, set up on first use.
typedef struct {
    u32 magic;
    u16 stats[PLAT_FRONTIER_STATS];             // Platinum's soloStats: the records of every facility, by Platinum's ids
    u8 streakFlags[FRONTIER_FACILITIES];        // Platinum's BattleFactoryStreakFlags, BattleHallStreakFlags,
                                                // BattleCastlePersistentSave, BattleArcadeStreakFlags: streakActiveFlags
    u8 castleHeardIntro;                        // BattleCastlePersistentSave.haveHeardIntro
    u8 padding[3];
    u8 challenge[0x690 - 4 - 2 * PLAT_FRONTIER_STATS - FRONTIER_FACILITIES - 4];   // the challenge saved part-way: Platinum's
                                                // union (BattleFactorySave, BattleHallSave, ...), each piece's layout
} PearlB2FrontierSave;

typedef BOOL (*PearlB2FrontierHandler)(VM *vm, FieldScriptEnv *env, u32 op);

PearlB2FrontierSave *PearlB2_Frontier_GetSave(SaveControl *save);
BOOL PearlB2_Ext_Frontier(VM *vm, FieldScriptEnv *env);
u16 PearlB2_Frontier_GetStat(SaveControl *save, u32 stat);
void PearlB2_Frontier_SetStat(SaveControl *save, u32 stat, u16 value);

#endif // POKEBW2_PEARLB2_PLAT_FRONTIER_H
