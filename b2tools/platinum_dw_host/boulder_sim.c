// (plat-dw-finish) The boulder puzzle's harness (notes/PLATINUM_DW.md): Platinum's own C (boulder_shim.c) beside the
// overlay's dw_core.c (b2_boulder.c), for every push next to a fall location and every fall, frame by frame.
//   boulder_sim DW_BLOB WORLD_BLOB [-v]
#include "boulder_snap.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_FRAMES 128
typedef struct {
    BoulderSnap s[MAX_FRAMES];
    int n;
} Run;

static void Record(void *arg, const BoulderSnap *s) {
    Run *r = arg;

    if (r->n < MAX_FRAMES) {
        r->s[r->n] = *s;
    }
    r->n++;
}

static int sMismatches, sVerbose;

static void Mismatch(const char *what) {
    if (sMismatches++ < 20) {
        printf("  MISMATCH %s\n", what);
    }
}

static int SameSnap(const BoulderSnap *a, const BoulderSnap *b) {
    return memcmp(a, b, sizeof(BoulderSnap)) == 0;
}

static void Show(const char *side, const BoulderSnap *s) {
    printf("    %s pos (%d, %d, %d) tile (%d, %d, %d) prev (%d, %d, %d) spriteY %d uid %d map %d flags %05x script %d "
           "sound %d deleted %d finished %d\n", side, s->pos[0], s->pos[1], s->pos[2], s->tile[0], s->tile[1], s->tile[2],
           s->prev[0], s->prev[1], s->prev[2], s->spriteY, s->uid, s->map, s->flags, s->script, s->sound, s->deleted,
           s->finished);
}

// One fall on both sides; the frames compared. Returns the last frame's flags (Platinum's)
static unsigned Fall(int map, int x, int yHalf, int z, int dir, int uid, unsigned flags, int *frames, int *finished,
                     int *script) {
    static const int dx[4] = { 0, 0, -1, 1 }, dz[4] = { -1, 1, 0, 0 };
    static Run p, o;
    char what[200];
    int i, np, no;

    p.n = o.n = 0;
    np = PlatB_Fall(map, x, yHalf, z, x - dx[dir], z - dz[dir], dir, uid, flags, Record, &p);
    no = B2B_Fall(map, x, yHalf, z, x - dx[dir], z - dz[dir], dir, uid, flags, Record, &o);
    snprintf(what, sizeof(what), "map %d (%d, %d) pushed %d, boulder %d, flags %05x", map, x, z, dir, uid, flags);
    if (np != no) {
        char m[260];

        snprintf(m, sizeof(m), "%s: %d frames, ours %d", what, np, no);
        Mismatch(m);
    }
    for (i = 0; i < np && i < no && i < MAX_FRAMES; i++) {
        if (!SameSnap(&p.s[i], &o.s[i])) {
            char m[260];

            snprintf(m, sizeof(m), "%s: frame %d", what, i);
            Mismatch(m);
            if (sMismatches <= 3) {
                Show("Platinum", &p.s[i]);
                Show("ours    ", &o.s[i]);
            }
            break;
        }
    }
    *frames += np;
    if (np > 0) {
        int last = (np < MAX_FRAMES ? np : MAX_FRAMES) - 1;

        for (i = 0; i <= last; i++) {
            if (p.s[i].finished) {
                *finished = 1;
            }
            if (p.s[i].script) {
                *script = p.s[i].script;
            }
        }
        if (sVerbose) {
            printf("  %s: %d frames, ends uid %d map %d flags %05x%s\n", what, np, p.s[last].uid, p.s[last].map,
                   p.s[last].flags, p.s[last].deleted ? " (gone)" : "");
        }
        return p.s[last].flags;
    }
    return flags;
}

int main(int argc, char **argv) {
    static const unsigned colls[] = { 0, 1, 2, 3, 4, 5, 8, 9, 0x10, 0x11, 0x12, 0x1e };
    static const int maps[] = { 577, 579, 580, 581 };
    int pushes = 0, pushYes = 0, falls = 0, frames = 0, i, m, x, z, d, c, u;

    if (argc < 3) {
        fprintf(stderr, "usage: boulder_sim DW_BLOB WORLD_BLOB [-v]\n");
        return 2;
    }
    sVerbose = argc > 3 && strcmp(argv[3], "-v") == 0;
    B2B_Open(argv[1], argv[2]);
    // ---- the push: every tile of the floors around the puzzle, every direction, collision bits
    for (m = 0; m < 4; m++) {
        int off[3];

        B2B_FloorOffset(maps[m], off);
        for (x = off[0] - 2; x < off[0] + 66; x++) {
            for (z = off[2] - 2; z < off[2] + 66; z++) {
                for (d = 0; d < 4; d++) {
                    for (c = 0; c < (int)(sizeof(colls) / sizeof(colls[0])); c++) {
                        int a = PlatB_Push(maps[m], x, z, d, colls[c]);
                        int b = B2B_Push(maps[m], x, z, d, colls[c]);

                        pushes++;
                        pushYes += a;
                        if (a != b) {
                            char what[160];

                            snprintf(what, sizeof(what), "push: map %d (%d, %d) dir %d coll %x: Platinum %d, ours %d", maps[m],
                                     x, z, d, colls[c], a, b);
                            Mismatch(what);
                        }
                    }
                }
            }
        }
    }
    printf("pushes: %d tested (%d go), the same on both sides\n", pushes, pushYes);
    // ---- the falls: each fall location, pushed from each side, each boulder, the pits' flags each way
    for (i = 0; i < B2B_FallCount(); i++) {
        int map, fx, fz, flag, off[3];

        B2B_Fall_(i, &map, &fx, &fz, &flag);
        B2B_FloorOffset(map, off);
        for (d = 0; d < 4; d++) {
            for (u = 128; u <= 130; u++) {
                for (c = 0; c < 8; c++) {
                    unsigned flags = (map == 579 ? 7u : (7u << 3)) | (7u << 13) | ((unsigned)c << 6);
                    int fin = 0, scr = 0;

                    Fall(map, fx + off[0], (off[1] + 1) * 2, fz + off[2], d, u, flags, &frames, &fin, &scr);
                    falls++;
                }
            }
        }
    }
    printf("falls: %d tested, %d frames, %s\n", falls, frames, sMismatches ? "MISMATCHES" : "every frame the same");
    // ---- the story's way through: the three boulders off B5F's holes, then into their own pits; the flag at the end
    {
        static const int b5fHole[3][2] = { { 0, 3 }, { 1, 2 }, { 2, 1 } };     // (fall index, pushed direction)
        static const int pit[3][3] = { { 3, 0, 128 }, { 6, 2, 129 }, { 9, 1, 130 } };
        unsigned flags = 7u | (7u << 13);      // InitPersistedData's three boulders on B5F; the hints' trio in B6F
        int fin = 0, scr = 0, f = 0;

        for (i = 0; i < 3; i++) {
            int map, fx, fz, flag, off[3];

            B2B_Fall_(b5fHole[i][0], &map, &fx, &fz, &flag);
            B2B_FloorOffset(map, off);
            flags = Fall(map, fx + off[0], (off[1] + 1) * 2, fz + off[2], b5fHole[i][1], 128 + i, flags, &f, &fin, &scr);
        }
        printf("the way through: three boulders off B5F: flags %05x\n", flags);
        for (i = 0; i < 3; i++) {
            int map, fx, fz, flag, off[3];

            scr = 0;
            B2B_Fall_(pit[i][0], &map, &fx, &fz, &flag);
            B2B_FloorOffset(map, off);
            flags = Fall(map, fx + off[0], (off[1] + 1) * 2, fz + off[2], pit[i][1], pit[i][2], flags, &f, &fin, &scr);
            printf("  boulder %d into the pit at (%d, %d): script %d, flags %05x\n", pit[i][2], fx, fz, scr, flags);
        }
        printf("the way through: puzzle finished %s\n", fin ? "yes" : "NO");
        if (!fin) {
            sMismatches++;
        }
    }
    printf("%d mismatches\n", sMismatches);
    return sMismatches != 0;
}
