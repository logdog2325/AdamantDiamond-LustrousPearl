#ifndef POKEBW2_PEARLB2_PLAT_ARCADE_H
#define POKEBW2_PEARLB2_PLAT_ARCADE_H

// Platinum's Battle Arcade (plat-arcade, 2026-11-07; PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Arcade"): three Pokémon at
// Level 50 at most, the game board (a roulette of 16 panels drawn from 32 effects) before every battle, the effects on either
// party, the field or the board, opponents by round, the streak, BP, and Dahlia, the Arcade Star, at the 21st and 49th battle of
// a Single streak.
// - src/pearlb2/plat_arcade/arcade_rules.c: the rules, Platinum's own (pokeplatinum src/overlay104/battle_arcade.c,
//   battle_arcade_helpers.c, frscrcmd_battle_arcade.c, src/battle_arcade_save.c, scrcmd_battle_arcade.c, frontier_opponents.c,
//   and the board's draw, speed and stop: applications/frontier/battle_arcade/main.c), with the same random draws in the same
//   order. It needs nothing of Black 2 (the calls below give it the parties, the sets and the records), so PearlB2's host harness
//   (b2tools/platinum_arcade_host) runs it as it is beside Platinum's own C.
// - src/pearlb2/plat_arcade/arcade_field.c: the Frontier ops of the Arcade (sub-command 0x93, ops 0x80-0x9f), the Arcade's
//   party, the opponents, the battle, the board on the field (a window of the 16 panels and the cursor, an event at Platinum's
//   timing).
// - src/pearlb2/resident/plat_arcade_ext.c: the core's row for the Arcade (plat_frontier.c sFacilityOps): loads the overlay, runs
//   the op, unloads it (the board's op instead has Black 2's GameEvent_CreateOverlayDelegate load it for as long as the board
//   runs); the battle's start effect (Trick Room, from ov167's battle start) and both parties as they left a battle (the Castle's
//   hook, PearlB2_Castle_StoreParties, calls PearlB2_Arcade_StoreParties).
// The code is its own overlay (PLATARCADE_OVERLAY_ID, at the gimmick overlays' address, as the Hall's 379 and the Castle's 380).
// The challenge's work is in the Frontier's save area (the core's challenge union).

#include "types.h"

#define PLATARCADE_BATTLES_PER_ROUND 7         // ARCADE_BATTLES_PER_ROUND
#define PLATARCADE_STREAK_SILVER 21            // ARCADE_STREAK_SILVER_BATTLE: Dahlia, Silver Print
#define PLATARCADE_STREAK_GOLD 49              // ARCADE_STREAK_GOLD_BATTLE: Dahlia, Gold Print
#define PLATARCADE_ROUNDS 8                    // ARCADE_MAX_DISTINCT_ROUNDS
#define PLATARCADE_PARTY_SOLO 3                // ARCADE_PARTY_SIZE_SOLO
#define PLATARCADE_PARTY_MULTI 2               // ARCADE_PARTY_SIZE_MULTI
#define PLATARCADE_MAX_PARTY 4                 // ARCADE_MAX_PARTY_SIZE
#define PLATARCADE_TRAINERS (PLATARCADE_BATTLES_PER_ROUND * 2)
#define PLATARCADE_MAX_LEVEL 50                // ARCADE_MAX_LEVEL
#define PLATARCADE_STAT_MAX 9999

// Platinum's Frontier Trainers (res/trainers/frontier/frontier_trainers.order, from 0)
#define PLATARCADE_DAHLIA_SILVER 311           // FRONTIER_TRAINER_ARCADE_STAR_DAHLIA_SILVER
#define PLATARCADE_DAHLIA_GOLD 312

#define PLATARCADE_WORK_MAGIC 0x43524141       // 'AARC': the challenge's work set up by the init op

enum {                                         // FRONTIER_CHALLENGE_*: the wireless and Wi-Fi Multi are closed here
    PLATARCADE_SINGLE,
    PLATARCADE_DOUBLE,
    PLATARCADE_MULTI,
    PLATARCADE_MULTI_WFC,
};

enum {                                         // FRONTIER_NEXT_BATTLE_*
    PLATARCADE_NEXT_NORMAL,
    PLATARCADE_NEXT_SILVER,
    PLATARCADE_NEXT_GOLD,
};

// The board's 32 effects (constants/battle_frontier.h ARCADE_EFFECT_*), in four kinds: on the opponent's party (0-8), on the
// player's (9-17), on the field (18-23: the weather, the fog, Trick Room), the board and bonuses (24-31)
enum {
    PLATARCADE_EFFECT_LOWER_FOE_HP,
    PLATARCADE_EFFECT_POISON_FOE,
    PLATARCADE_EFFECT_PARALYZE_FOE,
    PLATARCADE_EFFECT_BURN_FOE,
    PLATARCADE_EFFECT_SLEEP_FOE,
    PLATARCADE_EFFECT_FREEZE_FOE,
    PLATARCADE_EFFECT_FOE_GET_BERRY,
    PLATARCADE_EFFECT_FOE_GET_ITEM,
    PLATARCADE_EFFECT_FOE_LEVEL_UP,
    PLATARCADE_EFFECT_LOWER_ALLY_HP,
    PLATARCADE_EFFECT_POISON_ALLY,
    PLATARCADE_EFFECT_PARALYZE_ALLY,
    PLATARCADE_EFFECT_BURN_ALLY,
    PLATARCADE_EFFECT_SLEEP_ALLY,
    PLATARCADE_EFFECT_FREEZE_ALLY,
    PLATARCADE_EFFECT_ALLY_GET_BERRY,
    PLATARCADE_EFFECT_ALLY_GET_ITEM,
    PLATARCADE_EFFECT_ALLY_LEVEL_UP,
    PLATARCADE_EFFECT_SUNNY_BATTLE,
    PLATARCADE_EFFECT_RAINY_BATTLE,
    PLATARCADE_EFFECT_SANDY_BATTLE,
    PLATARCADE_EFFECT_HAIL_BATTLE,
    PLATARCADE_EFFECT_FOGGY_BATTLE,
    PLATARCADE_EFFECT_TRICK_ROOM,
    PLATARCADE_EFFECT_SPEED_UP,
    PLATARCADE_EFFECT_SLOW_DOWN,
    PLATARCADE_EFFECT_RANDOMIZE_CURSOR,
    PLATARCADE_EFFECT_SWAP_MONS,
    PLATARCADE_EFFECT_GET_1_BP,
    PLATARCADE_EFFECT_NO_BATTLE,
    PLATARCADE_EFFECT_NO_EVENT,
    PLATARCADE_EFFECT_GET_3_BP,
    PLATARCADE_EFFECTS,
};

enum {                                         // ARCADE_EFFECT_CATEGORY_*
    PLATARCADE_CATEGORY_FOE,
    PLATARCADE_CATEGORY_ALLY,
    PLATARCADE_CATEGORY_ENV,
    PLATARCADE_CATEGORY_BONUS,
    PLATARCADE_CATEGORIES,
};

// The weather an effect sets (Platinum's OVERWORLD_WEATHER_*, which its battle starts with: constants/overworld_weather.h)
#define PLATARCADE_WEATHER_CLEAR 0
#define PLATARCADE_WEATHER_RAINING 2
#define PLATARCADE_WEATHER_SNOWING 5          // hail in battle
#define PLATARCADE_WEATHER_SANDSTORM 10
#define PLATARCADE_WEATHER_FOG 14
#define PLATARCADE_WEATHER_HARSH_SUN 1001     // OVERWORLD_WEATHER_HARSH_SUN
#define PLATARCADE_WEATHER_TRICK_ROOM 1002    // OVERWORLD_WEATHER_TRICK_ROOM

// Platinum's MON_CONDITION_* (the party's status): the sleep turns in the low three bits
#define PLATARCADE_STATUS_POISON (1 << 3)
#define PLATARCADE_STATUS_BURN (1 << 4)
#define PLATARCADE_STATUS_FREEZE (1 << 5)
#define PLATARCADE_STATUS_PARALYSIS (1 << 6)

// Platinum's AI flags (generated/ai_flags.txt, a mask), the Arcade's three; Black 2's first three trainer AI bits are the same
#define PLATARCADE_AI_BASIC 0x1
#define PLATARCADE_AI_EVAL_ATTACK 0x2
#define PLATARCADE_AI_EXPERT 0x4

// Platinum's BattleFrontierStats ids of the Arcade (include/constants/battle_frontier_stats.h), by challenge type: the record
// streak, the latest streak (Single 94, Double 96, Multi 98)
#define PLATARCADE_STAT_SINGLE 94              // STAT_ARCADE_RECORD_STREAK_SINGLE
#define PLATARCADE_STAT_STRIDE 2
enum {
    PLATARCADE_STAT_RECORD_STREAK,
    PLATARCADE_STAT_LATEST_STREAK,
};
#define PLATARCADE_STAT_WFC_STREAK_ACTIVE 110  // STAT_ARCADE_WFC_STREAK_ACTIVE (the Wi-Fi Multi's; closed)

// Platinum's BattleArcadeFunction (include/constants/battle_arcade_functions.h): CallBattleArcadeFunction's fn
enum {
    PLATARCADE_FN_UNK_0,
    PLATARCADE_FN_UNK_1,
    PLATARCADE_FN_SET_CHALLENGE_TYPE,
    PLATARCADE_FN_GET_APP_CURSOR_POS,
    PLATARCADE_FN_GET_CURRENT_STREAK,
    PLATARCADE_FN_INCREMENT_CURRENT_STREAK,
    PLATARCADE_FN_INIT_COMM_MANAGER,
    PLATARCADE_FN_RESET_SYSTEM,
    PLATARCADE_FN_UNK_8,
    PLATARCADE_FN_HAS_SAVED,
    PLATARCADE_FN_QUICKSAVE,
    PLATARCADE_FN_SET_EFFECT_BACKGROUND,
    PLATARCADE_FN_GET_FREE_BP,
    PLATARCADE_FN_UNK_13,
    PLATARCADE_FN_INCREMENT_CURRENT_BATTLE,
    PLATARCADE_FN_GET_HELD_ITEM,
    PLATARCADE_FN_GET_ACTIVE_EFFECT,
    PLATARCADE_FN_GET_CHALLENGE_TYPE,
    PLATARCADE_FN_RESTORE_HELD_ITEMS,
    PLATARCADE_FN_GET_CURRENT_ROUND,
    PLATARCADE_FN_GET_OPPONENT_OBJECT_ID,
    PLATARCADE_FN_SAVE_ON_LOSS,
    PLATARCADE_FN_SAVE_ON_COMPLETING_ROUND,
    PLATARCADE_FN_GET_CURRENT_BATTLE,
    PLATARCADE_FN_UNK_24,
    PLATARCADE_FN_SWAP_MON_SPRITES,
    PLATARCADE_FN_UNK_26,
    PLATARCADE_FN_UNK_27,
    PLATARCADE_FN_IS_MULTIPLAYER_CHALLENGE,
    PLATARCADE_FN_LOAD_MON_SPRITE_DATA,
    PLATARCADE_FN_UNLOAD_MON_SPRITE_DATA,
    PLATARCADE_FN_CREATE_MON_SPRITES,
    PLATARCADE_FN_DELETE_MON_SPRITES,
    PLATARCADE_FN_LOAD_ITEM_SPRITE_DATA,
    PLATARCADE_FN_UNLOAD_ITEM_SPRITE_DATA,
    PLATARCADE_FN_CREATE_ITEM_SPRITES,
    PLATARCADE_FN_DELETE_ITEM_SPRITES,
    PLATARCADE_FN_LOAD_NORMAL_BACKGROUND,
    PLATARCADE_FN_SET_NAME_OF_AFFECTED_TRAINER,
    PLATARCADE_FN_CREATE_EMITTER,
    PLATARCADE_FN_LOAD_TRAINERS,
    PLATARCADE_FN_SET_DRAW_FLAG_PLAYER_MON,
    PLATARCADE_FN_SET_DRAW_FLAG_OPPONENT_MON,
    PLATARCADE_FN_SET_PALETTE,
    PLATARCADE_FN_UNK_44,
    PLATARCADE_FN_GET_EARNED_BP,
    PLATARCADE_FN_DISABLE_BG2_LAYER,
    PLATARCADE_FN_CHECK_IMMUNE_TO_EFFECT,
    PLATARCADE_FN_GET_NEXT_BATTLE_TYPE,
    PLATARCADE_FN_CREATE_OPPONENT_MONS,
    PLATARCADE_FN_SETUP_OPPONENTS_PARTY,
    PLATARCADE_FN_CHECK_SEEN_STAR_INTRO,
    PLATARCADE_FN_CLEAR_MSGS_RECEIVED,
    PLATARCADE_FN_COUNT,
};

// Platinum's BattleArcadeLobbyFunction
enum {
    PLATARCADE_LOBBY_CHECK_PARTY_ELIGIBLE,
    PLATARCADE_LOBBY_CHECK_STREAK_ACTIVE,
    PLATARCADE_LOBBY_UNUSED,
    PLATARCADE_LOBBY_DELETE_ACTIVE_STREAK,
    PLATARCADE_LOBBY_SELECT_POKEMON,
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
} PlatArcadeSet;

// An opponent's Pokémon as Platinum's FrontierPokemon_Init makes it (the fields the Arcade reads); the game makes the party
// Pokémon of it at Level 50 (arcade_field.c: Black 2's BSubwayPokemon, BtlInst_MakeParty)
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
} PlatArcadeMon;

// Platinum's BattleArcadeSave (include/battle_arcade_save.h): the challenge saved part-way, at the start of the core save's
// challenge area as Platinum's union has it
typedef struct {
    u8 challengeType : 3;
    u8 didSave : 1;
    u8 cursorRandomized : 1;
    u8 currentBattle;
    u8 rouletteSpeed;
    u8 partySlots[3];
    u16 heldItems[4];
    u16 trainerIDs[PLATARCADE_TRAINERS];
    u16 monSetIDs[PLATARCADE_TRAINERS];
    u16 unused;
} PlatArcadeSave;

// Platinum's BattleArcade (overlay104/battle_arcade.h), the challenge as it runs: the fields its rules use (the link's and the
// sprites' left out), the counts of its two parties (the parties themselves are the game's: arcade_field.c keeps the player's
// three as Black 2's Pokémon, and the opponent's as their sets plus what the board changed), and the random state
typedef struct {
    u32 magic;                                 // PLATARCADE_WORK_MAGIC
    u32 lcrng;                                 // Platinum's LCRNG (math_util.c LCRNG_Next) for this challenge
    u8 challengeType;
    u8 currentBattle;
    u8 cursorRandomized;
    u8 activeEffect;                           // the board's last effect (PLATARCADE_EFFECTS: none yet)
    s32 weather;                               // the battle's weather (PLATARCADE_WEATHER_*)
    u16 currentStreak;
    u16 currentRound;
    u8 rouletteSpeed;                          // 0-7: sCursorMoveFrames' row
    u8 performance;                            // how well the last battle went (BattleArcade_GetPerformance)
    u8 seenArcadeStarIntro;
    u8 immuneToEffect;
    u16 randomIndex;                           // the board's random number: the sleep's and the freeze's first Pokémon, the
                                               // Berry's and the item's row
    u16 appCursorPos;                          // the board's last panel (StoreAppResults: appCursorPos[0..5], all the same)
    s32 wonBattle;
    u8 partySlots[3];
    u8 saveStreak;
    u8 playerCount;                            // Party_GetCurrentCount(playersParty)
    u8 opponentCount;                          // Party_GetCurrentCount(opponentsParty)
    u8 unk_A74;                                // BA_FUNC_UNK_24: the link partner retired (a solo challenge: 0)
    u8 padding;
    u16 trainerIDs[PLATARCADE_TRAINERS];
    u16 monHP[PLATARCADE_MAX_PARTY];           // the player's party's stats when the board opened (SetupBattleArcadeAppArgs;
    u16 monAtk[PLATARCADE_MAX_PARTY];          // Platinum's are u32): the cleanup puts them back
    u16 monDef[PLATARCADE_MAX_PARTY];
    u16 monSpeed[PLATARCADE_MAX_PARTY];
    u16 monSpAtk[PLATARCADE_MAX_PARTY];
    u16 monSpDef[PLATARCADE_MAX_PARTY];
    u16 monSetIDs[PLATARCADE_MAX_PARTY];
    u8 opponentMonIVs[PLATARCADE_MAX_PARTY];
    u32 opponentMonPersonalities[PLATARCADE_MAX_PARTY];
    PlatArcadeMon opponentMons[PLATARCADE_MAX_PARTY];
    u16 savedHeldItems[3];
    u16 padding2;
} PlatArcade;

// The game board (BattleArcadeApp, applications/frontier/battle_arcade/main.c): what decides its panels and where it stops
#define PLATARCADE_GRID 16                     // GRID_SIZE: 4 x 4 panels
#define PLATARCADE_ROULETTE_FRAMES 900         // the 30 seconds the cursor runs at most (30 frames a second)
typedef struct {
    u8 challengeType;
    u8 performance;
    u8 randomizeCursorMovement;
    u8 cursorPos;
    u8 cursorUpdateTimer;
    u8 categoryTier;
    u8 numAvailableEffects;
    u8 resultCursorPos;
    u16 startingCursorPos;
    u16 battleStreak;
    u16 round;
    u16 padding;
    s32 rouletteTimer;
    u8 availableEffectsPerCategory[PLATARCADE_CATEGORIES];
    u8 rouletteEffects[PLATARCADE_GRID];
    u8 availableEffects[PLATARCADE_EFFECTS];
} PlatArcadeRoulette;

// The fields of a party Pokémon the rules read and write (Platinum's MON_DATA_*); the types in Platinum's numbering (9 the
// Mystery type; Black 2's from Fire on are one lower)
enum {
    PLATARCADE_MON_SPECIES,
    PLATARCADE_MON_EXISTS,                     // MON_DATA_SPECIES_EXISTS
    PLATARCADE_MON_LEVEL,
    PLATARCADE_MON_EXP,
    PLATARCADE_MON_HP,
    PLATARCADE_MON_MAX_HP,
    PLATARCADE_MON_ATK,
    PLATARCADE_MON_DEF,
    PLATARCADE_MON_SPEED,
    PLATARCADE_MON_SP_ATK,
    PLATARCADE_MON_SP_DEF,
    PLATARCADE_MON_STATUS,                     // Platinum's MON_CONDITION_* (any status: nonzero)
    PLATARCADE_MON_ITEM,
    PLATARCADE_MON_TYPE_1,
    PLATARCADE_MON_TYPE_2,
    PLATARCADE_MON_ABILITY,
    PLATARCADE_MON_FIELDS,
};

// The sides the calls below name: the Arcade's two parties (Platinum's playersParty, opponentsParty) and the parties of the last
// battle as they left it (FieldBattleDTO parties[BATTLER_PLAYER_1], [BATTLER_ENEMY_1])
enum {
    PLATARCADE_PLAYERS,
    PLATARCADE_OPPONENTS,
    PLATARCADE_BATTLE_PLAYER,
    PLATARCADE_BATTLE_ENEMY,
};

// ---- the rules (arcade_rules.c; the names are Platinum's, with PlatArcade_ for BattleArcade_)
u16 PlatArcade_Random(PlatArcade *arcade);
u32 PlatArcade_StatIndex(u8 challengeType, u32 which);
void PlatArcade_Init(PlatArcade *arcade, PlatArcadeSave *save, void *records, u16 resuming, u8 challengeType, u8 slot1,
                     u8 slot2, u8 slot3);
void PlatArcade_LoadTrainersForRound(PlatArcade *arcade, PlatArcadeSave *save, u16 resuming);
void PlatArcade_Save(PlatArcade *arcade, PlatArcadeSave *save, void *records, u8 saveType);
void PlatArcade_SaveOnLoss(PlatArcade *arcade, PlatArcadeSave *save, void *records);
void PlatArcade_SaveOnCompletingRound(PlatArcade *arcade, PlatArcadeSave *save, void *records);
void PlatArcade_SetupFirstOpponentsParty(PlatArcade *arcade);
void PlatArcade_SetupNextOpponentsParty(PlatArcade *arcade);
void PlatArcade_SetupOpponentsParty(PlatArcade *arcade);
void PlatArcade_CreateOpponentMons(PlatArcade *arcade);
void PlatArcade_ApplyEffect(PlatArcade *arcade, u8 effect);
u16 PlatArcade_GetEarnedBP(PlatArcade *arcade);
u16 PlatArcade_GetFreeBPFromEvent(PlatArcade *arcade, u8 activeEffect);
u16 PlatArcade_GetCurrentRound(PlatArcade *arcade);
u16 PlatArcade_GetAIMask(PlatArcade *arcade);
u8 PlatArcade_GetCategoryFromEffect(u8 effect);
u8 PlatArcade_GetPlayerPartySize(u8 challengeType, BOOL includePartnerMons);
u8 PlatArcade_GetOpponentPartySize(u8 challengeType, BOOL includeBothOpponents);
BOOL PlatArcade_IsMultiPlayerChallenge(u8 challengeType);
u16 PlatArcade_GetTrainerOffset(PlatArcade *arcade, u8 trainerSlot);
void PlatArcade_ClearActiveStreak(void *records, u8 challengeType);
// BattleArcade_SetupBattle's rules: the AI, whose parties fight (the swap), then both parties healed (after the game copied them
// into the battle). Returns the AI mask; *swapped TRUE when the player fights with the opponent's Pokémon
u16 PlatArcade_SetupBattle(PlatArcade *arcade, BOOL *swapped);
// FrontierScrCmd_BattleArcade_CleanupBattle: the performance, won or not, the held items as the battle left them, the level
// back after the Ally Level Up, the stats as they were when the board opened
void PlatArcade_CleanupBattle(PlatArcade *arcade, u32 turns, BOOL won);
// CallBattleArcadeFunction for the functions that only compute (the game's: arcade_field.c). FALSE: not one of them
BOOL PlatArcade_Function(PlatArcade *arcade, PlatArcadeSave *save, void *records, u8 fn, u8 arg1, u8 arg2, u16 *result);
// The board (OpenBattleArcadeApp): Open sets it up as the app does before its cursor runs (the scene's arguments, the random
// number, the starting panel, the 16 panels); Tick is one frame of the running cursor (30 a second), TRUE once it stops (the
// player pressed, or 30 seconds passed); Stop picks the panel's effect and keeps the cursor (the app's exit)
void PlatArcade_RouletteOpen(PlatArcade *arcade, PlatArcadeRoulette *roulette);
void PlatArcade_RouletteStart(PlatArcadeRoulette *roulette);
BOOL PlatArcade_RouletteTick(PlatArcade *arcade, PlatArcadeRoulette *roulette, BOOL stopPressed);
void PlatArcade_RouletteStop(PlatArcade *arcade, PlatArcadeRoulette *roulette);
u8 PlatArcade_CursorMoveFrames(u8 rouletteSpeed);   // sCursorMoveFrames: the frames between two moves of the cursor

// ---- what each side gives the rules (arcade_field.c on the DS, the harness's sim.c on the host)
// The records: Platinum's BattleFrontierStats soloStats by its ids, its BattleArcadeStreakFlags
u16 PlatArcade_GetStat(void *records, u32 stat);
void PlatArcade_SetStat(void *records, u32 stat, u16 value);       // (at most 9999, as BattleFrontierSave_SetStat)
u32 PlatArcade_GetStreakFlag(void *records, u32 challengeType);
void PlatArcade_SetStreakFlag(void *records, u32 challengeType, u32 value);
// The parties: the player's (empty at Init; a copy of a field party Pokémon added at the end), the opponent's (emptied, then
// each Pokémon made from its PlatArcadeMon at a level, FrontierPokemon_InitPokemon), and the last battle's (read only)
u32 PlatArcade_FieldMonItem(PlatArcade *arcade, u8 fieldSlot);
void PlatArcade_PartyAddFieldMon(PlatArcade *arcade, u8 fieldSlot);
void PlatArcade_OpponentsClear(PlatArcade *arcade);
void PlatArcade_OpponentAdd(PlatArcade *arcade, const PlatArcadeMon *mon, u8 level);
u32 PlatArcade_MonGet(PlatArcade *arcade, u32 side, u8 slot, u32 field);
void PlatArcade_MonSet(PlatArcade *arcade, u32 side, u8 slot, u32 field, u32 value);
void PlatArcade_MonCalcLevelAndStats(PlatArcade *arcade, u32 side, u8 slot);
void PlatArcade_PartyHeal(PlatArcade *arcade, u32 side);              // Party_HealAllMembers
u32 PlatArcade_BaseExpAt(u16 species, u8 level);                     // Pokemon_GetSpeciesBaseExpAt
// The Frontier's Trainers and sets
void PlatArcade_ReadSet(u16 setID, PlatArcadeSet *set);
u16 PlatArcade_TrainerSets(u16 trainerID, u16 *sets, u16 max);      // the Trainer's set ids, how many
u16 PlatArcade_SpeciesAbility(u16 species, u32 slot);               // the species' ability 1 or 2 (0: none)

// ---- the game side (arcade_field.c, overlay 381; the resident PearlB2_Ext_Arcade loads it for one op and unloads it after)
// gPlatArcadeTable, in the overlay's .data: filled by PearlB2's b2tools/patches/platinum_arcade.py in a Platinum build. Empty
// (Pearl, Diamond, a build without it), no challenge starts: every op answers 0
#define PLATARCADE_TABLE_MAGIC 0x44435241       // 'ARCD'
typedef struct {
    u32 magic;
    u16 entryRegulation;                        // the lobby's party screen: three (Black 2's Subway regulation with no level
                                                // rule, the same item allowed, Platinum's banned species)
    u16 brainBgm;                               // Dahlia's battle song (SEQ_PL_BA_BRAIN) once installed; 0: the Subway's
    u16 brainWinBgm;                            // her victory song (SEQ_PL_WINBRAIN)
    u16 padding;
} PlatArcadeTable;

// The opponent's Pokémon on the DS (Platinum's opponentsParty): the set as made, and what the board and the heal changed. The
// game makes a Black 2 party Pokémon of it when a value needs one (its stats) and for the battle
typedef struct {
    PlatArcadeMon mon;
    u32 exp;                                    // the level's experience (Level 50, 53 after the Foe Level Up)
    u32 status;                                 // Platinum's MON_CONDITION_*
    u16 hp;
    u16 maxHp;
    u16 item;
    u8 level;
    u8 padding;
} PlatArcadeOpponent;

// What the challenge keeps while it runs, in the core save's challenge area (PearlB2FrontierSave.challenge): Platinum's
// BattleArcadeSave first, as Platinum's union has it, then the running challenge, the board, the player's three (Black 2 party
// Pokémon: Platinum keeps them on its heap for the length of the scenes; here they live through the overlay's unloading and the
// warps between the rooms) and the opponent's
#define PLATARCADE_PKM_SIZE 220                // sizeof(PartyPkm)
typedef struct {
    PlatArcadeSave save;
    PlatArcade arcade;
    PlatArcadeRoulette roulette;
    u32 party[PLATARCADE_PARTY_SOLO][PLATARCADE_PKM_SIZE / 4];
    PlatArcadeOpponent opponents[PLATARCADE_MAX_PARTY];
    u8 picked[8];                       // the lobby's party screen's picks (slots from 1)
    u32 choice;
    u32 screenResult;
} PlatArcadeWork;

#if !defined(PEARLB2_HOST)
#include "struct_decls.h"
extern u32 OVERLAY_381_ID[];
#define PLATARCADE_OVERLAY_ID ((u32)OVERLAY_381_ID)
BOOL PlatArcade_Op(VM *vm, FieldScriptEnv *env, u32 op);
BOOL PearlB2_Ext_Arcade(VM *vm, FieldScriptEnv *env, u32 op);
// The board's event, made in the overlay by Black 2's GameEvent_CreateOverlayDelegate (the overlay stays loaded while it runs,
// and is unloaded when it ends); its args are a PlatArcadeBoardArgs
typedef struct {
    MsgData *msgData;                   // the room's text, whose lines name the 32 effects
    u16 firstLine;
} PlatArcadeBoardArgs;
GameEvent *PlatArcade_BoardEventProvider(GameSystem *gsys, void *args);
// The resident side across a battle (plat_arcade_ext.c): the battle's setup and its start effects (Trick Room)
#define PLATARCADE_START_TRICK_ROOM 1
void PearlB2_Arcade_SetBattle(BtlSetup *setup, u32 startEffects);
BtlSetup *PearlB2_Arcade_GetBattle(void);
// From the Castle's battle-end hook (resident/plat_castle_ext.c PearlB2_Castle_StoreParties, block plat-arcade): for the Arcade's
// battle, both parties as they left the battle into the setup (party 0 the player's side, 1 the enemy's: the player's own
// Pokémon after a swap), Black 2's own copy, without its giving back of held items (an item used up is gone, as Platinum)
void PearlB2_Arcade_StoreParties(BtlMainModule *mainModule);
// ov167 btl_server_flow.c BtlServerFlow_StartBattle's ServerControl_AfterSwitchIn call (plat-arcade_decomp.diff): Trick Room
// for five turns first for the Arcade's battle that has it, then the original
BOOL PearlB2_Arcade_AfterSwitchIn(BtlServerFlow *flow);
// Pearl's fog in battle (resident/leftovers.c, plat-arcade_decomp.diff): set for the next battle after SaveBtlFieldStatus, which
// notes the zone's
void PearlB2_SetBattleFog(BOOL fog);
#endif

// The Arcade's Frontier ops: the low five bits of ops 0x80-0x9f (sub-command 0x93; pearl_story.inc pl_Arcade*). Each argument
// is a value or a var. An op marked "event" runs a screen, the board or the battle: the script goes on when it ends
enum {
    PLATARCADE_OP_INIT,                 // resuming, challenge type, slot 1, slot 2, slot 3: InitBattleArcade
    PLATARCADE_OP_LOAD_ROUND,           // resuming: BattleArcade_LoadTrainersForRound
    PLATARCADE_OP_FUNCTION,             // fn, arg1, arg2, var: CallBattleArcadeFunction (SET_NAME_OF_AFFECTED_TRAINER: arg1 the
                                        // word, arg2 the Trainer's slot; the player's name for the player's effects)
    PLATARCADE_OP_FREE,                 // FreeBattleArcade
    PLATARCADE_OP_SETUP_FIRST,          // BattleArcade_SetupFirstOpponent
    PLATARCADE_OP_SETUP_NEXT,           // BattleArcade_SetupNextOpponent
    PLATARCADE_OP_START_BATTLE,         // (event) BattleArcade_StartBattle: Black 2's Subway battle, the board's effects on it
    PLATARCADE_OP_CLEANUP_BATTLE,       // BattleArcade_CleanupBattle
    PLATARCADE_OP_CHECK_WON,            // var: BattleArcade_CheckWonBattle
    PLATARCADE_OP_TRAINER_WORD,         // word, slot, line: the opponent's line into a word (BattleArcade_PrintTrainerInfo)
    PLATARCADE_OP_APPLY_EFFECT,         // ApplyArcadeEffect
    PLATARCADE_OP_BOARD,                // first line (event): OpenBattleArcadeApp, the board on the field (its 16 panels named by
                                        // 32 lines of the room's text from `first`); then BA_FUNC_GET_ACTIVE_EFFECT has its effect
    PLATARCADE_OP_LOBBY,                // fn, arg, var: CallBattleArcadeLobbyFunction 0-3 (4, the party screen: LOBBY_SELECT)
    PLATARCADE_OP_DELETE_STREAK,        // challenge type: DeleteActiveBattleArcadeStreak
    PLATARCADE_OP_LOBBY_SELECT,         // challenge type (event): BA_LOBBY_FUNC_SELECT_POKEMON, the field party on Black 2's
                                        // battle-entry party screen (three; not the same species twice, nor a banned one)
    PLATARCADE_OP_SELECTED_SLOTS,       // var, var, var: GetBattleArcadeSelectedSlots (0xff in the first for none)
    PLATARCADE_OP_COUNT,
};

#endif // POKEBW2_PEARLB2_PLAT_ARCADE_H
