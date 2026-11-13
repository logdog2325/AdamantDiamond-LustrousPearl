// Global scripts 10380-10382 (a/0/5/6 entry 1260), Platinum's (version.sources takes this file over
// src/field_scripts/1260_global_pokedex_rating.s, Pearl's and Diamond's; plat-fixes, 2026-11-07). Script_3 is
// Platinum's PC rating, pokeplatinum res/field/scripts/scripts_pokedex_ratings.s PokedexRatings_CheckPC (the Pokémon
// Center PC's professor entry, global 10090 = src/field_scripts/1244_global_pc.s, as Pearl's):
//   - no National Pokédex: "Accessed Professor Rowan's PC.", then PokedexRatings_RateLocalDex: after the first visit
//     to Eterna (FLAG_FIRST_ARRIVAL_ETERNA_CITY) with the Sinnoh Pokédex complete, FLAG_SHOWN_COMPLETE_LOCAL_DEX (Rowan's
//     National Pokédex scene in his lab); "Hmm... You've spotted N Pokémon in Sinnoh..." and Rowan's line for the count
//     (pearl_story.inc pl_LoadPokedexRatingLocalPlatinum: Platinum's 12 tiers up to 210, nothing left out);
//   - National Pokédex: "Accessed Professor Oak's PC.", "Hmhm... You've caught N so far..." and Oak's line
//     (pl_LoadPokedexRatingNational: Pearl's tiers, which are Platinum's too).
// Text: a/0/0/3 file 1051, src/text/script/platinum/1051_rowan_rating.txt = Platinum's rating bank 335 line for line
// (45 lines: Rowan 4-17, Oak 22-42, the PCs 43 and 44; made by patches/sinnoh_pokedex.py --sources), so the line
// numbers below are Platinum's. Script_1 / Script_2 (Black 2's Juniper) end at once, as Pearl's.
#include "pearl.h"
#include "asm/field_script.inc"
#include "pearl_story.inc"

#define RT_LINE 0x8044                 // the rating line (0x8020-0x805E are the caller's, restored after RTCallGlobal)
#define RT_COUNT 0x8045

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntriesEnd

Script_1:                                        // 10380: Black 2's Juniper in her lab (not in Sinnoh)
    RTEndGlobal

Script_2:                                        // 10381: Black 2's Juniper's father (not in Sinnoh)
    RTEndGlobal

Script_3:                                        // 10382: PokedexRatings_CheckPC
    PokeDexHaveNational RT_LINE                  // GetNationalDexEnabled
    WorkCmpConst RT_LINE, 1
    VMJumpIf CMP_EQ, L_Oak
    SystemMsg 43, 2                              // Accessed Professor Rowan's PC.
    FlagGet PFLAG_09BA, PL_TMP                   // PokedexRatings_RateLocalDex: GoToIfUnset FLAG_FIRST_ARRIVAL_ETERNA_CITY
    WorkCmpConst PL_TMP, 1
    VMJumpIf CMP_NE, L_Seen
    pl_CheckLocalDexCompleted RT_LINE
    WorkCmpConst RT_LINE, 1
    VMJumpIf CMP_NE, L_Seen
    FlagSet PFLAG_0110                           // FLAG_SHOWN_COMPLETE_LOCAL_DEX
L_Seen:                                          // PokedexRatings_JustRateLocalDex
    pl_GetLocalDexSeenCount RT_COUNT
    WordSetNumber 0, RT_COUNT, 0
    SystemMsg 1, 2                               // Hmm... You've spotted N Pokémon in Sinnoh...
    pl_LoadPokedexRatingLocalPlatinum RT_LINE, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17
    WordSetPlayerName 0
    SystemMsg RT_LINE, 2
    LastKeyWait
    RTEndGlobal

L_Oak:                                           // PokedexRatings_CheckPCNationalDex, PokedexRatings_RateNationalDex
    SystemMsg 44, 2                              // Accessed Professor Oak's PC.
    PokeDexGetCount 1, RT_COUNT                  // GetNationalDexCaughtCount
    WordSetNumber 0, RT_COUNT, 0
    SystemMsg 20, 2                              // Hmhm... You've caught N so far...
    pl_LoadPokedexRatingNational RT_LINE, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42
    WordSetPlayerName 0
    SystemMsg RT_LINE, 2
    LastKeyWait
    RTEndGlobal
    .balign 4, 0
