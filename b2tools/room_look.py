"""Offline look of a room zone (a cave, an outdoor room, a building) as the build installs it, any season (Platinum step 4,
2026-11-02; world_look.py does the overworld): what the screen shows at midday from the player's camera, for checking ground,
seams, holes, textures and props without a ROM or an emulator.

    python3 room_look.py shot ZONE TX,TZ SEASON OUT.png [--scale N] [--cracks PX]
    python3 room_look.py sheet OUT.png ZONE TX,TZ [SEASONS] [--label TEXT]       seasons 0-3 (default "13": summer, winter)
    python3 room_look.py top ZONE CX,CZ SEASON OUT.png                            one cell's chunk from above (no props)

ZONE: a Pearl zone id or name (MAP_AMITY_SQUARE, 253); TX,TZ a tile of the zone's matrix (Pearl's event coordinates). The
build's own code, called as sinnoh_rooms calls it: each chunk of the 3 x 3 cells round the tile through pearl_chunk.fix_model
in its first room matrix (the cracks and flicker fixes, the shifted nodes, Black 2's water and grass), the placed props
(b2_look.placed_props), the area's texture set: an outdoor room's (Pearl's day-cycle areas and the exterior ones) four
seasonal sets as sinnoh_reskin.reskin_sets makes them for sinnoh_rooms, an indoor one's b2_look.room_set (no seasons). Shapes
on translated nodes are drawn where the DS draws them. Camera: Black 2's camera 0 (237 away, vertical half-angle 20) at
the pitch the build gives the zone (maplook 'tilt', the default: its Pearl camera's pitch, 50.1 degrees in most buildings;
until 2026-11-07 this tool drew every room at the template's 53.2: PITCH = None now, a number forces one), on the tile's
ground. Midday light; the clear colour black. Season decals are an overworld
thing (season_decals): rooms have none.
"""
import functools, json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402
from version import land_id  # noqa: E402
import world_look  # noqa: E402

DIST, PITCH, HALF = 237.0, None, 20.0
SEASONS = world_look.SEASONS
GROUP = 2                                   # any seasonal group: the sets are made for this one (2-5)


@functools.lru_cache(maxsize=None)
def world():
    return json.load(open(version.data_path('sinnoh_world.json')))


def zone(name):
    """(Pearl zone id, its rooms row) by id or name."""
    rz = world()['rooms']['zones']
    if str(name) in rz: return int(name), rz[str(name)]
    want = name.upper() if name.upper().startswith('MAP_') else 'MAP_' + name.upper()
    for k, v in rz.items():
        if v['name'] == want: return int(k), v
    raise SystemExit(f'{name}: no room zone of that name or id')


@functools.lru_cache(maxsize=None)
def matrix(mid):
    return json.load(open(os.path.join(version.WORLD_WORK, 'matrices', f'{mid:03d}.json')))


@functools.lru_cache(maxsize=None)
def first_cells():
    """{chunk: (matrix, x, z)}: the room matrix sinnoh_rooms converts each chunk in (the first that holds it)."""
    out = {}
    for mid in world()['rooms']['matrices']:
        m = matrix(int(mid))
        for z in range(m['height']):
            for x in range(m['width']):
                c = m['maps'][z][x]
                if c != 0xffff and str(c) in world()['rooms']['chunks']: out.setdefault(c, (m, x, z))
    return out


@functools.lru_cache(maxsize=None)
def chunk_model(chunk):
    import pearl_chunk, pearl_mesh
    if chunk not in first_cells():                  # (an overworld chunk in a room's matrix: as sinnoh_world converts it)
        return world_look.chunk_model(chunk, False)
    m, x, z = first_cells()[chunk]
    bmd, _ = pearl_chunk.fix_model(chunk, around=pearl_chunk.neighbours(m, x, z))
    model = pearl_mesh.Model(bmd)
    model.shape_offsets = model.shape_translations()     # (the DS draws each shape where its node puts it)
    return model


def zone_pitch(pid):
    """The pitch (degrees) of the camera the build gives a room zone: Black 2's camera 0 at its Pearl camera's pitch
    (maplook.room_camera, 'tilt')."""
    import maplook
    zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    return maplook.PEARL_CAMERAS[zones[pid]['camera']][1] / 65536 * 360


def outdoor(pa):
    """Whether sinnoh_rooms gives the area four seasons (its day-cycle light, or an exterior area)."""
    import gen4rom, sinnoh_rooms
    field = sinnoh_rooms.pearl_light_field(gen4rom.Rom(version.WORLD_DUMP))
    return bool(field.get(pa)) or bool(world()['rooms']['areas'][str(pa)]['exterior'])


@functools.lru_cache(maxsize=None)
def texture_set(pa, season):
    import maplook, sinnoh_reskin, b2_look
    from gen4rom import Rom, narc_members
    a = world()['rooms']['areas'][str(pa)]
    if outdoor(pa):
        chunks = sorted({c for r in world()['rooms']['zones'].values() if r['pearl_area'] == pa
                         for row in matrix(r['pearl_matrix'])['maps'] for c in row if c != 0xffff})
        sets, _ = sinnoh_reskin.reskin_sets(maplook.texture_fixes(maplook.fixes()), {str(pa): dict(a, b2_area_group=GROUP)},
                                            chunks)
        if GROUP + season in sets: return sets[GROUP + season]
    texsets = narc_members(Rom(version.WORLD_DUMP).read('fielddata/areadata/area_map_tex/map_tex_set.narc'))
    return b2_look.room_set(texsets[a['pearl_texset']], pa)


@functools.lru_cache(maxsize=None)
def textures(pa, season):
    import pearl_render
    return pearl_render.textures(texture_set(pa, season))


def ground_y(chunk, tx, tz):
    import pearl_chunk
    s = pearl_chunk.surface(pearl_chunk.triangles(chunk), tx * 16 - 248, tz * 16 - 248)
    return s[0] if s else 0.0


def shot(name, tx, tz, season, scale=1, cracks=0.0, props=True):
    import pearl_render, b2_look
    pid, row = zone(name)
    m = matrix(row['pearl_matrix'])
    cx, cz = tx // 32, tz // 32
    chunk = m['maps'][cz][cx]
    tex = textures(row['pearl_area'], season)
    x, z = (tx % 32) * 16 - 248, (tz % 32) * 16 - 248
    y = ground_y(chunk, tx % 32, tz % 32)
    p = math.radians(PITCH if PITCH is not None else zone_pitch(pid))
    eye = (x, y + DIST * math.sin(p), z + DIST * math.cos(p))
    sc = pearl_render.Scene(256 * scale, 192 * scale, eye, (x, y + 4, z), half=HALF, shrink=cracks * scale)
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            X, Z = cx + dx, cz + dz
            if not (0 <= X < m['width'] and 0 <= Z < m['height']) or m['maps'][Z][X] == 0xffff: continue
            c = m['maps'][Z][X]
            off = (512.0 * dx, 0.0, 512.0 * dz)
            world_look.draw(sc, chunk_model(c), tex, off)
            if not props: continue
            land = json.load(open(os.path.join(version.WORLD_WORK, 'land', f'{land_id(c):03d}.json')))
            for pr in b2_look.placed_props(c, land['props']):
                pm = world_look.prop_model(pr['model'])
                if pm is None: continue
                world_look.draw(sc, pm[0], pm[1], (pr['pos'][0] + off[0], pr['pos'][1], pr['pos'][2] + off[2]),
                                pr['rot'][1] % 0x10000)
    return sc.image(world_look.EDGES, (0, 0, 0))


def top(name, cx, cz, season):
    import pearl_render
    pid, row = zone(name)
    chunk = matrix(row['pearl_matrix'])['maps'][cz][cx]
    p = math.radians(80)
    sc = pearl_render.Scene(1024, 1024, (0, 1000 * math.sin(p), 1000 * math.cos(p)), (0, 0, 0),
                            half=math.degrees(math.atan(256 / 1000)), ortho=True)
    world_look.draw(sc, chunk_model(chunk), textures(row['pearl_area'], season))
    return sc.image(world_look.EDGES, (0, 0, 0))


def sheet(out, name, tx, tz, seasons=(1, 3), label='', scale=1):
    from PIL import Image, ImageDraw
    pid, row = zone(name)
    seasons = seasons if outdoor(row['pearl_area']) else seasons[:1]
    ims = [shot(name, tx, tz, s, scale) for s in seasons]
    w, h = ims[0].size
    S = Image.new('RGB', (len(ims) * (w + 4), h + 14), (0, 0, 0))
    d = ImageDraw.Draw(S)
    for k, (s, im) in enumerate(zip(seasons, ims)):
        S.paste(im, (k * (w + 4), 14))
        d.text((k * (w + 4) + 2, 1), f'{label or row["name"][4:]} {SEASONS[s] if len(seasons) > 1 else ""} ({tx},{tz})',
               fill=(255, 255, 255))
    S.save(out)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = {a[i]: a[i + 1] for i in range(len(a)) if a[i].startswith('--') and i + 1 < len(a)}
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and not (i and a[i - 1].startswith('--'))]
    if not pos: raise SystemExit(__doc__)
    if pos[0] == 'shot':
        tx, tz = map(int, pos[2].split(','))
        shot(pos[1], tx, tz, int(pos[3]), int(opt.get('--scale', 1)), float(opt.get('--cracks', 0))).save(pos[4])
        print(pos[4])
    elif pos[0] == 'sheet':
        tx, tz = map(int, pos[3].split(','))
        seasons = tuple(int(c) for c in (pos[4] if len(pos) > 4 else '13'))
        print(sheet(pos[1], pos[2], tx, tz, seasons, opt.get('--label', ''), int(opt.get('--scale', 1))))
    elif pos[0] == 'top':
        cx, cz = map(int, pos[2].split(','))
        top(pos[1], cx, cz, int(pos[3])).save(pos[4]); print(pos[4])
    else:
        raise SystemExit(__doc__)
