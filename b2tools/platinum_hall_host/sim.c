// The Battle Hall's rules, Platinum's own C (plat_rules.c, copied by extract.py) against ours (the decomp's
// src/pearlb2/plat_hall/hall_rules.c, PearlB2's src/pokebw2/ copy, compiled as it is), with the same random numbers.
//
//   sim TABLE PERSONAL TRAINERS NAMES [SEEDS]
//
// TABLE: gPlatHallTable's bytes (platinum_hall_data.py --table, made from the dump); PERSONAL: Platinum's personal abilities
// (--personal); TRAINERS: the core's sets blob (platinum_frontier_data.py --sets: each Frontier Trainer's class); NAMES: the
// Trainers' names as Gen 4 codes (--names: Platinum's AI test reads one, hall_rules.c ArgentaProbe).
// 1. The tables: our table (from the dump) against Platinum's compiled ones (from the decomp's source and Trainer files).
// 2. Every challenge of SEEDS: a save (streak flags, the records, the type ranks, a challenge saved part-way or not) and a
//    party, the same on both sides; Init; then battles as the Hall's scene script runs them (frontier_scripts_battle_hall.s:
//    the type grid's cap, the chosen cell, the base level, the next opponent, the battle's setup with its Pokémon, a win or a
//    loss, the rank of the beaten type, the battle and the streak, the round's save and its BP, the loss's save, the win
//    record), every field compared after every step, and the random state too (the same count of numbers).
// 3. Sweeps: the opponents' level for every level, rank and count of types fought; the next opponent for every cell, rank
//    and battle of the round.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "plat_shim.h"
#undef TRUE
#undef FALSE
#undef NELEMS
#include "pearlb2/plat_hall.h"

// ------------------------------------------------------------------ the data
static PlatHallTable *gTable;
static u8 gPersonal[600][2];
static int gPersonalCount;
static u16 gTrainerClass[400];
static int gTrainerCount;

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

// ------------------------------------------------------------------ Platinum's side: the game around its Hall code
static u32 gPlatLCRNG;
u16 LCRNG_Next(void) {
    gPlatLCRNG = gPlatLCRNG * 1103515245L + 24691;
    return gPlatLCRNG >> 16;
}

fx32 FX_Sqrt(fx32 x) {                      // NitroSDK fx_cp.c: the divider's root of x << 32, rounded to fx32
    if (x <= 0) {
        return 0;
    }
    u64 v = (u64)(u32)x << 32, r = 0, b = (u64)1 << 62;
    while (b > v) {
        b >>= 2;
    }
    while (b) {
        if (v >= r + b) {
            v -= r + b;
            r = (r >> 1) + b;
        } else {
            r >>= 1;
        }
        b >>= 2;
    }
    return (fx32)(((u32)r + 0x200) >> 10);
}

struct SaveData {
    BattleFrontierSave frontier;
    BattleHallWinRecords records;
    Party party;
};
static SaveData gPlatSave;

void *Heap_Alloc(int heapID, u32 size) { (void)heapID; return calloc(1, size); }
void Heap_Free(void *p) { free(p); }
Party *Party_New(int heapID) { (void)heapID; return calloc(1, sizeof(Party)); }
void Party_Init(Party *party) { memset(party, 0, sizeof(Party)); }
void Party_InitWithCapacity(Party *party, int capacity) { (void)capacity; memset(party, 0, sizeof(Party)); }
BOOL Party_AddPokemon(Party *party, Pokemon *mon) { party->mons[party->count++] = *mon; return TRUE; }
Pokemon *Party_GetPokemonBySlotIndex(Party *party, int slot) { return &party->mons[slot]; }
void Party_HealAllMembers(Party *party) { (void)party; }
Pokemon *Pokemon_New(int heapID) { (void)heapID; return calloc(1, sizeof(Pokemon)); }
void Pokemon_Init(Pokemon *mon) { memset(mon, 0, sizeof(Pokemon)); }
void Pokemon_Copy(Pokemon *src, Pokemon *dest) { *dest = *src; }
u32 Pokemon_GetValue(Pokemon *mon, int field, void *dest) {
    (void)dest;
    switch (field) {
    case MON_DATA_SPECIES: return mon->species;
    case MON_DATA_LEVEL: return mon->level;
    case MON_DATA_HELD_ITEM: return mon->item;
    case MON_DATA_PERSONALITY: return mon->personality;
    }
    return 0;
}
void Pokemon_SetValue(Pokemon *mon, int field, const void *value) {
    const u8 *b = value;
    const u16 *h = value;
    const u32 *w = value;
    if (field >= MON_DATA_MOVE1 && field < MON_DATA_MOVE1 + 4) {
        mon->moves[field - MON_DATA_MOVE1] = *h;
        return;
    }
    if (field >= MON_DATA_MOVE1_PP_UPS && field < MON_DATA_MOVE1_PP_UPS + 4) {
        mon->ppUps[field - MON_DATA_MOVE1_PP_UPS] = *b;
        return;
    }
    if (field >= MON_DATA_HP_EV && field <= MON_DATA_SPDEF_EV) {
        mon->evs[field - MON_DATA_HP_EV] = *b;
        return;
    }
    switch (field) {
    case MON_DATA_HELD_ITEM: mon->item = *h; break;
    case MON_DATA_FORM: mon->form = *b; break;
    case MON_DATA_COMBINED_IVS: mon->ivs = *w; break;
    case MON_DATA_OT_ID: mon->otID = *w; break;
    case MON_DATA_ABILITY: mon->ability = *b; break;
    case MON_DATA_FRIENDSHIP: mon->friendship = *b; break;
    }
}
void Pokemon_InitWith(Pokemon *mon, int species, int level, int ivs, BOOL fixedIVs, u32 personality, int otIDType, u32 otID) {
    // ---- plat-arcade (2026-11-07): pokemon.c's Pokemon_InitWith -> sub_02073E18 draws random numbers, and the Hall's
    // BattleHall_SetupBattle makes each opponent's Pokémon with it (FrontierPokemon_InitPokemon): a personality unless one is
    // given, a trainer id until it isn't shiny with it (OTID_NOT_SHINY), and two IV draws when the IVs come as a number of 32 or
    // more. Platinum's real code makes them; this model made none before (and hall_rules.c neither), so the numbers after the
    // first battle's setup were not Platinum's. The values drawn are overwritten after (the set's trainer id, its IVs).
    if (!fixedIVs) {
        LCRNG_Next();
        LCRNG_Next();
    }
    if (otIDType == OTID_NOT_SHINY) {
        u32 drawn;
        do {
            drawn = LCRNG_Next();
            drawn |= (u32)LCRNG_Next() << 16;
        } while (Pokemon_IsPersonalityShiny(drawn, personality));
    }
    if (ivs >= 32) {
        LCRNG_Next();
        LCRNG_Next();
    }
    // ---- end plat-arcade
    (void)fixedIVs; (void)otIDType; (void)otID;
    memset(mon, 0, sizeof(Pokemon));
    mon->species = species;
    mon->level = level;
    mon->ivs = ivs;
    mon->personality = personality;
}
void Pokemon_CalcLevelAndStats(Pokemon *mon) { (void)mon; }
int Plat_GetFormNarcIndex(int species, int form);
void Pokemon_CalcAbility(Pokemon *mon) {        // pokemon.c BoxPokemon_CalcAbility, the form's personal entry
    int i = Plat_GetFormNarcIndex(mon->species, mon->form);
    u8 a1 = gPersonal[i][0], a2 = gPersonal[i][1];
    mon->ability = a2 != ABILITY_NONE && (mon->personality & 1) ? a2 : a1;
}
int SpeciesData_GetSpeciesValue(int species, int param) { return gPersonal[species][param == SPECIES_DATA_ABILITY_2]; }
void *SaveData_SaveTable(SaveData *saveData, int entry) { (void)entry; return &saveData->frontier; }
BattleFrontierSave *SaveData_GetBattleFrontier(SaveData *saveData) { return &saveData->frontier; }
Party *SaveData_GetParty(SaveData *saveData) { return &saveData->party; }
void *SaveData_GetVarsFlags(SaveData *saveData) { return saveData; }
BOOL SystemVars_GetWiFiFrontierCleared(void *varsFlags) { (void)varsFlags; return FALSE; }
static u16 capped(u16 v) { return v > 9999 ? 9999 : v; }        // BattleFrontierSave_SetStat's cap
u16 BattleFrontierSave_GetStatAutoHostIdx(BattleFrontierSave *f, int i) { return f->stats[i]; }
void BattleFrontierSave_SetStatAutoHostIdx(BattleFrontierSave *f, int i, u16 v) { f->stats[i] = capped(v); }
void BattleFrontierSave_SetIfBetterAutoHostIdx(BattleFrontierSave *f, int i, u16 v) { if (v > f->stats[i]) f->stats[i] = capped(v); }
u16 BattleFrontierSave_GetStat(BattleFrontierSave *f, int i, int host) { (void)host; return f->stats[i]; }
int NintendoWFC_GetHostFriendIdx(void) { return 0; }
void BattleFrontier_FlagGeonetLinkInfo(SaveData *saveData) { (void)saveData; }
BattleHallWinRecords *SaveData_BattleHallWinRecords(SaveData *saveData, int heapID, int *resultCode) {
    (void)heapID;
    *resultCode = LOAD_RESULT_OK;
    BattleHallWinRecords *r = malloc(sizeof(BattleHallWinRecords));
    *r = saveData->records;
    return r;
}
int SaveData_SaveBattleHallWinRecords(SaveData *saveData, BattleHallWinRecords *records) { saveData->records = *records; return 0; }
int SaveData_Save(SaveData *saveData) { (void)saveData; return 0; }
BOOL SaveData_MiscSaveBlock_InitFlag(SaveData *saveData) { (void)saveData; return TRUE; }
void BattleFrontier_GetPokemonBase(FrontierPokemonBase *monData, int narcIdx, enum NarcID narcID) {
    if (narcID != NARC_INDEX_BATTLE__B_PL_STAGE__PL_BSDPM) {
        fprintf(stderr, "a set of another facility\n");
        exit(3);
    }
    memcpy(monData, &gTable->sets[narcIdx], sizeof(FrontierPokemonBase));
}
// (BattleFrontier_GetTrainer and BattleFrontier_LoadTrainer are Platinum's own, copied: the Trainer's file and name come from here)
static u16 gNames[400][8];
struct String {
    u16 codes[8];
};
static struct String gNameString;
void *NARC_AllocAndReadWholeMemberByIndexPair(int narcID, int index, int heapID) {
    (void)narcID; (void)heapID;
    FrontierTrainerBase *b = calloc(1, 8);
    b->trainerType = gTrainerClass[index];
    return b;
}
u16 BattleFrontier_GetObjectIDFromTrainerClass(u8 trainerClass) { return trainerClass; }
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
    (void)dto; (void)a; (void)s; (void)m; (void)j; (void)b; (void)c;
}
void FieldBattleDTO_AddPokemonToBattler(FieldBattleDTO *dto, Pokemon *mon, int battler) { Party_AddPokemon(dto->parties[battler], mon); }
void FieldBattleDTO_CopyPlayerInfoToTrainerData(FieldBattleDTO *dto) { (void)dto; }
void FieldBattleDTO_InitFrontierTrainer(FieldBattleDTO *dto, FrontierTrainer *trainer, int partySize, int battler, int heapID) {
    (void)partySize; (void)heapID;
    dto->trainer[battler].trainerID = trainer->trainerID;
}
TrainerInfo *CommInfo_TrainerInfo(int netID) { (void)netID; return NULL; }
int CommSys_CurNetId(void) { return 0; }
void TrainerInfo_Copy(TrainerInfo *src, TrainerInfo *dest) { (void)src; (void)dest; }
MessageLoader *MessageLoader_Init(int mode, int narc, int bank, int heapID) { (void)mode; (void)narc; (void)bank; (void)heapID; return NULL; }
String *MessageLoader_GetNewString(MessageLoader *loader, int id) {  // the Trainers' names bank (TEXT_BANK_FRONTIER_TRAINER_NAMES)
    (void)loader;
    memcpy(gNameString.codes, gNames[id], 16);
    return &gNameString;
}
void String_ToChars(const String *s, u16 *dest, u32 n) {             // up to n characters, the terminator included
    for (u32 i = 0; i < n; i++) {
        dest[i] = s->codes[i];
        if (s->codes[i] == 0xffff) {
            break;
        }
    }
}
void MessageLoader_Free(MessageLoader *loader) { (void)loader; }
void MessageLoader_GetSpeciesName(int species, int heapID, u16 *dest) { (void)species; (void)heapID; dest[0] = 0xffff; }
void String_Free(String *s) { (void)s; }

// Platinum's code reached by extract.py's wrappers and its own public functions
void Plat_SetupNextOpponent(BattleHall *bh);
u16 Plat_CalcOpponentsLevel(BattleHall *bh);
u16 Plat_GetAIMask(BattleHall *bh, u8 battleNum, u8 rank);
u32 Plat_GetOpponentLevel(BattleHall *bh);
int Plat_OpponentCount(void);
u16 Plat_Opponent(int i);
u16 Plat_OpponentType(int i, int j);
u16 Plat_ClassByRank(int r, int c);
u16 Plat_ClassByType(int t, int c);
int Plat_FrontierClassCount(void);
u16 Plat_FrontierClass(int i);

// ------------------------------------------------------------------ our side: the save as the core keeps it
typedef struct {
    u16 stats[200];
    u8 streakFlags;
    u16 records[2 * PLAT_HALL_WIN_SPECIES];
} OurSave;
static OurSave gOurSave;
static PlatHallWork gWork;

u16 PlatHall_GetStat(void *save, u32 stat) { return ((OurSave *)save)->stats[stat]; }
void PlatHall_SetStat(void *save, u32 stat, u16 value) { ((OurSave *)save)->stats[stat] = value > 9999 ? 9999 : value; }
u32 PlatHall_GetStreakFlag(void *save, u32 type) { return (((OurSave *)save)->streakFlags >> type) & 1; }
void PlatHall_SetStreakFlag(void *save, u32 type, u32 value) {
    OurSave *s = save;
    if (value >= 1) {
        s->streakFlags |= 1 << type;
    } else {
        s->streakFlags &= 0xff ^ (1 << type);
    }
}
u16 *PlatHall_WinRecords(void *save) { return ((OurSave *)save)->records; }

// ------------------------------------------------------------------ the checks
static long gChecks, gProblems;
static const char *gWhere;
static unsigned gSeed;
#define CHECK(cond, ...)                                                                                                    \
    do {                                                                                                                   \
        gChecks++;                                                                                                         \
        if (!(cond)) {                                                                                                     \
            if (gProblems++ < 30) {                                                                                        \
                printf("DIFF seed %u at %s: ", gSeed, gWhere);                                                             \
                printf(__VA_ARGS__);                                                                                       \
                printf("\n");                                                                                              \
            }                                                                                                              \
        }                                                                                                                  \
    } while (0)

static u32 gRng;                            // the harness's own choices (not the rules')
static u32 pick(u32 n) {
    gRng = gRng * 1664525u + 1013904223u;
    return (gRng >> 8) % n;
}

static void compare_state(BattleHall *bh, int type) {
    PlatHallWork *w = &gWork;
    CHECK(gPlatLCRNG == w->lcrng, "random state %08x / %08x", gPlatLCRNG, w->lcrng);
    CHECK(bh->challengeType == w->challengeType && bh->currentBattle == w->currentBattle && bh->saveStreak == w->saveStreak,
          "type/battle/saveStreak %d %d %d / %d %d %d", bh->challengeType, bh->currentBattle, bh->saveStreak, w->challengeType,
          w->currentBattle, w->saveStreak);
    CHECK(bh->currentStreak == w->currentStreak && bh->currentRound == w->currentRound, "streak/round %d %d / %d %d",
          bh->currentStreak, bh->currentRound, w->currentStreak, w->currentRound);
    CHECK(bh->opponentsLevel == w->opponentsLevel, "opponents' level %d / %d", bh->opponentsLevel, w->opponentsLevel);
    CHECK(bh->playerLevelSqrt == w->playerLevelSqrt, "level root %d / %d", bh->playerLevelSqrt, w->playerLevelSqrt);
    CHECK(!memcmp(bh->trainerIDs, w->trainerIDs, sizeof(w->trainerIDs)), "trainer ids");
    CHECK(!memcmp(bh->monIndices, w->monIndices, sizeof(w->monIndices)), "Pokemon indices");
    CHECK(bh->partySlots[0] == w->partySlots[0] && bh->partySlots[1] == w->partySlots[1], "party slots");
    CHECK(bh->selectedTypeIdx2 == w->selectedTypeIdx2 && bh->selectedType == w->selectedType &&
          bh->selectedTypeIdx == w->selectedTypeIdx, "selected cell");
    CHECK(!memcmp(bh->typeRanks[type], w->typeRanks[type], 9), "type ranks");
    BattleHallSave *ps = &gPlatSave.frontier.hallSave;
    PlatHallSave *os = &w->save;
    CHECK(ps->challengeType == os->challengeType && ps->didSave == os->didSave && ps->currentBattleNum == os->currentBattleNum &&
          ps->partySlots[0] == os->partySlots[0] && ps->partySlots[1] == os->partySlots[1] &&
          !memcmp(ps->trainerIDs, os->trainerIDs, sizeof(os->trainerIDs)) &&
          !memcmp(ps->monIndices, os->monIndices, sizeof(os->monIndices)), "the saved challenge");
    CHECK(!memcmp(gPlatSave.frontier.stats, gOurSave.stats, sizeof(gOurSave.stats)), "the records (stats)");
    CHECK(gPlatSave.frontier.hall.streakFlags.streakActiveFlags == gOurSave.streakFlags, "streak flags %x / %x",
          gPlatSave.frontier.hall.streakFlags.streakActiveFlags, gOurSave.streakFlags);
    CHECK(!memcmp(gPlatSave.records.singleStreaks, gOurSave.records, 2 * PLAT_HALL_WIN_SPECIES) &&
          !memcmp(gPlatSave.records.doubleStreaks, gOurSave.records + PLAT_HALL_WIN_SPECIES, 2 * PLAT_HALL_WIN_SPECIES),
          "the win records");
}

static void check_tables(void) {
    gWhere = "tables";
    CHECK(Plat_OpponentCount() == gTable->opponentCount && gTable->opponentCount == PLAT_HALL_OPPONENTS, "opponent count");
    for (int i = 0; i < Plat_OpponentCount(); i++) {
        CHECK(Plat_Opponent(i) == gTable->opponents[i], "opponent %d", i);
        CHECK(Plat_OpponentType(i, 0) == gTable->opponentTypes[i][0] && Plat_OpponentType(i, 1) == gTable->opponentTypes[i][1],
              "opponent %d's types", i);
    }
    for (int r = 0; r < PLAT_HALL_MAX_RANK; r++) {
        for (int c = 0; c < 8; c++) {
            CHECK(Plat_ClassByRank(r, c) == gTable->classesByRank[r][c], "class by rank %d %d", r, c);
        }
    }
    for (int t = 0; t < PLAT_HALL_TYPES; t++) {
        for (int c = 0; c < 4; c++) {
            CHECK(Plat_ClassByType(t, c) == gTable->classesByType[t][c], "class by type %d %d", t, c);
        }
    }
    CHECK(Plat_FrontierClassCount() == gTable->trainerClassCount, "Frontier classes' count");
    for (int i = 0; i < Plat_FrontierClassCount(); i++) {
        CHECK(Plat_FrontierClass(i) == gTable->trainerClasses[i], "Frontier Trainer %d's class", i);
    }
    for (int c = 0; c < PLAT_HALL_GRID_CELLS; c++) {
        CHECK(BattleHall_CursorPosToType(c) == PlatHall_CursorPosToType(c), "grid cell %d", c);
    }
    for (int i = 0; i < PLAT_HALL_TRAINER_CLASSES; i++) {
        u8 f = (gNames[i][0] == 307 || gNames[i][0] == 308 ? 1 : 0) | (gNames[i][4] == 307 || gNames[i][4] == 308 ? 2 : 0);
        CHECK(f == gTable->nameFlags[i], "Trainer %d's name flags", i);
    }
    for (int i = 0; i < PLAT_HALL_SETS; i++) {
        int p = Plat_GetFormNarcIndex(gTable->sets[i].species, gTable->sets[i].form);
        CHECK(gPersonal[p][0] == gTable->setAbilities[i][0] && gPersonal[p][1] == gTable->setAbilities[i][1], "set %d's abilities", i);
    }
    for (int t = 0; t < 3; t++) {
        CHECK(BattleFrontierStats_GetHallCurrentStreakIndex(t) == PlatHall_StatIndex(t, PLAT_HALL_STAT_CURRENT) &&
              BattleFrontierStats_GetHallLatestStreakIndex(t) == PlatHall_StatIndex(t, PLAT_HALL_STAT_LATEST) &&
              BattleFrontierStats_GetHallLatestSpeciesIndex(t) == PlatHall_StatIndex(t, PLAT_HALL_STAT_SPECIES), "record ids %d", t);
        for (int ty = 0; ty < PLAT_HALL_TYPES; ty++) {
            CHECK(BattleFrontierStats_GetHallCurrentTypeRanksIndex(t, ty) == PlatHall_StatIndex(t, PLAT_HALL_STAT_RANKS + ty / 2),
                  "rank record id %d %d", t, ty);
        }
    }
}

// The party: two Pokémon (Double enters both), the same on both sides
static void make_party(void) {
    memset(&gPlatSave.party, 0, sizeof(Party));
    gPlatSave.party.count = 6;
    for (int i = 0; i < 6; i++) {
        Pokemon *m = &gPlatSave.party.mons[i];
        // species: often one of the Hall's own (its group decides Argenta's Silver opponent), sometimes any
        m->species = pick(3) ? gTable->opponents[pick(PLAT_HALL_OPPONENTS)] : 1 + pick(493);
        u32 r = pick(10);
        m->level = r < 2 ? 100 : r < 3 ? 50 : r < 4 ? 1 + pick(20) : 30 + pick(71);
        m->item = pick(4) ? pick(400) : 0;
    }
}

// A save as a player might have it: records, flags, ranks, a challenge saved part-way
static void make_save(void) {
    memset(&gPlatSave.frontier, 0, sizeof(gPlatSave.frontier));
    memset(&gPlatSave.records, 0, sizeof(gPlatSave.records));
    for (int t = 0; t < 3; t++) {
        u16 latest;
        u32 r = pick(6);
        latest = r == 0 ? 0 : r == 1 ? 40 + pick(10) : r == 2 ? 160 + pick(10) : r == 3 ? pick(400) : pick(30);
        latest -= latest % 10;              // (a streak saved between rounds is a round's end)
        gPlatSave.frontier.stats[PlatHall_StatIndex(t, 0)] = latest + pick(3) * 10;
        gPlatSave.frontier.stats[PlatHall_StatIndex(t, 1)] = latest;
        gPlatSave.frontier.stats[PlatHall_StatIndex(t, 2)] = 1 + pick(493);
        for (int k = 0; k < 9; k++) {
            u8 lo = pick(11), hi = pick(11);
            gPlatSave.frontier.stats[PlatHall_StatIndex(t, 3 + k)] = (u16)(lo | hi << 4);
        }
        if (pick(2)) {
            gPlatSave.frontier.hall.streakFlags.streakActiveFlags |= 1 << t;
        }
    }
    for (int s = 0; s < 40; s++) {
        int sp = pick(MAX_SPECIES);
        gPlatSave.records.singleStreaks[sp] = pick(300);
        gPlatSave.records.doubleStreaks[pick(MAX_SPECIES)] = pick(300);
    }
    BattleHallSave *hs = &gPlatSave.frontier.hallSave;
    hs->challengeType = pick(2);
    hs->didSave = pick(2);
    hs->currentBattleNum = pick(10);
    hs->partySlots[0] = pick(6);
    hs->partySlots[1] = pick(6);
    for (int i = 0; i < 20; i++) {
        hs->trainerIDs[i] = pick(300);
        hs->monIndices[i] = 1 + pick(PLAT_HALL_OPPONENTS);          // (above 255 too: the resume's u8 cast)
    }
    // ours: the same bytes, as the core keeps them
    memcpy(gOurSave.stats, gPlatSave.frontier.stats, sizeof(gOurSave.stats));
    gOurSave.streakFlags = gPlatSave.frontier.hall.streakFlags.streakActiveFlags;
    memcpy(gOurSave.records, gPlatSave.records.singleStreaks, 2 * PLAT_HALL_WIN_SPECIES);
    memcpy(gOurSave.records + PLAT_HALL_WIN_SPECIES, gPlatSave.records.doubleStreaks, 2 * PLAT_HALL_WIN_SPECIES);
}

static void our_party(PlatHallWork *w) {        // what the field reads from the party at each op (hall_field.c)
    w->levels[0] = gPlatSave.party.mons[w->partySlots[0]].level;
    w->levels[1] = gPlatSave.party.mons[w->partySlots[1]].level;
    w->species = gPlatSave.party.mons[w->partySlots[0]].species;
}

static long gBattles, gMons, gArgenta, gRankUps, gRounds, gLosses, gResumes;

// One challenge, as the scene script runs it
static void challenge(void) {
    BattleHall *bh;
    PlatHallWork *w = &gWork;
    u16 resuming = gPlatSave.frontier.hallSave.didSave && pick(3) == 0;
    u8 type = resuming ? gPlatSave.frontier.hallSave.challengeType : pick(2);
    u8 slot1 = pick(6), slot2 = (slot1 + 1 + pick(5)) % 6;
    u32 seed = pick(0xffffffff);

    gResumes += resuming;
    memset(w, 0, sizeof(*w));
    memcpy(&w->save, &gPlatSave.frontier.hallSave, sizeof(PlatHallSave));
    gWhere = "Init";
    gPlatLCRNG = seed;
    w->lcrng = seed;
    bh = BattleHall_Init(&gPlatSave, resuming, type, slot1, slot2);
    PlatHall_Init(w, &gOurSave, resuming, type, slot1, slot2);
    our_party(w);
    compare_state(bh, bh->challengeType);
    type = bh->challengeType;

    for (int battle = 0; battle < 40; battle++) {
        // the grid: the cap, a cell the grid lets the player pick
        gWhere = "the type grid";
        BattleHall_CapTypeRanks(bh);
        PlatHall_CapTypeRanks(w);
        compare_state(bh, type);
        int cell = -1;
        for (int tries = 0; tries < 200 && cell < 0; tries++) {
            int c = pick(PLAT_HALL_GRID_TYPES);
            if (BattleHall_GetRankOfType(c, bh->typeRanks[type]) < HALL_MAX_TYPE_RANK) {   // the app's own test
                cell = c;
            }
        }
        if (cell < 0) {
            break;
        }
        CHECK(PlatHall_TypeCellCheck(w, cell) != 1, "a cell the grid allows is refused");
        BattleHallAppArgs args = { 0 };
        args.selectedCell = cell;
        BattleHall_GetTypeSelectionAppResult(bh, &args);
        PlatHall_SetSelectedCell(w, cell);
        // OpenBattleHallApp's party: the first entered Pokémon (and the second's in a Double)
        Party_Init(bh->party);
        Party_AddPokemon(bh->party, &gPlatSave.party.mons[bh->partySlots[0]]);
        our_party(w);
        gWhere = "the base level";
        BattleHall_CalcPlayerLevelSqrt(bh);
        PlatHall_CalcPlayerLevelSqrt(w);
        compare_state(bh, type);
        gWhere = "the next opponent";
        BattleHall_SetupNextOpponent(bh, 0);
        PlatHall_SetupNextOpponent(w, gTable);
        compare_state(bh, type);
        u8 offset = bh->currentBattle * 2;
        gArgenta += bh->trainerIDs[offset] >= 307;
        // BH_FUNC_LOAD_TRAINERS (the script, before the intro), then the battle's setup: Platinum's own BattleHall_SetupBattle
        BattleFrontier_LoadTrainer(&bh->opponents[0], bh->trainerIDs[bh->currentBattle * 2], HEAP_ID_FIELD2,
                                   NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDTR);
        BattleFrontier_LoadTrainer(&bh->opponents[1], bh->trainerIDs[bh->currentBattle * 2 + 1], HEAP_ID_FIELD2,
                                   NARC_INDEX_BATTLE__B_PL_TOWER__PL_BTDTR);
        gWhere = "the battle's setup";
        FieldFrontierDTO fd = { 0 };
        fd.saveData = &gPlatSave;
        FieldBattleDTO *dto = BattleHall_SetupBattle(bh, &fd);
        u8 rank = PlatHall_GetBattleRank(w);
        u16 ai = PlatHall_GetAIMask(w, gTable, rank);
        PlatHall_MakeOpponents(w, gTable);
        compare_state(bh, type);
        CHECK(dto->trainer[1].header.aiMask == ai, "AI %x / %x", dto->trainer[1].header.aiMask, ai);
        CHECK(dto->trainer[1].trainerID == w->trainerIDs[offset], "the opponent %d / %d", dto->trainer[1].trainerID,
              w->trainerIDs[offset]);
        Party *enemy = dto->parties[BATTLER_ENEMY_1];
        CHECK(enemy->count == (type == 1 ? 2 : 1), "the opponent's party size %d", enemy->count);
        for (int i = 0; i < enemy->count; i++) {
            Pokemon *m = &enemy->mons[i];
            PlatHallMon *o = &w->mons[i];
            gMons++;
            CHECK(m->species == o->species && m->form == o->form && m->item == o->item, "Pokemon %d: species %d %d / %d %d", i,
                  m->species, m->form, o->species, o->form);
            CHECK(!memcmp(m->moves, o->moves, sizeof(o->moves)), "Pokemon %d: moves", i);
            CHECK(m->personality == o->personality && m->otID == o->otID, "Pokemon %d: personality %08x %08x / %08x %08x", i,
                  m->personality, m->otID, o->personality, o->otID);
            u32 ivs = o->ivs * 0x2108421u & 0x3fffffff;             // every stat's IV in its five bits
            CHECK((m->ivs & 0x3fffffff) == ivs, "Pokemon %d: IVs %08x / %08x", i, m->ivs, ivs);
            CHECK(!memcmp(m->evs, o->evs, 6), "Pokemon %d: EVs", i);
            CHECK(m->ability == o->ability && m->friendship == o->friendship, "Pokemon %d: ability %d friendship %d / %d %d", i,
                  m->ability, m->friendship, o->ability, o->friendship);
            CHECK(m->level == PlatHall_GetOpponentLevel(w), "Pokemon %d: level %d / %d", i, m->level, PlatHall_GetOpponentLevel(w));
            CHECK(Pokemon_GetNatureOf(m->personality) == o->nature, "Pokemon %d: nature", i);
        }
        for (int i = 0; i < MAX_BATTLERS; i++) {
            free(dto->parties[i]);
        }
        free(dto);
        gBattles++;
        // the battle's end
        BOOL won = pick(100) < 88;
        if (won) {
            gWhere = "a win";
            u8 before = BattleHall_GetRankOfType(bh->selectedTypeIdx, bh->typeRanks[type]);
            // BH_FUNC_INCREMENT_RANK_OF_BEATEN_TYPE (CallBattleHallFunction's own lines)
            u8 r = BattleHall_GetRankOfType(bh->selectedTypeIdx, &bh->typeRanks[bh->challengeType][0]);
            if (r < HALL_MAX_TYPE_RANK) {
                BattleHall_SetRankOfType(bh->selectedTypeIdx, &bh->typeRanks[bh->challengeType][0], r + 1);
            }
            PlatHall_IncrementRankOfBeatenType(w);
            gRankUps += BattleHall_GetRankOfType(bh->selectedTypeIdx, bh->typeRanks[type]) != before;
            BattleHall_IncrementCurrentBattle(bh);
            w->currentBattle++;
            if (bh->currentStreak < 9999) {             // BH_FUNC_INCREMENT_CURRENT_STREAK
                bh->currentStreak++;
            }
            if (w->currentStreak < 9999) {
                w->currentStreak++;
            }
            compare_state(bh, type);
            CHECK(PlatHall_GetNextBattleType(w) == (type == 0 && bh->currentStreak + 1 == 50 ? 1 :
                                                     type == 0 && bh->currentStreak + 1 == 170 ? 2 : 0), "next battle type");
            if (bh->currentBattle == HALL_BATTLES_PER_ROUND) {
                gWhere = "the round's save";
                BattleHall_SaveOnCompletingRound(bh);
                PlatHall_SaveOnCompletingRound(w, &gOurSave);
                compare_state(bh, type);
                CHECK(BattleHall_GetEarnedBP(bh) == PlatHall_GetEarnedBP(w), "BP %d / %d", BattleHall_GetEarnedBP(bh),
                      PlatHall_GetEarnedBP(w));
                gRounds++;
                if (pick(4) == 0) {
                    break;                      // a rest: the challenge resumes from the save later
                }
            }
        } else {
            gWhere = "a loss";
            BattleHall_SaveOnLoss(bh);
            PlatHall_SaveOnLoss(w, &gOurSave);
            compare_state(bh, type);
            u16 updated = 0;
            BattleHall_UpdateWinRecordForCurrentMon(bh, &updated);
            CHECK(updated == PlatHall_UpdateWinRecord(w, &gOurSave), "win record's answer");
            compare_state(bh, type);
            gLosses++;
            break;
        }
    }
    free(bh->party);
    free(bh->partnersMon);
    free(bh);
}

// The opponents' level for every level, rank and count of types fought
static void sweep_levels(void) {
    BattleHall bh;
    PlatHallWork *w = &gWork;
    gWhere = "the level sweep";
    for (int type = 0; type < 2; type++) {
        for (int level = 1; level <= 100; level++) {
            for (int rank = 0; rank <= 10; rank++) {
                for (int fought = 0; fought <= 17; fought++) {
                    memset(&bh, 0, sizeof(bh));
                    memset(w, 0, sizeof(*w));
                    bh.challengeType = w->challengeType = type;
                    bh.selectedTypeIdx = w->selectedTypeIdx = pick(17);
                    for (int t = 0; t < 18; t++) {
                        u8 v = t == bh.selectedTypeIdx ? rank : (t <= fought ? 1 + pick(10) : 0);
                        BattleHall_SetRankOfType(t, bh.typeRanks[type], v);
                        PlatHall_SetRankOfType(t, w->typeRanks[type], v);
                    }
                    Pokemon *m = &gPlatSave.party.mons[0];
                    m->level = level;
                    gPlatSave.party.mons[1].level = 1 + pick(100);
                    bh.saveData = &gPlatSave;
                    bh.partySlots[1] = w->partySlots[1] = 1;
                    w->levels[0] = level;
                    w->levels[1] = gPlatSave.party.mons[1].level;
                    BattleHall_CalcPlayerLevelSqrt(&bh);
                    PlatHall_CalcPlayerLevelSqrt(w);
                    CHECK(bh.playerLevelSqrt == w->playerLevelSqrt, "root of %d: %d / %d", level, bh.playerLevelSqrt, w->playerLevelSqrt);
                    CHECK(Plat_CalcOpponentsLevel(&bh) == PlatHall_CalcOpponentsLevel(w), "level %d rank %d fought %d: %d / %d",
                          level, rank, fought, Plat_CalcOpponentsLevel(&bh), PlatHall_CalcOpponentsLevel(w));
                }
            }
        }
    }
}

// The next opponent for every cell, rank and battle of a round, with Argenta's battles
static void sweep_opponents(void) {
    BattleHall *bh = calloc(1, sizeof(BattleHall));
    PlatHallWork *w = &gWork;
    bh->party = Party_New(0);
    bh->saveData = &gPlatSave;
    gWhere = "the opponent sweep";
    for (int type = 0; type < 2; type++) {
        for (int cell = 0; cell < PLAT_HALL_GRID_TYPES; cell++) {
            for (int rank = 0; rank <= 10; rank++) {
                for (int battle = 0; battle < 10; battle++) {
                    for (int round = 0; round < 19; round++) {
                        u32 seed = pick(0xffffffff);
                        memset(w, 0, sizeof(*w));
                        u16 sp = gTable->opponents[pick(PLAT_HALL_OPPONENTS)];
                        Pokemon *m = &gPlatSave.party.mons[0];
                        m->species = sp;
                        m->level = 1 + pick(100);
                        bh->challengeType = w->challengeType = type;
                        bh->currentBattle = w->currentBattle = battle;
                        bh->currentRound = w->currentRound = round;
                        bh->currentStreak = w->currentStreak = round * 10 + battle;
                        bh->partySlots[0] = w->partySlots[0] = 0;
                        bh->partySlots[1] = w->partySlots[1] = 1;
                        for (int i = 0; i < 20; i++) {
                            bh->trainerIDs[i] = w->trainerIDs[i] = i < battle * 2 ? pick(300) : 0;
                            bh->monIndices[i] = w->monIndices[i] = i < battle * 2 ? 1 + pick(PLAT_HALL_OPPONENTS) : 0;
                        }
                        memset(bh->typeRanks, 0, sizeof(bh->typeRanks));
                        BattleHall_SetRankOfType(cell, bh->typeRanks[type], rank);
                        PlatHall_SetRankOfType(cell, w->typeRanks[type], rank);
                        BattleHallAppArgs args = { 0 };
                        args.selectedCell = cell;
                        BattleHall_GetTypeSelectionAppResult(bh, &args);
                        PlatHall_SetSelectedCell(w, cell);
                        Party_Init(bh->party);
                        Party_AddPokemon(bh->party, m);
                        w->levels[0] = m->level;
                        w->levels[1] = gPlatSave.party.mons[1].level;
                        w->species = sp;
                        bh->playerLevelSqrt = w->playerLevelSqrt = FX_Sqrt(m->level << 12);
                        gPlatLCRNG = w->lcrng = seed;
                        Plat_SetupNextOpponent(bh);
                        PlatHall_SetupNextOpponent(w, gTable);
                        CHECK(gPlatLCRNG == w->lcrng && !memcmp(bh->trainerIDs, w->trainerIDs, 40) &&
                              !memcmp(bh->monIndices, w->monIndices, 40) && bh->opponentsLevel == w->opponentsLevel,
                              "cell %d rank %d battle %d round %d", cell, rank, battle, round);
                        gArgenta += bh->trainerIDs[battle * 2] >= 307;
                    }
                }
            }
        }
    }
    free(bh->party);
    free(bh);
}

int main(int argc, char **argv) {
    long size;
    if (argc < 5) {
        fprintf(stderr, "sim TABLE PERSONAL TRAINERS NAMES [SEEDS]\n");
        return 2;
    }
    gTable = slurp(argv[1], &size);
    if (size != (long)sizeof(PlatHallTable) || gTable->magic != PLAT_HALL_MAGIC) {
        fprintf(stderr, "%s: %ld bytes, PlatHallTable is %zu\n", argv[1], size, sizeof(PlatHallTable));
        return 2;
    }
    u8 *per = slurp(argv[2], &size);
    gPersonalCount = per[0] | per[1] << 8;
    memcpy(gPersonal, per + 2, gPersonalCount * 2);
    u8 *tr = slurp(argv[3], &size);         // u32 Trainers, u32 sets, then each Trainer's u16 length and u16s (class first)
    gTrainerCount = tr[0] | tr[1] << 8;
    u8 *p = tr + 8;
    for (int i = 0; i < gTrainerCount; i++) {
        int n = p[0] | p[1] << 8;
        gTrainerClass[i] = p[2] | p[3] << 8;
        p += 2 + 2 * n;
    }
    u8 *nm = slurp(argv[4], &size);         // u16 count, then 8 u16 Gen 4 codes each
    for (int i = 0; i < (nm[0] | nm[1] << 8); i++) {
        memcpy(gNames[i], nm + 2 + 16 * i, 16);
    }
    int seeds = argc > 5 ? atoi(argv[5]) : 1000;

    check_tables();
    printf("tables: %ld checks, %ld differences\n", gChecks, gProblems);
    for (gSeed = 1; gSeed <= (unsigned)seeds; gSeed++) {
        gRng = gSeed * 2654435761u;
        make_save();
        make_party();
        for (int c = 0; c < 4; c++) {
            challenge();
        }
    }
    printf("challenges: %d seeds x 4 (%ld resumed): %ld battles, %ld opponents' Pokemon, %ld rank-ups, %ld rounds, %ld losses, "
           "Argenta %ld times\n", seeds, gResumes, gBattles, gMons, gRankUps, gRounds, gLosses, gArgenta);
    gArgenta = 0;
    sweep_levels();
    sweep_opponents();
    printf("sweeps: levels 1-100 x ranks 0-10 x types fought, opponents for every cell, rank, battle and round (Argenta %ld)\n",
           gArgenta);
    printf("%ld checks, %ld differences\n", gChecks, gProblems);
    return gProblems != 0;
}
