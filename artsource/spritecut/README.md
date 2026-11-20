# RequiemWaltz의 SpriteCut 제작 경로

공용 제작 도구 저장소는 `../SpriteCut`(게임 루트 기준)이다. 이 게임에는 원화, 캐릭터별 파츠·포즈와 생성한 시트를 저장한다. 제작 도구 기준은 **SpriteCut 0.1.0**, Git `5c6a831cca040ebc74e4e51ad889991f51f7d842`이다. 게임에서 `tools/spritecut_cli.py`는 `SPRITECUT_ROOT`, 이웃 체크아웃, 설치된 패키지 순서로 도구를 찾는다. 환경 변수로 경로를 지정했다면 그 경로를 사용한다.

리네 이단 점프 v005(530ms)와 v006(385ms)을 공용 도구의 같은 시간축에서 비교했다. 짧은 클립이 끝나면 마지막 자세를 유지하며 비교 영상은 530ms에 끝난다. 점프 v007과 이단 점프 v006의 연결 양끝에서 컬러·노멀·이미시브 차이는 각각 0픽셀이었다. [재생 길이가 다른 두 버전의 비교](ryne/previews/double-jump-v005-v006-duration/before-after.png) · [게임에서 낙하와 착지까지 재생](ryne/motions/jump/v007/previews/full-jumps-game.gif)

이 경로의 캐릭터 입력·결과물·예제는 로컬 제작 자료다. 다른 체크아웃에서 아래 레시피와 프리뷰를 사용하려면 해당 제작 폴더를 별도로 준비한다.

## Godot 모션 미리보기

[리네 미리보기 씬](../../scenes/actors/ryne_spritecut_preview.tscn)을 열고 **F6**을 누른다. 왼쪽 목록에서 동작을 선택하면 원본 타이밍으로 재생된다. 단발 동작은 마지막 프레임에서 멈추고 **재생**을 누르면 다시 시작한다. **처음부터**는 재생 중에도 첫 프레임으로 돌아간다.

게임은 [모션 카탈로그](../../assets/actors/ryne_spritecut/catalog.json)와 베이크된 컬러·노멀·이미시브 PNG를 읽는다. 모션 24종을 이동·기본 8종, 검술 4종, 소셜 12종으로 묶었다. 비교본에는 초기 내려베기 v001, 기존 씬의 걷기·달리기, 508 걷기가 있다. [올려베기 v002](ryne/productions/pilot-01/motions/slash_up/v002/previews/full-speed.gif)는 현재 생성된 최신 후보이며 재생 시간은 920ms다. 기본 내려베기는 SpriteCut 소셜 제작 폴더의 v002 후보를 사용한다. 이단 점프는 게임 제작 기준표에서 선택한 v002 검수본을 사용한다.

### 소셜 모션 채택본

| 모션 | 클립 | 버전 |
| --- | --- | --- |
| 헐떡이기 | `pant` | v007 |
| 손인사 | `wave` | v004 |
| 무릎 앉기 | `kneel_hug` | v004 |
| 감사 인사 | `thank_you` | v003 |
| 머리 위 스트레칭 | `stretch_overhead` | v001 |
| 응원의 박수 | `applause` | v002 |
| 한 팔씩 뻗기 | `stretch_reach` | v002 |
| 귀 기울이기 | `listen` | v001 |
| 생각하기 | `think` | v001 |
| 대화하기 | `talk` | v001 |
| 꾸벅꾸벅 졸기 | `doze` | v001 |
| 하품하기 | `yawn` | v001 |

소셜 버전은 SpriteCut의 `build/social-ryne/pilot-01/selection.json`을 따른다. 시트를 갱신할 때는 두 프로젝트의 로컬 제작 자료를 준비하고 게임 루트에서 `python artsource/spritecut/ryne/build_preview.py`를 실행한다. 각 동작의 `clips.json`에는 프레임 영역, 재생 시간, 피벗, 반복 여부가 있다. 대시 폴더에는 프레임별 이동을 위한 `root_motion.json`도 있다. 복사한 결과만으로 Godot에서 재생할 수 있다.

## 게임 제작 폴더의 모션 원본

2026-11-20 기준 `pilot-01`에서 컬러·노멀·이미시브 시트를 확인한 동작은 10종이다. 모두 오른쪽 앞대각(`front_right`) 시점이다. 프레임 수와 시간은 각 버전의 `sheets/clips.json` 기준이며 모션 이름을 누르면 해당 속도로 재생되는 미리보기가 열린다.

| 모션 | 클립 | 버전 | 재료 | 프레임 | 재생 시간 | 제작 상태 |
| --- | --- | --- | --- | ---: | ---: | --- |
| [대기](ryne/productions/pilot-01/motions/idle/v002/previews/full-speed.gif) | `idle` | v002 | v002 | 48 | 1,920ms | 검수본 |
| [걷기](ryne/productions/pilot-01/motions/walk/v003/previews/full-speed.png) | `walk` | v003 | v002 | 48 | 1,200ms | 검수본 |
| [달리기](ryne/productions/pilot-01/motions/run/v012/previews/full-speed.gif) | `run` | v012 | v002 | 24 | 720ms | 채택 기준 |
| [팔 스윙](ryne/productions/pilot-01/motions/arm_swing/v002/previews/full-speed.gif) | `arm_swing` | v002 | v001 | 24 | 960ms | 검수본 |
| [점프](ryne/productions/pilot-01/motions/jump/v003/previews/full-speed.gif) | `jump` | v003 | v004 | 26 | 1,160ms | 검수본 |
| [전방 대시](ryne/productions/pilot-01/motions/dash_forward/v001/previews/full-speed.gif) | `dash_forward` | v001 | v004 | 15 | 380ms | 검증된 후보 |
| [후방 대시](ryne/productions/pilot-01/motions/dash_backward/v002/previews/full-speed.gif) | `dash_backward` | v002 | v004 | 15 | 360ms | 검증된 후보 |
| [왼쪽 횡베기](ryne/productions/pilot-01/motions/slash_left/v003/previews/full-speed.gif) | `slash_left` | v003 | v006 | 20 | 780ms | 채택 기준 |
| [오른쪽 횡베기](ryne/productions/pilot-01/motions/slash_right/v003/previews/full-speed.gif) | `slash_right` | v003 | v006 | 20 | 780ms | 채택 기준 |
| [내려베기](ryne/productions/pilot-01/motions/slash_down/v001/previews/downslash.gif) | `slash_down` | v001 | v006 | 26 | 1,040ms | 후보 |

대기·걷기·달리기·팔 스윙은 반복 클립이고 나머지 여섯 동작은 단발이다. 채택 기준과 검수본은 [선택 기록](ryne/productions/pilot-01/selection.json)을 따르고, 후보 상태는 해당 버전의 `revision.json`을 따른다. 두 횡베기는 [오른쪽에서 왼쪽으로 이어 보는 비교본](ryne/productions/pilot-01/reviews/horizontal-slashes-v003/right-then-left.gif)도 있다.

[이단 점프 v002](ryne/productions/pilot-01/motions/double_jump/v002/previews/full-speed.gif)(`double_jump`)는 530ms 단발 동작이다. [v001과 v002의 재생 비교](ryne/productions/pilot-01/motions/double_jump/v002/previews/before-after.gif)에서 두 버전을 볼 수 있다. 헐떡이기는 소셜 제작본 v007을 사용한다.

## 리네의 새 모션 제작

리네의 현재 모션 24종과 초기 내려베기 비교본은 각 제작 버전의 프레임 크기와 피벗으로 납품한다. 대기·횡베기는 64×64 px, 상하 베기는 64×80 px, 점프는 64×88 px다. 게임 루트에서 `python artsource/spritecut/ryne/build_preview.py`를 실행하면 세 재질 PNG와 `clips.json`이 `assets/actors/ryne_spritecut/motions/`에 복사된다.

Godot 미리보기는 시트를 전환할 때 컬러·노말과 발광 스프라이트의 오프셋을 각각 해당 시트의 `-pivot`으로 설정한다. 카탈로그의 모든 셀을 피벗 기준으로 겹친 범위에서 창에 맞는 공통 배율과 바닥 위치를 구하므로 크기가 다른 모션으로 바꿔도 캐릭터의 배율과 접지 기준점이 유지된다.

제작 루트는 `artsource/spritecut/ryne/productions/pilot-01`이다. 새 클립에 사용할 재료는 v002, 앞대각 달리기 기준은 run v012다. 같은 루트의 [제작 기준표](ryne/productions/pilot-01/selection.json)에서 채택본과 검수본을 구분한다. 달리기 한 주기는 720ms·40px이며 F23·F24·다음 F01에 왼무릎이 고관절 뒤에 있다. [실제 속도 전후 비교](ryne/productions/pilot-01/motions/run/v012/previews/gait/before-after.gif)

현재 SpriteCut 작업본으로 새 모션을 시작할 때는 게임 루트에서 `python tools/spritecut_cli.py motion-start artsource/spritecut/ryne/productions/pilot-01 클립명`을 실행한다. 각 작업은 출력된 버전을 사용한다. 준비한 드라이버는 대기·걷기·달리기·팔 스윙이며 단발 동작은 방향별 리그의 키 포즈와 타이밍을 저작한다.

## 기존 게임 씬의 걷기와 달리기

저장소 루트에서 실행한다. 아래 명령은 저장된 레시피와 PNG만으로 별도 폴더에 베이크한다.

```powershell
python tools/spritecut_cli.py bake artsource/spritecut/ryne/recipe.json .local/ryne-bake-review
```

이 레시피의 입력 맵은 `ryne/gait-materials/`에 있다. 기존 걷기(960ms)와 달리기(640ms)의 결과는 `assets/actors/ryne_spritecut/`에 보관하며 미리보기 씬의 **비교본**에서 재생한다.
