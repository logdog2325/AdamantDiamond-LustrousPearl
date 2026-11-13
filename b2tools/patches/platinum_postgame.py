"""Two of Platinum's post-game script commands that Black 2 has none for (plat-ch12, 2026-11-07; notes/PLATINUM_CHAPTERS.md
chapter 12). Both are PearlB2 extension sub-commands (notes/EXT_COMMAND.md: the leftovers row, under platinum_regigigas's 0xBF):

- 0xBE, value-or-var species, value-or-var level: Platinum's StartFatefulEncounter (pokeplatinum scrcmd.c, encounter.c
  Encounter_NewFatefulVsSpeciesAtLevel: a wild battle whose Pokémon has MON_DATA_FATEFUL_ENCOUNTER set). Flower Paradise's
  Shaymin (the deliveryman's Oak's Letter). Black 2's own static wild battle (ov036 s0174 CallWildBattle: species, level,
  flags 0, as pearl_story's StartLegendaryBattle), with Black 2's fateful-encounter mark (PKM_PARAM_FATEFUL_ENCOUNTER 0x6d)
  set on the wild Pokémon before the battle: Black 2 keeps that Pokémon when it is caught (ov166 event_battle_return.c takes
  setup->party[1]'s, and its met data leaves the mark alone), so the caught Shaymin has it. Floaroma's Gracidea needs it
  (pl_FindPartySlotWithFatefulEncounterSpecies, plat-ch3). The event's work is ov012 event_battle.c EventWildBattleCallWork
  (gsys, setup, ...): the setup is its second word.
- 0xBD, var: Platinum's GetRotomFormsInSave (pokeplatinum scrcmd.c SaveData_GetRotomFormsInSave): a bit for each form some
  Rotom has (bit n = form n), not an Egg, in the party, the Day Care and every box. Rotom's Room shows the appliance of each
  form nobody has (pearl_story.inc pl_GetRotomFormsInSave spreads the bits into Platinum's five vars).

How the commands reach the code: sExtModules (decomp src/pearlb2/resident/ext_cmd.c) row 5, the leftovers module, points at
the wrapper platinum_regigigas wrote; this patch puts its own wrapper there, which runs 0xBE and 0xBD and hands every other
sub-command to the one it replaced. Compiled with clang into the resident pool, calls by address only (as
platinum_regigigas).

Platinum only: a Pearl or Diamond build doesn't run it (their scripts never use 0xBD or 0xBE). List it after
platinum_regigigas.
"""
import os, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import decomp, itcm, resident, version  # noqa: E402

SUB_FATEFUL, SUB_ROTOM = 0x1E, 0x1D         # the leftovers row's sub-commands (0xBE, 0xBD in a script)
LEFTOVERS_ROW = 5                           # sExtModules[0xA0 >> 5]
# (all Thumb: config/b2_us/arm9/symbols.txt and the overlays')
CALLS = ('ScriptReadAny', 'ScriptReadVar', 'FieldScriptEnv_GetScriptWork', 'FieldScriptEnv_GetGameSystem',
         'FieldScriptEnv_GetGameData', 'GSYS_GetField', 'Field_GetEncountSystem', 'EventWildBattleCall_CreateStatic',
         'GameEvent_GetData', 'BtlSetup_GetParty', 'PokeParty_GetPkm', 'PokeParty_SetParam', 'PokeParty_GetParam',
         'ScriptWork_CallEvent', 'GameData_GetParty', 'PokeParty_GetPkmCount', 'GameData_GetSaveControl',
         'getDaycareBlockAddress', 'DayCareSave_GetPkmStatus', 'DayCareSave_GetPkm', 'GameData_GetBoxSaveAccessor',
         'BoxSaveAccessor_GetPkmParam')

C = """
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef u16 (*read_any_fn)(void *, void *);
typedef u16 *(*read_var_fn)(void *, void *);
typedef void *(*get_fn)(void *);
typedef void *(*static_fn)(void *, u32, u32, u32, u32);
typedef void *(*index_fn)(void *, u32);
typedef void (*set_param_fn)(void *, u32, u32);
typedef u32 (*get_param_fn)(void *, u32, void *);
typedef void (*call_event_fn)(void *, void *);
typedef u32 (*count_fn)(void *);
typedef u32 (*status_fn)(void *, u32);
typedef u32 (*box_param_fn)(void *, u32, u32, u32, void *);
typedef int (*ext_fn)(void *, void *, u32);

#define PKM_PARAM_SPECIES 0x5
#define PKM_PARAM_IS_EGG 0x4c
#define PKM_PARAM_FATEFUL_ENCOUNTER 0x6d
#define PKM_PARAM_FORM 0x6f
#define SPECIES_ROTOM 479
#define ROTOM_FORMS 6
#define DAY_CARE_SLOTS 2
#define BOX_MAX_TRAY 24
#define BOX_MAX_POS 30

static u32 RotomBit(u32 species, u32 isEgg, u32 form) {
    return (species == SPECIES_ROTOM && !isEgg && form < ROTOM_FORMS) ? (1u << form) : 0;
}

static u32 PartyRotomBit(void *pkm) {
    if (((get_param_fn)%(PokeParty_GetParam)#x)(pkm, PKM_PARAM_SPECIES, 0) != SPECIES_ROTOM) {
        return 0;
    }
    return RotomBit(SPECIES_ROTOM, ((get_param_fn)%(PokeParty_GetParam)#x)(pkm, PKM_PARAM_IS_EGG, 0),
                    ((get_param_fn)%(PokeParty_GetParam)#x)(pkm, PKM_PARAM_FORM, 0));
}

int PlatinumExtPostgame(void *vm, void *env, u32 sub) {
    if (sub == %(fateful)d) {
        u16 species = ((read_any_fn)%(ScriptReadAny)#x)(vm, env);
        u16 level = ((read_any_fn)%(ScriptReadAny)#x)(vm, env);
        void *work = ((get_fn)%(FieldScriptEnv_GetScriptWork)#x)(env);
        void *field = ((get_fn)%(GSYS_GetField)#x)(((get_fn)%(FieldScriptEnv_GetGameSystem)#x)(env));
        void *event = ((static_fn)%(EventWildBattleCall_CreateStatic)#x)(((get_fn)%(Field_GetEncountSystem)#x)(field),
                                                                        species, level & 0xff, 0, 0);
        void *setup = ((void **)((get_fn)%(GameEvent_GetData)#x)(event))[1];
        void *wild = ((index_fn)%(PokeParty_GetPkm)#x)(((index_fn)%(BtlSetup_GetParty)#x)(setup, 1), 0);
        ((set_param_fn)%(PokeParty_SetParam)#x)(wild, PKM_PARAM_FATEFUL_ENCOUNTER, 1);
        ((call_event_fn)%(ScriptWork_CallEvent)#x)(work, event);
        return 1;
    }
    if (sub == %(rotom)d) {
        u16 *result = ((read_var_fn)%(ScriptReadVar)#x)(vm, env);
        void *gameData = ((get_fn)%(FieldScriptEnv_GetGameData)#x)(env);
        void *party = ((get_fn)%(GameData_GetParty)#x)(gameData);
        void *dayCare = ((get_fn)%(getDaycareBlockAddress)#x)(((get_fn)%(GameData_GetSaveControl)#x)(gameData));
        void *boxes = ((get_fn)%(GameData_GetBoxSaveAccessor)#x)(gameData);
        u32 count = ((count_fn)%(PokeParty_GetPkmCount)#x)(party);
        u32 mask = 0, i, box;

        for (i = 0; i < count; i++) {
            mask |= PartyRotomBit(((index_fn)%(PokeParty_GetPkm)#x)(party, i));
        }
        for (i = 0; i < DAY_CARE_SLOTS; i++) {
            if (((status_fn)%(DayCareSave_GetPkmStatus)#x)(dayCare, i)) {
                mask |= PartyRotomBit(((index_fn)%(DayCareSave_GetPkm)#x)(dayCare, i));
            }
        }
        for (box = 0; box < BOX_MAX_TRAY; box++) {
            for (i = 0; i < BOX_MAX_POS; i++) {
                if (((box_param_fn)%(BoxSaveAccessor_GetPkmParam)#x)(boxes, box, i, PKM_PARAM_SPECIES, 0) == SPECIES_ROTOM) {
                    mask |= RotomBit(SPECIES_ROTOM,
                                     ((box_param_fn)%(BoxSaveAccessor_GetPkmParam)#x)(boxes, box, i, PKM_PARAM_IS_EGG, 0),
                                     ((box_param_fn)%(BoxSaveAccessor_GetPkmParam)#x)(boxes, box, i, PKM_PARAM_FORM, 0));
                }
            }
        }
        *result = mask;
        return 0;
    }
    return ((ext_fn)%(old)#x)(vm, env, sub);
}
"""


def source(code, old):
    """The wrapper's C, with every Black 2 function at its address (Thumb bit set) and the replaced row handler `old`."""
    sym = {n: decomp.symbol(n, code) for n in CALLS}
    missing = [n for n, a in sym.items() if a is None]
    assert not missing, f'platinum_postgame: not in this decomp: {missing}'
    return C % dict({n: a | 1 for n, a in sym.items()}, old=old | 1, fateful=SUB_FATEFUL, rotom=SUB_ROTOM)


def apply_code(code):
    assert version.PLATINUM, 'platinum_postgame: a Platinum build only'
    table = decomp.symbol('sExtModules', code)
    assert table is not None, 'platinum_postgame: the decomp has no sExtModules'
    row = table + 4 * LEFTOVERS_ROW
    old, = struct.unpack('<I', resident.read(code, row, 4))
    orig = decomp.symbol('PearlB2_Ext_Leftovers', code) | 1
    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, 'postgame.c')
        open(src, 'w').write(source(code, old))
        base, end, sym = resident.install(code, lambda b: itcm.build(src, b, t))
    assert old == orig or (old & ~1) < base, f'sExtModules[{LEFTOVERS_ROW}] = {old:#x}: not the leftovers handler or a wrapper'
    resident.write(code, row, struct.pack('<I', sym['PlatinumExtPostgame'] | 1))
    return (f'platinum_postgame: extension 0xBE (a fateful wild battle: Flower Paradise\'s Shaymin) and 0xBD (the Rotom forms '
            f'in the save) ({base:#x}-{end:#x}, {end - base} B; sExtModules[{LEFTOVERS_ROW}] {old:#x} -> the wrapper)')


if __name__ == '__main__':
    # offline: compile and link the wrapper against the decomp's last link map (no build dir needed)
    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, 'postgame.c')
        orig = decomp.symbol('PearlB2_Ext_Leftovers')
        assert orig is not None, 'no decomp link map'
        open(src, 'w').write(source(None, orig))
        blob, sym = itcm.build(src, 0x02300000, t)
        print(f'platinum_postgame: {len(blob)} B, symbols {sorted(sym)}')
