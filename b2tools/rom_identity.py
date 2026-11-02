"""The game's name outside the game: the ROM header's title and the DS menu banner (icon and title lines).

install(code) writes code/rom_identity/{header.yaml, banner/}; build_rom.write_config uses them in place of the decomp's
extract/b2_us/header.yaml and banner/ (a build without patches/pearl_title.py stays Black 2's). Called by that patch.

- Header: Black 2's, with version.HEADER_TITLE. The game code (IREO) stays: Black 2's code and its link rules read it.
- Icon: the version's own dump (version.SOURCE_DUMP), pixel for pixel: Pearl's Poké Ball on pink. Black 2's banner is the
  animated kind (banner version 0x103: the DSi shows 8 bitmaps and palettes by a sequence, the DS the static icon), so
  all 8 slots hold the one icon and the sequence keeps its timing with every entry on slot 0, no flips.
- Title lines: version.PUBLIC_NAME's two parts and "Fan project" (the originals say Nintendo), in every language
  Black 2 fills.

Banner layout: u16 version, CRCs; 0x20 bitmap (0x200: 4bpp, 8x8 tiles, 4 x 4), 0x220 palette (0x20: BGR555), 0x240 titles
(0x100 each, UTF-16); 0x1240 animation (0x1000 bitmaps, 0x100 palettes, 0x80 sequence). The PNG forms dsd reads were
checked against Black 2's own dump: decode_icon gives its bitmap.png and palette.png exactly.

    python3 rom_identity.py check ROM    read a built ROM's header and banner back and compare them with what is wanted
"""
import os, re, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

EXTRACT = os.path.join(ROOT, 'external', 'pokebw2', 'extract', 'b2_us')
OUT = 'rom_identity'
TITLE_LINES = ['Pokémon', version.TITLE, 'Fan project']
LANGUAGES = ('japanese', 'english', 'french', 'german', 'italian', 'spanish', 'korean')   # Black 2's filled ones
ICON_BITMAP, ICON_PALETTE, TITLES = 0x20, 0x220, 0x240
ANIMATION = 0x1240


def dump_icon(path=None):
    """(0x200 bytes of bitmap, 0x20 bytes of palette) of a dump's banner."""
    with open(path or version.SOURCE_DUMP, 'rb') as f:
        off = struct.unpack('<I', f.read(0x6C)[0x68:])[0]
        f.seek(off)
        d = f.read(0x240)
    return d[ICON_BITMAP:ICON_PALETTE], d[ICON_PALETTE:TITLES]


def decode_icon(bitmap, palette):
    """(32*32 indices, 16 RGB colours as dsd's PNGs hold them: BGR555 << 3)."""
    px = bytearray(32 * 32)
    for t in range(16):
        for y in range(8):
            for x in range(8):
                v = bitmap[t * 32 + y * 4 + x // 2]
                px[(t // 4 * 8 + y) * 32 + t % 4 * 8 + x] = v >> 4 if x & 1 else v & 15
    cols = struct.unpack('<16H', palette)
    return bytes(px), [((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3) for c in cols]


def banner_yaml():
    text = open(os.path.join(EXTRACT, 'banner', 'banner.yaml'), encoding='utf-8').read()
    assert text.count('Black Version 2') == len(LANGUAGES), 'Black 2\'s banner titles changed'
    assert text.count('Nintendo') == len(LANGUAGES), 'Black 2\'s banner publisher lines changed'
    return text.replace('Black Version 2', version.TITLE).replace('Nintendo', TITLE_LINES[2])


def animation(bitmap, palette):
    a = open(os.path.join(EXTRACT, 'banner', 'animation.bin'), 'rb').read()
    assert len(a) == 0x1180
    seq = struct.unpack('<64H', a[0x1100:])
    seq = [v & 0xFF for v in seq]                       # bits 8-15: bitmap, palette, flips -> slot 0; keep the durations
    return bitmap * 8 + palette * 8 + struct.pack('<64H', *seq)


def install(code):
    from PIL import Image
    d = os.path.join(code, OUT)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, 'banner'))
    head = open(os.path.join(EXTRACT, 'header.yaml'), encoding='utf-8').read()
    head, n = re.subn(r'^title: .*$', f'title: {version.HEADER_TITLE}', head, count=1, flags=re.M)
    assert n == 1 and len(version.HEADER_TITLE) <= 12
    open(os.path.join(d, 'header.yaml'), 'w', encoding='utf-8').write(head)
    bitmap, palette = dump_icon()
    px, cols = decode_icon(bitmap, palette)
    b = os.path.join(d, 'banner')
    im = Image.frombytes('P', (32, 32), px)
    im.putpalette([v for c in cols for v in c])
    im.save(os.path.join(b, 'bitmap.png'))
    p = Image.new('RGBA', (16, 1))
    p.putdata([c + (0 if i == 0 else 255,) for i, c in enumerate(cols)])
    p.save(os.path.join(b, 'palette.png'))
    open(os.path.join(b, 'animation.bin'), 'wb').write(animation(bitmap, palette))
    open(os.path.join(b, 'banner.yaml'), 'w', encoding='utf-8').write(banner_yaml())
    return f'ROM header "{version.HEADER_TITLE}", DS menu banner "{version.TITLE}" with {version.NAME}\'s icon'


def stamp_met_game(code):
    """The version's Met game, on every Pokémon the game makes (version.MET_GAME; None keeps Black 2's). In place, the
    functions keep their size (notes/DECOMP_WORKFLOW.md); called by patches/pearl_title.py.

    - PML_CreatePkm sets it from the byte game_version (poke_tool.c), PML_PkmSyncOriginGame from the constant 23: both become
      the stamp. game_version itself stays 23: Black 2's demos, mail and Battle Subway read it as "which Black 2".
    - s0113_PokePartyIsOriginGame (is this Pokémon mine?) compares with game_version: it compares with the stamp.
    - setAbilityForForm and getPkmAbilSlotNumber read a Pokémon below White (20) as a Gen 4 one, ability slot by PID bit 0.
      Ours are made by Black 2's rule (bit 16, PML_CreatePkm), so a stamped Pokémon would change ability when it evolves:
      the limit becomes the stamp, and only what Pal Park brings (Ruby to LeafGreen, 1-5) keeps the old rule.
    """
    stamp = version.MET_GAME
    if stamp is None:
        return 'Met game stays Black 2\'s'
    import decomp
    def edit(name, sym, at, old, new):
        path = os.path.join(code, name)
        data = bytearray(open(path, 'rb').read())
        o = decomp.symbol(sym, code) - {'arm9.bin': 0x02004000, 'arm9_ov012.bin': 0x021503C0}[name] + at
        o_, n_ = bytes.fromhex(old), bytes.fromhex(new)
        assert data[o:o + len(o_)] in (o_, n_), f'{sym}+{at:#x}: {data[o:o + len(o_)].hex()}, not {old}'
        data[o:o + len(o_)] = n_
        if os.path.islink(path):
            os.unlink(path)
        open(path + '.tmp', 'wb').write(data)
        os.replace(path + '.tmp', path)
    s = f'{stamp:02x}'
    edit('arm9.bin', 'PML_CreatePkm', 0x134, '604a301c1278', f'{s}22301cc046')     # ldr/ldrb game_version -> movs r2, #stamp
    edit('arm9.bin', 'PML_PkmSyncOriginGame', 4, '1722', f'{s}22')                  # movs r2, #23 -> #stamp
    edit('arm9.bin', 'setAbilityForForm', 0x38, '1428', f'{s}28')                   # cmp r0, #20 -> #stamp
    edit('arm9.bin', 'getPkmAbilSlotNumber', 0x44, '1428', f'{s}28')
    edit('arm9_ov012.bin', 's0113_PokePartyIsOriginGame', 0xEE, '06490978', f'{s}21c046')   # ldr/ldrb -> movs r1, #stamp
    return f'Met game {stamp}'


def crc16(data):
    c = 0xFFFF
    for b in data:
        c ^= b
        for _ in range(8):
            c = c >> 1 ^ 0xA001 if c & 1 else c >> 1
    return c


def crcs_ok(d):
    """The banner's four CRCs (the DS menu shows no icon if they are wrong; dsd computes them)."""
    return all(struct.unpack_from('<H', d, at)[0] == crc16(d[a:b]) for at, a, b in
               ((2, 0x20, 0x840), (4, 0x20, 0x940), (6, 0x20, 0xA40), (8, 0x1240, 0x23C0)))


def check(rom):
    with open(rom, 'rb') as f:
        head = f.read(0x200)
        f.seek(struct.unpack_from('<I', head, 0x68)[0])
        d = f.read(0x23C0)
    title = head[:12].rstrip(b'\0').decode()
    bitmap, palette = dump_icon()
    english = d[TITLES + 0x100:TITLES + 0x200].decode('utf-16-le').rstrip('\0')
    # the DS shows bit 15 clear; the icon's palette index 0 is transparent, and dsd keeps only 5 bits a channel
    masked = lambda p: [v & 0x7FFF for v in struct.unpack('<16H', p)]
    results = {'header title': title == version.HEADER_TITLE,
               'game code kept': head[12:16] == b'IREO',
               'icon bitmap': d[ICON_BITMAP:ICON_PALETTE] == bitmap,
               'icon palette': masked(d[ICON_PALETTE:TITLES]) == masked(palette),
               'animated icon, 8 bitmaps': d[ANIMATION:ANIMATION + 0x1000] == bitmap * 8,
               'english title': english == '\n'.join(TITLE_LINES),
               'banner CRCs': crcs_ok(d)}
    for k, ok in results.items():
        print(('ok   ' if ok else 'BAD  ') + k)
    print(f'header {title!r}, banner version {struct.unpack_from("<H", d, 0)[0]:#x}, english {english!r}')
    return all(results.values())


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'check':
        sys.exit(0 if check(sys.argv[2]) else 1)
    sys.exit(__doc__)
