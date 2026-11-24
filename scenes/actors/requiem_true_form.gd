extends RefCounted

const IDLE = preload("res://assets/vfx/requiem_forms/true_form_idle.tres")
const CONCERN = preload("res://assets/vfx/requiem_forms/true_form_concern.tres")
const PIVOT := Vector2(64, 50)
const FRAME_RATE := 30.0


static func texture_at(frames: SpriteFrames, elapsed: float) -> Texture2D:
	var count := frames.get_frame_count(&"fx")
	var index := floori(elapsed * FRAME_RATE)
	if frames.get_animation_loop(&"fx"):
		index = posmod(index, count)
	else:
		index = clampi(index, 0, count - 1)
	return frames.get_frame_texture(&"fx", index)
