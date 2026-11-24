extends RefCounted

# One baked clip, including its authored frame timing and optional dash trajectory.
var lit := CanvasTexture.new()
var emission: Texture2D
var pivot: Vector2
var frames: Array
var ends := PackedInt32Array()
var duration_ms := 0
var dash_samples: Array
var dash_distance := 0.0


func _init(name: String, library := "res://assets/actors/ryne_spritecut/motions", frame_ms: Array = []) -> void:
	var directory := library.path_join(name)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("clips.json")))
	var clip: Dictionary = manifest.clips[name]
	pivot = Vector2(manifest.pivot[0], manifest.pivot[1])
	lit.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	lit.diffuse_texture = load(directory.path_join(clip.maps.color))
	lit.normal_texture = load(directory.path_join(clip.maps.normal))
	emission = load(directory.path_join(clip.maps.emissive))
	frames = clip.frames
	if not frame_ms.is_empty():
		assert(frame_ms.size() == frames.size())
		for i in frames.size():
			frames[i].ms = frame_ms[i]
	if name.begins_with("dash_"):
		var path := directory.path_join("root_motion.json")
		var root_motion: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
		dash_samples = root_motion.samples
		dash_distance = root_motion.advance_px
		# Both dashes are airborne on frame eight. Carry its velocity through the hold.
		_extend_dash_frame(7, 60)
	for frame: Dictionary in frames:
		duration_ms += int(frame.ms)
		ends.append(duration_ms)


func _extend_dash_frame(index: int, extra_ms: int) -> void:
	var step_px := float(dash_samples[index + 1].x_px) - float(dash_samples[index].x_px)
	var extra_px := step_px * extra_ms / float(frames[index].ms)
	frames[index].ms += extra_ms
	for i in range(index + 1, dash_samples.size()):
		dash_samples[i].x_px += extra_px
	dash_distance += extra_px


func frame_at(ms: float) -> int:
	return mini(ends.bsearch(floori(ms), false), frames.size() - 1)


func dash_x(ms: float) -> float:
	var index := frame_at(ms)
	var start_ms := ends[index] - int(frames[index].ms)
	var start_x := float(dash_samples[index].x_px)
	var end_x := dash_distance
	if index + 1 < dash_samples.size():
		end_x = float(dash_samples[index + 1].x_px)
	return lerpf(start_x, end_x, clampf((ms - start_ms) / float(frames[index].ms), 0.0, 1.0))
