"""What differs between Platinum and Pearl, zone by zone, by Platinum's zone name: Pearl's finished build is the base (notes/PLATINUM.md section 3),
so a zone part that matches stays Pearl's, fixes included, and only what this lists needs work.

    PEARL_VERSION=platinum python3 platinum_worklist.py     -> data/platinum/worklist.json, notes/PLATINUM_WORKLIST.md

Compares the two dumps in Pearl's numbers (platinum_maps.py): each land cell (attributes, props, terrain model, heights), the events, script
files, level scripts and text. `script` also says whether pearl_story keeps Pearl's generated file (src/) or writes a new one (work/platinum/src).
"""
import collections, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402
import gen4_text  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402
ROOT = version.ROOT
PEARL = os.path.join(ROOT, 'roms', 'pearl.nds')
PW = os.path.join(ROOT, 'work', 'pearl')
TW = version.WORLD_WORK


# Each place Pearl and Diamond differ: which Platinum is closer to, and what it uses. Where Platinum replaces the item, that's all it says.
SPLITS = [('24 wild tables, 127 fields', 'Mixed: Pearl 30 fields, Diamond 14, neither 83', "Platinum's own 183 tables"),
          ('Honey trees (encdata_ex)', 'Diamond: members 2, 3, 4; Pearl\'s labelled unused in its code', 'Diamond\'s members, from its own dump'),
          ('Pokédex text, banks 615 and 616', 'Neither: of 494 lines 277 match Diamond\'s, 275 Pearl\'s', "Platinum's own (slot 616)"),
          ('Spear Pillar maps', 'Neither: rebuilt, 39-51 tiles differ per chunk from each', "Platinum's own, both states"),
          ('Spear Pillar scripts and scene', 'Diamond\'s camera constants in code; our scene plays flashes', "Platinum's scripts"),
          ('22 version script lines', 'Replaced', "Platinum's text"),
          ('Personal data (held items of 6 species)', 'Diamond: it carries a byte-identical personal.narc, unused', "pl_personal.narc"),
          ('Rival name list', 'Diamond\'s side in the dump', 'Not shown in our intro; Barry by default'),
          ('Title, banner, icon', 'Replaced', 'Griseous Platinum draft'),
          ('Met game, game version', 'Replaced', '12'),
          ('Underground, Ramanas Park', 'Both, by the user\'s decision', 'version.BDSP "both"'),
          ('Everything else (maps, rooms, fixes, flags)', 'The two are the same there', "Pearl's, unless the zone is listed above")]


def parts(m):
    ta, pr, mo, bd = struct.unpack_from('<4I', m, 0)
    return m[16:16 + ta], m[16 + ta:16 + ta + pr], m[16 + ta + pr:16 + ta + pr + mo]


def land_row(a, b):
    """same | model (terrain model only) | props | ground_small (<= 30 tiles) | ground_big."""
    x, y = parts(a), parts(b)
    if x == y:
        return 'same'
    if x[0] == y[0]:
        return 'props' if x[1] != y[1] else 'model'
    return 'ground_small' if sum(x[0][i:i + 2] != y[0][i:i + 2] for i in range(0, len(x[0]), 2)) <= 30 else 'ground_big'


def main():
    assert version.PLATINUM, 'run with PEARL_VERSION=platinum'
    import pearl_story, gen4_extract
    pd = pearl_story.PearlData()
    pz = json.load(open(os.path.join(PW, 'zones.json')))
    tz = json.load(open(os.path.join(TW, 'zones.json')))
    P = Rom(PEARL); T = Rom(version.WORLD_DUMP)
    pland = narc_members(P.read('fielddata/land_data/land_data_release.narc'))
    tland = version.slotted('land', narc_members(T.read(version.ARCHIVE['land'])))
    pev = narc_members(P.read('fielddata/eventdata/zone_event_release.narc'))
    tev = version.slotted('events', narc_members(T.read(version.ARCHIVE['events'])))
    pfiles = narc_members(P.read('fielddata/script/scr_seq_release.narc'))
    penc = narc_members(P.read('fielddata/encountdata/p_enc_data.narc'))
    tenc = narc_members(T.read(version.ENCOUNTER_NARC))
    gen_scripts = set(os.listdir(pearl_story.SRC_SCRIPTS)) if os.path.isdir(pearl_story.SRC_SCRIPTS) else set()
    rows, totals = [], collections.Counter()
    for z in tz:
        p = pz[z['id']] if z['id'] < len(pz) else None
        r = {'id': z['id'], 'pearl_name': p and p['name'], 'platinum_name': z.get('pl_name'), 'installed': z['id'] in pd.b2_zone,
             'b2_zone': pd.b2_zone.get(z['id']), 'new': p is None}
        if p is None:
            rows.append(r)
            continue
        mt = json.load(open(os.path.join(TW, 'matrices', f'{z["matrix"]:03d}.json')))
        mp = json.load(open(os.path.join(PW, 'matrices', f'{p["matrix"]:03d}.json')))
        # only this zone's cells on the shared overworld
        cells = collections.Counter()
        same_shape = (mt['width'], mt['height']) == (mp['width'], mp['height'])
        for ry in range(mt['height']):
            for rx in range(mt['width']):
                c = mt['maps'][ry][rx]
                if c == 0xffff or (mt['headers'] and mt['headers'][ry][rx] != z['id']):
                    continue
                q = mp['maps'][ry][rx] if same_shape else 0xffff
                if q == 0xffff or q >= len(pland):
                    cells['new_cell'] += 1
                else:
                    cells[land_row(pland[version.land_id(q)], tland[c])] += 1
        r['land'] = dict(cells)
        ea, eb = gen4_extract.read_events(pev[p['events']]), gen4_extract.read_events(tev[z['events']])
        pos = lambda ev: collections.Counter((o['graphics_id'], o['x'], o['z']) for o in ev['object_events'])
        wp = lambda ev: collections.Counter((o['x'], o['z']) for o in ev['warp_events'])
        r['events_same'] = pev[p['events']] == tev[z['events']]
        r['objects'] = [len(ea['object_events']), len(eb['object_events']), sum((pos(ea) & pos(eb)).values())]
        r['warps'] = [len(ea['warp_events']), len(eb['warp_events']), sum((wp(ea) & wp(eb)).values())]
        r['script_same'] = pfiles[p['scripts']] == pd.files[z['scripts']]
        r['level_same'] = pfiles[p['level_scripts']] == pd.files[z['level_scripts']]
        la, lb = gen4_text.bank_text(p['text_bank'], PEARL), gen4_text.bank_text(z['text_bank'])
        ca, cb = collections.Counter(la), collections.Counter(lb)
        r['lines'] = [len(la), len(lb), sum((ca & cb).values())]
        r['encounters_same'] = (p['encounters'] is None and z['encounters'] is None) or (
            p['encounters'] is not None and z['encounters'] is not None and penc[p['encounters']] == tenc[z['encounters']])
        for k in ('area', 'music_day', 'music_night', 'weather', 'camera', 'map_type', 'battle_bg', 'mapsec'):
            if p[k] != z[k]:
                r.setdefault('header', {})[k] = [p[k], z[k]]
        base = f'{pd.script_file(z):04d}_pearl_{pearl_story.slug(z["name"])}.s'
        r['script_source'] = 'generated' if base in gen_scripts else 'pearl'
        work = []
        if any(k != 'same' for k in cells):
            work.append('map: ' + ', '.join(f'{v} {k}' for k, v in sorted(cells.items()) if k != 'same'))
        if not r['events_same']:
            work.append(f'events: objects {r["objects"][0]} -> {r["objects"][1]} ({r["objects"][2]} same place), warps {r["warps"][0]} -> {r["warps"][1]}')
        if not r['script_same'] or not r['level_same']:
            work.append('script')
        if r['lines'][1] != r['lines'][2] and pd._shows_lines(z['scripts']):
            work.append(f'text: {r["lines"][1] - r["lines"][2]} of {r["lines"][1]} lines new')
        if not r['encounters_same']:
            work.append('wild')
        if 'header' in r:
            work.append('header: ' + ', '.join(r['header']))
        r['work'] = work
        rows.append(r)
        if r['installed']:
            totals['zones'] += 1
            totals['nothing to do'] += not work
            totals['map'] += any(w.startswith('map') for w in work)
            totals['events'] += any(w.startswith('events') for w in work)
            totals['script changed'] += 'script' in work
            totals['text'] += any(w.startswith('text') for w in work)
            totals['wild'] += 'wild' in work
            totals['keeps Pearl\'s script file'] += r['script_source'] == 'pearl'
    json.dump(rows, open(version.data_out('worklist.json'), 'w'), indent=0)
    lines = ['# Platinum against Pearl, zone by zone', '',
             'Generated by `PEARL_VERSION=platinum python3 b2tools/platinum_worklist.py`; don\'t edit. Pearl\'s build is the base: what isn\'t listed stays Pearl\'s, fixes included. '
             'See notes/PLATINUM.md section 3. Per-zone data: `data/platinum/worklist.json`.', '',
             '| Installed shared zones | ' + ' | '.join(totals) + ' |', '|---|' + '---|' * len(totals),
             '| | ' + ' | '.join(str(v) for v in totals.values()) + ' |', '']
    lines += ['## Pearl or Diamond, where they split', '',
              'Pearl is the base by default. Platinum\'s code paths follow Diamond; its content doesn\'t clearly follow either (measured in work/platinum/base_game.py in the main tree, and here).', '',
              '| Split (notes/DIAMOND.md) | Closer to Platinum | What Platinum uses |', '|---|---|---|'] + [f'| {a} | {b} | {c} |' for a, b, c in SPLITS] + ['']
    lines += ['## Zones that need work', '', '| Zone | Pearl name | Black 2 zone | Script file | What differs |', '|---|---|---|---|---|']
    for r in rows:
        if r.get('work') and r['installed']:
            lines.append(f"| {r['id']} {r['platinum_name'][4:]} | {r['pearl_name'][4:]} | {r['b2_zone']} | {r['script_source']} | {'; '.join(r['work'])} |")
    lines += ['', '## New zones (ids 685 + id - 559)', '', '| Zone | Name | Black 2 zone |', '|---|---|---|']
    for r in rows:
        if r['new']:
            lines.append(f"| {r['id']} | {r['platinum_name'][4:]} | {r['b2_zone'] or 'placeholder, nothing installed'} |")
    open(os.path.join(ROOT, 'notes', 'PLATINUM_WORKLIST.md'), 'w').write('\n'.join(lines) + '\n')
    print(dict(totals))
    print('unmatched text edits:', len(gen4_text.UNMATCHED_EDITS))


if __name__ == '__main__':
    main()
