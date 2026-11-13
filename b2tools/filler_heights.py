"""Pearl's raised filler cells in Black 2 (2026-11-09): Celestic Town's south edge drew black.

Pearl's map matrices give every cell an altitude, and Pearl draws the cell's model that many half-tiles up
(pokeplatinum land_data.c LandDataManager_CalculateRenderingPosition: y = altitude * MAP_OBJECT_TILE_SIZE / 2, 8
units each). Only the filler cells use it (the land in no zone between the routes: Pearl's chunks 173-178):
299 cells of matrix 0, at 1 to 26 (8 to 208 units), and the Great Marsh's 14 tree cells (matrix 240) at 2. The open
sea (174, a flat plane) is one of them: at 1 it meets the routes' sea at 8; at 0 it lay a step below it. Black 2 has no altitude: every chunk is drawn at y 0 (ov012 field_g3d_map.c
chunk->worldPos.y = 0), so a raised cell's model sat below Pearl's. South of Celestic (matrix cell (14, 17), chunk
175 at 16: a flat cliff-top plane 128 units up in Pearl, level with the town's south cliff) the camera looked over
the cliff past the plane, onto no chunk: the top screen's bottom rows were black.

apply(files): for each (installed chunk, altitude) that a raised cell shows, one copy of that chunk with its model
moved altitude * 8 units up (its terrain unchanged: filler cells are all wall), appended to a/0/0/8; the cell then
shows the copy. Matrices: 0 and every room matrix whose Pearl matrix has altitudes. Cells a map replacement names
(a/0/1/0: the hidden paths) are left as they are (pearl_paths raises the Spring Path's cover itself: Pearl's code
draws it at altitude 2, pearl_hidden_paths.PATHS). Called by pearl_paths, after every room's chunk and the paths' own
(sinnoh_rooms and pearl_paths check a/0/0/8's length when they start), before fixed_weather (which fogs these too).

    python3 b2tools/filler_heights.py        the raised cells and the copies they need (offline, nothing written)
"""
import json, os, struct, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import version  # noqa: E402

UNITS = 8                       # one altitude step: half a tile (MAP_OBJECT_TILE_SIZE / 2)
CHUNK_ARC, MATRIX_ARC, MAP_REPLACE_ARC = 8, 9, 10


def raised_cells(world=None):
    """{B2 matrix id: [(cell index, altitude)]} for every installed matrix whose Pearl matrix has altitudes."""
    world = world or json.load(open(version.data_path('sinnoh_world.json')))
    b2_of = {0: 0}
    for mid, r in world['rooms']['matrices'].items():
        b2_of[int(mid)] = r['b2_matrix']
    out = {}
    mdir = os.path.join(version.WORLD_WORK, 'matrices')
    for name in sorted(os.listdir(mdir)):
        if not name.endswith('.json'): continue
        mid = int(name[:-5])
        m = json.load(open(os.path.join(mdir, name)))
        cells = [(cz * m['width'] + cx, a) for cz, row in enumerate(m.get('altitudes') or [])
                 for cx, a in enumerate(row) if a and m['maps'][cz][cx] != 0xffff]
        if cells and mid in b2_of:
            out[b2_of[mid]] = (m['width'], m['height'], cells)
    return out


def raise_model(bmd, units):
    """The BMD0 with every vertex `units` map units higher (its bounding box grown to match)."""
    import pearl_mesh
    model = pearl_mesh.Model(bmd)
    dy = int(round(units * 4096 / model.pos_scale))
    for s in model.shapes:
        for g, (_, polys) in enumerate(s.groups):
            for k, p in enumerate(polys):
                polys[k] = [v.moved(y=v[1] + dy) for v in p]
                assert all(-32768 <= v[1] <= 32767 for v in polys[k]), f'{units} units up leaves the vertex range'
    return model.encode()


def apply(files):
    import narcio, pearl_chunk
    mats, chunks = narcio.load(files, MATRIX_ARC), narcio.load(files, CHUNK_ARC)
    replaced = set()
    rep = narcio.load(files, MAP_REPLACE_ARC)
    if rep and rep[0]:
        for i in range(0, len(rep[0]) - 15, 16):
            _, _, _, old, shown = struct.unpack_from('<HBBHH', rep[0], i)
            replaced |= {old, shown}
    copies, n_cells, skipped = {}, 0, []
    for b2m, (w, h, cells) in sorted(raised_cells().items()):
        m = bytearray(mats[b2m])
        assert struct.unpack_from('<HH', m, 4) == (w, h), f'matrix {b2m}: not {w} x {h}'
        for i, alt in cells:
            src = struct.unpack_from('<I', m, 8 + 4 * i)[0]
            if src == 0xFFFFFFFF or src >= len(chunks) or not chunks[src]: skipped.append((b2m, i, 'none')); continue
            if src in replaced: skipped.append((b2m, i, 'replaced')); continue
            key = (src, alt)
            if key not in copies:
                magic, layers, part = pearl_chunk.terrains(chunks[src])
                chunks.append(pearl_chunk.rebuild(magic, raise_model(part['model'], alt * UNITS), layers, part['props']))
                copies[key] = len(chunks) - 1
            struct.pack_into('<I', m, 8 + 4 * i, copies[key])
            n_cells += 1
        mats[b2m] = bytes(m)
    narcio.save(files, CHUNK_ARC, chunks)
    narcio.save(files, MATRIX_ARC, mats)
    return (f'filler_heights: {n_cells} raised cells show {len(copies)} raised chunk copies '
            f'({", ".join(f"{s}+{a * UNITS}" for s, a in sorted(copies))})'
            + (f'; skipped {len(skipped)}: {skipped[:6]}' if skipped else ''))


if __name__ == '__main__':
    import pearl_mesh
    total = Counter()
    for b2m, (w, h, cells) in sorted(raised_cells().items()):
        alts = Counter(a for _, a in cells)
        print(f'matrix {b2m} ({w} x {h}): {len(cells)} raised cells, altitudes {dict(sorted(alts.items()))}')
        total[b2m] = len(cells)
    for c in sorted({c for c in (173, 174, 175, 176, 177, 178)}):
        p = os.path.join(version.WORLD_WORK, 'land', f'{c:03d}.nsbmd')
        if not os.path.exists(p): continue
        bmd = open(p, 'rb').read()
        up = pearl_mesh.Model(raise_model(bmd, 26 * UNITS))
        ys = [up.units(v)[1] for s in up.shapes for q in s.polys for v in q]
        print(f'chunk {c}: raised 208 units -> y {min(ys):.1f} .. {max(ys):.1f}')
