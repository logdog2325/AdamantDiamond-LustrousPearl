# The Battle Zone: Pearl's Battle Tower and the PWT (2026-11-01)

## The Battle Tower, on Black 2's Battle Subway
Pearl's scripts run through the generator. Its tower commands become Black 2's Battle Subway commands (script plugin 1,
decomp ov050 and ov033) or the extension sub-commands 0x80-0x9F: `b2tools/tower_script.py` holds the mapping.

| Pearl | Here |
|---|---|
| Lobby | zone 443 |
| Elevator, corridors, arenas, partner room | zones 616-621 (622 is free) |
| Single, Double, Multi with a partner | play modes 0, 1, 2 |
| Wi-Fi, wireless Multi | closed: a line at the Wi-Fi desk; the Multi desk doesn't ask about a friend (data/pearl_script_patches.json) |
| 300 trainers, 5 partners, Palmer's 2 teams, 951 sets | Pearl's files in a/2/1/2 and a/2/1/1 (patches/battle_tower.py), same format |
| Names and lines | Pearl's banks 16 and 555 in system text 15 and 376 |
| Trainer draw, Palmer at battles 21 and 49 | `PearlB2_TowerDrawTrainerNo`, Pearl's ranges from the dump |
| IVs, BP awards (3, 3, 4, 4, 5, 5, 7; Palmer 20) | Black 2's functions with Pearl's values (`#if PEARLB2`) |
| BP | Black 2's purse (the Battle Subway score), so the PWT's BP shops share it |
| Exchange Service Corner | Pearl's 26 + 15 prizes and prices from the dump, Pearl's menus |
| Partners | all 5: their teams are drawn in the partner room; the chosen one takes Black 2's slot 0 |

Black 2's differences: every Pokémon battles at exactly Level 50; the party screen and regulations are Black 2's.
The player is hidden in the rooms as in Pearl (`pl_TowerActorVisible`: actor commands hang in a field-load script).
A saved challenge resumes in the lobby through `FieldSetNextZone` and flag 2405.

## The PWT
Zones 192 and 193 keep Black 2's rooms (plugins, gimmicks and the subscreen are keyed on them). `patches/pwt.py`:
- the Battle Park's east door of the Exchange building leads to the lobby; the west door keeps the Corner;
- the lobby's story people are hidden and its story scenes are off (src/field_scripts/0384, 0385, from HoennB2);
- the rooms take the Battle Park's place name, and the lobby's camera stops before the black below the entrance.

Decomp `src/ov055/wbt_tool.c`: Sinnoh Leaders opens with the Hall of Fame (flag 2400); the left desk's tournaments are
open from the start and the first (story) Driftveil tournament is never offered. The other tournaments stay as HoennB2
keeps them, Unova Leaders and Driftveil included.

## Not built
Wi-Fi, the wireless Multi, the tower's ribbons and trophies, the banned species' list in the "not eligible" line, and
the Unova mentions in the PWT lobby's texts.
