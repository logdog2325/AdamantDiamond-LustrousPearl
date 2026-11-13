// (plat-dw-finish) One frame of a falling boulder, as both sides report it, in Platinum's shared world (plain ints).
#ifndef BOULDER_SNAP_H
#define BOULDER_SNAP_H
typedef struct {
    int pos[3];         // fx32, Platinum's shared world
    int tile[3];        // x, y (in half tiles, Platinum's), z
    int prev[3];
    int spriteY;
    int uid;
    int map;
    unsigned flags;     // the persisted boulder puzzle flags
    int script;         // the script started this frame (0 none)
    int sound;          // the landing sound this frame
    int deleted;
    int finished;       // FLAG_DISTORTION_WORLD_PUZZLE_FINISHED set this frame
} BoulderSnap;
typedef void (*BoulderSnapFunc)(void *arg, const BoulderSnap *snap);

// boulder_shim.c: Platinum's own C. Push: 1 if ov5_021DFF1C starts the push (the boulder at (x, z) on map, pushed in dir,
// its collision bits coll). Fall: from the boulder standing where a push left it (shared world tiles, y in half tiles),
// frames until DistWorldFallingBoulder_Tick ends; 0 if DistWorld_IsBoulderAtFallLocation says no fall
int PlatB_Push(int map, int x, int z, int dir, unsigned coll);
int PlatB_Fall(int map, int x, int yHalf, int z, int prevX, int prevZ, int moveDir, int uid, unsigned flags,
               BoulderSnapFunc func, void *arg);
// b2_boulder.c: ours (dw_core.c), the same in the floor's own tiles (the sim converts)
void B2B_Open(const char *dwBlob, const char *worldBlob);
int B2B_FloorOffset(int map, int *offset);
int B2B_Push(int map, int x, int z, int dir, unsigned coll);
int B2B_Fall(int map, int x, int yHalf, int z, int prevX, int prevZ, int moveDir, int uid, unsigned flags,
             BoulderSnapFunc func, void *arg);
int B2B_FallCount(void);
void B2B_Fall_(int i, int *map, int *x, int *z, int *flag);
#endif
