"""Pearl's Secret Bases' script and text (notes/SECRET_BASES.md):

    python3 secret_base_scripts.py          -> src/field_scripts/1281_secret_bases.s, src/text/script/1310_secret_bases.txt
    python3 secret_base_scripts.py --check  the files must be what the dump gives (patches/secret_bases.py runs it)

Global scripts 10735-10784 (Black 2's plugin 9: only the Black Tower's zones start it). Text: Pearl's own lines through
gen4_text; the composed ones say which Pearl lines they join. Every op is a sub-command of the extension command, row 0xE0-0xFF
(the decomp's include/pearlb2/secret_base.h: secret_base_check.py compares the numbers).
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import secret_base_data as SB  # noqa: E402

OPS = ['DRILL_CHECK', 'HOLE_SHOW', 'MAKE', 'ENTER', 'LEAVE', 'WORD', 'WORD_ARTICLE', 'LIST', 'SLOT', 'RECEIVE', 'STORE', 'TRASH',
       'COUNTS', 'HOLD', 'CURSOR', 'CURSOR_END', 'CAN_PLACE', 'PLACE', 'AT_CURSOR', 'REMOVE', 'MOVE_BEGIN', 'MOVE_END', 'SHOP',
       'PRICE', 'GIVE', 'HAS_ROOM', 'FLAGS', 'FLAG_INFO', 'RECORD']
W_A, W_ARG, W_LIST, W_RES = 0x8050, 0x8051, 0x8052, 0x8053
LIST_MORE, LIST_CANCEL, LIST_B = 0xfff0, 0xfff1, 0xfffe
ENTRIES = ['Kit', 'Hole', 'Exit', 'PC', 'Trader', 'Shop', 'Record', 'Arrive']
SCRIPT = {e: SB.GLOBAL_FIRST + i for i, e in enumerate(ENTRIES)}
T_NAME, T_DESC, T_ARTICLE, T_RANK, T_RECORD = 0, 139, 278, 417, 422
T_MORE, T_CANCEL, T_PRICE = 436, 437, 438

# (name, Pearl bank, line): the lines the scripts say, after the fixed part above
PEARL_LINES = [
    ('DRILL_USED', 575, 33), ('CAVERN', 575, 34), ('MAKE_HERE', 575, 35), ('MOVE_HERE', 575, 36), ('CANT_USE', 575, 54),
    ('CLOSED_HOLE', 575, 56), ('GO_IN', 575, 41), ('ENTERED', 575, 44), ('EXIT_ASK', 575, 50), ('GO_UP_ASK', 575, 52),
    ('M_GOODS', 575, 123), ('M_GO_UP', 575, 126), ('M_CLOSE', 575, 127), ('M_DRILL', 571, 33), ('BAG_WHAT', 575, 129),
    ('THREW', 575, 130), ('M_TRASH', 575, 132), ('M_CANCEL', 575, 133),
    ('PC_DECORATE', 580, 0), ('PC_STORE', 580, 1), ('PC_RECEIVE', 580, 2), ('PC_FLAGS', 580, 3), ('PC_EXIT', 580, 5),
    ('PD_DECORATE', 580, 6), ('PD_STORE', 580, 7), ('PD_RECEIVE', 580, 8), ('PD_FLAGS', 580, 9), ('PD_EXIT', 580, 11),
    ('WITHDRAWN', 580, 36), ('STORED', 580, 37), ('PC_FULL', 580, 38), ('BAG_FULL', 580, 39), ('NO_WITHDRAW', 580, 55),
    ('NEED_GOODS', 580, 60),
    ('D_DECORATE', 578, 1), ('D_PUT_AWAY', 578, 2), ('D_MOVE', 578, 3), ('D_CANCEL', 578, 4), ('DD_DECORATE', 578, 5),
    ('DD_PUT_AWAY', 578, 6), ('DD_MOVE', 578, 7), ('DD_CANCEL', 578, 8), ('PLACED', 578, 11), ('CANT_PLACE', 578, 12),
    ('RETURNED', 578, 13), ('BOULDER_GONE', 578, 14), ('BOULDER_NEVER', 578, 15), ('BOULDER_NO_MOVE', 578, 16),
    ('BOULDER_ONE', 578, 17), ('BOULDER_NO_MORE', 578, 18), ('NO_GOODS', 578, 19), ('LIMIT', 578, 20), ('ON_SHOW', 578, 21),
    ('PC_NO_PUT', 578, 22), ('PC_NO_MOVE', 578, 23), ('BOULDER_MANY', 578, 25),
    ('FLAG_REG', 579, 7), ('RANK_1', 579, 14), ('RANK_2', 579, 15), ('RANK_3', 579, 16), ('RANK_4', 579, 17),
    ('WELCOME', 488, 0), ('COME_AGAIN', 488, 1), ('ELSE', 488, 2), ('NO_MONEY', 488, 3), ('THAT_WILL_BE', 488, 5),
    ('SEND_PC', 488, 11), ('SHOP_FULL', 488, 12), ('ON_HAND', 580, 28),
]


def text_lines():
    import gen4_text
    names, arts = gen4_text.bank(567), gen4_text.bank(568)
    b = gen4_text.b2_line
    lines = [b(names[g]) for g in range(139)]                 # 0: names
    lines += [b(names[139 + g]) or ' ' for g in range(139)]   # 139: descriptions
    # 278: names with their articles (Pearl's "remembered colour" codes around the name: Black 2 has no such colour)
    lines += [re.sub(r'\{ff00:\d+\}', '', b(arts[g])) or ' ' for g in range(139)]
    ranks = gen4_text.bank(581)
    lines += [b(ranks[20 + r]) for r in range(5)]             # 417: Normal Flag ...
    lines += [b(ranks[32 + r]) for r in range(14)]            # 422: what a good's A says (records)
    lines += ['More...']                                      # 436: a page of the PC (Pearl's PC scrolls: not Pearl's)
    lines += [b(gen4_text.bank(578)[4])]                      # 437: CANCEL
    lines += [b(gen4_text.bank(488)[22])]                     # 438: $price
    assert len(lines) == T_PRICE + 1
    named = {}
    for name, bank, n in PEARL_LINES:
        named[name] = len(lines)
        lines.append(b(gen4_text.bank(bank)[n]) or ' ')
    # Composed from Pearl's words:
    named['GOODS_SET'] = len(lines)
    lines.append(b(gen4_text.bank(578)[9]) + ' ' + b(gen4_text.bank(578)[10]))   # bank 578 lines 9, 10: Goods Set 3/10
    named['FLAG_CARD'] = len(lines)
    lines.append('{0100:0}\\n' + b(gen4_text.bank(580)[13]) + ' {0205:1}')       # bank 581 20-24, 580 line 13
    return lines, named


def text_file():
    lines, _ = text_lines()
    return ''.join(f'SecretBases_Text_{i:03d} = {t}\n' for i, t in enumerate(lines))


def script_file():
    _, T = text_lines()
    # A list's end: 0xfff1 CANCEL, 0xfffe B
    out = ['// Pearl\'s Secret Bases: global scripts 10735-. Written by b2tools/secret_base_scripts.py: do not edit',
           '// (notes/SECRET_BASES.md).', '#include "asm/field_script.inc"', '#include "pearl.h"', '#include "pearl_story.inc"', '',
           f'#define SB_W_A {W_A:#x}', f'#define SB_W_ARG {W_ARG:#x}', f'#define SB_W_LIST {W_LIST:#x}', f'#define SB_W_RES {W_RES:#x}', '']
    for i, op in enumerate(OPS):
        out.append(f'    .equ SB_OP_{op}, {i}')
    for name, n in sorted(T.items(), key=lambda kv: kv[1]):
        out.append(f'#define SBT_{name} {n}')
    out += ['', f'    .macro sb a, b=0', '    pl_ext 0xE0 + SB_OP_\\a', '    .2byte \\b', '    .endm',
            '    .macro sb_ifeq var, value, label', '    WorkCmpConst \\var, \\value', '    VMJumpIf CMP_EQ, \\label', '    .endm',
            '    .macro sb_ifne var, value, label', '    WorkCmpConst \\var, \\value', '    VMJumpIf CMP_NE, \\label', '    .endm',
            '    .macro sb_reload', '    FadeOutBlackQ', '    FadeWait', '    FieldClose', '    FieldOpen', '    FadeInBlackQ',
            '    FadeWait', '    .endm',
            '    .macro sb_end', '    MsgWinCloseAll', '    FinishAllEvents', '    ActorsUnpauseAll', '    VMHalt', '    .endm', '']
    out += [f'    ScriptEntry SB_{e}           // {SCRIPT[e]}' for e in ENTRIES] + ['    ScriptEntriesEnd', '']
    out.append(BODY.replace('{LIST_MORE}', str(LIST_MORE)).replace('{LIST_CANCEL}', str(LIST_CANCEL))
               .replace('{LIST_B}', str(LIST_B)).replace('{Arrive}', str(SCRIPT['Arrive']))
               .replace('{FLAG_DONE}', 'PFLAG_0973'))
    return '\n'.join(out) + '\n'


# {name} are this file's numbers; SBT_ and SB_ are #defines of the script.
BODY = r'''
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
    RTReserveScript {Arrive}
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
    sb_ifeq SB_W_LIST, {LIST_MORE}, L_KitGoodsList
    sb_ifeq SB_W_LIST, {LIST_CANCEL}, L_KitEnd
    sb_ifeq SB_W_LIST, {LIST_B}, L_KitEnd
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
    RTReserveScript {Arrive}
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
    RTReserveScript {Arrive}
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
    FlagSet {FLAG_DONE}
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
    sb_ifeq SB_W_LIST, {LIST_MORE}, L_Store
    sb_ifeq SB_W_LIST, {LIST_CANCEL}, L_PCMenu
    sb_ifeq SB_W_LIST, {LIST_B}, L_PCMenu
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
    sb_ifeq SB_W_LIST, {LIST_MORE}, L_Receive
    sb_ifeq SB_W_LIST, {LIST_CANCEL}, L_PCMenu
    sb_ifeq SB_W_LIST, {LIST_B}, L_PCMenu
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
    sb_ifeq SB_W_LIST, {LIST_MORE}, L_DecorGoods
    sb_ifeq SB_W_LIST, {LIST_CANCEL}, L_DecorMenu
    sb_ifeq SB_W_LIST, {LIST_B}, L_DecorMenu
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
    sb_ifeq SB_W_LIST, {LIST_CANCEL}, L_ShopEnd
    sb_ifeq SB_W_LIST, {LIST_B}, L_ShopEnd
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
'''


def paths():
    return (os.path.join(ROOT, 'src', 'field_scripts', f'{SB.SCRIPT_FILE}_secret_bases.s'),
            os.path.join(ROOT, 'src', 'text', 'script', f'{SB.TEXT_FILE}_secret_bases.txt'))


def main():
    s, t = paths()
    src, text = script_file(), text_file()
    if '--check' in sys.argv:
        if open(s, encoding='utf-8').read() != src or open(t, encoding='utf-8').read() != text:
            raise SystemExit('secret_base_scripts: the script or text is stale: run b2tools/secret_base_scripts.py')
        print('secret_base_scripts: up to date')
        return
    open(s, 'w', encoding='utf-8').write(src)
    open(t, 'w', encoding='utf-8').write(text)
    print(f'{s}\n{t}')


if __name__ == '__main__':
    main()
