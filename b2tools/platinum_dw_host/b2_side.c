// Our side of the harness: dw_core.c, the overlay's own file, called the way dw_field.c calls it on the DS: each frame
// the jump (an action command of ours there), the player's action command, the camera, the rotator; a held direction
// when the player is free: the jump points and camera triggers first, then the face's step. The land between the
// platforms is free and uses Platinum's land rule here (on the DS it is Black 2's own walking).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pearlb2/plat_dw.h"
#include "snap.h"

static DwTables *sTables;
static DwSystem sSys;
static DwBody sBody;
static DwActionRun sRun;
static BOOL sActionRunning;
static int sLastAction = -1;      // the last action set (Platinum's map object keeps it after it ends)
static BOOL sJumpActive;
static BOOL sElevatorActive;
static u32 sMoveState;

void B2_Open(const char *blob) {
    FILE *f = fopen(blob, "rb");
    long size;

    if (f == NULL) {
        fprintf(stderr, "%s: can't open\n", blob);
        exit(2);
    }
    fseek(f, 0, SEEK_END);
    size = ftell(f);
    fseek(f, 0, SEEK_SET);
    sTables = malloc(size);
    if (fread(sTables, 1, size, f) != (size_t)size || !DwTables_IsValid(sTables)) {
        fprintf(stderr, "%s: not the engine's tables\n", blob);
        exit(2);
    }
    fclose(f);
}

static u32 FloorOf(int mapHeaderID) {
    u32 i;

    for (i = 0; i < sTables->floorCount; i++) {
        if (DwTables_Floor(sTables, i)->map == mapHeaderID) {
            return i;
        }
    }
    fprintf(stderr, "map %d: no floor\n", mapHeaderID);
    exit(2);
}

int B2_FloorOffset(int mapHeaderID, int *offset) {
    const DwFloor *floor = DwTables_Floor(sTables, FloorOf(mapHeaderID));

    offset[0] = floor->offset[0];
    offset[1] = floor->offset[1];
    offset[2] = floor->offset[2];
    return 1;
}

// x, y, z: the floor's own tiles
void B2_Start(int mapHeaderID, int x, int y, int z, int face, int platform, int surfing) {
    memset(&sSys, 0, sizeof(sSys));
    memset(&sBody, 0, sizeof(sBody));
    DwSystem_Init(&sSys, sTables, FloorOf(mapHeaderID));
    DwCamera_Init(&sSys.camera, NULL);
    if (platform >= 0) {
        DwSystem_PrepareNewCurrentPlatform(&sSys, (u32)platform);
    }
    sSys.state = (u8)DwSystem_StateForKind(DwSystem_CurrentKind(&sSys));
    sSys.surfing = (u8)surfing;
    sSys.movingFlags = DwSystem_InitialMovingFlags(&sSys);
    sElevatorActive = FALSE;
    DwRotator_Init(&sSys.rotator, DwInitialRotation(sSys.state));
    sBody.x = sBody.prevX = (s16)x;
    sBody.y = sBody.prevY = (s16)y;
    sBody.z = sBody.prevZ = (s16)z;
    sBody.pos.x = x * DW_TILE + DW_TILE / 2;
    sBody.pos.y = y * DW_TILE;
    sBody.pos.z = z * DW_TILE + DW_TILE / 2;
    sBody.face = sBody.motion = (u16)face;
    sActionRunning = FALSE;
    sJumpActive = FALSE;
    sMoveState = DW_MOVE_STATE_NONE;
    sLastAction = -1;
}

void B2_Snapshot(DwSnap *snap) {
    snap->pos[0] = sBody.pos.x;
    snap->pos[1] = sBody.pos.y;
    snap->pos[2] = sBody.pos.z;
    snap->tile[0] = sBody.x;
    snap->tile[1] = sBody.y;
    snap->tile[2] = sBody.z;
    snap->face = sBody.face;
    snap->motion = sBody.motion;
    snap->jumpOffset[0] = sBody.jumpOffset.x;
    snap->jumpOffset[1] = sBody.jumpOffset.y;
    snap->jumpOffset[2] = sBody.jumpOffset.z;
    snap->state = sSys.state;
    snap->platform = sSys.platform >= sSys.floor->platformCount ? -1 : sSys.platform;
    snap->camera[0] = sSys.camera.current[0];
    snap->camera[1] = sSys.camera.current[1];
    snap->camera[2] = sSys.camera.current[2];
    snap->cameraActive = sSys.camera.active;
    snap->rotation = DwRotator_Frame(&sSys.rotator);
    snap->action = sLastAction;
    snap->map = sSys.floor->map;
    snap->spriteY = sElevatorActive ? sSys.elevator.spriteY : 0;
    snap->movingFlags = sSys.movingFlags;
}

void B2_BlackTwoCamera(unsigned short *pitch, unsigned short *yaw) {
    DwCamera_BlackTwoPitchYaw(&sSys.camera, pitch, yaw);
}

static void StartAction(u16 action) {
    DwActionRun_Start(&sRun, &sBody, action);
    sActionRunning = TRUE;
    sLastAction = action;
}

static void Frame(DwSnapFunc func, void *arg) {
    DwSnap snap;
    u16 face;

    if (sJumpActive) {
        if (DwSystem_JumpTick(&sSys, &sBody, !sActionRunning, &face) == TRUE) {
            sJumpActive = FALSE;
        }
        if (face != DW_ACTION_NONE) {
            StartAction(face);
        }
    }
    if (sElevatorActive && DwSystem_ElevatorTick(&sSys, &sBody) == DW_ELEVATOR_FINISHED) {
        sElevatorActive = FALSE;
    }
    if (sActionRunning && DwActionRun_Tick(&sRun, &sBody) == TRUE) {
        sActionRunning = FALSE;
    }
    DwCamera_Tick(&sSys.camera);
    DwRotator_Tick(&sSys.rotator);
    B2_Snapshot(&snap);
    func(arg, &snap);
}

// Platinum's land rule, for the free land of the harness (PlayerAvatar_UpdateMoveState, _SetMovement_Turning, _NotMoving,
// _NormalOverworld with nothing in the way)
static u16 LandMove(u32 dir, BOOL running) {
    if (dir > DW_DIR_RIGHT) {
        sMoveState = DW_MOVE_STATE_NONE;
        return DW_ACTION_FACE + sBody.face;
    }
    if (sBody.face != dir && sMoveState != DW_MOVE_STATE_MOVING) {
        sMoveState = DW_MOVE_STATE_TURNING;
        sBody.motion = (u16)dir;
        return DW_ACTION_WALK_ON_SPOT_FASTER + dir;
    }
    sMoveState = DW_MOVE_STATE_MOVING;
    return (running ? DW_ACTION_RUN : DW_ACTION_WALK_NORMAL) + dir;
}

// After a step: an elevator on the tile rides (dw_field.c: the gimmick's step check after Black 2's land steps, and our
// floor steps' end)
int B2_StepEnd(DwSnapFunc func, void *arg) {
    const DwMovingPlatform *m = DwSystem_ElevatorAt(&sSys, sBody.x, sBody.y, sBody.z);
    int guard = 0;

    if (m == NULL) {
        return 0;
    }
    DwSystem_ElevatorStart(&sSys, m, &sBody);
    sElevatorActive = TRUE;
    while (sElevatorActive) {
        Frame(func, arg);
        if (++guard >= 1000) {
            fprintf(stderr, "our side: stuck in an elevator\n");
            exit(3);
        }
    }
    return 1;
}

int B2_Token(int dir, int running, DwSnapFunc func, void *arg) {
    u32 d = dir < 0 ? DW_DIR_NONE : (u32)dir;
    int guard = 0;
    u16 action;
    u32 speed;
    BOOL bump;

    while (sJumpActive || !(DwSystem_IsOnFace(&sSys)
                                ? DwSystem_CanStartMove(&sSys, &sBody, d, !sActionRunning, sRun.action.action)
                                : !sActionRunning)) {
        Frame(func, arg);
        if (++guard >= 400) {
            fprintf(stderr, "our side: stuck\n");
            exit(3);
        }
    }
    if (d <= DW_DIR_RIGHT && DwSystem_HandlePlayerMoved(&sSys, &sBody, d) == TRUE) {
        sJumpActive = TRUE;
        while (sJumpActive) {
            Frame(func, arg);
            if (++guard >= 400) {
                fprintf(stderr, "our side: stuck in a jump\n");
                exit(3);
            }
        }
        return 1;
    }
    if (DwSystem_IsOnFace(&sSys)) {
        action = DwSystem_DecideMove(&sSys, &sBody, d, &sMoveState, running, &speed, &bump);
    } else {
        action = LandMove(d, running);
    }
    if (action == DW_ACTION_FACE + sBody.face && d > DW_DIR_RIGHT) {
        // (MovementAction_Face: done in its frame)
    }
    StartAction(action);
    do {
        Frame(func, arg);
        if (++guard >= 400) {
            fprintf(stderr, "our side: stuck in an action\n");
            exit(3);
        }
    } while (sActionRunning);
    return 0;
}
