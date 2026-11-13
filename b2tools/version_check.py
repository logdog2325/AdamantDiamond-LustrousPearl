"""Offline proof of the two versions (no ROM, no emulator): what a Pearl build makes is what it made at BASE, except what a
feature moves on purpose (FEATURE_MOVED, and new files), and a Diamond build differs from Pearl only where notes/DIAMOND.md says.

    python3 b2tools/version_check.py [--base COMMIT]     default base: BASE (BASE below)
    PEARL_VERSION=diamond python3 b2tools/version_check.py digests [--root DIR]     one tree's digests, as JSON

Three runs of `digests` (each a process of its own, version.py reads PEARL_VERSION once): this tree as Pearl, this tree as
Diamond, the base commit as Pearl (`git archive` into work/version_check/, with this tree's roms, external, tools and work).
Each digest is what a patch or generator produces, called the way the build calls it, without writing into a build:

    wild tables (all 183), the wild blob (honey, swarms), Underground lists and grotto files, Ramanas's rooms, script and text,
    Pal Park's text, the title's art, code edits and camera, the ROM's name and icon, the credits, the Pokédex bank, every field
    script assembled and every text file, the Spear Pillar chunks as converted, the legendaries' sprites, held items, the code
    edits for Met game; since 1.0.1 also the system text's overrides (data/text_overrides and the version's folder), the
    Pokédex AREA page's special places, and the map rows of version.py (each by name: version_row:GROUND_STAYS, ...).

The base is the 1.0 release (BASE). An older base (--base c3eb9ea) also allows what moved before 1.0 (BEFORE_1_0) and the
Spear Pillar chunks. Every map chunk's heights and models are checked by heights_check.py and pearl_seams_check.py --holes.

A digest that moves where nothing should stops the check (exit 1), and so does one that fails to move where it should.
"""
import glob, hashlib, json, os, shutil, struct, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

BASE = '5c90f60'        # the 1.0 release's code (main 5c90f60, the README for 1.0). Before 1.0.1: c3eb9ea, main before Secret
#                         Bases and Super Contests (Diamond started from d2bb913: its Spear Pillar fix is in this)
# What moved between c3eb9ea and 1.0 (Secret Bases, Super Contests): in the base now. Allowed only against an older base.
BEFORE_1_0 = {'script:1282_global_contests', 'script:1290_pearl_jublife', 'script:1299_pearl_jublife_tv_1f', 'script:1300_pearl_jublife_tv_2f', 'script:1400_pearl_hearthome_poffin_house', 'script:1401_pearl_hearthome_super_contest_hall_lobby', 'script:1405_pearl_pastoria', 'script:1424_pearl_veilstone_department_store_1f', 'script:1435_pearl_veilstone_massage_girl_house', 'script:1494_pearl_eterna_forest_exterior', 'script:1517_pearl_amity_square', 'script:1614_pearl_route_206_cycling_road_gatehouse', 'script:1654_pearl_route_221_pal_park_entrance', 'text:0413_contests', 'text:0684_pearl_jublife_tv_2f', 'text:0777_pearl_hearthome_poffin_house', 'text:0778_pearl_hearthome_super_contest_hall_lobby', 'text:0781_pearl_pastoria', 'text:0798_pearl_veilstone_department_store_1f', 'text:0809_pearl_veilstone_massage_girl_house', 'text:0851_pearl_eterna_forest_exterior', 'text:0874_pearl_amity_square', 'text:0940_pearl_route_206_cycling_road_gatehouse', 'text:0980_pearl_route_221_pal_park_entrance',
              'script:1376_pearl_eterna_underground_man_house', 'script:1377_pearl_hearthome',     # Secret Bases: the zones that
              'script:1427_pearl_veilstone_department_store_4f', 'script:1588_pearl_battle_tower_lobby',   # sell or give goods
              'text:0755_pearl_eterna_underground_man_house', 'text:0801_pearl_veilstone_department_store_4f'}
# What 1.0.1 moves on purpose, against the 1.0 base (work/agents/V101_BRIEF.md): one block per piece.
FEATURE_MOVED = set()
# ---- v101-story (1.0.1's scripts and small commands, work/agents/V101_BRIEF.md "v101-story"): what it moves on purpose
# against the 1.0 base. The zones whose generated scripts take Platinum's gates (version.py block "v101-story"): Barry's
# name (Canalave), the blackboard (Trainers' School), the ghosts (Old Chateau 1F, 2F room 4), the seen mark (Verity Cavern,
# Fullmoon Island, the Celestic elder), the field left open after a stubbed app (Jubilife TV 2F, 3F and gallery, the GTS,
# the Pokétch Co. 1F, Canalave's west house, the Fan Club, both Amity Square gatehouses, the Poffin house, the Contest Hall
# lobby, Snowpoint's and Route 226's trade houses, the League lobby 2F and B1F, Julia, the Battle Tower lobby), the Move
# Deleter, the trades (Oreburgh, Eterna, Snowpoint, Route 226), the fossil restorer (the Museum: its menu's lines), the
# roamers (Verity Cavern, Fullmoon Island), the nature check (Sunyshore east house), the exact money check and the ribbons
# (the Ribbon Syndicate), the party commands (the scarf man, Dr. Footstep, the Sunyshore Market, Julia: her ribbon names),
# Deoxys's forms (Veilstone).
FEATURE_MOVED |= {
    'script:1296_pearl_jublife_poketch_company_1f', 'script:1300_pearl_jublife_tv_2f', 'script:1301_pearl_jublife_tv_3f',
    'script:1303_pearl_jublife_tv_2f_gallery', 'script:1315_pearl_jublife_global_trade_station',
    'script:1316_pearl_jublife_trainer_school', 'script:1321_pearl_canalave', 'script:1331_pearl_canalave_move_deleter_house',
    'script:1334_pearl_canalave_west_house', 'script:1345_pearl_oreburgh_north_house_1f',
    'script:1350_pearl_oreburgh_mining_museum', 'script:1368_pearl_eterna_condominiums_1f',
    'script:1390_pearl_hearthome_pokemon_fan_club', 'script:1391_pearl_hearthome_amity_square_west_gatehouse',
    'script:1392_pearl_hearthome_amity_square_east_gatehouse', 'script:1400_pearl_hearthome_poffin_house',
    'script:1401_pearl_hearthome_super_contest_hall_lobby', 'script:1417_pearl_pastoria_scarf_guy_house',
    'script:1418_pearl_veilstone', 'script:1445_pearl_sunyshore_market', 'script:1446_pearl_sunyshore_julia_house',
    'script:1451_pearl_sunyshore_poketch_developer_house', 'script:1460_pearl_snowpoint_northwest_house',
    'script:1479_pearl_pokemon_league_lobby_2f', 'script:1480_pearl_pokemon_league_lobby_b1f',
    'script:1524_pearl_fullmoon_island_interior', 'script:1564_pearl_old_chateau_1f', 'script:1566_pearl_old_chateau_2f_room_4',
    'script:1577_pearl_verity_cavern', 'script:1588_pearl_battle_tower_lobby', 'script:1636_pearl_route_213_footstep_house',
    'script:1708_pearl_celestic_cynthia_grandparents_house', 'script:1726_pearl_resort_area_ribbon_syndicate_1f',
    'script:1734_pearl_route_226_house',
    'text:0730_pearl_oreburgh_mining_museum', 'text:0817_pearl_sunyshore_julia_house'}
# Hearthome's statues: the Master Rank flags set at the contest's end (the hand-written contest script), the Crystals
# (Hearthome); the Pokétch apps from the deliveryman (every Mart: his chain of lines and pearl_story.inc's gifts); TM64's
# clerk (the Game Corner: her streak check); the Battle Tower's trophies (its lobby)
FEATURE_MOVED |= {
    'script:1282_global_contests', 'script:1377_pearl_hearthome', 'script:1423_pearl_veilstone_game_corner',
    'script:1291_pearl_jublife_pokemart', 'script:1322_pearl_canalave_pokemart', 'script:1336_pearl_oreburgh_pokemart',
    'script:1357_pearl_eterna_pokemart', 'script:1378_pearl_hearthome_pokemart', 'script:1406_pearl_pastoria_pokemart',
    'script:1438_pearl_sunyshore_pokemart', 'script:1455_pearl_snowpoint_pokemart', 'script:1482_pearl_fight_area_pokemart',
    'script:1678_pearl_sandgem_pokemart', 'script:1687_pearl_floaroma_pokemart', 'script:1695_pearl_solaceon_pokemart',
    'script:1714_pearl_survival_area_pokemart',
    'text:0677_pearl_jublife_pokemart', 'text:0706_pearl_canalave_pokemart', 'text:0717_pearl_oreburgh_pokemart',
    'text:0737_pearl_eterna_pokemart', 'text:0757_pearl_hearthome_pokemart', 'text:0782_pearl_pastoria_pokemart',
    'text:0812_pearl_sunyshore_pokemart', 'text:0825_pearl_snowpoint_pokemart', 'text:0841_pearl_fight_area_pokemart',
    'text:1004_pearl_sandgem_pokemart', 'text:1012_pearl_floaroma_pokemart', 'text:1018_pearl_solaceon_pokemart',
    'text:1033_pearl_survival_area_pokemart'}
# Floaroma's Accessory shop (Pearl's berry exchange in a list menu: its script and the lines written in)
FEATURE_MOVED |= {'script:1691_pearl_floaroma_flower_shop', 'text:1014_pearl_floaroma_flower_shop'}
FEATURE_MOVED |= {'script:1414_pearl_pastoria_west_house'}   # the Burmy boy's real check (version.PARTY_QUESTIONS; the lead)
# pl_GetPartyMonSpecies gives 0 for an Egg, as Gen 4's 0x198 (2026-11-08, the lead after the command audit): every script
# that asks for a party Pokémon's species. (1331, 1345, 1368, 1451, 1460, 1303 and 1734 were already moved by v101-story.)
FEATURE_MOVED |= {f'script:{n}' for n in ('1415_pearl_pastoria_move_tutor_house', '1435_pearl_veilstone_massage_girl_house',
                  '1517_pearl_amity_square', '1625_pearl_route_210_grandma_wilma_house',
                  '1658_pearl_route_222_pokemon_size_contest_house', '1667_pearl_route_228_north_house',
                  '1682_pearl_sandgem_rowans_lab', '1699_pearl_solaceon_daycare', '1703_pearl_solaceon_seal_house')}
# Pearl's list menus close with B where Pearl's do (h_menu_init passes canExitWithB as Black 2's cancelable; 2026-11-08,
# found by v101-test): every script with such a menu that nothing else moved
FEATURE_MOVED |= {f'script:{n}' for n in (
    '1290_pearl_jublife', '1298_pearl_jublife_poketch_company_3f', '1306_pearl_jublife_tv_elevator',
    '1329_pearl_canalave_library_3f', '1338_pearl_oreburgh_pokecenter_1f',
    '1376_pearl_eterna_underground_man_house', '1405_pearl_pastoria', '1425_pearl_veilstone_department_store_2f',
    '1426_pearl_veilstone_department_store_3f', '1427_pearl_veilstone_department_store_4f',
    '1428_pearl_veilstone_department_store_5f', '1429_pearl_veilstone_department_store_elevator',
    '1431_pearl_veilstone_prize_exchange', '1481_pearl_fight_area', '1486_pearl_fight_area_battle_park_gatehouse',
    '1494_pearl_eterna_forest_exterior', '1496_pearl_fuego_ironworks_exterior', '1504_pearl_great_marsh_area_1',
    '1505_pearl_great_marsh_area_2', '1506_pearl_great_marsh_area_3', '1507_pearl_great_marsh_area_4',
    '1508_pearl_great_marsh_area_5', '1509_pearl_great_marsh_area_6',
    '1570_pearl_veilstone_galactic_headquarters_4f_1', '1587_pearl_battle_park_exchange_service_corner',
    '1610_pearl_route_205_south', '1612_pearl_route_205_north', '1613_pearl_route_206', '1616_pearl_route_207',
    '1617_pearl_route_208', '1618_pearl_route_208_berry_master_house', '1619_pearl_route_209',
    '1622_pearl_route_210_south', '1624_pearl_route_210_north', '1627_pearl_route_211_east',
    '1628_pearl_route_212_north', '1632_pearl_route_212_south', '1633_pearl_route_212_shard_weather_tm_house',
    '1634_pearl_route_213', '1641_pearl_route_214', '1643_pearl_route_215', '1649_pearl_route_218',
    '1653_pearl_route_221', '1654_pearl_route_221_pal_park_entrance', '1656_pearl_route_222',
    '1660_pearl_route_224', '1661_pearl_route_225', '1665_pearl_route_228', '1669_pearl_route_229',
    '1686_pearl_floaroma', '1694_pearl_solaceon', '1701_pearl_solaceon_news_press', '1721_pearl_resort_area',
    '1728_pearl_resort_area_ribbon_syndicate_elevator', '1733_pearl_route_226', '1735_pearl_route_230')}
FEATURE_MOVED |= {'text:0797_pearl_veilstone_game_corner'}   # the coin clerk's closed-slots line (h_can_add_coins; the lead)
# A money window's layout (pearl_story money_layout; v101-test, 2026-11-08): in a script that shows the money window,
# talk balloons at the bottom and menus under the window (the Game Corner's, the Dept. Store 5F's and the Berry Master's
# menus lay under a balloon or over the money); and a menu column after a buffered name pads for an empty name, so the
# window fits the shortest names (the BP Exchange's TM list cut its prices off)
FEATURE_MOVED |= {'script:1519_pearl_floaroma_meadow', 'script:1623_pearl_route_210_cafe',
                  'text:0805_pearl_veilstone_prize_exchange', 'text:0919_pearl_battle_park_exchange_service_corner'}
# ---- end v101-story
# ---- v101-world (1.0.1's maps and data)
FEATURE_MOVED |= {'version_row:GROUND_AT_BDHC',     # map heights at the BDHC (heights_check: Pearl 3,019 faults -> 0)
                  'version_row:GROUND_STAYS',       # the ground fix and plat-caves' layer rules (holes 1,147.2 -> 272.2)
                  'land:354',                       # (Spear Pillar's third chunk: its model under GROUND_STAYS; heights the same)
                  'dex_area_special'}               # the AREA page's honey trees, Great Marsh and Feebas (AREA_SPECIAL)
# ---- end v101-world
# ---- v101-seams (1.0.1: Pearl's alternate forms' Pokédex entries; the seams seen from the side, all three versions)
FEATURE_MOVED |= {'text_overrides'}                 # Pearl's shared pokedex.json: Rotom's, Giratina's, Shaymin's and
#                                                     Arceus's forms take Pearl's species entry (platinum_dex_check --text)
FEATURE_MOVED |= {'version_row:SEAM_GUARDS'}        # pearl_model_fix's three seam guards (pearl_seams_check --holes
#                                                     --views; the map chunks are checked by that, not here)
# ---- end v101-seams
# ---- plat-records (2026-11-08): the Battle Tower lobby's results machines (Single and Double, Multi, Wi-Fi) show the
# player's own results as a message in the records app's words (pearl_story h_tower_records, pearl_story.inc
# pl_TowerResults), not Black 2's list of other players' records; the leaders machine's 0x1E4 (h_tower_has_leaders) comes
# with the lobby's regeneration. Its script and its text (eleven lines added; the common scripts' lines after them move)
FEATURE_MOVED |= {'script:1588_pearl_battle_tower_lobby', 'text:0920_pearl_battle_tower_lobby'}
# ---- end plat-records
# ---- newgame-flash (2026-11-08): no look at Twinleaf between Rowan's fade and the bedroom (all three versions). The
# new game's script 30 (src/field_scripts/pearl/newgame.inc, in Twinleaf's file) no longer fades out, as pearl_intro's
# ov035 edit no longer fades zone 427 in (code edits are not digested here)
FEATURE_MOVED |= {'script:1670_pearl_twinleaf'}
# ---- end newgame-flash
# ---- slatefix (2026-11-09, 1.0.1): the Pal Park gate's slate clerk by version (b2tools/ramanas.py extra_code). Pearl's
# assembled gate script is byte-for-byte what it was; its text gains Diamond's two slate names after its last line
FEATURE_MOVED |= {'text:0980_pearl_route_221_pal_park_entrance'}
# ---- end slatefix (postdex below supersedes its clerk: all 11 rooms, the rules by version)
# ---- postdex (2026-11-09): the National Pokédex in the post-game (notes/POSTGAME_DEX.md). The Hideaways' lists (the other
# column at stage 6), Pal Park's 11 rooms (their script, text and the gate's clerk, whose rooms' rules split by version in
# the one shared file), the Underground's script (the other fossil in the daily balls), Spear Pillar's script (the other
# legendary's entries), the deliveryman's chain in every Mart (the event Pokémon: their scripts, already listed above by
# v101-story, and texts)
FEATURE_MOVED |= {'ug_lists', 'ramanas_rooms', 'ramanas_generated', 'script:1900_underground', 'script:1901_ramanas_rooms',
                  'text:1301_ramanas_rooms', 'script:1502_pearl_mount_coronet_spear_pillar',
                  'script:1654_pearl_route_221_pal_park_entrance', 'text:0980_pearl_route_221_pal_park_entrance',
                  'legendaries'}    # (Pearl repaints Dialga's sheet too: the other version's legendary at Spear Pillar)
# ---- end postdex
# ---- tower-fix (2026-11-12, the user: "fix them"): plat-fix2's three rows for Pearl and Diamond too (version.py block
# plat-fix2): the wireless link's starts answer cancel (the Poffin house, the Contest Hall lobby, the League lobby 2F, the
# Battle Tower lobby), the Tower opponent's line takes one A (the Multi and Wi-Fi arenas), a reset without saving ends the
# Tower streak at 0 (the lobby's tower function 14: pl_TowerDisqualify).
FEATURE_MOVED |= {'script:1400_pearl_hearthome_poffin_house', 'script:1401_pearl_hearthome_super_contest_hall_lobby',
                  'script:1479_pearl_pokemon_league_lobby_2f', 'script:1588_pearl_battle_tower_lobby',
                  'script:1592_pearl_battle_tower_arena_multi', 'script:1593_pearl_battle_tower_arena_wifi'}
# ---- end tower-fix
HERE = os.path.dirname(os.path.abspath(__file__))
ME = os.path.abspath(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
SPEAR_PILLAR = ('land:352', 'land:353', 'land:354', 'land:355', 'land_heights')
DIAMOND_SCRIPTS = ('1356_pearl_eterna', '1502_pearl_mount_coronet_spear_pillar', '1677_pearl_sandgem',
                   '1682_pearl_sandgem_rowans_lab', '1708_pearl_celestic_cynthia_grandparents_house', '1901_ramanas_rooms',
                   '1654_pearl_route_221_pal_park_entrance')    # (slatefix, 1.0.1: Diamond's slate clerk sells its rooms' slates)


def sha(b):
    if isinstance(b, str):
        b = b.encode('utf-8')
    return hashlib.sha1(b).hexdigest()[:16]


def jsha(o):
    return sha(json.dumps(o, sort_keys=True, default=str))


def digests(root):
    """{name: digest} of the tree at `root`, for this process's PEARL_VERSION. Works on an older tree too (no version_check
    or new function there is asked for: what is missing counts as unchanged code, by name)."""
    b2 = os.path.join(root, 'b2tools')
    sys.path[:0] = [b2, os.path.join(b2, 'patches')]
    os.chdir(b2)
    import version
    assert os.path.abspath(version.__file__).startswith(os.path.abspath(root)), version.__file__
    out = {}

    # wild tables, as sinnoh_encounters.apply makes them
    import sinnoh_encounters as enc
    tables = []
    for n in range(enc.PEARL_FILES):
        tables.append(b''.join(enc.convert(enc.pearl_file(n), p, k == enc.ROD_TABLE)[0] for k, p in enumerate(enc.TIME_TABLES)))
        out[f'wild_table:{n:03d}'] = sha(tables[-1])
    import wild
    out['wild_blob'] = sha(wild.table()[0])
    out['honey_members'] = jsha(wild.HONEY_MEMBERS)

    # Underground
    import ug_data, underground
    data = ug_data.data()
    out['ug_lists'] = jsha(ug_data.encounter_lists())
    for i, h in enumerate(ug_data.hideaways()):
        if h.get('grotto'):
            out[f'grotto:{h["key"]}'] = sha(underground.grotto_file(h, i, data))

    # Ramanas Park
    import ramanas
    d = ramanas.load()
    ver = ramanas.version(d)
    out['ramanas_rooms'] = jsha(ramanas.rooms(ver))
    src, text, problems = ramanas.write_rooms(ver)
    out['ramanas_generated'] = jsha([src, text])
    out['ramanas_problems'] = jsha(problems)

    # Pal Park, title, the ROM's face, credits, Pokédex
    import pal_park
    out['pal_park_text'] = sha(pal_park.text_source())
    import pearl_title, rom_identity, title_art
    art = os.path.join(title_art.DATA, pearl_title.VERSION_TITLE['art'])
    out['title_art'] = sha(open(os.path.join(art, 'logo.png'), 'rb').read() + open(os.path.join(art, 'strip.png'), 'rb').read())
    out['title_model'] = jsha([pearl_title.PEARL_MODEL, pearl_title.PEARL_ANIM, pearl_title.VERSION_TITLE['species']])
    out['title_code'] = jsha(pearl_title.CODE)
    out['rom_header'] = version.HEADER_TITLE
    out['banner_text'] = sha(rom_identity.banner_yaml())
    out['banner_icon'] = sha(b''.join(rom_identity.dump_icon()))
    import pearl_credits
    out['credits_game'] = jsha([pearl_credits.GAME, pearl_credits.pearl_lines()[pearl_credits.GAME]])
    out['credits_text'] = jsha(pearl_credits.overrides())
    import sinnoh_pokedex
    out['dex_bank'] = str(sinnoh_pokedex.ENTRY_BANK)
    # (1.0.1) the system text's overrides as sinnoh_names applies them: the shared files, and for Diamond and Platinum
    # their own folder over them (Diamond's Pokédex entries); the AREA page's special places (sinnoh_pokedex.AREA_SPECIAL:
    # none at the 1.0 base, which has no such row)
    tov = os.path.join(root, 'data', 'text_overrides')
    folders = [tov] + ([os.path.join(tov, version.VERSION)] if version.VERSION != 'pearl' else [])
    out['text_overrides'] = jsha([(os.path.relpath(p, tov), sha(open(p, 'rb').read())) for d in folders
                                  for p in sorted(glob.glob(os.path.join(d, '*.json')))])
    if getattr(sinnoh_pokedex, 'AREA_SPECIAL', False):
        tm_ = sinnoh_pokedex._tm()
        locs = tm_.locations(); locs = locs + [tm_.dummy_record(locs)] * (sinnoh_pokedex.NREC - len(locs))
        out['dex_area_special'] = jsha(sinnoh_pokedex.special_bits(tm_, locs))
    else:
        out['dex_area_special'] = jsha(None)
    import town_map                     # (reads the version's dump at fixed addresses: the same in both, or it asserts)
    for f in ('fly_table', 'spawn_table', 'area_places', 'blocks'):
        out['town_map:' + f] = sha(repr(getattr(town_map, f)()))

    # scripts and text, by the build's own sources and assembler
    import scripts
    music = os.path.join(root, 'work', 'world', 'music.json')
    if os.path.exists(music) and 'PEARL_MUSIC_EVENTS' not in os.environ:
        os.environ['PEARL_MUSIC_EVENTS'] = json.dumps(json.load(open(music)).get('events', {}))
    src_dir = os.path.join(root, 'src', 'field_scripts')
    txt_dir = os.path.join(root, 'src', 'text', 'script')
    both = getattr(version, 'sources', None)
    paths = both(src_dir, '.s') if both else sorted(glob.glob(os.path.join(src_dir, '*.s')))
    with ThreadPoolExecutor(6) as ex:
        for p, b in zip(paths, ex.map(scripts.assemble, paths)):
            out['script:' + os.path.basename(p)[:-2]] = sha(b)
    for p in (both(txt_dir, '.txt') if both else sorted(glob.glob(os.path.join(txt_dir, '*.txt')))):
        out['text:' + os.path.basename(p)[:-4]] = sha(open(p, 'rb').read())

    # Spear Pillar, as sinnoh_rooms converts it
    import pearl_chunk
    slopes, offsets = pearl_chunk.tables()
    m = json.load(open(os.path.join(root, 'work', 'pearl', 'matrices', '022.json')))
    heights = {}
    for z in range(2):
        for x in range(2):
            c = m['maps'][z][x]
            chunk, rep = pearl_chunk.convert(c, slopes, offsets, pearl_chunk.neighbours(m, x, z))
            out[f'land:{c}'] = sha(chunk)
            heights[c] = sorted((k, v) for k, v in rep['heights'].items())
    out['land_heights'] = jsha(heights)
    # (1.0.1) the map rows of version.py, as this tree has them (a row missing at the base: its off value). The maps they
    # switch are checked chunk by chunk by heights_check.py and pearl_seams_check.py --holes, not here (too slow).
    for row, off in (('GROUND_AT_BDHC', False), ('GROUND_STAYS', False), ('SELF_PAIRS_STAY', False), ('NODE_SHIFT', False),
                     ('EVERY_PALETTE', False), ('SNOW_PATCHES_WINTER_ONLY', ()), ('SNOW_DUSTED', {}), ('SEAM_GUARDS', False)):
        out['version_row:' + row] = jsha(getattr(version, row, off))
    land_id = getattr(version, 'land_id', lambda c: c)
    world = json.load(open(os.path.join(root, 'data', 'sinnoh_world.json')))
    out['world_table'] = sha(json.dumps(world, sort_keys=True))
    out['other_chunks_own_file'] = str(all(land_id(int(c)) == int(c) for c in list(world['chunks']) + list(world['rooms']['chunks'])
                                           if int(c) not in (352, 353, 354, 355)))

    # the legendaries' sprites, the one list pearl_npc_sprites goes through
    import pearl_npc_sprites as ns
    only = getattr(ns, 'POKEMON_ONLY_IN', {})
    shown = lambda w: version.VERSION in (only[w] if isinstance(only.get(w), tuple) else (only.get(w, version.VERSION),))
    out['legendaries'] = jsha([p for p in ns.POKEMON if shown(p[0])])     # (postdex: a tuple of versions, or one)
    sm = json.load(open(os.path.join(root, 'data', 'pearl_sprite_map.json')))
    for v in sm.values():
        if isinstance(v, dict):
            v.pop('note', None)
    out['sprite_map'] = jsha(sm)

    # held items and Met game, on copies of what the build starts from
    files = os.path.join(root, 'external', 'pokebw2', 'build', 'b2_us', 'files')
    code = os.path.join(root, 'external', 'pokebw2', 'build', 'b2_us', 'build')
    import narcio, b2files
    with tempfile.TemporaryDirectory(dir=os.environ.get('VERSION_CHECK_TMP')) as t:
        rel = os.path.relpath(b2files.arc_path(files, 16), files)
        os.makedirs(os.path.dirname(os.path.join(t, rel)))
        shutil.copyfile(b2files.arc_path(files, 16), os.path.join(t, rel))
        if hasattr(enc, 'held_items'):
            enc.held_items(t)
        pers = narcio.load(t, 16)
        out['held_items'] = jsha([list(struct.unpack_from('<3H', pers[s], 0x0C)) for s in (125, 126, 239, 240, 466, 467)])
        for f in ('arm9.bin', 'arm9_ov012.bin'):
            shutil.copyfile(os.path.join(code, f), os.path.join(t, f))
        if hasattr(rom_identity, 'stamp_met_game'):
            shutil.copyfile(os.path.join(os.path.dirname(code), 'arm9.o.xMAP'), os.path.join(t, 'arm9.o.xMAP'))
            rom_identity.stamp_met_game(t)
        for f in ('arm9.bin', 'arm9_ov012.bin'):
            out[f'met_code:{f}'] = sha(open(os.path.join(t, f), 'rb').read())
    return out


def run(root, ver):
    env = dict(os.environ, PEARL_VERSION=ver)
    if root != ROOT:
        del env['PEARL_VERSION']       # (the base's Ramanas tool read the variable itself: unset, as a Pearl build runs)
    r = subprocess.run([sys.executable, ME, 'digests', '--root', root], env=env, capture_output=True, text=True, timeout=500)
    if r.returncode:
        raise SystemExit(f'{ver} at {root}:\n{r.stderr[-3000:]}')
    return json.loads(r.stdout.splitlines()[-1])


def base_tree(commit, where):
    os.makedirs(where)
    a = subprocess.run(['git', 'archive', commit, 'b2tools', 'data', 'src'], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', where], input=a, check=True)
    for d in ('roms', 'external', 'tools', 'art_sources', 'work'):
        os.symlink(os.path.realpath(os.path.join(ROOT, d)) if d != 'work' else os.path.join(ROOT, d), os.path.join(where, d))


def diff(a, b, added=()):
    assert set(a) | set(added) == set(b) and set(a) <= set(b), sorted(set(a) ^ set(b))[:10]
    return sorted(k for k in a if a[k] != b[k])


def facts(p, d):
    """What must hold of the Diamond side, read back through the real functions."""
    code = r"""
import json, os, struct, sys
sys.path[:0] = ['.', 'patches']
import version, wild, ug_data, ramanas, pal_park, sinnoh_pokedex, pearl_title
blob = wild.table()[0]
at = 6 + 2 * 21
honey = struct.unpack_from('<6H', blob, at)
rooms = {r['id']: (r['zone'], r['slate']['item'] if isinstance(r['slate'], dict) else r['slate']) for r in ramanas.rooms()}
print(json.dumps(dict(version=version.VERSION, honey2=honey[1], fossil=ug_data.grotto_items()['a'][1][0], rooms=rooms,
    pal=[l for l in pal_park.text_source().split('\n') if l.startswith(('PearlMigrate_19', 'PearlMigrate_30', 'PearlMigrate_35'))],
    bank=sinnoh_pokedex.ENTRY_BANK, game=version.GAME_VERSION, met=version.MET_GAME, model=pearl_title.PEARL_MODEL,
    rom=version.ROM_NAME, stem=version.RELEASE_STEM, build=os.path.basename(version.build_dir('/x/rom')))))
"""
    return {v: json.loads(subprocess.run([sys.executable, '-c', code], cwd=HERE, env=dict(os.environ, PEARL_VERSION=v),
                                         capture_output=True, text=True, check=True, timeout=200).stdout.splitlines()[-1])
            for v in ('pearl', 'diamond')}


def main():
    args = sys.argv[1:]
    if args[:1] == ['digests']:
        root = args[args.index('--root') + 1] if '--root' in args else ROOT
        print(json.dumps(digests(root)))
        return 0
    commit = args[args.index('--base') + 1] if '--base' in args else BASE
    t0 = time.time()
    scratch = os.path.join(ROOT, 'work', 'version_check')
    os.makedirs(scratch, exist_ok=True)
    os.environ['VERSION_CHECK_TMP'] = scratch
    base = os.path.join(scratch, f'base_{commit}_{os.getpid()}')
    base_tree(commit, base)
    with ThreadPoolExecutor(3) as ex:
        fb, fp, fd = ex.submit(run, base, 'pearl'), ex.submit(run, ROOT, 'pearl'), ex.submit(run, ROOT, 'diamond')
        b, p, d = fb.result(), fp.result(), fd.result()
    shutil.move(base, os.path.expanduser(f'~/.Trash/version_check_base_{commit}_{os.getpid()}'))
    fail = []
    pearl_moved = diff(b, p, added=('script:1281_secret_bases', 'text:1310_secret_bases', 'script:1282_global_contests', 'text:0413_contests'))
    print(f'{len(p)} digests. Pearl against {commit}: {len(pearl_moved)} moved: {pearl_moved}')
    allowed = FEATURE_MOVED if commit == BASE else FEATURE_MOVED | BEFORE_1_0 | set(SPEAR_PILLAR)   # (an older base)
    for k in pearl_moved:
        if k not in allowed:
            fail.append(f'Pearl moved: {k}')
    if commit == 'd2bb913' and not set(SPEAR_PILLAR) <= set(pearl_moved):
        fail.append(f'the Spear Pillar fix did not move all of {SPEAR_PILLAR}')
    moved = diff(p, d)
    wild_files = [k for k in moved if k.startswith('wild_table:')]
    print(f'Diamond against Pearl: {len(wild_files)} wild tables, and: {[k for k in moved if k not in wild_files]}')
    want = {'wild_blob', 'honey_members', 'ug_lists', 'ramanas_rooms', 'ramanas_generated', 'pal_park_text', 'title_art',
            'title_model', 'title_code', 'rom_header', 'banner_text', 'banner_icon', 'credits_game', 'dex_bank', 'held_items',
            'met_code:arm9.bin', 'met_code:arm9_ov012.bin',
            'text_overrides', 'dex_area_special'} | set(SPEAR_PILLAR) | \
           {f'script:{s}' for s in DIAMOND_SCRIPTS if s != '1901_ramanas_rooms'} | \
           {'script:1900_underground', 'script:1654_pearl_route_221_pal_park_entrance'}
    # (postdex) both versions have all 11 rooms: their room script and text are the same (the comment names the version);
    # the gate's clerk and the Underground's fossil balls pick by PEARLB2_GAME_VERSION in Pearl's shared files
    extra = {k for k in moved if k not in want and not k.startswith(('wild_table:', 'grotto:'))}
    fail += [f'Diamond moved, nothing says it should: {k}' for k in sorted(extra)]
    fail += [f'Diamond did not move: {k}' for k in sorted(want - set(moved))]
    # (24 files differ in the dumps, 7 of them only in Poké Radar and dual-slot species, which no build installs: 9, 138, 140,
    # 146, 148, 157, 164; notes/ENCOUNTERS.md)
    if len(wild_files) != 17:
        fail.append(f'{len(wild_files)} installed wild tables differ, expected 17 of the dumps\' 24 (notes/DIAMOND.md 1.2)')
    f = facts(p, d)
    print(json.dumps(f, indent=1, ensure_ascii=False))
    pv, dv = f['pearl'], f['diamond']
    checks = [(pv['honey2'], 268), (dv['honey2'], 266), (pv['fossil'], 'ARMOR_FOSSIL'), (dv['fossil'], 'SKULL_FOSSIL'),
              (pv['bank'], 616), (dv['bank'], 615), (pv['game'], 11), (dv['game'], 10), (pv['met'], 11), (dv['met'], 10),
              (dv['rooms'].get('johto'), [661, 131]), (dv['rooms'].get('rainbow'), [662, 132]), (len(dv['rooms']), 11),
              (len(pv['rooms']), 11), ('kanto' in pv['rooms'], True), ('squall' in dv['rooms'], True),   # (postdex: all 11)
              ('johto' in pv['rooms'], True), (dv['model'], 6),
              (dv['rom'], 'diamond.nds'), (pv['rom'], 'pearl.nds'), (dv['stem'], 'Pokemon_Adamant_Diamond'),
              (dv['build'], 'rom_diamond'), (pv['build'], 'rom')]
    fail += [f'expected {w!r}, got {g!r}' for g, w in checks if g != w]
    fail += [f'Diamond\'s Pal Park line names Pearl: {l}' for l in dv['pal'] if 'Pearl' in l.split(' = ', 1)[1]]
    print(f'{time.time() - t0:.0f} s')
    print('\n'.join(fail) or 'version_check: ok')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
