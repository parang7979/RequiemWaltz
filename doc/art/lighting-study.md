# 봉인의 방 조명 실험

[봉인의 방](../../scenes/rooms/requiem_forms_review.tscn)을 실행하면 조명, 블룸, 왈츠의 노말 맵이 기본으로 켜진다. 같은 위치에서 아래 키를 눌러 각각의 효과를 비교할 수 있다.

| 키 | 비교 |
| --- | --- |
| **F3** | 방 조명. 횃불 근처와 가운데 제단에서 왈츠와 레퀴엠을 비교한다. |
| **F4** | 블룸. 레퀴엠의 밝은 능선과 검날 가장자리를 비교한다. |
| **F6** | 왈츠의 노말 맵. 횃불이나 레퀴엠 곁에서 후드와 얼굴의 명암을 비교한다. |

## 스프라이트 재질

- **왈츠**는 색상과 노말을 하나의 `CanvasTexture`로 묶는다. 대기, 걷기, 상체 반응과 쓰러짐 모두 기존 모션의 컬러·노말 시트에서 같은 셀을 샘플링한다. 후드와 얼굴은 광원 방향에 따라 명암이 바뀐다. 발광 레이어는 사용하지 않는다. [Godot CanvasTexture](https://docs.godotengine.org/en/4.7/classes/class_canvastexture.html)
- **레퀴엠**의 본체, 검, 사슬은 `unshaded` 재질로 자체 색을 유지한다. 검날은 기존 발광 마스크를 더하고, 본체는 컬러 시트의 밝은 보라색 능선에서 발광을 추출한다. 재질은 어두운 주름이나 금속 장식의 대비를 살리도록 발광을 제한한다. [레퀴엠 재질](../../assets/vfx/requiem_forms/spirit_surface.gdshader)

## 방 조명과 블룸

청보라 주변광 위에 앰버 횃불 두 개와 제단 쪽의 약한 채움광을 둔다. 레퀴엠 아래에는 별도의 보라색 점광원이 있어 바닥과 주변 캐릭터를 비춘다. 점광원은 본체의 위치를 따라가고, 실체가 흩어지는 동안 에너지가 줄어든다. [조명 장면](../../scenes/rooms/seal_chamber_lighting.tscn) · [Godot 2D 조명](https://docs.godotengine.org/en/4.7/tutorials/2d/2d_lights_and_shadows.html)

기존 GL Compatibility에서 밝기 임계값을 사용하는 화면 블룸을 적용했다. 레퀴엠의 밝은 부분과 횃불 불씨가 임계값을 넘을 수 있다. HUD는 별도 캔버스에서 그려 조명과 블룸을 전환해도 밝기가 일정하다. [Godot 2D 글로우](https://docs.godotengine.org/en/4.7/tutorials/3d/environment_and_post_processing.html#using-glow-in-2d)
