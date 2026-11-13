"""Offline render of a version's title screen, both screens, 256x384 (2026-11-07, plat-music; notes/TITLE.md).

    PEARL_VERSION=platinum python3 b2tools/title_render.py OUT.png [--cam "x y z"] [--look "x y z"] [--frame N] [--pose MEMBER,FRAME]

Top: the version's logo and strip as pearl_title packs them (title_art.top_image, Black 2's PRESS START). Bottom: the
version's titledemo model drawn with Black 2's title camera (ov162 title.c TitleG3D_Init: a frustum of 30 degrees up and
down from the centre, 4:3, near 0.1; the model at the origin, unscaled; sLightSetups: light 0 (1, -1/2, -1) and lights 1-3
(-1, -1, -1), all white), on black, with Black 2's credit line in front. The camera is pearl_title's (VERSION_TITLE), or
--cam/--look (as PEARL_TITLE_CAM/LOOK).

The model: its bind pose, from its nodes (translation, rotation (3x3 or pivot-packed), scale) through the render commands
(NODEDESC with the matrix stack, MTX), its display lists' MTX_RESTORE and MTX_SCALE (Giratina's skinned model; Palkia and
Dialga have one node) and its own textures, texels with alpha blended over what is behind (the auras), opaque ones
depth-tested. The bind pose is what Black 2's title draws: pearl_title gives the actor one animation, the texture scroll
(Platinum's own title also poses Giratina by its joint animation, titledemo 2, which isn't loaded here). --frame N: the
texture scroll's frame (default: the frame where the aura is brightest, as the screenshots show it). --pose 2,0: pose the
model by titledemo member 2 (Platinum's giratina.nsbca) at frame 0 instead of its bind pose.
"""
import math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'patches')]
import numpy as np  # noqa: E402
import version, pearl_mesh, pearl_render, pearl_buildings, title_art  # noqa: E402
from gen4rom import Rom, narc_members  # noqa: E402

pearl_mesh.PARAMS.update({0x14: 1, 0x1B: 3})        # (only so Model() reads the shapes; matrices are followed here)
FX = 4096.0
DL_PARAMS = {0x00: 0, 0x10: 1, 0x11: 0, 0x12: 1, 0x13: 1, 0x14: 1, 0x15: 0, 0x16: 16, 0x17: 12, 0x18: 16, 0x19: 12,
             0x1A: 9, 0x1B: 3, 0x1C: 3, 0x20: 1, 0x21: 1, 0x22: 1, 0x23: 2, 0x24: 1, 0x25: 1, 0x26: 1, 0x27: 1, 0x28: 1,
             0x29: 1, 0x2A: 1, 0x2B: 1, 0x30: 1, 0x31: 1, 0x32: 1, 0x33: 1, 0x34: 32, 0x40: 1, 0x41: 0}
_s = pearl_mesh._s


LUT = ((4, 5, 7, 8), (3, 5, 6, 8), (3, 4, 6, 7), (1, 2, 7, 8), (0, 2, 6, 8), (0, 1, 6, 7), (1, 2, 4, 5), (0, 2, 3, 5),
       (0, 1, 3, 4))                                  # NNS_COMPACT_ROT_LUT (pokebw2 lib/nnsys/src/g3d/nsbca.c)


def pivot_rot(pivot, minus, revc, revd, a, b):
    """A rotation stored as its pivot (NNS: the element that is +-1) and two numbers, row-major (row vectors)."""
    e = [0.0] * 9
    e[pivot] = -1.0 if minus else 1.0
    lut = LUT[pivot]
    e[lut[0]] = a; e[lut[1]] = b
    e[lut[2]] = -b if revc else b
    e[lut[3]] = -a if revd else a
    return np.array(e).reshape(3, 3)


def srt(T, R, S):
    """NNS's node matrix (row vectors: v * S * R + T) as a 4x4 for column vectors."""
    L = np.eye(4)
    L[:3, :3] = R.T @ np.diag(S)
    L[:3, 3] = T
    return L


def node_srt(model):
    """[(T, R, S)] per node (NNSG3dResNodeData; R row-major for row vectors)."""
    d, base = model.data, model.m + 0x40
    out = []
    for at, _ in pearl_mesh._ndict(d, base):
        p = base + struct.unpack_from('<I', d, at)[0]
        flag, m00 = struct.unpack_from('<Hh', d, p)
        q = p + 4
        T = np.zeros(3); R = np.eye(3); S = np.ones(3)
        if not flag & 1:
            T = np.array(struct.unpack_from('<3i', d, q)) / FX; q += 12
        if not flag & 2:
            if flag & 8:
                A, B = (v / FX for v in struct.unpack_from('<2h', d, q)); q += 4
                R = pivot_rot((flag >> 4) & 15, flag & 0x100, flag & 0x200, flag & 0x400, A, B)
            else:
                vals = [m00] + list(struct.unpack_from('<8h', d, q)); q += 16
                R = np.array(vals, float).reshape(3, 3) / FX
        if not flag & 4:
            S = np.array(struct.unpack_from('<3i', d, q)) / FX; q += 24
        out.append((T, R, S))
    return out


def node_mats(model):
    return [srt(*x) for x in node_srt(model)]


def joint_pose(model, bca, frame=0):
    """[4x4 local matrix] per node at a whole frame of a BCA0 joint animation (pokebw2 lib/nnsys nsbca.c
    getJntSRTAnmResult_: identity, the node's own, a constant or the curve's value; no blending at a whole frame)."""
    base = node_srt(model)
    d = bca
    blk = struct.unpack_from('<I', d, 0x10)[0]
    (off, _), = pearl_mesh._ndict(d, blk + 8)
    a = blk + struct.unpack_from('<I', d, off)[0]
    assert d[a:a + 4] == b'J\0AC'
    nframes, nnodes, aflag, o3, o5 = struct.unpack_from('<HHIII', d, a + 4)
    frame = max(0, min(frame, nframes - 1))
    tags = struct.unpack_from(f'<{nnodes}H', d, a + 0x14)

    def index(info, f):
        if not info & 0xC0000000: return f
        last = (info & 0x1FFF0000) >> 16
        if info & 0x40000000:
            return (last >> 1) + 1 if (f & 1 and f > last) else f >> 1      # (odd frames: an average, not at f 0)
        return (last >> 2) + (f & 3) if (f & 3 and f > last) else f >> 2

    def rot_idx(r):
        if r & 0x8000:
            p = struct.unpack_from('<3h', d, a + o3 + 6 * (r & 0x7FFF))
            return pivot_rot(p[0] & 15, p[0] & 0x10, p[0] & 0x20, p[0] & 0x40, p[1] / FX, p[2] / FX)
        p = struct.unpack_from('<5h', d, a + o5 + 10 * (r & 0x7FFF))
        bits = p[4] & 7
        e = [0] * 9
        e[4] = p[4] >> 3
        bits = (bits << 3) | (p[0] & 7); e[0] = p[0] >> 3
        bits = (bits << 3) | (p[1] & 7); e[1] = p[1] >> 3
        bits = (bits << 3) | (p[2] & 7); e[2] = p[2] >> 3
        bits = (bits << 3) | (p[3] & 7); e[3] = p[3] >> 3
        bits &= 0x1FFF; e[5] = bits - 0x2000 if bits & 0x1000 else bits
        r0 = np.array(e[0:3], float) / FX; r1 = np.array(e[3:6], float) / FX
        return np.array([r0, r1, np.cross(r0, r1)])

    out = [srt(*x) for x in base]
    for k, toff in enumerate(tags):
        p = a + toff
        tag = struct.unpack_from('<I', d, p)[0]; p += 4
        node = tag >> 24
        if tag & 1:
            out[node] = np.eye(4); continue
        T, R, S = base[node]
        T, R, S = T.copy(), R.copy(), S.copy()
        if not tag & 6:
            for c, bit in enumerate((8, 0x10, 0x20)):
                if tag & bit:
                    T[c] = struct.unpack_from('<i', d, p)[0] / FX; p += 4
                else:
                    info, o = struct.unpack_from('<II', d, p); p += 8
                    i = index(info, frame)
                    T[c] = (struct.unpack_from('<h', d, a + o + 2 * i)[0] if info & 0x20000000 else
                            struct.unpack_from('<i', d, a + o + 4 * i)[0]) / FX
        elif tag & 2:
            T = np.zeros(3)
        if not tag & 0xC0:
            if tag & 0x100:
                R = rot_idx(struct.unpack_from('<I', d, p)[0] & 0xFFFF); p += 4
            else:
                info, o = struct.unpack_from('<II', d, p); p += 8
                R = rot_idx(struct.unpack_from('<H', d, a + o + 2 * index(info, frame))[0])
        elif tag & 0x40:
            R = np.eye(3)
        if not tag & 0x600:
            for c, bit in enumerate((0x800, 0x1000, 0x2000)):
                if tag & bit:
                    S[c] = struct.unpack_from('<i', d, p)[0] / FX
                else:
                    info, o = struct.unpack_from('<II', d, p)
                    i = index(info, frame)
                    S[c] = (struct.unpack_from('<h', d, a + o + 4 * i)[0] if info & 0x20000000 else
                            struct.unpack_from('<i', d, a + o + 8 * i)[0]) / FX
                p += 8
        elif tag & 0x200:
            S = np.ones(3)
        out[node] = srt(T, R, S)
    return out


def decode(model, joint_locals=None):
    """[(material, [(world positions (n, 3), uv (n, 2), colours or None, normals (n, 3) or None)])] per shape."""
    d = model.data
    locals_ = joint_locals or node_mats(model)
    stack, cur = {}, np.eye(4)
    world = {}
    i, end = model.m + model.osbc, model.m + model.omat
    pos_scale = model.pos_scale
    shape_mtx = {}
    while i < end:
        c = d[i]; op = c & 0x1F
        if op == 1: break
        if op == 6:
            node, parent, flags = d[i + 1], d[i + 2], d[i + 3]
            k = i + 4
            dest = src = None
            if c & 0x20: dest = d[k]; k += 1
            if c & 0x40: src = d[k]; k += 1
            if src is not None: cur = stack[src].copy()
            cur = cur @ locals_[node]
            world[node] = cur.copy()
            if dest is not None: stack[dest] = cur.copy()
            i = k; continue
        if op == 3: cur = stack[d[i + 1]].copy()
        if op == 5: shape_mtx.setdefault(d[i + 1], cur.copy())
        if op == 9:
            raise SystemExit('NODEMIX (envelopes): not followed here')
        i += {0: 1, 2: 3, 3: 2, 4: 2, 5: 2, 7: 2, 8: 2, 0xB: 1, 0xC: 3, 0xD: 3}.get(op, 1)
    out = []
    for k, (at, name) in enumerate(pearl_mesh._ndict(d, model.m + model.oshp)):
        p = model.m + model.oshp + struct.unpack_from('<I', d, at)[0]
        _, _, flags, off, ln = struct.unpack_from('<HHIII', d, p)
        M = shape_mtx.get(k, np.eye(4)) @ np.diag([pos_scale, pos_scale, pos_scale, 1])
        polys = []
        j, e = p + off, p + off + ln
        pos = [0, 0, 0]; st = [0, 0]; nrm = None; col = None; prim = None; verts = []
        def close():
            if prim is None: return
            for poly in pearl_mesh._group_polys(prim, verts):
                P = np.array([v[0] for v in poly]); UV = np.array([v[1] for v in poly], float)
                C = None if any(v[2] is None for v in poly) else [v[2] for v in poly]
                N = None if any(v[3] is None for v in poly) else np.array([v[3] for v in poly])
                polys.append((P, UV, C, N))
        while j < e:
            cmds = d[j:j + 4]; j += 4
            for cm in cmds:
                n = DL_PARAMS[cm]
                prm = struct.unpack_from(f'<{n}I', d, j) if n else (); j += 4 * n
                if cm == 0x14:
                    M = stack[prm[0] & 31].copy()
                elif cm == 0x1B:
                    sx, sy, sz = (struct.unpack('<i', struct.pack('<I', v))[0] / FX for v in prm)
                    M = M @ np.diag([sx, sy, sz, 1])
                elif cm == 0x20: col = prm[0] & 0x7FFF
                elif cm == 0x21:
                    v = prm[0]
                    nv = np.array([_s(v, 10) / 512, _s(v >> 10, 10) / 512, _s(v >> 20, 10) / 512])
                    nrm = M[:3, :3] @ nv
                    L = np.linalg.norm(nrm); nrm = nrm / L if L else nrm
                elif cm == 0x22: st = [_s(prm[0], 16) / 16, _s(prm[0] >> 16, 16) / 16]
                elif cm in (0x23, 0x24, 0x25, 0x26, 0x27, 0x28):
                    if cm == 0x23: pos = [_s(prm[0], 16), _s(prm[0] >> 16, 16), _s(prm[1], 16)]
                    elif cm == 0x24: pos = [_s(prm[0], 10) << 6, _s(prm[0] >> 10, 10) << 6, _s(prm[0] >> 20, 10) << 6]
                    elif cm == 0x25: pos = [_s(prm[0], 16), _s(prm[0] >> 16, 16), pos[2]]
                    elif cm == 0x26: pos = [_s(prm[0], 16), pos[1], _s(prm[0] >> 16, 16)]
                    elif cm == 0x27: pos = [pos[0], _s(prm[0], 16), _s(prm[0] >> 16, 16)]
                    else: pos = [_s(pos[q] + _s(prm[0] >> (10 * q), 10), 16) for q in range(3)]
                    w = M @ np.array([pos[0] / FX, pos[1] / FX, pos[2] / FX, 1.0])
                    verts.append((w[:3], st, col, nrm))
                elif cm == 0x40:
                    close(); prim = prm[0] & 3; verts = []
                elif cm == 0x41:
                    close(); prim = None; verts = []
        close()
        out.append((model.shapes[k].material, polys))
    return out


# Black 2's title lights (ov162 title.c sLightSetups): white, directions as fx16
B2_TITLE = dict(lights=[((31, 31, 31), (4095, -2047, -4095)), ((31, 31, 31), (-4095, -4095, -4095)),
                        ((31, 31, 31), (-4095, -4095, -4095)), ((31, 31, 31), (-4095, -4095, -4095))],
                mat=None, own=True)


class AlphaScene(pearl_render.Scene):
    """pearl_render.Scene with texel alpha blended (A3I5 / A5I3 / colour 0): alpha under 1/8 skipped, translucent texels
    blended without writing depth, opaque ones as Scene draws them."""

    def tri(self, S, UV, C, tex, wrap, alpha_mode, pid, xlu=1.0):
        if np.any(S[:, 2] < 1): return
        x0, x1 = int(max(0, math.floor(S[:, 0].min()))), int(min(self.W - 1, math.ceil(S[:, 0].max())))
        y0, y1 = int(max(0, math.floor(S[:, 1].min()))), int(min(self.H - 1, math.ceil(S[:, 1].max())))
        if x0 > x1 or y0 > y1: return
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px, py = xs + 0.5, ys + 0.5
        (ax, ay), (bx, by), (cx, cy) = S[0, :2], S[1, :2], S[2, :2]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: return
        l0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
        l1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
        l2 = 1 - l0 - l1
        inside = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not inside.any(): return
        w = 1 / S[:, 2]
        iw = l0 * w[0] + l1 * w[1] + l2 * w[2]
        b0, b1, b2 = l0 * w[0] / iw, l1 * w[1] / iw, l2 * w[2] / iw
        depth = 1 / iw
        zbuf = self.z[y0:y1 + 1, x0:x1 + 1]
        ok = inside & (depth < zbuf - 1e-4)
        if not ok.any(): return
        u = b0 * UV[0, 0] + b1 * UV[1, 0] + b2 * UV[2, 0]
        v = b0 * UV[0, 1] + b1 * UV[1, 1] + b2 * UV[2, 1]
        a = np.full(u.shape, xlu)
        if tex is not None:
            th, tw = tex.shape[:2]
            def wrapc(c, n, rep, flip):
                i = np.floor(c).astype(int)
                if not rep: return np.clip(i, 0, n - 1)
                if flip:
                    k = np.floor_divide(i, n); i = np.mod(i, n)
                    return np.where(k % 2 == 1, n - 1 - i, i)
                return np.mod(i, n)
            t = tex[wrapc(v, th, wrap[1], wrap[3]), wrapc(u, tw, wrap[0], wrap[2])].astype(float)
            a = a * t[..., 3] / 255
            tc = np.floor(t[..., :3] / 8)
        else:
            tc = np.full(u.shape + (3,), 31.0)
        ok &= a >= 1 / 8
        vc = b0[..., None] * C[0] + b1[..., None] * C[1] + b2[..., None] * C[2]
        out = ((tc + 1) * (vc + 1) - 1) / 32
        region = self.col[y0:y1 + 1, x0:x1 + 1]
        solid = ok & (a > 0.97)
        blend = ok & ~solid
        region[solid] = out[solid]; zbuf[solid] = depth[solid]
        self.pid[y0:y1 + 1, x0:x1 + 1][solid] = pid
        region[blend] = region[blend] * (1 - a[blend, None]) + out[blend] * a[blend, None]
        empty = blend & ~np.isfinite(zbuf)
        zbuf[empty] = 1e9                                  # (blended over the black backdrop: drawn, not empty)


# a polygon is front-facing when its corners run clockwise on screen (y down: a negative area); checked against Palkia's
# shot, where the culled back of the orb shows the face in front
FRONT_NEGATIVE = True


def draw(scene, model, tex, shapes, setup=B2_TITLE):
    info = pearl_render.bindings(model)
    order = sorted(range(len(shapes)), key=lambda k: ((info[shapes[k][0]][5] >> 16) & 31) < 31 if shapes[k][0] is not None else True)
    for k in order:
        mat, polys = shapes[k]
        if mat is None: continue
        tname, pname, teximg, diffamb, specemi, poly, flags = info[mat]
        alpha = (poly >> 16) & 31
        if alpha == 0: continue
        img = tex.get((tname, pname)) if tname else None
        wrap = ((teximg >> 16) & 1, (teximg >> 17) & 1, (teximg >> 18) & 1, (teximg >> 19) & 1)
        show = (poly >> 6) & 3                            # GX polygon attribute: bit 0 back faces, bit 1 front faces drawn
        for P, UV, C, N in polys:
            if poly & 15 and N is not None:
                Cc = np.array([pearl_render.light_colour(info[mat], n, setup) for n in N])
            elif C is not None:
                Cc = np.array([pearl_render._rgb(c) for c in C])
            else:
                Cc = np.array([pearl_render._rgb(diffamb & 0x7FFF)] * len(P))
            S = scene.project(P)
            area = sum(S[i, 0] * S[(i + 1) % len(S), 1] - S[(i + 1) % len(S), 0] * S[i, 1] for i in range(len(S)))
            front = (area < 0) == FRONT_NEGATIVE           # (screen y down)
            if not show & (2 if front else 1):
                continue
            for a, b, c in ((0, 1, 2), (0, 2, 3)) if len(P) == 4 else ((0, 1, 2),):
                scene.tri(S[[a, b, c]], UV[[a, b, c]], Cc[[a, b, c]], img, wrap, True, (poly >> 24) & 63, alpha / 31)


def srt_anim(bta):
    """{material name: (frames, [transT per frame])} of a BTA0's first texture SRT animation (SRT0, 'M\\0AT'): each
    material has 5 tracks (scale S, scale T, rotation, translation S, translation T) of 8 bytes: u16 frames, u8, u8 flag
    (0x20: constant, 0x10: fx16 values), u32 constant or offset (from the animation). Only translation T moves in
    these titles (the aura's scroll)."""
    blk = struct.unpack_from('<I', bta, 0x10)[0]
    assert bta[blk:blk + 4] == b'SRT0'
    (off, _), = pearl_mesh._ndict(bta, blk + 8)
    a = blk + struct.unpack_from('<I', bta, off)[0]
    assert bta[a:a + 4] == b'M\0AT'
    frames = struct.unpack_from('<H', bta, a + 4)[0]
    out = {}
    for e, name in pearl_mesh._ndict(bta, a + 8):
        nf, _, flag, val = struct.unpack_from('<HBBI', bta, e + 32)     # translation T
        if flag & 0x20:
            out[name] = (frames, [struct.unpack('<i', struct.pack('<I', val))[0] / FX] * frames)
        elif flag & 0x10:
            out[name] = (frames, [v / FX for v in struct.unpack_from(f'<{nf}h', bta, a + val)])
        else:
            out[name] = (frames, [v / FX for v in struct.unpack_from(f'<{nf}i', bta, a + val)])
    return out


def scroll(model, shapes, tex, bta, frame):
    """The shapes with the texture animation's V translation at `frame` added to their texture coordinates (in texels of
    each material's texture)."""
    anim = srt_anim(bta)
    info = pearl_render.bindings(model)
    out = []
    for mat, polys in shapes:
        name = model.materials[mat] if mat is not None else None
        if name in anim:
            frames, tt = anim[name]
            img = tex.get((info[mat][0], info[mat][1])) if info[mat][0] else None
            h = img.shape[0] if img is not None else 0
            dv = tt[frame % len(tt)] * h
            polys = [(P, UV + np.array([0.0, dv]), C, N) for P, UV, C, N in polys]
        out.append((mat, polys))
    return out


def bottom(cam, look, member_model, member_anim=None, frame=None, pose=None):
    t = narc_members(Rom(version.SOURCE_DUMP).read('demo/title/titledemo.narc'))
    bmd = t[member_model]
    model = pearl_mesh.Model(pearl_buildings.mdl_only(bmd))
    tex = pearl_render.textures(pearl_buildings.btx0_of(bmd))
    shapes = decode(model, joint_pose(model, t[pose[0]], pose[1]) if pose else None)
    picked = None
    if member_anim is not None:
        frames = srt_anim(t[member_anim])
        n = max(f for f, _ in frames.values()) if frames else 1
        if frame is None:                  # the frame where the aura is brightest (what the screenshots show)
            best = None
            for f in range(0, n, max(1, n // 24)):
                sc = AlphaScene(128, 96, cam, look, half=30.0)
                draw(sc, model, tex, scroll(model, shapes, tex, t[member_anim], f))
                v = float(np.nan_to_num(sc.col).sum())
                if best is None or v > best[0]: best = (v, f)
            frame = best[1]
        picked = frame
        shapes = scroll(model, shapes, tex, t[member_anim], frame)
    sc = AlphaScene(256, 192, cam, look, half=30.0)
    draw(sc, model, tex, shapes)
    im = sc.image(None, (0, 0, 0)).convert('RGBA')
    return im, model, shapes, picked


def credit_line():
    """Black 2's 'Developed by GAME FREAK inc.' layer (a/0/2/6 files 8/9/10) as RGBA, colour 0 clear."""
    from PIL import Image
    e = title_art.title_entries()
    _, tiles = title_art.ncgr_tiles(title_art.lz10_decompress(e[9]))
    w, h, _, ents = title_art.nscr_entries(title_art.lz10_decompress(e[10]))
    cols = title_art.nclr_colours(e[8])
    img = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
    pix = img.load()
    for ty in range(min(h // 8, 24)):
        for tx in range(min(w // 8, 32)):
            ent = ents[ty * (w // 8) + tx]
            tile, hf, vf, pal = ent & 0x3FF, (ent >> 10) & 1, (ent >> 11) & 1, ent >> 12
            if tile >= len(tiles): continue
            t = tiles[tile]
            for y in range(8):
                for x in range(8):
                    v = t[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                    if v:
                        c = cols[pal * 16 + v] if pal * 16 + v < len(cols) else (255, 0, 255)
                        pix[tx * 8 + x, ty * 8 + y] = tuple(c) + (255,)
    return img


def main(argv):
    from PIL import Image
    import pearl_title
    out = argv[0]
    opt = {argv[i]: argv[i + 1] for i in range(1, len(argv) - 1) if argv[i].startswith('--')}
    vt = pearl_title.VERSION_TITLE
    cam = tuple(float(v) for v in opt.get('--cam', vt['camera']).split())
    look = tuple(float(v) for v in opt.get('--look', vt['look']).split())
    art = os.path.join(title_art.DATA, vt['art'])
    logo, pal, _ = title_art.load_indexed(os.path.join(art, 'logo.png'))
    strip, _, _ = title_art.load_indexed(os.path.join(art, 'strip.png'))
    top = title_art.top_image(logo, strip, pal)
    pose = tuple(int(v) for v in opt['--pose'].split(',')) if '--pose' in opt else None
    bot, model, shapes, frame = bottom(cam, look, vt['model'], vt['anim'], int(opt['--frame']) if '--frame' in opt else None,
                                       pose)
    bot = bot.convert('RGB')
    cl = credit_line()
    bot.paste(cl, (0, 0), cl)
    full = Image.new('RGB', (256, 384))
    full.paste(top, (0, 0)); full.paste(bot, (0, 192))
    full.save(out)
    P = np.concatenate([p[0] for _, ps in shapes for p in ps])
    print(out, f'camera {cam} -> {look}; texture scroll frame {frame}; model box {P.min(0).round(1)} .. {P.max(0).round(1)}, centre '
               f'{((P.min(0) + P.max(0)) / 2).round(1)}')


if __name__ == '__main__':
    main(sys.argv[1:])
