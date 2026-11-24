extends "res://scenes/actors/crypt_skeleton.gd"

signal fire_requested(origin: Vector2, direction: Vector2, kind: int)

enum Kind { WARDEN, LURKER, HEXER, SENTINEL }

const ART := [
	[preload("res://assets/actors/dungeon_monsters/crypt_warden_front_right.png"),
	 preload("res://assets/actors/dungeon_monsters/crypt_warden_back_right.png")],
	[preload("res://assets/actors/dungeon_monsters/spore_lurker_front_right.png"),
	 preload("res://assets/actors/dungeon_monsters/spore_lurker_back_right.png")],
	[preload("res://assets/actors/dungeon_monsters/ossuary_hexer_front_right.png"),
	 preload("res://assets/actors/dungeon_monsters/ossuary_hexer_back_right.png")],
	[preload("res://assets/actors/dungeon_monsters/quartz_sentinel_front_right.png"),
	 preload("res://assets/actors/dungeon_monsters/quartz_sentinel_back_right.png")],
]
const CLIPS := [&"idle", &"walk", &"windup", &"recover", &"hit", &"collapse"]
const VIEWS := ["front_right", "back_right"]
const CELL := 96
const COLUMNS := 8
const MAX_RANGE := 170.0
const RETREAT_RANGE := 67.0

var kind: Kind
var skins: Dictionary[Texture2D, AtlasTexture] = {}


func configure_kind(value: Kind) -> void:
	kind = value
	hp = 3 if kind == Kind.WARDEN or kind == Kind.SENTINEL else 2
	for view in VIEWS.size():
		var index := 0
		for clip in CLIPS:
			var animation := StringName(String(clip) + "_" + VIEWS[view])
			for frame in FRAMES.get_frame_count(animation):
				var original := FRAMES.get_frame_texture(animation, frame)
				var size := original.get_size()
				var corner := Vector2i(index % COLUMNS, floori(index / float(COLUMNS))) * CELL
				var atlas := AtlasTexture.new()
				atlas.atlas = ART[kind][view]
				atlas.region = Rect2(Vector2(corner) + Vector2((CELL - size.x) * 0.5, 0), size)
				skins[original] = atlas
				index += 1


func _update_sprite() -> void:
	super._update_sprite()
	paint.texture = skins.get(paint.texture, paint.texture)


func advance(delta: float, target: Vector2, separation: Vector2, bounds: Rect2) -> bool:
	if kind < Kind.HEXER or phase not in [Phase.CHASE, Phase.WINDUP]:
		return super.advance(delta, target, separation, bounds)
	if not visible:
		return false
	elapsed += delta
	cooldown = maxf(0.0, cooldown - delta)
	var before := position
	if phase == Phase.CHASE:
		var approach := target - position
		_face(approach)
		var distance := approach.length()
		if distance < RETREAT_RANGE or distance > MAX_RANGE:
			var travel := approach.normalized() * (-1.0 if distance < RETREAT_RANGE else 1.0)
			position = (position + (travel + separation * 0.8).normalized() * WALK_SPEED * delta).clamp(
				bounds.position, bounds.end)
		if cooldown == 0.0 and distance <= MAX_RANGE and (distance >= RETREAT_RANGE or position == before):
			strike_at = target
			_set_phase(Phase.WINDUP)
	elif elapsed >= WINDUP_TIME:
		var direction := position.direction_to(strike_at)
		if direction.is_zero_approx():
			direction = Vector2(facing, 0)
		fire_requested.emit(position + direction * 10.0, direction, kind)
		_set_phase(Phase.RECOVER)
		cooldown = 1.10 if kind == Kind.HEXER else 1.25
	var walking := phase == Phase.CHASE and not position.is_equal_approx(before)
	if walking != moving and phase == Phase.CHASE:
		elapsed = 0.0
	moving = walking
	_update_sprite()
	queue_redraw()
	return false


func _draw() -> void:
	if kind < Kind.HEXER:
		super._draw()
		return
	_draw_ground()
	if phase == Phase.WINDUP:
		var tint := Color("#c892ed") if kind == Kind.HEXER else Color("#8bd6d9")
		tint.a = lerpf(0.35, 0.90, elapsed / WINDUP_TIME)
		var aim_point := (strike_at - position).limit_length(MAX_RANGE).round()
		draw_line(Vector2(0, -18), aim_point + Vector2(0, -18), tint, 1.0)
		draw_arc(aim_point, 7.0, 0.0, TAU, 16, tint, 1.0)
	for index in hp:
		draw_rect(Rect2(-5 + index * 6, -49, 4, 2), Color("#e3ae83"))
