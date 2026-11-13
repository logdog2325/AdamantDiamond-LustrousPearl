// Platinum's side of the Arcade harness: the types and the calls its Battle Arcade code makes into the rest of the game (the save,
// the party, the battle's setup, the sets, the scene's context, the board's drawing, sound and touch). The rules themselves are the
// decomp's own text (extract.py); nothing here decides anything of them. sim.c implements the calls; the Pokémon here is a model
// (the fields the Arcade reads and writes, its stats and level from Platinum's own personal data and experience tables), the same
// one ours is given (sim.c).
#ifndef ARCADE_HOST_PLAT_SHIM_H
#define ARCADE_HOST_PLAT_SHIM_H
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
typedef s32 fx32;
typedef s16 fx16;
#define TRUE 1
#define FALSE 0
#define NELEMS(a) (sizeof(a) / sizeof((a)[0]))
#define SNELEMS(a) ((int)NELEMS(a))
#define UNUSED(x) ((void)(x))
#define GF_ASSERT(x) ((void)0)
#define MI_CpuClear8(p, n) memset((p), 0, (n))
#define MI_CpuClearFast(p, n) memset((p), 0, (n))
#define MI_CpuCopy8(s, d, n) memmove((d), (s), (n))
#define MATH_MAX(a, b) ((a) > (b) ? (a) : (b))
#define FX32_ONE 4096
#define FX32_CONST(x) ((fx32)((x) * 4096))

#include "plat_consts.h"

#define LEARNED_MOVES_MAX 4
#define STAT_MAX 6
#define TRAINER_NAME_LEN 7
#define MON_NAME_LEN 10
#define MAX_PARTY_SIZE 6
#define MAX_POKEMON_LEVEL 100
#define MAX_IVS_SINGLE_STAT 31
#define MAX_EVS_SINGLE_STAT 255
#define MAX_EVS_ALL_STATS 510
#define MAX_FRIENDSHIP_VALUE 255
#define LOW_FRIENDSHIP_LIMIT 100
#define MED_FRIENDSHIP_LIMIT 200
#define HIGH_FRIENDSHIP_LIMIT MAX_FRIENDSHIP_VALUE
#define MAX_PP_UP_BONUSES 3
#define MOVE_NONE 0
#define MOVE_FRUSTRATION 218
#define NATURE_COUNT 25
#define INIT_IVS_RANDOM 32
#define OTID_SET 0
#define OTID_NOT_SET 1
#define OTID_NOT_SHINY 2
#define SHINY_ODDS 8
#define MAX_FRIENDS 32
#define MON_CONDITION_NONE 0
#define MON_CONDITION_SLEEP 7
#define MON_CONDITION_POISON (1 << 3)
#define MON_CONDITION_BURN (1 << 4)
#define MON_CONDITION_FREEZE (1 << 5)
#define MON_CONDITION_PARALYSIS (1 << 6)
#define MON_CONDITION_TOXIC (1 << 7)
#define MON_CONDITION_ANY_POISON (MON_CONDITION_POISON | MON_CONDITION_TOXIC | (15 << 8))
#define TYPE_POISON 3
#define TYPE_GROUND 4
#define TYPE_STEEL 8
#define TYPE_FIRE 10
#define TYPE_ICE 15
#define ABILITY_LIMBER 7
#define ABILITY_INSOMNIA 15
#define ABILITY_IMMUNITY 17
#define ABILITY_MAGMA_ARMOR 40
#define ABILITY_WATER_VEIL 41
#define ABILITY_VITAL_SPIRIT 72
#define FRONTIER_CHALLENGE_SINGLE 0
#define FRONTIER_CHALLENGE_DOUBLE 1
#define FRONTIER_CHALLENGE_MULTI 2
#define FRONTIER_CHALLENGE_MULTI_WFC 3
#define FRONTIER_NEXT_BATTLE_NORMAL 0
#define FRONTIER_NEXT_BATTLE_SILVER 1
#define FRONTIER_NEXT_BATTLE_GOLD 2
#define BATTLE_TYPE_FRONTIER_SINGLES 0x80
#define BATTLE_TYPE_FRONTIER_DOUBLES 0x81
#define BATTLE_TYPE_FRONTIER_LINK 0x4
#define BATTLE_TYPE_TRAINER_DOUBLES 0x2
#define BATTLE_TYPE_2vs2 0x8
#define BACKGROUND_BATTLE_ARCADE 18
#define TERRAIN_BATTLE_ARCADE 18
#define gGameLanguage 2
#define TEXT_BANK_FRONTIER_TRAINER_NAMES 21
#define TEXT_BANK_SPECIES_NAME 412
#define MSG_LOADER_LOAD_ON_DEMAND 0
#define ITEM_POKE_BALL 4
#define GX_PLANEMASK_BG2 4
#define BG_LAYER_MAIN_2 2
#define BG_LAYER_MAIN_3 3
#define PLTTBUF_MAIN_OBJ 1
#define SE_CONFIRM_sseq_3 1500
#define SEQ_SE_DP_WIN_OPEN2_sseq 1501
#define SEQ_SE_DP_UG_020_sseq 1502
#define SEQ_SE_DP_BUTTON3_sseq 1503
#define SEQ_SE_DP_PIRORIRO2_sseq 1504
#define SEQ_SE_DP_BUTTON9_sseq 1505
#define FADE_BOTH_SCREENS 0
#define FADE_TYPE_BRIGHTNESS_IN 1
#define FADE_TYPE_BRIGHTNESS_OUT 0
#define COLOR_BLACK 0
#define OVERLAY_LOAD_ASYNC 0
#define TOUCHSCREEN_USE_CIRCLE 0xfe
#define TOUCHSCREEN_TABLE_TERMINATOR 0xff
#define TOUCH_BUTTON_PRESSED 0
#define FS_OVERLAY_ID(x) 0
enum BgLayer { BG_LAYER_DUMMY };
enum HeapID { HEAP_ID_SYSTEM = 0, HEAP_ID_FIELD1 = 4, HEAP_ID_FIELD2 = 11, HEAP_ID_APPLICATION = 3, HEAP_ID_94 = 94,
              HEAP_ID_BATTLE_ARCADE_APP = 100 };
#define HEAP_SIZE_BATTLE_ARCADE_APP 0x20000
enum NarcID { NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDTR = 1, NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDPM,
              NARC_INDEX_MSGDATA__PL_MSG };
enum BattleFrontierStatsIndex { STAT_ARCADE_INDEX_DUMMY = -1 };
enum { BATTLER_PLAYER_1, BATTLER_ENEMY_1, BATTLER_PLAYER_2, BATTLER_ENEMY_2, MAX_BATTLERS };

// The Pokémon (the model) and the party
enum { MON_DATA_SPECIES = 1, MON_DATA_SPECIES_EXISTS, MON_DATA_IS_EGG, MON_DATA_LEVEL, MON_DATA_EXPERIENCE, MON_DATA_HP,
       MON_DATA_MAX_HP, MON_DATA_STATUS, MON_DATA_HELD_ITEM, MON_DATA_FORM, MON_DATA_COMBINED_IVS, MON_DATA_MOVE1,
       MON_DATA_MOVE2, MON_DATA_MOVE3, MON_DATA_MOVE4, MON_DATA_MOVE1_PP, MON_DATA_MOVE2_PP, MON_DATA_MOVE3_PP,
       MON_DATA_MOVE4_PP, MON_DATA_MOVE1_PP_UPS, MON_DATA_MOVE2_PP_UPS, MON_DATA_MOVE3_PP_UPS, MON_DATA_MOVE4_PP_UPS,
       MON_DATA_MOVE1_MAX_PP, MON_DATA_MOVE2_MAX_PP, MON_DATA_MOVE3_MAX_PP, MON_DATA_MOVE4_MAX_PP, MON_DATA_OT_ID,
       MON_DATA_HP_EV, MON_DATA_ATK_EV, MON_DATA_DEF_EV, MON_DATA_SPEED_EV, MON_DATA_SPATK_EV, MON_DATA_SPDEF_EV,
       MON_DATA_ABILITY, MON_DATA_FRIENDSHIP, MON_DATA_NICKNAME_STRING, MON_DATA_NICKNAME, MON_DATA_PERSONALITY,
       MON_DATA_LANGUAGE, MON_DATA_ATK, MON_DATA_DEF, MON_DATA_SP_ATK, MON_DATA_SP_DEF, MON_DATA_SPEED, MON_DATA_GENDER,
       MON_DATA_TYPE_1, MON_DATA_TYPE_2 };
typedef struct Pokemon {
    u16 species, item, form, hp, maxHp;
    u16 atk, def, speed, spAtk, spDef;
    u8 level, isEgg, ability, friendship, language;
    u16 moves[4];
    u8 pp[4], ppUps[4];
    u32 exp, status, ivs, otID, personality;
    u8 evs[6];
} Pokemon;
typedef Pokemon BoxPokemon;
typedef struct Party {
    int count;
    Pokemon mons[6];
} Party;
typedef struct SaveData SaveData;
typedef struct String String;
typedef struct MessageLoader MessageLoader;
typedef struct TrainerInfo TrainerInfo;
typedef struct StringTemplate StringTemplate;
typedef struct BgConfig BgConfig;
typedef struct ApplicationManager ApplicationManager;
typedef struct PaletteData PaletteData;
typedef struct Options Options;
typedef struct NARC NARC;
typedef struct ItemData ItemData;
typedef struct Sprite Sprite;
typedef struct SPLEmitter SPLEmitter;
typedef struct ParticleSystem ParticleSystem;
typedef struct BattleArcadeAppSprite BattleArcadeAppSprite;
typedef struct { int dummy; } Window;
typedef struct { void *spriteList; } BattleArcadeAppSpriteManager;
typedef struct { Sprite *sprite; } ManagedSprite;
typedef struct { void *particleSys; void *plttData; BgConfig *bgConfig; } FrontierGraphics;
typedef struct { fx32 x, y, z; } VecFx32;
typedef struct { fx16 x, y, z; } VecFx16;
typedef struct { struct { u8 code, x, y, r; } circle; } TouchScreenHitTable;
#define NUM_MON_SPRITES MATH_MAX(ARCADE_PARTY_SIZE_SOLO, ARCADE_PARTY_SIZE_MULTI * 2)
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
    u32 resultMask;
    Party *parties[MAX_BATTLERS];
    TrainerInfo *trainerInfo[MAX_BATTLERS];
    struct {
        struct {
            u16 aiMask;
            u16 trainerType;
        } header;
    } trainer[MAX_BATTLERS];
    u32 trainerIDs[MAX_BATTLERS];
    int background, terrain, fieldWeather;
    int totalTurnsElapsed;
} FieldBattleDTO;
typedef struct { void *init, *main, *exit; u32 overlay; } ApplicationManagerTemplate;
#define FS_EXTERN_OVERLAY(x)
extern const ApplicationManagerTemplate gBattleApplicationTemplate;
typedef struct { u32 pressedKeys; } HarnessSystem;
extern HarnessSystem gSystem;

typedef struct BattleFrontierSave BattleFrontierSave;
typedef struct FrontierScriptManager FrontierScriptManager;
#include "plat_types.h"

// The Frontier's save: the Arcade's challenge, its streak flags, the records
typedef struct {
    u16 soloStats[112];
    u16 wfcStats[MAX_FRIENDS][32];
} BattleFrontierStats;
struct BattleFrontierSave {
    BattleFrontierStats stats;
    BattleArcadeSave arcadeSave;
    struct {
        BattleArcadeStreakFlags streakFlags;
    } arcade;
};
#define STATS_NUM_SOLO_STATS_AND_ACTIVE_FLAGS 112

// The scene's context (FrontierScriptContext): its arguments from a stream the harness fills
struct FrontierScriptManager {
    void *frontier;
    StringTemplate *strTemplate;
};
typedef struct FrontierScriptContext {
    FrontierScriptManager *scriptMan;
    u16 *args;
    int at;
    u32 data[4];
} FrontierScriptContext;
u16 FrontierScriptContext_GetVar(FrontierScriptContext *ctx);
u16 *FrontierScriptContext_TryGetVarPointer(FrontierScriptContext *ctx);
u8 FrontierScriptContext_ReadByte(FrontierScriptContext *ctx);
u16 FrontierScriptContext_ReadHalfWord(FrontierScriptContext *ctx);
void *BattleFrontier_GetFacilityStruct(void *frontier);
void BattleFrontier_SetFacilityStruct(void *frontier, void *facility);
FieldFrontierDTO *BattleFrontier_GetFieldData(void *frontier);
void BattleFrontier_RunSubApp(void *frontier, const ApplicationManagerTemplate *t, void *args, int a, void (*cb)(void *));
FrontierGraphics *FrontierScriptManager_GetGraphics(FrontierScriptManager *scriptMan);
BOOL CheckPlayerWonBattle(u32 resultMask);
void FieldBattleDTO_Free(FieldBattleDTO *dto);
void sub_0209BA80(void *arcade);
BOOL BattleCastle_IsMultiPlayerChallenge(u8 challengeType);
void OS_ResetSystem(int a);

// frontier_opponents.c's (copied) and the game's calls
void BattleFrontier_GetPokemonBase(FrontierPokemonBase *monData, int narcIdx, enum NarcID narcID);
FrontierTrainerBase *BattleFrontier_GetTrainer(FrontierTrainer *trainer, int trainerID, enum HeapID heapID, enum NarcID narcID);
void FrontierPokemon_InitPokemon(const FrontierPokemon *frontierMon, Pokemon *mon, u8 setLevel);
u16 BattleFrontier_GetObjectIDFromTrainerClass(u8 trainerClass);
void BattleFrontier_LoadTrainer(FrontierOpponent *opponent, u16 trainerID, enum HeapID heapID, enum NarcID narcID);
void FieldBattleDTO_InitFrontierTrainer(FieldBattleDTO *battleDTO, FrontierTrainer *trainer, int unused, int battlerId,
                                        enum HeapID heapID);
u32 BattleFrontier_LoadOpponentMonData(FrontierPokemon *frontierMon, u16 narcIdx, int unused, u8 ivs, u32 personality,
                                       enum HeapID heapID, enum NarcID narcID);
void BattleFrontier_LoadFrontierPokemon(FrontierPokemon *mons, u16 narcIdx[], u8 ivList[], u32 personalities[],
                                        u32 resultPersonalities[], int numMons, enum HeapID heapID, enum NarcID narcID);
void BattleFrontier_GetPokemonForTrainers(u8 numMons, u16 trainerID, u16 trainerID2, u16 *monSetIDs, FrontierPokemon *resultMons,
                                          u8 *ivs, u32 *personalities, u8 isMultiplayerChallenge);
void BattleFrontier_FlagGeonetLinkInfo(SaveData *saveData);
void *NARC_AllocAndReadWholeMemberByIndexPair(int narcID, int index, int heapID);
void NARC_ReadWholeMemberByIndexPair(void *dest, int narcID, int index);
void BattleFrontier_LoadMonSpriteData(FrontierGraphics *g);
void BattleFrontier_UnloadMonSpriteData(FrontierGraphics *g);
void BattleFrontier_LoadItemSpriteData(FrontierGraphics *g);
void BattleFrontier_UnloadItemSpriteData(FrontierGraphics *g);
void BattleFrontier_PrintNormalTrainerMessage(FrontierScriptContext *ctx, u16 *msg);

u16 LCRNG_Next(void);
int Plat_DSMod(int a, int b);           // the DS's remainder (_s32_div_f): 0 for a divisor of 0
void *Heap_Alloc(int heapID, u32 size);
void Heap_Free(void *p);
Party *Party_New(int heapID);
void Party_Init(Party *party);
void Party_InitWithCapacity(Party *party, int capacity);
BOOL Party_AddPokemon(Party *party, Pokemon *mon);
int Party_GetCurrentCount(const Party *party);
Pokemon *Party_GetPokemonBySlotIndex(const Party *party, int slot);
void Party_HealAllMembers(Party *party);
Pokemon *Pokemon_New(int heapID);
void Pokemon_Init(Pokemon *mon);
void Pokemon_Copy(Pokemon *src, Pokemon *dest);
u32 Pokemon_GetValue(Pokemon *mon, int field, void *dest);
void Pokemon_SetValue(Pokemon *mon, int field, const void *value);
void Pokemon_InitWith(Pokemon *mon, int species, int level, int ivs, BOOL useMonPersonalityParam, u32 personality,
                      int otIDSource, u32 otID);
void Pokemon_CalcLevelAndStats(Pokemon *mon);
u32 Pokemon_GetSpeciesBaseExpAt(int species, int level);
void Pokemon_UpdateAfterCatch(Pokemon *mon, TrainerInfo *trainer, int ball, int metLocation, int metTerrain, int heapID);
u8 Pokemon_IsPersonalityShiny(u32 monOTID, u32 monPersonality);
u8 Pokemon_GetNatureOf(u32 monPersonality);
u32 FlagIndex(int num);
int SpeciesData_GetSpeciesValue(int species, int param);
enum { SPECIES_DATA_ABILITY_1, SPECIES_DATA_ABILITY_2 };
u8 MoveTable_CalcMaxPP(u16 move, u8 ppUps);
void *SaveData_SaveTable(SaveData *saveData, int entry);
#define SAVE_TABLE_ENTRY_FRONTIER 0
BattleFrontierSave *SaveData_GetBattleFrontier(SaveData *saveData);
Party *SaveData_GetParty(SaveData *saveData);
void *SaveData_GetVarsFlags(SaveData *saveData);
TrainerInfo *SaveData_GetTrainerInfo(SaveData *saveData);
Options *SaveData_GetOptions(SaveData *saveData);
BOOL SystemVars_GetWiFiFrontierCleared(void *varsFlags);
int NintendoWFC_GetHostFriendIdx(void);
int BattleFrontierStats_GetHostFriendIdx(u32 statIndex);
u16 BattleFrontierSave_GetStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID);
u16 BattleFrontierSave_SetStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID, u16 newValue);
u16 BattleFrontierSave_SetIfBetter(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID,
                                   u16 newValue);
#define BattleFrontierSave_GetStatAutoHostIdx(f, i) BattleFrontierSave_GetStat(f, i, BattleFrontierStats_GetHostFriendIdx(i))
#define BattleFrontierSave_SetStatAutoHostIdx(f, i, v) BattleFrontierSave_SetStat(f, i, BattleFrontierStats_GetHostFriendIdx(i), v)
#define BattleFrontierSave_SetIfBetterAutoHostIdx(f, i, v) BattleFrontierSave_SetIfBetter(f, i, BattleFrontierStats_GetHostFriendIdx(i), v)
enum BattleFrontierStatsIndex BattleFrontierStats_GetArcadeLatestStreakIndex(u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetArcadeCurrentStreakIndex(u8 challengeType);
FieldBattleDTO *FieldBattleDTO_New(int heapID, u32 battleType);
void FieldBattleDTO_InitFromGameState(FieldBattleDTO *dto, void *a, SaveData *saveData, int mapHeaderID, void *journal,
                                      void *bag, u8 *cursor);
void FieldBattleDTO_AddPokemonToBattler(FieldBattleDTO *dto, Pokemon *mon, int battler);
void FieldBattleDTO_CopyPlayerInfoToTrainerData(FieldBattleDTO *dto);
TrainerInfo *CommInfo_TrainerInfo(int netID);
int CommSys_CurNetId(void);
void TrainerInfo_Copy(TrainerInfo *src, TrainerInfo *dest);
MessageLoader *MessageLoader_Init(int mode, int narc, int bank, int heapID);
String *MessageLoader_GetNewString(MessageLoader *loader, int id);
void MessageLoader_Free(MessageLoader *loader);
void MessageLoader_GetSpeciesName(int species, int heapID, u16 *dest);
void String_Free(String *s);
void String_ToChars(const String *s, u16 *dest, u32 n);
void StringTemplate_SetFrontierTrainerName(StringTemplate *t, u32 idx, u32 trainerID);
void StringTemplate_SetPlayerName(StringTemplate *t, u32 idx, TrainerInfo *info);
// item_use_pokemon.c's calls (the heal's)
enum ItemParam { ITEM_PARAM_PARTY_USE = 1, ITEM_PARAM_HEAL_SLEEP, ITEM_PARAM_HEAL_POISON, ITEM_PARAM_HEAL_BURN,
                 ITEM_PARAM_HEAL_FREEZE, ITEM_PARAM_HEAL_PARALYSIS, ITEM_PARAM_REVIVE, ITEM_PARAM_REVIVE_ALL,
                 ITEM_PARAM_LEVEL_UP, ITEM_PARAM_EVOLVE, ITEM_PARAM_PP_UP, ITEM_PARAM_PP_MAX, ITEM_PARAM_PP_RESTORE,
                 ITEM_PARAM_PP_RESTORE_ALL, ITEM_PARAM_HP_RESTORE, ITEM_PARAM_GIVE_HP_EVS, ITEM_PARAM_GIVE_ATK_EVS,
                 ITEM_PARAM_GIVE_DEF_EVS, ITEM_PARAM_GIVE_SPEED_EVS, ITEM_PARAM_GIVE_SPATK_EVS, ITEM_PARAM_GIVE_SPDEF_EVS,
                 ITEM_PARAM_GIVE_FRIENDSHIP_LOW, ITEM_PARAM_GIVE_FRIENDSHIP_MED, ITEM_PARAM_GIVE_FRIENDSHIP_HIGH,
                 ITEM_PARAM_HP_EVS, ITEM_PARAM_ATK_EVS, ITEM_PARAM_DEF_EVS, ITEM_PARAM_SPEED_EVS, ITEM_PARAM_SPATK_EVS,
                 ITEM_PARAM_SPDEF_EVS, ITEM_PARAM_HP_RESTORED, ITEM_PARAM_PP_RESTORED, ITEM_PARAM_FRIENDSHIP_LOW,
                 ITEM_PARAM_FRIENDSHIP_MED, ITEM_PARAM_FRIENDSHIP_HIGH };
enum Flavor { FLAVOR_DUMMY };

// The drawing, the particles, the link: the game's (nothing here)
void BattleArcade_UpdateBackgroundForEffect(BattleArcade *arcade, FrontierGraphics *graphics);
void BattleArcade_LoadNormalBackground(void *arcade, FrontierGraphics *graphics);
void BattleArcade_CreateMonSprites(BattleArcade *arcade, FrontierGraphics *graphics, u16 isOpponent);
void BattleArcade_DeleteMonSprites(BattleArcade *arcade, FrontierGraphics *graphics, u16 isOpponent);
void BattleArcade_SetPlayerMonSpriteDrawFlag(BattleArcade *arcade, FrontierGraphics *graphics, u16 draw, u16 index);
void BattleArcade_SetOpponentMonSpriteDrawFlag(BattleArcade *arcade, FrontierGraphics *graphics, u16 draw, u16 index);
void BattleArcade_CreateItemSprites(BattleArcade *arcade, FrontierGraphics *graphics, u16 isOpponent);
void BattleArcade_DeleteItemSprites(BattleArcade *arcade, FrontierGraphics *graphics, u16 isOpponent);
void BattleArcade_SetItemDrawFlag(BattleArcade *arcade, FrontierGraphics *graphics, u16 isOpponent, u16 slot, u16 drawItem);
void BattleArcade_SetPalette(u8 fraction, u8 source);
BOOL BattleArcade_SendCommMessage(BattleArcade *arcade, u16 command, u16 arg);
VecFx32 *Sprite_GetPosition(Sprite *sprite);
void Sprite_SetPosition(Sprite *sprite, VecFx32 *pos);
void Sprite_SetExplicitPriority(Sprite *sprite, int priority);
void GXLayers_EngineAToggleLayers(u32 mask, int on);
void PaletteData_Blend(void *pltt, int buf, int start, int size, int fraction, int color);
void *ov104_0223D5A8(void *frontier, int id);
u32 ov63_0222D050(void *sprite);
typedef struct { Sprite *sprite; } UnkStruct_ov104_0223C634;
ParticleSystem *FrontierParticleSystem_GetParticleSystem(void *ps, int i);
void ParticleSystem_CreateEmitterWithCallback(ParticleSystem *ps, int id, void (*cb)(SPLEmitter *), void *param);
void *ParticleSystem_GetEmitterCallbackParam(void);
void ParticleSystem_GetEmitterAxis(SPLEmitter *emitter, VecFx16 *axis);
void SPLEmitter_SetAxis(SPLEmitter *emitter, VecFx16 *axis);
void SPLEmitter_SetPos(SPLEmitter *emitter, const VecFx32 *pos);

// The board's calls: the app's frame, the screen, sound, touch, the link (the harness chooses when the stop is touched)
void Overlay_LoadByID(int id, int mode);
void Overlay_UnloadByID(int id);
void Heap_Create(int parent, int heapID, u32 size);
void Heap_Destroy(int heapID);
void *ApplicationManager_NewData(ApplicationManager *appMan, u32 size, int heapID);
void *ApplicationManager_Data(ApplicationManager *appMan);
void *ApplicationManager_Args(ApplicationManager *appMan);
void ApplicationManager_FreeData(ApplicationManager *appMan);
BgConfig *BgConfig_New(int heapID);
BattleFrontierSave *SaveData_GetBattleFrontier(SaveData *saveData);
BattleArcadeSave *BattleArcadeSave_Get(SaveData *saveData);
BattleArcadeStreakFlags *BattleArcadeStreakFlags_Get(SaveData *saveData);
void CommTool_ClearReceivedTempDataAllPlayers(void);
void CommTool_Init(int heapID);
void CommTiming_StartSync(int n);
BOOL CommTiming_IsSyncState(int n);
BOOL CommSys_SendData(int cmd, void *data, int size);
void StartScreenFade(int screens, int typeTop, int typeBottom, int color, int frames, int frameStep, int heapID);
BOOL IsScreenFadeDone(void);
void SpriteList_Update(void *list);
void VramTransfer_Free(void);
void SetVBlankCallback(void *cb, void *data);
void Sound_PlayEffect(u16 seq);
void Sound_StopEffect(u16 seq, int a);
int TouchScreen_CheckPressedHitTableID(const TouchScreenHitTable *table);
void BattleArcadeAppSprite_SetAnim(BattleArcadeAppSprite *sprite, int anim);
void BattleArcadeAppSprite_SetDrawFlag(BattleArcadeAppSprite *sprite, BOOL on);
void BattleArcadeAppSprite_SetPosition(BattleArcadeAppSprite *sprite, int x, int y);
#endif
