"""The post-game's wild slots (notes/POSTGAME_DEX.md; the user, 2026-11-09): data/postgame_dex.json, which patches/wild.py
turns into the decomp's gPearlB2PostGame (src/pearlb2/resident/wild.c PearlB2_Wild_PostGameSlots).

    python3 b2tools/postgame_dex.py --write      write data/postgame_dex.json from the three versions' encounter files
    python3 b2tools/postgame_dex.py --check      compare the file with what --write would make (exit 1 if it differs)
    python3 b2tools/postgame_dex.py              print the lists

After the game clear (flag 2400), each entry's grass or surf slot, when it holds the entry's own species, is the entry's
other species half the time:
- the other version's exclusives (version.POSTGAME_OTHER): every slot of every installed zone where Diamond's and
  Pearl's files differ in the morning, day or night table or in surf (notes/DIAMOND.md 1.2 without its Poké Radar and
  GBA rows; no rod table differs): 52 entries each way;
- the Poké Radar's four (version.POSTGAME_RADAR: Stantler, Smeargle, Swellow, Loudred, which no version's build has
  otherwise; the Radar stays closed): its Radar slots 4, 5, 10, 11 (Pearl's pokeplatinum wild_encounters.c order) where
  the version's own file has the species in its Radar list, else where the other Diamond/Pearl version's file does
  (Diamond's Route 207 Radar has Larvitar: it takes Stantler at Pearl's Route 207). Slots 4-5 and 10-11 have no
  time-of-day change, so the day table's species is the one to match.
Made from work/pearl, work/diamond and work/platinum (gen4_extract), so a build needs only its own dump. Names, not
numbers: the build resolves zones (version.data_path('sinnoh_world.json')) and species (pokebw2's species.h).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402

OUT = os.path.join(ROOT, 'data', 'postgame_dex.json')
RADAR_SLOTS = (4, 5, 10, 11)
PERIODS = ('morning', 'day', 'night')


def _world(v):
    p = os.path.join(ROOT, 'data', 'platinum', 'sinnoh_world.json') if v == 'platinum' else \
        os.path.join(ROOT, 'data', 'sinnoh_world.json')
    w = json.load(open(p))
    zones = {int(k): z['name'] for k, z in w['zones'].items()}
    zones.update({int(k): z['name'] for k, z in w['rooms']['zones'].items()})
    return zones


def _file(v, n):
    return json.load(open(os.path.join(ROOT, 'work', v, 'encounters', f'{n:03d}.json')))


def _slots_module():
    import sinnoh_encounters as se
    return se


def lists(v):
    """(exclusive entries, radar entries) for version v: [zone name, group, slot, own species, other species, other form]."""
    se = _slots_module()
    zj = json.load(open(os.path.join(ROOT, 'work', v, 'zones.json')))
    zones = _world(v)
    other = version.POSTGAME_OTHER_BY[v]
    radar_names = ['SPECIES_' + s for s in version.POSTGAME_RADAR_BY[v]]
    excl, radar = {}, {}
    for zid, name in sorted(zones.items(), key=lambda kv: kv[1]):
        n = zj[zid]['encounters']
        if n is None:
            continue
        a = _file(v, n)
        b = _file(other, n) if other else None
        if a['land_rate']:
            if b is not None:
                for per in PERIODS:
                    for i, (x, y) in enumerate(zip(se.grass_slots(a, per), se.grass_slots(b, per))):
                        if x[0] != y[0]:
                            excl[(name, 'grass', i, x[0])] = (y[0], y[1])
            day = se.grass_slots(a, 'day')
            sources = [a] + ([b] if b is not None else [])
            for s in radar_names:
                src = next((f for f in sources if s in f['radar']), None)
                if src is None:
                    continue
                for k, r in enumerate(src['radar']):
                    if r == s:
                        i = RADAR_SLOTS[k]
                        radar[(name, 'grass', i, day[i][0])] = (s, 0)
        if a['surf_rate'] and b is not None:
            sa, sb = se.water_slots(a, 'surf_encounters'), se.water_slots(b, 'surf_encounters')
            for i, (x, y) in enumerate(zip(sa, sb)):
                if x[0] != y[0]:
                    excl[(name, 'surf', i, x[0])] = (y[0], y[1])
    # (a Radar species takes the version's own Radar places in a zone; the other version's only where its own file has
    # none there: Diamond's Stantler)
    return ([[*k, *v_] for k, v_ in sorted(excl.items())], [[*k, *v_] for k, v_ in sorted(radar.items())])


def make():
    out = {'_doc': [
        "Written by b2tools/postgame_dex.py --write (do not edit): the post-game's wild slots (notes/POSTGAME_DEX.md).",
        "Per version: entries [zone, group, slot, own species, other species, other form]: after the game clear, the",
        "zone's grass or surf slot, when it holds its own species, is the other species half the time (decomp",
        "resident/wild.c PearlB2_Wild_PostGameSlots). exclusives: the other version's slots; radar: the Poké Radar's four."]}
    for v in version.VERSIONS:
        excl, radar = lists(v)
        out[v] = {'other': version.POSTGAME_OTHER_BY[v], 'exclusives': excl, 'radar': radar}
    return out


def dumps(d):
    lines = ['{']
    keys = list(d)
    for ki, k in enumerate(keys):
        end = ',' if ki < len(keys) - 1 else ''
        if k == '_doc':
            lines.append(f' "_doc": {json.dumps(d[k], ensure_ascii=False)}{end}')
            continue
        lines.append(f' "{k}": {{')
        lines.append(f'  "other": {json.dumps(d[k]["other"])},')
        for gi, g in enumerate(('exclusives', 'radar')):
            rows = d[k][g]
            lines.append(f'  "{g}": [' + ('' if rows else ']' + (',' if gi == 0 else '')))
            for ri, r in enumerate(rows):
                lines.append('   ' + json.dumps(r) + (',' if ri < len(rows) - 1 else ''))
            if rows:
                lines.append('  ]' + (',' if gi == 0 else ''))
        lines.append(' }' + end)
    lines.append('}')
    return '\n'.join(lines) + '\n'


def load():
    return json.load(open(OUT))


if __name__ == '__main__':
    if '--write' in sys.argv:
        text = dumps(make())
        open(OUT + '.tmp', 'w').write(text)
        os.replace(OUT + '.tmp', OUT)
        d = json.loads(text)
        print(f'{OUT}: ' + ', '.join(f'{v} {len(d[v]["exclusives"])} + {len(d[v]["radar"])}' for v in version.VERSIONS))
    elif '--check' in sys.argv:
        ok = os.path.exists(OUT) and open(OUT).read() == dumps(make())
        print('postgame_dex.json: ' + ('as the encounter files make it' if ok else 'DIFFERS from what --write makes'))
        sys.exit(0 if ok else 1)
    else:
        d = make()
        for v in version.VERSIONS:
            print(f'== {v} (other {d[v]["other"]}): {len(d[v]["exclusives"])} exclusive slots, {len(d[v]["radar"])} radar')
            for r in d[v]['exclusives'] + d[v]['radar']:
                print('  ', r)
