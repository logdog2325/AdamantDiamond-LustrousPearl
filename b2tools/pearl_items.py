"""Pearl's items in the world (notes/OPEN_CONTENT.md "Items, TMs, shops"): the data, read from the user's Pearl dump, and
the global scripts that give them.

    python3 pearl_items.py                 write src/field_scripts/1240_global_item_balls.s, 1241_global_hidden_items.s,
                                           src/text/script/1303_global_item_balls.txt, 1304_global_hidden_items.txt, 1302_global_mart.txt
    python3 pearl_items.py --check         the same, compared: nonzero exit if a file is out of date
    python3 pearl_items.py --list          every ball and hidden item: zone, tile, item, count, flag, range

Item balls: Pearl's objects with a script of 7000+n. Pearl's file 370 entry n+1 sets the item and count, its entry 256 is
the shared routine (found line, Bag check, the ball removed). Black 2's item balls are the same idea: a person with the
global script 7000+n (ov012 GLOBAL_SCRIPT_TABLE, a/0/5/6 file 1240). So file 1240 is Pearl's file 370 here, entry for
entry; every ball is a person of its zone (pearl_events: after Pearl's other people) with the same script id. A ball's
hide flag is its Pearl flag through the registry (986+n -> Black 2's 1100+n), set by the shared routine
(pl_RemoveTalkedObject): one-time, saved. Pearl has 255 ball scripts, 253 used, 260 objects (7 balls stand on two maps
of the same place, the lakes' two versions, with one flag).

Hidden items: Pearl's BG events of type 2 with a script of 8000+n. Pearl's code (pokediamond sub_020396E8; Platinum
ScriptManager_SetHiddenItem) looks n up in a table (arm9 0x020F2DB4, 229 records: item, count, Dowsing range, script)
and starts file 374's one shared routine with 0x8000 = item, 0x8001 = count, 0x8002 = flag 730+n. Black 2 has the same
thing: sign events with condition 2 run global script 8000+n (a/0/5/6 file 1241), each entry sets those works and goes
to a shared routine. So file 1241 holds one entry per Pearl script: Pearl's table's values, then Pearl's routine.
The game hides a found item by GetHiddenItemEventFlagNoBySCRID: flag 2820 + n (decomp src/ov012/hidden_item.c), the
registry's numbers for Pearl's 730+n (pearl_ids.py); Black 2's own table stops at 213, Pearl's at 229. Nothing brings
a hidden item back: Diamond and Pearl have no daily reset (Platinum's Honey and Iron Island one is its own), so
patches/pearl_shops.py clears the table's "comes back" bits.

Text: a/0/0/3 1303 (Pearl's bank 325) and 1304 (bank 333) (decomp PEARLB2_TEXT_GLOBAL_7000, _8000), each with the common
scripts' lines after it.

Shops: Pearl's tables (pokediamond arm9/src/scrcmd_mart.c), read from the dump: mart_normal(), mart_special().
Black 2's Mart menu (global 10110) reads a/0/0/3 1302 (PEARLB2_TEXT_GLOBAL_10110): Black 2's lines with Pearl's greeting
(Pearl's common script 2019) and Pearl's SEE YA!
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom  # noqa: E402

BALL_FILE, HIDDEN_FILE = 370, 374     # Pearl's script files (pearl_story SCRIPT_RANGES)
BALL_BANK, HIDDEN_BANK = 325, 333     # their text banks
BALL_SCRIPTS, HIDDEN_SCRIPTS = 1240, 1241     # Black 2's a/0/5/6 files for global 7000+ and 8000+
BALL_TEXT, HIDDEN_TEXT = 1303, 1304   # a/0/0/3 (decomp include/pearlb2.h PEARLB2_TEXT_GLOBAL_7000, _8000)
MART_TEXT = 1302                      # a/0/0/3 (decomp include/pearlb2.h PEARLB2_TEXT_GLOBAL_10110)
HIDDEN_TABLE, HIDDEN_COUNT = 0x020F2DB4, 229     # Pearl's hidden items (arm9): u16 item, u8 count, u8 range, u16 0, u16 n
HIDDEN_FLAG_PEARL = 730               # Pearl's flag of hidden item n: 730 + n (Black 2: pearl_ids, 2820 + n)
NORMAL_MART_COUNT, SPECIAL_MART_COUNT = 19, 19   # pokediamond sNormalMartBadgeThresholds, sSpecialMartPointers
BADGE_STEPS = 6                       # Pearl's "param" 1-6 (0 badges; 1-2; 3-4; 5-6; 7; 8): Black 2's six badge lists
ITEM_POKE_BALL = 4

_arm9 = None


def arm9():
    """(bytes of Pearl's ARM9 binary, its RAM address)."""
    global _arm9
    if _arm9 is None:
        d = Rom(os.path.join(ROOT, 'roms', 'pearl.nds')).data
        off, _, ram, size = struct.unpack_from('<4I', d, 0x20)
        _arm9 = d[off:off + size], ram
    return _arm9


def hidden_items():
    """{n: {'item', 'count', 'range'}} of Pearl's hidden-item table (script 8000 + n)."""
    a, ram = arm9()
    out = {}
    for i in range(HIDDEN_COUNT):
        item, count, rng, pad, n = struct.unpack_from('<HBBHH', a, HIDDEN_TABLE - ram + 8 * i)
        assert pad == 0 and n not in out and n < HIDDEN_COUNT, f'hidden item record {i}: {(item, count, rng, pad, n)}'
        out[n] = dict(item=item, count=count, range=rng)
    return out


def mart_normal():
    """[(Pearl item, step 1-6)] of Pearl's Mart, in its order: pokediamond sNormalMartBadgeThresholds, found in the dump
    by its first two rows (Poké Ball at 1, Great Ball at 3)."""
    a, _ = arm9()
    at = a.find(struct.pack('<4H', ITEM_POKE_BALL, 1, 3, 3))
    assert at >= 0 and a.find(struct.pack('<4H', ITEM_POKE_BALL, 1, 3, 3), at + 1) < 0, 'Mart table not found once'
    rows = [struct.unpack_from('<HH', a, at + 4 * i) for i in range(NORMAL_MART_COUNT)]
    assert all(1 <= s <= BADGE_STEPS for _, s in rows), rows
    return rows


def mart_lists():
    """Pearl's six badge lists, in Pearl's order (step k sells the rows with step <= k)."""
    rows = mart_normal()
    return [[it for it, s in rows if s <= k] for k in range(1, BADGE_STEPS + 1)]


def mart_special():
    """Pearl's 19 special lists (SpecialMart n), found in the dump: a table of 19 pointers whose list 8 begins with
    Potion, Super Potion and list 9 with Poké Ball, Great Ball (the Veilstone Dept. Store's first counters)."""
    a, ram = arm9()

    def items(p):
        o, out = p - ram, []
        while True:
            v, = struct.unpack_from('<H', a, o)
            if v == 0xFFFF:
                return out
            out.append(v)
            o += 2
            assert len(out) < 40, hex(p)

    found = []
    for at in range(0, len(a) - 4 * SPECIAL_MART_COUNT, 4):
        ptrs = struct.unpack_from(f'<{SPECIAL_MART_COUNT}I', a, at)
        if not all(ram <= p < ram + len(a) for p in ptrs):
            continue
        try:
            if items(ptrs[8])[:2] == [17, 26] and items(ptrs[9])[:2] == [4, 3]:
                found.append(ptrs)
        except (AssertionError, struct.error):
            continue
    assert len(found) == 1, f'{len(found)} special Mart tables in the dump'
    return [items(p) for p in found[0]]


def b2_item(item):
    """A Pearl item id as Black 2's: TMs and HMs by move, others the same."""
    import tm_audit
    return tm_audit.pearl_item(item)


# ---- the scripts --------------------------------------------------------------------------------------------------

def _job(pd, ids, f, bank):
    """A generator's Job for a global file: a Job needs a zone, so any with no events of its own, under the file's text
    bank (so the bank's line numbers stay)."""
    import pearl_events, pearl_story
    base = next(z for z in pd.zones if not any(pd.events(z)[k] for k in ('object_events', 'bg_events', 'coord_events'))
                and not pearl_events.level_scripts(pd, z)[0])
    return pearl_story.Job(pd, dict(base, name='GLOBAL_ITEMS', text_bank=bank, scripts=f), ids)


def _commons(pd, job):
    """The common scripts a global file calls (pearl_story translate's loop), as subroutines of the file."""
    import pearl_story
    subs, done = [], set()
    while job.common_queue:
        cf, bank, entry, mode = job.common_queue.pop(0)
        if (cf, entry, mode) in done:
            continue
        done.add((cf, entry, mode))
        pre = f'C{cf}_{entry}'
        tr = pearl_story.FileTr(job, cf, bank, mode=mode, starts=[(f'{pre}_S{entry}', pd.disasm(cf).entries[entry - 1],
                                                                   entry)], prefix=pre)
        subs += ['', f'// ---- Pearl global script {cf}:{entry} (a subroutine here)'] + tr.lines()
    return subs


HEAD = ['#include "asm/field_script.inc"', '#include "pearl.h"', '#include "pearl_story.inc"', '']


def ball_script(pd, ids):
    """(source lines, text lines, summary) of global 7000+: Pearl's file 370, entry for entry."""
    import pearl_story
    job = _job(pd, ids, BALL_FILE, BALL_BANK)
    d = pd.disasm(BALL_FILE)
    shared = len(d.entries)                          # entry 256: the routine the others go to
    starts = [(f'B_{k}', d.entries[k - 1], k) for k in range(1, shared)]
    code = pearl_story.FileTr(job, BALL_FILE, BALL_BANK, mode='common', starts=starts, prefix='B').lines()
    out = [f"// Global scripts 7000-{7000 + shared - 2} (a/0/5/6 entry {BALL_SCRIPTS}): Pearl's item balls, Pearl's file "
           f'{BALL_FILE} entry for entry. Written by', '// b2tools/pearl_items.py: do not edit. Text: a/0/0/3 file '
           f'{BALL_TEXT}.'] + HEAD
    out += [f'    ScriptEntry Ball_{k}' for k in range(1, shared)] + ['    ScriptEntriesEnd', '']
    for k in range(1, shared):
        out += [f'Ball_{k}:', f'    VMCall B_{k}', '    VMHalt', '']
    out += code + _commons(pd, job) + ['', '    .balign 4, 0', '']
    return out, [job.gen4_text.b2_line(t, v) for t, v in job.text], pearl_story.summary(job)


def hidden_script(pd, ids):
    """(source lines, text lines, summary) of global 8000+: Pearl's table's values, then file 374's routine."""
    import pearl_story
    job = _job(pd, ids, HIDDEN_FILE, HIDDEN_BANK)
    table = hidden_items()
    tr = pearl_story.FileTr(job, HIDDEN_FILE, HIDDEN_BANK, mode='common',
                            starts=[('H_Find', pd.disasm(HIDDEN_FILE).entries[0], 1)], prefix='H')
    code = tr.lines()
    out = [f"// Global scripts 8000-{8000 + HIDDEN_COUNT - 1} (a/0/5/6 entry {HIDDEN_SCRIPTS}): Pearl's hidden items "
           f"(arm9 table {HIDDEN_TABLE:#x}) and file {HIDDEN_FILE}'s routine.", '// Written by b2tools/pearl_items.py: '
           f'do not edit. Text: a/0/0/3 file {HIDDEN_TEXT}.'] + HEAD
    out += [f'    ScriptEntry Hidden_{n}' for n in range(HIDDEN_COUNT)] + ['    ScriptEntriesEnd', '']
    for n in range(HIDDEN_COUNT):
        r = table[n]
        item, note = pearl_story.item_value(r['item'])
        flag = ids.flag_value(HIDDEN_FLAG_PEARL + n)
        out += [f'Hidden_{n}:   // Pearl script {8000 + n}: {r["count"]} of item {r["item"]}, range {r["range"]}' + note,
                f'    WorkSet PVAR_8000, {item}', f'    WorkSet PVAR_8001, {r["count"]}',
                f'    WorkSet PVAR_8002, {flag}', '    VMJump H_Start', '']
    # (Pearl: the field plays the select sound and starts the routine with these works; Black 2's own hidden items
    # hold everyone still around theirs)
    out += ['H_Start:', '    ActorsPauseAll', '    pl_PlaySE SEQ_SE_MESSAGE', '    VMCall H_Find', '    FinishAllEvents',
            '    ActorsUnpauseAll', '    VMHalt', '']
    out += code + _commons(pd, job) + ['', '    .balign 4, 0', '']
    return out, [job.gen4_text.b2_line(t, v) for t, v in job.text], pearl_story.summary(job)


def mart_text():
    """Black 2's Mart lines (res/text/script/global_10110.txt, line for line) with Pearl's greeting and SEE YA!"""
    src = open(os.path.join(ROOT, 'external', 'pokebw2', 'res', 'text', 'script', 'global_10110.txt'),
               encoding='utf-8').read().split('\n')
    lines = [l for l in src if ' = ' in l]
    swap = {'Global10110_Text_WelcomeMayHelp': 'Welcome!\\nWhat do you need?',   # Pearl bank 199 line 37 (script 2019)
            'Global10110_Text_NoThanks': 'SEE YA!'}                              # Pearl bank 488 line 17
    out = []
    for l in lines:
        name = l.split(' = ')[0]
        out.append(f'{name} = {swap[name]}' if name in swap else l)
    assert all(any(l.startswith(k + ' =') for l in lines) for k in swap)
    return ''.join(l + '\n' for l in out)


def outputs():
    import pearl_ids, pearl_story
    pd = pearl_story.PearlData()
    ids = pearl_ids.Ids()
    b, btext, bwhy = ball_script(pd, ids)
    h, htext, hwhy = hidden_script(pd, ids)
    src, txt = os.path.join(ROOT, 'src', 'field_scripts'), os.path.join(ROOT, 'src', 'text', 'script')
    return {os.path.join(src, f'{BALL_SCRIPTS}_global_item_balls.s'): '\n'.join(b),
            os.path.join(src, f'{HIDDEN_SCRIPTS}_global_hidden_items.s'): '\n'.join(h),
            os.path.join(txt, f'{BALL_TEXT}_global_item_balls.txt'):
                ''.join(f'GlobalItemBalls_Text_{i:03d} = {t}\n' for i, t in enumerate(btext)),
            os.path.join(txt, f'{HIDDEN_TEXT}_global_hidden_items.txt'):
                ''.join(f'GlobalHiddenItems_Text_{i:03d} = {t}\n' for i, t in enumerate(htext)),
            os.path.join(txt, f'{MART_TEXT}_global_mart.txt'): mart_text()}, f'balls: {bwhy}\nhidden: {hwhy}'


def world():
    """Every Pearl ball and hidden item, one row each: dict(kind, zone, b2_zone, x, z, item, b2_item, count, flag,
    range, script, obj)."""
    import pearl_ids, pearl_story, pearl_events
    pd = pearl_story.PearlData()
    ids = pearl_ids.Ids()
    table = hidden_items()
    rows, seen = [], set()
    for z in pd.zones:
        if z['events'] in seen:
            continue
        seen.add(z['events'])
        ev = pd.events(z)
        for o in ev['object_events']:
            if pearl_events.item_ball(z, o):
                f, _, e = pearl_story.script_location(o['script'])
                d = pd.disasm(f)
                a = d.entries[e - 1]
                got = {}
                for _ in range(3):
                    end, op, args = d.insns[a]
                    if pd.cmd_name(op) == 'SetVarFromValue':
                        got[args[0][1]] = args[1][1]
                    a = end
                rows.append(dict(kind='ball', zone=z['name'], pearl_zone=z['id'], b2_zone=pd.b2_zone.get(z['id']),
                                 x=o['x'], z=o['z'], item=got[0x8008], b2_item=b2_item(got[0x8008]), count=got[0x8009],
                                 flag=ids.flag_value(o['hidden_flag']), script=o['script'], obj=o['id']))
        for b in ev['bg_events']:
            if pearl_events.script_kind(b['script']) == 'hidden':
                n = b['script'] - 8000
                r = table[n]
                rows.append(dict(kind='hidden', zone=z['name'], pearl_zone=z['id'], b2_zone=pd.b2_zone.get(z['id']),
                                 x=b['x'], z=b['z'], item=r['item'], b2_item=b2_item(r['item']), count=r['count'],
                                 flag=ids.flag_value(HIDDEN_FLAG_PEARL + n), range=r['range'], script=b['script']))
    return rows


def main(argv):
    if '--list' in argv:
        for r in world():
            print(json.dumps(r))
        return 0
    files, why = outputs()
    bad = 0
    for p, text in files.items():
        if '--check' in argv:
            if not os.path.exists(p) or open(p, encoding='utf-8').read() != text:
                print(f'{os.path.relpath(p, ROOT)}: out of date (run python3 b2tools/pearl_items.py)')
                bad = 1
        else:
            open(p, 'w', encoding='utf-8').write(text)
            print(os.path.relpath(p, ROOT))
    print(why)
    return bad


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
