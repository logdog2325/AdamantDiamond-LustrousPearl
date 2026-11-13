// ---- plat-castle (2026-11-07): Platinum's Battle Castle's two screens as field script (notes/PLATINUM_FRONTIER.md "The Battle
// Castle"; decomp include/pearlb2/plat_castle.h). Platinum's OpenBattleCastleSelfApp and OpenBattleCastleOpponentApp are screens of
// their own (applications/frontier/battle_castle/self_app.c, opponent_app.c); Black 2 has none like them. Here:
// - the self screen's Pokémon: Black 2's battle-entry party screen on the castle's three (HP bars, status, held items, its
//   summary pages), one to pick or B to leave (pl_CastleSelfScreen, pl_CastleSelfPick);
// - the opponent screen's Pokémon: a list menu of the opponent's three, a line of the zone's for one not identified yet
//   (pl_CastleOpponentList);
// - every menu after that: Black 2's list menus with Platinum's own entries and descriptions, Platinum's lines, its yes/no; each
//   purchase asked and made by pl_CastleAsk and pl_CastleBuy, which answer as Platinum's screens' state machines do (castle_rules.c:
//   b2tools/platinum_castle_host runs those state machines themselves beside them). Each answer shows the line Platinum's screen
//   shows for it, and goes back where Platinum's goes.
// Not kept: the screens' pictures (the castle's emblem, the Pokémon's sprites and HP bars drawn by the screen itself, the CP header,
// the grey of an entry the rank doesn't allow yet: the rank's message says so when it's picked); the summary and moves panels are
// one line each (the zone's lines CASTLE_LINES + 1 and + 2, made of Platinum's own labels).
//
// The script that uses these sets (assembler symbols: `.set CASTLE_SELF, n`), before `pl_CastleScreensCode`, the first line of
// each bank in its zone's text:
//   CASTLE_SELF   Platinum's battle_castle_self_app bank (93 lines)
//   CASTLE_OPP    Platinum's battle_castle_opponent_app bank (81 lines)
//   CASTLE_LINES  the Castle's own lines: + 0 an opponent not identified ("?????", the row of a ball), + 1 the summary panel
//                 (words 0 item, 1 nature, 2 ability, 3-7 Attack, Defense, Sp. Atk, Sp. Def, Speed), + 2 the moves panel
//                 (words 0-3 the moves, 4-7 their PP, 8-11 their maximum)
// and calls them with VMCall where Platinum's scene has OpenBattleCastleSelfApp and OpenBattleCastleOpponentApp. They use works
// 0x805F-0x8061 (no Frontier scene uses them) and the library's PL_TMP, PL_TMP2, PL_TMP3.
#define CS_SLOT 0x805F                  // the Pokémon (0-2)
#define CS_RESULT 0x8060                // pl_CastleAsk's and pl_CastleBuy's answer
#define CS_CHOICE 0x8061                // the menu's choice: a purchase (PLATCASTLE_BUY_*), or 0xFFFE (B, CANCEL)
#define CS_ROW PL_TMP3                  // the rental list's row
#define CS_RANK PL_TMP2                 // a rank before its rank-up (the rank-up's line names the new power)
#define CS_YESNO PL_TMP                 // the yes/no: 0 YES, 1 NO
#define CS_CANCEL 0xFFFE                // Black 2's list menu answers B so; CANCEL rows give it too
// PLATCASTLE_BUY_* and PLATCASTLE_RESULT_* (plat_castle.h)
#define CB_HEAL_HP 0
#define CB_RANK_HEALING 3
#define CB_BERRY 4
#define CB_ITEM 5
#define CB_RANK_RENTALS 6
#define CB_IDENTIFY 7
#define CB_LEVEL_UP 8
#define CB_LEVEL_DOWN 9
#define CB_STATS 10
#define CB_MOVES 11
#define CB_RANK_INFO 12
#define CB_PASS 13
#define CB_SWITCH 0x100
#define CR_DONE 0
#define CR_CONFIRM 1
#define CR_NOT_ENOUGH_CP 2
#define CR_RANK_TOO_LOW 3
#define CR_NO_BENEFIT 4
#define CR_HOLDING_ITEM 5
#define CR_MAX_RANK 6
#define CR_KNOWN 7
#define CR_CANT_GO_HIGHER 8
#define CR_CANT_GO_LOWER 9

    // a line, then A or B, then the window closed (Platinum's WAIT_* states)
    .macro pl_CastleSay line
    pl_msg_sys \line
    pl_WaitABPress
    pl_CloseMessage
    .endm
    // a question and Black 2's yes/no (CS_YESNO: 0 YES)
    .macro pl_CastleAskYesNo line
    pl_msg_sys \line
    pl_ShowYesNoMenu CS_YESNO
    pl_CloseMessage
    .endm
    .macro pl_CastleIf var, value, label
    WorkCmpConst \var, \value
    VMJumpIf CMP_EQ, \label
    .endm

    .macro pl_CastleScreensCode
// ------------------------------------------------------------------ the self screen (self_app.c)
CastleSelfScreen:
.Lcs_pick:
    pl_CastleSelfScreen                                 // SELECT_MON: the castle's three on Black 2's party screen
    pl_CastleSelfPick CS_SLOT
    pl_CastleIf CS_SLOT, 0xFF, .Lcs_exit                // B: the screen's EXIT
.Lcs_mon:                                               // MON_OPTIONS_MENU (sMonMenuEntries)
    ListMenu_AnchorTopRight 31, 11, 0, 0, CS_CHOICE
    ListMenuAdd CASTLE_SELF + 9, CASTLE_SELF + 14, 0        // HEAL: Restore HP and/or PP.
    ListMenuAdd CASTLE_SELF + 10, CASTLE_SELF + 15, 1       // RENTAL: You may rent a Berry or an item.
    ListMenuAdd CASTLE_SELF + 11, CASTLE_SELF + 16, 2       // SUMMARY: Check stats, including ability and nature.
    ListMenuAdd CASTLE_SELF + 12, CASTLE_SELF + 17, 3       // MOVES: Check moves and their PP.
    ListMenuAdd CASTLE_SELF + 13, CASTLE_SELF + 18, CS_CANCEL
    ListMenuShow
    pl_CastleIf CS_CHOICE, 0, .Lcs_heal
    pl_CastleIf CS_CHOICE, 1, .Lcs_rental
    pl_CastleIf CS_CHOICE, 2, .Lcs_summary
    pl_CastleIf CS_CHOICE, 3, .Lcs_moves
    VMJump .Lcs_pick
.Lcs_summary:                                           // SHOW_SUMMARY_DISPLAY
    pl_CastleMonWords 0, CS_SLOT, 1
    pl_CastleSay CASTLE_LINES + 1
    VMJump .Lcs_mon
.Lcs_moves:                                             // SHOW_MOVE_DISPLAY
    pl_CastleMonWords 0, CS_SLOT, 2
    pl_CastleSay CASTLE_LINES + 2
    VMJump .Lcs_mon
// the heal menu (HEAL_MENU: sHealMenuEntries; the rank up's description by the healing rank)
.Lcs_heal:
    pl_CastleInfo 0, 0, CS_RANK
    ListMenu_AnchorTopRight 31, 9, 0, 0, CS_CHOICE
    ListMenuAdd CASTLE_SELF + 19, CASTLE_SELF + 24, 0       // RESTORE HP: Which would you like to use?
    ListMenuAdd CASTLE_SELF + 20, CASTLE_SELF + 24, 1       // RESTORE PP
    ListMenuAdd CASTLE_SELF + 21, CASTLE_SELF + 24, 2       // RESTORE ALL
    pl_CastleIf CS_RANK, 3, .Lcs_heal_top
    pl_CastleIf CS_RANK, 1, .Lcs_heal_r1
    ListMenuAdd CASTLE_SELF + 22, CASTLE_SELF + 26, CB_RANK_HEALING   // RANK UP: ... both HP and PP by going up in rank.
    VMJump .Lcs_heal_show
.Lcs_heal_r1:
    ListMenuAdd CASTLE_SELF + 22, CASTLE_SELF + 25, CB_RANK_HEALING   // ... restore PP by going up in rank.
    VMJump .Lcs_heal_show
.Lcs_heal_top:
    ListMenuAdd CASTLE_SELF + 22, CASTLE_SELF + 27, CB_RANK_HEALING   // Your rank cannot be raised any higher.
.Lcs_heal_show:
    ListMenuAdd CASTLE_SELF + 23, CASTLE_SELF + 28, CS_CANCEL         // CANCEL: Return to previous selections.
    ListMenuShow
    pl_CastleIf CS_CHOICE, CS_CANCEL, .Lcs_mon
    pl_CastleAsk CS_CHOICE, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_MAX_RANK, .Lcs_heal_beep
    pl_CastleIf CS_RESULT, CR_RANK_TOO_LOW, .Lcs_heal_low
    pl_CastleIf CS_CHOICE, CB_RANK_HEALING, .Lcs_heal_rank
    pl_CastleAskYesNo CASTLE_SELF + 55                  // HEAL_YES_NO: It will cost N CP. Is that OK?
    pl_CastleIf CS_YESNO, 1, .Lcs_heal
    pl_CastleBuy CS_CHOICE, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_RANK_TOO_LOW, .Lcs_heal_low
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lcs_heal_cp
    pl_CastleIf CS_RESULT, CR_NO_BENEFIT, .Lcs_heal_nothing
    SEPlay SEQ_SE_RECOVERY                              // HealPokemon: X's HP / PP / HP and PP will be restored.
    pl_CastleIf CS_CHOICE, 1, .Lcs_heal_pp
    pl_CastleIf CS_CHOICE, 2, .Lcs_heal_all
    pl_CastleSay CASTLE_SELF + 34
    VMJump .Lcs_pick                                    // WAIT_RETURN_TO_MON_SELECTION
.Lcs_heal_pp:
    pl_CastleSay CASTLE_SELF + 35
    VMJump .Lcs_pick
.Lcs_heal_all:
    pl_CastleSay CASTLE_SELF + 36
    VMJump .Lcs_pick
.Lcs_heal_beep:                                         // the rank at the top: Platinum buzzes
    SEPlay SEQ_SE_BEEP
    VMJump .Lcs_heal
.Lcs_heal_low:                                          // WAIT_AFTER_HEAL_FAILURE
    pl_CastleSay CASTLE_SELF + 33                       // You are too low in healing rank to use this menu item.
    VMJump .Lcs_heal
.Lcs_heal_cp:
    pl_CastleSay CASTLE_SELF + 32                       // You don't have enough CP.
    VMJump .Lcs_heal
.Lcs_heal_nothing:
    pl_CastleSay CASTLE_SELF + 37                       // There is no benefit to using that command.
    VMJump .Lcs_heal
.Lcs_heal_rank:                                         // RANK_UP_HEALING_YES_NO
    pl_CastleAskYesNo CASTLE_SELF + 38                  // Would you like to up your rank for N CP?
    pl_CastleIf CS_YESNO, 1, .Lcs_heal
    pl_CastleBuy CB_RANK_HEALING, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lcs_heal_cp2
    pl_CastleIf CS_RANK, 2, .Lcs_heal_rank2
    pl_CastleSay CASTLE_SELF + 42                       // PLAYER gained the ability to restore PP!
    VMJump .Lcs_heal
.Lcs_heal_rank2:
    pl_CastleSay CASTLE_SELF + 43                       // PLAYER gained the ability to restore both HP and PP!
    VMJump .Lcs_heal
.Lcs_heal_cp2:
    pl_CastleSay CASTLE_SELF + 41
    VMJump .Lcs_heal
// the rental menu (RENTAL_MENU: sRentalMenuEntries; the rank up's description by the rental rank)
.Lcs_rental:
    pl_CastleInfo 1, 0, CS_RANK
    ListMenu_AnchorTopRight 31, 11, 0, 0, CS_CHOICE
    ListMenuAdd CASTLE_SELF + 44, CASTLE_SELF + 48, CB_BERRY      // BERRIES: You may rent a Berry for this Pokémon.
    ListMenuAdd CASTLE_SELF + 45, CASTLE_SELF + 49, CB_ITEM       // ITEMS: You may rent an item for this Pokémon.
    pl_CastleIf CS_RANK, 3, .Lcs_rent_top
    pl_CastleIf CS_RANK, 1, .Lcs_rent_r1
    ListMenuAdd CASTLE_SELF + 46, CASTLE_SELF + 51, CB_RANK_RENTALS   // RANK UP: ... choices ... will be expanded ...
    VMJump .Lcs_rent_show
.Lcs_rent_r1:
    ListMenuAdd CASTLE_SELF + 46, CASTLE_SELF + 50, CB_RANK_RENTALS   // ... rent an item ... by going up in rank.
    VMJump .Lcs_rent_show
.Lcs_rent_top:
    ListMenuAdd CASTLE_SELF + 46, CASTLE_SELF + 52, CB_RANK_RENTALS   // Your rank cannot be raised any higher.
.Lcs_rent_show:
    ListMenuAdd CASTLE_SELF + 47, CASTLE_SELF + 53, CS_CANCEL
    ListMenuShow
    pl_CastleIf CS_CHOICE, CS_CANCEL, .Lcs_mon
    pl_CastleIf CS_CHOICE, CB_RANK_RENTALS, .Lcs_rent_rank
    pl_CastleAsk CS_CHOICE, CS_SLOT, 0xFFFF, CS_RESULT  // the BERRIES or ITEMS entry itself
    pl_CastleIf CS_RESULT, CR_RANK_TOO_LOW, .Lcs_rent_low
.Lcs_rent_list:                                         // SELECT_ITEM_OR_BERRY: the rows the rank allows, their CP
    ListMenu_AnchorTopRight 31, 1, 0, 0, CS_ROW
    WorkCmpConst CS_CHOICE, CB_ITEM
    VMJumpIf CMP_EQ, .Lcs_rent_items
    pl_CastleRentalList 0
    VMJump .Lcs_rent_list_end
.Lcs_rent_items:
    pl_CastleRentalList 1
.Lcs_rent_list_end:
    ListMenuAdd CASTLE_SELF + 13, 65535, CS_CANCEL
    ListMenuShow
    pl_CastleIf CS_ROW, CS_CANCEL, .Lcs_rental
    pl_CastleAsk CS_CHOICE, CS_SLOT, CS_ROW, CS_RESULT
    pl_CastleAskYesNo CASTLE_SELF + 55                  // It will cost N CP. Is that OK?
    pl_CastleIf CS_YESNO, 1, .Lcs_rent_list
    pl_CastleBuy CS_CHOICE, CS_SLOT, CS_ROW, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lcs_rent_cp
    pl_CastleIf CS_RESULT, CR_HOLDING_ITEM, .Lcs_rent_switch
.Lcs_rent_done:
    SEPlay SEQ_SE_DECIDE2                               // RentItem: X was given the ITEM to hold.
    pl_CastleSay CASTLE_SELF + 59
    VMJump .Lcs_pick
.Lcs_rent_switch:                                       // SWITCH_ITEMS_PROMPT, SWITCH_ITEMS_YES_NO
    pl_CastleSay CASTLE_SELF + 60                       // X is already holding ITEM.
    pl_CastleAskYesNo CASTLE_SELF + 61                  // Would you like to switch the two items?
    pl_CastleIf CS_YESNO, 1, .Lcs_rent_list
    WorkAdd CS_ROW, CB_SWITCH
    pl_CastleBuy CS_CHOICE, CS_SLOT, CS_ROW, CS_RESULT
    VMJump .Lcs_rent_done
.Lcs_rent_cp:                                           // WAIT_AFTER_RENTAL_FAILURE
    pl_CastleSay CASTLE_SELF + 32
    VMJump .Lcs_rent_list
.Lcs_rent_low:                                          // WAIT_AFTER_CANT_OPEN_ITEM_SELECT
    pl_CastleSay CASTLE_SELF + 54                       // You are too low in rental rank to use CP.
    VMJump .Lcs_rental
.Lcs_rent_rank:
    pl_CastleAsk CB_RANK_RENTALS, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_MAX_RANK, .Lcs_rent_beep
    pl_CastleAskYesNo CASTLE_SELF + 38                  // RANK_UP_RENTALS_YES_NO
    pl_CastleIf CS_YESNO, 1, .Lcs_rental
    pl_CastleBuy CB_RANK_RENTALS, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lcs_rent_cp2
    pl_CastleIf CS_RANK, 2, .Lcs_rent_rank2
    pl_CastleSay CASTLE_SELF + 68                       // PLAYER gained the ability to rent items!
    VMJump .Lcs_rental
.Lcs_rent_rank2:
    pl_CastleSay CASTLE_SELF + 69                       // PLAYER expanded the variety of rentable Berries and items!
    VMJump .Lcs_rental
.Lcs_rent_cp2:
    pl_CastleSay CASTLE_SELF + 41
    VMJump .Lcs_rental
.Lcs_rent_beep:
    SEPlay SEQ_SE_BEEP
    VMJump .Lcs_rental
.Lcs_exit:
    VMReturn

// ------------------------------------------------------------------ the opponent screen (opponent_app.c)
CastleOpponentScreen:
.Lco_pick:                                              // SELECT_MON
    pl_msg_sys CASTLE_OPP + 4                           // Which Pokémon would you like to check?
    ListMenu_AnchorTopRight 31, 1, 0, 0, CS_SLOT
    pl_CastleOpponentList CASTLE_LINES + 0
    ListMenuAdd CASTLE_OPP + 5, 65535, CS_CANCEL        // EXIT
    ListMenuShow
    pl_CloseMessage
    pl_CastleIf CS_SLOT, CS_CANCEL, .Lco_exit
.Lco_mon:                                               // MON_OPTIONS_MENU (sMonMenuEntries, sMonMenuDescriptions)
    ListMenu_AnchorTopRight 31, 11, 0, 0, CS_CHOICE
    ListMenuAdd CASTLE_OPP + 8, CASTLE_OPP + 12, CB_IDENTIFY      // CHECK: Check the identity of a Pokémon.
    ListMenuAdd CASTLE_OPP + 9, CASTLE_OPP + 13, CB_LEVEL_UP      // LEVEL: Change the level of a Pokémon.
    ListMenuAdd CASTLE_OPP + 10, CASTLE_OPP + 14, CB_STATS        // SUMMARY: Examine the stats of a Pokémon.
    ListMenuAdd CASTLE_OPP + 11, CASTLE_OPP + 15, CS_CANCEL       // CANCEL
    ListMenuShow
    pl_CastleIf CS_CHOICE, CB_IDENTIFY, .Lco_identify
    pl_CastleIf CS_CHOICE, CB_LEVEL_UP, .Lco_level
    pl_CastleIf CS_CHOICE, CB_STATS, .Lco_summary
    VMJump .Lco_pick
.Lco_identify:
    pl_CastleAsk CB_IDENTIFY, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_KNOWN, .Lco_identity
    pl_CastleAskYesNo CASTLE_OPP + 16                   // REVEAL_MON_SLOT_YES_NO: identify this Pokémon? It will cost N CP.
    pl_CastleIf CS_YESNO, 1, .Lco_mon
    pl_CastleBuy CB_IDENTIFY, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lco_cp3
    SEPlay SEQ_SE_DECIDE2
.Lco_identity:
    pl_CastleSay CASTLE_OPP + 20                        // The Pokémon's identity is X.
    VMJump .Lco_pick
.Lco_cp3:
    pl_CastleSay CASTLE_OPP + 28                        // You don't have enough CP...
    VMJump .Lco_pick
.Lco_level:                                             // CHANGE_LEVEL_MENU
    pl_msg_sys CASTLE_OPP + 21                          // You may change this Pokémon's level. What would you like to do?
    ListMenu_AnchorTopRight 31, 11, 0, 0, CS_CHOICE
    ListMenuAdd CASTLE_OPP + 22, 65535, CB_LEVEL_UP     // LEVEL +5
    ListMenuAdd CASTLE_OPP + 23, 65535, CB_LEVEL_DOWN   // LEVEL -5
    ListMenuAdd CASTLE_OPP + 24, 65535, CS_CANCEL
    ListMenuShow
    pl_CloseMessage
    pl_CastleIf CS_CHOICE, CS_CANCEL, .Lco_mon
    pl_CastleAsk CS_CHOICE, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_CANT_GO_HIGHER, .Lco_higher
    pl_CastleIf CS_RESULT, CR_CANT_GO_LOWER, .Lco_lower
    pl_CastleAskYesNo CASTLE_OPP + 25                   // CHANGE_LEVEL_YES_NO: It will cost N CP. Is that OK?
    pl_CastleIf CS_YESNO, 1, .Lco_mon
    pl_CastleBuy CS_CHOICE, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lco_cp3
    pl_CastleIf CS_CHOICE, CB_LEVEL_DOWN, .Lco_lowered
    pl_CastleSay CASTLE_OPP + 31                        // The Pokémon's level was boosted by five.
    VMJump .Lco_pick
.Lco_lowered:
    pl_CastleSay CASTLE_OPP + 32                        // The Pokémon's level was lowered by five.
    VMJump .Lco_pick
.Lco_higher:
    pl_CastleSay CASTLE_OPP + 29
    VMJump .Lco_pick
.Lco_lower:
    pl_CastleSay CASTLE_OPP + 30
    VMJump .Lco_pick
.Lco_summary:                                           // SUMMARY_MENU (sSummaryMenuEntries; the rank up's description)
    pl_CastleInfo 2, 0, CS_RANK
    pl_msg_sys CASTLE_OPP + 37                          // Check the stats of the Pokémon.
    ListMenu_AnchorTopRight 31, 11, 0, 0, CS_CHOICE
    ListMenuAdd CASTLE_OPP + 33, CASTLE_OPP + 37, CB_STATS        // SUMMARY
    ListMenuAdd CASTLE_OPP + 34, CASTLE_OPP + 38, CB_MOVES        // MOVES: Check the move list of the Pokémon.
    pl_CastleIf CS_RANK, 1, .Lco_sum_r1
    ListMenuAdd CASTLE_OPP + 35, CASTLE_OPP + 40, CB_RANK_INFO    // RANK UP: Your rank cannot be raised any higher.
    VMJump .Lco_sum_show
.Lco_sum_r1:
    ListMenuAdd CASTLE_OPP + 35, CASTLE_OPP + 39, CB_RANK_INFO    // RANK UP: ... check moves using CP by going up in rank.
.Lco_sum_show:
    ListMenuAdd CASTLE_OPP + 36, CASTLE_OPP + 41, CS_CANCEL
    ListMenuShow
    pl_CloseMessage
    pl_CastleIf CS_CHOICE, CS_CANCEL, .Lco_mon
    pl_CastleAsk CS_CHOICE, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_MAX_RANK, .Lco_sum_beep
    pl_CastleIf CS_RESULT, CR_RANK_TOO_LOW, .Lco_moves_low
    pl_CastleIf CS_RESULT, CR_KNOWN, .Lco_show
    pl_CastleIf CS_CHOICE, CB_RANK_INFO, .Lco_rank
    pl_CastleIf CS_CHOICE, CB_MOVES, .Lco_moves_ask
    pl_CastleAskYesNo CASTLE_OPP + 43                   // UNLOCK_MONS_STATS_YES_NO: check this Pokémon's stats ... N CP
    pl_CastleIf CS_YESNO, 1, .Lco_summary
    pl_CastleBuy CB_STATS, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lco_cp1
    SEPlay SEQ_SE_DECIDE2
    pl_CastleSay CASTLE_OPP + 47                        // The Pokémon's stat summary was bought.
    VMJump .Lco_show
.Lco_moves_ask:
    pl_CastleAskYesNo CASTLE_OPP + 66                   // UNLOCK_MONS_MOVES_YES_NO: check this Pokémon's move list ... N CP
    pl_CastleIf CS_YESNO, 1, .Lco_summary
    pl_CastleBuy CB_MOVES, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lco_cp2
    SEPlay SEQ_SE_DECIDE2
    pl_CastleSay CASTLE_OPP + 70                        // The Pokémon's move-list data was bought.
.Lco_show:                                              // SHOW_STATS_DISPLAY, SHOW_MOVES_DISPLAY
    pl_CastleIf CS_CHOICE, CB_MOVES, .Lco_show_moves
    pl_CastleMonWords 1, CS_SLOT, 1
    pl_CastleSay CASTLE_LINES + 1
    VMJump .Lco_mon
.Lco_show_moves:
    pl_CastleMonWords 1, CS_SLOT, 2
    pl_CastleSay CASTLE_LINES + 2
    VMJump .Lco_mon
.Lco_cp1:
    pl_CastleSay CASTLE_OPP + 46                        // You don't have enough CP...
    VMJump .Lco_pick
.Lco_cp2:
    pl_CastleSay CASTLE_OPP + 69
    VMJump .Lco_pick
.Lco_moves_low:                                         // WAIT_RETURN_TO_SUMMARY_MENU
    pl_CastleSay CASTLE_OPP + 42                        // You are too low in information rank to check the target's move list.
    VMJump .Lco_summary
.Lco_sum_beep:
    SEPlay SEQ_SE_BEEP
    VMJump .Lco_summary
.Lco_rank:                                              // RANK_UP_SUMMARY_YES_NO
    pl_CastleAskYesNo CASTLE_OPP + 76                   // Would you like to up your rank for N CP?
    pl_CastleIf CS_YESNO, 1, .Lco_summary
    pl_CastleBuy CB_RANK_INFO, CS_SLOT, 0, CS_RESULT
    pl_CastleIf CS_RESULT, CR_NOT_ENOUGH_CP, .Lco_rank_cp
    pl_CastleSay CASTLE_OPP + 80                        // PLAYER gained the ability to buy the target's move-list information.
    VMJump .Lco_summary
.Lco_rank_cp:
    pl_CastleSay CASTLE_OPP + 69
    VMJump .Lco_summary
.Lco_exit:
    VMReturn
    .endm
// ---- end plat-castle
