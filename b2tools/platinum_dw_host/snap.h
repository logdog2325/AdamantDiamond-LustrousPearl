// One frame of the player, as both sides report it (Platinum's in its shared world; the sim compares them in the floor's
// own tiles). Plain ints, so the two sides' headers never meet.
#ifndef DW_SNAP_H
#define DW_SNAP_H

typedef struct {
    int pos[3];         // fx32 world position
    int tile[3];        // grid: x, tile height, z
    int face;
    int motion;
    int jumpOffset[3];
    int state;          // AvatarDistortionState
    int platform;       // the current platform, or -1
    int camera[3];      // the camera's current angles (Platinum's, without the base)
    int cameraActive;
    int rotation;       // the sprite's rotation, degrees
    int action;         // the movement action running, or -1
    int map;            // the floor (Platinum's map header)
    int spriteY;        // the drawn offset of an elevator's shake (Platinum's sprite position offset)
    int movingFlags;    // where the elevators stand (Platinum's persisted moving platform flags)
} DwSnap;

typedef void (*DwSnapFunc)(void *arg, const DwSnap *snap);

// plat_shim.c: Platinum's side
void Plat_Open(const char *twArc, const char *twArcAttr);
// platform: -1 on the land, or a platform to stand on (as InitPlayer restores the saved one)
void Plat_Start(int mapHeaderID, int x, int y, int z, int face, int platform, int surfing);
// One held direction (0-3, or -1 for none) until it has made one decision and its action is done; snap after each
// frame. Returns 1 if the direction started a jump
int Plat_Token(int dir, int running, DwSnapFunc func, void *arg);
// After a step (Field_ProcessStep): an elevator there rides, frame by frame. Returns 1 if one did
int Plat_StepEnd(DwSnapFunc func, void *arg);
void Plat_Snapshot(DwSnap *snap);

// b2_side.c: ours (dw_core.c)
void B2_Open(const char *blob);
int B2_FloorOffset(int mapHeaderID, int *offset);
void B2_Start(int mapHeaderID, int x, int y, int z, int face, int platform, int surfing);
int B2_Token(int dir, int running, DwSnapFunc func, void *arg);
int B2_StepEnd(DwSnapFunc func, void *arg);
void B2_Snapshot(DwSnap *snap);
void B2_BlackTwoCamera(unsigned short *pitch, unsigned short *yaw);

#endif
