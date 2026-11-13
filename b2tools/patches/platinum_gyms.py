"""Platinum's own Gyms where they differ from Pearl's (2026-11-02, plat-gyms): the Eterna Gym's flower clock, the Veilstone
Gym's punching bags and tire stacks, the Hearthome Gym's dark rooms, as Black 2's gimmicks 65, 66 and 67 (the decomp's
src/pearlb2/plat_gyms/, overlay 374, dispatched by src/pearlb2/gimmick_itcm.c). The data: b2tools/platinum_gym_data.py,
read from the Platinum dump. List it after veilstone_gym (it appends to the same model archive, after Sunyshore's gears
and, in a Pearl or Diamond build, Pearl's panels):

    build_rom.py ... sunyshore_gym veilstone_gym platinum_gyms game_clear

A Pearl or Diamond build: nothing (their Gyms are Pearl's own). A Platinum build:
- apply(files): the gimmick table (a/1/0/2) gives Platinum's Eterna Gym gimmick 65, its Veilstone Gym 66, its four
  Hearthome Gym rooms 67; Platinum's models and animations are appended to a/2/9/5 (ARCID_GIMMICK_EXPOBJ_MARINETUBE,
  as the Sunyshore Gym's gears);
- apply_code(code): the tables (include/pearlb2/plat_gyms.h) in overlay 374's own pool (PEARLB2_PLATGYM_POOL, in its
  file, so they cost the resident pool nothing), their address in gPlatGymTables (NULL: no gimmick does anything).
The sounds are guesses: Platinum's have no Black 2 equals, and PearlB2 ports no sound effects.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402
sys.path.insert(0, HERE)
import narcio  # noqa: E402

GIMMICK_TABLE_ARC = 102
MODEL_ARC = 295
OVERLAY = 374
# The C's struct sizes (src/pearlb2/plat_gyms/plat_gyms_common.c checks the same numbers)
SIZES = {'eterna': 380, 'veilstone': 598, 'hearthome_room': 88, 'hearthome': 812, 'tables': 16}
# [guess] Platinum's sounds -> Black 2's
SOUNDS = {
    'eterna_tick': 'SEQ_SE_FLD_148',        # SEQ_SE_PL_TOKEI21, the clock's hands turning (the gears' and panels' sound)
    'eterna_done': 'SEQ_SE_DECIDE2',        # SEQ_SE_DP_PIRORIRO2, the clock stops
    'eterna_drain': 'SEQ_SE_SW_MIZUGYM_01',  # SEQ_SE_DP_T_AME, the fountain draining (the Pastoria Gym's water)
    'veilstone_kick': 'SEQ_SE_WALL_HIT',    # SEQ_SE_PL_SUTYA2, the kick
    'veilstone_slide': 'SEQ_SE_FLD_148',    # SEQ_SE_PL_GYM01, the bag sliding
    'veilstone_stop': 'SEQ_SE_WALL_HIT',    # SEQ_SE_PL_GYM02, the bag stops
    'veilstone_topple': 'SEQ_SE_SW_GRGYM_01',  # SEQ_SE_DP_UG_026, a tire stack falls
}
BADGE_FLAG = 2414                           # pearl_story.inc pl_GiveBadge: Black 2's flag 2414 + the badge
FOREST_BADGE, RELIC_BADGE = 1, 4            # Gardenia's and Fantina's badges (Pearl's and Platinum's numbers)


def gyms():
    import platinum_gym_data
    return platinum_gym_data


def _b2_zones():
    w = json.load(open(version.data_path('sinnoh_world.json')))
    return {v['name']: v['b2_zone'] for v in list(w['zones'].values()) + list(w['rooms']['zones'].values())}


def zones():
    """{Black 2 zone: gimmick id} of Platinum's three Gyms."""
    g, b2 = gyms(), _b2_zones()
    out = {b2[g.ETERNA_ZONE]: g.ETERNA_GIMMICK, b2[g.VEILSTONE_ZONE]: g.VEILSTONE_GIMMICK}
    out.update({b2[z]: g.HEARTHOME_GIMMICK for z in g.HEARTHOME_ZONES})
    return out


def first_file():
    """Where Platinum's models start in a/2/9/5: after Black 2's, Sunyshore's gears and (Pearl's Gym only) the panels."""
    import veilstone_gym
    return veilstone_gym.first_file() + (len(veilstone_gym.gym.MODELS) if veilstone_gym.gym.GYM_KIND == 'panels' else 0)


def apply(files):
    if not version.PLATINUM:
        return f'platinum_gyms: {version.VERSION} has Pearl\'s Gyms: nothing'
    rows = narcio.load(files, GIMMICK_TABLE_ARC)
    table = [struct.unpack_from('<II', rows[0], o) for o in range(0, len(rows[0]), 8)]
    ours = zones()
    clash = [(a, b) for a, b in table if a in ours]
    table = [(a, b) for a, b in table if a not in ours] + sorted(ours.items())
    rows[0] = b''.join(struct.pack('<II', a, b) for a, b in table)
    narcio.save(files, GIMMICK_TABLE_ARC, rows)
    m = narcio.load(files, MODEL_ARC)
    assert len(m) == first_file(), f'a/2/9/5 has {len(m)} files, not {first_file()}: list platinum_gyms after veilstone_gym'
    added = [b for _, b in gyms().files()]
    narcio.save(files, MODEL_ARC, m + added)
    return (f'platinum_gyms: zones {sorted(ours.items())}' + (f' (replacing {clash})' if clash else '') +
            f'; Platinum\'s {len(added)} models and animations = a/2/9/5 files {len(m)}-{len(m) + len(added) - 1}')


def _sound(name):
    import snowpoint_gym
    return snowpoint_gym._sound(name)


def _work(name):
    """A var of Platinum's (its number) or of PearlB2's registry (a PVAR_ name) as Black 2's work."""
    reg = json.load(open(version.data_path('pearl_story_ids.json')))
    if isinstance(name, str):
        return int(reg['new'][name]['b2'], 16)
    return int(reg['vars'][f'0x{name:04X}']['b2'], 16)


def _bits(values):
    out = bytearray((len(values) + 7) // 8)
    for i, v in enumerate(values):
        if v:
            out[i >> 3] |= 1 << (i & 7)
    return bytes(out)


def _file_ids():
    """{name: a/2/9/5 file id} of the appended files (platinum_gym_data.files order)."""
    first = first_file()
    return {name: first + k for k, (name, _) in enumerate(gyms().files())}


def eterna_blob():
    g, f, b2 = gyms(), _file_ids(), _b2_zones()
    e = g.eterna()
    out = struct.pack('<6H', b2[g.ETERNA_ZONE], f['eterna hour hand'], f['eterna minute hand'], f['eterna fountain'],
                      f['eterna fountain running'], f['eterna fountain draining'])
    out += struct.pack('<3h', *e['hand_y'], e['fountain_y'])
    out += struct.pack('<5H', _sound(SOUNDS['eterna_tick']), _sound(SOUNDS['eterna_done']), _sound(SOUNDS['eterna_drain']),
                       _work(0x40AE), BADGE_FLAG + FOREST_BADGE)
    out += bytes([g.CLOCK_LEFT, g.CLOCK_TOP, *g.CLOCK_CENTER, g.FOUNTAIN_Z, g.FOUNTAIN_LEFT_X, g.FOUNTAIN_RIGHT_X, 0])
    out += b''.join(bytes(t) for t in e['times'])
    out += b''.join(struct.pack('<3b', x, z, axis if axis < 2 else 0) for x, z, axis in e['jumps']) + b'\0'
    out += b''.join(_bits(c) for c in e['collision'])
    out += b''.join(_bits(f_) for f_ in e['fountain'])
    out += struct.pack(f'<{len(e["heights"])}b', *e['heights'])
    out += struct.pack('<12H', *e['rotation'])
    assert len(out) == SIZES['eterna'], len(out)
    return out


def veilstone_blob():
    g, f, b2 = gyms(), _file_ids(), _b2_zones()
    v = g.veilstone()
    out = struct.pack('<H', b2[g.VEILSTONE_ZONE])
    out += struct.pack('<3H', *(f[f'veilstone model {m}'] for m in g.VEILSTONE_MODELS))
    out += struct.pack('<12H', *(f[f'veilstone anim {a}'] for a in g.VEILSTONE_ANIMS))
    out += struct.pack('<4H', *(_sound(SOUNDS[k]) for k in ('veilstone_kick', 'veilstone_slide', 'veilstone_stop',
                                                              'veilstone_topple')))
    out += struct.pack('<h', v['floor'] + g.OBJECT_Y)
    out += b''.join(bytes(p) for p in v['bags']) + b''.join(bytes(p) for p in v['stacks'])
    out += bytes(v['camera'])
    b = v['behaviors']
    out += bytes(b[2 * i] | b[2 * i + 1] << 4 for i in range(512))
    assert len(out) == SIZES['veilstone'], len(out)
    return out


def hearthome_blob():
    g, f, b2 = gyms(), _file_ids(), _b2_zones()
    h = g.hearthome()
    entrance, room1, room2, leader = (b2[z] for z in g.HEARTHOME_ZONES)
    out = struct.pack('<6H', entrance, leader, g.WRONG_DOOR_WARP, BADGE_FLAG + RELIC_BADGE, f['hearthome light'],
                      f['hearthome light anim'])
    out += struct.pack('<8H', *(f[f'hearthome clue {k}'] for k in range(8)))
    # the player's sprite here (boy, girl; 0 = their own). Platinum's 210 / 211 are the player's own walking sheets
    # (pokeplatinum object_event_gfx_data.c: player_m/f_nsbtx; step 6 found no candle art), drawn without fog
    # (gFogIgnoredModels: BILLBOARD_MODEL_HEARTHOME_GYM_PLAYER): the player keeps theirs
    out += struct.pack('<2H', 0, 0)
    out += b''.join(struct.pack('<3H', *t) for t in h['turns'])
    out += bytes(g.FOG_DENSITY) + bytes([g.LIGHT_TILES])
    for zone, r in zip((room1, room2), h['rooms']):
        doors = list(r['doors']) + [(0, 0)] * (5 - len(r['doors']))
        rec = struct.pack('<H6B', zone, r['first'], r['count'], *r['offset'], *r['size'])
        rec += b''.join(bytes(d) for d in doors) + bytes(2)
        mask = _bits(r['mask'])
        rec += mask + bytes(68 - len(mask))
        assert len(rec) == SIZES['hearthome_room'], len(rec)
        out += rec
    out += b''.join(struct.pack('<3i', *v) for row in h['scale'] for v in row)
    out += b''.join(struct.pack('<3i', *v) for row in h['offset'] for v in row)
    assert len(out) == SIZES['hearthome'], len(out)
    return out


def blob(base):
    """The tables at address base: PlatGymTables, then the three Gyms' (each 4-aligned)."""
    parts = [eterna_blob(), veilstone_blob(), hearthome_blob()]
    at, body = [], b''
    for p in parts:
        body += bytes(-(SIZES['tables'] + len(body)) % 4)
        at.append(base + SIZES['tables'] + len(body))
        body += p
    head = struct.pack('<HH3I', MODEL_ARC, _work('PVAR_GIMMICK_REQUEST'), *at)
    assert len(head) == SIZES['tables']
    return head + body


def apply_code(code):
    if not version.PLATINUM:
        return f'platinum_gyms: {version.VERSION} has Pearl\'s Gyms: no tables'
    import decomp
    slot = decomp.symbol('gPlatGymTables', code)
    pool, end = decomp.symbol('PEARLB2_PLATGYM_POOL', code), decomp.symbol('PEARLB2_PLATGYM_POOL_END', code)
    start = decomp.symbol(f'OV{OVERLAY}_TEXT_START', code)
    if slot is None or pool is None:
        return 'platinum_gyms: this decomp has no overlay 374 (no Platinum Gym code): nothing'
    path = os.path.join(code, f'arm9_ov{OVERLAY}.bin')
    data = bytearray(open(path, 'rb').read())
    b = blob(pool)
    assert pool + len(b) <= end, f'overlay {OVERLAY}\'s pool: {len(b)} B, {end - pool} B there'
    assert data[pool - start: pool - start + len(b)] == bytes(len(b)), 'overlay 374\'s pool is not empty'
    assert data[slot - start: slot - start + 4] == bytes(4), f'gPlatGymTables at {slot:#x}: not NULL'
    data[pool - start: pool - start + len(b)] = b
    data[slot - start: slot - start + 4] = struct.pack('<I', pool)
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(data)
    os.replace(path + '.tmp', path)
    return f'platinum_gyms: tables {len(b)} B at {pool:#x} in overlay {OVERLAY}\'s pool (gPlatGymTables {slot:#x})'


if __name__ == '__main__':
    b = blob(0x021F11C0)
    print(len(b), 'bytes of tables;', 'zones', zones(), 'first file', first_file())
