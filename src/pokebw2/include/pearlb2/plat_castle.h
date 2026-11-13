#ifndef POKEBW2_PEARLB2_PLAT_CASTLE_H
#define POKEBW2_PEARLB2_PLAT_CASTLE_H

// Platinum's Battle Castle (plat-castle, 2026-11-07; PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Castle"): three Pokémon
// whose HP, PP, status and held items carry from battle to battle, Castle Points (CP) earned by how well each battle went and
// spent on healing, rented items, the opponent's information and rank ups, opponents by round, the streak, BP, and Darach,
// the Castle Valet, at the 21st and 49th battle of a Single streak.
// - src/pearlb2/plat_castle/castle_rules.c: the rules, Platinum's own (pokeplatinum src/overlay104/battle_castle.c,
//   battle_castle_helpers.c, frscrcmd_battle_castle.c, src/battle_castle_save.c, scrcmd_battle_castle.c, frontier_opponents.c,
//   and the purchases of the two screens: applications/frontier/battle_castle/self_app.c and opponent_app.c), with the same
//   random draws in the same order. It needs nothing of Black 2 (the calls below give it the party, the sets and the records),
//   so PearlB2's host harness (b2tools/platinum_castle_host) runs it as it is beside Platinum's own C.
// - src/pearlb2/plat_castle/castle_field.c: the Frontier ops of the Castle (sub-command 0x93, ops 0x60-0x7f), the castle's
//   party, the battle, the two screens as Black 2's party screen and script list menus.
// - src/pearlb2/resident/plat_castle_ext.c: the core's row for the Castle (plat_frontier.c sFacilityOps): loads the overlay,
//   runs the op, unloads it; keeps the battle's setup between the start and the cleanup; and the battle's end copies the
//   party as it left the battle into the setup for a Castle battle (PearlB2_Castle_StoreParties, from ov167 btl_main.c),
//   which Black 2 does only for wild and Trainer battles: so the HP and PP carry.
// The code is its own overlay (PLATCASTLE_OVERLAY_ID, at the gimmick overlays' address, as the Hall's 379: loaded by the op,
// unloaded before it returns). The challenge's work is in the Frontier's save area (the core's challenge union).

#include "types.h"

#define PLATCASTLE_BATTLES_PER_ROUND 7         // CASTLE_BATTLES_PER_ROUND
#define PLATCASTLE_STREAK_SILVER 21            // CASTLE_STREAK_SILVER_BATTLE: Darach, Silver Print
#define PLATCASTLE_STREAK_GOLD 49              // CASTLE_STREAK_GOLD_BATTLE: Darach, Gold Print
#define PLATCASTLE_ROUNDS 8                    // CASTLE_MAX_DISTINCT_ROUNDS
#define PLATCASTLE_PARTY_SOLO 3                // CASTLE_PARTY_SIZE_SOLO
#define PLATCASTLE_PARTY_MULTI 2               // CASTLE_PARTY_SIZE_MULTI
#define PLATCASTLE_MAX_PARTY 4                 // CASTLE_MAX_PARTY_SIZE
#define PLATCASTLE_TRAINERS (PLATCASTLE_BATTLES_PER_ROUND * 2)
#define PLATCASTLE_MAX_LEVEL 50                // CASTLE_MAX_LEVEL
#define PLATCASTLE_STAT_MAX 9999
#define PLATCASTLE_RANKS 3                     // BATTLE_CASTLE_NUM_RANK_TYPES

// Platinum's Frontier Trainers (res/trainers/frontier/frontier_trainers.order, from 0)
#define PLATCASTLE_DARACH_SILVER 313           // FRONTIER_TRAINER_CASTLE_VALET_DARACH_SILVER
#define PLATCASTLE_DARACH_GOLD 314

#define PLATCASTLE_WORK_MAGIC 0x54534143       // 'CAST': the challenge's work set up by the init op

enum {                                         // FRONTIER_CHALLENGE_*: the wireless and Wi-Fi Multi are closed here
    PLATCASTLE_SINGLE,
    PLATCASTLE_DOUBLE,
    PLATCASTLE_MULTI,
    PLATCASTLE_MULTI_WFC,
};

enum {                                         // FRONTIER_NEXT_BATTLE_*
    PLATCASTLE_NEXT_NORMAL,
    PLATCASTLE_NEXT_SILVER,
    PLATCASTLE_NEXT_GOLD,
};

enum {                                         // BATTLE_CASTLE_RANK_*
    PLATCASTLE_RANK_HEALING,
    PLATCASTLE_RANK_RENTALS,
    PLATCASTLE_RANK_INFO,                      // BATTLE_CASTLE_RANK_OPPONENT_SUMMARY
};

enum {                                         // LEVEL_ADJUSTMENT_*
    PLATCASTLE_LEVEL_NONE,
    PLATCASTLE_LEVEL_UP_5,
    PLATCASTLE_LEVEL_DOWN_5,
};

// Platinum's AI flags (generated/ai_flags.txt, a mask), the Castle's three; Black 2's first three trainer AI bits are the same
#define PLATCASTLE_AI_BASIC 0x1
#define PLATCASTLE_AI_EVAL_ATTACK 0x2
#define PLATCASTLE_AI_EXPERT 0x4

// Platinum's BattleFrontierStats ids of the Castle (include/constants/battle_frontier_stats.h), by challenge type (Single 70,
// Double 78, Multi 86): the record streak, the latest streak, the CP now, the CP spent, the CP of the record, the three ranks
#define PLATCASTLE_STAT_SINGLE 70              // STAT_CASTLE_RECORD_STREAK_SINGLE
#define PLATCASTLE_STAT_STRIDE 8
enum {
    PLATCASTLE_STAT_RECORD_STREAK,
    PLATCASTLE_STAT_LATEST_STREAK,
    PLATCASTLE_STAT_LATEST_CP,
    PLATCASTLE_STAT_SPENT_CP,
    PLATCASTLE_STAT_RECORD_CP,
    PLATCASTLE_STAT_RANK,                      // + the rank type
};
#define PLATCASTLE_STAT_WFC_STREAK_ACTIVE 108   // STAT_CASTLE_WFC_STREAK_ACTIVE (the Wi-Fi Multi's; closed)

// Platinum's BattleCastleFunction (include/constants/battle_castle_functions.h): CallBattleCastleFunction's fn
enum {
    PLATCASTLE_FN_UNK_0,
    PLATCASTLE_FN_UNK_1,
    PLATCASTLE_FN_SET_CHALLENGE_TYPE,
    PLATCASTLE_FN_GET_SELECTED_APP_SLOT,
    PLATCASTLE_FN_GET_CURRENT_STREAK,
    PLATCASTLE_FN_INCREMENT_CURRENT_STREAK,
    PLATCASTLE_FN_UNK_6,
    PLATCASTLE_FN_RESET_SYSTEM,
    PLATCASTLE_FN_UNK_8,
    PLATCASTLE_FN_HAS_SAVED,
    PLATCASTLE_FN_QUICKSAVE,
    PLATCASTLE_FN_UNK_11,
    PLATCASTLE_FN_UNK_12,
    PLATCASTLE_FN_UNK_13,
    PLATCASTLE_FN_INCREMENT_CURRENT_BATTLE,
    PLATCASTLE_FN_GET_MONS_SPECIES,
    PLATCASTLE_FN_GET_MONS_MOVE,
    PLATCASTLE_FN_GET_CHALLENGE_TYPE,
    PLATCASTLE_FN_RESTORE_HELD_ITEMS,
    PLATCASTLE_FN_GET_CURRENT_ROUND,
    PLATCASTLE_FN_GET_OPPONENT_OBJECT_ID,
    PLATCASTLE_FN_SAVE_ON_LOSS,
    PLATCASTLE_FN_SAVE_ON_COMPLETING_ROUND,
    PLATCASTLE_FN_GET_CURRENT_BATTLE,
    PLATCASTLE_FN_UNK_24,
    PLATCASTLE_FN_CHECK_IF_MON_FAINTED,
    PLATCASTLE_FN_UNK_26,
    PLATCASTLE_FN_GET_CP_FROM_BATTLE,
    PLATCASTLE_FN_PREP_FOR_NEXT_BATTLE,
    PLATCASTLE_FN_INIT_COMM_MANAGER,
    PLATCASTLE_FN_UNK_30,
    PLATCASTLE_FN_UNK_31,
    PLATCASTLE_FN_UNK_32,
    PLATCASTLE_FN_UNK_33,
    PLATCASTLE_FN_UNK_34,
    PLATCASTLE_FN_IS_MULTIPLAYER_CHALLENGE,
    PLATCASTLE_FN_UPDATE_EMBLEM_FRAME,
    PLATCASTLE_FN_LOAD_TRAINERS,
    PLATCASTLE_FN_GET_EARNED_BP,
    PLATCASTLE_FN_CHECK_HAVE_HEARD_DARACHS_INTRO,
    PLATCASTLE_FN_GET_NEXT_BATTLE_TYPE,
    PLATCASTLE_FN_CREATE_OPPONENT_MONS,
    PLATCASTLE_FN_SETUP_OPPONENTS_PARTY,
    PLATCASTLE_FN_CHECK_SEEN_VALET_INTRO,
    PLATCASTLE_FN_UPDATE_CP,
    PLATCASTLE_FN_COUNT,
};

// Platinum's BattleCastleLobbyFunction
enum {
    PLATCASTLE_LOBBY_CHECK_PARTY_ELIGIBLE,
    PLATCASTLE_LOBBY_CHECK_STREAK_ACTIVE,
    PLATCASTLE_LOBBY_UNUSED,
    PLATCASTLE_LOBBY_DELETE_ACTIVE_STREAK,
    PLATCASTLE_LOBBY_SELECT_POKEMON,
};

// A set of the Frontier's Pokémon file (Platinum's FrontierPokemonBase, pl_btdpm; on the DS the Battle Subway's set arc,
// a/2/1/1, whose files 0-950 are Platinum's: patches/battle_tower.py)
typedef struct {
    u16 species;
    u16 moves[4];
    u8 evFlags;
    u8 nature;
    u16 item;
    u16 form;
} PlatCastleSet;

// An opponent's Pokémon as Platinum's FrontierPokemon_Init makes it (the fields the Castle reads); the game makes the party
// Pokémon of it at Level 50 (castle_field.c: Black 2's BSubwayPokemon, BtlInst_MakeParty), five up or down by the level change
typedef struct {
    u16 species;
    u16 item;
    u16 moves[4];
    u32 otID;
    u32 personality;
    u8 form;
    u8 ivs;
    u8 evs[6];
    u8 ability;
    u8 friendship;
    u8 nature;                                 // personality % 25
    u8 padding;
} PlatCastleMon;

// Platinum's BattleCastleSave (include/battle_castle_save.h): the challenge saved part-way, at the start of the core save's
// challenge area as Platinum's union has it
typedef struct {
    u8 challengeType : 3;
    u8 didSave : 1;
    u8 currentBattleNum;
    u8 unused;
    u8 partySlots[3];
    u16 trainerIDs[PLATCASTLE_TRAINERS];
    u16 monHP[PLATCASTLE_MAX_PARTY];
    u8 monPP[PLATCASTLE_MAX_PARTY][4];
    u32 monStatus[PLATCASTLE_MAX_PARTY];
    u16 heldItems[PLATCASTLE_MAX_PARTY];
    u16 monSetIDs[PLATCASTLE_TRAINERS];
    u16 unused2;
} PlatCastleSave;

// Platinum's BattleCastle (overlay104/battle_castle.h), the challenge as it runs: the fields its rules use (the link's left
// out), the counts of its two parties (the parties themselves are the game's: castle_field.c keeps the player's three as
// Black 2's Pokémon; the opponents' are made from opponentMons when shown or fought), and the random state
typedef struct {
    u32 magic;                                 // PLATCASTLE_WORK_MAGIC
    u32 lcrng;                                 // Platinum's LCRNG (math_util.c LCRNG_Next) for this challenge
    u8 challengeType;
    u8 currentBattle;
    u8 monFainted;
    u8 seenCastleValetIntro;
    u16 currentStreak;
    u16 currentRound;
    s32 wonBattle;
    u16 initialCP;
    u16 newCP;
    u8 partySlots[3];
    u8 saveStreak;
    u8 playerCount;                            // Party_GetCurrentCount(playersParty)
    u8 opponentCount;                          // Party_GetCurrentCount(opponentsParty)
    u16 trainerIDs[PLATCASTLE_TRAINERS];
    u16 monSetIDs[PLATCASTLE_MAX_PARTY];
    u8 opponentMonIVs[PLATCASTLE_MAX_PARTY];
    u32 opponentMonPersonalities[PLATCASTLE_MAX_PARTY];
    PlatCastleMon opponentMons[PLATCASTLE_MAX_PARTY];
    u16 savedHeldItems[3];
    u8 appIdentityUnlocked[PLATCASTLE_MAX_PARTY];
    u8 levelAdjustments[PLATCASTLE_MAX_PARTY];
    u8 appStatsUnlocked[PLATCASTLE_MAX_PARTY];
    u8 appMovesUnlocked[PLATCASTLE_MAX_PARTY];
    u16 selectedAppSlot;                       // the self screen's last Pokémon (selectedAppSlots[0..5]: all the same)
    u16 startingPP[PLATCASTLE_MAX_PARTY][4];
    u8 unk_A18;                                // set by BC_FUNC_UNK_32 (the link's choice; unread in a solo challenge)
    u8 unk_A1B;
    u16 partnersCP;
} PlatCastle;

// The fields of the player's castle party the rules read and write (Platinum's MON_DATA_*)
enum {
    PLATCASTLE_MON_SPECIES,
    PLATCASTLE_MON_EXISTS,                     // MON_DATA_SPECIES_EXISTS
    PLATCASTLE_MON_LEVEL,
    PLATCASTLE_MON_HP,
    PLATCASTLE_MON_MAX_HP,
    PLATCASTLE_MON_STATUS,
    PLATCASTLE_MON_ITEM,
    PLATCASTLE_MON_MOVE1,
    PLATCASTLE_MON_PP1 = PLATCASTLE_MON_MOVE1 + 4,
    PLATCASTLE_MON_MAX_PP1 = PLATCASTLE_MON_PP1 + 4,
    PLATCASTLE_MON_FIELDS = PLATCASTLE_MON_MAX_PP1 + 4,
};

// ---- the purchases of Platinum's two screens (the self app: heal, rent, rank up; the opponent app: identity, level,
// stats, moves, rank up) and the scene's pass. PlatCastle_Ask makes the checks Platinum makes before it asks yes or no,
// PlatCastle_Buy the checks after the yes, and the purchase.
enum {
    PLATCASTLE_BUY_HEAL_HP,                    // the self app's heal menu (MENU_ENTRY_RESTORE_HP .. _ALL): 10, 8, 12 CP
    PLATCASTLE_BUY_HEAL_PP,
    PLATCASTLE_BUY_HEAL_ALL,
    PLATCASTLE_BUY_RANK_HEALING,               // its rank up: 100, 100 CP
    PLATCASTLE_BUY_BERRY,                      // the rental menu's lists: arg the list's row (sBerriesForRent, sItemsForRent)
    PLATCASTLE_BUY_ITEM,
    PLATCASTLE_BUY_RANK_RENTALS,               // its rank up: 100, 150 CP
    PLATCASTLE_BUY_IDENTIFY,                   // the opponent app: CHECK (1 CP)
    PLATCASTLE_BUY_LEVEL_UP,                   // LEVEL +5 (1 CP)
    PLATCASTLE_BUY_LEVEL_DOWN,                 // LEVEL -5 (15 CP)
    PLATCASTLE_BUY_STATS,                      // SUMMARY (2 CP)
    PLATCASTLE_BUY_MOVES,                      // MOVES (5 CP, information rank 2)
    PLATCASTLE_BUY_RANK_INFO,                  // its rank up: 50 CP
    PLATCASTLE_BUY_PASS,                       // the scene's PASS (50 CP), from the 4th round on, not before Darach
    PLATCASTLE_BUY_KINDS,
};
#define PLATCASTLE_BUY_SWITCH 0x100            // Buy's arg flag: the item switch was confirmed (the second yes)

enum {                                         // what Ask and Buy answer: the script shows Platinum's line for it
    PLATCASTLE_RESULT_DONE,                    // bought (Buy), or nothing to buy: the information is shown (Ask)
    PLATCASTLE_RESULT_CONFIRM,                 // Ask: the cost's question (its CP in the word), then yes or no
    PLATCASTLE_RESULT_NOT_ENOUGH_CP,
    PLATCASTLE_RESULT_RANK_TOO_LOW,
    PLATCASTLE_RESULT_NO_BENEFIT,              // the HP or PP are full
    PLATCASTLE_RESULT_HOLDING_ITEM,            // Buy: the Pokémon holds an item: "switch?", then Buy again with the flag
    PLATCASTLE_RESULT_MAX_RANK,                // the rank can't go higher: Platinum only buzzes
    PLATCASTLE_RESULT_KNOWN,                   // Ask: bought already (identity, stats, moves): shown at no cost
    PLATCASTLE_RESULT_CANT_GO_HIGHER,
    PLATCASTLE_RESULT_CANT_GO_LOWER,
};

// ---- the rules (castle_rules.c; the names are Platinum's, with PlatCastle_ for BattleCastle_)
u16 PlatCastle_Random(PlatCastle *castle);
u32 PlatCastle_StatIndex(u8 challengeType, u32 which);
void PlatCastle_Init(PlatCastle *castle, PlatCastleSave *save, void *records, u16 resuming, u8 challengeType, u8 slot1,
                     u8 slot2, u8 slot3);
void PlatCastle_LoadTrainersForRound(PlatCastle *castle, PlatCastleSave *save, u16 resuming);
void PlatCastle_Save(PlatCastle *castle, PlatCastleSave *save, void *records, u8 saveType);
void PlatCastle_SaveOnLoss(PlatCastle *castle, PlatCastleSave *save, void *records);
void PlatCastle_SaveOnCompletingRound(PlatCastle *castle, PlatCastleSave *save, void *records);
void PlatCastle_SetupFirstOpponentsParty(PlatCastle *castle);
void PlatCastle_SetupNextOpponentsParty(PlatCastle *castle);
void PlatCastle_SetupOpponentsParty(PlatCastle *castle);
void PlatCastle_CreateOpponentMons(PlatCastle *castle);
void PlatCastle_PrepForNextBattle(PlatCastle *castle);
int PlatCastle_CalcCPEarnedFromBattle(PlatCastle *castle);
void PlatCastle_ReceiveCastlePoints(void *records, u8 challengeType, int cp);
void PlatCastle_SpendCastlePoints(void *records, u8 challengeType, int cp);
u16 PlatCastle_GetCurrentCP(void *records, u8 challengeType);
u16 PlatCastle_GetEarnedBP(PlatCastle *castle);
u16 PlatCastle_GetCurrentRound(PlatCastle *castle);
u16 PlatCastle_GetAIMask(PlatCastle *castle);
u16 PlatCastle_GetNextBattleType(PlatCastle *castle);
u8 PlatCastle_GetPlayerPartySize(u8 challengeType, BOOL includePartnersMons);
u8 PlatCastle_GetOpponentPartySize(u8 challengeType, BOOL includeBothOpponents);
BOOL PlatCastle_IsMultiPlayerChallenge(u8 challengeType);
u8 PlatCastle_GetOpponentLevel(PlatCastle *castle, u8 slot);       // 50, five up or down by the level change
u8 PlatCastle_GetRank(void *records, u8 challengeType, u8 rankType);
void PlatCastle_ClearActiveStreak(void *records, u8 challengeType);
// CallBattleCastleFunction for the functions that only compute (the game's: castle_field.c). FALSE: not one of them
BOOL PlatCastle_Function(PlatCastle *castle, PlatCastleSave *save, void *records, u8 fn, u8 arg1, u8 arg2, u16 *result);
// The purchases
u32 PlatCastle_Ask(PlatCastle *castle, void *records, u32 kind, u8 slot, u16 arg, u16 *cost);
u32 PlatCastle_Buy(PlatCastle *castle, void *records, u32 kind, u8 slot, u16 arg);
u16 PlatCastle_RentalCount(void *records, u8 challengeType, BOOL items);   // the list's rows by the rental rank
u16 PlatCastle_RentalItem(BOOL items, u16 row);
u16 PlatCastle_RentalPrice(BOOL items, u16 row);

// ---- what each side gives the rules (castle_field.c on the DS, the harness's sim.c on the host)
// The records: Platinum's BattleFrontierStats soloStats by its ids, its BattleCastlePersistentSave
u16 PlatCastle_GetStat(void *records, u32 stat);
void PlatCastle_SetStat(void *records, u32 stat, u16 value);       // (at most 9999, as BattleFrontierSave_SetStat)
u32 PlatCastle_GetStreakFlag(void *records, u32 challengeType);
void PlatCastle_SetStreakFlag(void *records, u32 challengeType, u32 value);
u32 PlatCastle_GetHeardIntro(void *records);
void PlatCastle_SetHeardIntro(void *records);
// The player's castle party (Platinum's playersParty): empty at Init; a copy of the field party's Pokémon added at the end
u32 PlatCastle_FieldMonItem(PlatCastle *castle, u8 fieldSlot);
void PlatCastle_PartyAddFieldMon(PlatCastle *castle, u8 fieldSlot);
u32 PlatCastle_MonGet(PlatCastle *castle, u8 slot, u32 field);
void PlatCastle_MonSet(PlatCastle *castle, u8 slot, u32 field, u32 value);
void PlatCastle_MonSetLevel(PlatCastle *castle, u8 slot, u8 level);  // the experience of the level, its stats again
// The Frontier's Trainers and sets
void PlatCastle_ReadSet(u16 setID, PlatCastleSet *set);
u16 PlatCastle_TrainerSets(u16 trainerID, u16 *sets, u16 max);      // the Trainer's set ids, how many
u16 PlatCastle_SpeciesAbility(u16 species, u32 slot);               // the species' ability 1 or 2 (0: none)

// ---- the game side (castle_field.c, overlay 380; the resident PearlB2_Ext_Castle loads it for one op and unloads it after)
// gPlatCastleTable, in the overlay's .data: filled by PearlB2's b2tools/patches/platinum_castle.py in a Platinum build. Empty
// (Pearl, Diamond, a build without it), no challenge starts: every op answers 0
#define PLATCASTLE_TABLE_MAGIC 0x4c545343       // 'CSTL'
typedef struct {
    u32 magic;
    u16 pickRegulation;                         // a/1/0/6's file for the self screen: one of the castle's three, no level rule
    u16 entryRegulation[2];                     // the lobby's party screen: three (Single, Double), two (Multi); Black 2's
                                                // Subway regulation with no level rule, the same item allowed
    u16 brainBgm;                               // Darach's battle song (SEQ_PL_BA_BRAIN) once installed; 0: the Subway's
    u16 brainWinBgm;                            // his victory song (SEQ_PL_WINBRAIN)
} PlatCastleTable;
#if !defined(PEARLB2_HOST)
#include "struct_decls.h"
extern u32 OVERLAY_380_ID[];
#define PLATCASTLE_OVERLAY_ID ((u32)OVERLAY_380_ID)
BOOL PlatCastle_Op(VM *vm, FieldScriptEnv *env, u32 op);
BOOL PearlB2_Ext_Castle(VM *vm, FieldScriptEnv *env, u32 op);
BtlSetup *PearlB2_Castle_SetBattle(BtlSetup *setup);   // keeps the battle's setup; returns the one kept before
// ov167 btl_main.c's call of BtlMain_StorePartiesToSetup comes here (resident): the original, then, for the Castle's battle,
// the player's party as it left the battle into the setup (Black 2's own copy, which it makes only for wild and Trainer
// battles), without Black 2's restoring of held items: as Platinum, an item used up in a battle is gone
void PearlB2_Castle_StoreParties(BtlMainModule *mainModule);
#endif

// The Castle's Frontier ops: the low five bits of ops 0x60-0x7f (sub-command 0x93; pearl_story.inc pl_Castle*). Each argument
// is a value or a var. An op marked "event" runs a screen or the battle: the script goes on when it ends
enum {
    PLATCASTLE_OP_INIT,                 // resuming, challenge type, slot 1, slot 2, slot 3: InitBattleCastle
    PLATCASTLE_OP_LOAD_ROUND,           // resuming: LoadTrainersForRound
    PLATCASTLE_OP_FUNCTION,             // fn, arg1, arg2, var: CallBattleCastleFunction
    PLATCASTLE_OP_FREE,                 // FreeBattleCastle
    PLATCASTLE_OP_SETUP_FIRST,          // BattleCastle_SetupFirstOpponent
    PLATCASTLE_OP_SETUP_NEXT,           // BattleCastle_SetupNextOpponent
    PLATCASTLE_OP_START_BATTLE,         // (event) BattleCastle_StartBattle: Black 2's Subway battle with the castle's party
    PLATCASTLE_OP_CLEANUP_BATTLE,       // BattleCastle_CleanupBattle: the party back from the battle, won or not
    PLATCASTLE_OP_CHECK_WON,            // var: BattleCastle_CheckWonBattle
    PLATCASTLE_OP_TRAINER_WORD,         // word, slot, line: the opponent's line into a word (BattleCastle_PrintTrainerIntro)
    PLATCASTLE_OP_GET_CP,               // challenge type, var: GetCurrentCastlePoints
    PLATCASTLE_OP_SPEND_CP,             // challenge type, cp: SpendCastlePoints
    PLATCASTLE_OP_RECEIVE_CP,           // challenge type, cp: ReceiveCastlePoints
    PLATCASTLE_OP_LOBBY,                // fn, arg, var: CallBattleCastleLobbyFunction 0-3 (4, the party screen, is the Subway's
                                        // select: the translator's, as the Hall's and the Tower's)
    PLATCASTLE_OP_DELETE_STREAK,        // challenge type: DeleteActiveBattleCastleStreak
    PLATCASTLE_OP_SELF_SCREEN,          // (event) the castle's party on Black 2's battle-entry party screen: one to pick, or B
    PLATCASTLE_OP_SELF_PICK,            // var: the picked slot (0-2), 0xff for none (OpenBattleCastleSelfApp's Pokémon)
    PLATCASTLE_OP_ASK,                  // kind, slot, arg, var: PLATCASTLE_RESULT_*; the cost into word 0
    PLATCASTLE_OP_BUY,                  // kind, slot, arg, var: PLATCASTLE_RESULT_*; the result's words as Platinum's line has
                                        // them (0 the species, 1 the item, 5 the player)
    PLATCASTLE_OP_RENTAL_LIST,          // items (0 Berries, 1 items): the rows the rental rank allows, each with its CP, into
                                        // the script's list menu (its value the row)
    PLATCASTLE_OP_OPPONENT_LIST,        // unknown line: the opponent's Pokémon into the script's list menu (an unidentified
                                        // one as the script's line), the value its slot
    PLATCASTLE_OP_MON_WORDS,            // side (0 the player's, 1 the opponent's), slot, what: words of a Pokémon (what 0: the
                                        // species, level, HP, max HP in words 0-3; 1: the summary panel: item 0, nature 1,
                                        // ability 2, Attack 3, Defense 4, Sp. Atk 5, Sp. Def 6, Speed 7; 2: the moves panel:
                                        // the moves in words 0-3, their PP 4-7 and max PP 8-11)
    PLATCASTLE_OP_INFO,                 // what, slot, var: 0-2 a rank (healing, rentals, information), 3 identity bought,
                                        // 4 stats bought, 5 moves bought, 6 the level change, 7 the party's count
    PLATCASTLE_OP_CP_WORD,              // word: the player's CP now (the CP window's number)
    PLATCASTLE_OP_LOBBY_SELECT,         // challenge type (event): the lobby's BC_LOBBY_FUNC_SELECT_POKEMON, the field party on
                                        // Black 2's battle-entry party screen (three, two for a Multi; not the same species twice,
                                        // nor a Pokémon Platinum's Frontier bans)
    PLATCASTLE_OP_SELECTED_SLOTS,       // var, var, var: GetBattleCastleSelectedSlots (the slots picked; 0xff in the first for none)
    PLATCASTLE_OP_COUNT,
};

// What the challenge keeps while it runs, in the core save's challenge area (PearlB2FrontierSave.challenge): Platinum's
// BattleCastleSave first, as Platinum's union has it, then the running challenge and the castle's party (three Black 2 party
// Pokémon: Platinum keeps them on its heap for the length of the scenes; here they live through the overlay's unloading and the
// warps between the rooms)
#define PLATCASTLE_PKM_SIZE 220                // sizeof(PartyPkm)
typedef struct {
    PlatCastleSave save;
    PlatCastle castle;
    u32 party[PLATCASTLE_PARTY_SOLO][PLATCASTLE_PKM_SIZE / 4];
    u8 picked[8];                       // the party screen's picks (slots from 1)
    u32 choice;
    u32 screenResult;
    void *screenParty;                  // the party the screen shows (freed by the pick op)
} PlatCastleWork;

#endif // POKEBW2_PEARLB2_PLAT_CASTLE_H
