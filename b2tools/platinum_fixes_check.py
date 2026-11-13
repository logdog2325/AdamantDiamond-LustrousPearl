"""Offline checks of the plat-fixes piece (2026-11-07): Platinum's Pokédex ratings, the Pokétch Calculator's Sinnoh dex,
the seasonal texture sets' palettes and the Marts' stock. No ROM, no emulator.

    PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py ratings     the professors' ratings
    PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py poketch     the Calculator's Sinnoh dex
    PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py palettes    every palette a chunk draws is in its set
    PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py marts       every Mart's and shop's stock
    PEARL_VERSION=platinum python3 b2tools/platinum_fixes_check.py all

ratings: the rating macros of src/include/pearl_story.inc are run here (a small interpreter of the few commands they
use) for every count, and the line each gives is compared with pokeplatinum's own choice (src/unk_0205DFC4.c
Pokedex_GetRatingMessageID_Local / _National, its thresholds read from the C; the lines' order from
res/text/pokedex_ratings.json): Rowan's for 0-210 seen, with and without the first visit to Eterna, with and without
Manaphy seen (it is not in Platinum's list); Oak's for 0-493 caught, boy and girl. Then every call of the macros in what
the build installs (the zones Platinum's generator writes, the PC's global 1260) passes lines whose words are Platinum's
rating bank's lines, in order. Exit 1 on any difference.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402

PLAT = os.path.join(ROOT, 'external', 'pokeplatinum')
INC = os.path.join(ROOT, 'src', 'include', 'pearl_story.inc')
SINNOH_GOAL = 210                     # Platinum's LOCAL_DEX_GOAL (REGIONAL_DEX_COUNT, nothing excluded)
NATIONAL_MAX = 493
MYTHICALS = 11                        # Platinum's sExcludedMonsNational: none caught in these runs


# ---- the macros, as gas expands them ----------------------------------------------------------------------------------
def macros(path=INC):
    """{name: (params, body lines)} of every .macro in the file."""
    out, cur = {}, None
    for line in open(path, encoding='utf-8'):
        code = line.split('//')[0].strip()
        m = re.match(r'\.macro\s+(\w+)[\s,]*(.*)$', code)
        if m:
            cur = (m.group(1), [p.strip().split('=')[0] for p in m.group(2).split(',') if p.strip()], [])
            continue
        if code == '.endm' and cur:
            out[cur[0]] = (cur[1], cur[2]); cur = None
        elif cur and code:
            cur[2].append(code)
    return out


def expand(name, args, defs, counter=[0]):
    """The commands a macro call becomes: [(op, [args])], labels as (':', [name]); .if / .irp done here."""
    params, body = defs[name]
    counter[0] += 1
    n = counter[0]
    sub = dict(zip(params, args))
    def fill(s):
        s = s.replace('\\@', str(n))
        for p in sorted(sub, key=len, reverse=True):
            s = s.replace('\\' + p, str(sub[p]))
        return s
    lines, out, i = [fill(l) for l in body], [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('.if '):
            depth, j = 1, i + 1
            while depth:
                depth += lines[j].startswith('.if ') - (lines[j] == '.endif'); j += 1
            if int(l[4:].strip(), 0):
                out += _run_lines(lines[i + 1:j - 1], defs)
            i = j; continue
        if l.startswith('.irp '):
            var, items = l[5:].split(',', 1)
            j = lines.index('.endr', i)
            for item in [x.strip() for x in items.split(',')]:
                out += _run_lines([x.replace('\\' + var.strip(), item) for x in lines[i + 1:j]], defs)
            i = j + 1; continue
        out += _run_lines([l], defs)
        i += 1
    return out


def _run_lines(lines, defs):
    out = []
    for l in lines:
        if l.endswith(':'):
            out.append((':', [l[:-1]])); continue
        op, _, rest = l.partition(' ')
        args = [a.strip() for a in rest.split(',')] if rest.strip() else []
        out += expand(op, args, defs) if op in defs else [(op, args)]
    return out


def run(cmds, state):
    """Runs the commands; state: seen (Sinnoh list), caught (National), victini, manaphy (seen), eterna (flag 0x9BA),
    gender (0 boy, 1 girl). Returns the works."""
    w, cmp, pc = {}, (0, 0), 0
    labels = {a[0]: k for k, (op, a) in enumerate(cmds) if op == ':'}
    def val(x):
        return w.get(x, 0) if not re.match(r'^-?(0x[0-9a-fA-F]+|\d+)$', x) else int(x, 0)
    while pc < len(cmds):
        op, a = cmds[pc]; pc += 1
        if op == ':': continue
        if op == 'WorkSetConst': w[a[0]] = val(a[1])
        elif op == 'WorkSet': w[a[0]] = w.get(a[1], 0)
        elif op == 'WorkSub': w[a[0]] = w.get(a[0], 0) - w.get(a[1], 0)
        elif op == 'WorkCmpConst': cmp = (w.get(a[0], 0), val(a[1]))
        elif op == 'VMJumpIf':
            ok = {'CMP_LT': cmp[0] < cmp[1], 'CMP_EQ': cmp[0] == cmp[1], 'CMP_NE': cmp[0] != cmp[1],
                  'CMP_GT': cmp[0] > cmp[1], 'CMP_GE': cmp[0] >= cmp[1], 'CMP_LE': cmp[0] <= cmp[1]}[a[0]]
            if ok: pc = labels[a[1]]
        elif op == 'FlagGet':
            assert a[0] == 'PFLAG_09BA', f'FlagGet {a[0]}: not the Eterna flag'
            w[a[1]] = int(state['eterna'])
        elif op == 'TrainerCardGetSex': w[a[0]] = state['gender']
        elif op == 'PokeDexGetEvaluationParams':
            assert a[0] == '2', a
            w[a[2]] = state['seen'] + state['victini']        # Black 2's regional seen count (Victini is #000)
        elif op == 'PokeDexIsRegist':
            sp = a[1]
            w[a[2]] = {'SPECIES_VICTINI': state['victini'], 'SPECIES_MANAPHY': state['manaphy']}.get(sp, 0) \
                if a[0] == '0' else 0
        elif op == 'PokeDexGetCount':
            assert a[0] == '1', a
            w[a[1]] = state['caught']
        else:
            raise SystemExit(f'ratings: the interpreter does not know {op} {a}')
    return w


# ---- Platinum's own choice ------------------------------------------------------------------------------------------
def platinum_rules():
    """(local [(max, line)], (complete, too early), national [(max, line or (boy, girl))], (boy, girl)) from the C."""
    names = [m['id'] for m in json.load(open(os.path.join(PLAT, 'res', 'text', 'pokedex_ratings.json')))['messages']]
    line = {n: i for i, n in enumerate(names)}
    c = open(os.path.join(PLAT, 'src', 'unk_0205DFC4.c'), encoding='utf-8').read()
    loc = c[c.index('u16 Pokedex_GetRatingMessageID_Local'):c.index('u16 Pokedex_GetRatingMessageID_National')]
    nat = c[c.index('u16 Pokedex_GetRatingMessageID_National'):c.index('u16 SaveData_GetFirstNonEggInParty')]
    local = [(SINNOH_GOAL - 1 if n == 'LOCAL_DEX_GOAL - 1' else int(n), line[t])
             for n, t in re.findall(r'pokemonSeen <= ([\w -]+?)\) \{\s*return (\w+);', loc)]
    done = re.search(r'if \(reachedEternaCity\) \{\s*return (\w+);\s*\} else \{\s*return (\w+);', loc)
    national = []
    for n, body in re.findall(r'pokemonCaught <= (\d+)\) \{(.*?)\n    \}', nat, re.S):
        g = re.search(r'if \(playerGender\) \{\s*return (\w+);\s*\} else \{\s*return (\w+);', body)
        national.append((int(n), (line[g.group(2)], line[g.group(1)]) if g else line[re.search(r'return (\w+);', body).group(1)]))
    last = re.findall(r'if \(playerGender\) \{\s*return (\w+);\s*\} else \{\s*return (\w+);', nat)[-1]
    return local, (line[done.group(1)], line[done.group(2)]), national, (line[last[1]], line[last[0]])


def platinum_local(n, eterna, rules):
    local, (complete, early), _, _ = rules
    for top, l in local:
        if n <= top: return l
    return complete if eterna else early


def platinum_national(n, gender, rules):
    _, _, national, done = rules
    for top, l in national:
        if n <= top: return l[gender] if isinstance(l, tuple) else l
    return done[gender]


def check_ratings():
    defs = macros()
    rules = platinum_rules()
    bad = []
    first, last, local_macro = version.DEX_RATING[0]
    nfirst, nlast, national_macro = version.DEX_RATING[1]
    assert (first, last, nfirst, nlast) == (4, 17, 22, 42), version.DEX_RATING
    lines = list(range(first, last + 1))
    cmds = expand(f'pl_LoadPokedexRating{local_macro}', ['RESULT'] + lines, defs)
    for seen in range(SINNOH_GOAL + 1):
        for eterna in (False, True):
            for manaphy in (0, 1):
                for victini in (0, 1):
                    got = run(cmds, dict(seen=seen, caught=0, victini=victini, manaphy=manaphy, eterna=eterna,
                                         gender=0))['RESULT']
                    want = platinum_local(seen, eterna, rules)
                    if got != want:
                        bad.append(f'Rowan, {seen} seen, Eterna {eterna}, Manaphy {manaphy}, Victini {victini}: line '
                                   f'{got}, Platinum {want}')
    nlines = list(range(nfirst, nlast + 1))
    ncmds = expand(f'pl_LoadPokedexRating{national_macro}', ['RESULT'] + nlines, defs)
    for caught in range(NATIONAL_MAX + 1):
        for gender in (0, 1):
            got = run(ncmds, dict(seen=0, caught=caught, victini=0, manaphy=0, eterna=True, gender=gender))['RESULT']
            want = platinum_national(caught, gender, rules)
            if got != want:
                bad.append(f'Oak, {caught} caught, {"girl" if gender else "boy"}: line {got}, Platinum {want}')
    shown = {n: platinum_local(n, e, rules) for n in (0, 60, 150, 209) for e in (True,)}
    print(f'ratings: Rowan for 0-{SINNOH_GOAL} seen x Eterna x Manaphy x Victini, Oak for 0-{NATIONAL_MAX} caught x boy/girl '
          f'run from pearl_story.inc against pokeplatinum: {len(bad)} differences')
    for n in (0, 60, 150, 210):
        print(f'  {n:3d} seen: line {platinum_local(n, False, rules)} before Eterna, {platinum_local(n, True, rules)} after '
              f'(the macro: {run(cmds, dict(seen=n, caught=0, victini=0, manaphy=0, eterna=False, gender=0))["RESULT"]}, '
              f'{run(cmds, dict(seen=n, caught=0, victini=0, manaphy=0, eterna=True, gender=0))["RESULT"]})')
    bad += check_calls(lines, nlines)
    for b in bad[:30]:
        print('  ' + b)
    return not bad


def bank_lines():
    import gen4_text
    return [gen4_text.b2_line(t) for t in gen4_text.bank(335)]


def text_of(path):
    """The lines of a res/text-format file (ID = text), by number."""
    return [l.split(' = ', 1)[1] if ' = ' in l else '' for l in open(path, encoding='utf-8').read().split('\n')[:-1]
            if not l.startswith('\\pad{')]


def check_calls(lines, nlines):
    """Every call of the rating macros in what a Platinum build installs passes the lines of Platinum's bank 335."""
    bank = bank_lines()
    scripts = {os.path.basename(p)[:4]: p for p in version.sources(os.path.join(ROOT, 'src', 'field_scripts'), '.s')}
    texts = {os.path.basename(p)[:4]: p for p in version.sources(os.path.join(ROOT, 'src', 'text', 'script'), '.txt')}
    bad, calls = [], 0
    import pearl_story
    for num, path in sorted(scripts.items()):
        src = open(path, encoding='utf-8').read()
        for macro, args in re.findall(r'^\s*(pl_LoadPokedexRating\w+)\s+([^/\n]+)', src, re.M):
            calls += 1
            args = [a.strip() for a in args.split(',')][1:]
            want = lines if 'Local' in macro else nlines
            if macro not in ('pl_LoadPokedexRatingLocalPlatinum', 'pl_LoadPokedexRatingNational') or len(args) != len(want):
                bad.append(f'{os.path.relpath(path, ROOT)}: {macro} with {len(args)} lines (Platinum: '
                           f'pl_LoadPokedexRatingLocalPlatinum 14, pl_LoadPokedexRatingNational 21)')
                continue
            # the script's text file: the global 1260 prints a/0/0/3 file 1051, a zone its own (pearl_story's numbering)
            tnum = '1051' if num == '1260' else next((t for t, p in texts.items() if os.path.basename(p)[5:-4] ==
                                                      os.path.basename(path)[5:-2]), None)
            assert tnum, path
            text = text_of(texts[tnum])
            for k, a in enumerate(args):
                got = text[int(a)] if int(a) < len(text) else None
                if got != bank[want[k]]:
                    bad.append(f'{os.path.relpath(path, ROOT)} {macro} line {a} ({os.path.basename(texts[tnum])}): not '
                               f'Platinum bank 335 line {want[k]}')
    print(f'ratings: {calls} calls of the rating macros in what the build installs, each line checked against Platinum\'s '
          f'bank 335')
    if calls < 4:
        bad.append(f'only {calls} rating calls found (Rowan\'s lab, Oak\'s house twice, the PC at least)')
    return bad


# ---- the Marts --------------------------------------------------------------------------------------------------------
def platinum_items():
    """{ITEM_X: id} from pokeplatinum generated/items.txt (an enum's list: ITEM_NONE 0, ITEM_MASTER_BALL 1, ...)."""
    names = [l.split('=')[0].strip() for l in open(os.path.join(PLAT, 'generated', 'items.txt'), encoding='utf-8')
             if l.strip() and not l.startswith('#')]
    assert names[0] == 'ITEM_NONE' and names[4] == 'ITEM_POKE_BALL' and names[328] == 'ITEM_TM01', names[:5]
    return {n: i for i, n in enumerate(names)}


def platinum_marts():
    """(badge list [(item, badges)], [special list n: [item]], {list name: [item]}) from include/data/mart_items.h."""
    ids = platinum_items()
    h = open(os.path.join(PLAT, 'include', 'data', 'mart_items.h'), encoding='utf-8').read()
    common = [(ids[n], int(b, 0)) for n, b in
              re.findall(r'\{ (ITEM_\w+), (0x\w+|\d+) \}', h[h.index('PokeMartCommonItems[]'):h.index('};')])]
    lists = {name: [ids[i] for i in re.findall(r'(?<![A-Z_])(ITEM_\w+)', body)]
             for name, body in re.findall(r'const u16 (\w+)\[\] = \{(.*?)\};', h, re.S)}
    table = h[h.index('*PokeMartSpecialties[]'):]
    table = table[:table.index('};')]
    order = [l.strip() for l in open(os.path.join(PLAT, 'generated', 'mart_specialties_id.txt')) if l.strip()]
    special = [None] * len(order)
    for key, name in re.findall(r'\[(MART_SPECIALTIES_ID_\w+)\] = (\w+)', table):
        special[order.index(key)] = lists[name]
    return common, special


def check_marts():
    """Every list pearl_shops writes against Platinum's tables; every clerk of what the build installs against the
    Platinum script of the same zone; every price a clerk asks against Platinum's (res/items/data/*.json)."""
    import narcio, pearl_items, pearl_shops, tm_audit
    import gen4_script
    from gen4rom import Rom, narc_members
    bad = []
    common, special = platinum_marts()
    lists = pearl_shops.lists()
    b2 = pearl_items.b2_item
    for k in range(pearl_items.BADGE_STEPS):            # Platinum's badge steps: 0; 1-2; 3-4; 5-6; 7; 8 = 1..6
        want = [b2(i) for i, need in common if need <= k + 1]
        if lists.get(k) != want:
            bad.append(f'badge list {k}: {lists.get(k)} != Platinum {want}')
    for n, items in enumerate(special):                # (Platinum's list, then the Game Corner prizes added on purpose:
        added = list(version.STORE_TMS.get(n, ())) + list(version.STORE_ITEMS.get(n, ()))   # version.STORE_TMS, STORE_ITEMS)
        want = [b2(i) for i in items + added]
        if lists.get(pearl_shops.FIRST_SPECIAL + n) != want:
            bad.append(f'special list {n} (file {pearl_shops.FIRST_SPECIAL + n}): {lists.get(pearl_shops.FIRST_SPECIAL + n)} '
                       f'!= Platinum {want}')
    extra = sorted(set(lists) - set(range(pearl_items.BADGE_STEPS)) -
                   {pearl_shops.FIRST_SPECIAL + n for n in range(len(special))})
    if extra:
        bad.append(f'lists past Platinum\'s: {extra}')
    print(f'marts: {pearl_items.BADGE_STEPS} badge lists and {len(special)} special lists written, compared with '
          f'pokeplatinum mart_items.h')

    # the clerks: the installed scripts against the Platinum dump's own script of the zone
    zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    files = version.slotted('scripts', narc_members(Rom(version.WORLD_DUMP).read(version.ARCHIVE['scripts'])))
    table = gen4_script.load_table()
    names = {e['name']: e['op'] for e in table if e.get('name')}
    ops = {names[n]: n for n in ('NormalMart', 'SpecialMart', 'GoodsMart', 'SealsMart')}
    installed = {os.path.basename(p)[11:-2]: p for p in version.sources(os.path.join(ROOT, 'src', 'field_scripts'), '.s')
                 if '_pearl_' in os.path.basename(p)}
    clerks = 0
    for z in zones:
        if not z.get('scripts') and z.get('scripts') != 0 or z['scripts'] >= len(files) or not files[z['scripts']]:
            continue
        d = gen4_script.Disasm(files[z['scripts']], table)
        dump = sorted((a, ops[op], args[0][1]) for a, (end, op, args, *_) in d.insns.items() if op in ops)
        if not dump:
            continue
        name = z['name'][4:].lower()
        path = installed.get(name)
        if not path and 'UNUSED' in z['name']:
            print(f'marts: {z["name"]} (an unused zone of Platinum\'s, not built) has {len(dump)} Mart commands')
            continue
        if not path:
            bad.append(f'{z["name"]}: Platinum\'s script has {len(dump)} Mart commands, no installed file')
            continue
        src = open(path, encoding='utf-8').read()
        got = re.findall(r'^\s*(?:pl_PokeMartCommon \S+|pl_PokeMartSpecial (\S+)|pl_GoodsMart (\S+)|'
                         r'pl_msg_talk \S+\s+// Pearl SealsMart (\d+))', src, re.M)
        got = sorted(((('SpecialMart', int(s)) if s else ('GoodsMart', int(g)) if g else ('SealsMart', int(sl)) if sl
                       else ('NormalMart', None)) for s, g, sl in got), key=str)
        want = sorted(((kind, None if kind == 'NormalMart' else v) for _, kind, v in dump), key=str)
        clerks += len(dump)
        if sorted(set(got), key=str) != sorted(set(want), key=str):
            bad.append(f'{os.path.relpath(path, ROOT)}: {sorted(set(got), key=str)} != Platinum\'s {sorted(set(want), key=str)}')
    print(f'marts: {clerks} Mart commands in Platinum\'s zone scripts, each zone\'s installed file sells the same lists')

    # prices: what the build charges (Black 2's record; the TMs Pearl's price: pearl_shops, pearl_tms) against Platinum's
    import pearl_tms
    vanilla = narcio.load(os.path.join(ROOT, 'external', 'pokebw2', 'build', 'b2_us', 'files'), 24)
    tm_prices = pearl_tms.pearl_prices()
    labels = pearl_tms.pearl_names() if hasattr(pearl_tms, 'pearl_names') else None
    pl_names = {v: k for k, v in platinum_items().items()}
    sold = sorted({i for i, _ in common} | {i for l in special for i in l} |       # (and the Game Corner prizes added)
                  {i for store in (version.STORE_TMS, version.STORE_ITEMS) for l in store.values() for i in l})
    differ = []
    for pearl in sold:
        item = b2(pearl)
        if 328 <= pearl <= 427:
            price = pearl_shops.pearl_price(pearl) if item == pearl else None
            if price is None:                  # TM96-TM120: pearl_tms gives them Pearl's price by label
                price = tm_prices[pl_names[pearl][5:]]
        else:
            price = struct_price(vanilla[item])
        js = os.path.join(PLAT, 'res', 'items', 'data', pl_names[pearl][5:].lower() + '.json')
        want = json.load(open(js, encoding='utf-8'))['price']
        if price != want:
            differ.append(f'{pl_names[pearl]} ({pearl} -> {item}): {price}, Platinum {want}')
    print(f'marts: {len(sold)} items sold, the build\'s price against Platinum\'s: {len(differ)} differ')
    for x in differ:
        print('  price ' + x)
    for b in bad[:30]:
        print('  ' + b)
    return not bad, differ


# ---- the seasons' palettes -------------------------------------------------------------------------------------------
def check_palettes():
    """Every (texture, palette) a chunk's material draws is in its area's set, all four seasons, for the overworld's
    areas and the outdoor rooms' (season_grass_check's areas and sets: sinnoh_reskin as the build calls it)."""
    import nsbtx, season_grass_check as sg
    from gen4rom import Rom
    from version import land_id
    areas = sg.areas_and_chunks(Rom(version.WORLD_DUMP))
    sets = sg.offline_sets(areas)
    bad, pairs = [], 0
    for k, (_, chunks) in areas.items():
        drawn = set()
        for c in chunks:
            p = os.path.join(version.WORLD_WORK, 'land', f'{land_id(c):03d}.nsbmd')
            if os.path.exists(p):
                drawn |= nsbtx.material_pairs(open(p, 'rb').read())
        for s in range(4):
            P = nsbtx._parse(sets[k][s])
            pals, texs = {p for p, _ in P['pals']}, {t for t, _ in P['texs']}
            for t, p in sorted(drawn, key=str):
                if t in texs and p:
                    pairs += 1
                    if p not in pals:
                        bad.append(f'{k[0]} area {k[1]}, {sg.SEASONS[s]}: {t} is drawn with palette {p}, not in the set')
    print(f'palettes: {len(areas)} area sets x 4 seasons, {pairs} (texture, palette) pairs drawn: {len(bad)} missing')
    for b in bad[:20]:
        print('  ' + b)
    return not bad


# ---- the Pokétch's Calculator ----------------------------------------------------------------------------------------
def check_poketch():
    """The Calculator's Sinnoh dex as the build makes it: the config's count (patches/poketch.py) is Platinum's 210; the
    regional dex table that patches/sinnoh_dex.py writes (a/0/1/6 file 709, on a copy of Black 2's) gives, read the
    way the C reads it (calculator.c SinnohDexSpecies: the first species 1-649 numbered n), the species Platinum's own
    lookup gives (Pokemon_NationalDexNumber: poketool/shinzukan member 0, entry n) for every n 1-210; and the C has no
    other limit (no gPearlB2SinnohDex, no 151/152 in the Pokétch's sources that read the dex)."""
    import shutil, struct, tempfile
    import narcio, poketch, sinnoh_dex
    from gen4rom import Rom
    bad = []
    count = poketch.sinnoh_dex_count()
    if count != 210:
        bad.append(f'the config\'s Sinnoh count is {count}, Platinum\'s is 210')
    shin = struct.unpack('<211H', poketch.narc_member(Rom(version.WORLD_DUMP).read(poketch.PEARL_SINNOH_DEX), 0)[:422])
    vanilla = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'b2_us', 'files')
    with tempfile.TemporaryDirectory() as t:
        for arc in (sinnoh_dex.ARC_PERSONAL, sinnoh_dex.ARC_SORT):
            p = os.path.join('a', f'{arc:03d}'[0], f'{arc:03d}'[1], f'{arc:03d}'[2])
            os.makedirs(os.path.join(t, os.path.dirname(p)), exist_ok=True)
            shutil.copy(os.path.join(vanilla, p), os.path.join(t, p))
        sinnoh_dex.apply(t)
        regional = narcio.load(t, sinnoh_dex.ARC_PERSONAL)[sinnoh_dex.FILE_REGIONAL]
    table = struct.unpack(f'<{len(regional) // 2}H', regional)
    def calculator(n):                         # calculator.c SinnohDexSpecies(heap, n, nationalDexMax)
        return next((i for i in range(1, poketch.NATIONAL_DEX_MAX + 1) if table[i] == n), 0)
    for n in range(1, count + 1):
        if calculator(n) != shin[n]:
            bad.append(f'Sinnoh {n}: the Calculator\'s species {calculator(n)}, Platinum\'s {shin[n]}')
    src = os.path.join(ROOT, 'external', 'pokebw2', 'src', 'pearlb2', 'poketch')
    calc = open(os.path.join(src, 'apps', 'calculator.c'), encoding='utf-8').read()
    if 'gPearlB2SinnohDex' in calc or 'SinnohDexSpecies(' not in calc:
        bad.append('the decomp\'s calculator.c is not the one that reads the regional dex table (external/pokebw2: '
                   'the plat-fixes decomp branch)')
    for app in ('calculator.c', 'pokemon_history.c', 'party_status.c', 'matchup_checker.c', 'daycare_checker.c'):
        code = re.sub(r'//[^\n]*|/\*.*?\*/', '', open(os.path.join(src, 'apps', app), encoding='utf-8').read(), flags=re.S)
        for line in code.split('\n'):          # (screen coordinates and tiles are numbers too: only dex lines)
            if re.search(r'(?i)dex|species|regional|sinnoh', line) and re.search(r'\b(151|152|210|211|493)\b', line):
                bad.append(f'{app}: a fixed dex size: {line.strip()}')
    print(f'poketch: the Calculator knows Sinnoh 1-{count}; its lookup (the regional dex table sinnoh_dex writes) '
          f'equals Platinum\'s shinzukan for all {count}, e.g. #152 = species {calculator(152)}, #210 = species '
          f'{calculator(210)}: {len(bad)} problems')
    for b in bad[:20]:
        print('  ' + b)
    return not bad


def struct_price(record):
    import struct
    return struct.unpack_from('<H', record, 0)[0] * 10


def main(argv):
    assert version.PLATINUM, 'PEARL_VERSION=platinum'
    what = argv[0] if argv else 'all'
    checks = {'ratings': check_ratings, 'poketch': check_poketch, 'palettes': check_palettes,
              'marts': lambda: check_marts()[0]}
    ok = all(checks[k]() for k in (checks if what == 'all' else [what]))
    print('ok' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
