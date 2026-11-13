// Porting library for Pearl's story scripts (notes/STORY.md). b2tools/pearl_story.py translates each Pearl script command
// into one of these macros: pl_ + the command's name (Platinum's name where pokediamond has none, pokediamond's number
// always; b2tools/data/gen4_script_cmds.json), each a short sequence of Black 2 field-script commands
// (external/pokebw2/include/asm/field_script.inc) used the way Black 2's own scripts use them. Include after
// "asm/field_script.inc" and "pearl.h". Emits no code by itself. Model: HoennB2 src/include/hoenn_story.inc.
//
// Facts the macros rely on (Black 2 code: pokebw2 src/ov012, src/ov036; Pearl: pokediamond, Platinum for names):
// - Comparisons: Black 2's VM is Gen 4's. WorkCmpConst/WorkCmpWork set the comparison register to 0 less, 1 equal,
//   2 greater, and VMJumpIf/VMCallIf take Pearl's conditions unchanged (0 LT, 1 EQ, 2 GT, 3 LE, 4 GE, 5 NE: ov012
//   scrcmd_vm.c VM_CMP_LUT = pokediamond's). Pearl's CheckFlag sets the register to the flag (0/1): here FlagGet +
//   WorkCmpConst against 1 gives the same 0 (unset = "less") / 1 (set = "equal").
// - Directions are the same in both games: 0 up, 1 down, 2 left, 3 right.
// - Movement codes are the same numbers in both games for every code Pearl's scripts use (b2tools/data/
//   pearl_movement.json; both fields run at 30 fps, the same frames per tile).
// - Script works: Black 2 has 0x8000-0x8061 per script; RTCallGlobal keeps 0x8020-0x805E of the caller
//   (ov012 FieldScriptEnv_Save/Restore) and shares 0x8000-0x801F with the callee; 0x8011 is the talked-to actor.
//   Pearl's 0x8000-0x800F are 0x8020-0x802F here (pearl.h PVAR_LOCAL), so a Black 2 global call never clobbers them.
// - ActorMsg / ParentActorMsg / SystemMsg return when the text is printed, like Pearl's Message; LastKeyWait = Pearl's
//   WaitButton; MsgWinCloseAll closes every message window (Pearl's CloseMessage).
// - ActorDelete does not set the NPC's hide flag; Pearl's RemoveObject does: pl_RemoveObject takes the flag.
#define PL_TMP 0x8040          // library scratch (never a Pearl var)
#define PL_TMP2 0x8041
#define PL_PLAYER 255          // Black 2's player actor (Pearl 0xFF)
#define PL_ELEVATOR_FROM 0x401E // map-local (cleared on a zone change; Pearl's 13 map-local vars take 0x4010-0x401C):
                                // in an elevator room, the floors above the floor the player came from (pearl_story
                                // ELEVATOR_FLOORS_ABOVE, PearlElevatorInit)

// ---- script frame ----------------------------------------------------------------------------------------------
    .macro pl_End                          // 0x02 End
    VMHalt
    .endm
    .macro pl_LockAll                      // 0x60 LockAll (pokediamond LockAllEvents)
    ActorsPauseAll
    .endm
    .macro pl_ReleaseAll                   // 0x61 ReleaseAll: Black 2 ends every script with these two
    FinishAllEvents
    ActorsUnpauseAll
    .endm
    .macro pl_FacePlayer                   // 0x68 FacePlayer: the talked-to NPC and the player face each other
    ActorSetEyeToEye
    .endm
    .macro pl_WaitTime frames, var         // 0x03 WaitTime frames, countdown var (both fields run at 30 fps)
    VMSleep \frames
    .endm

// ---- flow --------------------------------------------------------------------------------------------------------
    .macro pl_GoTo label                   // 0x16
    VMJump \label
    .endm
    .macro pl_GoToIf cond, label           // 0x1C
    VMJumpIf \cond, \label
    .endm
    .macro pl_Call label                   // 0x1A
    VMCall \label
    .endm
    .macro pl_CallIf cond, label           // 0x1D
    VMCallIf \cond, \label
    .endm
    .macro pl_Return                       // 0x1B
    VMReturn
    .endm
    .macro pl_ReturnCommonScript           // 0x15 ReturnCommonScript (pokediamond RestartCurrentScript): a Pearl common
    VMReturn                               // script is translated as a subroutine of the zone file (VMCall)
    .endm

// ---- flags, vars, comparisons --------------------------------------------------------------------------------------
    .macro pl_CompareVarToValue var, value // 0x11
    WorkCmpConst \var, \value
    .endm
    .macro pl_CompareVarToVar var1, var2   // 0x12
    WorkCmpWork \var1, \var2
    .endm
    .macro pl_CheckFlag flag               // 0x20: register = flag (0 "less", 1 "equal")
    FlagGet \flag, PL_TMP
    WorkCmpConst PL_TMP, 1
    .endm
    .macro pl_CheckFlagFromVar var         // 0x21: the flag whose number is in var (FlagGet reads a work's value)
    FlagGet \var, PL_TMP
    WorkCmpConst PL_TMP, 1
    .endm
    .macro pl_SetFlag flag                 // 0x1E
    FlagSet \flag
    .endm
    .macro pl_ClearFlag flag               // 0x1F
    FlagReset \flag
    .endm
    .macro pl_SetFlagFromVar var           // 0x22
    FlagSet \var
    .endm
    .macro pl_SetVarFromValue var, value   // 0x28 (pokediamond SetVar)
    WorkSetConst \var, \value
    .endm
    .macro pl_SetVarFromVar dst, src       // 0x29 (pokediamond CopyVar)
    WorkSet \dst, \src
    .endm
    .macro pl_AddVar var, value            // 0x26 (value: a number or a var, as Pearl's VarGet)
    WorkAdd \var, \value
    .endm
    .macro pl_SubVar var, value            // 0x27
    WorkSub \var, \value
    .endm
    .macro pl_GetRandom var, n             // 0x1B7 (pokediamond Random)
    Random \var, \n
    .endm
    .macro pl_SetTrainerFlag id            // 0x23 (Black 2 trainer flag = id + 1520)
    TrainerFlagSet \id
    .endm
    .macro pl_ClearTrainerFlag id          // 0x24
    TrainerFlagReset \id
    .endm
    .macro pl_CheckTrainerFlag id          // 0x25: register = 1 when beaten
    TrainerFlagGet \id, PL_TMP
    WorkCmpConst PL_TMP, 1
    .endm

// ---- messages: n = line of the zone's text file (src/text/script/NNNN_pearl_*.txt, 0-based) -------------------------
// Pearl has one plain message box; Black 2 shows a talking person's line in a balloon over them. The translator picks
// per Message (b2tools/pearl_story.py speaker): the talked-to NPC (pl_msg_talk), a named actor (pl_msg_actor), or no one
// (pl_msg_sys: Black 2's plain window, as Pearl's box).
    .macro pl_msg_talk n                   // 0x2C Message, said by the NPC the player talked to
    ParentActorMsg MSGFILE_SCRIPT, \n, 0, 0
    .endm
    .macro pl_msg_actor n, actor           // 0x2C Message, said by actor `actor` (uid; 255 = the player)
    ActorMsg MSGFILE_SCRIPT, \n, \actor, 0, 0
    .endm
    .macro pl_msg_talk_low n               // pl_msg_talk with the balloon at the bottom (a script that shows the money
    ParentActorMsg MSGFILE_SCRIPT, \n, 2, 0  // window: pearl_story money_layout, Black 2's black_city_5.s)
    .endm
    .macro pl_msg_actor_low n, actor       // pl_msg_actor with the balloon at the bottom (the same)
    ActorMsg MSGFILE_SCRIPT, \n, \actor, 2, 0
    .endm
    .macro pl_msg_sys n                    // 0x2C Message, nobody's (scenes, signs read as objects, "received")
    SystemMsg \n, 2
    .endm
    // a line naming the counterpart (Dawn for a boy, Lucas for a girl): two lines, Black 2's own gendered message
    .macro pl_msg_talk_gendered nboy, ngirl
    ActorMsgGendered MSGFILE_SCRIPT, \nboy, \ngirl, 0x8011, 0, 0
    .endm
    .macro pl_msg_actor_gendered nboy, ngirl, actor
    ActorMsgGendered MSGFILE_SCRIPT, \nboy, \ngirl, \actor, 0, 0
    .endm
    .macro pl_msg_sys_gendered nboy, ngirl
    TrainerCardGetSex PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lplg\@
    SystemMsg \nboy, 2
    VMJump .Lplg2\@
.Lplg\@:
    SystemMsg \ngirl, 2
.Lplg2\@:
    .endm
    .macro pl_WaitButton                   // 0x31 WaitButton (A/B, after a message)
    LastKeyWait
    .endm
    .macro pl_WaitABPress                  // 0x30
    LastKeyWait
    .endm
    .macro pl_WaitABPadPress               // 0x32 (A/B or the d-pad: Black 2 waits for A/B)
    LastKeyWait
    .endm
    .macro pl_CloseMessage                 // 0x34 (pokediamond CloseMessageBox)
    MsgWinCloseAll
    .endm
    .macro pl_CloseMessageWithoutErasing   // 0x35
    MsgWinCloseAll
    .endm
    .macro pl_ShowYesNoMenu var            // 0x3E: var 0 YES, 1 NO in both games
    YesNoWin \var
    .endm
    // signs (Pearl 0x36 DrawSignpostInstantMessage + 0x38/0x39/0x3B + common script 2000): Black 2's sign window.
    // Types: Pearl 0 map (town) -> Black 2 1, 1 arrow (route) -> 3, 2 landmark (houses) -> 2, 3 scrolling -> 0
    .macro pl_sign n, b2type
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign \n, \b2type
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    .endm

// word buffers (Pearl {STRVAR_1 t, n} -> Black 2 {01tt:n}: the same buffer numbers)
    .macro pl_BufferPlayerName n           // 0xCD
    WordSetPlayerName \n
    .endm
    .macro pl_BufferRivalName n            // 0xCE: Barry = the rival name Black 2's opening asks for
    WordSetLoadRivalName \n
    .endm
    .macro pl_BufferItemName n, item       // 0xD1
    WordSetItemName \n, \item
    .endm
    // Pockets: Pearl numbers them 0 items, 1 medicine, 2 balls, 3 TMs, 4 berries, 5 mail, 6 battle items, 7 key items;
    // Black 2 0 items (balls, mail and battle items too), 1 medicine, 2 TMs, 3 berries, 4 key items (pokebw2
    // constants/bag.h). Black 2's WordSetItemPocketName takes an ITEM and names its pocket (scrcmd_word.c), so a Pearl
    // pocket is named through an item of that pocket. (Found in game 2026-10-18: the Journal "put in the ITEMS
    // Pocket" with the item jingle, as Pearl's key-item branches never ran.)
    .macro pl_BufferPocketName n, pocket   // 0xD2 (pocket: Pearl's number, as pl_GetItemPocket gives it)
    WorkSetConst PL_TMP2, ITEM_POKE_BALL   // items, balls, mail, battle items
    WorkCmpConst \pocket, 1
    VMJumpIf CMP_NE, .Lpbp1\@
    WorkSetConst PL_TMP2, ITEM_POTION
.Lpbp1\@:
    WorkCmpConst \pocket, 3
    VMJumpIf CMP_NE, .Lpbp3\@
    WorkSetConst PL_TMP2, ITEM_TM01
.Lpbp3\@:
    WorkCmpConst \pocket, 4
    VMJumpIf CMP_NE, .Lpbp4\@
    WorkSetConst PL_TMP2, ITEM_CHERI_BERRY
.Lpbp4\@:
    WorkCmpConst \pocket, 7
    VMJumpIf CMP_NE, .Lpbp7\@
    WorkSetConst PL_TMP2, ITEM_BICYCLE
.Lpbp7\@:
    WordSetItemPocketName \n, PL_TMP2
    .endm
    .macro pl_BufferSpeciesName n, species // species from a number or a var
    WordSetPokeSpecies \n, \species
    .endm
    .macro pl_BufferPartyMonSpecies n, slot    // 0xD0
    WordSetPartyPokeSpecies \n, \slot
    .endm
    .macro pl_BufferPartyMonNickname n, slot   // 0xD6
    WordSetPartyPokeName \n, \slot
    .endm
    .macro pl_BufferMoveName n, move       // 0xD4
    WordSetMoveName \n, \move
    .endm
    .macro pl_BufferTMHMMoveName n, item   // 0xD3
    WordSetTMMoveName \n, \item
    .endm
    .macro pl_BufferNumber n, value, digits=0   // 0xD5: a number (Black 2 counts its own digits with 0)
    WordSetNumber \n, \value, \digits
    .endm
    .macro pl_BufferMapName n, zone        // 0xE2: zone = a Black 2 zone
    WordSetPlaceName \n, \zone
    .endm
    .macro pl_BufferTrainerClassName n, cls    // 0xD8
    WordSetTrainerClassName \n, \cls
    .endm
    // the starters: Pearl keeps the player's choice in its save; here PVAR_STARTER (pearl.h) holds the species
    .macro pl_GetPlayerStarterSpecies var      // 0xDE
    WorkSet \var, PVAR_STARTER
    .endm
    .macro pl_BufferPlayerStarterSpeciesName n // 0xDB
    WordSetPokeSpecies \n, PVAR_STARTER
    .endm
    .macro pl_rival_starter var                // the starter strong against the player's (Turtwig > Piplup > Chimchar)
    WorkSetConst \var, SPECIES_CHIMCHAR
    WorkCmpConst PVAR_STARTER, SPECIES_TURTWIG
    VMJumpIf CMP_EQ, .Lprs\@
    WorkSetConst \var, SPECIES_PIPLUP
    WorkCmpConst PVAR_STARTER, SPECIES_CHIMCHAR
    VMJumpIf CMP_EQ, .Lprs\@
    WorkSetConst \var, SPECIES_TURTWIG
.Lprs\@:
    .endm
    .macro pl_counterpart_starter var          // the one left in the briefcase
    WorkSetConst \var, SPECIES_PIPLUP
    WorkCmpConst PVAR_STARTER, SPECIES_TURTWIG
    VMJumpIf CMP_EQ, .Lpcs\@
    WorkSetConst \var, SPECIES_TURTWIG
    WorkCmpConst PVAR_STARTER, SPECIES_CHIMCHAR
    VMJumpIf CMP_EQ, .Lpcs\@
    WorkSetConst \var, SPECIES_CHIMCHAR
.Lpcs\@:
    .endm
    .macro pl_BufferRivalStarterSpeciesName n  // 0xDC
    pl_rival_starter PL_TMP2
    WordSetPokeSpecies \n, PL_TMP2
    .endm
    .macro pl_BufferCounterpartStarterSpeciesName n    // 0xDD
    pl_counterpart_starter PL_TMP2
    WordSetPokeSpecies \n, PL_TMP2
    .endm

// ---- player and gender -------------------------------------------------------------------------------------------
    .macro pl_GetPlayerGender var          // 0x14D: Pearl 0 boy, 1 girl = Black 2's TrainerCardGetSex
    TrainerCardGetSex \var
    .endm
    .macro pl_GetPlayerMapPos varx, varz   // 0x69 (pokediamond GetPlayerPosition): the same tile numbers (matrix 0 and
    PlayerGetGPos \varx, \varz             // the rooms keep Pearl's layout)
    .endm
    .macro pl_GetPlayerDir var             // 0x1BD
    PlayerGetDir \var
    .endm

// ---- objects ---------------------------------------------------------------------------------------------------
    .macro pl_ApplyMovement actor, list    // 0x5E: actor = Pearl's local id = the Black 2 NPC uid; 255 the player
    ActorCmdExec \actor, \list
    .endm
    .macro pl_WaitMovement                 // 0x5F
    ActorCmdWait
    .endm
    .macro pl_AddObject uid                // 0x64 (Pearl clears the hide flag itself before)
    ActorAdd \uid
    .endm
    .macro pl_RemoveObject uid, flag       // 0x65: deletes the actor and sets its hide flag, as Pearl's does
    ActorDelete \uid
    .if \flag
    FlagSet \flag
    .endif
    .endm
// Pearl's item-ball script (file 370 script 256) removes the talked-to ball (RemoveEvent VAR_LAST_TALKED), and Pearl's
// RemoveEvent sets the object's flag; here the ball's own hide flag (data/pearl_item_balls.json), read from the actor
// as Black 2's item script does (global 7000 Script_401: ActorGetSpawnFlag 0x8011 + FlagSet + ActorDelete).
    .macro pl_RemoveTalkedObject
    WorkSetConst PL_TMP, 0
    ActorGetSpawnFlag 0x8011, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lprto\@
    FlagSet PL_TMP
.Lprto\@:
    ActorDelete 0x8011
    .endm
    .macro pl_SetMovementType uid, move    // 0x6D: live actor (Black 2 move code)
    ActorSetMoveCode \uid, \move
    .endm
    .macro pl_SetPosition uid, x, y, z, dir    // 0x187: live actor
    ActorSetGPos \uid, \x, \y, \z, \dir
    .endm
// Pearl's SetObjectEventPos outside the zone init sets where an object appears when AddObject adds it; Black 2 cannot
// change its NPC list there (ObjInitNPCGPos: level 2 only), so the place goes into script works and pl_AddObjectAt sets
// the new actor there. Works 0x8030-0x803E (3 per object slot, 5 slots): script-local (ov012 ScriptWork localWork
// 0x8000-0x8061, cleared when the script starts: GFL_HeapAllocate(.., TRUE, ..)), kept across RTCallGlobal
// (ScriptWork_CreateVarCopy saves 0x8020-0x805E); x = 0 means "not set in this run" (2026-10-20: the counterpart at
// Jublife's entrance always appeared at x 175, the last of Pearl's three branches, not above the player)
#define PL_OBJ_X(slot) (0x8030 + 3 * (slot))
#define PL_OBJ_Y(slot) (0x8031 + 3 * (slot))
#define PL_OBJ_Z(slot) (0x8032 + 3 * (slot))
    .macro pl_SetObjectEventPosLater slot, uid, x, y, z, dir    // 0x186 outside the zone init
    ActorSetGPos \uid, \x, \y, \z, \dir    // (the live actor, if it is there, as before)
    WorkSet PL_OBJ_X(\slot), \x
    WorkSet PL_OBJ_Y(\slot), \y
    WorkSet PL_OBJ_Z(\slot), \z
    .endm
    .macro pl_AddObjectAt uid, slot, dir   // 0x64 after a pl_SetObjectEventPosLater of this object: there
    ActorAdd \uid
    WorkCmpConst PL_OBJ_X(\slot), 0
    VMJumpIf CMP_EQ, .Lpaoa\@
    ActorSetGPos \uid, PL_OBJ_X(\slot), PL_OBJ_Y(\slot), PL_OBJ_Z(\slot), \dir
.Lpaoa\@:
    .endm
    // event data before the actors exist (Pearl ON_TRANSITION = Black 2 zone init, level 2 only): index = position in the
    // zone's NPC list (the events patch keeps Pearl's order), y in 16-unit steps
    .macro pl_SetObjectEventPos index, x, z, dir, y=0     // 0x186 (+ the NPC's direction from its event)
    ObjInitNPCGPos \index, \dir, \x, \y, \z
    .endm
    .macro pl_SetWarpEventPos index, x, z, y=0  // 0x18A (Black 2 tiles, as Pearl's)
    ObjInitWarpGPos \index, \x, \y, \z
    .endm

    .macro pl_SetBgEventPos index, x, z, y=0    // 0x18B: a sign (BG event) moved (Black 2 tiles, y in units)
    ObjInitPointGPos \index, \x, \z, \y
    .endm

// ---- sound -----------------------------------------------------------------------------------------------------
    .macro pl_PlaySE se                    // 0x49 (pokediamond PlayFanfare)
    SEPlay \se
    .endm
    .macro pl_WaitSE se                    // 0x4B
    SEWait
    .endm
    .macro pl_StopSE se                    // 0x4A
    SEStop
    .endm
    .macro pl_PlayFanfare me               // 0x4E (pokediamond PlaySound): pauses the music, Black 2's ME
    MEPlay \me
    .endm
    .macro pl_WaitFanfare                  // 0x4F
    MEWait
    .endm
    .macro pl_PlayCry species              // 0x4C
    PVPlay \species, 0
    .endm
    .macro pl_WaitCry                      // 0x4D
    PVWait
    .endm
    .macro pl_PlayMusic bgm                // 0x50 / 0x57 SetBGM
    BGMPlay \bgm
    .endm
    .macro pl_PlayDefaultMusic             // 0x52: the zone's music again
    BGMChangeMap
    .endm
    .macro pl_FadeOutBGM frames            // 0x54
    BGMFadeOut \frames
    .endm

// ---- screen ------------------------------------------------------------------------------------------------------
    .macro pl_fade_out_black               // 0xBC FadeScreen _, _, 0 (out), black
    FadeOutBlack
    .endm
    .macro pl_fade_in_black                // 0xBC FadeScreen _, _, 1 (in), black
    FadeInBlack
    .endm
    .macro pl_fade_out_white
    FadeOutWhite
    .endm
    .macro pl_fade_in_white
    FadeInWhite
    .endm
    .macro pl_WaitFadeScreen               // 0xBD
    FadeWait
    .endm

// ---- warps ---------------------------------------------------------------------------------------------------------
    .macro pl_Warp zone, x, z, dir         // 0xBE Warp: Black 2 zone, Pearl's tile (the same tiles), dir 0-3. Black 2 puts
    MapChangeCore \zone, \x, 0, \z, \dir   // the player on the ground at the tile
    .endm
// ---- boats (Pearl 0x23D ShipAnimation: its ship scenes) -----------------------------------------------------------
// As HoennB2's boats (its src/field_scripts/common/boat.inc, notes/DECISIONS.md 2026-10-07): Black 2's own 3D boat
// cutscenes (Call3DDemo, overlay 293), which play on a closed field: fade out, FieldClose, the demo, FieldOpen on a
// black screen; then the generator's RTReserveScript + pl_Warp change the map, and the destination's arrival script
// (PearlArrive) fades in. Pearl's own docked boats stay on the maps. Pearl's ShipAnimation names the way the ship
// sails (pokeplatinum BOAT_TRAVEL_DIR_*): north-south and south-north are Canalave's regular ship, Eldritch's boat
// (Iron Island, Fullmoon and Newmoon Islands); east-west and west-east are the Snowpoint steamship (the Fight Area).
//   PL_BOAT_DEMO_SMALL = demo 4, Black 2's white motorboat (Castelia -> Unity Tower) with Castelia's pier hidden
//     (patches/boat_demos.py): a sailor's own small boat, as Eldritch's is, speeding off on the open sea;
//   PL_BOAT_DEMO_SHIP = demo 26, Black 2's Virbank ferry crossing the open sea: a big two-funnel passenger ship, as
//     Pearl's Snowpoint steamship is.
// Pearl silences the field music for its ship scenes (pokeplatinum FieldSystem_PlayBoatCutscene: SEQ_NONE), so the
// music fades out for both (demo 4 then has only its engine sounds, demo 26 its own ship music). Test from a cold boot:
// a savestate made on another build's file layout plays a black screen (HoennB2's finding).
#define PL_BOAT_DEMO_SMALL 4
#define PL_BOAT_DEMO_SHIP 26
    .macro pl_boat_ride demo
    FadeOutBlackQ
    BGMFadeOut 30
    FadeWait
    FieldClose
    Call3DDemo \demo, 0
    FieldOpen
    .endm
    .macro pl_BoatCutscene travel          // travel: Pearl's way (0 S->N, 1 E->W, 2 W->E, 3 N->S), a constant
    .if \travel == 1 || \travel == 2
    pl_boat_ride PL_BOAT_DEMO_SHIP
    .else
    pl_boat_ride PL_BOAT_DEMO_SMALL
    .endif
    .endm

// ---- the camera shake (Pearl 0x29F ShakeCamera: the Canalave Library's tremor) ----------------------------------
// Black 2's event camera shake with a rumble, the values of its own quake scenes (global 10470: "A dull sound echoed"
// 5, 0, 3, 8, 1, 0, 1, 5; "The dull sound is close!" 8, 0, 3, 15, 1, 0, 1, 5): x amplitude, y amplitude, period, steps
    .macro pl_ShakeCamera kind             // kind: Pearl's 0 (short) or 1 (long), a constant
    .if \kind == 0
    SEPlay SEQ_SE_FLD_154
    EvCameraShake 5, 0, 3, 8, 1, 0, 1, 5
    .else
    SEPlay SEQ_SE_FLD_155
    EvCameraShake 8, 0, 3, 15, 1, 0, 1, 5
    .endif
    SEWait
    .endm

// ---- Spear Pillar (chapter 7, 2026-10-26) ------------------------------------------------------------------------
// Pearl 0x20D SpearPillarSequence op, var (pokediamond ov06 SpearPillarSequence): Pearl's own effects of the summoning
// at the altar, which Black 2 has no counterpart for. Ops 1 and 6 report through the var whether the effect started by
// op 0 / op 5 is over, and the script loops until they say so (the var holds 0 from the WaitTime before it: a hang if
// nothing sets it): here the effect is a white flash, over at once. Ops 0 (the Red Chain opens the portal), 4 (the new
// galaxy) and 5 (the lake trio's power) flash white; ops 2 and 3 (an effect kept from the portal until after the tag
// battle) and 7-9 (the sky distorting at Spear Pillar, Valley Windworks, Hearthome, each shown 90 frames with Pearl's
// music) show nothing. The flash's sound is a [guess] (Black 2's Hypnosis wave).
    .macro pl_SpearPillarSequence op, var
    .if \op == 1 || \op == 6
    WorkSetConst \var, 1
    .elseif \op == 0 || \op == 4 || \op == 5
    .if \op == 0
    SEPlay SEQ_SE_W095_01
    .endif
    FadeOutWhiteQ
    FadeWait
    FadeInWhiteQ
    FadeWait
    .endif
    .endm
// Pearl 0xEE CheckHasTwoAliveMons var (pokediamond HasEnoughAlivePokemonForDoubleBattle): var = 1 if two Pokémon can
// battle (Black 2's PokePartyGetCount kind 2: not eggs, HP left), else 0 (Spear Pillar's two grunts, a double battle)
    .macro pl_CheckHasTwoAliveMons var
    PokePartyGetCount \var, 2
    WorkCmpConst \var, 2
    VMJumpIf CMP_GE, .Lptm1\@
    WorkSetConst \var, 0
    VMJump .Lptme\@
.Lptm1\@:
    WorkSetConst \var, 1
.Lptme\@:
    .endm
// Pearl 0x1B2 HideObject / 0x1B1 ShowObject (pokeplatinum MapObject_SetHidden; pokediamond names them the other way
// round): the person (or the player, 255) stays but is not drawn = Black 2's SetInvisible / SetVisible moves (69, 70,
// the same codes as Pearl's 0x45 / 0x46)
    .macro pl_HideObject actor
    ActorCmdExec \actor, .Lpho\@
    ActorCmdWait
    VMJump .Lphoe\@
    .balign 4, 0
.Lpho\@:
    Move 69, 1
    MoveEnd
.Lphoe\@:
    .endm
    .macro pl_ShowObject actor
    ActorCmdExec \actor, .Lpso\@
    ActorCmdWait
    VMJump .Lpsoe\@
    .balign 4, 0
.Lpso\@:
    Move 70, 1
    MoveEnd
.Lpsoe\@:
    .endm

// ---- items, Pokémon, money ---------------------------------------------------------------------------------------
    .macro pl_AddItem item, count, var     // 0x7B (silent, as Pearl's; var = 1 added)
    ItemAdd \item, \count, \var
    .endm
    .macro pl_RemoveItem item, count, var  // 0x7C
    ItemSub \item, \count, \var
    .endm
    .macro pl_CanFitItem item, count, var  // 0x7D
    ItemCheckSpace \item, \count, \var
    .endm
    .macro pl_CheckItem item, count, var   // 0x7E
    ItemCheckAmount \item, \count, \var
    .endm
    .macro pl_GetItemPocket item, var      // 0x80: Black 2's pocket -> Pearl's number (above)
    ItemGetPocket \item, \var
    WorkCmpConst \var, 2                   // TMs
    VMJumpIf CMP_NE, .Lpgp2\@
    WorkSetConst \var, 3
    VMJump .Lpgpe\@
.Lpgp2\@:
    WorkCmpConst \var, 3                   // berries
    VMJumpIf CMP_NE, .Lpgp3\@
    WorkSetConst \var, 4
    VMJump .Lpgpe\@
.Lpgp3\@:
    WorkCmpConst \var, 4                   // key items
    VMJumpIf CMP_NE, .Lpgp4\@
    WorkSetConst \var, 7
    VMJump .Lpgpe\@
.Lpgp4\@:
    WorkCmpConst \var, 5                   // (Black 2's free-space pocket: none in Pearl)
    VMJumpIf CMP_LT, .Lpgpe\@
    WorkSetConst \var, 0
.Lpgpe\@:
    .endm
    .macro pl_GivePokemon species, level, item, var    // 0x96: form 0 (the held item is not given: Black 2's
    PokePartyAdd \var, \species, 0, \level             // PokePartyAdd has none); flag 2401 = Black 2's "has a
    FlagSet 2401                                       // Pokemon" (set right after its own starter)
    .endm
    .macro pl_GetPartyCount var            // 0x177
    PokePartyGetCount \var, 0
    .endm
    .macro pl_HealParty                    // 0x14E (pokediamond HealParty)
    PokePartyRecoverAll
    .endm
    .macro pl_GiveMoney amount             // 0x6F (16 bits: pearl_story.py splits larger amounts)
    MoneyAdd \amount
    .endm
    .macro pl_RemoveMoney amount           // 0x70
    MoneySub \amount
    .endm
    .macro pl_GiveRunningShoes             // 0x15A: Black 2's own (flag 2403)
    GiveRunningShoes
    .endm
    .macro pl_GivePokedex                  // 0x158: Black 2's Pokedex, and flag 2402, which shows it in the start menu
    PokeDexEnable                          // (ov162 startmenu.c; Black 2's own scene sets it: aspertia_city.s)
    FlagSet 2402
    .endm

// ---- battles -------------------------------------------------------------------------------------------------------
    .macro pl_StartWildBattle species, level   // 0x124: a scripted wild battle
    CallWildBattle \species, \level, 0
    .endm
    .macro pl_StartTrainerBattle id1, id2  // 0xE5: Black 2 trainer ids (b2tools/pearl_story.py trainer registry)
    CallTrainerBattle \id1, \id2, 0
    .endm
    .macro pl_StartTagBattle partner, id1, id2 // 0x2A0: you and a partner trainer against two (Black 2's multi
    CallTrainerMultiBattle \partner, \id1, \id2, 0     // battle, as its Lacunosa scene; pl_CheckWonBattle after it)
    .endm
    .macro pl_PlayTrainerEncounterBGM id   // 0xEA: the trainer class's encounter music (patches/battle_music.py)
    TrainerBGMPlay \id
    .endm
    .macro pl_CheckWonBattle var           // 0xEC: var = 1 won; on a win Black 2 needs its battle end (the field again)
    TrainerBattleIsVictory \var
    WorkCmpConst \var, 1
    VMJumpIf CMP_NE, .Lpwb\@
    CallTrainerBattleEnd
.Lpwb\@:
    .endm
    .macro pl_CheckWonWildBattle var       // Pearl's CheckWonBattle after a wild battle
    WildBattleIsVictory \var
    WorkCmpConst \var, 1
    VMJumpIf CMP_NE, .Lpww\@
    CallWildBattleEnd
.Lpww\@:
    .endm
    .macro pl_BlackOutFromBattle           // 0xEB (after a lost trainer battle)
    CallTrainerLose
    .endm
    .macro pl_BlackOutFromWildBattle       // 0xEB after a lost wild battle
    CallWildLose
    .endm
    .macro pl_CheckLostBattle var          // 0xED after a wild (legendary) battle: var = 1 if it ended without a win
    WildBattleGetResult \var              // or a catch (fled, a draw). Black 2's result (ov012 GetWildBattleResult-
    WorkCmpConst \var, 1                  // ByCombined): 0 caught, 1 fled / draw / defeat, 2 knocked out
    VMJumpIf CMP_EQ, .Lpcl\@
    WorkSetConst \var, 0
.Lpcl\@:
    .endm
    .macro pl_CheckDidNotCapture var       // 0x2BC after a wild (legendary) battle: var = 1 if the Pokémon was not
    WildBattleGetResult \var              // caught. Black 2's result (ov012 GetWildBattleResultByCombined): 0 caught,
    WorkCmpConst \var, 0                  // 1 fled / draw / defeat, 2 knocked out (won)
    VMJumpIf CMP_EQ, .Lpdc\@
    WorkSetConst \var, 1
.Lpdc\@:
    .endm

// ---- stubs -------------------------------------------------------------------------------------------------------
// A Pearl command with no translation yet becomes `pl_stub` with its Pearl name: no code, listed per file in
// work/pearl/b2_scripts/report.txt and notes/STORY.md (never dropped silently).
    .macro pl_stub name
    .endm

// ---- doors (Pearl's door animations -> Black 2's building-model handles, ov036 scrcmd_buildmodel.c) -------------
// Pearl LoadDoorAnimation cellX, cellZ, tileX, tileZ, tag: a handle on the door prop at that tile, kept in a work per
// tag (PL_DOOR); prop kind 1 = a door (Black 2's own doors: aspertia_city.s). With no animated door there (Pearl's
// doors are plain models until the map converter gives them Black 2's door animation) the handle is 0 and the other
// commands do nothing (FieldPropSystem_GetHandleID / FindHandleByID are null-safe; BMHndAnmWait ends at once).
#define PL_DOOR(tag) (0x8048 + ((tag) & 15))
    .macro pl_LoadDoorAnimation tag, x, z
    BMCreateHandleByGPos PL_DOOR(\tag), 1, \x, \z
    .endm
    .macro pl_PlayDoorOpenAnimation tag
    BMHndAudioVisualAnmPlay PL_DOOR(\tag), 0
    .endm
    .macro pl_PlayDoorCloseAnimation tag
    BMHndAudioVisualAnmPlay PL_DOOR(\tag), 1
    .endm
    .macro pl_WaitForAnimation tag
    BMHndAnmWait PL_DOOR(\tag)
    .endm
    .macro pl_UnloadAnimation tag
    BMReleaseHandle PL_DOOR(\tag)
    .endm

    .macro pl_PlayHMCutIn slot             // Pearl's PlayHMCutIn: Black 2's own steps (its global 10000 L_005C, L_006C)
    PlayerSetSpecialSequence 128
    ActorCmdExec 255, 8f
    ActorCmdWait
    PlayHMCutInEffect \slot
    PlayerSetSpecialSequence 8
    VMJump 9f
    .balign 4, 0
8:
    Move 162, 1
    MoveEnd
9:
    .endm

// ---- more Pearl commands --------------------------------------------------------------------------------------------
    .macro pl_GetTimeOfDay var             // 0x1B6: Pearl 0 morning, 1 day, 2 evening, 3 night, 4 late night; Black 2's
    RTCGetDayPart \var                     // day period (GameData_GetDayPeriod) has the same five
    .endm
    .macro pl_GetNationalDex var           // 0x22D get
    PokeDexHaveNational \var
    .endm
    .macro pl_SetNationalDex               // 0x22D set
    PokeDexGiveNational
    .endm
    .macro pl_GetLocalDexSeenCount var     // 0x11E CountSinnohDexSeen: the regional (Sinnoh) list's seen count
    pl_DexSinnohSeen \var, 0               // (Pokédex macros at the end of this file)
    .endm
    .macro pl_GetPartyMonSpecies slot, var // 0x198
    // Gen 4 gives 0 for an Egg (pokediamond and pokeplatinum scrcmd_party.c); Black 2's command gives SPECIES_EGG (650),
    // so the scripts' "is it an Egg" test (species 0: the Move Deleter, the Day Care, Wilma ...) never fired (1.0.1)
    PokePartyGetSpecies \var, \slot
    WorkCmpConst \var, 650                 // SPECIES_EGG (generated/species.txt)
    VMJumpIf CMP_NE, .Lgpms\@
    WorkSetConst \var, 0
.Lgpms\@:
    .endm
    .macro pl_CountPartyNonEggs var        // 0x19A
    PokePartyGetCount \var, 1
    .endm
    .macro pl_CheckPartyPokerus var        // 0x119
    PokePartyCheckPokerus \var
    .endm
    .macro pl_PlayPokecenterHealingAnimation count   // 0x23B: Black 2's Pokemon Center machine (balls = party count)
    PokecenPlayHealingSequence \count
    .endm
    .macro pl_OpenPokemonNamingScreen slot, var  // 0xBB: Black 2's nickname screen (as HoennB2 h_name_received_mon)
    MsgWinCloseAll
    FadeOutBlackQ
    FadeWait
    CallPokeNameInput \var, \slot, 0
    FadeInBlackQ
    FadeWait
    .endm
    .macro pl_CheckBadgeAcquired badge, var    // 0x15B (badge 0-7 in both)
    TrainerCardHasBadge \var, \badge
    .endm
    .macro pl_GiveBadge badge                  // 0x15C: Black 2's badge, its per-badge flag 2414+ and the party record
    TrainerCardSaveGymVictoryParty \badge      // (as every Black 2 gym; HoennB2 h_givebadge)
    TrainerCardAddBadge \badge
    FlagSet (2414 + \badge)
    .endm
    .macro pl_CountBadgesAcquired var          // 0x15D
    TrainerCardGetBadgeCount \var
    .endm
    // Pearl's Marts (0x147 PokeMartCommon, 0x148 SpecialMart): Black 2's Mart menu (global 10110: Buy / Sell, as Black 2's
    // Centers call it; its first line Pearl's greeting, a/0/0/3 1302). Shop 255 is the badge Mart (ov036
    // SHOP_ID_BADGE_MART, Pearl's six lists in list files 0-5), shop n reads list file n + 6 (Pearl's SpecialMart n):
    // patches/pearl_shops.py
    .macro pl_mart shop
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSet 0x8000, \shop
    WorkSet 0x8001, 0                      // (1 would say Black 2's "Hello!" first: Pearl's clerk doesn't)
    RTCallGlobal 10110
    VMStackPop 0x8001
    VMStackPop 0x8000
    .endm
    .macro pl_PokeMartCommon var
    pl_mart 255
    .endm
    .macro pl_PokeMartSpecial shop
    pl_mart \shop
    .endm
    // Pearl's CheckItemIsPlate (Flame Plate 298 .. Iron Plate 313: pokediamond ItemIdIsPlate)
    .macro pl_CheckItemIsPlate item, var
    WorkSetConst \var, 0
    WorkCmpConst \item, 298
    VMJumpIf CMP_LT, .Lpcip\@
    WorkCmpConst \item, 313
    VMJumpIf CMP_GT, .Lpcip\@
    WorkSetConst \var, 1
.Lpcip\@:
    .endm

// ---- the follower (Pearl: SetMovementType X, 0x30 + SetObjectFlagIsPersistent; Black 2: ov012 pair_sys.c) ----------
// Black 2's follower: ActorPairSet makes the NPC follow (move code 0x30) and renames it 0xFE (Pearl's own id for the
// follower after EventStopFollowing; Pearl's 0xF2 = the object that follows: both are PL_FOLLOWER), persistent across
// zone changes (Pearl's SetObjectFlagIsPersistent 1), with its own script; flag 0x966 is set while it follows. The same
// steps as Black 2's global scripts 10535 (start) / 10536 (end). During a script every actor is paused (LockAll), the
// follower too, and the script moves it with ActorCmdExec as any NPC (Black 2's ActorPairSetMoveEnable 1 is for the
// opposite: letting it follow while the script walks the player; Pearl's scenes move both themselves).
#define PL_FOLLOWER 0xFE
#define PL_FOLLOW_FLAG 0x966
    .macro pl_follow_start uid             // follow the player (Pearl gives the movement type again after a scene:
    FlagGet PL_FOLLOW_FLAG, PL_TMP         // already following, nothing to do)
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Lpfs\@
    ActorPairSet \uid, 0, 1, 0, 0          // follower slot 0, persistent, no partner trainer, keeps its own script
    Cmd_022E 254                           // (as global 10535)
.Lpfs\@:
    .endm
    .macro pl_follow_start_ally uid, trainer, keep  // follow and battle at your side (Pearl's partner var 0x403F
    FlagGet PL_FOLLOW_FLAG, PL_TMP         // + SetHasPartner: Cheryl): Black 2's follower with an ally trainer, so
    WorkCmpConst PL_TMP, 1                 // two trainers who see you are a multi battle with it (ov036
    VMJumpIf CMP_EQ, .Lpfa\@               // event_trainer_eye: GetNowFollowerAllyTrID) and wild battles a wild
    ActorPairSet \uid, 0, \keep, \trainer, 0  // multi battle (field_encount.c pairActive). keep 0: only in this
                                           // zone (ActorPairEnd gives it back its id; a warp ends the following)
    Cmd_022E 254
.Lpfa\@:
    .endm
    .macro pl_follow_hold uid, move        // Pearl gives the follower another movement type for a scene: while it
    FlagGet PL_FOLLOW_FLAG, PL_TMP         // follows, Black 2's script moves it anyway (paused); else the NPC's code
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Lpfh\@
    ActorSetMoveCode \uid, \move
.Lpfh\@:
    .endm
    .macro pl_follow_hold_any              // (Pearl's partner flag off for a scene: nothing to do while paused)
    .endm
    .macro pl_follow_end                   // stops following and stays as an NPC (Pearl SetObjectFlagIsPersistent X, 0)
    FlagGet PL_FOLLOW_FLAG, PL_TMP
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Lpfe\@
    ActorPairEnd 0, 0
.Lpfe\@:
    .endm
    .macro pl_follow_leave                 // stops following and leaves the map (the scene has its own copy of the NPC)
    FlagGet PL_FOLLOW_FLAG, PL_TMP
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Lpfl\@
    ActorPairEnd 0, 0
    ActorDelete PL_FOLLOWER
.Lpfl\@:
    .endm
    .macro pl_SetPositionF uid, x, y, z, dir   // (plat-test) an object that may be the follower now: placed as it
    FlagGet PL_FOLLOW_FLAG, PL_TMP             // (Amity Square's walking Pokemon out of the other hut)
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Lpsf\@
    ActorSetGPos \uid, \x, \y, \z, \dir
    VMJump .Lpsfb\@
.Lpsf\@:
    ActorSetGPos PL_FOLLOWER, \x, \y, \z, \dir
.Lpsfb\@:
    .endm
    .macro pl_ApplyMovementF uid, list     // an object that may be the follower now (Black 2 renamed it 0xFE)
    FlagGet PL_FOLLOW_FLAG, PL_TMP
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Lpam\@
    ActorCmdExec \uid, \list
    VMJump .Lpamb\@
.Lpam\@:
    ActorCmdExec PL_FOLLOWER, \list
.Lpamb\@:
    .endm

// ---- Amity Square (Pearl script file 266; pokediamond scrcmd_amity_square.c; 2026-10-25) -------------------------
// Pearl counts every step in a saved var (pokeplatinum field_control.c SystemVars_IncrementAmitySquareStepCount, up to
// 10000); the square clears it when the walk starts and after each find, and reads it when you talk to the follower
// (a find from 200 steps on). Black 2's own saved step counter does the same (ov012 scrcmd_pedometer.c: PedometerStart
// starts it at 0 when it is off, PedometerEnd turns it off, PedometerGet reads it; it counts up to 9999; Fly, Teleport,
// the Escape Rope and a black-out turn it off, none of which can happen with a follower).
    .macro pl_ClearAmitySquareStepCount    // 0x215
    PedometerEnd
    PedometerStart
    .endm
    .macro pl_GetAmitySquareStepCount var  // 0x216
    PedometerGet \var
    .endm
// 0x217 CalcAmitySquareFoundAccessory: Pearl picks the next find's Accessory from a table per species (4 finds in 5;
// the other is one of Pearl's Berries): pl_AmityAccessory, Super Contests' Fashion Case (the user, 2026-11-01).

// ---- the briefcase and the first battle (Black 2's starter screen, as its Aspertia scene: aspertia_city.s) --------
// Pearl: StartChooseStarterScene (0xB4) opens the briefcase, SaveChosenStarter (0xB5) keeps the species (Pearl's var
// 0x4030; index 0/1/2 = Turtwig/Chimchar/Piplup, pokediamond overlay 64), ReturnToField (0xA1), then a fade in.
// Black 2: callPoke3Select gives 0/1/2 = the left/middle/right ball, which patches/pearl_starters.py makes Turtwig,
// Chimchar, Piplup. Black 2 keeps the index in work 0x4030 (its own code reads it); PVAR_STARTER holds the species.
#define PL_STARTER_INDEX 0x8042
    .macro pl_StartChooseStarterScene
    WorkSetConst PL_STARTER_INDEX, 0
    FieldClose
    callPoke3Select PL_STARTER_INDEX
    .endm
    .macro pl_SaveChosenStarter
    WorkSet 0x4030, PL_STARTER_INDEX
    WorkSetConst PVAR_STARTER, SPECIES_TURTWIG
    Cmd_0209 8, 3                          // (Black 2's survey answer: grass 3, fire 1, water 2)
    WorkCmpConst PL_STARTER_INDEX, 1
    VMJumpIf CMP_NE, .Lpss\@
    WorkSetConst PVAR_STARTER, SPECIES_CHIMCHAR
    Cmd_0209 8, 1
.Lpss\@:
    WorkCmpConst PL_STARTER_INDEX, 2
    VMJumpIf CMP_NE, .Lpss2\@
    WorkSetConst PVAR_STARTER, SPECIES_PIPLUP
    Cmd_0209 8, 2
.Lpss2\@:
    .endm
// Pearl's party select (0x191 ChoosePokemonMenu, 0x193 GetSelectedPartySlot; pearl_story poke_select_fades): Black 2's
// CallPokeSelect (ov036 s0107: flag 0 = the plain party list; picked = 1 when a Pokemon was chosen, index = its slot;
// ov020 EventPokeSelect_Callback fades, closes and reopens the field itself). Pearl's slot is 0xFF when cancelled.
#define PL_PSEL_PICKED 0x8044
#define PL_PSEL_SLOT 0x8045
    .macro pl_ChoosePokemonMenu
    CallPokeSelect 0, PL_PSEL_PICKED, PL_PSEL_SLOT, 0
    .endm
    .macro pl_GetSelectedPartySlot var
    WorkSet \var, PL_PSEL_SLOT
    WorkCmpConst PL_PSEL_PICKED, 1
    VMJumpIf CMP_EQ, .Lpgsps\@
    WorkSetConst \var, 255
.Lpgsps\@:
    .endm
    .macro pl_ReturnToField                // 0xA1
    FieldOpen
    .endm
    .macro pl_fade_in_after_starter        // Black 2's starter screen leaves the screens white (psel.c PselProc_Exit)
    FadeInWhiteQ
    .endm
    // Pearl FirstBattle species, level (0x125: a wild battle with no loss branch in Pearl's script). Here a wild battle;
    // a loss heals the party and the scene goes on (as Black 2's first Hugh battle; a whiteout would replay the lake and
    // give a second starter: notes/STORY.md question). Pearl's map script removes the Starly when the field reloads.
    .macro pl_StartFirstBattle species, level
    pl_ext 0xA0                            // Pearl's first-battle rules on: no critical hits, FIGHT only
    .2byte 1                               // (resident/leftovers.c PearlB2_IsFirstBattle)
    CallWildBattle \species, \level, 0
    WildBattleIsVictory PL_TMP
    pl_ext 0xA0
    .2byte 0
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Lpfb\@
    PokePartyRecoverAll
.Lpfb\@:
    CallWildBattleEnd
    .endm
    // Platinum's first battle (0x125 with one argument: the rival, by the starter): a Trainer battle with the same first-battle rules.
    // plat-ch1 (2026-11-07): as Black 2's own first battle (aspertia_city.s, Hugh): flags 1 (ov012 EventTrainerBattleCall_Create:
    // setup flag 0x100, no loss text and no money lost; no black-out), and CallTrainerBattleEnd win or lose. Platinum's script
    // restarts the field itself after a loss (ReturnToField, FadeScreen in): the generator drops those (pearl_story
    // first_battle_flow), and its CheckWonBattle only reads the result (pl_CheckWonFirstBattle).
    .macro pl_StartFirstTrainerBattle id
    pl_ext 0xA0
    .2byte 1
    CallTrainerBattle \id, 0, 1
    pl_ext 0xA0
    .2byte 0
    CallTrainerBattleEnd
    .endm
    .macro pl_CheckWonFirstBattle var      // plat-ch1: 0xEC after pl_StartFirstTrainerBattle: var = 1 won, 0 lost
    TrainerBattleIsVictory \var
    .endm
    // Pearl StartCatchingTutorial (0x126: the counterpart's starter Lv 5 catches a Bidoof Lv 2, pokeplatinum
    // FieldBattleDTO_NewCatchingTutorial): Black 2's capture demo as Black 2's Route 19 scene (CallCaptureDemo then
    // CallWildBattleEnd), made Pearl's by patches/capture_demo.py (Pokémon, moves, back picture, lines)
    .macro pl_StartCatchingTutorial
    CallCaptureDemo
    CallWildBattleEnd
    .endm
#define PL_STEP_FLAG 0x51              // Pearl's "step" flag (sys flag 0x965) as a map-local flag (see pearl_story.py)
    .macro pl_GetFirstNonEggInParty var    // 0x247: the first party slot that is not an Egg (HoennB2 h_get_lead_mon)
    WorkSetConst \var, 0
.Lpln\@:
    PokePartyIsEgg PL_TMP, \var
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lpln2\@
    WorkAdd \var, 1
    VMJump .Lpln\@
.Lpln2\@:
    .endm

// ---- the Pokédex: counts and the professors' ratings (2026-10-20) ---------------------------------------------------
// Black 2's regional list is Pearl's Sinnoh #1-#151 (patches/sinnoh_dex.py: Victini kept as the hidden #000). Black 2's
// regional counts (PokeDexGetEvaluationParams 2/3: PokeDex_GetSeenNoUnova / GetCaughtNoUnova) count Victini too; Pearl's
// (pokediamond arm9/src/pokedex.c) count the 151 Sinnoh species, and its "omit mythicals" counts leave out Manaphy
// (Sinnoh) or Mew, Lugia, Ho-Oh, Celebi, Jirachi, Deoxys, Phione, Manaphy, Darkrai, Shaymin, Arceus (National).
// Pearl's "Sinnoh Pokédex complete" (CheckLocalDexCompleted) = PokeDexIsComplete 2 (sinnoh_dex: seen without Manaphy
// >= 150, Pearl's Pokedex_SinnohDexIsComplete).
#define PL_DEX 0x8043          // the Pokédex macros' count (never a Pearl var)
    .macro pl_DexSinnohSeen var, nomyth    // Pearl Pokedex_CountSinnohDexSeen (nomyth 1: _OmitMythicals)
    PokeDexGetEvaluationParams 2, PL_TMP, \var, PL_TMP
    PokeDexIsRegist 0, SPECIES_VICTINI, PL_TMP
    WorkSub \var, PL_TMP
    .if \nomyth
    PokeDexIsRegist 0, SPECIES_MANAPHY, PL_TMP
    WorkSub \var, PL_TMP
    .endif
    .endm
    .macro pl_DexNationalCaughtNoMythical var  // Pearl Pokedex_CountNationalDexOwned_OmitMythicals (Black 2 counts 1-649)
    PokeDexGetCount 1, \var
    .irp sp, SPECIES_MEW, SPECIES_LUGIA, SPECIES_HO_OH, SPECIES_CELEBI, SPECIES_JIRACHI, SPECIES_DEOXYS, SPECIES_PHIONE, SPECIES_MANAPHY, SPECIES_DARKRAI, SPECIES_SHAYMIN, SPECIES_ARCEUS
    PokeDexIsRegist 1, \sp, PL_TMP
    WorkSub \var, PL_TMP
    .endr
    .endm
    .macro pl_GetNationalDexSeenCount var  // 0x120 CountNationalDexSeen
    PokeDexGetCount 0, \var
    .endm
    .macro pl_GetNationalDexCaughtCount var    // 0x121 CountNationalDexOwned
    PokeDexGetCount 1, \var
    .endm
    .macro pl_CheckLocalDexCompleted var   // 0x1E8 CheckSinnohDexComplete
    PokeDexIsComplete \var, 2
    .endm
    .macro pl_CheckLocalDexCompletedOrChampion var  // 0x1E8 where it gates Oak's National Pokédex: 1 also once the
    FlagGet 2400, \var                     // game-clear flag is set (user 2026-10-26: the National Pokédex at
    WorkCmpConst \var, 1                   // Champion; pearl_story NATIONAL_DEX_AT_CHAMPION)
    VMJumpIf CMP_EQ, .Lpcsc\@
    PokeDexIsComplete \var, 2
.Lpcsc\@:
    .endm
    // a step of the rating chains below: the count is at least `min` -> var = line
    .macro pl_dex_tier var, min, line, done
    WorkCmpConst PL_DEX, \min
    VMJumpIf CMP_LT, \done
    WorkSetConst \var, \line
    .endm
    // 0x123 LoadPokedexRating 0, var (Rowan; pokediamond ScrCmd_GetDexEvaluationMessage -> sub_02054CC8): var = the
    // line for the Sinnoh seen count without Manaphy: up to 14 / 24 / 39 / 59 / 89 / 114 / 134 / 144 / 149 -> Pearl's bank
    // 335 lines 6-14; all 150 -> line 4 when Pearl's flag 0x9BA is set, else 5. l4..l14: those lines' numbers in the
    // calling script's own text file (MessageVar prints var).
    .macro pl_LoadPokedexRatingLocal var, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14
    pl_DexSinnohSeen PL_DEX, 1
    WorkSetConst \var, \l6
    pl_dex_tier \var, 15, \l7, .Lpdr\@
    pl_dex_tier \var, 25, \l8, .Lpdr\@
    pl_dex_tier \var, 40, \l9, .Lpdr\@
    pl_dex_tier \var, 60, \l10, .Lpdr\@
    pl_dex_tier \var, 90, \l11, .Lpdr\@
    pl_dex_tier \var, 115, \l12, .Lpdr\@
    pl_dex_tier \var, 135, \l13, .Lpdr\@
    pl_dex_tier \var, 145, \l14, .Lpdr\@
    pl_dex_tier \var, 150, \l5, .Lpdr\@
    FlagGet PFLAG_09BA, PL_TMP
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Lpdr\@
    WorkSetConst \var, \l4
.Lpdr\@:
    .endm
    // 0x123 LoadPokedexRating 1, var (Oak; sub_02054D1C): the National caught count without Pearl's 11 mythicals: up to
    // 39 / 59 / 89 / 119 / 149 / 189 / 229 / 269 / 309 / 349 / 379 / 409 / 429 / 449 / 459 / 469 / 475 / 481 -> lines
    // 19-37 (429: 31 for a boy, 32 for a girl); 482 -> 38 boy / 39 girl (the same words). l19..l39: the lines' numbers.
    .macro pl_LoadPokedexRatingNational var, l19, l20, l21, l22, l23, l24, l25, l26, l27, l28, l29, l30, l31, l32, l33, l34, l35, l36, l37, l38, l39
    pl_DexNationalCaughtNoMythical PL_DEX
    TrainerCardGetSex PL_TMP2
    WorkSetConst \var, \l19
    pl_dex_tier \var, 40, \l20, .Lpdn\@
    pl_dex_tier \var, 60, \l21, .Lpdn\@
    pl_dex_tier \var, 90, \l22, .Lpdn\@
    pl_dex_tier \var, 120, \l23, .Lpdn\@
    pl_dex_tier \var, 150, \l24, .Lpdn\@
    pl_dex_tier \var, 190, \l25, .Lpdn\@
    pl_dex_tier \var, 230, \l26, .Lpdn\@
    pl_dex_tier \var, 270, \l27, .Lpdn\@
    pl_dex_tier \var, 310, \l28, .Lpdn\@
    pl_dex_tier \var, 350, \l29, .Lpdn\@
    pl_dex_tier \var, 380, \l30, .Lpdn\@
    pl_dex_tier \var, 410, \l31, .Lpdn\@
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lpdn1\@
    WorkSetConst \var, \l32
.Lpdn1\@:
    pl_dex_tier \var, 430, \l33, .Lpdn\@
    pl_dex_tier \var, 450, \l34, .Lpdn\@
    pl_dex_tier \var, 460, \l35, .Lpdn\@
    pl_dex_tier \var, 470, \l36, .Lpdn\@
    pl_dex_tier \var, 476, \l37, .Lpdn\@
    pl_dex_tier \var, 482, \l38, .Lpdn\@
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lpdn\@
    WorkSetConst \var, \l39
.Lpdn\@:
    .endm
    // ---- plat-fixes (2026-11-07): Platinum's Rowan (pearl_story h_dex_rating, version.DEX_RATING). 0x123
    // LoadPokedexRating 0, var in Platinum (pokeplatinum Pokedex_GetRatingMessageID_Local): the Sinnoh seen count with
    // nothing left out (Platinum's LOCAL_DEX_GOAL is all 210): up to 15 / 30 / 45 / 60 / 80 / 100 / 120 / 140 / 160 / 180 /
    // 200 / 209 -> Platinum's bank 335 lines 6-17; all 210 -> line 4 once the player has been to Eterna
    // (FIRST_ARRIVAL_ETERNA_CITY, flag 0x9BA as in Pearl), else line 5. l4..l17: those lines' numbers in the calling
    // script's own text file. Oak's tiers are Pearl's (pl_LoadPokedexRatingNational, Platinum's lines 22-42).
    .macro pl_LoadPokedexRatingLocalPlatinum var, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16, l17
    pl_DexSinnohSeen PL_DEX, 0
    WorkSetConst \var, \l6
    pl_dex_tier \var, 16, \l7, .Lpdp\@
    pl_dex_tier \var, 31, \l8, .Lpdp\@
    pl_dex_tier \var, 46, \l9, .Lpdp\@
    pl_dex_tier \var, 61, \l10, .Lpdp\@
    pl_dex_tier \var, 81, \l11, .Lpdp\@
    pl_dex_tier \var, 101, \l12, .Lpdp\@
    pl_dex_tier \var, 121, \l13, .Lpdp\@
    pl_dex_tier \var, 141, \l14, .Lpdp\@
    pl_dex_tier \var, 161, \l15, .Lpdp\@
    pl_dex_tier \var, 181, \l16, .Lpdp\@
    pl_dex_tier \var, 201, \l17, .Lpdp\@
    pl_dex_tier \var, 210, \l5, .Lpdp\@
    FlagGet PFLAG_09BA, PL_TMP
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Lpdp\@
    WorkSetConst \var, \l4
.Lpdp\@:
    .endm
    // ---- end plat-fixes

// ---- closed places (data/pearl_closed_facilities.json, b2tools/pearl_story.py CLOSED; 2026-10-25, chapters 4a/5a)
// A place Pearl has and this game does not build yet (the Contest counters, Amity Square, the Great Marsh): a short
// line in the plain window, then the player takes one step in direction `dir` (Pearl's 0 up, 1 down, 2 left, 3 right:
// WALK_NORMAL_NORTH 12 + dir in both games); dir 4 or more: no step (a person or sign talked to).
    .macro pl_closed_facility line, dir
    pl_LockAll
    pl_msg_sys \line
    pl_WaitButton
    pl_CloseMessage
    .if \dir < 4
    pl_ApplyMovement PL_PLAYER, .Lpcf_step\@
    pl_WaitMovement
    VMJump .Lpcf_end\@
    .balign 4, 0
.Lpcf_step\@:
    Move 12 + \dir, 1
    MoveEnd
.Lpcf_end\@:
    .endif
    pl_ReleaseAll
    .endm

// ---- the post-game's events built in (2026-10-26, chapter 9a; DECISIONS 2026-10-25) ------------------------------
// The deliveryman: Pearl's Mystery Gift man (globals 10200 / 10201 in every Pokémart, pearl_story h_mystery_gift)
// gives Pearl's four event gifts after the Hall of Fame (Black 2's game clear 2400 = Pearl's 0x964), one a talk, in
// the user's order: 0 the Member Card (454: Darkrai), 1 Oak's Letter (452: Shaymin), 2 the Azure Flute (455:
// Arceus), 3 the Manaphy Egg (490). PVAR_DELIVERY = how many were given; his map script hides him once all are given.
// Platinum (2026-11-02, plat-rooms): the Secret Key (467: Rotom's Room in the Team Galactic Eterna Building), Platinum's
// own distribution event 3, given last. Platinum (2026-11-07, plat-story; the user's choice of 2026-11-03): before it, 4
// an event Regigigas, the one the Regi ruins ask for (pl_CheckPartyHasFatefulEncounterRegigigas): the real 2009 event's
// (Toys "R" Us, 8-21 March 2009, before Platinum came out; the Secret Key's came later), made by Black 2's Mystery Gift
// maker (patches/platinum_regigigas.py, PearlB2 extension 0xBF). So 6 gifts (PL_DELIVERY_GIFTS), the Key 5.
// Pearl and Diamond (1.0.1, v101-story; version.POKETCH_APP_GIFTS): after the four, 4-6 the Pokétch apps no story script
// gives, Matchup Checker, Stopwatch and Alarm Clock (apps 22, 23, 24): Pearl's own Mystery Gift has a Pokétch-app gift
// (pokediamond scrcmd_12.s UNK_020F43E4's eleventh row: sub_020437DC asks for the Pokétch, sub_020437F8 registers the app;
// its line, bank 332 line 18, "received the Pokétch app ...!"). So 7 gifts.
// Platinum (plat-stubs, 2026-11-08; version.POKETCH_APP_GIFTS): after the Secret Key, 6-7 the Stopwatch and the Alarm Clock
// (apps 23, 24), which only its Mystery Gift gives (its Matchup Checker is the Great Marsh's): its line 19. So 8 gifts.
// (postdex, 2026-11-09; the user: notes/POSTGAME_DEX.md) Then, all three versions, the event Pokémon Mew, Celebi,
// Jirachi and Deoxys (version.EVENT_GIFTS, data/event_gifts.json: real Gen 4-era events, made by Black 2's Mystery Gift
// maker, PearlB2 extension 0xA9, patches/event_gifts.py), one a talk, each with room in the party: Pearl's and Diamond's
// gifts 7-10, Platinum's 8-11 (PL_DELIVERY_EVENTS), "received <species>!" (bank 332 line 7, the species in word 1).
#if PEARLB2_GAME_VERSION == 12
#define PL_DELIVERY_EVENTS 8
#else
#define PL_DELIVERY_EVENTS 7
#endif
#define PL_DELIVERY_GIFTS (PL_DELIVERY_EVENTS + 4)
    .macro pl_DeliveryEventSpecies         // word 1 = the event Pokémon of gift PVAR_DELIVERY (data/event_gifts.json's order)
    pl_BufferSpeciesName 1, 151            // Mew
    WorkCmpConst PVAR_DELIVERY, PL_DELIVERY_EVENTS + 1
    VMJumpIf CMP_LT, .Lpdes\@
    pl_BufferSpeciesName 1, 251            // Celebi
    WorkCmpConst PVAR_DELIVERY, PL_DELIVERY_EVENTS + 2
    VMJumpIf CMP_LT, .Lpdes\@
    pl_BufferSpeciesName 1, 385            // Jirachi
    WorkCmpConst PVAR_DELIVERY, PL_DELIVERY_EVENTS + 3
    VMJumpIf CMP_LT, .Lpdes\@
    pl_BufferSpeciesName 1, 386            // Deoxys
.Lpdes\@:
    .endm
    .macro pl_DeliveryWaiting var          // MysteryGiftGive 1: var = 1 after the Hall of Fame while gifts remain
    FlagGet 2400, \var
    WorkCmpConst PVAR_DELIVERY, PL_DELIVERY_GIFTS
    VMJumpIf CMP_LT, .Lpdw\@
    WorkSetConst \var, 0
.Lpdw\@:
    .endm
    .macro pl_DeliveryCanReceive var       // MysteryGiftGive 3: the Egg needs room in the party; key items always fit
    WorkSetConst \var, 1
    WorkCmpConst PVAR_DELIVERY, PL_DELIVERY_EVENTS     // (postdex) an event Pokémon: its name for line 7, room in the party
    VMJumpIf CMP_LT, .Lpdcv\@
    pl_DeliveryEventSpecies
    VMJump .Lpdcr\@
.Lpdcv\@:
#if PEARLB2_GAME_VERSION == 12
    pl_BufferSpeciesName 1, 486            // (plat-test) "received Regigigas!" (line 7) shows before pl_DeliveryGive
    WorkCmpConst PVAR_DELIVERY, 4          // (and Platinum's Regigigas)
    VMJumpIf CMP_EQ, .Lpdcp\@
#endif
    WorkCmpConst PVAR_DELIVERY, 3
    VMJumpIf CMP_NE, .Lpdc\@
#if PEARLB2_GAME_VERSION == 12
.Lpdcp\@:
#endif
.Lpdcr\@:
    PokePartyGetCount PL_TMP, 0
    WorkCmpConst PL_TMP, 6
    VMJumpIf CMP_LT, .Lpdc\@
    WorkSetConst \var, 0
.Lpdc\@:
    .endm
    .macro pl_DeliveryGive                 // MysteryGiftGive 4: the next gift into the Bag / the party
    WorkCmpConst PVAR_DELIVERY, PL_DELIVERY_EVENTS     // (postdex) an event Pokémon (extension 0xA9: index, result)
    VMJumpIf CMP_LT, .Lpdgv\@
    WorkSet PL_TMP2, PVAR_DELIVERY
    WorkSub PL_TMP2, PL_DELIVERY_EVENTS
    pl_ext 0xA9
    .2byte PL_TMP2
    .2byte PL_TMP
    VMJump .Lpdge\@
.Lpdgv\@:
    WorkCmpConst PVAR_DELIVERY, 0
    VMJumpIf CMP_NE, .Lpdg1\@
    ItemAdd 454, 1, PL_TMP                 // the Member Card
    VMJump .Lpdge\@
.Lpdg1\@:
    WorkCmpConst PVAR_DELIVERY, 1
    VMJumpIf CMP_NE, .Lpdg2\@
    ItemAdd 452, 1, PL_TMP                 // Oak's Letter
#if PEARLB2_GAME_VERSION == 12              // (plat-ch12) Platinum's InitShayminEvent: VAR_SHAYMIN_EVENT_STATE 0 -> 1, so
    WorkCmpConst PVAR_4057, 0              // Route 224's on-transition makes it 2 and Marley's step trigger comes
    VMJumpIf CMP_NE, .Lpdge\@              // (pokeplatinum scrcmd_mystery_gift.c)
    WorkSetConst PVAR_4057, 1
#endif
    VMJump .Lpdge\@
.Lpdg2\@:
    WorkCmpConst PVAR_DELIVERY, 2
    VMJumpIf CMP_NE, .Lpdg3\@
    ItemAdd 455, 1, PL_TMP                 // the Azure Flute
    VMJump .Lpdge\@
.Lpdg3\@:
    WorkCmpConst PVAR_DELIVERY, 3          // (v101-story: Pearl and Diamond compare too, apps follow)
    VMJumpIf CMP_NE, .Lpdg4\@
    PokePartyAddEgg PL_TMP, 490, 0         // the Manaphy Egg (Pearl: the Pokémon Ranger's gift)
#if PEARLB2_GAME_VERSION != 12
    VMJump .Lpdge\@
.Lpdg4\@:                                  // (v101-story) 4-6: the Pokétch apps 22-24 (Pearl's Mystery Gift app gift)
    WorkSet PL_TMP, PVAR_DELIVERY
    WorkAdd PL_TMP, 18
    pl_RegisterPoketchApp PL_TMP
#endif
#if PEARLB2_GAME_VERSION == 12
    VMJump .Lpdge\@
.Lpdg4\@:
    WorkCmpConst PVAR_DELIVERY, 4
    VMJumpIf CMP_NE, .Lpdg5\@
    pl_ext 0xBF                            // the event Regigigas into the party (patches/platinum_regigigas.py)
    .2byte PL_TMP
    pl_BufferSpeciesName 1, 486            // for "received Regigigas!" (the bank's line 7)
    VMJump .Lpdge\@
.Lpdg5\@:
    WorkCmpConst PVAR_DELIVERY, 5
    VMJumpIf CMP_NE, .Lpdg6\@
    ItemAdd 467, 1, PL_TMP                 // the Secret Key (Platinum's Rotom event)
    VMJump .Lpdge\@
.Lpdg6\@:                                  // (plat-stubs) 6-7: the Pokétch apps 23-24 (Platinum's Mystery Gift app gift)
    WorkSet PL_TMP, PVAR_DELIVERY
    WorkAdd PL_TMP, 17
    pl_RegisterPoketchApp PL_TMP
#endif
.Lpdge\@:
    WorkAdd PVAR_DELIVERY, 1
    .endm
    .macro pl_CheckDistributionEvent event, var  // Pearl 0x28B: var = 1 once the deliveryman gave the event's item
    WorkSetConst \var, 0                   // (event 0 Member Card, 1 Oak's Letter, 2 Azure Flute: his order;
#if PEARLB2_GAME_VERSION == 12              //  Platinum's event 3, Rotom's Secret Key, is his sixth gift: 5)
    .if \event == 3
    WorkCmpConst PVAR_DELIVERY, 5
    .else
    WorkCmpConst PVAR_DELIVERY, \event
    .endif
#else
    WorkCmpConst PVAR_DELIVERY, \event
#endif
    VMJumpIf CMP_LE, .Lpcde\@
    WorkSetConst \var, 1
.Lpcde\@:
    .endm
// Pearl's hidden places (SetHiddenLocation 2 the Spring Path, 3 the Seabreak Path): Black 2's map replacement events
// (ov012 map_replace.c EVENT_MAP_REPLACE_TABLE: uid 7 = work 0x4038 == 0x408, uid 9 = work 0x403A == 0x1028, the same
// number as Pearl's own Seabreak magic) swap the matrix cells (patches/pearl_hidden_paths.py writes a/0/1/0's entries)
#define PL_HIDDEN_EVENT_SPRING 7
#define PL_HIDDEN_EVENT_SEABREAK 9
    .macro pl_SetHiddenLocation place
    .if \place == 2                       // (set indoors: Rowan's lab, the Hall of Fame: nothing to reload)
    MapReplaceSetEvent PL_HIDDEN_EVENT_SPRING, 1, 0
    .elseif \place == 3                   // (on Route 224: matrix 0 reloaded with the path, as Black 2's own scripts)
    MapReplaceSetEvent PL_HIDDEN_EVENT_SEABREAK, 1, 1
    .endif
    .endm
    .macro pl_CheckHasAllLegendaryTitansInParty var  // Pearl 0x26B CheckRegis: Regirock, Regice, Registeel
    WorkSetConst \var, 0
    PokePartyFindBySpecies 377, PL_TMP, PL_TMP2
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Lpcr\@
    PokePartyFindBySpecies 378, PL_TMP, PL_TMP2
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Lpcr\@
    PokePartyFindBySpecies 379, PL_TMP, PL_TMP2
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Lpcr\@
    WorkSetConst \var, 1
.Lpcr\@:
    .endm
// Route 224's stone tablet (Pearl 0x271 / 0x272): Black 2's word-set name input (ov036 event_name_entry.c
// EventPokeNameWordSetInput: result 0 = cancelled or nothing typed, 1 / 2 = a name, into word buffer 1, which Pearl's
// "You most want to express your thanks to {1}?" reads), the player's starter as the screen's icon; var = 1 for
// "nothing written", as Pearl's
    .macro pl_OpenShayminTabletNamingScreen var
    MsgWinCloseAll
    CallWordSetPokeNameInput PVAR_STARTER, 1, \var
    WorkCmpConst \var, 0
    VMJumpIf CMP_EQ, .Lpts0\@
    WorkSetConst \var, 0
    VMJump .Lptse\@
.Lpts0\@:
    WorkSetConst \var, 1
.Lptse\@:
    .endm

// ---- the Day Care (2026-10-25, chapter 4b): Pearl's Day-Care Man and Lady (global scripts 9500/9501, file 464) on
// Black 2's own Day Care (ov012 scrcmd_sodateya.c, ov036 sodateya.c: the same save slots, compacted when one leaves;
// its egg comes by steps everywhere, as Pearl's). Pearl's semantics from pokediamond scrcmd_daycare.c / ov05.
#define PL_DC_SEX 0x8046                    // BufferDaycareNicknameLevelGender's gender (0 none, 1 male, 2 female)
    .macro pl_BufferDaycareMonNicknames        // 0x16D: buffer 0 the first Pokemon's nickname, 1 the second's (Pearl
    DayCareGetPkmCount PL_TMP                  // also puts the first's trainer in 2: no Pearl line shows it)
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lpbdn\@
    WordSetDaycarePokeName 0, 0
    WorkCmpConst PL_TMP, 2
    VMJumpIf CMP_NE, .Lpbdn\@
    WordSetDaycarePokeName 1, 1
.Lpbdn\@:
    .endm
    .macro pl_GetDaycareState var              // 0x16E: 1 an Egg waits, else 0 / 2 / 3 for 0 / 1 / 2 Pokemon
    DayCareCheckSpawnFlag PL_TMP
    WorkSetConst \var, 1
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lpgds\@
    DayCareGetPkmCount \var
    WorkCmpConst \var, 0
    VMJumpIf CMP_EQ, .Lpgds\@
    WorkAdd \var, 1
.Lpgds\@:
    .endm
    .macro pl_CheckDaycareHasEgg var           // 0x1BF: 1 when an Egg waits
    DayCareCheckSpawnFlag \var
    .endm
    .macro pl_GetDaycareCompatibilityLevel var // 0x1BE: Pearl's 0-3 from the egg chance 70 / 50 / 20 / 0 (Black 2's
    DayCareCalcEggSpawnChance PL_TMP           // 88 / 80 / 40 with the Oval Charm)
    WorkSetConst \var, 3
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lpgdc\@
    WorkSetConst \var, 2
    WorkCmpConst PL_TMP, 50
    VMJumpIf CMP_LT, .Lpgdc\@
    WorkSetConst \var, 1
    WorkCmpConst PL_TMP, 70
    VMJumpIf CMP_LT, .Lpgdc\@
    WorkCmpConst PL_TMP, 80
    VMJumpIf CMP_EQ, .Lpgdc\@
    WorkSetConst \var, 0
.Lpgdc\@:
    .endm
    .macro pl_CountAliveMonsAndBoxMons var     // 0x19C: party Pokemon able to battle + every Pokemon in the boxes
    PokePartyGetCount \var, 2
    BoxGetCount PL_TMP, 0
    WorkAdd \var, PL_TMP
    .endm
    .macro pl_CountAliveMonsExcept var, slot   // 0x19B: party Pokemon able to battle, not counting that slot's
    PokePartyGetCount \var, 2
    PokePartyIsEgg PL_TMP, \slot
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lpcame\@
    PokePartyGetParam PL_TMP, \slot, 160       // PKM_PARAM_HP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lpcame\@
    WorkSub \var, 1
.Lpcame\@:
    .endm
    .macro pl_OpenPartyMenuForDaycare var      // 0x290: Black 2's Day Care list (fades and reopens the field itself;
    DayCareCallPokeSelect PL_PSEL_SLOT         // its summary is in the list: Pearl's cursor var is not needed)
    .endm
    .macro pl_GetDayCarePartyMenuResult slot, summary   // 0x291: the slot (255 cancelled); no summary asked (0)
    WorkSetConst \summary, 0
    WorkSet \slot, PL_PSEL_SLOT
    PokePartyGetCount PL_TMP, 0
    WorkCmpWork PL_PSEL_SLOT, PL_TMP
    VMJumpIf CMP_LT, .Lpgdr\@
    WorkSetConst \slot, 255
.Lpgdr\@:
    .endm
    .macro pl_BufferPartyMonNicknameReturnSpecies slot, var   // 0x1AF: buffer 0 the party Pokemon's nickname
    WordSetPartyPokeName 0, \slot
    PokePartyGetSpecies \var, \slot
    .endm
    .macro pl_StorePartyMonIntoDaycare slot    // 0x1B0
    DayCareDeposit \slot
    .endm
    .macro pl_BufferDaycareGainedLevelsBySlot var, slot   // 0x1AE: levels gained; buffer 0 the nickname, 1 the number
    DayCareCalcLevelGain \var, \slot
    WordSetDaycarePokeName 0, \slot
    WordSetNumber 1, \var, 3
    .endm
    .macro pl_BufferDaycarePriceBySlot var, slot   // 0x1AA: the price; buffer 0 the nickname, 1 the price
    DayCareCalcWithdrawCost \var, \slot
    WordSetDaycarePokeName 0, \slot
    WordSetNumber 1, \var, 5
    .endm
    .macro pl_BufferDaycareNicknameLevelGender name, level, slot   // 0x1BC: the nickname, the level now; the gender
    WordSetDaycarePokeName \name, \slot        // in PL_DC_SEX (the menu line's copy with the symbol: pearl_story)
    DayCareCalcNewLevel PL_TMP, \slot
    WordSetNumber \level, PL_TMP, 3
    DayCareGetSexForNamePrint PL_DC_SEX, 0, \slot
    .endm
    .macro pl_MoveMonToPartyFromDaycareSlot var, slot   // 0x1A4: back to the party; buffer 0 the nickname, var the species
    DayCareGetSpecies \var, \slot
    WordSetDaycarePokeName 0, \slot
    DayCareWithdraw \slot
    .endm

// ---- the Solaceon News Press (2026-10-25, chapter 4b): Pearl's assignment is a random Pokemon the player has seen,
// to bring the same day (pokediamond ScrCmd_Unk0218-021A: a deadline counted in days in its save). Here the species by
// a walk over the Pokedex's seen flags (Pearl's own species, 1-493; Pearl takes its Sinnoh Pokedex's only, which is
// all a player sees before the National Pokedex), the day by PFLAG_NEWS_PRESS_TODAY (Black 2 clears it at midnight).
#define PL_TMP3 0x8047
    .macro pl_GetRandomSeenSpecies var         // 0x218: the r-th seen species, r random (Pikachu when none, as Pearl)
    WorkSetConst \var, 25
    PokeDexGetCount 0, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lpgrs_end\@
    Random PL_TMP2, PL_TMP
    WorkSetConst PL_TMP, 0
.Lpgrs_loop\@:
    WorkAdd PL_TMP, 1
    WorkCmpConst PL_TMP, 494
    VMJumpIf CMP_EQ, .Lpgrs_end\@
    PokeDexIsRegist 0, PL_TMP, PL_TMP3
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_EQ, .Lpgrs_loop\@
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lpgrs_found\@
    WorkSub PL_TMP2, 1
    VMJump .Lpgrs_loop\@
.Lpgrs_found\@:
    WorkSet \var, PL_TMP
.Lpgrs_end\@:
    .endm

// ---- plat-ch6 (2026-11-07): Platinum's chapter 6 (pearl_story.py block "plat-ch6"; Pearl's scripts use neither) ---------
    .macro pl_CheckHasSeenSpecies species, var  // 0x337: var = 1 if the Pokédex has seen it (Black 2's PokeDex_IsSeen)
    PokeDexIsRegist 0, \species, \var
    .endm
    // 0x264 CheckPartyCombeeGenderCount (pokeplatinum scrcmd.c): the party's Combee that aren't Eggs: 0 none, 1 of one
    // gender, 2 a male and a female. PL_TMP the slot, PL_TMP2 the party count, PL_TMP3 what is read; var gathers 1 for a
    // male and 2 for a female (Black 2's VM has no OR), then turns 3 into 2 and 2 into 1.
    .macro pl_CheckPartyCombeeGenderCount var
    WorkSetConst \var, 0
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lpcg_loop\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lpcg_end\@
    PokePartyIsEgg PL_TMP3, PL_TMP
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_NE, .Lpcg_next\@
    PokePartyGetParam PL_TMP3, PL_TMP, 5       // PKM_PARAM_SPECIES
    WorkCmpConst PL_TMP3, 415                   // SPECIES_COMBEE
    VMJumpIf CMP_NE, .Lpcg_next\@
    PokePartyGetParam PL_TMP3, PL_TMP, 0x6E    // PKM_PARAM_SEX: 0 male, 1 female, 2 none
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_EQ, .Lpcg_male\@
    WorkCmpConst PL_TMP3, 1
    VMJumpIf CMP_NE, .Lpcg_next\@
    WorkCmpConst \var, 2                        // a female: 0 -> 2, 1 -> 3
    VMJumpIf CMP_GE, .Lpcg_next\@
    WorkAdd \var, 2
    VMJump .Lpcg_next\@
.Lpcg_male\@:
    WorkCmpConst \var, 1                        // a male: 0 -> 1, 2 -> 3
    VMJumpIf CMP_EQ, .Lpcg_next\@
    WorkCmpConst \var, 3
    VMJumpIf CMP_EQ, .Lpcg_next\@
    WorkAdd \var, 1
.Lpcg_next\@:
    WorkAdd PL_TMP, 1
    VMJump .Lpcg_loop\@
.Lpcg_end\@:
    WorkCmpConst \var, 2
    VMJumpIf CMP_LT, .Lpcg_done\@
    WorkSub \var, 1                             // 2 (a female) -> 1, 3 (both) -> 2
.Lpcg_done\@:
    .endm
    // 0x264 in Pearl and Diamond is CheckBurmyForms (pokediamond scrcmd.c ScrCmd_CheckBurmyForms; 1.0.1): the number of
    // different Burmy forms in the party, 0-3 (Pearl reads no Egg flag, nor does this). One pass of the party per form
    // (Plant 0, Sandy 1, Trash 2), each adding 1 when it finds one: Black 2's VM has no OR. PL_TMP the slot, PL_TMP2 the
    // party count, PL_TMP3 what is read.
    .macro pl_BurmyFormPass var, form
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lbfp_loop\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lbfp_end\@
    PokePartyGetParam PL_TMP3, PL_TMP, 5       // PKM_PARAM_SPECIES
    WorkCmpConst PL_TMP3, 412                   // SPECIES_BURMY
    VMJumpIf CMP_NE, .Lbfp_next\@
    PokePartyGetParam PL_TMP3, PL_TMP, 0x6F    // PKM_PARAM_FORM (in s0110's stats_list)
    WorkCmpConst PL_TMP3, \form
    VMJumpIf CMP_NE, .Lbfp_next\@
    WorkAdd \var, 1
    VMJump .Lbfp_end\@
.Lbfp_next\@:
    WorkAdd PL_TMP, 1
    VMJump .Lbfp_loop\@
.Lbfp_end\@:
    .endm
    .macro pl_CheckBurmyForms var
    WorkSetConst \var, 0
    pl_BurmyFormPass \var, 0
    pl_BurmyFormPass \var, 1
    pl_BurmyFormPass \var, 2
    .endm

// ---- plat-ch10 (2026-11-07): Platinum's chapter 10 (pearl_story.py block "plat-ch10"; Pearl's scripts don't use it) -------
    // 0x213 FindPartySlotWithNature (pokeplatinum scrcmd_party.c): var = the first slot, not an Egg, whose nature is
    // nature (0-24), else 255. PL_TMP the slot, PL_TMP2 the party count, PL_TMP3 the nature read; cmp is WorkCmpConst
    // for a number, WorkCmpWork for a var (pearl_story's handler picks).
    .macro pl_FindPartySlotWithNature var, nature, cmp=WorkCmpConst
    WorkSetConst \var, 255
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lpfn_loop\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lpfn_end\@
    PokePartyIsEgg PL_TMP3, PL_TMP
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_NE, .Lpfn_next\@
    PokePartyGetParam PL_TMP3, PL_TMP, 0x70    // PKM_PARAM_NATURE
    \cmp PL_TMP3, \nature
    VMJumpIf CMP_NE, .Lpfn_next\@
    WorkSet \var, PL_TMP
    VMJump .Lpfn_end\@
.Lpfn_next\@:
    WorkAdd PL_TMP, 1
    VMJump .Lpfn_loop\@
.Lpfn_end\@:
    .endm
// ---- end plat-ch10

// ---- plat-ch9 (2026-11-07): Platinum's chapter 9 (pearl_story.py block "plat-ch9"; Pearl's scripts use none) -------------
    // 0x32F CheckPartyHasHeldItem item, var (pokeplatinum scrcmd_party.c): var = 1 if a party Pokémon holds the item
    // (Mt. Coronet 6F: the Adamant or Lustrous Orb). PL_TMP the slot, PL_TMP2 the party count, PL_TMP3 the item read.
    .macro pl_CheckPartyHasHeldItem item, var
    WorkSetConst \var, 0
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lphi_loop\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lphi_end\@
    PokePartyGetParam PL_TMP3, PL_TMP, 6       // PKM_PARAM_ITEM
    WorkCmpConst PL_TMP3, \item
    VMJumpIf CMP_EQ, .Lphi_yes\@
    WorkAdd PL_TMP, 1
    VMJump .Lphi_loop\@
.Lphi_yes\@:
    WorkSetConst \var, 1
.Lphi_end\@:
    .endm
    // 0x328 SetPartyGiratinaForm form (pokeplatinum Party_SetGiratinaForm): each party Giratina (487) to the Origin Forme
    // (form 1), or (form 0) to the forme its held item gives: the Origin Forme with the Griseous Orb (112), else the Altered
    // Forme. Black 2's PokePartySetForme recalculates its ability and stats and records it in the Pokédex.
    .macro pl_SetPartyGiratinaForm form
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lpgf_loop\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lpgf_end\@
    PokePartyGetParam PL_TMP3, PL_TMP, 5       // PKM_PARAM_SPECIES
    WorkCmpConst PL_TMP3, 487                   // SPECIES_GIRATINA
    VMJumpIf CMP_NE, .Lpgf_next\@
    .if \form
    PokePartySetForme PL_TMP, 1
    .else
    PokePartyGetParam PL_TMP3, PL_TMP, 6       // PKM_PARAM_ITEM
    WorkCmpConst PL_TMP3, 112                   // ITEM_GRISEOUS_ORB
    VMJumpIf CMP_EQ, .Lpgf_origin\@
    PokePartySetForme PL_TMP, 0
    VMJump .Lpgf_next\@
.Lpgf_origin\@:
    PokePartySetForme PL_TMP, 1
    .endif
.Lpgf_next\@:
    WorkAdd PL_TMP, 1
    VMJump .Lpgf_loop\@
.Lpgf_end\@:
    .endm
// ---- end plat-ch9

// ---- plat-ch12 (2026-11-07): Platinum's chapter 12 (pearl_story.py block "plat-ch12"; Pearl's scripts use none) ------------
    // 0x318 StartFatefulEncounter species, level: PearlB2 extension 0xBE (patches/platinum_postgame.py), Black 2's static wild
    // battle whose Pokémon has the fateful-encounter mark (Flower Paradise's Shaymin); then pl_CheckWonWildBattle, as after
    // pl_StartWildBattle
    .macro pl_StartFatefulEncounter species, level
    pl_ext 0xBE
    .2byte \species
    .2byte \level
    .endm
    // 0x302 GetRotomFormsInSave heat, wash, frost, fan, mow: extension 0xBD gives a bit for each form some Rotom has in the
    // party, the Day Care or a box (form n = bit n: 1 heat, 2 wash, 3 frost, 4 fan, 5 mow); each var 1 if its form is there
    .macro pl_RotomFormBit var, bit
    WorkSet \var, PL_TMP
    WorkAnd \var, \bit
    WorkCmpConst \var, 0
    VMJumpIf CMP_EQ, .Lprb\@
    WorkSetConst \var, 1
.Lprb\@:
    .endm
    .macro pl_GetRotomFormsInSave heat, wash, frost, fan, mow
    pl_ext 0xBD
    .2byte PL_TMP
    pl_RotomFormBit \heat, 2
    pl_RotomFormBit \wash, 4
    pl_RotomFormBit \frost, 8
    pl_RotomFormBit \fan, 16
    pl_RotomFormBit \mow, 32
    .endm
    // 0x303 GetPartyRotomCountAndFirst count, slot: the party's Rotom (479) in an appliance (form not 0), not Eggs, and the
    // first one's slot (255: none). PL_TMP the slot, PL_TMP2 the party count, PL_TMP3 a value read.
    .macro pl_GetPartyRotomCountAndFirst count, slot
    WorkSetConst \count, 0
    WorkSetConst \slot, 255
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lprc_loop\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lprc_end\@
    PokePartyIsEgg PL_TMP3, PL_TMP
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_NE, .Lprc_next\@
    PokePartyGetParam PL_TMP3, PL_TMP, 5       // PKM_PARAM_SPECIES
    WorkCmpConst PL_TMP3, 479                   // SPECIES_ROTOM
    VMJumpIf CMP_NE, .Lprc_next\@
    PokePartyGetForme PL_TMP3, PL_TMP
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_EQ, .Lprc_next\@
    WorkCmpConst \slot, 255
    VMJumpIf CMP_NE, .Lprc_count\@
    WorkSet \slot, PL_TMP
.Lprc_count\@:
    WorkAdd \count, 1
.Lprc_next\@:
    WorkAdd PL_TMP, 1
    VMJump .Lprc_loop\@
.Lprc_end\@:
    .endm
    // 0x2DD FindPartySlotWithSpecies var, species: the first slot (not an Egg) of the species, else 255 (Black 2's
    // PokePartyFindBySpecies writes the slot only when it finds one; PL_TMP its "found")
    .macro pl_FindPartySlotWithSpecies var, species
    WorkSetConst \var, 255
    PokePartyFindBySpecies \species, PL_TMP, \var
    .endm
    // 0x2E7 OpenSummaryScreenTeachMove slot, move + 0x2E8 GetSummarySelectedMoveSlot var: Black 2's forget-a-move screen
    // (CallPokeMoveReplace: PL_TMP3 1 when a move was chosen, PL_TMP2 its slot); the slot, or 4 when none was
    .macro pl_OpenSummaryScreenTeachMove slot, move
    MsgWinCloseAll
    CallPokeMoveReplace PL_TMP3, PL_TMP2, \slot, \move
    .endm
    .macro pl_GetSummarySelectedMoveSlot var
    WorkSet \var, PL_TMP2
    WorkCmpConst PL_TMP3, 1
    VMJumpIf CMP_EQ, .Lpss\@
    WorkSetConst \var, 4
.Lpss\@:
    .endm
// ---- end plat-ch12

// ---- plat-tutors (2026-11-07): Platinum's party commands (pearl_story's "plat-tutors" handlers; Platinum only so far).
// PearlB2 extension sub-commands 0xB0-0xB6 in the leftovers row (notes/EXT_COMMAND.md; decomp include/pearlb2/plat_party.h,
// src/pearlb2/plat_party/plat_party.c: overlay 376, loaded for the one command). Their tables are Platinum's (the dump,
// patches/platinum_tutors.py); without them (Pearl, Diamond) a tutor answers 0 and a footprint (0, 0).
// The shard tutors (pokeplatinum scrcmd_move_tutor.c): tutor move `index` (Platinum's order, 0-37) for a party slot:
// 0 can't learn it, 1 can, 2 knows it already (Platinum's species-and-form masks)
    .macro pl_TutorMoveCheck slot, index, var
    pl_ext 0xB0
    .2byte \slot, \index, \var
    .endm
// 0x2E5 CheckHasLearnableTutorMoves slot, location, var: 1 if a move of that tutor (0 Route 212, 1 the Survival Area,
// 2 Snowpoint) is left for it to learn
    .macro pl_CheckHasLearnableTutorMoves slot, location, var
    pl_ext 0xB1
    .2byte \slot, \location, \var
    .endm
// A tutor's move list (ShowMoveTutorMoveSelectionMenu, the generator writes one per move): Black 2's list menu, the move's
// name (word 2) in the entry, its Shards in the entry's description line (the plain window shows it while the cursor is
// there: ov012 ListMenu_ShowDescription). pl_TutorMenuMove adds it only when the Pokémon can learn it and doesn't know it
// (Platinum's list); pl_TutorMenuAny always (the Shard list on the wall: Platinum's PARTY_SLOT_NONE)
    .macro pl_TutorMenuMove slot, index, move, line, desc
    pl_TutorMoveCheck \slot, \index, PL_TMP
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, .Ltmm\@
    WordSetMoveName 2, \move
    ListMenuAdd \line, \desc, \move
.Ltmm\@:
    .endm
    .macro pl_TutorMenuAny move, line, desc
    WordSetMoveName 2, \move
    ListMenuAdd \line, \desc, \move
    .endm
// CheckCanAffordMove's test of one Shard (count 0: none needed): var = 0 when the Bag holds fewer; PayShardCost's payment
    .macro pl_TutorShardCheck item, count, var
    .if \count
    ItemCheckAmount \item, \count, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Ltsc\@
    WorkSetConst \var, 0
.Ltsc\@:
    .endif
    .endm
    .macro pl_TutorShardPay item, count
    .if \count
    ItemSub \item, \count, PL_TMP
    .endif
    .endm
// 0x23A GetPartyMonFootprintType print var, type var, slot (Dr. Footstep; overlay005 footprint_type.c)
    .macro pl_GetPartyMonFootprintType print, type, slot
    pl_ext 0xB2
    .2byte \print, \type, \slot
    .endm
// A contest condition (0x281 GetPartyMonContestStat: PKM_PARAM_CONTEST_COOL 0x13 + type) or one of Platinum's ribbons
// (0x230 GetPartyMonRibbon: the generator gives the ribbon's Black 2 PKM_PARAM) of a party slot
    .macro pl_GetPartyMonParam var, slot, param
    pl_ext 0xB3
    .2byte \var, \slot, \param
    .endm
// 0x231 SetPartyMonRibbon slot, ribbon (its Black 2 PKM_PARAM)
    .macro pl_SetPartyMonRibbon slot, param
    pl_ext 0xB4
    .2byte \slot, \param
    .endm
// 0x22F CountPartyRibbons var: Platinum's ribbons that some Pokémon of the party (no Egg) has (the Ribbon Syndicate)
    .macro pl_CountPartyRibbons var
    pl_ext 0xB5
    .2byte \var
    .endm
// 0x232 BufferRibbonName word, ribbon: the ribbon's name, a line of the zone's text, into word buffer `word`
    .macro pl_BufferLineWord word, line
    pl_ext 0xB6
    .2byte \word, \line
    .endm
// ---- end plat-tutors

// ---- plat-trades (2026-11-07): Gen 4's in-game trades, the Mining Museum's fossil restorer and the roamers (pearl_story's
// "plat-trades" handlers, on by version rows: Platinum now, Pearl and Diamond in 1.0.1). PearlB2 extension sub-commands
// 0xA7 and 0xA8 in the leftovers row (notes/EXT_COMMAND.md; decomp src/pearlb2/resident/npc_trade.c, roamers.c).
// StartNPCTrade (0x229): trade (the file's InitNPCTrade), party slot. Black 2's trade event: its demo, then the Pokémon,
// made by Gen 4's rules from the table patches/npc_trades.py writes, into the slot and the Pokédex. The script waits.
// Without the table (a build without the patch) nothing is traded.
    .macro pl_StartNPCTrade trade, slot
    pl_ext 0xA7
    .2byte \trade, \slot
    .endm
// ActivateRoamingPokemon (0x21C) slot (Gen 4's ROAMING_SLOT_*): that roamer released now, Lv and species by the slot
// (resident/roamers.c; Platinum's five from patches/roamers.py)
    .macro pl_ActivateRoamingPokemon slot
    pl_ext 0xA8
    .2byte \slot
    .endm
// The fossil commands (Gen 4's scrcmd_fossil.c) on Black 2's item commands, one line a fossil of the dump's table
// (b2tools/fossil_data.py), in its order. 0x1F1 GetFossilCount var: the Bag's count of every fossil, added up
    .macro pl_FossilCountAdd var, item
    ItemGetCount \item, PL_TMP
    WorkAdd \var, PL_TMP
    .endm
// 0x1F4 GetSpeciesFromFossil var, item: the fossil's species, 0 for any other item (the item waits in PL_TMP)
    .macro pl_FossilSpecies var, item, species
    WorkCmpConst PL_TMP, \item
    VMJumpIf CMP_NE, .Lfsp\@
    WorkSetConst \var, \species
.Lfsp\@:
    .endm
// 0x1F5 FindFossilAtThreshold item var, index var, threshold: the table walked with the Bag's counts added up (PL_TMP2);
// the first fossil where the sum reaches the threshold (PL_TMP3) gives its item and its index, none gives 0 and 0
    .macro pl_FossilFind item, index, fossil, k, done
    ItemGetCount \fossil, PL_TMP
    WorkAdd PL_TMP2, PL_TMP
    WorkCmpWork PL_TMP2, PL_TMP3
    VMJumpIf CMP_LT, .Lffn\@
    WorkSetConst \item, \fossil
    WorkSetConst \index, \k
    VMJump \done
.Lffn\@:
    .endm
// ---- end plat-trades

// ---- v101-story (2026-11-07): 1.0.1's new script fixes for Pearl and Diamond (pearl_story.py block "v101-story") ---------
// Pearl 0x263 SetDeoxysForm form: each party Deoxys (386) to that form = Black 2's PokePartySetForme (stats recalculated, the
// Pokédex records it), as pl_SetPartyGiratinaForm. Veilstone's meteorites.
    .macro pl_ChangeDeoxysForm form
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lpdf_loop\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lpdf_end\@
    PokePartyGetParam PL_TMP3, PL_TMP, 5       // PKM_PARAM_SPECIES
    WorkCmpConst PL_TMP3, 386                   // SPECIES_DEOXYS
    VMJumpIf CMP_NE, .Lpdf_next\@
    PokePartySetForme PL_TMP, \form
.Lpdf_next\@:
    WorkAdd PL_TMP, 1
    VMJump .Lpdf_loop\@
.Lpdf_end\@:
    .endm
// Pearl 0x1DF (the Battle Tower's trophies; pokediamond unk_0205FA2C.c sub_0205FE10): var = 1, 2 or 3 for the Bronze, Silver
// or Gold Trophy (goods 85-87) at a 20-, 50- or 100-win streak not yet given, marked given now; 4 when the PC has no room for
// it; 0 none. The longest streak of any room is decomp extension 0x91, the given trophies 0x92 (resident/tower.c: bits of
// the subway's score flags), the PC's room the Secret Bases' check (pl_CheckHasRoomForGoodsInPC)
// (plat-stubs, 2026-11-08) The streak the trophies count: Pearl's record 0x35, its Tower's best of any room (decomp extension
// 0x91); Platinum's STAT_TOWER_RECORD_STREAK_SINGLE (pokeplatinum unk_0206B9D8.c sub_0206BDBC: the Single record only), the
// Frontier core's record 0 (the Subway's single mode, plat_frontier.c)
    .macro pl_TowerTrophyStreak var
#if PEARLB2_GAME_VERSION == 12
    pl_FrontierStatGet 0, \var
#else
    pl_ext 0x91
    .2byte \var
#endif
    .endm
    .macro pl_TowerTrophyStep var, need, trophy, good, next
    WorkCmpConst PL_TMP, \need
    VMJumpIf CMP_LT, .Lttp_end\@
    pl_ext 0x92
    .2byte 0, \trophy, PL_TMP2
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_NE, \next
    pl_CheckHasRoomForGoodsInPC \good, PL_TMP2
    WorkSetConst \var, 4
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lttp_end\@
    pl_ext 0x92
    .2byte 1, \trophy, PL_TMP2
    WorkSetConst \var, \trophy + 1
.Lttp_end\@:
    .endm
    .macro pl_TowerTrophy var
    pl_TowerTrophyStreak PL_TMP
    WorkSetConst \var, 0
    pl_TowerTrophyStep \var, 20, 0, 85, .Lttq_1\@
    VMJump .Lttq_end\@
.Lttq_1\@:
    pl_TowerTrophyStep \var, 50, 1, 86, .Lttq_2\@
    VMJump .Lttq_end\@
.Lttq_2\@:
    pl_TowerTrophyStep \var, 100, 2, 87, .Lttq_end\@
.Lttq_end\@:
    .endm
// Pearl 0x1E0 (pokediamond sub_0205FF5C; 1.0.1): the trophy pl_TowerTrophy would give now, 1-3, without giving it; 0 none.
// The lobby's map script shows the trophy attendant when it isn't 0, and he gives it (0x1DF). Pearl answers 4-6 instead
// for a trophy an earlier try found no PC room for; PearlB2 keeps no such marks, so those read 1-3 (the map script only
// asks "not 0", so the attendant shows in the same cases)
    .macro pl_TowerTrophyDue var
    pl_TowerTrophyStreak PL_TMP                // the longest streak of any room (Platinum: the Single record)
    WorkSetConst \var, 0
    WorkCmpConst PL_TMP, 20
    VMJumpIf CMP_LT, .Lttd_end\@
    pl_ext 0x92
    .2byte 0, 0, PL_TMP2                       // the Bronze Trophy given?
    WorkSetConst \var, 1
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lttd_end\@
    WorkSetConst \var, 0
    WorkCmpConst PL_TMP, 50
    VMJumpIf CMP_LT, .Lttd_end\@
    pl_ext 0x92
    .2byte 0, 1, PL_TMP2                       // the Silver
    WorkSetConst \var, 2
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lttd_end\@
    WorkSetConst \var, 0
    WorkCmpConst PL_TMP, 100
    VMJumpIf CMP_LT, .Lttd_end\@
    pl_ext 0x92
    .2byte 0, 2, PL_TMP2                       // the Gold
    WorkSetConst \var, 3
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lttd_end\@
    WorkSetConst \var, 0
.Lttd_end\@:
    .endm
// ---- end v101-story

// ---- plat-records (2026-11-08): Gen 4's OpenBattleTowerRecordsApp rankings, type (pearl_story h_tower_records). The lobby's
// results machines show the player's own results as a message, in the records app's words: first = the first of the eleven
// lines pearl_story adds to the zone's text (_tower_records_lines). rankings not 0: Black 2's leaders screen, as before.
// type 0: Single and Double, 1: Multi and link Multi, 2: Wi-Fi (its rank, then its streaks).
// One room's two rows (Black 2's Subway mode mode): buffer 0 the latest streak, 1 the longest; line prev while no streak goes
// on, cur while one does (the mode has a stage)
    .macro pl_TowerResultsRoom mode, prev, cur
    BSubwayCmd_Tool 6, \mode, 0, PL_TMP           // the latest streak (BSubwayScoreData_GetStreak, at most 9,999)
    WordSetNumber 0, PL_TMP, 0
    pl_FrontierStatGet \mode*2, PL_TMP           // the longest (BSubwayScoreData_GetMaxStreak: plat_frontier.c)
    WordSetNumber 1, PL_TMP, 0
    BSubwayCmd_Tool 38, \mode, 0, PL_TMP          // a streak going on (BSubwayScoreData_HasStage)
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Ltrr_cur\@
    SystemMsg \prev, 2
    VMJump .Ltrr_end\@
.Ltrr_cur\@:
    SystemMsg \cur, 2
.Ltrr_end\@:
    .endm
    .macro pl_TowerResults rankings, type, first
    WorkSet PL_TMP, \rankings
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Ltr_own\@
    BSubwayCmd_Tool 111, 0, 0, 0                  // the Wi-Fi leaders: Black 2's leaders screen
    VMJump .Ltr_end\@
.Ltr_own\@:
    WorkSet PL_TMP, \type
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Ltr_multi\@
    WorkCmpConst PL_TMP, 2
    VMJumpIf CMP_EQ, .Ltr_wifi\@
    pl_TowerResultsRoom 0, \first, \first+1      // Battle Room Results: Single Record
    pl_TowerResultsRoom 1, \first+2, \first+3  // Double Record
    VMJump .Ltr_shown\@
.Ltr_multi\@:
    pl_TowerResultsRoom 2, \first+4, \first+5  // Multi Battle Room Results: Multi Record
    pl_TowerResultsRoom 3, \first+6, \first+7  // Link Record
    VMJump .Ltr_shown\@
.Ltr_wifi\@:
    BSubwayCmd_Tool 27, 0, 0, PL_TMP              // Wi-Fi Battle Room Results: Current Rank (BSubwayScoreData_GetWifiRank)
    WordSetNumber 0, PL_TMP, 0
    SystemMsg \first+8, 2
    pl_TowerResultsRoom 4, \first+9, \first+10 // Wi-Fi Record
.Ltr_shown\@:
    LastKeyWait
    MsgWinCloseAll
.Ltr_end\@:
    .endm
// Platinum's OpenFrontierRecordsApp challengeType, facility, species (pearl_story h_frontier_records): the Frontier records
// machines show the facility's records for the type picked (a var: 0 Single, 1 Double, 2 Multi) as messages, in the records
// app's words. kind: the facility (1 Tower, 2 Factory, 4 Castle, 6 Arcade: Platinum's FACILITY_*); first: the first of its lines
// (_frontier_records_lines, each a PREV and a CURRENT copy). The numbers are the Frontier core's records by Platinum's ids
// (BattleFrontierStats), the line by the facility's streak flag (Platinum's bits)
    .macro pl_FrontierRecordNumber buf, stat
    pl_FrontierStatGet \stat, PL_TMP
    WordSetNumber \buf, PL_TMP, 0
    .endm
    .macro pl_FrontierRecordsShow facility, bit, prev, cur
    pl_FrontierStreakFlag \facility, 0, \bit, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lfrs_cur\@
    SystemMsg \prev, 2
    VMJump .Lfrs_end\@
.Lfrs_cur\@:
    SystemMsg \cur, 2
.Lfrs_end\@:
    .endm
    // the Factory, one level (o: 0 Level 50, 1 Open Level) of type t: STAT_FACTORY_* 10 + 8 t + 4 o (the record streak, the
    // latest, the record's Rental/Trade count, the latest's); its flag bit 4 o + t (BattleFactoryStreakFlags)
    .macro pl_FrontierRecordsFactoryLevel t, o, prev, cur
    pl_FrontierRecordNumber 0, 11+8*\t+4*\o
    pl_FrontierRecordNumber 1, 13+8*\t+4*\o
    pl_FrontierRecordNumber 2, 10+8*\t+4*\o
    pl_FrontierRecordNumber 3, 12+8*\t+4*\o
    pl_FrontierRecordsShow 0, 4*\o+\t, \prev, \cur
    .endm
    .macro pl_FrontierRecordsType kind, t, first
    .if \kind == 1                                 // the Tower: Black 2's Subway records (pl_TowerResultsRoom)
    .if \t == 2
    pl_TowerResultsRoom 2, \first+4, \first+5      // Multi w/Trainer
    pl_TowerResultsRoom 3, \first+6, \first+7      // Multi w/friend (the wireless Multi: closed)
    .else
    pl_TowerResultsRoom \t, \first+2*\t, \first+2*\t+1
    .endif
    .elseif \kind == 2                             // the Factory: Level 50, then Open Level
    pl_FrontierRecordsFactoryLevel \t, 0, \first+2*\t, \first+2*\t+1
    pl_FrontierRecordsFactoryLevel \t, 1, \first+6, \first+7
    .elseif \kind == 4                             // the Castle: STAT_CASTLE_* 70 + 8 t (record, latest, latest CP, spent,
    pl_FrontierRecordNumber 0, 71+8*\t             // record CP); flag bit t
    pl_FrontierRecordNumber 1, 72+8*\t
    pl_FrontierRecordNumber 2, 70+8*\t
    pl_FrontierRecordNumber 3, 74+8*\t
    pl_FrontierRecordsShow 2, \t, \first+2*\t, \first+2*\t+1
    .else                                          // the Arcade: STAT_ARCADE_* 94 + 2 t (record, latest); flag bit t
    pl_FrontierRecordNumber 0, 95+2*\t
    pl_FrontierRecordNumber 1, 94+2*\t
    pl_FrontierRecordsShow 3, \t, \first+2*\t, \first+2*\t+1
    .endif
    .endm
    .macro pl_FrontierRecords kind, type, first
    WorkSet PL_TMP, \type
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Lfr_1\@
    WorkCmpConst PL_TMP, 2
    VMJumpIf CMP_EQ, .Lfr_2\@
    pl_FrontierRecordsType \kind, 0, \first
    VMJump .Lfr_shown\@
.Lfr_1\@:
    pl_FrontierRecordsType \kind, 1, \first
    VMJump .Lfr_shown\@
.Lfr_2\@:
    pl_FrontierRecordsType \kind, 2, \first
.Lfr_shown\@:
    LastKeyWait
    MsgWinCloseAll
    .endm
// ---- end plat-records

// ---- elevators (pearl_story ELEVATOR_FLOORS_ABOVE; 2026-10-25, chapter 4a) -----------------------------------------
// Pearl's ElevatorAnimation (0x23C) shakes the room while it rides; Black 2 has no shaking room, so the ride is Black 2's
// own elevator sounds (global 10405, Castelia's lifts: SEQ_SE_FLD_23 while it moves, SEQ_SE_FLD_87 on arrival) over
// about as long as Pearl's four shakes.
    .macro pl_elevator_ride
    SEPlay SEQ_SE_FLD_23
    VMSleep 45
    SEStop
    SEPlay SEQ_SE_FLD_87
    SEWait
    .endm

// ---- Pearl's Pastoria Gym (chapter 5a, 2026-10-25) --------------------------------------------------------------
    // 0x170 CheckPastoriaGymButton (pokeplatinum PastoriaGym_PressButton): the button under the player moves the gym's
    // water (blue: the top, green: the middle, orange: the bottom), and the script waits until it stops. The decomp's
    // src/pearlb2/pastoria_gym_itcm.c (gimmick 30 of the gym's zone, patches/pastoria_gym.py) moves it while
    // PVAR_PASTORIA_GYM_PRESS is 1 and sets it back to 0. Without that code the wait gives up after 8 s (240 frames).
    // The sound is a [guess] for Pearl's SEQ_SE_DP_FW056 (water moving): Humilau Gym's platform ride.
    .macro pl_PressPastoriaGymButton
    SEPlay SEQ_SE_SW_MIZUGYM_01
    WorkSetConst PVAR_PASTORIA_GYM_PRESS, 1
    WorkSetConst PL_TMP, 0
.Lpgb\@:
    VMSleep 1
    WorkAdd PL_TMP, 1
    WorkCmpConst PL_TMP, 240
    VMJumpIf CMP_GE, .Lpgbx\@
    WorkCmpConst PVAR_PASTORIA_GYM_PRESS, 0
    VMJumpIf CMP_NE, .Lpgb\@
.Lpgbx\@:
    WorkSetConst PVAR_PASTORIA_GYM_PRESS, 0
    .endm

// ---- Chapter 8 (2026-10-26): the Sunyshore Gym's gears, the League's scripted lift, the Hall of Fame -------------
    // A request to the zone's PearlB2 gimmick (PVAR_GIMMICK_REQUEST, map-local: the lead's one handshake work): set it,
    // then wait until the gimmick's C sets it back to 0 (at most \frames frames: without the gimmick the script goes on)
    .macro pl_gimmick_request value, frames
    WorkSetConst PVAR_GIMMICK_REQUEST, \value
    WorkSetConst PL_TMP, 0
.Lgrq\@:
    VMSleep 1
    WorkAdd PL_TMP, 1
    WorkCmpConst PL_TMP, \frames
    VMJumpIf CMP_GE, .Lgrqx\@
    WorkCmpConst PVAR_GIMMICK_REQUEST, 0
    VMJumpIf CMP_NE, .Lgrq\@
.Lgrqx\@:
    WorkSetConst PVAR_GIMMICK_REQUEST, 0
    .endm
    // 0x176 RotateSunyshoreGymGear type (0 a quarter turn, 1 a quarter back, 2 a half turn; pokeplatinum
    // SunyshoreGym_PressButton): every gear of the room turns 5.625 degrees a frame (16 or 32 frames), the script waits.
    // The decomp's src/pearlb2/sunyshore_gym_itcm.c (gimmick 62) plays the sound and turns them while the request is
    // 1 + type.
    .macro pl_RotateSunyshoreGymGear type
    pl_gimmick_request (1 + \type), 120
    .endm
    // Platinum's 0x2CA AdvanceEternaGymClock (its Eterna Gym, after each Gym Trainer's win and Gardenia's): the clock
    // turns to its next state while the script waits (gimmick 65, src/pearlb2/plat_gyms/plat_eterna_gym.c). After the
    // second and third Trainer the camera stops at the fountain that drains: the gimmick asks for the line (the
    // request goes to 2), the script shows it (the zone's line \line, "The fountain's water level dropped!", as
    // Platinum's field task prints it) and waits for A or B, then asks the camera back (3); 0 when it is done. Without
    // the gimmick the script goes on after 15 s.
    .macro pl_AdvanceEternaGymClock line
    WorkSetConst PVAR_GIMMICK_REQUEST, 1
    WorkSetConst PL_TMP, 0
.Lecw\@:
    VMSleep 1
    WorkAdd PL_TMP, 1
    WorkCmpConst PL_TMP, 900
    VMJumpIf CMP_GE, .Lecx\@
    WorkCmpConst PVAR_GIMMICK_REQUEST, 1
    VMJumpIf CMP_EQ, .Lecw\@
    WorkCmpConst PVAR_GIMMICK_REQUEST, 2
    VMJumpIf CMP_NE, .Lecb\@
    SystemMsg \line, 2
    pl_WaitButton
    pl_CloseMessage
    WorkSetConst PVAR_GIMMICK_REQUEST, 3
.Lecb\@:
    VMSleep 1
    WorkAdd PL_TMP, 1
    WorkCmpConst PL_TMP, 900
    VMJumpIf CMP_GE, .Lecx\@
    WorkCmpConst PVAR_GIMMICK_REQUEST, 0
    VMJumpIf CMP_NE, .Lecb\@
.Lecx\@:
    WorkSetConst PVAR_GIMMICK_REQUEST, 0
    .endm
    // Pearl's TriggerPlatformLift from a script (Cynthia's room after her battle, the player on the lift): gimmick 59
    // (pearl_platforms_itcm.c) rides the zone's lift with the player while the request is 1 (240 units at 2 a frame)
    .macro pl_TriggerPlatformLiftRide
    pl_gimmick_request 1, 300
    .endm
    // 0x28F (Pearl's League win count: the Hall of Fame room's first-time lines at 0, Fight Area Barry's team at 20):
    // Black 2's record of Hall of Fame entries (RECORD_HALL_OF_FAME_ENTRIES 71, which its game clear counts:
    // ov295 game_clear_save.c), 0 before the first, as Pearl's count
    .macro pl_GetLeagueVictories var
    RecordGet 71, \var
    .endm
    // 0x25A PlayHallOfFameHealingAnimation: Pearl's machine takes the party's balls with the healing tune. Black 2's
    // machine event needs its own Hall of Fame props, so: the tune (Black 2's Pokémon Center heal ME)
    .macro pl_PlayHallOfFameHealingAnimation
    MEPlay SEQ_ME_ASA
    MEWait
    .endm
    // 0xB0 ShowEndGameScreen: Black 2's own Hall of Fame ending, as its script ends it (pokemon_league_10.s): the
    // field's fade, CallGameClear (0 the first time: Black 2's game-clear flag 2400 = Pearl's 0x964 not yet set; 1 after,
    // the credits skippable), FinishAllEvents, unpause, end. CallGameClear runs the record screen, global 9601 (heal,
    // Continue in the player's room: src/field_scripts/1242_global_9600.s), the save, the credits and THE END
    // (PearlB2's ending places: the decomp's event_game_clear.c). Ending any other way (a raw GFL fade, a VMHalt
    // straight after CallGameClear) left HoennB2 on a black screen on melonDS and hardware (HoennB2 2fd355b).
    .macro pl_ClearGame
    MsgWinCloseAll
    FlagGet PFLAG_0964, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lcga\@
    FlagSet PFLAG_0964
    FadeOutBlackQ
    FadeWait
    CallGameClear 0
    VMJump .Lcge\@
.Lcga\@:
    FadeOutBlackQ
    FadeWait
    CallGameClear 1
.Lcge\@:
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt
    .endm

// ---- Pearl's Great Marsh as a normal area (chapter 5a, 2026-10-25; HoennB2's Safari Zone rule) -------------------
    // 0x202 EnableDisableSafariZone 0: Pearl's 30 Safari Balls into the Bag (no step count, no Safari battle screen)
    .macro pl_SafariStart
    ItemAdd ITEM_SAFARI_BALL, 30, PL_TMP
    .endm
    // 0x202 EnableDisableSafariZone 1: the Safari Balls left are taken back (HoennB2 c8b_take_safari_balls)
    .macro pl_SafariEnd
    ItemGetCount ITEM_SAFARI_BALL, PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lpse\@
    ItemSub ITEM_SAFARI_BALL, PL_TMP, PL_TMP2
.Lpse\@:
    .endm

// ---- move tutors (2026-10-26, chapter 5b: Grandma Wilma's Draco Meteor on Route 210 N; Route 228's ultimate moves,
// chapter 9, use the same) ------------------------------------------------------------------------------------------
    // 0x248 GetPartyMonTypes type1, type2, slot: Black 2's PokePartyGetTypes (the same order), its numbers made Gen 4's
    // (Gen 4 has the ??? type at 9, so Fire and every type after it is one higher: Dragon 16, Dark 17)
    .macro pl_GetPartyMonTypes t1, t2, slot
    PokePartyGetTypes \t1, \t2, \slot
    WorkCmpConst \t1, 9
    VMJumpIf CMP_LT, .Lgpt1\@
    WorkAdd \t1, 1
.Lgpt1\@:
    WorkCmpConst \t2, 9
    VMJumpIf CMP_LT, .Lgpt2\@
    WorkAdd \t2, 1
.Lgpt2\@:
    .endm
    // 0x224 OpenMoveTutorMenu slot, move (pokeplatinum ScrCmd_OpenMoveTutorMenu: the Move Reminder app showing that one
    // move, between a fade-out and RestoreOverworld + a fade-in, which the generator drops here) and 0x225
    // CheckLearnedTutorMove var (0 learned, 0xFF not). The app's own choices and lines (Pearl bank 586, the line numbers
    // the generator passes) on Black 2's commands, on the field: teach it? (no: give up?), a free move slot takes it
    // (PokePartyLearnMove), a Pokémon with four goes to Black 2's forget-a-move screen (CallPokeMoveReplace, as Black 2's
    // own tutors); no Heart Scale. The result waits in PL_TMP2 for pl_CheckLearnedTutorMove.
    .macro pl_OpenMoveTutorMenu slot, move, lteach, lgiveup, llearned, ltrying, lpoof, llearned2, lstop, ldidnot
.Lmta\@:
    WordSetPartyPokeName 0, \slot
    WordSetMoveName 1, \move
    SystemMsg \lteach, 2
    YesNoWin PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lmtt\@
    SystemMsg \lgiveup, 2
    YesNoWin PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lmta\@
    WorkSetConst PL_TMP2, 255
    VMJump .Lmte\@
.Lmtt\@:
    PokePartyGetMoveCount PL_TMP, \slot
    WorkCmpConst PL_TMP, 4
    VMJumpIf CMP_EQ, .Lmtf\@
    PokePartyLearnMove \slot, PL_TMP, \move
    MEPlay SEQ_ME_LVUP
    SystemMsg \llearned, 2
    MEWait
    WorkSetConst PL_TMP2, 0
    VMJump .Lmte\@
.Lmtf\@:
    WordSetPartyPokeName 0, \slot
    WordSetMoveName 1, \move
    SystemMsg \ltrying, 2
    YesNoWin PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lmtr\@
    SystemMsg \lstop, 2
    YesNoWin PL_TMP
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lmtf\@
    SystemMsg \ldidnot, 2
    WorkSetConst PL_TMP2, 255
    VMJump .Lmte\@
.Lmtr\@:
    MsgWinCloseAll
    CallPokeMoveReplace PL_TMP3, PL_TMP, \slot, \move
    WorkCmpConst PL_TMP3, 1
    VMJumpIf CMP_NE, .Lmtf\@
    PokePartyGetMove PL_TMP3, \slot, PL_TMP
    WordSetPartyPokeName 0, \slot
    WordSetMoveName 1, PL_TMP3
    SystemMsg \lpoof, 2
    PokePartyLearnMove \slot, PL_TMP, \move
    WordSetMoveName 1, \move
    MEPlay SEQ_ME_LVUP
    SystemMsg \llearned2, 2
    MEWait
    WorkSetConst PL_TMP2, 0
.Lmte\@:
    MsgWinCloseAll
    .endm
    .macro pl_CheckLearnedTutorMove var
    WorkSet \var, PL_TMP2
    .endm

// ---- PearlB2's extension command (notes/EXT_COMMAND.md): Black 2's command 0x15F (s015F_Nop, used by no Black 2
// script) is PearlB2's dispatcher (decomp src/pearlb2/ext_cmd_itcm.c): a sub-command byte, then its arguments.
// Sub-commands 0x00-0x1F the Pokétch, 0x20-0x3F the Underground, 0x40-0x5F Pal Park.
    .macro pl_ext sub
    FieldCommand 351
    .byte \sub
    .endm

// ---- the Pokétch (notes/POKETCH.md; decomp src/pearlb2/poketch_itcm.c PearlB2_Ext_Poketch) ----------------------
    .macro pl_EnablePoketch                // 0x131 (pokediamond GivePoketch): given; the bottom screen fades to it
    pl_ext 0x00
    .endm
    .macro pl_CheckPoketchEnabled var      // 0x132 (CheckPoketch): var = 1 when given
    pl_ext 0x01
    .2byte \var
    .endm
    .macro pl_RegisterPoketchApp app       // 0x133 (UnlockPoketchApp): app = a number or a var (Pearl's VarGet)
    pl_ext 0x02
    .2byte \app
    .endm
    .macro pl_CheckPoketchAppRegistered app, var   // 0x134 (CheckPoketchApp): var = 1 when registered
    pl_ext 0x03
    .2byte \app
    .2byte \var
    .endm
    .macro pl_HidePoketch                  // 0x265: Pearl's flag 0x97C set (the Pokétch not shown from the next start)
    pl_ext 0x04
    .endm
    .macro pl_ShowPoketch                  // 0x266: flag 0x97C cleared
    pl_ext 0x05
    .endm
// ---- Pearl's honey trees and swarms (notes/ENCOUNTERS.md; decomp resident/wild.c PearlB2_Ext_Wild, row 0x60-0x7F)
    .macro pl_GetHoneyTreeStatus var           // 0x128 CheckHoneyTree: 1 bare, 2 slathered, 3 a Pokémon may be there
    pl_ext 0x60
    .2byte \var
    .endm
    .macro pl_SlatherHoneyTree                 // 0x127 UpdateHoneyTree
    pl_ext 0x61
    .endm
    .macro pl_StartHoneyTreeBattle             // 0x129 HoneyTreeBattle: Pearl's species and level, the tree is bare
    pl_ext 0x62
    .2byte PL_TMP
    .2byte PL_TMP2
    CallWildBattle PL_TMP, PL_TMP2, 0
    .endm
    .macro pl_StopHoneyTreeShaking             // 0x12A StopHoneyTreeAnimation
    pl_ext 0x63
    .endm
    .macro pl_EnableSwarms                     // 0x21B: Barry's sister has told the player
    pl_ext 0x64
    .endm
    .macro pl_GetSwarmInfo zone, species       // 0xE3 GetSwarmInfo: the day's zone (Black 2's) and its first species
    pl_ext 0x65
    .2byte \zone
    .2byte \species
    .endm
// ---- Pearl's berry patches (notes/ENCOUNTERS.md; decomp resident/berry.c). 0x8011: Black 2's talked-to person
    .macro pl_GetBerry field, var              // 0x17D-0x181: 0 stage, 1 Berry item, 2 mulch item, 3 moisture, 4 yield
    pl_ext 0x66
    .2byte 0x8011
    .byte \field
    .2byte \var
    .endm
    .macro pl_SetBerryMulch item               // 0x182
    pl_ext 0x67
    .2byte 0x8011
    .2byte \item
    .endm
    .macro pl_PlantBerry item                  // 0x183
    pl_ext 0x68
    .2byte 0x8011
    .2byte \item
    .endm
    .macro pl_WaterBerry                       // 0x184 0: the patch in front (no pose in Black 2)
    pl_ext 0x69
    .2byte 0x8011
    VMSleep 30
    .endm
    .macro pl_HarvestBerry                     // 0x185
    pl_ext 0x6A
    .2byte 0x8011
    .endm
    .macro pl_BufferBerryName n, item          // 0x17B: "Cheri" of Cheri Berry
    pl_ext 0x6B
    .byte \n
    .2byte \item
    .endm
    .macro pl_OpenBerryBag pocket              // 0x178: the Bag on Black 2's pocket; the choice in work 0x8007
    pl_ext 0x6C
    .byte \pocket
    WorkSetConst 0x8006, \pocket
    FieldClose
    CallBag 1, PL_TMP, 0x8007
    FieldOpen
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lpobb\@
    WorkSetConst 0x8007, 0
.Lpobb\@:
    .endm
    .macro pl_GetBagSelection var              // 0x179: 0 for no choice; on the Berries, 0 for what isn't a Berry
    WorkSet \var, 0x8007
    WorkCmpConst 0x8006, 3
    VMJumpIf CMP_NE, .Lpgbs\@
    WorkCmpConst \var, 149
    VMJumpIf CMP_LT, .Lpgbz\@
    WorkCmpConst \var, 212
    VMJumpIf CMP_LE, .Lpgbs\@
.Lpgbz\@:
    WorkSetConst \var, 0
.Lpgbs\@:
    .endm
    .macro pl_CheckBerriesInBag var            // 0x17A CheckPocketNotEmpty 4
    pl_ext 0x6D
    .2byte \var
    .endm
// ---- Chapter 9b (2026-10-26)
    .macro pl_GetSpiritombCounter var          // 0x214 GetSpiritombTalkCounter (people talked to in Pearl's multiplayer
    WorkSet \var, PVAR_UG_HIDEAWAY_BATTLES     // Underground): the Hideaways' wild battles here (underground_itcm.c;
    .endm                                      // the lead 2026-10-26: 32 Hideaway battles wake the Hallowed Tower)
    .macro pl_ClearSpiritombCounter            // 0x26F ResetSpiritombTalkCounter
    WorkSetConst PVAR_UG_HIDEAWAY_BATTLES, 0
    .endm
    .macro pl_GetPartyMonLevel var, slot       // 0x278 (pokediamond ScrCmd_GetPartyMonLevel): 0 for an Egg
    WorkSetConst \var, 0
    PokePartyIsEgg PL_TMP, \slot
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_NE, .Lpgml\@
    PokePartyGetParam \var, \slot, 158         // PKM_PARAM_LEVEL
.Lpgml\@:
    .endm
    .macro pl_GetDailyRandomLevel var          // 0x277: Pearl's daily level 2-99 (pokeplatinum SystemVars_InitDailyRandomLevel:
    RTCGetDate \var, PL_TMP                    // a random one each day, kept in Pearl's save); here a level 2-99 from
    WorkMul \var, 31                           // the date (each date its own): ((month * 31 + day) * 53 + 17) % 98 + 2
    WorkAdd \var, PL_TMP
    WorkMul \var, 53
    WorkAdd \var, 17
    WorkMod \var, 98
    WorkAdd \var, 2
    .endm
// The Trophy Garden's daily Pokémon (Mr. Backlot, the Pokémon Mansion): Pearl's save keeps two slots (pokeplatinum
// special_encounter.c trophyGarden, trophy_garden_daily_encounters.c); here the species in PVAR_TROPHY_GARDEN_1/2.
// The 16 are Pearl's encdata_ex member 8, in its order (read from the dump). The wild side (grass slots 6 and 7 of the
// Trophy Garden become slots 1 and 2 with the National Pokédex: pokeplatinum wild_encounters.c
// WildEncounters_ReplaceTrophyGardenEncounters) is the encounter code's (STORY_HANDOFFS 9b).
    .macro pl_tg_pick index, species
    WorkCmpConst PL_TMP, \index
    VMJumpIf CMP_NE, .Lptgp\@
    WorkSetConst PL_TMP2, \species
.Lptgp\@:
    .endm
    .macro pl_AddTrophyGardenMon               // 0x1EC AddTrophyGardenMon: one of the 16 at random, not one of the two
.Lptga\@:                                      // there now; slot 1 moves to slot 2, the new one is slot 1
    Random PL_TMP, 16
    pl_tg_pick 0, 133                          // Eevee
    pl_tg_pick 1, 438                          // Bonsly
    pl_tg_pick 2, 440                          // Happiny
    pl_tg_pick 3, 52                           // Meowth
    pl_tg_pick 4, 173                          // Cleffa
    pl_tg_pick 5, 35                           // Clefairy
    pl_tg_pick 6, 174                          // Igglybuff
    pl_tg_pick 7, 311                          // Plusle
    pl_tg_pick 8, 39                           // Jigglypuff
#if PEARLB2_GAME_VERSION == 12
    pl_tg_pick 9, 132                          // (plat-ch12) Platinum's tenth is Ditto, not Pearl's Porygon
#else                                          // (pokeplatinum encounters_trophy_garden.json daily_encounters)
    pl_tg_pick 9, 137                          // Porygon
#endif
    pl_tg_pick 10, 351                         // Castform
    pl_tg_pick 11, 312                         // Minun
    pl_tg_pick 12, 439                         // Mime Jr.
    pl_tg_pick 13, 183                         // Marill
    pl_tg_pick 14, 113                         // Chansey
    pl_tg_pick 15, 298                         // Azurill
    WorkCmpWork PL_TMP2, PVAR_TROPHY_GARDEN_1
    VMJumpIf CMP_EQ, .Lptga\@
    WorkCmpWork PL_TMP2, PVAR_TROPHY_GARDEN_2
    VMJumpIf CMP_EQ, .Lptga\@
    WorkSet PVAR_TROPHY_GARDEN_2, PVAR_TROPHY_GARDEN_1
    WorkSet PVAR_TROPHY_GARDEN_1, PL_TMP2
    .endm
    .macro pl_GetTrophyGardenSlot1Species var  // 0x1ED: slot 1's species
    WorkSet \var, PVAR_TROPHY_GARDEN_1
    .endm

// ---- Pal Park (notes/PAL_PARK_MIGRATION.md; decomp src/pearlb2/resident/palpark.c PearlB2_Ext_PalPark): sub-commands
// 0x40-0x45 of PearlB2's extension command 0x15F (pl_ext, notes/EXT_COMMAND.md). A value may be a var.
    .macro pl_GetGBACartridgeVersion var   // 0x26E: the GBA game in slot 2, 0 none, 1 Sapphire, 2 Ruby, 3 Emerald,
    pl_ext 0x40                            // 4 FireRed, 5 LeafGreen (never one on a DSi or 3DS)
    .2byte \var
    .byte 0xff
    .endm
    .macro pl_GetGBACartridgeAndName var, word   // the same, and its player's name in word buffer `word`
    pl_ext 0x40
    .2byte \var
    .byte \word
    .endm
    .macro pl_PalParkMigrate var           // the migration screen (overlay 372): var = 6 when six came, else 0
    pl_ext 0x41
    .2byte \var
    .endm
    .macro pl_CheckHasEnoughMonForCatchingShow var   // 0x254: var = 1 when six are stocked
    pl_ext 0x42
    .2byte \var
    .endm
    .macro pl_SetClearInCatchingShowFlag value   // 0x253: 0 the show starts, 1 it ends (the time points)
    pl_ext 0x43
    .2byte \value
    .endm
    .macro pl_MoveCatchingShowMonsToPCBoxes     // 0x255: the six to the PC (met in Pal Park, in Park Balls)
    pl_ext 0x44
    .endm
    .macro pl_CalcCatchingShowPoints kind, var  // 0x256: kind 0 catching, 1 time, 2 type, 3 total
    pl_ext 0x45
    .2byte \kind
    .2byte \var
    .endm

// The Battle Tower's extension sub-commands 0x80-0x9F (notes/BATTLE_ZONE.md, decomp src/pearlb2/resident/tower.c)
    .macro pl_TowerBpGet var
    pl_ext 0x80
    .short \var
    .endm
    .macro pl_TowerBpAdd value
    pl_ext 0x81
    .short \value
    .endm
    .macro pl_TowerBpSub value
    pl_ext 0x82
    .short \value
    .endm
    .macro pl_TowerBpCheck value, var
    pl_ext 0x83
    .short \value
    .short \var
    .endm
    .macro pl_TowerBpWindow x, y
    pl_ext 0x84
    .short \x
    .short \y
    .endm
    .macro pl_TowerBpUpdate
    pl_ext 0x85
    .endm
    .macro pl_TowerCheckParty mode, var
    pl_ext 0x86
    .short \mode
    .short \var
    .endm
    .macro pl_TowerIsNull var
    pl_ext 0x87
    .short \var
    .endm
    .macro pl_TowerMakePartners
    pl_ext 0x88
    .endm
    .macro pl_TowerPartnerMon partner, mon, species, move
    pl_ext 0x89
    .short \partner
    .short \mon
    .short \species
    .short \move
    .endm
    .macro pl_TowerSetPartner partner
    pl_ext 0x8A
    .short \partner
    .endm
    .macro pl_TowerGetPartner var
    pl_ext 0x8B
    .short \var
    .endm
    .macro pl_TowerPartnerCode var
    pl_ext 0x8C
    .short \var
    .endm
    .macro pl_TowerResumePartner
    pl_ext 0x8D
    .endm
    .macro pl_TowerExchange list, prize, item, cost
    pl_ext 0x8E
    .short \list
    .short \prize
    .short \item
    .short \cost
    .endm
    .macro pl_TowerPlayerCode var
    pl_ext 0x8F
    .short \var
    .endm
    .macro pl_TowerActorVisible actor, value
    pl_ext 0x90
    .short \actor
    .short \value
    .endm

// ---- the smaller finishes of the base game (decomp src/pearlb2/resident/leftovers.c PearlB2_Ext_Leftovers, row 0xA0)
    .macro pl_GetUnownFormsSeenCount var   // 0x284 CountSeenUnown: the Unown forms the Pokédex has seen
    pl_ext 0xA5
    .2byte \var
    .endm
    .macro pl_MoveReminderCheck var, slot  // 0x21F GetMoveReminderCount: Black 2's own: 0 = nothing to remember
    MoveReminderCheckPkm \var, \slot
    .endm
    // 0x221 OpenMoveReminderMenu and 0x223 CheckLearnedReminderMove: Black 2's remembering screen; var = 0 when a move
    // was learned, 255 when not (Pearl's answers)
    .macro pl_OpenMoveReminderMenu slot
    MoveReminderCallMoveSelect PL_TMP3, \slot   // (0 = a move was learned, 1 = cancelled)
    .endm
    .macro pl_CheckLearnedReminderMove var
    WorkSetConst \var, 255
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_NE, .Lpclrm\@     // (MOVE_REMINDER_STATUS_LEARNED 0: scrcmd_proc.c MoveReminder_ReadResult; 1 cancelled)
    WorkSetConst \var, 0
.Lpclrm\@:
    .endm
    .macro pl_SetObjectEventMovementType uid, move   // 0x18D: the person's template (resident/leftovers.c), before they appear
    pl_ext 0xA6
    .2byte \uid
    .2byte \move
    .endm
    // 0x26A BlinkEvent uid, times, delay (pokeplatinum Task_FlickerMapObject): hidden, then shown, every delay frames
    .macro pl_FlickerObject uid, times, delay
    VMJump .Lplfl\@
    .balign 4, 0
.Lplflh\@:
    Move 69, 1
    MoveEnd
.Lplfls\@:
    Move 70, 1
    MoveEnd
.Lplfl\@:
    .rept (\times + 1) / 2
    ActorCmdExec \uid, .Lplflh\@
    ActorCmdWait
    VMSleep \delay
    ActorCmdExec \uid, .Lplfls\@
    ActorCmdWait
    VMSleep \delay
    .endr
    .endm

// ---- Pearl's Secret Base goods in any zone's script (notes/SECRET_BASES.md; decomp resident/secret_base.c, row 0xE0-0xFF;
// each op: one value-or-var argument, its result in work 0x8053; secret_base_check.py compares these numbers with the C's)
    .macro pl_SendGoodToPC good, var           // 0x083 GiveSecretBaseDecoration
    pl_ext 0xE0 + 24
    .2byte \good
    WorkSet \var, 0x8053
    .endm
    .macro pl_CheckHasRoomForGoodsInPC good, var   // 0x085 HasSpaceForDecoration
    pl_ext 0xE0 + 25
    .2byte \good
    WorkSet \var, 0x8053
    .endm
    .macro pl_GetCapturedFlagCount var         // 0x24A
    pl_ext 0xE0 + 27
    .2byte 0
    WorkSet \var, 0x8053
    .endm
    .macro pl_BufferUndergroundGoodsName n, good   // 0x0DF GetDecorationName
    WorkSet 0x8051, \good
    pl_ext 0xE0 + 5
    .2byte \n
    .endm
    .macro pl_GetDecorationNameWithArticle n, good // 0x2C6
    WorkSet 0x8051, \good
    pl_ext 0xE0 + 6
    .2byte \n
    .endm
    .macro pl_GoodsMart list                   // 0x149 GoodsMart: Veilstone's two lists, on the Secret Bases' shop script
    MsgWinCloseAll
    WorkSetConst 0x8057, \list
    RTCallGlobal 10740
    .endm

// ---- Super Contests (notes/CONTESTS.md; decomp src/pearlb2/resident/contest.c PearlB2_Ext_Contest): sub 0xc0-0xd7 of
// PearlB2's extension command 0x15F. A value may be a var.
    .macro pl_ContestEntry slot, rank, type, var   // var = 0 it can enter, else why not
    pl_ext 0xc0
    .2byte \slot, \rank, \type, \var
    .endm
    .macro pl_ContestRun slot, rank, type, mode, var   // the contest; var = the player's place, 0 = first
    pl_ext 0xc1
    .2byte \slot, \rank, \type, \mode, \var
    .endm
    .macro pl_AddAccessory id, count
    pl_ext 0xc3
    .2byte \id, \count
    .endm
    .macro pl_CanFitAccessory id, count, var
    pl_ext 0xc4
    .2byte \id, \count, \var
    .endm
    .macro pl_AddContestBackdrop id
    pl_ext 0xc5
    .2byte \id
    .endm
    .macro pl_CheckContestBackdrop id, var
    pl_ext 0xc6
    .2byte \id, \var
    .endm
    .macro pl_ContestMasterCount var
    pl_ext 0xc7
    .2byte \var
    .endm
    .macro pl_FirstWinAccessory rank, type, var    // the prize of a first win of this rank and type, or 0xFFFF
    pl_ext 0xc8
    .2byte \rank, \type, \var
    .endm
    .macro pl_MassageGirlAccessory var     // Pearl 0x26C: an Accessory the Case can take, else 0xFFFF
    pl_ext 0xc9
    .2byte \var
    .endm
    .macro pl_BufferAccessoryWord word, id // the Accessory's name in word buffer `word`
    pl_ext 0xca
    .byte \word
    .2byte \id
    .endm
    .macro pl_AmityAccessory var, species  // Pearl 0x217: Pearl's Accessory for the next find
    pl_ext 0xcb
    .2byte \var, \species
    .endm
    // Platinum's Amity Square gift man (pokeplatinum scrcmd_amity_square.c sBerryAndAccessoryManOptions: 9 Berries, then 7
    // Accessories; the option is rolled each day): 0x2E1 GetAmitySquareBerryOrAccessoryIDFromMan option, dst
    .macro pl_AmityGiftId option, dst
    WorkSetConst \dst, 176                 // Magost Berry
    WorkCmpConst \option, 1
    VMJumpIf CMP_LT, .Lagi\@
    WorkSetConst \dst, 175                 // Cornn Berry
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 177                 // Rabuta Berry
    WorkCmpConst \option, 2
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 178                 // Nomel Berry
    WorkCmpConst \option, 3
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 179                 // Spelon Berry
    WorkCmpConst \option, 4
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 180                 // Pamtre Berry
    WorkCmpConst \option, 5
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 181                 // Watmel Berry
    WorkCmpConst \option, 6
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 182                 // Durin Berry
    WorkCmpConst \option, 7
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 183                 // Belue Berry
    WorkCmpConst \option, 8
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 11                  // Mini Pebble (Accessories: Pearl's and Platinum's numbers, the same)
    WorkCmpConst \option, 9
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 7                   // Glitter Boulder
    WorkCmpConst \option, 10
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 10                  // Black Pebble
    WorkCmpConst \option, 11
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 16                  // Big Scale
    WorkCmpConst \option, 12
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 27                  // Big Leaf
    WorkCmpConst \option, 13
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 32                  // Thick Mushroom
    WorkCmpConst \option, 14
    VMJumpIf CMP_EQ, .Lagi\@
    WorkSetConst \dst, 33                  // Stump
.Lagi\@:
    .endm
    // 0x2E0 CheckAmitySquareManGiftIsAccessory option, dst: 1 for options 9-15 (Accessories), 0 for the Berries
    .macro pl_AmityGiftIsAccessory option, dst
    WorkSetConst \dst, 0
    WorkCmpConst \option, 9
    VMJumpIf CMP_LT, .Lagc\@
    WorkSetConst \dst, 1
.Lagc\@:
    .endm
    // Platinum's Great Marsh: GetCurrentSafariGameCaughtNum (0x31B) is the Pokémon caught since the Safari Game started.
    // Black 2 keeps no such count, so the start keeps the party's and the boxes' count (pl_SafariCountStart, a saved
    // work) and the end takes it from the count then (0 if it went down: Pokémon released in between)
    .macro pl_SafariCountStart keep
    PokePartyGetCount \keep, 0
    BoxGetCount PL_TMP, 0
    WorkAdd \keep, PL_TMP
    .endm
    .macro pl_SafariCaught var, keep
    PokePartyGetCount \var, 0
    BoxGetCount PL_TMP, 0
    WorkAdd \var, PL_TMP
    WorkCmpWork \var, \keep
    VMJumpIf CMP_LT, .Lsfc0\@
    WorkSub \var, \keep
    VMJump .Lsfc1\@
.Lsfc0\@:
    WorkSetConst \var, 0
.Lsfc1\@:
    .endm
    .macro pl_BufferAccessoryArticle word, id // with an article (Pearl's GetFashionNameWithArticle)
    pl_ext 0xcc
    .byte \word
    .2byte \id
    .endm
// Poffins (decomp src/pearlb2/resident/poffin.c): sub 0xd8-0xdd
    .macro pl_PoffinGive var, spicy, dry, sweet, bitter, sour, smooth // Pearl 0x289
    pl_ext 0xdc
    .2byte \var, \spicy, \dry, \sweet, \bitter, \sour, \smooth
    .endm
    .macro pl_PoffinHasRoom var            // Pearl 0x28A
    pl_ext 0xdd
    .2byte \var
    .endm
    .macro pl_PoffinCanCook var            // Pearl 0x1D8: 0 can, 1 no Berry, 2 the Case is full
    pl_ext 0xd8
    .2byte \var
    .endm
    .macro pl_PoffinCook var               // the cooking screen
    pl_ext 0xd9
    .2byte \var
    .endm
    .macro pl_PoffinCase var               // the Case: var = the slot chosen to give, 0xffff none
    pl_ext 0xda
    .2byte \var
    .endm
    .macro pl_PoffinFeed slot, party, var  // 0 liked, 1 disliked, 2 neutral, 3 it eats no more
    pl_ext 0xdb
    .2byte \slot, \party, \var
    .endm

// ---- Platinum's rooms (step 4, 2026-11-02, plat-rooms; pearl_story's "Platinum's rooms" handlers). Pearl uses none.
// The Regi ruins' dots (pokeplatinum ov5_021F6454.c ScrCmd_ActivateRegiRuinsDot): standing on one of the seven dots
// sets its bit in the ruins' state var with a sound; all seven make the state RUINS_STATE_ACTIVATED_ALL_DOTS. The
// handler writes one pl_RegiRuinsDot per dot of Platinum's table (read from its overlay 5), then pl_RegiRuinsDotsDone.
    .macro pl_RegiRuinsDot var, x, z, dx, dz, bit
    WorkCmpConst \x, \dx
    VMJumpIf CMP_NE, .Lrrd\@
    WorkCmpConst \z, \dz
    VMJumpIf CMP_NE, .Lrrd\@
    SEPlay SEQ_SE_DANSA                    // [guess] Platinum's SEQ_SE_PL_JUMP2: a small hop
    WorkOr \var, \bit
.Lrrd\@:
    .endm
    .macro pl_RegiRuinsDotsDone var, all, state
    WorkCmpConst \var, \all
    VMJumpIf CMP_NE, .Lrrdd\@
    WorkSetConst \var, \state
.Lrrdd\@:
    .endm
// Platinum's CheckPartyHasFatefulEncounterRegigigas (0x32B, scrcmd.c): var = 1 if a party Pokémon that is no Egg is
// Regigigas (486) with the fateful-encounter mark (Black 2's PKM_PARAM_FATEFUL_ENCOUNTER 0x6d, PKM_PARAM_SPECIES 5)
    .macro pl_CheckPartyHasFatefulEncounterRegigigas var
    WorkSetConst \var, 0
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lfrg\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lfrge\@
    PokePartyIsEgg \var, PL_TMP
    WorkCmpConst \var, 0
    VMJumpIf CMP_NE, .Lfrgn\@
    PokePartyGetParam \var, PL_TMP, 5
    WorkCmpConst \var, 486
    VMJumpIf CMP_NE, .Lfrgn\@
    PokePartyGetParam \var, PL_TMP, 0x6d
    WorkCmpConst \var, 0
    VMJumpIf CMP_NE, .Lfrgy\@
.Lfrgn\@:
    WorkAdd PL_TMP, 1
    VMJump .Lfrg\@
.Lfrgy\@:
    WorkSetConst \var, 1
    VMJump .Lfrgx\@
.Lfrge\@:
    WorkSetConst \var, 0
.Lfrgx\@:
    .endm
// A money check past 65535 (Black 2's MoneyCheck takes 16 bits; Platinum's Villa asks up to 220,000): the amount in
// 60,000s, then 15,000s, taken one at a time while the player has them, the rest checked, then everything taken given
// back. var = 1 if the player has the amount. (Pearl's build keeps its 65535 check: pearl_story EXACT_BIG_MONEY.)
// Every amount a money command takes must be under 0x4000 or 0xC000 and over: Black 2 reads 0x4000-0xBFFF as a work or a
// script var (ScriptReadAny), so 1.0.1's 40,000 rest of 100,000 read a var and passed (v101-test, 2026-11-08: the Ribbon
// Syndicate sold the 100,000 ribbon for 89,999 and the split RemoveMoney 34465 took the rest of the money).
    .macro pl_CheckMoneyBig var, amount
    WorkSetConst \var, 0
    WorkSetConst PL_TMP2, 0
    WorkSetConst PL_TMP3, 0
    .rept (\amount / 60000)
    MoneyCheck PL_TMP, 60000
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lcmb_back\@
    MoneySub 60000
    WorkAdd PL_TMP2, 1
    .endr
    .rept ((\amount % 60000) / 15000)
    MoneyCheck PL_TMP, 15000
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lcmb_back\@
    MoneySub 15000
    WorkAdd PL_TMP3, 1
    .endr
    MoneyCheck PL_TMP, ((\amount % 60000) % 15000)
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lcmb_back\@
    WorkSetConst \var, 1
.Lcmb_back\@:
    WorkCmpConst PL_TMP2, 0
    VMJumpIf CMP_EQ, .Lcmb_back2\@
    MoneyAdd 60000
    WorkSub PL_TMP2, 1
    VMJump .Lcmb_back\@
.Lcmb_back2\@:
    WorkCmpConst PL_TMP3, 0
    VMJumpIf CMP_EQ, .Lcmb_end\@
    MoneyAdd 15000
    WorkSub PL_TMP3, 1
    VMJump .Lcmb_back2\@
.Lcmb_end\@:
    .endm
// A question to the zone's PearlB2 gimmick (PVAR_GIMMICK_REQUEST, as pl_gimmick_request): the script sets the
// request, the gimmick's C answers with 0x8000 + the answer; var = the answer (0 if no gimmick answers in \frames)
    .macro pl_gimmick_ask value, var, frames
    WorkSetConst PVAR_GIMMICK_REQUEST, \value
    WorkSetConst PL_TMP, 0
.Lgak\@:
    VMSleep 1
    WorkAdd PL_TMP, 1
    WorkCmpConst PL_TMP, \frames
    VMJumpIf CMP_GE, .Lgakn\@
    WorkCmpConst PVAR_GIMMICK_REQUEST, 0x8000
    VMJumpIf CMP_LT, .Lgak\@
    WorkGet \var, PVAR_GIMMICK_REQUEST
    WorkAnd \var, 0x7fff
    VMJump .Lgakx\@
.Lgakn\@:
    WorkSetConst \var, 0
.Lgakx\@:
    WorkSetConst PVAR_GIMMICK_REQUEST, 0
    .endm
// The Villa's CheckMetFurnitureRequirements furniture + 1, var (pokeplatinum ov5_021F6454.c): the Villa's gimmick
// (decomp src/pearlb2/plat_rooms/villa.c, request 0x100 + furniture) answers from Black 2's records and the flags
    .macro pl_VillaFurnitureRequirement furniture, var
    pl_gimmick_ask (0x100 + \furniture), \var, 30
    .endm
// ---- plat-ch3 (2026-11-07): Platinum's chapter 3 (pearl_story's "plat-ch3" handlers; Platinum only) ----------------
// GetItemQuantity item, var (0x2FE): how many the Bag holds (Black 2's ItemGetCount, ov036 s00B9)
    .macro pl_GetItemQuantity item, var
    ItemGetCount \item, \var
    .endm
// FindPartySlotWithFatefulEncounterSpecies var, species (0x31C, pokeplatinum scrcmd_party.c): the first slot holding no Egg,
// that species (PKM_PARAM_SPECIES 5) and the fateful-encounter mark (PKM_PARAM_FATEFUL_ENCOUNTER 0x6d), else 0xFF
    .macro pl_FindPartySlotWithFatefulEncounterSpecies var, species
    PokePartyGetCount PL_TMP2, 0
    WorkSetConst PL_TMP, 0
.Lfps\@:
    WorkCmpWork PL_TMP, PL_TMP2
    VMJumpIf CMP_GE, .Lfpsn\@
    PokePartyIsEgg \var, PL_TMP
    WorkCmpConst \var, 0
    VMJumpIf CMP_NE, .Lfpsx\@
    PokePartyGetParam \var, PL_TMP, 5
    WorkCmpConst \var, \species
    VMJumpIf CMP_NE, .Lfpsx\@
    PokePartyGetParam \var, PL_TMP, 0x6d
    WorkCmpConst \var, 0
    VMJumpIf CMP_NE, .Lfpsy\@
.Lfpsx\@:
    WorkAdd PL_TMP, 1
    VMJump .Lfps\@
.Lfpsy\@:
    WorkSet \var, PL_TMP
    VMJump .Lfpse\@
.Lfpsn\@:
    WorkSetConst \var, 0xFF
.Lfpse\@:
    .endm
// CheckShouldShowGhost percent, var (0x292, pokeplatinum scrcmd.c): var = 1 when a random 0-100 is at most percent
    .macro pl_CheckShouldShowGhost percent, var
    Random \var, 101
    WorkCmpConst \var, \percent
    VMJumpIf CMP_LE, .Lcsg1\@
    WorkSetConst \var, 0
    VMJump .Lcsg2\@
.Lcsg1\@:
    WorkSetConst \var, 1
.Lcsg2\@:
    .endm

// ---- plat-ch11 (2026-11-07): Platinum's chapter 11 (pearl_story's "plat-ch11" handlers; Platinum only) --------------
// GetRandomBattlegroundTrainers v1, v2, v3, v4 (0x2F4, pokeplatinum scrcmd.c ScrCmd_GetRandomBattlegroundTrainers): v1 one of the
// eight Leaders; v2, then v3, another of them or none (a draw of nine, the ninth none, drawn again while it repeats one, none after
// eight draws); v4 one of the five other Trainers or none (a draw of six). The values are the Black 2 codes l0-l7 and o0-o4 the
// handler passes (the vars fill dynamic sprites), 0xFFF (BATTLEGROUND_TRAINER_NONE) for none. PL_TMP, PL_TMP2 and PL_TMP3 hold the
// Leaders' indexes (8: none) while v1 holds each draw and v4 counts them; the codes are written last.
    .macro pl_bg_draw out, r, tries, a, b
    WorkSetConst \tries, 0
.Lbgd\@:
    Random \r, 9
    WorkCmpConst \r, 8
    VMJumpIf CMP_EQ, .Lbgdx\@
    WorkAdd \tries, 1
    WorkCmpConst \tries, 8
    VMJumpIf CMP_GE, .Lbgdn\@
    WorkCmpWork \r, \a
    VMJumpIf CMP_EQ, .Lbgd\@
    WorkCmpWork \r, \b
    VMJumpIf CMP_EQ, .Lbgd\@
    VMJump .Lbgdx\@
.Lbgdn\@:
    WorkSetConst \r, 8
.Lbgdx\@:
    WorkSet \out, \r
    .endm
    .macro pl_bg_pick out, idx, n, code
    WorkCmpConst \idx, \n
    VMJumpIf CMP_NE, .Lbgp\@
    WorkSetConst \out, \code
.Lbgp\@:
    .endm
    .macro pl_bg_leader out, idx, l0, l1, l2, l3, l4, l5, l6, l7
    WorkSetConst \out, 0xFFF
    pl_bg_pick \out, \idx, 0, \l0
    pl_bg_pick \out, \idx, 1, \l1
    pl_bg_pick \out, \idx, 2, \l2
    pl_bg_pick \out, \idx, 3, \l3
    pl_bg_pick \out, \idx, 4, \l4
    pl_bg_pick \out, \idx, 5, \l5
    pl_bg_pick \out, \idx, 6, \l6
    pl_bg_pick \out, \idx, 7, \l7
    .endm
    .macro pl_GetRandomBattlegroundTrainers v1, v2, v3, v4, l0, l1, l2, l3, l4, l5, l6, l7, o0, o1, o2, o3, o4
    Random PL_TMP, 8
    pl_bg_draw PL_TMP2, \v1, \v4, PL_TMP, PL_TMP
    pl_bg_draw PL_TMP3, \v1, \v4, PL_TMP, PL_TMP2
    pl_bg_leader \v1, PL_TMP, \l0, \l1, \l2, \l3, \l4, \l5, \l6, \l7
    pl_bg_leader \v2, PL_TMP2, \l0, \l1, \l2, \l3, \l4, \l5, \l6, \l7
    pl_bg_leader \v3, PL_TMP3, \l0, \l1, \l2, \l3, \l4, \l5, \l6, \l7
    Random PL_TMP, 6
    WorkSetConst \v4, 0xFFF
    pl_bg_pick \v4, PL_TMP, 0, \o0
    pl_bg_pick \v4, PL_TMP, 1, \o1
    pl_bg_pick \v4, PL_TMP, 2, \o2
    pl_bg_pick \v4, PL_TMP, 3, \o3
    pl_bg_pick \v4, PL_TMP, 4, \o4
    .endm
// ---- end plat-ch11

// ---- plat-ch7 (2026-11-07): Platinum's chapter 7 (pearl_story's "plat-ch7" handlers; Platinum only) ----------------
// The Move Deleter (Canalave's east house, pokeplatinum scripts_canalave_city_east_house.s). 0x1C6 SelectPartyMonMove slot
// opens the summary's move list (FieldSystem_OpenSummaryScreenSelectMove) between a fade-out and ReturnToField + a fade-in,
// which the generator drops; 0x1C7 GetSelectedPartyMonMove var then gives the move slot 0-3, or MOVE_NOT_SELECTED 0xFF.
// Black 2's own: CallPokeMoveReplace with no new move (move 0: the summary in its forget-HM mode, any move can go; ov020
// EventPokeMoveReplace fades, closes and reopens the field itself), its "forgot" answer 1 with the slot. The answer waits in
// PL_TMP3 / PL_TMP2 for pl_GetSelectedPartyMonMove, right after it in Platinum's script.
    .macro pl_SelectPartyMonMove slot
    CallPokeMoveReplace PL_TMP3, PL_TMP2, \slot, 0
    .endm
    .macro pl_GetSelectedPartyMonMove var
    WorkSet \var, PL_TMP2
    WorkCmpConst PL_TMP3, 1
    VMJumpIf CMP_EQ, .Lgsm\@
    WorkSetConst \var, 0xFF
.Lgsm\@:
    .endm
// 0x1CB BufferPartyMoveName arg, slot, move slot: the name of that Pokemon's move in that slot (Black 2's PokePartyGetMove,
// WordSetMoveName)
    .macro pl_BufferPartyMoveName arg, slot, mslot
    PokePartyGetMove PL_TMP, \slot, \mslot
    WordSetMoveName \arg, PL_TMP
    .endm

// ---- plat-dw-world (2026-11-07): Platinum's Distortion World (pearl_story.py block "plat-dw-world"; notes/PLATINUM_DW.md "The
// world"). PearlB2 extension sub-commands 0x20-0x24, the row the Underground never took (include/pearlb2/ext_cmd.h
// PEARLB2_EXT_DIST_WORLD; resident/plat_dw_hooks.c PearlB2_Ext_DistWorld): 0x20 is resident (the warp into the Distortion World
// starts at Spear Pillar), 0x21-0x24 the engine's overlay answers while it runs (Black 2's own values when it doesn't).
    .macro pl_DWWarp                        // 0x320 DoDWWarp: the swirl into the Distortion World (the script waits)
    pl_ext 0x20
    .endm
    .macro pl_DWGetPlayer3DPos x, y, z      // 0x317 GetPlayer3DPos: the player's tile and height in Platinum's world
    pl_ext 0x21
    .2byte \x
    .2byte \y
    .2byte \z
    .endm
    .macro pl_DWGiratinaShadow index        // 0x321 StartDistortionWorldGiratinaShadowEvent (value or var)
    pl_ext 0x22
    .2byte \index
    .endm
    .macro pl_DWGiratinaShadowFinish        // 0x322 FinishDistortionWorldGiratinaShadowEvent: waits for the flight's end
    pl_ext 0x23
    .endm
    .macro pl_DWResetCameraAngles           // 0x31F ResetDistortionWorldPersistedCameraAngles
    pl_ext 0x24
    .endm
    .macro pl_PlatSound n                   // (plat-dw-rom) one of Platinum's own sounds (PLATSND_*: 0 SYUWA, 10 KUSARI; value or var)
    pl_ext 0x25
    .2byte \n
    .endm
// 0x314 GetBattleResult var after a wild battle: Platinum's BATTLE_RESULT_ from Black 2's answers (WildBattleIsVictory: 0 lost;
// WildBattleGetResult: 0 caught, 1 fled / a draw, 2 knocked out): 2 LOSE, 4 CAPTURED_MON, 1 WIN, 5 PLAYER_FLED
    .macro pl_GetBattleResult var
    WildBattleIsVictory \var
    WorkCmpConst \var, 0
    VMJumpIf CMP_NE, .Lgbr1\@
    WorkSetConst \var, 2
    VMJump .Lgbr9\@
.Lgbr1\@:
    WildBattleGetResult \var
    WorkCmpConst \var, 0
    VMJumpIf CMP_NE, .Lgbr2\@
    WorkSetConst \var, 4
    VMJump .Lgbr9\@
.Lgbr2\@:
    WorkCmpConst \var, 2
    VMJumpIf CMP_NE, .Lgbr3\@
    WorkSetConst \var, 1
    VMJump .Lgbr9\@
.Lgbr3\@:
    WorkSetConst \var, 5
.Lgbr9\@:
    .endm
// ---- end plat-dw-world

// ---- plat-frontier (2026-11-07): Platinum's Battle Frontier, its core (notes/PLATINUM_FRONTIER.md; pearl_story's block
// "plat-frontier"; decomp include/pearlb2/plat_frontier.h, src/pearlb2/resident/plat_frontier.c). The Frontier's ops are
// sub-command 0x93 of the Battle Tower's row (EXT_TOWER_FRONTIER), then an op byte, then its arguments (value or var each).
// A frontier script's vars 0x800D-0x8013 (b2tools/frontier_translate.py fvar: the scene manager's last three and the
// context's four) are script works here, kept across RTCallGlobal; no Frontier room runs the Musical, which shares them.
#define FR_VAR_800D 0x8058
#define FR_VAR_800E 0x8059
#define FR_VAR_800F 0x805A
#define FR_VAR_8010 0x805B
#define FR_VAR_8011 0x805C
#define FR_VAR_8012 0x805D
#define FR_VAR_8013 0x805E
    .macro pl_frontier op
    pl_ext 0x93
    .byte \op
    .endm
    // where ExitFrontier goes back to (the launching field script's place: pearl_story FrontierReturn_k)
    .macro pl_FrontierSetReturn site
    pl_frontier 0x00
    .short \site
    .endm
    .macro pl_FrontierGetReturn var
    pl_frontier 0x01
    .short \var
    .endm
    // the shared records: Platinum's BattleFrontierStats by its ids (the Tower's, 0-9, are Black 2's Subway records)
    .macro pl_FrontierStatGet stat, var
    pl_frontier 0x02
    .short \stat
    .short \var
    .endm
    .macro pl_FrontierStatSet stat, value
    pl_frontier 0x03
    .short \stat
    .short \value
    .endm
    .macro pl_FrontierStatAdd stat, value
    pl_frontier 0x04
    .short \stat
    .short \value
    .endm
    .macro pl_FrontierStatBest record, latest
    pl_frontier 0x05
    .short \record
    .short \latest
    .endm
    // a facility's streak flag (0 Factory, 1 Hall, 2 Castle, 3 Arcade; op 0 get, 1 set, 2 clear; bit: the challenge type)
    .macro pl_FrontierStreakFlag facility, op, bit, var
    pl_frontier 0x06
    .short \facility
    .short \op
    .short \bit
    .short \var
    .endm
    // the scene manager's var n (0x8008 + n) kept over a scene change (op 0) and given back (op 1)
    .macro pl_FrontierSceneVar op, n, var
    pl_frontier 0x07
    .short \op
    .short \n
    .short \var
    .endm
    // (plat-fix2) Platinum's tower function 14 after a reset without saving: the saved challenge ends (its round and room
    // again from the start, no streak flag) and its latest streak is 0 (Black 2's BSubwayCmd_Tool 7 keeps it); var = the mode
    .macro pl_TowerDisqualify var
    pl_frontier 0x08
    .short \var
    .endm
    // Platinum's PokeMartFrontier mart: the Exchange Service Corner, on Black 2's BP shop (0 the right counter's TMs: shop
    // 253; 1 the left counter's items: 254), whose lists patches/platinum_frontier.py makes Platinum's
    .macro pl_PokeMartFrontier mart
    .if \mart == 0
    pl_mart 253
    .else
    pl_mart 254
    .endif
    .endm
// ---- end plat-frontier
// ---- plat-factory (2026-11-07): Platinum's Battle Factory (notes/PLATINUM_FRONTIER.md "The Battle Factory"; decomp
// include/pearlb2/plat_factory.h, src/pearlb2/plat_factory/factory.c, overlay 378): the Frontier's ops 0x20-0x30. Each argument
// is a value or a var. pl_FactoryRentScreen, pl_FactorySwapScreen, pl_FactoryBattle and pl_FactoryTrainerIntro run a screen,
// the battle or a balloon: the script goes on after it.
    .macro pl_FactoryInit resuming, type, open
    pl_frontier 0x20
    .short \resuming
    .short \type
    .short \open
    .endm
    .macro pl_FactoryLoadRound resuming
    pl_frontier 0x21
    .short \resuming
    .endm
    // Platinum's CallBattleFactoryFunction fn, arg1, arg2, var
    .macro pl_FactoryFunction fn, arg1, arg2, var
    pl_frontier 0x22
    .short \fn
    .short \arg1
    .short \arg2
    .short \var
    .endm
    // the six rentals on Black 2's battle-entry party screen; the result: 1 three picked, 0 the screen was left (open it again)
    .macro pl_FactoryRentScreen
    pl_frontier 0x23
    .endm
    .macro pl_FactoryRentResult var
    pl_frontier 0x24
    .short \var
    .endm
    // the swap: stage 0 the player's three (one to give), stage 1 the beaten opponent's (one to take; nothing if none given)
    .macro pl_FactorySwapScreen stage
    pl_frontier 0x25
    .short \stage
    .endm
    .macro pl_FactorySwapResult stage
    pl_frontier 0x26
    .short \stage
    .endm
    .macro pl_FactoryAddSelected
    pl_frontier 0x27
    .endm
    .macro pl_FactorySetupNextOpponent
    pl_frontier 0x28
    .endm
    .macro pl_FactoryApplyTrade
    pl_frontier 0x29
    .endm
    .macro pl_FactorySetupNextParty
    pl_frontier 0x2A
    .endm
    .macro pl_FactoryBattle
    pl_frontier 0x2B
    .endm
    .macro pl_FactoryCleanupBattle
    pl_frontier 0x2C
    .endm
    .macro pl_FactoryCheckWon var
    pl_frontier 0x2D
    .short \var
    .endm
    // the opponent's (index 0) line in Black 2's balloon over the room's person
    .macro pl_FactoryTrainerIntro index, actor
    pl_frontier 0x2E
    .short \index
    .short \actor
    .endm
    .macro pl_FactoryFree
    pl_frontier 0x2F
    .endm
    // the lobby's DeleteActiveBattleFactoryStreak
    .macro pl_FactoryDeleteStreak type, open
    pl_frontier 0x30
    .short \type
    .short \open
    .endm
// ---- end plat-factory
// ---- plat-hall (2026-11-07): Platinum's Battle Hall, Frontier ops 0x40-0x4e (decomp include/pearlb2/plat_hall.h PLATHALL_OP_*,
// src/pearlb2/plat_hall/hall_field.c; notes/PLATINUM_FRONTIER.md "The Battle Hall"). Arguments: a value or a var each.
    .macro pl_HallInit resuming, type, slot1, slot2     // InitBattleHall
    pl_frontier 0x40
    .short \resuming
    .short \type
    .short \slot1
    .short \slot2
    .endm
    .macro pl_HallFunction fn, arg1, arg2, var          // CallBattleHallFunction (BH_FUNC_*)
    pl_frontier 0x41
    .short \fn
    .short \arg1
    .short \arg2
    .short \var
    .endm
    .macro pl_HallSetupNextOpponent                     // BattleHall_SetupNextOpponent
    pl_frontier 0x42
    .endm
    .macro pl_HallFree                                  // FreeBattleHall
    pl_frontier 0x43
    .endm
    .macro pl_HallStartBattle                           // BattleHall_StartBattle (the script waits for the battle)
    pl_frontier 0x44
    .endm
    .macro pl_HallCleanupBattle                         // BattleHall_CleanupBattle
    pl_frontier 0x45
    .endm
    .macro pl_HallCheckWonBattle var                    // BattleHall_CheckWonBattle
    pl_frontier 0x46
    .short \var
    .endm
    .macro pl_HallUpdateWinRecord var                   // BattleHall_UpdateWinRecord
    pl_frontier 0x47
    .short \var
    .endm
    .macro pl_HallTrainerIntro slot, person          // (plat-test) the opponent's line in Black 2's balloon over the
    pl_frontier 0x48                                    // person (PrintTrainerIntro: the Factory's way)
    .short \slot
    .short \person
    .endm
    .macro pl_HallTypeList summary                      // the grid's 17 types and the summary row (a line of the zone's text)
    pl_frontier 0x49                                    // into the list menu the script opened (OpenBattleHallApp)
    .short \summary
    .endm
    .macro pl_HallTypeCheck cell, var                   // 0 the cell can be picked, 1 not, 2 Argenta comes next
    pl_frontier 0x4A
    .short \cell
    .short \var
    .endm
    .macro pl_HallTypeWords cell, typeWord, rankWord    // the type's name and its rank (as the grid shows it) into words
    pl_frontier 0x4B
    .short \cell
    .short \typeWord
    .short \rankWord
    .endm
    .macro pl_HallSetCell cell                          // the type grid's answer (BattleHall_GetTypeSelectionAppResult)
    pl_frontier 0x4C
    .short \cell
    .endm
    .macro pl_HallLobbyFunction fn, arg, var            // CallBattleHallLobbyFunction 0-3 (4, the party screen, is the
    pl_frontier 0x4D                                    // Subway's select: pearl_story's handler)
    .short \fn
    .short \arg
    .short \var
    .endm
    .macro pl_HallRecords what, var                     // 0 GetNumSpeciesWithBattleHallRecords, 1 GetBattleHallTotalSingles-
    pl_frontier 0x4E                                    // Record, 2 CheckIfBattleHallStreakIs50
    .short \what
    .short \var
    .endm
    // (plat-fix2) the records machine: the species of letter group g (0 ABC .. 8 YZ) with a record of the type, into the list
    // menu the script opened (ShowBattleHallRecordMonSelectionMenu: Platinum's order; the script adds EXIT)
    .macro pl_HallRecordList type, group
    pl_frontier 0x4F
    .short \type
    .short \group
    .endm
    // (plat-fix2) the records screen's two numbers for a species: its latest streak (0 unless it is the type's latest
    // species) and its record (OpenFrontierRecordsApp, DisplayBattleHallRecord)
    .macro pl_HallSpeciesRecord type, species, latest, record
    pl_frontier 0x50
    .short \type
    .short \species
    .short \latest
    .short \record
    .endm
    // (plat-fix2) the Battle Hall's records screen as a message: "Battle Hall / <type> Record", "<species>'s record",
    // "PREV Win streak: N", "RECORD Win streak: N" (first .. first + 2: Single, Double, Multi; words 0, 1 the numbers, 2 the
    // species). Platinum's Hall shows PREV only (no CURRENT row)
    .macro pl_HallRecordShow type, species, first
    pl_HallSpeciesRecord \type, \species, PL_TMP, PL_TMP2
    WordSetNumber 0, PL_TMP, 0
    WordSetNumber 1, PL_TMP2, 0
    WordSetPokeSpecies 2, \species
    WorkSet PL_TMP, \type
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_EQ, .Lhrs_1\@
    WorkCmpConst PL_TMP, 2
    VMJumpIf CMP_EQ, .Lhrs_2\@
    SystemMsg \first, 2
    VMJump .Lhrs_shown\@
.Lhrs_1\@:
    SystemMsg \first+1, 2
    VMJump .Lhrs_shown\@
.Lhrs_2\@:
    SystemMsg \first+2, 2
.Lhrs_shown\@:
    LastKeyWait
    MsgWinCloseAll
    .endm
// ---- end plat-hall
// ---- plat-castle (2026-11-07): Platinum's Battle Castle, Frontier ops 0x60-0x79 (decomp include/pearlb2/plat_castle.h
// PLATCASTLE_OP_*, src/pearlb2/plat_castle/castle_field.c; notes/PLATINUM_FRONTIER.md "The Battle Castle"). Arguments: a value or
// a var each. pl_CastleBattle and pl_CastleSelfScreen run the battle or a screen: the script goes on after it.
    .macro pl_CastleInit resuming, type, slot1, slot2, slot3   // InitBattleCastle
    pl_frontier 0x60
    .short \resuming
    .short \type
    .short \slot1
    .short \slot2
    .short \slot3
    .endm
    .macro pl_CastleLoadRound resuming                  // LoadTrainersForRound
    pl_frontier 0x61
    .short \resuming
    .endm
    .macro pl_CastleFunction fn, arg1, arg2, var        // CallBattleCastleFunction (BC_FUNC_*)
    pl_frontier 0x62
    .short \fn
    .short \arg1
    .short \arg2
    .short \var
    .endm
    .macro pl_CastleFree                                // FreeBattleCastle
    pl_frontier 0x63
    .endm
    .macro pl_CastleSetupFirstOpponent                  // BattleCastle_SetupFirstOpponent
    pl_frontier 0x64
    .endm
    .macro pl_CastleSetupNextOpponent                   // BattleCastle_SetupNextOpponent
    pl_frontier 0x65
    .endm
    .macro pl_CastleBattle                              // BattleCastle_StartBattle (the script waits for the battle)
    pl_frontier 0x66
    .endm
    .macro pl_CastleCleanupBattle                       // BattleCastle_CleanupBattle: the party back as it left the battle
    pl_frontier 0x67
    .endm
    .macro pl_CastleCheckWonBattle var                  // BattleCastle_CheckWonBattle
    pl_frontier 0x68
    .short \var
    .endm
    .macro pl_CastleTrainerIntro slot, person          // (plat-test) the opponent's line in Black 2's balloon over the
    pl_frontier 0x69                                    // person (PrintTrainerIntro: the Factory's way)
    .short \slot
    .short \person
    .endm
    .macro pl_CastleGetCP type, var                     // GetCurrentCastlePoints
    pl_frontier 0x6A
    .short \type
    .short \var
    .endm
    .macro pl_CastleSpendCP type, cp                    // SpendCastlePoints
    pl_frontier 0x6B
    .short \type
    .short \cp
    .endm
    .macro pl_CastleReceiveCP type, cp                  // ReceiveCastlePoints
    pl_frontier 0x6C
    .short \type
    .short \cp
    .endm
    .macro pl_CastleLobbyFunction fn, arg, var          // CallBattleCastleLobbyFunction 0-3 (4, the party screen, is the
    pl_frontier 0x6D                                    // Subway's select: pearl_story's handler, as the Tower's and the Hall's)
    .short \fn
    .short \arg
    .short \var
    .endm
    .macro pl_CastleDeleteStreak type                   // DeleteActiveBattleCastleStreak
    pl_frontier 0x6E
    .short \type
    .endm
    .macro pl_CastleSelfScreen                          // the self screen's Pokémon: Black 2's battle-entry party screen
    pl_frontier 0x6F
    .endm
    .macro pl_CastleSelfPick var                        // its pick: the slot (0-2), 0xFF for none
    pl_frontier 0x70
    .short \var
    .endm
    .macro pl_CastleAsk kind, slot, arg, var            // a purchase's checks before its yes/no (PLATCASTLE_BUY_*,
    pl_frontier 0x71                                    // PLATCASTLE_RESULT_*); its cost into word 0
    .short \kind
    .short \slot
    .short \arg
    .short \var
    .endm
    .macro pl_CastleBuy kind, slot, arg, var            // its checks after the yes, and the purchase
    pl_frontier 0x72
    .short \kind
    .short \slot
    .short \arg
    .short \var
    .endm
    .macro pl_CastleRentalList items                    // the rental list's rows (0 Berries, 1 items) into the list menu
    pl_frontier 0x73
    .short \items
    .endm
    .macro pl_CastleOpponentList unknown                // the opponent's Pokémon into the list menu (unknown: the line of
    pl_frontier 0x74                                    // one not identified)
    .short \unknown
    .endm
    .macro pl_CastleMonWords side, slot, what           // a Pokémon's words (0 species and HP, 1 the summary, 2 the moves)
    pl_frontier 0x75
    .short \side
    .short \slot
    .short \what
    .endm
    .macro pl_CastleInfo what, slot, var                // 0-2 a rank, 3-5 identity, stats, moves bought, 6 the level change,
    pl_frontier 0x76                                    // 7 the party's count
    .short \what
    .short \slot
    .short \var
    .endm
    .macro pl_CastleCPWord word                         // the CP now into a word (the CP window)
    pl_frontier 0x77
    .short \word
    .endm
    .macro pl_CastleLobbySelect type                    // the lobby's party screen (CallBattleCastleLobbyFunction 4)
    pl_frontier 0x78
    .short \type
    .endm
    .macro pl_CastleSelectedSlots var1, var2, var3      // GetBattleCastleSelectedSlots
    pl_frontier 0x79
    .short \var1
    .short \var2
    .short \var3
    .endm
// ---- end plat-castle
// ---- plat-arcade (2026-11-07): Platinum's Battle Arcade, Frontier ops 0x80-0x8F (decomp include/pearlb2/plat_arcade.h
// PLATARCADE_OP_*, src/pearlb2/plat_arcade/arcade_field.c; notes/PLATINUM_FRONTIER.md "The Battle Arcade"). Arguments: a value or
// a var each. pl_ArcadeBattle, pl_ArcadeBoard and pl_ArcadeLobbySelect run the battle, the game board or a screen: the script
// goes on after it.
    .macro pl_ArcadeInit resuming, type, slot1, slot2, slot3   // InitBattleArcade
    pl_frontier 0x80
    .short \resuming
    .short \type
    .short \slot1
    .short \slot2
    .short \slot3
    .endm
    .macro pl_ArcadeLoadRound resuming                  // BattleArcade_LoadTrainersForRound
    pl_frontier 0x81
    .short \resuming
    .endm
    .macro pl_ArcadeFunction fn, arg1, arg2, var        // CallBattleArcadeFunction (BA_FUNC_*)
    pl_frontier 0x82
    .short \fn
    .short \arg1
    .short \arg2
    .short \var
    .endm
    .macro pl_ArcadeFree                                // FreeBattleArcade
    pl_frontier 0x83
    .endm
    .macro pl_ArcadeSetupFirstOpponent                  // BattleArcade_SetupFirstOpponent
    pl_frontier 0x84
    .endm
    .macro pl_ArcadeSetupNextOpponent                   // BattleArcade_SetupNextOpponent
    pl_frontier 0x85
    .endm
    .macro pl_ArcadeBattle                              // BattleArcade_StartBattle (the script waits for the battle)
    pl_frontier 0x86
    .endm
    .macro pl_ArcadeCleanupBattle                       // BattleArcade_CleanupBattle
    pl_frontier 0x87
    .endm
    .macro pl_ArcadeCheckWonBattle var                  // BattleArcade_CheckWonBattle
    pl_frontier 0x88
    .short \var
    .endm
    .macro pl_ArcadeTrainerIntro slot, person          // (plat-test) the opponent's line in Black 2's balloon over the
    pl_frontier 0x89                                    // person (PrintTrainerIntro: the Factory's way)
    .short \slot
    .short \person
    .endm
    .macro pl_ArcadeApplyEffect                         // ApplyArcadeEffect
    pl_frontier 0x8A
    .endm
    .macro pl_ArcadeBoard first                         // OpenBattleArcadeApp: the game board (the script waits for its stop);
    pl_frontier 0x8B                                    // `first`: the first of the room's 32 lines naming the effects
    .short \first
    .endm
    .macro pl_ArcadeLobbyFunction fn, arg, var          // CallBattleArcadeLobbyFunction 0-3
    pl_frontier 0x8C
    .short \fn
    .short \arg
    .short \var
    .endm
    .macro pl_ArcadeDeleteStreak type                   // DeleteActiveBattleArcadeStreak
    pl_frontier 0x8D
    .short \type
    .endm
    .macro pl_ArcadeLobbySelect type                    // the lobby's party screen (CallBattleArcadeLobbyFunction 4)
    pl_frontier 0x8E
    .short \type
    .endm
    .macro pl_ArcadeSelectedSlots var1, var2, var3      // GetBattleArcadeSelectedSlots
    pl_frontier 0x8F
    .short \var1
    .short \var2
    .short \var3
    .endm
// ---- end plat-arcade
// ---- plat-stubs (2026-11-08): the stubs a Platinum player still reached (pearl_story.py block "plat-stubs") ---------------
// Platinum 0x31E TryRevertPokemonForm slot, var (pokeplatinum ov5_021F6454.c): a Rotom in an appliance back to form 0 (Black 2's
// PokePartyChangeRotomForme: its appliance move goes, Thunder Shock if none is left), a Sky Forme Shaymin to its Land Forme;
// var 0. Giratina keeps its Griseous Orb here (no command for a held item; Platinum puts the Orb in the Bag, 255 if it's full).
// slot is a var (255: none picked); it may be var itself (the Tower's VAR_RESULT, VAR_RESULT): read first, as Platinum's
    .macro pl_TryRevertPokemonForm slot, var
    WorkSet PL_TMP2, \slot
    WorkSetConst \var, 0
    WorkCmpConst PL_TMP2, 255
    VMJumpIf CMP_EQ, .Lprf_end\@
    PokePartyGetForme PL_TMP, PL_TMP2
    WorkCmpConst PL_TMP, 0
    VMJumpIf CMP_EQ, .Lprf_end\@
    PokePartyGetParam PL_TMP3, PL_TMP2, 5      // PKM_PARAM_SPECIES
    WorkCmpConst PL_TMP3, 479                  // SPECIES_ROTOM
    VMJumpIf CMP_NE, .Lprf_shaymin\@
    PokePartyChangeRotomForme PL_TMP2, 0, 0
    VMJump .Lprf_end\@
.Lprf_shaymin\@:
    WorkCmpConst PL_TMP3, 492                  // SPECIES_SHAYMIN
    VMJumpIf CMP_NE, .Lprf_end\@
    PokePartySetForme PL_TMP2, 0
.Lprf_end\@:
    .endm
// ---- end plat-stubs
