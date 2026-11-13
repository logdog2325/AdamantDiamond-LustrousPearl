// (plat-dw-finish) What Platinum's extracted boulder puzzle (plat_boulder_extract.c: ov9's falls and falling boulder,
// overlay 5's push test) needs around it on the Mac: a map object, a field system, the constants of pokeplatinum's
// headers. boulder_shim.c holds the rest and the harness's side of it.
#ifndef BOULDER_SHIM_H
#define BOULDER_SHIM_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
typedef int32_t s32;
typedef int32_t fx32;
typedef int BOOL;
#define TRUE 1
#define FALSE 0
#define FX32_ONE 4096
typedef struct {
    fx32 x, y, z;
} VecFx32;

#define GF_ASSERT(x) do { if (!(x)) { fprintf(stderr, "Platinum's assert: %s (%s:%d)\n", #x, __FILE__, __LINE__); abort(); } } while (0)

enum FaceDirection { FACE_UP = 0, FACE_DOWN, FACE_LEFT, FACE_RIGHT };
#define DIR_NORTH 0
#define DIR_SOUTH 1
#define DIR_WEST 2
#define DIR_EAST 3
// include/map_object.h
#define MAP_OBJECT_COORD_EDGE_TO_FX32(coord) (((coord) << 4) * FX32_ONE)
// generated/map_headers.txt (a line each from 0)
#define MAP_HEADER_DISTORTION_WORLD_B5F 579
#define MAP_HEADER_DISTORTION_WORLD_B6F 580
#define MAP_HEADER_INVALID 0xffff
// include/constants/distortion_world.h
#define DIST_WORLD_MAP_OBJECT_B6F_MESPRIT_BOULDER_OUTSIDE 128
#define DIST_WORLD_MAP_OBJECT_B6F_AZELF_BOULDER_OUTSIDE 129
#define DIST_WORLD_MAP_OBJECT_B6F_UXIE_BOULDER_OUTSIDE 130
#define DIST_WORLD_MAP_OBJECT_B6F_MESPRIT_BOULDER_IN_PIT 144
#define DIST_WORLD_MAP_OBJECT_B6F_AZELF_BOULDER_IN_PIT 145
#define DIST_WORLD_MAP_OBJECT_B6F_UXIE_BOULDER_IN_PIT 146
#define GHOST_PROP_GROUP_MAX_COUNT 24
#define DIST_WORLD_PERSISTED_DATA_CURRENT_FLOATING_PLATFORM_SIZE 4
#define DYNAMIC_MAP_FEATURES_DISTORTION_WORLD 6
#define HEAP_ID_FIELD1 0
#define HANDLE_FLAG_CHECK 0
#define HANDLE_FLAG_SET 1
#define SEQ_SE_DP_UG_008_sseq 1
#define SEQ_SE_DP_UG_023_sseq 2
#define MAP_OBJ_STATUS_START_MOVEMENT (1 << 0)
#define MAP_OBJ_STATUS_1 (1 << 1)
#define MAP_OBJ_STATUS_END_MOVEMENT (1 << 2)

typedef struct MapObject {
    int x, y, z;            // y in half tiles, as Platinum's
    int xPrev, yPrev, zPrev;
    VecFx32 pos;
    VecFx32 spritePosOffset;
    int facingDir;
    int movingDir;
    int localID;
    int mapHeaderID;
    int graphicsID;
    u32 status;
} MapObject;

typedef struct FieldTask FieldTask;
typedef struct VarsFlags VarsFlags;
typedef struct PlayerAvatar PlayerAvatar;
typedef struct DistWorldSystem DistWorldSystem;
typedef struct {
    int mapHeaderID;
} Location;
typedef struct {
    void *dynamicMapFeaturesData;
} FieldSystemSub;
typedef struct FieldSystem {
    Location *location;
    FieldSystemSub *unk_04;
    void *saveData;
} FieldSystem;

FieldSystem *MapObject_FieldSystem(const MapObject *mapObj);
int MapObject_GetX(const MapObject *mapObj);
int MapObject_GetY(const MapObject *mapObj);
int MapObject_GetZ(const MapObject *mapObj);
void MapObject_SetX(MapObject *mapObj, int x);
void MapObject_SetY(MapObject *mapObj, int y);
void MapObject_SetZ(MapObject *mapObj, int z);
void MapObject_SetXPrev(MapObject *mapObj, int x);
void MapObject_SetYPrev(MapObject *mapObj, int y);
void MapObject_SetZPrev(MapObject *mapObj, int z);
void MapObject_GetPosPtr(const MapObject *mapObj, VecFx32 *pos);
void MapObject_SetPos(MapObject *mapObj, const VecFx32 *pos);
void MapObject_GetSpritePosOffset(const MapObject *mapObj, VecFx32 *pos);
void MapObject_SetSpritePosOffset(MapObject *mapObj, const VecFx32 *pos);
int MapObject_GetMovingDir(const MapObject *mapObj);
int MapObject_GetFacingDir(const MapObject *mapObj);
void MapObject_Face(MapObject *mapObj, int dir);
u32 MapObject_GetLocalID(const MapObject *mapObj);
void MapObject_SetLocalID(MapObject *mapObj, u32 id);
void MapObject_SetMapHeaderID(MapObject *mapObj, u32 id);
u32 MapObject_GetGraphicsID(const MapObject *mapObj);
void MapObject_SetStatusFlagOn(MapObject *mapObj, u32 flag);
void MapObject_SetStatusFlagOff(MapObject *mapObj, u32 flag);
void sub_020656DC(MapObject *mapObj);
void *Heap_AllocAtEnd(int heapID, u32 size);
void Heap_Free(void *p);
void Sound_PlayEffect(int seq);
void ScriptManager_Start(FieldTask *task, u16 scriptID, MapObject *obj, void *arg);
VarsFlags *SaveData_GetVarsFlags(void *saveData);
BOOL SystemFlag_HandleDistortionWorldPuzzleFinished(VarsFlags *varsFlags, int op);
// overlay 5's push test
MapObject *ov5_021E10D4(PlayerAvatar *playerAvatar, int dir);
u32 sub_02063EBC(MapObject *mapObj, int dir);
BOOL PersistedMapFeatures_IsCurrentDynamicMap(FieldSystem *fieldSystem, int id);
void ov5_021DFF88(int dir, FieldSystem *fieldSystem, PlayerAvatar *playerAvatar, MapObject *mapObj);

#endif
