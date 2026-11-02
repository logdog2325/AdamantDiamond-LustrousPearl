"""Black 2's Pokémon World Tournament in the Battle Park (notes/BATTLE_ZONE.md; after HoennB2's patches/pwt.py and its
notes/RESEARCH_PWT.md). Runs after sinnoh_events and scripts.

The engine keys the PWT on zones 192 (lobby) and 193 (stadium): script plugins 6/7, gimmicks 51/36, the stadium's
subscreen. They stay Black 2's rooms; this patch only connects them:
- the Battle Park's east door of the Exchange building leads to the lobby, and the lobby's exit mat back to that door
  (the west door keeps the Exchange Service Corner; the Corner's east mat still comes out at the east door);
- the lobby's map scripts from src/field_scripts/0385_pwt_lobby_init.s: Black 2's three plus a zone init hiding the
  five Unova story people and clearing the PWT's fly flag (RESEARCH_PWT 4.3, 3). The story tournament's scene is off
  in src/field_scripts/0384_pwt_lobby.s (4.2);
- both rooms get the Battle Park's place name, and the lobby's camera stops before the black south of the entrance.

The tournaments (decomp src/ov055/wbt_tool.c): Sinnoh Leaders open with the Hall of Fame; the left desk's are open from
the start, the first (story) Driftveil tournament never (PearlB2_WbtOpenCount).
"""
import json, os, struct, sys

import narcio, zoneheaders
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from zones import parse_entities, build_entities  # noqa: E402

LOBBY, STADIUM = 192, 193
ENTITIES_ARC, CAMERA_ARC = 126, 109
LOBBY_CAM_BOX = [72, 424, 24, 440]
LOBBY_CAM_ZMAX = 365            # HoennB2: camera 0 shows 82 units south of its target; the floor ends at z 447


def _park_zones():
    world = json.load(open(os.path.join(ROOT, 'data', 'sinnoh_world.json')))
    zones = {e['name']: e['b2_zone'] for e in world['rooms']['zones'].values()}
    return zones['MAP_BATTLE_PARK'], zones['MAP_BATTLE_PARK_EXCHANGE_SERVICE_CORNER']


def apply(files):
    from scripts import assemble
    park, corner = _park_zones()
    headers, hentries = zoneheaders.load(files)
    for z in (LOBBY, STADIUM):
        headers[z]['place'] = headers[park]['place']
    zoneheaders.save(files, headers, hentries)

    ents = narcio.load(files, ENTITIES_ARC)
    pi = headers[park]['entities']
    e, _ = parse_entities(ents[pi])
    doors = sorted((i for i, w in enumerate(e['warps']) if w['dest_zone'] == corner), key=lambda i: e['warps'][i]['x'])
    assert len(doors) == 2, f'pwt: the Battle Park has {len(doors)} doors to the Exchange building'
    east = doors[1]
    e['warps'][east]['dest_zone'], e['warps'][east]['dest_warp'] = LOBBY, 0
    ents[pi] = build_entities(e, ents[pi])

    li = headers[LOBBY]['entities']
    lobby, _ = parse_entities(ents[li])
    assert lobby['warps'][0]['type'] == 1, lobby['warps'][0]
    lobby['warps'][0]['dest_zone'], lobby['warps'][0]['dest_warp'] = park, east
    init = os.path.join(ROOT, 'src', 'field_scripts', '0385_pwt_lobby_init.s')
    ents[li] = build_entities(lobby, ents[li], assemble(init))
    narcio.save(files, ENTITIES_ARC, ents)

    cams = narcio.load(files, CAMERA_ARC)
    box = headers[LOBBY]['cam_bound']
    vals = list(struct.unpack('<7i', cams[box]))
    assert vals[3:] in (LOBBY_CAM_BOX, LOBBY_CAM_BOX[:3] + [LOBBY_CAM_ZMAX]), vals
    vals[6] = LOBBY_CAM_ZMAX
    cams[box] = struct.pack('<7i', *vals)
    narcio.save(files, CAMERA_ARC, cams)
    return f'pwt: Battle Park (zone {park}) door {east} <-> lobby {LOBBY}; place {headers[park]["place"]}'
