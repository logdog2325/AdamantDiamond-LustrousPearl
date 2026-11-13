// Platinum's side of the Factory harness: the types and the calls its Battle Factory makes outside the rules (the heap,
// the party, the script context, the message loaders). The rules themselves are the decomp's own text (extract.py).
#ifndef FACTORY_HOST_PLAT_SHIM_H
#define FACTORY_HOST_PLAT_SHIM_H
#include <string.h>
#include "../platinum_frontier_host/common.h"

#define LEARNED_MOVES_MAX 4
#define STAT_MAX 6
#define MON_NAME_LEN 10
#define TRAINER_NAME_LEN 7
#define MAX_PARTY_SIZE 6
#define NATURE_COUNT 25
#define MAX_EVS_ALL_STATS 510
#define MAX_EVS_SINGLE_STAT 255
#define MAX_FRIENDSHIP_VALUE 255
#define MOVE_FRUSTRATION 218
#define NUM_POKEMON_TYPES 18
#define ITEM_BRIGHTPOWDER 213
#define ITEM_LUM_BERRY 157
#define ITEM_LEFTOVERS 234
#define ITEM_QUICK_CLAW 217
#define FlagIndex(i) (1 << (i))
#define NELEMS(a) (sizeof(a) / sizeof((a)[0]))
#define UNUSED(x) ((void)(x))
#define GF_ASSERT(x) ((void)0)
#define MATH_MAX(a, b) ((a) > (b) ? (a) : (b))
#define MI_CpuClear8(p, n) memset((p), 0, (n))
#define FACTORY_BATTLES_PER_ROUND_ 7

enum HeapID { HEAP_ID_SYSTEM, HEAP_ID_FIELD1 = 4, HEAP_ID_FIELD2 = 11 };
enum NarcID { NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDPM = 1, NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDTR = 2 };
enum { SPECIES_DATA_ABILITY_1, SPECIES_DATA_ABILITY_2 };
enum { MON_DATA_SPECIES, MON_DATA_HELD_ITEM, MON_DATA_ATK_IV, MON_DATA_PERSONALITY, MON_DATA_TYPE_1, MON_DATA_TYPE_2 };
enum { BG_LAYER_MAIN_2 = 2, BG_LAYER_MAIN_3 = 3, BG_OFFSET_UPDATE_SET_Y = 3, BG_OFFSET_UPDATE_ADD_Y = 4 };
enum { RECORD_BATTLE_FACTORY_TRADES = 1 };
#define STAT_FACTORY_50_WFC_STREAK_ACTIVE_ 0

extern u8 gGameLanguage;

typedef struct SaveData SaveData;
typedef struct FieldBattleDTO FieldBattleDTO;
typedef struct SysTask SysTask;
typedef struct StringTemplate StringTemplate;
typedef struct VarsFlags VarsFlags;
typedef struct GameRecords GameRecords;
typedef struct BoxPokemon BoxPokemon;

// A party Pokémon: what the Factory reads of one (Pokemon_GetValue below)
typedef struct Pokemon {
    u16 species;
    u16 form;
    u16 item;
    u8 atkIV;
    u8 type1, type2;
    u32 personality;
    u32 otID;
} Pokemon;

typedef struct Party {
    int count;
    Pokemon mons[MAX_PARTY_SIZE];
} Party;

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

// The script contexts (only the parts CallBattleFactoryFunction and DeleteActiveBattleFactoryStreak use)
typedef struct FrontierScriptManager {
    void *frontier;
    StringTemplate *strTemplate;
} FrontierScriptManager;
typedef struct FrontierScriptContext {
    FrontierScriptManager *scriptMan;
} FrontierScriptContext;
typedef struct FrontierGraphics {
    void *bgConfig;
} FrontierGraphics;
typedef struct FieldSystem {
    SaveData *saveData;
} FieldSystem;
typedef struct ScriptContext {
    FieldSystem *fieldSystem;
} ScriptContext;

u16 LCRNG_Next(void);
void *Heap_Alloc(enum HeapID heapID, u32 size);
void Heap_Free(void *ptr);
Party *Party_New(enum HeapID heapID);
void Party_Init(Party *party);
int Party_GetCurrentCount(const Party *party);
Pokemon *Party_GetPokemonBySlotIndex(const Party *party, int slot);
void Party_AddPokemonBySlotIndex(Party *party, int slot, Pokemon *mon);
Pokemon *Pokemon_New(enum HeapID heapID);
u32 Pokemon_GetValue(Pokemon *mon, int field, void *dest);
BoxPokemon *Pokemon_GetBoxPokemon(Pokemon *mon);
u32 SpeciesData_GetSpeciesValue(int species, int field);
void MessageLoader_GetSpeciesName(u32 species, u32 heapID, u16 *dest);
SaveData *SaveData_GetBattleFrontier_(SaveData *saveData);
VarsFlags *SaveData_GetVarsFlags(SaveData *saveData);
GameRecords *SaveData_GetGameRecords(SaveData *saveData);
void GameRecords_IncrementRecordValue(GameRecords *records, int id);
u8 SystemVars_GetWiFiFrontierCleared(VarsFlags *vars);
void BattleFrontier_FlagGeonetLinkInfo(SaveData *saveData);
int NintendoWFC_GetHostFriendIdx(void);
void OS_ResetSystem(int x);
void Bg_ChangeTilemapRectPalette(void *bg, int layer, int x, int y, int w, int h, int pal);
void Bg_ScheduleTilemapTransfer(void *bg, int layer);
SysTask *SysTask_Start(void (*fn)(SysTask *, void *), void *data, int priority);
void SysTask_Done(SysTask *task);
FrontierGraphics *FrontierScriptManager_GetGraphics(FrontierScriptManager *man);
void *BattleFrontier_GetFacilityStruct(void *frontier);
u8 FrontierScriptContext_ReadByte(FrontierScriptContext *ctx);
u16 *FrontierScriptContext_TryGetVarPointer(FrontierScriptContext *ctx);
u16 ScriptContext_GetVar(ScriptContext *ctx);
void StringTemplate_SetSpeciesName(StringTemplate *t, int idx, BoxPokemon *mon);
void sub_0209BA80(void *factory);
void BattleFrontier_GetPokemonBase(FrontierPokemonBase *monData, int narcIdx, enum NarcID narcID);
#endif
