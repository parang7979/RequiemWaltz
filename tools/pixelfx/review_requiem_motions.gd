extends SceneTree

const ROOM = preload("res://scenes/rooms/requiem_forms_review.tscn")
const TrueForm = preload("res://scenes/actors/requiem_true_form.gd")
const OUTPUT := "res://.local/requiem-motion-capture"
const STEP := 1.0 / 60.0
const TICKS := 108

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
	await _action("hand", 0)
	await _action("counter", 0)
	await _action("bow", 1)
	await _action("cannon", 2)
	await _switch_forms()
	await _defeat(false)
	await _defeat(true)
	stage.queue_free()
	await create_timer(0.4).timeout
	print("Requiem motion review: %d failures." % failures)
	quit(failures)


func _room(form: int, left := false) -> Node2D:
	var room = ROOM.instantiate()
	stage.add_child(room)
	room.set_physics_process(false)
	room.player = Vector2(292, 222)
	room.follow_origin = room._shoulder()
	room.cursor = room.player + Vector2(-112.0 if left else 112.0, -20.0)
	room.form = form
	room.wanted_form = form
	room._update_aim()
	room.follow_bearing = room.aim
	room._update_pose()
	for enemy in room.enemies:
		enemy.hide()
		enemy.position = Vector2(558, 123)
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


func _action(label: String, form: int) -> void:
	var room = _room(form)
	var counter := label == "counter"
	var reached_release := false
	var used_counter := false
	for tick in TICKS:
		if counter and tick == 12:
			_press(room, KEY_SPACE)
		if tick == (19 if counter else 14):
			_attack(room)
		room._physics_process(STEP)
		reached_release = reached_release or (room.clip == "action" and room.released)
		used_counter = used_counter or room.counter_attack
		await _capture_tick(label, tick)
	_check(reached_release and used_counter == counter, label + " releases from the expected input")
	room.queue_free()
	await process_frame


func _switch_forms() -> void:
	var room = _room(0)
	var exits := {}
	var enters := {}
	for tick in TICKS:
		match tick:
			12: _press(room, KEY_2)
			39: _press(room, KEY_3)
			66: _press(room, KEY_1)
		room._physics_process(STEP)
		if room.clip == "exit":
			exits[room.form] = true
		if room.clip == "enter":
			enters[room.form] = true
		await _capture_tick("switch", tick)
	_check(exits.size() == 3 and enters.size() == 3 and room.form == 0, "complete weapon switch cycle")
	room.queue_free()
	await process_frame


func _defeat(left: bool) -> void:
	var room = _room(0, left)
	room.player_hp = 1
	var enemy = room.enemies[0]
	enemy.position = room.player + Vector2(20, 0)
	room._receive_hit(enemy)
	var concern_frames := {}
	var vanish_frames := {}
	var mirror := 0.0
	for tick in TICKS:
		room._physics_process(STEP)
		if room.true_requiem.visible:
			var cell: Texture2D = room.true_requiem.texture
			if room.defeat_elapsed < room.DEFEAT_DISPERSE_TIME:
				concern_frames[cell] = true
				mirror = signf(room.true_requiem.scale.x)
			else:
				vanish_frames[cell] = true
				_check(cell == TrueForm.texture_at(room.defeat_elapsed - room.DEFEAT_DISPERSE_TIME,
					TrueForm.VANISH), "defeat samples the new vanish sheet")
		if not left:
			await _capture_tick("defeat", tick)
	_check(concern_frames.size() >= 24 and vanish_frames.size() == 13 and not room.true_requiem.visible,
		"concern and vanish finish")
	_check(mirror == (1.0 if left else -1.0), "true form mirrors toward Waltz")
	room._reset()
	_check(not room.true_requiem.visible and room.defeat_elapsed < 0.0, "reset restores combat")
	room.queue_free()
	await process_frame


func _capture_tick(label: String, tick: int) -> void:
	if not capture:
		return
	await process_frame
	if tick % 2 != 0:
		return
	await RenderingServer.frame_post_draw
	var image := stage.get_texture().get_image()
	_check(image.save_png("%s/%s-%02d.png" % [OUTPUT, label, tick / 2]) == OK, "capture writes")


func _check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
