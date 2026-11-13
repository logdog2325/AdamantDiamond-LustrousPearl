# Sinnoh's music in Black 2 (started 2026-10-18)

User's choice: Sinnoh's own songs by default; a start-of-game choice of Black 2's music (with Rowan's questions, later).
Reference: HoennB2 notes/MUSIC.md (Black 2's sound archive, players, sound heap; read-only).

## How
- Pearl's songs are already in the DS sound format (SSEQ/SBNK/SWAR), but they share big instrument archives (field
  songs: bank 1001 over wave archives 1000 + 1001, ~500 KB) that Pearl keeps loaded. Black 2 loads a song's
  sequence + bank + wave archives together (~282 KB free per song, HoennB2's measurement) and stores each song with
  its own bank/archive. `b2tools/pearl_music.py` trims a Pearl song to what it plays (its programs, their
  instruments, only their waves, renumbered into one archive); the sequence is unchanged.
- Sizes (`python3 b2tools/pearl_music.py`): with whole instruments, 78 of the 80 songs fit the estimate (most
  120-220 KB) and SEQ_ROAD_F_D/N (Routes 210, 211 East, 214, 215) was ~291 KB.
- **Measured in game** (2026-10-18, `b2tools/hwtest/music_mem.py`, DeSmuME muted): with Twinleaf's SEQ_TOWN01_D
  (217 KB) playing, Black 2's sound heap had 584,460 of 643,008 bytes used, **58,548 free**. So a song may be about
  275 KB at most; Route 210's 291 KB would not fit.
- **Key-level trimming** (2026-10-18): drum sets and key splits hold one sample per key or key range, and a song
  plays only a few. `pearl_music.trim` now keeps only the samples of the notes the song plays (it follows every
  track's notes with its current instrument and transpose); a region no note reaches stays in place but points at a
  sample already kept. All 77 songs: **12.6 MB -> 6.5 MB**; the biggest is now SEQ_ROAD_F_N at **161 KB** (Route 210
  fits with ~110 KB to spare). Checked: for all 11,213 (instrument, key) pairs the 77 songs play, the trimmed bank
  gives the same sample bytes and the same settings as Pearl's. A song whose tracks use random/variable/condition
  commands or open tracks mid-song would keep every sample (none of the 77 does).
- **Measured again in game** with the trimmed songs (2026-10-18, `fish_shot.py ... HEAP` in Twinleaf): 474,220 of
  643,008 bytes used, **168,788 free** (was 58,548). The biggest song (161 KB) therefore fits with room to spare.
- `b2tools/patches/sinnoh_music.py` (after sinnoh_world/sinnoh_rooms): the 52 day themes the installed zones use go in
  as new sequences 4.. with new banks / wave archives (Black 2's empty ids), files appended (SDAT 89.4 -> 97.7 MB);
  every Sinnoh zone's bgm0-3 = its song (Pearl's SEQ_DUMMY "keep playing" -> the parent zone's song); mapping in
  work/world/music.json. Offline dry run: Twinleaf -> SEQ_TOWN01_D. Each new entry also takes ~76 B of sound heap
  (INFO + FAT), ~4 KB in all.

- **Night themes** (sinnoh_music.apply_code): the night versions go in too (77 songs in all, SDAT 89.4 -> 102.0 MB);
  Black 2's DecideZoneHeaderBGMID (arm9 0x02018968) long-jumps to src/code/night_music.c in ITCM (192 B), which plays
  Pearl's night theme in Black 2's NIGHT and MIDNIGHT day periods (25 day/night pairs). Shared tool:
  `b2tools/itcm.py` (compile, HoennB2's ELF linker, append to ITCM and move the arena literal at arm9 0x0207B400).
  Checked offline: the jump bytes, the ITCM growth, the compiled code.

- **Story songs** (2026-10-18): the 12 songs Pearl's scripts start themselves (PlayMusic/SetBGM across all 446 zone
  script files: Barry's SEQ_THE_RIV, Lucas/Dawn SEQ_THE_BOY/GIRL, "follow me" SEQ_TSURETEKE, Rowan's
  SEQ_THE_EVENT01-03, SEQ_SILENCE_DUNGEON, SEQ_OPENING2, SEQ_FUE, SEQ_D_SAFARI, SEQ_D_RYAYHY; 3-108 KB each) go in with
  the zone songs (sinnoh_music EVENT_SONGS). The translated scripts play `SEQ_PEARL_<name>` when the build ran
  sinnoh_music before `scripts`/`sinnoh_story` (the ids reach the assembler through the PEARL_MUSIC_EVENTS
  environment variable, `patches/scripts.py` defines()); otherwise Black 2's stand-ins. Checked: the Lake Verity
  scene assembles both ways and only the song ids differ.

## Battle music (2026-10-25; user: "it should be Pearl's, and same for any other unique Gen 4 battle track")
Rules: data/battle_music.json; patch: b2tools/patches/battle_music.py (after music_choice); code: the decomp's
src/pearlb2/battle_music_itcm.c (branch pearlb2-music). `python3 b2tools/patches/battle_music.py` prints the table.
- **Pearl's rules** (pokediamond): the class -> encounter-music table (arm9/asm/unk_0204AB0C.s UNK_020F4718, 78
  classes, any other class SEQ_EYE_KID); the class -> battle music (unk_02047500.s sub_020475C0 + UNK_020F457E: Gym
  Leaders SEQ_BA_GYM, Elite Four SEQ_BA_TENNO, Cynthia SEQ_BA_CHANP, Barry SEQ_BA_RIVAL, grunts SEQ_BA_GINGA,
  commanders SEQ_BA_GINGA3, Cyrus SEQ_BA_AKAGI, others SEQ_BA_TRAIN); the wild music by species (sub_02047668: Uxie,
  Mesprit, Azelf SEQ_BA_DPOKE1; Dialga, Palkia SEQ_BA_DPOKE2; Rotom, Heatran, Regigigas, Giratina, Darkrai
  SEQ_BA_SECRET2; Arceus SEQ_BA_SECRET1; others SEQ_BA_POKE); the victory by the first opponent's class (overlay 11:
  leaders SEQ_WINTGYM, Elite Four SEQ_WINTENNO, Cynthia SEQ_WINCHAMP, grunts and commanders SEQ_WINGINGA, Cyrus
  SEQ_WINAKAGI (the same notes as WINGINGA, installed once), others SEQ_WINTRAIN; wild SEQ_WINPOKE). Pearl's Elite Four
  battle (BA_TENNO) is the Gym Leader theme note for note. Not built: Pearl's trainer music for a double battle
  against a non-Galactic class (no story double battle has a leader, the Elite Four, Cynthia or Barry as opponent).
- **Black 2's way** (pokebw2): eye contact = GetTrainerClassEyeBGMID (TRAINER_CLASS_RESOURCES) from the scripts'
  TrainerBGMPlayPush (the eye-contact script global_3000), TrainerClassBGMPlayPush and TrainerBGMPlay; battle =
  EventBattleCall_DecideEnvWild / _DecideEnvTrainer (ov036 enceff.c: SPECIAL_TRAINER_BGM by class group, species
  overrides) from ov012 event_battle.c; victory = btl_setup.c BtlSetup_LoadTrainer by class group (WIN1 wild, WIN2
  trainers, WIN3 leaders and Elite Four, WIN4-6 Plasma and Champion), played through GetWinBGM (ov167). Black 2 also
  changes its leader song at the leader's last Pokemon (btl_client.c, SEQ 0x47b) and plays SEQ_BGM_BATTLEPINCH at low
  HP (btlv_gauge.c); the BGM stack frees a pushed song's waves, so one song's waves are in the sound heap at a time.
- **Installed**: 35 Pearl songs (34 sequences; the biggest SEQ_BA_CHANP 143,712 B trimmed, budget 282,000); the decomp
  calls PearlB2_EyeBGM / PearlB2_DecideEnvWild / PearlB2_DecideEnvTrainer / PearlB2_WinBGM in place of Black 2's
  (same-size call changes) and the leader's last-Pokemon change happens only over Black 2's own SEQ_BGM_VS_GYMLEADER.
  The tables (per Black 2 class: Sinnoh's and Black 2's song for eye contact, battle, victory; per species) are in ITCM
  at gPearlB2BattleMusic. Scripts: Pearl's PlayTrainerEncounterBGM (the Elite Four and Cynthia rooms) ->
  pl_PlayTrainerEncounterBGM (TrainerBGMPlay).
- **Black 2's music** (bit 13 = 0): the eye-contact songs per class, trainer and wild battles and their victories are
  Black 2's own; Gym Leaders and the Elite Four VS_DP_LEADER, Cynthia VS_DP_CHAMP (the PWT remixes), her encounter
  E_SHIRONA (Pearl's EYE_CHAMP melody, 0.97), the lake trio VS_UMA and the legendaries VS_DPLEGEND (Black 2's own
  versions of Pearl's tracks: the same notes, 1.00); victories WIN3 (leaders, Elite Four) and WIN5 (Champion). Pearl's
  in both modes: Team Galactic (eye contact, battle, victory), Cyrus, Barry's battle, the Elite Four's encounter,
  Dialga/Palkia, Arceus.
- check_waits (battle_music.py): every pair both ways (471): all these songs loop on both sides.
- **Tested in game** (2026-10-25, DeSmuME muted; the playing sequence read from the GFL BGM stack, 0x0209da74 /
  0x0209da7c + 28 x level, +4; logs in work/agents/music/shots/bgm_*.log; this build's ids: Pearl's battle songs
  90-123): Sinnoh's music: Valley Windworks grunt (eye contact) 93 SEQ_EYE_GINGA -> 112 SEQ_BA_GINGA -> 120
  SEQ_WINGINGA -> the zone's 60; Roark 106 SEQ_BA_GYM through his last Pokemon (no change of song) -> 118
  SEQ_WINTGYM; Route 202 wild Shinx 105 SEQ_BA_POKE -> 116 SEQ_WINPOKE. Black 2's music: the same grunt 93 -> 112 ->
  120 (Pearl's) over the zone's Black 2 song 1195. Sound heap free in those battles: 160-180 KB.

## Open
- Fanfares: done 2026-11-01, Pearl's with Sinnoh's music (patches/sinnoh_music.py JINGLES, Music_Redirect in
  src/code/music_choice.c); Black 2's with Black 2's music.
- Low HP: done 2026-11-01 (DECISIONS 2026-10-25): with Sinnoh's music the battle song plays on and a beep repeats
  (resident/leftovers.c PearlB2_GaugePinch; Black 2's SEQ_SE_BEEP stands in for SEQ_SE_DP_HINSI, once a second).
- Pearl's plain music in double battles (pokeplatinum EncEffects_GetEffectPair): nothing to build. All 23 double Trainers are
  of plain classes (Twins, Young Couple, Double Team, Sis and Bro, Belle & Pa, Interviewers), and only Team Galactic's keep
  their own, as the class table does already.
- The Black 2 music option (Rowan's question) and checking every place where Black 2 waits for a song to end
  (HoennB2's v16 freeze: a looping song where the game waits for a jingle; HoennB2 b2tools check_waits).
- In-game listening test of the trimmed songs and the night themes: next full build.

## Platinum (2026-11-07, plat-music; PEARL_VERSION=platinum)
- **The converter.** Every music patch reads the version's own sound archive (data/sound/pl_sound_data.sdat), so a Platinum
  build installs Platinum's bytes of every song, including the ten Pearl songs Platinum changed (SEQ_CITY11_D, the TV
  jingles, SEQ_BF_TOWWER, SEQ_BA_AKAGI, BA_DPOKE2, BA_CHANP, SEQ_TITLE00/01, SEQ_PRESENT). Its 34 new sequences are
  SEQ_PL_* 1189-1222 (28 .sseq files named SEQ_PL_* in the decomp, plus BATTLE_GIRATINA, BATTLE_REGI_TRIO and the Brains'
  two; SEQ_PL_BICYCLE is SEQ_BICYCLE's file, SEQ_PL_DMY10 a dummy). All 44 go through pearl_music.trim offline
  (work/agents/plat-music/tools/plat_songs.py): every one fits the budget (the biggest SEQ_PL_BA_GIRA, 228,000 B of
  282,000), and for every (program, key) a song plays the trimmed bank gives the same note definition and wave bytes.
- **Installed for Platinum** (where something plays them): the zone themes as sinnoh_music finds them in Platinum's zones
  (the GTS and Global Terminal SEQ_PL_WIFITOWER, Sendoff Spring and the Spring Path SEQ_ROAD_F instead of Pearl's SEQ_D_03,
  the Distortion World SEQ_PL_D_GIRATINA, the Frontier's four BF_* songs); the story songs (version.STORY_SONGS: Looker's
  SEQ_PL_HANDSOME, the Villa's SEQ_PL_PIANO, SEQ_PL_AUDIO and music box SEQ_PL_TOWN02, Spear Pillar's SEQ_PL_EV_GIRA and
  EV_GIRA2, Pearl's Poké Radar song SEQ_KUSAGASA); the Battle Hall's fanfare SEQ_PL_POINTGET3 (with Black 2's ME player, so
  its WaitFanfare ends); the battle songs SEQ_PL_BA_GIRA and SEQ_PL_BA_REGI (battle_music).
- **The Brains** (plat-frontier-rooms, 2026-11-07): SEQ_PL_BA_BRAIN and SEQ_PL_WINBRAIN are installed by battle_music
  (data/battle_music.json "versions": battle and victory of Palmer's class 198 and the four Brains' classes 236-239, Platinum's
  in both music modes: nothing in Black 2 has their notes, melody() at most 0.06). The Factory's and the Hall's tables take
  their ids from it (patches/platinum_factory.py, platinum_hall.py). SEQ_PL_EYEBRAIN is not installed: nothing in Platinum
  plays it (only its sound archive and the sound test list it); the Brains' cut-in plays SEQ_PL_BA_BRAIN.
- **Not installed** (nothing plays them yet): the Frontier's fanfares
  SEQ_PL_DON2, SEQ_PL_FRO and its SEQ_PL_BF_CASTLE02; Platinum's five contest dance songs SEQ_PL_MTKAKKO, MTKASHI, MTKAWA,
  MTTAKMA, MTUTSUK (patches/contests.py keeps Pearl's two dance songs and grid, notes/CONTESTS.md); the Wi-Fi Plaza's and
  its games' SEQ_PL_WIFIGAME, WIFIUNION, WIFIPARADE, WINMINI2, GURUGURU (Spin Trade), SEQ_PL_PTHAIFU. Each converts (above).
- **Scripts** (pearl_story.py block "plat-music"): Platinum's sound ids past Pearl's take Platinum's names (the decomp's
  pl_sound_data.json). SetBGM 1200 (CommonScript_SetLookerBGM: Jubilife, Veilstone, Route 213, Mt. Coronet 2F, Stark
  Mountain 3) and PlayMusic 1197, 1198 (the Villa's piano and audio system) and SEQ_KUSAGASA (Route 202) play as
  SEQ_PEARL_<name>; the music box is Black 2's BGMPlayPush SEQ_PEARL_PL_TOWN02 and BGMPop 0, 0 (the kept song back:
  Platinum's GetCurrentBGM and SetFieldScene); Spear Pillar's cutscene (plat-ch9's 2FB lines) fades the song with line 22,
  plays EV_GIRA before line 24 and EV_GIRA2 before line 26, and stops it at the end, as overlay 100 does. The coins' sound
  SEQ_SE_PL_COIN is Black 2's cash register SEQ_SE_SYS_22 [guess]. SEQ_SE_PL_KUSARI (the red chains) and SEQ_SE_PL_SYUWA
  (the Distortion World's portals) stay counted stubs: Black 2 has no sound found for them, and it plays only the sounds
  its sound groups have loaded (Platinum's own would need C). Regenerate the 14 zones that change: `PEARL_VERSION=platinum
  python3 b2tools/pearl_story.py zones MAP_JUBLIFE MAP_VEILSTONE MAP_VEILSTONE_GAME_CORNER MAP_MOUNT_CORONET_SPEAR_PILLAR
  MAP_MOUNT_CORONET_SOUTH_2F MAP_STARK_MOUNTAIN_INTERIOR_3 MAP_TURNBACK_CAVE_GIRATINA_ROOM MAP_ROUTE_202 MAP_ROUTE_213
  MAP_RESORT_AREA_SOUTHWEST_HOUSE MAP_BATTLE_HALL MAP_DISTORTION_WORLD_1F MAP_DISTORTION_WORLD_GIRATINA_ROOM
  MAP_DISTORTION_WORLD_TURNBACK_CAVE_ROOM` (or `all`); each assembles and passes b2_script_check with and without the song ids.
- **Alternate music** (pearl_alt_music): Platinum's SystemFlag_GetAltMusicForHeader is Pearl's sub_0205EF20 row for row (the
  same 12 flags 0x984-0x995, the same zones under Platinum's names, the same songs); a Platinum build checks RULES against
  the decomp's function (platinum_rules). Platinum's scripts set the same 10 flags (0x985 and 0x98A have no setter in either
  game). Platinum's field music has two more rules (pokeplatinum field_bgm.c FieldBGM_GetEffective, GetForMapHeader), both
  covered or left: (1) Route 206 entered from a Cycling Road gatehouse at x 299-306, z 576 or 681 plays the bike song: here
  the player rides there anyway, and Black 2 plays its bike song while riding (zone_flags enableCycleSurfBGM, Pearl's 1.0
  choice: Black 2's own bike and surf songs); (2) no surf song in the Distortion World's eleven zones: step 7's, by clearing
  zone_flags' surf_bgm bit (14) for those zones. The Poké Radar's chain song is Pearl's rule too (the Radar is closed, as in
  Pearl's 1.0).
- **Battle music** (data/battle_music.json "versions"): Platinum's eye-contact table is Pearl's plus the Maid (Black 2's MAID
  class: SEQ_EYE_FUN); Giratina SEQ_PL_BA_GIRA (Platinum's in both modes: no Black 2 counterpart), the Regi trio
  SEQ_PL_BA_REGI (Black 2's music: its own SEQ_BGM_VS_REGI, the same tune, melody 0.68), the Kanto birds SEQ_BA_SECRET2. Not
  the Platinum way: Platinum plays the plain wild theme for a Regi or a bird in Pal Park; the table has no zone, so a
  migrated one in the Catching Show plays its legendary theme (C in PearlB2_DecideEnvWild). The trainer battles and
  victories are Pearl's rules; Platinum's 28 double and 4 tag battles keep them (the Fight Area's Volkner and Flint: the
  leader theme, as Platinum's ENCEFF_DOUBLE_LEADER).
- **Rowan's question**: data/unova_music.json gives SEQ_PL_WIFITOWER the GTS row's Black 2 song (SEQ_BGM_GEAR_STATION); the
  other new songs stay Platinum's with Black 2's music, as Pearl's story songs without a row do.
- **Offline proof**: work/agents/plat-music/tools/music_dry.py runs sinnoh_music, battle_music, music_choice and pearl_alt_music
  as the build calls them on a scratch copy of Black 2's archive: Platinum 116 songs, 496 zones, 25 night themes, 25 story
  songs; battle 37 songs; music_choice's and battle_music's waits checks pass. Pearl and Diamond: the same archive, tables
  and mapping as before (digests equal to HEAD's code).
