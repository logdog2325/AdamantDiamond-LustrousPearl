// (plat-dw-finish) Platinum's side of the boulder puzzle's harness: its own C (plat_boulder_extract.c, word for word) on a
// map object of the harness's.
#include "boulder_shim.h"
#include "boulder_snap.h"

#include "plat_boulder_extract.c"

static MapObject sBoulder;
static Location sLocation;
static FieldSystemSub sSub;
static DistWorldPersistedData sPersisted;
static DistWorldSystem sSystem;
static FieldSystem sField = { &sLocation, &sSub, NULL };
static int sScript, sSound, sDeleted, sFinished, sPushed;
static u32 sColl;

FieldSystem *MapObject_FieldSystem(const MapObject *mapObj) { return &sField; }
int MapObject_GetX(const MapObject *m) { return m->x; }
int MapObject_GetY(const MapObject *m) { return m->y; }
int MapObject_GetZ(const MapObject *m) { return m->z; }
void MapObject_SetX(MapObject *m, int v) { m->x = v; }
void MapObject_SetY(MapObject *m, int v) { m->y = v; }
void MapObject_SetZ(MapObject *m, int v) { m->z = v; }
void MapObject_SetXPrev(MapObject *m, int v) { m->xPrev = v; }
void MapObject_SetYPrev(MapObject *m, int v) { m->yPrev = v; }
void MapObject_SetZPrev(MapObject *m, int v) { m->zPrev = v; }
void MapObject_GetPosPtr(const MapObject *m, VecFx32 *p) { *p = m->pos; }
void MapObject_SetPos(MapObject *m, const VecFx32 *p) { m->pos = *p; }
void MapObject_GetSpritePosOffset(const MapObject *m, VecFx32 *p) { *p = m->spritePosOffset; }
void MapObject_SetSpritePosOffset(MapObject *m, const VecFx32 *p) { m->spritePosOffset = *p; }
int MapObject_GetMovingDir(const MapObject *m) { return m->movingDir; }
int MapObject_GetFacingDir(const MapObject *m) { return m->facingDir; }
void MapObject_Face(MapObject *m, int dir) { m->facingDir = dir; }
u32 MapObject_GetLocalID(const MapObject *m) { return (u32)m->localID; }
void MapObject_SetLocalID(MapObject *m, u32 id) { m->localID = (int)id; }
void MapObject_SetMapHeaderID(MapObject *m, u32 id) { m->mapHeaderID = (int)id; }
u32 MapObject_GetGraphicsID(const MapObject *m) { return (u32)m->graphicsID; }
void MapObject_SetStatusFlagOn(MapObject *m, u32 f) { m->status |= f; }
void MapObject_SetStatusFlagOff(MapObject *m, u32 f) { m->status &= ~f; }
void sub_020656DC(MapObject *m) { }
void *Heap_AllocAtEnd(int heapID, u32 size) { return malloc(size); }
void Heap_Free(void *p) { free(p); }
void Sound_PlayEffect(int seq) { if (seq == SEQ_SE_DP_UG_008_sseq) sSound = 1; }
void ScriptManager_Start(FieldTask *task, u16 scriptID, MapObject *obj, void *arg) { sScript = scriptID; }
VarsFlags *SaveData_GetVarsFlags(void *saveData) { return NULL; }
BOOL SystemFlag_HandleDistortionWorldPuzzleFinished(VarsFlags *v, int op) { if (op == HANDLE_FLAG_SET) sFinished = 1; return FALSE; }
void DeleteMapObject(DistWorldSystem *system, MapObject *mapObj) { sDeleted = 1; }
MapObject *ov5_021E10D4(PlayerAvatar *p, int dir) { return &sBoulder; }
u32 sub_02063EBC(MapObject *mapObj, int dir) { return sColl; }
BOOL PersistedMapFeatures_IsCurrentDynamicMap(FieldSystem *f, int id) { return id == DYNAMIC_MAP_FEATURES_DISTORTION_WORLD; }
void ov5_021DFF88(int dir, FieldSystem *f, PlayerAvatar *p, MapObject *m) { sPushed = 1; }

int PlatB_Push(int map, int x, int z, int dir, unsigned coll) {
    memset(&sBoulder, 0, sizeof(sBoulder));
    sBoulder.x = x, sBoulder.z = z, sBoulder.graphicsID = 0x54;
    sLocation.mapHeaderID = map;
    sColl = coll;
    sPushed = 0;
    ov5_021DFF1C(&sField, NULL, dir, 1);
    return sPushed;
}

int PlatB_Fall(int map, int x, int yHalf, int z, int prevX, int prevZ, int moveDir, int uid, unsigned flags,
               BoulderSnapFunc func, void *arg) {
    DistWorldFallingBoulder *b;
    int frames = 0;

    memset(&sBoulder, 0, sizeof(sBoulder));
    memset(&sPersisted, 0, sizeof(sPersisted));
    sBoulder.x = x, sBoulder.y = yHalf, sBoulder.z = z;
    sBoulder.xPrev = prevX, sBoulder.yPrev = yHalf, sBoulder.zPrev = prevZ;
    sBoulder.pos.x = (x << 4) * FX32_ONE + 8 * FX32_ONE;
    sBoulder.pos.y = (yHalf << 3) * FX32_ONE;
    sBoulder.pos.z = (z << 4) * FX32_ONE + 8 * FX32_ONE;
    sBoulder.movingDir = sBoulder.facingDir = moveDir;
    sBoulder.localID = uid, sBoulder.mapHeaderID = map, sBoulder.graphicsID = 0x54;
    sLocation.mapHeaderID = map;
    sPersisted.valid = 1;
    sPersisted.boulderPuzzleFlags = flags;
    sSystem.fieldSystem = &sField;
    sSystem.persistedData = &sPersisted;
    sSub.dynamicMapFeaturesData = &sSystem;
    // ov5_021DFFBC's state 1: the boulder's push has ended where it stands
    if (DistWorld_IsBoulderAtFallLocation(&sBoulder) != 1) {
        return 0;
    }
    b = DistWorldFallingBoulder_New(&sField, NULL, &sBoulder);
    for (;;) {
        BoulderSnap s;
        BOOL done;

        sScript = sSound = sDeleted = sFinished = 0;
        done = DistWorldFallingBoulder_Tick(b);
        frames++;
        s.pos[0] = sBoulder.pos.x, s.pos[1] = sBoulder.pos.y, s.pos[2] = sBoulder.pos.z;
        s.tile[0] = sBoulder.x, s.tile[1] = sBoulder.y, s.tile[2] = sBoulder.z;
        s.prev[0] = sBoulder.xPrev, s.prev[1] = sBoulder.yPrev, s.prev[2] = sBoulder.zPrev;
        s.spriteY = sBoulder.spritePosOffset.y;
        s.uid = sBoulder.localID, s.map = sBoulder.mapHeaderID;
        s.flags = sPersisted.boulderPuzzleFlags;
        s.script = sScript, s.sound = sSound, s.deleted = sDeleted, s.finished = sFinished;
        func(arg, &s);
        if (done || frames > 1000) {
            break;
        }
    }
    return frames;
}
