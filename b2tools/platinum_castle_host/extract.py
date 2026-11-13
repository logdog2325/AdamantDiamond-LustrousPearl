"""The Castle harness's Platinum side (notes/PLATINUM_FRONTIER.md "The Battle Castle"): Platinum's own Battle Castle C, copied as it
is out of pokeplatinum, function by function, plus the constants and structs it names.

    python3 b2tools/platinum_castle_host/extract.py OUT_DIR

OUT_DIR/plat_consts.h   the decomp's generated constants the copied code names (items, the Frontier Trainers, the records' ids, the
                        two screens' text lines)
OUT_DIR/plat_types.h    the structs, as the decomp's headers have them (BattleCastle, BattleCastleSave, FrontierPokemon, ...)
OUT_DIR/plat_castle.c   src/overlay104/battle_castle.c (the rules' functions), battle_castle_helpers.c and src/battle_castle_save.c
                        (all but the includes), frscrcmd_battle_castle.c (the scene's commands the rules run through:
                        InitBattleCastle .. CallBattleCastleFunction, the CP commands, the battle's start and cleanup),
                        scrcmd_battle_castle.c (the lobby's streak deletion), frontier_opponents.c (the Trainers and their
                        Pokémon), battle_frontier_save.c and battle_frontier_stats.c (the records), item_use_pokemon.c (a Max
                        Potion's and a Max Elixir's effect)
OUT_DIR/plat_apps.c     the two screens' state machines (applications/frontier/battle_castle/self_app.c, opponent_app.c:
                        State_MainAppFlow with the functions it buys through, helpers.c), each in its own file scope
plat_shim.h gives them the types and the calls into the rest of the game (the save, the party, the battle's setup, the sets, the
screens' drawing, which does nothing here); app_stubs.h the screens' own drawing functions. One edit to Platinum's text, named
where it is made: LoadTrainersAndMonsFromSave's ivs array, which Platinum never sets, starts at 0 (castle_rules.c does the same).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PLAT = os.path.join(ROOT, 'external', 'pokeplatinum')
sys.path.insert(0, os.path.join(ROOT, 'b2tools', 'platinum_frontier_host'))
from extract import body as _body  # noqa: E402  (the core's harness: a function or table by its head, braces matched)


def body(text, head):
    """A definition (its head line doesn't end with ';': a static function's prototype comes first in these files)."""
    return _body(text, head if head.endswith('=') else head + r'[^;\n]*$')


def src(path):
    return open(os.path.join(PLAT, path)).read()


def lines(name):
    return [l.strip() for l in open(os.path.join(PLAT, 'generated', name)) if l.strip()]


def without_includes(text):
    return '\n'.join(l for l in text.split('\n') if not l.startswith('#include') and 'FS_EXTERN_OVERLAY' not in l)


def enum_values(text, name):
    """{constant: value} of an enum (explicit values and the counting after them)."""
    t = text[text.index('{', text.index(name)):]
    t = t[:t.index('}')]
    value, out = 0, {}
    for n, v in re.findall(r'^\s*(\w+)(?:\s*=\s*([\w() +\-]+?))?,?\s*(?://.*)?$', t, re.M):
        if v:
            value = eval(v, {}, dict(out))
        out[n] = value
        value += 1
    return out


def consts():
    out = ['// Platinum\'s constants for the copied Battle Castle code (extract.py; do not edit)', '#ifndef PLAT_CONSTS_H',
           '#define PLAT_CONSTS_H']
    for name in ('items', 'species'):
        out += [f'#define {n.split("=")[0].strip()} {i}' for i, n in enumerate(lines(name + '.txt'))]
    flags = lines('ai_flags.txt')           # a mask: NONE 0, then bits
    out += [f'#define {flags[0]} 0'] + [f'#define {n} (1 << {i})' for i, n in enumerate(flags[1:])]
    order = [l.strip() for l in open(os.path.join(PLAT, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    out += [f'#define FRONTIER_TRAINER_{n.upper()} {i}' for i, n in enumerate(order)]
    out += [f'#define {n} {v}' for n, v in enum_values(src('include/constants/battle_frontier_stats.h'),
                                                         'enum BattleFrontierStatsIndex').items()]
    for f in ('battle_castle_functions.h',):
        t = src('include/constants/' + f)
        for e in ('enum BattleCastleLobbyFunction', 'enum BattleCastleFunction'):
            out += [f'#define {n} {v}' for n, v in enum_values(t, e).items()]
    for bank in ('battle_castle_self_app', 'battle_castle_opponent_app'):
        msgs = json.load(open(os.path.join(PLAT, 'res', 'text', bank + '.json')))['messages']
        out += [f'#define {m["id"]} {i}' for i, m in enumerate(msgs)]
    w = src('include/applications/frontier/battle_castle/windows.h')
    for e in ('enum BattleCastleSelfAppWindow', 'enum BattleCastleOpponentAppWindow'):
        out += [f'#define {n} {v}' for n, v in enum_values(w, e).items()]
    out.append('#endif')
    return '\n'.join(out) + '\n'


def struct(path, name):
    """typedef struct NAME { ... } NAME; out of a header, as it is."""
    t = src(path)
    m = re.search(r'^typedef struct ' + name + r' \{.*?^\} ' + name + ';', t, re.M | re.S)
    assert m, name
    return m.group(0)


def types():
    out = ['// Platinum\'s structs for the copied Battle Castle code (extract.py; do not edit)', '#ifndef PLAT_TYPES_H',
           '#define PLAT_TYPES_H']
    for path, name in (('include/struct_defs/frontier_pokemon_base.h', 'FrontierPokemonBase'),
                       ('include/struct_defs/frontier_trainer_base.h', 'FrontierTrainerBase'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierTrainer'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierPokemon'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierOpponent'),
                       ('include/battle_castle_save.h', 'BattleCastleSave'),
                       ('include/battle_castle_save.h', 'BattleCastlePersistentSave'),
                       ('include/applications/frontier/battle_castle/args.h', 'BattleCastleAppArgs'),
                       ('include/overlay104/battle_castle.h', 'BattleCastle')):
        out.append(struct(path, name))
    for path in ('include/overlay104/battle_castle.h', 'include/overlay104/battle_castle_helpers.h',
                 'include/battle_castle_save.h', 'include/applications/frontier/battle_castle/helpers.h'):
        t = src(path)                          # the headers' defines and prototypes
        out += [l for l in t.split('\n') if re.match(r'#define (CASTLE_SAVE_|LEVEL_ADJUSTMENT_)', l)]
        out += re.findall(r'^[A-Za-z][\w \*]*\([^;{]*\);$', t, re.M)
    out.append('#endif')
    return '\n'.join(out) + '\n'


def plat():
    out = ['// Platinum\'s Battle Castle rules, copied by extract.py from pokeplatinum (do not edit)', '#include "plat_shim.h"', '']
    castle = src('src/overlay104/battle_castle.c')
    out += [p for p in re.findall(r'^static [^;{]*\);$', castle, re.M)
            if not re.search(r'DrawPlayerInfoWindow|PrintPlayerNameandCP', p)]
    for head in (r'^BattleCastle \*BattleCastle_Init\(', r'^void BattleCastle_LoadTrainersForRound\(',
                 r'^static void SelectTrainersAndFirstBattlesMons\(', r'^static void LoadTrainersAndMonsFromSave\(',
                 r'^static void LoadPlayersPartyFromSave\(', r'^void BattleCastle_Free\(',
                 r'^void BattleCastle_StoreAppResults\(', r'^static u16 GetBattleCastleAppSelectedSlot\(',
                 r'^void BattleCastle_Save\(', r'^u16 BattleCastle_IncrementCurrentBattle\(',
                 r'^u16 BattleCastle_GetCurrentBattle\(', r'^void BattleCastle_SaveOnLoss\(',
                 r'^void BattleCastle_SaveOnCompletingRound\(', r'^void BattleCastle_SetupFirstOpponentsParty\(',
                 r'^void BattleCastle_SetupNextOpponentsParty\(', r'^void BattleCastle_PrepForNextBattle\(',
                 r'^int BattleCastle_CalcCPEarnedFromBattle\(', r'^void BattleCastle_ReceiveCastlePoints\(',
                 r'^u16 BattleCastle_GetEarnedBP\(', r'^u16 BattleCastle_GetNextOpponentObjectID\('):
        b = body(castle, head)
        if 'LoadTrainersAndMonsFromSave' in head:      # the one edit: Platinum's ivs are never set (see the top)
            assert '    u8 ivs[MAX_PARTY_SIZE];\n' in b
            b = b.replace('    u8 ivs[MAX_PARTY_SIZE];\n', '    u8 ivs[MAX_PARTY_SIZE] = { 0 }; // (extract.py: never set)\n')
        out.append(b)
    out.append(without_includes(src('src/overlay104/battle_castle_helpers.c')))
    out.append(without_includes(src('src/battle_castle_save.c')))
    fr = src('src/overlay104/frscrcmd_battle_castle.c')
    out += [p for p in re.findall(r'^static [^;{]*\);$', fr, re.M)]
    for head in (r'^BOOL FrontierScrCmd_InitBattleCastle\(', r'^BOOL FrontierScrCmd_LoadTrainersForRound\(',
                 r'^BOOL FrontierScrCmd_FreeBattleCastle\(', r'^BOOL FrontierScrCmd_BattleCastle_CleanupBattle\(',
                 r'^BOOL FrontierScrCmd_BattleCastle_StartBattle\(', r'^static void SetupBattleCastleAppArgs\(',
                 r'^static void StoreBattleCastleAppResult\(', r'^BOOL FrontierScrCmd_BattleCastle_SetupFirstOpponent\(',
                 r'^BOOL FrontierScrCmd_BattleCastle_SetupNextOpponent\(', r'^BOOL FrontierScrCmd_CallBattleCastleFunction\(',
                 r'^BOOL FrontierScrCmd_BattleCastle_CheckWonBattle\(', r'^BOOL FrontierScrCmd_GetCurrentCastlePoints\(',
                 r'^BOOL FrontierScrCmd_SpendCastlePoints\(', r'^BOOL FrontierScrCmd_ReceiveCastlePoints\('):
        out.append(body(fr, head))
    sc = src('src/scrcmd_battle_castle.c')
    out.append(body(sc, r'^static void BattleCastle_ClearActiveStreak\('))
    stats = src('src/battle_frontier_stats.c')
    for name in ('GetCastleRankIndex', 'GetCastleLatestStreakIndex', 'GetCastleRecordStreakIndex', 'GetCastleLatestCPIndex',
                 'GetCastleSpentCPIndex', 'GetCastleRecordCPIndex'):
        out.append(body(stats, r'^enum BattleFrontierStatsIndex BattleFrontierStats_' + name + r'\('))
    out.append(body(stats, r'^int BattleFrontierStats_GetHostFriendIdx\('))
    sv = src('src/battle_frontier_save.c')
    for name in ('u16 BattleFrontierSave_GetStat', 'u16 BattleFrontierSave_SetStat', 'u16 BattleFrontierSave_AddToStat',
                 'u16 BattleFrontierSave_SubtractFromStat', 'u16 BattleFrontierSave_SetIfBetter'):
        out.append(body(sv, '^' + re.escape(name) + r'\('))
    fo = src('src/overlay104/frontier_opponents.c')
    for head in (r'^static FrontierTrainerBase \*BattleFrontier_GetTrainerBase\(', r'^void BattleFrontier_GetPokemonBase\(',
                 r'^FrontierTrainerBase \*BattleFrontier_GetTrainer\(', r'^static const u16 sFrontierPokemonDefaultItems\[\] =',
                 r'^static u32 FrontierPokemon_Init\(', r'^void FrontierPokemon_InitPokemon\(',
                 r'^void BattleFrontier_LoadTrainer\(', r'^u32 BattleFrontier_LoadOpponentMonData\(',
                 r'^void BattleFrontier_LoadFrontierPokemon\(', r'^static u8 GetIVsForTrainer\(',
                 r'^static BOOL SelectPokemonForTrainer\(', r'^void BattleFrontier_GetPokemonForTrainers\('):
        out.append(body(fo, head))
    it = src('src/item_use_pokemon.c')
    top = it[:it.index('static u8 IsMoveMissingPP(')]          # the defines and macros
    out.append(without_includes(top))
    out += re.findall(r'^static [^;{]*\);$', it, re.M)        # the file's prototypes
    for head in (r'^u8 Pokemon_ApplyItemEffects\(', r'^static u8 IsMoveMissingPP\(', r'^static u8 RestorePokemonMovePP\(',
                 r'^static u8 IncreaseMovePPUps\(', r'^static void RestorePokemonHP\(', r'^static s32 CalculateEVUpdate\(',
                 r'^void Party_HealAllMembers\('):
        out.append(body(it, head))
    # (the friendship change: no item the Castle uses gives one, so Pokemon_ApplyItemEffects never calls it here)
    out.append('static u8 UpdatePokemonFriendship(Pokemon *mon, s32 friendship, s32 change, u16 location, enum HeapID heapID)\n'
               '{\n    (void)mon, (void)friendship, (void)change, (void)location, (void)heapID;\n    return 1;\n}\n')
    hp = src('src/applications/frontier/battle_castle/helpers.c')
    for head in (r'^u8 BattleCastleApp_GetSelectedSlot\(', r'^u8 BattleCastleApp_GetSlotFromSlotID\(',
                 r'^u8 BattleCastleApp_GetRank\(', r'^void BattleCastleApp_PlaySound\('):
        out.append(body(hp, head))
    mon = src('src/pokemon.c')
    out.append(body(mon, r'^static inline BOOL Pokemon_InlineIsPersonalityShiny\('))
    out.append(body(mon, r'^u8 Pokemon_IsPersonalityShiny\('))
    out.append(body(mon, r'^u8 Pokemon_GetNatureOf\('))
    out.append(body(mon, r'^u32 FlagIndex\('))
    out.append('void Plat_ClearActiveStreak(SaveData *saveData, u8 challengeType)\n{\n'
               '    BattleCastle_ClearActiveStreak(saveData, BattleCastlePersistentSave_Get(saveData), challengeType);\n}\n'
               'u16 Plat_GetAIMask(BattleCastle *castle) { return BattleCastle_GetAIMask(castle); }\n'
               'void Plat_SetupAppArgs(BattleCastleAppArgs *args, BattleCastle *castle) { SetupBattleCastleAppArgs(args, castle); }\n'
               'void Plat_StoreAppResult(BattleCastleAppArgs *args) { StoreBattleCastleAppResult(args); }\n')
    return '\n\n'.join(out) + '\n'


# The screens: State_MainAppFlow and the functions its purchases run through, the rest of each file's own functions are drawing
# (app_stubs.h: nothing)
SELF_REAL = (r'^static void HealPokemon\(', r'^static void RentItem\(', r'^static void IncreaseRank\(',
             r'^static BOOL IsMonMissingPP\(', r'^static u16 GetItemPriceFromListPos\(', r'^static u16 GetItemPrice\(',
             r'^static u16 GetItemIDFromListPos\(', r'^static void ApplyItemEffect\(', r'^static BOOL State_MainAppFlow\(')
OPP_REAL = (r'^static u16 GetCostOfLevelAdjustment\(', r'^static void PrintCostOfLevelAdjustment\(',
            r'^static void UpdateLevelAdjustment\(', r'^static void RevealPokemonInSlot\(', r'^static BOOL TryToBuySummaryScreen\(',
            r'^static void UnlockStatsForSlot\(', r'^static void BuyStatsDisplay\(', r'^static void UnlockMovesForSlot\(',
            r'^static void BuyMovesListDisplay\(', r'^static void IncreaseRank\(', r'^static BOOL State_MainAppFlow\(')


# The harness's way in: the screen's struct set up as its Init sets it (the fields its purchases read; the drawing's left out),
# its state, the Pokémon the cursor is on
GLUE = {
    'SELF': '''BattleCastleSelfApp *Glue_NewSelfApp(SaveData *saveData, BattleCastleAppArgs *args)
{
    BattleCastleSelfApp *app = calloc(1, sizeof(BattleCastleSelfApp));
    app->saveData = args->saveData;
    app->castleSave = BattleCastleSave_Get(app->saveData);
    app->persistentSave = BattleCastlePersistentSave_Get(app->saveData);
    app->challengeType = args->challengeType;
    app->selectedMonSlotPtr = &args->selectedMonSlot;
    app->party = args->party;
    app->slotID = 0xff;
    app->partnersCP = args->partnersCP;
    app->frontier = SaveData_GetBattleFrontier(app->saveData);
    for (int i = 0; i < BATTLE_CASTLE_NUM_RANK_TYPES; i++) {
        app->partnersRanks[i] = 1;
    }
    app->numSlots = BattleCastle_IsMultiPlayerChallenge(app->challengeType) ? NUM_MONS_MAX : 3;
    app->exitSlot = app->numSlots;
    app->previousSlot = app->exitSlot - 1;
    (void)saveData;
    return app;
}
int Glue_SelfSubState(BattleCastleSelfApp *app) { return app->subState; }
void Glue_SelfSetSlot(BattleCastleSelfApp *app, int slot) { app->selectedMonSlot = slot; *app->selectedMonSlotPtr = slot; }
''',
    'OPP': '''BattleCastleOpponentApp *Glue_NewOppApp(SaveData *saveData, BattleCastleAppArgs *args)
{
    BattleCastleOpponentApp *app = calloc(1, sizeof(BattleCastleOpponentApp));
    app->saveData = args->saveData;
    app->castleSave = BattleCastleSave_Get(app->saveData);
    app->persistentSave = BattleCastlePersistentSave_Get(app->saveData);
    app->challengeType = args->challengeType;
    app->selectedMonSlotPtr = &args->selectedMonSlot;
    app->identityUnlockedForSlot = &args->identityUnlocked[0];
    app->levelAdjustmentForSlot = &args->levelAdjustments[0];
    app->statsUnlockedForSlot = &args->statsUnlocked[0];
    app->movesUnlockedForSlot = &args->movesUnlocked[0];
    app->opponentsParty = args->opponentsParty;
    app->slotID = 0xff;
    app->partnersCP = args->partnersCP;
    app->frontier = SaveData_GetBattleFrontier(app->saveData);
    for (int i = 0; i < BATTLE_CASTLE_NUM_RANK_TYPES; i++) {
        app->partnersRanks[i] = 1;
    }
    app->numSlots = BattleCastle_IsMultiPlayerChallenge(app->challengeType) ? NUM_MONS_MAX : 3;
    app->exitSlot = app->numSlots;
    app->previousSlot = app->exitSlot - 1;
    (void)saveData;
    return app;
}
int Glue_OppSubState(BattleCastleOpponentApp *app) { return app->subState; }
void Glue_OppSetSlot(BattleCastleOpponentApp *app, int slot) { app->selectedMonSlot = slot; *app->selectedMonSlotPtr = slot; }
''',
}


def app(path, real, prefix, stub_kind):
    t = src(path)
    first = re.search(r'^(BOOL|static BOOL|void|static void|u8|static u8) \w+\([^;]*\)\s*$\n\{', t, re.M).start()
    head = without_includes(t[:first])
    # (the list template's callbacks are drawing: its definition goes with them)
    head = re.sub(r'static const ListMenuTemplate \w+ = \{.*?\n\};\n', '', head, flags=re.S)
    tables = []
    for m in re.finditer(r'^static const (u16|u32) (s\w+)\[[^=]*= \{', t[first:], re.M):
        tables.append(body(t, r'^static const ' + m.group(1) + ' ' + m.group(2) + r'\[[^=]*='))
    funcs = [body(t, h) for h in real]
    out = [f'// {path}: its state machine, copied by extract.py (do not edit)', '#include "plat_shim.h"',
           f'#define APP_STUBS_{stub_kind} 1', head, '#include "app_stubs.h"'] + tables + funcs + [GLUE[stub_kind]]
    names = {m: f'{prefix}_{m}' for m in ('State_MainAppFlow',)}
    text = '\n\n'.join(out) + '\n'
    for a, b in names.items():
        text = re.sub(r'\b' + a + r'\b', b, text)
    # the screen's struct is the harness's to set up: its static functions stay in the file, reached through these
    text = re.sub(r'^static BOOL ' + prefix + '_State_MainAppFlow', 'BOOL ' + prefix + '_State_MainAppFlow', text, flags=re.M)
    return text


if __name__ == '__main__':
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'plat_consts.h'), 'w').write(consts())
    open(os.path.join(d, 'plat_types.h'), 'w').write(types())
    open(os.path.join(d, 'plat_castle.c'), 'w').write(plat())
    open(os.path.join(d, 'plat_self_app.c'), 'w').write(app('src/applications/frontier/battle_castle/self_app.c', SELF_REAL,
                                                             'Self', 'SELF'))
    open(os.path.join(d, 'plat_opponent_app.c'), 'w').write(app('src/applications/frontier/battle_castle/opponent_app.c',
                                                                 OPP_REAL, 'Opp', 'OPP'))
    print(f'{d}: plat_consts.h, plat_types.h, plat_castle.c, plat_self_app.c, plat_opponent_app.c')
