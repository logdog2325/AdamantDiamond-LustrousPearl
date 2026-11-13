"""The Arcade harness's Platinum side (notes/PLATINUM_FRONTIER.md "The Battle Arcade"): Platinum's own Battle Arcade C, copied as it
is out of pokeplatinum, function by function, plus the constants and structs it names.

    python3 b2tools/platinum_arcade_host/extract.py OUT_DIR

OUT_DIR/plat_consts.h   the decomp's generated constants the copied code names (items, species, the Frontier Trainers, the records'
                        ids, the Arcade's functions)
OUT_DIR/plat_types.h    the structs, as the decomp's headers have them (BattleArcade, BattleArcadeSave, FrontierPokemon, ...)
OUT_DIR/plat_arcade.c   src/overlay104/battle_arcade.c (its rules: all but the drawing), battle_arcade_helpers.c and
                        src/battle_arcade_save.c (all but the includes), frscrcmd_battle_arcade.c (the scene's commands the rules
                        run through: InitBattleArcade .. CallBattleArcadeFunction, ApplyArcadeEffect, the battle's start and cleanup,
                        the board's arguments and results), scrcmd_battle_arcade.c (the lobby's streak deletion), frontier_opponents.c
                        (the Trainers and their Pokémon), battle_frontier_save.c and battle_frontier_stats.c (the records),
                        item_use_pokemon.c (Party_HealAllMembers)
OUT_DIR/plat_app.c      the board (applications/frontier/battle_arcade/main.c): BattleArcadeApp_Init, _Main and _Exit, its states
                        and the functions they decide through; its drawing does nothing (app_stubs.h)
plat_shim.h gives them the types and the calls into the rest of the game (the save, the party, the battle's setup, the sets, the
scene's context, the screens' drawing, which does nothing here). Two edits to Platinum's text, named where they are made:
- LoadTrainersAndMonsFromSave's ivs array, which Platinum never sets, starts at 0 (arcade_rules.c does the same, as the Castle's);
- AssignEffectsToGrid's remainder by the count of a kind of effect, which is 0 for the field's effects in rounds 1 and 5, is the
  DS's (Plat_DSMod: 0, as _s32_div_f, whose bytes are the same in Platinum and Black 2; platinum_arcade_data.py checks them). The
  host's would be the dividend (arm64) or a trap.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PLAT = os.path.join(ROOT, 'external', 'pokeplatinum')


def _body(text, head):
    """The function or table that starts with `head` (a regex), to its closing brace (as the core's harness does)."""
    m = re.search(head, text, re.M)
    assert m, head
    i = text.index('{', m.end() - 1 if text[m.end() - 1] == '{' else m.end())
    depth = 0
    for j in range(i, len(text)):
        if text[j] == '{':
            depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                if text[end:end + 1] == ';':
                    end += 1
                return text[m.start():end]
    raise ValueError(head)


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
    out = ['// Platinum\'s constants for the copied Battle Arcade code (extract.py; do not edit)', '#ifndef PLAT_CONSTS_H',
           '#define PLAT_CONSTS_H']
    for name in ('items', 'species'):
        out += [f'#define {n.split("=")[0].strip()} {i}' for i, n in enumerate(lines(name + '.txt'))]
    flags = lines('ai_flags.txt')           # a mask: NONE 0, then bits
    out += [f'#define {flags[0]} 0'] + [f'#define {n} (1 << {i})' for i, n in enumerate(flags[1:])]
    order = [l.strip() for l in open(os.path.join(PLAT, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    out += [f'#define FRONTIER_TRAINER_{n.upper()} {i}' for i, n in enumerate(order)]
    out += [f'#define {n} {v}' for n, v in enum_values(src('include/constants/battle_frontier_stats.h'),
                                                         'enum BattleFrontierStatsIndex').items()]
    t = src('include/constants/battle_arcade_functions.h')
    for e in ('enum BattleArcadeLobbyFunction', 'enum BattleArcadeFunction'):
        out += [f'#define {n} {v}' for n, v in enum_values(t, e).items()]
    t = src('include/constants/battle_frontier.h')
    out += [l for l in t.split('\n') if re.match(r'#define (ARCADE_|NUM_ARCADE_)', l)]
    out += [l for l in src('include/constants/overworld_weather.h').split('\n') if re.match(r'#define OVERWORLD_WEATHER_', l)]
    out += [l for l in src('include/battle_arcade_save.h').split('\n') if re.match(r'#define ARCADE_SAVE_', l)]
    out.append('#endif')
    return '\n'.join(out) + '\n'


def struct(path, name):
    """typedef struct NAME { ... } NAME; out of a header, as it is."""
    t = src(path)
    m = re.search(r'^typedef struct ' + name + r' \{.*?^\} ' + name + ';', t, re.M | re.S)
    assert m, name
    return m.group(0)


def types():
    out = ['// Platinum\'s structs for the copied Battle Arcade code (extract.py; do not edit)', '#ifndef PLAT_TYPES_H',
           '#define PLAT_TYPES_H']
    for path, name in (('include/struct_defs/frontier_pokemon_base.h', 'FrontierPokemonBase'),
                       ('include/struct_defs/frontier_trainer_base.h', 'FrontierTrainerBase'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierTrainer'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierPokemon'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierOpponent'),
                       ('include/battle_arcade_save.h', 'BattleArcadeSave'),
                       ('include/battle_arcade_save.h', 'BattleArcadeStreakFlags'),
                       ('include/applications/frontier/battle_arcade/main.h', 'BattleArcadeAppArgs'),
                       ('include/overlay104/battle_arcade.h', 'BattleArcade')):
        out.append(struct(path, name))
    for path in ('include/overlay104/battle_arcade.h', 'include/overlay104/battle_arcade_helpers.h',
                 'include/battle_arcade_save.h', 'include/applications/frontier/battle_arcade/main.h'):
        out += re.findall(r'^[A-Za-z][\w \*]*\([^;{]*\);$', src(path), re.M)     # the headers' prototypes
    out.append('#endif')
    return '\n'.join(out) + '\n'


# battle_arcade.c: its drawing (the effect's screen, the sprites, the palette) and the link's messages are the game's, not the rules':
# plat_shim.h's stubs stand for them
DRAWING = ('BattleArcade_UpdateBackgroundForEffect', 'BattleArcade_LoadNormalBackground', 'BattleArcade_CreateMonSprites',
           'BattleArcade_DeleteMonSprites', 'BattleArcade_SetPlayerMonSpriteDrawFlag', 'BattleArcade_SetOpponentMonSpriteDrawFlag',
           'BattleArcade_CreateItemSprites', 'BattleArcade_DeleteItemSprites', 'BattleArcade_SetItemDrawFlag',
           'BattleArcade_SetPalette', 'BattleArcade_SendCommMessage')


def plat():
    out = ['// Platinum\'s Battle Arcade rules, copied by extract.py from pokeplatinum (do not edit)', '#include "plat_shim.h"', '']
    ar = src('src/overlay104/battle_arcade.c')
    out += re.findall(r'^static [^;{]*\);$', ar, re.M)
    out.append('typedef void (*BattleArcadeEffectFunc)(BattleArcade *, Party *, u8);')
    for head in (r'^static const struct \{\n    u8 round;\n    u8 speed;\n\} sRouletteSpeedByRound\[\] =',
                 r'^BattleArcade \*BattleArcade_Init\(', r'^void BattleArcade_LoadTrainersForRound\(',
                 r'^static void SelectTrainersAndFirstBattlesMons\(', r'^static void LoadTrainersAndMonsFromSave\(',
                 r'^static void LoadPlayersPartyFromSave\(', r'^void BattleArcade_Free\(',
                 r'^void BattleArcade_StoreAppResults\(', r'^static u16 GetBattleArcadeAppCursorPos\(',
                 r'^void BattleArcade_Save\(', r'^u16 BattleArcade_IncrementCurrentBattle\(',
                 r'^u16 BattleArcade_GetCurrentBattle\(', r'^u16 BattleArcade_GetNextOpponentObjectID\(',
                 r'^u16 BattleArcade_GetTrainerOffset\(', r'^void BattleArcade_SaveOnLoss\(',
                 r'^void BattleArcade_SaveOnCompletingRound\(', r'^void BattleArcade_SetupFirstOpponentsParty\(',
                 r'^void BattleArcade_SetupNextOpponentsParty\(',
                 r'^static const u8 sPerformanceByNumWithStatus\[[^=]*=', r'^static const u8 sPerformanceByNumFainted\[[^=]*=',
                 r'^static const struct \{\n    u8 turns;\n    u8 score;\n\} sPerformanceByTurnsElapsed\[\] =',
                 r'^int BattleArcade_GetPerformance\(', r'^static int CalcBasePerformance\(',
                 r'^static const u16 sItemPoolTier1\[\] =', r'^static const u16 sItemPoolTier2\[\] =',
                 r'^static const u16 sItemPoolTier3\[\] =', r'^static const u16 \*sItemPools\[\] =',
                 r'^static const u16 sBerryPoolTier1\[\] =', r'^static const u16 sBerryPoolTier2\[\] =',
                 r'^static const u16 sBerryPoolTier3\[\] =', r'^static const u16 \*sBerryPools\[\] =',
                 r'^static BattleArcadeEffectFunc sBattleArcadeEffectFunctions\[[^=]*=',
                 r'^void BattleArcade_ApplyEffect\(') + tuple(
                     r'^static void ArcadeEffect_' + n + r'\(' for n in (
                         'LowerHP', 'Poison', 'Paralyze', 'Burn', 'Sleep', 'Freeze', 'GetBerry', 'GetItem', 'LevelUp', 'Sunny',
                         'Rainy', 'Sandy', 'Hail', 'Foggy', 'TrickRoom', 'SpeedUp', 'SlowDown', 'RandomizeCursor', 'SwapMons',
                         'GetFreeBP', 'NoBattle', 'NoEvent')) + (
                 r'^u16 BattleArcade_GetEarnedBP\(', r'^void BattleArcade_SaveItemsAfterBattle\('):
        b = body(ar, head)
        if 'LoadTrainersAndMonsFromSave' in head:      # the first edit: Platinum's ivs are never set (see the top)
            assert '    u8 ivs[MAX_PARTY_SIZE];\n' in b
            b = b.replace('    u8 ivs[MAX_PARTY_SIZE];\n', '    u8 ivs[MAX_PARTY_SIZE] = { 0 }; // (extract.py: never set)\n')
        out.append(b)
    out.append(without_includes(src('src/overlay104/battle_arcade_helpers.c')))
    out.append(without_includes(src('src/battle_arcade_save.c')))
    fr = src('src/overlay104/frscrcmd_battle_arcade.c')
    out += [p for p in re.findall(r'^static [^;{]*\);$', fr, re.M)]
    for head in (r'^BOOL FrontierScrCmd_InitBattleArcade\(', r'^BOOL FrontierScrCmd_BattleArcade_LoadTrainersForRound\(',
                 r'^BOOL FrontierScrCmd_FreeBattleArcade\(', r'^BOOL FrontierScrCmd_BattleArcade_CleanupBattle\(',
                 r'^BOOL FrontierScrCmd_BattleArcade_StartBattle\(', r'^BOOL FrontierScrCmd_OpenBattleArcadeApp\(',
                 r'^static void SetupBattleArcadeAppArgs\(',
                 r'^static void StoreBattleArcadeAppResults\(', r'^BOOL FrontierScrCmd_BattleArcade_SetupFirstOpponent\(',
                 r'^BOOL FrontierScrCmd_BattleArcade_SetupNextOpponent\(', r'^BOOL FrontierScrCmd_CallBattleArcadeFunction\(',
                 r'^static void CreateEmitter\(', r'^static void EmitterCallback\(',
                 r'^BOOL FrontierScrCmd_BattleArcade_CheckWonBattle\(', r'^BOOL FrontierScrCmd_ApplyArcadeEffect\('):
        out.append(body(fr, head))
    sc = src('src/scrcmd_battle_arcade.c')
    out.append(body(sc, r'^static void BattleArcade_ClearActiveStreak\('))
    stats = src('src/battle_frontier_stats.c')
    for name in ('GetArcadeLatestStreakIndex', 'GetArcadeCurrentStreakIndex'):
        out.append(body(stats, r'^enum BattleFrontierStatsIndex BattleFrontierStats_' + name + r'\('))
    out.append(body(stats, r'^int BattleFrontierStats_GetHostFriendIdx\('))
    sv = src('src/battle_frontier_save.c')
    for name in ('u16 BattleFrontierSave_GetStat', 'u16 BattleFrontierSave_SetStat', 'u16 BattleFrontierSave_SetIfBetter'):
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
    for head in (r'^static u8 IsMoveMissingPP\(', r'^static u8 RestorePokemonMovePP\(', r'^void Party_HealAllMembers\('):
        out.append(body(it, head))
    mon = src('src/pokemon.c')
    out.append(body(mon, r'^static inline BOOL Pokemon_InlineIsPersonalityShiny\('))
    out.append(body(mon, r'^u8 Pokemon_IsPersonalityShiny\('))
    out.append(body(mon, r'^u8 Pokemon_GetNatureOf\('))
    out.append(body(mon, r'^u32 FlagIndex\('))
    out.append('void Plat_ClearActiveStreak(SaveData *saveData, u8 challengeType)\n{\n'
               '    BattleArcade_ClearActiveStreak(saveData, BattleArcadeStreakFlags_Get(saveData), challengeType);\n}\n'
               'void Plat_SetupAppArgs(BattleArcadeAppArgs *args, BattleArcade *arcade) { SetupBattleArcadeAppArgs(args, arcade); }\n'
               'void Plat_StoreAppResults(BattleArcadeAppArgs *args) { StoreBattleArcadeAppResults(args); }\n')
    text = '\n\n'.join(out) + '\n'
    # (the static functions item_use_pokemon.c names that the harness doesn't copy: never reached from the heal)
    return text


# The board: these of main.c's own functions decide or time; the rest draw (app_stubs.h: nothing)
APP_REAL = (r'^BOOL BattleArcadeApp_Init\(', r'^BOOL BattleArcadeApp_Main\(', r'^BOOL BattleArcadeApp_Exit\(',
            r'^static BOOL State_FadeInApp\(', r'^static BOOL State_OperateRoulette\(', r'^static BOOL State_SyncResult\(',
            r'^static BOOL State_SyncBeforeExit\(', r'^static BOOL State_FadeOutApp\(', r'^static void ChangeState\(',
            r'^static void UpdateCursorPosition\(', r'^static void UpdateCursorSpritePosition\(',
            r'^static void SetResultCursorPos\(', r'^static u8 NormalizeCursorPosition\(', r'^static u16 GetBattleNumber\(',
            r'^static BOOL SendCommMessage\(', r'^static void CreateInitialLayoutPayload\(', r'^static void CreateResultPayload\(',
            r'^static u16 GetRandomNumber\(', r'^static void UnusedCommCommandPayload\(', r'^static void SetSelectedEffect\(',
            r'^static void GetAvailableEffects\(', r'^static void GetEffectCategoryCounts\(', r'^static void AssignEffectsToGrid\(',
            r'^static u8 GetRandomCategory\(', r'^static BOOL CheckStopButtonPressed\(', r'^static void PressStopButton\(')

GLUE = '''
// (extract.py) the harness's way in: the board's state and the cursor
int Glue_AppSubState(void *app) { return ((BattleArcadeApp *)app)->subState; }
int Glue_AppCursor(void *app) { return ((BattleArcadeApp *)app)->cursorPos; }
int Glue_AppTimer(void *app) { return ((BattleArcadeApp *)app)->rouletteTimer; }
const u8 *Glue_AppEffects(void *app) { return ((BattleArcadeApp *)app)->rouletteEffects; }
int Glue_AppStart(void *app) { return ((BattleArcadeApp *)app)->startingCursorPos; }
int Glue_AppTier(void *app) { return ((BattleArcadeApp *)app)->categoryTier; }
int Glue_AppAvailable(void *app, u8 *effects) {
    memcpy(effects, ((BattleArcadeApp *)app)->availableEffects, NUM_ARCADE_EFFECTS);
    return ((BattleArcadeApp *)app)->numAvailableEffects;
}
int Glue_CursorMoveFrames(int speed) { return sCursorMoveFrames[speed][0]; }
'''


def app():
    t = src('src/applications/frontier/battle_arcade/main.c')
    first = re.search(r'^BOOL BattleArcadeApp_Init\(', t, re.M).start()
    head = without_includes(t[:first])
    funcs = []
    for h in APP_REAL:
        b = body(t, h)
        if 'AssignEffectsToGrid' in h:                # the second edit: the DS's remainder by zero (see the top)
            old = 'u16 start = LCRNG_Next() % numEffectsInCategory;'
            assert old in b
            b = b.replace(old, 'u16 start = Plat_DSMod(LCRNG_Next(), numEffectsInCategory); // (extract.py: the DS\'s remainder)')
        funcs.append(b)
    out = ['// applications/frontier/battle_arcade/main.c: the board, copied by extract.py (do not edit)', '#include "plat_shim.h"',
           head, '#include "app_stubs.h"'] + funcs + [GLUE]
    return '\n\n'.join(out) + '\n'


if __name__ == '__main__':
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'plat_consts.h'), 'w').write(consts())
    open(os.path.join(d, 'plat_types.h'), 'w').write(types())
    open(os.path.join(d, 'plat_arcade.c'), 'w').write(plat())
    open(os.path.join(d, 'plat_app.c'), 'w').write(app())
    print(f'{d}: plat_consts.h, plat_types.h, plat_arcade.c, plat_app.c')
