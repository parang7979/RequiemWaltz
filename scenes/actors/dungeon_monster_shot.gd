extends Node2D

const Monster := preload("res://scenes/actors/dungeon_monster.gd")
const HEIGHT := Vector2(0, -18)
const RADIUS := 10.0

var attacker: Monster
var velocity := Vector2.ZERO
var crystal := false
var life := 0.95


func configure(source: Monster, origin: Vector2, direction: Vector2, kind: int) -> void:
	attacker = source
	position = origin
	crystal = kind == Monster.Kind.SENTINEL
	velocity = direction * (255.0 if crystal else 176.0)
	z_index = 5


func advance(delta: float, target: Vector2) -> bool:
	var previous := position
	position += velocity * delta
	life -= delta
	return Geometry2D.get_closest_point_to_segment(target, previous, position).distance_squared_to(target) <= RADIUS * RADIUS


func _draw() -> void:
	draw_rect(Rect2(-3, -1, 6, 2), Color("#21182b"))
	var direction := velocity.normalized()
	var across := direction.orthogonal()
	var outline := Color("#423653") if not crystal else Color("#28465c")
	var core := Color("#d28cf3") if not crystal else Color("#84e0eb")
	var light := Color("#f7d8ff") if not crystal else Color("#d9ffff")
	var length := 12.0 if crystal else 8.0
	draw_line(HEIGHT - direction * length, HEIGHT, outline, 5.0)
	var point := HEIGHT + direction * 4.0
	var tail := HEIGHT - direction * (5.0 if crystal else 3.0)
	draw_colored_polygon(PackedVector2Array([point, HEIGHT + across * 3.5, tail, HEIGHT - across * 3.5]), core)
	draw_line(HEIGHT - direction, HEIGHT + direction * 2.0, light, 2.0)
