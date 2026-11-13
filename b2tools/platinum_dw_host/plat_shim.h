// What Platinum's extracted C (plat_extract.c) needs around it on the Mac: the types, the constants (the values of
// pokeplatinum's headers), and a map object, a player and a field system with only the fields the rules use. The
// functions are plat_shim.c's.
#ifndef PLAT_SHIM_H
#define PLAT_SHIM_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;
typedef int32_t fx32;
typedef int16_t fx16;
typedef int BOOL;
#define TRUE 1
#define FALSE 0
#define FX32_SHIFT 12
#define FX32_ONE 4096
#define FX32_CONST(x) ((fx32)((x) * 4096))
#define S16_SIGN_MASK 0x8000

typedef struct {
    fx32 x, y, z;
} VecFx32;

#define GF_ASSERT(x) do { if (!(x)) { fprintf(stderr, "Platinum's assert: %s (%s:%d)\n", #x, __FILE__, __LINE__); abort(); } } while (0)

// constants/field/map.h
#define MAP_OBJECT_TILE_SIZE (16 * FX32_ONE)
#define INVALID_TERRAIN_ATTRIBUTES -1
#define OUT_OF_BOUNDS_TERRAIN_ATTRIBUTES -2
#define TERRAIN_ATTRIBUTES_COLLISION_SHIFT 15
#define TERRAIN_ATTRIBUTES_COLLISION_MASK 0x8000
#define TERRAIN_ATTRIBUTES_TILE_BEHAVIOR_MASK 0xFF
#include "constants/field/map_tile_behaviors.h"        // pokeplatinum's own

enum FaceDirection { FACE_UP = 0, FACE_DOWN, FACE_LEFT, FACE_RIGHT };
#define DIR_NORTH 0
#define DIR_SOUTH 1
#define DIR_WEST 2
#define DIR_EAST 3
#define DIR_NONE -1
#define MAX_DIR 4

enum AvatarDistortionState {
    AVATAR_DISTORTION_STATE_NONE = 0,
    AVATAR_DISTORTION_STATE_ACTIVE,
    AVATAR_DISTORTION_STATE_FLOOR,
    AVATAR_DISTORTION_STATE_WEST_WALL,
    AVATAR_DISTORTION_STATE_EAST_WALL,
    AVATAR_DISTORTION_STATE_CEILING,
    AVATAR_DISTORTION_STATE_MAX,
};
enum AvatarMoveState { AVATAR_MOVE_STATE_NONE = 0, AVATAR_MOVE_STATE_MOVING, AVATAR_MOVE_STATE_TURNING };
#define PLAYER_MOVE_STATE_NONE 0
enum { PLAYER_AVATAR_WALKING = 0, PLAYER_AVATAR_CYCLING, PLAYER_AVATAR_SURFING };
enum { PLAYER_ACTION_SPEED_NONE = 0, PLAYER_ACTION_SPEED_NOT_MOVING, PLAYER_ACTION_SPEED_SLOWER,
       PLAYER_ACTION_SPEED_SLOW, PLAYER_ACTION_SPEED_NORMAL, PLAYER_ACTION_SPEED_FAST };
// constants/player_avatar.h (copied: the header includes a generated one)
#define PLAYER_COLLISION_NONE 0
#define PLAYER_COLLISION_WILL_COLLIDE (1 << 0)
#define PLAYER_COLLISION_1 (1 << 1)
#define PLAYER_COLLISION_JUMP (1 << 2)
#define PLAYER_COLLISION_WARP (1 << 3)
#define PLAYER_COLLISION_BIKE_RAMP (1 << 4)
#define PLAYER_COLLISION_WATER (1 << 5)
#define PLAYER_COLLISION_BIKE_BRIDGE (1 << 6)
#define PLAYER_COLLISION_JUMP_TWICE (1 << 7)
#include "constants/map_object.h"            // pokeplatinum's own: the status bits, MAP_OBJ_COLLISION_

// generated/movement_actions.txt, by number
enum MovementAction {
    MOVEMENT_ACTION_FACE_NORTH = 0,
    MOVEMENT_ACTION_WALK_NORMAL_NORTH = 12,
    MOVEMENT_ACTION_WALK_FAST_NORTH = 16,
    MOVEMENT_ACTION_WALK_ON_SPOT_SLOW_NORTH = 28,
    MOVEMENT_ACTION_WALK_ON_SPOT_SLOW_SOUTH,
    MOVEMENT_ACTION_WALK_ON_SPOT_SLOW_WEST,
    MOVEMENT_ACTION_WALK_ON_SPOT_SLOW_EAST,
    MOVEMENT_ACTION_WALK_ON_SPOT_FASTER_NORTH = 40,
    MOVEMENT_ACTION_RUN_NORTH = 88,
    MOVEMENT_ACTION_105 = 105, MOVEMENT_ACTION_106, MOVEMENT_ACTION_107, MOVEMENT_ACTION_108, MOVEMENT_ACTION_109,
    MOVEMENT_ACTION_110, MOVEMENT_ACTION_111, MOVEMENT_ACTION_112, MOVEMENT_ACTION_113, MOVEMENT_ACTION_114,
    MOVEMENT_ACTION_115, MOVEMENT_ACTION_116,
    MOVEMENT_ACTION_JUMP_DISTORTION_WORLD_NORTH = 117,
    MOVEMENT_ACTION_121 = 121, MOVEMENT_ACTION_122, MOVEMENT_ACTION_123, MOVEMENT_ACTION_124, MOVEMENT_ACTION_125,
    MOVEMENT_ACTION_126, MOVEMENT_ACTION_127, MOVEMENT_ACTION_128, MOVEMENT_ACTION_129, MOVEMENT_ACTION_130,
    MOVEMENT_ACTION_131, MOVEMENT_ACTION_132,
    MAX_MOVEMENT_ACTION = 160,
    MOVEMENT_ACTION_NONE = 0xff,
};

#define JUMP_HEIGHT_HIGH 0
#define JUMP_HEIGHT_LOW 1
#define JUMP_HEIGHT_NORMAL 2
#define SEQ_NONE 0
#define SEQ_SE_DP_WALL_HIT_sseq 1
#define SEQ_SE_PL_SUTYA2_sseq_3 2
#define HEAP_ID_FIELD1 0

typedef struct MapObject {
    u32 status;
    int x, y, z;          // y in half tiles, as Platinum's
    int xPrev, yPrev, zPrev;
    VecFx32 pos;
    VecFx32 spriteJumpOffset;
    int facingDir, prevFacingDir;
    int movingDir, prevMovingDir;
    int movementAction;
    int movementStep;
    u8 movementData[64];
    BOOL heightCalcDisabled;
    VecFx32 spritePosOffset;
    int data[3];
} MapObject;

typedef struct PlayerAvatar {
    MapObject *mapObj;
    int distortionState;
    int moveState;
    int playerState;
    int movementAction;
    int speed;
    BOOL running;
} PlayerAvatar;

typedef struct Billboard Billboard;
typedef struct NNSG3dAnmObj NNSG3dAnmObj;
typedef struct {
    int unused;
} NNSFndAllocator;
typedef struct NARC NARC;
typedef struct DistWorldSystem DistWorldSystem;
typedef struct FieldTask FieldTask;
typedef struct PlayerData PlayerData;
typedef struct LandDataManager LandDataManager;
typedef void PersistedMapFeatures;

typedef struct {
    u16 x, y, z;
    u16 padding_06;
} CameraAngle;

typedef struct Camera Camera;
typedef struct SysTask SysTask;

typedef struct DistWorldPersistedData {
    u32 valid : 1;
    u32 hiddenGhostPropGroups : 24;
    u32 currentFloatingPlatformIndex : 4;
    u32 padding : 3;
    u16 cameraAngleX;
    u16 cameraAngleY;
    u16 cameraAngleZ;
    u16 movingPlatformFlags;
    u32 boulderPuzzleFlags;
    u8 dummy10[16];
} DistWorldPersistedData;

typedef struct FieldSystem {
    PlayerAvatar *playerAvatar;
    struct {
        void *dynamicMapFeaturesData;
    } *unk_04;
    int mapHeaderID;
    void *saveData;
    void *mapObjMan;
} FieldSystem;

typedef BOOL (*FieldTaskFunc)(FieldTask *task);

// The map header ids of the Distortion World (generated/map_headers.txt)
enum MapHeaderID {
    MAP_HEADER_DISTORTION_WORLD_1F = 573,
    MAP_HEADER_DISTORTION_WORLD_B1F,
    MAP_HEADER_DISTORTION_WORLD_B2F,
    MAP_HEADER_DISTORTION_WORLD_B3F,
    MAP_HEADER_DISTORTION_WORLD_B4F,
    MAP_HEADER_DISTORTION_WORLD_B5F = 579,
    MAP_HEADER_DISTORTION_WORLD_B6F,
    MAP_HEADER_DISTORTION_WORLD_B7F,
    MAP_HEADER_DISTORTION_WORLD_GIRATINA_ROOM,
    MAP_HEADER_DISTORTION_WORLD_TURNBACK_CAVE_ROOM,
    MAP_HEADER_COUNT = 593,
    MAP_HEADER_INVALID = 593,
};
#define WATERFALL_B4F_X 104
#define WATERFALL_B4F_Y 170
#define WATERFALL_B4F_START_Z 76
#define WATERFALL_B4F_END_Z 79
#define WATERFALL_B5F_X 104
#define WATERFALL_B5F_Y 128
#define WATERFALL_B5F_START_Z 76
#define WATERFALL_B5F_END_Z 79
#define DISTORTION_WORLD_CAMERA_PERSISTED_ANGLES_FACTOR 0x100
// ov9_02249960.c's own constants
#define DISTORTION_WORLD_MAP_COUNT 10
#define MOVING_PLATFORM_MAP_COUNT 8
#define MOVING_PLATFORM_MANAGER_ANIMATOR_COUNT 32
#define MOVING_PLATFORM_VIBRATION_Y_DELTA (FX32_ONE * 3)
#define ELEVATOR_PLATFORM_PATH_COUNT 22
#define ELEVATOR_PLATFORM_PATH_INVALID ELEVATOR_PLATFORM_PATH_COUNT
#define ELEVATOR_PLATFORM_VIBRATION_Y_DELTA (FX32_ONE * 6)
#define SEQ_SE_PL_FW089_sseq 3
typedef struct OverworldAnimManager OverworldAnimManager;
typedef struct VarsFlags VarsFlags;
#include "constants/distortion_world.h"      // pokeplatinum's own: the progress values
#define FIELD_TASK_CONTEXT_MAX_SIZE 128

#define B7F_TELEPORT_TILE_X 89
#define B7F_TELEPORT_TILE_Y 65
#define B7F_TELEPORT_TILE_Z 57
#define B7F_TELEPORT_SCRIPT_ID 2
#define GIRATINA_ROOM_TELEPORT_TILE_X 15
#define GIRATINA_ROOM_TELEPORT_TILE_Y 1
#define GIRATINA_ROOM_TELEPORT_TILE_Z 25
#define GIRATINA_ROOM_TELEPORT_SCRIPT_ID 4
#define HANDLE_FLAG_CHECK 0
enum FloorLoadDirection { FLOOR_LOAD_NONE = 0, FLOOR_LOAD_PREVIOUS, FLOOR_LOAD_NEXT };

// plat_shim.c
MapObject *PlayerAvatar_GetMapObject(PlayerAvatar *playerAvatar);
void MapObject_GetSpritePosOffset(MapObject *mapObj, VecFx32 *offset);
void MapObject_SetSpritePosOffset(MapObject *mapObj, const VecFx32 *offset);
void MapObject_SetDataAt(MapObject *mapObj, int value, int index);
void MapObject_SetLocalID(MapObject *mapObj, int id);
void MapObject_SetMapHeaderID(MapObject *mapObj, int id);
void MapObject_SetScript(MapObject *mapObj, int script);
MapObject *MapObjMan_LocalMapObjByIndex(void *man, int index);
void PlayerAvatar_SetHeightCalculationEnabledAndUpdate(PlayerAvatar *playerAvatar, BOOL enabled);
VarsFlags *SaveData_GetVarsFlags(void *save);
void ScriptManager_Set(FieldSystem *fieldSystem, int script, void *arg);
void Sound_StopEffect(int seq, int frames);
BOOL SystemFlag_HandleDistortionWorldPuzzleFinished(VarsFlags *varsFlags, int op);
int SystemVars_GetDistortionWorldCyrusApperanceState(VarsFlags *varsFlags);
int SystemVars_GetDistortionWorldProgress(VarsFlags *varsFlags);
void *ov5_021EB1A0(MapObject *mapObj);
void ov5_021EDEB4(MapObject *mapObj, void *billboard);
FieldSystem *MapObject_FieldSystem(MapObject *mapObj);
int MapObject_GetLocalID(const MapObject *mapObj);
int MapObject_GetX(const MapObject *mapObj);
int MapObject_GetY(const MapObject *mapObj);
int MapObject_GetZ(const MapObject *mapObj);
void MapObject_SetX(MapObject *mapObj, int v);
void MapObject_SetY(MapObject *mapObj, int v);
void MapObject_SetZ(MapObject *mapObj, int v);
void MapObject_AddX(MapObject *mapObj, int v);
void MapObject_AddY(MapObject *mapObj, int v);
void MapObject_AddZ(MapObject *mapObj, int v);
void MapObject_SetXPrev(MapObject *mapObj, int v);
void MapObject_SetYPrev(MapObject *mapObj, int v);
void MapObject_SetZPrev(MapObject *mapObj, int v);
void MapObject_GetPosPtr(const MapObject *mapObj, VecFx32 *pos);
void MapObject_SetPos(MapObject *mapObj, const VecFx32 *pos);
VecFx32 *MapObject_GetSpriteJumpOffset1(MapObject *mapObj);
void MapObject_SetSpriteJumpOffset(MapObject *mapObj, const VecFx32 *offset);
int MapObject_GetFacingDir(const MapObject *mapObj);
int MapObject_GetMovingDir(const MapObject *mapObj);
int MapObject_GetMovementAction(const MapObject *mapObj);
int MapObject_GetMovementStep(const MapObject *mapObj);
void MapObject_SetMovementAction(MapObject *mapObj, int action);
void MapObject_SetMovementStep(MapObject *mapObj, int step);
void MapObject_AdvanceMovementStep(MapObject *mapObj);
void *MapObject_InitMovementData(MapObject *mapObj, int size);
void *MapObject_GetMovementData(MapObject *mapObj);
BOOL MapObject_CheckStatusFlag(const MapObject *mapObj, u32 flag);
BOOL MapObject_CheckStatus(const MapObject *mapObj, u32 flag);
void MapObject_SetStatusFlagOn(MapObject *mapObj, u32 flag);
void MapObject_SetStatusFlagOff(MapObject *mapObj, u32 flag);
void MapObject_SetStartMovement(MapObject *mapObj);
void MapObject_SetHeightCalculationDisabled(MapObject *mapObj, BOOL disabled);
int MapObject_RecalculateObjectHeight(MapObject *mapObj);
int MapObject_GetDxFromDir(int dir);
int MapObject_GetDzFromDir(int dir);
void sub_02062A0C(MapObject *mapObj, int v);
void sub_02062B68(MapObject *mapObj);
BOOL sub_02063F00(MapObject *mapObj, int x, int y, int z);
enum MovementAction MovementAction_TurnActionTowardsDir(int dir, enum MovementAction action);
void Sound_PlayEffect(int seq);
void ov5_021F3678(MapObject *mapObj, int dir);
void *Heap_Alloc(int heap, u32 size);
void *Heap_AllocAtEnd(int heap, u32 size);
void Heap_Free(void *p);
u32 NARC_GetMemberSize(NARC *narc, u32 index);
void NARC_ReadWholeMember(NARC *narc, u32 index, void *out);
PlayerData *PlayerAvatar_PlayerData(PlayerAvatar *playerAvatar);
BOOL PlayerData_HasRunningShoes(PlayerData *data);
BOOL PlayerAvatar_IsRunButtonHeld(PlayerAvatar *playerAvatar, u16 keyPress);
void PlayerAvatar_IncrementStepsRecord(PlayerAvatar *playerAvatar);
void PlayerAvatar_StartStep(PlayerAvatar *playerAvatar);
int PlayerAvatar_GetPlayerState(PlayerAvatar *playerAvatar);
int PlayerAvatar_MapDistortionState(PlayerAvatar *playerAvatar);
BOOL PlayerAvatar_DistortionGravityChanged(PlayerAvatar *playerAvatar);
void PlayerAvatar_SetDistortionState(PlayerAvatar *playerAvatar, int state);
void PlayerAvatar_ClearSpeed(PlayerAvatar *playerAvatar);
int PlayerAvatar_GetFacingDir(PlayerAvatar *playerAvatar);
int PlayerAvatar_GetMovingDir(PlayerAvatar *playerAvatar);
int PlayerAvatar_GetMoveState(PlayerAvatar *playerAvatar);
void PlayerAvatar_SetMoveState(PlayerAvatar *playerAvatar, int state);
void PlayerAvatar_SetMovementActionAndSpeed(PlayerAvatar *playerAvatar, int action, int speed);
int PlayerAvatar_GetMoveStateFromPlayerAvatarState(PlayerAvatar *playerAvatar, int dir);
u32 PlayerAvatar_CheckCollision(PlayerAvatar *playerAvatar, MapObject *mapObj, int dir);
void PlayerAvatar_SetMovement_NormalOverworld(PlayerAvatar *playerAvatar, MapObject *mapObj, int dir, u16 keyPad, u16 keyPress);
BOOL PersistedMapFeatures_IsCurrentDynamicMap(FieldSystem *fieldSystem, int id);
void FieldSystem_CreateTask(FieldSystem *fieldSystem, FieldTaskFunc func, void *env);
FieldSystem *FieldTask_GetFieldSystem(FieldTask *task);
void *FieldTask_GetEnv(FieldTask *task);
void Camera_SetAngleAroundTarget(const CameraAngle *angle, Camera *camera);
// The dynamic map feature ids and persisted map features, as far as the rules ask
#define DYNAMIC_MAP_FEATURES_DISTORTION_WORLD 8
void *MiscSaveBlock_GetPersistedMapFeatures(void *save);
void *FieldSystem_GetSaveData(FieldSystem *fieldSystem);
int PersistedMapFeatures_GetID(void *features);
int GetNullTileBehaviorID(void);
void HandleGhostPropTriggerAt(DistWorldSystem *system, int x, int y, int z, int dir);
void RunEventCommands(DistWorldSystem *system, const void *cmds);
extern const void *sMapEventB4F_Waterfall;
extern const void *sMapEventB5F_Waterfall;
#define sMapEventB4F_Waterfall NULL
#define sMapEventB5F_Waterfall NULL

#endif
