extends Node2D

const LANDING_DUST := preload("res://assets/vfx/landing_dust/landing_dust.tscn")

@onready var mouse_light: PointLight2D = $MouseLight

func _process(_delta: float) -> void:
	mouse_light.global_position = get_global_mouse_position()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		var step: float = 0.2 * (event.factor if event.factor > 0.0 else 1.0)
		match event.button_index:
			MOUSE_BUTTON_WHEEL_UP:
				mouse_light.energy = minf(3.0, mouse_light.energy + step)
			MOUSE_BUTTON_WHEEL_DOWN:
				mouse_light.energy = maxf(0.0, mouse_light.energy - step)
	if event.is_action_pressed("toggle_fullscreen"):
		var window := get_window()
		if window.mode == Window.MODE_EXCLUSIVE_FULLSCREEN:
			window.mode = Window.MODE_WINDOWED
		else:
			window.mode = Window.MODE_EXCLUSIVE_FULLSCREEN

func _on_actor_landed(feet: Vector2) -> void:
	var dust := LANDING_DUST.instantiate() as AnimatedSprite2D
	add_child(dust)
	dust.global_position = feet.round()
	dust.animation_finished.connect(dust.queue_free)
	$LandingSound.global_position = feet
	$LandingSound.play()
