# 봉인의 방 해골

## 원화 v002

왈츠 원화의 카메라 높이와 명암을 기준으로 묘지 경비병을 다시 디자인했다. 각진 눈썹뼈와 어두운 눈구멍, 갈비뼈 사이의 빈 공간을 크게 잡았다. 오른쪽 어깨에만 낡은 철 갑옷을 두고 허리는 자주색 천으로 묶었다. 맨손 공격과 보행에 필요한 관절이 보이도록 팔과 다리를 드러냈다.

정면, 우측전면, 우측측면, 우측후면, 후면의 발을 같은 기준선에 맞췄다. 왈츠와 같은 64×64px 셀과 (32, 58) 피벗으로 줄이면 두 캐릭터의 대기 높이는 46px이다. [5방향 원화](sources/v002/originals/crypt-skeleton-turnaround.png) · [픽셀 시트 3배](materials/v002/prepared/pixels-3x.png) · [왈츠와 크기 비교](materials/v002/previews/scale-comparison-3x.png)

[재료 기록](materials/v002/revision.json) · [ImageGen 프롬프트](sources/v002/imagegen-prompt.txt)

<a id="전투-모션-v003"></a>
<a id="전투-모션-v004"></a>

## 전투 모션 v005

우측전면과 우측후면에서 팔꿈치와 무릎, 손목과 발목을 나눴다. 게임은 반대쪽 이동에 좌우 반전을 사용한다. [Godot 사망 자세 1배율 화면](motions/combat/v004/previews/chamber-contact-1x.png) · [이동·공격 대표 자세](motions/combat/v002/previews/motion-poses-2x.png)

| 모션 | 동작 | 재생 |
| --- | --- | --- |
| 이동 | 양발이 지면을 번갈아 딛는 440ms 루프. 반대쪽 팔과 허리 천이 따라온다. | [이동](motions/combat/v002/previews/walk.gif) |
| 피격 | 두개골과 흉곽이 뒤로 튕기고 290ms 동안 자세를 되찾는다. | [피격](motions/combat/v002/previews/hit.gif) |
| 공격 | 팔을 당겨 360ms 동안 예고한다. 내지르는 첫 셀에 타격 판정이 나고 520ms 동안 팔을 거둔다. | [공격](motions/combat/v002/previews/attack.gif) |
| 사망 | 바라보던 방향의 반대쪽 대각선으로 쓰러진다. 흉곽과 얼굴이 위를 향하고, 등이 닿은 뒤 두개골이 마지막으로 내려앉는다. 12프레임, 전체 720ms. | [후면 발 위치 전후 비교](motions/combat/v005/previews/rear-foot-comparison.gif) |

왈츠 사망 모션과 같은 방식으로 두 발의 접지점을 맞추고, 몸통의 길이만 눕는 축을 따라 줄였다. [바닥 자세 원화](sources/v003/originals/supine-contact.png)에서 분리한 흉곽과 두개골은 각각 움직인다. 사망 셀은 96×96px이며 발 피벗의 높이는 58px이다.

v005 후면 동작에서는 첫 프레임의 두 발 그림과 발목 위치를 끝까지 유지한다. 바닥 자세의 다리는 그 발목에 이어지며, 발밑 표시가 있는 비교 GIF로 실제 발 픽셀을 확인할 수 있다. 전면 사망 모션은 v004 시트를 사용한다.

게임 루트에서 후면 사망 모션의 컬러·노멀·이미시브 시트를 다시 굽는다. `--publish`가 후면 컬러 시트만 게임에 적용한다.

~~~powershell
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v005.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v005.py --publish
~~~

[동작 레시피와 시트](motions/combat/v005/revision.json) · [Windows SpriteCut 뷰어](spritecut-viewer.cmd) · [v004](motions/combat/v004/revision.json) · [v003](motions/combat/v003/revision.json) · [v002](motions/combat/v002/revision.json)
