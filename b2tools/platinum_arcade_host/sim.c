// The Battle Arcade's rules, Platinum's own C (plat_arcade.c, plat_app.c, copied by extract.py) against ours (the decomp's
// src/pearlb2/plat_arcade/arcade_rules.c, PearlB2's src/pokebw2/ copy, compiled as it is), with the same random numbers and the
// same choices.
//
//   sim SETS PERSONAL [SEEDS]
//
// SETS: the Frontier's Trainers and sets (platinum_frontier_data.py --sets, from the dump); PERSONAL: Platinum's personal data and
// experience tables (platinum_arcade_data.py --personal).
// Each seed: a save (the records of both challenge types, the streak flags) and a field party, the same on both sides; then
// challenges as the Arcade's scene script runs them (frontier_scripts_battle_arcade.s): Init, the round's Trainers, the first
// opponent, the game board (Platinum's own app, BattleArcadeApp_Init, _Main frame by frame and _Exit, against our Open, Start and
// Tick: the stop touched on a frame the harness picks, the same on both sides, or the 30 seconds), the effect, the battle (its
// setup compared: both parties as they go in, the weather, the AI, the Trainer; then an outcome the harness draws, the same on both
// sides: HP, status, items used up, turns, won or lost), the cleanup, the free BP, the skipped battle, the round's end and its BP,
// the rest and the resume, the retire, the loss. Every field of the arcade, both parties, the save and the records is compared
// after every step, the random state too, and the cursor on every frame the board runs.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "plat_shim.h"
#undef TRUE
#undef FALSE
#undef NELEMS
#define PEARLB2_HOST 1
#include "pearlb2/plat_arcade.h"
#define COUNT(a) (sizeof(a) / sizeof((a)[0]))

// ------------------------------------------------------------------ the data
static FrontierPokemonBase *gSets;
static int gSetCount __attribute__((unused));
static struct {
    u16 cls, count;
    u16 *sets;
} gTrainers[400];
typedef struct {
    u8 base[6], type1, type2, ability1, ability2, growth;
} PersonalEntry;
static PersonalEntry gPer[600];
static int gPerCount;
static u32 gGrowth[8][101];

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
    gSets = (FrontierPokemonBase *)malloc(sets * sizeof(FrontierPokemonBase));
    memcpy(gSets, p, sets * 16);
    gSetCount = sets;
    u8 *q = slurp(personalPath, &n);
    u16 count;
    memcpy(&count, q, 2);
    for (int i = 0; i < count; i++) {
        memcpy(&gPer[i], q + 2 + 11 * i, 11);
    }
    gPerCount = count;
    memcpy(gGrowth, q + 2 + 11 * count, sizeof(gGrowth));
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

// ------------------------------------------------------------------ the Pokémon (a model both sides use), Platinum's own data
// pokemon.c Pokemon_GetFormNarcIndex: a form's personal entry
static int FormIndex(int species, int form) {
    if (form) {
        switch (species) {
        case SPECIES_DEOXYS: return form <= 3 ? 496 + form - 1 : species;
        case SPECIES_WORMADAM: return form <= 2 ? 499 + form - 1 : species;
        case SPECIES_GIRATINA: return form == 1 ? 501 : species;
        case SPECIES_SHAYMIN: return form == 1 ? 502 : species;
        case SPECIES_ROTOM: return form <= 5 ? 503 + form - 1 : species;
        }
    }
    return species;
}
static const PersonalEntry *Per(int species, int form) {
    int i = FormIndex(species, form);
    return i < gPerCount ? &gPer[i] : &gPer[0];
}
u8 MoveTable_CalcMaxPP(u16 move, u8 ppUps) {
    u8 base;
    if (move == 0) {
        return 0;
    }
    base = (u8)(5 * (1 + (move * 7) % 8));
    return (u8)(base + base * ppUps / 5);
}
u32 Pokemon_GetSpeciesBaseExpAt(int species, int level) { return gGrowth[Per(species, 0)->growth & 7][level]; }
static int LevelAt(int species, u32 exp) {                 // SpeciesData_GetLevelAt
    int i;
    for (i = 1; i < 101; i++) {
        if (gGrowth[Per(species, 0)->growth & 7][i] > exp) {
            break;
        }
    }
    return i - 1;
}
// Pokemon_GetNatureStatValue (its u16: a stat over 595 wraps when raised, as Platinum's)
static u16 NatureStat(u8 nature, u16 value, int statType) {
    int inc = nature / 5 + 1, dec = nature % 5 + 1;
    u16 result;
    if (inc == dec) {
        return value;
    }
    if (statType == inc) {
        result = (u16)(value * 110);
        result /= 100;
        return result;
    }
    if (statType == dec) {
        result = (u16)(value * 90);
        result /= 100;
        return result;
    }
    return value;
}
static int IV(const Pokemon *mon, int i) { return (mon->ivs >> (5 * i)) & 31; }
// pokemon.c Pokemon_CalcLevelAndStats: the level from the experience, the stats (base stats by form, IVs, EVs, nature), the HP
// moved with the maximum
void Pokemon_CalcLevelAndStats(Pokemon *mon) {
    const PersonalEntry *p = Per(mon->species, mon->form);
    int level = LevelAt(mon->species, mon->exp), maxHp = mon->maxHp, hp = mon->hp, newMax;
    u8 nature = (u8)(mon->personality % 25);
    static const int sBase[5] = { 1, 2, 3, 4, 5 };     // attack, defense, speed, sp. attack, sp. defense (personal order)
    u16 *stats[5] = { &mon->atk, &mon->def, &mon->speed, &mon->spAtk, &mon->spDef };

    mon->level = (u8)level;
    newMax = mon->species == SPECIES_SHEDINJA ? 1 : (2 * p->base[0] + IV(mon, 0) + mon->evs[0] / 4) * level / 100 + level + 10;
    mon->maxHp = (u16)newMax;
    for (int s = 0; s < 5; s++) {
        int v = (2 * p->base[sBase[s]] + IV(mon, s + 1) + mon->evs[s + 1] / 4) * level / 100 + 5;
        *stats[s] = NatureStat(nature, (u16)v, s + 1);
    }
    if (hp != 0 || maxHp == 0) {
        if (mon->species == SPECIES_SHEDINJA) {
            hp = 1;
        } else if (hp == 0) {
            hp = newMax;
        } else {
            hp += newMax - maxHp;
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
    case MON_DATA_ATK: return mon->atk;
    case MON_DATA_DEF: return mon->def;
    case MON_DATA_SPEED: return mon->speed;
    case MON_DATA_SP_ATK: return mon->spAtk;
    case MON_DATA_SP_DEF: return mon->spDef;
    case MON_DATA_TYPE_1: return Per(mon->species, mon->form)->type1;
    case MON_DATA_TYPE_2: return Per(mon->species, mon->form)->type2;
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
    switch (field) {                    // (Platinum's party fields: HP and the stats are u16, the status u32)
    case MON_DATA_SPECIES: mon->species = *h; break;
    case MON_DATA_LEVEL: mon->level = *b; break;
    case MON_DATA_EXPERIENCE: mon->exp = *w; break;
    case MON_DATA_HP: mon->hp = *h; break;
    case MON_DATA_MAX_HP: mon->maxHp = *h; break;
    case MON_DATA_ATK: mon->atk = *h; break;
    case MON_DATA_DEF: mon->def = *h; break;
    case MON_DATA_SPEED: mon->speed = *h; break;
    case MON_DATA_SP_ATK: mon->spAtk = *h; break;
    case MON_DATA_SP_DEF: mon->spDef = *h; break;
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
void Pokemon_Init(Pokemon *mon) { memset(mon, 0, sizeof(*mon)); }
Pokemon *Pokemon_New(int heapID) { (void)heapID; return calloc(1, sizeof(Pokemon)); }
void Pokemon_Copy(Pokemon *src, Pokemon *dest) { *dest = *src; }
void Pokemon_UpdateAfterCatch(Pokemon *mon, TrainerInfo *t, int ball, int loc, int terrain, int heap) {
    (void)mon, (void)t, (void)ball, (void)loc, (void)terrain, (void)heap;
}
int SpeciesData_GetSpeciesValue(int species, int param) {
    const PersonalEntry *p = Per(species, 0);
    return param == SPECIES_DATA_ABILITY_2 ? p->ability2 : p->ability1;
}
// pokemon.c Pokemon_InitWith -> sub_02073E18: its random numbers (a personality unless given, a trainer id that isn't shiny
// with it for OTID_NOT_SHINY, the IVs drawn when the number given is 32 or more), the experience of the level, the ability, the
// stats (Pokemon_CalcLevelAndStats from no HP)
static u32 gPlatLCRNG;
u16 LCRNG_Next(void) {
    gPlatLCRNG = gPlatLCRNG * 1103515245L + 24691;
    return gPlatLCRNG >> 16;
}
// The DS's remainder: _s32_div_f returns 0 for a divisor of 0 (platinum_arcade_data.py checks its bytes are Platinum's and
// Black 2's)
int Plat_DSMod(int a, int b) { return b == 0 ? 0 : a % b; }
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
int Party_GetCurrentCount(const Party *party) { return party->count; }
Pokemon *Party_GetPokemonBySlotIndex(const Party *party, int slot) { return (Pokemon *)&party->mons[slot]; }

// ------------------------------------------------------------------ Platinum's side: the game around its Arcade code
struct SaveData {
    BattleFrontierSave frontier;
    Party party;
};
static SaveData gPlatSave;
static BattleArcade *gPlatArcade;
static FieldFrontierDTO gFieldData;
static FrontierScriptManager gScriptMan;
static FrontierGraphics gGraphics;
static u16 gVars[16];
static FieldBattleDTO *gLastDTO;
const ApplicationManagerTemplate gBattleApplicationTemplate = { 0 };
HarnessSystem gSystem;
static BattleArcadeAppArgs *gAppArgs;
static void (*gAppDone)(void *);

u16 FrontierScriptContext_GetVar(FrontierScriptContext *ctx) { return ctx->args[ctx->at++]; }
u16 *FrontierScriptContext_TryGetVarPointer(FrontierScriptContext *ctx) { return &gVars[ctx->args[ctx->at++] & 15]; }
u8 FrontierScriptContext_ReadByte(FrontierScriptContext *ctx) { return (u8)ctx->args[ctx->at++]; }
u16 FrontierScriptContext_ReadHalfWord(FrontierScriptContext *ctx) { return ctx->args[ctx->at++]; }
void *BattleFrontier_GetFacilityStruct(void *frontier) { (void)frontier; return gPlatArcade; }
void BattleFrontier_SetFacilityStruct(void *frontier, void *facility) { (void)frontier; gPlatArcade = facility; }
FieldFrontierDTO *BattleFrontier_GetFieldData(void *frontier) { (void)frontier; return &gFieldData; }
void BattleFrontier_RunSubApp(void *frontier, const ApplicationManagerTemplate *t, void *args, int a, void (*cb)(void *)) {
    (void)frontier, (void)a;
    if (t == &gBattleApplicationTemplate) {
        gLastDTO = args;
    } else {
        gAppArgs = args;
        gAppDone = cb;
    }
}
FrontierGraphics *FrontierScriptManager_GetGraphics(FrontierScriptManager *scriptMan) { (void)scriptMan; return &gGraphics; }
BOOL CheckPlayerWonBattle(u32 resultMask) { return resultMask == 1; }
void FieldBattleDTO_Free(FieldBattleDTO *dto) {
    for (int i = 0; i < MAX_BATTLERS; i++) {
        free(dto->parties[i]);
    }
    free(dto);
}
void sub_0209BA80(void *arcade) { (void)arcade; }
BOOL BattleCastle_IsMultiPlayerChallenge(u8 challengeType) { return challengeType == 2 || challengeType == 3; }
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
Options *SaveData_GetOptions(SaveData *saveData) { (void)saveData; return NULL; }
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
void StringTemplate_SetFrontierTrainerName(StringTemplate *t, u32 idx, u32 trainerID) { (void)t, (void)idx, (void)trainerID; }
void StringTemplate_SetPlayerName(StringTemplate *t, u32 idx, TrainerInfo *info) { (void)t, (void)idx, (void)info; }
// The drawing, particles and link: nothing
void BattleArcade_UpdateBackgroundForEffect(BattleArcade *a, FrontierGraphics *g) { (void)a, (void)g; }
void BattleArcade_LoadNormalBackground(void *a, FrontierGraphics *g) { (void)a, (void)g; }
void BattleArcade_CreateMonSprites(BattleArcade *a, FrontierGraphics *g, u16 o) { (void)a, (void)g, (void)o; }
void BattleArcade_DeleteMonSprites(BattleArcade *a, FrontierGraphics *g, u16 o) { (void)a, (void)g, (void)o; }
void BattleArcade_SetPlayerMonSpriteDrawFlag(BattleArcade *a, FrontierGraphics *g, u16 d, u16 i) { (void)a, (void)g, (void)d, (void)i; }
void BattleArcade_SetOpponentMonSpriteDrawFlag(BattleArcade *a, FrontierGraphics *g, u16 d, u16 i) { (void)a, (void)g, (void)d, (void)i; }
void BattleArcade_CreateItemSprites(BattleArcade *a, FrontierGraphics *g, u16 o) { (void)a, (void)g, (void)o; }
void BattleArcade_DeleteItemSprites(BattleArcade *a, FrontierGraphics *g, u16 o) { (void)a, (void)g, (void)o; }
void BattleArcade_SetItemDrawFlag(BattleArcade *a, FrontierGraphics *g, u16 o, u16 s, u16 d) { (void)a, (void)g, (void)o, (void)s, (void)d; }
void BattleArcade_SetPalette(u8 f, u8 s) { (void)f, (void)s; }
BOOL BattleArcade_SendCommMessage(BattleArcade *a, u16 c, u16 g) { (void)a, (void)c, (void)g; return TRUE; }
static VecFx32 gPos;
VecFx32 *Sprite_GetPosition(Sprite *sprite) { (void)sprite; return &gPos; }
void Sprite_SetPosition(Sprite *sprite, VecFx32 *pos) { (void)sprite, (void)pos; }
void Sprite_SetExplicitPriority(Sprite *sprite, int priority) { (void)sprite, (void)priority; }
void GXLayers_EngineAToggleLayers(u32 mask, int on) { (void)mask, (void)on; }
void PaletteData_Blend(void *p, int b, int s, int n, int f, int c) { (void)p, (void)b, (void)s, (void)n, (void)f, (void)c; }
void *ov104_0223D5A8(void *frontier, int id) { (void)frontier, (void)id; return NULL; }
u32 ov63_0222D050(void *sprite) { (void)sprite; return 0; }
ParticleSystem *FrontierParticleSystem_GetParticleSystem(void *ps, int i) { (void)ps, (void)i; return NULL; }
void ParticleSystem_CreateEmitterWithCallback(ParticleSystem *ps, int id, void (*cb)(SPLEmitter *), void *param) {
    (void)ps, (void)id, (void)cb, (void)param;
}
void *ParticleSystem_GetEmitterCallbackParam(void) { return NULL; }
void ParticleSystem_GetEmitterAxis(SPLEmitter *e, VecFx16 *axis) { (void)e, (void)axis; }
void SPLEmitter_SetAxis(SPLEmitter *e, VecFx16 *axis) { (void)e, (void)axis; }
void SPLEmitter_SetPos(SPLEmitter *e, const VecFx32 *pos) { (void)e, (void)pos; }
void BattleFrontier_LoadMonSpriteData(FrontierGraphics *g) { (void)g; }
void BattleFrontier_UnloadMonSpriteData(FrontierGraphics *g) { (void)g; }
void BattleFrontier_LoadItemSpriteData(FrontierGraphics *g) { (void)g; }
void BattleFrontier_UnloadItemSpriteData(FrontierGraphics *g) { (void)g; }
void BattleFrontier_PrintNormalTrainerMessage(FrontierScriptContext *ctx, u16 *msg) { (void)ctx, (void)msg; }
// The board's app: its frame, the screen, sound, touch (the stop is touched on the frame the harness picks)
struct ApplicationManager {
    void *data;
    void *args;
};
static int gTouchStop;
void Overlay_LoadByID(int id, int mode) { (void)id, (void)mode; }
void Overlay_UnloadByID(int id) { (void)id; }
void Heap_Create(int parent, int heapID, u32 size) { (void)parent, (void)heapID, (void)size; }
void Heap_Destroy(int heapID) { (void)heapID; }
void *ApplicationManager_NewData(ApplicationManager *appMan, u32 size, int heapID) {
    (void)heapID;
    appMan->data = calloc(1, size);
    return appMan->data;
}
void *ApplicationManager_Data(ApplicationManager *appMan) { return appMan->data; }
void *ApplicationManager_Args(ApplicationManager *appMan) { return appMan->args; }
void ApplicationManager_FreeData(ApplicationManager *appMan) {
    free(appMan->data);
    appMan->data = NULL;
}
BgConfig *BgConfig_New(int heapID) { (void)heapID; return NULL; }
void CommTool_ClearReceivedTempDataAllPlayers(void) {}
void CommTool_Init(int heapID) { (void)heapID; }
void CommTiming_StartSync(int n) { (void)n; }
BOOL CommTiming_IsSyncState(int n) { (void)n; return TRUE; }
BOOL CommSys_SendData(int cmd, void *data, int size) { (void)cmd, (void)data, (void)size; return TRUE; }
void StartScreenFade(int s, int a, int b, int c, int f, int st, int h) { (void)s, (void)a, (void)b, (void)c, (void)f, (void)st, (void)h; }
BOOL IsScreenFadeDone(void) { return TRUE; }
void SpriteList_Update(void *list) { (void)list; }
void VramTransfer_Free(void) {}
void SetVBlankCallback(void *cb, void *data) { (void)cb, (void)data; }
void Sound_PlayEffect(u16 seq) { (void)seq; }
void Sound_StopEffect(u16 seq, int a) { (void)seq, (void)a; }
int TouchScreen_CheckPressedHitTableID(const TouchScreenHitTable *table) { (void)table; return gTouchStop ? TOUCH_BUTTON_PRESSED : -1; }
void BattleArcadeAppSprite_SetAnim(BattleArcadeAppSprite *s, int anim) { (void)s, (void)anim; }
void BattleArcadeAppSprite_SetDrawFlag(BattleArcadeAppSprite *s, BOOL on) { (void)s, (void)on; }
void BattleArcadeAppSprite_SetPosition(BattleArcadeAppSprite *s, int x, int y) { (void)s, (void)x, (void)y; }

// Platinum's code reached by extract.py's wrappers
void Plat_ClearActiveStreak(SaveData *saveData, u8 challengeType);
void Plat_SetupAppArgs(BattleArcadeAppArgs *args, BattleArcade *arcade);
void Plat_StoreAppResults(BattleArcadeAppArgs *args);
BOOL FrontierScrCmd_InitBattleArcade(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleArcade_LoadTrainersForRound(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_FreeBattleArcade(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleArcade_CleanupBattle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleArcade_StartBattle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleArcade_SetupFirstOpponent(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleArcade_SetupNextOpponent(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_CallBattleArcadeFunction(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_BattleArcade_CheckWonBattle(FrontierScriptContext *ctx);
BOOL FrontierScrCmd_ApplyArcadeEffect(FrontierScriptContext *ctx);
BOOL BattleArcadeApp_Init(ApplicationManager *appMan, int *state);
BOOL BattleArcadeApp_Main(ApplicationManager *appMan, int *state);
BOOL BattleArcadeApp_Exit(ApplicationManager *appMan, int *state);
int Glue_AppSubState(void *app);
int Glue_AppCursor(void *app);
int Glue_AppTimer(void *app);
const u8 *Glue_AppEffects(void *app);
int Glue_AppStart(void *app);
int Glue_AppTier(void *app);
int Glue_AppAvailable(void *app, u8 *effects);
int Glue_CursorMoveFrames(int speed);
BOOL FrontierScrCmd_OpenBattleArcadeApp(FrontierScriptContext *ctx);

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
    plat_cmd(FrontierScrCmd_CallBattleArcadeFunction, 4, fn, arg1, arg2, 8);
    return gVars[8];
}

// ------------------------------------------------------------------ our side: the records, the parties, the last battle's
typedef struct {
    u16 stats[200];
    u8 streakFlags;
} OurRecords;
static OurRecords gOurRec;
static PlatArcadeSave gOurSave;
static PlatArcade gOur;
static PlatArcadeRoulette gOurBoard;
static Party gOurPlayers, gOurOpponents, gOurBattle[2];
static Party gOurField;

u16 PlatArcade_GetStat(void *records, u32 stat) { return stat < 200 ? ((OurRecords *)records)->stats[stat] : 0; }
void PlatArcade_SetStat(void *records, u32 stat, u16 value) {
    if (stat < 200) {
        ((OurRecords *)records)->stats[stat] = value > 9999 ? 9999 : value;
    }
}
u32 PlatArcade_GetStreakFlag(void *records, u32 type) { return (((OurRecords *)records)->streakFlags >> type) & 1; }
void PlatArcade_SetStreakFlag(void *records, u32 type, u32 value) {
    OurRecords *r = records;
    if (value >= 1) {
        r->streakFlags |= 1 << type;
    } else {
        r->streakFlags &= 0xff ^ (1 << type);
    }
}
u32 PlatArcade_FieldMonItem(PlatArcade *arcade, u8 fieldSlot) { (void)arcade; return gOurField.mons[fieldSlot].item; }
void PlatArcade_PartyAddFieldMon(PlatArcade *arcade, u8 fieldSlot) {
    gOurPlayers.mons[arcade->playerCount] = gOurField.mons[fieldSlot];
    gOurPlayers.count = arcade->playerCount + 1;
}
void PlatArcade_OpponentsClear(PlatArcade *arcade) { (void)arcade; memset(&gOurOpponents, 0, sizeof(gOurOpponents)); }
// FrontierPokemon_InitPokemon's Pokémon, made without its random numbers (the rules drew them): the set's values, the level's
// experience, the stats from no HP
void PlatArcade_OpponentAdd(PlatArcade *arcade, const PlatArcadeMon *mon, u8 level) {
    Pokemon *p = &gOurOpponents.mons[arcade->opponentCount];
    memset(p, 0, sizeof(*p));
    p->species = mon->species;
    p->form = mon->form;
    p->item = mon->item;
    for (int i = 0; i < 4; i++) {
        p->moves[i] = mon->moves[i];
        p->pp[i] = MoveTable_CalcMaxPP(mon->moves[i], 0);
    }
    p->otID = mon->otID;
    p->personality = mon->personality;
    p->ivs = ((u32)mon->ivs * 0x2108421u) & 0x3fffffff;
    memcpy(p->evs, mon->evs, 6);
    p->ability = mon->ability;
    p->friendship = mon->friendship;
    p->language = gGameLanguage;
    p->exp = Pokemon_GetSpeciesBaseExpAt(mon->species, level == 120 ? 50 : level);
    Pokemon_CalcLevelAndStats(p);
    gOurOpponents.count = arcade->opponentCount + 1;
}
static Party *OurSide(u32 side) {
    switch (side) {
    case PLATARCADE_PLAYERS: return &gOurPlayers;
    case PLATARCADE_OPPONENTS: return &gOurOpponents;
    case PLATARCADE_BATTLE_PLAYER: return &gOurBattle[0];
    }
    return &gOurBattle[1];
}
static const int sOurField[PLATARCADE_MON_FIELDS] = {
    MON_DATA_SPECIES, MON_DATA_SPECIES_EXISTS, MON_DATA_LEVEL, MON_DATA_EXPERIENCE, MON_DATA_HP, MON_DATA_MAX_HP, MON_DATA_ATK,
    MON_DATA_DEF, MON_DATA_SPEED, MON_DATA_SP_ATK, MON_DATA_SP_DEF, MON_DATA_STATUS, MON_DATA_HELD_ITEM, MON_DATA_TYPE_1,
    MON_DATA_TYPE_2, MON_DATA_ABILITY,
};
u32 PlatArcade_MonGet(PlatArcade *arcade, u32 side, u8 slot, u32 field) {
    (void)arcade;
    return Pokemon_GetValue(&OurSide(side)->mons[slot], sOurField[field], NULL);
}
void PlatArcade_MonSet(PlatArcade *arcade, u32 side, u8 slot, u32 field, u32 value) {
    (void)arcade;
    Pokemon_SetValue(&OurSide(side)->mons[slot], sOurField[field], &value);   // (little-endian: the u8 and u16 fields read the low bytes)
}
void PlatArcade_MonCalcLevelAndStats(PlatArcade *arcade, u32 side, u8 slot) {
    (void)arcade;
    Pokemon_CalcLevelAndStats(&OurSide(side)->mons[slot]);
}
// Party_HealAllMembers: full HP, no status, full PP
void PlatArcade_PartyHeal(PlatArcade *arcade, u32 side) {
    Party *party = OurSide(side);
    (void)arcade;
    for (int i = 0; i < party->count; i++) {
        Pokemon *p = &party->mons[i];
        if (p->species == 0) {
            continue;
        }
        p->hp = p->maxHp;
        p->status = 0;
        for (int j = 0; j < 4; j++) {
            if (p->moves[j] != 0 && p->pp[j] < MoveTable_CalcMaxPP(p->moves[j], p->ppUps[j])) {
                p->pp[j] = MoveTable_CalcMaxPP(p->moves[j], p->ppUps[j]);
            }
        }
    }
}
u32 PlatArcade_BaseExpAt(u16 species, u8 level) { return Pokemon_GetSpeciesBaseExpAt(species, level); }
void PlatArcade_ReadSet(u16 setID, PlatArcadeSet *set) { memcpy(set, &gSets[setID], sizeof(*set)); }
u16 PlatArcade_TrainerSets(u16 trainerID, u16 *sets, u16 max) {
    u16 n = gTrainers[trainerID].count < max ? gTrainers[trainerID].count : max;
    memcpy(sets, gTrainers[trainerID].sets, 2 * n);
    return n;
}
u16 PlatArcade_SpeciesAbility(u16 species, u32 slot) {
    return (u16)SpeciesData_GetSpeciesValue(species, slot ? SPECIES_DATA_ABILITY_2 : SPECIES_DATA_ABILITY_1);
}

// ------------------------------------------------------------------ the comparisons
static long gStat[24];                  // what the run went through
enum { N_CHALLENGES, N_BATTLES, N_WINS, N_LOSSES, N_ROUNDS, N_DAHLIA, N_SKIPPED, N_RESTS, N_RETIRES, N_BOARDS, N_TIMEOUTS,
       N_RANDOM_BOARDS, N_IMMUNE, N_BP, N_FREE_BP, N_SWAPS, N_FRAMES, N_EMPTY_KIND };
static long gEffectCount[PLATARCADE_EFFECTS];
static long gSpeedCount[8];

static void compare_mon(const Pokemon *p, const Pokemon *o, const char *what, int i) {
    CHECK(p->species == o->species && p->form == o->form && p->level == o->level && p->exp == o->exp && p->hp == o->hp &&
              p->maxHp == o->maxHp && p->status == o->status && p->item == o->item && p->ability == o->ability,
          "%s %d: species %d/%d level %d/%d exp %u/%u hp %d/%d max %d/%d status %u/%u item %d/%d ability %d/%d", what, i,
          p->species, o->species, p->level, o->level, p->exp, o->exp, p->hp, o->hp, p->maxHp, o->maxHp, p->status, o->status,
          p->item, o->item, p->ability, o->ability);
    CHECK(p->atk == o->atk && p->def == o->def && p->speed == o->speed && p->spAtk == o->spAtk && p->spDef == o->spDef,
          "%s %d: stats %d %d %d %d %d / %d %d %d %d %d", what, i, p->atk, p->def, p->speed, p->spAtk, p->spDef, o->atk, o->def,
          o->speed, o->spAtk, o->spDef);
    CHECK(!memcmp(p->moves, o->moves, sizeof(p->moves)) && !memcmp(p->pp, o->pp, sizeof(p->pp)) && p->otID == o->otID &&
              p->personality == o->personality && (p->ivs & 0x3fffffff) == (o->ivs & 0x3fffffff) &&
              !memcmp(p->evs, o->evs, 6) && p->friendship == o->friendship,
          "%s %d: moves, PP, OT, personality, IVs, EVs or friendship", what, i);
}

static void compare_party(const Party *p, const Party *o, const char *what) {
    CHECK(p->count == o->count, "%s: count %d/%d", what, p->count, o->count);
    for (int i = 0; i < p->count && i < o->count; i++) {
        compare_mon(&p->mons[i], &o->mons[i], what, i);
    }
}

static void compare_state(void) {
    BattleArcade *c = gPlatArcade;
    PlatArcade *o = &gOur;
    BattleArcadeSave *ps = &gPlatSave.frontier.arcadeSave;
    PlatArcadeSave *os = &gOurSave;
    CHECK(gPlatLCRNG == o->lcrng, "random state %08x / %08x", gPlatLCRNG, o->lcrng);
    if (c != NULL) {
        CHECK(c->challengeType == o->challengeType && c->currentBattle == o->currentBattle &&
                  c->cursorRandomized == o->cursorRandomized && c->activeEffect == o->activeEffect && c->weather == o->weather,
              "type/battle/randomized/effect/weather %d %d %d %d %d / %d %d %d %d %d", c->challengeType, c->currentBattle,
              c->cursorRandomized, c->activeEffect, c->weather, o->challengeType, o->currentBattle, o->cursorRandomized,
              o->activeEffect, o->weather);
        CHECK(c->currentStreak == o->currentStreak && c->currentRound == o->currentRound && c->saveStreak == o->saveStreak,
              "streak/round/saveStreak %d %d %d / %d %d %d", c->currentStreak, c->currentRound, c->saveStreak, o->currentStreak,
              o->currentRound, o->saveStreak);
        CHECK(c->rouletteSpeed == o->rouletteSpeed && c->performance == o->performance &&
                  c->seenArcadeStarIntro == o->seenArcadeStarIntro && c->immuneToEffect == o->immuneToEffect &&
                  c->randomIndex == o->randomIndex && c->wonBattle == o->wonBattle,
              "speed/performance/star/immune/random/won %d %d %d %d %d %d / %d %d %d %d %d %d", c->rouletteSpeed,
              c->performance, c->seenArcadeStarIntro, c->immuneToEffect, c->randomIndex, c->wonBattle, o->rouletteSpeed,
              o->performance, o->seenArcadeStarIntro, o->immuneToEffect, o->randomIndex, o->wonBattle);
        CHECK(c->appCursorPos[0] == o->appCursorPos && c->appCursorPos[5] == o->appCursorPos, "app cursor %d / %d",
              c->appCursorPos[0], o->appCursorPos);
        CHECK(!memcmp(c->partySlots, o->partySlots, 3) && !memcmp(c->savedHeldItems, o->savedHeldItems, 6), "slots, held items");
        CHECK(!memcmp(c->trainerIDs, o->trainerIDs, sizeof(o->trainerIDs)), "trainer ids");
        for (int i = 0; i < 4; i++) {
            CHECK(c->monHP[i] == o->monHP[i] && c->monAtk[i] == o->monAtk[i] && c->monDef[i] == o->monDef[i] &&
                      c->monSpeed[i] == o->monSpeed[i] && c->monSpAtk[i] == o->monSpAtk[i] && c->monSpDef[i] == o->monSpDef[i],
                  "kept stats %d", i);
        }
        CHECK(!memcmp(c->monSetIDs, o->monSetIDs, sizeof(o->monSetIDs)) && !memcmp(c->opponentMonIVs, o->opponentMonIVs, 4) &&
                  !memcmp(c->opponentMonPersonalities, o->opponentMonPersonalities, 16),
              "the opponents' sets, IVs, personalities");
        for (int i = 0; i < 4; i++) {
            FrontierPokemon *pm = &c->opponentMons[i];
            PlatArcadeMon *om = &o->opponentMons[i];
            CHECK(pm->species == om->species && pm->form == om->form && pm->item == om->item && !memcmp(pm->moves, om->moves, 8) &&
                      pm->otID == om->otID && pm->personality == om->personality && pm->hpIV == om->ivs &&
                      pm->spDefIV == om->ivs && !memcmp(pm->evList, om->evs, 6) && pm->ability == om->ability &&
                      pm->friendship == om->friendship,
                  "opponentMons[%d]: species %d/%d personality %08x/%08x", i, pm->species, om->species, pm->personality,
                  om->personality);
        }
        CHECK(Party_GetCurrentCount(c->playersParty) == o->playerCount, "party count %d/%d",
              Party_GetCurrentCount(c->playersParty), o->playerCount);
        CHECK(Party_GetCurrentCount(c->opponentsParty) == o->opponentCount, "opponent count %d/%d",
              Party_GetCurrentCount(c->opponentsParty), o->opponentCount);
        compare_party(c->playersParty, &gOurPlayers, "the player's party");
        compare_party(c->opponentsParty, &gOurOpponents, "the opponent's party");
    }
    CHECK(ps->challengeType == os->challengeType && ps->didSave == os->didSave && ps->currentBattle == os->currentBattle &&
              ps->cursorRandomized == os->cursorRandomized && ps->rouletteSpeed == os->rouletteSpeed &&
              !memcmp(ps->partySlots, os->partySlots, 3) && !memcmp(ps->heldItems, os->heldItems, sizeof(os->heldItems)) &&
              !memcmp(ps->trainerIDs, os->trainerIDs, sizeof(os->trainerIDs)) &&
              !memcmp(ps->monSetIDs, os->monSetIDs, sizeof(os->monSetIDs)),
          "the saved challenge");
    CHECK(!memcmp(gPlatSave.frontier.stats.soloStats, gOurRec.stats, 2 * 112), "the records");
    CHECK(gPlatSave.frontier.arcade.streakFlags.streakActiveFlags == gOurRec.streakFlags, "streak flags %x/%x",
          gPlatSave.frontier.arcade.streakFlags.streakActiveFlags, gOurRec.streakFlags);
}

// ------------------------------------------------------------------ the scene script's steps, both sides
static u16 both_fn(int fn, int arg1, int arg2, const char *where) {
    u16 a, b = 0xbeef;
    gWhere = where;
    a = plat_fn(fn, arg1, arg2);
    if (PlatArcade_Function(&gOur, &gOurSave, &gOurRec, (u8)fn, (u8)arg1, (u8)arg2, &b)) {
        if (b != 0xbeef || a != 0xbeef) {
            CHECK(a == b, "function %d (%d, %d): %d / %d", fn, arg1, arg2, a, b);
        }
    } else {
        CHECK(0, "function %d isn't ours", fn);
    }
    compare_state();
    return a;
}

static void start(int resuming, int type, int s1, int s2, int s3) {
    u32 seed = pick(0xffffffff) ^ (pick(0x10000) << 16);
    gWhere = resuming ? "resume" : "init";
    gPlatLCRNG = seed;
    gOur.lcrng = seed;
    memset(&gOurPlayers, 0, sizeof(gOurPlayers));
    memset(&gOurOpponents, 0, sizeof(gOurOpponents));
    plat_cmd(FrontierScrCmd_InitBattleArcade, 6, resuming, type, s1, s2, s3, 1);
    PlatArcade_Init(&gOur, &gOurSave, &gOurRec, (u16)resuming, (u8)type, (u8)s1, (u8)s2, (u8)s3);
    compare_state();
    gWhere = "load the round";
    plat_cmd(FrontierScrCmd_BattleArcade_LoadTrainersForRound, 1, resuming);
    PlatArcade_LoadTrainersForRound(&gOur, &gOurSave, (u16)resuming);
    compare_state();
}

static void setup_first(void) {
    gWhere = "first opponent";
    plat_cmd(FrontierScrCmd_BattleArcade_SetupFirstOpponent, 0);
    PlatArcade_SetupFirstOpponentsParty(&gOur);
    compare_state();
}

static void setup_next(void) {
    gWhere = "next opponent";
    plat_cmd(FrontierScrCmd_BattleArcade_SetupNextOpponent, 0);
    PlatArcade_SetupNextOpponentsParty(&gOur);
    compare_state();
}

static void free_challenge(void) {
    gWhere = "free";
    plat_cmd(FrontierScrCmd_FreeBattleArcade, 0);
    gPlatArcade = NULL;
    gOur.magic = 0;
}

// The board: Platinum's app run frame by frame (its fade, its panels turning, the cursor) against ours; the stop touched on the
// `stopFrame`th frame the cursor runs (900 or more: never, the 30 seconds end it)
static void board(int stopFrame) {
    ApplicationManager appMan = { 0 };
    int state = 0, frames = 0, running = 0;
    BOOL ourStopped = FALSE;
    u8 avail[PLATARCADE_EFFECTS];

    gWhere = "the board";
    gAppArgs = NULL;
    plat_cmd(FrontierScrCmd_OpenBattleArcadeApp, 0);
    appMan.args = gAppArgs;
    BattleArcadeApp_Init(&appMan, &state);
    PlatArcade_RouletteOpen(&gOur, &gOurBoard);
    PlatArcade_RouletteStart(&gOurBoard);
    gTouchStop = 0;
    for (frames = 0; frames < 2000; frames++) {
        int sub = Glue_AppSubState(appMan.data);
        if (state == 1 && sub == 6) {          // STATE_OPERATE_ROULETTE's running step: this frame the cursor moves, the stop
            if (running == 0) {
                gWhere = "the board's panels";
                int n = Glue_AppAvailable(appMan.data, avail);
                CHECK(n == gOurBoard.numAvailableEffects && !memcmp(avail, gOurBoard.availableEffects, PLATARCADE_EFFECTS),
                      "available effects %d / %d", n, gOurBoard.numAvailableEffects);
                CHECK(!memcmp(Glue_AppEffects(appMan.data), gOurBoard.rouletteEffects, PLATARCADE_GRID), "the 16 panels");
                CHECK(Glue_AppStart(appMan.data) == gOurBoard.startingCursorPos && Glue_AppTier(appMan.data) == gOurBoard.categoryTier,
                      "start %d/%d tier %d/%d", Glue_AppStart(appMan.data), gOurBoard.startingCursorPos, Glue_AppTier(appMan.data),
                      gOurBoard.categoryTier);
                CHECK(gPlatLCRNG == gOur.lcrng, "random state before the cursor runs");
                for (int k = 0; k < PLATARCADE_CATEGORIES; k++) {
                    if (gOurBoard.availableEffectsPerCategory[k] == 0) {
                        gStat[N_EMPTY_KIND]++;
                    }
                }
                gWhere = "the board's cursor";
            }
            gTouchStop = running == stopFrame;
            ourStopped = PlatArcade_RouletteTick(&gOur, &gOurBoard, running == stopFrame);
            running++;
            gStat[N_FRAMES]++;
        } else {
            gTouchStop = 0;
        }
        if (BattleArcadeApp_Main(&appMan, &state)) {
            break;
        }
        if (state == 1 && running > 0 && Glue_AppSubState(appMan.data) >= 6) {
            CHECK(Glue_AppCursor(appMan.data) == gOurBoard.cursorPos, "frame %d: cursor %d/%d", running,
                  Glue_AppCursor(appMan.data), gOurBoard.cursorPos);
            CHECK(gPlatLCRNG == gOur.lcrng, "frame %d: random state", running);
        }
    }
    CHECK(ourStopped, "ours didn't stop");
    if (running > stopFrame + 1 || running == 0) {
        CHECK(0, "the board ran %d frames, the stop at %d", running, stopFrame);
    }
    if (stopFrame >= PLATARCADE_ROULETTE_FRAMES) {
        gStat[N_TIMEOUTS]++;
    }
    if (gOurBoard.randomizeCursorMovement) {
        gStat[N_RANDOM_BOARDS]++;
    }
    BattleArcadeApp_Exit(&appMan, &state);
    gAppDone(gAppArgs);
    PlatArcade_RouletteStop(&gOur, &gOurBoard);
    gStat[N_BOARDS]++;
    gEffectCount[gOur.activeEffect < PLATARCADE_EFFECTS ? gOur.activeEffect : 0]++;
    gSpeedCount[gOur.rouletteSpeed & 7]++;
    compare_state();
}

static void apply_effect(void) {
    gWhere = "the effect";
    plat_cmd(FrontierScrCmd_ApplyArcadeEffect, 0);
    PlatArcade_ApplyEffect(&gOur, gOur.activeEffect);
    if (gOur.immuneToEffect) {
        gStat[N_IMMUNE]++;
    }
    compare_state();
}

// The battle: Platinum's setup against our rules' (the parties as they go in, before the heal), an outcome the harness draws,
// the cleanup. TRUE if won
static BOOL battle(void) {
    BOOL swapped;
    u16 ai;

    gWhere = "the battle's setup";
    gLastDTO = NULL;
    gOurBattle[0] = gOurPlayers;
    gOurBattle[1] = gOurOpponents;
    plat_cmd(FrontierScrCmd_BattleArcade_StartBattle, 0);
    ai = PlatArcade_SetupBattle(&gOur, &swapped);
    if (swapped) {
        Party t = gOurBattle[0];
        gOurBattle[0] = gOurBattle[1];
        gOurBattle[1] = t;
        gStat[N_SWAPS]++;
    }
    FieldBattleDTO *dto = gLastDTO;
    compare_party(dto->parties[BATTLER_PLAYER_1], &gOurBattle[0], "the battle's player side");
    compare_party(dto->parties[BATTLER_ENEMY_1], &gOurBattle[1], "the battle's enemy side");
    CHECK(dto->trainer[BATTLER_ENEMY_1].header.aiMask == ai, "AI %d/%d", dto->trainer[BATTLER_ENEMY_1].header.aiMask, ai);
    CHECK(dto->fieldWeather == gOur.weather, "weather %d/%d", dto->fieldWeather, gOur.weather);
    CHECK(dto->trainerIDs[BATTLER_ENEMY_1] == gOur.trainerIDs[gOur.currentBattle], "trainer %u/%d",
          dto->trainerIDs[BATTLER_ENEMY_1], gOur.trainerIDs[gOur.currentBattle]);
    compare_state();
    // The outcome, on both sides' copies: HP (fainted or not), a status, an item used up, on either side; the turns; won or lost
    for (int side = 0; side < 2; side++) {
        Party *p = dto->parties[side == 0 ? BATTLER_PLAYER_1 : BATTLER_ENEMY_1];
        for (int i = 0; i < p->count; i++) {
            Pokemon *a = &p->mons[i], *b = &gOurBattle[side].mons[i];
            u32 r = pick(8);
            u16 hp = r < 3 ? 0 : (u16)pick(a->maxHp + 1u);
            u32 status = pick(3) == 0 ? (pick(2) ? MON_CONDITION_BURN : MON_CONDITION_PARALYSIS) : 0;
            u16 item = pick(4) == 0 ? 0 : a->item;
            a->hp = b->hp = hp;
            a->status = b->status = status;
            a->item = b->item = item;
        }
    }
    u32 turns = pick(4) == 0 ? pick(3) : pick(14);
    BOOL won = pick(6) != 0;
    dto->totalTurnsElapsed = (int)turns;
    dto->resultMask = won ? 1 : 2;
    gWhere = "the battle's cleanup";
    plat_cmd(FrontierScrCmd_BattleArcade_CleanupBattle, 0);
    PlatArcade_CleanupBattle(&gOur, turns, won);
    gVars[9] = 0xbeef;
    plat_cmd(FrontierScrCmd_BattleArcade_CheckWonBattle, 1, 9);
    CHECK(gVars[9] == (u16)gOur.wonBattle, "won %d/%d", gVars[9], gOur.wonBattle);
    compare_state();
    gStat[N_BATTLES]++;
    gStat[won ? N_WINS : N_LOSSES]++;
    return won;
}

// ------------------------------------------------------------------ a challenge, as frontier_scripts_battle_arcade.s runs it
// The field party: six Pokémon of every species and level (above 50 too), some of the forms, random IVs, EVs, natures, items
static void make_field_party(void) {
    Party *pp = &gPlatSave.party;
    memset(pp, 0, sizeof(*pp));
    for (int i = 0; i < 6; i++) {
        Pokemon *m = &pp->mons[i];
        static const u16 sForms[][2] = { { 386, 4 }, { 413, 3 }, { 479, 6 }, { 487, 2 }, { 492, 2 } };
        m->species = (u16)(1 + pick(493));
        if (pick(8) == 0) {
            int f = pick(5);
            m->species = sForms[f][0];
            m->form = (u16)pick(sForms[f][1]);
        }
        int level = 1 + pick(100);
        m->exp = Pokemon_GetSpeciesBaseExpAt(m->species, level);
        if (level < 100) {
            m->exp += pick(Pokemon_GetSpeciesBaseExpAt(m->species, level + 1) - m->exp);
        }
        m->personality = pick(0xffffffff) ^ (pick(0x10000) << 16);
        m->otID = pick(0xffffffff);
        m->ivs = pick(0x40000000);
        for (int s = 0; s < 6; s++) {
            m->evs[s] = (u8)pick(256);
        }
        const PersonalEntry *pe = Per(m->species, m->form);
        m->ability = (m->personality & 1) && pe->ability2 ? pe->ability2 : pe->ability1;
        if (pick(6) == 0) {             // (an ability the effects test: Immunity, Limber, Water Veil, Insomnia, Vital Spirit, Magma Armor)
            static const u8 sAbilities[] = { 17, 7, 41, 15, 72, 40 };
            m->ability = sAbilities[pick(6)];
        }
        m->item = pick(3) ? (u16)(1 + pick(400)) : 0;
        for (int k = 0; k < 4; k++) {
            m->moves[k] = (u16)(pick(5) ? 1 + pick(467) : 0);
            m->ppUps[k] = (u8)pick(4);
            m->pp[k] = MoveTable_CalcMaxPP(m->moves[k], m->ppUps[k]);
        }
        m->friendship = (u8)pick(256);
        m->language = 2;
        Pokemon_CalcLevelAndStats(m);
    }
    pp->count = 6;
    gOurField = *pp;
}

// The battle room's menu after a win (_28B3): 0 continue, 1 rest, 2 retire
static int menu_choice(void) {
    u32 r = pick(20);
    return r < 16 ? 0 : r < 18 ? 1 : 2;
}

static void challenge(int type) {
    int slots[6] = { 0, 1, 2, 3, 4, 5 };
    for (int i = 5; i > 0; i--) {
        int j = pick(i + 1), t = slots[i];
        slots[i] = slots[j];
        slots[j] = t;
    }
    gStat[N_CHALLENGES]++;
    start(0, type, slots[0], slots[1], slots[2]);
    setup_first();
    int resumed = 0;
    for (int guard = 0; guard < 200; guard++) {
        // _0B20: the next battle's number, Dahlia's approach, the board
        both_fn(PLATARCADE_FN_GET_CURRENT_STREAK, 0, 0, "the streak");
        u16 next = both_fn(PLATARCADE_FN_GET_NEXT_BATTLE_TYPE, 0, 0, "the next battle");
        if (next != PLATARCADE_NEXT_NORMAL) {
            gStat[N_DAHLIA]++;
        }
        u32 r = pick(10);
        int stop = r == 0 ? PLATARCADE_ROULETTE_FRAMES + (int)pick(5) : r < 3 ? (int)pick(8) : (int)pick(240);
        board(stop);
        apply_effect();
        u16 effect = both_fn(PLATARCADE_FN_GET_ACTIVE_EFFECT, 0, 0, "the effect's number");
        both_fn(PLATARCADE_FN_GET_HELD_ITEM, 0, 0, "the player's item");
        both_fn(PLATARCADE_FN_GET_HELD_ITEM, 1, 0, "the opponent's item");
        both_fn(PLATARCADE_FN_CHECK_IMMUNE_TO_EFFECT, 0, 0, "immune");
        if (effect == PLATARCADE_EFFECT_GET_1_BP || effect == PLATARCADE_EFFECT_GET_3_BP) {
            gStat[N_FREE_BP] += both_fn(PLATARCADE_FN_GET_FREE_BP, 0, 0, "the free BP");
        }
        BOOL won = TRUE;
        if (effect == PLATARCADE_EFFECT_NO_BATTLE) {
            gStat[N_SKIPPED]++;          // _1FFC: no battle, on to the next
        } else {
            won = battle();
        }
        if (!won) {                     // _2D52: the loss
            both_fn(PLATARCADE_FN_SAVE_ON_LOSS, 0, 0, "the loss");
            break;
        }
        both_fn(PLATARCADE_FN_INCREMENT_CURRENT_BATTLE, 1, 0, "the next battle");
        both_fn(PLATARCADE_FN_INCREMENT_CURRENT_STREAK, 0, 0, "the streak up");
        if (gOur.currentBattle == PLATARCADE_BATTLES_PER_ROUND) {     // _272A: the round's end
            both_fn(PLATARCADE_FN_SAVE_ON_COMPLETING_ROUND, 0, 0, "the round's end");
            gStat[N_BP] += both_fn(PLATARCADE_FN_GET_EARNED_BP, 0, 0, "the BP");
            gStat[N_ROUNDS]++;
            break;
        }
        // _28B3: Dahlia's approach (once), the menu
        if (both_fn(PLATARCADE_FN_GET_NEXT_BATTLE_TYPE, 0, 0, "the next battle") != PLATARCADE_NEXT_NORMAL && !resumed) {
            both_fn(PLATARCADE_FN_CHECK_SEEN_STAR_INTRO, 0, 0, "Dahlia's approach");
        }
        int choice = menu_choice();
        if (choice == 2) {               // _2CB2: retire
            gStat[N_RETIRES]++;
            both_fn(PLATARCADE_FN_SAVE_ON_LOSS, 0, 0, "the retire");
            break;
        }
        if (choice == 1) {               // _2C78: rest: the quick save, the reset, the resume (the lobby's Continue)
            gStat[N_RESTS]++;
            both_fn(PLATARCADE_FN_QUICKSAVE, 0, 0, "the rest");
            free_challenge();
            start(1, 0, 0, 0, 0);
            setup_first();             // _0A07, then the menu again (VAR_0x8003 1)
            resumed = 1;
            if (both_fn(PLATARCADE_FN_GET_NEXT_BATTLE_TYPE, 0, 0, "the next battle") != PLATARCADE_NEXT_NORMAL) {
                both_fn(PLATARCADE_FN_CHECK_SEEN_STAR_INTRO, 0, 0, "Dahlia's approach");
            }
            if (pick(6) == 0) {
                gStat[N_RETIRES]++;
                both_fn(PLATARCADE_FN_SAVE_ON_LOSS, 0, 0, "the retire");
                break;
            }
        }
        resumed = 0;
        setup_next();                   // _2B5E: continue
    }
    free_challenge();
}

// ------------------------------------------------------------------ the sweeps
// ArcadeEffect_LowerHP's double (maxHP * 1.2, truncated) against ours (maxHP * 6 / 5), every maxHP a u16 holds
static void sweep_lower_hp(void) {
    gWhere = "LowerHP's double";
    for (u32 maxHP = 0; maxHP < 65536; maxHP++) {
        u32 hp = maxHP * 1.2;
        CHECK(hp == maxHP * 6 / 5, "maxHP %u: %u / %u", maxHP, hp, maxHP * 6 / 5);
    }
    gWhere = "the cursor's speeds";
    for (int s = 0; s < 8; s++) {
        CHECK(Glue_CursorMoveFrames(s) == PlatArcade_CursorMoveFrames((u8)s), "speed %d: %d / %d", s, Glue_CursorMoveFrames(s),
              PlatArcade_CursorMoveFrames((u8)s));
    }
}

// The board for every round 0-15, battle 0-30 and 9998-10001, performance 0-30 (the tiers), random cursor on and off, at every
// speed: Platinum's app against ours, a random stop
static void sweep_boards(void) {
    static const int sBattles[] = { 9998, 9999, 10000 };
    for (int round = 0; round < 16; round++) {
        for (int b = 0; b < 34; b++) {
            int battle = b < 31 ? b : sBattles[b - 31];
            gSeed = 1000000 + round * 100 + b;
            gRng = gSeed;
            memset(&gOurRec, 0, sizeof(gOurRec));
            memset(&gPlatSave, 0, sizeof(gPlatSave));
            make_field_party();
            start(0, pick(2), 0, 1, 2);
            setup_first();
            for (int perf = 0; perf < 31; perf += 1 + (int)pick(3)) {
                gPlatArcade->currentRound = gOur.currentRound = (u16)round;
                gPlatArcade->currentStreak = gOur.currentStreak = (u16)battle;
                gPlatArcade->performance = gOur.performance = (u8)perf;
                gPlatArcade->rouletteSpeed = gOur.rouletteSpeed = (u8)pick(8);
                gPlatArcade->cursorRandomized = gOur.cursorRandomized = (u8)pick(2);
                board(pick(5) == 0 ? 900 : (int)pick(300));
            }
            free_challenge();
        }
    }
}

static void run_seed(unsigned seed) {
    gSeed = seed;
    gRng = seed * 2654435761u + 7;
    memset(&gOurRec, 0, sizeof(gOurRec));
    memset(&gPlatSave, 0, sizeof(gPlatSave));
    // The records: streaks a player has (some at Dahlia's door: 20, 48), the streak flags
    for (int t = 0; t < 2; t++) {
        static const u16 sStreaks[] = { 0, 0, 7, 14, 20, 21, 28, 48, 49, 56, 63, 70, 140, 9990 };
        u16 latest = sStreaks[pick(COUNT(sStreaks))];
        if (pick(4) == 0) {
            latest = (u16)pick(80);
        }
        u16 record = latest + (u16)pick(30);
        gOurRec.stats[PlatArcade_StatIndex((u8)t, PLATARCADE_STAT_LATEST_STREAK)] = latest;
        gOurRec.stats[PlatArcade_StatIndex((u8)t, PLATARCADE_STAT_RECORD_STREAK)] = record;
        if (pick(4)) {
            gOurRec.streakFlags |= 1 << t;
        }
    }
    memcpy(gPlatSave.frontier.stats.soloStats, gOurRec.stats, 2 * 112);
    gPlatSave.frontier.arcade.streakFlags.streakActiveFlags = gOurRec.streakFlags;
    make_field_party();
    for (int c = 0; c < 6; c++) {
        challenge(pick(2));
        if (pick(5) == 0) {             // the lobby's DeleteActiveBattleArcadeStreak
            int t = pick(2);
            gWhere = "the lobby's streak deletion";
            Plat_ClearActiveStreak(&gPlatSave, (u8)t);
            PlatArcade_ClearActiveStreak(&gOurRec, (u8)t);
            compare_state();
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "sim SETS PERSONAL [SEEDS]\n");
        return 2;
    }
    load(argv[1], argv[2]);
    int seeds = argc > 3 ? atoi(argv[3]) : 1000;
    gScriptMan.frontier = NULL;
    gFieldData.saveData = &gPlatSave;
    sweep_lower_hp();
    sweep_boards();
    for (int s = 1; s <= seeds; s++) {
        run_seed((unsigned)s);
    }
    printf("%d seeds: %ld challenges, %ld battles (%ld won, %ld lost), %ld skipped by the board, %ld rounds (%ld BP), %ld Dahlia "
           "battles, %ld rests resumed, %ld retires\n",
           seeds, gStat[N_CHALLENGES], gStat[N_BATTLES], gStat[N_WINS], gStat[N_LOSSES], gStat[N_SKIPPED], gStat[N_ROUNDS],
           gStat[N_BP], gStat[N_DAHLIA], gStat[N_RESTS], gStat[N_RETIRES]);
    printf("boards: %ld (%ld cursor frames, %ld stopped by the 30 seconds, %ld with the random cursor, %ld kinds with no effect), "
           "%ld immune, %ld swaps, %ld free BP\n",
           gStat[N_BOARDS], gStat[N_FRAMES], gStat[N_TIMEOUTS], gStat[N_RANDOM_BOARDS], gStat[N_EMPTY_KIND], gStat[N_IMMUNE],
           gStat[N_SWAPS], gStat[N_FREE_BP]);
    printf("effects drawn:");
    for (int e = 0; e < PLATARCADE_EFFECTS; e++) {
        printf(" %d:%ld", e, gEffectCount[e]);
    }
    printf("\nspeeds after the board:");
    for (int s = 0; s < 8; s++) {
        printf(" %d:%ld", s, gSpeedCount[s]);
    }
    printf("\n%ld checks, %ld different\n", gChecks, gProblems);
    return gProblems ? 1 : 0;
}
