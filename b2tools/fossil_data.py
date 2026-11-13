"""The fossils the version's Mining Museum restores (plat-trades, 2026-11-07), from its dump: what the generator's
"plat-trades" block (pearl_story.py) writes into the fossil commands' macros (pearl_story.inc block "plat-trades").

    PEARL_VERSION=platinum python3 b2tools/fossil_data.py         prints the table
    PEARL_VERSION=platinum python3 b2tools/fossil_data.py test    the offline test (below)

Gen 4's three fossil commands (pokeplatinum src/scrcmd_fossil.c; pokediamond arm9/src/scrcmd_fossils.c, the same) read
one table, sFossilItemToSpeciesMapping: seven {u16 item, u16 species}, Old Amber, Helix, Dome, Root, Claw, Armor and
Skull Fossil (Aerodactyl, Omanyte, Kabuto, Lileep, Anorith, Shieldon, Cranidos). GetFossilCount adds up the Bag's count
of every one; GetSpeciesFromFossil gives a fossil's species (0 for any other item); FindFossilAtThreshold walks the table
adding the counts and stops at the first fossil where the sum reaches the threshold (its item and its index). Platinum's
Underground gives both versions' fossils here (the user's decision: underground_digging.py), and the table takes both.

Black 2's own fossils (Cover, Plume: items 572, 573) are not in the table, as in Platinum: the Museum's script builds its
menu from its own seven CheckItems, so a Cover Fossil would be counted but never listed. Neither comes in Sinnoh.

The test: the table found once in the dump, equal to the decomp's, every item a fossil of Black 2's item numbers (the
same 99-105 its Nacrene restorer uses, decomp res/field/scripts/global_10280.s) and every species one of the seven.
"""
import functools, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

FOSSILS = 7
FIRST = (103, 142, 101, 138)            # Old Amber -> Aerodactyl, Helix Fossil -> Omanyte: how the table starts
ITEM_NAMES = {99: 'Root Fossil', 100: 'Claw Fossil', 101: 'Helix Fossil', 102: 'Dome Fossil', 103: 'Old Amber',
              104: 'Armor Fossil', 105: 'Skull Fossil'}
SPECIES_NAMES = {142: 'Aerodactyl', 138: 'Omanyte', 140: 'Kabuto', 345: 'Lileep', 347: 'Anorith', 410: 'Shieldon',
                 408: 'Cranidos'}
DECOMP_SRC = {'platinum': ('pokeplatinum', 'src/scrcmd_fossil.c'), 'pearl': ('pokediamond', 'arm9/src/scrcmd_fossils.c'),
              'diamond': ('pokediamond', 'arm9/src/scrcmd_fossils.c')}


@functools.lru_cache(None)
def table():
    """((item, species), ...) of the dump's sFossilItemToSpeciesMapping, in its order."""
    from gen4rom import Rom
    d = Rom(version.WORLD_DUMP).data
    hits = [m.start() for m in re.finditer(re.escape(struct.pack('<4H', *FIRST)), d)]
    assert len(hits) == 1, f'the fossil table: {len(hits)} matches in {version.WORLD_DUMP}'
    return tuple(struct.unpack_from('<2H', d, hits[0] + 4 * k) for k in range(FOSSILS))


def summary():
    return ', '.join(f'{ITEM_NAMES.get(i, i)} ({i}) -> {SPECIES_NAMES.get(s, s)} ({s})' for i, s in table())


def _decomp_table():
    repo, rel = DECOMP_SRC[version.VERSION]
    src = open(os.path.join(ROOT, 'external', repo, rel)).read()
    pairs = re.findall(r'(ITEM_\w+)\s*,\s*\.?species\s*=\s*(SPECIES_\w+)|\{\s*(ITEM_\w+)\s*,\s*(SPECIES_\w+)\s*\}', src)
    pairs += re.findall(r'\.item\s*=\s*(ITEM_\w+)\s*,\s*\.species\s*=\s*(SPECIES_\w+)', src)
    out = []
    for p in pairs:
        p = [x for x in p if x]
        if len(p) == 2 and tuple(p) not in out:
            out.append(tuple(p))
    return out


def test():
    problems = []
    t = table()
    print(summary())
    names = {'ITEM_OLD_AMBER': 103, 'ITEM_HELIX_FOSSIL': 101, 'ITEM_DOME_FOSSIL': 102, 'ITEM_ROOT_FOSSIL': 99,
             'ITEM_CLAW_FOSSIL': 100, 'ITEM_ARMOR_FOSSIL': 104, 'ITEM_SKULL_FOSSIL': 105,
             'SPECIES_AERODACTYL': 142, 'SPECIES_OMANYTE': 138, 'SPECIES_KABUTO': 140, 'SPECIES_LILEEP': 345,
             'SPECIES_ANORITH': 347, 'SPECIES_SHIELDON': 410, 'SPECIES_CRANIDOS': 408}
    dec = [(names[i], names[s]) for i, s in _decomp_table() if i in names and s in names]
    if dec and tuple(dec) != t:
        problems.append(f'the dump {t}, the decomp {dec}')
    if not dec:
        problems.append('the decomp\'s table was not found')
    for i, s in t:
        if i not in ITEM_NAMES or s not in SPECIES_NAMES:
            problems.append(f'({i}, {s}) is not a fossil this knows')
    if sorted(i for i, s in t) != list(range(99, 106)):
        problems.append('the items are not Black 2\'s 99-105 (Root .. Skull)')
    b2 = open(os.path.join(ROOT, 'external', 'pokebw2', 'res', 'field', 'scripts', 'global_10280.s')).read()
    for i in range(99, 106):
        if f'WorkSetConst 0x8025, {i}\n' not in b2:
            problems.append(f'Black 2\'s Nacrene restorer does not check item {i}')
    print(f'{len(t)} fossils; {len(problems)} problems')
    for p in problems:
        print('  ' + p)
    return not problems


if __name__ == '__main__':
    if sys.argv[1:] == ['test']:
        sys.exit(0 if test() else 1)
    print(summary())
