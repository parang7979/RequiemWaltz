extends Node2D

const BUNDLE := "res://assets/actors/requiem_forms/"
const WALK_BUNDLE := "res://assets/actors/waltz_walk/"
const REACTION_BUNDLE := "res://assets/actors/waltz_reactions/"
const DEFEAT_BUNDLE := "res://assets/actors/waltz_defeat/"
const WALK_TEXTURES := {
	"front_right": preload("res://assets/actors/waltz_walk/walk_front_right_color.png"),
	"back_right": preload("res://assets/actors/waltz_walk/walk_back_right_color.png"),
}
const Chain := preload("res://scenes/actors/requiem_chain.gd")
const TAIL = preload("res://assets/vfx/requiem_forms/tail.tres")
const REFORM = preload("res://assets/vfx/requiem_forms/shift.tres")
const DISPERSE = preload("res://assets/vfx/requiem_forms/disperse.tres")
const TrueForm = preload("res://scenes/actors/requiem_true_form.gd")
const BOW_FLASH = preload("res://assets/vfx/requiem_forms/bow_release.tres")
const CANNON_FLASH = preload("res://assets/vfx/requiem_forms/cannon_release.tres")
const HAND_CUT = preload("res://assets/vfx/requiem_forms/hand_cut.tres")
const COUNTER_CUT = preload("res://assets/vfx/requiem_forms/counter_cut.tres")
const HIT = preload("res://assets/vfx/combat_study/impact.tres")
const Pursuer := preload("res://scenes/actors/crypt_skeleton.gd")
const SOUNDS := {
	"hand": preload("res://assets/audio/combat_study_swing.wav"),
	"bow": preload("res://assets/audio/waltz_bow.wav"),
	"cannon": preload("res://assets/audio/waltz_cannon.wav"),
	"chain": preload("res://assets/audio/combat_study_swing.wav"),
	"hit": preload("res://assets/audio/combat_study_impact.wav"),
}
const FORMS := ["hand", "bow", "cannon", "chain"]
const LABELS := ["장갑", "활", "대포", "사슬"]
const CHAIN_FORM := 3
const SPAWNS := [Vector2(376, 218), Vector2(470, 150), Vector2(468, 275), Vector2(119, 144)]
const FIELD := Rect2(16, 45, 608, 277)
const PLAY_AREA := Rect2(70, 118, 499, 186)
const START := Vector2(222, 220)
const SHOULDER_HEIGHT := 22.0
const MOVE_SPEED := 113.0
const DODGE_TIME := 0.15
const DODGE_DISTANCE := 43.0
const DODGE_INVULNERABLE := 0.126
const DODGE_COOLDOWN := 0.38
const HURT_INVULNERABLE := 0.65
const HURT_PUSH_TIME := 0.125
const HURT_PUSH_DISTANCE := 23.0
const REQUIEM_FLINCH_TIME := 0.18
const DEFEAT_MORPH_TIME := 0.11
const DEFEAT_REVEAL_TIME := 0.24
const DEFEAT_DISPERSE_TIME := 1.10
const DEFEAT_VANISH_TIME := 1.52
const FOLLOW_STIFFNESS := 245.0
const FOLLOW_DODGE_STIFFNESS := 90.0
const FOLLOW_DAMPING := 17.0
const FOLLOW_TURN_SPEED := 14.0
const HAND_REACH := 92.0
const HAND_GRIP_TURN := PI * 62.0 / 180.0
const HAND_SWING_ANGLE := PI * 64.0 / 180.0
const HAND_STRIKE_MS := 118.0
const COUNTER_WINDOW := 0.14
const COUNTER_WINDUP_MS := 100.0
const COUNTER_STRIKE_MS := 150.0
const COUNTER_SWEEP_END_MS := COUNTER_WINDUP_MS + COUNTER_STRIKE_MS
# The open lid and the first step back into the gait in counter_peek.
const COUNTER_PEEK_GLANCE_FROM_MS := 24.0
const COUNTER_PEEK_GLANCE_TO_MS := 204.0
const COUNTER_SWING_ANGLE := deg_to_rad(105.0)
const COUNTER_REACH := 106.0
const INK := Color("#241a2d")
const LIGHT := Color("#f5e3df")
const GOLD := Color("#efc293")
const GHOST := Color("#e9b5fa")

var manifest: Dictionary
var walk_manifest: Dictionary
var walk_cycle_ms := 0.0
var reaction_manifest: Dictionary
var reaction_textures: Dictionary[String, Texture2D] = {}
var reaction_durations: Dictionary[String, float] = {}
var defeat_manifest: Dictionary
var defeat_textures: Dictionary[String, Texture2D] = {}
var textures: Dictionary[String, Texture2D] = {}
var voices: Dictionary[String, AudioStreamPlayer] = {}
var emissive := CanvasItemMaterial.new()
var hero: Sprite2D
var hero_upper: Sprite2D
var armor: Sprite2D
var sword: Sprite2D
var chain: Chain
var spirit: AnimatedSprite2D
var true_requiem: Sprite2D
var fluid: AnimatedSprite2D
var hand_cut: AnimatedSprite2D
var bolt: Sprite2D
var bowstring: Node2D
var hud: Node2D
var font: SystemFont
var title: SystemFont
var enemies: Array[Pursuer] = []

var form := 0
var wanted_form := 0
var clip := "idle"
var time_ms := 0.0
var idle_clock := 0.0
var released := false
var player := START
var velocity := Vector2.ZERO
var follow_origin := START - Vector2(0, SHOULDER_HEIGHT)
var follow_velocity := Vector2.ZERO
var follow_bearing := -0.02
var dodge_requested := false
var dodge_elapsed := DODGE_TIME
var dodge_cooldown := 0.0
var dodge_direction := Vector2.ZERO
var counter_window := 0.0
var counter_attack := false
var counter_start := Transform2D.IDENTITY
var counter_velocity := Vector2.ZERO
var counter_target: Pursuer
var counter_peek_ms := -1.0
var peek_heading := Vector2.ONE
var player_hp := 3
var hurt_time := 0.0
var hurt_direction := Vector2.ZERO
var defeat_elapsed := -1.0
var defeat_mount := Vector2.ZERO
var defeat_side := 1.0
var impact_ticks := 0
var walk_heading := Vector2(1, 1)
var walk_time_ms := 0.0
var walking := false
var cursor := Vector2(372, 194)
var pointer := false
var aim := -0.02
var locked_aim := 0.0
var swing := -1.0
var attack_reach := HAND_REACH
var attack_scale := 1.0
var attack_queued := false
var bolt_velocity := Vector2.ZERO
var bolt_muzzle := Vector2.ZERO
var cannon_bolt := false
var rig_at := Vector2.ZERO
var rig_basis := Transform2D.IDENTITY
var pose_points: Dictionary
var mounted_position := Vector2.ZERO
var blade_heading := 0.0
var previous_grip := Vector2.ZERO
var previous_tip := Vector2.ZERO
var hit_in_swing: Array[int] = []
var chain_return_hits: Array[int] = []
var side := "front_right"


func _ready() -> void:
	manifest = JSON.parse_string(FileAccess.get_file_as_string(BUNDLE + "clips.json"))
	walk_manifest = JSON.parse_string(FileAccess.get_file_as_string(WALK_BUNDLE + "clips.json"))
	walk_cycle_ms = _duration_ms(walk_manifest.clips.walk_front_right.frames)
	reaction_manifest = JSON.parse_string(FileAccess.get_file_as_string(REACTION_BUNDLE + "clips.json"))
	for name: String in reaction_manifest.clips:
		reaction_textures[name] = load(REACTION_BUNDLE + reaction_manifest.clips[name].maps.color)
		reaction_durations[name] = _duration_ms(reaction_manifest.clips[name].frames)
	defeat_manifest = JSON.parse_string(FileAccess.get_file_as_string(DEFEAT_BUNDLE + "clips.json"))
	for name: String in defeat_manifest.clips:
		defeat_textures[name] = load(DEFEAT_BUNDLE + defeat_manifest.clips[name].maps.color)
	emissive.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	emissive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	font = SystemFont.new()
	font.font_names = PackedStringArray(["Malgun Gothic", "Segoe UI"])
	title = SystemFont.new()
	title.font_names = PackedStringArray(["Georgia", "Cambria"])
	hero = _sprite(1)
	hero_upper = Sprite2D.new()
	hero_upper.centered = false
	hero_upper.hide()
	hero.add_child(hero_upper)
	armor = _sprite(6)
	sword = _new_sword()
	chain = Chain.new()
	chain.configure(manifest.chain_cast, _length("chain_front_right_action"))
	add_child(chain)
	spirit = _effect(TAIL, Vector2(55, 27), 2, true)
	true_requiem = _sprite(5)
	true_requiem.offset = -TrueForm.PIVOT
	true_requiem.hide()
	bowstring = Node2D.new()
	bowstring.z_index = 4
	add_child(bowstring)
	bowstring.draw.connect(_draw_bowstring)
	hud = Node2D.new()
	hud.z_index = 20
	add_child(hud)
	hud.draw.connect(_draw_hud)
	for key: String in SOUNDS:
		var voice := AudioStreamPlayer.new()
		voice.stream = SOUNDS[key]
		voice.bus = &"SFX"
		voice.volume_db = -4.0
		add_child(voice)
		voices[key] = voice
	get_window().mouse_exited.connect(_show_cursor)
	get_window().focus_exited.connect(_show_cursor)
	_spawn_enemies()
	_update_pose()


func _sprite(layer: int) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.z_index = layer
	add_child(sprite)
	return sprite


func _new_sword() -> Sprite2D:
	var sprite := _sprite(5)
	_set_sprite(sprite, "sword", 0)
	var glow := Sprite2D.new()
	glow.centered = false
	glow.texture = _texture(manifest.clips.sword.maps.emissive)
	glow.offset = sprite.offset
	glow.material = emissive
	glow.modulate.a = 0.72
	sprite.add_child(glow)
	return sprite


func _texture(file: String) -> Texture2D:
	if not textures.has(file):
		textures[file] = load(BUNDLE + file) as Texture2D
	return textures[file]


func _set_sprite(sprite: Sprite2D, name: String, frame: int) -> void:
	var data: Dictionary = manifest.clips[name]
	_set_sprite_cell(sprite, _texture(data.maps.color), data.frames[frame], data.pivot)


func _set_sprite_cell(sprite: Sprite2D, texture: Texture2D, cell: Dictionary, pivot: Array) -> void:
	sprite.texture = texture
	sprite.region_enabled = true
	sprite.region_rect = Rect2(cell.x, cell.y, cell.w, cell.h)
	sprite.offset = -Vector2(pivot[0], pivot[1])


func _frame_at(frames: Array, elapsed_ms: float) -> int:
	var index := 0
	while index < frames.size() - 1 and elapsed_ms >= float(frames[index].ms):
		elapsed_ms -= float(frames[index].ms)
		index += 1
	return index


func _effect(frames: SpriteFrames, pivot: Vector2, layer: int, glowing := false) -> AnimatedSprite2D:
	var effect := AnimatedSprite2D.new()
	effect.sprite_frames = frames
	effect.animation = &"fx"
	effect.centered = false
	effect.offset = -pivot
	effect.z_index = layer
	if glowing:
		effect.material = emissive
	add_child(effect)
	if not frames.get_animation_loop(&"fx"):
		effect.animation_finished.connect(effect.queue_free)
	effect.play()
	return effect


func _input(event: InputEvent) -> void:
	if defeat_elapsed >= 0.0:
		if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_R:
			_reset()
		return
	if event is InputEventMouseMotion:
		_point(event.position)
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_point(event.position)
		if pointer and player_hp > 0:
			attack_queued = true
	elif event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode >= KEY_1 and event.physical_keycode < KEY_1 + FORMS.size():
			wanted_form = event.physical_keycode - KEY_1
		elif event.physical_keycode == KEY_SPACE:
			dodge_requested = true
		elif event.physical_keycode == KEY_R:
			_reset()


func _point(at: Vector2) -> void:
	cursor = at
	pointer = FIELD.has_point(at)
	Input.mouse_mode = Input.MOUSE_MODE_HIDDEN if pointer else Input.MOUSE_MODE_VISIBLE


func _show_cursor() -> void:
	pointer = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _reset() -> void:
	player = START
	velocity = Vector2.ZERO
	follow_origin = _shoulder()
	follow_velocity = Vector2.ZERO
	dodge_requested = false
	dodge_elapsed = DODGE_TIME
	dodge_cooldown = 0.0
	dodge_direction = Vector2.ZERO
	counter_window = 0.0
	counter_attack = false
	counter_target = null
	counter_peek_ms = -1.0
	player_hp = 3
	hurt_time = 0.0
	hurt_direction = Vector2.ZERO
	defeat_elapsed = -1.0
	true_requiem.hide()
	armor.modulate = Color.WHITE
	armor.show()
	spirit.modulate = Color.WHITE
	impact_ticks = 0
	walk_heading = Vector2(1, 1)
	walk_time_ms = 0.0
	walking = false
	form = 0
	chain.hide()
	wanted_form = 0
	clip = "idle"
	time_ms = 0.0
	cursor = Vector2(372, 194)
	aim = -0.02
	follow_bearing = aim
	side = "front_right"
	attack_queued = false
	if is_instance_valid(fluid):
		fluid.queue_free()
		fluid = null
	if is_instance_valid(hand_cut):
		hand_cut.queue_free()
		hand_cut = null
	if is_instance_valid(bolt):
		bolt.queue_free()
		bolt = null
	_spawn_enemies()
	_show_cursor()


func _spawn_enemies() -> void:
	for enemy in enemies:
		enemy.hide()
		enemy.queue_free()
	enemies.clear()
	for i in SPAWNS.size():
		var enemy := Pursuer.new()
		enemy.configure(SPAWNS[i], 0.12 * i)
		add_child(enemy)
		enemies.append(enemy)


func _physics_process(delta: float) -> void:
	idle_clock += delta
	hurt_time = maxf(0.0, hurt_time - delta)
	if defeat_elapsed >= 0.0:
		_update_defeat(delta)
		return
	counter_window = maxf(0.0, counter_window - delta)
	_move(delta)
	_update_aim()
	var stopped := impact_ticks > 0
	if stopped:
		impact_ticks -= 1
	else:
		_advance_enemies(delta)
		if defeat_elapsed >= 0.0:
			_update_defeat(0.0)
			return
	_update_follow(delta)
	if not stopped:
		_update_clip(delta)
	_update_pose()
	if not stopped:
		if clip == "action" and time_ms >= _release_time() and not released:
			released = true
			_release()
		if clip == "action" and released:
			if form == 0 and time_ms <= _release_time() + _strike_duration():
				_check_sweep()
			elif form == CHAIN_FORM:
				_check_chain_strike()
		_fly(delta)
		_update_counter_peek(delta * 1000.0)
	_update_waltz_sprite()
	_update_hand_cut()
	sword.visible = form != 2 and (clip == "idle" or clip == "action") and not is_instance_valid(bolt) \
		and (form == 0 or form == CHAIN_FORM or clip != "action" or not released)
	queue_redraw()
	bowstring.queue_redraw()
	hud.queue_redraw()


func _move(delta: float) -> void:
	var x := float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A))
	var y := float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W))
	var step := Vector2(x, y).normalized() if player_hp > 0 else Vector2.ZERO
	var before := player
	var hurt_age := _hurt_age()
	var pushing := hurt_age - delta < HURT_PUSH_TIME
	dodge_cooldown = maxf(0.0, dodge_cooldown - delta)
	if dodge_requested:
		dodge_requested = false
		if player_hp > 0 and not pushing and not _is_dodging() and dodge_cooldown == 0.0:
			_start_dodge(step)
	if pushing:
		var previous := 1.0 - (hurt_age - delta) / HURT_PUSH_TIME
		var remaining := 1.0 - minf(hurt_age / HURT_PUSH_TIME, 1.0)
		player += hurt_direction * HURT_PUSH_DISTANCE * (previous * previous - remaining * remaining)
		step = Vector2.ZERO
	elif _is_dodging():
		var remaining := 1.0 - dodge_elapsed / DODGE_TIME
		dodge_elapsed = minf(DODGE_TIME, dodge_elapsed + delta)
		var next := 1.0 - dodge_elapsed / DODGE_TIME
		player += dodge_direction * DODGE_DISTANCE * (remaining * remaining - next * next)
		step = dodge_direction
	else:
		velocity = velocity.move_toward(step * MOVE_SPEED, 1050.0 * delta)
		player += velocity * delta
	player = player.clamp(PLAY_AREA.position, PLAY_AREA.end)
	if step != Vector2.ZERO:
		if absf(step.x) > 0.06:
			walk_heading.x = signf(step.x)
		if absf(step.y) > 0.06:
			walk_heading.y = signf(step.y)
	var distance := before.distance_to(player)
	walking = not pushing and distance > 13.0 * delta
	if walking:
		# Advance the gait from actual movement so bumping into a wall can settle to idle.
		walk_time_ms = fmod(walk_time_ms + distance * 1000.0 / MOVE_SPEED, walk_cycle_ms)
	else:
		walk_time_ms = 0.0


func _start_dodge(step: Vector2) -> void:
	dodge_direction = step if step != Vector2.ZERO else -Vector2.from_angle(aim)
	dodge_elapsed = 0.0
	dodge_cooldown = DODGE_COOLDOWN
	counter_window = DODGE_TIME + COUNTER_WINDOW
	counter_target = null
	counter_peek_ms = -1.0
	velocity = Vector2.ZERO
	if clip == "action":
		_begin("idle")


func _is_dodging() -> bool:
	return dodge_elapsed < DODGE_TIME


func _hurt_age() -> float:
	return HURT_INVULNERABLE - hurt_time


func _update_counter_peek(delta_ms: float) -> void:
	var sweep_end := COUNTER_SWEEP_END_MS - 0.001
	if counter_peek_ms >= 0.0:
		var previous_ms := counter_peek_ms
		counter_peek_ms += delta_ms
		if previous_ms < COUNTER_PEEK_GLANCE_TO_MS and counter_peek_ms >= COUNTER_PEEK_GLANCE_TO_MS and not walking:
			walk_heading = peek_heading
		if counter_peek_ms >= reaction_durations["counter_peek_front_right"]:
			counter_peek_ms = -1.0
			counter_target = null
	elif counter_attack and time_ms >= sweep_end and time_ms - delta_ms < sweep_end:
		counter_peek_ms = maxf(0.0, time_ms - COUNTER_SWEEP_END_MS)
		var glance := Vector2.from_angle(locked_aim)
		if is_instance_valid(counter_target):
			glance = _shoulder().direction_to(counter_target.hit_center())
		peek_heading.x = signf(glance.x) if absf(glance.x) > 0.18 else walk_heading.x
		peek_heading.y = -1.0 if glance.y < -0.27 else 1.0


func _update_waltz_sprite() -> void:
	var face := "back_right" if walk_heading.y < 0.0 else "front_right"
	var hurt_ms := _hurt_age() * 1000.0
	if walking:
		var frames: Array = walk_manifest.clips["walk_" + face].frames
		_set_sprite_cell(hero, WALK_TEXTURES[face], frames[_frame_at(frames, walk_time_ms)], walk_manifest.pivot)
	else:
		_set_sprite(hero, "waltz_" + face, 0)
	hero.scale.x = signf(walk_heading.x)
	hero.position = player.round()
	var tint := Color.WHITE
	if hurt_ms < 45.0:
		tint = Color(1.52, 0.83, 0.88)
	elif _is_dodging():
		tint = Color(1.0, 1.0, 1.0, 0.78)
	hero.modulate = tint
	hero_upper.scale.x = 1.0
	if _is_dodging():
		_apply_upper_reaction("dodge_" + face, dodge_elapsed * 1000.0)
	elif hurt_ms < reaction_durations["hurt_" + face] and clip != "action":
		_apply_upper_reaction("hurt_" + face, hurt_ms)
	elif counter_peek_ms >= 0.0:
		var heading := walk_heading
		if counter_peek_ms >= COUNTER_PEEK_GLANCE_FROM_MS and counter_peek_ms < COUNTER_PEEK_GLANCE_TO_MS:
			heading = peek_heading
		var peek_face := "back_right" if heading.y < 0.0 else "front_right"
		hero_upper.scale.x = heading.x * hero.scale.x
		_apply_upper_reaction("counter_peek_" + peek_face, counter_peek_ms)
	elif counter_attack and time_ms <= COUNTER_SWEEP_END_MS:
		_apply_upper_reaction("hood_grab_" + face, time_ms)
	elif clip == "action" and not counter_attack:
		var reaction := "cower_" + face
		_apply_upper_reaction(reaction, reaction_durations[reaction] * time_ms / _clip_duration())
	else:
		hero_upper.hide()


func _apply_upper_reaction(id: String, elapsed_ms: float) -> void:
	var frames: Array = reaction_manifest.clips[id].frames
	_set_sprite_cell(hero_upper, reaction_textures[id], frames[_frame_at(frames, elapsed_ms)], reaction_manifest.pivot)
	hero_upper.show()
	# Keep the walk legs under the posed upper body, including the hem's contact row.
	var hem := float(reaction_manifest.hem_row) - 1.0
	var legs := hero.region_rect
	legs.position.y += hem
	legs.size.y -= hem
	hero.region_rect = legs
	hero.offset.y += hem


func _update_follow(delta: float) -> void:
	var stiffness := FOLLOW_DODGE_STIFFNESS if _is_dodging() else FOLLOW_STIFFNESS
	var force := (_shoulder() - follow_origin) * stiffness - follow_velocity * FOLLOW_DAMPING
	follow_velocity += force * delta
	follow_origin += follow_velocity * delta
	follow_bearing = lerp_angle(follow_bearing, aim, 1.0 - exp(-FOLLOW_TURN_SPEED * delta))


func _floating_mount() -> Vector2:
	return follow_origin + Vector2(sin(idle_clock * 4.1), sin(idle_clock * 5.5) * 1.8)


func _advance_enemies(delta: float) -> void:
	for enemy in enemies:
		var separation := Vector2.ZERO
		if enemy.hp > 0:
			for other in enemies:
				if other == enemy or other.hp <= 0:
					continue
				var away := enemy.position - other.position
				var distance := away.length()
				if distance < 31.0:
					separation += away.normalized() * (1.0 - distance / 31.0)
		if enemy.advance(delta, player, separation, PLAY_AREA) and player_hp > 0 \
				and hurt_time <= 0.0 and dodge_elapsed >= DODGE_INVULNERABLE:
			_receive_hit(enemy)
			if player_hp == 0:
				break


func _receive_hit(enemy: Pursuer) -> void:
	player_hp -= 1
	hurt_time = HURT_INVULNERABLE
	hurt_direction = enemy.position.direction_to(player)
	if hurt_direction.is_zero_approx():
		hurt_direction = Vector2(-enemy.facing, 0.0)
	if absf(hurt_direction.x) > 0.18:
		walk_heading.x = -signf(hurt_direction.x)
	walk_heading.y = -1.0 if hurt_direction.y > 0.33 else 1.0
	velocity = Vector2.ZERO
	walking = false
	walk_time_ms = 0.0
	dodge_elapsed = DODGE_TIME
	counter_window = 0.0
	counter_target = null
	counter_peek_ms = -1.0
	attack_queued = false
	if clip == "action":
		_begin("idle")
	follow_velocity = follow_velocity * 0.45 + hurt_direction * 215.0 + Vector2(0, -192)
	var pop := _effect(HIT, Vector2(52, 53), 9)
	pop.position = (_shoulder() - hurt_direction * 7.0).round()
	pop.scale = Vector2.ONE * 0.60
	pop.rotation = hurt_direction.angle()
	voices["hit"].pitch_scale = 0.72
	voices["hit"].play()
	if player_hp == 0:
		_start_defeat()


func _start_defeat() -> void:
	defeat_elapsed = 0.0
	defeat_mount = rig_at
	defeat_side = -1.0 if defeat_mount.x < player.x else 1.0
	_begin("exit")
	if is_instance_valid(fluid):
		fluid.queue_free()
		fluid = null
	if is_instance_valid(hand_cut):
		hand_cut.queue_free()
		hand_cut = null
	if is_instance_valid(bolt):
		bolt.queue_free()
		bolt = null
	_show_cursor()


func _update_defeat(delta: float) -> void:
	var previous := defeat_elapsed
	defeat_elapsed += delta
	if delta > 0.0 and _hurt_age() - delta < HURT_PUSH_TIME:
		_move(delta)
	var face := "collapse_back_right" if walk_heading.y < 0.0 else "collapse_front_right"
	_set_defeat_cell(hero, face, defeat_elapsed * 1000.0)
	hero.position = player.round()
	hero.scale.x = walk_heading.x
	hero.modulate = Color(1.52, 0.83, 0.88) if defeat_elapsed < 0.045 else Color.WHITE
	hero_upper.hide()
	var enemy_alpha := lerpf(1.0, 0.34, smoothstep(0.12, 0.41, defeat_elapsed))
	for enemy in enemies:
		enemy.modulate.a = enemy_alpha

	if defeat_elapsed < DEFEAT_REVEAL_TIME:
		_update_follow(delta)
		time_ms = maxf(0.0, defeat_elapsed - 0.055) * 1000.0
		_update_pose()
		armor.modulate.a = 1.0 - smoothstep(0.075, 0.205, defeat_elapsed)
		sword.visible = form != 2 and defeat_elapsed < 0.076
		spirit.visible = form != CHAIN_FORM and defeat_elapsed < DEFEAT_MORPH_TIME
	if previous < DEFEAT_MORPH_TIME and defeat_elapsed >= DEFEAT_MORPH_TIME:
		defeat_mount = rig_at
		fluid = _effect(REFORM, Vector2(76, 47), 4, true)
		fluid.position = defeat_mount
	if previous < DEFEAT_DISPERSE_TIME and defeat_elapsed >= DEFEAT_DISPERSE_TIME:
		fluid = _effect(DISPERSE, Vector2(72, 86), 6, true)
		fluid.position = true_requiem.position
	if defeat_elapsed >= DEFEAT_REVEAL_TIME and defeat_elapsed < DEFEAT_VANISH_TIME:
		armor.hide()
		sword.hide()
		chain.hide()
		var elapsed := defeat_elapsed - DEFEAT_REVEAL_TIME
		var approach := smoothstep(0.045, 0.40, elapsed)
		var beside := player + Vector2(defeat_side * 45.0, -34.0)
		var bob := sin(elapsed * 6.0) * 1.4 * approach
		var body_scale := lerpf(0.57, 0.73, approach)
		var untether := smoothstep(DEFEAT_DISPERSE_TIME, DEFEAT_VANISH_TIME, defeat_elapsed)
		var anchor := defeat_mount.lerp(beside, approach) + Vector2(defeat_side * untether * 6.0, bob - untether * 14.0)
		true_requiem.texture = TrueForm.texture_at(elapsed)
		true_requiem.position = anchor.round()
		true_requiem.scale = Vector2(-defeat_side, 1.0) * body_scale
		true_requiem.modulate.a = smoothstep(0.0, 0.10, elapsed) * (1.0 - untether)
		true_requiem.show()
		spirit.hide()
	elif defeat_elapsed >= DEFEAT_VANISH_TIME:
		true_requiem.hide()
	queue_redraw()
	bowstring.queue_redraw()
	hud.queue_redraw()


func _set_defeat_cell(sprite: Sprite2D, id: String, elapsed_ms: float) -> void:
	var motion: Dictionary = defeat_manifest.clips[id]
	_set_sprite_cell(sprite, defeat_textures[id], motion.frames[_frame_at(motion.frames, elapsed_ms)], motion.pivot)


func _update_aim() -> void:
	var to_cursor := cursor - _shoulder()
	if to_cursor.length_squared() > 16.0:
		aim = to_cursor.angle()


func _shoulder() -> Vector2:
	return player - Vector2(0, SHOULDER_HEIGHT)


func _begin(next: String) -> void:
	clip = next
	time_ms = 0.0
	if next != "action":
		counter_attack = false


func _clip_id() -> String:
	return FORMS[form] + "_" + side + "_" + clip


func _length(name: String) -> float:
	return _duration_ms(manifest.clips[name].frames)


func _clip_duration() -> float:
	return reaction_durations["hood_grab_front_right"] if counter_attack else _length(_clip_id())


func _duration_ms(frames: Array) -> float:
	var result := 0.0
	for frame: Dictionary in frames:
		result += float(frame.ms)
	return result


func _release_time() -> float:
	if counter_attack:
		return COUNTER_WINDUP_MS
	var result := 0.0
	for frame: Dictionary in manifest.clips[FORMS[form] + "_" + side + "_action"].frames:
		if frame.get("events", []).has("release"):
			return result
		result += float(frame.ms)
	return result


func _strike_duration() -> float:
	return COUNTER_STRIKE_MS if counter_attack else HAND_STRIKE_MS


func _update_clip(delta: float) -> void:
	time_ms += delta * 1000.0
	var duration := _clip_duration()
	if clip != "idle":
		if time_ms < duration:
			return
		var spill := time_ms - duration
		match clip:
			"exit":
				form = wanted_form
				_begin("enter")
			"action", "enter":
				_begin("idle")
		time_ms = spill
		return
	time_ms = fmod(time_ms, duration)
	if wanted_form != form:
		_begin("exit")
		fluid = _effect(REFORM, Vector2(76, 47), 7, true)
		fluid.position = rig_at
	elif attack_queued and not is_instance_valid(bolt) and not _is_dodging() and _hurt_age() >= HURT_PUSH_TIME:
		attack_queued = false
		locked_aim = aim
		counter_target = null
		counter_peek_ms = -1.0
		counter_attack = form == 0 and counter_window > 0.0
		counter_window = 0.0
		var blade_length := float(manifest.sword_tip[0])
		var maximum_reach := COUNTER_REACH if counter_attack else HAND_REACH
		var inset := 16.0 if counter_attack else 34.0
		var minimum_reach := 28.0 if counter_attack else 14.0
		attack_reach = clampf(_shoulder().distance_to(cursor) - inset, minimum_reach, maximum_reach)
		attack_scale = (attack_reach + blade_length) / (maximum_reach + blade_length)
		if form == CHAIN_FORM:
			attack_reach = clampf(_shoulder().distance_to(cursor) - 70.0, 80.0, 145.0)
		swing *= -1.0
		if counter_attack:
			counter_start = _hand_pose()
			counter_velocity = follow_velocity
			var approach_side := Vector2.from_angle(locked_aim).cross(follow_origin - _shoulder())
			if absf(approach_side) > 8.0:
				swing = signf(approach_side)
		released = false
		hit_in_swing.clear()
		chain_return_hits.clear()
		_begin("action")


func _hand_pose() -> Transform2D:
	var pivot := _shoulder()
	var floating := _floating_mount()
	var rest_reach := minf(HAND_REACH, maxf(0.0, floating.distance_to(cursor) - 7.0))
	var rest_grip := (floating + Vector2.from_angle(follow_bearing) * rest_reach).round()
	var towards_cursor := cursor - rest_grip
	var rest_heading := towards_cursor.angle() if towards_cursor.length_squared() > 0.01 else aim
	if clip != "action":
		return Transform2D(rest_heading, rest_grip)
	if counter_attack:
		return _counter_pose(pivot, Transform2D(rest_heading, rest_grip))

	var windup_ms := _release_time()
	var strike_ms := time_ms - windup_ms
	var start := locked_aim + swing * HAND_SWING_ANGLE
	var finish := locked_aim - swing * HAND_SWING_ANGLE
	var heading: float
	var reach: float
	if strike_ms < 0.0:
		var windup := smoothstep(0.0, windup_ms, time_ms)
		heading = lerp_angle(locked_aim, start, windup)
		pivot = floating.lerp(pivot, windup)
		reach = lerpf(rest_reach, attack_reach - 9.0 * attack_scale, windup)
	elif strike_ms <= HAND_STRIKE_MS:
		var travel := smoothstep(0.0, HAND_STRIKE_MS, strike_ms)
		heading = lerp_angle(start, finish, travel)
		reach = attack_reach + (-9.0 * (1.0 - travel) + 12.0 * sin(PI * travel)) * attack_scale
	else:
		var recover := smoothstep(HAND_STRIKE_MS, 215.0, strike_ms)
		heading = lerp_angle(finish, aim, recover)
		pivot = pivot.lerp(floating, recover)
		reach = lerpf(attack_reach, rest_reach, recover)
	return Transform2D(heading, (pivot + Vector2.from_angle(heading) * reach).round())


func _counter_pose(pivot: Vector2, rest: Transform2D) -> Transform2D:
	var start := locked_aim + swing * COUNTER_SWING_ANGLE
	var finish := locked_aim - swing * COUNTER_SWING_ANGLE
	var strike_ms := time_ms - COUNTER_WINDUP_MS
	var start_reach := attack_reach - 9.0 * attack_scale
	if strike_ms < 0.0:
		var t := time_ms / COUNTER_WINDUP_MS
		var held := counter_start.origin
		var carry := counter_velocity.limit_length(300.0) * COUNTER_WINDUP_MS / 3000.0
		var ready := pivot + Vector2.from_angle(start) * start_reach
		var grip := held.bezier_interpolate(held + carry, ready, ready, t)
		return Transform2D(lerp_angle(counter_start.get_rotation(), start, smoothstep(0.0, 1.0, t)), grip.round())
	if strike_ms <= COUNTER_STRIKE_MS:
		var travel := smoothstep(0.0, COUNTER_STRIKE_MS, strike_ms)
		# The counter sweeps over half a circle, so keep the signed direction.
		var heading := lerpf(start, finish, travel)
		var reach := attack_reach + (-9.0 * (1.0 - travel) + 22.0 * sin(PI * travel)) * attack_scale
		return Transform2D(heading, (pivot + Vector2.from_angle(heading) * reach).round())
	var recover := smoothstep(COUNTER_STRIKE_MS, _clip_duration() - COUNTER_WINDUP_MS - 22.0, strike_ms)
	var end_grip := pivot + Vector2.from_angle(finish) * attack_reach
	return Transform2D(lerp_angle(finish, rest.get_rotation(), recover), end_grip.lerp(rest.origin, recover).round())


func _update_pose() -> void:
	var hand_form := form == 0
	var chain_form := form == CHAIN_FORM
	var grip := Vector2.ZERO
	blade_heading = locked_aim if clip == "action" else aim
	if hand_form:
		var hand_pose := _hand_pose()
		grip = hand_pose.origin
		blade_heading = hand_pose.get_rotation()
	var flinch_phase := clampf(_hurt_age() / REQUIEM_FLINCH_TIME, 0.0, 1.0)
	var flinch := sin(PI * flinch_phase) * (1.0 - flinch_phase) if clip != "action" else 0.0
	blade_heading += flinch * 0.53 * walk_heading.x
	var tool_heading := blade_heading + (HAND_GRIP_TURN if hand_form else 0.0)
	var facing := Vector2.from_angle(tool_heading)
	if absf(facing.y) > 0.09:
		side = "front_right" if facing.y > 0.0 else "back_right"
	var key: String = FORMS[form] + "_" + side
	var id := key + "_" + clip
	var frames: Array = manifest.clips[id].frames
	var pose_time := time_ms
	if counter_attack:
		pose_time *= _length(id) / _clip_duration()
	var step := _frame_at(frames, pose_time)
	pose_points = manifest.forms[key].tracks[id][step]
	var mirror := -1.0 if facing.x < 0.0 else 1.0
	var local := atan2(facing.y, absf(facing.x))
	var angle := mirror * (local - deg_to_rad(float(manifest.forms[key].axis_deg)))
	var follow := locked_aim if clip == "action" else follow_bearing
	rig_basis = Transform2D(angle, Vector2(mirror, 1.0), 0.0, Vector2.ZERO)
	var mount_reach := 51.0 if chain_form else 69.0
	var neutral_at := (_floating_mount() + Vector2.from_angle(follow) * mount_reach).round()
	rig_at = neutral_at
	if hand_form:
		var grip_at := grip - rig_basis.basis_xform(_point_local("socket"))
		match clip:
			"exit":
				rig_at = grip_at.lerp(neutral_at, smoothstep(0.0, _length(id), time_ms))
			"enter":
				rig_at = neutral_at.lerp(grip_at, smoothstep(0.0, _length(id), time_ms))
			_:
				rig_at = grip_at
	rig_basis.origin = rig_at
	_set_sprite(armor, id, step)
	armor.transform = rig_basis
	mounted_position = _world_point("socket")
	if chain_form:
		var cast_time := time_ms if clip == "action" else -1.0
		var flight := chain.pose(mounted_position, tool_heading, cast_time,
			attack_reach, float(pose_points.presence), idle_clock)
		mounted_position = flight.origin
		blade_heading = flight.get_rotation()
	else:
		chain.hide()
	sword.position = mounted_position.round()
	sword.rotation = blade_heading
	sword.z_index = 5 if form == 0 else 7
	var stretch := [0.88, 0.54, 0.68, 0.0][form] as float
	stretch *= 1.0 - 0.36 * flinch
	if form == 0 and clip == "action":
		stretch += 0.60 * sin(PI * clampf(time_ms / 305.0, 0.0, 1.0))
		if counter_attack and time_ms < COUNTER_WINDUP_MS + 70.0:
			stretch += 0.72 * sin(PI * time_ms / (COUNTER_WINDUP_MS + 70.0))
	spirit.position = _world_point("tail").round()
	spirit.rotation = angle
	spirit.scale = Vector2(stretch * mirror, stretch)
	spirit.visible = not chain_form and (clip == "idle" or clip == "action")
	if is_instance_valid(fluid):
		fluid.position = rig_at


func _point_local(name: String) -> Vector2:
	var point: Array = pose_points[name]
	return Vector2(point[0], point[1])


func _world_point(name: String) -> Vector2:
	return rig_basis * _point_local(name)


func _release() -> void:
	voices[FORMS[form]].pitch_scale = 0.83 if counter_attack else 1.0
	voices[FORMS[form]].play()
	if form == CHAIN_FORM:
		previous_grip = mounted_position
		previous_tip = _current_tip()
		return
	if form == 0:
		var frames := COUNTER_CUT if counter_attack else HAND_CUT
		var pivot := Vector2(56, 196) if counter_attack else Vector2(4, 150)
		hand_cut = _effect(frames, pivot, 3)
		hand_cut.rotation = locked_aim
		hand_cut.scale = Vector2(attack_scale, -swing * attack_scale)
		hand_cut.pause()
		previous_grip = mounted_position
		previous_tip = _current_tip()
		return

	var effect := _effect(BOW_FLASH if form == 1 else CANNON_FLASH, Vector2(42, 50), 8)
	var launch_direction := Vector2.from_angle(locked_aim)
	var muzzle := mounted_position
	if form == 1:
		muzzle = rig_at + launch_direction * 11.0
	effect.position = muzzle.round()
	effect.rotation = locked_aim
	bolt = _new_sword()
	bolt.z_index = 8
	bolt.position = mounted_position
	bolt.rotation = locked_aim
	bolt_velocity = launch_direction * (595.0 if form == 1 else 760.0)
	cannon_bolt = form == 2
	if cannon_bolt:
		bolt_muzzle = muzzle
		bolt.position -= launch_direction * float(manifest.sword_tip[0])
		_clip_cannon_bolt(launch_direction)


func _update_hand_cut() -> void:
	if not is_instance_valid(hand_cut):
		return
	var elapsed := time_ms - _release_time()
	var frames := hand_cut.sprite_frames
	var frame_ms := 1000.0 * frames.get_frame_duration(&"fx", 0) / frames.get_animation_speed(&"fx")
	var frame := roundi(elapsed / frame_ms)
	if clip != "action" or form != 0 or frame >= frames.get_frame_count(&"fx") - 1:
		hand_cut.queue_free()
		hand_cut = null
		return
	hand_cut.set_frame_and_progress(frame, 0.0)
	if elapsed <= _strike_duration():
		hand_cut.position = _shoulder().round()


func _current_tip() -> Vector2:
	return mounted_position + Vector2.from_angle(blade_heading) * float(manifest.sword_tip[0])


func _check_sweep() -> void:
	var tip := _current_tip()
	var swept_blade := PackedVector2Array([previous_grip, previous_tip, tip, mounted_position])
	for index in enemies.size():
		var enemy := enemies[index]
		if enemy.hp <= 0 or index in hit_in_swing:
			continue
		var target := enemy.hit_center()
		var from_tip := Geometry2D.get_closest_point_to_segment(target, previous_tip, tip)
		var from_blade := Geometry2D.get_closest_point_to_segment(target, mounted_position, tip)
		if minf(target.distance_to(from_tip), target.distance_to(from_blade)) < 15.0 \
				or Geometry2D.is_point_in_polygon(target, swept_blade):
			hit_in_swing.append(index)
			_impact(enemy, target, blade_heading)
	previous_grip = mounted_position
	previous_tip = tip


func _check_chain_strike() -> void:
	var leg := chain.hit_leg(time_ms)
	var tip := _current_tip()
	if leg != 0:
		var hits := hit_in_swing if leg > 0 else chain_return_hits
		for index in enemies.size():
			var enemy := enemies[index]
			if enemy.hp <= 0 or index in hits:
				continue
			var target := enemy.hit_center()
			if Chain.blade_crossed(target, previous_grip, previous_tip, mounted_position, tip):
				hits.append(index)
				_impact(enemy, target, blade_heading, leg < 0)
	previous_grip = mounted_position
	previous_tip = tip


func _fly(delta: float) -> void:
	if not is_instance_valid(bolt):
		return
	var next := bolt.position + bolt_velocity * delta
	var direction := bolt_velocity.normalized()
	var tip_offset := direction * float(manifest.sword_tip[0])
	var exposed_start := bolt.position
	if cannon_bolt:
		exposed_start += direction * maxf(0.0, (bolt_muzzle - exposed_start).dot(direction))
	var first: Pursuer
	var contact := Vector2.ZERO
	var closest := INF
	for enemy in enemies:
		if enemy.hp <= 0:
			continue
		var target := enemy.hit_center()
		var hit := Geometry2D.get_closest_point_to_segment(target, exposed_start, next + tip_offset)
		var distance := exposed_start.distance_squared_to(hit)
		if hit.distance_to(target) < 13.0 and distance < closest:
			first = enemy
			contact = hit
			closest = distance
	if first != null:
		_impact(first, contact, bolt.rotation)
		bolt.queue_free()
		bolt = null
		return
	bolt.position = next
	if cannon_bolt:
		_clip_cannon_bolt(direction)
	if not FIELD.grow(28.0).has_point(next):
		bolt.queue_free()
		bolt = null


func _clip_cannon_bolt(direction: Vector2) -> void:
	var pivot := Vector2(manifest.clips.sword.pivot[0], manifest.clips.sword.pivot[1])
	var size_px := bolt.texture.get_size()
	var inside := (bolt_muzzle - bolt.position).dot(direction)
	var start_x := clampi(ceili(pivot.x + inside), 0, int(size_px.x))
	bolt.visible = start_x < int(size_px.x)
	if not bolt.visible:
		return
	var glow := bolt.get_child(0) as Sprite2D
	var region := Rect2(start_x, 0, size_px.x - start_x, size_px.y)
	var offset := Vector2(start_x, 0) - pivot
	bolt.region_rect = region
	bolt.offset = offset
	glow.region_enabled = true
	glow.region_rect = region
	glow.offset = offset


func _impact(enemy: Pursuer, contact: Vector2, angle: float, pull := false) -> void:
	var push_direction := _shoulder().direction_to(enemy.hit_center())
	if push_direction.is_zero_approx():
		push_direction = Vector2.from_angle(angle)
	if pull:
		push_direction = -push_direction
	var force: float = [266.0, 166.0, 320.0, 118.0][form]
	if counter_attack:
		force = 346.0
		var angle_to_hit := _shoulder().angle_to_point(contact)
		if not is_instance_valid(counter_target) or absf(angle_difference(locked_aim, angle_to_hit)) < +				absf(angle_difference(locked_aim, _shoulder().angle_to_point(counter_target.hit_center()))):
			counter_target = enemy
	enemy.receive_strike(push_direction, force)
	impact_ticks = maxi(impact_ticks, 4 if counter_attack else [3, 2, 4, 2][form])
	var pop := _effect(HIT, Vector2(52, 53), 9)
	pop.position = contact.round()
	pop.rotation = angle
	voices["hit"].pitch_scale = 0.88 if counter_attack else [1.0, 1.14, 0.83, 1.08][form]
	voices["hit"].play()


func _draw_bowstring() -> void:
	if form != 1 or not (clip == "idle" or clip == "action"):
		return
	var joint := mounted_position.round()
	bowstring.draw_line(_world_point("upper").round(), joint, GHOST)
	bowstring.draw_line(joint, _world_point("lower").round(), GHOST)


func _draw() -> void:
	draw_rect(Rect2(player.round() - Vector2(12, 2), Vector2(24, 4)), Color("#21182b"))
	if is_instance_valid(true_requiem) and true_requiem.visible:
		var shadow := Color("#2a2036")
		shadow.a = true_requiem.modulate.a
		draw_rect(Rect2(true_requiem.position + Vector2(-19, 31), Vector2(38, 4)), shadow)
	elif armor != null and armor.visible:
		draw_rect(Rect2(rig_at + Vector2(-28, 24), Vector2(56, 4)), Color("#2a2036"))


func _draw_hud() -> void:
	hud.draw_rect(Rect2(0, 0, 640, 44), INK)
	hud.draw_rect(Rect2(0, 323, 640, 37), INK)
	hud.draw_line(Vector2(18, 43), Vector2(622, 43), Color("#896174"))
	hud.draw_line(Vector2(18, 323), Vector2(622, 323), Color("#896174"))
	hud.draw_string(title, Vector2(19, 28), "Requiem Waltz", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, LIGHT)
	_text(Vector2(191, 27), "봉인의 방", 13, GOLD)
	var alive := 0
	for enemy in enemies:
		alive += int(enemy.hp > 0)
	var status := "체력 %d/3    적 %d" % [player_hp, alive]
	if player_hp == 0:
		status = "쓰러짐    R 재시작"
	elif alive == 0:
		status = "방 돌파    R 다시 싸우기"
	_text(Vector2(484, 27), status, 12, GHOST if player_hp > 0 else Color("#f58b8b"))
	for i in LABELS.size():
		var bounds := Rect2(19 + i * 68, 328, 62, 26)
		hud.draw_rect(bounds, Color("#603a66") if i == form else Color("#322439"))
		hud.draw_rect(bounds, Color("#bc87b3") if i == form else Color("#664758"), false)
		_text(bounds.position + Vector2(8, 17), "%d  %s" % [i + 1, LABELS[i]], 12, LIGHT)
	_text(Vector2(297, 344), "WASD 이동   Space 회피   좌클릭 공격   R 초기화", 12, LIGHT)
	if pointer:
		for arm in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
			hud.draw_line(cursor + arm * 5.0, cursor + arm * 9.0, GOLD)


func _text(at: Vector2, value: String, size: int, color: Color) -> void:
	hud.draw_string(font, at, value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
