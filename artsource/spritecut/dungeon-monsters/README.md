# 지하 감옥 몬스터

Godot에서 [지하 감옥 검수실](../../../scenes/rooms/dungeon_monsters_review.tscn)을 열고 **F6**을 누르면 네 종과 싸울 수 있다. WASD로 이동하고 Space로 회피한다. 좌클릭으로 공격하고 `R`로 전투를 다시 시작한다.

| 몬스터 | 유형 | 공격 |
| --- | --- | --- |
| 묘실 간수 | 근거리 | 녹슨 철갑을 입고 추격해 건틀릿을 내지른다. |
| 균사 잠복자 | 근거리 | 청록색 균사 갓을 단 몬스터가 접근해 손톱으로 공격한다. |
| 납골술사 | 원거리 | 거리를 유지하고 보랏빛 저주탄을 발사한다. |
| 수정 파수꾼 | 원거리 | 조준 방향으로 저주탄보다 빠른 푸른 수정탄을 발사한다. |

[전투실 게임 화면](motions/combat/v001/previews/chamber-1x.png) · [전면·후면 동작 비교](motions/combat/v001/previews/combat.gif) · [대기 자세 시트](motions/combat/v001/previews/roster.png)

네 종 모두 해골의 대기·이동·공격 예고·공격/회수·피격·사망 프레임 시간을 공유한다. 각 몬스터의 관절 위치에 맞춰 동작을 옮기고, 원거리형은 공격 첫 프레임에 투사체를 생성한다. 해골과 같은 전면·후면 2방향 원본과 좌우 반전으로 표시한다.

[원화와 출처](sources/v001/source.json) · [관절 좌표](materials/v001/landmarks.json) · [모션 기록과 시트](motions/combat/v001/revision.json) · [Windows SpriteCut 뷰어](spritecut-viewer.cmd)

게임 루트에서 원화를 등록하고 관절 분리와 베이크를 다시 수행한다. `--publish`가 게임용 컬러 아틀라스를 복사한다.

~~~powershell
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/dungeon-monsters/authoring/bake_monsters.py
../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/dungeon-monsters/authoring/bake_monsters.py --publish
~~~
