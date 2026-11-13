"""The Battle Frontier's script language (Platinum's frontier/script/fr_script.narc), read and translated (notes/PLATINUM_FRONTIER.md).

    python3 b2tools/frontier_script.py --table      rebuild b2tools/data/frontier_script_cmds.json from the decomp and summarise it
    python3 b2tools/frontier_script.py check        every file of the dump decodes fully, and agrees with the decomp's sources
    python3 b2tools/frontier_script.py show N       one file's disassembly (N: 0-10, the narc's order)
    python3 b2tools/frontier_script.py report       each command: where it is used, what the translator does with it
    python3 b2tools/frontier_script.py scene NAME   the field-script lines one scene becomes (FRONTIER_SCENE_TOWER_CORRIDOR, ...)

The language (pokeplatinum src/overlay104/frscrcmd*.c, asm/macros/frscrcmd.inc). A file starts with u32 offsets (each relative to
its own end) to the entry points, ended by u16 0xFD13. Commands are a u16 opcode (the order of include/data/scripts/frscrcmd.h)
and their arguments: u8, u16 (a var-or-value: 0x8000-0x8013 are vars) or s32 offsets relative to the end of the offset. Offsets
point at code (GoTo, GoToIf, Call, CallIf) or at data rows, each list ended by u16 0xFD13:
    FrontierScrCmd_22   objects' graphics to load: (u16 gfx, u8 ?) rows; gfx 0xEEEE the player, 0xEEEF every linked player
    FrontierScrCmd_24   objects placed: (u16 local id, u16 gfx, u8 dir, u16 x+8, u16 y+16, u8, u8 [, u8 net id if gfx 0xEEEF])
    FrontierScrCmd_2A   sprite resources: u16 ids
    FrontierScrCmd_2C   sprites placed: (u16 id, u16 x, u16 y, u16 draw, u8, u8) rows
    ApplyMovement       a movement list: (u16 code, u16 count) pairs (include/constants/battle_frontier_movements.h)
Vars: 0x8000-0x8007 the running script's, 0x8008-0x800F the scene manager's (kept over ChangeScript), 0x8010-0x8013 the
context's data (FR_VAR_0x8010..). A scene (include/constants/battle_frontier.h FRONTIER_SCENE_*) is a script file, a text bank and a
song (src/overlay104/frontier_scenes.c): LaunchBattleFrontierScene (a field command) starts one at its entry 0, ChangeScript
starts another scene's file at an entry, ChangeSceneWithinScript keeps the script running over a new scene, ExitFrontier goes
back to the field script, after its ReturnToField.

Read-only on the dump. The translation into Black 2 field scripts is translate_scene() below.
"""
import json, os, re, struct, sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom, narc_members  # noqa: E402

PLATINUM = os.path.join(ROOT, 'external', 'pokeplatinum')
DUMP = os.path.join(ROOT, 'roms', 'platinum.nds')
NARC = 'frontier/script/fr_script.narc'
TABLE_JSON = os.path.join(HERE, 'data', 'frontier_script_cmds.json')
SOURCES = os.path.join(PLATINUM, 'res', 'field', 'frontier_scripts')
END = 0xFD13
PLAYER_GFX, LINKED_GFX = 0xEEEE, 0xEEEF
# The data an offset argument points at, by command
DATA_KIND = {'FrontierScrCmd_22': 'objgfx', 'FrontierScrCmd_24': 'objects', 'FrontierScrCmd_2A': 'ids',
             'FrontierScrCmd_2C': 'sprites', 'ApplyMovement': 'movement'}
FLOW = {'End': 'end', 'ExitFrontier': 'end', 'GoTo': 'jump', 'Return': 'return', 'GoToIf': 'cjump', 'Call': 'call',
        'CallIf': 'ccall'}
SIZES = {'u8': 1, 'u16': 2, 'rel': 4}


# ---------------------------------------------------------------- the command table
def _order():
    """[(FRSCRCMD_ constant, handler)] in opcode order."""
    text = open(os.path.join(PLATINUM, 'include', 'data', 'scripts', 'frscrcmd.h')).read()
    return re.findall(r'ScriptCommand\((FRSCRCMD_\w+),\s*(\w+)\)', text)


def _macros():
    """{macro: (params, body lines)} of asm/macros/frscrcmd.inc."""
    out, cur = OrderedDict(), None
    for raw in open(os.path.join(PLATINUM, 'asm', 'macros', 'frscrcmd.inc')):
        line = raw.split('//')[0].strip()
        m = re.match(r'\.macro\s+(\w+)\s*(.*)', line)
        if m:
            params = [p.strip().split('=')[0] for p in m.group(2).split(',') if p.strip()]
            cur = (m.group(1), params, [])
            continue
        if line == '.endm' and cur:
            out[cur[0]] = (cur[1], cur[2])
            cur = None
            continue
        if cur and line:
            cur[2].append(line)
    return out


def build_table():
    """{opcode: {name, const, handler, args: [[kind, param]], flow, data}} from the decomp (the macro that writes each opcode)."""
    order = _order()
    macros = _macros()
    by_const = {}
    for name, (params, body) in macros.items():
        consts = [re.match(r'\.short\s+(FRSCRCMD_\w+)', l).group(1) for l in body
                  if re.match(r'\.short\s+FRSCRCMD_\w+', l)]
        if not consts:
            continue
        # arguments: the directives after the opcode (after an .if/.else/.endif choosing between two opcodes)
        tail = body[max(i for i, l in enumerate(body) if l.startswith('.short') and 'FRSCRCMD_' in l or l == '.endif') + 1:]
        args = []
        for l in tail:
            m = re.match(r'\.(short|byte|long)\s+\\(\w+)', l)
            assert m, (name, l)
            kind = {'short': 'u16', 'byte': 'u8', 'long': 'rel'}[m.group(1)]
            args.append([kind, m.group(2)])
        for c in consts:
            by_const.setdefault(c, (name, args))
    table = {}
    for op, (const, handler) in enumerate(order):
        name, args = by_const.get(const, (None, None))
        row = {'const': const, 'handler': handler, 'name': name or handler.replace('FrontierScrCmd_', 'FrontierScrCmd_'),
               'args': args, 'macro': name is not None}
        if name in FLOW:
            row['flow'] = FLOW[name]
        if name in DATA_KIND:
            row['data'] = DATA_KIND[name]
        table[op] = row
    return table


def load_table(rebuild=False):
    if rebuild or not os.path.exists(TABLE_JSON):
        t = build_table()
        json.dump({'_doc': 'Platinum\'s frontier script commands by opcode (b2tools/frontier_script.py --table, from pokeplatinum '
                           'include/data/scripts/frscrcmd.h and asm/macros/frscrcmd.inc). args: [kind, macro parameter]; '
                           'u16 is a var-or-value. macro false: no macro writes it (no script uses it).',
                   'commands': {str(k): v for k, v in t.items()}}, open(TABLE_JSON, 'w'), indent=1)
    return {int(k): v for k, v in json.load(open(TABLE_JSON))['commands'].items()}


def movement_names():
    text = open(os.path.join(PLATINUM, 'include', 'constants', 'battle_frontier_movements.h')).read()
    out = {}
    for name, v in re.findall(r'#define FRONTIER_MOVEMENT_(\w+)\s+(\w+)', text):
        if name in ('DELAY_OFFSET',) or not re.match(r'^(0x[0-9A-Fa-f]+|\d+)$', v):
            continue
        out.setdefault(int(v, 0), ''.join(w.capitalize() for w in name.lower().split('_')))
    return out


# ---------------------------------------------------------------- the disassembler
class Disasm:
    """One frontier script file: entries, insns {addr: (end, op, [values])}, data {addr: (kind, end, rows)}, labels."""

    def __init__(self, data, table=None):
        self.data, self.t = data, table or load_table()
        self.entries, self.insns, self.data_blocks = [], {}, {}
        self.cover = bytearray(len(data))
        self.labels = set()
        self.unexplained = []
        self._header()
        self._flow()
        self._padding()

    def u8(self, a):
        return self.data[a]

    def u16(self, a):
        return struct.unpack_from('<H', self.data, a)[0]

    def s32(self, a):
        return struct.unpack_from('<i', self.data, a)[0]

    def _mark(self, a, n):
        for i in range(a, a + n):
            self.cover[i] = 1

    def _header(self):
        a = 0
        while self.u16(a) != END:
            self.entries.append(a + 4 + self.s32(a))
            a += 4
        self._mark(0, a + 2)
        self.header_end = a + 2

    def decode(self, a):
        """(end, op, values) of the command at a; a rel value is the absolute address it points at."""
        op = self.u16(a)
        row = self.t.get(op)
        if row is None or row['args'] is None:
            raise ValueError(f'{a:#x}: opcode {op:#x} has no layout')
        p, vals = a + 2, []
        for kind, _ in row['args']:
            if kind == 'u8':
                vals.append(self.u8(p))
            elif kind == 'u16':
                vals.append(self.u16(p))
            else:
                vals.append(p + 4 + self.s32(p))
            p += SIZES[kind]
        return p, op, vals

    def _flow(self, starts=None):
        todo = list(self.entries if starts is None else starts)
        self.labels |= set(todo)
        while todo:
            a = todo.pop()
            while a not in self.insns:
                end, op, vals = self.decode(a)
                self.insns[a] = (end, op, vals)
                self._mark(a, end - a)
                row = self.t[op]
                for (kind, _), v in zip(row['args'], vals):
                    if kind != 'rel':
                        continue
                    if 'data' in row:
                        self._data(row['data'], v)
                    else:
                        self.labels.add(v)
                        todo.append(v)
                if row.get('flow') in ('end', 'jump', 'return'):
                    break
                a = end

    def _data(self, kind, a):
        if a in self.data_blocks:
            return
        p, rows = a, []
        while True:
            first = self.u16(p)
            if first == END:
                p += 2
                break
            if kind == 'movement':
                rows.append((first, self.u16(p + 2)))
                p += 4
            elif kind == 'objgfx':
                rows.append((first, self.u8(p + 2)))
                p += 3
            elif kind == 'ids':
                rows.append((first,))
                p += 2
            elif kind == 'sprites':
                rows.append(struct.unpack_from('<4H2B', self.data, p))
                p += 10
            elif kind == 'objects':
                local, gfx, d = struct.unpack_from('<HHB', self.data, p)
                x, y, b, c = struct.unpack_from('<HHBB', self.data, p + 5)
                p += 11
                net = None
                if gfx == LINKED_GFX:
                    net = self.u8(p)
                    p += 1
                rows.append((local, gfx, d, x, y, b, c, net))
            else:
                raise ValueError(kind)
        self.data_blocks[a] = (kind, p, rows)
        self._mark(a, p - a)

    def gaps(self):
        out, a = [], 0
        while a < len(self.data):
            if self.cover[a]:
                a += 1
                continue
            b = a
            while b < len(self.data) and not self.cover[b]:
                b += 1
            out.append((a, b))
            a = b
        return out

    def _padding(self):
        """Bytes no flow reached. Code right after a command (the End the compiler put after a GoTo, scripts nothing jumps
        to) is decoded with its own flow and kept as unreferenced, with the data it points at; zero runs that align a data
        list (.balign 4) or end the file are padding; anything else is unexplained."""
        self.unreferenced = set()
        reached = set(self.insns)
        while True:
            ends = {e for e, op, v in self.insns.values()}
            starts = [a for a, b in self.gaps() if a in ends and any(self.data[a:b])]
            if not starts:
                break
            before = set(self.insns)
            for a in starts:
                try:
                    self._flow([a])
                except (ValueError, struct.error, KeyError, IndexError):
                    pass
            self.unreferenced |= set(self.insns) - before
            if set(self.insns) == before:
                break
        self.unreferenced -= reached
        self.unreferenced_data = set()
        for a, b in self.gaps():
            if any(self.data[a:b]):
                # a data list no command points at (the Hall's and the Arcade's spare object lists): it must parse as a
                # list that ends where the gap's zeros start
                p = (a + 3) & ~3
                last = b
                while last > p and self.data[last - 1] == 0:
                    last -= 1
                for kind in ('objgfx', 'objects', 'sprites', 'movement', 'ids'):
                    try:
                        self._data(kind, p)
                    except (struct.error, IndexError, ValueError):
                        continue
                    if self.data_blocks[p][1] in (last, last + 1):
                        self.unreferenced_data.add(p)
                        break
                    del self.data_blocks[p]
                    for i in range(p, b):
                        self.cover[i] = 0
            if any(self.data[i] for i in range(a, b) if not self.cover[i]):
                self.unexplained.append((a, b))
            else:
                self._mark(a, b - a)

    def covered(self):
        return all(self.cover)

    def name(self, op):
        return self.t[op]['name']

    def text(self):
        out, mv = [], movement_names()
        items = sorted([(a, 'i') for a in self.insns] + [(a, 'd') for a in self.data_blocks])
        for k, e in enumerate(self.entries):
            out.append(f'    ScriptEntry _{e:04X}  // entry {k}')
        for a, what in items:
            if what == 'd':
                kind, end, rows = self.data_blocks[a]
                out.append(f'_{a:04X}:  // {kind}')
                for r in rows:
                    if kind == 'movement':
                        out.append(f'    {mv.get(r[0], r[0])} {r[1]}')
                    else:
                        out.append('    ' + ', '.join(f'{v:#x}' if isinstance(v, int) else str(v) for v in r))
                continue
            end, op, vals = self.insns[a]
            row = self.t[op]
            if a in self.labels:
                out.append(f'_{a:04X}:')
            args = ', '.join(f'_{v:04X}' if k == 'rel' else (f'{v:#x}' if v >= 0x8000 else str(v))
                             for (k, _), v in zip(row['args'], vals))
            note = '  // unreferenced' if a in getattr(self, 'unreferenced', ()) else ''
            out.append(f'    {row["name"]} {args}'.rstrip() + note)
        return '\n'.join(out)


_ROM = None


def files():
    """The dump's frontier script files, in the narc's order."""
    global _ROM
    if _ROM is None:
        _ROM = Rom(DUMP)
    return narc_members(_ROM.read(NARC))


def source_order():
    """The decomp's file names in the narc's order (res/field/frontier_scripts/fr_script.order)."""
    return [l.strip() for l in open(os.path.join(SOURCES, 'fr_script.order')) if l.strip()]


# ---------------------------------------------------------------- the check against the decomp's sources
_COMPOSITE = {'FadeScreenOut': ['FadeScreen', 'WaitFadeScreen'], 'FadeScreenIn': ['FadeScreen', 'WaitFadeScreen']}


def _composites():
    """{macro: [primitive macro names]} for macros made of other macros (GoToIfEq = CompareVar + GoToIf, ...)."""
    macros = _macros()
    out = {}
    for name, (params, body) in macros.items():
        if any(l.startswith('.short') or l.startswith('.byte') or l.startswith('.long') or l.startswith('.if')
               for l in body):
            continue
        out[name] = [l.split()[0] for l in body]
    return out


def source_listing(name):
    """[(label or None, macro, [args as text])] of a decomp source file, composite macros expanded, data directives kept
    as ('.short', value) rows."""
    comp = _composites()
    out = []
    for raw in open(os.path.join(SOURCES, name + '.s')):
        line = raw.split('//')[0].rstrip()
        if not line.strip() or line.strip().startswith('#') or line.strip().startswith('.data') or \
                line.strip().startswith('.balign') or line.strip().startswith('ScriptEntry'):
            continue
        m = re.match(r'^(\w+):\s*$', line)
        if m:
            out.append((m.group(1), None, []))
            continue
        parts = line.strip().split(None, 1)
        mac, args = parts[0], [a.strip() for a in parts[1].split(',')] if len(parts) > 1 else []
        stack = [mac]
        names = []
        while stack:
            n = stack.pop(0)
            if n in comp:
                stack = comp[n] + stack
            else:
                names.append(n)
        for n in names:
            out.append((None, n, args if len(names) == 1 else []))
    return out


def check(verbose=False):
    """Every file decodes fully; each decomp label _XXXX is at its address; the commands match the decomp's, in order."""
    t = load_table()
    names = source_order()
    mv = movement_names()
    problems, n_cmds = [], 0
    for i, data in enumerate(files()):
        name = names[i]
        if name.endswith('.bin'):
            # the two unused files are shipped as binaries in the decomp: compare bytes
            src = open(os.path.join(SOURCES, name), 'rb').read()
            if src != data:
                problems.append(f'{name}: bytes differ from the dump')
            continue
        d = Disasm(data, t)
        if not d.covered() or d.unexplained:
            problems.append(f'{name}: {sum(1 for c in d.cover if not c)} bytes not decoded {d.unexplained[:3]}')
        listing = source_listing(name)
        # the decomp's commands in source order, and its _XXXX labels
        src_cmds, labels = [], {}
        pending = []
        mvn = set(mv.values()) | {'EndMovement'}
        for label, mac, args in listing:
            if label:
                pending.append(label)
                continue
            if mac.startswith('.') or mac in mvn:
                pending = []                      # (a data list's label)
                continue
            src_cmds.append((mac, args, pending))
            pending = []
        mine = []
        for a in sorted(d.insns):
            end, op, vals = d.insns[a]
            mine.append((a, d.name(op), vals))
        if len(src_cmds) != len(mine):
            problems.append(f'{name}: {len(src_cmds)} commands in the source, {len(mine)} decoded')
        for (mac, args, labs), (a, nm, vals) in zip(src_cmds, mine):
            n_cmds += 1
            if mac != nm:
                problems.append(f'{name}: {a:#06x} decoded {nm}, source {mac}')
                break
            for lab in labs:
                if re.match(r'^_[0-9A-F]{4}$', lab) and int(lab[1:], 16) != a:
                    problems.append(f'{name}: label {lab} is at {a:#06x}')
        if verbose:
            print(f'{name}: {len(data)} bytes, {len(d.entries)} entries, {len(d.insns)} commands, '
                  f'{len(d.data_blocks)} data lists, decoded {"fully" if d.covered() and not d.unexplained else "NOT fully"}')
    return problems, n_cmds


def usage():
    """{command name: Counter(file name: uses)} over the dump's files."""
    t = load_table()
    names = source_order()
    out = {}
    for i, data in enumerate(files()):
        if names[i].endswith('.bin'):
            continue
        d = Disasm(data, t)
        for a, (end, op, vals) in d.insns.items():
            if a in getattr(d, 'unreferenced', ()):
                continue
            out.setdefault(d.name(op), Counter())[names[i]] += 1
    return out


def main(argv):
    if argv and argv[0] == '--table':
        t = load_table(rebuild=True)
        used = sum(1 for r in t.values() if r['macro'])
        print(f'{TABLE_JSON}: {len(t)} commands, {used} with a macro (a layout)')
        return 0
    if argv and argv[0] == 'check':
        problems, n = check(verbose=True)
        for p in problems:
            print('PROBLEM', p)
        print(f'{n} commands compared with the decomp\'s sources: {len(problems)} problems')
        return 1 if problems else 0
    if argv and argv[0] == 'show':
        print(Disasm(files()[int(argv[1])]).text())
        return 0
    if argv and argv[0] == 'report':
        import frontier_translate
        return frontier_translate.report()
    if argv and argv[0] == 'scene':
        import frontier_translate
        print('\n'.join(frontier_translate.scene_lines(argv[1])))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
