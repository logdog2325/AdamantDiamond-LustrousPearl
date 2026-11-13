"""Platinum in Pearl's numbers (notes/PLATINUM.md section 3: Pearl's finished build is Platinum's base). Everything the tools and their
hand fixes name by a number of Pearl's dump (land file, matrix, event file, script file, text bank) means the same place in Platinum, so
data/*.json, the fixes in the generators and Pearl's generated files carry over. Platinum's archives are numbered their own way; this
finds, for each, which of Platinum's files fills each of Pearl's numbers, and gives what Pearl doesn't have numbers after Pearl's.

    PEARL_VERSION=platinum python3 platinum_maps.py      -> data/platinum/id_map.json (run before gen4_extract, gen4_land, gen4_script)

A map is {slot: Platinum's file}. Slots below Pearl's count are Pearl's numbers.
- Zones keep their numbers (559 shared). Matrices, events and scripts: a shared zone's file in Platinum takes that zone's number in Pearl,
  each slot once (zone order; the file most of a Pearl file's zones moved to wins, as with the empty script file 114 zones share).
- Land: the same cell of the same matrix slot, each slot once.
- Text banks: Platinum keeps Pearl's order with insertions, so the two lists are aligned by the lines they share; zones' banks and the
  common scripts' banks pin the alignment.
- zone_files: every shared zone's a/0/5/6 and a/0/0/3 numbers, computed by pearl_story as a Pearl run (so Pearl's src/ files keep theirs).
"""
import collections, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import version  # noqa: E402
import gen4_text  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402

ROOT = version.ROOT
PEARL_WORK = os.path.join(ROOT, 'work', 'pearl')
PEARL_DUMP = os.path.join(ROOT, 'roms', 'pearl.nds')
# pokediamond's LoadScriptsAndMessagesByMapId, as pearl_story keeps it (first id, script file, text bank)
PEARL_RANGES = [(10300, 977, 496), (10200, 373, 332), (10150, 1042, 562), (10100, 1041, 563), (10000, 375, 334),
                (9950, 376, 335), (9900, 365, 199), (9800, 206, 203), (9700, 387, 378), (9600, 377, 199),
                (9500, 464, 492), (9400, 391, 381), (9300, 372, 329), (9200, 388, 379), (9100, 0, 9),
                (9000, 207, 207), (8970, 390, 7), (8950, 463, 486), (8900, 389, 380), (8800, 462, 485),
                (8000, 374, 333), (7000, 370, 325), (5000, 1040, 199), (3000, 1040, 199), (2800, 378, 350),
                (2500, 1, 13), (2000, 205, 199)]
# Platinum inserted the Giratina forms' weight and height banks, which the alignment can't tell apart from the plain lists; 616: Platinum's
# own English Pokédex entries are what Pearl's entries' number holds (bank 699 is Pearl's old text, unused in English Platinum)
BANK_OVERRIDES = {619: 707, 620: 709, 616: 706}


def platinum_ranges():
    """[(first id, script file, text bank)] of Platinum's common scripts (its decomp's numbers, for pearl_story)."""
    import re
    P = os.path.join(ROOT, 'external', 'pokeplatinum')
    read = lambda *p: open(os.path.join(P, *p), encoding='utf-8').read()
    first = {m[0]: int(m[1]) for m in re.findall(r'#define SCRIPT_ID_OFFSET_(\w+)\s+(\d+)', read('include', 'script_manager.h'))}
    files = {n: i for i, n in enumerate(read('res', 'field', 'scripts', 'scripts.order').split())}
    banks = {n: i for i, n in enumerate(read('generated', 'text_banks.txt').split())}
    rows = re.findall(r'Entry\(SCRIPT_ID_OFFSET_(\w+),\s*(\w+),\s*(\w+)\)', read('src', 'script_manager.c'))
    return sorted({(first[o], files[f], banks[b]) for o, f, b in rows}, reverse=True)


def raw_zones(rom, n):
    import gen4_extract
    return gen4_extract.read_headers(rom, *gen4_extract.zone_names())[1][:n]


def bank_lines(path, narc):
    return [set(tuple(c) for c in gen4_text.decrypt_bank(m)) for m in narc_members(Rom(path).read(narc))]


def align(a, b, fixed):
    """{index in a: index in b}, monotonic, maximising the lines shared; `fixed` pairs must hold."""
    n, m = len(a), len(b)
    def score(i, j):
        s = len({x for x in a[i] if len(x) > 3} & b[j]) * 4 + 1 + (len(a[i]) == len(b[j]))
        if i in fixed:
            s = s + 10000 if fixed[i] == j else -10000
        return s
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best[i][j] = max(best[i + 1][j + 1] + score(i, j), best[i + 1][j], best[i][j + 1])
    out, i, j = {}, 0, 0
    while i < n and j < m:
        if best[i][j] == best[i + 1][j + 1] + score(i, j):
            out[i] = j; i += 1; j += 1
        elif best[i][j] == best[i + 1][j]:
            i += 1
        else:
            j += 1
    return out


def slots_by_zone(pz, tz, key, pearl_count, platinum_count, pins=()):
    """{slot: Platinum's file}: each Pearl file takes the Platinum file most of its zones moved to, once; then the other files after."""
    votes = collections.defaultdict(collections.Counter)
    for a, b in zip(pz, tz):
        votes[a[key]][b[key]] += 1
    out, taken = {}, set()
    for p, t in pins:
        out[p] = t; taken.add(t)
    for p in sorted(votes, key=lambda p: -sum(votes[p].values())):
        if p in out:
            continue
        for t, _ in votes[p].most_common():
            if t not in taken:
                out[p] = t; taken.add(t)
                break
    # Platinum's other files after Pearl's numbers; Pearl's numbers no zone uses keep the same-numbered file only if free
    nxt = pearl_count
    for t in range(platinum_count):
        if t not in taken:
            out[nxt] = t; nxt += 1
    return out


def land_map(pm, tm, matrix_slots):
    """{slot: Platinum's land file} by matrix cell. pm, tm: Pearl's and Platinum's matrices by file; matrix_slots: slot -> Platinum's file."""
    out, taken = {}, set()
    for slot in sorted(matrix_slots, key=lambda s: s != 0):       # the overworld first
        if slot >= len(pm):
            continue
        p, t = pm[slot], tm[matrix_slots[slot]]
        if (p['width'], p['height']) != (t['width'], t['height']):
            continue
        for ra, rb in zip(p['maps'], t['maps']):
            for ca, cb in zip(ra, rb):
                if ca != 0xffff and cb != 0xffff and ca not in out and cb not in taken:
                    out[ca] = cb; taken.add(cb)
    return out, taken


def main():
    assert version.PLATINUM, 'run with PEARL_VERSION=platinum'
    import gen4_extract
    P, T = Rom(PEARL_DUMP), Rom(version.WORLD_DUMP)
    pz = json.load(open(os.path.join(PEARL_WORK, 'zones.json')))
    tz = raw_zones(T, version.ZONE_COUNT)
    shared = tz[:len(pz)]
    pm = [gen4_extract.read_matrix(m) for m in narc_members(P.read('fielddata/mapmatrix/map_matrix.narc'))]
    tm = [gen4_extract.read_matrix(m) for m in narc_members(T.read('fielddata/mapmatrix/map_matrix.narc'))]
    n_land_p = len(narc_members(P.read('fielddata/land_data/land_data_release.narc')))
    n_land_t = len(narc_members(T.read('fielddata/land_data/land_data.narc')))
    n_scr_p = len(narc_members(P.read('fielddata/script/scr_seq_release.narc')))
    n_scr_t = len(narc_members(T.read('fielddata/script/scr_seq.narc')))
    n_ev_p = len(narc_members(P.read('fielddata/eventdata/zone_event_release.narc')))
    n_ev_t = len(narc_members(T.read('fielddata/eventdata/zone_event.narc')))
    ranges = {r[0]: r for r in platinum_ranges()}

    matrices = slots_by_zone(pz, shared, 'matrix', len(pm), len(tm), pins=[(0, 0)])
    for s, t in list(matrices.items()):                    # Pearl's matrices no zone names (their numbers stay free in Platinum too)
        pass
    land, taken = land_map(pm, tm, matrices)
    # Pearl's land files no matrix cell names (map replacements: the hidden paths, ...): the same bytes, else the nearest attributes
    pl = narc_members(P.read('fielddata/land_data/land_data_release.narc'))
    tl = narc_members(T.read('fielddata/land_data/land_data.narc'))
    free = [t for t in range(n_land_t) if t not in taken]
    for p in range(n_land_p):
        if p in land:
            continue
        same = next((t for t in free if tl[t] == pl[p]), None)
        if same is None:
            score = lambda t: sum(pl[p][16 + i:18 + i] == tl[t][16 + i:18 + i] for i in range(0, 2048, 2))
            best = max(free, key=score, default=None)
            same = best if best is not None and score(best) >= 900 else None
        if same is not None:
            land[p] = same; taken.add(same); free.remove(same)
    nxt = n_land_p
    for t in range(n_land_t):
        if t not in taken:
            land[nxt] = t; nxt += 1
    events = slots_by_zone(pz, shared, 'events', n_ev_p, n_ev_t, pins=[(0, 0)])
    pins = [(f, ranges[first][1]) for first, f, _ in PEARL_RANGES]
    pins = list(dict(pins).items())
    scripts = {}
    votes = collections.defaultdict(collections.Counter)
    for a, b in zip(pz, shared):
        votes[a['scripts']][b['scripts']] += 1
        votes[a['level_scripts']][b['level_scripts']] += 1
    taken_s = set()
    for p, t in pins:
        scripts[p] = t; taken_s.add(t)
    for p in sorted(votes, key=lambda p: -sum(votes[p].values())):
        if p not in scripts:
            for t, _ in votes[p].most_common():
                if t not in taken_s:
                    scripts[p] = t; taken_s.add(t)
                    break
    nxt = n_scr_p
    for t in range(n_scr_t):
        if t not in taken_s:
            scripts[nxt] = t; nxt += 1

    a = bank_lines(PEARL_DUMP, 'msgdata/msg.narc')
    b = bank_lines(version.WORLD_DUMP, 'msgdata/pl_msg.narc')
    fixed = {}
    for x, y in zip(pz, shared):
        if not x['name'].startswith(('MAP_UNUSED', 'MAP_UNKNOWN')):
            fixed.setdefault(x['text_bank'], y['text_bank'])
    pinned, last = {}, -1
    for k in sorted(fixed):
        if fixed[k] > last:
            pinned[k] = fixed[k]; last = fixed[k]
    banks = align(a, b, pinned)
    for first, f, bank in PEARL_RANGES:
        banks[bank] = ranges[first][2]
    banks.update(BANK_OVERRIDES)
    used = set()
    for k in sorted(banks):                                # (one Platinum bank fills one slot)
        if banks[k] in used:
            del banks[k]
        else:
            used.add(banks[k])
    nxt = len(a)
    for t in range(len(b)):
        if t not in used:
            banks[nxt] = t; nxt += 1

    # the zones' a/0/5/6 and a/0/0/3 numbers, as a Pearl run gives them
    code = ("import json,sys;sys.path[:0]=['.','patches'];import pearl_story as S;pd=S.PearlData();"
            "print(json.dumps({z['id']:[pd.script_file(z),pd.text_file(z)] for z in pd.zones}))")
    env = {k: v for k, v in os.environ.items() if k != 'PEARL_VERSION'}
    r = subprocess.run([sys.executable, '-c', code], cwd=HERE, env=env, capture_output=True, text=True, timeout=300)
    assert not r.returncode, r.stderr[-800:]
    zone_files = json.loads(r.stdout.splitlines()[-1])

    out = {'_doc': __doc__.split('\n\n')[0], 'land': land, 'matrices': matrices, 'events': events, 'scripts': scripts, 'banks': banks,
           'zone_files': zone_files, 'ranges': [[f, next(s for s, t in scripts.items() if t == sf), next(s for s, t in banks.items() if t == bk)]
                                                 for f, sf, bk in platinum_ranges()],
           'bank_names': {s: gen4_text.platinum_banks().get(t) for s, t in banks.items()}}
    path = version.data_out('id_map.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({k: ({str(a): b for a, b in sorted(v.items())} if isinstance(v, dict) else v) for k, v in out.items()}, open(path, 'w'), indent=0)
    moved = sum(s != t for s, t in land.items())
    print(f'{len(land)} land files ({moved} renumbered, {len(land) - n_land_p} past Pearl\'s), {len(matrices)} matrices, {len(events)} event files, '
          f'{len(scripts)} script files, {len(banks)} text banks -> {path}')


if __name__ == '__main__':
    main()
