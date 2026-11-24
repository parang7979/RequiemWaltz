# 왈츠와 레퀴엠의 봉인 해제 시안

왈츠가 레퀴엠을 풀어 주는 도입과 대화를 시험한 선행 씬이다. 공식 플레이는 F5로 열리는 [봉인의 방](../../scenes/rooms/requiem_forms_review.tscn)을 기준으로 한다.

[Godot 씬](../../scenes/rooms/waltz_combat.tscn) · [전투 재생](../../doc/art/waltz-combat-preview.gif) · [장면 모음](../../doc/art/waltz-combat-stills.png)

씬을 열고 **F6**으로 시작한다. **WASD**로 걷고 **E**로 봉인을 풀거나 대화를 넘긴다. 마우스로 조준하고 좌클릭으로 공격한다. **1** 마검, **2** 영궁, **3** 마포로 바꾸고 **R**로 처음부터 시작한다.

왈츠가 우연히 봉인을 풀자 레퀴엠은 원수인 마왕을 찾아가자고 제안한다. 레퀴엠의 [본모습](../spritecut/waltz/sources/form-studies/true-form/v001/README.md)은 봉인 위로 피어오르고, 전투에서는 각 무기에 이어진 영체로 나타난다. 마검에는 스스로 깜박이는 눈을 그려 두었다. 왈츠는 이동 방향을 바라보고, 레퀴엠의 방향은 마우스를 따른다. 왈츠의 셀은 40×44px이며 발을 2px씩 교대하고 후드는 한 프레임에서 1px 내려간다.

마검은 넓은 각도를 빠르게 벤다. 영궁은 당겼다가 화살 한 발을 쏜다. 마포는 느리게 충전한 뒤 맞은 곳에 범위 폭발을 일으킨다. 실제 명중에 따라 짧은 정지, 충격음과 피격 섬광을 재생하며 충격의 길이와 넉백은 무기별로 다르다. 첫 습격을 끝내면 피해 증가와 회수 시간 감소 중 하나를 고르고 두 번째 습격으로 들어간다.

## 재생성

별도 작업 복사본의 프로젝트 루트에서 실행한다. 픽셀 원본 스크립트는 Python과 Pillow를 사용한다.

```powershell
python artsource/waltz_combat/pixel_art.py
node tools/pixelfx/render_waltz_combat.mjs
node ../plinkfx/dist/cli.js render artsource/audio/waltz_bow.json --rate 48000 --variant 0 -o assets/audio/waltz_bow.wav
node ../plinkfx/dist/cli.js render artsource/audio/waltz_cannon.json --rate 48000 --variant 0 -o assets/audio/waltz_cannon.wav
node ../plinkfx/dist/cli.js render artsource/audio/waltz_unseal.json --rate 48000 --variant 0 -o assets/audio/waltz_unseal.wav
```

왈츠·레퀴엠의 색과 실루엣, 무기 형태는 제공된 콘셉트 시트 세 장을 참고했다. [PixelFX 모듈](../pixelfx/waltz_combat.mjs)은 공용 PixelFX 0.3.1(공유 `4ec9a35938d2b0da20cdb19ca72e9de8d6cf4b19`, 업스트림 `5294518ce7c72e48b6100a744596e0acf57f2826`)에서 60fps 아틀라스로 내보냈다. 공용 체크아웃은 `PIXELFX_ROOT`로 선택할 수 있다. PixelFX 저작권 고지는 공유 도구의 `LICENSE`와 `NOTICE.md`에 있다.

마검 바람음과 공통 명중 섬광·충격음은 [이전 대검 시안에서 가져온 공용 자산](../../doc/art/production-pipeline.md#pixelfx와-plinkfx)이다. 새 레시피는 PlinkFX 0.3.0(공유 `e702c299f23d4fd8337f7a0ad06b4707c3632b69`, 업스트림 `7e5f6a477037679a29df9c5141e9853b1267e7d8`)의 CC0 카탈로그를 바탕으로 한다. 새 WAV는 48kHz 모노 0번 테이크이며 재렌더한 WAV의 SHA-256이 각각 일치했다.

| 효과음 | PlinkFX 원본 | 재생 시간 | 최대 순간 음량 | 트루 피크 | 검사 목표 |
| --- | --- | ---: | ---: | ---: | ---: |
| [영궁](../../assets/audio/waltz_bow.wav) | `bow-twang` | 0.23초 | −24.0 LUFS | −4.0 dBTP | −24 LUFS |
| [마포](../../assets/audio/waltz_cannon.wav) | `explosion` | 0.80초 | −17.1 LUFS | −1.4 dBTP | −18 LUFS |
| [봉인 해제](../../assets/audio/waltz_unseal.wav) | `summon` | 1.13초 | −23.9 LUFS | −10.6 dBTP | −24 LUFS |

각 목표로 `check --rate 48000 --target 값`을 실행했으며 네 테이크가 모두 통과했다.

| 파일 | SHA-256 |
| --- | --- |
| `waltz_bow.json` | `3dafce87ecba5f05b6a006723090ecef3ad55c1a951e84e23fdce4cbce90a408` |
| `waltz_bow.wav` | `045cf863410508ba7ce3063a06074159f280f62ae012d6c684fbd3399ca162c5` |
| `waltz_cannon.json` | `19fa70f943131ed71d9102b72e54dc2e86fc5c22d29f8ade807d7d94ef48c909` |
| `waltz_cannon.wav` | `cb69b09614d177965da29b25437ffbae5bb1a0577cf096504ce99edae613187a` |
| `waltz_unseal.json` | `cd84e247218106270cdf3cd2806f18fb4d3fc6051851fbc7367be579fcb152f3` |
| `waltz_unseal.wav` | `5f05031506ad7866bef7c5133aec9853571d6dd9b25f2430178c272931aa5617` |
