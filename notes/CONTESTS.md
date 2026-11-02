# Super Contests (2026-11-01)

Pearl's Super Contests replace the Musical at Hearthome's counters, in Lustrous Pearl and Adamant Diamond. Sources: Pearl's dump and
pokediamond first, Platinum's C as a reading guide. Link play is cut. Calls the guide left open: notes/DECISIONS.md 2026-11-01.

## What was checked against Pearl (b2tools/contest_check.py)
- **The guide's overlay numbers are Platinum's.** Pearl's Dance, Acting and scoring are overlay 12 (103,008 B); Visual is overlay 17
  (28,288 B; the 5-entry table in pokediamond `asm/unk_02080C38.s`, and it reads imageclip's layout). Pearl's overlay 22 is something else.
- Pearl and Diamond: contest code the same but for a few literals of arm9 addresses; all data files byte for byte. So no version split.
- Pearl's AI table (165 rows), type chart, fixed-order keys, Visual steps: where Platinum has them.
- **Pearl differs from Platinum:** Dance has two songs, not seven: Normal and Great SEQ_CO_KASHI (120 BPM, 3 steps), Ultra and Master
  SEQ_CO_TAKUMA (120 BPM, 4 steps), no 12-beat grid (ov12_02230BE4). Platinum's other songs and grid are not used.
- Not compared line by line: the rest of overlay 12's asm against Platinum's C. The tables above held, so the logic is taken as Platinum's.

## The beat
Pearl's VBlank reads `GF_SndPlayerGetTick(7)` and computes frames as (framesPerBeat / 48) x tick. Black 2 has `GFL_SndBGMGetTick`, the same
`NNS_SndPlayerGetTick` (gym_elec.c uses it). contest_dance.c takes the frame from the tick on every pass and runs each new frame once.

## Poffins (2026-11-01)
Rules `resident/poffin_rules.c` (host-safe), save and commands `resident/poffin.c` (ext 0xD8-0xDD: can cook, cook, Case, feed, give, has room), screens `contest/contest_poffin.c`. Pearl's overlay 73 has Platinum's overlay083 tables at 0x21DBF5C on (`contest_check.py`), so Platinum's C is the guide. `contest_host/poffin_sim.c` cooks too slowly, too fast, watching the pot, and not at all.
The ways in: Hearthome's Poffin House counter (object 3 → global script 10788), the Case from the Bag (item 449 in the Bicycle's Use row; common event → 10789), Pearl's own gift in the Contest Hall lobby (GivePoffin, CheckHasEmptyPoffinCaseSlot); the Case itself is Pearl's Fan Club gift. Pearl has no Poffin vendor. Feeding: Pearl's flavor table per nature, Pearl's limit (Sheen 255 eats no more), friendship +1.
The pot is Pearl's six 3D sprites as: the plate on BG 3, the rim on BG 2 (palette 35, 36, 37 by phase), the batter as a turning OBJ (42, 44, 46; four 64 x 64 blocks), the ring on BG 1, the arrow 32/31/30 with palette 33: pixel for pixel, `bitmap_ncgr`, `batter_ncgr`.
Stand-ins: the rim and ring don't turn (only the batter does); Pearl's burn and overflow puffs (20, 23, 26) and DONE! banner (29) aren't drawn, the lines say it; a plain list for the Bag when choosing a Berry; A/B for "keep cooking?"; the Case's flavors as numbers on Pearl's pentagon, not its graph; YES/NO without the question line when trashing; closing the Case returns to the field, not the Bag. Group cooking is link play, cut. To check on the combined ROM: the batter's turning direction against the finger (`UpdateStirSprites`) and seams between its four blocks.

## Files
Decomp, branch `pearlb2-contests`: `include/pearlb2/contest.h` (rules, host-safe), `contest_port.h`, `contest_app.h` (archive layout, save,
commands), `contest_ui.h`, `contest_text_ids.h` (generated); `src/pearlb2/contest/`: `contest_rules.c`, `contest_app.c` (driver, shared UI),
`contest_acting.c`, `contest_dance.c`, `contest_visual.c` (dress-up, scoring), `contest_results.c`, generated `.inc`;
`src/pearlb2/resident/contest.c` (ext commands 0xC0-0xCC, entry rule, ribbons, save). `tools/pearlb2/link_overlays.py`, `configure.py`: overlay 373.
Tree: `b2tools/contest_data.py` (`inc` regenerates tables, text ids, reception text), `contest_check.py`, `contest_host/` (`run.sh`: AI-only contests
under sanitizers), `patches/contests.py`, `src/field_scripts/1282_global_contests.s`, `src/text/script/0413_contests.txt`.
Art: archive a/0/5/1 (the Musical's Pokémon pictures), 459 members, 948 KB: Pearl's contest_bg, contest_obj, imageclip, nutmixer, poru_gra unpacked. The 100 Accessories are
linear bitmaps for Pearl's 3D sprites: `clip_ncgr` rewrites them as OBJ tiles, the same pixels.

## Condition stats (for Poffins)
`PKM_PARAM_CONTEST_COOL + i` in CONTEST_COOL, BEAUTY, CUTE, SMART, TOUGH, SHEEN order, 0-255, read in contest_app.c FillPlayer. Poffins raise those fields; nothing
else is needed. Ext rows 0xD8-0xDF: `PearlB2_Ext_Contest` gets sub 0x18-0x1F and has no case for them yet. **The save doesn't fit the brief:** block 42 is 676 B, so
Pearl's 800 B Case can't go there; 108 B are free at +0x1EC.

## Stands in for Pearl's art (the art exists; only sprite scripting is missing)
Hearts, Voltage stars and result bars: numbers in windows (asked for as Pearl's sprites 2026-11-01; left as windows, each needs its sprite scripting and a look on a ROM: Pearl's contest_obj chars/cells/anims 17/16/15, 20/19/18, 26/25/24, 29/28/27, 23/22/21, 73/74/75 with palette 7, bars 90/89/88, 93/92/91, 96/95/94; Platinum's ov17_022413D8.c and ov17_0223F118.c). Judges aren't on stage. Dancers hop instead of Pearl's animations. Black 2's frame and message window, Black 2's
sound effects (Pearl's SEQ_SE_DP_CON_* aren't installed; five Pearl songs are). A Pokémon's move type on a card is the word, not Pearl's icon.

## First play (2026-11-02)
Pearl's contest_bg is Platinum's numbers minus one from member 11 on: Visual's scoring stage 22/21 with palette 34 (curtain 23/20 not raised), the audience 18/19 with 33 on the touch screen in scoring and results; Dance stage 13/14 with 31, panel palette 32; Acting's cards take Platinum's type colours in rows 4-7 (`sMoveTypeColors`) on panel palette 39; results board 26/24 with 38. A Dance frame is two VBlanks: presses are latched in `danceInput`. Stand-ins seen on screen: the dressed Pokémon isn't in the top frame (the theme and clock on the shelf's panel); the backdrop stays Pearl's first. Changed from Pearl for this: the how-to (bank 337 line 47, `contest_data.py` LINE_EDITS) says the rank's real limit (Pearl's ov17 at 0x2742: 5, 10, 15, 20, Pearl's own line says ten) and drops the backdrop button. Acting's key cursor is a blinking frame drawn in the card's window; the cooking lines clear after two seconds.
