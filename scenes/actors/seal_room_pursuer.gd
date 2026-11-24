extends Node2D

const Motion := preload("res://scenes/actors/ryne_motion.gd")
const PAINT_SCALE := 0.79
const WALK_SPEED := 65.0
const WINDUP_TIME := 0.36
const RECOVERY_TIME := 0.52
const STRIKE_RADIUS := 19.0
const BRAKE := 1320.0

enum Phase { CHASE, WINDUP, RECOVER, STAGGER, FALL }

var hp := 2
var phase := Phase.CHASE
var elapsed := 0.0
var stride := 0.0
var facing := 1.0
var cooldown := 0.0
var strike_at := Vector2.ZERO
var push := Vector2.ZERO
var paint: Sprite2D
var idle_motion: Motion
var hit_motion: Motion
var fall_motion: Motion


func configure(at: Vector2, delay: float, idle: Motion, hit: Motion, fall: Motion) -> void:
	position = at
	cooldown = delay
	idle_motion = idle
	hit_motion = hit
	fall_motion = fall
	z_index = 4
	paint = Sprite2D.new()
	paint.centered = false
	paint.region_enabled = true
	add_child(paint)
	_draw_pose()


func hit_center() -> Vector2:
	return position - Vector2(0, 20)


func receive_strike(direction: Vector2, force: float) -> void:
	hp -= 1
	push = direction * force
	if absf(direction.x) > 0.15:
		facing = -signf(direction.x)
	_set_phase(Phase.STAGGER if hp > 0 else Phase.FALL)
	_draw_pose()
	queue_redraw()


func advance(delta: float, target: Vector2, separation: Vector2, bounds: Rect2) -> bool:
	if not visible:
		return false
	elapsed += delta
	stride += delta
	cooldown = maxf(0.0, cooldown - delta)
	var struck := false
	match phase:
		Phase.CHASE:
			var approach := target - position
			if absf(approach.x) > 3.0:
				facing = signf(approach.x)
			if approach.length_squared() < 28.0 * 28.0 and cooldown == 0.0:
				strike_at = target
				_set_phase(Phase.WINDUP)
			elif approach.length_squared() > 23.0 * 23.0:
				var course := (approach.normalized() + separation * 0.8).normalized()
				position += course * WALK_SPEED * delta
		Phase.WINDUP:
			if elapsed >= WINDUP_TIME:
				position += position.direction_to(strike_at) * 7.0
				struck = target.distance_squared_to(strike_at) < STRIKE_RADIUS * STRIKE_RADIUS
				_set_phase(Phase.RECOVER)
		Phase.RECOVER:
			if elapsed >= RECOVERY_TIME:
				_set_phase(Phase.CHASE)
		Phase.STAGGER, Phase.FALL:
			push = push.move_toward(Vector2.ZERO, BRAKE * delta)
			position += push * delta
			if phase == Phase.STAGGER and elapsed >= 0.29:
				cooldown = 0.20
				_set_phase(Phase.CHASE)
			elif phase == Phase.FALL and elapsed >= 0.56:
				hide()
	position = position.clamp(bounds.position, bounds.end)
	_draw_pose()
	queue_redraw()
	return struck


func _set_phase(next: Phase) -> void:
	phase = next
	elapsed = 0.0


func _draw_pose() -> void:
	var motion := idle_motion
	var time := fmod(stride * 1000.0, float(idle_motion.duration_ms))
	var step_height := roundf(absf(sin(stride * 13.0))) if phase == Phase.CHASE else 0.0
	paint.modulate = Color.WHITE
	match phase:
		Phase.STAGGER, Phase.FALL:
			motion = hit_motion if phase == Phase.STAGGER else fall_motion
			time = elapsed * 1000.0
			if elapsed < 0.065:
				paint.modulate = Color(2.1, 1.8, 1.7)
			elif phase == Phase.FALL:
				paint.modulate.a = 1.0 - smoothstep(0.27, 0.56, elapsed)
		Phase.WINDUP:
			paint.modulate = Color(1.25, 0.83, 0.81)
	paint.position = Vector2(0, -step_height)
	paint.scale = Vector2(facing * PAINT_SCALE, PAINT_SCALE)
	paint.texture = motion.lit
	paint.offset = -motion.pivot
	var frame: Dictionary = motion.frames[motion.frame_at(time)]
	paint.region_rect = Rect2(frame.x, frame.y, frame.w, frame.h)


func _draw() -> void:
	draw_rect(Rect2(-10, -2, 20, 4), Color("#21182b"))
	if phase == Phase.WINDUP:
		var point := (strike_at - position).round()
		var tint := Color("#f58b8b")
		tint.a = lerpf(0.4, 0.92, elapsed / WINDUP_TIME)
		draw_arc(point, STRIKE_RADIUS, 0, TAU, 24, tint, 1.5)
	for i in hp:
		draw_rect(Rect2(-5 + i * 6, -49, 4, 2), Color("#e3ae83"))
