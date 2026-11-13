#include "pearlb2.h"
#include "types.h"
#include "pearlb2/plat_hall.h"

// Platinum's Battle Hall rules (include/pearlb2/plat_hall.h; PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Hall"), written from
// pokeplatinum's src/overlay104/battle_hall.c, battle_hall_helpers.c, src/battle_hall_save.c, battle_hall_win_records.c and
// overlay104/frontier_opponents.c, step for step, with the same random draws in the same order. It needs nothing of Black 2:
// its tables are gPlatHallTable's (passed in), the save goes through PlatHall_GetStat and its kin, so PearlB2's host harness
// (b2tools/platinum_hall_host) runs this file as it is beside Platinum's own C. Platinum's game-wide LCRNG (math_util.c) is the
// challenge's own here (PlatHallWork.lcrng), the same generator.

#if PEARLB2

#define LCRNG_MULTIPLIER 1103515245L    // pokeplatinum include/math_util.h
#define LCRNG_INCREMENT 24691
#define FX32_SHIFT 12
#define PLATHALL_FX_TO_F32(x) ((f32)((x) / (f32)(1 << FX32_SHIFT)))     // nitro/fx.h FX_FX32_TO_F32
#define MAX_IVS_SINGLE_STAT 31
#define MAX_EVS_SINGLE_STAT 255
#define MAX_EVS_ALL_STATS 510
#define MAX_FRIENDSHIP_VALUE 255
#define MAX_POKEMON_LEVEL 100
#define MOVE_FRUSTRATION 218
#define SHINY_ODDS 8
#define NATIONAL_DEX_COUNT 493

// battle_hall_helpers.c: the opponents' groups (indices into sBattleHallPotentialOpponents, plus 1)
#define GROUP_1_START 1
#define GROUP_2_START 155
#define GROUP_3_START 271
#define GROUP_4_START 376

typedef struct {
    u16 min;
    u16 max;
} PlatHallRange;

// sBattleHallAppGridOrder: the grid's cells, Platinum's types
static const u8 sGridOrder[PLAT_HALL_GRID_CELLS] = {
    0, 10, 11, 13, 12, 15, 1, 3, 4, 2, 14, 6, 5, 7, 16, 17, 8, PLAT_HALL_MON_SUMMARY, PLAT_HALL_MON_SUMMARY, PLAT_HALL_TYPE_MYSTERY,
};

// sBPPerRoundSolo, sBPPerRoundWiFi (BattleHall_GetEarnedBP)
static const u8 sBPPerRoundSolo[PLAT_HALL_MAX_ROUNDS + 1] = { 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 6, 6, 8, 8, 10, 10, 12 };
static const u8 sBPPerRoundWiFi[PLAT_HALL_MAX_ROUNDS + 1] = { 0, 6, 6, 6, 8, 8, 8, 10, 10, 10, 12, 12, 14, 15, 17, 17, 20, 20, 23 };

// sIVsPerTypeRank's ivs
static const u8 sIVsPerTypeRank[PLAT_HALL_MAX_RANK] = { 8, 10, 12, 14, 16, 18, 20, 22, 24, 26 };

u16 PlatHall_Random(PlatHallWork *w) {
    w->lcrng = w->lcrng * LCRNG_MULTIPLIER + LCRNG_INCREMENT;
    return w->lcrng >> 16;
}

// Two draws into a u32, the first the low half (Platinum's LCRNG_Next() | (LCRNG_Next() << 16))
static u32 Random32(PlatHallWork *w) {
    u32 low = PlatHall_Random(w);
    u32 high = PlatHall_Random(w);

    return low | (high << 16);
}

// The NitroSDK's FX_Sqrt (fx_cp.c): the divider's square root of x << 32, rounded to fx32
static s32 FxSqrt(s32 x) {
    u32 hi, lo, root, bit, rest_hi, rest_lo, trial_hi, trial_lo;

    if (x <= 0) {
        return 0;
    }
    // floor(sqrt((u64)x << 32)) by digits, in two words (no 64-bit division needed)
    hi = (u32)x;
    lo = 0;
    root = 0;
    rest_hi = 0;
    rest_lo = 0;
    for (bit = 0; bit < 32; bit++) {
        // shift two bits of the radicand into the remainder
        rest_hi = (rest_hi << 2) | (rest_lo >> 30);
        rest_lo = (rest_lo << 2) | (hi >> 30);
        hi = (hi << 2) | (lo >> 30);
        lo <<= 2;
        // trial = root * 4 + 1
        trial_hi = root >> 30;
        trial_lo = (root << 2) | 1;
        if (rest_hi > trial_hi || (rest_hi == trial_hi && rest_lo >= trial_lo)) {
            rest_hi = rest_hi - trial_hi - (rest_lo < trial_lo ? 1 : 0);
            rest_lo -= trial_lo;
            root = (root << 1) | 1;
        } else {
            root <<= 1;
        }
    }
    return (s32)((root + 0x200) >> 10);
}

static BOOL IsShiny(u32 otID, u32 personality) {
    return ((((otID & 0xffff0000) >> 16) ^ (otID & 0xffff) ^ ((personality & 0xffff0000) >> 16) ^ (personality & 0xffff)) <
            SHINY_ODDS);
}

static u16 CheckTypeRank(u8 typeRank) {
    if (typeRank >= PLAT_HALL_MAX_RANK) {
        typeRank = PLAT_HALL_MAX_RANK - 1;
    }
    return typeRank;
}

u8 PlatHall_GetRankOfType(u8 idx, const u8 *typeRanks) {
    u8 byte = idx / 2;
    u8 nybble = idx % 2;

    return (typeRanks[byte] >> (4 * nybble)) & 0xf;
}

void PlatHall_SetRankOfType(u8 idx, u8 *typeRanks, u8 value) {
    u8 byte = idx / 2;
    u8 nybble = idx % 2;

    if (nybble == 0) {
        typeRanks[byte] = typeRanks[byte] & 0xf0;
    } else {
        typeRanks[byte] = typeRanks[byte] & 0xf;
    }
    typeRanks[byte] |= (u8)(value << (4 * nybble));
}

void PlatHall_ResetRankOfAllTypes(u8 *typeRanks) {
    int i;

    for (i = 0; i < PLAT_HALL_TYPES; i++) {
        PlatHall_SetRankOfType(i, typeRanks, 0);
    }
}

// BattleFrontierStats_GetHall*Index: which 0 current streak, 1 latest streak, 2 latest species, 3 + n the ranks of types 2n, 2n + 1
u32 PlatHall_StatIndex(u8 challengeType, u32 which) {
    return PLAT_HALL_STAT_SINGLE + challengeType * PLAT_HALL_STAT_STRIDE + which;
}

// BattleHall_LoadTypeRanks
static u16 LoadTypeRank(void *save, u8 challengeType, u8 type) {
    u16 rankPair = PlatHall_GetStat(save, PlatHall_StatIndex(challengeType, PLAT_HALL_STAT_RANKS + type / 2));

    rankPair &= 0xff;
    if (type % 2 == 0) {
        return rankPair & 0xf;
    }
    return rankPair >> 4;
}

// BattleHall_SaveTypeRank
static void SaveTypeRank(void *save, u8 challengeType, u8 type, u8 value) {
    u16 rankPair = PlatHall_GetStat(save, PlatHall_StatIndex(challengeType, PLAT_HALL_STAT_RANKS + type / 2)) & 0xff;
    u8 currentRanks = (u8)(((rankPair >> 4) << 4) | (rankPair & 0xf));
    u8 nybble = type % 2;

    if (nybble == 0) {
        currentRanks = currentRanks & 0xf0;
    } else {
        currentRanks = currentRanks & 0xf;
    }
    currentRanks |= (u8)(value << (4 * nybble));
    PlatHall_SetStat(save, PlatHall_StatIndex(challengeType, PLAT_HALL_STAT_RANKS + type / 2), currentRanks);
}

u8 PlatHall_GetPlayerPartySize(u8 challengeType) {
    return challengeType == PLAT_HALL_DOUBLE ? 2 : 1;
}

static u8 GetOpponentPartySize(u8 challengeType) {
    return challengeType == PLAT_HALL_DOUBLE ? 2 : 1;
}

// BattleHall_Init (the party's held items are the field's: hall_field.c)
void PlatHall_Init(PlatHallWork *w, void *save, u16 resuming, u8 challengeType, u8 slot1, u8 slot2) {
    u16 i;
    u8 streakActive, partySize;
    u32 lcrng = w->lcrng;
    u16 levels[2], species;
    PlatHallSave *saved = &w->save;
    u8 *raw = (u8 *)w;

    levels[0] = w->levels[0];
    levels[1] = w->levels[1];
    species = w->species;
    for (i = 0; i < (u16)((u8 *)saved - raw); i++) {      // the work, not the saved challenge
        raw[i] = 0;
    }
    w->magic = PLAT_HALL_WORK_MAGIC;
    w->lcrng = lcrng;
    w->levels[0] = levels[0];
    w->levels[1] = levels[1];
    w->species = species;

    if (!resuming) {
        w->challengeType = challengeType;
        partySize = PlatHall_GetPlayerPartySize(w->challengeType);
        w->currentBattle = 0;
        for (i = 0; i < sizeof(PlatHallSave); i++) {         // BattleHallSave_Init
            ((u8 *)saved)[i] = 0;
        }
        streakActive = (u8)PlatHall_GetStreakFlag(save, w->challengeType);
        if (streakActive == TRUE) {
            w->currentStreak = PlatHall_GetStat(save, PlatHall_StatIndex(w->challengeType, PLAT_HALL_STAT_LATEST));
        } else {
            w->currentStreak = 0;
            for (i = 0; i < PLAT_HALL_TYPES; i++) {
                SaveTypeRank(save, w->challengeType, (u8)i, 0);
            }
        }
        w->partySlots[0] = slot1;
        w->partySlots[1] = slot2;
    } else {
        w->challengeType = saved->challengeType;
        partySize = PlatHall_GetPlayerPartySize(w->challengeType);
        w->currentBattle = saved->currentBattleNum;
        w->currentStreak = PlatHall_GetStat(save, PlatHall_StatIndex(w->challengeType, PLAT_HALL_STAT_LATEST));
        for (i = 0; i < partySize; i++) {
            w->partySlots[i] = saved->partySlots[i];
        }
        for (i = 0; i < PLAT_HALL_BATTLES_PER_ROUND * 2; i++) {
            w->trainerIDs[i] = saved->trainerIDs[i];
        }
        for (i = 0; i < PLAT_HALL_BATTLES_PER_ROUND * 2; i++) {
            w->monIndices[i] = (u8)saved->monIndices[i];      // (u8) as Platinum's: a resumed index above 255 loses its high byte
        }
    }
    (void)partySize;

    w->currentRound = w->currentStreak / PLAT_HALL_BATTLES_PER_ROUND;
    if (w->challengeType == PLAT_HALL_MULTI) {
        for (i = 0; i < PLAT_HALL_TYPES; i++) {
            PlatHall_SetRankOfType((u8)i, &w->typeRanks[2][0], PLAT_HALL_MAX_RANK - 1);
        }
    } else {
        for (i = 0; i < PLAT_HALL_TYPES; i++) {
            PlatHall_SetRankOfType((u8)i, &w->typeRanks[w->challengeType][0], (u8)LoadTypeRank(save, w->challengeType, (u8)i));
        }
    }
}

// BattleHall_PickOpponentTrainerClasses
static void PickOpponentTrainerClasses(PlatHallWork *w, const PlatHallTable *t, u8 selectedTypeIdx, u8 numTrainers, u8 typeRank,
                                       u8 currentBattle, u16 trainerIDs[]) {
    int i = 0;
    u8 offset = currentBattle * 2;
    u16 rand;

    typeRank = (u8)CheckTypeRank(typeRank);
    do {
        rand = PlatHall_Random(w) % (8 + 4);
        if (rand < 8) {
            trainerIDs[offset + i] = t->classesByRank[typeRank][rand];
        } else {
            trainerIDs[offset + i] = t->classesByType[selectedTypeIdx][rand - 8];
        }
        i++;
    } while (i < numTrainers);
}

// BattleHall_PickOpponentTrainers: a Trainer of each picked class, none twice in the round; Argenta at the 50th and 170th
static void PickOpponentTrainers(PlatHallWork *w, const PlatHallTable *t, u8 challengeType, u8 numTrainers, int currentRound,
                                 u8 rank, u8 currentBattle, u16 trainerIDs[]) {
    int startingIndex;
    int selectedTrainers = 0;
    u8 offset = currentBattle * 2;
    u8 typeRank = (u8)CheckTypeRank(rank);
    int currentStreak, trainerClass, pastTrainersIdx;
    u16 trainerID, newIdx;

    if (challengeType == PLAT_HALL_SINGLE) {
        currentStreak = (currentRound * PLAT_HALL_BATTLES_PER_ROUND) + (currentBattle + 1);
        if (currentStreak == PLAT_HALL_STREAK_SILVER) {
            trainerIDs[offset] = PLAT_HALL_ARGENTA_SILVER;
            return;
        } else if (currentStreak == PLAT_HALL_STREAK_GOLD) {
            trainerIDs[offset] = PLAT_HALL_ARGENTA_GOLD;
            return;
        }
    }
    do {
        trainerID = PlatHall_Random(w) % t->trainerClassCount;
        startingIndex = trainerID;
        while (TRUE) {
            trainerClass = trainerIDs[offset + selectedTrainers];
            if (trainerClass == t->trainerClasses[trainerID]) {
                for (pastTrainersIdx = 0; pastTrainersIdx < (offset + selectedTrainers); pastTrainersIdx++) {
                    if (trainerIDs[pastTrainersIdx] == trainerID) {
                        break;
                    }
                }
                if (pastTrainersIdx == (offset + selectedTrainers)) {
                    trainerIDs[offset + selectedTrainers] = trainerID;
                    selectedTrainers++;
                    break;
                }
            }
            trainerID++;
            if (trainerID >= t->trainerClassCount) {
                trainerID = 0;
            }
            if (trainerID == startingIndex) {
                while (TRUE) {
                    newIdx = PlatHall_Random(w) % 8;
                    if (trainerClass != t->classesByRank[typeRank][newIdx]) {
                        trainerIDs[offset + selectedTrainers] = t->classesByRank[typeRank][newIdx];
                        break;
                    }
                }
            }
        }
    } while (selectedTrainers < numTrainers);
}

// BattleHall_PickNextOpponentPokemon: for a normal battle from the group the rank allows, of the chosen type, not fought yet this
// round (once the whole group was searched: not the last one); Argenta's Silver battle from the player's species' group, her Gold
// from group 4
static void PickNextOpponentPokemon(PlatHallWork *w, const PlatHallTable *t, u8 numOpponentsToPick, u8 selectedType, u8 typeRank,
                                    u8 currentBattle, u16 playersSpecies, u16 opponentIndices[], u8 battleType) {
    PlatHallRange matchupRange;
    PlatHallRange groups[4];
    int opponentsFound = 0;
    u8 loopedThrough = FALSE;
    u8 currentBattleIndex = currentBattle * 2;
    u16 i, playersMonIndex = 0, playersMonsGroup, groupSize, opponentIndex, startingIndex, pastOpponentsIndex;
    u16 count = t->opponentCount;

    typeRank = (u8)CheckTypeRank(typeRank);
    groups[0].min = GROUP_1_START;
    groups[0].max = GROUP_2_START - 1;
    groups[1].min = GROUP_2_START;
    groups[1].max = GROUP_3_START - 1;
    groups[2].min = GROUP_3_START;
    groups[2].max = GROUP_4_START - 1;
    groups[3].min = GROUP_4_START;
    groups[3].max = count;

    if (battleType != PLAT_HALL_NEXT_NORMAL) {
        for (i = 0; i < count; i++) {
            if (playersSpecies == t->opponents[i]) {
                playersMonIndex = i;
                break;
            }
        }
        if (i == count) {
            playersMonIndex = groups[3].min;
        }
        for (playersMonsGroup = 0; playersMonsGroup < 4; playersMonsGroup++) {
            if (playersMonIndex < groups[playersMonsGroup].max) {
                break;
            }
        }
        if (playersMonsGroup == 4) {
            playersMonsGroup = 3;
        }
        if (battleType == PLAT_HALL_NEXT_GOLD) {
            matchupRange = groups[3];
        } else {
            matchupRange = groups[playersMonsGroup];
        }
    } else {
        // sPotentialMatchupRangesByRank
        if (typeRank < 2) {
            matchupRange.min = GROUP_1_START;
            matchupRange.max = GROUP_2_START - 1;
        } else if (typeRank < 5) {
            matchupRange.min = GROUP_1_START;
            matchupRange.max = GROUP_3_START - 1;
        } else if (typeRank < 8) {
            matchupRange.min = GROUP_2_START;
            matchupRange.max = GROUP_4_START - 1;
        } else {
            matchupRange.min = GROUP_3_START;
            matchupRange.max = count;
        }
    }

    groupSize = matchupRange.max - matchupRange.min + 1;
    opponentIndex = matchupRange.min + PlatHall_Random(w) % groupSize;
    opponentIndex -= 1;
    startingIndex = opponentIndex;

    while (opponentsFound < numOpponentsToPick) {
        if (!loopedThrough) {
            for (pastOpponentsIndex = 0; pastOpponentsIndex < currentBattleIndex; pastOpponentsIndex++) {
                if (opponentIndices[pastOpponentsIndex] == (opponentIndex + 1)) {
                    break;
                }
            }
        } else {
            if (opponentIndices[currentBattleIndex - 2] == (opponentIndex + 1)) {
                pastOpponentsIndex = 0;
            } else {
                pastOpponentsIndex = currentBattleIndex;
            }
        }
        if (pastOpponentsIndex == currentBattleIndex) {
            if (battleType != 0) {
                if (playersSpecies != t->opponents[opponentIndex]) {
                    opponentIndices[currentBattleIndex + opponentsFound] = opponentIndex + 1;
                    opponentsFound++;
                }
            } else if (selectedType == t->opponentTypes[opponentIndex][0] || selectedType == t->opponentTypes[opponentIndex][1]) {
                if (playersSpecies != t->opponents[opponentIndex]) {
                    opponentIndices[currentBattleIndex + opponentsFound] = opponentIndex + 1;
                    opponentsFound++;
                }
            }
        }
        opponentIndex++;
        if (opponentIndex + 1 >= matchupRange.max) {
            opponentIndex = matchupRange.min - 1;
        }
        if (opponentIndex == startingIndex) {
            loopedThrough = TRUE;
        }
    }
}

// BattleHall_GetHighestLevelInParty (the levels are the party's, read by the field at each op)
u16 PlatHall_GetHighestLevelInParty(PlatHallWork *w) {
    u16 firstMonsLevel = w->levels[0];

    if (PlatHall_GetPlayerPartySize(w->challengeType) == 2) {
        return firstMonsLevel > w->levels[1] ? firstMonsLevel : w->levels[1];
    }
    return firstMonsLevel;
}

// BattleHall_CalcOpponentsLevel: the player's level, less three square roots of it, plus the rank's share, plus half a level for
// each type fought (the chosen one counted), never above the player's
u16 PlatHall_CalcOpponentsLevel(PlatHallWork *w) {
    s32 baseLevel;
    int type;
    u8 typeRank = PlatHall_GetRankOfType(w->selectedTypeIdx, &w->typeRanks[w->challengeType][0]);
    int playersLevel = PlatHall_GetHighestLevelInParty(w);
    float rankFactor, numBattledTypesFactor, opponentsLevelFloat;
    s32 product;
    int opponentsLevel;

    if (w->challengeType == PLAT_HALL_MULTI) {
        return playersLevel;
    }
    baseLevel = (playersLevel << FX32_SHIFT) - w->playerLevelSqrt * 3;
    rankFactor = PLATHALL_FX_TO_F32(w->playerLevelSqrt) * 5.0;
    if (playersLevel / rankFactor < 1.0) {
        rankFactor = typeRank + 1 - 1;
    } else {
        product = (s32)(typeRank * playersLevel) << FX32_SHIFT;
        rankFactor = PLATHALL_FX_TO_F32(product) / rankFactor;
    }
    numBattledTypesFactor = 0.0;
    for (type = 0; type < PLAT_HALL_TYPES; type++) {
        if (type == w->selectedTypeIdx) {
            numBattledTypesFactor += 1.0;
        } else if (PlatHall_GetRankOfType((u8)type, &w->typeRanks[w->challengeType][0]) > 0) {
            numBattledTypesFactor += 1.0;
        }
    }
    if (numBattledTypesFactor != 0.0) {
        numBattledTypesFactor -= 1.0;
    }
    numBattledTypesFactor *= 0.5;
    opponentsLevelFloat = PLATHALL_FX_TO_F32(baseLevel) + rankFactor + numBattledTypesFactor;
    opponentsLevel = (int)(opponentsLevelFloat);
    // Platinum's float != float: compared as doubles (a float converts to a double exactly, so the answer is the same), as Black
    // 2's soft-float library has no _fneq (_f2d and _dneq it has)
    if ((double)opponentsLevelFloat != (double)(int)opponentsLevelFloat) {
        opponentsLevel++;
    }
    if (opponentsLevel > playersLevel) {
        opponentsLevel = playersLevel;
    }
    if (opponentsLevel > MAX_POKEMON_LEVEL) {
        opponentsLevel = MAX_POKEMON_LEVEL;
    }
    return (u16)opponentsLevel;
}

u8 PlatHall_GetHallMatronTypeRank(PlatHallWork *w) {
    return (u8)(w->levels[0] / 10);
}

// SetupNextOpponent: the next battle's Trainer and Pokémon
void PlatHall_SetupNextOpponent(PlatHallWork *w, const PlatHallTable *t) {
    u8 battleType = PLAT_HALL_NEXT_NORMAL;
    u8 numOppTrainers = w->challengeType != PLAT_HALL_SINGLE ? 2 : 1;
    u8 typeRank = PlatHall_GetRankOfType(w->selectedTypeIdx, &w->typeRanks[w->challengeType][0]);
    u8 offset;

    w->opponentsLevel = (u8)PlatHall_CalcOpponentsLevel(w);
    PickOpponentTrainerClasses(w, t, w->selectedTypeIdx, numOppTrainers, typeRank, w->currentBattle, w->trainerIDs);
    PickOpponentTrainers(w, t, w->challengeType, numOppTrainers, w->currentRound, typeRank, w->currentBattle, w->trainerIDs);
    offset = w->currentBattle * 2;
    if (w->trainerIDs[offset] == PLAT_HALL_ARGENTA_SILVER || w->trainerIDs[offset] == PLAT_HALL_ARGENTA_GOLD) {
        typeRank = PlatHall_GetHallMatronTypeRank(w);
    }
    if (w->trainerIDs[offset] == PLAT_HALL_ARGENTA_SILVER) {
        battleType = PLAT_HALL_NEXT_SILVER;
    }
    if (w->trainerIDs[offset] == PLAT_HALL_ARGENTA_GOLD) {
        battleType = PLAT_HALL_NEXT_GOLD;
    }
    PickNextOpponentPokemon(w, t, 1, w->selectedType, typeRank, w->currentBattle, w->species, w->monIndices, battleType);
}

// The battle's rank (BattleHall_SetupBattle): the chosen type's; the Multi's is the top
u8 PlatHall_GetBattleRank(PlatHallWork *w) {
    u8 rank = PlatHall_GetRankOfType(w->selectedTypeIdx, &w->typeRanks[w->challengeType][0]);

    if (w->challengeType == PLAT_HALL_MULTI) {
        rank = PLAT_HALL_MAX_RANK - 1;
    }
    return rank;
}

// BattleHall_GetAIMask, as Platinum calls it: BattleHall_SetupBattle passes the battle's offset (currentBattle * 2) where the
// battle's number belongs, and the function doubles it again, so the Argenta test reads trainerIDs[currentBattle * 4]: another
// battle's Trainer for battles 1-5, and past the array for 6-10, into opponents[0] (BH_FUNC_LOAD_TRAINERS loads the current
// Trainer there just before): battle 6 its id, battle 7 its name's first character, battle 8 the fifth, battle 9 introMsg[0]
// (0xffff), battle 10 winMsg[0] (0). Argenta's ids are the characters I and J (Gen 4 codes 307, 308), so in a Single the 7th
// battle of a round against a Trainer whose name starts with I or J gets her full AI: Platinum's, kept (gPlatHallTable nameFlags)
static u16 ArgentaProbe(PlatHallWork *w, const PlatHallTable *t) {
    u32 k = w->currentBattle * 4;
    u16 current = w->trainerIDs[w->currentBattle * 2];
    u8 flags = current < t->trainerClassCount ? t->nameFlags[current] : 0;

    if (k < PLAT_HALL_BATTLES_PER_ROUND * 2) {
        return w->trainerIDs[k];
    }
    switch (k) {
    case 20:
        return current;                                     // opponents[0].trainer.trainerID (its low half)
    case 24:
        return (flags & PLAT_HALL_NAME_FIRST_IJ) ? PLAT_HALL_ARGENTA_SILVER : 0;    // trainerName[0]
    case 28:
        return (flags & PLAT_HALL_NAME_FIFTH_IJ) ? PLAT_HALL_ARGENTA_SILVER : 0;    // trainerName[4]
    case 32:
        return 0xffff;                                      // introMsg[0]
    default:
        return 0;                                           // winMsg[0]
    }
}

u16 PlatHall_GetAIMask(PlatHallWork *w, const PlatHallTable *t, u8 rank) {
    u16 aiMask, probe;

    if (rank + 1 >= 8) {
        aiMask = PLAT_HALL_AI_BASIC | PLAT_HALL_AI_EVAL_ATTACK | PLAT_HALL_AI_EXPERT;
    } else if (rank + 1 >= 4) {
        aiMask = PLAT_HALL_AI_BASIC;
    } else {
        aiMask = 0;
    }
    if (w->challengeType == PLAT_HALL_SINGLE) {
        probe = ArgentaProbe(w, t);
        if (probe == PLAT_HALL_ARGENTA_SILVER || probe == PLAT_HALL_ARGENTA_GOLD) {
            aiMask = PLAT_HALL_AI_BASIC | PLAT_HALL_AI_EVAL_ATTACK | PLAT_HALL_AI_EXPERT;
        }
    }
    if (w->challengeType == PLAT_HALL_MULTI) {
        aiMask = PLAT_HALL_AI_BASIC | PLAT_HALL_AI_EVAL_ATTACK | PLAT_HALL_AI_EXPERT;
    }
    return aiMask;
}

// FrontierPokemon_Init (frontier_opponents.c) for a set, its Trainer's ID and the IVs, the personality drawn
static void LoadOpponentMon(PlatHallWork *w, const PlatHallTable *t, PlatHallMon *mon, u16 setIdx, u32 otID, u8 ivs) {
    const PlatHallSet *set = &t->sets[setIdx < t->setCount ? setIdx : 0];
    u32 personality;
    u8 friendship = MAX_FRIENDSHIP_VALUE;
    int i, evs = 0;

    for (i = 0; i < (int)sizeof(PlatHallMon); i++) {
        ((u8 *)mon)[i] = 0;
    }
    mon->species = set->species;
    mon->form = set->form;
    mon->item = set->item;
    for (i = 0; i < 4; i++) {
        mon->moves[i] = set->moves[i];
        if (set->moves[i] == MOVE_FRUSTRATION) {
            friendship = 0;
        }
    }
    mon->otID = otID;
    do {
        personality = Random32(w);
    } while (set->nature != personality % 25 || IsShiny(otID, personality) == TRUE);
    mon->personality = personality;
    mon->ivs = ivs;
    for (i = 0; i < 6; i++) {
        if (set->evFlags & (1 << i)) {
            evs++;
        }
    }
    if (evs != 0) {                         // (Platinum divides by 0 for set 0, then gives no stat any: the same)
        if (MAX_EVS_ALL_STATS / evs > MAX_EVS_SINGLE_STAT) {
            evs = MAX_EVS_SINGLE_STAT;
        } else {
            evs = MAX_EVS_ALL_STATS / evs;
        }
        for (i = 0; i < 6; i++) {
            if (set->evFlags & (1 << i)) {
                mon->evs[i] = (u8)evs;
            }
        }
    }
    mon->friendship = friendship;
}

// BattleHall_LoadOpponentMonData, then BattleHall_SetupBattle's loop: each of the opponent's Pokémon is the first set's, its
// personality moved by 250,025 (the nature kept) until it isn't shiny, once more for the second (Platinum's Doubles field two of
// the same set; the second set is loaded, drawing its numbers, and not used), its ability Pokemon_CalcAbility's
void PlatHall_MakeOpponents(PlatHallWork *w, const PlatHallTable *t) {
    PlatHallMon loaded[2];
    u8 offset = w->currentBattle * 2;
    u8 rank = PlatHall_GetBattleRank(w);
    u8 partySize = GetOpponentPartySize(w->challengeType);
    u8 ivs;
    u32 otID, personality;
    int i;
    const u8 *abilities;

    if (w->trainerIDs[offset] == PLAT_HALL_ARGENTA_SILVER || w->trainerIDs[offset] == PLAT_HALL_ARGENTA_GOLD) {
        ivs = MAX_IVS_SINGLE_STAT;
    } else {
        ivs = sIVsPerTypeRank[CheckTypeRank(rank)];
    }
    for (i = 0; i < partySize; i++) {
        otID = Random32(w);                                 // BattleFrontier_LoadOpponentMonData
        LoadOpponentMon(w, t, &loaded[i], w->monIndices[offset + i], otID, ivs);
    }
    for (i = 0; i < partySize; i++) {
        do {                                                // BattleHall_SetMonsPersonality
            personality = loaded[0].personality;
            if (personality > ((24 + 1) * 10001)) {
                personality -= ((24 + 1) * 10001);
            } else {
                personality += ((24 + 1) * 10001);
            }
            loaded[0].personality = personality;
        } while (IsShiny(loaded[0].otID, loaded[0].personality) != 0);
        w->mons[i] = loaded[0];
        abilities = t->setAbilities[w->monIndices[offset] < t->setCount ? w->monIndices[offset] : 0];
        w->mons[i].ability = abilities[1] != 0 && (w->mons[i].personality & 1) ? abilities[1] : abilities[0];
        w->mons[i].nature = (u8)(w->mons[i].personality % 25);
        // ---- plat-arcade (2026-11-07): BattleHall_SetupBattle makes each Pokémon here with FrontierPokemon_InitPokemon, whose
        // Pokemon_InitWith draws random numbers (pokemon.c sub_02073E18): a trainer id until it isn't shiny with the personality
        // (OTID_NOT_SHINY), then two for the IVs, given as one number of 32 or more. The values are overwritten (the set's trainer
        // id and IVs), but the numbers after them are Platinum's only with these drawn (platinum_hall_host's model draws them now)
        do {
            otID = Random32(w);
        } while (IsShiny(otID, loaded[0].personality));
        if ((((u32)loaded[0].ivs * 0x2108421) & 0x3fffffff) >= 32) {
            PlatHall_Random(w);
            PlatHall_Random(w);
        }
        // ---- end plat-arcade
    }
}

// BattleHall_GetOpponentLevel
u16 PlatHall_GetOpponentLevel(PlatHallWork *w) {
    u8 offset = w->currentBattle * 2;

    if (w->trainerIDs[offset] == PLAT_HALL_ARGENTA_SILVER || w->trainerIDs[offset] == PLAT_HALL_ARGENTA_GOLD) {
        return PlatHall_GetHighestLevelInParty(w);
    }
    return w->opponentsLevel;
}

// BattleHall_GetEarnedBP: for the round just cleared
u16 PlatHall_GetEarnedBP(PlatHallWork *w) {
    u8 bp;

    if (w->challengeType == PLAT_HALL_SINGLE || w->challengeType == PLAT_HALL_DOUBLE) {
        bp = w->currentRound >= PLAT_HALL_MAX_ROUNDS ? sBPPerRoundSolo[PLAT_HALL_MAX_ROUNDS] : sBPPerRoundSolo[w->currentRound];
    } else {
        bp = w->currentRound >= PLAT_HALL_MAX_ROUNDS ? sBPPerRoundWiFi[PLAT_HALL_MAX_ROUNDS] : sBPPerRoundWiFi[w->currentRound];
    }
    if (w->challengeType == PLAT_HALL_SINGLE) {
        if (w->currentStreak == PLAT_HALL_STREAK_SILVER || w->currentStreak == PLAT_HALL_STREAK_GOLD) {
            bp = 20;
        }
    } else if (w->challengeType == PLAT_HALL_MULTI) {
        bp = 12;
    }
    return bp;
}

// BattleHall_CapTypeRanks: every type at the top rank, all go back to the top rank's start
void PlatHall_CapTypeRanks(PlatHallWork *w) {
    int type;

    if (w->challengeType != PLAT_HALL_MULTI) {
        for (type = 0; type < PLAT_HALL_TYPES - 1; type++) {
            if (PlatHall_GetRankOfType((u8)type, &w->typeRanks[w->challengeType][0]) < PLAT_HALL_MAX_RANK) {
                break;
            }
        }
        if (type == PLAT_HALL_TYPES - 1) {
            for (type = 0; type < PLAT_HALL_TYPES - 1; type++) {
                PlatHall_SetRankOfType((u8)type, &w->typeRanks[w->challengeType][0], PLAT_HALL_MAX_RANK - 1);
            }
        }
    }
}

void PlatHall_CalcPlayerLevelSqrt(PlatHallWork *w) {
    w->playerLevelSqrt = FxSqrt(PlatHall_GetHighestLevelInParty(w) << FX32_SHIFT);
}

u8 PlatHall_CursorPosToType(u8 cell) {
    return cell < PLAT_HALL_GRID_CELLS ? sGridOrder[cell] : PLAT_HALL_MON_SUMMARY;
}

// BattleHall_GetTypeSelectionAppResult
void PlatHall_SetSelectedCell(PlatHallWork *w, u16 cell) {
    w->selectedTypeIdx2 = cell;
    w->selectedTypeIdx = (u8)w->selectedTypeIdx2;
    w->selectedType = PlatHall_CursorPosToType((u8)w->selectedTypeIdx2);
    if (w->selectedTypeIdx >= 17) {
        w->selectedTypeIdx = 17;
    }
}

// BH_FUNC_GET_NEXT_BATTLE_TYPE
u16 PlatHall_GetNextBattleType(PlatHallWork *w) {
    if (w->challengeType == PLAT_HALL_SINGLE) {
        if (w->currentStreak + 1 == PLAT_HALL_STREAK_SILVER) {
            return PLAT_HALL_NEXT_SILVER;
        } else if (w->currentStreak + 1 == PLAT_HALL_STREAK_GOLD) {
            return PLAT_HALL_NEXT_GOLD;
        }
    }
    return PLAT_HALL_NEXT_NORMAL;
}

// BH_FUNC_INCREMENT_RANK_OF_BEATEN_TYPE
void PlatHall_IncrementRankOfBeatenType(PlatHallWork *w) {
    u8 rank = PlatHall_GetRankOfType(w->selectedTypeIdx, &w->typeRanks[w->challengeType][0]);

    if (rank < PLAT_HALL_MAX_RANK) {
        PlatHall_SetRankOfType(w->selectedTypeIdx, &w->typeRanks[w->challengeType][0], rank + 1);
    }
}

// The type grid's rules (applications/frontier/battle_hall/main.c State_SelectNextBattle): a type at the full rank can't be
// picked, nor the Mystery cell; a summary cell isn't a pick. 0 can be picked, 1 can't, 2 can, and the Hall Matron comes next
// (NextOpponentIsHallMatron: the app's streak is the next battle's number)
u32 PlatHall_TypeCellCheck(PlatHallWork *w, u16 cell) {
    u8 type;

    if (cell >= PLAT_HALL_GRID_CELLS) {
        return 1;
    }
    type = PlatHall_CursorPosToType((u8)cell);
    if (type == PLAT_HALL_MON_SUMMARY || type == PLAT_HALL_TYPE_MYSTERY) {
        return 1;
    }
    if (PlatHall_GetRankOfType((u8)(cell >= 17 ? 17 : cell), &w->typeRanks[w->challengeType][0]) >= PLAT_HALL_MAX_RANK) {
        return 1;
    }
    if (w->challengeType == PLAT_HALL_SINGLE &&
        (w->currentStreak + 1 == PLAT_HALL_STREAK_SILVER || w->currentStreak + 1 == PLAT_HALL_STREAK_GOLD)) {
        return 2;
    }
    return 0;
}

// BattleHall_Save: saveType 0 a round cleared, 1 a loss, 2 the quick save (no streak written)
void PlatHall_Save(PlatHallWork *w, void *save, u8 saveType) {
    u16 i;
    PlatHallSave *saved = &w->save;

    saved->challengeType = w->challengeType;
    saved->didSave = TRUE;
    saved->currentBattleNum = w->currentBattle;
    PlatHall_SetStat(save, PlatHall_StatIndex(w->challengeType, PLAT_HALL_STAT_LATEST), w->currentStreak);
    if (saveType != 2) {
        if (w->challengeType != PLAT_HALL_MULTI_WFC) {
            PlatHall_SetStat(save, PlatHall_StatIndex(w->challengeType, PLAT_HALL_STAT_CURRENT), w->currentStreak);
        }
        PlatHall_SetStreakFlag(save, w->challengeType, w->saveStreak);
    }
    for (i = 0; i < PLAT_HALL_BATTLES_PER_ROUND * 2; i++) {
        saved->trainerIDs[i] = w->trainerIDs[i];
    }
    for (i = 0; i < 2; i++) {
        saved->partySlots[i] = w->partySlots[i];
    }
    for (i = 0; i < PLAT_HALL_TYPES; i++) {
        SaveTypeRank(save, w->challengeType, (u8)i, PlatHall_GetRankOfType((u8)i, &w->typeRanks[w->challengeType][0]));
    }
    for (i = 0; i < PLAT_HALL_BATTLES_PER_ROUND * 2; i++) {
        saved->monIndices[i] = w->monIndices[i];
    }
    PlatHall_SetStat(save, PlatHall_StatIndex(w->challengeType, PLAT_HALL_STAT_SPECIES), w->species);
}

void PlatHall_SaveOnLoss(PlatHallWork *w, void *save) {
    PlatHall_ResetRankOfAllTypes(&w->typeRanks[w->challengeType][0]);
    PlatHall_Save(w, save, 1);
}

void PlatHall_SaveOnCompletingRound(PlatHallWork *w, void *save) {
    w->saveStreak = TRUE;
    if (w->currentRound < PLAT_HALL_MAX_ROUNDS) {
        w->currentRound++;
    }
    w->currentBattle = 0;
    PlatHall_Save(w, save, 0);
}

// BattleHall_ClearActiveStreak (the lobby's DeleteActiveBattleHallStreak)
void PlatHall_ClearActiveStreak(void *save, u8 challengeType) {
    PlatHall_SetStreakFlag(save, challengeType, 0);
    PlatHall_SetStat(save, PlatHall_StatIndex(challengeType, PLAT_HALL_STAT_LATEST), 0);
}

// BattleHallWinRecords_GetRecordForSpecies
u16 PlatHall_GetRecordForSpecies(void *save, u8 challengeType, u16 species) {
    u16 *records = PlatHall_WinRecords(save);
    u16 record;

    if (records == NULL || challengeType > PLAT_HALL_DOUBLE || species >= PLAT_HALL_WIN_SPECIES) {
        return 0;
    }
    record = records[challengeType * PLAT_HALL_WIN_SPECIES + species];
    return record > PLAT_HALL_STAT_MAX ? PLAT_HALL_STAT_MAX : record;
}

// BattleHall_UpdateWinRecordForCurrentMon (BattleHallWinRecords_UpdateRecord): the species' record rises to the current streak;
// TRUE when the streak isn't the record that was there (Platinum's answer, also when it's lower)
u16 PlatHall_UpdateWinRecord(PlatHallWork *w, void *save) {
    u16 *records = PlatHall_WinRecords(save);
    u16 newRecord, currentRecord, species;

    if (w->challengeType == PLAT_HALL_MULTI_WFC) {
        return FALSE;
    }
    newRecord = PlatHall_GetStat(save, PlatHall_StatIndex(w->challengeType, PLAT_HALL_STAT_CURRENT));
    species = PlatHall_GetStat(save, PlatHall_StatIndex(w->challengeType, PLAT_HALL_STAT_SPECIES));
    currentRecord = PlatHall_GetRecordForSpecies(save, w->challengeType, species);
    if (records != NULL && w->challengeType <= PLAT_HALL_DOUBLE && species < PLAT_HALL_WIN_SPECIES) {
        if (currentRecord < newRecord) {
            records[w->challengeType * PLAT_HALL_WIN_SPECIES + species] =
                newRecord > PLAT_HALL_STAT_MAX ? PLAT_HALL_STAT_MAX : newRecord;
        } else if (records[w->challengeType * PLAT_HALL_WIN_SPECIES + species] > PLAT_HALL_STAT_MAX) {
            records[w->challengeType * PLAT_HALL_WIN_SPECIES + species] = PLAT_HALL_STAT_MAX;
        }
    }
    return newRecord != currentRecord;
}

// ScrCmd_GetNumSpeciesWithBattleHallRecords
u16 PlatHall_CountSpeciesWithRecords(void *save) {
    u32 species, n = 0;

    for (species = 0; species < NATIONAL_DEX_COUNT; species++) {
        if (PlatHall_GetRecordForSpecies(save, PLAT_HALL_SINGLE, (u16)species) +
                PlatHall_GetRecordForSpecies(save, PLAT_HALL_DOUBLE, (u16)species) > 0) {
            n++;
        }
    }
    return (u16)n;
}

// ScrCmd_GetBattleHallTotalSinglesRecord
u16 PlatHall_TotalSinglesRecord(void *save) {
    u32 species, total = 0;

    for (species = 0; species < NATIONAL_DEX_COUNT; species++) {
        total += PlatHall_GetRecordForSpecies(save, PLAT_HALL_SINGLE, (u16)species);
    }
    return (u16)(total > 10000 ? 10000 : total);
}

#endif
