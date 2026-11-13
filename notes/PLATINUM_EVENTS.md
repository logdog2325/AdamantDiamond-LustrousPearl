# Platinum's events: people, doors, warps, signs, triggers

Written by `PEARL_VERSION=platinum python3 b2tools/platinum_events.py`; don't edit. What Platinum changed against Pearl in the installed zones' events, and the offline check of what a Platinum build installs (the tool's docstring says what each check is). The lists for later pieces are in `data/platinum/events_waiting.json`.

- Installed zones: 506; with a script file: 485.
- Problems: 0. Step 4's rooms: 0. Later steps (7, 8): 17. Notes: 121.
- Event scripts waiting for the chapter pieces: 21. Sprites waiting for step 6: 0.

## What Platinum changed

302 installed zones have other events than Pearl's. People (matched by sprite and tile, then by sprite and script): 190 moved, 15 re-cast (another sprite on the same tile), 320 added, 85 removed, 5 in place with another movement or facing. Warps: 46 moved, 45 new, 2 aimed elsewhere, 0 renumbered, 0 gone. Signs: 116 moved, 57 new, 4 gone. Step triggers: 8 moved, 59 new, 9 changed, 15 gone.

### Outdoor zones by people moved, added or removed

| Zone | Black 2 zone | Moved | Added | Removed | Moved (sprite: Pearl's tile -> Platinum's) |
|---|---|---|---|---|---|
| FIGHT_AREA | 448 | 15 | 8 | 0 | 91: (636, 431) -> (633, 433); 94: (631, 429) -> (631, 430); 94: (656, 427) -> (652, 426); 182: (648, 436) -> (648, 438) ... |
| RESORT_AREA | 397 | 12 | 7 | 0 | 91: (805, 449) -> (805, 451); 93: (817, 460) -> (813, 457); 87: (829, 466) -> (815, 462); 13: (806, 462) -> (806, 458) ... |
| VEILSTONE | 120 | 1 | 6 | 2 | 7: (699, 618) -> (701, 618) |
| HEARTHOME | 107 | 0 | 4 | 4 |  |
| STARK_MOUNTAIN_EXTERIOR | 230 | 3 | 4 | 0 | 87: (742, 243) -> (740, 248); 11: (749, 245) -> (749, 248); 93: (750, 235) -> (748, 232) |
| ROUTE_218 | 38 | 0 | 7 | 0 |  |
| ETERNA | 96 | 3 | 3 | 0 | 17: (302, 550) -> (300, 550); 1: (328, 527) -> (330, 527); 14: (306, 544) -> (308, 552) |
| PASTORIA | 113 | 2 | 3 | 1 | 93: (608, 810) -> (613, 810); 53: (607, 815) -> (607, 818) |
| OREBURGH | 62 | 0 | 5 | 0 |  |
| ROUTE_224 | 108 | 0 | 5 | 0 |  |
| ACUITY_LAKEFRONT | 7 | 0 | 2 | 2 |  |
| ROUTE_216 | 29 | 0 | 3 | 1 |  |
| ROUTE_217 | 37 | 0 | 4 | 0 |  |
| SURVIVAL_AREA | 389 | 0 | 4 | 0 |  |
| VALOR_LAKEFRONT | 461 | 1 | 2 | 0 | 87: (719, 769) -> (717, 748) |
| ROUTE_201 | 319 | 2 | 1 | 0 | 99: (104, 853) -> (105, 853); 101: (104, 854) -> (105, 853) |
| ROUTE_203 | 329 | 2 | 1 | 0 | 4: (245, 756) -> (234, 757); 6: (234, 757) -> (243, 757) |
| ROUTE_212_NORTH | 474 | 1 | 2 | 0 | 87: (453, 804) -> (450, 777) |
| ROUTE_214 | 19 | 2 | 1 | 0 | 87: (733, 674) -> (725, 678); 87: (714, 722) -> (722, 727) |
| SOLACEON | 233 | 0 | 3 | 0 |  |
| CELESTIC | 355 | 0 | 2 | 1 |  |
| JUBLIFE | 6 | 1 | 1 | 0 | 14: (150, 756) -> (145, 761) |
| SUNYSHORE | 406 | 1 | 1 | 0 | 16: (856, 780) -> (856, 782) |
| SNOWPOINT | 412 | 0 | 2 | 0 |  |
| VALLEY_WINDWORKS_EXTERIOR | 154 | 0 | 2 | 0 |  |
| ROUTE_207 | 370 | 1 | 1 | 0 | 20: (335, 715) -> (329, 715) |
| ROUTE_210_NORTH | 437 | 0 | 2 | 0 |  |
| ROUTE_212_SOUTH | 475 | 0 | 2 | 0 |  |
| ROUTE_213 | 18 | 1 | 1 | 0 | 124: (684, 834) -> (683, 833) |
| ROUTE_222 | 98 | 0 | 2 | 0 |  |
| FLOAROMA | 465 | 0 | 1 | 1 |  |
| ROUTE_223 | 445 | 0 | 2 | 0 |  |
| CANALAVE | 16 | 0 | 1 | 0 |  |
| POKEMON_LEAGUE | 439 | 1 | 0 | 0 | 93: (853, 598) -> (848, 598) |
| IRON_ISLAND_EXTERIOR | 240 | 0 | 1 | 0 |  |
| VERITY_LAKEFRONT | 456 | 0 | 0 | 1 |  |
| ROUTE_206 | 368 | 0 | 1 | 0 |  |
| ROUTE_209 | 387 | 0 | 1 | 0 |  |
| ROUTE_211_EAST | 463 | 0 | 1 | 0 |  |
| ROUTE_215 | 20 | 0 | 1 | 0 |  |
| ROUTE_225 | 111 | 0 | 1 | 0 |  |
| ROUTE_227 | 112 | 0 | 1 | 0 |  |
| SANDGEM | 458 | 0 | 1 | 0 |  |
| ROUTE_230 | 473 | 0 | 1 | 0 |  |

### New and moved warps

| Zone | Black 2 zone | Warp | Tile | Was | Leads to |
|---|---|---|---|---|---|
| ACUITY_LAKEFRONT | 7 | 0 | (308, 229) | (310, 239) | LAKE_ACUITY warp 0 |
| ACUITY_LAKEFRONT | 7 | 1 | (309, 229) | (311, 239) | LAKE_ACUITY warp 1 |
| ACUITY_LAKEFRONT | 7 | 2 | (308, 229) | (310, 239) | LAKE_ACUITY_GALACTIC warp 3 |
| ACUITY_LAKEFRONT | 7 | 3 | (309, 229) | (311, 239) | LAKE_ACUITY_GALACTIC warp 4 |
| FIGHT_AREA | 448 | 2 | (654, 423) | (658, 425) | BATTLE_FRONTIER_GATE_TO_FIGHT_AREA warp 3 |
| FIGHT_AREA | 448 | 3 | (655, 423) | (659, 425) | BATTLE_FRONTIER_GATE_TO_FIGHT_AREA warp 3 |
| FIGHT_AREA | 448 | 4 | (654, 438) | (654, 440) | FIGHT_AREA_SOUTHEAST_HOUSE warp 0 |
| FIGHT_AREA | 448 | 5 | (654, 444) | (645, 440) | FIGHT_AREA_SOUTHWEST_HOUSE warp 0 |
| FIGHT_AREA | 448 | 6 | (647, 429) | (647, 431) | FIGHT_AREA_POKECENTER_1F warp 0 |
| FIGHT_AREA | 448 | 7 | (660, 429) | (663, 440) | FIGHT_AREA_POKEMART warp 0 |
| POKEMON_LEAGUE | 439 | 4 (new) | (850, 597) | - | VICTORY_ROAD_1F warp 7 |
| POKEMON_LEAGUE | 439 | 5 (new) | (852, 597) | - | VICTORY_ROAD_1F warp 7 |
| POKEMON_LEAGUE | 439 | 6 (new) | (853, 581) | - | VICTORY_ROAD_1F warp 8 |
| POKEMON_LEAGUE | 439 | 7 (new) | (853, 583) | - | VICTORY_ROAD_1F warp 8 |
| RESORT_AREA | 397 | 0 | (822, 469) | (802, 465) | RESORT_AREA_SOUTHWEST_HOUSE warp 0 |
| RESORT_AREA | 397 | 1 | (810, 455) | (816, 469) | RESORT_AREA_SOUTHEAST_HOUSE warp 0 |
| RESORT_AREA | 397 | 2 | (824, 453) | (826, 453) | RESORT_AREA_RIBBON_SYNDICATE_1F warp 0 |
| RESORT_AREA | 397 | 3 | (802, 472) | (807, 457) | RESORT_AREA_POKECENTER_1F warp 0 |
| ROUTE_228 | 159 | 4 (new) | (785, 340) | - | ROUTE_228_ROCK_PEAK_RUINS warp 0 |
| ROUTE_228 | 159 | 5 (new) | (785, 340) | - | ROCK_PEAK_RUINS warp 0 |
| STARK_MOUNTAIN_EXTERIOR | 230 | 0 | (750, 231) | (747, 234) | STARK_MOUNTAIN_INTERIOR_1 warp 0 |
| SURVIVAL_AREA | 389 | 0 | (652, 338) | (650, 338) | SURVIVAL_AREA_WEST_HOUSE warp 0 |
| SURVIVAL_AREA | 389 | 3 | (659, 338) | (657, 338) | SURVIVAL_AREA_POKECENTER_1F warp 0 |
| BATTLE_TOWER_LOBBY | 443 | 1 (new) | (14, 19) | - | BATTLE_FRONTIER warp 0 |
| BATTLE_TOWER_LOBBY | 443 | 2 (new) | (16, 19) | - | BATTLE_FRONTIER warp 0 |
| BATTLE_TOWER_LOBBY | 443 | 0 | (15, 19) | (11, 17) | BATTLE_FRONTIER warp 0 |
| ETERNA_GALACTIC_BUILDING_1F | 106 | 2 (new) | (20, 6) | - | ETERNA_GALACTIC_BUILDING_2F warp 2 |
| ETERNA_GALACTIC_BUILDING_1F | 106 | 3 (new) | (2, 2) | - | ROTOMS_ROOM warp 0 |
| ETERNA_GALACTIC_BUILDING_1F | 106 | 0 | (11, 15) | (11, 12) | ETERNA warp 3 |
| ETERNA_GALACTIC_BUILDING_1F | 106 | 1 | (14, 6) | (15, 3) | ETERNA_GALACTIC_BUILDING_2F warp 0 |
| ETERNA_GALACTIC_BUILDING_2F | 109 | 2 (new) | (8, 3) | on a tile Pearl had a warp on | ETERNA_GALACTIC_BUILDING_1F warp 2 |
| ETERNA_GALACTIC_BUILDING_2F | 109 | 3 (new) | (14, 3) | - | ETERNA_GALACTIC_BUILDING_3F warp 2 |
| ETERNA_GALACTIC_BUILDING_2F | 109 | 0 | (3, 3) | (8, 3) | ETERNA_GALACTIC_BUILDING_1F warp 1 |
| ETERNA_GALACTIC_BUILDING_2F | 109 | 1 | (20, 3) | (15, 3) | ETERNA_GALACTIC_BUILDING_3F warp 0 |
| ETERNA_GALACTIC_BUILDING_3F | 110 | 2 (new) | (2, 3) | - | ETERNA_GALACTIC_BUILDING_2F warp 3 |
| ETERNA_GALACTIC_BUILDING_3F | 110 | 3 (new) | (14, 3) | - | ETERNA_GALACTIC_BUILDING_4F warp 1 |
| ETERNA_GALACTIC_BUILDING_3F | 110 | 1 | (20, 3) | (15, 3) | ETERNA_GALACTIC_BUILDING_4F warp 0 |
| ETERNA_GALACTIC_BUILDING_4F | 115 | 1 (new) | (3, 3) | - | ETERNA_GALACTIC_BUILDING_3F warp 3 |
| ETERNA_GYM_ENTRANCE | 102 | 0 | (11, 27) | (8, 11) | ETERNA warp 10 |
| ETERNA_GYM_ENTRANCE | 102 | 1 | (11, 0) | (8, 2) | ETERNA_GYM warp 0 |
| ETERNA_ROUTE_206_GATEHOUSE | 122 | 2 (new) | (6, 12) | - | ROUTE_206 warp 4 |
| ETERNA_ROUTE_206_GATEHOUSE | 122 | 3 (new) | (8, 12) | - | ROUTE_206 warp 4 |
| ETERNA_ROUTE_206_GATEHOUSE | 122 | 4 (new) | (6, 2) | - | ETERNA warp 8 |
| ETERNA_ROUTE_206_GATEHOUSE | 122 | 5 (new) | (8, 2) | - | ETERNA warp 8 |
| ETERNA_ROUTE_206_GATEHOUSE | 122 | 0 | (7, 2) | (5, 2) | ETERNA warp 8 |
| ETERNA_ROUTE_206_GATEHOUSE | 122 | 1 | (7, 12) | (5, 12) | ROUTE_206 warp 4 |
| GREAT_MARSH_AREA_6 | 536 | 0 | (68, 118) | (68, 117) | PASTORIA_GREAT_MARSH_ENTRANCE_1F warp 2 |
| GREAT_MARSH_AREA_6 | 536 | 1 | (69, 118) | (69, 117) | PASTORIA_GREAT_MARSH_ENTRANCE_1F warp 2 |
| HEARTHOME_BEBE_HOUSE | 169 | 0 | (5, 8) | (4, 8) | HEARTHOME warp 6 |
| HEARTHOME_GYM_FIRST_QUESTION_ROOM | 128 | 4 (new) | (11, 3) | - | HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 4 |
| HEARTHOME_GYM_FIRST_QUESTION_ROOM | 128 | 0 | (11, 7) | (9, 2) | HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0 |
| HEARTHOME_GYM_FIRST_QUESTION_ROOM | 128 | 2 | (12, 7) | (14, 2) | HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3 |
| HEARTHOME_GYM_FIRST_QUESTION_ROOM | 128 | 3 | (4, 8) | (9, 22) | HEARTHOME warp 8 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1 | 129 | 1 (new) | (4, 2) | - | HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1 | 129 | 2 (new) | (8, 2) | - | HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1 | 129 | 3 (new) | (12, 2) | - | HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1 | 129 | 0 | (8, 10) | (7, 10) | HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 | 130 | 1 (new) | (4, 2) | - | HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 | 130 | 2 (new) | (9, 2) | - | HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 | 130 | 3 (new) | (14, 2) | - | HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 | 130 | 4 (new) | (19, 2) | - | HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 | 130 | 5 (new) | (24, 2) | - | HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3 |
| HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 | 130 | 0 | (14, 22) | (7, 10) | HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 |
| HEARTHOME_GYM_SECOND_QUESTION_ROOM | 131 | 4 (new) | (14, 3) | - | HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 4 |
| HEARTHOME_GYM_SECOND_QUESTION_ROOM | 131 | 0 | (3, 17) | (9, 2) | HEARTHOME_GYM_THIRD_QUESTION_ROOM warp 3 |
| HEARTHOME_GYM_SECOND_QUESTION_ROOM | 131 | 1 | (1, 17) | (4, 2) | HEARTHOME_GYM_SECOND_QUESTION_TRAINER_ROOM_1 warp 0 |
| HEARTHOME_GYM_SECOND_QUESTION_ROOM | 131 | 2 | (5, 17) | (14, 2) | HEARTHOME_GYM_SECOND_QUESTION_TRAINER_ROOM_2 warp 0 |
| HEARTHOME_GYM_SECOND_QUESTION_ROOM | 131 | 3 | (4, 13) | (9, 22) | HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 |
| IRON_ISLAND_B3F | 402 | 2 (new) | (14, 1) | - | IRON_ISLAND_IRON_RUINS warp 0 |
| IRON_ISLAND_B3F | 402 | 3 (new) | (14, 1) | - | IRON_RUINS warp 0 |
| JUBLIFE_GLOBAL_TRADE_STATION | 42 | 1 (new) | (16, 4) | - | GLOBAL_TERMINAL_2F warp 0 |
| JUBLIFE_GLOBAL_TRADE_STATION | 42 | 2 (new) | (20, 4) | - | GLOBAL_TERMINAL_3F warp 0 |
| JUBLIFE_GLOBAL_TRADE_STATION | 42 | 0 | (13, 18) | (12, 13) | JUBLIFE warp 1 |
| MOUNT_CORONET_6F | 323 | 2 (new) | (7, 5) | on a tile Pearl had a warp on | MOUNT_CORONET_UNUSED_2 warp 0 |
| MOUNT_CORONET_6F | 323 | 3 (new) | (7, 5) | on a tile Pearl had a warp on | SPEAR_PILLAR_DIALGA warp 0 |
| MOUNT_CORONET_6F | 323 | 4 (new) | (7, 5) | on a tile Pearl had a warp on | SPEAR_PILLAR_PALKIA warp 0 |
| MOUNT_CORONET_NORTH_1F_ROOM_2 | 325 | 2 (new) | (15, 16) | - | MT_CORONET_ICEBERG_RUINS warp 0 |
| MOUNT_CORONET_NORTH_1F_ROOM_2 | 325 | 3 (new) | (15, 16) | - | ICEBERG_RUINS warp 0 |
| MOUNT_CORONET_UNUSED_2 | 265 | 0 (new) | (31, 53) | - | MOUNT_CORONET_6F warp 2 |
| POKEMON_LEAGUE_LOBBY_1F | 231 | 2 | (2, 12) | (2, 10) | POKEMON_LEAGUE_LOBBY_2F warp 0 |
| POKEMON_LEAGUE_LOBBY_1F | 231 | 3 | (6, 14) | (19, 10) | POKEMON_LEAGUE_LOBBY_B1F warp 0 |
| RESORT_AREA_SOUTHWEST_HOUSE | 578 | 0 | (11, 11) | (4, 8) | RESORT_AREA warp 0 |
| SURVIVAL_AREA_WEST_HOUSE | 570 | 0 | (7, 11) | (4, 8) | SURVIVAL_AREA warp 0 |
| VEILSTONE_DEPARTMENT_STORE_1F | 186 | 3 (new) | (7, 8) | - | VEILSTONE_STORE_B1F warp 0 |
| VEILSTONE_GALACTIC_HEADQUARTERS_2F | 415 | 9 (aimed elsewhere) | (52, 6) | VEILSTONE_GALACTIC_HEADQUARTERS_2F warp 10 | GALACTIC_HQ_HALL warp 1 |
| VEILSTONE_GALACTIC_HEADQUARTERS_2F | 415 | 10 (aimed elsewhere) | (29, 13) | VEILSTONE_GALACTIC_HEADQUARTERS_2F warp 9 | GALACTIC_HQ_HALL warp 0 |
| VEILSTONE_GALACTIC_HEADQUARTERS_4F_1 | 417 | 3 (new) | (8, 3) | - | GALACTIC_HQ_HALL warp 2 |
| VEILSTONE_GYM | 183 | 0 | (12, 30) | (12, 25) | VEILSTONE warp 13 |
| VICTORY_ROAD_1F | 359 | 9 (new) | (14, 78) | - | POKEMON_LEAGUE warp 2 |
| VICTORY_ROAD_1F | 359 | 10 (new) | (16, 78) | - | POKEMON_LEAGUE warp 2 |
| VICTORY_ROAD_1F | 359 | 11 (new) | (34, 4) | on a tile Pearl had a warp on | POKEMON_LEAGUE warp 3 |
| VICTORY_ROAD_1F | 359 | 12 (new) | (34, 6) | - | POKEMON_LEAGUE warp 3 |
| VICTORY_ROAD_1F | 359 | 8 | (34, 5) | (34, 4) | POKEMON_LEAGUE warp 3 |

Platinum's new zones (685-718) have 53 warps of their own, all new; their rows are in the check below.

## Sprites waiting for step 6

Platinum's own sprites have no sheet in the build yet: each is drawn with the existing code that shows the same person, or the nearest (data/platinum/sprite_map.json), or left out. Changed art of the same people is listed too.

| Graphics | Name | Drawn now as | Objects | Zones | Step 6 brings |
|---|---|---|---|---|---|
| - | none: every sprite the installed zones use shows Platinum's own picture (step 6, patches/pearl_npc_sprites) | | | | |

## Event scripts waiting for the chapter pieces

21 references (all in data/platinum/events_waiting.json), by kind and reason:

- zone: no script file (20)
- sign: the converted file has no script at this entry (Pearl's events have it too) (1)

Item balls run work/platinum/src/field_scripts/1240_global_item_balls.s (327 entries). Hidden items run work/platinum/src/field_scripts/1241_global_hidden_items.s, made from Pearl's table (b2tools/pearl_items.py): 0 of the hidden items Platinum's zones use get another item or count than Platinum's own table gives (its arm9 at 0x20ea378, 257 records, numbers up to 0); the list is in the JSON.

## Doors and sprite counts

Doors (pearl_doors.check): 176 door warps, 176 with exactly one door prop in Black 2's search box; 0 other warps would open a door (2 accepted); 18 door models, every record a working Black 2 door.

Different sprites per zone (Black 2 draws 30 besides the player's two): the busiest are BATTLE_FRONTIER 21, FIGHT_AREA 19, PASTORIA 18, ROUTE_209 17, RESORT_AREA_SOUTHWEST_HOUSE 17, ROUTE_210_SOUTH 16.

## Pokémon Centers

18 Centers checked: each 1F has the heal machine prop (build model 123 with Black 2's heal record; the balls are resource 0x62) within 5 tiles of the counter: JUBLIFE_POKECENTER_1F 2.4, CANALAVE_POKECENTER_1F 2.4, OREBURGH_POKECENTER_1F 2.4, ETERNA_POKECENTER_1F 2.4, HEARTHOME_POKECENTER_1F 2.4, PASTORIA_POKECENTER_1F 2.4, VEILSTONE_POKECENTER_1F 2.4, SUNYSHORE_POKECENTER_1F 2.4, SNOWPOINT_POKECENTER_1F 2.4, POKEMON_LEAGUE_POKECENTER_1F 2.4, POKEMON_LEAGUE_LOBBY_1F 2.2, FIGHT_AREA_POKECENTER_1F 2.4, SANDGEM_POKECENTER_1F 2.4, FLOAROMA_POKECENTER_1F 2.4, SOLACEON_POKECENTER_1F 2.4, CELESTIC_POKECENTER_1F 2.4, SURVIVAL_AREA_POKECENTER_1F 2.4, RESORT_AREA_POKECENTER_1F 2.4 tiles.

## Zones Platinum didn't change

160 of 160 zones whose events are Pearl's, byte for byte, install what a Pearl build installs, field by field (people, signs, step triggers, every hand fix; scripts named by what they run); a height that follows Platinum's own floor is noted below ("floor height").

## Pearl's fixes keyed by an object, a sign or a tile

177 of 177 still find what they were made for.

## Left for later steps

Their events convert as the rest; these findings are those steps'.

- step 8: the Battle Frontier: MAP_BATTLE_FACTORY_CORRIDOR: (entities) the entity file does not pack: 593
- step 8: the Battle Frontier: MAP_BATTLE_FACTORY_BATTLE_ROOM: (entities) the entity file does not pack: 594
- step 8: the Battle Frontier: MAP_BATTLE_HALL_CORRIDOR: (entities) the entity file does not pack: 595
- step 8: the Battle Frontier: MAP_BATTLE_HALL_BATTLE_ROOM: (entities) the entity file does not pack: 596
- step 8: the Battle Frontier: MAP_BATTLE_CASTLE_CORRIDOR: (entities) the entity file does not pack: 597
- step 8: the Battle Frontier: MAP_BATTLE_CASTLE_BATTLE_ROOM: (entities) the entity file does not pack: 598
- step 8: the Battle Frontier: MAP_BATTLE_ARCADE_CORRIDOR: (entities) the entity file does not pack: 599
- step 8: the Battle Frontier: MAP_BATTLE_ARCADE_BATTLE_ROOM: (entities) the entity file does not pack: 600
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 2 at (77, 34) -> MAP_BATTLE_FACTORY warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 12
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 3 at (77, 35) -> MAP_BATTLE_FACTORY warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 12
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 4 at (19, 34) -> MAP_BATTLE_HALL warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 13
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 5 at (19, 35) -> MAP_BATTLE_HALL warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 13
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 6 at (33, 62) -> MAP_BATTLE_CASTLE warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 15
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 7 at (33, 63) -> MAP_BATTLE_CASTLE warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 15
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 8 at (64, 62) -> MAP_BATTLE_ARCADE warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 14
- step 8: the Battle Frontier: MAP_BATTLE_FRONTIER: (warp pair) warp 9 at (64, 63) -> MAP_BATTLE_ARCADE warp 0, whose way back leads to MAP_BATTLE_FRONTIER warp 14
- step 7: the Distortion World: MAP_DISTORTION_WORLD_1F: (warp pair) warp 0 at (10, 43) -> MAP_MOUNT_CORONET_6F warp 2, whose way back leads to MAP_MOUNT_CORONET_SPEAR_PILLAR warp 0

## Notes

- MAP_UNDERGROUND: (zone) no script file: its 21 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_JUBLIFE_POKECENTER_2F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: the same events)
- MAP_JUBLIFE_TV_3F_GLOBAL_RANKINGS: (sign) sign (bg 0) at (8, 5): script 1 (Platinum 1) shows no text (as in Pearl)
- MAP_JUBLIFE_TV_3F_GLOBAL_RANKINGS: (sign) sign (bg 1) at (3, 3): script 2 (Platinum 2) shows no text (as in Pearl)
- MAP_JUBLIFE_TV_3F_GLOBAL_RANKINGS: (sign) sign (bg 2) at (13, 3): script 3 (Platinum 3) shows no text (as in Pearl)
- MAP_JUBLIFE_TV_3F_GROUP_RANKINGS: (sign) sign (bg 0) at (8, 5): script 1 (Platinum 1) shows no text (as in Pearl)
- MAP_JUBLIFE_TV_3F_GROUP_RANKINGS: (sign) sign (bg 1) at (3, 3): script 2 (Platinum 2) shows no text (as in Pearl)
- MAP_JUBLIFE_TV_3F_GROUP_RANKINGS: (sign) sign (bg 2) at (13, 3): script 3 (Platinum 3) shows no text (as in Pearl)
- MAP_JUBLIFE_GLOBAL_TRADE_STATION: (sign) sign (bg 0) at (9, 10): script 48 (Platinum 2025) shows no text (as in Pearl)
- MAP_JUBLIFE_GLOBAL_TRADE_STATION: (sign) sign (bg 1) at (10, 10): script 48 (Platinum 2025) shows no text (as in Pearl)
- MAP_HEARTHOME_SOUTHEAST_HOUSE_ELEVATOR: (sign) sign (bg 0) at (1, 5): script 1 (Platinum 1) shows no text (as in Pearl)
- MAP_HEARTHOME_NORTHEAST_HOUSE_ELEVATOR: (sign) sign (bg 0) at (1, 5): script 1 (Platinum 1) shows no text (as in Pearl)
- MAP_HEARTHOME_SUPER_CONTEST_HALL_LOBBY: (sign) sign (bg 0) at (9, 5): script 96 (Platinum 9812) shows no text (as in Pearl)
- MAP_UNION_ROOM: (zone) no script file: its 51 people, 0 signs and 0 triggers are not installed (as in Pearl: the same events)
- MAP_JUBLIFE_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_CANALAVE_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_OREBURGH_POKECENTER_B1F: (zone) no script file: its 4 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_ETERNA_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_HEARTHOME_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_PASTORIA_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_VEILSTONE_POKECENTER_B1F: (zone) no script file: its 4 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_SUNYSHORE_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_SNOWPOINT_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_POKEMON_LEAGUE_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_FIGHT_AREA_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_SANDGEM_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_FLOAROMA_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_SOLACEON_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_CELESTIC_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_SURVIVAL_AREA_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_RESORT_AREA_POKECENTER_B1F: (zone) no script file: its 3 people, 0 signs and 0 triggers are not installed (as in Pearl: Pearl installs none here either)
- MAP_ACUITY_LAKEFRONT: (warp) 2 warps on (308, 229) (warps [0, 2]): only the first fires (kept: Pearl's story versions of the lake (normal / Galactic): its map script (zone ini...)
- MAP_ACUITY_LAKEFRONT: (warp) 2 warps on (309, 229) (warps [1, 3]): only the first fires (kept: Pearl's story versions of the lake (normal / Galactic): its map script (zone ini...)
- MAP_ROUTE_214: (warp) 3 warps on (713, 670) (warps [2, 3, 4]): only the first fires (kept: the Ruin Maniac cave's three stages: Route 214's map script moves two of warps 2...)
- MAP_JUBLIFE_SOUTHEAST_HOUSE_3F: (warp) warp 0 at (9, 3) -> MAP_JUBLIFE_SOUTHEAST_HOUSE_2F warp 1: arrival (0, -1) is off the map (as in Pearl)
- MAP_JUBLIFE_CONDOMINIUMS_3F: (warp) warp 0 at (9, 3) -> MAP_JUBLIFE_CONDOMINIUMS_2F warp 1: arrival (0, -1) is off the map (as in Pearl)
- MAP_OREBURGH_NORTHWEST_HOUSE_3F: (warp) warp 0 at (9, 3) -> MAP_OREBURGH_NORTHWEST_HOUSE_2F warp 1: arrival (1, 0) is solid (as in Pearl)
- MAP_OREBURGH_NORTH_HOUSE_3F: (warp) warp 0 at (9, 3) -> MAP_OREBURGH_NORTH_HOUSE_2F warp 1: arrival (1, 0) is solid (as in Pearl)
- MAP_OREBURGH_EAST_HOUSE_3F: (warp) warp 0 at (9, 3) -> MAP_OREBURGH_EAST_HOUSE_2F warp 1: arrival (1, 0) is solid (as in Pearl)
- MAP_ETERNA_GYM: (warp) warp 0 at (16, 29) -> MAP_ETERNA_GYM_ENTRANCE warp 1: arrival (11, -1) is off the map (Platinum's design: Platinum's zone 68 is the leftover DP Gym room: its only way in, the Gym's warp 1 at (11, 0), is in the Gym's top wall, so nobody reaches it)
- MAP_ETERNA_CONDOMINIUMS_4F: (warp) warp 0 at (9, 3) -> MAP_ETERNA_CONDOMINIUMS_3F warp 1: arrival (1, 0) is solid (as in Pearl)
- MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM: (warp pair) warp 0 at (11, 7) -> MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's entrance room: (11, 7) and (12, 7) are walled in (DP leftovers), nobody reaches them)
- MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM: (warp pair) warp 2 at (12, 7) -> MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's entrance room: (11, 7) and (12, 7) are walled in (DP leftovers), nobody reaches them)
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1: (warp pair) warp 1 at (4, 2) -> MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1: (warp pair) warp 2 at (8, 2) -> MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1: (warp pair) warp 3 at (12, 2) -> MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2 warp 0, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2: (warp pair) warp 0 at (14, 22) -> MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1 warp 0 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2: (warp pair) warp 1 at (4, 2) -> MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2: (warp pair) warp 2 at (9, 2) -> MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2: (warp pair) warp 3 at (14, 2) -> MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2: (warp pair) warp 4 at (19, 2) -> MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_2: (warp pair) warp 5 at (24, 2) -> MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM warp 3, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_HEARTHOME_GYM_SECOND_QUESTION_ROOM: (warp pair) warp 3 at (4, 13) -> MAP_HEARTHOME_GYM_FIRST_QUESTION_ROOM warp 1, whose way back leads to MAP_HEARTHOME_GYM_FIRST_QUESTION_TRAINER_ROOM_1 warp 0 (Platinum's design: Platinum's dark rooms: every room's bottom door leads back to the entrance room's door (warp 1), the doors at the top lead on (the wrong ones, picked at random on entering, back to the entrance: gimmick 67, src/pearlb2/plat_gyms/plat_hearthome_gym.c))
- MAP_ROUTE_228: (warp) 2 warps on (785, 340) (warps [4, 5]): only the first fires: Platinum's own switch, its map script moves all but one away (pl_SetWarpEventPos)
- MAP_SUNYSHORE_UNUSED_HOUSE_1: (warp) warp 0 at (4, 8) -> MAP_SUNYSHORE warp 7: arrival (832, 750) is solid (as in Pearl)
- MAP_MOUNT_CORONET_6F: (warp) 4 warps on (7, 5) (warps [1, 2, 3, 4]): only the first fires: Platinum's own switch, its map script moves all but one away (pl_SetWarpEventPos)
- MAP_MOUNT_CORONET_NORTH_1F_ROOM_2: (warp) 2 warps on (15, 16) (warps [2, 3]): only the first fires: Platinum's own switch, its map script moves all but one away (pl_SetWarpEventPos)
- MAP_ROUTE_206: (warp pair) warp 8 at (304, 681) -> MAP_ROUTE_206_CYCLING_ROAD_GATEHOUSE warp 2, whose way back leads to MAP_ROUTE_206 warp 16 (as in Pearl)
- MAP_IRON_ISLAND_B3F: (warp) 2 warps on (14, 1) (warps [2, 3]): only the first fires: Platinum's own switch, its map script moves all but one away (pl_SetWarpEventPos)
- MAP_LAKE_VALOR: (warp pair) warp 0 at (51, 8) -> MAP_VALOR_LAKEFRONT warp 7, whose way back leads to MAP_LAKE_VALOR_GALACTIC warp 0 (as in Pearl)
- MAP_LAKE_VALOR: (warp pair) warp 2 at (51, 7) -> MAP_VALOR_LAKEFRONT warp 8, whose way back leads to MAP_LAKE_VALOR_GALACTIC warp 2 (as in Pearl)
- MAP_VALOR_CAVERN: (warp) 2 warps on (14, 29) (warps [0, 1]): only the first fires (kept: the way out to Lake Valor or Lake Valor (Galactic): the cavern's map script move...)
- MAP_LAKE_ACUITY_GALACTIC: (warp pair) warp 0 at (11, 50) -> MAP_ACUITY_LAKEFRONT warp 4, whose way back leads to MAP_LAKE_ACUITY warp 0 (as in Pearl)
- MAP_LAKE_ACUITY_GALACTIC: (warp pair) warp 2 at (12, 50) -> MAP_ACUITY_LAKEFRONT warp 5, whose way back leads to MAP_LAKE_ACUITY warp 1 (as in Pearl)
- MAP_VERITY_LAKEFRONT: (warp) 2 warps on (81, 843) (warps [0, 3]): only the first fires (kept: Pearl's story versions of the lake (normal / Galactic): its map script (zone ini...)
- MAP_VERITY_LAKEFRONT: (warp) 2 warps on (80, 843) (warps [1, 2]): only the first fires (kept: Pearl's story versions of the lake (normal / Galactic): its map script (zone ini...)
- MAP_VALOR_LAKEFRONT: (warp) 2 warps on (717, 760) (warps [3, 5]): only the first fires (kept: Pearl's story versions of the lake (normal / Galactic): its map script (zone ini...)
- MAP_VALOR_LAKEFRONT: (warp) 2 warps on (717, 761) (warps [4, 6]): only the first fires (kept: Pearl's story versions of the lake (normal / Galactic): its map script (zone ini...)
- MAP_HALL_OF_ORIGIN: (warp pair) warp 0 at (31, 53) -> MAP_MOUNT_CORONET_6F warp 1, whose way back leads to MAP_MOUNT_CORONET_SPEAR_PILLAR warp 0 (as in Pearl)
- MAP_POKEMON_LEAGUE_LOBBY_2F: (warp pair) warp 1 at (8, 2) -> MAP_UNION_ROOM warp 0, whose way back leads to MAP_JUBLIFE_POKECENTER_2F warp 1 (as in Pearl)
- MAP_ACUITY_LAKEFRONT: (rock climb) Platinum's climb starts differ from Pearl's: 0 -> 4 (data/platinum/pearl_rock_climb.json)
- MAP_STARK_MOUNTAIN_EXTERIOR: (rock climb) Platinum's climb starts differ from Pearl's: 6 -> 6 (data/platinum/pearl_rock_climb.json)
- rock climb: (left out) MAP_MOUNT_CORONET_NORTH_MOUNTAINSIDE [31, 50] dir 1; MAP_MOUNT_CORONET_NORTH_MOUNTAINSIDE [31, 53] dir 0 (start or landing has no height in the dump's BDHC)
- fix: (same person) MAP_BATTLE_TOWER_LOBBY object 2: gfx 27 at (15, 5) -> gfx 235 at (19, 5), script 3 -> 3: the fix follows it (the same local id)
- fix: (same person) MAP_ETERNA_GALACTIC_BUILDING_4F object 2: gfx 15 at (9, 8) -> gfx 15 at (14, 9), script 4 -> 5: the fix follows it (the same local id)
- MAP_FIGHT_AREA_ROUTE_225_GATEHOUSE: (land signs) its map gives 2 wall-map, honey-tree or Rock Climb sign events, Pearl's 0: Platinum's own map
- MAP_FIGHT_AREA_ROUTE_225_GATEHOUSE: (floor height) the same events as Pearl's, on Platinum's converted floor (its ground, plat-world's; y in 1/4096 units): npcs 0: y 0 -> -8192; npcs 1: y 0 -> -8192
- MAP_ROUTE_213_FOOTSTEP_HOUSE: (floor height) the same events as Pearl's, on Platinum's converted floor (its ground, plat-world's; y in 1/4096 units): npcs 0: y -8192 -> 0
- MAP_PASTORIA: (person on a solid tile) object 27 (gfx 128) at (589, 827): solid (moved or added by Platinum; hidden by flag 0x1fb until its scene)
- MAP_VEILSTONE: (person on a solid tile) object 25 (gfx 128) at (684, 611): solid (moved or added by Platinum; hidden by flag 0x191 until its scene)
- MAP_VEILSTONE_GALACTIC_HEADQUARTERS_2F: (person on a solid tile) object 6 (gfx 183) at (41, 17): solid (moved or added by Platinum)
- MAP_ROUTE_208_BERRY_MASTER_HOUSE: (person on a solid tile) object 3 (gfx 183) at (4, 6): solid (moved or added by Platinum)
- MAP_TWINLEAF_RIVAL_HOUSE_2F: (person on a solid tile) object 0 (gfx 148) at (10, 4): solid (moved or added by Platinum; hidden by flag 0x173 until its scene)
- MAP_SANDGEM: (person on a solid tile) object 14 (gfx 99) at (168, 842): solid (moved or added by Platinum; hidden by flag 0x2c4 until its scene)
- MAP_CELESTIC_RUINS: (person on a solid tile) object 2 (gfx 138) at (9, 10): solid (moved or added by Platinum; hidden by flag 0x1a6 until its scene)
- MAP_RESORT_AREA: (person on a solid tile) object 11 (gfx 46) at (816, 455): solid (moved or added by Platinum)
- MAP_BATTLE_TOWER_LOBBY: (furniture) (m) the player at (12, 18) facing north (code 231): stands inside bf_object01#265.22 (16 px) across sprite rows 9-9 (head); slice 16 px
- MAP_BATTLE_TOWER_LOBBY: (furniture) (m) the player at (12, 8) facing north (code 231): stands inside bf_object01#265.19 (16 px) across sprite rows 9-9 (head); slice 16 px
- MAP_BATTLE_TOWER_LOBBY: (furniture) (m) the player at (18, 18) facing north (code 231): stands inside bf_object01#265.21 (16 px) across sprite rows 9-9 (head); slice 16 px
- MAP_BATTLE_TOWER_LOBBY: (furniture) (m) the player at (18, 8) facing north (code 231): stands inside bf_object01#265.20 (16 px) across sprite rows 9-9 (head); slice 16 px
- MAP_CELESTIC_RUINS: (furniture) (n) obj 2 (gfx 138, code 215) at (9, 10): feet at 32 (collision), drawn surface at 24
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (10, 11) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (10, 15) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (12, 11) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (12, 15) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (13, 11) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (13, 12) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (13, 14) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (13, 15) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (14, 11) facing north (code 240): stands inside room 293:flower_purple (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (14, 12) facing north (code 240): stands inside room 293:flower_purple (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (14, 14) facing north (code 240): stands inside room 293:flower_purple (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (14, 15) facing north (code 240): stands inside room 293:flower_purple (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (17, 23) facing north (code 231): stands inside room 293:hana_mini (6 px) across sprite rows 28-28 (feet); slice 6 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (17, 24) facing north (code 231): stands inside room 293:hana_mini (6 px) across sprite rows 28-28 (feet); slice 6 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (17, 26) facing north (code 231): stands inside room 293:hana_mini (9 px) across sprite rows 30-30 (feet); slice 9 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (5, 23) facing north (code 231): stands inside room 293:hana_mini (8 px) across sprite rows 28-28 (feet); slice 8 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (5, 24) facing north (code 231): stands inside room 293:hana_mini (8 px) across sprite rows 28-28 (feet); slice 8 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (5, 25) facing north (code 240): stands inside room 293:hana_mini (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (5, 26) facing north (code 231): stands inside room 293:hana_mini (9 px) across sprite rows 30-30 (feet); slice 9 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (8, 11) facing north (code 240): stands inside room 293:flower_purple (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (8, 12) facing north (code 240): stands inside room 293:flower_purple (8 px) across sprite rows 29-29 (feet); slice 8 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (8, 14) facing north (code 240): stands inside room 293:flower_purple (8 px) across sprite rows 29-29 (feet); slice 8 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (8, 15) facing north (code 240): stands inside room 293:flower_purple (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (9, 11) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (9, 12) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (9, 14) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_ETERNA_GYM_ENTRANCE: (furniture) (m) the player at (9, 15) facing north (code 240): stands inside room 293:flower_red (7 px) across sprite rows 29-29 (feet); slice 7 px
- MAP_POKEMON_LEAGUE_LOBBY_1F: (furniture) (n) obj 0 (gfx 11, code 30) at (11, 3): feet at 0 (collision), drawn surface at -4
- MAP_TWINLEAF_RIVAL_HOUSE_2F: (furniture) (n) obj 0 (gfx 148, code 291) at (10, 4): feet at -24 (collision), drawn surface at -16
- MAP_VEILSTONE_STORE_B1F: (furniture) (m) obj 2 (gfx 25, code 53) at (15, 11) facing S: stands inside room 587:tep_a007 (7 px) across sprite rows 27-29 (feet); slice 7 px
