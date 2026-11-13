"""The Battle Frontier's picture rooms (plat-frontier-rooms, 2026-11-07; notes/PLATINUM_FRONTIER.md "The picture rooms").

Platinum draws the Factory's, Hall's, Castle's and Arcade's corridors and battle rooms as 2D scenes: a background picture of
Platinum's own (resource/eng/frontier_graphic/frontier_bg.narc: an 8bpp tile map with its palettes) and sprites over it, with
no zone and no map (overlay 104). Here each becomes a Black 2 field room, one mechanism for all of them:

- the picture: the scene's background layers from Platinum's dump, as the DS shows them (frontier_graphics.c: BG3, and BG2 when
  the scene keeps it shown, in their priority order; transparent pixels show the backdrop, black), pixel for pixel;
- the texture set: the picture cut into 32 x 32 blocks; each distinct block is one texture, 16 colours (4bpp) when it has at
  most 16, else 256 (8bpp), with its own palette; empty (all black) blocks are left out (the room's void is black too);
- the model: one flat quad per block at height 0, a material per texture, unlit, vertex colour white (the texels as they are),
  textures clamped, both faces drawn;
- the land: Black 2's flat tiles at height 0; the tiles the scene's people stand on and walk over are floor, the rest wall;
- the room: a picture pixel (px, py) is the world point (px + 8 + 16 AX, py + 8 + 16 AZ): the sprites stand where the scene
  draws them (Platinum places a sprite's feet at its (x, y) less 2; Black 2 draws a person, seen from above, over its tile with
  the feet 14 units south of the tile's centre), and the camera's centre falls on a tile's centre;
- the camera: straight down nearly (87 degrees), at the distance where one texel is one pixel (Black 2's 20-degree half-angle:
  96 / tan 20 = 263.76 units to the floor), W-buffered (a person's sprite lies almost flat there, a few units over the floor
  and its neighbours); the camera follows the hidden player, who stands where Platinum's scene camera looks (its object 0:
  the screen's top-left is (x - 120, y - 112));
- the zone: Platinum's new zones end at 718 (685 + its map id - 559); the picture rooms are pseudo map ids 593-600 on zones
  719-726 by the same rule, a block of their own (allocate_sinnoh FRONTIER_ROOMS_BLOCK, Platinum only).

    python3 b2tools/frontier_rooms.py check            every room: picture, its facility's texture set (decoded back pixel for
                                                       pixel), model, chunks
    python3 b2tools/frontier_rooms.py render [ROOM]    work/agents/plat-frontier-rooms/rooms/<room>.png: the room as the camera
                                                       shows it, its people at their first places, beside Platinum's picture
    python3 b2tools/frontier_rooms.py scripts [ZONE..]  pearl_story's files of the rooms and their lobbies (PEARL_VERSION=platinum):
                                                       written, assembled, and checked as sinnoh_story installs them
                                                       (b2_script_check at the map scripts' levels, lines, entries, people)
"""
import math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

BG_NARC = 'resource/eng/frontier_graphic/frontier_bg.narc'
ORDER = os.path.join(ROOT, 'external', 'pokeplatinum', 'res', 'graphics', 'frontier', 'backgrounds',
                     'frontier_backgrounds.order')
BLOCK = 32                      # texture blocks (texels = picture pixels)
CHUNK = 512                     # a Black 2 map chunk: 32 tiles of 16 units
POS_SCALE = 64                  # the model's position scale: +-256 units fit its 16-bit vertices (a land model's 32 does not)
POLY_ID = 0                     # the floor's polygon id (edge group 0: Pearl's indoor outlines, black against the void)
PICTURE_Y = -4                  # the picture's height, under the land's 0 (2026-11-08, plat-test): Black 2 draws a person 2 units
#                                 under the land (Field_CalcActorYOffset's floor at this pitch), and under a camera this
#                                 steep a sprite lies almost flat (facing the camera: its top only 0.12 units higher a unit up
#                                 the screen), so at 0 the picture covered every person's lower half (the Arcade's battle room,
#                                 steeper by its target offset: all but a line of their heads). 4 under them all;
#                                 the view's distance to it is then about one texel a pixel (as at 0: 1.4 % larger)
FLOOR_CELL = (0x00, 0x80)       # Black 2 tile (class, flags): plain floor; wall
WALL_CELL = (0x01, 0x81)
BACKDROP = 0x0000               # frontier_graphics.c: PaletteData_FillBufferRange(... 0x0 ...): the backdrop is black
# The camera (a/0/5/9 record, Black 2's layout: zoom, pitch, yaw, unk, unk, swap mode, half-angle, near, far, bind, target)
CAMERA_PITCH_DEG = 87.0
CAMERA_HALF_DEG = 20.0          # Black 2's camera 0
CAMERA_TARGET_Y = 4.0           # Black 2's camera 0 looks 4 units over the player
FIRST_ZONE, FIRST_MAP = 719, 593

# The rooms. layers: back to front, (tile map, tiles, palette) of frontier_bg.narc as the scene table names them (pokeplatinum
# src/overlay104/frontier_scenes.c); a layer the scene's setup hides (BG2 of the Hall's and the Arcade's battle rooms) is left
# out. Not here: FRONTIER_SCENE_13 (battle_castle_unknown), which only unreferenced code of the Castle's script changes to
# (Platinum never shows it). clip: the part of the picture the room keeps (the Factory's moving floor runs the whole 512 rows of its layer, which
# scrolls under the corridor's 192). AX, AZ: the picture's place in tiles (the same for every room of one script file: frontier_translate's staging is the
# file's). Names: PearlB2's zone names for them (MAP_...; pearl_story's pseudo maps).
ROOMS = [
    dict(name='MAP_BATTLE_FACTORY_CORRIDOR', scene='FRONTIER_SCENE_FACTORY_CORRIDOR', AX=0, AZ=1, clip=(0, 0, 256, 192),
         layers=[('battle_factory_corridor_floor', 'battle_factory', 'battle_factory'),       # BG2, priority 3: behind
                 ('battle_factory_corridor', 'battle_factory', 'battle_factory')]),
    dict(name='MAP_BATTLE_FACTORY_BATTLE_ROOM', scene='FRONTIER_SCENE_FACTORY_BATTLE_ROOM', AX=0, AZ=1,
         layers=[('battle_factory_battle_room', 'battle_factory', 'battle_factory')]),
    dict(name='MAP_BATTLE_HALL_CORRIDOR', scene='FRONTIER_SCENE_HALL_CORRIDOR', AX=0, AZ=1,
         layers=[('battle_hall_corridor', 'battle_hall_corridor', 'battle_hall_corridor')]),
    dict(name='MAP_BATTLE_HALL_BATTLE_ROOM', scene='FRONTIER_SCENE_HALL_BATTLE_ROOM', AX=0, AZ=1,
         layers=[('battle_hall_battle_room', 'battle_hall_battle_room', 'battle_hall_battle_room')]),  # (BG2: the lights, hidden)
    dict(name='MAP_BATTLE_CASTLE_CORRIDOR', scene='FRONTIER_SCENE_CASTLE_CORRIDOR', AX=0, AZ=1,
         layers=[('battle_castle_corridor', 'battle_castle_corridor', 'battle_castle_corridor')]),
    dict(name='MAP_BATTLE_CASTLE_BATTLE_ROOM', scene='FRONTIER_SCENE_CASTLE_BATTLE_ROOM', AX=0, AZ=1,
         layers=[('battle_castle_battle_room', 'battle_castle_battle_room', 'battle_castle_battle_room'),
                 ('battle_castle_battle_room_curtains', 'battle_castle_battle_room', 'battle_castle_battle_room')]),
    dict(name='MAP_BATTLE_ARCADE_CORRIDOR', scene='FRONTIER_SCENE_ARCADE_CORRIDOR', AX=0, AZ=1,
         layers=[('battle_arcade_corridor', 'battle_arcade_corridor', 'battle_arcade_corridor')]),
    dict(name='MAP_BATTLE_ARCADE_BATTLE_ROOM', scene='FRONTIER_SCENE_ARCADE_BATTLE_ROOM', AX=0, AZ=1,
         layers=[('battle_arcade_battle_room', 'battle_arcade_battle_room', 'battle_arcade_battle_room')]),  # (BG2: hidden)
]
for _i, _r in enumerate(ROOMS):
    _r['zone'], _r['map'] = FIRST_ZONE + _i, FIRST_MAP + _i
    _r['lobby'] = 'MAP_' + '_'.join(_r['name'].split('_')[1:3])      # the facility's lobby (Platinum's map, 688-691)
EMPTY_SCRIPTS, EMPTY_LEVEL, EMPTY_EVENTS = 368, 827, 0   # Platinum's empty script, level-script and event files (map 561's)
BY_NAME = {r['name']: r for r in ROOMS}
BY_SCENE = {r['scene']: r for r in ROOMS}


def room(name_or_scene):
    return BY_NAME.get(name_or_scene) or BY_SCENE[name_or_scene]


# ---------------------------------------------------------------- the picture
_BG = {}


def _members():
    if not _BG:
        import version
        from gen4rom import Rom, narc_members
        order = [l.strip() for l in open(ORDER) if l.strip()]
        _BG['order'] = order
        _BG['m'] = narc_members(Rom(os.path.join(ROOT, 'roms', 'platinum.nds')).read(BG_NARC))
        assert len(_BG['m']) == len(order), (len(_BG['m']), len(order))
    return _BG


def bg_file(name):
    """A frontier_bg.narc member by its decomp name (battle_factory_corridor.NSCR, ...), decompressed."""
    import title_art
    b = _members()
    for i, n in enumerate(b['order']):
        if n.rsplit('.lz', 1)[0] == name:
            d = b['m'][i]
            return title_art.lz10_decompress(d) if n.endswith('.lz') else d
    raise KeyError(name)


def layer(nscr, ncgr, nclr):
    """(w, h, [BGR555 or None per pixel]) of a background layer as the DS draws it: the scenes' BG2 and BG3 are extended
    affine layers (frontier_graphics.c: BG_TYPE_STATIC_WITH_AFFINE, 256 colours, extended palettes), whose map is one row
    after another and whose entries pick an extended palette of 256 colours; colour 0 is transparent."""
    import title_art as ta
    w, h, _, ent = ta.nscr_entries(bg_file(nscr + '.NSCR'))
    bpp, tiles = ta.ncgr_tiles(bg_file(ncgr + '.NCGR'))
    pal = bg_file(nclr + '.NCLR')
    size, off = struct.unpack_from('<II', pal, 0x20)
    cols = struct.unpack_from(f'<{size // 2}H', pal, 0x18 + off)
    out = [None] * (w * h)
    cw = w // 8
    for i, e in enumerate(ent[:cw * (h // 8)]):
        tx, ty = i % cw, i // cw
        t = tiles[e & 0x3FF] if (e & 0x3FF) < len(tiles) else bytes(64)
        t = ta.flip_tile(t, e >> 10 & 1, e >> 11 & 1)
        p = (e >> 12) * (256 if bpp == 8 else 16)
        for y in range(8):
            row = (ty * 8 + y) * w + tx * 8
            for x in range(8):
                v = t[y * 8 + x]
                if v:
                    out[row + x] = cols[p + v] & 0x7FFF
    return w, h, out


_PIC = {}


def picture(r):
    """(w, h, [BGR555 per pixel]) of a room's picture: its layers back to front, the backdrop where none draws."""
    if r['name'] not in _PIC:
        w = h = 0
        px = None
        for lay in r['layers']:
            lw, lh, lp = layer(*lay)
            if px is None:
                w, h, px = lw, lh, [None] * (lw * lh)
            assert (lw, lh) == (w, h), (r['name'], lay)
            for i, v in enumerate(lp):
                if v is not None:
                    px[i] = v
        x0, z0, x1, z1 = r.get('clip', (0, 0, w, h))
        _PIC[r['name']] = (w, h, [BACKDROP if v is None or not (x0 <= i % w < x1 and z0 <= i // w < z1) else v
                                  for i, v in enumerate(px)])
    return _PIC[r['name']]


def bbox(r):
    """The picture's drawn part (x0, z0, x1, z1): what isn't the backdrop."""
    w, h, px = picture(r)
    xs = [i % w for i, v in enumerate(px) if v != BACKDROP]
    zs = [i // w for i, v in enumerate(px) if v != BACKDROP]
    return min(xs), min(zs), max(xs) + 1, max(zs) + 1


# ---------------------------------------------------------------- the scenes' staging
STEP = {4: (0, -16), 5: (0, 16), 6: (-16, 0), 7: (16, 0)}     # frontier movement codes: walk north, south, west, east
for _k in (8, 12):                                             # (slow and fast walks the same)
    for _d in range(4):
        STEP[_k + _d] = STEP[4 + _d]
LINKED_GFX = 0xEEEF             # the wireless partner's look: the multi challenges are closed, no person for it
_STAGE, _SEEDS = {}, {}


def staging(index):
    """{scene id: {'places': [(local, gfx, dir, x, y, visible)] in the order the scene reaches them, 'moves': {local:
    [steps]}}} of frontier script file `index`: which scene each command
    runs in follows the flow from the file's entries (entry 0: the first scene of the file, which the field starts; another
    entry: the scene a ChangeScript names with it) through ChangeSceneWithinScript."""
    if index in _STAGE:
        return _STAGE[index]
    import collections
    import frontier_script as fs, frontier_translate as ft
    files = fs.files()
    d = fs.Disasm(files[index])
    sc = ft.scenes()
    mine = sorted(k for k, s in sc.items() if s['script'] == index)
    seeds = [(d.entries[0], mine[0])]
    for j, other in enumerate(files):          # ChangeScript scene, entry k into this file
        if not other or fs.source_order()[j].endswith('.bin'):
            continue
        od = fs.Disasm(other)
        for e, op, v in od.insns.values():
            if od.name(op) == 'ChangeScript' and sc.get(v[0], {}).get('script') == index and v[1] < len(d.entries):
                seeds.append((d.entries[v[1]], v[0]))
    seen, order, todo = set(), [], collections.deque(seeds)
    while todo:
        a, s = todo.popleft()
        if (a, s) in seen or a not in d.insns:
            continue
        seen.add((a, s))
        order.append((a, s))
        end, op, v = d.insns[a]
        name = d.name(op)
        if name == 'GoTo':
            todo.append((v[0], s))
        elif name in ('GoToIf', 'CallIf'):
            todo += [(v[1], s), (end, s)]
        elif name == 'Call':
            todo += [(v[0], s), (end, s)]
        elif name == 'ChangeSceneWithinScript':
            todo.append((end, v[0]))
        elif name not in ('End', 'Return', 'ChangeScript', 'ExitFrontier'):
            todo.append((end, s))
    out = {k: {'places': [], 'moves': collections.defaultdict(list)} for k in mine}
    for a, s in order:
        if s not in out:
            continue
        end, op, v = d.insns[a]
        name = d.name(op)
        if name == 'FrontierScrCmd_24':
            for local, gfx, di, x, y, visible, c, net in d.data_blocks[v[0]][2]:
                out[s]['places'].append((local, gfx, di, x, y, visible))
        elif name == 'ApplyMovement' and v[0] < 0x8000:
            out[s]['moves'][v[0]].append([c for c, n in d.data_blocks[v[1]][2] for _ in range(n)])
    _SEEDS[index] = seeds
    _STAGE[index] = out
    return out


_PATHS = {}


def paths(index):
    """{scene id: {'paths': {(x, y)}, 'player': {(x, y)}}}: every pixel position a person of frontier script file `index`
    stands on or walks over, by scene, and those of its object 0 (the scene camera follows it):
    the flow again, a state {local: {(x, y)}} per command (a placement puts a person, a move walks it from wherever it can be),
    joined where paths meet, until nothing grows."""
    if index in _PATHS:
        return _PATHS[index]
    import collections
    import frontier_script as fs
    d = fs.Disasm(fs.files()[index])
    st0 = staging(index)
    seeds = _SEEDS[index]
    out = {k: {'paths': set(), 'player': set()} for k in st0}
    state = {}
    todo = collections.deque((a, s, ()) for a, s in seeds)
    while todo:
        a, s, st = todo.popleft()
        if a not in d.insns:
            continue
        old = state.get((a, s))
        st = dict(st)
        if old is not None:
            merged = {k: old.get(k, frozenset()) | st.get(k, frozenset()) for k in set(old) | set(st)}
            if merged == old:
                continue
            st = merged
        state[(a, s)] = st
        end, op, v = d.insns[a]
        name = d.name(op)
        nxt = dict(st)
        if name == 'FrontierScrCmd_24':
            for local, gfx, di, x, y, visible, c, net in d.data_blocks[v[0]][2]:
                nxt[local] = frozenset({(x, y)})
                if s in out:
                    out[s]['paths'].add((x, y))
                    if local == 0:
                        out[s]['player'].add((x, y))
        elif name == 'ApplyMovement' and v[0] < 0x8000:
            ends = set()
            for x, y in st.get(v[0], ()):
                for c, n in d.data_blocks[v[1]][2]:
                    for _ in range(n):
                        dx, dy = STEP.get(c, (0, 0))
                        x, y = x + dx, y + dy
                        if s in out:
                            out[s]['paths'].add((x, y))
                            if v[0] == 0:
                                out[s]['player'].add((x, y))
                if -64 <= x <= 576 and -64 <= y <= 576:     # (a loop walking someone further each time: past the picture)
                    ends.add((x, y))
            nxt[v[0]] = frozenset(ends)
        nxt = {k: frozenset(p) for k, p in nxt.items()}
        if name == 'GoTo':
            todo.append((v[0], s, nxt))
        elif name in ('GoToIf', 'CallIf'):
            todo += [(v[1], s, nxt), (end, s, nxt)]
        elif name == 'Call':
            todo += [(v[0], s, nxt), (end, s, nxt)]
        elif name == 'ChangeSceneWithinScript':
            todo.append((end, v[0], nxt))
        elif name not in ('End', 'Return', 'ChangeScript', 'ExitFrontier'):
            todo.append((end, s, nxt))
    _PATHS[index] = out
    return _PATHS[index]


def scene_index(r):
    import frontier_translate as ft
    return ft.scene_id(r['scene'])


def scene_staging(r):
    import frontier_translate as ft
    k = scene_index(r)
    return staging(ft.scenes()[k]['script'])[k]


def player_place(r):
    """Where the scene first puts its object 0 (Platinum's player, hidden; the scene camera follows it)."""
    return next((x, y) for local, gfx, di, x, y, vis in scene_staging(r)['places'] if local == 0)


def people(r):
    """{local id: gfx} of the persons a room needs: every object its file's scenes place but the player (0) and the wireless
    partners (their look is the linked player's), so a staging command of either room's scene finds its person
    (frontier_translate keeps a file's local ids as the room's object ids)."""
    import frontier_translate as ft
    k = scene_index(r)
    out = {}
    for st in staging(ft.scenes()[k]['script']).values():
        for local, gfx, di, x, y, vis in st['places']:
            if local != 0 and gfx != LINKED_GFX:
                out.setdefault(local, gfx)
    return dict(sorted(out.items()))


def pseudo_zone(r, lobby, bank):
    """A room as pearl_story's PearlData zones hold Platinum's maps (map id r['map'], past Platinum's 593): its lobby's header
    (music, place, weather, map type) with the empty script, level-script and event files, the scene's text bank and no Gen 4
    matrix (pearl_events.Heights: the floor is flat, at 0)."""
    return dict(lobby, id=r['map'], name=r['name'], pl_name=r['name'], scripts=EMPTY_SCRIPTS, level_scripts=EMPTY_LEVEL,
                events=EMPTY_EVENTS, text_bank=bank, encounters=None, matrix=None,
                dump=dict(lobby.get('dump', {}), scripts=None, level_scripts=None, events=None))


def people_entities(r):
    """The room's people as Black 2 NPC records (pearl_events.entities' dicts): uid = the scene's local id, its look (a
    Platinum gfx through data/platinum/sprite_map.json, or a look slot: VAR_OBJ_GFX_ID n, Black 2 code 162 + n), standing
    still (move 0) on a parking tile, where the camera never looks: the scene puts each where it draws it (SetPosition,
    Show / Hide) before it fades in, and one the room's scene doesn't use stays there."""
    import pearl_events, frontier_translate as ft
    h = ft.HOSTS.get(r['scene'])
    slots = h['dynamic'] if h else {l: n for n, l in enumerate(sorted(l for l, g in people(r).items() if g >= 0x8000))}
    out = []
    for k, (local, gfx) in enumerate(people(r).items()):
        code = 162 + slots[local] if gfx >= 0x8000 else pearl_events.sprite_code(gfx)
        assert code is not None, (r['name'], local, gfx)
        out.append(dict(uid=local, model=code, move=0, evtype=0, flag=0, script=0, dir=1, p0=0, p1=0, p2=0, areaw=0, areah=0,
                        rail=0, x=parking(r)[k][0], z=parking(r)[k][1], y=0, clone=False))
    return out


def parking(r):
    """[(tx, tz)]: tiles of the room's matrix no camera place shows (the view is 256 x 192 around the camera's tile, which
    follows where the scene's people go: paths()), farthest from the picture first."""
    import frontier_translate as ft
    k = scene_index(r)
    ox, oz = origin(r)
    seen = set()
    for x, y in paths(ft.scenes()[k]['script'])[k]['player'] | {player_place(r)}:
        tx, tz, _, _ = camera_tile(r, x, y)
        seen |= {(tx + dx, tz + dz) for dx in range(-9, 10) for dz in range(-7, 8)}
    mw, mh = matrix_size(r)
    free = [(tx, tz) for tz in range(32 * mh) for tx in range(32 * mw) if (tx, tz) not in seen]
    free.sort(key=lambda t: (-t[1], -t[0]))
    assert len(free) >= len(people(r)), (r['name'], 'no parking tiles')
    return free


def floor_tiles(r):
    """{(tx, tz)}: the tiles the scene's people stand on and walk over, and the hidden player's."""
    ox, oz = origin(r)
    import frontier_translate as ft
    k = scene_index(r)
    tiles = {((x + ox) // 16, (y + oz) // 16) for x, y in paths(ft.scenes()[k]['script'])[k]['paths']}
    tiles.add(camera_tile(r, *player_place(r))[:2])
    tiles |= {(p['x'], p['z']) for p in people_entities(r)}         # (the parking tiles)
    return tiles


# ---------------------------------------------------------------- placement
def world_of(r, px, py):
    """World (x, z) of picture pixel (px, py)."""
    return px + 8 + 16 * r['AX'], py + 8 + 16 * r['AZ']


def origin(r):
    """frontier_translate's HOSTS origin: a scene object's tile is ((x + ox) // 16, (y + oz) // 16). Its feet are at the picture's
    (x, y - 2) (FrontierScrCmd_24 stores (x - 8, y - 16), the shadow at +8, +14), so it stands on the tile whose person's feet
    Black 2 draws there: the tile's centre is 14 units north of them."""
    return 16 * r['AX'], 16 * r['AZ'] - 16


def camera_tile(r, x0, y0):
    """(tx, tz, dx, dz): the tile the hidden player stands on so the camera shows what Platinum's scene camera shows when its
    object 0 is at (x0, y0) (ov63_0222D160: the screen's top-left (x0 - 8 - 112, y0 - 16 - 96), so its centre (x0 + 8,
    y0 - 16)), and what the camera's target must add to the tile's centre (units) when that centre isn't one."""
    X, Z = world_of(r, x0 + 8, y0 - 16)
    tx, dx = divmod(X - 8, 16)
    tz, dz = divmod(Z - 8, 16)
    # Black 2 moves only the camera's target by the record's offset, not its eye (field_camera.c: the eye from the bound
    # player, FinishLookAtMatrix adds targetOffset to the target and eyeOffset, 0, to the eye): an offset across turns the
    # view about the vertical (8 units: 14 degrees, the Castle corridor's picture drawn askew; seen 2026-11-08 in RAM), so
    # across the centre goes to the nearer tile's (Platinum's is between two: 8 px off). Along the view it only steepens or
    # flattens it a little (12 south: 85.5 degrees for 82.9), and stays.
    if dx > 8:
        tx += 1
    return tx, tz, 0, dz


def matrix_size(r):
    """(chunks wide, high) holding the picture's drawn part and every tile a person can reach."""
    x0, z0, x1, z1 = bbox(r)
    X1, Z1 = world_of(r, x1, z1)
    return max(1, math.ceil(X1 / CHUNK)), max(1, math.ceil(Z1 / CHUNK))


# ---------------------------------------------------------------- textures
def _blocks(r):
    """{(bx, bz): (BGR555 tuple of 32 x 32)} of the picture's blocks that aren't all backdrop."""
    w, h, px = picture(r)
    out = {}
    for bz in range(0, h, BLOCK):
        for bx in range(0, w, BLOCK):
            blk = tuple(px[(bz + y) * w + bx + x] for y in range(BLOCK) for x in range(BLOCK))
            if any(v != BACKDROP for v in blk):
                out[(bx // BLOCK, bz // BLOCK)] = blk
    return out


def facilities():
    """{facility: [its rooms]} (FACTORY, HALL, CASTLE, ARCADE): a facility's rooms share a texture set and an area."""
    out = {}
    for r in ROOMS:
        out.setdefault(r['name'].split('_')[2], []).append(r)
    return out


_SETS = {}


def texture_set(r):
    """(BTX0 bytes, {(bx, bz): texture name} of the room, {texture: palette}, stats of the set): the room's facility's set."""
    btx, tex_of, pal_of_tex, stats = facility_texture_set(r['name'].split('_')[2])
    return btx, tex_of[r['name']], pal_of_tex, stats


def facility_texture_set(facility):
    """(BTX0 bytes, {room name: {(bx, bz): texture name}}, {texture: palette}, stats): every distinct block of the facility's
    rooms once (a texture is fr_tNNN, a palette fr_pNNN)."""
    if facility in _SETS:
        return _SETS[facility]
    import nsbtx
    tex_of, texs, pals, pal_of = {}, [], [], {}
    texdata, pdata = bytearray(), bytearray()
    names = {}
    nblocks = 0
    for room_key, key, blk in [(r['name'], key, blk) for r in facilities()[facility]
                               for key, blk in sorted(_blocks(r).items())]:
        nblocks += 1
        tex_of.setdefault(room_key, {})
        if blk in names:
            tex_of[room_key][key] = names[blk]
            continue
        colours = sorted(set(blk))
        assert len(colours) <= 256, (r['name'], key, len(colours))
        fmt = 3 if len(colours) <= 16 else 4
        pal = tuple(colours + [0] * (16 - len(colours))) if fmt == 3 else tuple(colours)
        index = {c: i for i, c in enumerate(pal)}
        if pal not in pal_of:
            pname = f'fr_p{len(pals):03d}'
            while len(pdata) % 16:      # the DS finds a 16- or 256-colour palette in 16-byte units (TEXPLTT_BASE): one
                pdata.append(0)         # 8 bytes in took the 4 colours before it (2026-11-08, plat-test: the Hall's battle room)
            pals.append((pname, struct.pack('<HH', len(pdata) >> 3, 0)))
            pdata += struct.pack(f'<{len(pal)}H', *pal)
            pal_of[pal] = pname
        if fmt == 3:
            raw = bytes(index[blk[i]] | index[blk[i + 1]] << 4 for i in range(0, len(blk), 2))
        else:
            raw = bytes(index[v] for v in blk)
        while len(texdata) % 8:
            texdata.append(0)
        size_code = {8: 0, 16: 1, 32: 2, 64: 3, 128: 4}[BLOCK]
        params = (len(texdata) >> 3) | size_code << 20 | size_code << 23 | fmt << 26
        extra = BLOCK | BLOCK << 11 | 0x80000000
        tname = f'fr_t{len(texs):03d}'
        texs.append((tname, struct.pack('<II', params, extra), pal_of[pal]))
        texdata += raw
        names[blk] = tname
        tex_of[room_key][key] = tname
    tdict = nsbtx.dict_build([(n, e) for n, e, _ in texs], 8)
    pdict = nsbtx.dict_build(pals, 4)
    o_tdict = 0x3C
    o_pdict = o_tdict + len(tdict)
    o_tex = o_pdict + len(pdict)
    o_p = o_tex + len(texdata)
    size = o_p + len(pdata)
    hdr = bytearray(0x3C)
    hdr[0:4] = b'TEX0'
    struct.pack_into('<I', hdr, 4, size)
    struct.pack_into('<HH', hdr, 0xC, len(texdata) >> 3, o_tdict)
    struct.pack_into('<I', hdr, 0x14, o_tex)
    struct.pack_into('<HH', hdr, 0x1C, 0, o_tdict)
    struct.pack_into('<II', hdr, 0x24, o_p, o_p)
    struct.pack_into('<HH', hdr, 0x30, len(pdata) >> 3, 0)
    struct.pack_into('<H', hdr, 0x34, o_pdict)
    struct.pack_into('<I', hdr, 0x38, o_p)
    block = bytes(hdr) + tdict + pdict + bytes(texdata) + bytes(pdata)
    head = b'BTX0' + struct.pack('<HHIHHI', 0xFEFF, 1, 0x14 + len(block), 0x10, 1, 0x14)
    stats = dict(blocks=nblocks, textures=len(texs), palettes=len(pals),
                 bpp4=sum(1 for _, e, _ in texs if (struct.unpack_from('<I', e)[0] >> 26) & 7 == 3),
                 texels=len(texdata), palette_bytes=len(pdata))
    _SETS[facility] = (head + block, tex_of, {n: p for n, _, p in texs}, stats)
    return _SETS[facility]


# ---------------------------------------------------------------- the model
_TEMPLATE = {}


def template():
    """A Platinum land model whose file and model headers and node the room models keep (the Tower battle room's chunk:
    one node, nothing translated); its position scale goes to POS_SCALE."""
    if not _TEMPLATE:
        import json, pearl_mesh
        from version import land_id
        work = os.path.join(ROOT, 'work', 'platinum')
        m = json.load(open(os.path.join(work, 'matrices', '197.json')))       # MAP_BATTLE_TOWER_ARENA_MULTI's matrix
        bmd = bytearray(open(os.path.join(work, 'land', f'{land_id(m["maps"][0][0]):03d}.nsbmd'), 'rb').read())
        mo = pearl_mesh.Model(bytes(bmd))
        struct.pack_into('<ii', bmd, mo.m + 28, POS_SCALE << 12, 4096 // POS_SCALE)    # posScale, invPosScale (fx32)
        _TEMPLATE['model'] = pearl_mesh.Model(bytes(bmd))
    return _TEMPLATE['model']


def material_record(tname):
    """A material: unlit, the vertex colour white, the texture as it is (clamped), both faces, opaque, POLY_ID."""
    rec = bytearray(44)
    struct.pack_into('<HHIIIIIIHHHHii', rec, 0, 0, 44, 0x8000 | 0x7FFF, 0, 0x001F00C0 | POLY_ID << 24, 0x3F1FF8FF,
                     0x00000000, 0xFFFFFFFF, 0, 0x1FCE, BLOCK, BLOCK, 0x1000, 0x1000)
    return bytes(rec)


def chunk_model(r, cx, cz, tex_of, pal_of_tex):
    """BMD0 of chunk (cx, cz) of a room: the blocks' quads inside it, cut at its edges."""
    import pearl_mesh
    t = template()
    by_tex = {}
    X0c, Z0c = cx * CHUNK, cz * CHUNK
    for (bx, bz), tname in sorted(tex_of.items()):
        X0, Z0 = world_of(r, bx * BLOCK, bz * BLOCK)
        x0, x1 = max(X0, X0c), min(X0 + BLOCK, X0c + CHUNK)
        z0, z1 = max(Z0, Z0c), min(Z0 + BLOCK, Z0c + CHUNK)
        if x0 >= x1 or z0 >= z1:
            continue
        def v(x, z):          # chunk-centred raw position, texel coordinate in 1/16
            return pearl_mesh.Vertex((x - X0c - CHUNK // 2) * 4096 // POS_SCALE, PICTURE_Y * 4096 // POS_SCALE,
                                     (z - Z0c - CHUNK // 2) * 4096 // POS_SCALE,
                                     (x - X0) * 16, (z - Z0) * 16, None, 0x7FFF)
        by_tex.setdefault(tname, []).append([v(x0, z0), v(x0, z1), v(x1, z1), v(x1, z0)])
    mats, shapes, pairs = [], [], []
    for k, (tname, quads) in enumerate(sorted(by_tex.items())):
        mats.append({'name': f'{tname}_m', 'rec': material_record(tname), 'tex': tname, 'pal': pal_of_tex[tname]})
        shapes.append({'name': f'{tname}_s', 'flag': 6, 'dl': pearl_mesh.encode_groups([(pearl_mesh.QUADS, quads)])})
        pairs.append((k, k))
    cmds = pearl_mesh.sbc_commands(t)
    first_mat = next(i for i, (op, _) in enumerate(cmds) if op == 4)
    last_shp = max(i for i, (op, _) in enumerate(cmds) if op == 5)
    sbc = bytearray(b''.join(b for _, b in cmds[:first_mat]))
    sbc += b''.join(bytes((0x04, mi, 0x05, si)) for mi, si in pairs)
    sbc += b''.join(b for _, b in cmds[last_shp + 1:])
    while len(sbc) % 4:
        sbc.append(0)
    return fit_box(pearl_mesh.write_model(t, mats, shapes, bytes(sbc))), sum(len(q) for q in by_tex.values())


BOX_SCALE = 128                 # the box's position scale: a chunk's +-256 units fit its 16-bit box (1/32 unit)


def fit_box(bmd):
    """The model's bounding box (NNSG3dResMdlInfo box and boxPosScale) set to hold its quads. Black 2's field leaves out a
    map block whose box is out of view: the template's box (the Tower battle room's, 208 x 156 units) kept the Hall's
    battle room drawn only while the camera saw its top (2026-11-08, plat-test: black past z 282, the scene's walk south)."""
    import pearl_mesh
    mo = pearl_mesh.Model(bmd)
    lo, hi = [None] * 3, [None] * 3
    for s in mo.shapes:
        for p in s.polys:
            for v in p:
                for k in range(3):
                    u = v[k] * mo.pos_scale / 4096
                    lo[k] = u if lo[k] is None else min(lo[k], u)
                    hi[k] = u if hi[k] is None else max(hi[k], u)
    if lo[0] is None:
        return bmd
    f = 4096 / BOX_SCALE
    lo[1], hi[1] = lo[1] - 1, hi[1] + 1                     # (a flat floor: a unit of height either side)
    lo = [math.floor(a * f) - 1 for a in lo]
    hi = [math.ceil(b * f) + 1 for b in hi]
    vals = lo + [b - a for a, b in zip(lo, hi)]
    assert all(-32768 <= v <= 32767 for v in vals), vals
    out = bytearray(bmd)
    info = mo.m + 20
    struct.pack_into('<6h', out, info + 24, *vals)
    struct.pack_into('<ii', out, info + 36, BOX_SCALE << 12, 4096 // BOX_SCALE)
    return bytes(out)


# ---------------------------------------------------------------- the land
def tables():
    import pearl_chunk
    slopes, offsets = pearl_chunk.tables()
    a = next(i for i, s in enumerate(slopes) if s[0] == 0 and s[2] == 0 and s[1] > 0)
    b = next(i for i, o in enumerate(offsets) if o == 0)
    return a << 2, b


def terrain(r, cx, cz, floor):
    """A chunk's 32 x 32 tiles, flat at height 0: floor where the room's people go (floor: {(tx, tz)} in world tiles)."""
    a, b = tables()
    cells = []
    for tz in range(32):
        for tx in range(32):
            cls, flags = FLOOR_CELL if (cx * 32 + tx, cz * 32 + tz) in floor else WALL_CELL
            cells.append(struct.pack('<HHI', a, b, cls | flags << 16))
    return struct.pack('<HH', 32, 32) + b''.join(cells)


def build(r, floor=None):
    """Everything a room's install needs: {'chunks': {(cx, cz): WB bytes}, 'texset': BTX0, 'size': (w, h), 'stats'}."""
    from b2files import gf_container_build
    floor = floor if floor is not None else set()
    btx, tex_of, pal_of_tex, stats = texture_set(r)
    mw, mh = matrix_size(r)
    chunks = {}
    quads = 0
    for cz in range(mh):
        for cx in range(mw):
            bmd, n = chunk_model(r, cx, cz, tex_of, pal_of_tex)
            quads += n
            chunks[(cx, cz)] = gf_container_build('WB', [bmd, terrain(r, cx, cz, floor), struct.pack('<I', 0)])
    stats = dict(stats, quads=quads, chunks=len(chunks), floor_tiles=len(floor))
    return {'chunks': chunks, 'texset': btx, 'size': (mw, mh), 'stats': stats}


# ---------------------------------------------------------------- the camera
def camera_record(template_rec, dx=0, dz=0):
    """The rooms' camera (a/0/5/9): Black 2's camera 0 (its half-angle, bound to the player 4 units up) looking down at
    CAMERA_PITCH_DEG from where one texel is one pixel on the floor, W-buffered (swap mode 1); its target (dx, 4, dz) from
    the player (camera_tile's offsets: Platinum's screen centre between two tiles' centres). Black 2 puts the eye no
    steeper than 82.8 degrees over the bound player (field_camera.c TransRot: cos(pitch) at least 0x200), so the view is
    82.9 degrees (measured in RAM, 2026-11-08), the same for any pitch past that."""
    rec = bytearray(template_rec[:44])
    struct.pack_into('<3i', rec, 32, dx << 12, int(CAMERA_TARGET_Y * 4096), dz << 12)
    pitch = math.radians(CAMERA_PITCH_DEG)
    floor_dist = 96 / math.tan(math.radians(CAMERA_HALF_DEG))       # along the view, eye to the floor's centre
    zoom = floor_dist - CAMERA_TARGET_Y / math.sin(pitch)            # eye to the target, 4 units over the floor
    struct.pack_into('<i', rec, 0, int(round(zoom)))
    struct.pack_into('<I', rec, 4, int(round(CAMERA_PITCH_DEG / 360 * 65536)))
    rec[17] = 1                                                      # swap mode: W-buffer
    return bytes(rec)


def eye_target(r, tx, tz, dx=0, dz=0):
    """(eye, target) in world units for the hidden player on tile (tx, tz) (pearl_render's camera: eye = target +
    zoom (0, sin p, cos p))."""
    pitch = math.radians(CAMERA_PITCH_DEG)
    floor_dist = 96 / math.tan(math.radians(CAMERA_HALF_DEG))
    zoom = round(floor_dist - CAMERA_TARGET_Y / math.sin(pitch))
    target = (tx * 16 + 8 + dx, CAMERA_TARGET_Y, tz * 16 + 8 + dz)
    eye = (target[0], target[1] + zoom * math.sin(pitch), target[2] + zoom * math.cos(pitch))
    return eye, target


# ---------------------------------------------------------------- checks and pictures
def check_room(r):
    """[problems]: the textures decode back to the picture, block by block; the model holds every block once per chunk."""
    import pearl_render
    problems = []
    btx, tex_of, pal_of_tex, stats = texture_set(r)
    blocks = _blocks(r)
    e = lambda c: ((c & 31) << 3 | (c & 31) >> 2, (c >> 5 & 31) << 3 | (c >> 5 & 31) >> 2,
                   (c >> 10 & 31) << 3 | (c >> 10 & 31) >> 2)
    for key, blk in blocks.items():
        img = pearl_render._decode_with(btx, tex_of[key], pal_of_tex[tex_of[key]])    # (the palette its material names)
        got = [tuple(int(v) for v in p[:3]) for p in img.reshape(-1, 4)]
        want = [e(c) for c in blk]
        if got != want:
            problems.append(f'{r["name"]}: block {key} decodes to other colours ({sum(a != b for a, b in zip(got, want))} pixels)')
    return problems, stats


def render(r, people=(), out=None, scale=1):
    """The room through its camera (pearl_render), the hidden player on its camera tile; people: [(x, z) world tile, colour]
    drawn as the outline a person's sprite fills there seen from above (32 x 32 over the tile's centre)."""
    import numpy as np
    import pearl_mesh, pearl_render
    from b2files import gf_container
    from PIL import Image, ImageDraw
    b = build(r)
    tex = pearl_render.textures(b['texset'])
    eye, target = eye_target(r, *camera_tile(r, *player_place(r)))
    sc = pearl_render.Scene(256 * scale, 192 * scale, eye, target, half=CAMERA_HALF_DEG)
    for (cx, cz), data in b['chunks'].items():
        model = pearl_mesh.Model(gf_container(data)[1][0])
        pearl_render.draw_model(sc, model, tex, offset=(cx * CHUNK + CHUNK // 2, 0, cz * CHUNK + CHUNK // 2))
    im = sc.image()
    d = ImageDraw.Draw(im)
    for (tx, tz), colour in people:
        P = np.array([[tx * 16 - 8, 0, tz * 16 - 8], [tx * 16 + 24, 0, tz * 16 + 24]], float)
        (x0, y0, _), (x1, y1, _) = sc.project(P)
        d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], outline=colour)
    return im


def platinum_view(r, x0=120, y0=112, people=()):
    """Platinum's screen for the scene camera at object 0's (x0, y0): 256 x 192 of the picture from (x0 - 120, y0 - 112)
    (past the layer: the backdrop, the layers' area-over setting 0); people: [(x, y, colour)] drawn as their sprites' 32 x 32
    outlines (FrontierScrCmd_24 stores (x - 8, y - 16); the sprite centred there, its feet 2 over y)."""
    from PIL import Image, ImageDraw
    w, h, px = picture(r)
    im = Image.new('RGB', (256, 192))
    e = lambda c: ((c & 31) << 3 | (c & 31) >> 2, (c >> 5 & 31) << 3 | (c >> 5 & 31) >> 2,
                   (c >> 10 & 31) << 3 | (c >> 10 & 31) >> 2)
    ox, oy = x0 - 120, y0 - 112
    for y in range(192):
        for x in range(256):
            sx, sy = x + ox, y + oy
            im.putpixel((x, y), e(px[sy * w + sx]) if 0 <= sx < w and 0 <= sy < h else e(BACKDROP))
    d = ImageDraw.Draw(im)
    for x, y, colour in people:
        d.rectangle([x - 16 - ox, y - 32 - oy, x + 16 - ox, y - oy], outline=colour)
    return im


def check_scripts(names=None):
    """[problems] of the rooms' and lobbies' generated script files, by sinnoh_story's checks (patches/sinnoh_story.py)."""
    import pearl_story, pearl_ids, pearl_events, b2_script_check
    pd = pearl_story.PearlData()
    ids = pearl_ids.Ids()
    names = names or [r['name'] for r in ROOMS] + sorted({r['lobby'] for r in ROOMS})
    problems = []
    for name in names:
        zone = pd.by_name[name]
        p, tp, job = pearl_story.write_zone(pd, ids, zone)
        binary = pearl_story.assemble(p)
        init, levels = pearl_events.map_script_table(pd, zone, ids)
        nscripts = len(b2_script_check.entries(binary))
        heights = pearl_events.Heights()
        npcs, signs, trigs, skipped = pearl_events.entities(pd, zone, ids, heights, lambda sid: sid)
        for o in npcs + signs + trigs:
            if 0 < o['script'] < 2000 and o['script'] > nscripts:
                problems.append(f'{name}: a script {o["script"]} past the file\'s {nscripts}')
        nlines = sum(1 for l in open(tp, encoding='utf-8') if ' = ' in l)
        missing = sorted(n for n in b2_script_check.message_lines(binary) if n >= nlines)
        if missing:
            problems.append(f'{name}: lines {missing[:8]} past its text file\'s {nlines}')
        problems += [f'{name}: {q}' for q in b2_script_check.check(binary, levels)]
        uids = [n['uid'] for n in npcs]
        if len(uids) != len(set(uids)):
            problems.append(f'{name}: NPC uids repeat')
        print(f'{name}: {os.path.basename(p)}, {nscripts} scripts, {len(binary)} B, {len(npcs)} people; '
              f'{pearl_story.summary(job)}')
    return problems


def main(argv):
    cmd = argv[0] if argv else 'check'
    if cmd == 'scripts':
        problems = check_scripts(argv[1:] or None)
        print('\n'.join(problems) or 'every file assembles and passes b2_script_check')
        return 1 if problems else 0
    if cmd == 'check':
        bad = 0
        for r in ROOMS:
            problems, stats = check_room(r)
            b = build(r)
            print(f'{r["name"]} (zone {r["zone"]}, map {r["map"]}): picture {bbox(r)}, matrix {b["size"]}, {stats["blocks"]} blocks, '
                  f'{stats["textures"]} textures ({stats["bpp4"]} 16-colour), {stats["texels"] + stats["palette_bytes"]} B of '
                  f'texture set, {b["stats"]["quads"]} quads; {len(problems)} problems')
            for p in problems[:5]:
                print('  ', p)
            bad += len(problems)
        return 1 if bad else 0
    if cmd == 'render':
        outdir = os.path.join(ROOT, 'work', 'agents', 'plat-frontier-rooms', 'rooms')
        os.makedirs(outdir, exist_ok=True)
        for r in ROOMS if len(argv) < 2 else [room(argv[1])]:
            from PIL import Image
            ox, oz = origin(r)
            first = {}
            for local, gfx, di, x, y, vis in scene_staging(r)['places']:
                first.setdefault(local, (x, y))
            marks = [(((x + ox) // 16, (y + oz) // 16), (255, 0, 255) if local == 0 else (0, 255, 0))
                     for local, (x, y) in first.items() if local != 0]
            a = platinum_view(r, *player_place(r), people=[(x, y, (0, 255, 0)) for local, (x, y) in first.items()
                                                           if local != 0])
            b = render(r, marks)
            sheet = Image.new('RGB', (256 * 2 + 8, 192))
            sheet.paste(a, (0, 0)); sheet.paste(b, (264, 0))
            p = os.path.join(outdir, f'{r["name"][4:].lower()}.png')
            sheet.save(p)
            print(p)
        return 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
