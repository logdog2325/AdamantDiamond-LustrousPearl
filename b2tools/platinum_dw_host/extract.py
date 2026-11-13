"""Platinum's own C for the Distortion World harness: copies the functions and tables the rules are made of, word for
word, from pokeplatinum's sources into one file (plat_extract.c) that compiles on the Mac with plat_shim.h.

    python3 extract.py OUT.c

Nothing is rewritten: a function is taken from its first line to the closing brace at the start of a line. What the
functions call outside this list (the map object's fields, the heap, the archives, sounds, the land) is plat_shim.c's.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PLAT = os.path.join(ROOT, 'external', 'pokeplatinum', 'src')

OV9 = [
    'DistWorldBounds_AreCoordinatesInBounds', 'CalculateCameraAngleDelta', 'ApplyRotationToTarget',
    'ApplyRotationToTargetFx32',
    'DistWorldMapInfoFile_Load', 'DistWorldMapInfoFile_FindForMap', 'FindMapInfo', 'FindMapFileIndex',
    'DistWorldMapFile_Load', 'DistWorldMapFile_GetFloatingPlatformSectionSize',
    'DistWorldMapFile_GetFloatingPlatformCount', 'DistWorldMapFile_GetFloatingPlatformSectionTemplates',
    'DistWorldMapFile_GetFloatingPlatformJumpPointSectionSize', 'DistWorldMapFile_GetFloatingPlatformJumpPointCount',
    'DistWorldMapFile_GetFloatingPlatformJumpPointTemplates', 'DistWorldMapFile_GetCameraAngleSectionSize',
    'DistWorldMapFile_GetCameraAngleCount', 'DistWorldMapFile_GetCameraAngleTemplates',
    'InitFloatingPlatformManager', 'HasFloatingPlatformAtCoords', 'FindAndPrepareNewCurrentFloatingPlatform',
    'PrepareNewCurrentFloatingPlatform', 'GetCurrentFloatingPlatformKind2', 'GetCurrentFloatingPlatformKind',
    'LoadFloatingPlatformTerrainAttributes', 'GetCurrentFloatingPlatformTileAttributesRelative',
    'GetCurrentFloatingPlatformTileAttributes', 'InitFloatingPlatformJumpPoint', 'FindFloatingPlatformJumpPointAt',
    'InitCameraAngleTemplates', 'FindCameraAngleForPlayerPosition',
    'DoCameraTransition', 'CameraTransitionTask', 'ApplyCameraAngleForPlayerPosition',
    'HandleFloatingPlatformJumpPointAt', 'CreateJumpOnFloatingPlatformTask', 'JumpOnFloatingPlatform',
    'TickJumpOnFloatingPlatformMovementAnimation',
    'DistWorldMapObjectRotator_Init', 'BindMapObjectRotator', 'RotateMapObject', 'TickMapObjectRotator',
    'DistWorld_GetMapObjectRotatorAnimFrame', 'InitFieldTaskContext', 'GetFieldTaskContext',
    'DistWorld_HandlePlayerMoved', 'GetPlayerPos', 'DistWorld_CheckCollisionOnCurrentFloatingPlatform',
    'DistWorld_IsValidTileOnCurrentFloatingPlatform', 'DistWorld_AreCoordsValidOnCurrentFloatingPlatformKind',
    'DistWorld_FindAndPrepareNewCurrentFloatingPlatform', 'DistWorld_GetTileBehaviorOnCurrentFloatingPlatform',
    'GetAvatarDistortionStateForFloatingPlatformKind',
    # the elevators
    'GetConnectionsForMap', 'GetMovingPlatformsTemplatesForMap', 'GetMovingPlatformTemplateForMap',
    'GetMovingPlatformElevatorPath', 'HandleElevatorPlatformPropAnimatorAt', 'FindMovingPlatformPropAnimatorAt',
    'CreateElevatorPlatformHandlerTask', 'CallElevatorPlatformHandler', 'DistWorldElevatorPlatform_BeginMovement',
    'DistWorldElevatorPlatform_Vibrate', 'DistWorldElevatorPlatform_MoveFirstHalf', 'DistWorldElevatorPlatform_ChangeMaps',
    'DistWorldElevatorPlatform_MoveSecondHalf', 'DistWorldElevatorPlatform_EndMovement',
    'DistWorldMovingPlatformPropAnimator_ChangeMaps', 'DistWorldMovingPlatformPropAnimator_SetPreventDeletion',
    'DistWorldMovingPlatformPropAnimator_InitFromTemplate', 'InitMovingPlatformPropsForMap',
    'InitMovingPlatformPropsForMapEx', 'InitSpecificMovingPlatformPropForMap', 'FindUnusedMovingPlatformPropAnimator',
    'GetAnimatorForMovingPlatform', 'SetPersistedMovingPlatformFlag', 'ClearPersistedMovingPlatformFlag',
    'CheckPersistedMovingPlatformFlag', 'SetPersistedMovingPlatformFlags', 'InitPersistedData', 'SetMapObjectPos',
    'DistWorld_HandlePlayerPositionChanged',
]
OV9_TABLES = ['sFloatingPlatformJumpOffsets', 'sFloatingPlatformJumpPointHandlers', 'sDistWorldMapConnectionList',
              'sElevatorPlatformPaths', 'sElevatorPlatformHandlers']
# the struct typedefs the functions use, in their file order
OV9_TYPES = ['DistWorldBounds', 'DistWorldMapInfo', 'DistWorldMapInfoFile', 'DistWorldFloatingPlatformTemplate',
             'DistWorldFloatingPlatformJumpPointTemplate', 'DistWorldCameraAngleTemplate',
             'DistWorldFloatingPlatformManager', 'DistWorldMapFileFloatingPlatformJumpPointSection',
             'DistWorldCameraAngleTemplates', 'DistWorldMapFileHeader', 'DistWorldMapFileFloatingPlatformSection',
             'DistWorldMapFileCameraAngleSection', 'DistWorldMapFile', 'DistWorldCameraTransition',
             'DistWorldCameraManager', 'DistWorldFloatingPlatformJumpTaskContext', 'DistWorldFieldTaskContext',
             'DistWorldMapObjectRotator', 'DistWorldMapObjectRotatorManager', 'DistWorldElevatorPlatformPath',
             'DistWorldMovingPlatformTemplate', 'DistWorldMovingPlatformMapTemplates',
             'DistWorldMovingPlatformPropAnimator', 'DistWorldMovingPlatformPropManager', 'DistWorldMapConnections',
             'DistWorldElevatorPlatform']
OV9_ENUMS = ['FloatingPlatformKind', 'FloatingPlatformJumpTaskState', 'PropKind', 'Axis', 'MovingPlatformElevatorDirection',
             'MovingPlatformMapObjectData', 'ElevatorPlatformState', 'ElevatorPlatformHandlerResult']

PLAYER_MOVE = [
    'PlayerAvatar_CheckStartMoveInternal', 'PlayerAvatar_UpdateMoveState2', 'PlayerAvatar_ValidateState',
    'PlayerAvatar_UpdateMoveState', 'PlayerAvatar_SetMovement_Normal', 'PlayerAvatar_SetMovement_NotMoving',
    'PlayerAvatar_SetMovement_Moving', 'PlayerAvatar_SetMovement_DistortionFloor',
    'PlayerAvatar_UpdateMovement_NormalDistortion', 'PlayerAvatar_SetMovement_DistortionWestWall',
    'PlayerAvatar_SetMovement_DistortionEastWall', 'PlayerAvatar_SetMovement_DistortionCeiling',
    'PlayerAvatar_SetMovement_Turning', 'PlayerAvatar_SetMovement', 'PlayerAvatar_CheckDistortionMapObjectCollision',
    'PlayerAvatar_WillBeOnWaterDistortion', 'PlayerAvatar_CheckDistortionCollision',
    'PlayerAvatar_WillJumpTwiceDistortion', 'PlayerAvatar_GetStepDistortionWorldPos', 'MovementAction_IsWalkOnSpotSlow',
]
PLAYER_MOVE_TABLES = ['sDistortionStepDirectionFloor', 'sDistortionStepDirectionWestWall',
                      'sDistortionStepDirectionEastWall', 'sDistortionStepDirectionCeiling']

ACTIONS = [
    'LocalMapObj_IsAnimationSet', 'LocalMapObj_SetAnimationCode', 'MapObject_DoMovementAction', 'sub_020658DC',
    'MapObject_DoMovementActionStep', 'MovementAction_End', 'MovementAction_InitFace', 'MovementAction_InitWalk',
    'MovementAction_Walk_Step1', 'MovementAction_InitWalkOnSpot', 'MovementAction_WalkOnSpot_Step1',
    'MovementAction_InitJumpCustomSound', 'MovementAction_Jump_Step1', 'sub_02066824', 'sub_020668EC',
]
DIRS = ['North', 'South', 'West', 'East']
for d in DIRS:
    ACTIONS += [f'MovementAction_Face{d}_Step0', f'MovementAction_WalkNormal{d}_Step0', f'MovementAction_WalkFast{d}_Step0',
                f'MovementAction_Run{d}_Step0', f'MovementAction_WalkOnSpotSlow{d}_Step0',
                f'MovementAction_WalkOnSpotFaster{d}_Step0', f'MovementAction_JumpDistortionWorld{d}_Step0']
ACTION_TABLES = ['sJumpHeights_High', 'sJumpHeights_Low', 'sJumpHeights_Normal', 'sJumpHeightsTable']
# the action arrays by Platinum's number; 105-116 and 121-132 name their init function inside
ACTION_ARRAYS = {0: 'FaceNorth', 12: 'WalkNormalNorth', 16: 'WalkFastNorth', 28: 'WalkOnSpotSlowNorth',
                 40: 'WalkOnSpotFasterNorth', 88: 'RunNorth', 117: 'JumpDistortionWorldNorth'}
MAP_OBJECT = ['MapObject_TryFace', 'MapObject_Turn', 'MapObject_TryFaceAndTurn']
MAP_OBJECT_MOVE = ['MapObject_StepDir', 'MapObject_UpdateCoords', 'MapObject_AddVecToPos', 'MapObject_MovePosInDir']
TILE_BEHAVIOR = ['TileBehavior_IsSurfable', 'TileBehavior_IsJumpNorthTwice', 'TileBehavior_IsJumpSouthTwice',
                 'TileBehavior_IsJumpWestTwice', 'TileBehavior_IsJumpEastTwice']


def read(name):
    return open(os.path.join(PLAT, name)).read()


def function(src, name, path):
    m = re.search(r'^(?:static\s+)?[A-Za-z_][\w \*]*?\b' + re.escape(name) + r'\(([^;{]*)\)\s*\n\{', src, re.M)
    assert m, f'{path}: no function {name}'
    end = src.index('\n}\n', m.start()) + 3
    return src[m.start():end]


def table(src, name, path):
    m = re.search(r'^(?:static\s+)?(?:const\s+)?[^\n=;]*\b' + re.escape(name) + r'\b[^\n=;]*=\s*\{', src, re.M)
    assert m, f'{path}: no table {name}'
    end = src.index('\n};\n', m.start()) + 4
    return src[m.start():end]


def typedef(src, name, path):
    m = re.search(r'^typedef struct ' + re.escape(name) + r' \{.*?^\} ' + re.escape(name) + r';\n', src, re.M | re.S)
    assert m, f'{path}: no struct {name}'
    return m.group(0)


def enum(src, name, path):
    m = re.search(r'^enum ' + re.escape(name) + r' \{.*?^\};\n', src, re.M | re.S)
    assert m, f'{path}: no enum {name}'
    return m.group(0)


def main(out):
    parts = ['// Generated by b2tools/platinum_dw_host/extract.py from pokeplatinum\'s sources: don\'t edit.\n',
             '#include "plat_shim.h"\n']
    ov9 = read('overlay009/ov9_02249960.c')
    for e in OV9_ENUMS:
        parts.append(enum(ov9, e, 'ov9'))
    for t in OV9_TYPES:
        parts.append(typedef(ov9, t, 'ov9'))
    parts.append('typedef void (*FloatingPlatformJumpPointHandler)(DistWorldSystem *, const DistWorldFloatingPlatformJumpPointTemplate *);\n')
    parts.append('typedef int (*ElevatorPlatformHandler)(DistWorldSystem *, DistWorldElevatorPlatform *);\n')
    hdr = open(os.path.join(PLAT, '..', 'include', 'overlay009', 'ov9_02249960.h')).read()
    parts.append(enum(hdr, 'DistWorldPersistedMovingPlatformFlag', 'ov9_02249960.h'))
    parts.append(enum(hdr, 'DistWorldPersistedBoulderPuzzleFlag', 'ov9_02249960.h'))
    parts.append('#include "plat_shim_system.h"\n')
    protos = []
    bodies = []
    pm = read('player_move.c')
    parts.append(re.search(r'^typedef struct \{\n    s16 dx;.*?\} DistortionWorldStepDirection;\n', pm, re.M | re.S).group(0))
    for name in PLAYER_MOVE_TABLES:
        bodies.append(table(pm, name, 'player_move.c'))
    for name in PLAYER_MOVE:
        bodies.append(function(pm, name, 'player_move.c'))
    # the moving platforms' templates, each floor's list and the list of lists, in the file's order
    for m in re.finditer(r'^static const DistWorldMovingPlatformTemplate (\*)?(sMovingPlatform\w+)(\[\])? = \{', ov9, re.M):
        bodies.append(table(ov9, m.group(2), 'ov9'))
    bodies.append(table(ov9, 'sMovingPlatformsMapTemplates', 'ov9'))
    for name in OV9_TABLES:
        t = table(ov9, name, 'ov9')
        if name == 'sFloatingPlatformJumpOffsets':
            # TickJumpOnFloatingPlatformMovementAnimation reads index 16 on a jump's last step (jumpOffsetIndex reaches
            # 16 tiles' 16ths) and sets the offset to 0 right after: on the DS it reads the next table's first word. One
            # more element here keeps the Mac's sanitizers quiet; the value is overwritten either way
            t = t.replace('[MAP_OBJECT_TILE_SIZE / FX32_ONE] = {', '[MAP_OBJECT_TILE_SIZE / FX32_ONE + 1] = {', 1)
            assert '+ 1] = {' in t
        bodies.append(t)
    for name in OV9:
        bodies.append(function(ov9, name, 'ov9'))
    act = read('unk_020655F4.c')
    for s in ('typedef struct {\n    int dir;\n    fx32 distance;', ):
        pass
    for name in ('WalkMovementData', 'WalkOnSpotMovementData', 'JumpMovementData', 'UnkStruct_02066824'):
        m = re.search(r'^typedef struct[^{]*\{[^}]*\} ' + name + ';\n', act, re.M | re.S)
        assert m, f'unk_020655F4.c: no struct {name}'
        parts.append(m.group(0))
    for name in ACTION_TABLES:
        bodies.append(table(act, name, 'unk_020655F4.c'))
    for name in ACTIONS:
        bodies.append(function(act, name, 'unk_020655F4.c'))
    # 105-116 and 121-132: their init functions, from their arrays
    vector_inits = []
    for n in list(range(105, 117)) + list(range(121, 133)):
        arr = table(act, f'gMovementActionFuncs_{n}', 'unk_020655F4.c')
        init = re.search(r'\{\s*(\w+),', arr).group(1)
        vector_inits.append(init)
        bodies.append(function(act, init, 'unk_020655F4.c'))
        bodies.append(arr)
    for n, base in ACTION_ARRAYS.items():
        for k, d in enumerate(DIRS):
            bodies.append(table(act, f'gMovementActionFuncs_{base.replace("North", d)}', 'unk_020655F4.c'))
    mo = read('map_object.c')
    for name in MAP_OBJECT:
        bodies.append(function(mo, name, 'map_object.c'))
    mom = read('map_object_move.c')
    for name in MAP_OBJECT_MOVE:
        bodies.append(function(mom, name, 'map_object_move.c'))
    tb = read('map_tile_behavior.c')
    bodies.append(table(tb, 'sTileBehaviorFlags', 'map_tile_behavior.c'))
    for name in TILE_BEHAVIOR:
        bodies.append(function(tb, name, 'map_tile_behavior.c'))
    # prototypes of every static function, so the order doesn't matter
    for b in bodies:
        m = re.match(r'((?:static\s+)?[A-Za-z_][\w \*]*?\b(\w+)\(([^;{]*)\))\s*\n\{', b)
        if m:
            protos.append(m.group(1) + ';\n')
    # the action table: Platinum's number -> its functions
    rows = []
    for n, base in ACTION_ARRAYS.items():
        for k, d in enumerate(DIRS):
            rows.append(f'    [{n + k}] = gMovementActionFuncs_{base.replace("North", d)},\n')
    for n in list(range(105, 117)) + list(range(121, 133)):
        rows.append(f'    [{n}] = gMovementActionFuncs_{n},\n')
    table_src = ('BOOL (*const *const gMovementActionFuncs[MAX_MOVEMENT_ACTION])(MapObject *) = {\n' + ''.join(rows) +
                 '};\n')
    # the array declarations used by the table, before it
    decls = []
    for b in bodies:
        m = re.match(r'(BOOL \(\*const (gMovementActionFuncs_\w+)\[\]\)\(MapObject \*\))', b)
        if m:
            decls.append(m.group(1) + ';\n')
    text = ''.join(parts) + ''.join(protos) + ''.join(decls) + table_src + '\n'.join(bodies)
    open(out, 'w').write(text)
    print(f'{out}: {len(bodies)} pieces of Platinum\'s C')


# (plat-dw-finish) the boulder puzzle: ov9's falls and falling boulder, overlay 5's push test, word for word
BOULDER_OV9 = ['FindBoulderFallLocationFlag', 'DistWorld_WillBoulderBeAtFallLocation', 'FindMapObjectBoulderFallLocationFlag',
               'DistWorld_IsBoulderAtFallLocation', 'DistWorldFallingBoulder_New', 'DistWorldFallingBoulder_TickToB6F',
               'DistWorldFallingBoulder_TickToCorrectPit', 'DistWorldFallingBoulder_TickToWrongPit',
               'DistWorldFallingBoulder_Tick', 'SetPersistedBoulderPuzzleFlag', 'ClearPersistedBoulderPuzzleFlag',
               'CheckPersistedBoulderPuzzleFlag']
BOULDER_MOVE = ['MapObject_GetDxFromDir', 'MapObject_GetDzFromDir', 'MapObject_UpdateCoords', 'MapObject_MovePosInDir']


def boulder(out):
    """plat_boulder_extract.c: the boulder puzzle's C (boulder_shim.c includes it)."""
    ov9 = read('overlay009/ov9_02249960.c')
    hdr = open(os.path.join(PLAT, '..', 'include', 'overlay009', 'ov9_02249960.h')).read()
    parts = ['// Generated by b2tools/platinum_dw_host/extract.py --boulder from pokeplatinum\'s sources: don\'t edit.\n',
             '#include "boulder_shim.h"\n', enum(hdr, 'DistWorldPersistedBoulderPuzzleFlag', 'ov9_02249960.h'),
             re.search(r'^typedef struct DistWorldPersistedData \{.*?^\} DistWorldPersistedData;\n', hdr, re.M | re.S).group(0),
             re.search(r'^typedef struct DistWorldFallingBoulder \{.*?^\} DistWorldFallingBoulder;\n', hdr, re.M | re.S).group(0),
             enum(ov9, 'FallingBoulderDestination', 'ov9'), typedef(ov9, 'DistWorldBoulderFallLocation', 'ov9'),
             '#include "boulder_shim_system.h"\n']
    bodies = [table(ov9, 'sBoulderFallLocations', 'ov9')]
    bodies += [function(ov9, n, 'ov9') for n in BOULDER_OV9]
    mom = read('map_object_move.c')
    bodies += [table(mom, 'sMapObjectDxDir', 'map_object_move.c'), table(mom, 'sMapObjectDzDir', 'map_object_move.c')]
    bodies += [function(mom, n, 'map_object_move.c') for n in BOULDER_MOVE]
    bodies.append(function(read('map_object.c'), 'MapObject_SetPosDirFromVec', 'map_object.c'))
    bodies.append(function(read('overlay005/ov5_021DFB54.c'), 'ov5_021DFF1C', 'ov5_021DFB54.c'))
    protos = []
    for b in bodies:
        m = re.match(r'((?:static\s+)?[A-Za-z_][\w \*]*?\b(\w+)\(([^;{]*)\))\s*\n\{', b)
        if m:
            protos.append(m.group(1) + ';\n')
    open(out, 'w').write(''.join(parts) + ''.join(protos) + '\n'.join(bodies))
    print(f'{out}: {len(bodies)} pieces of Platinum\'s C')


if __name__ == '__main__':
    if sys.argv[1] == '--boulder':
        boulder(sys.argv[2])
    else:
        main(sys.argv[1])
