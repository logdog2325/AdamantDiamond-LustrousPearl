"""Pearl script file -> Black 2 field-script source (notes/STORY.md).

    python3 pearl_story.py zones NAME|ID ...    translate those Pearl zones into src/field_scripts/NNNN_pearl_<zone>.s and
                                                 their text into src/text/script/NNNN_pearl_<zone>.txt (and assemble)
    python3 pearl_story.py chapter 1            the zones of a chapter (CHAPTERS below)
    python3 pearl_story.py all                  every installed zone (PEARL_VERSION=platinum: into work/platinum/src)
    python3 pearl_story.py report               translate every Pearl zone's script file offline into
                                                 work/pearl/b2_scripts/ (not installed), assemble each, and write the
                                                 coverage report there (report.txt)
    python3 pearl_story.py show FILE            print the translation of one Pearl script file (stdout)

How (details in notes/STORY.md):
- Pearl's scripts are read from the dump (roms/pearl.nds, fielddata/script/scr_seq_release.narc) with gen4_script's
  disassembler (pokediamond's command table, b2tools/data/gen4_script_cmds.json). Every command is translated by a
  handler below into a macro of src/include/pearl_story.inc (pl_ + the command's name: Platinum's name for the opcode
  below 0x2C4, where Platinum numbers commands as pokediamond does, else pokediamond's) or into Black 2 commands.
  A command with no handler becomes `pl_stub Name` (no code), its Pearl command and arguments in a comment, counted
  per file in the report: nothing is dropped silently.
- Labels: P<file>_<addr> (Pearl byte offsets), scripts P<file>_S<n>. Only code reachable from the scripts is emitted.
  Movement lists keep Pearl's codes (the same in Black 2: b2tools/data/pearl_movement.json), after `.balign 4, 0`.
- Pearl's common scripts (CallCommonScript id >= 2000: pokediamond LoadScriptsAndMessagesByMapId's ranges,
  SCRIPT_RANGES) run as a sub-script sharing the vars in Pearl; here each one a zone uses becomes a subroutine of the
  zone's file (VMCall; ReturnCommonScript and End -> VMReturn), its lines appended to the zone's text file.
  NATIVE_COMMON lists the ones Black 2 does itself.
- Warps: Pearl's script goes on in the new map after Warp; Black 2's MapChangeCore changes the map when the script
  ends, and a reserved script runs on arrival. So the code after each Pearl Warp becomes a script of the destination
  zone's file ("continuation", entries after Pearl's own: warp_continuations), and the Warp itself RTReserveScript +
  MapChangeCore. Every generated file also ends with PearlArrive (fade in, release) for warps with nothing after them.
- Ids: flags, vars and trainers by their names in src/include/pearl.h (b2tools/pearl_ids.py, data/pearl_story_ids.json).
- Text: the zone's Pearl bank line for line (b2tools/gen4_text.py: Pearl's own text from the dump, converted to Black 2's
  codes), then the common scripts' and continuations' lines and the boy/girl copies of lines naming the counterpart.
- Who speaks: lines of a talk script (an NPC's) are said by that NPC (Black 2's balloon, ParentActorMsg); others use
  Black 2's plain window (SystemMsg), Pearl's own look; data/pearl_speakers.json can name the actor of a line
  ({"MAP_X": {"<pearl line>": uid}}).
"""
import collections, json, os, re, struct, sys
import b2font

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402
import gen4_script  # noqa: E402

PEARL = version.WORLD_WORK
PLATINUM = os.path.join(ROOT, 'external', 'pokeplatinum')
SRC_SCRIPTS = version.generated_folder(os.path.join(ROOT, 'src', 'field_scripts'))
SRC_TEXT = version.generated_folder(os.path.join(ROOT, 'src', 'text', 'script'))
OFFLINE = os.path.join(PEARL, 'b2_scripts')
SPEAKERS = version.data_path('pearl_speakers.json')   # (Platinum: data/platinum/, by its own line and object numbers)
# A line's word buffer that Gen 4 filled in an earlier script (its field keeps one word set for every script) and Black 2
# doesn't (a word set per script run): {"MAP_X": {"<line>": {"<buffer>": "rival" | "player"}}}, filled right before the
# line (h_message). Only Platinum has rows (data/platinum/pearl_buffer_fills.json; b2tools/text_check.py finds them).
# (plat-ch2, 2026-11-07) "item:N" fills an item's name (N: the script's item number), for a line whose script names the
# item only after it.
BUFFER_FILLS = version.data_path('pearl_buffer_fills.json')
FILL_MACROS = {'rival': 'pl_BufferRivalName', 'player': 'pl_BufferPlayerName'}
# Closed places (2026-10-25, chapters 4a/5a: the Contest counters, Amity Square, the Great Marsh): places Pearl has and
# this game does not build yet. data/pearl_closed_facilities.json, keyed by Pearl map name ("MAP_..."), a list of rows:
#   {"x", "z", "w", "h", "dir", "text"}      a step trigger (work 0: always) on those tiles; walking onto it shows text in
#                                            the plain window, then the player steps once in dir (Pearl's 0 up, 1 down,
#                                            2 left, 3 right): pl_closed_facility line, dir
#   {"talk": true, "obj": id, "text"}        the person with that Pearl object id shows text instead of its script
#   {"talk": true, "bg": index, "text"}      the same for the sign (bg event) with that index in Pearl's bg_events
#   {"talk": true, "obj": id, "contest": n, "text"}   (2026-11-01) that person runs global script 10785 + n, a Super Contest
#                                            counter: 0 official, 1 link (closed), 2 practice, 3 Poffin cooking. text is unused but kept.
#   {"talk": true, "obj": id, "musical": true, "text"}   (2026-10-25, the user: "for contests use musicals") that
#                                            person is a Pokémon Musical receptionist (src/include/pearl_musical.inc:
#                                            pl_musical_reception greeting, first): text is the greeting, in Pearl
#                                            spelling (\r a new page); the Musical's own lines (MUSICAL) are added once
#                                            to the zone's text
# text: plain words, "\n" breaks the line (the plain window is 224 px wide). Each row is a script entry after the
# zone's PearlArrive (PearlData.closed_ids), its line appended to the zone's text; pearl_events.entities adds the
# trigger or points the person/sign at the entry.
CLOSED = os.path.join(ROOT, 'data', 'pearl_closed_facilities.json')
MUSICAL = os.path.join(ROOT, 'data', 'pearl_musical.json')                # the Musical's lines (Black 2's)
MUSICAL_INC = os.path.join(ROOT, 'src', 'include', 'pearl_musical.inc')   # their order: its MUSL_* defines
# Pearl's elevators (2026-10-25, chapter 4a). Pearl's GetDynamicWarpFloorNumber (GetFloorsAbove var) gives the floors
# above the map the player came into the elevator from (the dynamic warp the elevator's exit, dest warp 0x100, goes
# back to: pokeplatinum field_map_change.c, SetSpecialLocation / FieldMenu_GetFloorsAbove); SetDynamicWarp
# (SetSpecialLocation) points that exit at the chosen floor. Black 2 keeps the same spot (GameData nextSpawn, set on
# the way in and by FieldSetNextZone) but no script command reads it, so: every floor below sets Pearl's own
# VAR_ELEVATOR_FLOORS_ABOVE (0x40CE) in a zone-init entry, the elevator room copies it into PL_ELEVATOR_FROM when
# the player walks in, GetFloorsAbove reads that, and SetSpecialLocation is FieldSetNextZone + the new floor there.
# Floors above per Pearl map: pokediamond MapNumToFloorNo (ov05 0x021E2608), any other map 1.
ELEVATOR_FLOORS_ABOVE = {11: 3, 12: 2, 13: 1, 14: 0,                 # Jubilife TV 1F-4F
                         103: 1, 104: 0, 112: 1, 113: 0,             # Hearthome south-east / north-east houses
                         137: 4, 138: 3, 139: 2, 140: 1, 141: 0,     # Veilstone Department Store 1F-5F
                         150: 1, 164: 0,                             # Sunyshore, the Vista Lighthouse deck
                         461: 1, 462: 0}                             # Resort Area Ribbon Syndicate 1F/2F
if version.PLATINUM:                                                 # (2026-11-02, plat-rooms) Platinum's own floor:
    ELEVATOR_FLOORS_ABOVE[566] = 5                                   # Veilstone Store B1F (field_menu.c, the same table)
FIRST_SCRIPT_FILE = 1290        # a/0/5/6: Black 2 has 0-1288, 1289 = 1289_twinleaf_newgame.s; Pearl zone files after
FIRST_TEXT_FILE = 676           # a/0/0/3: Black 2 has 0-675; Pearl zone text files after
NEWGAME_ZONE = 'MAP_TWINLEAF'   # Black 2 loads zone 427 first and runs its scripts 29 and 30 (notes/WORLD.md)
NEWGAME_ENTRIES = (29, 30, 31)
PEARL_START = ('MAP_TWINLEAF_RIVAL_HOUSE_2F', 4, 6, 0)    # Pearl's start: the player's room, (4, 6) facing up
# (pokeplatinum location.c sPlayerStartLocation; the tile is walkable here). pokediamond's names of zones 412-415 are
# swapped: 412/413 ("PLAYER_HOUSE") are Barry's house, 414/415 ("RIVAL_HOUSE") the player's (by their scripts and text,
# and Platinum's own header order). data/sinnoh_world.json keeps pokediamond's names.
FIRST_PROXY = 48                # Pearl global scripts that people/signs/triggers run: proxy entries from here, the same
                                # number in every zone file (a follower carries its script id from zone to zone)
FOLLOW = 0x30                   # Pearl's (and Black 2's) "follow the player" movement type
PARTNER_VAR = 0x403F            # Pearl's partner trainer (pokediamond sub_0205F368, read by StartTrainerBattle while
                                # SetHasPartner is on): Cheryl 608 in Eterna Forest (2026-10-25, chapter 3)

CHAPTERS = {
    1: ['MAP_TWINLEAF', 'MAP_TWINLEAF_PLAYER_HOUSE_1F', 'MAP_TWINLEAF_PLAYER_HOUSE_2F', 'MAP_TWINLEAF_RIVAL_HOUSE_1F',
        'MAP_TWINLEAF_RIVAL_HOUSE_2F', 'MAP_TWINLEAF_NORTHEAST_HOUSE', 'MAP_TWINLEAF_SOUTHWEST_HOUSE', 'MAP_ROUTE_201',
        'MAP_VERITY_LAKEFRONT', 'MAP_LAKE_VERITY', 'MAP_SANDGEM', 'MAP_SANDGEM_ROWANS_LAB',
        'MAP_SANDGEM_PROFESSOR_ASSISTANT_HOUSE_1F', 'MAP_SANDGEM_PROFESSOR_ASSISTANT_HOUSE_2F',
        'MAP_SANDGEM_SOUTHWEST_HOUSE', 'MAP_SANDGEM_POKEMART', 'MAP_SANDGEM_POKECENTER_1F'],
    # Chapter 2 (2026-10-18): Route 202 to Roark's Gym. Left out: Jubilife's south-east house 4F (on Pearl's
    # empty script file 368 with nothing to install: data/story_chapters.json "skip"), the Pokémon Center 2F/B1F
    # rooms (the shared 2F: pearl_centers) and the Route 218 gate (a later chapter)
    2: ['MAP_ROUTE_202', 'MAP_JUBLIFE', 'MAP_JUBLIFE_POKEMART', 'MAP_JUBLIFE_POKETCH_COMPANY_1F',
        'MAP_JUBLIFE_POKETCH_COMPANY_2F', 'MAP_JUBLIFE_POKETCH_COMPANY_3F', 'MAP_JUBLIFE_TV_1F', 'MAP_JUBLIFE_TV_2F',
        'MAP_JUBLIFE_TV_3F', 'MAP_JUBLIFE_TV_4F', 'MAP_JUBLIFE_TV_2F_GALLERY', 'MAP_JUBLIFE_TV_3F_GLOBAL_RANKINGS',
        'MAP_JUBLIFE_TV_3F_GROUP_RANKINGS', 'MAP_JUBLIFE_TV_ELEVATOR', 'MAP_JUBLIFE_SOUTHEAST_HOUSE_1F',
        'MAP_JUBLIFE_SOUTHEAST_HOUSE_2F', 'MAP_JUBLIFE_SOUTHEAST_HOUSE_3F', 'MAP_JUBLIFE_CONDOMINIUMS_1F',
        'MAP_JUBLIFE_CONDOMINIUMS_2F', 'MAP_JUBLIFE_CONDOMINIUMS_3F', 'MAP_JUBLIFE_CONDOMINIUMS_4F',
        'MAP_JUBLIFE_GLOBAL_TRADE_STATION', 'MAP_JUBLIFE_TRAINER_SCHOOL', 'MAP_JUBLIFE_SOUTHWEST_HOUSE_1F',
        'MAP_JUBLIFE_SOUTHWEST_HOUSE_2F', 'MAP_JUBLIFE_UNUSED_HOUSE_2', 'MAP_JUBLIFE_UNUSED_HOUSE_3', 'MAP_ROUTE_203',
        'MAP_OREBURGH_GATE_1F', 'MAP_OREBURGH_GATE_B1F', 'MAP_OREBURGH', 'MAP_OREBURGH_POKEMART', 'MAP_OREBURGH_GYM',
        'MAP_OREBURGH_NORTHWEST_HOUSE_1F', 'MAP_OREBURGH_NORTHWEST_HOUSE_2F', 'MAP_OREBURGH_NORTHWEST_HOUSE_3F',
        'MAP_OREBURGH_NORTHWEST_HOUSE_4F', 'MAP_OREBURGH_NORTH_HOUSE_1F', 'MAP_OREBURGH_NORTH_HOUSE_2F',
        'MAP_OREBURGH_NORTH_HOUSE_3F', 'MAP_OREBURGH_NORTH_HOUSE_4F', 'MAP_OREBURGH_MIDDLE_HOUSE',
        'MAP_OREBURGH_MINING_MUSEUM', 'MAP_OREBURGH_WEST_HOUSE', 'MAP_OREBURGH_EAST_HOUSE_1F',
        'MAP_OREBURGH_EAST_HOUSE_2F', 'MAP_OREBURGH_EAST_HOUSE_3F', 'MAP_OREBURGH_SOUTH_HOUSE',
        'MAP_OREBURGH_MINE_B1F', 'MAP_OREBURGH_MINE_B2F'],
    # every Pokémon Center 1F (nurse, PC, people), ahead of the story: healing everywhere (2026-10-18, the lead)
    90: [f'MAP_{t}_POKECENTER_1F' for t in ('JUBLIFE', 'CANALAVE', 'OREBURGH', 'ETERNA', 'HEARTHOME', 'PASTORIA',
                                            'VEILSTONE', 'SUNYSHORE', 'SNOWPOINT', 'POKEMON_LEAGUE', 'FIGHT_AREA',
                                            'FLOAROMA', 'SOLACEON', 'CELESTIC', 'SURVIVAL_AREA', 'RESORT_AREA')],
}

# Chapters 3-9 (and 'skip'): data/story_chapters.json (b2tools/story_chapters.py, notes/STORY_CHAPTERS.md). Platinum: every
# chapter, 1, 2 and 90 too, from data/platinum/story_chapters.json (its own order: notes/PLATINUM_CHAPTERS.md)
_CH = version.data_path('story_chapters.json')
if os.path.exists(_CH):
    for _k, _v in json.load(open(_CH)).items():
        if not _k.startswith('_'):
            _k = int(_k) if _k.isdigit() else _k
            if version.PLATINUM:
                CHAPTERS[_k] = _v
            else:
                CHAPTERS.setdefault(_k, _v)


# ---------------------------------------------------------------- Pearl data

class PearlData:
    def __init__(self):
        rom = Rom(version.WORLD_DUMP)
        self.files = version.slotted('scripts', narc_members(rom.read(version.ARCHIVE['scripts'])))
        self.table = gen4_script.load_table()
        self.zones = json.load(open(os.path.join(PEARL, 'zones.json')))
        self.by_name = {z['name']: z for z in self.zones}
        self.world = json.load(open(version.data_path('sinnoh_world.json')))
        self.b2_zone = {int(k): v['b2_zone'] for k, v in self.world['zones'].items()}
        self.b2_zone.update({int(k): v['b2_zone'] for k, v in self.world['rooms']['zones'].items()})
        self.level_files = {z['level_scripts'] for z in self.zones}
        self._dis, self._ev = {}, {}
        self._addrs, self._pearl_files, self._pearl_table, self._pearl_zones = {}, None, None, None
        script_files = sorted({z['scripts'] for z in self.zones})
        self.script_file_no = {f: FIRST_SCRIPT_FILE + i for i, f in enumerate(script_files)}
        banks = sorted({z['text_bank'] for z in self.zones})
        self.text_file_no = {b: FIRST_TEXT_FILE + i for i, b in enumerate(banks)}
        self._own_text = None                       # text_file(): own numbers of files on a shared bank
        self._own_zone = None                       # script_file(), text_file(): zones on a shared script file
        self.names = platinum_names()
        self._warps = None

    def pearl_addr(self, f, a):
        """Pearl's address of Platinum's command or movement list at (slot f, a), the same in both by aligning the two files (None: Pearl's
        file has none like it). So Pearl's fixes keyed by file and address stay on the same command when a file changed around it."""
        if not version.PLATINUM:
            return a
        if f not in self._addrs:
            self._addrs[f] = self._align_addrs(f)
        return self._addrs[f].get(a)

    def platinum_addr(self, f, pearl_a):
        """Platinum's address of Pearl's command at (slot f, pearl_a): for a fix's jump target."""
        if not version.PLATINUM:
            return pearl_a
        self.pearl_addr(f, 0)
        return next(a for a, p in dict(self._addrs[f]).items() if p == pearl_a)

    def zone_same(self, zone, script_path=None, text_path=None):
        """Platinum: does this zone keep Pearl's generated files, with every fix in them (notes/PLATINUM.md section 3)? Its script file and level
        scripts equal Pearl's, what we'd generate shows the same text as Pearl's file, and its people run the same scripts (the same events,
        or a generated file equal to Pearl's). script_path, text_path: this run's generated files."""
        if not version.PLATINUM or zone['id'] >= version.PEARL_ZONES:
            return False
        if self._pearl_zones is None:
            self._pearl_zones = json.load(open(os.path.join(ROOT, 'work', 'pearl', 'zones.json')))
            self._align_addrs(0)
            self._pearl_events = narc_members(Rom(os.path.join(ROOT, 'roms', 'pearl.nds')).read('fielddata/eventdata/zone_event_release.narc'))
            self._plat_events = version.slotted('events', narc_members(Rom(version.WORLD_DUMP).read(version.ARCHIVE['events'])))
        p = self._pearl_zones[zone['id']]
        if self._pearl_files[p['scripts']] != self.files[zone['scripts']] or self._pearl_files[p['level_scripts']] != self.files[zone['level_scripts']]:
            return False
        if script_path is None:
            return True
        base = os.path.join(ROOT, 'src')
        pearl_s = os.path.join(base, 'field_scripts', os.path.basename(script_path))
        pearl_t = os.path.join(base, 'text', 'script', os.path.basename(text_path))
        if not (os.path.exists(pearl_s) and os.path.exists(pearl_t)):
            return False
        ours, theirs = open(text_path, 'rb').read().split(b'\n'), open(pearl_t, 'rb').read().split(b'\n')
        if not self._shows_lines(zone['scripts']):      # (a zone with no lines of its own sits on Jubilife's bank: only what follows it counts)
            import gen4_text
            ours = [l.split(b' = ', 1)[-1] for l in ours[len(gen4_text.bank(zone['text_bank'])):]]
            theirs = [l.split(b' = ', 1)[-1] for l in theirs[len(gen4_text.bank_text(p['text_bank'], os.path.join(ROOT, 'roms', 'pearl.nds'))):]]
        if ours != theirs:
            return False
        # (and the generated file is Pearl's: other proxies, common scripts or labels would leave the people's script numbers off)
        return self._pearl_events[p['events']] == self._plat_events[zone['events']] and open(pearl_s, 'rb').read() == open(script_path, 'rb').read()

    def _align_addrs(self, f):
        import difflib
        if self._pearl_files is None:
            self._pearl_files = narc_members(Rom(os.path.join(ROOT, 'roms', 'pearl.nds')).read('fielddata/script/scr_seq_release.narc'))
            self._pearl_table = json.load(open(os.path.join(HERE, 'data', 'gen4_script_cmds.json')))
        if f >= len(self._pearl_files) or not self._pearl_files[f]:
            return {}
        if self._pearl_files[f] == self.files[f]:
            return collections.defaultdict(lambda: None, {a: a for a in self.disasm(f).insns} | {a: a for a in self.disasm(f).movement})
        def tokens(d, table):
            out = []
            for a in sorted(set(d.insns) | set(d.movement)):
                if a in d.movement:
                    out.append((a, ('mov', tuple(d.movement[a]))))
                else:
                    _, op, args = d.insns[a]
                    out.append((a, (table[op]['name'], tuple(v for t, v in args if t not in ('rel', 'mov')))))
            return out
        try:
            p = tokens(gen4_script.Disasm(self._pearl_files[f], self._pearl_table), self._pearl_table)
        except Exception:
            return {}
        t = tokens(self.disasm(f), self.table)
        sm = difflib.SequenceMatcher(None, [x[1] for x in t], [x[1] for x in p], autojunk=False)
        out = {}
        for i, j, n in sm.get_matching_blocks():
            for k in range(n):
                out[t[i + k][0]] = p[j + k][0]
        return out

    def disasm(self, f):
        if f not in self._dis:
            self._dis[f] = gen4_script.Disasm(self.files[f], self.table)
        return self._dis[f]

    def events(self, zone):
        n = zone['events']
        if n not in self._ev:
            self._ev[n] = json.load(open(os.path.join(PEARL, 'events', f'{n:03d}.json')))
        return self._ev[n]

    def cmd_name(self, op):
        """Platinum's name for an opcode below 0x2C4 (its numbering = pokediamond's there), else pokediamond's."""
        if op < 0x2C4 and op in self.names:
            return self.names[op][0]
        return self.table[op]['name']

    def bank_of(self, f):
        """The text bank a script file's messages come from (its zone's, or its global range's)."""
        for z in self.zones:
            if z['scripts'] == f:
                return z['text_bank']
        for first, ff, bank in SCRIPT_RANGES:
            if ff == f:
                return bank
        return None

    def shared_file_zones(self):
        """{zone id: rank} of the zones on a script file several zones share: Pearl's empty file 368 (one End;
        MAP_EVERYWHERE's), which 114 zones with no scripts of their own use. Each of them gets its own Black 2 script
        and text file (script_file, text_file): a translated file holds the zone's own entries (the proxies of the
        global scripts its people and signs run, its warp continuations, PearlArrive) and its text the lines of
        those, so one file for all 114 would give every one of them the last zone's (2026-10-25, chapter 4a). Ranked
        by zone id over all such zones, installed or not, so the numbers never move."""
        if self._own_zone is None:
            users = collections.Counter(z['scripts'] for z in self.zones)
            shared = sorted(z['id'] for z in self.zones if users[z['scripts']] > 1)
            self._own_zone = {zid: i for i, zid in enumerate(shared)}
        return self._own_zone

    def script_file(self, zone):
        """a/0/5/6 number of a zone's script file: its Pearl file's (FIRST_SCRIPT_FILE + rank), or for a zone on a
        shared file (shared_file_zones) its own, after the last Pearl file's."""
        if version.PLATINUM:        # Pearl's number for a shared zone (Pearl's src/ files are the base), new numbers after them for the new zones
            kept = version.id_map('zone_files')
            top = max(v[0] for v in kept.values()) + 1
            return kept[zone['id']][0] if zone['id'] in kept else top + zone['id'] - version.PEARL_ZONES
        own = self.shared_file_zones().get(zone['id'])
        if own is not None:
            return FIRST_SCRIPT_FILE + len(self.script_file_no) + own
        return self.script_file_no[zone['scripts']]

    def zones_of_script_file(self):
        """{a/0/5/6 number: [Pearl zones installed from it]} (sinnoh_story, pearl_trainers)."""
        out = collections.defaultdict(list)
        for z in self.zones:
            out[self.script_file(z)].append(z)
        return out

    def text_file(self, zone):
        """a/0/0/3 number of a zone's text file. Pearl gives zones with no text of their own Jubilife's bank 18 (72
        script files share it; only Jubilife's file shows its lines), and each translated file appends its common
        scripts' lines to its own text file: so a script file on a bank another file also uses gets its own number
        after the last bank's, unless it is the one that shows the bank's lines (2026-10-25, chapter 3: Ravaged
        Path's Rock Smash lines)."""
        if version.PLATINUM:        # (the same; 1320 on: a/0/0/3's 1236-1310 are other things)
            kept = version.id_map('zone_files')
            return kept[zone['id']][1] if zone['id'] in kept else 1320 + zone['id'] - version.PEARL_ZONES
        if self._own_text is None:
            users = collections.defaultdict(set)
            for z in self.zones:
                users[z['text_bank']].add(z['scripts'])
            extra = []
            for bank, fs in users.items():
                if len(fs) > 1:
                    shows = {f for f in fs if self._shows_lines(f)}
                    extra += sorted(fs - shows) if shows else sorted(fs)[1:]
            top = FIRST_TEXT_FILE + len(self.text_file_no)
            self._own_text = {f: top + i for i, f in enumerate(sorted(extra))}
        own = self.shared_file_zones().get(zone['id'])
        if own is not None:                         # a zone on a shared script file: its own, after those
            return FIRST_TEXT_FILE + len(self.text_file_no) + len(self._own_text) + own
        return self._own_text.get(zone['scripts'], self.text_file_no[zone['text_bank']])

    def _shows_lines(self, f):
        try:
            d = self.disasm(f)
        except Exception:
            return False
        return any(self.cmd_name(op) in ('Message', 'MessageNoSkip', 'MessageInstant')
                   for e, op, args in d.insns.values())

    def zone_entries(self, pearl_map):
        return len(self.disasm(self.zones[pearl_map]['scripts']).entries)

    def warp_continuations(self, pearl_map):
        """[(src file, Warp address, address after it, src bank)] of every Pearl Warp to pearl_map, in a fixed order:
        their scripts in the destination file are its Pearl script count + 1, + 2, ..."""
        if self._warps is None:
            self._warps = collections.defaultdict(list)
            for f, data in enumerate(self.files):
                if not data or f in self.level_files:
                    continue
                try:
                    d = self.disasm(f)
                except Exception:       # (files that are not script code)
                    continue
                for a in sorted(d.insns):
                    end, op, args = d.insns[a]
                    if op == 0xBE and not args[0][0] == 'var':
                        self._warps[args[0][1]].append((f, a, end, self.bank_of(f)))
        return self._warps.get(pearl_map, [])

    def proxy_ids(self):
        """{Pearl global script id: its proxy entry number}, over every zone's people, signs and triggers."""
        if getattr(self, '_proxies', None) is None:
            import pearl_events
            gids = set()
            for z in self.zones:
                gids |= set(pearl_events.proxies(self.events(z), self, z))
            # scripts the project's own events run (not Pearl's people, signs or triggers) come after Pearl's, so
            # adding one never moves the numbers every installed zone file already has (2026-10-26: the Rock Climb
            # walls' ROCKY_WALL; sorted in, it moved Pearl's 10200 and up, and the Marts' clerks ran past their files)
            added = [g for g in pearl_events.ADDED_PROXIES if g in gids]
            base = sorted(gids - set(added))
            self._proxies = {g: FIRST_PROXY + i for i, g in enumerate(base + added)}
        return self._proxies

    def closed(self, zone):
        """The zone's rows of data/pearl_closed_facilities.json (CLOSED)."""
        if getattr(self, '_closed', None) is None:
            self._closed = {k: v for k, v in json.load(open(CLOSED)).items() if k != '_doc'} \
                if os.path.exists(CLOSED) else {}
        return self._closed.get(zone['name'], [])

    def _extra_ids(self, pearl_map, n, skip=0):
        """n script ids after the zone's PearlArrive (and `skip` ids taken before them), past Twinleaf's new-game
        entries and the house's black-out entry, below the proxies."""
        _, k = self.arrival_ids(pearl_map)
        out = []
        while len(out) < skip + n:
            k += 1
            while self.zones[pearl_map]['name'] == NEWGAME_ZONE and k in NEWGAME_ENTRIES or \
                    (self.zones[pearl_map]['name'] == BLACKOUT_HOME_ZONE and k == BLACKOUT_ENTRY):
                k += 1
            assert k < FIRST_PROXY, f'{self.zones[pearl_map]["name"]}: an extra entry {k} reaches the proxies'
            out.append(k)
        return out[skip:]

    def closed_ids(self, pearl_map):
        """Script ids of the zone's closed-place entries (CLOSED), in row order: after its PearlArrive."""
        return self._extra_ids(pearl_map, len(self.closed(self.zones[pearl_map])))

    def elevator_init(self, pearl_map):
        """(script id, lines) of the zone's elevator zone-init entry (ELEVATOR_FLOORS_ABOVE), or None: a floor an
        elevator serves keeps its floors-above in Pearl's VAR_ELEVATOR_FLOORS_ABOVE (0x40CE), an elevator room copies
        it into PL_ELEVATOR_FROM when the player walks in (pl_GetFloorsAbove reads that)."""
        if getattr(self, '_elevators', None) is None:
            self._elevators = {z['id'] for z in self.zones if z['scripts'] in self.files_using('GetFloorsAbove')
                               and self.shared_file_zones().get(z['id']) is None}
        if pearl_map in ELEVATOR_FLOORS_ABOVE:
            lines = [f'    WorkSetConst PVAR_40CE, {ELEVATOR_FLOORS_ABOVE[pearl_map]}  // this floor\'s floors above '
                     f'(an elevator reads it)']
        elif pearl_map in self._elevators:
            lines = ['    WorkSet PL_ELEVATOR_FROM, PVAR_40CE  // the floor the player came from']
        else:
            return None
        k, = self._extra_ids(pearl_map, 1, skip=len(self.closed(self.zones[pearl_map])))
        return k, lines + ['    VMHalt']

    def ramanas_ids(self, pearl_map):
        """{extra name: script id} of Ramanas Park's entries in Pal Park's gate and park (b2tools/ramanas.py
        zone_extras: the slate clerk, the walk-out after a visit, the park attendant), after the zone's closed places,
        elevator entry and item balls; {} elsewhere."""
        import ramanas
        zone = self.zones[pearl_map]
        names = ramanas.zone_extras(zone['name'])
        if not names:
            return {}
        skip = len(self.closed(zone)) + (1 if self.elevator_init(pearl_map) else 0)
        return dict(zip(names, self._extra_ids(pearl_map, len(names), skip=skip)))

    def game_clear_ids(self, pearl_map):
        """(before, after) script ids of the Hall of Fame room's two ending entries (GAME_CLEAR_ZONE), or None: Black 2's
        game clear runs a script of its ending zone before the credits and one after them (event_game_clear.c states
        17 and 18); PearlB2's decomp sends both ending map changes here (patches/game_clear.py reads these ids)."""
        if self.zones[pearl_map]['name'] != GAME_CLEAR_ZONE:
            return None
        zone = self.zones[pearl_map]
        skip = len(self.closed(zone)) + (1 if self.elevator_init(pearl_map) else 0)
        return tuple(self._extra_ids(pearl_map, 2, skip=skip))

    def turnback_doors(self, pearl_map):
        """Script id of a Turnback Cave maze zone's doors map script (b2tools/turnback.py doors_code: Black 2 type 4,
        after each arrival), after the zone's other extra entries; None elsewhere."""
        import turnback
        if pearl_map not in turnback.maze_rooms():
            return None
        zone = self.zones[pearl_map]
        skip = len(self.closed(zone)) + (1 if self.elevator_init(pearl_map) else 0) + \
            len(self.ramanas_ids(pearl_map)) + \
            (2 if self.game_clear_ids(pearl_map) else 0)
        k, = self._extra_ids(pearl_map, 1, skip=skip)
        return k

    def villa_init(self, pearl_map):
        """(script id, lines) of the day's Villa visitor's zone-init entry (VILLA_VISITOR_ZONES, Platinum only), run before
        the zone's own zone init (pearl_events.map_script_table), after the zone's other extra entries; else None."""
        zone = self.zones[pearl_map]
        if zone['name'] not in VILLA_VISITOR_ZONES:
            return None
        skip = len(self.closed(zone)) + (1 if self.elevator_init(pearl_map) else 0) + \
            len(self.ramanas_ids(pearl_map)) + (2 if self.game_clear_ids(pearl_map) else 0) + \
            (1 if self.turnback_doors(pearl_map) else 0)
        k, = self._extra_ids(pearl_map, 1, skip=skip)
        return k, villa_visitor_lines(self, k)

    def files_using(self, cmd):
        """Pearl script files (zone files) that use a command."""
        if not hasattr(self, '_using'):
            self._using = {}
        if cmd not in self._using:
            out = set()
            for f in {z['scripts'] for z in self.zones}:
                try:
                    d = self.disasm(f)
                except Exception:
                    continue
                if any(self.cmd_name(op) == cmd for e, op, args in d.insns.values()):
                    out.add(f)
            self._using[cmd] = out
        return self._using[cmd]

    def arrival_ids(self, pearl_map):
        """{(src file, Warp address): script id} in the destination, and the id of its PearlArrive script."""
        n = self.zone_entries(pearl_map)
        ids, k = {}, n
        for f, a, after, bank in self.warp_continuations(pearl_map):
            k += 1
            while self.zones[pearl_map]['name'] == NEWGAME_ZONE and k in NEWGAME_ENTRIES:
                k += 1
            ids[(f, a)] = k
        k += 1
        while self.zones[pearl_map]['name'] == NEWGAME_ZONE and k in NEWGAME_ENTRIES:
            k += 1
        return ids, k


def platinum_names():
    """{opcode: (name, [param names])} from pokeplatinum's command list and macros (names only)."""
    order = []
    for line in open(os.path.join(PLATINUM, 'include', 'data', 'scripts', 'scrcmd.h')):
        m = re.match(r'ScriptCommand\((SCRCMD_\w+),\s*ScrCmd_(\w+)\)', line)
        if m:
            order.append((m.group(1), m.group(2)))
    params = {}
    src = open(os.path.join(PLATINUM, 'asm', 'macros', 'scrcmd.inc')).read()
    for m in re.finditer(r'\.macro (\w+)([^\n]*)\n\s*\.short (SCRCMD_\w+)', src):
        params.setdefault(m.group(3), (m.group(1), [p.split('=')[0].strip() for p in m.group(2).split(',') if p.strip()]))
    out = {}
    for op, (const, handler) in enumerate(order):
        name, ps = params.get(const, (handler, []))
        if handler.startswith(('Unused', 'Dummy')) or re.match(r'^[0-9A-F]{3}$', handler):
            name = handler
        out[op] = (name, ps)
    return out


# Pearl's script id ranges (pokediamond arm9/asm/unk_02038C78.s LoadScriptsAndMessagesByMapId): (first id, script
# file, text bank); the first entry whose id is <= the script's applies
SCRIPT_RANGES = [(10300, 977, 496), (10200, 373, 332), (10150, 1042, 562), (10100, 1041, 563), (10000, 375, 334),
                 (9950, 376, 335), (9900, 365, 199), (9800, 206, 203), (9700, 387, 378), (9600, 377, 199),
                 (9500, 464, 492), (9400, 391, 381), (9300, 372, 329), (9200, 388, 379), (9100, 0, 9),
                 (9000, 207, 207), (8970, 390, 7), (8950, 463, 486), (8900, 389, 380), (8800, 462, 485),
                 (8000, 374, 333), (7000, 370, 325), (5000, 1040, 199), (3000, 1040, 199), (2800, 378, 350),
                 (2500, 1, 13), (2000, 205, 199)]
PEARL_NEW_GAME_SCRIPT = 9600     # Pearl's new-game flags (file 377 script 1, run by the new-game event)
# After a black-out Black 2 runs a script of the zone you wake up in: script 2 at home (ov012 EventBattleLose_Callback;
# 2001 at a Pokémon Center), which in the translated house is Pearl's own script 2 (Mom's opening scene). Pearl runs
# common script 2020 there (pokediamond blackout.c: 0x7E4 at Mom's spawn, 0x7E5 at a Center). So the home zone's file
# gets that script as entry BLACKOUT_ENTRY, and patches/sinnoh_respawn.py makes Black 2 call it (found in game
# 2026-10-19: after a black-out Mom said "Barry came calling..." again).
BLACKOUT_HOME_ZONE = 'MAP_TWINLEAF_RIVAL_HOUSE_1F'   # the player's house 1F (pokediamond's names are swapped)
BLACKOUT_ENTRY = 40                                 # below the proxies (FIRST_PROXY), above Pearl's and continuations
PEARL_BLACKOUT_HOME_SCRIPT = 2020
# Black 2's game clear (CallGameClear: the Hall of Fame record, the save, the credits, THE END) changes the map twice
# for its Unova epilogue and runs a script there each time (ov012 event_game_clear.c states 15/17 and 16/18). PearlB2's
# decomp sends both to the Hall of Fame room (patches/game_clear.py), whose file gets two entries after its own
# (PearlData.game_clear_ids): before the credits Black 2's ending song starts (Pearl's ending song is not installed;
# Pearl has no field scene there either: the screen stays black), after them nothing (2026-10-26, chapter 8).
GAME_CLEAR_ZONE = 'MAP_POKEMON_LEAGUE_HALL_OF_FAME'


if version.PLATINUM:                # (first id, script file, text bank): Platinum's ranges, in slots (platinum_maps.py)
    import json as _json
    SCRIPT_RANGES = [tuple(r) for r in _json.load(open(os.path.join(ROOT, 'data', 'platinum', 'id_map.json')))['ranges']]


def script_location(sid):
    """(file, text bank, 1-based entry) of a Pearl script id >= 2000."""
    for first, f, bank in SCRIPT_RANGES:
        if sid >= first:
            return f, bank, sid - first + 1
    raise ValueError(sid)


# ---------------------------------------------------------------- Black 2 side tables

MOVEMENT = {int(k, 16): v for k, v in json.load(open(os.path.join(HERE, 'data', 'pearl_movement.json')))['codes'].items()}

# Pearl sounds (pokediamond include/constants/sndseq.h names) -> Black 2 (pokebw2 generated/sound.txt).
# [guess] = chosen by name and use, to audition. Sinnoh's own music comes with the music port (DECISIONS.md).
SOUND = {
    'SEQ_SE_DP_SELECT': 'SEQ_SE_MESSAGE',        # Pearl's click before an NPC speaks = Black 2's talk sound
    'SEQ_SE_DP_DECIDE': 'SEQ_SE_DECIDE1',
    'SEQ_SE_DP_KAIDAN2': 'SEQ_SE_KAIDAN',        # stairs / door
    'SEQ_SE_DP_WALL_HIT2': 'SEQ_SE_WALL_HIT',    # Barry's "Thud!!"
    'SEQ_SE_DP_SAVE': 'SEQ_SE_SAVE',
    'SEQ_SE_DP_PC_LOGIN': 'SEQ_SE_PC_LOGIN', 'SEQ_SE_DP_PC_ON': 'SEQ_SE_PC_ON', 'SEQ_SE_DP_PC_LOGOFF': 'SEQ_SE_PC_LOGOFF',
    'SEQ_SE_DP_DOOR_OPEN': 'SEQ_SE_OPEN1',       # [guess]
    'SEQ_SE_DP_DOOR10': 'SEQ_SE_OPEN1',          # [guess]
    'SEQ_SE_DP_PINPON': 'SEQ_SE_DECIDE2',        # [guess] (a chime)
    'SEQ_SE_DP_UG_020': 'SEQ_SE_DECIDE2',        # [guess] the Hearthome Gym's "Correct! Congratulations!" board (its
                                                 # only use outside the Underground: a chime)
    'SEQ_SE_DP_BUTTON9': 'SEQ_SE_DECIDE1', 'SEQ_SE_DP_BUTTON3': 'SEQ_SE_DECIDE1',   # [guess]
    'SEQ_SE_DP_BOX03': 'SEQ_SE_PC_ON',           # [guess]
    'SEQ_SE_DP_REGI': 'SEQ_SE_SYS_22',           # the cash register (Great Marsh fee): HoennB2's Safari Zone fee sound
    'SEQ_SE_DP_KI_GASYAN': 'SEQ_SE_FLD_94',      # [guess] the Elite Four rooms' doors shutting / opening (Pearl's lift
                                                 # stop clunk too): gimmick 59's own lift-stop sound (chapter 8)
    'SEQ_FANFA4': 'SEQ_ME_ITEM',                 # an item obtained (Platinum's obtain script: FANFA4 items, FANFA3 key)
    'SEQ_FANFA3': 'SEQ_ME_KEYITEM', 'SEQ_FANFA2': 'SEQ_ME_ITEM',
    'SEQ_FANFA1': 'SEQ_ME_POKEGET',              # [guess] a Pokémon received
    'SEQ_GONIN': 'SEQ_ME_KEYITEM',               # [guess]
    'SEQ_ASA': 'SEQ_ME_ASA', 'SEQ_BADGE': 'SEQ_ME_BADGE', 'SEQ_WAZA': 'SEQ_ME_WAZA', 'SEQ_ACCE': 'SEQ_ME_ACCE',
    'SEQ_WASURE': 'SEQ_ME_WASURE', 'SEQ_KINOMI': 'SEQ_ME_KINOMI', 'SEQ_POCKETCH': 'SEQ_ME_KEYITEM',   # [guess]
    'SEQ_TV_END': 'SEQ_ME_QUIZ',                 # [guess] the TV show's closing jingle (the bedroom TV). Every
                                                 # PlayFanfare needs a real jingle: a WaitFanfare after a stub hangs
                                                 # (tested in game 2026-10-18: the opening TV scene never ended)
    'SEQ_THE_RIV': 'SEQ_BGM_E_HUE',              # Barry's theme -> Black 2's rival (Hugh), until Sinnoh's music
    'SEQ_TSURETEKE': 'SEQ_BGM_E_TSURETEKE2',     # "follow me"
    'SEQ_THE_BOY': 'SEQ_BGM_E_BERU', 'SEQ_THE_GIRL': 'SEQ_BGM_E_BERU',   # [guess] Lucas/Dawn -> Bianca's theme
    'SEQ_THE_EVENT01': 'SEQ_BGM_E_DOCTOR',       # [guess] Rowan
    'SEQ_SE_DP_W025': 'SEQ_SE_W026_01',             # [guess] Spear Pillar, the new galaxy (Pearl's Mega Kick; Black 2 has no W025)
    'SEQ_SE_DP_W060C': 'SEQ_SE_W095_01',            # [guess] Spear Pillar, the lake trio's power (Pearl's Psybeam; no W060)
    # Platinum's rooms (2026-11-02, plat-rooms; Pearl never plays these)
    'SEQ_SE_DP_KON': 'SEQ_SE_KON',                  # a knock (Rotom's Room): Black 2 has the same name
    'SEQ_SE_DP_W062': 'SEQ_SE_SHINKA_W062',         # the Secret Key opens Rotom's Room's wall: Black 2's own copy of W062
    'SEQ_SE_DP_DENDOU': 'SEQ_SE_SW_PKWOOD_AUD_01',  # [guess] the grunts cheer Cyrus (Galactic HQ hall): a studio audience
}
_SEQ = None
PEARL_SONGS = ('SEQ_THE_RIV', 'SEQ_THE_BOY', 'SEQ_THE_GIRL', 'SEQ_TSURETEKE', 'SEQ_THE_EVENT01', 'SEQ_THE_EVENT02',
               'SEQ_THE_EVENT03', 'SEQ_SILENCE_DUNGEON', 'SEQ_OPENING2', 'SEQ_FUE', 'SEQ_D_SAFARI', 'SEQ_D_RYAYHY')


def seq_name(v):
    """(Black 2 sound constant or None, Pearl's name) for a Pearl sound id."""
    global _SEQ
    if _SEQ is None:
        _SEQ, base = {}, {'SNDARC_BGM_BASE': 1000, 'SNDARC_SE_BASE': 1500}
        for line in open(os.path.join(ROOT, 'external', 'pokediamond', 'include', 'constants', 'sndseq.h')):
            m = re.match(r'#define (SEQ_\w+)\s+\((?:(SNDARC_\w+) \+ )?(\d+)\)', line)
            if m:
                _SEQ[int(m.group(3)) + (base[m.group(2)] if m.group(2) else 0)] = m.group(1)
    name = _SEQ.get(v)
    return SOUND.get(name), name


# ---------------------------------------------------------------- one output file

class Job:
    """One Black 2 script file (a Pearl zone's), its text, and what the translation needed."""

    def __init__(self, pd, zone, ids):
        import gen4_text
        self.pd, self.zone, self.ids, self.gen4_text = pd, zone, ids, gen4_text
        self.name = zone['name']
        self.events = pd.events(zone)
        self.bank = gen4_text.bank(zone['text_bank'])      # Pearl's lines (Gen 4 markup)
        self.text = [(t, None) for t in self.bank]        # this zone's text file: (Pearl line, variant)
        self.extra = {}                                   # (bank, line, variant) -> line number in this file
        self.stubs = collections.Counter()                # Pearl command -> uses left as stubs
        self.approx = collections.Counter()               # translated approximately
        self.done = collections.Counter()                 # translated
        self.insn_status = {}                             # (Pearl file, address) -> (command, 'done' | 'stub')
        self.notes = []
        self.common = {}                                  # (file, entry) -> subroutine label
        self.common_queue = []
        self.speakers = {}
        if os.path.exists(SPEAKERS):
            self.speakers = {int(k): v for k, v in json.load(open(SPEAKERS)).get(self.name, {}).items()}
        self.buffer_fills = {}                            # BUFFER_FILLS: {line: {buffer: whose name}}
        if os.path.exists(BUFFER_FILLS):
            self.buffer_fills = {int(k): {int(i): w for i, w in v.items()}
                                 for k, v in json.load(open(BUFFER_FILLS)).get(self.name, {}).items()}
        import pearl_events
        self.init_level = pearl_events.map_script_table(pd, zone, ids)[1]   # {script: feature level} of map scripts
        # Pearl global scripts that a map script runs through a proxy entry: (file, entry) -> that feature level, so
        # their subroutine copy translates as map-script code (2026-10-26, chapter 8: the League lobby 2F's field-load
        # script runs global 9000, whose HideObject 255 became an ActorCmdExec: sinnoh_story's level check refused it)
        self.level_commons = {}
        self.pending_pos = {}                             # object -> its SetObjectEventPos for the next AddObject
        # Pearl's own objects by local id; copies of a neighbouring zone's objects (script 0xFFFF) share ids with them
        # and no script addresses them (2026-10-20: Route 201's copy id 5 hid Rowan's RemoveObject 5 flag)
        self.objects = {o['id']: o for o in self.events['object_events'] if o['script'] != pearl_events.COPY_SCRIPT}
        # index in the zone's Black 2 NPC list (pl_SetObjectEventPos): the people pearl_events installs, in Pearl's order
        # (item balls, berry soil and objects without a Black 2 actor are left out, so later indices shift; 2026-10-20)
        self.object_index = {o['id']: i for i, o in enumerate(pearl_events.kept_objects(pd, zone))
                             if o['script'] != pearl_events.COPY_SCRIPT}

    def line_for(self, bank, n, variant=None):
        """Line number in this zone's text file of Pearl bank line n (variant: a ('boy'|'girl', buffers) copy)."""
        if bank == self.zone['text_bank'] and variant is None:
            return n
        key = (bank, n, variant)
        if key not in self.extra:
            src = self.gen4_text.bank(bank)[n]
            self.extra[key] = len(self.text)
            self.text.append((src, variant))
        return self.extra[key]

    def line_text(self, key, text):
        """Line number of a line written here (Pearl markup text; key: what it stands for, kept once)."""
        key = ('text',) + key
        if key not in self.extra:
            self.extra[key] = len(self.text)
            self.text.append((text, None))
        return self.extra[key]

    def values_before_call(self, var, f, entry):
        """Values the zone's own file sets var to (SetVarFromValue) right before calling Pearl common script
        (file f, entry)."""
        d = self.pd.disasm(self.zone['scripts'])
        prev = {e: x for x, (e, op, args) in d.insns.items()}               # end address -> the instruction
        out = set()
        for x, (e, op, args) in d.insns.items():
            if self.pd.cmd_name(op) != 'CallCommonScript' or args[0][1] < 2000 or args[0][1] in NATIVE_COMMON:
                continue
            cf, _, ce = script_location(args[0][1])
            if (cf, ce) != (f, entry):
                continue
            y = x
            for _ in range(8):                      # (the lobby sets 0x8004, then 0x8005, then calls 2047)
                y = prev.get(y)
                if y is None:
                    break
                pe_, pop, pargs = d.insns[y]
                if self.pd.table[pop]['flow'] in ('end', 'jump', 'return'):
                    break
                if self.pd.cmd_name(pop) == 'SetVarFromValue' and pargs[0][1] == var:
                    out.add(pargs[1][1])
                    break
        return out

    def label_common(self, sid, mode='common'):
        """The subroutine label of Pearl global script sid in this file (translated once per mode: 'common' for
        CallCommonScript, 'proxytalk' for a person's talk script run through a proxy entry)."""
        f, bank, entry = script_location(sid)
        key = (f, entry, mode)
        if key not in self.common:
            self.common[key] = f'{"C" if mode == "common" else "T"}{f}_{entry}_S{entry}'
            self.common_queue.append((f, bank, entry, mode))
        return self.common[key]


class FileTr:
    """The translation of a Pearl script file from some starting points.
    mode 'zone': the zone's own file, all its scripts; 'common': one common script as a subroutine;
    'warp': the code after a Warp, as a script of the destination."""

    def __init__(self, job, f, bank, mode='zone', starts=None, prefix=None):
        self.job, self.f, self.bank, self.mode = job, f, bank, mode
        self.d = d = job.pd.disasm(f)
        self.prefix = prefix or f'P{f}'
        if starts is None:
            starts = [(f'{self.prefix}_S{k}', d.entries[k - 1], k) for k in range(1, len(d.entries) + 1)]
        self.starts = starts                                 # [(label, address, entry number or None)]
        self.reach_from = collections.defaultdict(set)      # addr -> entries whose flow reaches it
        self.cp_bufs = collections.defaultdict(set)         # addr -> word buffers that may hold the counterpart name
        self.sign_type = 3
        self.last_battle = 'trainer'
        self.after_starter = False
        self.force_levels = None                 # a zone-init copy of a subroutine (call_label): always level 2
        self.init_copies = {}                    # subroutine address -> its zone-init copy's label
        # objects this file makes follow the player (SetMovementType X, 0x30): Black 2 renames a follower 0xFE
        self.follow_uids = {args[0][1] for a, (e, op, args) in d.insns.items()
                            if job.pd.cmd_name(op) == 'SetMovementType' and args[1][1] == FOLLOW and args[0][1] < 0xF0}
        if version.PLATINUM:                     # (plat-test, 2026-11-08) one made to follow through a var (Amity Square's
            fvars = {args[0][1] for a, (e, op, args) in d.insns.items()   # walking Pokemon: PVAR_8002 = 5): the
                     if job.pd.cmd_name(op) == 'SetMovementType' and args[1][1] == FOLLOW and args[0][1] >= 0x4000}
            self.follow_uids |= {args[1][1] for a, (e, op, args) in d.insns.items()   # var's constant values
                                 if job.pd.cmd_name(op) == 'SetVarFromValue' and args[0][1] in fvars and args[1][1] < 0xF0}
        self.flow()
        # the entries whose flow shows the money window (ShowMoney): their talk balloons and menus take Black 2's places
        # for a money window (money_layout)
        self.money_entries = {k for b, (e, op, args) in d.insns.items() if job.pd.cmd_name(op) == 'ShowMoney'
                              for k in self.reach_from[b]}

    @property
    def zone_file(self):
        return self.mode == 'zone'

    def succ(self, a):
        end, op, args = self.d.insns[a]
        fl = self.job.pd.table[op]['flow']
        out = [t for ty, t in args if ty == 'rel']
        if fl not in ('end', 'jump', 'return') and op != 0xBE:      # (nothing after a Warp runs here: continuation)
            out.append(end)
        return out

    def flow(self):
        d = self.d
        for label, start, k in self.starts:
            todo, seen = [(start, frozenset())], {}
            while todo:
                a, cp = todo.pop()
                if a not in d.insns:
                    continue
                prev = seen.get(a)
                if prev is not None and cp <= prev:
                    continue
                cp = cp | (prev or frozenset())
                seen[a] = cp
                self.reach_from[a].add(k)
                self.cp_bufs[a] |= cp
                end, op, args = d.insns[a]
                name = self.job.pd.cmd_name(op)
                ncp = cp
                if name in BUFFER_CMDS:
                    idx = args[0][1]
                    ncp = (cp | {idx}) if name == 'BufferCounterpartName' else (cp - {idx})
                for t in self.succ(a):
                    todo.append((t, ncp))

    MSG_OPS = {'Message', 'MessageNoSkip', 'MessageInstant', 'MessageVar', 'MessageFromBank', 'MessageFromBankInstant',
               'MessageUnown'}
    CLOSE_OPS = {'CloseMessage', 'CloseMessageWithoutErasing', 'DrawSignpostInstantMessage',
                 'DrawSignpostScrollingMessage'}

    def prints(self, d, start, limit=400):
        """Whether the code reachable from start (a subroutine, up to its returns) shows a line."""
        seen, todo = set(), [start]
        while todo and len(seen) < limit:
            a = todo.pop()
            if a in seen or a not in d.insns:
                continue
            seen.add(a)
            end, op, args = d.insns[a]
            name = self.job.pd.cmd_name(op)
            if name in self.MSG_OPS:
                return True
            if name == 'CallCommonScript' and args[0][1] >= 2000 and args[0][1] not in NATIVE_COMMON:
                f, bank, entry = script_location(args[0][1])
                if self.prints(self.job.pd.disasm(f), self.job.pd.disasm(f).entries[entry - 1], limit - len(seen)):
                    return True
            fl = self.job.pd.table[op]['flow']
            todo += [t for ty, t in args if ty == 'rel']
            if fl not in ('end', 'jump', 'return') and op != 0xBE:
                todo.append(end)
        return len(seen) >= limit

    def speakers_in(self):
        """{address: which message window may be open there}: None (none), (kind, uid), or UNKNOWN; a forward
        dataflow over the code (Pearl has one box; Black 2 has a balloon per person and a plain window, and two at
        once hung the game: Mom's Journal scene, 2026-10-18)."""
        d, state = self.d, {}
        todo = []
        for label, a, k in self.starts:
            st = None if self.mode == 'zone' else UNKNOWN       # (a sub-script's caller may have one open)
            todo.append((a, st))
        while todo:
            a, st = todo.pop()
            if a not in d.insns:
                continue
            if a in state:
                if state[a] == st or state[a] == UNKNOWN:
                    continue
                st = UNKNOWN
            state[a] = st
            end, op, args = d.insns[a]
            name = self.job.pd.cmd_name(op)
            out = st
            if name in self.MSG_OPS:
                n = args[0][1] if name.startswith('Message') and name not in ('MessageVar', 'MessageFromBank',
                                                                               'MessageFromBankInstant') else -1
                out = speaker(self, a, n)
            elif name in self.CLOSE_OPS:
                out = None
            elif name in ('Call', 'CallIf'):
                t = next(t for ty, t in args if ty == 'rel')
                if self.prints(d, t):
                    out = UNKNOWN
            elif name == 'CallCommonScript' and args[0][1] >= 2000 and args[0][1] not in NATIVE_COMMON:
                f, bank, entry = script_location(args[0][1])
                cd = self.job.pd.disasm(f)
                if self.prints(cd, cd.entries[entry - 1]):
                    out = UNKNOWN
            for t in self.succ(a):
                todo.append((t, out))
        return state

    def kind_of(self, k):
        """Entry k's trigger in the zone: 'talk' (an NPC's), 'sign', 'trigger', or 'other'."""
        if self.mode == 'proxytalk':
            return 'talk'
        if not self.zone_file or k is None:
            return self.mode
        ev = self.job.events
        import pearl_events
        sign = pearl_events.is_sign                 # (Pearl's sign objects are Black 2 sign events: no talker)
        # a script a step trigger also runs is no person's talk: Black 2's balloon over the talked-to person
        # (ParentActorMsg) shows nothing when no person was talked to (ov036 scrcmd_msg.c: no parent actor), and
        # Pearl's one box serves both (2026-10-25: Valley Windworks' Mars scene is his talk script and the trigger's)
        shared = any(c['script'] == k for c in ev['coord_events'])
        if not shared and any(o['script'] == k and not o['trainer_type'] and not sign(o) for o in ev['object_events']):
            return 'talk'
        if any(b['script'] == k for b in ev['bg_events']) or any(o['script'] == k and sign(o)
                                                                  for o in ev['object_events']):
            return 'sign'
        if any(c['script'] == k for c in ev['coord_events']):
            return 'trigger'
        return 'other'

    def levels(self, a):
        """Black 2 feature levels the code at a runs at (2 zone init, 1 field load, 0 the rest)."""
        if self.force_levels:
            return self.force_levels
        if self.mode != 'zone':
            return {0}
        return {self.job.init_level.get(k, 0) for k in self.reach_from.get(a, ())} or {0}

    # Commands translated one way in a zone init (level 2: the zone's NPC list, no live actors) and another way
    # elsewhere (live actors): a subroutine with one of them that a zone init and another script both call gets a
    # zone-init copy (2026-10-25, chapter 4b: Veilstone's zone init places the counterpart by the subroutine its
    # Pokedex scene also calls; one copy for both turned the live actor in the zone init, which hangs)
    LEVEL_CMDS = {'AddObject', 'RemoveObject', 'SetObjectEventPos', 'SetObjectEventDir', 'CheckDaycareHasEgg'}

    def call_label(self, a, t):
        """The label a Call / CallIf at a jumps to: t's, or its zone-init copy (LEVEL_CMDS)."""
        if self.mode != 'zone' or self.force_levels or self.levels(a) != {2} or self.levels(t) == {2}:
            return self.label(t)
        seen, todo = set(), [t]
        while todo:                                 # the subroutine, up to its Returns
            x = todo.pop()
            if x in seen or x not in self.d.insns:
                continue
            seen.add(x)
            end, op, args = self.d.insns[x]
            if self.job.pd.cmd_name(op) in self.LEVEL_CMDS:
                self.init_copies.setdefault(t, f'{self.prefix}_Zinit_{t:04X}')
                return self.init_copies[t]
            fl = self.job.pd.table[op]['flow']
            todo += [y for ty, y in args if ty == 'rel']
            if fl not in ('end', 'jump', 'return') and op != 0xBE:
                todo.append(end)
        return self.label(t)

    def app_bufs(self, a):
        """{buffer: Pearl app (a number) or ('var', v)} of the word buffers that hold a Pokétch app's name at a
        (Pearl GetPoketchAppName = BufferPoketchAppName idx, app or var): a forward dataflow like flow()'s, computed
        once, only for files that use the command (2026-10-25, chapter 4a: Route 207's Dowsing Machine line)."""
        if getattr(self, '_app_bufs', None) is None:
            d, pd = self.d, self.job.pd
            self._app_bufs = {}
            if any(pd.cmd_name(op) in NAME_SOURCES for e, op, args in d.insns.values()):
                for label, start, k in self.starts:
                    for x, st in self._app_walk(start, frozenset())[0].items():
                        self._app_bufs[x] = self._app_bufs.get(x, frozenset()) | st
        return {i: v for i, v in self._app_bufs.get(a, ())}

    def const_before(self, a, var, limit=8):
        """The value a SetVarFromValue gives var shortly before a in straight-line code, or None."""
        d, pd = self.d, self.job.pd
        if getattr(self, '_prev', None) is None:
            self._prev = {e: x for x, (e, op, args) in d.insns.items()}
        x = a
        for _ in range(limit):
            x = self._prev.get(x)
            if x is None:
                return None
            e, op, args = d.insns[x]
            name = pd.cmd_name(op)
            if pd.table[op]['flow'] in ('end', 'jump', 'return'):
                return None
            if name == 'SetVarFromValue' and args[0][1] == var:
                return args[1][1]
            if any(ty == 'var' and v == var for ty, v in args):
                return None                         # (something else writes or reads it: not a plain constant)
        return None

    def _app_walk(self, start, st0, depth=0):
        """(states by address, states at the Returns) of app_bufs' dataflow from start; a Call's fall-through
        gets what its subroutine set (Route 207's counterpart names the app a Call buffered)."""
        d, pd = self.d, self.job.pd
        todo, seen, rets = [(start, st0)], {}, set()
        while todo:
            x, st = todo.pop()
            if x not in d.insns or (x in seen and st <= seen[x]):
                continue
            st = st | seen.get(x, frozenset())
            seen[x] = st
            end, op, args = d.insns[x]
            name = pd.cmd_name(op)
            nst = st
            if name in BUFFER_CMDS or name in NAME_SOURCES or (name.startswith('Buffer') and args and
                                                                args[0][0] == 'u8'):
                idx = args[0][1]
                nst = frozenset(b for b in st if b[0] != idx)
                if name in NAME_SOURCES:
                    v = args[1][1]
                    if name == 'BufferValuePaddingDigits':
                        v = f'{v}/{args[3][1]}'       # (a u32 value and its digits, "value/digits": no var)
                    elif v >= 0x4000:               # a var set just before (Route 206's gate: 0x8004 = 96)
                        k = self.const_before(x, v)
                        v = ('var', v) if k is None else k
                    nst |= {(idx, (name, v))}
            if pd.table[op]['flow'] == 'return':
                rets |= st
            if name in ('Call', 'CallIf') and depth < 8:
                t = next(t for ty, t in args if ty == 'rel')
                for y, sst in self._app_walk(t, st, depth + 1)[0].items():
                    if y not in seen or not sst <= seen[y]:
                        todo.append((y, sst))
                nst = st | self._app_walk(t, st, depth + 1)[1]
                todo += [(end, nst)]
                continue
            for t in self.succ(x):
                todo.append((t, nst))
        return seen, rets

    def is_talk(self, a):
        ks = self.reach_from.get(a, set())
        return bool(ks) and all(self.kind_of(k) == 'talk' for k in ks)

    def talks_to_thing(self, a):
        """Whether every object whose talk script reaches a is a thing (THING_GFX), not a person."""
        if not self.zone_file:
            return False
        ks = self.reach_from.get(a, set())
        objs = [o for o in self.job.events['object_events'] if o['script'] in ks]
        return bool(objs) and all(o['graphics_id'] in THING_GFX for o in objs)

    def label(self, a):
        return f'{self.prefix}_{a:04X}'

    def var(self, v):
        """A var-or-value argument."""
        if v > 0xFFFF:                             # (a u32 value: money)
            return str(v)
        if v >= 0x8000:
            return self.job.ids.local(v)
        if v >= 0x4000:
            return self.job.ids.var(v)
        return str(v)

    def flag(self, v):
        return self.job.ids.flag(v)

    def lines(self):
        d, out = self.d, []
        names = collections.defaultdict(list)
        for label, a, k in self.starts:
            names[a].append(label)
        code = sorted(a for a in d.insns if a in self.reach_from)
        targets = {t for a in code for ty, t in d.insns[a][2] if ty == 'rel'}
        movs = sorted({t for a in code for ty, t in d.insns[a][2] if ty == 'mov'})
        prev_end = None
        self.open_speaker = None
        spk = self.speakers_in()
        for a in code:
            end, op, args = d.insns[a]
            if a in names or a in targets or prev_end != a:
                if out:
                    out.append('')
                out += [f'{n}:' for n in names.get(a, [])] + [f'{self.label(a)}:']
                # which message window may be open here (speakers_in): another speaker's line closes it first
                self.open_speaker = spk.get(a, UNKNOWN)
            for x in self.translate(a, end, op, args):
                out.append(x if x.startswith(('//', '.L')) or x.endswith(':') else f'    {x}')
            fl = self.job.pd.table[op]['flow']
            prev_end = None if fl in ('end', 'jump', 'return') or op == 0xBE else end
        for m in movs:
            out += ['', '    .balign 4, 0', f'{self.label(m)}:']
            fix = path_fixes().get((self.f, self.job.pd.pearl_addr(self.f, m)))
            if fix is not None:
                out.append(f'// path fix (data/pearl_path_fixes.json): {fix["why"]}')
            for cmd, n in (fix['moves'] + [(0xFE, 0)] if fix is not None else d.movement[m]):
                if cmd == 0xFE:
                    out.append('    MoveEnd')
                    break
                info = MOVEMENT.get(cmd)
                if info is None or info['b2'] is None:
                    out.append(f'    Move {cmd}, {n}  // Pearl 0x{cmd:02X}: no Black 2 code (same number kept)')
                    self.job.approx[f'movement 0x{cmd:02X}'] += 1
                    continue
                if not info['exact']:
                    self.job.approx[f'movement 0x{cmd:02X} {info["pearl_name"]}'] += 1
                note = '' if info['exact'] else '  // approx.: ' + info['note'][:70]
                out.append(f'    Move {info["b2"]}, {n}  // {info["pearl_name"]}{note}')
        for t, label in self.init_copies.items():  # zone-init copies of subroutines (call_label)
            sub = FileTr(self.job, self.f, self.bank, mode='zone', starts=[(label, t, None)], prefix=f'{self.prefix}Z')
            sub.force_levels = {2}
            out += ['', f'// ---- a zone-init copy of {self.label(t)} (another script calls it outside the zone init)'] \
                + sub.lines()
        return out

    def translate(self, a, end, op, args):
        name = self.job.pd.cmd_name(op)
        h = HANDLERS.get(name)
        if name in TOWER_ONLY_HANDLERS and self.job.zone['name'] not in TOWER_ZONES:
            h = None                                   # (b2tools/tower_script.py: these stay stubs elsewhere)
        vals = [v for ty, v in args]
        patch = script_patches().get((self.f, self.job.pd.pearl_addr(self.f, a)))      # (data/pearl_script_patches.json: one command changed)
        if patch is not None:
            if 'drop' in patch:
                self.job.insn_status[(self.f, a)] = (name, 'done')
                return [f'// Pearl 0x{op:03X} {name} {", ".join(map(str, vals))}: dropped '
                        f'(data/pearl_script_patches.json: {patch["drop"]})']
            assert len(patch['args']) == len(vals), (self.f, hex(a), name, patch)
            vals = [self.job.pd.platinum_addr(self.f, v) if ty in ('rel', 'mov') else v for (ty, _), v in zip(args, patch['args'])]
            args = [(ty, v) for (ty, _), v in zip(args, vals)]
        if h is None:
            self.job.insn_status[(self.f, a)] = (name, 'stub')
            self.job.stubs[name] += 1
            return [f'pl_stub {name}  // Pearl 0x{op:03X} {self.job.pd.table[op]["name"]} {", ".join(map(str, vals))}'
                    f': not translated yet']
        before = sum(self.job.stubs.values())
        r = h(self, a, vals, name)
        if (self.f, self.job.pd.pearl_addr(self.f, a)) in SCENE_AFTER:
            r = r + SCENE_AFTER[(self.f, self.job.pd.pearl_addr(self.f, a))](self)
        if self.money_entries and self.reach_from[a] & self.money_entries:
            r = [money_layout(line) for line in r]     # (a script that shows the money window: money_layout)
        for line in r:                                 # (MONEY_WORD: the last buffer written into word 2)
            if re.match(rf'\s*pl_Buffer\w+ {MONEY_WORD},', line):
                self.money_word_buf = line.split('//')[0].strip()
        if name in ('ShowMoney', 'UpdateMoneyDisplay') and getattr(self, 'money_word_buf', None):
            r = r + [f'{self.money_word_buf}  // again: Black 2\'s money window wrote the money into word {MONEY_WORD}']
        self.job.done[name] += 1
        self.job.insn_status[(self.f, a)] = (name, 'stub' if sum(self.job.stubs.values()) > before else 'done')
        return r


# ---- the money window's layout (v101-test, 2026-11-08). Black 2 puts the money window at the top right (MoneyWinDisp
# 31, 1) and, while it shows, the talk balloon at the bottom (ActorMsg pos 2: Black 2's own balloons go to the top when
# the speaker stands above the player, ov036 ActorMsgWin_CalcWinPosAuto) and a menu under the money window (31, 5):
# black_city_5.s. Pearl's scripts show their menus at the top left with the money at the right, so in Black 2 the
# Game Corner's coin menu and money window lay under the clerk's balloon and the Dept. Store 5F's and the Berry Master's
# menus over their money windows. In a script whose flow shows the money window: talk lines with the balloon at the
# bottom, a menu at row 5 or lower.
def money_layout(line):
    line = re.sub(r'^(\s*)pl_msg_talk (\S)', r'\1pl_msg_talk_low \2', line)
    line = re.sub(r'^(\s*)pl_msg_actor (\S)', r'\1pl_msg_actor_low \2', line)
    return re.sub(r'^(\s*ListMenu_AnchorTopRight 31, )([0-4])(,)', r'\g<1>5\3', line)


# ---- script patches: single Pearl commands changed or dropped (data/pearl_script_patches.json; 2026-10-26: the
# Underground Man's missions that need digging, traps or Secret Bases)
SCRIPT_PATCHES = os.path.join(ROOT, 'data', 'pearl_script_patches.json')
_SCRIPT_PATCHES = None


def windworks_door_opens(tr):
    """The Works Key (the user, 2026-11-01: "the door doesn't open automatically"): after "Ker-chunk! The door to Valley
    Windworks opened!" the door opens by itself and the player walks in, as the door grunt did before (Pearl only moves
    the warp back and leaves the walking to the player, with the door still shut on screen). Then the warp the door
    has, onto the interior's mat."""
    pd = tr.job.pd
    m = pd.by_name['MAP_VALLEY_WINDWORKS_INTERIOR']['id']
    _, arrive = pd.arrival_ids(m)
    return ['pl_LoadDoorAnimation 77, 243, 654  // the door opens by itself',
            'pl_PlayDoorOpenAnimation 77',
            'pl_WaitForAnimation 77',
            'pl_ApplyMovement PL_PLAYER, P210_door_walk',
            'pl_WaitMovement',
            'pl_fade_out_black',
            'pl_WaitFadeScreen',
            'pl_UnloadAnimation 77',
            f'RTReserveScript {arrive}  // PearlArrive: fade in, release',
            f'pl_Warp {pd.b2_zone[m]}, 12, 16, 0  // Pearl map {m} (MAP_VALLEY_WINDWORKS_INTERIOR), its mat',
            'pl_ReleaseAll',
            'pl_End',
            '.balign 4, 0',
            'P210_door_walk:',
            '    Move 12, 1  // WALK_NORMAL_NORTH',
            '    MoveEnd']


# Lines added after one translated command, for a Pearl scene that needs more than Pearl has: {(script file, command
# address): function(tr) -> lines}
SCENE_AFTER = {(210, 0x198): windworks_door_opens}


def script_patches():
    """{(Pearl script file, command address): {'args': [...]} or {'drop': why}}."""
    global _SCRIPT_PATCHES
    if _SCRIPT_PATCHES is None:
        _SCRIPT_PATCHES = {}
        if os.path.exists(SCRIPT_PATCHES):
            for f, cmds in json.load(open(SCRIPT_PATCHES)).items():
                if f.startswith('_'):
                    continue
                for addr, p in cmds.items():
                    if not addr.startswith('_'):
                        _SCRIPT_PATCHES[(int(f), int(addr, 16))] = p
    return _SCRIPT_PATCHES


# ---- path fixes: Pearl movement lists changed where Black 2 places the player differently (data/pearl_path_fixes.json,
# checked by b2tools/scene_check.py; 2026-10-20: Mom walking into / past the player after the stairs)
PATH_FIXES = os.path.join(ROOT, 'data', 'pearl_path_fixes.json')
_PATH_FIXES = None


def path_fixes():
    """{(Pearl script file, movement list address): {'moves': [(code, count)], 'why': str}}."""
    global _PATH_FIXES
    if _PATH_FIXES is None:
        _PATH_FIXES = {}
        if os.path.exists(PATH_FIXES):
            for f, lists in json.load(open(PATH_FIXES)).items():
                if f.startswith('_'):
                    continue
                for addr, fx in lists.items():
                    _PATH_FIXES[(int(f), int(addr, 16))] = dict(moves=[tuple(m) for m in fx['moves']], why=fx['why'])
    return _PATH_FIXES


def movement_steps(pd, f, addr):
    """[(code, count)] of Pearl file f's movement list at addr as installed (its path fix if it has one)."""
    fx = path_fixes().get((f, addr))
    if fx is not None:
        return list(fx['moves'])
    return [(c, n) for c, n in pd.disasm(f).movement.get(addr, []) if c != 0xFE]


OBJECT_LINE_BANKS = {334: None, 199: {67}}   # speaker(): {Pearl text bank: its lines, None = all}
# Pearl graphics of things, not people or Pokémon (pokediamond sprites.h; data/pearl_sprite_map.json): Poké Ball 87, snowball
# 118, air vent 182, book 183, Moss Rock 190, Ice Rock 191, Galactic door 202, wall painting 203, Elite Four door 209
# and the legendary Pokémon met on the map (151-161, 184): Pearl's narration around them, whose object is gone by then
THING_GFX = {87, 118, 182, 183, 190, 191, 202, 203, 209, 184} | set(range(151, 162))
UNKNOWN = ('unknown',)               # FileTr.open_speaker: some window may be open (see lines())

BUFFER_CMDS = {'BufferPlayerName', 'BufferRivalName', 'BufferCounterpartName', 'BufferPartyMonSpecies',
               'BufferItemName', 'BufferPocketName', 'BufferTMHMMoveName', 'BufferMoveName', 'BufferNumber',
               'BufferPartyMonNickname', 'BufferPoketchAppName', 'BufferTrainerClassName', 'BufferSpeciesNameFromVar',
               'BufferPlayerStarterSpeciesName', 'BufferRivalStarterSpeciesName',
               'BufferPlayerCounterpartStarterSpeciesName', 'BufferMapName'}

HANDLERS = {}
# Handlers only the Battle Tower's zones use: other zones' scripts keep these commands as they were
TOWER_ONLY_HANDLERS = {'CheckSaveType', 'OpenSaveInfo', 'CloseSaveInfo', 'GetCurNetID', 'Unk02C9', '1DF', '1E0',
                       'BufferVarPaddingDigits', 'MessageSeenBanlistSpecies'}
TOWER_ZONES = ('MAP_BATTLE_TOWER_LOBBY', 'MAP_BATTLE_TOWER_ELEVATOR', 'MAP_BATTLE_TOWER_CORRIDOR_MULTI',
               'MAP_BATTLE_TOWER_CORRIDOR_WIFI', 'MAP_BATTLE_TOWER_ARENA_MULTI', 'MAP_BATTLE_TOWER_ARENA_WIFI',
               'MAP_BATTLE_TOWER_PARTNER_ROOM', 'MAP_BATTLE_PARK_EXCHANGE_SERVICE_CORNER')


def handler(*names):
    def deco(fn):
        for n in names:
            HANDLERS[n] = fn
        return fn
    return deco


def simple(macro, *argfmt):
    """A handler writing `macro args`, each argument as argfmt says: 'var' (var or value), 'flag', 'n' (as it is)."""
    def fn(tr, a, vals, name):
        parts = [tr.var(v) if f == 'var' else tr.flag(v) if f == 'flag' else str(v) for f, v in zip(argfmt, vals)]
        return [f'{macro} {", ".join(parts)}'.rstrip()]
    return fn


for _pl, _macro, _fmt in [
        ('LockAll', 'pl_LockAll', ()), ('FacePlayer', 'pl_FacePlayer', ()), ('ReleaseAll', 'pl_ReleaseAll', ()),
        ('CompareVarToValue', 'pl_CompareVarToValue', ('var', 'n')),
        ('CompareVarToVar', 'pl_CompareVarToVar', ('var', 'var')),
        ('SetFlag', 'pl_SetFlag', ('flag',)), ('ClearFlag', 'pl_ClearFlag', ('flag',)), ('CheckFlag', 'pl_CheckFlag', ('flag',)),
        ('SetFlagFromVar', 'pl_SetFlagFromVar', ('var',)),
        ('SetVarFromVar', 'pl_SetVarFromVar', ('var', 'var')),
        ('AddVar', 'pl_AddVar', ('var', 'var')), ('SubVar', 'pl_SubVar', ('var', 'var')),
        ('WaitButton', 'pl_WaitButton', ()), ('WaitABPress', 'pl_WaitABPress', ()), ('WaitABPadPress', 'pl_WaitABPadPress', ()),
        ('ShowYesNoMenu', 'pl_ShowYesNoMenu', ('var',)),
        ('WaitMovement', 'pl_WaitMovement', ()), ('WaitFanfare', 'pl_WaitFanfare', ()), ('WaitCry', 'pl_WaitCry', ()),
        ('WaitFadeScreen', 'pl_WaitFadeScreen', ()),
        ('GetPlayerMapPos', 'pl_GetPlayerMapPos', ('var', 'var')), ('GetPlayerDir', 'pl_GetPlayerDir', ('var',)),
        ('GetPlayerGender', 'pl_GetPlayerGender', ('var',)), ('GetRandom', 'pl_GetRandom', ('var', 'var')),
        ('AddItem', 'pl_AddItem', ('var', 'var', 'var')), ('RemoveItem', 'pl_RemoveItem', ('var', 'var', 'var')),
        ('CanFitItem', 'pl_CanFitItem', ('var', 'var', 'var')), ('CheckItem', 'pl_CheckItem', ('var', 'var', 'var')),
        ('GetItemPocket', 'pl_GetItemPocket', ('var', 'var')),
        ('GivePokemon', 'pl_GivePokemon', ('var', 'var', 'var', 'var')),
        ('GetPartyCount', 'pl_GetPartyCount', ('var',)), ('HealParty', 'pl_HealParty', ()),
        ('GiveRunningShoes', 'pl_GiveRunningShoes', ()), ('GivePokedex', 'pl_GivePokedex', ()),
        ('BufferPlayerName', 'pl_BufferPlayerName', ('n',)), ('BufferRivalName', 'pl_BufferRivalName', ('n',)),
        ('BufferItemName', 'pl_BufferItemName', ('n', 'var')), ('BufferPocketName', 'pl_BufferPocketName', ('n', 'var')),
        ('BufferPartyMonSpecies', 'pl_BufferPartyMonSpecies', ('n', 'var')),
        ('BufferPartyMonNickname', 'pl_BufferPartyMonNickname', ('n', 'var')),
        ('BufferMoveName', 'pl_BufferMoveName', ('n', 'var')), ('BufferTMHMMoveName', 'pl_BufferTMHMMoveName', ('n', 'var')),
        ('BufferNumber', 'pl_BufferNumber', ('n', 'var')),
        ('BufferPlayerStarterSpeciesName', 'pl_BufferPlayerStarterSpeciesName', ('n',)),
        ('BufferRivalStarterSpeciesName', 'pl_BufferRivalStarterSpeciesName', ('n',)),
        ('BufferPlayerCounterpartStarterSpeciesName', 'pl_BufferCounterpartStarterSpeciesName', ('n',)),
        ('GetPlayerStarterSpecies', 'pl_GetPlayerStarterSpecies', ('var',)),
]:
    HANDLERS[_pl] = simple(_macro, *_fmt)


ITEM_VARS = (0x8004, 0x8008)     # Pearl's give-item var (common script 2044's) and the item balls' (file 370)
PEARL_TMHM = range(328, 428)     # Pearl's TM01-TM92, HM01-HM08 items


def item_value(value):
    """(Black 2 item, comment) for an item value in a Pearl script: Pearl's TM/HM ids are mapped BY MOVE to the item
    that teaches the same move here (b2tools/tm_audit.py, notes/TMS.md: Black 2's TM of that number teaches another
    move, Pearl's 25 moves Black 2 lacks are TM96-TM120); other ids are Black 2's already. The comment `// Pearl item N`
    marks every TM/HM line for tm_audit.py check."""
    if value not in PEARL_TMHM:
        return value, ''
    import tm_audit
    b2 = tm_audit.pearl_item(value)
    pearl = tm_audit.pearl_label(value - 328)
    return b2, f'  // Pearl item {value} ({pearl}) = {tm_audit.item_name(b2)}'


ITEM_ARG = {'AddItem': 0, 'RemoveItem': 0, 'CanFitItem': 0, 'CheckItem': 0, 'GetItemPocket': 0, 'IsItemTMHM': 0,
            'BufferItemName': 1, 'BufferTMHMMoveName': 1, 'GetItemNamePlural': 1}


def _item_handler(fn, k):
    """A handler of a command with an item argument (ITEM_ARG): an immediate Pearl TM/HM id becomes Black 2's
    (item_value), with its comment on the line."""
    def h(tr, a, vals, name):
        if vals[k] >= 0x4000:                       # a var: the value was mapped where it was set
            return fn(tr, a, vals, name)
        b2, note = item_value(vals[k])
        out = fn(tr, a, [b2 if i == k else v for i, v in enumerate(vals)], name)
        return [out[0] + note] + out[1:] if note else out
    return h


@handler('SetVarFromValue')
def h_setvar(tr, a, vals, name):
    var, value = vals
    if var in ITEM_VARS:                        # an item (every value Pearl's scripts put there is one: tm_audit)
        b2, note = item_value(value)
        if note:
            return [f'pl_SetVarFromValue {tr.var(var)}, {b2}{note}']
    if 0x4020 <= var < 0x4030:                  # a dynamic sprite: Black 2 reads an object code from it
        import pearl_events
        code = pearl_events.sprite_code(value)
        if code is None:
            tr.job.stubs[f'SetVarFromValue (dynamic sprite {value}: no Black 2 code)'] += 1
            code = 0
        return [f'pl_SetVarFromValue {tr.var(var)}, {code}  // dynamic sprite: Pearl graphics {value} -> Black 2 code']
    return [f'pl_SetVarFromValue {tr.var(var)}, {value}']


@handler('End')
def h_end(tr, a, vals, name):
    return ['VMReturn  // End: the sub-script ends'] if tr.mode in ('common', 'proxytalk') else ['pl_End']


@handler('ReturnCommonScript')
def h_return_common(tr, a, vals, name):
    return ['pl_ReturnCommonScript']


@handler('WaitTime')
def h_wait(tr, a, vals, name):
    return [f'pl_WaitTime {vals[0]}, {tr.var(vals[1])}']


@handler('GoTo')
def h_goto(tr, a, vals, name):
    return [f'pl_GoTo {tr.label(vals[0])}']


@handler('GoToIf')
def h_gotoif(tr, a, vals, name):
    return [f'pl_GoToIf {vals[0]}, {tr.label(vals[1])}']


@handler('Call')
def h_call(tr, a, vals, name):
    if tr.prints(tr.d, vals[0]):
        tr.open_speaker = UNKNOWN              # (the subroutine shows a line)
    return [f'pl_Call {tr.call_label(a, vals[0])}']


@handler('CallIf')
def h_callif(tr, a, vals, name):
    if tr.prints(tr.d, vals[1]):
        tr.open_speaker = UNKNOWN
    return [f'pl_CallIf {vals[0]}, {tr.call_label(a, vals[1])}']


@handler('CloseMessage', 'CloseMessageWithoutErasing')
def h_close(tr, a, vals, name):
    tr.open_speaker = None
    return [f'pl_{name}']


@handler('Return')
def h_return(tr, a, vals, name):
    return ['pl_Return']


@handler('CheckFlagFromVar')
def h_cfv(tr, a, vals, name):
    return [f'pl_CheckFlagFromVar {tr.var(vals[0])}']


def trainer(tr, v):
    """A trainer argument: a Pearl trainer id (its Black 2 id's name), 0 = none, or a var."""
    if v == 0:
        return '0'
    return tr.job.ids.trainer(v) if v < 0x4000 else tr.var(v)


@handler('CheckTrainerFlag', 'SetTrainerFlag', 'ClearTrainerFlag')
def h_trainer_flag(tr, a, vals, name):
    tid = vals[0]
    return [f'pl_{name} {tr.job.ids.trainer(tid) if tid < 0x4000 else tr.var(tid)}']


# ---- messages
def speaker(tr, a, line):
    """('talk' | 'actor' | 'sys', uid) of a Message."""
    if tr.zone_file and line in tr.job.speakers:
        who = tr.job.speakers[line]
        if who != 'sys' and who not in tr.job.object_index and version.PLATINUM:
            # (a person the zone doesn't install yet, as Platinum's Looker until his sprite is mapped: Black 2's ActorMsg
            # skips the line for a missing actor, so the plain window shows it, with Platinum's "Looker:" in front)
            tr.job.approx['a speaker not installed yet (data/platinum/pearl_speakers.json): the plain window'] += 1
            return ('sys', None)
        return ('sys', None) if who == 'sys' else ('actor', who)   # 'sys': a narration line (the plain window)
    if not tr.is_talk(a):
        return ('sys', None)
    # Pearl has one window, no balloons: Black 2's balloon is for people. The field-object lines of Pearl's common
    # banks (rocks, trees, boulders, water, walls: bank 334; the vents: bank 199 line 67) and a talk script of a thing
    # (THING_GFX) use the plain window (2026-11-01, the user: the "big boulder" line had a tail)
    if tr.bank in OBJECT_LINE_BANKS and (OBJECT_LINE_BANKS[tr.bank] is None or line in OBJECT_LINE_BANKS[tr.bank]):
        return ('sys', None)
    if tr.talks_to_thing(a):
        return ('sys', None)
    return ('talk', None)


def switch_window(tr, kind, uid):
    """[MsgWinCloseAll] when another window may be open (FileTr.speakers_in), and the window this line opens."""
    out = []
    if tr.open_speaker not in (None, (kind, uid)):
        out.append('MsgWinCloseAll  // another speaker: close the first window')
    tr.open_speaker = (kind, uid)
    return out


@handler('Message', 'MessageNoSkip', 'MessageInstant')
def h_message(tr, a, vals, name):
    n = vals[0]
    out = [(f'pl_BufferItemName {i}, {item_value(int(who[5:]))[0]}' if who.startswith('item:') else f'{FILL_MACROS[who]} {i}')
           + '  // a buffer Gen 4 filled earlier (BUFFER_FILLS)'
           for i, who in (tr.job.buffer_fills.get(n, {}) if tr.zone_file else {}).items()]
    kind, uid = speaker(tr, a, n)
    src = tr.job.gen4_text.bank(tr.bank)[n]
    cp = tuple(sorted(i for i in tr.cp_bufs.get(a, set()) if i in tr.job.gen4_text.buffers(src)))
    out += switch_window(tr, kind, uid)
    apps = {i: v for i, v in tr.app_bufs(a).items() if i in tr.job.gen4_text.buffers(src)}
    if apps and not cp:                                     # the app's name written into the line (h_app_message)
        return out + h_app_message(tr, a, n, src, apps, kind, uid)
    if cp:
        boy, girl = (tr.job.line_for(tr.bank, n, (g, cp)) for g in ('boy', 'girl'))
        tail = f'  // Pearl line {n}, naming the counterpart: Dawn (boy) / Lucas (girl)'
        if kind == 'actor':
            return out + [f'pl_msg_actor_gendered {boy}, {girl}, {uid}{tail}']
        return out + [f'pl_msg_{kind}_gendered {boy}, {girl}{tail}']
    m = tr.job.line_for(tr.bank, n)
    note = '' if m == n and tr.zone_file else f'  // Pearl bank {tr.bank} line {n}'
    return out + [(f'pl_msg_actor {m}, {uid}' if kind == 'actor' else f'pl_msg_{kind} {m}') + note]


def message_var_values(tr, a, var):
    """The values SetVarFromValue gives var on every path into a (backwards over the script's own flow, at most 64
    steps a path), or None when a path reaches a without one or a call/other write could change it."""
    d, pd = tr.d, tr.job.pd
    preds = {}
    for x in d.insns:
        for t in tr.succ(x):
            preds.setdefault(t, []).append(x)
    out, seen, todo = set(), set(), [(p, 0) for p in preds.get(a, [])]
    if not todo:
        return None
    while todo:
        x, depth = todo.pop()
        if x in seen:
            continue
        seen.add(x)
        e, op, args = d.insns[x]
        n = pd.cmd_name(op)
        if n == 'SetVarFromValue' and args[0][1] == var:
            out.add(args[1][1])
            continue
        if depth >= 64 or n in ('Call', 'CallIf', 'CallCommonScript') or \
                (not n.startswith('Compare') and any(ty == 'var' and v == var for ty, v in args)):
            return None                                       # (anything else naming var may write it)
        if x not in preds:
            return None                                       # the script's start: nothing set var on this path
        todo += [(p, depth + 1) for p in preds[x]]
    return out


@handler('MessageUnown')
def h_message_unown(tr, a, vals, name):
    """Pearl's MessageUnown n (0x26D): line n of the zone's bank in the Unown alphabet (pokediamond ScrCmd_MessageUnown:
    the plain box with font 3), the Solaceon Ruins' wall writings, among them the maze's way ("TOP RIGHT, LOWER
    LEFT, ..."). Black 2 has no Unown font: the line in Latin letters in the same window (2026-10-25, chapter 4b)."""
    n = vals[0]
    tr.job.approx['MessageUnown (the line in Latin letters: Black 2 has no Unown font)'] += 1
    kind, uid = speaker(tr, a, n)
    m = tr.job.line_for(tr.bank, n)
    return switch_window(tr, kind, uid) + [(f'pl_msg_actor {m}, {uid}' if kind == 'actor' else f'pl_msg_{kind} {m}')
                                           + f'  // MessageUnown {n}']


@handler('MessageVar')
def h_message_var(tr, a, vals, name):
    # Pearl's line number in a var: a line of the script's own bank, which in Black 2 sits at another number in the
    # zone's text (line_for). When the script sets the var to constants on every way in (the Pokémon Center nurse,
    # Pearl common script 2002: 120 "Good morning", 121 "Hello", 0 "Good evening" by the time of day; 2026-10-25, the
    # user saw an empty window at 21:26), the message is a chain over those lines; else the var as the zone's own line.
    kind, _ = speaker(tr, a, -1)
    kind = 'talk' if kind == 'talk' else 'sys'
    out = switch_window(tr, kind, None)
    values = message_var_values(tr, a, vals[0])
    bank = tr.job.gen4_text.bank(tr.bank)
    if not values or any(v >= len(bank) for v in values):
        tr.job.approx['MessageVar (line number from a var: the zone file\'s own lines only)'] += 1
        return out + [f'pl_msg_{kind} {tr.var(vals[0])}']
    values = sorted(values)
    v_ = tr.var(vals[0])
    for v in values[:-1]:
        out += [f'WorkCmpConst {v_}, {v}', f'VMJumpIf CMP_NE, .Lmv{a:x}_{v}',
                f'pl_msg_{kind} {tr.job.line_for(tr.bank, v)}  // Pearl bank {tr.bank} line {v}',
                f'VMJump .Lmv{a:x}_end', f'.Lmv{a:x}_{v}:']
    return out + [f'pl_msg_{kind} {tr.job.line_for(tr.bank, values[-1])}  // Pearl bank {tr.bank} line {values[-1]}',
                  f'.Lmv{a:x}_end:']


@handler('BufferCounterpartName')
def h_counterpart(tr, a, vals, name):
    return [f'// BufferCounterpartName {vals[0]}: the lines naming Dawn/Lucas come as a boy and a girl copy']


# ---- Pokétch app names (Pearl GetPoketchAppName, pokediamond BufferPoketchAppName: bank 406). Black 2 has no
# word-buffer command that reads a free text line (the Pokétch's commands: h_poketch below), so a
# line naming an app gets the name written in: one copy per app (Pearl's caps names in Black 2's case, as species).
# The app is a constant at Route 207, the Berry Master's house and Pal Park; in common script 2009 ("obtained the
# Pokétch app ...") it is var 0x8004, which every caller sets the line before: the line becomes a chain over the
# values this zone's callers set (FileTr.app_bufs, Job.values_before_call; 2026-10-25, chapter 4a)
# Names Black 2 has no word for: Pearl's command -> (its text bank (pokediamond message_format.c), Pearl's capitals in
# Black 2's case): Pokétch apps (BufferPoketchAppName), Contest Accessories (GetFashionName, with an article:
# GetFashionNameWithArticle; 2026-10-25, chapter 4a: Keira's "Obtained the Glitter Powder!" in the Contest Hall).
NAME_SOURCES = {'BufferPoketchAppName': (406, True), 'BufferAccessoryName': (338, False),
                'GetFashionNameWithArticle': (339, False),
                # Platinum's (2026-11-02, the dialogue step): a Trainer's name by its id (bank 559: the Pokémon Mansion's
                # maid names her challenger; Black 2 has no word command for a Trainer's name), and a number Black 2's
                # WordSetNumber can't hold (u16: the Villa's prices go to 220,000), written in (bank None: the number)
                'BufferTrainerName': (559, False), 'BufferValuePaddingDigits': (None, False)}
ACCESSORY_NAMES = {'BufferAccessoryName': 'pl_BufferAccessoryWord', 'GetFashionNameWithArticle': 'pl_BufferAccessoryArticle'}
NAME_WHAT = {'BufferPoketchAppName': 'the app', 'BufferAccessoryName': 'the Accessory',
             'GetFashionNameWithArticle': 'the Accessory', 'BufferTrainerName': 'the Trainer',
             'BufferValuePaddingDigits': 'the number'}
WRITTEN_IN_MENUS = ('BufferTrainerName', 'BufferValuePaddingDigits')   # names a menu entry gets written in (h_menu_add)


def source_name(cmd, k):
    import gen4_text
    bank, recase = NAME_SOURCES[cmd]
    if bank is None:                    # BufferValuePaddingDigits value, padding, digits: the number, right-aligned to its
        v, digits = map(int, str(k).split('/')) if '/' in str(k) else (int(k), 0)   # digits with spaces of a digit's width
        font = b2font.load(0)
        pad = max(0, digits - len(str(v))) * font.width('0')
        return ' ' * round(pad / font.width(' ')) + str(v)
    nm = gen4_text.bank(bank)[k].replace('{TRNAME}', '')     # (bank 559's names are stored compressed)
    if not recase:
        return nm
    return ' '.join('-'.join(w[:1] + w[1:].lower() for w in word.split('-')) for word in nm.split(' '))


def poketch_app_name(app):
    return source_name('BufferPoketchAppName', app)


@handler('BufferAccessoryName', 'GetFashionNameWithArticle')
def h_accessory_name(tr, a, vals, name):
    # (Super Contests, 2026-11-01): a real word now, at run time, for the lines to take: h_app_message's {0102:n}
    return [f'{ACCESSORY_NAMES[name]} {vals[0]}, {tr.var(vals[1]) if vals[1] >= 0x4000 else vals[1]}  // Pearl {name}']


@handler('BufferPoketchAppName', 'BufferTrainerName', 'BufferValuePaddingDigits')
def h_source_name(tr, a, vals, name):
    v = vals[1] if name == 'BufferValuePaddingDigits' or vals[1] < 0x4000 else tr.var(vals[1])   # (a u32 value: no var)
    return [f'// {name} {vals[0]}, {v}: the lines naming '
            f'{NAME_WHAT[name]} have its name written in (Black 2 has no word for it: NAME_SOURCES)']


def h_app_message(tr, a, n, src, apps, kind, uid):
    """A Message whose buffers hold a name Black 2 has no word for (FileTr.app_bufs, NAME_SOURCES): a copy of the
    line per name."""
    # Accessories are words at run time: their buffers keep a plain word tag (Black 2 prints any word for it)
    words = {i for i, (c, v) in apps.items() if c in ACCESSORY_NAMES}
    apps = {i: x for i, x in apps.items() if i not in words}
    src = tr.job.gen4_text._STRVAR.sub(lambda m: '{STRVAR_1 1, %d, 0}' % int(m.group(2)) if int(m.group(2)) in words else m.group(0), src)

    def line(binding):
        text = tr.job.gen4_text._STRVAR.sub(lambda m: source_name(*binding[int(m.group(2))])
                                            if int(m.group(2)) in binding else m.group(0), src)
        return tr.job.line_text((tr.bank, n, tuple(sorted(binding.items()))), text)

    def msg(m, note):
        return (f'pl_msg_actor {m}, {uid}' if kind == 'actor' else f'pl_msg_{kind} {m}') + f'  // {note}'
    fixed = {i: (c, v) for i, (c, v) in apps.items() if not isinstance(v, tuple)}
    var = [(i, c, v[1]) for i, (c, v) in apps.items() if isinstance(v, tuple)]
    if not var and not fixed:
        return [msg(line({}), f'Pearl bank {tr.bank} line {n}, an Accessory by word')]
    if not var:
        return [msg(line(fixed), f'Pearl bank {tr.bank} line {n}, naming '
                                 f'{", ".join(source_name(c, v) for c, v in fixed.values())}')]
    (idx, cmd, v), = var[:1]
    entry = tr.starts[0][2] if tr.mode == 'common' else None
    values = sorted(tr.job.values_before_call(v, tr.f, entry)) if entry else []
    plain = tr.job.line_for(tr.bank, n)
    if not values:
        tr.job.approx[f'{cmd} (from a var no caller sets: the name is not written)'] += 1
        return [msg(plain, f'Pearl bank {tr.bank} line {n} ({NAME_WHAT[cmd]} from {tr.var(v)}: not known here)')]
    done = f'{tr.prefix}_{a:04X}_AppDone'
    out = []
    for k in values:
        out += [f'pl_CompareVarToValue {tr.var(v)}, {k}', f'pl_GoToIf 1, {tr.prefix}_{a:04X}_App{k}']
    out += [msg(plain, f'Pearl bank {tr.bank} line {n}: another one (no caller here sets it)'), f'pl_GoTo {done}']
    for k in values:
        out += [f'{tr.prefix}_{a:04X}_App{k}:', msg(line({**fixed, idx: (cmd, k)}), f'naming {source_name(cmd, k)}'),
                f'pl_GoTo {done}']
    return out + [f'{done}:']


SIGN_TYPE = {0: 1, 1: 3, 2: 2, 3: 0}     # Pearl map/arrow/landmark/scrolling -> Black 2's sign windows (1, 3, 2, 0)


@handler('DrawSignpostInstantMessage')
def h_sign(tr, a, vals, name):
    n, ptype = vals[0], vals[1]
    tr.open_speaker = None                     # (pl_sign closes its window)
    return [f'pl_sign {tr.job.line_for(tr.bank, n)}, {SIGN_TYPE.get(ptype, 2)}  // Pearl sign type {ptype}']


@handler('DrawSignpostTextBox')
def h_sign_box(tr, a, vals, name):
    tr.sign_type = vals[0]
    return [f'// DrawSignpostTextBox type {vals[0]} (the window opens with the next sign message)']


@handler('DrawSignpostScrollingMessage')
def h_sign_scroll(tr, a, vals, name):
    tr.open_speaker = None
    return [f'pl_sign {tr.job.line_for(tr.bank, vals[0])}, {SIGN_TYPE.get(tr.sign_type, 0)}  // Pearl sign type '
            f'{tr.sign_type}']


@handler('SetSignpostCommand', 'WaitForSignpostDone')
def h_sign_rest(tr, a, vals, name):
    return [f'// {name}: done by pl_sign']


@handler('GetSignpostInput')
def h_sign_input(tr, a, vals, name):
    return [f'WorkSetConst {tr.var(vals[0])}, 0  // GetSignpostInput: Black 2\'s sign closes on A/B']


# ---- common scripts
NATIVE_COMMON = {
    2000: ['// CallCommonScript 2000 (Pearl closes the sign; X opens the menu): done by pl_sign'],
    # Pearl's Mart greeting: Black 2's Mart menu (global 10110, its text here a/0/0/3 1302: b2tools/pearl_items.py) says
    # Pearl's line with the menu open
    2019: ['// CallCommonScript 2019 (Pearl\'s Mart greeting): Black 2\'s Mart menu says it'],
}


@handler('CallCommonScript')
def h_common(tr, a, vals, name):
    sid = vals[0]
    if sid in NATIVE_COMMON:
        return NATIVE_COMMON[sid]
    if sid < 2000:
        tr.job.stubs['CallCommonScript (a zone script)'] += 1
        return [f'pl_stub CallCommonScript  // script {sid} of the zone: not a common script']
    f, bank, entry = script_location(sid)
    cd = tr.job.pd.disasm(f)
    if tr.prints(cd, cd.entries[entry - 1]):
        tr.open_speaker = UNKNOWN              # (the common script shows lines in its own window)
    return [f'VMCall {tr.job.label_common(sid)}  // CallCommonScript {sid} (Pearl file {f} script {entry})']


# ---- objects
def actor(tr, v):
    """Black 2 actor of a Pearl object id: 0xFF the player; 0xF2 (the object that follows) and 0xFE (its id after
    EventStopFollowing) = Black 2's follower 0xFE (pair_sys.c FOLLOWER_ACTOR_ID)."""
    if v == 0xFF:
        return 'PL_PLAYER'
    if v in (0xF2, 0xFE):
        return 'PL_FOLLOWER'
    return tr.var(v)


@handler('AddObject')
def h_add(tr, a, vals, name):
    if tr.levels(a) == {2}:                    # zone init: no actors yet; the object appears by its flag
        return [f'// AddObject {vals[0]} in the zone init: it appears by its flag (ActorAdd is not allowed there)']
    o = tr.job.objects.get(vals[0]) if tr.mode != 'common' else None
    import pearl_events
    if o is not None and pearl_events.object_skipped(o, tr.job.zone) is not None:
        # (2026-10-26, chapter 8) a Pearl object with no Black 2 actor (the Elite Four rooms' doors) is not in the
        # zone's NPC list, and Black 2's ActorAdd of a uid with no entity returns an unset pointer it then writes
        # through (ov012 SpawnZoneNPCByUID's BUG): nothing
        tr.job.approx['AddObject (an object with no Black 2 actor: nothing)'] += 1
        return [f'// AddObject {vals[0]}: not installed ({pearl_events.object_skipped(o, tr.job.zone)}): nothing']
    slot = obj_slot(tr, vals[0]) if o is not None else None
    if slot is not None:                       # placed by a SetObjectEventPos of this script (if one ran)
        return [f'pl_AddObjectAt {vals[0]}, {slot}, {o["initial_dir"]}  // at its SetObjectEventPos']
    out = [f'pl_AddObject {tr.var(vals[0])}']
    pos = tr.job.pending_pos.get(vals[0])
    if pos:
        out.append(f'pl_SetPosition {vals[0]}, {pos[0]}, {pos[2]}, {pos[1]}, {pos[3]}  // its SetObjectEventPos')
    return out


ITEM_BALL_FILE = 370             # Pearl's item-ball scripts 7000+n (SCRIPT_RANGES): entry n+1 sets the item, then 256
LAST_TALKED = 0x800D             # Pearl's VAR_LAST_TALKED (Black 2's 0x8011, pearl.h PVAR_800D)


def item_ball_item(pd, sid):
    """The Pearl item an item-ball script (7000+n) gives: its SetVar 0x8008 (pokediamond scr_seq 370)."""
    f, bank, entry = script_location(sid)
    assert f == ITEM_BALL_FILE, sid
    d = pd.disasm(f)
    a = d.entries[entry - 1]
    for _ in range(3):
        end, op, args = d.insns[a]
        if pd.cmd_name(op) == 'SetVarFromValue' and args[0][1] == 0x8008:
            return args[1][1]
        a = end
    raise ValueError(f'item-ball script {sid}: no item')


@handler('IsItemTMHM')
def h_item_tmhm(tr, a, vals, name):
    """Pearl ItemIdIsTMOrHM item, result (0x7F; pokediamond scrcmd_items.c) = Black 2's ItemIsTMHM (FieldCommand 186,
    the same order): Pearl's item ids up to 467 are Black 2's (2026-10-25, chapter 4b: the item-ball script's TM/HM
    line)."""
    return [f'ItemIsTMHM {tr.var(vals[0])}, {tr.var(vals[1])}  // ItemIdIsTMOrHM']


@handler('TrySetUnusedCollectedOrbFlag')
def h_orb_flag(tr, a, vals, name):
    """Pearl 0x2A2 (pokediamond ScrCmd_Unk02A2): for the Adamant / Lustrous Orb (items 135, 136) a save record of
    Pearl's (sub_02025C30) that no script reads; nothing in Black 2."""
    return [f'// Unk02A2 {tr.var(vals[0])}: Pearl\'s orb record (items 135/136), read by no script: nothing in Black 2']


@handler('RemoveObject')
def h_remove(tr, a, vals, name):
    if tr.f == ITEM_BALL_FILE and vals[0] == LAST_TALKED:
        # Pearl's item-ball script removes the talked-to ball and its RemoveEvent sets the ball's flag: Black 2's
        # ActorDelete does not, so the ball's own flag (pearl_events.item_ball_flag) is
        # set as Black 2's item script does it (2026-10-25, chapter 4b)
        return ['pl_RemoveTalkedObject  // RemoveEvent VAR_LAST_TALKED: the ball, and its flag']
    o = tr.job.objects.get(vals[0]) if tr.mode != 'common' else None
    flag = tr.flag(o['hidden_flag']) if o and o['hidden_flag'] else '0'
    if tr.levels(a) == {2}:
        return [f'pl_SetFlag {flag}  // RemoveObject {vals[0]} in the zone init: its flag (ActorDelete is not allowed '
                f'there)'] if flag != '0' else [f'// RemoveObject {vals[0]} in the zone init (no flag)']
    if vals[0] in tr.follow_uids or vals[0] in (0xF2, 0xFE):
        return [f'pl_follow_leave', f'pl_RemoveObject {actor(tr, vals[0])}, {flag}']
    return [f'pl_RemoveObject {tr.var(vals[0])}, {flag}']


def ev_object(tr, uid, what):
    if tr.mode == 'common' or uid not in tr.job.objects:
        tr.job.stubs[f'{what} (object not in the zone)'] += 1
        return None, None
    if uid not in tr.job.object_index:
        tr.job.stubs[f'{what} (an object Black 2 does not install: item ball, berry soil, no actor)'] += 1
        return None, None
    return tr.job.object_index[uid], tr.job.objects[uid]


_HEIGHTS = None


def heights():
    """The converted maps' tile heights (pearl_events.Heights) for grid_y and cam_point: the last build's (work/world);
    (plat-ch2, 2026-11-07) Platinum's own converted heights (platinum_events --heights) in a Platinum run."""
    global _HEIGHTS
    if _HEIGHTS is None:
        import pearl_events
        if version.PLATINUM:
            import platinum_events
            _HEIGHTS = platinum_events.version_heights(pearl_events)
        else:
            _HEIGHTS = pearl_events.Heights()
    return _HEIGHTS


def grid_y(tr, x, z, pearl_y, own=None):
    """Black 2's height step (16 units) of tile (x, z) of this zone's converted map, for a script that places a person.
    Pearl's own y counts Pearl's levels (Jubilife's ground is 1 there, 2 in the converted map): a person placed with it
    stood a level below the player, so Black 2 neither drew nor let anyone talk to them (the Pokétch president after
    the third clown, found in game 2026-10-19). Pearl's y is kept only when the tile is a variable or has no height.
    (plat-ch2, 2026-11-07) Platinum: the heights are Platinum's converted ones (platinum_events --heights, not the last
    Pearl build's work/world), and a tile in a var takes the ground of the person's own tile (own: its event tile):
    Platinum's Looker at (179, the player's z) in Jubilife was a level under the ground, so were Route 207's and
    Solaceon's Barry."""
    if not (isinstance(x, int) and isinstance(z, int)) or x >= 0x4000 or z >= 0x4000:
        if version.PLATINUM and own is not None:                # (plat-ch2)
            h = heights().at(tr.job.zone, *own)
            return pearl_y if h is None else h // 16
        return pearl_y
    h = heights().at(tr.job.zone, x, z)
    return pearl_y if h is None else h // 16


def same_block_before(tr, a, cmd, uid, limit=8):
    """The values of the last `cmd` on object uid earlier in a's basic block (no label, entry or jump in between), or
    None. Black 2's zone-init command for a person (ObjInitNPCGPos) sets tile and direction at once, Pearl's
    SetObjectEventPos and SetObjectEventDir one each: a pair in one block becomes one place (2026-10-20: the Dir half
    re-sent Mom's original tile and undid her move before the Running Shoes scene, so she walked off the room)."""
    d = tr.d
    if getattr(tr, '_blocks', None) is None:
        ends = {e: s for s, (e, op, args) in d.insns.items()}
        targets = {t for s, (e, op, args) in d.insns.items() for ty, t in args if ty == 'rel'}
        tr._blocks = ends, targets | {s for _, s, _ in tr.starts}
    ends, targets = tr._blocks
    for _ in range(limit):
        p = None if a in targets else ends.get(a)
        if p is None:
            return None
        e, op, args = d.insns[p]
        if tr.job.pd.table[op]['flow'] in ('end', 'jump', 'return'):
            return None
        if tr.job.pd.cmd_name(op) == cmd and args[0][1] == uid:
            return [v for ty, v in args]
        a = p
    return None


@handler('SetObjectEventPos')
def h_setobjpos(tr, a, vals, name):
    uid, x, z = vals
    i, o = ev_object(tr, uid, name)
    if o is None:
        return [f'pl_stub SetObjectEventPos  // object {uid} is not in this zone']
    y = grid_y(tr, x, z, o['y'], own=(o['x'], o['z']))
    if tr.levels(a) == {2}:
        turned = same_block_before(tr, a, 'SetObjectEventDir', uid)     # (a Dir just before: keep it)
        d = tr.var(turned[1]) if turned else o['initial_dir']
        return [f'pl_SetObjectEventPos {i}, {tr.var(x)}, {tr.var(z)}, {d}, {y}  // object {uid}']
    # outside the zone init Black 2 cannot change the zone's NPC list (ObjInitNPCGPos: level 2 only): the actor is
    # moved now if it is there, and when the script adds it
    slot = obj_slot(tr, uid)
    if slot is not None:                       # and AddObject puts it there (pl_AddObjectAt), in this script's run
        return [f'pl_SetObjectEventPosLater {slot}, {uid}, {tr.var(x)}, {y}, {tr.var(z)}, {o["initial_dir"]}  '
                f'// SetObjectEventPos {uid} (the live actor; and where AddObject puts it)']
    tr.job.pending_pos[uid] = (tr.var(x), tr.var(z), y, o['initial_dir'])
    return [f'pl_SetPosition {uid}, {tr.var(x)}, {y}, {tr.var(z)}, {o["initial_dir"]}  // SetObjectEventPos {uid} '
            f'(the live actor)']


OBJ_SLOTS = 5                                  # pearl_story.inc PL_OBJ_X/Y/Z: works 0x8030-0x803E


def obj_slot(tr, uid):
    """The work slot holding where AddObject puts object uid (Pearl's SetObjectEventPos outside the zone init), or None
    (more than OBJ_SLOTS such objects in one file: the last place in address order, as before 2026-10-20)."""
    if getattr(tr, '_obj_slots', None) is None:
        tr._obj_slots = {}
        for a in sorted(tr.d.insns):
            e, op, args = tr.d.insns[a]
            if a in tr.reach_from and tr.job.pd.cmd_name(op) == 'SetObjectEventPos' and tr.levels(a) != {2}:
                u = args[0][1]
                if u not in tr._obj_slots and len(tr._obj_slots) < OBJ_SLOTS:
                    tr._obj_slots[u] = len(tr._obj_slots)
    return tr._obj_slots.get(uid)


@handler('SetObjectEventDir')
def h_setobjdir(tr, a, vals, name):
    uid, d = vals
    i, o = ev_object(tr, uid, name)
    if o is None:
        return [f'pl_stub SetObjectEventDir  // object {uid} is not in this zone']
    if tr.levels(a) == {2}:
        moved = same_block_before(tr, a, 'SetObjectEventPos', uid)      # (a Pos just before: turn there)
        if moved:
            x, z = moved[1], moved[2]
            return [f'pl_SetObjectEventPos {i}, {tr.var(x)}, {tr.var(z)}, {tr.var(d)}, {grid_y(tr, x, z, o["y"])}  '
                    f'// SetObjectEventDir {uid} (at the place SetObjectEventPos just gave)']
        return [f'pl_SetObjectEventPos {i}, {o["x"]}, {o["z"]}, {tr.var(d)}, {grid_y(tr, o["x"], o["z"], o["y"])}  '
                f'// SetObjectEventDir {uid} (at its own place)']
    return [f'pl_ApplyMovement {uid}, .Lface{a:x}  // SetObjectEventDir {uid}: the live actor turns',
            'pl_WaitMovement', f'VMJump .Lface{a:x}_end', '.balign 4, 0', f'.Lface{a:x}:',
            f'    Move {vals[1] if vals[1] < 4 else 0}, 1', '    MoveEnd', f'.Lface{a:x}_end:']


_PLANNER = None


@handler('SetWarpEventPos')
def h_setwarp(tr, a, vals, name):
    """Black 2 places the warp at y = arg * 16 units and fires it within 2 units of the walker's height
    (ObjInitWarpGPos, ov012 SetZoneWarpLocation / CheckWarpPositionMatch): y is the height, in 16-unit steps rounded,
    of the tile the player fires it from (a mat: its own tile; a bump warp: the tile its dir steps from). Before
    2026-10-20 y was 0: Valley Windworks' door, moved back to (243, 654) on 80-unit ground, would never fire."""
    global _PLANNER
    i, x, z = vals
    y = 0
    if tr.zone_file and i < 0x4000:
        if _PLANNER is None:
            from patches import sinnoh_events
            _PLANNER = (sinnoh_events, sinnoh_events.Planner())
        se, pl = _PLANNER
        ws = pl.warps(tr.job.zone['id'])[0] if tr.job.zone['id'] in pl.b2_of else []
        if i < len(ws):
            w = ws[i]
            units = (w['y'] ^ 0x8000) - 0x8000                  # the warp's own height (s16)
            if x < 0x4000 and z < 0x4000:
                step = {0: (0, -1), 1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}.get(w['dir'], (0, 0))
                fx, fz = (x, z) if w['type'] in (0, 1) else (x + step[0], z + step[1])
                t = pl.tile(pl.matrix(tr.job.zone['matrix']), fx, fz)
                if t is not None and t[2] is not None:
                    units = t[2]
            y = int(round(units / 16))
    return [f'pl_SetWarpEventPos {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}, {y}']


@handler('CallBattleTowerFunction')
def h_tower_function(tr, a, vals, name):
    """Pearl's Battle Tower on Black 2's Battle Subway (b2tools/tower_script.py, notes/BATTLE_ZONE.md)."""
    import tower_script
    return tower_script.h_function(tr, vals)


@handler('InitBattleTower')
def h_tower_init(tr, a, vals, name):
    import tower_script
    return tower_script.h_init(tr, vals)


@handler('FreeBattleTower')
def h_tower_free(tr, a, vals, name):
    return ['Plugin1_Cmd1002  // FreeBattleTower']


@handler('SetBattleTowerNull')
def h_tower_null(tr, a, vals, name):
    return ['Plugin1_Cmd1000  // SetBattleTowerNull']


@handler('PrintBattleTowerIntroMessage')
def h_tower_intro(tr, a, vals, name):
    import tower_script
    return tower_script.h_intro(tr, vals)


# ---- plat-records (2026-11-08): the Tower lobby's results machines show the player's own results
# Gen 4's OpenBattleTowerRecordsApp isRankingsScreen, resultsType (pokeplatinum scripts_battle_tower.s BattleTower_ResultsMachine;
# Pearl's file 358 the same) opens the records app (pokeplatinum applications/frontier/tower_records.c). With isRankingsScreen
# FALSE it shows the player's own results for resultsType (PrintRecordsScreen): 0 the Single and Double rooms, 1 the Multi and
# link Multi rooms, 2 the Wi-Fi room (its rank, then its streaks). Each room has two rows: PREV or CURRENT (CURRENT while the
# streak goes on) with the latest streak, and RECORD with the longest. Black 2 has no such screen: its records screen
# (BSubwayCmd_Tool 111, overlay 141) lists OTHER players' records. So these machines show the same rows as a message, in the
# app's own words (its bank, TOWER_RECORDS_BANK: Pearl's, Diamond's and Platinum's lines 0-21 are the same), with the numbers
# Black 2's Battle Subway keeps for the Tower (its score block, by play mode: Pearl's and Platinum's 0 Single, 1 Double, 2 Multi,
# 3 link Multi, 4 Wi-Fi are Black 2's modes 0-4; tower_script.py): the latest streak BSubwayCmd_Tool 6 (BSubwayScoreData_
# GetStreak, set at a loss and after seven wins), the longest the Frontier core's record 2 * mode (BSubwayScoreData_GetMaxStreak,
# plat_frontier.c: no Black 2 command reads it by mode), CURRENT when the mode has a stage (BSubwayCmd_Tool 38, BSubwayScoreData_
# HasStage: set when a challenge starts, raised after seven wins, cleared at a loss or a disqualification), the Wi-Fi rank
# BSubwayCmd_Tool 27. With isRankingsScreen TRUE (the leaders machine, after 0x1E4 found leaders: never, the Wi-Fi rooms are
# closed) Black 2's leaders screen stays. The rows' colors are the app's palette (dropped).
TOWER_RECORDS_BANK = 17     # pokediamond narc_0017.gmm, pokeplatinum res/text/battle_tower_records_app.json


def _tower_records_lines(job):
    """The first of the eleven lines pl_TowerResults shows (src/include/pearl_story.inc), added to the zone's text in its order:
    Single PREV, Single CURRENT, Double PREV, Double CURRENT, the same for Multi and Link, the Wi-Fi rank, Wi-Fi PREV and CURRENT.
    Built from the records app's own lines (bank TOWER_RECORDS_BANK, by number): 0-2 the screens' titles, 3-5 the first rooms'
    names and 6-8 the second ones' (two rows each in the app: one here), 9 PREV, 10 CURRENT, 11 RECORD, 12 RANK, 13 "Win streak:
    N" (buffer 0 the latest streak, 1 the longest), 14 the rank's number."""
    w = [re.sub(r'\{COLOR \d+\}', '', t) for t in job.gen4_text.bank(TOWER_RECORDS_BANK)]
    assert w[13].startswith('Win streak: {STRVAR_1 53, 0}') and w[14] == '{STRVAR_1 51, 0}', w[13:15]
    name = lambda n: ' '.join(w[n].replace('\\n', ' ').split())             # "Single\nRecord" -> "Single Record"
    streak = lambda i: w[13].rstrip().replace('{STRVAR_1 53, 0}', f'{{STRVAR_1 53, {i}}}')
    rows = lambda now: f'{w[now]} {streak(0)}\\f{w[11]} {streak(1)}'      # PREV or CURRENT, then RECORD
    lines = []
    for title, first, second in ((0, 3, 6), (1, 4, 7)):
        for now in (9, 10):
            lines.append(f'{w[title]}\\n{name(first)}\\f{rows(now)}\\r')
        for now in (9, 10):
            lines.append(f'{name(second)}\\n{rows(now)}')
    lines.append(f'{w[2]}\\n{name(5)}\\f{w[12]} {w[14]}\\r')
    for now in (9, 10):
        lines.append(f'{name(8)}\\n{rows(now)}')
    ns = [job.line_text(('tower_results', k), t) for k, t in enumerate(lines)]
    assert ns == list(range(ns[0], ns[0] + len(lines))), ns          # (the macro counts from the first)
    return ns[0]


@handler('OpenBattleTowerRecordsApp')
def h_tower_records(tr, a, vals, name):
    first = _tower_records_lines(tr.job)
    return [f'pl_TowerResults {tr.var(vals[0])}, {tr.var(vals[1])}, {first}  // OpenBattleTowerRecordsApp: the player\'s '
            f'results as a message (Black 2\'s leaders screen for the rankings)']
# ---- end plat-records


@handler('1E4')
def h_tower_has_leaders(tr, a, vals, name):
    """Gen 4's 0x1E4 var (pokeplatinum ScrCmd_1E4: WifiBattleTowerDownloadData_HasMatchListData; Pearl's the same): whether
    the Wi-Fi Battle Room leaders were ever downloaded, which the lobby's leaders machine asks before its list (none: "There
    doesn't appear to be any data yet..."). Black 2's own question about its Wi-Fi Subway leaders (ov050 scrcmd_bsubway.c
    case 110, BSubwayWifiData_HasLeaders): none, the Wi-Fi rooms closed. It was a stub, leaving the var as it was, so the
    machine opened Black 2's leader list ("SUCCESSIVE TRAINERS", empty; 2026-11-08, plat-test)."""
    return [f'BSubwayCmd_Tool 110, 0, 0, {tr.var(vals[0])}  // Gen 4 0x1E4: any Wi-Fi leaders downloaded (Black 2\'s '
            f'Wi-Fi Subway leaders)']


@handler('GetBattleTowerPartnerSpeciesAndMove')
def h_tower_partner_mon(tr, a, vals, name):
    return [f'pl_TowerPartnerMon {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}, {tr.var(vals[3])}']


@handler('ShowBattlePoints', 'HideBattlePoints', 'UpdateBPDisplay', 'GetBattlePoints', 'GiveBattlePoints',
         'RemoveBattlePoints', 'CheckBattlePoints')
def h_battle_points(tr, a, vals, name):
    import tower_script
    return tower_script.h_battle_points(name, tr, vals)


@handler('GetExchangeServiceCornerItemAndCost')
def h_exchange(tr, a, vals, name):
    return [f'pl_TowerExchange {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}, {tr.var(vals[3])}']


@handler('BufferVarPaddingDigits')
def h_buffer_padded(tr, a, vals, name):
    return [f'pl_BufferNumber {vals[0]}, {tr.var(vals[1])}, {vals[3]}  // BufferVarPaddingDigits']


# Platinum's text buffers (2026-11-02, the dialogue step: notes/PORT_AUDIT.md "Step 2: dialogue")
@handler('BufferTypeName')
def h_buffer_type(tr, a, vals, name):
    """Platinum 0x2FD BufferTypeName idx, type (Veilstone's Hidden Power guitarist): Black 2's WordSetPokeTypeName. The
    type comes from CalcHiddenPowerType, which gives Black 2's type number here (Gen 4 numbers ??? as 9, Fire 10)."""
    return [f'WordSetPokeTypeName {vals[0]}, {tr.var(vals[1])}  // BufferTypeName (a type of Black 2\'s numbering)']


@handler('CalcHiddenPowerType')
def h_hidden_power_type(tr, a, vals, name):
    """Platinum 0x2FF CalcHiddenPowerType slot, var: the Hidden Power type of a party Pokémon, 0xFFFF when it can't learn
    TM10 (scrcmd.c). Black 2's PokePartyGetHiddenPowerType does the same (ov036 scrcmd_pokemon_misc.c), in Black 2's
    type numbers, which BufferTypeName above takes."""
    return [f'PokePartyGetHiddenPowerType {tr.var(vals[1])}, {tr.var(vals[0])}  // CalcHiddenPowerType']


@handler('BufferFloorNumber')
def h_buffer_floor(tr, a, vals, name):
    """Platinum 0x347 BufferFloorNumber idx, floor: the floor for its elevators' floor window (ShowCurrentFloor), which
    Black 2 lacks (h_show_floor: no window, as Pearl's elevators), so nothing reads it."""
    tr.job.approx['BufferFloorNumber (for the floor window Black 2 lacks: nothing reads it)'] += 1
    return [f'// BufferFloorNumber {vals[0]}, {vals[1]}: for the floor window, which Black 2 lacks (ShowCurrentFloor)']


@handler('1DF', '1E0')
def h_tower_none(tr, a, vals, name):
    """Pearl's tower trophies and the Wi-Fi history: Black 2 has neither, and the scripts read the var."""
    return [f'pl_SetVarFromValue {tr.var(vals[0])}, 0  // Pearl 0x{name}: none here']


@handler('MessageSeenBanlistSpecies')
def h_banlist(tr, a, vals, name):
    """Pearl's "you don't have N eligible Pokémon" with the banned species seen: the line without that list."""
    tr.job.approx['MessageSeenBanlistSpecies (the line without the list of banned species)'] += 1
    return [f'pl_BufferNumber 0, {vals[1]}, 1  // MessageSeenBanlistSpecies line {vals[0]}, {vals[1]} Pokémon'] + \
        h_message(tr, a, [vals[0]], 'Message')


@handler('CheckSaveType')
def h_save_type(tr, a, vals, name):
    """Pearl's save-state check: Black 2's save has one state, the plain save."""
    return [f'pl_SetVarFromValue {tr.var(vals[0])}, 1  // CheckSaveType: a plain save']


@handler('OpenSaveInfo', 'CloseSaveInfo')
def h_save_info(tr, a, vals, name):
    return [f'// {name}: no save details window here']


@handler('GetCurNetID')
def h_net_id(tr, a, vals, name):
    """No link here: always the first player."""
    return [f'pl_SetVarFromValue {tr.var(vals[0])}, 0  // GetCurNetID: no link']


@handler('Unk02C9')
def h_species_article(tr, a, vals, name):
    return [f'pl_BufferSpeciesName {vals[0]}, {tr.var(vals[1])}  // Pearl 0x2C9']


@handler('InitTurnbackCave')
def h_turnback(tr, a, vals, name):
    """Pearl 0x285 (pokediamond ScrCmd_Unk0285, pokeplatinum ScrCmd_InitTurnbackCave): Turnback Cave's maze sets the
    doors of the room. Here in the zone init only the room's rocks (a zone holding two of Pearl's rooms); the doors
    after the arrival, in the zone's TurnbackDoors map script (b2tools/turnback.py, PearlData.turnback_doors)."""
    import turnback
    tr.job.approx['InitTurnbackCave (the doors in a map script after the arrival: b2tools/turnback.py)'] += 1
    return turnback.init_lines(tr, vals)


@handler('SetBgEventPos')
def h_setbg(tr, a, vals, name):
    """Pearl 0x18B (SetBgEventPosition index, x, z) moves a sign (BG event) = Black 2's ObjInitPointGPos (ov012
    SetBGEntityLocation; every level). Pearl's BG events keep their index in the zone's sign list (pearl_events.entities
    puts Pearl's sign objects after them); y = the tile's height in units, as a sign's (pearl_events sign_y). Valley
    Windworks: the door's "It's locked" sign moves away once the Works Key opened it (2026-10-25)."""
    i, x, z = vals
    y = 0
    if isinstance(x, int) and isinstance(z, int) and x < 0x4000 and z < 0x4000:
        y = heights().at(tr.job.zone, x, z) or 0
    return [f'pl_SetBgEventPos {tr.var(i)}, {tr.var(x)}, {tr.var(z)}, {y}  // SetBgEventPosition {i}, {x}, {z}']


@handler('SetPosition')
def h_setpos(tr, a, vals, name):
    uid, x, y, z, d = vals
    if version.PLATINUM and uid in tr.follow_uids:   # (plat-test) the follower once it follows (Black 2 renamed it 0xFE)
        return [f'pl_SetPositionF {uid}, {tr.var(x)}, {grid_y(tr, x, z, tr.var(y))}, {tr.var(z)}, {tr.var(d)}  '
                f'// (the follower once it follows)']
    return [f'pl_SetPosition {tr.var(uid)}, {tr.var(x)}, {grid_y(tr, x, z, tr.var(y))}, {tr.var(z)}, {tr.var(d)}']


@handler('SetMovementType')
def h_setmove(tr, a, vals, name):
    import pearl_events
    uid, t = vals
    if t == FOLLOW:
        ally = same_block_before(tr, a, 'SetVarFromValue', PARTNER_VAR)
        if ally and ally[1] < 0x4000 and str(ally[1]) in tr.job.ids.reg['trainers']:
            # a partner this file also stops (SetObjectFlagIsPersistent X, 0: Cheryl at the forest's entrance) stays
            # in the zone: Black 2's non-persistent follower, which ActorPairEnd gives back its own id, so Pearl's
            # later moves of object X find it (a persistent one keeps 0xFE for good)
            stays = any(self_op == 'SetObjectFlagIsPersistent' and args[0][1] == uid and args[1][1] == 0
                        for self_op, args in ((tr.job.pd.cmd_name(op), args) for e, op, args in tr.d.insns.values()))
            stays = stays or partner_stays(tr, uid)
            return [f'pl_follow_start_ally {actor(tr, uid)}, {tr.job.ids.trainer(ally[1])}, {0 if stays else 1}  '
                    f'// Pearl SetMovementType {uid}, 0x30 with partner trainer {ally[1]} (var 0x403F): follows and '
                    f'battles with you{" (in this zone only)" if stays else ""}']
        return [f'pl_follow_start {actor(tr, uid)}  // Pearl SetMovementType {uid}, 0x30 (follow the player)']
    if uid in tr.follow_uids or uid in (0xF2, 0xFE):
        return [f'pl_follow_hold {actor(tr, uid)}, {pearl_events.b2_move(t)}  // Pearl SetMovementType {uid}, {t}: '
                f'the follower stops to be moved by the script']
    return [f'pl_SetMovementType {actor(tr, uid)}, {pearl_events.b2_move(t)}  // Pearl movement type {t}']


@handler('SetObjectFlagIsPersistent')
def h_keep(tr, a, vals, name):
    if vals[1] == 0 and (vals[0] in (0xF2, 0xFE) or vals[0] in tr.follow_uids):
        return [f'pl_follow_end  // SetObjectFlagIsPersistent {vals[0]}, 0: the follower stops following']
    tr.job.approx['SetObjectFlagIsPersistent (not needed: Black 2 keeps actors while the zone is loaded)'] += 1
    return [f'// SetObjectFlagIsPersistent {vals[0]}, {vals[1]}: not needed in Black 2']


# ---- sound
@handler('PlaySE', 'StopSE', 'WaitSE', 'PlayFanfare', 'PlayMusic', 'SetBGM')
def h_sound(tr, a, vals, name):
    macro = {'PlaySE': 'pl_PlaySE', 'StopSE': 'pl_StopSE', 'WaitSE': 'pl_WaitSE', 'PlayFanfare': 'pl_PlayFanfare',
             'PlayMusic': 'pl_PlayMusic', 'SetBGM': 'pl_PlayMusic'}[name]
    b2, pname = seq_name(vals[0])
    if macro == 'pl_PlayMusic' and pname in PEARL_SONGS:     # Pearl's own song (patches/sinnoh_music EVENT_SONGS)
        alt = [f'    {macro} {b2}  // Black 2 stand-in (a build without sinnoh_music)'] if b2 else \
              [f'    pl_stub {name}  // Pearl sound {pname}: no Black 2 stand-in']
        return [f'#ifdef SEQ_PEARL_{pname[4:]}', f'    {macro} SEQ_PEARL_{pname[4:]}  // Pearl {pname}', '#else',
                *alt, '#endif']
    if b2 is None:
        tr.job.stubs[f'{name} {pname or vals[0]} (no Black 2 sound chosen)'] += 1
        return [f'pl_stub {name}  // Pearl sound {pname or vals[0]}: no Black 2 sound chosen yet']
    return [f'{macro} {b2}  // Pearl {pname}']


@handler('PlayCry')
def h_cry(tr, a, vals, name):
    return [f'pl_PlayCry {tr.var(vals[0])}']


@handler('PlayDefaultMusic')
def h_defmusic(tr, a, vals, name):
    return ['pl_PlayDefaultMusic']


@handler('StopMusic')
def h_stopmusic(tr, a, vals, name):
    tr.job.approx['StopMusic (a short fade-out)'] += 1
    return ['pl_FadeOutBGM 1  // StopMusic']


# ---- the wall maps (2026-10-26; Pearl's tile behaviour 0x85 -> pearl_events.TOWN_MAP's sign events): Pearl's common
# script 2508 is PlaySE, LockAll, FadeScreen out, WaitFadeScreen, OpenRegionMap (pokediamond ScrCmd_ShowTownMapScreen:
# the Town Map app), ReturnToField, FadeScreen in, WaitFadeScreen, ReleaseAll. Black 2's CallPlaceSelect runs the town
# map as a field subprocess (ov036 s0284_CallPlaceSelect: EventFieldSubprocessCall closes and reopens the field), so
# the ReturnToField after it is dropped; patches/town_map.py opens it view-only in a zone without Fly (the rooms).
@handler('OpenRegionMap')
def h_region_map(tr, a, vals, name):
    tr.after_region_map = True
    return ['CallPlaceSelect PL_TMP, PL_TMP2  // OpenRegionMap: the Sinnoh town map, view-only here (patches/town_map.py)']


@handler('FadeOutBGM')
def h_fadebgm(tr, a, vals, name):
    return [f'pl_FadeOutBGM {vals[1]}  // FadeOutBGM to volume {vals[0]}']


# ---- screen
@handler('FadeScreen')
def h_fade(tr, a, vals, name):
    trans, frames, typ, color = vals
    if a in poke_select_fades(tr):
        return [f'// FadeScreen {trans}, {frames}, {typ}, {color:#x}: Black 2\'s party select fades itself']
    if typ == 1 and getattr(tr, 'after_diploma', False):      # (not the starter screen's white: the diploma ends black)
        tr.after_diploma = tr.after_starter = False
    if typ == 1 and tr.after_starter:
        tr.after_starter = False
        return [f'pl_fade_in_after_starter  // FadeScreen {trans}, {frames}, {typ}, {color:#x} (the starter screen ends '
                f'white in Black 2)']
    if typ not in (0, 1):
        tr.job.approx[f'FadeScreen type {typ}'] += 1
    return [f'pl_fade_{"in" if typ == 1 else "out"}_{"white" if color else "black"}  // FadeScreen {trans}, {frames}, '
            f'{typ}, {color:#x}']


# ---- warps
# ---- elevators (ELEVATOR_FLOORS_ABOVE: the floor the player came from, and where the exit goes)
@handler('GetFloorsAbove')
def h_floors_above(tr, a, vals, name):
    return [f'WorkSet {tr.var(vals[0])}, PL_ELEVATOR_FROM  // GetDynamicWarpFloorNumber: the floors above the '
            f'floor the player came from (PearlElevatorInit)']


@handler('SetSpecialLocation')
def h_special_location(tr, a, vals, name):
    m, w, x, z, d = vals
    pd = tr.job.pd
    if any(v >= 0x4000 for v in vals) or pd.b2_zone.get(m) is None:
        tr.job.stubs['SetSpecialLocation (a var, or a zone not installed)'] += 1
        return [f'pl_stub SetSpecialLocation  // Pearl SetDynamicWarp {vals}']
    ws = pd.events(pd.zones[m])['warp_events']
    if w < len(ws):                                 # Pearl takes a warp's tile when it names one (Location.warpId)
        x, z = ws[w]['x'], ws[w]['z']
        import pearl_events
        h = pearl_events.Heights()
        dx, dz = {0: (0, -1), 1: (0, 1), 2: (-1, 0), 3: (1, 0)}.get(d, (0, 0))
        if h.solid(pd.zones[m], x, z) and not h.solid(pd.zones[m], x + dx, z + dz):
            x, z = x + dx, z + dz                   # (a door tile: Black 2 puts the player where it is told)
    else:
        h = None
    y = h.at(pd.zones[m], x, z) if h else None
    return [f'FieldSetNextZone {pd.b2_zone[m]}, {d + 1}, {x}, {round((y or 0) / 16)}, {z}  // SetDynamicWarp: the exit '
            f'(dest 0x100) goes to Pearl map {m} ({pd.zones[m]["name"]}) warp {w}',
            f'WorkSetConst PL_ELEVATOR_FROM, {ELEVATOR_FLOORS_ABOVE.get(m, 1)}  // and that is now where the player '
            f'came from']


@handler('ShowCurrentFloor')
def h_show_floor(tr, a, vals, name):
    tr.job.approx['ShowCurrentFloor (no floor window in Black 2)'] += 1
    return [f'// ShowCurrentFloor {vals[0]}, {vals[1]}, {tr.var(vals[2])}: no floor window in Black 2']


@handler('PlayElevatorAnimation')
def h_elevator_anim(tr, a, vals, name):
    tr.job.approx['PlayElevatorAnimation (Black 2\'s elevator sounds and a wait: no shaking room)'] += 1
    return [f'pl_elevator_ride  // PlayElevatorAnimation {tr.var(vals[0])}, {tr.var(vals[1])}']


HALL_OF_ORIGIN, HALL_OF_ORIGIN_TILE = 510, (31, 52)


@handler('Warp')
def h_warp(tr, a, vals, name):
    m, _, x, z, d = vals
    pd = tr.job.pd
    b2 = pd.b2_zone.get(m)
    if b2 is None:
        tr.job.stubs['Warp (to a zone not installed)'] += 1
        return [f'pl_stub Warp  // to Pearl map {m}: no Black 2 zone (not installed)', 'pl_ReleaseAll', 'pl_End']
    ids, _ = pd.arrival_ids(m)
    sid = ids[(tr.f, a)]
    if (x >= 0x4000 or z >= 0x4000) and tr.f in CAMERA_PLAN_FILES and camera_plan(pd, tr.f) is not None \
            and None not in {c for xz in _WARP_PLACES[tr.f].get(a, {(None, None)}) for c in xz}:
        # Black 2's MapChangeCore takes numbers, not works (ov036 scrcmd_mapchange.c: VM_Read16): a Warp to a place
        # in vars (Spear Pillar's vistas going back to where the player stood: Pearl file 230, 0x458) is a chain over
        # the places camera_plan finds the scene there with (2026-10-26, chapter 7: the player landed at (0x8020,
        # 0x8021), the var numbers). Black 2's script works 0x8000+ live in the running script (ov012
        # script_work.c: a new, cleared ScriptWork for each script, the continuation after a map change too), so
        # vars set before an earlier Warp of the chain read 0 here: the last place, the one taken then, is the
        # middle one (Spear Pillar: the player comes back to (31, 35), the middle of the row of five).
        out, places = end_free_camera(tr, 'a Warp', a), sorted(_WARP_PLACES[tr.f][a])
        mid = places[len(places) // 2]
        places = [p_ for p_ in places if p_ != mid] + [mid]
        for i, (px, pz) in enumerate(places):
            nxt = f'.Lwarp{a:x}_{i + 1}'
            if i < len(places) - 1:
                out += [f'WorkCmpConst {tr.var(x)}, {px}' if x >= 0x4000 else '', f'VMJumpIf CMP_NE, {nxt}' if x >= 0x4000 else '',
                        f'WorkCmpConst {tr.var(z)}, {pz}' if z >= 0x4000 else '', f'VMJumpIf CMP_NE, {nxt}' if z >= 0x4000 else '']
            out += [f'RTReserveScript {sid}  // the rest of this Pearl script runs there (continuation {sid})',
                    f'pl_Warp {b2}, {px}, {pz}, {d}  // Pearl map {m} ({pd.zones[m]["name"]}) at ({tr.var(x)}, '
                    f'{tr.var(z)}) = ({px}, {pz})', 'pl_ReleaseAll', 'pl_End']
            if i < len(places) - 1:
                out.append(f'{nxt}:')
        return [l for l in out if l]
    if x >= 0x4000 and z >= 0x4000 and m == HALL_OF_ORIGIN:
        # MapChangeCore takes numbers (above). Pearl's common script 2039 warps to where the player stands, and its one
        # trigger is Spear Pillar's (31, 52) (2026-11-01, found in game: the player landed at (0x8004, 0x8005))
        x, z = HALL_OF_ORIGIN_TILE
    return end_free_camera(tr, 'a Warp', a) + [f'RTReserveScript {sid}  // the rest of this Pearl script runs there (continuation {sid})',
            f'pl_Warp {b2}, {tr.var(x)}, {tr.var(z)}, {d}  // Pearl map {m} ({pd.zones[m]["name"]})',
            'pl_ReleaseAll', 'pl_End']


# ---- Chapter 6a (2026-10-25): the boats, Pearl's moving platforms, the Riolu Egg, the library's tremor
@handler('PlayBoatCutscene')
def h_boat(tr, a, vals, name):
    """Pearl 0x23D ShipAnimation (pokediamond ScrCmd_ShipAnimation: travel way, the player's facing on arrival, map, x,
    z; pokeplatinum FieldSystem_PlayBoatCutscene): the ship sails off (Canalave's drawbridge opens), the screen and the
    music fade, a voyage scene, then the map change to (x, z). Here Black 2's own boat cutscene by the way the ship
    sails (pl_BoatCutscene: Eldritch's boat = demo 4, the Snowpoint ship = demo 26, as HoennB2's boats), then the map
    change to Pearl's place, where PearlArrive fades in. Eldritch's boat (Canalave <-> Iron Island), the Snowpoint
    ship (post-game), Fullmoon / Newmoon (Chapter 9)."""
    travel, facing, m, x, z = vals
    pd = tr.job.pd
    b2 = pd.b2_zone.get(m)
    if b2 is None:
        tr.job.stubs['PlayBoatCutscene (to a zone not installed)'] += 1
        return [f'pl_stub PlayBoatCutscene  // to Pearl map {m}: no Black 2 zone']
    tr.job.approx['PlayBoatCutscene (Black 2\'s boat demo for Pearl\'s ship scenes; no drawbridge)'] += 1
    _, arrive = pd.arrival_ids(m)
    return [f'pl_BoatCutscene {travel}  // Pearl ShipAnimation {travel}, {facing}, {m}, {x}, {z}: Black 2\'s boat demo',
            f'RTReserveScript {arrive}  // PearlArrive there',
            f'pl_Warp {b2}, {x}, {z}, {facing}  // Pearl map {m} ({pd.zones[m]["name"]})']


def platform_zone(tr):
    """Whether this zone's platforms are Black 2's gimmick 59 (b2tools/pearl_gimmicks.py)."""
    import pearl_gimmicks
    return tr.job.zone['name'] in {c['name'] for c in pearl_gimmicks.zone_configs()}


@handler('InitPersistedMapFeaturesForCanalaveGym', 'InitPersistedMapFeaturesForPlatformLift', 'TriggerPlatformLift')
def h_platforms(tr, a, vals, name):
    """Pearl's platforms (the Canalave Gym's InitCanalaveGym; the platform lifts' set-up and trigger, which their zone
    script and step trigger run): Black 2's gimmick 59 sets them up on entry and moves them when the player steps on
    them (decomp src/pearlb2/pearl_platforms_itcm.c, patches/pearl_platforms.py), so the scripts have nothing to do.
    Zones not in the gimmick yet (the League's lifts) keep the stub."""
    if not platform_zone(tr):
        tr.job.stubs[f'{name} (a zone without gimmick 59 yet)'] += 1
        return [f'pl_stub {name}  // the zone is not in b2tools/pearl_gimmicks.py yet']
    import pearl_gimmicks
    if name == 'TriggerPlatformLift' and pearl_gimmicks.scripted_lift(tr.job.zone['name']):
        # (2026-10-26, chapter 8) a lift whose ride Pearl starts from a script with the player on it (Cynthia's room,
        # after her battle: no step trigger): the script asks gimmick 59 and waits for the ride
        tr.job.approx['TriggerPlatformLift from a script (gimmick 59 rides when asked: PVAR_GIMMICK_REQUEST)'] += 1
        return ['pl_TriggerPlatformLiftRide  // Pearl TriggerPlatformLift: gimmick 59 rides the lift with the player']
    tr.job.approx[f'{name} (gimmick 59 does it: patches/pearl_platforms.py)'] += 1
    return [f'// {name}: gimmick 59 does it (decomp src/pearlb2/pearl_platforms_itcm.c)']


@handler('CheckPlatformLiftNotUsedWhenEnteredMap')
def h_lift_not_used(tr, a, vals, name):
    """Pearl 0x25D (pokeplatinum PlatformLift_WasNotUsedWhenEnteredMap): 1 when the player came into a League lift
    room at the bottom (Pearl's lift then waits there and its step trigger is armed), 0 at the top. Gimmick 59 places
    the lift by the player's floor and rides it on the step itself, so the trigger's script has nothing to do either
    way: 1, Pearl's answer on every way into these rooms (each is entered from below; 2026-10-26, chapter 8)."""
    if not platform_zone(tr):
        tr.job.stubs[f'{name} (a zone without gimmick 59 yet)'] += 1
        return [f'pl_stub {name}  // {tr.var(vals[0])}: the zone is not in b2tools/pearl_gimmicks.py yet']
    tr.job.approx[f'{name} (1: gimmick 59 places the lift by the player\'s floor)'] += 1
    return [f'WorkSetConst {tr.var(vals[0])}, 1  // Pearl {name}: the lift waits at the player\'s floor (gimmick 59)']


@handler('InitPersistedMapFeaturesForSunyshoreGym')
def h_sunyshore_init(tr, a, vals, name):
    """Pearl 0x175 InitSunyshoreGym room (the gym rooms' zone scripts; pokediamond InitSunyshoreGym 0x02064D88): the
    gears' start state by the room and the warp the player came in by (from the entrance: 0; else rooms 1-3 at 2, 1,
    0). Gimmick 62 (decomp src/pearlb2/sunyshore_gym_itcm.c, patches/sunyshore_gym.py) decides it on the zone's first
    frame by the player's tile, so the script has nothing to do (2026-10-26, chapter 8)."""
    tr.job.approx['InitSunyshoreGym (gimmick 62 does it)'] += 1
    return [f'// InitSunyshoreGym {vals[0]}: gimmick 62 sets the gears by the player\'s way in (sunyshore_gym_itcm.c)']


@handler('InitPersistedMapFeaturesForVeilstoneGym')
def h_veilstone_init(tr, a, vals, name):
    """Pearl 0x174 InitVeilstoneGym (the Gym's zone script; pokediamond arm9 0x02064D4C): the 12 panels at their start
    states. Gimmick 60 (decomp src/pearlb2/resident/veilstone_gym.c, patches/veilstone_gym.py) starts them there on
    each entry, since Black 2 clears the gimmick's saved work on a zone change, so the script has nothing to do.
    Platinum's own Gym (its bags and tire stacks): gimmick 66 does the same (src/pearlb2/plat_gyms/plat_veilstone_gym.c,
    patches/platinum_gyms.py; 2026-11-02, plat-gyms)."""
    if version.PLATINUM:
        tr.job.approx['InitPersistedMapFeaturesForVeilstoneGym (gimmick 66 does it)'] += 1
        return ['// InitPersistedMapFeaturesForVeilstoneGym: gimmick 66 puts the bags and stacks at their places '
                '(plat_gyms/plat_veilstone_gym.c)']
    tr.job.approx['InitVeilstoneGym (gimmick 60 does it)'] += 1
    return ['// InitVeilstoneGym: gimmick 60 starts the panels at their places (resident/veilstone_gym.c)']


@handler('InitPersistedMapFeaturesForEternaGym')
def h_eterna_init(tr, a, vals, name):
    """Platinum 0x2C9 (its Eterna Gym's on-transition script): the flower clock's set-up. Gimmick 65 (decomp
    src/pearlb2/plat_gyms/plat_eterna_gym.c, patches/platinum_gyms.py) sets the hands and the fountains by the clock's
    state on each field, so the script has nothing to do (2026-11-02, plat-gyms)."""
    tr.job.approx['InitPersistedMapFeaturesForEternaGym (gimmick 65 does it)'] += 1
    return ['// InitPersistedMapFeaturesForEternaGym: gimmick 65 sets the clock by its state (plat_gyms/plat_eterna_gym.c)']


ETERNA_FOUNTAIN_LINE = 12                  # Platinum's eterna_city_gym bank: EternaGym_Text_FountainWaterLevelDropped


@handler('AdvanceEternaGymClock')
def h_eterna_clock(tr, a, vals, name):
    """Platinum 0x2CA (its Eterna Gym, after each Gym Trainer's win and Gardenia's TM): the clock turns, the camera
    looks on, a fountain drains after the second and third Trainer with its line (pokeplatinum scrcmd.c
    ScrCmd_AdvanceEternaGymClock, gym_features.c FieldTask_EternaGym_AdvanceClockState). Gimmick 65 does it through
    PVAR_GIMMICK_REQUEST; the macro shows the fountain's line from the zone's own text (2026-11-02, plat-gyms)."""
    assert tr.job.zone['name'] == 'MAP_ETERNA_GYM_ENTRANCE', tr.job.zone['name']
    tr.job.approx['AdvanceEternaGymClock (gimmick 65 turns the clock: PVAR_GIMMICK_REQUEST)'] += 1
    return [f'pl_AdvanceEternaGymClock {ETERNA_FOUNTAIN_LINE}  // Platinum AdvanceEternaGymClock: the clock turns '
            f'(plat_gyms/plat_eterna_gym.c)']


@handler('PressSunyshoreGymButton')
def h_sunyshore_button(tr, a, vals, name):
    """Pearl 0x176 RotateSunyshoreGymGear type (0 a quarter turn, 1 a quarter back, 2 a half turn; pokeplatinum
    SunyshoreGym_PressButton): every gear of the room turns and the script waits (Pearl's field task). Gimmick 62 turns
    them; pl_RotateSunyshoreGymGear asks through PVAR_GIMMICK_REQUEST (1 + the type) and waits for 0 (2026-10-26,
    chapter 8)."""
    if vals[0] >= 0x4000:
        tr.job.stubs['RotateSunyshoreGymGear (the type from a var)'] += 1
        return [f'pl_stub {name}  // {tr.var(vals[0])}']
    return [f'pl_RotateSunyshoreGymGear {vals[0]}  // Pearl RotateSunyshoreGymGear {vals[0]}: the gears turn '
            f'(sunyshore_gym_itcm.c)']


@handler('GetLeagueVictories')
def h_league_victories(tr, a, vals, name):
    """Pearl 0x28F (the Hall of Fame room: Rowan's and Cynthia's first-time lines when 0; Fight Area Barry's team at
    20 wins): Pearl counts the player's League wins in its save. Black 2's record of Hall of Fame entries
    (RECORD_HALL_OF_FAME_ENTRIES 71, counted by its game clear: ov295 game_clear_save.c) is the same count, 0 the
    first time (2026-10-26, the lead: not the game-clear flag, whose 0/1 breaks Barry's 20)."""
    tr.job.approx['GetLeagueVictories (Black 2\'s Hall of Fame entries record)'] += 1
    return [f'pl_GetLeagueVictories {tr.var(vals[0])}']


@handler('PlayHallOfFameHealingAnimation')
def h_hof_heal(tr, a, vals, name):
    """Pearl 0x25A (the Hall of Fame machine: the party's balls on it and the healing tune). Black 2's machine event
    (EventDendouMachine) needs Black 2's own Hall of Fame props, and its Pokémon Center heal needs a Center machine
    prop (a data abort without one: the heal fix, 2026-10-25), so: the healing tune only (SEQ_ME_ASA, the Center's)."""
    tr.job.approx['PlayHallOfFameHealingAnimation (the healing tune only: no machine animation)'] += 1
    return [f'pl_PlayHallOfFameHealingAnimation  // Pearl 0x25A {tr.var(vals[0])}: the healing tune']


@handler('IncrementGameRecord')
def h_game_record(tr, a, vals, name):
    """Pearl 0x1E5 IncrementGameStat n (its save's records: the Hall of Fame room's 46, times entered; Black 2's game
    clear counts its own): nothing, as IncrementTrainerScore2 (2026-10-26, chapter 8)."""
    tr.job.approx['IncrementGameRecord (Black 2 keeps its own records)'] += 1
    return [f'// IncrementGameRecord {vals[0]}: nothing in Black 2 (its own records)']


@handler('ClearGame')
def h_clear_game(tr, a, vals, name):
    """Pearl 0xB0 ShowEndGameScreen (pokeplatinum ClearGame: the game-clear flag, the Hall of Fame record, the save,
    the credits, a reset). Black 2's own Hall of Fame ending, exactly as its script does it (pokemon_league_10.s:
    FadeOutBlackQ, FadeWait, CallGameClear 0 the first time / 1 after, FinishAllEvents, ActorsUnpauseAll: HoennB2's
    black screen came from ending another way, 2fd355b), PearlB2's game clear in the decomp's event_game_clear.c
    (Pearl's start room on Continue: global 9601, src/field_scripts/1242_global_9600.s). Nothing after it runs (Pearl
    resets there too). 2026-10-26, chapter 8."""
    tr.job.approx['ClearGame (Black 2\'s game clear: record, save, credits, THE END)'] += 1
    return ['pl_ClearGame  // Pearl ShowEndGameScreen: Black 2\'s Hall of Fame record, save, credits (ends the script)']


@handler('InitPersistedMapFeaturesForHearthomeGym', 'MoveHearthomeGymDPLift')
def h_hearthome_lift(tr, a, vals, name):
    """Pearl's Hearthome Gym lift (0x171 InitHearthomeGym in the four question rooms' zone scripts, 0x172
    MoveHearthomeGymElevator on their step trigger (9, 13); 2026-10-26, the ch5b agent): gimmick 59's platform lift
    (pearl_gimmicks.HEARTHOME_LIFTS), which places it by the player's floor (the first room's up and still until flag
    0x98D, as Pearl's) and rides it on the step, so the scripts have nothing to do.
    Platinum's own Gym (pearl_gimmicks.HEARTHOME_GYM 'dark rooms'): its trainer rooms' on-transition script sets up the
    dark, the doors and the clue; gimmick 67 does that on each field (src/pearlb2/plat_gyms/plat_hearthome_gym.c,
    patches/platinum_gyms.py; 2026-11-02, plat-gyms)."""
    import pearl_gimmicks
    if pearl_gimmicks.HEARTHOME_GYM == 'dark rooms' and name == 'InitPersistedMapFeaturesForHearthomeGym':
        tr.job.approx['InitPersistedMapFeaturesForHearthomeGym (gimmick 67 does it)'] += 1
        return ['// InitPersistedMapFeaturesForHearthomeGym: gimmick 67 sets up the dark, the doors and the clue '
                '(plat_gyms/plat_hearthome_gym.c)']
    return h_platforms(tr, a, vals, name)


@handler('GiveEgg')
def h_give_egg(tr, a, vals, name):
    """Pearl 0x97 GiveEgg species, place (pokediamond: an Egg from a gift; Riley's Riolu at Iron Island) = Black 2's
    PokePartyAddEgg (its own met place for a gift Egg; the script checks the party's room first, as Pearl's)."""
    tr.job.approx['GiveEgg (Black 2 writes its own met place)'] += 1
    return [f'PokePartyAddEgg PL_TMP, {tr.var(vals[0])}, 0  // GiveEgg {vals[0]}, {vals[1]}']


# ---- the post-game's events built in (2026-10-26, chapter 9a; user 2026-10-25: "make it so all the events like
# darkrai shaymin etc are built into the base game already", "arceus too"; DECISIONS 2026-10-25)
# Pearl's Mystery Gift deliveryman (globals 10200 on load / 10201 talk, file 373, in every Pokémart) gives Pearl's four
# event gifts after the Hall of Fame, one a talk, in the user's order; PVAR_DELIVERY counts the ones given
# (pearl_story.inc "the deliveryman"). Pearl's lines for each are its own (bank 332).
DELIVERY_BANK = 332
DELIVERY_LINES = (14, 15, 16, 13)     # "received a Member's Card", "Oak's Letter", "an Azure Flute", "the MANAPHY Egg"
if version.PLATINUM:                  # Platinum's: the event Regigigas, "received {Regigigas}!" (its line 7; 2026-11-07,
    DELIVERY_LINES += (7, 17)         # plat-story), then "received a Secret Key" (line 17: Rotom's event; 2026-11-02,
                                      # plat-rooms); pearl_story.inc PL_DELIVERY_GIFTS
# (v101-story) Pearl and Diamond 1.0.1: then the Pokétch apps (version.POKETCH_APP_GIFTS), each "received the Pokétch app
# ...!" (line 18) with the app's name written in (Black 2 has no word for it: NAME_SOURCES). (plat-stubs) Platinum: its
# Stopwatch and Alarm Clock after the Secret Key, its line 19
DELIVERY_APP_LINE = 19 if version.PLATINUM else 18     # (plat-stubs: Platinum's bank has "We look forward..." at 18)
DELIVERY_LINES += tuple(('app', app) for app in version.POKETCH_APP_GIFTS)
# (postdex, 2026-11-09) Then the event Pokémon (version.EVENT_GIFTS: Mew, Celebi, Jirachi, Deoxys), each "received
# <species>!" (line 7; pearl_story.inc pl_DeliveryCanReceive puts the species in word 1)
DELIVERY_LINES += (7,) * len(version.EVENT_GIFTS)
DELIVERY_PARTY_FULL = 4               # "Your party is full, I'm afraid. I can't give this to you yet."


@handler('MysteryGiftGive')
def h_mystery_gift(tr, a, vals, name):
    """Pearl 0x23E MysteryGiftGive sub, ... (pokeplatinum scrcmd_mystery_gift.c, the same subcommands in Pearl: 0 load,
    1 a gift waiting? (var), 2 its type (var), 3 can it be received? (var), 4 give it, 5 / 6 the received / can't-receive
    line (bank var, line var: MessageFromBank shows it), 7 / 8 unload). Pearl's distribution events (the Member Card,
    Oak's Letter, the Azure Flute, the Manaphy Egg) are built in here, given by the same man with the same lines."""
    sub = vals[0]
    if sub in (0, 7, 8):
        return [f'// MysteryGiftGive {sub}: nothing to load or unload (the gifts are built in)']
    if sub == 1:
        return [f'pl_DeliveryWaiting {tr.var(vals[1])}  // MysteryGiftGive 1: a gift waiting?']
    if sub == 3:
        return [f'pl_DeliveryCanReceive {tr.var(vals[1])}  // MysteryGiftGive 3: can it be received?']
    if sub == 4:
        return ['pl_DeliveryGive  // MysteryGiftGive 4: the next gift']
    if sub == 5:
        return ['pl_BufferPlayerName 0  // MysteryGiftGive 5: the received line (MessageFromBank shows it)']
    if sub == 6:
        return ['// MysteryGiftGive 6: the can\'t-receive line (MessageFromBank shows it)']
    tr.job.stubs[f'{name} {sub}'] += 1
    return [f'pl_stub {name}  // MysteryGiftGive {", ".join(map(str, vals))}']


def delivery_message(tr, a, name):
    """The deliveryman's MessageFromBank after MysteryGiftGive 5 / 6 in the same block: Pearl's own line for the gift
    PVAR_DELIVERY points at (DELIVERY_LINES), or the full party's; None for any other MessageFromBank."""
    if name != 'MessageFromBank':
        return None
    got, cant = (same_block_before(tr, a, 'MysteryGiftGive', s) for s in (5, 6))
    if got is None and cant is None:
        return None
    kind, uid = speaker(tr, a, -1)
    out = switch_window(tr, kind, uid)

    def msg(n):
        if isinstance(n, tuple):        # (v101-story) a Pokétch app: line 18 with its name written in
            src = tr.job.gen4_text.bank(DELIVERY_BANK)[DELIVERY_APP_LINE]
            app = poketch_app_name(n[1])
            text = tr.job.gen4_text._STRVAR.sub(lambda mm: app if int(mm.group(2)) == 1 else mm.group(0), src)
            m = tr.job.line_text((DELIVERY_BANK, DELIVERY_APP_LINE, n), text)
            return (f'pl_msg_actor {m}, {uid}' if kind == 'actor' else f'pl_msg_{kind} {m}') + \
                f'  // Pearl bank {DELIVERY_BANK} line {DELIVERY_APP_LINE}: the Pokétch app {app}'
        m = tr.job.line_for(DELIVERY_BANK, n)
        return (f'pl_msg_actor {m}, {uid}' if kind == 'actor' else f'pl_msg_{kind} {m}') + \
            f'  // Pearl bank {DELIVERY_BANK} line {n}'
    if got is None:
        return out + [msg(DELIVERY_PARTY_FULL) + ' (only the Egg can be refused: the key items always fit)']
    for i, n in enumerate(DELIVERY_LINES[:-1]):
        out += [f'WorkCmpConst PVAR_DELIVERY, {i}', f'VMJumpIf CMP_NE, .Ldm{a:x}_{i}', msg(n),
                f'VMJump .Ldm{a:x}_end', f'.Ldm{a:x}_{i}:']
    return out + [msg(DELIVERY_LINES[-1]), f'.Ldm{a:x}_end:']


@handler('CheckDistributionEvent')
def h_distribution_event(tr, a, vals, name):
    """Pearl 0x28B CheckDistributionEvent event, var (pokeplatinum SystemVars_CheckDistributionEvent: Mystery Gift wrote a
    magic number when the event's item came: 0 Darkrai's Member Card, 1 Shaymin's Oak's Letter, 2 Arceus's Azure
    Flute). Built in: the deliveryman gave that item (PVAR_DELIVERY past its place in DELIVERY_LINES' order)."""
    return [f'pl_CheckDistributionEvent {vals[0]}, {tr.var(vals[1])}  // CheckDistributionEvent {vals[0]}: its item '
            f'came from the deliveryman']


@handler('SetHiddenLocation')
def h_hidden_location(tr, a, vals, name):
    """Pearl SetHiddenLocation place, 1 (pokeplatinum SystemVars_SetHiddenLocationMagic: 0 Fullmoon Island, 1 Newmoon
    Island, 2 Spring Path, 3 Seabreak Path). Pearl's map loader swaps matrix cells for a revealed place (pokediamond
    map_matrix.c sub_02034678 hides the Spring Path until it is set; sub_020346CC opens Route 224 to the Seabreak Path
    once it is): Black 2's map replacement does the same (patches/pearl_paths.py: a/0/1/0 entries on events
    PL_HIDDEN_EVENT_*, set here). The Town Map's hidden places (0, 1, and these on the map) are the Town Map's."""
    place = vals[0]
    if place in (2, 3):
        return [f'pl_SetHiddenLocation {place}  // SetHiddenLocation {place}: Black 2\'s map replacement']
    tr.job.approx['SetHiddenLocation 0/1 (Fullmoon / Newmoon Island on the Town Map: not drawn yet)'] += 1
    return [f'// SetHiddenLocation {", ".join(map(str, vals))}: the Town Map\'s hidden island (not drawn yet)']


@handler('CheckHasAllLegendaryTitansInParty')
def h_check_regis(tr, a, vals, name):
    """Pearl 0x26B (Snowpoint Temple B5F's statue: pokediamond CheckRegis = Regirock, Regice and Registeel in the
    party) = three of Black 2's PokePartyFindBySpecies."""
    return [f'pl_CheckHasAllLegendaryTitansInParty {tr.var(vals[0])}  // CheckRegis: Regirock, Regice, Registeel']


@handler('ShakeObject')
def h_shake_object(tr, a, vals, name):
    """Pearl 0x269 ShakeEvent object, ... (Snowpoint Temple B5F: Regigigas's statue shakes before it wakes). Black 2 has
    no command that shakes one person: the statue stays still (the cry and the battle follow as Pearl's)."""
    tr.job.approx['ShakeObject (Black 2 cannot shake one person: Regigigas\'s statue stays still)'] += 1
    return [f'// ShakeObject {", ".join(map(str, vals))}: nothing in Black 2 (no one-person shake)']


@handler('OpenShayminTabletNamingScreen')
def h_tablet_naming(tr, a, vals, name):
    """Pearl 0x271 WriteWhiteRockInscription var (Route 224's stone tablet: the name of the one the player thanks,
    typed on the naming screen; var 1 = nothing written). Black 2's word-set name input (CallWordSetPokeNameInput, as
    its Funfest quiz: the text into word buffer 1, which Pearl's next line reads, BufferTabletName 1), with the player's
    starter as the screen's icon. Black 2 has no save string for the inscription: the tablet's later line
    (BufferTabletName after the event) shows the player's name (pl_BufferTabletName)."""
    tr.job.approx['OpenShayminTabletNamingScreen (Black 2\'s name input; the inscription is not kept)'] += 1
    return [f'pl_OpenShayminTabletNamingScreen {tr.var(vals[0])}  // WriteWhiteRockInscription']


@handler('BufferTabletName')
def h_tablet_name(tr, a, vals, name):
    """Pearl 0x272 GetWhiteRockInscription buffer: right after the naming screen the typed name is already in word
    buffer 1 (pl_OpenShayminTabletNamingScreen); later (the tablet read after the event) Black 2 has no kept
    inscription: the player's name (h_tablet_naming)."""
    after_input = any(tr.job.pd.cmd_name(op) == 'OpenShayminTabletNamingScreen'     # (a few commands before)
                      for p, (e, op, args) in tr.d.insns.items() if 0 < a - p < 0x30)
    if after_input:
        return [f'// BufferTabletName {vals[0]}: the typed name is in word buffer 1 already']
    tr.job.approx['BufferTabletName (no kept inscription: the player\'s name)'] += 1
    return [f'pl_BufferPlayerName {vals[0]}  // BufferTabletName: no kept inscription in Black 2 (the player\'s name)']


@handler('FadeInBGM')
def h_fade_in_bgm(tr, a, vals, name):
    """Pearl 0x55 FadeInBgm frames (Route 224's Shaymin scene: the music faded out by FadeOutBGM comes back). Black 2's
    BGMFadeOut stops it: the zone's music again (BGMChangeMap)."""
    tr.job.approx['FadeInBGM (the zone\'s music again, no fade)'] += 1
    return [f'pl_PlayDefaultMusic  // FadeInBGM {vals[0]}: the zone\'s music again']


@handler('29F')
def h_shake(tr, a, vals, name):
    """Pearl 0x29F ShakeCamera kind (pokediamond: 0 a short shake, 1 the long one; the tremor of Lake Valor's explosion
    in the Canalave Library) = Black 2's event camera shake with its rumble, as its own quake scenes (global 10470)."""
    if vals[0] >= 0x4000:
        tr.job.stubs['ShakeCamera (the kind from a var)'] += 1
        return [f'pl_stub ShakeCamera  // {tr.var(vals[0])}']
    cam = getattr(tr, 'cam', None)
    if cam is None:
        return [f'pl_ShakeCamera {vals[0]}  // Pearl ShakeCamera {vals[0]}']
    # Black 2's shake shakes around the camera's bound target and binds it back after (ov036 FieldCameraShakeTask):
    # with the free camera unbound there is none, and the view jumped to the map's corner (the Canalave Library's
    # tremor, found in game 2026-10-25). So the view goes back to the player for the shake, then the free camera is
    # set up again where it was.
    return ['EvCameraReturn 1  // (the free camera ends for the shake: Black 2 shakes the bound camera)', 'EvCameraWait',
            'EvCameraRebind', 'EvCameraEnd', f'pl_ShakeCamera {vals[0]}  // Pearl ShakeCamera {vals[0]}',
            f'EvCameraInit  // the free camera again at ({cam[0]}, {cam[1]})', 'EvCameraUnbind',
            f'EvCameraMoveTo {CAM_ANGLE}, {cam_point(tr, cam[0], cam[1])}, 1', 'EvCameraWait']


@handler('2B6')
def h_obj_flag18(tr, a, vals, name):
    """Pearl 0x2B6 object, clear (pokediamond MapObject_ClearFlag18 on the object: after Riley's Egg, Riley's flag 18,
    a map-object state flag of Pearl's own) has nothing to do in Black 2."""
    tr.job.approx['2B6 (Pearl\'s map-object flag 18: nothing in Black 2)'] += 1
    return [f'// Pearl 0x2B6 {vals[0]}, {vals[1]}: Pearl\'s map-object flag 18, nothing in Black 2']


# ---- the briefcase (Black 2's three-ball screen, overlay 316: patches/pearl_starters.py shows Turtwig, Chimchar,
# Piplup left to right = Pearl's index 0/1/2) and the first battle
@handler('StartChooseStarterScene')
def h_starter(tr, a, vals, name):
    return ['pl_StartChooseStarterScene']


@handler('SaveChosenStarter')
def h_starter_save(tr, a, vals, name):
    return ['pl_SaveChosenStarter']


@handler('ReturnToField')
def h_return_field(tr, a, vals, name):
    if a in poke_select_fades(tr):
        return ['// RestoreOverworld: Black 2\'s party select reopened the field itself']
    if getattr(tr, 'after_region_map', False):            # (h_region_map)
        tr.after_region_map = False
        return ['// RestoreOverworld: Black 2\'s CallPlaceSelect reopened the field itself']
    tr.after_starter = True
    return ['pl_ReturnToField']


# ---- the party select (Pearl ChoosePokemonMenu + GetSelectedPartySlot, 2026-10-25 chapter 4b: the Veilstone massage
# girl, the Jubilife TV gallery, the Eterna condominiums' nickname checker, ...). Pearl always writes it as FadeScreen
# out, WaitFadeScreen, ChoosePokemonMenu (pokediamond ScrCmd_ChoosePokemonMenu: the party menu app), GetSelectedPartySlot
# var (the slot, 0xFF when cancelled), RestoreOverworld, FadeScreen in, WaitFadeScreen. Black 2's CallPokeSelect does
# the whole round trip itself (ov020 EventPokeSelect_Callback: fade out, field closed, the list, field reopened, fade
# in), so Pearl's fades and RestoreOverworld around it are dropped (a FieldOpen on an open field, a white fade-in on a
# shown field).
def poke_select_fades(tr):
    """Addresses of the FadeScreens and the RestoreOverworld of Pearl's party-select pattern in this file."""
    if getattr(tr, '_psel', None) is None:
        d, pd = tr.d, tr.job.pd
        tr._psel = set()
        nxt = {a: e for a, (e, op, args) in d.insns.items()}
        prv = {e: a for a, e in nxt.items()}
        name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
        for c, (e, op, args) in d.insns.items():
            if name(c) != 'SelectMoveTutorPokemon':
                continue
            w0 = prv.get(c)
            f0 = prv.get(w0)
            g = nxt.get(c)
            r = nxt.get(g)
            f1 = nxt.get(r)
            if (name(w0), name(f0), name(g), name(r), name(f1)) == ('WaitFadeScreen', 'FadeScreen', 'GetSelectedPartySlot',
                                                                  'ReturnToField', 'FadeScreen'):
                tr._psel |= {f0, r, f1}
        # the Day-Care Lady's (file 464): FadeScreen, WaitFadeScreen, SetVar, then a loop of OpenPartyMenuForDaycare /
        # GetDayCarePartyMenuResult (and the summary), then RestoreOverworld, ShowMoneyBox, FadeScreen
        for c, (e, op, args) in d.insns.items():
            if name(c) != 'OpenPartyMenuForDaycare':
                continue
            f0 = c
            for _ in range(4):
                f0 = prv.get(f0)
                if name(f0) == 'FadeScreen':
                    break
            r = c
            for _ in range(10):
                r = nxt.get(r)
                if name(r) == 'ReturnToField':
                    break
            f1 = r
            for _ in range(3):
                f1 = nxt.get(f1)
                if name(f1) == 'FadeScreen':
                    break
            if (name(f0), name(r), name(f1)) == ('FadeScreen', 'ReturnToField', 'FadeScreen'):
                tr._psel |= {f0, r, f1}
        # a move tutor's (2026-10-26, chapter 5b: Grandma Wilma; Route 228's): FadeScreen, WaitFadeScreen,
        # OpenMoveTutorMenu, CheckLearnedTutorMove, RestoreOverworld, FadeScreen (pl_OpenMoveTutorMenu stays on the
        # field and Black 2's forget-a-move screen fades and reopens it itself)
        for c, (e, op, args) in d.insns.items():
            if name(c) != 'OpenMoveTutorMenu':
                continue
            w0, k = prv.get(c), nxt.get(c)
            f0, r = prv.get(w0), nxt.get(k)
            f1 = nxt.get(r)
            if (name(f0), name(w0), name(k), name(r), name(f1)) == ('FadeScreen', 'WaitFadeScreen',
                                                                  'CheckLearnedTutorMove', 'ReturnToField',
                                                                  'FadeScreen'):
                tr._psel |= {f0, r, f1}
        # the Move Reminder's (2026-11-01: Pastoria): FadeScreen, WaitFadeScreen, OpenMoveReminderMenu,
        # CheckLearnedReminderMove, ReturnToField, FadeScreen: Black 2's screen fades and reopens the field itself
        for c, (e, op, args) in d.insns.items():
            if name(c) != 'OpenMoveReminderMenu':
                continue
            w0, k = prv.get(c), nxt.get(c)
            f0, r = prv.get(w0), nxt.get(k)
            f1 = nxt.get(r)
            if (name(f0), name(w0), name(k), name(r), name(f1)) == ('FadeScreen', 'WaitFadeScreen',
                                                                  'CheckLearnedReminderMove', 'ReturnToField',
                                                                  'FadeScreen'):
                tr._psel |= {f0, r, f1}
    return tr._psel


# ---- move tutors (2026-10-26, chapter 5b: Grandma Wilma's Draco Meteor, Route 210 N; Route 228's ultimate moves use
# the same commands): pearl_story.inc "move tutors"
TUTOR_BANK = 586        # Pearl's Move Reminder / tutor app's lines (the app Pearl's OpenMoveTutorMenu opens)
TUTOR_LINES = (1, 2, 3, 4, 5, 6, 7, 8)   # teach? / give up? / learned / trying (four moves) / poof / learned / stop? /
                                         # did not learn


@handler('GetPartyMonType')
def h_party_types(tr, a, vals, name):
    """Pearl 0x248 GetPartyMonTypes type1, type2, slot = Black 2's PokePartyGetTypes, the types numbered as Gen 4's."""
    return [f'pl_GetPartyMonTypes {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}']


@handler('CheckPartyMonHasMove')
def h_party_has_move(tr, a, vals, name):
    """Pearl 0x099 PartyMonHasMove result, move, slot (1 when that party Pokémon knows the move) = Black 2's
    PokePartyHasMove (the same order and answer; an Egg answers 0 in both)."""
    return [f'PokePartyHasMove {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}  // PartyMonHasMove']


@handler('OpenMoveTutorMenu')
def h_move_tutor(tr, a, vals, name):
    """Pearl 0x224 OpenMoveTutorMenu slot, move: the tutor app's choices on the field with its own lines (Pearl bank
    586), Black 2's forget-a-move screen for a Pokémon with four moves (pl_OpenMoveTutorMenu)."""
    lines = [tr.job.line_for(TUTOR_BANK, n) for n in TUTOR_LINES]
    tr.job.approx['OpenMoveTutorMenu (the tutor app\'s lines on the field; Black 2\'s forget-a-move screen)'] += 1
    return [f'pl_OpenMoveTutorMenu {tr.var(vals[0])}, {tr.var(vals[1])}, {", ".join(map(str, lines))}']


@handler('CheckLearnedTutorMove')
def h_move_tutor_result(tr, a, vals, name):
    """Pearl 0x225 CheckLearnedTutorMove var: 0 learned, 0xFF not (pl_OpenMoveTutorMenu's answer)."""
    return [f'pl_CheckLearnedTutorMove {tr.var(vals[0])}']


@handler('CheckHasLearnableReminderMoves')
def h_reminder_check(tr, a, vals, name):
    """Pearl 0x21F: var = what the Pokémon in a slot can remember, 0 = nothing (Black 2's own check)."""
    return [f'pl_MoveReminderCheck {tr.var(vals[0])}, {tr.var(vals[1])}']


@handler('OpenMoveReminderMenu')
def h_reminder_menu(tr, a, vals, name):
    return [f'pl_OpenMoveReminderMenu {tr.var(vals[0])}  // Black 2\'s remembering screen (it fades by itself)']


@handler('CheckLearnedReminderMove')
def h_reminder_result(tr, a, vals, name):
    return [f'pl_CheckLearnedReminderMove {tr.var(vals[0])}']


@handler('GetUnownFormsSeenCount')
def h_unown_forms(tr, a, vals, name):
    return [f'pl_GetUnownFormsSeenCount {tr.var(vals[0])}']


@handler('ShowDiplomaSinnoh')
def h_diploma_sinnoh(tr, a, vals, name):
    tr.after_diploma = True
    return ['FieldClose', 'CallPokedexDiploma 0, 0  // Pearl\'s Sinnoh diploma: Black 2\'s, its words Pearl\'s '
            '(data/script_text_overrides.json)']


@handler('ShowDiplomaNationalDex')
def h_diploma_national(tr, a, vals, name):
    tr.after_diploma = True
    return ['FieldClose', 'CallPokedexDiploma 1, 0  // Pearl\'s National Pokédex diploma: Black 2\'s']


def preview_waits(tr):
    """The WaitABPress right after a ShowPokemonPic: Black 2's preview waits for A or B itself."""
    if getattr(tr, '_pview', None) is None:
        d, pd = tr.d, tr.job.pd
        name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
        tr._pview = {e for c, (e, op, args) in d.insns.items() if name(c) == 'DrawPokemonPreview' and name(e) == 'WaitABPress'}
    return tr._pview


@handler('DrawPokemonPreview')
def h_pokemon_preview(tr, a, vals, name):
    """Pearl 0x208 ShowPokemonPic species, gender: Black 2's own Pokémon window (scrcmd_poke_disp.c), Black 2's picture of
    the Pokémon; it stays until A or B, so a message Pearl prints over the picture comes after it."""
    tr.job.approx['DrawPokemonPreview (Black 2\'s window and picture; it closes on A or B before any line)'] += 1
    return ['MsgWinCloseAll  // (as Black 2\'s own uses: its window needs the message window gone)',
            f'CallPokemonPreview {tr.var(vals[0])}, 0, {tr.var(vals[1])}, 0  // ShowPokemonPic']


@handler('RemovePokemonPreview')
def h_pokemon_preview_off(tr, a, vals, name):
    return ['// RemovePokemonPreview: Black 2\'s window closed itself']


@handler('WaitABPress')
def h_wait_ab(tr, a, vals, name):
    if a in preview_waits(tr):
        return ['// WaitABPress: Black 2\'s Pokémon window waits itself']
    return ['pl_WaitABPress']


@handler('FlickerObject')
def h_flicker(tr, a, vals, name):
    """Pearl 0x26A BlinkEvent uid, times, delay (pokeplatinum Task_FlickerMapObject): hidden and shown in turn."""
    return [f'pl_FlickerObject {vals[0]}, {vals[1]}, {vals[2]}']


@handler('SelectMoveTutorPokemon')
def h_choose_pokemon(tr, a, vals, name):
    return ['pl_ChoosePokemonMenu  // ChoosePokemonMenu: Black 2\'s party select (CallPokeSelect)']


def keep_stub(tr, a, vals, name):
    """The plain stub line (FileTr.translate's) for a command whose handler covers only some uses."""
    op = tr.d.insns[a][1]
    tr.job.stubs[name] += 1
    return [f'pl_stub {name}  // Pearl 0x{op:03X} {tr.job.pd.table[op]["name"]} {", ".join(map(str, vals))}: '
            f'not translated yet']


@handler('GetSelectedPartySlot')
def h_selected_slot(tr, a, vals, name):
    prev = next((x for x, (e, op, args) in tr.d.insns.items() if e == a), None)
    if prev is None or tr.job.pd.cmd_name(tr.d.insns[prev][1]) != 'SelectMoveTutorPokemon':
        return keep_stub(tr, a, vals, name)     # after another party app (OpenTradeScreen: NPC trades, not built)
    return [f'pl_GetSelectedPartySlot {tr.var(vals[0])}  // the slot, 255 when cancelled (as Pearl)']


# ---- the Day Care (2026-10-25, chapter 4b): Pearl's Day-Care Man and Lady (global scripts 9500 / 9501 = file 464) on
# Black 2's Day Care commands with Pearl's lines: macros in pearl_story.inc ("the Day Care"). The party-menu commands
# CountAliveMonsExcept, SetMonSummary and GetMonPartySlot are translated in the Day Care's file only (the Jubilife TV
# and the Contest Hall use them in other ways).
DAYCARE_FILE = 464


@handler('BufferDaycareMonNicknames', 'ResetDaycarePersonalityAndStepCounter', 'GiveEggFromDaycare')
def h_daycare0(tr, a, vals, name):
    return {'BufferDaycareMonNicknames': ['pl_BufferDaycareMonNicknames  // GetDaycarePokemonNames'],
            'ResetDaycarePersonalityAndStepCounter': ['DayCareResetSeed  // DeleteDaycareEgg: the Egg is not taken'],
            'GiveEggFromDaycare': ['DayCareBreed  // GiveDaycareEgg: the Egg into the party']}[name]


@handler('GetDaycareState', 'CheckDaycareHasEgg', 'GetDaycareCompatibilityLevel', 'CountAliveMonsAndBoxMons',
         'OpenPartyMenuForDaycare', 'StorePartyMonIntoDaycare')
def h_daycare1(tr, a, vals, name):
    if name == 'CheckDaycareHasEgg' and 2 in tr.levels(a):
        # Solaceon's zone init turns the Day-Care Man when an Egg waits; Black 2's Day Care commands are not allowed
        # there (EVCMD_PERM_TABLE), its own egg work is: 0x417F = 1 from the step an Egg appears (with room in the
        # party) until it is taken or declined (ov036 sodateya.c setPartyHasSpaceToConst)
        return [f'WorkSet {tr.var(vals[0])}, 0x417F  // Unk01BF (an Egg waits) in the zone init: Black 2\'s egg work']
    return [f'pl_{name} {tr.var(vals[0])}']


@handler('BufferDaycareGainedLevelsBySlot', 'BufferDaycarePriceBySlot', 'MoveMonToPartyFromDaycareSlot',
         'GetDayCarePartyMenuResult')
def h_daycare2(tr, a, vals, name):
    return [f'pl_{name} {tr.var(vals[0])}, {tr.var(vals[1])}']


@handler('BufferPartyMonNicknameReturnSpecies')
def h_daycare_nick(tr, a, vals, name):
    return [f'pl_BufferPartyMonNicknameReturnSpecies {tr.var(vals[1])}, {tr.var(vals[2])}  // (Pearl\'s first '
            f'argument {vals[0]} is unused)']


@handler('BufferDaycareNicknameLevelGender')
def h_daycare_menu_line(tr, a, vals, name):
    """Pearl buffers the nickname, the level and the gender symbol (a string in buffer vals[2]) for the next menu
    line; Black 2 has no gender-symbol word, so the gender goes into PL_DC_SEX and h_menu_add picks the line's copy with
    the symbol written in (as Black 2's own Day Care menu lines 34-36)."""
    tr.dc_sex_buf = vals[2]
    return [f'pl_BufferDaycareNicknameLevelGender {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[3])}']


@handler('SetMonSummary', 'GetMonPartySlot')       # (CountAliveMonsExcept: h_count_alive_except)
def h_daycare_party(tr, a, vals, name):
    if tr.f != DAYCARE_FILE:
        return keep_stub(tr, a, vals, name)
    return [f'// {name} {tr.var(vals[0])}: Black 2\'s Day Care list shows the summary itself (never reached: '
            f'GetDayCarePartyMenuResult gives 0)']


@handler('IncreasePartyMonFriendship')
def h_add_friendship(tr, a, vals, name):
    """Pearl AddPartyMonFriendship amount, slot (0x1BA; pokediamond scrcmd_party.c: plus the Soothe Bell, Luxury Ball
    and home-town bonuses) = Black 2's PokePartyAdjustHappiness slot, amount, 1 (add, capped at 255) without Pearl's
    bonuses (2026-10-25, chapter 4b: the Veilstone massage girl)."""
    tr.job.approx['IncreasePartyMonFriendship (Black 2\'s plain add: no Soothe Bell / Luxury Ball bonus)'] += 1
    return [f'PokePartyAdjustHappiness {tr.var(vals[1])}, {tr.var(vals[0])}, 1  // AddPartyMonFriendship']


@handler('TryGetRandomMassageGirlAccessory')
def h_massage_accessory(tr, a, vals, name):
    """Pearl Unk026C var: a random Contest Accessory the massage girl finds, or 0xFFFF (decomp resident/contest.c)."""
    return [f'pl_MassageGirlAccessory {tr.var(vals[0])}  // Pearl 0x26C']


@handler('GivePoffin')
def h_give_poffin(tr, a, vals, name):
    return [f'pl_PoffinGive {tr.var(vals[0])}, {", ".join(str(v) for v in vals[1:])}  // Pearl 0x289 (spicy .. sour, smoothness)']


@handler('CheckHasEmptyPoffinCaseSlot')
def h_poffin_room(tr, a, vals, name):
    return [f'pl_PoffinHasRoom {tr.var(vals[0])}  // Pearl 0x28A']


@handler('AddAccessory')
def h_add_accessory(tr, a, vals, name):
    return [f'pl_AddAccessory {tr.var(vals[0])}, {tr.var(vals[1])}  // Pearl AddAccessory (the Fashion Case)']


@handler('AddContestBackdrop')
def h_add_backdrop(tr, a, vals, name):
    return [f'pl_AddContestBackdrop {tr.var(vals[0])}  // Pearl AddContestBackdrop (the Fashion Case)']


@handler('GetPartyMonNature')
def h_mon_nature(tr, a, vals, name):
    """Pearl GetPartyMonNature result, slot (0x212) = Black 2's PokePartyGetParam result, slot, PKM_PARAM_NATURE (0x70):
    the same 25 natures (2026-10-25, chapter 4b: Solaceon's nature man)."""
    return [f'PokePartyGetParam {tr.var(vals[0])}, {tr.var(vals[1])}, 0x70  // GetPartyMonNature']


@handler('BufferNatureName')
def h_nature_name(tr, a, vals, name):
    return [f'WordSetLoadNature {vals[0]}, {tr.var(vals[1])}  // GetNatureName']


@handler('CheckIsDepartmentStoreRegular')
def h_dept_regular(tr, a, vals, name):
    """Pearl Unk027E (0x27E): 1 once the player has shopped at the Veilstone Department Store 5 times (a counter in
    Pearl's save); Black 2 keeps no such count: never a regular."""
    tr.job.approx['CheckIsDepartmentStoreRegular (never: Black 2 counts no Department Store visits)'] += 1
    return [f'WorkSetConst {tr.var(vals[0])}, 0  // Unk027E: the Department Store\'s regulars (not counted here)']


@handler('GetRandomSeenSpecies')
def h_news_species(tr, a, vals, name):
    """Pearl Unk0218 var (the News Press assignment): a random seen species (pearl_story.inc pl_GetRandomSeenSpecies;
    2026-10-25, chapter 4b)."""
    return [f'pl_GetRandomSeenSpecies {tr.var(vals[0])}  // Unk0218']


@handler('SetNewsPressDeadline')
def h_news_set(tr, a, vals, name):
    """Pearl Unk0219 days: the assignment's deadline in days (Pearl gives 1: today). Here PFLAG_NEWS_PRESS_TODAY,
    which Black 2 clears at midnight (data/pearl_story_ids.json new_flags)."""
    if vals[0] >= 0x4000:
        return keep_stub(tr, a, vals, name)
    return [f'{"FlagSet" if vals[0] else "FlagReset"} PFLAG_NEWS_PRESS_TODAY  // Unk0219 {vals[0]}: the deadline '
            f'is today']


@handler('GetNewsPressDeadline')
def h_news_get(tr, a, vals, name):
    return [f'FlagGet PFLAG_NEWS_PRESS_TODAY, {tr.var(vals[0])}  // Unk021A: days left (1 today, 0 after midnight)']


@handler('CheckMoney2')
def h_check_money_var(tr, a, vals, name):
    return [f'MoneyCheck {tr.var(vals[0])}, {tr.var(vals[1])}  // HasEnoughMoneyAddress (an amount in a var)']


@handler('RemoveMoney2')
def h_remove_money_var(tr, a, vals, name):
    return [f'MoneySub {tr.var(vals[0])}  // TakeMoneyAddress (an amount in a var)']


@handler('StartFirstBattle')
def h_first_battle(tr, a, vals, name):
    tr.job.approx['StartFirstBattle (a wild battle with Pearl\'s first-battle rules: no critical hits, FIGHT only; a '
                  'loss heals and the scene goes on)'] += 1
    if len(vals) == 1:          # Platinum's first battle is against the rival (a trainer id): a trainer battle with the same rules
        tr.last_battle = 'trainer'
        return [f'pl_StartFirstTrainerBattle {trainer(tr, vals[0])}']
    return [f'pl_StartFirstBattle {tr.var(vals[0])}, {tr.var(vals[1])}']


# ---- battles
@handler('StartCatchingTutorial')
def h_catch_tutorial(tr, a, vals, name):
    tr.job.approx['StartCatchingTutorial (Black 2\'s capture demo with Pearl\'s Pokémon, moves and lines: '
                  'patches/capture_demo.py; its fixed HP changes)'] += 1
    return ['pl_StartCatchingTutorial']


@handler('StartWildBattle')
def h_wild(tr, a, vals, name):
    tr.last_battle = 'wild'
    return end_free_camera(tr, 'a battle', a) + [f'pl_StartWildBattle {tr.var(vals[0])}, {tr.var(vals[1])}']


def insn_before(tr, a):
    """The name of the command just before a in its basic block (none when a is a label, an entry or a jump target)."""
    d = tr.d
    if getattr(tr, '_blocks', None) is None:
        same_block_before(tr, a, '', 0, limit=0)          # (builds tr._blocks)
    ends, targets = tr._blocks
    p = None if a in targets else ends.get(a)
    return None if p is None else tr.job.pd.cmd_name(d.insns[p][1])


def file_partner(tr):
    """The partner trainer this file sets Pearl's partner var 0x403F to (one known trainer), or None."""
    known = tr.job.ids.reg['trainers']
    vals = {args[1][1] for e, op, args in tr.d.insns.values()
            if tr.job.pd.cmd_name(op) == 'SetVarFromValue' and args[0][1] == PARTNER_VAR and args[1][0] != 'var'}
    vals = [v for v in vals if v < 0x4000 and str(v) in known]
    return vals[0] if len(vals) == 1 else None


@handler('StartTrainerBattle')
def h_trainer(tr, a, vals, name):
    tr.last_battle = 'trainer'
    if insn_before(tr, a) == 'SetHasPartner' and file_partner(tr) is not None:
        # Pearl's StartTrainerBattle with its "has partner" flag on is a battle at the partner's side against the two
        # (pokediamond ScrCmd_Unk00E5: the partner from var 0x403F): Iron Island's grunts with Riley (2026-10-25, ch6a)
        return [f'pl_StartTagBattle {tr.job.ids.trainer(file_partner(tr))}, {trainer(tr, vals[0])}, '
                f'{trainer(tr, vals[1])}  // StartTrainerBattle with the partner (SetHasPartner, var 0x403F)']
    return end_free_camera(tr, 'a battle', a) + [f'pl_StartTrainerBattle {trainer(tr, vals[0])}, {trainer(tr, vals[1])}']


def tag_partner_values(tr, a, var):
    """The values SetVarFromValue gives var on the way to a: in a's basic block and the subroutines it Calls before a
    (Jubilife: `Call` of the starter check that sets 0x8004 = 613-618), else anywhere in the file (0x8004 also holds
    items and other numbers elsewhere)."""
    d, pd = tr.d, tr.job.pd
    ends = {e: s for s, (e, op, args) in d.insns.items()}
    targets = {t for s, (e, op, args) in d.insns.items() for ty, t in args if ty == 'rel'}
    found, subs, b = set(), [], a
    for _ in range(16):
        p = None if b in targets else ends.get(b)
        if p is None:
            break
        e, op, args = d.insns[p]
        n = pd.cmd_name(op)
        if n == 'SetVarFromValue' and args[0][1] == var:
            found.add(args[1][1])
            break
        if n == 'Call':
            subs.append(args[0][1])
        b = p
    seen = set()
    while subs:
        s = subs.pop()
        if s in seen or s not in d.insns:
            continue
        seen.add(s)
        e, op, args = d.insns[s]
        if pd.cmd_name(op) == 'SetVarFromValue' and args[0][1] == var:
            found.add(args[1][1])
        subs += [t for ty, t in args if ty == 'rel']
        if pd.table[op]['flow'] not in ('end', 'jump', 'return'):
            subs.append(e)
    if found:
        return found
    return {args[1][1] for e, op, args in d.insns.values() if pd.cmd_name(op) == 'SetVarFromValue' and args[0][1] == var}


@handler('StartTagBattle')
def h_tag_battle(tr, a, vals, name):
    """Pearl 0x2A0 (pokediamond ScrCmd_Unk02A0: partner, opponent 1, opponent 2): you and a partner against two
    trainers (Jubilife after the Coal Badge: the counterpart against two Galactic grunts) = Black 2's
    CallTrainerMultiBattle partner, opponent 1, opponent 2 (as its Lacunosa scene). Pearl picks the partner by the
    starter in a var (0x8004 = 613-618): the var holds Pearl's trainer number, so the battle is a chain over the
    trainer numbers this file sets that var to (the last one without a check)."""
    tr.last_battle = 'trainer'
    partner, t1, t2 = vals
    o1, o2 = trainer(tr, t1), trainer(tr, t2)
    if partner < 0x4000:
        return end_free_camera(tr, 'a battle', a) + [f'pl_StartTagBattle {trainer(tr, partner)}, {o1}, {o2}']
    known = tr.job.ids.reg['trainers']
    values = sorted(v for v in tag_partner_values(tr, a, partner) if str(v) in known)
    if not values:
        tr.job.stubs['StartTagBattle (a partner from a var this file never sets)'] += 1
        return [f'pl_stub StartTagBattle  // partner {tr.var(partner)}: no trainer number set in this file']
    out = end_free_camera(tr, 'a battle', a) + \
        [f'// StartTagBattle {tr.var(partner)}, {t1}, {t2}: the partner by Pearl\'s trainer number in the var']
    for v in values[:-1]:
        out += [f'WorkCmpConst {tr.var(partner)}, {v}', f'VMJumpIf CMP_NE, .Ltag{a:x}_{v}',
                f'pl_StartTagBattle {trainer(tr, v)}, {o1}, {o2}', f'VMJump .Ltag{a:x}_end', f'.Ltag{a:x}_{v}:']
    return out + [f'pl_StartTagBattle {trainer(tr, values[-1])}, {o1}, {o2}', f'.Ltag{a:x}_end:']


@handler('PlayTrainerEncounterBGM')
def h_trainer_bgm(tr, a, vals, name):
    # Pearl 0xEA (pokediamond ScrCmd_Unk00EA: the trainer's class encounter music, sub_0204AD0C): Black 2's
    # TrainerBGMPlay, whose class song the decomp's PearlB2_EyeBGM gives (patches/battle_music.py: Pearl's with Sinnoh's
    # music); the Elite Four's and Cynthia's rooms
    return [f'pl_PlayTrainerEncounterBGM {trainer(tr, vals[0])}']


@handler('CheckWonBattle')
def h_won(tr, a, vals, name):
    import tower_script
    if tower_script.is_tower(tr):               # the Battle Subway keeps its own battle's setup: 1 = won
        return [f'BSubwayCmd_Tool 332, 0, 0, {tr.var(vals[0])}', 'BSubwayCmd_Tool 347, 0, 0, 0']
    return [f'pl_CheckWon{"Wild" if tr.last_battle == "wild" else ""}Battle {tr.var(vals[0])}']


@handler('BlackOutFromBattle')
def h_blackout(tr, a, vals, name):
    return [f'pl_BlackOutFrom{"Wild" if tr.last_battle == "wild" else ""}Battle']


# Pearl's 0xED (pokediamond ScrCmd_Unk00ED -> sub_020480C8): 0 if the battle was won or the Pokémon caught, else 1 (the
# player fled, a draw). Its 5 uses follow legendary battles (Valor/Acuity Cavern: a knocked-out Azelf/Uxie is gone for
# good; one the player ran from "disappeared deep into the cavern" and comes back). Pearl's 0x2BC (sub_020480D8: 0 only
# if caught) is pl_CheckDidNotCapture (Chapter 7, Palkia). (2026-10-26, ch6b, from the Chapter 7 agent's reading)
@handler('CheckLostBattle')
def h_lost_battle(tr, a, vals, name):
    return [f'pl_CheckLostBattle {tr.var(vals[0])}']



# ---- doors
@handler('LoadDoorAnimation')
def h_door_load(tr, a, vals, name):
    cx, cz, tx, tz, tag = vals
    out = []
    coords = []
    for c, t, w in ((cx, tx, 'PL_TMP'), (cz, tz, 'PL_TMP2')):
        if t < 0x4000:
            coords.append(str(c * 32 + t))
        else:                                   # a var tile: cell * 32 + the var, in a scratch work
            out += [f'WorkSetConst {w}, {c * 32}', f'WorkAdd {w}, {tr.var(t)}']
            coords.append(w)
    return out + [f'pl_LoadDoorAnimation {tag}, {coords[0]}, {coords[1]}  // the door at cell ({cx},{cz}) tile '
                  f'({tr.var(tx)},{tr.var(tz)})']


@handler('PlayDoorOpenAnimation', 'PlayDoorCloseAnimation', 'WaitForAnimation', 'UnloadAnimation')
def h_door(tr, a, vals, name):
    return [f'pl_{name} {vals[0]}']


# ---- more commands (2026-10-18: Chapter 1's)
for _pl, _macro, _fmt in [
        ('GetTimeOfDay', 'pl_GetTimeOfDay', ('var',)), ('GetLocalDexSeenCount', 'pl_GetLocalDexSeenCount', ('var',)),
        ('GetPartyMonSpecies', 'pl_GetPartyMonSpecies', ('var', 'var')),
        ('CountPartyNonEggs', 'pl_CountPartyNonEggs', ('var',)), ('CheckPartyPokerus', 'pl_CheckPartyPokerus', ('var',)),
        ('PlayPokecenterHealingAnimation', 'pl_PlayPokecenterHealingAnimation', ('var',)),
        ('OpenPokemonNamingScreen', 'pl_OpenPokemonNamingScreen', ('var', 'var')),
        ('CheckBadgeAcquired', 'pl_CheckBadgeAcquired', ('var', 'var')), ('GiveBadge', 'pl_GiveBadge', ('var',)),
        ('CountBadgesAcquired', 'pl_CountBadgesAcquired', ('var',)), ('PokeMartCommon', 'pl_PokeMartCommon', ('var',)),
        ('BufferSpeciesNameFromVar', 'pl_BufferSpeciesName', ('n', 'var')),
        ('Unk02CA', 'pl_BufferCounterpartStarterSpeciesName', ('n',))]:
    HANDLERS[_pl] = simple(_macro, *_fmt)


@handler('PokeMartSpecialties')
def h_mart_special(tr, a, vals, name):
    """Pearl's SpecialMart n (a Mart's second counter, the Herb Shop, the Veilstone Dept. Store's counters): Black 2's
    shop list n (patches/pearl_shops.py: list file n + 6 = Pearl's list n), through Black 2's Mart menu."""
    return [f'pl_PokeMartSpecial {tr.var(vals[0])}  // Pearl SpecialMart {tr.var(vals[0])}']


SEALS_LINE = ('Our Seals haven’t arrived.\\nPlease come again!')          # nor Ball Capsules (notes/OPEN_CONTENT.md)


@handler('PokeMartDecor', 'PokeMartSeal')
def h_mart_goods(tr, a, vals, name):
    """Pearl's GoodsMart n (decorations: Veilstone 4F): the Secret Bases' shop (notes/SECRET_BASES.md). SealsMart n (Seals:
    Sunyshore's market): Black 2 has no Seals, so the clerk says so (notes/OPEN_CONTENT.md) rather than sell a Mart's stock."""
    if name == 'PokeMartDecor':
        return [f'pl_GoodsMart {vals[0]}  // Pearl GoodsMart']
    tr.job.approx[f'{name} (Black 2 has no such goods: a closed line)'] += 1
    line = tr.job.line_text(('seals',), SEALS_LINE)
    return ['MsgWinCloseAll', f'pl_msg_talk {line}  // Pearl SealsMart {tr.var(vals[0])}: not built', 'pl_WaitButton',
            'pl_CloseMessage']


@handler('SendGoodToPC')
def h_send_good(tr, a, vals, name):
    """Pearl's GiveSecretBaseDecoration good, count, result (decomp resident/secret_base.c): a count of 1 everywhere."""
    return [f'pl_SendGoodToPC {tr.var(vals[0])}, {tr.var(vals[2])}']


@handler('CheckHasRoomForGoodsInPC')
def h_room_good(tr, a, vals, name):
    return [f'pl_CheckHasRoomForGoodsInPC {tr.var(vals[0])}, {tr.var(vals[2])}']


@handler('GetCapturedFlagCount')
def h_flag_count(tr, a, vals, name):
    return [f'pl_GetCapturedFlagCount {tr.var(vals[0])}']


@handler('BufferUndergroundGoodsName', 'GetDecorationNameWithArticle')
def h_good_word(tr, a, vals, name):
    return [f'pl_{name} {vals[0]}, {tr.var(vals[1])}']


# commands with nothing to do in Black 2 (each listed as approximated in the report, with why)
NOOP = {
    'GiveJournal': 'Black 2 has no journal',
    'SetInitialVolumeForSequence': 'Black 2 sets the volume itself',
    'Unused_06E': 'Pearl renames the follower 0xFE: Black 2\'s follower is 0xFE already',
    'LockObject': 'Black 2 pauses all actors (LockAll) only',
    'ReleaseObject': 'Black 2 pauses all actors (LockAll) only',
    'Dummy1F9': 'a debug command',
    'SetPlayerState': 'the player\'s avatar state (the Pokemon Center bow): Black 2 does its own',
    'ChangePlayerState': 'the player\'s avatar state (the Pokemon Center bow): Black 2 does its own',
    'SetHasPartner': 'Pearl\'s "partner walks along" flag 0x961: Black 2 pairs at SetMovementType 0x30',
    'CreateJournalEvent': 'Black 2 has no journal',
    'IncrementTrainerScore2': 'Pearl\'s trainer-card score (Black 2 keeps its own records)',
    # Platinum's (2026-11-02, plat-rooms; Pearl has none of these)
    'IncrementTrainerScore': 'Platinum\'s trainer-card score (Black 2 keeps its own records)',
    'AddToGameRecord': 'Platinum\'s records (money spent): Black 2 keeps its own',
    'AddToGameRecordBigValue': 'Platinum\'s records (money spent): Black 2 keeps its own',
    'SaveTVSegmentHomeAndManor': 'a TV segment: Pearl\'s TV segments are not built either',
    'SaveTVSegmentHomeAndManorNoFurniture': 'a TV segment: Pearl\'s TV segments are not built either',
    'InitPersistedMapFeaturesForVilla': 'the Villa\'s gimmick reads the furniture flags on every field load '
                                        '(b2tools/patches/platinum_villa.py)',
    '2CD': 'Platinum\'s dark blue fog over the room (overworld weather 26, the Eterna building\'s 4F): Black 2 has '
           'no such weather',
}


def h_noop(tr, a, vals, name):
    tr.job.approx[f'{name} ({NOOP[name]})'] += 1
    return [f'// {name} {", ".join(map(str, vals))}: nothing in Black 2 ({NOOP[name]})']


for _n in NOOP:
    HANDLERS[_n] = h_noop


@handler('CheckHasPartner')
def h_has_partner(tr, a, vals, name):
    """Pearl CheckHasPartner var (pokeplatinum ScrCmd_CheckHasPartner: the "partner walks along" flag 0x961): here
    whether a partner follows the player now, Black 2's pair flag (pearl_story.inc PL_FOLLOW_FLAG, set while one
    follows: Cheryl, Mira, Riley, Buck, Marley). Pearl's Rock Climb wall script refuses with a partner."""
    return [f'FlagGet PL_FOLLOW_FLAG, {tr.var(vals[0])}  // CheckHasPartner: 1 while a partner follows']


@handler('PlayHMCutIn')
def h_hm_cut_in(tr, a, vals, name):
    """Pearl's field-move cut-in (Rock Smash, Strength, ...) = Black 2's own steps round PlayHMCutInEffect (its global
    10000 L_005C, L_006C). The slot var comes from FindPartySlotWithMove: the Pokémon that knows the move, or with the HM
    rule the party's first that isn't an Egg (the decomp's resident/field_moves.c)."""
    return [f'pl_PlayHMCutIn {tr.var(vals[0])}']


@handler('UseRockClimb')
def h_rock_climb(tr, a, vals, name):
    """Pearl UseRockClimb slot (pokeplatinum ScrCmd_UseRockClimb -> ov5 FieldTask_StartUseRockClimb, the same in
    Pearl): the Pokemon's cut-in, then the player hops onto the wall ahead, walks fast across it and hops off (Pearl's
    task: JUMP_NEAR_FAST, WALK_FAST while the tile ahead is a climb tile, JUMP_NEAR_FAST). Black 2 has no climb tiles:
    the zone's climb starts (data/pearl_rock_climb.json, b2tools/rock_climb.py) are compared with the player's tile and
    facing, and the matching one's moves run, after Black 2's cut-in (pl_PlayHMCutIn). Nowhere else (the sign read
    sideways) nothing moves."""
    import pearl_events
    ends = pearl_events.rock_climb_ends(tr.job.zone['name'])
    tr.job.approx['UseRockClimb (the climb: hop, fast walks, hop, by data/pearl_rock_climb.json)'] += 1
    base = f'{tr.label(a)}_rc'
    out = [f'// UseRockClimb {tr.var(vals[0])}: {len(ends)} climb starts in this zone',
           f'pl_PlayHMCutIn {tr.var(vals[0])}',
           'pl_GetPlayerMapPos PL_TMP, PL_TMP2', 'pl_GetPlayerDir PL_TMP3']
    for k, r in enumerate(ends):
        (x, z), d = r['stand'], r['dir']
        out += [f'WorkCmpConst PL_TMP, {x}', f'VMJumpIf CMP_NE, {base}{k}_next',
                f'WorkCmpConst PL_TMP2, {z}', f'VMJumpIf CMP_NE, {base}{k}_next',
                f'WorkCmpConst PL_TMP3, {d}', f'VMJumpIf CMP_NE, {base}{k}_next',
                f'pl_ApplyMovement PL_PLAYER, {base}{k}  // from {tuple(r["stand"])} to {tuple(r["land"])}',
                'pl_WaitMovement', f'VMJump {base}_end', f'{base}{k}_next:']
    out += [f'VMJump {base}_end']
    for k, r in enumerate(ends):
        out += ['.balign 4, 0', f'{base}{k}:'] + [f'    Move {c}, {n}' for c, n in r['moves']] + ['    MoveEnd']
    return out + [f'{base}_end:']


@handler('StartDestroyObstacleAnimation')
def h_destroy_anim(tr, a, vals, name):
    """Pearl's rock/tree breaking animation (pokeplatinum ScrCmd_StartDestroyObstacleAnimation: obstacle, result var)
    sets its var when the animation is over, and the scripts wait for that (Roark's Rock Smash in Oreburgh Mine loops
    until it is non-zero: the game hung there, found in game 2026-10-19). Black 2 has no such animation here: the var
    is set at once, and the script removes the object itself."""
    tr.job.approx[f'{name} (no breaking animation: done at once)'] += 1
    return [f'// StartDestroyObstacleAnimation {vals[0]}: no animation in Black 2',
            f'pl_SetVarFromValue {tr.var(vals[1])}, 1  // the animation is "over" at once (the script waits for it)']


def partner_stays(tr, uid):
    """Whether a partner (SetMovementType uid, 0x30 with var 0x403F) stays in its zone as its own NPC when it stops
    following: the file gives it another movement type right after ClearHasPartner (Riley at Iron Island: "Are you
    going back?" and the grunts; Mira, Marley, Buck the same) and never makes it persistent (Cheryl's file does:
    SetObjectFlagIsPersistent, the rule before). 2026-10-25, ch6a: Riley vanished (pl_follow_leave deleted 0xFE)"""
    names = {a: tr.job.pd.cmd_name(op) for a, (e, op, args) in tr.d.insns.items()}
    if any(n == 'SetObjectFlagIsPersistent' and tr.d.insns[a][2][0][1] == uid for a, n in names.items()):
        return False
    for a, n in names.items():
        if n != 'ClearHasPartner':
            continue
        nxt = tr.d.insns.get(tr.d.insns[a][0])
        if nxt and tr.job.pd.cmd_name(nxt[1]) == 'SetMovementType' and nxt[2][0][1] == uid \
                and nxt[2][1][1] != FOLLOW:
            return True
    return False


@handler('ClearHasPartner')
def h_clear_partner(tr, a, vals, name):
    """Pearl's "partner" flag off. If the same script makes someone follow again later (Route 201: Barry blocks the
    way back), the follower only stops for the scene; a partner that stays in its zone (partner_stays) stops following
    and is its own NPC again; else (Lake Verity: the follower stays behind) Black 2's follower ends and leaves the
    map."""
    nxt = tr.d.insns.get(tr.d.insns[a][0])
    if nxt and tr.job.pd.cmd_name(nxt[1]) == 'SetMovementType' and nxt[2][1][1] != FOLLOW \
            and nxt[2][0][1] in tr.follow_uids and partner_stays(tr, nxt[2][0][1]):
        return ['pl_follow_end  // ClearHasPartner: the partner stops following and stays here (its own NPC again)']
    seen, todo = set(), list(tr.succ(a))
    while todo:
        b = todo.pop()
        if b in seen or b not in tr.d.insns:
            continue
        seen.add(b)
        e, op, args = tr.d.insns[b]
        if tr.job.pd.cmd_name(op) == 'SetMovementType' and args[1][1] == FOLLOW:
            return ['pl_follow_hold_any  // ClearHasPartner: the follower stops while the scene moves it']
        todo += tr.succ(b)
    return ['pl_follow_leave  // ClearHasPartner: the follower stays behind']


MOVEMENT_TYPE_ZONES = {'MAP_CANALAVE_SAILOR_ELDRITCH_HOUSE'}   # where pl_SetObjectEventMovementType is used so far


@handler('SetObjectEventMovementType')
def h_set_obj_move(tr, a, vals, name):
    import pearl_events
    uid, t = vals
    o = tr.job.objects.get(uid) if tr.mode != 'common' else None
    same = o is not None and t < 0x4000 and pearl_events.b2_move(o['movement_type']) == pearl_events.b2_move(t)
    if same or tr.job.zone['name'] not in MOVEMENT_TYPE_ZONES:
        tr.job.approx['SetObjectEventMovementType (Black 2 cannot change an NPC\'s movement before it appears: it keeps '
                      'its own' + (')' if not same else '; here the same anyway)')] += 1
        return [f'// SetObjectEventMovementType {uid}, {tr.var(t)}: Black 2 has no command for it (the NPC keeps its own'
                f'{", the same" if same else ""})']
    # The person's template, before the zone's people appear (the zone init), as Pearl's: decomp resident/leftovers.c
    # (2026-11-01: Eldritch's boy lay on his bed turning on the spot, with Pearl's wander on a tile he can't leave)
    move = pearl_events.b2_move(t) if t < 0x4000 else None
    if move is None:
        tr.job.approx['SetObjectEventMovementType (a movement Black 2 lacks or in a var: the NPC keeps its own)'] += 1
        return [f'// SetObjectEventMovementType {uid}, {tr.var(t)}: no Black 2 movement (the NPC keeps its own)']
    return [f'pl_SetObjectEventMovementType {tr.var(uid)}, {move}  // Pearl movement {t}']


@handler('FindPartySlotWithMove')
def h_find_move(tr, a, vals, name):
    return [f'PokePartyHasMoveAny {tr.var(vals[0])}, {tr.var(vals[1])}  // FindPartySlotWithMove: the slot, 6 = none '
            f'(the same in both games)']


@handler('CheckPartyHasSpecies')
def h_has_species(tr, a, vals, name):
    return [f'PokePartyFindBySpecies {tr.var(vals[1])}, {tr.var(vals[0])}, PL_TMP  // CheckPartyHasSpecies (1 = yes)']


# ---- the Pokétch (notes/POKETCH.md): Pearl's commands are sub-commands of PearlB2's extension command 0x15F
# (notes/EXT_COMMAND.md; src/include/pearl_story.inc pl_EnablePoketch ...), the save and the screen in the decomp's
# src/pearlb2/poketch_itcm.c. Pearl's numbers: 0x131 EnablePoketch (GivePoketch), 0x132 CheckPoketchEnabled, 0x133
# RegisterPoketchApp, 0x134 CheckPoketchAppRegistered, 0x265 HidePoketch / 0x266 ShowPoketch (Pearl's flag 0x97C).
@handler('EnablePoketch', 'HidePoketch', 'ShowPoketch')
def h_poketch(tr, a, vals, name):
    return [f'pl_{name}']


@handler('RegisterPoketchApp')
def h_poketch_register(tr, a, vals, name):
    note = f'  // {poketch_app_name(vals[0])}' if vals[0] < NUM_POKETCH_APPS else ''
    return [f'pl_RegisterPoketchApp {tr.var(vals[0])}{note}']


@handler('CheckPoketchEnabled')
def h_poketch_enabled(tr, a, vals, name):
    return [f'pl_CheckPoketchEnabled {tr.var(vals[0])}']


@handler('CheckPoketchAppRegistered')
def h_poketch_check(tr, a, vals, name):
    note = f'  // {poketch_app_name(vals[0])}' if vals[0] < NUM_POKETCH_APPS else ''
    return [f'pl_CheckPoketchAppRegistered {tr.var(vals[0])}, {tr.var(vals[1])}{note}']


NUM_POKETCH_APPS = 25


# ---- Pal Park's migration and Catching Show (notes/PAL_PARK_MIGRATION.md): Pearl's commands are sub-commands 0x40-0x45
# of PearlB2's extension command 0x15F (notes/EXT_COMMAND.md; src/include/pearl_story.inc pl_SetClearInCatchingShowFlag
# ...; decomp src/pearlb2/resident/palpark.c). Pearl's numbers: 0x253 SetClearInCatchingShowFlag (0 start, 1 end),
# 0x254 CheckHasEnoughMonForCatchingShow, 0x255 MoveCatchingShowMonsToPCBoxes, 0x256 CalcCatchingShowPoints, 0x26E
# GetGBACartridgeVersion. In the gate, with nothing stocked and a GBA game in slot 2, the receptionist asks Pearl's
# migration question (b2tools/palpark_offer.py migrate_offer) before Pearl's "six are needed" line.
@handler('SetClearInCatchingShowFlag')
def h_catching_show_flag(tr, a, vals, name):
    return [f'pl_SetClearInCatchingShowFlag {tr.var(vals[0])}']


@handler('CheckHasEnoughMonForCatchingShow')
def h_catching_show_stock(tr, a, vals, name):
    import palpark_offer
    var = tr.var(vals[0])
    return [f'pl_CheckHasEnoughMonForCatchingShow {var}'] + palpark_offer.migrate_offer(tr.job, a, var)


@handler('MoveCatchingShowMonsToPCBoxes')
def h_catching_show_pc(tr, a, vals, name):
    return ['pl_MoveCatchingShowMonsToPCBoxes']


@handler('CalcCatchingShowPoints')
def h_catching_show_points(tr, a, vals, name):
    return [f'pl_CalcCatchingShowPoints {tr.var(vals[0])}, {tr.var(vals[1])}']


@handler('GetGBACartridgeVersion')
def h_gba_cartridge(tr, a, vals, name):
    return [f'pl_GetGBACartridgeVersion {tr.var(vals[0])}']


@handler('GetGameVersion')
def h_version(tr, a, vals, name):
    return [f'WorkSetConst {tr.var(vals[0])}, PEARLB2_GAME_VERSION  // GetGameVersion: the build\'s (patches/scripts.py)']


@handler('CheckNationalDexCompleted')
def h_natdex_done(tr, a, vals, name):
    return [f'PokeDexIsComplete {tr.var(vals[0])}, 1  // CheckNationalDexCompleted (Black 2\'s National Dex)']


@handler('CheckIsTodayPlayerBirthday')
def h_birthday(tr, a, vals, name):
    tr.job.approx['CheckIsTodayPlayerBirthday (0)'] += 1
    return [f'WorkSetConst {tr.var(vals[0])}, 0  // CheckIsTodayPlayerBirthday: not checked']


# Pearl's "step" flag 0x965 (ops 0x163-0x165: set when Barry starts following, read by his talk script): Black 2's
# 0x965 is its own (EVENT_FLAG_CONTINUE_SCRIPT), so a map-local flag of ours, PL_STEP_FLAG
@handler('SetStepFlag')
def h_step_set(tr, a, vals, name):
    return ['FlagSet PL_STEP_FLAG  // SetStepFlag (Pearl sys flag 0x965)']


@handler('CheckStepFlag')
def h_step_check(tr, a, vals, name):
    return [f'FlagGet PL_STEP_FLAG, {tr.var(vals[0])}  // CheckStepFlag (Pearl sys flag 0x965)']


# Pearl's "Strength is on" flag (ScrCmd_DoStrengthFunc 0x1CF, the boulder script 10002: 1 sets, 0 clears, 2 reads into
# a var; a map change clears it, pokeplatinum field_map_change_flags.c) is Black 2's flag 0x964 (2404): Black 2's own
# boulder script sets it, the field pushes a boulder only while it is set (ov036 fieldmap_event.c contactFlags) and
# every zone change clears it (ov012 zone_change.c)
B2_STRENGTH_FLAG = 2404


@handler('DoStrengthFunc')
def h_strength(tr, a, vals, name):
    op = vals[0]
    if op == 1:
        return [f'FlagSet {B2_STRENGTH_FLAG}  // GetSetStrength 1: Strength on (Black 2\'s flag 0x964, the push reads it)']
    if op == 0:
        return [f'FlagReset {B2_STRENGTH_FLAG}  // GetSetStrength 0: Strength off (Black 2\'s flag 0x964)']
    return [f'FlagGet {B2_STRENGTH_FLAG}, {tr.var(vals[1])}  // GetSetStrength 2: is Strength on (Black 2\'s flag 0x964)']


@handler('ClearStepFlag')
def h_step_clear(tr, a, vals, name):
    return ['FlagReset PL_STEP_FLAG  // ClearStepFlag (Pearl sys flag 0x965)']


@handler('GetSetNationalDexEnabled')
def h_natdex(tr, a, vals, name):
    mode, var = vals
    if mode == 1:
        return ['pl_SetNationalDex']
    return [f'pl_GetNationalDex {tr.var(var)}']


@handler('GetItemNamePlural')
def h_item_plural(tr, a, vals, name):
    tr.job.approx['GetItemNamePlural (the singular name: Black 2 has no plural)'] += 1
    return [f'pl_BufferItemName {vals[0]}, {tr.var(vals[1])}  // GetItemNamePlural']


@handler('SaveTVSegmentHiddenItem')
def h_tv_hidden(tr, a, vals, name):
    """Pearl 0x236 (file 374): a TV segment about the hidden item. No TV here; Black 2's own hidden items count the find
    in its record instead (global 2811: RecordAdd 44, the Medal Box's counter)."""
    return ['RecordAdd 44, 1  // SaveTVSegmentHiddenItem: Black 2\'s record of hidden items found']


@handler('CheckItemIsPlate')
def h_plate(tr, a, vals, name):
    if tr.job.name == 'GLOBAL_ITEMS':                # (b2tools/pearl_items.py: balls and hidden items give Plates)
        return [f'pl_CheckItemIsPlate {tr.var(vals[0])}, {tr.var(vals[1])}']
    tr.job.approx['CheckItemIsPlate (0: the item-get line of a non-plate)'] += 1
    return [f'WorkSetConst {tr.var(vals[1])}, 0  // CheckItemIsPlate {tr.var(vals[0])}']


# ---- plat-ch8 (2026-11-07): a Plate a person gives (Platinum: Route 217's hiker, the Icicle Plate; Oreburgh Mine B1F, the
# Flame Plate). Platinum's give-item script asks CheckItemIsPlate and then shows the next of the Plates' eight engraving
# lines (scripts_common CommonScript_DeterminePlateEngraving: VAR_NUM_PLATES_OBTAINED counts them, 1-8). The approximation
# above (0) skipped that in zone files: the hiker's Plate showed no engraving and wasn't counted, so the balls' Plates showed
# the lines one step early. Platinum runs the real check in every file, as the item balls do; for any other item it is 0,
# as before. Pearl and Diamond keep their 1.0's approximation.
if version.PLATINUM:
    @handler('CheckItemIsPlate')
    def h_plate_platinum(tr, a, vals, name):
        return [f'pl_CheckItemIsPlate {tr.var(vals[0])}, {tr.var(vals[1])}  // CheckItemIsPlate: Plates 298-313']
# ---- end plat-ch8


@handler('GetTrainerCardLevel')
def h_card_level(tr, a, vals, name):
    tr.job.approx['GetTrainerCardLevel (0: no trainer card stars in Black 2)'] += 1
    return [f'WorkSetConst {tr.var(vals[0])}, 0  // GetTrainerCardLevel']


# The National Pokédex at Champion (user 2026-10-26, DECISIONS: limited trading in a ROM hack): the checks that gate
# Oak's upgrade on the Sinnoh Pokédex seen also pass once the game-clear flag 2400 (Pearl's 0x964) is set; Oak's scene
# and every National Dex unlock then run as Pearl's. Pearl's other completion checks stay the true count: the
# Pokédex rating (Rowan's PC, file 376: it sets 0x110, which picks Rowan's "you've met every kind" line), the Grand
# Lake's diploma (file 384). (chapter 9a)
NATIONAL_DEX_AT_CHAMPION = {
    (990, 0x61): "Rowan's lab, Rowan's talk: the Sinnoh Pokédex seen -> Oak's National Pokédex scene",
    (977, 0x23): "Dawn / Lucas (global 10300: outside the lab after the Hall of Fame, and in it): 'Have you shown "
                 "your Pokédex to Prof. Rowan yet?'",
}


@handler('CheckLocalDexCompleted')
def h_dex_done(tr, a, vals, name):
    # (2026-10-20) the regional list is Pearl's Sinnoh one (patches/sinnoh_dex.py, its completion rule too)
    if (tr.f, tr.job.pd.pearl_addr(tr.f, a)) in NATIONAL_DEX_AT_CHAMPION:
        return [f'pl_CheckLocalDexCompletedOrChampion {tr.var(vals[0])}  // the National Pokédex at Champion '
                f'(NATIONAL_DEX_AT_CHAMPION)']
    return [f'pl_CheckLocalDexCompleted {tr.var(vals[0])}']


# ---- the Pokédex's counts and ratings (2026-10-20; pearl_story.inc "the Pokédex")
@handler('GetNationalDexSeenCount', 'GetNationalDexCaughtCount')
def h_dex_national(tr, a, vals, name):
    return [f'pl_{name} {tr.var(vals[0])}']


@handler('LoadPokedexRating')
def h_dex_rating(tr, a, vals, name):
    """Pearl 0x123 (GetDexEvaluationMessage mode, var): var = the line of Pearl's rating bank (335: Rowan 4-14, Oak
    19-39) for the count; the script then prints it with MessageVar. Here var = that line's number in this file."""
    mode, var = vals
    # ---- plat-fixes (2026-11-07): the version's lines and tiers (version.DEX_RATING; Platinum: Rowan 4-17, Oak 22-42)
    first, last, macro = version.DEX_RATING[1 if mode else 0]
    # ---- end plat-fixes
    lines = [tr.job.line_for(tr.bank, n) for n in range(first, last + 1)]
    return [f'pl_LoadPokedexRating{macro} {tr.var(var)}, {", ".join(map(str, lines))}  // Pearl bank {tr.bank} '
            f'lines {first}-{last}']


@handler('GetSwarmMapAndSpecies')
def h_swarm(tr, a, vals, name):
    """Pearl's daily swarm (decomp resident/wild.c): the map var gets the Black 2 zone (h_mapname)."""
    tr.job.swarm_map_var = vals[0]
    return [f'pl_GetSwarmInfo {tr.var(vals[0])}, {tr.var(vals[1])}']


@handler('EnableSwarms')
def h_enable_swarms(tr, a, vals, name):
    return ['pl_EnableSwarms']


# ---- Pearl's honey trees (common script 2008, the sign events of pearl_events.honey_tree_tiles; decomp resident/wild.c)
@handler('GetHoneyTreeStatus')
def h_honey_status(tr, a, vals, name):
    return [f'pl_GetHoneyTreeStatus {tr.var(vals[0])}']


@handler('SlatherHoneyTree')
def h_honey_slather(tr, a, vals, name):
    return ['pl_SlatherHoneyTree']


@handler('StartHoneyTreeBattle')
def h_honey_battle(tr, a, vals, name):
    return end_free_camera(tr, 'a battle', a) + ['pl_StartHoneyTreeBattle']


@handler('StopHoneyTreeShaking')
def h_honey_stop(tr, a, vals, name):
    return ['pl_StopHoneyTreeShaking']


# ---- Pearl's berry patches (global script 2800, the soil people of pearl_events.is_berry_patch; decomp resident/berry.c)
BERRY_FIELDS = {'GetBerryGrowthStage': 0, 'GetBerryItemID': 1, 'GetBerryMulchType': 2, 'GetBerryMoisture': 3,
                'GetBerryYield': 4}


@handler(*BERRY_FIELDS)
def h_berry_get(tr, a, vals, name):
    return [f'pl_GetBerry {BERRY_FIELDS[name]}, {tr.var(vals[0])}  // {name}']


@handler('SetBerryMulch')
def h_berry_mulch(tr, a, vals, name):
    return [f'pl_SetBerryMulch {tr.var(vals[0])}']


@handler('PlantBerry')
def h_berry_plant(tr, a, vals, name):
    return [f'pl_PlantBerry {tr.var(vals[0])}']


@handler('SetBerryWateringState')
def h_berry_water(tr, a, vals, name):
    """0: Pearl's watering starts (the player's pose and walking along the row: Black 2 has neither, the patch in front
    is watered); 1: it ends."""
    if vals[0] == 0:
        tr.job.approx['SetBerryWateringState (the patch in front is watered: no pose, no walking along the row)'] += 1
        return ['pl_WaterBerry']
    return ['// SetBerryWateringState 1: nothing to end']


@handler('HarvestBerry')
def h_berry_harvest(tr, a, vals, name):
    return ['pl_HarvestBerry']


@handler('BufferBerryName')
def h_berry_name(tr, a, vals, name):
    return [f'pl_BufferBerryName {vals[0]}, {tr.var(vals[1])}  // Pearl\'s count {tr.var(vals[2])}: its name has one form']


@handler('CheckPocketHasItems')
def h_pocket_items(tr, a, vals, name):
    if vals[0] != 4:
        tr.job.stubs['CheckPocketHasItems (a pocket other than the Berries)'] += 1
        return [f'pl_stub CheckPocketHasItems  // Pearl pocket {vals[0]}']
    return [f'pl_CheckBerriesInBag {tr.var(vals[1])}']


@handler('OpenBag')
def h_open_bag(tr, a, vals, name):
    """Pearl 0x178 ShowBagScreen 0 (Mulch) / 1 (Berries). Black 2's Bag in its returning mode: every pocket, opened on
    the one Pearl's lists; pl_GetBagSelection throws away what doesn't fit (Pearl's list has only those)."""
    tr.after_region_map = True                 # (the macro reopens the field: h_return_field)
    tr.job.approx['OpenBag (Black 2\'s Bag shows every pocket, opened on Pearl\'s)'] += 1
    return [f'pl_OpenBerryBag {3 if vals[0] else 0}']


@handler('GetSelectedItem')
def h_selected_item(tr, a, vals, name):
    return [f'pl_GetBagSelection {tr.var(vals[0])}']


@handler('BufferMapName')
def h_mapname(tr, a, vals, name):
    n, m = vals
    if m < 0x4000:
        b2 = tr.job.pd.b2_zone.get(m)
        if b2 is not None:
            return [f'pl_BufferMapName {n}, {b2}  // Pearl map {m}']
    if m == getattr(tr.job, 'swarm_map_var', None):   # (pl_GetSwarmInfo: already a Black 2 zone)
        return [f'pl_BufferMapName {n}, {tr.var(m)}  // the swarm\'s place']
    tr.job.approx['BufferMapName (a Pearl map from a var: this zone\'s name)'] += 1
    return [f'WordSetPlaceName {n}, {tr.job.pd.b2_zone.get(tr.job.zone["id"], 0)}  // BufferMapName {n}, {tr.var(m)}']


# ---- Amity Square (Pearl script file 266, 2026-10-25; pearl_story.inc "Amity Square"): the walk with a Pokémon. The
# receptionists at the gates (triggers (12, 46) / (51, 46) on var 0x4099 = 0) offer each allowed Pokémon of the party in
# turn, heal the party, place its object behind the player, start Pearl's step count and pick the first find; the
# follower is Black 2's (SetMovementType 0x30); the triggers one tile south (var 0x4099 = 1) end the walk. Talking to
# the follower after 200 steps gives the find.
AMITY = 'MAP_AMITY_SQUARE'
AMITY_FIND_KIND = 0x409B                       # Pearl's kind of the next find (P266_0858: 0 a Berry, 1 an Accessory)


@handler('ClearAmitySquareStepCount')
def h_amity_clear_steps(tr, a, vals, name):
    return ['pl_ClearAmitySquareStepCount  // Pearl 0x215: Black 2\'s step counter from 0']


@handler('GetAmitySquareStepCount')
def h_amity_steps(tr, a, vals, name):
    return [f'pl_GetAmitySquareStepCount {tr.var(vals[0])}  // Pearl 0x216']


@handler('CalcAmitySquareFoundAccessory')
def h_amity_accessory(tr, a, vals, name):
    """Pearl's Accessory for the next find (by species): Pearl's table and chances (the user, 2026-11-01, replacing the
    Berries-only decision of 2026-10-25). Platinum's own table and pools (amity_platinum): in the script."""
    if version.PLATINUM:
        return amity_platinum(tr, a, tr.var(vals[0]), tr.var(vals[1]))
    return [f'pl_AmityAccessory {tr.var(vals[0])}, {tr.var(vals[1])}  // Pearl 0x217']


# Platinum's Amity Square finds (pokeplatinum scrcmd_amity_square.c ScrCmd_CalcAmitySquareFoundAccessory; its table is the
# dump's 60 u16 at ROM 0xEFF84, checked in amity_platinum_table): six pools of ten Accessories, the column by a roll of 100
# (15, 15, 15, 15, 10, 10, 8, 5, 5, 2 %), the pool by the walking Pokémon. Pearl's compiled table (resident/contest.c) is
# Pearl's own rows by Pearl's species: Platinum's starters have pools of their own, so a Platinum build does it in the
# script (no C change; the resident code stays the same in every version).
AMITY_POOLS_PLATINUM = [('CHIMCHAR', 'MONFERNO', 'INFERNAPE'), ('PIPLUP', 'PRINPLUP', 'EMPOLEON'),
                        ('TURTWIG', 'GROTLE', 'TORTERRA'), ('PSYDUCK', 'BUNEARY', 'DRIFLOON'),
                        ('PIKACHU', 'CLEFAIRY', 'PACHIRISU', 'HAPPINY'), ('JIGGLYPUFF', 'TORCHIC', 'SKITTY', 'SHROOMISH')]
AMITY_UP_TO = (15, 30, 45, 60, 70, 80, 88, 93, 98, 100)
AMITY_TABLE_ROM = 0xEFF84


def amity_platinum_table():
    """Platinum's 6 x 10 Accessories (pokeplatinum's source, Pearl's numbers: the same constants), checked against the dump."""
    src = open(os.path.join(ROOT, 'external', 'pokeplatinum', 'src', 'scrcmd_amity_square.c')).read()
    block = src[src.index('sMonFindableAccessories[NUM'):src.index('BOOL ScrCmd_CalcAmitySquareFoundAccessory')]
    names = re.findall(r'ACCESSORY_\w+', block[block.index('{'):])
    acc = [l.strip() for l in open(os.path.join(ROOT, 'external', 'pokeplatinum', 'generated', 'accessories.txt'))
           if l.strip() and not l.startswith('#')]
    ids = [acc.index(n) for n in names]
    from gen4rom import Rom
    rom = Rom(version.WORLD_DUMP)
    assert bytes(rom.data[AMITY_TABLE_ROM:AMITY_TABLE_ROM + 120]) == struct.pack('<60H', *ids), \
        "Platinum's Amity Square table is not the dump's (pokeplatinum src/scrcmd_amity_square.c)"
    return [ids[r * 10:r * 10 + 10] for r in range(6)]


def amity_platinum(tr, a, dst, species):
    sp = {}
    for line in open(os.path.join(ROOT, 'external', 'pokebw2', 'generated', 'species.txt'), encoding='utf-8'):
        m = re.match(r'(SPECIES_\w+)', line.strip())
        if m: sp[m.group(1)] = len(sp)
    table = amity_platinum_table()
    out = [f'// CalcAmitySquareFoundAccessory {dst}, {species}: Platinum\'s pools (pearl_story AMITY_POOLS_PLATINUM)',
           'pl_GetRandom PL_TMP, 100']
    for p, names in enumerate(AMITY_POOLS_PLATINUM):
        for n in names:
            out += [f'WorkCmpConst {species}, {sp["SPECIES_" + n]}', f'VMJumpIf CMP_EQ, .Lam{a:x}_{p}']
    out.append(f'VMJump .Lam{a:x}_0')                  # (anything else: the first pool, as Platinum's default)
    for p, row in enumerate(table):
        out.append(f'.Lam{a:x}_{p}:')
        for c, (up, acc) in enumerate(zip(AMITY_UP_TO, row)):
            out += [f'WorkSetConst {dst}, {acc}']
            if c < 9: out += [f'WorkCmpConst PL_TMP, {up}', f'VMJumpIf CMP_LT, .Lam{a:x}_end']
            else: out += [f'VMJump .Lam{a:x}_end']
    return out + [f'.Lam{a:x}_end:']


# Platinum's Amity Square gift man (pokeplatinum scrcmd_amity_square.c): a daily option of 16, a Berry (0-8) or an Accessory
@handler('CalcAmitySquareBerryAndAccessoryManOptionID')
def h_amity_gift_roll(tr, a, vals, name):
    return [f'pl_GetRandom {tr.var(vals[0])}, 16  // Platinum 0x2DF: the gift man\'s option of the day']


@handler('GetAmitySquareBerryOrAccessoryIDFromMan')
def h_amity_gift_id(tr, a, vals, name):
    return [f'pl_AmityGiftId {tr.var(vals[0])}, {tr.var(vals[1])}  // Platinum 0x2E1: the option\'s Berry or Accessory']


@handler('CheckAmitySquareManGiftIsAccessory')
def h_amity_gift_kind(tr, a, vals, name):
    return [f'pl_AmityGiftIsAccessory {tr.var(vals[0])}, {tr.var(vals[1])}  // Platinum 0x2E0: 1 = an Accessory']


@handler('32D', '338', '32E', '339')
def h_amity_hut_objects(tr, a, vals, name):
    """Platinum's Amity Square huts (a step into one fades and moves the player and the follower to another): 0x32D keeps
    every other person drawn (MAP_OBJ_STATUS_13) at the player's height while the map round them reloads, 0x338 the gift
    man at a height by his column, 0x32E / 0x339 let go (pokeplatinum ov5_021F6454.c). Black 2 keeps Amity Square's 2 x 2
    chunks loaded whole and every person on its own tile's height: nothing to do. (The walking Pokémon, object 5, follows
    as Black 2's 0xFE: the scene's ApplyMovement 5 and SetPosition 5 move it as the follower, TR.follow_uids.)"""
    return [f'// {name}: Platinum keeps people drawn through the hut warp; Black 2 loads the 2 x 2 map whole']


@handler('GetCurrentSafariGameCaughtNum')
def h_safari_caught(tr, a, vals, name):
    """Platinum 0x31B: the Pokémon caught in this Safari Game (5 or more: the Matchup Checker); pl_SafariCaught counts
    the party and the boxes against the count pl_SafariCountStart kept."""
    return [f'pl_SafariCaught {tr.var(vals[0])}, PVAR_SAFARI_START_COUNT  // Platinum 0x31B GetCurrentSafariGameCaughtNum']


@handler('CanFitAccessory')
def h_can_fit_accessory(tr, a, vals, name):
    """Whether the Fashion Case takes it (Amity Square's find, gifts)."""
    return [f'pl_CanFitAccessory {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}  // Pearl 0x1D3']


@handler('27C')
def h_tv_amity(tr, a, vals, name):
    """Pearl's TV records (pokeplatinum ScrCmd_27C: 0 the walk's Pokémon, 1 a found item, 2 a found Accessory, for the
    "Amity Square Watch" programme). Black 2 has no Sinnoh TV."""
    tr.job.approx['27C (Pearl\'s TV records of Amity Square: no Sinnoh TV)'] += 1
    return [f'// 27C {", ".join(map(str, vals))}: Pearl\'s TV record of the walk; nothing in Black 2 (no Sinnoh TV)']


# ---- Pearl's free camera (AddFreeCamera x, z: a camera object on that tile; ApplyMovement 0xF1 walks it; RestoreCamera
# puts the view back on the player) -> Black 2's event camera, as HoennB2 ports Sapphire's camera object
# (scenes/emerald/em_ch10_lib.inc): EvCameraInit + EvCameraUnbind, EvCameraMoveTo pitch 9688, yaw 0, distance 0xed000
# (the field camera's own angle: 96 of Black 2's 120 uses) to the fx32 point looked at, EvCameraWait; back with
# EvCameraReturn, EvCameraRebind, EvCameraEnd. The camera's walk becomes one move to where the walk ends, over the walk's
# frames (Pearl's movement codes: frames a tile in data/pearl_movement.json). Lake Verity: Rowan and the counterpart
# talk on screen before the view comes back to the player and Barry (user 2026-10-19).
CAM_ANGLE = '9688, 0, 0xed000'
CAM_STEP = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'WEST': (-1, 0), 'EAST': (1, 0)}


def cam_point(tr, x, z):
    h = None
    if isinstance(x, int) and isinstance(z, int) and x < 0x4000 and z < 0x4000:
        h = heights().at(tr.job.zone, x, z)
    return f'{(x * 16 + 8) << 12}, {(h or 0) << 12}, {(z * 16 + 8) << 12}'


# Pearl's AddFreeCamera on the player's tile (GetPlayerMapPos just before): the tile the scene has the player on there,
# (Pearl script file, the command's address) -> (x, z), as scene_check plays the scene (2026-10-25, ch6a). Canalave
# Library 3F's lakes scene: its frame-table script runs on the one arrival, the stairs' foot (4, 3), then the player
# walks south 2, east 3, south 2. (Spear Pillar's four and Lake Acuity's start on triggers or arrivals of several
# tiles: no single tile, the camera stays on the player.)
CAMERA_AT_PLAYER = {(42, 0x0087): (7, 7)}
# The same where the scene starts on one of a few tiles (2026-10-26, ch6b): the free camera starts where the field's
# camera is (on the player: no cut) and its walks are counted from the tile given. Lake Acuity (Galactic)'s scene runs
# on the two arrivals (14, 50) / (15, 50) from Acuity Lakefront; its camera goes up 5 to Jupiter and Barry, so from
# (14, 50) it drifts one column right on the way up.
CAMERA_NEAR_PLAYER = {(351, 0x000E): (15, 50)}
# Where the free camera is when a subroutine walks it (the translator writes code in address order, so a subroutine
# after its caller's RestoreCamera would find no camera): (Pearl script file, ApplyMovement's address) -> tile. Lake
# Acuity (Galactic): the camera comes back down with Jupiter (Pearl's Mov_0234) from (15, 45).
CAMERA_MOVE_FROM = {(351, 0x0142): (15, 45), (351, 0x0160): (15, 45)}


@handler('AddFreeCamera')
def h_cam_add(tr, a, vals, name):
    x, z = vals
    pa = tr.job.pd.pearl_addr(tr.f, a)
    if (x >= 0x4000 or z >= 0x4000) and (tr.f, pa) in CAMERA_NEAR_PLAYER:
        tr.cam = CAMERA_NEAR_PLAYER[(tr.f, pa)]
        return [f'EvCameraInit  // AddFreeCamera {tr.var(x)}, {tr.var(z)} (the player\'s tile): Black 2\'s event camera '
                f'where the camera is, counted as {tr.cam}', 'EvCameraUnbind']
    if (x >= 0x4000 or z >= 0x4000) and (tr.f, pa) in CAMERA_AT_PLAYER:
        x, z = CAMERA_AT_PLAYER[(tr.f, pa)]
    elif (x >= 0x4000 or z >= 0x4000) and tr.f in CAMERA_PLAN_FILES and a in camera_plan(tr.job.pd, tr.f):
        tr.cam = planned_camera(tr, a) or PLAYER_CAM          # (camera_plan: where it is for each start tile)
        tr.cam_vars = (x, z)                                  # (the start tile's vars: planned_branches)
        return [f'EvCameraInit  // AddFreeCamera {tr.var(x)}, {tr.var(z)}: the player\'s tile (camera_plan); the '
                f'view stays where it is', 'EvCameraUnbind']
    elif x >= 0x4000 or z >= 0x4000:
        tr.job.stubs['AddFreeCamera (a tile from a var)'] += 1
        tr.cam_stubbed = True
        return [f'pl_stub AddFreeCamera  // {tr.var(x)}, {tr.var(z)}: the camera stays on the player']
    tr.cam = (x, z)
    return [f'EvCameraInit  // AddFreeCamera {x}, {z}: Black 2\'s event camera on that tile', 'EvCameraUnbind',
            f'EvCameraMoveTo {CAM_ANGLE}, {cam_point(tr, x, z)}, 1', 'EvCameraWait']


@handler('RestoreCamera')
def h_cam_restore(tr, a, vals, name):
    if getattr(tr, 'cam', None) is None and getattr(tr, 'cam_stubbed', False):
        return ['// RestoreCamera: the free camera was not made (its AddFreeCamera is a stub): the camera stayed']
    tr.cam = None
    return ['EvCameraReturn 1  // RestoreCamera: the view cuts back to the player', 'EvCameraWait', 'EvCameraRebind',
            'EvCameraEnd']


# ---- the free camera on the player's tile in scenes that start on several tiles (2026-10-26, chapter 7). Spear
# Pillar's scenes start on wide step triggers (5 tiles at the altar's foot, 3 at Barry's row), put the free camera on
# the player (AddFreeCamera with GetPlayerMapPos's vars) and walk it with a movement list per branch of the player's x
# (P230_0510: from x 29 north 6 east 2, from x 30 north 6 east 1, ...), so each walk ends on one tile whatever the
# start; the vistas' warps keep the start tile in vars 0x8000/0x8001 and the scene goes on there (continuation 16).
# camera_plan plays each scene of a file in CAMERA_PLAN_FILES from every tile of the triggers that start it, the
# player's tile and Pearl's vars followed through branches, calls and Warps (Pearl's script goes on after a Warp), and
# keeps where the free camera is after each AddFreeCamera / ApplyMovement 0xF1 for each start tile. A camera walk that
# ends on one tile from every start is Black 2's EvCameraMoveTo that tile; AddFreeCamera itself is EvCameraInit +
# EvCameraUnbind (the view stays where it is: on the player, Pearl's tile). Lake Acuity (Galactic)'s scene (file 351)
# is made the same way and can use a row here.
CAMERA_PLAN_FILES = {230}
if version.PLATINUM:                # (2026-11-02, plat-rooms) the Galactic HQ hall's speech (Platinum's file 1110: Looker
    CAMERA_PLAN_FILES |= {1110}     # and the player walk to z 12 or 13, the camera goes to Cyrus's stage and back)
# ---- plat-ch8 (2026-11-07): Acuity Lakefront's Barry (Platinum's file 385, CoordEvent_Rival on (310-311, 244)): the free
# camera starts on the player's tile (GetPlayerMapPos), goes north 6 to Barry at the lumpy rocks and back. Without a row
# its AddFreeCamera was a stub and the camera stayed: Barry spoke 7 tiles north, at the screen's top edge. Each start x
# gets its own walk (planned_branches). Platinum only: Pearl's file 385 is another zone.
if version.PLATINUM:
    CAMERA_PLAN_FILES |= {385}
# ---- end plat-ch8
_CAM_PLANS, _CAM_ACTIVE, _WARP_PLACES = {}, {}, {}
_COND = {0: (0,), 1: (1,), 2: (2,), 3: (0, 1), 4: (1, 2), 5: (0, 2)}


def move_delta(steps):
    """(dx, dz) a Pearl movement list moves its walker."""
    dx = dz = 0
    for cmd, n in steps:
        nm = (MOVEMENT.get(cmd) or {}).get('pearl_name', '')
        d = next((v for k, v in CAM_STEP.items() if nm.endswith('_' + k)), None)
        if d is None or nm.startswith(('FACE_', 'WALK_ON_SPOT', 'JUMP_ON_SPOT')):
            continue
        k = 3 if nm.startswith('JUMP_FARTHER') else 2 if nm.startswith('JUMP_FAR') else \
            1 if nm.startswith(('WALK_', 'RUN_', 'JUMP_NEAR')) else 0
        dx, dz = dx + d[0] * k * n, dz + d[1] * k * n
    return dx, dz


def camera_plan(pd, f):
    """{address of an AddFreeCamera or ApplyMovement 0xF1 in Pearl file f: {start tile: the camera's tile after it}}."""
    if f in _CAM_PLANS:
        return _CAM_PLANS[f]
    d = pd.disasm(f)
    starts = []
    for z in pd.zones:
        if z['scripts'] == f:
            for c in pd.events(z)['coord_events']:
                if 1 <= c['script'] <= len(d.entries):
                    starts += [(d.entries[c['script'] - 1], (x, zz)) for x in range(c['x'], c['x'] + c['width'])
                               for zz in range(c['z'], c['z'] + c['length'])]
    plan, active, places = collections.defaultdict(dict), set(), collections.defaultdict(set)
    for entry, tile in starts:
        todo, seen = [(entry, (), tile, {}, None, None)], set()
        while todo:
            a, stack, player, vs, cam, cmp = todo.pop()
            for _ in range(4000):
                key = (a, stack, player, tuple(sorted(vs.items())), cam, cmp)
                if a not in d.insns or key in seen:
                    break
                seen.add(key)
                if cam is not None:
                    active.add(a)
                e, op, args = d.insns[a]
                nm, v = pd.cmd_name(op), [x[1] for x in args]
                val = lambda x: x if x < 0x4000 else vs.get(x)
                vs, nxt = dict(vs), e
                if nm in ('End', 'ReturnCommonScript'):
                    break
                if nm == 'Return':
                    if not stack:
                        break
                    nxt, stack = stack[-1], stack[:-1]
                elif nm == 'GoTo':
                    nxt = v[0]
                elif nm == 'Call':
                    nxt, stack = v[0], stack + (e,)
                elif nm in ('GoToIf', 'CallIf'):
                    go = (v[1], stack + ((e,) if nm == 'CallIf' else ()))
                    if cmp is None:                       # (not known: both ways)
                        todo.append((go[0], go[1], player, vs, cam, None))
                    elif cmp in _COND[v[0]]:
                        nxt, stack = go
                elif nm == 'CompareVarToValue':
                    x = vs.get(v[0])
                    cmp = None if x is None else (0 if x < v[1] else 1 if x == v[1] else 2)
                elif nm == 'CompareVarToVar':
                    x, y = vs.get(v[0]), vs.get(v[1])
                    cmp = None if x is None or y is None else (0 if x < y else 1 if x == y else 2)
                elif nm == 'GetPlayerMapPos':
                    vs[v[0]], vs[v[1]] = player
                elif nm == 'SetVarFromValue':
                    vs[v[0]] = v[1]
                elif nm == 'SetVarFromVar':
                    vs[v[0]] = vs.get(v[1])
                elif nm == 'AddVar' and vs.get(v[0]) is not None and val(v[1]) is not None:
                    vs[v[0]] += val(v[1])
                elif nm == 'Warp':                        # Pearl's script goes on there (a continuation)
                    player, cam = (val(v[2]), val(v[3])), None
                    places[a].add(player)
                elif nm == 'AddFreeCamera':
                    cam = (val(v[0]), val(v[1]))
                    plan[a][tile] = cam
                elif nm == 'RestoreCamera':
                    cam = None
                elif nm == 'ApplyMovement' and v[0] in (0xF1, 0xFF):
                    dx, dz = move_delta(movement_steps(pd, f, v[1]))
                    if v[0] == 0xFF and None not in player:
                        player = (player[0] + dx, player[1] + dz)
                    elif v[0] == 0xF1 and cam is not None and None not in cam:
                        cam = (cam[0] + dx, cam[1] + dz)
                        plan[a][tile] = cam
                else:                                     # any other command may write its vars
                    for ty, x in args:
                        if ty == 'var' and x >= 0x4000:
                            vs.pop(x, None)
                a = nxt
    _CAM_PLANS[f], _CAM_ACTIVE[f], _WARP_PLACES[f] = dict(plan), active, dict(places)
    return _CAM_PLANS[f]


PLAYER_CAM = (None, None)        # tr.cam: a free camera on the player's tile, not one tile from every start


def move_frames(steps):
    """Frames a Pearl movement list's walk takes (its walking steps: data/pearl_movement.json frames a tile)."""
    frames = 0
    for cmd, n in steps:
        per = re.search(r'(\d+) frames/tile', (MOVEMENT.get(cmd) or {}).get('note', ''))
        if per:
            frames += n * int(per.group(1))
    return frames


def cam_angle(tr):
    """EvCameraMoveTo's pitch, yaw and distance for a camera_plan walk: Black 2's camera 0 (distance 237) at the zone's
    own pitch, as the field camera is since 2026-10-26 (maplook 'tilt': Pearl's pitch for the zone's Pearl camera
    type, the overworld's for matrix 0), so the view does not tilt when the walk starts. (CAM_ANGLE is camera 0's own
    pitch, 9688.)"""
    import maplook
    z = tr.job.zone
    return f'{maplook.PEARL_CAMERAS[0 if z["matrix"] == 0 else z["camera"]][1]}, 0, 0xed000'


def end_free_camera(tr, why, a):
    """A camera_plan scene (CAMERA_PLAN_FILES) whose free camera is still out at a battle or a Warp (at a, in some
    start: camera_plan's _CAM_ACTIVE): Pearl rebuilds the field there (the camera is the player's again); Black 2's
    event camera is ended first."""
    if tr.f in CAMERA_PLAN_FILES and (camera_plan(tr.job.pd, tr.f) is not None) and a in _CAM_ACTIVE[tr.f]:
        tr.cam = None
        return [f'EvCameraReturn 1  // ({why}: the free camera ends first, as Pearl\'s field is rebuilt there)',
                'EvCameraWait', 'EvCameraRebind', 'EvCameraEnd']
    return []


def planned_camera(tr, a):
    """The one tile the free camera is on after the command at a in every start of camera_plan, or None."""
    if tr.f not in CAMERA_PLAN_FILES:
        return None
    ends = set(camera_plan(tr.job.pd, tr.f).get(a, {}).values())
    return ends.pop() if len(ends) == 1 and None not in next(iter(ends)) else None


def planned_branches(tr, a, frames=None):
    """A camera_plan walk that ends on another tile from each start (2026-11-02, plat-rooms: the Galactic HQ hall's speech
    starts at z 12 or 13, and Platinum's camera walks from there): when the starts differ only in z (or only in x) and
    the scene's AddFreeCamera took the start tile from vars (tr.cam_vars), a branch on that var for each start, each
    EvCameraMoveTo its own end. frames None: whether it applies (a list or None)."""
    plan = camera_plan(tr.job.pd, tr.f).get(a, {})
    cv = getattr(tr, 'cam_vars', None)
    if cv is None or len(plan) < 2 or None in plan or any(None in t for t in plan.values()):
        return None
    xs, zs = {t[0] for t in plan}, {t[1] for t in plan}
    k = 1 if len(xs) == 1 and len(zs) == len(plan) else 0 if len(zs) == 1 and len(xs) == len(plan) else None
    if k is None or cv[k] < 0x4000:
        return None
    if frames is None:
        return [True]
    out = [f'// ApplyMovement 0xF1 (the free camera): from each start its own end (camera_plan), by {tr.var(cv[k])}']
    for i, (start, end) in enumerate(sorted(plan.items())):
        out += [f'WorkCmpConst {tr.var(cv[k])}, {start[k]}', f'VMJumpIf CMP_NE, .Lcpb{a:x}_{i}',
                f'EvCameraMoveTo {cam_angle(tr)}, {cam_point(tr, end[0], end[1])}, {max(1, frames)}  // to {end}',
                f'VMJump .Lcpb{a:x}_end', f'.Lcpb{a:x}_{i}:']
    tr.cam = PLAYER_CAM
    return out + [f'.Lcpb{a:x}_end:', 'EvCameraWait']


@handler('ApplyMovement')
def h_move(tr, a, vals, name):
    if vals[0] == 0xF1 and tr.f in CAMERA_PLAN_FILES and a in camera_plan(tr.job.pd, tr.f):
        to = planned_camera(tr, a)
        frames = move_frames(tr.d.movement.get(vals[1]) or [])
        if to is None and planned_branches(tr, a):
            return planned_branches(tr, a, frames)
        if to is None:
            tr.job.approx['ApplyMovement on the free camera ending on several tiles (the camera stays)'] += 1
            return [f'// ApplyMovement 0xF1 (the free camera), {tr.label(vals[1])}: it ends on several tiles, the '
                    f'camera stays']
        tr.cam = to
        return [f'EvCameraMoveTo {cam_angle(tr)}, {cam_point(tr, to[0], to[1])}, {max(1, frames)}  // ApplyMovement '
                f'0xF1 {tr.label(vals[1])}: the free camera walks to {to} (camera_plan)', 'EvCameraWait']
    if vals[0] == 0xF1:
        cam = CAMERA_MOVE_FROM.get((tr.f, tr.job.pd.pearl_addr(tr.f, a))) or getattr(tr, 'cam', None)
        steps = tr.d.movement.get(vals[1]) if hasattr(tr.d, 'movement') else None
        if cam is None or steps is None:
            tr.job.approx['ApplyMovement on the free camera without AddFreeCamera here (the camera stays)'] += 1
            return [f'// ApplyMovement 0xF1 (the free camera), {tr.label(vals[1])}: the camera stays']
        x, z, frames = cam[0], cam[1], 0
        for cmd, n in steps:
            info = MOVEMENT.get(cmd) or {}
            nm, note = info.get('pearl_name', ''), info.get('note', '')
            d = next((v for k, v in CAM_STEP.items() if nm.endswith(k)), None)
            per = re.search(r'(\d+) frames/tile', note)
            if d and per and 'WALK' in nm:
                x, z, frames = x + d[0] * n, z + d[1] * n, frames + n * int(per.group(1))
            elif per:
                frames += n * int(per.group(1))
        tr.cam = (x, z)
        return [f'EvCameraMoveTo {CAM_ANGLE}, {cam_point(tr, x, z)}, {max(1, frames)}  // ApplyMovement 0xF1 '
                f'{tr.label(vals[1])}: the free camera walks to ({x}, {z})', 'EvCameraWait']
    if vals[0] in tr.follow_uids:
        return [f'pl_ApplyMovementF {vals[0]}, {tr.label(vals[1])}  // (the follower once it follows)']
    return [f'pl_ApplyMovement {actor(tr, vals[0])}, {tr.label(vals[1])}']


# ---- menus (Pearl's multiple-choice and list menus -> Black 2's list menu, ov036 scrcmd_menu.c): Pearl's "global"
# menus take their lines from bank 321 (pokediamond ov05_021E1AD8: NewMsgDataFromNarc 0x141), "local" ones from the
# script's bank; Black 2 shows lines of the script's own text file, so they are copied there. Black 2's menus open at the
# right edge (x = 31, as its own yes/no menus); Pearl's row is kept.
MENU_BANK = 321


@handler('InitGlobalTextMenu', 'InitLocalTextMenu', 'InitGlobalTextListMenu', 'InitLocalTextListMenu')
def h_menu_init(tr, a, vals, name):
    x, y, cursor, b_exits, var = vals
    tr.menu_bank = MENU_BANK if 'Global' in name else tr.bank
    tr.job.approx['menus (Black 2\'s list menu at the right edge)'] += 1
    # Black 2's flags byte is the list's "cancelable" (ov012 scrcmd_work.c InitListMenu -> ListMenuUI_Create); B writes
    # 0xFFFE, as Gen 4's. Pearl's canExitWithB goes straight in (1.0.1, found by v101-test: 1.0 wrote 0, so B never
    # closed a Pearl menu, e.g. the Trainers' School blackboard needed EXIT)
    return [f'ListMenu_AnchorTopRight 31, {y}, {cursor}, {1 if b_exits else 0}, {tr.var(var)}  // Pearl {name} {x}, {y}, '
            f'{cursor}, {b_exits}, {tr.var(var)}']


@handler('AddMenuEntryImm', 'AddMenuEntry', 'AddListMenuEntry')
def h_menu_add(tr, a, vals, name):
    # Pearl's AddListMenuEntry is line, alt text (255: none), index (pokeplatinum scrcmd.inc): the index is the third
    msg, value = vals[0], vals[2] if name == 'AddListMenuEntry' else vals[1]
    if msg >= 0x4000:
        tr.job.stubs[f'{name} (the line from a var)'] += 1
        return [f'pl_stub {name}  // line from {tr.var(msg)}: Black 2 menus take a fixed line']
    bank = getattr(tr, 'menu_bank', tr.bank)
    sex = getattr(tr, 'dc_sex_buf', None)
    mark = f'{{STRVAR_1 2, {sex}}}' if sex is not None else None
    src = tr.job.gen4_text.bank(bank)[msg]
    apps = {i: v for i, v in tr.app_bufs(a).items() if v[0] in WRITTEN_IN_MENUS and not isinstance(v[1], tuple)
            and i in tr.job.gen4_text.buffers(src)}
    if apps:                                    # (Platinum: the Villa's prices, written into each entry: NAME_SOURCES)
        src = tr.job.gen4_text._STRVAR.sub(lambda m: source_name(*apps[int(m.group(2))]) if int(m.group(2)) in apps
                                           else m.group(0), src)
        apps = tuple(sorted(apps.items()))
    if mark and mark in src:                    # a Day Care line with the gender symbol (h_daycare_menu_line)
        tr.dc_sex_buf = None
        # Black 2's list menu sizes its window by the text and ignores a cursor move: Pearl's {CURSOR_X 90}Lv. 100 fell
        # outside the window (seen in game 2026-10-25); Black 2's own Day Care lines put a space there
        src = re.sub(r'\{CURSOR_X \d+\}', ' ', src)
        out, end = [], f'{tr.prefix}_{a:04X}_SexDone'
        for k, sym in ((1, '♂'), (2, '♀')):
            out += [f'WorkCmpConst PL_DC_SEX, {k}', f'VMJumpIf CMP_EQ, {tr.prefix}_{a:04X}_Sex{k}']
        out += [f'ListMenuAdd {tr.job.line_text(("menu_sex", bank, msg, 0), src.replace(mark, ""))}, 65535, '
                f'{tr.var(value)}  // Pearl {name} {msg}, {tr.var(value)} (no gender)', f'VMJump {end}']
        for k, sym in ((1, '♂'), (2, '♀')):
            out += [f'{tr.prefix}_{a:04X}_Sex{k}:',
                    f'ListMenuAdd {tr.job.line_text(("menu_sex", bank, msg, k), src.replace(mark, sym))}, 65535, '
                    f'{tr.var(value)}  // ({sym})', f'VMJump {end}']
        return out + [f'{end}:']
    cursor = re.search(r'\{CURSOR_X (\d+)\}', src)
    if cursor:
        # Black 2's list menu sizes its window by the text and ignores a cursor move, so the column after it was cut
        # off (the Exchange's "16B", seen in game 2026-11-01): spaces before the move count and draw nothing
        # A buffered name counts as empty (v101-test, 2026-11-08): the window must fit the list's shortest names too;
        # with the longest prize name ("Power Bracer") the BP Exchange's TM list, short names, cut its prices off
        font = b2font.load(0)
        left = re.sub(r'\{STRVAR_1 [^}]*\}', '', src[:cursor.start()])
        pad = max(0, int(cursor.group(1)) - font.width(left))
        src = src[:cursor.start()] + ' ' * -(-pad // font.width(' ')) + src[cursor.start():]
        line = tr.job.line_text(('menu_column', bank, msg) + ((apps,) if apps else ()), src)
    elif apps:
        line = tr.job.line_text(('menu_written_in', bank, msg, apps), src)
    else:
        line = tr.job.line_for(bank, msg)
    return [f'ListMenuAdd {line}, 65535, {tr.var(value)}  // Pearl {name} {msg}, {tr.var(value)}']


@handler('ShowMenu', 'ShowListMenu')
def h_menu_show(tr, a, vals, name):
    return ['ListMenuShow']


# ---- plat-ch2 (2026-11-07): Platinum's chapter 2 ---------------------------------------------------------------------
if version.MENU_COLUMNS:            # (v101-story: Pearl and Diamond too, version.MENU_COLUMNS)
    @handler('ShowMenuMultiColumn')
    def h_menu_columns(tr, a, vals, name):
        """0x048 ShowMenuMultiColumn columns (pokeplatinum scrcmd ShowMenuMultiColumn): the Trainers' School blackboard,
        the six status lessons in two columns. Black 2's list menu has one column: the same entries in one list. Left a
        stub (Pearl's 1.0 has it), the menu was never shown and the script read the old answer and went round again:
        the player could not leave the blackboard."""
        tr.job.approx['ShowMenuMultiColumn (Black 2\'s list menu: one column)'] += 1
        return [f'ListMenuShow  // ShowMenuMultiColumn {vals[0]}: one column']


if version.PLATINUM:
    @handler('Unk02CF')
    def h_menu_side(tr, a, vals, name):
        """0x33A SetMenuXOriginSide side (pokeplatinum ScrCmd_SetMenuXOriginSide; SetMenuXOriginToRight = 1): the menu
        just made opens at the screen's right edge. Black 2's list menus here open there already
        (ListMenu_AnchorTopRight, h_menu_init); a left one (0) stays at the right."""
        if vals[0] != 1:
            tr.job.approx['SetMenuXOriginSide left (Black 2\'s list menu stays at the right edge)'] += 1
        return [f'// SetMenuXOriginSide {vals[0]}: Black 2\'s list menu is at the right edge already']

    @handler('AddCameraOverrideObject', 'RemoveCameraOverrideObject')
    def h_camera_override(tr, a, vals, name):
        """0x308 AddCameraOverrideObject x, z / 0x309 RemoveCameraOverrideObject (pokeplatinum scrcmd.c): an invisible
        object at x, z that ApplyFreeCameraMovement walks, but unlike AddFreeCamera the camera isn't told to follow it
        (no Camera_TrackTarget): the view stays on the player, which is what the translation of the camera's walk
        does (Route 202's Poké Radar scene: the walk is only a pause). Nothing to show."""
        return [f'// {name} {", ".join(tr.var(v) for v in vals)}: an object the camera does not follow (the view stays)']


for _pl, _macro, _fmt in [
        ('GetItemNameWithIndefArticle', 'WordSetItemNameWithArticle', ('n', 'var')),
        ('GetPartyMonFriendship', 'PokePartyGetHappiness', ('var', 'var')),
        ('GetRandom2', 'pl_GetRandom', ('var', 'var')), ('GetDayOfWeek', 'RTCGetWeekDay', ('var',)),
        ('HideMoney', 'MoneyWinClose', ()), ('UpdateMoneyDisplay', 'MoneyWinUpdate', ()),
        ('TrySaveGame', 'SaveDataWrite', ('var',))]:
    HANDLERS[_pl] = simple(_macro, *_fmt)


# Black 2's money window (ov036 scrcmd_msg.c MoneyWinDisp / MoneyWinUpdate) formats the money into the script's word 2
# (WordSetNumber(wordSet, 2, ...)), so a Pearl line that names word 2's Pokémon after it showed the money instead (the
# Ribbon Syndicate's "put the Royal Ribbon on 0."; found by v101-test, 2026-11-08). The translator re-issues the last
# buffer written into word 2 right after each money window command (FileTr.translate).
MONEY_WORD = 2


@handler('ShowMoney')
def h_show_money(tr, a, vals, name):
    return [f'MoneyWinDisp 31, 1  // Pearl ShowMoney {tr.var(vals[0])}, {tr.var(vals[1])} (Black 2\'s place)']


@handler('WaitABPressTime')
def h_wait_time(tr, a, vals, name):
    tr.job.approx['WaitABPressTime (waits the time; no early A/B)'] += 1
    return [f'VMSleep {tr.var(vals[0])}  // WaitABPressTime']


@handler('CheckPartyHasBadEgg')
def h_bad_egg(tr, a, vals, name):
    return [f'WorkSetConst {tr.var(vals[0])}, 0  // CheckPartyHasBadEgg: never']


@handler('CheckGameCompleted')
def h_game_done(tr, a, vals, name):
    return [f'FlagGet 2400, {tr.var(vals[0])}  // CheckGameCompleted: Black 2\'s game clear (Pearl 0x964 = 2400 here)']


@handler('GetFirstNonEggInParty')
def h_lead(tr, a, vals, name):
    return [f'pl_GetFirstNonEggInParty {tr.var(vals[0])}']


@handler('StartLegendaryBattle')
def h_legend(tr, a, vals, name):
    """Pearl 0x2BD (pokediamond LegendaryBattle: species, level): a scripted wild battle, flag 0. Black 2's legendary
    flag 1 (its Regirock, HoennB2's Kyogre) only changes the opening line to "Palkia appeared!" (ov167 btlv_scu.c
    BtlvScu_GetWildEncountMsg, setup flag 4: system text 0017 line 6); Pearl's says "A wild Palkia appeared!" (bank 324
    line 965), Black 2's flag 0 line. Pearl's legendary music comes by species (data/battle_music.json "wild")."""
    tr.last_battle = 'wild'
    tr.job.approx['StartLegendaryBattle (a wild battle: no legendary rules)'] += 1
    return end_free_camera(tr, 'a battle', a) + [f'pl_StartWildBattle {tr.var(vals[0])}, {tr.var(vals[1])}']


@handler('CapitalizeFirstChar', 'ShowSavingIcon', 'HideSavingIcon')
def h_noop2(tr, a, vals, name):
    tr.job.approx[f'{name} (nothing in Black 2)'] += 1
    return [f'// {name}: nothing in Black 2']


@handler('MessageFromBank', 'MessageFromBankInstant')
def h_msg_bank(tr, a, vals, name):
    bank, n = vals
    gift = delivery_message(tr, a, name)            # the deliveryman's received / can't-receive line (chapter 9a)
    if gift is not None:
        return gift
    if bank >= 0x4000 or n >= 0x4000:
        tr.job.stubs[f'{name} (bank or line from a var)'] += 1
        return [f'pl_stub {name}  // {tr.var(bank)}, {tr.var(n)}']
    kind, uid = speaker(tr, a, -1)
    m = tr.job.line_for(bank, n)
    return switch_window(tr, kind, uid) + [(f'pl_msg_actor {m}, {uid}' if kind == 'actor' else f'pl_msg_{kind} {m}')
                                           + f'  // Pearl bank {bank} line {n}']


@handler('GetCurrentMapID')
def h_mapid(tr, a, vals, name):
    """Pearl scripts compare it with Pearl map numbers: the number of the zone this file belongs to."""
    zs = [z['id'] for z in tr.job.pd.zones if z['scripts'] == tr.job.zone['scripts']]
    if len(zs) == 1 or tr.mode == 'common':
        return [f'WorkSetConst {tr.var(vals[0])}, {tr.job.zone["id"]}  // GetCurrentMapID: Pearl map {tr.job.zone["id"]}']
    out = [f'RTGetZoneID {tr.var(vals[0])}  // GetCurrentMapID: Black 2 zone -> Pearl map']
    for pz in zs:
        b2 = tr.job.pd.b2_zone.get(pz)
        if b2 is not None:
            out += [f'WorkCmpConst {tr.var(vals[0])}, {b2}', f'VMJumpIf CMP_NE, .Lmap{a:x}_{pz}',
                    f'WorkSetConst {tr.var(vals[0])}, {pz}', f'VMJump .Lmap{a:x}_end', f'.Lmap{a:x}_{pz}:']
    return out + [f'.Lmap{a:x}_end:']


# An amount past 65535 checked exactly (pearl_story.inc pl_CheckMoneyBig), by version: Platinum's Villa asks up to 220,000
# (2026-11-02, plat-rooms). Pearl's build keeps its 1.0 check of 65535 (the Ribbon Syndicate's two 100,000 ribbons): a
# Pearl change moves its released scripts (notes/V1_0_1.md).
EXACT_BIG_MONEY = version.EXACT_BIG_MONEY      # (v101-story: Pearl and Diamond too in 1.0.1)


@handler('GiveMoney', 'RemoveMoney', 'CheckMoney')
def h_money(tr, a, vals, name):
    """Pearl's amounts are 32-bit, Black 2's money commands take 16 bits: larger amounts in steps."""
    amount = vals[-1]
    macro = {'GiveMoney': 'pl_GiveMoney', 'RemoveMoney': 'pl_RemoveMoney', 'CheckMoney': 'MoneyCheck'}[name]
    if name == 'CheckMoney':
        if (amount > 0xFFFF or 0x4000 <= amount < 0xC000) and EXACT_BIG_MONEY:     # (0x4000-0xBFFF: read as a var)
            return [f'pl_CheckMoneyBig {tr.var(vals[0])}, {amount}  // CheckMoney {amount} (in 60,000s)']
        if amount > 0xFFFF:
            tr.job.approx['CheckMoney over 65535 (checks 65535)'] += 1
            amount = 0xFFFF
        return [f'MoneyCheck {tr.var(vals[0])}, {amount}']
    out = []
    while amount > 0xFFFF:
        out.append(f'{macro} 65535')
        amount -= 0xFFFF
    while 0x4000 <= amount < 0xC000:             # Black 2 reads 0x4000-0xBFFF as a var (ScriptReadAny): smaller steps
        out.append(f'{macro} 15000')             # (v101-test: the Ribbon Syndicate's 34465 and 16974 rests)
        amount -= 15000
    return out + [f'{macro} {amount}']


@handler('CountAliveMonsExcept')
def h_count_alive_except(tr, a, vals, name):
    """Pearl 0x19B (pokeplatinum ScrCmd_CountAliveMonsExcept: var, slot): the party's Pokémon that are not eggs and
    have HP, except the one in `slot`. With a constant slot past the party (Pearl's double-battle trainers ask with 6:
    the Seven Stars Restaurant, Jubilife TV) that is Black 2's PokePartyGetCount kind 2 (howManyPokesAreAbleToFight:
    the same test). A slot from a var stays a stub (2026-10-25, chapter 5a)."""
    var, slot = vals
    if slot >= 6 and slot < 0x4000:
        return [f'PokePartyGetCount {tr.var(var)}, 2  // Pearl CountAliveMonsExcept {var}, {slot}: no slot left out']
    if tr.f == DAYCARE_FILE:                    # the Day Care's slot from its list (chapter 4b): the macro tests it
        return [f'pl_CountAliveMonsExcept {tr.var(var)}, {tr.var(slot)}']
    tr.job.stubs[f'{name} (slot from a var)'] += 1
    return [f'pl_stub {name}  // Pearl {name} {var}, {slot}: the left-out slot from a var']


@handler('GetHour')
def h_get_hour(tr, a, vals, name):
    """Pearl 0x268 GetHour var (the clock's hour, 0-23) = Black 2's RTCGetTime hour, minute (ov012
    scrcmd_game_state.c s00D1_RTCGetTime: the same clock); the minute goes to the library's scratch work. The Seven
    Stars Restaurant's trainers are there from 9 to 22 (2026-10-25, chapter 5a)."""
    return [f'RTCGetTime {tr.var(vals[0])}, PL_TMP  // Pearl GetHour (the minute in PL_TMP)']


# Chapter 9b (2026-10-26; the macros' notes in pearl_story.inc "Chapter 9b"): the Hallowed Tower's Spiritomb counter
# (the Hideaways' battles: PVAR_UG_HIDEAWAY_BATTLES), Route 221's daily level (from the date) and party level, the
# Trophy Garden's daily Pokémon (PVAR_TROPHY_GARDEN_1/2; the wild slots are the encounter code's)
for _pl, _fmt in [('GetSpiritombCounter', ('var',)), ('ClearSpiritombCounter', ()),
                  ('GetDailyRandomLevel', ('var',)), ('GetPartyMonLevel', ('var', 'var')),
                  ('AddTrophyGardenMon', ()), ('GetTrophyGardenSlot1Species', ('var',))]:
    HANDLERS[_pl] = simple(f'pl_{_pl}', *_fmt)


@handler('PressPastoriaGymButton')
def h_pastoria_button(tr, a, vals, name):
    """Pearl 0x170 CheckPastoriaGymButton (pokeplatinum PastoriaGym_PressButton): the button under the player moves
    the Pastoria Gym's water to its height and the script waits (Pearl's field task). Here the decomp's
    src/pearlb2/pastoria_gym_itcm.c (gimmick 30, patches/pastoria_gym.py) moves it; pl_PressPastoriaGymButton asks
    through PVAR_PASTORIA_GYM_PRESS and waits (2026-10-25, chapter 5a)."""
    return ['pl_PressPastoriaGymButton  // Pearl CheckPastoriaGymButton: the water moves (pastoria_gym_itcm.c)']


@handler('InitPersistedMapFeaturesForPastoriaGym')
def h_pastoria_init(tr, a, vals, name):
    """Pearl 0x16F InitPastoriaGym (the zone's on-transition script): the water starts at the middle (Pearl's green
    button). The same script sets the three button works to say so, and the gym's gimmick reads them when the field
    starts (pastoria_gym_itcm.c): nothing to do here (2026-10-25, chapter 5a)."""
    return ['// InitPastoriaGym: the water at the middle; the button works below say so (pastoria_gym_itcm.c reads them)']

@handler('StartEndSafariGame')
def h_safari(tr, a, vals, name):
    """Pearl 0x202 EnableDisableSafariZone 0 (start) / 1 (end): Pearl's Safari Game (Safari Balls, a 500-step limit,
    its own battle screen). Black 2 has none, so the Great Marsh is a normal area (user 2026-10-25: "for safari port it
    over how we did in hoenn", HoennB2 DECISIONS 2026-10-07): the start puts Pearl's 30 Safari Balls in the Bag (Black
    2's Safari Ball is a Poke Ball with a 1.5x catch rate; Pearl's own lines say "received 30 Safari Balls"), the end
    takes the ones left (Pearl: "I'll relieve you of your remaining Safari Balls"). No step count or timer
    (2026-10-25, chapter 5a)."""
    tr.job.approx['StartEndSafariGame (the Great Marsh as a normal area: Safari Balls as items, no step count)'] += 1
    if vals[0] == 0 and version.PLATINUM:          # (its exit counts the Pokémon caught: GetCurrentSafariGameCaughtNum)
        return ['pl_SafariStart  // Pearl EnableDisableSafariZone 0: 30 Safari Balls into the Bag',
                'pl_SafariCountStart PVAR_SAFARI_START_COUNT  // the party and the boxes now (Platinum counts the catches)']
    return ['pl_SafariStart  // Pearl EnableDisableSafariZone 0: 30 Safari Balls into the Bag' if vals[0] == 0 else
            'pl_SafariEnd  // Pearl EnableDisableSafariZone 1: the Safari Balls left are taken back']


@handler('GetPCBoxesFreeSlotCount')
def h_pc_free(tr, a, vals, name):
    """Pearl 0x252 CountPCFreeSpace var: the free slots in the PC boxes = Black 2's BoxGetCount kind 5 (720 minus the
    Pokemon in the boxes; ov012 scrcmd_pokemon.c). Kind 4 is not a kind: it answers 0 (2026-10-25, chapter 5a)."""
    return [f'BoxGetCount {tr.var(vals[0])}, 5  // Pearl CountPCFreeSpace: free PC box slots']

# ---- Spear Pillar (2026-10-26, chapter 7)
@handler('20D')
def h_spear_pillar(tr, a, vals, name):
    """Pearl 0x20D SpearPillarSequence op, var (pokediamond ov06 SpearPillarSequence): Pearl's effects of the summoning
    (pl_SpearPillarSequence: white flashes; the polls report "over" at once, or the script loops forever)."""
    tr.job.approx['SpearPillarSequence (Pearl\'s summoning effects: white flashes; the sky\'s distortion not shown)'] += 1
    if tr.levels(a) - {0} and vals[0] in (0, 4, 5):    # (no screen fades in a map script)
        return [f'// Pearl SpearPillarSequence {vals[0]} in a map script: no flash there']
    return [f'pl_SpearPillarSequence {vals[0]}, {tr.var(vals[1])}  // Pearl SpearPillarSequence {vals[0]}']


@handler('18C')
def h_event_dir(tr, a, vals, name):
    """Pearl 0x18C SetEventDirection object, dir (pokediamond ScrCmd_SetEventDirection: the live object, or the player
    255, turns at once): a FACE move (Pearl's FACE_NORTH..EAST 0-3 = Black 2's, the directions' numbers)."""
    uid, d = vals
    if tr.levels(a) - {0}:
        tr.job.approx['SetEventDirection in a map script (Black 2 moves no actor there)'] += 1
        return [f'// SetEventDirection {uid}, {d} in a map script: Black 2 moves no actor there (left out)']
    if d >= 4:
        tr.job.stubs['SetEventDirection (the direction from a var)'] += 1
        return [f'pl_stub SetEventDirection  // {uid}, {tr.var(d)}']
    return [f'pl_ApplyMovement {actor(tr, uid)}, .Lfacee{a:x}  // SetEventDirection {uid}, {d}: turns at once',
            'pl_WaitMovement', f'VMJump .Lfacee{a:x}_end', '.balign 4, 0', f'.Lfacee{a:x}:', f'    Move {d}, 1',
            '    MoveEnd', f'.Lfacee{a:x}_end:']


@handler('HideObject', 'ShowObject')
def h_hide_show(tr, a, vals, name):
    """Pearl 0x1B2 HideObject / 0x1B1 ShowObject: the object (or the player) stays but is not drawn / is drawn again
    (Spear Pillar hides Palkia's place and the player during the vistas). Black 2 moves no actor in a map script (a
    field-load or zone-init script: ActorCmdExec hangs there, b2_script_check): there it is left out (the GTS's
    on-resume script hides the player coming back from the trade machine)."""
    import tower_script
    if tower_script.is_tower(tr) and tr.levels(a) - {0}:    # the tower's rooms hide the player and the entrants
        return [f'pl_TowerActorVisible {actor(tr, vals[0])}, {1 if name == "ShowObject" else 0}  // Pearl {name} '
                f'{vals[0]} (no actor command)']
    if tr.levels(a) - {0}:
        tr.job.approx[f'{name} in a map script (Black 2 moves no actor there)'] += 1
        return [f'// Pearl {name} {vals[0]} in a map script: Black 2 moves no actor there (left out)']
    return [f'pl_{name} {actor(tr, vals[0])}  // Pearl {name} {vals[0]}']


# ---- the Galactic HQ lab's containment units (2026-10-26, chapter 7; b2tools/pearl_lab_units.py)
FREED_TRIO_FLAG = 0x97D             # Pearl's FLAG_FREED_GALACTIC_HQ_POKEMON (set by the lab's button)


@handler('InitLakeGuardianContainmentUnits', 'DeactivateLakeGuardianContainmentUnits')
def h_lab_units(tr, a, vals, name):
    """Pearl 0x25E / 0x25F (pokeplatinum lake_guardian_containment_units.c): the units' glass shown gone after the
    release (the lab's on-resume script) / the glass's opening animation played and waited for (the button). Black 2:
    model 496's record plays Pearl's opening as its animation 0 (pearl_lab_units): the button takes a handle per unit,
    plays it, waits, holds the shared instance on its last frame (BMAnmPlayInv) and lets the handles go; the
    on-resume script holds the last frame when the flag is set. The band's scroll is not ported (pearl_lab_units)."""
    import pearl_lab_units as U
    spots = U.tiles(tr.job.zone['matrix'])
    if not spots:
        tr.job.approx[f'{name} (no containment unit in the zone)'] += 1
        return [f'// Pearl {name}: no containment unit (build model {U.UNIT}) in this zone']
    tr.job.approx[f'{name} (the band\'s scroll not shown)'] += 1
    x0, z0 = spots[0]
    if name.startswith('Init'):
        if 2 in tr.levels(a):                 # (BMAnmPlayInv: levels 0 and 1)
            return [f'// Pearl {name} in a zone init: Black 2 animates no prop there (left out)']
        return [f'pl_CheckFlag {tr.flag(FREED_TRIO_FLAG)}  // Pearl {name}: after the release the units stay open',
                f'pl_GoToIf 5, .Lunits{a:x}',
                f'BMAnmPlayInv {U.PROP_KIND}, {x0}, {z0}  // every unit (one shared instance) on the last frame',
                f'.Lunits{a:x}:']
    if tr.levels(a) - {0}:
        return [f'// Pearl {name} in a map script: Black 2 takes no prop handle there (left out)']
    assert len(spots) <= len(U.HANDLE_TAGS), spots
    tags = U.HANDLE_TAGS[:len(spots)]
    out = [f'// Pearl {name}: the units open (Pearl\'s animation 49: the glass shrinks away)']
    out += [f'BMCreateHandleByGPos PL_DOOR({t}), {U.PROP_KIND}, {x}, {z}' for t, (x, z) in zip(tags, spots)]
    out += [f'BMHndAudioVisualAnmPlay PL_DOOR({t}), 0' for t in tags]
    out += [f'BMHndAnmWait PL_DOOR({tags[-1]})',
            f'BMAnmPlayInv {U.PROP_KIND}, {x0}, {z0}  // the units keep the last frame when the handles go']
    out += [f'BMReleaseHandle PL_DOOR({t})' for t in tags]
    return out


@handler('CheckHasTwoAliveMons')
def h_two_alive(tr, a, vals, name):
    return [f'pl_CheckHasTwoAliveMons {tr.var(vals[0])}']


@handler('CheckDidNotCapture')
def h_did_not_capture(tr, a, vals, name):
    """Pearl 0x2BC (pokediamond ScrCmd_Unk02BC -> sub_020480D8: 0 only if the Pokémon was caught, else 1; Platinum's
    CheckDidNotCapture): Spear Pillar's Palkia (not caught: it comes back after the Hall of Fame, file 192). The macro
    is chapter 6b's (Black 2's wild battle result); 0xED CheckLostBattle is a different test (6b's handler)."""
    return [f'pl_CheckDidNotCapture {tr.var(vals[0])}  // Pearl 0x2BC: 1 unless caught']


@handler('SetBGMFixed')
def h_bgm_fixed(tr, a, vals, name):
    """Pearl 0x58 (pokediamond ScrCmd_Unk0058 -> sub_020040F4: the music kept over map changes, 1 on, 0 off): Black 2
    changes to the zone's music on every map change, so a warp continuation that Pearl runs with the music kept plays
    that song again when it starts (fixed_music)."""
    tr.job.approx['SetBGMFixed (the song played again after each warp: fixed_music)'] += 1
    return [f'// SetBGMFixed {vals[0]}: the music {"kept over the next warps" if vals[0] else "follows the zone again"} '
            f'(fixed_music)']


@handler('Unused_2C3')
def h_scope_mode(tr, a, vals, name):
    tr.job.approx['ScopeMode (Pearl\'s flag for the vistas\' map loads: nothing in Black 2)'] += 1
    return [f'// ScopeMode {vals[0]} (pokediamond ScrCmd_ScopeMode, field 0xB4): nothing in Black 2']


@handler('SetSubScene63')
def h_sub_scene63(tr, a, vals, name):
    tr.job.approx['SetSubScene63 (Pearl\'s sound sequence SEQ_PV001 for the Red Chain: none)'] += 1
    return ['// Pearl 0x5D (pokediamond ScrCmd_Unk005D: sound sequence SEQ_PV001 as a sub-scene): nothing in Black 2']


def fixed_music(pd, f, after):
    """The song a warp continuation of Pearl file f starting at `after` must play again (or None): Pearl keeps the music
    over map changes after SetBGMFixed 1 (Spear Pillar's vistas: THE_EVENT03 over Valley Windworks and Hearthome and
    back at Spear Pillar), Black 2 plays the new zone's. The setting and the last song are the last ones before
    `after` in file f's code, in address order from the script it belongs to; a continuation that plays a song itself
    before anything else is left alone."""
    d = pd.disasm(f)
    entry = max((e for e in d.entries if e <= after), default=0)
    fixed, song = 0, None
    for a in sorted(d.insns):
        if not entry <= a < after:
            continue
        e, op, args = d.insns[a]
        nm = pd.cmd_name(op)
        if nm == 'SetBGMFixed':
            fixed = args[0][1]
        elif nm in ('PlayMusic', 'SetBGM'):
            song = args[0][1]
    if not fixed or song is None:
        return None
    for a in sorted(x for x in d.insns if x >= after):
        nm = pd.cmd_name(d.insns[a][1])
        if nm in ('PlayMusic', 'SetBGM'):
            return None
        if nm in ('Warp', 'End', 'PlayDefaultMusic'):
            break
    return song


# ---- Platinum's rooms (step 4, 2026-11-02, plat-rooms): the Regi ruins, Rotom's Room, the Veilstone Store B1F, the
# Villa. Pearl has none of these commands (macros: pearl_story.inc "Platinum's rooms").
# The ruins' seven dots each (pokeplatinum ov5_021F6454.c sDotCoordinatesIronRuins, ..IcebergRuins, ..RockPeakRuins:
# x, z as s16 pairs, one table after the other in Platinum's overlay 5), by dot type (regi_ruins.h DOT_TYPE_*: the
# ruins' own map numbers); the bit of dot i is 1 << i, all seven RUINS_STATE_ACTIVATED_ALL_DOTS
RUINS_DOTS = {588: ((4, 7), (5, 5), (5, 9), (7, 7), (9, 5), (9, 9), (10, 7)),      # the Iron Ruins
              590: ((3, 7), (5, 7), (7, 5), (7, 7), (7, 9), (9, 7), (11, 7)),      # the Iceberg Ruins
              592: ((5, 5), (5, 7), (5, 9), (7, 7), (9, 5), (9, 7), (9, 9))}       # the Rock Peak Ruins
RUINS_ALL_DOTS = 260
_RUINS_CHECKED = False


def ruins_dots():
    """RUINS_DOTS, found once in the Platinum dump's overlay 5 (the three tables in a row)."""
    global _RUINS_CHECKED
    if not _RUINS_CHECKED:
        from gen4rom import Rom
        rom = Rom(version.WORLD_DUMP)
        off, _ = struct.unpack_from('<II', rom.data, 0x50)
        fid, flags = struct.unpack_from('<2I', rom.data, off + 32 * 5 + 24)
        assert not flags & 1, 'Platinum overlay 5 is compressed'
        st, en = rom.fat[fid]
        pat = b''.join(struct.pack('<hh', x, z) for k in (588, 590, 592) for x, z in RUINS_DOTS[k])
        assert rom.data[st:en].count(pat) == 1, 'the ruins\' dot tables are not in Platinum\'s overlay 5'
        _RUINS_CHECKED = True
    return RUINS_DOTS


@handler('ActivateRegiRuinsDot')
def h_regi_dot(tr, a, vals, name):
    """Platinum 0x32C ActivateRegiRuinsDot state var, dot type, x, z: in script, the same test as Platinum's C."""
    var, kind, x, z = vals
    assert kind in RUINS_DOTS, f'ActivateRegiRuinsDot: dot type {kind}'
    dots = ruins_dots()[kind]
    out = [f'// Pearl 0x32C ActivateRegiRuinsDot {tr.var(var)}, {kind}: the dot under the player sets its bit']
    out += [f'pl_RegiRuinsDot {tr.var(var)}, {tr.var(x)}, {tr.var(z)}, {dx}, {dz}, {1 << i}'
            for i, (dx, dz) in enumerate(dots)]
    return out + [f'pl_RegiRuinsDotsDone {tr.var(var)}, {(1 << len(dots)) - 1}, {RUINS_ALL_DOTS}']


@handler('CheckPartyHasFatefulEncounterRegigigas')
def h_fateful_regigigas(tr, a, vals, name):
    return [f'pl_CheckPartyHasFatefulEncounterRegigigas {tr.var(vals[0])}  // Platinum 0x32B']


@handler('GetRotomFormsInSave')
def h_rotom_forms(tr, a, vals, name):
    """Platinum 0x302 GetRotomFormsInSave heat, wash, frost, fan, mow: 1 for each form some Pokémon in the party or the
    boxes has (Rotom's Room shows the appliance of each form nobody has). Nothing in this game makes a Rotom form yet
    (the forms are a later piece: notes/PORT_AUDIT.md "Forms, Rotom, Giratina"): all 0, so every appliance shows."""
    tr.job.approx['GetRotomFormsInSave (no Rotom forms in this game yet: every form 0)'] += 1
    return [f'WorkSetConst {tr.var(v)}, 0  // GetRotomFormsInSave: no form in the save (no form change yet)' for v in vals]


@handler('GetEmptyPoffinCaseSlotCount')
def h_poffin_empty(tr, a, vals, name):
    """Platinum 0x307 (the Veilstone Store B1F's Poffin seller: is there room for the one Poffin he sells): PearlB2's Poffin
    Case answers room or not (pl_PoffinHasRoom), which is the count's answer for one Poffin."""
    tr.job.approx['GetEmptyPoffinCaseSlotCount (room for one or none: the seller sells one at a time)'] += 1
    return [f'pl_PoffinHasRoom {tr.var(vals[0])}  // GetEmptyPoffinCaseSlotCount: 1 room, 0 the Case is full']


@handler('ShowListMenuSetWidth')
def h_menu_show_width(tr, a, vals, name):
    tr.job.approx['ShowListMenuSetWidth (Black 2\'s list menu sizes itself)'] += 1
    return [f'ListMenuShow  // ShowListMenuSetWidth {vals[0]}']


@handler('CheckMetFurnitureRequirements')
def h_villa_requirement(tr, a, vals, name):
    """Platinum 0x30F CheckMetFurnitureRequirements furniture + 1, var: the Villa's gimmick answers (decomp
    src/pearlb2/plat_rooms/villa.c, b2tools/patches/platinum_villa.py)."""
    return [f'pl_VillaFurnitureRequirement {tr.var(vals[0])}, {tr.var(vals[1])}  // CheckMetFurnitureRequirements']


@handler('GetCurrentBGM', 'SetScenePlayBGMMusicBox', 'SetFieldScene')
def h_music_box(tr, a, vals, name):
    """The Villa's music box (pokeplatinum scrcmd_sound.c: GetCurrentBGM keeps the song, SetScenePlayBGMMusicBox plays
    SEQ_PL_TOWN02 as a music box, SetFieldScene the kept song again). Platinum's songs are not in the game yet (step 6,
    music): the room's song plays on."""
    tr.job.approx[f'{name} (the music box: Platinum\'s SEQ_PL_TOWN02 is not in the game yet, the room\'s song plays on)'] += 1
    return [f'// {name} {", ".join(tr.var(v) for v in vals)}: the music box\'s song (Platinum\'s SEQ_PL_TOWN02) is step 6\'s']


@handler('CheckABPress')
def h_ab_press(tr, a, vals, name):
    """Platinum 0x2FC CheckABPress var (A or B held now): the music box's loop asks each frame for up to 600 frames.
    Black 2's scripts can only wait for the press: the box plays until A or B, with no 20-second end."""
    tr.job.approx['CheckABPress (waits for A or B: no time limit)'] += 1
    return ['ABKeyWait  // CheckABPress: wait for A or B', f'WorkSetConst {tr.var(vals[0])}, 1']


# The Villa's visitor of the day (pokeplatinum system_vars.c SystemVars_UpdateVillaVisitor, run when the date changes
# and the player is not in the Resort Area or the Villa): the inside and outside flags cleared; the owned furniture
# counted (FLAG_VILLA_FURNITURE_*: 0x997-0x9AA); a visitor with 25, 75 or 90 % (12+ pieces: 90 %, of 15 visitors; 8+:
# 75 %, of 12; else 25 %, of 4), else none (0xFF); the visitor's line 0-4. Here the Resort Area's zone init picks it
# once a day (PFLAG_VILLA_VISITOR_TODAY, a flag Black 2 clears at midnight): the first time the player comes there after
# the date changed, before Platinum's own zone init reads it. (Platinum skips a day that ends with the player in the
# Area; here the next day's visitor comes at the first visit of that day.) Only the Resort Area's: the Villa's one door
# is there, and Platinum never changes the visitor while the player is in the Villa either.
VILLA_VISITOR_ZONES = ('MAP_RESORT_AREA',) if version.PLATINUM else ()
VILLA_FURNITURE_FLAGS = range(0x997, 0x9AB)        # FLAG_VILLA_FURNITURE_TABLE .. _CHANDELIER (20)
VILLA_VISITOR_INSIDE, VILLA_VISITOR_OUTSIDE = 0x9AB, 0x9AC
VAR_VILLA_VISITOR, VAR_VILLA_VISITOR_MESSAGE = 0x404E, 0x405A   # VAR_RESORT_VILLA_VISITOR, _MESSAGE_NUM
VILLA_ODDS = ((12, 90, 15), (8, 75, 12), (0, 25, 4))           # (pieces at least, percent, visitors)


def villa_visitor_lines(pd, k):
    import pearl_ids
    ids = pearl_ids.Ids()
    flag = lambda f: f'{ids.flag_value(f)}  // Platinum flag {f:#x}'
    out = ['    FlagGet PFLAG_VILLA_VISITOR_TODAY, PL_TMP', '    WorkCmpConst PL_TMP, 1', '    VMJumpIf CMP_EQ, .Lvv_end',
           '    FlagSet PFLAG_VILLA_VISITOR_TODAY',
           f'    FlagReset {flag(VILLA_VISITOR_INSIDE)}', f'    FlagReset {flag(VILLA_VISITOR_OUTSIDE)}',
           '    WorkSetConst PL_TMP2, 0  // the furniture owned']
    for f in VILLA_FURNITURE_FLAGS:
        out += [f'    FlagGet {ids.flag_value(f)}, PL_TMP  // Platinum flag {f:#x}', '    WorkAdd PL_TMP2, PL_TMP']
    out += ['    Random PL_TMP, 100']
    for i, (least, pct, n) in enumerate(VILLA_ODDS):
        out += [f'    WorkCmpConst PL_TMP2, {least}', f'    VMJumpIf CMP_LT, .Lvv_{i}',
                f'    WorkCmpConst PL_TMP, {pct}', '    VMJumpIf CMP_GT, .Lvv_none',
                f'    Random {ids.var(VAR_VILLA_VISITOR)}, {n}', '    VMJump .Lvv_line', f'.Lvv_{i}:']
    return out + ['.Lvv_none:', f'    WorkSetConst {ids.var(VAR_VILLA_VISITOR)}, 0xFF', '.Lvv_line:',
                  f'    Random {ids.var(VAR_VILLA_VISITOR_MESSAGE)}, 5', '.Lvv_end:', '    VMHalt']


# ---- plat-ch1 (2026-11-07): Platinum's chapter 1 and the Pokémon Centers (chapter 90). Pearl's scripts have none of these
# patterns (its output doesn't change: version_check). The handlers below wrap the ones above; nothing above is changed.
#
# Platinum's first battle is Barry, a Trainer (StartFirstBattle trainer: pokeplatinum Encounter_NewVsFirstBattle,
# BATTLE_STATUS_FIRST_BATTLE). Platinum doesn't restart the field after a loss: its script then runs ReturnToField and
# FadeScreen in itself (Route201_RivalWonLetsGoHome). Black 2's own first battle (aspertia_city.s, Hugh) is CallTrainerBattle
# with flags 1 (ov012 event_battle.c: setup flag 0x100, no loss text and no money lost, and no black-out) and CallTrainerBattleEnd
# win or lose. So pl_StartFirstTrainerBattle does both, CheckWonBattle after it only reads the result, and the loss branch's
# ReturnToField and FadeScreen in are dropped (the field is back and shown).
def first_battle_flow(tr):
    """(addresses of the CheckWonBattle after a first trainer battle, addresses of the loss branch's ReturnToField and its FadeScreen
    in) in this file."""
    if getattr(tr, '_first_battle', None) is None:
        d, pd = tr.d, tr.job.pd
        name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
        follow = lambda x: d.insns[x][2][0][1] if name(x) == 'GoTo' else x
        won, drop = set(), set()
        for a, (e, op, args) in d.insns.items():
            if name(a) != 'StartFirstBattle' or len(args) != 1:
                continue
            c = follow(e)
            if name(c) != 'CheckWonBattle':
                continue
            won.add(c)
            cmp_, jump = d.insns[c][0], d.insns[d.insns[c][0]][0]
            if name(cmp_) != 'CompareVarToValue' or name(jump) != 'GoToIf':
                continue
            var, value = d.insns[cmp_][2][0][1], d.insns[cmp_][2][1][1]
            cond, lose = d.insns[jump][2][0][1], d.insns[jump][2][1][1]
            if var != d.insns[c][2][0][1] or (value, cond) != (0, 1):
                continue
            if name(lose) == 'ReturnToField':
                drop.add(lose)
                x = d.insns[lose][0]
                for _ in range(3):
                    if name(x) == 'FadeScreen' and d.insns[x][2][2][1] == 1:
                        drop.add(x)
                        break
                    x = d.insns[x][0] if x in d.insns else None
        tr._first_battle = (won, drop)
    return tr._first_battle


_h_won_base, _h_return_field_base, _h_fade_base = HANDLERS['CheckWonBattle'], HANDLERS['ReturnToField'], HANDLERS['FadeScreen']


@handler('CheckWonBattle')
def h_won_first(tr, a, vals, name):
    if a in first_battle_flow(tr)[0]:
        return [f'pl_CheckWonFirstBattle {tr.var(vals[0])}  // after Platinum\'s first battle: the field is back already']
    return _h_won_base(tr, a, vals, name)


@handler('ReturnToField')
def h_return_field_first(tr, a, vals, name):
    if a in first_battle_flow(tr)[1]:
        return ['// RestoreOverworld after the first battle\'s loss: Black 2\'s battle end reopened the field (pl_StartFirstTrainerBattle)']
    return _h_return_field_base(tr, a, vals, name)


@handler('FadeScreen')
def h_fade_first(tr, a, vals, name):
    if a in first_battle_flow(tr)[1]:
        return [f'// FadeScreen {vals[0]}, {vals[1]}, {vals[2]}, {vals[3]:#x} after the first battle\'s loss: shown already '
                f'(pl_StartFirstTrainerBattle)']
    return _h_fade_base(tr, a, vals, name)


# Dynamic sprites compared (the Pokémon Center daily Trainers, file 1138: VAR_OBJ_GFX_ID_A/B hold who stands there, and their talk
# scripts ask it; the Battleground's too). The var holds the Black 2 code SetVarFromValue wrote (h_setvar), so a comparison with a
# Platinum graphics id compares with that id's code. Pearl compares none.
@handler('CompareVarToValue')
def h_compare_dynamic(tr, a, vals, name):
    var, value = vals
    if 0x4020 <= var < 0x4030 and value < 0x4000:
        import pearl_events
        code = pearl_events.sprite_code(value)
        if code is not None:
            if dynamic_codes(tr, var).get(code, {value}) != {value}:
                tr.job.approx['CompareVarToValue (two graphics share a dynamic sprite\'s Black 2 code)'] += 1
            return [f'pl_CompareVarToValue {tr.var(var)}, {code}  // dynamic sprite: Pearl graphics {value} -> Black 2 code']
    return [f'pl_CompareVarToValue {tr.var(var)}, {value}']


def dynamic_codes(tr, var):
    """{Black 2 code: the graphics ids this file sets or compares var with that have it}."""
    cache = tr.__dict__.setdefault('_dynamic_codes', {})
    if var not in cache:
        import pearl_events
        out = collections.defaultdict(set)
        for e, op, args in tr.d.insns.values():
            if tr.job.pd.cmd_name(op) in ('SetVarFromValue', 'CompareVarToValue') and args[0][1] == var and args[1][1] < 0x4000:
                code = pearl_events.sprite_code(args[1][1])
                if code is not None:
                    out[code].add(args[1][1])
        cache[var] = dict(out)
    return cache[var]


# A Trainer battle with a var (StartTrainerBattle VAR_0x8005: the daily Trainers, file 1138; the Pokémon Mansion's Liam and Celeste,
# file 419; the Battleground's leaders, file 1027): the var holds a Platinum trainer number that SetVarFromValue put there. Here it
# takes that Trainer's Black 2 id (the battle, BufferTrainerName and the defeat flag read it). A number with no Black 2 id stays,
# counted as a stub.
def trainer_vars(tr):
    """The vars this file's StartTrainerBattle commands battle."""
    if getattr(tr, '_trainer_vars', None) is None:
        pd = tr.job.pd
        tr._trainer_vars = {v for e, op, args in tr.d.insns.values() if pd.cmd_name(op) == 'StartTrainerBattle'
                            for t, v in args if t == 'var' and v >= 0x4000}
    return tr._trainer_vars


_h_setvar_base = HANDLERS['SetVarFromValue']


@handler('SetVarFromValue')
def h_setvar_trainer(tr, a, vals, name):
    var, value = vals
    if var in trainer_vars(tr) and 0 < value < 0x4000:
        if str(value) in tr.job.ids.reg['trainers']:
            return [f'pl_SetVarFromValue {tr.var(var)}, {tr.job.ids.trainer(value)}  // Pearl trainer {value}: battled by the var']
        tr.job.stubs[f'SetVarFromValue (trainer {value} for a battle: no Black 2 id)'] += 1
    return _h_setvar_base(tr, a, vals, name)


# ---- plat-ch11 (2026-11-07): Platinum's chapter 11 (the post-game). The Battleground (our Survival Area west house, Platinum's
# file 1027, scripts_battleground.s): four Trainers stand on dynamic sprites (VAR_OBJ_GFX_ID_1-4), filled on transition from
# VAR_BATTLEGROUND_TRAINER_1-4, which GetRandomBattlegroundTrainers (0x2F4) picks once a day (FLAG_DAILY_SET_BATTLEGROUND_TRAINERS):
# three of the eight Leaders and one of five other Trainers, or fewer (pokeplatinum scrcmd.c ScrCmd_GetRandomBattlegroundTrainers).
# A talk copies the Trainer's sprite var into VAR_MAP_LOCAL_0x01 and asks it who stands there (the Leader's team, lines, defeat
# flag). It was a stub: nobody stood there. Platinum only (Pearl's Battleground has no such command; its output doesn't change).
if version.PLATINUM:
    BATTLEGROUND_LEADERS = (126, 127, 128, 129, 130, 131, 132, 133)     # OBJ_EVENT_GFX_ROARK .. _VOLKNER (sBattlegroundGymLeaders)
    BATTLEGROUND_OTHERS = (141, 142, 143, 144, 145)                     # _CHERYL, _RILEY, _MARLEY, _BUCK, _MIRA (sBattlegroundStatTrainers)

    @handler('GetRandomBattlegroundTrainers')
    def h_battleground_trainers(tr, a, vals, name):
        """0x2F4 v1, v2, v3, v4 = pl_GetRandomBattlegroundTrainers (pearl_story.inc "plat-ch11"): Platinum's draws, written as
        the Black 2 codes of the graphics (the vars feed dynamic sprites: h_setvar's rule), 0xFFF (BATTLEGROUND_TRAINER_NONE)
        for none."""
        import pearl_events
        codes = [pearl_events.sprite_code(g) for g in BATTLEGROUND_LEADERS + BATTLEGROUND_OTHERS]
        assert None not in codes and len(set(codes)) == len(codes), f'the Battleground\'s Trainers\' Black 2 codes: {codes}'
        return [f'pl_GetRandomBattlegroundTrainers {", ".join(tr.var(v) for v in vals)}, {", ".join(map(str, codes))}'
                f'  // Platinum 0x2F4: three Leaders and one other, as Black 2 codes']

    def dynamic_copies(tr):
        """Vars this file fills only with SetVarFromVar from a dynamic sprite var (0x4020-0x402F) and otherwise only compares
        (the Battleground's VAR_MAP_LOCAL_0x01): they hold a Black 2 code too."""
        if getattr(tr, '_dynamic_copies', None) is None:
            pd, ok, bad = tr.job.pd, set(), set()
            for e, op, args in tr.d.insns.values():
                n = pd.cmd_name(op)
                vs = [v for t, v in args if t == 'var' or (isinstance(v, int) and 0x4000 <= v < 0x8100)]
                if n == 'SetVarFromVar' and len(args) == 2 and 0x4020 <= args[1][1] < 0x4030:
                    ok.add(args[0][1])
                elif n == 'CompareVarToValue':
                    pass
                else:
                    bad |= set(vs)
            tr._dynamic_copies = {v for v in ok - bad if not 0x4020 <= v < 0x4030}
        return tr._dynamic_copies

    _h_compare_ch1 = HANDLERS['CompareVarToValue']

    @handler('CompareVarToValue')
    def h_compare_dynamic_copy(tr, a, vals, name):
        var, value = vals
        if var in dynamic_copies(tr) and value < 0x4000:
            import pearl_events
            code = pearl_events.sprite_code(value)
            if code is not None:
                return [f'pl_CompareVarToValue {tr.var(var)}, {code}  // a copy of a dynamic sprite: Platinum graphics {value} '
                        f'-> Black 2 code']
        return _h_compare_ch1(tr, a, vals, name)
# ---- end plat-ch11


# ---- plat-ch4 (2026-11-07): Platinum's chapter 4 (Route 206 to Hearthome). The Bicycle in scripts. Pearl checks the Bicycle in the
# Bag at its Cycling Road gates (CheckItem); Platinum checks that the player rides it, and gets the player off it before a partner
# walks along. Black 2 has both: PlayerGetExState (ov036 s0078: 0 on foot, 1 cycling, 2 surfing, 3 diving) and
# PlayerSetSpecialSequence (s0075: 1 back on foot, 2 on the Bicycle, as Field_ToggleCycling; route_5.s gets the player off the same
# way). Platinum only (Pearl's scripts don't use these; its output doesn't change).
if version.PLATINUM:
    @handler('CheckPlayerOnBike')
    def h_on_bike(tr, a, vals, name):
        """0x0C7 CheckPlayerOnBike var (pokeplatinum ScrCmd_CheckPlayerOnBike: TRUE while cycling): Black 2's ex state, 1 kept,
        anything else 0. Route 206's two Cycling Road gates (CoordEvent_OnlyBicycles, CoordEvent_OnlyCyclists) turn back a player
        on foot and let a cyclist through. Left a stub (Pearl's 1.0 has none: Pearl's gates check the Bag), the var kept its last
        value: the gates turned back or let through by chance; the north gate stands between Eterna and the story."""
        v, end = tr.var(vals[0]), f'.L{tr.label(a)}_bike'
        return [f'PlayerGetExState {v}  // CheckPlayerOnBike: Black 2\'s ex state (1 = cycling)',
                f'WorkCmpConst {v}, 1', f'VMJumpIf CMP_EQ, {end}', f'WorkSetConst {v}, 0', f'{end}:']

    @handler('SetPlayerBike')
    def h_set_bike(tr, a, vals, name):
        """0x0C8 SetPlayerBike on (pokeplatinum ScrCmd_SetPlayerBike): FALSE gets the player off the Bicycle (Mira in Wayward Cave,
        Cheryl, Riley, Buck and Marley before they walk along: Black 2 refuses the Bicycle while a partner follows), TRUE puts them
        on it (the common bike-parking script). Black 2's form change, only when the player isn't in that form already (as
        route_5.s). Platinum's music override comes with it: Black 2's field plays its bike song while cycling. Was a stub [Pearl
        too]: a partner could start following a player on the Bicycle."""
        on = bool(vals[0])
        skip = f'.L{tr.label(a)}_bike'
        return [f'PlayerGetExState PL_TMP  // SetPlayerBike {int(on)}: Black 2\'s form change ({"on" if on else "off"} the Bicycle)',
                f'WorkCmpConst PL_TMP, {0 if on else 1}', f'VMJumpIf CMP_NE, {skip}',
                f'PlayerSetSpecialSequence {2 if on else 1}', f'{skip}:']

    @handler('SetCyclingBGM')
    def h_cycling_bgm(tr, a, vals, name):
        """0x2BF SetCyclingBGM (Route 206's on-resume, with ForceBicycling, as the player comes onto the Cycling Road): the bike
        song. Black 2's field plays the zone's bike song while the player cycles (patches/zone_flags), and on foot its own."""
        tr.job.approx['SetCyclingBGM (Black 2 plays the bike song while cycling)'] += 1
        return ['// SetCyclingBGM: Black 2 plays the bike song while the player cycles']


# ---- plat-ch3 (2026-11-07): Platinum's chapter 3 (Floaroma, the Windworks, Eterna). Platinum only: Pearl's scripts use
# Unk0292, SetObjectEventDir and AddObject too, and Pearl's output stays its 1.0's (version_check). (The Bicycle's commands,
# CheckPlayerOnBike and SetPlayerBike, are plat-ch4's block above.)
if version.PLATINUM:
    @handler('GetItemQuantity')
    def h_item_quantity(tr, a, vals, name):
        """0x2FE GetItemQuantity item, var (pokeplatinum: the Bag's count) = Black 2's ItemGetCount (ov036 s00B9). Mr. Fuego
        offers ten Star Pieces at once when the player has ten."""
        item, var = vals
        b2, note = (item, '') if item >= 0x4000 else item_value(item)
        return [f'pl_GetItemQuantity {tr.var(b2)}, {tr.var(var)}{note}']

    @handler('FindPartySlotWithFatefulEncounterSpecies')
    def h_fateful_slot(tr, a, vals, name):
        """0x31C FindPartySlotWithFatefulEncounterSpecies var, species (pokeplatinum scrcmd_party.c): the first party slot,
        no Egg, of that species with the fateful-encounter mark, else 0xFF. In script, as plat-rooms' Regigigas check
        (Black 2's PKM_PARAM_FATEFUL_ENCOUNTER 0x6d). Floaroma's Gracidea (an event Shaymin in the party)."""
        var, species = vals
        if species >= 0x4000:
            tr.job.stubs['FindPartySlotWithFatefulEncounterSpecies (species in a var)'] += 1
            return [f'pl_stub FindPartySlotWithFatefulEncounterSpecies  // species in {tr.var(species)}']
        return [f'pl_FindPartySlotWithFatefulEncounterSpecies {tr.var(var)}, {species}']


if version.GHOSTS:                  # (v101-story: Pearl and Diamond too, version.GHOSTS)
    @handler('CheckShouldShowGhost')
    def h_ghost(tr, a, vals, name):
        """0x292 CheckShouldShowGhost percent, var (pokeplatinum scrcmd.c: var = 1 when LCRNG % 101 <= percent): the Old
        Chateau's old man (10 %) and girl (25 %) in its zone inits. Black 2's Random (allowed in a zone init: the Villa's
        visitor). Pearl's 1.0 left it a stub: the ghosts never showed."""
        return [f'pl_CheckShouldShowGhost {min(vals[0], 100)}, {tr.var(vals[1])}']


if version.PLATINUM:
    _h_setobjdir_ch3_base = HANDLERS['SetObjectEventDir']

    @handler('SetObjectEventDir')
    def h_setobjdir_var(tr, a, vals, name):
        """SetObjectEventDir on an object held in a var (the Eterna Gym's Trainers turn to the player after their battle:
        EternaGym_LookTowardsPlayer, VAR_0x8007 = the Trainer's local id): outside a zone init the live actor turns
        (Black 2's ActorCmdExec reads its actor as a var too, ov036 s0064). Only when every value the file puts in the
        var is an object of the zone; else as before (a stub)."""
        uid, d = vals
        if uid < 0x4000 or tr.levels(a) == {2} or tr.mode == 'common' or d >= 4:
            return _h_setobjdir_ch3_base(tr, a, vals, name)
        pd = tr.job.pd
        ids = {args[1][1] for e, op, args in tr.d.insns.values()
               if pd.cmd_name(op) == 'SetVarFromValue' and args[0][1] == uid}
        if not ids or not all(i in tr.job.object_index for i in ids):
            return _h_setobjdir_ch3_base(tr, a, vals, name)
        return [f'pl_ApplyMovement {tr.var(uid)}, .Lface{a:x}  // SetObjectEventDir {tr.var(uid)} (objects {sorted(ids)}): '
                'the live actor turns', 'pl_WaitMovement', f'VMJump .Lface{a:x}_end', '.balign 4, 0', f'.Lface{a:x}:',
                f'    Move {d}, 1', '    MoveEnd', f'.Lface{a:x}_end:']

    # Platinum's movement 0x99 (MOVEMENT_ACTION_153, pokeplatinum unk_020655F4.c: the "!" emote, sub_020664A0(obj, 0, 1): the
    # balloon shown two frames late, with its sound) = Pearl's 0x4B's Black 2 code (75, "!" with its sound). Kept as the bare
    # number before, Black 2's own action 153 played instead: Cheryl in Eterna Forest (3 uses; else only step 7's Distortion
    # World uses Platinum's 0x69-0x99). Pearl's codes stop at 0x68.
    MOVEMENT.setdefault(0x99, dict(MOVEMENT[0x4B], pearl_name='EMOTE_EXCLAMATION_MARK_LATE (Platinum 0x99)', exact=False,
                                   note='Platinum shows the "!" two frames later; here at once'))

    _h_add_ch3_base = HANDLERS['AddObject']

    @handler('AddObject')
    def h_add_facing(tr, a, vals, name):
        """AddObject after a SetObjectEventDir of the same object in its block (Platinum: SetObjectEventPos,
        SetObjectEventMovementType, SetObjectEventDir, AddObject): the actor appears facing that way, not its event's
        way. (The Dir before it turns no actor: the object isn't there yet.) The Eterna Galactic building's Looker
        appeared facing north at (12, 15), not west to the player."""
        out = _h_add_ch3_base(tr, a, vals, name)
        uid = vals[0]
        turned = same_block_before(tr, a, 'SetObjectEventDir', uid) if uid < 0x4000 and tr.levels(a) != {2} else None
        if not turned or not out:
            return out
        d = tr.var(turned[1])
        m = re.match(rf'^(pl_AddObjectAt {uid}, \S+, )(\S+)(  // .*)$', out[0])
        if m:
            return [f'{m.group(1)}{d}{m.group(3)}, facing as its SetObjectEventDir'] + out[1:]
        if len(out) > 1:
            m = re.match(rf'^(pl_SetPosition {uid}, \S+, \S+, \S+, )(\S+)(  // .*)$', out[1])
            if m:
                return [out[0], f'{m.group(1)}{d}{m.group(3)}, facing as its SetObjectEventDir'] + out[2:]
        return out


# ---- plat-ch6 (2026-11-07): Platinum's chapter 6 (Route 214 to Pastoria). Two of Platinum's party and Pokédex questions, on
# Black 2's own commands (macros in pearl_story.inc, block "plat-ch6"). Platinum only: Pearl's output doesn't change (Pearl's
# Pastoria middle house keeps its stub, as in 1.0). 1.0.1: Pearl and Diamond too (version.PARTY_QUESTIONS).
if version.PARTY_QUESTIONS:
    @handler('CheckHasSeenSpecies')
    def h_seen_species(tr, a, vals, name):
        """0x337 CheckHasSeenSpecies species, var (pokeplatinum ScrCmd_CheckHasSeenSpecies: Pokedex_HasSeenSpecies) = Black 2's
        PokeDexIsRegist 0 (PokeDex_IsSeen; the same national numbers). The Pokémon Mansion office's book (Manaphy, 490): left a
        stub, the var kept the last answer, so the picture showed or not by chance."""
        return [f'pl_CheckHasSeenSpecies {tr.var(vals[0])}, {tr.var(vals[1])}  // Black 2\'s Pokédex: seen']

    @handler('CheckPartyCombeeGenderCount')
    def h_combee_genders(tr, a, vals, name):
        """0x264 CheckPartyCombeeGenderCount var (pokeplatinum scrcmd.c): the party's Combee that aren't Eggs, 0 none, 1 of one
        gender, 2 a male and a female. Pastoria's middle house gives the Macho Brace for both. A party loop on Black 2's
        PokePartyGetParam (species 5, sex 0x6E: both in its stats_list) and PokePartyIsEgg. Was a stub [Pearl too]: the var
        kept whatever it held, so the boy's answer and the Macho Brace came by chance.
        Pearl and Diamond (1.0.1): the same op is their own CheckBurmyForms (pokediamond scrcmd.c ScrCmd_CheckBurmyForms):
        the number of different Burmy forms in the party, 0-3; their boy asks for all three cloaks and gives the Macho
        Brace at 3 (his script compares 0, 1 and 2 first)."""
        if not version.PLATINUM:
            return [f'pl_CheckBurmyForms {tr.var(vals[0])}  // a party pass per cloak: 0-3 different Burmy forms']
        return [f'pl_CheckPartyCombeeGenderCount {tr.var(vals[0])}  // a party loop: 0 none, 1 one gender, 2 both']


if version.PREVIEW_SEEN:            # (v101-story: Pearl and Diamond too, version.PREVIEW_SEEN)
    _h_preview_base = HANDLERS['DrawPokemonPreview']

    @handler('DrawPokemonPreview')
    def h_preview_seen(tr, a, vals, name):
        """0x208 DrawPokemonPreview species, gender also marks the species seen (pokeplatinum ScrCmd_DrawPokemonPreview:
        FieldSystem_WriteSpeciesSeen; Pearl's ScrCmd_ShowPokemonPic the same). Black 2's CallPokemonPreview only shows it
        (ov036 scrcmd_poke_disp.c), so PokeDexRegist 0 (PokeDex_RegistPkm) follows. The Mansion office's book says "Manaphy's
        data was added to the Pokédex"; Verity Cavern's Mesprit (chapter 8) and Fullmoon Island's Cresselia (chapter 12) are
        the other two. Pearl's handler is unchanged (its 1.0 shows the picture without the Pokédex entry)."""
        return _h_preview_base(tr, a, vals, name) + [
            f'PokeDexRegist 0, {tr.var(vals[0])}  // DrawPokemonPreview marks the species seen (Black 2\'s preview doesn\'t)']


# ---- plat-ch7 (2026-11-07): Platinum's chapter 7 (Celestic, Canalave, Iron Island, the library). Platinum only: Pearl's output
# stays its 1.0's (version_check). Nothing above is changed; the handlers below wrap or add.
# (v101-story: the ReturnToField rule and the Move Deleter are on for Pearl and Diamond too, version.FIELD_STAYS_OPEN and
# MOVE_DELETER; the library's TV and its camera stay Platinum's. The order of the definitions is as before.)
if version.PLATINUM or version.FIELD_STAYS_OPEN or version.MOVE_DELETER:
    def _prev_insn(tr, a):
        """The instruction before address a in Platinum's file (address order), or None."""
        if getattr(tr, '_prev_ch7', None) is None:
            tr._prev_ch7 = {e: x for x, (e, op, args) in tr.d.insns.items()}
        return tr._prev_ch7.get(a)


if version.PLATINUM:
    @handler('StartLibraryTV')
    def h_library_tv(tr, a, vals, name):
        """0x310 StartLibraryTV (pokeplatinum library_tv.c, the Canalave library's explosion scene): a full-screen picture,
        the TV's footage of Lake Valor (graphic/library_tv in the intro TV's frame, with moving scan lines) for 240 frames,
        between the scene's fade-out and its ReturnToField. Black 2 has no such screen: the scene goes on, the footage isn't
        shown (a stub, counted). The field stays open: the ReturnToField after it opens nothing (h_return_field_open)."""
        tr.job.stubs['StartLibraryTV (the TV\'s footage of Lake Valor: no Black 2 screen)'] += 1
        return ['pl_stub StartLibraryTV  // the TV\'s footage of Lake Valor (240 frames): no Black 2 screen; the field stays open']


if version.FIELD_STAYS_OPEN:
    # ReturnToField (0x0A1) after an app that didn't run: Black 2's FieldOpen waits for the proc manager to be idle (pokebw2
    # field_event.c EventFieldOpen_Callback: GSYS_GetProcMgrState), which never happens while the field runs, so a FieldOpen
    # on an open field hangs the script. When every command since the scene's last fade or message is a stub (or
    # StartLibraryTV) or only reads a result, the field never closed: nothing to open, and the fade-in after it is a black one
    # (not the starter screen's white). The library's explosion scene stopped there; also Jublife TV's photo boards and
    # custom-word menus, the Union Room, the Frontier's closed scenes (all stubs).
    _NO_SCREEN = {'StartLibraryTV'}
    _NEUTRAL = {'GoToIf', 'GoTo', 'CallIf', 'Call', 'CompareVarToValue', 'CompareVarToVar', 'SetVarFromValue', 'SetVarFromVar'}
    _BOUNDARY = {'WaitFadeScreen', 'FadeScreen', 'CloseMessage', 'WaitButton', 'Message', 'WaitTime', 'LockAll', 'ReleaseAll',
                 'RestoreCamera', 'ApplyMovement', 'WaitMovement'}      # (field commands: the scene was on the field there)
    _h_return_field_ch7_base = HANDLERS['ReturnToField']

    @handler('ReturnToField')
    def h_return_field_open(tr, a, vals, name):
        if a in poke_select_fades(tr):
            return _h_return_field_ch7_base(tr, a, vals, name)
        pd, apps, p = tr.job.pd, [], _prev_insn(tr, a)
        while p is not None and len(apps) < 6:
            n = pd.cmd_name(tr.d.insns[p][1])
            if n in _BOUNDARY or n in ('End', 'Return', 'ReturnCommonScript') or (n == 'GoTo' and not apps):
                break
            if n not in _NEUTRAL and not n.startswith('Get'):
                apps.append(n)
            p = _prev_insn(tr, p)
        if apps and all(n in _NO_SCREEN or n not in HANDLERS for n in apps):
            return [f'// ReturnToField: the field stayed open ({", ".join(reversed(apps))}: no Black 2 screen ran)']
        return _h_return_field_ch7_base(tr, a, vals, name)


if version.MOVE_DELETER:
    # The Move Deleter (Canalave's east house; pearl_story.inc "plat-ch7"): Black 2's move list fades and reopens the field
    # itself, so Platinum's fades and ReturnToField around SelectPartyMonMove are dropped, as around the party select.
    _psel_ch7_base = poke_select_fades

    def poke_select_fades(tr):
        out = _psel_ch7_base(tr)
        if not getattr(tr, '_psel_ch7', False):
            tr._psel_ch7 = True
            d, pd = tr.d, tr.job.pd
            nxt = {x: e for x, (e, op, args) in d.insns.items()}
            name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
            for c in [x for x in d.insns if name(x) == 'SelectPartyMonMove']:
                w0 = _prev_insn(tr, c)
                f0 = _prev_insn(tr, w0) if w0 is not None else None
                g = nxt.get(c)
                r = nxt.get(g)
                f1 = nxt.get(r)
                if (name(f0), name(w0), name(g), name(r), name(f1)) == ('FadeScreen', 'WaitFadeScreen',
                                                                      'GetSelectedPartyMonMove', 'ReturnToField', 'FadeScreen'):
                    out |= {f0, r, f1}
        return out

    def _ch7_handler(cmd):
        """A handler for cmd unless another chapter's block gave it one first (the shard tutor's commands are chapter 6's)."""
        def deco(fn):
            return fn if cmd in HANDLERS else handler(cmd)(fn)
        return deco

    @_ch7_handler('GetPartyMonMoveCount')
    def h_move_count(tr, a, vals, name):
        """0x1C8 GetPartyMonMoveCount var, slot: the moves that party Pokémon knows = Black 2's PokePartyGetMoveCount."""
        return [f'PokePartyGetMoveCount {tr.var(vals[0])}, {tr.var(vals[1])}  // GetPartyMonMoveCount']

    @_ch7_handler('SelectPartyMonMove')
    def h_select_move(tr, a, vals, name):
        """0x1C6 SelectPartyMonMove slot: the summary's move list (pearl_story.inc pl_SelectPartyMonMove)."""
        return [f'pl_SelectPartyMonMove {tr.var(vals[0])}  // SelectPartyMonMove: Black 2\'s move list (CallPokeMoveReplace)']

    @_ch7_handler('GetSelectedPartyMonMove')
    def h_selected_move(tr, a, vals, name):
        """0x1C7 GetSelectedPartyMonMove var: the slot chosen, 0xFF when cancelled."""
        return [f'pl_GetSelectedPartyMonMove {tr.var(vals[0])}']

    @_ch7_handler('BufferPartyMoveName')
    def h_buffer_party_move(tr, a, vals, name):
        """0x1CB BufferPartyMoveName arg, slot, move slot."""
        return [f'pl_BufferPartyMoveName {vals[0]}, {tr.var(vals[1])}, {tr.var(vals[2])}']

    @_ch7_handler('ClearPartyMonMoveSlot')
    def h_clear_move_slot(tr, a, vals, name):
        """0x1C9 ClearPartyMonMoveSlot slot, move slot (pokeplatinum Pokemon_ClearMoveSlot: the moves after it move up, the
        last is emptied) = Black 2's PokePartyLearnMove with move 0 (ov012 s010B: the same)."""
        return [f'PokePartyLearnMove {tr.var(vals[0])}, {tr.var(vals[1])}, 0  // ClearPartyMonMoveSlot: the move forgotten']


if version.PLATINUM:
    # The library's explosion scene puts the free camera on the player again after the TV (AddFreeCamera with
    # GetPlayerMapPos's vars, at Platinum's 0x1FF, not in Pearl's file): the player is still at (7, 7), the first camera's
    # tile (CAMERA_AT_PLAYER), so it walks east 3 to the table again before the fade-in, west 3 with Rowan at the end, and
    # RestoreCamera then cuts back. (Platinum's file, Platinum's address: no Pearl address to key it by.)
    PL_CAMERA_AT_PLAYER = {(42, 0x01FF): (7, 7)}
    _h_cam_add_ch7_base = HANDLERS['AddFreeCamera']

    @handler('AddFreeCamera')
    def h_cam_add_platinum(tr, a, vals, name):
        x, z = vals
        if (x >= 0x4000 or z >= 0x4000) and (tr.f, a) in PL_CAMERA_AT_PLAYER and tr.mode != 'common':
            return _h_cam_add_ch7_base(tr, a, list(PL_CAMERA_AT_PLAYER[(tr.f, a)]), name)
        return _h_cam_add_ch7_base(tr, a, vals, name)
# ---- end plat-ch7 ------------------------------------------------------------------------------------------------------


# ---- plat-ch10 (2026-11-07): Platinum's chapter 10 (Sunyshore and the League). The Pokétch developer's nature question, on
# Black 2's own party commands (macro in pearl_story.inc, block "plat-ch10"). Platinum only: Pearl's output doesn't change
# (Pearl's Sunyshore east house keeps its stub, as in 1.0).
if version.NATURE_CHECK:            # (v101-story: Pearl and Diamond too, version.NATURE_CHECK)
    @handler('FindPartySlotWithNature')
    def h_nature_slot(tr, a, vals, name):
        """0x213 FindPartySlotWithNature var, nature (pokeplatinum scrcmd_party.c): the first party slot, not an Egg, with
        that nature, else 0xFF (PARTY_SLOT_NONE). A party loop on Black 2's PokePartyGetParam nature (PKM_PARAM_NATURE 0x70,
        in its stats_list; Gen 5 keeps the nature apart from the personality, the same 25 in the same order) and
        PokePartyIsEgg. Sunyshore's Pokétch developer gives the Calendar, Dot Artist and Roulette apps for a Serious, Naive
        and Quirky Pokémon. It was a stub [Pearl too]: VAR_0x8000 kept whatever it held, so the app came or not by chance."""
        nat = tr.var(vals[1])
        cmp = 'WorkCmpWork' if vals[1] >= 0x4000 else 'WorkCmpConst'
        return [f'pl_FindPartySlotWithNature {tr.var(vals[0])}, {nat}, {cmp}  // a party loop: the slot, or 255']
# ---- end plat-ch10

# ---- plat-ch9 (2026-11-07): Platinum's chapter 9 (the Galactic HQ, Mt. Coronet, Spear Pillar, Sendoff Spring). Platinum's party
# and Pokédex commands there on Black 2's own commands (macros in pearl_story.inc, block "plat-ch9"), Spear Pillar's cutscene,
# and the Distortion World's entrance marked for step 7. Platinum only: Pearl's scripts use none of these.
if version.PLATINUM:
    @handler('CheckPartyHasHeldItem')
    def h_party_held_item(tr, a, vals, name):
        """0x32F CheckPartyHasHeldItem item, var (pokeplatinum scrcmd_party.c: TRUE if a party Pokémon holds the item). A party
        loop on Black 2's PokePartyGetParam (PKM_PARAM_ITEM 6, in its stats_list). Mt. Coronet 6F's map scripts (chapter 12):
        the Adamant or Lustrous Orb held by a party Pokémon, not only in the Bag, leads the stairs to Dialga's or Palkia's
        pillar. Was a stub: the var kept CheckItem's answer, so a held Orb didn't count."""
        if vals[0] >= 0x4000:
            tr.job.stubs['CheckPartyHasHeldItem (an item in a var)'] += 1
            return ['pl_stub CheckPartyHasHeldItem  // an item in a var']
        item, note = item_value(vals[0])
        return [f'pl_CheckPartyHasHeldItem {item}, {tr.var(vals[1])}  // a party loop on the held item{note}']

    @handler('SetPartyGiratinaForm')
    def h_giratina_form(tr, a, vals, name):
        """0x328 SetPartyGiratinaForm form (pokeplatinum ScrCmd_SetPartyGiratinaForm, Party_SetGiratinaForm): each party
        Giratina to the Origin Forme (1), or (0) to the forme its held item gives (the Origin Forme with the Griseous Orb, else
        the Altered Forme), and the Pokédex records it = Black 2's PokePartySetForme (PokeParty_ChangeForme: ability and stats
        recalculated; PokeDex_RegistPkm). Spear Pillar Distorted, into the Distortion World (1, step 7), and Sendoff Spring,
        back out (0). Was a stub: a Giratina caught there stayed in the Origin Forme without the Orb after step 7."""
        what = 'the Origin Forme' if vals[0] else 'the forme its held item gives'
        return [f'pl_SetPartyGiratinaForm {vals[0]}  // each party Giratina: {what}']

    @handler('SetSpeciesSeen')
    def h_species_seen(tr, a, vals, name):
        """0x31A SetSpeciesSeen species (pokeplatinum FieldSystem_WriteSpeciesSeen) = Black 2's PokeDexRegist 0
        (PokeDex_RegistPkm), as plat-ch6's DrawPokemonPreview. Spear Pillar: Dialga and Palkia seen after the summoning. Was a
        stub."""
        return [f'PokeDexRegist 0, {tr.var(vals[0])}  // SetSpeciesSeen: the Pokédex has seen it']

    SPEAR_PILLAR_CUTSCENE = (       # (line, cries before it, a long shake before it): overlay 100's order (ov100_021D2F0C:
        (14, (483,), False),        # Dialga and Palkia come, lines 14, 16, 18, 19; ov100_021D1C44: the lake trio, lines
        (16, (484,), False),        # 20-23, Giratina's shadow and its cries, 24-26; the line numbers are Spear Pillar's bank)
        (18, (), False), (19, (), False), (20, (), False), (21, (), False), (22, (), False), (23, (), False),
        (24, (487,), True), (25, (), False), (26, (487,), True))     # (one cry at a time: the cutscene's Dialga and
    # Palkia crying together before Giratina's first cry are left out)

    @handler('2FB')
    def h_spear_pillar_cutscene(tr, a, vals, name):
        """Platinum 0x2FB (pokeplatinum ScrCmd_2FB, sub_020985E4): Spear Pillar's cutscene, overlay 100 (Dialga and Palkia
        summoned in 3D, the lake trio, Giratina's shadow; NARC demo_tengan). Black 2 has no such screen. Its 11 lines (Spear
        Pillar's text bank, lines 14-26: Cyrus's speech, "a Pokémon that can only appear as a shadow") were lost with the stub;
        now they show in the field, in the cutscene's order, with Dialga's, Palkia's and Giratina's cries and the camera's long
        shake where Giratina comes. The 3D pictures and the cutscene's songs (SEQ_PL_EV_GIRA, GIRA2) aren't shown."""
        src = tr.job.gen4_text.bank(tr.bank)
        if len(src) <= 26 or 'shadow' not in src[24]:
            tr.job.stubs['2FB (not Spear Pillar\'s text bank)'] += 1
            return ['pl_stub 2FB  // Spear Pillar\'s cutscene, outside Spear Pillar\'s text bank']
        tr.job.approx['2FB (Spear Pillar\'s cutscene, overlay 100: its 11 lines in the field with the cries and a shake; the '
                      '3D pictures not shown)'] += 1
        out = ['// Platinum 0x2FB: Spear Pillar\'s cutscene (overlay 100) has no Black 2 screen: its lines, cries and a shake']
        for n, cries, shake in SPEAR_PILLAR_CUTSCENE:
            if shake:
                out.append('pl_ShakeCamera 1')
            out += [f'pl_PlayCry {c}' for c in cries]
            if 0 in tr.job.gen4_text.buffers(src[n]):       # (line 22: "Now, PLAYER.": the cutscene buffers the name)
                out.append('pl_BufferPlayerName 0')
            out += h_message(tr, a, [n], 'Message')
            if cries:
                out.append('pl_WaitCry')
        return out + ['pl_CloseMessage']

    @handler('DoDWWarp')
    def h_dw_warp(tr, a, vals, name):
        """0x320 DoDWWarp (pokeplatinum FieldSystem_StartDWWarp: the warp effect into the Distortion World, an app the script
        waits for). Step 7 (the Distortion World, built later: the user's order). A marked stub; the Warp after it leads to
        MAP_DISTORTION_WORLD_1F, which step 7 builds (notes/PLATINUM_HANDOFFS.md, "Chapter 9", the step 7 handoff)."""
        tr.job.stubs['DoDWWarp (step 7: the Distortion World is built later)'] += 1
        return ['pl_stub DoDWWarp  // STEP 7: the warp effect into the Distortion World (FieldSystem_StartDWWarp); '
                'notes/PLATINUM_HANDOFFS.md "Chapter 9"']

    @handler('2B5')
    def h_exit_location(tr, a, vals, name):
        """Platinum 0x2B5 map, x, z (pokeplatinum ScrCmd_2B5): the save's exit location, where an Escape Rope or Dig leads
        and the Town Map's spot inside. Sendoff Spring after the Distortion World sets the Spring Path (762, 714): the player
        came by a script warp, not by walking in. Black 2 remembers its escape point only when the player walks from the
        overworld into a cave (ov035 event_mapchange.c GameData_SetEscapeRopeZone), and no script command sets it: that would
        be C. Sendoff Spring has no Escape Rope; in Turnback Cave's rooms that allow one, it leads to the last cave entrance
        until the player walks out by the Spring Path once. The Harbor Inn's Darkrai dream (chapter 12) sets Canalave the
        same way. Listed as cosmetic (was a stub that did the same nothing)."""
        tr.job.approx['2B5 (the exit for an Escape Rope or Dig: no Black 2 command; Black 2 remembers its own when the '
                      'player walks into a cave)'] += 1
        return [f'// Platinum 0x2B5 {", ".join(map(str, vals))}: the exit location (Escape Rope, Dig): no Black 2 command']

# ---- end plat-ch9


# ---- plat-ch12 (2026-11-07): Platinum's chapter 12 (the post-game's event islands, Rotom's Room). Flower Paradise's Shaymin
# with Black 2's fateful-encounter mark, and Rotom's forms on Black 2's own party commands (macros in pearl_story.inc, block
# "plat-ch12"; two of them PearlB2 extension sub-commands, patches/platinum_postgame.py). Platinum only: Pearl's scripts use
# none of these. A command another chapter's block gave a handler first keeps it (as plat-ch7's _ch7_handler).
if version.PLATINUM:
    def _ch12_handler(cmd):
        def deco(fn):
            return fn if cmd in HANDLERS else handler(cmd)(fn)
        return deco

    @handler('StartFatefulEncounter')
    def h_fateful_encounter(tr, a, vals, name):
        """0x318 StartFatefulEncounter species, level (pokeplatinum Encounter_NewFatefulVsSpeciesAtLevel: a wild battle whose
        Pokémon has the fateful-encounter mark): Flower Paradise's Shaymin. PearlB2 extension 0xBE (patches/platinum_postgame.py):
        Black 2's static wild battle, as StartLegendaryBattle's, with PKM_PARAM_FATEFUL_ENCOUNTER set on the wild Pokémon; the
        caught Shaymin keeps it, so Floaroma's Gracidea is given (plat-ch3's FindPartySlotWithFatefulEncounterSpecies). Was a
        stub: no battle, nothing caught."""
        tr.last_battle = 'wild'
        return end_free_camera(tr, 'a battle', a) + [f'pl_StartFatefulEncounter {tr.var(vals[0])}, {tr.var(vals[1])}  // a wild '
                                                     f'battle; the Pokémon has the fateful-encounter mark']

    @handler('GetRotomFormsInSave')
    def h_rotom_forms_in_save(tr, a, vals, name):
        """0x302 GetRotomFormsInSave heat, wash, frost, fan, mow (pokeplatinum SaveData_GetRotomFormsInSave): 1 for each form
        some Rotom has, not an Egg, in the party, the Day Care or a box; Rotom's Room shows the appliance of each form nobody
        has. PearlB2 extension 0xBD (patches/platinum_postgame.py) reads all three; the macro spreads its bits (form n = bit n).
        Replaces plat-rooms' handler (every form 0: nothing in the game made a form before Rotom's Room's commands below)."""
        return [f'pl_GetRotomFormsInSave {", ".join(tr.var(v) for v in vals)}  // party, Day Care and boxes (ext 0xBD)']

    @handler('GetPartyRotomCountAndFirst')
    def h_rotom_count(tr, a, vals, name):
        """0x303 GetPartyRotomCountAndFirst count, slot (pokeplatinum ScrCmd_GetPartyRotomCountAndFirst): the party's Rotom in
        an appliance (form not 0, not an Egg), and the first one's slot (255: none). A party loop on Black 2's PokePartyIsEgg,
        PokePartyGetParam (species) and PokePartyGetForme."""
        return [f'pl_GetPartyRotomCountAndFirst {tr.var(vals[0])}, {tr.var(vals[1])}']

    @handler('SetRotomForm')
    def h_set_rotom_form(tr, a, vals, name):
        """0x304 SetRotomForm slot, move slot, move, form (pokeplatinum Pokemon_SetRotomForm: the form's move replaces the
        other form's, or goes in the first free slot, or in the move slot given; Thunder Shock when no move is left; the
        Pokédex records the form) = Black 2's PokePartyChangeRotomForme slot, move slot, form (ov012 s011C, PML_PkmChangeRotomForme:
        the same rule, the same five moves; PokeDex_RegistPkm), as Black 2's own appliance script (global 10315). Platinum's
        third argument (the move) is unused by its command too."""
        return [f'PokePartyChangeRotomForme {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[3])}  // SetRotomForm: the form '
                f'and its move']

    @handler('GetPartyMonForm2')
    def h_party_form2(tr, a, vals, name):
        """0x305 GetPartyMonForm2 slot, var = Black 2's PokePartyGetForme var, slot."""
        return [f'PokePartyGetForme {tr.var(vals[1])}, {tr.var(vals[0])}  // GetPartyMonForm2']

    @_ch12_handler('GetPartyMonMove')
    def h_party_move(tr, a, vals, name):
        """0x1CA GetPartyMonMove var, slot, move slot = Black 2's PokePartyGetMove (the same order)."""
        return [f'PokePartyGetMove {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}  // GetPartyMonMove']

    @_ch12_handler('CountRepeatedSpeciesInParty')
    def h_count_species(tr, a, vals, name):
        """0x2CB CountRepeatedSpeciesInParty var, species: how many party Pokémon (not Eggs) are that species = Black 2's
        PokePartyGetCountBySpecies species, var. (Species 0, Platinum's "any species twice", is used by no script: a stub.)"""
        if vals[1] == 0:
            return keep_stub(tr, a, vals, name)
        return [f'PokePartyGetCountBySpecies {tr.var(vals[1])}, {tr.var(vals[0])}  // CountRepeatedSpeciesInParty']

    @_ch12_handler('FindPartySlotWithSpecies')
    def h_find_species(tr, a, vals, name):
        """0x2DD FindPartySlotWithSpecies var, species: the first party slot (not an Egg) of that species, else 255 = Black 2's
        PokePartyFindBySpecies (pl_FindPartySlotWithSpecies)."""
        return [f'pl_FindPartySlotWithSpecies {tr.var(vals[0])}, {tr.var(vals[1])}']

    @_ch12_handler('OpenSummaryScreenTeachMove')
    def h_summary_teach(tr, a, vals, name):
        """0x2E7 OpenSummaryScreenTeachMove slot, move (pokeplatinum: the summary's move screen, a move to forget for the new
        one) = Black 2's CallPokeMoveReplace (the forget-a-move screen; it fades and reopens the field itself, so the fades and
        ReturnToField around it are dropped: _ch12_psel)."""
        return [f'pl_OpenSummaryScreenTeachMove {tr.var(vals[0])}, {tr.var(vals[1])}  // Black 2\'s forget-a-move screen']

    @_ch12_handler('GetSummarySelectedMoveSlot')
    def h_summary_slot(tr, a, vals, name):
        """0x2E8 GetSummarySelectedMoveSlot var: the move slot chosen, 4 (LEARNED_MOVES_MAX) when none."""
        return [f'pl_GetSummarySelectedMoveSlot {tr.var(vals[0])}']

    # Rotom's Room writes its two party selects and its move screen with a CloseMessage after the fade-out (FadeScreen,
    # WaitFadeScreen, CloseMessage, SelectMoveTutorPokemon / OpenSummaryScreenTeachMove, GetSelectedPartySlot /
    # GetSummarySelectedMoveSlot, ReturnToField, FadeScreen): Black 2's screens fade and reopen the field themselves, so the
    # fades and the ReturnToField are dropped, as poke_select_fades does for the pattern without the CloseMessage (a FieldOpen
    # on an open field hangs: plat-ch7). Only Rotom's Room has it (and the Battle Tower's, another shape: step 8).
    _psel_ch12_base = poke_select_fades

    def poke_select_fades(tr):
        out = _psel_ch12_base(tr)
        if not getattr(tr, '_psel_ch12', False):
            tr._psel_ch12 = True
            d, pd = tr.d, tr.job.pd
            nxt = {x: e for x, (e, op, args) in d.insns.items()}
            prv = {e: x for x, e in nxt.items()}
            name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
            pairs = {'SelectMoveTutorPokemon': 'GetSelectedPartySlot', 'OpenSummaryScreenTeachMove': 'GetSummarySelectedMoveSlot'}
            for c in [x for x in d.insns if name(x) in pairs]:
                m0 = prv.get(c)
                w0 = prv.get(m0)
                f0 = prv.get(w0)
                g = nxt.get(c)
                r = nxt.get(g)
                f1 = nxt.get(r)
                if (name(f0), name(w0), name(m0), name(g), name(r), name(f1)) == ('FadeScreen', 'WaitFadeScreen', 'CloseMessage',
                                                                               pairs[name(c)], 'ReturnToField', 'FadeScreen'):
                    out |= {f0, r, f1}
        return out
# ---- end plat-ch12


# ---- plat-tutors (2026-11-07): Platinum's party commands that Black 2's script commands can't do, on PearlB2 extension
# sub-commands 0xB0-0xB6 (the decomp's overlay 376, src/pearlb2/plat_party/; macros in pearl_story.inc block "plat-tutors";
# notes/EXT_COMMAND.md) and Black 2's own: the three shard tutors (Route 212, Snowpoint, the Survival Area) and their Shard
# lists, Pastoria's scarf man (contest conditions), the ribbon givers (Dr. Footstep, Julia, the Sunyshore Market, the
# Ribbon Syndicate), Dr. Footstep's footprints. The Pokémon Mansion's turn count needs no script: the battle's end writes
# the work (decomp src/pearlb2/resident/plat_party_ext.c). The tutors' forget-a-move screen and move read are plat-ch12's
# handlers (OpenSummaryScreenTeachMove, GetSummarySelectedMoveSlot, GetPartyMonMove, the fades). Platinum's tables come
# from its dump (b2tools/platinum_party_data.py). Platinum only: Pearl's scripts keep their 1.0 stubs.
# (v101-story: on for Pearl and Diamond too, version.PARTY_COMMANDS: their ribbon and footprint tables from their own dumps;
# Pearl's scripts have no shard tutor.)
if version.PARTY_COMMANDS:
    import platinum_party_data as PPD

    PL_PARTY_SLOT_NONE = 255                # Platinum's PARTY_SLOT_NONE: every move of the tutor (the Shard list)
    PL_MENU_CANCEL = 0xFFFE                 # MENU_CANCEL (-2): EXIT or B, as Black 2's list menu answers B
    PL_TUTOR_CMDS = ('ShowMoveTutorMoveSelectionMenu', 'CheckHasLearnableTutorMoves')

    def _tutor_menu_after(tr, a):
        """The command right after the one at a (address order) is a tutor's move list."""
        end = tr.d.insns[a][0] if a in tr.d.insns else None
        return end in tr.d.insns and tr.job.pd.cmd_name(tr.d.insns[end][1]) == 'ShowMoveTutorMoveSelectionMenu'

    _speaker_tutors_base = speaker

    def speaker(tr, a, line):
        # The question right before a tutor's move list goes to the plain window: Black 2's list menu prints an entry's
        # description (the move's Shards) only there (ov012 ListMenu_ShowDescription: SCRIPT_SUB_EVENT_SYSTEM_MSG; a person's
        # balloon gets none). Both h_message and the window dataflow (FileTr.speakers_in) ask here.
        if _tutor_menu_after(tr, a):
            return ('sys', None)
        return _speaker_tutors_base(tr, a, line)

    def _tutor_locations(tr, a, loc):
        """The tutor locations a command's location argument can be: a constant, or the values set into its var on every
        way in (message_var_values: the Shard list's common script, VAR_0x8004 set by each caller), else all three."""
        if loc < 0x4000:
            return [loc]
        values = message_var_values(tr, a, loc)
        return sorted(v for v in values if v in (0, 1, 2)) if values and all(v in (0, 1, 2) for v in values) else [0, 1, 2]

    def _file_locations(tr):
        """The tutor locations this file's tutor commands name (a move bought here is one of theirs)."""
        if getattr(tr, '_tutor_locs', None) is None:
            locs = set()
            for x, (e, op, args) in tr.d.insns.items():
                if tr.job.pd.cmd_name(op) in PL_TUTOR_CMDS:
                    locs |= set(_tutor_locations(tr, x, args[1][1]))
            tr._tutor_locs = sorted(locs) or [0, 1, 2]
        return tr._tutor_locs

    def _shard_text(costs):
        """A move's Shards in Platinum's words (bank 321: RED SHARDS .. GREEN SHARDS, "X n": its cost window), two to a line
        of the plain window, the second column lined up."""
        import gen4_text
        bank = gen4_text.bank(PPD.MENU_BANK)
        times = bank[PPD.TIMES_LINE]
        cells = [f'{bank[PPD.SHARD_LINES[k]]} ' + re.sub(r'\{STRVAR_1 \d+(?:, \d+)*\}', str(costs[k]), times) for k in range(4)]
        font = b2font.load(0)
        col = max(font.width(cells[0]), font.width(cells[2])) + 3 * font.width(' ')
        pad = lambda c: c + ' ' * max(1, round((col - font.width(c)) / font.width(' ')))
        return f'{pad(cells[0])}{cells[1]}\\n{pad(cells[2])}{cells[3]}'

    def _shard_line(tr, index):
        costs = PPD.tutor_moves()[0][index][1]
        return tr.job.line_text(('tutor_shards', index), _shard_text(costs))

    def _move_chain(tr, a, move, body, what):
        """For each move a tutor of this file teaches: when the move var holds it, body(index, move, costs)."""
        m, end = tr.var(move), f'{tr.prefix}_{a:04X}_{what}End'
        out = []
        for loc in _file_locations(tr):
            for i, mv, costs in PPD.location_moves(loc):
                nxt = f'{tr.prefix}_{a:04X}_{what}{i}'
                out += [f'WorkCmpConst {m}, {mv}', f'VMJumpIf CMP_NE, {nxt}'] + body(i, mv, costs) + [f'VMJump {end}',
                                                                                                       f'{nxt}:']
        return out + [f'{end}:']

    @handler('CheckHasLearnableTutorMoves')
    def h_tutor_any(tr, a, vals, name):
        """0x2E5 CheckHasLearnableTutorMoves slot, location, var (Pokemon_HasLearnableMovesAt): 1 if a move of that tutor is
        left for the Pokémon to learn, by Platinum's species-and-form masks = PearlB2 extension 0xB1. Was a stub: the tutor
        said "no moves to teach" or not by chance."""
        return [f'pl_CheckHasLearnableTutorMoves {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}  // '
                f'{PPD.LOCATIONS[vals[1]] if vals[1] < 3 else "the tutor"}\'s moves, Platinum\'s masks (ext 0xB1)']

    @handler('ShowMoveTutorMoveSelectionMenu')
    def h_tutor_menu(tr, a, vals, name):
        """0x2E6 ShowMoveTutorMoveSelectionMenu slot, location, var: the tutor's moves the Pokémon can learn and doesn't know
        (PARTY_SLOT_NONE: all of them, the Shard list), then EXIT; var = the move, MENU_CANCEL (-2) for EXIT or B. Black 2's
        list menu at the right edge (Platinum's is at the top right too), each move's name (word 2) in its entry and its Shards
        in Platinum's words in the entry's description line, which the plain window shows while the cursor is there (the
        question before it moves there: speaker). Each entry asks PearlB2 extension 0xB0 (Platinum's masks). Was a stub."""
        slot, loc, var = vals
        entry = tr.job.line_text(('tutor_move',), '{STRVAR_1 6, 2}')
        exit_line = tr.job.line_for(PPD.MENU_BANK, PPD.EXIT_LINE)
        out = [f'ListMenu_AnchorTopRight 31, 1, 0, 1, {tr.var(var)}  // {name}: Black 2\'s list menu, the Shards in each '
               f'entry\'s description line']
        locs = _tutor_locations(tr, a, loc)
        done = f'{tr.prefix}_{a:04X}_TutorExit'
        for L in locs:
            nxt = f'{tr.prefix}_{a:04X}_Tutor{L}'
            if len(locs) > 1:
                out += [f'WorkCmpConst {tr.var(loc)}, {L}', f'VMJumpIf CMP_NE, {nxt}']
            for i, mv, costs in PPD.location_moves(L):
                desc = _shard_line(tr, i)
                if slot == PL_PARTY_SLOT_NONE:
                    out.append(f'pl_TutorMenuAny {mv}, {entry}, {desc}  // tutor move {i}, Shards {"/".join(map(str, costs))}')
                else:
                    out.append(f'pl_TutorMenuMove {tr.var(slot)}, {i}, {mv}, {entry}, {desc}  // tutor move {i}, Shards '
                               f'{"/".join(map(str, costs))}')
            if len(locs) > 1:
                out += [f'VMJump {done}', f'{nxt}:']
        if len(locs) > 1:
            out.append(f'{done}:')
        return out + [f'ListMenuAdd {exit_line}, 65535, {PL_MENU_CANCEL}  // EXIT (MENU_CANCEL)', 'ListMenuShow']

    @handler('CheckCanAffordMove')
    def h_tutor_afford(tr, a, vals, name):
        """0x2EA CheckCanAffordMove move, var: 1 when the Bag holds the move's red, blue, yellow and green Shards (Platinum's
        table) = Black 2's ItemCheckAmount for each. Was a stub."""
        move, var = vals
        v = tr.var(var)
        assert move >= 0x4000, f'{name} with a constant move'
        return [f'WorkSetConst {v}, 0  // {name}: the Bag\'s Shards against the move\'s (Platinum\'s table)'] + _move_chain(
            tr, a, move, lambda i, mv, costs: [f'WorkSetConst {v}, 1'] + [f'pl_TutorShardCheck {it}, {n}, {v}'
                                                                        for it, n in zip(PPD.SHARDS, costs) if n], 'Afford')

    @handler('PayShardCost')
    def h_tutor_pay(tr, a, vals, name):
        """0x2EB PayShardCost move: the move's Shards out of the Bag = Black 2's ItemSub for each. Was a stub (the move was
        free)."""
        assert vals[0] >= 0x4000, f'{name} with a constant move'
        return [f'// {name}: the move\'s Shards (Platinum\'s table)'] + _move_chain(
            tr, a, vals[0], lambda i, mv, costs: [f'pl_TutorShardPay {it}, {n}' for it, n in zip(PPD.SHARDS, costs) if n],
            'Pay')

    @handler('ResetMoveSlot')
    def h_tutor_learn(tr, a, vals, name):
        """0x2E9 ResetMoveSlot slot, move slot, move (Party_ResetMonMoveSlot: the move there, its full PP, no PP Ups) = Black 2's
        PokePartyLearnMove (PokeParty_SetMove: the same). Was a stub (the move was never learned)."""
        return [f'PokePartyLearnMove {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}  // {name}']

    @handler('ShowShardCost')
    def h_tutor_cost(tr, a, vals, name):
        """0x2EC ShowShardCost x, y, move, var: Platinum's window of the move's four Shards next to the message. Here the same
        words in the plain window the Shard list's question was in (the next WaitABPress waits on it). Was a stub."""
        x, y, move, var = vals
        return [f'// {name} {x}, {y}: the move\'s Shards in the plain window'] + _move_chain(
            tr, a, move, lambda i, mv, costs: [f'pl_msg_sys {_shard_line(tr, i)}'], 'Cost')

    @handler('CloseShardCostWindow')
    def h_tutor_cost_close(tr, a, vals, name):
        return [f'// {name}: the Shards were in the plain window (its CloseMessage closes it)']

    @handler('GetPartyMonContestStat')
    def h_contest_stat(tr, a, vals, name):
        """0x281 GetPartyMonContestStat slot, type, var (MON_DATA_COOL + type): Black 2 keeps the five conditions as Platinum
        (PKM_PARAM_CONTEST_COOL 0x13 ..), but its PokePartyGetParam doesn't read them: PearlB2 extension 0xB3. Pastoria's scarf
        man (a scarf for a condition of 200 or more). Was a stub [Pearl too]."""
        slot, typ, var = vals
        if typ >= 0x4000:
            return [f'WorkSet PL_TMP2, {tr.var(typ)}', f'WorkAdd PL_TMP2, {PPD.CONTEST_COOL}',
                    f'pl_GetPartyMonParam {tr.var(var)}, {tr.var(slot)}, PL_TMP2  // {name}']
        return [f'pl_GetPartyMonParam {tr.var(var)}, {tr.var(slot)}, {PPD.CONTEST_COOL + typ:#x}  // {name} {typ}']

    def _ribbon(tr, ribbon):
        import gen4_text
        return gen4_text.bank(PPD.RIBBON_NAMES_BANK)[PPD.ribbon_name_line(ribbon)]

    @handler('GetPartyMonRibbon')
    def h_get_ribbon(tr, a, vals, name):
        """0x230 GetPartyMonRibbon var, slot, ribbon: Platinum's ribbon id (generated/ribbons.txt) -> its MON_DATA field
        (sRibbonDataTable, from the dump) -> Black 2's PKM_PARAM (platinum_party_data.b2_param), read by PearlB2 extension
        0xB3 (Black 2's PokePartyGetParam reads no ribbon). Was a stub [Pearl too]."""
        var, slot, ribbon = vals
        if ribbon >= 0x4000:
            return keep_stub(tr, a, vals, name)
        p = PPD.ribbon_param(ribbon)
        return [f'pl_GetPartyMonParam {tr.var(var)}, {tr.var(slot)}, {p:#x}  // {name}: the {_ribbon(tr, ribbon)}']

    @handler('SetPartyMonRibbon')
    def h_set_ribbon(tr, a, vals, name):
        """0x231 SetPartyMonRibbon slot, ribbon: the same parameter set (PearlB2 extension 0xB4; Black 2 has no such set).
        Platinum also tells the TV (sub_0206DDB8): Black 2's TV has no such show. Was a stub [Pearl too]."""
        slot, ribbon = vals
        if ribbon >= 0x4000:
            return keep_stub(tr, a, vals, name)
        p = PPD.ribbon_param(ribbon)
        return [f'pl_SetPartyMonRibbon {tr.var(slot)}, {p:#x}  // {name}: the {_ribbon(tr, ribbon)}']

    @handler('CountPartyRibbons')
    def h_count_ribbons(tr, a, vals, name):
        """0x22F CountPartyRibbons var: Platinum's 80 ribbons that some Pokémon of the party has, no Egg (the Ribbon
        Syndicate lets in a player with 10) = PearlB2 extension 0xB5. Was a stub [Pearl too]."""
        return [f'pl_CountPartyRibbons {tr.var(vals[0])}  // {name}']

    @handler('BufferRibbonName')
    def h_ribbon_name(tr, a, vals, name):
        """0x232 BufferRibbonName word, ribbon: Platinum's name for it (bank 484), a line of the zone's text, into the word
        buffer at run time (PearlB2 extension 0xB6: Black 2 has no word command for a ribbon). Julia's seven ribbons meet in one
        "received the ..." line. Was a stub [Pearl too]."""
        word, ribbon = vals
        if ribbon >= 0x4000:
            return keep_stub(tr, a, vals, name)
        nm = _ribbon(tr, ribbon)
        return [f'pl_BufferLineWord {word}, {tr.job.line_text(("ribbon_name", ribbon), nm)}  // {name}: the {nm}']

    @handler('GetPartyMonFootprintType')
    def h_footprint(tr, a, vals, name):
        """0x23A GetPartyMonFootprintType print var, type var, slot (footprint_type.c, from the dump): Dr. Footstep's five
        kinds of footprint and whether the species has one = PearlB2 extension 0xB2. Was a stub [Pearl too]: his reading was
        any one by chance."""
        return [f'pl_GetPartyMonFootprintType {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}  // {name}']

    @handler('GetPartyMonEVTotal')
    def h_ev_total(tr, a, vals, name):
        """0x233 GetPartyMonEVTotal var, slot = Black 2's PokePartyGetEVTotal (the six effort values added; the Sunyshore
        Market's Effort Ribbon at 510). Was a stub [Pearl too]."""
        return [f'PokePartyGetEVTotal {tr.var(vals[0])}, {tr.var(vals[1])}  // {name}']
# ---- end plat-tutors
# ---- plat-music (2026-11-07): Platinum's songs and sounds in its scripts (notes/MUSIC.md "Platinum"). Platinum's sound ids
# past Pearl's (its SEQ_PL_* songs 1189-1222, its SEQ_SE_PL_* sounds 1350-1499) take Platinum's names (the decomp's
# res/sound/pl_sound_data.json); the songs its scripts start (version.STORY_SONGS: Looker's theme, the Villa's piano, audio
# system and music box, Spear Pillar's cutscene, the Poké Radar's song) and its fanfares (version.STORY_FANFARES) play as
# SEQ_PEARL_<name>, installed by patches/sinnoh_music.py, as Pearl's own story songs do. Platinum only: Pearl's and
# Diamond's scripts have none of these ids, and the rows are empty for them.
if version.PLATINUM:
    _PL_SEQ_NAMES = None
    _seq_name_pearl = seq_name

    def seq_name(v):        # noqa: F811  (Pearl's names, and Platinum's own past them)
        """(Black 2 sound constant or None, name) for a Platinum sound id: Pearl's name (pokediamond's sndseq.h), or
        Platinum's for the ids it added (SEQ_PL_*, SEQ_SE_PL_*)."""
        global _PL_SEQ_NAMES
        if _PL_SEQ_NAMES is None:
            info = json.load(open(os.path.join(PLATINUM, 'res', 'sound', 'pl_sound_data.json')))['seqInfo']
            _PL_SEQ_NAMES = {i: e['name'] for i, e in enumerate(info) if e.get('name', '').startswith(('SEQ_PL_', 'SEQ_SE_PL_'))}
        name = _PL_SEQ_NAMES.get(v)
        if name:
            return SOUND.get(name), name
        return _seq_name_pearl(v)

    # Platinum's own sounds -> Black 2's (as SOUND above: [guess] = chosen by name and use). SEQ_SE_PL_KUSARI (Spear
    # Pillar's red chains) and SEQ_SE_PL_SYUWA (the Distortion World's portals) have no Black 2 sound found: they stay counted
    # stubs (Black 2 plays only the sounds its sound groups have loaded, so Platinum's own can't simply be added: C).
    SOUND.update({
        'SEQ_SE_PL_COIN': 'SEQ_SE_SYS_22',     # [guess] the Game Corner's coins: the cash register (Pearl's SEQ_SE_DP_REGI)
    })
    # (plat-dw-rom) Platinum's own sounds PearlB2 installs (patches/platinum_dw.py PLAT_SOUNDS; include/pearlb2.h PLATSND_*):
    # SEQ_SE_PL_SYUWA (the Distortion World's portals) and SEQ_SE_PL_KUSARI (Spear Pillar's chains) play by number through
    # extension 0x25 (resident PearlB2_PlatSound: loaded when played; silent in a build without them, as the stubs were)
    PLAT_SE = {'SEQ_SE_PL_SYUWA': 0, 'SEQ_SE_PL_KUSARI': 10}
    _h_sound_before_plat_se = HANDLERS['PlaySE']

    @handler('PlaySE')
    def h_playse_platinum(tr, a, vals, name):
        b2, pname = seq_name(vals[0])
        if pname in PLAT_SE:
            return [f'pl_PlatSound {PLAT_SE[pname]}  // Platinum {pname} (patches/platinum_dw.py)']
        return _h_sound_before_plat_se(tr, a, vals, name)
    PEARL_SONGS = PEARL_SONGS + version.STORY_SONGS      # noqa: F811  (h_sound plays these as SEQ_PEARL_<name>)
    _h_sound_pearl = HANDLERS['PlayFanfare']

    @handler('PlayFanfare')
    def h_fanfare_platinum(tr, a, vals, name):
        """PlayFanfare of Platinum's own fanfares (version.STORY_FANFARES: the Battle Hall's BP fanfare, SEQ_PL_POINTGET3):
        sinnoh_music installs them with Black 2's ME player. A WaitFanfare follows, so a build without them plays Black 2's
        item jingle instead of nothing (a WaitFanfare after a stub hangs: 2026-10-18)."""
        b2, pname = seq_name(vals[0])
        if pname not in version.STORY_FANFARES:
            return _h_sound_pearl(tr, a, vals, name)
        return [f'#ifdef SEQ_PEARL_{pname[4:]}', f'    pl_PlayFanfare SEQ_PEARL_{pname[4:]}  // Platinum {pname}', '#else',
                f'    pl_PlayFanfare SEQ_ME_ITEM  // Black 2 stand-in (a build without sinnoh_music): a jingle, for the WaitFanfare',
                '#endif']

    @handler('GetCurrentBGM', 'SetScenePlayBGMMusicBox', 'SetFieldScene')
    def h_music_box_platinum(tr, a, vals, name):
        """The Villa's music box (pokeplatinum scrcmd_sound.c): GetCurrentBGM keeps the song that plays, SetScenePlayBGMMusicBox
        plays SEQ_PL_TOWN02 as the music box, SetFieldScene the kept song again. = Black 2's BGMPlayPush (the field's song
        kept on Black 2's BGM stack, the box's song played) and BGMPop (the kept song back). Replaces plat-rooms' comment."""
        if name == 'GetCurrentBGM':
            return [f'// GetCurrentBGM {tr.var(vals[0])}: the song that plays is kept by the BGMPlayPush below']
        if name == 'SetScenePlayBGMMusicBox':
            return ['#ifdef SEQ_PEARL_PL_TOWN02', '    BGMPlayPush SEQ_PEARL_PL_TOWN02  // Platinum SEQ_PL_TOWN02: the music box',
                    '#else', '// SetScenePlayBGMMusicBox: no Platinum songs in this build, the room\'s song plays on', '#endif']
        return ['#ifdef SEQ_PEARL_PL_TOWN02', f'    BGMPop 0, 0  // SetFieldScene {tr.var(vals[0])}: the kept song again',
                '#endif']

    _h_spear_pillar_cutscene = HANDLERS.get('2FB')

    @handler('2FB')
    def h_spear_pillar_cutscene_music(tr, a, vals, name):
        """plat-ch9's Spear Pillar cutscene (0x2FB) with the cutscene's music (overlay 100, ov100_021D1C44.c): the song that
        plays fades out with line 22 (Sound_FadeOutBGM 0, 10), SEQ_PL_EV_GIRA starts after line 23 (state 11, before the
        shadow's line 24), SEQ_PL_EV_GIRA2 after line 25 (state 18, before Giratina's cry and line 26), and the cutscene's
        end stops it (Sound_StopBGM); the script's warp to the distorted pillar then plays that zone's song."""
        out = _h_spear_pillar_cutscene(tr, a, vals, name)
        if not out or out[0].startswith('pl_stub'):
            return out

        def group_start(n):
            """Where the lines before Spear Pillar line n begin (its shake, cries and name buffer)."""
            at = next(i for i, l in enumerate(out) if re.match(rf'\s*pl_msg\w* {n}\b', l))
            while at and out[at - 1].strip().startswith(('pl_ShakeCamera', 'pl_PlayCry', 'pl_BufferPlayerName')):
                at -= 1
            return at

        def song(s):
            return [f'#ifdef SEQ_PEARL_{s[4:]}', f'    pl_PlayMusic SEQ_PEARL_{s[4:]}  // Platinum {s}: the cutscene\'s song',
                    '#endif']
        for n, lines in ((26, song('SEQ_PL_EV_GIRA2')), (24, song('SEQ_PL_EV_GIRA')),
                         (22, ['pl_FadeOutBGM 10  // the cutscene fades the song out (Sound_FadeOutBGM 0, 10)'])):
            at = group_start(n)
            out[at:at] = lines
        at = len(out) - (out[-1] == 'pl_CloseMessage')
        out[at:at] = ['#ifdef SEQ_PEARL_PL_EV_GIRA2', '    pl_FadeOutBGM 1  // the cutscene\'s end stops its song (Sound_StopBGM)',
                      '#endif']
        tr.job.approx['2FB: the cutscene\'s songs SEQ_PL_EV_GIRA and EV_GIRA2 with its lines'] += 1
        return out
# ---- end plat-music


# ---- plat-trades (2026-11-07): Gen 4's in-game trades, the Mining Museum's fossil restorer and ActivateRoamingPokemon as
# real commands (pearl_story.inc block "plat-trades"; decomp src/pearlb2/resident/npc_trade.c, roamers.c; extension
# sub-commands 0xA7, 0xA8: notes/EXT_COMMAND.md). On by version rows (version.NPC_TRADES, FOSSIL_RESTORER,
# ROAMER_COMMAND): Platinum now; Pearl's and Diamond's 1.0 keep their stubs until 1.0.1 turns the rows on (their
# commands have the same names here: FileTr's cmd_name). A command another block gave a handler first keeps it.
if version.NPC_TRADES:
    import npc_trade_data as NTD

    _TRADE_MENUS = ('OpenPartyMenuForTrade',)

    def _prev_insn_trades(tr, a):
        if getattr(tr, '_prev_trades', None) is None:
            tr._prev_trades = {e: x for x, (e, op, args) in tr.d.insns.items()}
        return tr._prev_trades.get(a)

    def _trade_at(tr, a):
        """The trade of the file's InitNPCTrade before address a (the nearest; the one of the file if none is before)."""
        pd = tr.job.pd
        inits = sorted((x, args[0][1]) for x, (e, op, args) in tr.d.insns.items() if pd.cmd_name(op) == 'InitNPCTrade')
        assert inits, f'{tr.f}: a trade command without InitNPCTrade'
        before = [n for x, n in inits if x < a]
        return before[-1] if before else inits[0][1]

    def _trade_name(n):
        t = NTD.trades()[n]
        return f'{t["nickname"]} (species {t["species"]}) for species {t["wanted"]}'

    @handler('OpenPartyMenuForTrade')
    def h_trade_menu(tr, a, vals, name):
        """0x2A5 OpenPartyMenuForTrade (pokeplatinum FieldSystem_OpenPartyMenu_SelectForTrade: the party menu, any Pokémon
        may be picked, an Egg too: GetPartyMonSpecies then answers no species) = Black 2's party select (CallPokeSelect).
        It fades and reopens the field itself, so Platinum's fades and ReturnToField around it are dropped (poke_select_fades
        below). Platinum's ball-capsule question has no Black 2 counterpart (no Ball Capsules)."""
        return ['pl_ChoosePokemonMenu  // OpenPartyMenuForTrade: Black 2\'s party select (CallPokeSelect)']

    _h_selected_slot_trades_base = HANDLERS['GetSelectedPartySlot']

    @handler('GetSelectedPartySlot')
    def h_selected_slot_trade(tr, a, vals, name):
        p = _prev_insn_trades(tr, a)
        if p is not None and tr.job.pd.cmd_name(tr.d.insns[p][1]) in _TRADE_MENUS:
            return [f'pl_GetSelectedPartySlot {tr.var(vals[0])}  // the slot, 255 when cancelled (as Platinum)']
        return _h_selected_slot_trades_base(tr, a, vals, name)

    _psel_trades_base = poke_select_fades

    def poke_select_fades(tr):
        out = _psel_trades_base(tr)
        if not getattr(tr, '_psel_trades', False):
            tr._psel_trades = True
            d, pd = tr.d, tr.job.pd
            nxt = {x: e for x, (e, op, args) in d.insns.items()}
            name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
            for c in [x for x in d.insns if name(x) in _TRADE_MENUS]:
                w0 = _prev_insn_trades(tr, c)
                f0 = _prev_insn_trades(tr, w0) if w0 is not None else None
                g = nxt.get(c)
                r = nxt.get(g)
                f1 = nxt.get(r)
                if (name(f0), name(w0), name(g), name(r), name(f1)) == ('FadeScreen', 'WaitFadeScreen',
                                                                      'GetSelectedPartySlot', 'ReturnToField', 'FadeScreen'):
                    out |= {f0, r, f1}
        return out

    @handler('InitNPCTrade')
    def h_trade_init(tr, a, vals, name):
        """0x226 InitNPCTrade trade: Platinum loads the trade's data for the commands after it. Here they take the trade
        from this line (the generator: GetNPCTradeRequestedSpecies a constant, StartNPCTrade its argument)."""
        return [f'// InitNPCTrade {vals[0]}: {_trade_name(vals[0])} (the commands below name it)']

    @handler('GetNPCTradeRequestedSpecies')
    def h_trade_wanted(tr, a, vals, name):
        """0x228 GetNPCTradeRequestedSpecies var: the species the trade wants, from the dump's table (npc_trade_data)."""
        n = _trade_at(tr, a)
        return [f'pl_SetVarFromValue {tr.var(vals[0])}, {NTD.requested_species(n)}  // GetNPCTradeRequestedSpecies: '
                f'trade {n} wants species {NTD.requested_species(n)}']

    @handler('GetNPCTradeSpecies')
    def h_trade_offered(tr, a, vals, name):
        """0x227 GetNPCTradeSpecies var: the species the trade gives."""
        n = _trade_at(tr, a)
        return [f'pl_SetVarFromValue {tr.var(vals[0])}, {NTD.offered_species(n)}  // GetNPCTradeSpecies: trade {n} gives '
                f'species {NTD.offered_species(n)}']

    @handler('StartNPCTrade')
    def h_trade_start(tr, a, vals, name):
        """0x229 StartNPCTrade slot = extension 0xA7 (pl_StartNPCTrade): Black 2's trade event with the Pokémon made by
        Platinum's rules (decomp resident/npc_trade.c; the table: patches/npc_trades.py). It fades and reopens the field
        itself, as Platinum's trade task does."""
        n = _trade_at(tr, a)
        return [f'pl_StartNPCTrade {n}, {tr.var(vals[0])}  // {_trade_name(n)}: Black 2\'s trade event and demo']

    @handler('FinishNPCTrade')
    def h_trade_finish(tr, a, vals, name):
        return ['// FinishNPCTrade: nothing to free (the trade event frees its own)']


if version.FOSSIL_RESTORER:
    import fossil_data as FOS

    @handler('GetFossilCount')
    def h_fossil_count(tr, a, vals, name):
        """0x1F1 GetFossilCount var: the Bag's count of every fossil of the dump's table, added up (Black 2's ItemGetCount)."""
        v = tr.var(vals[0])
        return [f'pl_SetVarFromValue {v}, 0  // GetFossilCount: every fossil in the Bag, added up'] + \
            [f'pl_FossilCountAdd {v}, {item}  // {FOS.ITEM_NAMES.get(item, item)}' for item, sp in FOS.table()]

    @handler('GetSpeciesFromFossil')
    def h_fossil_species(tr, a, vals, name):
        """0x1F4 GetSpeciesFromFossil var, item: the fossil's species (0 for any other item)."""
        v, item = tr.var(vals[0]), vals[1]
        first = f'WorkSet PL_TMP, {tr.var(item)}' if item >= 0x4000 else f'WorkSetConst PL_TMP, {item}'
        return [f'{first}  // GetSpeciesFromFossil: the item', f'pl_SetVarFromValue {v}, 0'] + \
            [f'pl_FossilSpecies {v}, {i}, {s}  // {FOS.ITEM_NAMES.get(i, i)}: {FOS.SPECIES_NAMES.get(s, s)}'
             for i, s in FOS.table()]

    @handler('FindFossilAtThreshold')
    def h_fossil_find(tr, a, vals, name):
        """0x1F5 FindFossilAtThreshold item var, index var, threshold: the first fossil (the table's order) where the Bag's
        counts added up reach the threshold, its item and index (0, 0 when none)."""
        item, index, thr = tr.var(vals[0]), tr.var(vals[1]), vals[2]
        done = f'.Lfossil_{tr.prefix}_{a:04X}'
        out = [f'WorkSet PL_TMP3, {tr.var(thr)}' if thr >= 0x4000 else f'WorkSetConst PL_TMP3, {thr}',
               f'WorkSetConst PL_TMP2, 0  // FindFossilAtThreshold: the counts so far',
               f'pl_SetVarFromValue {item}, 0', f'pl_SetVarFromValue {index}, 0']
        out += [f'pl_FossilFind {item}, {index}, {i}, {k}, {done}  // {FOS.ITEM_NAMES.get(i, i)}'
                for k, (i, s) in enumerate(FOS.table())]
        return out + [f'{done}:']

    # The Museum's fossil menu (Platinum's MiningMuseum_FossilMenuLoop) adds each fossil's entry by a line in a var: the
    # fossil's index plus MenuEntries_Text_Fossil_OldAmber (SetVarFromVar V, W; AddVar V, base; AddMenuEntry V, value).
    # Black 2's ListMenuAdd takes a fixed line, so the entry is written once for every value W is compared with in the
    # file (0-6: the loop's CallIfEq chain), each picked by V. Only the Museum has a menu line in a var.
    _h_menu_add_fossil_base = HANDLERS['AddMenuEntry']

    def _var_line_values(tr, a, var):
        """[(line, ...)] the var can hold at a (SetVarFromVar var, W; AddVar var, base; W's compared values), or None."""
        pd = tr.job.pd
        p1 = next((x for x, (e, op, args) in tr.d.insns.items() if e == a), None)
        p2 = next((x for x, (e, op, args) in tr.d.insns.items() if e == p1), None) if p1 is not None else None
        if p1 is None or p2 is None:
            return None
        (_, op1, args1), (_, op2, args2) = tr.d.insns[p1], tr.d.insns[p2]
        if (pd.cmd_name(op1), pd.cmd_name(op2)) != ('AddVar', 'SetVarFromVar') or args1[0][1] != var or args2[0][1] != var:
            return None
        base, w = args1[1][1], args2[1][1]
        if base >= 0x4000:
            return None
        ks = sorted({args[1][1] for x, (e, op, args) in tr.d.insns.items()
                     if pd.cmd_name(op) == 'CompareVarToValue' and args[0][1] == w and args[1][1] < 0x4000})
        return [base + k for k in ks] or None

    @handler('AddMenuEntryImm', 'AddMenuEntry', 'AddListMenuEntry')
    def h_menu_add_var_line(tr, a, vals, name):
        if vals[0] < 0x4000:
            return _h_menu_add_fossil_base(tr, a, vals, name)
        lines = _var_line_values(tr, a, vals[0])
        if not lines:
            return _h_menu_add_fossil_base(tr, a, vals, name)
        end, out = f'{tr.prefix}_{a:04X}_LineDone', []
        for k, line in enumerate(lines):
            nxt = f'{tr.prefix}_{a:04X}_Line{k}'
            out += [f'WorkCmpConst {tr.var(vals[0])}, {line}  // {name}: the line in {tr.var(vals[0])}',
                    f'VMJumpIf CMP_NE, {nxt}']
            out += _h_menu_add_fossil_base(tr, a, [line] + list(vals[1:]), name)
            out += [f'VMJump {end}', f'{nxt}:']
        return out + [f'{end}:']


if version.ROAMER_COMMAND:
    @handler('ActivateRoamingPokemon')
    def h_roamer(tr, a, vals, name):
        """0x21C ActivateRoamingPokemon slot = extension 0xA8 (pl_ActivateRoamingPokemon): the roamer of Gen 4's slot is
        released now (decomp resident/roamers.c; Platinum's five slots from patches/roamers.py)."""
        return [f'pl_ActivateRoamingPokemon {vals[0]}  // the roamer of slot {vals[0]} released (Black 2\'s roamer save)']
# ---- end plat-trades


# ---- v101-story (2026-11-07): 1.0.1's new script fixes for Pearl and Diamond (work/agents/V101_BRIEF.md "v101-story";
# pearl_story.inc block "v101-story"). The Platinum gates they turn on are the rows in version.py's block of the same name.
if version.DEOXYS_FORMS:
    @handler('CheckPartyHasSpecies2')
    def h_has_species2(tr, a, vals, name):
        """Pearl 0x262 CheckPokemonInParty species, var (pokediamond ScrCmd_CheckPokemonInParty: Party_HasMon, any party
        Pokémon of that species): Veilstone's meteorites ask for a Deoxys. As 0x1C1's CheckPartyHasSpecies (Black 2's
        PokePartyFindBySpecies). Was a stub: the var kept its last value. 0x262's arguments are species, var (0x1C1's are
        var, species), so they swap here (2026-11-08: they didn't, and every meteorite read species 0)."""
        return h_has_species(tr, a, [vals[1], vals[0]], 'CheckPartyHasSpecies')

    @handler('ChangeDeoxysForm')
    def h_deoxys_form(tr, a, vals, name):
        """Pearl 0x263 SetDeoxysForm form (pokediamond ScrCmd_SetDeoxysForm: each party Deoxys to that form, its stats
        recalculated, the Pokédex records it) = Black 2's PokePartySetForme over the party (PokeParty_ChangeForme,
        PokeDex_RegistPkm), as plat-ch9's Giratina. Veilstone's four meteorites: Normal 0, Attack 1, Defense 2, Speed 3 (the
        same numbers in Black 2). Was a stub: Deoxys never changed."""
        return [f'pl_ChangeDeoxysForm {tr.var(vals[0])}  // each party Deoxys to form {tr.var(vals[0])}']

if version.UNDERGROUND_GIFTS:
    UNDERGROUND_FEATS = {'GetUndergroundTalkCounter': 'people met in the tunnels',
                         'GetUndergroundItemsGivenAway': 'items given away there',
                         'GetUndergroundFossilsUnearthed': 'Fossils dug up', 'GetUndergroundTrapsSet': 'Traps set'}

    @handler(*UNDERGROUND_FEATS)
    def h_underground_feat(tr, a, vals, name):
        """Pearl 0x293, 0x286, 0x287, 0x288 (the Underground's records: people met, items given away, Fossils dug up, Traps
        set): Hearthome's man gives a Crystal for 100 of each. This Underground has no digging, no Traps and no other
        players, so the record counts as reached (version.UNDERGROUND_GIFTS): he gives them one a talk, after his other
        goods. Was a stub: the var kept a smaller value, the Crystals never came."""
        tr.job.approx[f'{name} (the Underground has no such feat here: counted as 100)'] += 1
        return [f'WorkSetConst {tr.var(vals[0])}, 100  // {name}: {UNDERGROUND_FEATS[name]}, which this Underground '
                f'has none of: counted as reached']

if version.GAME_CORNER_CLOSED:
    @handler('CheckBonusRoundStreak')
    def h_bonus_streak(tr, a, vals, name):
        """Pearl 0x275 (the Game Corner: ten straight bonus rounds on the slots, for the coin clerk's TM64): the slots are
        closed here (the lead's choice for 1.0.1), so it counts as met; the clerk stands at the closed line
        (version.MOVED_PEOPLE). Was a stub that left the Coin Case check's 1 in the var: the same answer, by chance."""
        tr.job.approx['CheckBonusRoundStreak (the slots are closed: met)'] += 1
        return [f'WorkSetConst {tr.var(vals[0])}, 1  // CheckBonusRoundStreak: the slots are closed, counted as met']

    @handler('CheckCanAddCoins')
    def h_can_add_coins(tr, a, vals, name):
        """Pearl 0x276 CanGiveCoins var, count: the Coin Case's room. Coins have no use while the slots are closed and Black
        2 has no Coins to give (AddCoins stays a stub), so it answers 0: the clerk's sale ends on her "can't" line (bank 139
        line 5, data/pearl_text_edits.json: the slots are closed) and she takes no money (2026-11-08: the stub left the
        money check's 1 in the var, so she took $1,000 or $10,000 for nothing; found by plat-stubs)."""
        tr.job.approx['CheckCanAddCoins (the slots are closed: no Coins sold)'] += 1
        return [f'WorkSetConst {tr.var(vals[0])}, 0  // CheckCanAddCoins: the slots are closed, no Coins sold']

if version.TOWER_TROPHIES:
    @handler('1DF')
    def h_tower_trophy(tr, a, vals, name):
        """Pearl 0x1DF var (pokediamond sub_0205FE10): the Battle Tower's trophy for a 20-, 50- or 100-win streak, 1-3, 4 when
        the PC is full, 0 none = pearl_story.inc pl_TowerTrophy (decomp extension 0x91, 0x92). The lobby's attendant
        gives the Bronze, Silver and Gold Trophy goods with Pearl's lines. Was "none here" (h_tower_none). (plat-stubs)
        Platinum's 0x1DF is the same (pokeplatinum sub_0206BDBC: Teala in its Tower's lobby) on its Single record streak only
        (pearl_story.inc pl_TowerTrophyStreak)."""
        return [f'pl_TowerTrophy {tr.var(vals[0])}  // Pearl 0x1DF: the trophy for the longest streak, given once each']

    @handler('1E0')
    def h_tower_trophy_due(tr, a, vals, name):
        """Pearl 0x1E0 var (pokediamond sub_0205FF5C): the trophy 0x1DF would give now, without giving it = pearl_story.inc
        pl_TowerTrophyDue (1-3, 0 none; Pearl's 4-6 for an earlier try with a full PC read 1-3). The lobby's map script
        shows the trophy attendant when it isn't 0 (2026-11-08: it was "none here", so he never showed)."""
        return [f'pl_TowerTrophyDue {tr.var(vals[0])}  // Pearl 0x1E0: a trophy due (the attendant shows)']

if version.ACCESSORY_SHOP:
    SHOP_BANK = 516                      # Pearl's flower shop: the zone's lines, then the shop app's (pokediamond ov06_0224D70C)
    SHOP_LINES = dict(greet=4, thanks=5, which=6, confirm=7, ok=8, few=9, full=10, bye=11, got=12, all=13, berry=16,
                      needed=17, exit=19)
    FIRST_BERRY = 149                    # ITEM_CHERI_BERRY: the rows' Berry numbers count from it (Black 2's the same)

    def accessory_shop_rows():
        """[(Accessory, Berry item, how many)] of Pearl's shop (overlay 6, pokediamond ov06_02252080: 22 rows of three u32,
        found by their first two: the Red Flower for 10 Razz Berries, the Pink Flower for 10 Bluk Berries). (plat-stubs,
        2026-11-08) Platinum's own: overlay 7 (pokeplatinum overlay007/accessory_shop.c sAccessoryShop_ItemLists, the same
        Accessories 50-71), its first two the Red Flower for one Cheri Berry, the Pink Flower for one Chesto Berry."""
        import contest_data
        rom = Rom(version.WORLD_DUMP)
        ov, first = (7, (50, 0, 1, 51, 1, 1)) if version.PLATINUM else (6, (50, 15, 10, 51, 16, 10))
        ram, o = contest_data.overlay(rom, ov)
        pat = struct.pack('<6I', *first)
        at = o.find(pat)
        assert at >= 0 and o.find(pat, at + 1) < 0, f'the Accessory shop\'s table: not found once in overlay {ov}'
        rows = [struct.unpack_from('<3I', o, at + 12 * k) for k in range(22)]
        assert [a for a, b, n in rows] == list(range(50, 72)) and all(b < 64 and 0 < n < 1000 for a, b, n in rows), rows
        return [(a, FIRST_BERRY + b, n) for a, b, n in rows]

    @handler('ShowAccessoryShop')
    def h_accessory_shop(tr, a, vals, name):
        """Pearl 0x257 AccessoriesShop (pokediamond scrcmd_mart.c, sub_02038AD0: overlay 6's berry exchange; Platinum's
        overlay007/accessory_shop.c is the same screen with other prices): its greeting, a list of Pearl's 22 Accessories
        with the Berries each costs in the entry's description line (the plain window, as Black 2's list menu shows it),
        the question, the Bag's Berries and the Fashion Case's room checked (pl_CanFitAccessory, the 1.0 Super Contests'),
        the Berries taken (ItemSub) and the Accessory given (pl_AddAccessory), Pearl's lines (bank 516) with the names and
        counts written in; the thanks once every Accessory is traded (none fits any more). The shop's "In Bag: n" line has
        no place here. Was a stub: the clerk said nothing."""
        import gen4_text
        bank = gen4_text.bank(SHOP_BANK)
        acc, berry, plural = gen4_text.bank(338), gen4_text.bank(344), gen4_text.bank(347)
        rows = accessory_shop_rows()
        L = lambda key, text: tr.job.line_text(('accessory_shop',) + key, text)
        line = lambda n: tr.job.line_for(SHOP_BANK, SHOP_LINES[n])

        def fill(src, k):
            ac, it, n = rows[k]
            names = {0: plural[it] if n > 1 else berry[it], 1: str(n), 2: acc[ac]}
            return gen4_text._STRVAR.sub(lambda m: names.get(int(m.group(2)), m.group(0)), src)
        p = f'{tr.prefix}_{a:04X}_Acc'
        out = [f'// Pearl 0x257 AccessoriesShop: Pearl\'s berry exchange (overlay 6) in Black 2\'s list menu, its lines (bank 516)',
               'MsgWinCloseAll', f'pl_msg_sys {line("greet")}', 'pl_WaitButton',
               'WorkSetConst PL_TMP3, 0  // the Accessories that fit no more']
        for k, (ac, it, n) in enumerate(rows):
            out += [f'pl_CanFitAccessory {ac}, 1, PL_TMP', 'WorkCmpConst PL_TMP, 0', f'VMJumpIf CMP_NE, {p}Fit{k}',
                    'WorkAdd PL_TMP3, 1', f'{p}Fit{k}:']
        out += [f'WorkCmpConst PL_TMP3, {len(rows)}', f'VMJumpIf CMP_EQ, {p}AllDone', f'{p}Menu:',
                f'pl_msg_sys {line("which")}',
                'ListMenu_AnchorTopRight 31, 1, 0, 1, PVAR_8004']
        for k, (ac, it, n) in enumerate(rows):
            desc = L(('desc', k), fill(bank[SHOP_LINES['berry']], k) + '\\n' + fill(bank[SHOP_LINES['needed']], k).rstrip())
            out.append(f'ListMenuAdd {L(("entry", k), acc[ac])}, {desc}, {k}  // the {acc[ac]}: {n} of item {it}')
        out += [f'ListMenuAdd {line("exit")}, 65535, 65534  // EXIT (B answers 65534 too)', 'ListMenuShow',
                f'WorkCmpConst PVAR_8004, {len(rows)}', f'VMJumpIf CMP_LT, {p}Pick',
                'MsgWinCloseAll', f'pl_msg_sys {line("bye")}', 'pl_WaitButton', f'VMJump {p}End', f'{p}Pick:']
        for k, (ac, it, n) in enumerate(rows):
            out += [f'WorkCmpConst PVAR_8004, {k}', f'VMJumpIf CMP_NE, {p}Row{k}',
                    'MsgWinCloseAll', f'pl_msg_sys {L(("confirm", k), fill(bank[SHOP_LINES["confirm"]], k))}',
                    'pl_ShowYesNoMenu PVAR_800C', 'pl_CompareVarToValue PVAR_800C, 1', f'pl_GoToIf 1, {p}Menu',
                    f'ItemCheckAmount {it}, {n}, PL_TMP', 'WorkCmpConst PL_TMP, 0', f'VMJumpIf CMP_EQ, {p}Few',
                    f'pl_CanFitAccessory {ac}, 1, PL_TMP', 'WorkCmpConst PL_TMP, 0', f'VMJumpIf CMP_EQ, {p}Full',
                    f'pl_msg_sys {line("ok")}', 'pl_WaitButton', f'ItemSub {it}, {n}, PL_TMP', f'pl_AddAccessory {ac}, 1',
                    f'pl_msg_sys {L(("got", k), fill(bank[SHOP_LINES["got"]], k))}', 'pl_WaitButton',
                    f'pl_CanFitAccessory {ac}, 1, PL_TMP', 'WorkCmpConst PL_TMP, 0', f'VMJumpIf CMP_NE, {p}Menu',
                    'WorkAdd PL_TMP3, 1', f'WorkCmpConst PL_TMP3, {len(rows)}', f'VMJumpIf CMP_LT, {p}Menu',
                    f'pl_msg_sys {line("all")}', 'pl_WaitButton', f'VMJump {p}AllDone', f'{p}Row{k}:']
        out += [f'VMJump {p}Menu', f'{p}Few:', f'pl_msg_sys {line("few")}', 'pl_WaitButton', f'VMJump {p}Menu',
                f'{p}Full:', f'pl_msg_sys {line("full")}', 'pl_WaitButton', f'VMJump {p}Menu',
                f'{p}AllDone:', f'pl_msg_sys {line("thanks")}', 'pl_WaitButton', f'{p}End:', 'pl_CloseMessage']
        return out
# ---- end v101-story


# ---- plat-dw-world (2026-11-07): Platinum's Distortion World (step 7, notes/PLATINUM_DW.md "The world"; pearl_story.inc block
# "plat-dw-world"). Its floors' tiles are their own (Platinum's shared world less the floor's offset, notes/PLATINUM_DW.md
# "Coordinates"): a Warp into a floor and the player's place in its scripts convert. Its people are in overlay 9, not the event
# files: gen4_extract puts them in the floors' own event files, and the engine's overlay keeps Platinum's rules for them
# (src/pearlb2/plat_dw/dw_world.c). Its commands that need the engine are PearlB2 extension sub-commands 0x20-0x24 (the row
# the Underground never took), which the overlay answers while it runs. Platinum only: Pearl's scripts use none of these.
if version.PLATINUM:
    _DW_FLOORS = None

    def dw_floors():
        """{Platinum map header: floor} of the Distortion World (b2tools/platinum_dw_data.py's tables)."""
        global _DW_FLOORS
        if _DW_FLOORS is None:
            import platinum_dw_data
            _DW_FLOORS = {f['map']: f for f in platinum_dw_data.read_tables()['floors']}
        return _DW_FLOORS

    def dw_floor_of_file(tr):
        """The Distortion World's floor whose zone script file this is, or None."""
        for z in tr.job.pd.zones:
            if z['scripts'] == tr.f and z['id'] in dw_floors():
                return dw_floors()[z['id']]
        return None

    # Platinum's distortion movement actions (105-116 the faces' walks, 117-120 the Distortion World's jumps, 121-132 the faces'
    # runs): PearlB2's action commands 0x100 + Platinum's number, which the engine's overlay runs (include/pearlb2/plat_dw.h
    # PLATDW_ACMD_FIRST; resident/plat_dw_hooks.c sends them there for any actor)
    _DW_ACTION_NAMES = {117: 'JUMP_DISTORTION_WORLD_NORTH', 118: 'JUMP_DISTORTION_WORLD_SOUTH',
                        119: 'JUMP_DISTORTION_WORLD_WEST', 120: 'JUMP_DISTORTION_WORLD_EAST'}
    for _c in list(range(105, 133)):
        MOVEMENT[_c] = {'pearl_name': f'Platinum {_DW_ACTION_NAMES.get(_c, f"MOVEMENT_ACTION_{_c}")} (the Distortion '
                                      f'World\'s, run by its overlay: 0x100 + {_c})', 'b2': 0x100 + _c, 'exact': True}

    @handler('InitPersistedMapFeaturesForDistortionWorld')
    def h_dw_init_features(tr, a, vals, name):
        """0x2F2 InitPersistedMapFeaturesForDistortionWorld (pokeplatinum: the persisted map features made the Distortion
        World's, once, on entering it). The engine's gimmick does it: Black 2 clears a zone's gimmick work when the player
        warps in (ov035 GameData_SetGimmickByZone), and the gimmick starts it as Platinum's InitPersistedData then."""
        return ['// Platinum 0x2F2 InitPersistedMapFeaturesForDistortionWorld: the engine\'s gimmick (69) inits its work on entering']

    @handler('AddDistortionWorldMapObject')
    def h_dw_add_object(tr, a, vals, name):
        """0x311 AddDistortionWorldMapObject id (DistWorld_AddMapObjectWithLocalID): the person of overlay 9's table with that
        local id. Each is in the floor's event file (gen4_extract), always spawned; the engine deletes the ones Platinum
        doesn't show at the floor's load and places the added ones as Platinum's table says (height, rotation on a face)."""
        return [f'ActorAdd {tr.var(vals[0])}  // AddDistortionWorldMapObject: the engine places it (dw_world.c)']

    @handler('DeleteDistortionWorldMapObject')
    def h_dw_delete_object(tr, a, vals, name):
        """0x312 DeleteDistortionWorldMapObject id (DistWorld_DeleteMapObjectWithLocalID): the person goes."""
        return [f'ActorDelete {tr.var(vals[0])}  // DeleteDistortionWorldMapObject']

    @handler('StartDistortionWorldGiratinaShadowEvent')
    def h_dw_shadow_start(tr, a, vals, name):
        """0x321 StartDistortionWorldGiratinaShadowEvent index (DistWorld_StartGiratinaShadowEvent): Giratina's shadow flies
        past (1F's first sight of it), drawn by the engine's overlay = extension 0x22."""
        return [f'pl_DWGiratinaShadow {tr.var(vals[0])}  // Giratina\'s shadow flies past (the engine\'s overlay)']

    @handler('FinishDistortionWorldGiratinaShadowEvent')
    def h_dw_shadow_finish(tr, a, vals, name):
        """0x322 FinishDistortionWorldGiratinaShadowEvent: waits for the shadow's flight to end, then frees it = extension 0x23."""
        return ['pl_DWGiratinaShadowFinish  // waits for the shadow\'s flight']

    @handler('ResetDistortionWorldPersistedCameraAngles')
    def h_dw_reset_camera(tr, a, vals, name):
        """0x31F ResetDistortionWorldPersistedCameraAngles (DistWorld_ResetPersistedCameraAngles): the camera trigger's saved
        angles back to the base = extension 0x24 (the Giratina room after the battle)."""
        return ['pl_DWResetCameraAngles  // the camera at its base angles']

    @handler('DoDWWarp')
    def h_dw_warp(tr, a, vals, name):
        """0x320 DoDWWarp (pokeplatinum FieldSystem_StartDWWarp: dw_warp.c, the swirl into the Distortion World over a
        screen wipe, SEQ_SE_PL_SYUWA2) = extension 0x20 (resident/plat_dw_hooks.c PearlB2_DWWarp; the script waits)."""
        return ['pl_DWWarp  // the warp effect into the Distortion World']

    # (plat-dw-rom) Platinum's swirl is an app (the field closed, then ReturnToField); here it runs on the open field (overlay
    # 377's dw_warp.c), so the ReturnToField after it would open the field a second time (overlay 35 loaded twice:
    # GFL_OvlCheckMemoryCollision's assert, as plat-tower found after the Frontier's screens): it goes
    if version.FIELD_STAYS_OPEN:
        _NO_SCREEN.add('DoDWWarp')

    @handler('GetPlayer3DPos')
    def h_dw_player_3d(tr, a, vals, name):
        """0x317 GetPlayer3DPos x, y, z (the player's tile and height): Platinum's shared world's tiles in the Distortion
        World, which its scripts compare (B2F's Cynthia: the height 231 or 232) = extension 0x21: the engine adds the floor's
        offset to the player's own tiles."""
        return [f'pl_DWGetPlayer3DPos {tr.var(vals[0])}, {tr.var(vals[1])}, {tr.var(vals[2])}  // Platinum\'s world tiles']

    _h_player_map_pos_base = HANDLERS['GetPlayerMapPos']

    @handler('GetPlayerMapPos')
    def h_dw_player_map_pos(tr, a, vals, name):
        """0x69 GetPlayerMapPos in a Distortion World floor's script: the tile in Platinum's shared world, which its scripts
        compare (B7F: x 86, z 74), so the floor's offset is added to Black 2's tile."""
        out = _h_player_map_pos_base(tr, a, vals, name)
        f = dw_floor_of_file(tr)
        if f is None or tr.mode != 'zone':
            return out
        ox, _, oz = f['offset']
        return out + ([f'pl_AddVar {tr.var(vals[0])}, {ox}  // + the floor\'s offset: Platinum\'s world tile'] if ox else []) + \
            ([f'pl_AddVar {tr.var(vals[1])}, {oz}'] if oz else [])

    @handler('StartGiratinaOriginBattle')
    def h_dw_giratina_battle(tr, a, vals, name):
        """0x319 StartGiratinaOriginBattle species, level (pokeplatinum ScrCmd_StartGiratinaOriginBattle: a wild battle with
        Giratina in its Origin Forme, the Distortion World's) = Black 2's CallWildBattleEx species, level, form 1 (Origin), 0:
        the static wild battle with the forme given (ov036 scrcmd_encount.c, EventWildBattleCall_CreateStatic)."""
        tr.last_battle = 'wild'
        return [f'CallWildBattleEx {tr.var(vals[0])}, {tr.var(vals[1])}, 1, 0  // Giratina in its Origin Forme']

    @handler('GetBattleResult')
    def h_dw_battle_result(tr, a, vals, name):
        """0x314 GetBattleResult var (pokeplatinum: the last battle's result, BATTLE_RESULT_*) from Black 2's wild battle answers
        (pl_GetBattleResult: lost 2, caught 4, knocked out 1, fled 5). The Giratina room after its battle."""
        return [f'pl_GetBattleResult {tr.var(vals[0])}  // Platinum\'s BATTLE_RESULT_ from Black 2\'s wild battle']

    _h_warp_base = HANDLERS['Warp']

    @handler('Warp')
    def h_dw_warp_into(tr, a, vals, name):
        """A Warp into a Distortion World floor: the tile in the floor's own tiles (Platinum's less the floor's offset): Spear
        Pillar Distorted's way in (55, 40) is 1F's (34, 30), B7F's (89, 57) is (15, 25), Turnback Cave's into its room."""
        m, w, x, z, d = vals
        f = dw_floors().get(m)
        if f is not None and x < 0x4000 and z < 0x4000:
            vals = [m, w, x - f['offset'][0], z - f['offset'][2], d]
        return _h_warp_base(tr, a, vals, name)

    # The Giratina room after the battle (Platinum's DistortionWorldGiratinaRoom_PostBattle): the free camera starts on the player's
    # tile (GetPlayerMapPos), goes 5 south to Cyrus and back. The player stands south of Giratina at (15, 14), the tile its arrival
    # stops them on (overlay 9's event at (15, 1, 14)); the camera starts where the field's is (CAMERA_NEAR_PLAYER's way).
    DW_CAMERA_NEAR_PLAYER = {582: (15, 14)}
    _h_cam_add_base = HANDLERS['AddFreeCamera']

    @handler('AddFreeCamera')
    def h_dw_cam_add(tr, a, vals, name):
        x, z = vals
        f = dw_floor_of_file(tr)
        if f is not None and (x >= 0x4000 or z >= 0x4000) and f['map'] in DW_CAMERA_NEAR_PLAYER:
            tr.cam = DW_CAMERA_NEAR_PLAYER[f['map']]
            return [f'EvCameraInit  // AddFreeCamera {tr.var(x)}, {tr.var(z)} (the player\'s tile): Black 2\'s event camera '
                    f'where the camera is, counted as {tr.cam}', 'EvCameraUnbind']
        return _h_cam_add_base(tr, a, vals, name)

    # The free camera's walks there keep the Distortion World's own camera (the engine's: Platinum's base pitch, 59.1 degrees,
    # and distance 0x29AEC1 at yaw 0; DwCamera_BlackTwoPitchYaw), which the engine's gimmick also writes every frame: Black 2's
    # camera 0 angle (CAM_ANGLE) would tilt the view for the scene.
    DW_CAM_ANGLE = f'{10750}, 0, {0x29AEC1:#x}'
    _h_apply_movement_base = HANDLERS['ApplyMovement']

    @handler('ApplyMovement')
    def h_dw_apply_movement(tr, a, vals, name):
        out = _h_apply_movement_base(tr, a, vals, name)
        if vals and vals[0] == 0xF1 and dw_floor_of_file(tr) is not None:
            out = [l.replace(f'EvCameraMoveTo {CAM_ANGLE},', f'EvCameraMoveTo {DW_CAM_ANGLE},') for l in out]
        return out
# ---- end plat-dw-world

# ---- plat-frontier (2026-11-07): the Battle Frontier's scenes in field rooms (notes/PLATINUM_FRONTIER.md; b2tools/frontier_script.py
# reads Platinum's frontier scripts, b2tools/frontier_translate.py makes each into a Platinum field-script file). Those files are
# PearlData slots from frontier_translate.FILE_BASE; a scene runs in its host room's zone file from its entry point (frontier_entries,
# called by translate()). Platinum's LaunchBattleFrontierScene starts one (a warp to the host with RTReserveScript, as Gen 4's Warp
# is translated); the synthesized files' markers on the same opcode change scenes and end the Frontier: ExitFrontier goes on with
# the field script that started the chain, after its ReturnToField (FrontierReturn_k blocks in the host). Pearl's and Diamond's
# scripts have no LaunchBattleFrontierScene: nothing here touches their output.
if version.PLATINUM:
    import frontier_translate as _ft

    _pd_init_frontier_base = PearlData.__init__

    def _pd_init_frontier(self):
        _pd_init_frontier_base(self)
        self.files = list(self.files)
        for k, s in _ft.scenes().items():
            if _ft.host(k):
                n = _ft.slot(s['script'])
                if len(self.files) <= n:
                    self.files += [b''] * (n + 1 - len(self.files))
                self.files[n] = _ft.synthesize(s['script'])[0]
        self._frontier = None

    PearlData.__init__ = _pd_init_frontier

    import pearl_ids as _pearl_ids_frontier
    _frontier_local_base = _pearl_ids_frontier.Ids.local

    def _frontier_local(self, v):
        if _ft.VAR_EXTRA <= v <= _ft.VAR_EXTRA + 6:          # a frontier script's vars 0x800D-0x8013 (frontier_translate.fvar)
            return f'FR_VAR_{0x800D + v - _ft.VAR_EXTRA:04X}'
        return _frontier_local_base(self, v)

    _pearl_ids_frontier.Ids.local = _frontier_local

    # A ChangeSceneWithinScript inside a subroutine (plat-frontier-flow, 2026-11-08: the Factory's and the Castle's
    # after-battle subroutines stranded the player in the corridor). Platinum's script keeps its call frames over the scene
    # change, so the subroutine's Return goes back to its caller, in the new scene. Ours ends the script at the change
    # (RTReserveScript, a warp, pl_End) and the destination room goes on from the change with no call frame. So the
    # translation keeps the frames itself, as call stacks (ctx: the return addresses, innermost first):
    # - a subroutine with a within change in its code or in a subroutine it calls (_fr_wsubs) gets a copy per call stack
    #   (FrTr units ('call', ...)), so each copy's within change reserves its own continuation, ('within', file, address,
    #   ctx);
    # - that continuation's frame is "virtual" (no VM frame after the warp): its Return jumps to the caller's code from the
    #   return address (a unit ('ret', ...) in the destination room, its frames the rest of ctx), and each Call in it goes to
    #   a translation of its own (a unit ('sub', ...), or ('call', ...) for a subroutine with a within change), so a Return
    #   in a callee stays the callee's.
    # _fr_contexts walks those units from the file's entries, as FrTr makes them, for the keys of _frontier_graph.
    def _fr_is_call(pd, op):
        return pd.table[op]['flow'] in ('call', 'ccall')

    def _fr_is_within(pd, op, args):
        return pd.cmd_name(op) == 'LaunchBattleFrontierScene' and _ft.MARK_WITHIN <= args[0][1] < _ft.MARK_EXIT

    def _fr_frame(pd, d, start):
        """The addresses of one frame's code from start: FileTr.succ's flow with each Call stepped over (not into)."""
        seen, todo = set(), [start]
        while todo:
            a = todo.pop()
            if a in seen or a not in d.insns:
                continue
            seen.add(a)
            end, op, args = d.insns[a]
            if not _fr_is_call(pd, op):
                todo += [t for ty, t in args if ty == 'rel']
            if pd.table[op]['flow'] not in ('end', 'jump', 'return') and op != 0xBE:
                todo.append(end)
        return seen

    def _fr_target(d, a):
        return next(t for ty, t in d.insns[a][2] if ty == 'rel')

    def _fr_wsubs(pd, f):
        """The subroutines of frontier file f whose code, or a subroutine's it calls, has a ChangeSceneWithinScript."""
        cache = pd.__dict__.setdefault('_fr_wsubs_cache', {})
        if f not in cache:
            d = pd.disasm(f)
            subs = {_fr_target(d, a) for a, (e, op, args) in d.insns.items() if _fr_is_call(pd, op)}
            body = {t: _fr_frame(pd, d, t) for t in subs}
            w = set()
            while True:
                more = {t for t in subs - w if any(_fr_is_within(pd, d.insns[a][1], d.insns[a][2]) or
                                                   (_fr_is_call(pd, d.insns[a][1]) and _fr_target(d, a) in w) for a in body[t])}
                if not more:
                    break
                w |= more
            cache[f] = w
        return cache[f]

    def _fr_contexts(pd, f):
        """{within-change address: sorted call stacks it runs with} of frontier file f: FrTr's units (start, ctx, virtual)
        walked from the file's entries."""
        cache = pd.__dict__.setdefault('_fr_contexts_cache', {})
        if f in cache:
            return cache[f]
        d, w = pd.disasm(f), _fr_wsubs(pd, f)
        out, seen, todo = collections.defaultdict(set), set(), [(e, (), False) for e in d.entries]
        while todo:
            u = todo.pop()
            if u in seen:
                continue
            seen.add(u)
            start, ctx, virtual = u
            assert len(ctx) <= 8, f'frontier file {f}: call stacks past 8 frames at {start:04X} (a recursion?)'
            for a in _fr_frame(pd, d, start):
                end, op, args = d.insns[a]
                if _fr_is_call(pd, op):
                    if _fr_target(d, a) in w:
                        todo.append((_fr_target(d, a), (end,) + ctx, False))
                elif _fr_is_within(pd, op, args):
                    out[a].add(ctx)
                    todo.append((end, ctx, bool(ctx)))
                elif pd.table[op]['flow'] == 'return' and virtual:
                    todo.append((ctx[0], ctx[1:], bool(ctx[1:])))
        cache[f] = {a: sorted(c) for a, c in out.items()}
        return cache[f]

    def _fr_within_key(f, end, ctx):
        return ('within', f, end) + ((ctx,) if ctx else ())

    def _fr_ctx_tag(ctx):
        return ''.join(f'_{r:04X}' for r in ctx)

    class _FrUnits:
        """A zone's extra frontier translations (FrTr), {key: label} in the order asked: ('call', file, subroutine, ctx) a
        subroutine's copy for one call stack, ('sub', file, subroutine, ()) a subroutine a virtual frame calls, ('ret',
        file, return address, ctx) the caller's code after a virtual frame's Return."""

        def __init__(self):
            self.labels, self.banks = {}, {}

        def need(self, key, bank):
            if key not in self.labels:
                kind, f, at, ctx = key
                self.labels[key] = f'Fr{kind.capitalize()}_{f}_{at:04X}{_fr_ctx_tag(ctx)}'
                self.banks[key] = bank
            return self.labels[key]

    class FrTr(FileTr):
        """One frame's translation of a frontier file: ctx, the return addresses of the frames under it; virtual, its Return
        has no VM frame (a subroutine's code after its ChangeSceneWithinScript: the Return goes on with the caller's code,
        ctx[0]); units, the zone's _FrUnits for its split Calls and its Returns. A subroutine with a within change (and, in a
        virtual frame, every subroutine) is a unit of its own; the rest are translated in the frame, as FileTr does."""

        def __init__(self, job, f, bank, starts, prefix, ctx=(), virtual=False, units=None):
            self.fr_ctx, self.fr_virtual, self.fr_units = ctx, virtual, units
            self.fr_w = _fr_wsubs(job.pd, f)
            super().__init__(job, f, bank, mode='warp', starts=starts, prefix=prefix)

        def _split(self, t):
            return self.fr_virtual or t in self.fr_w

        def succ(self, a):
            end, op, args = self.d.insns[a]
            if _fr_is_call(self.job.pd, op) and self._split(_fr_target(self.d, a)):
                return [end]
            return super().succ(a)

        def call_label(self, a, t):
            if not self._split(t):
                return super().call_label(a, t)
            if t in self.fr_w:
                return self.fr_units.need(('call', self.f, t, (self.d.insns[a][0],) + self.fr_ctx), self.bank)
            return self.fr_units.need(('sub', self.f, t, ()), self.bank)

    _h_return_frontier_base = HANDLERS['Return']

    @handler('Return')
    def h_return_frontier(tr, a, vals, name):
        """A virtual frame's Return (FrTr): Platinum's caller goes on, after the scene change, in this room."""
        if getattr(tr, 'fr_virtual', False):
            ret, rest = tr.fr_ctx[0], tr.fr_ctx[1:]
            return [f'VMJump {tr.fr_units.need(("ret", tr.f, ret, rest), tr.bank)}  // Return: the caller goes on from '
                    f'{ret:04X} (its call frame is Platinum\'s, kept over ChangeSceneWithinScript)']
        return _h_return_frontier_base(tr, a, vals, name)

    def _frontier_graph(pd):
        """The Frontier's chains, once per run: {'sites': [(k, file, launch addr, scene, return addr, live)],
        'next': {scene: {scenes it changes to}}, 'exits': {scene: has an ExitFrontier}, 'starts': {Pearl map: [keys]}}.
        Keys: ('scene', scene, entry) a scene started at an entry; ('within', slot, addr) the script going on after
        ChangeSceneWithinScript, ('within', slot, addr, ctx) after one in a subroutine, for its call stack (_fr_contexts)."""
        if pd._frontier is not None:
            return pd._frontier
        sc = _ft.scenes()
        nxt, exits, starts = collections.defaultdict(set), collections.defaultdict(bool), collections.defaultdict(list)

        def start(key, scene):
            h = _ft.host(scene)
            if h is not None and key not in starts[h['zone']]:
                starts[h['zone']].append(key)
        for k, s in sorted(sc.items()):
            if not _ft.host(k):
                continue
            d = pd.disasm(_ft.slot(s['script']))
            for a in sorted(d.insns):
                end, op, args = d.insns[a]
                if pd.cmd_name(op) != 'LaunchBattleFrontierScene':
                    continue
                v = args[0][1]
                same = [k2 for k2, s2 in sc.items() if s2['script'] == s['script']]
                if v == _ft.MARK_EXIT:
                    for k2 in same:
                        exits[k2] = True
                elif v >= _ft.MARK_WITHIN:
                    for k2 in same:
                        nxt[k2].add(v - _ft.MARK_WITHIN)
                    f = _ft.slot(s['script'])
                    for ctx in _fr_contexts(pd, f).get(a, [()]):     # (a change no entry reaches: its old key)
                        start(_fr_within_key(f, end, ctx), v - _ft.MARK_WITHIN)
                elif v >= _ft.MARK_CHANGE:
                    t = v - (_ft.MARK_CHANGE1 if v >= _ft.MARK_CHANGE1 else _ft.MARK_CHANGE)
                    for k2 in same:
                        nxt[k2].add(t)
                    start(('scene', t, 1 if v >= _ft.MARK_CHANGE1 else 0), t)
        sites = []
        for z in sorted(pd.zones, key=lambda z: z['id']):
            f = z['scripts']
            if f not in pd.files_using('LaunchBattleFrontierScene') or pd.shared_file_zones().get(z['id']) is not None:
                continue
            d = pd.disasm(f)
            nth = 0
            for a in sorted(d.insns):
                end, op, args = d.insns[a]
                if pd.cmd_name(op) != 'LaunchBattleFrontierScene':
                    continue
                nth += 1
                scene, ret, p = args[0][1], end, end
                for _ in range(4):                    # (the field script goes on after ReturnToField)
                    if p not in d.insns:
                        break
                    pe, pop, _a = d.insns[p]
                    if pd.cmd_name(pop) == 'ReturnToField':
                        ret = pe
                        break
                    p = pe
                live = (z['name'], nth) not in _ft.CLOSED_SITES
                sites.append((len(sites), f, a, scene, ret, live, z['name']))
                start(('scene', scene, 0), scene)
        pd._frontier = {'sites': sites, 'next': nxt, 'exits': exits, 'starts': starts}
        for s in sites:                 # (an ExitFrontier in a picture room: the field script goes on in its lobby)
            if any(s in _frontier_returns(pd, r) for r in _fr_picture_rooms()):
                starts[s[6]].append(('return', s[0]))
        return pd._frontier

    # ExitFrontier in a picture room (plat-frontier-flow, 2026-11-08; found by plat-test in the Hall: retire, a loss and the
    # 7-win end left the player in the room). Platinum's picture scenes run over the lobby's field, so the lobby's script
    # after ReturnToField (FrontierReturn_k: a fade-in) goes on in the lobby, where Platinum's walk back (WalkBackInvisibly*,
    # before LaunchBattleFrontierScene) left the player: in front of the attendant, facing it. Here the room is another
    # zone, so FrontierExit fades out and warps to that tile, and FrontierReturn_k is an entry of the lobby's file
    # (('return', k) keys), reserved before the warp; the lobby's own frame scripts (the challenge's end) run after it. The
    # Tower's rooms keep FrontierReturn_k in the room: its code has Platinum's own Warp to the lobby.
    def _fr_picture_rooms():
        return sorted({h['zone'] for h in _ft.HOSTS.values() if h.get('picture')})

    def _fr_lobby_place(pd, site):
        """(x, z, dir): the tile in front of the first person of the lobby whose script reaches the site's
        LaunchBattleFrontierScene (the Single and Double attendant; a Multi challenge's attendant stands beside), facing
        them."""
        k, f, a = site[0], site[1], site[2]
        zone = pd.by_name[site[6]]
        d = pd.disasm(f)
        for o in sorted(pd.events(zone)['object_events'], key=lambda o: o['id']):
            if not 1 <= o['script'] <= len(d.entries):
                continue
            seen, todo = set(), [d.entries[o['script'] - 1]]
            while todo and a not in seen:
                x = todo.pop()
                if x in seen or x not in d.insns:
                    continue
                seen.add(x)
                end, op, args = d.insns[x]
                todo += [t for ty, t in args if ty == 'rel']
                if pd.table[op]['flow'] not in ('end', 'jump', 'return') and op != 0xBE:
                    todo.append(end)
            if a in seen:
                dx, dz = {0: (0, -1), 1: (0, 1), 2: (-1, 0), 3: (1, 0)}[o['initial_dir']]
                return o['x'] + dx, o['z'] + dz, {0: 1, 1: 0, 2: 3, 3: 2}[o['initial_dir']]
        raise AssertionError(f'{site[6]}: no person\'s script reaches the LaunchBattleFrontierScene at {a:04X}')

    def _frontier_chain(pd, scene):
        g, out, todo = _frontier_graph(pd), set(), [scene]
        while todo:
            s = todo.pop()
            if s not in out:
                out.add(s)
                todo += list(g['next'].get(s, ()))
        return out

    def _frontier_returns(pd, zone_name):
        """The live launch sites whose chain ends (ExitFrontier) in a scene this room hosts."""
        g = _frontier_graph(pd)
        hosted = {k for k in _ft.scenes() if (_ft.host(k) or {}).get('zone') == zone_name}
        return [s for s in g['sites'] if s[5] and any(g['exits'][c] and c in hosted for c in _frontier_chain(pd, s[3]))]

    def _frontier_ids(pd, pearl_map):
        """{start key: script id} of the room's scene entries, after the zone's other extra entries."""
        zone = pd.zones[pearl_map]
        keys = _frontier_graph(pd)['starts'].get(zone['name'], [])
        if not keys:
            return {}
        skip = len(pd.closed(zone)) + (1 if pd.elevator_init(pearl_map) else 0) + len(pd.ramanas_ids(pearl_map)) + \
            (2 if pd.game_clear_ids(pearl_map) else 0) + (1 if pd.turnback_doors(pearl_map) else 0) + \
            (1 if pd.villa_init(pearl_map) else 0)
        return dict(zip(keys, pd._extra_ids(pearl_map, len(keys), skip=skip)))

    def _frontier_arrival(scene):
        """Where the warp into a scene's room puts the player (frontier_translate.HOSTS arrive: Pearl's own warps there)."""
        return _ft.host(scene)['arrive']

    def frontier_entries(job, pd, zone):
        """[(script id, label, lines)]: the scenes this room hosts, from each place they start, and the field code each
        ExitFrontier here goes on with (FrontierReturn_k)."""
        if not _ft.HOSTS or (zone['name'] not in {h['zone'] for h in _ft.HOSTS.values()} and
                             not _frontier_graph(pd)['starts'].get(zone['name'])):
            return []
        out, units = [], _FrUnits()
        for key, k in _frontier_ids(pd, zone['id']).items():
            ctx = ()
            if key[0] == 'return':          # (a lobby: its script after ReturnToField, an ExitFrontier's warp reserves it)
                out.append((k, f'FrontierReturn_{key[1]}', _fr_return_lines(job, pd, _frontier_graph(pd)['sites'][key[1]])))
                continue
            if key[0] == 'scene':
                scene, entry = key[1], key[2]
                f = _ft.slot(_ft.scenes()[scene]['script'])
                at = pd.disasm(f).entries[entry]
                label = f'FrontierScene{scene}_{entry}'
            else:
                f, at = key[1], key[2]
                ctx = key[3] if len(key) > 3 else ()
                scene = next(s for s, v in _ft.scenes().items() if _ft.slot(v['script']) == f)
                label = f'FrontierWithin_{f}_{at:04X}{_fr_ctx_tag(ctx)}'
            name = _ft.scenes()[scene]['name']
            tr = FrTr(job, f, _ft.bank_slot(scene), starts=[(label, at, None)], prefix=f'F{k}', ctx=ctx, virtual=bool(ctx),
                      units=units)
            where = 'entry ' + str(key[2]) if key[0] == 'scene' else 'after its scene change' + \
                (f' in a subroutine (its callers go on from {", ".join(f"{r:04X}" for r in ctx)})' if ctx else '')
            out.append((k, label, ['', f'// ---- {name} (Platinum\'s frontier script {_ft.scenes()[scene]["script"]}), '
                                      f'{where}: b2tools/frontier_translate.py'] + tr.lines()))
        lines, n = [], 0
        while n < len(units.labels):                    # (FrTr's units: each may ask for more)
            key, label = list(units.labels.items())[n]
            kind, f, at, ctx = key
            tr = FrTr(job, f, units.banks[key], starts=[(label, at, None)], prefix=f'FU{n}', ctx=ctx,
                      virtual=kind == 'ret' and bool(ctx), units=units)
            if kind == 'call':
                what = f'a copy of subroutine {at:04X} for the call that returns to {ctx[0]:04X}'
            elif kind == 'sub':
                what = f'subroutine {at:04X}, called after a scene change in a subroutine'
            else:
                what = f'the caller\'s code from {at:04X}, after a scene change in its subroutine'
            lines += ['', f'// ---- frontier script file {f}: {what} (plat-frontier-flow, FrTr)'] + tr.lines()
            n += 1
        if lines:
            out.append((None, None, lines))
        rets = _frontier_returns(pd, zone['name'])
        picture = zone['name'] in _fr_picture_rooms()       # (the field script goes on in the lobby: a warp there)
        go = (lambda s: f'FrontierExit_{s[0]}') if picture else (lambda s: f'FrontierReturn_{s[0]}')
        lines = ['', 'FrontierExit:                     // ExitFrontier: back to the field script that started the scenes']
        if len(rets) == 1:
            lines.append(f'    VMJump {go(rets[0])}')
        else:
            lines.append('    pl_FrontierGetReturn PL_TMP')
            for s in rets:
                lines += [f'    WorkCmpConst PL_TMP, {s[0]}', f'    VMJumpIf CMP_EQ, {go(s)}']
            lines += ['    pl_ReleaseAll', '    pl_End']
        for s in rets:
            if not picture:
                lines += _fr_return_lines(job, pd, s)
                continue
            lobby = pd.by_name[s[6]]
            x, z, d = _fr_lobby_place(pd, s)
            sid = _frontier_ids(pd, lobby['id'])[('return', s[0])]
            lines += ['', f'{go(s)}:', '    pl_fade_out_black',
                      '    pl_WaitFadeScreen',
                      f'    RTReserveScript {sid}  // FrontierReturn_{s[0]}: {s[6]}\'s script after ReturnToField (its entry {sid})',
                      f'    pl_Warp {pd.b2_zone[lobby["id"]]}, {x}, {z}, {d}  // the lobby, in front of the attendant: where '
                      f'Platinum\'s walk back left the player',
                      '    pl_End']
        if rets:
            out.append((None, None, lines))
        return out

    def _fr_return_lines(job, pd, s):
        """The field script after a launch site's ReturnToField, as FrontierReturn_k."""
        k, f, a, scene, ret, live, zname = s
        tr = FileTr(job, f, pd.bank_of(f), mode='warp', starts=[(f'FrontierReturn_{k}', ret, None)], prefix=f'FR{k}')
        return ['', f'// ---- after the Frontier: {zname}\'s script from {ret:04X} (its LaunchBattleFrontierScene at '
                    f'{a:04X}, then ReturnToField)'] + tr.lines()

    @handler('LaunchBattleFrontierScene')
    def h_frontier_scene(tr, a, vals, name):
        """A scene starts (a field script's), changes (ChangeScript, ChangeSceneWithinScript) or the Frontier ends (ExitFrontier)."""
        v, pd = vals[0], tr.job.pd
        if v == _ft.MARK_EXIT:
            return ['VMJump FrontierExit  // ExitFrontier']
        end = tr.d.insns[a][0]
        if v >= _ft.MARK_WITHIN:
            scene, key, what = v - _ft.MARK_WITHIN, _fr_within_key(tr.f, end, getattr(tr, 'fr_ctx', ())), 'ChangeSceneWithinScript'
        elif v >= _ft.MARK_CHANGE:
            scene = v - (_ft.MARK_CHANGE1 if v >= _ft.MARK_CHANGE1 else _ft.MARK_CHANGE)
            key, what = ('scene', scene, 1 if v >= _ft.MARK_CHANGE1 else 0), 'ChangeScript'
        else:
            scene, key, what = v, ('scene', v, 0), 'LaunchBattleFrontierScene'
        h = _ft.host(scene)
        sname = _ft.scenes().get(scene, {}).get('name', str(scene))
        if h is None:
            tr.job.stubs[f'{what} {sname} (its room is a later piece)'] += 1
            return [f'pl_stub {what}  // {sname}: no room yet (step 8\'s facility pieces); the field goes on']
        target = pd.by_name[h['zone']]
        sid = _frontier_ids(pd, target['id'])[key]
        x, z, d = _frontier_arrival(scene)
        out = []
        if what == 'LaunchBattleFrontierScene':
            g = _frontier_graph(pd)
            site = next(s for s in g['sites'] if s[1] == tr.f and s[2] == a)
            chain = _frontier_chain(pd, scene)
            rooms = {(_ft.host(c) or {}).get('zone') for c in chain if g['exits'][c]}
            if any(len(_frontier_returns(pd, r)) > 1 for r in rooms if r):
                out.append(f'pl_FrontierSetReturn {site[0]}  // where ExitFrontier goes on (FrontierExit)')
        return out + [f'RTReserveScript {sid}  // {what} {sname}: the scene runs in {h["zone"]} (its entry {sid})',
                      f'pl_Warp {pd.b2_zone[target["id"]]}, {x}, {z}, {d}', 'pl_End']

    _h_return_field_frontier_base = HANDLERS['ReturnToField']

    @handler('ReturnToField')
    def h_return_field_frontier(tr, a, vals, name):
        """ReturnToField right after LaunchBattleFrontierScene (compares and conditional calls between): no Black 2 screen ran,
        so it opens nothing. A scene that runs warps away first (its room's FrontierReturn_k is the field script after it);
        one whose room is a later piece leaves the field open."""
        prev = {e: x for x, (e, op, args) in tr.d.insns.items()}
        p = prev.get(a)
        while p is not None and tr.job.pd.cmd_name(tr.d.insns[p][1]) in ('CompareVarToValue', 'CompareVarToVar', 'CallIf'):
            p = prev.get(p)
        if p is not None and tr.job.pd.cmd_name(tr.d.insns[p][1]) == 'LaunchBattleFrontierScene':
            return ['// ReturnToField: the field stayed open (LaunchBattleFrontierScene: the scene warped away, or its room is '
                    'a later piece)']
        return _h_return_field_frontier_base(tr, a, vals, name)

    # (WaitForTransition, TerminateOverworldProcess, stays a stub that writes nothing: plat-ch7's ReturnToField rule counts a
    # command without a handler as no screen, and the warp to a scene's room needs nothing before it)

    @handler('PokeMartFrontier')
    def h_frontier_mart(tr, a, vals, name):
        """The Exchange Service Corner's two counters on Black 2's BP shop (pearl_story.inc pl_PokeMartFrontier)."""
        return [f'pl_PokeMartFrontier {vals[0]}  // Platinum\'s {("right", "left")[vals[0]]} counter']
# ---- end plat-frontier
# ---- plat-castle (2026-11-07): the Battle Castle's lobby (MAP_BATTLE_CASTLE, Platinum's scripts_battle_castle.s) on the Castle's
# Frontier ops (pearl_story.inc block "plat-castle"; notes/PLATINUM_FRONTIER.md "The Battle Castle"). Platinum only: Pearl's and
# Diamond's scripts have none of these commands.
if version.PLATINUM:
    @handler('CallBattleCastleLobbyFunction')
    def h_castle_lobby(tr, a, vals, name):
        fn, arg, var = vals
        if fn == 4:         # BC_LOBBY_FUNC_SELECT_POKEMON: Black 2's battle-entry party screen; GetBattleCastleSelectedSlots reads it
            return [f'pl_CastleLobbySelect {tr.var(arg)}  // Platinum CallBattleCastleLobbyFunction 4 (the party screen)']
        return [f'pl_CastleLobbyFunction {fn}, {tr.var(arg)}, {tr.var(var)}  // Platinum CallBattleCastleLobbyFunction {fn}']

    @handler('GetBattleCastleSelectedSlots')
    def h_castle_slots(tr, a, vals, name):
        return [f'pl_CastleSelectedSlots {", ".join(tr.var(v) for v in vals)}  // Platinum GetBattleCastleSelectedSlots']

    @handler('DeleteActiveBattleCastleStreak')
    def h_castle_delete(tr, a, vals, name):
        return [f'pl_CastleDeleteStreak {tr.var(vals[0])}  // Platinum DeleteActiveBattleCastleStreak']
# ---- end plat-castle
# ---- plat-frontier-rooms (2026-11-07): the Frontier's picture rooms (b2tools/frontier_rooms.py) as maps of PearlData, and the
# facilities' scene commands (notes/PLATINUM_FRONTIER.md "The picture rooms"). Platinum only: Pearl's and Diamond's PearlData and
# scripts have none of these.
# - The rooms: pseudo map ids 593-600 after Platinum's 593 maps (frontier_rooms.ROOMS: zones 719-726), each its lobby's header with
#   the empty script, level-script and event files and its scene's text bank; the frontier scenes they host make their files
#   (frontier_entries, as the Tower's rooms), their people come from frontier_rooms.people_entities (pearl_events).
# - The commands: frontier_translate carries a facility's own commands as they are, opcode CARRIER_BASE + the frontier opcode with
#   the frontier's arguments; the table grows by them here (named FR_ + the frontier name), and the handlers below turn them into
#   the facilities' Frontier ops (pearl_story.inc blocks "plat-factory", "plat-hall", "plat-castle").
if version.PLATINUM:
    import frontier_rooms as _fr

    _pd_init_rooms_base = PearlData.__init__

    def _pd_init_rooms(self):
        _pd_init_rooms_base(self)
        import frontier_script as _fs
        table = list(self.table)
        assert len(table) == _ft.CARRIER_BASE, f'{len(table)} field commands: frontier_translate.CARRIER_BASE is {_ft.CARRIER_BASE}'
        ftab = _fs.load_table()
        for op in range(max(ftab) + 1):
            row = ftab.get(op)
            table.append({'op': _ft.CARRIER_BASE + op, 'name': 'FR_' + (row['name'] if row else f'none_{op}'),
                          'handler': None, 'flow': None, 'args': [('u8' if t == 'u8' else 'var') for t, _ in (row or {}).get('args', [])],
                          'source': 'plat-frontier-rooms'})
        self.table = table
        self.zones = list(self.zones)
        for r in _fr.ROOMS:
            assert len(self.zones) == r['map'], (len(self.zones), r['map'])
            bank = _ft.bank_slot(_ft.scene_id(r['scene']))
            z = _fr.pseudo_zone(r, self.by_name[r['lobby']], bank)
            self.zones.append(z)
            self.by_name[z['name']] = z
            self.b2_zone[z['id']] = r['zone']
        self._frontier = None

    PearlData.__init__ = _pd_init_rooms

    def _fr_scratch(tr, a, what):
        return f'{tr.prefix}_{a:04X}_{what}'

    # the shared ones
    @handler('FR_BufferTypeName')
    def h_fr_type_name(tr, a, vals, name):
        """A type's name (the Factory's hint: its opponents' most common type, Black 2's numbering: the overlay counts the
        types of Black 2's own personal data)."""
        return [f'WordSetPokeTypeName {vals[0]}, {tr.var(vals[1])}  // BufferTypeName (Black 2\'s type numbers)']

    # the Battle Factory (pearl_story.inc "plat-factory"; notes/PLATINUM_FRONTIER.md "The Battle Factory")
    _FACTORY_SIMPLE = {'FR_InitBattleFactory': 'pl_FactoryInit', 'FR_BattleFactory_LoadTrainersForRound': 'pl_FactoryLoadRound',
                       'FR_CallBattleFactoryFunction': 'pl_FactoryFunction', 'FR_AddSelectedRentalsToParty': 'pl_FactoryAddSelected',
                       'FR_BattleFactory_SetupNextOpponent': 'pl_FactorySetupNextOpponent',
                       'FR_BattleFactory_ApplyTrade': 'pl_FactoryApplyTrade',
                       'FR_BattleFactory_SetupNextOpponentsParty': 'pl_FactorySetupNextParty',
                       'FR_BattleFactory_StartBattle': 'pl_FactoryBattle', 'FR_BattleFactory_CleanupBattle': 'pl_FactoryCleanupBattle',
                       'FR_BattleFactory_CheckWonBattle': 'pl_FactoryCheckWon', 'FR_FreeBattleFactory': 'pl_FactoryFree',
                       # the Hall's (pearl_story.inc "plat-hall")
                       'FR_InitBattleHall': 'pl_HallInit', 'FR_CallBattleHallFunction': 'pl_HallFunction',
                       'FR_FreeBattleHall': 'pl_HallFree', 'FR_BattleHall_StartBattle': 'pl_HallStartBattle',
                       'FR_BattleHall_CleanupBattle': 'pl_HallCleanupBattle', 'FR_BattleHall_CheckWonBattle': 'pl_HallCheckWonBattle',
                       'FR_BattleHall_UpdateWinRecord': 'pl_HallUpdateWinRecord',
                       # the Castle's (pearl_story.inc "plat-castle")
                       'FR_LoadTrainersForRound': 'pl_CastleLoadRound', 'FR_CallBattleCastleFunction': 'pl_CastleFunction',
                       'FR_FreeBattleCastle': 'pl_CastleFree', 'FR_BattleCastle_SetupFirstOpponent': 'pl_CastleSetupFirstOpponent',
                       'FR_BattleCastle_SetupNextOpponent': 'pl_CastleSetupNextOpponent',
                       'FR_BattleCastle_StartBattle': 'pl_CastleBattle', 'FR_BattleCastle_CleanupBattle': 'pl_CastleCleanupBattle',
                       'FR_BattleCastle_CheckWonBattle': 'pl_CastleCheckWonBattle',
                       'FR_GetCurrentCastlePoints': 'pl_CastleGetCP', 'FR_SpendCastlePoints': 'pl_CastleSpendCP',
                       'FR_ReceiveCastlePoints': 'pl_CastleReceiveCP'}

    @handler(*_FACTORY_SIMPLE)
    def h_fr_simple(tr, a, vals, name):
        """A facility command with an op of its own, its arguments as they are (each a value or a var)."""
        return [f'{_FACTORY_SIMPLE[name]} {", ".join(tr.var(v) for v in vals)}  // Platinum {name[3:]}'.replace(' , ', ' ')
                if vals else f'{_FACTORY_SIMPLE[name]}  // Platinum {name[3:]}']

    @handler('FR_BattleHall_SetupNextOpponent')
    def h_fr_hall_next(tr, a, vals, name):
        return ['pl_HallSetupNextOpponent  // Platinum BattleHall_SetupNextOpponent (its argument is unused)']

    @handler('FR_InitBattleCastle')
    def h_fr_castle_init(tr, a, vals, name):
        return [f'pl_CastleInit {", ".join(tr.var(v) for v in vals[:5])}  // Platinum InitBattleCastle (its last var is the '
                f'link\'s: {tr.var(vals[5])})']

    @handler('FR_OpenBattleFactoryAppInitial')
    def h_fr_factory_rent(tr, a, vals, name):
        """The rental screen: Black 2's battle-entry party screen on the six rentals, until three are picked (B leaves it:
        it opens again; Platinum's can't be left without three). Work 0x8006 holds the answer (the Factory's script doesn't
        use it)."""
        again = _fr_scratch(tr, a, 'rent')
        return [f'{again}:                       // Platinum OpenBattleFactoryAppInitial', '    pl_FactoryRentScreen',
                '    pl_FactoryRentResult 0x8006', '    pl_CompareVarToValue 0x8006, 0', f'    pl_GoToIf 1, {again}']

    @handler('FR_OpenBattleFactoryAppForTrade')
    def h_fr_factory_swap(tr, a, vals, name):
        """The swap: the player's three (one to give, B for none), then the beaten opponent's three (one to take)."""
        return ['pl_FactorySwapScreen 0  // Platinum OpenBattleFactoryAppForTrade: the player\'s three', 'pl_FactorySwapResult 0',
                'pl_FactorySwapScreen 1  // the beaten opponent\'s three', 'pl_FactorySwapResult 1']

    @handler('FR_BattleFactory_PrintTrainerIntro')
    def h_fr_factory_intro(tr, a, vals, name):
        """The opponent's line in Black 2's balloon over the room's opponent (person 98, or 99 for the second)."""
        return [f'pl_FactoryTrainerIntro {vals[0]}, {98 + vals[0]}  // Platinum BattleFactory_PrintTrainerIntro {vals[0]}']

    # (plat-test, 2026-11-08) The balloon (Black 2's EventBtlInstTrainerMsg) waits for A or B and closes itself, so the
    # WaitABPress Platinum's scene has right after the line (its message window's wait) asked for a second A: dropped, in
    # the four facilities alike. The double battles' WaitTime 30 after each line stays (the balloon's A, then 30 frames).
    _FR_INTROS = {'FR_BattleFactory_PrintTrainerIntro', 'FR_BattleHall_PrintTrainerIntro',
                  'FR_BattleCastle_PrintTrainerIntro', 'FR_BattleArcade_PrintTrainerInfo'}
    _h_wait_ab_intro_base = HANDLERS['WaitABPress']

    @handler('WaitABPress')
    def h_wait_ab_after_intro(tr, a, vals, name):
        p = _prev_insn(tr, a)
        if p is not None and tr.job.pd.cmd_name(tr.d.insns[p][1]) in _FR_INTROS:
            return ["// WaitABPress: the Trainer's balloon waited for A itself"]
        return _h_wait_ab_intro_base(tr, a, vals, name)

    @handler('FR_BattleHall_PrintTrainerIntro', 'FR_BattleCastle_PrintTrainerIntro')
    def h_fr_word_intro(tr, a, vals, name):
        """The opponent's intro line in Black 2's balloon over the room's opponent (person 98, or 99 for the second), as the
        Factory's (plat-test, 2026-11-08: through a script word it never showed, the word holds 63 characters)."""
        op = 'pl_HallTrainerIntro' if 'Hall' in name else 'pl_CastleTrainerIntro'
        return [f'{op} {vals[0]}, {98 + vals[0]}  // Platinum {name[3:]} {vals[0]}']

    @handler('FR_OpenBattleHallApp')
    def h_fr_hall_app(tr, a, vals, name):
        """The type grid: Black 2's list menu of the 17 types with their ranks and a summary row (pl_HallTypeList), the app's
        rules (pl_HallTypeCheck: a type at the full rank buzzes; Argenta next: Platinum's own "Excuse me!" and "Will you
        battle against the Hall Matron?" lines, scene bank 32 and 31), else "Will you battle the X-type, Rank N Pokemon?"
        (bank 24, the type and rank into words 0 and 1: pl_HallTypeWords) and yes/no; the cell picked (pl_HallSetCell).
        Black 2 has no field command for a Pokemon's summary: the summary row shows the line that names it and opens the grid
        again (not as Platinum, which opens the summary screen). Works 0x8006 (the cell) and PL_TMP (the answers).
        (plat-fix3, 2026-11-12) Platinum's scene fades to black before the app (FadeScreenOut, CloseMessage) and in again after
        it (FadeScreenIn, after the engine-layer toggle and the base level); the app is its own screen and fades itself in and
        out. Here the grid is a list on the field, so, as the Arcade's board: the room fades in under the list first, and out
        again after the cell is set (the scene's own fade-in follows). Without it the grid and its question showed on a black
        screen (plat-fix2's final checks)."""
        scene_bank = tr.bank
        top, check, ask, matron, summary = (_fr_scratch(tr, a, k) for k in ('grid', 'check', 'ask', 'matron', 'summary'))
        done = _fr_scratch(tr, a, 'done')
        row = tr.job.line_for(402, 146)             # Platinum's party menu "SUMMARY" (TEXT_BANK_PARTY_MENU)
        return ['pl_fade_in_black  // Platinum OpenBattleHallApp: its screen fades in (the room, under the grid\'s list)',
                'pl_WaitFadeScreen',
                f'{top}:                        // Platinum OpenBattleHallApp: the type grid as a list menu',
                '    ListMenu_AnchorTopRight 31, 1, 0, 0, 0x8006', f'    pl_HallTypeList {row}', '    ListMenuShow',
                '    pl_CompareVarToValue 0x8006, 17', f'    pl_GoToIf 1, {summary}',
                '    pl_CompareVarToValue 0x8006, 17', f'    pl_GoToIf 4, {top}   // (B: the grid again: it must pick)',
                f'{check}:', '    pl_HallTypeCheck 0x8006, PL_TMP', '    pl_CompareVarToValue PL_TMP, 2', f'    pl_GoToIf 1, {matron}',
                '    pl_CompareVarToValue PL_TMP, 0', f'    pl_GoToIf 1, {ask}', '    pl_PlaySE SEQ_SE_BEEP', f'    pl_GoTo {top}',
                f'{ask}:', '    pl_HallTypeWords 0x8006, 0, 1',
                f'    pl_msg_sys {tr.job.line_for(scene_bank, 24)}', '    pl_ShowYesNoMenu PL_TMP', '    pl_CloseMessage',
                '    pl_CompareVarToValue PL_TMP, 0', f'    pl_GoToIf 5, {top}', f'    pl_GoTo {done}',
                f'{matron}:', f'    pl_msg_sys {tr.job.line_for(scene_bank, 32)}', '    pl_WaitABPress',
                f'    pl_msg_sys {tr.job.line_for(scene_bank, 31)}', '    pl_ShowYesNoMenu PL_TMP', '    pl_CloseMessage',
                '    pl_CompareVarToValue PL_TMP, 0', f'    pl_GoToIf 5, {top}', f'    pl_GoTo {done}',
                f'{summary}:', f'    pl_GoTo {top}', f'{done}:', '    pl_HallSetCell 0x8006',
                'pl_fade_out_black  // the app fades out', 'pl_WaitFadeScreen']

    # the Castle's screens and CP windows (src/include/pearl_castle_screens.inc)
    @handler('FR_OpenBattleCastleSelfApp', 'FR_OpenBattleCastleOpponentApp')
    def h_fr_castle_screen(tr, a, vals, name):
        tr.job.castle_screens = True
        return [f'pl_Call CastleSelfScreen  // Platinum {name[3:]}' if 'Self' in name else
                f'pl_Call CastleOpponentScreen  // Platinum {name[3:]}']

    # The Castle's two screens are subroutines of the room's file (pearl_castle_screens.inc pl_CastleScreensCode), with the two
    # screens' text banks (Platinum's battle_castle_self_app and _opponent_app) and three lines of the Castle's own in the zone's
    # text, in order, after the scenes (frontier_entries' last entry)
    CASTLE_SELF_BANK, CASTLE_OPP_BANK = 633, 635        # (Pearl's slots of Platinum's banks 199 and 201)
    CASTLE_LINES = ['?????',                            # an opponent's Pokemon not identified yet (Platinum's row)
                    # the summary panel, of the self screen's labels (bank 199 lines 70-85): words 0 item, 1 nature, 2 ability,
                    # 3-7 Attack, Defense, Sp. Atk, Sp. Def, Speed
                    'Item: {STRVAR_1 8, 0}\\nNature: {STRVAR_1 7, 1}\\rAbility: {STRVAR_1 5, 2}\\r'
                    'Attack {STRVAR_1 52, 3}  Defense {STRVAR_1 52, 4}\\nSp. Atk {STRVAR_1 52, 5}  Sp. Def {STRVAR_1 52, 6}\\r'
                    'Speed {STRVAR_1 52, 7}',
                    # the moves panel: words 0-3 the moves, 4-7 their PP, 8-11 their maximum
                    '{STRVAR_1 6, 0}  {STRVAR_1 52, 4}/{STRVAR_1 52, 8}\\n{STRVAR_1 6, 1}  {STRVAR_1 52, 5}/{STRVAR_1 52, 9}\\r'
                    '{STRVAR_1 6, 2}  {STRVAR_1 52, 6}/{STRVAR_1 52, 10}\\n{STRVAR_1 6, 3}  {STRVAR_1 52, 7}/{STRVAR_1 52, 11}']

    _frontier_entries_rooms_base = frontier_entries

    def frontier_entries(job, pd, zone):
        out = _frontier_entries_rooms_base(job, pd, zone)
        if getattr(job, 'castle_screens', False):
            first = {}
            for key, bank in (('self', CASTLE_SELF_BANK), ('opp', CASTLE_OPP_BANK)):
                for j, text in enumerate(job.gen4_text.bank(bank)):
                    n = job.line_text(('castle', key, j), text)
                    first.setdefault(key, n)
                    assert n == first[key] + j, f'{zone["name"]}: the Castle bank {bank} is not in one run of lines'
            lines0 = [job.line_text(('castle', 'own', j), t) for j, t in enumerate(CASTLE_LINES)]
            assert lines0 == list(range(lines0[0], lines0[0] + len(CASTLE_LINES))), lines0
            out.append((None, None, ['', '// ---- the Castle\'s two screens (src/include/pearl_castle_screens.inc), its lines in this zone\'s '
                                         'text', f'.set CASTLE_SELF, {first["self"]}', f'.set CASTLE_OPP, {first["opp"]}',
                                         f'.set CASTLE_LINES, {lines0[0]}', '#include "pearl_castle_screens.inc"',
                                         '    pl_CastleScreensCode']))
        return out

    @handler('FR_ShowCastlePointsWindows', 'FR_ReprintCastlePointsInfo')
    def h_fr_castle_cp(tr, a, vals, name):
        return ['pl_CastleCPWord 0  // Platinum ' + name[3:] + ': the CP into word 0 (no window: the screens\' lines say them)']

    @handler('FR_ClearCastlePointsWindows')
    def h_fr_castle_cp_clear(tr, a, vals, name):
        return ['// Platinum ClearCastlePointsWindows: no window to clear']

    # The lobbies' own commands (Platinum's field scripts scripts_battle_factory.s and _hall.s), on the facilities' ops
    @handler('DeleteActiveBattleFactoryStreak')
    def h_fr_factory_delete(tr, a, vals, name):
        return [f'pl_FactoryDeleteStreak {tr.var(vals[0])}, {tr.var(vals[1])}  // Platinum DeleteActiveBattleFactoryStreak']

    HALL_SLOT1, HALL_SLOT2 = 'PL_TMP2', 'PL_TMP3'      # the lobby's picks, until GetBattleHallSelectedSlots reads them

    @handler('CallBattleHallLobbyFunction')
    def h_fr_hall_lobby(tr, a, vals, name):
        """CallBattleHallLobbyFunction fn, arg, var: 0-3 the Hall's op (eligibility, the streak, its species, its deletion);
        4, the party screen (Platinum's party app for one Pokemon, two of the same species in a Double): Black 2's party
        list (pl_ChoosePokemonMenu), once, or twice in a Double, the second asked again until it is the first's species (the
        app's rule). A cancel leaves slot 0xFF, as Platinum's."""
        fn, arg, var = vals
        if fn != 4:
            return [f'pl_HallLobbyFunction {fn}, {tr.var(arg)}, {tr.var(var)}  // Platinum CallBattleHallLobbyFunction {fn}']
        second, again, done = (_fr_scratch(tr, a, k) for k in ('second', 'again', 'done'))
        tr.job.approx['the Hall\'s party app (Black 2\'s party list, one pick at a time)'] += 1
        return [f'pl_ChoosePokemonMenu  // Platinum CallBattleHallLobbyFunction 4: the party app', f'pl_GetSelectedPartySlot {HALL_SLOT1}',
                f'WorkSetConst {HALL_SLOT2}, 255', f'WorkCmpConst {HALL_SLOT1}, 255', f'VMJumpIf CMP_EQ, {done}',
                f'WorkCmpConst {tr.var(arg)}, 1', f'VMJumpIf CMP_NE, {done}   // (a Double: a second of the same species)',
                f'{again}:', 'pl_ChoosePokemonMenu', f'pl_GetSelectedPartySlot {HALL_SLOT2}',
                f'WorkCmpConst {HALL_SLOT2}, 255', f'VMJumpIf CMP_EQ, {second}',
                f'WorkCmpWork {HALL_SLOT2}, {HALL_SLOT1}', f'VMJumpIf CMP_EQ, {again}',
                f'pl_GetPartyMonSpecies {HALL_SLOT1}, PL_TMP', f'pl_GetPartyMonSpecies {HALL_SLOT2}, {tr.var(var)}',
                f'WorkCmpWork PL_TMP, {tr.var(var)}', f'VMJumpIf CMP_NE, {again}', f'VMJump {done}',
                f'{second}:', f'WorkSetConst {HALL_SLOT1}, 255   // (the second cancelled: no challenge)', f'{done}:']

    @handler('GetBattleHallSelectedSlots')
    def h_fr_hall_slots(tr, a, vals, name):
        return [f'WorkSet {tr.var(vals[0])}, {HALL_SLOT1}  // Platinum GetBattleHallSelectedSlots', f'WorkSet {tr.var(vals[1])}, {HALL_SLOT2}']

    @handler('DeleteActiveBattleHallStreak')
    def h_fr_hall_delete(tr, a, vals, name):
        return [f'pl_HallLobbyFunction 3, {tr.var(vals[0])}, PL_TMP  // Platinum DeleteActiveBattleHallStreak']

    @handler('GetNumSpeciesWithBattleHallRecords', 'GetBattleHallTotalSinglesRecord', 'CheckIfBattleHallStreakIs50')
    def h_fr_hall_records(tr, a, vals, name):
        what = {'GetNumSpeciesWithBattleHallRecords': 0, 'GetBattleHallTotalSinglesRecord': 1, 'CheckIfBattleHallStreakIs50': 2}[name]
        return [f'pl_HallRecords {what}, {tr.var(vals[0])}  // Platinum {name}']
# ---- end plat-frontier-rooms
# ---- plat-arcade (2026-11-07): the Battle Arcade's lobby (MAP_BATTLE_ARCADE, Platinum's scripts_battle_arcade.s) and its scenes
# in its picture rooms (frontier_rooms' MAP_BATTLE_ARCADE_CORRIDOR and _BATTLE_ROOM: the facility commands frontier_translate
# carries, plat-frontier-rooms' carrier) on the Arcade's Frontier ops (pearl_story.inc block "plat-arcade"; notes/PLATINUM_FRONTIER.md
# "The Battle Arcade"). Platinum only: Pearl's and Diamond's scripts have none of these commands.
if version.PLATINUM:
    @handler('CallBattleArcadeLobbyFunction')
    def h_arcade_lobby(tr, a, vals, name):
        fn, arg, var = vals
        if fn == 4:         # BA_LOBBY_FUNC_SELECT_POKEMON: Black 2's battle-entry party screen; GetBattleArcadeSelectedSlots reads it
            return [f'pl_ArcadeLobbySelect {tr.var(arg)}  // Platinum CallBattleArcadeLobbyFunction 4 (the party screen)']
        return [f'pl_ArcadeLobbyFunction {fn}, {tr.var(arg)}, {tr.var(var)}  // Platinum CallBattleArcadeLobbyFunction {fn}']

    @handler('GetBattleArcadeSelectedSlots')
    def h_arcade_slots(tr, a, vals, name):
        return [f'pl_ArcadeSelectedSlots {", ".join(tr.var(v) for v in vals)}  // Platinum GetBattleArcadeSelectedSlots']

    @handler('DeleteActiveBattleArcadeStreak')
    def h_arcade_delete(tr, a, vals, name):
        return [f'pl_ArcadeDeleteStreak {tr.var(vals[0])}  // Platinum DeleteActiveBattleArcadeStreak']

    _ARCADE_SIMPLE = {'FR_BattleArcade_LoadTrainersForRound': 'pl_ArcadeLoadRound', 'FR_FreeBattleArcade': 'pl_ArcadeFree',
                      'FR_CallBattleArcadeFunction': 'pl_ArcadeFunction',
                      'FR_BattleArcade_SetupFirstOpponent': 'pl_ArcadeSetupFirstOpponent',
                      'FR_BattleArcade_SetupNextOpponent': 'pl_ArcadeSetupNextOpponent',
                      'FR_BattleArcade_StartBattle': 'pl_ArcadeBattle', 'FR_BattleArcade_CleanupBattle': 'pl_ArcadeCleanupBattle',
                      'FR_BattleArcade_CheckWonBattle': 'pl_ArcadeCheckWonBattle', 'FR_ApplyArcadeEffect': 'pl_ArcadeApplyEffect'}

    @handler(*_ARCADE_SIMPLE)
    def h_fr_arcade_simple(tr, a, vals, name):
        """An Arcade command with an op of its own, its arguments as they are (each a value or a var)."""
        op = _ARCADE_SIMPLE[name]
        return [f'{op} {", ".join(tr.var(v) for v in vals)}  // Platinum {name[3:]}' if vals else f'{op}  // Platinum {name[3:]}']

    @handler('FR_InitBattleArcade')
    def h_fr_arcade_init(tr, a, vals, name):
        return [f'pl_ArcadeInit {", ".join(tr.var(v) for v in vals[:5])}  // Platinum InitBattleArcade (its last var is the '
                f'link\'s: {tr.var(vals[5])})']

    @handler('FR_BattleArcade_PrintTrainerInfo')
    def h_fr_arcade_intro(tr, a, vals, name):
        """The opponent's intro line in Black 2's balloon over the room's opponent (person 98 or 99), as the Factory's."""
        return [f'pl_ArcadeTrainerIntro {vals[0]}, {98 + vals[0]}  // Platinum BattleArcade_PrintTrainerInfo {vals[0]}']

    @handler('FR_OpenBattleArcadeApp')
    def h_fr_arcade_board(tr, a, vals, name):
        """The game board: a window of its 16 panels on the field (arcade_field.c), named by 32 lines of this zone's text, in a
        run (platinum_arcade_data.BOARD_NAMES); the script goes on when it stops. Platinum's scene has faded to black before
        it, and the app fades its own screens in and out: here the room fades in under the window, and out again after."""
        import platinum_arcade_data as _pad
        lines = [tr.job.line_text(('arcade_board', i), n) for i, n in enumerate(_pad.BOARD_NAMES)]
        assert lines == list(range(lines[0], lines[0] + len(lines))), lines
        tr.job.approx['OpenBattleArcadeApp (the board as a window over the room: arcade_field.c)'] += 1
        return ['pl_fade_in_black  // Platinum OpenBattleArcadeApp: its screens fade in (the room, under the board\'s window)',
                'pl_WaitFadeScreen',
                f'pl_ArcadeBoard {lines[0]}  // the game board (its names: lines {lines[0]}-{lines[-1]})',
                'pl_fade_out_black  // the app fades out', 'pl_WaitFadeScreen']

    @handler('FR_SetItemDrawFlag')
    def h_fr_arcade_items(tr, a, vals, name):
        return ['// Platinum SetItemDrawFlag: the items beside the board are sprites (none here)']

    @handler('FR_AddToRecordValue')
    def h_fr_arcade_record(tr, a, vals, name):
        """Platinum's AddToRecordValue RECORD_UNK_067, VAR_0x8008 (the board's free BP added to a Game Record; only the Arcade's
        scene has it): nothing, as IncrementGameRecord (Black 2 keeps its own records). GiveBattlePoints after it gives the BP."""
        tr.job.approx['AddToRecordValue (Black 2 keeps its own records)'] += 1
        return [f'// Platinum AddToRecordValue {vals[0]}, {tr.var(vals[1])}: nothing in Black 2 (its own records)']

    # The board's free BP plays Platinum's SEQ_PL_DON2, then waits for it (WaitFanfare): a stub there would hang, so Black 2's item
    # jingle stands in [guess]. The effects' sounds (SEQ_SE_PL_FR03, FR04, FR05: with the particles) and the swap's SEQ_SE_DP_Z_SEARCH
    # stay counted stubs (their waits are stubs too): no Black 2 sound chosen
    SOUND.update({'SEQ_PL_DON2': 'SEQ_ME_ITEM'})
# ---- end plat-arcade
# ---- plat-tower (2026-11-08): the Frontier's party and record screens reopen the field themselves. Black 2's battle-entry party
# screen (ov012 EventBSubwayPokeSelect / EventBtlInstPokeSelect: the Tower's function 30, the Castle's and the Arcade's lobby
# function 4), its party list (CallPokeSelect: the Stats Judge's SelectMoveTutorPokemon, the Hall's lobby function 4) and the
# Subway's records screen (EventBSubwayRecords, a field subprocess: OpenBattleTowerRecordsApp) fade out, close the field, run the
# screen, open the field again (EventFieldOpen_CreateHeadless) and fade in. Platinum's ReturnToField after them was a second
# FieldOpen on the open field: it loads the field's glue overlay 35 again while it is loaded, GFL_OvlCheckMemoryCollision
# asserts, "An error has occurred" (the Tower's CONFIRM, the Stats Judge, the records machine; the Hall's, Castle's and Arcade's
# lobby party screens the same). Pearl's Tower drops them by address (data/pearl_script_patches.json, file 358), which doesn't
# align with Platinum's lobby. So, as poke_select_fades does for the other party screens: the fade-out before the screen, the
# ReturnToField after it and the fade-in after that are dropped (the waits stay: nothing to wait for). Platinum only: Pearl's
# and Diamond's output doesn't change.
if version.PLATINUM:
    # the screens' commands (the facility functions by their number: the party screens), then what may sit between
    _FR_SCREENS = {'CallBattleTowerFunction': 30, 'CallBattleHallLobbyFunction': 4, 'CallBattleCastleLobbyFunction': 4,
                   'CallBattleArcadeLobbyFunction': 4, 'SelectMoveTutorPokemon': None, 'OpenBattleTowerRecordsApp': None}
    _FR_BEFORE = {'CloseMessage', 'WaitFadeScreen'}                                  # between the fade-out and the screen
    _FR_READS = {'GetSelectedPartySlot', 'GetBattleHallSelectedSlots', 'GetBattleCastleSelectedSlots',
                 'GetBattleArcadeSelectedSlots'}                                     # the screen's answer, before ReturnToField
    _FR_AFTER = {'SetVarFromVar', 'SetVarFromValue'}                                 # between ReturnToField and the fade-in
    _psel_tower_base = poke_select_fades

    def poke_select_fades(tr):
        out = _psel_tower_base(tr)
        if not getattr(tr, '_psel_tower', False):
            tr._psel_tower = True
            d, pd = tr.d, tr.job.pd
            nxt = {x: e for x, (e, op, args) in d.insns.items()}
            prv = {e: x for x, e in nxt.items()}
            name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
            first = lambda x: d.insns[x][2][0][1] if x in d.insns and d.insns[x][2] else None
            for c in d.insns:
                n = name(c)
                if n not in _FR_SCREENS or (_FR_SCREENS[n] is not None and first(c) != _FR_SCREENS[n]):
                    continue
                f0 = prv.get(c)
                while name(f0) in _FR_BEFORE:
                    f0 = prv.get(f0)
                r = nxt.get(c)
                while name(r) in _FR_READS:
                    r = nxt.get(r)
                f1 = nxt.get(r)
                while name(f1) in _FR_AFTER or (name(f1) == 'CallBattleTowerFunction' and first(f1) == 31):   # (31: the choice)
                    f1 = nxt.get(f1)
                if (name(f0), name(r), name(f1)) == ('FadeScreen', 'ReturnToField', 'FadeScreen') and \
                        (d.insns[f0][2][2][1], d.insns[f1][2][2][1]) == (0, 1):                          # out, then in
                    out |= {f0, r, f1}
        return out
# ---- end plat-tower
# ---- plat-stubs (2026-11-08): the stubs a Platinum player still reached (work/agents/plat-stubs/STUBS.md, notes/PLATINUM_STUBS.md;
# pearl_story.inc block "plat-stubs"). Platinum only: Pearl's and Diamond's scripts don't change.
if version.PLATINUM:
    # The Frontier's four lobbies save with the common save script (Platinum's CommonScript 2007: CheckSaveType, the save details
    # window) and show the banned-species line, as the Tower's lobby: the Tower's handlers (TOWER_ONLY_HANDLERS) there too. Left
    # stubs, CheckSaveType kept the var's last answer: a 0 (Yes to the question before it) read as "a save that can't be
    # overwritten", the challenge didn't start.
    TOWER_ZONES = TOWER_ZONES + ('MAP_BATTLE_FACTORY', 'MAP_BATTLE_HALL', 'MAP_BATTLE_CASTLE', 'MAP_BATTLE_ARCADE')  # noqa: F811

    @handler('TryRevertPokemonForm')
    def h_revert_form(tr, a, vals, name):
        """0x31E TryRevertPokemonForm slot, var (pokeplatinum ov5_021F6454.c): a party Pokémon entered at a Frontier facility,
        the Tower or put in the Day Care goes back to its first form: a Rotom out of its appliance (Black 2's
        PokePartyChangeRotomForme to form 0: its appliance move goes, Thunder Shock if it has none left, as Platinum's
        Pokemon_SetRotomForm), Shaymin to its Land Forme; var 0, 255 only when a Griseous Orb finds no room in the Bag.
        Giratina's Orb isn't taken here (Black 2 has no script command for a held item; its Giratina takes its form from
        the item): Giratina can't enter the Frontier (banned), so only the Day Care keeps an Origin Giratina so."""
        tr.job.approx['TryRevertPokemonForm (Giratina keeps its Griseous Orb)'] += 1
        slot = tr.var(vals[0])
        out = []
        if vals[0] < 0x4000:
            out, slot = [f'WorkSetConst PL_TMP2, {vals[0]}'], 'PL_TMP2'
        return out + [f'pl_TryRevertPokemonForm {slot}, {tr.var(vals[1])}  // TryRevertPokemonForm: Rotom and Shaymin to '
                      f'their first form']

    @handler('ShowListMenuRememberCursor')
    def h_list_menu_cursor(tr, a, vals, name):
        """0x306 ShowListMenuRememberCursor cursor, scroll: the list menu, opening where it was left (the vars keep the place).
        Black 2's list menu opens at the top (approximation). Left a stub, the menu was never shown: the Frontier records'
        letter list (the Battle Hall's machine) read its old answer and went round for ever."""
        tr.job.approx['ShowListMenuRememberCursor (Black 2\'s list menu opens at the top)'] += 1
        return [f'ListMenuShow  // ShowListMenuRememberCursor {tr.var(vals[0])}, {tr.var(vals[1])}: opens at the top']

    @handler('ShowBattleHallRecordMonSelectionMenu')
    def h_hall_record_mons(tr, a, vals, name):
        """0x2DE ShowBattleHallRecordMonSelectionMenu type, letters, var, ...: the Battle Hall records machine's list of the
        species with a record whose names start with the letters picked, for the records screen (OpenFrontierRecordsApp),
        which Black 2 doesn't have. The answer is EXIT (MENU_CANCEL): back to the letters, whose EXIT leaves."""
        tr.job.approx['ShowBattleHallRecordMonSelectionMenu (no records screen: EXIT)'] += 1
        return [f'WorkSetConst {tr.var(vals[2])}, 65534  // ShowBattleHallRecordMonSelectionMenu: EXIT (no records screen here)']

    if version.HALL_RECORDS_MACHINE:
        @handler('ShowBattleHallRecordMonSelectionMenu')
        def h_hall_record_mons_list(tr, a, vals, name):
            """(plat-fix2) 0x2DE ShowBattleHallRecordMonSelectionMenu type, letters, var, list pos, cursor pos (pokeplatinum
            ov5_021F6454.c): the species of the letters with a record of the type, in Platinum's alphabetical lists, then EXIT
            (menu entries line 12; MENU_CANCEL, as B), in Black 2's list menu at the right edge (Platinum's at tile 20). The
            list and cursor positions aren't kept: Black 2's list menu opens at the top (as the letters' menu)."""
            tr.job.approx['ShowBattleHallRecordMonSelectionMenu (Black 2\'s list menu opens at the top)'] += 1
            return [f'ListMenu_AnchorTopRight 31, 1, 0, 1, {tr.var(vals[2])}  // ShowBattleHallRecordMonSelectionMenu',
                    f'pl_HallRecordList {tr.var(vals[0])}, {tr.var(vals[1])}  // the species with a record',
                    f'ListMenuAdd {tr.job.line_for(MENU_BANK, 12)}, 65535, 65534  // EXIT (MenuEntries_Text_ListMenu_Exit)',
                    'ListMenuShow']

    _HALL_MILESTONES = None

    def hall_milestones():
        """[(total record, BP)] of Platinum's Battle Hall record keeper (pokeplatinum scrcmd_battle_hall.c
        sBattleHallRecordMilestones: its rows and count), checked against the dump's ARM9 ({u32 record, u32 bp} rows, found
        by the first four)."""
        global _HALL_MILESTONES
        if _HALL_MILESTONES is None:
            import pearl_items
            src = open(os.path.join(PLATINUM, 'src', 'scrcmd_battle_hall.c')).read()
            at = src.index('sBattleHallRecordMilestones[] = {')
            rows = [(int(r), int(b)) for r, b in re.findall(r'\{\s*(\d+),\s*(\d+)\s*\}', src[at:src.index('};', at)])]
            arm9, _ = pearl_items.world_arm9()
            first = struct.pack('<8I', *[v for row in rows[:4] for v in row])
            at = arm9.find(first)
            assert at >= 0 and arm9.find(first, at + 1) < 0, 'the Hall milestones: not found once in the ARM9'
            assert [struct.unpack_from('<2I', arm9, at + 8 * k) for k in range(len(rows))] == rows, 'the Hall milestones'
            _HALL_MILESTONES = rows
        return _HALL_MILESTONES

    @handler('GetBattleHallRecordKeeperStats')
    def h_hall_record_keeper(tr, a, vals, name):
        """0x324 GetBattleHallRecordKeeperStats cur, passed, next, bp (words), milestone var, var (pokeplatinum
        scrcmd_battle_hall.c): the Battle Hall's record keeper. The total of every species' Single record (pl_HallRecords 1)
        into word cur; each milestone from the var's on that the total reached gives its BP (BP added, the var counts on;
        word passed the last one reached, else the first's 10), word next the next one, word bp the BP; var 0 no record
        (or nothing reached yet), 1 BP given, 2 no new milestone, 3 every milestone passed (no words). The total is a u16
        here: the milestones past 65,535 (70,000-100,000) are never reached (the word shows 65,535 for them)."""
        cur, passed, nxt, bpw = vals[:4]
        mv, res = tr.var(vals[4]), tr.var(vals[5])
        rows = hall_milestones()
        p = f'{tr.prefix}_{a:04X}_Hall'
        out = ['// GetBattleHallRecordKeeperStats: Platinum\'s record keeper (its milestones from the dump)',
               'pl_HallRecords 1, PL_TMP  // the total of the Single records', f'pl_BufferNumber {cur}, PL_TMP',
               'WorkSetConst PL_TMP2, 0  // the BP earned', f'WorkSetConst PL_TMP3, {rows[0][0]}  // the last milestone reached']
        for i, (rec, bp) in enumerate(rows):
            if rec > 0xFFFF:
                break
            out += [f'WorkCmpConst {mv}, {i}', f'VMJumpIf CMP_NE, {p}M{i}', f'WorkCmpConst PL_TMP, {rec}',
                    f'VMJumpIf CMP_LT, {p}Scanned', f'WorkAdd PL_TMP2, {bp}', f'WorkAdd {mv}, 1',
                    f'WorkSetConst PL_TMP3, {rec}  // {rec} reached: {bp} BP', f'{p}M{i}:']
        out += [f'{p}Scanned:', 'WorkCmpConst PL_TMP2, 0', f'VMJumpIf CMP_EQ, {p}NoBP', 'pl_TowerBpAdd PL_TMP2',
                f'{p}NoBP:', f'WorkSetConst {res}, 0', 'WorkCmpConst PL_TMP, 0', f'VMJumpIf CMP_EQ, {p}Words',
                f'WorkSetConst {res}, 1', 'WorkCmpConst PL_TMP2, 0', f'VMJumpIf CMP_NE, {p}Words', f'WorkSetConst {res}, 2',
                f'WorkCmpConst {mv}, {len(rows)}', f'VMJumpIf CMP_LT, {p}Words', f'WorkSetConst {res}, 3',
                f'VMJump {p}End', f'{p}Words:', f'pl_BufferNumber {passed}, PL_TMP3']
        for i, (rec, bp) in enumerate(rows):
            out += [f'WorkCmpConst {mv}, {i}', f'VMJumpIf CMP_NE, {p}N{i}', f'pl_BufferNumber {nxt}, {min(rec, 0xFFFF)}',
                    f'{p}N{i}:']
        return out + [f'pl_BufferNumber {bpw}, PL_TMP2', f'{p}End:']

    @handler('CheckHeapMemory')
    def h_check_heap(tr, a, vals, name):
        """0x313 CheckHeapMemory check (pokeplatinum scrcmd.c): a debug check that the field's heaps are as large as when the
        Frontier lobby's script began (an assert, nothing else): nothing in Black 2."""
        return [f'// CheckHeapMemory {vals[0]}: Platinum\'s debug check of its heaps (an assert): nothing here']

    @handler('331', '332')
    def h_eterna_rival_objects(tr, a, vals, name):
        """0x331 / 0x332 (pokeplatinum ov5_021F6454.c): Eterna's scene with Barry by the Galactic building (the free camera
        pans away) keeps objects 32 and 2 drawn at height 9 (MAP_OBJ_STATUS_13) and lets go after, as 0x32D / 0x32E in Amity
        Square. Black 2 keeps every person of the zone drawn, on its own tile's height: nothing to do."""
        return [f'// {name}: Platinum keeps two people drawn through the camera pan; Black 2 draws them anyway']

    _SCRATCH = None

    def scratch_card_prizes():
        """(Nugget item, [the Berries a card can show]) of the Battle Frontier's scratch-off cards (pokeplatinum
        applications/scratch_off_cards/main.c sAvailableItems, by generated/items.txt), checked against the dump's overlay 111."""
        global _SCRATCH
        if _SCRATCH is None:
            import contest_data
            src = open(os.path.join(PLATINUM, 'src', 'applications', 'scratch_off_cards', 'main.c')).read()
            at = src.index('sAvailableItems[] = {')
            ids = {n: i for i, n in enumerate(open(os.path.join(PLATINUM, 'generated', 'items.txt')).read().split())}
            berries = [ids[n] for n in re.findall(r'ITEM_\w+', src[at:src.index('};', at)])]
            _, o = contest_data.overlay(Rom(version.WORLD_DUMP), 111)
            assert o.find(struct.pack(f'<{len(berries)}H', *berries)) >= 0, 'the scratch-off cards\' Berries: not in overlay 111'
            _SCRATCH = ids['ITEM_NUGGET'], berries
        return _SCRATCH

    if version.FIELD_STAYS_OPEN:                # (plat-test, 2026-11-08) no screen runs, so the field never closed: the
        _NO_SCREEN |= {'OpenScratchOffCardsApp', 'FreeScratchOffCardsArgs'}   # ReturnToField after them opens nothing
        # (h_return_field_open; its FieldOpen on the open field stopped the game: "An error has occurred")

    @handler('OpenScratchOffCardsApp', 'FreeScratchOffCardsArgs')
    def h_scratch_app(tr, a, vals, name):
        """0x2E2 OpenScratchOffCardsApp / 0x2E3 FreeScratchOffCardsArgs: the Battle Frontier's scratch-off cards (1 BP for three).
        Black 2 has no such touch screen: the cards are scratched for the player (GetScratchOffCardsWonItem below)."""
        if name == 'OpenScratchOffCardsApp':
            tr.job.approx['OpenScratchOffCardsApp (no touch screen: the cards come out at Platinum\'s odds)'] += 1
        return [f'// {name}: no scratch-off screen here; each card\'s prize is drawn at Platinum\'s odds']

    @handler('GetScratchOffCardsWonItem')
    def h_scratch_prize(tr, a, vals, name):
        """0x2E4 GetScratchOffCardsWonItem card, item, count: what a card won (0, 0: nothing). Platinum's card (its app's
        PlaceValuesInScratchCells, CheckIfThreeOfAKindFound): nine cells, two Dittos (wild) and three, two and two of three
        of the card's four prizes (one a Nugget, the others Berries of the 23); three cells scratched win when they show one
        prize (Dittos count as any). The cells lie in random places, so which three the player picks doesn't matter: 18 of
        the 84 picks win, a quarter of them the Nugget (one), the rest a Berry (three of it). = Black 2's Random: 18 in 336
        the Nugget, 54 in 336 a Berry of the 23, else nothing."""
        nugget, berries = scratch_card_prizes()
        it, n = tr.var(vals[1]), tr.var(vals[2])
        p = f'{tr.prefix}_{a:04X}_Card'
        out = [f'// GetScratchOffCardsWonItem {vals[0]}: card {vals[0] + 1} at Platinum\'s odds', f'WorkSetConst {it}, 0',
               f'WorkSetConst {n}, 0', 'Random PL_TMP, 336', 'WorkCmpConst PL_TMP, 18', f'VMJumpIf CMP_GE, {p}Berry',
               f'WorkSetConst {it}, {nugget}  // a Nugget', f'WorkSetConst {n}, 1', f'VMJump {p}End', f'{p}Berry:',
               'WorkCmpConst PL_TMP, 72', f'VMJumpIf CMP_GE, {p}End', f'WorkSetConst {n}, 3', f'Random PL_TMP, {len(berries)}']
        for k, b in enumerate(berries):
            out += [f'WorkCmpConst PL_TMP, {k}', f'VMJumpIf CMP_NE, {p}B{k}', f'WorkSetConst {it}, {b}', f'VMJump {p}End',
                    f'{p}B{k}:']
        return out + [f'{p}End:']

    _JUDGE_LINES = None

    def judge_lines():
        """[the line naming each stat as best] of the Battle Tower's Stats Judge, by IV (HP, Attack, Defense, Speed, Sp. Atk,
        Sp. Def): pokeplatinum ov5_021F6454.c sHighestIVMessageIndices, found in the dump's overlay 5 (lines of the lobby's
        own bank, which keep their numbers in its text file)."""
        global _JUDGE_LINES
        if _JUDGE_LINES is None:
            import contest_data
            _, o = contest_data.overlay(Rom(version.WORLD_DUMP), 5)
            want = (122, 123, 124, 127, 125, 126)
            at = o.find(struct.pack('<6H', *want))
            assert at >= 0 and o.find(struct.pack('<6H', *want), at + 1) < 0, 'the Stats Judge\'s lines: not once in overlay 5'
            _JUDGE_LINES = list(want)
        return _JUDGE_LINES

    @handler('JudgeStats')
    def h_judge_stats(tr, a, vals, name):
        """0x2EE JudgeStats slot, total, line, best (pokeplatinum ov5_021F6454.c): the Battle Tower lobby's Stats Judge. total =
        the six IVs added, best = the highest IV, line = the line naming the stat with it (the first highest; an equal one
        later takes its place on a coin toss, as Platinum's LCRNG % 2). Black 2's PokePartyGetIV (ov036: 0 the total, 1 the
        highest, 2-7 HP, Attack, Defense, Speed, Sp. Atk, Sp. Def: Platinum's order) and Random."""
        slot, total, line, best = (tr.var(v) for v in vals)
        lines = judge_lines()
        p = f'{tr.prefix}_{a:04X}_Judge'
        out = ['// JudgeStats: Platinum\'s Stats Judge on Black 2\'s PokePartyGetIV',
               f'PokePartyGetIV {slot}, 0, {total}  // the six IVs added',
               f'PokePartyGetIV {slot}, 2, PL_TMP2  // HP: the best so far', f'WorkSetConst {line}, {lines[0]}']
        for i in range(1, 6):
            out += [f'PokePartyGetIV {slot}, {2 + i}, PL_TMP', 'WorkCmpWork PL_TMP2, PL_TMP', f'VMJumpIf CMP_GT, {p}N{i}',
                    f'VMJumpIf CMP_LT, {p}T{i}', 'Random PL_TMP3, 2  // as high: a coin toss', 'WorkCmpConst PL_TMP3, 0',
                    f'VMJumpIf CMP_NE, {p}N{i}', f'{p}T{i}:', 'WorkSet PL_TMP2, PL_TMP', f'WorkSetConst {line}, {lines[i]}',
                    f'{p}N{i}:']
        return out + [f'WorkSet {best}, PL_TMP2  // the highest IV']

    @handler('SaveExtraData')
    def h_save_extra(tr, a, vals, name):
        """0x2D6 SaveExtraData (pokeplatinum SaveDataExtra_Init: the extra save blocks set up before their first save):
        Black 2's save writes its own blocks."""
        return ['// SaveExtraData: Black 2\'s save writes its own extra blocks']

    @handler('CheckIsMiscSaveInit')
    def h_misc_save_init(tr, a, vals, name):
        """0x2D7 CheckIsMiscSaveInit var: 1 once the save's extra data was set up (the common save asks it after a save
        that couldn't be overwritten). Black 2's save always has its blocks: 1."""
        return [f'WorkSetConst {tr.var(vals[0])}, 1  // CheckIsMiscSaveInit: Black 2\'s save has its blocks']

    @handler('258', '259')
    def h_save_player_task(tr, a, vals, name):
        """0x258 / 0x259 (pokeplatinum scrcmd.c, around the common save): a task on the player's sprite started and ended
        while the game saves. Black 2's save has its own: nothing to do."""
        return [f'// {name}: Platinum\'s player task while saving; Black 2\'s save has its own']

    @handler('GetOverworldWeather')
    def h_overworld_weather(tr, a, vals, name):
        """0x315 GetOverworldWeather var (Route 213's Looker scene: rain plays SEQ_SE_DP_T_AME, a sound Black 2 has none for,
        a counted stub): no rain asked (0); nothing else reads it."""
        tr.job.approx['GetOverworldWeather (0: the rain\'s sound has no Black 2 sound)'] += 1
        return [f'WorkSetConst {tr.var(vals[0])}, 0  // GetOverworldWeather: not asked (the rain sound has no Black 2 sound)']

    @handler('Dummy316')
    def h_dummy316(tr, a, vals, name):
        return ['// Dummy316: Platinum\'s command does nothing']

    @handler('WaitForTransition')
    def h_wait_transition(tr, a, vals, name):
        """0x1F8 TerminateOverworldProcess / WaitForTransition (pokeplatinum): before a Frontier scene starts, the field's
        process ends. The scene here is a warp (RTReserveScript and Warp just after it), which ends the field itself."""
        return ['// WaitForTransition: the warp after it ends the field (the scene is a room here)']
# ---- end plat-stubs
# ---- plat-records (2026-11-08): the Frontier's records machines (Platinum's global 10450-10455, scripts_battle_frontier_records.s:
# the Tower lobby's (13, 5), the Factory's (22, 6), the Hall's (7, 8), the Castle's (6, 8), the Arcade's (16, 5)). After the menu
# (SINGLE, DOUBLE, MULTI) Platinum's OpenFrontierRecordsApp challengeType, facility, species (pokeplatinum applications/frontier/
# records/main.c DisplayRecords) shows the facility's own records for that type: each row PREV or CURRENT (CURRENT while the
# facility's streak flag for the type is set) with the latest streak, and RECORD with the record. Black 2 has no such screen, so
# the same rows show as messages, in the app's own words (its bank, FRONTIER_RECORDS_BANK), with the numbers the Frontier core
# keeps (plat_frontier.c: Platinum's BattleFrontierStats by its ids, pl_FrontierStatGet; the facilities' streak flags,
# pl_FrontierStreakFlag, bits as Platinum's), which the Factory, Castle and Arcade write as Platinum does (factory_rules.c,
# castle_rules.c, arcade_rules.c); the Tower's are Black 2's Subway records (pl_TowerResultsRoom). The screen's fades and its
# ReturnToField are dropped (the message is on the field). Platinum only (Pearl has no Frontier).
if version.PLATINUM:
    FRONTIER_RECORDS_BANK = 627     # pokeplatinum res/text/battle_frontier_records.json (TEXT_BANK_BATTLE_FRONTIER_RECORDS)
    FRONTIER_FACILITIES = {1: 'Tower', 2: 'Factory', 3: 'Factory', 4: 'Castle', 5: 'Hall', 6: 'Arcade'}   # FACILITY_* (Open: the same)

    def _frontier_records_lines(job, kind):
        """The first of the facility's lines pl_FrontierRecords shows (pearl_story.inc), added to the zone's text in its order,
        each in a PREV and a CURRENT copy. Tower (kind 1): Single, Double, Multi w/Trainer, Multi w/friend. Factory (2): Level 50
        for Single, Double, Multi, then Open Level. Castle (4), Arcade (6): Single, Double, Multi. Built from the app's lines by
        number (bank FRONTIER_RECORDS_BANK): 21-25 the facilities, 26-28 the types' records, 29 PREV, 30 CURRENT, 31 RECORD,
        32-33 the Multi's two rooms, 34-36 the Factory's levels and its Rental/Trade column, 38 and 42 "Win streak: N", 40 a
        number, 41 "N CP", 43 "Games cleared: N" (buffers: 0 the latest, 1 the record, or 0-3 latest, its count, record, its
        count)."""
        w = job.gen4_text.bank(FRONTIER_RECORDS_BANK)
        want = {21: 'Battle Tower', 22: 'Battle Factory', 23: 'Battle Castle', 25: 'Battle Arcade', 26: 'Single Record',
                27: 'Double Record', 28: 'Multi Record', 29: 'PREV', 30: 'CURRENT', 31: 'RECORD', 32: 'Multi w/Trainer',
                33: 'Multi w/friend', 34: 'Level 50', 35: 'Open Level', 36: 'Rental/Trade', 38: 'Win streak: {STRVAR_1 53, 0}',
                40: '{STRVAR_1 53, 0}', 41: '{STRVAR_1 53, 0} CP', 42: 'Win streak: {STRVAR_1 53, 0}',
                43: 'Games cleared: {STRVAR_1 53, 0}'}
        assert all(w[k] == v for k, v in want.items()), [(k, w[k]) for k, v in want.items() if w[k] != v]
        num = lambda n, i: w[n].replace('{STRVAR_1 53, 0}', f'{{STRVAR_1 53, {i}}}')
        types, now = (26, 27, 28), (29, 30)
        if kind == 1:
            rows = lambda pv: f'{w[pv]} {num(38, 0)}\\f{w[31]} {num(38, 1)}'
            lines = [f'{w[21]}\\n{w[types[t]]}\\f{rows(pv)}' for t in (0, 1) for pv in now]
            lines += [f'{w[21]}\\n{w[28]}\\f{w[32]}\\f{rows(pv)}\\r' for pv in now]
            lines += [f'{w[33]}\\n{rows(pv)}' for pv in now]
        elif kind == 2:
            rows = lambda pv: f'{w[pv]} {num(38, 0)}\\f{w[36]} {num(40, 1)}\\r{w[31]} {num(38, 2)}\\n{w[36]} {num(40, 3)}'
            lines = [f'{w[22]}\\n{w[types[t]]}\\r{w[34]}\\n{rows(pv)}\\r' for t in range(3) for pv in now]
            lines += [f'{w[35]}\\n{rows(pv)}' for pv in now]
        elif kind == 4:
            lines = [f'{w[23]}\\n{w[types[t]]}\\r{w[pv]} {num(42, 0)}\\n{num(41, 1)}\\r{w[31]} {num(42, 2)}\\n{num(41, 3)}'
                     for t in range(3) for pv in now]
        elif kind == 5:                 # (plat-fix2) the Hall: one PREV line per type (its screen has no CURRENT row); the
            mons = w[39].replace('{STRVAR_1 0, 0}', '{STRVAR_1 0, 2}')     # species in word 2, the numbers in 0 and 1
            assert mons != w[39], w[39]
            lines = [f'{w[24]}\\n{w[types[t]]}\\r{mons}\\n{w[29]} {num(38, 0)}\\f{w[31]} {num(38, 1)}' for t in range(3)]
        else:
            lines = [f'{w[25]}\\n{w[types[t]]}\\f{w[pv]} {num(43, 0)}\\f{w[31]} {num(43, 1)}' for t in range(3) for pv in now]
        ns = [job.line_text(('frontier_records', kind, k), t) for k, t in enumerate(lines)]
        assert ns == list(range(ns[0], ns[0] + len(lines))), ns          # (the macro counts from the first)
        return ns[0]

    def _frontier_records_facility(tr, a, var):
        """The facility values var can hold at the command at a: a value, or the SetVarFromValue values of var in the code the
        same entries reach (each machine's entry sets it once: FrontierRecords_BattleTower .. _BattleArcade)."""
        if var < 0x4000:
            return {var}
        d, pd, ents = tr.d, tr.job.pd, tr.reach_from.get(a, set())
        return {args[1][1] for x, (e, op, args) in d.insns.items() if tr.reach_from.get(x, set()) & ents
                and pd.cmd_name(op) == 'SetVarFromValue' and args[0][1] == var}

    @handler('OpenFrontierRecordsApp')
    def h_frontier_records(tr, a, vals, name):
        ctype, facility, species = vals
        fac = _frontier_records_facility(tr, a, facility)
        kinds = {FRONTIER_FACILITIES.get(f) for f in fac}
        if len(kinds) != 1 or None in kinds:
            tr.job.stubs[f'OpenFrontierRecordsApp (facility {sorted(fac)}: not one known facility)'] += 1
            return [f'pl_stub OpenFrontierRecordsApp  // facility {sorted(fac)}: not one known facility (no records shown)']
        kind = kinds.pop()
        if kind == 'Hall' and version.HALL_RECORDS_MACHINE:
            first = _frontier_records_lines(tr.job, 5)
            return [f'pl_HallRecordShow {tr.var(ctype)}, {tr.var(species)}, {first}  // OpenFrontierRecordsApp: the Battle '
                    f'Hall\'s record of the species as a message']
        if kind == 'Hall':
            # The Hall's records are a species' (its record and, for the latest species, the latest streak): the machine's
            # species list (ShowBattleHallRecordMonSelectionMenu) answers EXIT here, so this is never reached, and no script
            # command reads a species' record (PlatHall_GetRecordForSpecies has no op)
            tr.job.stubs['OpenFrontierRecordsApp for the Hall (its species list answers EXIT; no op reads a species\' record)'] += 1
            return [f'pl_stub OpenFrontierRecordsApp  // the Battle Hall\'s records of species {tr.var(species)}: never reached '
                    f'(its species list answers EXIT)']
        k = {'Tower': 1, 'Factory': 2, 'Castle': 4, 'Arcade': 6}[kind]
        first = _frontier_records_lines(tr.job, k)
        return [f'pl_FrontierRecords {k}, {tr.var(ctype)}, {first}  // OpenFrontierRecordsApp: the Battle {kind}\'s records '
                f'as messages']

    def _frontier_records_drops(tr):
        """{address: what it says}: the ReturnToField after OpenFrontierRecordsApp (no Black 2 screen ran: the field is open),
        and, where the records show as a message, the FadeScreen in after it and the FadeScreen out before the Call that
        opens them (CloseMessage and WaitFadeScreen between: FrontierRecords_OpenRecordDisplay, _OpenApp). The Hall's copy
        keeps its fades (nothing shows there)."""
        if getattr(tr, '_fr_records', None) is None:
            d, pd = tr.d, tr.job.pd
            name = lambda x: pd.cmd_name(d.insns[x][1]) if x in d.insns else None
            nxt = {x: e for x, (e, op, args) in d.insns.items()}
            prv = {e: x for x, e in nxt.items()}
            out = {}
            for c in [x for x in d.insns if name(x) == 'OpenFrontierRecordsApp']:
                kinds = {FRONTIER_FACILITIES.get(f) for f in _frontier_records_facility(tr, c, d.insns[c][2][1][1])}
                shown = len(kinds) == 1 and kinds <= ({'Tower', 'Factory', 'Castle', 'Arcade'} |
                                                      ({'Hall'} if version.HALL_RECORDS_MACHINE else set()))
                r = nxt.get(c)
                f1 = nxt.get(r)
                if name(r) == 'ReturnToField':
                    out[r] = ('the records were a message' if shown else 'no Black 2 screen ran')
                    if shown and name(f1) == 'FadeScreen' and d.insns[f1][2][2][1] == 1:
                        out[f1] = 'the records show as a message on the field'
                for x, (e, op, args) in d.insns.items():
                    if shown and name(x) == 'Call' and args and args[0] == ('rel', c):
                        p = prv.get(x)
                        while name(p) in ('CloseMessage', 'WaitFadeScreen'):
                            p = prv.get(p)
                        if name(p) == 'FadeScreen' and d.insns[p][2][2][1] == 0:
                            out[p] = 'the records show as a message on the field'
            tr._fr_records = out
        return tr._fr_records

    _h_fade_frrec_base, _h_return_field_frrec_base = HANDLERS['FadeScreen'], HANDLERS['ReturnToField']

    @handler('FadeScreen')
    def h_fade_frontier_records(tr, a, vals, name):
        if a in _frontier_records_drops(tr):
            return [f'// FadeScreen {vals[0]}, {vals[1]}, {vals[2]}, {vals[3]:#x}: {_frontier_records_drops(tr)[a]}']
        return _h_fade_frrec_base(tr, a, vals, name)

    @handler('ReturnToField')
    def h_return_field_frontier_records(tr, a, vals, name):
        if a in _frontier_records_drops(tr):
            return [f'// ReturnToField: the field stayed open (OpenFrontierRecordsApp: {_frontier_records_drops(tr)[a]})']
        return _h_return_field_frrec_base(tr, a, vals, name)
# ---- end plat-records
# ---- plat-fix2 (2026-11-11): the Frontier's and the Tower's last differences (version.LINK_STARTS_CANCEL, TOWER_INTRO_ONE_A).
def _prev_insn_fix2(tr, a):
    """The instruction before address a in the file (address order), or None."""
    if getattr(tr, '_prev_fix2', None) is None:
        tr._prev_fix2 = {e: x for x, (e, op, args) in tr.d.insns.items()}
    return tr._prev_fix2.get(a)


if version.LINK_STARTS_CANCEL:
    @handler('StartBattleClient', 'StartBattleServer')
    def h_link_start_closed(tr, a, vals, name):
        """Gen 4 StartBattleClient / StartBattleServer type, a, b, result (the wireless link's search for a group): the link is
        closed, so the answer is COMM_CLUB_RET_CANCEL (1), as when the player backs out with nobody there. Platinum's scripts
        then go back to their "join a group or become the leader" menu (pokeplatinum scripts_battle_factory.s
        BattleFactory_CancelJoiningGroup and the same in the Hall, Castle, Arcade, Tower, Poffin house, Contests, the Centers'
        2F). As a stub the result kept the menu's Yes (0, connected): the Frontier's Multi started with no partner."""
        return [f'pl_SetVarFromValue {tr.var(vals[3])}, 1  // Platinum {name} {", ".join(map(str, vals[:3]))}: the wireless '
                f'link is closed (COMM_CLUB_RET_CANCEL: nobody there)']

if version.TOWER_INTRO_ONE_A:
    _h_wait_ab_tower_base = HANDLERS['WaitABPress']

    @handler('WaitABPress')
    def h_wait_ab_after_tower_intro(tr, a, vals, name):
        """The WaitABPress right after PrintBattleTowerIntroMessage: Black 2's balloon (BSubwayCmd_Tool 352, EventBSubwayTrainerMsg)
        waits for A or B and closes itself, so the wait asked for a second A (as plat-test found for the four facilities)."""
        p = _prev_insn_fix2(tr, a)
        if p is not None and tr.job.pd.cmd_name(tr.d.insns[p][1]) == 'PrintBattleTowerIntroMessage':
            return ["// WaitABPress: the Tower opponent's balloon waited for A itself"]
        return _h_wait_ab_tower_base(tr, a, vals, name)
# ---- end plat-fix2


# ---------------------------------------------------------------- whole files

def musical_lines():
    """The Musical's lines (MUSICAL), in the order of pearl_musical.inc's MUSL_* (checked)."""
    lines = json.load(open(MUSICAL))['lines']
    order = {int(n): name for name, n in re.findall(r'^#define MUSL_(\w+) (\d+)', open(MUSICAL_INC).read(), re.M)
             if name != 'COUNT'}
    assert [m['id'] for m in lines] == [order[n] for n in sorted(order)], \
        f'{MUSICAL}: the ids are not pearl_musical.inc\'s MUSL_* order'
    return lines


def translate(pd, zone, ids):
    """(source lines, Black 2 text lines, job) for a Pearl zone's script file."""
    job = Job(pd, zone, ids)
    f = zone['scripts']
    main = FileTr(job, f, zone['text_bank'])
    body = main.lines()
    pid = zone['id']
    newgame = zone['name'] == NEWGAME_ZONE
    arrive_ids, arrive = pd.arrival_ids(pid)
    conts = []
    for sf, a, after, sbank in pd.warp_continuations(pid):
        k = arrive_ids[(sf, a)]
        label = f'W{sf}_{a:04X}_S'
        tr = FileTr(job, sf, sbank, mode='warp', starts=[(label, after, None)], prefix=f'W{sf}_{a:04X}')
        code = tr.lines()
        song = fixed_music(pd, sf, after)          # (SetBGMFixed: Pearl kept the music over the map change)
        if song is not None:
            at = code.index(f'{label}:') + 1
            code[at:at] = ['// the music Pearl kept over the map change (SetBGMFixed, fixed_music):'] + \
                [l if l.startswith(('#', ' ')) else '    ' + l for l in h_sound(tr, after, [song], 'PlayMusic')]
        conts.append((k, label, ['', f'// ---- continuation {k}: after the Warp at {sf}:{a:04X} '
                                     f'({next((z["name"] for z in pd.zones if z["scripts"] == sf), "a common script")})']
                      + code))
    if newgame:
        job.label_common(PEARL_NEW_GAME_SCRIPT)
    blackout = job.label_common(PEARL_BLACKOUT_HOME_SCRIPT) if zone['name'] == BLACKOUT_HOME_ZONE else None
    # proxies: Pearl global scripts this zone's people, signs and triggers run
    import pearl_events
    ev = job.events
    talkers = {o['script'] for o in ev['object_events']}
    proxies = []
    for gid in pearl_events.proxies(ev, pd, zone):
        label = job.label_common(gid, 'proxytalk' if gid in talkers else 'common')
        k = pd.proxy_ids()[gid]
        if job.init_level.get(k, 0):
            cf, _, centry = script_location(gid)
            job.level_commons[(cf, centry)] = job.init_level[k]
        proxies.append((k, f'PearlProxy_{gid}', ['', f'PearlProxy_{gid}:                  // Pearl global script {gid} '
                                                    f'(run by this zone\'s events)', f'    VMCall {label}', '    VMHalt']))
    subs, done = [], set()
    while job.common_queue:
        cf, bank, entry, mode = job.common_queue.pop(0)
        if (cf, entry, mode) in done:
            continue
        done.add((cf, entry, mode))
        d = pd.disasm(cf)
        pre = f'{"C" if mode == "common" else "T"}{cf}_{entry}'
        sub = FileTr(job, cf, bank, mode=mode, starts=[(f'{pre}_S{entry}', d.entries[entry - 1], entry)], prefix=pre)
        if (cf, entry) in job.level_commons:            # run by a map script (above): its level
            sub.force_levels = {job.level_commons[(cf, entry)]}
        subs += ['', f'// ---- Pearl global script {cf}:{entry} (a subroutine here)'] + sub.lines()
    n = len(main.d.entries)
    entry_label = {k: f'P{f}_S{k}' for k in range(1, n + 1)}
    entry_label.update({k: label for k, label, _ in conts})
    entry_label[arrive] = 'PearlArrive'
    entry_label.update({k: label for k, label, _ in proxies})
    if newgame:
        entry_label.update({k: f'PearlNewGame_{k}' for k in NEWGAME_ENTRIES})
    if blackout:
        assert BLACKOUT_ENTRY not in entry_label and BLACKOUT_ENTRY < FIRST_PROXY, entry_label
        entry_label[BLACKOUT_ENTRY] = 'PearlBlackoutHome'
    closed = []                                     # data/pearl_closed_facilities.json (CLOSED)
    musical = None                                  # the zone's first Musical line (a musical row: MUSICAL)
    for i, (k, row) in enumerate(zip(pd.closed_ids(pid), pd.closed(zone))):
        line = job.line_text(('musical', 'greeting', row['text']) if row.get('musical') else ('closed', i),
                             row['text'].replace('\n', '\\n'))    # (the same greeting: one line)
        dir_ = 255 if row.get('talk') else row['dir']
        entry_label[k] = f'PearlClosed_{i}'
        what = (f'object {row["obj"]}' if 'obj' in row else f'sign {row["bg"]}') if row.get('talk') else \
            f'trigger ({row["x"]}, {row["z"]}) {row["w"]}x{row["h"]}'
        if row.get('contest') is not None:
            assert row.get('talk') and 'obj' in row, f'{zone["name"]}: a Contest row is a person: {row}'
            closed += ['', f'PearlClosed_{i}:                  // a Super Contest counter (src/field_scripts/'
                           f'1282_global_contests.s): {what}', f'    RTCallGlobal {10785 + row["contest"]}', '    VMHalt']
            continue
        if row.get('musical'):
            assert row.get('talk') and 'obj' in row, f'{zone["name"]}: a Musical row is a person: {row}'
            if musical is None:
                musical = [job.line_text(('musical', m['id']), m['text'].replace('\n', '\\n'))
                           for m in musical_lines()][0]
            closed += ['', f'PearlClosed_{i}:                  // the Pokémon Musical\'s reception (data/pearl_closed_'
                           f'facilities.json "musical"): {what}', f'    pl_musical_reception {line}, {musical}', '    VMHalt']
            continue
        closed += ['', f'PearlClosed_{i}:                  // a closed place (data/pearl_closed_facilities.json): {what}',
                   f'    pl_closed_facility {line}, {dir_}', '    VMHalt']
    elev = pd.elevator_init(pid)                    # ELEVATOR_FLOORS_ABOVE: an elevator's floor or room
    if elev:
        entry_label[elev[0]] = 'PearlElevatorInit'
        closed += ['', 'PearlElevatorInit:                // zone init (after Pearl\'s): an elevator (ELEVATOR_FLOORS_ABOVE)']\
            + elev[1]
    rids = pd.ramanas_ids(pid)                      # Ramanas Park in Pal Park (b2tools/ramanas.py): the gate's
    if rids:                                        # slate clerk and walk-out, the park attendant's line in a visit
        import ramanas
        for name, k in rids.items():
            entry_label[k] = f'RamanasExtra_{name}'
        closed += ramanas.extra_code(job, pd, zone, rids)
    tb = pd.turnback_doors(pid)                     # Turnback Cave's maze: the doors after each arrival
    if tb:
        import turnback
        entry_label[tb] = 'TurnbackDoors'
        closed += turnback.doors_code(pid)
    villa = pd.villa_init(pid)                      # VILLA_VISITOR_ZONES (Platinum): the day's Villa visitor
    if villa:
        entry_label[villa[0]] = 'PearlVillaVisitor'
        closed += ['', 'PearlVillaVisitor:                // zone init (before Platinum\'s): the Villa\'s visitor of the day '
                       '(VILLA_VISITOR_ZONES)'] + villa[1]
    # ---- plat-frontier: the Battle Frontier's scenes this room hosts (block "plat-frontier" below; Platinum only)
    if version.PLATINUM:
        for k, label, lines in frontier_entries(job, pd, zone):
            if k is not None:
                entry_label[k] = label
            closed += lines
    # ---- end plat-frontier
    ending = pd.game_clear_ids(pid)                 # GAME_CLEAR_ZONE: Black 2's game clear's two ending scripts
    if ending:
        entry_label[ending[0]] = 'PearlEndingBeforeCredits'
        entry_label[ending[1]] = 'PearlEndingAfterCredits'
        closed += ['', 'PearlEndingBeforeCredits:          // Black 2\'s game clear, before the credits (GAME_CLEAR_ZONE): '
                       'the screen stays black,', '    BGMPlay SEQ_BGM_ENDING     // the ending song (Black 2\'s: Pearl\'s '
                       'is not installed)', '    VMHalt',
                   '', 'PearlEndingAfterCredits:           // Black 2\'s game clear, after the credits: nothing (THE END '
                       'follows)', '    VMHalt']
    while job.common_queue:                         # (sub-scripts queued by the extra entries just above)
        cf, bank, entry, mode = job.common_queue.pop(0)
        if (cf, entry, mode) in done:
            continue
        done.add((cf, entry, mode))
        d = pd.disasm(cf)
        pre = f'{"C" if mode == "common" else "T"}{cf}_{entry}'
        sub = FileTr(job, cf, bank, mode=mode, starts=[(f'{pre}_S{entry}', d.entries[entry - 1], entry)], prefix=pre)
        subs += ['', f'// ---- Pearl global script {cf}:{entry} (a subroutine here)'] + sub.lines()
    head = [f'// {zone["name"]}: Pearl script file {f}, text bank {zone["text_bank"]}. Written by b2tools/pearl_story.py:',
            '// do not edit; rerun `python3 b2tools/pearl_story.py zones ...` (notes/STORY.md).',
            f'// Scripts 1-{n}: Pearl\'s; {", ".join(f"{k}: after a Warp" for k, _, _ in conts) or "no warp continuations"}; '
            f'{arrive}: PearlArrive' + ('; 29-31: the new game' if newgame else '') +
            (f'; {BLACKOUT_ENTRY}: after a black-out (Pearl {PEARL_BLACKOUT_HOME_SCRIPT})' if blackout else '') +
            (f'; {", ".join(f"{k}: Pearl {l[11:]}" for k, l, _ in proxies)}' if proxies else ''),
            '#include "asm/field_script.inc"', '#include "pearl.h"', '#include "pearl_story.inc"'] + \
        (['#include "pearl_musical.inc"'] if musical is not None else []) + ['']
    for k in range(1, max(entry_label) + 1):
        head.append(f'    ScriptEntry {entry_label.get(k, "PearlNoScript")}')
    head += ['    ScriptEntriesEnd', '']
    tail = ['', 'PearlNoScript:', '    VMHalt', '',
            'PearlArrive:                      // arriving by a script warp with nothing after it: fade in, release',
            '    FadeInBlack', '    FadeWait', '    FinishAllEvents', '    ActorsUnpauseAll', '    VMHalt']
    if blackout:
        tail += ['', f'PearlBlackoutHome:                // after a black-out at home: Pearl\'s common script {PEARL_BLACKOUT_HOME_SCRIPT}',
                 f'    VMCall {blackout}', '    VMHalt']
    if newgame:
        z0, x0, z_0, d0 = PEARL_START
        start = pd.by_name[z0]
        _, start_arrive = pd.arrival_ids(start['id'])
        tail += ['', f'#define PEARL_START_ZONE {pd.b2_zone[start["id"]]}   // {z0}',
                 f'#define PEARL_START_X {x0}', f'#define PEARL_START_Z {z_0}', f'#define PEARL_START_DIR {d0}',
                 f'#define PEARL_START_ARRIVE {start_arrive}   // its PearlArrive']
        if job.label_common(PEARL_NEW_GAME_SCRIPT) != 'C377_1_S1':      # (newgame.inc names Pearl's label; Platinum's file has another number)
            tail += [f'#define C377_1_S1 {job.label_common(PEARL_NEW_GAME_SCRIPT)}']
        tail += ['#include "pearl/newgame.inc"']
    src = head + body + [l for _, _, c in conts for l in c] + [l for _, _, c in proxies for l in c] + closed + subs + tail + \
        ['', '    .balign 4, 0', '']
    text = [job.gen4_text.b2_line(t, v) for t, v in job.text]
    return src, text, job


def slug(name):
    return name[4:].lower() if name.startswith('MAP_') else name.lower()


def write_zone(pd, ids, zone):
    src, text, job = translate(pd, zone, ids)
    num, tnum = pd.script_file(zone), pd.text_file(zone)
    base = f'pearl_{slug(zone["name"])}'
    for d, n, ext in ((SRC_SCRIPTS, num, '.s'), (SRC_TEXT, tnum, '.txt')):
        os.makedirs(d, exist_ok=True)
        for old in os.listdir(d):
            if old.startswith(f'{n:04d}_') and old != f'{n:04d}_{base}{ext}':
                raise SystemExit(f'{d}/{old} already has number {n}')
    p = os.path.join(SRC_SCRIPTS, f'{num:04d}_{base}.s')
    open(p, 'w').write('\n'.join(src))
    tp = os.path.join(SRC_TEXT, f'{tnum:04d}_{base}.txt')
    pre = 'Pearl' + ''.join(w.capitalize() for w in slug(zone['name']).split('_'))
    open(tp, 'w', encoding='utf-8').write(''.join(f'{pre}_Text_{i:03d} = {t}\n' for i, t in enumerate(text)))
    return p, tp, job


def assemble(path):
    sys.path.insert(0, os.path.join(HERE, 'patches'))
    import scripts
    return scripts.assemble(path)


def summary(job):
    s = f'{job.name}: {sum(job.done.values())} commands translated'
    if job.stubs:
        s += f', {sum(job.stubs.values())} stubbed ({", ".join(f"{k} x{v}" for k, v in job.stubs.most_common())})'
    if job.approx:
        s += f'; approximated: {", ".join(f"{k} x{v}" for k, v in job.approx.most_common())}'
    return s


def zone_arg(pd, a):
    return pd.zones[int(a)] if a.isdigit() else pd.by_name[a if a.startswith('MAP_') else 'MAP_' + a.upper()]


def _decodes(pd, f):
    try:
        pd.disasm(f)
        return True
    except Exception:
        return False


def report(pd, ids):
    """Translate every Pearl zone's script file offline, assemble each, count translated and stubbed commands."""
    os.makedirs(OFFLINE, exist_ok=True)
    done, stub, approx = collections.Counter(), collections.Counter(), collections.Counter()
    per_file, bad, seen = [], [], set()
    status = {}
    for z in pd.zones:
        if z['scripts'] in seen:
            continue
        seen.add(z['scripts'])
        try:
            src, text, job = translate(pd, z, ids)
        except Exception as e:          # one file's problem must not hide the others' results
            bad.append(f'{z["name"]} (file {z["scripts"]}): {type(e).__name__}: {e}')
            continue
        p = os.path.join(OFFLINE, f'{z["scripts"]:04d}_{slug(z["name"])}.s')
        open(p, 'w').write('\n'.join(src))
        try:
            assemble(p)
        except BaseException as e:
            bad.append(f'{z["name"]} (file {z["scripts"]}): does not assemble: {str(e)[:300]}')
        status.update(job.insn_status)
        done.update(job.done)
        stub.update(job.stubs)
        approx.update(job.approx)
        per_file.append(summary(job))
    nd, ns = sum(done.values()), sum(stub.values())
    # every Pearl command once (a common script counts once, not once per zone that calls it)
    ud = sum(1 for n, s in status.values() if s == 'done')
    us = collections.Counter(n for n, s in status.values() if s == 'stub')
    total = sum(len(pd.disasm(f).insns) for f in range(len(pd.files)) if pd.files[f] and f not in pd.level_files
                and _decodes(pd, f))
    out = [f'{len(seen)} Pearl zone script files translated offline (common scripts inside the zones that call them), '
           f'{len(bad)} with problems',
           f'command uses: {nd} translated, {ns} stubbed ({100 * nd / max(1, nd + ns):.1f} % translated); '
           f'{len(done)} commands translated, {len(stub)} stubbed',
           f'Pearl\'s own commands, each once: {ud} translated, {sum(us.values())} stubbed '
           f'({100 * ud / max(1, ud + sum(us.values())):.1f} %), of {total} decoded in all of Pearl\'s script files '
           f'({total - ud - sum(us.values())} are in code no zone, warp or person reaches: unused scripts, the extra '
           f'End after a GoTo, files of features no zone uses)', '',
           'stubbed, each Pearl command once:'] + [f'  {k}: {v}' for k, v in us.most_common()] + ['',
           'stubbed (uses in the translated files; a common script counts in every zone that calls it):']
    out += [f'  {k}: {v}' for k, v in stub.most_common()]
    out += ['', 'approximated (uses):'] + [f'  {k}: {v}' for k, v in approx.most_common()]
    out += ['', 'problems:'] + [f'  {b}' for b in bad] + ['', 'per file:'] + [f'  {s}' for s in per_file]
    open(os.path.join(OFFLINE, 'report.txt'), 'w').write('\n'.join(out) + '\n')
    print('\n'.join(out[:4]))
    print(f'full report: {os.path.relpath(os.path.join(OFFLINE, "report.txt"), ROOT)}')
    return 0


# ---- plat-look (2026-11-08): Veilstone's walk into the Galactic Warehouse (Platinum's file 131,
# VeilstoneCity_EnterWarehouseZ595/Z597: the player one step to z 596, east 5 behind the Department Store, north 5 up
# the warehouse's steps). Black 2's camera is 237 units from the player, Platinum's 667: on that street Black 2's eye
# passes 20-60 units over the store's rooftop balloons (build model 214, material c7_s04_b_lm4, 146-201 units up) and
# they fill 30-52 % of the screen (plat-test's frames; offline ray cast work/agents/plat-look/scratch/store_camera.py),
# where Platinum's eye, on the same line of sight but far behind, shows them small (6 %). For the walk the camera stays
# on the player (EvCameraInit without EvCameraUnbind: the bound target wins over the move's, ov036 field_camera.c
# TARGET_REL) at the field's pitch, 59 degrees, and pulls back to 340 units over the walk's first 16 frames (the
# balloons at most 10 %, nothing nearer than 100 units; 400 units: 4 %); back to the field's camera behind the fade-out,
# before the warp.
if version.PLATINUM:
    WAREHOUSE_FILE = 131                                   # MAP_VEILSTONE's script file
    WAREHOUSE_WALK = {0x8A9, 0x8C3}                        # each branch's first ApplyMovement (Looker's)
    WAREHOUSE_WARP = 0x8FF                                 # Warp MAP_HEADER_VEILSTONE_CITY_GALACTIC_WAREHOUSE, 8, 11
    WAREHOUSE_CAM = f'{0x29FE}, 0, {340 << 12:#x}'          # pitch (maplook 'tilt': Pearl's 59), yaw, distance

    _h_apply_movement_look = HANDLERS['ApplyMovement']

    @handler('ApplyMovement')
    def h_warehouse_walk_camera(tr, a, vals, name):
        out = _h_apply_movement_look(tr, a, vals, name)
        if tr.f == WAREHOUSE_FILE and a in WAREHOUSE_WALK:
            out = ['EvCameraInit  // (plat-look) the walk behind the Department Store: the camera stays on the player',
                   f'EvCameraMoveTo {WAREHOUSE_CAM}, 0, 0, 0, 16  // and pulls back to 340 units (its target: the player)'] + out
        return out

    _h_warp_look = HANDLERS['Warp']

    @handler('Warp')
    def h_warehouse_warp_camera(tr, a, vals, name):
        out = _h_warp_look(tr, a, vals, name)
        if tr.f == WAREHOUSE_FILE and a == WAREHOUSE_WARP:
            out = ['EvCameraReturn 1  // (plat-look) the field\'s camera again, behind the fade', 'EvCameraWait',
                   'EvCameraEnd'] + out
        return out
# ---- end plat-look


# every handler is registered: the item arguments of ITEM_ARG's commands go through item_value
for _n, _k in ITEM_ARG.items():
    if _n in HANDLERS:
        HANDLERS[_n] = _item_handler(HANDLERS[_n], _k)


def main(argv):
    import pearl_ids
    pd = PearlData()
    ids = pearl_ids.Ids()
    if argv[:1] == ['show']:
        f = int(argv[1])
        z = next(z for z in pd.zones if z['scripts'] == f)
        src, text, job = translate(pd, z, ids)
        print('\n'.join(src))
        print(summary(job), file=sys.stderr)
        return 0
    if argv[:1] == ['all']:         # every zone the world installs (a Platinum tree's first run: Pearl's are in src/, by Pearl's numbers)
        written = sorted({z['id'] for z in pd.zones if z['id'] in pd.b2_zone})
        if version.PLATINUM:        # (as Pearl: a zone Pearl installs with no file of this generator's keeps its own: the shared Center 2F,
            pearl_world = json.load(open(os.path.join(ROOT, 'data', 'sinnoh_world.json')))      # the Underground, unused rooms)
            pearl_world = set(pearl_world['zones']) | set(pearl_world['rooms']['zones'])
            mine = lambda z: os.path.exists(os.path.join(ROOT, 'src', 'field_scripts', f'{pd.script_file(z):04d}_pearl_{slug(z["name"])}.s'))
            for zid in [z for z in written if str(z) in pearl_world and not mine(pd.zones[z])]:
                written.remove(zid)
                for d, n, ext in ((SRC_SCRIPTS, pd.script_file(pd.zones[zid]), '.s'), (SRC_TEXT, pd.text_file(pd.zones[zid]), '.txt')):
                    old = os.path.join(d, f'{n:04d}_pearl_{slug(pd.zones[zid]["name"])}{ext}')
                    if os.path.exists(old):
                        os.replace(old, os.path.expanduser(f'~/.Trash/{os.path.basename(old)}'))
        problems, kept = [], 0
        for zid in written:
            try:
                p, tp, job = write_zone(pd, ids, pd.zones[zid])
                if pd.zone_same(pd.zones[zid], p, tp):     # Pearl's files, as they are
                    kept += 1
                    os.replace(p, os.path.expanduser(f'~/.Trash/{os.path.basename(p)}'))
                    os.replace(tp, os.path.expanduser(f'~/.Trash/{os.path.basename(tp)}'))
                    continue
                assemble(p)
            except BaseException as e:
                problems.append(f'{pd.zones[zid]["name"]}: {type(e).__name__}: {str(e)[:200]}')
        print(f'{len(written)} zones: {kept} keep Pearl\'s files, {len(written) - kept} written -> {os.path.relpath(SRC_SCRIPTS, ROOT)}, {len(problems)} with problems')
        print('\n'.join(problems[:40]))
        return 0
    if argv[:1] in (['zones'], ['chapter']):
        for a in (CHAPTERS[int(argv[1]) if argv[1].isdigit() else argv[1]] if argv[0] == 'chapter' else argv[1:]):
            p, tp, job = write_zone(pd, ids, zone_arg(pd, a))
            assemble(p)
            print(f'{os.path.relpath(p, ROOT)} + {os.path.relpath(tp, ROOT)}: {summary(job)}')
        return 0
    if argv[:1] == ['report']:
        return report(pd, ids)
    print(__doc__)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
