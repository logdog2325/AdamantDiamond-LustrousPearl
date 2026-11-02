"""Logo drafts for Pokémon Lustrous Pearl and Pokémon Adamant Diamond (notes/TITLE.md): Black 2's "Pokémon" wordmark and
crystal strip, new lettering below it. Unlike title_art.py's earlier drafts every pixel here is either on or off:
letters are drawn from title_art's polygons, thresholded to the 1x grid (no averaged edges), so they stay sharp at
the DS's 256x192. Shading goes by whole rows and whole edge pixels.

    python3 title_lustrous.py OUT     draw all drafts of both versions into folder OUT, check them against the format's
                                      limits, write mockups (1x, 2x) and the contact sheet OUT/title_drafts.png
    python3 title_lustrous.py use C   draw draft C (the user's pick, 2026-11-01) into data/title/ (Lustrous Pearl) and
                                      data/title/diamond/ (Adamant Diamond), as patches/pearl_title.py reads them

Limits checked (title_art.pack_top, patches/pearl_title.py): 8 bpp, one 256-colour palette shared with the strip, at
most 512 tiles for logo + strip together, a/0/2/6 no larger than Black 2's.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import numpy as np                  # noqa: E402
import title_art as ta              # noqa: E402

W, H = 256, 192
SS = 8

# Each version's colours. orb: the item's own look (pokeplatinum res/items/icons lustrous_orb, adamant_orb): a pale
# glass sphere; a faceted ice-blue gem.
THEMES = {
    'pearl': dict(
        chrome=[(0, (255, 250, 252)), (.22, (255, 214, 232)), (.47, (248, 150, 196)), (.49, (196, 52, 124)),
                (.70, (226, 84, 150)), (.90, (250, 140, 190)), (1, (255, 196, 222))],
        gloss_top=(255, 255, 255), gloss_mid=(255, 226, 238), gloss_low=(246, 150, 194), gloss_end=(216, 84, 146),
        dark=(52, 6, 36), rim=((176, 72, 128), (116, 36, 84)), hi=(255, 255, 255), lo=(140, 30, 92),
        plaque=[(0, (150, 34, 96)), (.5, (102, 18, 66)), (1, (66, 10, 44))], plaque_rim=(255, 214, 232),
        text=(255, 252, 253), text_low=(255, 214, 232), sparkle=(255, 255, 255), glow=(255, 150, 200),
        strip={'A': (115, 1.0, 1.0), 'B': (115, .45, 1.05), 'C': (115, .75, 1.0)}),
    'diamond': dict(
        chrome=[(0, (250, 253, 255)), (.22, (208, 228, 248)), (.47, (136, 176, 228)), (.49, (44, 84, 164)),
                (.70, (72, 118, 196)), (.90, (128, 172, 228)), (1, (190, 222, 246))],
        gloss_top=(255, 255, 255), gloss_mid=(214, 232, 250), gloss_low=(130, 172, 226), gloss_end=(70, 110, 180),
        dark=(6, 14, 50), rim=((84, 112, 164), (44, 64, 112)), hi=(255, 255, 255), lo=(24, 50, 112),
        plaque=[(0, (58, 84, 136)), (.5, (34, 52, 98)), (1, (18, 28, 64))], plaque_rim=(204, 222, 244),
        text=(252, 254, 255), text_low=(204, 224, 248), sparkle=(255, 255, 255), glow=(130, 180, 240),
        strip={'A': (0, .8, 1.0), 'B': (0, .45, 1.0), 'C': (0, .6, .95)}),
}
WORDS = {'pearl': ('LUSTROUS', 'PEARL'), 'diamond': ('ADAMANT', 'DIAMOND')}
VERSION_NAME = {'pearl': 'Pokémon Lustrous Pearl', 'diamond': 'Pokémon Adamant Diamond'}


# ---------------------------------------------------------------------------------------------- crisp letters
def glyph(ch, w, h, t, m0, m1):
    if ch == 'T':
        return [([(0, 0), (w, 0), (w, t), (w / 2 + t / 2, t), (w / 2 + t / 2, h), (w / 2 - t / 2, h), (w / 2 - t / 2, t),
                  (0, t)], 'add', {})]
    return ta.glyph(ch, w, h, t, m0, m1)


def line_width(text, widths, gap, space=0):
    return sum(space if c == ' ' else widths[c] for c in text) + gap * (len(text) - 1)


def word(text, x, y, widths, h, t, m0, m1, gap, r=1.5, r_in=0.0, style='cut', space=0):
    """Bool mask (192, 256) of `text` with its top-left at integer (x, y): polygons thresholded to whole pixels."""
    from PIL import Image, ImageDraw
    x0, x1 = x - 2, x + line_width(text, widths, gap, space) + 2
    img = Image.new('L', ((x1 - x0) * SS, (h + 4) * SS), 0)
    d = ImageDraw.Draw(img)
    cx = x
    for ch in text:
        if ch == ' ':
            cx += space + gap
            continue
        for pts, kind, over in glyph(ch, widths[ch], h, t, m0, m1):
            r_o = r * (.5 if kind == 'cut' else 1)
            pts = ta.corner_poly(pts, r_o, r_in, style, over)
            d.polygon([((cx + px - x0) * SS, (py + 2) * SS) for px, py in pts], fill=255 if kind == 'add' else 0)
        cx += widths[ch] + gap
    a = np.asarray(img, 'float32') / 255
    hh, ww = a.shape
    a = a.reshape(hh // SS, SS, ww // SS, SS).mean((1, 3)) >= .5
    m = np.zeros((H, W), bool)
    m[y - 2:y - 2 + a.shape[0], x0:x1] = a
    return m


def centred(text, widths, gap, cx=128, space=0):
    return cx - line_width(text, widths, gap, space) // 2


def dilate(m, n=1, diag=True):
    for i in range(n):
        o = m.copy()
        o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        if diag:
            o[1:, 1:] |= m[:-1, :-1]; o[:-1, :-1] |= m[1:, 1:]; o[1:, :-1] |= m[:-1, 1:]; o[:-1, 1:] |= m[1:, :-1]
        m = o
    return m


def erode(m, n=1):
    return ~dilate(~m, n)


def fill_holes(m):
    from collections import deque
    seen = np.zeros_like(m); q = deque()
    for y in range(H):
        q += [(y, 0), (y, W - 1)]
    for x in range(W):
        q += [(0, x), (H - 1, x)]
    while q:
        y, x = q.popleft()
        if 0 <= y < H and 0 <= x < W and not seen[y, x] and not m[y, x]:
            seen[y, x] = True
            q += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return ~seen


def silhouette(m, gap):
    """The word as one solid shape: gaps between letters (up to `gap` px) and counters closed. Rims go around this, so
    a rim never eats a counter or draws a line between two letters."""
    return fill_holes(erode(dilate(m, gap // 2 + 1), gap // 2 + 1) | m)


def shift(m, dx, dy):
    o = np.zeros_like(m)
    ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
    xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
    o[ys, xs] = m[yd, xd]
    return o


def rows(top, height, stops):
    """Colours per screen row, (192, 1, 3): gradient `stops` over top..top+height, sampled at whole rows."""
    y = (np.arange(H, dtype='float32') + .5 - top) / height
    return ta.ramp(y, stops)[:, None, :]


class Canvas:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3), 'float32')
        self.on = np.zeros((H, W), bool)

    def put(self, mask, colour):
        c = np.broadcast_to(np.asarray(colour, 'float32'), self.rgb.shape)
        self.rgb[mask] = c[mask]
        self.on |= mask


def chrome_word(cv, th, m, top, height, gap, light_rim=True):
    """Black 2's polished metal: dark horizon in the middle, a highlight along the upper-left edges, the far edges
    darker; a dark line and a pale rim around the whole word."""
    sil = silhouette(m, gap)
    dark = dilate(sil, 1)
    if light_rim:
        rim = dilate(dark, 1)
        c0, c1 = th['rim']
        cv.put(rim, rows(top, height, [(0, c0), (1, c1)]))
    cv.put(dark, th['dark'])
    cv.put(m, rows(top, height, th['chrome']))
    cv.put(m & ~shift(m, 1, 1), th['hi'])
    cv.put(m & ~shift(m, -1, -1) & shift(m, 1, 1), th['lo'])


def gloss_word(cv, th, m, top, height, gap):
    """A pearl's gloss: white above a hard gloss line, the version's colour below; a dark rim and a thin coloured one
    around the whole word (a pale rim here read as a second, hollow letter at 1x)."""
    sil = silhouette(m, gap)
    dark = dilate(sil, 1)
    c0, c1 = th['rim']
    cv.put(dilate(dark, 1), rows(top, height, [(0, c0), (1, c1)]))
    cv.put(dark, th['dark'])
    mid = height * .5
    stops = [(0, th['gloss_top']), (.49, th['gloss_mid']), (.5, th['gloss_low']), (1, th['gloss_end'])]
    cv.put(m, rows(top, height, stops))
    cv.put(m & ~shift(m, -1, -1) & shift(m, 1, 1) & (np.arange(H)[:, None] > top + mid), th['lo'])


def flat_word(cv, th, m, top, height, gap):
    """Plain white letters with a dark rim, for the plaque."""
    cv.put(dilate(m, 1), th['dark'])
    cv.put(m, rows(top, height, [(0, th['text']), (.55, th['text']), (.56, th['text_low']), (1, th['text_low'])]))


# ---------------------------------------------------------------------------------------------- ornaments
def circle(cx, cy, r):
    yy, xx = np.mgrid[0:H, 0:W].astype('float32')
    return np.hypot(xx + .5 - cx, yy + .5 - cy) <= r


def sparkle(cv, x, y, size, colour):
    """A four-point star on the pixel grid."""
    m = np.zeros((H, W), bool)
    for k in range(-size, size + 1):
        m[y, x + k] = True; m[y + k, x] = True
    for k in range(-(size // 3), size // 3 + 1):
        m[y + k, x - (size // 3 - abs(k))] = True; m[y + k, x + (size // 3 - abs(k))] = True
    cv.put(m, colour)


def lustrous_orb(cv, th, cx, cy, r):
    """The Lustrous Orb: a pale pink-white glass sphere, banded (whole colours, no averaged edge), an aqua sheen at the
    lower right as on its item icon, a hard highlight at the upper left."""
    yy, xx = np.mgrid[0:H, 0:W].astype('float32')
    dx, dy = (xx + .5 - cx) / r, (yy + .5 - cy) / r
    d = np.hypot(dx, dy)
    on = d <= 1
    # light from the upper left, a darker rim all around
    t = np.clip(.72 - .34 * (dx + dy) - .34 * d ** 3, 0, 1)
    bands = np.floor(t * 7) / 7
    col = ta.ramp(bands, [(0, (206, 128, 176)), (.3, (240, 178, 212)), (.6, (255, 222, 236)), (1, (255, 248, 250))])
    cv.put(dilate(on, 2), th['dark'])
    cv.put(dilate(on, 1) & ~on, th['glow'])
    cv.put(on, col)
    sheen = on & (np.hypot(dx - .10, dy - .06) > .80) & (dx + dy > .55)
    cv.put(sheen, (176, 226, 240))
    sheen2 = on & (np.hypot(dx - .10, dy - .06) > .68) & (np.hypot(dx - .10, dy - .06) <= .80) & (dx + dy > .75)
    cv.put(sheen2, (214, 236, 244))
    hl = on & (((dx + .36) / .30) ** 2 + ((dy + .40) / .18) ** 2 <= 1)
    cv.put(hl, (255, 255, 255))
    cv.put(on & (np.hypot(dx + .02, dy + .58) <= .07), (255, 255, 255))


def adamant_orb(cv, th, cx, cy, r):
    """The Adamant Orb: a cut gem in ice blue and steel (its item icon), hard-edged facets."""
    import math
    from PIL import Image, ImageDraw
    n = 8
    outer = [(cx + r * math.cos(math.pi * (k + .5) * 2 / n), cy + r * math.sin(math.pi * (k + .5) * 2 / n))
             for k in range(n)]
    inner = [(cx - r * .1 + r * .52 * math.cos(math.pi * (k + .5) * 2 / n),
              cy - r * .1 + r * .52 * math.sin(math.pi * (k + .5) * 2 / n)) for k in range(n)]
    def poly(pts):
        img = Image.new('L', (W * SS, H * SS), 0)
        ImageDraw.Draw(img).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        a = np.asarray(img, 'float32') / 255
        return a.reshape(H, SS, W, SS).mean((1, 3)) >= .5
    on = poly(outer)
    cv.put(dilate(on, 2), th['dark'])
    cv.put(dilate(on, 1) & ~on, th['glow'])
    shades = [(120, 160, 214), (92, 132, 196), (124, 164, 218), (168, 200, 238), (218, 236, 252), (240, 250, 255),
              (206, 228, 250), (150, 186, 230)]
    for k in range(n):
        cv.put(poly([outer[k], outer[(k + 1) % n], inner[(k + 1) % n], inner[k]]) & on, shades[k])
    cv.put(poly(inner) & on, (196, 222, 248))
    cv.put(poly([inner[4], inner[5], inner[6], (cx - r * .1, cy - r * .1)]) & on, (244, 251, 255))
    cv.put(poly([inner[0], inner[1], inner[2], (cx - r * .1, cy - r * .1)]) & on, (150, 188, 232))


ORB = {'pearl': lustrous_orb, 'diamond': adamant_orb}


# ---------------------------------------------------------------------------------------------- the drafts
def fit(widths, keys, scale):
    return {k: max(4, int(round(widths[k] * scale))) for k in keys}


BASE = dict(A=21, D=19, E=18, I=6, L=17, M=24, N=20, O=20, P=19, R=20, S=20, T=18, U=20)


def draft_a(version):
    """Chrome stack: the small word over the big one, both in Black 2's polished metal, two sparkles. The current
    title's look, grown to fit a second line."""
    th = THEMES[version]; cv = Canvas()
    w1, w2 = WORDS[version]
    # first line: as wide as the wordmark; second: the big one
    keys = set(w1)
    s = (196 - 3 * (len(w1) - 1)) / sum(BASE[c] for c in w1)
    wd1 = fit(BASE, keys, s)
    y1, h1 = 103, 19
    m1 = word(w1, centred(w1, wd1, 3), y1, wd1, h1, 5, 8, 11, 3, r=1.5)
    s2 = (150 if version == 'pearl' else 186) / (sum(BASE[c] for c in w2) + 3 * (len(w2) - 1))
    wd2 = fit(BASE, set(w2), max(s2, 1.0) * (1.25 if version == 'pearl' else 1))
    y2, h2 = 126, 26
    x2 = centred(w2, wd2, 4)
    m2 = word(w2, x2, y2, wd2, h2, 7, 11, 15, 4, r=2.5)
    chrome_word(cv, th, m2, y2, h2, 4)
    chrome_word(cv, th, m1, y1, h1, 3)
    x2r = x2 + line_width(w2, wd2, 4)
    sparkle(cv, x2 - 7, y2 + 8, 6, th['sparkle'])
    sparkle(cv, x2r + 7, y2 + h2 - 8, 4, th['sparkle'])
    return cv


def draft_b(version):
    """Orb emblem: the version's orb large at the left, the two words as a block beside it, both lines the same width,
    pearl-gloss letters with a white rim."""
    th = THEMES[version]; cv = Canvas()
    w1, w2 = WORDS[version]
    orb_cx, orb_cy, orb_r = 38, 129, 24
    block_x, block_w = 70, 174
    def widths_for(text, gap):
        s = (block_w - gap * (len(text) - 1)) / sum(BASE[c] for c in text)
        wd = fit(BASE, set(text), s)
        return wd
    wd1 = widths_for(w1, 2)
    wd2 = widths_for(w2, 3)
    y1, h1 = 104, 19
    y2, h2 = 127, 24
    m1 = word(w1, block_x + (block_w - line_width(w1, wd1, 2)) // 2, y1, wd1, h1, 5, 8, 11, 2, r=2.0, style='round')
    m2 = word(w2, block_x + (block_w - line_width(w2, wd2, 3)) // 2, y2, wd2, h2, 6, 10, 14, 3, r=3.0, style='round')
    gloss_word(cv, th, m2, y2, h2, 3)
    gloss_word(cv, th, m1, y1, h1, 2)
    ORB[version](cv, th, orb_cx, orb_cy, orb_r)
    return cv


def draft_c(version):
    """Plaque: the whole name on one line, white block letters on a dark plaque with a pale rim; Pearl: a string of
    pearls with the orb hanging below it; Diamond: a string of small cut diamonds with the gem."""
    th = THEMES[version]; cv = Canvas()
    w1, w2 = WORDS[version]
    text = f'{w1} {w2}'
    limit, gap, space = 232, 2, 7
    s = (limit - gap * (len(text) - 1) - space) / sum(BASE[c] for c in text if c != ' ')
    wd = fit(BASE, set(text.replace(' ', '')), s)
    h, y = 17, 109
    x = centred(text, wd, gap, space=space)
    tw = line_width(text, wd, gap, space)
    m = word(text, x, y, wd, h, 4, 7, 10, gap, r=1.5, space=space)
    # the plaque: chamfered ends
    px0, px1, py0, py1 = x - 6, x + tw + 6, y - 6, y + h + 6
    from PIL import Image, ImageDraw
    def poly(pts):
        img = Image.new('L', (W, H), 0)
        ImageDraw.Draw(img).polygon(pts, fill=255)
        return np.asarray(img) > 127
    c = 6
    pl = poly([(px0 + c, py0), (px1 - c, py0), (px1, py0 + c), (px1, py1 - c), (px1 - c, py1), (px0 + c, py1),
               (px0, py1 - c), (px0, py0 + c)])
    # the string hanging under the plaque, with the orb in the middle
    pearl = np.zeros((H, W), bool); hi = np.zeros((H, W), bool)
    cy0, sag = py1 + 2, 11
    crown = np.zeros((H, W), bool); pavilion = np.zeros((H, W), bool)
    for k in range(-12, 13):
        if abs(k) < 3: continue
        px = 128 + k * 8
        py = cy0 + sag * (1 - (k / 12) ** 2)
        if version == 'diamond':       # a cut stone seen from the side: flat table, crown, pavilion down to a point
            q, r = int(round(px)), int(round(py))
            crown |= poly([(q - 2, r - 3), (q + 2, r - 3), (q + 3, r - 1), (q + 3, r), (q - 3, r), (q - 3, r - 1)])
            pavilion |= poly([(q - 3, r + 1), (q + 3, r + 1), (q, r + 4)])
            hi |= poly([(q - 1, r - 2), (q, r - 2), (q, r - 1), (q - 1, r - 1)])
        else:
            pearl |= circle(px, py, 3.2)
            hi |= circle(px - 1, py - 1, 1.0)
    if version == 'diamond':
        cv.put(dilate(crown | pavilion, 1), th['dark'])
        cv.put(crown, th['gloss_mid'])
        cv.put(pavilion, th['gloss_low'])
    else:
        cv.put(dilate(pearl, 1), th['dark'])
        cv.put(pearl, th['gloss_mid'])
        cv.put(pearl & shift(~pearl, -1, -1), th['gloss_low'])
    cv.put(hi, (255, 255, 255))
    cv.put(dilate(dilate(pl, 1), 1), th['dark'])
    cv.put(dilate(pl, 1), th['plaque_rim'])
    cv.put(pl, rows(py0, py1 - py0, th['plaque']))
    flat_word(cv, th, m, y, h, gap)
    ORB[version](cv, th, 128, cy0 + sag + 1, 9)
    sparkle(cv, px0 + 3, py0 + 1, 5, th['sparkle'])
    sparkle(cv, px1 - 3, py1 - 2, 4, th['sparkle'])
    return cv


DRAFTS = {'A': draft_a, 'B': draft_b, 'C': draft_c}
BLURB = {'A': 'Chrome stack', 'B': 'Orb emblem', 'C': 'Plaque and string of pearls'}


# ---------------------------------------------------------------------------------------------- composing and checks
def compose(version, key):
    """-> (logo, strip, palette) as title_art.pack_top takes them; every colour exact in BGR555."""
    e = ta.title_entries()
    logo0, strip0, pal0 = ta.original_top(e)
    pal = [ta.BACKDROP] + [(0, 0, 0)] * 255
    dh, ds, dv = THEMES[version]['strip'][key]
    for i in ta.STRIP_SLOTS:
        pal[i] = ta.tint(pal0[i], dh, ds, dv)
    free = [i for i in range(1, 256) if i not in ta.STRIP_SLOTS]
    logo = bytearray(W * H)
    wm = ta.wordmark(logo0); remap = {}
    for (x, y), v in sorted(wm.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if v not in remap:
            remap[v] = free.pop(0); pal[remap[v]] = pal0[v]
        logo[y * W + x + ta.WORDMARK_DX] = remap[v]
    cv = DRAFTS[key](version)
    ys, xs = np.nonzero(cv.on)
    px = [ta.to555(tuple(int(round(float(v))) for v in cv.rgb[y, x])) for y, x in zip(ys, xs)]
    uniq = sorted(set(px)); count = {u: 0 for u in uniq}
    for p in px:
        count[p] += 1
    cents, lab = ta.quantize(uniq, [count[u] for u in uniq], len(free))
    for j, c in enumerate(cents):
        pal[free[j]] = c
    look = {u: free[l] for u, l in zip(uniq, lab)}
    for (y, x), p in zip(zip(ys, xs), px):
        logo[y * W + x] = look[p]
    return bytes(logo), strip0, pal, dict(colours=len(uniq), free=len(free))


def limits(logo, strip, pal):
    """Tile count and a/0/2/6's size change against Black 2's (patches/pearl_title.py stops the build if it grows)."""
    top, n = ta.pack_top(logo, strip, pal)
    e = ta.title_entries()
    grow = sum((len(v) + 3) // 4 * 4 - (len(e[k]) + 3) // 4 * 4 for k, v in top.items())
    return n, grow


def bottom_screen(version):
    """The bottom screen for the mockup: the real Palkia shot (DeSmuME, current camera, title_test/tune_D); Diamond's
    Dialga has never been rendered, so its bottom shows only the credit line."""
    from PIL import Image
    shot = Image.open(os.path.join(ROOT_MAIN, 'work', 'title_test', 'tune_D.png')).convert('RGB')
    if version == 'pearl':
        return shot
    a = np.array(shot)
    grey = (a.max(2).astype(int) - a.min(2).astype(int)) < 30       # the credit's white and greys, not Palkia's feet
    a[~grey] = 0
    a[:176] = 0
    return Image.fromarray(a)


ROOT_MAIN = os.path.expanduser('~/Documents/GitHub/PearlB2')


def main(out):
    from PIL import Image, ImageDraw
    os.makedirs(out, exist_ok=True)
    sheet_rows = []
    for key in DRAFTS:
        row = {}
        for version in THEMES:
            logo, strip, pal, info = compose(version, key)
            n, grow = limits(logo, strip, pal)
            d = os.path.join(out, 'drafts', f'{version}_{key}')
            ta.save_indexed(os.path.join(d, 'logo.png'), logo, pal)
            ta.save_indexed(os.path.join(d, 'strip.png'), strip, pal)
            top = ta.top_image(logo, strip, pal)
            full = Image.new('RGB', (W, H * 2))
            full.paste(top, (0, 0)); full.paste(bottom_screen(version), (0, H))
            base = os.path.join(out, f'mock_{version}_{key}')
            full.save(base + '.png')
            full.resize((W * 2, H * 4), Image.NEAREST).save(base + '_2x.png')
            row[version] = (full, top)
            print(f'{key} {version}: {info["colours"]} colours ({info["free"]} free slots), {n}/512 tiles, '
                  f'a/0/2/6 {grow:+d} bytes vs Black 2')
            if n > 512: raise SystemExit('too many tiles')
            if info['colours'] > info['free']: print('  quantized')
        sheet_rows.append((key, row))
    gap, label = 12, 18
    sw = W * 2 + W * 2 + gap * 4
    sh = (H * 2 + label + gap) * len(sheet_rows) + gap
    sheet = Image.new('RGB', (sw, sh), (34, 34, 38))
    d = ImageDraw.Draw(sheet)
    y = gap
    for key, row in sheet_rows:
        d.text((gap, y), f'Draft {key}: {BLURB[key]}  (1x: Lustrous Pearl, Adamant Diamond; 2x top: Lustrous Pearl)',
               fill=(235, 235, 235))
        y += label
        sheet.paste(row['pearl'][0], (gap, y))
        sheet.paste(row['diamond'][0], (gap * 2 + W, y))
        sheet.paste(row['pearl'][1].resize((W * 2, H * 2), Image.NEAREST), (gap * 3 + W * 2, y))
        y += H * 2 + gap
    sheet.save(os.path.join(out, 'title_drafts.png'))
    print(os.path.join(out, 'title_drafts.png'), sheet.size)


def use(key):
    for ver, sub in (('pearl', ''), ('diamond', 'diamond')):
        logo, strip, pal, _ = compose(ver, key)
        d = os.path.join(ta.DATA, sub)
        ta.save_indexed(os.path.join(d, 'logo.png'), logo, pal)
        ta.save_indexed(os.path.join(d, 'strip.png'), strip, pal)
        print(f'{os.path.relpath(d, ROOT)}: {VERSION_NAME[ver]}, draft {key}: {limits(logo, strip, pal)[0]}/512 tiles')
    open(os.path.join(ta.DATA, 'CHOSEN'), 'w').write(f'lustrous {key}\n')


if __name__ == '__main__':
    if sys.argv[1] == 'use':
        use(sys.argv[2])
    else:
        main(sys.argv[1])
