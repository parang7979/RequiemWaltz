# 원화 기반 2D 컷아웃 애니메이션

현재 공용 구현은 별도 SpriteCut 저장소에서 관리한다. 이 폴더의 Python 파일은 과거 연구 레시피의 import 경로를 연결한다. 새 시트 제작·도구 리비전·Godot 재생 예제는 [SpriteCut 게임 제작 가이드](../../artsource/spritecut/README.md)에 있다. 아래 내용은 기존 SpriteKiln 연구 경로의 재현 기록이다.

이 프로젝트는 SpriteKiln으로 매 프레임의 뼈와 관절 위치를 구한 뒤, Python에서 원화 조각을 변형해 투명 스프라이트 시트를 만든다. 이 폴더에는 캐릭터마다 다시 쓸 계산을 두고, 원화·마스크·관절 좌표·동작 키·결과물은 각 캐릭터의 작업 폴더에 둔다. 첫 적용 사례는 [리네의 두 번째 3/4 자세](../../artsource/spritekiln/studies/ryne-quarter-walk/)다.

## 어디까지 SpriteKiln인가

두 번째 적용 사례인 [해골 몬스터 Idle](../../artsource/spritekiln/studies/skeleton-quarter-idle/)은 생성 원화 한 장에서 56px 포즈와 36프레임을 만든다. 공유 환경의 Python으로 이 폴더의 `render_idle.py`를 실행한다. 공용 텍스처 등록 및 메시 렌더러를 재사용하고, 두개골·아래턱·흉곽·팔·허리띠의 본과 가중치를 새로 작성했다.

| 단계 | 설치된 SpriteKiln에서 사용한 기능 | 프로젝트에서 제작한 부분 |
|---|---|---|
| 리그와 시간 | `spec.load`가 YAML 상속을 처리하고, `rest_env`와 `Ctx.frame`이 채널 식과 부모·자식 뼈 변환을 평가한다. `frames_of`가 Idle과 Walk의 프레임별 채널과 시간을 제공한다. | 뼈 배치와 길이, 가동 범위, 호흡·스윙 타이밍은 리네용 YAML에 작성했다. Run은 Walk의 위상을 받아 가속·보폭·체공을 다시 계산한다. Slash는 자체 키프레임과 보간을 사용한다. |
| 다리 IK와 접지 | `Ctx`의 두 마디 IK가 다리 길이, 목표 발목, 무릎이 굽을 방향을 받아 무릎·발목 변환을 계산한다. | 발을 디딜 장소와 시점, 신발 밑창의 지면 높이, 뒤꿈치 굴림, 발코가 정면에서 옆으로 보이는 그림, 오른발 고정 여부를 정한다. |
| 원화와 관절 | Idle에서 `Camera.from_spec`와 카메라 투영을 사용한다. 본 변환은 모든 클립의 입력이다. | 투명 원화 등록, 팔·다리·몸통 분리, 가려졌던 옷감 보완, 가중치와 삼각형 텍스처 렌더링을 담당한다. Idle의 눈꺼풀 교체·호흡 변형, 머리카락의 지연, 허벅지를 따라가는 바짓단도 프로젝트 코드와 리네용 값의 조합이다. |
| 횡베기와 출력 | 어깨·팔꿈치·척추 회전과 다리 IK를 평가한다. | 골반이 먼저 도는 순서, 팔의 단축, 손가락과 칼자루의 앞뒤 순서, 손–칼 정렬, 칼끝 잔상, 프레임 합성, PNG·GIF·JSON 출력을 담당한다. |

확인한 공유 체크아웃의 `UPSTREAM.json` 기록은 SpriteKiln **0.4.0**, upstream 커밋 `17ae0ea8d822b9bb543e539118516ae37d25b114`다. 이 방식의 최종 픽셀을 그리는 것은 프로젝트의 NumPy/Pillow 렌더러다. YAML만 표준 SpriteKiln 렌더 명령에 넘기면 해당 원화, 컷아웃 가중치와 손그림 효과가 빠진다. 현재 Godot에 전달할 수 있는 결과는 프레임·피벗·시간이 있는 베이크된 시트다. Godot에서 본과 메시를 실시간으로 구동하는 변환기는 별도 구현 대상이다.

## 공용 코드

| 파일 | 입력과 결과 |
|---|---|
| [pixelate_pose.py](../pixelate_pose.py) | 원화 한 포즈를 지정한 셀과 캐릭터 높이에 맞춰 투명 PNG로 만든다. 원래 CLI 경로를 계속 사용한다. |
| [texture.py](texture.py) | `register_texture(original, cell, pose_height)`가 가운데 정렬된 픽셀 포즈를 원본 RGBA 좌표로 복원한다. 원본 실루엣을 알파로 사용하므로 조각과 관절을 원화 좌표로 지정할 수 있다. |
| [mesh.py](mesh.py) | `SkinMesh`가 원화 조각에서 삼각형 격자를 만들고, `draw(posed)`가 변형된 꼭짓점에 텍스처를 입힌다. `screen`, `rigid`, `segment`, `blend`는 측면 투영과 관절 연결에 사용한다. |
| [contact.py](contact.py) | `sole_outline`이 신발의 실제 밑창을 찾고, `contact_offset`이 굴림 중 접지점이 밀리지 않게 발목 이동량을 구한다. 신발마다 다른 발볼 위치와 굽힘 방식은 호출자가 제공한다. |

## 다음 캐릭터에 적용하기

1. **기준 자세와 픽셀 크기를 정한다.** 한 방향의 전신을 투명 원화로 준비한다. 리네는 64×64 셀에 신장 56px를 썼다. 원본과 픽셀 포즈 모두에서 발이 닿는 기준선을 기록한다.
2. **관절을 원화 위에 한 번 표시한다.** 어깨–팔꿈치–손목과 골반–무릎–발목, 발볼, 머리카락 뿌리, 무기 손잡이 위치를 잡는다. 앞뒤 팔다리를 분리하고 팔을 들어 올렸을 때 드러나는 재킷 안쪽을 채운다. 리네의 좌표와 마스크는 [paint.py](../../artsource/spritekiln/studies/ryne-quarter-walk/paint.py)에 있다.
3. **뼈와 원화 조각을 연결한다.** 관절 길이와 부모를 YAML에 넣고, 각 조각을 `SkinMesh(layer, canvas_size=(w,h), spacing=(dx,dy), origin=(x,y))`로 만든다. 프레임마다 `mesh.vertices`를 뼈에 따라 이동시키고, 관절 주변은 가중치를 섞어 `mesh.draw(posed)`에 넘긴다. `canvas_size`와 `origin`은 최종 64px 시트가 아닌 작업 캔버스의 픽셀 단위다. [Walk의 바짓단·무릎·발목 연결 예시](../../artsource/spritekiln/studies/ryne-quarter-walk/render_walk.py)
4. **동작을 하나씩 맞춘다.** Idle은 발을 고정하고 호흡·눈·머리카락을 본다. Walk는 몸이 전진하는 거리까지 포함해 디딘 발의 미끄러짐을 잰다. Run은 뒤로 밀기–체공–착지 순서와 양팔의 교차를 본다. Slash는 준비–타격–회수의 세 자세에서 팔꿈치·손·칼끝을 확인하고 캔버스를 넓힌다. 이 순서는 재사용할 수 있고, 보폭·가림 순서·쥐는 손 그림·무기 길이는 새 원화에서 정한다.
5. **실제 표시 크기로 확인한다.** 프레임마다 같은 카메라와 피벗을 사용하고, 무기 끝과 머리카락의 잘림, 반복 경계, 정지 중인 발의 픽셀을 검사한다. 시트와 프레임 시간 JSON을 함께 보관한다. [리네의 내보내기 코드](../../artsource/spritekiln/studies/ryne-quarter-walk/render_pixelated.py)

## 리네를 다시 렌더링하기

저장소 루트에서 실행한다. 아래 경로는 이 작업 환경처럼 게임과 SpriteKiln 공유 체크아웃이 나란히 있을 때의 PowerShell 예시다. 렌더링은 공유 환경의 Python을 사용하고, 내부에서 `pixelate_pose.py`를 부르는 PATH의 `python`에는 Pillow·NumPy·SciPy가 필요하다. 같은 이름의 결과를 다시 생성한다.

```powershell
$rigPython = "../spritekiln/.venv/Scripts/python.exe"
$study = "artsource/spritekiln/studies/ryne-quarter-walk"
& $rigPython "$study/render_pixelated.py" --height 56
& $rigPython "$study/compare_slash_foot.py"
```

첫 명령은 Idle → Walk → Run → 기본 Slash를 만든다. 두 번째 명령은 같은 픽셀 원화로 오른발 고정 Slash를 별도 폴더에 렌더링하고 두 버전의 비교 GIF를 만든다. 현재 채택한 기준은 **Idle·Walk·Run은 64×64 셀, Slash는 96×64 셀에 캐릭터의 오른발을 Idle 위치로 고정한 버전**이다. [이동 결과와 기본 베기](../../artsource/spritekiln/studies/ryne-quarter-walk/pixelated-56/) · [채택한 횡베기](../../artsource/spritekiln/studies/ryne-quarter-walk/pixelated-56/slash-idle-right-foot/slash.gif)

입력 미술은 사용자가 제공한 턴어라운드의 두 번째 자세다. PixelLab 자료는 달리기 포즈 및 56px 밀도의 시각적 참고로 사용했다. 초록색 블레이드 PNG는 ImageGen으로 만든 소품이고 손에 쥐는 각도와 잔상은 횡베기 코드에서 계산한다. [횡베기 구현](../../artsource/spritekiln/studies/ryne-quarter-walk/render_slash.py)
