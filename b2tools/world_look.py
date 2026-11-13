"""Offline look of an overworld place as the build installs it (Platinum step 3, 2026-11-02): what the screen shows at
midday from the player's camera, for checking ground, seams, holes, textures and props without a ROM or an emulator.

    python3 world_look.py shot CHUNK TX,TZ SEASON OUT.png [--scale N] [--cracks PX] [--decals 0]
    python3 world_look.py sheet OUT.png CHUNK TX,TZ [SEASONS] [--label TEXT]      seasons 0-3 (default "13": summer, winter)
    python3 world_look.py top CHUNK SEASON OUT.png                                 the whole chunk from above (no props)

CHUNK is a land slot of the version's world (Pearl's numbers; work/<world>/land), TX,TZ a tile of it. Everything is the
build's own code, called as the patches call it: each chunk of the 3 x 3 around the target through pearl_chunk.fix_model
with its matrix-0 neighbours (the cracks and flicker fixes, Black 2's water and grass), season_decals.decorate (snow
patches, leaf clusters, ribbons: not in the north), the placed props (b2_look.placed_props; signs as Pearl's own models),
the zone's area texture set of the season as sinnoh_reskin.reskin_sets + season_decals.add_textures build it (Black 2 loads
one set per zone and draws every chunk with it). Camera: Black 2's camera 0 at Pearl's pitch (maplook 'tilt', the
default): distance 237, 59 degrees, vertical half-angle 20, on the tile's ground. Midday: Black 2's light saturates to
white on these materials (notes/MAP_LOOK.md), so lit polygons show their texture colours; edge marking in Pearl's outdoor
outline colour (4,4,4); the clear colour is black (maplook.outdoor_light). --cracks PX shrinks every polygon PX pixels
(pearl_render's stand-in for the DS's 1-pixel cracks): black there is a hole to the clear colour.

To compare with an older pipeline, run this file from that tree (copy it into its b2tools): it only calls the tree's own
modules. Pictures go where OUT says; nothing in the tree is written.
"""
import functools, json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import version  # noqa: E402
from version import land_id  # noqa: E402

DIST, PITCH, HALF = 237.0, 59.0, 20.0
SEASONS = ('spring', 'summer', 'autumn', 'winter')
NOON = dict(lights=[((31, 31, 31), (0, -4096, 0)), None, None, None],
            mat=((31, 31, 31), (31, 31, 31), (0, 0, 0), (31, 31, 31)), own=False)
EDGES = [0x1084] * 8                     # Pearl's outdoor outlines: every ID group (4,4,4)


@functools.lru_cache(maxsize=None)
def world():
    return json.load(open(version.data_path('sinnoh_world.json')))


@functools.lru_cache(maxsize=None)
def matrix():
    return json.load(open(os.path.join(version.WORLD_WORK, 'matrices', '000.json')))


@functools.lru_cache(maxsize=None)
def cell_of(chunk):
    """(x, z) of the chunk's first matrix-0 cell (as sinnoh_world converts it)."""
    m = matrix()
    for z in range(m['height']):
        for x in range(m['width']):
            if m['maps'][z][x] == chunk: return x, z
    raise SystemExit(f'chunk {chunk} is not on matrix 0')


def area_at(x, z):
    """(Pearl area number, its sinnoh_world area) of the zone at matrix cell (x, z), or of the nearest zoned cell."""
    m, w = matrix(), world()
    zones = {int(k): v for k, v in w['zones'].items()}
    best = None
    for zz in range(m['height']):
        for xx in range(m['width']):
            h = m['headers'][zz][xx]
            if h in zones:
                d = (xx - x) ** 2 + (zz - z) ** 2
                if best is None or d < best[0]: best = (d, zones[h]['pearl_area'])
    pa = best[1]
    return pa, w['areas'][str(pa)]


@functools.lru_cache(maxsize=None)
def texture_sets():
    """{a/0/1/4 index: BTX0} of every overworld area group and season, as sinnoh_reskin + season_decals install them."""
    import maplook, sinnoh_reskin, season_decals
    sets, _ = sinnoh_reskin.reskin_sets(maplook.texture_fixes(maplook.fixes()))
    for pa, a in world()['areas'].items():
        if int(pa) != season_decals.NORTH_AREA:
            season_decals.add_textures(sets, a['b2_area_group'])
    return sets


@functools.lru_cache(maxsize=None)
def textures(index):
    import pearl_render
    return pearl_render.textures(texture_sets()[index])


@functools.lru_cache(maxsize=None)
def chunk_model(chunk, decals=True):
    """The chunk's model as the build installs it on matrix 0 (fix_model, then the season decals)."""
    import pearl_chunk, pearl_mesh
    x, z = cell_of(chunk)
    bmd, _ = pearl_chunk.fix_model(chunk, around=pearl_chunk.neighbours(matrix(), x, z))
    if decals:
        import season_decals
        pa, _ = area_at(x, z)
        if pa != season_decals.NORTH_AREA:
            land = json.load(open(os.path.join(version.WORLD_WORK, 'land', f'{land_id(chunk):03d}.json')))
            tpl = json.load(open(os.path.join(ROOT, 'data', 'season_ribbons.json')))['chunks']
            props = land['props']
            room = season_decals.CHUNK_MAX - (20 + len(bmd) + 8196 + 4 + 16 * len(props))
            bmd, _ = season_decals.decorate(bmd, land, x, z, tpl, budget=room)
    return pearl_mesh.Model(bmd)


@functools.lru_cache(maxsize=None)
def _build():
    from gen4rom import Rom, narc_members
    return narc_members(Rom(version.WORLD_DUMP).read('fielddata/build_model/build_model.narc'))


@functools.lru_cache(maxsize=None)
def prop_model(mid):
    import pearl_mesh, pearl_buildings, pearl_render
    b = _build()[mid]
    try:
        return pearl_mesh.Model(pearl_buildings.mdl_only(b)), pearl_render.textures(pearl_buildings.btx0_of(b))
    except Exception:
        return None


def draw(scene, model, tex, offset=(0.0, 0.0, 0.0), rot_y=0.0, setup=NOON):
    """pearl_render.draw_model with a rotation about y (props: 0x10000 = 360 degrees)."""
    import pearl_render
    if not rot_y:
        return pearl_render.draw_model(scene, model, tex, offset=offset, setup=setup)
    a = rot_y / 65536 * 2 * math.pi
    c, s = math.cos(a), math.sin(a)
    proj = scene.project
    off = np.array(offset, float)
    def rotated(P):
        Q = P - off
        R = np.stack([c * Q[:, 0] + s * Q[:, 2], Q[:, 1], -s * Q[:, 0] + c * Q[:, 2]], 1)
        return proj(R + off)
    scene.project = rotated
    try:
        pearl_render.draw_model(scene, model, tex, offset=offset, setup=setup)
    finally:
        scene.project = proj


def ground_y(chunk, tx, tz):
    import pearl_chunk
    s = pearl_chunk.surface(pearl_chunk.triangles(chunk), tx * 16 - 248, tz * 16 - 248)
    return s[0] if s else 0.0


def shot(chunk, tx, tz, season, scale=1, cracks=0.0, decals=True, props=True):
    """PIL image: the view from the player's camera at tile (tx, tz) of chunk, at midday in the season."""
    import pearl_render, b2_look
    cx, cz = cell_of(chunk)
    pa, area = area_at(cx, cz)
    tex = textures(area['b2_area_group'] + season)
    x, z = tx * 16 - 248, tz * 16 - 248
    y = ground_y(chunk, tx, tz)
    p = math.radians(PITCH)
    eye = (x, y + DIST * math.sin(p), z + DIST * math.cos(p))
    sc = pearl_render.Scene(256 * scale, 192 * scale, eye, (x, y, z), half=HALF, shrink=cracks * scale)
    m = matrix()
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            X, Z = cx + dx, cz + dz
            if not (0 <= X < m['width'] and 0 <= Z < m['height']) or m['maps'][Z][X] == 0xffff: continue
            c = m['maps'][Z][X]
            off = (512.0 * dx, 0.0, 512.0 * dz)
            draw(sc, chunk_model(c, decals), tex, off)
            if not props: continue
            land = json.load(open(os.path.join(version.WORLD_WORK, 'land', f'{land_id(c):03d}.json')))
            for pr in b2_look.placed_props(c, land['props']):
                pm = prop_model(pr['model'])
                if pm is None: continue
                pos = (pr['pos'][0] + off[0], pr['pos'][1], pr['pos'][2] + off[2])
                draw(sc, pm[0], pm[1], pos, pr['rot'][1] % 0x10000)
    return sc.image(EDGES, (0, 0, 0))


def top(chunk, season):
    """The whole chunk's fixed model from above (orthographic, nearly straight down), no props."""
    import pearl_render
    cx, cz = cell_of(chunk)
    pa, area = area_at(cx, cz)
    tex = textures(area['b2_area_group'] + season)
    p = math.radians(80)
    sc = pearl_render.Scene(1024, 1024, (0, 1000 * math.sin(p), 1000 * math.cos(p)), (0, 0, 0),
                            half=math.degrees(math.atan(256 / 1000)), ortho=True)
    draw(sc, chunk_model(chunk), tex)
    return sc.image(EDGES, (0, 0, 0))


def sheet(out, chunk, tx, tz, seasons=(1, 3), label='', scale=1):
    from PIL import Image, ImageDraw
    ims = [shot(chunk, tx, tz, s, scale) for s in seasons]
    w, h = ims[0].size
    S = Image.new('RGB', (len(ims) * (w + 4), h + 14), (0, 0, 0))
    d = ImageDraw.Draw(S)
    for k, (s, im) in enumerate(zip(seasons, ims)):
        S.paste(im, (k * (w + 4), 14))
        d.text((k * (w + 4) + 2, 1), f'{label} {SEASONS[s]} ({chunk}: {tx},{tz})'.strip(), fill=(255, 255, 255))
    S.save(out)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = {a[i]: a[i + 1] for i in range(len(a)) if a[i].startswith('--') and i + 1 < len(a)}
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and not (i and a[i - 1].startswith('--'))]
    if not pos: raise SystemExit(__doc__)
    if pos[0] == 'shot':
        tx, tz = map(int, pos[2].split(','))
        im = shot(int(pos[1]), tx, tz, int(pos[3]), int(opt.get('--scale', 1)), float(opt.get('--cracks', 0)),
                  opt.get('--decals', '1') == '1')
        im.save(pos[4]); print(pos[4])
    elif pos[0] == 'sheet':
        tx, tz = map(int, pos[3].split(','))
        seasons = tuple(int(c) for c in (pos[4] if len(pos) > 4 else '13'))
        print(sheet(pos[1], int(pos[2]), tx, tz, seasons, opt.get('--label', ''), int(opt.get('--scale', 1))))
    elif pos[0] == 'top':
        top(int(pos[1]), int(pos[2])).save(pos[3]); print(pos[3])
    else:
        raise SystemExit(__doc__)
