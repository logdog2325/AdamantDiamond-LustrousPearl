#include "pearlb2.h"
#include "pearlb2/plat_frontier.h"
#include "pearlb2/plat_hall.h"
#include "pearlb2/tower.h"
#include "types.h"
#include "battle/btl_result.h"
#include "battle/btl_setup.h"
#include "constants/arc.h"
#include "constants/pokemon.h"
#include "constants/text_banks.h"
#include "field/battle_facility.h"
#include "field/bsubway_scr.h"
#include "field/event_battle.h"
#include "field/field_event.h"
#include "field/field_msgbg.h"
#include "field/field_script.h"
#include "field/fld_btl_inst_event.h"
#include "gfl/backup_system.h"
#include "gfl/heap.h"
#include "gfl/msg.h"
#include "gfl/random.h"
#include "gfl/std.h"
#include "gfl/str.h"
#include "nitro/os.h"
#include "pml/poke_party.h"
#include "save/save_control.h"
#include "system/game_data.h"
#include "system/game_system.h"
#include "system/pms_data.h"
#include "system/bmp_menuwork.h"     // (plat-fix2) the records machine's list
#include "system/vm.h"
#include "system/wordset.h"

// Platinum's Battle Hall on the field (include/pearlb2/plat_hall.h; PearlB2's notes/PLATINUM_FRONTIER.md "The Battle Hall"): the
// Hall's Frontier ops (sub-command 0x93, ops 0x40-0x5f), run by resident/plat_hall_ext.c with this overlay loaded for the op.
// The rules are hall_rules.c's (Platinum's, proven on the host); this file gives them the save, the party, the battle and the
// type grid. The challenge's work lives in the Frontier's save area (the core's challenge union), as Platinum's BattleHall lives
// on its heap for the length of the scenes.

#if PEARLB2

#define HALL_HEAP HEAPID_GAMEEVENT
#define BSUBWAY_ARC_TRAINERS 0xd4       // a/2/1/2: the Battle Subway's Trainers (patches/battle_tower.py: Platinum's in Platinum)
#define BSUBWAY_MSG_NAMES 0xf           // their names (BtlInst_MakeRomTrainer's message file)
#define BSUBWAY_MSG_LINES 0x178         // their lines, three each (BtlInst_MakeRomTrainer: trainerId * 3)
#define HALL_SUMMARY_ROW 17             // the type list's summary row: Platinum's grid cell 17
#define HALL_LEVEL_MIN 30               // CheckPartyIsBattleHallEligible
#define NATIONAL_DEX_COUNT 493

typedef char PlatHallCheckWorkSize[sizeof(PlatHallWork) <= sizeof(((PearlB2FrontierSave *)0)->challenge) ? 1 : -1];
typedef char PlatHallCheckTableSize[sizeof(PlatHallTable) == 11280 ? 1 : -1];   // b2tools/platinum_hall_data.py table()
typedef char PlatHallCheckWinSize[sizeof(PlatHallWinSave) == 1984 && sizeof(PlatHallWinSave) <= PLAT_HALL_WIN_EXTRA_SIZE ? 1 : -1];

// Filled by PearlB2's b2tools/patches/platinum_hall.py in a Platinum build (in this overlay's .data, so in its file)
#pragma explicit_zero_data on
PlatHallTable gPlatHallTable = { 0 };
#pragma explicit_zero_data reset

// Platinum's sBattleFrontierBanlist (pokemon.c)
static const u16 sBanlist[] = { 150, 151, 249, 250, 251, 382, 383, 384, 385, 386, 483, 484, 487, 489, 490, 491, 492, 493 };

// ---------------------------------------------------------------- the save, through the core (resident/plat_frontier.c)
u16 PlatHall_GetStat(void *save, u32 stat) {
    return PearlB2_Frontier_GetStat(save, stat);
}

void PlatHall_SetStat(void *save, u32 stat, u16 value) {
    PearlB2_Frontier_SetStat(save, stat, value);
}

u32 PlatHall_GetStreakFlag(void *save, u32 challengeType) {
    return (PearlB2_Frontier_GetSave(save)->streakFlags[FRONTIER_FACILITY_HALL] >> challengeType) & 1;
}

void PlatHall_SetStreakFlag(void *save, u32 challengeType, u32 value) {
    u8 *flags = &PearlB2_Frontier_GetSave(save)->streakFlags[FRONTIER_FACILITY_HALL];

    if (value >= 1) {
        *flags |= 1 << challengeType;
    } else {
        *flags &= 0xff ^ (1 << challengeType);
    }
}

// ---------------------------------------------------------------- the win records (plat-frontier-rooms)
// Platinum keeps them in an extra save block, loads it when a rule needs them and writes it with the whole save when one rises
// (battle_hall_win_records.c, BattleHallWinRecords_Save). Here: Black 2's extra save block 4, the C-Gear's downloaded skin, which
// nothing that can run in Sinnoh reads or writes (PearlB2's notes/DATA.md registry), behind a magic (include/pearlb2/plat_hall.h).
// The ops that need them load the block, point sWinRecords at it, run the rule and free it; Black 2's extra save is a dual save:
// the block and the whole save, as Platinum's.
static u16 *sWinRecords;                // while an op has the records (this overlay's .bss: cleared when it loads)

u16 *PlatHall_WinRecords(void *save) {
    return sWinRecords;
}

static void *WinRecords_Load(SaveControl *save) {
    void *buffer = GFL_HeapAllocate(HEAPID_TAIL(HALL_HEAP), PLAT_HALL_WIN_EXTRA_AREA, TRUE, "hall_field.c", 0);
    u32 result = SaveControl_LoadExtraBlock(save, PLAT_HALL_WIN_EXTRA_BLOCK, HEAPID_TAIL(HALL_HEAP), buffer,
                                            PLAT_HALL_WIN_EXTRA_AREA);
    PlatHallWinSave *win = getAddressOfExtraSaveBlk(save, PLAT_HALL_WIN_EXTRA_BLOCK, 0);

    if ((result != SAVE_LOAD_RESULT_OK && result != SAVE_LOAD_RESULT_OK_PARTIAL) || win->magic != PLAT_HALL_WIN_MAGIC) {
        MI_CpuFill8(win, 0, PLAT_HALL_WIN_EXTRA_SIZE);  // set up empty on first use (BattleHallWinRecords_Init)
        win->magic = PLAT_HALL_WIN_MAGIC;
    }
    sWinRecords = win->records;
    return buffer;
}

static void WinRecords_Free(SaveControl *save, void *buffer) {
    sWinRecords = NULL;
    freeIntermediateSaveExtraBlksAfterLoad2(save, PLAT_HALL_WIN_EXTRA_BLOCK);
    GFL_HeapFree(buffer);
}

// BattleHallWinRecords_Save: the block and the whole save, at once (as Trial House's BattleExamination_Load writes its block)
static void WinRecords_Save(GameData *gameData) {
    u32 result;

    GameData_StartSaveBlock(gameData, PLAT_HALL_WIN_EXTRA_BLOCK);
    for (;;) {
        result = GameData_UpdateSaveBlock(gameData, PLAT_HALL_WIN_EXTRA_BLOCK);
        if (result == SAVE_RESULT_OK || result == SAVE_RESULT_NG) {
            break;
        }
        OS_WaitIrq(TRUE, 1);
    }
}

static PlatHallWork *GetWork(SaveControl *save) {
    return (PlatHallWork *)PearlB2_Frontier_GetSave(save)->challenge;
}

// What Platinum reads from the party at the moment it needs it: the entered Pokémon's levels and the first one's species
static void ReadParty(PlatHallWork *w, GameData *gameData) {
    PokeParty *party = GameData_GetParty(gameData);
    PartyPkm *pkm = PokeParty_GetPkm(party, w->partySlots[0]);

    w->levels[0] = PokeParty_GetParam(pkm, PKM_PARAM_LEVEL, NULL);
    w->species = PokeParty_GetParam(pkm, PKM_PARAM_SPECIES, NULL);
    w->levels[1] = PokeParty_GetParam(PokeParty_GetPkm(party, w->partySlots[1]), PKM_PARAM_LEVEL, NULL);
}

// A Frontier Trainer's Black 2 class: its file in the Subway's Trainers (patches/battle_tower.py writes Platinum's there)
u16 PearlB2_Hall_TrainerClass(u16 trainerId) {
    u16 *data = BtlInst_LoadTrainerData(BSUBWAY_ARC_TRAINERS, trainerId, HALL_HEAP);
    u16 trainerClass = data[0];

    GFL_HeapFree(data);
    return trainerClass;
}

static u8 PlatinumTypeToB2(u8 type) {
    return type < PLAT_HALL_TYPE_MYSTERY ? type : type - 1;    // Black 2 has no Mystery type between Steel and Fire
}

// ---------------------------------------------------------------- the battle (BattleHall_SetupBattle, BattleHall_StartBattle)
static void ToSubwayMon(const PlatHallMon *m, BSubwayPokemon *p, MsgData *speciesNames) {
    int i;

    MI_CpuFill8(p, 0, sizeof(BSubwayPokemon));
    p->species = m->species;
    p->form = m->form;
    p->item = m->item;
    for (i = 0; i < 4; i++) {
        p->moves[i] = m->moves[i];
    }
    p->id = m->otID;
    p->personality = m->personality;
    p->ivs.all = (m->ivs * 0x2108421) & 0x3fffffff;        // every stat's IV in its five bits
    for (i = 0; i < 6; i++) {
        p->evs[i] = m->evs[i];
    }
    p->ability = m->ability;
    p->happiness = m->friendship;
    p->nature = m->nature;
    GFL_MsgDataLoadRawStr(speciesNames, m->species, p->nickname, NELEMS(p->nickname));
}

static BtlSetup *MakeBattle(PlatHallWork *w, GameSystem *gsys) {
    GameData *gameData = GSYS_GetGameData(gsys);
    PokeParty *party = GameData_GetParty(gameData);
    u8 offset = w->currentBattle * 2;
    u8 count = PlatHall_GetPlayerPartySize(w->challengeType);
    BtlFieldStatus status;
    BtlSetup *setup;
    BSubwayTrainer *trainer;
    BtlSetupTrainer *dest;
    BSubwayPokemon mons[2];
    MsgData *speciesNames;
    void *trainerData;
    u8 rank;
    u16 ai;
    int i;

    PokeParty_RecoverAll(party);                            // Party_HealAllMembers
    SaveBtlFieldStatus(&status, gameData, GSYS_GetField(gsys));
    setup = BtlSetup_Create(HALL_HEAP);
    if (w->challengeType == PLAT_HALL_DOUBLE) {
        BtlSetup_SetTrainer1v1Double(setup, gameData, &status, 0, HALL_HEAP);
    } else {
        BtlSetup_SetTrainer1v1Single(setup, gameData, &status, 0, HALL_HEAP);
    }
    setup->unk34[0] = GetGameDataPlayerInfo(gameData);
    PokeParty_InitCore(setup->party[0], 6);
    for (i = 0; i < count; i++) {
        PokeParty_AddPkm(setup->party[0], PokeParty_GetPkm(party, w->partySlots[i]));
    }

    trainer = GFL_HeapAllocate(HEAPID_TAIL(HALL_HEAP), sizeof(BSubwayTrainer), TRUE, "hall_field.c", 0);
    trainerData = BtlInst_MakeRomTrainer(trainer, BSUBWAY_ARC_TRAINERS, w->trainerIDs[offset], BSUBWAY_MSG_NAMES, HALL_HEAP);
    GFL_HeapFree(trainerData);
    rank = PlatHall_GetBattleRank(w);
    ai = PlatHall_GetAIMask(w, &gPlatHallTable, rank);
    dest = setup->trainers[1];
    dest->trainerId = trainer->unk00;
    dest->trainerClass = trainer->trainerId;
    dest->aiFlags = ai;                                     // Platinum's three flags are Black 2's first three
    GFL_StrBufLoadString(dest->name, trainer->name);
    PMSData_Clear(&dest->unk18);
    PMSData_Clear(&dest->unk20);
    GFL_HeapFree(trainer);

    PlatHall_MakeOpponents(w, &gPlatHallTable);
    speciesNames = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_SPECIES_NAMES, HALL_HEAP);
    for (i = 0; i < count; i++) {
        ToSubwayMon(&w->mons[i], &mons[i], speciesNames);
    }
    GFL_MsgDataFree(speciesNames);
    BtlInst_MakeParty(setup->party[1], mons, PlatHall_GetOpponentLevel(w), count, HALL_HEAP);

    BtlSetup_PostProcessTrialHouse(setup);                  // a facility battle: the Subway's music, no prize money
    if ((w->trainerIDs[offset] == PLAT_HALL_ARGENTA_SILVER || w->trainerIDs[offset] == PLAT_HALL_ARGENTA_GOLD) &&
        gPlatHallTable.brainBgm != 0) {
        setup->fieldSituation.bgm = gPlatHallTable.brainBgm;            // Platinum's SEQ_PL_BA_BRAIN, once installed
        setup->fieldSituation.unk12 = gPlatHallTable.brainWinBgm;       // SEQ_PL_WINBRAIN
    }
    return setup;
}

// ---------------------------------------------------------------- the type grid as Black 2's list menu (OpenBattleHallApp)
// Each of the grid's 17 types, in the grid's order, with its rank as the grid shows it (stored + 1, at most 10), then the
// summary row; the script's own list menu (InitLocalTextListMenu before, ShowListMenu after) shows them, its result the cell
static void AppendDigits(StrBuf *s, u32 n) {
    if (n >= 10) {
        GFL_StrBufAppend(s, (u16)('0' + n / 10));
    }
    GFL_StrBufAppend(s, (u16)('0' + n % 10));
}

static void AddTypeRows(PlatHallWork *w, FieldScriptEnv *env, u16 summaryLine) {
    ScriptListMenu *menu = &env->subwork->listMenu;
    MsgData *types = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_TYPE_NAMES, HALL_HEAP);
    StrBuf *row = GFL_StrBufCreate(32, HALL_HEAP);
    u32 rank;
    u16 cell;

    for (cell = 0; cell < PLAT_HALL_GRID_TYPES; cell++) {
        rank = PlatHall_GetRankOfType((u8)cell, &w->typeRanks[w->challengeType][0]) + 1;
        if (rank > PLAT_HALL_MAX_RANK) {
            rank = PLAT_HALL_MAX_RANK;
        }
        GFL_MsgDataLoadStrbuf(types, PlatinumTypeToB2(PlatHall_CursorPosToType((u8)cell)), row);
        GFL_StrBufAppend(row, ' ');
        GFL_StrBufAppend(row, ' ');
        AppendDigits(row, rank);
        AppendListMenuOption(menu->options, row, cell, HALL_HEAP);
    }
    GFL_MsgDataLoadStrbuf(menu->msgData, summaryLine, row);              // the summary row: a line of the script's own text
    AppendListMenuOption(menu->options, row, HALL_SUMMARY_ROW, HALL_HEAP);
    GFL_StrBufFree(row);
    GFL_MsgDataFree(types);
}

// ---------------------------------------------------------------- the records machine (plat-fix2, 2026-11-11)
// Platinum's ShowBattleHallRecordMonSelectionMenu (pokeplatinum overlay005/ov5_021F6454.c) lists, for the letters picked, the
// species with a record of the challenge type, in its alphabetical lists: application/zukanlist/zkn_data/zukan_data.narc
// members 18-26 (ABC .. YZ; together every species 1-493 once), read from Platinum's dump (sAlphaSpecies[sAlphaStart[g] ..
// sAlphaStart[g + 1] - 1] is group g). Then EXIT (the script's own row). Its list holds 120 rows; Black 2's script list
// menu 32, so a longer list gets a list of its own size (the largest group, STU, has 97 species)
#define HALL_LETTER_GROUPS 9
static const u16 sAlphaStart[10] = { 0, 87, 136, 191, 235, 303, 360, 457, 487, 493 };
static const u16 sAlphaSpecies[493] = {
    460, 63, 359, 142, 306, 190, 65, 334, 424, 181, 347, 24, 59, 493, 168, 348,
    304, 144, 482, 184, 298, 371, 343, 354, 339, 411, 153, 267, 15, 374, 182, 69,
    400, 399, 9, 257, 242, 438, 286, 437, 436, 406, 418, 1, 427, 412, 12, 331,
    332, 323, 455, 318, 268, 351, 10, 251, 113, 6, 4, 5, 441, 421, 420, 152,
    390, 358, 170, 433, 366, 344, 36, 35, 173, 91, 415, 256, 341, 222, 346, 408,
    342, 488, 453, 169, 159, 104, 155, 491, 301, 225, 386, 87, 483, 50, 132, 85,
    84, 232, 148, 149, 452, 147, 426, 425, 96, 51, 206, 356, 477, 355, 269, 133,
    23, 125, 466, 309, 101, 239, 395, 244, 196, 102, 103, 295, 83, 22, 349, 160,
    456, 180, 136, 419, 330, 205, 478, 162, 444, 475, 445, 282, 92, 423, 94, 74,
    443, 203, 487, 471, 362, 431, 207, 472, 44, 42, 118, 55, 76, 368, 210, 75,
    88, 388, 383, 253, 58, 326, 316, 130, 440, 297, 93, 485, 214, 449, 450, 107,
    106, 237, 250, 430, 163, 187, 116, 229, 228, 367, 97, 174, 314, 392, 2, 39,
    385, 135, 189, 124, 140, 141, 64, 14, 115, 352, 230, 99, 281, 109, 98, 401,
    402, 382, 305, 171, 131, 246, 380, 381, 470, 166, 165, 463, 108, 345, 264, 271,
    428, 270, 294, 448, 272, 249, 457, 337, 370, 404, 405, 68, 67, 66, 240, 219,
    129, 126, 467, 81, 82, 462, 296, 473, 490, 310, 56, 226, 458, 179, 183, 105,
    259, 284, 303, 308, 307, 154, 52, 481, 376, 375, 11, 151, 150, 262, 350, 241,
    439, 312, 200, 429, 146, 391, 414, 122, 258, 89, 446, 198, 177, 34, 31, 29,
    32, 30, 33, 290, 38, 291, 164, 299, 322, 274, 224, 43, 138, 139, 95, 417,
    484, 46, 47, 279, 53, 231, 489, 172, 18, 17, 16, 25, 221, 204, 127, 393,
    311, 186, 60, 61, 62, 77, 261, 137, 474, 233, 57, 394, 476, 54, 247, 432,
    195, 156, 211, 26, 243, 280, 409, 78, 20, 19, 384, 378, 486, 377, 379, 369,
    223, 112, 111, 464, 447, 315, 407, 479, 302, 373, 27, 28, 254, 212, 123, 117,
    119, 364, 273, 86, 161, 336, 319, 492, 292, 372, 90, 422, 410, 275, 403, 285,
    213, 353, 266, 227, 188, 300, 451, 435, 289, 287, 80, 199, 79, 218, 235, 238,
    215, 143, 361, 459, 209, 338, 21, 363, 167, 327, 442, 325, 7, 234, 398, 397,
    396, 121, 120, 208, 434, 185, 245, 192, 191, 283, 333, 317, 260, 277, 220, 276,
    114, 465, 128, 216, 72, 73, 468, 175, 176, 255, 324, 389, 158, 454, 328, 252,
    357, 387, 157, 248, 236, 197, 201, 217, 480, 134, 49, 48, 3, 416, 329, 71,
    288, 45, 313, 100, 37, 320, 321, 365, 8, 461, 13, 70, 110, 340, 293, 40,
    278, 202, 194, 413, 265, 360, 178, 193, 469, 335, 145, 263, 41,
};

static void AddRecordRows(SaveControl *save, FieldScriptEnv *env, u16 challengeType, u16 group) {
    ScriptListMenu *menu = &env->subwork->listMenu;
    MsgData *names;
    StrBuf *row;
    void *buffer;
    u32 i, count = 0;
    u16 species;

    if (group >= HALL_LETTER_GROUPS) {
        return;
    }
    buffer = WinRecords_Load(save);
    for (i = sAlphaStart[group]; i < sAlphaStart[group + 1]; i++) {
        if (PlatHall_GetRecordForSpecies(save, (u8)challengeType, sAlphaSpecies[i]) != 0) {
            count++;
        }
    }
    if (count + 1 + ListMenuCore_GetFirstFreeIndex(menu->options) > 32) {     // (the rows, EXIT; nothing was added yet)
        ListMenuCore_FreeOptionList(menu->options);
        menu->options = InitListMenuOptionHeap(count + 1, env->heapId);
    }
    names = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_SPECIES_NAMES, HALL_HEAP);
    row = GFL_StrBufCreate(32, HALL_HEAP);
    for (i = sAlphaStart[group]; i < sAlphaStart[group + 1]; i++) {
        species = sAlphaSpecies[i];
        if (PlatHall_GetRecordForSpecies(save, (u8)challengeType, species) != 0) {
            GFL_MsgDataLoadStrbuf(names, species, row);
            AppendListMenuOption(menu->options, row, species, env->heapId);
        }
    }
    GFL_StrBufFree(row);
    GFL_MsgDataFree(names);
    WinRecords_Free(save, buffer);
}

// ---------------------------------------------------------------- the lobby (ScrCmd_CallBattleHallLobbyFunction)
static BOOL IsBanned(u16 species) {
    u32 i;

    for (i = 0; i < NELEMS(sBanlist); i++) {
        if (species == sBanlist[i]) {
            return TRUE;
        }
    }
    return species > NATIONAL_DEX_COUNT;                    // (Black 2's own species: the Hall has no sets for their types)
}

// CheckPartyIsBattleHallEligible: one Pokémon of level 30 or more, not an Egg, not banned; for a Double, two of the same species
static BOOL CheckPartyEligible(PokeParty *party, u16 numPokemonNeeded) {
    u16 eligible[6];
    u8 i, j, numEligible = 0;
    u8 partyCount = (u8)PokeParty_GetPkmCount(party);
    u16 species;
    PartyPkm *pkm;

    if (partyCount < numPokemonNeeded) {
        return FALSE;
    }
    for (i = 0; i < 6; i++) {
        eligible[i] = 0;
    }
    for (i = 0; i < partyCount; i++) {
        pkm = PokeParty_GetPkm(party, i);
        species = PokeParty_GetParam(pkm, PKM_PARAM_SPECIES, NULL);
        if (PokeParty_GetParam(pkm, PKM_PARAM_IS_EGG, NULL) || PokeParty_GetParam(pkm, PKM_PARAM_LEVEL, NULL) < HALL_LEVEL_MIN ||
            IsBanned(species)) {
            continue;
        }
        numEligible++;
        eligible[i] = species;
    }
    if (numPokemonNeeded == 2) {
        for (j = 0; j < partyCount; j++) {
            for (i = 0; i < partyCount; i++) {
                if (j != i && eligible[j] != 0 && eligible[j] == eligible[i]) {
                    return TRUE;
                }
            }
        }
        return FALSE;
    }
    return numEligible >= numPokemonNeeded;
}

// ---------------------------------------------------------------- CallBattleHallFunction (frscrcmd_battle_hall.c)
static u16 HallFunction(PlatHallWork *w, GameData *gameData, SaveControl *save, u16 fn, u16 arg1) {
    PokeParty *party = GameData_GetParty(gameData);
    u16 result = 0;
    u8 i, partySize;

    switch (fn) {
    case 2:                                                 // BH_FUNC_SET_CHALLENGE_TYPE
        w->challengeType = (u8)arg1;
        break;
    case 3:                                                 // BH_FUNC_GET_SELECTED_TYPE_INDEX
        result = w->selectedTypeIdx2;
        break;
    case 4:                                                 // BH_FUNC_GET_CURRENT_STREAK
        result = w->currentStreak;
        break;
    case 5:                                                 // BH_FUNC_INCREMENT_CURRENT_STREAK
        if (w->currentStreak < PLAT_HALL_STAT_MAX) {
            w->currentStreak++;
        }
        break;
    case 7:                                                 // BH_FUNC_RESET_SYSTEM: the rest's save is done; the script
        break;                                              // ends the scene there (the Tower's rest does the same)
    case 9:                                                 // BH_FUNC_CHECK_HAS_SAVED
        result = w->save.didSave;
        break;
    case 10:                                                // BH_FUNC_QUICKSAVE
        PlatHall_Save(w, save, 2);
        break;
    case 14:                                                // BH_FUNC_INCREMENT_CURRENT_BATTLE
        result = ++w->currentBattle;
        break;
    case 15:                                                // BH_FUNC_GET_PLAYERS_MONS_SPECIES
        result = PokeParty_GetParam(PokeParty_GetPkm(party, w->partySlots[0]), PKM_PARAM_SPECIES, NULL);
        break;
    case 17:                                                // BH_FUNC_GET_CHALLENGE_TYPE
        result = w->challengeType;
        break;
    case 19:                                                // BH_FUNC_GET_CURRENT_ROUND
        result = w->challengeType == PLAT_HALL_MULTI ? 10 : w->currentRound;
        break;
    case 20:                                                // BH_FUNC_GET_OPPONENT_OBJECT_ID: the Trainer's walker code
        result = PearlB2_TowerObjCode(PearlB2_Hall_TrainerClass(w->trainerIDs[w->currentBattle * 2 + arg1]));
        break;
    case 21:                                                // BH_FUNC_SAVE_ON_LOSS
        PlatHall_SaveOnLoss(w, save);
        break;
    case 22:                                                // BH_FUNC_SAVE_ON_COMPLETING_ROUND
        PlatHall_SaveOnCompletingRound(w, save);
        break;
    case 23:                                                // BH_FUNC_GET_CURRENT_BATTLE
        result = w->currentBattle;
        break;
    case 27:                                                // BH_FUNC_RESTORE_HELD_ITEMS
        partySize = PlatHall_GetPlayerPartySize(w->challengeType);
        for (i = 0; i < partySize; i++) {
            PokeParty_SetParam(PokeParty_GetPkm(party, w->partySlots[i]), PKM_PARAM_ITEM, w->heldItems[i]);
        }
        break;
    case 28:                                                // BH_FUNC_INCREMENT_RANK_OF_BEATEN_TYPE
        PlatHall_IncrementRankOfBeatenType(w);
        break;
    case 30:                                                // BH_FUNC_IS_MULTIPLAYER_CHALLENGE (the Multi is closed)
        result = w->challengeType == PLAT_HALL_MULTI || w->challengeType == PLAT_HALL_MULTI_WFC;
        break;
    case 33:                                                // BH_FUNC_GET_RANK_OF_BEATEN_TYPE
        result = PlatHall_GetRankOfType(w->selectedTypeIdx, &w->typeRanks[w->challengeType][0]);
        break;
    case 34:                                                // BH_FUNC_GET_EARNED_BP
        result = PlatHall_GetEarnedBP(w);
        break;
    case 35:                                                // BH_FUNC_CAP_TYPE_RANKS
        PlatHall_CapTypeRanks(w);
        break;
    case 36:                                                // BH_FUNC_SET_BASE_LEVEL
        ReadParty(w, gameData);
        PlatHall_CalcPlayerLevelSqrt(w);
        break;
    case 37:                                                // BH_FUNC_GET_NEXT_BATTLE_TYPE
        result = PlatHall_GetNextBattleType(w);
        break;
    default:                                                // the screen layer (31), LOAD_TRAINERS (32: MakeBattle reads the
        break;                                              // Trainer itself), the TV (29), the unused ones: nothing
    }
    return result;
}

// ---------------------------------------------------------------- the ops
BOOL PlatHall_Op(VM *vm, FieldScriptEnv *env, u32 op) {
    GameSystem *gsys = FieldScriptEnv_GetGameSystem(env);
    GameData *gameData = GSYS_GetGameData(gsys);
    SaveControl *save = GameData_GetSaveControl(gameData);
    PlatHallWork *w = GetWork(save);
    WordSet *words;
    BtlSetup *setup;
    void *buffer;
    u16 a, b, c, d;
    u16 *var;
    u8 i;

    switch (op) {
    case PLATHALL_OP_INIT:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        d = ScriptReadAny(vm, env);
        if (gPlatHallTable.magic != PLAT_HALL_MAGIC) {
            break;
        }
        w->lcrng = (GFL_RandomLC(0x10000) << 16) | GFL_RandomLC(0x10000);     // the challenge's own LCRNG, seeded once
        PlatHall_Init(w, save, a, (u8)b, (u8)c, (u8)d);
        for (i = 0; i < PlatHall_GetPlayerPartySize(w->challengeType); i++) {
            w->heldItems[i] =
                PokeParty_GetParam(PokeParty_GetPkm(GameData_GetParty(gameData), w->partySlots[i]), PKM_PARAM_ITEM, NULL);
        }
        ReadParty(w, gameData);
        break;
    case PLATHALL_OP_FUNC:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = w->magic == PLAT_HALL_WORK_MAGIC ? HallFunction(w, gameData, save, a, b) : 0;
        (void)c;
        break;
    case PLATHALL_OP_SETUP_NEXT:
        if (w->magic == PLAT_HALL_WORK_MAGIC) {
            ReadParty(w, gameData);
            PlatHall_SetupNextOpponent(w, &gPlatHallTable);
        }
        break;
    case PLATHALL_OP_FREE:
        w->magic = 0;
        break;
    case PLATHALL_OP_START_BATTLE:
        if (w->magic != PLAT_HALL_WORK_MAGIC) {
            break;
        }
        ReadParty(w, gameData);
        setup = MakeBattle(w, gsys);
        PearlB2_Hall_SetBattle(setup);
        ScriptWork_CallEvent(FieldScriptEnv_GetScriptWork(env), EventBSubwayBattleCall_Create(gsys, GSYS_GetField(gsys), setup));
        return TRUE;
    case PLATHALL_OP_CLEANUP_BATTLE:
        setup = PearlB2_Hall_SetBattle(NULL);
        if (setup != NULL) {
            w->wonBattle = setup->result == BTL_RESULT_VICTORY;    // CheckPlayerWonBattle
            BtlSetup_Free(setup);
        }
        break;
    case PLATHALL_OP_CHECK_WON:
        var = ScriptReadVar(vm, env);
        *var = (u16)w->wonBattle;
        break;
    case PLATHALL_OP_WIN_RECORD:                           // BattleHallWinRecords_UpdateRecord: 1 when it changed and saved
        var = ScriptReadVar(vm, env);
        buffer = WinRecords_Load(save);
        *var = PlatHall_UpdateWinRecord(w, save);
        if (*var) {
            WinRecords_Save(gameData);                      // (Platinum's script saves only when this didn't)
        }
        WinRecords_Free(save, buffer);
        break;
    case PLATHALL_OP_TRAINER_INTRO: {                      // (plat-test) the Factory's way: Black 2's balloon over the
        BSubwayTrainer *trainer;                           // opponent. A script word holds 63 characters (ov012 script_work.c
                                                           // 0x40): longer lines were never copied (GFL_StrBufCopy)
        a = ScriptReadAny(vm, env);                        // the Trainer's slot (0, 1)
        b = ScriptReadAny(vm, env);                        // the person (98, 99)
        trainer = GFL_HeapAllocate(HEAPID_TAIL(HALL_HEAP), sizeof(BSubwayTrainer), TRUE, "hall_field.c", 0);
        GFL_HeapFree(BtlInst_MakeRomTrainer(trainer, BSUBWAY_ARC_TRAINERS, w->trainerIDs[w->currentBattle * 2 + a],
                                            BSUBWAY_MSG_NAMES, HALL_HEAP));
        ScriptWork_CallEvent(FieldScriptEnv_GetScriptWork(env), EventBtlInstTrainerMsg_Create(gsys, trainer, 0, b));
        GFL_HeapFree(trainer);          // (the event made its text from the Trainer's line already)
        return TRUE;
    }
    case PLATHALL_OP_TYPE_LIST:
        a = ScriptReadAny(vm, env);                        // the summary row's line in the script's text
        AddTypeRows(w, env, a);
        break;
    case PLATHALL_OP_TYPE_CHECK:
        a = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = (u16)PlatHall_TypeCellCheck(w, a);
        break;
    case PLATHALL_OP_TYPE_WORDS:
        a = ScriptReadAny(vm, env);                        // the cell
        b = ScriptReadAny(vm, env);                        // the type's word
        c = ScriptReadAny(vm, env);                        // the rank's word
        words = ScriptWork_GetWordSet(FieldScriptEnv_GetScriptWork(env));
        loadTypeTextToStrbuf(words, b, PlatinumTypeToB2(PlatHall_CursorPosToType((u8)a)));
        d = PlatHall_GetRankOfType((u8)(a >= 17 ? 17 : a), &w->typeRanks[w->challengeType][0]) + 1;
        WordSetNumber(words, c, d > PLAT_HALL_MAX_RANK ? PLAT_HALL_MAX_RANK : d, 2, 0, TRUE);
        break;
    case PLATHALL_OP_SET_CELL:
        a = ScriptReadAny(vm, env);
        PlatHall_SetSelectedCell(w, a);
        break;
    case PLATHALL_OP_LOBBY:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = 0;
        switch (a) {
        case 0:                                             // BH_LOBBY_FUNC_CHECK_PARTY_ELIGIBLE
            *var = CheckPartyEligible(GameData_GetParty(gameData), b);
            break;
        case 1:                                             // BH_LOBBY_FUNC_CHECK_STREAK_ACTIVE
            *var = (u16)PlatHall_GetStreakFlag(save, b);
            break;
        case 2:                                             // BH_LOBBY_FUNC_GET_CURRENT_STREAK_SPECIES
            *var = PlatHall_GetStat(save, PlatHall_StatIndex((u8)b, PLAT_HALL_STAT_SPECIES));
            break;
        case 3:                                             // BH_LOBBY_FUNC_DELETE_ACTIVE_STREAK
            PlatHall_ClearActiveStreak(save, (u8)b);
            break;
        }
        break;
    case PLATHALL_OP_RECORDS:
        a = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        if (a == 0) {
            buffer = WinRecords_Load(save);
            *var = PlatHall_CountSpeciesWithRecords(save);
            WinRecords_Free(save, buffer);
        } else if (a == 1) {
            buffer = WinRecords_Load(save);
            *var = PlatHall_TotalSinglesRecord(save);
            WinRecords_Free(save, buffer);
        } else {                                            // CheckIfBattleHallStreakIs50
            *var = PlatHall_GetStat(save, PlatHall_StatIndex(PLAT_HALL_SINGLE, PLAT_HALL_STAT_LATEST)) == PLAT_HALL_STREAK_SILVER;
        }
        break;
    case PLATHALL_OP_RECORD_LIST:                          // (plat-fix2) ShowBattleHallRecordMonSelectionMenu's rows
        a = ScriptReadAny(vm, env);                        // the challenge type
        b = ScriptReadAny(vm, env);                        // the letter group
        AddRecordRows(save, env, a, b);
        break;
    case PLATHALL_OP_SPECIES_RECORD:                       // (plat-fix2) DisplayBattleHallRecord's two numbers
        a = ScriptReadAny(vm, env);                        // the challenge type
        b = ScriptReadAny(vm, env);                        // the species
        var = ScriptReadVar(vm, env);                      // the latest streak: 0 unless the species is the type's latest
        *var = 0;
        if (a <= PLAT_HALL_MULTI && PlatHall_GetStat(save, PlatHall_StatIndex((u8)a, PLAT_HALL_STAT_SPECIES)) == b) {
            *var = PlatHall_GetStat(save, PlatHall_StatIndex((u8)a, PLAT_HALL_STAT_LATEST));
        }
        var = ScriptReadVar(vm, env);                      // the species' record (BattleHallWinRecords_GetRecordForSpecies)
        buffer = WinRecords_Load(save);
        *var = PlatHall_GetRecordForSpecies(save, (u8)a, b);
        WinRecords_Free(save, buffer);
        break;
    default:
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    return FALSE;
}

#endif
