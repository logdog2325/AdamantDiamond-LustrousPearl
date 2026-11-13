"""The Distortion World's world tables, read from Platinum's dump (plat-dw-world, 2026-11-07; notes/PLATINUM_DW.md "The
world"). The engine's own tables (platforms, jump points, camera triggers, elevators) are b2tools/platinum_dw_data.py's.

    PEARL_VERSION=platinum python3 b2tools/platinum_dw_world.py           writes data/platinum/distortion_world_story.json
    PEARL_VERSION=platinum python3 b2tools/platinum_dw_world.py --check   also checks the dump against pokeplatinum's C

What overlay 9 keeps for the world (src/overlay009/ov9_02249960.c in pokeplatinum), each found in the dump by its rows:
- sMapObjectEvents: the people of each floor (DistWorldObjectEvent: a flag condition, the sprite's rotation on a face,
  then Platinum's ObjectEvent). They are not in the event files: overlay 9 adds them when the floor loads, by their
  condition (CheckFlagConditionForObjectEvent), and the scripts add the rest (AddDistortionWorldMapObject).
- sMapEvents: the events at a tile (DistWorldEvent: the tile, a flag condition, a list of commands), which overlay 9
  runs after a step (HandleEventAt): start a zone script, set the progress, add or delete a person, move a platform with
  the player on it, the waterfalls, Giratina's shadows and arrival, the lake trio's boulder hints, the Giratina room's
  platforms.
- sSimplePropsMapTemplates: the portals and B5F's waterfall (a model at a tile, by a flag condition).
- sBoulderFallLocations: where a boulder pushed onto B5F's holes falls, and B6F's pits.
- the prop kinds' tables: the field effect archive's model and animation of each kind (data/mmodel/fldeff.narc), its
  offset from the tile and its scale.

Coordinates as the engine's (notes/PLATINUM_DW.md "Coordinates"): Platinum's shared world, and each floor's own tiles
(less the floor's offset) in the *_local fields.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom, narc_members  # noqa: E402
import platinum_dw_data as dwd  # noqa: E402

DECOMP = os.path.join(ROOT, 'external', 'pokeplatinum')
MAPS = [573, 574, 575, 576, 577, 579, 580, 581, 582, 583]
INVALID = dwd.MAP_HEADER_INVALID
PROP_KIND_COUNT = 25
PROP_ANIM_KIND_COUNT = 5
FLDEFF = 'data/mmodel/fldeff.narc'

# enum EventCmdKind
CMDS = ['set_map_object_animation', 'move_platform', 'add_map_object', 'delete_map_object', 'cascade_up',
        'start_script', 'set_progress', 'show_giratina_shadow', 'set_giratina_animation_flag', 'set_puzzle_flag',
        'cascade_down', 'play_giratina_arrival', 'show_uxie_boulder_tuto', 'show_azelf_boulder_tuto',
        'show_mesprit_boulder_tuto', 'show_giratina_room_platforms', 'hide_giratina_room_platforms',
        'clear_puzzle_flag']
CMD_END = len(CMDS)
# enum FlagCondition
CONDS = ['none', 'boulder_puzzle_false', 'boulder_puzzle_true', 'progress_eq', 'progress_leq', 'progress_geq',
         'manual_add_only', 'giratina_shadow', 'cyrus_appearance']
# enum PropKind
PROP_KINDS = ['small_platform', 'floating_blue_rock', 'medium_elevator_platform_1', 'medium_elevator_platform_2',
              'medium_elevator_platform_sw', 'medium_moving_platform_1', 'medium_moving_platform_2',
              'medium_elevator_platform_3', 'large_elevator_platform_1', 'medium_elevator_platform_4',
              'horizontal_platform_1', 'vertical_platform_1', 'vertical_platform_2', 'horizontal_platform_2',
              'rotated_platform_east', 'rotated_platform_west', 'large_elevator_platform_2',
              'large_elevator_platform_3', 'large_elevator_platform_4', 'medium_elevator_platform_5',
              'giratina_shadow', 'waterfall', 'land_vine_flower', 'land_rock', 'portal']
ANIM_KINDS = ['giratina_shadow', 'land_vine_flower', 'land_rock', 'waterfall', 'portal']


def _rows(o, ram, maps, what):
    """The offset of a {u32 map header, pointer} table with exactly these maps, then {MAP_HEADER_INVALID, NULL}."""
    want = b''.join(struct.pack('<I', m) for m in maps)
    found = []
    for at in range(0, len(o) - 8 * (len(maps) + 1), 4):
        ok = True
        for k, m in enumerate(maps):
            mh, p = struct.unpack_from('<II', o, at + 8 * k)
            if mh != m or not ram <= p < ram + len(o):
                ok = False
                break
        if ok and struct.unpack_from('<II', o, at + 8 * len(maps)) == (INVALID, 0):
            found.append(at)
    assert len(found) == 1, f'overlay 9: {what}: {len(found)} tables match'
    del want
    return found[0]


def _find_one(o, pat, what):
    return dwd._find_one(o, pat, what)


def read(rom=None):
    rom = rom or Rom(dwd.PLATINUM_DUMP)
    ram, o = dwd.overlay(rom, dwd.OV9)
    assert ram == dwd.OV9_RAM

    def ptr(p):
        assert ram <= p < ram + len(o), f'{p:#x} is not in overlay 9'
        return p - ram

    # ---- the people
    at = _rows(o, ram, MAPS, 'sMapObjectEvents')
    objects = {}
    for k, mh in enumerate(MAPS):
        lst = ptr(struct.unpack_from('<I', o, at + 8 * k + 4)[0])
        out = []
        while True:
            p, = struct.unpack_from('<I', o, lst)
            if p == 0:
                break
            q = ptr(p)
            cond, val, rot, ang = struct.unpack_from('<4H', o, q)
            (lid, gfx, mtype, ttype, hflag, script, odir, d0, d1, d2, rx, rz, x, z, y) = \
                struct.unpack_from('<6Hh3Hhh2Hi', o, q + 8)
            out.append({'cond': CONDS[cond], 'cond_value': val, 'rotated': bool(rot), 'rotation': ang,
                        'local_id': lid, 'gfx': gfx, 'movement': mtype, 'trainer_type': ttype, 'hidden_flag': hflag,
                        'script': script, 'dir': odir, 'data': [d0, d1, d2], 'range': [rx, rz], 'x': x, 'z': z,
                        'y_fx': y})
            lst += 4
        objects[mh] = out
    # the elevators' passenger: 1F's Cynthia (129) rides down with the player and becomes B1F's 128 (ChangeMaps: her local
    # id and map changed); B1F's table has no 128, so its event file gets her (always deleted on a fresh entry: manual), and
    # the engine makes her B1F's 128 where she arrives. (B6F's Cynthia becomes B7F's 128, which B7F's table has.)
    c = next(o for o in objects[573] if o['local_id'] == 129)
    objects[574] = objects[574] + [dict(c, cond='manual_add_only', cond_value=0, local_id=128, script=0, x=40 + 0, z=19 + 35,
                                        y_fx=(257 << 16), passenger=True)]

    # ---- the events at a tile and their commands
    at = _rows(o, ram, [573, 574, 575, 576, 577, 579, 581, 582], 'sMapEvents')
    cmd_lists = {}

    def params(kind, p):
        if p == 0:
            return None
        q = ptr(p)
        name = CMDS[kind]
        if name in ('start_script', 'set_progress', 'set_giratina_animation_flag', 'set_puzzle_flag',
                    'clear_puzzle_flag', 'delete_map_object'):
            return {'value': struct.unpack_from('<I', o, q)[0]}
        if name == 'add_map_object':
            mh, lid = struct.unpack_from('<HH', o, q)
            return {'map': mh, 'local_id': lid}
        if name == 'set_map_object_animation':
            lid, act = struct.unpack_from('<II', o, q)
            return {'local_id': lid, 'action': act}
        if name == 'move_platform':
            idx, move_player, dummy, fx, fy, fz, dx, dy, dz = struct.unpack_from('<3H3h3i', o, q)
            return {'platform': idx, 'move_player': move_player, 'dummy': dummy, 'final': [fx, fy, fz],
                    'delta': [dx, dy, dz]}
        if name in ('cascade_up', 'cascade_down'):
            axis, mdir, *v = struct.unpack_from('<IH9h3i', o, q)
            return {'axis': axis, 'dir': mdir, 'finishing_fix': v[0:3], 'final_offset': v[3:6],
                    'map_load_offset': v[6:9], 'delta': v[9:12]}
        if name == 'show_giratina_shadow':
            x, y, z, rot, snd, *v = struct.unpack_from('<3hbB3i3ii', o, q)
            return {'x': x, 'y': y, 'z': z, 'rot_index': rot, 'sound': snd, 'scale': v[0:3], 'delta': v[3:6],
                    'steps': v[6]}
        raise AssertionError(f'command {name} with parameters at {p:#x}')

    def commands(p):
        if p in cmd_lists:
            return cmd_lists[p]['index']
        q = ptr(p)
        out = []
        while True:
            kind, pp = struct.unpack_from('<II', o, q)
            if kind == CMD_END:
                break
            assert kind < CMD_END, f'command kind {kind}'
            out.append({'cmd': CMDS[kind], 'params': params(kind, pp)})
            q += 8
        cmd_lists[p] = {'index': len(cmd_lists), 'commands': out}
        return cmd_lists[p]['index']

    events = {mh: [] for mh in MAPS}
    for k, mh in enumerate([573, 574, 575, 576, 577, 579, 581, 582]):
        q = ptr(struct.unpack_from('<I', o, at + 8 * k + 4)[0])
        while True:
            x, y, z, cond, val, cmds = struct.unpack_from('<hhiHHI', o, q)
            if cmds == 0:
                break
            events[mh].append({'x': x, 'y': y, 'z': z, 'cond': CONDS[cond], 'cond_value': val,
                               'commands': commands(cmds)})
            q += 16
    lists = [None] * len(cmd_lists)
    for v in cmd_lists.values():
        lists[v['index']] = v['commands']

    # ---- the simple props
    at = _rows(o, ram, [573, 579, 582, 583], 'sSimplePropsMapTemplates')
    simple = {mh: [] for mh in MAPS}
    for k, mh in enumerate([573, 579, 582, 583]):
        q = ptr(struct.unpack_from('<I', o, at + 8 * k + 4)[0])
        while True:
            _, kind, x, y, z, cond, val = struct.unpack_from('<IH3hHH', o, q)
            if kind == PROP_KIND_COUNT:
                break
            simple[mh].append({'kind': PROP_KINDS[kind], 'kind_id': kind, 'x': x, 'y': y, 'z': z,
                               'cond': CONDS[cond], 'cond_value': val})
            q += 16

    # ---- the prop kinds
    i = _find_one(o, struct.pack('<25I', *range(0x7C, 0x95)), 'sProp3DModelNARCIndexByKind')
    models = list(struct.unpack_from('<25I', o, i))
    anims = list(struct.unpack_from('<5I', o, _find_one(o, struct.pack('<5I', 0xC6, 0xBF, 0xC0, 0xC8, 0xC1),
                                                         'sPropAnimSetNARCIndexByKind')))
    # sPropAnimInfoByKind: {propKind, animKind, isStatic} by kind; the static ones' animKind is PROP_ANIM_KIND_INVALID
    first = b''.join(struct.pack('<HHI', k, PROP_ANIM_KIND_COUNT, 1) for k in range(20))
    info_at = _find_one(o, first, 'sPropAnimInfoByKind')
    info = [struct.unpack_from('<HHI', o, info_at + 8 * k) for k in range(PROP_KIND_COUNT)]
    assert [p for p, _, _ in info] == list(range(PROP_KIND_COUNT)), 'sPropAnimInfoByKind'
    # sPropInitialPosOffsetByKind: the first eight rows are {0, -25, -6} tiles' units
    off_at = _find_one(o, struct.pack('<3i', 0, -25 * 4096, -6 * 4096) * 8 + struct.pack('<3i', -8 * 4096, -25 * 4096,
                                                                                          2 * 4096),
                       'sPropInitialPosOffsetByKind')
    offsets = [list(struct.unpack_from('<3i', o, off_at + 12 * k)) for k in range(PROP_KIND_COUNT)]
    # sPropScaleByKind: the first 22 rows are 1.25 on each axis
    scale_at = _find_one(o, struct.pack('<3i', *[4096 + 1024] * 3) * 22 + struct.pack('<3i', 5120, 5120, 6144) +
                         bytes(24), 'sPropScaleByKind')
    scales = [list(struct.unpack_from('<3i', o, scale_at + 12 * k)) for k in range(PROP_KIND_COUNT)]
    assert scales[-1] == [0, 0, 0] and offsets[-1] == [0, -14 * 4096, 8 * 4096], (scales[-1], offsets[-1])
    kinds = [{'kind': PROP_KINDS[k], 'model': models[k], 'anim': None if info[k][1] == PROP_ANIM_KIND_COUNT
              else ANIM_KINDS[info[k][1]], 'anim_file': None if info[k][1] == PROP_ANIM_KIND_COUNT
              else anims[info[k][1]], 'static': bool(info[k][2]), 'offset': offsets[k], 'scale': scales[k]}
             for k in range(PROP_KIND_COUNT)]

    # ---- the boulders' falls
    i = _find_one(o, struct.pack('<IhhI', 579, 0x4C, 0x44, 0xffffffff), 'sBoulderFallLocations') \
        if o.find(struct.pack('<IhhI', 579, 0x4C, 0x44, 0xffffffff)) >= 0 else None
    falls = []
    if i is None:          # DIST_WORLD_PUZZLE_FLAG_INVALID's value: whatever B5F's rows hold
        rows = [k for k in range(0, len(o) - 12, 4) if struct.unpack_from('<Ihh', o, k) == (579, 0x4C, 0x44)]
        assert len(rows) == 1, 'overlay 9: sBoulderFallLocations'
        i = rows[0]
    while True:
        mh, x, z, flag = struct.unpack_from('<IhhI', o, i)
        if mh == INVALID:
            break
        falls.append({'map': mh, 'x': x, 'z': z, 'flag': flag if flag < 0x80000000 else -1})
        i += 12
    return {'objects': objects, 'events': events, 'commands': lists, 'simple_props': simple, 'prop_kinds': kinds,
            'boulder_falls': falls}


def defines():
    """The world's constants overlay 9 keeps as immediates in its code (pokeplatinum's #defines)."""
    src = open(os.path.join(DECOMP, 'src', 'overlay009', 'ov9_02249960.c')).read()
    out = {}
    for name in ('WATERFALL_B4F_X', 'WATERFALL_B4F_Y', 'WATERFALL_B4F_START_Z', 'WATERFALL_B4F_END_Z',
                 'WATERFALL_B5F_X', 'WATERFALL_B5F_Y', 'WATERFALL_B5F_START_Z', 'WATERFALL_B5F_END_Z',
                 'B7F_TELEPORT_TILE_X', 'B7F_TELEPORT_TILE_Y', 'B7F_TELEPORT_TILE_Z', 'B7F_TELEPORT_SCRIPT_ID',
                 'GIRATINA_ROOM_TELEPORT_TILE_X', 'GIRATINA_ROOM_TELEPORT_TILE_Y', 'GIRATINA_ROOM_TELEPORT_TILE_Z',
                 'GIRATINA_ROOM_TELEPORT_SCRIPT_ID', 'GIRATINA_ROOM_POST_BATTLE_CYNTHIA_TILE_X',
                 'GIRATINA_ROOM_POST_BATTLE_CYNTHIA_TILE_Y', 'GIRATINA_ROOM_POST_BATTLE_CYNTHIA_TILE_Z',
                 'GHOST_PROP_OPACITY_MIN', 'GHOST_PROP_OPACITY_MAX', 'OBSTACLE_PROP_ANIM_DELTA',
                 'PLATFORM_PROP_ANIM_DELTA', 'FOG_OFFSET', 'FOG_ALPHA', 'FOG_DENSITY', 'DISTORTION_WORLD_MIN_Y',
                 'DISTORTION_WORLD_MAX_Y', 'SKY_BACKGROUND_MIN_DARKNESS', 'SKY_BACKGROUND_MAX_DARKNESS'):
            m = re.search(r'^#define ' + name + r'\s+(.+?)\s*$', src, re.M)
            assert m, name
            out[name] = m.group(1)
    return out


def local_objects(world, floors):
    """{map: [object]} with each object's tile in its floor's own tiles (x, z, and y the height in tiles)."""
    out = {}
    for f in floors:
        ox, oy, oz = f['offset']
        out[f['map']] = [{**o, 'x_local': o['x'] - ox, 'z_local': o['z'] - oz,
                          'y_local': (o['y_fx'] >> 16) - oy} for o in world['objects'][f['map']]]
    return out


def zone_events(map_header, ev, world=None, floors=None):
    """A floor's events in its own tiles, with overlay 9's people: what the build installs for the zone (gen4_extract,
    Platinum). Platinum's event files use the shared world's tiles: each event less the floor's offset. Its people are
    in overlay 9: each local id once (the first template, as Platinum's floor first shows it), always spawned (no hide
    flag: Platinum's are 0 but the Turnback room's Griseous Orb ball's, which keeps it);
    the engine's world code (src/pearlb2/plat_dw/dw_world.c) keeps Platinum's rules at the zone's load: the template
    whose condition holds places the person, none deletes it, and the scripts add the rest (ActorAdd)."""
    world = world or read()
    floors = floors or {f['map']: f for f in dwd.read_tables()['floors']}
    ox, oy, oz = floors[map_header]['offset']
    out = {'bg_events': [{**b, 'x': b['x'] - ox, 'z': b['z'] - oz, 'y': b['y'] - oy * 16 if b['y'] else b['y']}
                         for b in ev['bg_events']],
           'object_events': [{**o, 'x': o['x'] - ox, 'z': o['z'] - oz, 'y': o['y'] - oy} for o in ev['object_events']],
           'warp_events': [{**w, 'x': w['x'] - ox, 'z': w['z'] - oz} for w in ev['warp_events']],
           'coord_events': [{**c, 'x': c['x'] - ox, 'z': c['z'] - oz} for c in ev['coord_events']]}
    seen = {o['id'] for o in out['object_events']}
    for o in world['objects'][map_header]:
        if o['local_id'] in seen:
            continue
        seen.add(o['local_id'])
        out['object_events'].append({'id': o['local_id'], 'graphics_id': o['gfx'], 'movement_type': o['movement'],
                                     'trainer_type': o['trainer_type'], 'hidden_flag': o['hidden_flag'], 'script': o['script'],
                                     'initial_dir': o['dir'], 'data': o['data'], 'movement_range_x': o['range'][0],
                                     'movement_range_z': o['range'][1], 'x': o['x'] - ox, 'z': o['z'] - oz,
                                     'y': (o['y_fx'] >> 16) - oy, 'dw': True})
    return out


def check(world):
    """The dump's tables against pokeplatinum's C: counts and a few rows by name."""
    src = open(os.path.join(DECOMP, 'src', 'overlay009', 'ov9_02249960.c')).read()
    n_obj = len(re.findall(r'^static const DistWorldObjectEvent sMapObjectEvent\w+ = \{', src, re.M))
    got = sum(1 for v in world['objects'].values() for o in v if not o.get('passenger'))
    assert got == n_obj, (got, n_obj)
    n_ev = sum(len(re.findall(r'\.cmds = ', m)) for m in re.findall(r'static const DistWorldEvent sMapEvents\w+\[\] = \{(.*?)\n\};',
                                                                    src, re.S))
    got_ev = sum(len(v) for v in world['events'].values())
    assert got_ev == n_ev, (got_ev, n_ev)
    tur = world['objects'][583]
    assert [(o['x'], o['z'], o['y_fx'] >> 16) for o in tur] == [(0x74, 0x4A, 65), (0x59, 0x37, 65)], tur
    return f'{got} people, {got_ev} events, {len(world["commands"])} command lists, ' \
           f'{sum(len(v) for v in world["simple_props"].values())} simple props, {len(world["boulder_falls"])} ' \
           f'boulder falls: the dump agrees with pokeplatinum\'s C'


def main():
    import version
    world = read()
    tables = dwd.read_tables()
    floors = {f['map']: f for f in tables['floors']}
    objs = local_objects(world, tables['floors'])
    out = {'note': 'Generated by b2tools/platinum_dw_world.py from Platinum\'s dump (overlay 9): don\'t edit. Tiles '
                   'in Platinum\'s shared world; *_local in the floor\'s own tiles (less its offset). y_fx: Platinum\'s '
                   'fx32 height (units of 1/4096, 16 units a tile).',
           'floors': {floors[m]['name']: {'map': m, 'zone': floors[m]['zone'], 'offset': floors[m]['offset'],
                                          'objects': objs[m],
                                          'events': [{**e, 'x_local': e['x'] - floors[m]['offset'][0],
                                                      'y_local': e['y'] - floors[m]['offset'][1],
                                                      'z_local': e['z'] - floors[m]['offset'][2]}
                                                     for e in world['events'][m]],
                                          'simple_props': [{**p, 'x_local': p['x'] - floors[m]['offset'][0],
                                                            'y_local': p['y'] - floors[m]['offset'][1],
                                                            'z_local': p['z'] - floors[m]['offset'][2]}
                                                           for p in world['simple_props'][m]]}
                      for m in MAPS},
           'commands': world['commands'], 'prop_kinds': world['prop_kinds'],
           'boulder_falls': world['boulder_falls'], 'defines': defines()}
    path = version.data_out('distortion_world_story.json')
    with open(path, 'w') as fh:
        json.dump(out, fh, indent=1)
    print(f'{path}: {sum(len(v) for v in world["objects"].values())} people, '
          f'{sum(len(v) for v in world["events"].values())} events')
    if '--check' in sys.argv:
        print(check(world))


if __name__ == '__main__':
    main()


# ---- the engine's world tables (include/pearlb2/plat_dw.h DwWorld*, the same layout): in overlay 377's pool after the core's
WORLD_MAGIC = b'PDWW'
WORLD_VERSION = 1
WORLD_HEADER = '<4sHH11I8H'     # magic, floors, version; offsets: floors, command lists, prop kinds, falls, ids; counts
WORLD_FLOOR = '<HHHHHHHHIIIII'  # map, zone, objects, events, simple props, ghost templates, ghost triggers, ghost default visible; offsets
WORLD_OBJECT = '<HBBHhhhiHH'    # uid, condition, rotated, condition value, rotation, x, z (local tiles), y (fx32, local), dir, script
WORLD_EVENT = '<hhhBBHH'        # x, y, z (local tiles), condition, pad, condition value, command list
WORLD_SIMPLE = '<HhhhBBH'       # prop kind, x, y, z (local), condition, pad, condition value
WORLD_GHOST = '<BBhhh'          # group, prop kind, x, y, z (local)
WORLD_GHOST_TRIGGER = '<BBBB6h'  # group, direction, show, pad, bounds (local)
WORLD_PROP_KIND = '<HHBB2x3i3i'  # model file, animation file (0xffff none), animation kind (5 none), static, offset, scale
# (plat-dwplay) The portal's disc (fldeff.narc 0x94, one quad; its joint animation 0xC1 stands it up 55 degrees and spins
# it about its own normal (0, cos 55, sin 55), 12.57 units up and 7.18 north) lies on 1F's cliff slope by the arrival point
# (56.3 degrees: its normal (0, 0.555, 0.832)), 0.2 to 0.6 units behind the face. That is about the DS's Z-buffer step
# there (15-bit z/w: about 0.08 units at 670 units with Platinum's near 150), so melonDS's depth fought it on every view: the
# flicker and the dark band of the user's v3 shot (DeSmuME resolves it as hidden). The packed offset moves the disc 2 units
# along its normal, clear of the face it stands on (the project's 2-unit rule for layers, notes/MAP_LOOK.md). The JSON keeps
# Platinum's own sPropInitialPosOffsetByKind (--check)
PORTAL_LIFT = (0, round(2 * 0.5736 * 4096), round(2 * 0.8192 * 4096))
WORLD_FALL = '<Hhhh'            # floor's map, x, z (local), the puzzle flag (-1 none, 17 Platinum's invalid)
WORLD_CAMERA = '<6h3Hhi'        # DwCameraTrigger: bounds, angles (Platinum's 256ths), direction, steps


def _rgb(r, g, b):
    return r | g << 5 | b << 10


# (plat-dw-rom, 2026-11-08) Overlay 9's small tables the world's C uses, moved out of overlay 377 (dw_world.c had them as
# rodata: the overlay was full). include/pearlb2/plat_dw.h DwWorldConsts, the same order; Platinum's numbers, as the C had them
WORLD_CONSTS = {
    # sGiratinaRoomPlatformsShownCameraAngle; UpdateCascadeDownCamera's two, UpdateCascadeUpCamera's (direction 0, up)
    'cameras': [((0x10, 0, 0), 0x14), ((245, 239, 0), 72), ((0, 0, 0), 32), ((55, 240, 0), 16)],
    # DistWorldPlatformProp_AnimTick and DistWorldObstacleProp_AnimTick's bob, fx32
    'platform_bob': [0x0, -0x1000, -0x2000, -0x4000, -0x5000, -0x5800, -0x5c00, -0x6000],
    # the trio's hover (EventCmdShowUxieBoulderTuto), fx32
    'hover_y': [0, 2048, 4096, 8192, 16384, 24576, 28672, 32768],
    # sGiratinaSpriteBasePalette
    'giratina_palette': [_rgb(9, 22, 12), _rgb(21, 6, 8), _rgb(15, 2, 4), _rgb(13, 13, 15), _rgb(16, 16, 18), _rgb(9, 9, 10),
                         _rgb(18, 19, 21), _rgb(21, 22, 24), _rgb(31, 31, 26), _rgb(29, 26, 3), _rgb(10, 9, 2),
                         _rgb(21, 18, 2), _rgb(30, 10, 8), _rgb(6, 6, 6), _rgb(0, 0, 0), _rgb(31, 31, 31)],
    # sGiratinaShadowExternal[0]: 1F's crying flight east (x, y, z, rotation, sound, scale, delta, steps)
    'shadow_external': (6, 297, 42, 3, 1, (4096, 4096, 4096), (48 * 4096, 0, 0), 64),
    # B6F's trio bob (ov5_021EC9E8), in 0x800 (0.5 units)
    'trio_bob': [0, 1, 2, 4, 8, 11, 14, 16, 15, 13, 10, 6, 4, 2, 1, 0],
    # MapObjectAnimCmd lists (action, count; Black 2's action commands have Platinum's numbers: pearl_movement.json), 0xff
    'azelf_hint': [66, 1, 7, 1, 7, 1, 10, 1, 6, 1, 65, 1, 0xff],
    'mesprit_hint_top': [66, 1, 15, 2, 16, 2, 19, 2, 17, 2, 18, 2, 16, 2, 19, 2, 17, 2, 18, 2, 18, 2, 14, 1, 10, 1, 66, 1, 11,
                         2, 7, 1, 65, 1, 0xff],
    'mesprit_hint_bottom': [66, 1, 15, 2, 16, 1, 19, 2, 17, 2, 18, 2, 16, 2, 19, 2, 17, 2, 18, 2, 16, 1, 18, 2, 14, 1, 10, 1,
                            66, 1, 11, 2, 7, 1, 65, 1, 0xff],
    'player_hint': [66, 1, 63, 2, 2, 1, 60, 3, 0, 1, 60, 3, 3, 1, 60, 3, 1, 1, 60, 3, 2, 1, 60, 3, 0, 1, 60, 3, 3, 1, 60, 3,
                    1, 1, 60, 3, 2, 1, 0xff],
}
CONSTS_BYTES = {'trio_bob': 16, 'azelf_hint': 13, 'mesprit_hint_top': 35, 'mesprit_hint_bottom': 37, 'player_hint': 39}


def consts_blob(k=WORLD_CONSTS):
    """DwWorldConsts: the four camera triggers, the bobs, Giratina's palette, 1F's shadow, the trio's bob and hint lists."""
    out = b''.join(struct.pack(WORLD_CAMERA, 0, 0, 0, 0, 0, 0, *a, 0, steps) for a, steps in k['cameras'])
    out += struct.pack('<8i', *k['platform_bob']) + struct.pack('<8i', *k['hover_y'])
    out += struct.pack('<16H', *k['giratina_palette'])
    x, y, z, rot, sound, scale, delta, steps = k['shadow_external']
    out += struct.pack('<3hbB3i3ii', x, y, z, rot, sound, *scale, *delta, steps)
    for name, n in CONSTS_BYTES.items():
        assert len(k[name]) == n, name
        out += bytes(k[name])
    return out
CMD_PARAM_SIZES = {'set_map_object_animation': 8, 'move_platform': 24, 'add_map_object': 4, 'delete_map_object': 4,
                   'cascade_up': 36, 'cascade_down': 36, 'start_script': 4, 'set_progress': 4, 'show_giratina_shadow': 36,
                   'set_giratina_animation_flag': 4, 'set_puzzle_flag': 4, 'clear_puzzle_flag': 4}


def cmd_params(c, floors):
    """A command's parameters as Platinum's struct bytes (positions made local where Platinum's are absolute)."""
    p, name = c['params'], c['cmd']
    if p is None:
        return b''
    if name in ('start_script', 'set_progress', 'set_giratina_animation_flag', 'set_puzzle_flag', 'clear_puzzle_flag',
                'delete_map_object'):
        return struct.pack('<I', p['value'])
    if name == 'add_map_object':
        return struct.pack('<HH', p['map'], p['local_id'])
    if name == 'set_map_object_animation':
        return struct.pack('<II', p['local_id'], p['action'])
    if name == 'move_platform':
        return struct.pack('<3H3h3i', p['platform'], p['move_player'], p['dummy'], *p['final'], *p['delta'])
    if name in ('cascade_up', 'cascade_down'):
        return struct.pack('<IH9h3i', p['axis'], p['dir'], *p['finishing_fix'], *p['final_offset'], *p['map_load_offset'],
                           *p['delta'])
    if name == 'show_giratina_shadow':
        return struct.pack('<3hbB3i3ii', p['x'], p['y'], p['z'], p['rot_index'], p['sound'], *p['scale'], *p['delta'],
                           p['steps'])
    raise AssertionError(name)


def world_blob(world=None, tables=None, ids=None, files=None):
    """The world's tables for the engine (dw_world.c): the floors' people, events, simple props and ghost props in their own
    tiles; the command lists (each command: kind, size, then Platinum's parameter struct, the list ended by 0xff); the prop
    kinds (their files in a/2/9/5: files = {'model': first, 'anim': {narc index: file}, 'giratina': (model, texture)});
    the boulders' falls; the ids (Black 2's works and flags: ids = {'progress', 'cyrus', 'shadow1', 'shadow2', 'puzzle',
    'stones'})."""
    world = world or read()
    tables = tables or dwd.read_tables()
    floors = tables['floors']
    ids = ids or {'progress': 0, 'cyrus': 0, 'shadow1': 0, 'shadow2': 0, 'puzzle': 0, 'stones': 0}
    files = files or {'model': 0, 'anim': {}, 'giratina': (0, 0)}
    head = struct.calcsize(WORLD_HEADER)
    out = bytearray(head)

    def align():
        out.extend(b'\0' * (-len(out) % 4))

    # the command lists
    align()
    list_offsets = []
    for cmds in world['commands']:
        list_offsets.append(len(out))
        for c in cmds:
            pb = cmd_params(c, floors)
            assert len(pb) == CMD_PARAM_SIZES.get(c['cmd'], 0), (c, len(pb))
            out.extend(struct.pack('<BBH', CMDS.index(c['cmd']), len(pb), 0) + pb)
        out.extend(struct.pack('<BBH', 0xff, 0, 0))
    align()
    list_table = len(out)
    out.extend(b''.join(struct.pack('<I', o) for o in list_offsets))
    # the floors
    rows = []
    for f in floors:
        m = f['map']
        ox, oy, oz = f['offset']
        align()
        obj_off = len(out)
        for o in world['objects'][m]:
            out.extend(struct.pack(WORLD_OBJECT, o['local_id'], CONDS.index(o['cond']), int(o['rotated']), o['cond_value'],
                                   o['rotation'], o['x'] - ox, o['z'] - oz, o['y_fx'] - (oy << 16), o['dir'] & 0xffff,
                                   o['script']))
        align()
        ev_off = len(out)
        for e in world['events'][m]:
            out.extend(struct.pack(WORLD_EVENT, e['x'] - ox, e['y'] - oy, e['z'] - oz, CONDS.index(e['cond']), 0,
                                   e['cond_value'], e['commands']))
        align()
        sp_off = len(out)
        for s in world['simple_props'][m]:
            out.extend(struct.pack(WORLD_SIMPLE, s['kind_id'], s['x'] - ox, s['y'] - oy, s['z'] - oz, CONDS.index(s['cond']),
                                   0, s['cond_value']))
        g = f['ghost_props'] or {'default_visible': 0, 'templates': [], 'triggers': []}
        align()
        gt_off = len(out)
        for t in g['templates']:
            out.extend(struct.pack(WORLD_GHOST, t['group'], t['kind'], t['x'] - ox, t['y'] - oy, t['z'] - oz))
        align()
        gtr_off = len(out)
        for t in g['triggers']:
            b = t['bounds']
            out.extend(struct.pack(WORLD_GHOST_TRIGGER, t['group'], t['dir'] & 0xff, t['show'] & 0xff, 0, b['x'] - ox,
                                   b['y'] - oy, b['z'] - oz, b['sx'], b['sy'], b['sz']))
        rows.append(struct.pack(WORLD_FLOOR, m, f['zone'], len(world['objects'][m]), len(world['events'][m]),
                                len(world['simple_props'][m]), len(g['templates']), len(g['triggers']),
                                g['default_visible'] & 0xffff, obj_off, ev_off, sp_off, gt_off, gtr_off))
    align()
    floor_off = len(out)
    for r in rows:
        out.extend(r)
    align()
    kind_off = len(out)
    for k in world['prop_kinds']:
        anim = k['anim_file']
        offset = k['offset']
        if k['kind'] == 'portal':
            offset = [v + d for v, d in zip(offset, PORTAL_LIFT)]
        out.extend(struct.pack(WORLD_PROP_KIND, files['model'] + PROP_KINDS.index(k['kind']),
                               0xffff if anim is None else files['anim'].get(anim, 0xffff),
                               PROP_ANIM_KIND_COUNT if k['anim'] is None else ANIM_KINDS.index(k['anim']), int(k['static']),
                               *offset, *k['scale']))
    align()
    fall_off = len(out)
    by_map = {f['map']: f for f in floors}
    for fl in world['boulder_falls']:
        ox, _, oz = by_map[fl['map']]['offset']
        out.extend(struct.pack(WORLD_FALL, fl['map'], fl['x'] - ox, fl['z'] - oz, fl['flag']))
    align()
    consts_off = len(out)                           # (plat-dw-rom) DwWorldConsts
    out.extend(consts_blob())
    struct.pack_into(WORLD_HEADER, out, 0, WORLD_MAGIC, len(floors), WORLD_VERSION, floor_off, list_table, kind_off, fall_off,
                     consts_off, 0, 0, 0, 0, 0, 0,
                     len(world['commands']), len(world['prop_kinds']), len(world['boulder_falls']), ids['progress'],
                     ids['cyrus'], ids['shadow1'], ids['shadow2'], ids['puzzle'])
    return bytes(out)
