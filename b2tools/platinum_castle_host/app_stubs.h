// The Castle's two screens' own drawing functions, for the harness: they draw nothing. What a screen prints is logged (gMsgLog: the
// line of its text bank; gTemplateNumber0: the number in string template slot 0, the cost a question names), so the harness
// compares the messages Platinum's screen shows with the ones our rules' answers stand for. Included by the copied screens
// (extract.py), after their own declarations; the state machine and the purchases are Platinum's own text.
#ifdef APP_STUBS_SELF
typedef BattleCastleSelfApp APP_T;
#else
typedef BattleCastleOpponentApp APP_T;
#endif

static u8 PrintMessageAndCopyToVRAM(APP_T *app, int entryID, u8 font) {
    (void)app;
    (void)font;
    if (gMsgCount < 16) {
        gMsgLog[gMsgCount++] = entryID;
    }
    return 0;
}

static void SetStringTemplateNumber(APP_T *app, u32 idx, s32 num, u32 maxDigits, enum PaddingMode paddingMode) {
    (void)app;
    (void)maxDigits;
    (void)paddingMode;
    if (idx == 0) {
        gTemplateNumber0 = num;
    }
}

static u8 PrintLeftAlignedMessageWithBg(APP_T *app, Window *window, int entryID, u32 xOffset, u32 yOffset, u32 renderDelay,
                                        u8 fgColor, u8 shadowColor, u8 bgColor, u8 font) {
    (void)app, (void)window, (void)entryID, (void)xOffset, (void)yOffset, (void)renderDelay, (void)fgColor, (void)shadowColor,
        (void)bgColor, (void)font;
    return 0;
}

static void SetStringTemplateSpecies(APP_T *app, u32 idx, BoxPokemon *boxMon) { (void)app, (void)idx, (void)boxMon; }
static void SetStringTemplatePlayerName(APP_T *app, u32 idx) { (void)app, (void)idx; }
static void PrintMonSelectionStrings(APP_T *app) { (void)app; }
static void CloseMonSelectionMessageBox(APP_T *app) { (void)app; }
static void OpenMonOptionsMenu(APP_T *app) { (void)app; }
static void UpdateSelectedMon(APP_T *app, int unused) { (void)app, (void)unused; }
static void UpdateCursorPosition(APP_T *app) { (void)app; }
static void CloseMessageBox(Window *window) { (void)window; }
static void FreeListMenu2(APP_T *app) { (void)app; }
static void OpenYesNoMenu(APP_T *app) { (void)app; }
static void PrintPlayersAndPartnersCastlePoints(APP_T *app, Window *window) { (void)app, (void)window; }
static BOOL UpdateAfterPurchase(APP_T *app, u8 selectedSlot, u8 menuOption) {
    (void)app, (void)selectedSlot, (void)menuOption;
    return TRUE;
}
static void ShowMonSummary(APP_T *app, u8 slot) { (void)app, (void)slot; }
static void ShowMovesList(APP_T *app, u8 slot) { (void)app, (void)slot; }
static void ChangeSelectedMonOnSummaryDisplay(APP_T *app, s8 step) { (void)app, (void)step; }
static void ChangeSelectedMonOnMoveDisplay(APP_T *app, s8 step) { (void)app, (void)step; }
static void CloseSummaryScreen(APP_T *app) { (void)app; }

#ifdef APP_STUBS_SELF
static void OpenHealMenu(APP_T *app) { (void)app; }
static void OpenRentalMenu(APP_T *app) { (void)app; }
static void CloseMonOptions(APP_T *app) { (void)app; }
static void CloseYesNoMenu(APP_T *app) { (void)app; }
static void FreeListMenu3(APP_T *app) { (void)app; }
static void OpenItemSelectScreen(APP_T *app, u8 menuOption) { (void)app, (void)menuOption; }
static void FreeItemSelect(APP_T *app) { (void)app; }
static void RefreshItemSelectMenu(APP_T *app) { (void)app; }
#else
static void OpenSummaryMenu(APP_T *app) { (void)app; }
static void OpenLevelMenu(APP_T *app) { (void)app; }
static void CloseListMenu(APP_T *app) { (void)app; }
static void DrawMessageBox(APP_T *app) { (void)app; }
static void FreeSimpleMenu(APP_T *app) { (void)app; }
static void PrintAllMonsHP(APP_T *app, Window *window) { (void)app, (void)window; }
static void PrintAllMonsLevelAndGender(APP_T *app, Window *window) { (void)app, (void)window; }
static void UpdateAllFlagSprites(APP_T *app) { (void)app; }
#endif
