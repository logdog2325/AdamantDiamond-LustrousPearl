"""People drawn into furniture: the upright depth (notes/MAP_LOOK.md "The upright depth", the decomp's
src/pearlb2/resident/people_depth.c). This patch only gives the code its table, gPearlB2PeopleDepth: by Black 2 zone id,
how far a person's z leans, in 256ths of a plane standing straight up at their feet; 0 draws as Black 2. No table
(the patch left out of the build's list) = Black 2's drawing everywhere.

data/people_depth.json is the switch: the slope of each kind of zone (rooms by Pearl's map type, the overworld) and of
single Pearl zones by name, so a version or a zone can leave or take it without touching the code.

    build_rom.py ... sinnoh_world sinnoh_rooms ... people_depth
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402


def slopes():
    """{Black 2 zone id: slope (1..255)} from data/people_depth.json."""
    cfg = json.load(open(os.path.join(ROOT, 'data', 'people_depth.json')))
    world = json.load(open(version.data_path('sinnoh_world.json')))
    zones = {z['id']: z for z in json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))}
    out = {}
    for pid, r in world['zones'].items():
        out[r['b2_zone']] = cfg['zones'].get(r['name'], cfg['overworld'])
    for pid, r in world['rooms']['zones'].items():
        kind = str(zones[int(pid)]['map_type'])
        out[r['b2_zone']] = cfg['zones'].get(r['name'], cfg['map_types'].get(kind, cfg['map_types']['default']))
    return {z: s for z, s in out.items() if s}


def table():
    """resident/people_depth.c's PeopleDepth: zone count, the margin, a pad byte, one slope per zone."""
    cfg = json.load(open(os.path.join(ROOT, 'data', 'people_depth.json')))
    s = slopes()
    count = max(s, default=-1) + 1
    return struct.pack('<HBB', count, cfg['margin_16ths'], 0) + bytes(s.get(z, 0) for z in range(count))


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2PeopleDepth', code)
    if slot is None:
        return 'people_depth: no gPearlB2PeopleDepth in this decomp: nothing installed'
    blob = table()
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:
        resident.write(code, old, blob)
    else:
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    return f'people_depth: {sum(1 for v in blob[4:] if v)} zones upright, {len(blob)} B'
