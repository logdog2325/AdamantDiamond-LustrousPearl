#include "pearlb2.h"
#include "pearlb2/plat_factory.h"
#include "pearlb2/plat_frontier.h"
#include "pearlb2/tower.h"
#include "types.h"
#include "battle/btl_result.h"
#include "battle/btl_setup.h"
#include "battle/regulation.h"
#include "constants/arc.h"
#include "constants/text_banks.h"
#include "field/battle_facility.h"
#include "field/bsubway_scr.h"
#include "field/event_battle.h"
#include "field/field.h"
#include "field/field_script.h"
#include "field/fld_btl_inst_event.h"
#include "gfl/arc.h"
#include "gfl/heap.h"
#include "gfl/msg.h"
#include "gfl/random.h"
#include "gfl/std.h"
#include "nitro/os.h"
#include "pml/personal.h"
#include "pml/poke_party.h"
#include "save/save_control.h"
#include "system/game_data.h"
#include "system/game_system.h"
#include "system/vm.h"
#include "system/wordset.h"

// PearlB2: Platinum's Battle Factory, the game side (include/pearlb2/plat_factory.h; notes/PLATINUM_FRONTIER.md "The Battle
// Factory"). Overlay 378, at Pal Park's address: the resident PearlB2_Frontier_Factory loads it for one op and unloads it
// before the op returns. An op that runs a screen or the battle gives the script an event made of Black 2's own (overlay
// 12's party screen and battle call), whose data is in the challenge's work or on the event heap, so nothing of this
// overlay is needed while it runs; the op after it reads the result.
// - The rules are factory_rules.c's (Platinum's, checked on the host against Platinum's C).
// - The rental and swap screens: Black 2's battle-entry party screen (EventBtlInstPokeSelect_Create, the Battle Subway's and
//   Trial House's), on a party made of the rentals, with the Factory's regulations (gPlatFactoryTable: three of six, one of
//   three; no level rule or clause). Its summary pages show each rental's moves, ability and item, as Platinum's rental
//   screen does. Platinum's rental screen can't be left without three; Black 2's can (B): the script opens it again.
// - The battle: Black 2's Trial House battle (SetupTrialHouseBattle, the Subway's own), the player's three rentals against
//   the Factory Trainer (his name, class and lines from the Subway's Trainer archive, which holds Platinum's Frontier
//   Trainers: patches/battle_tower.py), his Pokémon as factory_rules.c made them, at Level 50 or 100 (the Trial House sets
//   50: Open Level makes both parties again at 100), Platinum's AI flags for the round.
// - Not as Platinum: the rentals' Original Trainer and met place (Platinum: "?????" and the Battle Factory) are Black 2's
//   facility Pokémon's; Platinum's game record of swaps (RECORD_BATTLE_FACTORY_TRADES) has no Black 2 counterpart.

#if PEARLB2

#define SET_ARC 0xd3                    // a/2/1/1: the Subway's sets, Platinum's 0-950 (patches/battle_tower.py)
#define TRAINER_ARC 0xd4                // a/2/1/2: the Subway's Trainers, file id + 1
#define TRAINER_NAMES 0xf               // system text 15: their names
#define CLIENT_PLAYER 0
#define CLIENT_ENEMY 1
#define PICK_MODE 0x17                  // the party list's battle-entry mode (the Trial House's)
#define FACILITY_AI 0x80                // the bit Black 2's facility Trainers have besides the three AI levels (0x87)
#define NO_SLOT 0xff

// The table only a Platinum build fills (patches/platinum_factory.py writes it into this overlay's file)
#pragma explicit_zero_data on
PlatFactoryTable gPlatFactoryTable = { 0 };
#pragma explicit_zero_data reset

typedef char FactoryCheckWorkSize[sizeof(PlatFactoryWork) <= sizeof(((PearlB2FrontierSave *)0)->challenge) ? 1 : -1];

// ---------------------------------------------------------------- what the rules read (plat_factory.h)
void PlatFactory_ReadSet(u16 setID, PlatFactorySet *set) {
    GFL_ArcSysRead(set, SET_ARC, setID);
}

u16 PlatFactory_SpeciesAbility(u16 species, u32 slot) {
    return (u16)PML_PersonalGetParamSingle(species, 0, slot == 0 ? PERSONAL_ABILITY_1 : PERSONAL_ABILITY_2);
}

// Black 2's types (17, no Mystery type): the common type's hint gives Black 2's number, which BufferTypeName names
void PlatFactory_SpeciesTypes(u16 species, u16 form, u8 *type1, u8 *type2) {
    *type1 = (u8)PML_PersonalGetParamSingle(species, form, PERSONAL_TYPE_1);
    *type2 = (u8)PML_PersonalGetParamSingle(species, form, PERSONAL_TYPE_2);
}

// ---------------------------------------------------------------- the challenge
static PlatFactoryWork *Factory_GetWork(SaveControl *save) {
    return (PlatFactoryWork *)PearlB2_Frontier_GetSave(save)->challenge;
}

static PlatFactoryRecords Factory_Records(SaveControl *save) {
    PearlB2FrontierSave *frontier = PearlB2_Frontier_GetSave(save);
    PlatFactoryRecords records;

    records.stats = frontier->stats;
    records.streakFlags = &frontier->streakFlags[FRONTIER_FACILITY_FACTORY];
    return records;
}

// A Pokémon as Black 2's facility code makes party Pokémon (BtlInst_MakeParty): the fields factory_rules.c made
static void Factory_ToSubway(const PlatFactoryMon *mon, BSubwayPokemon *pkm, HeapID heapId) {
    MsgData *msgData;
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
    pkm->ivs.stat.hp = mon->ivs;
    pkm->ivs.stat.attack = mon->ivs;
    pkm->ivs.stat.defense = mon->ivs;
    pkm->ivs.stat.speed = mon->ivs;
    pkm->ivs.stat.spAttack = mon->ivs;
    pkm->ivs.stat.spDefense = mon->ivs;
    for (i = 0; i < 6; i++) {
        pkm->evs[i] = mon->evs[i];
    }
    pkm->ability = (u8)mon->ability;
    pkm->happiness = mon->happiness;
    pkm->nature = mon->nature;
    msgData = GFL_MsgSysLoadData(FALSE, ARCID_SYSTEM_MESSAGE, TEXT_BANK_SPECIES_NAMES, heapId);
    GFL_MsgDataLoadRawStr(msgData, pkm->species, pkm->nickname, NELEMS(pkm->nickname));
    GFL_MsgDataFree(msgData);
}

// A party of the Pokémon at the challenge's level (on the event heap: freed by the op after the screen, or at once)
static void Factory_MakeParty(PokeParty *party, const PlatFactoryMon *mons, int count, u8 level, HeapID heapId) {
    BSubwayPokemon *pkms = GFL_HeapAllocate(HEAPID_TAIL(heapId), sizeof(BSubwayPokemon) * PLATFACTORY_RENTALS, TRUE,
                                            "plat_factory", __LINE__);
    int i;

    for (i = 0; i < count; i++) {
        Factory_ToSubway(&mons[i], &pkms[i], heapId);
    }
    BtlInst_MakeParty(party, pkms, level, count, heapId);
    GFL_HeapFree(pkms);
}

static void Factory_FreeScreenParty(PlatFactoryWork *work) {
    if (work->screenParty != NULL) {
        GFL_HeapFree(work->screenParty);
        work->screenParty = NULL;
    }
}

// The battle-entry party screen on the Pokémon, `need` of them to pick
static GameEvent *Factory_Screen(GameSystem *gsys, PlatFactoryWork *work, const PlatFactoryMon *mons, int count, u32 need) {
    PokeParty *party = PokeParty_Create(HEAPID_GAMEEVENT);
    u32 regulation = need == PLATFACTORY_PARTY_SOLO ? gPlatFactoryTable.rentRegulation : gPlatFactoryTable.swapRegulation;

    Factory_FreeScreenParty(work);
    Factory_MakeParty(party, mons, count, PlatFactory_GetPokemonLevel(&work->factory), HEAPID_GAMEEVENT);
    work->screenParty = party;
    MI_CpuFill8(work->picked, 0, sizeof(work->picked));
    work->choice = 0;
    work->screenResult = 0;
    return EventBtlInstPokeSelect_Create(gsys, work->factory.challengeType == PLATFACTORY_DOUBLE, PICK_MODE, regulation,
                                         party, work->picked, &work->choice, &work->screenResult, NULL);
}

// The screen's picks (slots from 0), how many; none when it was left (B)
static int Factory_Picks(PlatFactoryWork *work, u16 *slots, int max) {
    int i, n = 0;

    if (work->screenResult != 0 || work->choice == 7 || work->choice == 8) {
        return 0;
    }
    for (i = 0; i < (int)sizeof(work->picked) && n < max; i++) {
        if (work->picked[i] >= 1 && work->picked[i] <= PLATFACTORY_RENTALS) {
            slots[n++] = (u16)(work->picked[i] - 1);
        }
    }
    return n;
}

// The Trainer of the battle, as the Subway loads one (name, class, its line), with the Factory's Pokémon
static BSubwayTrainer *Factory_LoadTrainer(PlatFactoryWork *work, u32 index, HeapID heapId) {
    BSubwayTrainer *trainer = GFL_HeapAllocate(HEAPID_TAIL(heapId), sizeof(BSubwayTrainer), TRUE, "plat_factory",
                                               __LINE__);
    PlatFactory *factory = &work->factory;
    u16 trainerId = factory->trainerIDs[factory->currentBattle + index * PLATFACTORY_BATTLES_PER_ROUND];
    int i;

    GFL_HeapFree(BtlInst_MakeRomTrainer(trainer, TRAINER_ARC, trainerId, TRAINER_NAMES, heapId));
    for (i = 0; i < factory->opponentCount && i < 4; i++) {
        Factory_ToSubway(&factory->opponentsParty[i], &trainer->pokemon[i], heapId);
    }
    return trainer;
}

// BattleFactory_SetupBattle
static BtlSetup *Factory_SetupBattle(GameSystem *gsys, PlatFactoryWork *work) {
    PlatFactory *factory = &work->factory;
    u8 count = PlatFactory_GetPlayerPartySize(factory->challengeType);
    u8 level = PlatFactory_GetPokemonLevel(factory);
    PokeParty *party = PokeParty_Create(HEAPID_TAIL(HEAPID_GAMEEVENT));
    BSubwayTrainer *trainer = Factory_LoadTrainer(work, 0, HEAPID_GAMEEVENT);
    BtlSetup *setup;

    Factory_MakeParty(party, factory->playersParty, count, level, HEAPID_GAMEEVENT);
    setup = SetupTrialHouseBattle(gsys, party, factory->challengeType, trainer, NULL, count);
    if (level != 50) {                  // (the Trial House's parties are at Level 50)
        Factory_MakeParty(setup->party[CLIENT_PLAYER], factory->playersParty, count, level, HEAPID_GAMEEVENT);
        Factory_MakeParty(setup->party[CLIENT_ENEMY], factory->opponentsParty, count, level, HEAPID_GAMEEVENT);
    }
    setup->trainers[CLIENT_ENEMY]->aiFlags = FACILITY_AI | PlatFactory_GetAIMask(factory);
    if (gPlatFactoryTable.brainBgm != 0 &&
        (factory->trainerIDs[factory->currentBattle] == PLATFACTORY_THORTON_SILVER ||
         factory->trainerIDs[factory->currentBattle] == PLATFACTORY_THORTON_GOLD)) {
        setup->fieldSituation.bgm = gPlatFactoryTable.brainBgm;
    }
    GFL_HeapFree(trainer);
    GFL_HeapFree(party);
    return setup;
}

BOOL PlatFactory_Op(VM *vm, FieldScriptEnv *env, u32 op) {
    GameSystem *gsys = FieldScriptEnv_GetGameSystem(env);
    GameData *gameData = GSYS_GetGameData(gsys);
    SaveControl *save = GameData_GetSaveControl(gameData);
    ScriptWork *script = FieldScriptEnv_GetScriptWork(env);
    PlatFactoryWork *work = Factory_GetWork(save);
    PlatFactory *factory = &work->factory;
    PlatFactoryRecords records = Factory_Records(save);
    u16 a, b, c, d;
    u16 *var;
    u16 slots[PLATFACTORY_RENTALS];
    int i, n;

    switch (op) {
    case PLATFACTORY_OP_INIT:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        work->screenParty = NULL;
        work->setup = NULL;
        PlatFactory_Init(factory, &work->save, &records, a, (u8)b, (u8)c, GFL_RandomLC(0xffffffff));
        break;
    case PLATFACTORY_OP_LOAD_ROUND:
        a = ScriptReadAny(vm, env);
        PlatFactory_LoadTrainersAndRentalsForRound(factory, &work->save, a);
        break;
    case PLATFACTORY_OP_FUNCTION:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        c = ScriptReadAny(vm, env);
        var = ScriptReadVar(vm, env);
        d = *var;
        switch (a) {
        case PLATFACTORY_FN_RESET_SYSTEM:           // the rest: saved, then the game starts again
            OS_ResetSystem(0);
            break;
        case PLATFACTORY_FN_GET_OPPONENT_OBJECT_ID: {
            BSubwayTrainer *trainer = Factory_LoadTrainer(work, b, HEAPID_GAMEEVENT);

            *var = PearlB2_TowerObjCode(trainer->trainerId);
            GFL_HeapFree(trainer);
            break;
        }
        case PLATFACTORY_FN_SET_RENTED_MONS_IN_STRING:
            for (i = 0; i < PlatFactory_GetPlayerPartySize(factory->challengeType); i++) {
                WordSet_LoadSpeciesName(ScriptWork_GetWordSet(script), i, factory->playersParty[i].species);
            }
            break;
        case PLATFACTORY_FN_UPDATE_BACKGROUND:      // Platinum's picture effects: the room is a field room here
        case PLATFACTORY_FN_START_CORRIDOR_ANIMATION:
        case PLATFACTORY_FN_STOP_CORRIDOR_ANIMATION:
        case PLATFACTORY_FN_LOAD_TRAINERS:          // (the Trainer is loaded where his line and battle need him)
        case PLATFACTORY_FN_INIT_COMM_MANAGER:      // the multi challenges: closed
        case PLATFACTORY_FN_UPDATE_PARTNERS_PARTY:
            break;
        default:
            if (!PlatFactory_Function(factory, &work->save, &records, (u8)a, (u8)b, (u8)c, var)) {
                *var = d;
            }
            break;
        }
        break;
    case PLATFACTORY_OP_RENT_SCREEN:
        ScriptWork_CallEvent(script, Factory_Screen(gsys, work, factory->initialRentalMons, PLATFACTORY_RENTALS,
                                                    PlatFactory_GetPlayerPartySize(factory->challengeType)));
        return TRUE;
    case PLATFACTORY_OP_RENT_RESULT:
        var = ScriptReadVar(vm, env);
        n = Factory_Picks(work, slots, PLATFACTORY_RENTALS);
        Factory_FreeScreenParty(work);
        *var = n == PlatFactory_GetPlayerPartySize(factory->challengeType);
        if (*var) {
            for (i = 0; i < 6; i++) {
                factory->selectedAppSlots[i] = i < n ? slots[i] : 0;
            }
        }
        break;
    case PLATFACTORY_OP_SWAP_SCREEN:
        a = ScriptReadAny(vm, env);
        if (a == 0) {
            factory->selectedAppSlots[0] = NO_SLOT;
            ScriptWork_CallEvent(script, Factory_Screen(gsys, work, factory->playersParty, factory->playerCount, 1));
            return TRUE;
        }
        if (factory->selectedAppSlots[0] == NO_SLOT) {
            break;                                  // (nothing given: no second screen)
        }
        ScriptWork_CallEvent(script, Factory_Screen(gsys, work, factory->opponentsParty, factory->opponentCount, 1));
        return TRUE;
    case PLATFACTORY_OP_SWAP_RESULT:
        a = ScriptReadAny(vm, env);
        if (a == 0 || factory->selectedAppSlots[0] != NO_SLOT) {
            n = Factory_Picks(work, slots, 1);
            Factory_FreeScreenParty(work);
            if (n == 0) {
                factory->selectedAppSlots[0] = NO_SLOT;
            } else if (a < 2) {
                factory->selectedAppSlots[a] = slots[0];
            }
        }
        break;
    case PLATFACTORY_OP_ADD_SELECTED:
        PlatFactory_AddSelectedRentalsToParty(factory);
        break;
    case PLATFACTORY_OP_SETUP_NEXT_OPPONENT:
        PlatFactory_SetupNextOpponent(factory);
        break;
    case PLATFACTORY_OP_APPLY_TRADE:
        PlatFactory_ApplyTrade(factory);
        break;
    case PLATFACTORY_OP_SETUP_NEXT_PARTY:
        PlatFactory_SetupNextOpponentsParty(factory);
        break;
    case PLATFACTORY_OP_START_BATTLE:
        work->setup = Factory_SetupBattle(gsys, work);
        ScriptWork_CallEvent(script, EventBSubwayBattleCall_Create(gsys, GSYS_GetField(gsys), work->setup));
        return TRUE;
    case PLATFACTORY_OP_CLEANUP_BATTLE:
        if (work->setup != NULL) {
            factory->wonBattle = ((BtlSetup *)work->setup)->result == BTL_RESULT_VICTORY;
            BtlSetup_Free(work->setup);
            work->setup = NULL;
        }
        break;
    case PLATFACTORY_OP_CHECK_WON:
        var = ScriptReadVar(vm, env);
        *var = factory->wonBattle;
        break;
    case PLATFACTORY_OP_TRAINER_INTRO: {
        BSubwayTrainer *trainer;

        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        trainer = Factory_LoadTrainer(work, a, HEAPID_GAMEEVENT);
        ScriptWork_CallEvent(script, EventBtlInstTrainerMsg_Create(gsys, trainer, 0, b));
        GFL_HeapFree(trainer);          // (the event made its text from the Trainer's line already)
        return TRUE;
    }
    case PLATFACTORY_OP_FREE:
        Factory_FreeScreenParty(work);
        break;
    case PLATFACTORY_OP_DELETE_STREAK:
        a = ScriptReadAny(vm, env);
        b = ScriptReadAny(vm, env);
        PlatFactory_DeleteActiveStreak(&records, (u8)a, (u8)b);
        break;
    default:
        GFL_ASSERT(FALSE);
        VM_Halt(vm);
        return TRUE;
    }
    return FALSE;
}

#endif
