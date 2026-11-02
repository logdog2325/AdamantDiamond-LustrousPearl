// Pearl's Poffins on the host (notes/CONTESTS.md): cook by stirring well, badly and not at all; feed up to Sheen's limit.
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "pearlb2/poffin.h"

// a finger going round the pot the way the arrow says, `step` degrees a frame; with a target, a player watching the pot:
// faster below it, slower above
static void Cook(PoffinCook *cook, double step, BOOL touch, s32 target) {
    double angle = 0;
    u32 guard = 0;

    PoffinCook_Init(cook, 12345);
    for (;;) {
        s32 x = (s32)(128 + 60 * cos(angle)), y = (s32)(96 + 60 * sin(angle));
        s32 speed = cook->speed < 0 ? -cook->speed : cook->speed;

        if (PoffinCook_Step(cook, touch, x, y)) {
            return;
        }
        if (target != 0) {
            step += speed < target ? 0.2 : -0.2;
            step = step < 2 ? 2 : step > 60 ? 60 : step;
        }
        angle += (cook->direction ? -step : step) * 3.14159265 / 180;
        assert(++guard < 30 * 600);     // never stuck: ten minutes of frames
    }
}

int main(void) {
    static const PoffinBerry cheri = { { 10, 0, 0, 0, 0 }, 25 };
    PoffinCook cook;
    Poffin poffin;
    u32 i, rng = 1, liked = 0, disliked = 0, neutral = 0;
    u8 stats[6];
    static const u8 gift[5] = { 60, 30, 30, 30, 30 };

    // A steady finger: too slow burns, too fast overflows. A player who watches the pot does neither and is quicker.
    {
        Poffin slow, fast;
        u32 slowBurns, fastOverflows;

        Cook(&cook, 4, TRUE, 0);
        PoffinCook_Result(&cook, &slow, &cheri);
        slowBurns = cook.burns;
        printf("too slow: %u frames, %u overflows, %u burns, type %u, level %u\n", cook.frames, cook.overflows, cook.burns, slow.type, Poffin_Level(&slow));
        assert(slow.type == POFFIN_TYPE_FOUL && slowBurns > 0);
        Cook(&cook, 44, TRUE, 0);
        PoffinCook_Result(&cook, &fast, &cheri);
        fastOverflows = cook.overflows;
        printf("too fast: %u frames, %u overflows, %u burns, type %u, level %u\n", cook.frames, cook.overflows, cook.burns, fast.type, Poffin_Level(&fast));
        assert(fastOverflows > 0 && cook.frames < 1800);
        Cook(&cook, 16, TRUE, 2000);
        PoffinCook_Result(&cook, &poffin, &cheri);
        printf("watching the pot: %u frames, %u overflows, %u burns, type %u, level %u, smoothness %u\n", cook.frames, cook.overflows, cook.burns,
               poffin.type, Poffin_Level(&poffin), poffin.smoothness);
        assert(cook.overflows + cook.burns <= 3 && poffin.type == 0 && Poffin_Level(&poffin) > Poffin_Level(&fast));
        Cook(&cook, 0, FALSE, 0);
        PoffinCook_Result(&cook, &slow, &cheri);
        printf("not stirred: %u frames, %u burns, type %u\n", cook.frames, cook.burns, slow.type);
        assert(slow.type == POFFIN_TYPE_FOUL);
    }
    // the Contest Hall's gift, Pearl's numbers: a Mild Poffin (a flavor of 50 or more among several)
    assert(Poffin_Make(&poffin, gift, 40, FALSE, &rng) == POFFIN_TYPE_MILD);
    assert(poffin.smoothness == 40);
    // every nature has its place in Pearl's table
    for (i = 0; i < 25; i++) {
        Poffin_Make(&poffin, cheri.flavor, 25, FALSE, &rng);
        switch (Poffin_Preference(&poffin, i)) {
        case POFFIN_LIKE:
            liked++;
            break;
        case POFFIN_DISLIKE:
            disliked++;
            break;
        default:
            neutral++;
            break;
        }
    }
    printf("spicy: %u natures like it, %u dislike it, %u neutral\n", liked, disliked, neutral);
    assert(liked == 4 && disliked == 4 && neutral == 17);
    // Sheen's limit: feeding adds up to 255 at most; the script stops at 255 itself
    for (i = 0; i < 6; i++) {
        stats[i] = 250;
    }
    Poffin_Make(&poffin, cheri.flavor, 25, FALSE, &rng);
    Poffin_Feed(&poffin, 0, stats);
    for (i = 0; i < 6; i++) {
        assert(stats[i] >= 250);    // u8: never wraps
    }
    printf("poffin_sim: all good\n");
    return 0;
}
