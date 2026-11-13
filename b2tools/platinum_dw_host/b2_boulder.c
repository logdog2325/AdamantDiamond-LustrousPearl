// (plat-dw-finish) Our side of the boulder puzzle's harness: the overlay's dw_core.c (DwBoulder_*, DwFallingBoulder_*)
// on a body in the floor's own tiles, with the fall table of the world's tables (b2tools/platinum_dw_world.py
// world_blob: what the overlay reads), reported in Platinum's shared world.
#include "pearlb2/plat_dw.h"
#include "boulder_snap.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static u8 *sTables;
static u8 *sWorld;
static const DwWorldFall *sFalls;
static u32 sFallCount;

static u8 *ReadAll(const char *path) {
    FILE *f = fopen(path, "rb");
    long n;
    u8 *buf;

    if (f == NULL) {
        perror(path);
        exit(2);
    }
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    fseek(f, 0, SEEK_SET);
    buf = malloc((size_t)n + 4);
    if (fread(buf, 1, (size_t)n, f) != (size_t)n) {
        exit(2);
    }
    fclose(f);
    return buf;
}

void B2B_Open(const char *dwBlob, const char *worldBlob) {
    u32 fallOffset;
    u16 fallCount;

    sTables = ReadAll(dwBlob);
    sWorld = ReadAll(worldBlob);
    // the world's header (platinum_dw_world.WORLD_HEADER '<4sHH11I8H'): the falls' offset is the 4th word, their count the
    // 3rd half word after the words (include/pearlb2/plat_dw.h DwWorld)
    memcpy(&fallOffset, sWorld + 8 + 3 * 4, 4);
    memcpy(&fallCount, sWorld + 8 + 11 * 4 + 2 * 2, 2);
    sFalls = (const DwWorldFall *)(sWorld + fallOffset);
    sFallCount = fallCount;
}

int B2B_FallCount(void) {
    return (int)sFallCount;
}

void B2B_Fall_(int i, int *map, int *x, int *z, int *flag) {
    *map = sFalls[i].map, *x = sFalls[i].x, *z = sFalls[i].z, *flag = sFalls[i].flag;
}

int B2B_FloorOffset(int map, int *offset) {
    const DwTables *t = (const DwTables *)sTables;
    u32 i;

    for (i = 0; i < t->floorCount; i++) {
        const DwFloor *f = DwTables_Floor(t, i);

        if (f->map == map) {
            offset[0] = f->offset[0], offset[1] = f->offset[1], offset[2] = f->offset[2];
            return 1;
        }
    }
    return 0;
}

// Black 2's FieldPlayerGrid_CheckStrengthRockPushEvent with the resident hook: coll = PearlB2_RockPushCollCheck() & ~1
// (DwBoulder_PushCollision on ActorRouteCollCheckOneTileInDir's bits); a hole's exception (bit 1 with Strength holes ahead)
// can't apply: no Distortion World tile converts to Black 2's hole class (pearl_chunk.BEHAVIOURS has no 0x1d)
int B2B_Push(int map, int x, int z, int dir, unsigned coll) {
    int off[3];

    if (!B2B_FloorOffset(map, off)) {
        return -1;
    }
    coll = DwBoulder_PushCollision(sFalls, sFallCount, (u16)map, x - off[0], z - off[2], (u32)dir, coll) & ~1u;
    return coll == 0;
}

static void Snap(const DwFallingBoulder *fall, const DwBoulderBody *b, u32 flags, BoulderSnapFunc func, void *arg) {
    BoulderSnap s;
    int off[3];

    // (the boulder stays in the floor it was pushed on: B5F's frame even after it lands on B6F, as the field keeps it)
    B2B_FloorOffset(fall->destination == DW_FALL_TO_B6F ? DW_MAP_B5F : b->map, off);
    s.pos[0] = b->pos.x + DW_FX(off[0] * 16), s.pos[1] = b->pos.y + DW_FX(off[1] * 16), s.pos[2] = b->pos.z + DW_FX(off[2] * 16);
    s.tile[0] = b->x + off[0], s.tile[1] = (b->y + off[1]) * 2, s.tile[2] = b->z + off[2];
    s.prev[0] = b->prevX + off[0], s.prev[1] = (b->prevY + off[1]) * 2, s.prev[2] = b->prevZ + off[2];
    s.spriteY = b->spriteY, s.uid = b->uid, s.map = b->map, s.flags = flags;
    s.script = fall->script, s.sound = fall->sound, s.deleted = fall->deleted, s.finished = fall->finished;
    func(arg, &s);
}

int B2B_Fall(int map, int x, int yHalf, int z, int prevX, int prevZ, int moveDir, int uid, unsigned flags,
             BoulderSnapFunc func, void *arg) {
    DwFallingBoulder fall;
    DwBoulderBody b;
    int off[3];
    int frames = 0;
    u32 puzzle = flags;

    if (!B2B_FloorOffset(map, off)) {
        return -1;
    }
    memset(&b, 0, sizeof(b));
    b.x = (s16)(x - off[0]), b.y = (s16)(yHalf / 2 - off[1]), b.z = (s16)(z - off[2]);
    b.prevX = (s16)(prevX - off[0]), b.prevY = b.y, b.prevZ = (s16)(prevZ - off[2]);
    b.pos.x = DW_FX(b.x * 16 + 8), b.pos.y = DW_FX(b.y * 16), b.pos.z = DW_FX(b.z * 16 + 8);
    b.moveDir = (u16)moveDir, b.face = (u16)moveDir, b.uid = (u16)uid, b.map = (u16)map;
    if (!DwFallingBoulder_New(&fall, sFalls, sFallCount, &b, puzzle)) {
        return 0;
    }
    for (;;) {
        BOOL done = DwFallingBoulder_Tick(&fall, &b, &puzzle, off[1]);

        frames++;
        Snap(&fall, &b, puzzle, func, arg);
        if (done || frames > 1000) {
            break;
        }
    }
    return frames;
}
