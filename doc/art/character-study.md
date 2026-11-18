# 여검사의 측면 조명 기준 포즈

은빛 머리카락, 자줏빛 짧은 망토, 뒤로 트인 검은 옷자락, 긴 결투검을 갖춘 성인 여검사를 53픽셀 높이로 만들었다. 옷단과 부츠의 황동선은 어두운 바닥에서 발 위치를 읽게 하고, 목의 석류석 브로치는 작은 발광 소재가 암부에서 어떻게 보이는지 확인하는 기준이 된다. 원화와 전투 애니메이션을 작업하기 전에 검사 비율과 무기 길이를 실제 방 크기에서 판단하기 위한 정지 포즈다.

| 항목 | 값 |
| --- | --- |
| 프레임 | 64 × 64픽셀, 측면 동·서 각각 한 장 |
| 정면 방향 | `idle_e`는 오른쪽, `idle_w`는 왼쪽. 오른손에 든 검을 양쪽에서 따로 렌더했다. |
| 지면 피벗 | 왼쪽 위 원점에서 (32, 56.74). 정수 배치 시 (32, 57) |
| 발 부착점 | `sole`은 지면 피벗과 일치한다. 검 끝 `sword_tip`은 동쪽에서 피벗 대비 (+29.32, −27.85), 서쪽에서 (−29.32, −27.85)픽셀 |
| 광원 반응 | 컬러와 노멀의 불투명 영역은 방향당 1,103픽셀. 노멀의 +X는 화면 오른쪽, +Y는 위쪽, +Z는 관찰자 쪽이다. |
| 발광 영역 | 브로치에 동쪽 3픽셀, 서쪽 2픽셀 |

[런타임 텍스처](../../assets/actors/vigil)에서 같은 방향의 컬러를 Godot `CanvasTexture.diffuse_texture`, 노멀을 `normal_texture`에 연결한다. `_emissive.png`는 같은 피벗에 조명을 받지 않는 발광 레이어로 겹친다. 좌우 모두 `Sprite2D.centered = true`일 때 발 원점에 대한 스프라이트 위치는 (0, −25)픽셀이다.

## 원본에서 다시 만들기

[캐릭터 원본](../../artsource/spritekiln/specs/characters/vigil/vigil.yaml)에 의상 재료, 머리·망토 형태, 무기와 정지 자세가 있다. [프로젝트 설정](../../artsource/spritekiln/spritekiln.toml)에 카메라와 도구 리비전을 기록했다. SpriteKiln 0.4.0의 CC0 측면 인체 템플릿, 머리, 포니테일, 검, 망토 키트를 활용했다. [SpriteKiln REUSE 기록](https://github.com/LucasJRamos/spritekiln/blob/17ae0ea8d822b9bb543e539118516ae37d25b114/REUSE.toml)

저장소 루트에서 아래 명령을 실행한다. 같은 부모 폴더에 있는 공유 SpriteKiln 가상 환경을 사용하며, 다른 위치에 설치한 경우 `SPRITEKILN_ROOT`로 경로를 지정한다.

```powershell
$kilnRoot = if ($env:SPRITEKILN_ROOT) { $env:SPRITEKILN_ROOT } else { '..\spritekiln' }
& "$kilnRoot\.venv\Scripts\python.exe" artsource/spritekiln/build_vigil.py
```

[빌드 스크립트](../../artsource/spritekiln/build_vigil.py)는 스펙 검증과 전체 렌더를 수행하고 QA 결과를 확인한 뒤, 아틀라스 JSON에 기록된 사각형으로 컬러·노멀·이미시브를 각각 잘라낸다. 생성된 아틀라스, 피벗·소켓 JSON, QA 결과와 검토용 시트는 `artsource/spritekiln/out/vigil/`에 함께 남는다.

2026-11-18 기준 양쪽 포즈와 머리 확대본을 검사했고, 전체 렌더에서 오류·경고 0개와 사용 색상 40개를 확인했다. 캐시를 사용하지 않고 다시 렌더했을 때 아틀라스 3장과 JSON의 바이트가 각각 일치했다. 다음 캐릭터 검토에서는 달리기의 발 접지, 올려베기의 검 끝 궤적, 공중 스왑 때 망토가 손을 가리는 프레임을 확인한다.
