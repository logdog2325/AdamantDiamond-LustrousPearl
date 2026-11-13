// The Battle Tower's rules, Platinum's against ours, on the host (notes/PLATINUM_FRONTIER.md "The harness").
//   sim SEEDS      every seed 1..SEEDS: each mode (single, double, multi), each room 0-9 (a round's 7 or 14 opponents);
//                  the Battle Points for 0-20 rounds won in each mode, with and without Palmer; the IVs by Trainer id
// Both sides take their random numbers from Platinum's challenge generator (state * 48828125 + 1, the state / 65535), seeded
// the same: Platinum's through its own BattleTower_GetRandom, ours through randFFFFFFFFdivFFFF (Black 2's on the DS).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "plat_shim.h"
#include "b2_shim.h"

BOOL Plat_PickTeam(BattleTower *bt, FrontierTrainerBase *tr, u16 id, FrontierPokemon *mons, u8 n, BattleTowerPartnerData *partner);

static u32 sB2State;
static u8 *sBlob;
static u32 sTrainerCount, sSetCount;
static const u16 *sTrainers[400];
static const u8 *sSets;
static u16 sPicked[2][8];
static u32 sPickedSeed[2];
static int sPickCount[2];
static u16 sStage;
static u16 sPlatRoom;

u16 randFFFFFFFFdivFFFF(BSubwayScrWork *bsw) {
    (void)bsw;
    sB2State = sB2State * 48828125u + 1;
    return (u16)(sB2State / 65535);
}
u32 BSubwayPlayData_GetData(void *play, int id, void *out) { (void)play; (void)id; (void)out; return 0; }
s32 BSubwayScoreData_GetWifiRank(void *score) { (void)score; return 0; }
u16 BSubwayScoreData_GetStage(void *score, u32 mode) { (void)score; (void)mode; return sStage; }
void BSubwayScoreData_AddBattlePoints(void *score, u16 points) { (void)score; (void)points; }
SaveControl *GameData_GetSaveControl(void *gameData) { (void)gameData; return NULL; }
void *getTrainerCardInfoBlkAddress(SaveControl *save) { (void)save; return NULL; }
void RecordAdd(void *records, int id, u32 value) { (void)records; (void)id; (void)value; }
u16 BsubwayScr_DrawTrainerNo(BSubwayScrWork *bsw, u16 level, u8 index, u32 mode, u8 side) {
    (void)bsw; (void)level; (void)index; (void)mode; (void)side;
    abort();                // (Black 2's own draw: PEARLB2 never calls it)
}
u16 LCRNG_Next(void) { abort(); }
void sub_0204B640(FrontierPokemonBase *param0, int param1) { memcpy(param0, sSets + 16 * param1, 16); }
u32 sub_0204B1E8(BattleTower *battleTower, FrontierPokemon *param1, u16 param2, u32 param3, u32 param4, u8 ivs, u8 param6,
                 BOOL param7, enum HeapID heapID) {
    (void)battleTower; (void)param1; (void)param4; (void)ivs; (void)param6; (void)param7; (void)heapID;
    sPicked[0][sPickCount[0]++] = param2;
    sPickedSeed[0] = param3;
    return 0;
}
void BtlInst_ReadPokemonData(u32 arcId, BSubwayPokemonData *data, u32 file) { (void)arcId; memcpy(data, sSets + 16 * file, 16); }
u16 BtlInst_Random16(MATHRandContext32 *rand) { (void)rand; return randFFFFFFFFdivFFFF(NULL); }
u32 BtlInst_MakeRomPokemon(BSubwayPokemon *pkm, u32 arcId, u32 file, u32 seed, u32 pid, u8 iv, int index, BOOL failed,
                           HeapID heapId) {
    (void)pkm; (void)arcId; (void)pid; (void)iv; (void)index; (void)failed; (void)heapId;
    sPicked[1][sPickCount[1]++] = (u16)file;
    sPickedSeed[1] = seed;
    return 0;
}

static void LoadSets(const char *path) {
    FILE *f = fopen(path, "rb");
    long size;
    u8 *p;
    u32 i;

    if (f == NULL) {
        fprintf(stderr, "%s: can't open\n", path);
        exit(2);
    }
    fseek(f, 0, SEEK_END);
    size = ftell(f);
    fseek(f, 0, SEEK_SET);
    sBlob = malloc(size);
    if (fread(sBlob, 1, size, f) != (size_t)size) {
        exit(2);
    }
    fclose(f);
    memcpy(&sTrainerCount, sBlob, 4);
    memcpy(&sSetCount, sBlob + 4, 4);
    p = sBlob + 8;
    for (i = 0; i < sTrainerCount; i++) {
        u16 len;
        memcpy(&len, p, 2);
        sTrainers[i] = (const u16 *)(p + 2);
        p += 2 + 2 * len;
    }
    sSets = p;
}

// The same Trainer's team, Platinum's picks and Black 2's (both its sets, no species twice, an item twice only after 50 tries)
static u32 Picks(u32 seeds, u32 *bad) {
    u32 seed, t, n = 0;
    int count, i;

    for (seed = 1; seed <= seeds; seed++) {
        for (t = 0; t < sTrainerCount; t++) {
            for (count = 2; count <= 4; count++) {
                BattleTower bt;
                BattleTowerPartnerData partner;
                FrontierPokemon mons[4];
                BSubwayPokemon pkms[4];
                BSubwayTeamConfig config;
                BOOL a, b;
                u16 *copy;
                u16 words = 2 + sTrainers[t][1];

                {
                    // (a Trainer with fewer species than the team needs: both sides would draw for ever; the game never asks)
                    u16 seen[128];
                    int k, j, distinct = 0;
                    for (k = 0; k < sTrainers[t][1]; k++) {
                        u16 sp;
                        memcpy(&sp, sSets + 16 * sTrainers[t][2 + k], 2);
                        for (j = 0; j < distinct && seen[j] != sp; j++) {
                        }
                        if (j == distinct && distinct < 128) {
                            seen[distinct++] = sp;
                        }
                    }
                    if (distinct < count) {
                        continue;
                    }
                }
                copy = malloc(2 * words + 2 * 4);
                memcpy(copy, sTrainers[t], 2 * words);
                memset(&bt, 0, sizeof(bt));
                bt.unk_08 = seed * 2246822519u + t;
                sPickCount[0] = sPickCount[1] = 0;
                a = Plat_PickTeam(&bt, (FrontierTrainerBase *)copy, (u16)t, mons, (u8)count, &partner);
                sB2State = seed * 2246822519u + t;
                b = BtlInst_MakeRomTeam(copy, (u16)t, pkms, (u8)count, 0, NULL, NULL, &config, NULL, BsubwayScr_GetMonIv(t), 0);
                n++;
                if (a != b || sPickCount[0] != sPickCount[1] || sPickedSeed[0] != sPickedSeed[1] || bt.unk_08 != sB2State) {
                    if ((*bad)++ < 10) {
                        printf("DIFF picks seed %u Trainer %u count %d\n", seed, t, count);
                    }
                } else {
                    for (i = 0; i < sPickCount[0]; i++) {
                        if (sPicked[0][i] != sPicked[1][i] && (*bad)++ < 10) {
                            printf("DIFF picks seed %u Trainer %u count %d: set %d Platinum %u, ours %u\n", seed, t, count, i,
                                   sPicked[0][i], sPicked[1][i]);
                        }
                    }
                }
                free(copy);
            }
        }
    }
    return n;
}
u16 WifiBattleTowerRecord_UpdateRoomNum(void *record, int mode, int op) { (void)record; (void)mode; (void)op; return sPlatRoom; }
u16 WifiBattleTowerRecord_UpdateRank(void *record, int op) { (void)record; (void)op; return 0; }
void WifiBattleTowerRecord_UpdateBattlePoints(void *record, u16 points, int op) { (void)record; (void)points; (void)op; }

int main(int argc, char **argv) {
    u32 seeds = argc > 2 ? (u32)atoi(argv[2]) : 2000;
    u32 rounds = 0, ids = 0, bad = 0, bp = 0, iv = 0, teams;
    static const int modes[3] = { BATTLE_TOWER_MODE_SINGLE, BATTLE_TOWER_MODE_DOUBLE, BATTLE_TOWER_MODE_MULTI };
    u32 seed, room, i;
    int m, palmer;

    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 2) {
        fprintf(stderr, "sim SETS_BLOB [SEEDS]\n");
        return 2;
    }
    LoadSets(argv[1]);
    for (seed = 1; seed <= seeds; seed++) {
        for (m = 0; m < 3; m++) {
            for (room = 0; room < 10; room++) {
                BattleTower bt;
                BSubwayScrWork bsw;
                int n = modes[m] == BATTLE_TOWER_MODE_MULTI ? 14 : 7;

                memset(&bt, 0, sizeof(bt));
                memset(&bsw, 0, sizeof(bsw));
                bt.unk_08 = seed * 2654435761u;
                bt.challengeMode = modes[m];
                bt.roomNum = (u16)room;
                sB2State = bt.unk_08;
                bsw.playMode = (u8)m;               // Black 2's play modes 0, 1, 2 = Platinum's single, double, multi
                bsw.unkE = (u16)(room * 7);         // the wins so far: the room is wins / 7
                sub_0204A4C8(&bt, NULL);
                BsubwayScr_DrawTrainerNos(&bsw);
                rounds++;
                for (i = 0; i < (u32)n; i++) {
                    ids++;
                    if (bt.trainerIDs[i] != bsw.unk32[i]) {
                        if (bad++ < 10) {
                            printf("DIFF seed %u mode %d room %u opponent %u: Platinum %u, ours %u\n", seed, m, room, i,
                                   bt.trainerIDs[i], bsw.unk32[i]);
                        }
                    }
                }
                if (sB2State != bt.unk_08 && bad++ < 10) {
                    printf("DIFF seed %u mode %d room %u: the two used a different count of random numbers\n", seed, m, room);
                }
            }
        }
    }
    for (m = 0; m < 3; m++) {
        for (room = 1; room <= 20; room++) {        // (a round won: 1 or more)
            for (palmer = 0; palmer < 2; palmer++) {
                BattleTower bt;
                BSubwayScrWork bsw;
                u16 a, b;

                if (palmer && m != 0) {
                    continue;                       // (Palmer is the singles' only)
                }
                memset(&bt, 0, sizeof(bt));
                memset(&bsw, 0, sizeof(bsw));
                bt.challengeMode = modes[m];
                bt.beatPalmer = palmer;
                sPlatRoom = (u16)room;
                bsw.playMode = (u8)m;
                bsw.unkC_1 = palmer;
                sStage = (u16)room;
                a = BattleTower_GiveBattlePointsReward(&bt);
                b = func_ov033_0217b8ec(&bsw);
                bp++;
                if (a != b) {
                    bad++;
                    printf("DIFF BP mode %d rounds %u palmer %d: Platinum %u, ours %u\n", m, room, palmer, a, b);
                }
            }
        }
    }
    for (i = 0; i < 400; i++) {
        iv++;
        if (BattleTower_GetIVsFromTrainerID((u16)i) != BsubwayScr_GetMonIv(i) && bad++ < 20) {
            printf("DIFF IVs Trainer %u: Platinum %u, ours %u\n", i, BattleTower_GetIVsFromTrainerID((u16)i),
                   BsubwayScr_GetMonIv(i));
        }
    }
    teams = Picks(seeds / 10 ? seeds / 10 : 1, &bad);
    printf("%u rounds (%u opponents) drawn; %u Battle Point awards; IVs of %u Trainer ids; %u teams picked: %u problems\n",
           rounds, ids, bp, iv, teams, bad);
    return bad ? 1 : 0;
}
