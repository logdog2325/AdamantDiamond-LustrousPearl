#ifndef POKEBW2_PEARLB2_PLAT_HALL_H
#define POKEBW2_PEARLB2_PLAT_HALL_H

// Platinum's Battle Hall (plat-hall, 2026-11-07; PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Hall"): one Pokémon, the 17-type
// grid, a rank of 1-10 for each type, opponents drawn by type and rank, their level from the player's, the streak, BP, and Argenta,
// the Hall Matron, at the 50th and 170th battle of a Single streak.
// - src/pearlb2/plat_hall/hall_rules.c: the rules, Platinum's own (pokeplatinum src/overlay104/battle_hall.c,
//   battle_hall_helpers.c, battle_hall_save.c, frontier_opponents.c), written to run the same on the DS and in PearlB2's host
//   harness (b2tools/platinum_hall_host: the same draws as Platinum's C for the same random numbers).
// - src/pearlb2/plat_hall/hall_field.c: the Frontier ops of the Hall (sub-command 0x93, ops 0x40-0x5f), the battle, the type list.
// - src/pearlb2/resident/plat_hall_ext.c: the core's row for the Hall (plat_frontier.c sFacilityOps): loads the overlay, runs the
//   op, unloads it; keeps the battle's setup between the start and the cleanup.
// The code is its own overlay (PLATHALL_OVERLAY_ID, at Pal Park's address, as plat-tutors' 376: loaded by the op, unloaded before
// it returns), so nothing of it stays in memory between ops: the challenge's work is in the Frontier's save area (the core's
// challenge union) and its tables are gPlatHallTable, in the overlay's .data, which only a Platinum build fills
// (b2tools/patches/platinum_hall.py, from the dump; empty, every op answers 0 and the battle doesn't start).

#include "types.h"
#include "struct_decls.h"

// plat-hall: the Hall's overlay (decomp tools/pearlb2/link_overlays.py PLATHALL; 378 is left for plat-factory)
extern u32 OVERLAY_379_ID[];
#define PLATHALL_OVERLAY_ID ((u32)OVERLAY_379_ID)

#define PLAT_HALL_BATTLES_PER_ROUND 10  // HALL_BATTLES_PER_ROUND
#define PLAT_HALL_STREAK_SILVER 50      // HALL_STREAK_SILVER_BATTLE: Argenta, Silver Print
#define PLAT_HALL_STREAK_GOLD 170       // HALL_STREAK_GOLD_BATTLE: Argenta, Gold Print
#define PLAT_HALL_MAX_ROUNDS 18         // HALL_MAX_DISTINCT_ROUNDS
#define PLAT_HALL_MAX_RANK 10           // HALL_MAX_TYPE_RANK
#define PLAT_HALL_TYPES 18              // NUM_POKEMON_TYPES (Platinum's 17 and the Mystery type)
#define PLAT_HALL_GRID_TYPES 17         // the grid's types (its cells 0-16)
#define PLAT_HALL_GRID_CELLS 20         // sBattleHallAppGridOrder: 17 types, two summary cells, the Mystery (Argenta's) cell
#define PLAT_HALL_MON_SUMMARY 0xfe      // BATTLE_HALL_MON_SUMMARY
#define PLAT_HALL_TYPE_MYSTERY 9        // Platinum's TYPE_MYSTERY
#define PLAT_HALL_SETS 478              // battle/b_pl_stage/pl_bsdpm.narc (set 0 is empty)
#define PLAT_HALL_OPPONENTS 477         // sBattleHallPotentialOpponents: set n + 1's species
#define PLAT_HALL_TRAINER_CLASSES 300   // sFrontierTrainerClasses: Frontier Trainers 0-299
#define PLAT_HALL_ARGENTA_SILVER 307    // FRONTIER_TRAINER_HALL_MATRON_ARGENTA_SILVER
#define PLAT_HALL_ARGENTA_GOLD 308
#define PLAT_HALL_STAT_MAX 9999

#define PLAT_HALL_MAGIC 0x4c4c4148      // 'HALL': gPlatHallTable filled
#define PLAT_HALL_WORK_MAGIC 0x4b524f57 // 'WORK': the challenge's work set up by the init op

enum {                                  // FRONTIER_CHALLENGE_*: the wireless and Wi-Fi Multi are closed here
    PLAT_HALL_SINGLE,
    PLAT_HALL_DOUBLE,
    PLAT_HALL_MULTI,
    PLAT_HALL_MULTI_WFC,
};

enum {                                  // FRONTIER_NEXT_BATTLE_*
    PLAT_HALL_NEXT_NORMAL,
    PLAT_HALL_NEXT_SILVER,
    PLAT_HALL_NEXT_GOLD,
};

// Platinum's AI flags (generated/ai_flags.txt, a mask): the Hall's three. Black 2's first three trainer AI bits are the same
// three (basic, the attack's evaluation, expert)
#define PLAT_HALL_AI_BASIC 0x1
#define PLAT_HALL_AI_EVAL_ATTACK 0x2
#define PLAT_HALL_AI_EXPERT 0x4

// Platinum's BattleFrontierStats ids of the Hall (include/constants/battle_frontier_stats.h), by challenge type: current streak,
// latest streak, latest species, then nine rank pairs (two types a stat: the low nibble the even type)
#define PLAT_HALL_STAT_SINGLE 34        // STAT_HALL_CURRENT_STREAK_SINGLE
#define PLAT_HALL_STAT_STRIDE 12        // .. _DOUBLE 46, _MULTI 58
#define PLAT_HALL_STAT_CURRENT 0
#define PLAT_HALL_STAT_LATEST 1
#define PLAT_HALL_STAT_SPECIES 2
#define PLAT_HALL_STAT_RANKS 3
#define PLAT_HALL_WIN_SPECIES 495       // MAX_SPECIES (SPECIES_BAD_EGG): the win records' row length (BattleHallWinRecords)

// One set of pl_bsdpm (Platinum's FrontierPokemonBase)
typedef struct {
    u16 species;
    u16 moves[4];
    u8 evFlags;
    u8 nature;
    u16 item;
    u16 form;
} PlatHallSet;

// gPlatHallTable (b2tools/platinum_hall_data.py table(): every table found in Platinum's dump by its bytes)
typedef struct {
    u32 magic;                                              // PLAT_HALL_MAGIC; 0: not filled (Pearl, Diamond)
    u16 setCount;
    u16 opponentCount;
    u16 trainerClassCount;
    u16 padding;
    PlatHallSet sets[PLAT_HALL_SETS];
    u8 setAbilities[PLAT_HALL_SETS][2];                     // Platinum's abilities 1 and 2 of the set's species and form
    u16 opponents[PLAT_HALL_OPPONENTS];                     // sBattleHallPotentialOpponents
    u8 opponentTypes[PLAT_HALL_OPPONENTS][2];               // sBattleHallPotentialOpponentTypes (Platinum's type ids)
    u8 trainerClasses[PLAT_HALL_TRAINER_CLASSES];           // sFrontierTrainerClasses (Platinum's class ids)
    u8 classesByRank[PLAT_HALL_MAX_RANK][8];                // sHallTrainerClassesByRank
    u8 classesByType[PLAT_HALL_TYPES][4];                   // sHallTrainerClassesBySelectedType, by grid cell
    u8 nameFlags[PLAT_HALL_TRAINER_CLASSES];                // PLAT_HALL_NAME_*: the AI test's misread (hall_rules.c ArgentaProbe)
    u16 brainBgm;                                           // Argenta's battle song (SEQ_PL_BA_BRAIN) once installed; 0: Black 2's
    u16 brainWinBgm;                                        // her victory song (SEQ_PL_WINBRAIN)
} PlatHallTable;

#define PLAT_HALL_NAME_FIRST_IJ 0x1     // the Trainer's name starts with I or J (Gen 4 codes 307, 308: Argenta's ids)
#define PLAT_HALL_NAME_FIFTH_IJ 0x2     // its fifth character is I or J

// Platinum's BattleHallSave: the challenge saved part-way
typedef struct {
    u8 challengeType : 3;
    u8 didSave : 1;
    u8 currentBattleNum;
    u8 partySlots[2];
    u16 trainerIDs[PLAT_HALL_BATTLES_PER_ROUND * 2];
    u16 monIndices[PLAT_HALL_BATTLES_PER_ROUND * 2];
} PlatHallSave;

// An opponent's Pokémon as Platinum's FrontierPokemon_Init and the Hall make it (frontier_opponents.c, battle_hall_helpers.c)
typedef struct {
    u16 species;
    u16 form;
    u16 item;
    u16 moves[4];
    u32 otID;
    u32 personality;
    u8 ivs;                                                 // every stat's
    u8 evs[6];
    u8 friendship;
    u8 ability;                                             // after the Hall's personality change (Pokemon_CalcAbility)
    u8 nature;                                              // personality % 25
    u8 language;
    u8 padding;
} PlatHallMon;

// The challenge's work: Platinum's BattleHall struct (overlay104/battle_hall.h), what its rules use, plus the saved part and the
// random state. It lives in the Frontier's save area (the core's challenge union), so it survives the overlay's unloading and
// the warps between the scenes' rooms; Platinum's own resume after a reset reads only `save` and the records, as Platinum's does
typedef struct {
    u32 magic;                                              // PLAT_HALL_WORK_MAGIC
    u32 lcrng;                                              // Platinum's LCRNG (math_util.c LCRNG_Next) for this challenge
    u8 challengeType;
    u8 currentBattle;
    u8 saveStreak;
    u8 opponentsLevel;
    u16 currentStreak;
    u16 currentRound;
    s32 playerLevelSqrt;                                    // fx32
    s32 wonBattle;
    u16 trainerIDs[PLAT_HALL_BATTLES_PER_ROUND * 2];
    u16 monIndices[PLAT_HALL_BATTLES_PER_ROUND * 2];
    u8 partySlots[2];
    u16 heldItems[2];
    u16 selectedTypeIdx2;
    u8 selectedType;
    u8 selectedTypeIdx;
    u8 typeRanks[4][9];
    u16 levels[2];                                          // the entered Pokémon's levels (the party's, read at each op)
    u16 species;                                            // the first entered Pokémon's species
    u16 padding;
    PlatHallMon mons[2];                                    // the next battle's opponents (Platinum's opponentMons[offset ..])
    PlatHallSave save;
} PlatHallWork;

// The save and the records, through the core (src/pearlb2/resident/plat_frontier.c); the harness gives its own
u16 PlatHall_GetStat(void *save, u32 stat);
void PlatHall_SetStat(void *save, u32 stat, u16 value);
u32 PlatHall_GetStreakFlag(void *save, u32 challengeType);
void PlatHall_SetStreakFlag(void *save, u32 challengeType, u32 value);
// Platinum's BattleHallWinRecords: each species' best streak, a row of PLAT_HALL_WIN_SPECIES u16 for Single and one for Double (the
// Multi is closed). NULL: none loaded (nothing is kept, the records count 0). On the DS (plat-frontier-rooms, hall_field.c) they
// are in an extra save block, as Platinum keeps them (battle_hall_win_records.c): loaded for the ops that need them, written
// with the whole save when one rises
u16 *PlatHall_WinRecords(void *save);

// (plat-frontier-rooms) The win records' save: Black 2's extra save block 4, the C-Gear's downloaded skin (0x2600 B; nothing that
// can run in Sinnoh reads or writes it: PearlB2's notes/DATA.md registry), its first 1,984 B. Without the magic (old saves, new
// games, a cleared block) it is set up empty on first use
#define PLAT_HALL_WIN_MAGIC 0x4E495748          // 'HWIN'
#define PLAT_HALL_WIN_EXTRA_BLOCK 4             // SAVE_EXTRA_ID_CGEAR_PICTURE
#define PLAT_HALL_WIN_EXTRA_AREA 0x2800         // its area in the save (save_table.c sv_extra_blk_data), as c_gear_sw.c loads it
#define PLAT_HALL_WIN_EXTRA_SIZE 0x2600         // its block (CGearPictureSave_GetSize)

typedef struct {
    u32 magic;                                          // PLAT_HALL_WIN_MAGIC
    u16 records[2 * PLAT_HALL_WIN_SPECIES];             // Single, then Double: PlatHall_WinRecords
} PlatHallWinSave;

// hall_rules.c: Platinum's rules (the names are Platinum's, with PlatHall_ for BattleHall_)
u16 PlatHall_Random(PlatHallWork *w);
u8 PlatHall_GetRankOfType(u8 idx, const u8 *typeRanks);
void PlatHall_SetRankOfType(u8 idx, u8 *typeRanks, u8 value);
void PlatHall_ResetRankOfAllTypes(u8 *typeRanks);
void PlatHall_Init(PlatHallWork *w, void *save, u16 resuming, u8 challengeType, u8 slot1, u8 slot2);
void PlatHall_SetupNextOpponent(PlatHallWork *w, const PlatHallTable *t);
void PlatHall_MakeOpponents(PlatHallWork *w, const PlatHallTable *t);
u16 PlatHall_CalcOpponentsLevel(PlatHallWork *w);
u16 PlatHall_GetOpponentLevel(PlatHallWork *w);
u16 PlatHall_GetAIMask(PlatHallWork *w, const PlatHallTable *t, u8 rank);
u8 PlatHall_GetBattleRank(PlatHallWork *w);
u16 PlatHall_GetEarnedBP(PlatHallWork *w);
void PlatHall_CapTypeRanks(PlatHallWork *w);
void PlatHall_CalcPlayerLevelSqrt(PlatHallWork *w);
void PlatHall_SetSelectedCell(PlatHallWork *w, u16 cell);
u8 PlatHall_CursorPosToType(u8 cell);
u16 PlatHall_GetNextBattleType(PlatHallWork *w);
u8 PlatHall_GetHallMatronTypeRank(PlatHallWork *w);
u16 PlatHall_GetHighestLevelInParty(PlatHallWork *w);
u8 PlatHall_GetPlayerPartySize(u8 challengeType);
void PlatHall_Save(PlatHallWork *w, void *save, u8 saveType);
void PlatHall_SaveOnLoss(PlatHallWork *w, void *save);
void PlatHall_SaveOnCompletingRound(PlatHallWork *w, void *save);
void PlatHall_IncrementRankOfBeatenType(PlatHallWork *w);
void PlatHall_ClearActiveStreak(void *save, u8 challengeType);
u32 PlatHall_TypeCellCheck(PlatHallWork *w, u16 cell);
u32 PlatHall_StatIndex(u8 challengeType, u32 which);
u16 PlatHall_UpdateWinRecord(PlatHallWork *w, void *save);
u16 PlatHall_GetRecordForSpecies(void *save, u8 challengeType, u16 species);
u16 PlatHall_CountSpeciesWithRecords(void *save);
u16 PlatHall_TotalSinglesRecord(void *save);

// The Hall's Frontier ops (sub-command 0x93, op byte 0x40 + these; macros in PearlB2's src/include/pearl_story.inc block
// "plat-hall"). Arguments: a value or a var each, read as the other sub-commands' are
enum {
    PLATHALL_OP_INIT,               // resuming, challenge type, slot 1, slot 2: InitBattleHall
    PLATHALL_OP_FUNC,               // function, arg 1, arg 2, var: CallBattleHallFunction (BH_FUNC_*)
    PLATHALL_OP_SETUP_NEXT,         // BattleHall_SetupNextOpponent
    PLATHALL_OP_FREE,               // FreeBattleHall: the work's magic cleared
    PLATHALL_OP_START_BATTLE,       // BattleHall_StartBattle: the battle (the script waits)
    PLATHALL_OP_CLEANUP_BATTLE,     // BattleHall_CleanupBattle: won or not, the setup freed
    PLATHALL_OP_CHECK_WON,          // var: BattleHall_CheckWonBattle
    PLATHALL_OP_WIN_RECORD,         // var: BattleHall_UpdateWinRecord (1: the species' record changed, and the game was saved)
    PLATHALL_OP_TRAINER_INTRO,      // trainer slot, person: the opponent's line in a balloon (PrintTrainerIntro)
    PLATHALL_OP_TYPE_LIST,          // the type grid's 17 types and the summary row into the script's list menu (OpenBattleHallApp)
    PLATHALL_OP_TYPE_CHECK,         // cell, var: 0 the cell can be picked, 1 it can't (a full rank or the Mystery cell), 2 the
                                    // Hall Matron comes next (Platinum's app: the pick is kept, Argenta's message, then her cell)
    PLATHALL_OP_TYPE_WORDS,         // cell, type word, rank word: the type's name and its rank as the grid shows it (stored + 1)
    PLATHALL_OP_SET_CELL,           // cell: the app's result (BattleHall_GetTypeSelectionAppResult)
    PLATHALL_OP_LOBBY,              // function, arg, var: CallBattleHallLobbyFunction (BH_LOBBY_FUNC_*; 4, the party screen, is
                                    // the Tower's: Black 2's Subway select)
    PLATHALL_OP_RECORDS,            // what, var: 0 GetNumSpeciesWithBattleHallRecords, 1 GetBattleHallTotalSinglesRecord, 2
                                    // CheckIfBattleHallStreakIs50
    PLATHALL_OP_RECORD_LIST,        // (plat-fix2) type, letter group (0 ABC .. 8 YZ): the records machine's species list
                                    // (ShowBattleHallRecordMonSelectionMenu): the species of the group with a record of the
                                    // type, in Platinum's order, into the list menu the script opened (the script adds EXIT)
    PLATHALL_OP_SPECIES_RECORD,     // (plat-fix2) type, species, latest var, record var: what the records screen shows for
                                    // the species (OpenFrontierRecordsApp's DisplayBattleHallRecord): its latest streak (0
                                    // unless it is the latest species of the type) and its record
    PLATHALL_OP_COUNT,
};

// hall_field.c (the overlay) and resident/plat_hall_ext.c
BOOL PlatHall_Op(VM *vm, FieldScriptEnv *env, u32 op);
BOOL PearlB2_Ext_Hall(VM *vm, FieldScriptEnv *env, u32 op);
BtlSetup *PearlB2_Hall_SetBattle(BtlSetup *setup);       // keeps the battle's setup; returns the one kept before
u16 PearlB2_Hall_TrainerClass(u16 trainerId);

#endif // POKEBW2_PEARLB2_PLAT_HALL_H
