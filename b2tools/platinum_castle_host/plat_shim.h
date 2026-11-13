// Platinum's side of the Castle harness: the types and the calls its Battle Castle code makes into the rest of the game (the
// save, the party, the battle's setup, the sets, the scene's context, the screens' drawing). The rules themselves are the decomp's
// own text (extract.py); nothing here decides anything of them. sim.c implements the calls; the Pokémon here is a model (the
// fields the Castle reads and writes, a level from its experience), the same one ours is given (sim.c).
#ifndef CASTLE_HOST_PLAT_SHIM_H
#define CASTLE_HOST_PLAT_SHIM_H
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
#define TRUE 1
#define FALSE 0
#define NELEMS(a) (sizeof(a) / sizeof((a)[0]))
#define UNUSED(x) ((void)(x))
#define GF_ASSERT(x) ((void)0)
#define MI_CpuClear8(p, n) memset((p), 0, (n))
#define MI_CpuClearFast(p, n) memset((p), 0, (n))
#define MI_CpuCopy8(s, d, n) memmove((d), (s), (n))
#define MATH_MAX(a, b) ((a) > (b) ? (a) : (b))
#define FX32_ONE 4096

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
#define FRONTIER_CHALLENGE_SINGLE 0
#define FRONTIER_CHALLENGE_DOUBLE 1
#define FRONTIER_CHALLENGE_MULTI 2
#define FRONTIER_CHALLENGE_MULTI_WFC 3
#define FRONTIER_NEXT_BATTLE_NORMAL 0
#define FRONTIER_NEXT_BATTLE_SILVER 1
#define FRONTIER_NEXT_BATTLE_GOLD 2
#define CASTLE_BATTLES_PER_ROUND 7
#define CASTLE_STREAK_SILVER_BATTLE 21
#define CASTLE_STREAK_GOLD_BATTLE 49
#define CASTLE_MAX_DISTINCT_ROUNDS ((CASTLE_STREAK_GOLD_BATTLE / CASTLE_BATTLES_PER_ROUND) + 1)
#define CASTLE_PARTY_SIZE_SOLO 3
#define CASTLE_PARTY_SIZE_MULTI 2
#define CASTLE_MAX_PARTY_SIZE MATH_MAX(CASTLE_PARTY_SIZE_SOLO, 2 * CASTLE_PARTY_SIZE_MULTI)
#define CASTLE_MAX_LEVEL 50
#define BATTLE_CASTLE_RANK_HEALING 0
#define BATTLE_CASTLE_RANK_RENTALS 1
#define BATTLE_CASTLE_RANK_OPPONENT_SUMMARY 2
#define BATTLE_CASTLE_NUM_RANK_TYPES 3
#define BATTLE_TYPE_FRONTIER_SINGLES 0x80
#define BATTLE_TYPE_FRONTIER_DOUBLES 0x81
#define BATTLE_TYPE_FRONTIER_LINK 0x4
#define BATTLE_TYPE_TRAINER_DOUBLES 0x2
#define BATTLE_TYPE_2vs2 0x8
#define BACKGROUND_BATTLE_CASTLE 17
#define TERRAIN_BATTLE_CASTLE 17
#define gGameLanguage 2
#define TEXT_BANK_FRONTIER_TRAINER_NAMES 21
#define TEXT_BANK_BATTLE_CASTLE_SELF_APP 199
#define TEXT_BANK_ITEM_NAMES 392
#define MSG_LOADER_LOAD_ON_DEMAND 0
#define MSG_LOADER_PRELOAD_ENTIRE_BANK 1
#define RECORD_CASTLE_POINTS_RECEIVED 1
#define BG_LAYER_MAIN_3 3
#define BG_TILE_FLIP_H 0x400
#define MENU_YES 0
#define MENU_NO 1
#define MENU_NOTHING_CHOSEN -1
#define MENU_CANCEL -2
#define PAD_BUTTON_A 0x1
#define PAD_BUTTON_B 0x2
#define PAD_KEY_RIGHT 0x10
#define PAD_KEY_LEFT 0x20
#define PAD_KEY_UP 0x40
#define PAD_KEY_DOWN 0x80
#define JOY_NEW(buttons) (gSystem.pressedKeys & (buttons))
#define FONT_SYSTEM 0
#define FONT_MESSAGE 1
#define TEXT_SPEED_NO_TRANSFER 0
#define TEXT_SPEED_INSTANT 1
#define PADDING_MODE_NONE 0
#define PADDING_MODE_SPACES 1
#define GX_PLANEMASK_BG2 4
#define BG_LAYER_MAIN_0 0
#define BG_LAYER_MAIN_2 2
#define SE_CONFIRM_sseq_3 1500
#define SEQ_SE_DP_BOX03_sseq 1501
#define SEQ_SE_DP_KAIFUKU_sseq 1502
#define SEQ_SE_DP_UG_020_sseq 1503
#define SEQ_SE_DP_OPEN7_sseq 1504
#define SEQ_SE_DP_CLOSE7_sseq 1505
#define SEQ_SE_DP_PIRORIRO2_sseq 1506
#define LIST_MENU_PARENT 19
#define LIST_MENU_COUNT 2
#define LIST_MENU_MAX_DISPLAY 3
#define LIST_MENU_WINDOW 4
enum TextAlignment { TEXT_ALIGN_LEFT, TEXT_ALIGN_RIGHT, TEXT_ALIGN_CENTER };
enum PaddingMode { PADDING_MODE_DUMMY };
enum BgLayer { BG_LAYER_DUMMY };
enum HeapID { HEAP_ID_SYSTEM = 0, HEAP_ID_FIELD1 = 4, HEAP_ID_FIELD2 = 11, HEAP_ID_BATTLE_CASTLE_APP = 100 };
enum NarcID { NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDTR = 1, NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDPM,
              NARC_INDEX_MSGDATA__PL_MSG };
enum BattleFrontierStatsIndex { STAT_CASTLE_INDEX_DUMMY = -1 };
enum { BATTLER_PLAYER_1, BATTLER_ENEMY_1, BATTLER_PLAYER_2, BATTLER_ENEMY_2, MAX_BATTLERS };
enum Flavor { FLAVOR_DUMMY };

// The Pokémon (the model) and the party
enum { MON_DATA_SPECIES = 1, MON_DATA_SPECIES_EXISTS, MON_DATA_IS_EGG, MON_DATA_LEVEL, MON_DATA_EXPERIENCE, MON_DATA_HP,
       MON_DATA_MAX_HP, MON_DATA_STATUS, MON_DATA_HELD_ITEM, MON_DATA_FORM, MON_DATA_COMBINED_IVS, MON_DATA_MOVE1,
       MON_DATA_MOVE2, MON_DATA_MOVE3, MON_DATA_MOVE4, MON_DATA_MOVE1_PP, MON_DATA_MOVE2_PP, MON_DATA_MOVE3_PP,
       MON_DATA_MOVE4_PP, MON_DATA_MOVE1_PP_UPS, MON_DATA_MOVE2_PP_UPS, MON_DATA_MOVE3_PP_UPS, MON_DATA_MOVE4_PP_UPS,
       MON_DATA_MOVE1_MAX_PP, MON_DATA_MOVE2_MAX_PP, MON_DATA_MOVE3_MAX_PP, MON_DATA_MOVE4_MAX_PP, MON_DATA_OT_ID,
       MON_DATA_HP_EV, MON_DATA_ATK_EV, MON_DATA_DEF_EV, MON_DATA_SPEED_EV, MON_DATA_SPATK_EV, MON_DATA_SPDEF_EV,
       MON_DATA_ABILITY, MON_DATA_FRIENDSHIP, MON_DATA_NICKNAME_STRING, MON_DATA_NICKNAME, MON_DATA_PERSONALITY,
       MON_DATA_LANGUAGE, MON_DATA_ATK, MON_DATA_DEF, MON_DATA_SP_ATK, MON_DATA_SP_DEF, MON_DATA_SPEED, MON_DATA_GENDER };
typedef struct Pokemon {
    u16 species, item, form, hp, maxHp;
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
typedef struct Menu Menu;
typedef struct ListMenu ListMenu;
typedef struct PaletteData PaletteData;
typedef struct FontSpecialCharsContext FontSpecialCharsContext;
typedef struct Options Options;
typedef struct NARC NARC;
typedef struct BattleCastleAppSprite BattleCastleAppSprite;
typedef struct ItemData ItemData;
typedef struct { int dummy; } Window;
typedef struct { int dummy; Window *window; } MenuTemplate;
typedef struct { int dummy; } StringList;
typedef struct { int dummy; } ListMenuTemplate;
typedef struct { int dummy; } BattleCastleAppSpriteManager;
typedef struct { BgConfig *bgConfig; } FrontierGraphics;
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
    int background, terrain;
} FieldBattleDTO;
typedef struct { u32 x; } ApplicationManagerTemplate;
extern const ApplicationManagerTemplate gBattleApplicationTemplate;
typedef struct { u32 pressedKeys; } HarnessSystem;
extern HarnessSystem gSystem;

typedef struct BattleFrontierSave BattleFrontierSave;
typedef struct FrontierScriptManager FrontierScriptManager;
#define TEXT_BANK_SPECIES_NAME 412
#include "plat_types.h"

// The Frontier's save: the Castle's challenge, its persistent flags, the records
typedef struct {
    u16 soloStats[112];
    u16 wfcStats[MAX_FRIENDS][32];
} BattleFrontierStats;
struct BattleFrontierSave {
    BattleFrontierStats stats;
    BattleCastleSave castleSave;
    struct {
        BattleCastlePersistentSave persistentSave;
    } castle;
};
#define STATS_NUM_SOLO_STATS_AND_ACTIVE_FLAGS 112

// The scene's context (FrontierScriptContext): its arguments from a stream the harness fills
struct FrontierScriptManager {
    void *frontier;
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
void BattleFrontier_PrintNormalTrainerMessage(FrontierScriptContext *ctx, u16 *msg);
void sub_0209BA80(void *castle);
BOOL BattleCastle_SendCommMessage(BattleCastle *castle, u16 command, u16 arg);

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

u16 LCRNG_Next(void);
void *Heap_Alloc(int heapID, u32 size);
void Heap_Free(void *p);
Party *Party_New(int heapID);
void Party_Init(Party *party);
void Party_InitWithCapacity(Party *party, int capacity);
BOOL Party_AddPokemon(Party *party, Pokemon *mon);
void Party_AddPokemonBySlotIndex(Party *party, int slot, Pokemon *mon);
int Party_GetCurrentCount(const Party *party);
Pokemon *Party_GetPokemonBySlotIndex(const Party *party, int slot);
void Party_HealAllMembers(Party *party);
void OS_ResetSystem(int a);
Pokemon *Pokemon_New(int heapID);
void Pokemon_Init(Pokemon *mon);
void Pokemon_Copy(Pokemon *src, Pokemon *dest);
u32 Pokemon_GetValue(Pokemon *mon, int field, void *dest);
void Pokemon_SetValue(Pokemon *mon, int field, const void *value);
void Pokemon_IncreaseValue(Pokemon *mon, int field, int value);
void Pokemon_InitWith(Pokemon *mon, int species, int level, int ivs, BOOL useMonPersonalityParam, u32 personality,
                      int otIDSource, u32 otID);
void Pokemon_CalcLevelAndStats(Pokemon *mon);
u32 Pokemon_GetSpeciesBaseExpAt(int species, int level);
u32 Pokemon_GetExpToNextLevel(Pokemon *mon);
void Pokemon_UpdateAfterCatch(Pokemon *mon, TrainerInfo *trainer, int ball, int metLocation, int metTerrain, int heapID);
BoxPokemon *Pokemon_GetBoxPokemon(Pokemon *mon);
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
void *SaveData_GetGameRecords(SaveData *saveData);
void GameRecords_AddToRecordValue(void *records, int record, int value);
BOOL SystemVars_GetWiFiFrontierCleared(void *varsFlags);
int NintendoWFC_GetHostFriendIdx(void);
int BattleFrontierStats_GetHostFriendIdx(u32 statIndex);
u16 BattleFrontierSave_GetStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID);
u16 BattleFrontierSave_SetStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID, u16 newValue);
u16 BattleFrontierSave_AddToStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID, int addValue);
u16 BattleFrontierSave_SubtractFromStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID,
                                        int subtractValue);
u16 BattleFrontierSave_SetIfBetter(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID,
                                   u16 newValue);
#define BattleFrontierSave_GetStatAutoHostIdx(f, i) BattleFrontierSave_GetStat(f, i, BattleFrontierStats_GetHostFriendIdx(i))
#define BattleFrontierSave_SetStatAutoHostIdx(f, i, v) BattleFrontierSave_SetStat(f, i, BattleFrontierStats_GetHostFriendIdx(i), v)
#define BattleFrontierSave_SetIfBetterAutoHostIdx(f, i, v) BattleFrontierSave_SetIfBetter(f, i, BattleFrontierStats_GetHostFriendIdx(i), v)
enum BattleFrontierStatsIndex BattleFrontierStats_GetCastleRankIndex(u8 challengeType, u8 rankType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetCastleLatestStreakIndex(u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetCastleRecordStreakIndex(u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetCastleLatestCPIndex(u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetCastleSpentCPIndex(u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetCastleRecordCPIndex(u8 challengeType);
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
void Bg_LoadToTilemapRect(BgConfig *bg, u32 layer, const void *src, u8 x, u8 y, u8 w, u8 h);
void Bg_ScheduleTilemapTransfer(BgConfig *bg, u32 layer);
// item_use_pokemon.c's calls
enum ItemParam { ITEM_PARAM_PARTY_USE = 1, ITEM_PARAM_HEAL_SLEEP, ITEM_PARAM_HEAL_POISON, ITEM_PARAM_HEAL_BURN,
                 ITEM_PARAM_HEAL_FREEZE, ITEM_PARAM_HEAL_PARALYSIS, ITEM_PARAM_REVIVE, ITEM_PARAM_REVIVE_ALL,
                 ITEM_PARAM_LEVEL_UP, ITEM_PARAM_EVOLVE, ITEM_PARAM_PP_UP, ITEM_PARAM_PP_MAX, ITEM_PARAM_PP_RESTORE,
                 ITEM_PARAM_PP_RESTORE_ALL, ITEM_PARAM_HP_RESTORE, ITEM_PARAM_GIVE_HP_EVS, ITEM_PARAM_GIVE_ATK_EVS,
                 ITEM_PARAM_GIVE_DEF_EVS, ITEM_PARAM_GIVE_SPEED_EVS, ITEM_PARAM_GIVE_SPATK_EVS, ITEM_PARAM_GIVE_SPDEF_EVS,
                 ITEM_PARAM_GIVE_FRIENDSHIP_LOW, ITEM_PARAM_GIVE_FRIENDSHIP_MED, ITEM_PARAM_GIVE_FRIENDSHIP_HIGH,
                 ITEM_PARAM_HP_EVS, ITEM_PARAM_ATK_EVS, ITEM_PARAM_DEF_EVS, ITEM_PARAM_SPEED_EVS, ITEM_PARAM_SPATK_EVS,
                 ITEM_PARAM_SPDEF_EVS, ITEM_PARAM_HP_RESTORED, ITEM_PARAM_PP_RESTORED, ITEM_PARAM_FRIENDSHIP_LOW,
                 ITEM_PARAM_FRIENDSHIP_MED, ITEM_PARAM_FRIENDSHIP_HIGH };
#define ITEM_FILE_TYPE_DATA 0
ItemData *Item_Load(u16 item, int type, int heapID);
s32 Item_Get(ItemData *item, int param);
u8 Item_LoadParam(u16 item, int param, int heapID);
BOOL Pokemon_CanEvolve(Pokemon *mon);

// The screens' calls: drawing and input (sim.c: the input is the harness's choice, the drawing nothing but the messages logged)
u32 ListMenu_ProcessInput(ListMenu *menu);
void ListMenu_CalcTrueCursorPos(ListMenu *menu, u16 *pos);
void ListMenu_TestInput(ListMenu *menu, ListMenuTemplate *t, u16 a, u16 b, u16 c, u32 key, void *d, void *e);
void ListMenu_Draw(ListMenu *menu);
u32 ListMenu_GetAttribute(ListMenu *menu, int attr);
void ListMenu_GetListAndCursorPos(ListMenu *menu, u16 *list, u16 *cursor);
void ListMenu_SetTextColors(ListMenu *menu, u8 fg, u8 bg, u8 shadow);
u32 Menu_ProcessInput(Menu *menu);
void Sound_PlayEffect(u16 seq);
void Sound_StopEffect(u16 seq, int a);
void GXLayers_EngineAToggleLayers(u32 mask, int on);
u8 Options_Frame(Options *options);
void Window_ClearAndScheduleCopyToVRAM(Window *window);
void Window_FillTilemap(Window *window, u8 fill);
void Window_ScheduleCopyToVRAM(Window *window);
void StringTemplate_SetItemNameWithArticle(StringTemplate *t, u32 idx, u32 item);
void StringTemplate_SetItemName(StringTemplate *t, u32 idx, u32 item);
void BattleCastleApp_DrawMessageBox(Window *window, u8 frame);
void BattleCastleApp_DrawWindow(BgConfig *bg, Window *window);
void BattleCastleAppSprite_PlaySparkleAnim(BattleCastleAppSprite *sprite, int x, int y);
void BattleCastleAppSprite_SetDrawFlag(BattleCastleAppSprite *sprite, BOOL on);
void BattleCastleApp_SetItemGraphic(BattleCastleAppSpriteManager *man, u16 item);
void BattleCastleApp_SetItemPalette(BattleCastleAppSpriteManager *man, u16 item);
void BattleCastleApp_SetPartnerName(StringTemplate *t, u32 idx);
// What the screens print (sim.c logs each message and the number of string template slot 0)
extern int gMsgLog[16];
extern int gMsgCount;
extern s32 gTemplateNumber0;
#endif
