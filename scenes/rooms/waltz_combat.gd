extends Node2D

enum Phase { SEALED, PACT, FIGHT, REWARD, CLEAR, DOWN }
enum Form { BLADE, BOW, CANNON }

const PLAY_MIN := Vector2(74, 123)
const PLAY_MAX := Vector2(566, 302)
const AIM_AREA := Rect2(0, 43, 640, 280)
const SEAL := Vector2(320, 154)
const START := Vector2(253, 216)
const MAX_HEARTS := 4
const WINDUP := [5, 8, 13]
const RECOVERY := [23, 19, 43]
const SWEEP_TICKS := 6
const SWEEP_FROM := -1.45
const SWEEP_TO := 1.37
const GRIP_DISTANCE := 28.0
const SWORD_TIP := 90.0
const SOUND_STREAMS := {
	&"seal": preload("res://assets/audio/waltz_unseal.wav"),
	&"swing": preload("res://assets/audio/combat_study_swing.wav"),
	&"bow": preload("res://assets/audio/waltz_bow.wav"),
	&"cannon": preload("res://assets/audio/waltz_cannon.wav"),
	&"hit": preload("res://assets/audio/combat_study_impact.wav"),
}

class Guard:
	var position: Vector2
	var push := Vector2.ZERO
	var hp: int
	var total_hp: int
	var born := 20
	var windup := 0
	var pause := 0
	var flash := 0
	var swing := 0
	var gait := 0.0
	var face_left := false
	var threat := Vector2.ZERO

	func _init(at: Vector2, health: int) -> void:
		position = at
		hp = health
		total_hp = health


class Bolt:
	var position: Vector2
	var velocity: Vector2
	var is_shell: bool
	var age := 0

	func _init(at: Vector2, direction: Vector2, shell: bool) -> void:
		position = at
		is_shell = shell
		velocity = direction * (310.0 if shell else 600.0)


class Burst:
	var kind: StringName
	var position: Vector2
	var angle: float
	var tick := 0

	func _init(cue: StringName, at: Vector2, direction: float) -> void:
		kind = cue
		position = at
		angle = direction


var phase := Phase.SEALED
var form := Form.BLADE
var player := START
var velocity := Vector2.ZERO
var gait := 0.0
var face_row := 0
var face_left := false
var hearts := MAX_HEARTS
var i_frames := 0
var wave := 0
var dialogue := 0
var cursor := Vector2(395, 195)
var pointer := false
var aim := 0.0
var locked_aim := 0.0
var attack := -1
var queued := 0
var next_form := -1
var sweep_side := -1.0
var sweep_origin := Vector2.ZERO
var hitstop := 0
var shake := 0
var ticks := 0
var form_flash := 0
var extra_damage := 0
var haste := false
var guards: Array[Guard] = []
var struck: Array[Guard] = []
var bolts: Array[Bolt] = []
var bursts: Array[Burst] = []
var voices: Dictionary[StringName, AudioStreamPlayer] = {}


func _ready() -> void:
	for cue: StringName in SOUND_STREAMS:
		var voice := AudioStreamPlayer.new()
		voice.stream = SOUND_STREAMS[cue]
		voice.bus = &"SFX"
		voice.volume_db = -4.0 if cue == &"hit" else -2.0
		voice.max_polyphony = 3
		add_child(voice)
		voices[cue] = voice
	get_window().mouse_exited.connect(_release_pointer)
	get_window().focus_exited.connect(_release_pointer)
	_reset()


func _reset() -> void:
	phase = Phase.SEALED
	form = Form.BLADE
	player = START
	velocity = Vector2.ZERO
	gait = 0.0
	face_row = 0
	face_left = false
	hearts = MAX_HEARTS
	i_frames = 0
	wave = 0
	dialogue = 0
	cursor = Vector2(395, 195)
	aim = 0.0
	attack = -1
	queued = 0
	next_form = -1
	sweep_side = -1.0
	hitstop = 0
	shake = 0
	ticks = 0
	form_flash = 0
	extra_damage = 0
	haste = false
	guards.clear()
	struck.clear()
	bolts.clear()
	bursts.clear()
	for voice in voices.values():
		voice.stop()
	_release_pointer()


func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_point(event.position)
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_point(event.position)
		if phase == Phase.FIGHT and pointer:
			queued = 12
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_R:
				_reset()
			KEY_E, KEY_ENTER:
				_interact()
			KEY_1, KEY_2, KEY_3:
				_choose(event.physical_keycode - KEY_1)


func _point(at: Vector2) -> void:
	cursor = at
	pointer = phase == Phase.FIGHT and AIM_AREA.has_point(at)
	Input.mouse_mode = Input.MOUSE_MODE_HIDDEN if pointer else Input.MOUSE_MODE_VISIBLE


func _release_pointer() -> void:
	pointer = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _interact() -> void:
	if phase == Phase.SEALED and player.distance_to(SEAL) < 101.0:
		phase = Phase.PACT
		velocity = Vector2.ZERO
		bursts.append(Burst.new(&"seal", SEAL, 0.0))
		voices[&"seal"].play()
	elif phase == Phase.PACT:
		dialogue += 1
		if dialogue == 2:
			_start_wave(1)


func _choose(index: int) -> void:
	if phase == Phase.REWARD and index <= 1:
		extra_damage = 1 if index == 0 else 0
		haste = index == 1
		_start_wave(2)
	elif phase == Phase.FIGHT:
		next_form = index


func _start_wave(number: int) -> void:
	wave = number
	phase = Phase.FIGHT
	queued = 0
	next_form = -1
	attack = -1
	hitstop = 0
	shake = 0
	struck.clear()
	bolts.clear()
	guards.clear()
	var locations := [Vector2(368, 208), Vector2(494, 162), Vector2(462, 268), Vector2(157, 269)]
	if wave == 2:
		locations = [Vector2(136, 151), Vector2(498, 148), Vector2(502, 270), Vector2(114, 271), Vector2(323, 137)]
	for at in locations:
		var spawn: Vector2 = at
		if player.distance_to(spawn) < 55.0:
			spawn.x = PLAY_MAX.x - 20.0 if player.x < 320.0 else PLAY_MIN.x + 20.0
		guards.append(Guard.new(spawn, 2 if wave == 1 else 3))
	_point(cursor)


func _physics_process(delta: float) -> void:
	ticks += 1
	shake = maxi(0, shake - 1)
	if hitstop > 0:
		hitstop -= 1
		$Art.queue_redraw()
		return
	for i in range(bursts.size() - 1, -1, -1):
		bursts[i].tick += 1
		if bursts[i].tick >= 34:
			bursts.remove_at(i)
	if phase == Phase.SEALED or phase == Phase.FIGHT:
		_move(delta)
	if phase == Phase.FIGHT:
		i_frames = maxi(0, i_frames - 1)
		form_flash = maxi(0, form_flash - 1)
		if origin().distance_squared_to(cursor) > 4.0:
			aim = origin().angle_to_point(cursor)
		_update_attack()
		_update_bolts(delta)
		_update_guards(delta)
		_check_wave()
	$Art.queue_redraw()


func _move(delta: float) -> void:
	var x := float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A))
	var y := float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W))
	var movement := Vector2(x, y).normalized()
	velocity = velocity.move_toward(movement * 122.0, delta * 1180.0)
	player = (player + velocity * delta).clamp(PLAY_MIN, PLAY_MAX)
	if velocity.length() > 12.0:
		gait = fmod(gait + delta * 9.8, 4.0)
	if movement != Vector2.ZERO:
		face_row = 2 if absf(x) > absf(y) else (1 if y < 0.0 else 0)
		face_left = x < 0.0


func origin() -> Vector2:
	return player + Vector2(0, -17)


func release_tick() -> int:
	return attack - int(WINDUP[form])


func _arc(tick: int) -> float:
	return lerpf(SWEEP_FROM, SWEEP_TO, float(tick) / SWEEP_TICKS)


func weapon_angle() -> float:
	if attack < 0:
		return aim
	if form != Form.BLADE:
		return locked_aim if release_tick() < 4 else lerp_angle(locked_aim, aim, clampf((release_tick() - 4.0) / 8.0, 0.0, 1.0))
	var t := release_tick()
	if t < 0:
		return locked_aim + sweep_side * SWEEP_FROM * float(attack + 1) / float(WINDUP[form] + 1)
	if t <= SWEEP_TICKS:
		return locked_aim + sweep_side * _arc(t)
	return lerp_angle(locked_aim + sweep_side * SWEEP_TO, aim, clampf((t - SWEEP_TICKS) / 10.0, 0.0, 1.0))


func _update_attack() -> void:
	if attack < 0:
		if next_form >= 0 and next_form != form:
			form = next_form as Form
			form_flash = 13
		next_form = -1
		if queued > 0:
			queued = 0
			attack = 0
			locked_aim = aim
			sweep_side *= -1.0
			struck.clear()
		return
	queued = maxi(0, queued - 1)
	attack += 1
	if attack >= int(RECOVERY[form]) - (5 if haste else 0):
		attack = -1
		return
	var t := release_tick()
	if t == 0:
		match form:
			Form.BLADE:
				voices[&"swing"].pitch_scale = 1.08 if sweep_side > 0.0 else 0.96
				voices[&"swing"].play()
			Form.BOW, Form.CANNON:
				var direction := Vector2.from_angle(locked_aim)
				var shell := form == Form.CANNON
				var muzzle := origin() + direction * (GRIP_DISTANCE + (47.0 if shell else 23.0))
				# Resolve the space between caster and muzzle, including enemies at point-blank range.
				var shot := Bolt.new(muzzle, direction, shell)
				var blocked := _strike_bolt(shot, origin() + direction * 10.0, muzzle)
				if not blocked:
					bolts.append(shot)
				voices[&"cannon" if shell else &"bow"].play()
				if shell:
					shake = maxi(shake, 6)
	if form == Form.BLADE and t >= 0 and t <= SWEEP_TICKS:
		sweep_origin = origin()
		if t > 0:
			_sweep(_arc(t - 1), _arc(t))


func _sweep(low: float, high: float) -> void:
	var connected := false
	for guard in guards:
		if not _hittable(guard) or guard in struck:
			continue
		var offset := _guard_center(guard) - sweep_origin
		var distance := offset.length()
		if distance > SWORD_TIP + 10.0:
			continue
		var angle := wrapf(offset.angle() - locked_aim, -PI, PI) * sweep_side
		var pad := asin(minf(1.0, 11.0 / maxf(1.0, distance)))
		if distance > 11.0 and (angle < low - pad or angle > high + pad):
			continue
		struck.append(guard)
		var direction := offset.normalized() if distance > 1.0 else Vector2.from_angle(locked_aim)
		_damage_guard(guard, 2, direction, 191.0)
		connected = true
	if connected:
		_contact(4, 10, 1.0)


func _update_bolts(delta: float) -> void:
	for i in range(bolts.size() - 1, -1, -1):
		var shot := bolts[i]
		shot.age += 1
		var next := shot.position + shot.velocity * delta
		if _strike_bolt(shot, shot.position, next):
			bolts.remove_at(i)
			continue
		shot.position = next
		if shot.age >= (32 if shot.is_shell else 47) or not AIM_AREA.has_point(next):
			if shot.is_shell:
				_detonate(next, shot.velocity.normalized())
			bolts.remove_at(i)


func _strike_bolt(shot: Bolt, start: Vector2, end: Vector2) -> bool:
	var first: Guard
	var point := end
	var closest := INF
	for guard in guards:
		if not _hittable(guard):
			continue
		var center := _guard_center(guard)
		var contact := Geometry2D.get_closest_point_to_segment(center, start, end)
		if contact.distance_squared_to(center) > (272.0 if shot.is_shell else 169.0):
			continue
		var length := start.distance_squared_to(contact)
		if length < closest:
			closest = length
			first = guard
			point = contact
	if first == null:
		return false
	var direction := shot.velocity.normalized()
	if shot.is_shell:
		_detonate(point, direction)
	else:
		_damage_guard(first, 1, direction, 110.0)
		_contact(2, 5, 1.20)
	return true


func _detonate(at: Vector2, direction: Vector2) -> void:
	bursts.append(Burst.new(&"cannon", at, 0.0))
	var connected := false
	for guard in guards:
		var offset := _guard_center(guard) - at
		if _hittable(guard) and offset.length_squared() <= 49.0 * 49.0:
			var away := offset.normalized() if offset.length_squared() > 16.0 else direction
			_damage_guard(guard, 2, away, 238.0)
			connected = true
	if connected:
		_contact(5, 12, 0.82)


func _guard_center(guard: Guard) -> Vector2:
	return guard.position + Vector2(0, -15)


func _hittable(guard: Guard) -> bool:
	return guard.hp > 0 and guard.born <= 5


func _damage_guard(guard: Guard, power: int, direction: Vector2, push_speed: float) -> void:
	guard.hp = maxi(0, guard.hp - power - extra_damage)
	guard.push = direction * push_speed
	guard.windup = 0
	guard.pause = 16
	guard.flash = 7
	var at := _guard_center(guard) - direction * 7.0
	bursts.append(Burst.new(&"hit", at, direction.angle()))
	if guard.hp == 0:
		bursts.append(Burst.new(&"seal", guard.position, 0.0))


func _contact(stop_ticks: int, shake_ticks: int, pitch: float) -> void:
	hitstop = maxi(hitstop, stop_ticks)
	shake = maxi(shake, shake_ticks)
	voices[&"hit"].pitch_scale = pitch
	voices[&"hit"].play()


func _update_guards(delta: float) -> void:
	for guard in guards:
		if guard.hp <= 0:
			guard.flash = maxi(0, guard.flash - 1)
			continue
		guard.flash = maxi(0, guard.flash - 1)
		guard.swing = maxi(0, guard.swing - 1)
		if guard.born > 0:
			guard.born -= 1
			continue
		if guard.pause > 0:
			guard.pause -= 1
			guard.position = (guard.position + guard.push * delta).clamp(PLAY_MIN, PLAY_MAX)
			guard.push = guard.push.move_toward(Vector2.ZERO, delta * 930.0)
			continue
		if guard.windup > 0:
			guard.windup -= 1
			if guard.windup == 0:
				guard.pause = 32
				guard.swing = 10
				guard.position = (guard.position + guard.position.direction_to(guard.threat) * 9.0).clamp(PLAY_MIN, PLAY_MAX)
				if i_frames == 0 and player.distance_to(guard.threat) < 22.0:
					hearts -= 1
					i_frames = 55
					_contact(3, 8, 0.75)
			continue
		var to_player := player - guard.position
		if absf(to_player.x) > 3.0:
			guard.face_left = to_player.x < 0.0
		if to_player.length_squared() < 34.0 * 34.0:
			guard.threat = player
			guard.windup = 27 if wave == 1 else 22
			continue
		var steer := to_player.normalized()
		for neighbor in guards:
			var apart := guard.position - neighbor.position
			if neighbor != guard and neighbor.hp > 0 and apart.length_squared() < 24.0 * 24.0:
				steer += apart.normalized() * 0.66
		guard.position = (guard.position + steer.normalized() * delta * (43.0 if wave == 1 else 55.0)).clamp(PLAY_MIN, PLAY_MAX)
		guard.gait += delta * 12.0


func _check_wave() -> void:
	if hearts <= 0:
		phase = Phase.DOWN
	else:
		for guard in guards:
			if guard.hp > 0 or guard.flash > 0:
				return
		phase = Phase.REWARD if wave == 1 else Phase.CLEAR
	attack = -1
	velocity = Vector2.ZERO
	_release_pointer()
