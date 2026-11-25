extends RefCounted

const CONCERN = preload("res://assets/vfx/requiem_forms/true_form_concern.tres")
const VANISH = preload("res://assets/vfx/requiem_forms/true_form_vanish.tres")
const PIVOT := Vector2(64, 50)
const FRAME_RATE := 30.0


static func texture_at(elapsed: float, frames: SpriteFrames = CONCERN) -> Texture2D:
	var count := frames.get_frame_count(&"fx")
	var index := clampi(floori(elapsed * FRAME_RATE), 0, count - 1)
	return frames.get_frame_texture(&"fx", index)
