"""Platinum's Trainers past Black 2's 813 (the user, 2026-11-02: the defeat flags move, no Trainer is cut; notes/PORT_AUDIT.md "Trainers").

Black 2's defeat flag is id + 1520 (ov012 trainer_script.c TrainerFlagGet, setTrainerBattleFlag, clearTrainerBattleFlag, all that touch them),
which past 813 lands on flags in use. Platinum's ids 814 on take flags 2561 on instead (pearl_ids.EXTENDED_TRAINER_FLAGS: free in Black 2's
survey, kept out of Platinum's free list). The three functions jump to the same three in ITCM. Id 813 and below are as Black 2's.

Platinum only: list it after the other patches that append to ITCM. A Pearl or Diamond build doesn't run it, so their code is unchanged.
"""
import os, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import decomp, itcm, pearl_ids, version  # noqa: E402

C = """
typedef unsigned short u16;
typedef int (*get_fn)(void *, u16);
typedef void (*set_fn)(void *, u16);
static u16 flag_of(u16 id) { return id > %(last)d ? %(first)d + id - %(last)d - 1 : id + 0x5f0; }
int PlatinumTrainerFlagGet(void *w, u16 id) { return ((get_fn)%(get)#x)(w, flag_of(id)); }
void PlatinumTrainerFlagSet(void *w, u16 id) { ((set_fn)%(set)#x)(w, flag_of(id)); }
void PlatinumTrainerFlagClear(void *w, u16 id) { ((set_fn)%(reset)#x)(w, flag_of(id)); }
"""


def apply_code(code):
    assert version.PLATINUM, 'platinum_trainer_flags: a Platinum build only'
    ov12 = os.path.join(code, 'arm9_ov012.bin')
    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, 'flags.c')
        open(src, 'w').write(C % dict(last=pearl_ids.LAST_B2_TRAINER, first=pearl_ids.EXTENDED_TRAINER_FLAGS,
                                      get=decomp.symbol('EventWork_FlagGet') | 1, set=decomp.symbol('EventWork_FlagSet') | 1,
                                      reset=decomp.symbol('EventWork_FlagReset') | 1))
        base, end, sym = itcm.install(code, lambda b: itcm.build(src, b, t))
    d = bytearray(open(ov12, 'rb').read())
    start = 0x021503C0                  # overlay 12 (pokebw2 config/b2_us/arm9/overlays.yaml)
    for name, target in (('TrainerFlagGet', 'PlatinumTrainerFlagGet'), ('setTrainerBattleFlag', 'PlatinumTrainerFlagSet'),
                         ('clearTrainerBattleFlag', 'PlatinumTrainerFlagClear')):
        a = decomp.symbol(name) & ~1
        j = itcm.long_jump(a, sym[target])
        d[a - start:a - start + len(j)] = j
    open(ov12, 'wb').write(d)
    return f'platinum_trainer_flags: Trainers past {pearl_ids.LAST_B2_TRAINER} use flags from {pearl_ids.EXTENDED_TRAINER_FLAGS} (ITCM {base:#x}-{end:#x})'
