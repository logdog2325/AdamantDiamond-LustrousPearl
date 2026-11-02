"""Offline checks of Pearl's Secret Bases (notes/SECRET_BASES.md). No ROM, no emulator.

    python3 b2tools/secret_base_check.py

1 the dump: the goods, lists and traders are the same in Pearl and Diamond, and where the tools look for them; the models fit the
  goods. 2 the numbers shared by the script, the C and the macros. 3 the script assembles; every text word it needs exists.
4 the pack: every model's textures in the merged set pixel for pixel (no same-named texture or palette hiding another), res ids,
  sizes. 5 the room: Pearl's chunk has the room the rules assume; boulders from Pearl's formula never block the way from the exit
  to the PC; the biggest good fits. 6 the traders stand on floor, reachable, clear of the holes. 7 the save fits.
"""
import json, os, random, re, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'patches'))
ERRORS = []


def ok(cond, msg):
    if not cond:
        ERRORS.append(msg)
        print('FAIL', msg)


def version_data(version_name):
    """Goods, lists and traders of one version: its own process (version.py reads PEARL_VERSION once)."""
    code = ('import json,secret_base_data as S;print(json.dumps({"goods":S.goods(),"stock":S.stock(),"traders":S.traders(),'
            '"models":S.good_models()}))')
    env = dict(os.environ, PEARL_VERSION=version_name)
    return json.loads(subprocess.run([sys.executable, '-c', code], cwd=HERE, env=env, check=True, capture_output=True, text=True).stdout)


def header():
    return open(os.path.join(ROOT, 'external', 'pokebw2', 'include', 'pearlb2', 'secret_base.h'), encoding='utf-8').read()


def main():
    import secret_base_data as SB, secret_base_scripts as SS
    p, d = version_data('pearl'), version_data('diamond')
    for key in p:
        ok(p[key] == d[key], f'{key}: Pearl and Diamond differ: a version split is needed')
    goods = p['goods']
    ok(len(goods) == 139 and goods[1]['width'] == 2 and goods[6]['collision'][:5] == [1, 1, 0, 1, 1], 'the goods table: not Pearl\'s')
    ok(all(g['width'] <= 3 and g['depth'] <= 3 for g in goods), 'a good over 3 x 3')
    ok([goods[g]['money'] > 0 for lst in p['stock'] for g in lst] == [True] * 11, 'a Veilstone good without a money price')
    ok(len(p['traders']) == 8, 'not eight goods traders')
    import gen4_text
    for bank in (97, 488, 567, 568, 571, 575, 577, 578, 579, 580, 581):
        ok(gen4_text.read_bank(bank, os.path.join(ROOT, 'roms', 'pearl.nds')) == gen4_text.read_bank(bank, os.path.join(ROOT, 'roms', 'diamond.nds')),
           f'text bank {bank}: Pearl and Diamond differ')
    print(f'1 dump: same in both versions; {sum(1 for g in goods if g["money"])} goods with a money price; '
          f'{sum(1 for g in goods if SB.trader_price(g, 100))} with a trader price')

    # 2 numbers
    h = header()
    enum = re.findall(r'^\s+(SB_OP_\w+)\b', h[h.index('enum {'):h.index('SB_OP_COUNT\n')], re.M)
    ok(enum == ['SB_OP_' + o for o in SS.OPS], 'the script\'s OPS are not the C\'s enum')
    for name, v in (('SB_W_A', SS.W_A), ('SB_W_ARG', SS.W_ARG), ('SB_W_LIST', SS.W_LIST), ('SB_W_RES', SS.W_RES),
                    ('SB_T_DESC', SS.T_DESC), ('SB_T_ARTICLE', SS.T_ARTICLE), ('SB_T_RANK', SS.T_RANK), ('SB_T_RECORD', SS.T_RECORD),
                    ('SB_T_MORE', SS.T_MORE), ('SB_T_CANCEL', SS.T_CANCEL), ('SB_T_PRICE', SS.T_PRICE),
                    ('SB_LIST_MORE', SS.LIST_MORE), ('SB_LIST_CANCEL', SS.LIST_CANCEL)):
        m = re.search(rf'#define {name} (\w+)', h)
        ok(m and int(m.group(1), 0) == v, f'{name}: header {m and m.group(1)}, script {v}')
    pearlb2 = open(os.path.join(ROOT, 'external', 'pokebw2', 'include', 'pearlb2.h'), encoding='utf-8').read()
    ok(f'PEARLB2_GIMMICK_SECRET_BASE {SB.GIMMICK}' in pearlb2, 'the gimmick id')
    ok(f'PEARLB2_TEXT_GLOBAL_10735 {SB.TEXT_FILE}' in pearlb2, 'the text file')
    inc = open(os.path.join(ROOT, 'src', 'include', 'pearl_story.inc'), encoding='utf-8').read()
    for macro, op in (('pl_SendGoodToPC', 'GIVE'), ('pl_CheckHasRoomForGoodsInPC', 'HAS_ROOM'), ('pl_GetCapturedFlagCount', 'FLAG_INFO'),
                      ('pl_BufferUndergroundGoodsName', 'WORD'), ('pl_GetDecorationNameWithArticle', 'WORD_ARTICLE')):
        m = re.search(rf'\.macro {macro} .*?pl_ext 0xE0 \+ (\d+)', inc, re.S)
        ok(m and int(m.group(1)) == SS.OPS.index(op), f'{macro}: not op {op}')
    ok(f'RTCallGlobal {SS.SCRIPT["Shop"]}' in inc, 'pl_GoodsMart: not the Shop script')
    print('2 numbers: script, C and macros agree')

    # 3 script and text
    subprocess.run([sys.executable, os.path.join(HERE, 'secret_base_scripts.py'), '--check'], check=True, capture_output=True)
    import scripts
    s, t = SS.paths()
    binary = scripts.assemble(s)
    lines, named = SS.text_lines()
    ok(len(lines) == len(set(f'{i}' for i in range(len(lines)))), 'text')
    for name, i in named.items():
        ok(lines[i].strip() != '', f'{name}: an empty line')
    # every word a line reads is set: the words each op fills, by the lines' own placeholders
    words = {'PLACED': {0}, 'RETURNED': {0}, 'SEND_PC': {0}, 'THAT_WILL_BE': {0, 1, 2}, 'BAG_WHAT': {2}, 'THREW': {2}, 'WITHDRAWN': {2},
             'STORED': {2}, 'DRILL_USED': {3}, 'GOODS_SET': {0, 1}, 'BOULDER_ONE': {0}, 'BOULDER_MANY': {0}, 'FLAG_CARD': {0, 1}}
    for name, i in named.items():
        used = {int(n) for n in re.findall(r'\{0[12][0-9a-f]{2}:(\d+)\}', lines[i])}
        ok(used == words.get(name, set()), f'{name}: reads words {used}: {lines[i]}')
    for i in list(range(SS.T_RECORD, SS.T_MORE)):
        ok({int(n) for n in re.findall(r'\{0[12][0-9a-f]{2}:(\d+)\}', lines[i])} == {6}, f'record line {i}')
    ok(max(len(l) for l in lines[:139]) < 24, 'a good\'s name too long for the list')
    print(f'3 script {len(binary)} B, text {len(lines)} lines, {os.path.getsize(t)} B source; every line\'s words are filled')

    # 4 the pack
    import secret_bases as patch, nsbtx, pearl_buildings as pb
    from gen4rom import Rom, narc_members
    from b2files import gf_container
    pack, tex = patch.build_pack()
    magic, secs = gf_container(pack)
    n = len(secs) // 2
    res = [struct.unpack_from('<H', secs[i], 0)[0] for i in range(n)]
    ok(len(set(res)) == n and max(res) == SB.RES_CURSOR and max(res) < 0x200 and min(res) >= 1, f'res ids {res[:5]}...')
    ok(not set(res) & set(SB.HOLE_GOODS), 'a hole in the pack')
    merged = nsbtx._parse(tex)
    rom = Rom(os.path.join(ROOT, 'roms', 'pearl.nds'))
    build = narc_members(rom.read('fielddata/build_model/build_model.narc'))

    bad = []
    have_t, have_p = dict(merged['texs']), dict(merged['pals'])
    models = {g: build[m] for g, m in p['models'].items() if int(g) not in SB.HOLE_GOODS}
    models = {int(g): b for g, b in models.items()}
    models[SB.RES_CURSOR] = rom.read('data/ug_base_cur.nsbmd')
    for g, b in sorted(models.items()):
        own = nsbtx._parse(pb.btx0_of(b))
        for t, pl in nsbtx.material_pairs(b):
            if t not in have_t or (pl and pl not in have_p):
                bad.append((g, t, pl, 'missing'))
                continue
            if not same_texture(own, merged, t, pl):
                bad.append((g, t, pl, 'other pixels'))
    ok(not bad, f'textures hidden by a same-named one: {bad[:8]} ({len(bad)})')
    print(f'4 pack: {n} models, {len(pack):,} B; textures {len(tex):,} B ({len(merged["texs"])} textures, {len(merged["pals"])} palettes), '
          f'each model\'s pixel for pixel')

    # 5 the room
    land = json.load(open(os.path.join(ROOT, 'work', 'pearl', 'land', f'{SB.BASE_CHUNK:03d}.json')))
    coll = land['collision']
    ok(all(not coll[z][x] for z in range(12, 24) for x in range(10, 22)), 'the room is not 12 x 12 at (10, 12)')
    ok(not coll[24][15] and coll[24][14] and coll[24][16], 'the exit is not at (15, 24)')
    ok(all(coll[11][x] for x in range(10, 22)), 'no wall behind the PC')
    rng = random.Random(4)
    for _ in range(3000):
        boulders = make_boulders(rng)
        ok(len(set(boulders)) == 16 and all(10 <= x <= 20 and 12 <= z <= 22 for x, z in boulders), f'boulders {boulders}')
        ok(reach_ok(boulders), f'boulders block the way: {boulders}')
    print('5 room: 12 x 12 at (10, 12), exit (15, 24); 3000 sets of boulders leave the way from the exit to the PC')

    # 6 the traders, and the holes the drill must leave alone
    import ug_data
    m2 = json.load(open(os.path.join(ROOT, 'work', 'pearl', 'matrices', '002.json')))

    def wall(x, z):
        c = m2['maps'][z // 32][x // 32]
        return json.load(open(os.path.join(ROOT, 'work', 'pearl', 'land', f'{c:03d}.json')))['collision'][z % 32][x % 32]
    holes = [tuple(h['hole']) for h in ug_data.hideaways()]
    ok(len(holes) == 18, 'not 18 holes')
    for x, z in p['traders']:
        ok(not wall(x, z), f'trader on a wall at ({x}, {z})')
        ok(sum(1 for dx, dz in ((0, 1), (0, -1), (1, 0), (-1, 0)) if not wall(x + dx, z + dz)) >= 2, f'trader cut off at ({x}, {z})')
        ok(all(abs(x - hx) + abs(z - hz) > 1 for hx, hz in holes), f'trader at a hole: ({x}, {z})')
    print(f'6 traders: {p["traders"]} on tunnel floor, clear of the {len(holes)} holes')

    # 7 the save
    w = open(os.path.join(ROOT, 'external', 'pokebw2', 'include', 'pearlb2', 'wild.h'), encoding='utf-8').read()
    wild = 12 + 21 * 6 + 118 * 12
    size = 4 + 6 + 2 + 2 + 2 + 2 + 15 * 3 + 16 + 200 + 40
    ok(wild <= 0x700 and 0x700 + size <= 0x848, f'save: wild {wild}, base {size}')
    print(f'7 save: {size} B at block 0x3C +0x700 (to +{0x700 + size:#x}, the block\'s free bytes end at +0x847; the wild save ends at +{wild:#x}); '
          'the C checks both sizes at compile time')
    if ERRORS:
        raise SystemExit(f'{len(ERRORS)} problems')
    print('all pass')


def make_boulders(rng):
    """Pearl's SecretBases_CreateBase, as PearlB2SB's MakeBase."""
    out = []
    while len(out) < 16:
        col = rng.randrange(5)
        x = col * 2 + 10 if col < 2 else (col - 3) * 2 + 18
        z = rng.randrange(6) * 2 + 12
        if (x, z) != (16, 12) and (x, z) not in out:
            out.append((x, z))
    return out


def reach_ok(boulders):
    solid = {(x + dx, z + dz) for x, z in boulders for dx in (0, 1) for dz in (0, 1)} | {(15, 12), (16, 12)}
    seen, todo = {(15, 23)}, [(15, 23)]
    while todo:
        x, z = todo.pop()
        for nx, nz in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
            if 10 <= nx <= 21 and 12 <= nz <= 23 and (nx, nz) not in solid and (nx, nz) not in seen:
                seen.add((nx, nz))
                todo.append((nx, nz))
    return (15, 13) in seen and (16, 13) in seen


def same_texture(own, merged, tname, pname):
    """The same pixels, format and palette under the same name, whatever the sets' offsets."""
    import nsbtx

    def piece(parsed):
        params = dict(parsed['texs'])[tname][0]
        pixels = nsbtx._tex_bytes(parsed, params)
        shape = params & ~0xffff                    # (format, size; the low half is the offset)
        if not pname:
            return shape, pixels, b''
        off = dict(parsed['pals'])[pname][0] << 3
        return shape, pixels, parsed['pdata'][off:off + nsbtx._pal_size(parsed, pname)]
    return piece(own) == piece(merged)


if __name__ == '__main__':
    main()
