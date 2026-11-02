// Pearl's Secret Bases: global scripts 10735-. Written by b2tools/secret_base_scripts.py: do not edit
// (notes/SECRET_BASES.md).
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

#define SB_W_A 0x8050
#define SB_W_ARG 0x8051
#define SB_W_LIST 0x8052
#define SB_W_RES 0x8053

    .equ SB_OP_DRILL_CHECK, 0
    .equ SB_OP_HOLE_SHOW, 1
    .equ SB_OP_MAKE, 2
    .equ SB_OP_ENTER, 3
    .equ SB_OP_LEAVE, 4
    .equ SB_OP_WORD, 5
    .equ SB_OP_WORD_ARTICLE, 6
    .equ SB_OP_LIST, 7
    .equ SB_OP_SLOT, 8
    .equ SB_OP_RECEIVE, 9
    .equ SB_OP_STORE, 10
    .equ SB_OP_TRASH, 11
    .equ SB_OP_COUNTS, 12
    .equ SB_OP_HOLD, 13
    .equ SB_OP_CURSOR, 14
    .equ SB_OP_CURSOR_END, 15
    .equ SB_OP_CAN_PLACE, 16
    .equ SB_OP_PLACE, 17
    .equ SB_OP_AT_CURSOR, 18
    .equ SB_OP_REMOVE, 19
    .equ SB_OP_MOVE_BEGIN, 20
    .equ SB_OP_MOVE_END, 21
    .equ SB_OP_SHOP, 22
    .equ SB_OP_PRICE, 23
    .equ SB_OP_GIVE, 24
    .equ SB_OP_HAS_ROOM, 25
    .equ SB_OP_FLAGS, 26
    .equ SB_OP_FLAG_INFO, 27
    .equ SB_OP_RECORD, 28
#define SBT_DRILL_USED 439
#define SBT_CAVERN 440
#define SBT_MAKE_HERE 441
#define SBT_MOVE_HERE 442
#define SBT_CANT_USE 443
#define SBT_CLOSED_HOLE 444
#define SBT_GO_IN 445
#define SBT_ENTERED 446
#define SBT_EXIT_ASK 447
#define SBT_GO_UP_ASK 448
#define SBT_M_GOODS 449
#define SBT_M_GO_UP 450
#define SBT_M_CLOSE 451
#define SBT_M_DRILL 452
#define SBT_BAG_WHAT 453
#define SBT_THREW 454
#define SBT_M_TRASH 455
#define SBT_M_CANCEL 456
#define SBT_PC_DECORATE 457
#define SBT_PC_STORE 458
#define SBT_PC_RECEIVE 459
#define SBT_PC_FLAGS 460
#define SBT_PC_EXIT 461
#define SBT_PD_DECORATE 462
#define SBT_PD_STORE 463
#define SBT_PD_RECEIVE 464
#define SBT_PD_FLAGS 465
#define SBT_PD_EXIT 466
#define SBT_WITHDRAWN 467
#define SBT_STORED 468
#define SBT_PC_FULL 469
#define SBT_BAG_FULL 470
#define SBT_NO_WITHDRAW 471
#define SBT_NEED_GOODS 472
#define SBT_D_DECORATE 473
#define SBT_D_PUT_AWAY 474
#define SBT_D_MOVE 475
#define SBT_D_CANCEL 476
#define SBT_DD_DECORATE 477
#define SBT_DD_PUT_AWAY 478
#define SBT_DD_MOVE 479
#define SBT_DD_CANCEL 480
#define SBT_PLACED 481
#define SBT_CANT_PLACE 482
#define SBT_RETURNED 483
#define SBT_BOULDER_GONE 484
#define SBT_BOULDER_NEVER 485
#define SBT_BOULDER_NO_MOVE 486
#define SBT_BOULDER_ONE 487
#define SBT_BOULDER_NO_MORE 488
#define SBT_NO_GOODS 489
#define SBT_LIMIT 490
#define SBT_ON_SHOW 491
#define SBT_PC_NO_PUT 492
#define SBT_PC_NO_MOVE 493
#define SBT_BOULDER_MANY 494
#define SBT_FLAG_REG 495
#define SBT_RANK_1 496
#define SBT_RANK_2 497
#define SBT_RANK_3 498
#define SBT_RANK_4 499
#define SBT_WELCOME 500
#define SBT_COME_AGAIN 501
#define SBT_ELSE 502
#define SBT_NO_MONEY 503
#define SBT_THAT_WILL_BE 504
#define SBT_SEND_PC 505
#define SBT_SHOP_FULL 506
#define SBT_ON_HAND 507
#define SBT_GOODS_SET 508
#define SBT_FLAG_CARD 509

    .macro sb a, b=0
    pl_ext 0xE0 + SB_OP_\a
    .2byte \b
    .endm
    .macro sb_ifeq var, value, label
    WorkCmpConst \var, \value
    VMJumpIf CMP_EQ, \label
    .endm
    .macro sb_ifne var, value, label
    WorkCmpConst \var, \value
    VMJumpIf CMP_NE, \label
    .endm
    .macro sb_reload
    FadeOutBlackQ
    FadeWait
    FieldClose
    FieldOpen
    FadeInBlackQ
    FadeWait
    .endm
    .macro sb_end
    MsgWinCloseAll
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt
    .endm

    ScriptEntry SB_Kit           // 10735
    ScriptEntry SB_Hole           // 10736
    ScriptEntry SB_Exit           // 10737
    ScriptEntry SB_PC           // 10738
    ScriptEntry SB_Trader           // 10739
    ScriptEntry SB_Shop           // 10740
    ScriptEntry SB_Record           // 10741
    ScriptEntry SB_Arrive           // 10742
    ScriptEntriesEnd


// ---- the Explorer Kit's Use in the tunnels, in place of UG_GoUp (underground_itcm.c); 0x4010 = 1 goes up as UG_GoUp's yes
// (Pearl's Underground menu keeps TRAPS, SPHERES, TREASURES for what isn't built: the Digger Drill is the Kit's own entry)
SB_Kit:
    ActorsPauseAll
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    ListMenuAdd SBT_M_DRILL, 0xffff, 0
    ListMenuAdd SBT_M_GOODS, 0xffff, 1
    ListMenuAdd SBT_M_GO_UP, 0xffff, 2
    ListMenuAdd SBT_M_CLOSE, 0xffff, 3
    ListMenuShow
    sb_ifeq SB_W_LIST, 0, L_Drill
    sb_ifeq SB_W_LIST, 1, L_KitGoods
    sb_ifeq SB_W_LIST, 2, L_KitUp
L_KitEnd:
    sb_end
L_KitUp:
    SystemMsg SBT_GO_UP_ASK, 2
    YesNoWin SB_W_LIST
    sb_ifne SB_W_LIST, 0, L_KitEnd
    WorkSetConst 0x4010, 1
    VMJump L_KitEnd

// Pearl's SecretBases_DiggerDrillTask
L_Drill:
    sb DRILL_CHECK
    sb_ifeq SB_W_RES, 2, L_DrillNo
    WorkSet SB_W_A, SB_W_RES
    WorkSetConst SB_W_ARG, SBT_M_DRILL        // (line 0 + the line: the word from any line of this file)
    sb WORD, 3
    SEPlay SEQ_SE_FLD_21
    SystemMsg SBT_DRILL_USED, 2
    LastKeyWait
    sb HOLE_SHOW, 1
    SystemMsg SBT_CAVERN, 2
    LastKeyWait
    sb_ifeq SB_W_A, 1, L_DrillMove
    SystemMsg SBT_MAKE_HERE, 2
    VMJump L_DrillAsk
L_DrillMove:
    SystemMsg SBT_MOVE_HERE, 2
L_DrillAsk:
    YesNoWin SB_W_LIST
    sb_ifne SB_W_LIST, 0, L_DrillCancel
    sb MAKE
    FlagSet PFLAG_0971
    MsgWinCloseAll
    SEPlay SEQ_SE_FLD_21
    FadeOutBlack
    RTReserveScript 10742
    FadeWait
    sb ENTER
    VMHalt
L_DrillCancel:
    sb HOLE_SHOW, 0
    SystemMsg SBT_CLOSED_HOLE, 2
    LastKeyWait
    VMJump L_KitEnd
L_DrillNo:
    SystemMsg SBT_CANT_USE, 2
    LastKeyWait
    VMJump L_KitEnd

// The Bag's goods: Pearl's Underground menu's GOODS, TRASH
L_KitGoods:
    WorkSetConst SB_W_A, 1
L_KitGoodsList:
    SystemMsg SBT_ON_HAND, 2
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    sb LIST, 1
    ListMenuShow
    sb_ifeq SB_W_LIST, 65520, L_KitGoodsList
    sb_ifeq SB_W_LIST, 65521, L_KitEnd
    sb_ifeq SB_W_LIST, 65534, L_KitEnd
    WorkSetConst SB_W_A, 1
    sb SLOT, SB_W_LIST
    sb WORD, 2
    SystemMsg SBT_BAG_WHAT, 2
    WorkSet 0x8054, SB_W_LIST
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    ListMenuAdd SBT_M_TRASH, 0xffff, 0
    ListMenuAdd SBT_M_CANCEL, 0xffff, 1
    ListMenuShow
    sb_ifne SB_W_LIST, 0, L_KitGoodsList
    sb TRASH, 0x8054
    SystemMsg SBT_THREW, 2
    LastKeyWait
    VMJump L_KitGoodsList

// ---- walking into the hole (gimmick 64's step check): Pearl's walk in
SB_Hole:
    ActorsPauseAll
    SystemMsg SBT_GO_IN, 2
    YesNoWin SB_W_LIST
    sb_ifne SB_W_LIST, 0, L_HoleNo
    SystemMsg SBT_ENTERED, 2
    LastKeyWait
    MsgWinCloseAll
    SEPlay SEQ_SE_FLD_21
    FadeOutBlack
    RTReserveScript 10742
    FadeWait
    sb ENTER
    VMHalt
L_HoleNo:
    sb_end

// ---- walking out: Pearl's "Exit the Secret Base?"
SB_Exit:
    ActorsPauseAll
    SystemMsg SBT_EXIT_ASK, 2
    YesNoWin SB_W_LIST
    sb_ifne SB_W_LIST, 0, L_HoleNo
    MsgWinCloseAll
    SEPlay SEQ_SE_FLD_21
    FadeOutBlack
    RTReserveScript 10742
    FadeWait
    sb LEAVE
    VMHalt

// ---- arriving: what fades the field back in
SB_Arrive:
    FadeInBlack
    FadeWait
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// ---- the base's PC (sign events on its two tiles, read facing north): Pearl's UndergroundPC menu, without its Radar
SB_PC:
    ActorsPauseAll
    SEPlay SEQ_SE_PC_LOGIN
    sb FLAGS
    sb_ifeq SB_W_RES, 0, L_PCMenu
    WorkSet 0x8054, SB_W_A
    SystemMsg SBT_FLAG_REG, 2
    LastKeyWait
    FlagSet PFLAG_0973
    sb_ifeq 0x8054, 0, L_PCMenu
    sb_ifeq 0x8054, 1, L_Rank1
    sb_ifeq 0x8054, 2, L_Rank2
    sb_ifeq 0x8054, 3, L_Rank3
    SystemMsg SBT_RANK_4, 2
    VMJump L_RankEnd
L_Rank1:
    SystemMsg SBT_RANK_1, 2
    VMJump L_RankEnd
L_Rank2:
    SystemMsg SBT_RANK_2, 2
    VMJump L_RankEnd
L_Rank3:
    SystemMsg SBT_RANK_3, 2
L_RankEnd:
    LastKeyWait
L_PCMenu:
    SystemMsg SBT_PD_DECORATE, 2
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    ListMenuAdd SBT_PC_DECORATE, SBT_PD_DECORATE, 0
    ListMenuAdd SBT_PC_STORE, SBT_PD_STORE, 1
    ListMenuAdd SBT_PC_RECEIVE, SBT_PD_RECEIVE, 2
    ListMenuAdd SBT_PC_FLAGS, SBT_PD_FLAGS, 3
    ListMenuAdd SBT_PC_EXIT, SBT_PD_EXIT, 4
    ListMenuShow
    sb_ifeq SB_W_LIST, 0, L_Decor
    sb_ifeq SB_W_LIST, 1, L_Store
    sb_ifeq SB_W_LIST, 2, L_Receive
    sb_ifeq SB_W_LIST, 3, L_Flags
    SEPlay SEQ_SE_PC_LOGOFF
    sb_end

L_Flags:
    sb FLAG_INFO
    SystemMsg SBT_FLAG_CARD, 2
    LastKeyWait
    VMJump L_PCMenu

L_Store:
    SystemMsg SBT_PD_STORE, 2
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    sb LIST, 1
    ListMenuShow
    sb_ifeq SB_W_LIST, 65520, L_Store
    sb_ifeq SB_W_LIST, 65521, L_PCMenu
    sb_ifeq SB_W_LIST, 65534, L_PCMenu
    WorkSetConst SB_W_A, 1
    sb SLOT, SB_W_LIST
    sb WORD, 2
    sb STORE, SB_W_LIST
    sb_ifne SB_W_RES, 0, L_StoreFull
    SystemMsg SBT_STORED, 2
    LastKeyWait
    VMJump L_Store
L_StoreFull:
    SystemMsg SBT_PC_FULL, 2
    LastKeyWait
    VMJump L_PCMenu

L_Receive:
    SystemMsg SBT_PD_RECEIVE, 2
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    sb LIST, 0
    ListMenuShow
    sb_ifeq SB_W_LIST, 65520, L_Receive
    sb_ifeq SB_W_LIST, 65521, L_PCMenu
    sb_ifeq SB_W_LIST, 65534, L_PCMenu
    WorkSetConst SB_W_A, 0
    sb SLOT, SB_W_LIST
    sb_ifne SB_W_RES, 0, L_ReceiveShown
    sb WORD, 2
    sb RECEIVE, SB_W_LIST
    sb_ifne SB_W_RES, 0, L_ReceiveFull
    SystemMsg SBT_WITHDRAWN, 2
    LastKeyWait
    VMJump L_Receive
L_ReceiveShown:
    SystemMsg SBT_NO_WITHDRAW, 2
    LastKeyWait
    VMJump L_Receive
L_ReceiveFull:
    SystemMsg SBT_BAG_FULL, 2
    LastKeyWait
    VMJump L_PCMenu

// ---- decorating: Pearl's BaseDecoration_MenuTask and its three tasks
L_Decor:
    FlagSet PFLAG_0972
L_DecorMenu:
    SystemMsg SBT_DD_DECORATE, 2
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    ListMenuAdd SBT_D_DECORATE, SBT_DD_DECORATE, 0
    ListMenuAdd SBT_D_PUT_AWAY, SBT_DD_PUT_AWAY, 1
    ListMenuAdd SBT_D_MOVE, SBT_DD_MOVE, 2
    ListMenuAdd SBT_D_CANCEL, SBT_DD_CANCEL, 3
    ListMenuShow
    sb_ifeq SB_W_LIST, 0, L_DecorGoods
    sb_ifeq SB_W_LIST, 1, L_PutAway
    sb_ifeq SB_W_LIST, 2, L_MoveGoods
    VMJump L_PCMenu

L_DecorGoods:
    sb COUNTS
    sb_ifne SB_W_RES, 0, L_DecorLimit
    SystemMsg SBT_GOODS_SET, 2
    LastKeyWait
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    sb LIST, 0
    sb_ifeq SB_W_RES, 0, L_DecorNone
    ListMenuShow
    sb_ifeq SB_W_LIST, 65520, L_DecorGoods
    sb_ifeq SB_W_LIST, 65521, L_DecorMenu
    sb_ifeq SB_W_LIST, 65534, L_DecorMenu
    WorkSetConst SB_W_A, 0
    sb SLOT, SB_W_LIST
    sb_ifne SB_W_RES, 0, L_DecorShown
    WorkSet 0x8054, SB_W_LIST                // the PC slot
    WorkSet 0x8055, SB_W_ARG                 // the good
    MsgWinCloseAll
    sb HOLD, 0x8055
    sb_reload
L_DecorPlace:
    sb CURSOR, 0x8055
    sb_ifeq SB_W_RES, 0, L_DecorDone
    sb CAN_PLACE
    sb_ifeq SB_W_RES, 0, L_DecorCant
    sb PLACE, 0x8054
    WorkSet SB_W_ARG, 0x8055
    sb WORD, 0
    SEPlay SEQ_SE_FLD_05
    sb CURSOR_END
    sb_reload
    SystemMsg SBT_PLACED, 2
    LastKeyWait
    VMJump L_DecorMenu
L_DecorDone:
    sb CURSOR_END
    sb_reload
    VMJump L_DecorMenu
L_DecorCant:
    SEPlay SEQ_SE_BEEP
    SystemMsg SBT_CANT_PLACE, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_DecorPlace
L_DecorLimit:
    SystemMsg SBT_LIMIT, 2
    LastKeyWait
    VMJump L_DecorMenu
L_DecorNone:
    ListMenuShow                              // (only CANCEL)
    SystemMsg SBT_NEED_GOODS, 2
    LastKeyWait
    VMJump L_DecorMenu
L_DecorShown:
    SystemMsg SBT_ON_SHOW, 2
    LastKeyWait
    VMJump L_DecorGoods

L_PutAway:
    MsgWinCloseAll
L_PutAwayCursor:
    sb CURSOR, 0
    sb_ifeq SB_W_RES, 0, L_PutAwayEnd
    sb AT_CURSOR
    sb_ifeq SB_W_RES, 0, L_PutAwayCursor
    sb_ifeq SB_W_RES, 3, L_PutAwayPC
    sb WORD, 0
    sb REMOVE
    sb_ifeq SB_W_RES, 2, L_BoulderNever
    sb_ifeq SB_W_RES, 3, L_BoulderNoMore
    WorkSet 0x8055, SB_W_RES
    WorkSet 0x8056, SB_W_A
    sb CURSOR_END
    sb_reload
    sb_ifeq 0x8055, 1, L_BoulderGone
    SEPlay SEQ_SE_FLD_05
    SystemMsg SBT_RETURNED, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_PutAwayCursor
L_BoulderGone:
    SystemMsg SBT_BOULDER_GONE, 2
    LastKeyWait
    sb_ifeq 0x8056, 0, L_BoulderLast
    sb_ifeq 0x8056, 1, L_BoulderOne
    SystemMsg SBT_BOULDER_MANY, 2
    LastKeyWait
    VMJump L_DecorMenu
L_BoulderOne:
    SystemMsg SBT_BOULDER_ONE, 2
    LastKeyWait
L_BoulderLast:
    VMJump L_DecorMenu
L_BoulderNever:
    SystemMsg SBT_BOULDER_NEVER, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_PutAwayCursor
L_BoulderNoMore:
    SystemMsg SBT_BOULDER_NO_MORE, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_PutAwayCursor
L_PutAwayPC:
    SystemMsg SBT_PC_NO_PUT, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_PutAwayCursor
L_PutAwayEnd:
    sb CURSOR_END
    VMJump L_DecorMenu

L_MoveGoods:
    MsgWinCloseAll
L_MoveCursor:
    sb CURSOR, 0
    sb_ifeq SB_W_RES, 0, L_PutAwayEnd
    sb AT_CURSOR
    sb_ifeq SB_W_RES, 0, L_MoveCursor
    sb_ifeq SB_W_RES, 3, L_MovePC
    sb_ifeq SB_W_RES, 2, L_MoveBoulder
    WorkSet 0x8055, SB_W_ARG
    sb CURSOR_END
    sb MOVE_BEGIN
    sb_reload
L_MovePlace:
    sb CURSOR, 0x8055
    sb_ifeq SB_W_RES, 0, L_MoveCancel
    sb CAN_PLACE
    sb_ifeq SB_W_RES, 0, L_MoveCant
    sb MOVE_END, 1
    SEPlay SEQ_SE_FLD_05
    sb CURSOR_END
    sb_reload
    VMJump L_DecorMenu
L_MoveCancel:
    sb MOVE_END, 0
    sb CURSOR_END
    sb_reload
    VMJump L_DecorMenu
L_MoveCant:
    SEPlay SEQ_SE_BEEP
    SystemMsg SBT_CANT_PLACE, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_MovePlace
L_MovePC:
    SystemMsg SBT_PC_NO_MOVE, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_MoveCursor
L_MoveBoulder:
    SystemMsg SBT_BOULDER_NO_MOVE, 2
    LastKeyWait
    MsgWinCloseAll
    VMJump L_MoveCursor

// ---- A on a good that says something (Pearl's UndergroundRecords_PrintEntryForDecoration)
SB_Record:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    sb RECORD
    SystemMsg SB_W_ARG, 2
    LastKeyWait
    sb_end

// ---- the goods traders in the tunnels (Pearl's vendors, for money)
SB_Trader:
    SEPlay SEQ_SE_MESSAGE
    ActorsPauseAll
    ActorSetEyeToEye
    SystemMsg SBT_WELCOME, 2
    WorkSetConst 0x8057, 2
    VMJump L_Shop

// ---- a shop: 0x8057 = the list (RTCallGlobal from Veilstone 4F's clerks: pl_GoodsMart)
SB_Shop:
    SystemMsg SBT_WELCOME, 2
L_Shop:
    MoneyWinDisp 31, 1
L_ShopList:
    ListMenu_AnchorTopLeft 1, 1, 0, 1, SB_W_LIST
    sb SHOP, 0x8057
    ListMenuShow
    sb_ifeq SB_W_LIST, 65521, L_ShopEnd
    sb_ifeq SB_W_LIST, 65534, L_ShopEnd
    WorkSet SB_W_ARG, SB_W_LIST
    sb WORD, 0
    sb PRICE, 0x8057
    SystemMsg SBT_THAT_WILL_BE, 2
    YesNoWin SB_W_LIST
    sb_ifne SB_W_LIST, 0, L_ShopElse
    sb HAS_ROOM, SB_W_ARG
    sb_ifeq SB_W_RES, 0, L_ShopFull
    MoneyCheck SB_W_RES, SB_W_A
    sb_ifeq SB_W_RES, 0, L_ShopPoor
    MoneySub SB_W_A
    MoneyWinUpdate
    sb GIVE, SB_W_ARG
    SEPlay SEQ_SE_FLD_05
    SystemMsg SBT_SEND_PC, 2
    LastKeyWait
L_ShopElse:
    SystemMsg SBT_ELSE, 2
    VMJump L_ShopList
L_ShopFull:
    SystemMsg SBT_SHOP_FULL, 2
    LastKeyWait
    VMJump L_ShopElse
L_ShopPoor:
    SystemMsg SBT_NO_MONEY, 2
    LastKeyWait
    VMJump L_ShopElse
L_ShopEnd:
    MoneyWinClose
    SystemMsg SBT_COME_AGAIN, 2
    LastKeyWait
    WorkCmpConst 0x8057, 2
    VMJumpIf CMP_NE, L_ShopGlobalEnd
    sb_end
L_ShopGlobalEnd:
    MsgWinCloseAll
    RTEndGlobal

