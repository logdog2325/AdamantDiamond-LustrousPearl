"""Platinum's own Gyms where they differ from Pearl's (notes/PORT_AUDIT.md, step 4): the data of the decomp's overlay 374
(src/pearlb2/plat_gyms/, include/pearlb2/plat_gyms.h), read from the user's Platinum dump. 2026-11-02, plat-gyms.

    PEARL_VERSION=platinum python3 b2tools/platinum_gym_data.py        prints the tables

Three gimmicks, each as Platinum's code does it (pokeplatinum src/overlay008/gym_features.c and overlay005):
- the Eterna Gym's flower clock (gimmick 65, EternaGym_*): five clock states, each with its walkable paths (a 13 x 13
  collision table over tiles x 5-17, z 7-19), the fountains' row (z 19, x 1-21) and the hour hand's jump tile; the
  hands' times; the hands are build models 537 (hour) and 536 (minute) at the clock's centre, 12 and 13 units up; the
  fountains are field effect 111 with animations 166 (running) and 167 (draining) (ov5_021F4018.c). The paths' height
  is Platinum's BDHC under each clock tile (the converted room has the flower beds' shape there);
- the Veilstone Gym's punching bags and tire stacks (gimmick 66, VeilstoneGym_*): 9 bags, 11 stacks, the 32 x 32 tile
  table (0 a bag may pass, 1 not, 3 not east-west, 4 it stops there, 5 not west), the camera's distance table; field
  effects 112-114 and animations 182-190, 195, 196, 168 (veilstone_gym_object_renderer.c);
- the Hearthome Gym's dark rooms (gimmick 67, HearthomeGym_*): the two trainer rooms' layouts (their doors, where the
  clue may be), the fog, the candle's light (field effect 115, animation 199) and the eight clue marks (116-123;
  ov5_021F47B0.c).
Every table is found by its contents (as pearl_veilstone_gym.py does Pearl's); each search must match once.
"""
import functools, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

# The zones (Pearl's names for Platinum's numbers: Platinum's Gyms took the zone numbers of Pearl's rooms)
ETERNA_ZONE = 'MAP_ETERNA_GYM_ENTRANCE'                          # Platinum 67, ETERNA_CITY_GYM
VEILSTONE_ZONE = 'MAP_VEILSTONE_GYM'                             # Platinum 133
HEARTHOME_ZONES = ('MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM',      # Platinum 88, the entrance room
                   'MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1',   # 89, trainer room 1
                   'MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2',   # 90, trainer room 2
                   'MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM')     # 91, the Leader's room
ETERNA_GIMMICK, VEILSTONE_GIMMICK, HEARTHOME_GIMMICK = 65, 66, 67

CLOCK = 13                       # ETERNA_CLOCK_DIAMETER
CLOCK_LEFT, CLOCK_TOP = 5, 7     # ETERNA_CLOCK_LEFT_BOUND, _TOP_BOUND
CLOCK_CENTER = (11, 13)
FOUNTAIN_Z, FOUNTAIN_LEFT_X, FOUNTAIN_RIGHT_X, GYM_WIDTH = 19, 2, 20, 21
STATES = 5
HAND_MODELS = (537, 536)         # sEternaGymClockModelIds: the hour, the minute hand (build_model.narc)
FOUNTAIN = (111, 166, 167)       # ov5_021F4044: the model, its running and its draining animation (fldeff.narc)
VEILSTONE_MODELS = (112, 114, 113)   # sVeilstoneGymObjectModelIDs: a toppled stack, a stack, a bag
VEILSTONE_ANIMS = (182, 183, 184, 185, 186, 187, 188, 189, 190, 195, 196, 168)
TIRE_ANIM_INDICES = (8, 9, 10, 11)   # sTireStackAnimIndices
OBJECT_Y = 6                     # InitPunchingBagRenderer / TireStackAnim_Init: 6 units over the tile's height
HEARTHOME_LIGHT = (0x73, 0xC7)   # Unk_ov5_0220079C[0], Unk_ov5_02200750: the light, its animation
HEARTHOME_CLUES = tuple(range(0x74, 0x7C))   # Unk_ov5_0220079C[1-8]: circle, square, triangle, sun, donut, moon,
#                                              star, heart (the door ids 0-7)
FOG_DENSITY = (109, 119, 91)     # HearthomeGym_InitFog: the rooms, trainer room 2, after the Relic Badge
LIGHT_TILES = 2                  # the player's light (HearthomeGym_InitTrainers: 2)
WRONG_DOOR_WARP = 1              # the entrance room's warp a wrong door leads to
EXIT_DOOR = 8                    # HEARTHOME_DOOR_ID_EXIT


@functools.lru_cache(None)
def rom():
    from gen4rom import Rom
    assert version.PLATINUM, 'platinum_gym_data reads the Platinum dump: run with PEARL_VERSION=platinum'
    return Rom(version.WORLD_DUMP)


def _find(pat, what):
    d = rom().data
    hits = [m.start() for m in re.finditer(re.escape(pat), d)]
    assert len(hits) == 1, f'{what}: {len(hits)} matches in the Platinum dump'
    return hits[0]


@functools.lru_cache(None)
def eterna():
    d = rom().data
    o = _find(bytes([1] * CLOCK * (CLOCK - 1) + [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0]), 'sEternaGymClockCollision')
    collision = [list(d[o + k * CLOCK * CLOCK: o + (k + 1) * CLOCK * CLOCK]) for k in range(STATES)]
    o = _find(bytes(([1] * 4 + [0] * 13 + [1] * 4) * 2 + [1] * 4 + [0] * 17), 'sEternaGymFountainCollision')
    fountain = [list(d[o + k * GYM_WIDTH: o + (k + 1) * GYM_WIDTH]) for k in range(STATES)]
    o = _find(struct.pack('<10H', 7, 25, 6, 15, 9, 15, 0, 45, 0, 30), 'sEternaGymClockTimes')
    times = [struct.unpack_from('<2H', d, o + 4 * k) for k in range(STATES)]
    o = _find(struct.pack('<2hi2hi', -1, -1, 2, 11, 18, 1), 'sEternaGymHourHandJumpTiles')
    jumps = [struct.unpack_from('<2hi', d, o + 8 * k) for k in range(STATES)]
    o = _find(struct.pack('<4H', 0, 0x1559, 0x2AB2, 0x4000), 'sEternaGymRotationForHour')
    rotation = list(struct.unpack_from('<12H', d, o))
    _find(struct.pack('<2I', *HAND_MODELS), 'sEternaGymClockModelIds')
    cx, cz = ((c * 16 + 8) << 12 for c in CLOCK_CENTER)
    o = _find(struct.pack('<2i', cx, 12 << 12) + struct.pack('<i', cz) + struct.pack('<i', cx), 'sEternaGymClockHandsCenter')
    centre = [struct.unpack_from('<3i', d, o + 12 * k) for k in range(2)]
    assert all(c[0] == cx and c[2] == cz for c in centre), f'sEternaGymClockHandsCenter: {centre}'
    assert all(set(c) <= {0, 1} for c in collision + fountain), 'clock or fountain collision: values other than 0/1'
    return dict(collision=collision, fountain=fountain, times=times, jumps=jumps, rotation=rotation,
                hand_y=[c[1] >> 12 for c in centre], heights=clock_heights(), fountain_y=fountain_height())


def _zone(name):
    zs = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    return next(z for z in zs if z['name'] == name)


def _chunk(name):
    z = _zone(name)
    m = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', f"{z['matrix']:03d}.json")))
    assert m['width'] == 1 and m['height'] == 1, f'{name}: one chunk expected'
    return m['maps'][0][0]


def _bdhc(name):
    import gen4_land
    b = open(os.path.join(version.WORLD_WORK, 'land', f'{version.land_id(_chunk(name)):03d}.bdhc'), 'rb').read()
    return gen4_land.bdhc_platinum_as_dp(b) if gen4_land.is_platinum_bdhc(b) else gen4_land.read_bdhc_dp(b)


def _height(bd, x, z):
    import gen4_land
    hs = gen4_land.bdhc_dp_heights(bd, x * 16 + 8 - 256, z * 16 + 8 - 256)
    return round(max(h for h, _ in hs)) if hs else 0


def clock_heights():
    """Platinum's walking height (its BDHC, the highest plate) of each clock tile: the paths along the hands."""
    bd = _bdhc(ETERNA_ZONE)
    return [_height(bd, CLOCK_LEFT + i % CLOCK, CLOCK_TOP + i // CLOCK) for i in range(CLOCK * CLOCK)]


def fountain_height():
    bd = _bdhc(ETERNA_ZONE)
    hs = {_height(bd, x, FOUNTAIN_Z) for x in list(range(1, 5)) + list(range(18, 22))}
    assert len(hs) == 1, f'the fountains\' floor: {hs}'
    return hs.pop()


@functools.lru_cache(None)
def veilstone():
    d = rom().data
    bag_xz = [(3, 12), (4, 24), (8, 9), (8, 22), (15, 28), (16, 12), (20, 19), (21, 26), (23, 13)]
    o = _find(b''.join(struct.pack('<2i', *p) for p in bag_xz[:3]), 'sPunchingBagPositions')
    bags = [struct.unpack_from('<2i', d, o + 8 * k) for k in range(9)]
    o = _find(struct.pack('<4i', 3, 23, 8, 12), 'sTireStackPositions')
    stacks = [struct.unpack_from('<2i', d, o + 8 * k) for k in range(11)]
    o = _find(bytes([1] * 8 + [0, 0, 0, 4] + [0] * 10 + [1] * 10), 'sVeilstoneTileBehaviors row 7')
    behaviors = list(d[o - 7 * 32: o - 7 * 32 + 32 * 32])
    assert set(behaviors) <= {0, 1, 2, 3, 4, 5}, sorted(set(behaviors))
    o = _find(struct.pack('<4i', 3, 4, 4, 4) + struct.pack('<10H', 7, 25, 6, 15, 9, 15, 0, 45, 0, 30),
              'sVeilstoneTravelDistanceRequiringCameraMovement (before the clock times)')
    camera = list(struct.unpack_from('<4i', d, o))
    o = _find(struct.pack('<3I', *VEILSTONE_MODELS), 'sVeilstoneGymObjectModelIDs')
    assert struct.unpack_from('<4I', d, o + 12) == TIRE_ANIM_INDICES, 'sTireStackAnimIndices (after the models)'
    _find(struct.pack('<12I', *VEILSTONE_ANIMS), 'sVeilstoneGymObjectAnimationsIDs')
    # the floor the objects stand on (MapObject_RecalculatePositionHeight: the BDHC), one height on every tile a bag or a
    # stack can be on (the converted room's tiles there take the rails over them: 76-77, notes/PLATINUM_GYMS.md)
    bd = _bdhc(VEILSTONE_ZONE)
    floors = {_height(bd, i % 32, i // 32) for i, b in enumerate(behaviors) if b != 1}
    floors |= {_height(bd, x, z - 2) for x, z in stacks}
    assert len(floors) == 1, f'the Veilstone Gym\'s floor under the bags: {floors}'
    return dict(bags=bags, stacks=stacks, behaviors=behaviors, camera=camera, floor=floors.pop())


@functools.lru_cache(None)
def hearthome():
    d = rom().data
    o = _find(struct.pack('<7i', 89, 0, 3, 1, 3, 15, 8), 'sTrainerRoomLayouts')
    layouts = [struct.unpack_from('<7i', d, o + 28 * k) for k in range(2)]
    o = _find(bytes([1] * 30 + [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1] + [0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0]),
              'sTrainerRoom1CluePositions')
    masks = [list(d[o: o + 15 * 8]), list(d[o + 15 * 8: o + 15 * 8 + 27 * 20])]
    assert masks[1][:3] == [0, 1, 1] and set(masks[1]) <= {0, 1}, 'sTrainerRoom2CluePositions'
    rooms = []
    for (header, first, count, ox, oz, sx, sz), mask, pat in zip(
            layouts, masks, (struct.pack('<i2h', 0, 4, 2), struct.pack('<i2h', 3, 4, 2) + struct.pack('<i2h', 4, 9, 2))):
        o = _find(pat + (struct.pack('<i2h', 1, 8, 2) if first == 0 else b''), f'sTrainerRoom{1 + (first > 0)}Doors')
        doors = []
        while True:
            i, x, z = struct.unpack_from('<i2h', d, o)
            if i == EXIT_DOOR:
                break
            doors.append((i, x, z))
            o += 8
        assert [i for i, _, _ in doors] == list(range(first, first + count)), doors
        rooms.append(dict(header=header, first=first, count=count, offset=(ox, oz), size=(sx, sz), mask=mask,
                          doors=[(x, z) for _, x, z in doors]))
    # ov5_021F47B0.c: the light's turn by the holder's facing (Unk_ov5_0220077C, degrees), the models (Unk_ov5_0220079C),
    # then its scale and its offset from the holder by facing and reach in tiles (Unk_ov5_022007C0, Unk_ov5_022008E0)
    turns = [(0x10E, 0xB4, 0), (0x5A, 0xB4, 0xB4), (0, 0x10E, 0x10E), (0, 0x5A, 0x5A)]
    o = _find(b''.join(struct.pack('<4H', *t, 0) for t in turns) + struct.pack('<9I', *([HEARTHOME_LIGHT[0]] + list(HEARTHOME_CLUES))),
              'Unk_ov5_0220077C and Unk_ov5_0220079C (the light, the clues)')
    o += 32 + 36
    scale = [[struct.unpack_from('<3i', d, o + 12 * (6 * f + k)) for k in range(6)] for f in range(4)]
    offset = [[struct.unpack_from('<3i', d, o + 288 + 12 * (6 * f + k)) for k in range(6)] for f in range(4)]
    assert scale[0][0] == (0xC00, 0x100, 0x1000) and offset[0][0] == (0, -15 << 12, -15 << 12), (scale[0][0], offset[0][0])
    assert offset[3][5] == (85 << 12, 0, 10 << 12), offset[3][5]
    return dict(rooms=rooms, turns=turns, scale=scale, offset=offset)


@functools.lru_cache(None)
def fldeff():
    from gen4rom import narc_members
    return narc_members(rom().read('data/mmodel/fldeff.narc'))


@functools.lru_cache(None)
def build_models():
    from gen4rom import narc_members
    return narc_members(rom().read('fielddata/build_model/build_model.narc'))


def no_fog(bmd):
    """A BMD0 with every material's polygon attribute's fog bit (15) cleared: NNS_G3dMdlSetMdlFogEnableFlagAll(mdl, 0), as
    ov5_021F47DC does to the candle's light, so the dark rooms' fog leaves it bright."""
    from nsbmd_fix import _ndict
    d = bytearray(bmd)
    mdl = struct.unpack_from('<I', d, 16)[0]
    assert d[mdl:mdl + 4] == b'MDL0', 'no MDL0 first'
    for ent, _ in _ndict(d, mdl + 8):
        m = mdl + struct.unpack_from('<I', d, ent)[0]
        mo = m + struct.unpack_from('<I', d, m + 8)[0]          # NNSG3dResMdl ofsMat
        for me, _ in _ndict(d, mo + 4):
            at = mo + struct.unpack_from('<I', d, me)[0]        # NNSG3dResMatData: tag, size, diffAmb, specEmi, polyAttr
            struct.pack_into('<I', d, at + 12, struct.unpack_from('<I', d, at + 12)[0] & ~(1 << 15))
    return bytes(d)


def files():
    """The models and animations the patch appends to the model archive, in order: [(name, bytes)]."""
    fe, bm = fldeff(), build_models()
    out = [('eterna hour hand', bm[HAND_MODELS[0]]), ('eterna minute hand', bm[HAND_MODELS[1]]),
           ('eterna fountain', fe[FOUNTAIN[0]]), ('eterna fountain running', fe[FOUNTAIN[1]]),
           ('eterna fountain draining', fe[FOUNTAIN[2]])]
    out += [(f'veilstone model {m}', fe[m]) for m in VEILSTONE_MODELS]
    out += [(f'veilstone anim {a}', fe[a]) for a in VEILSTONE_ANIMS]
    out += [('hearthome light', no_fog(fe[HEARTHOME_LIGHT[0]])), ('hearthome light anim', fe[HEARTHOME_LIGHT[1]])]
    out += [(f'hearthome clue {k}', fe[m]) for k, m in enumerate(HEARTHOME_CLUES)]
    for name, b in out:
        assert b[:4] in (b'BMD0', b'BCA0', b'BTP0', b'BTA0', b'BMA0'), f'{name}: {b[:4]}'
    return out


def main():
    e, v, h = eterna(), veilstone(), hearthome()
    print('Eterna: times', e['times'], 'jumps', e['jumps'], 'hands at', e['hand_y'], 'fountains at', e['fountain_y'])
    for k in range(STATES):
        print(f'  state {k}: walkable {sum(1 for c in e["collision"][k] if not c)} of {CLOCK * CLOCK}, '
              f'fountain row {"".join(map(str, e["fountain"][k]))}')
    print('  path heights', sorted(set(e['heights'])))
    print('Veilstone: bags', v['bags'], 'stacks', v['stacks'], 'camera', v['camera'])
    for r in h['rooms']:
        print('Hearthome room', r['header'], 'doors', r['doors'], 'clue area', r['offset'], r['size'],
              sum(1 for c in r['mask'] if not c), 'tiles')
    print('files', [(n, len(b)) for n, b in files()])
    return 0


if __name__ == '__main__':
    sys.exit(main())
