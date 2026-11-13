# Platinum's new and changed rooms (step 4, the rooms piece)

Written 2026-11-02 by the plat-rooms piece. Offline only: what needs a ROM is in "For the combined ROM" below.
The rooms generate with the rest (`PEARL_VERSION=platinum`: gen4_extract, gen4_land, gen4_script, `pearl_story.py all`,
`platinum_events.py --heights`, then `platinum_events.py --rooms`, which checks every script at its level).

## What each room got

**Team Galactic Eterna Building, 1F-4F.** Platinum's maps, people and scripts, generated. No new script commands here:
the audit's "2 commands" on this row are the Eterna Gym's clock (AdvanceEternaGymClock and its init), the Gyms piece's.
- 1F's wall before Rotom's Room opens with the Secret Key (Platinum's own rule). Its sound is Black 2's
  SEQ_SE_SHINKA_W062, Black 2's copy of W062. The wall is Black 2's invisible blocker until step 6 brings Platinum's
  wall model.
- 4F: Platinum darkens the room with a dark blue fog (command 2CD: overworld weather 26). Black 2 has no such weather.
  Left out, and listed as approximated.

**Rotom's Room.** Reached through 1F's wall, so it needs the Secret Key. The user's rule "all the events built in"
covers it: the Poké Mart deliveryman gives Platinum's fifth gift, the Secret Key, after the Manaphy Egg
(pearl_story.inc PL_DELIVERY_GIFTS, Platinum's own line 17). Platinum's distribution event 3 is that gift.
- The room works: walk, read both notebooks, Rowan's scene, the appliances show (GetRotomFormsInSave: no form exists
  yet, so every appliance shows) and answer "It's an appliance" until the forms exist.
- What the forms need (a later chapter piece): GetPartyRotomCountAndFirst, CountRepeatedSpeciesInParty,
  FindPartySlotWithSpecies, SetRotomForm, GetPartyMonForm2, GetPartyMonMove(Count), OpenSummaryScreenTeachMove,
  GetSummarySelectedMoveSlot (all stubs now, reachable only with a Rotom and the key), a true GetRotomFormsInSave (party
  and boxes), Black 2's PokePartyChangeRotomForme / its form-move rules, and the appliances' own models (step 6:
  Platinum's mmodel 400-404; now Black 2's Rotom form walkers stand in).

**The Regi ruins (6 zones).** The entrance rooms hold an item ball and a hidden item; the inner rooms the statue and the
seven dots. ActivateRegiRuinsDot is script now (pearl_story.inc pl_RegiRuinsDot): the dot under the player sets its
bit in the ruins' state var with a sound, all seven give 260. The dot tables are read from Platinum's overlay 5.
CheckPartyHasFatefulEncounterRegigigas is script too (party, not an Egg, species 486, Black 2's fateful-encounter
param). The statue wakes only with an event Regigigas in the party: no way to get one in this game yet (decision).

**Veilstone Store B1F.** Platinum's new floor, with the elevator: the store elevator now knows B1F
(ELEVATOR_FLOORS_ABOVE[566] = 5, Platinum's field_menu.c). The Poffin seller asks for room for one Poffin
(GetEmptyPoffinCaseSlotCount -> PearlB2's pl_PoffinHasRoom: he sells one at a time). The records it adds to are left
out (Black 2 keeps its own).

**Galactic HQ hall.** Cyrus's speech: the free camera goes to the stage and back from either start row (z 12 or 13:
pearl_story planned_branches, a branch on the start's var). The cheers are a [guess]: SEQ_SE_SW_PKWOOD_AUD_01.

**Global Terminal 2F and 3F.** Scenery (the user's decision): walkable, people talk. The Box Data, Dress-Up Data and
Battle Video machines say they are closed (data/pearl_closed_facilities.json, as the Battle Tower's Wi-Fi rooms).
1F's two new warp panels lead to them and back.

**The Pokémon League and the Hall of Fame.** The rooms are Platinum's maps and scripts, generated; Pearl's patches
stand: pearl_e4_doors (the same door model and graphics id) and game_clear (the same Hall of Fame room, warp and walk;
now checked against the version's warp). The Hall of Fame ends as Pearl's does, Black 2's own way. Platinum gives each
room its own battle background: here all are indoors, as Pearl's (zone_flags PEARL_BG 12-16).

**The Villa (Pearl's Resort Area southwest house).** Platinum's 17 people, 190 lines and its furniture:
- `b2tools/villa_furniture.py` reads the 23 places, 20 kinds, models (build models 559-578) and scripts from Platinum's
  overlay 5. sinnoh_rooms places all 23 as props of the Villa's chunk (599), after its own.
- Gimmick 68 (decomp src/pearlb2/plat_rooms/villa.c, overlay 375 at the gimmick address; patches/platinum_villa.py
  writes its table): shows the owned ones, hides the rest, makes their boxes solid, runs a kind's script on A (the TV:
  Black 2's TV script, facing north only; the order form's sign tiles on the table stay the order form's), and answers
  the order form's requirement questions (pl_VillaFurnitureRequirement, through PVAR_GIMMICK_REQUEST).
- Purchases past 65,535: an exact check (pl_CheckMoneyBig, in 60,000s). Pearl's build keeps its 65,535 check
  (EXACT_BIG_MONEY): its Ribbon Syndicate has the same bug (a 1.0.1 item).
- Requirements: the piano (10 Hall of Fame entries), the masterpiece (30 Eggs hatched) and the chandelier (300,000
  steps) read Black 2's records. The Pokémon busts need the Battle Frontier (step 8): not on the form yet. The guest set
  (50 Battleground battles) and the wall clock (50 Berries planted) have no count in this game: not on the form yet.
- Visitors: Platinum picks the day's visitor when the date changes. Here the Resort Area's zone init picks it once a
  day (PFLAG_VILLA_VISITOR_TODAY, a midnight flag), with Platinum's odds by furniture owned.
- The music box, the piano and the audio system play Platinum's songs (SEQ_PL_TOWN02, SEQ_PL_PIANO, SEQ_PL_AUDIO):
  step 6's music. Until then the room's song plays on. The music box plays until A or B (Black 2's scripts can't
  check a key without waiting).

## People standing wrong (from the events piece)
- The HQ hall's grunts at (16, 13-15), Eterna Galactic 2F's (13, 8) and (19, 8), Iron Island B1F's (11, 13) and (7, 8):
  not wrong in the game. These rooms draw shapes on translated nodes; the heights apply them, the check didn't.
  pearl_rooms_view now draws each shape where the DS draws it (pearl_mesh.shape_translations), and the findings go.
- Charon at the HQ lab (7, 6): the flat drawing (Saturn's lab is kept flat for the trio's lids, the user's decision of
  2026-10-26) cuts the top row of his head on the console behind him (12 px, from some camera spots). A small lean
  fixes him and keeps the trio as flat (slope 12-16 in pearl_rooms_view --upright), but cuts 41-51 px off the player's
  head in front of the middle unit (8, 11) facing north, a tile players stand on. So the lab stays flat: one row of
  Charon's hair, for the combined ROM to look at. (A per-person exception would be C in resident/people_depth.c.)
- Chunks 609 (the HQ hall) and 200 (Eterna 3F) also rotate some nodes (flags 0xfa0c, 0xf800), which
  pearl_mesh.shape_translations doesn't apply: the pictures and checks there are close, not exact. The game draws
  them right (the installed model keeps its nodes) and the heights are right (apicula applies them).

## The ground
- The layers fix pushed a piece away from itself (a pair of polygons inside one piece): Veilstone Store B1F's back wall
  went 4.5 units over its B1 sign and panels, 1,288 units^2 of holes. Platinum's build leaves such pairs alone
  (version.SELF_PAIRS_STAY); Pearl's released maps keep the old rule. All of Platinum's rooms (`pearl_seams_check.py --holes
  --rooms`): 3,232.8 units^2 in 47 chunks before, 1,578.5 in 43 now. My rooms' holes: 25 units^2 left, on translated
  nodes (Eterna 2F (1, 19), the HQ hall (17, 22)), where the fixes still judge shapes where they aren't (plat-world).

## For the combined ROM
See the plat-rooms report (work/agents/plat-rooms/STATE.md): places, flags, what to look at.
