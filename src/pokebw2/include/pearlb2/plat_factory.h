#ifndef POKEBW2_PEARLB2_PLAT_FACTORY_H
#define POKEBW2_PEARLB2_PLAT_FACTORY_H

// Platinum's Battle Factory (PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Factory"; plat-factory 2026-11-07).
//
// Two parts:
// - The rules (src/pearlb2/plat_factory/factory_rules.c): Platinum's own, function for function (pokeplatinum
//   src/overlay104/battle_factory.c, battle_factory_helpers.c, frontier_opponents.c, frscrcmd_battle_factory.c). They need
//   nothing of Black 2: the sets, the species' abilities and types and the records come through the calls below, and the
//   random numbers are Platinum's LCRNG on the challenge's own state. The host harness (b2tools/platinum_factory_host)
//   compiles this file beside Platinum's C and checks both give the same for the same random numbers.
// - The game side (src/pearlb2/plat_factory/factory.c, overlay 378): the Frontier ops 0x20-0x3f (the Factory's row of
//   sub-command 0x93), the rental and swap screens (Black 2's battle-entry party screen), the battle (a Trial House
//   battle with the rentals), the save.

#include "types.h"

#define PLATFACTORY_BATTLES_PER_ROUND 7
#define PLATFACTORY_STREAK_SILVER 21
#define PLATFACTORY_STREAK_GOLD 49
#define PLATFACTORY_ROUNDS (PLATFACTORY_STREAK_GOLD / PLATFACTORY_BATTLES_PER_ROUND + 1)
#define PLATFACTORY_RENTALS 6
#define PLATFACTORY_PARTY_SOLO 3
#define PLATFACTORY_PARTY_MULTI 2
#define PLATFACTORY_MAX_PARTY 4
#define PLATFACTORY_TRAINERS (PLATFACTORY_BATTLES_PER_ROUND * 2)
#define PLATFACTORY_TYPES 18                // Platinum's type count (with its Mystery type); Black 2 has 17
#define PLATFACTORY_NO_TYPE 0xff

// Platinum's Frontier Trainers (res/trainers/frontier/frontier_trainers.order, from 0)
#define PLATFACTORY_THORTON_SILVER 309
#define PLATFACTORY_THORTON_GOLD 310

// Platinum's challenge types
enum {
    PLATFACTORY_SINGLE,
    PLATFACTORY_DOUBLE,
    PLATFACTORY_MULTI,
    PLATFACTORY_MULTI_WFC,
};

// Platinum's BattleFactoryFunction (include/constants/battle_factory_functions.h): CallBattleFactoryFunction's fn
enum {
    PLATFACTORY_FN_UNK_0,
    PLATFACTORY_FN_SET_IS_OPEN_LEVEL,
    PLATFACTORY_FN_SET_CHALLENGE_TYPE,
    PLATFACTORY_FN_GET_SELECTED_APP_SLOT,
    PLATFACTORY_FN_GET_CURRENT_STREAK,
    PLATFACTORY_FN_INCREMENT_CURRENT_STREAK,
    PLATFACTORY_FN_UNK_6,
    PLATFACTORY_FN_RESET_SYSTEM,
    PLATFACTORY_FN_UNK_8,
    PLATFACTORY_FN_HAS_SAVED,
    PLATFACTORY_FN_QUICKSAVE,
    PLATFACTORY_FN_UNK_11,
    PLATFACTORY_FN_UNK_12,
    PLATFACTORY_FN_UNK_13,
    PLATFACTORY_FN_INCREMENT_CURRENT_BATTLE,
    PLATFACTORY_FN_GET_MONS_SPECIES,
    PLATFACTORY_FN_GET_MONS_MOVE,
    PLATFACTORY_FN_GET_MONS_TYPE,
    PLATFACTORY_FN_GET_COMMON_TYPE,
    PLATFACTORY_FN_GET_CURRENT_ROUND,
    PLATFACTORY_FN_GET_OPPONENT_OBJECT_ID,
    PLATFACTORY_FN_SAVE_ON_LOSS,
    PLATFACTORY_FN_SAVE_ON_COMPLETING_ROUND,
    PLATFACTORY_FN_GET_CURRENT_BATTLE,
    PLATFACTORY_FN_UNK_24,
    PLATFACTORY_FN_UNK_25,
    PLATFACTORY_FN_UNK_26,
    PLATFACTORY_FN_INIT_COMM_MANAGER,
    PLATFACTORY_FN_IS_MULTIPLAYER_CHALLENGE,
    PLATFACTORY_FN_GET_CHALLENGE_TYPE,
    PLATFACTORY_FN_UPDATE_BACKGROUND,
    PLATFACTORY_FN_START_CORRIDOR_ANIMATION,
    PLATFACTORY_FN_STOP_CORRIDOR_ANIMATION,
    PLATFACTORY_FN_LOAD_TRAINERS,
    PLATFACTORY_FN_SET_RENTED_MONS_IN_STRING,
    PLATFACTORY_FN_GET_EARNED_BP,
    PLATFACTORY_FN_INCREMENT_TRADE_COUNT,
    PLATFACTORY_FN_GET_NEXT_BATTLE_TYPE,
    PLATFACTORY_FN_UPDATE_PARTNERS_PARTY,
    PLATFACTORY_FN_CREATE_OPPONENT_MONS,
    PLATFACTORY_FN_CREATE_INITIAL_PARTY,
    PLATFACTORY_FN_CHECK_SEEN_HEAD_INTRO,
    PLATFACTORY_FN_COUNT,
};

// FRONTIER_NEXT_BATTLE_*
enum {
    PLATFACTORY_NEXT_NORMAL,
    PLATFACTORY_NEXT_SILVER,
    PLATFACTORY_NEXT_GOLD,
};

// A set of the Frontier's Pokémon file (Platinum's FrontierPokemonBase, pl_btdpm; here the Battle Subway's set arc,
// a/2/1/1, whose files 0-950 are Platinum's: patches/battle_tower.py)
typedef struct {
    u16 species;
    u16 moves[4];
    u8 evFlags;
    u8 nature;
    u16 item;
    u16 form;
} PlatFactorySet;

// A Pokémon made from a set (Platinum's FrontierPokemon, the fields the Factory reads): its party Pokémon is made from this
// at the challenge's level (factory.c: Black 2's BSubwayPokemon, BtlInst_MakeParty)
typedef struct {
    u16 species;
    u8 form;
    u8 happiness;
    u16 item;
    u16 ability;
    u16 moves[4];
    u32 otID;
    u32 personality;
    u8 ivs;
    u8 nature;
    u8 evs[6];
} PlatFactoryMon;

// Platinum's BattleFactorySave (include/battle_factory_save.h), what a saved challenge keeps; at the start of the core
// save's challenge area (PearlB2FrontierSave.challenge)
typedef struct {
    u8 isOpenLevel : 1;
    u8 challengeType : 3;
    u8 didSave : 1;
    u8 currentBattleNum;
    u16 unused2;
    u16 trainerIDs[PLATFACTORY_TRAINERS];
    u16 playerPartySets[PLATFACTORY_MAX_PARTY];
    u8 playerIVs[PLATFACTORY_MAX_PARTY];
    u32 playerPersonality[PLATFACTORY_MAX_PARTY];
    u16 opponentPartySets[PLATFACTORY_MAX_PARTY];
    u8 opponentIVs[PLATFACTORY_MAX_PARTY];
    u32 opponentPersonality[PLATFACTORY_MAX_PARTY];
} PlatFactorySave;

// The records the Factory reads and writes: Platinum's BattleFrontierStats.soloStats by its ids (the core's
// PearlB2FrontierSave.stats) and BattleFactoryStreakFlags.streakActiveFlags (PearlB2FrontierSave.streakFlags[0])
typedef struct {
    u16 *stats;
    u8 *streakFlags;
} PlatFactoryRecords;

// Platinum's BattleFactory, the challenge as it runs (the fields the rules use; the link-only ones left out). The parties
// are the Pokémon as made (Platinum keeps Pokemon structs made from them)
typedef struct {
    u32 rng;                                // Platinum's LCRNG state, the challenge's own
    u8 challengeType;
    u8 isOpenLevel;
    u8 currentBattle;
    u8 saveStreak;
    u8 seenFactoryHeadIntro;
    u8 wonBattle;
    u8 playerCount;
    u8 opponentCount;
    u16 tradeCount;
    u16 currentStreak;
    u16 currentRound;
    u16 unused2;
    u16 trainerIDs[PLATFACTORY_TRAINERS];
    u16 initialRentalSetIDs[PLATFACTORY_RENTALS];
    u8 initialRentalIVs[PLATFACTORY_RENTALS];
    u32 initialRentalPersonalities[PLATFACTORY_RENTALS];
    PlatFactoryMon initialRentalMons[PLATFACTORY_RENTALS];
    u16 opponentMonSetIDs[PLATFACTORY_MAX_PARTY];
    u8 opponentMonIVs[PLATFACTORY_MAX_PARTY];
    u32 opponentMonPersonalities[PLATFACTORY_MAX_PARTY];
    PlatFactoryMon opponentMons[PLATFACTORY_MAX_PARTY];
    PlatFactoryMon playersParty[PLATFACTORY_RENTALS];
    PlatFactoryMon opponentsParty[PLATFACTORY_MAX_PARTY];
    u16 selectedAppSlots[6];
    u16 playerMonSetIDs[PLATFACTORY_RENTALS];
} PlatFactory;

// ---- the rules (factory_rules.c)
u16 PlatFactory_Random(PlatFactory *factory);
void PlatFactory_Init(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records, u16 resumingFromSave,
                      u8 challengeType, u8 isOpenLevel, u32 seed);
void PlatFactory_LoadTrainersAndRentalsForRound(PlatFactory *factory, PlatFactorySave *save, u16 resumingFromSave);
void PlatFactory_Save(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records, u8 saveType);
void PlatFactory_SaveOnLoss(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records);
void PlatFactory_SaveOnCompletingRound(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records);
void PlatFactory_AddSelectedRentalsToParty(PlatFactory *factory);
void PlatFactory_SetupNextOpponent(PlatFactory *factory);
BOOL PlatFactory_ApplyTrade(PlatFactory *factory);
void PlatFactory_SetupNextOpponentsParty(PlatFactory *factory);
void PlatFactory_CreateInitialRentalParty(PlatFactory *factory);
void PlatFactory_IncrementTradeCount(PlatFactory *factory);
u16 PlatFactory_GetEarnedBP(PlatFactory *factory);
u16 PlatFactory_GetCurrentRound(PlatFactory *factory);
u8 PlatFactory_GetPokemonLevel(PlatFactory *factory);
u8 PlatFactory_GetPlayerPartySize(u8 challengeType);
u8 PlatFactory_GetOpponentPartySize(u8 challengeType, BOOL includePartnersMons);
u16 PlatFactory_GetAIMask(PlatFactory *factory);
// Platinum's CallBattleFactoryFunction for the functions that only compute (the rest need the game: factory.c). Returns
// FALSE for a function this doesn't do
BOOL PlatFactory_Function(PlatFactory *factory, PlatFactorySave *save, PlatFactoryRecords *records, u8 fn, u8 arg1,
                          u8 arg2, u16 *result);
// Platinum's DeleteActiveBattleFactoryStreak (the lobby's field command, src/scrcmd_battle_factory.c)
void PlatFactory_DeleteActiveStreak(PlatFactoryRecords *records, u8 challengeType, u8 isOpenLevel);
// Platinum's BattleFrontierStats_GetFactory*Idx
u16 PlatFactory_LatestStreakStat(u8 isOpenLevel, u8 challengeType);
u16 PlatFactory_RecordStreakStat(u8 isOpenLevel, u8 challengeType);
u16 PlatFactory_LatestTradeCountStat(u8 isOpenLevel, u8 challengeType);
u16 PlatFactory_RecordTradeCountStat(u8 isOpenLevel, u8 challengeType);

// ---- the game side (factory.c, overlay 378; the resident PearlB2_Frontier_Factory loads it for one op and unloads it after)
#if !defined(PEARLB2_HOST)
#include "struct_decls.h"
extern u32 OVERLAY_378_ID[];
#define PLATFACTORY_OVERLAY_ID ((u32)OVERLAY_378_ID)
// The overlay's entry, and the resident side that loads it (src/pearlb2/resident/plat_frontier.c's Factory row)
BOOL PlatFactory_Op(VM *vm, FieldScriptEnv *env, u32 op);
BOOL PearlB2_Frontier_Factory(VM *vm, FieldScriptEnv *env, u32 op);
#endif

// The Factory's ops: the low five bits of the Frontier ops 0x20-0x3f (sub-command 0x93; pearl_story.inc pl_Factory*). Each
// argument is a value or a var. An op marked "event" runs a screen or the battle: the script goes on when it ends
enum {
    PLATFACTORY_OP_INIT,                // resuming, challenge type, open level: Platinum's InitBattleFactory
    PLATFACTORY_OP_LOAD_ROUND,          // resuming: BattleFactory_LoadTrainersForRound
    PLATFACTORY_OP_FUNCTION,            // fn, arg1, arg2, var: CallBattleFactoryFunction
    PLATFACTORY_OP_RENT_SCREEN,         // (event) the six rentals on Black 2's battle-entry party screen, three to pick
    PLATFACTORY_OP_RENT_RESULT,         // var: 1 three picked (their slots to selectedAppSlots), 0 the screen was left
    PLATFACTORY_OP_SWAP_SCREEN,         // stage (event): 0 the player's three, one to give; 1 the beaten opponent's three,
                                        // one to take (nothing when stage 0 gave none)
    PLATFACTORY_OP_SWAP_RESULT,         // stage: the pick into selectedAppSlots[stage], 0xff in [0] for none
    PLATFACTORY_OP_ADD_SELECTED,        // AddSelectedRentalsToParty
    PLATFACTORY_OP_SETUP_NEXT_OPPONENT, // BattleFactory_SetupNextOpponent
    PLATFACTORY_OP_APPLY_TRADE,         // BattleFactory_ApplyTrade
    PLATFACTORY_OP_SETUP_NEXT_PARTY,    // BattleFactory_SetupNextOpponentsParty
    PLATFACTORY_OP_START_BATTLE,        // (event) BattleFactory_StartBattle: Black 2's Trial House battle with the rentals
    PLATFACTORY_OP_CLEANUP_BATTLE,      // BattleFactory_CleanupBattle: the result kept, the battle's setup freed
    PLATFACTORY_OP_CHECK_WON,           // var: BattleFactory_CheckWonBattle
    PLATFACTORY_OP_TRAINER_INTRO,       // index, actor (event): BattleFactory_PrintTrainerIntro, in Black 2's balloon
    PLATFACTORY_OP_FREE,                // FreeBattleFactory
    PLATFACTORY_OP_DELETE_STREAK,       // challenge type, open level: the lobby's DeleteActiveBattleFactoryStreak
    PLATFACTORY_OP_COUNT,
};

// What the challenge keeps while it runs, in the core save's challenge area (PearlB2FrontierSave.challenge: RAM all the
// time, written by a save): Platinum's BattleFactorySave first, as Platinum's union has it, then the running challenge
typedef struct {
    PlatFactorySave save;
    PlatFactory factory;
    u8 picked[8];                       // the party screen's picks (slots from 1)
    u32 choice;
    u32 screenResult;
    void *screenParty;                  // the party the screen shows (freed by the result op)
    void *setup;                        // the battle's BtlSetup (freed by the cleanup op)
} PlatFactoryWork;

// Filled by the build (patches/platinum_factory.py) in the overlay's data: the regulations of the two screens (Black 2's
// regulation file of the Subway's single train, with the counts the Factory needs and no level rule or clause) and the
// Brain's battle song (0: the Trial House's)
typedef struct {
    u16 rentRegulation;
    u16 swapRegulation;
    u16 brainBgm;
    u16 padding;
} PlatFactoryTable;

// ---- what each side gives the rules (factory.c on the DS, the harness's sim.c on the host)
void PlatFactory_ReadSet(u16 setID, PlatFactorySet *set);
// The species' ability of slot 0 or 1 (0: none)
u16 PlatFactory_SpeciesAbility(u16 species, u32 slot);
// The species' two types (the same twice for one type), in the game's own numbering below PLATFACTORY_TYPES
void PlatFactory_SpeciesTypes(u16 species, u16 form, u8 *type1, u8 *type2);

#endif // POKEBW2_PEARLB2_PLAT_FACTORY_H
