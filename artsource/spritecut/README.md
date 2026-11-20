# RequiemWaltz의 SpriteCut 제작 경로

공용 제작 도구 저장소는 `../SpriteCut`(게임 루트 기준)이다. 이 게임에는 원화, 캐릭터별 파츠·포즈와 생성한 시트를 저장한다. 제작 도구 기준은 **SpriteCut 0.1.0**, Git `607cf83c011fd54b351b6da2e4bd1ca29fbfd24a`이다. 게임에서 `tools/spritecut_cli.py`는 `SPRITECUT_ROOT`, 이웃 체크아웃, 설치된 패키지 순서로 도구를 찾는다. 환경 변수로 경로를 지정했다면 그 경로를 사용한다.

이 경로의 캐릭터 입력·결과물·예제는 로컬 제작 자료다. 다른 체크아웃에서 아래 레시피와 프리뷰를 사용하려면 해당 제작 폴더를 별도로 준비한다.

## 리네의 새 모션 제작

같은 캐릭터의 납품 시트는 [제작 루트의 시트 규격](ryne/productions/pilot-01/sheet-layout.json)을 공유한다. 리네의 현재 모션 24종과 초기 내려베기 비교본은 64×88 px, 접지 피벗 [32, 85]다. 게임 경로는 `assets/actors/ryne_spritecut/motions/`이고 컬러·노말·이미시브 PNG와 `clips.json`을 함께 설치한다. 기존 씬의 걷기·달리기와 508 걷기는 별도 원화 세트의 비교 자료다.

`motion-start`는 새 버전에 규격 사본을 만든다. 소셜 제작 루트에도 같은 규격을 둔다. 기존 버전의 시트를 개별 재생성할 때는 게임 루트에서 다음 명령을 사용한다. 전체 묶음은 로컬 제작 스크립트 `python artsource/spritecut/ryne/build_preview.py`로 갱신한다.

```powershell
$production = 'artsource/spritecut/ryne/productions/pilot-01'
python tools/spritecut_cli.py normalize "$production/motions/run/v012/sheets/clips.json" "$production/sheet-layout.json" .local/ryne-run-normalized
```

제작 루트는 `artsource/spritecut/ryne/productions/pilot-01`이다. 새 클립에 사용할 재료는 v002, 앞대각 달리기 기준은 run v012다. 같은 루트의 [제작 기준표](ryne/productions/pilot-01/selection.json)에서 채택본과 검수본을 구분한다. 달리기 한 주기는 720ms·40px이며 F23·F24·다음 F01에 왼무릎이 고관절 뒤에 있다. [실제 속도 전후 비교](ryne/productions/pilot-01/motions/run/v012/previews/gait/before-after.gif)

현재 SpriteCut 작업본으로 새 모션을 시작할 때는 게임 루트에서 `python tools/spritecut_cli.py motion-start artsource/spritecut/ryne/productions/pilot-01 클립명`을 실행한다. 각 작업은 출력된 버전을 사용한다. 준비한 드라이버는 대기·걷기·달리기·팔 스윙이며 단발 동작은 방향별 리그의 키 포즈와 타이밍을 저작한다.

## 기존 게임 씬의 걷기와 달리기

저장소 루트에서 실행한다. 아래 명령은 저장된 레시피와 PNG만으로 별도 폴더에 베이크한다.

```powershell
python tools/spritecut_cli.py bake artsource/spritecut/ryne/recipe.json .local/ryne-bake-review
```

검토 후 `assets/actors/ryne_spritecut/`에 PNG 여섯 장과 `clips.json`을 반영하고 `python artsource/spritecut/ryne/build_preview.py`로 Godot 씬에 프레임 시간을 반영한다. [미리보기 씬](../../scenes/actors/ryne_spritecut_preview.tscn)을 열고 F6을 누르면 왼쪽은 걷기 24프레임(960ms), 오른쪽은 달리기 24프레임(640ms)을 반복한다. 이 씬은 베이크된 세 맵을 사용하는 소비 예제다.

메시 포즈 자체를 바꿀 때는 기존 리네 R&D 리그에서 `artsource/spritekiln/studies/ryne-quarter-walk/build_godot_gaits.py`를 SpriteKiln 환경으로 실행한다. 6개 정지 파츠의 맵, 프레임별 꼭짓점, 발 접지, 피벗, 주기당 이동 거리를 갱신한다. Idle·Slash와 해골 원본 및 과거 비교 결과는 기존 연구 디렉터리에 있다.

도구를 업데이트할 때 새 리비전의 SpriteCut 예제 테스트를 실행하고 게임에서 리네 레시피를 다시 베이크한다. 게임에 배포된 선택적 Godot 실시간 코어는 SpriteCut의 `integrations/godot/addons/pixel_cutout/`에서 같은 이름의 파일을 가져온다. 게임용 패널·예제·원화는 RequiemWaltz에서 관리한다.
