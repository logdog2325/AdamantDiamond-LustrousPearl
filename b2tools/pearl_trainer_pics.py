"""Pearl's own trainer pictures for the 46 Pearl trainer classes Black 2 does not have (user decision 2026-10-18,
"Pearl's own trainer pictures, from the dump"), as Black 2 trainer front sprites. Nothing is redrawn or resized.

    python3 pearl_trainer_pics.py [build]    roms/pearl.nds -> work/trainer_pics/<CLASS>/ (46 folders), then check
                                             and preview
    python3 pearl_trainer_pics.py check      the folders and the installed Black 2 files against Pearl's pictures
    python3 pearl_trainer_pics.py preview    work/trainer_pics/preview.png (Pearl's picture | the converted sprite)

Pearl's side (pokediamond is the reference):
- poketool/trgra/trfgra.narc: class c's front picture = member 2c (NCGR) + 2c + 1 (NCLR) (pokediamond
  arm9/src/pokemon.c sub_020690AC / sub_02068FE0: unk2 = class * 2, unk4 = class * 2 + 1). Class numbers:
  pokediamond include/constants/trainer_classes.h (98 classes, 196 members).
- NCGR: 160x80, 4 bpp, "scanned" (row-major, not tiled; low nibble = left pixel), encrypted back to front as DP does
  (pokediamond tools/nitrogfx gfx.c Decode, encodeMode 1: key = last u16, then each u16 from the end XOR key,
  key = key * 1103515245 + 24691). Two 80x80 frames side by side; the second is empty for all 98 classes, so the
  picture is the left 80x80. NCLR: 16 BGR555 colours, colour 0 = transparent.
- Checked: all 98 decoded pictures and palettes equal pokediamond's files/poketool/trgra/trfgra PNGs.

Black 2's side (b2tools/sprites.py `tr-export` folder; HoennB2 sprite_unique.build_trainer is the model):
- Pearl's pictures are 80x80 and 16 colours, as Black 2's, so each is used pixel for pixel with its own 16 colours.
- static.png (+0, the 80x80 still) = the picture; parts.png (+1, the 256x128 MCSS texture) = the picture at (0, 0),
  the rest clear; palette.pal (+7) = Pearl's 16 colours.
- Cells and animations (+2 NCER, +3 NANR, +4 NMCR, +5 NMAR, +6 MCSS quads) are copied unchanged from Black 2's front
  sprite 20 (TRAINER_SPRITE_NO_DATA_M_20, a placeholder): one cell of 6 OBJs showing texture (0, 0)-(80, 80) as one
  whole figure, one multi-cell with one node at (0, -40), animations 0 (intro) and 1 (loop) both show it. So the
  figure stands still in battle, feet on the sprite's ground line. (Sprites 22, 23, 39, 55, 76, 81 have the same files.)
- New sprite ids: Black 2 has front sprites 0-187; the 46 become 188-233 in Pearl class-number order (CLASSES below:
  fixed, so an id never moves once given). b2tools/patches/pearl_trainer_pics.py appends them to a/0/7/1.

Output: work/trainer_pics/<CLASS>/ (sprite.json, palette.pal, parts.png, static.png), work/trainer_pics/preview.png.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import sprites, mcss, version  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402

OUT = os.path.join(ROOT, 'work', 'trainer_pics')
DIAMOND_CLASSES = os.path.join(ROOT, 'external', 'pokediamond', 'include', 'constants', 'trainer_classes.h')
B2_FILES = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'b2_us', 'files')   # Black 2's own files (build_rom's)
TRFGRA = 'poketool/trgra/trfgra.narc'
ARC_FRONT = sprites.ARC_TR['front']      # 71
B2_FRONT_SPRITES = 188                   # Black 2's front sprites 0-187 (a/0/7/1 has 1504 files)
FIRST_SPRITE = B2_FRONT_SPRITES          # the new ids start right after them
DONOR = 20                               # TRAINER_SPRITE_NO_DATA_M_20: one still 80x80 cell (see above)

# The 46 Pearl classes with no Black 2 equivalent ("stand-in" in sinnoh_trainers.CLASS_MAP and used by a Pearl
# trainer), in Pearl class-number order. New sprite id = FIRST_SPRITE + position. Append only; never reorder.
CLASSES = [
    'CAMPER', 'PICNICKER', 'BUG_CATCHER', 'AROMA_LADY', 'COWGIRL', 'JOGGER', 'POKE_KID', 'YOUNG_COUPLE',
    'NINJA_BOY', 'DRAGON_TAMER', 'BIRD_KEEPER', 'DOUBLE_TEAM', 'COLLECTOR', 'TUBER_M', 'TUBER_F', 'SAILOR',
    'SIS_AND_BRO', 'RUIN_MANIAC', 'PI', 'SKIER_M', 'SKIER_F', 'PKMN_TRAINER_BARRY', 'ELITE_FOUR_AARON',
    'ELITE_FOUR_BERTHA', 'ELITE_FOUR_FLINT', 'ELITE_FOUR_LUCIEN', 'BELLE__PA', 'RANCHER', 'COMMANDER_MARS',
    'GALACTIC', 'INTERVIEWERS', 'CAMERAMAN', 'REPORTER', 'IDOL', 'GALACTIC_BOSS', 'COMMANDER_JUPITER',
    'COMMANDER_SATURN', 'GALACTIC_F', 'PKMN_TRAINER_CHERYL', 'PKMN_TRAINER_RILEY', 'PKMN_TRAINER_MARLEY',
    'PKMN_TRAINER_BUCK', 'PKMN_TRAINER_MIRA', 'PKMN_TRAINER_LUCAS', 'PKMN_TRAINER_DAWN', 'TOWER_TYCOON',
]
assert len(CLASSES) == 46 and FIRST_SPRITE + len(CLASSES) <= 256      # TrClassResource.sprite is a u8
# Platinum's Frontier Brains (Black 2 has its own MAID), after Pearl's so that no id moves
if version.PLATINUM:
    CLASSES += ['HALL_MATRON', 'FACTORY_HEAD', 'ARCADE_STAR', 'CASTLE_VALET']
    assert FIRST_SPRITE + len(CLASSES) <= 256


def sprite_id(name):
    return FIRST_SPRITE + CLASSES.index(name)


def sprite_ids():
    """{Pearl class name: new front sprite id} (work/world/trainer_pics.json)."""
    return {c: sprite_id(c) for c in CLASSES}


def pearl_class_numbers():
    """{class name without TRAINER_CLASS_: number} from pokediamond."""
    text = open(DIAMOND_CLASSES, encoding='utf-8').read()
    out = {m.group(1): int(m.group(2)) for m in re.finditer(r'#define\s+TRAINER_CLASS_(\w+)\s+(\d+)', text)}
    if version.PLATINUM:                # its 98-104
        for i, l in enumerate(open(os.path.join(ROOT, 'external', 'pokeplatinum', 'generated', 'trainer_classes.txt'))):
            if i >= 98:
                out[l.strip()[len('TRAINER_CLASS_'):]] = i
    return out


# ---------------------------------------------------------------------------------------------------- Pearl's pictures

def dp_decode_ncgr(ncgr):
    """(w, h, palette indices row-major) of a DP trainer/Pokémon NCGR: scanned 4 bpp, encrypted back to front."""
    assert ncgr[:4] == b'RGCN' and ncgr[0x10:0x14] == b'RAHC', 'not an NCGR'
    th, tw, depth, _, scanned, size, off = struct.unpack_from('<HHIIIII', ncgr, 0x18)
    assert depth == 3 and scanned == 1, (depth, scanned)
    d = bytearray(ncgr[0x18 + off:0x18 + off + size])
    key = d[-1] << 8 | d[-2]
    for i in range(size, 0, -2):
        v = (d[i - 1] << 8 | d[i - 2]) ^ (key & 0xFFFF)
        d[i - 1], d[i - 2] = v >> 8, v & 0xFF
        key = (key * 1103515245 + 24691) & 0xFFFFFFFF
    w, h = tw * 8, th * 8
    return w, h, bytes(sprites.unpack4(d, w * h))


def platinum_picture(members, c):
    """Class c's front in Platinum's layout (5 files: tiles, palette, cells, animation, scan; pokeplatinum SpriteSystem_SetTrainerClassGraphics
    Index): frame 0, the cell its first animation starts on, as 80 x 80 indices and 16 colours. Its scan file holds only 6.6 % of the pixels,
    so the picture comes from the tiles through the cell (checked with b2tools/pearl_trainer_pics.py check against res/trainers/classes/*/
    front.png). The Frontier Brains and others that animate stay on this frame for now (the user, 2026-11-02)."""
    import mcss, struct as st
    tiles, pal, ncer, nanr = members[5 * c:5 * c + 4]
    size, off = st.unpack_from('<II', tiles, 0x28)
    pix = sprites.unpack4(tiles[0x18 + off:0x18 + off + size], size * 2)
    idx = mcss.parse_anim(nanr)[0]['frames'][0][1]['idx']
    n, attr, celloff, cmap, vt = st.unpack_from('<HHIII', ncer, 0x18)
    unit = 64 << cmap
    src = 2 * st.unpack_from('<I', ncer, 0x18 + vt + st.unpack_from('<I', ncer, 0x18 + vt + 4)[0] + 8 * idx)[0] if vt else 0
    cb = 0x18 + celloff; csz = 16 if attr & 1 else 8; ob = cb + n * csz
    no, _, oo = st.unpack_from('<HHI', ncer, cb + csz * idx)
    out = bytearray(6400)
    for j in range(no):
        a0, a1, a2 = st.unpack_from('<HHH', ncer, ob + oo + 6 * j)
        y = (a0 & 0xff) - (256 if a0 & 0x80 else 0); x = (a1 & 0x1ff) - (512 if a1 & 0x100 else 0)
        w, h = sprites.OBJ_SIZES[(a0 >> 14, a1 >> 14)]
        t = src + (a2 & 0x3ff) * unit
        for i in range(w * h):
            px, py = x + i // 64 % (w // 8) * 8 + i % 64 % 8 + 40, y + i // 64 // (w // 8) * 8 + i % 64 // 8 + 40
            if pix[t + i] and 0 <= px < 80 and 0 <= py < 80:
                out[py * 80 + px] = pix[t + i]
    return bytes(out), sprites.nclr_colors_any(pal)[1][:16]


def class_picture(members, c):
    """(80x80 indices, 16 BGR555 colours) of class number c from the dump's trfgra.narc members."""
    if version.PLATINUM:
        return platinum_picture(members, c)
    w, h, pix = dp_decode_ncgr(members[2 * c])
    assert (w, h) == (160, 80), (c, w, h)
    assert not any(pix[y * w + x] for y in range(h) for x in range(80, 160)), f'{c}: second frame not empty'
    _, pal = sprites.nclr_colors(members[2 * c + 1])
    return bytes(pix[y * w + x] for y in range(80) for x in range(80)), pal


def pearl_pictures(dump=None):
    """{class name: (80x80 indices bytes, 16 BGR555 colours)} for CLASSES, from the dump's trfgra.narc."""
    rom = Rom(dump or version.SOURCE_DUMP)
    members = narc_members(rom.read(TRFGRA))
    numbers = pearl_class_numbers()
    assert len(members) == (5 if version.PLATINUM else 2) * len(numbers), (len(members), len(numbers))
    return {name: class_picture(members, numbers[name]) for name in CLASSES}


# ---------------------------------------------------------------------------------------------------- folders

def folder(name):
    return os.path.join(OUT, name)


def build(dump=None):
    """Write the 46 folders (sprites.py trainer-folder format)."""
    numbers = pearl_class_numbers()
    pics = pearl_pictures(dump)
    for name in CLASSES:
        pix, pal = pics[name]
        rgbs = [sprites.bgr555_to_rgb(c) for c in pal]
        d = folder(name)
        os.makedirs(d, exist_ok=True)
        parts = bytearray(256 * 128)
        for y in range(80):
            parts[y * 256:y * 256 + 80] = pix[y * 80:y * 80 + 80]
        sprites.write_pal(os.path.join(d, 'palette.pal'), rgbs)
        sprites.write_png(os.path.join(d, 'static.png'), pix, 80, 80, rgbs)
        sprites.write_png(os.path.join(d, 'parts.png'), bytes(parts), 256, 128, rgbs)
        s = sprite_id(name)
        sprites.write_json(os.path.join(d, 'sprite.json'), dict(
            kind='trainer', side='front', sprite=s, archive=ARC_FRONT, files=sprites.tr_files(s),
            pearl_class=name, pearl_class_number=numbers[name],
            source=f'{os.path.basename(version.SOURCE_DUMP)} {TRFGRA} members {2 * numbers[name]} (NCGR, left 80x80 '
                   f'of 160x80) + {2 * numbers[name] + 1} (NCLR)',
            donor=DONOR, donor_note='cells/animations (+2..+6) copied from Black 2 front sprite 20: one still 80x80 cell',
            made_by='b2tools/pearl_trainer_pics.py'))
    return len(CLASSES)


def folders_missing():
    return [n for n in CLASSES if not all(os.path.exists(os.path.join(folder(n), f))
                                          for f in ('sprite.json', 'palette.pal', 'parts.png', 'static.png'))]


# ---------------------------------------------------------------------------------------------------- install

def install(entries, black2_entries):
    """`entries` (a/0/7/1 files, Black 2's 1504) with the 46 sprites appended as ids 188-233: per class, Black 2
    sprite DONOR's 8 files from `black2_entries` (Black 2's own a/0/7/1), then the folder's pictures and colours over
    +0, +1 and +7 (sprites.tr_import: headers kept, LZ11 as the game's). Returns the new list."""
    n = len(entries)
    assert n == 8 * B2_FRONT_SPRITES, (f'a/0/7/1 has {n} files ({n / 8:g} sprites), expected Black 2\'s '
                                       f'{8 * B2_FRONT_SPRITES}: run pearl_trainer_pics before any patch that '
                                       f'appends front sprites (e.g. sprite_switch)')
    out = list(entries)
    donor = black2_entries[8 * DONOR:8 * DONOR + 8]
    for name in CLASSES:
        s = sprite_id(name)
        assert len(out) == 8 * s
        out += donor
        for k, data in sprites.tr_import(folder(name), out, sprite=s).items():
            out[k] = data
    return out


# ---------------------------------------------------------------------------------------------------- check

def _render_ok(sp, tex, still):
    """True if every tick of animations 0 and 1 draws exactly `still` (80x80) with its top-left at screen
    (-40, -80) (cell (-40, -40) at node (0, -40)) and nothing else."""
    want = mcss.np.zeros((mcss.CANVAS[1], mcss.CANVAS[0]), mcss.np.uint8)
    x0, y0 = mcss.ORIGIN[0] - 40, mcss.ORIGIN[1] - 80
    want[y0:y0 + 80, x0:x0 + 80] = mcss.np.frombuffer(still, mcss.np.uint8).reshape(80, 80)
    ticks = max(sum(f[0] for f in s['frames']) for s in sp.nanr + sp.nmar)
    for anim in (0, 1):
        for t in range(ticks + 1):
            if not (mcss.render(sp, tex, anim, t) == want).all():
                return False
    return True


def diamond_check(pics):
    """Problems [(class, what)] of the dump's decoded pictures against pokediamond's own PNGs (pixels by index,
    colours as BGR555), for the classes in `pics`. Skipped (empty) when pokediamond's files are not there."""
    from PIL import Image
    numbers = pearl_class_numbers()
    out = []
    for name, (pix, pal) in pics.items():
        p = os.path.join(ROOT, 'external', 'pokediamond', 'files', 'poketool', 'trgra', 'trfgra',
                         f'narc_{2 * numbers[name]:04d}.png')
        if not os.path.exists(p):
            return []
        im = Image.open(p)
        a = im.tobytes()
        if bytes(a[y * 160 + x] for y in range(80) for x in range(80)) != pix:
            out.append((name, 'pixels differ from pokediamond'))
        rp = im.getpalette()[:48]
        if [sprites.rgb_to_bgr555(rp[3 * i:3 * i + 3]) for i in range(16)] != [c & 0x7FFF for c in pal]:
            out.append((name, 'colours differ from pokediamond'))
    return out


def check(dump=None, verbose=True):
    """Exactness: (0) the dump's decoded pictures equal pokediamond's PNGs; (1) each folder's static.png and parts.png
    have Pearl's pixels and palette.pal Pearl's 16 colours; (2) after install() the Black 2 files decode to the same
    pixels and colours (+0, +1, +7), +2..+6 are the donor's, and Black 2's own 1504 files are unchanged; (3) the
    sprite's animations 0 and 1 draw Pearl's picture exactly, at every tick. Returns the number of problems."""
    from b2files import arc_path, narc_entries
    pics = pearl_pictures(dump)
    dia = diamond_check(pics)
    for name, what in dia:
        print(f'  {name}: {what}')
    print(f'pokediamond: {len(CLASSES) - len({n for n, _ in dia})}/{len(CLASSES)} decoded pictures equal its trfgra PNGs')
    b2 = narc_entries(arc_path(B2_FILES, ARC_FRONT))
    new = install(b2, b2)
    bad = len(dia)
    if new[:len(b2)] != b2:
        print('Black 2\'s own files changed'); bad += 1
    for name in CLASSES:
        pix, pal = pics[name]
        s = sprite_id(name)
        d = folder(name)
        problems = []
        rgbs = sprites.read_pal(os.path.join(d, 'palette.pal'))
        if [sprites.rgb_to_bgr555(c) for c in rgbs] != [c & 0x7FFF for c in pal]:
            problems.append('palette.pal colours differ')
        if sprites.read_png(os.path.join(d, 'static.png'), rgbs, 80, 80) != pix:
            problems.append('static.png pixels differ')
        parts = sprites.read_png(os.path.join(d, 'parts.png'), rgbs, 256, 128)
        want_parts = bytearray(256 * 128)
        for y in range(80):
            want_parts[y * 256:y * 256 + 80] = pix[y * 80:y * 80 + 80]
        if parts != bytes(want_parts):
            problems.append('parts.png differs')
        f = sprites.tr_files(s)
        if sprites.tr_decode_image(new[f['static']], 'static')[2] != pix:
            problems.append('installed +0 (still) differs')
        tex = sprites.tr_decode_image(new[f['parts']], 'parts')[2]
        if tex != bytes(want_parts):
            problems.append('installed +1 (texture) differs')
        if sprites.nclr_colors(new[f['palette']])[1] != [c & 0x7FFF for c in pal]:
            problems.append('installed +7 colours differ')
        if new[8 * s + 2:8 * s + 7] != b2[8 * DONOR + 2:8 * DONOR + 7]:
            problems.append('cells/animations are not the donor\'s')
        sp = mcss.Sprite(new, 8 * s)
        if not _render_ok(sp, mcss.np.frombuffer(tex, mcss.np.uint8).reshape(128, 256), pix):
            problems.append('MCSS animation does not draw the picture exactly')
        if problems:
            bad += 1
        if verbose or problems:
            print(f'  {s} {name:20s} {len(set(pix))} colours used, {sum(1 for p in pix if p)} px: '
                  + ('; '.join(problems) if problems else 'exact'))
    extra = sum(len(x) for x in new[len(b2):])
    print(f'check: {len(CLASSES) - bad}/{len(CLASSES)} exact (Pearl pixels and 16 colours in the folders, in the '
          f'Black 2 files and in the drawn animation); a/0/7/1 grows by {extra} B in {len(new) - len(b2)} files')
    return bad


# ---------------------------------------------------------------------------------------------------- preview

def preview(dump=None, path=None, scale=2):
    """Every class: Pearl's picture (decoded from the dump) | the converted sprite as Black 2's MCSS draws it
    (animation 1, from the installed files), on a grey ground, with the class name and new sprite id."""
    from PIL import Image, ImageDraw
    from b2files import arc_path, narc_entries
    np = mcss.np
    pics = pearl_pictures(dump)
    b2 = narc_entries(arc_path(B2_FILES, ARC_FRONT))
    new = install(b2, b2)
    cols, cw, ch, pad, lab = 4, 2 * 80 * scale + 3 * 6, 80 * scale + 22, 6, 14
    rows = (len(CLASSES) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cw + pad, rows * ch + 24 + pad), (250, 250, 250))
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 6), 'Pearl trainer pictures: Pearl (dump) | converted Black 2 sprite (MCSS drawing). '
                      'Number = new front sprite id.', fill=(0, 0, 0))
    ground = (176, 184, 192)

    def tile(idx, rgbs):
        im = Image.new('RGB', (80, 80), ground)
        px = im.load()
        for i, v in enumerate(idx):
            if v:
                px[i % 80, i // 80] = rgbs[v]
        return im.resize((80 * scale, 80 * scale), Image.NEAREST)

    for k, name in enumerate(CLASSES):
        pix, pal = pics[name]
        s = sprite_id(name)
        f = sprites.tr_files(s)
        tex = np.frombuffer(sprites.tr_decode_image(new[f['parts']], 'parts')[2], np.uint8).reshape(128, 256)
        drawn = mcss.render(mcss.Sprite(new, 8 * s), tex, 1, 0)
        x0, y0 = mcss.ORIGIN[0] - 40, mcss.ORIGIN[1] - 80
        conv = drawn[y0:y0 + 80, x0:x0 + 80].tobytes()
        b2pal = [sprites.bgr555_to_rgb(c) for c in sprites.nclr_colors(new[f['palette']])[1]]
        x, y = pad + (k % cols) * cw, 24 + pad + (k // cols) * ch
        exact = conv == pix and drawn.sum() == np.frombuffer(conv, np.uint8).sum()
        dr.text((x, y), f'{s} {name}' + ('' if exact else '  DIFFERS'), fill=(0, 0, 0) if exact else (200, 0, 0))
        sheet.paste(tile(pix, [sprites.bgr555_to_rgb(c) for c in pal]), (x, y + lab))
        sheet.paste(tile(conv, b2pal), (x + 80 * scale + 6, y + lab))
    path = path or os.path.join(OUT, 'preview.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path)
    print('preview:', os.path.relpath(path, ROOT), sheet.size)
    return path


def main(argv):
    cmd = argv[0] if argv else 'build'
    if cmd in ('-h', '--help'):
        print(__doc__); return
    if cmd == 'build':
        print(f'{build()} folders in {os.path.relpath(OUT, ROOT)}/ (sprites {FIRST_SPRITE}-{FIRST_SPRITE + len(CLASSES) - 1})')
        bad = check(verbose=False)
        preview()
        sys.exit(1 if bad else 0)
    elif cmd == 'check':
        sys.exit(1 if check() else 0)
    elif cmd == 'preview':
        preview()
    else:
        sys.exit(f'unknown command {cmd}\n' + __doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
