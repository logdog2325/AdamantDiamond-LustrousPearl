"""Pearl's Super Contests (notes/CONTESTS.md): they replace the Musical at Hearthome's counters, in both versions.

apply(files): the archive of Pearl's art, data and text (b2tools/contest_data.py members(), in the order of the decomp's
include/pearlb2/contest_app.h) over ARCID_MUSICAL_POKEGRA, a/0/5/1, read only by the Musical.
apply_code(code): ContestConfig (the Black 2 ids of Pearl's five songs from work/world/music.json) in the resident pool,
gPearlB2Contest pointing at it. List after sinnoh_music (the songs) and the Pokétch's patch (the resident section and its
pool). Replaces `musical` in the build list. The screen's overlay 373 goes in by pearlb2_overlays.py.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.dirname(HERE))
import contest_data  # noqa: E402

ITEM_ARC, ITEM_POFFIN_CASE, ITEM_BICYCLE, ITEM_FIELD_FUNC = 24, 449, 450, 0xA     # include/pml/item.h ItemData.fieldFunc
SONGS = ('SEQ_CO_DRESS', 'SEQ_CO_KASHI', 'SEQ_CO_TAKUMA', 'SEQ_CO_KEKKA', 'SEQ_CO_FANFA')


def apply(files):
    import narcio
    members = contest_data.members()
    narcio.save(files, contest_data.ARC, members)
    # the Poffin Case (449) gets the Bicycle's Use in the Bag: its field function (as HoennB2's patches/contests.py)
    items = narcio.load(files, ITEM_ARC)
    rec = bytearray(items[ITEM_POFFIN_CASE])
    rec[ITEM_FIELD_FUNC] = items[ITEM_BICYCLE][ITEM_FIELD_FUNC]
    items[ITEM_POFFIN_CASE] = bytes(rec)
    narcio.save(files, ITEM_ARC, items)
    return f'contests: archive {contest_data.ARC} = {len(members)} members, {sum(map(len, members))} B'


def apply_code(code):
    import decomp, resident
    slot = decomp.symbol('gPearlB2Contest', code)
    assert slot is not None, 'the decomp has no gPearlB2Contest (its src/pearlb2/resident/contest.c)'
    events = json.load(open(os.path.join(ROOT, 'work', 'world', 'music.json')))['events']
    ids = [events[n] for n in SONGS]

    def build(base):
        return struct.pack('<6H', ids[0], ids[1], ids[2], ids[3], ids[4], 0), {}
    base, end, _ = resident.install(code, build)
    assert resident.read(code, slot, 4) in (bytes(4), struct.pack('<I', base)), f'gPearlB2Contest at {slot:#x}: set'
    resident.write(code, slot, struct.pack('<I', base))
    return f'contests: ContestConfig {end - base} B at {base:#x}, songs {ids}'
