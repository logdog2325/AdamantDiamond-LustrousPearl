"""Platinum's Villa in the Resort Area: its furniture, read from the user's Platinum dump (2026-11-02, plat-rooms; step 4,
notes/PORT_AUDIT.md). What the build does with it: patches/platinum_villa.py (the gimmick's table, the zone's gimmick) and
the decomp's src/pearlb2/plat_rooms/villa.c (gimmick 68, overlay 375).

    PEARL_VERSION=platinum python3 b2tools/villa_furniture.py        prints the furniture and checks the tables

How Platinum does it (pokeplatinum src/overlay005/villa_furniture.c, ov5_021F6454.c, system_flags.c): 20 kinds of
furniture (VILLA_FURNITURE_TABLE .. _CHANDELIER), each owned by a flag (FLAG_VILLA_FURNITURE_START + kind, 0x997);
23 places (four house plants), each a kind, a position, and a box of solid tiles (or none: the music box, the wall clock,
the masterpiece, the tea set, the chandelier). On every field load the owned ones are loaded as map props (their models
are build models 559-578, t7_o01 .. t7_o20, in the Villa's area); the boxes block the player; A on a box's tile runs the
kind's script (the zone's scripts 0x15-0x28; the TV, 0x2774, only facing north: Platinum's TV broadcast). Buying one sets
its flag and warps into the room again, so the field reloads with it.

Here (the same behaviour on Black 2's field): sinnoh_rooms places all 23 as props of the Villa's chunk, after its own
(extra_props: their indices are fixed); gimmick 68 shows the owned ones and hides the rest (the platforms' way:
pearl_platforms_itcm.c), makes their boxes solid (a terrain layer) and runs the script on A (its step check). The TV runs
Black 2's TV (SCRID_TV 0x2922, which Black 2's own TV tiles run facing north). The room's chunk and zone are Pearl's slot
for Platinum's Villa: Pearl's Resort Area southwest house (MAP_RESORT_AREA_SOUTHWEST_HOUSE).
The tables are found by their contents in Platinum's overlay 5 (each search must match once).
"""
import functools, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

ZONE = 'MAP_RESORT_AREA_SOUTHWEST_HOUSE'       # Platinum's MAP_VILLA, in Pearl's slot
GIMMICK = 68                                  # PearlB2's gimmick ids: 59-64 Pearl's, 65-67 Platinum's Gyms (plat-gyms)
KINDS = ('table', 'big sofa', 'small sofa', 'bed', 'night table', 'TV', 'audio system', 'bookshelf', 'rack',
         'houseplant', 'PC desk', 'music box', 'Pokémon bust', 'Pokémon bust (silver)', 'piano', 'guest set',
         'wall clock', 'masterpiece', 'tea set', 'chandelier')
FLAG_FIRST = 0x997                            # FLAG_VILLA_FURNITURE_START
TV, PLATINUM_TV_SCRIPT, B2_TV_SCRIPT = 5, 0x2774, 0x2922
OVERLAY = 5
SLOTS = 23
FIRST_MODEL = 559                             # t7_o01
# The requirements before a kind is on the order form (ov5_021F6454.c ScrCmd_CheckMetFurnitureRequirements, by kind):
# (what, Black 2's record or None, at least). None: this game keeps no such count (yet): the kind stays off the form.
#   12 the Pokémon bust: a win in each of the Battle Frontier's five facilities (step 8, not built)
#   13 the silver bust: a silver print from any facility (step 8)
#   14 the piano: the Hall of Fame entered 10 times (Black 2's record 0x47, which its game clear counts)
#   15 the guest set: 50 battles at the Battleground (Platinum's RECORD_TIMES_BATTLED_AT_BATTLEGROUND: no count here)
#   16 the wall clock: 50 Berries planted (Platinum's RECORD_BERRIES_PLANTED: Pearl's patches count none here)
#   17 the masterpiece: 30 Eggs hatched (Black 2's record 30, egg_demo.c)
#   19 the chandelier: 300,000 steps (Black 2's record 0, fieldmap_event.c)
NEVER = 0xFFFF
REQUIREMENTS = {12: ('the Battle Frontier', None, 5), 13: ('a Frontier silver print', None, 1),
                14: ('Hall of Fame entries', 0x47, 10), 15: ('Battleground battles', None, 50),
                16: ('Berries planted', None, 50), 17: ('Eggs hatched', 30, 30), 19: ('steps', 0, 300000)}


@functools.lru_cache(maxsize=None)
def _overlay():
    from gen4rom import Rom
    rom = Rom(version.WORLD_DUMP)
    off, _ = struct.unpack_from('<II', rom.data, 0x50)
    fid, flags = struct.unpack_from('<2I', rom.data, off + 32 * OVERLAY + 24)
    assert not flags & 1, f'Platinum overlay {OVERLAY} is compressed'
    st, en = rom.fat[fid]
    return rom.data[st:en]


def _find_once(pat, what):
    d = _overlay()
    assert d.count(pat) == 1, f'{what}: {d.count(pat)} matches in Platinum\'s overlay {OVERLAY}'
    return d.index(pat)


@functools.lru_cache(maxsize=None)
def furniture():
    """[{kind, solid, x, y, z (units, the room's), box (left, top, right, bottom tiles)}] of the 23 places
    (sVillaFurnitures), checked against the model table (kind k: build model 559 + k) and the script table."""
    assert version.PLATINUM, 'the Villa is Platinum\'s'
    _find_once(struct.pack('<20I', *range(FIRST_MODEL, FIRST_MODEL + len(KINDS))), 'sVillaFurnitureModelIDs')
    _find_once(struct.pack('<20I', *[PLATINUM_TV_SCRIPT if k == TV else 0x15 + k for k in range(len(KINDS))]),
               'sVillaFurnitureScriptIDs')
    at = _find_once(struct.pack('<HHiii4h', 0, 1, 200 << 12, 0, 112 << 12, 11, 5, 13, 8), 'sVillaFurnitures')
    out = []
    for i in range(SLOTS):
        k, solid, x, y, z, l, t, r, b = struct.unpack_from('<HHiii4h', _overlay(), at + 24 * i)
        assert k < len(KINDS) and solid in (0, 1), (i, k, solid)
        out.append(dict(kind=k, solid=solid, x=x / 4096, y=y / 4096, z=z / 4096, box=(l, t, r, b)))
    return out


def model(kind):
    return FIRST_MODEL + kind


def script(kind):
    """The Black 2 script id A runs on a kind: the Villa file's own entry (Platinum's 0x15 + kind), Black 2's TV."""
    return B2_TV_SCRIPT if kind == TV else 0x15 + kind


@functools.lru_cache(maxsize=None)
def chunk():
    """The Villa's one chunk (Pearl's numbers), or None outside Platinum."""
    if not version.PLATINUM:
        return None
    w = json.load(open(version.data_path('sinnoh_world.json')))
    z = next(z for z in w['rooms']['zones'].values() if z['name'] == ZONE)
    sys.path.insert(0, os.path.join(HERE, 'patches'))
    import sinnoh_rooms
    m = sinnoh_rooms.load_matrix(z['pearl_matrix'])
    cells = {c for row in m['maps'] for c in row if c != 0xFFFF}
    assert len(cells) == 1 and m['width'] == m['height'] == 1, f'the Villa is one chunk: {cells}'
    return cells.pop()


def extra_props(c):
    """Pearl-style props of the 23 places for the Villa's chunk (sinnoh_rooms appends them after pearl_gimmicks'),
    every one placed: the gimmick hides the ones not owned. [] for any other chunk or version."""
    if not version.PLATINUM or c != chunk():
        return []
    return [dict(model=model(f['kind']), pos=[f['x'] - 256, f['y'], f['z'] - 256], rot=[0, 0, 0], scale=[1, 1, 1])
            for f in furniture()]


STATE = os.path.join(ROOT, 'work', 'world', 'platinum_villa.json')


def note_first_prop(index):
    """sinnoh_rooms: the Villa chunk's first place's prop is at this index of its props (work/world/platinum_villa.json,
    which patches/platinum_villa.py reads)."""
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump({'chunk': chunk(), 'first_prop': index}, open(STATE + '.tmp', 'w'))
    os.replace(STATE + '.tmp', STATE)


if __name__ == '__main__':
    for i, f in enumerate(furniture()):
        req = REQUIREMENTS.get(f['kind'])
        print(f'{i:2d} {KINDS[f["kind"]]:<22} model {model(f["kind"])} at ({f["x"]:5.0f}, {f["z"]:5.0f}) '
              f'{"box " + str(f["box"]) if f["solid"] else "no box":<22} script {script(f["kind"]):#x}'
              + (f'  needs {req[2]} {req[0]}' if req else ''))
    print('chunk', chunk(), 'extra props', len(extra_props(chunk())))
