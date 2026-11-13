#include "pearlb2.h"
#include "types.h"
#include "pearlb2/plat_castle.h"

// Platinum's Battle Castle rules (include/pearlb2/plat_castle.h; PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Castle"),
// written from pokeplatinum, step for step, with the same random draws in the same order:
// - src/overlay104/battle_castle.c (the challenge: Init, the round's Trainers, the save, the next battle, the CP earned, the BP)
// - src/overlay104/battle_castle_helpers.c (the Trainers by round, Darach, the party sizes, the AI, the revive, the CP spent)
// - src/overlay104/frscrcmd_battle_castle.c (CallBattleCastleFunction, the CP commands)
// - src/battle_castle_save.c, src/scrcmd_battle_castle.c (the save; the lobby's streak deletion)
// - src/overlay104/frontier_opponents.c (the opponents' Pokémon from the Trainers' sets)
// - src/applications/frontier/battle_castle/self_app.c and opponent_app.c: what each purchase checks, costs and does (their
//   state machines' checks before and after the yes, as PlatCastle_Ask and PlatCastle_Buy)
// It needs nothing of Black 2: the party, the sets and the records come through the calls plat_castle.h lists, so PearlB2's
// host harness (b2tools/platinum_castle_host) runs this file as it is beside Platinum's own C. Platinum's game-wide LCRNG
// (math_util.c) is the challenge's own here (PlatCastle.lcrng), the same generator. What differs:
// - The opponents' Pokémon are kept as made from their sets (PlatCastleMon); Platinum makes a Pokemon of each at Level 50
//   (FrontierPokemon_InitPokemon), which draws random numbers of its own (a trainer id that isn't shiny with the personality,
//   then random IVs it overwrites). Those draws are made here too, in the same places (InitPokemonRandom).
// - A resumed challenge loads its opponents' Pokémon from the save with IVs Platinum never sets (LoadTrainersAndMonsFromSave's
//   ivs array is uninitialised); they decide only whether that Pokémon's making draws its two IV numbers, and the Pokémon are
//   made again before any battle. Here they are 0 (no draws).
// - Only a solo challenge's link state: the multi challenges are the wireless and Wi-Fi ones, closed here.

#if !defined(PEARLB2) || PEARLB2

#define LCRNG_MULTIPLIER 1103515245     // pokeplatinum include/math_util.h
#define LCRNG_INCREMENT 24691
#define MAX_IVS_SINGLE_STAT 31
#define MAX_EVS_ALL_STATS 510
#define MAX_EVS_SINGLE_STAT 255
#define MAX_FRIENDSHIP_VALUE 255
#define MOVE_FRUSTRATION 218
#define NATURE_COUNT 25
#define STAT_MAX 6
#define SHINY_ODDS 8
#define INIT_IVS_RANDOM 32
#define ITEM_NONE 0

// Platinum's Frontier Trainers (res/trainers/frontier/frontier_trainers.order)
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

#ifndef NELEMS
#define NELEMS(a) (sizeof(a) / sizeof((a)[0]))
#endif

// sBattleCastleOpponentPools (battle_castle_helpers.c)
static const struct {
    u16 normalMin;
    u16 normalMax;
    u16 finalMin;
    u16 finalMax;
} sOpponentPools[] = {
    { TRAINER_YOUNGSTER_JIM, TRAINER_REPORTER_GINGHAM, TRAINER_CYCLIST_GASPAR, TRAINER_SOCIALITE_CARMEN },
    { TRAINER_HIKER_RAIDEN, TRAINER_SOCIALITE_CARMEN, TRAINER_PSYCHIC_ALPHA, TRAINER_CLOWN_PRESCOT },
    { TRAINER_CYCLIST_GASPAR, TRAINER_CLOWN_PRESCOT, TRAINER_ACE_TRAINER_YARDLEY, TRAINER_ACE_TRAINER_DANIELA },
    { TRAINER_PSYCHIC_ALPHA, TRAINER_ACE_TRAINER_DANIELA, TRAINER_YOUNGSTER_KADEN, TRAINER_IDOL_UTAH },
    { TRAINER_ACE_TRAINER_YARDLEY, TRAINER_IDOL_UTAH, TRAINER_JOGGER_COLT, TRAINER_PI_SERGEI },
    { TRAINER_YOUNGSTER_KADEN, TRAINER_PI_SERGEI, TRAINER_CAMPER_FREDDY, TRAINER_BREEDER_ANTONIA },
    { TRAINER_JOGGER_COLT, TRAINER_BREEDER_ANTONIA, TRAINER_ACE_TRAINER_SAWYER, TRAINER_VETERAN_ALFRED },
    { TRAINER_CAMPER_FREDDY, TRAINER_IDOL_NISSA, TRAINER_CAMPER_FREDDY, TRAINER_IDOL_NISSA },
};

// BattleCastle_GetEarnedBP's tables
static const u8 sBPPerRoundSolo[PLATCASTLE_ROUNDS + 1] = { 0, 3, 3, 4, 4, 5, 5, 7, 7 };
static const u8 sBPPerRoundWifi[PLATCASTLE_ROUNDS + 1] = { 0, 8, 9, 11, 12, 14, 15, 18, 18 };

// self_app.c: the rentals (Platinum's item ids, which are Black 2's for these items) and their CP
static const u16 sItemsForRent[] = {
    221 /* King's Rock */, 217 /* Quick Claw */, 271 /* Power Herb */, 253 /* Shell Bell */, 277 /* Metronome */,
    269 /* Light Clay */, 286 /* Grip Claw */, 296 /* Big Root */, 272 /* Toxic Orb */, 273 /* Flame Orb */,
    236 /* Light Ball */, 258 /* Thick Club */, 214 /* White Herb */, 230 /* Focus Band */, 275 /* Focus Sash */,
    234 /* Leftovers */, 213 /* BrightPowder */, 232 /* Scope Lens */, 265 /* Wide Lens */, 276 /* Zoom Lens */,
    220 /* Choice Band */, 297 /* Choice Specs */, 287 /* Choice Scarf */, 266 /* Muscle Band */, 267 /* Wise Glasses */,
    268 /* Expert Belt */, 270 /* Life Orb */,
};
static const u16 sItemPrices[NELEMS(sItemsForRent)] = {
    10, 15, 5, 15, 10, 10, 10, 10, 10, 10, 15, 15, 5, 15, 10, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20,
};
static const u16 sBerriesForRent[] = {
    149 /* Cheri */, 150 /* Chesto */, 151 /* Pecha */, 152 /* Rawst */, 153 /* Aspear */, 156 /* Persim */, 157 /* Lum */,
    158 /* Sitrus */, 201 /* Liechi */, 202 /* Ganlon */, 203 /* Salac */, 204 /* Petaya */, 205 /* Apicot */,
    206 /* Lansat */, 207 /* Starf */, 184 /* Occa */, 185 /* Passho */, 186 /* Wacan */, 187 /* Rindo */, 188 /* Yache */,
    189 /* Chople */, 190 /* Kebia */, 191 /* Shuca */, 192 /* Coba */, 193 /* Payapa */, 194 /* Tanga */, 195 /* Charti */,
    196 /* Kasib */, 197 /* Haban */, 198 /* Colbur */, 199 /* Babiri */, 200 /* Chilan */,
};
static const u16 sBerryPrices[NELEMS(sBerriesForRent)] = {
    2, 2, 2, 2, 2, 2, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
};
static const u16 sItemsAvailableByRank[] = { 12, 12, NELEMS(sItemsForRent) };
static const u16 sBerriesAvailableByRank[] = { 8, 8, NELEMS(sBerriesForRent) };

// self_app.c: the heal menu's costs and the ranks they need (sHealMenuEntries' first column), the rank ups' costs
static const u16 sHealingCosts[] = { 10, 8, 12 };
static const u8 sHealRanks[] = { 1, 2, 3 };
static const u16 sRankUpCosts[3][3] = {
    { 0, 100, 100 },
    { 0, 100, 150 },
    { 0, 50, 50 },
};

// opponent_app.c's costs
#define CP_COST_CHECK_IDENTITY 1
#define CP_COST_LEVEL_UP 1
#define CP_COST_LEVEL_DOWN 15
#define CP_COST_SHOW_STATS 2
#define CP_COST_SHOW_MOVES 5
#define CP_COST_RANK_UP 50
// the scene's pass (frontier_scripts_battle_castle.s _0A1C: BufferNumber 0, 50 .. SpendCastlePoints VAR_0x8008, 50)
#define CP_COST_PASS 50

// ---------------------------------------------------------------- the random numbers
u16 PlatCastle_Random(PlatCastle *castle) {
    castle->lcrng = castle->lcrng * LCRNG_MULTIPLIER + LCRNG_INCREMENT;
    return (u16)(castle->lcrng >> 16);
}

// LCRNG_Next() | LCRNG_Next() << 16: the low half drawn first
static u32 Random32(PlatCastle *castle) {
    u32 low = PlatCastle_Random(castle);
    u32 high = PlatCastle_Random(castle);

    return low | (high << 16);
}

static BOOL IsShiny(u32 otID, u32 personality) {
    return ((((otID & 0xffff0000) >> 16) ^ (otID & 0xffff) ^ ((personality & 0xffff0000) >> 16) ^ (personality & 0xffff)) <
            SHINY_ODDS);
}

// ---------------------------------------------------------------- the records (battle_frontier_save.c, battle_frontier_stats.c)
// BattleFrontierStats_GetCastle*Index: which is PLATCASTLE_STAT_*
u32 PlatCastle_StatIndex(u8 challengeType, u32 which) {
    u32 index = PLATCASTLE_STAT_SINGLE;

    switch (challengeType) {
    case PLATCASTLE_SINGLE:
        index = PLATCASTLE_STAT_SINGLE;
        break;
    case PLATCASTLE_DOUBLE:
        index = PLATCASTLE_STAT_SINGLE + PLATCASTLE_STAT_STRIDE;
        break;
    case PLATCASTLE_MULTI:
        index = PLATCASTLE_STAT_SINGLE + 2 * PLATCASTLE_STAT_STRIDE;
        break;
    case PLATCASTLE_MULTI_WFC:
        index = 134;                    // STAT_CASTLE_RECORD_STREAK_MULTI_WFC: a Wi-Fi stat (the core keeps none)
        break;
    }
    return index + which;
}

static u16 GetStat(void *records, u32 stat) {
    return PlatCastle_GetStat(records, stat);
}

// BattleFrontierSave_SetStat: at most 9999
static void SetStat(void *records, u32 stat, u16 value) {
    PlatCastle_SetStat(records, stat, value > PLATCASTLE_STAT_MAX ? PLATCASTLE_STAT_MAX : value);
}

// BattleFrontierSave_AddToStat: a u16 sum
static void AddToStat(void *records, u32 stat, int addValue) {
    u16 value = GetStat(records, stat);

    value += addValue;
    SetStat(records, stat, value);
}

static void SubtractFromStat(void *records, u32 stat, int subtractValue) {
    int value = GetStat(records, stat) - subtractValue;

    if (value < 0) {
        value = 0;
    }
    SetStat(records, stat, (u16)value);
}

static void SetIfBetter(void *records, u32 stat, u16 newValue) {
    u16 currentValue = GetStat(records, stat);

    if (currentValue < newValue) {
        SetStat(records, stat, newValue);
    } else if (currentValue > PLATCASTLE_STAT_MAX) {
        SetStat(records, stat, PLATCASTLE_STAT_MAX);
    }
}

// BattleCastleApp_GetRank (helpers.c)
u8 PlatCastle_GetRank(void *records, u8 challengeType, u8 rankType) {
    return (u8)GetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_RANK + rankType));
}

u16 PlatCastle_GetCurrentCP(void *records, u8 challengeType) {
    return GetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_LATEST_CP));
}

// BattleCastlePersistentSave_SetFlag(CASTLE_SAVE_STREAK_FLAGS)
static void SetStreakFlag(void *records, u8 challengeType, u8 value) {
    PlatCastle_SetStreakFlag(records, challengeType, value >= 1);
}

// ---------------------------------------------------------------- battle_castle_helpers.c
u8 PlatCastle_GetPlayerPartySize(u8 challengeType, BOOL includePartnersMons) {
    switch (challengeType) {
    case PLATCASTLE_SINGLE:
    case PLATCASTLE_DOUBLE:
        return PLATCASTLE_PARTY_SOLO;
    case PLATCASTLE_MULTI:
    case PLATCASTLE_MULTI_WFC:
        return includePartnersMons == FALSE ? PLATCASTLE_PARTY_MULTI : PLATCASTLE_PARTY_MULTI * 2;
    }
    return PLATCASTLE_PARTY_SOLO;
}

u8 PlatCastle_GetOpponentPartySize(u8 challengeType, BOOL includeBothOpponents) {
    switch (challengeType) {
    case PLATCASTLE_SINGLE:
    case PLATCASTLE_DOUBLE:
        return PLATCASTLE_PARTY_SOLO;
    case PLATCASTLE_MULTI:
    case PLATCASTLE_MULTI_WFC:
        return includeBothOpponents == FALSE ? PLATCASTLE_PARTY_MULTI : PLATCASTLE_PARTY_MULTI * 2;
    }
    return PLATCASTLE_PARTY_SOLO;
}

BOOL PlatCastle_IsMultiPlayerChallenge(u8 challengeType) {
    return challengeType == PLATCASTLE_MULTI || challengeType == PLATCASTLE_MULTI_WFC;
}

// BattleCastle_GetCurrentRound (the partner's round of a link Multi: closed)
u16 PlatCastle_GetCurrentRound(PlatCastle *castle) {
    return castle->currentRound;
}

// BattleCastle_GetOpponentTrainerID: Darach at the 21st and 49th battle of a Single streak (the round's 7th, and the second
// Trainer row's 7th of the round before, which a Single never fights); the round's 7th Trainers from the final range
static int GetOpponentTrainerID(PlatCastle *castle, u8 challengeType, int currentRound, int trainerOffset) {
    int currentStreak, spread, min;

    if (challengeType == PLATCASTLE_SINGLE) {
        currentStreak = (currentRound * PLATCASTLE_BATTLES_PER_ROUND) + (trainerOffset + 1);
        if (currentStreak == PLATCASTLE_STREAK_SILVER) {
            return PLATCASTLE_DARACH_SILVER;
        } else if (currentStreak == PLATCASTLE_STREAK_GOLD) {
            return PLATCASTLE_DARACH_GOLD;
        }
    }
    if (currentRound >= (int)NELEMS(sOpponentPools)) {
        currentRound = NELEMS(sOpponentPools) - 1;
    }
    if (trainerOffset == PLATCASTLE_BATTLES_PER_ROUND - 1 || trainerOffset == (PLATCASTLE_BATTLES_PER_ROUND * 2) - 1) {
        spread = sOpponentPools[currentRound].finalMax - sOpponentPools[currentRound].finalMin;
        min = sOpponentPools[currentRound].finalMin;
    } else {
        spread = sOpponentPools[currentRound].normalMax - sOpponentPools[currentRound].normalMin;
        min = sOpponentPools[currentRound].normalMin;
    }
    return min + PlatCastle_Random(castle) % spread;
}

// BattleCastle_PickOpponentTrainers: no Trainer twice in a round
static void PickOpponentTrainers(PlatCastle *castle, u8 challengeType, int currentRound, u16 trainerIDs[], u8 numTrainers) {
    int i = 0, j;

    do {
        trainerIDs[i] = (u16)GetOpponentTrainerID(castle, challengeType, currentRound, i);
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

// BattleCastle_GetAIMask: Darach's battles the full AI; rounds 1-2 none, 3-4 the basic one, then the full
u16 PlatCastle_GetAIMask(PlatCastle *castle) {
    u16 round, aiMask;

    if (castle->challengeType == PLATCASTLE_SINGLE) {
        if (castle->trainerIDs[castle->currentBattle] == PLATCASTLE_DARACH_SILVER ||
            castle->trainerIDs[castle->currentBattle] == PLATCASTLE_DARACH_GOLD) {
            return PLATCASTLE_AI_BASIC | PLATCASTLE_AI_EVAL_ATTACK | PLATCASTLE_AI_EXPERT;
        }
    }
    round = PlatCastle_GetCurrentRound(castle);
    aiMask = PLATCASTLE_AI_BASIC | PLATCASTLE_AI_EVAL_ATTACK | PLATCASTLE_AI_EXPERT;
    switch (round + 1) {
    case 1:
    case 2:
        aiMask = 0;
        break;
    case 3:
    case 4:
        aiMask = PLATCASTLE_AI_BASIC;
        break;
    }
    return aiMask;
}

// BattleCastle_RevivePokemon: a fainted Pokémon back at 1 HP, every status cured
static void RevivePokemon(PlatCastle *castle) {
    int i;

    for (i = 0; i < castle->playerCount; i++) {
        if (!PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_EXISTS)) {
            continue;
        }
        if (PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_HP) == 0) {
            PlatCastle_MonSet(castle, (u8)i, PLATCASTLE_MON_HP, 1);
        }
        PlatCastle_MonSet(castle, (u8)i, PLATCASTLE_MON_STATUS, 0);
    }
}

// BattleCastle_SpendCastlePoints: the CP now down (not below 0), the CP spent up (at most 9999)
void PlatCastle_SpendCastlePoints(void *records, u8 challengeType, int castlePoints) {
    u16 totalSpent;

    SubtractFromStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_LATEST_CP), castlePoints);
    totalSpent = GetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_SPENT_CP));
    if (totalSpent + castlePoints > PLATCASTLE_STAT_MAX) {
        SetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_SPENT_CP), PLATCASTLE_STAT_MAX);
    } else {
        AddToStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_SPENT_CP), castlePoints);
    }
}

// ---------------------------------------------------------------- the opponents' Pokémon (frontier_opponents.c)
// GetIVsForTrainer
static u8 GetIVsForTrainer(u16 trainerID) {
    if (trainerID < 100) {
        return (MAX_IVS_SINGLE_STAT / 8) * 1;
    } else if (trainerID < 120) {
        return (MAX_IVS_SINGLE_STAT / 8) * 2;
    } else if (trainerID < 140) {
        return (MAX_IVS_SINGLE_STAT / 8) * 3;
    } else if (trainerID < 160) {
        return (MAX_IVS_SINGLE_STAT / 8) * 4;
    } else if (trainerID < 180) {
        return (MAX_IVS_SINGLE_STAT / 8) * 5;
    } else if (trainerID < 200) {
        return (MAX_IVS_SINGLE_STAT / 8) * 6;
    } else if (trainerID < 220) {
        return (MAX_IVS_SINGLE_STAT / 8) * 7;
    }
    return MAX_IVS_SINGLE_STAT;
}

// FrontierPokemon_Init (alwaysFalse: the set's own item)
static u32 Mon_Init(PlatCastle *castle, PlatCastleMon *mon, u16 setID, u32 otID, u32 personality, u8 ivs) {
    PlatCastleSet set;
    u8 friendship = MAX_FRIENDSHIP_VALUE;
    u16 ability2;
    int i, evs;

    PlatCastle_ReadSet(setID, &set);
    mon->species = set.species;
    mon->form = (u8)set.form;
    mon->item = set.item;
    for (i = 0; i < 4; i++) {
        mon->moves[i] = set.moves[i];
        if (set.moves[i] == MOVE_FRUSTRATION) {
            friendship = 0;
        }
    }
    mon->otID = otID;
    if (personality == 0) {
        do {
            personality = Random32(castle);
        } while (set.nature != personality % NATURE_COUNT || IsShiny(otID, personality) == TRUE);
    }
    mon->personality = personality;
    mon->nature = (u8)(personality % NATURE_COUNT);
    mon->ivs = ivs;
    evs = 0;
    for (i = 0; i < STAT_MAX; i++) {
        if (set.evFlags & (1 << i)) {
            evs++;
        }
    }
    // (set 0, the padding a resumed solo challenge loads as its fourth Pokémon, has no flag: Platinum's quotient goes to no
    // stat)
    if (evs == 0 || MAX_EVS_ALL_STATS / evs > MAX_EVS_SINGLE_STAT) {
        evs = MAX_EVS_SINGLE_STAT;
    } else {
        evs = MAX_EVS_ALL_STATS / evs;
    }
    for (i = 0; i < STAT_MAX; i++) {
        mon->evs[i] = (set.evFlags & (1 << i)) ? (u8)evs : 0;
    }
    ability2 = PlatCastle_SpeciesAbility(mon->species, 1);
    if (ability2 != 0 && (mon->personality & 1)) {
        mon->ability = (u8)ability2;
    } else {
        mon->ability = (u8)PlatCastle_SpeciesAbility(mon->species, 0);
    }
    mon->friendship = friendship;
    return personality;
}

// BattleFrontier_LoadOpponentMonData: a trainer id first, then the Pokémon
static u32 LoadOpponentMonData(PlatCastle *castle, PlatCastleMon *mon, u16 setID, u8 ivs, u32 personality) {
    u32 otID = Random32(castle);

    return Mon_Init(castle, mon, setID, otID, personality, ivs);
}

// BattleFrontier_LoadFrontierPokemon
static void LoadFrontierPokemon(PlatCastle *castle, PlatCastleMon *mons, const u16 *setIDs, const u8 *ivList,
                                const u32 *personalities, u32 *resultPersonalities, int numMons) {
    int i;
    u32 personality;

    for (i = 0; i < numMons; i++) {
        personality = LoadOpponentMonData(castle, &mons[i], setIDs[i], ivList == NULL ? 0 : ivList[i],
                                          personalities == NULL ? 0 : personalities[i]);
        if (resultPersonalities != NULL) {
            resultPersonalities[i] = personality;
        }
    }
}

// The random numbers of FrontierPokemon_InitPokemon (Pokemon_InitWith with the personality and OTID_NOT_SHINY: a trainer id
// that isn't shiny with it; the IVs as one number, which, 32 or more, makes it draw random IVs before it sets them)
static void InitPokemonRandom(PlatCastle *castle, u32 personality, u8 ivs) {
    u32 otID, combined;

    do {
        otID = Random32(castle);
    } while (IsShiny(otID, personality));
    combined = (u32)ivs * (1 | (1 << 5) | (1 << 10) | (1 << 15) | (1 << 20) | (1 << 25));
    if ((combined & 0x3fffffff) >= INIT_IVS_RANDOM) {
        PlatCastle_Random(castle);
        PlatCastle_Random(castle);
    }
}

// SelectPokemonForTrainer: sets of the Trainer's list, no species or item twice (nor the partner's, for 50 tries)
static BOOL SelectPokemonForTrainer(PlatCastle *castle, u16 trainerID, const u16 partnersSpecies[],
                                    const u16 partnersItems[], int partnersNumMons, int numMons, u16 selectedMons[]) {
    PlatCastleSet newMon[PLATCASTLE_MAX_PARTY];
    u16 sets[128];                      // (the Frontier Trainers have 100 sets at most)
    u16 numSets = PlatCastle_TrainerSets(trainerID, sets, NELEMS(sets));
    int i = 0, j, partnerConflictCounter = 0;
    u16 narcIdx;

    if (numSets == 0) {                 // (no Trainer file: nothing to draw from)
        for (i = 0; i < numMons; i++) {
            selectedMons[i] = 0;
        }
        return FALSE;
    }
    while (i != numMons) {
        narcIdx = sets[PlatCastle_Random(castle) % numSets];
        PlatCastle_ReadSet(narcIdx, &newMon[i]);
        for (j = 0; j < i; j++) {
            if (newMon[j].species == newMon[i].species || newMon[j].item == newMon[i].item) {
                break;
            }
        }
        if (j != i) {
            continue;
        }
        if (partnerConflictCounter < 50) {
            for (j = 0; j < partnersNumMons; j++) {
                if (newMon[i].species == partnersSpecies[j] || newMon[i].item == partnersItems[j]) {
                    break;
                }
            }
            if (j != partnersNumMons) {
                partnerConflictCounter++;
                continue;
            }
        }
        selectedMons[i] = narcIdx;
        i++;
    }
    return partnerConflictCounter >= 50;
}

// BattleFrontier_GetPokemonForTrainers: the IVs by the Trainer's id, its sets, then the Pokémon made
static void GetPokemonForTrainers(PlatCastle *castle, u8 numMons, u16 trainerID, u16 trainerID2, u16 *monSetIDs,
                                  PlatCastleMon *resultMons, u8 *ivs, u32 *personalities, u8 isMultiplayerChallenge) {
    u16 alreadySelectedSpecies[4] = { 0 };
    u16 alreadySelectedItems[4] = { 0 };
    PlatCastleSet mon;
    int i;

    for (i = 0; i < numMons; i++) {
        ivs[i] = GetIVsForTrainer(trainerID);
    }
    if (!isMultiplayerChallenge) {
        SelectPokemonForTrainer(castle, trainerID, alreadySelectedSpecies, alreadySelectedItems, 0, numMons, monSetIDs);
    } else {
        SelectPokemonForTrainer(castle, trainerID, alreadySelectedSpecies, alreadySelectedItems, 0, numMons / 2, monSetIDs);
        for (i = 0; i < numMons / 2; i++) {
            PlatCastle_ReadSet(monSetIDs[i], &mon);
            alreadySelectedSpecies[i] = mon.species;
            alreadySelectedItems[i] = mon.item;
        }
        SelectPokemonForTrainer(castle, trainerID2, alreadySelectedSpecies, alreadySelectedItems, numMons / 2, numMons / 2,
                                &monSetIDs[numMons / 2]);
        for (i = 0; i < numMons / 2; i++) {
            ivs[i + (numMons / 2)] = GetIVsForTrainer(trainerID2);
        }
    }
    LoadFrontierPokemon(castle, resultMons, monSetIDs, ivs, NULL, personalities, numMons);
}

// ---------------------------------------------------------------- battle_castle.c
static void Save_Init(PlatCastleSave *save) {
    u8 *bytes = (u8 *)save;
    u32 i;

    for (i = 0; i < sizeof(PlatCastleSave); i++) {
        bytes[i] = 0;
    }
}

// BattleCastle_Init. castle->lcrng is the caller's (seeded); the castle's party is the game's (PlatCastle_PartyAddFieldMon)
void PlatCastle_Init(PlatCastle *castle, PlatCastleSave *save, void *records, u16 resuming, u8 challengeType, u8 slot1,
                     u8 slot2, u8 slot3) {
    u32 lcrng = castle->lcrng;
    u8 *bytes = (u8 *)castle;
    u8 streakActive, partySize;
    u16 i;

    for (i = 0; i < sizeof(PlatCastle); i++) {      // MI_CpuClear8
        bytes[i] = 0;
    }
    castle->magic = PLATCASTLE_WORK_MAGIC;
    castle->lcrng = lcrng;

    if (!resuming) {
        castle->challengeType = challengeType;
        castle->currentBattle = 0;
        Save_Init(save);
        if (castle->challengeType == PLATCASTLE_MULTI_WFC) {
            streakActive = FALSE;                        // SystemVars_GetWiFiFrontierCleared: the Wi-Fi Multi is closed
        } else {
            streakActive = (u8)PlatCastle_GetStreakFlag(records, castle->challengeType);
        }
        if (streakActive == TRUE) {
            castle->currentStreak = GetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_STREAK));
        } else {
            castle->currentStreak = 0;
            SetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_CP), 0);
            SetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_SPENT_CP), 0);
            for (i = 0; i < PLATCASTLE_RANKS; i++) {
                SetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_RANK + i), 1);
            }
        }
        castle->currentRound = castle->currentStreak / PLATCASTLE_BATTLES_PER_ROUND;
        castle->partySlots[0] = slot1;
        castle->partySlots[1] = slot2;
        castle->partySlots[2] = slot3;
        castle->initialCP = GetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_CP));
        AddToStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_CP), 10);
    } else {
        castle->challengeType = save->challengeType;
        castle->currentBattle = save->currentBattleNum;
        castle->currentStreak = GetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_STREAK));
        castle->currentRound = castle->currentStreak / PLATCASTLE_BATTLES_PER_ROUND;
        for (i = 0; i < PLATCASTLE_PARTY_SOLO; i++) {
            castle->partySlots[i] = save->partySlots[i];
        }
    }

    for (i = 0; i < PLATCASTLE_PARTY_SOLO; i++) {
        castle->savedHeldItems[i] = (u16)PlatCastle_FieldMonItem(castle, castle->partySlots[i]);
    }
    // The castle's party: copies of the field party's Pokémon, no held item, Level 50 at most
    partySize = PlatCastle_GetPlayerPartySize(castle->challengeType, FALSE);
    for (i = 0; i < partySize; i++) {
        PlatCastle_PartyAddFieldMon(castle, castle->partySlots[i]);
        castle->playerCount++;
        PlatCastle_MonSet(castle, (u8)i, PLATCASTLE_MON_ITEM, ITEM_NONE);
        if (PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_LEVEL) > PLATCASTLE_MAX_LEVEL) {
            PlatCastle_MonSetLevel(castle, (u8)i, PLATCASTLE_MAX_LEVEL);
        }
    }
}

// SelectTrainersAndFirstBattlesMons: the PP the battle starts with, the round's 14 Trainers, the first one's Pokémon
static void SelectTrainersAndFirstBattlesMons(PlatCastle *castle) {
    int i, j;

    for (i = 0; i < castle->playerCount; i++) {
        for (j = 0; j < 4; j++) {
            castle->startingPP[i][j] = (u16)PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_PP1 + j);
        }
    }
    PickOpponentTrainers(castle, castle->challengeType, PlatCastle_GetCurrentRound(castle), castle->trainerIDs,
                         PLATCASTLE_TRAINERS);
    GetPokemonForTrainers(castle, PlatCastle_GetOpponentPartySize(castle->challengeType, TRUE),
                          castle->trainerIDs[castle->currentBattle],
                          castle->trainerIDs[castle->currentBattle + PLATCASTLE_BATTLES_PER_ROUND], castle->monSetIDs,
                          castle->opponentMons, castle->opponentMonIVs, castle->opponentMonPersonalities,
                          PlatCastle_IsMultiPlayerChallenge(castle->challengeType));
}

// LoadPlayersPartyFromSave: the HP, PP, status and held item each Pokémon had when the challenge was saved
static void LoadPlayersPartyFromSave(PlatCastle *castle, PlatCastleSave *save) {
    int i, j;

    for (i = 0; i < castle->playerCount; i++) {
        PlatCastle_MonSet(castle, (u8)i, PLATCASTLE_MON_HP, save->monHP[i]);
        for (j = 0; j < 4; j++) {
            PlatCastle_MonSet(castle, (u8)i, PLATCASTLE_MON_PP1 + j, save->monPP[i][j]);
        }
        PlatCastle_MonSet(castle, (u8)i, PLATCASTLE_MON_STATUS, save->monStatus[i]);
        PlatCastle_MonSet(castle, (u8)i, PLATCASTLE_MON_ITEM, save->heldItems[i]);
    }
}

// LoadTrainersAndMonsFromSave: the Trainers and the set ids back; four Pokémon made from the sets into the opponents' party,
// which the script makes again before a battle (BattleCastle_SetupNextOpponent): only their random numbers stay
static void LoadTrainersAndMonsFromSave(PlatCastle *castle, PlatCastleSave *save) {
    PlatCastleMon mons[PLATCASTLE_MAX_PARTY];
    u8 ivs[PLATCASTLE_MAX_PARTY] = { 0 };       // (Platinum's are never set: see the top)
    u32 personalities[PLATCASTLE_MAX_PARTY];
    u16 setIDs[PLATCASTLE_MAX_PARTY];
    int i;

    LoadPlayersPartyFromSave(castle, save);
    for (i = 0; i < PLATCASTLE_TRAINERS; i++) {
        castle->trainerIDs[i] = save->trainerIDs[i];
    }
    for (i = 0; i < PLATCASTLE_PARTY_MULTI * 2; i++) {
        setIDs[i] = save->monSetIDs[i];
        castle->monSetIDs[i] = setIDs[i];
    }
    LoadFrontierPokemon(castle, mons, setIDs, ivs, NULL, personalities, PLATCASTLE_MAX_PARTY);
    for (i = 0; i < PLATCASTLE_PARTY_MULTI * 2; i++) {
        InitPokemonRandom(castle, mons[i].personality, mons[i].ivs);
        if (castle->opponentCount < 6) {
            castle->opponentCount++;
        }
    }
}

void PlatCastle_LoadTrainersForRound(PlatCastle *castle, PlatCastleSave *save, u16 resuming) {
    if (!resuming) {
        SelectTrainersAndFirstBattlesMons(castle);
    } else {
        LoadTrainersAndMonsFromSave(castle, save);
    }
}

// BattleCastle_Save. saveType 2 (the rest's quick save) keeps the records and the streak flag
void PlatCastle_Save(PlatCastle *castle, PlatCastleSave *save, void *records, u8 saveType) {
    u16 recordStreak, newRecord, i;
    u32 latestCP;
    int j;

    save->challengeType = castle->challengeType;
    save->didSave = TRUE;
    save->currentBattleNum = castle->currentBattle;
    SetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_STREAK), castle->currentStreak);

    if (saveType != 2) {
        recordStreak = GetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_RECORD_STREAK));
        SetIfBetter(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_RECORD_STREAK), castle->currentStreak);
        newRecord = GetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_RECORD_STREAK));
        latestCP = GetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_CP));
        if (castle->currentStreak == recordStreak) {
            SetIfBetter(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_RECORD_CP), (u16)latestCP);
        } else if (recordStreak < newRecord) {
            SetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_RECORD_CP), (u16)latestCP);
        }
        SetStreakFlag(records, castle->challengeType, castle->saveStreak);
        if (castle->challengeType == PLATCASTLE_MULTI_WFC) {
            SetStat(records, PLATCASTLE_STAT_WFC_STREAK_ACTIVE, castle->saveStreak);
        }
    }
    for (i = 0; i < PLATCASTLE_TRAINERS; i++) {
        save->trainerIDs[i] = castle->trainerIDs[i];
    }
    for (i = 0; i < PLATCASTLE_PARTY_SOLO; i++) {
        save->partySlots[i] = castle->partySlots[i];
    }
    for (i = 0; i < castle->playerCount; i++) {
        save->monHP[i] = (u16)PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_HP);
        for (j = 0; j < 4; j++) {
            save->monPP[i][j] = (u8)PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_PP1 + j);
        }
        save->monStatus[i] = PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_STATUS);
        save->heldItems[i] = (u16)PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_ITEM);
    }
    for (i = 0; i < castle->opponentCount && i < PLATCASTLE_MAX_PARTY; i++) {
        save->monSetIDs[i] = castle->monSetIDs[i];
    }
}

// BattleCastle_SaveOnLoss: the ranks back to 1
void PlatCastle_SaveOnLoss(PlatCastle *castle, PlatCastleSave *save, void *records) {
    int i;

    for (i = 0; i < PLATCASTLE_RANKS; i++) {
        SetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_RANK + i), 1);
    }
    PlatCastle_Save(castle, save, records, 1);
}

void PlatCastle_SaveOnCompletingRound(PlatCastle *castle, PlatCastleSave *save, void *records) {
    castle->saveStreak = TRUE;
    if (castle->currentRound < PLATCASTLE_ROUNDS) {
        castle->currentRound++;
    }
    castle->currentBattle = 0;
    PlatCastle_Save(castle, save, records, 0);
}

// BattleCastle_SetupOpponentsParty: Party_Init, then each Pokémon made at Level 50 (its random numbers) and added
void PlatCastle_SetupOpponentsParty(PlatCastle *castle) {
    u8 partySize = PlatCastle_GetOpponentPartySize(castle->challengeType, TRUE);
    int i;

    castle->opponentCount = 0;
    for (i = 0; i < partySize; i++) {
        InitPokemonRandom(castle, castle->opponentMons[i].personality, castle->opponentMons[i].ivs);
        castle->opponentCount++;
    }
}

void PlatCastle_SetupFirstOpponentsParty(PlatCastle *castle) {
    PlatCastle_SetupOpponentsParty(castle);
}

void PlatCastle_SetupNextOpponentsParty(PlatCastle *castle) {
    GetPokemonForTrainers(castle, PlatCastle_GetOpponentPartySize(castle->challengeType, TRUE),
                          castle->trainerIDs[castle->currentBattle],
                          castle->trainerIDs[castle->currentBattle + PLATCASTLE_BATTLES_PER_ROUND], castle->monSetIDs,
                          castle->opponentMons, castle->opponentMonIVs, castle->opponentMonPersonalities,
                          PlatCastle_IsMultiPlayerChallenge(castle->challengeType));
    PlatCastle_SetupOpponentsParty(castle);
}

// CallBattleCastleFunction's BC_FUNC_CREATE_OPPONENT_MONS: the sets again, with the IVs and personalities kept
void PlatCastle_CreateOpponentMons(PlatCastle *castle) {
    LoadFrontierPokemon(castle, castle->opponentMons, castle->monSetIDs, castle->opponentMonIVs,
                        castle->opponentMonPersonalities, NULL, PLATCASTLE_MAX_PARTY);
}

// BattleCastle_PrepForNextBattle: the PP now are the next battle's starting PP; the fainted back at 1 HP, every status
// cured; the opponent's information bought for this battle forgotten
void PlatCastle_PrepForNextBattle(PlatCastle *castle) {
    u8 partyOffset = 0, playerPartySize = PlatCastle_GetPlayerPartySize(castle->challengeType, FALSE);
    int i, j;

    for (i = partyOffset; i < playerPartySize + partyOffset; i++) {
        for (j = 0; j < 4; j++) {
            castle->startingPP[i - partyOffset][j] = (u16)PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_PP1 + j);
        }
    }
    RevivePokemon(castle);
    for (i = 0; i < PLATCASTLE_PARTY_MULTI * 2; i++) {
        castle->appIdentityUnlocked[i] = FALSE;
        castle->levelAdjustments[i] = PLATCASTLE_LEVEL_NONE;
        castle->appStatsUnlocked[i] = FALSE;
        castle->appMovesUnlocked[i] = FALSE;
    }
}

// BattleCastle_CalcCPEarnedFromBattle: 3 a Pokémon standing, 3 more at full HP, else 2 at half or more, else 1; 1 with no
// status; 8, 6 or 4 for 5, 10 or 15 PP used at most; 7 an opponent raised five levels; 1 at least
int PlatCastle_CalcCPEarnedFromBattle(PlatCastle *castle) {
    u8 cpFactors[20];
    int i, j, earnedCP = 0, remainingPP = 0, startingPP = 0;
    u8 partyOffset = 0;
    u8 playerPartySize = PlatCastle_GetPlayerPartySize(castle->challengeType, FALSE);
    u8 opponentPartySize = PlatCastle_GetOpponentPartySize(castle->challengeType, TRUE);
    u32 currentHP, maxHP;

    for (i = 0; i < 20; i++) {
        cpFactors[i] = 0;
    }
    castle->monFainted = FALSE;
    for (i = partyOffset; i < playerPartySize + partyOffset; i++) {
        if (PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_EXISTS) == 0) {
            continue;
        }
        currentHP = PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_HP);
        maxHP = PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_MAX_HP);
        if (currentHP > 0) {
            cpFactors[0]++;
            if (currentHP == maxHP) {
                cpFactors[1]++;
            } else if (currentHP >= maxHP / 2) {
                cpFactors[2]++;
            } else {
                cpFactors[3]++;
            }
            if (PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_STATUS) == 0) {
                cpFactors[4]++;
            }
        } else {
            castle->monFainted = TRUE;
        }
        for (j = 0; j < 4; j++) {
            remainingPP += PlatCastle_MonGet(castle, (u8)i, PLATCASTLE_MON_PP1 + j);
        }
    }
    for (i = 0; i < opponentPartySize; i++) {
        if (castle->levelAdjustments[i] == PLATCASTLE_LEVEL_UP_5) {
            cpFactors[8]++;
        }
    }
    for (i = 0; i < playerPartySize; i++) {
        for (j = 0; j < 4; j++) {
            startingPP += castle->startingPP[i][j];
        }
    }
    if (startingPP - remainingPP <= 5) {
        cpFactors[5]++;
    } else if (startingPP - remainingPP <= 10) {
        cpFactors[6]++;
    } else if (startingPP - remainingPP <= 15) {
        cpFactors[7]++;
    }
    earnedCP += cpFactors[0] * 3;
    earnedCP += cpFactors[1] * 3;
    earnedCP += cpFactors[2] * 2;
    earnedCP += cpFactors[3] * 1;
    earnedCP += cpFactors[4] * 1;
    earnedCP += cpFactors[5] * 8;
    earnedCP += cpFactors[6] * 6;
    earnedCP += cpFactors[7] * 4;
    earnedCP += cpFactors[8] * 7;
    if (earnedCP <= 0) {
        earnedCP = 1;
    }
    return earnedCP;
}

// BattleCastle_ReceiveCastlePoints (Platinum also adds them to the game record RECORD_CASTLE_POINTS_RECEIVED: Black 2 has
// no such record)
void PlatCastle_ReceiveCastlePoints(void *records, u8 challengeType, int newCP) {
    u16 currentCP = GetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_LATEST_CP));

    if (currentCP + newCP > PLATCASTLE_STAT_MAX) {
        SetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_LATEST_CP), PLATCASTLE_STAT_MAX);
    } else {
        AddToStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_LATEST_CP), newCP);
    }
}

// BattleCastle_GetEarnedBP: by the round (the one just completed: SaveOnCompletingRound counted it); Darach's two 20
u16 PlatCastle_GetEarnedBP(PlatCastle *castle) {
    u8 bp;
    u16 currentRound = castle->currentRound;

    if (castle->challengeType == PLATCASTLE_SINGLE || castle->challengeType == PLATCASTLE_DOUBLE) {
        bp = currentRound >= PLATCASTLE_ROUNDS ? sBPPerRoundSolo[PLATCASTLE_ROUNDS] : sBPPerRoundSolo[currentRound];
    } else {
        bp = currentRound >= PLATCASTLE_ROUNDS ? sBPPerRoundWifi[PLATCASTLE_ROUNDS] : sBPPerRoundWifi[currentRound];
    }
    if (castle->challengeType == PLATCASTLE_SINGLE) {
        if (castle->currentStreak == PLATCASTLE_STREAK_SILVER || castle->currentStreak == PLATCASTLE_STREAK_GOLD) {
            bp = 20;
        }
    }
    return bp;
}

// BC_FUNC_GET_NEXT_BATTLE_TYPE: Darach next?
u16 PlatCastle_GetNextBattleType(PlatCastle *castle) {
    if (castle->challengeType == PLATCASTLE_SINGLE) {
        if (castle->currentStreak + 1 == PLATCASTLE_STREAK_SILVER) {
            return PLATCASTLE_NEXT_SILVER;
        } else if (castle->currentStreak + 1 == PLATCASTLE_STREAK_GOLD) {
            return PLATCASTLE_NEXT_GOLD;
        }
    }
    return PLATCASTLE_NEXT_NORMAL;
}

// The level a shown or fought opponent has: Level 50 (BattleCastle_GetOpponentLevel), five up or down as the opponent app's
// UpdateLevelAdjustment set it (the experience of Level 55 or 45)
u8 PlatCastle_GetOpponentLevel(PlatCastle *castle, u8 slot) {
    switch (castle->levelAdjustments[slot]) {
    case PLATCASTLE_LEVEL_UP_5:
        return PLATCASTLE_MAX_LEVEL + 5;
    case PLATCASTLE_LEVEL_DOWN_5:
        return PLATCASTLE_MAX_LEVEL - 5;
    }
    return PLATCASTLE_MAX_LEVEL;
}

// The lobby's BattleCastle_ClearActiveStreak (scrcmd_battle_castle.c)
void PlatCastle_ClearActiveStreak(void *records, u8 challengeType) {
    int i;

    SetStreakFlag(records, challengeType, FALSE);
    if (challengeType == PLATCASTLE_MULTI_WFC) {
        SetStat(records, PLATCASTLE_STAT_WFC_STREAK_ACTIVE, 0);
    }
    SetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_LATEST_STREAK), 0);
    SetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_LATEST_CP), 0);
    for (i = 0; i < PLATCASTLE_RANKS; i++) {
        SetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_RANK + i), 1);
    }
}

// ---------------------------------------------------------------- CallBattleCastleFunction (frscrcmd_battle_castle.c)
BOOL PlatCastle_Function(PlatCastle *castle, PlatCastleSave *save, void *records, u8 fn, u8 arg1, u8 arg2, u16 *result) {
    int v10;

    switch (fn) {
    case PLATCASTLE_FN_SET_CHALLENGE_TYPE:
        castle->challengeType = arg1;
        break;
    case PLATCASTLE_FN_GET_SELECTED_APP_SLOT:
        *result = arg1 < 6 ? castle->selectedAppSlot : 0;
        break;
    case PLATCASTLE_FN_GET_CURRENT_STREAK:
        *result = castle->currentStreak;
        break;
    case PLATCASTLE_FN_INCREMENT_CURRENT_STREAK:
        if (castle->currentStreak < PLATCASTLE_STAT_MAX) {
            castle->currentStreak++;
        }
        break;
    case PLATCASTLE_FN_HAS_SAVED:
        *result = save->didSave;
        break;
    case PLATCASTLE_FN_QUICKSAVE:
        PlatCastle_Save(castle, save, records, 2);
        break;
    case PLATCASTLE_FN_INCREMENT_CURRENT_BATTLE:
        *result = ++castle->currentBattle;
        break;
    case PLATCASTLE_FN_GET_MONS_SPECIES:
        *result = castle->opponentMons[arg1 & 3].species;
        break;
    case PLATCASTLE_FN_GET_MONS_MOVE:
        *result = castle->opponentMons[arg1 & 3].moves[arg2 & 3];
        break;
    case PLATCASTLE_FN_GET_CURRENT_ROUND:
        *result = PlatCastle_GetCurrentRound(castle);
        break;
    case PLATCASTLE_FN_SAVE_ON_LOSS:
        PlatCastle_SaveOnLoss(castle, save, records);
        break;
    case PLATCASTLE_FN_SAVE_ON_COMPLETING_ROUND:
        PlatCastle_SaveOnCompletingRound(castle, save, records);
        break;
    case PLATCASTLE_FN_GET_CURRENT_BATTLE:
        *result = castle->currentBattle;
        break;
    case PLATCASTLE_FN_UNK_24:                      // the partner's retire (unk_A10) and its answer (unk_A11): the link's
    case PLATCASTLE_FN_UNK_26:
        *result = 0;
        break;
    case PLATCASTLE_FN_GET_CP_FROM_BATTLE:
        *result = (u16)PlatCastle_CalcCPEarnedFromBattle(castle);
        PlatCastle_ReceiveCastlePoints(records, castle->challengeType, *result);
        break;
    case PLATCASTLE_FN_PREP_FOR_NEXT_BATTLE:
        PlatCastle_PrepForNextBattle(castle);
        break;
    case PLATCASTLE_FN_UNK_30:
        *result = castle->unk_A1B >= 6 ? castle->unk_A1B - 6 : castle->unk_A1B;
        break;
    case PLATCASTLE_FN_UNK_31:
        castle->unk_A1B = 0;
        castle->unk_A18 = 0;
        break;
    case PLATCASTLE_FN_UNK_32:
        castle->unk_A18 = arg1;
        break;
    case PLATCASTLE_FN_UNK_33:                      // the link's pass (the host's net id: 0)
        v10 = castle->unk_A1B >= 6 ? 0 : 1;
        if (v10 == 1) {
            PlatCastle_SpendCastlePoints(records, castle->challengeType, CP_COST_PASS);
        } else {
            castle->partnersCP -= CP_COST_PASS;
        }
        break;
    case PLATCASTLE_FN_UNK_34:
        *result = 0;
        if (PlatCastle_IsMultiPlayerChallenge(castle->challengeType) == TRUE && castle->unk_A1B >= 6) {
            *result = 1;
        }
        break;
    case PLATCASTLE_FN_IS_MULTIPLAYER_CHALLENGE:
        *result = PlatCastle_IsMultiPlayerChallenge(castle->challengeType);
        break;
    case PLATCASTLE_FN_GET_CHALLENGE_TYPE:
        *result = castle->challengeType;
        break;
    case PLATCASTLE_FN_CHECK_IF_MON_FAINTED:
        *result = castle->monFainted;
        break;
    case PLATCASTLE_FN_GET_EARNED_BP:
        *result = PlatCastle_GetEarnedBP(castle);
        break;
    case PLATCASTLE_FN_CHECK_HAVE_HEARD_DARACHS_INTRO:
        *result = (u16)PlatCastle_GetHeardIntro(records);
        PlatCastle_SetHeardIntro(records);
        break;
    case PLATCASTLE_FN_GET_NEXT_BATTLE_TYPE:
        *result = PlatCastle_GetNextBattleType(castle);
        break;
    case PLATCASTLE_FN_CREATE_OPPONENT_MONS:
        PlatCastle_CreateOpponentMons(castle);
        break;
    case PLATCASTLE_FN_SETUP_OPPONENTS_PARTY:
        PlatCastle_SetupOpponentsParty(castle);
        break;
    case PLATCASTLE_FN_CHECK_SEEN_VALET_INTRO:
        *result = castle->seenCastleValetIntro;
        castle->seenCastleValetIntro = TRUE;
        break;
    case PLATCASTLE_FN_UPDATE_CP:                   // the Wi-Fi Multi's (closed)
        if (castle->challengeType == PLATCASTLE_MULTI_WFC) {
            if (arg1 == 0) {
                castle->newCP = PlatCastle_GetCurrentCP(records, castle->challengeType);
                SetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_CP), castle->initialCP);
            } else {
                SetStat(records, PlatCastle_StatIndex(castle->challengeType, PLATCASTLE_STAT_LATEST_CP), castle->newCP);
            }
        }
        break;
    case PLATCASTLE_FN_RESET_SYSTEM:                // the game's (castle_field.c)
    case PLATCASTLE_FN_RESTORE_HELD_ITEMS:
    case PLATCASTLE_FN_GET_OPPONENT_OBJECT_ID:
    case PLATCASTLE_FN_INIT_COMM_MANAGER:
    case PLATCASTLE_FN_UPDATE_EMBLEM_FRAME:
    case PLATCASTLE_FN_LOAD_TRAINERS:
        return FALSE;
    default:                                        // (Platinum's switch has no other case: nothing)
        break;
    }
    return TRUE;
}

// ---------------------------------------------------------------- the purchases (self_app.c, opponent_app.c, the scene)
u16 PlatCastle_RentalCount(void *records, u8 challengeType, BOOL items) {
    u8 rank = PlatCastle_GetRank(records, challengeType, PLATCASTLE_RANK_RENTALS);

    if (rank < 1 || rank > 3) {         // (Platinum's table read out of its range: never, the ranks are 1-3)
        rank = 1;
    }
    return items ? sItemsAvailableByRank[rank - 1] : sBerriesAvailableByRank[rank - 1];
}

// GetItemIDFromListPos, GetItemPriceFromListPos
u16 PlatCastle_RentalItem(BOOL items, u16 row) {
    if (items) {
        return row < NELEMS(sItemsForRent) ? sItemsForRent[row] : ITEM_NONE;
    }
    return row < NELEMS(sBerriesForRent) ? sBerriesForRent[row] : ITEM_NONE;
}

u16 PlatCastle_RentalPrice(BOOL items, u16 row) {
    if (items) {
        return row < NELEMS(sItemPrices) ? sItemPrices[row] : 0;
    }
    return row < NELEMS(sBerryPrices) ? sBerryPrices[row] : 0;
}

// IsMonMissingPP
static BOOL IsMonMissingPP(PlatCastle *castle, u8 slot) {
    BOOL isMissingPP = FALSE;
    int i;

    for (i = 0; i < 4; i++) {
        if (PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_PP1 + i) != PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_MAX_PP1 + i)) {
            isMissingPP = TRUE;
        }
    }
    return isMissingPP;
}

// HealPokemon: a Max Potion's effect (HP below the maximum: to the maximum), a Max Elixir's (each move's PP below its
// maximum: to the maximum), or both (Pokemon_ApplyItemEffects with ITEM_MAX_POTION, ITEM_MAX_ELIXIR)
static void HealPokemon(PlatCastle *castle, u8 slot, u32 kind) {
    u32 maxHP, move, maxPP;
    int i;

    if (kind == PLATCASTLE_BUY_HEAL_HP || kind == PLATCASTLE_BUY_HEAL_ALL) {
        maxHP = PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_MAX_HP);
        if (PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_HP) < maxHP) {
            PlatCastle_MonSet(castle, slot, PLATCASTLE_MON_HP, maxHP);
        }
    }
    if (kind == PLATCASTLE_BUY_HEAL_PP || kind == PLATCASTLE_BUY_HEAL_ALL) {
        for (i = 0; i < 4; i++) {
            move = PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_MOVE1 + i);
            maxPP = PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_MAX_PP1 + i);
            if (move != 0 && PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_PP1 + i) < maxPP) {
                PlatCastle_MonSet(castle, slot, PLATCASTLE_MON_PP1 + i, maxPP);
            }
        }
    }
}

static u16 RankUpCost(void *records, u8 challengeType, u8 rankType) {
    u8 rank = PlatCastle_GetRank(records, challengeType, rankType);

    return rank < 3 ? sRankUpCosts[rankType][rank] : 0;
}

// IncreaseRank (both apps): the cost of the rank now spent, the rank up by one
static void IncreaseRank(void *records, u8 challengeType, u8 rankType, u16 cost) {
    u8 rank;

    PlatCastle_SpendCastlePoints(records, challengeType, cost);
    rank = PlatCastle_GetRank(records, challengeType, rankType);
    SetStat(records, PlatCastle_StatIndex(challengeType, PLATCASTLE_STAT_RANK + rankType), (u16)(rank + 1));
}

// The checks each screen makes before its yes/no (the self app's HEAL_MENU and RENTAL_MENU, the opponent app's
// MON_OPTIONS_MENU, CHANGE_LEVEL_MENU and SUMMARY_MENU states; the scene's pass). arg: a rental list's row (0xffff: the
// rental menu's BERRIES or ITEMS entry itself, which opens the list)
u32 PlatCastle_Ask(PlatCastle *castle, void *records, u32 kind, u8 slot, u16 arg, u16 *cost) {
    u8 type = castle->challengeType;
    u8 rank;

    *cost = 0;
    switch (kind) {
    case PLATCASTLE_BUY_HEAL_HP:
    case PLATCASTLE_BUY_HEAL_PP:
    case PLATCASTLE_BUY_HEAL_ALL:
        rank = PlatCastle_GetRank(records, type, PLATCASTLE_RANK_HEALING);
        if (rank < sHealRanks[kind - PLATCASTLE_BUY_HEAL_HP]) {
            return PLATCASTLE_RESULT_RANK_TOO_LOW;
        }
        *cost = sHealingCosts[kind - PLATCASTLE_BUY_HEAL_HP];
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_RANK_HEALING:
    case PLATCASTLE_BUY_RANK_RENTALS:
        rank = PlatCastle_GetRank(records, type, kind == PLATCASTLE_BUY_RANK_HEALING ? PLATCASTLE_RANK_HEALING :
                                                                                       PLATCASTLE_RANK_RENTALS);
        if (rank == 3) {
            return PLATCASTLE_RESULT_MAX_RANK;
        }
        *cost = RankUpCost(records, type, kind == PLATCASTLE_BUY_RANK_HEALING ? PLATCASTLE_RANK_HEALING :
                                                                                 PLATCASTLE_RANK_RENTALS);
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_ITEM:
        if (PlatCastle_GetRank(records, type, PLATCASTLE_RANK_RENTALS) == 1) {
            return PLATCASTLE_RESULT_RANK_TOO_LOW;
        }
        // fall through
    case PLATCASTLE_BUY_BERRY:
        if (arg == 0xffff) {
            return PLATCASTLE_RESULT_DONE;
        }
        *cost = PlatCastle_RentalPrice(kind == PLATCASTLE_BUY_ITEM, arg);
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_IDENTIFY:
        if (castle->appIdentityUnlocked[slot]) {
            return PLATCASTLE_RESULT_KNOWN;
        }
        *cost = CP_COST_CHECK_IDENTITY;
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_LEVEL_UP:
        if (castle->levelAdjustments[slot] == PLATCASTLE_LEVEL_UP_5) {
            return PLATCASTLE_RESULT_CANT_GO_HIGHER;
        }
        *cost = CP_COST_LEVEL_UP;
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_LEVEL_DOWN:
        if (castle->levelAdjustments[slot] == PLATCASTLE_LEVEL_DOWN_5) {
            return PLATCASTLE_RESULT_CANT_GO_LOWER;
        }
        *cost = CP_COST_LEVEL_DOWN;
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_STATS:
        if (castle->appStatsUnlocked[slot]) {
            return PLATCASTLE_RESULT_KNOWN;
        }
        *cost = CP_COST_SHOW_STATS;
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_MOVES:
        if (PlatCastle_GetRank(records, type, PLATCASTLE_RANK_INFO) == 1) {
            return PLATCASTLE_RESULT_RANK_TOO_LOW;
        }
        if (castle->appMovesUnlocked[slot]) {
            return PLATCASTLE_RESULT_KNOWN;
        }
        *cost = CP_COST_SHOW_MOVES;
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_RANK_INFO:
        if (PlatCastle_GetRank(records, type, PLATCASTLE_RANK_INFO) == 2) {
            return PLATCASTLE_RESULT_MAX_RANK;
        }
        *cost = CP_COST_RANK_UP;
        return PLATCASTLE_RESULT_CONFIRM;
    case PLATCASTLE_BUY_PASS:
        *cost = CP_COST_PASS;
        return PLATCASTLE_RESULT_CONFIRM;
    }
    return PLATCASTLE_RESULT_DONE;
}

// What each screen does after the yes (the self app's HEAL_YES_NO, RANK_UP_*_YES_NO, SELECT_ITEM_OR_BERRY_YES_NO and
// SWITCH_ITEMS_YES_NO states; the opponent app's REVEAL_MON_SLOT_YES_NO, CHANGE_LEVEL_YES_NO, UNLOCK_MONS_*_YES_NO,
// RANK_UP_SUMMARY_YES_NO; the scene's pass): its checks, then the CP spent and the purchase made
u32 PlatCastle_Buy(PlatCastle *castle, void *records, u32 kind, u8 slot, u16 arg) {
    u8 type = castle->challengeType;
    u16 currentCP = PlatCastle_GetCurrentCP(records, type);
    u16 cost, row = arg & 0xff;
    u8 rank;
    BOOL items;

    switch (kind) {
    case PLATCASTLE_BUY_HEAL_HP:
    case PLATCASTLE_BUY_HEAL_PP:
    case PLATCASTLE_BUY_HEAL_ALL:
        rank = PlatCastle_GetRank(records, type, PLATCASTLE_RANK_HEALING);
        if (rank < sHealRanks[kind - PLATCASTLE_BUY_HEAL_HP]) {
            return PLATCASTLE_RESULT_RANK_TOO_LOW;
        }
        cost = sHealingCosts[kind - PLATCASTLE_BUY_HEAL_HP];
        if (currentCP < cost) {
            return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
        }
        if (kind == PLATCASTLE_BUY_HEAL_HP) {
            if (PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_HP) == PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_MAX_HP)) {
                return PLATCASTLE_RESULT_NO_BENEFIT;
            }
        } else if (kind == PLATCASTLE_BUY_HEAL_PP) {
            if (!IsMonMissingPP(castle, slot)) {
                return PLATCASTLE_RESULT_NO_BENEFIT;
            }
        } else if (PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_HP) == PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_MAX_HP) &&
                   !IsMonMissingPP(castle, slot)) {
            return PLATCASTLE_RESULT_NO_BENEFIT;
        }
        PlatCastle_SpendCastlePoints(records, type, cost);
        HealPokemon(castle, slot, kind);
        return PLATCASTLE_RESULT_DONE;
    case PLATCASTLE_BUY_RANK_HEALING:
    case PLATCASTLE_BUY_RANK_RENTALS:
        cost = RankUpCost(records, type, kind == PLATCASTLE_BUY_RANK_HEALING ? PLATCASTLE_RANK_HEALING : PLATCASTLE_RANK_RENTALS);
        if (currentCP < cost) {
            return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
        }
        IncreaseRank(records, type, kind == PLATCASTLE_BUY_RANK_HEALING ? PLATCASTLE_RANK_HEALING : PLATCASTLE_RANK_RENTALS,
                     cost);
        return PLATCASTLE_RESULT_DONE;
    case PLATCASTLE_BUY_BERRY:
    case PLATCASTLE_BUY_ITEM:
        items = kind == PLATCASTLE_BUY_ITEM;
        cost = PlatCastle_RentalPrice(items, row);
        if (!(arg & PLATCASTLE_BUY_SWITCH)) {
            if (currentCP < cost) {
                return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
            }
            if (PlatCastle_MonGet(castle, slot, PLATCASTLE_MON_ITEM) != ITEM_NONE) {
                return PLATCASTLE_RESULT_HOLDING_ITEM;
            }
        }
        PlatCastle_SpendCastlePoints(records, type, cost);
        PlatCastle_MonSet(castle, slot, PLATCASTLE_MON_ITEM, PlatCastle_RentalItem(items, row));      // RentItem
        return PLATCASTLE_RESULT_DONE;
    case PLATCASTLE_BUY_IDENTIFY:
        if (currentCP < CP_COST_CHECK_IDENTITY) {
            return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
        }
        PlatCastle_SpendCastlePoints(records, type, CP_COST_CHECK_IDENTITY);
        castle->appIdentityUnlocked[slot] = TRUE;       // RevealPokemonInSlot
        return PLATCASTLE_RESULT_DONE;
    case PLATCASTLE_BUY_LEVEL_UP:
    case PLATCASTLE_BUY_LEVEL_DOWN:
        cost = kind == PLATCASTLE_BUY_LEVEL_UP ? CP_COST_LEVEL_UP : CP_COST_LEVEL_DOWN;
        if (currentCP < cost) {
            return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
        }
        PlatCastle_SpendCastlePoints(records, type, cost);
        // UpdateLevelAdjustment: from Level 50 up or down; back to 50 from the other way
        if (castle->levelAdjustments[slot] == PLATCASTLE_LEVEL_NONE) {
            castle->levelAdjustments[slot] = kind == PLATCASTLE_BUY_LEVEL_UP ? PLATCASTLE_LEVEL_UP_5 : PLATCASTLE_LEVEL_DOWN_5;
        } else {
            castle->levelAdjustments[slot] = PLATCASTLE_LEVEL_NONE;
        }
        return PLATCASTLE_RESULT_DONE;
    case PLATCASTLE_BUY_STATS:
    case PLATCASTLE_BUY_MOVES:
        cost = kind == PLATCASTLE_BUY_STATS ? CP_COST_SHOW_STATS : CP_COST_SHOW_MOVES;
        if (currentCP < cost) {                         // TryToBuySummaryScreen
            return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
        }
        PlatCastle_SpendCastlePoints(records, type, cost);
        if (kind == PLATCASTLE_BUY_STATS) {
            castle->appStatsUnlocked[slot] = TRUE;
        } else {
            castle->appMovesUnlocked[slot] = TRUE;
        }
        return PLATCASTLE_RESULT_DONE;
    case PLATCASTLE_BUY_RANK_INFO:
        if (currentCP < CP_COST_RANK_UP) {
            return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
        }
        PlatCastle_SpendCastlePoints(records, type, CP_COST_RANK_UP);
        rank = PlatCastle_GetRank(records, type, PLATCASTLE_RANK_INFO);
        SetStat(records, PlatCastle_StatIndex(type, PLATCASTLE_STAT_RANK + PLATCASTLE_RANK_INFO), (u16)(rank + 1));
        return PLATCASTLE_RESULT_DONE;
    case PLATCASTLE_BUY_PASS:
        if (currentCP < CP_COST_PASS) {                 // GetCurrentCastlePoints, GoToIfLt 50
            return PLATCASTLE_RESULT_NOT_ENOUGH_CP;
        }
        PlatCastle_SpendCastlePoints(records, type, CP_COST_PASS);
        return PLATCASTLE_RESULT_DONE;
    }
    return PLATCASTLE_RESULT_DONE;
}

#endif
