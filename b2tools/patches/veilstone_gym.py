"""The Veilstone Gym's sliding wall panels (Pearl's Maylene gym; 2026-11-01) as Black 2's gimmick 60 (the decomp's
src/pearlb2/resident/veilstone_gym.c, dispatched by src/pearlb2/gimmick_itcm.c). The data: b2tools/pearl_veilstone_gym.py,
read from the Pearl dump. List it after sinnoh_rooms and zone_effects, and after sunyshore_gym (it appends to the same
model archive, whose patch checks nothing came before it):

    build_rom.py ... sunyshore_gym veilstone_gym game_clear

- apply(files): the gimmick table (a/1/0/2) gives the Gym gimmick 60; Pearl's seven panel models (BMD0 with their
  textures) are appended to a/2/9/5 (ARCID_GIMMICK_EXPOBJ_MARINETUBE, as the Sunyshore Gym's gears);
- apply_code(code): the table in the resident section's pool, its address in gPearlB2VeilstoneGym (NULL: no panels; the
  Gym is then open as converted).
The Gym's zone script (Pearl's InitVeilstoneGym) stays a stub: Black 2 clears the gimmick's saved work on a zone change,
so the panels are back at their start states on every entry, and a battle or a saved game keeps them, as in Pearl.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402
sys.path.insert(0, HERE)
import itcm, resident, narcio  # noqa: E402
import pearl_veilstone_gym as gym  # noqa: E402

VANILLA = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'b2_us', 'files')
SOUND_H = os.path.join(ROOT, 'external', 'pokebw2', 'build', 'include', 'generated', 'constants', 'sound.h')
GIMMICK_TABLE_ARC = 102
MODEL_ARC = 295
SUNYSHORE_MODELS = 7               # patches/sunyshore_gym.py: Pearl's gears come first in the appended files
# [guess] Pearl's sound 0x616 (pokediamond's name SEQ_SE_DP_TV_NOISE; Black 2 has no such sound and PearlB2 ports no
# sound effects): gimmick 59's moving sound, stopped when the panel stops as Pearl stops its own
SOUND = 'SEQ_SE_FLD_148'


def zone():
    world = json.load(open(version.data_path('sinnoh_world.json')))['rooms']['zones']
    return next(v['b2_zone'] for v in world.values() if v['name'] == gym.GYM_ZONE)


def first_file():
    return len(narcio.load(VANILLA, MODEL_ARC)) + SUNYSHORE_MODELS


def apply(files):
    if gym.GYM_KIND != 'panels':
        return f'veilstone_gym: {version.VERSION} has its own Gym ({gym.GYM_KIND}): not built yet, nothing'
    rows = narcio.load(files, GIMMICK_TABLE_ARC)
    table = [struct.unpack_from('<II', rows[0], o) for o in range(0, len(rows[0]), 8)]
    z = zone()
    clash = [(a, b) for a, b in table if a == z]
    table = [(a, b) for a, b in table if a != z] + [(z, gym.GIMMICK_ID)]
    rows[0] = b''.join(struct.pack('<II', a, b) for a, b in table)
    narcio.save(files, GIMMICK_TABLE_ARC, rows)
    from gen4rom import narc_members
    build = narc_members(gym._rom().read('fielddata/build_model/build_model.narc'))
    m = narcio.load(files, MODEL_ARC)
    assert len(m) == first_file(), f'a/2/9/5 has {len(m)} files, not {first_file()}: list veilstone_gym after sunyshore_gym'
    added = []
    for model in gym.MODELS:
        assert build[model][:4] == b'BMD0', f'Pearl build model {model} is not a BMD0'
        added.append(build[model])
    narcio.save(files, MODEL_ARC, m + added)
    return (f'veilstone_gym: zone {z} -> gimmick {gym.GIMMICK_ID}' + (f' (replacing {clash})' if clash else '') +
            f'; Pearl\'s panel models {gym.MODELS[0]}-{gym.MODELS[-1]} = a/2/9/5 files {len(m)}-{len(m) + len(added) - 1}')


def sound_id(name):
    m = re.search(rf'^#define {name} (0x[0-9a-fA-F]+|\d+)', open(SOUND_H).read(), re.M)
    assert m, f'{name} not in {SOUND_H}'
    return int(m.group(1), 0)


def blob(base, first=None, sound=None):
    """The table veilstone_gym.c reads: PearlB2VeilstoneGym, resources, panels, push spots."""
    panels, spots = gym.panels(), gym.push_spots()
    first = first_file() if first is None else first
    sound = sound_id(SOUND) if sound is None else sound
    res = list(gym.MODELS)
    head = 24

    def spans(sp):
        flat = [v for s in sp for v in s]
        return bytes(flat + [0] * (4 - len(flat)))
    body = struct.pack(f'<{len(res)}H', *(first + m - res[0] for m in res))
    body += bytes(-len(body) % 4)
    at_panels = len(body)
    for p in panels:
        body += bytes([res.index(p['model']), p['row'], p['a'], p['b'], p['start'], 0, 0, 0]) + \
            spans(p['spans_a']) + spans(p['spans_b'])
    at_spots = len(body)
    for x, z, f, i in spots:
        body += bytes([x, z, f, i])
    out = struct.pack('<3H3B3xIII', zone(), MODEL_ARC, sound, len(panels), len(res), len(spots),
                      base + head, base + head + at_panels, base + head + at_spots)
    assert len(out) == head
    return out + body


def apply_code(code):
    if gym.GYM_KIND != 'panels':
        return f'veilstone_gym: {version.VERSION} has its own Gym ({gym.GYM_KIND}): no panel table'
    import decomp
    slot = decomp.symbol('gPearlB2VeilstoneGym', code)
    if slot is None:
        return 'veilstone_gym: no gPearlB2VeilstoneGym in this decomp (no panel code): nothing'
    base, end, _ = resident.install(code, lambda b: (blob(b), {}))
    assert resident.read(code, slot, 4) == bytes(4), f'gPearlB2VeilstoneGym at {slot:#x}: not NULL'
    resident.write(code, slot, struct.pack('<I', base))
    return f'veilstone_gym: table {end - base} B at {base:#x} (gPearlB2VeilstoneGym {slot:#x})'


if __name__ == '__main__':
    b = blob(itcm.ITCM_BASE, first=0, sound=0)
    print(len(b), 'bytes; zone', zone(), '; spots', len(gym.push_spots()))
