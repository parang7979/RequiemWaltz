extends Node2D

const LINKS := preload("res://assets/actors/requiem_forms/chain_links.png")
const LINK_CELL := Vector2(20, 20)
const LINK_STEP := 8.25
const POMMEL_TO_GRIP := 9.0
const REST_LENGTH := 25.0
const HIT_RADIUS := 13.0

var cast: Dictionary
var action_end := 0.0
var _curve := Curve2D.new()
var _strength := 0.0


func configure(timing: Dictionary, duration: float) -> void:
	cast = timing
	action_end = duration
	z_index = 5
	_curve.bake_interval = 2.0


func pose(root: Vector2, bearing: float, elapsed: float, reach: float,
		presence: float, clock: float) -> Transform2D:
	var direction := Vector2.from_angle(bearing)
	var side := -1.0 if direction.x < 0.0 else 1.0
	var down := Vector2(-direction.y, direction.x) * side
	var length := REST_LENGTH
	var drop := 2.0
	var tilt := -0.22
	var sag := 12.0 + 2.0 * sin(clock * TAU / 0.66)
	var release := float(cast.release)
	var at_reach := float(cast.reach)
	var pull := float(cast.pull)
	var caught := float(cast["catch"])
	if elapsed >= 0.0 and elapsed < release:
		var t := smoothstep(0.0, release, elapsed)
		length = lerpf(REST_LENGTH, 13.0, t)
		tilt = lerpf(-0.22, -0.51, t)
		sag = lerpf(sag, 18.0, t)
	elif elapsed >= release and elapsed < at_reach:
		var t := smoothstep(release, at_reach, elapsed)
		length = lerpf(13.0, reach, t)
		drop = lerpf(2.0, -2.0, t)
		tilt = lerpf(-0.51, -0.04, 1.0 - pow(1.0 - t, 3))
		sag = 18.0 * pow(1.0 - t, 1.5)
	elif elapsed >= at_reach and elapsed < pull:
		var t := smoothstep(at_reach, pull, elapsed)
		length = reach + 4.0 * t
		drop = -2.0
		tilt = lerpf(-0.04, -0.30, t)
		sag = 0.0
	elif elapsed >= pull and elapsed < caught:
		var t := clampf(inverse_lerp(pull, caught, elapsed), 0.0, 1.0)
		var arc := sin(PI * t)
		length = lerpf(reach + 4.0, 32.0, smoothstep(0.0, 1.0, t))
		drop = lerpf(-2.0, 3.0, t) + 17.0 * arc
		tilt = lerpf(-0.30, -0.36, t) - 1.18 * pow(arc, .9)
		sag = 6.0 * t * t
	elif elapsed >= caught:
		var t := smoothstep(caught, action_end, elapsed)
		length = lerpf(32.0, REST_LENGTH, t)
		drop = lerpf(3.0, 2.0, t)
		tilt = lerpf(-0.36, -0.22, t)
		sag = lerpf(6.0, sag, t)

	var pommel := root + (direction * length + down * drop) * presence
	var blade := bearing + tilt * side * presence
	_strength = presence
	visible = presence > 0.0
	if visible:
		_curve.clear_points()
		for i in 17:
			var t := i / 16.0
			var bow := sin(PI * t) * sag * presence
			_curve.add_point(root.lerp(pommel, t) + Vector2(0, bow))
	queue_redraw()
	return Transform2D(blade, pommel + Vector2.from_angle(blade) * POMMEL_TO_GRIP)


func hit_leg(elapsed: float) -> int:
	if elapsed >= float(cast.release) and elapsed <= float(cast.reach):
		return 1
	if elapsed >= float(cast.pull) and elapsed <= float(cast["catch"]):
		return -1
	return 0


static func blade_crossed(target: Vector2, from_grip: Vector2, from_tip: Vector2,
		to_grip: Vector2, to_tip: Vector2) -> bool:
	var tip_path := Geometry2D.get_closest_point_to_segment(target, from_tip, to_tip)
	var blade := Geometry2D.get_closest_point_to_segment(target, to_grip, to_tip)
	var sweep := PackedVector2Array([from_grip, from_tip, to_tip, to_grip])
	return (
		minf(target.distance_to(tip_path), target.distance_to(blade)) < HIT_RADIUS
		or Geometry2D.is_point_in_polygon(target, sweep)
	)


func _draw() -> void:
	var length := _curve.get_baked_length()
	var distance := length - 3.0
	var link := 0
	while distance > 0.0:
		var at := _curve.sample_baked(distance)
		var ahead := _curve.sample_baked(minf(distance + 1.0, length))
		var behind := _curve.sample_baked(maxf(distance - 1.0, 0.0))
		draw_set_transform(at.round(), behind.angle_to_point(ahead))
		var tile := Rect2(Vector2((link % 2) * LINK_CELL.x, 0), LINK_CELL)
		var strength := _strength * lerpf(.49, 1.0, smoothstep(0.0, 17.0, distance))
		draw_texture_rect_region(LINKS, Rect2(-LINK_CELL / 2, LINK_CELL), tile,
			Color(1.0, 1.0, 1.0, strength))
		distance -= LINK_STEP
		link += 1
	draw_set_transform(Vector2.ZERO)
