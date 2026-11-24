extends Node2D

const FRAMES := preload("res://assets/actors/crypt_skeleton/crypt_skeleton_frames.tres")
const WALK_SPEED := 65.0
const WINDUP_TIME := 0.36
const RECOVERY_TIME := 0.52
const STAGGER_TIME := 0.29
const FALL_TIME := 0.72
const FALL_FADE_START := 0.5
const STRIKE_RADIUS := 19.0
const BRAKE := 1320.0

enum Phase { CHASE, WINDUP, RECOVER, STAGGER, FALL }

var hp := 2
var phase := Phase.CHASE
var facing := 1.0
var strike_at := Vector2.ZERO
var cooldown := 0.0
var elapsed := 0.0
var push := Vector2.ZERO
var back_view := false
var moving := false
var paint := Sprite2D.new()


func _ready() -> void:
	z_index = 4
	# The 64 × 64 cell has its ground pivot at (32, 58).
	paint.offset = Vector2(0, -26)
	add_child(paint)
	_update_sprite()


func configure(at: Vector2, delay: float) -> void:
	position = at
	cooldown = delay


func hit_center() -> Vector2:
	return position - Vector2(0, 20)


func receive_strike(direction: Vector2, force: float) -> void:
	hp -= 1
	push = direction * force
	_face(-direction)
	_set_phase(Phase.STAGGER if hp > 0 else Phase.FALL)
	_update_sprite()
	queue_redraw()


func advance(delta: float, target: Vector2, separation: Vector2, bounds: Rect2) -> bool:
	if not visible:
		return false
	elapsed += delta
	cooldown = maxf(0.0, cooldown - delta)
	var struck := false
	var before := position
	match phase:
		Phase.CHASE:
			var approach := target - position
			_face(approach)
			if approach.length_squared() < 28.0 * 28.0 and cooldown == 0.0:
				strike_at = target
				_set_phase(Phase.WINDUP)
			elif approach.length_squared() > 23.0 * 23.0:
				position += (approach.normalized() + separation * 0.8).normalized() * WALK_SPEED * delta
		Phase.WINDUP:
			if elapsed >= WINDUP_TIME:
				position += position.direction_to(strike_at) * 7.0
				struck = target.distance_squared_to(strike_at) < STRIKE_RADIUS * STRIKE_RADIUS
				# Recovery opens on the strike's contact cel.
				_set_phase(Phase.RECOVER)
		Phase.RECOVER:
			if elapsed >= RECOVERY_TIME:
				_set_phase(Phase.CHASE)
		Phase.STAGGER, Phase.FALL:
			push = push.move_toward(Vector2.ZERO, BRAKE * delta)
			position += push * delta
			if phase == Phase.STAGGER and elapsed >= STAGGER_TIME:
				cooldown = 0.20
				_set_phase(Phase.CHASE)
			elif phase == Phase.FALL and elapsed >= FALL_TIME:
				hide()
	position = position.clamp(bounds.position, bounds.end)
	var walking := phase == Phase.CHASE and not position.is_equal_approx(before)
	if walking != moving:
		moving = walking
		if phase == Phase.CHASE:
			elapsed = 0.0
	_update_sprite()
	queue_redraw()
	return struck


func _face(direction: Vector2) -> void:
	var distance := direction.length()
	if absf(direction.x) > 0.15 * distance:
		facing = signf(direction.x)
	if absf(direction.y) > 0.18 * distance:
		back_view = direction.y < 0.0


func _set_phase(next: Phase) -> void:
	phase = next
	elapsed = 0.0


func _update_sprite() -> void:
	var clip: String = ["walk" if moving else "idle", "windup", "recover", "hit", "collapse"][phase]
	var animation := StringName(clip + ("_back_right" if back_view else "_front_right"))
	var frame_count := FRAMES.get_frame_count(animation)
	var cursor := elapsed * FRAMES.get_animation_speed(animation)
	if FRAMES.get_animation_loop(animation):
		var duration := 0.0
		for index in frame_count:
			duration += FRAMES.get_frame_duration(animation, index)
		cursor = fmod(cursor, duration)
	var frame := 0
	while frame < frame_count - 1 and cursor >= FRAMES.get_frame_duration(animation, frame):
		cursor -= FRAMES.get_frame_duration(animation, frame)
		frame += 1
	paint.texture = FRAMES.get_frame_texture(animation, frame)
	paint.flip_h = facing < 0.0
	paint.modulate = Color.WHITE
	if phase == Phase.WINDUP:
		paint.modulate = Color(1.25, 0.83, 0.81)
	elif phase == Phase.STAGGER or phase == Phase.FALL:
		if elapsed < 0.065:
			paint.modulate = Color(2.1, 1.8, 1.7)
		elif phase == Phase.FALL:
			paint.modulate.a = 1.0 - smoothstep(FALL_FADE_START, FALL_TIME, elapsed)


func _draw() -> void:
	draw_rect(Rect2(-10, -2, 20, 4), Color("#21182b"))
	if phase == Phase.WINDUP:
		var tint := Color("#f58b8b")
		tint.a = lerpf(0.4, 0.92, elapsed / WINDUP_TIME)
		draw_arc((strike_at - position).round(), STRIKE_RADIUS, 0, TAU, 24, tint, 1.5)
	for index in hp:
		draw_rect(Rect2(-5 + index * 6, -49, 4, 2), Color("#e3ae83"))
