"""Phase 1/2 reader: a Gen 4 game's map chunks (land_data_release.narc, Platinum's land_data.narc) to JSON + NSBMD.

    python3 gen4_land.py [ROM] [OUT_DIR]          defaults: the version's world dump, work/<world>/land
                                                  (Pearl and Diamond: roms/pearl.nds, work/pearl/land;
                                                  PEARL_VERSION=platinum: roms/platinum.nds, work/platinum/land)

Each 32x32-tile chunk holds: tile attributes (u16 per tile: collision bit 15, behaviour in the low byte), placed
buildings ("props": model id into build_model.narc, position, rotation, scale), the terrain model (NSBMD) and the
height data (BDHC: sloped plates over the chunk). pokediamond has no layout for this file (a gap), so it follows
pokeplatinum docs/maps/file_format_specifications.md "Land data"; every chunk's section sizes are checked against its
file size. Read-only.

BDHC: Pearl's height blocks do NOT match Platinum's documented BDHC, and pokediamond's loader is not decompiled. Each
chunk's BDHC is written raw (NNN.bdhc); read_bdhc() is for Platinum's layout, read_bdhc_dp() reads Pearl's own
(decoded 2026-10-25 from the files themselves, for the bridges' two levels; below) and turns a Platinum file into the same
shape (bdhc_platinum_as_dp), so the tools that use heights ask read_bdhc_dp in every version.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from gen4rom import Rom, narc_members  # noqa: E402
import version  # noqa: E402

FX = 1 << 12


def read_bdhc(b):
    assert b[:4] == b'BDHC', 'no BDHC magic'
    np_, nn, nc, npl, ns, na = struct.unpack_from('<6H', b, 4)
    p = 16
    points = [struct.unpack_from('<2i', b, p + 8 * i) for i in range(np_)]; p += 8 * np_
    normals = [struct.unpack_from('<3i', b, p + 12 * i) for i in range(nn)]; p += 12 * nn
    consts = list(struct.unpack_from(f'<{nc}i', b, p)); p += 4 * nc
    plates = [struct.unpack_from('<4H', b, p + 8 * i) for i in range(npl)]; p += 8 * npl
    strips = [struct.unpack_from('<iHH', b, p + 8 * i) for i in range(ns)]; p += 8 * ns
    access = list(struct.unpack_from(f'<{na}H', b, p)); p += 2 * na
    assert p == len(b), f'BDHC: {len(b) - p} bytes left'
    return {'points': [[x / FX, z / FX] for x, z in points], 'normals': [[c / FX for c in n] for n in normals],
            'constants': [c / FX for c in consts], 'plates': [list(pl) for pl in plates],
            'strips': [[s / FX, n, i] for s, n, i in strips], 'access': access}


def height_at(bdhc, x, z):
    """Height (world units) of the plate under BDHC point (x, z), or None. The plane is n.(x,y,z) + d = 0."""
    for a, c, ni, ci in bdhc['plates']:
        (x0, z0), (x1, z1) = bdhc['points'][a], bdhc['points'][c]
        if min(x0, x1) <= x <= max(x0, x1) and min(z0, z1) <= z <= max(z0, z1):
            nx, ny, nz = bdhc['normals'][ni]
            if ny:
                return -(nx * x + nz * z + bdhc['constants'][ci]) / ny
    return None


def read_bdhc_dp(b):
    """Diamond/Pearl's BDHC (decoded 2026-10-25 from Pearl's files; pokediamond's loader is assembly): None if the
    file doesn't fit the layout (Pearl's 10 unused chunks 422-430 and 453 don't), else
    {'points': [(x, y, z)], 'normals': [(x, y, z)], 'plates': [(i0, i1, i2, normal, d)]} in map units (fx32 / 4096).
    0x00 'BDHC'; 0x04 u32 0x20 (the header's size); 0x08 six (element size, count) u16 pairs: points (12: VecFx32),
    normals (12: VecFx32), plates (12), 28-byte records and two more (a lookup grid, not read here). 0x20 a 36-byte
    grid header: two u32, the grid's width and height (u16; 1x1 in Twinleaf, 2x2 on Route 215), its min and max
    corner and cell size (x, z fx32 pairs). 0x44 the points, the normals, the plates: u16 three point indices, u16 the
    normal, fx32 d. A plate is a TRIANGLE (its points' x, z) of the plane n.(x, y, z) + d = 0 (two per square: Twinleaf
    is (0,1,2) + (0,2,3) at y 16). Like Platinum (pokeplatinum src/overlay005/bdhc.c CalculateObjectHeight) a walker
    takes, of the plates over its x, z, the one nearest its own height: where two plates overlap (a bridge over a
    road) the walker stays on its own level (pokeplatinum terrain_collision_manager.c: a step of 20 units or more is a
    wall)."""
    if b[:4] != b'BDHC':
        return None
    u = struct.unpack_from('<14H', b, 4)
    if u[0] != 0x20 and is_platinum_bdhc(b):
        return bdhc_platinum_as_dp(b)
    out = _read_dp(b, u)
    if out is None and is_platinum_bdhc(b):
        # (a Platinum file of 32 points: its first count, 0x20, reads as Pearl's header size, and nothing came out:
        # Sendoff Spring 444, Route 214 152 and four rooms 385, 436, 468, 477; found by the events piece, 2026-11-02)
        return bdhc_platinum_as_dp(b)
    return out


def _read_dp(b, u):
    """read_bdhc_dp's Pearl layout (u: the 14 u16 after the magic), or None."""
    if u[0] != 0x20 or (u[2], u[4], u[6]) != (12, 12, 12):
        return None
    n_points, n_normals, n_plates = u[3], u[5], u[7]
    p = 0x44
    if p + 12 * (n_points + n_normals + n_plates) > len(b):
        return None
    points = [tuple(v / FX for v in struct.unpack_from('<3i', b, p + 12 * i)) for i in range(n_points)]
    p += 12 * n_points
    normals = [tuple(v / FX for v in struct.unpack_from('<3i', b, p + 12 * i)) for i in range(n_normals)]
    p += 12 * n_normals
    plates = []
    for i in range(n_plates):
        i0, i1, i2, n, d = struct.unpack_from('<4Hi', b, p + 12 * i)
        if max(i0, i1, i2) >= n_points or n >= n_normals:
            return None
        plates.append((i0, i1, i2, n, d / FX))
    return {'points': points, 'normals': normals, 'plates': plates}


def is_platinum_bdhc(b):
    """Does the file fit Platinum's layout exactly (six counts, then sections that end at the file's end)?"""
    np_, nn, nc, npl, ns, na = struct.unpack_from('<6H', b, 4)
    return 16 + 8 * np_ + 12 * nn + 4 * nc + 8 * npl + 8 * ns + 2 * na == len(b)


def bdhc_platinum_as_dp(b):
    """A Platinum BDHC in read_bdhc_dp's shape. Platinum's plate is a rectangle on a plane (two corners, normal, constant;
    pokeplatinum src/overlay005/bdhc.c), read_bdhc_dp's a triangle: each rectangle gives Pearl's two triangles (0,1,2) + (0,2,3)."""
    r = read_bdhc(b)
    points, normals, plates = [], [tuple(n) for n in r['normals']], []
    for a, c, n, k in r['plates']:
        (x0, z0), (x1, z1) = r['points'][a], r['points'][c]
        nx, ny, nz = r['normals'][n]
        d = r['constants'][k]
        y = (lambda x, z: -(nx * x + nz * z + d) / ny) if ny else (lambda x, z: 0.0)
        i = len(points)
        points += [(px, y(px, pz), pz) for px, pz in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
        plates += [(i, i + 1, i + 2, n, d), (i, i + 2, i + 3, n, d)]
    return {'points': points, 'normals': normals, 'plates': plates}


def bdhc_dp_heights(bdhc, x, z):
    """[(height, normal)] of every plate of a read_bdhc_dp BDHC over chunk-centred (x, z), highest first."""
    out = []
    for i0, i1, i2, n, d in bdhc['plates']:
        A, B, C = bdhc['points'][i0], bdhc['points'][i1], bdhc['points'][i2]
        den = (B[0] - A[0]) * (C[2] - A[2]) - (C[0] - A[0]) * (B[2] - A[2])
        nv = bdhc['normals'][n]
        if abs(den) < 1e-9 or abs(nv[1]) < 1e-6:
            continue
        s = ((x - A[0]) * (C[2] - A[2]) - (C[0] - A[0]) * (z - A[2])) / den
        t = ((B[0] - A[0]) * (z - A[2]) - (x - A[0]) * (B[2] - A[2])) / den
        if s < -1e-6 or t < -1e-6 or s + t > 1 + 1e-6:
            continue
        out.append((-(nv[0] * x + nv[2] * z + d) / nv[1], nv))
    return sorted(out, key=lambda h: -h[0])


def read_chunk(m):
    ta, pr, mo, bd = struct.unpack_from('<4I', m, 0)
    assert ta == 2048 and 16 + ta + pr + mo + bd == len(m), f'sizes {ta} {pr} {mo} {bd} vs {len(m)}'
    attrs = list(struct.unpack_from('<1024H', m, 16))
    props = []
    for i in range(pr // 48):
        f = struct.unpack_from('<I3i3i3i2I', m, 16 + ta + 48 * i)
        props.append({'model': f[0], 'pos': [v / FX for v in f[1:4]], 'rot': list(f[4:7]),
                      'scale': [v / FX for v in f[7:10]]})
    model = m[16 + ta + pr:16 + ta + pr + mo]
    assert model[:4] == b'BMD0', 'terrain model is not NSBMD'
    bdhc = m[16 + ta + pr + mo:]
    assert bdhc[:4] == b'BDHC', 'no BDHC magic'
    return {'collision': [[a >> 15 for a in attrs[r * 32:(r + 1) * 32]] for r in range(32)],
            'behaviour': [[a & 0xff for a in attrs[r * 32:(r + 1) * 32]] for r in range(32)],
            'props': props}, model, bdhc


# Platinum names some of its new map materials by its exporter's default: 'file1Material' for the Battle Zone's palm
# tree3_01, 'file3Material' tree3_02, 'file4Material' the palm rows conttree3_2, 'a' for Pastoria's building shadow h_kage;
# in rooms the rebuilt Eterna Gym's 'fgds', 'qq', 's', 'ss' (its trees and their shadow), chairs' and counters' shadows.
# Pearl always puts the texture's name in the material's, and the tools tell trees, shadows and snow from the ground by the
# material's name (pearl_chunk.SKIP_MATERIALS for heights, pearl_model_fix.is_tree for the layers, season_decals): the
# palms' crowns became ground, 30-54 units over the walkable tiles under them (walls in Route 229 and the Fight Area). So such
# a material takes its texture's name in front of its own (2026-11-02; Pearl's and Diamond's models have none: unchanged).
NAME_KEYS = ('tree', 'shadow', 'kage', 's_snow', 's_sonwp')


def named_materials(bmd):
    """(BMD0, [(old name, new name)]): the land model with each material whose texture's name has a NAME_KEYS word that its
    own name lacks renamed '<texture>_<name>' (16 characters at most, unique); the material dictionary is written anew
    (pearl_mesh.write_model), every other part of the model as it was."""
    import pearl_mesh, pearl_render
    model = pearl_mesh.Model(bmd)
    info = pearl_render.bindings(model)
    names = list(model.materials)
    renames = []
    for i, (name, t) in enumerate(zip(model.materials, info)):
        tex = (t[0] or '').lower()
        if not any(k in tex and k not in name.lower() for k in NAME_KEYS): continue
        base, new, n = f'{t[0]}_{name}'[:16], None, 0
        new = base
        while new in names:
            n += 1; new = base[:16 - len(str(n))] + str(n)
        names[i] = new
        renames.append((name, new))
    if not renames: return bmd, []
    mats, shapes, _ = pearl_mesh.unchanged_parts(model)
    for i, n in enumerate(names): mats[i] = dict(mats[i], name=n)
    return pearl_mesh.write_model(model, mats, shapes, pearl_mesh.sbc_with(model)), renames


def main():
    rom = Rom(sys.argv[1] if len(sys.argv) > 1 else version.WORLD_DUMP)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(version.WORLD_WORK, 'land')
    os.makedirs(out, exist_ok=True)
    chunks = version.slotted('land', narc_members(rom.read(version.ARCHIVE['land'])))
    props = 0
    renamed = []
    for i, m in enumerate(chunks):
        if not m:
            continue
        data, model, bdhc = read_chunk(m)
        model, names = named_materials(model)
        renamed += [(i, a, b) for a, b in names]
        json.dump(data, open(os.path.join(out, f'{i:03d}.json'), 'w'))
        open(os.path.join(out, f'{i:03d}.nsbmd'), 'wb').write(model)
        open(os.path.join(out, f'{i:03d}.bdhc'), 'wb').write(bdhc)
        props += len(data['props'])
    print(f'{len(chunks)} chunks -> {out}: {props} placed buildings; materials named after their textures '
          f'(named_materials): {len(renamed)} in {len({c for c, _, _ in renamed})} chunks')


if __name__ == '__main__':
    main()
