// Platinum's side of the harness: what plat_extract.c (Platinum's own C) calls, and a frame loop in the order of
// Platinum's field: the field task (the jump), the player's action (sub_020658DC), the camera task, the rotators.
// The land is free to walk in both sides' harness (it is Black 2's own on the DS); everything on a platform is
// Platinum's code.
#include "plat_shim.h"
#include "snap.h"

// Platinum's own functions (extract.py), in this file so their statics are in reach
#include "plat_extract.c"

#define TASK_NONE NULL

static MapObject sMapObj;
static PlayerAvatar sAvatar;
static FieldSystem sField;
static struct {
    void *dynamicMapFeaturesData;
} sUnk04;
static DistWorldPersistedData sPersisted;
static DistWorldSystem sSystem;
static DistWorldMapObjectRotator sRotators[6];
static FieldTaskFunc sTask;
static void *sTaskEnv;

struct NARC {
    int count;
    unsigned char *base;
    unsigned int (*offsets)[2];
};

static NARC sMain, sAttr;

static void ReadNarc(const char *path, NARC *narc) {
    FILE *f = fopen(path, "rb");
    long size;
    unsigned char *d;
    unsigned int btaf, btnf, gmif;

    GF_ASSERT(f != NULL);
    fseek(f, 0, SEEK_END);
    size = ftell(f);
    fseek(f, 0, SEEK_SET);
    d = malloc(size);
    GF_ASSERT(fread(d, 1, size, f) == (size_t)size);
    fclose(f);
    GF_ASSERT(memcmp(d, "NARC", 4) == 0);
    btaf = *(u16 *)(d + 0xc);
    narc->count = *(u16 *)(d + btaf + 8);
    narc->offsets = (unsigned int (*)[2])(d + btaf + 12);
    btnf = btaf + *(u32 *)(d + btaf + 4);
    gmif = btnf + *(u32 *)(d + btnf + 4);
    narc->base = d + gmif + 8;
}

u32 NARC_GetMemberSize(NARC *narc, u32 index) {
    GF_ASSERT((int)index < narc->count);
    return narc->offsets[index][1] - narc->offsets[index][0];
}

void NARC_ReadWholeMember(NARC *narc, u32 index, void *out) {
    memcpy(out, narc->base + narc->offsets[index][0], NARC_GetMemberSize(narc, index));
}

void *Heap_Alloc(int heap, u32 size) { return calloc(1, size); }
void *Heap_AllocAtEnd(int heap, u32 size) { return calloc(1, size); }
void Heap_Free(void *p) { free(p); }

MapObject *PlayerAvatar_GetMapObject(PlayerAvatar *playerAvatar) { return playerAvatar->mapObj; }
FieldSystem *MapObject_FieldSystem(MapObject *mapObj) { return &sField; }
int MapObject_GetLocalID(const MapObject *mapObj) { return 0xff; }
int MapObject_GetX(const MapObject *mapObj) { return mapObj->x; }
int MapObject_GetY(const MapObject *mapObj) { return mapObj->y; }
int MapObject_GetZ(const MapObject *mapObj) { return mapObj->z; }
void MapObject_SetX(MapObject *mapObj, int v) { mapObj->x = v; }
void MapObject_SetY(MapObject *mapObj, int v) { mapObj->y = v; }
void MapObject_SetZ(MapObject *mapObj, int v) { mapObj->z = v; }
void MapObject_AddX(MapObject *mapObj, int v) { mapObj->x += v; }
void MapObject_AddY(MapObject *mapObj, int v) { mapObj->y += v; }
void MapObject_AddZ(MapObject *mapObj, int v) { mapObj->z += v; }
void MapObject_SetXPrev(MapObject *mapObj, int v) { mapObj->xPrev = v; }
void MapObject_SetYPrev(MapObject *mapObj, int v) { mapObj->yPrev = v; }
void MapObject_SetZPrev(MapObject *mapObj, int v) { mapObj->zPrev = v; }
void MapObject_GetPosPtr(const MapObject *mapObj, VecFx32 *pos) { *pos = mapObj->pos; }
void MapObject_SetPos(MapObject *mapObj, const VecFx32 *pos) { mapObj->pos = *pos; }
VecFx32 *MapObject_GetSpriteJumpOffset1(MapObject *mapObj) { return &mapObj->spriteJumpOffset; }
void MapObject_SetSpriteJumpOffset(MapObject *mapObj, const VecFx32 *offset) { mapObj->spriteJumpOffset = *offset; }
int MapObject_GetFacingDir(const MapObject *mapObj) { return mapObj->facingDir; }
int MapObject_GetMovingDir(const MapObject *mapObj) { return mapObj->movingDir; }
int MapObject_GetMovementAction(const MapObject *mapObj) { return mapObj->movementAction; }
int MapObject_GetMovementStep(const MapObject *mapObj) { return mapObj->movementStep; }
void MapObject_SetMovementAction(MapObject *mapObj, int action) { mapObj->movementAction = action; }
void MapObject_SetMovementStep(MapObject *mapObj, int step) { mapObj->movementStep = step; }
void MapObject_AdvanceMovementStep(MapObject *mapObj) { mapObj->movementStep++; }
void *MapObject_InitMovementData(MapObject *mapObj, int size)
{
    GF_ASSERT(size <= (int)sizeof(mapObj->movementData));
    memset(mapObj->movementData, 0, sizeof(mapObj->movementData));
    return mapObj->movementData;
}
void *MapObject_GetMovementData(MapObject *mapObj) { return mapObj->movementData; }
BOOL MapObject_CheckStatusFlag(const MapObject *mapObj, u32 flag) { return (mapObj->status & flag) ? TRUE : FALSE; }
BOOL MapObject_CheckStatus(const MapObject *mapObj, u32 flag) { return (mapObj->status & flag) ? TRUE : FALSE; }
void MapObject_SetStatusFlagOn(MapObject *mapObj, u32 flag) { mapObj->status |= flag; }
void MapObject_SetStatusFlagOff(MapObject *mapObj, u32 flag) { mapObj->status &= ~flag; }
void MapObject_SetStartMovement(MapObject *mapObj) { mapObj->status |= MAP_OBJ_STATUS_START_MOVEMENT; }
void MapObject_SetHeightCalculationDisabled(MapObject *mapObj, BOOL disabled) { mapObj->heightCalcDisabled = disabled; }
// No land in the harness: the height stays (on a platform it is disabled anyway)
int MapObject_RecalculateObjectHeight(MapObject *mapObj) { return 0; }
int MapObject_GetDxFromDir(int dir) { static const int dx[4] = { 0, 0, -1, 1 }; return dx[dir]; }
int MapObject_GetDzFromDir(int dir) { static const int dz[4] = { -1, 1, 0, 0 }; return dz[dir]; }
void sub_02062A0C(MapObject *mapObj, int v) { }
void sub_02062B68(MapObject *mapObj) { }
// Nobody else in the harness's Distortion World
BOOL sub_02063F00(MapObject *mapObj, int x, int y, int z) { return FALSE; }

// The actions come four in a row, north south west east (generated/movement_actions.txt; extract.py's table)
enum MovementAction MovementAction_TurnActionTowardsDir(int dir, enum MovementAction action)
{
    static const int bases[] = { 0, 12, 16, 28, 40, 88, 117 };
    unsigned i;

    for (i = 0; i < sizeof(bases) / sizeof(bases[0]); i++) {
        if ((int)action >= bases[i] && (int)action < bases[i] + 4) {
            return bases[i] + dir;
        }
    }
    GF_ASSERT(FALSE);
    return action;
}

void Sound_PlayEffect(int seq) { }
void ov5_021F3678(MapObject *mapObj, int dir) { }
PlayerData *PlayerAvatar_PlayerData(PlayerAvatar *playerAvatar) { return NULL; }
BOOL PlayerData_HasRunningShoes(PlayerData *data) { return TRUE; }
BOOL PlayerAvatar_IsRunButtonHeld(PlayerAvatar *playerAvatar, u16 keyPress) { return playerAvatar->running; }
void PlayerAvatar_IncrementStepsRecord(PlayerAvatar *playerAvatar) { }
void PlayerAvatar_StartStep(PlayerAvatar *playerAvatar) { }
int PlayerAvatar_GetPlayerState(PlayerAvatar *playerAvatar) { return playerAvatar->playerState; }
int PlayerAvatar_MapDistortionState(PlayerAvatar *playerAvatar) { return playerAvatar->distortionState; }
BOOL PlayerAvatar_DistortionGravityChanged(PlayerAvatar *playerAvatar)
{
    return playerAvatar->distortionState != AVATAR_DISTORTION_STATE_NONE &&
           playerAvatar->distortionState != AVATAR_DISTORTION_STATE_ACTIVE;
}
void PlayerAvatar_SetDistortionState(PlayerAvatar *playerAvatar, int state) { playerAvatar->distortionState = state; }
void PlayerAvatar_ClearSpeed(PlayerAvatar *playerAvatar) { playerAvatar->speed = 0; }
int PlayerAvatar_GetFacingDir(PlayerAvatar *playerAvatar) { return playerAvatar->mapObj->facingDir; }
int PlayerAvatar_GetMovingDir(PlayerAvatar *playerAvatar) { return playerAvatar->mapObj->movingDir; }
int PlayerAvatar_GetMoveState(PlayerAvatar *playerAvatar) { return playerAvatar->moveState; }
void PlayerAvatar_SetMoveState(PlayerAvatar *playerAvatar, int state) { playerAvatar->moveState = state; }
void PlayerAvatar_SetMovementActionAndSpeed(PlayerAvatar *playerAvatar, int action, int speed)
{
    playerAvatar->movementAction = action;
    playerAvatar->speed = speed;
}
int PlayerAvatar_GetMoveStateFromPlayerAvatarState(PlayerAvatar *playerAvatar, int dir) { return playerAvatar->moveState; }
// The land: free (Black 2's own collision decides there on the DS)
u32 PlayerAvatar_CheckCollision(PlayerAvatar *playerAvatar, MapObject *mapObj, int dir) { return PLAYER_COLLISION_NONE; }

// PlayerAvatar_SetMovement_NormalOverworld on free land, walking (player_move.c): a walk, or a run with B
void PlayerAvatar_SetMovement_NormalOverworld(PlayerAvatar *playerAvatar, MapObject *mapObj, int dir, u16 keyPad, u16 keyPress)
{
    int movementAction = MOVEMENT_ACTION_WALK_NORMAL_NORTH;
    int speed = PLAYER_ACTION_SPEED_NORMAL;

    if (playerAvatar->running) {
        movementAction = MOVEMENT_ACTION_RUN_NORTH;
        speed = PLAYER_ACTION_SPEED_FAST;
    }
    movementAction = MovementAction_TurnActionTowardsDir(dir, movementAction);
    PlayerAvatar_SetMovementActionAndSpeed(playerAvatar, movementAction, speed);
    LocalMapObj_SetAnimationCode(mapObj, movementAction);
}

BOOL PersistedMapFeatures_IsCurrentDynamicMap(FieldSystem *fieldSystem, int id) { return TRUE; }
void *MiscSaveBlock_GetPersistedMapFeatures(void *save) { return &sPersisted; }
void *FieldSystem_GetSaveData(FieldSystem *fieldSystem) { return NULL; }
int PersistedMapFeatures_GetID(void *features) { return DYNAMIC_MAP_FEATURES_DISTORTION_WORLD; }
int GetNullTileBehaviorID(void) { return 0; }
// The ghost props and the waterfalls' events are the world's (plat-dw-world): the routes never reach them
void HandleGhostPropTriggerAt(DistWorldSystem *system, int x, int y, int z, int dir) { }
void RunEventCommands(DistWorldSystem *system, const void *cmds)
{
    fprintf(stderr, "a waterfall event: not in the harness\n");
    abort();
}

void FieldSystem_CreateTask(FieldSystem *fieldSystem, FieldTaskFunc func, void *env)
{
    GF_ASSERT(sTask == TASK_NONE);
    sTask = func;
    sTaskEnv = env;
}
FieldSystem *FieldTask_GetFieldSystem(FieldTask *task) { return &sField; }
void *FieldTask_GetEnv(FieldTask *task) { return sTaskEnv; }


void MapObject_GetSpritePosOffset(MapObject *mapObj, VecFx32 *offset) { *offset = mapObj->spritePosOffset; }
void MapObject_SetSpritePosOffset(MapObject *mapObj, const VecFx32 *offset) { mapObj->spritePosOffset = *offset; }
void MapObject_SetDataAt(MapObject *mapObj, int value, int index) { mapObj->data[index] = value; }
void MapObject_SetLocalID(MapObject *mapObj, int id) { }
void MapObject_SetMapHeaderID(MapObject *mapObj, int id) { }
void MapObject_SetScript(MapObject *mapObj, int script) { }
MapObject *MapObjMan_LocalMapObjByIndex(void *man, int index) { abort(); }
void PlayerAvatar_SetHeightCalculationEnabledAndUpdate(PlayerAvatar *playerAvatar, BOOL enabled)
{
    playerAvatar->mapObj->heightCalcDisabled = !enabled;
}
VarsFlags *SaveData_GetVarsFlags(void *save) { return NULL; }
static int sScript = -1;
void ScriptManager_Set(FieldSystem *fieldSystem, int script, void *arg) { sScript = script; }
void Sound_StopEffect(int seq, int frames) { }
// A Distortion World entered for the first time: no progress, the puzzle not done, Cyrus already gone from B4F
BOOL SystemFlag_HandleDistortionWorldPuzzleFinished(VarsFlags *varsFlags, int op) { return FALSE; }
int SystemVars_GetDistortionWorldCyrusApperanceState(VarsFlags *varsFlags) { return 1; }
int SystemVars_GetDistortionWorldProgress(VarsFlags *varsFlags) { return 0; }
void *ov5_021EB1A0(MapObject *mapObj) { return NULL; }
void ov5_021EDEB4(MapObject *mapObj, void *billboard) { }

MapObject *Shim_NewPlatformMapObject(int x, int y, int z)
{
    MapObject *m = calloc(1, sizeof(MapObject));

    m->x = x;
    m->y = y * 2;
    m->z = z;
    return m;
}

OverworldAnimManager *Shim_NewProp(int x, int y, int z)
{
    ShimProp *p = calloc(1, sizeof(ShimProp));

    p->pos.x = x * MAP_OBJECT_TILE_SIZE + MAP_OBJECT_TILE_SIZE / 2;
    p->pos.y = y * MAP_OBJECT_TILE_SIZE;
    p->pos.z = z * MAP_OBJECT_TILE_SIZE + MAP_OBJECT_TILE_SIZE / 2;
    return (OverworldAnimManager *)p;
}

static void LoadFloorTables(DistWorldSystem *system, int mapHeaderID)
{
    if (system->mainArchive.mapFile.buffer != NULL) {
        free(system->mainArchive.mapFile.buffer);
    }
    if (system->mainArchive.floatingPlatformMan.terrainAttributes != NULL) {
        free(system->mainArchive.floatingPlatformMan.terrainAttributes);
    }
    memset(&system->mainArchive.mapFile, 0, sizeof(system->mainArchive.mapFile));
    memset(&system->mainArchive.floatingPlatformMan, 0, sizeof(system->mainArchive.floatingPlatformMan));
    memset(&system->mainArchive.floatingPlatformJumpPoints, 0, sizeof(system->mainArchive.floatingPlatformJumpPoints));
    memset(&system->mainArchive.cameraAngleTemplates, 0, sizeof(system->mainArchive.cameraAngleTemplates));
    DistWorldMapFile_Load(system, &system->mainArchive.mapFile, mapHeaderID);
    InitFloatingPlatformManager(system);
    InitFloatingPlatformJumpPoint(system);
    InitCameraAngleTemplates(system);
    system->mainArchive.floatingPlatformMan.currentPlatformIndex = system->mainArchive.floatingPlatformMan.platformCount;
}

// The floors' moving platforms: the active floor's and the one below's (Platinum keeps the two loaded)
static void InitFloorsMovingPlatforms(DistWorldSystem *system)
{
    const DistWorldMapConnections *c = GetConnectionsForMap(sField.mapHeaderID);
    int i;

    for (i = 0; i < MOVING_PLATFORM_MANAGER_ANIMATOR_COUNT; i++) {
        DistWorldMovingPlatformPropAnimator *a = &system->movingPlatformPropMan.animators[i];

        if (a->valid && a->mapHeaderID != c->currID && a->mapHeaderID != c->nextID && !a->preventDeletion) {
            a->valid = FALSE;
        }
    }
    InitMovingPlatformPropsForMap(system, c->currID);
    if (c->nextID != MAP_HEADER_INVALID) {
        InitMovingPlatformPropsForMap(system, c->nextID);
    }
}

void Shim_LoadFloor(DistWorldSystem *system, int dir)
{
    const DistWorldMapConnections *c = GetConnectionsForMap(sField.mapHeaderID);
    int dest = dir == FLOOR_LOAD_NEXT ? c->nextID : c->prevID;

    GF_ASSERT(dest != MAP_HEADER_INVALID);
    sField.mapHeaderID = dest;
    LoadFloorTables(system, dest);
    InitFloorsMovingPlatforms(system);
}

void Plat_Open(const char *twArc, const char *twArcAttr)
{
    ReadNarc(twArc, &sMain);
    ReadNarc(twArcAttr, &sAttr);
}

void Plat_Start(int mapHeaderID, int x, int y, int z, int face, int platform, int surfing)
{
    memset(&sMapObj, 0, sizeof(sMapObj));
    memset(&sAvatar, 0, sizeof(sAvatar));
    memset(&sPersisted, 0, sizeof(sPersisted));
    memset(sRotators, 0, sizeof(sRotators));
    if (sSystem.mainArchive.mapFile.buffer != NULL) {
        free(sSystem.mainArchive.mapFile.buffer);
    }
    if (sSystem.mainArchive.mapInfoFile.buffer != NULL) {
        free(sSystem.mainArchive.mapInfoFile.buffer);
    }
    if (sSystem.mainArchive.floatingPlatformMan.terrainAttributes != NULL) {
        free(sSystem.mainArchive.floatingPlatformMan.terrainAttributes);
    }
    memset(&sSystem, 0, sizeof(sSystem));
    sTask = TASK_NONE;
    sField.playerAvatar = &sAvatar;
    sField.unk_04 = (void *)&sUnk04;
    sUnk04.dynamicMapFeaturesData = &sSystem;
    sField.mapHeaderID = mapHeaderID;
    sAvatar.mapObj = &sMapObj;
    sAvatar.playerState = surfing ? PLAYER_AVATAR_SURFING : PLAYER_AVATAR_WALKING;
    sAvatar.distortionState = AVATAR_DISTORTION_STATE_ACTIVE;
    sMapObj.status = MAP_OBJ_STATUS_0;
    sMapObj.movementAction = MOVEMENT_ACTION_NONE;
    sMapObj.x = x;
    sMapObj.y = y * 2;
    sMapObj.z = z;
    sMapObj.xPrev = x;
    sMapObj.yPrev = y * 2;
    sMapObj.zPrev = z;
    sMapObj.pos.x = x * MAP_OBJECT_TILE_SIZE + MAP_OBJECT_TILE_SIZE / 2;
    sMapObj.pos.y = y * MAP_OBJECT_TILE_SIZE;
    sMapObj.pos.z = z * MAP_OBJECT_TILE_SIZE + MAP_OBJECT_TILE_SIZE / 2;
    sMapObj.facingDir = face;
    sMapObj.movingDir = face;
    sSystem.fieldSystem = &sField;
    sSystem.persistedData = &sPersisted;
    sSystem.mainNARC = &sMain;
    sSystem.attrNARC = &sAttr;
    DistWorldMapInfoFile_Load(sSystem.mainNARC, &sSystem.mainArchive.mapInfoFile);
    LoadFloorTables(&sSystem, mapHeaderID);
    InitPersistedData(&sSystem);
    InitFloorsMovingPlatforms(&sSystem);
    sSystem.cameraMan.baseAngle.x = -10750;
    sSystem.mapObjRotatorMan.count = 6;
    sSystem.mapObjRotatorMan.rotators = sRotators;
    {
        // InitPlayer: the state of the current platform's kind, the height calculation off on a platform, the rotation
        static const int rotAngles[6] = { 0, 0, 0, 90, 270, 180 };
        u32 kind;

        if (platform >= 0) {
            PrepareNewCurrentFloatingPlatform(&sSystem, platform);
        }
        kind = GetAvatarDistortionStateForFloatingPlatformKind(GetCurrentFloatingPlatformKind(&sSystem));
        sAvatar.distortionState = kind;
        MapObject_SetHeightCalculationDisabled(&sMapObj, kind != AVATAR_DISTORTION_STATE_ACTIVE);
        BindMapObjectRotator(&sSystem, &sMapObj, rotAngles[kind]);
    }
}

void Plat_Snapshot(DwSnap *snap)
{
    DistWorldFloatingPlatformManager *man = &sSystem.mainArchive.floatingPlatformMan;

    snap->pos[0] = sMapObj.pos.x;
    snap->pos[1] = sMapObj.pos.y;
    snap->pos[2] = sMapObj.pos.z;
    snap->tile[0] = sMapObj.x;
    snap->tile[1] = sMapObj.y / 2;
    snap->tile[2] = sMapObj.z;
    snap->face = sMapObj.facingDir;
    snap->motion = sMapObj.movingDir;
    snap->jumpOffset[0] = sMapObj.spriteJumpOffset.x;
    snap->jumpOffset[1] = sMapObj.spriteJumpOffset.y;
    snap->jumpOffset[2] = sMapObj.spriteJumpOffset.z;
    snap->state = sAvatar.distortionState;
    snap->platform = man->currentPlatformIndex >= man->platformCount ? -1 : man->currentPlatformIndex;
    snap->camera[0] = sSystem.cameraMan.currentAngle.x;
    snap->camera[1] = sSystem.cameraMan.currentAngle.y;
    snap->camera[2] = sSystem.cameraMan.currentAngle.z;
    snap->cameraActive = sSystem.cameraMan.transition.isActive;
    snap->rotation = DistWorld_GetMapObjectRotatorAnimFrame(&sField, &sMapObj);
    snap->action = sMapObj.movementAction == MOVEMENT_ACTION_NONE ? -1 : sMapObj.movementAction;
    snap->map = sField.mapHeaderID;
    snap->spriteY = sMapObj.spritePosOffset.y;
    snap->movingFlags = sPersisted.movingPlatformFlags;
}

static void Frame(DwSnapFunc func, void *arg)
{
    DwSnap snap;

    if (sTask != TASK_NONE && sTask(NULL) == TRUE) {
        sTask = TASK_NONE;
    }
    // MapObject_Move: the player's action while one is set
    if (MapObject_CheckStatus(&sMapObj, MAP_OBJ_STATUS_4)) {
        MapObject_DoMovementAction(&sMapObj);
    }
    CameraTransitionTask(NULL, &sSystem);
    TickMapObjectRotator(&sSystem, &sSystem.mapObjRotatorMan, &sRotators[0]);
    Plat_Snapshot(&snap);
    func(arg, &snap);
}

// Field_ProcessStep after a step: DistWorld_HandlePlayerPositionChanged, and an elevator's ride (its field task)
int Plat_StepEnd(DwSnapFunc func, void *arg)
{
    int guard = 0;

    sScript = -1;
    if (DistWorld_HandlePlayerPositionChanged(&sField) != TRUE) {
        return 0;
    }
    GF_ASSERT(sScript < 0);
    while (sTask != TASK_NONE) {
        Frame(func, arg);
        GF_ASSERT(++guard < 1000);
    }
    return 1;
}

// The field's input, a frame at a time (field_control.c, ov5_021DFDE0, PlayerAvatar_MoveMain for walking)
int Plat_Token(int dir, int running, DwSnapFunc func, void *arg)
{
    int guard = 0;

    sAvatar.running = running;
    while (sTask != TASK_NONE || PlayerAvatar_CheckStartMoveInternal(&sAvatar, dir) == FALSE) {
        Frame(func, arg);
        GF_ASSERT(++guard < 400);
    }
    if (dir != DIR_NONE && DistWorld_HandlePlayerMoved(&sField, dir) == TRUE) {
        while (sTask != TASK_NONE) {
            Frame(func, arg);
            GF_ASSERT(++guard < 400);
        }
        return 1;
    }
    PlayerAvatar_SetMovement_Normal(&sAvatar, &sMapObj, NULL, dir, 0, 0);
    do {
        Frame(func, arg);
        GF_ASSERT(++guard < 400);
    } while (LocalMapObj_IsAnimationSet(&sMapObj) == FALSE);
    return 0;
}
