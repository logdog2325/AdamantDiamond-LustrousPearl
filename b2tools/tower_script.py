"""Pearl's Battle Tower commands in Black 2's terms, for the story generator (pearl_story.py; notes/BATTLE_ZONE.md).

Pearl's scripts run as they are. Its tower commands (pokeplatinum unk_020494DC.c, the same numbers as Pearl's) become
Black 2's Battle Subway commands (script plugin 1: BSubwayCmd_Tool, decomp src/ov050/scrcmd_bsubway.c) or the tower's
extension sub-commands (0x80-0x9F, decomp src/pearlb2/resident/tower.c, macros in src/include/pearl_story.inc).

Modes: Pearl's 0 Single, 1 Double, 2 Multi with a partner are Black 2's play modes 0, 1, 2. Wi-Fi and the wireless
Multi are closed (the lead, 2026-11-01): the Wi-Fi receptionist is a closed place (data/pearl_closed_facilities.json),
and the Multi receptionist doesn't ask about a friend (data/pearl_script_patches.json). What only those paths use
stays a stub.
"""

ZONES = ('MAP_BATTLE_TOWER_LOBBY', 'MAP_BATTLE_TOWER_ELEVATOR', 'MAP_BATTLE_TOWER_CORRIDOR_MULTI',
         'MAP_BATTLE_TOWER_CORRIDOR_WIFI', 'MAP_BATTLE_TOWER_ARENA_MULTI', 'MAP_BATTLE_TOWER_ARENA_WIFI',
         'MAP_BATTLE_TOWER_PARTNER_ROOM')
LOBBY = 'MAP_BATTLE_TOWER_LOBBY'
# Where a saved challenge resumes: in front of the room's receptionist (Pearl's returning Warps), facing up
LOBBY_RESUME = {'MAP_BATTLE_TOWER_ARENA_MULTI': (11, 6), 'MAP_BATTLE_TOWER_ARENA_WIFI': (7, 6), LOBBY: (11, 6)}
# The opponents' people in each arena, by opponent number
OPPONENT_OBJECTS = {'MAP_BATTLE_TOWER_ARENA_MULTI': (1,), 'MAP_BATTLE_TOWER_ARENA_WIFI': (4, 5)}
FLAG_CONTINUE_SCRIPT = 2405


def is_tower(tr):
    return tr.job.zone['name'] in ZONES


def _tool(cmd, p0=0, p1=0, ret=0):
    return f'BSubwayCmd_Tool {cmd}, {p0}, {p1}, {ret}'


def h_function(tr, vals):
    """Pearl's CallBattleTowerFunction function, argument, var."""
    fn, arg, var = vals
    v, a = tr.var(var), tr.var(arg)
    zone = tr.job.zone['name']
    simple = {
        2: (1, 0),      # reset the system (Black 2's OS_ResetSystem)
        3: (2, 0),      # forget the saved challenge
        4: (3, 1),      # is a challenge saved?
        14: (7, 1),     # the saved challenge's streak ends: its mode
        33: (8, 1),     # the next opponent's number
        34: (357, 1),   # one more win
        35: (303, 1),   # seven won?
        36: (358, 1),   # the streak
        37: (304, 0),   # lost: records
        38: (305, 0),   # seven won: records
        40: (307, 0),   # the next opponent's team
        43: (21, 1),    # the mode
        45: (312, 1),   # beat Palmer?
        46: (313, 1),   # the Battle Points award
    }
    if fn in simple:
        cmd, has_ret = simple[fn]
        return [_tool(cmd, 0, 0, v if has_ret else 0) + f'  // Pearl tower function {fn}']
    if fn == 1:                 # enough Pokémon? Mode 2 asks before any work exists, so the mode comes from the argument
        mode = 2 if arg == 2 else 255
        return [f'pl_TowerCheckParty {mode}, {v}  // Pearl tower function 1 ({arg} Pokémon)']
    if fn in (5, 6):            # Pearl's Communication Club doors: Black 2's work needs none
        return [f'// Pearl tower function {fn}: nothing to do']
    if fn == 30:                # the party screen
        return [_tool(300) + '  // Pearl tower function 30: the party screen']
    if fn == 31:                # the choice
        return [_tool(301, 0, 0, v) + '  // Pearl tower function 31: 1 = chosen']
    if fn == 32:                # Black 2's party screen doesn't let duplicates through
        return [f'pl_SetVarFromValue {v}, 0  // Pearl tower function 32: the party screen checks them']
    if fn == 39:                # save and quit: the challenge resumes in the lobby on Continue
        x, z = LOBBY_RESUME.get(zone, LOBBY_RESUME[LOBBY])
        lobby = tr.job.pd.b2_zone[next(z_['id'] for z_ in tr.job.pd.zones if z_['name'] == LOBBY)]
        return [_tool(306) + '  // Pearl tower function 39: the play block keeps the challenge',
                f'FieldSetNextZone {lobby}, 1, {x}, 0, {z}',
                f'FlagSet {FLAG_CONTINUE_SCRIPT}']
    if fn == 41:                # the opponent's sprite
        return [_tool(308, a, 0, v) + '  // Pearl tower function 41']
    if fn == 42:                # the battle
        return [_tool(309) + '  // Pearl tower function 42: the battle']
    if fn == 44:                # beat Palmer: 1 silver, 2 gold
        return [_tool(311, a) + '  // Pearl tower function 44']
    if fn in (48, 49):          # Black 2 has no ribbon script commands (OPEN_CONTENT: the Ribbon Syndicate)
        tr.job.approx[f'CallBattleTowerFunction {fn} (the tower\'s ribbons: none in Black 2)'] += 1
        return [f'pl_SetVarFromValue {v}, 0  // Pearl tower function {fn}: no ribbons']
    if fn == 50:
        return [f'pl_TowerSetPartner {a}  // Pearl tower function 50']
    if fn == 51:
        return [f'pl_TowerGetPartner {v}  // Pearl tower function 51']
    if fn == 52:                # the seven opponents are drawn (Black 2: a streak starts here if none is going)
        return [_tool(359) + '  // Pearl tower function 52', _tool(316), _tool(321)]
    if fn == 55:                # 0 the player's sprite, 1 the partner's, 2 the partner's id
        if arg == 0:            # (runs in a zone init too: no plugin command there)
            return [f'pl_TowerPlayerCode {v}  // Pearl tower function 55: the player\'s sprite']
        return [f'pl_TowerPartnerCode {v}  // Pearl tower function 55' if arg == 1
                else f'pl_TowerGetPartner {v}  // Pearl tower function 55']
    if fn == 56:
        return ['pl_TowerMakePartners  // Pearl tower function 56']
    if fn == 57:                # Pearl's random seed for a new challenge: Black 2 has its own
        return [f'pl_SetVarFromValue {v}, 0  // Pearl tower function 57']
    if fn == 100:
        return [f'pl_TowerIsNull {v}  // Pearl tower function 100']
    # The Wi-Fi rooms' functions (8-12, 15, 16, 54 ...): nothing reaches them, the rooms are closed
    tr.job.approx[f'CallBattleTowerFunction {fn} (Wi-Fi only: closed)'] += 1
    return [f'pl_SetVarFromValue {v}, 0  // Pearl tower function {fn}: Wi-Fi only']


def h_init(tr, vals):
    """Pearl's InitBattleTower resume, mode: 0 a new challenge in that mode, 1 the saved one."""
    resume, mode = vals
    if resume:
        return ['Plugin1_Cmd1001 1, 0  // InitBattleTower: the saved challenge', 'pl_TowerResumePartner']
    return [f'Plugin1_Cmd1001 0, {tr.var(mode)}  // InitBattleTower']


def h_battle_points(name, tr, vals):
    """Pearl's Battle Points commands: Black 2's purse (its Battle Subway score)."""
    if name == 'ShowBattlePoints':
        # (Pearl's top right is under Black 2's speech balloon and list menu: left, below the balloon)
        return [f'pl_TowerBpWindow 9, 6  // ShowBattlePoints {vals[0]}, {vals[1]}: Black 2\'s money window']
    if name == 'HideBattlePoints':
        return ['MoneyWinClose  // HideBattlePoints']
    if name == 'UpdateBPDisplay':               # (the window again: a reprint over the old number leaves its digits)
        return ['pl_TowerBpWindow 9, 6  // UpdateBPDisplay']
    if name == 'GetBattlePoints':
        return [f'pl_TowerBpGet {tr.var(vals[0])}']
    if name == 'GiveBattlePoints':
        return [f'pl_TowerBpAdd {tr.var(vals[0])}']
    if name == 'RemoveBattlePoints':
        return [f'pl_TowerBpSub {tr.var(vals[0])}']
    return [f'pl_TowerBpCheck {tr.var(vals[0])}, {tr.var(vals[1])}  // CheckBattlePoints']


def h_intro(tr, vals):
    """Pearl's PrintBattleTowerIntroMessage opponent: Black 2 prints the trainer's line (system text 376) from them."""
    objects = OPPONENT_OBJECTS[tr.job.zone['name']]
    return [_tool(352, tr.var(vals[0]), objects[vals[0]]) + '  // PrintBattleTowerIntroMessage']
