"""The Battle Frontier's picture rooms (plat-frontier-rooms, 2026-11-07; b2tools/frontier_rooms.py, notes/PLATINUM_FRONTIER.md
"The picture rooms"): the Factory's, Hall's, Castle's and Arcade's corridors and battle rooms as Black 2 field rooms, zones
719-726. Platinum only (its build list, after sinnoh_music: each room copies its lobby's music, place and flags; before scripts
and sinnoh_story, which give the rooms their script, text and people as pearl_story's pseudo maps 593-600).

apply(files), for each room:
- a/0/0/8: its chunks (frontier_rooms.build: the picture's quads, flat tiles, floor where the scene's people go), appended;
- a/0/0/9: its matrix (format 0), appended;
- a/0/1/4: one texture set per facility (its rooms' picture blocks; the textures are named by room, so the two rooms of a
  facility share one set and one area);
- a/0/1/3: one area per facility, appended (AREA_COUNT, decomp area_data.c, holds them: Black 2's 409, the Secret Base's,
  and these four), a copy of its lobby's area record (Pearl's indoor light and outlines) with the set and an empty building
  pack (a/2/2/6 + a/1/7/5, appended once: no building stands in a picture room);
- a/0/5/9: the rooms' camera (frontier_rooms.camera_record: straight down nearly, a texel a pixel, W-buffered), once per
  target offset;
- a/1/2/6: an empty entity file of its own (sinnoh_story writes its people into it);
- a/0/1/2: its zone header: its lobby's (music, place name, weather, flags, battle background) with map type 16, its area,
  matrix, camera, entity file, no camera boundary, the lobby as parent.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402
import narcio, zoneheaders  # noqa: E402
from b2files import arc_path  # noqa: E402

CHUNKS, MATRICES, AREAS, TEXSETS, PACKS, PACK_TEX, CAMERAS, ENTITIES = 8, 9, 13, 14, 226, 175, 59, 126
AREA_COUNT = 0x1A1          # decomp src/system/area_data.c (PEARLB2): records past it read as area 0
EMPTY_ENTITIES = 3          # Black 2's empty entity file (zoneheaders.EMPTY_ENTITIES): copied, never written into


def apply(files):
    if not version.PLATINUM:
        return "platinum_frontier_rooms: Platinum only (nothing)"
    import frontier_rooms as F, pearl_buildings, maplook
    headers, hentries = zoneheaders.load(files)
    assert len(headers) > max(r['zone'] for r in F.ROOMS), \
        'frontier_rooms: the zone table has no block for the rooms (allocate_sinnoh FRONTIER_ROOMS_BLOCK, sinnoh_world)'
    lobby_zone = {r['lobby']: 688 + ['FACTORY', 'HALL', 'CASTLE', 'ARCADE'].index(r['name'].split('_')[2]) for r in F.ROOMS}

    # an empty building pack for the rooms' areas
    pack, ptex = pearl_buildings.build_pack([])
    packs, btex = narcio.load(files, PACKS), narcio.load(files, PACK_TEX)
    assert len(packs) == len(btex)
    pack_id = len(packs)
    packs.append(pack)
    btex.append(ptex)
    narcio.save(files, PACKS, packs)
    narcio.save(files, PACK_TEX, btex)

    # a texture set and an area per facility
    path = arc_path(files, AREAS)
    tab = bytearray(open(path, 'rb').read())
    sets = narcio.load(files, TEXSETS)
    area_of = {}
    for facility, rooms in F.facilities().items():
        btx = F.facility_texture_set(facility)[0]
        set_id = len(sets)
        sets.append(btx)
        area = len(tab) // 10
        assert area < AREA_COUNT, f'frontier_rooms: area {area} is past AREA_COUNT {AREA_COUNT} (area_data.c)'
        lobby = headers[lobby_zone[rooms[0]['lobby']]]
        rec = bytearray(tab[10 * lobby['area']:10 * lobby['area'] + 10])
        assert rec[6] == 0, f'{rooms[0]["lobby"]}: not an interior area'
        struct.pack_into('<HH', rec, 0, pack_id, set_id)
        rec[4] = rec[5] = 0xFF                       # no texture animations
        tab += rec
        for r in rooms:
            area_of[r['name']] = (area, set_id)
    open(path + '.tmp', 'wb').write(tab)
    os.replace(path + '.tmp', path)
    narcio.save(files, TEXSETS, sets)

    # chunks, matrices, cameras, entity files, headers
    chunks, mats, ents = narcio.load(files, CHUNKS), narcio.load(files, MATRICES), narcio.load(files, ENTITIES)
    cam0 = narcio.load(files, CAMERAS)[0][0:44]
    out = []
    for r in F.ROOMS:
        b = F.build(r, F.floor_tiles(r))
        mw, mh = b['size']
        ids = []
        for cz in range(mh):
            for cx in range(mw):
                ids.append(len(chunks))
                chunks.append(b['chunks'][(cx, cz)])
        matrix = len(mats)
        mats.append(struct.pack('<HHHH', 0, 0, mw, mh) + struct.pack(f'<{len(ids)}I', *ids))
        tx, tz, dx, dz = F.camera_tile(r, *F.player_place(r))
        cam = maplook._record_index(files, F.camera_record(cam0, dx, dz))
        assert cam < 0x80, f'camera record {cam}: the zone header keeps 7 bits'
        ent = len(ents)
        ents.append(ents[EMPTY_ENTITIES])
        lob = lobby_zone[r['lobby']]
        hd = dict(headers[lob])
        hd.update(map_type=16, area=area_of[r['name']][0], matrix=matrix, entities=ent, parent=lob, cam_bound=0xFFFF,
                  fly_x=0, fly_y=0, fly_z=0, npc_cache=zoneheaders.NO_PRELOAD, encounters=zoneheaders.NO_ENCOUNTERS, enc_slot=0,
                  scripts=zoneheaders.EMPTY_SCRIPTS, init_scripts=zoneheaders.EMPTY_INIT)
        hd['weather_word'] = (hd['weather_word'] & ~0x3F & ~(0x7F << 9)) | (cam << 9)
        headers[r['zone']] = hd
        out.append(f'{r["name"][4:]} {r["zone"]} (matrix {matrix} {mw}x{mh}, area {area_of[r["name"]][0]}, camera {cam})')
    narcio.save(files, CHUNKS, chunks)
    narcio.save(files, MATRICES, mats)
    narcio.save(files, ENTITIES, ents)
    zoneheaders.save(files, headers, hentries)
    return f'frontier_rooms: {len(F.ROOMS)} rooms: {", ".join(out)}; building pack {pack_id}'


if __name__ == "__main__":          # offline: python3 b2tools/patches/platinum_frontier_rooms.py FILES_DIR (a scratch clone)
    print(apply(sys.argv[1]))
