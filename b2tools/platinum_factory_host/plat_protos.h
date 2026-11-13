// The Factory harness: what Platinum's copied C calls before it defines it, and the calls that need its structs
// (extract.py includes this after them). The bodies are sim.c's, or Platinum's own further down the copied file.
#ifndef FACTORY_HOST_PLAT_PROTOS_H
#define FACTORY_HOST_PLAT_PROTOS_H
#define BattleFrontierSave_GetStatAutoHostIdx(frontierSave, statIndex) \
    BattleFrontierSave_GetStat(frontierSave, statIndex, BattleFrontierStats_GetHostFriendIdx(statIndex))
#define BattleFrontierSave_SetStatAutoHostIdx(frontierSave, statIndex, newValue) \
    BattleFrontierSave_SetStat(frontierSave, statIndex, BattleFrontierStats_GetHostFriendIdx(statIndex), newValue)
#define BattleFrontierSave_SetIfBetterAutoHostIdx(frontierSave, statIndex, newValue) \
    BattleFrontierSave_SetIfBetter(frontierSave, statIndex, BattleFrontierStats_GetHostFriendIdx(statIndex), newValue)
int BattleFrontierStats_GetHostFriendIdx(u32 statIndex);
BattleFrontierSave *SaveData_GetBattleFrontier(SaveData *saveData);
BattleFactorySave *BattleFactorySave_Get(SaveData *saveData);
BattleFactoryStreakFlags *BattleFactoryStreakFlags_Get(SaveData *saveData);
void FrontierPokemon_InitPokemon(const FrontierPokemon *frontierMon, Pokemon *mon, u8 setLevel);
void BattleFactory_AddRentalPokemonToParty(SaveData *saveData, Party *party, Pokemon *mon);
u16 BattleFactory_GetNextOpponentObjectID(BattleFactory *factory, u8 trainerSlot);
void BattleFrontier_LoadTrainer(FrontierOpponent *opponent, u16 trainerID, enum HeapID heapID, enum NarcID narcID);
void BattleFactory_UpdatePartnersParty(BattleFactory *factory);
void UpdateCorridorFloorBG(SysTask *task, void *data);
BattleFactory *BattleFactory_Init(SaveData *saveData, u16 resumingFromSave, u8 challengeType, u8 isOpenLevel);
void BattleFactory_LoadTrainersAndRentalsForRound(BattleFactory *factory, u16 resumingFromSave);
void BattleFactory_PickOpponentTrainers(u8 challengeType, int currentRound, u16 trainerIDs[], u8 numTrainers);
const BattleFactoryPokemonPool *BattleFactory_GetPokemonPoolForTrainer(int trainerID, BOOL isOpenLevel);
BOOL BattleFactory_SelectPokemonFromPool(const u16 excludedSpecies[], const u16 excludedItems[], int numExcluded, int numMons,
                                         u16 monSetIDs[], int unused, const BattleFactoryPokemonPool *pool, u16 tradeCount,
                                         u8 ivList[]);
u8 BattleFactory_GetPlayerPartySize(u8 challengeType);
u8 BattleFactory_GetOpponentPartySize(u8 challengeType, BOOL includePartnersMons);
void BattleFactory_SelectInitialRentalOptions(u16 round, u8 isOpenLevel, u16 *monSetIDs, FrontierPokemon *mons, u8 *ivs,
                                              u32 *personalities, u16 tradeCount, u16 *excludedSpecies, u16 *unused);
void BattleFactory_SelectInitialOpponentMons(u8 numMons, u16 trainerID, u8 isOpenLevel, FrontierPokemon *excludedMons,
                                             u16 *monSetIDs, FrontierPokemon *mons, u8 *ivList, u32 *personalities,
                                             int numExcluded);
u8 BattleFactory_GetPokemonLevel(BattleFactory *battleFactory);
BOOL BattleFactory_IsMultiplayerChallenge(u8 challengeType);
u16 BattleFactory_GetCurrentRound(BattleFactory *battleFactory);
void BattleFactory_Save(BattleFactory *factory, u8 saveType);
u16 BattleFactory_IncrementCurrentBattle(BattleFactory *factory);
void BattleFactory_SaveOnLoss(BattleFactory *factory);
void BattleFactory_SaveOnCompletingRound(BattleFactory *factory);
void BattleFactory_IncrementTradeCount(BattleFactory *factory);
u16 BattleFactory_GetEarnedBP(BattleFactory *factory);
void BattleFactory_GetMonSelectionAppResult(BattleFactory *battleFactory, BattleFactoryAppArgs *args);
void BattleFactory_AddSelectedRentalsToParty(BattleFactory *factory);
void BattleFactory_SetupNextOpponent(BattleFactory *factory);
void BattleFactory_ApplyTrade(BattleFactory *factory);
void BattleFactory_SetupNextOpponentsParty(BattleFactory *factory);
void BattleFactory_CreateInitialRentalParty(BattleFactory *battleFactory);
void BattleFactorySave_Init(BattleFactorySave *save);
BOOL BattleFactorySave_HasSaved(BattleFactorySave *save);
void BattleFactorySave_RecordSave(BattleFactorySave *save, BOOL didSave);
void BattleFactorySave_SetMember(BattleFactorySave *save, u8 field, u8 index, const void *value);
u32 BattleFactorySave_GetMember(BattleFactorySave *save, u8 field, u8 index, void *unused);
void BattleFactoryStreakFlags_SetFlag(BattleFactoryStreakFlags *flags, u8 field, u8 challengeType, u8 *value);
u32 BattleFactoryStreakFlags_GetFlag(BattleFactoryStreakFlags *flags, u8 field, u8 challengeType, void *unused);
enum BattleFrontierStatsIndex BattleFrontierStats_GetFactoryLatestStreakIdx(u8 isOpenLevel, u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetFactoryRecordStreakIdx(u8 isOpenLevel, u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetFactoryLatestTradeCountIndex(u8 isOpenLevel, u8 challengeType);
enum BattleFrontierStatsIndex BattleFrontierStats_GetFactoryRecordTradeCountIndex(u8 isOpenLevel, u8 challengeType);
u16 BattleFrontierSave_GetStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID);
u16 BattleFrontierSave_SetStat(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID,
                               u16 newValue);
u16 BattleFrontierSave_SetIfBetter(BattleFrontierSave *frontier, enum BattleFrontierStatsIndex statIndex, int hostFriendID,
                                   u16 newValue);
u8 Pokemon_GetNatureOf(u32 monPersonality);
u8 Pokemon_IsPersonalityShiny(u32 monOTID, u32 monPersonality);
BOOL FrontierScrCmd_CallBattleFactoryFunction(FrontierScriptContext *ctx);
BOOL ScrCmd_DeleteActiveBattleFactoryStreak(ScriptContext *ctx);
u16 Plat_GetAIMask(BattleFactory *factory);
#endif
