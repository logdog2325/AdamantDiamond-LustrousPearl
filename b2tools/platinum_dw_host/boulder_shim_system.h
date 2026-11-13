// (plat-dw-finish) ov9's system as far as the boulder puzzle uses it: the persisted data, and its map object deletion
#ifndef BOULDER_SHIM_SYSTEM_H
#define BOULDER_SHIM_SYSTEM_H
struct DistWorldSystem {
    FieldSystem *fieldSystem;
    DistWorldPersistedData *persistedData;
};
void DeleteMapObject(DistWorldSystem *system, MapObject *mapObj);
#endif
