"""Check an assembled Black 2 field-script file offline (no ROM, no emulator).

    python3 b2_script_check.py FILE.bin [--level SCRIPT:LEVEL ...]

- Decodes every script entry with Black 2's command table (pokebw2 tools/script/field_commands.json: the arguments of
  each command, from its handler) following jumps and calls: every opcode must exist and every jump/call target must
  be inside the file (an error otherwise).
- --level S:L: script S runs at feature level L (a zone's map scripts: zone init = 2, field load/return = 1; ov012
  script_sys.c FieldScript_CallZoneInitCore; every other script at level 0). Every command reachable from a script
  must be allowed at its level by
  EVCMD_PERM_TABLE (ov012 script_sys.c; a forbidden command hangs the game: FieldScript_ThrowOpcodeAccessError,
  HoennB2 notes/STORY_COMMON.md "Map-script permissions").
Used by b2tools/patches/sinnoh_story.py for every zone it installs, and importable: check(data, levels).
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECOMP = os.path.join(HERE, '..', 'external', 'pokebw2')
SIZES = {'u8': 1, 'u16': 2, 'any': 2, 'var': 2, 'u32': 4}
JUMPS = {30: 'jump', 31: 'cjump', 4: 'call', 32: 'ccall'}     # VMJump, VMJumpIf, VMCall, VMCallIf: u32 relative
# PearlB2's extension command (notes/EXT_COMMAND.md): command 0x15F, a sub-command byte, then the sub-command's own
# arguments (bytes after the sub-command byte; each module adds its rows)
EXT_CMD = 0x15F
# ---- plat-frontier: the Battle Frontier's sub-command (the Tower's row, EXT_TOWER_FRONTIER): one op byte, then the op's
# argument bytes (decomp include/pearlb2/plat_frontier.h; the facility pieces add theirs from 0x20)
FRONTIER_SUB = 0x93
FRONTIER_OPS = {0x00: 2, 0x01: 2, 0x02: 4, 0x03: 4, 0x04: 4, 0x05: 4, 0x06: 8, 0x07: 6}
FRONTIER_OPS[0x08] = 2        # (plat-fix2) the Tower's disqualification after a reset without saving, var
FRONTIER_OPS.update({0x4F: 4, 0x50: 8})   # (plat-fix2) the Hall's records machine: its species list, a species' record
# (plat-hall) the Battle Hall's ops 0x40-0x4e (decomp include/pearlb2/plat_hall.h PLATHALL_OP_*; pearl_story.inc "plat-hall")
FRONTIER_OPS.update({0x40: 8, 0x41: 8, 0x42: 0, 0x43: 0, 0x44: 0, 0x45: 0, 0x46: 2, 0x47: 2, 0x48: 4, 0x49: 2, 0x4A: 4,
                     0x4B: 6, 0x4C: 2, 0x4D: 6, 0x4E: 4})
# (plat-test, 2026-11-08) 0x48, 0x69, 0x89: the Trainer's intro in a balloon (slot, person), no longer a word (word, slot, line)
# ---- end plat-frontier
# ---- plat-factory: the Battle Factory's ops 0x20-0x30 (decomp include/pearlb2/plat_factory.h PLATFACTORY_OP_*, pearl_story.inc
# block "plat-factory"): init, round, function, rent screen and result, swap screen and result, add, next opponent, trade,
# next party, battle, cleanup, won, the Trainer's line, free, the lobby's streak deletion
FRONTIER_OPS.update({0x20: 6, 0x21: 2, 0x22: 8, 0x23: 0, 0x24: 2, 0x25: 2, 0x26: 2, 0x27: 0, 0x28: 0, 0x29: 0, 0x2A: 0,
                     0x2B: 0, 0x2C: 0, 0x2D: 2, 0x2E: 4, 0x2F: 0, 0x30: 4})
# ---- end plat-factory
# ---- plat-castle: the Battle Castle's ops 0x60-0x79 (decomp include/pearlb2/plat_castle.h PLATCASTLE_OP_*, pearl_story.inc
# block "plat-castle"): init, round, function, free, first and next opponent, battle, cleanup, won, the Trainer's line, the CP
# (get, spend, receive), the lobby, the streak's deletion, the self screen and its pick, ask, buy, the rental list, the
# opponent list, a Pokémon's words, the screens' information, the CP's word, the lobby's party screen and its slots
FRONTIER_OPS.update({0x60: 10, 0x61: 2, 0x62: 8, 0x63: 0, 0x64: 0, 0x65: 0, 0x66: 0, 0x67: 0, 0x68: 2, 0x69: 4, 0x6A: 4,
                     0x6B: 4, 0x6C: 4, 0x6D: 6, 0x6E: 2, 0x6F: 0, 0x70: 2, 0x71: 8, 0x72: 8, 0x73: 2, 0x74: 2, 0x75: 6,
                     0x76: 6, 0x77: 2, 0x78: 2, 0x79: 6})
# ---- end plat-castle
# ---- plat-arcade: the Battle Arcade's ops 0x80-0x8F (decomp include/pearlb2/plat_arcade.h PLATARCADE_OP_*, pearl_story.inc
# block "plat-arcade"): init, round, function, free, first and next opponent, battle, cleanup, won, the Trainer's line, the
# board's effect, the board, the lobby's function, the streak's deletion, the lobby's party screen and its slots
FRONTIER_OPS.update({0x80: 10, 0x81: 2, 0x82: 8, 0x83: 0, 0x84: 0, 0x85: 0, 0x86: 0, 0x87: 0, 0x88: 2, 0x89: 4, 0x8A: 0,
                     0x8B: 2, 0x8C: 6, 0x8D: 2, 0x8E: 2, 0x8F: 6})
# ---- end plat-arcade
EXT_ARGS = {
    0x00: 0, 0x01: 2, 0x02: 2, 0x03: 4, 0x04: 0, 0x05: 0,   # the Pokétch (src/pearlb2/poketch_itcm.c)
    0x20: 0, 0x21: 6, 0x22: 2, 0x23: 0, 0x24: 0,   # (plat-dw-world) the Distortion World (resident/plat_dw_hooks.c, overlay 377)
    0x25: 2,                                       # (plat-dw-rom) pl_PlatSound n: one of Platinum's own sounds
    0x40: 3, 0x41: 2, 0x42: 2, 0x43: 2, 0x44: 0, 0x45: 4,   # Pal Park (src/pearlb2/resident/palpark.c)
    0x60: 2, 0x61: 0, 0x62: 4, 0x63: 0, 0x64: 0, 0x65: 4, 0x66: 5, 0x67: 4, 0x68: 4, 0x69: 2, 0x6a: 2, 0x6b: 3, 0x6c: 1, 0x6d: 2,   # honey trees, swarms, berries (resident/wild.c, berry.c)
    0x80: 2, 0x81: 2, 0x82: 2, 0x83: 4, 0x84: 4, 0x85: 0, 0x86: 4, 0x87: 2, 0x88: 0, 0x89: 8, 0x8a: 2, 0x8b: 2, 0x8c: 2, 0x8d: 0, 0x8e: 8, 0x8f: 2, 0x90: 4,   # the Battle Tower (resident/tower.c)
    0x91: 2, 0x92: 6,                 # (v101-story) the Tower's longest streak, var; a trophy given, op, trophy, var (resident/tower.c)
    0xa0: 2, 0xa1: 4, 0xa2: 2, 0xa3: 6, 0xa4: 2, 0xa5: 2, 0xa6: 4,   # the smaller finishes (resident/leftovers.c, vs_seeker.c)
    0xa7: 4, 0xa8: 2,                 # (plat-trades) Gen 4's StartNPCTrade, trade, slot; ActivateRoamingPokemon, slot (resident/npc_trade.c, roamers.c)
    0xa9: 4,                          # (postdex) the deliveryman's event Pokémon, index, var (resident/leftovers.c, patches/event_gifts.py)
    0xbf: 2,                          # Platinum's deliveryman's event Regigigas, var (patches/platinum_regigigas.py)
    0xb0: 6, 0xb1: 6, 0xb2: 6, 0xb3: 6, 0xb4: 4, 0xb5: 2, 0xb6: 4,   # (plat-tutors) Platinum's party commands (decomp src/pearlb2/plat_party/, overlay 376)
    0xbd: 2, 0xbe: 4,                 # (plat-ch12) Platinum's Rotom forms in the save, var; a fateful wild battle, species, level (patches/platinum_postgame.py)
    0xc0: 8, 0xc1: 10, 0xc2: 8, 0xc3: 4, 0xc4: 6, 0xc5: 2, 0xc6: 4, 0xc7: 2, 0xc8: 6, 0xc9: 2, 0xca: 3, 0xcb: 4, 0xcc: 3,   # Super Contests (resident/contest.c)
    0xd8: 2, 0xd9: 2, 0xda: 2, 0xdb: 6, 0xdc: 14, 0xdd: 2,   # Poffins (resident/poffin.c)
    **{sub: 2 for sub in range(0xe0, 0x100)},   # Secret Bases (resident/secret_base.c): one value-or-var each
}
_CMDS = _PERM = None


def commands():
    global _CMDS
    if _CMDS is None:
        _CMDS = {int(k): v for k, v in json.load(open(os.path.join(DECOMP, 'tools', 'script',
                                                                   'field_commands.json')))['commands'].items()}
        # the overlay plugins' commands (1000+: the Battle Subway's, for the Battle Tower) are only in the macros
        inc = open(os.path.join(DECOMP, 'include', 'asm', 'field_script.inc')).read()
        for m in re.finditer(r'\.macro\s+(\S+)[^\n]*\n\s*FieldCommand (\d+)\n(.*?)\.endm', inc, re.S):
            # the numbers are per plugin, so 1003 means ten things: PearlB2's scripts use only the Battle Subway's
            if m.group(1) in ('Plugin1_Cmd1000', 'Plugin1_Cmd1001', 'Plugin1_Cmd1002', 'BSubwayCmd_Tool'):
                kinds = {'.byte': 'u8', '.2byte': 'u16', '.4byte': 'u32', '.word': 'u32'}
                args = [kinds[l.split()[0]] for l in m.group(3).split('\n') if l.split() and l.split()[0] in kinds]
                _CMDS[int(m.group(2))] = {'handler': m.group(1), 'overlay': None, 'args': args}
    return _CMDS


def permissions():
    """[(level0, level1, level2)] per command, from EVCMD_PERM_TABLE."""
    global _PERM
    if _PERM is None:
        src = open(os.path.join(DECOMP, 'src', 'ov012', 'script_sys.c')).read()
        body = src[src.index('EVCMD_PERM_TABLE[] = {'):]
        body = body[:body.index('};')]
        # PearlB2's entries (#if PEARLB2 ... #else <Black 2's> #endif): the PearlB2 side, as the build compiles it
        body = re.sub(r'#else\b.*?#endif', '', body, flags=re.S)
        body = re.sub(r'#(?:if|endif)\b[^\n]*', '', body)
        _PERM = [tuple(map(int, m)) for m in re.findall(r'\{ (\d), (\d), (\d) \}', body)]
    return _PERM


def entries(data):
    out, p = [], 0
    while struct.unpack_from('<H', data, p)[0] != 0xFD13:
        off, = struct.unpack_from('<i', data, p)
        out.append(p + 4 + off)
        p += 4
    return out


def walk(data, start):
    """{address: opcode} reachable from start; raises ValueError on a bad opcode or target."""
    cmds, seen, todo = commands(), {}, [start]
    while todo:
        a = todo.pop()
        while a not in seen:
            if not 0 <= a < len(data) - 1:
                raise ValueError(f'code at {a:#x} outside the file')
            op, = struct.unpack_from('<H', data, a)
            c = cmds.get(op)
            if c is None:
                raise ValueError(f'unknown opcode {op} at {a:#x}')
            seen[a] = op
            p = a + 2
            for ty in c['args']:
                p += SIZES[ty]
            if op == EXT_CMD:
                sub = data[p]
                if sub == FRONTIER_SUB:       # (plat-frontier) the Frontier's op byte, then the op's arguments
                    fop = data[p + 1]
                    if fop not in FRONTIER_OPS:
                        raise ValueError(f'unknown Battle Frontier op {fop:#x} at {a:#x}')
                    p += 2 + FRONTIER_OPS[fop]
                    sub = None
                elif sub not in EXT_ARGS:
                    raise ValueError(f'unknown PearlB2 extension sub-command {sub:#x} at {a:#x}')
                if sub is not None:
                    p += 1 + EXT_ARGS[sub]
            if op in JUMPS:
                off, = struct.unpack_from('<i', data, p - 4)
                t = p + off
                if not 0 <= t < len(data):
                    raise ValueError(f'{c["handler"]} at {a:#x} jumps outside the file ({t:#x})')
                todo.append(t)
                if JUMPS[op] == 'jump':
                    break
            if set(c.get('flow', [])) & {'end', 'return'}:
                break
            a = p
    return seen


MSG_ARGS = {52: [0], 53: [0], 60: [1], 61: [1], 67: [0], 72: [1, 2], 175: [0]}   # SystemMsg(Async), ActorMsg,
# ParentActorMsg, MsgPlaceSign, ActorMsgGendered, ListMenuAdd: which arguments are a line of the script's text file


def message_lines(data):
    """{line number} of the script's own text file that the reachable code shows (constant ids only; ActorMsg with a
    file other than the script's own, MSGFILE_SCRIPT 0x400, is skipped)."""
    cmds, out = commands(), set()
    for start in entries(data):
        for a, op in walk(data, start).items():
            if op not in MSG_ARGS:
                continue
            p, vals = a + 2, []
            for ty in cmds[op]['args']:
                n = SIZES[ty]
                vals.append(int.from_bytes(data[p:p + n], 'little'))
                p += n
            if op in (60, 61, 72) and vals[0] != 0x400:
                continue
            out |= {vals[i] for i in MSG_ARGS[op] if vals[i] < 0x4000}
    return out


def check(data, levels=None):
    """List of problems (empty = fine). levels: {1-based script number: feature level}."""
    problems, perm, cmds = [], permissions(), commands()
    ents = entries(data)
    for k, start in enumerate(ents, 1):
        try:
            seen = walk(data, start)
        except ValueError as e:
            problems.append(f'script {k}: {e}')
            continue
        lv = (levels or {}).get(k, 0)              # a script started by a person, sign, trigger or warp: level 0
        if True:
            bad = sorted({cmds[op]['handler'] for op in seen.values() if op < len(perm) and not perm[op][lv]})
            if bad:
                problems.append(f'script {k} runs at level {lv} but uses {", ".join(bad)} (not allowed there: hangs)')
    return problems


def main(argv):
    data = open(argv[0], 'rb').read()
    levels = {}
    for a in argv[1:]:
        if a != '--level':
            s, l = a.split(':')
            levels[int(s)] = int(l)
    probs = check(data, levels)
    print('\n'.join(probs) or f'{argv[0]}: {len(entries(data))} scripts decode cleanly')
    return 1 if probs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
