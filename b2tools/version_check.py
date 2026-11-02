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
    edits for Met game.

A digest that moves where nothing should stops the check (exit 1), and so does one that fails to move where it should.
"""
import glob, hashlib, json, os, shutil, struct, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

BASE = 'c3eb9ea'        # main before Secret Bases and Super Contests (Diamond started from d2bb913: its Spear Pillar fix is in this)
FEATURE_MOVED = {'script:1282_global_contests', 'script:1290_pearl_jublife', 'script:1299_pearl_jublife_tv_1f', 'script:1300_pearl_jublife_tv_2f', 'script:1400_pearl_hearthome_poffin_house', 'script:1401_pearl_hearthome_super_contest_hall_lobby', 'script:1405_pearl_pastoria', 'script:1424_pearl_veilstone_department_store_1f', 'script:1435_pearl_veilstone_massage_girl_house', 'script:1494_pearl_eterna_forest_exterior', 'script:1517_pearl_amity_square', 'script:1614_pearl_route_206_cycling_road_gatehouse', 'script:1654_pearl_route_221_pal_park_entrance', 'text:0413_contests', 'text:0684_pearl_jublife_tv_2f', 'text:0777_pearl_hearthome_poffin_house', 'text:0778_pearl_hearthome_super_contest_hall_lobby', 'text:0781_pearl_pastoria', 'text:0798_pearl_veilstone_department_store_1f', 'text:0809_pearl_veilstone_massage_girl_house', 'text:0851_pearl_eterna_forest_exterior', 'text:0874_pearl_amity_square', 'text:0940_pearl_route_206_cycling_road_gatehouse', 'text:0980_pearl_route_221_pal_park_entrance',
                 'script:1376_pearl_eterna_underground_man_house', 'script:1377_pearl_hearthome',     # Secret Bases: the zones that
                 'script:1427_pearl_veilstone_department_store_4f', 'script:1588_pearl_battle_tower_lobby',   # sell or give goods
                 'text:0755_pearl_eterna_underground_man_house', 'text:0801_pearl_veilstone_department_store_4f'}
HERE = os.path.dirname(os.path.abspath(__file__))
ME = os.path.abspath(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
SPEAR_PILLAR = ('land:352', 'land:353', 'land:354', 'land:355', 'land_heights')
DIAMOND_SCRIPTS = ('1356_pearl_eterna', '1502_pearl_mount_coronet_spear_pillar', '1677_pearl_sandgem',
                   '1682_pearl_sandgem_rowans_lab', '1708_pearl_celestic_cynthia_grandparents_house', '1901_ramanas_rooms')


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
    land_id = getattr(version, 'land_id', lambda c: c)
    world = json.load(open(os.path.join(root, 'data', 'sinnoh_world.json')))
    out['world_table'] = sha(json.dumps(world, sort_keys=True))
    out['other_chunks_own_file'] = str(all(land_id(int(c)) == int(c) for c in list(world['chunks']) + list(world['rooms']['chunks'])
                                           if int(c) not in (352, 353, 354, 355)))

    # the legendaries' sprites, the one list pearl_npc_sprites goes through
    import pearl_npc_sprites as ns
    only = getattr(ns, 'POKEMON_ONLY_IN', {})
    out['legendaries'] = jsha([p for p in ns.POKEMON if only.get(p[0], version.VERSION) == version.VERSION])
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
    for k in pearl_moved:
        if k not in SPEAR_PILLAR and k not in FEATURE_MOVED:
            fail.append(f'Pearl moved: {k}')
    if commit == 'd2bb913' and not set(SPEAR_PILLAR) <= set(pearl_moved):
        fail.append(f'the Spear Pillar fix did not move all of {SPEAR_PILLAR}')
    moved = diff(p, d)
    wild_files = [k for k in moved if k.startswith('wild_table:')]
    print(f'Diamond against Pearl: {len(wild_files)} wild tables, and: {[k for k in moved if k not in wild_files]}')
    want = {'wild_blob', 'honey_members', 'ug_lists', 'ramanas_rooms', 'ramanas_generated', 'pal_park_text', 'title_art',
            'title_model', 'title_code', 'rom_header', 'banner_text', 'banner_icon', 'credits_game', 'dex_bank', 'legendaries', 'held_items',
            'met_code:arm9.bin', 'met_code:arm9_ov012.bin', 'text:1301_ramanas_rooms'} | set(SPEAR_PILLAR) | \
           {f'script:{s}' for s in DIAMOND_SCRIPTS}
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
              (dv['rooms'].get('johto'), [661, 131]), (dv['rooms'].get('rainbow'), [662, 132]), (len(dv['rooms']), 9),
              (len(pv['rooms']), 9), ('kanto' in pv['rooms'], True), ('squall' in dv['rooms'], False), (dv['model'], 6),
              (dv['rom'], 'diamond.nds'), (pv['rom'], 'pearl.nds'), (dv['stem'], 'Pokemon_Adamant_Diamond'),
              (dv['build'], 'rom_diamond'), (pv['build'], 'rom')]
    fail += [f'expected {w!r}, got {g!r}' for g, w in checks if g != w]
    fail += [f'Diamond\'s Pal Park line names Pearl: {l}' for l in dv['pal'] if 'Pearl' in l.split(' = ', 1)[1]]
    print(f'{time.time() - t0:.0f} s')
    print('\n'.join(fail) or 'version_check: ok')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
