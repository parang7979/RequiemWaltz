# 챕터 1 최하층 · 봉인의 방

봉인문과 철제 횃대가 있는 석벽, 마모된 봉인 문양이 새겨진 석판 바닥으로 구성한다. 캐릭터와 공격 예고가 읽히도록 전투 영역은 채도와 대비를 낮췄다.

| 항목 | 크기와 위치 |
| --- | --- |
| 기본 출력 | 1280×720. 640×360 뷰포트를 최근접 필터로 2배 확대 |
| [벽](../../assets/rooms/seal_chamber_wall.png) | 640×68. 뷰포트 원점에서 (0, 44) |
| [바닥](../../assets/rooms/seal_chamber_floor.png) | 640×211. 뷰포트 원점에서 (0, 112) |

[ImageGen 원화](seal_chamber_source.png)를 별도로 보관한다. 넓은 원화의 벽과 바닥 비율을 전투실 좌표에 맞추고 SpriteCut `pixelate`로 픽셀 격자에 맞춘다. 바닥 가장자리와 색을 보정한 뒤 두 텍스처로 저장한다. [Godot 장면](../../scenes/rooms/requiem_forms_review.tscn)이 각 텍스처를 캐릭터와 전투 효과 아래에 배치한다.

공용 SpriteCut 리비전은 `79b60ad93205b59bfc5fba220c30f5eb059eb35e`다. 게임 루트에서 재생성한다.

```powershell
../SpriteCut/.venv/Scripts/python.exe artsource/seal_chamber/build_chamber.py
```
