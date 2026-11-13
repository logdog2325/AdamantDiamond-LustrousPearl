"""The Factory harness's Platinum side (notes/PLATINUM_FRONTIER.md "The Battle Factory"): Platinum's own C, copied as it is.

    python3 b2tools/platinum_factory_host/extract.py OUT_DIR

OUT_DIR/plat_types.h, plat_factory.c   Platinum's Battle Factory (pokeplatinum src/overlay104/battle_factory.c, battle_factory_helpers.c,
                         frontier_opponents.c, frscrcmd_battle_factory.c, src/scrcmd_battle_factory.c, src/battle_factory_save.c,
                         src/battle_frontier_stats.c, src/battle_frontier_save.c): the round's Trainers, the rentals, the
                         opponents' Pokémon, the swap, the records and the save, the Battle Points, CallBattleFactoryFunction.
Each is the decomp's own text, a function, table or struct at a time (by its name, braces matched); plat_shim.h gives them
the types and the few calls they make outside the rules (the heap, the party, the script context, the message loaders).
The other side, the code the ROM runs, is compiled as it is: src/pearlb2/plat_factory/factory_rules.c.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PLAT = os.path.join(ROOT, 'external', 'pokeplatinum')

def _core_body():
    import importlib.util
    spec = importlib.util.spec_from_file_location('frontier_host_extract', os.path.join(HERE, '..', 'platinum_frontier_host', 'extract.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.body


body = _core_body()      # the core harness's: a function or table by its head, braces matched


def src(path):
    return open(os.path.join(PLAT, path)).read()


def struct(text, name):
    """typedef struct NAME { ... } NAME; (or an anonymous typedef ending in NAME;)."""
    m = re.search(r'typedef struct (%s )?\{' % name, text)
    starts = [m.start()] if m and text[m.end():].find('} %s;' % name) >= 0 else []
    if not starts:
        end = text.index('} %s;' % name)
        start = text.rindex('typedef struct', 0, end)
    else:
        start = starts[0]
        end = text.index('} %s;' % name, start)
    return text[start:end + len('} %s;' % name)]


def plat():
    helpers = src('src/overlay104/battle_factory_helpers.c')
    factory = src('src/overlay104/battle_factory.c')
    opponents = src('src/overlay104/frontier_opponents.c')
    frscr = src('src/overlay104/frscrcmd_battle_factory.c')
    scrcmd = src('src/scrcmd_battle_factory.c')
    save = src('src/battle_factory_save.c')
    stats = src('src/battle_frontier_stats.c')
    fsave = src('src/battle_frontier_save.c')
    pokemon = src('src/pokemon.c')
    order = [l.strip() for l in open(os.path.join(PLAT, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    out = ['// Platinum\'s Battle Factory\'s types, copied by extract.py from pokeplatinum (do not edit)',
           '#ifndef FACTORY_HOST_PLAT_TYPES_H', '#define FACTORY_HOST_PLAT_TYPES_H', '#include "plat_shim.h"', '']
    out += [f'#define FRONTIER_TRAINER_{n.upper()} {i}' for i, n in enumerate(order)] + ['']
    flags = [l.strip() for l in src('generated/ai_flags.txt').split('\n') if l.strip()]
    out += ['#define AI_FLAG_NONE 0'] + [f'#define {n} (1 << {i})' for i, n in enumerate(flags[1:])] + [
        '// (generated/ai_flags.txt: a mask, the first name none)', '']
    enum = src('include/constants/battle_frontier_stats.h')
    out.append(enum[enum.index('enum BattleFrontierStatsIndex'):enum.index('#define STATS_NUM_WFC_STATS')].strip())
    out.append(src('include/constants/battle_frontier.h')[src('include/constants/battle_frontier.h').index('#define FRONTIER_CHALLENGE_SINGLE'):]
               .split('#endif')[0].strip())
    out.append(src('include/constants/battle_factory_functions.h').split('#define POKEPLATINUM_CONSTANTS_BATTLE_FACTORY_FUNCTIONS_H')[1]
               .split('#endif')[0].strip())
    opp_h = src('include/overlay104/frontier_opponents.h')
    for name in ('FrontierTrainer', 'FrontierPokemon', 'FrontierOpponent'):
        out.append(struct(opp_h, name))
    save_h = src('include/battle_factory_save.h')
    out += [l for l in save_h.split('\n') if re.match(r'#define FACTORY_SAVE_', l)]
    for name in ('BattleFactoryStreakFlags', 'BattleFactorySave'):
        out.append(struct(save_h, name))
    out.append('typedef struct BattleFrontierStats {\n    u16 soloStats[STATS_NUM_SOLO_STATS_AND_ACTIVE_FLAGS];\n'
               '    u16 wfcStats[1][1];\n} BattleFrontierStats;\n'
               '// (the harness\'s: the stats and the Factory\'s two parts of Platinum\'s BattleFrontierSave)\n'
               'typedef struct BattleFrontierSave {\n    BattleFrontierStats stats;\n    BattleFactorySave factorySave;\n'
               '    struct { BattleFactoryStreakFlags streakFlags; } factory;\n} BattleFrontierSave;')
    out.append(struct(src('include/overlay104/battle_factory_helpers.h'), 'BattleFactoryPokemonPool'))
    out.append(struct(src('include/overlay104/battle_factory.h'), 'BattleFactory'))
    out.append('typedef struct BattleFactoryAppArgs {\n    u16 selectedIndices[6];\n    BattleFactory *battleFactory;\n'
               '} BattleFactoryAppArgs;')
    out.append('#include "plat_protos.h"')
    types, out = out, ['// Platinum\'s Battle Factory, copied by extract.py from pokeplatinum (do not edit)', '#include "plat_types.h"',
                       '#include "plat_static.h"', '']
    # the records
    out.append(body(fsave, r'^u16 BattleFrontierSave_GetStat\('))
    out.append(body(fsave, r'^u16 BattleFrontierSave_SetStat\('))
    out.append(body(fsave, r'^u16 BattleFrontierSave_SetIfBetter\('))
    out.append(body(stats, r'^int BattleFrontierStats_GetHostFriendIdx\('))
    for kind in ('LatestStreakIdx', 'RecordStreakIdx', 'LatestTradeCountIndex', 'RecordTradeCountIndex'):
        out.append(body(stats, r'^enum BattleFrontierStatsIndex BattleFrontierStats_GetFactory' + kind + r'\('))
    for name in ('void BattleFactorySave_Init', 'BOOL BattleFactorySave_HasSaved', 'void BattleFactorySave_RecordSave',
                 'void BattleFactorySave_SetMember', 'u32 BattleFactorySave_GetMember',
                 'void BattleFactoryStreakFlags_SetFlag', 'u32 BattleFactoryStreakFlags_GetFlag'):
        out.append(body(save, '^' + re.escape(name) + r'\('))
    # the Pokémon (pokemon.c's two helpers the rules call)
    out.append(body(pokemon, r'^u8 Pokemon_GetNatureOf\('))
    out.append(body(pokemon, r'^static inline BOOL Pokemon_InlineIsPersonalityShiny\(.*\)$'))
    out.append(body(pokemon, r'^u8 Pokemon_IsPersonalityShiny\('))
    out.append(body(opponents, r'^static const u16 sFrontierPokemonDefaultItems\[\] ='))
    out.append(body(opponents, r'^static u32 FrontierPokemon_Init\('))
    out.append(body(opponents, r'^u32 BattleFrontier_LoadOpponentMonData\('))
    out.append(body(opponents, r'^void BattleFrontier_LoadFrontierPokemon\('))
    # the rules
    for head in (r'^static const struct \{\n    u16 normalMin;', r'^static const BattleFactoryPokemonPool sLevel50Pools\[\] =',
                 r'^static const BattleFactoryPokemonPool sOpenLevelOpponentPools\[\] =',
                 r'^static const BattleFactoryPokemonPool sOpenLevelPlayerPools\[\] =',
                 r'^static int BattleFactory_GetOpponentTrainerID\(u8 challengeType, int currentRound, int trainerOffset\)$',
                 r'^void BattleFactory_PickOpponentTrainers\(', r'^const BattleFactoryPokemonPool \*BattleFactory_GetPokemonPoolForTrainer\(',
                 r'^static const BattleFactoryPokemonPool \*GetPlayerPoolForRound\(int round, int isOpenLevel\)$',
                 r'^static const int sTradeCountsNeededForUpgrades\[\] =', r'^BOOL BattleFactory_SelectPokemonFromPool\(',
                 r'^u8 BattleFactory_GetPlayerPartySize\(', r'^u8 BattleFactory_GetOpponentPartySize\(',
                 r'^void BattleFactory_SelectInitialRentalOptions\(', r'^void BattleFactory_SelectInitialOpponentMons\(',
                 r'^u8 BattleFactory_GetPokemonLevel\(', r'^void BattleFactory_CreateInitialRentalParty\(',
                 r'^BOOL BattleFactory_IsMultiplayerChallenge\(', r'^static u16 BattleFactory_GetAIMask\(BattleFactory \*battleFactory\)$',
                 r'^u16 BattleFactory_GetCurrentRound\('):
        out.append(body(helpers, head))
    for head in (r'^BattleFactory \*BattleFactory_Init\(', r'^void BattleFactory_LoadTrainersAndRentalsForRound\(',
                 r'^static void SetupTrainersAndInitialRentalOptions\(BattleFactory \*factory\)$',
                 r'^static void SwapMonIndices\(BattleFactory \*factory, u8 idx1, u8 isPartners\)$',
                 r'^static void LoadTrainersAndMonsFromSave\(BattleFactory \*factory\)$',
                 r'^void BattleFactory_GetMonSelectionAppResult\(',
                 r'^static u16 GetBattleFactoryAppSelectedIndices\(BattleFactoryAppArgs \*args, u8 i\)$',
                 r'^void BattleFactory_Save\(', r'^u16 BattleFactory_IncrementCurrentBattle\(', r'^u16 BattleFactory_GetCurrentBattle\(',
                 r'^void BattleFactory_SaveOnLoss\(', r'^void BattleFactory_SaveOnCompletingRound\(',
                 r'^void BattleFactory_AddSelectedRentalsToParty\(', r'^void BattleFactory_SetupNextOpponent\(',
                 r'^void BattleFactory_ApplyTrade\(', r'^void BattleFactory_SetupNextOpponentsParty\(',
                 r'^void BattleFactory_IncrementTradeCount\(', r'^u16 BattleFactory_GetEarnedBP\('):
        out.append(body(factory, head))
    out.append(body(frscr, r'^BOOL FrontierScrCmd_CallBattleFactoryFunction\('))
    out.append(body(scrcmd, r'^BOOL ScrCmd_DeleteActiveBattleFactoryStreak\('))
    out.append('// (the harness\'s: the AI mask is static in Platinum)\nu16 Plat_GetAIMask(BattleFactory *factory)\n{\n'
               '    return BattleFactory_GetAIMask(factory);\n}')
    return '\n\n'.join(types) + '\n#endif\n', '\n\n'.join(out) + '\n'


if __name__ == '__main__':
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    types, code = plat()
    open(os.path.join(d, 'plat_types.h'), 'w').write(types)
    open(os.path.join(d, 'plat_factory.c'), 'w').write(code)
    print(f'{d}: plat_types.h, plat_factory.c')
