"""Story-flow comparison of a Platinum chapter, offline (2026-11-07, plat-ch1; work/agents/PLATINUM_CHAPTER_BRIEF.md "Prove it offline").
Written beside plat-ch2's b2tools/platinum_flow_check.py (one path through the generated files, from a chapter's test start, with its
start-tile and assembly checks): this one plays both Platinum's own scripts and the generated files, every way, and compares them.

    PEARL_VERSION=platinum python3 b2tools/platinum_flow_compare.py CHAPTER ... | all [-v]
        CHAPTER: data/platinum/beats/<CHAPTER>.json, or else that chapter's row of data/platinum/story_flow.json (plat-ch2's
        platinum_flow_check beats, converted: load_beats); all: every chapter either file has; -v prints every beat's changes
    Run after the chapters' zones are generated (pearl_story.py chapter N, or all): it reads work/platinum/src/field_scripts.

The chapter's beats are played in order from its start, twice: once as Platinum plays them (its scripts from the dump) and once as the
Black 2 build will (the generated files, work/platinum/src/field_scripts, their pl_ macros as Platinum's commands and their raw Black 2
commands). For every beat it checks that
- its trigger holds when the beat comes: a step trigger's var has its value; a frame-table script is the first row whose var matches
  (Black 2's condition table checks the same rows in the same order); a person talked to is there (its hide flag clear); "not": the
  trigger is off (a way that must be open);
- what the beat leaves (the saved flags and vars, the zone, the Trainers battled by Platinum's number) is the same on both sides, its
  "expect" values hold, and no frame-table script of the zone it ends in would run before the next beat;
and at the end, that the state matches the next chapter's test start ("next_start", over the new game's own flags), so nothing the
next chapter needs is left unset.

Each side keeps every end state its paths reach: a branch on something not known offline follows every way. Results with a known set of
values fork there (DOMAINS: a YES/NO, the gender, the starter, a battle won or lost, the weekday, an item's pocket; items always fit;
Black 2's card stars are 0, as the translation has them); a step trigger runs once per tile of it, and a path that changes nothing
saved, when another does, is dropped (a tile no case takes, a NO: the player goes on). Zone changes clear the map-local flags (1-0x3F)
and vars (0x4000-0x401F) and run the new zone's on-transition and on-load scripts (Platinum's level types 2 and 4: Black 2's zone init
and field load). A Platinum Warp goes on in the new zone; a generated pl_Warp ends its script and the reserved script (RTReserveScript
n: the continuation) runs there. A dynamic sprite var holds the Black 2 code on both sides (pearl_events.sprite_code).

The beats file ({"_doc", "start", "beats", "next_start"}):
- start: "newgame" (Platinum's new-game script 9600, then the start room PEARL_START) or a TEST_SET string ("PVAR_40F9=1,PFLAG_0173,..."),
  set over the new-game script's state as test_story_start does, with "start_zone": a Pearl map name (and "start_clear": flags
  TEST_LINES resets);
- beats: [{"zone": "MAP_...", "script": "<Platinum's label less its zone prefix>" or a global script id (10401), "note": "...",
  "not": true (the trigger must be off), "optional": true (runs only where its trigger holds; a problem only if nowhere),
  "fresh": true (from the start state, not after the beat before), "arrive": true (enter the zone again first; with no script: only
  that), "expect": {decomp name: value} (FLAG_X: true/false, VAR_X: a number, in every end state)}];
- next_start: the next chapter's TEST_SET (notes/PLATINUM_CHAPTERS.md).
A story_flow.json row (plat-starts, 2026-11-07) plays as platinum_flow_check plays it: every battle won and the saved states carried
(its "compare" options, or won_only and carry "saved" when it has none), a beat's PVAR_ "set" answers its menu or check, a warp beat
is the arrival in its zone, and the next start is compared with the chapter's own end (before the later chapters' beats its row runs)
in the end state nearest it. What the starts leave out on purpose (side gifts' flags, the day's flags) is a note there, not a problem.
Exit 1 on a problem.
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402
import pearl_story, pearl_events, pearl_ids  # noqa: E402

BEATS = os.path.join(ROOT, 'data', 'platinum', 'beats')
DECOMP_SCRIPTS = os.path.join(ROOT, 'external', 'pokeplatinum', 'res', 'field', 'scripts')
PATHS, STEPS, STATES = 400, 6000, 48
B2_FLAG = 0x10000                      # Black 2's own flags (a raw number in a generated file), apart from Platinum's
TRAINER_TAG = 0x200000                 # PTRAINER_n in a generated file: Platinum's trainer n
NATDEX_FLAG = 0x3FFE                    # (plat-ch11) the National Pokédex, as a flag of this tool's (Platinum's flags end before it)
LOCAL_FLAGS, LOCAL_VARS = range(1, 0x40), range(0x4000, 0x4020)
CMP = {'CMP_LT': 0, 'CMP_EQ': 1, 'CMP_GT': 2, 'CMP_LE': 3, 'CMP_GE': 4, 'CMP_NE': 5}
DYNAMIC = range(0x4020, 0x4030)        # dynamic sprite vars: Black 2 reads an object code there (Platinum: a graphics id)
PLATES = range(298, 314)                # Platinum's Flame Plate .. Iron Plate (CheckItemIsPlate)
# results known to be one of a few values: each path takes one (so a chain of GoToIfEq always finds its case)
# ({command: (the result's argument, its values)}; CanFitItem: the story's items always fit)
DOMAINS = {'ShowYesNoMenu': (0, [0, 1]), 'GetPlayerGender': (0, [0, 1]), 'CheckWonBattle': (0, [1, 0]), 'CheckWonFirstBattle': (0, [1, 0]),
           'GetPlayerStarterSpecies': (0, [387, 390, 393]), 'GetPlayerDir': (0, [0, 1, 2, 3]),
           'GetTimeOfDay': (0, [0, 1, 2, 3, 4]), 'CanFitItem': (2, [1]), 'GetItemPocket': (1, list(range(8))),
           'GetDayOfWeek': (0, list(range(7))), 'RTCGetWeekDay': (0, list(range(7))),
           'GetTrainerCardLevel': (0, [0]),      # (Black 2 has no card stars: the translation's 0, an approximation in the report)
           'CheckPlayerOnBike': (0, [0, 1]), 'PlayerGetExState': (0, [0, 1])}    # (plat-starts: on the Bicycle or not, both
#            sides: the Cycling Road gates; Black 2's ex state 1 is cycling, the generated code makes any other 0)
LUT = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (0, 1, 1), (1, 0, 1)]     # Gen 4's and Black 2's conditions 0-5 by result
# commands that only read, show or move (not flags or vars): no effect here
QUIET = re.compile(r'^(msg_|Message|Buffer|ApplyMovement|WaitMovement|Play|Wait|Close|Fade|Lock|Release|FacePlayer|follow_|'
                   r'SetObjectEvent|SetPosition|SetMovementType|SetObjectFlag|SetHasPartner|ClearHasPartner|Ev[A-Z]|Actor|'
                   r'MsgWin|FinishAllEvents|SE|BGM|Stop|sign|stub|PearlArrive|Load|Unload|Shake|Show(?!YesNo)|Hide|Cry)')


def decomp_entries(zone):
    """{label less the zone prefix: 1-based entry} of the zone's Platinum script file (its decomp source, by the zone's pl_name)."""
    path = os.path.join(DECOMP_SCRIPTS, f'scripts_{zone["pl_name"][4:].lower()}.s')
    out, k = {}, 0
    for line in open(path):
        m = re.match(r'\s*ScriptEntry (\w+)', line)
        if m:
            k += 1
            out[m.group(1).split('_', 1)[1]] = k
    return out


class Names:
    def __init__(self):
        self.by_num = pearl_ids.decomp_names()
        self.by_name = {v: k for k, v in self.by_num.items()}

    def show(self, n):
        return f'{self.by_num.get(n, "?")} ({n:#x})'


def parse_set(s):
    """TEST_SET -> ({flag: True}, {var: value}) in Platinum's numbers (PFLAG_xxxx / PVAR_xxxx; Black 2's own numbers are left out)."""
    flags, vars_ = {}, {}
    same = {b2: f for f, b2 in pearl_ids.SYSTEM_SAME.items()}      # (plat-ch11: Black 2's game clear and town arrivals that are
    for part in [p.strip() for p in (s or '').split(',') if p.strip()]:     # Platinum's own flags: 2400, 2478, 2480, 2485)
        if part.isdigit() and int(part) in same:
            flags[same[int(part)]] = True
            continue
        m = re.fullmatch(r'P(FLAG|VAR)_([0-9A-F]{4})(?:=(\d+))?', part)
        if not m:
            continue
        if m.group(1) == 'FLAG':
            flags[int(m.group(2), 16)] = True
        else:
            vars_[int(m.group(2), 16)] = int(m.group(3) or 0)
    return flags, vars_


# ---------------------------------------------------------------- the two programs

class PlatProg:
    """Platinum's own script file (from the dump), by address."""

    def __init__(self, pd, f):
        self.pd, self.f, self.d = pd, f, pd.disasm(f)
        self.key = ('plat', f)

    def entry(self, k):
        return self.d.entries[k - 1] if 1 <= k <= len(self.d.entries) else None

    def insn(self, a):
        if a not in self.d.insns:
            return None
        end, op, args = self.d.insns[a]
        name = self.pd.cmd_name(op)
        vals = [v for t, v in args]
        tgt = next((v for t, v in args if t == 'rel'), None)
        if name in ('GoToIf', 'CallIf'):
            vals = vals[:1]
        if name == 'Warp':
            vals = [vals[0], vals[2], vals[3], vals[4]]
        if name == 'PlayBoatCutscene':          # (plat-ch7) a boat (Eldritch's, the Snowpoint ship) ends at its map: a Warp there
            name, vals = 'Warp', [vals[2], vals[3], vals[4], vals[1]]
        return name, vals, end, tgt


class B2Prog:
    """The generated Black 2 file of a zone (its pl_ macros and raw commands), by line."""

    def __init__(self, pd, zone, path=None):
        self.path = path                        # (plat-ch5: a global file by its path, the item balls; else the zone's)
        if path is None:
            num = pd.script_file(zone)
            for d in (pearl_story.SRC_SCRIPTS, os.path.join(ROOT, 'src', 'field_scripts')):
                if os.path.isdir(d):
                    self.path = self.path or next((os.path.join(d, n) for n in sorted(os.listdir(d)) if n.startswith(f'{num:04d}_pearl_')), None)
        self.key = ('b2', zone['id']) if zone is not None else ('b2', 'balls')
        self.code, self.labels, self.entries = [], {}, []
        if self.path is None:
            return
        in_mov = False
        for raw in open(self.path):
            ln = raw.split('//', 1)[0].strip()
            if not ln or ln.startswith(('.balign', '#', '.byte', '.2byte', '.4byte')):
                continue
            m = re.match(r'^([A-Za-z_.][\w.]*):$', ln)
            if m:
                self.labels[m.group(1)] = len(self.code)
                continue
            parts = ln.split(None, 1)
            mac, args = parts[0], [a.strip() for a in parts[1].split(',')] if len(parts) > 1 else []
            if mac == 'ScriptEntry':
                self.entries.append(args[0])
            elif mac not in ('Move', 'MoveEnd', 'ScriptEntriesEnd'):
                self.code.append((mac, args))

    def entry(self, k):
        return self.labels.get(self.entries[k - 1]) if 1 <= k <= len(self.entries) else None

    @staticmethod
    def value(tok):
        tok = tok.strip()
        m = re.fullmatch(r'P(VAR|FLAG)_([0-9A-Fa-f]{4})', tok)
        if m:
            return int(m.group(2), 16)
        m = re.fullmatch(r'PTRAINER_(\d+)', tok)
        if m:
            return TRAINER_TAG + int(m.group(1))    # (Platinum's trainer n; a bare number in a battle is a Black 2 id)
        if tok in CMP:
            return CMP[tok]
        try:
            return int(tok, 0)
        except ValueError:
            return ('?', tok)                   # a name the check doesn't know (PTRAINER_n, PL_PLAYER, a Black 2 constant)

    def insn(self, i):
        if not 0 <= i < len(self.code):
            return None
        mac, args = self.code[i]
        name = mac[3:] if mac.startswith('pl_') else mac
        vals = [self.value(a) for a in args]
        tgt = None
        if name in ('GoTo', 'Call', 'VMJump', 'VMCall'):
            tgt = self.labels.get(args[0])
            name = {'VMJump': 'GoTo', 'VMCall': 'Call'}.get(name, name)
        elif name in ('GoToIf', 'CallIf', 'VMJumpIf', 'VMCallIf'):
            tgt = self.labels.get(args[1])
            name = {'VMJumpIf': 'GoToIf', 'VMCallIf': 'CallIf'}.get(name, name)
            vals = vals[:1]
        elif name == 'VMReturn':
            name = 'Return'
        elif name == 'VMHalt':
            name = 'End'
        elif name == 'FlagSet':
            name = 'SetFlag'
        elif name == 'FlagReset':
            name = 'ClearFlag'
        elif name == 'WorkSetConst':
            name = 'SetVarFromValue'
        elif name == 'WorkSet':
            name = 'SetVarFromVar'
        elif name == 'WorkCmpConst':
            name = 'CompareVarToValue'
        elif name == 'FlagGet':                 # FlagGet flag, var
            name = 'FlagGetVar'
        if name in ('SetFlag', 'ClearFlag', 'CheckFlag', 'FlagGetVar') and args and not args[0].startswith('PFLAG_'):
            vals[0] = B2_FLAG + vals[0] if isinstance(vals[0], int) else vals[0]   # Black 2's own flag (2402, 2403, ...)
            if vals[0] == B2_FLAG + 2400:       # (plat-ch11) Black 2's game clear is Platinum's FLAG_GAME_COMPLETED (pearl_ids
                vals[0] = 0x964                 # SYSTEM_SAME): CheckGameCompleted's translation, the deliveryman
        return name, vals, i + 1, tgt


# ---------------------------------------------------------------- the simulator

class Side:
    """One side's programs and its rules for warps and zone inits."""

    def __init__(self, ck, kind):
        self.ck, self.kind, self.progs = ck, kind, {}

    def prog(self, key):
        if key not in self.progs:
            pd = self.ck.pd
            if key == ('b2', 'balls'):          # (plat-ch5) Black 2's global item-ball file (pearl_items.py)
                self.progs[key] = B2Prog(pd, None, path=b2_item_ball_file())
            else:
                self.progs[key] = PlatProg(pd, key[1]) if key[0] == 'plat' else B2Prog(pd, pd.zones[key[1]])
        return self.progs[key]

    def zone_prog(self, pid):
        return self.prog(('plat', self.ck.pd.zones[pid]['scripts']) if self.kind == 'plat' else ('b2', pid))


# ---- plat-ch5 (2026-11-07): item balls, and a chapter's "compare" options (data/platinum/story_flow.json row or beats file) ----
# - item balls: Platinum's visible items 7000+n (file 370, entry n+1) are Black 2's global file 1240, entry for entry
#   (pearl_items.py); the person talked to is VAR_LAST_TALKED on Platinum's side and pl_RemoveTalkedObject's on Black 2's.
# - "compare": {"won_only": true}: every battle is won (CheckWonBattle answers 1: a lost battle blacks out on both sides and
#   ends the story path); {"carry": "saved"}: the Trainers are compared beat by beat (the set battled on each side), and the
#   states carried to the next beat are the distinct saved ones (zone, flags, vars). A long chapter's forks (gender,
#   starter, time of day, a YES or NO) multiply otherwise past STATES and the cut drops the story's own path.
ITEM_BALLS = range(7000, 7327)
B2_ITEM_BALL_FILE = '1240_global_item_balls.s'
PARTNER_VAR = 0x403F                    # (plat-ch7) Platinum's VAR_PARTNER_TRAINER_ID: SetHasPartner's partner
LAST_TALKED = 0x800D                    # Platinum's VAR_LAST_TALKED (generated/vars_flags.txt)


def b2_item_ball_file():
    for d in (pearl_story.SRC_SCRIPTS, os.path.join(ROOT, 'src', 'field_scripts')):
        p = os.path.join(d, B2_ITEM_BALL_FILE)
        if os.path.exists(p):
            return p
    return None


def leaves(st, must):
    """Does state st leave a beat's "must" (story_flow.json: PFLAG_xxxx, PVAR_xxxx=v; Platinum's own numbers; ITEM:, BADGE:,
    T:, POKETCH are not kept here)?"""
    for m in must:
        k, _, v = m.partition('=')
        mm = re.fullmatch(r'!?P(FLAG|VAR)_([0-9A-Fa-f]{4})', k)
        if not mm:
            continue
        n = int(mm.group(2), 16)
        if k.startswith('!'):                       # "!NAME": must stay clear
            if (st['flags'].get(n, False) if mm.group(1) == 'FLAG' else st['vars'].get(n, 0)):
                return False
            continue
        if mm.group(1) == 'FLAG' and not st['flags'].get(n, False):
            return False
        if mm.group(1) == 'VAR' and st['vars'].get(n, 0) != (int(v, 0) if v else st['vars'].get(n, 0) or 1):
            return False
    return True


def saved_sig(st):
    """sig without the Trainers battled."""
    return sig(st)[:3]
# ---- end plat-ch5 ------------------------------------------------------------------------------------------------------


# ---- plat-ch6 (2026-11-07): badges, and the clock. GiveBadge gives one, CheckBadgeAcquired reads it (both sides: pl_GiveBadge and
# pl_CheckBadgeAcquired are Platinum's commands), and a test start's `pl_GiveBadge n` lines give them first. Before, a badge
# check was unknown and forked: Route 213's on-transition, which shows the grunt only with the Fen Badge, carried a state
# without him to the next beat. st['badges'] is a tuple (copy() keeps it); a state without the key has none.
def test_start_badges(chapter, part=None):
    """The badges a chapter's test start gives (its TEST_LINES' pl_GiveBadge n), or () (part: a second start, plat-ch9)."""
    sec = start_section(chapter, part)
    tl = re.search(r'TEST_LINES="([^"]*)"', sec) if sec else None
    return tuple(sorted({int(x) for x in re.findall(r'pl_GiveBadge (\d+)', tl.group(1))})) if tl else ()


def badge_op(st, name, vals):
    """True if name is a badge command (and its effect is done on st). Also Black 2's RTCGetTime hour, minute (the
    translation of Platinum's GetHour): both are unknown here (before, only the minute was, so the hour stayed 0 and the
    Pokémon Mansion office's night branch never ran on Black 2's side)."""
    if name == 'RTCGetTime':
        for v in vals[:2]:
            if isinstance(v, int) and v >= 0x4000:
                st['vars'][v] = None
        return True
    if name == 'GiveBadge' and isinstance(vals[0], int) and vals[0] < 0x4000:
        st['badges'] = tuple(sorted(set(st.get('badges', ())) | {vals[0]}))
        return True
    if name == 'CheckBadgeAcquired' and len(vals) > 1 and isinstance(vals[1], int) and vals[1] >= 0x4000 \
            and isinstance(vals[0], int) and vals[0] < 0x4000:
        st['vars'][vals[1]] = int(vals[0] in st.get('badges', ()))
        return True
    return False
# ---- end plat-ch6 ------------------------------------------------------------------------------------------------------


def sig(st):
    """What a state leaves for later beats: the saved flags and vars (no map-local or script ones), the zone, and the Trainers
    battled on the way (Platinum's numbers)."""
    return (st['zone'], tuple(sorted((k, v) for k, v in st['flags'].items() if k not in LOCAL_FLAGS and k < B2_FLAG and v)),
            tuple(sorted((k, v) for k, v in st['vars'].items() if k not in LOCAL_VARS and k < 0x8000 and v)), st.get('battles', ()))


class Checker:
    def __init__(self, verbose=False):
        self.pd = pearl_story.PearlData()
        self.names = Names()
        self.verbose = verbose
        self.sides = {'plat': Side(self, 'plat'), 'b2': Side(self, 'b2')}
        self.b2_to_pid = {}
        for pid, b2 in self.pd.b2_zone.items():
            self.b2_to_pid.setdefault(b2, pid)
        self.problems = []
        self.b2_trainer = {e['b2']: int(k) for k, e in pearl_ids.Ids().reg['trainers'].items()}

    # ---- state helpers
    def objects(self, pid):
        return {o['id']: o for o in self.pd.events(self.pd.zones[pid])['object_events']
                if o['script'] != pearl_events.COPY_SCRIPT}

    def arrive(self, side, st, pid):
        """Zone change: map-local flags and vars cleared, the new zone's on-transition then on-load scripts."""
        st['flags'] = {k: v for k, v in st['flags'].items() if k not in LOCAL_FLAGS}
        st['vars'] = {k: v for k, v in st['vars'].items() if k not in LOCAL_VARS}
        st['zone'] = pid
        entries, tables = pearl_events.level_scripts(self.pd, self.pd.zones[pid])
        out = [st]
        for kind in (2, 4):
            for t, sid in entries:
                if t != kind:
                    continue
                nxt = []
                for s in out:
                    nxt += self.run(side, s, self.script_start(side, pid, sid), init=True)
                out = nxt or out
        return out

    def script_start(self, side, pid, sid):
        """(program key, position) of zone pid's script sid (a global id >= 2000: its common file / the zone file's proxy)."""
        sd = self.sides[side]
        if side == 'b2' and sid in ITEM_BALLS:          # (plat-ch5) an item ball: Black 2's global file, entry for entry
            p = sd.prog(('b2', 'balls'))
            return p.key, p.entry(sid - ITEM_BALLS.start + 1)
        if sid >= 2000:
            f, bank, k = pearl_story.script_location(sid)
            if side == 'plat':
                return ('plat', f), sd.prog(('plat', f)).entry(k)
            p = sd.zone_prog(pid)
            lbl = next((l for l in (f'PearlProxy_{sid}', f'C{f}_{k}_S{k}', f'T{f}_{k}_S{k}') if l in p.labels), None)
            return p.key, p.labels.get(lbl)
        p = sd.zone_prog(pid)
        return p.key, p.entry(sid)

    # ---- running a script
    def run(self, side, st0, start, init=False, limit_paths=PATHS, keep_all=False):
        """Every end state of a script from st0. A Platinum Warp goes on in the new zone; a generated pl_Warp ends the path and
        the reserved script runs in the destination."""
        sd = self.sides[side]
        key, a = start
        if a is None:
            return [st0]
        st = self.copy(st0)
        st.update(stack=[], cmp=None, steps=0, reserve=None)
        todo, ends, paths, seen = [(key, a, st)], [], 0, set()
        while todo and paths < limit_paths:
            key, a, st = todo.pop()
            paths += 1
            prog = sd.prog(key)
            alive = True
            while alive:
                st['steps'] += 1
                ins = prog.insn(a) if st['steps'] < STEPS else None
                if ins is None:
                    alive = False
                    if st['steps'] >= STEPS:
                        break
                    ends.append(st)
                    break
                name, vals, nxt, tgt = ins
                mark = (key, a, st['cmp'], tuple(sorted(st['flags'].items())), tuple(sorted(st['vars'].items(), key=lambda kv: kv[0])),
                        tuple(st['stack']), st.get('battles', ()))
                if name in ('GoToIf', 'CallIf', 'GoTo'):
                    if mark in seen:                      # a loop that changes nothing (a NO answered again): dropped
                        alive = False
                        break
                    seen.add(mark)
                if name in ('End', 'ReturnCommonScript') or (name == 'Return' and not st['stack']):
                    if name == 'ReturnCommonScript' and st['stack']:
                        key, nxt = st['stack'].pop()
                        prog = sd.prog(key)
                        a = nxt
                        continue
                    if name == 'End' and st['stack'] and key[0] == 'plat' and st['stack'][-1][0] != key:
                        key, nxt = st['stack'].pop()          # a common script's End returns to its caller (Platinum)
                        prog = sd.prog(key)
                        a = nxt
                        continue
                    ends.append(st)
                    alive = False
                    break
                if name == 'Return':
                    key, nxt = st['stack'].pop()
                    prog = sd.prog(key)
                elif name == 'GoTo':
                    nxt = tgt
                elif name == 'Call':
                    st['stack'].append((key, nxt))
                    nxt = tgt
                elif name == 'CallCommonScript' and side == 'plat':
                    f, bank, k = pearl_story.script_location(vals[0])
                    st['stack'].append((key, nxt))
                    key, nxt = ('plat', f), sd.prog(('plat', f)).entry(k)
                    prog = sd.prog(key)
                elif name in ('GoToIf', 'CallIf'):
                    c = vals[0]
                    taken = None if st['cmp'] is None or not isinstance(c, int) or c >= 6 else bool(LUT[c][st['cmp']])
                    if taken is None:
                        other = self.copy(st)
                        if name == 'CallIf':
                            other['stack'].append((key, nxt))
                        todo.append((key, tgt, other))
                        taken = False
                    if taken:
                        if name == 'CallIf':
                            st['stack'].append((key, nxt))
                        nxt = tgt
                elif name == 'Warp' and side == 'plat':
                    m = vals[0]
                    if isinstance(m, int) and m < 0x4000:
                        keep = dict(stack=list(st['stack']), cmp=None, steps=st['steps'], reserve=None)
                        rest = [dict(o, **self.copy(keep)) for o in self.arrive(side, st, m)]
                        st = rest[0]
                        for o in rest[1:]:
                            todo.append((key, nxt, o))
                elif name in DOMAINS and len(vals) > DOMAINS[name][0] and isinstance(vals[DOMAINS[name][0]], int) \
                        and vals[DOMAINS[name][0]] >= 0x4000:
                    arg, choices = DOMAINS[name]
                    if getattr(self, 'won_only', False) and name in ('CheckWonBattle', 'CheckWonFirstBattle'):
                        choices = [1]                             # (plat-ch5: "compare": {"won_only": true})
                    if vals[arg] in getattr(self, 'beat_set', {}):  # (plat-starts: a story_flow beat's "set" answers it, as
                        choices = [self.beat_set[vals[arg]]]         # platinum_flow_check: on the Bicycle, a NO)
                    for v in choices[1:]:
                        other = self.copy(st)
                        other['vars'][vals[arg]] = v
                        todo.append((key, nxt, other))
                    st['vars'][vals[arg]] = choices[0]
                elif name == 'ClearGame':                 # (plat-ch10) the game clear, both sides (Platinum's ClearGame, the
                    st['flags'][0x964] = True             # generated pl_ClearGame: Black 2's own ending): FLAG_GAME_COMPLETED,
                    for o in self.arrive(side, st, self.pd.by_name['MAP_TWINLEAF_PLAYER_HOUSE_2F']['id']):    # the record,
                        o.update(stack=[], cmp=None, reserve=None)    # the save, the credits; Continue in the player's room
                        ends.append(o)
                    alive = False
                    break
                elif name == 'RTReserveScript':
                    st['reserve'] = vals[0]
                elif name == 'Warp':                      # generated: the map changes when the script ends
                    pid = self.b2_to_pid.get(vals[0])
                    k = st['reserve']
                    steps = st['steps']
                    for o in self.arrive(side, st, pid) if pid is not None else [st]:
                        o.update(stack=[], cmp=None, steps=steps, reserve=None)
                        if k is not None:
                            p = sd.zone_prog(o['zone'])
                            todo.append((p.key, p.entry(k), o))
                        else:
                            ends.append(o)
                    alive = False
                    break
                else:
                    self.op(side, st, name, vals)
                if nxt is None:
                    ends.append(st)
                    break
                a = nxt
        if not init and not keep_all:
            changed = [s for s in ends if sig(s) != sig(st0)]
            ends = changed or ends
        out, have = [], set()
        for s in ends:
            for k in ('stack', 'cmp', 'steps', 'reserve'):
                s.pop(k, None)
            g = (sig(s), tuple(sorted(s['vars'].items(), key=lambda kv: kv[0])) if init else ())
            if g not in have:
                have.add(g)
                out.append(s)
        return out

    @staticmethod
    def copy(st):
        return {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in st.items()}

    @staticmethod
    def val(st, v):
        if isinstance(v, tuple):
            return None
        return st['vars'].get(v, 0) if 0x4000 <= v < 0x10000 else v

    def op(self, side, st, name, vals):
        F, V = st['flags'], st['vars']
        isvar = lambda v: isinstance(v, int) and v >= 0x4000
        if side == 'plat' and name in ('SetVarFromValue', 'CompareVarToValue') and vals[0] in DYNAMIC and isinstance(vals[1], int):
            vals = [vals[0], pearl_events.sprite_code(vals[1]) or 0]    # (the code the translation writes and compares)
        # (plat-ch11: the Battleground. Its daily draw (VAR_BATTLEGROUND_TRAINER_1-4, copied into the sprite vars) is the Black 2
        # codes on both sides, as the translation writes it (pl_GetRandomBattlegroundTrainers): the first three Leaders and the
        # first other Trainer, as platinum_flow_check; Platinum's talks copy a sprite var into VAR_MAP_LOCAL_0x01 and compare it
        # with graphics: compared as codes, as the translation does (pearl_story h_compare_dynamic_copy))
        if side == 'plat' and name == 'SetVarFromVar' and len(vals) > 1 and isinstance(vals[1], int) and vals[1] in DYNAMIC \
                and vals[0] not in DYNAMIC:
            st['dyncopy'] = sorted(set(st.get('dyncopy', [])) | {vals[0]})
        if side == 'plat' and name == 'CompareVarToValue' and vals[0] in st.get('dyncopy', []) and isinstance(vals[1], int) \
                and vals[1] < 0x4000 and pearl_events.sprite_code(vals[1]) is not None:
            vals = [vals[0], pearl_events.sprite_code(vals[1])]
        if name == 'GetRandomBattlegroundTrainers' and len(vals) >= 4:
            got = [pearl_events.sprite_code(g) for g in (126, 127, 128, 141)] if side == 'plat' else [vals[4], vals[5], vals[6], vals[12]]
            for v, x in zip(vals[:4], got):
                st['vars'][v] = x
            return
        if name == 'CompareVarToValue':
            x, y = self.val(st, vals[0]), self.val(st, vals[1]) if len(vals) > 1 else None
            st['cmp'] = None if x is None or y is None else (0 if x < y else 1 if x == y else 2)
        elif name == 'CompareVarToVar':
            x, y = self.val(st, vals[0]), self.val(st, vals[1])
            st['cmp'] = None if x is None or y is None else (0 if x < y else 1 if x == y else 2)
        elif name == 'CheckFlag':
            f = vals[0]
            v = F.get(f, False) if isinstance(f, int) and (f < 0x4000 or f >= B2_FLAG) else None
            st['cmp'] = None if v is None else int(v)
        elif name == 'FlagGetVar':
            f, var = vals[0], vals[1]
            if isvar(var):
                V[var] = int(F.get(f, False)) if isinstance(f, int) and (f < 0x4000 or f >= B2_FLAG) else None
        elif name in ('SetFlag', 'ClearFlag'):
            if isinstance(vals[0], int) and (vals[0] < 0x4000 or vals[0] >= B2_FLAG):
                F[vals[0]] = name == 'SetFlag'
        elif name == 'SetVarFromValue':
            if isvar(vals[0]):
                V[vals[0]] = vals[1] if isinstance(vals[1], int) else None
        elif name == 'SetVarFromVar':
            if isvar(vals[0]):
                V[vals[0]] = self.val(st, vals[1])
        elif name in ('AddVar', 'SubVar', 'WorkAdd', 'WorkSub'):
            if isvar(vals[0]):
                x, y = self.val(st, vals[0]), self.val(st, vals[1])
                V[vals[0]] = None if x is None or y is None else (x + y if name in ('AddVar', 'WorkAdd') else x - y) & 0xFFFF
        elif name == 'RemoveObject':
            if side == 'plat':
                o = self.objects(st['zone']).get(self.val(st, vals[0]))
                if o and o['hidden_flag']:
                    F[o['hidden_flag']] = True
            elif len(vals) > 1 and isinstance(vals[1], int) and 0 < vals[1] < 0x4000:
                F[vals[1]] = True                       # pl_RemoveObject uid, flag
        elif name in ('SetHasPartner', 'ClearHasPartner') and side == 'plat':     # (plat-ch7) a partner battles along
            st['partner'] = name == 'SetHasPartner'
        elif name in ('StartTrainerBattle', 'StartFirstBattle', 'StartFirstTrainerBattle', 'StartTagBattle'):
            ids = [self.val(st, v) for v in vals if v]
            if side == 'plat' and name == 'StartTrainerBattle' and st.get('partner'):
                ids = [st['vars'].get(PARTNER_VAR, 0)] + ids      # (plat-ch7: Riley; Black 2's pl_StartTagBattle names him)
            if side == 'b2':                          # Black 2 ids back to Platinum's numbers (PTRAINER_n is n already)
                ids = [None if t is None else t - TRAINER_TAG if t >= TRAINER_TAG else self.b2_trainer.get(t, ('b2', t)) for t in ids]
            st['battles'] = st.get('battles', ()) + (tuple(ids),)
        elif name == 'GetCurrentMapID' and side == 'plat' and isvar(vals[0]):
            V[vals[0]] = st['zone']                     # (the generated file writes the zone's own number)
        elif name == 'RemoveTalkedObject' and side == 'b2':     # (plat-ch5) an item ball taken: the talked person's flag
            o = self.objects(st['zone']).get(st.get('talked'))
            if o and o['hidden_flag']:
                F[o['hidden_flag']] = True
        elif name == 'CheckItemIsPlate' and isvar(vals[1]):        # (plat-ch5: the generated macro tests the same, both sides)
            item = self.val(st, vals[0])
            V[vals[1]] = None if item is None else int(item in PLATES)
        elif name == 'GetPlayerMapPos' and st.get('pos') and isvar(vals[0]) and isvar(vals[1]):
            V[vals[0]], V[vals[1]] = st['pos']
        elif badge_op(st, name, vals):                            # (plat-ch6) GiveBadge, CheckBadgeAcquired, RTCGetTime
            pass
        # (plat-ch11: the post-game's two checks on both sides: the National Pokédex, kept as flag NATDEX_FLAG (no Platinum flag
        # has that number) so it is carried with the saved flags; the game clear, Platinum's CheckGameCompleted and the
        # generated FlagGet 2400 (Black 2's game clear, read as FLAG_GAME_COMPLETED where the file is parsed) both reading it)
        elif name == 'SetNationalDex' or (name == 'GetSetNationalDexEnabled' and vals and vals[0] == 1):
            F[NATDEX_FLAG] = True               # (Platinum's 0x22D mode 1 sets, the other modes get: pearl_story h_natdex)
        elif name in ('GetNationalDex', 'GetSetNationalDexEnabled') and vals and isvar(vals[-1]):
            V[vals[-1]] = int(F.get(NATDEX_FLAG, False))
        elif name == 'CheckGameCompleted' and side == 'plat' and isvar(vals[0]):   # (plat-ch9) FLAG_GAME_COMPLETED (0x964), which
            V[vals[0]] = int(F.get(0x964, False) or F.get(B2_FLAG + 2400, False))  # the translation reads as Black 2's 2400
        elif QUIET.match(name) or name.startswith('GetItemName'):    # (plat-ch5: GetItemNameWithIndefArticle buffers a name)
            pass
        elif vals and isvar(vals[-1]) and re.search(r'Get|Is|Check|Count|Can|Find|Show|Open|Choose|Select|Victory|Result', name):
            V[vals[-1]] = None                          # a result: not known here
            if name in ('GetPlayerMapPos',) and len(vals) > 1 and isvar(vals[-2]):
                V[vals[-2]] = None

    # ---- beats
    def trigger(self, side, st, pid, k, beat):
        """(holds, why) of the beat's trigger in state st (zone pid, script entry k)."""
        zone = self.pd.zones[pid]
        ev = self.pd.events(zone)
        F, V = st['flags'], st['vars']
        entries, tables = pearl_events.level_scripts(self.pd, zone)
        for rows in tables:
            if any(s == k for var, val, s in rows):
                first = next(((var, val, s) for var, val, s in rows if V.get(var, 0) == val), None)
                if first is None:
                    return False, 'no frame-table row matches (' + ', '.join(f'{self.names.show(v)} = {V.get(v, 0)}, wants {x}' for v, x, s in rows if s == k) + ')'
                if first[2] != k:
                    return False, f'another frame-table row comes first: script {first[2]} ({self.names.show(first[0])} = {first[1]})'
                return True, f'frame table: {self.names.show(first[0])} = {first[1]}'
        coords = [c for c in ev['coord_events'] if c['script'] == k]
        if coords:
            c = coords[0]
            if c['var'] and V.get(c['var'], 0) != c['value']:
                return False, f'step trigger at ({c["x"]}, {c["z"]}): {self.names.show(c["var"])} = {V.get(c["var"], 0)}, wants {c["value"]}'
            return True, f'step trigger at ({c["x"]}, {c["z"]})' + (f': {self.names.show(c["var"])} = {c["value"]}' if c['var'] else '')
        objs = [o for o in ev['object_events'] if o['script'] == k]
        if objs:
            o = objs[0]
            if o['hidden_flag'] and F.get(o['hidden_flag'], False):
                return False, f'person {o["id"]} is hidden ({self.names.show(o["hidden_flag"])} set)'
            return True, f'talk to person {o["id"]} at ({o["x"]}, {o["z"]})'
        if any(b['script'] == k for b in ev['bg_events']):
            return True, 'a sign'
        if any(s == k for t, s in entries):
            return True, 'a map script'
        return False, 'nothing in the zone runs this script'

    def trigger_tiles(self, pid, k):
        """The tiles of the step trigger that runs script k in zone pid (the player stands on one), or None."""
        c = next((c for c in self.pd.events(self.pd.zones[pid])['coord_events'] if c['script'] == k), None)
        if c is None:
            return None
        return [(x, z) for x in range(c['x'], c['x'] + c['width']) for z in range(c['z'], c['z'] + c['length'])]

    def frame_due(self, st):
        """The frame-table row (var, value, script) that runs next in st's zone, or None."""
        if st['zone'] is None:
            return None
        for rows in pearl_events.level_scripts(self.pd, self.pd.zones[st['zone']])[1]:
            first = next(((var, val, s) for var, val, s in rows if st['vars'].get(var, 0) == val), None)
            if first:
                return first
        return None

    def newgame(self, side):
        """The states after Platinum's new-game script (9600; the generated C377_1_S1 in Twinleaf's file), in Twinleaf."""
        pd = self.pd
        tw = pd.by_name[pearl_story.NEWGAME_ZONE]['id']
        start = self.script_start(side, tw, pearl_story.PEARL_NEW_GAME_SCRIPT)
        if side == 'b2':
            p = self.sides['b2'].zone_prog(tw)
            start = (p.key, p.labels.get('C377_1_S1'))
        return self.run(side, dict(flags={}, vars={}, zone=tw), start)

    def restart_states(self, data):
        """(plat-ch9) Both sides' states at a restart beat's test start (a story_flow row's "restart": its own start's TEST_SET,
        FlagReset lines, badges and zone), as check() builds the chapter's first start."""
        states = {}
        for side in ('plat', 'b2'):
            sts = self.newgame(side)
            flags, vars_ = parse_set(data['start'])
            for st in sts:
                st['flags'].update(flags)
                st['vars'].update(vars_)
                for f in data.get('start_clear', ()):
                    st['flags'][f] = False
                st['badges'] = tuple(data.get('start_badges', ()))
            states[side] = [s2 for s in sts for s2 in self.arrive(side, s, data['start_pid'])]
        return states

    def check(self, chapter):
        data = load_beats(self, chapter)
        pd = self.pd
        opts = data.get('compare') or {}                        # (plat-ch5)
        self.won_only = bool(opts.get('won_only'))
        states = {}
        for side in ('plat', 'b2'):
            sts = self.newgame(side)                    # (a test start runs the new-game script first too: test_story_start)
            if data['start'] == 'newgame':
                z0 = pd.by_name[pearl_story.PEARL_START[0]]['id']
            else:
                flags, vars_ = parse_set(data['start'])
                for st in sts:
                    st['flags'].update(flags)
                    st['vars'].update(vars_)
                    for f in data.get('start_clear', ()):
                        st['flags'][f] = False
                    st['badges'] = tuple(data.get('start_badges', ()))      # (plat-ch6)
                z0 = data['start_pid'] if 'start_pid' in data else pd.by_name[data['start_zone']]['id']
            states[side] = [s2 for s in sts for s2 in self.arrive(side, s, z0)]
            if side == 'plat':
                base = self.copy(self.newgame(side)[0])
        start_states = {side: [self.copy(s) for s in states[side]] for side in states}
        print(f'chapter {chapter}: {len(data["beats"])} beats from {data["start"] if data["start"] == "newgame" else "its test start"}'
              f'{" (" + data["source"] + ")" if data.get("source") else ""}')
        own_end = None                                          # (plat-starts: the states before another chapter's beat)
        for i, beat in enumerate(data['beats'], 1):
            if beat.get('foreign') and own_end is None:
                own_end = {side: [self.copy(s) for s in states[side]] for side in states}
            if beat.get('restart'):                             # (plat-ch9) the second test start
                states = self.restart_states(beat)
                print(f'{i:2d}. test start {beat["restart"]}: {beat["note"]}')
                continue
            zone = pd.by_name[beat['zone']]
            pid = zone['id']
            sc = beat.get('script')
            k = sc if isinstance(sc, int) else decomp_entries(zone).get(sc) if sc else 0
            label = f'{i:2d}. {beat["zone"][4:]} {sc or "(arrive)"}'
            if beat.get('fresh'):                               # from the start state, not after the beat before
                states = {side: [self.copy(s) for s in start_states[side]] for side in start_states}
            if k is None:
                self.problem(f'{label}: no such script in {zone["pl_name"]}')
                continue
            res, why, ran, fought = {}, {}, {}, {}
            for side in ('plat', 'b2'):
                nxt, bad = [], []
                for st in states[side]:
                    here = self.arrive(side, st, pid) if st['zone'] != pid or beat.get('arrive') else [st]
                    for s in here:
                        if not k:                                   # only the arrival
                            why[side] = 'arrival'
                            nxt.append(s)
                            continue
                        ok, w = self.trigger(side, s, pid, k, beat)
                        why[side] = w
                        if beat.get('not') or not ok:
                            if ok == bool(beat.get('not')) and not beat.get('optional'):
                                bad.append(w)
                            nxt.append(s)
                            continue
                        ran[side] = True
                        ends = []
                        talked = next((o['id'] for o in pd.events(zone)['object_events'] if o['script'] == k), None) \
                            if str(w).startswith('talk to person') else None        # (plat-ch5: the person talked to)
                        for t in self.trigger_tiles(pid, k) or [None]:     # a step trigger: the player on each of its tiles
                            s2 = self.copy(s)
                            s2['pos'] = t
                            if talked is not None:
                                s2['talked'] = talked
                                if side == 'plat':
                                    s2['vars'][LAST_TALKED] = talked
                            self.beat_set = {int(x[5:], 16): v for x, v in (beat.get('set') or {}).items()   # (plat-starts)
                                             if re.fullmatch(r'PVAR_[0-9A-F]{4}', x)}
                            ends += self.run(side, s2, self.script_start(side, pid, k), keep_all=True)
                            self.beat_set = {}
                        for e in ends:
                            e.pop('pos', None)
                            e.pop('talked', None)
                        if opts.get('carry') == 'saved' and beat.get('must'):   # (plat-ch5) the story's own way first: an
                            ends = [e for e in ends if leaves(e, beat['must'])] or ends   # unchanged path can be it
                        changed = [e for e in ends if sig(e) != sig(s)]  # (a tile no case takes, a NO: the player goes on)
                        nxt += changed or ends
                uniq, have = [], set()
                for s in nxt:
                    if sig(s) not in have:
                        have.add(sig(s))
                        uniq.append(s)
                if opts.get('carry') == 'saved' and beat.get('must') and uniq:   # (plat-ch5) the story's own way: what the
                    sel = [s for s in uniq if leaves(s, beat['must'])]           # beat must leave picks its end states
                    if not sel:
                        self.problem(f'{label}: {side}: no end state leaves {", ".join(beat["must"])}')
                    uniq = sel or uniq
                if opts.get('carry') == 'saved':               # (plat-ch5) this beat's Trainers, then the distinct saved states
                    fought[side] = {s.get('battles', ()) for s in uniq}
                    kept, have = [], set()
                    for s in uniq:
                        if saved_sig(s) not in have:
                            have.add(saved_sig(s))
                            kept.append(dict(s, battles=()))
                    uniq = kept
                if len(uniq) > STATES:
                    self.problem(f'{label}: {side}: {len(uniq)} end states (more than {STATES}): kept the first {STATES}')
                    uniq = uniq[:STATES]
                res[side] = uniq
                if beat.get('optional') and not ran.get(side):
                    bad.append(f'{why.get(side)} in every state')
                for w in sorted(set(bad)):
                    self.problem(f'{label}: {side}: ' + (f'should not run but does ({w})' if beat.get('not') else f'does not run: {w}'))
            for name, want in (beat.get('expect') or {}).items():
                n = self.names.by_name.get(name)
                for side in ('plat', 'b2'):
                    for s in res[side]:
                        got = s['flags'].get(n, False) if name.startswith('FLAG_') else s['vars'].get(n, 0)
                        if got != want:
                            self.problem(f'{label}: {side}: expected {name} = {want}, got {got}')
                            break
            a = {sig(s) for s in res['plat']}
            b = {sig(s) for s in res['b2']}
            if a != b:
                self.problem(f'{label}: the two sides end differently:\n' + self.diff(res['plat'], res['b2']))
            if fought and fought.get('plat') != fought.get('b2'):  # (plat-ch5: carry "saved": this beat's Trainers)
                self.problem(f'{label}: the Trainers battled differ: Platinum {sorted(fought.get("plat", ()), key=str)}, '
                             f'Black 2 {sorted(fought.get("b2", ()), key=str)}')
            if self.verbose or a != b:
                print(f'{label}: {why.get("plat", "")}; {len(res["plat"])}/{len(res["b2"])} end states')
                if self.verbose:
                    print(self.changes(states['plat'], res['plat']))
            else:
                print(f'{label}: ok ({why.get("plat", "")})')
            states = res
            nb = data['beats'][i] if i < len(data['beats']) else None
            for side in ('plat', 'b2') if not (nb and nb.get('restart')) else ():   # (plat-ch9: the next start replaces it)
                for s in states[side]:
                    f = self.frame_due(s)
                    if f is None:
                        continue
                    zname = pd.zones[s['zone']]['name']
                    nk = nb and (nb['script'] if isinstance(nb.get('script'), int)        # (plat-ch5: a story_flow row's number)
                                 else decomp_entries(pd.zones[s['zone']]).get(nb['script']))
                    want = nb and nb['zone'] == zname and nk == f[2]
                    if not want:
                        self.problem(f'{label}: {side}: then the frame table of {zname[4:]} runs script {f[2]} '
                                     f'({self.names.show(f[0])} = {f[1]}), which is not the next beat')
        if data.get('next_start'):
            states = own_end or states                  # (plat-starts: the next start against the chapter's own end, as
            want_f, want_v = parse_set(data['next_start'])      # platinum_flow_check --next: not after the later chapters' beats
                                                                # its row runs in its zones, chapter 2's Looker and grunts)
            want_f = {k for k, v in base['flags'].items() if v and k not in LOCAL_FLAGS and k < B2_FLAG} | set(want_f)
            want_f -= set(data.get('next_clear', ()))   # (plat-ch5: the next start's FlagReset lines)
            want_v = {**{k: v for k, v in base['vars'].items() if v and k not in LOCAL_VARS and k < 0x8000}, **want_v}
            def off_by(s):                              # (plat-starts: how far an end state is from the next start)
                F = {k for k, v in s['flags'].items() if v and k not in LOCAL_FLAGS and k < B2_FLAG}
                V = {k: v for k, v in s['vars'].items() if v and k not in LOCAL_VARS and k < 0x8000 and k not in DYNAMIC}
                wv = {k: v for k, v in want_v.items() if k not in DYNAMIC}
                return len(F ^ set(want_f)) + sum(1 for k in set(wv) | set(V) if wv.get(k, 0) != V.get(k, 0))
            for side in ('plat', 'b2'):
                # (plat-starts: of a chapter's several end states (a YES or NO, a weekday, a Trainer met or not), the one
                # nearest the next start, not the first: chapter 5's first end state had used the Storage Key at the
                # warehouse's inner door, a way the story doesn't take there)
                for s in sorted(states[side], key=off_by)[:1]:
                    F = {k for k, v in s['flags'].items() if v and k not in LOCAL_FLAGS and k < B2_FLAG}
                    V = {k: v for k, v in s['vars'].items() if v and k not in LOCAL_VARS and k < 0x8000}
                    miss_f = sorted(set(want_f) - F)
                    extra_f = sorted(F - set(want_f))
                    diff_v = sorted(k for k in set(want_v) | set(V) if want_v.get(k, 0) != V.get(k, 0))
                    for f in miss_f:
                        self.problem(f'next start ({side}): sets {self.names.show(f)}, which this chapter leaves clear')
                    for f in extra_f:
                        if not_carried(self.names.by_num.get(f, '')):          # (plat-starts)
                            print(f'  note: next start ({side}) leaves {self.names.show(f)} clear, which this chapter sets: '
                                  f'not carried (notes/PLATINUM_CHAPTERS.md "How to test the whole story")')
                            continue
                        self.problem(f'next start ({side}): leaves {self.names.show(f)} clear, which this chapter sets')
                    want_v = {k: v for k, v in want_v.items() if k not in DYNAMIC}
                    V = {k: v for k, v in V.items() if k not in DYNAMIC}
                    diff_v = sorted(k for k in set(want_v) | set(V) if want_v.get(k, 0) != V.get(k, 0))
                    for v in diff_v:
                        self.problem(f'next start ({side}): {self.names.show(v)} = {want_v.get(v, 0)}, this chapter leaves {V.get(v, 0)}')
        print(f'{len(self.problems)} problems')
        for p in self.problems:
            print('  ' + p)
        return 1 if self.problems else 0

    def problem(self, msg):
        if msg not in self.problems:
            self.problems.append(msg)

    def diff(self, a, b):
        fa = [(s['flags'], s['vars']) for s in a]
        fb = [(s['flags'], s['vars']) for s in b]
        out = []
        def saved(fv):
            f, v = fv
            return ({k for k, x in f.items() if x and k not in LOCAL_FLAGS and k < B2_FLAG},
                    {k: x for k, x in v.items() if x and k not in LOCAL_VARS and k < 0x8000})
        sa, sb = [saved(x) for x in fa], [saved(x) for x in fb]
        allf_a = set.union(*[x[0] for x in sa]) if sa else set()
        allf_b = set.union(*[x[0] for x in sb]) if sb else set()
        for f in sorted(allf_a - allf_b):
            out.append(f'      only Platinum sets {self.names.show(f)}')
        for f in sorted(allf_b - allf_a):
            out.append(f'      only Black 2 sets {self.names.show(f)}')
        va = collections.defaultdict(set)
        vb = collections.defaultdict(set)
        for f, v in sa:
            for k, x in v.items():
                va[k].add(x)
        for f, v in sb:
            for k, x in v.items():
                vb[k].add(x)
        for k in sorted(set(va) | set(vb)):
            if va.get(k, set()) != vb.get(k, set()):
                out.append(f'      {self.names.show(k)}: Platinum {sorted(va.get(k, {0}), key=str)}, Black 2 {sorted(vb.get(k, {0}), key=str)}')
        ba, bb = {s.get('battles', ()) for s in a}, {s.get('battles', ()) for s in b}
        if ba != bb:
            out.append(f'      Trainers battled: Platinum {sorted(ba, key=str)}, Black 2 {sorted(bb, key=str)}')
        zs = ({s['zone'] for s in a}, {s['zone'] for s in b})
        if zs[0] != zs[1]:
            out.append(f'      zone: Platinum {sorted(self.pd.zones[z]["name"] for z in zs[0])}, Black 2 {sorted(self.pd.zones[z]["name"] for z in zs[1] if z is not None)}')
        if len(a) != len(b):
            out.append(f'      end states: Platinum {len(a)}, Black 2 {len(b)}')
        return '\n'.join(out) or '      (the same flags and vars; the states differ in number)'

    def changes(self, before, after):
        if not before or not after:
            return '      (no state)'
        b, a = before[0], after[0]
        out = []
        for k in sorted(set(a['flags']) | set(b['flags'])):
            if k not in LOCAL_FLAGS and k < B2_FLAG and a['flags'].get(k, False) != b['flags'].get(k, False):
                out.append(f'      {"set" if a["flags"].get(k) else "clear"} {self.names.show(k)}')
        for k in sorted(set(a['vars']) | set(b['vars'])):
            if k not in LOCAL_VARS and k < 0x8000 and a['vars'].get(k, 0) != b['vars'].get(k, 0):
                out.append(f'      {self.names.show(k)} = {a["vars"].get(k, 0)}')
        return '\n'.join(out) or '      (nothing saved changes)'


# ---- plat-starts (2026-11-07): what the test starts leave out on purpose (notes/PLATINUM_CHAPTERS.md "How to test the whole
# story"): side gifts' received flags (FLAG_RECEIVED_*, FLAG_OBTAINED_*: a start carries a gift only where a later chapter
# reads it; key items' flags are always carried, so they never come here), the day's flags (Black 2 clears them when the day
# changes) and chapter 3's side Rotom (a start's party is TEST_TEAM's; chapter 12 catches the TV's Rotom itself).
def not_carried(name):
    return bool(re.match(r'^FLAG_(RECEIVED|OBTAINED|DAILY)_', name)) or name == 'FLAG_CAUGHT_OLD_CHATEAU_ROTOM'
# ---- end plat-starts ----------------------------------------------------------------------------------------------------


STORY_FLOW = os.path.join(ROOT, 'data', 'platinum', 'story_flow.json')
CHAPTERS_NOTE = os.path.join(ROOT, 'notes', 'PLATINUM_CHAPTERS.md')


def start_section(chapter, part=None):
    """A chapter's section of notes/PLATINUM_CHAPTERS.md, or with part (plat-ch9) its "**Test start B**" block; None."""
    text = open(CHAPTERS_NOTE, encoding='utf-8').read()
    m = re.search(rf'^## Chapter {re.escape(str(chapter))}\b.*?(?=^## )', text, re.M | re.S)
    if not m or part is None:
        return m.group(0) if m else None
    b = re.search(rf'^\*\*Test start {part}\*\*.*?(?=^\*\*|\Z)', m.group(0), re.M | re.S)
    return b.group(0) if b else None


def test_start(chapter, part=None):
    """(TEST_SET, flags TEST_LINES clears, TEST_START's Black 2 zone or None) of a chapter's "Test start" in
    notes/PLATINUM_CHAPTERS.md (PFLAG_ and PVAR_ only; badges, items and the team don't matter here; part: a second start)."""
    sec = start_section(chapter, part)
    if not sec:
        return None
    ts = re.search(r'TEST_SET="([^"]*)"', sec)
    tl = re.search(r'TEST_LINES="([^"]*)"', sec)
    tz = re.search(r'TEST_START=(\d+),', sec)
    clear = [int(x, 16) for x in re.findall(r'FlagReset PFLAG_([0-9A-F]{4})', tl.group(1) if tl else '')]
    sets = re.findall(r'FlagSet (PFLAG_[0-9A-F]{4})', tl.group(1) if tl else '')
    return ','.join(filter(None, [ts.group(1) if ts else '', *sets])), clear, int(tz.group(1)) if tz else None


def load_beats(ck, chapter):
    """A chapter's beats: data/platinum/beats/<chapter>.json, or else its row of plat-ch2's data/platinum/story_flow.json (its
    trigger / frame / script N: the zone file's script N; talk N: the script of the person with local id N; expect "off": not;
    the start: the chapter's test start in notes/PLATINUM_CHAPTERS.md, and its next chapter's for next_start)."""
    path = os.path.join(BEATS, f'{chapter}.json')
    if os.path.exists(path):
        return json.load(open(path))
    rows = json.load(open(STORY_FLOW)).get(str(chapter)) if os.path.exists(STORY_FLOW) else None
    if rows is None:
        raise SystemExit(f'no beats for chapter {chapter} ({path}, {STORY_FLOW})')
    pd = ck.pd
    beats = []
    for r in rows['beats']:
        if 'warp' in r:                             # (plat-ch8) a warp beat runs no script; (plat-starts) it is the arrival in
            b = dict(zone='MAP_' + r['zone'], script=None, note=r.get('what', ''))      # its zone, whose map scripts
            if r.get('chapter') not in (None, chapter, str(chapter)):                     # platinum_flow_check runs too (the
                b['foreign'] = True                                                       # lakes' Maylene, Snowpoint's Center)
            beats.append(b)
            continue
        if 'restart' in r:                          # (plat-ch9) a second test start: both sides start there again
            tb = test_start(chapter, r['restart'])
            beats.append(dict(restart=r['restart'], note=r.get('what', ''), start=tb[0], start_clear=tb[1],
                              start_badges=test_start_badges(chapter, r['restart']), start_pid=ck.b2_to_pid.get(tb[2])))
            continue
        zone = pd.by_name['MAP_' + r['zone']]
        if 'talk' in r:
            o = next((o for o in pd.events(zone)['object_events'] if o['id'] == r['talk']), None)
            k = o['script'] if o else -1
        else:
            k = next(r[x] for x in ('trigger', 'frame', 'script') if x in r)
        b = dict(zone='MAP_' + r['zone'], script=k, note=r.get('what', ''))
        if r.get('set'):
            b['set'] = r['set']                     # (plat-starts: its PVAR_ answers, as platinum_flow_check gives them)
        if r.get('must'):
            b['must'] = r['must']                   # (plat-ch5: carry "saved" keeps the end states that leave it)
        if r.get('expect') == 'off':
            b['not'] = True
        if r.get('chapter') not in (None, chapter, str(chapter)):
            b['optional'] = True                    # (another chapter's beat run here: what it needs)
            b['foreign'] = True                     # (plat-starts: the chapter's own end is before it, as flow_check's)
        beats.append(b)
    ts = test_start(chapter)
    data = dict(beats=beats, source='story_flow.json')
    if rows.get('compare'):                         # (plat-ch5) the row's options for this tool
        data['compare'] = rows['compare']
    else:                                           # (plat-starts: a row is the story's way, as platinum_flow_check plays it:
        data['compare'] = {'won_only': True, 'carry': 'saved'}  # every battle won; rows 2-4 had no options, so the lost
                                                                # battles' states filled the 48 kept and the beats after failed)
    if ts is None or not ts[0] and ts[2] is None:
        data['start'] = 'newgame'
    else:
        data['start'], data['start_clear'] = ts[0], ts[1]
        data['start_badges'] = test_start_badges(chapter)           # (plat-ch6)
        data['start_pid'] = ck.b2_to_pid.get(ts[2]) if ts[2] is not None else pd.by_name[pearl_story.PEARL_START[0]]['id']
    nxt = test_start(int(chapter) + 1) if str(chapter).isdigit() else None
    if nxt and nxt[0]:
        data['next_start'] = nxt[0]
        data['next_clear'] = nxt[1]                 # (plat-ch5) the flags its TEST_LINES reset
    return data


def chapters_known():
    """Every chapter with beats, in story order (data/platinum/beats first, then story_flow.json's)."""
    out = [os.path.splitext(n)[0] for n in os.listdir(BEATS) if n.endswith('.json')] if os.path.isdir(BEATS) else []
    if os.path.exists(STORY_FLOW):
        out += [k for k in json.load(open(STORY_FLOW)) if not k.startswith('_')]
    return sorted(set(out), key=lambda c: (not c.isdigit(), int(c) if c.isdigit() else 0, c))


def main(argv):
    if not version.PLATINUM:
        print('run with PEARL_VERSION=platinum')
        return 2
    args = [a for a in argv if not a.startswith('-')]
    if not args:
        print(__doc__)
        return 2
    chapters = chapters_known() if args[0] == 'all' else args
    ck, worst = Checker('-v' in argv), 0
    for c in chapters:
        worst |= ck.check(c)
        ck.problems = []
    return worst


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
