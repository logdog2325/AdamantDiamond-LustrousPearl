"""Pearl's Secret Bases (notes/SECRET_BASES.md; decomp src/pearlb2/resident/secret_base.c). Runs after underground and
ramanas_park, before the patches that size tables from the zone headers:

    build_rom.py ... underground ramanas_park secret_bases pearl_starters ...

apply(files)
- The room: zone 670, a 1 x 1 matrix on Pearl's chunk 561 (the tunnels' copy, installed by sinnoh_rooms), a new area record
  (a/0/1/3 grows by one: Black 2 reads it by offset) with the tunnels' textures and light and its own building pack.
- The pack (a/2/2/6, its textures a/1/7/5): Pearl's goods as res = good id, past a bundle's limit of 127: the decomp's
  PearlB2SB_LoadResBundle loads only those in use. + Pearl's data/ug_base_cur.nsbmd, the decorating cursor.
- Its events: the PC's two tiles (sign events, read facing north). Zone 633: the goods traders, at Pearl's tiles.
- Gimmick 64 for zones 633 and 670.
apply_code(code)
- gPearlB2SecretBase: the table in the resident section's pool.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import narcio, nsbtx, zoneheaders, resident, maplook, pearl_buildings, pearl_model_fix, ug_data  # noqa: E402
import secret_base_data as SB, secret_base_scripts as SS  # noqa: E402
from b2files import arc_path, gf_container, gf_container_build  # noqa: E402
from zones import parse_entities, build_entities  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402
import version  # noqa: E402

STATE = os.path.join(ROOT, 'work', 'world', 'secret_bases.json')
EMPTY = struct.pack('<I', 4) + bytes(4) + bytes(4)
EMPTY_INIT = 7
PACKS, TEXTURES, AREAS, MATRICES, ENTITIES, GIMMICKS = 226, 175, 13, 9, 126, 102
TRADER_MODEL = 64                       # Pearl's graphics 20 (data/pearl_sprite_map.json: Hiker)


def build_pack():
    """(pack, textures): every good but the holes, and the cursor. pearl_buildings.build_pack's way, without its 128 limit and
    door and machine records (a good is plain furniture here)."""
    import sinnoh_rooms
    rom = Rom(version.SOURCE_DUMP)
    build = narc_members(rom.read('fielddata/build_model/build_model.narc'))
    models = [(g, build[m]) for g, m in SB.good_models().items() if g not in SB.HOLE_GOODS]
    models.append((SB.RES_CURSOR, rom.read('data/ug_base_cur.nsbmd')))
    texset = None
    for _, bmd in models:
        src = pearl_buildings.btx0_of(bmd)
        texset = src if texset is None else nsbtx.merge(texset, [(src, t, p) for t, p in sorted(nsbtx.material_pairs(bmd))])
    pack = gf_container_build('AB', [pearl_buildings.info(r) for r, _ in models]
                              + [pearl_buildings.mdl_only(b) for _, b in models])
    if os.environ.get('MAP_FIXES') != 'none':
        pack, _ = pearl_model_fix.fix_pack(pack)
    magic, secs = gf_container(pack)
    fixes = maplook.fixes()
    pack = gf_container_build(magic, [sinnoh_rooms.room_model(s, False, fixes) if s[:4] == b'BMD0' else s for s in secs])
    return pack, texset


def apply(files):
    import subprocess
    subprocess.run([sys.executable, os.path.join(os.path.dirname(HERE), 'secret_base_scripts.py'), '--check'], check=True)
    world = json.load(open(version.data_path('sinnoh_world.json')))
    rooms = world['rooms']
    headers, entries = zoneheaders.load(files)
    assert len(headers) > SB.BASE_ZONE, 'secret_bases: the zone table has no block for the base (allocate_sinnoh, sinnoh_world)'
    th = headers[SB.TUNNEL_ZONE]
    assert th['scripts'] == ug_data.data()['files']['script'], 'secret_bases: list it after underground'

    # the pack, and the area record that loads it
    pack, tex = build_pack()
    packs, btex = narcio.load(files, PACKS), narcio.load(files, TEXTURES)
    assert len(packs) == len(btex)
    pack_id = len(packs)
    packs.append(pack)
    btex.append(tex)
    narcio.save(files, PACKS, packs)
    narcio.save(files, TEXTURES, btex)
    path = arc_path(files, AREAS)
    tab = bytearray(open(path, 'rb').read())
    assert len(tab) % 10 == 0
    area = len(tab) // 10
    rec = bytearray(tab[10 * th['area']:10 * th['area'] + 10])
    assert rec[6] == 0, 'the tunnels are an interior area'
    struct.pack_into('<H', rec, 0, pack_id)
    tab += rec
    open(path + '.tmp', 'wb').write(tab)
    os.replace(path + '.tmp', path)

    # the matrix
    mats = narcio.load(files, MATRICES)
    matrix = len(mats)
    mats.append(struct.pack('<HHHH', 0, 0, 1, 1) + struct.pack('<I', rooms['chunks'][str(SB.BASE_CHUNK)]))
    narcio.save(files, MATRICES, mats)

    # the entities: the base's PC, the tunnels' traders
    ents = narcio.load(files, ENTITIES)
    signs = [dict(script=SS.SCRIPT['PC'], cond=0, dir=0, rail=0, x=x, z=12, y=0) for x in (15, 16)]
    base_ent = len(ents)
    ents.append(build_entities({'signs': signs, 'npcs': [], 'warps': [], 'triggers': []}, EMPTY))
    tunnels = ents[th['entities']]
    e, _ = parse_entities(tunnels)
    floor = json.load(open(os.path.join(ROOT, 'work', 'world', 'underground.json')))['tunnel_floor_y']
    npcs = [n for n in e['npcs'] if n['uid'] < SB.TRADER_UID or n['uid'] >= SB.TRADER_UID + 8]     # (a quick rerun)
    for i, (x, z) in enumerate(SB.traders()):
        npcs.append(dict(uid=SB.TRADER_UID + i, model=TRADER_MODEL, move=0, evtype=0, flag=0, script=SS.SCRIPT['Trader'], dir=1,
                         p0=0, p1=0, p2=0, areaw=0, areah=0, rail=0, x=x, z=z, y=floor * 0x1000))
    e['npcs'] = npcs
    ents[th['entities']] = build_entities(e, tunnels)         # (keeps its map scripts)
    narcio.save(files, ENTITIES, ents)

    # the zone
    hd = dict(th)
    hd.update(map_type=16, area=area, matrix=matrix, entities=base_ent, init_scripts=EMPTY_INIT, encounters=0x1FFF, enc_slot=0,
              parent=SB.TUNNEL_ZONE, cam_bound=0xFFFF, fly_x=0, fly_y=0, fly_z=0)
    headers[SB.BASE_ZONE] = hd
    zoneheaders.save(files, headers, entries)

    # gimmick 64
    rows = narcio.load(files, GIMMICKS)
    table = [struct.unpack_from('<II', rows[0], o) for o in range(0, len(rows[0]), 8)]
    table = [(z, g) for z, g in table if z not in (SB.TUNNEL_ZONE, SB.BASE_ZONE)]
    table += [(SB.TUNNEL_ZONE, SB.GIMMICK), (SB.BASE_ZONE, SB.GIMMICK)]
    rows[0] = b''.join(struct.pack('<II', z, g) for z, g in table)
    narcio.save(files, GIMMICKS, rows)

    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump({'pack': pack_id}, open(STATE + '.tmp', 'w'))
    os.replace(STATE + '.tmp', STATE)
    return (f'secret_bases: zone {SB.BASE_ZONE}, matrix {matrix}, area {area}, pack {pack_id} ({len(pack):,} B, textures '
            f'{len(tex):,} B); {len(npcs)} traders')


def apply_code(code):
    import decomp
    state = json.load(open(STATE))
    slot = decomp.symbol('gPearlB2SecretBase', code)
    if slot is None:
        raise SystemExit('secret_bases: the decomp has no gPearlB2SecretBase (src/pearlb2/resident/secret_base.c)')
    world = json.load(open(version.data_path('sinnoh_world.json')))
    res = [world['rooms']['building_res'][str(m)] for m in SB.HOLE_MODELS]
    holes = [h['hole'] for h in ug_data.hideaways()]
    table = SB.blob(state['pack'], res, holes, SS.SCRIPT)
    base, end, _ = resident.install(code, lambda b: (table, {}))
    resident.write(code, slot, struct.pack('<I', base))
    return f'secret_bases: the table {end - base} B at {base:#x} (gPearlB2SecretBase {slot:#x})'
