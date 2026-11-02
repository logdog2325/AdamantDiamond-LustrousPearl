"""Pearl's Battle Tower on Black 2's Battle Subway (notes/BATTLE_ZONE.md). Runs after zone_effects (the plugin lists).

apply (NitroFS):
- Pearl's tower trainers and sets, battle/b_tower/btdtr.narc and btdpm.narc of the dump, over Black 2's a/2/1/2 and
  a/2/1/1. The formats are the same (trainer: u16 class, u16 count, u16 sets[]; set: 16 bytes) and both archives have
  room: id t is file t + 1 of a/2/1/2 (Pearl's 307: 300-304 the partners Cheryl, Mira, Riley, Marley, Buck; 305-306
  Palmer's silver and gold teams). Each class becomes the Black 2 class data/pearl_trainer_classes.json gives it.
- Their names and lines: Pearl's banks 16 and 555 (3 lines per trainer, as Black 2) into system text 15 and 376.
apply_code:
- Script plugin 1 (Black 2's Battle Subway commands) loads in the tower's zones: its 11 zone slots
  (SCRIPT_PLUGIN_TABLE, ov012) = the lobby, the six rooms, then no zone.
- gPearlB2TowerSprites: the opponents' field sprites, Pearl's own table (class -> graphics id, read from the dump)
  through data/pearl_sprite_map.json.
"""
import json, os, re, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import narcio  # noqa: E402

TRAINER_ARC, SET_ARC = 212, 211
TRAINER_COUNT, SET_COUNT = 307, 951
NAME_BANK, LINE_BANK = 16, 555
SYSTEM_NAMES, SYSTEM_LINES = 15, 376
LOBBY = 'MAP_BATTLE_TOWER_LOBBY'
ROOMS = ('MAP_BATTLE_TOWER_ELEVATOR', 'MAP_BATTLE_TOWER_CORRIDOR_MULTI', 'MAP_BATTLE_TOWER_CORRIDOR_WIFI',
         'MAP_BATTLE_TOWER_ARENA_MULTI', 'MAP_BATTLE_TOWER_ARENA_WIFI', 'MAP_BATTLE_TOWER_PARTNER_ROOM')
PLUGIN_TABLE, OV012, PLUGIN_SUBWAY, SUBWAY_SLOTS, NO_ZONE = 0x0216C1AC, 0x021503C0, 1, 11, 0xFFFF
# The start of Pearl's class -> graphics table in the dump (Cheryl, Riley, Marley, Buck)
SPRITE_TABLE_START = struct.pack('<8H', 90, 141, 91, 142, 92, 143, 93, 144)
SPRITE_TABLE_ROWS = 63


def _rom():
    from gen4rom import Rom
    return Rom(os.path.join(ROOT, 'roms', 'pearl.nds'))


def _pearl_classes():
    """{Pearl class number: Black 2 class number}."""
    import pearl_trainers, sinnoh_trainers
    reg = pearl_trainers.class_registry()
    b2_classes, _ = pearl_trainers.b2_constants()
    consts = re.findall(r'#define (TRAINER_CLASS_\w+)\s+(\d+)', open(os.path.join(
        ROOT, 'external', 'pokediamond', 'include', 'constants', 'trainer_classes.h')).read())
    out = {}
    for name, number in consts:
        pc = name[len('TRAINER_CLASS_'):]
        if pc in reg['classes']:
            out[int(number)] = reg['classes'][pc]['b2']
        elif 'TRAINER_CLASS_' + sinnoh_trainers.CLASS_MAP.get(pc, ('?',))[0] in b2_classes:  # Black 2's for the role
            out[int(number)] = b2_classes.index('TRAINER_CLASS_' + sinnoh_trainers.CLASS_MAP[pc][0])
    return out


def trainers_and_sets():
    """(a/2/1/2's trainer files, by id; a/2/1/1's set files), Pearl's, with Black 2's class numbers."""
    from gen4rom import narc_members
    rom = _rom()
    tr = narc_members(rom.read('battle/b_tower/btdtr.narc'))
    sets = narc_members(rom.read('battle/b_tower/btdpm.narc'))
    assert (len(tr), len(sets)) == (TRAINER_COUNT, SET_COUNT), (len(tr), len(sets))
    classes = _pearl_classes()
    out = []
    for t in tr:
        cls, count = struct.unpack_from('<HH', t)
        assert cls in classes, f'battle_tower: Pearl class {cls} has no Black 2 class'
        out.append(struct.pack('<HH', classes[cls], count) + t[4:4 + 2 * count])
    assert all(len(s) == 16 for s in sets)
    return out, sets


def _texts(tree):
    """Pearl's names and lines into the facility's trainer data of the clone (system text takes them from there)."""
    import gen4_text
    sys.path.insert(0, os.path.join(ROOT, 'external', 'pokebw2'))
    from tools.text.text_sources import to_json
    names, lines = gen4_text.bank(NAME_BANK), gen4_text.bank(LINE_BANK)
    assert len(names) == TRAINER_COUNT and len(lines) == 3 * TRAINER_COUNT, (len(names), len(lines))
    root = os.path.join(tree, 'res', 'trainers', 'facilities', 'battle_subway')
    order = json.load(open(os.path.join(root, 'order.json')))['trainers']
    for t in range(TRAINER_COUNT):
        path = os.path.join(root, 'trainers', order[t] + '.json')
        data = json.load(open(path, encoding='utf-8'))
        data['name'] = names[t]
        msgs = []
        for i in range(3):
            line = gen4_text.b2_line(lines[3 * t + i].strip())
            while line.endswith('\\n'):
                line = line[:-2]
            msgs.append(to_json(line))
        data['messages'] = msgs
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)


def apply(files):
    import pokebw2_mod
    tr, sets = trainers_and_sets()
    arc = narcio.load(files, TRAINER_ARC)
    assert len(arc) > TRAINER_COUNT, len(arc)
    for t, data in enumerate(tr):
        arc[t + 1] = data
    narcio.save(files, TRAINER_ARC, arc)
    arc = narcio.load(files, SET_ARC)
    assert len(arc) >= SET_COUNT, len(arc)
    arc[:SET_COUNT] = sets
    narcio.save(files, SET_ARC, arc)

    tree = pokebw2_mod.make_tree('battle_tower')
    _texts(tree)
    text = pokebw2_mod.pack_text(tree, 'system')['a/0/0/2']
    sys.path.insert(0, os.path.join(ROOT, 'external', 'pokebw2'))
    from tools.data.narc import read_narc, write_narc
    mine = read_narc(text)
    path = os.path.join(files, 'a', '0', '0', '2')
    cur = read_narc(open(path, 'rb').read())
    vanilla = read_narc(pokebw2_mod.vanilla('a/0/0/2'))
    for n in (SYSTEM_NAMES, SYSTEM_LINES):
        assert cur[n] == vanilla[n], f'a/0/0/2 file {n} was changed by another patch'
        cur[n] = mine[n]
    if os.path.islink(path):
        os.unlink(path)
    open(path + '.tmp', 'wb').write(write_narc(cur))
    os.replace(path + '.tmp', path)
    shutil.rmtree(tree)
    return f'battle_tower: Pearl\'s {len(tr)} trainers, {len(sets)} sets, names and lines'


def sprite_rows():
    """Black 2's (class, object code) for Pearl's class -> graphics table in the dump."""
    data = _rom().data
    at = data.find(SPRITE_TABLE_START)
    assert at >= 0, 'battle_tower: Pearl\'s class -> graphics table not found'
    sprite_map = json.load(open(os.path.join(ROOT, 'data', 'pearl_sprite_map.json')))
    classes = _pearl_classes()
    rows, seen = [], set()
    for i in range(SPRITE_TABLE_ROWS):
        cls, gfx = struct.unpack_from('<HH', data, at + 4 * i)
        entry = sprite_map.get(str(gfx))
        if cls in classes and entry and entry.get('code') is not None and classes[cls] not in seen:
            rows.append((classes[cls], entry['code']))
            seen.add(classes[cls])
    tycoon = sprite_map.get('169')             # Palmer (Pearl's graphics 0xA9), not in that table
    if tycoon:
        rows.append((json.load(open(os.path.join(ROOT, 'data', 'pearl_trainer_classes.json')))
                     ['classes']['TOWER_TYCOON']['b2'], tycoon['code']))
    return rows


def apply_code(code):
    import decomp, resident
    world = json.load(open(os.path.join(ROOT, 'data', 'sinnoh_world.json')))
    zones = {e['name']: e['b2_zone'] for e in world['rooms']['zones'].values()}
    wanted = [zones[LOBBY]] + [zones[r] for r in ROOMS]
    assert len(wanted) <= SUBWAY_SLOTS

    path = os.path.join(code, 'arm9_ov012.bin')
    ov = bytearray(open(path, 'rb').read())
    table = decomp.symbol('SCRIPT_PLUGIN_TABLE', code) or PLUGIN_TABLE
    _, zp, n, _, _ = struct.unpack_from('<IIIii', ov, table - OV012 + 20 * PLUGIN_SUBWAY)
    assert n == SUBWAY_SLOTS, f'battle_tower: plugin {PLUGIN_SUBWAY} has {n} zones'
    for i in range(n):
        struct.pack_into('<H', ov, zp - OV012 + 2 * i, wanted[i] if i < len(wanted) else NO_ZONE)
    if os.path.islink(path):
        os.unlink(path)
    open(path, 'wb').write(ov)

    rows = sprite_rows()
    blob = b''.join(struct.pack('<HH', c, o) for c, o in rows)
    slot, count = decomp.symbol('gPearlB2TowerSprites', code), decomp.symbol('gPearlB2TowerSpriteCount', code)
    assert slot is not None and count is not None, 'battle_tower: this decomp has no tower code'
    base, _, _ = resident.install(code, lambda b: (blob, {}))
    resident.write(code, slot, struct.pack('<I', base))
    resident.write(code, count, struct.pack('<I', len(rows)))
    return f'battle_tower: plugin {PLUGIN_SUBWAY} in zones {wanted}; {len(rows)} opponent sprites at {base:#x}'
