# 레퀴엠 조작구 도트 시안 v003

[Godot 시안](../../../scenes/rooms/requiem_forms_review.tscn) · [실제 재생](../../../doc/art/requiem-forms-v003-preview.gif) · [그립과 포구 확대](../../../doc/art/requiem-forms-v003-details.png)

Godot에서 시안 씬을 열고 **F6**으로 실행한다. **1·2·3**으로 장갑·활·대포를 바꾸고, **WASD**로 왈츠를 이동한다. 마우스로 레퀴엠을 조준하고 좌클릭으로 공격한다. 해골 네 마리가 왈츠를 추격한다. 가까워진 해골은 공격 위치를 바닥에 표시한다. 맞은 해골은 피격 자세와 함께 밀려나고 일반 베기는 명중 시 3틱 정지한다. 이때 왈츠의 이동은 계속된다. **R**은 초기화다. [추격과 이동 전투](../../../doc/art/requiem-pursuit-combat.gif)

**Space**를 누르면 **WASD**로 입력한 방향으로 150ms 동안 최대 43px 회피한다. **Space**만 누르면 조준 방향의 반대로 물러난다. 회피 초반에는 해골의 공격을 피할 수 있다. 장갑을 든 상태에서 회피 도중 좌클릭하거나 착지 후 140ms 안에 공격하면 되베기가 나간다. 회피 중 누른 공격은 착지하는 첫 틱에 시작한다. [회피와 강한 되베기](../../../doc/art/requiem-heavy-counter.gif)

장갑의 손바닥과 손목 안쪽, 활의 안쪽, 대포의 뒤쪽에 작은 눈·코·입이 들어간다. 우측전면과 우측후면을 각각 구웠고 좌측은 게임에서 수평 반전한다. 조작구 셀은 112×104px, 왈츠의 표시 높이는 약 46px다.

왈츠의 걷기는 우측전면과 우측후면 각각 10프레임, 440ms다. 짧은 보폭과 서로 다른 발 디딤 시간으로 살짝 서툰 박자를 만든다. 상체는 제자리에서 최대 1px 들썩인다. 게임은 실제 이동 거리로 걷기 프레임을 진행하고 공격 중에도 걸음을 이어간다. [걷기 확대](../../../doc/art/waltz-walk-directions.gif) · [이동 공격](../../../doc/art/waltz-walk-combat.gif) · [SpriteCut 걷기 기록](motions/walk/v001/revision.json)

일반 베기에서는 후드를 낮추고 손을 가슴 가까이 당긴다. 되베기에서는 양손으로 후드 가장자리를 잡고 더 깊게 몸을 접는다. 고개를 숙인 각도에 맞춰 눈꺼풀의 도트 위치를 잡고, 주변 피부와 머리카락 그림자 색을 섞어 눈을 꼭 감는 표정을 그렸다. 우측후면에서는 가까운 손만 보인다. 두 방향의 상체를 SpriteCut으로 굽고, 이동 중에는 그 아래에서 걷기 발이 계속 움직인다. [일반 베기와 되베기 자세 확대](../../../doc/art/waltz-hood-grab-comparison.gif) · [SpriteCut 상체 동작 기록](motions/upper_reactions/v002/revision.json)

v003 장갑은 손가락이 손잡이를 감싸는 원화로 바꿨다. 대기 도트의 실제 가로 폭은 우측전면 84→69px, 우측후면 80→70px다. 검 손잡이 위치와 마우스를 향하는 칼끝 각도를 정한 뒤, SpriteCut 프레임의 그립을 손잡이에 맞춰 손을 배치한다.

장갑은 손잡이를 축으로 검의 축에서 62도 돌아간 자세로 그린다. 손목이 검의 옆에서 접근하며, 베는 동안에도 손잡이와 손가락의 접점이 맞물린다. [그립 자세 비교](../../../doc/art/requiem-hand-side-grip.gif)

현재 검수 씬에서는 대기 중 검이 마우스를 향한다. 클릭할 때 조준 방향이 베기의 가운데가 되고, 손과 검이 왈츠의 몸통을 축으로 양옆 64도 사이를 돈다. 연속 공격은 회전 방향을 번갈아 사용한다. 118ms 동안 베며, 칼끝 궤적을 기준으로 PixelFX 잔상과 타격을 계산한다. [왈츠 중심 베기](../../../doc/art/requiem-hand-orbit-swing.gif)

레퀴엠은 감쇠 스프링으로 왈츠의 출발과 정지를 따라간다. 회피할 때는 스프링을 느슨하게 해 잠깐 뒤처지고 이후 부드럽게 따라붙는다. 대기 중에는 살짝 떠다니고 마우스가 크게 움직이면 손잡이가 몸통 주변을 돌아 자리 잡는다. 한손검이 베기에 들어갈 때는 몸통 축에 붙고, 베기가 끝나면 떠다니는 위치로 돌아온다. 가까운 적을 조준하면 손잡이의 원호와 PixelFX 궤적을 함께 줄여 베기 거리를 맞춘다.

되베기의 준비 동작은 레퀴엠이 따라붙을 때의 위치와 속도에서 출발한다. 한손검은 150ms 동안 총 210도를 돌아가고 더 넓은 PixelFX 궤적이 붙는다. 명중 시 4틱 정지하며 해골이 더 강하게 밀린다.

되베기가 끝나면 눈을 살짝 뜨고 맞은 해골이 밀려난 방향을 잠깐 본다. 양손을 후드에서 시간차를 두고 떼면서 걷는 자세로 돌아간다. 상체 회복은 약 0.3초며 그 아래에서 걷는 발은 계속 진행한다. 다음 공격이나 회피가 시작되면 새 동작으로 이어진다. [실제 전투](../../../doc/art/requiem-counter-peek.gif) · [상체와 표정 확대](../../../doc/art/waltz-counter-peek.gif) · [SpriteCut 회복 동작 기록](motions/upper_reactions/v003/revision.json)

해골의 공격에 맞으면 왈츠가 눈과 입을 살짝 벌리고, 공격해 온 쪽을 향한 채 반대 방향으로 최대 23px 밀린다. 125ms 동안 발을 버티고 그 뒤 입력 방향으로 다시 걷는다. 레퀴엠은 충격 방향으로 튀면서 위로 움찔하고, 감쇠 스프링을 따라 왈츠 옆으로 돌아온다. [피격과 이동 재개](../../../doc/art/requiem-player-hit.gif) · [피격 자세 확대](../../../doc/art/waltz-hit-reaction.gif) · [SpriteCut 피격 동작 기록](motions/upper_reactions/v004/revision.json)

마지막 체력이 사라지면 왈츠의 무릎이 꺾이고, 몸이 앞으로 무너져 바닥에 엎드린다. 레퀴엠의 조작구는 PixelFX 유동체로 풀린 뒤 뿔 달린 본모습으로 뭉친다. 레퀴엠은 놀라 몸을 뺐다가 왈츠 곁으로 다가가 고개를 숙인다. [본모습](sources/form-studies/true-form/v002/README.md)은 주름 안쪽에 눈과 입이 비치고 팔과 꼬리가 유체로 이어진다. 눈매가 낮아진 뒤 본모습의 소멸 컷으로 이어져 보랏빛 입자로 흩어진다. 전투는 그 자리에서 멈추고 **R**로 다시 시작한다. [체력 0 장면](../../../doc/art/requiem-defeat.gif) · [두 캐릭터 확대](../../../doc/art/requiem-defeat-close-up.gif) · [SpriteCut 쓰러짐 기록](motions/defeat/v001/revision.json)

이후 회피 동작은 입력 방향으로 폴짝 뛴 뒤 어설프게 넘어지고 서둘러 일어나는 리듬을 검토한다. 쓰러짐 모션에서 몸이 앞으로 넘어가는 자세와 바닥에 처음 닿는 자세를 회피의 연결 키로 활용한다.

## 동작과 검 장착

| 조작구 | SpriteCut 프레임 동작 | 게임 동작 |
| --- | --- | --- |
| 장갑 | 손가락이 검 손잡이를 감싼 자세에서 힘을 주었다가 푼다. | 마우스로 베기 방향을 정하고, 왈츠를 축으로 손과 검을 함께 돌린다. 공격 중 손목 뒤 PixelFX 불꽃이 커진다. |
| 활 | 활 끝이 뒤로 당겨지고 발사 직후 펴짐을 지나 한 번 튕긴다. | 프레임별 위아래 활 끝과 검 손잡이 좌표에 시위를 연결한다. 등록된 발사 프레임에 장착 한손검이 날아간다. |
| 대포 | 뒤쪽이 팽창한 뒤 반동으로 뒤로 밀리고 원래 형태로 돌아간다. | 장전 중 검을 감추고, 발사할 때 포구를 지난 검의 컬러와 이미시브만 함께 드러낸다. |

각 방향에는 대기·공격·ENTER·EXIT가 있다. EXIT 118ms와 ENTER 130ms 사이에서 조작구 컬러는 투명해지고 한 개의 공통 PixelFX 유동체가 이어진다. 형태 쌍에 따라 전환 애니메이션을 추가할 필요가 없다.

한손검은 손잡이가 피벗인 68×28px 정적 스프라이트다. 검날만 조명과 독립된 가산 이미시브로 표시된다. 왈츠·조작구의 컬러와 노멀은 SpriteCut으로 구웠고, 조작구 시트의 이미시브는 투명하다. 일렁이는 후미 영체와 전환 유동체는 게임에서 별도의 조명 독립 가산 PixelFX로 표시한다. 공격 궤적, 발사 섬광, 명중 입자는 별도 PixelFX 아틀라스에서 재생한다.

## 재생성

프로젝트 루트에서 실행한다.

~~~powershell
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/waltz/authoring/build_requiem_forms.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/waltz/authoring/build_waltz_walk.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/waltz/authoring/build_waltz_reactions.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/waltz/authoring/build_waltz_defeat.py
node tools/pixelfx/render_requiem_forms.mjs
~~~

SpriteCut 0.1.0, Git 67ba005b109574712c55416bef1c591bf166aaad와 PixelFX 0.3.1, 공유 Git 4ec9a35938d2b0da20cdb19ca72e9de8d6cf4b19를 사용했다. PixelFX 저작권 고지는 공용 도구의 LICENSE와 NOTICE.md에 있다. 검수 씬은 기존 PlinkFX 바람음·영궁·마포·명중음을 함께 사용한다.

[ImageGen 원화와 프롬프트](materials/v003/revision.json) · [SpriteCut 레시피와 시트](motions/forms/v003/revision.json) · [SpriteCut 뷰어](spritecut-viewer.cmd)
