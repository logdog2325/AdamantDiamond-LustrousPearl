"""The Factory harness's species table (sim.c): each species of Platinum's dump (poketool/personal/pl_personal.narc) as
type 1, type 2 (u8, Platinum's numbers), ability 1, ability 2 (u16), from its personal record (bytes 6, 7, 22, 23).

    python3 b2tools/platinum_factory_host/species.py OUT
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'b2tools'))
from gen4rom import Rom, narc_members  # noqa: E402

if __name__ == '__main__':
    rows = narc_members(Rom(os.path.join(ROOT, 'roms', 'platinum.nds')).read('poketool/personal/pl_personal.narc'))
    open(sys.argv[1], 'wb').write(b''.join(struct.pack('<BBHH', r[6], r[7], r[22], r[23]) for r in rows[:494]))
