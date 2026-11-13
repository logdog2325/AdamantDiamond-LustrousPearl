"""PearlB2's own overlays (the decomp's tools/pearlb2/link_overlays.py: 371 the resident section, 344 the Pokétch's
system, 345-370 its apps, 372 Pal Park's migration screen, 373 Super Contests, 374 Platinum's Gym gimmicks, 375 Platinum's rooms, 376 Platinum's party commands (plat-tutors), 377 Platinum's Distortion World (plat-dw-core), 378 Platinum's Battle Factory, 379 its Battle Hall (plat-frontier-rooms)), not in dsd's config: build_rom puts them into the ROM's
overlay table right after it copies the decomp's code binaries, before any patch, so they are in every build of a
decomp that has them (the resident section is read at boot and its code is called from Black 2's).

    install(code) -> message      their entries in code/arm9_overlays.yaml (unsigned, uncompressed, file id = id);
                                  their bytes are the build's arm9_ovNNN.bin, already in the code dir
"""
import os, re, struct

FIRST, RESIDENT, PALPARK, CONTEST, PLATGYM, PLATROOMS, PLATPARTY, LAST = 344, 371, 372, 373, 374, 375, 376, 377
PLATDW = 377          # (plat-dw-core) Platinum's Distortion World, at the gimmick overlays' address too
PLATHALL = 379        # (plat-hall) Platinum's Battle Hall, at the gimmick overlays' address too (loaded for an op; 378 is left
                      # for plat-factory)
PLATFACTORY = 378     # (plat-frontier-rooms) Platinum's Battle Factory, at Pal Park's address (loaded for an op, as 376)
PLATCASTLE = 380      # (plat-castle) Platinum's Battle Castle, at the gimmick overlays' address too (loaded for an op)
PLATARCADE = 381      # (plat-arcade) Platinum's Battle Arcade, at the gimmick overlays' address too (loaded for an op; the
                      # board's op keeps it for as long as the board runs: Black 2's GameEvent_CreateOverlayDelegate)
PLATDWWARP = 382      # (plat-dw3) the Distortion World's way in (Spear Pillar's swirl, out of 377 for room), at the gimmick
                      # overlays' address too (DoDWWarp loads it where no gimmick runs)
# (plat-dw-core) Our overlays at Black 2's gimmick overlays' address must end before the overlays linked after all of
# those (146, 148, 149, 155-157, 226-252, 281 start there), which can be loaded beside a gimmick
AFTER_GIMMICKS = 146


def _elf_symbols(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'\x7fELF' and d[4] == 1 and d[5] == 1, f'{path}: not a 32-bit little-endian ELF'
    shoff, = struct.unpack_from('<I', d, 0x20)
    shentsize, shnum = struct.unpack_from('<HH', d, 0x2E)
    secs = [struct.unpack_from('<10I', d, shoff + i * shentsize) for i in range(shnum)]
    syms = {}
    for name, typ, flags, addr, off, size, link, info, align, entsize in secs:
        if typ != 2:                                # SHT_SYMTAB
            continue
        stroff = secs[link][4]
        for k in range(size // 16):
            nm, value = struct.unpack_from('<II', d, off + 16 * k)
            if nm:
                e = d.index(b'\0', stroff + nm)
                syms[d[stroff + nm:e].decode()] = value
    return syms


def pearlb2_on():
    import decomp
    text = open(decomp.SWITCH).read()
    return bool(re.search(r'^#define PEARLB2 1$', text, re.M))


def modules():
    """[(id, base, code size, bss size, ctor start, ctor end)] of our overlays in the decomp's link, [] without them."""
    import decomp
    syms = _elf_symbols(os.path.join(decomp.BUILD, 'arm9.o'))
    if f'OV{RESIDENT}_TEXT_START' not in syms:
        return []
    out = []
    for n in range(FIRST, max(LAST, PLATFACTORY, PLATHALL, PLATCASTLE, PLATARCADE, PLATDWWARP) + 1):    # (plat-hall: up to the Hall's 379;
                                                                                            # plat-castle: 380; plat-arcade: 381)
        if f'OV{n}_TEXT_START' not in syms:      # (a decomp before Pal Park's overlay 372)
            continue
        start, bss, end = syms[f'OV{n}_TEXT_START'], syms[f'OV{n}_BSS_START'], syms[f'OV{n}_BSS_END']
        out.append((n, start, bss - start, end - bss, syms[f'OV{n}_CTOR_START'], syms[f'OV{n}_CTOR_END']))
    return out


def install(code):
    if not pearlb2_on():
        return 'PearlB2 overlays: the decomp is vanilla (PEARLB2 0), none'
    mods = modules()
    if not mods:
        return 'PearlB2 overlays: this decomp has none'
    yml = os.path.join(code, 'arm9_overlays.yaml')
    text = open(yml).read()
    assert f'id: {FIRST}\n' not in text, f'{yml}: overlay {FIRST} is there already'
    last = max(int(m) for m in re.findall(r'^  - id: (\d+)$', text, re.M))
    assert last == FIRST - 1, f'{yml}: the last overlay is {last}, not {FIRST - 1}'
    m = re.search(r'^  - id: %d\n    base_address: (\d+)' % AFTER_GIMMICKS, text, re.M)
    if m:
        limit = int(m.group(1))
        for n, base, size, bss, ctor_start, ctor_end in mods:
            if n in (PLATGYM, PLATROOMS, PLATDW, PLATHALL, PLATCASTLE, PLATARCADE, PLATDWWARP):   # (plat-dw3: 382)
                assert base + size + bss <= limit, (f'overlay {n} ends at {base + size + bss:#x}, past overlay '
                                                    f'{AFTER_GIMMICKS}\'s {limit:#x}: the gimmick overlays\' room')
    # (plat-hall) the ROM's overlay table is indexed by id: a gap (379 linked without a 378) must be an empty overlay instead
    assert [m[0] for m in mods] == list(range(FIRST, mods[-1][0] + 1)), f'overlay ids not consecutive: {[m[0] for m in mods]}'
    entries = []
    for n, base, size, bss, ctor_start, ctor_end in mods:
        path = os.path.join(code, f'arm9_ov{n:03d}.bin')
        assert os.path.getsize(path) == size, f'{path}: {os.path.getsize(path)} B, the link says {size}'
        entries.append(f'  - id: {n}\n    base_address: {base}\n    code_size: {size}\n    bss_size: {bss}\n'
                       f'    ctor_start: {ctor_start}\n    ctor_end: {ctor_end}\n    file_id: {n}\n'
                       f'    compressed: false\n    signed: false\n    file_name: {path}\n')
    if os.path.islink(yml):
        os.unlink(yml)
    open(yml, 'w').write(text.rstrip('\n') + '\n' + ''.join(entries))
    res = next(m for m in mods if m[0] == RESIDENT)
    pp = [m for m in mods if m[0] == PALPARK]
    con = [m for m in mods if m[0] == CONTEST]
    gym = [m for m in mods if m[0] == PLATGYM]
    rooms = [m for m in mods if m[0] == PLATROOMS]
    party = [m for m in mods if m[0] == PLATPARTY]
    dw = [m for m in mods if m[0] == PLATDW]
    fac = [m for m in mods if m[0] == PLATFACTORY]      # (plat-frontier-rooms)
    hall = [m for m in mods if m[0] == PLATHALL]
    return (f'PearlB2 overlays {FIRST}-{mods[-1][0]}: the resident section {res[2] + res[3]} B at {res[1]:#x}, the '
            f'Pokétch {FIRST}-{RESIDENT - 1}' + (f', Pal Park\'s screen {pp[0][2] + pp[0][3]} B at {pp[0][1]:#x}'
                                                  if pp else '') +
            (f', Super Contests {con[0][2] + con[0][3]} B at {con[0][1]:#x}' if con else '') +
            (f', Platinum\'s Gyms {gym[0][2] + gym[0][3]} B at {gym[0][1]:#x}' if gym else '') +
            (f', Platinum\'s rooms {rooms[0][2] + rooms[0][3]} B at {rooms[0][1]:#x}' if rooms else '') +
            (f', Platinum\'s party commands {party[0][2] + party[0][3]} B at {party[0][1]:#x}' if party else '') +
            (f', Platinum\'s Distortion World {dw[0][2] + dw[0][3]} B at {dw[0][1]:#x}' if dw else '') +
            ''.join(f', its way in {m[2] + m[3]} B at {m[1]:#x}' for m in mods if m[0] == PLATDWWARP) +   # (plat-dw3)
            (f', the Battle Factory {fac[0][2] + fac[0][3]} B at {fac[0][1]:#x}' if fac else '') +   # (plat-frontier-rooms)
            (f', the Battle Hall {hall[0][2] + hall[0][3]} B at {hall[0][1]:#x}' if hall else ''))
