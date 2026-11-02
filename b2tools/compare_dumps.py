"""Compare two NDS dumps file by file: which NitroFS files, NARC members and code files differ (notes/DIAMOND.md).

    python3 compare_dumps.py PEARL.nds DIAMOND.nds OUT.json
"""
import hashlib, json, struct, sys


def files(rom):
    """{path: bytes} of the NitroFS, plus arm9, arm7, the overlay tables, the overlays and the banner."""
    u32 = lambda o: struct.unpack_from('<I', rom, o)[0]
    fnt, fat = u32(0x40), u32(0x48)
    def body(i):
        a, b = struct.unpack_from('<II', rom, fat + 8 * i)
        return rom[a:b]
    out = {}
    def walk(d, path):
        off, first, _ = struct.unpack_from('<IHH', rom, fnt + (d & 0xFFF) * 8)
        p, i = fnt + off, first
        while rom[p]:
            n = rom[p] & 0x7F
            name = rom[p + 1:p + 1 + n].decode('latin1')
            if rom[p] & 0x80:
                walk(struct.unpack_from('<H', rom, p + 1 + n)[0], path + name + '/')
                p += 3 + n
            else:
                out[path + name] = body(i)
                i += 1
                p += 1 + n
    walk(0, '')
    out['<arm9>'] = rom[u32(0x20):u32(0x20) + u32(0x2C)]
    out['<arm7>'] = rom[u32(0x30):u32(0x30) + u32(0x3C)]
    out['<banner>'] = rom[u32(0x68):u32(0x68) + 0x840]
    ovt, n = u32(0x50), u32(0x54)
    out['<overlay table>'] = rom[ovt:ovt + n]
    for k in range(n // 32):
        out[f'<overlay {k}>'] = body(u32(ovt + k * 32 + 24))
    return out


def narc(d):
    """[member bytes], or None if d isn't a NARC."""
    if d[:4] != b'NARC':
        return None
    o = struct.unpack_from('<H', d, 12)[0]
    size = struct.unpack_from('<I', d, o + 4)[0]
    n = struct.unpack_from('<H', d, o + 8)[0]
    fatb = o + 12
    fntb = o + size
    fimg = fntb + struct.unpack_from('<I', d, fntb + 4)[0] + 8
    return [d[fimg + a:fimg + b] for a, b in struct.iter_unpack('<II', d[fatb:fatb + n * 8])]


def main(a, b, out):
    fa, fb = files(open(a, 'rb').read()), files(open(b, 'rb').read())
    res = {'files_a': len(fa), 'files_b': len(fb), 'only_a': sorted(set(fa) - set(fb)), 'only_b': sorted(set(fb) - set(fa)),
           'same': 0, 'differ': {}}
    for path in sorted(set(fa) & set(fb)):
        x, y = fa[path], fb[path]
        if x == y:
            res['same'] += 1
            continue
        e = {'size_a': len(x), 'size_b': len(y)}
        nx, ny = narc(x), narc(y)
        if nx is not None and ny is not None:
            e['members_a'], e['members_b'] = len(nx), len(ny)
            e['changed'] = [i for i in range(min(len(nx), len(ny))) if nx[i] != ny[i]]
        res['differ'][path] = e
    json.dump(res, open(out, 'w'), indent=1)
    print(f"{res['files_a']} / {res['files_b']} files; same {res['same']}, differ {len(res['differ'])}, only a {len(res['only_a'])}, only b {len(res['only_b'])}")
    for p, e in res['differ'].items():
        c = e.get('changed')
        print(f"{p}: {e['size_a']} -> {e['size_b']}" + (f"; {len(c)} of {e['members_a']} members" if c is not None else ''))


if __name__ == '__main__':
    main(*sys.argv[1:4])
