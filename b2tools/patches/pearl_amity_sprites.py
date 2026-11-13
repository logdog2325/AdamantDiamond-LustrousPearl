"""Pearl's own overworld Pokémon (Amity Square, 2026-10-25; the user: "open Amity Square with the Pokémon following
like in Pearl", Pearl's own art pixel for pixel). Run after pearl_npc_sprites (both edit a/0/4/8).
2026-10-26 (the following Pokémon, patches/followers.py; user: convert Pearl's own walkers): also Pearl's other two
16-frame Pokémon walkers, Machop (SPRITE_WANRIKY, Oreburgh and its mine) and Shaymin's Land Forme (SPRITE_SPPOKE8,
Route 224 and Flower Paradise), on codes 337 and 338 (nothing in Black 2 names them:
work/agents/followers/free_codes.py). Pearl's other Pokémon sheets are not walkers (Starly 4 frames, Magikarp 2, the
legendaries 1-2) and keep Black 2's own walking sprites.

The 11 Pokémon that walk with the player in Amity Square, which also stand in Pearl's houses, gates and routes, had
Black 2's own overworld Pokémon (codes 0x1000 + species: Black 2's look, drawn with its Pokémon animation sets 13/14,
which loop a walk cycle in place). Pearl draws them as people (pokeplatinum object_event_gfx_data.c: the same draw
functions as its townspeople and the Elite Four) from 32 x 32 sheets of 16 frames: back, front, left, right, 4 per
direction (stand, step, stand, step), feet on row 29. Each now has a Black 2 person code of its own (12-frame walker,
scene node 2, controller 3, shadow on, as the Elite Four's codes in pearl_npc_sprites), repainted with Pearl's frames
0, 1, 3 of each direction (Black 2's stand, step, step), 1 pixel lower (Black 2's feet are on row 30), with Pearl's
16 colours. data/pearl_sprite_map.json gives each graphics id its code.

The codes: none of Black 2's own zones that this game keeps, none of its scripts' ActorNew, none of its tables (the
PWT's a/2/4/7, ov012 BtlInst_GetTrainerClassObjCode, union_view.c) and none of its C names them (pokebw2 res/field
events and scripts, src); 111 nothing at all, the others only Unova zones whose numbers Sinnoh's maps took (listed per
code in the sprite map's notes). Each sheet (res1 of the code's a/0/4/7 record) belongs to that code alone. Checked
here: each code is one Pearl graphics id's only, and outside the PWT's table.
"""
import json, os, struct, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import narcio, sprites  # noqa: E402
from pearl_player_sprites import MMODEL, shift, SHIFT_DOWN  # noqa: E402

# (Pokémon, Pearl graphics id, Pearl mmodel file, texture name)
POKEMON = [('Pikachu', 71, 69, 'pikachu'), ('Clefairy', 72, 70, 'pippi'), ('Jigglypuff', 73, 71, 'purin'),
           ('Psyduck', 74, 72, 'koduck'), ('Torchic', 78, 76, 'achamo'), ('Skitty', 79, 77, 'eneco'),
           ('Drifloon', 185, 163, 'balloon'), ('Pachirisu', 204, 371, 'patiritusu'),
           ('Shroomish', 205, 372, 'kinococo'), ('Buneary', 206, 373, 'mimituto'), ('Happiny', 207, 374, 'kolucky'),
           ('Machop', 208, 375, 'wanriky'), ('Shaymin', 158, 137, 'sppoke8')]   # 2026-10-26: the following Pokémon
# Platinum's Amity Square also lets the Sinnoh starters and their evolutions walk with the player (pokeplatinum
# scripts_amity_square.s, AmitySquare_CheckPartyHasSpecies: Pikachu, Clefairy, Psyduck, Pachirisu, Drifloon, Buneary,
# Happiny and the nine; Jigglypuff, Torchic, Skitty and Shroomish once the National Pokédex is obtained). Its own 16-frame
# walkers, from Platinum's dump (mmodel 383-391), on codes no kept Black 2 zone, script, table or C names
# (data/platinum/sprite_map.json 220-228; work/agents/plat-caves/tools/free_codes.py found them).
PLATINUM_POKEMON = [('Turtwig', 220, 383, 'naetle'), ('Grotle', 221, 384, 'hayashigame'), ('Torterra', 222, 385, 'dodaitose'),
                    ('Chimchar', 223, 386, 'hikozaru'), ('Monferno', 224, 387, 'moukazaru'), ('Infernape', 225, 388, 'goukazaru'),
                    ('Piplup', 226, 389, 'pochama'), ('Prinplup', 227, 390, 'pottaishi'), ('Empoleon', 228, 391, 'emperte')]
ARC_PWT = 247                                        # a/2/4/7: the PWT's trainers, u16 x 8 records, object code at +2
WALK12 = [d * 4 + k for d in range(4) for k in (0, 1, 3)]


# Platinum redrew Buneary and Happiny (its mmodel 373 and 374, the same members as Pearl's; 2026-11-07, step 6,
# plat-sprites): a Platinum build takes them from its own dump. Pearl's other walkers are the same pixels in both.
PLATINUM_REDRAWN = {206, 207}


def walkers():
    """[(Pokémon, graphics id, mmodel file, texture name, dump)] of the version's own walkers: Pearl's 13 (from
    people_dump(); for Platinum, the two it redrew from its own), and for Platinum its starters (from its own dump)."""
    import version
    out = [(w, g, m, t, version.WORLD_DUMP if version.PLATINUM and g in PLATINUM_REDRAWN else people_dump())
           for w, g, m, t in POKEMON]
    if version.PLATINUM:
        out += [(w, g, m, t, version.WORLD_DUMP) for w, g, m, t in PLATINUM_POKEMON]
    return out


def sprite_map():
    """{graphics id (str): row}: data/pearl_sprite_map.json, with Platinum's own rows over it in a Platinum build."""
    import version
    smap = json.load(open(os.path.join(ROOT, 'data', 'pearl_sprite_map.json'), encoding='utf-8'))
    if version.PLATINUM:
        smap.update({k: v for k, v in json.load(open(os.path.join(ROOT, 'data', 'platinum', 'sprite_map.json'),
                                                     encoding='utf-8')).items() if k != '_doc'})
    return smap


def apply(files):
    import version
    from gen4rom import Rom, narc_members
    smap = sprite_map()
    dumps = {}
    sheets = narcio.load(files, sprites.ARC_OW_SHEETS)
    table = sprites.ow_table(files)
    t = narcio.load(files, ARC_PWT)[0]
    pwt = {struct.unpack_from('<H', t, 16 * i + 2)[0] for i in range(len(t) // 16)}
    res1 = Counter(r['res1'] for r in table)
    done = []
    for who, gfx, mid, tex, dump in walkers():
        if dump not in dumps: dumps[dump] = narc_members(Rom(dump).read(MMODEL))
        mm = dumps[dump]
        code = smap[str(gfx)]['code']
        users = [k for k, v in smap.items() if isinstance(v, dict) and v.get('code') == code]
        assert users == [str(gfx)], (who, code, users)
        assert code < 377 and code not in pwt, f'{who}: code {code} is not a free person code'
        sheet, rec = sprites.ow_sheet_of(files, code, table)
        assert res1[sheet] == 1, f'{who}: sheet {sheet} of code {code} is shared'
        assert (rec['sceneNodeType'], rec['spriteControllerType'], rec['shadow']) == (2, 3, 1), (who, rec)
        lay, _, _ = sprites.btx_layout(sheets[sheet])
        assert len(lay) == 12 and all((w, h) == (32, 32) for _, w, h, _ in lay), who
        fr, _, pal = sprites.btx_decode(mm[mid])
        fr = sorted(fr, key=lambda f: int(f[0].split('.')[-1]))
        assert len(fr) == 16 and all(f[0].rsplit('.', 1)[0] == tex and (f[1], f[2]) == (32, 32) for f in fr), who
        sheets[sheet] = sprites.btx_encode(sheets[sheet], [shift(fr[i][3], SHIFT_DOWN) for i in WALK12], pal)
        done.append(f'{who} = code {code} (sheet {sheet})')
    narcio.save(files, sprites.ARC_OW_SHEETS, sheets)
    return 'pearl_amity_sprites: ' + '; '.join(done)


def people_dump():
    """Platinum moved 59 of Pearl's sheets and changed others: until step 6 maps its own, its people are Pearl's (the base), from Pearl's
    dump. Diamond's and Pearl's are their own."""
    import version
    return os.path.join(ROOT, 'roms', 'pearl.nds') if version.PLATINUM else version.SOURCE_DUMP
