# Pokémon Adamant Diamond & Lustrous Pearl

Sinnoh's Diamond and Pearl rebuilt inside Pokémon Black 2, in the Gen 5 style. Version 1.0 has both games: Lustrous
Pearl and Adamant Diamond. Releases are `.bps` patches only; no ROMs are ever included.

## Playing it
1. Get a clean **Pokémon Black 2 (USA)** ROM from your own cartridge (game code IREO, CRC32 D4427FD1).
2. Apply the release's `.bps` patch for the version you want with a BPS patcher (Floating IPS, Rom Patcher JS), on a
   computer: a 512 MB game is too much for a phone browser.
3. Play it in melonDS or on hardware. DeSmuME hides some bugs that melonDS and hardware show.

## Status: 1.0
- **Story:** the whole story, from Twinleaf to the Hall of Fame, with Palkia in Lustrous Pearl and Dialga in Adamant
  Diamond, each with its version's wild Pokémon, Orb, title screen and Pokédex entries. Post-game: the National
  Pokédex at Champion, the Battle Zone with the Battle Tower and the PWT, Stark Mountain, Snowpoint Temple, Turnback
  Cave, Fullmoon and Newmoon Islands, and the event Pokémon (Darkrai, Shaymin, Arceus, the Manaphy Egg) from the
  Poké Mart deliveryman.
- **Features:** Super Contests (Visual, Dance, Acting) with Accessories and Poffins; Secret Bases; the Grand
  Underground with wandering Pokémon; the Pokétch; Pal Park with BDSP's Ramanas Park rooms; roaming Mesprit and
  Cresselia; following Pokémon; seasons; TMs, HMs, Rock Climb and Defog.
- **Known issues:** in Super Contests, hearts, Voltage and result bars are numbers rather than the original sprites,
  the top screen shows numbers instead of the dressed Pokémon during Visual, and the curtain doesn't count in Visual's
  score. Black 2's sounds stand in for the contests' and the Digger Drill's. Cooking Poffins is solo, with simplified
  art. Secret Bases have no Radar or other players' bases, and a placed good can wall you in, as in the original: Move
  Goods frees you.
- **Not in yet:** digging in the Underground; the Veilstone Game Corner; online features. Some people can't do their
  job yet, including the Mining Museum's fossil restoring and in-game trades. Pal Park's migration from a GBA game is
  in the build but unconfirmed. The full list is in [Known issues](docs/known-issues.md).

Please report bugs: this is a big game, and some parts have been tested only in an emulator.

## Player guide
The [player guide](docs/README.md) lists each version's wild Pokémon, item locations, important trainers and post-game,
plus Pal Park's rooms, the Underground, Secret Bases, Super Contests, Poffins, the Pokétch, TMs and more. It's made from
the game's own data.

## Screenshots
| | |
|---|---|
| ![Lustrous Pearl's title](docs/screenshots/title_pearl_palkia.png) | Lustrous Pearl |
| ![Adamant Diamond's title](docs/screenshots/title_diamond_dialga.png) | Adamant Diamond |
| ![Black 2's water](docs/screenshots/water_route219.png) | Black 2's animated sea on Route 219 |
| ![Winter in Snowpoint](docs/screenshots/winter_snowpoint.png) | Snowpoint City in winter |
| ![Following Pokémon](docs/screenshots/follower_route201.png) | Following Pokémon on Route 201 in autumn |
| ![Palkia at Spear Pillar](docs/screenshots/spear_pillar_palkia.png) | Spear Pillar in Lustrous Pearl |
| ![Dialga at Spear Pillar](docs/screenshots/spear_pillar_dialga.png) | Spear Pillar in Adamant Diamond |
| ![The Grand Underground](docs/screenshots/hideaway_wandering_pokemon.png) | The Grand Underground: Pokémon wandering in a Hideaway |
| ![A Secret Base](docs/screenshots/secret_base_decorated.png) | A decorated Secret Base |
| ![Ramanas Park](docs/screenshots/ramanas_raikou.png) | Meeting Raikou in Adamant Diamond's Johto Room |
| ![Defog](docs/screenshots/defog_weather.png) | Weather: Route 210's fog, then cleared with Defog |
| ![Seasons](docs/screenshots/seasons.png) | Route 201 in summer and autumn |
| ![Hidden Grottos](docs/screenshots/hidden_grottos.png) | Hidden Grottos and the Hideaways |
| ![Summoning Kyogre](docs/screenshots/ramanas_summon.png) | Placing the Oceanic Slate: Kyogre appears |
| ![Place names](docs/screenshots/place_banners.png) | Sinnoh's place names on arrival |

## For developers
- Start with `notes/START_HERE.md` (open decisions and status), then `notes/PLAN.md` (feasibility and phases).
- `notes/SETUP.md`: what is in this repo, where each tool came from, how to set up.
- `notes/DECISIONS.md`: every decision, dated, with who made it.
- The game's C changes live in a branch of the pokebw2 decomp (`pearlb2`), not published yet.

This project is built with the help of AI coding tools (Anthropic's Claude).

## Credits
- Pokémon Pearl and Pokémon Black 2: Game Freak, Nintendo, The Pokémon Company. This is a fan project.
- The player's battle back as Lucas: "Trainer Lucas back BW style" by tebited15 (DeviantArt, free use;
  `art_sources/fan_tebited15_lucas_back/CREDIT.txt`).
- The Pokémon Black 2 decompilation (pokebw2) and the Diamond/Pearl and Platinum decompilations (pokediamond,
  pokeplatinum), which this work reads.
