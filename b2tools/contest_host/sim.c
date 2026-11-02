// The rules of Pearl's Super Contests on the host: thousands of AI-only contests (notes/CONTESTS.md).
//   python3 b2tools/contest_data.py blob OUT.bin
//   b2tools/contest_host/run.sh [count]
//   ./sim OUT.bin 20000
// Asserts the invariants a contest must hold and prints the shape of the results; the contest's picks of opponents and
// judges for all 20 ranks and types are exercised too.
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "pearlb2/contest.h"

static u8 *gBlob;

static const u8 *Part(u32 index, u32 *size) {
    const u8 *p = gBlob;
    u32 i, n;

    for (i = 0; i <= index; i++) {
        memcpy(&n, p, 4);
        p += 4;
        if (i == index) {
            *size = n;
            return p;
        }
        p += n;
    }
    return NULL;
}

static void GivePlayer(Contest *c, u32 rng, u32 row) {
    ContestMon *mon = &c->mons[CONTEST_PLAYER];
    const ContestOpponent *o = &c->data->opponents[row];
    u32 i;

    memset(mon, 0, sizeof(*mon));
    mon->opponent = 0xff;
    mon->species = o->species;
    for (i = 0; i < CONTEST_MOVES; i++) {
        mon->moves[i] = o->moves[i];
    }
    for (i = 0; i < CONTEST_CONDITIONS; i++) {
        mon->condition[i] = (u8)((rng >> (i * 4)) & 0xff);
    }
    mon->scarf = rng % 6;
    mon->skill = rng % 4;
}

int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "rb");
    long len;
    u32 count = argc > 2 ? (u32)atoi(argv[2]) : 2000, n, s;
    ContestData data;
    u32 wins[4] = { 0 }, played[CONTEST_RANKS][CONTEST_TYPES] = { { 0 } };
    s32 best[3] = { 0 }, stageTotals[3] = { 0 };
    long effectUse[EFFECT_COUNT] = { 0 };
    u32 voltageMax = 0, orderFixed = 0;
    s32 hist[8] = { 0 };

    fseek(f, 0, SEEK_END);
    len = ftell(f);
    fseek(f, 0, SEEK_SET);
    gBlob = malloc(len);
    fread(gBlob, 1, len, f);
    fclose(f);

    data.opponents = (const ContestOpponent *)Part(0, &s);
    data.opponentCount = s / sizeof(ContestOpponent);
    data.judges = (const ContestJudge *)Part(1, &s);
    data.judgeCount = s / sizeof(ContestJudge);
    data.dresses = (const ContestDress *)Part(2, &s);
    data.themeScores = Part(3, &s);
    assert(s == CONTEST_THEMES * CONTEST_ACCESSORIES);
    data.moves = (const ContestMoveData *)Part(4, &s);
    data.moveCount = s / sizeof(ContestMoveData);
    printf("opponents %u judges %u moves %u\n", data.opponentCount, data.judgeCount, data.moveCount);

    srand(12345);
    for (n = 0; n < count; n++) {
        static Contest c;
        static Acting act;
        static Dance dance;
        u32 type = n % CONTEST_TYPES, rank = (n / CONTEST_TYPES) % CONTEST_RANKS, mode;
        BOOL late = (n >> 3) & 1;
        s16 final[CONTEST_MONS], stage[3 * CONTEST_MONS];
        u32 i, row, placed;

        mode = (n % 11 == 0) ? CONTEST_MODE_PRACTICE_VISUAL + (n / 11) % 3 : CONTEST_MODE_OFFICIAL;
        if (mode != CONTEST_MODE_OFFICIAL) {
            rank = CONTEST_RANK_NORMAL;     // Pearl's scripts practice at Normal Rank only (its practice rows are all there)
        }
        memset(&c, 0, sizeof(c));
        if (!Contest_Init(&c, &data, type, rank, mode, late, (u32)rand() * 2u + n)) {
            printf("no contest for rank %u type %u mode %u late %d\n", rank, type, mode, late);
            abort();
        }
        played[rank][type]++;
        // the player: a random opponent's moves
        row = (u32)rand() % data.opponentCount;
        GivePlayer(&c, (u32)rand() * 3u, row);
        for (i = 1; i < CONTEST_MONS; i++) {
            assert(c.mons[i].species != 0);
            assert(c.mons[i].opponent != 0xff && c.data->opponents[c.mons[i].opponent].rank == rank);
        }
        // Visual
        Contest_ComputeVisualStats(&c);
        Contest_ComputeVisualDress(&c);
        for (i = 0; i < CONTEST_MONS; i++) {
            s32 h = Contest_VisualHearts(&c, i);

            assert(h >= 0 && h <= 12);
        }
        // Dance
        Dance_RunAI(&dance, &c);
        for (i = 0; i < CONTEST_MONS; i++) {
            assert(c.mons[i].danceScore >= 0);
            if (c.mons[i].danceScore > best[1]) {
                best[1] = c.mons[i].danceScore;
            }
        }
        Contest_OrderFromStages(&c);
        // Acting
        Acting_Run(&act, &c);
        for (i = 0; i < CONTEST_MONS; i++) {
            u32 k;

            if (c.mons[i].actingScore > best[2]) {
                best[2] = c.mons[i].actingScore;
            }
            for (k = 0; k < CONTEST_MOVES; k++) {
                u32 e = Acting_MoveEffect(&c, c.mons[i].moves[k]);

                assert(e < EFFECT_COUNT);
                effectUse[e]++;
            }
            assert(act.voltage[0] < CONTEST_VOLTAGE_MAX && act.voltage[1] < CONTEST_VOLTAGE_MAX && act.voltage[2] < CONTEST_VOLTAGE_MAX);
            assert(act.order[i] < CONTEST_MONS);
            if (act.mon[i].voltageBonus > 0) {
                voltageMax++;
            }
            if (act.mon[i].orderKind != 0) {
                orderFixed++;
            }
        }
        {
            // the order must be a permutation at the end of every round
            u32 seen = 0;

            for (i = 0; i < CONTEST_MONS; i++) {
                seen |= 1u << act.order[i];
            }
            assert(seen == 0xf);
        }
        Contest_ComputeFinal(&c, final, stage);
        if (mode == CONTEST_MODE_OFFICIAL) {
            placed = 0;
            for (i = 0; i < CONTEST_MONS; i++) {
                assert(c.mons[i].placement < CONTEST_MONS);
                placed |= 1u << c.mons[i].placement;
                assert(final[i] >= 0 && final[i] <= 192 + 1);
                if (c.mons[i].placement == 0) {
                    wins[i]++;
                }
                hist[final[i] / 32]++;
            }
            assert(placed == 0xf);
        } else {
            assert(c.mons[CONTEST_PLAYER].placement < CONTEST_MONS);
        }
        for (s = 0; s < 3; s++) {
            stageTotals[s] += stage[s * CONTEST_MONS];
        }
    }
    printf("contests %u ok; wins by slot: %u %u %u %u\n", count, wins[0], wins[1], wins[2], wins[3]);
    printf("best dance %d, best acting %d; voltage maxed %u times; fixed orders %u\n", best[1], best[2], voltageMax, orderFixed);
    printf("final bars histogram (per 32 px):");
    for (s = 0; s < 8; s++) {
        printf(" %d", hist[s]);
    }
    printf("\neffects of the moves seen:");
    for (s = 0; s < EFFECT_COUNT; s++) {
        printf(" %ld", effectUse[s]);
    }
    printf("\n");
    return 0;
}
