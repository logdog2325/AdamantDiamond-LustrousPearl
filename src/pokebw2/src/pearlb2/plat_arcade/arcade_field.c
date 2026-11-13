#include "pearlb2.h"
#include "pearlb2/plat_arcade.h"
#include "pearlb2/plat_frontier.h"
#include "pearlb2/tower.h"
#include "types.h"
#include "battle/btl_result.h"
#include "battle/btl_setup.h"
#include "constants/arc.h"
#include "constants/pokemon.h"
#include "constants/sound.h"
#include "constants/text_banks.h"
#include "field/battle_facility.h"
#include "field/bsubway_scr.h"
#include "field/event_battle.h"
#include "field/field.h"
#include "field/field_event.h"
#include "field/field_msgbg.h"
#include "field/field_script.h"
#include "field/fld_btl_inst_event.h"
#include "gfl/arc.h"
#include "gfl/bmp.h"
#include "gfl/bmpwin.h"
#include "gfl/heap.h"
#include "gfl/key.h"
#include "gfl/msg.h"
#include "gfl/random.h"
#include "gfl/sound.h"
#include "gfl/std.h"
#include "gfl/str.h"
#include "gfl/touchpanel.h"
#include "nitro/os.h"
#include "pml/personal.h"
#include "pml/poke_party.h"
#include "save/save_control.h"
#include "system/game_data.h"
#include "system/game_event.h"
#include "system/game_system.h"
#include "system/pms_data.h"
#include "system/printsys.h"
#include "system/vm.h"
#include "system/wordset.h"

// PearlB2: Platinum's Battle Arcade on the field (include/pearlb2/plat_arcade.h; notes/PLATINUM_FRONTIER.md "The Battle Arcade").
// Overlay 381, at the gimmick overlays' address: the resident PearlB2_Ext_Arcade loads it for one op and unloads it before the
// op returns; the board's op has Black 2's GameEvent_CreateOverlayDelegate load it for as long as the board runs. The battle and
// the lobby's party screen are Black 2's own events (overlay 12), whose data is in the challenge's work or on the event heap.
// - The rules are arcade_rules.c's (Platinum's, checked on the host against Platinum's C, its game board's app too).
// - The player's party: three copies of the field party's Pokémon (Black 2's party Pokémon) in the challenge's work, as
//   Platinum's BattleArcade keeps its playersParty: no held item, Level 50 at most; the field party isn't touched. The board's
//   effects change them (HP, status, held item, level); the battle copies them, then they are healed (BattleArcade_SetupBattle);
//   after it they keep the held items as the battle left them (the resident hook) and the stats they had when the board opened.
// - The opponent's party: each Pokémon as its set was made (PlatArcadeMon) plus what the board and the heal changed (HP, status,
//   item, level: PlatArcadeOpponent); a Black 2 Pokémon is made of it (BtlInst_MakeParty) when a value needs one and for the
//   battle.
// - The board: a window of the 16 panels at the top of the screen, each the name of its effect (the room's text: 32 lines from
//   the op's first line), the cursor a panel drawn light on dark, at Platinum's frames: the panels count 3, 2, 1 (24 frames each,
//   after 10), then the cursor runs at the board's speed (sCursorMoveFrames, the field's 30 frames a second, as the app's) until A
//   or a touch stops it or 30 seconds pass; every panel then shows the effect for 30 frames. The decisions are arcade_rules.c's
//   (PlatArcade_RouletteTick each frame), so the panels, the cursor and the effect are Platinum's for the same frame.
// - The Frontier Trainer of a battle: his name, class and lines from the Subway's Trainer archive, which holds Platinum's
//   Frontier Trainers (patches/battle_tower.py).

#if PEARLB2

#define ARCADE_HEAP HEAPID_GAMEEVENT
#define SET_ARC 0xd3                    // a/2/1/1: the Subway's sets, Platinum's 0-950 (patches/battle_tower.py)
#define TRAINER_ARC 0xd4                // a/2/1/2: the Subway's Trainers, file id + 1
#define TRAINER_NAMES 0xf               // system text 15: their names
#define TRAINER_LINES 0x178             // system text 376: their lines, three each
#define PICK_MODE 0x17                  // the party list's battle-entry mode (the Trial House's)
#define FACILITY_AI 0x80                // the bit Black 2's facility Trainers have besides the three AI levels (0x87)
#define NO_SLOT 0xff
#define NATIONAL_DEX_COUNT 493
#define ITEM_NONE 0
#define B2_TYPE_FIRE 9                  // Black 2's types from Fire on are Platinum's less one (Platinum's 9 is the Mystery type)
// Black 2's battle weather (constants/battle.h BTL_WEATHER_*), which a battle starts with from its setup (BtlServerFlow_StartBattle)
#define B2_WEATHER_SUN 1
#define B2_WEATHER_RAIN 2
#define B2_WEATHER_HAIL 3
#define B2_WEATHER_SANDSTORM 4
// Black 2's party status (a condition of constants/battle.h, the battle's own for the party's): one value, no sleep turns
#define B2_STATUS_PARALYSIS 1
#define B2_STATUS_SLEEP 2
#define B2_STATUS_FREEZE 3
#define B2_STATUS_BURN 4
#define B2_STATUS_POISON 5

typedef char PlatArcadeCheckWorkSize[sizeof(PlatArcadeWork) <= sizeof(((PearlB2FrontierSave *)0)->challenge) ? 1 : -1];
typedef char PlatArcadeCheckPkmSize[PLATARCADE_PKM_SIZE == sizeof(PartyPkm) ? 1 : -1];

// Filled by PearlB2's b2tools/patches/platinum_arcade.py in a Platinum build (in this overlay's .data, so in its file)
#pragma explicit_zero_data on
PlatArcadeTable gPlatArcadeTable = { 0 };
#pragma explicit_zero_data reset

// Platinum's sBattleFrontierBanlist (pokemon.c)
static const u16 sBanlist[] = { 150, 151, 249, 250, 251, 382, 383, 384, 385, 386, 483, 484, 487, 489, 490, 491, 492, 493 };

// The field party, for the op running (the rules' calls below read it)
static GameData *sGameData;

// ---------------------------------------------------------------- the records, through the core (resident/plat_frontier.c)
u16 PlatArcade_GetStat(void *records, u32 stat) {
    return PearlB2_Frontier_GetStat(records, stat);
}

void PlatArcade_SetStat(void *records, u32 stat, u16 value) {
    PearlB2_Frontier_SetStat(records, stat, value);
}

u32 PlatArcade_GetStreakFlag(void *records, u32 challengeType) {
    return (PearlB2_Frontier_GetSave(records)->streakFlags[FRONTIER_FACILITY_ARCADE] >> challengeType) & 1;
}

void PlatArcade_SetStreakFlag(void *records, u32 challengeType, u32 value) {
    u8 *flags = &PearlB2_Frontier_GetSave(records)->streakFlags[FRONTIER_FACILITY_ARCADE];

    if (value >= 1) {
        *flags |= 1 << challengeType;
    } else {
        *flags &= 0xff ^ (1 << challengeType);
    }
}

static PlatArcadeWork *GetWork(SaveControl *save) {
    return (PlatArcadeWork *)PearlB2_Frontier_GetSave(save)->challenge;
}

static PlatArcadeWork *WorkOf(PlatArcade *arcade) {
    return (PlatArcadeWork *)((u8 *)arcade - (u32) & ((PlatArcadeWork *)0)->arcade);
}

// ---------------------------------------------------------------- the conversions
// Platinum's MON_CONDITION_* (sleep: its turns, 1-7) to Black 2's one value: the battle draws a sleeping Pokémon's turns itself
static u32 StatusToB2(u32 status) {
    if (status & 7) {
        return B2_STATUS_SLEEP;
    } else if (status & (PLATARCADE_STATUS_POISON | (1 << 7))) {
        return B2_STATUS_POISON;
    } else if (status & PLATARCADE_STATUS_BURN) {
        return B2_STATUS_BURN;
    } else if (status & PLATARCADE_STATUS_FREEZE) {
        return B2_STATUS_FREEZE;
    } else if (status & PLATARCADE_STATUS_PARALYSIS) {
        return B2_STATUS_PARALYSIS;
    }
    return 0;
}

static u32 StatusFromB2(u32 status) {
    switch (status) {
    case B2_STATUS_PARALYSIS: return PLATARCADE_STATUS_PARALYSIS;
    case B2_STATUS_SLEEP: return 1;
    case B2_STATUS_FREEZE: return PLATARCADE_STATUS_FREEZE;
    case B2_STATUS_BURN: return PLATARCADE_STATUS_BURN;
    case 0: return 0;
    }
    return PLATARCADE_STATUS_POISON;
}

static u32 TypeFromB2(u32 type) {
    return type >= B2_TYPE_FIRE ? type + 1 : type;
}

// ---------------------------------------------------------------- the player's party (Platinum's playersParty)
static PartyPkm *ArcadeMon(PlatArcade *arcade, u8 slot) {
    return (PartyPkm *)WorkOf(arcade)->party[slot < PLATARCADE_PARTY_SOLO ? slot : 0];
}

u32 PlatArcade_FieldMonItem(PlatArcade *arcade, u8 fieldSlot) {
    (void)arcade;
    return PokeParty_GetParam(PokeParty_GetPkm(GameData_GetParty(sGameData), fieldSlot), PKM_PARAM_ITEM, NULL);
}

void PlatArcade_PartyAddFieldMon(PlatArcade *arcade, u8 fieldSlot) {
    copyPartyPkm(PokeParty_GetPkm(GameData_GetParty(sGameData), fieldSlot), ArcadeMon(arcade, arcade->playerCount));
}

static const u8 sMonParams[PLATARCADE_MON_FIELDS] = {
    PKM_PARAM_SPECIES, PKM_PARAM_SPECIES, PKM_PARAM_LEVEL, PKM_PARAM_EXP, PKM_PARAM_HP, PKM_PARAM_MAX_HP, PKM_PARAM_ATTACK,
    PKM_PARAM_DEFENSE, PKM_PARAM_SPEED, PKM_PARAM_SP_ATTACK, PKM_PARAM_SP_DEFENSE, PKM_PARAM_STATUS, PKM_PARAM_ITEM,
    PKM_PARAM_TYPE1, PKM_PARAM_TYPE2, PKM_PARAM_ABILITY,
};

static u32 PkmGet(PartyPkm *pkm, u32 field) {
    u32 value = PokeParty_GetParam(pkm, sMonParams[field], NULL);

    switch (field) {
    case PLATARCADE_MON_EXISTS: return value != 0;
    case PLATARCADE_MON_STATUS: return StatusFromB2(value);
    case PLATARCADE_MON_TYPE_1:
    case PLATARCADE_MON_TYPE_2: return TypeFromB2(value);
    }
    return value;
}

// ---------------------------------------------------------------- the Frontier's sets and Trainers
void PlatArcade_ReadSet(u16 setID, PlatArcadeSet *set) {
    GFL_ArcSysRead(set, SET_ARC, setID);
}

u16 PlatArcade_TrainerSets(u16 trainerID, u16 *sets, u16 max) {
    u16 *data = BtlInst_LoadTrainerData(TRAINER_ARC, trainerID, ARCADE_HEAP);   // class, count, the set ids
    u16 count = data[1] < max ? data[1] : max;
    u16 i;

    for (i = 0; i < count; i++) {
        sets[i] = data[2 + i];
    }
    GFL_HeapFree(data);
    return count;
}

u16 PlatArcade_SpeciesAbility(u16 species, u32 slot) {
    return (u16)PML_PersonalGetParamSingle(species, 0, slot == 0 ? PERSONAL_ABILITY_1 : PERSONAL_ABILITY_2);
}

u32 PlatArcade_BaseExpAt(u16 species, u8 level) {
    return PML_UtilGetPkmLvExp(species, 0, level);
}

static u16 TrainerClass(u16 trainerId) {
    u16 *data = BtlInst_LoadTrainerData(TRAINER_ARC, trainerId, ARCADE_HEAP);
    u16 trainerClass = data[0];

    GFL_HeapFree(data);
    return trainerClass;
}

// ---------------------------------------------------------------- the opponent's party (Platinum's opponentsParty)
static PlatArcadeOpponent *Opponent(PlatArcade *arcade, u8 slot) {
    return &WorkOf(arcade)->opponents[slot < PLATARCADE_MAX_PARTY ? slot : 0];
}

static void ToSubwayMon(const PlatArcadeMon *mon, BSubwayPokemon *pkm, MsgData *speciesNames) {
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

// Black 2 Pokémon of the opponent's first `count` (those of a set; the empty ones a resumed challenge has are left out): made at
// Level 50 (FrontierPokemon_InitPokemon), at their experience, with `apply` their HP, status and item as the board left them
static void MakeOpponents(PlatArcade *arcade, PokeParty *party, u8 count, BOOL apply) {
    BSubwayPokemon *pkms = GFL_HeapAllocate(HEAPID_TAIL(ARCADE_HEAP), sizeof(BSubwayPokemon) * PLATARCADE_MAX_PARTY, TRUE,
                                            "arcade_field.c", __LINE__);
    MsgData *speciesNames = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_SPECIES_NAMES, ARCADE_HEAP);
    PlatArcadeOpponent *o;
    PartyPkm *pkm;
    u8 i, made = 0;

    for (i = 0; i < count; i++) {
        if (Opponent(arcade, i)->mon.species != 0) {
            ToSubwayMon(&Opponent(arcade, i)->mon, &pkms[made++], speciesNames);
        }
    }
    GFL_MsgDataFree(speciesNames);
    BtlInst_MakeParty(party, pkms, PLATARCADE_MAX_LEVEL, made, ARCADE_HEAP);
    GFL_HeapFree(pkms);
    made = 0;
    for (i = 0; i < count; i++) {
        o = Opponent(arcade, i);
        if (o->mon.species == 0) {
            continue;
        }
        pkm = PokeParty_GetPkm(party, made++);
        if (o->exp != PML_UtilGetPkmLvExp(o->mon.species, o->mon.form, PLATARCADE_MAX_LEVEL)) {
            PokeParty_SetParam(pkm, PKM_PARAM_EXP, o->exp);
            PokeParty_RecalcStats(pkm);
            PokeParty_Recover(pkm);
        }
        if (apply) {
            PokeParty_SetParam(pkm, PKM_PARAM_HP, o->hp);
            PokeParty_SetParam(pkm, PKM_PARAM_STATUS, StatusToB2(o->status));
            PokeParty_SetParam(pkm, PKM_PARAM_ITEM, o->item);
        }
    }
}

// One opponent made as a Black 2 Pokémon (a value the state doesn't keep: its stats, its level from its experience)
static u32 OpponentStat(PlatArcade *arcade, u8 slot, u32 field) {
    PlatArcadeOpponent *o = Opponent(arcade, slot);
    PokeParty *party;
    PlatArcadeOpponent keep;
    u32 value;

    if (o->mon.species == 0) {
        return 0;
    }
    party = PokeParty_Create(ARCADE_HEAP);
    keep = *Opponent(arcade, 0);
    *Opponent(arcade, 0) = *o;          // (MakeOpponents makes from the first slots)
    MakeOpponents(arcade, party, 1, FALSE);
    *Opponent(arcade, 0) = keep;
    value = PokeParty_GetParam(PokeParty_GetPkm(party, 0), sMonParams[field], NULL);
    GFL_HeapFree(party);
    return value;
}

void PlatArcade_OpponentsClear(PlatArcade *arcade) {
    MI_CpuFill8(WorkOf(arcade)->opponents, 0, sizeof(WorkOf(arcade)->opponents));
}

// FrontierPokemon_InitPokemon at the level, BattleArcade_AddMonToParty: the next slot (the rules count it)
void PlatArcade_OpponentAdd(PlatArcade *arcade, const PlatArcadeMon *mon, u8 level) {
    PlatArcadeOpponent *o = Opponent(arcade, arcade->opponentCount);

    MI_CpuFill8(o, 0, sizeof(*o));
    o->mon = *mon;
    o->item = mon->item;
    if (mon->species != 0) {
        o->exp = PML_UtilGetPkmLvExp(mon->species, mon->form, level);
        o->level = level;
        o->maxHp = (u16)OpponentStat(arcade, arcade->opponentCount, PLATARCADE_MON_MAX_HP);
        o->hp = o->maxHp;
    }
}

// ---------------------------------------------------------------- the parties, as the rules see them
static PokeParty *ArcadeBattleParty(u32 side) {
    BtlSetup *setup = PearlB2_Arcade_GetBattle();

    return setup != NULL ? setup->party[side == PLATARCADE_BATTLE_PLAYER ? 0 : 1] : NULL;
}

u32 PlatArcade_MonGet(PlatArcade *arcade, u32 side, u8 slot, u32 field) {
    PlatArcadeOpponent *o;
    PokeParty *party;

    switch (side) {
    case PLATARCADE_PLAYERS:
        return PkmGet(ArcadeMon(arcade, slot), field);
    case PLATARCADE_OPPONENTS:
        o = Opponent(arcade, slot);
        switch (field) {
        case PLATARCADE_MON_SPECIES: return o->mon.species;
        case PLATARCADE_MON_EXISTS: return o->mon.species != 0;
        case PLATARCADE_MON_LEVEL: return o->level;
        case PLATARCADE_MON_EXP: return o->exp;
        case PLATARCADE_MON_HP: return o->hp;
        case PLATARCADE_MON_MAX_HP: return o->maxHp;
        case PLATARCADE_MON_STATUS: return o->status;
        case PLATARCADE_MON_ITEM: return o->item;
        case PLATARCADE_MON_ABILITY: return o->mon.ability;
        case PLATARCADE_MON_TYPE_1:
            return o->mon.species ? TypeFromB2(PML_PersonalGetParamSingle(o->mon.species, o->mon.form, PERSONAL_TYPE_1)) : 0;
        case PLATARCADE_MON_TYPE_2:
            return o->mon.species ? TypeFromB2(PML_PersonalGetParamSingle(o->mon.species, o->mon.form, PERSONAL_TYPE_2)) : 0;
        }
        return OpponentStat(arcade, slot, field);
    }
    party = ArcadeBattleParty(side);
    if (party == NULL || slot >= PokeParty_GetPkmCount(party)) {
        return 0;
    }
    return PkmGet(PokeParty_GetPkm(party, slot), field);
}

void PlatArcade_MonSet(PlatArcade *arcade, u32 side, u8 slot, u32 field, u32 value) {
    PlatArcadeOpponent *o;

    if (side == PLATARCADE_PLAYERS) {
        PokeParty_SetParam(ArcadeMon(arcade, slot), sMonParams[field],
                           field == PLATARCADE_MON_STATUS ? StatusToB2(value) : value);
    } else if (side == PLATARCADE_OPPONENTS) {
        o = Opponent(arcade, slot);
        switch (field) {
        case PLATARCADE_MON_EXP: o->exp = value; break;
        case PLATARCADE_MON_HP: o->hp = (u16)value; break;
        case PLATARCADE_MON_MAX_HP: o->maxHp = (u16)value; break;
        case PLATARCADE_MON_STATUS: o->status = value; break;
        case PLATARCADE_MON_ITEM: o->item = (u16)value; break;
        }
    }                                   // (the battle's parties are read only)
}

// Pokemon_CalcLevelAndStats: the level from the experience, the stats, the HP moved with the maximum
void PlatArcade_MonCalcLevelAndStats(PlatArcade *arcade, u32 side, u8 slot) {
    PlatArcadeOpponent *o;
    int hp, oldMax, newMax;

    if (side == PLATARCADE_PLAYERS) {
        PokeParty_RecalcStats(ArcadeMon(arcade, slot));
    } else if (side == PLATARCADE_OPPONENTS) {
        o = Opponent(arcade, slot);
        if (o->mon.species == 0) {
            return;
        }
        o->level = (u8)OpponentStat(arcade, slot, PLATARCADE_MON_LEVEL);
        newMax = (int)OpponentStat(arcade, slot, PLATARCADE_MON_MAX_HP);
        oldMax = o->maxHp;
        hp = o->hp;
        if (hp != 0 || oldMax == 0) {
            hp = hp == 0 ? newMax : hp + newMax - oldMax;
        }
        o->maxHp = (u16)newMax;
        if (hp) {
            o->hp = (u16)hp;
        }
    }
}

// Party_HealAllMembers
void PlatArcade_PartyHeal(PlatArcade *arcade, u32 side) {
    PlatArcadeOpponent *o;
    u8 i;

    if (side == PLATARCADE_PLAYERS) {
        for (i = 0; i < arcade->playerCount && i < PLATARCADE_PARTY_SOLO; i++) {
            PokeParty_Recover(ArcadeMon(arcade, i));
        }
    } else if (side == PLATARCADE_OPPONENTS) {
        for (i = 0; i < arcade->opponentCount && i < PLATARCADE_MAX_PARTY; i++) {
            o = Opponent(arcade, i);
            if (o->mon.species != 0) {
                o->hp = o->maxHp;
                o->status = 0;
            }
        }
    }
}

// ---------------------------------------------------------------- the battle (BattleArcade_SetupBattle, BattleArcade_StartBattle)
// Both parties as the board left them go into the battle (the opponent's for the player after the swap), the weather or Trick
// Room with them; then the rules heal the Arcade's two
static BtlSetup *MakeBattle(PlatArcade *arcade, GameSystem *gsys) {
    GameData *gameData = GSYS_GetGameData(gsys);
    u8 count = PlatArcade_GetPlayerPartySize(arcade->challengeType, FALSE);
    u8 opponentCount = PlatArcade_GetOpponentPartySize(arcade->challengeType, FALSE);
    u16 trainerId = arcade->trainerIDs[arcade->currentBattle];
    BtlFieldStatus status;
    BtlSetup *setup;
    BSubwayTrainer *trainer;
    BtlSetupTrainer *dest;
    PokeParty *mine, *theirs;
    BOOL swapped;
    u16 ai;
    u8 i;

    SaveBtlFieldStatus(&status, gameData, GSYS_GetField(gsys));
    setup = BtlSetup_Create(ARCADE_HEAP);
    if (arcade->challengeType == PLATARCADE_DOUBLE) {
        BtlSetup_SetTrainer1v1Double(setup, gameData, &status, 0, ARCADE_HEAP);
    } else {
        BtlSetup_SetTrainer1v1Single(setup, gameData, &status, 0, ARCADE_HEAP);
    }
    setup->unk34[0] = GetGameDataPlayerInfo(gameData);
    swapped = arcade->activeEffect == PLATARCADE_EFFECT_SWAP_MONS;
    mine = setup->party[swapped ? 1 : 0];
    theirs = setup->party[swapped ? 0 : 1];
    PokeParty_InitCore(mine, 6);                    // the player's three as they are: the board's HP, status, item, level
    for (i = 0; i < count; i++) {
        PokeParty_AddPkm(mine, ArcadeMon(arcade, i));
    }
    MakeOpponents(arcade, theirs, opponentCount, TRUE);

    trainer = GFL_HeapAllocate(HEAPID_TAIL(ARCADE_HEAP), sizeof(BSubwayTrainer), TRUE, "arcade_field.c", __LINE__);
    GFL_HeapFree(BtlInst_MakeRomTrainer(trainer, TRAINER_ARC, trainerId, TRAINER_NAMES, ARCADE_HEAP));
    dest = setup->trainers[1];
    dest->trainerId = trainer->unk00;
    dest->trainerClass = trainer->trainerId;
    ai = PlatArcade_SetupBattle(arcade, &swapped);  // (the Arcade's two healed: they are copied above)
    dest->aiFlags = FACILITY_AI | ai;               // Platinum's three flags are Black 2's first three
    GFL_StrBufLoadString(dest->name, trainer->name);
    PMSData_Clear(&dest->unk18);
    PMSData_Clear(&dest->unk20);
    GFL_HeapFree(trainer);

    BtlSetup_PostProcessTrialHouse(setup);          // a facility battle: the Subway's music, no prize money, no exp
    // The board's field: the weather a battle starts with and keeps (Platinum's *_PERM, Black 2's 0xff turns), Pearl's fog (every
    // move's accuracy 3/5: resident/leftovers.c, set after SaveBtlFieldStatus noted the room's), Trick Room (the resident hook
    // at the battle's start, five turns)
    switch (arcade->weather) {
    case PLATARCADE_WEATHER_HARSH_SUN: setup->fieldSituation.env.weather = B2_WEATHER_SUN; break;
    case PLATARCADE_WEATHER_RAINING: setup->fieldSituation.env.weather = B2_WEATHER_RAIN; break;
    case PLATARCADE_WEATHER_SANDSTORM: setup->fieldSituation.env.weather = B2_WEATHER_SANDSTORM; break;
    case PLATARCADE_WEATHER_SNOWING: setup->fieldSituation.env.weather = B2_WEATHER_HAIL; break;
    default: setup->fieldSituation.env.weather = 0; break;
    }
    PearlB2_SetBattleFog(arcade->weather == PLATARCADE_WEATHER_FOG);
    PearlB2_Arcade_SetBattle(setup, arcade->weather == PLATARCADE_WEATHER_TRICK_ROOM ? PLATARCADE_START_TRICK_ROOM : 0);
    if ((trainerId == PLATARCADE_DAHLIA_SILVER || trainerId == PLATARCADE_DAHLIA_GOLD) && gPlatArcadeTable.brainBgm != 0) {
        setup->fieldSituation.bgm = gPlatArcadeTable.brainBgm;          // Platinum's SEQ_PL_BA_BRAIN, once installed
        setup->fieldSituation.unk12 = gPlatArcadeTable.brainWinBgm;     // SEQ_PL_WINBRAIN
    }
    return setup;
}

// ---------------------------------------------------------------- the lobby (ScrCmd_CallBattleArcadeLobbyFunction)
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

// ---------------------------------------------------------------- the board (BattleArcadeApp, an event while the overlay is in)
#define BOARD_X 1                       // the window: tiles, at the top of the screen
#define BOARD_Y 1
#define BOARD_W 30
#define BOARD_H 8
#define PANEL_W 60                      // a panel: pixels, 4 x 4 of them
#define PANEL_H 16
#define PANEL_TEXT_X 4
#define COLOR_PANEL PRINT_COLOR(1, 2, 15)       // the window's own text on its white
#define COLOR_CURSOR PRINT_COLOR(15, 2, 1)      // the cursor: white on the text's dark
#define FILL_CURSOR 1
#define SE_COUNT SEQ_SE_OPEN2           // [guess] Platinum's SEQ_SE_DP_WIN_OPEN2: the panels turn
#define SE_READY SEQ_SE_DECIDE2         // SEQ_SE_DP_UG_020 (pearl_story's SE map)
#define SE_MOVE SEQ_SE_DECIDE1          // SEQ_SE_DP_BUTTON3 (pearl_story's SE map)
#define SE_STOP SEQ_SE_DECIDE1          // SEQ_SE_DP_BUTTON9 (pearl_story's SE map)
#define SE_RESULT SEQ_SE_DECIDE2        // [guess] SEQ_SE_DP_PIRORIRO2

enum {
    BOARD_OPEN,
    BOARD_WAIT,                         // State_OperateRoulette 1: 10 frames
    BOARD_COUNT_3,                      // 2-4: the panels turn, 24 frames each
    BOARD_COUNT_2,
    BOARD_COUNT_1,
    BOARD_RUN,                          // 6: the cursor runs
    BOARD_STOP,                         // 7: SetSelectedEffect
    BOARD_HOLD,                         // 8: 30 frames
};

typedef struct {
    PlatArcadeWork *work;
    MoneyWin *win;
    Font *font;
    StrBuf *names[PLATARCADE_GRID];     // the 16 panels' effects
    StrBuf *count;                      // "3", "2", "1"
    u16 timer;
} BoardEvent;

static void DrawPanel(BoardEvent *b, u8 pos, StrBuf *text, BOOL cursor) {
    u16 x = (pos % 4) * PANEL_W, y = (pos / 4) * PANEL_H;

    if (cursor) {
        GFL_BitmapFillArea(BmpWin_GetBitmap(MsgBGPrinter_GetMsgWinBmpWin(b->win)), x, y, PANEL_W, PANEL_H, FILL_CURSOR);
        MsgBGPrinter_MsgWinPrintStrColorFont(b->win, x + PANEL_TEXT_X, y, text, COLOR_CURSOR, b->font);
    } else {
        MsgBGPrinter_FillMsgWin(b->win, x, y, PANEL_W, PANEL_H);
        MsgBGPrinter_MsgWinPrintStrColorFont(b->win, x + PANEL_TEXT_X, y, text, COLOR_PANEL, b->font);
    }
}

static void DrawCount(BoardEvent *b, u16 digit) {
    u8 i;

    GFL_StrBufClear(b->count);
    GFL_StrBufAppend(b->count, digit);
    for (i = 0; i < PLATARCADE_GRID; i++) {
        DrawPanel(b, i, b->count, FALSE);
    }
    GFL_SndSEPlay(SE_COUNT);
}

static void FreeBoard(BoardEvent *b) {
    u8 i;

    if (b->win != NULL) {
        MsgBGPrinter_DeleteMsgWin(b->win);
        b->win = NULL;
    }
    for (i = 0; i < PLATARCADE_GRID; i++) {
        if (b->names[i] != NULL) {
            GFL_StrBufFree(b->names[i]);
            b->names[i] = NULL;
        }
    }
    if (b->count != NULL) {
        GFL_StrBufFree(b->count);
        b->count = NULL;
    }
}

static BOOL StopPressed(void) {
    u32 x, y;

    return (GCTX_HIDGetPressedKeys() & PAD_BUTTON_A) != 0 || GFL_HIDGetTouchPressedPoint(&x, &y);
}

static GameEventReturnCode BoardEvent_Callback(GameEvent *event, u32 *state, void *data) {
    BoardEvent *b = data;
    PlatArcade *arcade = &b->work->arcade;
    PlatArcadeRoulette *r = &b->work->roulette;
    FieldMsgBG *sys;
    BOOL press, stopped;
    u8 i, prev;

    if (b->names[0] == NULL) {                      // (no challenge: nothing to show)
        return GAMEEVENT_DONE;
    }
    switch (*state) {
    case BOARD_OPEN:
        sys = Field_GetMsgBGSys(GSYS_GetField(GameEvent_GetGameSystem(event)));
        b->font = MsgBGPrinter_GetFont(sys);
        b->win = FieldMsgBG_CreateMoneyWin(sys, NULL, BOARD_X, BOARD_Y, BOARD_W, BOARD_H);
        b->timer = 0;
        *state = BOARD_WAIT;
        break;
    case BOARD_WAIT:
        if (++b->timer >= 10) {
            b->timer = 0;
            DrawCount(b, '3');
            *state = BOARD_COUNT_3;
        }
        break;
    case BOARD_COUNT_3:
    case BOARD_COUNT_2:
    case BOARD_COUNT_1:
        if (++b->timer < 24) {
            break;
        }
        b->timer = 0;
        if (*state == BOARD_COUNT_1) {
            for (i = 0; i < PLATARCADE_GRID; i++) {
                DrawPanel(b, i, b->names[i], i == r->cursorPos);
            }
            GFL_SndSEPlay(SE_READY);
            *state = BOARD_RUN;
        } else {
            DrawCount(b, *state == BOARD_COUNT_3 ? '2' : '1');
            (*state)++;
        }
        break;
    case BOARD_RUN:
        press = StopPressed();
        prev = r->cursorPos;
        stopped = PlatArcade_RouletteTick(arcade, r, press);
        if (r->cursorUpdateTimer == 0) {            // the cursor moved this frame (UpdateCursorPosition's sound)
            GFL_SndSEPlay(SE_MOVE);
            if (prev != r->cursorPos) {
                DrawPanel(b, prev, b->names[prev], FALSE);
                DrawPanel(b, r->cursorPos, b->names[r->cursorPos], TRUE);
            }
        }
        if (stopped) {
            if (press) {
                GFL_SndSEPlay(SE_STOP);             // PressStopButton
            }
            *state = BOARD_STOP;
        }
        break;
    case BOARD_STOP:                                // every panel shows the effect, the cursor on its own
        PlatArcade_RouletteStop(arcade, r);
        for (i = 0; i < PLATARCADE_GRID; i++) {
            DrawPanel(b, i, b->names[r->cursorPos], i == r->cursorPos);
        }
        GFL_SndSEPlay(SE_RESULT);
        b->timer = 0;
        *state = BOARD_HOLD;
        break;
    case BOARD_HOLD:
        if (++b->timer < 30) {
            break;
        }
        FreeBoard(b);
        return GAMEEVENT_DONE;
    }
    return GAMEEVENT_CONTINUE;
}

// The board's event (GameEvent_CreateOverlayDelegate's provider): OpenBattleArcadeApp's arguments and the app's start, the 16
// panels' names from the room's text
GameEvent *PlatArcade_BoardEventProvider(GameSystem *gsys, void *args) {
    PlatArcadeBoardArgs *a = args;
    PlatArcadeWork *work = GetWork(GameData_GetSaveControl(GSYS_GetGameData(gsys)));
    GameEvent *event = GameEvent_Create(gsys, NULL, BoardEvent_Callback, sizeof(BoardEvent));
    BoardEvent *b = GameEvent_GetData(event);
    u8 i;

    MI_CpuFill8(b, 0, sizeof(BoardEvent));
    b->work = work;
    sGameData = GSYS_GetGameData(gsys);
    if (work->arcade.magic == PLATARCADE_WORK_MAGIC && gPlatArcadeTable.magic == PLATARCADE_TABLE_MAGIC && a->msgData != NULL) {
        PlatArcade_RouletteOpen(&work->arcade, &work->roulette);
        PlatArcade_RouletteStart(&work->roulette);
        for (i = 0; i < PLATARCADE_GRID; i++) {
            b->names[i] = GFL_MsgDataLoadStrbufNew(a->msgData, a->firstLine + work->roulette.rouletteEffects[i] % PLATARCADE_EFFECTS);
        }
        b->count = GFL_StrBufCreate(4, ARCADE_HEAP);
    }
    return event;
}

// ---------------------------------------------------------------- the ops
BOOL PlatArcade_Op(VM *vm, FieldScriptEnv *env, u32 op) {
    GameSystem *gsys = FieldScriptEnv_GetGameSystem(env);
    GameData *gameData = GSYS_GetGameData(gsys);
    SaveControl *save = GameData_GetSaveControl(gameData);
    ScriptWork *script = FieldScriptEnv_GetScriptWork(env);
    WordSet *words = ScriptWork_GetWordSet(script);
    PlatArcadeWork *work = GetWork(save);
    PlatArcade *arcade = &work->arcade;
    BOOL ready = arcade->magic == PLATARCADE_WORK_MAGIC && gPlatArcadeTable.magic == PLATARCADE_TABLE_MAGIC;
    u16 a, b, c, d, e;
    u16 *var;
    BtlSetup *setup;
    MsgData *msg;
    StrBuf *line;
    PokeParty *party;
    u8 i;

    sGameData = gameData;
    switch (op) {
    case PLATARCADE_OP_INIT:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        d = ScriptReadAny(vm, env);
        e = ScriptReadAny(vm, env);
        if (gPlatArcadeTable.magic != PLATARCADE_TABLE_MAGIC) {
            break;
        }
        arcade->lcrng = GFL_RandomLC(0xffffffff);          // the challenge's own LCRNG, seeded once
        PlatArcade_Init(arcade, &work->save, save, a, (u8)b, (u8)c, (u8)d, (u8)e);
        break;
    case PLATARCADE_OP_LOAD_ROUND:
        a = ScriptReadAny(vm, env);
        if (ready) {
            PlatArcade_LoadTrainersForRound(arcade, &work->save, a);
        }
        break;
    case PLATARCADE_OP_FUNCTION:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        if (!ready) {
            *var = 0;
            break;
        }
        switch (a) {
        case PLATARCADE_FN_RESET_SYSTEM:                    // the rest: saved, then the game starts again
            OS_ResetSystem(0);
            break;
        case PLATARCADE_FN_RESTORE_HELD_ITEMS:              // (the field party's own: Platinum's Arcade party is a copy)
            party = GameData_GetParty(gameData);
            for (i = 0; i < PLATARCADE_PARTY_SOLO; i++) {
                PokeParty_SetParam(PokeParty_GetPkm(party, arcade->partySlots[i]), PKM_PARAM_ITEM, arcade->savedHeldItems[i]);
            }
            break;
        case PLATARCADE_FN_GET_OPPONENT_OBJECT_ID:          // the Trainer's walker code
            *var = PearlB2_TowerObjCode(TrainerClass(arcade->trainerIDs[PlatArcade_GetTrainerOffset(arcade, (u8)b)]));
            break;
        case PLATARCADE_FN_SET_NAME_OF_AFFECTED_TRAINER:    // word b: the Trainer of slot c for the opponent's effects, the
            if (PlatArcade_GetCategoryFromEffect(arcade->activeEffect) == PLATARCADE_CATEGORY_FOE) {    // player otherwise
                msg = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TRAINER_NAMES, ARCADE_HEAP);
                line = GFL_MsgDataLoadStrbufNew(msg, arcade->trainerIDs[PlatArcade_GetTrainerOffset(arcade, (u8)c)]);
                GFL_WordSetSetStrbuf(words, b, line, 0, TRUE, 0);
                GFL_StrBufFree(line);
                GFL_MsgDataFree(msg);
            } else {
                copyVarForText(words, b, GetGameDataPlayerInfo(gameData));
            }
            break;
        default:                                            // the link (closed), the sprites, backgrounds, palettes and
            if (!PlatArcade_Function(arcade, &work->save, save, (u8)a, (u8)b, (u8)c, var)) {    // particles (the room's), the
                *var = 0;                                   // Trainers' data (loaded where the line and the battle need it)
            }
            break;
        }
        break;
    case PLATARCADE_OP_FREE:
        arcade->magic = 0;
        break;
    case PLATARCADE_OP_SETUP_FIRST:
        if (ready) {
            PlatArcade_SetupFirstOpponentsParty(arcade);
        }
        break;
    case PLATARCADE_OP_SETUP_NEXT:
        if (ready) {
            PlatArcade_SetupNextOpponentsParty(arcade);
        }
        break;
    case PLATARCADE_OP_START_BATTLE:
        if (!ready) {
            break;
        }
        setup = MakeBattle(arcade, gsys);
        ScriptWork_CallEvent(script, EventBSubwayBattleCall_Create(gsys, GSYS_GetField(gsys), setup));
        return TRUE;
    case PLATARCADE_OP_CLEANUP_BATTLE:                      // FrontierScrCmd_BattleArcade_CleanupBattle
        setup = PearlB2_Arcade_GetBattle();
        if (setup != NULL) {
            if (ready) {
                // the turns ended (Platinum's totalTurnsElapsed: BtlMain_StoreResultStats' setup->unkD2), won or not
                PlatArcade_CleanupBattle(arcade, setup->unkD2, setup->result == BTL_RESULT_VICTORY);
            }
            PearlB2_Arcade_SetBattle(NULL, 0);
            BtlSetup_Free(setup);
        }
        PearlB2_SetBattleFog(FALSE);
        break;
    case PLATARCADE_OP_CHECK_WON:
        var = ScriptReadVar(vm, env);
        *var = ready ? (u16)arcade->wonBattle : 0;
        break;
    case PLATARCADE_OP_TRAINER_WORD:
        a = ScriptReadAny(vm, env);                        // the word
        b = ScriptReadAny(vm, env);                        // the Trainer's slot (0, 1)
        c = ScriptReadAny(vm, env);                        // the line (0 the intro)
        if (!ready) {
            break;
        }
        msg = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TRAINER_LINES, ARCADE_HEAP);
        line = GFL_MsgDataLoadStrbufNew(msg, arcade->trainerIDs[PlatArcade_GetTrainerOffset(arcade, (u8)b)] * 3 + c);
        GFL_WordSetSetStrbuf(words, a, line, 0, TRUE, 0);
        GFL_StrBufFree(line);
        GFL_MsgDataFree(msg);
        break;
    case PLATARCADE_OP_APPLY_EFFECT:
        if (ready) {
            PlatArcade_ApplyEffect(arcade, arcade->activeEffect);
        }
        break;
    case PLATARCADE_OP_LOBBY:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        *var = 0;
        switch (a) {
        case PLATARCADE_LOBBY_CHECK_PARTY_ELIGIBLE:
            *var = CheckPartyEligible(GameData_GetParty(gameData), b);
            break;
        case PLATARCADE_LOBBY_CHECK_STREAK_ACTIVE:
            *var = b == PLATARCADE_MULTI_WFC ? PlatArcade_GetStat(save, PLATARCADE_STAT_WFC_STREAK_ACTIVE) :
                                               (u16)PlatArcade_GetStreakFlag(save, b);
            break;
        case PLATARCADE_LOBBY_DELETE_ACTIVE_STREAK:
            PlatArcade_ClearActiveStreak(save, (u8)b);
            break;
        }
        break;
    case PLATARCADE_OP_DELETE_STREAK:
        a = ScriptReadAny(vm, env);
        PlatArcade_ClearActiveStreak(save, (u8)a);
        break;
    case PLATARCADE_OP_LOBBY_SELECT:                        // the lobby's BA_LOBBY_FUNC_SELECT_POKEMON (SelectBattleArcadeChallengers)
        a = ScriptReadAny(vm, env);
        if (gPlatArcadeTable.magic != PLATARCADE_TABLE_MAGIC || gPlatArcadeTable.entryRegulation == 0) {
            work->choice = 7;                               // (no Arcade: as the screen left)
            break;
        }
        MI_CpuFill8(work->picked, 0, sizeof(work->picked));
        work->choice = 0;
        work->screenResult = 0;
        ScriptWork_CallEvent(script, EventBtlInstPokeSelect_Create(gsys, a == PLATARCADE_DOUBLE, PICK_MODE,
                                                                   gPlatArcadeTable.entryRegulation, GameData_GetParty(gameData),
                                                                   work->picked, &work->choice, &work->screenResult, NULL));
        return TRUE;
    case PLATARCADE_OP_SELECTED_SLOTS:                      // ScrCmd_GetBattleArcadeSelectedSlots: the slots from 0
        for (i = 0; i < 3; i++) {
            var = ScriptReadVar(vm, env);
            if (work->screenResult != 0 || work->choice == 7 || work->choice == 8 || work->picked[0] == 0) {
                if (i == 0) {
                    *var = NO_SLOT;                         // PARTY_SLOT_NONE: the screen was left
                }
            } else {
                *var = work->picked[i] > 0 ? work->picked[i] - 1 : 0;
            }
        }
        break;
    default:                                                // (PLATARCADE_OP_BOARD is the resident's: plat_arcade_ext.c)
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    return FALSE;
}

#endif
