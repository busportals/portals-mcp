# API Cheat Sheet

Compact reference of all library functions. Pass to subagents alongside the component template.

## portals_core — Item Creators

All creators return `(item_dict, logic_dict)` tuples. Unpack: `items[id_], logic[id_] = create_*(...)`.

```
create_cube(pos, scale=(1,1,1), color="888888", emission=0.0, opacity=1.0, texture="", collider=True, shadows=True, nav_mesh=False, title="")
create_text(pos, content, billboard=True, scale=(1,1,1))
create_spawn(pos, name="", rotation_offset=0.0)
create_portal(pos, scale, destination_room_id, spawn_name="", auto_teleport=True)
create_glb(pos, glb_url, scale=(1,1,1), rot=(0,0,0,1), shadows=True, collider=True)
create_collectible(pos, glb_url, variable, value_change=1, sound_url="", display_value=True, respawn_time=None)
create_trigger(pos, scale=(1,1,1), press_button=False, key_code="X", message="")
create_jump_pad(pos, power=6.9, scale=(1,1,1))
create_light(pos, color="FFFFFF", brightness=2.0, range=10.0, night_only=False)
create_spotlight(pos, rot=(0,0,0,1), color="FFFFFF", brightness=2.0, range=5.0, angle=80.0)
create_blink_light(pos, color="FFB200", brightness=2.5, range=7.0, blink_duration=1.0, blink_interval=2.0)
create_npc(pos, glb_url, name, personality="", animation="", auto_popup=True, rot=(0,0,0,1))
create_image(pos, image_url, scale=(2,1.5,0.03), rot=(0,0,0,1), transparent=False, borderless=False, emission=0.0)
create_video(pos, video_url, scale=(3,1.7,0.03), rot=(0,0,0,1), borderless=False, emission=0.0)
create_gun(pos, weapon_type=1, max_damage=20, min_damage=10, firerate=0.5, clip_size=12, infinite_ammo=False, automatic=False, color="000000")
create_destructible(pos, glb_url, scale=(1,1,1), max_health=100, respawn_time=10.0, multiplayer=False)
create_elemental(pos, element_type="lava", scale=(1,1,1), collider=True)
create_addressable(pos, effect_name, scale=(1,1,1), rot=(0,0,0,1))
create_leaderboard(pos, game_name, score_label="Score", time_based=False, style="blue")
```

## portals_effects — Effectors

Each returns `{"$type": "...", ...}` payload. Attach via `add_task_to_logic()`.

```
# Visibility
effector_show()
effector_hide()
effector_show_outline()
effector_hide_outline()
effector_duplicate(position=None, rotation=None, scale=None, destroy_after=0.0)

# Movement & Transform
effector_move_to_spot(position=None, rotation=None, scale=None, duration=0.0)
effector_move_item_to_player()
effector_animation(transform_states, states, loop=False, seamless=False, state_events=None)

# Player
effector_velocity(vel, local=True)                     — vel=[x,y,z]
effector_teleport(room_id, spawn_name="", spawn_radius=0.0)
effector_heal(amount)
effector_damage(amount)
effector_damage_over_time()
effector_lock_movement() / effector_unlock_movement()
effector_start_auto_run() / effector_stop_auto_run()
effector_emote(animation_name)                          — "Chicken","Wave","Salute","Jive","Salsa","Shuffling","Robot","Can Can","Sitting"
effector_mute_player()
effector_hide_all_players()
effector_lock_avatar_change() / effector_unlock_avatar_change()
effector_display_avatar_screen()
effector_change_avatar(url, persistent=True)
effector_change_movement_profile(profile)
effector_equip_wearable(item_id)

# Camera
effector_lock_camera() / effector_unlock_camera()
effector_camera_zoom(zoom_amount, lock_zoom=False)
effector_toggle_free_cam()
effector_change_cam_state(cam_state, transition_speed=1.0)
effector_camera_filter(url, alpha=1.0)
effector_toggle_cursor_lock(lock=True)

# UI
effector_notification(text, color="FFFFFF", hide_background=False)

# Values (Variables)
effector_display_value(label, color="FFFFFF")
effector_hide_value(label)
effector_update_value(label="", op=1, change=1.0)      — OMIT op to set value. 1=add, 2=sub, 3=mul, 4=div
effector_update_string_value(label, text)

# Function
effector_function(expression)                           — NCalc expression

# Quest/Task Control
effector_run_triggers(linked_tasks, use_random=False)
effector_reset_all_tasks()

# Timers
effector_start_timer(timer_name, countdown_id="")
effector_stop_timer(timer_name, countdown_id="")
effector_cancel_timer(timer_name)

# Leaderboard
effector_post_score(label="")                          — only for numeric values, not timers
effector_clear_leaderboard(label)
effector_open_leaderboard(leaderboard_name)

# Audio
effector_play_sound_once(url, distance=10.0)
effector_play_sound_loop(url, distance=-1.0, preload=True)
effector_stop_sound(url, fade_out=0.0)
effector_change_audius(playlist)

# Environment
effector_change_bloom(intensity, clamp=1.0, diffusion=1.0)
effector_change_time_of_day()
effector_rotate_skybox(rotation, duration=1.0)
effector_change_fog(color, distance)

# Communication
effector_send_iframe_message(message)
effector_change_voice_group(group)
effector_open_iframe(url) / effector_close_iframe(url)

# NPC
effector_npc_message(npc_name, message, repeatable=True)

# Token Swap
effector_show_token_swap(swap_id, typ=3) / effector_hide_token_swap()

# Dialogue
effector_dialogue_display(character_name, dialogue_nodes, creator_uid, repeatable=True, ...)

# Inventory
effector_refresh_inventory()
```

## portals_effects — Triggers

Each returns `{"$type": "..."}` payload.

```
# General (any item)
trigger_on_click()
trigger_on_collide() / trigger_collision_stopped()
trigger_hover_start() / trigger_hover_end()
trigger_player_logged_in()
trigger_player_died() / trigger_player_revived()
trigger_player_move() / trigger_player_stopped_moving()
trigger_key_pressed() / trigger_key_released()
trigger_mic_unmuted()
trigger_timer_stopped() / trigger_countdown_finished()
trigger_value_updated()
trigger_animation_stopped()
trigger_item_collected()
trigger_backpack_item_activated()
trigger_player_leave()
trigger_swap_volume()

# Trigger-cube only (prefabName: "Trigger")
trigger_on_enter() / trigger_on_exit()
```

## portals_effects — Wrappers & Helpers

```
basic_interaction(trigger, effector)         — direct trigger->effect, no quest
quest_effector(quest_id, quest_name, target_state, effector)  — fires on quest state
quest_trigger(quest_id, quest_name, target_state, trigger)    — advances quest on trigger
add_task_to_logic(logic_entry, task)         — attach one task to logic dict
add_tasks_to_logic(logic_entry, tasks)       — attach multiple tasks
```

## portals_effects — Quest Class

Bound helper that eliminates repeated quest_id/quest_name.

```python
q = Quest(number, name_suffix, creator, **kwargs)
# Properties: q.entries, q.id, q.name

quests.update(q.entries)                     # register quest pair

q.effector(logic[id_], target_state, eff)    # single quest-linked effect
q.on_state(logic[id_], target_state, [       # multiple effects, same state
    effector_hide(),
    effector_notification("Done!", "00FF00"),
])
q.trigger(logic[id_], target_state, trig)    # quest-linked trigger
```

Target states for quest_effector: `0`=Not Active, `1`=In Progress, `2`=Completed

Target states for quest_trigger (encoded transitions):
`111`=NotActive->Active, `121`=Active->Completed, `181`=NotActive->Completed,
`161`=Active->NotActive, `171`=Completed->NotActive, `101`=Any->NotActive,
`141`=Any->Completed, `151`=Any->Active, `131`=Completed->Active

## portals_utils — Helpers

```
yrot(deg)                                    — Y-axis rotation quaternion shorthand
quaternion_from_euler(yaw=0, pitch=0, roll=0) — full Euler to quaternion
create_quest_pair(number, name_suffix, creator, **kwargs) — returns {"entries", "quest_id", "quest_name"}
default_settings()                           — complete room settings template
serialize_logic(data)                        — serialize logic values to JSON strings before output
validate_room_data(data)                     — basic pre-push validation
generate_build_summary(game_name, items, logic, quests, zones=None, spectacle_moments=None)
```
