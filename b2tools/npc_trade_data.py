"""The in-game trades of the version's dump (plat-trades, 2026-11-07): what the decomp's src/pearlb2/resident/npc_trade.c
(PearlB2 extension 0xA7, include/pearlb2/npc_trade.h) and the generator's "plat-trades" block (pearl_story.py) need.

    PEARL_VERSION=platinum python3 b2tools/npc_trade_data.py         prints the trades
    PEARL_VERSION=platinum python3 b2tools/npc_trade_data.py test    the offline test (below)

Gen 4 keeps them in fielddata/pokemon_trade/fld_trade.narc, one file of 80 bytes a trade (pokeplatinum
include/overlay006/npc_trade.h NPCTradeMon: 20 words, species, the six IVs in HP, Attack, Defense, Speed, Sp. Atk,
Sp. Def order, a word the code never reads (the ability the personality gives), the OT's ID, the five contest
conditions, the personality, the held item, the OT's gender, a second unread word, the language, the species wanted),
and the nicknames and OT names in a text bank (TEXT_BANK_NPC_TRADE_NAMES: lines 0-3 the nicknames, 4-7 the OT names;
pokeplatinum src/overlay006/npc_trade.c NPCTrade_GetOTName). Platinum's four: Oreburgh's Kazza (Abra for Machop),
Eterna's Charap (Chatot for Buizel), Snowpoint's Gaspar (Haunter for Medicham), Route 226's Foppa (Magikarp for Finneon).
Pearl's and Diamond's dumps hold the same four (their language word differs), read the same way (1.0.1).

How Platinum makes the Pokémon (npc_trade.c NPCTrade_CreateMon): the level of the Pokémon given, the fixed personality
(so its nature, its gender and which of its two abilities), the OT's ID, the six IVs, the nickname (marked as one), the
five conditions, the held item, the OT's name, gender and language; met "in a trade" at its level (sel 1 of
UpdateMonStatusAndTrainerInfo: SpecialMetLoc 2001, whatever map); its friendship the species' own; never shiny (it
asserts). blob() is the table the resident code reads (PearlB2NpcTradeTable), which patches/npc_trades.py writes into the
resident pool; the C sets the nature (Black 2 draws one at random) and the ability (Black 2 picks it by another bit) from
the table, so both are Platinum's.

The test (no ROM build): every trade against the decomp's res/npc_trades/*.json (Platinum) and the dump's own names,
the ability the personality gives against the record's unread word and the personal data, the gender it gives, that
none is shiny with its OT, the names' Black 2 characters and lengths, and blob()'s layout read back.
"""
import functools, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402

TRADE_NARC = 'fielddata/pokemon_trade/fld_trade.narc'
NAMES_BANK = {'msgdata/pl_msg.narc': 370, 'msgdata/msg.narc': 326}   # pokeplatinum generated/text_banks.txt (0-based);
                                                                     # pokediamond files/msgdata/msg/narc_0326.gmm
RECORD = 80
NICKNAME_SIZE, OT_NAME_SIZE = 11, 8      # Black 2's u16 arrays with the 0xFFFF end (PKM_PARAM_NICKNAME_RAW, OT_NAME_RAW)
TRADE_SIZE = 68                          # include/pearlb2/npc_trade.h PearlB2NpcTrade
HEADER = 4                               # u16 count, u16 version of the table
TABLE_VERSION = 1
EOS = 0xFFFF
PLATINUM_SRC = os.path.join(ROOT, 'external', 'pokeplatinum')
IV_KEYS = ('hpIV', 'atkIV', 'defIV', 'speedIV', 'spAtkIV', 'spDefIV')
CONTEST_KEYS = ('cool', 'beauty', 'cute', 'smart', 'tough')
LANGUAGES = {'LANGUAGE_JAPANESE': 1, 'LANGUAGE_ENGLISH': 2, 'LANGUAGE_FRENCH': 3, 'LANGUAGE_ITALIAN': 4,
             'LANGUAGE_GERMAN': 5, 'LANGUAGE_SPANISH': 7}          # Gen 4's = Black 2's PKM_PARAM_REGION values


@functools.lru_cache(None)
def rom():
    from gen4rom import Rom
    return Rom(version.WORLD_DUMP)


def _members(path):
    from gen4rom import narc_members
    return narc_members(rom().read(path))


@functools.lru_cache(None)
def names():
    """The trade names bank as text, in its own numbering (not the tools' slots)."""
    import gen4_text
    arc = gen4_text.msg_archive(rom())
    return [gen4_text.to_gmm(m) for m in gen4_text.decrypt_bank(_members(arc)[NAMES_BANK[arc]])]


@functools.lru_cache(None)
def personal(species):
    """(ability 1, ability 2, gender ratio, friendship) of a species in the dump's personal data (Gen 4: 44 bytes).
    (v101-story) The version's own dump: Diamond's personal.narc is in roms/diamond.nds, not in Pearl's world dump (the
    same file for Pearl and Platinum)."""
    from gen4rom import Rom, narc_members
    p = narc_members(Rom(version.SOURCE_DUMP).read(version.PERSONAL_NARC))[species]
    return p[0x16], p[0x17], p[0x10], p[0x12]


def ability_of(species, pid):
    """The ability Gen 4 gives: the second when the personality is odd and the species has one (Pokemon_InitWith)."""
    a1, a2, _, _ = personal(species)
    return a2 if (pid & 1) and a2 else a1


def gender_of(species, pid):
    """0 male, 1 female, 2 none (Gen 4's and Black 2's rule: the personality's low byte against the ratio)."""
    ratio = personal(species)[2]
    if ratio in (0, 254, 255):
        return {0: 0, 254: 1, 255: 2}[ratio]
    return 1 if (pid & 0xFF) < ratio else 0


def shiny(ot_id, pid):
    x = (ot_id >> 16) ^ (ot_id & 0xFFFF) ^ (pid >> 16) ^ (pid & 0xFFFF)
    return x < 8


@functools.lru_cache(None)
def trades():
    """The dump's trades: [{species, ivs, ability_word, ot_id, contest, pid, item, ot_gender, unused2, language, wanted,
    nickname, ot_name}] in trade-id order."""
    recs = _members(TRADE_NARC)
    text = names()
    n = len(recs)
    assert len(text) == 2 * n, f'{TRADE_NARC}: {n} trades, {len(text)} names'
    out = []
    for i, r in enumerate(recs):
        assert len(r) == RECORD, f'trade {i}: {len(r)} bytes'
        w = struct.unpack('<20I', r)
        out.append(dict(species=w[0], ivs=tuple(w[1:7]), ability_word=w[7], ot_id=w[8], contest=tuple(w[9:14]),
                        pid=w[14], item=w[15], ot_gender=w[16], unused2=w[17], language=w[18], wanted=w[19],
                        nickname=text[i], ot_name=text[n + i]))
    return tuple(out)


def chars(s, size):
    """A name as Black 2's u16 characters with the 0xFFFF end, padded with 0xFFFF to size."""
    assert re.fullmatch(r"[A-Za-z0-9 .'-]+", s), f'{s!r}: a character this table has no Black 2 code for'
    codes = [ord(c) for c in s] + [EOS]
    assert len(codes) <= size, f'{s!r}: longer than {size - 1}'
    return codes + [EOS] * (size - len(codes))


def record_bytes(t):
    """PearlB2NpcTrade: u16 species 0, u16 heldItem 2, u32 otId 4, u32 pid 8, u8 ivs[6] 12, u8 contest[5] 18, u8 otGender 23,
    u8 language 24, u8 ability 25, u16 wantedSpecies 26, u16 nickname[11] 28, u16 otName[8] 50, 2 bytes of padding (68)."""
    b = struct.pack('<HHII', t['species'], t['item'], t['ot_id'], t['pid'])
    b += bytes(t['ivs']) + bytes(t['contest'])
    b += struct.pack('<BBBH', t['ot_gender'], t['language'], ability_of(t['species'], t['pid']), t['wanted'])
    b += struct.pack(f'<{NICKNAME_SIZE}H', *chars(t['nickname'], NICKNAME_SIZE))
    b += struct.pack(f'<{OT_NAME_SIZE}H', *chars(t['ot_name'], OT_NAME_SIZE))
    b += b'\0\0'
    assert len(b) == TRADE_SIZE, len(b)
    return b


def blob():
    """PearlB2NpcTradeTable: u16 count, u16 TABLE_VERSION, then the trades."""
    ts = trades()
    return struct.pack('<HH', len(ts), TABLE_VERSION) + b''.join(record_bytes(t) for t in ts)


def requested_species(trade):
    """The species trade `trade` wants (Platinum's GetNPCTradeRequestedSpecies): the generator writes it as a constant."""
    return trades()[trade]['wanted']


def offered_species(trade):
    return trades()[trade]['species']


def summary():
    lines = []
    for i, t in enumerate(trades()):
        lines.append(f'{i}: {t["nickname"]} (species {t["species"]}, OT {t["ot_name"]} {t["ot_id"]}, '
                     f'{"female" if t["ot_gender"] else "male"}, language {t["language"]}) for species {t["wanted"]}: '
                     f'IVs {"/".join(map(str, t["ivs"]))}, personality {t["pid"]} (nature {t["pid"] % 25}, ability '
                     f'{ability_of(t["species"], t["pid"])}), item {t["item"]}, contest {t["contest"]}')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------------------------------------------- test
def _decomp_trades():
    """pokeplatinum's res/npc_trades/*.json in constants/npc_trades.h order, the values as numbers."""
    order = re.findall(r'NPC_TRADE_(\w+)\s*=?', open(os.path.join(PLATINUM_SRC, 'include', 'constants', 'npc_trades.h')).read())
    order = [o for o in order if o != 'MAX' and not o.startswith('MAX')]
    consts = {}
    for name in ('species', 'items'):
        p = os.path.join(PLATINUM_SRC, 'generated', f'{name}.txt')
        if os.path.exists(p):
            for k, line in enumerate(l.strip() for l in open(p) if l.strip()):
                consts[line] = k
    out = []
    for o in order:
        d = json.load(open(os.path.join(PLATINUM_SRC, 'res', 'npc_trades', o.lower() + '.json')))
        out.append(d)
    return order, out, consts


def test():
    problems = []
    ts = trades()
    print(summary())
    if version.PLATINUM:
        order, dec, consts = _decomp_trades()
        if len(dec) != len(ts):
            problems.append(f'{len(ts)} trades in the dump, {len(dec)} in the decomp')
        for i, (t, d) in enumerate(zip(ts, dec)):
            def num(v, kind):
                if isinstance(v, int):
                    return v
                if v in consts:
                    return consts[v]
                if v in LANGUAGES:
                    return LANGUAGES[v]
                if v.startswith('GENDER_'):
                    return {'GENDER_MALE': 0, 'GENDER_FEMALE': 1}[v]
                raise KeyError(f'{v} ({kind})')
            want = dict(species=num(d['species'], 'species'), ivs=tuple(d[k] for k in IV_KEYS), ability_word=d['unused1'],
                        ot_id=d['otID'], contest=tuple(d[k] for k in CONTEST_KEYS), pid=d['personality'],
                        item=num(d['heldItem'], 'item'), ot_gender=num(d['otGender'], 'gender'), unused2=d['unused2'],
                        language=num(d['language'], 'language'), wanted=num(d['requestedSpecies'], 'species'),
                        nickname=d['name'], ot_name=d['otName'])
            for k, v in want.items():
                if t[k] != v:
                    problems.append(f'trade {i} ({order[i]}): {k} {t[k]!r} in the dump, {v!r} in the decomp')
    for i, t in enumerate(ts):
        a = ability_of(t['species'], t['pid'])
        if a != t['ability_word']:
            problems.append(f'trade {i}: the personality gives ability {a}, the record says {t["ability_word"]}')
        if shiny(t['ot_id'], t['pid']):
            problems.append(f'trade {i}: shiny with its OT (Platinum asserts it is not)')
        if not 1 <= t['species'] <= 493 or not 1 <= t['wanted'] <= 493:
            problems.append(f'trade {i}: a species past 493')
        if t['item'] > 467:
            problems.append(f'trade {i}: item {t["item"]} is no Gen 4 item (Black 2 keeps their numbers up to 467)')
        if any(v > 31 for v in t['ivs']) or any(v > 255 for v in t['contest']):
            problems.append(f'trade {i}: an IV or a condition out of range')
        chars(t['nickname'], NICKNAME_SIZE), chars(t['ot_name'], OT_NAME_SIZE)
    b = blob()
    n, ver = struct.unpack_from('<HH', b, 0)
    if n != len(ts) or ver != TABLE_VERSION or len(b) != HEADER + n * TRADE_SIZE:
        problems.append(f'blob: {n} trades, version {ver}, {len(b)} bytes')
    for i, t in enumerate(ts):
        o = HEADER + i * TRADE_SIZE
        sp, item, ot, pid = struct.unpack_from('<HHII', b, o)
        ivs, cond = tuple(b[o + 12:o + 18]), tuple(b[o + 18:o + 23])
        g, lang, abil = b[o + 23], b[o + 24], b[o + 25]
        wanted, = struct.unpack_from('<H', b, o + 26)
        nick = struct.unpack_from(f'<{NICKNAME_SIZE}H', b, o + 28)
        otn = struct.unpack_from(f'<{OT_NAME_SIZE}H', b, o + 50)
        got = (sp, item, ot, pid, ivs, cond, g, lang, abil, wanted,
               ''.join(map(chr, nick[:nick.index(EOS)])), ''.join(map(chr, otn[:otn.index(EOS)])))
        exp = (t['species'], t['item'], t['ot_id'], t['pid'], t['ivs'], t['contest'], t['ot_gender'], t['language'],
               ability_of(t['species'], t['pid']), t['wanted'], t['nickname'], t['ot_name'])
        if got != exp:
            problems.append(f'blob trade {i}: read back {got}, expected {exp}')
        print(f'  {t["nickname"]}: gender {("male", "female", "none")[gender_of(t["species"], t["pid"])]}, '
              f'friendship {personal(t["species"])[3]}, not shiny')
    print(f'{len(ts)} trades, blob {len(b)} B; {len(problems)} problems')
    for p in problems:
        print('  ' + p)
    return not problems


if __name__ == '__main__':
    if sys.argv[1:] == ['test']:
        sys.exit(0 if test() else 1)
    print(summary())
