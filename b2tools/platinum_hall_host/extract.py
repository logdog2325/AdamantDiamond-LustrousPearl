"""The Hall harness's Platinum side (notes/PLATINUM_FRONTIER.md "The Battle Hall"): Platinum's own Battle Hall C, copied as it is
out of pokeplatinum, function by function, plus the constants it names.

    python3 b2tools/platinum_hall_host/extract.py OUT_DIR

OUT_DIR/plat_consts.h   the decomp's generated constants the copied code names (types, Trainer classes, species, AI flags, the
                        Frontier records' ids) and sFrontierTrainerClasses as the decomp's frontierproc writes it (Trainers 0-299,
                        from res/trainers/frontier/data: not from the dump, which our table is made from)
OUT_DIR/plat_types.h    the structs, as the decomp's headers have them (BattleHall, BattleHallSave, FrontierPokemon, ...)
OUT_DIR/plat_rules.c    src/overlay104/battle_hall.c (the rules' functions), battle_hall_helpers.c (all of it but the includes),
                        src/battle_hall_save.c, battle_hall_win_records.c, the Hall's record ids of battle_frontier_stats.c,
                        frontier_opponents.c (BattleFrontier_GetTrainer, BattleFrontier_LoadTrainer, FrontierPokemon_Init,
                        BattleFrontier_LoadOpponentMonData, FrontierPokemon_InitPokemon), pokemon.c (the shiny test, the nature, the form's personal entry)
plat_shim.h gives them the types and the calls into the rest of the game (the save, the party, the battle's setup, the sets).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PLAT = os.path.join(ROOT, 'external', 'pokeplatinum')
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(ROOT, 'b2tools', 'platinum_frontier_host'))
from extract import body as _body  # noqa: E402  (the core's harness: a function or table by its head, braces matched)


def body(text, head):
    """A definition (its head line doesn't end with ';': a static function's prototype comes first in these files)."""
    return _body(text, head if head.endswith('=') else head + r'[^;\n]*$')


def src(path):
    return open(os.path.join(PLAT, path)).read()


def lines(name):
    return [l.strip() for l in open(os.path.join(PLAT, 'generated', name)) if l.strip()]


def consts():
    out = ['// Platinum\'s constants for the copied Battle Hall code (extract.py; do not edit)', '#ifndef PLAT_CONSTS_H',
           '#define PLAT_CONSTS_H']
    for name in ('pokemon_types', 'trainer_classes', 'species', 'items'):
        out += [f'#define {n.split("=")[0].strip()} {i}' for i, n in enumerate(lines(name + '.txt'))]
    flags = lines('ai_flags.txt')           # a mask (generated/meson.build 'ai_flags': type mask, no auto): NONE 0, then bits
    out += [f'#define {flags[0]} 0'] + [f'#define {n} (1 << {i})' for i, n in enumerate(flags[1:])]
    order = [l.strip() for l in open(os.path.join(PLAT, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    out += [f'#define FRONTIER_TRAINER_{n.upper()} {i}' for i, n in enumerate(order)]
    t = src('include/constants/battle_frontier_stats.h')
    enum = t[t.index('{', t.index('enum BattleFrontierStatsIndex')):]
    value, known = 0, {}
    for n, v in re.findall(r'^\s*(STAT\w+)(?:\s*=\s*(\w+))?,', enum, re.M):
        if v:
            value = int(v, 0) if v[0].isdigit() else known[v]
        known[n] = value
        value += 1
    out += [f'#define {n} {v}' for n, v in known.items()]
    out.append('#endif')
    return '\n'.join(out) + '\n'


def frontier_classes():
    """sFrontierTrainerClasses as frontierproc writes it (tools/dataproc/src/frontierproc.c: Trainers before Cheryl)."""
    order = [l.strip() for l in open(os.path.join(PLAT, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    first_partner = order.index('trainer_cheryl_cheryl')
    names = [json.load(open(os.path.join(PLAT, 'res', 'trainers', 'frontier', 'data', n + '.json')))['class']
             for n in order[:first_partner]]
    return 'static const u16 sFrontierTrainerClasses[] = {\n' + ''.join(f'    {n},\n' for n in names) + '};\n'


def struct(path, name):
    """typedef struct NAME { ... } NAME; out of a header, as it is."""
    t = src(path)
    m = re.search(r'^typedef struct ' + name + r' \{.*?^\} ' + name + ';', t, re.M | re.S)
    assert m, name
    return m.group(0)


def types():
    out = ['// Platinum\'s structs for the copied Battle Hall code (extract.py; do not edit)', '#ifndef PLAT_TYPES_H',
           '#define PLAT_TYPES_H']
    for path, name in (('include/struct_defs/frontier_pokemon_base.h', 'FrontierPokemonBase'),
                       ('include/struct_defs/frontier_trainer_base.h', 'FrontierTrainerBase'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierTrainer'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierPokemon'),
                       ('include/overlay104/frontier_opponents.h', 'FrontierOpponent'),
                       ('include/battle_hall_save.h', 'BattleHallSave'),
                       ('include/battle_hall_save.h', 'BattleHallStreakFlags'),
                       ('include/battle_hall_win_records.h', 'BattleHallWinRecords'),
                       ('include/overlay104/battle_hall.h', 'BattleHall'),
                       ('include/applications/frontier/battle_hall/main.h', 'BattleHallAppArgs')):
        out.append(struct(path, name))
    for path in ('include/overlay104/battle_hall.h', 'include/overlay104/battle_hall_helpers.h', 'include/battle_hall_save.h',
                 'include/battle_hall_win_records.h', 'include/battle_frontier_stats.h'):
        t = src(path)                          # the headers' defines and prototypes
        out += [l for l in t.split('\n') if re.match(r'#define (HALL_SAVE_|BATTLE_HALL_)', l)]
        out += re.findall(r'^[A-Za-z][\w \*]*\([^;{]*\);$', t, re.M)
    out.append('#endif')
    return '\n'.join(out) + '\n'


def without_includes(text):
    return '\n'.join(l for l in text.split('\n') if not l.startswith('#include') and 'FS_EXTERN_OVERLAY' not in l)


def plat():
    out = ['// Platinum\'s Battle Hall rules, copied by extract.py from pokeplatinum (do not edit)', '#include "plat_shim.h"', '']
    hall = src('src/overlay104/battle_hall.c')
    out += re.findall(r'^static [^;{]*\);$', hall, re.M)
    for head in (r'^BattleHall \*BattleHall_Init\(', r'^void BattleHall_SetupNextOpponent\(', r'^static void SetupNextOpponent\(',
                 r'^void BattleHall_GetTypeSelectionAppResult\(', r'^static u16 GetBattleHallAppSelectedCell\(',
                 r'^void BattleHall_UpdateWinRecordForCurrentMon\(', r'^void BattleHall_Save\(',
                 r'^u16 BattleHall_IncrementCurrentBattle\(', r'^void BattleHall_SaveOnLoss\(',
                 r'^void BattleHall_SaveOnCompletingRound\(', r'^u16 BattleHall_GetEarnedBP\(',
                 r'^static u16 BattleHall_LoadTypeRanks\(', r'^static void BattleHall_SaveTypeRank\(',
                 r'^void BattleHall_CapTypeRanks\(', r'^void BattleHall_CalcPlayerLevelSqrt\(',
                 r'^static u16 BattleHall_CalcOpponentsLevel\('):
        out.append(body(hall, head))
    helpers = without_includes(src('src/overlay104/battle_hall_helpers.c'))
    out.append(helpers.replace('#include "res/trainers/frontier/frontier_trainer_classes.h"', ''))
    # (the copied helpers file names sFrontierTrainerClasses where it is included: the table goes before it)
    out.insert(3, frontier_classes())
    out.append(without_includes(src('src/battle_hall_save.c')))
    out.append(without_includes(src('src/battle_hall_win_records.c')))
    stats = src('src/battle_frontier_stats.c')
    for name in ('BattleFrontierStats_GetHallCurrentTypeRanksIndex', 'BattleFrontierStats_GetHallLatestStreakIndex',
                 'BattleFrontierStats_GetHallCurrentStreakIndex', 'BattleFrontierStats_GetHallLatestSpeciesIndex',
                 'BattleFrontierStats_GetHallRecordStreakIndex'):
        out.append(body(stats, r'^enum BattleFrontierStatsIndex ' + name + r'\('))
    out.append(body(stats, r'^int BattleFrontierStats_GetHostFriendIdx\('))
    fo = src('src/overlay104/frontier_opponents.c')
    out.append(body(fo, r'^static FrontierTrainerBase \*BattleFrontier_GetTrainerBase\('))
    out.append(body(fo, r'^FrontierTrainerBase \*BattleFrontier_GetTrainer\('))
    out.append(body(fo, r'^void BattleFrontier_LoadTrainer\('))
    out.append(body(fo, r'^static const u16 sFrontierPokemonDefaultItems\[\] ='))
    out.append(body(fo, r'^static u32 FrontierPokemon_Init\('))
    out.append(body(fo, r'^u32 BattleFrontier_LoadOpponentMonData\('))
    out.append(body(fo, r'^void FrontierPokemon_InitPokemon\('))
    mon = src('src/pokemon.c')
    out.append(body(mon, r'^static inline BOOL Pokemon_InlineIsPersonalityShiny\('))
    out.append(body(mon, r'^u8 Pokemon_IsPersonalityShiny\('))
    out.append(body(mon, r'^u8 Pokemon_GetNatureOf\('))
    out.append(body(mon, r'^static int Pokemon_GetFormNarcIndex\('))
    out.append(body(mon, r'^u32 FlagIndex\('))
    # The harness reaches two of the static functions through these
    out.append('void Plat_SetupNextOpponent(BattleHall *bh) { SetupNextOpponent(bh); }\n'
               'u16 Plat_CalcOpponentsLevel(BattleHall *bh) { return BattleHall_CalcOpponentsLevel(bh); }\n'
               'int Plat_GetFormNarcIndex(int species, int form) { return Pokemon_GetFormNarcIndex(species, form); }\n'
               'u16 Plat_GetAIMask(BattleHall *bh, u8 battleNum, u8 rank) { return BattleHall_GetAIMask(bh, battleNum, rank); }\n'
               'u32 Plat_GetOpponentLevel(BattleHall *bh) { return BattleHall_GetOpponentLevel(bh, 0); }\n'
               'int Plat_OpponentCount(void) { return NELEMS(sBattleHallPotentialOpponents); }\n'
               'u16 Plat_Opponent(int i) { return sBattleHallPotentialOpponents[i]; }\n'
               'u16 Plat_OpponentType(int i, int j) { return sBattleHallPotentialOpponentTypes[i][j]; }\n'
               'u16 Plat_ClassByRank(int r, int c) { return sHallTrainerClassesByRank[r][c]; }\n'
               'u16 Plat_ClassByType(int t, int c) { return sHallTrainerClassesBySelectedType[t][c]; }\n'
               'int Plat_FrontierClassCount(void) { return NELEMS(sFrontierTrainerClasses); }\n'
               'u16 Plat_FrontierClass(int i) { return sFrontierTrainerClasses[i]; }\n')
    return '\n\n'.join(out) + '\n'


if __name__ == '__main__':
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'plat_consts.h'), 'w').write(consts())
    open(os.path.join(d, 'plat_types.h'), 'w').write(types())
    open(os.path.join(d, 'plat_rules.c'), 'w').write(plat())
    print(f'{d}: plat_consts.h, plat_types.h, plat_rules.c')
