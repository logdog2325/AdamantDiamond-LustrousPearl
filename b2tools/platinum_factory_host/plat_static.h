// The Factory harness: the static functions of Platinum's copied C, declared before their use (plat_factory.c only)
static int BattleFactory_GetOpponentTrainerID(u8 challengeType, int currentRound, int trainerOffset);
static const BattleFactoryPokemonPool *GetPlayerPoolForRound(int round, int isOpenLevel);
static u16 BattleFactory_GetAIMask(BattleFactory *battleFactory);
static void SetupTrainersAndInitialRentalOptions(BattleFactory *factory);
static void LoadTrainersAndMonsFromSave(BattleFactory *factory);
static u16 GetBattleFactoryAppSelectedIndices(BattleFactoryAppArgs *args, u8 i);
static void SwapMonIndices(BattleFactory *factory, u8 idx1, u8 isPartners);
static inline BOOL Pokemon_InlineIsPersonalityShiny(u32 monOTID, u32 monPersonality);
