#include "pearlb2.h"
#include "pearlb2/plat_castle.h"
#include "pearlb2/plat_frontier.h"
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
#include "gfl/arc.h"
#include "gfl/heap.h"
#include "gfl/msg.h"
#include "gfl/random.h"
#include "gfl/std.h"
#include "gfl/str.h"
#include "nitro/os.h"
#include "pml/personal.h"
#include "pml/poke_party.h"
#include "save/save_control.h"
#include "system/game_data.h"
#include "system/game_system.h"
#include "system/pms_data.h"
#include "system/vm.h"
#include "system/wordset.h"

// PearlB2: Platinum's Battle Castle on the field (include/pearlb2/plat_castle.h; notes/PLATINUM_FRONTIER.md "The Battle Castle").
// Overlay 380, at the gimmick overlays' address: the resident PearlB2_Ext_Castle loads it for one op and unloads it before the
// op returns. An op that runs a screen or the battle gives the script an event of Black 2's own (overlay 12's party screen and
// battle call), whose data is in the challenge's work or on the event heap, so nothing of this overlay runs while it does.
// - The rules are castle_rules.c's (Platinum's, checked on the host against Platinum's C, its two screens' state machines too).
// - The castle's party: three copies of the field party's Pokémon (Black 2's party Pokémon) in the challenge's work, as
//   Platinum's BattleCastle keeps its playersParty: no held item, Level 50 at most; the field party isn't touched. The battle
//   fights with them as they are and gives them back as they left it (the resident hook PearlB2_Castle_StoreParties), so
//   their HP, PP, status and held items carry from battle to battle.
// - The opponents' Pokémon: made from the rules' PlatCastleMon (Black 2's BSubwayPokemon, BtlInst_MakeParty) at Level 50,
//   five up or down by the level change, when a screen shows them or the battle starts.
// - The two screens: the self screen picks one of the castle's three on Black 2's battle-entry party screen (with its summary
//   pages), the rest is the script's: list menus of Platinum's own lines, its yes/no, and the purchases here (ops ASK and BUY,
//   which answer as Platinum's screens do: castle_rules.c). The opponent screen is a list menu of the opponent's three (op
//   OPPONENT_LIST), the same menus and purchases. MON_WORDS gives the summary and moves panels' numbers and names as words.
// - The Frontier Trainer of a battle: his name, class and lines from the Subway's Trainer archive, which holds Platinum's
//   Frontier Trainers (patches/battle_tower.py).

#if PEARLB2

#define CASTLE_HEAP HEAPID_GAMEEVENT
#define SET_ARC 0xd3                    // a/2/1/1: the Subway's sets, Platinum's 0-950 (patches/battle_tower.py)
#define TRAINER_ARC 0xd4                // a/2/1/2: the Subway's Trainers, file id + 1
#define TRAINER_NAMES 0xf               // system text 15: their names
#define TRAINER_LINES 0x178             // system text 376: their lines, three each
#define PICK_MODE 0x17                  // the party list's battle-entry mode (the Trial House's)
#define FACILITY_AI 0x80                // the bit Black 2's facility Trainers have besides the three AI levels (0x87)
#define NO_SLOT 0xff
#define NATIONAL_DEX_COUNT 493
#define ITEM_NONE 0

typedef char PlatCastleCheckWorkSize[sizeof(PlatCastleWork) <= sizeof(((PearlB2FrontierSave *)0)->challenge) ? 1 : -1];
typedef char PlatCastleCheckPkmSize[PLATCASTLE_PKM_SIZE == sizeof(PartyPkm) ? 1 : -1];

// Filled by PearlB2's b2tools/patches/platinum_castle.py in a Platinum build (in this overlay's .data, so in its file)
#pragma explicit_zero_data on
PlatCastleTable gPlatCastleTable = { 0 };
#pragma explicit_zero_data reset

// Platinum's sBattleFrontierBanlist (pokemon.c)
static const u16 sBanlist[] = { 150, 151, 249, 250, 251, 382, 383, 384, 385, 386, 483, 484, 487, 489, 490, 491, 492, 493 };

// The field party, for the op running (the rules' calls below read it)
static GameData *sGameData;

// ---------------------------------------------------------------- the records, through the core (resident/plat_frontier.c)
u16 PlatCastle_GetStat(void *records, u32 stat) {
    return PearlB2_Frontier_GetStat(records, stat);
}

void PlatCastle_SetStat(void *records, u32 stat, u16 value) {
    PearlB2_Frontier_SetStat(records, stat, value);
}

u32 PlatCastle_GetStreakFlag(void *records, u32 challengeType) {
    return (PearlB2_Frontier_GetSave(records)->streakFlags[FRONTIER_FACILITY_CASTLE] >> challengeType) & 1;
}

void PlatCastle_SetStreakFlag(void *records, u32 challengeType, u32 value) {
    u8 *flags = &PearlB2_Frontier_GetSave(records)->streakFlags[FRONTIER_FACILITY_CASTLE];

    if (value >= 1) {
        *flags |= 1 << challengeType;
    } else {
        *flags &= 0xff ^ (1 << challengeType);
    }
}

u32 PlatCastle_GetHeardIntro(void *records) {
    return PearlB2_Frontier_GetSave(records)->castleHeardIntro;
}

void PlatCastle_SetHeardIntro(void *records) {
    PearlB2_Frontier_GetSave(records)->castleHeardIntro = TRUE;
}

static PlatCastleWork *GetWork(SaveControl *save) {
    return (PlatCastleWork *)PearlB2_Frontier_GetSave(save)->challenge;
}

// ---------------------------------------------------------------- the castle's party (Platinum's playersParty)
static PartyPkm *CastleMon(PlatCastle *castle, u8 slot) {
    PlatCastleWork *work = (PlatCastleWork *)((u8 *)castle - (u32) & ((PlatCastleWork *)0)->castle);

    return (PartyPkm *)work->party[slot < PLATCASTLE_PARTY_SOLO ? slot : 0];
}

u32 PlatCastle_FieldMonItem(PlatCastle *castle, u8 fieldSlot) {
    (void)castle;
    return PokeParty_GetParam(PokeParty_GetPkm(GameData_GetParty(sGameData), fieldSlot), PKM_PARAM_ITEM, NULL);
}

void PlatCastle_PartyAddFieldMon(PlatCastle *castle, u8 fieldSlot) {
    copyPartyPkm(PokeParty_GetPkm(GameData_GetParty(sGameData), fieldSlot), CastleMon(castle, castle->playerCount));
}

static const u8 sMonParams[PLATCASTLE_MON_FIELDS] = {
    PKM_PARAM_SPECIES, PKM_PARAM_SPECIES, PKM_PARAM_LEVEL, PKM_PARAM_HP, PKM_PARAM_MAX_HP, PKM_PARAM_STATUS, PKM_PARAM_ITEM,
    PKM_PARAM_MOVE1, PKM_PARAM_MOVE2, PKM_PARAM_MOVE3, PKM_PARAM_MOVE4,
    PKM_PARAM_MOVE1_PP, PKM_PARAM_MOVE2_PP, PKM_PARAM_MOVE3_PP, PKM_PARAM_MOVE4_PP,
    PKM_PARAM_MOVE1_MAX_PP, PKM_PARAM_MOVE2_MAX_PP, PKM_PARAM_MOVE3_MAX_PP, PKM_PARAM_MOVE4_MAX_PP,
};

u32 PlatCastle_MonGet(PlatCastle *castle, u8 slot, u32 field) {
    u32 value = PokeParty_GetParam(CastleMon(castle, slot), sMonParams[field], NULL);

    return field == PLATCASTLE_MON_EXISTS ? value != 0 : value;
}

void PlatCastle_MonSet(PlatCastle *castle, u8 slot, u32 field, u32 value) {
    PokeParty_SetParam(CastleMon(castle, slot), sMonParams[field], value);
}

// Pokemon_GetSpeciesBaseExpAt and Pokemon_CalcLevelAndStats
void PlatCastle_MonSetLevel(PlatCastle *castle, u8 slot, u8 level) {
    PartyPkm *pkm = CastleMon(castle, slot);
    u16 species = PokeParty_GetParam(pkm, PKM_PARAM_SPECIES, NULL);
    u16 form = PokeParty_GetParam(pkm, PKM_PARAM_FORM, NULL);

    PokeParty_SetParam(pkm, PKM_PARAM_EXP, PML_UtilGetPkmLvExp(species, form, level));
    PokeParty_RecalcStats(pkm);
}

// ---------------------------------------------------------------- the Frontier's sets and Trainers
void PlatCastle_ReadSet(u16 setID, PlatCastleSet *set) {
    GFL_ArcSysRead(set, SET_ARC, setID);
}

u16 PlatCastle_TrainerSets(u16 trainerID, u16 *sets, u16 max) {
    u16 *data = BtlInst_LoadTrainerData(TRAINER_ARC, trainerID, CASTLE_HEAP);   // class, count, the set ids
    u16 count = data[1] < max ? data[1] : max;
    u16 i;

    for (i = 0; i < count; i++) {
        sets[i] = data[2 + i];
    }
    GFL_HeapFree(data);
    return count;
}

u16 PlatCastle_SpeciesAbility(u16 species, u32 slot) {
    return (u16)PML_PersonalGetParamSingle(species, 0, slot == 0 ? PERSONAL_ABILITY_1 : PERSONAL_ABILITY_2);
}

static u16 TrainerClass(u16 trainerId) {
    u16 *data = BtlInst_LoadTrainerData(TRAINER_ARC, trainerId, CASTLE_HEAP);
    u16 trainerClass = data[0];

    GFL_HeapFree(data);
    return trainerClass;
}

// ---------------------------------------------------------------- the opponents' Pokémon
static void ToSubwayMon(const PlatCastleMon *mon, BSubwayPokemon *pkm, MsgData *speciesNames) {
    int i;

    MI_CpuFill8(pkm, 0, sizeof(BSubwayPokemon));
    pkm->species = mon->species;
    pkm->form = mon->form;
    pkm->item = mon->item;
    for (i = 0; i < 4; i++) {
        pkm->moves[i] = mon->moves[i];
    }
    pkm->id = mon->otID;
    pkm->personality = mon->personality;
    pkm->ivs.all = ((u32)mon->ivs * 0x2108421) & 0x3fffffff;   // every stat's IV in its five bits
    for (i = 0; i < 6; i++) {
        pkm->evs[i] = mon->evs[i];
    }
    pkm->ability = mon->ability;
    pkm->happiness = mon->friendship;
    pkm->nature = mon->nature;
    GFL_MsgDataLoadRawStr(speciesNames, mon->species, pkm->nickname, NELEMS(pkm->nickname));
}

// The opponent's first `count` Pokémon as Platinum's opponentsParty has them: made at Level 50 (FrontierPokemon_InitPokemon),
// a changed one at the experience of Level 55 or 45 with its stats again (the opponent app's UpdateLevelAdjustment), full HP
static void MakeOpponents(PlatCastle *castle, PokeParty *party, u8 count) {
    BSubwayPokemon *pkms = GFL_HeapAllocate(HEAPID_TAIL(CASTLE_HEAP), sizeof(BSubwayPokemon) * PLATCASTLE_MAX_PARTY, TRUE,
                                            "castle_field.c", __LINE__);
    MsgData *speciesNames = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_SPECIES_NAMES, CASTLE_HEAP);
    PartyPkm *pkm;
    u8 i, level;

    for (i = 0; i < count; i++) {
        ToSubwayMon(&castle->opponentMons[i], &pkms[i], speciesNames);
    }
    GFL_MsgDataFree(speciesNames);
    BtlInst_MakeParty(party, pkms, PLATCASTLE_MAX_LEVEL, count, CASTLE_HEAP);
    GFL_HeapFree(pkms);
    for (i = 0; i < count; i++) {
        level = PlatCastle_GetOpponentLevel(castle, i);
        if (level != PLATCASTLE_MAX_LEVEL) {
            pkm = PokeParty_GetPkm(party, i);
            PokeParty_SetParam(pkm, PKM_PARAM_EXP,
                               PML_UtilGetPkmLvExp(castle->opponentMons[i].species, castle->opponentMons[i].form, level));
            PokeParty_RecalcStats(pkm);
            PokeParty_Recover(pkm);
        }
    }
}

// ---------------------------------------------------------------- the battle (BattleCastle_SetupBattle, BattleCastle_StartBattle)
static BtlSetup *MakeBattle(PlatCastle *castle, GameSystem *gsys) {
    GameData *gameData = GSYS_GetGameData(gsys);
    u8 count = PlatCastle_GetPlayerPartySize(castle->challengeType, FALSE);
    u8 opponentCount = PlatCastle_GetOpponentPartySize(castle->challengeType, FALSE);
    u16 trainerId = castle->trainerIDs[castle->currentBattle];
    BtlFieldStatus status;
    BtlSetup *setup;
    BSubwayTrainer *trainer;
    BtlSetupTrainer *dest;
    u8 i;

    SaveBtlFieldStatus(&status, gameData, GSYS_GetField(gsys));
    setup = BtlSetup_Create(CASTLE_HEAP);
    if (castle->challengeType == PLATCASTLE_DOUBLE) {
        BtlSetup_SetTrainer1v1Double(setup, gameData, &status, 0, CASTLE_HEAP);
    } else {
        BtlSetup_SetTrainer1v1Single(setup, gameData, &status, 0, CASTLE_HEAP);
    }
    setup->unk34[0] = GetGameDataPlayerInfo(gameData);
    PokeParty_InitCore(setup->party[0], 6);                 // the castle's party as it is: its HP, PP, status and items
    for (i = 0; i < count; i++) {
        PokeParty_AddPkm(setup->party[0], CastleMon(castle, i));
    }

    trainer = GFL_HeapAllocate(HEAPID_TAIL(CASTLE_HEAP), sizeof(BSubwayTrainer), TRUE, "castle_field.c", __LINE__);
    GFL_HeapFree(BtlInst_MakeRomTrainer(trainer, TRAINER_ARC, trainerId, TRAINER_NAMES, CASTLE_HEAP));
    dest = setup->trainers[1];
    dest->trainerId = trainer->unk00;
    dest->trainerClass = trainer->trainerId;
    dest->aiFlags = FACILITY_AI | PlatCastle_GetAIMask(castle);     // Platinum's three flags are Black 2's first three
    GFL_StrBufLoadString(dest->name, trainer->name);
    PMSData_Clear(&dest->unk18);
    PMSData_Clear(&dest->unk20);
    GFL_HeapFree(trainer);

    MakeOpponents(castle, setup->party[1], opponentCount);
    PokeParty_RecoverAll(setup->party[1]);                  // Party_HealAllMembers(opponentsParty)
    BtlSetup_PostProcessTrialHouse(setup);                  // a facility battle: the Subway's music, no prize money, no exp
    if ((trainerId == PLATCASTLE_DARACH_SILVER || trainerId == PLATCASTLE_DARACH_GOLD) && gPlatCastleTable.brainBgm != 0) {
        setup->fieldSituation.bgm = gPlatCastleTable.brainBgm;          // Platinum's SEQ_PL_BA_BRAIN, once installed
        setup->fieldSituation.unk12 = gPlatCastleTable.brainWinBgm;     // SEQ_PL_WINBRAIN
    }
    return setup;
}

// ---------------------------------------------------------------- the screens' rows and words
static void AppendDigits(StrBuf *s, u32 n) {
    if (n >= 1000) {
        GFL_StrBufAppend(s, (u16)('0' + n / 1000 % 10));
    }
    if (n >= 100) {
        GFL_StrBufAppend(s, (u16)('0' + n / 100 % 10));
    }
    if (n >= 10) {
        GFL_StrBufAppend(s, (u16)('0' + n / 10 % 10));
    }
    GFL_StrBufAppend(s, (u16)('0' + n % 10));
}

// The rental list (OpenItemSelectScreen): the rows the rental rank allows, each "Name  N CP", the value its row
static void AddRentalRows(PlatCastle *castle, SaveControl *save, FieldScriptEnv *env, BOOL items) {
    ScriptListMenu *menu = &env->subwork->listMenu;
    MsgData *names = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_ITEM_NAMES, CASTLE_HEAP);
    StrBuf *row = GFL_StrBufCreate(40, CASTLE_HEAP);
    u16 count = PlatCastle_RentalCount(save, castle->challengeType, items);
    u16 i;

    for (i = 0; i < count; i++) {
        GFL_MsgDataLoadStrbuf(names, PlatCastle_RentalItem(items, i), row);
        GFL_StrBufAppend(row, ' ');
        GFL_StrBufAppend(row, ' ');
        AppendDigits(row, PlatCastle_RentalPrice(items, i));
        GFL_StrBufAppend(row, ' ');
        GFL_StrBufAppend(row, 'C');
        GFL_StrBufAppend(row, 'P');
        AppendListMenuOption(menu->options, row, i, CASTLE_HEAP);
    }
    GFL_StrBufFree(row);
    GFL_MsgDataFree(names);
}

// The opponent screen's Pokémon (its balls until identified): "Name  Lv. N", or the script's line for one not identified
static void AddOpponentRows(PlatCastle *castle, FieldScriptEnv *env, u16 unknownLine) {
    ScriptListMenu *menu = &env->subwork->listMenu;
    MsgData *names = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_SPECIES_NAMES, CASTLE_HEAP);
    StrBuf *row = GFL_StrBufCreate(40, CASTLE_HEAP);
    u8 i, count = castle->opponentCount < PLATCASTLE_PARTY_SOLO ? castle->opponentCount : PLATCASTLE_PARTY_SOLO;

    for (i = 0; i < count; i++) {
        if (castle->appIdentityUnlocked[i]) {
            GFL_MsgDataLoadStrbuf(names, castle->opponentMons[i].species, row);
            GFL_StrBufAppend(row, ' ');
            GFL_StrBufAppend(row, ' ');
            GFL_StrBufAppend(row, 'L');
            GFL_StrBufAppend(row, 'v');
            GFL_StrBufAppend(row, '.');
            AppendDigits(row, PlatCastle_GetOpponentLevel(castle, i));
        } else {
            GFL_MsgDataLoadStrbuf(menu->msgData, unknownLine, row);
        }
        AppendListMenuOption(menu->options, row, i, CASTLE_HEAP);
    }
    GFL_StrBufFree(row);
    GFL_MsgDataFree(names);
}

// A Pokémon's words: what 0 the species, level, HP, max HP (words 0-3); 1 the summary panel (item 0, nature 1, ability 2,
// Attack 3, Defense 4, Sp. Atk 5, Sp. Def 6, Speed 7); 2 the moves panel (moves 0-3, PP 4-7, max PP 8-11)
static void MonWords(PlatCastle *castle, WordSet *words, u8 side, u8 slot, u16 what) {
    static const u8 sStats[5] = { PKM_PARAM_ATTACK, PKM_PARAM_DEFENSE, PKM_PARAM_SP_ATTACK, PKM_PARAM_SP_DEFENSE, PKM_PARAM_SPEED };
    PokeParty *party = NULL;
    PartyPkm *pkm;
    int i;

    if (side == 0) {
        pkm = CastleMon(castle, slot);
    } else {
        party = PokeParty_Create(CASTLE_HEAP);
        MakeOpponents(castle, party, PLATCASTLE_PARTY_SOLO);
        pkm = PokeParty_GetPkm(party, slot < PLATCASTLE_PARTY_SOLO ? slot : 0);
    }
    if (what == 0) {
        setPartyPokemonSpeciesNameToStrbuf(words, 0, pkm);
        WordSetNumber(words, 1, PokeParty_GetParam(pkm, PKM_PARAM_LEVEL, NULL), 3, 0, TRUE);
        WordSetNumber(words, 2, PokeParty_GetParam(pkm, PKM_PARAM_HP, NULL), 3, 0, TRUE);
        WordSetNumber(words, 3, PokeParty_GetParam(pkm, PKM_PARAM_MAX_HP, NULL), 3, 0, TRUE);
    } else if (what == 1) {
        loadItemNameToStrbuf(words, 0, PokeParty_GetParam(pkm, PKM_PARAM_ITEM, NULL));
        loadNatureToStrbuf(words, 1, PokeParty_GetParam(pkm, PKM_PARAM_NATURE, NULL));
        loadAbilityNameToStrbuf(words, 2, PokeParty_GetParam(pkm, PKM_PARAM_ABILITY, NULL));
        for (i = 0; i < 5; i++) {
            WordSetNumber(words, 3 + i, PokeParty_GetParam(pkm, sStats[i], NULL), 3, 1, TRUE);
        }
    } else {
        for (i = 0; i < 4; i++) {
            loadMoveNameToStrbuf(words, i, PokeParty_GetParam(pkm, PKM_PARAM_MOVE1 + i, NULL));
            WordSetNumber(words, 4 + i, PokeParty_GetParam(pkm, PKM_PARAM_MOVE1_PP + i, NULL), 2, 0, TRUE);
            WordSetNumber(words, 8 + i, PokeParty_GetParam(pkm, PKM_PARAM_MOVE1_MAX_PP + i, NULL), 2, 0, TRUE);
        }
    }
    if (party != NULL) {
        GFL_HeapFree(party);
    }
}

// The words Platinum's lines for a purchase's answer name: the Pokémon (0) and the item it holds or got (1), or, for a rank up,
// the player (5)
static void ResultWords(PlatCastle *castle, WordSet *words, GameData *gameData, u32 kind, u8 slot) {
    if (kind == PLATCASTLE_BUY_RANK_HEALING || kind == PLATCASTLE_BUY_RANK_RENTALS || kind == PLATCASTLE_BUY_RANK_INFO) {
        copyVarForText(words, 5, GetGameDataPlayerInfo(gameData));
    } else if (kind >= PLATCASTLE_BUY_IDENTIFY && kind < PLATCASTLE_BUY_PASS) {
        WordSet_LoadSpeciesName(words, 0, castle->opponentMons[slot < PLATCASTLE_MAX_PARTY ? slot : 0].species);
    } else if (kind < PLATCASTLE_BUY_IDENTIFY) {
        setPartyPokemonSpeciesNameToStrbuf(words, 0, CastleMon(castle, slot));
        loadItemNameToStrbuf(words, 1, PokeParty_GetParam(CastleMon(castle, slot), PKM_PARAM_ITEM, NULL));
    }
}

// ---------------------------------------------------------------- the lobby (ScrCmd_CallBattleCastleLobbyFunction)
static BOOL IsBanned(u16 species) {
    u32 i;

    for (i = 0; i < NELEMS(sBanlist); i++) {
        if (species == sBanlist[i]) {
            return TRUE;
        }
    }
    return species > NATIONAL_DEX_COUNT;                    // (Black 2's own species: not Platinum's)
}

// sub_02049EC4(count, save, FALSE): enough Pokémon that aren't Eggs or banned, with `count` of different species among them
// (the held items aren't compared: its last argument is FALSE)
static BOOL CheckPartyEligible(PokeParty *party, u16 count) {
    u16 species[6];
    u8 i, j, numEligible = 0, distinct = 0;
    u8 partyCount = (u8)PokeParty_GetPkmCount(party);
    PartyPkm *pkm;

    if (partyCount < count) {
        return FALSE;
    }
    for (i = 0; i < partyCount; i++) {
        pkm = PokeParty_GetPkm(party, i);
        if (PokeParty_GetParam(pkm, PKM_PARAM_IS_EGG, NULL) || IsBanned(PokeParty_GetParam(pkm, PKM_PARAM_SPECIES, NULL))) {
            continue;
        }
        species[numEligible++] = PokeParty_GetParam(pkm, PKM_PARAM_SPECIES, NULL);
    }
    for (i = 0; i < numEligible; i++) {
        for (j = 0; j < i; j++) {
            if (species[j] == species[i]) {
                break;
            }
        }
        distinct += j == i;
    }
    return numEligible >= count && distinct >= count;
}

// ---------------------------------------------------------------- the ops
BOOL PlatCastle_Op(VM *vm, FieldScriptEnv *env, u32 op) {
    GameSystem *gsys = FieldScriptEnv_GetGameSystem(env);
    GameData *gameData = GSYS_GetGameData(gsys);
    SaveControl *save = GameData_GetSaveControl(gameData);
    ScriptWork *script = FieldScriptEnv_GetScriptWork(env);
    WordSet *words = ScriptWork_GetWordSet(script);
    PlatCastleWork *work = GetWork(save);
    PlatCastle *castle = &work->castle;
    BOOL ready = castle->magic == PLATCASTLE_WORK_MAGIC && gPlatCastleTable.magic == PLATCASTLE_TABLE_MAGIC;
    u16 a, b, c, d, e;
    u16 *var;
    BtlSetup *setup;
    MsgData *msg;
    StrBuf *line;
    PokeParty *party;
    u8 i;

    sGameData = gameData;
    switch (op) {
    case PLATCASTLE_OP_INIT:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        d = ScriptReadAny(vm, env);
        e = ScriptReadAny(vm, env);
        if (gPlatCastleTable.magic != PLATCASTLE_TABLE_MAGIC) {
            break;
        }
        work->screenParty = NULL;
        castle->lcrng = GFL_RandomLC(0xffffffff);          // the challenge's own LCRNG, seeded once
        PlatCastle_Init(castle, &work->save, save, a, (u8)b, (u8)c, (u8)d, (u8)e);
        break;
    case PLATCASTLE_OP_LOAD_ROUND:
        a = ScriptReadAny(vm, env);
        if (ready) {
            PlatCastle_LoadTrainersForRound(castle, &work->save, a);
        }
        break;
    case PLATCASTLE_OP_FUNCTION:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        if (!ready) {
            *var = 0;
            break;
        }
        switch (a) {
        case PLATCASTLE_FN_RESET_SYSTEM:                    // the rest: saved, then the game starts again
            OS_ResetSystem(0);
            break;
        case PLATCASTLE_FN_RESTORE_HELD_ITEMS:              // (the field party's own: Platinum's castle party is a copy)
            party = GameData_GetParty(gameData);
            for (i = 0; i < PLATCASTLE_PARTY_SOLO; i++) {
                PokeParty_SetParam(PokeParty_GetPkm(party, castle->partySlots[i]), PKM_PARAM_ITEM, castle->savedHeldItems[i]);
            }
            break;
        case PLATCASTLE_FN_GET_OPPONENT_OBJECT_ID:          // the Trainer's walker code
            *var = PearlB2_TowerObjCode(TrainerClass(castle->trainerIDs[castle->currentBattle + b * PLATCASTLE_BATTLES_PER_ROUND]));
            break;
        case PLATCASTLE_FN_INIT_COMM_MANAGER:               // the link (closed), the emblem's picture (the room's), the
        case PLATCASTLE_FN_UPDATE_EMBLEM_FRAME:             // Trainers' data (loaded where the line and the battle need it)
        case PLATCASTLE_FN_LOAD_TRAINERS:
            break;
        default:
            PlatCastle_Function(castle, &work->save, save, (u8)a, (u8)b, (u8)c, var);
            break;
        }
        break;
    case PLATCASTLE_OP_FREE:
        if (work->screenParty != NULL) {
            GFL_HeapFree(work->screenParty);
            work->screenParty = NULL;
        }
        castle->magic = 0;
        break;
    case PLATCASTLE_OP_SETUP_FIRST:
        if (ready) {
            PlatCastle_SetupFirstOpponentsParty(castle);
        }
        break;
    case PLATCASTLE_OP_SETUP_NEXT:
        if (ready) {
            PlatCastle_SetupNextOpponentsParty(castle);
        }
        break;
    case PLATCASTLE_OP_START_BATTLE:
        if (!ready) {
            break;
        }
        setup = MakeBattle(castle, gsys);
        PearlB2_Castle_SetBattle(setup);
        ScriptWork_CallEvent(script, EventBSubwayBattleCall_Create(gsys, GSYS_GetField(gsys), setup));
        return TRUE;
    case PLATCASTLE_OP_CLEANUP_BATTLE:                      // FrontierScrCmd_BattleCastle_CleanupBattle
        setup = PearlB2_Castle_SetBattle(NULL);
        if (setup != NULL) {
            if (ready) {
                for (i = 0; i < castle->playerCount && i < PokeParty_GetPkmCount(setup->party[0]); i++) {
                    copyPartyPkm(PokeParty_GetPkm(setup->party[0], i), CastleMon(castle, i));
                }
                castle->wonBattle = setup->result == BTL_RESULT_VICTORY;      // CheckPlayerWonBattle
            }
            BtlSetup_Free(setup);
        }
        break;
    case PLATCASTLE_OP_CHECK_WON:
        var = ScriptReadVar(vm, env);
        *var = ready ? (u16)castle->wonBattle : 0;
        break;
    case PLATCASTLE_OP_TRAINER_WORD:
        a = ScriptReadAny(vm, env);                        // the word
        b = ScriptReadAny(vm, env);                        // the Trainer's slot (0, 1)
        c = ScriptReadAny(vm, env);                        // the line (0 the intro)
        if (!ready) {
            break;
        }
        msg = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TRAINER_LINES, CASTLE_HEAP);
        line = GFL_MsgDataLoadStrbufNew(msg, castle->trainerIDs[castle->currentBattle + b * PLATCASTLE_BATTLES_PER_ROUND] * 3 + c);
        GFL_WordSetSetStrbuf(words, a, line, 0, TRUE, 0);
        GFL_StrBufFree(line);
        GFL_MsgDataFree(msg);
        break;
    case PLATCASTLE_OP_GET_CP:
        a = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = PlatCastle_GetCurrentCP(save, (u8)a);
        break;
    case PLATCASTLE_OP_SPEND_CP:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        PlatCastle_SpendCastlePoints(save, (u8)a, b);
        break;
    case PLATCASTLE_OP_RECEIVE_CP:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        PlatCastle_ReceiveCastlePoints(save, (u8)a, b);
        break;
    case PLATCASTLE_OP_LOBBY:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = 0;
        switch (a) {
        case PLATCASTLE_LOBBY_CHECK_PARTY_ELIGIBLE:
            *var = CheckPartyEligible(GameData_GetParty(gameData), b);
            break;
        case PLATCASTLE_LOBBY_CHECK_STREAK_ACTIVE:
            *var = b == PLATCASTLE_MULTI_WFC ? PlatCastle_GetStat(save, PLATCASTLE_STAT_WFC_STREAK_ACTIVE) :
                                               (u16)PlatCastle_GetStreakFlag(save, b);
            break;
        case PLATCASTLE_LOBBY_DELETE_ACTIVE_STREAK:
            PlatCastle_ClearActiveStreak(save, (u8)b);
            break;
        }
        break;
    case PLATCASTLE_OP_DELETE_STREAK:
        a = ScriptReadAny(vm, env);
        PlatCastle_ClearActiveStreak(save, (u8)a);
        break;
    case PLATCASTLE_OP_SELF_SCREEN:                         // OpenBattleCastleSelfApp's Pokémon selection
        if (!ready || gPlatCastleTable.pickRegulation == 0) {
            break;
        }
        if (work->screenParty != NULL) {
            GFL_HeapFree(work->screenParty);
        }
        party = PokeParty_Create(CASTLE_HEAP);
        for (i = 0; i < castle->playerCount; i++) {
            PokeParty_AddPkm(party, CastleMon(castle, i));
        }
        work->screenParty = party;
        MI_CpuFill8(work->picked, 0, sizeof(work->picked));
        work->choice = 0;
        work->screenResult = 0;
        ScriptWork_CallEvent(script, EventBtlInstPokeSelect_Create(gsys, castle->challengeType == PLATCASTLE_DOUBLE, PICK_MODE,
                                                                   gPlatCastleTable.pickRegulation, party, work->picked,
                                                                   &work->choice, &work->screenResult, NULL));
        return TRUE;
    case PLATCASTLE_OP_SELF_PICK:
        var = ScriptReadVar(vm, env);
        *var = NO_SLOT;
        if (work->screenParty != NULL) {
            GFL_HeapFree(work->screenParty);
            work->screenParty = NULL;
            if (work->screenResult == 0 && work->choice != 7 && work->choice != 8 && work->picked[0] >= 1 &&
                work->picked[0] <= castle->playerCount) {
                *var = work->picked[0] - 1;
                castle->selectedAppSlot = *var;
            }
        }
        break;
    case PLATCASTLE_OP_ASK:
    case PLATCASTLE_OP_BUY:
        a = ScriptReadAny(vm, env);                        // the purchase
        b = ScriptReadAny(vm, env);                        // the Pokémon (0-2)
        c = ScriptReadAny(vm, env);                        // a rental list's row (Ask: 0xffff the menu's entry)
        var = ScriptReadVar(vm, env);
        if (!ready || a >= PLATCASTLE_BUY_KINDS || b >= PLATCASTLE_PARTY_SOLO) {
            *var = PLATCASTLE_RESULT_NOT_ENOUGH_CP;
            break;
        }
        if (op == PLATCASTLE_OP_ASK) {
            *var = (u16)PlatCastle_Ask(castle, save, a, (u8)b, c, &d);
            WordSetNumber(words, 0, d, 4, 0, TRUE);
            if (*var == PLATCASTLE_RESULT_KNOWN) {
                ResultWords(castle, words, gameData, a, (u8)b);
            }
        } else {
            *var = (u16)PlatCastle_Buy(castle, save, a, (u8)b, c);
            ResultWords(castle, words, gameData, a, (u8)b);
        }
        break;
    case PLATCASTLE_OP_RENTAL_LIST:
        a = ScriptReadAny(vm, env);
        if (ready) {
            AddRentalRows(castle, save, env, a != 0);
        }
        break;
    case PLATCASTLE_OP_OPPONENT_LIST:
        a = ScriptReadAny(vm, env);
        if (ready) {
            AddOpponentRows(castle, env, a);
        }
        break;
    case PLATCASTLE_OP_MON_WORDS:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        if (ready && b < PLATCASTLE_PARTY_SOLO) {
            MonWords(castle, words, (u8)a, (u8)b, c);
        }
        break;
    case PLATCASTLE_OP_INFO:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = 0;
        if (!ready || b >= PLATCASTLE_MAX_PARTY) {
            break;
        }
        switch (a) {
        case 0:
        case 1:
        case 2:
            *var = PlatCastle_GetRank(save, castle->challengeType, (u8)a);
            break;
        case 3:
            *var = castle->appIdentityUnlocked[b];
            break;
        case 4:
            *var = castle->appStatsUnlocked[b];
            break;
        case 5:
            *var = castle->appMovesUnlocked[b];
            break;
        case 6:
            *var = castle->levelAdjustments[b];
            break;
        case 7:
            *var = castle->playerCount;
            break;
        }
        break;
    case PLATCASTLE_OP_CP_WORD:
        a = ScriptReadAny(vm, env);
        WordSetNumber(words, a, ready ? PlatCastle_GetCurrentCP(save, castle->challengeType) : 0, 4, 1, TRUE);
        break;
    case PLATCASTLE_OP_LOBBY_SELECT:                        // the lobby's BC_LOBBY_FUNC_SELECT_POKEMON (SelectBattleCastleChallengers)
        a = ScriptReadAny(vm, env);
        if (gPlatCastleTable.magic != PLATCASTLE_TABLE_MAGIC) {
            work->choice = 7;                               // (no Castle: as the screen left)
            break;
        }
        MI_CpuFill8(work->picked, 0, sizeof(work->picked));
        work->choice = 0;
        work->screenResult = 0;
        ScriptWork_CallEvent(script, EventBtlInstPokeSelect_Create(gsys, a == PLATCASTLE_DOUBLE, PICK_MODE,
                                                                   gPlatCastleTable.entryRegulation[a == PLATCASTLE_MULTI],
                                                                   GameData_GetParty(gameData), work->picked, &work->choice,
                                                                   &work->screenResult, NULL));
        return TRUE;
    case PLATCASTLE_OP_SELECTED_SLOTS:                      // ScrCmd_GetBattleCastleSelectedSlots: the slots from 0
        for (i = 0; i < 3; i++) {
            var = ScriptReadVar(vm, env);
            if (work->screenResult != 0 || work->choice == 7 || work->choice == 8 || work->picked[0] == 0) {
                if (i == 0) {
                    *var = NO_SLOT;                         // PARTY_SLOT_NONE: the screen was left
                }
            } else {
                *var = work->picked[i] > 0 ? work->picked[i] - 1 : 0;      // (Platinum's third is 0 when a Multi picks two)
            }
        }
        break;
    default:
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    return FALSE;
}

#endif
