"""Platinum's Villa in the Resort Area, its furniture (2026-11-02, plat-rooms; b2tools/villa_furniture.py has the how and
why). Platinum's build only: list it after sinnoh_rooms (which places the 23 places' props in the Villa's chunk and notes
where they start: work/world/platinum_villa.json) and secret_bases (which rewrites the gimmick table, keeping other rows).

apply(files)
- a/1/0/2: the Villa's zone gets gimmick 68 (the decomp's src/pearlb2/plat_rooms/villa.c, overlay 375).
apply_code(code)
- gPlatRoomsVilla (include/pearlb2/plat_rooms.h), in overlay 375's .data (code/arm9_ov375.bin): the zone, its chunk and
  first place's prop, the request work, each kind's flag, script and requirement, the 23 places, and the tiles A leaves
  to the room's sign events (the order form on the table).
Pearl and Diamond: nothing (the Villa is Platinum's).
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import version, narcio  # noqa: E402
import villa_furniture as V  # noqa: E402

GIMMICKS = 102                         # a/1/0/2: (zone, gimmick) u32 pairs
OVERLAY = 375
STATE = V.STATE
SKIPS, ROWS = 4, 16
REQ_ALWAYS, REQ_NEVER = 0xFFFE, 0xFFFF
SIZE = 444                             # sizeof(PlatRoomsVilla)


def _zone():
    w = json.load(open(version.data_path('sinnoh_world.json')))
    pid, z = next((int(k), z) for k, z in w['rooms']['zones'].items() if z['name'] == V.ZONE)
    return pid, z['b2_zone'], w['rooms']['chunks'][str(V.chunk())]


def _request_work():
    inc = os.path.join(ROOT, 'src', 'include', 'platinum', 'pearl.h')
    return int(re.search(r'#define PVAR_GIMMICK_REQUEST (0x[0-9A-Fa-f]+)', open(inc).read()).group(1), 16)


def table():
    """(gPlatRoomsVilla's bytes, a summary)."""
    import pearl_ids, pearl_story
    pid, b2, dat = _zone()
    state = json.load(open(STATE))
    assert state['chunk'] == V.chunk(), state
    ids = pearl_ids.Ids()
    furn = V.furniture()
    flags = [ids.flag_value(V.FLAG_FIRST + k) for k in range(len(V.KINDS))]
    scripts = [V.script(k) for k in range(len(V.KINDS))]
    pd = pearl_story.PearlData()
    signs = [(b['x'], b['z']) for b in pd.events(pd.zones[pid])['bg_events']]
    skip = [t for t in signs if any(f['solid'] and f['box'][0] <= t[0] <= f['box'][2] and f['box'][1] <= t[1] <= f['box'][3]
                                    for f in furn)]
    assert len(skip) <= SKIPS, skip
    assert all(f['box'][2] < 32 and f['box'][3] < ROWS for f in furn), 'a box past the gimmick\'s 32 x 16 tiles'
    blob = struct.pack('<4H', b2, dat, state['first_prop'], _request_work())
    blob += struct.pack('<20H', *flags) + struct.pack('<20H', *scripts)
    blob += struct.pack('<BB', V.TV, len(skip)) + b''.join(struct.pack('<BB', x, z) for x, z in skip)
    blob += bytes(2 * (SKIPS - len(skip))) + bytes(2)
    for k in range(len(V.KINDS)):
        what, record, least = V.REQUIREMENTS.get(k, (None, REQ_ALWAYS, 0))
        blob += struct.pack('<HHI', REQ_NEVER if record is None else record, 0, least)
    for f in furn:
        blob += struct.pack('<6B2x', f['kind'], f['solid'], *f['box'])
    assert len(blob) == SIZE, len(blob)
    return blob, dict(zone=b2, chunk=dat, first_prop=state['first_prop'], skip=skip)


def apply(files):
    if not version.PLATINUM:
        return 'platinum_villa: Platinum\'s only (nothing)'
    pid, b2, dat = _zone()
    rows = narcio.load(files, GIMMICKS)
    pairs = [struct.unpack_from('<II', rows[0], o) for o in range(0, len(rows[0]), 8)]
    pairs = [(z, g) for z, g in pairs if z != b2] + [(b2, V.GIMMICK)]
    rows[0] = b''.join(struct.pack('<II', z, g) for z, g in pairs)
    narcio.save(files, GIMMICKS, rows)
    return f'platinum_villa: zone {b2} gets gimmick {V.GIMMICK}'


def apply_code(code):
    if not version.PLATINUM:
        return 'platinum_villa: Platinum\'s only (nothing)'
    import decomp
    slot = decomp.symbol('gPlatRoomsVilla', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if slot is None or start is None:
        raise SystemExit('platinum_villa: the decomp has no gPlatRoomsVilla in overlay 375 (src/pearlb2/plat_rooms/villa.c)')
    blob, info = table()
    path = os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin')
    data = bytearray(open(path, 'rb').read())
    at = slot - start
    assert data[at:at + SIZE] == bytes(SIZE), f'gPlatRoomsVilla at {slot:#x} is not empty'
    data[at:at + SIZE] = blob
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(data)
    os.replace(path + '.tmp', path)
    return (f'platinum_villa: gPlatRoomsVilla {slot:#x} ({SIZE} B): zone {info["zone"]}, chunk {info["chunk"]}, props from '
            f'{info["first_prop"]}, the order form\'s tiles {info["skip"]}')


if __name__ == '__main__':
    blob, info = table()
    print(info, blob.hex())
