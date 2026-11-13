// Platinum's side of the Hall harness: the types and the calls its Battle Hall code makes into the rest of the game (the save,
// the party, the battle's setup, the sets, the random numbers). The rules themselves are the decomp's own text (extract.py);
// nothing here decides anything of them. sim.c implements the calls.
#ifndef HALL_HOST_PLAT_SHIM_H
#define HALL_HOST_PLAT_SHIM_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;
typedef int BOOL;
typedef float f32;
typedef s32 fx32;
#define TRUE 1
#define FALSE 0
#define NELEMS(a) (sizeof(a) / sizeof((a)[0]))
#define UNUSED(x) ((void)(x))
#define GF_ASSERT(x) ((void)0)
#define MI_CpuClear8(p, n) memset((p), 0, (n))
// nitro/fx.h
#define FX32_SHIFT 12
#define FX_FX32_TO_F32(x) ((f32)((x) / (f32)(1 << FX32_SHIFT)))
#define FX_F32_TO_FX32(x) ((fx32)(((x) > 0) ? ((x) * (1 << FX32_SHIFT) + 0.5f) : ((x) * (1 << FX32_SHIFT) - 0.5f)))
#define FX32_CONST(x) FX_F32_TO_FX32(x)
fx32 FX_Sqrt(fx32 x);

#include "plat_consts.h"

#define LEARNED_MOVES_MAX 4
#define STAT_MAX 6
#define TRAINER_NAME_LEN 7
#define MON_NAME_LEN 10
#define MAX_SPECIES SPECIES_BAD_EGG
#define NATIONAL_DEX_COUNT (MAX_SPECIES - 2)
#define MAX_IVS_SINGLE_STAT 31
#define MAX_EVS_SINGLE_STAT 255
#define MAX_EVS_ALL_STATS 510
#define MAX_POKEMON_LEVEL 100
#define MAX_FRIENDSHIP_VALUE 255
#define MOVE_FRUSTRATION 218
#define NATURE_COUNT 25
#define ABILITY_NONE 0
#define OTID_NOT_SHINY 2
#define DEOXYS_FORM_COUNT 4
#define WORMADAM_FORM_COUNT 3
#define GIRATINA_FORM_COUNT 2
#define SHAYMIN_FORM_COUNT 2
#define ROTOM_FORM_COUNT 6
#define LOAD_RESULT_OK 0
#define FRONTIER_CHALLENGE_SINGLE 0
#define FRONTIER_CHALLENGE_DOUBLE 1
#define FRONTIER_CHALLENGE_MULTI 2
#define FRONTIER_CHALLENGE_MULTI_WFC 3
#define FRONTIER_NEXT_BATTLE_NORMAL 0
#define FRONTIER_NEXT_BATTLE_SILVER 1
#define FRONTIER_NEXT_BATTLE_GOLD 2
#define HALL_BATTLES_PER_ROUND 10
#define HALL_STREAK_SILVER_BATTLE 50
#define HALL_STREAK_GOLD_BATTLE 170
#define HALL_MAX_DISTINCT_ROUNDS ((HALL_STREAK_GOLD_BATTLE / HALL_BATTLES_PER_ROUND) + 1)
#define HALL_MAX_TYPE_RANK 10
enum HeapID { HEAP_ID_FIELD1 = 4, HEAP_ID_FIELD2 = 11, HEAP_ID_FIELD3 = 32 };
enum NarcID { NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDTR = 1, NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDPM,
              NARC_INDEX_BATTLE__B_PL_STAGE__PL_BSDPM, NARC_INDEX_MSGDATA__PL_MSG };
enum BattleFrontierStatsIndex { STAT_HALL_INDEX_DUMMY = -1 };
enum { BATTLER_PLAYER_1, BATTLER_ENEMY_1, BATTLER_PLAYER_2, BATTLER_ENEMY_2, MAX_BATTLERS };
#define BATTLE_TYPE_FRONTIER_SINGLES 0x80
#define BATTLE_TYPE_FRONTIER_DOUBLES 0x81
#define BATTLE_TYPE_FRONTIER_LINK 0x4
#define BATTLE_TYPE_TRAINER_DOUBLES 0x2
#define BATTLE_TYPE_2vs2 0x8
#define BACKGROUND_BATTLE_HALL 16
#define TERRAIN_BATTLE_HALL 16
#define gGameLanguage 2
#define TEXT_BANK_SPECIES_NAME 0
#define MSG_LOADER_LOAD_ON_DEMAND 0

// The Pokémon and the party: what the Hall's code reads and writes, as plain fields
enum { MON_DATA_SPECIES = 1, MON_DATA_LEVEL, MON_DATA_HELD_ITEM, MON_DATA_FORM, MON_DATA_COMBINED_IVS, MON_DATA_MOVE1,
       MON_DATA_MOVE1_PP_UPS = MON_DATA_MOVE1 + 4, MON_DATA_MOVE1_MAX_PP = MON_DATA_MOVE1_PP_UPS + 4,
       MON_DATA_MOVE1_PP = MON_DATA_MOVE1_MAX_PP + 4, MON_DATA_OT_ID = MON_DATA_MOVE1_PP + 4, MON_DATA_HP_EV, MON_DATA_ATK_EV,
       MON_DATA_DEF_EV, MON_DATA_SPEED_EV, MON_DATA_SPATK_EV, MON_DATA_SPDEF_EV, MON_DATA_ABILITY, MON_DATA_FRIENDSHIP,
       MON_DATA_NICKNAME_STRING, MON_DATA_NICKNAME, MON_DATA_PERSONALITY, MON_DATA_LANGUAGE };
typedef struct Pokemon {
    u16 species, level, item, form;
    u16 moves[4];
    u8 ppUps[4];
    u32 ivs, otID, personality;
    u8 evs[6];
    u8 ability, friendship;
} Pokemon;
typedef struct Party {
    int count;
    Pokemon mons[6];
} Party;
typedef struct SaveData SaveData;
typedef struct BattleFrontierSave BattleFrontierSave;
typedef struct String String;
typedef struct MessageLoader MessageLoader;
typedef struct TrainerInfo TrainerInfo;
typedef struct FieldFrontierDTO {
    void *facilityData;
    const void *options;
    SaveData *saveData;
    void *journalEntry;
    void *bagCursor;
    int unk_14;
    int unk_18;
    int mapHeaderID;
    u8 *subscreenCursorOn;
} FieldFrontierDTO;
typedef struct FieldBattleDTO {
    u32 battleType;
    Party *parties[MAX_BATTLERS];
    TrainerInfo *trainerInfo[MAX_BATTLERS];
    struct {
        struct {
            u16 aiMask;
        } header;
        u16 trainerID;
    } trainer[MAX_BATTLERS];
    int background, terrain;
} FieldBattleDTO;

#include "plat_types.h"

// The Frontier's save: the Hall's challenge, its streak flags, the records (soloStats), the win records
struct BattleFrontierSave {
    BattleHallSave hallSave;
    struct {
        BattleHallStreakFlags streakFlags;
    } hall;
    u16 stats[200];
};
u32 BattleFrontier_LoadOpponentMonData(FrontierPokemon *frontierMon, u16 narcIdx, int unused, u8 ivs, u32 personality,
                                       enum HeapID heapID, enum NarcID narcID);
void FrontierPokemon_InitPokemon(const FrontierPokemon *frontierMon, Pokemon *mon, u8 setLevel);
void BattleFrontier_LoadTrainer(FrontierOpponent *opponent, u16 trainerID, enum HeapID heapID, enum NarcID narcID);

u16 LCRNG_Next(void);
void *Heap_Alloc(int heapID, u32 size);
void Heap_Free(void *p);
Party *Party_New(int heapID);
void Party_Init(Party *party);
void Party_InitWithCapacity(Party *party, int capacity);
BOOL Party_AddPokemon(Party *party, Pokemon *mon);
Pokemon *Party_GetPokemonBySlotIndex(Party *party, int slot);
void Party_HealAllMembers(Party *party);
Pokemon *Pokemon_New(int heapID);
void Pokemon_Init(Pokemon *mon);
void Pokemon_Copy(Pokemon *src, Pokemon *dest);
u32 Pokemon_GetValue(Pokemon *mon, int field, void *dest);
void Pokemon_SetValue(Pokemon *mon, int field, const void *value);
void Pokemon_InitWith(Pokemon *mon, int species, int level, int ivs, BOOL fixedIVs, u32 personality, int otIDType, u32 otID);
void Pokemon_CalcLevelAndStats(Pokemon *mon);
void Pokemon_CalcAbility(Pokemon *mon);
u8 Pokemon_IsPersonalityShiny(u32 monOTID, u32 monPersonality);
u8 Pokemon_GetNatureOf(u32 monPersonality);
u32 FlagIndex(int num);
int SpeciesData_GetSpeciesValue(int species, int param);
enum { SPECIES_DATA_ABILITY_1, SPECIES_DATA_ABILITY_2 };
void *SaveData_SaveTable(SaveData *saveData, int entry);
#define SAVE_TABLE_ENTRY_FRONTIER 0
BattleFrontierSave *SaveData_GetBattleFrontier(SaveData *saveData);
Party *SaveData_GetParty(SaveData *saveData);
void *SaveData_GetVarsFlags(SaveData *saveData);
BOOL SystemVars_GetWiFiFrontierCleared(void *varsFlags);
u16 BattleFrontierSave_GetStatAutoHostIdx(BattleFrontierSave *frontier, int statIndex);
void BattleFrontierSave_SetStatAutoHostIdx(BattleFrontierSave *frontier, int statIndex, u16 value);
void BattleFrontierSave_SetIfBetterAutoHostIdx(BattleFrontierSave *frontier, int statIndex, u16 value);
u16 BattleFrontierSave_GetStat(BattleFrontierSave *frontier, int statIndex, int hostFriendID);
int NintendoWFC_GetHostFriendIdx(void);
void BattleFrontier_FlagGeonetLinkInfo(SaveData *saveData);
BattleHallWinRecords *SaveData_BattleHallWinRecords(SaveData *saveData, int heapID, int *resultCode);
int SaveData_SaveBattleHallWinRecords(SaveData *saveData, BattleHallWinRecords *records);
int SaveData_Save(SaveData *saveData);
BOOL SaveData_MiscSaveBlock_InitFlag(SaveData *saveData);
void BattleFrontier_GetPokemonBase(FrontierPokemonBase *monData, int narcIdx, enum NarcID narcID);
FrontierTrainerBase *BattleFrontier_GetTrainer(FrontierTrainer *trainer, int trainerID, enum HeapID heapID, enum NarcID narcID);
u16 BattleFrontier_GetObjectIDFromTrainerClass(u8 trainerClass);
FieldBattleDTO *FieldBattleDTO_New(int heapID, u32 battleType);
void FieldBattleDTO_InitFromGameState(FieldBattleDTO *dto, void *a, SaveData *saveData, int mapHeaderID, void *journal,
                                      void *bag, u8 *cursor);
void FieldBattleDTO_AddPokemonToBattler(FieldBattleDTO *dto, Pokemon *mon, int battler);
void FieldBattleDTO_CopyPlayerInfoToTrainerData(FieldBattleDTO *dto);
void FieldBattleDTO_InitFrontierTrainer(FieldBattleDTO *dto, FrontierTrainer *trainer, int partySize, int battler, int heapID);
TrainerInfo *CommInfo_TrainerInfo(int netID);
int CommSys_CurNetId(void);
void TrainerInfo_Copy(TrainerInfo *src, TrainerInfo *dest);
MessageLoader *MessageLoader_Init(int mode, int narc, int bank, int heapID);
String *MessageLoader_GetNewString(MessageLoader *loader, int id);
void MessageLoader_Free(MessageLoader *loader);
void MessageLoader_GetSpeciesName(int species, int heapID, u16 *dest);
void String_Free(String *s);
void String_ToChars(const String *s, u16 *dest, u32 n);
void *NARC_AllocAndReadWholeMemberByIndexPair(int narcID, int index, int heapID);
#define TEXT_BANK_FRONTIER_TRAINER_NAMES 21
#endif
