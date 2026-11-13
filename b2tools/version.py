"""The game version of a build: Pearl (default), Diamond or Platinum (the HoennB2 HOENN_VERSION pattern; HoennB2's full module
is kept in reference/hoenn_version.py).

    PEARL_VERSION=pearl|diamond|platinum       (unset or empty = pearl; anything else stops the build)

Every tool that differs per version asks this module; nothing else reads PEARL_VERSION. A Pearl build must stay
byte-identical whether or not the other versions' support exists (b2tools/version_check.py proves it offline, against a base
commit). notes/DIAMOND.md has every difference of Diamond, section 7 what each one became here; notes/PLATINUM.md and
notes/PORT_AUDIT.md the same for Platinum.

A row of this file says which of two things a tool wants. Diamond shares Pearl's world: its maps, scripts, text and trainers
come from Pearl's dump (WORLD_DUMP, WORLD_WORK), with only what differs taken from its own (SOURCE_DUMP, WORK). Platinum's
world is its own, so the two are the same file there.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))

VERSIONS = ('pearl', 'diamond', 'platinum')
VERSION = (os.environ.get('PEARL_VERSION') or 'pearl').strip().lower()
if VERSION not in VERSIONS:
    raise SystemExit(f'PEARL_VERSION={VERSION!r}: expected one of {", ".join(VERSIONS)}')
DIAMOND = VERSION == 'diamond'
PLATINUM = VERSION == 'platinum'

NAME = {'pearl': 'Pearl', 'diamond': 'Diamond', 'platinum': 'Platinum'}[VERSION]
# The games' names (the user, 2026-11-01): title logo (data/title, title_lustrous.py), DS menu banner and ROM header
# (rom_identity.py), the credits and the Pal Park's migration text (game_names).
TITLE = {'pearl': 'Lustrous Pearl', 'diamond': 'Adamant Diamond', 'platinum': 'Griseous Platinum'}[VERSION]
PUBLIC_NAME = f'Pokémon {TITLE}'
RELEASE_STEM = f'Pokemon_{TITLE.replace(" ", "_")}'
HEADER_TITLE = {'pearl': 'POKEMON LP', 'diamond': 'POKEMON AD', 'platinum': 'POKEMON GP'}[VERSION]   # the ROM header's 12 characters
SOURCE_GAME_CODE = {'pearl': 'APAE', 'diamond': 'ADAE', 'platinum': 'CPUE'}[VERSION]   # the Gen 4 dump the content comes from
SOURCE_DUMP = os.path.join(ROOT, 'roms', f'{VERSION}.nds')
ENCOUNTER_NARC = {'pearl': 'fielddata/encountdata/p_enc_data.narc',
                  'diamond': 'fielddata/encountdata/d_enc_data.narc',
                  'platinum': 'fielddata/encountdata/pl_enc_data.narc'}[VERSION]
PERSONAL_NARC = {'pearl': 'poketool/personal_pearl/personal.narc', 'diamond': 'poketool/personal/personal.narc',
                 'platinum': 'poketool/personal/pl_personal.narc'}[VERSION]
WORK = os.path.join(ROOT, 'work', VERSION)         # gen4_extract's output for the version's own wild tables and Town Map
# Where the world comes from: maps, events, scripts, text, trainers, music. Diamond shares Pearl's (see above).
_WORLD = 'platinum' if PLATINUM else 'pearl'
WORLD_DUMP = os.path.join(ROOT, 'roms', f'{_WORLD}.nds')
WORLD_WORK = os.path.join(ROOT, 'work', _WORLD)    # gen4_extract, gen4_land, gen4_script, gen4_trainers, sinnoh_trainers, ...
# The world dump's archives, by what they hold. Platinum dropped "_release" and has its own msg, moves, items and sound.
ARCHIVE = {'land': 'fielddata/land_data/land_data.narc' if PLATINUM else 'fielddata/land_data/land_data_release.narc',
           'scripts': 'fielddata/script/scr_seq.narc' if PLATINUM else 'fielddata/script/scr_seq_release.narc',
           'events': 'fielddata/eventdata/zone_event.narc' if PLATINUM else 'fielddata/eventdata/zone_event_release.narc',
           'msg': 'msgdata/pl_msg.narc' if PLATINUM else 'msgdata/msg.narc',
           'moves': 'poketool/waza/pl_waza_tbl.narc' if PLATINUM else 'poketool/waza/waza_tbl.narc',
           'items': 'itemtool/itemdata/pl_item_data.narc' if PLATINUM else 'itemtool/itemdata/item_data.narc',
           'sound': 'data/sound/pl_sound_data.sdat' if PLATINUM else 'data/sound/sound_data.sdat',
           'batt_obj': 'battle/graphic/pl_batt_obj.narc' if PLATINUM else 'battle/graphic/batt_obj.narc',
           'pokedex_area': {'pearl': 'application/zukanlist/zkn_data/zukan_enc_pearl.narc',
                            'diamond': 'application/zukanlist/zkn_data/zukan_enc_diamond.narc',
                            'platinum': 'application/zukanlist/zkn_data/zukan_enc_platinum.narc'}[VERSION]}
SCRIPT_TABLE = 'gen4_script_cmds_platinum.json' if PLATINUM else 'gen4_script_cmds.json'   # gen4_script's command table
PEARL_ZONES = 559                                  # Diamond's and Pearl's zones, the same places under the same numbers in Platinum
ZONE_COUNT = 593 if PLATINUM else PEARL_ZONES      # zones of the dump
ROM_NAME = f'{VERSION}.nds'                        # the built ROM, in the build dir
GAME_VERSION_BY = {'pearl': 11, 'diamond': 10, 'platinum': 12}
GAME_VERSION = GAME_VERSION_BY[VERSION]   # pokediamond VERSION_PEARL / VERSION_DIAMOND,
                                                       # pokeplatinum VERSION_PLATINUM: what a converted script's
                                                       # GetGameVersion gets (PEARLB2_GAME_VERSION, patches/scripts.py)
# The list column of BDSP's data (Underground Hideaways, Ramanas Park): Shining Pearl's, Brilliant Diamond's, or both for
# Platinum (the user, 2026-11-01: all 11 rooms, both versions' Hideaways and treasures; notes/PLATINUM.md section 5). The
# build version alone picks it (the data files keep no "version" key). Readers go through bdsp_columns().
BDSP = {'pearl': 'sp', 'diamond': 'bd', 'platinum': 'both'}[VERSION]
# What every Pokémon made in the game is stamped with (Met game): Diamond 10 (rom_identity.stamp_met_game). None leaves
# Black 2's own 23, which is what a Pearl build has always done (Pearl's real 11 would change its ROM; see DIAMOND.md 7).
MET_GAME = {'pearl': 11, 'diamond': 10, 'platinum': 12}[VERSION]
# Which builds take the six species' held items from their dump (patches/sinnoh_encounters.py HELD_SPECIES): Diamond. A Pearl
# build keeps Black 2's, as it always has (Pearl's own would change its ROM; see DIAMOND.md 7).
HELD_ITEMS_FROM_DUMP = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
ENCOUNTER_FILES = 183
# pearl_model_fix's ground rule (notes/MAP_LOOK.md "Platinum's ground", 2026-11-02): a big ground piece moves only against a
# bigger one (never as the decal of a smaller piece), one ground drawn twice stays, and the under-floor tries 8 units down under
# a backing layer. Platinum's snow patches (polygons bigger than the grass tiles under them) sank Twinleaf's ground in steps:
# black seams. 1.0.1 (2026-11-07): on for Pearl and Diamond too. With plat-caves' rules under it, it changes 197 of their 526
# chunks: holes 1,147.2 -> 272.2 units^2 (pearl_seams_check --holes), Route 211 West's line 91.5 -> 7.5, the Contest Hall
# lobby's 18 -> 0; one chunk worse, Route 210 North 63 (0 -> 8, a cliff corner at (28, 22); notes/V1_0_1.md). SEAM_GUARDS
# (below) fixes that corner and the two places the check missed.
GROUND_STAYS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# The seams seen from the side (1.0.1, 2026-11-07, v101-seams; on for all three versions): three guards in pearl_model_fix's
# layer rules under GROUND_STAYS (DECAL_PIECES, SLIVER_TREES, SLOPES_HELD), found with pearl_seams_check --holes --views:
# Route 210 North's corner, the Contest Hall lobby's back wall and Valor Lakefront's corner (1.0.1's ground fix made them
# worse than 1.0) are clean, and Turnback Cave's Giratina room. Pearl: 10 of 526 chunks change from main, 8 better, none
# worse (notes/MAP_LOOK.md "1.0.1: the seams seen from the side"; notes/V1_0_1.md).
SEAM_GUARDS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# Land models drawn on translated nodes (notes/MAP_LOOK.md "Shifted nodes", 2026-11-02): the DS adds a node's translation to
# its shapes' vertices. With this row the map fixes (pearl_model_fix), the checks (pearl_seams_check) and the rooms' camera
# boundary (sinnoh_rooms) take each shape where it is drawn. Platinum draws 43 land models on such nodes (gatehouses, the Lost
# Tower, Veilstone Store 1F, the Galactic HQ, Iron Island, ...): the fixes judged those shapes where they aren't and opened
# holes. Pearl's and Diamond's two (chunks 410 and 417) keep the older way: with it on, 1.0.1 measured their holes at 0 either
# way (it would change the two models and fix nothing), so it stays off for them.
NODE_SHIFT = {'pearl': False, 'diamond': False, 'platinum': True}[VERSION]
# Platinum's snow patches (Twinleaf, Routes 201-202, Verity Lakefront, Lake Verity) show in winter only (the user,
# 2026-11-03): sinnoh_reskin clears these textures in the spring, summer and autumn sets (seasons off: spring all year, so
# never), and pearl_chunk reads their tiles (SNOW_WITH_SHADOWS) as the plain ground Pearl has there, so summer grass leaves
# no snow footprints and no snow battle background. Pearl and Diamond have no such textures.
SNOW_PATCHES_WINTER_ONLY = ('s_snow', 's_snow02', 's_snow04', 's_sonwp') if PLATINUM else ()
# The same places' trees: Platinum's tree04_2 is tree01 with 150 of its 4,096 texels turned to snow (same palette, format and
# size). It takes tree01's texels in every season (nsbtx.copy_texels): outside winter the dusting goes with the patches, and
# in winter Black 2's recolour turns the dusting into bright cyan specks (Lake Verity, 2026-11-07), so winter's trees are
# the plain tree's, recoloured like every other.
SNOW_DUSTED = {'tree04_2': 'tree01'} if PLATINUM else {}
# The layers fix (pearl_model_fix.separate) leaves alone an overlapping pair inside one piece (2026-11-02, plat-rooms):
# a piece moves as one, and such a pair pushed it to MAX_PUSH. Pearl's and Diamond's released maps keep the old rule (1.0.1
# measured it with GROUND_STAYS on: none of their 526 chunks changes, so it stays off for them).
SELF_PAIRS_STAY = {'pearl': False, 'diamond': False, 'platinum': True}[VERSION]
# A tile's drawn surface is its ground only at a BDHC plate (pearl_chunk.bdhc_ground, 2026-11-07, plat-heights): over every
# plate it is overhead (the Veilstone Gym's ceiling rails were the floor of 122 tiles), under every plate the water or floor
# is drawn elsewhere (the lakes' water props). 1.0.1 (2026-11-07): on for Pearl and Diamond too (Azelf's and Uxie's pools,
# the lakes' Surf, the Elite Four's doors, ...: notes/V1_0_1.md "Map heights"); b2tools/heights_check.py finds 0 in all three.
GROUND_AT_BDHC = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# A room's solid tiles take the BDHC's ground too (pearl_chunk.room_chunks, 2026-11-08, plat-test). Platinum's scripts walk
# people through walls (the four Frontier lobbies' walk to the corridor: the attendant and the player north through the back
# wall's rows): Gen 4 moves them at the plate under the wall or keeps their height where there is none, while the wall's
# drawn top (116 units in the Factory's lobby) lifted them and the camera into the void over the room. Pearl's and
# Diamond's released maps keep the drawn surface there.
SOLID_AT_BDHC = {'pearl': False, 'diamond': False, 'platinum': True}[VERSION]
# Archive reserves past build_rom.RESERVE's (bytes over the original, {archive: reserve}; 2026-11-07, plat-test): Platinum's
# story, Distortion World and five Frontier facilities filled the script text (a/0/0/3: 4,121 of 4,096 KiB) and scripts
# (a/0/5/6: 1,050 of 1,024 KiB). Pearl's and Diamond's ROM layout stays as released.
RESERVE_MORE = {'pearl': {}, 'diamond': {}, 'platinum': {3: 6 << 20, 56: 2 << 20}}[VERSION]
# Defog used in a zone sets that zone's story flag (pokeplatinum scripts_field_moves.s FieldMoves_UseDefogFromMenu: the Lost
# Tower 5F's old ladies give their Spell Tag and Cleanse Tag only after it; 2026-11-07, plat-ch5). Pearl's Lost Tower has no fog.
# {zone: the flag's pearl.h name}; patches/pearl_defog.py writes the check into the Defog script.
DEFOG_ZONE_FLAGS = {'pearl': {}, 'diamond': {},
                    'platinum': {'MAP_ROUTE_209_LOST_TOWER_5F': 'PFLAG_007B'}}[VERSION]   # FLAG_USED_DEFOG_IN_ROUTE_209_LOST_TOWER_5F
# ---- plat-fixes (2026-11-07)
# A texture some chunks draw with a second palette: sinnoh_reskin puts every palette a chunk's material names into the
# autumn and winter sets it rebuilds (and gives each one the season's recolour). It kept one palette a texture, the first
# chunk's, so a second one was missing: Platinum draws criffp and wcliff with criff on most routes but with criffp and
# wcriff on Routes 225-230 and Stark Mountain, whose rocks and paths drew pink, with white specks and green fringes, in
# autumn and winter. Pearl's and Diamond's overworld draws each texture with one palette; their outdoor rooms keep the
# released sets.
EVERY_PALETTE = {'pearl': False, 'diamond': False, 'platinum': True}[VERSION]
# The professors' Pokédex ratings (pearl_story h_dex_rating, pearl_story.inc): {mode: (first line, last line, macro)} of the
# rating bank (335). Rowan (mode 0, the Sinnoh seen count): Pearl's and Diamond's lines 4-14 (the two "met them all" lines,
# then 9 tiers up to 150: pokediamond sub_02054CC8), Platinum's 4-17 (12 tiers up to 210, nothing left out of the count:
# pokeplatinum Pokedex_GetRatingMessageID_Local). Oak (mode 1, the National caught count, the same tiers in all three):
# Pearl's lines 19-39, Platinum's 22-42. The PC's rating is src/field_scripts/<version>/1260_global_pokedex_rating.s.
DEX_RATING = {'pearl': {0: (4, 14, 'Local'), 1: (19, 39, 'National')},
              'diamond': {0: (4, 14, 'Local'), 1: (19, 39, 'National')},
              'platinum': {0: (4, 17, 'LocalPlatinum'), 1: (22, 42, 'National')}}[VERSION]
# ---- end plat-fixes
# The songs a version's scripts start themselves, on top of Pearl's (patches/sinnoh_music.py EVENT_SONGS), and the fanfares
# its scripts play by id (2026-11-07, plat-music; notes/MUSIC.md "Platinum"). sinnoh_music installs them; the scripts play
# them as SEQ_PEARL_<name> (pearl_story.py's block "plat-music"). Platinum: Looker's theme (CommonScript_SetLookerBGM: SetBGM
# 1200), the Villa's piano, audio system and music box, Spear Pillar's cutscene songs (overlay 100), the Poké Radar's song
# (Route 202's demonstration: Pearl's SEQ_KUSAGASA), and the Battle Hall's BP fanfare (a WaitFanfare follows it).
STORY_SONGS = {'pearl': (), 'diamond': (),
               'platinum': ('SEQ_PL_HANDSOME', 'SEQ_PL_PIANO', 'SEQ_PL_AUDIO', 'SEQ_PL_TOWN02', 'SEQ_PL_EV_GIRA',
                            'SEQ_PL_EV_GIRA2', 'SEQ_KUSAGASA')}[VERSION]
# (plat-stubs, 2026-11-08) And the Battle Castle's CP fanfare after each win (SEQ_PL_FRO; a WaitFanfare follows: as a stub it hung).
STORY_FANFARES = {'pearl': (), 'diamond': (), 'platinum': ('SEQ_PL_POINTGET3', 'SEQ_PL_FRO')}[VERSION]
# ---- plat-frontier-rooms (2026-11-07): Platinum's Frontier Brains
# Trainer classes past Black 2's 236, in this order from 236 (the decomp's include/pearlb2/trainer_class.h,
# resident/trainer_class.c): patches/pearl_trainers.py gives each its name, picture, sex and eye-contact song. Black 2's spare
# classes are all Pearl's. Platinum: Argenta, Thorton, Dahlia, Darach (Palmer is Pearl's TOWER_TYCOON on class 198). Append
# only: a class id never moves once given; ids stay below 256 (some of Black 2's structs keep a class in a u8).
NEW_TRAINER_CLASSES = {'pearl': (), 'diamond': (),
                       'platinum': ('HALL_MATRON', 'FACTORY_HEAD', 'ARCADE_STAR', 'CASTLE_VALET')}[VERSION]
# ---- end plat-frontier-rooms
# Gen 4's in-game trades, the Mining Museum's fossil restorer and ActivateRoamingPokemon (CreateRoamer) as real commands
# (plat-trades, 2026-11-07): the generator's "plat-trades" block, patches/npc_trades.py, patches/roamers.py's extension
# table. On for Platinum; Pearl's and Diamond's 1.0 keep their stubs and their two roamers until 1.0.1 turns these on
# (notes/V1_0_1.md). The code (decomp resident/npc_trade.c, roamers.c) is in every build and does nothing without them.
# (v101-story, 2026-11-07: 1.0.1 turns all three on for Pearl and Diamond. Pearl keeps its two roamer slots: roamers.py has
# no extension table for it, so CreateRoamer releases its slot at once. The trade table comes from the version's dump.)
NPC_TRADES = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
FOSSIL_RESTORER = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
ROAMER_COMMAND = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# ---- v101-story (2026-11-07): 1.0.1's script fixes for Pearl and Diamond (work/agents/V101_BRIEF.md "v101-story";
# notes/V1_0_1.md). Each row is a gate of pearl_story.py that was Platinum's only; Pearl's and Diamond's 1.0 kept the stub
# (False there would give the 1.0 scripts back). Rows that are new fixes, which Platinum doesn't have, say so.
# The Trainers' School blackboard: ShowMenuMultiColumn as Black 2's list menu (plat-ch2's h_menu_columns). The menu never
# showed: the lesson went round for ever.
MENU_COLUMNS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# The Old Chateau's ghosts: CheckShouldShowGhost at 10 % and 25 % with Black 2's Random (plat-ch3's h_ghost).
GHOSTS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# A Pokémon shown in a scene is marked seen, as Gen 4's preview does (plat-ch6's h_preview_seen): Verity Cavern's Mesprit,
# Fullmoon Island's Cresselia, the Celestic elder's Dialga and Palkia.
PREVIEW_SEEN = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# Pastoria's Combee boy (CheckPartyCombeeGenderCount) and the Pokémon Mansion office's book (CheckHasSeenSpecies): plat-ch6's
# party and Pokédex questions. Both were stubs in Pearl's 1.0 too, so the Macho Brace came by chance (the lead, 2026-11-07).
PARTY_QUESTIONS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# ReturnToField after an app that never ran opens nothing (plat-ch7's h_return_field_open): Black 2's FieldOpen on an open
# field waits for ever (the Jubilife TV boards, the trades' and the Move Deleter's old hang).
FIELD_STAYS_OPEN = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# The Move Deleter on Black 2's move list (plat-ch7's five handlers and fades).
MOVE_DELETER = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# The Pokétch developer's nature check, a party loop (plat-ch10's h_nature_slot).
NATURE_CHECK = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# A price past 65,535 checked exactly (pearl_story.inc pl_CheckMoneyBig, plat-rooms' Villa): the Ribbon Syndicate's two
# 100,000 ribbons. Pearl's 1.0 checked 65,535.
EXACT_BIG_MONEY = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# Platinum's party commands for ribbons, contest conditions, footprints and effort values (plat-tutors' block; extension
# 0xB0-0xB6, overlay 376): the scarf man, Dr. Footstep, Julia, the Sunyshore Market, the Ribbon Syndicate. Their tables come
# from the version's own dump (platinum_party_data.py); the shard tutors are Platinum's only.
PARTY_COMMANDS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# New in 1.0.1, Pearl and Diamond only (Platinum's output doesn't change; it can take each one by its row):
# Deoxys's forms at Veilstone's meteorites (Pearl 0x262 CheckPokemonInParty, 0x263 SetDeoxysForm) on Black 2's
# PokePartySetForme, as plat-ch9's Giratina.
# (plat-stubs, 2026-11-08) Platinum too: its 0x262 CheckPartyHasSpecies2 species, var and 0x263 ChangeDeoxysForm form are the same
# commands (pokeplatinum scrcmd.c: Party_HasSpecies, each party Deoxys to the form, stats and Pokédex), Veilstone's same four.
DEOXYS_FORMS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# Hearthome's Secret Base goods for the Underground's feats (Pearl 0x293, 0x286-0x288: people met, items given away, Fossils
# dug, Traps set in the tunnels; the Blue, Pink, Red and Yellow Crystal): this Underground has no digging, Traps or other
# players, so they count as done and the man gives the four, one a talk, after his other goods (the brief: "give the
# stubbed gifts"). Pearl's 1.0 left them stubs: never given.
# (plat-stubs) Platinum too: its Hearthome man asks the same four records (0x293, 0x286-0x288) for the same Crystals.
UNDERGROUND_GIFTS = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# The Pokétch apps no story script gives (Matchup Checker 22, Stopwatch 23, Alarm Clock 24): Pearl's own source is its Mystery
# Gift, which has a Pokétch-app gift (pokediamond UNK_020F43E4, bank 332 line 18): the deliveryman gives them after Pearl's four
# event gifts (pearl_story.inc PL_DELIVERY_GIFTS 7). Platinum gives its Matchup Checker in the Great Marsh: none here.
# (plat-stubs, 2026-11-08) Platinum: its Matchup Checker comes from the Great Marsh (Pastoria's observatory gate, five caught);
# the Stopwatch and the Alarm Clock only from its Mystery Gift (pokeplatinum scripts_common.s CommonScript_ObtainedPoketch-
# Stopwatch / AlarmClock, its deliveryman's line 19 "received the Pokétch app ...!"): the deliveryman gives those two after its
# six gifts (pearl_story.inc PL_DELIVERY_GIFTS 8).
POKETCH_APP_GIFTS = {'pearl': (22, 23, 24), 'diamond': (22, 23, 24), 'platinum': (23, 24)}[VERSION]
# The Game Corner's prize TMs on sale at Veilstone Dept. Store 3F (the lead's decision, 2026-11-07: the Game Corner stays
# closed; notes/DECISIONS.md): {SpecialMart n: Pearl items added after Pearl's own}. Pearl's own price each (its item data,
# as the counters' other TMs: pearl_shops.pearl_price): the support TMs at the left counter (list 12: TM44 Rest 3,000, TM58
# Endure, TM108 here, 2,000, TM75 Swords Dance 1,500), the attacks at the right one with Hyper Beam (list 13: TM74 Gyro Ball
# 3,000, TM68 Giga Impact 7,500). pearl_items.mart_special() adds them, so the shop patch and the guide read the same lists.
# (plat-stubs, 2026-11-08) Platinum: its own prize list (pokeplatinum scrcmd_game_corner_prize.c) has six TMs no other
# script, ball, hidden item or Mart gives (TM10 Hidden Power, TM44 Rest, TM58 Endure, TM68 Giga Impact, TM74 Gyro Ball, TM75
# Swords Dance; TM44 is also a Pickup find, as in Pearl): the same counters at Platinum's own prices (pl_item_data: TM44 3,000,
# TM108 Endure 2,000, TM75 1,500 at the left counter, list 12 MART_SPECIALTIES_ID_VEILSTONE_3F_UP after its TM70 Flash; TM10
# 2,000, TM74 3,000, TM68 7,500 at the right one, list 13 _3F_DOWN after its TM15 Hyper Beam, in the prize list's order).
STORE_TMS = {'pearl': {12: (371, 385, 402), 13: (401, 395)}, 'diamond': {12: (371, 385, 402), 13: (401, 395)},
             'platinum': {12: (371, 385, 402), 13: (337, 401, 395)}}[VERSION]
# (2026-11-11, the user: "yes") Griseous Platinum: its Game Corner's four held-item prizes (pokeplatinum
# scrcmd_game_corner_prize.c, 1,000 coins each: Silk Scarf, Wide Lens, Zoom Lens, Metronome), which no script, ball, hidden
# item or Mart gives, are sold for money at Veilstone Dept. Store 2F's battle-item counter (list 10
# MART_SPECIALTIES_ID_VEILSTONE_2F_UP, after its X Sp. Def), at Black 2's prices, which are Platinum's (Silk Scarf 100, the
# others 200). pearl_items.mart_special() adds them after STORE_TMS. Pearl's and Diamond's Game Corner had the same four
# (pokediamond scrcmd_prizes.c), with no other source there either; (2026-11-11, the user: "Yes, rebuild them") their 1.0.1
# sells them at the same counter (Pearl's list 10 is its Veilstone 2F X items too, script 5 of
# 1425_pearl_veilstone_department_store_2f), after its X Sp. Def.
STORE_ITEMS = {'pearl': {10: (251, 265, 276, 277)}, 'diamond': {10: (251, 265, 276, 277)},
               'platinum': {10: (251, 265, 276, 277)}}[VERSION]
# People who stand where the player can't reach them and have a job: {Pearl zone: {Pearl object id: (x, z, direction)}}
# (pearl_events.entities puts them there). The Veilstone Game Corner's coin clerk, TM64's giver, stands behind its closed
# line (data/pearl_closed_facilities.json: row 10): here at the line, (4, 10), facing the player in row 11 (the lead's
# decision, 2026-11-07). Her talk is Pearl's: with a Coin Case she gives TM64, then her Coin counter. Her check of ten
# straight bonus rounds (Pearl 0x275) counts as met while the slots are closed (GAME_CORNER_CLOSED; a stub before, which
# left the Coin Case's answer in the var).
# (plat-stubs) Platinum the same: its Game Corner is Pearl's map (land 196, the same rows 10 and 11) with the same people (and
# Looker at (9, 8), behind the line), its coin clerk object 0 at (2, 4) with the same talk (TM64 Explosion with a Coin Case, the
# Veilstone southeast house's, after ten bonus rounds: 0x275 CheckBonusRoundStreak).
MOVED_PEOPLE = {'pearl': {'MAP_VEILSTONE_GAME_CORNER': {0: (4, 10, 1)}},
                'diamond': {'MAP_VEILSTONE_GAME_CORNER': {0: (4, 10, 1)}},
                'platinum': {'MAP_VEILSTONE_GAME_CORNER': {0: (4, 10, 1)}}}[VERSION]
GAME_CORNER_CLOSED = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# The Battle Tower's trophies for a 20-, 50- and 100-win streak (Pearl 0x1DF; the Bronze, Silver and Gold Trophy goods):
# pearl_story.inc pl_TowerTrophy on decomp extension 0x91 and 0x92 (resident/tower.c). A stub before ("none here").
# (plat-stubs, 2026-11-08) Platinum too, by its own rule (pokeplatinum unk_0206B9D8.c sub_0206BDBC, sub_0206BF04): the Single
# record streak (STAT_TOWER_RECORD_STREAK_SINGLE: the Frontier core's record 0, the Subway's single mode), not the best of any
# room; the same steps, goods and marks (pl_TowerTrophy*'s #if).
TOWER_TROPHIES = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# Floaroma's Accessory shop (Pearl 0x257 AccessoriesShop: its berry-for-Accessory exchange, overlay 6): Pearl's own 22 rows
# (the Accessory, the Berry, how many) and its lines (bank 516), in Black 2's list menu with the 1.0 Fashion Case commands
# (pearl_story h_accessory_shop). A stub before: the clerk said nothing.
# (plat-stubs, 2026-11-08) Platinum too, with its own 22 rows (overlay 7, pokeplatinum overlay007/accessory_shop.c: the same
# Accessories 50-71 for other Berries and counts, the Red Flower for one Cheri Berry) and its own lines (the same numbers of
# its flower shop bank).
ACCESSORY_SHOP = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]
# ---- end v101-story
# ---- postdex (2026-11-09): the National Pokédex can be completed in the post-game (the user, 2026-11-09; notes/POSTGAME_DEX.md).
# Everything waits on the game clear, flag 2400. The other version whose exclusives come after the Champion: its wild slots
# where its files differ (data/postgame_dex.json, patches/wild.py gPearlB2PostGame: half the time in the shared slot), its
# Grand Underground column at stage 6 (ug_data.entry_stage), its fossil in the daily fossil balls (underground_scripts).
# None: no other version.
POSTGAME_OTHER_BY = {'pearl': 'diamond', 'diamond': 'pearl', 'platinum': None}
POSTGAME_OTHER = POSTGAME_OTHER_BY[VERSION]
# The Poké Radar's species that no build has otherwise: after the Champion at the Radar's slots, half the time (the Radar
# stays closed). Taillow, Whismur and Exploud follow by breeding and evolving.
POSTGAME_RADAR_BY = {v: ('STANTLER', 'SMEARGLE', 'SWELLOW', 'LOUDRED') for v in VERSIONS}
POSTGAME_RADAR = POSTGAME_RADAR_BY[VERSION]
# Pal Park's rooms (b2tools/ramanas.py): 'sp' / 'bd' (9 rooms, 1.0), 'both' (all 11, the data's "both" requirements), 'sp+bd'
# and 'bd+sp' (all 11, each room keeping its own version's requirement, the first column's for the shared rooms: a 1.0
# save's open rooms stay open). The park itself opens at Champion.
RAMANAS_ROOMS_BY = {'pearl': 'sp+bd', 'diamond': 'bd+sp', 'platinum': 'both'}
RAMANAS_ROOMS = RAMANAS_ROOMS_BY[VERSION]
# The other version's legendary at Spear Pillar after the Hall of Fame, once the version's own is caught (pearl_story's
# Spear Pillar hook, b2tools/postgame_legend.py): (species, level, the Orb it leaves). Platinum has both already.
POSTGAME_LEGEND_BY = {'pearl': (483, 47, 'ADAMANT_ORB'), 'diamond': (484, 47, 'LUSTROUS_ORB'), 'platinum': None}
POSTGAME_LEGEND = POSTGAME_LEGEND_BY[VERSION]
# The deliveryman's event Pokémon after his other gifts (data/event_gifts.json, patches/event_gifts.py, decomp extension
# 0xA9): real Gen 4-era events, one a talk.
EVENT_GIFTS = ('MEW', 'CELEBI', 'JIRACHI', 'DEOXYS')
# ---- end postdex
# ---- plat-fix2 (2026-11-11): the Frontier's and the Tower's last differences from Platinum.
# The wireless link's starts (Gen 4 StartBattleClient / StartBattleServer: the Frontier lobbies' Multi, the Tower's link
# Multi, the Poffin house, the Contest Hall, a Pokémon Center 2F) answer COMM_CLUB_RET_CANCEL (1), as when a player backs out
# of the search with nobody there: the script goes back to its "join a group or become the leader" menu. As stubs they kept
# the Yes (0, "connected"), so the Frontier's Multi attendant started a Multi challenge with no partner. Pearl and Diamond:
# the same stubs (the Poffin house, the Contest Hall, the League's 2F; the Tower's Multi drops that branch) wait for a later
# release, as their output must not change now.
LINK_STARTS_CANCEL = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]   # (2026-11-12, the user: "fix them": Pearl's and Diamond's 1.0.1 too)
# The Battle Tower's opponent's line (PrintBattleTowerIntroMessage: Black 2's balloon, BSubwayCmd_Tool 352) waits for A itself,
# so the WaitABPress after it asked for a second A, as the four facilities' did before plat-test's fix: dropped. Pearl and
# Diamond have the same second A (their Tower rooms): for a later release.
TOWER_INTRO_ONE_A = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]   # (2026-11-12, the user: "fix them": Pearl's and Diamond's 1.0.1 too)
# The Battle Tower after a reset without saving (tower function 14, the lobby's "didn't save before quitting"): Platinum's
# rule (pokeplatinum unk_02049D08.c sub_0204A064) ends the challenge and sets its latest streak to 0; Black 2's
# BSubwayCmd_Tool 7 ends it but keeps the latest streak saved at the last loss or seven wins (the records machines' PREV).
# True: pl_TowerDisqualify (decomp Frontier core op 0x08, resident/plat_frontier.c). Pearl's own rule is likely the same
# as Platinum's (its lobby runs the same function 14 after the same line; pokediamond doesn't decompile it): Pearl and
# Diamond keep Black 2's for now (their output must not change; the op is in Platinum's Frontier core).
TOWER_DISQUALIFY_ZERO = {'pearl': True, 'diamond': True, 'platinum': True}[VERSION]   # (2026-11-12, the user: "fix them": Pearl's and Diamond's 1.0.1 too)
# The Battle Hall's records machine (Platinum's global 10453 in the Hall's lobby, (7, 8)): its species list (the letters'
# species with a record, Platinum's alphabetical order) and each species' record, as a message (Black 2 has no records
# screen), on the Hall's ops 0x4F, 0x50 (decomp hall_field.c, overlay 379). False: the list answers EXIT (plat-stubs).
# Platinum only (Pearl and Diamond have no Battle Hall).
HALL_RECORDS_MACHINE = {'pearl': False, 'diamond': False, 'platinum': True}[VERSION]
# ---- end plat-fix2

# Spear Pillar: its header says matrix 22 in both games, and pokediamond's MapHeader_GetMatrixId (arm9/src/map_header.c:663)
# swaps 22 for 23 in Pearl. The maps differ: Diamond's chunks 352-355, Pearl's 356-359 (other pillars, other collision).
# Our tables (data/sinnoh_world.json: matrix 511, chunks 1356-1359) name the place by 22 and 352-355 in both versions, so
# no released number moves; those numbers are slots, and land_id says which of Pearl's land files fills one.
# Platinum's land files have their own numbers and data/platinum/sinnoh_world.json names them directly.
_LAND_OF_SLOT = {'pearl': {352: 356, 353: 357, 354: 358, 355: 359}, 'diamond': {}, 'platinum': {}}[VERSION]


def land_id(chunk):
    """The file <WORLD_WORK>/land/NNN.* of a chunk of our tables, for this version (every other chunk is its own file)."""
    return _LAND_OF_SLOT.get(chunk, chunk)


def bdsp_columns():
    """The BDSP columns this version reads, in the order the lists join: ('sp',), ('bd',) or, for Platinum, both."""
    return ('sp', 'bd') if BDSP == 'both' else (BDSP,)


def data_out(name):
    """Where a tool writes a registry or table of data/: data/NAME; Platinum's own numbers (keyed by its land files, ...) go to
    data/platinum/NAME, so a Platinum run never rewrites what Pearl and Diamond read."""
    return os.path.join(ROOT, 'data', 'platinum', name) if PLATINUM else os.path.join(ROOT, 'data', name)


def data_path(name):
    """A registry or table of data/: data/platinum/NAME when Platinum has its own, else data/NAME. Pearl and Diamond always
    read data/NAME."""
    own = data_out(name)
    return own if os.path.exists(own) else os.path.join(ROOT, 'data', name)


_ID_MAP = None


def id_map(kind):
    """Platinum's {slot: its own file} by data/platinum/id_map.json (platinum_maps.py): a slot is Pearl's number for the same place."""
    global _ID_MAP
    if _ID_MAP is None:
        import json
        _ID_MAP = json.load(open(os.path.join(ROOT, 'data', 'platinum', 'id_map.json')))
    return {int(k): v for k, v in _ID_MAP[kind].items()}


def slotted(kind, members):
    """An archive's members as the tools index them: as they are, or for Platinum by slot (Pearl's numbers; b'' where no file fills one)."""
    if not PLATINUM:
        return members
    m = id_map(kind)
    return [members[m[k]] if k in m else b'' for k in range(max(m) + 1)]


def of_slot(kind):
    """{Platinum's file: slot}: the number the tools use for it."""
    return {v: k for k, v in id_map(kind).items()}


def build_dir(default):
    """The ROM folder: PEARL_BUILD_DIR or `default` (work/rom) for Pearl, the same + '_diamond' or '_platinum' for the others
    (an explicit folder too, unless its name already says so), so another version's build never writes into a Pearl build."""
    d = (os.environ.get('PEARL_BUILD_DIR') or default).rstrip('/')
    if VERSION != 'pearl' and VERSION not in os.path.basename(d):
        d += '_' + VERSION
    return d


def sources(folder, ext):
    """A source folder's files in number order; a Diamond or Platinum build takes folder/<version>/ NAME in place of folder/
    NAME (the files that are generated per version: Ramanas Park's rooms). Pearl never reads those folders. Platinum starts from Pearl's
    files too (its base), and pearl_story's generated_folder(folder), git-ignored like the rest of work/, replaces those a zone changed;
    Diamond only replaces."""
    import glob
    out = {os.path.basename(p): p for p in glob.glob(os.path.join(folder, '*' + ext))}
    if VERSION != 'pearl':
        for p in glob.glob(os.path.join(folder, VERSION, '*' + ext)):
            assert PLATINUM or os.path.basename(p) in out, f'{p} replaces nothing'
            out[os.path.basename(p)] = p
    if PLATINUM:
        for p in glob.glob(os.path.join(generated_folder(folder), '*' + ext)):
            out[os.path.basename(p)] = p
    return [out[k] for k in sorted(out)]


def generated_folder(folder):
    """Where a generator's output for this source folder goes: the folder itself, or for Platinum the same place under work/platinum."""
    return os.path.join(WORK, 'src', os.path.relpath(folder, os.path.join(ROOT, 'src'))) if PLATINUM else folder


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
    return text.replace('Pokémon Pearl', 'Pokémon Lustrous Pearl').replace('Pokémon Diamond', 'Pokémon Adamant Diamond') \
               .replace('Pokémon Platinum', 'Pokémon Griseous Platinum')
