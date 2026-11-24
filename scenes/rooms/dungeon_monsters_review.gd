extends "res://scenes/rooms/requiem_forms_review.gd"

const Monster := preload("res://scenes/actors/dungeon_monster.gd")
const Shot := preload("res://scenes/actors/dungeon_monster_shot.gd")
const ROSTER := [Monster.Kind.WARDEN, Monster.Kind.LURKER, Monster.Kind.HEXER, Monster.Kind.SENTINEL]
const DUNGEON_SPAWNS := [Vector2(345, 210), Vector2(395, 283), Vector2(484, 143), Vector2(116, 154)]

var shots: Array[Shot] = []


func _spawn_enemies() -> void:
	_clear_shots()
	for enemy in enemies:
		enemy.hide()
		enemy.queue_free()
	enemies.clear()
	for index in ROSTER.size():
		var monster := Monster.new()
		monster.configure_kind(ROSTER[index])
		monster.configure(DUNGEON_SPAWNS[index], 0.12 * index)
		monster.fire_requested.connect(_launch_shot.bind(monster))
		add_child(monster)
		enemies.append(monster)


func _launch_shot(origin: Vector2, direction: Vector2, kind: int, source: Monster) -> void:
	var shot := Shot.new()
	shot.configure(source, origin, direction, kind)
	add_child(shot)
	shots.append(shot)


func _advance_enemies(delta: float) -> void:
	super._advance_enemies(delta)
	if player_hp <= 0:
		_clear_shots()
		return
	for index in range(shots.size() - 1, -1, -1):
		var shot := shots[index]
		var hit := shot.advance(delta, player)
		if hit or shot.life <= 0.0 or not PLAY_AREA.grow(12.0).has_point(shot.position):
			shot.queue_free()
			shots.remove_at(index)
		if hit and hurt_time <= 0.0 and dodge_elapsed >= DODGE_INVULNERABLE:
			_receive_hit(shot.attacker)
			if player_hp == 0:
				_clear_shots()
				break


func _clear_shots() -> void:
	for shot in shots:
		shot.hide()
		shot.queue_free()
	shots.clear()


func _draw_hud() -> void:
	super._draw_hud()
	hud.draw_rect(Rect2(187, 9, 125, 30), INK)
	_text(Vector2(191, 27), "지하 감옥", 13, GOLD)
