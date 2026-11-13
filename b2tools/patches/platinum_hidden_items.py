"""Platinum's hidden items past 228 (2026-11-07, plat-story; notes/PLATINUM_CHAPTERS.md "Hidden items").

The field hides a found hidden item by its flag, PearlB2_HiddenItemFlag (decomp src/pearlb2/resident/items.c): 2820 + n for
script 8000 + n. Platinum numbers its hidden items 0-228 and 256-283 (b2tools/pearl_items.py writes file 1241 from its own
table), and 2820 + n runs past Black 2's saved flags (3063) from n 244: the flag of an item past that would never set. This patch
gives 256-283 the flags 1100 + n - 256 (pearl_ids.HIDDEN_EXTRA: the registry's numbers for Platinum's flags 986-1013); 0-228 keep
2820 + n. PearlB2_HiddenItemFlag jumps to the new rule, so both its callers have it: the field's hidden-item signs
(GetHiddenItemEventFlagNoBySCRID, ov012) and the Pokétch's Dowsing app.

The Dowsing app's search ranges (sHiddenItemRanges, decomp src/pearlb2/poketch/poketch_map.c: Pearl's 229) take Platinum's for
0-228. The app's table stops at 229, so it doesn't show Platinum's 21 items 256-276; they are found with A like any other.

Platinum only: a Pearl or Diamond build doesn't run it, so their code is unchanged. List it after platinum_trainer_flags.
"""
import os, re, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import decomp, itcm, pearl_ids, resident, version  # noqa: E402

SCRIPT_FIRST, FLAG_FIRST = 8000, 2820       # decomp include/pearlb2.h PEARLB2_HIDDEN_SCRIPT_FIRST, PEARLB2_HIDDEN_FLAG_FIRST
RANGES = 229                                # sHiddenItemRanges' length (Pearl's table)
C = """
typedef unsigned short u16;
u16 PlatinumHiddenItemFlag(u16 scrId) {
    u16 n = scrId - %(script)d;
    return n >= %(first)d ? %(flag)d + n - %(first)d : n + %(base)d;
}
"""


def flag_of(n):
    """The rule the C has, for the offline check (pearl_items.hidden_flag is the generator's)."""
    first, flag = pearl_ids.HIDDEN_EXTRA
    return flag + n - first if n >= first else n + FLAG_FIRST


def _size(name, code):
    path = os.path.join(code, 'arm9.o.xMAP') if os.path.exists(os.path.join(code, 'arm9.o.xMAP')) else decomp.XMAP
    m = re.search(rf'^\s+[0-9A-F]{{8}} ([0-9A-F]{{8}}) \.\w+\s+{name}\t', open(path, errors='replace').read(), re.M)
    return int(m.group(1), 16) if m else None


def ranges(table):
    return bytes(table[n]['range'] if n in table else 0 for n in range(RANGES))


def pearl_table():
    """Pearl's hidden-item table (pearl_items.arm9 is Pearl's dump in every build), {n: record}."""
    import pearl_items
    a, ram = pearl_items.arm9()
    out = {}
    for i in range(229):
        item, count, rng, pad, n = struct.unpack_from('<HBBHH', a, 0x020F2DB4 - ram + 8 * i)
        out[n] = dict(item=item, count=count, range=rng)
    return out


def apply_code(code):
    assert version.PLATINUM, 'platinum_hidden_items: a Platinum build only'
    import pearl_items
    fn = decomp.symbol('PearlB2_HiddenItemFlag', code)
    at = decomp.symbol('sHiddenItemRanges', code)
    size = _size('PearlB2_HiddenItemFlag', code)
    assert fn is not None and at is not None and size, 'platinum_hidden_items: the decomp has no PearlB2_HiddenItemFlag / sHiddenItemRanges'
    first, flag = pearl_ids.HIDDEN_EXTRA
    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, 'hidden_items.c')
        open(src, 'w').write(C % dict(script=SCRIPT_FIRST, first=first, flag=flag, base=FLAG_FIRST))
        base, end, sym = resident.install(code, lambda b: itcm.build(src, b, t))
    jump = itcm.long_jump(fn, sym['PlatinumHiddenItemFlag'])
    assert len(jump) <= size, f'PearlB2_HiddenItemFlag is {size} B, the jump {len(jump)}'
    resident.write(code, fn, jump)
    old, new = resident.read(code, at, RANGES), ranges(pearl_items.hidden_items())
    if old != new:              # (a quick non-clean build has them already)
        assert old == ranges(pearl_table()), 'sHiddenItemRanges: not Pearl\'s ranges'
        resident.write(code, at, new)
    moved = sum(a != b for a, b in zip(old, new))
    return (f'platinum_hidden_items: hidden items {first}+ on flags {flag}+ (PearlB2_HiddenItemFlag -> {base:#x}-{end:#x}); '
            f'the Dowsing app\'s ranges are Platinum\'s ({moved} of {RANGES} changed)')
