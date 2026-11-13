"""Which chapter owns each Pearl zone not yet installed (notes/STORY_CHAPTERS.md; next week's chapter agents).

    python3 b2tools/story_chapters.py        writes data/story_chapters.json and prints the counts

Chapters 1, 2 and 90 (every Pokémon Center 1F) stay in pearl_story.CHAPTERS; 3-9 come from the rules below (zone name
prefixes, in Pearl's story order: the first chapter whose story reaches a zone owns it), and pearl_story.py reads
data/story_chapters.json for them. "skip" = zones nothing installs (Pearl's Pokémon Center basements and Union Room:
Black 2's shared 2F does that; an unused route).

    PEARL_VERSION=platinum python3 b2tools/story_chapters.py     writes data/platinum/story_chapters.json (Platinum's order)

Platinum tells the story in another order (notes/PLATINUM_CHAPTERS.md): its own rules (PLATINUM_RULES) give every installed zone a
chapter, 1, 2 and 90 too, since its opening changed as well; only a Platinum build reads that file (version.data_path), so
Pearl's and Diamond's data/story_chapters.json stays as it is. The Distortion World (step 7) and the Battle Frontier with its
Battle Tower (step 8) are in no chapter: the file lists them under "_later".
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

# (chapter, prefixes), first match wins: the more specific prefixes first
RULES = [
    # also: zones on Pearl's empty script file 368 (MAP_EVERYWHERE's: one End, 114 zones) with nothing at all to
    # install (no people, signs, triggers, item balls or hidden items): Jubilife's south-east house 4F and two Old
    # Chateau 2F rooms (2026-10-25, chapter 3). Zones on 368 with any of those stay in their chapters: each gets its
    # own script and text file (pearl_story.PearlData.shared_file_zones, 2026-10-25, chapter 4a).
    ('skip', ['UNION_ROOM', 'ROUTE_231_UNUSED', 'JUBLIFE_POKECENTER_2F', '_POKECENTER_B1F',
              'JUBLIFE_SOUTHEAST_HOUSE_4F', 'OLD_CHATEAU_2F_CORRIDOR', 'OLD_CHATEAU_2F_ROOM_3']),
    (7, ['VEILSTONE_GALACTIC_HEADQUARTERS', 'MOUNT_CORONET_SPEAR_PILLAR', 'MOUNT_CORONET_2F', 'MOUNT_CORONET_3F',
         'MOUNT_CORONET_4F', 'MOUNT_CORONET_5F', 'MOUNT_CORONET_6F', 'MOUNT_CORONET_B1F', 'MOUNT_CORONET_SOUTH_2F',
         'MOUNT_CORONET_SOUTH_3F', 'MOUNT_CORONET_SOUTH_MOUNTAINSIDE', 'MOUNT_CORONET_TUNNEL_ROOM']),
    (5, ['HEARTHOME_GYM']),
    (9, ['FIGHT_AREA', 'BATTLE_PARK', 'BATTLE_TOWER', 'ROUTE_224', 'ROUTE_225', 'ROUTE_226', 'ROUTE_227', 'ROUTE_228',
         'ROUTE_229', 'ROUTE_230', 'SURVIVAL_AREA', 'RESORT_AREA', 'STARK_MOUNTAIN', 'SNOWPOINT_TEMPLE',
         'TURNBACK_CAVE', 'SENDOFF_SPRING', 'SPRING_PATH', 'FULLMOON_ISLAND', 'NEWMOON_ISLAND', 'FLOWER_PARADISE',
         'ROUTE_219', 'ROUTE_220', 'ROUTE_221', 'PAL_PARK', 'TROPHY_GARDEN', 'ETERNA_OAK_HOUSE', 'HALL_OF_ORIGIN']),
    (3, ['JUBLIFE_SOUTHEAST_HOUSE_4F', 'ROUTE_204', 'RAVAGED_PATH', 'FLOAROMA', 'VALLEY_WINDWORKS', 'ROUTE_205',
         'ETERNA', 'FUEGO_IRONWORKS', 'OLD_CHATEAU']),
    (4, ['ROUTE_206', 'WAYWARD_CAVE', 'ROUTE_207', 'MOUNT_CORONET_SOUTH_1F', 'ROUTE_208', 'HEARTHOME', 'AMITY_SQUARE',
         'ROUTE_209', 'SOLACEON', 'ROUTE_210_SOUTH', 'ROUTE_215', 'VEILSTONE']),
    (5, ['ROUTE_214', 'RUIN_MANIAC_CAVE', 'VALOR_LAKEFRONT', 'ROUTE_213', 'PASTORIA', 'GREAT_MARSH', 'ROUTE_212',
         'ROUTE_210_NORTH', 'ROUTE_210_GRANDMA_WILMA_HOUSE', 'ROUTE_210_CAFE', 'CELESTIC', 'ROUTE_211',
         'MOUNT_CORONET_NORTH_1F']),
    (6, ['ROUTE_218', 'CANALAVE', 'IRON_ISLAND', 'LAKE_VALOR', 'VALOR_CAVERN', 'LAKE_VERITY_GALACTIC', 'VERITY_CAVERN',
         'ROUTE_216', 'ROUTE_217', 'ACUITY_LAKEFRONT', 'SNOWPOINT', 'LAKE_ACUITY', 'ACUITY_CAVERN',
         'MOUNT_CORONET_NORTH_MOUNTAINSIDE']),
    (8, ['ROUTE_222', 'SUNYSHORE', 'ROUTE_223', 'VICTORY_ROAD', 'POKEMON_LEAGUE']),
]


def chapter_of(name):
    short = name[4:]
    for ch, prefixes in RULES:
        if any(short.startswith(p) or (p.startswith('_') and short.endswith(p[1:])) for p in prefixes):
            return ch
    return None


# Platinum (2026-11-07, notes/PLATINUM_CHAPTERS.md): (key, names), first match wins. A name is a whole zone name or its first words
# (MOUNT_CORONET_4F is MOUNT_CORONET_4F_ROOM_1 and _ROOM_3; ROUTE_21 would be no route), or with $ the zone alone. Every name must
# match a zone.
_PEARL_CH1 = ['TWINLEAF', 'ROUTE_201', 'VERITY_LAKEFRONT', 'LAKE_VERITY$', 'SANDGEM']   # Pearl's Chapter 1 zones ($: that zone alone)
_PEARL_CENTERS = [f'{t}_POKECENTER_1F' for t in ('JUBLIFE', 'CANALAVE', 'OREBURGH', 'ETERNA', 'HEARTHOME', 'PASTORIA', 'VEILSTONE',
                                                  'SUNYSHORE', 'SNOWPOINT', 'POKEMON_LEAGUE', 'FIGHT_AREA', 'FLOAROMA', 'SOLACEON',
                                                  'CELESTIC', 'SURVIVAL_AREA', 'RESORT_AREA')]
PLATINUM_RULES = [
    ('step7', ['DISTORTION_WORLD']),
    ('step8', ['BATTLE_FRONTIER', 'BATTLE_FACTORY', 'BATTLE_HALL', 'BATTLE_CASTLE', 'BATTLE_ARCADE', 'BATTLE_TOWER']),
    # nothing installs these: as Pearl's skip, and the Underground (its own feature, notes/UNDERGROUND.md) and the Wi-Fi Plaza's
    # entrance (no warp leads there; Wi-Fi is closed)
    ('skip', ['UNION_ROOM', 'ROUTE_231_UNUSED', 'JUBLIFE_POKECENTER_2F', 'JUBLIFE_POKECENTER_B1F', 'CANALAVE_POKECENTER_B1F',
              'OREBURGH_POKECENTER_B1F', 'ETERNA_POKECENTER_B1F', 'HEARTHOME_POKECENTER_B1F', 'PASTORIA_POKECENTER_B1F',
              'VEILSTONE_POKECENTER_B1F', 'SUNYSHORE_POKECENTER_B1F', 'SNOWPOINT_POKECENTER_B1F', 'POKEMON_LEAGUE_POKECENTER_B1F',
              'FIGHT_AREA_POKECENTER_B1F', 'SANDGEM_POKECENTER_B1F', 'FLOAROMA_POKECENTER_B1F', 'SOLACEON_POKECENTER_B1F',
              'CELESTIC_POKECENTER_B1F', 'SURVIVAL_AREA_POKECENTER_B1F', 'RESORT_AREA_POKECENTER_B1F', 'JUBLIFE_SOUTHEAST_HOUSE_4F',
              'OLD_CHATEAU_2F_CORRIDOR', 'OLD_CHATEAU_2F_ROOM_3', 'UNDERGROUND', 'WIFI_PLAZA_ENTRANCE']),
    ('90', _PEARL_CENTERS),
    ('1', _PEARL_CH1),
    # 12 before 3's ETERNA and 11 before 8's SNOWPOINT and 7's IRON_ISLAND; 9's HQ before 5's VEILSTONE
    ('12', ['ETERNA_OAK_HOUSE', 'ROTOMS_ROOM', 'ROUTE_224', 'FLOWER_PARADISE', 'SPEAR_PILLAR_DIALGA', 'SPEAR_PILLAR_PALKIA',
            'HALL_OF_ORIGIN', 'TURNBACK_CAVE', 'ROUTE_219', 'ROUTE_220', 'ROUTE_221', 'PAL_PARK',
            'FULLMOON_ISLAND', 'NEWMOON_ISLAND', 'TROPHY_GARDEN']),
    ('11', ['FIGHT_AREA', 'ROUTE_225', 'ROUTE_226', 'ROUTE_227', 'ROUTE_228', 'ROUTE_229', 'ROUTE_230', 'SURVIVAL_AREA', 'RESORT_AREA',
            'STARK_MOUNTAIN', 'SNOWPOINT_TEMPLE', 'IRON_ISLAND_IRON_RUINS', 'IRON_RUINS', 'MT_CORONET_ICEBERG_RUINS', 'ICEBERG_RUINS',
            'ROCK_PEAK_RUINS']),
    # MOUNT_CORONET_UNUSED_2 is Platinum's Spear Pillar Distorted (its zone 221), where the story enters the Distortion World;
    # the story comes out of it at Sendoff Spring (Cynthia's scene) and leaves by the Spring Path, which the Distortion World opens
    ('9', ['VEILSTONE_GALACTIC_HEADQUARTERS', 'GALACTIC_HQ_HALL', 'MOUNT_CORONET_SPEAR_PILLAR', 'MOUNT_CORONET_UNUSED_2',
           'SENDOFF_SPRING', 'SPRING_PATH',
           'MOUNT_CORONET_SOUTH_2F', 'MOUNT_CORONET_SOUTH_3F', 'MOUNT_CORONET_SOUTH_MOUNTAINSIDE', 'MOUNT_CORONET_4F',
           'MOUNT_CORONET_5F', 'MOUNT_CORONET_6F', 'MOUNT_CORONET_TUNNEL_ROOM', 'MOUNT_CORONET_NORTH_MOUNTAINSIDE']),
    ('2', ['ROUTE_202', 'JUBLIFE', 'GLOBAL_TERMINAL', 'ROUTE_203', 'OREBURGH']),
    ('3', ['ROUTE_204', 'RAVAGED_PATH', 'FLOAROMA', 'VALLEY_WINDWORKS', 'ROUTE_205', 'ETERNA', 'FUEGO_IRONWORKS', 'OLD_CHATEAU']),
    ('4', ['ROUTE_206', 'WAYWARD_CAVE', 'ROUTE_207', 'MOUNT_CORONET_SOUTH_1F', 'ROUTE_208', 'HEARTHOME', 'AMITY_SQUARE']),
    ('5', ['ROUTE_209', 'SOLACEON', 'ROUTE_210_SOUTH', 'ROUTE_215', 'VEILSTONE']),
    ('6', ['ROUTE_214', 'RUIN_MANIAC_CAVE', 'VALOR_LAKEFRONT', 'ROUTE_213', 'PASTORIA', 'GREAT_MARSH', 'ROUTE_212']),
    # the way to Route 216 (Route 211 -> north 1F room 1 -> B1F -> north 1F room 2) is 8's past room 1
    ('7', ['ROUTE_210_NORTH', 'ROUTE_210_GRANDMA_WILMA_HOUSE', 'ROUTE_210_CAFE', 'ROUTE_211', 'MOUNT_CORONET_NORTH_1F_ROOM_1',
           'CELESTIC', 'ROUTE_218', 'CANALAVE', 'IRON_ISLAND']),
    ('8', ['MOUNT_CORONET_B1F', 'MOUNT_CORONET_NORTH_1F_ROOM_2', 'LAKE_VALOR', 'VALOR_CAVERN', 'LAKE_VERITY_GALACTIC', 'VERITY_CAVERN',
           'ROUTE_216', 'ROUTE_217', 'ACUITY_LAKEFRONT', 'SNOWPOINT', 'LAKE_ACUITY', 'ACUITY_CAVERN']),
    ('10', ['ROUTE_222', 'SUNYSHORE', 'ROUTE_223', 'VICTORY_ROAD', 'POKEMON_LEAGUE']),
]
PLATINUM_TITLES = {
    '1': 'Twinleaf to Sandgem: the starter, the first battle, the Pokédex',
    '2': 'Route 202 to Roark: Jubilife, Oreburgh, the Coal Badge',
    '3': 'Floaroma, the Windworks and Eterna: the Forest Badge, the Galactic building, the Bicycle',
    '4': 'Route 206 to Hearthome: the Relic Badge',
    '5': 'Route 209 to Veilstone: the Cobble Badge, Fly',
    '6': 'Route 214 to Pastoria: the Fen Badge, the Great Marsh',
    '7': 'Celestic and Canalave: Cyrus, Surf, the Mine Badge, Iron Island, the library',
    '8': 'The lakes and Snowpoint: Saturn, Mars, the Icicle Badge, Jupiter',
    '9': 'The Galactic HQ, Mt. Coronet and Spear Pillar; the story enters the Distortion World (step 7) and comes out at Sendoff Spring',
    '10': 'Sunyshore and the Pokémon League: the Beacon Badge, the Champion',
    '11': 'Post-game: the Fight, Survival and Resort Areas, Routes 225-230, Stark Mountain, Snowpoint Temple and the Regi ruins',
    '12': 'Post-game: Route 224 and the event islands, Spear Pillar, the Hall of Origin, Turnback Cave, Routes 219-221, Pal Park, '
          'Rotom',
    '90': 'Every Pokémon Center 1F (as Pearl)',
}


def _matches(short, name):
    return short == name[:-1] if name.endswith('$') else short == name or short.startswith(name + '_')


def platinum_main():
    """Platinum's chapters: every installed zone in exactly one chapter, skip or a later step; written to data/platinum."""
    zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    world = json.load(open(version.data_path('sinnoh_world.json')))
    inst = {int(k) for k in world['zones']} | {int(k) for k in world['rooms']['zones']}
    out, unassigned, used = {}, [], set()
    for i, z in enumerate(zones):
        if i not in inst:
            continue
        hit = next(((key, n) for key, names in PLATINUM_RULES for n in names if _matches(z['name'][4:], n)), None)
        if hit is None:
            unassigned.append(z['name'])
            continue
        used.add(hit)
        out.setdefault(hit[0], []).append(z['name'])
    assert not unassigned, unassigned
    dead = [(k, n) for k, names in PLATINUM_RULES for n in names if (k, n) not in used]
    assert not dead, f'rule names that match no installed zone: {dead}'
    import platinum_events                  # the later steps as the events check sorts them
    later = {z for k in ('step7', 'step8') for z in out[k]}
    assert later == {z['name'] for i, z in enumerate(zones) if i in inst and platinum_events.later(z["name"])}, \
        'steps 7 and 8 differ from platinum_events.LATER'
    order = [str(n) for n in range(1, 13)] + ['90', 'skip']
    data = {'_doc': "Platinum's story chapters (b2tools/story_chapters.py, PEARL_VERSION=platinum, writes this; "
                    "notes/PLATINUM_CHAPTERS.md is the brief for each). pearl_story.py reads every chapter from here in a "
                    "Platinum build. _later: the zones of steps 7 (the Distortion World) and 8 (the Battle Frontier), in no chapter.",
            '_titles': PLATINUM_TITLES}
    data.update({k: out[k] for k in order})
    data['_later'] = {'step7': out['step7'], 'step8': out['step8']}
    path = version.data_out('story_chapters.json')
    json.dump(data, open(path, 'w'), indent=1)
    print(f'{os.path.relpath(path, ROOT)}: ' + ', '.join(f'{k} {len(data[k])}' for k in order)
          + f'; step 7 {len(out["step7"])}, step 8 {len(out["step8"])}; {len(inst)} installed zones')


def main():
    if version.PLATINUM:
        return platinum_main()
    import pearl_story
    zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
    world = json.load(open(version.data_path('sinnoh_world.json')))
    inst = {int(k) for k in world['zones']} | {int(k) for k in world['rooms']['zones']}
    done = {n for c in (1, 2, 90) for n in pearl_story.CHAPTERS[c]}
    out, unassigned = {}, []
    for i, z in enumerate(zones):
        if i not in inst or z['name'] in done:
            continue
        ch = chapter_of(z['name'])
        if ch is None:
            unassigned.append(z['name'])
        else:
            out.setdefault(str(ch), []).append(z['name'])
    assert not unassigned, unassigned
    data = {'_doc': 'Zones each story chapter owns (b2tools/story_chapters.py writes this; notes/STORY_CHAPTERS.md '
                    'describes the chapters). pearl_story.py reads chapters 3-9 from here.'}
    data.update({k: out[k] for k in sorted(out, key=lambda k: (k == 'skip', k))})
    json.dump(data, open(os.path.join(ROOT, 'data', 'story_chapters.json'), 'w'), indent=1)
    for k in data:
        if k != '_doc':
            print(k, len(data[k]))


if __name__ == '__main__':
    main()
