extends CharacterBody2D

signal landed(feet: Vector2)

const IDLE_SHEET := preload("res://assets/actors/ryne/idle.tres")
const WALK_SHEET := preload("res://assets/actors/ryne/walk.tres")
const IDLE_EMISSION := preload("res://assets/actors/ryne/idle_emissive.png")
const WALK_EMISSION := preload("res://assets/actors/ryne/walk_emissive.png")
@export var run_speed := 180.0
@export var walk_speed := 48.0
@export var acceleration := 1450.0
@export var gravity := 1000.0
@export var jump_speed := 350.0

var has_touched_floor := false
var gait := "idle"
var gait_phase := 0.0
@onready var idle_walk: Sprite2D = $IdleWalk
@onready var idle_walk_emission: Sprite2D = $IdleWalk/Emission
@onready var run_sprite: Sprite2D = $Run
@onready var run_emission: Sprite2D = $Run/Emission

func _physics_process(delta: float) -> void:
	var direction := Input.get_axis("move_left", "move_right")
	var top_speed := walk_speed if Input.is_action_pressed("walk_modifier") else run_speed
	velocity.x = move_toward(velocity.x, direction * top_speed, acceleration * delta)
	if not is_zero_approx(direction):
		idle_walk.flip_h = direction < 0.0

	var was_on_floor := is_on_floor()
	if was_on_floor and Input.is_action_just_pressed("jump"):
		velocity.y = -jump_speed
	elif not was_on_floor:
		velocity.y += gravity * delta
	if Input.is_action_just_released("jump") and velocity.y < 0.0:
		velocity.y *= 0.5

	move_and_slide()
	_update_locomotion(delta)
	if is_on_floor() and not was_on_floor:
		if has_touched_floor:
			landed.emit(global_position)
		has_touched_floor = true

func _update_locomotion(delta: float) -> void:
	var speed := absf(get_real_velocity().x)
	if is_on_floor():
		var next_gait := "idle"
		if speed > 1.0:
			next_gait = "walk" if speed <= walk_speed * 1.45 else "run"
		if next_gait != gait and (gait == "idle" or next_gait == "idle"):
			gait_phase = 0.0
		gait = next_gait

	run_sprite.visible = gait == "run"
	idle_walk.visible = not run_sprite.visible
	if run_sprite.visible:
		var count := run_sprite.hframes * run_sprite.vframes
		run_sprite.frame = _advance_frame(delta, count, 50.0, speed / run_speed)
		run_sprite.flip_h = idle_walk.flip_h
		run_emission.frame = run_sprite.frame
		run_emission.flip_h = run_sprite.flip_h
	else:
		var walking := gait == "walk"
		idle_walk.texture = WALK_SHEET if walking else IDLE_SHEET
		idle_walk_emission.texture = WALK_EMISSION if walking else IDLE_EMISSION
		var count := idle_walk.hframes * idle_walk.vframes
		idle_walk.frame = _advance_frame(delta, count, 70.0 if walking else 100.0,
				speed / walk_speed if walking else 1.0)
		idle_walk_emission.frame = idle_walk.frame
		idle_walk_emission.flip_h = idle_walk.flip_h

func _advance_frame(delta: float, count: int, frame_ms: float, rate: float) -> int:
	if is_on_floor():
		gait_phase = fposmod(gait_phase + delta * rate * 1000.0 / (count * frame_ms), 1.0)
	return floori(gait_phase * count)
