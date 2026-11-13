"""Platinum's story flow, chapter by chapter, offline (no ROM): does each beat's trigger hold when the player gets there, and
is everything a chapter needs set by an earlier beat or by the chapter's test start? (notes/PLATINUM_CHAPTERS.md;
work/agents/PLATINUM_CHAPTER_BRIEF.md step 6.) Written for chapter 2 (plat-ch2, 2026-11-07); other chapters add their
beats to data/platinum/story_flow.json.

    PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py [N ...] [--trace] [--next]
        N        the chapters (default: every chapter in story_flow.json)
        --trace  every beat's path: the lines it reads (flag/var, value, where the value came from) and what it sets
        --next   also compare the chapter's end state with chapter N+1's test start (its TEST_SET in PLATINUM_CHAPTERS.md)
        --end    also print the chapter's end state as a test start (TEST_ITEMS, TEST_SET, TEST_LINES over the new game's
                 own state), the next chapter's start to begin from (plat-ch9)
    PEARL_VERSION=platinum python3 b2tools/platinum_flow_check.py --starts
                 every chapter's test start as one env line for patches/test_story_start.py, in test order (plat-starts:
                 notes/PLATINUM_CHAPTERS.md "How to test the whole story")

Run after `PEARL_VERSION=platinum python3 b2tools/pearl_story.py chapter N` (it reads the generated files,
work/platinum/src/field_scripts, which are what a build installs) and with work/platinum/heights (platinum_events.py
--heights) for the start tile. Exit 1 on a finding.

What it does:
- The start: what a test start runs, in order: Platinum's new-game script (C377_1_S1 in Twinleaf's generated file, which
  test_story_start keeps), TEST_TEAM's six Pokémon, flag 2401, TEST_ITEMS, TEST_SET, TEST_LINES (the chapter's section
  of notes/PLATINUM_CHAPTERS.md, or "start" in the chapter's row of story_flow.json).
- The start tile: the zone owns the tile (the overworld's matrix cell; patches/test_story_start's own check), the tile is
  walkable on the converted collision (warp_check.Warps offline), and the test start's Twinleaf file assembles (the real
  test_story_start.apply, given the zone headers and the world matrix it would read) and passes b2_script_check.
- Each beat (story_flow.json, in story order): its zone's map scripts first when the zone changes (on transition, on
  load; map-local flags and vars cleared, as Black 2 clears them), then its trigger is checked against the state:
    trigger N   a step trigger running script N: its var must equal its value;
    frame N     a row of the zone's frame table running script N: its var must equal its value;
    talk N      the person (Platinum's local id) N: its hide flag must be clear;
    script N    no condition (a sign, an item, a scene reached another way);
    warp [x, z] with "to": ZONE  no script runs: the first warp still on that tile after the zone's map scripts (their
                SetWarpEventPos) must lead to ZONE (plat-ch8: the lakes' stacked warps);
    restart X   (plat-ch9) no zone, no scene: the state becomes the chapter's test start X ("**Test start X**" in its
                section), its tile and file checked as the first start's; the beats after it run from there.
  "expect": "off" turns it round: the trigger must NOT hold then (a scene that must not play again, a guard gone).
  After a trigger or frame beat its condition must no longer hold (else the scene plays again), unless "repeats": true
  (a guard that turns the player back each time); "must": ["NAME", "NAME=v", "ITEM:n", "BADGE:n"] is what the beat
  must leave (its story outcome); "!NAME": what it must leave clear (plat-ch5).
  Then the beat's script runs in the generated file's macros (pl_ ...): GoTo/Call/If follow the state; a value the
  state can't know takes the beat's "set" ({"PVAR_800C": 1}: say NO), else the story's way: the player is a boy at the
  trigger's first tile (or "at"), YES in menus, every battle won, six Pokémon in the party, Turtwig as starter (387).
  Its writes (flags, vars, hide flags of RemoveObject, items, badges, beaten trainers) go into the state.
- Findings: a beat whose trigger doesn't hold (with who sets what it needs); a beat that ends where the script stops
  without End (a missing label, a loop); with --next, a flag or var chapter N+1's start sets that this chapter's end
  state (before any other chapter's beat run here) lacks. Notes (not findings): a story flag or var a beat reads before
  a later beat of the chapter sets it (mostly a branch for "not yet"; an order problem when the beat needed it).
"""
import collections, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402

FLOW = os.path.join(ROOT, 'data', 'platinum', 'story_flow.json')
CHAPTERS_NOTE = os.path.join(ROOT, 'notes', 'PLATINUM_CHAPTERS.md')
PEARL_H = os.path.join(ROOT, 'src', 'include', 'platinum', 'pearl.h')
TWINLEAF = 'MAP_TWINLEAF'
NEWGAME = 'C377_1_S1'               # Platinum's new-game flags (pearl_story: Pearl file 377 script 1 as a subroutine)
STEPS = 20000                       # a beat's command limit (a loop the state can't leave)
PLAYER_TEAM = 6                     # TEST_TEAM=1: six Pokémon
STARTER = 387                       # the chapters' PVAR_STARTER (Turtwig)
LOCAL_FLAG = re.compile(r'^PFLAG_00[0-3][0-9A-F]$')            # Platinum's map-local flags 0-0x3F
LOCAL_VAR = re.compile(r'^PVAR_40[01][0-9A-F]$|^PVAR_8')        # map-local vars 0x4000-0x401F, script vars 0x8000+
COND = {0: lambda r: r == 0, 1: lambda r: r == 1, 2: lambda r: r == 2, 3: lambda r: r in (0, 1), 4: lambda r: r in (1, 2),
        5: lambda r: r != 1}                                    # GoToIf/CallIf: 0 <, 1 ==, 2 >, 3 <=, 4 >=, 5 != (both VMs)


def cmp(a, b):
    if isinstance(a, str) or isinstance(b, str):    # (plat-ch11: a var holding a Trainer's name is only equal to itself)
        return 1 if a == b else 2
    return 0 if a < b else 1 if a == b else 2


class Names:
    """pearl.h: PFLAG_xxxx / PVAR_xxxx / PTRAINER_n -> Black 2 id, and the decomp's name in its comment."""
    def __init__(self):
        self.b2, self.what = {}, {}
        for m in re.finditer(r'^#define (P(?:FLAG|VAR|TRAINER)_\w+) (0x[0-9A-Fa-f]+|\d+)\s*(?://\s*(.*))?$', open(PEARL_H).read(), re.M):
            self.b2[m.group(1)] = int(m.group(2), 0)
            self.what[m.group(1)] = (m.group(3) or '').split(';')[0].strip()

    def label(self, k):
        w = self.what.get(k, '')
        w = w.split(': ', 1)[-1] if w else ''
        return f'{k} ({w})' if w else k


class File:
    """A generated zone file: its entries and its commands, by label."""
    LABEL = re.compile(r'^([.\w]+):')

    def __init__(self, path):
        self.path = path
        self.entries, self.code, self.at = [], [], {}
        for n, raw in enumerate(open(path), 1):
            line = raw.split('//')[0].rstrip()
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            m = re.match(r'ScriptEntry (\w+)$', s)
            if m:
                self.entries.append(m.group(1)); continue
            m = self.LABEL.match(s)
            if m:
                self.at[m.group(1)] = len(self.code); continue
            op, _, rest = s.partition(' ')
            args = [a.strip() for a in rest.split(',')] if rest.strip() else []
            self.code.append((op, args, n))

    def entry(self, n):
        """Label of script entry n (1-based, as Platinum numbers a zone's scripts)."""
        return self.entries[n - 1]


class Flow:
    def __init__(self):
        import pearl_story
        self.ps = pearl_story
        self.pd = pearl_story.PearlData()
        self.names = Names()
        self.files = {}
        self.b2_to_pid = {b2: pid for pid, b2 in self.pd.b2_zone.items()}

    # ---------------------------------------------------------------- data
    def zone(self, name):
        name = name if name.startswith('MAP_') else 'MAP_' + name
        return self.pd.by_name[name]

    def file(self, zone):
        n = self.pd.script_file(zone)
        if n not in self.files:
            path = next((p for p in version.sources(os.path.join(ROOT, 'src', 'field_scripts'), '.s')
                         if os.path.basename(p).startswith(f'{n:04d}_pearl_')), None)
            assert path, f'{zone["name"]}: no generated script file {n} (run pearl_story.py chapter N first)'
            self.files[n] = File(path)
        return self.files[n]

    def level(self, zone):
        import pearl_events
        return pearl_events.level_scripts(self.pd, zone)

    def var_name(self, v):
        return f'PVAR_{v:04X}'

    def flag_name(self, f):
        return f'PFLAG_{f:04X}'

    # ---------------------------------------------------------------- the interpreter
    def run(self, f, label, st, ctx):
        """Run a generated script from label with state st (dict name -> value) and ctx (the beat: pos, set, reads,
        origin, writes); returns how it ended ('end', 'halt', 'limit', 'missing <label>', 'warp <zone> <entry>')."""
        pc, stack, reg, steps = f.at.get(label), [], 1, 0
        if pc is None:
            return f'missing {label}'
        names = self.names

        def val(a):
            a = a.strip()
            if re.match(r'^-?(0x[0-9A-Fa-f]+|\d+)$', a):
                return int(a, 0)
            if a.startswith('PTRAINER_'):           # (plat-ch11: a Trainer put in a var, battled by it: the Battleground)
                return a
            return get(a)

        def get(k):
            if k in ctx['set']:
                v = ctx['set'][k]
            else:
                v = st.get(k, 0)
            if not LOCAL_VAR.match(k) and not LOCAL_FLAG.match(k) and k.startswith('P'):
                ctx['reads'].setdefault(k, (v, ctx['origin'].get(k, 'default')))
            return v

        def put(k, v):
            st[k] = v
            if not LOCAL_VAR.match(k) and not LOCAL_FLAG.match(k):
                ctx['writes'][k] = v
                ctx['origin'][k] = ctx['who']

        reserved, recent = None, collections.deque(maxlen=12)
        while True:
            steps += 1
            if steps > STEPS:
                return 'limit (a loop: lines ' + ' '.join(str(f.code[p][2]) for p in recent) + ')'
            recent.append(pc)
            if pc >= len(f.code):
                return 'fell off the file'
            op, args, line = f.code[pc]
            pc += 1
            if op in ('pl_GoTo', 'VMJump'):
                t = f.at.get(args[0])
                if t is None:
                    return f'missing {args[0]} (line {line})'
                pc = t
            elif op in ('pl_GoToIf', 'pl_CallIf', 'VMJumpIf', 'VMCallIf'):
                c = int(args[0]) if args[0].isdigit() else {'CMP_LT': 0, 'CMP_EQ': 1, 'CMP_GT': 2, 'CMP_LE': 3, 'CMP_GE': 4,
                                                             'CMP_NE': 5}.get(args[0])
                if c is not None and COND[c](reg):
                    t = f.at.get(args[1])
                    if t is None:
                        return f'missing {args[1]} (line {line})'
                    if op in ('pl_CallIf', 'VMCallIf'):
                        stack.append(pc)
                    pc = t
            elif op in ('pl_Call', 'VMCall'):
                t = f.at.get(args[0])
                if t is None:
                    return f'missing {args[0]} (line {line})'
                stack.append(pc); pc = t
            elif op in ('pl_Return', 'pl_ReturnCommonScript', 'VMReturn'):
                if not stack:
                    return 'end'
                pc = stack.pop()
            elif op in ('pl_End', 'VMHalt', 'VMEnd'):
                return f'warp {reserved}' if reserved else 'end'
            elif op == 'pl_CompareVarToValue' or op == 'WorkCmpConst':
                reg = cmp(val(args[0]), val(args[1]))
            elif op == 'pl_CompareVarToVar' or op == 'WorkCmpWork':
                reg = cmp(val(args[0]), val(args[1]))
            elif op == 'pl_CheckFlag':
                reg = cmp(1 if get(args[0]) else 0, 1)
            elif op == 'pl_CheckTrainerFlag':
                reg = cmp(1 if get('T:' + args[0]) else 0, 1)
            elif op in ('pl_SetFlag', 'FlagSet'):
                put(args[0], 1)
            elif op in ('pl_ClearFlag', 'FlagReset'):
                put(args[0], 0)
            elif op in ('pl_SetVarFromValue', 'pl_SetVarFromVar', 'WorkSetConst', 'WorkSet'):
                put(args[0], val(args[1]))
            elif op in ('pl_AddVar', 'WorkAdd'):
                put(args[0], (val(args[0]) + val(args[1])) & 0xFFFF)
            elif op in ('pl_SubVar', 'WorkSub'):
                put(args[0], (val(args[0]) - val(args[1])) & 0xFFFF)
            elif op == 'pl_RemoveObject':
                if len(args) > 1 and args[1] not in ('0', ''):
                    put(args[1], 1)
            elif op == 'pl_RemoveTalkedObject':              # (plat-ch5) an item ball taken: its flag
                if ctx.get('talked'):
                    put(ctx['talked'], 1)
            elif op == 'pl_CheckItemIsPlate':                # (plat-ch5) the macro's own test: Flame Plate 298 .. Iron Plate 313
                put(args[1], 1 if 298 <= val(args[0]) <= 313 else 0)
            elif op == 'pl_GetPlayerMapPos':
                put(args[0], ctx['pos'][0]); put(args[1], ctx['pos'][1])
            elif op == 'pl_GetPlayerGender':
                put(args[0], ctx['set'].get('gender', 0))
            elif op == 'pl_GetPartyCount':
                put(args[0], ctx['set'].get('party', PLAYER_TEAM))     # (plat-ch3: "party" n in a beat's set)
            elif op == 'pl_GetPlayerStarterSpecies':
                put(args[0], get('PVAR_STARTER') or STARTER)
            elif op in ('pl_ShowYesNoMenu', 'ListMenuShow'):
                if args:
                    put(args[0], ctx['set'].get(args[0], 0))
            elif op == 'pl_GetRandom':          # (each draw the next number: a "draw again if the same" loop ends)
                ctx['draws'] = ctx.get('draws', -1) + 1
                put(args[0], ctx['set'].get(args[0], ctx['draws'] % max(1, val(args[1]))))
            elif op == 'pl_CheckWonBattle':
                put(args[0], 1)
            elif op in ('pl_StartTrainerBattle', 'pl_StartTagBattle'):
                for t in args[(1 if op == 'pl_StartTagBattle' else 0):]:
                    if t.startswith('PVAR_') and str(st.get(t, '')).startswith('PTRAINER_'):     # (plat-ch11: by a var)
                        t = st[t]
                    if t.startswith('PTRAINER_'):
                        put('T:' + t, 1)
                        ctx['battles'].append(t)
            elif op == 'pl_SetTrainerFlag':
                put('T:' + args[0], 1)
            elif op == 'pl_ClearTrainerFlag':
                put('T:' + args[0], 0)
            elif op == 'pl_SetHiddenLocation':              # (plat-ch9: the Spring Path, the Seabreak Path)
                put(f'HIDDEN:{val(args[0])}', 1)
            elif op == 'pl_CheckHasTwoAliveMons':           # (plat-ch9: Spear Pillar's double battle; "party" n in a beat's set)
                put(args[0], 1 if ctx['set'].get('party', PLAYER_TEAM) >= 2 else 0)
            elif op == 'pl_SpearPillarSequence':            # (plat-ch9: the macro's polls, ops 1 and 6, report "over" at once)
                if val(args[0]) in (1, 6):
                    put(args[1], 1)
            elif op in ('pl_AddItem', 'ItemAdd'):
                it, n = val(args[0]), val(args[1])
                put(f'ITEM:{it}', st.get(f'ITEM:{it}', 0) + n)
                ctx['items'].append(it)
                if len(args) > 2: put(args[2], 1)
            elif op in ('pl_RemoveItem', 'ItemSub'):
                it, n = val(args[0]), val(args[1])
                have = st.get(f'ITEM:{it}', 0)
                ctx['reads'].setdefault(f'ITEM:{it}', (have, ctx['origin'].get(f'ITEM:{it}', 'default')))
                put(f'ITEM:{it}', max(0, have - n))
                if len(args) > 2: put(args[2], 1 if have >= n else 0)
            elif op in ('pl_CheckItem', 'ItemCheckAmount'):
                it, n = val(args[0]), val(args[1])
                have = st.get(f'ITEM:{it}', 0)
                ctx['reads'].setdefault(f'ITEM:{it}', (have, ctx['origin'].get(f'ITEM:{it}', 'default')))
                put(args[2], 1 if have >= n else 0)
            elif op in ('pl_CanFitItem', 'ItemCheckSpace'):
                put(args[2], 1)
            elif op == 'pl_GiveBadge':
                put(f'BADGE:{val(args[0])}', 1)
            elif op == 'pl_CheckBadgeAcquired':
                b = val(args[0])
                have = st.get(f'BADGE:{b}', 0)
                ctx['reads'].setdefault(f'BADGE:{b}', (have, ctx['origin'].get(f'BADGE:{b}', 'default')))
                put(args[1], have)
            elif op == 'pl_EnablePoketch':
                put('POKETCH', 1)
            elif op == 'pl_CheckPoketchEnabled':
                put(args[0], st.get('POKETCH', 0))
            elif op == 'pl_RegisterPoketchApp':
                put(f'APP:{val(args[0])}', 1)
            elif op == 'pl_CheckPoketchAppRegistered':
                put(args[1], st.get(f'APP:{val(args[0])}', 0))
            elif op == 'RTReserveScript':
                reserved = args[0]
            elif op == 'pl_Warp':
                reserved = f'{reserved} {args[0]}'
            elif op == 'pl_SetObjectEventPosLater' or op == 'pl_SetPosition' or op == 'pl_SetObjectEventPos':
                ctx['placed'].append((op, args, line))
            # (plat-ch3: chapter 3's commands; the beat's "set" gives "dir" the way the player faces (0-3; else the var
            # keeps its value), "fateful" the slot of an event Pokémon (default 0xFF: none), "ghost" 1 for an Old
            # Chateau ghost shown)
            elif op == 'pl_GetItemQuantity':
                it = val(args[0])
                ctx['reads'].setdefault(f'ITEM:{it}', (st.get(f'ITEM:{it}', 0), ctx['origin'].get(f'ITEM:{it}', 'default')))
                put(args[1], st.get(f'ITEM:{it}', 0))
            elif op == 'pl_GetPlayerDir' and 'dir' in ctx['set']:
                put(args[0], ctx['set']['dir'])
            elif op == 'pl_FindPartySlotWithFatefulEncounterSpecies':
                put(args[0], ctx['set'].get('fateful', 0xFF))
            elif op == 'pl_CheckShouldShowGhost':
                put(args[1], ctx['set'].get('ghost', 0))
            # (plat-ch8: a map script's SetWarpEventPos moves warp n for this visit of the zone; a "warp" beat reads it)
            elif op == 'pl_SetWarpEventPos':
                st[f'WARP:{int(args[0], 0)}'] = (val(args[1]), val(args[2]))
            # (plat-ch10: the Pokétch developer's nature question: the beat's "set" gives "nature_slot", the party slot with
            # the nature asked for, default 255: none; Black 2's game clear (pl_ClearGame) sets the game-clear flag 2400, Platinum's
            # FLAG_GAME_COMPLETED, and the script ends there: the credits, THE END, the title)
            elif op == 'pl_FindPartySlotWithNature':
                put(args[0], ctx['set'].get('nature_slot', 0xFF))
            elif op == 'pl_ClearGame':
                put('PFLAG_0964', 1)
                return 'warp (game clear: Continue at home)'
            # (plat-ch10: a scripted wild battle is won, as the trainer battles; "caught": 0 in the beat's "set" for one
            # that got away or was knocked out, default caught)
            elif op == 'pl_CheckWonWildBattle':
                put(args[0], 1)
            elif op == 'pl_CheckDidNotCapture':
                put(args[0], 0 if ctx['set'].get('caught', 1) else 1)
            # (plat-ch11: the post-game's checks. FlagGet n, var: Black 2's flag n (CheckGameCompleted: 2400) by its pearl.h
            # name; the National Pokédex as "NATDEX" (pl_SetNationalDex in a script or a start's TEST_LINES); the day of the
            # week from a beat's "set" "weekday" (0 Sunday .. 6; default 1, a weekday: no weekend battles); the Battleground's
            # draw: its first three Leaders and the first other Trainer, as the macro's own codes)
            elif op == 'FlagGet':
                put(args[1], 1 if get(self.b2_key(args[0])) else 0)
            elif op == 'pl_GetNationalDex':
                ctx['reads'].setdefault('NATDEX', (st.get('NATDEX', 0), ctx['origin'].get('NATDEX', 'default')))
                put(args[0], st.get('NATDEX', 0))
            elif op == 'pl_SetNationalDex':
                put('NATDEX', 1)
            elif op == 'RTCGetWeekDay':
                put(args[0], ctx['set'].get('weekday', 1))
            elif op == 'pl_RegiRuinsDot':                  # (the Regi ruins: the dot under the player sets its bit; all seven: the state)
                if val(args[1]) == val(args[3]) and val(args[2]) == val(args[4]):
                    put(args[0], val(args[0]) | val(args[5]))
            elif op == 'pl_RegiRuinsDotsDone':
                if val(args[0]) == val(args[1]):
                    put(args[0], val(args[2]))
            elif op == 'pl_GetLeagueVictories':            # (Hall of Fame entries: "league_wins" in a beat's set; 1 after the game clear)
                put(args[0], ctx['set'].get('league_wins', 1 if get('PFLAG_0964') else 0))
            elif op == 'pl_GetRandomBattlegroundTrainers':
                for k, c in zip(args[:4], (args[4], args[5], args[6], args[12])):
                    put(k, val(c))
            elif op in ('pl_CheckLocalDexCompleted', 'pl_CheckLocalDexCompletedOrChampion'):    # (the Sinnoh Pokédex: "localdex")
                done = ctx['set'].get('localdex', 0) or (op.endswith('Champion') and get('PFLAG_0964'))
                put(args[0], 1 if done else 0)
            # the party's legendaries and event Pokémon ("PARTY:species", "PARTY:486F" the deliveryman's fateful Regigigas): a
            # wild battle catches as plat-ch10's rule above ("caught": 0 in the beat's "set": it got away); the deliveryman's
            # gifts as pearl_story.inc gives them
            elif op == 'pl_StartWildBattle':
                if ctx['set'].get('caught', 1):
                    put(f'PARTY:{val(args[0])}', 1)
            elif op == 'pl_CheckHasAllLegendaryTitansInParty':
                put(args[0], 1 if all(get(f'PARTY:{s}') for s in (377, 378, 379)) else 0)
            elif op == 'pl_CheckPartyHasFatefulEncounterRegigigas':
                put(args[0], 1 if get('PARTY:486F') else 0)
            elif op == 'pl_DeliveryWaiting':
                put(args[0], 1 if get('PFLAG_0964') and get('PVAR_DELIVERY') < 6 else 0)
            elif op == 'pl_DeliveryCanReceive':
                put(args[0], 1 if get('PVAR_DELIVERY') not in (3, 4) or ctx['set'].get('party', PLAYER_TEAM) < 6 else 0)
            elif op == 'pl_DeliveryGive':
                g = get('PVAR_DELIVERY')
                gift = {0: 'ITEM:454', 1: 'ITEM:452', 2: 'ITEM:455', 3: 'PARTY:490', 4: 'PARTY:486F', 5: 'ITEM:467'}.get(g)
                if gift:
                    put(gift, st.get(gift, 0) + 1)
                if g == 1 and not get('PVAR_4057'):        # (plat-ch12: Oak's Letter starts Platinum's Shaymin event, as
                    put('PVAR_4057', 1)                     # pl_DeliveryGive: VAR_SHAYMIN_EVENT_STATE 0 -> 1)
                put('PVAR_DELIVERY', g + 1)
            elif self.ch12_op(op, args, val, get, put, ctx, st):     # (plat-ch12: chapter 12's commands, below)
                pass
            elif self.dw_op(op, args, val, get, put, ctx, st):       # (plat-dw-world: the Distortion World's, below)
                pass

    # ---------------------------------------------------------------- the start
    def start(self, chapter, row, part=None):
        """(state, origin, start) for a chapter's test start (part: a second start, "**Test start B**", plat-ch9)."""
        start = dict(note_start(chapter, part))
        start.update(row.get('start' if part is None else f'start_{part}', {}))
        st, origin = {}, {}
        ctx = dict(pos=(0, 0), set={}, reads={}, writes={}, origin=origin, who='the new game', battles=[], items=[],
                   placed=[])
        tw = self.file(self.zone(TWINLEAF))
        end = self.run(tw, NEWGAME, st, ctx)
        assert end == 'end', f'the new-game script: {end}'
        st['FLAG:2401'] = 1
        for i in [i for i in start.get('TEST_ITEMS', '').split(',') if i.strip()]:
            st[f'ITEM:{int(i)}'] = st.get(f'ITEM:{int(i)}', 0) + 1
            origin[f'ITEM:{int(i)}'] = 'TEST_ITEMS'
        for s in [s.strip() for s in start.get('TEST_SET', '').split(',') if s.strip()]:
            k, _, v = s.partition('=')
            k = self.b2_key(k)
            st[k] = int(v, 0) if v else 1
            origin[k] = 'TEST_SET'
        for line in [l.strip() for l in start.get('TEST_LINES', '').split(';') if l.strip()]:
            op, _, rest = line.partition(' ')
            a = [x.strip() for x in rest.split(',')]
            k = None
            if op == 'pl_GiveBadge':
                k, v = f'BADGE:{int(a[0])}', 1
            elif op in ('FlagSet', 'pl_SetFlag', 'FlagReset', 'pl_ClearFlag'):
                k, v = self.b2_key(a[0]), int(op in ('FlagSet', 'pl_SetFlag'))
            elif op in ('WorkSetConst', 'pl_SetVarFromValue'):
                k, v = self.b2_key(a[0]), int(a[1], 0)
            elif op in ('ItemAdd', 'pl_AddItem'):
                k = f'ITEM:{int(a[0], 0)}'; v = st.get(k, 0) + int(a[1], 0)
            elif op == 'pl_EnablePoketch':                  # (plat-ch3: the Pokétch and its apps in a start)
                k, v = 'POKETCH', 1
            elif op == 'pl_RegisterPoketchApp':
                k, v = f'APP:{int(a[0], 0)}', 1
            elif op == 'pl_SetTrainerFlag':                 # (plat-ch9: a Trainer beaten in an earlier chapter)
                k, v = f'T:{a[0]}', 1
            elif op == 'pl_SetHiddenLocation':              # (plat-ch9: the Spring Path the Distortion World opens)
                k, v = f'HIDDEN:{int(a[0], 0)}', 1
            elif op == 'pl_SetNationalDex':                 # (plat-ch11: chapter 12's start has it)
                k, v = 'NATDEX', 1
            if k:
                st[k] = v; origin[k] = 'TEST_LINES'
        return st, origin, start

    def b2_key(self, k):
        """A TEST_SET name as the state's key: PFLAG_/PVAR_ names stay; a number is a Black 2 flag or work: the
        pearl.h name with that id when there is one (so the scripts' reads find it), else FLAG:n / WORK:n."""
        if not k.isdigit() and not k.startswith('0x'):
            return k
        n = int(k, 0)
        hits = [name for name, b in self.names.b2.items() if b == n and (name.startswith('PVAR') == (n >= 0x4000))]
        return hits[0] if hits else (f'WORK:{n:#x}' if n >= 0x4000 else f'FLAG:{n}')

    def check_start_tile(self, start):
        """Findings about TEST_START: the zone owning the tile, the walkable tile, the assembled file."""
        out = []
        if not start.get('TEST_START'):
            return out
        b2, x, z = (int(v) for v in start['TEST_START'].split(','))
        pid = self.b2_to_pid.get(b2)
        if pid is None:
            return [f'TEST_START: zone {b2} is not an installed Sinnoh zone']
        zone = self.pd.zones[pid]
        if zone['matrix'] == 0:
            m = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', '000.json')))
            owner = m['headers'][z // 32][x // 32] if 0 <= z // 32 < m['height'] and 0 <= x // 32 < m['width'] else None
            if owner != pid:
                out.append(f'TEST_START: tile ({x}, {z}) is in {self.pd.zones[owner]["name"] if owner is not None else "no zone"}, '
                           f'not {zone["name"]}')
        import warp_check
        w = warp_check.Warps('offline')
        if not w.walkable(b2, x, z):
            out.append(f'TEST_START: tile ({x}, {z}) of {zone["name"]} is not walkable ({w.tile(b2, x, z)})')
        out += self.assemble_start(start, b2, zone)
        return out

    def assemble_start(self, start, b2, zone):
        """test_story_start.apply on a stand-in of the files it reads (the zone headers, the world matrix, the script
        archive), so its own checks and its assembly run as in a build; then b2_script_check on the result."""
        import test_story_start as tss, b2_script_check
        world = json.load(open(version.data_path('sinnoh_world.json')))
        zone_of = {int(k): v['b2_zone'] for k, v in world['zones'].items()}
        m = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', '000.json')))
        w, h = m['width'], m['height']
        cells = [zone_of.get(m['headers'][zz][xx], 0xFFFFFFFF) for zz in range(h) for xx in range(w)]
        matrix = struct.pack('<HHHH', 1, 0, w, h) + struct.pack(f'<{w * h}I', *([0] * (w * h))) + struct.pack(f'<{w * h}I', *cells)
        headers = collections.defaultdict(lambda: {'matrix': 1, 'scripts': 0})
        for pid, bz in self.pd.b2_zone.items():
            z = self.pd.zones[pid]
            headers[bz] = {'matrix': 0 if z['matrix'] == 0 else 1, 'scripts': self.pd.script_file(z)}
        saved = {}
        loads = {9: [matrix], 56: [b''] * (tss.TWINLEAF + 1)}
        env = {k: os.environ.get(k) for k in ('TEST_START', 'TEST_SET', 'TEST_ITEMS', 'TEST_LINES', 'TEST_TEAM')}
        old = (tss.zoneheaders.load, tss.narcio.load, tss.narcio.save)
        try:
            os.environ.update({k: v for k, v in start.items() if k.startswith('TEST_')})
            os.environ.setdefault('TEST_TEAM', '1')
            tss.zoneheaders.load = lambda files: (headers, None)
            tss.narcio.load = lambda files, n: list(loads[n])
            tss.narcio.save = lambda files, n, e: saved.__setitem__(n, e)
            msg = tss.apply('offline')
        except SystemExit as e:
            return [str(e) if str(e).startswith('TEST_START') else f'TEST_START: {e}']
        except Exception as e:                      # noqa: BLE001
            return [f'TEST_START: test_story_start failed: {type(e).__name__}: {e}']
        finally:
            tss.zoneheaders.load, tss.narcio.load, tss.narcio.save = old
            for k, v in env.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        code = saved[56][tss.TWINLEAF]
        probs = b2_script_check.check(code, {})
        print(f'  start: {msg}; the assembled file: {len(b2_script_check.entries(code))} scripts, '
              f'{len(probs)} problems')
        return [f'TEST_START: assembled Twinleaf file: {p}' for p in probs]

    # ---------------------------------------------------------------- beats
    def condition(self, zone, beat):
        """(kind, description, test(st) -> bool, needs [names], tiles)."""
        ev = self.pd.events(zone)
        if 'trigger' in beat:
            n = beat['trigger']
            cs = [c for c in ev['coord_events'] if c['script'] == n]
            assert cs, f'{zone["name"]}: no step trigger runs script {n}'
            c = cs[0]
            k = self.var_name(c['var'])
            tiles = [(c['x'] + i, c['z'] + j) for j in range(c['length']) for i in range(c['width'])]
            return (f'trigger {n} at ({c["x"]}, {c["z"]}) {c["width"]}x{c["length"]}', f'{k} == {c["value"]}',
                    lambda st: st.get(k, 0) == c['value'], [k], tiles)
        if 'frame' in beat:
            n = beat['frame']
            _, tables = self.level(zone)
            rows = [(v, val) for t in tables for v, val, s in t if s == n]
            assert rows, f'{zone["name"]}: no frame-table row runs script {n}'
            v, value = rows[0]
            k = self.var_name(v)
            return f'frame {n}', f'{k} == {value}', lambda st: st.get(k, 0) == value, [k], []
        if 'dw' in beat or ('talk' in beat and self.dw_floor(zone)):     # (plat-dw-world)
            return self.dw_condition(zone, beat)
        if 'talk' in beat:
            uid = beat['talk']
            os_ = [o for o in ev['object_events'] if o['id'] == uid]
            assert os_, f'{zone["name"]}: no person {uid}'
            o = os_[0]
            if not o['hidden_flag']:
                return f'talk {uid}', 'always there', lambda st: True, [], [(o['x'], o['z'] + 1)]
            k = self.flag_name(o['hidden_flag'])
            return (f'talk {uid}', f'{k} clear', lambda st: not st.get(k, 0), [k], [(o['x'], o['z'] + 1)])
        if 'warp' in beat:                                  # (plat-ch8)
            return self.warp_condition(zone, beat)
        return f'script {beat["script"]}', 'no condition', lambda st: True, [], []

    def script_of(self, zone, beat):
        if 'talk' in beat and 'script' not in beat:
            o = next(o for o in self.pd.events(zone)['object_events'] if o['id'] == beat['talk'])
            return o['script']
        for k in ('trigger', 'frame', 'script'):
            if k in beat:
                return beat[k]

    # ---- plat-ch5 (2026-11-07): a person's global script (an item ball: 7000-7326, file 1240, pearl_items.py) ----------
    ITEM_BALLS, ITEM_BALL_FILE = range(7000, 7327), '1240_global_item_balls.s'

    def script_file(self, zone, n):
        """(file, label) of script n of a zone: its own file's entry n, or an item ball's global script (Ball_k)."""
        if n in self.ITEM_BALLS:
            if self.ITEM_BALL_FILE not in self.files:
                path = next(p for p in version.sources(os.path.join(ROOT, 'src', 'field_scripts'), '.s')
                            if os.path.basename(p) == self.ITEM_BALL_FILE)
                self.files[self.ITEM_BALL_FILE] = File(path)
            f = self.files[self.ITEM_BALL_FILE]
            return f, f.entry(n - self.ITEM_BALLS.start + 1)
        f = self.file(zone)
        if n > len(f.entries) and f'PearlProxy_{n}' in f.at:   # (plat-ch11: a global script run by the zone's events, as the
            return f, f'PearlProxy_{n}'                         # deliveryman's 10201: the file's proxy for it)
        return f, f.entry(n)

    def talked_flag(self, zone, beat):
        """The hide flag of the person a talk beat talks to (pl_RemoveTalkedObject sets it), as PFLAG_xxxx."""
        if 'talk' not in beat:
            return None
        o = next((o for o in self.pd.events(zone)['object_events'] if o['id'] == beat['talk']), None)
        return self.flag_name(o['hidden_flag']) if o and o['hidden_flag'] else None
    # ---- end plat-ch5 ---------------------------------------------------------------------------------------------------

    # ---- plat-ch8 (2026-11-07): warp beats. The lakes switch their stacked warps (Valor Lakefront, Verity Lakefront, Acuity
    # Lakefront, Valor Cavern: two warps on one tile, a map script moves one away with SetWarpEventPos by a story flag; only the
    # first warp on a tile fires). A beat {"zone", "warp": [x, z], "to": ZONE} checks, after the zone's map scripts, that the
    # first warp still on that tile leads to ZONE ("expect": "off": that it doesn't); its "must" is checked too. --------------
    def warp_condition(self, zone, beat):
        x, z = beat['warp']
        to = self.zone(beat['to'])
        ws = self.pd.events(zone)['warp_events']

        def lead(st):
            for i, w in enumerate(ws):
                if tuple(st.get(f'WARP:{i}', (w['x'], w['z']))) == (x, z):
                    return w['dest_header_id']
            return None
        return (f'warp ({x}, {z})', f'the first warp there leads to {to["name"][4:]}', lambda st: lead(st) == to['id'],
                beat.get('needs', []), [(x, z)])

    def warp_must(self, i, zone, kind, beat, st):
        out = []
        for m in beat.get('must', []):
            k, _, v = m.partition('=')
            bad = bool(st.get(k[1:], 0)) if k.startswith('!') else ((st.get(k, 0) != int(v, 0)) if v else not st.get(k, 0))
            if bad:
                out.append(f'beat {i} ({zone["name"][4:]} {kind}): should leave {m}; it leaves '
                           f'{self.names.label(k.lstrip("!"))} = {st.get(k.lstrip("!"), 0)}')
        return out
    # ---- end plat-ch8 ---------------------------------------------------------------------------------------------------

    def map_scripts(self, zone, st, origin, who):
        """The zone's on-transition and on-load scripts (Platinum's init types 2 and 4), with map-local state cleared."""
        for k in [k for k in st if LOCAL_FLAG.match(k) or LOCAL_VAR.match(k) or k.startswith(('WARP:', 'DWOBJ:'))]:   # (plat-ch8: WARP; plat-dw-world: DWOBJ)
            del st[k]
        f = self.file(zone)
        entries, _ = self.level(zone)
        for t, s in sorted(entries, key=lambda e: {2: 0, 4: 1, 3: 2}.get(e[0], 3)):
            if t in (2, 4) and 0 < s <= len(f.entries):
                ctx = dict(pos=(0, 0), set={}, reads={}, writes={}, origin=origin, who=who, battles=[], items=[], placed=[])
                self.run(f, f.entry(s), st, ctx)

    def chapter(self, n, row, trace, compare_next):
        st, origin, start = self.start(n, row)
        findings = self.check_start_tile(start)
        print(f'Chapter {n}: start {start.get("TEST_START", "a new game")}; {len(row["beats"])} beats')
        for f in findings:
            print(f'  ! {f}')
        last_zone, later_sets = None, collections.defaultdict(list)
        beats = row['beats']
        results, notes, own_end = [], [], None
        for i, beat in enumerate(beats, 1):
            if own_end is None and beat.get('chapter', n) != n:
                own_end = (dict(st), dict(origin))      # (the chapter's own end: before another chapter's beats here)
            if 'restart' in beat:                       # (plat-ch9) a second test start: the story goes on there (chapter
                st, origin, start = self.start(n, row, beat['restart'])     # 9: after step 7's Distortion World)
                print(f'{i:4d}. test start {beat["restart"]}: {start.get("TEST_START")}: {beat.get("what", "")}')
                for f in self.check_start_tile(start):
                    findings.append(f'start {beat["restart"]}: {f}')
                    print(f'  ! {f}')
                last_zone = None
                results.append(None)
                continue
            zone = self.zone(beat['zone'])
            who = f'beat {i}'
            if zone['id'] != last_zone:
                self.map_scripts(zone, st, origin, f'{who} (zone scripts)')
                last_zone = zone['id']
            kind, need, test, needs, tiles = self.condition(zone, beat)
            holds = test(st)
            want = beat.get('expect', 'on') == 'on'
            label = f'{i:2d}. {zone["name"][4:]}: {kind}: {beat.get("what", "")}'
            if holds != want:
                why = ', '.join(f'{self.names.label(k)} = {st.get(k, 0)} ({origin.get(k, "default")})' for k in needs)
                findings.append(f'beat {i} ({zone["name"][4:]} {kind}): {"needs" if want else "should not play:"} {need}; now {why}')
                print(f'  ! {label}: {"needs" if want else "should be off:"} {need}; now {why}')
                results.append(None)
                continue
            if not want:
                print(f'  ok {label}: off ({need} does not hold)')
                results.append(None)
                continue
            if 'warp' in beat:                              # (plat-ch8) a warp beat runs nothing: only its "must"
                findings += self.warp_must(i, zone, kind, beat, st)
                print(f'  ok {label}: {need}')
                results.append(None)
                continue
            pos = tuple(beat.get('at', tiles[0] if tiles else (0, 0)))
            ctx = dict(pos=pos, set=dict(beat.get('set', {})), reads={}, writes={}, origin=origin, who=who, battles=[],
                       items=[], placed=[], talked=self.talked_flag(zone, beat))
            if self.dw_floor(zone):                         # (plat-dw-world) the floor's offset: Platinum's world tiles
                ctx['dw_offset'] = tuple(self.dw_floor(zone)['offset'])
            for k, v in beat.get('dw_sets', {}).items():    # (plat-dw-world) what the engine's C sets first (the boulders)
                st[k] = v; ctx['writes'][k] = v; origin[k] = f'{who} (the engine)'
            if 'dw' in beat:                                # (plat-dw-world) overlay 9's commands at a tile
                end = self.dw_run(zone, beat, st, ctx)
                if end not in ('end',) and not end.startswith('warp'):
                    findings.append(f'beat {i} ({zone["name"][4:]} {kind}): the event ends with "{end}"')
                if not beat.get('repeats') and test(st):
                    findings.append(f'beat {i} ({zone["name"][4:]} {kind}): {need} still holds after it: the event runs again')
                findings += self.warp_must(i, zone, kind, beat, st)
                sets = {k: v for k, v in ctx['writes'].items() if not k.startswith('ITEM:')}
                print(f'  ok {label}: {need}; ends {end}; sets {len(sets)}')
                results.append(ctx)
                continue
            f, entry = self.script_file(zone, self.script_of(zone, beat))      # (plat-ch5: an item ball's global script)
            end = self.run(f, entry, st, ctx)
            if end not in ('end',) and not end.startswith('warp'):
                findings.append(f'beat {i} ({zone["name"][4:]} {kind}): the script ends with "{end}"')
            # (plat-ch10: a scene on a map-local var that ends by leaving the zone (a Warp, the game clear) is done: the var is
            # cleared on the way back anyway, and Platinum sets none (the League's Cynthia, corridor and Hall of Fame scenes))
            left = end.startswith('warp') and needs and all(LOCAL_VAR.match(k) for k in needs)
            if ('trigger' in beat or 'frame' in beat) and not beat.get('repeats') and not left and test(st):
                findings.append(f'beat {i} ({zone["name"][4:]} {kind}): {need} still holds after it: the scene plays again')
            for m in beat.get('must', []):
                k, _, v = m.partition('=')
                if k.startswith('!'):                       # (plat-ch5) "!NAME": must stay clear (a way the story doesn't take)
                    if st.get(k[1:], 0):
                        findings.append(f'beat {i} ({zone["name"][4:]} {kind}): should leave {k[1:]} clear; it leaves '
                                        f'{self.names.label(k[1:])} = {st.get(k[1:], 0)}')
                    continue
                if (st.get(k, 0) != int(v, 0)) if v else not st.get(k, 0):
                    findings.append(f'beat {i} ({zone["name"][4:]} {kind}): should leave {m}; it leaves '
                                    f'{self.names.label(k)} = {st.get(k, 0)}')
            sets = {k: v for k, v in ctx['writes'].items() if not k.startswith('ITEM:')}
            print(f'  ok {label}: {need}; ends {end}; sets {len(sets)}'
                  + (f'; battles {", ".join(self.names.label(t) for t in ctx["battles"])}' if ctx['battles'] else '')
                  + (f'; items {ctx["items"]}' if ctx['items'] else ''))
            if trace:
                for k, (v, o) in sorted(ctx['reads'].items()):
                    print(f'       reads {self.names.label(k)} = {v} ({o})')
                for k, v in sorted(sets.items()):
                    print(f'       sets  {self.names.label(k)} = {v}')
            results.append(ctx)
        # read before set: a read whose value was the default while a later beat sets it
        for i, ctx in enumerate(results, 1):
            if ctx is None:
                continue
            for k, (v, o) in ctx['reads'].items():
                if o != 'default':
                    continue
                setter = next((j for j, c in enumerate(results[i:], i + 1) if c and k in c['writes']), None)
                if setter:
                    notes.append(f'beat {i} reads {self.names.label(k)} = {v} before beat {setter} sets it')
        if compare_next:
            findings += self.compare_next(n, *(own_end or (st, origin)))
        self.end_state = dict((own_end or (st, origin))[0])        # (plat-ch9: --end)
        for t in notes:
            print(f'  note: {t}')
        print(f'  end state: {sum(1 for k in st if k.startswith("PFLAG") and st[k])} flags set, '
              f'{sum(1 for k in st if k.startswith("PVAR") and st[k])} vars non-zero, '
              f'badges {sorted(int(k[6:]) for k in st if k.startswith("BADGE:") and st[k])}')
        for f in findings:
            print(f'  FINDING: {f}')
        return findings

    def compare_next(self, n, st, origin):
        if n == DW_ROW:                                     # (plat-dw-world: the Distortion World ends at chapter 9's start B)
            return self.compare_start(n, st, origin, 9, 'B')
        return self.compare_start(n, st, origin, n + 1)

    def compare_start(self, n, st, origin, m, part=None):
        """The end state against chapter n+1's test start (run as this tool runs a start): a story flag or var its start
        has that this end lacks is a finding (the start assumes what the story doesn't do); what this end has and its
        start lacks is printed as a note (the start may miss it)."""
        if not note_start(m, part).get('TEST_SET'):
            return []
        nst, _, _ = self.start(m, {}, part)
        story = lambda k: (k.startswith(('PFLAG', 'PVAR', 'BADGE:', 'ITEM:', 'T:', 'POKETCH', 'APP:', 'HIDDEN:', 'NATDEX')) and not LOCAL_FLAG.match(k)   # (plat-ch11: NATDEX)
                           and not LOCAL_VAR.match(k) and k != 'PVAR_STARTER')
        out = []
        for k in sorted(set(nst) | set(st)):
            if not story(k):
                continue
            a, b = st.get(k, 0), nst.get(k, 0)
            if a == b:
                continue
            if k.startswith('ITEM:') and a and b:           # (counts: a start gives one of each)
                continue
            if b and not a or k.startswith('PVAR') and b > a:
                out.append(f'chapter {m}{part or ""} starts with {self.names.label(k)} = {b}; chapter {n} ends with {a}')
            else:
                print(f'  note: chapter {n} ends with {self.names.label(k)} = {a} ({origin.get(k, "default")}); '
                      f'chapter {m}{part or ""}\'s start has {b}')
        return out


    # ---- plat-ch9 (2026-11-07): an end state written as a test start --------------------------------------------------
    STORY_KEYS = ('PFLAG', 'PVAR', 'BADGE:', 'ITEM:', 'T:', 'POKETCH', 'APP:', 'FLAG:', 'WORK:', 'HIDDEN:')

    def story_key(self, k):
        """A key a test start carries: story flags and vars, items, badges, beaten Trainers, the Pokétch, hidden places; not
        map-local ones, nor the people's sprite vars 0x4020-0x402F (their zones' scripts set them)."""
        return (k.startswith(self.STORY_KEYS) and not LOCAL_FLAG.match(k) and not LOCAL_VAR.match(k)
                and not re.match(r'^PVAR_402[0-9A-F]$', k) and k != 'PVAR_STARTER')

    def write_start(self, st):
        """{TEST_ITEMS, TEST_SET, TEST_LINES} that give state st over the new game's own (FlagReset for the flags the new
        game sets and st clears; pl_SetTrainerFlag for beaten Trainers; badges, the Pokétch, hidden places as lines)."""
        base, _, _ = self.start(0, {})
        flags, vars_, nums, items, resets, trainers, badges, poke, hidden = [], [], [], [], [], [], [], [], []
        for k in sorted(set(st) | set(base)):
            if not self.story_key(k):
                continue
            a, b = st.get(k, 0), base.get(k, 0)
            if a == b:
                continue
            if k.startswith('PFLAG'):
                (flags if a else resets).append(k)
            elif k.startswith('PVAR'):
                vars_.append(f'{k}={a}')
            elif k.startswith('FLAG:') and a:
                nums.append(int(k[5:]))
            elif k.startswith('ITEM:') and a > 0 and not b:
                items += [int(k[5:])] * a
            elif k.startswith('BADGE:') and a:
                badges.append(f'pl_GiveBadge {k[6:]}')
            elif k == 'POKETCH' and a:
                poke.insert(0, 'pl_EnablePoketch')
            elif k.startswith('APP:') and a:
                poke.append(f'pl_RegisterPoketchApp {k[4:]}')
            elif k.startswith('T:') and a:
                trainers.append(f'pl_SetTrainerFlag {k[2:]}')
            elif k.startswith('HIDDEN:') and a:
                hidden.append(f'pl_SetHiddenLocation {k[7:]}')
        test_set = [f'PVAR_STARTER={st.get("PVAR_STARTER") or STARTER}'] + vars_ + flags + [str(n) for n in sorted(nums)]
        natdex = ['pl_SetNationalDex'] if st.get('NATDEX') else []   # (plat-starts: the National Pokédex, as start() reads it)
        lines = sorted(badges) + poke + hidden + natdex + [f'FlagReset {k}' for k in resets] + trainers
        return dict(TEST_ITEMS=','.join(map(str, sorted(items))), TEST_SET=','.join(test_set), TEST_LINES=';'.join(lines))
    # ---- end plat-ch9 ---------------------------------------------------------------------------------------------------

    # ---- plat-ch12 (2026-11-07): chapter 12's commands (the interpreter's last rows: an op an earlier row reads stays
    # theirs; Black 2's own party commands answer only when the state or the beat knows, else they leave the var as before,
    # so other chapters' rows read what they read). The deliveryman's events: pl_CheckDistributionEvent n = 1 once
    # PVAR_DELIVERY is past the gift's place (pearl_story.inc: 0 Member Card, 1 Oak's Letter, 2 Azure Flute; event 3, the
    # Secret Key, is gift 5). StartFatefulEncounter catches "PARTY:<species>" and "PARTY:<species>F" (fateful) unless the
    # beat's set has "caught": 0. The time of day from a beat's set "time" (Platinum's 0 morning .. 3 night, 4 late night).
    # One party Rotom ("PARTY:479", the Old Chateau's), its form "ROTOM_FORM" (PokePartyChangeRotomForme), in the slot a set's
    # "rotom_slot" gives (default 5); Rotom forms elsewhere in the save from a set "forms" (form numbers). A set's "moves"
    # (PokePartyGetMoveCount), "has_move" (PokePartyHasMove), "move_slot" (the forget-a-move screen) and "menu" (a list menu's
    # answer).
    def ch12_op(self, op, args, val, get, put, ctx, st):
        s = ctx['set']
        rotom_slot = s.get('rotom_slot', 5)
        slot_of = lambda sp: rotom_slot if sp == 479 else 0
        if op == 'pl_CheckDistributionEvent':
            n = val(args[0])
            put(args[1], 1 if get('PVAR_DELIVERY') > (5 if n == 3 else n) else 0)
        elif op == 'pl_StartFatefulEncounter':
            if s.get('caught', 1):
                put(f'PARTY:{val(args[0])}', 1)
                put(f'PARTY:{val(args[0])}F', 1)
        elif op == 'pl_GetTimeOfDay' and 'time' in s:
            put(args[0], s['time'])
        elif op == 'PokePartyFindBySpecies' and f'PARTY:{val(args[0])}' in st:     # (CheckPartyHasSpecies: species, found, slot)
            have = get(f'PARTY:{val(args[0])}')
            put(args[1], 1 if have else 0)
            if have and not args[2].startswith('PL_'):
                put(args[2], slot_of(val(args[0])))
        elif op == 'pl_FindPartySlotWithSpecies':
            put(args[0], slot_of(val(args[1])) if get(f'PARTY:{val(args[1])}') else 255)
        elif op == 'PokePartyGetCountBySpecies' and f'PARTY:{val(args[0])}' in st:
            put(args[1], 1 if get(f'PARTY:{val(args[0])}') else 0)
        elif op == 'pl_GetPartyRotomCountAndFirst':
            inform = get('PARTY:479') and get('ROTOM_FORM')
            put(args[0], 1 if inform else 0)
            put(args[1], rotom_slot if inform else 255)
        elif op == 'pl_GetRotomFormsInSave':
            forms = set(s.get('forms', [])) | ({get('ROTOM_FORM')} if get('PARTY:479') else set())
            for i, a in enumerate(args[:5]):
                put(a, 1 if i + 1 in forms else 0)
        elif op == 'PokePartyChangeRotomForme':
            put('ROTOM_FORM', val(args[2]))
        elif op == 'PokePartyGetForme' and 'PARTY:479' in st and val(args[1]) == rotom_slot:
            put(args[0], get('ROTOM_FORM'))
        elif op == 'PokePartyGetMoveCount' and 'moves' in s:
            put(args[0], s['moves'])
        elif op == 'PokePartyHasMove' and 'has_move' in s:
            put(args[0], s['has_move'])
        elif op == 'pl_GetSummarySelectedMoveSlot' and 'move_slot' in s:
            put(args[0], s['move_slot'])
        elif op == 'ListMenu_AnchorTopRight' and 'menu' in s:
            put(args[-1], s['menu'])
        else:
            return False
        return True
    # ---- end plat-ch12 --------------------------------------------------------------------------------------------------


# ---- plat-dw-world (2026-11-07): the Distortion World (step 7), row "9b" of story_flow.json: from chapter 9's state at its
# restart (the distorted pillar's YES) to chapter 9's start B (Sendoff Spring). Its story runs in overlay 9's C as much as in
# its scripts (notes/PLATINUM_DW.md "The world"; data/platinum/distortion_world_story.json): a beat {"zone", "dw": [x, y, z]}
# is overlay 9's event at that tile of the floor's own tiles (HandleEventAt): its flag condition (Platinum's CheckFlagCondition:
# the progress var PVAR_4055, the boulder puzzle's flags "DWPUZZLE:n", B4F's shadows PFLAG_09AE / 09AF, Cyrus's appearance
# PVAR_405B) must hold, then its commands run (a zone script, the progress, the flags; the rest is the engine's drawing). A talk
# beat there needs the person's condition (CheckFlagConditionForObjectEvent: one of its templates' conditions, or added by a
# script: "DWOBJ:uid", map-local). The macros: pl_DWGetPlayer3DPos gives the beat's tile plus the floor's offset (Platinum's world
# tiles; the height "y" from the beat's set, else the floor's ground, 1); CallWildBattleEx catches "PARTY:<species>" as the other
# wild battles; pl_GetBattleResult is 4 (caught), or the set's "battle_result"; the rest draw.
DW_ROW = '9b'
DW_PROGRESS, DW_CYRUS, DW_SHADOWS = 'PVAR_4055', 'PVAR_405B', ('PFLAG_09AE', 'PFLAG_09AF')
_DW = None


def dw_world():
    global _DW
    if _DW is None:
        _DW = json.load(open(os.path.join(ROOT, 'data', 'platinum', 'distortion_world_story.json')))
    return _DW


def dw_cond(cond, value, st):
    """Platinum's CheckFlagCondition on the flow's state."""
    g = lambda k: st.get(k, 0)
    return {'none': lambda: True, 'boulder_puzzle_false': lambda: not g(f'DWPUZZLE:{value}'),
            'boulder_puzzle_true': lambda: bool(g(f'DWPUZZLE:{value}')), 'progress_eq': lambda: g(DW_PROGRESS) == value,
            'progress_leq': lambda: g(DW_PROGRESS) <= value, 'progress_geq': lambda: g(DW_PROGRESS) >= value,
            'manual_add_only': lambda: False, 'giratina_shadow': lambda: not g(DW_SHADOWS[value]),
            'cyrus_appearance': lambda: g(DW_CYRUS) == value}[cond]()


def _dw_floor(self, zone):
    return next((f for f in dw_world()['floors'].values() if f['map'] == zone['id']), None)


def _dw_condition(self, zone, beat):
    f = self.dw_floor(zone)
    if 'dw' in beat:
        x, y, z = beat['dw']
        evs = [e for e in f['events'] if (e['x_local'], e['y_local'], e['z_local']) == (x, y, z)]
        assert evs, f'{zone["name"]}: no overlay 9 event at {(x, y, z)}'
        need = ' or '.join(f'{e["cond"]} {e["cond_value"]}' for e in evs)
        return (f'event at ({x}, {y}, {z})', need, lambda st: any(dw_cond(e['cond'], e['cond_value'], st) for e in evs),
                [DW_PROGRESS], [(x, z)])
    uid = beat['talk']
    objs = [o for o in f['objects'] if o['local_id'] == uid]
    assert objs, f'{zone["name"]}: no person {uid} in overlay 9\'s table'
    need = ' or '.join(f'{o["cond"]} {o["cond_value"]}' for o in objs) + f' or DWOBJ:{uid}'
    test = lambda st: st.get(f'DWOBJ:{uid}', 0) == 1 or (st.get(f'DWOBJ:{uid}', 0) != -1 and
                                                         any(dw_cond(o['cond'], o['cond_value'], st) for o in objs))
    return f'talk {uid}', need, test, [DW_PROGRESS], [(objs[0]['x_local'], objs[0]['z_local'] + 1)]


def _dw_run(self, zone, beat, st, ctx):
    """An overlay 9 event's commands: the first event at the tile whose condition holds (HandleEventAt)."""
    f = self.dw_floor(zone)
    x, y, z = beat['dw']
    e = next(e for e in f['events'] if (e['x_local'], e['y_local'], e['z_local']) == (x, y, z)
             and dw_cond(e['cond'], e['cond_value'], st))
    end = 'end'
    for c in dw_world()['commands'][e['commands']]:
        p = c['params'] or {}
        if c['cmd'] == 'start_script':
            fl, entry = self.script_file(zone, p['value'])
            end = self.run(fl, entry, st, ctx)
            if end != 'end' and not end.startswith('warp'):
                return end
        elif c['cmd'] == 'set_progress':
            st[DW_PROGRESS] = p['value']; ctx['writes'][DW_PROGRESS] = p['value']; ctx['origin'][DW_PROGRESS] = ctx['who']
        elif c['cmd'] == 'set_giratina_animation_flag':
            st[DW_SHADOWS[p['value']]] = 1; ctx['writes'][DW_SHADOWS[p['value']]] = 1
        elif c['cmd'] in ('set_puzzle_flag', 'clear_puzzle_flag'):
            st[f'DWPUZZLE:{p["value"]}'] = int(c['cmd'] == 'set_puzzle_flag')
        elif c['cmd'] == 'add_map_object' and p['map'] == zone['id']:
            st[f'DWOBJ:{p["local_id"]}'] = 1
        elif c['cmd'] == 'delete_map_object':
            st[f'DWOBJ:{p["value"]}'] = -1
        elif c['cmd'] in ('show_uxie_boulder_tuto', 'show_azelf_boulder_tuto', 'show_mesprit_boulder_tuto'):
            # (each tutorial marks itself seen: EventCmdShow*BoulderTuto_*: DIST_WORLD_PUZZLE_FLAG_*_TUTO_SEEN, 10-12)
            st[f'DWPUZZLE:{e["cond_value"]}'] = 1
    return end


def _dw_op(self, op, args, val, get, put, ctx, st):
    if op == 'pl_DWGetPlayer3DPos':
        ox, oy, oz = ctx.get('dw_offset', (0, 0, 0))
        put(args[0], ctx['pos'][0] + ox); put(args[1], ctx['set'].get('y', 1) + oy); put(args[2], ctx['pos'][1] + oz)
    elif op == 'ActorAdd':
        put(f'DWOBJ:{val(args[0])}', 1)
    elif op == 'ActorDelete':
        put(f'DWOBJ:{val(args[0])}', -1)
    elif op == 'CallWildBattleEx':
        if ctx['set'].get('caught', 1):
            put(f'PARTY:{val(args[0])}', 1)
    elif op == 'pl_GetBattleResult':
        put(args[0], ctx['set'].get('battle_result', 4 if ctx['set'].get('caught', 1) else 1))
    elif op in ('pl_DWWarp', 'pl_DWGiratinaShadow', 'pl_DWGiratinaShadowFinish', 'pl_DWResetCameraAngles'):
        pass
    else:
        return False
    return True


Flow.dw_floor, Flow.dw_condition, Flow.dw_run, Flow.dw_op = _dw_floor, _dw_condition, _dw_run, _dw_op
# ---- end plat-dw-world


def note_start(n, part=None):
    """TEST_START, TEST_ITEMS, TEST_SET, TEST_LINES of chapter n's "Test start" in notes/PLATINUM_CHAPTERS.md (part B: the
    lines after "**Test start B**" up to the next bold line, plat-ch9)."""
    text = open(CHAPTERS_NOTE).read()
    m = re.search(rf'^## Chapter {n}\b.*?(?=^## )', text, re.M | re.S)   # (plat-starts: \b, so "## Chapter 90 and skip" too)
    out = {}
    if m:
        sec = m.group(0)
        if part is not None:
            b = re.search(rf'^\*\*Test start {part}\*\*.*?(?=^\*\*|\Z)', sec, re.M | re.S)
            sec = b.group(0) if b else ''
        for k, v in re.findall(r'`?(TEST_[A-Z]+)="?([^"`]*)"?`?', sec):
            out.setdefault(k, v)
    return out


# ---- plat-starts (2026-11-07): every test start in test order, as the env lines for patches/test_story_start.py ---------
START_ORDER = [(n, None) for n in range(2, 10)] + [(9, 'B')] + [(n, None) for n in (10, 11, 12)] + [(12, 'B')]


def print_starts():
    """notes/PLATINUM_CHAPTERS.md "How to test the whole story": each chapter's test start from its section, one env line."""
    print('chapter 1: a plain new game (no TEST_ variables)')
    for n, part in START_ORDER:
        s = note_start(n, part)
        env = [f'TEST_START={s["TEST_START"]}', 'TEST_TEAM=1'] + [f'{k}="{s[k]}"' for k in ('TEST_ITEMS', 'TEST_SET', 'TEST_LINES')
                                                                  if s.get(k)]
        print(f'chapter {n}{" start " + part if part else ""}:\n    ' + ' '.join(env))
    s = note_start(90)                                  # (outside the chain: every Pokémon Center 1F)
    if s.get('TEST_START'):
        print('chapter 90 (its own start):\n    ' + ' '.join([f'TEST_START={s["TEST_START"]}', 'TEST_TEAM=1'] + [
            f'{k}="{s[k]}"' for k in ('TEST_ITEMS', 'TEST_SET', 'TEST_LINES') if s.get(k)]))
# ---- end plat-starts ------------------------------------------------------------------------------------------------
def row_key(k):
    """(plat-dw-world) the rows in story order: "9b" (the Distortion World, step 7) after 9."""
    m = re.match(r'(\d+)(.*)', k)
    return (int(m.group(1)), m.group(2))


def main(argv):
    if '--starts' in argv:                              # (plat-starts)
        print_starts()
        return 0
    rows = {k: v for k, v in json.load(open(FLOW)).items() if not k.startswith('_')}
    chapters = [a for a in argv if not a.startswith('--')] or sorted(rows, key=row_key)
    fl = Flow()
    found = []
    for n in chapters:
        found += fl.chapter(int(n) if n.isdigit() else n, rows[n], '--trace' in argv, '--next' in argv)
        if '--end' in argv:                             # (plat-ch9)
            for k, v in fl.write_start(fl.end_state).items():
                print(f'  end as a start: `{k}="{v}"`')
    print(f'{len(found)} findings')
    return 1 if found else 0


if __name__ == '__main__':
    assert version.PLATINUM, 'PEARL_VERSION=platinum'
    sys.exit(main(sys.argv[1:]))
