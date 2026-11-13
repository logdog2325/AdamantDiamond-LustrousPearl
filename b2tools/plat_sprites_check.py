"""Platinum's people's sheets (step 6, plat-sprites, 2026-11-07): offline checks and pictures. No ROM, no emulator.

    PEARL_VERSION=platinum python3 b2tools/plat_sprites_check.py [--out DIR] [--verbose]
        runs pearl_npc_sprites, pearl_amity_sprites and pearl_e4_doors on a copy of Black 2's a/0/4/7, a/0/4/8 and a/2/4/7
        (as the build does, in its order) and checks what Platinum's art went to:
        - every person (PLATINUM_PEOPLE, the redrawn Barry, Palmer, Buneary, Happiny): each Black 2 frame is the Platinum
          frame the layout names, pixel for pixel, 1 row lower; the 16 colours are Platinum's; nothing is cut off; the
          record is an ordinary walker's (scene node 2, controller 3, shadow), the sheet the code's alone;
        - every model (PLATINUM_MODELS): the record (a drawn 1 x 1 model, the file appended), the file Platinum's own
          byte for byte, the shards' one model the two halves' quads where Platinum draws them;
        and draws DIR/sheets/<who>.png (Platinum's 16 frames over Black 2's), DIR/models/<what>.png (the models' quads
        with their pictures, from the front and from above, on the tile grid), DIR/hq_hall.png (the HQ hall's crowd,
        row by row, from the camera's side), DIR/contact.png (everything, for the user). Exit 1 on a failed check.
    PEARL_VERSION=platinum python3 b2tools/plat_sprites_check.py --zones
        different sprites per installed zone (every person present, as platinum_events counts), billboard codes apart
        from models (Black 2's 32 materials hold billboards: npc_check.py), and the sheets' texture bytes; the busiest
    python3 b2tools/plat_sprites_check.py --codes
        Black 2 codes free for new walkers and models: nothing in a kept zone, script, table or C names them (as
        work/agents/plat-caves/tools/free_codes.py, plus the 12-frame records of other scene nodes, the sprite map's zone
        codes and the 3D-model codes)
    python3 b2tools/plat_sprites_check.py --versions [--base COMMIT]
        Pearl's and Diamond's a/0/4/7 and a/0/4/8 after the three patches, against the same at the base commit (default:
        the merge base with main): they must not change. One process at a time.
"""
import collections, glob, hashlib, json, os, re, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
VANILLA = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'b2_us', 'files')
ARCS = (47, 48, 247)                          # a/0/4/7 records, a/0/4/8 sheets and models, a/2/4/7 the PWT's table
OUT = os.path.join(ROOT, 'work', 'agents', 'plat-sprites')
SCALE = 3
VERBOSE = '--verbose' in sys.argv


def arc_rel(n):
    return os.path.join('a', str(n // 100), str(n // 10 % 10), str(n % 10))


def copy_files(where):
    for n in ARCS:
        os.makedirs(os.path.dirname(os.path.join(where, arc_rel(n))), exist_ok=True)
        shutil.copyfile(os.path.realpath(os.path.join(VANILLA, arc_rel(n))), os.path.join(where, arc_rel(n)))


def run_patches(files):
    import pearl_npc_sprites, pearl_amity_sprites, pearl_e4_doors
    return [pearl_npc_sprites.apply(files), pearl_amity_sprites.apply(files), pearl_e4_doors.apply(files)]


# ------------------------------------------------------------------------------------------------------------ pictures
def rgba(pal, v, clear=True):
    import sprites
    return (0, 0, 0, 0) if (v == 0 and clear) else sprites.bgr555_to_rgb(pal[v]) + (255,)


def frame_image(pix, w, h, pal, scale=SCALE, ground=None):
    from PIL import Image
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for i, v in enumerate(pix):
        if v:
            px[i % w, i // w] = rgba(pal, v)
    im = im.resize((w * scale, h * scale), Image.NEAREST)
    if ground is not None:                    # a tick at the feet row, both edges
        for x in (0, 1, w * scale - 2, w * scale - 1):
            for y in range(ground * scale, ground * scale + scale):
                im.putpixel((x, y), (220, 40, 40, 255))
    return im


def strip(images, labels, title, bg=(198, 214, 198, 255), pad=4):
    from PIL import Image, ImageDraw
    W = sum(i.width + pad for i in images) + pad
    H = max(i.height for i in images) + 30
    out = Image.new('RGBA', (max(W, 8 * len(title) + 8), H), bg)
    d = ImageDraw.Draw(out)
    d.text((pad, 2), title, fill=(0, 0, 0, 255))
    x = pad
    for im, lab in zip(images, labels):
        out.alpha_composite(im, (x, 14))
        d.text((x, 14 + im.height + 1), lab, fill=(60, 60, 60, 255))
        x += im.width + pad
    return out


def stack(rows, bg=(255, 255, 255, 255), gap=4):
    from PIL import Image
    out = Image.new('RGBA', (max(r.width for r in rows), sum(r.height + gap for r in rows)), bg)
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height + gap
    return out


PL_LABELS = [f'{d}{k}' for d in ('up', 'dn', 'lt', 'rt') for k in range(1, 5)]
B2_LABELS = {12: [f'{d}{k}' for d in ('up', 'dn', 'lt', 'rt') for k in ('s', '1', '2')],
             17: [f'{d}{k}' for d in ('up', 'dn', 'lt', 'rt') for k in ('s', '1', '2')] + ['x1', 'x2', 'x3', 'x4', 'x5']}


# ------------------------------------------------------------------------------------------------------------ models
def quads_of(bmd):
    """[(material index, [(x, y, z, s, t) map units and texels])] of a one-model BMD0, with its node's translation and
    scale (no rotation)."""
    import pearl_mesh, pearl_npc_sprites as ns
    blocks, ver = ns.bmd_blocks(bmd)
    m = ns.one_block_model(blocks['MDL0'], ver)
    tr, sc = ns.node_srt(m)
    out = []
    for s in m.shapes:
        for p in s.polys:
            out.append((s.material, [tuple(v[k] / 4096 * m.pos_scale * sc[k] + tr[k] for k in range(3)) + (v[3] / 16, v[4] / 16)
                                     for v in p]))
    return out, m


def render(quads, tex, view, box, scale=SCALE, untextured=(70, 70, 80, 255), tiles=True, mark=None):
    """A picture of textured quads, orthographic: view 'front' (x right, y up, nearer z on top) or 'top' (x right, z
    down). box = (x0, x1, a0, a1) in map units (a: y or z). tex = (w, h, pix, pal, clear) or None per material.
    The tile grid every 16 units; mark = (x0, x1, a0, a1) a rectangle drawn in red (the object's tile)."""
    from PIL import Image, ImageDraw
    x0, x1, a0, a1 = box
    W, H = int((x1 - x0) * scale), int((a1 - a0) * scale)
    im = Image.new('RGBA', (W, H), (232, 236, 232, 255))
    d = ImageDraw.Draw(im)
    if tiles:
        for gx in range(int(x0 // 16) * 16, int(x1) + 1, 16):
            d.line([((gx - x0) * scale, 0), ((gx - x0) * scale, H)], fill=(200, 205, 200, 255))
        for ga in range(int(a0 // 16) * 16, int(a1) + 1, 16):
            yy = (a1 - ga) * scale if view == 'front' else (ga - a0) * scale
            d.line([(0, yy), (W, yy)], fill=(200, 205, 200, 255))
    depth = {}
    px = im.load()
    for mat, q in quads:
        t = tex.get(mat)
        span = max(max(abs(q[i][k] - q[(i + 1) % 4][k]) for k in range(3)) for i in range(4))
        n = int(span * scale * 1.5) + 4                # samples per side: more than one per output pixel
        for i in range(n):
            for j in range(n):
                a, b = (i + 0.5) / n, (j + 0.5) / n
                P = [(1 - a) * (1 - b) * q[0][k] + a * (1 - b) * q[1][k] + a * b * q[2][k] + (1 - a) * b * q[3][k]
                     for k in range(5)]
                x, y, z, s, tt = P
                if view == 'front':
                    X, Y, Dp = (x - x0) * scale, (a1 - y) * scale, z
                else:
                    X, Y, Dp = (x - x0) * scale, (z - a0) * scale, y
                X, Y = int(X), int(Y)
                if not (0 <= X < W and 0 <= Y < H):
                    continue
                if t is None:
                    c = untextured
                else:
                    w, h, pix, pal, clear = t
                    v = pix[int(tt) % h * w + int(s) % w]
                    if v == 0 and clear:
                        continue
                    c = rgba(pal, v, clear)
                if depth.get((X, Y), -1e9) <= Dp:
                    depth[(X, Y)] = Dp
                    for dx in range(scale):
                        for dy in range(scale):
                            if X + dx < W and Y + dy < H:
                                px[X + dx, Y + dy] = c
    if mark:
        mx0, mx1, ma0, ma1 = mark
        if view == 'front':
            r = [((mx0 - x0) * scale, (a1 - ma1) * scale), ((mx1 - x0) * scale, (a1 - ma0) * scale)]
        else:
            r = [((mx0 - x0) * scale, (ma0 - a0) * scale), ((mx1 - x0) * scale, (ma1 - a0) * scale)]
        d.rectangle(r, outline=(220, 40, 40, 255))
    return im


def textures_of(bmd, model):
    """{material index: (w, h, pix, pal, clear)} for a model whose textured material uses its one texture (the
    materials with no texture: None)."""
    import pearl_npc_sprites as ns
    name, w, h, pix, pal, clear = ns.model_texture(bmd)
    d = model.data
    out = {}
    for k, at in enumerate(model.mat_at):
        # NNSG3dResMatData: origWidth (+0x20) is 0 when the material has no texture
        out[k] = (w, h, pix, pal, clear) if struct.unpack_from('<H', d, at + 0x20)[0] else None
    return out


# ------------------------------------------------------------------------------------------------------------ checks
class Report:
    def __init__(self):
        self.fail, self.ok = [], []

    def check(self, cond, text):
        (self.ok if cond else self.fail).append(text)
        return cond


def check_people(files, R, out_dir, contact):
    import version, narcio, sprites, pearl_npc_sprites as ns, pearl_amity_sprites as am
    from gen4rom import Rom, narc_members
    from pearl_player_sprites import shift, SHIFT_DOWN
    smap = ns.sprite_map()
    table = sprites.ow_table(files)
    vanilla = sprites.ow_table(VANILLA)
    sheets = narcio.load(files, sprites.ARC_OW_SHEETS)
    res1 = collections.Counter(r['res1'] for r in table)
    plat = narc_members(Rom(version.SOURCE_DUMP).read(ns.MMODEL))
    rows = [(w, g, m, t) for w, g, m, t in ns.PLATINUM_PEOPLE]
    rows += [(w, g, m, t) for w, g, m, t in ns.PEOPLE if g in ns.PLATINUM_REDRAWN]
    rows += [(w, g, m, t) for w, g, m, t in am.POKEMON if g in am.PLATINUM_REDRAWN]
    os.makedirs(os.path.join(out_dir, 'sheets'), exist_ok=True)
    for who, gfx, mid, tex in rows:
        code = smap[str(gfx)]['code']
        users = [k for k, v in smap.items() if isinstance(v, dict) and (v.get('code') == code
                                                                         or code in v.get('zone_codes', {}).values())]
        R.check(users == [str(gfx)], f'{who}: code {code} is graphics {gfx}\'s alone ({users})')
        fr, _, pal = sprites.btx_decode(plat[mid])
        fr = sorted(fr, key=lambda f: int(f[0].split('.')[-1]))
        R.check([f[0] for f in fr] == [f'{tex}.{k}' for k in range(1, 17)], f'{who}: Platinum\'s 16 frames ({tex})')
        rec = table[sprites.obj_record(code)]
        sheet = rec['res1']
        got, _, gpal = sprites.btx_decode(sheets[sheet])
        lay = ns.LAYOUT[len(got)]
        R.check(res1[sheet] == 1, f'{who}: sheet {sheet} is code {code}\'s alone')
        if gfx in ns.PLATINUM_REDRAWN or gfx in am.PLATINUM_REDRAWN:     # Pearl's code: its record as Pearl's build has it
            R.check(rec == vanilla[sprites.obj_record(code)], f'{who}: code {code}\'s record is Black 2\'s own')
        else:
            R.check((rec['entityType'], rec['sceneNodeType'], rec['spriteControllerType'], rec['shadow'], rec['billboardSize'])
                    == (1, 2, 3, 1, 0), f'{who}: code {code} is an ordinary walker (node {rec["sceneNodeType"]}, '
                    f'controller {rec["spriteControllerType"]}, shadow {rec["shadow"]})')
        R.check(gpal == pal, f'{who}: the sheet\'s 16 colours are Platinum\'s')
        bad = [j for j, (i, g) in enumerate(zip(lay, got)) if g[3] != shift(fr[i][3], SHIFT_DOWN)]
        R.check(not bad, f'{who}: every Black 2 frame is its Platinum frame, 1 row lower (wrong: {bad})')
        lost = [k for k, f in enumerate(fr) if any(f[3][31 * 32:])]
        R.check(not lost, f'{who}: nothing on Platinum\'s last row, so nothing is cut off by the shift ({lost})')
        top = strip([frame_image(f[3], 32, 32, pal, ground=29) for f in fr], PL_LABELS,
                    f'{who}: Platinum mmodel {mid} \'{tex}\' (16 frames, feet tick row 29)')
        bottom = strip([frame_image(g[3], 32, 32, gpal, ground=30) for g in got], B2_LABELS[len(got)],
                       f'Black 2 code {code}, sheet {sheet} ({len(got)} frames: frames {lay} of Platinum\'s; tick row 30)',
                       bg=(214, 206, 198, 255))
        pic = stack([top, bottom])
        pic.save(os.path.join(out_dir, 'sheets', re.sub(r'[^a-z0-9]+', '_', who.lower()).strip('_') + '.png'))
        contact.append((who, code, [fr[4][3], fr[0][3], fr[8][3], fr[12][3]], pal, [g[3] for g in got], gpal))


def hq_hall_crowd(files, R, out_dir, models):
    """The Galactic HQ hall's crowd from the camera's side (a front view, no perspective), one picture per row of tiles
    (z 3-17): left as Platinum draws it (its crowd models and its grunts' back view, 1 unit per pixel, from the ground),
    right as this build does (the crowd models and the Black 2 sheets' back view, both PERSON_SCALE units per pixel,
    from PERSON_BOTTOM: Black 2's billboard)."""
    import version, narcio, sprites, pearl_npc_sprites as ns
    from gen4rom import Rom, narc_members
    from PIL import ImageDraw
    ev = json.load(open(os.path.join(ROOT, 'external', 'pokeplatinum', 'res', 'field', 'events',
                                     'events_galactic_hq_hall.json')))
    smap = ns.sprite_map()
    gfx_ids = gfx_numbers()
    sheets = narcio.load(files, sprites.ARC_OW_SHEETS)
    table = sprites.ow_table(files)
    mm = narc_members(Rom(version.SOURCE_DUMP).read(ns.MMODEL))
    plat_models = {g: mm[member] for _, g, narc, member, _ in ns.PLATINUM_MODELS if g in ns.CROWD_GRUNTS}
    objs = [(gfx_ids[o['graphics_id']], o['x'], o['z']) for o in ev['object_events']]
    box = (7 * 16, 21 * 16, -4, 36)
    pics = []

    def person(gfx, code, build):
        """(texture, width, height of a 32 x 32 frame's quad, its bottom) of a single person: the back view."""
        if build:
            rec = table[sprites.obj_record(code)]
            fr, _, pal = sprites.btx_decode(sheets[rec['res1']])
            return (32, 32, fr[0][3], pal, 1), 32 * ns.PERSON_SCALE, ns.PERSON_BOTTOM + ns.SHIFT_DOWN * ns.PERSON_SCALE
        mid = {125: 104, 120: 99, 213: 376}.get(gfx, 103)       # (Platinum's sheets: grunts, Cyrus, Looker)
        fr, _, pal = sprites.btx_decode(mm[mid])
        fr = sorted(fr, key=lambda f: int(f[0].split('.')[-1]))
        return (32, 32, fr[0][3], pal, 1), 32, 0
    for z in sorted({z for _, _, z in objs}):
        row = []
        for build in (False, True):
            quads, tex = [], {}
            for g, x, zz in sorted((o for o in objs if o[2] == z), key=lambda o: o[1]):
                cx = x * 16 + 8
                code = smap[str(g)]['code']
                if g in ns.CROWD_GRUNTS:
                    bmd = models[g][1] if build else plat_models[g]
                    q, m = quads_of(bmd)
                    t = textures_of(bmd, m)[0]
                    key = len(tex); tex[key] = t
                    quads += [(key, [(v[0] + cx,) + v[1:] for v in qq]) for _, qq in q]
                else:
                    t, size, bottom = person(g, code, build)
                    key = len(tex); tex[key] = t
                    b0 = bottom                       # (the build's frames are already 1 row lower)
                    quads.append((key, [(cx - size / 2, b0, 0, 0, 32), (cx + size / 2, b0, 0, 32, 32),
                                        (cx + size / 2, b0 + size, 0, 32, 0), (cx - size / 2, b0 + size, 0, 0, 0)]))
            im = render(quads, tex, 'front', box)
            ImageDraw.Draw(im).text((2, 2), f'z {z} ' + ('this build' if build else 'Platinum'), fill=(0, 0, 0, 255))
            row.append(im)
        pics.append(strip(row, ['', ''], ''))
    out = stack(pics)
    out.save(os.path.join(out_dir, 'hq_hall.png'))
    R.check(True, f'HQ hall crowd drawn: {len(pics)} rows ({os.path.join(out_dir, "hq_hall.png")})')


def transparent(im):
    """The background colour of render() made clear (to lay one object over another)."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] == (232, 236, 232, 255):
                px[x, y] = (0, 0, 0, 0)
    return im


def gfx_numbers():
    """{OBJ_EVENT_GFX_ name: number} of Platinum (pokeplatinum generated/object_events_gfx.txt)."""
    out, v = {}, 0
    for line in open(os.path.join(ROOT, 'external', 'pokeplatinum', 'generated', 'object_events_gfx.txt')):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, _, val = line.partition('=')
        if val.strip():
            v = int(val.strip(), 0)
        out[name.strip()] = v
        v += 1
    return out


def check_models(files, R, out_dir, contact_models):
    import version, narcio, sprites, pearl_npc_sprites as ns
    from gen4rom import Rom, narc_members
    smap = ns.sprite_map()
    rec = narcio.load(files, sprites.ARC_OW_TABLE)[0]
    sheets = narcio.load(files, sprites.ARC_OW_SHEETS)
    rom = Rom(version.SOURCE_DUMP)
    narcs = {n: narc_members(rom.read(n)) for n in (ns.MMODEL, ns.FLDEFF)}
    models = ns.platinum_models()
    os.makedirs(os.path.join(out_dir, 'models'), exist_ok=True)
    seen = set()
    for who, gfx, narc, member, tex in ns.PLATINUM_MODELS:
        code = smap[str(gfx)]['code']
        at = 4 + 28 * sprites.obj_record(code)
        f = struct.unpack_from('<HBBBBBBBBBBBbbbHHHHH', rec, at)
        R.check(f[0] == code and f[1:15] == ns.MODEL_RECORD, f'{who}: code {code:#x} is a drawn 1 x 1 model record {f[:15]}')
        R.check(f[16:] == (0xFFFF,) * 4, f'{who}: code {code:#x} loads its model and nothing else')
        R.check(code in ns.FREE_MODELS and code not in seen, f'{who}: code {code:#x} is free and its own')
        seen.add(code)
        bmd = sheets[f[15]]
        R.check(bmd == models[gfx][1], f'{who}: a/0/4/8 file {f[15]} is the model')
        if isinstance(member, tuple):
            left, right = (narcs[narc][k] for k in member)
            want = quads_of(left)[0] + [(m, [(v[0] + ns.SHARDS_DX,) + v[1:] for v in q]) for m, q in quads_of(right)[0]]
            got = quads_of(bmd)[0]
            close = len(got) == len(want) and all(
                ma == mb and all(abs(a - b) < 0.01 for va, vb in zip(qa, qb) for a, b in zip(va, vb))
                for (ma, qa), (mb, qb) in zip(got, want))
            R.check(close, f'{who}: the one model draws both halves where Platinum does ({got} / {want})')
            R.check(ns.model_texture(bmd)[:4] == ns.model_texture(left)[:4], f'{who}: the picture is Platinum\'s')
        elif gfx in ns.CROWD_GRUNTS:
            check_crowd(R, who, gfx, bmd, narcs[narc][member], narcs[ns.MMODEL])
        else:
            R.check(bmd == narcs[narc][member], f'{who}: the model is Platinum\'s {narc.split("/")[-1]} {member}, byte for byte')
        if narc == ns.MMODEL and not isinstance(member, tuple):
            sheet_tex = {441: 411, 444: 412}[member]
            fr, _, pal = sprites.btx_decode(narcs[narc][sheet_tex])
            name, w, h, pix, mpal, clear = ns.model_texture(bmd)
            R.check((name, w, h, pix, mpal[:16]) == (fr[0][0], fr[0][1], fr[0][2], fr[0][3], pal),
                    f'{who}: the model\'s picture is Platinum\'s sheet {sheet_tex} \'{name}\' byte for byte')
        q, m = quads_of(bmd)
        tex = textures_of(bmd, m)
        xs = [v[0] for _, qq in q for v in qq]; ys = [v[1] for _, qq in q for v in qq]; zs = [v[2] for _, qq in q for v in qq]
        box = (min(min(xs), -8) - 8, max(max(xs), 8) + 8)
        front = render(q, tex, 'front', box + (min(min(ys), 0) - 4, max(ys) + 4), mark=(-8, 8, 0, 1))
        top = render(q, tex, 'top', box + (min(min(zs), -8) - 4, max(max(zs), 8) + 4), mark=(-8, 8, -8, 8))
        name = re.sub(r'[^a-z0-9]+', '_', who.lower()).strip('_')
        pic = stack([strip([front], ['front (x right, y up); red: the object\'s tile'], f'{who}: code {code:#x}'),
                     strip([top], ['from above (x right, z down)'], '')])
        pic.save(os.path.join(out_dir, 'models', name + '.png'))
        contact_models.append((who, code, front if max(ys) - min(ys) > 4 else top))
    return models


GRUNT_FRAMES = {'M': 103, 'F': 104}                   # Platinum's grunts (gingam, gingaw); frame 1 (index 0): back view


def colour_image(pix, pal, w, h):
    return [[pal[pix[y * w + x]] if pix[y * w + x] else None for x in range(w)] for y in range(h)]


def check_crowd(R, who, gfx, bmd, plat_bmd, mm):
    """The crowd model against Platinum's: the same TEX0, node and material; one quad per grunt of CROWD_GRUNTS, whose
    columns cover the picture's opaque columns once; each grunt's columns are its own back-view frame's pixels (by
    colour; the grunts' frame placement found here), at Black 2's person scale around its tile."""
    import sprites, pearl_npc_sprites as ns
    (bl, ver), (pb, _) = ns.bmd_blocks(bmd), ns.bmd_blocks(plat_bmd)
    R.check(bl['TEX0'] == pb['TEX0'], f'{who}: the picture (TEX0) is Platinum\'s byte for byte')
    m, pm = ns.one_block_model(bl['MDL0'], ver), ns.one_block_model(pb['MDL0'], ver)
    R.check(ns.node_srt(m) == ns.node_srt(pm) and m.data[m.mat_at[0]:m.mat_at[0] + 44] == pm.data[pm.mat_at[0]:pm.mat_at[0] + 44]
            and m.pos_scale == pm.pos_scale, f'{who}: node, material and scale are Platinum\'s')
    sbc = lambda mod: mod.data[mod.m + mod.osbc:mod.m + mod.omat]
    R.check(sbc(m) == sbc(pm) and b'\x07' in sbc(m)[:8], f'{who}: Platinum\'s render commands, its billboard (SBC BB) kept')
    name, w, h, pix, pal, clear = ns.model_texture(bmd)
    comp = colour_image(pix, pal, w, h)
    grunts = ns.CROWD_GRUNTS[gfx]
    cols = [c for c in range(w) if any(comp[y][c] for y in range(h))]
    covered = sorted(c for _, a, b in grunts for c in range(a, b + 1))
    R.check(covered == cols, f'{who}: the grunts\' columns cover the picture\'s {len(cols)} opaque columns once ({covered == cols})')
    frames = {}
    for g, mid in GRUNT_FRAMES.items():
        fr, _, fpal = sprites.btx_decode(mm[mid])
        fr = sorted(fr, key=lambda f: int(f[0].split('.')[-1]))
        frames[g] = colour_image(fr[0][3], fpal, 32, 32)
    (pq,), = [ps for _, ps in pm.shapes[0].groups]
    x0 = min(v[0] / 4096 * pm.pos_scale for v in pq)
    stray, odd = 0, []
    for k, a, b in grunts:
        tc = 16 * k - x0                         # the picture's column at the tile's centre
        best = None
        for g, f in frames.items():
            for u0 in range(int(tc) - 19, int(tc) - 12):
                hits = sum(1 for y in range(h) for x in range(a, b + 1) if comp[y][x] and 0 <= x - u0 < 32 and f[y][x - u0] == comp[y][x])
                if best is None or hits > best[0]:
                    best = (hits, g, u0)
        hits, g, u0 = best
        mine = [(y, x) for y in range(h) for x in range(a, b + 1) if comp[y][x]]
        miss = [(y, x) for y, x in mine if not (0 <= x - u0 < 32 and frames[g][y][x - u0] == comp[y][x])]
        stray += sum(1 for y, x in miss if any(0 <= x - u1 < 32 and frames[g1][y][x - u1] == comp[y][x]
                                               for _, g1, u1 in [(0, 'M', u0 - 16), (0, 'F', u0 - 16), (0, 'M', u0 + 16), (0, 'F', u0 + 16)]))
        odd += [f'tile {k}: {g} frame at {u0}, {len(miss)} of {len(mine)} pixels not its frame\'s {miss[:4]}']
    R.check(all(int(o.split(', ')[1].split(' of ')[0]) <= 4 for o in odd),
            f'{who}: each grunt\'s columns are its own back view ({"; ".join(odd)})')
    q, _ = quads_of(bmd)
    R.check(len(q) == len(grunts), f'{who}: one quad per grunt ({len(q)})')
    for (mat, qq), (k, a, b) in zip(q, grunts):
        xs, ys, ss = [v[0] for v in qq], [v[1] for v in qq], [v[3] for v in qq]
        tc = 16 * k - x0
        ok = (abs(min(xs) - (16 * k + (a - tc) * ns.PERSON_SCALE)) < 0.01 and abs(max(xs) - (16 * k + (b + 1 - tc) * ns.PERSON_SCALE)) < 0.01
              and abs(min(ys) - ns.PERSON_BOTTOM) < 0.01 and abs(max(ys) - (ns.PERSON_BOTTOM + 28)) < 0.01
              and (min(ss), max(ss)) == (a, b + 1))
        R.check(ok, f'{who}: grunt on tile {k}: columns {a}-{b} at x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}')


def contact_sheet(people, models, path):
    from PIL import Image, ImageDraw
    import sprites
    rows = []
    for who, code, plat4, pal, b2, gpal in people:
        ims = [frame_image(p, 32, 32, pal, scale=2) for p in plat4]
        ims2 = [frame_image(p, 32, 32, gpal, scale=2) for p in b2]
        sep = Image.new('RGBA', (8, 64), (0, 0, 0, 0))
        rows.append(strip(ims + [sep] + ims2, ['Pt dn', 'Pt up', 'Pt lt', 'Pt rt', ''] + B2_LABELS[len(b2)],
                          f'{who} (code {code}): Platinum\'s own frames, then the Black 2 sheet'))
    for who, code, im in models:
        rows.append(strip([im], [''], f'{who} (model code {code:#x})'))
    stack(rows).save(path)


def main_check(out_dir):
    import version
    assert version.PLATINUM, 'PEARL_VERSION=platinum'
    R = Report()
    with tempfile.TemporaryDirectory(dir=OUT) as t:
        copy_files(t)
        for line in run_patches(t):
            pass
        people, mods = [], []
        check_people(t, R, out_dir, people)
        models = check_models(t, R, out_dir, mods)
        hq_hall_crowd(t, R, out_dir, models)
        contact_sheet(people, mods, os.path.join(out_dir, 'contact.png'))
    for line in R.ok if VERBOSE else ():
        print('ok  ', line)
    for line in R.fail:
        print('FAIL', line)
    print(f'{len(R.ok)} checks passed, {len(R.fail)} failed; pictures in {out_dir}')
    return 1 if R.fail else 0


# ------------------------------------------------------------------------------------------------------------ zones
def main_zones(top=12):
    """Different sprites per installed zone, as sinnoh_story installs them (platinum_events' World and entities)."""
    import version, narcio, sprites, platinum_events as P
    from npc_check import tex_bytes
    assert version.PLATINUM, 'PEARL_VERSION=platinum'
    W = P.World()
    pe, pd, ids = W.pe, W.pd, W.ids
    with tempfile.TemporaryDirectory(dir=OUT) as t:
        copy_files(t)
        run_patches(t)
        table = sprites.ow_table(t)
        sheets = narcio.load(t, sprites.ARC_OW_SHEETS)

        def sheet_bytes(code):
            if 162 <= code <= 177:
                return 12320                  # a dynamic code: the rival's or the counterpart's player-sized sheet
            return tex_bytes(sheets[table[sprites.obj_record(code)]['res1']])
        import pearl_npc_sprites as ns
        smap = ns.sprite_map()
        new = {smap[str(g)]['code'] for _, g, _, _ in ns.PLATINUM_PEOPLE} | \
              {smap[str(m[1])]['code'] for m in ns.PLATINUM_MODELS} | {smap[str(g)]['code'] for g in ns.PLATINUM_REDRAWN}
        rows = []
        for zid in W.installed():
            zone = pd.zones[zid]
            try:
                npcs, _, _, _ = pe.entities(pd, zone, ids, W.heights, lambda s: W.ss.script_id(pd, ids, s))
            except Exception as e:                  # noqa: BLE001
                rows.append((zone['name'], -1, -1, 0, 0, str(e)[:60]))
                continue
            codes = {n['model'] for n in npcs}
            bill = {c for c in codes if c < 0x2000}
            rows.append((zone['name'], len(codes), len(bill), sum(sheet_bytes(c) for c in bill), len(npcs),
                         ' new: ' + ','.join(str(c) for c in sorted(codes & new)) if codes & new else ''))
    rows.sort(key=lambda r: (-r[2], -r[3]))
    print(f'{len(rows)} installed zones. Black 2: 32 billboard materials (the player\'s two included: 30 left), 64 actors.')
    print('zone | codes | billboard codes | their sheets (bytes) | people')
    for r in rows[:top]:
        print(f'{r[0][4:]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} {r[5]}')
    print('zones with Platinum\'s new or redrawn sheets, busiest first:')
    for r in [r for r in rows if r[5]][:top]:
        print(f'  {r[0][4:]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}{r[5]}')
    over = [r for r in rows if r[2] > 30 or r[4] > 63]
    print('over a limit:', over or 'none')
    by_bytes = sorted(rows, key=lambda r: -r[3])[:6]
    print('most sheet bytes:', ', '.join(f'{r[0][4:]} {r[3]}' for r in by_bytes))
    return 1 if over else 0


# ------------------------------------------------------------------------------------------------------------ codes
def main_codes():
    import narcio, sprites
    DEC = os.path.join(ROOT, 'external', 'pokebw2')
    names = []
    for line in open(os.path.join(DEC, 'generated', 'obj_codes.txt')):
        line = line.strip()
        if line and not line.startswith('#'):
            names.append(line)
    import platinum_events
    value = platinum_events.b2_obj_codes()
    znames = [l.strip() for l in open(os.path.join(DEC, 'generated', 'zones.txt')) if l.strip() and not l.startswith('#')]
    sinnoh = set()
    for f in (os.path.join(ROOT, 'data', 'sinnoh_world.json'), os.path.join(ROOT, 'data', 'platinum', 'sinnoh_world.json')):
        w = json.load(open(f))
        sinnoh |= {z['b2_zone'] for z in w['zones'].values()} | {z['b2_zone'] for z in w['rooms']['zones'].values()}
    kept = {n.lower().replace('zone_', '', 1) for i, n in enumerate(znames) if i not in sinnoh}

    def zone_file(p):
        stem = os.path.splitext(os.path.basename(p))[0]
        return stem.startswith('global') or stem in kept or not any(d in p for d in ('/events/', '/scripts/', '/zones/'))
    named = set()
    pat = re.compile(r'\bOBJ_CODE_\w+')
    for path in [p for p in glob.glob(os.path.join(DEC, 'res', 'field', '**', '*'), recursive=True)
                 if '/actors/' not in p and zone_file(p)] + \
            glob.glob(os.path.join(DEC, 'src', '**', '*.[ch]'), recursive=True) + \
            glob.glob(os.path.join(DEC, 'include', '**', '*.h'), recursive=True):
        if os.path.isdir(path) or os.path.getsize(path) > 8_000_000:
            continue
        t = open(path, encoding='utf-8', errors='ignore').read()
        named |= {value[m] for m in pat.findall(t) if m in value}
    taken = collections.defaultdict(list)
    for f in (os.path.join(ROOT, 'data', 'pearl_sprite_map.json'), os.path.join(ROOT, 'data', 'platinum', 'sprite_map.json')):
        for k, v in json.load(open(f, encoding='utf-8')).items():
            if isinstance(v, dict):
                for c in [v.get('code')] + list(v.get('zone_codes', {}).values()):
                    if isinstance(c, int):
                        taken[c].append(f'{os.path.basename(os.path.dirname(f))}/{k}')
    t = narcio.load(VANILLA, 247)[0]
    pwt = {struct.unpack_from('<H', t, 16 * i + 2)[0] for i in range(len(t) // 16)}
    table = sprites.ow_table(VANILLA)
    res1 = collections.Counter(r['res1'] for r in table if r['entityType'] == 1)
    sheets = narcio.load(VANILLA, sprites.ARC_OW_SHEETS)
    name_of = {v: k for k, v in value.items()}
    print('12-frame 32 x 32 walkers (node 2: as they are; 5, 15, 20: their record becomes a walker\'s):')
    for code in range(1, 377):
        rec = table[code]
        if code in named or code in pwt or rec['entityType'] != 1 or rec['spriteControllerType'] != 3:
            continue
        lay, _, _ = sprites.btx_layout(sheets[rec['res1']])
        if len(lay) != 12 or any((w, h) != (32, 32) for _, w, h, _ in lay) or res1[rec['res1']] != 1:
            continue
        print(f'  {code} {name_of.get(code, "?")}: node {rec["sceneNodeType"]}, sheet {rec["res1"]}'
              + (f'; taken by {", ".join(taken[code])}' if code in taken else ''))
    print('3D-model codes (0x2000-0x200A):')
    for code in range(0x2000, 0x200B):
        why = 'named in kept Black 2 content' if code in named else 'free'
        if code in (0x2003, 0x2004, 0x2005):
            why = 'a Strength boulder (fldmmdl.c IsNPCStrengthRock)' + (' and named' if code in named else '')
        print(f'  {code:#x} {name_of.get(code, "?")}: {why}' + (f'; taken by {", ".join(taken[code])}' if code in taken else ''))
    return 0


# ------------------------------------------------------------------------------------------------------------ versions
def digest(root):
    """{archive: sha1} of a/0/4/7 and a/0/4/8 after the three patches, with root's b2tools and data."""
    b2 = os.path.join(root, 'b2tools')
    sys.path[:0] = [b2, os.path.join(b2, 'patches')]
    for m in [m for m in list(sys.modules) if m in ('version', 'narcio', 'sprites', 'pearl_player_sprites',
                                                      'pearl_npc_sprites', 'pearl_amity_sprites', 'pearl_e4_doors')]:
        del sys.modules[m]
    import version
    assert os.path.abspath(version.__file__).startswith(os.path.abspath(root)), version.__file__
    with tempfile.TemporaryDirectory(dir=OUT) as t:
        copy_files(t)
        run_patches(t)
        return {arc_rel(n): hashlib.sha1(open(os.path.join(t, arc_rel(n)), 'rb').read()).hexdigest() for n in (47, 48)}


def main_versions(base):
    base = base or subprocess.run(['git', 'merge-base', 'HEAD', 'main'], cwd=ROOT, capture_output=True, text=True,
                                  check=True).stdout.strip()
    where = os.path.join(OUT, 'version_base')
    if os.path.exists(where):
        shutil.move(where, os.path.expanduser(f'~/.Trash/plat_sprites_version_base_{os.getpid()}'))
    os.makedirs(where)
    a = subprocess.run(['git', 'archive', base, 'b2tools', 'data'], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', where], input=a, check=True)
    for d in ('roms', 'external', 'tools', 'art_sources', 'work'):
        os.symlink(os.path.realpath(os.path.join(ROOT, d)), os.path.join(where, d))
    bad = 0
    for ver in ('pearl', 'diamond'):
        got = {}
        for root in (where, ROOT):
            env = dict(os.environ, PEARL_VERSION=ver)
            r = subprocess.run([sys.executable, os.path.abspath(__file__), '--digest', root], env=env, capture_output=True,
                               text=True, timeout=600)
            if r.returncode:
                raise SystemExit(r.stderr[-3000:])
            got[root] = json.loads(r.stdout.splitlines()[-1])
        same = got[where] == got[ROOT]
        bad += not same
        print(f'{ver}: a/0/4/7 and a/0/4/8 {"as at " + base[:7] if same else "CHANGED"} {got[ROOT]}')
    shutil.move(where, os.path.expanduser(f'~/.Trash/plat_sprites_version_base_{os.getpid()}'))
    return 1 if bad else 0


if __name__ == '__main__':
    argv = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    if '--digest' in argv:
        print(json.dumps(digest(argv[argv.index('--digest') + 1])))
        sys.exit(0)
    if '--codes' in argv:
        sys.exit(main_codes())
    if '--versions' in argv:
        sys.exit(main_versions(argv[argv.index('--base') + 1] if '--base' in argv else None))
    if '--zones' in argv:
        sys.exit(main_zones())
    sys.exit(main_check(argv[argv.index('--out') + 1] if '--out' in argv else os.path.join(OUT, 'render')))
