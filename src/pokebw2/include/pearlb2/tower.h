#ifndef POKEBW2_PEARLB2_TOWER_H
#define POKEBW2_PEARLB2_TOWER_H

// Pearl's Battle Tower on Black 2's Battle Subway (PearlB2's notes/BATTLE_ZONE.md): the code the subway has no room
// for. src/pearlb2/resident/tower.c. Script side: b2tools/battle_tower.py, macros in src/include/pearl_story.inc.

#include "types.h"
#include "struct_decls.h"
#include "field/bsubway_scr.h"

// Sub-commands of PearlB2's extension command, row 0x80-0x9f (their low five bits)
enum {
    EXT_TOWER_BP_GET,           // var
    EXT_TOWER_BP_ADD,           // value or var
    EXT_TOWER_BP_SUB,           // value or var
    EXT_TOWER_BP_CHECK,         // value or var, var: 1 if the player has that many
    EXT_TOWER_BP_WINDOW,        // x, y (value or var): Black 2's money window, showing the BP
    EXT_TOWER_BP_UPDATE,        // the window shows the BP again
    EXT_TOWER_CHECK_PARTY,      // mode (value or var; 255: the challenge's), var: 1 if the party can enter
    EXT_TOWER_IS_NULL,          // var: 1 if no challenge's work exists
    EXT_TOWER_MAKE_PARTNERS,    // Pearl's five partners draw their teams
    EXT_TOWER_PARTNER_MON,      // partner, mon (value or var), species var, move var
    EXT_TOWER_SET_PARTNER,      // partner (value or var)
    EXT_TOWER_GET_PARTNER,      // var
    EXT_TOWER_PARTNER_CODE,     // var: the chosen partner's object code
    EXT_TOWER_RESUME_PARTNER,   // after a resumed multi challenge's work: the partner's team again
    EXT_TOWER_EXCHANGE,         // list, prize (value or var), item var, cost var: Pearl's Exchange Service Corner
    EXT_TOWER_PLAYER_CODE,      // var: the player's object code (works in a zone init)
    EXT_TOWER_ACTOR_VISIBLE,    // actor, 0 or 1 (value or var): drawn or not (works in a field-load script)
    EXT_TOWER_BEST_STREAK,      // var: the longest win streak of any room (1.0.1: Pearl's trophies)
    EXT_TOWER_TROPHY,           // op (0 get, 1 set), trophy 0-2, var (values or vars): a trophy given (1.0.1)
    EXT_TOWER_FRONTIER,         // (plat-frontier-core) an op byte, then its arguments: Platinum's Battle Frontier
                                // (include/pearlb2/plat_frontier.h, src/pearlb2/resident/plat_frontier.c)
};

#define PEARLB2_TOWER_PARTNERS 5

// One {Black 2 trainer class, object code} row: the opponent's field sprite (patches/battle_tower.py)
typedef struct {
    u16 trainerClass;
    u16 objCode;
} PearlB2TowerSprite;

u16 PearlB2_TowerDrawTrainerNo(BSubwayScrWork *bsw, u16 level, u8 index, u32 mode, u8 side);
u16 PearlB2_TowerObjCode(u32 trainerClass);
BOOL PearlB2_Ext_Tower(VM *vm, FieldScriptEnv *env, u32 sub);
u16 PearlB2_WbtOpenCount(void *save, int index);

#endif // POKEBW2_PEARLB2_TOWER_H
