"""Where each TM and HM can be had, per version, and which come twice (fix102, 2026-11-22). Read-only.

    PEARL_VERSION=<pearl|diamond|platinum> python3 b2tools/tm_sources.py [--all] [--strict]

Black 2's Bag holds one of each TM and HM (Pearl's held 999), so a TM that two one-time sources give (two balls, a ball and
a gift) can only be taken once. Since fix102 a free source of a TM the Bag already holds still goes, with Pearl's lines
(pl_CanFitItemFree): no ball or gift stays saying the Bag is full. This lists:
  - every TM/HM with more than one source of which at least one is one-time (a ball, a hidden item, a gift), the
    shops and the Battle Point Exchange shown beside them (they show the TM as owned and sell no second one);
  - the Underground's Hideaway balls that give a TM something else gives too (the Discord report: TM12 in the Underground
    and on Route 211). None since the user's choice (2026-11-22, notes/UNDERGROUND.md 13): 16 of the Hideaways' 17 TM
    balls give Black 2's own TMs that Sinnoh never gives, TM55 Scald the 17th;
  - Black 2's own TMs (moves that aren't Pearl TMs) and where they come from, and every Pearl TM/HM with no source.
  --strict exits 1 on an Underground TM given elsewhere too or a Pearl TM/HM with no source. --all: every TM/HM with
  its sources. (Not real doubles, as listed: the Ruin Maniac Cave's stages are one ball, two branches of one script are
  one gift.)
Sources, as the guide's TM page reads them (gen_docs.tms_page): pearl_items.world() (balls, hidden items), the
installed scripts' gift lines (`pl_SetVarFromValue PVAR_8004, <TM>`: this version's own generated files first), the
special Marts' lists (pl_PokeMartSpecial n), the Exchange (resident/tower.c sExchange), data/underground.json."""
import collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import version, gen_docs, tm_audit, pearl_items, ug_data  # noqa: E402

ONCE = ('ball', 'hidden', 'gift', 'underground')


def script_files():
    """{file name: path} of the zone scripts this version installs (Diamond's and Platinum's own files first)."""
    fs = gen_docs.FS
    out = {f: os.path.join(fs, f) for f in os.listdir(fs) if '_pearl_' in f and f.endswith('.s')}
    for d in (os.path.join(fs, version.VERSION), version.generated_folder(fs)):
        if d != fs and os.path.isdir(d):
            out.update({f: os.path.join(d, f) for f in os.listdir(d) if '_pearl_' in f and f.endswith('.s')})
    return out


def sources(names):
    """{Black 2 item: sorted [(kind, where)]} of every TM/HM."""
    mach = names.machines
    get = collections.defaultdict(set)
    for r in pearl_items.world():
        if r['b2_item'] in mach:
            get[r['b2_item']].add(('hidden' if r['kind'] == 'hidden' else 'ball', gen_docs.place(r['zone'])))
    gift = re.compile(r'pl_SetVarFromValue PVAR_8004, (\d+)\s*// Pearl item \d+')
    lists = pearl_items.mart_special()
    for f, p in sorted(script_files().items()):
        src = open(p, encoding='utf-8').read()
        where = gen_docs.place(re.match(r'// (MAP_\w+)', src).group(1))
        for m in gift.finditer(src):
            if int(m.group(1)) in mach:
                get[int(m.group(1))].add(('gift', where))
        for n in re.findall(r'pl_PokeMartSpecial (\d+)', src):
            for i in lists[int(n)]:
                if tm_audit.pearl_item(i) in mach:
                    get[tm_audit.pearl_item(i)].add(('shop', where))
    table = re.search(r'sExchange\[41\]\[2\] = \{(.*?)\};', gen_docs.read('external/pokebw2/src/pearlb2/resident/tower.c'), re.S)
    for it, bp in re.findall(r'\{ (\d+), (\d+) \}', table.group(1)):
        if int(it) in mach:
            get[int(it)].add(('exchange', f'{bp} BP, Battle Park Exchange'))
    for h in ug_data.hideaways():
        for name, x, z in h['items']:
            if ug_data.item(name) in mach:
                get[ug_data.item(name)].add(('underground', h['pokemon']['name']))
    return {k: sorted(v) for k, v in get.items()}


def main(argv):
    names = gen_docs.Names()
    get = sources(names)
    label = lambda it: f'{names.machines[it][0]} {names.move(names.machines[it][1])}'
    twice, ug = [], []
    print(f'== {version.VERSION}')
    for it in sorted(get, key=lambda i: names.machines[i][2] if len(names.machines[i]) > 2 else i):
        once = [s for s in get[it] if s[0] in ONCE]
        if '--all' in argv or (once and len(get[it]) > 1):
            print(f'{label(it):24} ' + '; '.join(f'{k}: {w}' for k, w in get[it]))
        if once and len(get[it]) > 1:
            twice.append(it)
            if any(k == 'underground' for k, _ in get[it]):
                ug.append(it)
    print(f'{len(twice)} TMs/HMs come more than once; {len(ug)} of them from the Underground too: '
          + (', '.join(label(i) for i in ug) or 'none'))
    pearl = set(tm_audit.pearl_moves())
    b2 = [it for it in sorted(names.machines, key=lambda i: names.machines[i][2]) if names.machines[it][1] not in pearl]
    print("Black 2's own TMs/HMs: " + '; '.join(f'{label(it)} ({", ".join(w for _, w in get.get(it, [])) or "-"})' for it in b2))
    by_move = {m: it for it, (_, m, _) in names.machines.items()}
    none = [label(by_move[m]) for m in tm_audit.pearl_moves() if not get.get(by_move[m])]
    print('Pearl TMs/HMs with no source: ' + (', '.join(none) or 'none'))
    return 1 if '--strict' in argv and (ug or none) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
