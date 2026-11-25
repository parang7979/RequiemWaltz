extends Node2D

const REQUIEM_ENERGY := 0.72

var normal_maps_enabled := true

@onready var lights: Node2D = $Lights
@onready var environment: Environment = $WorldEnvironment.environment
@onready var spirit_light: PointLight2D = $Lights/Requiem


func _unhandled_key_input(event: InputEvent) -> void:
	if not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_F3:
			lights.visible = not lights.visible
		KEY_F4:
			environment.glow_enabled = not environment.glow_enabled
		KEY_F6:
			normal_maps_enabled = not normal_maps_enabled


func place_spirit_light(source: Sprite2D, ground_offset: float, opacity_limit := 1.0) -> void:
	spirit_light.position = (source.position + Vector2(0.0, ground_offset)).round()
	spirit_light.enabled = source.visible
	spirit_light.energy = REQUIEM_ENERGY * minf(source.modulate.a, opacity_limit)
