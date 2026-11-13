#include "pearlb2.h"
#include "types.h"
#include "pearlb2/plat_arcade.h"

// Platinum's Battle Arcade rules (include/pearlb2/plat_arcade.h; PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Arcade"),
// written from pokeplatinum, step for step, with the same random draws in the same order:
// - src/overlay104/battle_arcade.c (the challenge: Init, the round's Trainers and the board's speed, the save, the next battle,
//   the performance, the 32 effects, the BP)
// - src/overlay104/battle_arcade_helpers.c (the Trainers by round, Dahlia, the party sizes, the battle's AI and parties, the free
//   BP, the effects' kinds)
// - src/overlay104/frscrcmd_battle_arcade.c (CallBattleArcadeFunction, the board's arguments, the battle's cleanup)
// - src/battle_arcade_save.c, src/scrcmd_battle_arcade.c (the save; the lobby's streak deletion)
// - src/overlay104/frontier_opponents.c (the opponents' Pokémon from the Trainers' sets)
// - src/applications/frontier/battle_arcade/main.c: the board (its random number, its starting panel, its 16 panels by the
//   round, the battle's number and the last battle's performance, the cursor's speed and its random moves, the 30 seconds, the
//   stop)
// It needs nothing of Black 2: the parties, the sets and the records come through the calls plat_arcade.h lists, so PearlB2's
// host harness (b2tools/platinum_arcade_host) runs this file as it is beside Platinum's own C. Platinum's game-wide LCRNG
// (math_util.c) is the challenge's own here (PlatArcade.lcrng), the same generator. What differs:
// - The opponents' Pokémon are kept as made from their sets (PlatArcadeMon); Platinum makes a Pokemon of each at Level 50
//   (FrontierPokemon_InitPokemon), which draws random numbers of its own (a trainer id that isn't shiny with the personality,
//   then random IVs it overwrites). Those draws are made here too, in the same places (InitPokemonRandom).
// - A resumed challenge loads its opponents' Pokémon from the save with IVs Platinum never sets (LoadTrainersAndMonsFromSave's
//   ivs array is uninitialised); they decide only whether that Pokémon's making draws its two IV numbers, and the Pokémon are
//   made again before any battle. Here they are 0 (no draws), as the Castle's.
// - A remainder by zero is the DS's: 0 (its division routine _s32_div_f, the same bytes in Platinum and Black 2, returns the
//   dividend as the quotient and 0 as the remainder). The board divides by the count of a kind of effect, which is 0 for the
//   field's effects in rounds 1 and 5 (DSMod).
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
#define MAX_POKEMON_LEVEL 100

// Platinum's types (constants/pokemon.h) and abilities the effects name
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

// sBattleArcadeOpponentPools (battle_arcade_helpers.c)
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

// battle_arcade_helpers.c: the free BP of the board's two BP panels, by round (rounds 1-3, 4-6, 7 on)
static const u8 sBonus1BP[] = { 1, 1, 1 };
static const u8 sBonus3BP[] = { 3, 3, 3 };

// battle_arcade.c: the board's speed by round (the first row whose round the current one reaches)
static const struct {
    u8 round;
    u8 speed;
} sRouletteSpeedByRound[] = {
    { 7, 5 },
    { 4, 4 },
    { 0, 3 },
};

// battle_arcade.c: BattleArcade_GetEarnedBP's tables
static const u8 sBPPerRoundSolo[PLATARCADE_ROUNDS + 1] = { 0, 2, 2, 2, 2, 4, 4, 5, 6 };
static const u8 sBPPerRoundWifi[PLATARCADE_ROUNDS + 1] = { 0, 7, 8, 9, 10, 13, 14, 16, 17 };

// battle_arcade.c: the performance of a battle (the status conditions and fainted Pokémon at its end, its turns)
static const u8 sPerformanceByNumWithStatus[PLATARCADE_MAX_PARTY + 1] = { 8, 6, 4, 0, 0 };
static const u8 sPerformanceByNumFainted[PLATARCADE_MAX_PARTY + 1] = { 6, 4, 2, 0, 0 };
static const struct {
    u8 turns;
    u8 score;
} sPerformanceByTurnsElapsed[] = {
    { 3, 10 },
    { 5, 6 },
    { 7, 4 },
    { 9, 2 },
    { 10, 0 },
};

// battle_arcade.c: the items and Berries the board lends, by round (Platinum's item ids, which are Black 2's for these)
static const u16 sItemPoolTier1[] = {
    221 /* King's Rock */, 217 /* Quick Claw */, 213 /* BrightPowder */, 277 /* Metronome */, 296 /* Big Root */,
    230 /* Focus Band */, 275 /* Focus Sash */, 234 /* Leftovers */, 278 /* Iron Ball */, 279 /* Lagging Tail */,
    281 /* Black Sludge */,
};
static const u16 sItemPoolTier2[] = {
    214 /* White Herb */, 271 /* Power Herb */, 266 /* Muscle Band */, 267 /* Wise Glasses */, 253 /* Shell Bell */,
    232 /* Scope Lens */, 265 /* Wide Lens */, 276 /* Zoom Lens */, 268 /* Expert Belt */, 270 /* Life Orb */,
    278 /* Iron Ball */, 279 /* Lagging Tail */, 281 /* Black Sludge */,
};
static const u16 sItemPoolTier3[] = {
    230 /* Focus Band */, 275 /* Focus Sash */, 234 /* Leftovers */, 232 /* Scope Lens */, 265 /* Wide Lens */,
    276 /* Zoom Lens */, 268 /* Expert Belt */, 270 /* Life Orb */, 220 /* Choice Band */, 297 /* Choice Specs */,
    287 /* Choice Scarf */,
};
static const u16 sBerryPoolTier1[] = {
    149 /* Cheri */, 150 /* Chesto */, 151 /* Pecha */, 152 /* Rawst */, 153 /* Aspear */, 156 /* Persim */,
    158 /* Sitrus */, 157 /* Lum */,
};
static const u16 sBerryPoolTier2[] = {
    184 /* Occa */, 185 /* Passho */, 186 /* Wacan */, 187 /* Rindo */, 188 /* Yache */, 189 /* Chople */, 190 /* Kebia */,
    191 /* Shuca */, 192 /* Coba */, 193 /* Payapa */, 194 /* Tanga */, 195 /* Charti */, 196 /* Kasib */, 197 /* Haban */,
    198 /* Colbur */, 199 /* Babiri */, 200 /* Chilan */, 156 /* Persim */, 158 /* Sitrus */, 157 /* Lum */,
};
static const u16 sBerryPoolTier3[] = {
    156 /* Persim */, 158 /* Sitrus */, 157 /* Lum */, 201 /* Liechi */, 202 /* Ganlon */, 203 /* Salac */, 204 /* Petaya */,
    205 /* Apicot */, 206 /* Lansat */, 207 /* Starf */,
};

// applications/frontier/battle_arcade/main.c: the board
// The frames between two moves of the cursor, by the board's speed (sCursorMoveFrames' first column)
static const u8 sCursorMoveFrames[8] = { 20, 16, 8, 4, 3, 2, 1, 0 };

// sEffectAvailabilityByRound: bit r-1 the effect can be on the board in round r (round 7 and on: bit 6)
static const u8 sEffectAvailabilityByRound[PLATARCADE_EFFECTS] = {
    0x7e, 0x45, 0x45, 0x45, 0x70, 0x70, 0x47, 0x78, 0x7e,      // the opponent's
    0x7e, 0x45, 0x45, 0x45, 0x70, 0x70, 0x47, 0x78, 0x7e,      // the player's
    0x46, 0x46, 0x46, 0x46, 0x68, 0x68,                        // the field's
    0x7f, 0x47, 0x7f, 0x70, 0x78, 0x70, 0x7f, 0x40,            // the board's and the bonuses
};

// sEffectAvailabilityByBattle: bit b-1 the effect can be on the board for the round's battle b, for these seven
static const u8 sEffectAvailabilityByBattle[7] = { 0x3f, 0x3f, 0x3f, 0x3f, 0x15, 0x2a, 0x2a };
static const u8 sByBattleEffects[7] = {
    PLATARCADE_EFFECT_SWAP_MONS, PLATARCADE_EFFECT_SPEED_UP, PLATARCADE_EFFECT_SLOW_DOWN, PLATARCADE_EFFECT_RANDOMIZE_CURSOR,
    PLATARCADE_EFFECT_GET_1_BP, PLATARCADE_EFFECT_NO_BATTLE, PLATARCADE_EFFECT_GET_3_BP,
};

// sCategoryWeights: the four kinds' weights out of 100 (Foe, Ally, Env, Bonus), by tier; the tier from the last battle's
// performance (sCategoryTierPerformanceThresholds: the first it reaches, tier 4 below them all)
static const u8 sCategoryWeights[5][PLATARCADE_CATEGORIES] = {
    { 15, 15, 40, 30 },
    { 35, 20, 30, 15 },
    { 30, 30, 35, 5 },
    { 25, 40, 30, 5 },
    { 10, 75, 10, 5 },
};
static const u8 sCategoryTierPerformanceThresholds[] = { 21, 16, 10, 5 };

// ---------------------------------------------------------------- the random numbers
u16 PlatArcade_Random(PlatArcade *arcade) {
    arcade->lcrng = arcade->lcrng * LCRNG_MULTIPLIER + LCRNG_INCREMENT;
    return (u16)(arcade->lcrng >> 16);
}

// LCRNG_Next() | LCRNG_Next() << 16: the low half drawn first
static u32 Random32(PlatArcade *arcade) {
    u32 low = PlatArcade_Random(arcade);
    u32 high = PlatArcade_Random(arcade);

    return low | (high << 16);
}

// The DS's remainder (_s32_div_f): 0 for a divisor of 0
static int DSMod(int a, int b) {
    return b == 0 ? 0 : a % b;
}

static BOOL IsShiny(u32 otID, u32 personality) {
    return ((((otID & 0xffff0000) >> 16) ^ (otID & 0xffff) ^ ((personality & 0xffff0000) >> 16) ^ (personality & 0xffff)) <
            SHINY_ODDS);
}

// ---------------------------------------------------------------- the records (battle_frontier_save.c, battle_frontier_stats.c)
// BattleFrontierStats_GetArcadeCurrentStreakIndex (the record) and _GetArcadeLatestStreakIndex
u32 PlatArcade_StatIndex(u8 challengeType, u32 which) {
    u32 index = PLATARCADE_STAT_SINGLE;

    switch (challengeType) {
    case PLATARCADE_SINGLE:
        index = PLATARCADE_STAT_SINGLE;
        break;
    case PLATARCADE_DOUBLE:
        index = PLATARCADE_STAT_SINGLE + PLATARCADE_STAT_STRIDE;
        break;
    case PLATARCADE_MULTI:
        index = PLATARCADE_STAT_SINGLE + 2 * PLATARCADE_STAT_STRIDE;
        break;
    case PLATARCADE_MULTI_WFC:
        index = 142;                    // STAT_ARCADE_RECORD_STREAK_MULTI_WFC: a Wi-Fi stat (the core keeps none)
        break;
    }
    return index + which;
}

static u16 GetStat(void *records, u32 stat) {
    return PlatArcade_GetStat(records, stat);
}

// BattleFrontierSave_SetStat: at most 9999
static void SetStat(void *records, u32 stat, u16 value) {
    PlatArcade_SetStat(records, stat, value > PLATARCADE_STAT_MAX ? PLATARCADE_STAT_MAX : value);
}

static void SetIfBetter(void *records, u32 stat, u16 newValue) {
    u16 currentValue = GetStat(records, stat);

    if (currentValue < newValue) {
        SetStat(records, stat, newValue);
    } else if (currentValue > PLATARCADE_STAT_MAX) {
        SetStat(records, stat, PLATARCADE_STAT_MAX);
    }
}

// BattleArcadeStreakFlags_SetFlag(ARCADE_SAVE_STREAK_FLAGS)
static void SetStreakFlag(void *records, u8 challengeType, u8 value) {
    PlatArcade_SetStreakFlag(records, challengeType, value >= 1);
}

// scrcmd_battle_arcade.c BattleArcade_ClearActiveStreak
void PlatArcade_ClearActiveStreak(void *records, u8 challengeType) {
    SetStreakFlag(records, challengeType, 0);
    if (challengeType == PLATARCADE_MULTI_WFC) {
        SetStat(records, PLATARCADE_STAT_WFC_STREAK_ACTIVE, 0);
    }
    SetStat(records, PlatArcade_StatIndex(challengeType, PLATARCADE_STAT_LATEST_STREAK), 0);
}

// ---------------------------------------------------------------- battle_arcade_helpers.c
u8 PlatArcade_GetPlayerPartySize(u8 challengeType, BOOL includePartnerMons) {
    switch (challengeType) {
    case PLATARCADE_SINGLE:
    case PLATARCADE_DOUBLE:
        return PLATARCADE_PARTY_SOLO;
    case PLATARCADE_MULTI:
    case PLATARCADE_MULTI_WFC:
        return includePartnerMons == FALSE ? PLATARCADE_PARTY_MULTI : PLATARCADE_PARTY_MULTI * 2;
    }
    return PLATARCADE_PARTY_SOLO;
}

u8 PlatArcade_GetOpponentPartySize(u8 challengeType, BOOL includeBothOpponents) {
    switch (challengeType) {
    case PLATARCADE_SINGLE:
    case PLATARCADE_DOUBLE:
        return PLATARCADE_PARTY_SOLO;
    case PLATARCADE_MULTI:
    case PLATARCADE_MULTI_WFC:
        return includeBothOpponents == FALSE ? PLATARCADE_PARTY_MULTI : PLATARCADE_PARTY_MULTI * 2;
    }
    return PLATARCADE_PARTY_SOLO;
}

BOOL PlatArcade_IsMultiPlayerChallenge(u8 challengeType) {
    return challengeType == PLATARCADE_MULTI || challengeType == PLATARCADE_MULTI_WFC;
}

// BattleArcade_GetCurrentRound (the partner's round of a link Multi: closed)
u16 PlatArcade_GetCurrentRound(PlatArcade *arcade) {
    return arcade->currentRound;
}

u16 PlatArcade_GetTrainerOffset(PlatArcade *arcade, u8 trainerSlot) {
    return arcade->currentBattle + (trainerSlot * PLATARCADE_BATTLES_PER_ROUND);
}

// BattleArcade_GetOpponentTrainerID: Dahlia at the 21st and 49th battle of a Single streak (the round's 7th, and the second
// Trainer row's 7th of the round before, which a Single never fights); the round's 7th Trainers from the final range
static int GetOpponentTrainerID(PlatArcade *arcade, u8 challengeType, int currentRound, int trainerOffset) {
    int currentStreak, spread, min;

    if (challengeType == PLATARCADE_SINGLE) {
        currentStreak = (currentRound * PLATARCADE_BATTLES_PER_ROUND) + (trainerOffset + 1);
        if (currentStreak == PLATARCADE_STREAK_SILVER) {
            return PLATARCADE_DAHLIA_SILVER;
        } else if (currentStreak == PLATARCADE_STREAK_GOLD) {
            return PLATARCADE_DAHLIA_GOLD;
        }
    }
    if (currentRound >= (int)NELEMS(sOpponentPools)) {
        currentRound = NELEMS(sOpponentPools) - 1;
    }
    if (trainerOffset == PLATARCADE_BATTLES_PER_ROUND - 1 || trainerOffset == (PLATARCADE_BATTLES_PER_ROUND * 2) - 1) {
        spread = sOpponentPools[currentRound].finalMax - sOpponentPools[currentRound].finalMin;
        min = sOpponentPools[currentRound].finalMin;
    } else {
        spread = sOpponentPools[currentRound].normalMax - sOpponentPools[currentRound].normalMin;
        min = sOpponentPools[currentRound].normalMin;
    }
    return min + DSMod(PlatArcade_Random(arcade), spread);
}

// BattleArcade_PickOpponentTrainers: no Trainer twice in a round
static void PickOpponentTrainers(PlatArcade *arcade, u8 challengeType, int currentRound, u16 trainerIDs[], u8 numTrainers) {
    int i = 0, j;

    do {
        trainerIDs[i] = (u16)GetOpponentTrainerID(arcade, challengeType, currentRound, i);
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

// BattleArcade_GetAIMask: Dahlia's battles the full AI; rounds 1-2 none, 3-4 the basic one, then the full
u16 PlatArcade_GetAIMask(PlatArcade *arcade) {
    u16 round, aiMask;

    if (arcade->challengeType == PLATARCADE_SINGLE) {
        if (arcade->trainerIDs[arcade->currentBattle] == PLATARCADE_DAHLIA_SILVER ||
            arcade->trainerIDs[arcade->currentBattle] == PLATARCADE_DAHLIA_GOLD) {
            return PLATARCADE_AI_BASIC | PLATARCADE_AI_EVAL_ATTACK | PLATARCADE_AI_EXPERT;
        }
    }
    round = PlatArcade_GetCurrentRound(arcade);
    aiMask = PLATARCADE_AI_BASIC | PLATARCADE_AI_EVAL_ATTACK | PLATARCADE_AI_EXPERT;
    switch (round + 1) {
    case 1:
    case 2:
        aiMask = 0;
        break;
    case 3:
    case 4:
        aiMask = PLATARCADE_AI_BASIC;
        break;
    }
    return aiMask;
}

// BattleArcade_GetFreeBPFromEvent
u16 PlatArcade_GetFreeBPFromEvent(PlatArcade *arcade, u8 activeEffect) {
    u16 currentRound = PlatArcade_GetCurrentRound(arcade);
    const u8 *table = activeEffect == PLATARCADE_EFFECT_GET_1_BP ? sBonus1BP : sBonus3BP;

    if (currentRound < 3) {
        return table[0];
    } else if (currentRound < 6) {
        return table[1];
    }
    return table[2];
}

// BattleArcade_GetCategoryFromEffect
u8 PlatArcade_GetCategoryFromEffect(u8 effect) {
    if (effect < PLATARCADE_EFFECT_LOWER_ALLY_HP) {
        return PLATARCADE_CATEGORY_FOE;
    } else if (effect < PLATARCADE_EFFECT_SUNNY_BATTLE) {
        return PLATARCADE_CATEGORY_ALLY;
    } else if (effect < PLATARCADE_EFFECT_SWAP_MONS) {
        return PLATARCADE_CATEGORY_ENV;
    }
    return PLATARCADE_CATEGORY_BONUS;
}

// ---------------------------------------------------------------- the opponents' Pokémon (frontier_opponents.c)
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
static u32 Mon_Init(PlatArcade *arcade, PlatArcadeMon *mon, u16 setID, u32 otID, u32 personality, u8 ivs) {
    PlatArcadeSet set;
    u8 friendship = MAX_FRIENDSHIP_VALUE;
    u16 ability2;
    int i, evs;

    PlatArcade_ReadSet(setID, &set);
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
            personality = Random32(arcade);
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
    ability2 = PlatArcade_SpeciesAbility(mon->species, 1);
    if (ability2 != 0 && (mon->personality & 1)) {
        mon->ability = (u8)ability2;
    } else {
        mon->ability = (u8)PlatArcade_SpeciesAbility(mon->species, 0);
    }
    mon->friendship = friendship;
    return personality;
}

// BattleFrontier_LoadOpponentMonData: a trainer id first, then the Pokémon
static u32 LoadOpponentMonData(PlatArcade *arcade, PlatArcadeMon *mon, u16 setID, u8 ivs, u32 personality) {
    u32 otID = Random32(arcade);

    return Mon_Init(arcade, mon, setID, otID, personality, ivs);
}

// BattleFrontier_LoadFrontierPokemon
static void LoadFrontierPokemon(PlatArcade *arcade, PlatArcadeMon *mons, const u16 *setIDs, const u8 *ivList,
                                const u32 *personalities, u32 *resultPersonalities, int numMons) {
    int i;
    u32 personality;

    for (i = 0; i < numMons; i++) {
        personality = LoadOpponentMonData(arcade, &mons[i], setIDs[i], ivList == NULL ? 0 : ivList[i],
                                          personalities == NULL ? 0 : personalities[i]);
        if (resultPersonalities != NULL) {
            resultPersonalities[i] = personality;
        }
    }
}

// The random numbers of FrontierPokemon_InitPokemon (Pokemon_InitWith with the personality and OTID_NOT_SHINY: a trainer id
// that isn't shiny with it; the IVs as one number, which, 32 or more, makes it draw random IVs before it sets them)
static void InitPokemonRandom(PlatArcade *arcade, u32 personality, u8 ivs) {
    u32 otID, combined;

    do {
        otID = Random32(arcade);
    } while (IsShiny(otID, personality));
    combined = (u32)ivs * (1 | (1 << 5) | (1 << 10) | (1 << 15) | (1 << 20) | (1 << 25));
    if ((combined & 0x3fffffff) >= INIT_IVS_RANDOM) {
        PlatArcade_Random(arcade);
        PlatArcade_Random(arcade);
    }
}

// FrontierPokemon_InitPokemon at the Arcade's level, then BattleArcade_AddMonToParty (Pokemon_UpdateAfterCatch: the met
// data, no random number)
static void AddOpponent(PlatArcade *arcade, const PlatArcadeMon *mon, u8 level) {
    InitPokemonRandom(arcade, mon->personality, mon->ivs);
    PlatArcade_OpponentAdd(arcade, mon, level);
    arcade->opponentCount++;
}

// SelectPokemonForTrainer: sets of the Trainer's list, no species or item twice (nor the partner's, for 50 tries)
static BOOL SelectPokemonForTrainer(PlatArcade *arcade, u16 trainerID, const u16 partnersSpecies[],
                                    const u16 partnersItems[], int partnersNumMons, int numMons, u16 selectedMons[]) {
    PlatArcadeSet newMon[PLATARCADE_MAX_PARTY];
    u16 sets[128];                      // (the Frontier Trainers have 100 sets at most)
    u16 numSets = PlatArcade_TrainerSets(trainerID, sets, NELEMS(sets));
    int i = 0, j, partnerConflictCounter = 0;
    u16 narcIdx;

    if (numSets == 0) {                 // (no Trainer file: nothing to draw from)
        for (i = 0; i < numMons; i++) {
            selectedMons[i] = 0;
        }
        return FALSE;
    }
    while (i != numMons) {
        narcIdx = sets[PlatArcade_Random(arcade) % numSets];
        PlatArcade_ReadSet(narcIdx, &newMon[i]);
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
static void GetPokemonForTrainers(PlatArcade *arcade, u8 numMons, u16 trainerID, u16 trainerID2, u16 *monSetIDs,
                                  PlatArcadeMon *resultMons, u8 *ivs, u32 *personalities, u8 isMultiplayerChallenge) {
    u16 alreadySelectedSpecies[4] = { 0 };
    u16 alreadySelectedItems[4] = { 0 };
    PlatArcadeSet mon;
    int i;

    for (i = 0; i < numMons; i++) {
        ivs[i] = GetIVsForTrainer(trainerID);
    }
    if (!isMultiplayerChallenge) {
        SelectPokemonForTrainer(arcade, trainerID, alreadySelectedSpecies, alreadySelectedItems, 0, numMons, monSetIDs);
    } else {
        SelectPokemonForTrainer(arcade, trainerID, alreadySelectedSpecies, alreadySelectedItems, 0, numMons / 2, monSetIDs);
        for (i = 0; i < numMons / 2; i++) {
            PlatArcade_ReadSet(monSetIDs[i], &mon);
            alreadySelectedSpecies[i] = mon.species;
            alreadySelectedItems[i] = mon.item;
        }
        SelectPokemonForTrainer(arcade, trainerID2, alreadySelectedSpecies, alreadySelectedItems, numMons / 2, numMons / 2,
                                &monSetIDs[numMons / 2]);
        for (i = 0; i < numMons / 2; i++) {
            ivs[i + (numMons / 2)] = GetIVsForTrainer(trainerID2);
        }
    }
    LoadFrontierPokemon(arcade, resultMons, monSetIDs, ivs, NULL, personalities, numMons);
}

// ---------------------------------------------------------------- battle_arcade.c
static void Save_Init(PlatArcadeSave *save) {
    u8 *bytes = (u8 *)save;
    u32 i;

    for (i = 0; i < sizeof(PlatArcadeSave); i++) {
        bytes[i] = 0;
    }
}

// BattleArcade_Init. arcade->lcrng is the caller's (seeded); the parties are the game's (PlatArcade_PartyAddFieldMon)
void PlatArcade_Init(PlatArcade *arcade, PlatArcadeSave *save, void *records, u16 resuming, u8 challengeType, u8 slot1,
                     u8 slot2, u8 slot3) {
    u32 lcrng = arcade->lcrng;
    u8 *bytes = (u8 *)arcade;
    u8 streakActive, partySize, level;
    u16 i;

    for (i = 0; i < sizeof(PlatArcade); i++) {      // MI_CpuClear8
        bytes[i] = 0;
    }
    arcade->magic = PLATARCADE_WORK_MAGIC;
    arcade->lcrng = lcrng;
    arcade->activeEffect = PLATARCADE_EFFECTS;

    if (!resuming) {
        arcade->challengeType = challengeType;
        arcade->currentBattle = 0;
        arcade->rouletteSpeed = 3;
        arcade->cursorRandomized = 0;
        Save_Init(save);
        if (arcade->challengeType == PLATARCADE_MULTI_WFC) {
            streakActive = FALSE;           // SystemVars_GetWiFiFrontierCleared: the Wi-Fi Multi is closed
        } else {
            streakActive = (u8)PlatArcade_GetStreakFlag(records, arcade->challengeType);
        }
        if (streakActive == TRUE) {
            arcade->currentStreak = GetStat(records, PlatArcade_StatIndex(arcade->challengeType, PLATARCADE_STAT_LATEST_STREAK));
        } else {
            arcade->currentStreak = 0;
        }
        arcade->currentRound = arcade->currentStreak / PLATARCADE_BATTLES_PER_ROUND;
        arcade->partySlots[0] = slot1;
        arcade->partySlots[1] = slot2;
        arcade->partySlots[2] = slot3;
    } else {
        arcade->challengeType = save->challengeType;
        arcade->currentBattle = save->currentBattle;
        arcade->rouletteSpeed = save->rouletteSpeed;
        arcade->cursorRandomized = save->cursorRandomized;
        arcade->currentStreak = GetStat(records, PlatArcade_StatIndex(arcade->challengeType, PLATARCADE_STAT_LATEST_STREAK));
        arcade->currentRound = arcade->currentStreak / PLATARCADE_BATTLES_PER_ROUND;
        for (i = 0; i < PLATARCADE_PARTY_SOLO; i++) {
            arcade->partySlots[i] = save->partySlots[i];
        }
    }

    for (i = 0; i < PLATARCADE_PARTY_SOLO; i++) {
        arcade->savedHeldItems[i] = (u16)PlatArcade_FieldMonItem(arcade, arcade->partySlots[i]);
    }

    // The player's party: copies of the field Pokémon, no held item, Level 50 at most (the experience of Level 50, its stats
    // again)
    partySize = PlatArcade_GetPlayerPartySize(arcade->challengeType, FALSE);
    for (i = 0; i < partySize; i++) {
        PlatArcade_PartyAddFieldMon(arcade, arcade->partySlots[i]);
        arcade->playerCount++;
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_ITEM, ITEM_NONE);
        level = (u8)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_LEVEL);
        if (level > PLATARCADE_MAX_LEVEL) {
            PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_EXP,
                              PlatArcade_BaseExpAt((u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i,
                                                                          PLATARCADE_MON_SPECIES),
                                                   PLATARCADE_MAX_LEVEL));
            PlatArcade_MonCalcLevelAndStats(arcade, PLATARCADE_PLAYERS, (u8)i);
        }
    }
}

// SelectTrainersAndFirstBattlesMons: the round's 14 Trainers, the first opponent's three, the board's speed by round
static void SelectTrainersAndFirstBattlesMons(PlatArcade *arcade) {
    u16 currentRound;
    int i;

    PickOpponentTrainers(arcade, arcade->challengeType, PlatArcade_GetCurrentRound(arcade), arcade->trainerIDs,
                         PLATARCADE_TRAINERS);
    GetPokemonForTrainers(arcade, PlatArcade_GetOpponentPartySize(arcade->challengeType, TRUE),
                          arcade->trainerIDs[arcade->currentBattle],
                          arcade->trainerIDs[arcade->currentBattle + PLATARCADE_BATTLES_PER_ROUND], arcade->monSetIDs,
                          arcade->opponentMons, arcade->opponentMonIVs, arcade->opponentMonPersonalities,
                          (u8)PlatArcade_IsMultiPlayerChallenge(arcade->challengeType));
    currentRound = PlatArcade_GetCurrentRound(arcade);
    for (i = 0; i < (int)NELEMS(sRouletteSpeedByRound); i++) {
        if (currentRound >= sRouletteSpeedByRound[i].round) {
            arcade->rouletteSpeed = sRouletteSpeedByRound[i].speed;
            break;
        }
    }
}

// LoadPlayersPartyFromSave: the held items as saved
static void LoadPlayersPartyFromSave(PlatArcade *arcade, PlatArcadeSave *save) {
    u8 i;

    for (i = 0; i < arcade->playerCount; i++) {
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_ITEM, save->heldItems[i]);
    }
}

// LoadTrainersAndMonsFromSave: the Trainers and the saved sets; the opponent's party gets four more Pokémon of them (the
// fourth from set 0, the padding of a solo challenge); its opponentMons stay as Init left them (none)
static void LoadTrainersAndMonsFromSave(PlatArcade *arcade, PlatArcadeSave *save) {
    PlatArcadeMon mons[PLATARCADE_MAX_PARTY];
    u8 ivs[PLATARCADE_MAX_PARTY] = { 0 };      // (Platinum's are never set: see the top)
    u16 setIDs[PLATARCADE_MAX_PARTY];
    u32 personalities[PLATARCADE_MAX_PARTY];
    int i;

    LoadPlayersPartyFromSave(arcade, save);
    for (i = 0; i < PLATARCADE_TRAINERS; i++) {
        arcade->trainerIDs[i] = save->trainerIDs[i];
    }
    for (i = 0; i < PLATARCADE_MAX_PARTY; i++) {
        setIDs[i] = save->monSetIDs[i];
        arcade->monSetIDs[i] = setIDs[i];
    }
    LoadFrontierPokemon(arcade, mons, setIDs, ivs, NULL, personalities, PLATARCADE_MAX_PARTY);
    for (i = 0; i < PLATARCADE_MAX_PARTY; i++) {
        AddOpponent(arcade, &mons[i], PLATARCADE_MAX_LEVEL);
    }
}

void PlatArcade_LoadTrainersForRound(PlatArcade *arcade, PlatArcadeSave *save, u16 resuming) {
    if (!resuming) {
        SelectTrainersAndFirstBattlesMons(arcade);
    } else {
        LoadTrainersAndMonsFromSave(arcade, save);
    }
}

// BattleArcade_Save: saveType 0 a completed round, 1 a loss, 2 a rest (the record and the streak flag aren't touched)
void PlatArcade_Save(PlatArcade *arcade, PlatArcadeSave *save, void *records, u8 saveType) {
    u16 i;

    save->challengeType = arcade->challengeType;
    save->didSave = TRUE;
    save->currentBattle = arcade->currentBattle;
    save->rouletteSpeed = arcade->rouletteSpeed;
    save->cursorRandomized = arcade->cursorRandomized;
    SetStat(records, PlatArcade_StatIndex(arcade->challengeType, PLATARCADE_STAT_LATEST_STREAK), arcade->currentStreak);
    if (saveType != 2) {
        SetIfBetter(records, PlatArcade_StatIndex(arcade->challengeType, PLATARCADE_STAT_RECORD_STREAK), arcade->currentStreak);
        SetStreakFlag(records, arcade->challengeType, arcade->saveStreak);
        if (arcade->challengeType == PLATARCADE_MULTI_WFC) {
            SetStat(records, PLATARCADE_STAT_WFC_STREAK_ACTIVE, arcade->saveStreak);
        }
    }
    for (i = 0; i < PLATARCADE_TRAINERS; i++) {
        save->trainerIDs[i] = arcade->trainerIDs[i];
    }
    for (i = 0; i < PLATARCADE_PARTY_SOLO; i++) {
        save->partySlots[i] = arcade->partySlots[i];
    }
    for (i = 0; i < arcade->playerCount; i++) {
        save->heldItems[i] = (u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_ITEM);
    }
    for (i = 0; i < arcade->opponentCount && i < PLATARCADE_MAX_PARTY; i++) {
        save->monSetIDs[i] = arcade->monSetIDs[i];
    }
}

void PlatArcade_SaveOnLoss(PlatArcade *arcade, PlatArcadeSave *save, void *records) {
    PlatArcade_Save(arcade, save, records, 1);
}

void PlatArcade_SaveOnCompletingRound(PlatArcade *arcade, PlatArcadeSave *save, void *records) {
    arcade->saveStreak = TRUE;
    if (arcade->currentRound < PLATARCADE_ROUNDS) {
        arcade->currentRound++;
    }
    arcade->currentBattle = 0;
    PlatArcade_Save(arcade, save, records, 0);
}

// BattleArcade_SetupOpponentsParty: the opponent's three made at Level 50 from opponentMons, none holding an item
void PlatArcade_SetupOpponentsParty(PlatArcade *arcade) {
    u8 partySize = PlatArcade_GetOpponentPartySize(arcade->challengeType, TRUE);
    u8 i;

    PlatArcade_OpponentsClear(arcade);
    arcade->opponentCount = 0;
    for (i = 0; i < partySize; i++) {
        AddOpponent(arcade, &arcade->opponentMons[i], PLATARCADE_MAX_LEVEL);
        PlatArcade_MonSet(arcade, PLATARCADE_OPPONENTS, i, PLATARCADE_MON_ITEM, ITEM_NONE);
    }
}

void PlatArcade_SetupFirstOpponentsParty(PlatArcade *arcade) {
    PlatArcade_SetupOpponentsParty(arcade);
}

void PlatArcade_SetupNextOpponentsParty(PlatArcade *arcade) {
    GetPokemonForTrainers(arcade, PlatArcade_GetOpponentPartySize(arcade->challengeType, TRUE),
                          arcade->trainerIDs[arcade->currentBattle],
                          arcade->trainerIDs[arcade->currentBattle + PLATARCADE_BATTLES_PER_ROUND], arcade->monSetIDs,
                          arcade->opponentMons, arcade->opponentMonIVs, arcade->opponentMonPersonalities,
                          (u8)PlatArcade_IsMultiPlayerChallenge(arcade->challengeType));
    PlatArcade_SetupOpponentsParty(arcade);
}

// BA_FUNC_CREATE_OPPONENT_MONS (the link Multi's)
void PlatArcade_CreateOpponentMons(PlatArcade *arcade) {
    LoadFrontierPokemon(arcade, arcade->opponentMons, arcade->monSetIDs, arcade->opponentMonIVs,
                        arcade->opponentMonPersonalities, NULL, 4);
}

// CalcBasePerformance and BattleArcade_GetPerformance: of the player's side of the battle as it left it
static int GetPerformance(PlatArcade *arcade, u32 turns) {
    u8 partySize = PlatArcade_GetPlayerPartySize(arcade->challengeType, FALSE);
    u8 faintedMons = 0, monsWithStatusCondition = 0;
    int performance = 0, i;

    for (i = 0; i < partySize; i++) {
        if (PlatArcade_MonGet(arcade, PLATARCADE_BATTLE_PLAYER, (u8)i, PLATARCADE_MON_EXISTS) == 0) {
            continue;
        }
        if (PlatArcade_MonGet(arcade, PLATARCADE_BATTLE_PLAYER, (u8)i, PLATARCADE_MON_HP) == 0) {
            faintedMons++;
        }
        if (PlatArcade_MonGet(arcade, PLATARCADE_BATTLE_PLAYER, (u8)i, PLATARCADE_MON_STATUS) != 0) {
            monsWithStatusCondition++;
        }
    }
    // (the partner's party of a link Multi: closed)
    performance += sPerformanceByNumWithStatus[monsWithStatusCondition];
    performance += sPerformanceByNumFainted[faintedMons];
    for (i = 0; i < (int)NELEMS(sPerformanceByTurnsElapsed); i++) {
        if ((int)turns < sPerformanceByTurnsElapsed[i].turns) {
            performance += sPerformanceByTurnsElapsed[i].score;
            break;
        }
    }
    return performance;
}

// ---------------------------------------------------------------- the 32 effects (BattleArcade_ApplyEffect)
static u32 Get(PlatArcade *arcade, u32 side, int slot, u32 field) {
    return PlatArcade_MonGet(arcade, side, (u8)slot, field);
}

// ArcadeEffect_LowerHP: maxHP * 1.2 (a double), less maxHP, from maxHP: 2 * maxHP - floor(1.2 * maxHP). The double's floor
// is maxHP * 6 / 5 for every maxHP below 2^32 / 6 (1.2 as a double is below 6/5 by less than half the product's last unit;
// the harness checks the two for maxHP 0-65535)
static void Effect_LowerHP(PlatArcade *arcade, u32 side, u8 partySize) {
    u32 maxHP, hp;
    int i;

    for (i = 0; i < partySize; i++) {
        maxHP = Get(arcade, side, i, PLATARCADE_MON_MAX_HP);
        hp = maxHP * 6 / 5;
        hp -= maxHP;
        hp = maxHP - hp;
        PlatArcade_MonSet(arcade, side, (u8)i, PLATARCADE_MON_HP, hp);
    }
}

// ArcadeEffect_Poison, _Paralyze, _Burn: every Pokémon that can be; immune if none
static void Effect_Status(PlatArcade *arcade, u32 side, u8 partySize, u8 typeA, u8 typeB, u8 ability, u32 status) {
    int numImmune = 0, i;
    u32 type1, type2, monAbility;

    for (i = 0; i < partySize; i++) {
        type1 = Get(arcade, side, i, PLATARCADE_MON_TYPE_1);
        type2 = Get(arcade, side, i, PLATARCADE_MON_TYPE_2);
        monAbility = Get(arcade, side, i, PLATARCADE_MON_ABILITY);
        if (type1 == typeA || type2 == typeA || type1 == typeB || type2 == typeB || monAbility == ability) {
            numImmune++;
        } else {
            PlatArcade_MonSet(arcade, side, (u8)i, PLATARCADE_MON_STATUS, status);
        }
    }
    if (numImmune >= partySize) {
        arcade->immuneToEffect = TRUE;
    }
}

// ArcadeEffect_Sleep: one Pokémon, from the board's random number's slot on, the first without Insomnia or Vital Spirit;
// 2-5 turns
static void Effect_Sleep(PlatArcade *arcade, u32 side, u8 partySize) {
    int numImmune = 0, i;
    u8 slot = (u8)(arcade->randomIndex % partySize);
    u32 ability;

    for (i = 0; i < partySize; i++) {
        ability = Get(arcade, side, slot, PLATARCADE_MON_ABILITY);
        if (ability == ABILITY_INSOMNIA || ability == ABILITY_VITAL_SPIRIT) {
            numImmune++;
            slot++;
            if (slot >= partySize) {
                slot = 0;
            }
        } else {
            PlatArcade_MonSet(arcade, side, slot, PLATARCADE_MON_STATUS, PlatArcade_Random(arcade) % 4 + 2);
            break;
        }
    }
    if (numImmune >= partySize) {
        arcade->immuneToEffect = TRUE;
    }
}

// ArcadeEffect_Freeze: one Pokémon, from the board's random number's slot on, the first not Ice-type nor with Magma Armor
static void Effect_Freeze(PlatArcade *arcade, u32 side, u8 partySize) {
    int numImmune = 0, i;
    u8 slot = (u8)(arcade->randomIndex % partySize);
    u32 type1, type2, ability;

    for (i = 0; i < partySize; i++) {
        type1 = Get(arcade, side, slot, PLATARCADE_MON_TYPE_1);
        type2 = Get(arcade, side, slot, PLATARCADE_MON_TYPE_2);
        ability = Get(arcade, side, slot, PLATARCADE_MON_ABILITY);
        if (type1 == TYPE_ICE || type2 == TYPE_ICE || ability == ABILITY_MAGMA_ARMOR) {
            numImmune++;
            slot++;
            if (slot >= partySize) {
                slot = 0;
            }
        } else {
            PlatArcade_MonSet(arcade, side, slot, PLATARCADE_MON_STATUS, PLATARCADE_STATUS_FREEZE);
            break;
        }
    }
    if (numImmune >= partySize) {
        arcade->immuneToEffect = TRUE;
    }
}

// ArcadeEffect_GetBerry and _GetItem: the pool's row of the board's random number, to every Pokémon of the side
static void Effect_GetItem(PlatArcade *arcade, u32 side, u8 partySize, BOOL berry) {
    u16 currentRound = PlatArcade_GetCurrentRound(arcade);
    const u16 *itemPool;
    int poolSize, i;
    u16 newItem;

    if (currentRound < 3) {
        itemPool = berry ? sBerryPoolTier1 : sItemPoolTier1;
        poolSize = berry ? NELEMS(sBerryPoolTier1) : NELEMS(sItemPoolTier1);
    } else if (currentRound < 6) {
        itemPool = berry ? sBerryPoolTier2 : sItemPoolTier2;
        poolSize = berry ? NELEMS(sBerryPoolTier2) : NELEMS(sItemPoolTier2);
    } else {
        itemPool = berry ? sBerryPoolTier3 : sItemPoolTier3;
        poolSize = berry ? NELEMS(sBerryPoolTier3) : NELEMS(sItemPoolTier3);
    }
    newItem = itemPool[arcade->randomIndex % poolSize];
    for (i = 0; i < partySize; i++) {
        PlatArcade_MonSet(arcade, side, (u8)i, PLATARCADE_MON_ITEM, newItem);
    }
}

// ArcadeEffect_LevelUp: three levels (the experience of the level, its stats again)
static void Effect_LevelUp(PlatArcade *arcade, u32 side, u8 partySize) {
    u32 level;
    int i;

    for (i = 0; i < partySize; i++) {
        level = Get(arcade, side, i, PLATARCADE_MON_LEVEL);
        level += 3;
        if (level > MAX_POKEMON_LEVEL) {
            level = MAX_POKEMON_LEVEL;
        }
        PlatArcade_MonSet(arcade, side, (u8)i, PLATARCADE_MON_EXP,
                          PlatArcade_BaseExpAt((u16)Get(arcade, side, i, PLATARCADE_MON_SPECIES), (u8)level));
        PlatArcade_MonCalcLevelAndStats(arcade, side, (u8)i);
    }
}

void PlatArcade_ApplyEffect(PlatArcade *arcade, u8 effect) {
    u32 side;
    u8 partySize;

    if (effect < PLATARCADE_EFFECT_LOWER_ALLY_HP) {
        side = PLATARCADE_OPPONENTS;
        partySize = PlatArcade_GetOpponentPartySize(arcade->challengeType, TRUE);
    } else {
        side = PLATARCADE_PLAYERS;
        partySize = PlatArcade_GetPlayerPartySize(arcade->challengeType, TRUE);
    }
    switch (effect) {
    case PLATARCADE_EFFECT_LOWER_FOE_HP:
    case PLATARCADE_EFFECT_LOWER_ALLY_HP:
        Effect_LowerHP(arcade, side, partySize);
        break;
    case PLATARCADE_EFFECT_POISON_FOE:
    case PLATARCADE_EFFECT_POISON_ALLY:
        Effect_Status(arcade, side, partySize, TYPE_POISON, TYPE_STEEL, ABILITY_IMMUNITY, PLATARCADE_STATUS_POISON);
        break;
    case PLATARCADE_EFFECT_PARALYZE_FOE:
    case PLATARCADE_EFFECT_PARALYZE_ALLY:
        Effect_Status(arcade, side, partySize, TYPE_GROUND, TYPE_GROUND, ABILITY_LIMBER, PLATARCADE_STATUS_PARALYSIS);
        break;
    case PLATARCADE_EFFECT_BURN_FOE:
    case PLATARCADE_EFFECT_BURN_ALLY:
        Effect_Status(arcade, side, partySize, TYPE_FIRE, TYPE_FIRE, ABILITY_WATER_VEIL, PLATARCADE_STATUS_BURN);
        break;
    case PLATARCADE_EFFECT_SLEEP_FOE:
    case PLATARCADE_EFFECT_SLEEP_ALLY:
        Effect_Sleep(arcade, side, partySize);
        break;
    case PLATARCADE_EFFECT_FREEZE_FOE:
    case PLATARCADE_EFFECT_FREEZE_ALLY:
        Effect_Freeze(arcade, side, partySize);
        break;
    case PLATARCADE_EFFECT_FOE_GET_BERRY:
    case PLATARCADE_EFFECT_ALLY_GET_BERRY:
        Effect_GetItem(arcade, side, partySize, TRUE);
        break;
    case PLATARCADE_EFFECT_FOE_GET_ITEM:
    case PLATARCADE_EFFECT_ALLY_GET_ITEM:
        Effect_GetItem(arcade, side, partySize, FALSE);
        break;
    case PLATARCADE_EFFECT_FOE_LEVEL_UP:
    case PLATARCADE_EFFECT_ALLY_LEVEL_UP:
        Effect_LevelUp(arcade, side, partySize);
        break;
    case PLATARCADE_EFFECT_SUNNY_BATTLE:
        arcade->weather = PLATARCADE_WEATHER_HARSH_SUN;
        break;
    case PLATARCADE_EFFECT_RAINY_BATTLE:
        arcade->weather = PLATARCADE_WEATHER_RAINING;
        break;
    case PLATARCADE_EFFECT_SANDY_BATTLE:
        arcade->weather = PLATARCADE_WEATHER_SANDSTORM;
        break;
    case PLATARCADE_EFFECT_HAIL_BATTLE:
        arcade->weather = PLATARCADE_WEATHER_SNOWING;
        break;
    case PLATARCADE_EFFECT_FOGGY_BATTLE:
        arcade->weather = PLATARCADE_WEATHER_FOG;
        break;
    case PLATARCADE_EFFECT_TRICK_ROOM:
        arcade->weather = PLATARCADE_WEATHER_TRICK_ROOM;
        break;
    case PLATARCADE_EFFECT_SPEED_UP:
        if (arcade->rouletteSpeed < 7) {
            arcade->rouletteSpeed++;
        }
        break;
    case PLATARCADE_EFFECT_SLOW_DOWN:
        if (arcade->rouletteSpeed > 0) {
            arcade->rouletteSpeed--;
        }
        break;
    case PLATARCADE_EFFECT_RANDOMIZE_CURSOR:
        arcade->cursorRandomized = TRUE;
        break;
    default:                            // the swap, the BP, no battle, no event: the scene and the battle do them
        break;
    }
}

// BattleArcade_GetEarnedBP: by round (the 8th and on: the last row); Dahlia's two battles 20
u16 PlatArcade_GetEarnedBP(PlatArcade *arcade) {
    u16 currentRound = arcade->currentRound;
    u8 bp;

    if (arcade->challengeType == PLATARCADE_SINGLE || arcade->challengeType == PLATARCADE_DOUBLE) {
        bp = currentRound >= PLATARCADE_ROUNDS ? sBPPerRoundSolo[PLATARCADE_ROUNDS] : sBPPerRoundSolo[currentRound];
    } else {
        bp = currentRound >= PLATARCADE_ROUNDS ? sBPPerRoundWifi[PLATARCADE_ROUNDS] : sBPPerRoundWifi[currentRound];
    }
    if (arcade->challengeType == PLATARCADE_SINGLE) {
        if (arcade->currentStreak == PLATARCADE_STREAK_SILVER || arcade->currentStreak == PLATARCADE_STREAK_GOLD) {
            bp = 20;
        }
    }
    return bp;
}

// ---------------------------------------------------------------- the battle
// BattleArcade_SetupBattle's rules: the swap's parties, the AI; both parties healed once the game copied them into the battle
u16 PlatArcade_SetupBattle(PlatArcade *arcade, BOOL *swapped) {
    *swapped = arcade->activeEffect == PLATARCADE_EFFECT_SWAP_MONS;
    PlatArcade_PartyHeal(arcade, PLATARCADE_PLAYERS);
    PlatArcade_PartyHeal(arcade, PLATARCADE_OPPONENTS);
    return PlatArcade_GetAIMask(arcade);
}

// BattleArcade_SaveItemsAfterBattle
static void SaveItemsAfterBattle(PlatArcade *arcade, u32 battleSide, int battleSlot, int arcadeSlot) {
    PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, (u8)arcadeSlot, PLATARCADE_MON_ITEM,
                      (u16)PlatArcade_MonGet(arcade, battleSide, (u8)battleSlot, PLATARCADE_MON_ITEM));
}

// FrontierScrCmd_BattleArcade_CleanupBattle
void PlatArcade_CleanupBattle(PlatArcade *arcade, u32 turns, BOOL won) {
    u32 side = arcade->activeEffect == PLATARCADE_EFFECT_SWAP_MONS ? PLATARCADE_BATTLE_ENEMY : PLATARCADE_BATTLE_PLAYER;
    u32 level;
    u8 numMons, i;

    arcade->performance = (u8)GetPerformance(arcade, turns);
    arcade->wonBattle = won;
    SaveItemsAfterBattle(arcade, side, 0, 0);
    SaveItemsAfterBattle(arcade, side, 1, 1);
    SaveItemsAfterBattle(arcade, side, 2, 2);  // (a link Multi's: the partner's two; closed)
    if (arcade->activeEffect == PLATARCADE_EFFECT_ALLY_LEVEL_UP) {
        numMons = PlatArcade_GetPlayerPartySize(arcade->challengeType, PLATARCADE_DOUBLE);
        for (i = 0; i < numMons; i++) {
            level = PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_LEVEL);
            level -= 3;
            PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_EXP,
                              PlatArcade_BaseExpAt((u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_SPECIES),
                                                   (u8)level));
            PlatArcade_MonCalcLevelAndStats(arcade, PLATARCADE_PLAYERS, i);
        }
    }
    for (i = 0; i < arcade->playerCount; i++) {
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_MAX_HP, arcade->monHP[i]);
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_HP, arcade->monHP[i]);
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_ATK, arcade->monAtk[i]);
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_DEF, arcade->monDef[i]);
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_SPEED, arcade->monSpeed[i]);
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_SP_ATK, arcade->monSpAtk[i]);
        PlatArcade_MonSet(arcade, PLATARCADE_PLAYERS, i, PLATARCADE_MON_SP_DEF, arcade->monSpDef[i]);
    }
}

// ---------------------------------------------------------------- CallBattleArcadeFunction (frscrcmd_battle_arcade.c)
// The functions that only compute or change the challenge's state. FALSE: one that draws, runs a screen or is the game's
BOOL PlatArcade_Function(PlatArcade *arcade, PlatArcadeSave *save, void *records, u8 fn, u8 arg1, u8 arg2, u16 *result) {
    u8 type;

    (void)arg2;
    switch (fn) {
    case PLATARCADE_FN_SET_CHALLENGE_TYPE:
        arcade->challengeType = arg1;
        break;
    case PLATARCADE_FN_GET_APP_CURSOR_POS:
        *result = arcade->appCursorPos;
        break;
    case PLATARCADE_FN_GET_CURRENT_STREAK:
        *result = arcade->currentStreak;
        break;
    case PLATARCADE_FN_INCREMENT_CURRENT_STREAK:
        if (arcade->currentStreak < PLATARCADE_STAT_MAX) {
            arcade->currentStreak++;
        }
        break;
    case PLATARCADE_FN_HAS_SAVED:
        *result = save->didSave;
        break;
    case PLATARCADE_FN_QUICKSAVE:
        PlatArcade_Save(arcade, save, records, 2);
        break;
    case PLATARCADE_FN_GET_FREE_BP:
        *result = PlatArcade_GetFreeBPFromEvent(arcade, arcade->activeEffect);
        break;
    case PLATARCADE_FN_INCREMENT_CURRENT_BATTLE:
        *result = ++arcade->currentBattle;
        break;
    case PLATARCADE_FN_GET_HELD_ITEM:
        *result = (u16)PlatArcade_MonGet(arcade, arg1 == 0 ? PLATARCADE_PLAYERS : PLATARCADE_OPPONENTS, 0, PLATARCADE_MON_ITEM);
        break;
    case PLATARCADE_FN_GET_ACTIVE_EFFECT:
        *result = arcade->activeEffect;
        break;
    case PLATARCADE_FN_GET_CURRENT_ROUND:
        *result = PlatArcade_GetCurrentRound(arcade);
        break;
    case PLATARCADE_FN_SAVE_ON_LOSS:
        PlatArcade_SaveOnLoss(arcade, save, records);
        break;
    case PLATARCADE_FN_SAVE_ON_COMPLETING_ROUND:
        PlatArcade_SaveOnCompletingRound(arcade, save, records);
        break;
    case PLATARCADE_FN_GET_CURRENT_BATTLE:
        *result = arcade->currentBattle;
        break;
    case PLATARCADE_FN_UNK_24:
        *result = arcade->unk_A74;
        break;
    case PLATARCADE_FN_IS_MULTIPLAYER_CHALLENGE:
        *result = (u16)PlatArcade_IsMultiPlayerChallenge(arcade->challengeType);
        break;
    case PLATARCADE_FN_GET_CHALLENGE_TYPE:
        *result = arcade->challengeType;
        break;
    case PLATARCADE_FN_GET_EARNED_BP:
        *result = PlatArcade_GetEarnedBP(arcade);
        break;
    case PLATARCADE_FN_CHECK_IMMUNE_TO_EFFECT:
        *result = arcade->immuneToEffect;
        break;
    case PLATARCADE_FN_GET_NEXT_BATTLE_TYPE:
        *result = PLATARCADE_NEXT_NORMAL;
        if (arcade->challengeType == PLATARCADE_SINGLE) {
            if (arcade->currentStreak + 1 == PLATARCADE_STREAK_SILVER) {
                *result = PLATARCADE_NEXT_SILVER;
            } else if (arcade->currentStreak + 1 == PLATARCADE_STREAK_GOLD) {
                *result = PLATARCADE_NEXT_GOLD;
            }
        }
        break;
    case PLATARCADE_FN_CREATE_OPPONENT_MONS:
        PlatArcade_CreateOpponentMons(arcade);
        break;
    case PLATARCADE_FN_SETUP_OPPONENTS_PARTY:
        PlatArcade_SetupOpponentsParty(arcade);
        break;
    case PLATARCADE_FN_CHECK_SEEN_STAR_INTRO:
        *result = arcade->seenArcadeStarIntro;
        arcade->seenArcadeStarIntro = TRUE;
        break;
    case PLATARCADE_FN_CLEAR_MSGS_RECEIVED:   // (the link's)
        break;
    default:
        type = 0;
        (void)type;
        return FALSE;
    }
    return TRUE;
}

// ---------------------------------------------------------------- the board (applications/frontier/battle_arcade/main.c)
u8 PlatArcade_CursorMoveFrames(u8 rouletteSpeed) {
    return sCursorMoveFrames[rouletteSpeed < NELEMS(sCursorMoveFrames) ? rouletteSpeed : NELEMS(sCursorMoveFrames) - 1];
}

// GetAvailableEffects: the round's effects; seven of them also by the round's battle (the streak's battle number % 7, the 9999th
// and on as the 7th)
static void GetAvailableEffects(PlatArcadeRoulette *roulette) {
    u16 battleNum, normalizedBattleNum;
    u8 effect, isAvailable, column, k;

    for (effect = 0; effect < PLATARCADE_EFFECTS; effect++) {
        column = roulette->round < 6 ? (u8)roulette->round : 6;
        isAvailable = (sEffectAvailabilityByRound[effect] >> column) & 1;
        if (isAvailable == TRUE) {
            battleNum = roulette->battleStreak;        // GetBattleNumber (the partner's of a link Multi: closed)
            normalizedBattleNum = battleNum % PLATARCADE_BATTLES_PER_ROUND;
            if (battleNum >= 9999) {
                normalizedBattleNum = 6;
            }
            for (k = 0; k < NELEMS(sByBattleEffects); k++) {
                if (sByBattleEffects[k] == effect) {
                    isAvailable = (sEffectAvailabilityByBattle[k] >> normalizedBattleNum) & 1;
                    break;
                }
            }
            if (isAvailable == TRUE) {
                roulette->availableEffects[roulette->numAvailableEffects] = effect;
                roulette->numAvailableEffects++;
            }
        }
    }
}

// GetEffectCategoryCounts: the tier from the performance, the effects of each kind
static void GetEffectCategoryCounts(PlatArcadeRoulette *roulette) {
    int i;

    for (i = 0; i < (int)NELEMS(sCategoryTierPerformanceThresholds); i++) {
        if (roulette->performance >= sCategoryTierPerformanceThresholds[i]) {
            break;
        }
    }
    roulette->categoryTier = (u8)i;
    for (i = 0; i < roulette->numAvailableEffects; i++) {
        roulette->availableEffectsPerCategory[PlatArcade_GetCategoryFromEffect(roulette->availableEffects[i])]++;
    }
}

// GetRandomCategory: a kind by the tier's weights (out of 100)
static u8 GetRandomCategory(PlatArcade *arcade, u8 categoryTier) {
    u8 category, sum = 0;
    u16 rand = PlatArcade_Random(arcade) % 100;

    for (category = PLATARCADE_CATEGORY_FOE; category < PLATARCADE_CATEGORIES; category++) {
        sum += sCategoryWeights[categoryTier][category];
        if (rand < sum) {
            break;
        }
    }
    if (category >= PLATARCADE_CATEGORIES) {
        category = PLATARCADE_CATEGORY_FOE;
    }
    return category;
}

// AssignEffectsToGrid: each panel a kind, then an effect of the kind from a random place in the list on (the next kind when
// the list has none: after a whole turn of it)
static void AssignEffectsToGrid(PlatArcade *arcade, PlatArcadeRoulette *roulette) {
    u8 effectsIndex, category, *perCategory = roulette->availableEffectsPerCategory;
    int i, numEffectsInCategory, startOffset, loopCounter;
    u16 start;

    for (i = 0; i < PLATARCADE_GRID; i++) {
        category = GetRandomCategory(arcade, roulette->categoryTier);
        numEffectsInCategory = perCategory[category];
        startOffset = 0;
        if (category == PLATARCADE_CATEGORY_ALLY) {
            startOffset += perCategory[PLATARCADE_CATEGORY_FOE];
        } else if (category == PLATARCADE_CATEGORY_ENV) {
            startOffset += perCategory[PLATARCADE_CATEGORY_FOE];
            startOffset += perCategory[PLATARCADE_CATEGORY_ALLY];
        } else if (category == PLATARCADE_CATEGORY_BONUS) {
            startOffset += perCategory[PLATARCADE_CATEGORY_FOE];
            startOffset += perCategory[PLATARCADE_CATEGORY_ALLY];
            startOffset += perCategory[PLATARCADE_CATEGORY_ENV];
        }
        start = (u16)DSMod(PlatArcade_Random(arcade), numEffectsInCategory);
        start += startOffset;
        effectsIndex = (u8)start;
        loopCounter = 0;
        while (TRUE) {
            if (loopCounter >= 50) {
                roulette->rouletteEffects[i] = PLATARCADE_EFFECT_LOWER_FOE_HP;
                break;
            }
            if (PlatArcade_GetCategoryFromEffect(roulette->availableEffects[effectsIndex]) == category) {
                roulette->rouletteEffects[i] = roulette->availableEffects[effectsIndex];
                break;
            }
            effectsIndex++;
            loopCounter++;
            if (effectsIndex >= roulette->numAvailableEffects) {
                effectsIndex = 0;
            }
            if (effectsIndex == start) {
                category++;
                if (category >= PLATARCADE_CATEGORIES) {
                    category = PLATARCADE_CATEGORY_FOE;
                }
            }
        }
    }
}

// SetupBattleArcadeAppArgs (the board's arguments: the weather back to clear, the random cursor passed on and cleared, the
// player's stats kept), then BattleArcadeApp_Init (the random number, the starting panel) and its fade-in (the 16 panels)
void PlatArcade_RouletteOpen(PlatArcade *arcade, PlatArcadeRoulette *roulette) {
    u8 *bytes = (u8 *)roulette;
    u32 i;

    for (i = 0; i < sizeof(PlatArcadeRoulette); i++) {
        bytes[i] = 0;
    }
    roulette->challengeType = arcade->challengeType;
    roulette->round = PlatArcade_GetCurrentRound(arcade);
    roulette->performance = arcade->performance;
    roulette->battleStreak = arcade->currentStreak;
    arcade->weather = PLATARCADE_WEATHER_CLEAR;
    roulette->randomizeCursorMovement = arcade->cursorRandomized;
    arcade->cursorRandomized = FALSE;
    arcade->immuneToEffect = FALSE;
    for (i = 0; i < arcade->playerCount && i < PLATARCADE_MAX_PARTY; i++) {
        arcade->monHP[i] = (u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_MAX_HP);
        arcade->monAtk[i] = (u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_ATK);
        arcade->monDef[i] = (u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_DEF);
        arcade->monSpeed[i] = (u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_SPEED);
        arcade->monSpAtk[i] = (u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_SP_ATK);
        arcade->monSpDef[i] = (u16)PlatArcade_MonGet(arcade, PLATARCADE_PLAYERS, (u8)i, PLATARCADE_MON_SP_DEF);
    }
    roulette->rouletteTimer = PLATARCADE_ROULETTE_FRAMES;
    for (i = 0; i < PLATARCADE_EFFECTS; i++) {
        roulette->availableEffects[i] = PLATARCADE_EFFECTS;
    }
    arcade->randomIndex = PlatArcade_Random(arcade);                   // GetRandomNumber
    roulette->startingCursorPos = PlatArcade_Random(arcade) % PLATARCADE_GRID;
    GetAvailableEffects(roulette);
    GetEffectCategoryCounts(roulette);
    AssignEffectsToGrid(arcade, roulette);
}

// State_OperateRoulette's first step: the cursor on the starting panel
void PlatArcade_RouletteStart(PlatArcadeRoulette *roulette) {
    roulette->cursorPos = (u8)roulette->startingCursorPos;
}

// State_OperateRoulette's running step, one frame: the cursor (UpdateCursorPosition: a move every sCursorMoveFrames frames of
// the speed, to the next panel or, after the Random effect, to a random one), the 30 seconds, the stop
BOOL PlatArcade_RouletteTick(PlatArcade *arcade, PlatArcadeRoulette *roulette, BOOL stopPressed) {
    roulette->cursorUpdateTimer++;
    if (roulette->cursorUpdateTimer >= PlatArcade_CursorMoveFrames(arcade->rouletteSpeed)) {
        roulette->cursorUpdateTimer = 0;
        if (roulette->randomizeCursorMovement == TRUE) {
            roulette->cursorPos = (u8)(PlatArcade_Random(arcade) % PLATARCADE_GRID);
        } else {
            roulette->cursorPos++;
        }
        if (roulette->cursorPos >= PLATARCADE_GRID) {
            roulette->cursorPos = 0;
        }
    }
    if (roulette->rouletteTimer > 0) {
        roulette->rouletteTimer--;
    }
    if (stopPressed || roulette->rouletteTimer == 0) {
        roulette->resultCursorPos = roulette->cursorPos;              // SetResultCursorPos
        return TRUE;
    }
    return FALSE;
}

// SetSelectedEffect, and the app's exit: the panel's effect, the cursor kept (StoreBattleArcadeAppResults)
void PlatArcade_RouletteStop(PlatArcade *arcade, PlatArcadeRoulette *roulette) {
    u8 pos = roulette->cursorPos < PLATARCADE_GRID ? roulette->cursorPos : (u8)(roulette->cursorPos - PLATARCADE_GRID);

    arcade->activeEffect = roulette->rouletteEffects[pos];
    arcade->appCursorPos = roulette->cursorPos;
}

#endif
