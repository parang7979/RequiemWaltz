extends SceneTree

const ROOM := preload("res://scenes/rooms/requiem_forms_review.tscn")
const RoomScript := preload("res://scenes/rooms/requiem_forms_review.gd")
const FIRE := preload("res://assets/vfx/requiem_forms/shift.tres")
const OUTPUT := "res://.local/requiem-chain-capture"
const STEP := 1.0 / 60.0

var stage: SubViewport
var capture := false
var failures := 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	capture = DisplayServer.get_name() != "headless"
	if capture:
		DirAccess.make_dir_recursive_absolute(OUTPUT)
	stage = SubViewport.new()
	stage.size = Vector2i(640, 360)
	stage.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(stage)
	await process_frame
	await _fight(1.0)
	await _fight(-1.0)
	await _defeat_and_reset()
	stage.queue_free()
	await create_timer(0.35).timeout
	print("Requiem chain review: %d failures." % failures)
	quit(failures)


func _room(direction: float) -> RoomScript:
	var room := ROOM.instantiate() as RoomScript
	stage.add_child(room)
	room.set_physics_process(false)
	room.player = Vector2(295, 222)
	room.follow_origin = room._shoulder()
	room.enemies[0].position = room.player + Vector2(174.0 * direction, 0)
	room.enemies[0].hp = 3
	for i in range(1, room.enemies.size()):
		room.enemies[i].hide()
		room.enemies[i].hp = 0
	room._point(room.enemies[0].hit_center())
	room.follow_bearing = room.aim
	room._update_pose()
	return room


func _press(room: Node2D, key: Key) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = key
	event.pressed = true
	room._input(event)


func _attack(room: Node2D) -> void:
	var event := InputEventMouseButton.new()
	event.position = room.cursor
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	room._input(event)


func _fight(direction: float) -> void:
	var room := _room(direction)
	var enemy: Node2D = room.enemies[0]
	var legs: Array[int] = []
	var hp: int = enemy.hp
	var arrived := false
	var departed := false
	var cast_visible := false
	var inbound_push := 0.0
	for tick in 114:
		if tick == 8:
			_press(room, KEY_4)
		elif tick == 28:
			_attack(room)
		elif tick == 60:
			_press(room, KEY_2)
		room._physics_process(STEP)
		if room.form == room.CHAIN_FORM and room.clip == "enter":
			arrived = arrived or is_instance_valid(room.fluid) and room.fluid.sprite_frames == FIRE
		if room.form == room.CHAIN_FORM and room.clip == "exit":
			departed = departed or is_instance_valid(room.fluid) and room.fluid.sprite_frames == FIRE
		if room.form == room.CHAIN_FORM and room.clip == "action":
			cast_visible = cast_visible or room.sword.visible and room.chain.visible
			if enemy.hp < hp:
				var leg: int = room.chain.hit_leg(room.time_ms)
				legs.append(leg)
				if leg == -1:
					inbound_push = enemy.push.x * direction
				hp = enemy.hp
		if capture and direction > 0.0:
			await process_frame
			await RenderingServer.frame_post_draw
			var frame := stage.get_texture().get_image()
			_check(frame.save_png("%s/chain-%03d.png" % [OUTPUT, tick]) == OK, "save chain capture")
	_check(arrived and departed and room.form == 1, "key 4 enters and queued key 2 exits with shared flame")
	_check(cast_visible, "sword and chain stay visible during cast")
	_check(legs == [1, -1] and enemy.hp == 1 and inbound_push < 0.0,
		"one outbound hit and one pulling hit, direction %.0f. Actual legs %s." % [direction, legs])
	room.queue_free()
	await process_frame


func _defeat_and_reset() -> void:
	var room := _room(1.0)
	_press(room, KEY_4)
	for i in 20:
		room._physics_process(STEP)
	room.player_hp = 1
	room._receive_hit(room.enemies[0])
	for i in 45:
		room._physics_process(STEP)
	_check(not room.chain.visible and not room.sword.visible, "defeat hides chain and sword")
	_press(room, KEY_R)
	room._physics_process(STEP)
	_check(room.form == 0 and not room.chain.visible and room.player_hp == 3, "reset returns to gauntlet")
	room.queue_free()
	await process_frame


func _check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
