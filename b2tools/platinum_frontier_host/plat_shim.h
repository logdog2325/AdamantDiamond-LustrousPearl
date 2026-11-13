// Platinum's side of the harness: the types and the few calls its Battle Tower rules make (pokeplatinum src/unk_02049D08.c,
// src/unk_0204AEE8.c). The rules themselves are the decomp's own text (extract.py).
#ifndef FRONTIER_HOST_PLAT_SHIM_H
#define FRONTIER_HOST_PLAT_SHIM_H
#include "common.h"
#define BT_OPPONENTS_COUNT 7
#define MAX_IVS_SINGLE_STAT 31
enum { BATTLE_TOWER_MODE_SINGLE, BATTLE_TOWER_MODE_DOUBLE, BATTLE_TOWER_MODE_MULTI, BATTLE_TOWER_MODE_LINK_MULTI,
       BATTLE_TOWER_MODE_WIFI, BATTLE_TOWER_MODE_5, BATTLE_TOWER_MODE_6 };
enum { BATTLE_POINTS_FUNC_ADD = 1 };
typedef struct SaveData SaveData;
typedef struct BattleTower {
    u32 unk_08;                 // the challenge's random state
    int challengeMode;
    u16 roomNum;
    u16 unk_14;
    u16 trainerIDs[BT_OPPONENTS_COUNT * 2];
    BOOL beatPalmer;
    void *unk_74;
} BattleTower;
u16 LCRNG_Next(void);
u16 WifiBattleTowerRecord_UpdateRoomNum(void *record, int mode, int op);
u16 WifiBattleTowerRecord_UpdateRank(void *record, int op);
void WifiBattleTowerRecord_UpdateBattlePoints(void *record, u16 points, int op);
enum HeapID { HEAP_ID_FIELD2 = 11 };
#define GF_ASSERT(x) ((void)0)
#define LEARNED_MOVES_MAX 4
typedef struct FrontierTrainerBase {
    u16 trainerType;
    u16 numSets;
    u16 setIDs[];
} FrontierTrainerBase;
typedef struct FrontierPokemonBase {
    u16 species;
    u16 moves[LEARNED_MOVES_MAX];
    u8 evFlags;
    u8 nature;
    u16 item;
    u16 form;
} FrontierPokemonBase;
typedef struct FrontierPokemon { u8 opaque[0x38]; } FrontierPokemon;
typedef struct BattleTowerPartnerData {
    u32 otID;
    u16 monSetIDs[2];
    u32 personalities[2];
} BattleTowerPartnerData;
// The two calls of the picks that read the sets and make the Pokemon (sim.c): the set from the dump's pl_btdpm, and the
// Pokemon left to the caller (its personality loop comes after the picks)
void sub_0204B640(FrontierPokemonBase *param0, int param1);
u32 sub_0204B1E8(BattleTower *battleTower, FrontierPokemon *param1, u16 param2, u32 param3, u32 param4, u8 ivs, u8 param6,
                 BOOL param7, enum HeapID heapID);
u32 sub_0206BFF0(u32 param0);
u16 BattleTower_GetRandom(BattleTower *battleTower);
u16 BattleTower_GetTrainerIDForRoomAndOpponentNum(BattleTower *battleTower, u8 roomNum, u8 opponentNum, int challengeMode);
void sub_0204A4C8(BattleTower *battleTower, SaveData *saveData);
u16 BattleTower_GiveBattlePointsReward(BattleTower *battleTower);
u8 BattleTower_GetIVsFromTrainerID(u16 battleTowerID);
#endif
