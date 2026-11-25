shader_type canvas_item;
render_mode unshaded;

varying vec4 tint;

void vertex() {
	tint = COLOR;
}

void fragment() {
	vec4 base = texture(TEXTURE, UV);
	// Most form atlases have empty emission maps. Pick out the painted violet ridges.
	float violet = smoothstep(0.045, 0.19, base.b - base.g);
	float highlights = smoothstep(0.48, 0.84, base.b) * violet;
	vec3 emission = vec3(0.37, 0.25, 0.53) * highlights;
	COLOR = vec4((base.rgb + emission) * tint.rgb, base.a * tint.a);
}
