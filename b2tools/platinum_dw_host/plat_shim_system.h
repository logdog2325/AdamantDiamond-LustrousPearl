// The Distortion World's system as far as the extracted rules use it (ov9_02249960.c's struct DistWorldSystem has
// these members among its others: the sky, the props, the floors drawn, the events)
#ifndef PLAT_SHIM_SYSTEM_H
#define PLAT_SHIM_SYSTEM_H

typedef struct DistWorldMainArchive {
    DistWorldMapInfoFile mapInfoFile;
    DistWorldMapFile mapFile;
    DistWorldFloatingPlatformManager floatingPlatformMan;
    DistWorldMapFileFloatingPlatformJumpPointSection floatingPlatformJumpPoints;
    DistWorldCameraAngleTemplates cameraAngleTemplates;
} DistWorldMainArchive;

struct DistWorldSystem {
    FieldSystem *fieldSystem;
    DistWorldMovingPlatformPropManager movingPlatformPropMan;
    DistWorldPersistedData *persistedData;
    NARC *mainNARC;
    NARC *attrNARC;
    DistWorldMainArchive mainArchive;
    DistWorldCameraManager cameraMan;
    DistWorldMapObjectRotatorManager mapObjRotatorMan;
    DistWorldFieldTaskContext fieldTaskCtx;
};

static u32 DistWorldSystem_GetMapHeaderID(DistWorldSystem *system)
{
    return system->fieldSystem->mapHeaderID;
}

static void SetPersistedCurrentFloatingPlatformIndex(DistWorldSystem *system, u32 floatingPlatformIndex)
{
    system->persistedData->currentFloatingPlatformIndex = floatingPlatformIndex;
}

static void SetPersistedCameraAngles(DistWorldSystem *system, u16 angleX, u16 angleY, u16 angleZ)
{
    system->persistedData->cameraAngleX = angleX;
    system->persistedData->cameraAngleY = angleY;
    system->persistedData->cameraAngleZ = angleZ;
}

// The rotator's billboard side: the harness has no billboards, every rotator stays valid
static int DistWorldMapObjectRotator_GetValidity(DistWorldMapObjectRotator *mapObjRotator)
{
    return 0;
}

static void DistWorldMapObjectRotatorManager_ResetRotator(DistWorldMapObjectRotatorManager *man, DistWorldMapObjectRotator *r)
{
}

static void DistWorldMapObjectRotatorManager_FreeRotator(DistWorldMapObjectRotatorManager *man, DistWorldMapObjectRotator *r)
{
}

static void DistWorldMapObjectRotatorManager_TryPrepareRotator(DistWorldMapObjectRotatorManager *man, DistWorldMapObjectRotator *r)
{
}

// The moving platforms' props and map objects (the harness draws nothing): a position each
typedef struct {
    VecFx32 pos;
} ShimProp;

MapObject *Shim_NewPlatformMapObject(int x, int y, int z);
OverworldAnimManager *Shim_NewProp(int x, int y, int z);

static MapObject *AddMovingPlatformMapObject(DistWorldSystem *system, int x, int y, int z, int index, int path, u32 mapHeaderID)
{
    return Shim_NewPlatformMapObject(x, y, z);
}

static OverworldAnimManager *InitAnimManagerForMovingPlatform(DistWorldSystem *system, DistWorldMovingPlatformPropAnimator *animator)
{
    return Shim_NewProp(animator->template.tileX, animator->template.tileY, animator->template.tileZ);
}

static VecFx32 *GetMovingPlatformPropPos(OverworldAnimManager *animMan)
{
    return &((ShimProp *)animMan)->pos;
}

// The floor's change (Task_LoadFloor's work in Platinum, over frames): at once, the new floor's tables
void Shim_LoadFloor(DistWorldSystem *system, int dir);
static void DistWorldMovingPlatformPropAnimator_SetPreventDeletion(DistWorldMovingPlatformPropAnimator *animator, BOOL preventDeletion);

static void LoadFloor(DistWorldSystem *system, DistWorldMovingPlatformPropAnimator *animator, enum FloorLoadDirection loadDir)
{
    Shim_LoadFloor(system, loadDir);
    DistWorldMovingPlatformPropAnimator_SetPreventDeletion(animator, FALSE);
}

static BOOL IsFloorLoaderActive(DistWorldSystem *system)
{
    return FALSE;
}

// The world's events and Cyrus on B4F (plat-dw-world): the routes never reach them
static BOOL HandleEventAt(DistWorldSystem *system, int playerX, int playerY, int playerZ)
{
    return FALSE;
}

static int DistWorldElevatorPlatform_CyrusB4FStartAnimation(DistWorldSystem *system, DistWorldElevatorPlatform *e)
{
    abort();
}

static int DistWorldElevatorPlatform_CyrusB4FEndAnimation(DistWorldSystem *system, DistWorldElevatorPlatform *e)
{
    abort();
}

#define MAP_OBJECT_ROTATOR_VALIDITY_OK 0
#define MAP_OBJECT_ROTATOR_VALIDITY_NEEDS_RESET 1
#define MAP_OBJECT_ROTATOR_VALIDITY_NEEDS_FREE 2

#endif
