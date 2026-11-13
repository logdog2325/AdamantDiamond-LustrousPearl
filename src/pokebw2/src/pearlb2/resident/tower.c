#include "pearlb2.h"
#include "pearlb2/ext_cmd.h"
#include "pearlb2/tower.h"
#include "pearlb2/plat_frontier.h"
#include "types.h"
#include "battle/regulation.h"
#include "constants/arc.h"
#include "field/battle_facility.h"
#include "field/bsubway_scr.h"
#include "field/field.h"
#include "field/field_actor.h"
#include "field/field_msgbg.h"
#include "field/field_script.h"
#include "field/player_state.h"
#include "gfl/heap.h"
#include "gfl/msg.h"
#include "gfl/std.h"
#include "gfl/str.h"
#include "pml/poke_party.h"
#include "save/bsubway_save.h"
#include "save/player_info.h"
#include "save/records.h"
#include "save/save_control.h"
#include "save/wbt_save.h"
#include "system/game_data.h"
#include "system/game_system.h"
#include "system/vm.h"
#include "system/wordset.h"

// Pearl's Battle Tower on Black 2's Battle Subway (PearlB2's notes/BATTLE_ZONE.md).

#if PEARLB2

// The shop screen's "N BP" line
#define TOWER_BP_TEXT_FILE 613
#define TOWER_BP_TEXT_LINE 26
#define TOWER_BP_MAX 9999

// Pearl's trainer ids (battle/b_tower/btdtr.narc, as arcs 211/212 hold them here)
#define TOWER_PARTNER_FIRST 300
#define TOWER_PALMER_SILVER 305
#define TOWER_PALMER_GOLD 306

// A partner's id travels with its team in the save's team config: natures[1], above the nature (0-24, 5 bits)
#define TOWER_PARTNER_SHIFT 5

#define MON_PER_PARTNER 2

// Pearl's arm9 tables (sBattleTowerTrainerRangesPerRoom, sBattleTowerBossTrainerRangesPerRoom)
static const u16 sTrainerRanges[8][2] = {
    { 0, 99 }, { 80, 119 }, { 100, 139 }, { 120, 159 }, { 140, 179 }, { 160, 199 }, { 180, 219 }, { 200, 299 },
};
static const u16 sLastTrainerRanges[8][2] = {
    { 100, 119 }, { 120, 139 }, { 140, 159 }, { 160, 179 }, { 180, 199 }, { 200, 219 }, { 220, 239 }, { 200, 299 },
};
// The partners' sprites, in Pearl's partner order (data/pearl_sprite_map.json)
static const u16 sPartnerCodes[PEARLB2_TOWER_PARTNERS] = { 373, 300, 289, 99, 107 };

#pragma explicit_zero_data on
const PearlB2TowerSprite *gPearlB2TowerSprites = NULL;
u32 gPearlB2TowerSpriteCount = 0;
#pragma explicit_zero_data off

// Pearl's Exchange Service Corner, as in the dump: {item, BP}. 26 prizes, then 15 TMs. A TM is the item that teaches
// Pearl's move here (PearlB2's b2tools/tm_audit.py pearl_item): Pearl's TM59 (386) Dragon Pulse is item 518 (TM109),
// Black 2's own TM59 being Incinerate (1.0.1); the other 14 have Pearl's move under Pearl's number
#define EXCHANGE_TMS_FIRST 26
static const u16 sExchange[41][2] = {
    { 46, 1 },    { 49, 1 },    { 47, 1 },    { 52, 1 },    { 48, 1 },    { 45, 1 },    { 289, 16 },
    { 290, 16 },  { 291, 16 },  { 292, 16 },  { 293, 16 },  { 294, 16 },  { 272, 16 },  { 273, 16 },
    { 214, 32 },  { 271, 32 },  { 213, 48 },  { 220, 48 },  { 230, 48 },  { 232, 48 },  { 266, 48 },
    { 275, 48 },  { 287, 48 },  { 326, 48 },  { 327, 48 },  { 50, 48 },   { 333, 32 },  { 400, 32 },
    { 388, 32 },  { 372, 32 },  { 367, 40 },  { 358, 40 },  { 335, 48 },  { 331, 48 },  { 408, 64 },
    { 357, 64 },  { 380, 64 },  { 363, 80 },  { 518, 80 },  { 398, 80 },  { 353, 80 },
};

// Pearl's trophies for a win streak (1.0.1; pokediamond unk_0205FA2C.c sub_0205FE10): which were given, as bits of the
// subway's score flags that Black 2 never uses (BSubwayScoreData_SetFlag takes ids 0-10), as Pearl keeps them in its
// Tower's frontier data
#define TROPHY_FLAG_SHIFT 24
#define TROPHY_COUNT 3

static BSubwayTeamConfig sPartnerConfigs[PEARLB2_TOWER_PARTNERS];
static u16 sPartnerSpecies[PEARLB2_TOWER_PARTNERS][MON_PER_PARTNER];
static u16 sPartnerMoves[PEARLB2_TOWER_PARTNERS][MON_PER_PARTNER];
static u8 sPartnerFailed[PEARLB2_TOWER_PARTNERS];
static u8 sPartner;

// Pearl's BattleTower_GetTrainerIDForRoomAndOpponentNum: Palmer ends rooms 3 and 7 of the Single Battle Room
u16 PearlB2_TowerDrawTrainerNo(BSubwayScrWork *bsw, u16 level, u8 index, u32 mode, u8 side) {
    const u16 *range;

    if (mode == 0 && index == 6) {
        if (level == 2) {
            return TOWER_PALMER_SILVER;
        }
        if (level == 6) {
            return TOWER_PALMER_GOLD;
        }
    }
    if (level >= 7) {
        range = sTrainerRanges[7];
    } else if (index == 6) {
        range = sLastTrainerRanges[level];
    } else {
        range = sTrainerRanges[level];
    }
    return range[0] + randFFFFFFFFdivFFFF(bsw) % (range[1] - range[0] + 1);
}

// The opponent's field sprite: Pearl's by its class, else Black 2's
u16 PearlB2_TowerObjCode(u32 trainerClass) {
    u32 i;

    for (i = 0; i < gPearlB2TowerSpriteCount; i++) {
        if (gPearlB2TowerSprites[i].trainerClass == trainerClass) {
            return gPearlB2TowerSprites[i].objCode;
        }
    }
    return BtlInst_GetTrainerClassObjCode(trainerClass);
}

// s0040_MoneyWinDisp with the BP, or the shown window printed again
static void Tower_PrintBP(FieldScriptEnv *env, BOOL create, u16 x, u16 y) {
    GameSystem *gsys = FieldScriptEnv_GetGameSystem(env);
    GameData *gameData = GSYS_GetGameData(gsys);
    Field *field = GSYS_GetField(gsys);
    MoneyWin *window = Field_GetMoneyWin(field);
    ScriptWork *work = FieldScriptEnv_GetScriptWork(env);
    WordSet *wordSet = ScriptWork_GetWordSet(work);
    StrBuf *text = ScriptWork_GetAltStrBuf(work);
    HeapID heapId = Field_GetHeapID(field);
    MsgData *msgData = GFL_MsgSysLoadData(FALSE, ARCID_SCRIPT_MESSAGE, TOWER_BP_TEXT_FILE, heapId);
    StrBuf *strbuf = GFL_StrBufCreate(0x80, heapId);
    BSubwayScoreData *score = SaveControl_GetBlockPtr(GameData_GetSaveControl(gameData), SAVE_BLOCK_BSUBWAY_SCORE);

    if (create) {
        if (window != NULL) {
            MsgBGPrinter_DeleteMsgWin(window);
        }
        window = FieldMsgBG_CreateMoneyWin(Field_GetMsgBGSys(field), msgData, x - 9, y, 9, 2);
        Field_SetMoneyWin(field, window);
    }
    WordSetNumber(wordSet, 0, BSubwayScoreData_GetBattlePoints(score), 4, 1, TRUE);
    GFL_MsgDataLoadStrbuf(msgData, TOWER_BP_TEXT_LINE, text);
    GFL_WordSetFormatStrbuf(wordSet, strbuf, text);
    if (window != NULL) {
        MsgBGPrinter_MsgWinPrintStr(window, 0, 0, strbuf);
    }
    GFL_StrBufFree(strbuf);
    GFL_MsgDataFree(msgData);
}

// Black 2's own regulations of its Single, Double and Multi Trains (BSubway_GetModeRegulation)
static u16 Tower_CheckParty(GameData *gameData, u32 mode) {
    Regulation *regulation = PokeRegulation_LoadNew(20 + mode, HEAPID_GAMEEVENT);
    u32 check = PokeRegulation_CheckPartyCanEnter(regulation, GameData_GetParty(gameData));

    GFL_HeapFree(regulation);
    return check <= 1 ? 1 : 0;
}

// Pearl draws all five partners' teams when the player enters the partner room (sub_0204A97C). Black 2's work keeps
// three, so slot 0 is made from the chosen one's config (Tower_SetPartner) and only the configs stay here
static void Tower_MakePartners(BSubwayScrWork *bsw) {
    BSubwayTrainer *trainer = &bsw->unk2C8[0];
    s32 p, i;

    for (p = 0; p < PEARLB2_TOWER_PARTNERS; p++) {
        sPartnerFailed[p] = BsubwayScr_CreateTrainer(bsw, trainer, TOWER_PARTNER_FIRST + p, bsw->memberCount,
                                                     bsw->memberSpecies, bsw->memberItems, &sPartnerConfigs[p],
                                                     bsw->heapId);
        for (i = 0; i < MON_PER_PARTNER; i++) {
            sPartnerSpecies[p][i] = trainer->pokemon[i].species;
            sPartnerMoves[p][i] = trainer->pokemon[i].moves[0];
        }
    }
}

static void Tower_SetPartner(BSubwayScrWork *bsw, u32 partner) {
    BSubwayTeamConfig *config = &bsw->teamConfigs[0];

    sPartner = partner;
    *config = sPartnerConfigs[partner];
    config->natures[1] = (u8)((config->natures[1] & ((1 << TOWER_PARTNER_SHIFT) - 1)) | (partner << TOWER_PARTNER_SHIFT));
    bsw->unkC_5 = 0;
    bsw->unk664[0] = sPartnerFailed[partner];
    BsubwayScr_CreatePartnerMons(bsw, &bsw->unk2C8[0], TOWER_PARTNER_FIRST + partner, sPartnerFailed[partner], config,
                                 bsw->heapId);
}

static void Tower_ResumePartner(BSubwayScrWork *bsw) {
    BSubwayTeamConfig *config = &bsw->teamConfigs[0];

    if (bsw->playMode == 2) {
        sPartner = config->natures[1] >> TOWER_PARTNER_SHIFT;
        bsw->unk664[0] = (u8)BSubwayPlayData_GetData(bsw->unk70, BSUBWAY_PLAY_UNK0_0, NULL);
        BsubwayScr_CreatePartnerMons(bsw, &bsw->unk2C8[0], TOWER_PARTNER_FIRST + sPartner, bsw->unk664[0], config,
                                     bsw->heapId);
    }
}

// The PWT's left desk: Black 2 opens it with a win of its story tournament, which is never offered here
u16 PearlB2_WbtOpenCount(void *save, int index) {
    u16 count = WbtSave_GetCount(save, index);

    if (index == 18 && count == 0) {
        count = 1;
    }
    return count;
}

BOOL PearlB2_Ext_Tower(VM *vm, FieldScriptEnv *env, u32 sub) {
    GameData *gameData = FieldScriptEnv_GetGameData(env);
    SaveControl *save = GameData_GetSaveControl(gameData);
    BSubwayScoreData *score = SaveControl_GetBlockPtr(save, SAVE_BLOCK_BSUBWAY_SCORE);
    BSubwayScrWork *bsw = GameData_GetBSubwayScrWork(gameData);
    u16 a, b;
    u16 *var, *var2;

    switch (sub) {
    case EXT_TOWER_BP_GET:
        var = ScriptReadVar(vm, env);
        *var = BSubwayScoreData_GetBattlePoints(score);
        break;
    case EXT_TOWER_BP_ADD:
        a = ScriptReadAny(vm, env);
        BSubwayScoreData_AddBattlePoints(score, a);
        break;
    case EXT_TOWER_BP_SUB:
        a = ScriptReadAny(vm, env);
        BSubwayScoreData_SubBattlePoints(score, a);
        break;
    case EXT_TOWER_BP_CHECK:
        a = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = BSubwayScoreData_GetBattlePoints(score) >= a;
        break;
    case EXT_TOWER_BP_WINDOW:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        Tower_PrintBP(env, TRUE, a, b);
        break;
    case EXT_TOWER_BP_UPDATE:
        Tower_PrintBP(env, FALSE, 0, 0);
        break;
    case EXT_TOWER_CHECK_PARTY:
        a = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        if (a == 255) {
            a = bsw != NULL ? bsw->playMode : 0;
        }
        *var = Tower_CheckParty(gameData, a);
        break;
    case EXT_TOWER_IS_NULL:
        var = ScriptReadVar(vm, env);
        *var = bsw == NULL;
        break;
    case EXT_TOWER_MAKE_PARTNERS:
        Tower_MakePartners(bsw);
        break;
    case EXT_TOWER_PARTNER_MON:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        var2 = ScriptReadVar(vm, env);
        *var = sPartnerSpecies[a][b];
        *var2 = sPartnerMoves[a][b];
        break;
    case EXT_TOWER_SET_PARTNER:
        a = ScriptReadAny(vm, env);
        Tower_SetPartner(bsw, a);
        break;
    case EXT_TOWER_GET_PARTNER:
        var = ScriptReadVar(vm, env);
        *var = sPartner;
        break;
    case EXT_TOWER_PARTNER_CODE:
        var = ScriptReadVar(vm, env);
        *var = sPartnerCodes[sPartner];
        break;
    case EXT_TOWER_RESUME_PARTNER:
        Tower_ResumePartner(bsw);
        break;
    case EXT_TOWER_EXCHANGE:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        var2 = ScriptReadVar(vm, env);
        if (a != 0) {
            b += EXCHANGE_TMS_FIRST;
        }
        *var = sExchange[b][0];
        *var2 = sExchange[b][1];
        break;
    case EXT_TOWER_PLAYER_CODE:
        var = ScriptReadVar(vm, env);
        *var = FieldPlayer_GetObjCodeByForme(getTrainerGender(&GameData_GetPlayerState(gameData)->playerInfo), 0);
        break;
    case EXT_TOWER_BEST_STREAK: {
        // the longest win streak of any room (Pearl's record 0x35, its Tower's best)
        u32 i, best = 0;

        var = ScriptReadVar(vm, env);
        for (i = 0; i < BSUBWAY_SCORE_MODE_MAX; i++) {
            if (BSubwayScoreData_GetMaxStreak(score, i) > best) {
                best = BSubwayScoreData_GetMaxStreak(score, i);
            }
        }
        *var = (u16)best;
        break;
    }
    case EXT_TOWER_TROPHY:
        // op (0: was trophy n given?, 1: it is given now), trophy 0-2 (Bronze, Silver, Gold), var
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = 0;
        if (b < TROPHY_COUNT) {
            if (a == 1) {
                score->flags |= 1u << (TROPHY_FLAG_SHIFT + b);
            }
            *var = (u16)((score->flags >> (TROPHY_FLAG_SHIFT + b)) & 1);
        }
        break;
    case EXT_TOWER_ACTOR_VISIBLE: {
        Field *field = GSYS_GetField(FieldScriptEnv_GetGameSystem(env));
        FieldActor *actor;

        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        actor = field != NULL ? FindFieldActor(Field_GetActorSystem(field), a) : NULL;
        if (actor != NULL) {
            SetActorHidden(actor, b == 0);
        }
        break;
    }
    case EXT_TOWER_FRONTIER:
        return PearlB2_Ext_Frontier(vm, env);
    default:
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    return FALSE;
}

#endif
