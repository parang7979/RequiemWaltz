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
	await _charge_controls()
	await _switch_controls()
	await _charged_hits()
	stage.queue_free()
	await create_timer(0.35).timeout
	print("Requiem chain review: %d failures." % failures)
	quit(failures)


func _room(direction: float) -> RoomScript:
	var room := ROOM.instantiate() as RoomScript
	stage.add_child(room)
	room.set_physics_process(false)
	if not capture:
		for voice in room.voices.values():
			voice.stream = null
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
	_mouse(room, MOUSE_BUTTON_LEFT, true)


func _mouse(room: Node2D, button: MouseButton, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.position = room.cursor
	event.button_index = button
	event.pressed = pressed
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


func _advance(room: RoomScript, ticks: int) -> void:
	for i in ticks:
		room._physics_process(STEP)


func _charge_controls() -> void:
	var room := _room(1.0)
	room.enemies[0].hp = 0
	_mouse(room, MOUSE_BUTTON_RIGHT, true)
	_advance(room, 10)
	_mouse(room, MOUSE_BUTTON_RIGHT, false)
	_check(room.clip == "idle" and room.charge_elapsed < 0.0, "early release cancels the charge")
	_attack(room)
	_advance(room, 1)
	_check(room.clip == "action" and not room.charged_attack, "left click remains a regular attack")
	_advance(room, 25)
	_mouse(room, MOUSE_BUTTON_RIGHT, true)
	_advance(room, 32)
	_check(room.clip == "idle" and room.charge_elapsed >= room.CHARGE_TIME, "full charge waits for release")
	room._point(Vector2(222, 264))
	_mouse(room, MOUSE_BUTTON_RIGHT, false)
	_check(room.clip == "action" and room.charged_attack and not room.counter_attack
		and is_equal_approx(room.locked_aim, room._shoulder().angle_to_point(room.cursor)),
		"charge locks the aim at release and stays separate from the counter")
	room.time_ms = room._release_time() + room._strike_duration() / 2.0
	_check(is_zero_approx(angle_difference(room._hand_pose().get_rotation(), room.locked_aim)),
		"the wide gauntlet strike sweeps through the aimed direction")
	room.time_ms = 0.0
	_advance(room, 30)
	_mouse(room, MOUSE_BUTTON_RIGHT, true)
	_advance(room, 10)
	_press(room, KEY_SPACE)
	_advance(room, 1)
	_mouse(room, MOUSE_BUTTON_RIGHT, false)
	_check(room.charge_elapsed < 0.0 and room.clip == "idle", "dodge cancels the held charge")
	_attack(room)
	_advance(room, 24)
	_check(room.counter_attack, "attack buffered during dodge still starts the gauntlet counter")
	_advance(room, 45)
	_mouse(room, MOUSE_BUTTON_RIGHT, true)
	_advance(room, 10)
	_press(room, KEY_Q)
	_advance(room, 1)
	_mouse(room, MOUSE_BUTTON_RIGHT, false)
	_check(room.clip == "exit" and room.charge_elapsed < 0.0, "starting a switch cancels the held charge")
	room.queue_free()
	await process_frame


func _switch_controls() -> void:
	var room := _room(1.0)
	room.enemies[0].hp = 0
	room.available_forms = 1 << room.CHAIN_FORM
	_press(room, KEY_E)
	_advance(room, 1)
	_press(room, KEY_2)
	_advance(room, 18)
	_check(room.form == room.CHAIN_FORM and room.clip == "idle" and room.switch_cooldown > 0.0,
		"E skips locked forms and the switch target stays fixed")
	_press(room, KEY_Q)
	_advance(room, 1)
	_check(room.clip == "idle" and room.wanted_form == 0, "Q queues the next swap during the shared cooldown")
	_attack(room)
	_advance(room, 1)
	_check(room.clip == "action", "a new form can attack during the switch cooldown")
	_advance(room, 70)
	_check(room.form == 0 and room.clip == "idle", "the queued switch waits for the attack to recover")
	_advance(room, 30)
	_press(room, KEY_F2)
	_press(room, KEY_Q)
	_advance(room, 1)
	_check(room.clip == "exit" and is_equal_approx(room.switch_cooldown, 0.35),
		"the upgraded switch interval applies in both directions")
	_press(room, KEY_R)
	room.available_forms = 0
	_press(room, KEY_Q)
	_press(room, KEY_E)
	_advance(room, 1)
	_check(room.form == 0 and room.clip == "idle" and room.switch_cooldown == 0.0,
		"switching with only the gauntlet consumes no cooldown")
	room.queue_free()
	await process_frame


func _charged_hits() -> void:
	var room := _room(1.0)
	var target: Node2D = room.enemies[0]
	var other: Node2D = room.enemies[1]
	other.position = target.position + Vector2(45.0, 0.0)
	other.hp = 3
	other.show()
	_press(room, KEY_Q)
	_advance(room, 18)
	_mouse(room, MOUSE_BUTTON_RIGHT, true)
	_advance(room, 29)
	_mouse(room, MOUSE_BUTTON_RIGHT, false)
	var pull := 0.0
	for i in 55:
		room._physics_process(STEP)
		pull = minf(pull, target.push.x)
	_check(target.hp == 2 and other.hp == 3 and pull < -350.0, "charged chain pulls one target once")
	room.queue_free()
	await process_frame

	for charged in [false, true]:
		room = _room(1.0)
		room.player = Vector2(155, 222)
		target = room.enemies[0]
		var far := Vector2(530, 222)
		target.position = far
		room._point(target.hit_center())
		_press(room, KEY_E)
		_advance(room, 18)
		if charged:
			_mouse(room, MOUSE_BUTTON_RIGHT, true)
			_advance(room, 29)
			_mouse(room, MOUSE_BUTTON_RIGHT, false)
		else:
			_attack(room)
		for i in 70:
			target.position = far
			room._physics_process(STEP)
		_check(target.hp == (2 if charged else 3), "only the charged bow reaches the distant target")
		room.queue_free()
		await process_frame

	room = _room(1.0)
	target = room.enemies[0]
	_press(room, KEY_3)
	_advance(room, 18)
	_mouse(room, MOUSE_BUTTON_RIGHT, true)
	_advance(room, 29)
	_mouse(room, MOUSE_BUTTON_RIGHT, false)
	var push := 0.0
	for i in 40:
		room._physics_process(STEP)
		push = maxf(push, target.push.x)
	_check(target.hp == 2 and push > 450.0, "charged cannon increases knockback")
	room.queue_free()
	await process_frame


func _check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
