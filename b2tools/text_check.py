"""Platinum's text in Black 2's windows, checked offline (the dialogue step, notes/PORT_AUDIT.md "Step 2: dialogue").

    PEARL_VERSION=platinum python3 b2tools/text_check.py              every installed zone and the system text
    PEARL_VERSION=platinum python3 b2tools/text_check.py ZONE ...     only those zones (MAP_ names or zone ids)
        --widths FILE      also write every line's widest row (zone, line, px, new?) to FILE, tab separated
        --speakers         also list the talk-script lines that may be another person's (for data/pearl_speakers.json)
        --scripts          also assemble every installed zone's script file and run b2_script_check on it
        --zones-only       only the zone text (no system text, no comparison with Pearl's build)
The Battle Frontier's and the Distortion World's zones are left out (later pieces: later_piece). Exit status 1 when a
check fails. It writes nothing but --widths and its own pokebw2 clone (work/pokebw2_mod/text_check_<tree>).

Zone text. Every installed zone is translated in-process by pearl_story (what `pearl_story.py all` writes), so each line
is known with the commands that show it and the buffers its script fills. Each line of every zone text file:
- fit: each row of a page is at most 224 px in Black 2's font 0 (b2font), the width of Black 2's own widest script
  rows (all 36,276 rows of external/pokebw2/res/text/script measure 224 px or less); a page (up to a {be00} or {be01})
  has at most 2 rows (the windows are 4 tiles, 2 rows of 16 px). A buffer counts as its longest value (budget): a
  name 7 characters, a nickname 10, the longest species, item, move, nature, place or class name, a number its
  digits, a word of a Gen 4 kind Black 2 lacks 15 letters (WIDE_KINDS). The windows themselves: the balloon and the
  plain window print 232 px from x = 8 (ov036 talkmsgwin.c ActorMsgWin_CreateCore, field_msgbg.c
  InfoSysWinPrintStr), the sign window 223 px from x = 1 (28 tiles, MsgBGPrinter_CreateBgWin), so 224 leaves Black 2's
  own margin for the arrow.
- length: at most 1,280 characters with the buffers filled (the script's message buffer, ov012 script_work.c 0x500).
- codes: every control code is one Black 2's own text uses (B2_CODES), every character is in font 0, and nothing was
  dropped on the way (gen4_text.UNCONVERTED) without a row in DROPPED; every Gen 4 code met has a row in GEN4_CODES
  (what it became, or why it can go).
- buffers: every buffer a shown line reads is filled by a command the translation kept (not a stub), on some way
  into the command that shows it (a forward dataflow over Platinum's script, as pearl_story's app_bufs: a Call's
  fall-through gets what its subroutine filled), or by data/platinum/pearl_buffer_fills.json; a stub of a feature
  Black 2 lacks is counted (KNOWN_STUBS). A common script's lines are checked against their callers only for stubs.
  Lines only scripts nothing runs can show are counted apart (entry_used).
- speakers: a line said in the balloon of a talked-to person whom the script removed before it (Black 2's
  ParentActorMsg has nobody to point at). --speakers lists the lines to review besides: talk-script lines that start
  with another person's name ("Looker: ...", "{rival}: ...") or tell what the player did ("{player} received ...").

System text (system_problems): the place names and every zone's place, the Town Map's lines, Platinum's new items and
the Griseous Orb, the Pokédex categories, as patches/sinnoh_names.py packs them (on a clone, read back); the installed
Trainers' names against the dump, their messages (field 224 px, battle 240 px: Black 2's own Trainer lines), and the
class names they show (notes where they differ from Platinum's; Pearl's build shows the same).

A problem Pearl's own build has the same (same zone, kind and line: the check run as Pearl, pearl_problems) is listed
as Pearl's and doesn't fail the check: those lines are Pearl's, left as they are.
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402
import b2font  # noqa: E402

FIT, SIGN_FIT, ROWS, MAX_CHARS = 224, 223, 2, 0x500
PB2 = os.path.join(ROOT, 'external', 'pokebw2')
# Control codes Black 2's own text uses (res/text/script and res/text/system, counted 2026-11-02) that ours may have:
# word buffers 01xx and numbers 0200-0207, layout bd00-bd05 (bd02 centre, bd03 right, bd05 x), stream be00 (scroll),
# be01 (clear), be02 (pause), colour ff00.
B2_CODES = {f'01{k:02x}' for k in range(0x00, 0x43)} | {f'02{k:02x}' for k in range(8)} | \
    {f'bd{k:02x}' for k in range(6)} | {'be00', 'be01', 'be02', 'ff00'}
# What gen4_text.b2_line may drop (UNCONVERTED) and why: the kind of a buffer Black 2 has no word kind for is given
# Black 2's 0100 (its field text reads only the buffer number: wordset.c), so nothing is lost.
DROPPED = {'kind': 'a buffer of a Gen 4 kind Black 2 lacks: kind 0100, the same buffer (the field text ignores kinds)',
           'WAIT': 'Gen 4\'s {WAIT n} calls the printer back to sync a sound (the "learned" fanfare, the move deleter\'s '
                   '"Poof"): Black 2 has no such code; pl_OpenMoveTutorMenu plays the fanfare itself (MEPlay SEQ_ME_LVUP)'}

_FONT = None


def font():
    global _FONT
    if _FONT is None:
        _FONT = b2font.load(0)
    return _FONT


def _widest(kind):
    """The widest name of a kind in Black 2's data as the build has it (pokebw2's res, Sinnoh's places)."""
    import glob
    f = font()
    if kind == 'place':                                # (the zone's own map sections: Pearl's or Platinum's)
        import gen4_text
        names = [gen4_text.to_b2(t) for t in gen4_text.bank(382)]
    elif kind == 'class':
        names = [json.load(open(p, encoding='utf-8')).get('name') or '' for p in
                 glob.glob(os.path.join(PB2, 'res', 'trainers', 'classes', '*.json'))]
        names = [n for n in names if '⒆' not in n]
        import gen4_text
        names += [gen4_text.to_b2(t) for t in gen4_text.bank(560)]
    else:
        folder = {'species': 'pokemon', 'item': 'items', 'move': 'moves', 'nature': 'natures'}[kind]
        paths = glob.glob(os.path.join(PB2, 'res', folder, '*', 'data.json')) + \
            glob.glob(os.path.join(PB2, 'res', folder, '*.json'))
        data = [json.load(open(p, encoding='utf-8')) for p in paths]
        names = [d.get('name') or '' for d in data if isinstance(d, dict)]
        names = [n for n in names if '―' not in n and '?' not in n]
    return max(f.width(n) for n in names if n)


_BUDGET = {}


def budget(tag):
    """The width a buffer of Black 2 kind `tag` (e.g. '0101') counts as."""
    if tag not in _BUDGET:
        w6 = font().advance('0')
        if tag.startswith('02'):                       # a number of (tag - 0200 + 1) digits, with its commas
            d = int(tag[2:], 16) + 1
            _BUDGET[tag] = d * w6 + (d - 1) // 3 * font().advance(',')
        else:
            kind = {'0100': 'name', '0102': 'nickname', '0101': 'species', '0105': 'place', '0107': 'move',
                    '0108': 'nature', '0109': 'item', '010e': 'class', '0112': 'pocket'}.get(tag)
            if kind == 'name':
                _BUDGET[tag] = 7 * font().width('M')    # a name has 7 characters (Black 2's name screen)
            elif kind in ('nickname', None):
                _BUDGET[tag] = 10 * font().width('M')   # a nickname has 10; any other word as long
            elif kind == 'pocket':
                _BUDGET[tag] = max(font().width(n) for n in ('Items', 'Medicine', 'TMs & HMs', 'Berries', 'Key Items',
                                                             'ITEMS', 'MEDICINE', 'BERRIES', 'KEY ITEMS', 'Free Space'))
            else:
                _BUDGET[tag] = _widest(kind)
    return _BUDGET[tag]


CODE = re.compile(r'(?<!\\)\{([0-9a-f]{4})(?::([0-9,]*))?\}')


def page_rows(text):
    """{page: [rows]}: the rows each page shows (a {be0x}\\n starts the next page with the row after the \\n)."""
    pages = collections.defaultdict(list)
    page = 0
    for part in re.split(r'(\{be0[01]\})', text):
        if re.fullmatch(r'\{be0[01]\}', part):
            page += 1
            continue
        if page and part.startswith('\\n'):
            part = part[2:]
        if not part and page:
            continue
        pages[page] += part.split('\\n')
    return pages


def row_width(r, values=None):
    """Pixels of one row in font 0, each buffer at its budget (or its known value in values: {buffer: text})."""
    f = font()
    w = 0
    for i, part in enumerate(CODE.split(r)):
        k = i % 3
        if k == 0:
            w += f.width(part.replace('\\\\', '\\').replace('\\{', '{').replace('\\}', '}'))
        elif k == 1:
            tag, args = part, CODE.split(r)[i + 1]
            if tag[:2] in ('01', '02'):
                idx = int(args.split(',')[0]) if args else 0
                w += f.width(values[idx]) if values and idx in values else budget(tag)
    return w


def filled_length(text):
    n = 0
    for i, part in enumerate(CODE.split(text)):
        k = i % 3
        if k == 0:
            n += len(part.replace('\\n', '\n').replace('\\\\', '\\').replace('\\{', '{').replace('\\}', '}'))
        elif k == 1:
            args = CODE.split(text)[i + 1]
            n += (budget(part) // 6 if part[:2] in ('01', '02') else 3 + (len(args.split(',')) if args else 0))
    return n


# Gen 4 buffer kinds Black 2 has no word kind for (gen4_text.STRVAR1_TO_B2: they become kind 0100): gifts, Pokétch apps,
# decorations, cups, easy-chat words, accessories, contest ranks, cities, ribbons, Union groups. Their words are wider
# than a name: 15 letters (90 px) each.
WIDE_KINDS = {10, 15, 24, 25, 26, 28, 31, 34, 35, 36, 37, 39, 61}
WIDE_WORD = 'M' * 15
# Gen 4 control codes and what each becomes (gen4_text.to_b2); the ones with no Black 2 equivalent say why they can go.
GEN4_CODES = {'STRVAR_1': 'a word buffer, the same number ({01xx:n}, numbers {02xx:n})',
              'COLOR': 'a colour, the same palette numbers ({ff00:n}); COLOR 100+ (remember a colour) shows nothing',
              'PAUSE': 'a pause ({be02:n})', 'CURSOR_X': 'a text x position ({bd05:n}; menus get spaces)',
              'ALN_CENTER': 'centred ({bd02})', 'ALN_RIGHT': 'right-aligned ({bd03:n})',
              'SIZE': 'none: Gen 4\'s big letters ("Thud!!"); the line shows in normal size',
              'YESNO': 'none: Gen 4\'s yes/no icon at the window\'s edge; Black 2\'s yes/no menu follows the line',
              'WAIT': 'none: a printer callback for a sound (DROPPED)'}


def gen4_codes(src):
    """Counter of the Gen 4 control codes of a line in .gmm spelling."""
    return collections.Counter(m.group(1) for m in re.finditer(r'\{([A-Z_0-9]+)[ }]', src))


def wide_buffers(src):
    """{buffer: a widest word} for a line's buffers of a Gen 4 kind Black 2 lacks (WIDE_KINDS)."""
    return {int(m.group(2)): WIDE_WORD for m in re.finditer(r'\{STRVAR_1 (\d+), (\d+)', src) if int(m.group(1)) in WIDE_KINDS}


def line_problems(text, sign=False, limit=None, rows=ROWS, values=None):
    """Problems of one Black 2 text line by itself: fit, rows, length, codes, characters."""
    out = []
    limit = limit or (SIGN_FIT if sign else FIT)
    ROWS_ = rows
    for page, rs in page_rows(text).items():
        if len(rs) > ROWS_:
            out.append(('rows', f'page {page + 1} has {len(rs)} rows'))
        for r in rs:
            w = row_width(r, values)
            if w > limit:
                out.append(('fit', f'{w} px > {limit}: {r!r}'))
    if filled_length(text) > MAX_CHARS:
        out.append(('length', f'{filled_length(text)} characters > {MAX_CHARS}'))
    for m in CODE.finditer(text):
        if m.group(1) not in B2_CODES:
            out.append(('code', f'{{{m.group(1)}}} is no code Black 2 uses'))
    plain = CODE.sub('', text).replace('\\n', '').replace('\\\\', '\\').replace('\\{', '{').replace('\\}', '}')
    for ch in sorted(set(plain)):
        if not font().has(ch):
            out.append(('char', f'{ch!r} (U+{ord(ch):04X}) is not in Black 2\'s font'))
    return out


def widest_row(text):
    return max((row_width(r) for rs in page_rows(text).values() for r in rs), default=0)


# ------------------------------------------------------------------------------------------- the zones, translated

def buffer_defs(pd, name, args):
    """The word buffers a Platinum (Gen 4) script command fills: [index]."""
    vals = [v for t, v in args]
    if name in ('BufferDaycareMonNicknames', 'GetDaycarePokemonNames'):
        return [0, 1]
    if name == 'BufferDaycareNicknameLevelGender':
        return vals[:3]
    if name in ('BufferDaycarePriceBySlot', 'BufferDaycareGainedLevelsBySlot', 'BufferPartyMonNicknameReturnSpecies'):
        return [vals[0]] if name != 'BufferPartyMonNicknameReturnSpecies' else [0]
    if name == 'BufferCustomMessageWord':
        return [vals[0]] if vals[0] < 0x4000 else []
    if name in ('BufferPartyPokemonSize', 'BufferSizeContestRecord', 'BufferPokemonRecordSize'):
        return vals[:2]
    if name in ('BufferContestantTrainerName', 'BufferContestantMonName', 'BufferContestRegistrationEntryNumber'):
        return [vals[1]]
    if args and args[0][0] == 'u8' and (name.startswith('Buffer') or name.startswith('Get') and
                                        any(w in name.lower() for w in ('name', 'article', 'plural', 'inscription'))
                                        or name in ('TryBufferAndUnlockRandomToughWord',)):
        return [vals[0]]
    return []


class Flow:
    """Which buffer fills reach each command of a FileTr (pearl_story): {address: {(buffer, (file, address, command))}}."""

    def __init__(self, tr):
        self.tr, self.d, self.pd = tr, tr.d, tr.job.pd
        self.at = {}
        self._subs = {}
        for label, start, k in tr.starts:
            self._walk(start, frozenset(), self.at)

    def _sub(self, t, depth):
        """The fills a subroutine at t may leave (up to its Returns)."""
        if t not in self._subs:
            self._subs[t] = frozenset()
            seen = {}
            rets = self._walk(t, frozenset(), seen, depth + 1)
            self._subs[t] = rets
        return self._subs[t]

    def _walk(self, start, st0, seen, depth=0):
        d, pd, tr = self.d, self.pd, self.tr
        todo, rets = [(start, st0)], frozenset()
        while todo:
            x, st = todo.pop()
            if x not in d.insns or (x in seen and st <= seen[x]):
                continue
            st = st | seen.get(x, frozenset())
            seen[x] = st
            end, op, args = d.insns[x]
            name = pd.cmd_name(op)
            nst = st
            for idx in buffer_defs(pd, name, args):
                nst = frozenset(b for b in nst if b[0] != idx) | {(idx, (tr.f, x, name))}
            if pd.table[op]['flow'] == 'return':
                rets |= st
            if name in ('Call', 'CallIf') and depth < 8:
                t = next(t for ty, t in args if ty == 'rel')
                todo.append((t, nst))
                todo.append((end, nst | self._sub(t, depth)))
                continue
            for t in tr.succ(x):
                todo.append((t, nst))
        return rets


def translate_all(pd, zones):
    """[(zone, job, text lines, uses, unconverted)] with uses = [(line, tr, address, command, (bank, n, variant))]
    and the speaker of each message: pearl_story translated with its line lookups recorded."""
    import pearl_story as ps, pearl_ids, gen4_text
    stack, uses, spk = [], collections.defaultdict(list), {}
    tr_orig, lf_orig, lt_orig, sp_orig = ps.FileTr.translate, ps.Job.line_for, ps.Job.line_text, ps.speaker

    def translate(self, a, end, op, args):
        stack.append((self, a, self.job.pd.cmd_name(op)))
        try:
            return tr_orig(self, a, end, op, args)
        finally:
            stack.pop()

    def line_for(self, bank, n, variant=None):
        k = lf_orig(self, bank, n, variant)
        if stack:
            uses[id(self)].append((k,) + stack[-1] + ((bank, n, variant),))
        return k

    def line_text(self, key, text):
        k = lt_orig(self, key, text)
        if stack:
            uses[id(self)].append((k,) + stack[-1] + (('text',) + tuple(key),))
        return k

    def speaker(tr, a, line):
        r = sp_orig(tr, a, line)
        spk[(id(tr), a)] = r
        return r
    ps.FileTr.translate, ps.Job.line_for, ps.Job.line_text, ps.speaker = translate, line_for, line_text, speaker
    ids = pearl_ids.Ids()
    out = []
    try:
        for z in zones:
            n0 = len(gen4_text.UNCONVERTED)
            src, text, job = ps.translate(pd, z, ids)
            out.append((z, job, text, uses.pop(id(job), []), gen4_text.UNCONVERTED[n0:]))
    finally:
        ps.FileTr.translate, ps.Job.line_for, ps.Job.line_text, ps.speaker = tr_orig, lf_orig, lt_orig, sp_orig
    return pd, out, spk


SKIP_PLACES = ('BATTLE_FRONTIER', 'BATTLE_FACTORY', 'BATTLE_HALL', 'BATTLE_CASTLE', 'BATTLE_ARCADE', 'BATTLE_TOWER',
               'DISTORTION_WORLD')


def later_piece(z):
    """Zones whose text comes with a later piece (the Battle Frontier, the Distortion World): left as generated."""
    names = (z['name'], z.get('pl_name') or '')
    return any(p in n for n in names for p in SKIP_PLACES)


def installed_zones(pd):
    """The zones `pearl_story.py all` writes (a Platinum zone Pearl installs with no generated file keeps its own)."""
    import pearl_story as ps
    out = [z for z in pd.zones if z['id'] in pd.b2_zone]
    if version.PLATINUM:
        world = json.load(open(os.path.join(ROOT, 'data', 'sinnoh_world.json')))
        world = set(world['zones']) | set(world['rooms']['zones'])
        mine = lambda z: os.path.exists(os.path.join(ROOT, 'src', 'field_scripts', f'{pd.script_file(z):04d}_pearl_{ps.slug(z["name"])}.s'))
        out = [z for z in out if str(z['id']) not in world or mine(z)]
    return out


def pearl_lines(z):
    """Pearl's own text file's lines for a zone, as installed in Pearl's build (None: Pearl has none)."""
    import pearl_story as ps
    import glob
    hits = glob.glob(os.path.join(ROOT, 'src', 'text', 'script', f'*_pearl_{ps.slug(z["name"])}.txt'))
    if not hits:
        return None
    return {l.split(' = ', 1)[1] for l in open(hits[0], encoding='utf-8').read().split('\n') if ' = ' in l}


def removed_before(tr, job):
    """{(id(tr), address): {local ids}} of the talked-to people a talk script removed (RemoveObject) on some way to the
    address: a balloon over that person (ParentActorMsg) has nobody to point at after it."""
    out = {}
    d, pd = tr.d, job.pd
    for label, start, k in tr.starts:
        if tr.kind_of(k) != 'talk':
            continue
        me = {o['id'] for o in job.events['object_events'] if o['script'] == k}
        todo, seen = [(start, frozenset())], {}
        while todo:
            x, st = todo.pop()
            if x not in d.insns or (x in seen and st <= seen[x]):
                continue
            st = st | seen.get(x, frozenset())
            seen[x] = st
            end, op, args = d.insns[x]
            nst = st
            if pd.cmd_name(op) == 'RemoveObject' and args and args[0][1] in me:
                nst = st | {args[0][1]}
            if st:
                out.setdefault((id(tr), x), set()).update(st)
            for t in tr.succ(x):
                todo.append((t, nst))
    return out


def decomp_objects(z):
    """{local id: (LOCALID_ name, OBJ_EVENT_GFX_ name)} of a Platinum zone's people, from pokeplatinum's events (the dump's
    order); {} for Pearl and Diamond."""
    if not version.PLATINUM or not z.get('pl_name'):
        return {}
    path = os.path.join(ROOT, 'external', 'pokeplatinum', 'res', 'field', 'events', f'events_{z["pl_name"][4:].lower()}.json')
    if not os.path.exists(path):
        return {}
    ours = json.load(open(os.path.join(version.WORLD_WORK, 'events', f'{z["events"]:03d}.json')))['object_events']
    theirs = json.load(open(path))['object_events']
    return {o['id']: (p['id'], str(p['graphics_id'])) for o, p in zip(ours, theirs) if o['script'] != 0xFFFF}


SPEAKER_WORDS = {'DAWN': ('COUNTERPART', 'GFX_VAR_', 'PLAYER_F', 'DAWN'), 'LUCAS': ('COUNTERPART', 'GFX_VAR_', 'PLAYER_M', 'LUCAS'),
                 'COUNTERPART': ('COUNTERPART', 'GFX_VAR_'), 'RIVAL': ('RIVAL', 'BARRY'), 'BARRY': ('RIVAL', 'BARRY'),
                 'GRUNT': ('GRUNT',), 'MOM': ('MOM', 'MOTHER'), 'PROF': ('PROF',)}


def speaker_matches(prefix, tag):
    """Whether a line's speaker name ("Dawn", "Grunt 1", "Dr. Footstep", "Pikachu") names a person (LOCALID, GFX)."""
    localid, gfx = tag
    hay = (localid + ' ' + gfx).upper()
    words = [w for w in re.split(r'[^A-Z]+', prefix.upper()) if len(w) > 2 and w not in ('THE', 'MR', 'DR', 'MRS', 'MS')]
    for w in words:
        if any(k in hay for k in SPEAKER_WORDS.get(w, (w,))):
            return True
    return False


BUFFER_PREFIX = re.compile(r'^\{0100:(\d)\}: ')
NARRATION = re.compile(r'^\{0100:0\}(?:’s|\'s)? [a-z]')
NAME_PREFIX = re.compile(r'^((?:\{0100:\d\}’s |\{0100:\d\}\'s )?[A-Z][\w.’\' -]{1,24}?): ')


# Commands whose macro fills the buffers of the lines it shows itself (pl_OpenMoveTutorMenu: WordSetPartyPokeName 0,
# WordSetMoveName 1), and stubbed fillers of features Black 2 lacks, as Pearl's build has them: listed, not failed.
SELF_FILLED = {'OpenMoveTutorMenu': {0, 1}}
KNOWN_STUBS = {
    'BufferContestBackdropName': 'contest backdrops (the dress-up photos): Black 2 has none, as in Pearl\'s build',
    'BufferVarPaddingDigits': 'the Battle Tower\'s padded numbers outside the Tower zones (TOWER_ONLY_HANDLERS), as in Pearl\'s build',
    'BufferCustomMessageWord': 'Gen 4\'s easy-chat words (the dress-up photo\'s title, Julia\'s stories): Black 2 has other word '
                               'lists; the same stub in Pearl\'s build',
    'BufferTrainerClassFromAppearance': 'the Union Room look the Oreburgh Center lady asks about: Black 2 has no such looks; '
                                        'the same stub in Pearl\'s build',
}


def entry_used(tr, job, a):
    """Whether some entry that reaches a is run by something: a person, sign or trigger of the zone, or a map script.
    (Platinum keeps Diamond and Pearl's unused scenes as entries nothing runs: Route 201's DPProfRowanScene_Unused.)"""
    if not tr.zone_file:
        return True
    ks = tr.reach_from.get(a, set())
    ev = job.events
    run = {o['script'] for o in ev['object_events']} | {b['script'] for b in ev['bg_events']} | \
        {c['script'] for c in ev['coord_events']} | set(job.init_level)
    return not ks or None in ks or bool(ks & run)


def problem_key(p):
    """What makes two runs' problems the same: zone, kind, the line's text and the message without addresses."""
    msg = re.sub(r'\b\d+:[0-9A-F]{4}\b', 'X', re.sub(r'line \d+', 'line N', p['msg']))
    return (p['zone'], p['kind'], p['text'], msg)


def zone_problems(pd, zones, widths=None, speakers=False):
    """(problems, counts, width rows, review rows) of the zones' text: problems are dicts zone, line, kind, msg, text."""
    import pearl_story as ps
    pd, done, spk = translate_all(pd, zones)
    problems, counts, width_rows, review = [], collections.Counter(), [], []
    codes = collections.Counter()

    def bad(zn, kind, k, msg, text=''):
        problems.append({'zone': zn, 'kind': kind, 'line': k, 'msg': msg, 'text': text})
    for z, job, text, uses, unconv in done:
        zn = z['name']
        pearl = pearl_lines(z) if version.PLATINUM else None
        sign_lines = {k for k, tr, a, cmd, key in uses if cmd in ('DrawSignpostInstantMessage',
                                                                  'DrawSignpostScrollingMessage', 'DrawSignpostMessage')}
        for k, t in enumerate(text):
            if not t.strip():
                counts['blank lines'] += 1         # (Gen 4's unused rows: spaces as long as the Japanese, never shown)
                continue
            new = pearl is not None and t not in pearl
            counts['lines'] += 1
            counts['new lines'] += new
            src = job.text[k][0]
            codes.update(gen4_codes(src))
            for kind, msg in line_problems(t, sign=k in sign_lines, values=wide_buffers(src)):
                bad(zn, kind, k, msg, t)
            if widths is not None:
                width_rows.append((zn, k, widest_row(t), int(new)))
        for src, dropped in unconv:
            for d in dropped:
                if d.startswith('kind of '):
                    counts['buffer kinds given 0100'] += 1
                elif re.fullmatch(r'\{WAIT \d+\}', d):
                    counts['WAIT codes dropped'] += 1     # (DROPPED['WAIT'])
                else:
                    bad(zn, 'dropped', None, f'{d} in {src[:70]!r}', src)
        # buffers: every buffer a shown line reads, filled before it by a translated command
        flows = {}
        for k, tr, a, cmd, key in uses:
            if k >= len(text):
                bad(zn, 'line', k, f'{cmd} at {tr.f}:{a:04X} shows line {k}, past the file\'s {len(text)}')
                continue
            bufs = {int(m.group(2).split(',')[0]) for m in CODE.finditer(text[k]) if m.group(1)[:2] in ('01', '02')}
            bufs -= SELF_FILLED.get(cmd, set())
            if not bufs:
                continue
            if not entry_used(tr, job, a):
                counts['buffered lines nothing runs'] += 1
                continue
            if id(tr) not in flows:
                flows[id(tr)] = Flow(tr)
            st = flows[id(tr)].at.get(a, frozenset())
            fills = job.buffer_fills.get(key[1], {}) if tr.zone_file and key[0] == z['text_bank'] else {}
            for i in sorted(bufs):
                if i in fills:                            # (data/platinum/pearl_buffer_fills.json: filled before it)
                    continue
                defs = [dd for b, dd in st if b == i]
                stubs = {dd[2] for dd in defs if job.insn_status.get((dd[0], dd[1]), (None, 'done'))[1] == 'stub'}
                known = stubs & set(KNOWN_STUBS)
                if known:
                    counts['buffers of features Black 2 lacks'] += 1
                    stubs -= known
                if stubs:
                    bad(zn, 'buffer', k, f'buffer {i} of line {k} ({cmd} at {tr.f}:{a:04X}) is filled by '
                                         f'{", ".join(sorted(stubs))}, not translated', text[k])
                elif not defs and tr.mode in ('zone', 'proxytalk', 'warp'):
                    bad(zn, 'buffer', k, f'buffer {i} of line {k} ({cmd} at {tr.f}:{a:04X}) is filled by nothing '
                                         f'before it: {text[k][:60]!r}', text[k])
            counts['buffered lines checked'] += 1
        # speakers: a balloon over the talked-to person after the script removed that person points at nobody
        names = decomp_objects(z)
        gone = {}
        for tr in {id(u[1]): u[1] for u in uses}.values():
            if tr.zone_file:
                gone.update(removed_before(tr, job))
        for k, tr, a, cmd, key in uses:
            who = spk.get((id(tr), a))
            if who != ('talk', None) or k >= len(text) or not tr.zone_file or not entry_used(tr, job, a):
                continue
            if gone.get((id(tr), a)):
                bad(zn, 'speaker', k, f'line {k} ({cmd} at {tr.f}:{a:04X}) is said in the balloon of '
                                      f'{sorted(gone[(id(tr), a)])}, whom the script removed before it: '
                                      f'{text[k][:50]!r}', text[k])
                continue
            if not speakers:
                continue
            m, b = NAME_PREFIX.match(text[k]), BUFFER_PREFIX.match(text[k])
            if NARRATION.match(text[k]):
                review.append((zn, k, tr.f, a, '(narration)', [], [], text[k][:80]))
                continue
            if not m and not b:
                continue
            if b:                                         # "{0100:1}: Hey!": whose name the buffer holds
                if id(tr) not in flows:
                    flows[id(tr)] = Flow(tr)
                fill = {dd[2] for i, dd in flows[id(tr)].at.get(a, ()) if i == int(b.group(1))}
                who = 'RIVAL BARRY' if 'BufferRivalName' in fill else 'COUNTERPART' if 'BufferCounterpartName' in fill \
                    else 'PLAYER' if fill == {'BufferPlayerName'} else '?'
            else:
                who = m.group(1)
            talked = [o for o in job.events['object_events'] if o['script'] in tr.reach_from.get(a, ())]
            tags = [names.get(o['id'], ('', '')) for o in talked]
            if any(speaker_matches(who, t) for t in tags):
                continue
            cand = sorted({uid for uid, t in names.items() if speaker_matches(who, t)})
            review.append((zn, k, tr.f, a, who, [t[0][8:] for t in tags], cand, text[k][:80]))
    counts['zones'] = len(done)
    counts.update({'code ' + k: v for k, v in codes.items()})
    return problems, counts, width_rows, review


def pearl_problems():
    """The same zone check run as Pearl's build (a PEARL_VERSION=pearl subprocess): its problems' keys."""
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'pearl.json')
        env = dict(os.environ, PEARL_VERSION='pearl')
        subprocess.run([sys.executable, os.path.abspath(__file__), '--zones-only', '--json', out], env=env,
                       capture_output=True, text=True, timeout=600)
        return {tuple(k) for k in json.load(open(out))}


# ------------------------------------------------------------------------------------------------------ system text
BATTLE_FIT = 240                # the battle window: Black 2's own in-battle Trainer lines reach 240 px (res/trainers/data)
BATTLE_TYPES = {1, 17, 18, 19, 20}     # Black 2 message types shown in battle (patches/pearl_trainers.py MSG_TYPE)
PLACE_FIT = 112                 # the place banner: Black 2's widest place name measures 106 px (Driftveil Drawbridge)
TOWN_MAP_ROWS = 3               # the Town Map's description box (Pearl's lines, on screen in Pearl's build)


def text_bank_numbers(tree):
    """{TEXT_BANK_ name: number} of a pokebw2 tree's system text list (an enum: a name without a value is the last + 1)."""
    out, n = {}, 0
    for l in open(os.path.join(tree, 'generated', 'text_banks.txt')):
        if l.startswith('TEXT_BANK_'):
            name, _, value = l.partition('=')
            n = int(value) if value.strip() else n
            out[name.strip()] = n
            n += 1
    return out


def system_problems():
    """Platinum's system text as the build packs it (patches/sinnoh_names.py's sources, packed by pokebw2's own packer
    on a clone and read back): place names and the zones' places, the Town Map's lines, the items Platinum adds and the
    Griseous Orb, Pokédex categories; and its Trainers' names, classes and messages as patches/pearl_trainers.py makes
    them. -> (problems, notes, counts)."""
    import gen4_text, pokebw2_mod, sinnoh_names
    problems, notes, counts = [], [], collections.Counter()

    def bad(kind, what, msg, text=''):
        problems.append({'zone': 'system', 'kind': kind, 'line': what, 'msg': msg, 'text': text})
    tree, names, _, _ = sinnoh_names.system_text_tree('text_check')
    packed = pokebw2_mod.pack_text(tree, 'system')['a/0/0/2']
    sys.path.insert(0, PB2)
    from tools.data.narc import read_narc
    from tools.text import text_data
    files, num = read_narc(packed), text_bank_numbers(tree)

    def bank(name):
        return [l for l in text_data.unpack_file(files[num['TEXT_BANK_' + name]]).split('\n')[:-1]
                if not l.startswith('\\pad{')]
    # place names: every section on its line, the Grand Underground's 265 and the Hoenn games' lines untouched
    places = bank('PLACE_NAMES')
    hoenn = {int(k) for k in json.load(open(os.path.join(ROOT, 'data', 'hoenn_places.json')))['lines']}
    lines_of = {}
    for sec in range(1, len(names)):
        line = sinnoh_names.place_line(sec)
        lines_of[sec] = line
        if places[line] != names[sec]:
            bad('place', sec, f'section {sec} on line {line} reads {places[line]!r}, not {names[sec]!r}')
        if line in hoenn or line == 265:
            bad('place', sec, f'section {sec} takes line {line}, the Hoenn games\' or the Grand Underground\'s')
        if row_width(names[sec]) > PLACE_FIT:
            bad('place', sec, f'{names[sec]!r} is {row_width(names[sec])} px > {PLACE_FIT}')
        for kind, msg in line_problems(names[sec], limit=PLACE_FIT, rows=1):
            if kind != 'fit':
                bad('place', sec, msg)
    if places[265] != 'Grand Underground':
        bad('place', 265, f'line 265 reads {places[265]!r}')
    counts['place names'] = len(names) - 1
    world = json.load(open(version.data_path('sinnoh_world.json')))
    zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    for group in (world['zones'], world['rooms']['zones']):
        for pid in group:
            sec = zones[int(pid)]['mapsec']
            if sec and sec not in lines_of:
                bad('place', pid, f'zone {pid} ({zones[int(pid)]["name"]}) is in section {sec}, which has no name')
            counts['zones placed'] += 1
    # the Town Map's lines (after Black 2's own; data/text_overrides/town_map.json, and Platinum's platinum/ rows)
    import town_map
    tm, want = bank('TOWN_MAP'), gen4_text.bank(556)
    for i, n in enumerate(town_map.desc_lines()):
        got = tm[town_map.B2_TOWNMAP_LINES + i]
        if got != gen4_text.b2_line(want[n]):
            bad('town map', n, f'Town Map line {n} reads {got[:50]!r}, not the dump\'s {want[n][:50]!r}')
        for kind, msg in line_problems(got, rows=TOWN_MAP_ROWS):
            bad('town map', n, msg, got)
        counts['Town Map lines'] += 1
    # items: Platinum's new ones and the Griseous Orb, as Black 2 names and describes them
    for what, b2, slot in (('name', 'ITEM_NAMES', 344), ('plural', 'ITEM_NAMES_PLURAL', 347),
                           ('description', 'ITEM_DESCRIPTIONS', 343)):
        got, dump = bank(b2), gen4_text.bank(slot)
        for item in (112, 465, 466, 467):
            w = gen4_text.to_b2(dump[item])
            if got[item] != w:
                bad('item', item, f'item {item} {what}: Black 2 {got[item]!r}, Platinum {w!r}')
            counts['item texts'] += 1
    # Pokédex categories
    got, dump = bank('SPECIES_CATEGORIES'), gen4_text.bank(621)
    for sp in range(1, 494):
        w = gen4_text.to_b2(dump[sp])
        if got[sp] != w:
            bad('category', sp, f'species {sp}: Black 2 {got[sp]!r}, Platinum {w!r}')
        counts['categories'] += 1
    # Trainers: names, the classes they show, their messages
    import pearl_trainers
    ids = json.load(open(version.data_path('pearl_story_ids.json')))
    todo = pearl_trainers.wanted(ids)
    index = json.load(open(os.path.join(pearl_trainers.TRAINERS, 'index.json')))
    reg = pearl_trainers.class_registry()
    dump_names = [n.replace('{TRNAME}', '') for n in gen4_text.bank(559)]
    dump_classes = [gen4_text.to_b2(n, punctuation='pearl') for n in gen4_text.bank(560)]
    from gen4rom import Rom, narc_members
    trdata = narc_members(Rom(version.WORLD_DUMP).read('poketool/trainer/trdata.narc'))
    msgs = pearl_trainers.pearl_messages()
    shown_classes = {}
    for t in todo:
        d = json.load(open(os.path.join(pearl_trainers.TRAINERS, 'data', f'{t:03d}.json'), encoding='utf-8'))
        pc = index[str(t)]['pearl_class']
        name = 'Barry' if pc == 'PKMN_TRAINER_BARRY' else d['name']
        if name != dump_names[t] and pc != 'PKMN_TRAINER_BARRY':
            bad('trainer', t, f'Trainer {t}: {name!r}, the dump says {dump_names[t]!r}')
        if len(name) > 10:
            bad('trainer', t, f'Trainer {t}: {name!r} is longer than 10 characters')
        e = reg['classes'].get(pc, {})
        shown = e.get('name') or json.load(open(os.path.join(PB2, 'res', 'trainers', 'classes',
                                                              index[str(t)]['b2_class'].lower() + '.json'),
                                                 encoding='utf-8'))['name']
        shown_classes.setdefault(pc, (shown, trdata[t][1]))
        for ty, line in msgs.get(t, []):
            ty2 = pearl_trainers.MSG_TYPE.get(ty)
            if ty2 is None:
                continue
            for kind, msg in line_problems(line, limit=BATTLE_FIT if ty2 in BATTLE_TYPES else FIT):
                bad('trainer message', t, f'Trainer {t} type {ty}: {msg}', line)
            counts['Trainer messages'] += 1
        counts['Trainers'] += 1
    if version.PLATINUM:                          # each class's Black 2 name against Platinum's own
        for pc, (shown, n) in sorted(shown_classes.items()):
            want = dump_classes[n]
            if shown != want:
                how = 'the registry\'s name' if pc in reg['classes'] else 'Black 2\'s class name'
                notes.append(f'class {pc}: {shown!r} ({how}, as Pearl\'s build), Platinum {want!r}')
                if n >= 98:
                    bad('class', pc, f'Platinum\'s new class {pc} shows {shown!r}, not {want!r}')
        counts['classes'] = len(shown_classes)
    return problems, notes, counts


def script_problems(pd):
    """Every installed zone's script file (what the build installs: version.sources) assembles with pokebw2's macros, passes
    b2_script_check at its map scripts' levels and shows only lines its text file has: patches/sinnoh_story.py's checks,
    offline (--scripts; the speakers, buffer fills and new buffer commands of this step change the scripts)."""
    import pearl_ids, pearl_events, b2_script_check, scripts as sp
    ids = pearl_ids.Ids()
    by_num = pd.zones_of_script_file()
    srcs = {int(os.path.basename(p)[:4]): p for p in version.sources(os.path.join(ROOT, 'src', 'field_scripts'), '.s')
            if '_pearl_' in os.path.basename(p)}
    texts = {int(os.path.basename(p)[:4]): p for p in version.sources(os.path.join(ROOT, 'src', 'text', 'script'), '.txt')}
    out, n = [], 0
    for num, path in sorted(srcs.items()):
        if num not in by_num:
            continue
        binary = sp.assemble(path)
        for z in by_num[num]:
            if pd.b2_zone.get(z['id']) is None:
                continue
            init, levels = pearl_events.map_script_table(pd, z, ids)
            t = texts.get(pd.text_file(z))
            nl = sum(1 for l in open(t, encoding='utf-8') if ' = ' in l) if t else 0
            missing = sorted(m for m in b2_script_check.message_lines(binary) if m >= nl)
            if missing:
                out.append({'zone': z['name'], 'kind': 'script', 'line': None, 'text': '',
                            'msg': f'lines {missing[:6]} past its text file\'s {nl}'})
            for p in b2_script_check.check(binary, levels):
                out.append({'zone': z['name'], 'kind': 'script', 'line': None, 'text': '', 'msg': p})
            n += 1
    return out, n


def main(argv):
    import pearl_story as ps
    opts = {}
    for flag in ('--widths', '--json'):
        if flag in argv:
            i = argv.index(flag)
            opts[flag] = argv[i + 1]
            del argv[i:i + 2]
    flags = {a for a in argv if a.startswith('--')}
    argv = [a for a in argv if not a.startswith('--')]
    pd = ps.PearlData()
    zones = [ps.zone_arg(pd, a) for a in argv] or [z for z in installed_zones(pd) if not later_piece(z)]
    problems, counts, width_rows, review = zone_problems(pd, zones, opts.get('--widths'), '--speakers' in flags)
    if '--json' in opts:                          # (pearl_problems: the keys only)
        json.dump([problem_key(p) for p in problems], open(opts['--json'], 'w'))
        return 0
    notes, scounts = [], collections.Counter()
    if '--zones-only' not in flags and not argv:
        sp, notes, scounts = system_problems()
        problems += sp
    if '--scripts' in flags:
        sp, n = script_problems(pd)
        problems += sp
        scounts['zone script files assembled and checked'] = n
    inherited = []
    if version.PLATINUM and not argv:             # problems Pearl's own build has the same (same zone, line, kind)
        keys = pearl_problems()
        inherited = [p for p in problems if problem_key(p) in keys]
        problems = [p for p in problems if problem_key(p) not in keys]
    for title, rows in (('Problems', problems), ('Pearl\'s own, the same in its 1.0 build (left as they are)', inherited)):
        if not rows:
            continue
        print(f'{title}:')
        for zn in sorted({p['zone'] for p in rows}):
            print(f'  {zn}')
            for p in (p for p in rows if p['zone'] == zn):
                print(f'    {p["kind"]:8} line {p["line"] if p["line"] is not None else "-"}: {p["msg"]}')
    print(f'{counts["zones"]} zones, {counts["lines"]} lines ({counts["new lines"]} not in Pearl\'s files), '
          f'{counts["buffered lines checked"]} lines with buffers checked ({counts["buffered lines nothing runs"]} more '
          f'only in scripts nothing runs); {len(problems)} problems, {len(inherited)} the same as in Pearl\'s build')
    for k, why in (('buffer kinds given 0100', DROPPED['kind']), ('WAIT codes dropped', DROPPED['WAIT']),
                   ('buffers of features Black 2 lacks', 'filled by commands of features Black 2 lacks: KNOWN_STUBS')):
        if counts[k]:
            print(f'  {counts[k]} {k}: {why}')
    print('Gen 4 control codes in the zone lines, and what each became:')
    for k in sorted(c[5:] for c in counts if c.startswith('code ')):
        print(f'  {k} x{counts["code " + k]}: {GEN4_CODES.get(k, "NOT MAPPED")}')
        if k not in GEN4_CODES:
            problems.append({'zone': '-', 'kind': 'code', 'line': None, 'msg': f'{k} has no row in GEN4_CODES', 'text': ''})
    if scounts:
        print('system text: ' + ', '.join(f'{v} {k}' for k, v in scounts.items()))
    for n in notes:
        print(f'  note: {n}')
    if widths := opts.get('--widths'):
        with open(widths, 'w', encoding='utf-8') as fh:
            fh.write('zone\tline\tpx\tnew\n' + ''.join(f'{a}\t{b}\t{c}\t{d}\n' for a, b, c, d in width_rows))
    if '--speakers' in flags:
        print(f'\n{len(review)} talk-script lines that may be another speaker\'s (for data/pearl_speakers.json):')
        for zn, k, f, a, nm, talked, cand, t in review:
            print(f'  {zn} line {k} ({f}:{a:04X}) [{nm}] talked to {talked}, objects named so: {cand}: {t}')
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
