# 왈츠 엎어짐 실험 v001

[재생 GIF](previews/looping.gif) · [투명 스프라이트 시트](sheets/prone_fall_study_color.png) · [마지막 자세 원화](source/prone.png)

왈츠가 화면 오른쪽 아래로 넘어지는 한 방향을 시험했다. 무릎이 먼저 꺾이고, 손바닥이 바닥을 짚은 뒤 가슴과 후드가 차례로 내려앉는다. 손을 뻗어 바닥을 향하는 프레임부터 반대쪽 팔은 몸통과 망토에 가려진다. 독립 검수용 클립으로 게임과 연결하지 않았다.

내장 ImageGen에 왈츠의 캐릭터 설정을 텍스트로 입력해 마지막 자세 원화를 먼저 그렸다. 그 원화에서 넘어지는 키 포즈와 중간 포즈를 따로 만들었다. [생성 프롬프트](source/imagegen-prompts.md)에 손과 소매를 수정한 지시도 함께 기록했다.

[포즈 레시피](poses.json)의 점은 각 원화 전체의 좌상단을 기준으로 측정했다. 망토 아래의 골반과 후드 아래의 목은 추정 지점이다. 처음 세 프레임은 지지하는 장화를, 6–9번 프레임은 바닥을 짚은 손바닥을 같은 셀 좌표에 맞췄다. 셀은 100×72 px, 피벗은 (40, 60)이다. 9개 프레임 중 앞의 8개는 470 ms, 마지막 자세는 850 ms다. 클립은 한 번 재생되며, 검수 GIF는 같은 속도로 반복된다.

게임 루트에서 재생성한다.

```powershell
& ../SpriteCut/.venv/Scripts/python.exe artsource/spritecut/waltz/motions/prone_fall_study/v001/build.py build/waltz-prone-fall-study
```

[축 추적 GIF](previews/pose-axes.gif)와 [검수 결과](previews/index.json)에서 접지 순서와 실루엣 분리 검사를 확인할 수 있다. 검수 프레임 9개에서 분리된 실루엣은 없었다.
