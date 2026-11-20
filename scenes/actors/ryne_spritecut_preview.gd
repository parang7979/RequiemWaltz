extends Control

const CATALOG := "res://assets/actors/ryne_spritecut/catalog.json"

@onready var motions: ItemList = $Sidebar/Motions
@onready var stage: Control = $Stage
@onready var paint: Sprite2D = $Stage/Paint
@onready var glow: Sprite2D = $Stage/Paint/Glow
@onready var playback: Button = $Footer/Playback
@onready var info: Label = $Footer/Info

var frames: Array
var frame_ends := PackedInt32Array()
var elapsed_ms := 0.0
var frame_index := -1
var playing := false
var looping := false
var pivot := Vector2.ZERO
var cell := Vector2.ZERO


func _ready() -> void:
	var group := ""
	var catalog: Array = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	for item: Dictionary in catalog:
		if item.group != group:
			group = item.group
			var header := motions.add_item(group)
			motions.set_item_selectable(header, false)
			motions.set_item_custom_fg_color(header, Color("#bdabc9"))
		var row := motions.add_item("   " + str(item.label))
		motions.set_item_metadata(row, item)
	motions.item_selected.connect(_select_motion)
	playback.pressed.connect(_toggle_playback)
	$Footer/Restart.pressed.connect(_restart)
	stage.resized.connect(_place_sprite)
	motions.select(1)
	_select_motion(1)
	motions.grab_focus()


func _select_motion(row: int) -> void:
	var item: Dictionary = motions.get_item_metadata(row)
	var path: String = item.manifest
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	var clip: Dictionary = manifest.clips[item.clip]
	var directory := path.get_base_dir()
	var lit := CanvasTexture.new()
	lit.diffuse_texture = load(directory.path_join(clip.maps.color))
	lit.normal_texture = load(directory.path_join(clip.maps.normal))
	paint.texture = lit
	glow.texture = load(directory.path_join(clip.maps.emissive))
	pivot = Vector2(manifest.pivot[0], manifest.pivot[1])
	cell = Vector2(manifest.cell[0], manifest.cell[1])
	paint.offset = -pivot
	glow.offset = -pivot
	frames = clip.frames
	looping = clip.loop
	frame_ends.clear()
	var total_ms := 0
	for frame: Dictionary in frames:
		total_ms += int(frame.ms)
		frame_ends.append(total_ms)
	$MotionName.text = ("%s  %s" % [item.label, item.version]).strip_edges()
	_place_sprite()
	_restart()


func _place_sprite() -> void:
	if cell.y <= 0:
		return
	var zoom := maxf(1, floorf(minf(stage.size.x / cell.x, (stage.size.y - 4) / cell.y)))
	paint.scale = Vector2.ONE * zoom
	paint.position = Vector2(roundf(stage.size.x * 0.5), stage.size.y - (cell.y - pivot.y) * zoom)
	$Stage/Ground.offset_top = paint.position.y
	$Stage/Ground.offset_bottom = paint.position.y + 1


func _restart() -> void:
	elapsed_ms = 0
	frame_index = -1
	_set_playing(true)
	_show_frame(0)


func _toggle_playback() -> void:
	if elapsed_ms >= frame_ends[-1]:
		_restart()
	else:
		_set_playing(not playing)


func _set_playing(value: bool) -> void:
	playing = value
	playback.text = "일시정지" if playing else "재생"


func _process(delta: float) -> void:
	if not playing:
		return
	elapsed_ms += delta * 1000.0
	var duration := frame_ends[-1]
	if elapsed_ms >= duration:
		if looping:
			elapsed_ms = fmod(elapsed_ms, duration)
		else:
			elapsed_ms = duration
			_show_frame(frames.size() - 1)
			_set_playing(false)
			return
	_show_frame(frame_ends.bsearch(floori(elapsed_ms), false))


func _show_frame(index: int) -> void:
	if index == frame_index:
		return
	frame_index = index
	var f: Dictionary = frames[index]
	paint.region_rect = Rect2(f.x, f.y, f.w, f.h)
	glow.region_rect = paint.region_rect
	info.text = "%d / %d F   ·   %.2f초   ·   %s" % [
		index + 1, frames.size(), frame_ends[-1] / 1000.0, "반복" if looping else "단발"]
