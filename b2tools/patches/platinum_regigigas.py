"""Platinum's deliveryman gives an event Regigigas (the user, 2026-11-03; 2026-11-07, plat-story; notes/PLATINUM_CHAPTERS.md).

Platinum's Regi ruins wake only with a fateful-encounter Regigigas in the party (CheckPartyHasFatefulEncounterRegigigas,
pearl_story.inc pl_CheckPartyHasFatefulEncounterRegigigas), and only an event gave one. The deliveryman's fifth gift
(pearl_story.inc pl_DeliveryGive, PVAR_DELIVERY 4) runs PearlB2's extension command 0xBF (notes/EXT_COMMAND.md: the
leftovers row's last sub-command, kept for this). Black 2's script commands can't mark a Pokémon fateful or set its OT, so this
patch makes it the way Black 2 makes a Mystery Gift Pokémon: a gift card (MysteryGiftPokemon, decomp include/save/mystery_gift.h)
handed to CreateMysteryGiftPokemon (ov012), which sets the fateful mark and the met data (setFatefulEncounterPkmData).

The card is the real 2009 event's, the North American one (Toys "R" Us, 8-21 March 2009, for Diamond and Pearl, to unlock
Platinum's Regis): Lv 100, OT TRU, ID 03089, holding a Custap Berry, in a Cherish Ball, Slow Start, Iron Head, Rock Slide, Icy
Wind and Crush Grip, met at "Pokémon Event" (Black 2's place 40059) at Lv 100; nature, IVs and shininess at random as the
event's; the date it is received, as a received card's; its game Platinum (version.MET_GAME), where it was received.

How the command reaches it: sExtModules (decomp src/pearlb2/resident/ext_cmd.c) row 5, the leftovers module, points at a
wrapper here that runs sub-command 0x1F and hands every other to PearlB2_Ext_Leftovers. Script: pl_ext 0xBF, var (1 = given,
0 = no room in the party or no Pokémon made).

Platinum only: a Pearl or Diamond build doesn't run it (their scripts never use 0xBF). List it after platinum_hidden_items.
"""
import os, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import decomp, itcm, resident, version  # noqa: E402

SUB = 0x1F                                  # the leftovers row's sub-command (0xBF in a script)
LEFTOVERS_ROW = 5                           # sExtModules[0xA0 >> 5]
SPECIES, LEVEL = 486, 100                   # Regigigas
MOVES = (442, 157, 196, 462)                # Iron Head, Rock Slide, Icy Wind, Crush Grip
CUSTAP_BERRY, CHERISH_BALL = 210, 16
OT_NAME, OT_ID = 'TRU', 3089                # the event's OT and ID (SID 0)
PLACE_POKEMON_EVENT = 40059                 # Black 2's event places from 40001: bank 0x6e line 58, "Pokémon Event"
GIFT_SIZE, DATE_AT, KIND_AT = 0xCC, 0xAC, 0xB3
# (all Thumb: config/b2_us/arm9/symbols.txt and ov012's)
CALLS = ('ScriptReadVar', 'FieldScriptEnv_GetGameData', 'FieldScriptEnv_GetHeapID', 'GameData_GetParty', 'PokeParty_GetCapacity',
         'PokeParty_GetPkmCount', 'RTC_GetCachedDate', 'CreateMysteryGiftPokemon', 'PokeParty_AddPkm', 'GameData_GetPokedex',
         'addPkmToDex', 'GFL_HeapFree', 'PearlB2_Ext_Leftovers')

C = """
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u32 year, month, day, week; } RTCDate;
typedef u16 *(*read_var_fn)(void *, void *);
typedef void *(*get_fn)(void *);
typedef u32 (*count_fn)(void *);
typedef u16 (*heap_fn)(void *);
typedef void (*date_fn)(RTCDate *);
typedef void *(*create_fn)(const void *, u32, void *);
typedef int (*add_fn)(void *, void *);
typedef void (*dex_fn)(void *, void *);
typedef void (*free_fn)(void *);
typedef int (*ext_fn)(void *, void *, u32);

static const u32 kGift[%(words)d] = { %(gift)s };

int PlatinumExtLeftovers(void *vm, void *env, u32 sub) {
    u32 gift[%(words)d];
    RTCDate date;
    u16 *result;
    void *gameData, *party, *pkm;
    u32 heap, i;

    if (sub != %(sub)d) {
        return ((ext_fn)%(PearlB2_Ext_Leftovers)#x)(vm, env, sub);
    }
    result = ((read_var_fn)%(ScriptReadVar)#x)(vm, env);
    gameData = ((get_fn)%(FieldScriptEnv_GetGameData)#x)(env);
    heap = ((heap_fn)%(FieldScriptEnv_GetHeapID)#x)(env);
    party = ((get_fn)%(GameData_GetParty)#x)(gameData);
    *result = 0;
    if (((count_fn)%(PokeParty_GetCapacity)#x)(party) <= ((count_fn)%(PokeParty_GetPkmCount)#x)(party)) {
        return 0;
    }
    for (i = 0; i < %(words)d; i++) {
        gift[i] = kGift[i];
    }
    ((date_fn)%(RTC_GetCachedDate)#x)(&date);
    gift[%(date_word)d] = ((2000 + date.year) << 16) | (date.month << 8) | date.day;
    pkm = ((create_fn)%(CreateMysteryGiftPokemon)#x)(gift, heap, gameData);
    if (pkm == 0) {
        return 0;
    }
    ((add_fn)%(PokeParty_AddPkm)#x)(party, pkm);
    ((dex_fn)%(addPkmToDex)#x)(((get_fn)%(GameData_GetPokedex)#x)(gameData), pkm);
    ((free_fn)%(GFL_HeapFree)#x)(pkm);
    *result = 1;
    return 0;
}
"""


def gift_card():
    """The 0xCC-byte card (MysteryGift with its MysteryGiftPokemon at the start), the date left 0 (the C writes it)."""
    g = bytearray(GIFT_SIZE)
    struct.pack_into('<IIIHHH4HHBB', g, 0, OT_ID, version.MET_GAME, 0, 0, CHERISH_BALL, CUSTAP_BERRY, *MOVES, SPECIES, 0, 0)
    struct.pack_into('<11H', g, 0x1E, 0xFFFF, *([0] * 10))       # no nickname: the species' name (the terminator first)
    struct.pack_into('<BBBB', g, 0x34, 0xFF, 0xFF, 0, 0)          # nature, gender at random; ability slot 0; shiny: any
    struct.pack_into('<HHB', g, 0x38, 0, PLACE_POKEMON_EVENT, LEVEL)   # egg place, met place, met level
    g[0x43:0x49] = b'\xff' * 6                                    # IVs at random
    name = [ord(c) for c in OT_NAME] + [0xFFFF] + [0] * (7 - len(OT_NAME))
    struct.pack_into('<8H', g, 0x4A, *name)
    struct.pack_into('<BBB', g, 0x5A, 0, LEVEL, 0)                # OT male, Lv 100, not an Egg
    g[KIND_AT] = 1                                                # a Pokémon gift
    return bytes(g)


def source(code):
    sym = {n: decomp.symbol(n, code) for n in CALLS}
    missing = [n for n, a in sym.items() if a is None]
    assert not missing, f'platinum_regigigas: not in this decomp: {missing}'
    words = struct.unpack(f'<{GIFT_SIZE // 4}I', gift_card())
    return C % dict({n: a | 1 for n, a in sym.items()}, words=len(words), sub=SUB, date_word=DATE_AT // 4,
                    gift=', '.join(f'{w:#x}' for w in words))


def apply_code(code):
    assert version.PLATINUM, 'platinum_regigigas: a Platinum build only'
    table = decomp.symbol('sExtModules', code)
    assert table is not None, 'platinum_regigigas: the decomp has no sExtModules'
    row = table + 4 * LEFTOVERS_ROW
    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, 'regigigas.c')
        open(src, 'w').write(source(code))
        base, end, sym = resident.install(code, lambda b: itcm.build(src, b, t))
    old, = struct.unpack('<I', resident.read(code, row, 4))
    orig = decomp.symbol('PearlB2_Ext_Leftovers', code) | 1
    assert old == orig or (old & ~1) < base, f'sExtModules[{LEFTOVERS_ROW}] = {old:#x}: not the leftovers handler'
    resident.write(code, row, struct.pack('<I', sym['PlatinumExtLeftovers'] | 1))
    return (f'platinum_regigigas: extension 0xBF gives the event Regigigas (Lv {LEVEL}, OT {OT_NAME} {OT_ID:05d}, fateful) '
            f'({base:#x}-{end:#x}; sExtModules[{LEFTOVERS_ROW}] {old:#x} -> the wrapper)')
