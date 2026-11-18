extends Node2D

const LANDING_DUST := preload("res://assets/vfx/landing_dust/landing_dust.tscn")

func _unhandled_input(event: InputEvent) -> void:
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
