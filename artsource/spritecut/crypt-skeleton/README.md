# 봉인의 방 해골

## 원화 v002

왈츠 원화의 카메라 높이와 명암을 기준으로 묘지 경비병을 다시 디자인했다. 각진 눈썹뼈와 어두운 눈구멍, 갈비뼈 사이의 빈 공간을 크게 잡았다. 오른쪽 어깨에만 낡은 철 갑옷을 두고 허리는 자주색 천으로 묶었다. 맨손 공격과 보행에 필요한 관절이 보이도록 팔과 다리를 드러냈다.

정면, 우측전면, 우측측면, 우측후면, 후면의 발을 같은 기준선에 맞췄다. 왈츠와 같은 64×64px 셀과 (32, 58) 피벗으로 줄이면 두 캐릭터의 대기 높이는 46px이다. [5방향 원화](sources/v002/originals/crypt-skeleton-turnaround.png) · [픽셀 시트 3배](materials/v002/prepared/pixels-3x.png) · [왈츠와 크기 비교](materials/v002/previews/scale-comparison-3x.png)

[재료 기록](materials/v002/revision.json) · [ImageGen 프롬프트](sources/v002/imagegen-prompt.txt)

## 전투 모션 v003

우측전면과 우측후면에서 팔꿈치와 무릎, 손목과 발목을 나눴다. 게임은 같은 피벗에 두 방향을 배치하고 반대쪽 이동은 좌우 반전을 사용한다. [Godot 사망 자세 1배율 화면](motions/combat/v003/previews/chamber-falls-1x.png) · [이동·공격 대표 자세](motions/combat/v002/previews/motion-poses-2x.png)

| 모션 | 동작 | 재생 |
| --- | --- | --- |
| 이동 | 양발이 지면을 번갈아 딛는 440ms 루프. 반대쪽 팔과 허리 천이 따라온다. | [이동](motions/combat/v002/previews/walk.gif) |
| 피격 | 두개골과 흉곽이 뒤로 튕기고 290ms 동안 자세를 되찾는다. | [피격](motions/combat/v002/previews/hit.gif) |
| 공격 | 팔을 당겨 360ms 동안 예고한다. 내지르는 첫 셀에 타격 판정이 나고 520ms 동안 팔을 거둔다. | [공격](motions/combat/v002/previews/attack.gif) |
| 사망 | 무릎이 꺾인 뒤 바라보던 방향의 반대쪽 대각선으로 눕는다. 우측전면은 머리가 왼쪽 위, 우측후면은 왼쪽 아래를 향한다. 전체 720ms. | [사망 전후 비교](motions/combat/v003/previews/death-comparison.gif) |

게임 루트에서 리그와 컬러·노멀·이미시브 시트를 다시 굽는다. `--publish`가 확인한 컬러 시트와 SpriteFrames를 게임에 적용한다.

~~~powershell
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/prepare_combat_v002.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v002.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v002.py --publish
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v003.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v003.py --publish
~~~

[동작 레시피와 시트](motions/combat/v003/revision.json) · [Windows SpriteCut 뷰어](spritecut-viewer.cmd) · [이전 v002](motions/combat/v002/revision.json)
