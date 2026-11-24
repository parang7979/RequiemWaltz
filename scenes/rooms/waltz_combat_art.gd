extends Node2D

const Logic = preload("res://scenes/rooms/waltz_combat.gd")
const CHAMBER = preload("res://assets/waltz_combat/chamber.png")
const WALTZ = preload("res://assets/waltz_combat/waltz.png")
const TrueForm = preload("res://scenes/actors/requiem_true_form.gd")
const SPIRIT = preload("res://assets/waltz_combat/weapon_spirit.png")
const WEAPONS = preload("res://assets/waltz_combat/weapons.png")
const GUARD = preload("res://assets/waltz_combat/imp.png")
const SWORD_ARC = preload("res://assets/vfx/waltz_combat/arc.tres")
const SEAL_FLASH = preload("res://assets/vfx/waltz_combat/seal.tres")
const CANNON_BLAST = preload("res://assets/vfx/waltz_combat/cannon.tres")
const CONTACT = preload("res://assets/vfx/combat_study/impact.tres")

const INK := Color("#201627")
const CREAM := Color("#f8e3d5")
const GREY := Color("#d1b3c9")
const GOLD := Color("#efbc92")
const LILAC := Color("#e3aff4")
const AMETHYST := Color("#b66dd6")
const FONT_TITLE_SIZE := 22
const WEAPON_NAMES := ["마검", "영궁", "마포"]
const WEAPON_MOVES := ["쓸어베기", "빠른 화살", "범위 폭발"]
const PACT_SPEAKERS := ["레퀴엠", "왈츠"]
const PACT_LINES := [
	"날 풀어줬군, 왈츠. 마왕에게 갚아 줄 게 있어. 네가 길을 고르면 무기는 내가 맡지.",
	"마, 마왕이요? 알았어요. 저기 뼈다귀들부터 어떻게 해봐요!",
]

@onready var game := get_parent() as Logic
var title: SystemFont
var font: SystemFont
var heavy: SystemFont
var shift := Vector2.ZERO


func _ready() -> void:
	title = SystemFont.new()
	title.font_names = PackedStringArray(["Georgia", "Cambria"])
	font = SystemFont.new()
	font.font_names = PackedStringArray(["Malgun Gothic", "Segoe UI"])
	heavy = font.duplicate() as SystemFont
	heavy.font_weight = 700


func _draw() -> void:
	if title == null:
		return
	var strength := float(game.shake) * 0.33
	shift = (Vector2(sin(game.ticks * 2.3), cos(game.ticks * 1.76)) * strength).round()
	draw_texture(CHAMBER, shift)
	_draw_seal()
	var fighting := game.phase == Logic.Phase.FIGHT
	if fighting:
		_draw_aura()
	for guard in game.guards:
		_draw_threat(guard)
		if guard.position.y < game.player.y:
			_draw_guard(guard)
	if fighting and game.form == Logic.Form.BLADE and game.release_tick() >= 0:
		_draw_atlas(SWORD_ARC, game.release_tick(), Vector2(100, 100), game.sweep_origin,
			game.locked_aim, game.sweep_side)
	var angle := game.weapon_angle()
	if fighting and sin(angle) < -0.12:
		_draw_weapon(angle)
	_draw_waltz()
	if fighting and sin(angle) >= -0.12:
		_draw_weapon(angle)
	for guard in game.guards:
		if guard.position.y >= game.player.y:
			_draw_guard(guard)
	for shot in game.bolts:
		_draw_bolt(shot)
	for burst in game.bursts:
		match burst.kind:
			&"hit":
				_draw_atlas(CONTACT, burst.tick, Vector2(52, 53), burst.position, burst.angle)
			&"seal":
				_draw_atlas(SEAL_FLASH, burst.tick, Vector2(64, 61), burst.position)
			&"cannon":
				_draw_atlas(CANNON_BLAST, burst.tick, Vector2(68, 63), burst.position)
	if game.pointer:
		_draw_cursor()
	_draw_hud()


func _draw_seal() -> void:
	var at := (Logic.SEAL + shift).round()
	var sealed := game.phase == Logic.Phase.SEALED
	var talking := game.phase == Logic.Phase.PACT
	_ellipse(at + Vector2(0, 4), Vector2(36, 13), Color("#8f5ba0") if sealed or talking else Color("#594461"))
	_ellipse(at + Vector2(0, 4), Vector2(29, 10), Color("#725180"))
	_shape([at + Vector2(-24, 0), at + Vector2(-15, -7), at + Vector2(15, -7),
		at + Vector2(24, 0), at + Vector2(22, 8), at + Vector2(-22, 8)], Color("#251a32"))
	_shape([at + Vector2(-21, -1), at + Vector2(-13, -6), at + Vector2(13, -6),
		at + Vector2(21, -1), at + Vector2(13, 4), at + Vector2(-13, 4)], Color("#63446e"))
	draw_line(at + Vector2(-14, -5), at + Vector2(13, -5), Color("#9a699b"))
	if sealed:
		var bob := roundf(sin(game.ticks * 0.065) * 2.0)
		var core := at + Vector2(0, -25 + bob)
		_ellipse(at + Vector2(0, -4), Vector2(34, 15), Color("#b36bd4"), 0.55)
		_shape([core + Vector2(-12, 1), core + Vector2(2, -21), core + Vector2(15, -3),
			core + Vector2(9, 7), core + Vector2(-4, 16)], Color("#5a327b"))
		_shape([core + Vector2(-7, 1), core + Vector2(2, -19), core + Vector2(12, -3),
			core + Vector2(7, 8), core + Vector2(-4, 13)], Color("#b166d5"))
		_shape([core + Vector2(2, -19), core + Vector2(12, -3), core + Vector2(1, 7),
			core + Vector2(-1, -2)], Color("#edb0f4"))
		draw_line(core + Vector2(-4, 5), core + Vector2(2, -17), Color("#fdf0dd"))
		for side in [-1.0, 1.0]:
			var outer := at + Vector2(26 * side, -4)
			draw_line(outer, core, Color("#2c2036"), 3.0)
			for link in range(1, 6):
				var p := outer.lerp(core, float(link) / 6.0).round()
				draw_rect(Rect2(p - Vector2(2, 1), Vector2(4, 3)), Color("#bd86a6"), false)
	if talking:
		var elapsed := float(game.ticks - game.pact_started) / 60.0
		var rise := smoothstep(0.0, 0.50, elapsed)
		var bob := sin(elapsed * TAU / 1.6) * 2.0
		for ring in range(3):
			_ellipse(at + Vector2(0, 4 - 7 * ring), Vector2(36 - ring * 5, 12 - ring * 2), AMETHYST, 0.60)
		var center := at + Vector2(0, lerpf(-18.0, -46.0, rise) + bob * rise)
		draw_set_transform(center.round(), 0.0, Vector2.ONE * lerpf(0.52, 0.87, rise))
		draw_texture(TrueForm.texture_at(TrueForm.IDLE, elapsed), -TrueForm.PIVOT,
			Color(1, 1, 1, smoothstep(0.0, 0.24, elapsed)))
		draw_set_transform(Vector2.ZERO)


func _draw_aura() -> void:
	var at := (game.player + shift).round()
	var active := game.attack >= 0 and game.release_tick() < 0
	var opacity := 0.64 if active else 0.31
	_ellipse(at, Vector2(23, 9), AMETHYST, opacity)
	for i in range(6):
		var angle := i * TAU / 6 + game.ticks * 0.045
		var offset := Vector2(cos(angle) * 23.0, sin(angle) * 9.0).round()
		draw_rect(Rect2(at + offset, Vector2(2, 1)), Color(LILAC, opacity))


func _draw_waltz() -> void:
	var at := (game.player + shift).round()
	_shadow(at, 13)
	var moving: bool = game.velocity.length() > 12.0
	var pose: int = [0, 1, 0, 2][int(game.gait)] if moving else 0
	var blink: bool = game.ticks % 155 in [143, 144, 145, 146, 147]
	if (blink and not moving) or game.i_frames > 43:
		pose = 3
	var tint := Color.WHITE
	if game.i_frames > 0 and game.i_frames % 8 >= 4:
		tint.a = 0.65
	draw_set_transform(at, 0.0, Vector2(-1.0 if game.face_left else 1.0, 1.0))
	var destination := Rect2(-20, -43, 40, 44)
	draw_texture_rect_region(WALTZ, destination, Rect2(40 * pose, 44 * game.face_row, 40, 44), tint)
	draw_set_transform(Vector2.ZERO)


func _draw_threat(guard: Logic.Guard) -> void:
	if guard.hp <= 0:
		return
	if guard.born > 0:
		_ellipse((guard.position + shift).round(), Vector2(18, 9), AMETHYST, 0.75)
	if guard.windup > 0:
		var at := (guard.threat + shift).round()
		_ellipse(at, Vector2(23, 11), Color("#ec756e"), 0.51 + 0.47 * float(27 - guard.windup) / 27.0)
		_ellipse(at, Vector2(18, 8), Color("#d45467"), 0.65)
	if guard.swing > 0:
		var at := (guard.threat + shift).round()
		_ellipse(at, Vector2(22, 10), Color("#ffa18a"), float(guard.swing) / 12.0)


func _draw_guard(guard: Logic.Guard) -> void:
	if guard.hp == 0 and guard.flash == 0:
		return
	var at := (guard.position + shift).round()
	var hop := floorf(absf(sin(guard.gait)) * 2.8)
	if guard.flash > 0:
		hop += 2
	var tint := Color.WHITE
	if guard.born > 0:
		tint = Color(1.1, 0.8, 1.2, 0.35 + 0.60 * float(20 - guard.born) / 20.0)
	elif guard.flash > 0:
		tint = Color(1.65, 1.3, 1.35, 0.65 if guard.hp == 0 else 1.0)
	_shadow(at, 11)
	draw_set_transform(at, guard.windup / 135.0 if guard.face_left else -guard.windup / 135.0,
		Vector2(-1.0 if guard.face_left else 1.0, 1.0))
	draw_texture(GUARD, Vector2(-16, -35 - hop), tint)
	draw_set_transform(Vector2.ZERO)
	if guard.hp > 0:
		for pip in range(guard.total_hp):
			draw_rect(Rect2(at + Vector2(-guard.total_hp * 3 + pip * 6, -40 - hop), Vector2(4, 2)),
				GOLD if pip < guard.hp else Color("#785770"))


func _draw_weapon(angle: float) -> void:
	var t: int = game.release_tick()
	var form: int = game.form
	var recoil := 0.0
	var follow := 0.0
	if game.attack >= 0:
		if t < 0:
			follow = 4.0 * float(t) / float(Logic.WINDUP[form])
		elif form == Logic.Form.CANNON:
			recoil = maxf(0.0, 14.0 - 2.0 * t)
	var bow_draw := form == Logic.Form.BOW and game.attack >= 0 and t < 0
	var flip := -1.0 if cos(angle) < 0.0 else 1.0
	draw_set_transform((game.origin() + shift).round(), angle, Vector2(1, flip))
	var grip := Vector2(Logic.GRIP_DISTANCE + follow - recoil, 0)
	var pulse := roundf(sin(game.ticks * 0.15) * 1.8)
	draw_texture(SPIRIT, grip - Vector2(34, 30 - pulse), Color(1, 0.94, 1.0, 0.94))
	var tint := Color(1.32, 1.1, 1.2) if game.form_flash > 0 else Color.WHITE
	draw_texture_rect_region(WEAPONS, Rect2(grip - Vector2(18, 21), Vector2(80, 42)),
		Rect2(0, 42 * form, 80, 42), tint)
	if form == Logic.Form.BLADE and game.ticks % 123 > 116:
		draw_rect(Rect2(grip + Vector2(10, -2), Vector2(8, 3)), Color("#9561ab"))
		draw_line(grip + Vector2(11, -1), grip + Vector2(16, -1), GOLD)
	if bow_draw:
		var pull := float(game.attack + 1) * 1.35
		var center := grip + Vector2(5 - pull, 0)
		draw_line(grip + Vector2(21, -18), center, LILAC)
		draw_line(center, grip + Vector2(20, 18), LILAC)
		draw_line(center, grip + Vector2(41, 0), CREAM, 2.0)
		_diamond(grip + Vector2(41, 0), Vector2(6, 3), GOLD)
	if form == Logic.Form.CANNON and game.attack >= 0 and t >= 0 and t < 5:
		var muzzle := grip + Vector2(59, 0)
		_diamond(muzzle, Vector2(13 - t * 2, 7 - t), LILAC)
		_diamond(muzzle, Vector2(9 - t, 4), CREAM)
	draw_set_transform(Vector2.ZERO)


func _draw_bolt(shot: Logic.Bolt) -> void:
	var at := (shot.position + shift).round()
	draw_set_transform(at, shot.velocity.angle())
	if shot.is_shell:
		draw_line(Vector2(-35, 0), Vector2(3, 0), AMETHYST, 4.0)
		draw_line(Vector2(-27, 0), Vector2(2, 0), LILAC, 2.0)
		_diamond(Vector2.ZERO, Vector2(13, 7), Color("#9a50be"))
		_diamond(Vector2(3, 0), Vector2(8, 4), CREAM)
		draw_rect(Rect2(-19, -4, 3, 2), GOLD)
	else:
		draw_line(Vector2(-30, 0), Vector2(7, 0), AMETHYST, 2.0)
		draw_line(Vector2(-19, 0), Vector2(7, 0), CREAM)
		_diamond(Vector2(5, 0), Vector2(7, 3), GOLD)
	draw_set_transform(Vector2.ZERO)


func _draw_atlas(atlas: SpriteFrames, frame: int, pivot: Vector2, at: Vector2, angle := 0.0, mirror := 1.0) -> void:
	if frame < 0 or frame >= atlas.get_frame_count(&"fx"):
		return
	draw_set_transform((at + shift).round(), angle, Vector2(1.0, mirror))
	draw_texture(atlas.get_frame_texture(&"fx", frame), -pivot)
	draw_set_transform(Vector2.ZERO)


func _draw_cursor() -> void:
	var at := game.cursor.round()
	for side in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
		draw_line(at + side * 4.0, at + side * 8.0, INK, 3.0)
		draw_line(at + side * 4.0, at + side * 8.0, GOLD)
	draw_rect(Rect2(at, Vector2.ONE), CREAM)


func _draw_hud() -> void:
	draw_rect(Rect2(0, 0, 640, 44), Color("#211828"))
	draw_rect(Rect2(0, 323, 640, 37), Color("#211828"))
	draw_line(Vector2(19, 43), Vector2(621, 43), Color("#795468"))
	draw_line(Vector2(19, 323), Vector2(621, 323), Color("#795468"))
	_text(Vector2(20, 28), "Requiem Waltz", FONT_TITLE_SIZE, CREAM, title)
	_text(Vector2(193, 28), "봉인의 방", 12, GOLD, heavy)
	for i in range(Logic.MAX_HEARTS):
		var at := Vector2(486 + i * 18, 22)
		var color := Color("#eb798a") if game.hearts > i else Color("#624153")
		_shape([at + Vector2(-7, -2), at + Vector2(-7, -4), at + Vector2(-4, -6),
			at + Vector2(-1, -6), at + Vector2(1, -3), at + Vector2(3, -6),
			at + Vector2(6, -5), at + Vector2(8, -2), at + Vector2(7, 1), at + Vector2(1, 6)], color)
		if game.hearts > i:
			draw_line(at + Vector2(-4, -4), at + Vector2(-2, -4), Color("#ffc0b6"))
	_text(Vector2(577, 27), "%d / 2" % game.wave, 12, GOLD, heavy)
	if game.phase == Logic.Phase.SEALED:
		_key(Vector2(20, 331), "WASD")
		_text(Vector2(63, 345), "이동", 12, GREY)
		if game.player.distance_to(Logic.SEAL) < 101.0:
			_key(Vector2(109, 331), "E")
			_text(Vector2(134, 345), "보랏빛 봉인에 손 대기", 12, CREAM, heavy)
		else:
			_text(Vector2(109, 345), "보랏빛 봉인 가까이 가기", 12, CREAM)
		return
	if game.phase == Logic.Phase.PACT:
		_panel(Rect2(19, 245, 602, 70))
		_text(Vector2(32, 268), PACT_SPEAKERS[game.dialogue], 12, LILAC, heavy)
		_text(Vector2(32, 293), PACT_LINES[game.dialogue], 13, CREAM)
		_key(Vector2(592, 254), "E")
		return
	_draw_form_bar()
	match game.phase:
		Logic.Phase.REWARD:
			_panel(Rect2(122, 122, 396, 129))
			_text(Vector2(140, 151), "계약이 깊어진다", 18, CREAM, heavy)
			_text(Vector2(140, 173), "다음 습격에서 발휘할 능력을 고르세요.", 12, GREY)
			_draw_reward(Vector2(139, 189), "1", "충격 증폭", "모든 무기 피해 +1")
			_draw_reward(Vector2(323, 189), "2", "빠른 재소환", "모든 무기 회수 시간 감소")
		Logic.Phase.CLEAR, Logic.Phase.DOWN:
			_panel(Rect2(166, 128, 308, 99))
			var won: bool = game.phase == Logic.Phase.CLEAR
			_text(Vector2(183, 158), "봉인의 방 돌파" if won else "왈츠가 주저앉았다", 18, CREAM, heavy)
			_text(Vector2(183, 182), "다음은 마왕을 찾아갈 차례야." if won else "한 번만 더요. 이번엔 발부터 뗄게요.", 12, GREY)
			_key(Vector2(183, 194), "R")
			_text(Vector2(207, 207), "다시 시작", 11, GREY)


func _draw_form_bar() -> void:
	for i in range(3):
		var x := 19.0 + i * 109.0
		var selected: bool = game.form == i
		var cell := Rect2(x, 328, 104, 27)
		draw_rect(cell, Color("#492b53") if selected else Color("#2f2336"))
		draw_rect(cell, Color("#aa74b0") if selected else Color("#51384f"), false)
		_key(Vector2(x + 4, 332), str(i + 1))
		_text(Vector2(x + 27, 340), WEAPON_NAMES[i], 11, CREAM, heavy)
		_text(Vector2(x + 27, 351), WEAPON_MOVES[i], 9, LILAC if selected else GREY)
		if selected and game.attack >= 0:
			var ready := float(game.attack) / float(Logic.RECOVERY[i] - (5 if game.haste else 0))
			draw_line(Vector2(x + 1, 354), Vector2(x + 1 + ready * 102, 354), LILAC)
	_text(Vector2(363, 340), "WASD 이동    마우스 조준", 11, GREY)
	_text(Vector2(363, 352), "좌클릭 공격    R 다시 시작", 11, GREY)


func _draw_reward(at: Vector2, key: String, name: String, benefit: String) -> void:
	draw_rect(Rect2(at, Vector2(178, 48)), Color("#3c2847"))
	draw_rect(Rect2(at, Vector2(178, 48)), Color("#895987"), false)
	_key(at + Vector2(7, 7), key)
	_text(at + Vector2(32, 20), name, 13, LILAC, heavy)
	_text(at + Vector2(32, 37), benefit, 11, GREY)


func _panel(bounds: Rect2) -> void:
	draw_rect(Rect2(bounds.position + Vector2(3, 4), bounds.size), Color("#211725"))
	draw_rect(bounds, Color("#2c1d34"))
	draw_rect(bounds, Color("#ac7498"), false)
	draw_rect(bounds.grow(-3), Color("#58374e"), false)


func _key(at: Vector2, label: String) -> void:
	var width := heavy.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x
	draw_rect(Rect2(at, Vector2(width + 9, 17)), Color("#4e3653"))
	_text(at + Vector2(4, 12), label, 10, CREAM, heavy)


func _text(at: Vector2, content: String, size: int, ink: Color, typeface: Font = null) -> void:
	draw_string(typeface if typeface != null else font, at, content, HORIZONTAL_ALIGNMENT_LEFT, -1, size, ink)


func _shadow(at: Vector2, radius: float) -> void:
	draw_rect(Rect2(at - Vector2(radius, 2), Vector2(radius * 2.0, 3)), Color("#23182e"))
	draw_rect(Rect2(at - Vector2(radius - 2, 3), Vector2(radius * 2.0 - 4, 5)), Color("#23182e"))


func _ellipse(at: Vector2, radius: Vector2, ink: Color, alpha := 1.0) -> void:
	var points := PackedVector2Array()
	for i in range(37):
		var angle := i * TAU / 36
		points.append((at + Vector2(cos(angle), sin(angle)) * radius).round())
	draw_polyline(points, Color(ink, alpha))


func _diamond(at: Vector2, size: Vector2, ink: Color) -> void:
	_shape([at - Vector2(size.x, 0), at - Vector2(0, size.y),
		at + Vector2(size.x, 0), at + Vector2(0, size.y)], ink)


func _shape(points: Array[Vector2], ink: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points), ink)
