# 봉인의 방 해골

## 원화 v002

왈츠 원화의 카메라 높이와 명암을 기준으로 묘지 경비병을 다시 디자인했다. 각진 눈썹뼈와 어두운 눈구멍, 갈비뼈 사이의 빈 공간을 크게 잡았다. 오른쪽 어깨에만 낡은 철 갑옷을 두고 허리는 자주색 천으로 묶었다. 맨손 공격과 보행에 필요한 관절이 보이도록 팔과 다리를 드러냈다.

정면, 우측전면, 우측측면, 우측후면, 후면의 발을 같은 기준선에 맞췄다. 왈츠와 같은 64×64px 셀과 (32, 58) 피벗으로 줄이면 두 캐릭터의 대기 높이는 46px이다. [5방향 원화](sources/v002/originals/crypt-skeleton-turnaround.png) · [픽셀 시트 3배](materials/v002/prepared/pixels-3x.png) · [왈츠와 크기 비교](materials/v002/previews/scale-comparison-3x.png)

[재료 기록](materials/v002/revision.json) · [ImageGen 프롬프트](sources/v002/imagegen-prompt.txt)

<a id="전투-모션-v003"></a>
<a id="전투-모션-v004"></a>

## 전투 모션 v006

우측전면과 우측후면에서 팔꿈치와 무릎, 손목과 발목을 나눴다. 게임은 반대쪽 이동에 좌우 반전을 사용한다. [이동·공격 대표 자세](motions/combat/v002/previews/motion-poses-2x.png)

| 모션 | 동작 | 재생 |
| --- | --- | --- |
| 이동 | 양발이 지면을 번갈아 딛는 440ms 루프. 반대쪽 팔과 허리 천이 따라온다. | [이동](motions/combat/v002/previews/walk.gif) |
| 피격 | 두개골과 흉곽이 뒤로 튕기고 290ms 동안 자세를 되찾는다. | [피격](motions/combat/v002/previews/hit.gif) |
| 공격 | 팔을 당겨 360ms 동안 예고한다. 내지르는 첫 셀에 타격 판정이 나고 520ms 동안 팔을 거둔다. | [공격](motions/combat/v002/previews/attack.gif) |
| 사망 | 바라보던 방향의 반대쪽 대각선으로 쓰러진다. 등이 닿은 뒤 두개골이 내려앉는다. 각 방향 12프레임, 전체 720ms. | [v004와 동시 재생](motions/combat/v006/previews/original-parts-comparison.gif) |

v002에서 분리한 두개골, 흉곽, 팔과 다리에 v004의 프레임 길이와 골반·목 궤적을 옮겼다. 발이 지면을 짚은 뒤에는 발목을 고정하고 무릎을 풀어 쓰러진다. 후면에서는 뒤통수가 넘어가 시야에서 벗어날 때 v002의 전면 두개골 파츠가 드러난다. 사망 셀은 96×96px이며 피벗은 (48, 58)이다.

게임 루트에서 사망 모션의 컬러·노멀·이미시브 시트를 다시 굽는다. `--publish`는 채택한 컬러 시트 두 장과 SpriteFrames를 게임에 적용한다.

~~~powershell
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v006.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/crypt-skeleton/authoring/bake_combat_v006.py --publish
~~~

[동작 레시피와 시트](motions/combat/v006/revision.json) · [Windows SpriteCut 뷰어](spritecut-viewer.cmd) · [v004 모션 참조](motions/combat/v004/revision.json) · [v005 발 위치 비교](motions/combat/v005/previews/rear-foot-comparison.gif)
