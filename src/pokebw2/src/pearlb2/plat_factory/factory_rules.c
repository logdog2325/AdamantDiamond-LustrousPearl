#if !defined(PEARLB2_HOST)
#include "pearlb2.h"     // (plat-frontier-rooms: PEARLB2 0 leaves this file out, as factory.c)
#endif
#include "pearlb2/plat_factory.h"
#include "types.h"

// Platinum's Battle Factory rules (include/pearlb2/plat_factory.h), function for function from pokeplatinum:
// src/overlay104/battle_factory.c, battle_factory_helpers.c, frontier_opponents.c (the sets made into Pokémon),
// frscrcmd_battle_factory.c (CallBattleFactoryFunction), src/scrcmd_battle_factory.c, src/battle_frontier_stats.c and
// src/battle_frontier_save.c (the records). Platinum's names are kept in the comments. What differs:
// - The random numbers are Platinum's LCRNG on the challenge's own state (Platinum's is the game's global one).
// - A Pokémon is kept as it was made from its set (PlatFactoryMon); Platinum makes a Pokemon of it at the challenge's level
//   (FrontierPokemon_InitPokemon), which draws random numbers of its own (a trainer id that isn't shiny with the
//   personality, then random IVs it overwrites). Those draws are made here too, in the same places
//   (InitPokemonRandom), so the numbers after them are Platinum's.
// - Only what a solo challenge does: the multi challenges are the wireless and Wi-Fi ones, closed here (the partner's
//   rentals, the link messages and the link's round are left out).
// This file needs nothing of Black 2: b2tools/platinum_factory_host compiles it on the host beside Platinum's own C.

#if !defined(PEARLB2) || PEARLB2

#define TRAINER_YOUNGSTER_JIM 0
#define TRAINER_HIKER_RAIDEN 80
#define TRAINER_REPORTER_GINGHAM 99
#define TRAINER_CYCLIST_GASPAR 100
#define TRAINER_SOCIALITE_CARMEN 119
#define TRAINER_PSYCHIC_ALPHA 120
#define TRAINER_CLOWN_PRESCOT 139
#define TRAINER_ACE_TRAINER_YARDLEY 140
#define TRAINER_ACE_TRAINER_DANIELA 159
#define TRAINER_YOUNGSTER_KADEN 160
#define TRAINER_IDOL_UTAH 179
#define TRAINER_JOGGER_COLT 180
#define TRAINER_PI_SERGEI 199
#define TRAINER_CAMPER_FREDDY 200
#define TRAINER_BREEDER_ANTONIA 219
#define TRAINER_ACE_TRAINER_SAWYER 220
#define TRAINER_VETERAN_ALFRED 239
#define TRAINER_IDOL_NISSA 299
#define TRAINER_TRAINER_CHERYL_CHERYL 300
#define TRAINER_ARCADE_STAR_DAHLIA_SILVER 311

#define MAX_EVS_ALL_STATS 510
#define MAX_EVS_SINGLE_STAT 255
#define MOVE_FRUSTRATION 218
#define NATURE_COUNT 25
#define STAT_MAX 6
#define STATS_NUM_SOLO 112
#define STAT_VALUE_MAX 9999
#define STAT_FACTORY_FIRST 10           // STAT_FACTORY_RECORD_STREAK_50_SINGLE
#define LCRNG_MULTIPLIER 1103515245
#define LCRNG_INCREMENT 24691

typedef struct {
    u16 normalMin;
    u16 normalMax;
    u16 finalMin;
    u16 finalMax;
} OpponentPool;

// Platinum's BattleFactoryPokemonPool
typedef struct {
    u16 trainerIDMax;
    u16 setIDMin;
    u16 setIDMax;
    u8 ivs;
    u8 canBeUpgraded;
} PokemonPool;

// sBattleFactoryOpponentPools
static const OpponentPool sOpponentPools[] = {
    { TRAINER_YOUNGSTER_JIM, TRAINER_REPORTER_GINGHAM, TRAINER_CYCLIST_GASPAR, TRAINER_SOCIALITE_CARMEN },
    { TRAINER_HIKER_RAIDEN, TRAINER_SOCIALITE_CARMEN, TRAINER_PSYCHIC_ALPHA, TRAINER_CLOWN_PRESCOT },
    { TRAINER_CYCLIST_GASPAR, TRAINER_CLOWN_PRESCOT, TRAINER_ACE_TRAINER_YARDLEY, TRAINER_ACE_TRAINER_DANIELA },
    { TRAINER_PSYCHIC_ALPHA, TRAINER_ACE_TRAINER_DANIELA, TRAINER_YOUNGSTER_KADEN, TRAINER_IDOL_UTAH },
    { TRAINER_ACE_TRAINER_YARDLEY, TRAINER_IDOL_UTAH, TRAINER_JOGGER_COLT, TRAINER_PI_SERGEI },
    { TRAINER_YOUNGSTER_KADEN, TRAINER_PI_SERGEI, TRAINER_CAMPER_FREDDY, TRAINER_BREEDER_ANTONIA },
    { TRAINER_JOGGER_COLT, TRAINER_BREEDER_ANTONIA, TRAINER_ACE_TRAINER_SAWYER, TRAINER_VETERAN_ALFRED },
    { TRAINER_CAMPER_FREDDY, TRAINER_IDOL_NISSA, TRAINER_CAMPER_FREDDY, TRAINER_IDOL_NISSA },
};

// sLevel50Pools: the rentals of a round (by round) and an opponent's Pokémon (by the Trainer's id)
static const PokemonPool sLevel50Pools[] = {
    { TRAINER_CYCLIST_GASPAR, 1, 150, 0, TRUE },
    { TRAINER_PSYCHIC_ALPHA, 151, 250, 4, TRUE },
    { TRAINER_ACE_TRAINER_YARDLEY, 251, 350, 8, TRUE },
    { TRAINER_YOUNGSTER_KADEN, 351, 486, 12, TRUE },
    { TRAINER_JOGGER_COLT, 487, 622, 16, TRUE },
    { TRAINER_CAMPER_FREDDY, 623, 758, 20, TRUE },
    { TRAINER_ACE_TRAINER_SAWYER, 759, 894, 24, TRUE },
    { TRAINER_TRAINER_CHERYL_CHERYL, 351, 950, 31, FALSE },
    { PLATFACTORY_THORTON_GOLD, 351, 486, 12, FALSE },
    { TRAINER_ARCADE_STAR_DAHLIA_SILVER, 351, 486, 31, FALSE },
};

// sOpenLevelOpponentPools
static const PokemonPool sOpenLevelOpponentPools[] = {
    { TRAINER_CYCLIST_GASPAR, 351, 486, 0, TRUE },
    { TRAINER_PSYCHIC_ALPHA, 487, 622, 4, TRUE },
    { TRAINER_ACE_TRAINER_YARDLEY, 623, 758, 8, TRUE },
    { TRAINER_YOUNGSTER_KADEN, 759, 894, 12, TRUE },
    { TRAINER_JOGGER_COLT, 351, 950, 16, TRUE },
    { TRAINER_CAMPER_FREDDY, 351, 950, 20, TRUE },
    { TRAINER_ACE_TRAINER_SAWYER, 351, 950, 24, TRUE },
    { TRAINER_TRAINER_CHERYL_CHERYL, 351, 950, 31, FALSE },
    { PLATFACTORY_THORTON_GOLD, 759, 950, 12, FALSE },
    { TRAINER_ARCADE_STAR_DAHLIA_SILVER, 759, 950, 31, FALSE },
};

// sOpenLevelPlayerPools
static const PokemonPool sOpenLevelPlayerPools[] = {
    { TRAINER_CYCLIST_GASPAR, 351, 486, 0, TRUE },
    { TRAINER_PSYCHIC_ALPHA, 487, 622, 4, TRUE },
    { TRAINER_ACE_TRAINER_YARDLEY, 623, 758, 8, TRUE },
    { TRAINER_YOUNGSTER_KADEN, 759, 894, 12, TRUE },
    { TRAINER_JOGGER_COLT, 623, 950, 16, TRUE },
    { TRAINER_CAMPER_FREDDY, 623, 950, 20, TRUE },
    { TRAINER_ACE_TRAINER_SAWYER, 623, 950, 24, TRUE },
    { TRAINER_TRAINER_CHERYL_CHERYL, 351, 950, 31, FALSE },
    { PLATFACTORY_THORTON_GOLD, 759, 950, 12, FALSE },
    { TRAINER_ARCADE_STAR_DAHLIA_SILVER, 759, 950, 31, FALSE },
};

// sTradeCountsNeededForUpgrades
static const u16 sTradeCountsForUpgrades[] = { 6, 13, 20, 27, 34 };

// BattleFactory_GetEarnedBP's tables
static const u8 sBPPerRoundSolo[PLATFACTORY_ROUNDS + 1] = { 0, 5, 5, 5, 5, 7, 7, 8, 9 };
static const u8 sBPPerRoundWifi[PLATFACTORY_ROUNDS + 1] = { 0, 10, 11, 12, 13, 16, 17, 19, 21 };

#ifndef NELEMS
#define NELEMS(a) (sizeof(a) / sizeof((a)[0]))
#endif

// Platinum's LCRNG_Next
u16 PlatFactory_Random(PlatFactory *factory) {
    factory->rng = factory->rng * LCRNG_MULTIPLIER + LCRNG_INCREMENT;
    return (u16)(factory->rng >> 16);
}

// LCRNG_Next() | LCRNG_Next() << 16: the low half drawn first
static u32 Random32(PlatFactory *factory) {
    u32 low = PlatFactory_Random(factory);
    u32 high = PlatFactory_Random(factory);

    return low | (high << 16);
}

static BOOL IsShiny(u32 otID, u32 personality) {
    return (((otID & 0xffff0000) >> 16) ^ (otID & 0xffff) ^ ((personality & 0xffff0000) >> 16) ^ (personality & 0xffff)) <
           8;
}

// ---------------------------------------------------------------- the records (battle_frontier_stats.c, _save.c)
static u16 StatIndex(u8 isOpenLevel, u8 challengeType, u32 offset) {
    u32 type = challengeType > PLATFACTORY_MULTI ? PLATFACTORY_MULTI : challengeType;      // (the Wi-Fi one is closed)

    return (u16)(STAT_FACTORY_FIRST + 8 * type + 4 * isOpenLevel + offset);
}

u16 PlatFactory_RecordStreakStat(u8 isOpenLevel, u8 challengeType) {
    return StatIndex(isOpenLevel, challengeType, 0);
}

u16 PlatFactory_LatestStreakStat(u8 isOpenLevel, u8 challengeType) {
    return StatIndex(isOpenLevel, challengeType, 1);
}

u16 PlatFactory_RecordTradeCountStat(u8 isOpenLevel, u8 challengeType) {
    return StatIndex(isOpenLevel, challengeType, 2);
}

u16 PlatFactory_LatestTradeCountStat(u8 isOpenLevel, u8 challengeType) {
    return StatIndex(isOpenLevel, challengeType, 3);
}

static u16 GetStat(PlatFactoryRecords *records, u16 stat) {
    return stat < STATS_NUM_SOLO ? records->stats[stat] : 0;
}

// BattleFrontierSave_SetStat (a solo stat)
static u16 SetStat(PlatFactoryRecords *records, u16 stat, u16 value) {
    if (value > STAT_VALUE_MAX) {
        value = STAT_VALUE_MAX;
    }
    if (stat < STATS_NUM_SOLO) {
        records->stats[stat] = value;
    }
    return value;
}

// BattleFrontierSave_SetIfBetter
static u16 SetIfBetter(PlatFactoryRecords *records, u16 stat, u16 value) {
    u16 current = GetStat(records, stat);

    if (current < value) {
        return SetStat(records, stat, value);
    }
    if (current > STAT_VALUE_MAX) {
        return SetStat(records, stat, STAT_VALUE_MAX);
    }
    return current;
}

// BattleFactoryStreakFlags_GetFlag / _SetFlag (FACTORY_SAVE_STREAK_FLAGS)
static u8 GetStreakFlag(PlatFactoryRecords *records, u8 index) {
    return (*records->streakFlags >> index) & 1;
}

static void SetStreakFlag(PlatFactoryRecords *records, u8 index, u8 value) {
    if (value >= 1) {
        *records->streakFlags |= 1 << index;
    } else {
        *records->streakFlags &= 0xff ^ (1 << index);
    }
}

// ---------------------------------------------------------------- the challenge's save (battle_factory_save.c)
static void Save_Init(PlatFactorySave *save) {
    u8 *bytes = (u8 *)save;
    u32 i;

    for (i = 0; i < sizeof(PlatFactorySave); i++) {
        bytes[i] = 0;
    }
}

// ---------------------------------------------------------------- Pokémon from sets (frontier_opponents.c)
// FrontierPokemon_Init (alwaysFalse FALSE: the set's own item)
static u32 Mon_Init(PlatFactory *factory, PlatFactoryMon *mon, u16 setID, u32 otID, u32 personality, u8 ivs) {
    PlatFactorySet set;
    u16 ability2;
    u8 happiness = 255;
    int i, evs;

    PlatFactory_ReadSet(setID, &set);
    mon->species = set.species;
    mon->form = (u8)set.form;
    mon->item = set.item;
    for (i = 0; i < 4; i++) {
        mon->moves[i] = set.moves[i];
        if (set.moves[i] == MOVE_FRUSTRATION) {
            happiness = 0;
        }
    }
    mon->otID = otID;
    if (personality == 0) {
        do {
            personality = Random32(factory);
        } while (set.nature != personality % NATURE_COUNT || IsShiny(otID, personality) == TRUE);
    }
    mon->personality = personality;
    mon->nature = set.nature;
    mon->ivs = ivs;
    evs = 0;
    for (i = 0; i < STAT_MAX; i++) {
        if (set.evFlags & (1 << i)) {
            evs++;
        }
    }
    // (Platinum divides by the count as it is: no set has no flag)
    if (evs == 0 || MAX_EVS_ALL_STATS / evs > MAX_EVS_SINGLE_STAT) {
        evs = MAX_EVS_SINGLE_STAT;
    } else {
        evs = MAX_EVS_ALL_STATS / evs;
    }
    for (i = 0; i < STAT_MAX; i++) {
        mon->evs[i] = (set.evFlags & (1 << i)) ? (u8)evs : 0;
    }
    ability2 = PlatFactory_SpeciesAbility(mon->species, 1);
    if (ability2 != 0 && (mon->personality & 1)) {
        mon->ability = ability2;
    } else {
        mon->ability = PlatFactory_SpeciesAbility(mon->species, 0);
    }
    mon->happiness = happiness;
    return personality;
}

// BattleFrontier_LoadOpponentMonData: a trainer id first, then the Pokémon
static u32 Mon_Load(PlatFactory *factory, PlatFactoryMon *mon, u16 setID, u8 ivs, u32 personality) {
    u32 otID = Random32(factory);

    return Mon_Init(factory, mon, setID, otID, personality, ivs);
}

// BattleFrontier_LoadFrontierPokemon
static void Mons_Load(PlatFactory *factory, PlatFactoryMon *mons, const u16 *setIDs, const u8 *ivList,
                      const u32 *personalities, u32 *resultPersonalities, int count) {
    int i;
    u32 personality;

    for (i = 0; i < count; i++) {
        personality = Mon_Load(factory, &mons[i], setIDs[i], ivList == NULL ? 0 : ivList[i],
                               personalities == NULL ? 0 : personalities[i]);
        if (resultPersonalities != NULL) {
            resultPersonalities[i] = personality;
        }
    }
}

// The random numbers of FrontierPokemon_InitPokemon (Pokemon_InitWith with the personality and OTID_NOT_SHINY: a trainer id
// that isn't shiny with it; the IVs as one number, which, 32 or more, makes it draw random IVs before it sets them)
static void InitPokemonRandom(PlatFactory *factory, const PlatFactoryMon *mon) {
    u32 otID, combined;

    do {
        otID = Random32(factory);
    } while (IsShiny(otID, mon->personality));
    combined = (u32)mon->ivs * (1 | (1 << 5) | (1 << 10) | (1 << 15) | (1 << 20) | (1 << 25));
    if ((combined & 0x3fffffff) >= 32) {
        PlatFactory_Random(factory);
        PlatFactory_Random(factory);
    }
}

// FrontierPokemon_InitPokemon then BattleFactory_AddRentalPokemonToParty: the party gets the Pokémon as made
static void Party_Add(PlatFactory *factory, PlatFactoryMon *party, u8 *count, u8 capacity, const PlatFactoryMon *mon) {
    InitPokemonRandom(factory, mon);
    if (*count < capacity) {
        party[(*count)++] = *mon;
    }
}

// ---------------------------------------------------------------- battle_factory_helpers.c
u8 PlatFactory_GetPlayerPartySize(u8 challengeType) {
    switch (challengeType) {
    case PLATFACTORY_SINGLE:
    case PLATFACTORY_DOUBLE:
        return PLATFACTORY_PARTY_SOLO;
    case PLATFACTORY_MULTI:
    case PLATFACTORY_MULTI_WFC:
        return PLATFACTORY_PARTY_MULTI;
    }
    return 0;
}

u8 PlatFactory_GetOpponentPartySize(u8 challengeType, BOOL includePartnersMons) {
    switch (challengeType) {
    case PLATFACTORY_SINGLE:
    case PLATFACTORY_DOUBLE:
        return PLATFACTORY_PARTY_SOLO;
    case PLATFACTORY_MULTI:
    case PLATFACTORY_MULTI_WFC:
        return includePartnersMons == FALSE ? PLATFACTORY_PARTY_MULTI : PLATFACTORY_PARTY_MULTI * 2;
    }
    return 0;
}

static BOOL IsMultiplayerChallenge(u8 challengeType) {
    return challengeType == PLATFACTORY_MULTI || challengeType == PLATFACTORY_MULTI_WFC;
}

// BattleFactory_GetCurrentRound (a solo challenge: the link's round is the partner's)
u16 PlatFactory_GetCurrentRound(PlatFactory *factory) {
    return factory->currentRound;
}

u8 PlatFactory_GetPokemonLevel(PlatFactory *factory) {
    return factory->isOpenLevel == FALSE ? 50 : 100;
}

// BattleFactory_GetOpponentTrainerID: Thorton at the 21st and 49th battles of a Single challenge
static int GetOpponentTrainerID(PlatFactory *factory, u8 challengeType, int currentRound, int trainerOffset) {
    int currentStreak, spread, min;

    if (currentRound >= (int)NELEMS(sOpponentPools)) {
        currentRound = NELEMS(sOpponentPools) - 1;
    }
    if (challengeType == PLATFACTORY_SINGLE) {
        currentStreak = currentRound * PLATFACTORY_BATTLES_PER_ROUND + (trainerOffset + 1);
        if (currentStreak == PLATFACTORY_STREAK_SILVER) {
            return PLATFACTORY_THORTON_SILVER;
        } else if (currentStreak == PLATFACTORY_STREAK_GOLD) {
            return PLATFACTORY_THORTON_GOLD;
        }
    }
    if (trainerOffset == PLATFACTORY_BATTLES_PER_ROUND - 1 || trainerOffset == PLATFACTORY_BATTLES_PER_ROUND * 2 - 1) {
        spread = sOpponentPools[currentRound].finalMax - sOpponentPools[currentRound].finalMin;
        min = sOpponentPools[currentRound].finalMin;
    } else {
        spread = sOpponentPools[currentRound].normalMax - sOpponentPools[currentRound].normalMin;
        min = sOpponentPools[currentRound].normalMin;
    }
    return min + PlatFactory_Random(factory) % spread;
}

// BattleFactory_PickOpponentTrainers: no Trainer twice in a round
static void PickOpponentTrainers(PlatFactory *factory, u8 challengeType, int currentRound, u16 *trainerIDs,
                                 u8 numTrainers) {
    int i = 0, j;

    do {
        trainerIDs[i] = (u16)GetOpponentTrainerID(factory, challengeType, currentRound, i);
        for (j = 0; j < i; j++) {
            if (trainerIDs[j] == trainerIDs[i]) {
                break;
            }
        }
        if (j != i) {
            continue;
        }
        i++;
    } while (i < numTrainers);
}

// BattleFactory_GetPokemonPoolForTrainer
static const PokemonPool *GetPoolForTrainer(int trainerID, BOOL isOpenLevel) {
    const PokemonPool *pools = isOpenLevel ? sOpenLevelOpponentPools : sLevel50Pools;
    int numPools = isOpenLevel ? (int)NELEMS(sOpenLevelOpponentPools) : (int)NELEMS(sLevel50Pools);
    int i;

    for (i = 0; i < numPools; i++) {
        if (trainerID < pools[i].trainerIDMax) {
            break;
        }
    }
    if (i >= numPools) {
        i = numPools - 1;
    }
    return &pools[i];
}

// GetPlayerPoolForRound
static const PokemonPool *GetPlayerPoolForRound(int round, int isOpenLevel) {
    if (round >= PLATFACTORY_ROUNDS) {
        round = PLATFACTORY_ROUNDS - 1;
    }
    return !isOpenLevel ? &sLevel50Pools[round] : &sOpenLevelPlayerPools[round];
}

// BattleFactory_SelectPokemonFromPool: numMons sets of the pool (the last ones of the next pool after enough swaps), no
// species or item twice, none of the excluded species or items
static void SelectPokemonFromPool(PlatFactory *factory, const u16 *excludedSpecies, const u16 *excludedItems,
                                  int numExcluded, int numMons, u16 *monSetIDs, const PokemonPool *pool, u16 tradeCount,
                                  u8 *ivList) {
    PlatFactorySet newMon[PLATFACTORY_RENTALS];
    int slot = 0, setIDRange, setID, i, numUpgradable = 0;
    u8 ivs;

    setIDRange = pool->setIDMax - pool->setIDMin;
    if (tradeCount != 0) {
        numUpgradable = NELEMS(sTradeCountsForUpgrades);
        for (i = 0; i < (int)NELEMS(sTradeCountsForUpgrades); i++) {
            if (tradeCount <= sTradeCountsForUpgrades[i]) {
                numUpgradable = i;
                break;
            }
        }
    }
    while (slot != numMons) {
        if (slot >= numMons - numUpgradable && pool->canBeUpgraded == TRUE) {
            setIDRange = pool[1].setIDMax - pool[1].setIDMin;
            setID = pool[1].setIDMax - PlatFactory_Random(factory) % (setIDRange + 1);
            ivs = pool[1].ivs;
        } else {
            setID = pool->setIDMax - PlatFactory_Random(factory) % (setIDRange + 1);
            ivs = pool->ivs;
        }
        PlatFactory_ReadSet((u16)setID, &newMon[slot]);
        for (i = 0; i < slot; i++) {
            if (newMon[i].species == newMon[slot].species || newMon[i].item == newMon[slot].item) {
                break;
            }
        }
        if (i != slot) {
            continue;
        }
        for (i = 0; i < numExcluded; i++) {
            if (newMon[slot].species == excludedSpecies[i] || newMon[slot].item == excludedItems[i]) {
                break;
            }
        }
        if (i != numExcluded) {
            continue;
        }
        monSetIDs[slot] = (u16)setID;
        ivList[slot] = ivs;
        slot++;
    }
}

// BattleFactory_SelectInitialRentalOptions (no partner)
static void SelectInitialRentalOptions(PlatFactory *factory, u16 round, u8 isOpenLevel, u16 tradeCount) {
    SelectPokemonFromPool(factory, NULL, NULL, 0, PLATFACTORY_RENTALS, factory->initialRentalSetIDs,
                          GetPlayerPoolForRound(round, isOpenLevel), tradeCount, factory->initialRentalIVs);
    Mons_Load(factory, factory->initialRentalMons, factory->initialRentalSetIDs, factory->initialRentalIVs, NULL,
              factory->initialRentalPersonalities, PLATFACTORY_RENTALS);
}

// BattleFactory_SelectInitialOpponentMons
static void SelectInitialOpponentMons(PlatFactory *factory, u8 numMons, u16 trainerID, u8 isOpenLevel,
                                      const PlatFactoryMon *excludedMons, int numExcluded) {
    u16 excludedSpecies[PLATFACTORY_RENTALS * 2];
    u16 excludedItems[PLATFACTORY_RENTALS * 2];
    int i;

    for (i = 0; i < numExcluded; i++) {
        excludedSpecies[i] = excludedMons[i].species;
        excludedItems[i] = excludedMons[i].item;
    }
    SelectPokemonFromPool(factory, excludedSpecies, excludedItems, numExcluded, numMons, factory->opponentMonSetIDs,
                          GetPoolForTrainer(trainerID, isOpenLevel), 0, factory->opponentMonIVs);
    Mons_Load(factory, factory->opponentMons, factory->opponentMonSetIDs, factory->opponentMonIVs, NULL,
              factory->opponentMonPersonalities, numMons);
}

// BattleFactory_GetAIMask (Platinum's AI flags: 1 basic, 2 evaluate attacks, 4 expert)
u16 PlatFactory_GetAIMask(PlatFactory *factory) {
    u16 round, aiMask;

    if (factory->challengeType == PLATFACTORY_SINGLE) {
        if (factory->trainerIDs[factory->currentBattle] == PLATFACTORY_THORTON_SILVER ||
            factory->trainerIDs[factory->currentBattle] == PLATFACTORY_THORTON_GOLD) {
            return 1 | 2 | 4;
        }
    }
    round = PlatFactory_GetCurrentRound(factory);
    aiMask = 1 | 2 | 4;
    switch (round + 1) {
    case 1:
    case 2:
        aiMask = 0;
        break;
    case 3:
    case 4:
        aiMask = 1;
        break;
    }
    return aiMask;
}

// BattleFactory_CreateInitialRentalParty
void PlatFactory_CreateInitialRentalParty(PlatFactory *factory) {
    int i;

    Mons_Load(factory, factory->initialRentalMons, factory->initialRentalSetIDs, factory->initialRentalIVs,
              factory->initialRentalPersonalities, NULL, PLATFACTORY_RENTALS);
    factory->playerCount = 0;
    for (i = 0; i < PLATFACTORY_RENTALS; i++) {
        Party_Add(factory, factory->playersParty, &factory->playerCount, PLATFACTORY_RENTALS,
                  &factory->initialRentalMons[i]);
    }
}

// ---------------------------------------------------------------- battle_factory.c
// BattleFactory_Init (the streak's records: Platinum's BattleFrontierStats by its ids)
void PlatFactory_Init(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records, u16 resumingFromSave,
                      u8 challengeType, u8 isOpenLevel, u32 seed) {
    u8 *bytes = (u8 *)factory;
    u32 i;
    u8 streakActive;

    for (i = 0; i < sizeof(PlatFactory); i++) {
        bytes[i] = 0;
    }
    factory->rng = seed;
    if (!resumingFromSave) {
        factory->challengeType = challengeType;
        factory->isOpenLevel = isOpenLevel;
        factory->currentBattle = 0;
        Save_Init(save);
        // (the Wi-Fi challenge reads the system var of its cleared state: closed here)
        streakActive = GetStreakFlag(records, (u8)(factory->isOpenLevel * 4 + factory->challengeType));
        if (streakActive == TRUE) {
            factory->currentStreak = GetStat(records, PlatFactory_LatestStreakStat(factory->isOpenLevel,
                                                                                     factory->challengeType));
            factory->tradeCount = GetStat(records, PlatFactory_LatestTradeCountStat(factory->isOpenLevel,
                                                                                      factory->challengeType));
        } else {
            factory->currentStreak = 0;
            factory->tradeCount = 0;
        }
    } else {
        factory->challengeType = save->challengeType;
        factory->isOpenLevel = save->isOpenLevel;
        factory->currentBattle = save->currentBattleNum;
        factory->currentStreak = GetStat(records, PlatFactory_LatestStreakStat(factory->isOpenLevel, factory->challengeType));
        factory->tradeCount = GetStat(records, PlatFactory_LatestTradeCountStat(factory->isOpenLevel,
                                                                                  factory->challengeType));
    }
    factory->currentRound = factory->currentStreak / PLATFACTORY_BATTLES_PER_ROUND;
}

// SwapMonIndices (the player's rentals)
static void SwapMonIndices(PlatFactory *factory, u8 idx1) {
    u16 idx2 = PlatFactory_Random(factory) % PLATFACTORY_RENTALS;
    u16 setID = factory->initialRentalSetIDs[idx1];
    u8 ivs = factory->initialRentalIVs[idx1];
    u32 personality = factory->initialRentalPersonalities[idx1];
    PlatFactoryMon mon = factory->initialRentalMons[idx1];

    factory->initialRentalSetIDs[idx1] = factory->initialRentalSetIDs[idx2];
    factory->initialRentalIVs[idx1] = factory->initialRentalIVs[idx2];
    factory->initialRentalPersonalities[idx1] = factory->initialRentalPersonalities[idx2];
    factory->initialRentalMons[idx1] = factory->initialRentalMons[idx2];
    factory->initialRentalSetIDs[idx2] = setID;
    factory->initialRentalIVs[idx2] = ivs;
    factory->initialRentalPersonalities[idx2] = personality;
    factory->initialRentalMons[idx2] = mon;
}

// SetupTrainersAndInitialRentalOptions: the round's 14 Trainers, the six rentals (the last two moved to random places,
// so the upgraded ones aren't always last), the first opponent's Pokémon (none of the rentals' species or items)
static void SetupTrainersAndInitialRentalOptions(PlatFactory *factory) {
    PlatFactoryMon usedMons[PLATFACTORY_RENTALS * 2];
    int i;

    PickOpponentTrainers(factory, factory->challengeType, PlatFactory_GetCurrentRound(factory), factory->trainerIDs,
                         PLATFACTORY_TRAINERS);
    SelectInitialRentalOptions(factory, PlatFactory_GetCurrentRound(factory), factory->isOpenLevel, factory->tradeCount);
    SwapMonIndices(factory, 4);
    SwapMonIndices(factory, 5);
    for (i = 0; i < PLATFACTORY_RENTALS; i++) {
        usedMons[i] = factory->initialRentalMons[i];
    }
    SelectInitialOpponentMons(factory, PlatFactory_GetOpponentPartySize(factory->challengeType, TRUE),
                              factory->trainerIDs[factory->currentBattle], factory->isOpenLevel, usedMons,
                              PLATFACTORY_RENTALS);
    factory->playerCount = 0;
    for (i = 0; i < PLATFACTORY_RENTALS; i++) {
        Party_Add(factory, factory->playersParty, &factory->playerCount, PLATFACTORY_RENTALS,
                  &factory->initialRentalMons[i]);
    }
}

// LoadTrainersAndMonsFromSave: four Pokémon each, as Platinum loads them (a solo challenge's fourth is set 0)
static void LoadTrainersAndMonsFromSave(PlatFactory *factory, PlatFactorySave *save) {
    PlatFactoryMon mons[PLATFACTORY_MAX_PARTY];
    u16 setIDs[PLATFACTORY_MAX_PARTY];
    u8 ivs[PLATFACTORY_MAX_PARTY];
    u32 personalities[PLATFACTORY_MAX_PARTY];
    int i;

    for (i = 0; i < PLATFACTORY_TRAINERS; i++) {
        factory->trainerIDs[i] = save->trainerIDs[i];
    }
    for (i = 0; i < PLATFACTORY_MAX_PARTY; i++) {
        setIDs[i] = save->playerPartySets[i];
        personalities[i] = save->playerPersonality[i];
        ivs[i] = save->playerIVs[i];
        factory->playerMonSetIDs[i] = setIDs[i];
    }
    Mons_Load(factory, mons, setIDs, ivs, personalities, NULL, PLATFACTORY_MAX_PARTY);
    factory->playerCount = 0;
    for (i = 0; i < PLATFACTORY_MAX_PARTY; i++) {
        Party_Add(factory, factory->playersParty, &factory->playerCount, PLATFACTORY_RENTALS, &mons[i]);
    }
    for (i = 0; i < PLATFACTORY_MAX_PARTY; i++) {
        setIDs[i] = save->opponentPartySets[i];
        personalities[i] = save->opponentPersonality[i];
        ivs[i] = save->opponentIVs[i];
        factory->opponentMonSetIDs[i] = setIDs[i];
    }
    Mons_Load(factory, mons, setIDs, ivs, personalities, NULL, PLATFACTORY_MAX_PARTY);
    factory->opponentCount = 0;
    for (i = 0; i < PLATFACTORY_MAX_PARTY; i++) {
        Party_Add(factory, factory->opponentsParty, &factory->opponentCount, PLATFACTORY_MAX_PARTY, &mons[i]);
    }
}

void PlatFactory_LoadTrainersAndRentalsForRound(PlatFactory *factory, PlatFactorySave *save, u16 resumingFromSave) {
    if (!resumingFromSave) {
        SetupTrainersAndInitialRentalOptions(factory);
    } else {
        LoadTrainersAndMonsFromSave(factory, save);
    }
}

// BattleFactory_Save: saveType 0 a round completed, 1 a loss, 2 the save before a rest (no records)
void PlatFactory_Save(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records, u8 saveType) {
    u16 recordStreak, latestStreak, i;
    u8 isOpenLevel = factory->isOpenLevel, challengeType = factory->challengeType;

    save->isOpenLevel = isOpenLevel;
    save->challengeType = challengeType;
    save->didSave = TRUE;
    save->currentBattleNum = factory->currentBattle;
    SetStat(records, PlatFactory_LatestTradeCountStat(isOpenLevel, challengeType), factory->tradeCount);
    SetStat(records, PlatFactory_LatestStreakStat(isOpenLevel, challengeType), factory->currentStreak);
    if (saveType != 2) {
        recordStreak = GetStat(records, PlatFactory_RecordStreakStat(isOpenLevel, challengeType));
        SetIfBetter(records, PlatFactory_RecordStreakStat(isOpenLevel, challengeType), factory->currentStreak);
        latestStreak = GetStat(records, PlatFactory_RecordStreakStat(isOpenLevel, challengeType));
        if (factory->currentStreak == recordStreak) {
            SetIfBetter(records, PlatFactory_RecordTradeCountStat(isOpenLevel, challengeType), factory->tradeCount);
        } else if (recordStreak < latestStreak) {
            SetStat(records, PlatFactory_RecordTradeCountStat(isOpenLevel, challengeType), factory->tradeCount);
        }
        SetStreakFlag(records, (u8)(isOpenLevel * 4 + challengeType), factory->saveStreak);
    }
    for (i = 0; i < PLATFACTORY_TRAINERS; i++) {
        save->trainerIDs[i] = factory->trainerIDs[i];
    }
    for (i = 0; i < factory->playerCount && i < PLATFACTORY_MAX_PARTY; i++) {
        save->playerPartySets[i] = factory->playerMonSetIDs[i];
        save->playerIVs[i] = factory->playersParty[i].ivs;
        save->playerPersonality[i] = factory->playersParty[i].personality;
    }
    for (i = 0; i < factory->opponentCount && i < PLATFACTORY_MAX_PARTY; i++) {
        save->opponentPartySets[i] = factory->opponentMonSetIDs[i];
        save->opponentIVs[i] = factory->opponentsParty[i].ivs;
        save->opponentPersonality[i] = factory->opponentsParty[i].personality;
    }
}

void PlatFactory_SaveOnLoss(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records) {
    PlatFactory_Save(factory, save, records, 1);
}

void PlatFactory_SaveOnCompletingRound(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records) {
    factory->saveStreak = TRUE;
    if (factory->currentRound < PLATFACTORY_ROUNDS) {
        factory->currentRound++;
    }
    factory->currentBattle = 0;
    PlatFactory_Save(factory, save, records, 0);
}

// BattleFactory_AddSelectedRentalsToParty: the three picked (selectedAppSlots) and the opponent's
void PlatFactory_AddSelectedRentalsToParty(PlatFactory *factory) {
    u8 playerPartySize = PlatFactory_GetPlayerPartySize(factory->challengeType);
    u8 opponentPartySize = PlatFactory_GetOpponentPartySize(factory->challengeType, TRUE);
    int i;

    factory->playerCount = 0;
    for (i = 0; i < playerPartySize; i++) {
        Party_Add(factory, factory->playersParty, &factory->playerCount, PLATFACTORY_RENTALS,
                  &factory->initialRentalMons[factory->selectedAppSlots[i]]);
        factory->playerMonSetIDs[i] = factory->initialRentalSetIDs[factory->selectedAppSlots[i]];
    }
    for (i = 0; i < opponentPartySize; i++) {
        Party_Add(factory, factory->opponentsParty, &factory->opponentCount, PLATFACTORY_MAX_PARTY,
                  &factory->opponentMons[i]);
    }
}

// BattleFactory_SetupNextOpponent: the next Trainer's Pokémon, none of the species or items of both parties; the beaten
// opponent's sets are kept for the swap (initialRentalSetIDs)
void PlatFactory_SetupNextOpponent(PlatFactory *factory) {
    u16 usedSpecies[PLATFACTORY_MAX_PARTY * 2 + PLATFACTORY_RENTALS];
    u16 usedItems[PLATFACTORY_MAX_PARTY * 2 + PLATFACTORY_RENTALS];
    int i, partySize, playersPartySize;
    u8 opponentPartySize;

    for (i = 0; i < (int)NELEMS(usedSpecies); i++) {
        usedSpecies[i] = 0;
        usedItems[i] = 0;
    }
    opponentPartySize = PlatFactory_GetOpponentPartySize(factory->challengeType, TRUE);
    partySize = factory->playerCount;
    for (i = 0; i < partySize; i++) {
        usedSpecies[i] = factory->playersParty[i].species;
        usedItems[i] = factory->playersParty[i].item;
    }
    playersPartySize = partySize;
    partySize = factory->opponentCount;
    for (i = 0; i < partySize; i++) {
        usedSpecies[i + playersPartySize] = factory->opponentsParty[i].species;
        usedItems[i + playersPartySize] = factory->opponentsParty[i].item;
        factory->initialRentalSetIDs[i] = factory->opponentMonSetIDs[i];
    }
    SelectPokemonFromPool(factory, usedSpecies, usedItems, playersPartySize + partySize, opponentPartySize,
                          factory->opponentMonSetIDs,
                          GetPoolForTrainer(factory->trainerIDs[factory->currentBattle], factory->isOpenLevel), 0,
                          factory->opponentMonIVs);
    Mons_Load(factory, factory->opponentMons, factory->opponentMonSetIDs, factory->opponentMonIVs, NULL,
              factory->opponentMonPersonalities, opponentPartySize);
}

// BattleFactory_ApplyTrade: selectedAppSlots[0] the player's Pokémon given, [1] the beaten opponent's taken (0xff: none).
// TRUE when a swap was made (the game record RECORD_BATTLE_FACTORY_TRADES goes up: the caller's)
BOOL PlatFactory_ApplyTrade(PlatFactory *factory) {
    if (factory->selectedAppSlots[0] == 0xff) {
        return FALSE;
    }
    factory->playersParty[factory->selectedAppSlots[0]] = factory->opponentsParty[factory->selectedAppSlots[1]];
    factory->playerMonSetIDs[factory->selectedAppSlots[0]] = factory->initialRentalSetIDs[factory->selectedAppSlots[1]];
    PlatFactory_IncrementTradeCount(factory);
    return TRUE;
}

// BattleFactory_SetupNextOpponentsParty
void PlatFactory_SetupNextOpponentsParty(PlatFactory *factory) {
    u8 partySize = PlatFactory_GetOpponentPartySize(factory->challengeType, TRUE);
    int i;

    factory->opponentCount = 0;
    for (i = 0; i < partySize; i++) {
        Party_Add(factory, factory->opponentsParty, &factory->opponentCount, PLATFACTORY_MAX_PARTY,
                  &factory->opponentMons[i]);
    }
}

void PlatFactory_IncrementTradeCount(PlatFactory *factory) {
    if (factory->tradeCount < STAT_VALUE_MAX) {
        factory->tradeCount++;
    }
}

// BattleFactory_GetEarnedBP: by the round just completed; Thorton's battles 20
u16 PlatFactory_GetEarnedBP(PlatFactory *factory) {
    u16 currentRound = factory->currentRound;
    u8 bp;

    if (factory->challengeType == PLATFACTORY_SINGLE || factory->challengeType == PLATFACTORY_DOUBLE) {
        bp = currentRound >= PLATFACTORY_ROUNDS ? sBPPerRoundSolo[PLATFACTORY_ROUNDS] : sBPPerRoundSolo[currentRound];
    } else {
        bp = currentRound >= PLATFACTORY_ROUNDS ? sBPPerRoundWifi[PLATFACTORY_ROUNDS] : sBPPerRoundWifi[currentRound];
    }
    if (factory->challengeType == PLATFACTORY_SINGLE) {
        if (factory->currentStreak == PLATFACTORY_STREAK_SILVER || factory->currentStreak == PLATFACTORY_STREAK_GOLD) {
            bp = 20;
        }
    }
    return bp;
}

// ---------------------------------------------------------------- CallBattleFactoryFunction (frscrcmd_battle_factory.c)
// The opponents' most common type (BF_FUNC_GET_COMMON_TYPE): PLATFACTORY_NO_TYPE if none is shared
static u16 GetCommonType(PlatFactory *factory) {
    int typeCounts[PLATFACTORY_TYPES];
    u8 partySize = PlatFactory_GetOpponentPartySize(factory->challengeType, TRUE);
    u8 type1, type2;
    u32 commonType = 0;
    int i;

    for (i = 0; i < PLATFACTORY_TYPES; i++) {
        typeCounts[i] = 0;
    }
    for (i = 0; i < partySize; i++) {
        InitPokemonRandom(factory, &factory->opponentMons[i]);
        PlatFactory_SpeciesTypes(factory->opponentMons[i].species, factory->opponentMons[i].form, &type1, &type2);
        typeCounts[type1]++;
        if (type2 != type1) {
            typeCounts[type2]++;
        }
    }
    for (i = 0; i < PLATFACTORY_TYPES; i++) {
        if (typeCounts[commonType] < typeCounts[i]) {
            commonType = i;
        }
    }
    return typeCounts[commonType] <= 1 ? PLATFACTORY_NO_TYPE : (u16)commonType;
}

BOOL PlatFactory_Function(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records, u8 fn, u8 arg1,
                          u8 arg2, u16 *result) {
    u8 type1, type2;

    switch (fn) {
    case PLATFACTORY_FN_UNK_0:
        factory->unused2 = arg1;
        break;
    case PLATFACTORY_FN_SET_IS_OPEN_LEVEL:
        factory->isOpenLevel = arg1;
        break;
    case PLATFACTORY_FN_SET_CHALLENGE_TYPE:
        factory->challengeType = arg1;
        break;
    case PLATFACTORY_FN_GET_SELECTED_APP_SLOT:
        *result = factory->selectedAppSlots[arg1];
        break;
    case PLATFACTORY_FN_GET_CURRENT_STREAK:
        *result = factory->currentStreak;
        break;
    case PLATFACTORY_FN_INCREMENT_CURRENT_STREAK:
        if (factory->currentStreak < STAT_VALUE_MAX) {
            factory->currentStreak++;
        }
        break;
    case PLATFACTORY_FN_HAS_SAVED:
        *result = save->didSave;
        break;
    case PLATFACTORY_FN_QUICKSAVE:
        PlatFactory_Save(factory, save, records, 2);
        break;
    case PLATFACTORY_FN_INCREMENT_CURRENT_BATTLE:
        *result = ++factory->currentBattle;
        break;
    case PLATFACTORY_FN_GET_MONS_SPECIES:
        *result = factory->opponentMons[arg1].species;
        break;
    case PLATFACTORY_FN_GET_MONS_MOVE:
        *result = factory->opponentMons[arg1].moves[arg2];
        break;
    case PLATFACTORY_FN_GET_MONS_TYPE:
        InitPokemonRandom(factory, &factory->opponentMons[arg1]);
        PlatFactory_SpeciesTypes(factory->opponentMons[arg1].species, factory->opponentMons[arg1].form, &type1, &type2);
        *result = type1;
        break;
    case PLATFACTORY_FN_GET_COMMON_TYPE:
        *result = GetCommonType(factory);
        break;
    case PLATFACTORY_FN_GET_CURRENT_ROUND:
        *result = PlatFactory_GetCurrentRound(factory);
        break;
    case PLATFACTORY_FN_SAVE_ON_LOSS:
        PlatFactory_SaveOnLoss(factory, save, records);
        break;
    case PLATFACTORY_FN_SAVE_ON_COMPLETING_ROUND:
        PlatFactory_SaveOnCompletingRound(factory, save, records);
        break;
    case PLATFACTORY_FN_GET_CURRENT_BATTLE:
        *result = factory->currentBattle;
        break;
    case PLATFACTORY_FN_UNK_24:
    case PLATFACTORY_FN_UNK_26:
        *result = 0;                        // (the partner's answers: no link here)
        break;
    case PLATFACTORY_FN_IS_MULTIPLAYER_CHALLENGE:
        *result = IsMultiplayerChallenge(factory->challengeType);
        break;
    case PLATFACTORY_FN_GET_CHALLENGE_TYPE:
        *result = factory->challengeType;
        break;
    case PLATFACTORY_FN_GET_EARNED_BP:
        *result = PlatFactory_GetEarnedBP(factory);
        break;
    case PLATFACTORY_FN_INCREMENT_TRADE_COUNT:
        PlatFactory_IncrementTradeCount(factory);
        break;
    case PLATFACTORY_FN_GET_NEXT_BATTLE_TYPE:
        *result = PLATFACTORY_NEXT_NORMAL;
        if (factory->challengeType == PLATFACTORY_SINGLE) {
            if (factory->currentStreak + 1 == PLATFACTORY_STREAK_SILVER) {
                *result = PLATFACTORY_NEXT_SILVER;
            } else if (factory->currentStreak + 1 == PLATFACTORY_STREAK_GOLD) {
                *result = PLATFACTORY_NEXT_GOLD;
            }
        }
        break;
    case PLATFACTORY_FN_CREATE_OPPONENT_MONS:
        Mons_Load(factory, factory->opponentMons, factory->opponentMonSetIDs, factory->opponentMonIVs,
                  factory->opponentMonPersonalities, NULL, PLATFACTORY_MAX_PARTY);
        break;
    case PLATFACTORY_FN_CREATE_INITIAL_PARTY:
        PlatFactory_CreateInitialRentalParty(factory);
        break;
    case PLATFACTORY_FN_CHECK_SEEN_HEAD_INTRO:
        *result = factory->seenFactoryHeadIntro;
        factory->seenFactoryHeadIntro = TRUE;
        break;
    default:
        return FALSE;
    }
    return TRUE;
}

// DeleteActiveBattleFactoryStreak (the lobby, after a challenge not saved before quitting)
void PlatFactory_DeleteActiveStreak(PlatFactoryRecords *records, u8 challengeType, u8 isOpenLevel) {
    SetStreakFlag(records, (u8)(isOpenLevel * 4 + challengeType), 0);
    SetStat(records, PlatFactory_LatestStreakStat(isOpenLevel, challengeType), 0);
    SetStat(records, PlatFactory_LatestTradeCountStat(isOpenLevel, challengeType), 0);
}

#endif
