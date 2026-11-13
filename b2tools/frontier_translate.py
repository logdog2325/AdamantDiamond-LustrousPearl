"""The Battle Frontier's scenes as Black 2 field scripts (notes/PLATINUM_FRONTIER.md "The script language").

Platinum runs the Frontier's battle rooms as 2D scenes with their own script language (b2tools/frontier_script.py reads it).
Here each scene runs in a field room of ours, its host, as scripts of that zone's file:

1. synthesize(): a scene's frontier script becomes a Platinum field-script file, command for command (FIELD below), with the
   same flow, messages, menus, Tower functions, sounds and saves. Platinum's own field commands are what its field scripts use
   for the same jobs, so pearl_story's handlers, which already translate those into Black 2's, do the rest: the scene's
   file is translated like any Platinum script file, from the entry points the scenes are started at (pearl_story.py block
   "plat-frontier").
2. The scene's staging goes onto the host room: its objects (FrontierScrCmd_24 rows: local id, look, direction, pixel x and
   y, drawn) are the room's people (HOSTS: local id -> the room's object, the scene's pixel origin on the room's grid), its
   movement lists convert code for code (MOVES), WarpIn/WarpOut show and hide, its door sprites are the room's door
   animations.
3. Scenes start and end with markers on Platinum's LaunchBattleFrontierScene (an opcode no other file uses with these values):
   0x00-0x1F a field script starts scene n (Platinum's own use); 0x20 + n ChangeScript n, entry 0; 0x40 + n ChangeScript n,
   entry 1; 0x60 + n ChangeSceneWithinScript n (the script goes on in scene n's room); 0xFF ExitFrontier (back to the
   field script that started the chain, after its ReturnToField). pearl_story turns them into warps between the rooms with
   RTReserveScript, as it does for Gen 4's Warp.

    python3 b2tools/frontier_translate.py report        what every command becomes, by scene file
"""
import json, os, re, struct, sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import frontier_script as fs  # noqa: E402

PLATINUM = fs.PLATINUM
FILE_BASE = 3000            # synthesized files' slots in pearl_story's PearlData.files (past Platinum's 1,257 slots)
CARRIER_BASE = 840          # (plat-frontier-rooms) a facility command's carrier: 840 + its frontier opcode, past Platinum's
#                             840 field commands (gen4_script_cmds_platinum.json); pearl_story's table grows by them
VAR_EXTRA = 0x8800          # frontier vars 0x800D-0x8013 in a synthesized file (pearl_story maps them to FR_VAR_800D..)
LOCALID_PLAYER = 0xFF
MARK_CHANGE, MARK_CHANGE1, MARK_WITHIN, MARK_EXIT = 0x20, 0x40, 0x60, 0xFF
GFX_VAR0, GFX_VAR_FIRST = 101, 0x4020   # OBJ_EVENT_GFX_VAR_0..3 read VAR_OBJ_GFX_ID_0..3 (0x4020-0x4023)
DOOR_TAG = (77, 78)                     # ANIMATION_TAG_DOOR_1, _2


# ---------------------------------------------------------------- the scenes (src/overlay104/frontier_scenes.c)
def _text_bank_numbers():
    rows = [l.strip() for l in open(os.path.join(PLATINUM, 'generated', 'text_banks.txt')) if l.strip()]
    return {n: i for i, n in enumerate(rows)}


def scenes():
    """{scene id: {name, script (fr_script narc index), bank (Platinum's bank), bgm}} for the scenes with a script."""
    enum = re.findall(r'(FRONTIER_SCENE_\w+)', open(os.path.join(PLATINUM, 'include', 'constants', 'battle_frontier.h')).read())
    ids = {n: i for i, n in enumerate(OrderedDict.fromkeys(enum))}
    text = open(os.path.join(PLATINUM, 'src', 'overlay104', 'frontier_scenes.c')).read()
    banks = _text_bank_numbers()
    order = fs.source_order()
    out = {}
    for name, body in re.findall(r'\[(FRONTIER_SCENE_\w+)\]\s*=\s*\{(.*?)\n    \}', text, re.S):
        script = re.search(r'\.scriptID\s*=\s*(\w+)', body)
        bank = re.search(r'\.textBankID\s*=\s*(\w+)', body).group(1)
        bgm = re.search(r'\.bgmID\s*=\s*(\w+)', body).group(1)
        if not script:
            continue
        out[ids[name]] = {'name': name, 'script': order.index(script.group(1)),
                          'bank': banks[bank] if bank in banks else int(bank, 0), 'bgm': bgm}
    return out


def scene_id(name):
    return next(k for k, s in scenes().items() if s['name'] == name)


# ---------------------------------------------------------------- the host rooms
# Each Tower scene runs in the field room Platinum still carries for it (Pearl's room: notes/BATTLE_ZONE.md), named here by
# PearlB2's zone names (pokediamond's): Platinum's BATTLE_TOWER_CORRIDOR is our MAP_BATTLE_TOWER_CORRIDOR_MULTI, and so on.
# origin: added to a scene's pixel x and y before // 16 gives the room's tile; found from the room's own people, which stand
# where the scene draws them (the corridor's attendant (56, 32) is the room's (2, 1); the battle room's attendant (48, 104),
# its player (128, 168) and opponent's first step (128, 56) are (2, 6), (7, 10) and (7, 3); the multi rooms' pairs the same).
# objects: the scene's local id -> the room's object id ('player': the real player). dynamic: the room's objects drawn from
# VAR_OBJ_GFX_ID_n (Platinum gfx 101-104), so a row's look var is copied there before the object is added. doors: the
# scene's door sprite slot -> (x, z) of the room's door animation (the room's own LoadDoorAnimation in Platinum's field script
# for it). arrive: where the warp into the room puts the real player, (x, z, direction): Pearl's own warps into these rooms
# (Pearl's elevator, script 359: the corridors (2, 1) and (8, 3) facing down; the corridors' warps into the battle rooms, (7, 6)
# and (7, 5) facing up), so the camera frames each room as Pearl's did (the scene hides the player in all but the corridor,
# where the player walks out of the door from that tile). The Factory's, Hall's and Castle's scenes run in the picture rooms
# (plat-frontier-rooms: their rows are added below, from b2tools/frontier_rooms.py).
HOSTS = {
    'FRONTIER_SCENE_TOWER_CORRIDOR': {
        'zone': 'MAP_BATTLE_TOWER_CORRIDOR_MULTI', 'origin': (-16, -16),
        'objects': {0: 'player', 1: 0}, 'dynamic': {}, 'flags': {}, 'doors': {0: (2, 2)}, 'arrive': (2, 1, 1)},
    'FRONTIER_SCENE_TOWER_MULTI_CORRIDOR': {
        'zone': 'MAP_BATTLE_TOWER_CORRIDOR_WIFI', 'origin': (-8, -16),
        'objects': {0: 'player', 1: 0, 2: 1, 3: 2, 4: 3, 5: 2, 6: 3}, 'dynamic': {2: 0, 3: 1}, 'flags': {},
        'doors': {0: (3, 2), 1: (14, 2)}, 'arrive': (8, 3, 1)},
    'FRONTIER_SCENE_TOWER_BATTLE_ROOM': {
        'zone': 'MAP_BATTLE_TOWER_ARENA_MULTI', 'origin': (-16, 0),
        'objects': {0: 'player', 1: 0, 2: 1, 3: 2}, 'dynamic': {1: 1, 2: 0}, 'flags': {1: 459}, 'doors': {}, 'arrive': (7, 6, 0)},
    'FRONTIER_SCENE_TOWER_MULTI_BATTLE_ROOM': {
        'zone': 'MAP_BATTLE_TOWER_ARENA_WIFI', 'origin': (-8, -24),
        'objects': {0: 'player', 1: 0, 2: 1, 3: 5, 4: 4, 5: 2, 6: 3, 7: 2, 8: 3}, 'dynamic': {2: 0, 3: 1, 4: 3, 5: 2},
        'flags': {4: 491, 5: 490}, 'doors': {}, 'arrive': (7, 5, 0)},
}


# ---- plat-frontier-rooms (2026-11-07): the Factory's, Hall's and Castle's scenes in their picture rooms (b2tools/frontier_rooms.py:
# Platinum's own backgrounds as field rooms, zones 719-726). Each room's people are the objects its script file places, by their
# local ids (the room's person uid = the scene's local id), so a file's two or three scenes stage the same way in their rooms:
# the same origin, the same people, the same look slots. A person drawn from a var takes a slot of VAR_OBJ_GFX_ID_n (Platinum
# gfx 101 + n, Black 2 code 162 + n), in local id order. arrive: the hidden player's tile, where Platinum's scene camera looks
# (frontier_rooms.camera_tile; the room's camera adds what lies between two tiles). The Arcade's rooms are built too, but its
# scenes wait for plat-arcade's commands (PICTURE_HOSTED).
PICTURE_HOSTED = ('FACTORY', 'HALL', 'CASTLE')


def _picture_hosts():
    import frontier_rooms as fr
    out = {}
    for r in fr.ROOMS:
        if r['name'].split('_')[2] not in PICTURE_HOSTED:
            continue
        people = fr.people(r)
        looks = sorted(local for local, gfx in people.items() if gfx >= 0x8000)
        tx, tz, dx, dz = fr.camera_tile(r, *fr.player_place(r))
        out[r['scene']] = {
            'zone': r['name'], 'origin': fr.origin(r), 'objects': dict([(0, 'player')] + [(l, l) for l in people]),
            'dynamic': {l: n for n, l in enumerate(looks)}, 'flags': {}, 'doors': {}, 'arrive': (tx, tz, 0), 'picture': True}
    return out


HOSTS.update(_picture_hosts())
# ---- end plat-frontier-rooms
# ---- plat-arcade (2026-11-07): the Arcade's scenes in their picture rooms too, its commands on its Frontier ops (pearl_story's block
# "plat-arcade": the board, the effect, the battle; notes/PLATINUM_FRONTIER.md "The Battle Arcade")
PICTURE_HOSTED = PICTURE_HOSTED + ('ARCADE',)
HOSTS.update(_picture_hosts())
# ---- end plat-arcade


def host(scene):
    return HOSTS.get(scenes()[scene]['name'])


# Launch sites that no game reaches here: the Wi-Fi rooms are closed (data/pearl_closed_facilities.json: the lobby's Wi-Fi
# attendant), so the elevator's Wi-Fi branch never starts its scene: {(Pearl map, the n-th LaunchBattleFrontierScene of
# its file)}
CLOSED_SITES = {('MAP_BATTLE_TOWER_ELEVATOR', 3)}         # its third: BattleTowerElevator_WiFiBattleRoom


# ---------------------------------------------------------------- the field side: opcodes and layouts
_FIELD = None


def field_ops():
    """{SCRCMD name without prefix: (opcode, [arg types])} of Platinum's field scripts (the gen4_script table's layouts)."""
    global _FIELD
    if _FIELD is None:
        import gen4_script
        consts = re.findall(r'ScriptCommand\(SCRCMD_(\w+),\s*(\w+)\)',
                            open(os.path.join(PLATINUM, 'include', 'data', 'scripts', 'scrcmd.h')).read())
        table = json.load(open(os.path.join(HERE, 'data', 'gen4_script_cmds_platinum.json')))
        rows = table['commands'] if isinstance(table, dict) and 'commands' in table else table
        rows = {int(k): v for k, v in (rows.items() if isinstance(rows, dict) else enumerate(rows))}
        _FIELD = {n: (op, rows[op]['args']) for op, (n, h) in enumerate(consts) if op in rows}
    return _FIELD


# Frontier movement codes -> Platinum field movement codes (b2tools/data/pearl_movement.json's numbers)
MOVES = {0: 0x00, 1: 0x01, 2: 0x02, 3: 0x03,                 # Face
         4: 0x0C, 5: 0x0D, 6: 0x0E, 7: 0x0F,                 # Walk = WalkNormal
         8: 0x08, 9: 0x09, 10: 0x0A, 11: 0x0B,               # WalkSlow
         12: 0x10, 13: 0x11, 14: 0x12, 15: 0x13,             # WalkFast
         16: 0x20, 17: 0x21, 18: 0x22, 19: 0x23,             # WalkOnSpot = WalkOnSpotNormal
         20: 0x1C, 21: 0x1D, 22: 0x1E, 23: 0x1F,             # WalkOnSpotSlow
         24: 0x24, 25: 0x25, 26: 0x26, 27: 0x27,             # WalkOnSpotFast
         28: 0x28, 29: 0x29, 30: 0x2A, 31: 0x2B,             # WalkOnSpotFaster
         32: 0x3C, 33: 0x3D, 34: 0x3E, 35: 0x3F, 36: 0x40, 37: 0x41, 38: 0x42,   # Delay 1, 2, 4, 8, 15, 16, 32
         39: 0x46, 40: 0x45}                                 # WarpIn = SetVisible, WarpOut = SetInvisible (the draw flag)
FIELD_MOVE_END = 0xFE


class Asm:
    """A Platinum field-script file: entries, commands with label arguments, movement lists."""

    def __init__(self):
        self.items, self.entries = [], []

    def label(self, name):
        self.items.append(('label', name))

    def op(self, name, *args):
        opcode, types = field_ops()[name]
        assert len(args) == len(types), (name, args, types)
        self.items.append(('op', opcode, list(zip(types, args))))

    def raw(self, opcode, args):
        """A command by opcode with typed arguments [(type, value)] (plat-frontier-rooms: the facility commands' carriers)."""
        self.items.append(('op', opcode, list(args)))

    def movement(self, name, rows):
        self.items.append(('align',))
        self.items.append(('label', name))
        self.items.append(('mov', rows))

    def build(self):
        def size(it):
            if it[0] == 'op':
                return 2 + sum(fs.SIZES.get(t, 2) if t not in ('rel', 'mov', 'u32') else 4 for t, v in it[2])
            if it[0] == 'mov':
                return 4 * len(it[1]) + 4
            return 0
        head = 4 * len(self.entries) + 2
        for _ in range(2):
            pos, labels = head, {}
            for it in self.items:
                if it[0] == 'align':
                    pos = (pos + 3) & ~3
                elif it[0] == 'label':
                    labels[it[1]] = pos
                else:
                    pos += size(it)
        out = bytearray()
        for i, e in enumerate(self.entries):
            out += struct.pack('<i', labels[e] - (4 * i + 4))
        out += struct.pack('<H', fs.END)
        for it in self.items:
            if it[0] == 'align':
                while len(out) % 4:
                    out.append(0)
            elif it[0] == 'label':
                assert labels[it[1]] == len(out), it
            elif it[0] == 'mov':
                for code, n in it[1]:
                    out += struct.pack('<HH', code, n)
                out += struct.pack('<HH', FIELD_MOVE_END, 0)
            else:
                out += struct.pack('<H', it[1])
                for t, v in it[2]:
                    if t in ('rel', 'mov'):
                        out += struct.pack('<i', labels[v] - (len(out) + 4))
                    elif t == 'u8':
                        out += struct.pack('<B', v)
                    elif t == 'u32':
                        out += struct.pack('<I', v)
                    else:
                        out += struct.pack('<H', v & 0xFFFF)
        return bytes(out), labels


def fvar(v):
    """A frontier var-or-value in a synthesized file: vars 0x8000-0x800C keep their numbers (Platinum's field script vars),
    0x800D-0x8013 go to 0x8800 + n (pearl_story maps those to FR_VAR_800D ..: no Platinum field script uses them)."""
    if 0x800D <= v <= 0x8013:
        return VAR_EXTRA + v - 0x800D
    return v


# ---------------------------------------------------------------- the translation, command by command
# What each frontier command becomes: a function (synth, insn) or a note. 'drop' = no field command: the reason is the note.
DROPPED = {
    'FrontierScrCmd_22': 'loads the objects\' pictures: the room loads its people itself',
    'FrontierScrCmd_23': 'frees a picture: nothing to free',
    'FrontierScrCmd_2A': 'loads door sprites: the room\'s door is part of its map',
    'FrontierScrCmd_2B': 'frees door sprites: nothing to free',
    'FrontierScrCmd_2C': 'places door sprites: the room\'s door is part of its map',
    'FrontierScrCmd_2F': 'mirrors a door sprite: the room\'s doors are drawn the right way',
    'FrontierScrCmd_32': 'stops a door sprite\'s animation (it stays open): the room\'s door stays open the same way',
    'SetMenuXOriginSide': 'Black 2\'s list menu is at the right edge already',
    'InitNewBattleRecording': 'the Vs. Recorder: not in Black 2 here (closed like the Battle Video machines)',
    'FreeBattleRecording': 'the Vs. Recorder: not in Black 2 here',
    'FrontierScrCmd_3F': 'the battle\'s screen transition and song: the Battle Subway\'s battle start plays its own',
    'PlayFrontierBrainEncounterEffect': 'the Brain\'s cut-in before the battle: Black 2 has no such screen; the battle starts '
                                        'with the Subway\'s transition (an approximation, listed in the report)',
    'FrontierScrCmd_C8': 'a TV segment about the partner (TV segments are dropped, as Pearl\'s are)',
    'Noop': 'nothing',
}
# Commands that only the wireless Multi uses (closed: notes/BATTLE_ZONE.md): a value that keeps the solo path
WIRELESS = {'ClearReceivedTempDataAllPlayers', 'SyncConnectedPlayers', 'EndCommunication', 'FrontierScrCmd_89',
            'FrontierScrCmd_8A', 'FrontierScrCmd_4B'}


class Synth:
    def __init__(self, index):
        self.index = index
        self.d = fs.Disasm(fs.files()[index])
        self.scene_ids = [k for k, s in scenes().items() if s['script'] == index]
        self.asm = Asm()
        self.notes = Counter()          # (command, what) -> uses
        self.movs = {}                  # frontier movement address -> label
        self.skip = set()
        self.host = None
        for k in self.scene_ids:
            if host(k):
                self.host = host(k)
        self.picture = bool(self.host and self.host.get('picture'))     # (plat-frontier-rooms)
        if self.picture:
            self._looks()

    def L(self, a):
        return f'L{a:04X}'

    def note(self, name, what):
        self.notes[(name, what)] += 1

    def build(self):
        a = self.asm
        self._recorder_question()
        # vars that hold a scene's local id for ApplyMovement (the multi rooms: 0x8001-0x8003 by mode): the values set into
        # them are local ids too, so they become the room's object ids (HOSTS objects)
        self.local_vars = {v[0] for e, op, v in self.d.insns.values() if self.d.name(op) == 'ApplyMovement' and v[0] >= 0x8000}
        for e in self.d.entries:
            a.entries.append(self.L(e))
        code = sorted(x for x in self.d.insns if x not in getattr(self.d, 'unreferenced', ()))
        for x in code:
            a.label(self.L(x))
            if x in self.skip:
                continue
            end, op, vals = self.d.insns[x]
            self.command(x, self.d.name(op), vals, end)
        for m, label in sorted(self.movs.items()):
            kind, end, rows = self.d.data_blocks[m]
            a.movement(label, [(MOVES[c], n) for c, n in rows])
        data, labels = a.build()
        return data, {x: labels[self.L(x)] for x in code}

    def _recorder_question(self):
        """FrontierScrCmd_70 (is a battle video saved?), its two lines, ShowYesNoMenu (record this battle?): the Vs.
        Recorder isn't here, so the question isn't asked and the answer is No (a SetVar on the menu's var)."""
        d = self.d
        code = sorted(x for x in d.insns if x not in getattr(d, 'unreferenced', ()))
        for i, x in enumerate(code):
            if d.name(d.insns[x][1]) != 'FrontierScrCmd_70':
                continue
            j = i
            while d.name(d.insns[code[j]][1]) != 'ShowYesNoMenu':
                j += 1
            for y in code[i:j]:
                self.skip.add(y)
            self.recorder_at = getattr(self, 'recorder_at', set()) | {code[j]}

    def gfx_var(self, local, gfx):
        """Lines before an object appears: its look into the room's VAR_OBJ_GFX_ID_n when the scene draws it from a var."""
        h = self.host
        f = h['objects'].get(local)
        if f is None or f == 'player' or f not in h['dynamic'] or gfx in (fs.PLAYER_GFX, fs.LINKED_GFX):
            return
        if gfx >= 0x8000 and self.picture and (gfx in self.const_looks or gfx in self.player_looks):
            return                  # (plat-frontier-rooms: the slot was set where the var was: SetVar, GetPlayerObjEventGfx)
        if gfx >= 0x8000:
            self.asm.op('SETVARFROMVAR', GFX_VAR_FIRST + h['dynamic'][f], fvar(gfx))
        else:
            self.asm.op('SETVARFROMVALUE', GFX_VAR_FIRST + h['dynamic'][f], gfx)

    def command(self, x, name, v, end):
        a = self.asm
        if x in getattr(self, 'recorder_at', ()):
            a.op('SETVARFROMVALUE', fvar(v[0]), 1)
            self.note(name, 'the Vs. Recorder\'s question: not asked, answered No')
            return
        if name in DROPPED:
            self.note(name, 'dropped: ' + DROPPED[name])
            return
        if name in WIRELESS:
            self.note(name, 'wireless Multi only (closed): nothing')
            return
        simple = {'End': 'END', 'Return': 'RETURN', 'WaitFadeScreen': 'WAITFADESCREEN', 'CloseMessage': 'CLOSEMESSAGE',
                  'WaitABPress': 'WAITABPRESS', 'ShowListMenu': 'SHOWLISTMENU', 'WaitMovement': 'WAITMOVEMENT',
                  'HealParty': 'HEALPARTY', 'WaitFanfare': 'WAITFANFARE', 'ShowSavingIcon': 'SHOWSAVINGICON',
                  'HideSavingIcon': 'HIDESAVINGICON', 'FreeTowerStruct': 'FREEBATTLETOWER',
                  'FreeBattleTower': 'FREEBATTLETOWER'}
        if name in simple:
            a.op(simple[name])
            return
        if name == 'GoTo':
            a.op('GOTO', self.L(v[0]))
        elif name == 'Call':
            a.op('CALL', self.L(v[0]))
        elif name == 'GoToIf':
            a.op('GOTOIF', v[0], self.L(v[1]))
        elif name == 'CallIf':
            a.op('CALLIF', v[0], self.L(v[1]))
        elif name == 'CompareVar':
            a.op('COMPAREVARTOVAR' if v[1] >= 0x8000 else 'COMPAREVARTOVALUE', fvar(v[0]), fvar(v[1]))
        elif name == 'SetVar':
            value = v[1]
            if v[0] in self.local_vars and value < 0x8000 and self.host is not None:
                f = self.host['objects'].get(value)
                value = LOCALID_PLAYER if f == 'player' else (f if f is not None else value)
                self.note(name, 'a local id into a var: the room\'s object id')
            a.op('SETVARFROMVAR' if value >= 0x8000 else 'SETVARFROMVALUE', fvar(v[0]), fvar(value))
            if self.picture and v[0] in self.const_looks and value < 0x8000:    # (plat-frontier-rooms) a look by number
                for n in self.look_slots[v[0]]:
                    a.op('SETVARFROMVALUE', GFX_VAR_FIRST + n, value)
                self.note(name, 'a look by its number: into the look slots of the people drawn from that var')
        elif name in ('AddVar', 'SubVar'):
            a.op(name.upper(), fvar(v[0]), fvar(v[1]))
        elif name == 'WaitTime':
            a.op('WAITTIME', v[0], fvar(v[1]))
        elif name in ('Message', 'MessageInstant'):
            assert v[0] < 256, (name, v)
            a.op('MESSAGE' if name == 'Message' else 'MESSAGEINSTANT', v[0])
        elif name == 'MessageNoSkip':
            a.op('MESSAGENOSKIP', fvar(v[0]))
        elif name == 'FadeScreen':
            a.op('FADESCREEN', *v)
        elif name == 'InitGlobalTextListMenu':
            a.op('INITGLOBALTEXTLISTMENU', v[0], v[1], v[2], v[3], fvar(v[4]))
        elif name == 'InitLocalTextListMenu':
            a.op('INITLOCALTEXTLISTMENU', v[0], v[1], v[2], v[3], fvar(v[4]))
        elif name == 'AddListMenuEntry':
            a.op('ADDLISTMENUENTRY', v[0], v[1], v[2])
        elif name == 'ShowYesNoMenu':
            a.op('SHOWYESNOMENU', fvar(v[0]))
            if v[1]:
                self.note(name, 'Platinum\'s cursor starts on No here; Black 2\'s yes/no menu starts on Yes (an approximation)')
        elif name == 'PlaySoundEffect':
            a.op('PLAYSE', v[0])
        elif name == 'WaitSoundEffect':
            a.op('WAITSE', v[0])
        elif name == 'PlayFanfare':
            a.op('PLAYFANFARE', v[0])
        elif name == 'BufferNumber':
            a.op('BUFFERNUMBER', v[0], fvar(v[1]))
        elif name == 'BufferPlayerName':
            a.op('BUFFERPLAYERNAME', v[0])
        elif name == 'BufferRivalName':
            a.op('BUFFERRIVALNAME', v[0])
        elif name == 'GetRandom':
            a.op('GETRANDOM', fvar(v[0]), fvar(v[1]))
        elif name == 'SetSystemVar':
            a.op('SETVARFROMVAR' if v[1] >= 0x8000 else 'SETVARFROMVALUE', v[0], fvar(v[1]))
        elif name == 'GetSystemVar':
            a.op('SETVARFROMVAR', fvar(v[1]), v[0])
        elif name == 'IncrementRecordValue':
            a.op('INCREMENTGAMERECORD', v[0])
        elif name == 'CallBattleTowerFunction':
            a.op('CALLBATTLETOWERFUNCTION', v[0], fvar(v[1]), fvar(v[2]))
        elif name == 'BattleTower_StartBattle':
            a.op('CALLBATTLETOWERFUNCTION', 42, 0, 0)          # BT_FUNC_UNK_42: the field's battle (the same DTO)
        elif name == 'BattleTower_CheckWonBattle':
            a.op('CHECKWONBATTLE', fvar(v[0]))
        elif name == 'FrontierScrCmd_85':                       # the opponent's line before the battle
            a.op('PRINTBATTLETOWERINTROMESSAGE', v[0])
        elif name in ('FrontierScrCmd_72', 'FrontierScrCmd_73'):   # the save: SaveData_Save / the save in steps
            a.op('TRYSAVEGAME', fvar(v[0]))
        elif name in ('FrontierScrCmd_70', 'FrontierScrCmd_71'):   # a battle video saved? the battle recorded? no
            a.op('SETVARFROMVALUE', fvar(v[0]), 0)
            self.note(name, 'the Vs. Recorder: none (0)')
        elif name == 'FrontierScrCmd_6D':                       # save the battle video: never reached (no question)
            a.op('SETVARFROMVALUE', fvar(v[3]), 0)
            self.note(name, 'the Vs. Recorder: not saved')
        elif name == 'ApplyMovement':
            self.movs.setdefault(v[1], f'M{v[1]:04X}')
            local = self.local(v[0])
            if local is None:
                self.note(name, f'object {v[0]} has no person in the room: not moved')
                return
            a.op('APPLYMOVEMENT', local, self.movs[v[1]])
        elif name == 'FrontierScrCmd_24':
            self.place(v[0])
        elif name == 'FrontierScrCmd_25':                       # an object removed
            local = self.local(v[0])
            if local is not None:
                a.op('HIDEOBJECT', local)
        elif name == 'FrontierScrCmd_26':                       # an object drawn or not
            local = self.local(v[0])
            if local is not None:
                a.op('SHOWOBJECT' if v[1] else 'HIDEOBJECT', local)
        elif name in ('FrontierScrCmd_31', 'FrontierScrCmd_33', 'FrontierScrCmd_2D'):
            self.door(name, v)
        elif name == 'ChangeScript':
            a.op('LAUNCHBATTLEFRONTIERSCENE', (MARK_CHANGE if v[1] == 0 else MARK_CHANGE1) + v[0])
            a.op('END')
        elif name == 'ChangeSceneWithinScript':
            a.op('LAUNCHBATTLEFRONTIERSCENE', MARK_WITHIN + v[0])
        elif name == 'ExitFrontier':
            a.op('LAUNCHBATTLEFRONTIERSCENE', MARK_EXIT)
            a.op('END')
        elif self.picture and self.picture_command(x, name, v):     # (plat-frontier-rooms)
            return
        else:
            self.note(name, 'not translated yet (a facility\'s command: its piece)')
            a.op('NOOP') if 'NOOP' in field_ops() else None
            return

    # ---- plat-frontier-rooms (2026-11-07): the facilities' scenes in their picture rooms (HOSTS 'picture')
    def _looks(self):
        """The vars the file's people take their look from: look_slots {var: [VAR_OBJ_GFX_ID slots]}; player_looks: set by
        GetPlayerObjEventGfx (Platinum's player look: 0 or 97, Black 2's 231 or 240 through pearl_story's dynamic sprite
        rule); const_looks: set only by SetVar to a number (an attendant's look: Platinum's gfx numbers, which pearl_story
        turns into Black 2 codes in a look slot). The rest (the opponents') a facility command fills with Black 2 codes (the
        C ops: PearlB2_TowerObjCode): copied when the person appears, as the Tower's."""
        h, d = self.host, self.d
        self.look_slots = {}
        for kind, end, rows in d.data_blocks.values():
            if kind != 'objects':
                continue
            for local, gfx, di, x, y, vis, c, net in rows:
                if gfx >= 0x8000 and local in h['dynamic']:
                    self.look_slots.setdefault(gfx, [])
                    if h['dynamic'][local] not in self.look_slots[gfx]:
                        self.look_slots[gfx].append(h['dynamic'][local])
        sets = {}
        for e, op, v in d.insns.values():
            n = d.name(op)
            if n == 'GetPlayerObjEventGfx':
                sets.setdefault(v[0], set()).add('player')
            elif n == 'SetVar':
                sets.setdefault(v[0], set()).add('const' if v[1] < 0x8000 else 'var')
            elif n.startswith('Call') and n.endswith('Function') and len(v) == 4:
                sets.setdefault(v[3], set()).add('function')
        self.player_looks = {var for var in self.look_slots if sets.get(var) == {'player'}}
        self.const_looks = {var for var in self.look_slots if sets.get(var) == {'const'}}

    PICTURE_WIRELESS = {'BufferPartnerName', 'FrontierScrCmd_94', 'FrontierScrCmd_C9'}
    PICTURE_EFFECTS = {
        'InitParticleSystem': 'the particles (spotlights, confetti, sparks): Black 2 has no field form of them',
        'CreateParticleSystemEmitter': 'the particles: no field form',
        'WaitForParticleSystemEmitters': 'the particles: no field form',
        'FreeParticleSystem': 'the particles: no field form',
        'FrontierScrCmd_4C': 'the picture shakes (an offset of its layers): no field form',
        'FrontierScrCmd_4D': 'waits for the shake: none',
        'FrontierScrCmd_45': 'the Hall\'s big screen shows the player\'s Pokemon (a sprite over the picture): no field form',
        'FrontierScrCmd_46': 'the big screen\'s sprite goes: nothing',
        'FrontierScrCmd_4E': 'the Hall\'s lights (the lights layer\'s colour cycle on the picture): no field form',
        'FrontierScrCmd_C7': 'a TV segment about the Hall (TV segments are dropped, as Pearl\'s are)',
        'StopSoundEffect': 'a sound effect stops: Black 2\'s stop on its own (approximation)',
    }
    FIELD_SAME = {'BufferSpeciesName': 'BUFFERSPECIESNAMEFROMVAR', 'BufferMoveName': 'BUFFERMOVENAME',
                  'BufferItemName': 'BUFFERITEMNAME', 'GiveBattlePoints': 'GIVEBATTLEPOINTS'}

    def picture_command(self, x, name, v):
        """A command of a facility's scene in a picture room: True when handled. Field commands where Platinum's field has one;
        the wireless Multi's (closed) nothing; the picture effects nothing (noted); the facility's own commands as they are,
        on a carrier opcode (CARRIER_BASE + the frontier opcode, its arguments as the frontier's) that pearl_story's block
        "plat-frontier-rooms" turns into the facility's Frontier ops."""
        a = self.asm
        if name in self.FIELD_SAME:
            op = self.FIELD_SAME[name]
            types = field_ops()[op][1]
            a.op(op, *[fvar(val) if t == 'var' else val for t, val in zip(types, list(v) + [0] * (len(types) - len(v)))])
            return True
        if name == 'IncrementTrainerScore':
            a.op('INCREMENTTRAINERSCORE2', v[0])
            return True
        if name == 'GetPlayerObjEventGfx':
            self.player_look(x, v[0])
            return True
        if name in self.PICTURE_WIRELESS or name.endswith('_WaitForCommResponses'):
            self.note(name, 'wireless Multi only (closed): nothing')
            return True
        if name.endswith('_SendCommMessage'):
            a.op('SETVARFROMVALUE', fvar(v[-1]), 1)          # (sent: the closed Multi's send loops end)
            self.note(name, 'wireless Multi only (closed): its result var 1 (sent)')
            return True
        if name in self.PICTURE_EFFECTS:
            self.note(name, 'dropped: ' + self.PICTURE_EFFECTS[name])
            return True
        op = fs.load_table()
        code = next(k for k, row in op.items() if row['name'] == name)
        args = [('u8' if t == 'u8' else 'var', fvar(val) if t != 'u8' else val) for (t, _), val in zip(op[code]['args'], v)]
        a.raw(CARRIER_BASE + code, args)
        self.note(name, 'the facility\'s command, carried to pearl_story (block "plat-frontier-rooms")')
        return True

    def player_look(self, x, var):
        """GetPlayerObjEventGfx var: the player's look, Platinum's numbers (0 Lucas, 97 Dawn: pearl_events PLAYER_SPRITES),
        into the var and into the look slots of the people drawn from it (pearl_story makes those Black 2's 231 or 240)."""
        a = self.asm
        dawn, done = f'G{x:04X}_dawn', f'G{x:04X}_done'
        a.op('GETPLAYERGENDER', fvar(var))
        a.op('COMPAREVARTOVALUE', fvar(var), 0)
        a.op('GOTOIF', 5, dawn)                     # (not equal: the girl)
        for target in [fvar(var)] + [GFX_VAR_FIRST + n for n in self.look_slots.get(var, ())]:
            a.op('SETVARFROMVALUE', target, 0)
        a.op('GOTO', done)
        a.label(dawn)
        for target in [fvar(var)] + [GFX_VAR_FIRST + n for n in self.look_slots.get(var, ())]:
            a.op('SETVARFROMVALUE', target, 97)
        a.label(done)
        self.note('GetPlayerObjEventGfx', 'the player\'s look by the player\'s gender, into the look slots')
    # ---- end plat-frontier-rooms

    def local(self, v):
        """The room's object for a scene's local id (a var: the scene's two-way local ids by mode, 0x8001-0x8003)."""
        if self.host is None:
            return None
        if v >= 0x8000:
            return fvar(v)             # (a var holding a local id: the multi rooms; their ids map 1:1 to the room's: HOSTS)
        f = self.host['objects'].get(v)
        return LOCALID_PLAYER if f == 'player' else f

    def place(self, table):
        """FrontierScrCmd_24's rows: each object onto its tile of the room, drawn or not, facing its way."""
        a, h = self.asm, self.host
        kind, end, rows = self.d.data_blocks[table]
        if h is None:
            self.note('FrontierScrCmd_24', 'no room yet: objects not placed')
            return
        ox, oy = h['origin']
        doorway = {(dx, dz) for dx, dz in h['doors'].values()} | {(dx, dz - 1) for dx, dz in h['doors'].values()}
        for local, gfx, d, x, y, visible, c, net in rows:
            f = h['objects'].get(local)
            if f is None:
                self.note('FrontierScrCmd_24', f'object {local}: no person in the room')
                continue
            tx, tz = (x + ox) // 16, (y + oy) // 16
            if visible and (tx, tz) in doorway:
                # Platinum's door sprite is drawn over whoever stands in the doorway until their WarpIn; the room's door is
                # part of the map and covers no one, so they wait hidden there
                visible = 0
                self.note('FrontierScrCmd_24', 'a person in the doorway waits hidden for their WarpIn (the door covers them '
                                               'in Platinum\'s picture)')
            if f == 'player':
                if not visible:
                    a.op('HIDEOBJECT', LOCALID_PLAYER)
                continue                      # (the warp puts the player in the room: HOSTS arrive)
            self.gfx_var(local, gfx)
            if self.picture and f in h['dynamic']:
                # (plat-test, 2026-11-08) Black 2 takes a person's VAR_OBJ_GFX_ID look when it makes them (the zone's load,
                # ov012 GetWKOBJCODENPCOBJCODE): a look the scene sets in the room (the Arcade corridor's 0x4020-0x4022,
                # 0 at the warp: its attendant and the player's stand-in walked unseen) reaches only a person made after
                # it, so the person is made again here, as Platinum makes the scene's objects at this command
                a.op('REMOVEOBJECT', f)
                a.op('ADDOBJECT', f)
            if visible and f in h['flags']:
                a.op('CLEARFLAG', h['flags'][f])
                a.op('ADDOBJECT', f)
            a.op('SETPOSITION', f, tx, 0, tz, d)
            a.op('SHOWOBJECT' if visible else 'HIDEOBJECT', f)

    def door(self, name, v):
        a, h = self.asm, self.host
        slot = v[0]
        if h is None or slot not in h['doors']:
            self.note(name, 'no door in the room')
            return
        tag = DOOR_TAG[sorted(h['doors']).index(slot)]
        dx, dz = h['doors'][slot]
        if name == 'FrontierScrCmd_31':
            if v[1] == 0 and not getattr(self, f'_door{slot}', False):     # anim 0: the door opens
                setattr(self, f'_door{slot}', True)
                a.op('LOADDOORANIMATION', 0, 0, dx, dz, tag)
                a.op('PLAYDOOROPENANIMATION', tag)
            else:
                self.note(name, 'a door sprite\'s other animation: nothing')
        elif name == 'FrontierScrCmd_33':
            a.op('WAITFORANIMATION', tag)
        else:                                  # FrontierScrCmd_2D: the open door sprite goes (the screen is black)
            a.op('PLAYDOORCLOSEANIMATION', tag)
            a.op('WAITFORANIMATION', tag)
            a.op('UNLOADANIMATION', tag)


_SYNTH = {}


def synthesize(index):
    """(field-script bytes, {frontier address: field address}, notes) of frontier script file `index`."""
    if index not in _SYNTH:
        s = Synth(index)
        data, addr = s.build()
        _SYNTH[index] = (data, addr, s.notes)
    return _SYNTH[index]


def slot(index):
    return FILE_BASE + index


def bank_slot(scene):
    """The scene's text bank as the tools number banks (Platinum's bank -> Pearl's slot: data/platinum/id_map.json)."""
    import version
    return version.of_slot('banks')[scenes()[scene]['bank']]


def report():
    names = fs.source_order()
    usage = fs.usage()
    total = Counter()
    for i, name in enumerate(names):
        if name.endswith('.bin'):
            continue
        data, addr, notes = synthesize(i)
        sc = [s['name'] for k, s in scenes().items() if s['script'] == i]
        hosted = [n for n in sc if n in HOSTS]
        print(f'{name}: {len(data)} bytes as a field script; scenes {", ".join(sc) or "none"}; '
              f'hosted: {", ".join(hosted) or "none (no room yet)"}')
        for (cmd, what), n in sorted(notes.items()):
            print(f'    {cmd} x{n}: {what}')
            total[what.split(':')[0]] += n
    print(f'{len(usage)} commands used in the dump\'s scripts; notes by kind: {dict(total)}')
    return 0


def scene_lines(name):
    k = scene_id(name)
    data, addr, notes = synthesize(scenes()[k]['script'])
    return [f'{name}: script {scenes()[k]["script"]}, {len(data)} bytes, host {HOSTS.get(name, {}).get("zone")}'] + \
        [f'  {c} x{n}: {w}' for (c, w), n in sorted(notes.items())]


if __name__ == '__main__':
    if sys.argv[1:2] == ['report']:
        sys.exit(report())
    print(__doc__)
