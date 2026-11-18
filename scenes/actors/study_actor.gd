extends CharacterBody2D

signal landed(feet: Vector2)

@export var run_speed := 180.0
@export var acceleration := 1450.0
@export var gravity := 1000.0
@export var jump_speed := 350.0

var has_touched_floor := false

func _physics_process(delta: float) -> void:
	var direction := Input.get_axis("move_left", "move_right")
	velocity.x = move_toward(velocity.x, direction * run_speed, acceleration * delta)
	if not is_zero_approx(direction):
		$East.visible = direction > 0.0
		$West.visible = direction < 0.0

	var was_on_floor := is_on_floor()
	if was_on_floor and Input.is_action_just_pressed("jump"):
		velocity.y = -jump_speed
	elif not was_on_floor:
		velocity.y += gravity * delta
	if Input.is_action_just_released("jump") and velocity.y < 0.0:
		velocity.y *= 0.5

	move_and_slide()
	if is_on_floor() and not was_on_floor:
		if has_touched_floor:
			landed.emit(global_position)
		has_touched_floor = true
