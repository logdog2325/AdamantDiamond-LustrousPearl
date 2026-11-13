"""The harness's sources (notes/PLATINUM_FRONTIER.md "The harness"): functions and tables copied, as they are, out of the two decomps.

    python3 b2tools/platinum_frontier_host/extract.py OUT_DIR

OUT_DIR/plat_rules.c   Platinum's Battle Tower rules (pokeplatinum src/unk_0204AEE8.c, src/unk_02049D08.c, src/unk_0206B9D8.c):
                       the room's Trainer draw, the seven (or fourteen) opponents of a round, the challenge's random numbers,
                       the Battle Points for a won round, the team picks (sub_0204B470: the sets, no species or item twice).
OUT_DIR/b2_rules.c     ours, the code the ROM runs (pokebw2 src/pearlb2/resident/tower.c, src/ov033/bsubway_scr.c): PearlB2's
                       draw and Black 2's round, Battle Points (PearlB2's values), team picks (ov012 fld_btl_inst_tool.c
                       BtlInst_MakeRomTeam) and IVs (ov033 bsubway_trainers.c).
Each is the decomp's own text, a function at a time (by its name, braces matched); plat_shim.h and b2_shim.h give them the
types and the few calls they make (the challenge's save data, the records), nothing of the rules.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PLAT = os.path.join(ROOT, 'external', 'pokeplatinum')
B2 = os.path.join(ROOT, 'external', 'pokebw2')


def body(text, head):
    """The function or table that starts with `head` (a regex), to its closing brace."""
    m = re.search(head, text, re.M)
    assert m, head
    i = text.index('{', m.end() - 1 if text[m.end() - 1] == '{' else m.end())
    depth = 0
    for j in range(i, len(text)):
        if text[j] == '{':
            depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                if text[end:end + 1] == ';':
                    end += 1
                return text[m.start():end]
    raise ValueError(head)


def plat():
    a = open(os.path.join(PLAT, 'src', 'unk_0204AEE8.c')).read()
    b = open(os.path.join(PLAT, 'src', 'unk_02049D08.c')).read()
    c = open(os.path.join(PLAT, 'src', 'unk_0206B9D8.c')).read()
    order = [l.strip() for l in open(os.path.join(PLAT, 'res', 'trainers', 'frontier', 'frontier_trainers.order')) if l.strip()]
    out = ['// Platinum\'s Battle Tower rules, copied by extract.py from pokeplatinum (do not edit)', '#include "plat_shim.h"', '']
    out += [f'#define FRONTIER_TRAINER_{n.upper()} {i}' for i, n in enumerate(order)] + ['']
    out.append(body(c, r'^u32 sub_0206BFF0\(u32 param0\)'))
    out.append(body(b, r'^u16 BattleTower_GetRandom\(BattleTower \*battleTower\)'))
    out.append(body(a, r'^static const u16 sBattleTowerTrainerRangesPerRoom\[\]\[2\] ='))
    out.append(body(a, r'^static const u16 sBattleTowerBossTrainerRangesPerRoom\[\]\[2\] ='))
    out.append(body(a, r'^u16 BattleTower_GetTrainerIDForRoomAndOpponentNum\('))
    out.append(body(b, r'^static BOOL BattleTower_IsTrainerAlreadyUsed\('))
    out.append(body(b, r'^void sub_0204A4C8\(BattleTower \*battleTower, SaveData \*saveData\)'))
    out.append(body(b, r'^u16 BattleTower_GiveBattlePointsReward\(BattleTower \*battleTower\)'))
    out.append(body(b, r'^u8 BattleTower_GetIVsFromTrainerID\(u16 battleTowerID\)'))
    out.append(body(a, r'^static BOOL sub_0204B470\(BattleTower \*battleTower, FrontierTrainerBase \*trainerData, u16 partnerBattleTowerID, FrontierPokemon \*param3, u8 partySize, u16 \*param5, u16 \*param6, BattleTowerPartnerData \*param7, enum HeapID heapID\)$'))
    out.append('BOOL Plat_PickTeam(BattleTower *bt, FrontierTrainerBase *tr, u16 id, FrontierPokemon *mons, u8 n, '
               'BattleTowerPartnerData *partner)\n{\n    return sub_0204B470(bt, tr, id, mons, n, NULL, NULL, partner, HEAP_ID_FIELD2);\n}')
    return '\n\n'.join(out) + '\n'


def b2():
    t = open(os.path.join(B2, 'src', 'pearlb2', 'resident', 'tower.c')).read()
    s = open(os.path.join(B2, 'src', 'ov033', 'bsubway_scr.c')).read()
    out = ['// Ours: PearlB2\'s draw and Black 2\'s round and Battle Points, copied by extract.py from pokebw2 (do not edit)',
           '#include "b2_shim.h"', '']
    out += [l for l in t.split('\n') if re.match(r'#define (TOWER_PARTNER_FIRST|TOWER_PALMER_SILVER|TOWER_PALMER_GOLD)\b', l)]
    out.append(body(t, r'^static const u16 sTrainerRanges\[8\]\[2\] ='))
    out.append(body(t, r'^static const u16 sLastTrainerRanges\[8\]\[2\] ='))
    out.append(body(t, r'^u16 PearlB2_TowerDrawTrainerNo\('))
    out.append(body(s, r'^static const u8 sBattlePointRewards\[7\]\[10\] ='))
    f = open(os.path.join(B2, 'src', 'ov012', 'fld_btl_inst_tool.c')).read()
    out.append(body(f, r'^BOOL BtlInst_MakeRomTeam\('))
    out.append(body(open(os.path.join(B2, 'src', 'ov033', 'bsubway_trainers.c')).read(), r'^u8 BsubwayScr_GetMonIv\('))
    for name in ('u16 BsubwayScr_GetWinCount', 'BOOL BsubwayScr_IsTrainerNoUsed', 'u16 BsubwayScr_GetStageNo',
                 'void BsubwayScr_DrawTrainerNos', 'u16 func_ov033_0217b8ec'):
        out.append(body(s, '^' + re.escape(name) + r'\('))
    return '\n\n'.join(out) + '\n'


if __name__ == '__main__':
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'plat_rules.c'), 'w').write(plat())
    open(os.path.join(d, 'b2_rules.c'), 'w').write(b2())
    print(f'{d}: plat_rules.c, b2_rules.c')
