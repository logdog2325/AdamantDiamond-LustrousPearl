"""Cracks and flicker in Sinnoh's converted map chunks (the world pass, 2026-10-20; HoennB2's tjunction.py,
water_seams_check.py, exterior_layers.py / exterior_check.py layer_pairs ported to Pearl's map models).

    python3 pearl_seams_check.py [--fixed] [--rooms|--world] [--json=OUT] [CHUNK ...]   per chunk, totals
    python3 pearl_seams_check.py --holes [--rooms|--world] [CHUNK ...]    the seams the fixes open (holes(), 2026-11-02)
    python3 pearl_seams_check.py --holes --views [--json=OUT] [CHUNK ...]   the same from the build's own camera: every
                                          chunk along nine rays of its screen, where the player can stand (2026-11-07)
    python3 pearl_seams_check.py --compare OLD.json NEW.json              chunks worse or better between two --json runs

The models are Pearl's own (work/pearl/land/NNN.nsbmd, b2tools/pearl_mesh.py), drawn by Black 2: with --fixed they
go through pearl_chunk.fix_model first (what the build installs). Measured, per chunk (Pearl chunk ids):
- tj      T-junctions in the ground (an opaque, upward-facing polygon's vertex inside another one's edge, within 0.05
          units), in the chunk and across its borders (the neighbours in the matrix, at their offsets). melonDS and the
          hardware open 1-pixel cracks there.
- open    length (units) of edges inside the flat ground (normal y >= 0.95; each edge counted from both sides, at
          2-unit samples), where the ground goes on at the same height on both sides,
          with nothing opaque 1-16 units under them: a crack along them shows the clear colour (sky blue by day,
          black in caves). The DS opens cracks even along shared edges (HoennB2 cracks 2026-10-18); the under-floor
          (pearl_chunk.underfloor) backs them.
- border  area (units^2) where this chunk's ground and a neighbour's overlap in one plane with different texels
          (Pearl's models overhang their chunk by 4 units: both are drawn there).
- fight   pairs of overlapping polygons facing the same way less than MIN_GAP apart along their normal, with
          different texels (Black 2's field camera 0: Z-buffer, near 1: one depth step is ~1.7 units at the player,
          ~3.7 at the top of the screen; HoennB2's rule: 2 units), by material pair.
- size    the chunk's bytes as sinnoh_world/sinnoh_rooms write it (model + 8,196 terrain + placements + 20), against
          Black 2's 110,600-byte chunk buffer.
"""
import json, math, os, sys, collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import version  # noqa: E402
from version import land_id  # noqa: E402  (Spear Pillar: the chunk's file for this version)
import pearl_mesh  # noqa: E402

LAND = os.path.join(version.WORLD_WORK, 'land')
MIN_GAP = 2.0
EPS = 0.05
CHUNK_LIMIT = 110600
TREES = ('tree', 'conttree', 'g1_tree', 'plant')


def base(name):
    return name.split('_lm')[0]


def is_tree(name):
    return any(t in name for t in TREES)


class Poly:
    __slots__ = ('mat', 'alpha', 'pid', 'P', 'UV', 'n', 'd', 'shape', 'index', 'faces')


def load(model):
    """[Poly] of a pearl_mesh.Model in map units, each shape where the DS draws it (its node's translation added:
    pearl_mesh.shape_translations, as pearl_rooms_view and room_look draw them; the fixes judge them there with
    version.NODE_SHIFT)."""
    out = []
    ps = model.pos_scale / 4096
    tr = [np.array(t, float) for t in model.shape_translations()]
    for si, s in enumerate(model.shapes):
        if s.material is None: continue
        pa = model.poly_attr(s.material)
        name = model.materials[s.material]
        for k, p in enumerate(s.polys):
            P = np.array([v.pos for v in p], float) * ps
            P = P + tr[si]
            n = np.cross(P[1] - P[0], P[2] - P[0])
            if len(P) == 4: n = n + np.cross(P[2] - P[0], P[3] - P[0])
            L = np.linalg.norm(n)
            if L < 1e-9: continue
            q = Poly()
            q.mat, q.alpha, q.pid = name, (pa >> 16) & 31, (pa >> 24) & 63
            q.faces = (pa >> 6) & 3                   # (the sides the DS draws: 1 back, 2 front, 3 both)
            q.P, q.UV, q.n = P, np.array([(v[3] / 16, v[4] / 16) for v in p], float), n / L
            q.d = float(q.n @ P.mean(0)); q.shape = si; q.index = k
            out.append(q)
    return out


def ground(polys):
    return [q for q in polys if q.alpha == 31 and q.n[1] > 0.7 and not is_tree(q.mat)]


def top_ground(g, drop=4.0):
    """(ground, under-floor): ground polygons with ground `drop` units above their centre are the under-floor
    (pearl_model_fix.underfloor), counted as backing only; with version.GROUND_STAYS also its second try's drop
    (pearl_model_fix.UNDER_DEEP)."""
    T, C = tris_xz(g); G = Grid(T, C)
    ctr = np.array([q.P.mean(0) for q in g]) if g else np.zeros((0, 3))
    hs = G.heights(ctr[:, [0, 2]]) if len(ctr) else []
    drops = (drop, 8.0) if version.GROUND_STAYS else (drop,)
    top, under = [], []
    for q, c, h in zip(g, ctr, hs):
        (under if any(np.any(np.abs(h - (c[1] + d)) < 0.3) for d in drops) else top).append(q)
    return top, under


def tris_xz(polys):
    """(T (K,3,2) x/z corners, plane (K,3): y = a x + b z + c) of polys' triangles."""
    T, Y = [], []
    for q in polys:
        for a, b, c in ((0, 1, 2), (0, 2, 3)) if len(q.P) == 4 else ((0, 1, 2),):
            T.append(q.P[[a, b, c]][:, [0, 2]]); Y.append(q.P[[a, b, c]])
    if not T: return np.zeros((0, 3, 2)), np.zeros((0, 3))
    T = np.array(T); Y = np.array(Y)
    # plane through the three corners
    A = np.concatenate([T, np.ones((len(T), 3, 1))], axis=2)
    det = np.linalg.det(A)
    ok = np.abs(det) > 1e-9
    coef = np.zeros((len(T), 3))
    coef[ok] = np.linalg.solve(A[ok], Y[ok][:, :, 1][..., None])[..., 0]
    return T[ok], coef[ok]


class Grid:
    """Triangles bucketed by 16-unit x/z cells, for point queries."""
    def __init__(self, T, coef, cell=16.0):
        self.T, self.coef, self.cell = T, coef, cell
        self.b = collections.defaultdict(list)
        if not len(T): return
        lo = np.floor(T.min(1) / cell).astype(int); hi = np.floor(T.max(1) / cell).astype(int)
        for i in range(len(T)):
            for gx in range(lo[i, 0], hi[i, 0] + 1):
                for gz in range(lo[i, 1], hi[i, 1] + 1):
                    self.b[(gx, gz)].append(i)

    def heights(self, pts, margin=1e-3):
        """For points (M,2): list of arrays of the heights of the triangles that hold each point."""
        out = [None] * len(pts)
        keys = np.floor(pts / self.cell).astype(int)
        groups = collections.defaultdict(list)
        for i, k in enumerate(map(tuple, keys)): groups[k].append(i)
        for k, idx in groups.items():
            cand = self.b.get(k)
            if not cand:
                for i in idx: out[i] = np.zeros(0)
                continue
            T = self.T[cand]; C = self.coef[cand]
            Q = pts[idx]
            inside = np.ones((len(idx), len(cand)), bool)
            area = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
            sgn = np.sign(area)
            for e in range(3):
                a, b = T[:, e], T[:, (e + 1) % 3]
                L = np.maximum(np.hypot(b[:, 0] - a[:, 0], b[:, 1] - a[:, 1]), 1e-9)
                cr = ((b[:, 0] - a[:, 0])[None] * (Q[:, None, 1] - a[None, :, 1])
                      - (b[:, 1] - a[:, 1])[None] * (Q[:, None, 0] - a[None, :, 0])) * sgn[None] / L[None]
                inside &= cr >= -margin
            Y = C[:, 0][None] * Q[:, None, 0] + C[:, 1][None] * Q[:, None, 1] + C[:, 2][None]
            for r, i in enumerate(idx):
                out[i] = Y[r][inside[r]]
        return out


def t_junctions(gpolys, others=()):
    """[(polygon, edge, point)]: vertices of gpolys + others lying strictly inside an edge of a gpolys polygon."""
    pts = {}
    for q in list(gpolys) + list(others):
        for p in q.P: pts[tuple(np.round(p, 3))] = p
    P = np.array(list(pts.values())) if pts else np.zeros((0, 3))
    grid = collections.defaultdict(list)
    for i, p in enumerate(P): grid[(int(p[0] // 16), int(p[2] // 16))].append(i)
    out = []
    for q in gpolys:
        k = len(q.P)
        for e in range(k):
            a, b = q.P[e], q.P[(e + 1) % k]
            d = b - a; L2 = float(d @ d)
            if L2 < 1e-6: continue
            x0, x1 = sorted((a[0], b[0])); z0, z1 = sorted((a[2], b[2]))
            cand = [i for gx in range(int((x0 - EPS) // 16), int((x1 + EPS) // 16) + 1)
                    for gz in range(int((z0 - EPS) // 16), int((z1 + EPS) // 16) + 1) for i in grid.get((gx, gz), ())]
            if not cand: continue
            C = P[cand]
            s = ((C - a) @ d) / L2
            close = np.linalg.norm(a + s[:, None] * d[None] - C, axis=1) < EPS
            hit = close & (s > 1e-4) & (s < 1 - 1e-4)
            for j in np.nonzero(hit)[0]: out.append((q, e, C[j]))
    return out


def open_edges(gpolys, backing, step=2.0):
    """(length of edges inside the ground, length of those with nothing opaque 1-16 units under them)."""
    T, C = tris_xz(gpolys); G = Grid(T, C)
    bT, bC = tris_xz(backing); B = Grid(bT, bC)
    samples, ys = [], []
    for q in gpolys:
        k = len(q.P)
        for e in range(k):
            a, b = q.P[e], q.P[(e + 1) % k]
            L = math.hypot(b[0] - a[0], b[2] - a[2])
            if L < 1e-3: continue
            n = max(1, int(L // step))
            for j in range(n):
                f = (j + 0.5) / n
                p = a + f * (b - a)
                dx, dz = (b[2] - a[2]) / L * 0.3, -(b[0] - a[0]) / L * 0.3
                samples.append((p[0], p[2], dx, dz, L / n)); ys.append(p[1])
    if not samples: return 0.0, 0.0
    S = np.array(samples); Y = np.array(ys)
    left = G.heights(S[:, :2] + S[:, 2:4]); right = G.heights(S[:, :2] - S[:, 2:4])
    under = B.heights(S[:, :2])
    inner = unbacked = 0.0
    for i in range(len(S)):
        if not (np.any(np.abs(left[i] - Y[i]) < 0.5) and np.any(np.abs(right[i] - Y[i]) < 0.5)): continue
        inner += S[i, 4]
        h = under[i]
        if not np.any((h < Y[i] - 1.0) & (h > Y[i] - 16)): unbacked += S[i, 4]
    return inner, unbacked


def _basis(n):
    u = np.cross(n, (0, 1, 0)) if abs(n[1]) < 0.9 else np.cross(n, (1, 0, 0))
    u = u / np.linalg.norm(u)
    return u, np.cross(n, u)


def _clip(poly, clipper):
    """Convex 2D polygon poly clipped by convex polygon clipper (both counter-clockwise)."""
    out = poly
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp: break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            sp = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            sq = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
            if sp >= 0: out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq); out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _ccw(pts):
    a = sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))
    return pts if a <= 0 else pts[::-1]


def _area(poly):
    return abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))) / 2


def _uv_at(q, pt):
    """Texture coordinate of polygon q at 3D point pt (affine over its first triangle; quads are planar here)."""
    P = q.P; e1, e2 = P[1] - P[0], P[2] - P[0]
    M = np.array([[e1 @ e1, e1 @ e2], [e1 @ e2, e2 @ e2]])
    r = pt - P[0]
    try: s, t = np.linalg.solve(M, [r @ e1, r @ e2])
    except np.linalg.LinAlgError: return q.UV[0]
    return q.UV[0] + s * (q.UV[1] - q.UV[0]) + t * (q.UV[2] - q.UV[0])


def same_texels(a, b, pts):
    """Polygons a and b draw the same texels at pts (same material, texture coordinates equal or 16 texels apart)."""
    if base(a.mat) != base(b.mat): return False
    for p in pts:
        d = _uv_at(a, p) - _uv_at(b, p)
        if np.any(np.abs(d - 16 * np.round(d / 16)) > 0.6): return False
    return True


def layer_pairs(polys, others=(), min_gap=MIN_GAP, max_gap=None, points=False):
    """[(a, b, gap, area)]: overlapping polygons facing the same way, b behind a by gap < min_gap along a's normal
    (others: polygons that only count as the other member, e.g. a neighbour's). Same texels never fight. points: each
    pair also carries its overlap's corners [(point on a's plane, b's gap there)]."""
    allp = list(polys) + list(others)
    own = len(polys)
    buckets = collections.defaultdict(list)
    for i, q in enumerate(allp):
        ax = int(np.argmax(np.abs(q.n)))
        o = [k for k in range(3) if k != ax]
        lo = np.floor(q.P[:, o].min(0) / 32).astype(int); hi = np.floor(q.P[:, o].max(0) / 32).astype(int)
        for g0 in range(lo[0], hi[0] + 1):
            for g1 in range(lo[1], hi[1] + 1):
                buckets[(ax, g0, g1)].append(i)
    seen, out = set(), []
    for idx in buckets.values():
        for x in range(len(idx)):
            i = idx[x]
            for y in range(x + 1, len(idx)):
                j = idx[y]
                if (i, j) in seen or (i >= own and j >= own): continue
                seen.add((i, j))
                a, b = allp[i], allp[j]
                nn = float(a.n @ b.n)
                if nn < 0.98: continue
                if abs(a.d - b.d) > min_gap + 64: continue
                u, v = _basis(a.n)
                pa = _ccw([(float(p @ u), float(p @ v)) for p in a.P])
                pb = _ccw([(float(p @ u), float(p @ v)) for p in b.P])
                ov = _clip(pa, pb)
                if len(ov) < 3 or _area(ov) < 0.5: continue
                pts3 = [a.d * a.n + s * u + t * v for s, t in ov]
                gaps = [(b.d - float(b.n @ q)) / nn for q in pts3]     # from a's plane to b's, along a's normal
                g = min(gaps, key=abs) if max(gaps) * min(gaps) > 0 else 0.0
                if abs(g) >= min_gap: continue
                if same_texels(a, b, pts3): continue
                if g > 0: a, b = b, a                                    # b behind a
                out.append((a, b, abs(g), _area(ov)) + ((list(zip(pts3, gaps)),) if points else ()))
    return out


# ---------------------------------------------------------------------------------------- depth precision (--depth)
# (the polish pass, 2026-10-20; user, melonDS: "some trees still flicker slightly") Two layers fight when the DS
# stores them in one depth step: camera 0's Z-buffer keeps z/w to 1/16384 (near 1, far 1024: one step is w^2 / 32800
# units of view depth w), and a layer pair g units apart along its normal is g (r.f) / |r.n| apart in w along a pixel's
# ray r (f: the view axis). Every place can come to every screen row as the camera follows the player, so a pair is
# measured at the rows of the screen's top, middle and bottom (rays 33.2, 43.2, 53.2, 63.2, 73.2 degrees down; the
# eye 189.73 over the ground the camera's target stands on, here the highest ground under the point): ratio = that w
# gap / one step, the smallest over the rows and the overlap's corners. Under 1 the two can round to one depth value
# and the picture depends on the draw order (flicker as the camera moves); DESIRED 1.25 leaves room for the DS's
# per-vertex depth rounding.
EYE_H, PITCH = 189.73, 53.2
ROWS = (33.2, 43.2, 53.2, 63.2, 73.2)
DEPTH_RATIO = 1.0


def depth_ratio(p, n, g, y0):
    """Smallest (w gap / depth step) over the screen rows for a layer pair g apart along unit normal n at point p
    (y0: the ground under the camera's target)."""
    f = np.array([0.0, -math.sin(math.radians(PITCH)), -math.cos(math.radians(PITCH))])
    best = math.inf
    for phi in ROWS:
        r = np.array([0.0, -math.sin(math.radians(phi)), -math.cos(math.radians(phi))])
        L = (EYE_H - (p[1] - y0)) / math.sin(math.radians(phi))
        if L <= 1: continue
        w = L * float(r @ f)
        rn = abs(float(r @ n))
        if rn < 1e-3: continue
        best = min(best, abs(g) * float(r @ f) / rn / (w * w / 32800.0))
    return best


def depth_pairs(chunk, cell, fixed=True, cache=None):
    """Layer pairs of a chunk (with its neighbours) under 8 units apart, each with its depth ratio (depth_ratio):
    [(a, b, gap, area, ratio, tree)]."""
    import pearl_chunk
    cache = {} if cache is None else cache
    m, x, z = cell
    cells = cache.setdefault('cells', {})
    cells.setdefault(chunk, cell)
    def model_of(c):
        if (c, fixed) not in cache:
            bmd = open(os.path.join(LAND, f'{land_id(c):03d}.nsbmd'), 'rb').read()
            if fixed:
                mm, xx, zz = cells.get(c, cell)
                bmd, _ = pearl_chunk.fix_model(c, bmd, pearl_chunk.neighbours(mm, xx, zz))
            cache[(c, fixed)] = (len(bmd), load(pearl_mesh.Model(bmd)), {})
        return cache[(c, fixed)]
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if 0 <= x + dx < m['width'] and 0 <= z + dz < m['height'] and m['maps'][z + dz][x + dx] != 0xffff:
                cells.setdefault(m['maps'][z + dz][x + dx], (m, x + dx, z + dz))
    polys = model_of(chunk)[1]
    near = neighbour_polys((x, z), m, lambda c: model_of(c)[1])
    gT, gC = tris_xz(ground(polys + near)); G = Grid(gT, gC)
    out = []
    for a, b, gap, area, pts in layer_pairs(polys, near, min_gap=8.0, points=True):
        P = np.array([q for q, _ in pts])
        hs = G.heights(P[:, [0, 2]])
        r = math.inf
        for (q, g), h in zip(pts, hs):
            under = h[h <= q[1] + 1.0] if len(h) else h
            y0 = float(under.max()) if len(under) else float(min(a.P[:, 1].min(), b.P[:, 1].min()))
            r = min(r, depth_ratio(q, a.n, g, y0))
        out.append((a, b, gap, area, r, is_tree(a.mat) or is_tree(b.mat)))
    return out


def neighbour_polys(chunk_matrix_cell, matrix, models):
    """Polygons of the 8 cells around (x, z) of matrix, moved to their offset (only those within 32 of the border)."""
    x, z = chunk_matrix_cell
    out = []
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not (dx or dz): continue
            if not (0 <= x + dx < matrix['width'] and 0 <= z + dz < matrix['height']): continue
            c = matrix['maps'][z + dz][x + dx]
            if c == 0xffff: continue
            for q in models(c):
                P = q.P + np.array([512 * dx, 0, 512 * dz])
                if np.all(np.abs(P[:, 0]) > 288) or np.all(np.abs(P[:, 2]) > 288): continue
                r = Poly()
                for f in Poly.__slots__: setattr(r, f, getattr(q, f))
                r.P = P; r.d = float(r.n @ P.mean(0))
                out.append(r)
    return out


def cells_of(world):
    """{Pearl chunk: (matrix dict, x, z)}: the overworld chunks in matrix 0, the rooms' in their first matrix."""
    out = {}
    m0 = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', '000.json')))
    for z in range(m0['height']):
        for x in range(m0['width']):
            c = m0['maps'][z][x]
            if c != 0xffff and str(c) in world['chunks']: out.setdefault(c, (m0, x, z))
    for mid in world['rooms']['matrices']:
        m = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', f'{int(mid):03d}.json')))
        for z in range(m['height']):
            for x in range(m['width']):
                c = m['maps'][z][x]
                if c != 0xffff and str(c) in world['rooms']['chunks']: out.setdefault(c, (m, x, z))
    return out


def check(chunk, cell, fixed=False, cache=None):
    import pearl_chunk
    cache = {} if cache is None else cache
    m, x, z = cell
    def model_of(c, where=None):
        if (c, fixed) not in cache:
            bmd = open(os.path.join(LAND, f'{land_id(c):03d}.nsbmd'), 'rb').read()
            rep = {}
            if fixed:
                mm, xx, zz = where or cells_of_cache[c]
                bmd, rep = pearl_chunk.fix_model(c, bmd, pearl_chunk.neighbours(mm, xx, zz))
            cache[(c, fixed)] = (len(bmd), load(pearl_mesh.Model(bmd)), rep)
        return cache[(c, fixed)]
    cells_of_cache = cache.setdefault('cells', {})
    cells_of_cache.setdefault(chunk, cell)
    # (a neighbour is fixed within its own first cell when it has one, else within this matrix)
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if 0 <= x + dx < m['width'] and 0 <= z + dz < m['height'] and m['maps'][z + dz][x + dx] != 0xffff:
                cells_of_cache.setdefault(m['maps'][z + dz][x + dx], (m, x + dx, z + dz))
    size, polys, fixrep = model_of(chunk, cell)
    near = neighbour_polys((x, z), m, lambda c: model_of(c)[1])
    g = ground(polys); gn = ground(near)
    g, under = top_ground(g)
    inside = lambda q: np.all(np.abs(q.P[:, [0, 2]]) <= 256 + 1e-3)
    tj = t_junctions(g, [q for q in gn])
    tj_border = sum(1 for q, e, p in tj if max(abs(p[0]), abs(p[2])) >= 252)
    opaque = [q for q in polys + near if q.alpha == 31]
    flat = [q for q in g if q.n[1] >= 0.95]                 # (the walkable ground: cliff bottoms and tops left out)
    inner, unbacked = open_edges([q for q in flat if inside(q)] or flat, opaque)
    pairs = layer_pairs(polys, near)
    nearset = {id(q) for q in near}
    border, border_pairs = 0.0, collections.Counter()
    fights = collections.Counter()
    for a, b, gap, ar in pairs:
        if gap < 0.01 and (id(a) in nearset or id(b) in nearset):
            border += ar; border_pairs[(base(a.mat), base(b.mat))] += round(ar)
            continue
        fights[(base(a.mat), base(b.mat))] += 1
    props = json.load(open(os.path.join(LAND, f'{land_id(chunk):03d}.json')))['props']
    total = 20 + size + 8196 + 4 + 16 * len(props)
    return dict(chunk=chunk, tj=len(tj), tj_border=tj_border, open=round(inner), unbacked=round(unbacked),
                border=round(border), border_pairs=border_pairs.most_common(4), fights=sum(fights.values()),
                fight_pairs=fights.most_common(6), size=total, fixes=fixrep)


def main_depth(args):
    """--depth [CHUNK ...]: per chunk the layer pairs under DEPTH_RATIO (trees / others, their overlap area)."""
    fixed = '--fixed' in args
    world = json.load(open(version.data_path('sinnoh_world.json')))
    cells = cells_of(world)
    chunks = [int(a) for a in args if a.isdigit()] or (sorted(int(c) for c in world['chunks'])
                                                       + sorted(int(c) for c in world['rooms']['chunks']))
    cache, tot = {'cells': dict(cells)}, collections.Counter()
    worst = collections.Counter()
    for c in chunks:
        ps = depth_pairs(c, cells[c], fixed, cache)
        bad = [p for p in ps if p[4] < DEPTH_RATIO]
        t = [p for p in bad if p[5]]
        tot['pairs'] += len(bad); tot['tree_pairs'] += len(t)
        tot['area'] += sum(p[3] for p in bad); tot['tree_area'] += sum(p[3] for p in t)
        for p in t: worst[(base(p[0].mat), base(p[1].mat), round(p[2], 2))] += 1
        if bad:
            print(json.dumps(dict(chunk=c, pairs=len(bad), trees=len(t), tree_area=round(sum(p[3] for p in t)),
                                  area=round(sum(p[3] for p in bad)),
                                  min_ratio=round(min(p[4] for p in bad), 2))), flush=True)
    print(f"{len(chunks)} chunks{' (fixed)' if fixed else ''}: layer pairs under depth ratio {DEPTH_RATIO}: "
          f"{tot['pairs']} ({round(tot['area'])} units^2), trees {tot['tree_pairs']} ({round(tot['tree_area'])} units^2)")
    print('tree pairs (materials, gap):', worst.most_common(15))


# ------------------------------------------------------------------------------------------------ holes (2026-11-02)
# What the fixes open up: the chunk's opaque polygons (trees left out: their cards move on purpose) seen along the build's
# camera (Black 2's camera 0 at Pearl's pitch, maplook 'tilt': 59 degrees, from the south), Pearl's raw model against
# the model the build installs, at HOLE_PX pixels a unit. A pixel the raw model covers and the fixed one leaves open is a
# hole the fixes made: there the screen shows the clear colour (black outdoors), a seam. Platinum's Twinleaf had 3,000+ px
# of them (its ground moved in steps under its snow patches) before version.GROUND_STAYS. Polygons from the chunk itself
# only, in both models.
HOLE_PX, HOLE_PITCH = 2, 59.0

# ---- the build's own camera (--holes --views; 2026-11-07, v101-seams). The view above looks along one ray, the screen's
# middle, in a parallel view: a piece the layers fix moves along Black 2's view direction (pearl_model_fix.VIEW) stays put
# there, and a gap it opens at its edge is seen only from the side. The DS camera is a perspective one that follows the
# player, so any place can come to any part of the screen, and the rays there come in at other angles: up to 25.8 degrees
# left and right (camera 0: projMtx[1][1] 2.7539, 4:3) and 20 degrees up and down. The Contest Hall lobby's back-wall seams
# (chunk 240), Route 210 North's cliff corner (63) and Valor Lakefront's (157) are such gaps. With --views every chunk is
# seen along the rays of the screen's four corners, the middles of its four sides and its middle (VIEW_SPOTS), at the pitch
# the build gives the chunk's zones (view_pitches: maplook 'tilt', the default; 59.06 on the overworld, each room its own
# Pearl camera's), each ray in a parallel view (the screen near that ray), with the DS's back-face culling (every Pearl
# land material draws its front side only), counting a hole only where the player can stand so that the camera shows it
# along that ray (seen(), below). A chunk's score is its worst ray; a hole counts on the tile it is on. The old view above
# stays as it was (its numbers are the ones in the notes before 1.0.1's v101-seams).
VIEW_COT = 2.75390625                                    # camera 0's projMtx[1][1]
VIEW_HALF = (math.degrees(math.atan(4 / 3 / VIEW_COT)), math.degrees(math.atan(1 / VIEW_COT)))   # (25.8, 20.0) degrees
VIEW_SPOTS = ((-1, 1), (0, 1), (1, 1), (-1, 0), (0, 0), (1, 0), (-1, -1), (0, -1), (1, -1))      # (x, y) on the screen


def view_dir(pitch, sx=0.0, sy=0.0):
    """Unit ray from the eye of a camera pitched `pitch` degrees down, looking north, through screen spot (sx, sy) in
    [-1, 1] (x right, y up)."""
    p = math.radians(pitch)
    f = np.array([0.0, -math.sin(p), -math.cos(p)]); u = np.array([0.0, math.cos(p), -math.sin(p)])
    d = f + sx * math.tan(math.radians(VIEW_HALF[0])) * np.array([1.0, 0.0, 0.0]) + sy * math.tan(math.radians(VIEW_HALF[1])) * u
    return d / np.linalg.norm(d)


_PITCHES = {}


def view_pitches(chunk):
    """The pitches (degrees) the build's cameras look at a chunk with: Pearl's overworld camera on the overworld
    (maplook.tilt_camera), each room zone's own Pearl camera (maplook.room_camera) where a room matrix holds it."""
    import maplook
    deg = lambda t: round(maplook.PEARL_CAMERAS[t][1] / 65536 * 360, 2)
    if not _PITCHES:
        world = json.load(open(version.data_path('sinnoh_world.json')))
        zones = json.load(open(os.path.join(version.WORLD_WORK, 'zones.json')))
        m0 = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', '000.json')))
        for row in m0['maps']:
            for c in row:
                if c != 0xffff: _PITCHES.setdefault(c, set()).add(deg(0))
        for pid, r in world['rooms']['zones'].items():
            m = json.load(open(os.path.join(version.WORLD_WORK, 'matrices', f"{r['pearl_matrix']:03d}.json")))
            for row in m['maps']:
                for c in row:
                    if c != 0xffff: _PITCHES.setdefault(c, set()).add(deg(zones[int(pid)]['camera']))
    return tuple(sorted(_PITCHES.get(chunk) or {deg(0)}))


def view_box(polys, d, margin=16.0):
    """(X0, X1, Y0, Y1): the screen rectangle (units) that holds polys seen along ray d, with a margin."""
    r = np.cross(d, (0.0, 1.0, 0.0)); r /= np.linalg.norm(r); u = np.cross(r, d)
    P = np.concatenate([q.P for q in polys]) if polys else np.zeros((1, 3))
    xs, ys = P @ r, P @ u
    return (float(xs.min()) - margin, float(xs.max()) + margin, float(ys.min()) - margin, float(ys.max()) + margin)


def coverage(polys, px=HOLE_PX, pitch=HOLE_PITCH, view=None, box=None, where=False, cull=False):
    """(covered (H, W) bool, front polygon index (H, W) int, -1 none) of polygons [Poly] seen along the camera: the
    screen's middle ray at `pitch` from the south, or along the ray `view` (a unit vector from the eye) in the screen
    rectangle `box` (view_box). where: also each pixel's point on its front polygon (H, W, 3), map units. cull: leave out
    the sides the DS doesn't draw (every Pearl land material draws its front only: a wall seen from behind is not there)."""
    d = view_dir(pitch) if view is None else np.asarray(view, float)
    r = np.cross(d, (0.0, 1.0, 0.0)); r /= np.linalg.norm(r); u = np.cross(r, d)
    X0, X1, Y0, Y1 = (-300.0, 300.0, -460.0, 460.0) if box is None else box
    W, H = int((X1 - X0) * px), int((Y1 - Y0) * px)
    depth = np.full((H, W), -np.inf); idx = np.full((H, W), -1, int)
    for k, q in enumerate(polys):
        if cull and not q.faces & (2 if float(q.n @ d) < 0 else 1): continue
        P = q.P
        sx = (P @ r - X0) * px
        sy = (Y1 - P @ u) * px
        dz = -(P @ d)                                       # toward the eye: bigger is nearer
        for a, b, cc in ((0, 1, 2), (0, 2, 3)) if len(P) == 4 else ((0, 1, 2),):
            xs, ys, ds = sx[[a, b, cc]], sy[[a, b, cc]], dz[[a, b, cc]]
            x0, x1 = max(0, int(math.floor(xs.min()))), min(W - 1, int(math.ceil(xs.max())))
            y0, y1 = max(0, int(math.floor(ys.min()))), min(H - 1, int(math.ceil(ys.max())))
            if x0 > x1 or y0 > y1: continue
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9: continue
            gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            gx = gx + 0.5; gy = gy + 0.5
            l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            dd = l0 * ds[0] + l1 * ds[1] + l2 * ds[2]
            reg_d = depth[y0:y1 + 1, x0:x1 + 1]; reg_i = idx[y0:y1 + 1, x0:x1 + 1]
            take = inside & (dd > reg_d)
            reg_d[take] = dd[take]; reg_i[take] = k
    if where:
        gy, gx = np.mgrid[0:H, 0:W]
        pts = ((X0 + (gx + 0.5) / px)[..., None] * r + (Y1 - (gy + 0.5) / px)[..., None] * u
               - np.where(np.isfinite(depth), depth, 0.0)[..., None] * d)
        return idx >= 0, idx, pts
    return idx >= 0, idx


def _water(model):
    """Material names of a model's water, Pearl's (b2_look.PEARL_WATER, by texture) or Black 2's (b2_look's records): left
    out of the holes measure, as b2_look rebuilds the water in layers of its own (a translucent surface over a base 2.5
    units under it, which the camera sees a little lower)."""
    import pearl_render, b2_look
    return {model.materials[i] for i, t in enumerate(pearl_render.bindings(model))
            if t[0] in b2_look.PEARL_WATER or model.materials[i] in b2_look.B2_MATERIALS}


_FIXED = {}         # (chunk, its neighbours) -> the fixed model's bytes, within one run (neighbours are asked again)


def fixed_bytes(chunk, around):
    import pearl_chunk
    key = (chunk, tuple(sorted(around.items())))
    if key not in _FIXED:
        _FIXED[key] = pearl_chunk.fix_model(chunk, around=around)[0]
    return _FIXED[key]


def holes(chunk, cell, views=None):
    """(hole area in units^2, {(tile x, tile z): units^2}) the fixes open in the chunk (see above). views: a list of rays
    [(pitch, unit vector from the eye)] (view_dir): only holes the camera can show along each ray count (seen()); the area
    is the worst ray's, a tile's the most any ray shows there; holes.last holds every ray's area, holes.unseen every ray's
    area before the seen() filter."""
    import pearl_chunk
    m, x, z = cell
    raw_m = pearl_chunk.pearl_model(chunk)
    fixed_m = pearl_mesh.Model(fixed_bytes(chunk, pearl_chunk.neighbours(m, x, z)))
    keep = lambda q, wet: q.alpha == 31 and not is_tree(q.mat) and q.mat not in wet
    raw = [q for q in load(raw_m) if keep(q, _water(raw_m))]
    fixed = [q for q in load(fixed_m) if keep(q, _water(fixed_m))]
    near = None
    def neighbours_drawn():
        out = []
        for (dx, dz), nc in pearl_chunk.neighbours(m, x, z).items():
            if not (0 <= z + dz < m['height'] and 0 <= x + dx < m['width']): continue
            nm = pearl_mesh.Model(fixed_bytes(nc, pearl_chunk.neighbours(m, x + dx, z + dz)))
            for q in load(nm):
                if keep(q, _water(nm)):
                    q.P = q.P + np.array([512.0 * dx, 0.0, 512.0 * dz]); out.append(q)
        return out
    best, tiles, every, unseen = 0.0, collections.Counter(), [], []
    for pitch, d in views or ((None, None),):
        box = None if d is None else view_box(raw, d)
        cull = d is not None                    # (--views: as the DS draws; the old view as before)
        cov_r, idx_r, *at = coverage(raw, view=d, box=box, where=cull, cull=cull)
        cov_f, _ = coverage(fixed, view=d, box=box, cull=cull)
        hole = cov_r & ~cov_f
        if hole.any() and any(np.abs(raw[k].P[:, [0, 2]]).max() > 256 for k in set(idx_r[hole].tolist())):
            # (a piece that overhangs the chunk's edge: Pearl's models reach 4-8 units into the neighbour, which draws
            # there too; a pixel the neighbours cover as the build fixes them is no hole: Spear Pillar's dhole, 2026-11-02)
            if near is None: near = neighbours_drawn()
            if near:
                hole &= ~coverage(near, view=d, box=box, cull=cull)[0]
        out, ys = collections.Counter(), collections.Counter()
        for k, p in zip(idx_r[hole], at[0][hole] if at else [None] * int(hole.sum())):
            ctr = raw[k].P.mean(0)
            if max(abs(ctr[0]), abs(ctr[2])) > 256: continue
            if p is not None: ctr = np.clip(p, -255.9, 255.9)       # (--views: the tile the hole is on)
            t = (int((ctr[0] + 256) // 16), int((ctr[2] + 256) // 16))
            out[t] += 1 / HOLE_PX ** 2; ys[t] += ctr[1]
        unseen.append(sum(out.values()))
        if d is not None:
            out = collections.Counter({t: v for t, v in out.items()
                                       if seen(chunk, cell, pitch, d, t, ys[t] / (v * HOLE_PX ** 2))})
        every.append(sum(out.values()))
        best = max(best, every[-1])
        for t, v in out.items(): tiles[t] = max(tiles[t], v)
    holes.last, holes.unseen = every, unseen
    return best, tiles


# ---- where the camera can be (--views). The DS camera follows the player: its target is the player's feet (4 units up) and
# its eye VIEW_DIST from there at the pitch (world_look's camera). A spot P seen along ray d has the target at
# T = P - t d - E (E: eye minus target), on the ground there; the hole is seen only when the player can stand near T: a
# walkable tile (Pearl's collision of the chunk or a neighbour) within VIEW_REACH tiles (half the step between two of the
# nine rays there).
# So a back wall's top is never seen along the screen's bottom rays (the target would stand behind the wall), and a hole
# the camera can't reach is not counted. Conservative otherwise: any walkable tile counts, reached or not, at any level.
VIEW_DIST, VIEW_REACH = 237.0, 4
_STAND = {}


def _stand(chunk, cell):
    """{(tile x, tile z) relative to the chunk's own: ground height} of the walkable tiles of the chunk and its 8 neighbours."""
    m, x, z = cell
    key = (chunk, id(m), x, z)
    if key not in _STAND:
        import pearl_chunk
        out = {}
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if not (0 <= x + dx < m['width'] and 0 <= z + dz < m['height']): continue
                c = m['maps'][z + dz][x + dx]
                if c == 0xffff: continue
                coll = json.load(open(os.path.join(LAND, f'{land_id(c):03d}.json')))['collision']
                tris = pearl_chunk.triangles(c)
                for tz in range(32):
                    for tx in range(32):
                        if coll[tz][tx]: continue
                        sf = pearl_chunk.surface(tris, tx * 16 - 248, tz * 16 - 248)
                        out[(tx + 32 * dx, tz + 32 * dz)] = sf[0] if sf else 0.0
        _STAND[key] = out
    return _STAND[key]


def seen(chunk, cell, pitch, d, tile, y):
    """Whether the camera can show the spot over tile (chunk's own tile coordinates) at height y along ray d."""
    stand = _stand(chunk, cell)
    p = math.radians(pitch)
    E = VIEW_DIST * np.array([0.0, math.sin(p), math.cos(p)])
    P = np.array([tile[0] * 16 - 248.0, y, tile[1] * 16 - 248.0])
    g = stand.get(tile, y)
    for _ in range(3):                                      # (the ground under the target: settle it)
        t = (P[1] - E[1] - (g + 4.0)) / d[1]
        if t <= 0: return False
        T = P - t * d - E
        at = (int(math.floor((T[0] + 256) / 16)), int(math.floor((T[2] + 256) / 16)))
        near = [stand[(at[0] + i, at[1] + j)] for i in range(-VIEW_REACH, VIEW_REACH + 1)
                for j in range(-VIEW_REACH, VIEW_REACH + 1) if (at[0] + i, at[1] + j) in stand]
        if not near: return False
        g = min(near, key=lambda h: abs(h - g))
    return True


def main_holes(args):
    """--holes [--views] [--world|--rooms] [--json=OUT] [CHUNK ...]: per chunk the units^2 of holes the fixes open
    (holes()), worst tiles; --views: from the build's own camera (VIEW_SPOTS at view_pitches), each chunk's worst ray;
    --json: every chunk's result (also those under HOLE_REPORT), for --compare."""
    world = json.load(open(version.data_path('sinnoh_world.json')))
    cells = cells_of(world)
    chunks = [int(a) for a in args if a.isdigit()]
    if not chunks:
        ow = sorted(int(c) for c in world['chunks']); rooms = sorted(int(c) for c in world['rooms']['chunks'])
        chunks = rooms if '--rooms' in args else ow if '--world' in args else ow + rooms
    views = '--views' in args
    total, bad, rows = 0.0, [], {}
    for c in chunks:
        rays = [(p, view_dir(p, sx, sy)) for p in view_pitches(c) for sx, sy in VIEW_SPOTS] if views else None
        area, tiles = holes(c, cells[c], rays)
        total += area
        row = dict(chunk=c, holes=round(area, 2), tiles=[[t[0], t[1], round(v, 2)] for t, v in tiles.most_common(6)])
        if views:
            row['views'] = [round(v, 2) for v in holes.last]; row['pitches'] = list(view_pitches(c))
            row['unseen'] = [round(v, 2) for v in holes.unseen]
        rows[c] = dict(row, tiles=[[t[0], t[1], round(v, 2)] for t, v in tiles.most_common()])
        if area >= HOLE_REPORT:
            bad.append(c)
            print(json.dumps(row), flush=True)
    print(f"{len(chunks)} chunks: holes the fixes open, seen from {'the build camera (worst ray)' if views else 'the camera'}: "
          f'{round(total, 1)} units^2; chunks with {HOLE_REPORT}+ units^2: {len(bad)} {bad[:30]}')
    out = next((a.split('=', 1)[1] for a in args if a.startswith('--json=')), None)
    if out: json.dump(dict(version=version.VERSION, views=views, chunks=rows), open(out, 'w'))
    return bad


HOLE_REPORT = 2.0           # units^2 (8 pixels at HOLE_PX 2) a chunk may have before it is listed: rounding at edges
HOLE_WORSE = 1.0            # units^2 (4 pixels) more than before, in a chunk's worst ray or in any one ray: worse (--compare)


def main_compare(args):
    """--compare OLD.json NEW.json [...]: per chunk, the holes of two --holes --json runs (several files of a side are
    joined with '+': a.json+b.json). Lists the chunks worse (HOLE_WORSE more in the worst ray, or in any one ray) and
    better, and the tiles that are worse (a tile's holes: the most any ray shows on it; only the 6 worst tiles of a chunk
    are kept by a run without --json); exit 1 when any chunk is worse (--places: or any tile)."""
    files = [a for a in args if not a.startswith('--')]
    def read(spec):
        rows = {}
        for f in spec.split('+'):
            rows.update({int(k): v for k, v in json.load(open(f))['chunks'].items()})
        return rows
    old, new = read(files[0]), read(files[1])
    worse, better, places = [], [], []
    for c in sorted(set(old) & set(new)):
        a, b = old[c], new[c]
        ta, tb = ({(t[0], t[1]): t[2] for t in r['tiles']} for r in (a, b))
        places += [(c, t, ta.get(t, 0.0), v) for t, v in sorted(tb.items()) if v - ta.get(t, 0.0) > HOLE_WORSE]
        ray = max((y - x for x, y in zip(a.get('views', [a['holes']]), b.get('views', [b['holes']]))), default=0.0)
        if b['holes'] - a['holes'] > HOLE_WORSE or ray > HOLE_WORSE:
            worse.append((c, a['holes'], b['holes'], round(ray, 2), b['tiles'][:3]))
        elif a['holes'] - b['holes'] > HOLE_WORSE:
            better.append((c, a['holes'], b['holes']))
    t_old = sum(old[c]['holes'] for c in set(old) & set(new)); t_new = sum(new[c]['holes'] for c in set(old) & set(new))
    print(f'{len(set(old) & set(new))} chunks in both; worst rays summed {round(t_old, 1)} -> {round(t_new, 1)} units^2; '
          f'missing: {sorted(set(old) ^ set(new))[:20]}')
    print(f'better ({len(better)}): ' + ', '.join(f'{c} {a}->{b}' for c, a, b in better))
    print(f'worse ({len(worse)}):')
    for c, a, b, r, t in worse:
        print(f'  {c}: {a} -> {b} (one ray up to +{r}); tiles {t}')
    print(f'places (tiles) worse by more than {HOLE_WORSE} units^2 in some ray, chunks better or worse ({len(places)}): '
          + ', '.join(f'{c} ({t[0]}, {t[1]}) {a}->{v}' for c, t, a, v in places))
    return 1 if worse or ('--places' in args and places) else 0


def main(args):
    if '--depth' in args: return main_depth(args)
    if '--compare' in args: return main_compare(args)
    if '--holes' in args: return main_holes(args)
    fixed = '--fixed' in args
    world = json.load(open(version.data_path('sinnoh_world.json')))
    cells = cells_of(world)
    chunks = [int(a) for a in args if a.isdigit()]
    if not chunks:
        ow = sorted(int(c) for c in world['chunks']); rooms = sorted(int(c) for c in world['rooms']['chunks'])
        chunks = rooms if '--rooms' in args else ow if '--world' in args else ow + rooms
    cache, tot = {}, collections.Counter()
    pairs, bpairs, rows = collections.Counter(), collections.Counter(), []
    worst = []
    for c in chunks:
        cache.setdefault('cells', {}).update(cells)
        r = check(c, cells[c], fixed, cache)
        for k in ('tj', 'tj_border', 'open', 'unbacked', 'border', 'fights'): tot[k] += r[k]
        for k, v in r['fight_pairs']: pairs[k] += v
        for k, v in r['border_pairs']: bpairs[k] += v
        rows.append(r)
        worst.append((r['size'], c))
        if len(chunks) <= 20 or r['size'] > CHUNK_LIMIT:
            print(json.dumps(r))
    worst.sort(reverse=True)
    print(f"{len(chunks)} chunks{' (fixed)' if fixed else ''}: T-junctions {tot['tj']} ({tot['tj_border']} at borders), "
          f"edges inside the ground {tot['open']} units, unbacked {tot['unbacked']}, border overlaps with other texels "
          f"{tot['border']} units^2, fighting pairs {tot['fights']}; largest chunks {worst[:4]} (limit {CHUNK_LIMIT})")
    print('fighting materials:', pairs.most_common(25))
    print('border overlaps:', bpairs.most_common(12))
    out = next((a.split('=', 1)[1] for a in args if a.startswith('--json=')), None)
    if out: json.dump(rows, open(out, 'w'), default=str)


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:]) == 1 else 0)
