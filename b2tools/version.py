"""The game version of a build: Pearl (default) or Diamond (the HoennB2 HOENN_VERSION pattern; HoennB2's full module is
kept in reference/hoenn_version.py).

    PEARL_VERSION=pearl|diamond       (unset or empty = pearl; anything else stops the build)

Every tool that differs per version asks this module; nothing else reads PEARL_VERSION. A Pearl build must stay
byte-identical whether or not Diamond support exists (b2tools/version_check.py proves it offline, against a base commit).
notes/DIAMOND.md has every difference; section 7 what each one became here.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))

VERSIONS = ('pearl', 'diamond')
VERSION = (os.environ.get('PEARL_VERSION') or 'pearl').strip().lower()
if VERSION not in VERSIONS:
    raise SystemExit(f'PEARL_VERSION={VERSION!r}: expected one of {", ".join(VERSIONS)}')
DIAMOND = VERSION == 'diamond'

NAME = {'pearl': 'Pearl', 'diamond': 'Diamond'}[VERSION]
# The games' names (the user, 2026-11-01): title logo (data/title, title_lustrous.py), DS menu banner and ROM header
# (rom_identity.py), the credits and the Pal Park's migration text (game_names).
TITLE = {'pearl': 'Lustrous Pearl', 'diamond': 'Adamant Diamond'}[VERSION]
PUBLIC_NAME = f'Pokémon {TITLE}'
RELEASE_STEM = f'Pokemon_{TITLE.replace(" ", "_")}'
HEADER_TITLE = {'pearl': 'POKEMON LP', 'diamond': 'POKEMON AD'}[VERSION]   # the ROM header's 12 characters
SOURCE_GAME_CODE = {'pearl': 'APAE', 'diamond': 'ADAE'}[VERSION]   # the Gen 4 dump the content comes from
SOURCE_DUMP = os.path.join(ROOT, 'roms', f'{VERSION}.nds')
ENCOUNTER_NARC = {'pearl': 'fielddata/encountdata/p_enc_data.narc',
                  'diamond': 'fielddata/encountdata/d_enc_data.narc'}[VERSION]
PERSONAL_NARC = {'pearl': 'poketool/personal_pearl/personal.narc', 'diamond': 'poketool/personal/personal.narc'}[VERSION]
WORK = os.path.join(ROOT, 'work', VERSION)         # gen4_extract's output for the version's own wild tables and Town Map
ROM_NAME = f'{VERSION}.nds'                        # the built ROM, in the build dir
GAME_VERSION = {'pearl': 11, 'diamond': 10}[VERSION]   # pokediamond VERSION_PEARL / VERSION_DIAMOND: what a converted
                                                       # script's GetGameVersion gets (PEARLB2_GAME_VERSION, patches/scripts.py)
# The list column of BDSP's data (Underground Hideaways, Ramanas Park): Shining Pearl's or Brilliant Diamond's. The build
# version alone picks it (the data files keep no "version" key).
BDSP = {'pearl': 'sp', 'diamond': 'bd'}[VERSION]
# What every Pokémon made in the game is stamped with (Met game): Diamond 10 (rom_identity.stamp_met_game). None leaves
# Black 2's own 23, which is what a Pearl build has always done (Pearl's real 11 would change its ROM; see DIAMOND.md 7).
MET_GAME = {'pearl': 11, 'diamond': 10}[VERSION]
# Which builds take the six species' held items from their dump (patches/sinnoh_encounters.py HELD_SPECIES): Diamond. A Pearl
# build keeps Black 2's, as it always has (Pearl's own would change its ROM; see DIAMOND.md 7).
HELD_ITEMS_FROM_DUMP = {'pearl': True, 'diamond': True}[VERSION]
ENCOUNTER_FILES = 183

# Spear Pillar: its header says matrix 22 in both games, and pokediamond's MapHeader_GetMatrixId (arm9/src/map_header.c:663)
# swaps 22 for 23 in Pearl. The maps differ: Diamond's chunks 352-355, Pearl's 356-359 (other pillars, other collision).
# Our tables (data/sinnoh_world.json: matrix 511, chunks 1356-1359) name the place by 22 and 352-355 in both versions, so
# no released number moves; those numbers are slots, and land_id says which of Pearl's land files fills one.
_LAND_OF_SLOT = {'pearl': {352: 356, 353: 357, 354: 358, 355: 359}, 'diamond': {}}[VERSION]


def land_id(chunk):
    """The file work/pearl/land/NNN.* of a chunk of our tables, for this version (every other chunk is its own file)."""
    return _LAND_OF_SLOT.get(chunk, chunk)


def build_dir(default):
    """The ROM folder: PEARL_BUILD_DIR or `default` (work/rom) for Pearl, the same + '_diamond' for Diamond (an explicit
    folder too, unless its name already says so), so a Diamond build never writes into a Pearl build."""
    d = (os.environ.get('PEARL_BUILD_DIR') or default).rstrip('/')
    if DIAMOND and 'diamond' not in os.path.basename(d):
        d += '_diamond'
    return d


def sources(folder, ext):
    """A source folder's files in number order; a Diamond build takes folder/diamond/ NAME in place of folder/ NAME (the
    files that are generated per version: Ramanas Park's rooms). Pearl never reads diamond/."""
    import glob
    out = {os.path.basename(p): p for p in glob.glob(os.path.join(folder, '*' + ext))}
    if DIAMOND:
        for p in glob.glob(os.path.join(folder, 'diamond', '*' + ext)):
            assert os.path.basename(p) in out, f'{p} replaces nothing'
            out[os.path.basename(p)] = p
    return [out[k] for k in sorted(out)]


def check_inputs():
    """A build stops here, at once, if this version's own data is missing: nothing may fall back on the other version's."""
    from gen4rom import Rom
    if not os.path.exists(SOURCE_DUMP):
        raise SystemExit(f'{VERSION}: {SOURCE_DUMP} is missing (your own {NAME} dump; roms/ is git-ignored)')
    code = Rom(SOURCE_DUMP).code
    if code != SOURCE_GAME_CODE:
        raise SystemExit(f'{SOURCE_DUMP} is {code}, not {NAME} ({SOURCE_GAME_CODE})')
    enc = os.path.join(WORK, 'encounters')
    have = len(os.listdir(enc)) if os.path.isdir(enc) else 0
    if have != ENCOUNTER_FILES or not all(os.path.exists(os.path.join(WORK, p)) for p in ('zones.json', 'matrices', 'events')):
        raise SystemExit(f'{VERSION}: {enc} has {have} of {ENCOUNTER_FILES} encounter files: run '
                         f'PEARL_VERSION={VERSION} python3 b2tools/gen4_extract.py first')


def game_names(text):
    """A line of Pearl's own text that names the game as a product ("Pokémon Pearl"), with the games' new names. Only
    for those lines: "Pearl" as an item or in Pearl's story stays."""
    return text.replace('Pokémon Pearl', 'Pokémon Lustrous Pearl').replace('Pokémon Diamond', 'Pokémon Adamant Diamond')
