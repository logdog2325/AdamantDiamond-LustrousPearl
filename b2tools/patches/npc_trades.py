"""Gen 4's in-game trades (plat-trades, 2026-11-07; the decomp's include/pearlb2/npc_trade.h, src/pearlb2/resident/
npc_trade.c): the version's trade table into the resident pool and its address into gPearlB2NpcTrades. The scripts' trades
are PearlB2 extension 0xA7 (pearl_story.inc pl_StartNPCTrade): Black 2's own trade event and demo with the Pokémon made
by Platinum's rules from this table (b2tools/npc_trade_data.py: the dump's fld_trade.narc and its names).

apply_code(code): only when version.NPC_TRADES (Platinum now; Pearl and Diamond in 1.0.1). Otherwise nothing: the
pointer stays NULL and the command trades nothing (Pearl's 1.0 scripts keep their stubs). List it anywhere after the code
binaries are copied (the resident pool is set up before any patch).

    PEARL_VERSION=platinum python3 b2tools/patches/npc_trades.py      the table it would install, offline
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import version  # noqa: E402


def apply_code(code):
    if not version.NPC_TRADES:
        return f'npc_trades: {version.VERSION}\'s trades stay stubs (version.NPC_TRADES off)'
    import decomp, resident
    import npc_trade_data as T
    slot = decomp.symbol('gPearlB2NpcTrades', code)
    if slot is None:
        raise SystemExit('npc_trades: the decomp has no gPearlB2NpcTrades (src/pearlb2/resident/npc_trade.c)')
    blob = T.blob()
    old = struct.unpack('<I', resident.read(code, slot, 4))[0]
    if old:                                      # a quick non-clean build: the table is there, rewrite it in place
        assert resident.read(code, old, 4) == blob[:4], 'gPearlB2NpcTrades: not the table'
        resident.write(code, old, blob)
        base = old
    else:
        base, end, _ = resident.install(code, lambda b: (blob, {}))
        resident.write(code, slot, struct.pack('<I', base))
    names = ', '.join(t['nickname'] for t in T.trades())
    return f'npc_trades: {len(T.trades())} trades ({names}), {len(blob)} B at {base:#x} (gPearlB2NpcTrades {slot:#x})'


if __name__ == '__main__':
    import npc_trade_data as T
    print(T.summary())
    print(f'{len(T.blob())} B; installed: {version.NPC_TRADES}')
