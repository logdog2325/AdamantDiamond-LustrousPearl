// Our side of the harness: the fields of Black 2's BSubwayScrWork the rules read (pokebw2 include/field/bsubway_scr.h) and the
// calls they make. randFFFFFFFFdivFFFF gives the same numbers as Platinum's challenge generator from the same seed (sim.c),
// so the two sides draw from one stream: what differs is the rules.
#ifndef FRONTIER_HOST_B2_SHIM_H
#define FRONTIER_HOST_B2_SHIM_H
#include "common.h"
#define PEARLB2 1
#define NULL_ ((void *)0)
enum { BSUBWAY_PLAY_UNK0_10 = 10 };
typedef struct SaveControl SaveControl;
typedef int HeapID;
typedef struct MATHRandContext32 MATHRandContext32;
typedef struct { u8 opaque[0x38]; } BSubwayPokemon;
typedef struct {
    u16 species;
    u16 moves[4];
    u8 evFlags;
    u8 nature;
    u16 item;
    u16 form;
} BSubwayPokemonData;
typedef struct {
    u32 id;
    u16 files[2];
    u32 pids[2];
    u8 natures[2];
} BSubwayTeamConfig;
// Black 2's calls of the picks (sim.c): the set, its random numbers (BtlInst_Random16: GFL_RandomLC / 0xffff), the Pokemon made
void BtlInst_ReadPokemonData(u32 arcId, BSubwayPokemonData *data, u32 file);
u16 BtlInst_Random16(MATHRandContext32 *rand);
u32 BtlInst_MakeRomPokemon(BSubwayPokemon *pkm, u32 arcId, u32 file, u32 seed, u32 pid, u8 iv, int index, BOOL failed,
                           HeapID heapId);
BOOL BtlInst_MakeRomTeam(const u16 *trainerData, u16 trainerId, BSubwayPokemon *pkms, u8 count, u32 arcId,
                         const u16 *species, const u16 *items, BSubwayTeamConfig *config, MATHRandContext32 *rand,
                         u8 iv, HeapID heapId);
u8 BsubwayScr_GetMonIv(u32 value);
typedef struct BSubwayScrWork {
    u8 playMode;
    u16 unkC_1 : 2;
    u16 unkE;
    u16 unk18;
    u16 unk32[0x1d];
    void *unk70;
    void *unk74;
    void *gameData;
} BSubwayScrWork;
u16 randFFFFFFFFdivFFFF(BSubwayScrWork *bsw);
u32 BSubwayPlayData_GetData(void *play, int id, void *out);
s32 BSubwayScoreData_GetWifiRank(void *score);
u16 BSubwayScoreData_GetStage(void *score, u32 mode);
void BSubwayScoreData_AddBattlePoints(void *score, u16 points);
SaveControl *GameData_GetSaveControl(void *gameData);
void *getTrainerCardInfoBlkAddress(SaveControl *save);
void RecordAdd(void *records, int id, u32 value);
u16 BsubwayScr_DrawTrainerNo(BSubwayScrWork *bsw, u16 level, u8 index, u32 mode, u8 side);
u16 PearlB2_TowerDrawTrainerNo(BSubwayScrWork *bsw, u16 level, u8 index, u32 mode, u8 side);
u16 BsubwayScr_GetWinCount(BSubwayScrWork *bsw);
BOOL BsubwayScr_IsTrainerNoUsed(const u16 *list, u16 value, u16 count);
u16 BsubwayScr_GetStageNo(s32 value);
void BsubwayScr_DrawTrainerNos(BSubwayScrWork *bsw);
u16 func_ov033_0217b8ec(BSubwayScrWork *bsw);
#endif
