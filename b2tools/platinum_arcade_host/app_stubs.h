// The board's own drawing functions (applications/frontier/battle_arcade/main.c), for the harness: they draw nothing and load
// nothing. Included by the copied board (extract.py), after its own declarations; its states, its random numbers, its cursor and its
// stop are Platinum's own text.
static void FreeAssets(BattleArcadeApp *app) { (void)app; }
static void InitGraphicsPlane(void) {}
static void LoadAssets(BattleArcadeApp *app) { (void)app; }
static void InitSpriteManager(BattleArcadeApp *app) { (void)app; }
static void LoadBackgrounds(BattleArcadeApp *app) { (void)app; }
static void FreeBackgrounds(BgConfig *bgConfig) { (void)bgConfig; }
static void VBlankCallback(void *data) { (void)data; }
static void InitGXBanks(void) {}
static void InitBackgrounds(BgConfig *bgConfig) { (void)bgConfig; }
static void LoadInitialBackround(BattleArcadeApp *app, enum BgLayer bgLayer) { (void)app, (void)bgLayer; }
static void LoadRouletteBackground(BattleArcadeApp *app, enum BgLayer bgLayer) { (void)app, (void)bgLayer; }
static void LoadPalette(void) {}
static void LoadSubScreenBackground(BattleArcadeApp *app, enum BgLayer bgLayer) { (void)app, (void)bgLayer; }
static void UpdateItemSprites(BattleArcadeApp *app) { (void)app; }
