"""Pearl's alternate zone music after story events (pokediamond arm9/src/unk_0205EC84.c sub_0205EF20, pokeplatinum
SystemFlag_GetAltMusicForHeader): e.g. Team Galactic's Eterna Building plays Eterna's song once the team has gone.

Black 2's own rule is the same idea (decomp src/system/field_sound.c GetZoneBGMOverrideID, its ZONE_WK_BGM_MAP), so the
decomp asks PearlB2_ZoneBGMOverride (resident/leftovers.c) first, with this table: gPearlB2AltMusic. Black 2's day
periods NIGHT and MIDNIGHT take the night song, as Pearl's IsNighttime. Pearl's songs reach Black 2's players through
Rowan's music question as every Pearl song does (music_choice's play shims).

    build_rom.py ... sinnoh_music ... music_choice ... pearl_alt_music

Platinum (2026-11-07, plat-music): its SystemFlag_GetAltMusicForHeader (pokeplatinum src/system_flags.c) is Pearl's rule row
for row: the same 12 flags (0x984-0x995), the same places under the same zone numbers (Platinum's names for them differ:
LAKE_VALOR_DRAINED is Pearl's LAKE_VALOR_GALACTIC, GALACTIC_HQ_CONTROL_ROOM its 4F_BACK, ...), the same songs (Platinum's own
bytes, as sinnoh_music installs every song from the version's archive). So RULES serve both; a Platinum build checks that
against the decomp's function (platinum_rules). Platinum's scripts set the same 10 of them (0x985 and 0x98A have no setter
in either game), through its own scripts' flag ids (data/platinum/pearl_story_ids.json).
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402

MUSIC = os.path.join(ROOT, 'work', 'world', 'music.json')
HQ = ['1F', '2F', '3F', '4F_1', 'B1F', 'B2F', '4F_BACK', '4F_2']
# (Pearl map, Pearl flag, day song, night song or None), Pearl's order: the first match wins
RULES = [('MAP_LAKE_VALOR_GALACTIC', 0x984, 'SEQ_D_LAKE', None),
         ('MAP_VALOR_CAVERN', 0x984, 'SEQ_D_RYAYHY', None),
         ('MAP_LAKE_VERITY_GALACTIC', 0x98E, 'SEQ_D_LAKE', None),
         ('MAP_LAKE_ACUITY_GALACTIC', 0x98F, 'SEQ_D_LAKE', None),
         ('MAP_PAL_PARK', 0x995, 'SEQ_D_SAFARI', None),
         ('MAP_SANDGEM_ROWANS_LAB', 0x993, 'SEQ_OPENING2', None)] + \
        [(f'MAP_VEILSTONE_GALACTIC_HEADQUARTERS_{f}', 0x985, 'SEQ_CITY07_D', 'SEQ_CITY07_N') for f in HQ] + \
        [('MAP_VEILSTONE_GALACTIC_HEADQUARTERS_1F', 0x986, 'SEQ_D_AGITO', None)] + \
        [(f'MAP_ETERNA_GALACTIC_BUILDING_{f}', 0x987, 'SEQ_CITY04_D', 'SEQ_CITY04_N') for f in ('1F', '2F', '3F', '4F')] + \
        [('MAP_VALLEY_WINDWORKS_INTERIOR', 0x988, 'SEQ_ROAD_C_D', 'SEQ_ROAD_C_N'),
         ('MAP_FLOAROMA_MEADOW', 0x989, 'SEQ_TOWN03_D', 'SEQ_TOWN03_N'),
         ('MAP_ROUTE_224', 0x98A, 'SEQ_TOWN03_D', 'SEQ_TOWN03_N'),
         ('MAP_POKEMON_LEAGUE_CYNTHIA_ROOM', 0x98B, 'SEQ_SILENCE_FIELD', None)]


def platinum_rules():
    """RULES as Platinum's SystemFlag_GetAltMusicForHeader has them: (zone name, flag, day song, night song or None), its
    order. Read from the decomp: its case labels (map header = zone number, named by our zones.json), CheckFlag's flag
    (generated/vars_flags.txt), and the songs (their .sseq names; SEQ_X_sseq_1 is the second sequence of that file)."""
    import pearl_ids
    pl = os.path.join(ROOT, 'external', 'pokeplatinum')
    src = open(os.path.join(pl, 'src', 'system_flags.c')).read()
    body = src[src.index('u16 SystemFlag_GetAltMusicForHeader('):]
    body = body[:body.index('\n}\n')]
    headers = [l.strip() for l in open(os.path.join(pl, 'generated', 'map_headers.txt')) if l.strip()]
    zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    flags = {name: n for n, name in pearl_ids.decomp_names().items() if isinstance(name, str)}
    seqs, count = {}, {}
    for e in json.load(open(os.path.join(pl, 'res', 'sound', 'pl_sound_data.json')))['seqInfo']:
        stem = e.get('fileName', '')[:-5]
        if stem:
            k = count.get(stem, 0); count[stem] = k + 1
            seqs.setdefault(f'{stem}_sseq' + (f'_{k}' if k else ''), e['name'])
    rows, cases, open_case, flag, branch, got = [], [], False, None, None, {}

    def close():
        for c in cases:
            if got:
                rows.append((zones[headers.index(c)]['name'], flag, got.get('day', got.get('any')), got.get('night')))
    for line in body.splitlines():
        t = line.strip()
        m = re.match(r'case (MAP_HEADER_\w+):', t)
        if m:
            if not open_case:
                close(); cases, flag, got, branch = [], None, {}, None
            cases.append(m.group(1)); open_case = True
            continue
        open_case = False
        if (m := re.match(r'if \(mapHeader == (MAP_HEADER_\w+)\)', t)):
            close(); cases, got = [m.group(1)], {}
        elif (m := re.search(r'CheckFlag\(varsFlags, (FLAG_\w+)\)', t)):
            flag = flags[m.group(1)]
        elif t.startswith('if (!IsNight())'):
            branch = 'day'
        elif t.startswith('} else {') and branch == 'day':
            branch = 'night'
        elif (m := re.match(r'sdatID = (\w+);', t)):
            got[branch or 'any'] = seqs[m.group(1)]
        elif t == 'break;' and branch == 'night':
            branch = None
    close()
    return rows


def table():
    """{u16 count, pad} then {u16 zone, flag, day, night} rows; flags only of Pearl's flags a script uses (the others
    can never be set: 0x985, 0x98A have no setter in Pearl's scripts)."""
    if version.PLATINUM:
        rules = platinum_rules()
        assert rules == RULES, f'pearl_alt_music: Platinum\'s rule is not RULES: {set(rules) ^ set(RULES)}'
    music = json.load(open(MUSIC))
    zones = {e['zone']: int(z) for z, e in music['zones'].items()}
    ids = json.load(open(version.data_path('pearl_story_ids.json')))['flags']
    rows, skipped = [], []
    for pmap, flag, day, night in RULES:
        k = f'0x{flag:04X}'
        if k not in ids:
            skipped.append(pmap)
            continue
        assert pmap in zones, f'{pmap}: no zone in {MUSIC}'
        d = music['songs'][day]['b2_seq']
        n = music['songs'][night]['b2_seq'] if night else d
        rows.append((zones[pmap], ids[k]['b2'], d, n))
    blob = struct.pack('<HH', len(rows), 0) + b''.join(struct.pack('<4H', *r) for r in rows)
    return blob, f'{len(rows)} zone rows' + (f', no setter in Pearl: {len(skipped)}' if skipped else '')


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2AltMusic', code)
    if slot is None:
        return 'pearl_alt_music: no gPearlB2AltMusic in this decomp'
    blob, summary = table()
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:
        resident.write(code, old, blob)
        base = old
    else:
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    return f'pearl_alt_music: {summary}, table {len(blob)} B at {base:#x}'


if __name__ == '__main__':
    print(table()[1])
