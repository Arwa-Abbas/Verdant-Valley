# Verdant Valley - Winter Snow & Mud Puddle Task
## Objective
Winter_snow appears randomly during rain (Winter only), season end -> mud_puddle (10s) -> regular.

## Steps
- [x] Step 1: Add snow_timer to Tile class (grid.py), update_tick decrement -> restore.
- [x] Step 2: Enhance apply_rain(season_index) for random Winter_snow (~20 tiles max, Winter rain).
- [x] Step 3: Rename clear_winter_freeze to handle_thaw_end_of_season(): Winter end -> TILE_MUD + _thaw_stage=1 (10s puddle).
- [x] Step 4: Update season.py trigger_rain calls apply_rain(self.index), _apply_season_effects calls handle_thaw_end_of_season.
- [x] Step 5: Enhance _update_thaw for _pre_thaw_type, handle_thaw_end_of_season cleanup.

- [ ] Step 6: Test in game: Winter rain -> random Winter_snow (5s fade), season end -> TILE_MUD puddle 10s -> dirt -> regular.

Current: Testing
