"""Platinum's Distortion World, its engine (2026-11-07, plat-dw-core; notes/PLATINUM_DW.md): the decomp's
src/pearlb2/plat_dw/, overlay 377, gimmick 69 of src/pearlb2/gimmick_itcm.c. The tables: b2tools/platinum_dw_data.py, read
from the Platinum dump. List it after platinum_gyms (both write the gimmick table; their zones don't meet):

    build_rom.py ... platinum_gyms platinum_dw ...

A Pearl or Diamond build: nothing (they have no Distortion World). A Platinum build:
- apply(files): the gimmick table (a/1/0/2) gives the Distortion World's ten zones (b2tools/platinum_dw_data.py's floors,
  Black 2 zones 699-709 but 704, the unused placeholder) gimmick 69;
- apply_code(code): the tables in overlay 377's own pool (PEARLB2_PLATDW_POOL, in its file), their address in
  gPlatDWTables (NULL: the gimmick does nothing). (plat-dw-rom, 2026-11-08) Now a file of a/2/9/5 after the world's tables,
  read into the field's heap by the gimmick (gPlatDWTablesFile = 295 << 16 | file; 0: nothing happens): the overlay's 5 KB
  pool went to code for the parts the ROM decided (its room was 1.4 KB).
(plat-dw-world, 2026-11-07) The world (src/pearlb2/plat_dw/dw_world.c, notes/PLATINUM_DW.md "The world"):
- apply(files) also appends to a/2/9/5 (after platinum_gyms' files: list it after platinum_gyms) Platinum's prop models
  (data/mmodel/fldeff.narc 0x7C-0x94, the 25 kinds), their 5 animations (0xBF, 0xC0, 0xC1, 0xC6, 0xC8), the Giratina room's
  Giratina (data/mmodel/mmodel.narc 440, its billboard model, and 393, its sheet), and the world's tables
  (b2tools/platinum_dw_world.py world_blob: the people, events, props, ghost props, commands, by floor), which the
  gimmick reads into the heap: they would not fit the overlay's room;
- apply_code(code) writes gPlatDWWorld = 295 << 16 | the tables' file (0: no world).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402
sys.path.insert(0, HERE)
import narcio  # noqa: E402

GIMMICK_TABLE_ARC = 102
OVERLAY = 377
WARP_OVERLAY = 382      # (plat-dw3) the way in (Spear Pillar's swirl, dw_warp.c): its own overlay, at overlay 377's address
GIMMICK = 69
MODEL_ARC = 295                     # (plat-dw-world) a/2/9/5, after platinum_gyms' files
FLDEFF, MMODEL = 'data/mmodel/fldeff.narc', 'data/mmodel/mmodel.narc'
PROP_MODELS = range(0x7C, 0x95)     # sProp3DModelNARCIndexByKind
PROP_ANIMS = (0xBF, 0xC0, 0xC1, 0xC6, 0xC8)     # sPropAnimSetNARCIndexByKind's files, in file order
GIRATINA_ORIGIN = (440, 393)        # field_sprites: giratina_origin.nsbmd, giratina_origin.nsbtx


def tables():
    import platinum_dw_data as platinum_dw
    return platinum_dw.read_tables()


def zones():
    """{Black 2 zone: gimmick id} of the Distortion World's floors."""
    return {f['zone']: GIMMICK for f in tables()['floors']}


def first_file():
    """(plat-dw-world) Where the world's files start in a/2/9/5: after platinum_gyms'."""
    import platinum_gyms
    return platinum_gyms.first_file() + len(platinum_gyms.gyms().files())


def world_files():
    """(plat-dw-world) [(what, bytes)] appended to a/2/9/5, in order; the last is the world's tables."""
    sys.path.insert(0, os.path.dirname(HERE))
    from gen4rom import Rom, narc_members
    import platinum_dw_world
    rom = Rom(os.path.join(version.ROOT, 'roms', 'platinum.nds'))
    fe, mm = narc_members(rom.read(FLDEFF)), narc_members(rom.read(MMODEL))
    out = [(f'prop model {k:#x}', fe[k]) for k in PROP_MODELS] + [(f'prop animation {k:#x}', fe[k]) for k in PROP_ANIMS]
    out += [('Giratina Origin model', mm[GIRATINA_ORIGIN[0]]), ('Giratina Origin sheet', mm[GIRATINA_ORIGIN[1]])]
    first = first_file()
    reg = __import__('json').load(open(version.data_path('pearl_story_ids.json')))
    flag = lambda k: reg['flags'][k]['b2']
    ids = {'progress': int(reg['vars']['0x4055']['b2'], 16), 'cyrus': int(reg['vars']['0x405B']['b2'], 16),
           'shadow1': flag('0x09AE'), 'shadow2': flag('0x09AF'), 'puzzle': flag('0x09AD')}
    files = {'model': first, 'anim': {k: first + len(PROP_MODELS) + i for i, k in enumerate(PROP_ANIMS)}}
    out.append(('the world\'s tables', platinum_dw_world.world_blob(ids=ids, files=files)))
    for name, b in out[:-1]:
        assert b[:4] in (b'BMD0', b'BCA0', b'BTA0', b'BTX0'), (name, b[:4])
    import platinum_dw_data
    out.append(('the engine\'s tables', bytes(platinum_dw_data.blob())))     # (plat-dw-rom) after the world's: tables_file()
    out.append(('the sky', sky_blob(rom)))      # (plat-dw-rom) sky_file()
    demo = narc_members(rom.read(WARP_DEMO))    # (plat-dw-rom) warp_file(): the swirl's model, its animations
    out += [(f'the swirl {k}', demo[k]) for k in WARP_FILES]
    assert [b[:4] for _, b in out[-3:]] == [b'BMD0', b'BTA0', b'BCA0'], 'titledemo: not the swirl'
    return out


def world_file():
    """(plat-dw-world) The world's tables' file in a/2/9/5."""
    return first_file() + len(PROP_MODELS) + len(PROP_ANIMS) + 2


def tables_file():
    """(plat-dw-rom) The engine's tables' file in a/2/9/5 (they were in overlay 377's pool)."""
    return world_file() + 1


def sky_file():
    """(plat-dw-rom) The sky's file in a/2/9/5 (dw_sky.c), after the engine's tables."""
    return tables_file() + 1


# (plat-dw-rom) DoDWWarp's swirl (dw_warp.c): Platinum's title demo's model and its two animations (dw_warp.c
# DWWarp_InitModel: demo/title/titledemo.narc 16, 18 its joints', 17 its textures'), in file order
WARP_DEMO = 'demo/title/titledemo.narc'
WARP_FILES = (16, 17, 18)


def warp_file():
    """(plat-dw-rom) The swirl's model in a/2/9/5, after the sky; its animations follow."""
    return sky_file() + 1


# (plat-dw-rom) Platinum's sky and clouds (ov9_02249960.c InitSkyBackground, InitSkyClouds, sSkyCloudsTemplates), drawn by
# src/pearlb2/plat_dw/dw_sky.c in the 3D (Black 2's field has no BG layer free). From data/tw_arc_etc.narc: the sky's tiles,
# palette and screen (0-2: each screen row one tile across, so the texture is one 8-pixel column, repeated), the clouds'
# cells and tiles (3 + 3i, 4 + 3i; cloud 1, i = 0, is no template's) and their 5 palettes (24)
SKY_ETC = 'data/tw_arc_etc.narc'
SKY_MAGIC = b'PDSK'
SKY_LEVELS = 13         # SKY_BACKGROUND_MAX_DARKNESS + 1
# sSkyCloudsTemplates: resIDsIndex, group, initialRotAngle, rotAngleOffset (degrees), distToCenter, baseRotAngleDelta,
# basePos (screen pixels), scale
SKY_CLOUDS = ((6, 3, 0, 135, 0x68, 1.25, 128, 108, 2), (6, 3, 180, 135, 0x68, 1.25, 128, 108, 2),
              (6, 3, 90, 135, 0x68, 1.25, 128, 108, 2), (6, 3, 270, 135, 0x68, 1.25, 128, 108, 2),
              (1, 2, 0, 90, 0x3C, 1, 128, 128, 1), (2, 2, 180, 90, 0x3C, 1, 128, 128, 1),
              (3, 1, 315, 90, 0x2A, 0.75, 128, 128, 1), (4, 1, 135, 90, 0x2A, 0.75, 128, 128, 1),
              (5, 0, 0, 90, 0, 0.5, 128, 128, 1))
SKY_DELTAS = ((0, 0, 0, 0), (0.5, 1.5, 3, 5), (-2, -4.5, -7, -12.5))     # sSkyCloudsRotAngleDeltas[kind][group]
OAM_SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
             (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def _nitro_sections(b):
    o, out = struct.unpack_from('<H', b, 12)[0], {}
    for _ in range(struct.unpack_from('<H', b, 14)[0]):
        size = struct.unpack_from('<I', b, o + 4)[0]
        out[b[o:o + 4]] = b[o:o + size]
        o += size
    return out


def _ncgr_tiles(b):
    s = _nitro_sections(b)[b'RAHC']
    depth, size, off = struct.unpack_from('<I', s, 12)[0], struct.unpack_from('<I', s, 24)[0], struct.unpack_from('<I', s, 28)[0]
    assert depth == 3, 'not 4 bits a pixel'
    return s[8 + off: 8 + off + size]


def _nclr_colors(b, count):
    s = _nitro_sections(b)[b'TTLP']
    off = struct.unpack_from('<I', s, 20)[0]
    return list(struct.unpack_from(f'<{16 * count}H', s, 8 + off))


def _tile_rows(tiles, tile, w, h):
    """An OAM's w x h pixels from 1D-mapped 4-bit tiles (its tiles row by row) as a linear 4-bit texture."""
    out = bytearray()
    for y in range(h):
        for tx in range(w // 8):
            t = tile + (y // 8) * (w // 8) + tx
            out += tiles[t * 32 + (y % 8) * 4: t * 32 + (y % 8) * 4 + 4]
    return bytes(out)


def sky_blob(rom=None):
    """(plat-dw-rom) The sky's file (dw_sky.c DwSkyFile): the header, the 6 palettes, the deltas, the clouds, the quads
    (each cloud cell's OAMs), then the textures (the sky's first: 8 x 256)."""
    sys.path.insert(0, os.path.dirname(HERE))
    from gen4rom import Rom, narc_members
    rom = rom or Rom(os.path.join(version.ROOT, 'roms', 'platinum.nds'))
    m = narc_members(rom.read(SKY_ETC))
    fx = lambda v: int(round(v * 4096))
    # the sky: each screen row's one tile (all 32 columns alike), its 8 rows down the texture's 256
    tiles = _ncgr_tiles(m[0])
    s = _nitro_sections(m[2])[b'NRCS']
    w, h, _, size = struct.unpack_from('<HHII', s, 8)
    screen = struct.unpack_from(f'<{size // 2}H', s, 20)
    assert (w, h) == (256, 256)
    tex = bytearray()
    for r in range(32):
        row = screen[r * 32: r * 32 + 32]
        assert len(set(row)) == 1 and row[0] >> 12 == 0, f'sky row {r}: not one tile of palette 0 across'
        t, hf, vf = row[0] & 0x3ff, row[0] >> 10 & 1, row[0] >> 11 & 1
        for y in range(8):
            px = tiles[t * 32 + (7 - y if vf else y) * 4: t * 32 + (7 - y if vf else y) * 4 + 4]
            if hf:
                n = [(px[i // 2] >> (4 * (i & 1))) & 15 for i in range(8)][::-1]
                px = bytes(n[i] | n[i + 1] << 4 for i in range(0, 8, 2))
            tex += px
    # the 13 darkness levels' palettes (RecalculateSkyBackgroundDarkness: CalculateTintedColor toward GX_RGB(4, 4, 8) for the
    # sky's, GX_RGB(6, 6, 8) for the clouds', 16ths by the level), the sky's then the clouds' 5 each
    base = _nclr_colors(m[1], 1) + _nclr_colors(m[24], 5)

    def tint(c, t, level):
        r, g, b = c & 31, c >> 5 & 31, c >> 10 & 31
        return (r + ((t[0] - r) * level >> 4)) | (g + ((t[1] - g) * level >> 4)) << 5 | (b + ((t[2] - b) * level >> 4)) << 10
    colors = [tint(c, (4, 4, 8) if i < 16 else (6, 6, 8), level) for level in range(SKY_LEVELS) for i, c in enumerate(base)]
    # the clouds' cells: each OAM a quad, its texture after the sky's (one per tile start and size)
    quads, placed = [], {}
    for cell in sorted({c[0] for c in SKY_CLOUDS}):
        ctiles = _ncgr_tiles(m[4 + 3 * cell])
        c = _nitro_sections(m[3 + 3 * cell])[b'KBEC']
        n, attr, off = struct.unpack_from('<HHI', c, 8)
        assert n == 1
        esz = 16 if attr & 1 else 8
        noam, _, ooff = struct.unpack_from('<HHI', c, 8 + off)
        for j in range(noam):
            a0, a1, a2 = struct.unpack_from('<HHH', c, 8 + off + n * esz + ooff + 6 * j)
            ow, oh = OAM_SIZES[(a0 >> 14, a1 >> 14)]
            y, x = a0 & 0xff, a1 & 0x1ff
            y, x = y - 256 if y >= 128 else y, x - 512 if x >= 256 else x
            assert not a0 & 0x300 and not a0 & 0x2000, f'cloud cell {cell}: an affine or 8-bit OAM'
            key = (cell, a2 & 0x3ff, ow, oh)
            if key not in placed:
                while len(tex) % 32:
                    tex += bytes(1)
                placed[key] = len(tex)
                tex += _tile_rows(ctiles, a2 & 0x3ff, ow, oh)
            quads.append(struct.pack('<HBBbbBBB3x', placed[key] // 8, cell, a2 >> 12, x, y, ow.bit_length() - 4,
                                     oh.bit_length() - 4, a1 >> 12 & 3))
    clouds = [struct.pack('<BBHhhiiii', cell, group, dist, bx, by, fx(init), fx(offset), fx(delta), fx(scale))
              for cell, group, init, offset, dist, delta, bx, by, scale in SKY_CLOUDS]
    head = 20 + 2 * len(colors) + 4 * 12
    cloud_at = head
    quad_at = cloud_at + sum(map(len, clouds))
    tex_at = (quad_at + sum(map(len, quads)) + 31) & ~31
    out = bytearray(SKY_MAGIC + struct.pack('<HBBIII', len(tex), len(clouds), len(quads), tex_at, cloud_at, quad_at))
    out += struct.pack(f'<{len(colors)}H', *colors)
    out += struct.pack('<12i', *[fx(v) for kind in SKY_DELTAS for v in kind])
    assert len(out) == head
    out += b''.join(clouds) + b''.join(quads)
    out += bytes(tex_at - len(out)) + tex
    return bytes(out)


# (plat-dw-rom) Platinum's own sounds the Distortion World and Spear Pillar play (include/pearlb2.h PLATSND_*, in that order),
# each with the Black 2 sound whose player and priorities it takes (the stand-in the C plays without it). Each goes into the
# sound archive with its own trimmed bank and wave archive (pearl_music.trim, as sinnoh_music does the songs)
PLAT_SOUNDS = (('SEQ_SE_PL_SYUWA', 'SEQ_SE_FLD_19'), ('SEQ_SE_PL_SYUWA2', 'SEQ_SE_FLD_19'), ('SEQ_SE_PL_SYUWA3', 'SEQ_SE_FLD_19'),
               ('SEQ_SE_PL_FW089', 'SEQ_SE_FLD_148'), ('SEQ_SE_PL_FW089B', 'SEQ_SE_FLD_148'),
               ('SEQ_SE_PL_FW089_2', 'SEQ_SE_WALL_HIT'), ('SEQ_SE_PL_FW463', 'SEQ_SE_FLD_148'),
               ('SEQ_SE_PL_MEKI', 'SEQ_SE_WALL_HIT'), ('SEQ_SE_PL_MEKI2', 'SEQ_SE_WALL_HIT'), ('SEQ_SE_PL_GIRA', 'SEQ_SE_FLD_19'),
               ('SEQ_SE_PL_KUSARI', 'SEQ_SE_FLD_19'), ('SEQ_SE_PL_SUTYA2', 'SEQ_SE_DANSA'), ('SEQ_SE_DP_UG_008', 'SEQ_SE_FLD_04'))
SOUNDS_JSON = 'platinum_dw_sounds.json'      # (beside files/: what apply_code writes into the resident section)


def add_sounds(files):
    """(plat-dw-rom) Platinum's sounds into Black 2's sound archive: {name: (sequence id, size in 256-byte steps)}."""
    b2tools = os.path.dirname(HERE)
    if 'sdat' in sys.modules and os.path.dirname(os.path.abspath(sys.modules['sdat'].__file__)) != b2tools:
        del sys.modules['sdat']          # (narcio puts the decomp's tools/data, which has an sdat.py too, first)
    sys.path.insert(0, b2tools)
    import pearl_music
    from sdat import SDAT
    sys.path.insert(0, HERE)
    import sinnoh_music
    path = os.path.join(files, 'swan_sound_data.sdat')
    B = SDAT(open(path, 'rb').read())
    P = pearl_music.pearl_sdat()
    sound = sinnoh_music.b2_sound_ids()
    free_seq = [i for i in range(4, len(B.info['seq'])) if B.info['seq'][i] is None]
    free_bank = [i for i in range(len(B.info['bank'])) if B.info['bank'][i] is None]
    free_wave = [i for i in range(len(B.info['wavearc'])) if B.info['wavearc'][i] is None]
    assert min(len(free_seq), len(free_bank), len(free_wave)) >= len(PLAT_SOUNDS), 'the sound archive is full'
    new_files, ents, out = [], {}, {}
    next_file = len(B.fat)
    for k, (name, like) in enumerate(PLAT_SOUNDS):
        seq, bank, swar, info = pearl_music.trim(P, P.index('seq', name))
        sid, bid, wid = free_seq[k], free_bank[k], free_wave[k]
        st = B.info['seq'][sound[like]]
        ents[('seq', sid)] = SDAT.seq_entry(next_file, bid, volume=info['volume'], channel_prio=st['channel_prio'],
                                            player_prio=st['player_prio'], player=st['player'])
        ents[('bank', bid)] = SDAT.bank_entry(next_file + 1, [wid])
        ents[('wavearc', wid)] = SDAT.wavearc_entry(next_file + 2)
        new_files += [seq, bank, swar]
        next_file += 3
        out[name] = (sid, (len(seq) + len(bank) + len(swar) + 255) // 256)
    data = B.build(new_files=new_files, entries=ents)
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(data)
    os.replace(path + '.tmp', path)
    __import__('json').dump(out, open(os.path.join(os.path.dirname(files), SOUNDS_JSON), 'w'), indent=1)
    return out


def apply(files):
    if not version.PLATINUM:
        return f'platinum_dw: {version.VERSION} has no Distortion World: nothing'
    rows = narcio.load(files, GIMMICK_TABLE_ARC)
    table = [struct.unpack_from('<II', rows[0], o) for o in range(0, len(rows[0]), 8)]
    ours = zones()
    clash = [(a, b) for a, b in table if a in ours]
    table = [(a, b) for a, b in table if a not in ours] + sorted(ours.items())
    rows[0] = b''.join(struct.pack('<II', a, b) for a, b in table)
    narcio.save(files, GIMMICK_TABLE_ARC, rows)
    # (plat-dw-rom) no camera boundary: Platinum's camera follows the player anywhere in the Distortion World (its camera
    # system has no bounds there); sinnoh_rooms gives each room one that stops the camera at the map's south edge, which
    # held the camera's target back on B1F's south wall (23 units)
    import zoneheaders
    headers, entries = zoneheaders.load(files)
    for z in ours:
        headers[z]['cam_bound'] = 0xFFFF
    zoneheaders.save(files, headers, entries)
    # (plat-dw-world) the props' models and animations, Giratina's, the world's tables
    m = narcio.load(files, MODEL_ARC)
    assert len(m) == first_file(), f'a/2/9/5 has {len(m)} files, not {first_file()}: list platinum_dw after platinum_gyms'
    added = [b for _, b in world_files()]
    narcio.save(files, MODEL_ARC, m + added)
    assert len(m) + len(added) - 1 == warp_file() + len(WARP_FILES) - 1
    sounds = add_sounds(files)          # (plat-dw-rom)
    return (f'platinum_dw: zones {sorted(ours)} gimmick {GIMMICK}' + (f' (replacing {clash})' if clash else '') +
            f'; the world\'s {len(added)} files = a/2/9/5 {len(m)}-{len(m) + len(added) - 1} (world tables {world_file()}, '
            f'{len(added[-6])} B; engine tables {tables_file()}, {len(added[-5])} B; the sky {sky_file()}, '
            f'{len(added[-4])} B; the swirl {warp_file()}-{warp_file() + 2}); Platinum\'s sounds: '
            f'{len(sounds)} (seq {min(v[0] for v in sounds.values())}.., {sum(v[1] for v in sounds.values()) // 4} KB)')


def _save(path, data):
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(data)
    os.replace(path + '.tmp', path)


def apply_code(code):
    if not version.PLATINUM:
        return f'platinum_dw: {version.VERSION} has no Distortion World: no tables'
    import decomp
    import platinum_dw_data as platinum_dw
    slot = decomp.symbol('gPlatDWTablesFile', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if slot is None:
        return f'platinum_dw: this decomp has no overlay {OVERLAY} (no Distortion World code): nothing'
    path = os.path.join(code, f'arm9_ov{OVERLAY:03d}.bin')
    data = bytearray(open(path, 'rb').read())
    assert data[slot - start: slot - start + 4] == bytes(4), f'gPlatDWTablesFile at {slot:#x}: not 0'
    data[slot - start: slot - start + 4] = struct.pack('<I', MODEL_ARC << 16 | tables_file())
    world = decomp.symbol('gPlatDWWorld', code)        # (plat-dw-world) the world's tables' file
    if world is not None:
        assert data[world - start: world - start + 4] == bytes(4), f'gPlatDWWorld at {world:#x}: not 0'
        data[world - start: world - start + 4] = struct.pack('<I', MODEL_ARC << 16 | world_file())
    sky = decomp.symbol('gPlatDWSky', code)            # (plat-dw-rom) the sky's file, the swirl's
    at = decomp.symbol('gPlatDWSky', code)
    if at is not None:
        assert data[at - start: at - start + 4] == bytes(4), f'gPlatDWSky at {at:#x}: not 0'
        data[at - start: at - start + 4] = struct.pack('<I', MODEL_ARC << 16 | sky_file())
    _save(path, data)
    # (plat-dw3) the swirl's file into its own overlay (382, at the same address as 377: an address alone can't say which
    # binary holds it), or into 377's in a decomp from before the move
    at = decomp.symbol('gPlatDWWarp', code)
    if at is not None:
        wstart = decomp.symbol(f'OV{WARP_OVERLAY}_TEXT_START', code)
        wpath = os.path.join(code, f'arm9_ov{WARP_OVERLAY:03d}.bin') if wstart is not None else path
        wstart = start if wstart is None else wstart
        wdata = bytearray(open(wpath, 'rb').read())
        assert wstart <= at < wstart + len(wdata), f'gPlatDWWarp at {at:#x}: not in {wpath}'
        assert wdata[at - wstart: at - wstart + 4] == bytes(4), f'gPlatDWWarp at {at:#x}: not 0'
        wdata[at - wstart: at - wstart + 4] = struct.pack('<I', MODEL_ARC << 16 | warp_file())
        _save(wpath, wdata)
    snd = sounds_code(code)
    return (f'platinum_dw: the engine\'s tables a/2/9/5 {tables_file()}, the world\'s {world_file()} '
            f'(gPlatDWTablesFile {slot:#x}), the sky\'s ' + (f'{sky_file()}' if sky is not None else 'none (no gPlatDWSky)') +
            f'; {snd}')


def sounds_code(code):
    """(plat-dw-rom) The sounds' sequence ids and sizes into the resident section (gPearlB2PlatSoundSeq, _Size)."""
    import decomp
    import pearlb2_overlays
    js = os.path.join(os.path.dirname(code), SOUNDS_JSON)
    seq_at, size_at = decomp.symbol('gPearlB2PlatSoundSeq', code), decomp.symbol('gPearlB2PlatSoundSize', code)
    if seq_at is None or not os.path.exists(js):
        return 'no Platinum sounds (stand-ins)'
    sounds = __import__('json').load(open(js))
    res = pearlb2_overlays.RESIDENT
    start = decomp.symbol(f'OV{res}_TEXT_START', code)
    path = os.path.join(code, f'arm9_ov{res:03d}.bin')
    data = bytearray(open(path, 'rb').read())
    for k, (name, _) in enumerate(PLAT_SOUNDS):
        sid, size = sounds[name]
        assert data[seq_at - start + 2 * k: seq_at - start + 2 * k + 2] == bytes(2), f'gPearlB2PlatSoundSeq[{k}] not 0'
        struct.pack_into('<H', data, seq_at - start + 2 * k, sid)
        struct.pack_into('<H', data, size_at - start + 2 * k, size)
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(data)
    os.replace(path + '.tmp', path)
    return f'{len(PLAT_SOUNDS)} Platinum sounds (gPearlB2PlatSoundSeq {seq_at:#x})'



if __name__ == '__main__':
    print('zones', sorted(zones()))
    if version.PLATINUM:
        w = world_files()
        print(f'the world: {len(w)} files from a/2/9/5 {first_file()} (tables {world_file()}, {len(w[-6][1])} B; '
              f'{sum(len(b) for _, b in w)} B in all)')
