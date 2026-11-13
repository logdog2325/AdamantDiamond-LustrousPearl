// The Battle Factory's rules, Platinum's against ours, on the host (notes/PLATINUM_FRONTIER.md "The Battle Factory").
//   sim SETS SPECIES SEEDS
// For every seed, each Single and Double challenge at Level 50 and Open Level, starting at each round 0-9 with each trade
// count that changes the rentals (0, 6-7, 13-14, 20-21, 27-28, 34-35): the round's Trainers (Thorton at the 21st and 49th),
// the six rentals, the first opponent's Pokémon, the three rented, then the seven battles: the streak and next-battle
// kind, the hints (the opponent's species, moves, common type), the next opponent, a swap or none, the round's end
// (records, streak flag, Battle Points) or a loss; the save before a rest and the challenge resumed from it; the lobby's
// streak deletion. Both sides take Platinum's LCRNG from the same state; after every step the random state must be the same,
// so both drew the same numbers.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "plat_types.h"
#include "pearlb2/plat_factory.h"

u8 gGameLanguage = 2;
static u32 sLCRNGState;
static u8 *sSets;
static u32 sSetCount;
static u8 sSpecies[600][6];         // type 1, type 2, ability 1 (u16), ability 2 (u16)
static int sB2Types;                // ours reads Black 2's type numbers (no Mystery type)
static BattleFrontierSave sPlatFrontier;
static BattleFactory *sPlat;
static u8 sCtxBytes[3];
static int sCtxPos;
static u16 sCtxVar;
static u16 sScrVars[2];
static int sScrPos;
static long sChecks, sFails;

// ---------------------------------------------------------------- Platinum's calls outside the rules
u16 LCRNG_Next(void) {
    sLCRNGState = sLCRNGState * 1103515245 + 24691;
    return (u16)(sLCRNGState >> 16);
}
void *Heap_Alloc(enum HeapID heapID, u32 size) { (void)heapID; return calloc(1, size); }
void Heap_Free(void *ptr) { free(ptr); }
Party *Party_New(enum HeapID heapID) { (void)heapID; return calloc(1, sizeof(Party)); }
void Party_Init(Party *party) { party->count = 0; }
int Party_GetCurrentCount(const Party *party) { return party->count; }
Pokemon *Party_GetPokemonBySlotIndex(const Party *party, int slot) { return (Pokemon *)&party->mons[slot]; }
void Party_AddPokemonBySlotIndex(Party *party, int slot, Pokemon *mon) { party->mons[slot] = *mon; }
Pokemon *Pokemon_New(enum HeapID heapID) { (void)heapID; return calloc(1, sizeof(Pokemon)); }
u32 Pokemon_GetValue(Pokemon *mon, int field, void *dest) {
    (void)dest;
    switch (field) {
    case MON_DATA_SPECIES: return mon->species;
    case MON_DATA_HELD_ITEM: return mon->item;
    case MON_DATA_ATK_IV: return mon->atkIV;
    case MON_DATA_PERSONALITY: return mon->personality;
    case MON_DATA_TYPE_1: return mon->type1;
    case MON_DATA_TYPE_2: return mon->type2;
    }
    abort();
}
BoxPokemon *Pokemon_GetBoxPokemon(Pokemon *mon) { (void)mon; return NULL; }
u32 SpeciesData_GetSpeciesValue(int species, int field) {
    const u8 *s = sSpecies[species];
    return field == SPECIES_DATA_ABILITY_1 ? (u32)(s[2] | s[3] << 8) : (u32)(s[4] | s[5] << 8);
}
void MessageLoader_GetSpeciesName(u32 species, u32 heapID, u16 *dest) { (void)species; (void)heapID; dest[0] = 0xffff; }
BattleFrontierSave *SaveData_GetBattleFrontier(SaveData *saveData) { (void)saveData; return &sPlatFrontier; }
BattleFactorySave *BattleFactorySave_Get(SaveData *saveData) { (void)saveData; return &sPlatFrontier.factorySave; }
BattleFactoryStreakFlags *BattleFactoryStreakFlags_Get(SaveData *saveData) {
    (void)saveData;
    return &sPlatFrontier.factory.streakFlags;
}
VarsFlags *SaveData_GetVarsFlags(SaveData *saveData) { (void)saveData; return NULL; }
GameRecords *SaveData_GetGameRecords(SaveData *saveData) { (void)saveData; return NULL; }
void GameRecords_IncrementRecordValue(GameRecords *records, int id) { (void)records; (void)id; }
u8 SystemVars_GetWiFiFrontierCleared(VarsFlags *vars) { (void)vars; abort(); }
void BattleFrontier_FlagGeonetLinkInfo(SaveData *saveData) { (void)saveData; abort(); }
int NintendoWFC_GetHostFriendIdx(void) { abort(); }
void OS_ResetSystem(int x) { (void)x; abort(); }
void Bg_ChangeTilemapRectPalette(void *bg, int layer, int x, int y, int w, int h, int pal) {
    (void)bg; (void)layer; (void)x; (void)y; (void)w; (void)h; (void)pal;
}
void Bg_ScheduleTilemapTransfer(void *bg, int layer) { (void)bg; (void)layer; }
SysTask *SysTask_Start(void (*fn)(SysTask *, void *), void *data, int priority) {
    (void)fn; (void)data; (void)priority;
    return NULL;
}
void SysTask_Done(SysTask *task) { (void)task; }
void UpdateCorridorFloorBG(SysTask *task, void *data) { (void)task; (void)data; }
FrontierGraphics *FrontierScriptManager_GetGraphics(FrontierScriptManager *man) { (void)man; return NULL; }
void *BattleFrontier_GetFacilityStruct(void *frontier) { (void)frontier; return sPlat; }
u8 FrontierScriptContext_ReadByte(FrontierScriptContext *ctx) { (void)ctx; return sCtxBytes[sCtxPos++]; }
u16 *FrontierScriptContext_TryGetVarPointer(FrontierScriptContext *ctx) { (void)ctx; return &sCtxVar; }
u16 ScriptContext_GetVar(ScriptContext *ctx) { (void)ctx; return sScrVars[sScrPos++]; }
void StringTemplate_SetSpeciesName(StringTemplate *t, int idx, BoxPokemon *mon) { (void)t; (void)idx; (void)mon; }
void sub_0209BA80(void *factory) { (void)factory; abort(); }
u16 BattleFactory_GetNextOpponentObjectID(BattleFactory *factory, u8 trainerSlot) { (void)factory; (void)trainerSlot; return 0; }
void BattleFrontier_LoadTrainer(FrontierOpponent *opponent, u16 trainerID, enum HeapID heapID, enum NarcID narcID) {
    (void)opponent; (void)trainerID; (void)heapID; (void)narcID;
}
void BattleFrontier_GetPokemonBase(FrontierPokemonBase *monData, int narcIdx, enum NarcID narcID) {
    (void)narcID;
    if ((u32)narcIdx >= sSetCount) {
        abort();
    }
    memcpy(monData, sSets + 16 * narcIdx, 16);
}
// FrontierPokemon_InitPokemon: the Pokémon at its level. Its random numbers are pokemon.c's Pokemon_InitWith ->
// sub_02073E18 with the personality given and OTID_NOT_SHINY (a trainer id drawn until it isn't shiny with it), then,
// as the IVs come as one number of 32 or more, one draw for HP/Attack/Defense and one for the other three
static void TypesOf(u16 species, u8 *type1, u8 *type2) {
    *type1 = sSpecies[species][0];
    *type2 = sSpecies[species][1];
}
void FrontierPokemon_InitPokemon(const FrontierPokemon *frontierMon, Pokemon *mon, u8 setLevel) {
    u32 otID;
    (void)setLevel;
    memset(mon, 0, sizeof(*mon));
    do {
        otID = LCRNG_Next();
        otID |= (u32)LCRNG_Next() << 16;
    } while (Pokemon_IsPersonalityShiny(otID, frontierMon->personality));
    if ((frontierMon->combinedIVs & 0x3FFFFFFF) >= 32) {
        LCRNG_Next();
        LCRNG_Next();
    }
    mon->species = frontierMon->species;
    mon->form = frontierMon->form;
    mon->item = frontierMon->item;
    mon->atkIV = frontierMon->atkIV;
    mon->personality = frontierMon->personality;
    mon->otID = frontierMon->otID;
    TypesOf(mon->species, &mon->type1, &mon->type2);
}
void BattleFactory_UpdatePartnersParty(BattleFactory *factory) { (void)factory; abort(); }   // (a multi challenge's)
void BattleFactory_AddRentalPokemonToParty(SaveData *saveData, Party *party, Pokemon *mon) {
    (void)saveData;
    if (party->count < MAX_PARTY_SIZE) {
        party->mons[party->count++] = *mon;
    }
}

// ---------------------------------------------------------------- ours: what factory.c gives the rules on the DS
void PlatFactory_ReadSet(u16 setID, PlatFactorySet *set) {
    if (setID >= sSetCount) {
        abort();
    }
    memcpy(set, sSets + 16 * setID, 16);
}
u16 PlatFactory_SpeciesAbility(u16 species, u32 slot) { return (u16)SpeciesData_GetSpeciesValue(species, (int)slot); }
// Black 2's numbering drops Platinum's Mystery type (9): Fire 10 -> 9 .. Dark 17 -> 16
static u8 ToB2Type(u8 t) { return t > 9 ? (u8)(t - 1) : t; }
void PlatFactory_SpeciesTypes(u16 species, u16 form, u8 *type1, u8 *type2) {
    (void)form;
    TypesOf(species, type1, type2);
    if (sB2Types) {
        *type1 = ToB2Type(*type1);
        *type2 = ToB2Type(*type2);
    }
}

// ---------------------------------------------------------------- comparing
static char sWhere[200];
#define CHECK(cond, ...)                                                       \
    do {                                                                       \
        sChecks++;                                                             \
        if (!(cond)) {                                                         \
            if (sFails++ < 20) {                                               \
                printf("DIFF %s: ", sWhere);                                   \
                printf(__VA_ARGS__);                                           \
                printf("\n");                                                  \
            }                                                                  \
        }                                                                      \
    } while (0)

static void SameMon(const FrontierPokemon *p, const PlatFactoryMon *o, const char *what, int i) {
    int k;
    CHECK(p->species == o->species && p->form == o->form && p->item == o->item, "%s %d species/form/item %d/%d/%d vs %d/%d/%d",
          what, i, p->species, p->form, p->item, o->species, o->form, o->item);
    for (k = 0; k < 4; k++) {
        CHECK(p->moves[k] == o->moves[k], "%s %d move %d", what, i, k);
    }
    CHECK(p->otID == o->otID && p->personality == o->personality, "%s %d otID/personality %08x/%08x vs %08x/%08x", what, i,
          p->otID, p->personality, o->otID, o->personality);
    CHECK(p->hpIV == o->ivs && p->spDefIV == o->ivs, "%s %d ivs %d vs %d", what, i, p->hpIV, o->ivs);
    for (k = 0; k < 6; k++) {
        CHECK(p->evList[k] == o->evs[k], "%s %d ev %d: %d vs %d", what, i, k, p->evList[k], o->evs[k]);
    }
    CHECK(p->ability == o->ability && p->friendship == o->happiness, "%s %d ability/friendship %d/%d vs %d/%d", what, i,
          p->ability, p->friendship, o->ability, o->happiness);
}

static void SameParty(const Party *p, const PlatFactoryMon *o, int count, const char *what) {
    int i;
    CHECK(p->count == count, "%s count %d vs %d", what, p->count, count);
    for (i = 0; i < p->count && i < count; i++) {
        CHECK(p->mons[i].species == o[i].species && p->mons[i].item == o[i].item && p->mons[i].atkIV == o[i].ivs &&
                  p->mons[i].personality == o[i].personality && p->mons[i].otID == o[i].otID,
              "%s %d", what, i);
    }
}

static void Same(BattleFactory *p, PlatFactory *o, PlatFactorySave *save, u16 *stats, u8 flags) {
    int i;
    CHECK(sLCRNGState == o->rng, "random state %08x vs %08x", sLCRNGState, o->rng);
    CHECK(p->challengeType == o->challengeType && p->isOpenLevel == o->isOpenLevel && p->currentBattle == o->currentBattle,
          "type/level/battle");
    CHECK(p->currentStreak == o->currentStreak && p->currentRound == o->currentRound && p->tradeCount == o->tradeCount,
          "streak/round/trades %d/%d/%d vs %d/%d/%d", p->currentStreak, p->currentRound, p->tradeCount, o->currentStreak,
          o->currentRound, o->tradeCount);
    CHECK(p->saveStreak == o->saveStreak, "saveStreak");
    for (i = 0; i < 14; i++) {
        CHECK(p->trainerIDs[i] == o->trainerIDs[i], "trainer %d: %d vs %d", i, p->trainerIDs[i], o->trainerIDs[i]);
    }
    for (i = 0; i < 6; i++) {
        CHECK(p->initialRentalSetIDs[i] == o->initialRentalSetIDs[i] && p->initialRentalIVs[i] == o->initialRentalIVs[i] &&
                  p->initialRentalPersonalities[i] == o->initialRentalPersonalities[i],
              "rental %d set/iv/personality", i);
        SameMon(&p->initialRentalMons[i], &o->initialRentalMons[i], "rental", i);
        CHECK(p->playerMonSetIDs[i] == o->playerMonSetIDs[i], "player set %d: %d vs %d", i, p->playerMonSetIDs[i],
              o->playerMonSetIDs[i]);
    }
    for (i = 0; i < 4; i++) {
        CHECK(p->opponentMonSetIDs[i] == o->opponentMonSetIDs[i] && p->opponentMonIVs[i] == o->opponentMonIVs[i] &&
                  p->opponentMonPersonalities[i] == o->opponentMonPersonalities[i],
              "opponent %d set/iv/personality %d vs %d", i, p->opponentMonSetIDs[i], o->opponentMonSetIDs[i]);
        SameMon(&p->opponentMons[i], &o->opponentMons[i], "opponent", i);
    }
    SameParty(p->playersParty, o->playersParty, o->playerCount, "player's party");
    SameParty(p->opponentsParty, o->opponentsParty, o->opponentCount, "opponent's party");
    CHECK(memcmp(&sPlatFrontier.factorySave, save, sizeof(*save)) == 0, "the challenge's save");
    CHECK(memcmp(sPlatFrontier.stats.soloStats, stats, 2 * STATS_NUM_SOLO_STATS_AND_ACTIVE_FLAGS) == 0, "the records");
    CHECK(sPlatFrontier.factory.streakFlags.streakActiveFlags == flags, "the streak flags %02x vs %02x",
          sPlatFrontier.factory.streakFlags.streakActiveFlags, flags);
}

// Platinum's CallBattleFactoryFunction and ours, the same function
static void Function(PlatFactory *o, PlatFactorySave *save, PlatFactoryRecords *rec, u8 fn, u8 a1, u8 a2, int typesToo) {
    u16 ours = 0;
    BOOL done;
    sCtxBytes[0] = fn;
    sCtxBytes[1] = a1;
    sCtxBytes[2] = a2;
    sCtxPos = 0;
    sCtxVar = 0;
    FrontierScriptManager man = { NULL, NULL };
    FrontierScriptContext ctx = { &man };
    FrontierScrCmd_CallBattleFactoryFunction(&ctx);
    done = PlatFactory_Function(o, save, rec, fn, a1, a2, &ours);
    CHECK(done, "function %d not done", fn);
    if (fn == PLATFACTORY_FN_GET_COMMON_TYPE && sB2Types && sCtxVar != 0xff) {
        CHECK(ToB2Type((u8)sCtxVar) == ours, "function %d: %d vs %d (Black 2's numbers)", fn, sCtxVar, ours);
    } else if (typesToo || fn != PLATFACTORY_FN_GET_MONS_TYPE) {
        CHECK(sCtxVar == ours, "function %d (%d, %d): %d vs %d", fn, a1, a2, sCtxVar, ours);
    }
}

static u32 sPick = 1;
static u32 Pick(u32 n) {
    sPick = sPick * 1664525u + 1013904223u;
    return (sPick >> 8) % n;
}

static void LoadFile(const char *path, u8 **out, long *size) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) {
        fprintf(stderr, "%s: can't open\n", path);
        exit(2);
    }
    fseek(f, 0, SEEK_END);
    *size = ftell(f);
    fseek(f, 0, SEEK_SET);
    *out = malloc(*size);
    if (fread(*out, 1, *size, f) != (size_t)*size) {
        exit(2);
    }
    fclose(f);
}

static long sRounds, sBattles, sSwaps, sThorton, sResumes, sLosses, sBP[32];

// One challenge from its start: the round's draws, the rentals, then up to seven battles (a loss at `lose`, a rest at `rest`)
static void Challenge(u32 seed, u8 type, u8 open, u16 round, u16 trades, int lose, int rest) {
    static u16 stats[STATS_NUM_SOLO_STATS_AND_ACTIVE_FLAGS];
    static u8 flags;
    static PlatFactory o;
    static PlatFactorySave save;
    PlatFactoryRecords rec = { stats, &flags };
    BattleFactoryAppArgs args;
    int b, i;
    u16 streak = (u16)(round * 7);

    memset(&sPlatFrontier, 0, sizeof(sPlatFrontier));
    memset(stats, 0, sizeof(stats));
    memset(&save, 0xA5, sizeof(save));
    memcpy(&sPlatFrontier.factorySave, &save, sizeof(save));
    flags = 0;
    if (streak || trades) {         // a streak going on: Platinum reads the latest streak and trade count
        flags = (u8)(1 << (open * 4 + type));
        stats[PlatFactory_LatestStreakStat(open, type)] = streak;
        stats[PlatFactory_LatestTradeCountStat(open, type)] = trades;
        stats[PlatFactory_RecordStreakStat(open, type)] = (u16)(streak + Pick(10));
        stats[PlatFactory_RecordTradeCountStat(open, type)] = (u16)Pick(40);
    }
    memcpy(sPlatFrontier.stats.soloStats, stats, sizeof(stats));
    sPlatFrontier.factory.streakFlags.streakActiveFlags = flags;
    snprintf(sWhere, sizeof(sWhere), "seed %u type %d open %d round %d trades %d: start", seed, type, open, round, trades);

    sLCRNGState = seed;
    sPlat = BattleFactory_Init(NULL, 0, type, open);
    PlatFactory_Init(&o, &save, &rec, 0, type, open, seed);
    BattleFactory_LoadTrainersAndRentalsForRound(sPlat, 0);
    PlatFactory_LoadTrainersAndRentalsForRound(&o, &save, 0);
    Same(sPlat, &o, &save, stats, flags);
    sRounds++;
    Function(&o, &save, &rec, PLATFACTORY_FN_GET_CURRENT_ROUND, 0, 0, 1);
    for (i = 0; i < 3; i++) {
        Function(&o, &save, &rec, PLATFACTORY_FN_GET_MONS_SPECIES, (u8)i, 0, 1);
        Function(&o, &save, &rec, PLATFACTORY_FN_GET_MONS_MOVE, (u8)i, (u8)Pick(4), 1);
    }
    Function(&o, &save, &rec, PLATFACTORY_FN_GET_COMMON_TYPE, 0, 0, 1);
    Function(&o, &save, &rec, PLATFACTORY_FN_GET_MONS_TYPE, (u8)Pick(3), 0, !sB2Types);
    // the rental screen: three of the six
    {
        u16 picks[6] = { 0, 1, 2, 3, 4, 5 };
        for (i = 0; i < 3; i++) {
            u32 j = i + Pick(6 - i);
            u16 t = picks[i];
            picks[i] = picks[j];
            picks[j] = t;
        }
        memset(&args, 0, sizeof(args));
        for (i = 0; i < 6; i++) {
            args.selectedIndices[i] = picks[i];
            o.selectedAppSlots[i] = picks[i];
        }
        BattleFactory_GetMonSelectionAppResult(sPlat, &args);
    }
    BattleFactory_AddSelectedRentalsToParty(sPlat);
    PlatFactory_AddSelectedRentalsToParty(&o);
    snprintf(sWhere, sizeof(sWhere), "seed %u type %d open %d round %d trades %d: rented", seed, type, open, round, trades);
    Same(sPlat, &o, &save, stats, flags);
    CHECK(Plat_GetAIMask(sPlat) == PlatFactory_GetAIMask(&o), "AI mask");

    for (b = 0; b < 7; b++) {
        snprintf(sWhere, sizeof(sWhere), "seed %u type %d open %d round %d trades %d: battle %d", seed, type, open, round,
                 trades, b + 1);
        Function(&o, &save, &rec, PLATFACTORY_FN_GET_NEXT_BATTLE_TYPE, 0, 0, 1);
        if (sCtxVar != PLATFACTORY_NEXT_NORMAL) {
            sThorton++;
            CHECK(o.trainerIDs[o.currentBattle] == (sCtxVar == PLATFACTORY_NEXT_SILVER ? PLATFACTORY_THORTON_SILVER
                                                                                      : PLATFACTORY_THORTON_GOLD),
                  "Thorton's battle: Trainer %d", o.trainerIDs[o.currentBattle]);
        }
        CHECK(Plat_GetAIMask(sPlat) == PlatFactory_GetAIMask(&o), "AI mask");
        sBattles++;
        if (b == lose) {
            Function(&o, &save, &rec, PLATFACTORY_FN_SAVE_ON_LOSS, 0, 0, 1);
            Same(sPlat, &o, &save, stats, flags);
            sLosses++;
            break;
        }
        Function(&o, &save, &rec, PLATFACTORY_FN_INCREMENT_CURRENT_STREAK, 0, 0, 1);
        Function(&o, &save, &rec, PLATFACTORY_FN_INCREMENT_CURRENT_BATTLE, 1, 0, 1);
        Function(&o, &save, &rec, PLATFACTORY_FN_GET_CURRENT_BATTLE, 0, 0, 1);
        if (o.currentBattle >= 7) {
            Function(&o, &save, &rec, PLATFACTORY_FN_SAVE_ON_COMPLETING_ROUND, 0, 0, 1);
            Function(&o, &save, &rec, PLATFACTORY_FN_GET_EARNED_BP, 0, 0, 1);
            if (sCtxVar < 32) {
                sBP[sCtxVar]++;
            }
            Same(sPlat, &o, &save, stats, flags);
            break;
        }
        if (b == rest) {             // the rest: the save, then the challenge resumed from it as after a reset
            Function(&o, &save, &rec, PLATFACTORY_FN_QUICKSAVE, 0, 0, 1);
            Function(&o, &save, &rec, PLATFACTORY_FN_HAS_SAVED, 0, 0, 1);
            Same(sPlat, &o, &save, stats, flags);
            free(sPlat->playersParty);
            free(sPlat->opponentsParty);
            free(sPlat);
            sPlat = BattleFactory_Init(NULL, 1, 0, 0);
            PlatFactory_Init(&o, &save, &rec, 1, 0, 0, sLCRNGState);
            BattleFactory_LoadTrainersAndRentalsForRound(sPlat, 1);
            PlatFactory_LoadTrainersAndRentalsForRound(&o, &save, 1);
            snprintf(sWhere, sizeof(sWhere), "seed %u type %d open %d round %d trades %d: resumed before battle %d", seed,
                     type, open, round, trades, b + 2);
            Same(sPlat, &o, &save, stats, flags);
            Function(&o, &save, &rec, PLATFACTORY_FN_CREATE_OPPONENT_MONS, 0, 0, 1);
            Same(sPlat, &o, &save, stats, flags);
            sResumes++;
            continue;                // (Platinum resumes at the next battle's corridor, the opponent's party as saved)
        }
        BattleFactory_SetupNextOpponent(sPlat);
        PlatFactory_SetupNextOpponent(&o);
        Same(sPlat, &o, &save, stats, flags);
        Function(&o, &save, &rec, PLATFACTORY_FN_GET_COMMON_TYPE, 0, 0, 1);
        Function(&o, &save, &rec, PLATFACTORY_FN_GET_MONS_SPECIES, (u8)Pick(3), 0, 1);
        Function(&o, &save, &rec, PLATFACTORY_FN_GET_MONS_MOVE, (u8)Pick(3), (u8)Pick(4), 1);
        // the swap screen: none, or one of the player's three for one of the beaten opponent's
        memset(&args, 0, sizeof(args));
        if (Pick(4) == 0) {
            args.selectedIndices[0] = 0xff;
        } else {
            args.selectedIndices[0] = (u16)Pick(3);
            args.selectedIndices[1] = (u16)Pick(3);
            sSwaps++;
        }
        for (i = 0; i < 6; i++) {
            o.selectedAppSlots[i] = args.selectedIndices[i];
        }
        BattleFactory_GetMonSelectionAppResult(sPlat, &args);
        BattleFactory_ApplyTrade(sPlat);
        PlatFactory_ApplyTrade(&o);
        BattleFactory_SetupNextOpponentsParty(sPlat);
        PlatFactory_SetupNextOpponentsParty(&o);
        Same(sPlat, &o, &save, stats, flags);
    }
    // the lobby after a challenge not saved: the streak deleted
    if (seed % 5 == 0) {
        static FieldSystem fs;
        ScriptContext sctx = { &fs };
        sScrVars[0] = type;
        sScrVars[1] = open;
        sScrPos = 0;
        ScrCmd_DeleteActiveBattleFactoryStreak(&sctx);
        PlatFactory_DeleteActiveStreak(&rec, type, open);
        snprintf(sWhere, sizeof(sWhere), "seed %u type %d open %d: streak deleted", seed, type, open);
        Same(sPlat, &o, &save, stats, flags);
    }
    free(sPlat->playersParty);
    free(sPlat->opponentsParty);
    free(sPlat);
}

int main(int argc, char **argv) {
    static const u16 trades[] = { 0, 6, 7, 13, 14, 20, 21, 27, 28, 34, 35, 40 };
    u8 *blob;
    long size, ssize;
    u32 seeds, seed;
    u8 type, open;
    u16 round;
    u32 t;

    if (argc < 4) {
        fprintf(stderr, "usage: sim SETS SPECIES SEEDS\n");
        return 2;
    }
    LoadFile(argv[1], &blob, &size);
    {
        u32 trainers, i;
        u8 *p;
        memcpy(&trainers, blob, 4);
        memcpy(&sSetCount, blob + 4, 4);
        p = blob + 8;
        for (i = 0; i < trainers; i++) {
            u16 len;
            memcpy(&len, p, 2);
            p += 2 + 2 * len;
        }
        sSets = p;
    }
    {
        u8 *sp;
        LoadFile(argv[2], &sp, &ssize);
        memcpy(sSpecies, sp, ssize > (long)sizeof(sSpecies) ? (long)sizeof(sSpecies) : ssize);
    }
    seeds = (u32)atoi(argv[3]);
    for (seed = 1; seed <= seeds; seed++) {
        sB2Types = seed & 1;
        for (type = 0; type < 2; type++) {
            for (open = 0; open < 2; open++) {
                for (round = 0; round < 10; round++) {
                    t = trades[(seed + round) % (sizeof(trades) / sizeof(trades[0]))];
                    Challenge(seed * 7919u + round * 131u + type * 17u + open, type, open, round, (u16)t,
                              (int)Pick(10) - 3, (int)Pick(12) - 6);
                }
            }
        }
    }
    printf("%ld rounds started, %ld battles, %ld swaps, %ld Thorton battles, %ld rests resumed, %ld losses\n", sRounds,
           sBattles, sSwaps, sThorton, sResumes, sLosses);
    printf("BP for a round:");
    for (t = 0; t < 32; t++) {
        if (sBP[t]) {
            printf(" %u BP x%ld", t, sBP[t]);
        }
    }
    printf("\n%ld checks, %ld different\n", sChecks, sFails);
    return sFails ? 1 : 0;
}
