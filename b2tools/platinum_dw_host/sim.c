// The Distortion World's harness: each route (b2tools/platinum_dw_check.py writes them from Platinum's tables) runs on
// Platinum's own C and on dw_core.c, a held direction at a time, and every frame of the two must be the same: the
// position, the tile, the directions, the jump's offset, the face (state), the platform, the camera's angles, the
// sprite's rotation, the action. Platinum's frames are in its shared world, ours in the floor's own tiles: the floor's
// offset is taken off Platinum's first.
//
//   sim TW_ARC TW_ARC_ATTR BLOB ROUTES [TRACE]
// ROUTES: lines "route NAME MAP X Y Z FACE [PLATFORM [SURFING]]" (Platinum's world; a platform to start on), then "tokens T..." (U D L R, lower case running,
// . for none; +X presses X until the player leaves the tile, jumps or bumps). Prints one line per route and a summary; exits 1 on any difference.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snap.h"

#define MAX_FRAMES 4000

typedef struct {
    DwSnap frames[MAX_FRAMES];
    int count;
} Track;

static Track sPlat, sOurs;

static void Record(void *arg, const DwSnap *snap) {
    Track *t = arg;

    if (t->count < MAX_FRAMES) {
        t->frames[t->count] = *snap;
    }
    t->count++;
}

static int Same(const DwSnap *p, const DwSnap *o, char *why, size_t n) {
    int i;
    int offset[3];

    if (p->map != o->map) {
        snprintf(why, n, "floor %d against %d", p->map, o->map);
        return 0;
    }
    B2_FloorOffset(p->map, offset);
    if (p->spriteY != o->spriteY) {
        snprintf(why, n, "sprite offset %d against %d", p->spriteY, o->spriteY);
        return 0;
    }
    if (p->movingFlags != o->movingFlags) {
        snprintf(why, n, "elevator flags %#x against %#x", p->movingFlags, o->movingFlags);
        return 0;
    }

    for (i = 0; i < 3; i++) {
        int unit = 16 * 4096;
        int pp = p->pos[i] - offset[i] * unit;
        if (pp != o->pos[i]) {
            snprintf(why, n, "position %c %d against %d", "xyz"[i], pp, o->pos[i]);
            return 0;
        }
        if (p->tile[i] - offset[i] != o->tile[i]) {
            snprintf(why, n, "tile %c %d against %d", "xyz"[i], p->tile[i] - offset[i], o->tile[i]);
            return 0;
        }
        if (p->jumpOffset[i] != o->jumpOffset[i]) {
            snprintf(why, n, "jump offset %c %d against %d", "xyz"[i], p->jumpOffset[i], o->jumpOffset[i]);
            return 0;
        }
        if ((p->camera[i] & 0xffff) != (o->camera[i] & 0xffff)) {
            snprintf(why, n, "camera %c %d against %d", "xyz"[i], p->camera[i] & 0xffff, o->camera[i] & 0xffff);
            return 0;
        }
    }
    if (p->face != o->face || p->motion != o->motion) {
        snprintf(why, n, "directions %d/%d against %d/%d", p->face, p->motion, o->face, o->motion);
        return 0;
    }
    if (p->state != o->state || p->platform != o->platform) {
        snprintf(why, n, "state %d platform %d against %d, %d", p->state, p->platform, o->state, o->platform);
        return 0;
    }
    if (p->cameraActive != o->cameraActive) {
        snprintf(why, n, "camera moving %d against %d", p->cameraActive, o->cameraActive);
        return 0;
    }
    if (p->rotation != o->rotation) {
        snprintf(why, n, "rotation %d against %d", p->rotation, o->rotation);
        return 0;
    }
    if (p->action != o->action) {
        snprintf(why, n, "action %d against %d", p->action, o->action);
        return 0;
    }
    return 1;
}

static int Dir(char c, int *running) {
    *running = c >= 'a' && c <= 'z';
    switch (c) {
    case 'U': case 'u': return 0;
    case 'D': case 'd': return 1;
    case 'L': case 'l': return 2;
    case 'R': case 'r': return 3;
    }
    return -1;
}

int main(int argc, char **argv) {
    FILE *routes;
    FILE *trace = NULL;
    char line[4096];
    char name[128];
    int map = 0, x = 0, y = 0, z = 0, face = 0, platform = -1, surfing = 0;
    int offset[3];
    int routesRun = 0, routesBad = 0;
    long framesCompared = 0;
    int jumps = 0;
    int elevators = 0;

    if (argc < 5) {
        fprintf(stderr, "sim TW_ARC TW_ARC_ATTR BLOB ROUTES [TRACE]\n");
        return 2;
    }
    Plat_Open(argv[1], argv[2]);
    B2_Open(argv[3]);
    routes = fopen(argv[4], "r");
    if (argc > 5) {
        trace = fopen(argv[5], "w");
    }
    while (fgets(line, sizeof(line), routes)) {
        if (sscanf(line, "route %127s %d %d %d %d %d", name, &map, &x, &y, &z, &face) == 6) {
            platform = -1;
            surfing = 0;
            sscanf(line, "route %*s %*d %*d %*d %*d %*d %d %d", &platform, &surfing);
            continue;
        }
        if (strncmp(line, "tokens ", 7) == 0) {
            const char *t = line + 7;
            int bad = 0;
            int steps = 0;
            char why[200] = "";
            int lastState = -99, lastPlatform = -99;

            B2_FloorOffset(map, offset);
            Plat_Start(map, x, y, z, face, platform, surfing);
            B2_Start(map, x - offset[0], y - offset[1], z - offset[2], face, platform, surfing);
            if (trace) {
                fprintf(trace, "== %s (map %d) from (%d, %d, %d) local (%d, %d, %d)\n", name, map, x, y, z,
                        x - offset[0], y - offset[1], z - offset[2]);
            }
            for (; *t && *t != '\n' && !bad; t++) {
                int running;
                int dir;
                int pj, oj, i;
                int repeat = 0;
                int tries = 0;
                DwSnap before;

                if (*t == ' ') {
                    continue;
                }
                // "+X": X again until the player has left the tile, jumped or bumped (a turn takes a press first)
                if (*t == '+') {
                    repeat = 1;
                    t++;
                }
                dir = Dir(*t, &running);
            again:
                Plat_Snapshot(&before);
                sPlat.count = sOurs.count = 0;
                pj = Plat_Token(dir, running, Record, &sPlat);
                oj = B2_Token(dir, running, Record, &sOurs);
                steps++;
                jumps += pj;
                if (trace) {
                    int off[3];

                    B2_FloorOffset(before.map, off);
                    fprintf(trace, "pre (%d, %d, %d) dir %d map %d\n", before.tile[0] - off[0], before.tile[1] - off[1],
                            before.tile[2] - off[2], dir, before.map);
                }
                if (pj != oj) {
                    snprintf(why, sizeof(why), "token %d '%c': a jump on one side only", steps, *t);
                    bad = 1;
                    break;
                }
                if (sPlat.count != sOurs.count) {
                    snprintf(why, sizeof(why), "token %d '%c': %d frames against %d", steps, *t, sPlat.count,
                             sOurs.count);
                    bad = 1;
                    break;
                }
                for (i = 0; i < sPlat.count && i < MAX_FRAMES; i++) {
                    char w[160];

                    framesCompared++;
                    if (!Same(&sPlat.frames[i], &sOurs.frames[i], w, sizeof(w))) {
                        snprintf(why, sizeof(why), "token %d '%c' frame %d: %s", steps, *t, i, w);
                        bad = 1;
                        break;
                    }
                }
                // Field_ProcessStep: after a step that set Platinum's step flag (PlayerAvatar_StartStep: the land's
                // and a floor platform's walks, runs and double jumps, and surfing), an elevator there rides
                if (!bad && !pj && sPlat.count > 0) {
                    int a = sPlat.frames[sPlat.count - 1 < MAX_FRAMES ? sPlat.count - 1 : MAX_FRAMES - 1].action;
                    int stepped = (a >= 12 && a < 20) || (a >= 88 && a < 92) || (a >= 117 && a < 121) ||
                                  (surfing && a >= 105 && a < 133);
                    if (stepped) {
                        int pe, oe, k;

                        sPlat.count = sOurs.count = 0;
                        pe = Plat_StepEnd(Record, &sPlat);
                        oe = B2_StepEnd(Record, &sOurs);
                        if (pe != oe || sPlat.count != sOurs.count) {
                            snprintf(why, sizeof(why), "token %d: elevator %d/%d frames %d/%d", steps, pe, oe,
                                     sPlat.count, sOurs.count);
                            bad = 1;
                        }
                        for (k = 0; !bad && k < sPlat.count && k < MAX_FRAMES; k++) {
                            char w[160];

                            framesCompared++;
                            if (!Same(&sPlat.frames[k], &sOurs.frames[k], w, sizeof(w))) {
                                snprintf(why, sizeof(why), "token %d elevator frame %d: %s", steps, k, w);
                                bad = 1;
                            }
                        }
                        if (pe && !bad) {
                            elevators++;
                            if (trace) {
                                const DwSnap *e = &sOurs.frames[sOurs.count - 1];
                                fprintf(trace, "    elevator to map %d tile (%d, %d, %d) flags %#x frames %d\n", e->map,
                                        e->tile[0], e->tile[1], e->tile[2], e->movingFlags, sOurs.count);
                            }
                        }
                    }
                }
                if (trace && sOurs.count > 0) {
                    const DwSnap *e = &sOurs.frames[sOurs.count - 1];
                    unsigned short pitch, yaw;

                    B2_BlackTwoCamera(&pitch, &yaw);
                    fprintf(trace, "%3d %c%s tile (%d, %d, %d) face %d motion %d state %d platform %d camera (%d, %d, %d) "
                                   "B2 pitch %#06x yaw %#06x rotation %d action %d frames %d\n",
                            steps, *t, pj ? " jump" : "", e->tile[0], e->tile[1], e->tile[2], e->face, e->motion,
                            e->state, e->platform, e->camera[0], e->camera[1], e->camera[2], pitch, yaw, e->rotation,
                            e->action, sOurs.count);
                    if (e->state != lastState || e->platform != lastPlatform) {
                        fprintf(trace, "    plane: state %d platform %d\n", e->state, e->platform);
                        lastState = e->state;
                        lastPlatform = e->platform;
                    }
                }
                if (repeat && !bad && !pj && sPlat.count > 0 && ++tries < 3) {
                    const DwSnap *e = &sPlat.frames[sPlat.count - 1 < MAX_FRAMES ? sPlat.count - 1 : MAX_FRAMES - 1];
                    int bumped = e->action >= 28 && e->action < 32;

                    if (!bumped && e->tile[0] == before.tile[0] && e->tile[1] == before.tile[1] &&
                        e->tile[2] == before.tile[2]) {
                        goto again;
                    }
                }
            }
            routesRun++;
            if (bad) {
                routesBad++;
                printf("DIFF %s: %s\n", name, why);
            } else {
                printf("same %s: %d tokens\n", name, steps);
            }
        }
    }
    printf("%d routes, %d differ; %ld frames compared; %d jumps, %d elevator rides\n", routesRun, routesBad, framesCompared,
           jumps, elevators);
    if (trace) {
        fclose(trace);
    }
    return routesBad ? 1 : 0;
}
