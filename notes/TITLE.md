# Title screen (plan, 2026-10-18)

User's choice (question 7): a custom Gen 5-style top screen like Ruby/Sapphire/Emerald NDS; the bottom screen is
Pearl's own title bottom screen with Palkia's outline, taken straight from the Pearl dump.

## Pearl's title (pokediamond files/demo/title/titledemo/, = the dump's demo/title/titledemo.narc)
- file 3: the "Pokémon Pearl Version" logo (file 1 is Diamond's), 256x128, 8 bpp.
- file 15: "© 2007 GAME FREAK inc." line; files 0/8/12/17 screens, 2/4/9/10/13/14/16 palettes.
- **Palkia's outline is 3D**: file 5 `title_air` (textures `pal`, `air_pink`, `air_blinn`, `outUV1`: the pink
  energy aura) + texture animation file 18 (NSBTA) scrolling the aura over Palkia's silhouette. File 6 `title_iar`
  + 19 are Dialga's (Diamond, later).

## Black 2's title (HoennB2 notes/RESEARCH_TITLE.md; overlay 162, fully decompiled: src/ov162/title.c)
- Top (sub engine): the logo is an 8 bpp BG (a/0/2/6 files 0/1/2) over a crystal strip (file 3) and PRESS START.
- Bottom (main engine): 3D Black Kyurem (a/1/5/8 446-453) through a motion blur, credit line on BG3 (a/0/2/6 8/9/10).

## Plan
1. Top: a new Gen 5-style "Pokémon Pearl" logo, 3 drafts for the user to pick (HoennB2 b2tools/title_art.py
   drafts the Hoenn logos; its packer writes a/0/2/6 0/1/2/3), Black 2's crystal strip and PRESS START.
2. Bottom: replace TitleG3D_Init/Draw/Free (as HoennB2's patches/title_scene.c does) with code that loads Pearl's
   Palkia model (file 5, its own textures) and texture animation (file 18) and draws them with a fixed camera;
   Pearl's copyright line on BG3; no motion blur, no 29 s swap; Palkia's cry on Start (cry species literal).
3. Skip Black 2's opening movie (HoennB2: arm9 0x02036332 `movs r0, #2` -> `#3`).
Needs: copy HoennB2's title_art.py / title_scene.c pieces (read-only source), a test build (disk), user's logo pick.

## Built and tested (2026-10-18, DeSmuME)
- `b2tools/patches/pearl_title.py`: top = logo draft 3 (user's pick) over the pink-tinted crystal strip, PRESS START;
  bottom = Pearl's Palkia (titledemo 5 + 18 appended to a/1/5/8 479/480) as the title scene's only actor.
- Black 2's title code loops over 3 actors (bind, draw, step, set frame) whatever the setup says: with 1 actor and
  the loops at 3 the game crashed into VRAM (PC 0x06369000); the four `cmp #3` -> `#1` (addresses by bytes:
  0x0219d5b6, d756, d7a0, d836; armdis's listing drifts by 2 after a literal pool).
- Black 2's camera path framed Kyurem (Palkia filled the screen): the per-frame `bl GFL_G3DCurveApplyCamera`
  (0x0219d726) is removed and the camera's position/target (sCameraPosition 0x021A148C, sCameraTarget 0x021A1498)
  are set: (-105, -30, 25) looking at (0, 0, -10), tuned by eye against a DeSmuME shot of Pearl's own title
  (work/pearl_ref): Palkia side-on, head and arm at the right, striped wing up-left, tail down-left.
  Tuning: `b2tools/hwtest/title_tune.sh "x y z" "tx ty tz" tag` (title-only build, ~2 min).
- Open: Pearl's aura flashes on/off (its title alternates the aura brightness); here the texture animation runs but
  no flashing. Pearl's "© 2007 GAME FREAK inc." vs Black 2's "Developed by GAME FREAK inc.": Black 2's kept, as in
  the Hoenn games.

## Pokémon Lustrous Pearl and Pokémon Adamant Diamond (user's new names and pick, 2026-11-01)
- Logo: **draft C** of `b2tools/title_lustrous.py`, the whole name on one line on a plaque, with a string of pearls and the
  Lustrous Orb below it (Diamond: steel plaque, a string of small cut diamonds, the Adamant Orb's cut gem). Black 2's wordmark, strip and PRESS START stay.
  Drafts A (chrome stack) and B (orb emblem) stay in that file. Its letters are thresholded to whole pixels, not averaged
  like title_art's earlier drafts, and rims go around the whole word so they can't fill a counter (a pale rim read as a
  hollow second letter at 1x). `python3 title_lustrous.py use C` writes data/title/ and data/title/diamond/; draft C is
  345 (Diamond 372) of 512 tiles, 31 (33) colours for the lettering. The old data/title/drafts/ are the Pearl-only logos.
- Version: `PEARL_VERSION=diamond` makes pearl_title.py take data/title/diamond/ and titledemo files 6 + 19 (Dialga), cry 483.
  Dialga's camera is its own (291, 103, -13 looking at -1, 103, -80): Dialga's model is not centred as Palkia's is (centre -1, 103, -80, 152 x 210 x 324 units; Palkia's camera shows only its legs). Chosen from an offline render with Black 2's frustum that reproduces the DeSmuME shot of Palkia's outline; not seen in game yet. `PEARL_VERSION=diamond b2tools/hwtest/title_tune.sh` tunes it. The Diamond dump must be roms/diamond.nds.
- The name elsewhere, all from `b2tools/version.py` (TITLE, PUBLIC_NAME, HEADER_TITLE, game_names):
  - ROM header "POKEMON LP" / "POKEMON AD", DS menu banner `Pokémon / Lustrous Pearl / Nintendo` with the dump's own icon
    (Pearl's Poké Ball on pink): `b2tools/rom_identity.py`, installed by pearl_title.py, used by build_rom.write_config.
    The game code stays IREO. `python3 rom_identity.py check ROM` reads a built ROM back (also the banner's CRCs).
  - Credits: Pearl's "Pokémon Pearl" line (pearl_credits.py; regenerate data/text_overrides/pearl_credits.json with it).
  - Pal Park migration text (Pearl's bank 403, patches/pal_park.py): the longest line is now 214 px (Diamond) in a 240 px window.
- Left as they are: "Pearl" as an item or in Pearl's story; Pearl's banks 206 and 315 (options, demo: not used here); Black
  2's lines naming Pokémon Black/White (Version) 2 (ability_handlers_2: Memory Link and Key exchange; 0092: Poké Transfer;
  title_8: Xtransceiver, transfer; 0355 and questionnaire_answers: surveys; castelia_city_13): real carts or Black 2 features;
  the copyright screen after the credits (a/2/0/5, Black 2's art and years) and "Developed by GAME FREAK inc.".
