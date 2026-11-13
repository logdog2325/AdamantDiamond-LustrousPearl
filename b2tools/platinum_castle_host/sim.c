// The Battle Castle's rules, Platinum's own C (plat_castle.c, plat_self_app.c, plat_opponent_app.c, copied by extract.py) against
// ours (the decomp's src/pearlb2/plat_castle/castle_rules.c, PearlB2's src/pokebw2/ copy, compiled as it is), with the same random
// numbers and the same choices.
//
//   sim SETS PERSONAL [SEEDS]
//
// SETS: the Frontier's Trainers and sets (platinum_frontier_data.py --sets, from the dump); PERSONAL: Platinum's personal abilities
// (platinum_hall_data.py --personal).
// Each seed: a save (the records of both challenge types, the streak flags, Darach's intro heard or not) and a field party, the
// same on both sides; then challenges as the Castle's scene script runs them (frontier_scripts_battle_castle.s): Init, the round's
// Trainers, the first opponent, the castle's menu (the two screens' purchases, run through Platinum's own state machines with the
// harness's choices; the pass), the battle (its setup compared: the party as it is, the opponents at their levels, the AI, the
// Trainer; then an outcome the harness draws, the same on both sides: HP and PP used, a status, an item used up, won or lost), the
// CP earned, the next battle's preparation, the round's end and its BP, the rest and the resume, the retire, the loss. Every field of
// the castle, the castle's party, the opponents, the save and the records is compared after every step, and the random state too.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "plat_shim.h"
#undef TRUE
#undef FALSE
#undef NELEMS
#define PEARLB2_HOST 1
#include "pearlb2/plat_castle.h"

// ------------------------------------------------------------------ the data
static FrontierPokemonBase *gSets;
static int gSetCount;
static struct {
    u16 cls, count;
    u16 *sets;
} gTrainers[400];
static int gTrainerCount __attribute__((unused));
static u8 gPersonal[800][2];
static int gPersonalCount;

static void *slurp(const char *path, long *size) {
    FILE *f = fopen(path, "rb");
    if (!f) {
        perror(path);
        exit(2);
    }
    fseek(f, 0, SEEK_END);
    *size = ftell(f);
    fseek(f, 0, SEEK_SET);
    void *p = malloc(*size);
    if (fread(p, 1, *size, f) != (size_t)*size) {
        exit(2);
    }
    fclose(f);
    return p;
}

static void load(const char *setsPath, const char *personalPath) {
    long n;
    u8 *d = slurp(setsPath, &n);
    u32 trainers, sets;
    memcpy(&trainers, d, 4);
    memcpy(&sets, d + 4, 4);
    u8 *p = d + 8;
    for (u32 t = 0; t < trainers; t++) {
        u16 len;
        memcpy(&len, p, 2);
        p += 2;
        u16 *w = (u16 *)malloc(2 * (len + 2));
        memcpy(w, p, 2 * len);
        p += 2 * len;
        gTrainers[t].cls = w[0];
        gTrainers[t].count = w[1];
        gTrainers[t].sets = w + 2;
    }
    gTrainerCount = trainers;
    (void)gTrainerCount;
    gSets = (FrontierPokemonBase *)malloc(sets * sizeof(FrontierPokemonBase));
    memcpy(gSets, p, sets * 16);
    gSetCount = sets;
    u8 *q = slurp(personalPath, &n);
    u16 count;
    memcpy(&count, q, 2);
    memcpy(gPersonal, q + 2, 2 * count);
    gPersonalCount = count;
}

// ------------------------------------------------------------------ the checks
static long gChecks, gProblems;
static const char *gWhere = "start";
static unsigned gSeed;
#define CHECK(cond, ...)                                                                                                    \
    do {                                                                                                                   \
        gChecks++;                                                                                                         \
        if (!(cond)) {                                                                                                     \
            if (gProblems++ < 40) {                                                                                        \
                printf("DIFF seed %u at %s: ", gSeed, gWhere);                                                             \
                printf(__VA_ARGS__);                                                                                       \
                printf("\n");                                                                                              \
            }                                                                                                              \
        }                                                                                                                  \
    } while (0)

static u32 gRng;                        // the harness's own choices (not the rules')
static u32 pick(u32 n) {
    gRng = gRng * 1664525u + 1013904223u;
    return n ? (gRng >> 8) % n : 0;
}

// ------------------------------------------------------------------ the Pokémon (a model both sides use)
u8 MoveTable_CalcMaxPP(u16 move, u8 ppUps) {
    u8 base;
    if (move == 0) {
        return 0;
    }
    base = (u8)(5 * (1 + (move * 7) % 8));
    return (u8)(base + base * ppUps / 5);
}
u32 Pokemon_GetSpeciesBaseExpAt(int species, int level) {
    u32 cube = (u32)level * level * level;
    switch (species % 3) {
    case 0:
        return cube;
    case 1:
        return cube * 4 / 5;
    }
    return cube * 5 / 4;
}
static u32 Stat(Pokemon *mon, int which) {
    return (2 * (40 + (mon->species * 13 + which * 7) % 80) + (mon->ivs & 31) + mon->evs[which] / 4) * mon->level / 100 + 5;
}
// pokemon.c Pokemon_CalcLevelAndStats: the level from the experience, the maximum HP, the HP moved with it
void Pokemon_CalcLevelAndStats(Pokemon *mon) {
    int level = 1, oldMax = mon->maxHp, hp = mon->hp, newMax;
    while (level < 100 && Pokemon_GetSpeciesBaseExpAt(mon->species, level + 1) <= mon->exp) {
        level++;
    }
    mon->level = (u8)level;
    newMax = (2 * (40 + mon->species % 80) + (mon->ivs & 31) + mon->evs[0] / 4) * level / 100 + level + 10;
    mon->maxHp = (u16)newMax;
    if (hp != 0 || oldMax == 0) {
        if (hp == 0) {
            hp = newMax;
        } else {
            hp += newMax - oldMax;
        }
    }
    if (hp) {
        mon->hp = (u16)hp;
    }
}
u32 Pokemon_GetValue(Pokemon *mon, int field, void *dest) {
    (void)dest;
    if (field >= MON_DATA_MOVE1 && field <= MON_DATA_MOVE4) {
        return mon->moves[field - MON_DATA_MOVE1];
    }
    if (field >= MON_DATA_MOVE1_PP && field <= MON_DATA_MOVE4_PP) {
        return mon->pp[field - MON_DATA_MOVE1_PP];
    }
    if (field >= MON_DATA_MOVE1_PP_UPS && field <= MON_DATA_MOVE4_PP_UPS) {
        return mon->ppUps[field - MON_DATA_MOVE1_PP_UPS];
    }
    if (field >= MON_DATA_MOVE1_MAX_PP && field <= MON_DATA_MOVE4_MAX_PP) {
        int i = field - MON_DATA_MOVE1_MAX_PP;
        return MoveTable_CalcMaxPP(mon->moves[i], mon->ppUps[i]);
    }
    if (field >= MON_DATA_HP_EV && field <= MON_DATA_SPDEF_EV) {
        return mon->evs[field - MON_DATA_HP_EV];
    }
    switch (field) {
    case MON_DATA_SPECIES: return mon->species;
    case MON_DATA_SPECIES_EXISTS: return mon->species != 0;
    case MON_DATA_IS_EGG: return mon->isEgg;
    case MON_DATA_LEVEL: return mon->level;
    case MON_DATA_EXPERIENCE: return mon->exp;
    case MON_DATA_HP: return mon->hp;
    case MON_DATA_MAX_HP: return mon->maxHp;
    case MON_DATA_STATUS: return mon->status;
    case MON_DATA_HELD_ITEM: return mon->item;
    case MON_DATA_FORM: return mon->form;
    case MON_DATA_COMBINED_IVS: return mon->ivs;
    case MON_DATA_OT_ID: return mon->otID;
    case MON_DATA_ABILITY: return mon->ability;
    case MON_DATA_FRIENDSHIP: return mon->friendship;
    case MON_DATA_PERSONALITY: return mon->personality;
    case MON_DATA_LANGUAGE: return mon->language;
    case MON_DATA_ATK: return Stat(mon, 1);
    case MON_DATA_DEF: return Stat(mon, 2);
    case MON_DATA_SPEED: return Stat(mon, 3);
    case MON_DATA_SP_ATK: return Stat(mon, 4);
    case MON_DATA_SP_DEF: return Stat(mon, 5);
    }
    return 0;
}
void Pokemon_SetValue(Pokemon *mon, int field, const void *value) {
    const u8 *b = value;
    const u16 *h = value;
    const u32 *w = value;
    if (field >= MON_DATA_MOVE1 && field <= MON_DATA_MOVE4) {
        mon->moves[field - MON_DATA_MOVE1] = *h;
        return;
    }
    if (field >= MON_DATA_MOVE1_PP && field <= MON_DATA_MOVE4_PP) {
        mon->pp[field - MON_DATA_MOVE1_PP] = *b;
        return;
    }
    if (field >= MON_DATA_MOVE1_PP_UPS && field <= MON_DATA_MOVE4_PP_UPS) {
        mon->ppUps[field - MON_DATA_MOVE1_PP_UPS] = *b;
        return;
    }
    if (field >= MON_DATA_HP_EV && field <= MON_DATA_SPDEF_EV) {
        mon->evs[field - MON_DATA_HP_EV] = *b;
        return;
    }
    switch (field) {
    case MON_DATA_SPECIES: mon->species = *h; break;
    case MON_DATA_LEVEL: mon->level = *b; break;
    case MON_DATA_EXPERIENCE: mon->exp = *w; break;
    case MON_DATA_HP: mon->hp = *h; break;
    case MON_DATA_MAX_HP: mon->maxHp = *h; break;
    case MON_DATA_STATUS: mon->status = *w; break;
    case MON_DATA_HELD_ITEM: mon->item = *h; break;
    case MON_DATA_FORM: mon->form = *b; break;
    case MON_DATA_COMBINED_IVS: mon->ivs = *w; break;
    case MON_DATA_OT_ID: mon->otID = *w; break;
    case MON_DATA_ABILITY: mon->ability = *b; break;
    case MON_DATA_FRIENDSHIP: mon->friendship = *b; break;
    case MON_DATA_LANGUAGE: mon->language = *b; break;
    }
}
void Pokemon_IncreaseValue(Pokemon *mon, int field, int value) {
    if (field == MON_DATA_EXPERIENCE) {
        mon->exp += value;
    }
}
u32 Pokemon_GetExpToNextLevel(Pokemon *mon) {
    return Pokemon_GetSpeciesBaseExpAt(mon->species, mon->level + 1) - mon->exp;
}
void Pokemon_Init(Pokemon *mon) { memset(mon, 0, sizeof(*mon)); }
Pokemon *Pokemon_New(int heapID) { (void)heapID; return calloc(1, sizeof(Pokemon)); }
void Pokemon_Copy(Pokemon *src, Pokemon *dest) { *dest = *src; }
BoxPokemon *Pokemon_GetBoxPokemon(Pokemon *mon) { return mon; }
void Pokemon_UpdateAfterCatch(Pokemon *mon, TrainerInfo *t, int ball, int loc, int terrain, int heap) {
    (void)mon, (void)t, (void)ball, (void)loc, (void)terrain, (void)heap;
}
int SpeciesData_GetSpeciesValue(int species, int param) {
    return species < gPersonalCount ? gPersonal[species][param == SPECIES_DATA_ABILITY_2] : 0;
}
// pokemon.c Pokemon_InitWith -> sub_02073E18: its random numbers (a personality unless given, a trainer id that isn't shiny
// with it for OTID_NOT_SHINY, the IVs drawn when the number given is 32 or more), the experience of the level, the ability
static u32 gPlatLCRNG;
u16 LCRNG_Next(void) {
    gPlatLCRNG = gPlatLCRNG * 1103515245L + 24691;
    return gPlatLCRNG >> 16;
}
void Pokemon_InitWith(Pokemon *mon, int species, int level, int ivs, BOOL usePersonality, u32 personality, int otIDSource,
                      u32 otID) {
    u32 v1;
    memset(mon, 0, sizeof(*mon));
    if (!usePersonality) {
        personality = LCRNG_Next();
        personality |= (u32)LCRNG_Next() << 16;
    }
    mon->personality = personality;
    if (otIDSource == OTID_NOT_SHINY) {
        do {
            otID = LCRNG_Next();
            otID |= (u32)LCRNG_Next() << 16;
        } while (Pokemon_IsPersonalityShiny(otID, personality));
    } else if (otIDSource != OTID_SET) {
        otID = 0;
    }
    mon->otID = otID;
    mon->species = (u16)species;
    mon->exp = Pokemon_GetSpeciesBaseExpAt(species, level);
    if (ivs < INIT_IVS_RANDOM) {
        mon->ivs = (u32)ivs * 0x2108421u;
    } else {
        v1 = LCRNG_Next();
        mon->ivs = v1 & 0x7fff;
        v1 = LCRNG_Next();
        mon->ivs |= (v1 & 0x7fff) << 15;
    }
    mon->ability = (u8)SpeciesData_GetSpeciesValue(species, (personality & 1) && SpeciesData_GetSpeciesValue(species, 1) ?
                                                                SPECIES_DATA_ABILITY_2 : SPECIES_DATA_ABILITY_1);
    mon->level = (u8)level;
    Pokemon_CalcLevelAndStats(mon);
}

// The party
void *Heap_Alloc(int heapID, u32 size) { (void)heapID; return calloc(1, size); }
void Heap_Free(void *p) { free(p); }
Party *Party_New(int heapID) { (void)heapID; return calloc(1, sizeof(Party)); }
void Party_Init(Party *party) { memset(party, 0, sizeof(Party)); }
void Party_InitWithCapacity(Party *party, int capacity) { (void)capacity; memset(party, 0, sizeof(Party)); }
BOOL Party_AddPokemon(Party *party, Pokemon *mon) {
    if (party->count >= 6) {
        return FALSE;
    }
    party->mons[party->count++] = *mon;
    return TRUE;
}
void Party_AddPokemonBySlotIndex(Party *party, int slot, Pokemon *mon) {     // party.c: the count moves by the species' presence
    int add = (party->mons[slot].species != 0) - (mon->species != 0);
    party->mons[slot] = *mon;
    party->count += add;
}
int Party_GetCurrentCount(const Party *party) { return party->count; }
Pokemon *Party_GetPokemonBySlotIndex(const Party *party, int slot) { return (Pokemon *)&party->mons[slot]; }

// ------------------------------------------------------------------ Platinum's side: the game around its Castle code
struct SaveData {
    BattleFrontierSave frontier;
    Party party;
};
static SaveData gPlatSave;
static BattleCastle *gPlatCastle;
static FieldFrontierDTO gFieldData;
static FrontierScriptManager gScriptMan;
static FrontierGraphics gGraphics;
static u16 gVars[16];
static FieldBattleDTO *gLastDTO;
const ApplicationManagerTemplate gBattleApplicationTemplate = { 0 };
HarnessSystem gSystem;
int gMsgLog[16];
int gMsgCount;
s32 gTemplateNumber0;

u16 FrontierScriptContext_GetVar(FrontierScriptContext *ctx) { return ctx->args[ctx->at++]; }
u16 *FrontierScriptContext_TryGetVarPointer(FrontierScriptContext *ctx) { return &gVars[ctx->args[ctx->at++] & 15]; }
u8 FrontierScriptContext_ReadByte(FrontierScriptContext *ctx) { return (u8)ctx->args[ctx->at++]; }
u16 FrontierScriptContext_ReadHalfWord(FrontierScriptContext *ctx) { return ctx->args[ctx->at++]; }
void *BattleFrontier_GetFacilityStruct(void *frontier) { (void)frontier; return gPlatCastle; }
void BattleFrontier_SetFacilityStruct(void *frontier, void *facility) { (void)frontier; gPlatCastle = facility; }
FieldFrontierDTO *BattleFrontier_GetFieldData(void *frontier) { (void)frontier; return &gFieldData; }
void BattleFrontier_RunSubApp(void *frontier, const ApplicationManagerTemplate *t, void *args, int a, void (*cb)(void *)) {
    (void)frontier, (void)t, (void)a, (void)cb;
    gLastDTO = args;
}
FrontierGraphics *FrontierScriptManager_GetGraphics(FrontierScriptManager *scriptMan) { (void)scriptMan; return &gGraphics; }
BOOL CheckPlayerWonBattle(u32 resultMask) { return resultMask == 1; }
void FieldBattleDTO_Free(FieldBattleDTO *dto) {
    for (int i = 0; i < MAX_BATTLERS; i++) {
        free(dto->parties[i]);
    }
    free(dto);
}
void BattleFrontier_PrintNormalTrainerMessage(FrontierScriptContext *ctx, u16 *msg) { (void)ctx, (void)msg; }
void sub_0209BA80(void *castle) { (void)castle; }
BOOL BattleCastle_SendCommMessage(BattleCastle *castle, u16 command, u16 arg) { (void)castle, (void)command, (void)arg; return TRUE; }
void OS_ResetSystem(int a) { (void)a; }
void BattleFrontier_FlagGeonetLinkInfo(SaveData *saveData) { (void)saveData; }
struct String {
    u16 codes[8];
};
static struct String gNameString = { { 0xffff } };
void *NARC_AllocAndReadWholeMemberByIndexPair(int narcID, int index, int heapID) {
    (void)narcID, (void)heapID;
    FrontierTrainerBase *b = calloc(1, 4 + 2 * (gTrainers[index].count + 1));
    b->trainerType = gTrainers[index].cls;
    b->numSets = gTrainers[index].count;
    memcpy(b->setIDs, gTrainers[index].sets, 2 * gTrainers[index].count);
    return b;
}
void NARC_ReadWholeMemberByIndexPair(void *dest, int narcID, int index) {
    (void)narcID;
    memcpy(dest, &gSets[index], sizeof(FrontierPokemonBase));
}
u16 BattleFrontier_GetObjectIDFromTrainerClass(u8 trainerClass) { return trainerClass; }
void *SaveData_SaveTable(SaveData *saveData, int entry) { (void)entry; return &saveData->frontier; }
BattleFrontierSave *SaveData_GetBattleFrontier(SaveData *saveData) { return &saveData->frontier; }
Party *SaveData_GetParty(SaveData *saveData) { return &saveData->party; }
void *SaveData_GetVarsFlags(SaveData *saveData) { return saveData; }
TrainerInfo *SaveData_GetTrainerInfo(SaveData *saveData) { (void)saveData; return NULL; }
void *SaveData_GetGameRecords(SaveData *saveData) { return saveData; }
void GameRecords_AddToRecordValue(void *records, int record, int value) { (void)records, (void)record, (void)value; }
BOOL SystemVars_GetWiFiFrontierCleared(void *varsFlags) { (void)varsFlags; return FALSE; }
int NintendoWFC_GetHostFriendIdx(void) { return 0; }
FieldBattleDTO *FieldBattleDTO_New(int heapID, u32 battleType) {
    (void)heapID;
    FieldBattleDTO *dto = calloc(1, sizeof(FieldBattleDTO));
    dto->battleType = battleType;
    for (int i = 0; i < MAX_BATTLERS; i++) {
        dto->parties[i] = calloc(1, sizeof(Party));
    }
    return dto;
}
void FieldBattleDTO_InitFromGameState(FieldBattleDTO *dto, void *a, SaveData *s, int m, void *j, void *b, u8 *c) {
    (void)dto, (void)a, (void)s, (void)m, (void)j, (void)b, (void)c;
}
void FieldBattleDTO_AddPokemonToBattler(FieldBattleDTO *dto, Pokemon *mon, int battler) { Party_AddPokemon(dto->parties[battler], mon); }
void FieldBattleDTO_CopyPlayerInfoToTrainerData(FieldBattleDTO *dto) { (void)dto; }
void FieldBattleDTO_InitFrontierTrainer(FieldBattleDTO *dto, FrontierTrainer *trainer, int unused, int battler, enum HeapID heapID) {
    (void)unused, (void)heapID;
    dto->trainerIDs[battler] = trainer->trainerID;
    dto->trainer[battler].header.trainerType = trainer->trainerType;
}
TrainerInfo *CommInfo_TrainerInfo(int netID) { (void)netID; return NULL; }
int CommSys_CurNetId(void) { return 0; }
void TrainerInfo_Copy(TrainerInfo *src, TrainerInfo *dest) { (void)src, (void)dest; }
MessageLoader *MessageLoader_Init(int mode, int narc, int bank, int heapID) { (void)mode, (void)narc, (void)bank, (void)heapID; return NULL; }
String *MessageLoader_GetNewString(MessageLoader *loader, int id) { (void)loader, (void)id; return &gNameString; }
void MessageLoader_Free(MessageLoader *loader) { (void)loader; }
void MessageLoader_GetSpeciesName(int species, int heapID, u16 *dest) { (void)species, (void)heapID; dest[0] = 0xffff; }
void String_Free(String *s) { (void)s; }
void String_ToChars(const String *s, u16 *dest, u32 n) {
    for (u32 i = 0; i < n; i++) {
        dest[i] = s->codes[0];
    }
}
void Bg_LoadToTilemapRect(BgConfig *bg, u32 layer, const void *src, u8 x, u8 y, u8 w, u8 h) {
    (void)bg, (void)layer, (void)src, (void)x, (void)y, (void)w, (void)h;
}
void Bg_ScheduleTilemapTransfer(BgConfig *bg, u32 layer) { (void)bg, (void)layer; }
// Items: a Max Potion's and a Max Elixir's data (res/items/data/max_potion.json, max_elixir.json): party use; the potion's HP
// restored in full (255), the elixir's PP of every move in full (127); no friendship, status or EV change
struct ItemData {
    u16 item;
};
static struct ItemData gItem;
ItemData *Item_Load(u16 item, int type, int heapID) {
    (void)type, (void)heapID;
    ItemData *d = malloc(sizeof(ItemData));
    d->item = item;
    return d;
}
s32 Item_Get(ItemData *item, int param) {
    switch (param) {
    case ITEM_PARAM_PARTY_USE:
        return item->item == ITEM_MAX_POTION || item->item == ITEM_MAX_ELIXIR;
    case ITEM_PARAM_HP_RESTORE:
        return item->item == ITEM_MAX_POTION;
    case ITEM_PARAM_HP_RESTORED:
        return item->item == ITEM_MAX_POTION ? 255 : 0;
    case ITEM_PARAM_PP_RESTORE_ALL:
        return item->item == ITEM_MAX_ELIXIR;
    case ITEM_PARAM_PP_RESTORED:
        return item->item == ITEM_MAX_ELIXIR ? 127 : 0;
    }
    return 0;
}
u8 Item_LoadParam(u16 item, int param, int heapID) { (void)heapID; gItem.item = item; return (u8)Item_Get(&gItem, param); }
BOOL Pokemon_CanEvolve(Pokemon *mon) { (void)mon; return FALSE; }
// The screens' input and drawing
static u32 gListInput;
static u16 gListPos;
static u32 gMenuInput;
u32 ListMenu_ProcessInput(ListMenu *menu) { (void)menu; return gListInput; }
void ListMenu_CalcTrueCursorPos(ListMenu *menu, u16 *pos) { (void)menu; *pos = gListPos; }
void ListMenu_TestInput(ListMenu *menu, ListMenuTemplate *t, u16 a, u16 b, u16 c, u32 key, void *d, void *e) {
    (void)menu, (void)t, (void)a, (void)b, (void)c, (void)key, (void)d, (void)e;
}
void ListMenu_Draw(ListMenu *menu) { (void)menu; }
u32 Menu_ProcessInput(Menu *menu) { (void)menu; return gMenuInput; }
void Sound_PlayEffect(u16 seq) { (void)seq; }
void Sound_StopEffect(u16 seq, int a) { (void)seq, (void)a; }
void GXLayers_EngineAToggleLayers(u32 mask, int on) { (void)mask, (void)on; }
u8 Options_Frame(Options *options) { (void)options; return 0; }
void Window_ClearAndScheduleCopyToVRAM(Window *window) { (void)window; }
void StringTemplate_SetItemNameWithArticle(StringTemplate *t, u32 idx, u32 item) { (void)t, (void)idx, (void)item; }
void StringTemplate_SetItemName(StringTemplate *t, u32 idx, u32 item) { (void)t, (void)idx, (void)item; }
void BattleCastleApp_DrawMessageBox(Window *window, u8 frame) { (void)window, (void)frame; }
void BattleCastleAppSprite_PlaySparkleAnim(BattleCastleAppSprite *sprite, int x, int y) { (void)sprite, (void)x, (void)y; }
void BattleCastleAppSprite_SetDrawFlag(BattleCastleAppSprite *sprite, BOOL on) { (void)sprite, (void)on; }
void BattleCastleApp_SetPartnerName(StringTemplate *t, u32 idx) { (void)t, (void)idx; }

// Platinum's code reached by extract.py's wrappers, the screens' state machines
void Plat_ClearActiveStreak(SaveData *saveData, u8 challengeType);
u16 Plat_GetAIMask(BattleCastle *castle);
void Plat_SetupAppArgs(BattleCastleAppArgs *args, BattleCastle *castle);
void Plat_StoreAppResult(BattleCastleAppArgs *args);
BOOL FrontierScrCmd_InitBattleCastle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_LoadTrainersForRound(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_FreeBattleCastle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleCastle_CleanupBattle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleCastle_StartBattle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleCastle_SetupFirstOpponent(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleCastle_SetupNextOpponent(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_CallBattleCastleFunction(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleCastle_CheckWonBattle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_GetCurrentCastlePoints(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_SpendCastlePoints(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_ReceiveCastlePoints(FrontierScriptContext *ctx);
typedef struct BattleCastleSelfApp BattleCastleSelfApp;
typedef struct BattleCastleOpponentApp BattleCastleOpponentApp;
BOOL Self_State_MainAppFlow(BattleCastleSelfApp *app);
BOOL Opp_State_MainAppFlow(BattleCastleOpponentApp *app);
// (plat_apps_glue.c: the screens' structs are their files' own; these set them up and read them)
BattleCastleSelfApp *Glue_NewSelfApp(SaveData *saveData, BattleCastleAppArgs *args);
BattleCastleOpponentApp *Glue_NewOppApp(SaveData *saveData, BattleCastleAppArgs *args);
int Glue_SelfSubState(BattleCastleSelfApp *app);
void Glue_SelfSetSlot(BattleCastleSelfApp *app, int slot);
int Glue_OppSubState(BattleCastleOpponentApp *app);
void Glue_OppSetSlot(BattleCastleOpponentApp *app, int slot);

// Run a scene command with these arguments (a value or a var number each, as the command reads them)
static void plat_cmd(BOOL (*cmd)(FrontierScriptContext *), int n, ...) {
    u16 args[8];
    __builtin_va_list ap;
    __builtin_va_start(ap, n);
    for (int i = 0; i < n; i++) {
        args[i] = (u16)__builtin_va_arg(ap, int);
    }
    __builtin_va_end(ap);
    FrontierScriptContext ctx = { &gScriptMan, args, 0, { 0 } };
    cmd(&ctx);
}
static u16 plat_fn(int fn, int arg1, int arg2) {
    gVars[8] = 0xbeef;
    plat_cmd(FrontierScrCmd_CallBattleCastleFunction, 4, fn, arg1, arg2, 8);
    return gVars[8];
}

// ------------------------------------------------------------------ our side: the records, the castle's party
typedef struct {
    u16 stats[200];
    u8 streakFlags;
    u8 heardIntro;
} OurRecords;
static OurRecords gOurRec;
static PlatCastleSave gOurSave;
static PlatCastle gOur;
static Pokemon gOurParty[6];
static Party gOurField;

u16 PlatCastle_GetStat(void *records, u32 stat) { return stat < 200 ? ((OurRecords *)records)->stats[stat] : 0; }
void PlatCastle_SetStat(void *records, u32 stat, u16 value) {
    if (stat < 200) {
        ((OurRecords *)records)->stats[stat] = value > 9999 ? 9999 : value;
    }
}
u32 PlatCastle_GetStreakFlag(void *records, u32 type) { return (((OurRecords *)records)->streakFlags >> type) & 1; }
void PlatCastle_SetStreakFlag(void *records, u32 type, u32 value) {
    OurRecords *r = records;
    if (value >= 1) {
        r->streakFlags |= 1 << type;
    } else {
        r->streakFlags &= 0xff ^ (1 << type);
    }
}
u32 PlatCastle_GetHeardIntro(void *records) { return ((OurRecords *)records)->heardIntro; }
void PlatCastle_SetHeardIntro(void *records) { ((OurRecords *)records)->heardIntro = TRUE; }
u32 PlatCastle_FieldMonItem(PlatCastle *castle, u8 fieldSlot) { (void)castle; return gOurField.mons[fieldSlot].item; }
void PlatCastle_PartyAddFieldMon(PlatCastle *castle, u8 fieldSlot) { gOurParty[castle->playerCount] = gOurField.mons[fieldSlot]; }
static const int sOurField[PLATCASTLE_MON_FIELDS] = {
    MON_DATA_SPECIES, MON_DATA_SPECIES_EXISTS, MON_DATA_LEVEL, MON_DATA_HP, MON_DATA_MAX_HP, MON_DATA_STATUS, MON_DATA_HELD_ITEM,
    MON_DATA_MOVE1, MON_DATA_MOVE2, MON_DATA_MOVE3, MON_DATA_MOVE4, MON_DATA_MOVE1_PP, MON_DATA_MOVE2_PP, MON_DATA_MOVE3_PP,
    MON_DATA_MOVE4_PP, MON_DATA_MOVE1_MAX_PP, MON_DATA_MOVE2_MAX_PP, MON_DATA_MOVE3_MAX_PP, MON_DATA_MOVE4_MAX_PP,
};
u32 PlatCastle_MonGet(PlatCastle *castle, u8 slot, u32 field) {
    (void)castle;
    return Pokemon_GetValue(&gOurParty[slot], sOurField[field], NULL);
}
void PlatCastle_MonSet(PlatCastle *castle, u8 slot, u32 field, u32 value) {
    (void)castle;
    Pokemon_SetValue(&gOurParty[slot], sOurField[field], &value);       // (little-endian: the u8 and u16 fields read the low bytes)
}
void PlatCastle_MonSetLevel(PlatCastle *castle, u8 slot, u8 level) {
    (void)castle;
    gOurParty[slot].exp = Pokemon_GetSpeciesBaseExpAt(gOurParty[slot].species, level);
    Pokemon_CalcLevelAndStats(&gOurParty[slot]);
}
void PlatCastle_ReadSet(u16 setID, PlatCastleSet *set) { memcpy(set, &gSets[setID], sizeof(*set)); }
u16 PlatCastle_TrainerSets(u16 trainerID, u16 *sets, u16 max) {
    u16 n = gTrainers[trainerID].count < max ? gTrainers[trainerID].count : max;
    memcpy(sets, gTrainers[trainerID].sets, 2 * n);
    return n;
}
u16 PlatCastle_SpeciesAbility(u16 species, u32 slot) { return (u16)SpeciesData_GetSpeciesValue(species, slot ? SPECIES_DATA_ABILITY_2 : SPECIES_DATA_ABILITY_1); }

// ------------------------------------------------------------------ the comparisons
static long gStat[16];                  // what the run went through
enum { N_CHALLENGES, N_BATTLES, N_WINS, N_LOSSES, N_ROUNDS, N_DARACH, N_PASSES, N_RESTS, N_RETIRES, N_SELF, N_OPP, N_BOUGHT,
       N_RANKUPS, N_CP_EARNED, N_BP, N_FAINTED };

static void compare_mon(const Pokemon *p, const Pokemon *o, const char *what, int i) {
    CHECK(p->species == o->species && p->level == o->level && p->exp == o->exp && p->hp == o->hp && p->maxHp == o->maxHp &&
              p->status == o->status && p->item == o->item,
          "%s %d: species %d/%d level %d/%d exp %u/%u hp %d/%d max %d/%d status %u/%u item %d/%d", what, i, p->species,
          o->species, p->level, o->level, p->exp, o->exp, p->hp, o->hp, p->maxHp, o->maxHp, p->status, o->status, p->item,
          o->item);
    CHECK(!memcmp(p->moves, o->moves, sizeof(p->moves)) && !memcmp(p->pp, o->pp, sizeof(p->pp)) &&
              !memcmp(p->ppUps, o->ppUps, sizeof(p->ppUps)),
          "%s %d: moves or PP", what, i);
}

// The opponents: Platinum's party of made Pokémon against ours, made from opponentMons at their levels
static int gOppObservable;
static void compare_opponents(void) {
    BattleCastle *c = gPlatCastle;
    if (!gOppObservable) {
        return;
    }
    CHECK(Party_GetCurrentCount(c->opponentsParty) == gOur.opponentCount, "opponent count %d/%d",
          Party_GetCurrentCount(c->opponentsParty), gOur.opponentCount);
    for (int i = 0; i < gOur.opponentCount && i < 4; i++) {
        Pokemon *p = Party_GetPokemonBySlotIndex(c->opponentsParty, i);
        PlatCastleMon *o = &gOur.opponentMons[i];
        CHECK(p->species == o->species && p->item == o->item && p->personality == o->personality &&
                  p->level == PlatCastle_GetOpponentLevel(&gOur, (u8)i) && !memcmp(p->moves, o->moves, 8) &&
                  p->ability == o->ability && p->friendship == o->friendship && (p->ivs & 31) == o->ivs &&
                  !memcmp(p->evs, o->evs, 6),
              "opponent %d: species %d/%d level %d/%d personality %08x/%08x", i, p->species, o->species, p->level,
              PlatCastle_GetOpponentLevel(&gOur, (u8)i), p->personality, o->personality);
    }
}

static void compare_state(void) {
    BattleCastle *c = gPlatCastle;
    PlatCastle *o = &gOur;
    BattleCastleSave *ps = &gPlatSave.frontier.castleSave;
    PlatCastleSave *os = &gOurSave;
    CHECK(gPlatLCRNG == o->lcrng, "random state %08x / %08x", gPlatLCRNG, o->lcrng);
    if (c != NULL) {
        CHECK(c->challengeType == o->challengeType && c->currentBattle == o->currentBattle && c->monFainted == o->monFainted &&
                  c->seenCastleValetIntro == o->seenCastleValetIntro,
              "type/battle/fainted/valet %d %d %d %d / %d %d %d %d", c->challengeType, c->currentBattle, c->monFainted,
              c->seenCastleValetIntro, o->challengeType, o->currentBattle, o->monFainted, o->seenCastleValetIntro);
        CHECK(c->currentStreak == o->currentStreak && c->currentRound == o->currentRound && c->saveStreak == o->saveStreak,
              "streak/round/saveStreak %d %d %d / %d %d %d", c->currentStreak, c->currentRound, c->saveStreak, o->currentStreak,
              o->currentRound, o->saveStreak);
        CHECK(c->wonBattle == o->wonBattle && c->initialCP == o->initialCP && c->newCP == o->newCP, "won/initialCP/newCP");
        CHECK(!memcmp(c->partySlots, o->partySlots, 3) && !memcmp(c->savedHeldItems, o->savedHeldItems, 6), "slots, held items");
        CHECK(!memcmp(c->trainerIDs, o->trainerIDs, sizeof(o->trainerIDs)), "trainer ids");
        CHECK(!memcmp(c->monSetIDs, o->monSetIDs, sizeof(o->monSetIDs)) && !memcmp(c->opponentMonIVs, o->opponentMonIVs, 4) &&
                  !memcmp(c->opponentMonPersonalities, o->opponentMonPersonalities, 16),
              "the opponents' sets, IVs, personalities");
        for (int i = 0; i < 4; i++) {
            FrontierPokemon *pm = &c->opponentMons[i];
            PlatCastleMon *om = &o->opponentMons[i];
            CHECK(pm->species == om->species && pm->form == om->form && pm->item == om->item && !memcmp(pm->moves, om->moves, 8) &&
                      pm->otID == om->otID && pm->personality == om->personality && pm->hpIV == om->ivs &&
                      pm->spDefIV == om->ivs && !memcmp(pm->evList, om->evs, 6) && pm->ability == om->ability &&
                      pm->friendship == om->friendship,
                  "opponentMons[%d]: species %d/%d personality %08x/%08x", i, pm->species, om->species, pm->personality,
                  om->personality);
        }
        CHECK(!memcmp(c->appIdentityUnlocked, o->appIdentityUnlocked, 4) && !memcmp(c->levelAdjustments, o->levelAdjustments, 4) &&
                  !memcmp(c->appStatsUnlocked, o->appStatsUnlocked, 4) && !memcmp(c->appMovesUnlocked, o->appMovesUnlocked, 4),
              "the information bought");
        CHECK(!memcmp(c->startingPP, o->startingPP, sizeof(o->startingPP)), "starting PP");
        CHECK(Party_GetCurrentCount(c->playersParty) == o->playerCount, "party count %d/%d",
              Party_GetCurrentCount(c->playersParty), o->playerCount);
        for (int i = 0; i < o->playerCount; i++) {
            compare_mon(Party_GetPokemonBySlotIndex(c->playersParty, i), &gOurParty[i], "castle party", i);
        }
        compare_opponents();
    }
    CHECK(ps->challengeType == os->challengeType && ps->didSave == os->didSave && ps->currentBattleNum == os->currentBattleNum &&
              !memcmp(ps->partySlots, os->partySlots, 3) && !memcmp(ps->trainerIDs, os->trainerIDs, sizeof(os->trainerIDs)) &&
              !memcmp(ps->monHP, os->monHP, sizeof(os->monHP)) && !memcmp(ps->monPP, os->monPP, sizeof(os->monPP)) &&
              !memcmp(ps->monStatus, os->monStatus, sizeof(os->monStatus)) &&
              !memcmp(ps->heldItems, os->heldItems, sizeof(os->heldItems)) &&
              !memcmp(ps->monSetIDs, os->monSetIDs, sizeof(os->monSetIDs)),
          "the saved challenge");
    CHECK(!memcmp(gPlatSave.frontier.stats.soloStats, gOurRec.stats, 2 * 112), "the records");
    CHECK(gPlatSave.frontier.castle.persistentSave.streakActiveFlags == gOurRec.streakFlags &&
              gPlatSave.frontier.castle.persistentSave.haveHeardIntro == gOurRec.heardIntro,
          "streak flags %x/%x, intro heard %d/%d", gPlatSave.frontier.castle.persistentSave.streakActiveFlags,
          gOurRec.streakFlags, gPlatSave.frontier.castle.persistentSave.haveHeardIntro, gOurRec.heardIntro);
}

// ------------------------------------------------------------------ the scene script's steps, both sides
static u16 both_fn(int fn, int arg1, int arg2, const char *where) {
    u16 a, b = 0xbeef;
    gWhere = where;
    if (fn == BC_FUNC_PREP_FOR_NEXT_BATTLE) {
        gOppObservable = 0;             // (Platinum's opponents keep their levels until the next ones are made; nothing shows them)
    }
    a = plat_fn(fn, arg1, arg2);
    if (PlatCastle_Function(&gOur, &gOurSave, &gOurRec, (u8)fn, (u8)arg1, (u8)arg2, &b)) {
        CHECK(a == b, "function %d (%d, %d): %d / %d", fn, arg1, arg2, a, b);
    }                                   // (else the game's: castle_field.c)
    compare_state();
    return a;
}

static void start(int resuming, int type, int s1, int s2, int s3) {
    u32 seed = pick(0xffffffff) ^ (pick(0x10000) << 16);
    gWhere = resuming ? "resume" : "init";
    gPlatLCRNG = seed;
    gOur.lcrng = seed;
    gVars[1] = 0;
    plat_cmd(FrontierScrCmd_InitBattleCastle, 6, resuming, type, s1, s2, s3, 1);
    PlatCastle_Init(&gOur, &gOurSave, &gOurRec, (u16)resuming, (u8)type, (u8)s1, (u8)s2, (u8)s3);
    compare_state();
    gWhere = "load the round";
    plat_cmd(FrontierScrCmd_LoadTrainersForRound, 1, resuming);
    PlatCastle_LoadTrainersForRound(&gOur, &gOurSave, (u16)resuming);
    gOppObservable = 0;
    compare_state();
}

static void setup_first(void) {
    gWhere = "first opponent";
    plat_cmd(FrontierScrCmd_BattleCastle_SetupFirstOpponent, 0);
    PlatCastle_SetupFirstOpponentsParty(&gOur);
    gOppObservable = 1;
    compare_state();
}

static void setup_next(void) {
    gWhere = "next opponent";
    plat_cmd(FrontierScrCmd_BattleCastle_SetupNextOpponent, 0);
    PlatCastle_SetupNextOpponentsParty(&gOur);
    gOppObservable = 1;
    compare_state();
}

// ------------------------------------------------------------------ the screens: Platinum's state machines, our Ask and Buy
enum { SELF_SELECT_MON, SELF_MON_OPTIONS, SELF_HEAL_MENU, SELF_HEAL_YES_NO, SELF_RANK_HEAL_YES_NO, SELF_UPDATE_RANK_HEAL,
       SELF_WAIT_RANK_HEAL, SELF_WAIT_HEAL_FAIL, SELF_RENTAL_MENU, SELF_SELECT_ITEM, SELF_SELECT_ITEM_YES_NO,
       SELF_RANK_RENT_YES_NO, SELF_UPDATE_RANK_RENT, SELF_WAIT_RANK_RENT, SELF_WAIT_CANT_OPEN, SELF_WAIT_RENT_FAIL,
       SELF_SWITCH_PROMPT, SELF_SWITCH_YES_NO, SELF_UPDATE_PURCHASE, SELF_WAIT_RETURN, SELF_SHOW_SUMMARY, SELF_SHOW_MOVES };
enum { OPP_INIT, OPP_SELECT_MON, OPP_MON_OPTIONS, OPP_REVEAL_YES_NO, OPP_LEVEL_MENU, OPP_LEVEL_YES_NO, OPP_SUMMARY_MENU,
       OPP_STATS_YES_NO, OPP_MOVES_YES_NO, OPP_RANK_YES_NO, OPP_WAIT_RANK_MSG, OPP_UPDATE_OPTION, OPP_UPDATE_SUMMARY,
       OPP_SHOW_SUMMARY, OPP_WAIT_RETURN_SUMMARY, OPP_WAIT_RETURN, OPP_SHOW_STATS, OPP_SHOW_MOVES };

// One purchase on Platinum's self screen: from the Pokémon's selection, into its menus, the answers, and back out
static void plat_self(BattleCastleSelfApp *app, int kind, int slot, int row, int yes1, int yes2) {
    int phase = 0;
    for (int steps = 0; steps < 100; steps++) {
        int s = Glue_SelfSubState(app);
        gSystem.pressedKeys = 0;
        gListInput = (u32)MENU_NOTHING_CHOSEN;
        gMenuInput = (u32)MENU_NOTHING_CHOSEN;
        gListPos = 0;
        switch (s) {
        case SELF_SELECT_MON:
            if (phase) {
                return;
            }
            Glue_SelfSetSlot(app, slot);
            gSystem.pressedKeys = PAD_BUTTON_A;
            break;
        case SELF_MON_OPTIONS:
            gListInput = phase ? (u32)MENU_CANCEL : (kind <= PLATCASTLE_BUY_RANK_HEALING ? 0 : 5);
            break;
        case SELF_HEAL_MENU:
            gListInput = phase ? (u32)MENU_CANCEL : (u32)(kind + 1);
            gListPos = phase ? 4 : (u16)kind;
            break;
        case SELF_RENTAL_MENU:
            gListInput = phase ? (u32)MENU_CANCEL : (u32)(6 + kind - PLATCASTLE_BUY_BERRY);
            gListPos = phase ? 3 : (u16)(kind - PLATCASTLE_BUY_BERRY);
            break;
        case SELF_SELECT_ITEM:
            gListInput = phase ? (u32)MENU_CANCEL : (u32)row;
            gListPos = (u16)row;
            break;
        case SELF_HEAL_YES_NO:
        case SELF_RANK_HEAL_YES_NO:
        case SELF_SELECT_ITEM_YES_NO:
        case SELF_RANK_RENT_YES_NO:
            gMenuInput = yes1 ? MENU_YES : MENU_NO;
            phase = 1;
            break;
        case SELF_SWITCH_YES_NO:
            gMenuInput = yes2 ? MENU_YES : MENU_NO;
            phase = 1;
            break;
        case SELF_WAIT_RANK_HEAL:
        case SELF_WAIT_HEAL_FAIL:
        case SELF_WAIT_RANK_RENT:
        case SELF_WAIT_CANT_OPEN:
        case SELF_WAIT_RENT_FAIL:
        case SELF_SWITCH_PROMPT:
        case SELF_WAIT_RETURN:
            gSystem.pressedKeys = PAD_BUTTON_A;
            phase = 1;
            break;
        }
        Self_State_MainAppFlow(app);
        if (!phase && (s == SELF_HEAL_MENU || s == SELF_RENTAL_MENU) && Glue_SelfSubState(app) == s) {
            phase = 1;                  // (a rank already at the top: Platinum buzzes and stays)
        }
    }
    CHECK(0, "the self screen didn't come back (kind %d)", kind);
}

static void plat_opp(BattleCastleOpponentApp *app, int kind, int slot, int yes1) {
    int phase = 0;
    for (int steps = 0; steps < 100; steps++) {
        int s = Glue_OppSubState(app);
        gSystem.pressedKeys = 0;
        gListInput = (u32)MENU_NOTHING_CHOSEN;
        gMenuInput = (u32)MENU_NOTHING_CHOSEN;
        gListPos = 0;
        switch (s) {
        case OPP_SELECT_MON:
            if (phase) {
                return;
            }
            Glue_OppSetSlot(app, slot);
            gSystem.pressedKeys = PAD_BUTTON_A;
            break;
        case OPP_MON_OPTIONS:
            gListInput = phase ? (u32)MENU_CANCEL :
                         kind == PLATCASTLE_BUY_IDENTIFY ? 0 :
                         (kind == PLATCASTLE_BUY_LEVEL_UP || kind == PLATCASTLE_BUY_LEVEL_DOWN) ? 1 : 2;
            break;
        case OPP_LEVEL_MENU:
            gMenuInput = phase ? 2 : (kind == PLATCASTLE_BUY_LEVEL_UP ? 0 : 1);
            break;
        case OPP_SUMMARY_MENU:
            gListInput = phase ? (u32)MENU_CANCEL : (u32)(3 + kind - PLATCASTLE_BUY_STATS);
            gListPos = phase ? 3 : (u16)(kind - PLATCASTLE_BUY_STATS);
            break;
        case OPP_REVEAL_YES_NO:
        case OPP_LEVEL_YES_NO:
        case OPP_STATS_YES_NO:
        case OPP_MOVES_YES_NO:
        case OPP_RANK_YES_NO:
            gMenuInput = yes1 ? MENU_YES : MENU_NO;
            phase = 1;
            break;
        case OPP_WAIT_RANK_MSG:
        case OPP_WAIT_RETURN_SUMMARY:
        case OPP_WAIT_RETURN:
        case OPP_SHOW_STATS:
        case OPP_SHOW_MOVES:
            gSystem.pressedKeys = PAD_BUTTON_A;
            phase = 1;
            break;
        }
        Opp_State_MainAppFlow(app);
        if (!phase && s == OPP_SUMMARY_MENU && Glue_OppSubState(app) == s) {
            phase = 1;                  // (the information rank at the top: a buzz)
        }
    }
    CHECK(0, "the opponent screen didn't come back (kind %d)", kind);
}

// What Platinum's screens print for our answers (the lines of battle_castle_self_app and battle_castle_opponent_app)
static int gExp[8], gExpCount;
static s32 gExpNumber;
static void expect(int line) {
    gExp[gExpCount++] = line;
}

static int self_rank_msg(int rankType, int oldRank) {
    static const int msgs[2][3] = { { 0, BattleCastleSelfApp_Text_GainedAbilityToRestorePP,
                                      BattleCastleSelfApp_Text_GainedAbilityToRestoreHPAndPP },
                                    { 0, BattleCastleSelfApp_Text_GainedAbilityToRentItems,
                                      BattleCastleSelfApp_Text_ExpandedItemRentals } };
    return msgs[rankType][oldRank];
}

// Our side of one purchase: Ask, the same answers, Buy, the messages Platinum shows for each answer
static void our_purchase(int kind, int slot, int row, int yes1, int yes2) {
    u16 cost = 0;
    u32 r, b;
    u8 rank;
    gExpCount = 0;
    gExpNumber = -1;
    switch (kind) {
    case PLATCASTLE_BUY_HEAL_HP:
    case PLATCASTLE_BUY_HEAL_PP:
    case PLATCASTLE_BUY_HEAL_ALL:
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, 0, &cost);
        if (r == PLATCASTLE_RESULT_RANK_TOO_LOW) {
            expect(BattleCastleSelfApp_Text_HealRankTooLow);
            return;
        }
        expect(BattleCastleSelfApp_Text_WillCostCP);
        gExpNumber = cost;
        if (!yes1) {
            return;
        }
        b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, 0);
        expect(b == PLATCASTLE_RESULT_RANK_TOO_LOW ? BattleCastleSelfApp_Text_HealRankTooLow :
               b == PLATCASTLE_RESULT_NOT_ENOUGH_CP ? BattleCastleSelfApp_Text_NotEnoughCP :
               b == PLATCASTLE_RESULT_NO_BENEFIT ? BattleCastleSelfApp_Text_NoBenefit :
                                                    BattleCastleSelfApp_Text_HPWillBeRestored + (kind - PLATCASTLE_BUY_HEAL_HP));
        gStat[N_BOUGHT] += b == PLATCASTLE_RESULT_DONE;
        return;
    case PLATCASTLE_BUY_RANK_HEALING:
    case PLATCASTLE_BUY_RANK_RENTALS:
        rank = PlatCastle_GetRank(&gOurRec, gOur.challengeType, kind == PLATCASTLE_BUY_RANK_HEALING ? 0 : 1);
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, 0, &cost);
        if (r == PLATCASTLE_RESULT_MAX_RANK) {
            return;
        }
        expect(BattleCastleSelfApp_Text_RankUpForCP);
        gExpNumber = cost;
        if (!yes1) {
            return;
        }
        b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, 0);
        expect(b == PLATCASTLE_RESULT_NOT_ENOUGH_CP ? BattleCastleSelfApp_Text_NotEnoughCP2 :
                                                       self_rank_msg(kind == PLATCASTLE_BUY_RANK_HEALING ? 0 : 1, rank));
        gStat[N_RANKUPS] += b == PLATCASTLE_RESULT_DONE;
        return;
    case PLATCASTLE_BUY_BERRY:
    case PLATCASTLE_BUY_ITEM:
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, 0xffff, &cost);
        if (r == PLATCASTLE_RESULT_RANK_TOO_LOW) {
            expect(BattleCastleSelfApp_Text_RentalRankTooLow);
            return;
        }
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, (u16)row, &cost);
        expect(BattleCastleSelfApp_Text_WillCostCP);
        gExpNumber = cost;
        if (!yes1) {
            return;
        }
        b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, (u16)row);
        if (b == PLATCASTLE_RESULT_HOLDING_ITEM) {
            expect(BattleCastleSelfApp_Text_AlreadyHoldingItem);
            expect(BattleCastleSelfApp_Text_WantToSwitchItems);
            if (!yes2) {
                return;
            }
            b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, (u16)(row | PLATCASTLE_BUY_SWITCH));
        }
        expect(b == PLATCASTLE_RESULT_NOT_ENOUGH_CP ? BattleCastleSelfApp_Text_NotEnoughCP : BattleCastleSelfApp_Text_ItemGivenToMon);
        gStat[N_BOUGHT] += b == PLATCASTLE_RESULT_DONE;
        return;
    case PLATCASTLE_BUY_IDENTIFY:
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, 0, &cost);
        if (r == PLATCASTLE_RESULT_KNOWN) {
            expect(BattleCastleOpponentApp_Text_IdentityRevealed);
            return;
        }
        expect(BattleCastleOpponentApp_Text_IdentifyForCP);
        gExpNumber = cost;
        if (!yes1) {
            return;
        }
        b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, 0);
        expect(b == PLATCASTLE_RESULT_NOT_ENOUGH_CP ? BattleCastleOpponentApp_Text_NotEnoughCP3 :
                                                       BattleCastleOpponentApp_Text_IdentityRevealed);
        gStat[N_BOUGHT] += b == PLATCASTLE_RESULT_DONE;
        return;
    case PLATCASTLE_BUY_LEVEL_UP:
    case PLATCASTLE_BUY_LEVEL_DOWN:
        expect(BattleCastleOpponentApp_Text_MayChangeLevel);
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, 0, &cost);
        if (r == PLATCASTLE_RESULT_CANT_GO_HIGHER || r == PLATCASTLE_RESULT_CANT_GO_LOWER) {
            expect(r == PLATCASTLE_RESULT_CANT_GO_HIGHER ? BattleCastleOpponentApp_Text_LevelCantGoHigher :
                                                           BattleCastleOpponentApp_Text_LevelCantGoLower);
            return;
        }
        expect(BattleCastleOpponentApp_Text_WillCostCP);
        gExpNumber = cost;
        if (!yes1) {
            return;
        }
        b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, 0);
        expect(b == PLATCASTLE_RESULT_NOT_ENOUGH_CP ? BattleCastleOpponentApp_Text_NotEnoughCP3 :
               kind == PLATCASTLE_BUY_LEVEL_UP ? BattleCastleOpponentApp_Text_LevelBoostedBy5 :
                                                 BattleCastleOpponentApp_Text_LevelLoweredBy5);
        gStat[N_BOUGHT] += b == PLATCASTLE_RESULT_DONE;
        return;
    case PLATCASTLE_BUY_STATS:
    case PLATCASTLE_BUY_MOVES:
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, 0, &cost);
        if (r == PLATCASTLE_RESULT_RANK_TOO_LOW) {
            expect(BattleCastleOpponentApp_Text_TooLowForMoveList);
            return;
        }
        if (r == PLATCASTLE_RESULT_KNOWN) {
            return;
        }
        expect(kind == PLATCASTLE_BUY_STATS ? BattleCastleOpponentApp_Text_CanCheckStats : BattleCastleOpponentApp_Text_MayCheckMoveList);
        gExpNumber = cost;
        if (!yes1) {
            return;
        }
        b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, 0);
        expect(b == PLATCASTLE_RESULT_NOT_ENOUGH_CP ?
                   (kind == PLATCASTLE_BUY_STATS ? BattleCastleOpponentApp_Text_NotEnoughCP : BattleCastleOpponentApp_Text_NotEnoughCP2) :
                   (kind == PLATCASTLE_BUY_STATS ? BattleCastleOpponentApp_Text_SummaryBought : BattleCastleOpponentApp_Text_MoveListBought));
        gStat[N_BOUGHT] += b == PLATCASTLE_RESULT_DONE;
        return;
    case PLATCASTLE_BUY_RANK_INFO:
        r = PlatCastle_Ask(&gOur, &gOurRec, kind, (u8)slot, 0, &cost);
        if (r == PLATCASTLE_RESULT_MAX_RANK) {
            return;
        }
        expect(BattleCastleOpponentApp_Text_RankUpForCP);
        gExpNumber = cost;
        if (!yes1) {
            return;
        }
        b = PlatCastle_Buy(&gOur, &gOurRec, kind, (u8)slot, 0);
        expect(b == PLATCASTLE_RESULT_NOT_ENOUGH_CP ? BattleCastleOpponentApp_Text_NotEnoughCP2 :
                                                       BattleCastleOpponentApp_Text_GainedMoveListPurchasePower);
        gStat[N_RANKUPS] += b == PLATCASTLE_RESULT_DONE;
        return;
    }
}

static long gCover[PLATCASTLE_BUY_KINDS][100];  // purchases by kind and the last line Platinum's screen showed (the outcome)
static void compare_messages(int kind) {
    gCover[kind][gMsgCount ? gMsgLog[gMsgCount - 1] % 100 : 99]++;
    CHECK(gMsgCount == gExpCount && !memcmp(gMsgLog, gExp, sizeof(int) * gExpCount), "kind %d: %d messages %d %d %d / %d: %d %d %d",
          kind, gMsgCount, gMsgLog[0], gMsgLog[1], gMsgLog[2], gExpCount, gExp[0], gExp[1], gExp[2]);
    if (gExpNumber >= 0) {
        CHECK(gTemplateNumber0 == gExpNumber, "kind %d: the cost %d / %d", kind, gTemplateNumber0, gExpNumber);
    }
}

// A visit to a screen: several purchases, then Platinum's results back into the castle (StoreBattleCastleAppResult)
static void screen(int self) {
    BattleCastleAppArgs *args = calloc(1, sizeof(BattleCastleAppArgs));
    void *app;
    int n = 1 + pick(4);
    args->saveData = &gPlatSave;
    Plat_SetupAppArgs(args, gPlatCastle);
    app = self ? (void *)Glue_NewSelfApp(&gPlatSave, args) : (void *)Glue_NewOppApp(&gPlatSave, args);
    gStat[self ? N_SELF : N_OPP]++;
    for (int k = 0; k < n; k++) {
        int kind, slot = pick(3), row = 0, yes1 = pick(8) != 0, yes2 = pick(3) != 0;
        if (self) {
            kind = pick(PLATCASTLE_BUY_RANK_RENTALS + 1);
            if (kind == PLATCASTLE_BUY_BERRY || kind == PLATCASTLE_BUY_ITEM) {
                row = pick(PlatCastle_RentalCount(&gOurRec, gOur.challengeType, kind == PLATCASTLE_BUY_ITEM));
            }
        } else {
            kind = PLATCASTLE_BUY_IDENTIFY + pick(PLATCASTLE_BUY_RANK_INFO - PLATCASTLE_BUY_IDENTIFY + 1);
        }
        gWhere = self ? "the self screen" : "the opponent screen";
        gMsgCount = 0;
        gTemplateNumber0 = -1;
        if (self) {
            plat_self(app, kind, slot, row, yes1, yes2);
        } else {
            plat_opp(app, kind, slot, yes1);
        }
        our_purchase(kind, slot, row, yes1, yes2);
        compare_messages(kind);
        if (!self) {                    // (the screen buys into its arguments; StoreAppResults copies them into the castle)
            CHECK(!memcmp(args->identityUnlocked, gOur.appIdentityUnlocked, 4) && !memcmp(args->levelAdjustments, gOur.levelAdjustments, 4) &&
                      !memcmp(args->statsUnlocked, gOur.appStatsUnlocked, 4) && !memcmp(args->movesUnlocked, gOur.appMovesUnlocked, 4),
                  "kind %d: the information bought", kind);
            for (int i = 0; i < gOur.opponentCount; i++) {
                CHECK(Party_GetPokemonBySlotIndex(gPlatCastle->opponentsParty, i)->level == PlatCastle_GetOpponentLevel(&gOur, (u8)i),
                      "kind %d: opponent %d's level", kind, i);
            }
        }
        CHECK(!memcmp(gPlatSave.frontier.stats.soloStats, gOurRec.stats, 2 * 112), "kind %d: the records (CP, spent, ranks)", kind);
        for (int i = 0; i < gOur.playerCount; i++) {
            compare_mon(Party_GetPokemonBySlotIndex(gPlatCastle->playersParty, i), &gOurParty[i], "after a purchase", i);
        }
    }
    free(app);
    Plat_StoreAppResult(args);          // (frees args)
    gOur.selectedAppSlot = gPlatCastle->selectedAppSlots[0];
    gWhere = "after the screen";
    compare_state();
}

// ------------------------------------------------------------------ the battle
// The setup (BattleCastle_SetupBattle) against ours, an outcome the harness draws, the cleanup on both sides
static int battle(void) {
    FieldBattleDTO *dto;
    int won;
    gWhere = "the battle";
    gLastDTO = NULL;
    plat_cmd(FrontierScrCmd_BattleCastle_StartBattle, 0);
    dto = gLastDTO;
    gStat[N_BATTLES]++;
    // the setup: the player's party as it is, the opponents' at their levels (healed), the Trainer, the AI
    CHECK(Party_GetCurrentCount(dto->parties[BATTLER_PLAYER_1]) == gOur.playerCount, "the battle's party count");
    for (int i = 0; i < gOur.playerCount; i++) {
        compare_mon(Party_GetPokemonBySlotIndex(dto->parties[BATTLER_PLAYER_1], i), &gOurParty[i], "battle party", i);
    }
    for (int i = 0; i < PlatCastle_GetOpponentPartySize(gOur.challengeType, FALSE); i++) {
        Pokemon *p = Party_GetPokemonBySlotIndex(dto->parties[BATTLER_ENEMY_1], i);
        CHECK(p->species == gOur.opponentMons[i].species && p->level == PlatCastle_GetOpponentLevel(&gOur, (u8)i) &&
                  p->hp == p->maxHp, "battle opponent %d", i);
    }
    CHECK(dto->trainerIDs[BATTLER_ENEMY_1] == gOur.trainerIDs[gOur.currentBattle], "the Trainer %u / %d",
          dto->trainerIDs[BATTLER_ENEMY_1], gOur.trainerIDs[gOur.currentBattle]);
    CHECK(dto->trainer[BATTLER_ENEMY_1].header.aiMask == PlatCastle_GetAIMask(&gOur), "the AI %d / %d",
          dto->trainer[BATTLER_ENEMY_1].header.aiMask, PlatCastle_GetAIMask(&gOur));
    if (gOur.trainerIDs[gOur.currentBattle] >= PLATCASTLE_DARACH_SILVER) {
        gStat[N_DARACH]++;
    }
    // the outcome
    won = pick(100) < 88;
    for (int i = 0; i < gOur.playerCount; i++) {
        Pokemon *p = Party_GetPokemonBySlotIndex(dto->parties[BATTLER_PLAYER_1], i);
        Pokemon *o = &gOurParty[i];
        int lose = pick(10) == 0 ? p->hp : (int)pick(p->hp + 1) * pick(2);
        p->hp -= lose;
        if (p->hp == 0) {
            p->status = 0;
            gStat[N_FAINTED]++;
        } else if (pick(5) == 0) {
            p->status = 1 + pick(7);
        }
        for (int j = 0; j < 4; j++) {
            if (p->moves[j]) {
                p->pp[j] -= pick(3) ? pick(p->pp[j] + 1) / 2 : 0;
            }
        }
        if (p->item && pick(4) == 0) {
            p->item = 0;
        }
        o->hp = p->hp;
        o->status = p->status;
        memcpy(o->pp, p->pp, 4);
        o->item = p->item;
    }
    dto->resultMask = won ? 1 : 2;
    plat_cmd(FrontierScrCmd_BattleCastle_CleanupBattle, 0);
    gOur.wonBattle = won;               // (castle_field.c's cleanup: the party back from the battle, won or not)
    compare_state();
    gVars[8] = 0xbeef;
    plat_cmd(FrontierScrCmd_BattleCastle_CheckWonBattle, 1, 8);
    CHECK(gVars[8] == won, "won %d / %d", gVars[8], won);
    return won;
}

// After a won battle or a pass, as the scene script goes (_10CA, _10DA, _110F; _1084, _122A)
static void next_battle(int passed) {
    both_fn(BC_FUNC_INCREMENT_CURRENT_BATTLE, 1, 0, "the next battle");
    both_fn(BC_FUNC_INCREMENT_CURRENT_STREAK, 0, 0, "the streak");
    if (!passed) {
        u16 cp = both_fn(BC_FUNC_GET_CP_FROM_BATTLE, 0, 0, "the CP earned");
        gStat[N_CP_EARNED] += cp;
    }
    both_fn(BC_FUNC_PREP_FOR_NEXT_BATTLE, 0, 0, "the next battle's preparation");
}

// The pass (_0A1C .. _0AB8): the CP checked, 50 spent
static int pass(void) {
    u16 cost;
    u32 r;
    gWhere = "the pass";
    gVars[8] = 0xbeef;
    plat_cmd(FrontierScrCmd_GetCurrentCastlePoints, 2, gOur.challengeType, 8);
    CHECK(gVars[8] == PlatCastle_GetCurrentCP(&gOurRec, gOur.challengeType), "the CP %d", gVars[8]);
    r = PlatCastle_Ask(&gOur, &gOurRec, PLATCASTLE_BUY_PASS, 0, 0, &cost);
    CHECK(r == PLATCASTLE_RESULT_CONFIRM && cost == 50, "the pass's question");
    r = PlatCastle_Buy(&gOur, &gOurRec, PLATCASTLE_BUY_PASS, 0, 0);
    CHECK((gVars[8] < 50) == (r == PLATCASTLE_RESULT_NOT_ENOUGH_CP), "the pass's CP check");
    if (gVars[8] < 50) {
        compare_state();
        return 0;
    }
    plat_cmd(FrontierScrCmd_SpendCastlePoints, 2, gOur.challengeType, 50);
    compare_state();
    gStat[N_PASSES]++;
    return 1;
}

// ------------------------------------------------------------------ a challenge, as the scene runs it
// 0 the round ended (won), 1 lost or retired, 2 rested (saved; the caller resumes)
static int challenge(int resuming, int type, int s1, int s2, int s3) {
    int passed = 0;
    start(resuming, type, s1, s2, s3);
    if (!resuming) {
        gStat[N_CHALLENGES]++;
    }
    if (both_fn(BC_FUNC_GET_CURRENT_BATTLE, 0, 0, "the current battle") == 0) {
        setup_first();
        both_fn(BC_FUNC_CHECK_HAVE_HEARD_DARACHS_INTRO, 0, 0, "Darach's intro");
    } else {
        goto menu_after;                // (_1349: the menu after a battle, VAR_0x8003 = 1)
    }
    for (;;) {
        // the castle's menu (_0706): the screens, the pass, the battle
        both_fn(BC_FUNC_GET_CURRENT_ROUND, 0, 0, "the menu's round");
        for (;;) {
            int round = gOur.currentRound, choice = pick(10);
            u16 next = both_fn(BC_FUNC_GET_NEXT_BATTLE_TYPE, 0, 0, "the menu's next battle");
            if (choice < 3) {
                both_fn(BC_FUNC_UNK_32, 1, 0, "the menu");
                both_fn(BC_FUNC_UNK_34, 0, 0, "the menu");
                both_fn(BC_FUNC_UNK_31, 0, 0, "the menu");
                screen(1);
            } else if (choice < 6) {
                both_fn(BC_FUNC_UNK_32, 2, 0, "the menu");
                both_fn(BC_FUNC_UNK_31, 0, 0, "the menu");
                screen(0);
            } else if (choice == 6 && round >= 3 && next == FRONTIER_NEXT_BATTLE_NORMAL) {
                if (pass()) {
                    passed = 1;
                    break;
                }
            } else {
                passed = 0;
                both_fn(BC_FUNC_UNK_32, 4, 0, "the menu");
                both_fn(BC_FUNC_UNK_31, 0, 0, "the menu");
                break;
            }
        }
        if (passed) {
            next_battle(1);
        } else {
            u16 next = both_fn(BC_FUNC_GET_NEXT_BATTLE_TYPE, 0, 0, "the battle room");
            both_fn(BC_FUNC_GET_CURRENT_STREAK, 0, 0, "the battle room");
            if (next == FRONTIER_NEXT_BATTLE_NORMAL) {
                both_fn(BC_FUNC_GET_OPPONENT_OBJECT_ID, 0, 0, "the opponent's look");
            }
            both_fn(BC_FUNC_LOAD_TRAINERS, 0, 0, "the Trainers");
            if (!battle()) {
                gStat[N_LOSSES]++;
                both_fn(BC_FUNC_SAVE_ON_LOSS, 0, 0, "the loss");
                return 1;
            }
            gStat[N_WINS]++;
            both_fn(BC_FUNC_GET_CURRENT_STREAK, 0, 0, "after the battle");
            next_battle(0);
        }
        if (both_fn(BC_FUNC_GET_CURRENT_BATTLE, 0, 0, "the round") == CASTLE_BATTLES_PER_ROUND) {
            both_fn(BC_FUNC_SAVE_ON_COMPLETING_ROUND, 0, 0, "the round's end");
            gStat[N_BP] += both_fn(BC_FUNC_GET_EARNED_BP, 0, 0, "the BP");
            gStat[N_ROUNDS]++;
            return 0;
        }
        if (!passed) {
            both_fn(BC_FUNC_CHECK_IF_MON_FAINTED, 0, 0, "the fainted");
        }
    menu_after:
        // _1349: Darach's approach, then continue, rest or retire
        if (both_fn(BC_FUNC_GET_NEXT_BATTLE_TYPE, 0, 0, "Darach next?") != FRONTIER_NEXT_BATTLE_NORMAL && !resuming) {
            both_fn(BC_FUNC_CHECK_SEEN_VALET_INTRO, 0, 0, "Darach's approach");
        }
        resuming = 0;
        both_fn(BC_FUNC_GET_CURRENT_STREAK, 0, 0, "the menu after");
        both_fn(BC_FUNC_GET_CURRENT_BATTLE, 0, 0, "the menu after");
        {
            int c = pick(20);
            if (c == 0) {
                gStat[N_RETIRES]++;
                both_fn(BC_FUNC_SAVE_ON_LOSS, 0, 0, "the retire");
                return 1;
            }
            if (c == 1) {
                gStat[N_RESTS]++;
                both_fn(BC_FUNC_QUICKSAVE, 0, 0, "the rest");
                gWhere = "the rest";
                plat_cmd(FrontierScrCmd_FreeBattleCastle, 0);
                gPlatCastle = NULL;
                return 2;
            }
        }
        setup_next();
    }
}

// ------------------------------------------------------------------ the rental lists (self_app.c's own tables, file-scope there)
extern const u16 sItemsForRent[27], sItemPrices[27], sBerriesForRent[32], sBerryPrices[32], sItemsAvailableByRank[3],
    sBerriesAvailableByRank[3];
static void check_tables(void) {
    OurRecords r;
    gWhere = "the rental lists";
    for (int i = 0; i < 32; i++) {
        CHECK(PlatCastle_RentalItem(FALSE, (u16)i) == sBerriesForRent[i] && PlatCastle_RentalPrice(FALSE, (u16)i) == sBerryPrices[i],
              "Berry %d", i);
        if (i < 27) {
            CHECK(PlatCastle_RentalItem(TRUE, (u16)i) == sItemsForRent[i] && PlatCastle_RentalPrice(TRUE, (u16)i) == sItemPrices[i],
                  "item %d", i);
        }
    }
    for (int type = 0; type < 2; type++) {
        for (int rank = 1; rank <= 3; rank++) {
            memset(&r, 0, sizeof(r));
            r.stats[PlatCastle_StatIndex((u8)type, PLATCASTLE_STAT_RANK + PLATCASTLE_RANK_RENTALS)] = (u16)rank;
            CHECK(PlatCastle_RentalCount(&r, (u8)type, FALSE) == sBerriesAvailableByRank[rank - 1] &&
                      PlatCastle_RentalCount(&r, (u8)type, TRUE) == sItemsAvailableByRank[rank - 1],
                  "the rentals at rank %d", rank);
        }
    }
}

// ------------------------------------------------------------------ a seed: a save, a party, challenges
static void random_mon(Pokemon *m) {
    memset(m, 0, sizeof(*m));
    FrontierPokemonBase *s = &gSets[1 + pick(gSetCount - 1)];
    m->species = s->species;
    m->exp = Pokemon_GetSpeciesBaseExpAt(m->species, 20 + pick(81)) + pick(50);
    m->ivs = pick(0x40000000);
    for (int j = 0; j < 6; j++) {
        m->evs[j] = (u8)pick(256);
    }
    Pokemon_CalcLevelAndStats(m);
    m->hp = m->maxHp;
    for (int j = 0; j < 4; j++) {
        m->moves[j] = pick(5) ? (u16)(1 + pick(466)) : 0;
        m->ppUps[j] = (u8)pick(4);
        m->pp[j] = MoveTable_CalcMaxPP(m->moves[j], m->ppUps[j]);
    }
    if (m->moves[0] == 0) {
        m->moves[0] = 33;
        m->pp[0] = MoveTable_CalcMaxPP(33, m->ppUps[0]);
    }
    m->item = pick(3) ? (u16)pick(470) : 0;
    m->personality = pick(0xffffffff);
}

static void random_records(void) {
    memset(&gPlatSave.frontier, 0, sizeof(gPlatSave.frontier));
    memset(&gOurRec, 0, sizeof(gOurRec));
    memset(&gOurSave, 0, sizeof(gOurSave));
    for (int t = 0; t < 2; t++) {
        u32 base = PLATCASTLE_STAT_SINGLE + t * PLATCASTLE_STAT_STRIDE;
        u16 v[8] = { (u16)pick(60), (u16)pick(60), (u16)(pick(8) ? pick(pick(2) ? 60 : 600) : 9990 + pick(10)), (u16)pick(2000),
                     (u16)pick(500), (u16)(1 + pick(3)), (u16)(1 + pick(3)), (u16)(1 + pick(2)) };
        if (pick(2) == 0) {
            v[1] = (u16)(pick(2) ? 14 + pick(7) : 42 + pick(7));     // (a streak of a round before Darach's)
        }
        for (int i = 0; i < 8; i++) {
            gPlatSave.frontier.stats.soloStats[base + i] = v[i];
            gOurRec.stats[base + i] = v[i];
        }
        if (pick(4)) {
            gPlatSave.frontier.castle.persistentSave.streakActiveFlags |= 1 << t;
            gOurRec.streakFlags |= 1 << t;
        }
    }
    gOurRec.heardIntro = gPlatSave.frontier.castle.persistentSave.haveHeardIntro = (u8)pick(2);
}

static void run_seed(unsigned seed) {
    int type = pick(2), slots[3], n;
    gSeed = seed;
    gRng = seed * 2654435761u + 1;
    random_records();
    memset(&gPlatSave.party, 0, sizeof(Party));
    n = 3 + pick(4);
    for (int i = 0; i < n; i++) {
        random_mon(&gPlatSave.party.mons[i]);
    }
    gPlatSave.party.count = n;
    gOurField = gPlatSave.party;
    slots[0] = pick(n);
    do {
        slots[1] = pick(n);
    } while (slots[1] == slots[0]);
    do {
        slots[2] = pick(n);
    } while (slots[2] == slots[0] || slots[2] == slots[1]);
    gFieldData.saveData = &gPlatSave;
    gScriptMan.frontier = &gFieldData;
    for (int k = 0; k < 4; k++) {               // challenges in a row: a won round goes on with the streak
        int r = challenge(0, type, slots[0], slots[1], slots[2]);
        while (r == 2) {
            r = challenge(1, type, 0, 0, 0);
        }
        if (gPlatCastle) {
            plat_cmd(FrontierScrCmd_FreeBattleCastle, 0);
            gPlatCastle = NULL;
        }
        if (pick(6) == 0) {                     // the lobby's streak deletion
            gWhere = "the lobby's deletion";
            Plat_ClearActiveStreak(&gPlatSave, (u8)type);
            PlatCastle_ClearActiveStreak(&gOurRec, (u8)type);
            compare_state();
        }
        if (pick(3) == 0) {
            type ^= 1;
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "sim SETS PERSONAL [SEEDS]\n");
        return 2;
    }
    load(argv[1], argv[2]);
    check_tables();
    int seeds = argc > 3 ? atoi(argv[3]) : 300;
    for (int s = 0; s < seeds; s++) {
        run_seed((unsigned)s);
    }
    printf("%d seeds: %ld challenges, %ld battles (%ld won, %ld lost, %ld Pokemon fainted), %ld rounds (%ld BP), %ld Darach battles, "
           "%ld passes, %ld rests resumed, %ld retires; screens: %ld self, %ld opponent, %ld purchases made, %ld rank ups; %ld CP "
           "earned\n",
           seeds, gStat[N_CHALLENGES], gStat[N_BATTLES], gStat[N_WINS], gStat[N_LOSSES], gStat[N_FAINTED], gStat[N_ROUNDS],
           gStat[N_BP], gStat[N_DARACH], gStat[N_PASSES], gStat[N_RESTS], gStat[N_RETIRES], gStat[N_SELF], gStat[N_OPP],
           gStat[N_BOUGHT], gStat[N_RANKUPS], gStat[N_CP_EARNED]);
    {
        static const char *kinds[] = { "heal HP", "heal PP", "heal all", "healing rank", "Berry", "item", "rental rank", "identity",
                                       "level +5", "level -5", "stats", "moves", "information rank", "pass" };
        printf("purchases by the line Platinum's screen ended on:\n");
        for (int k = 0; k < PLATCASTLE_BUY_KINDS - 1; k++) {
            printf("  %-16s", kinds[k]);
            for (int m = 0; m < 100; m++) {
                if (gCover[k][m]) {
                    printf(" %d:%ld", m, gCover[k][m]);
                }
            }
            printf("\n");
        }
    }
    printf("%ld checks, %ld different\n", gChecks, gProblems);
    return gProblems ? 1 : 0;
}
