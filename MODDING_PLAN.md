# 7.62 High Calibre — 한글 패치 (Blue Sun Mod 기준)

## 대상
- 설치: `C:\Program Files (x86)\Steam\steamapps\common\7.62` (Steam, 영문판)
- 본체: `EB.exe` (32bit, D3D9, "1.11 Build 286", 소스 경로 `d:\e6\source_for_ger`) — `E6.exe`는 34KB 런처
- 모드: Blue Sun Mod (Steam판). `INI\vfs.ini` 우선순위:
  `BlueSun.azp` > `HWM.azp` > `patch_1_10` > `patch_1_02` > `patch_1_01` > `Pack0.azp`
- 퀘스트: `Quests\E1P\e6q.*`(본편) + `Quests\RAS\BlueSun.*`(Blue Sun 미션팩, `e6q.modinfo`로 연결)

## 포맷 (EB.exe 분석으로 확인)
| 대상 | 구조 | 암호화 |
|---|---|---|
| `.azp` 팩 | `"AZP\x01"`, u32 data_start, u32 6, u32 count / 디렉토리 / zlib 스트림 | 디렉토리만 xcrypt(0xF69DA025) |
| 디렉토리 항목 | u32 name_len, name(cp1251), u32 offset, u32 comp_size, u32 size | |
| `LOCAL.TXT`, `e6q.txt` 등 텍스트 | `ID "문자열"` | 파일 전체 xcrypt(0xF69DA025) |
| 퀘스트 바이트코드 `.gen/.cht` 문자열 | opcode `#`(0x23 00) + u16 len(NUL 포함) + 데이터 | 문자열별 xcrypt(0x82549171) |
| `.FNT` 폰트 | u32 flags, u32 texW, u32 texH, 224×(w,h), 픽셀 RLE | 없음 |

xcrypt = `006af9b0` 의 16비트 mul 스트림 암호 (`tools/azp.py`에 정확히 재현, 복호/암호 둘 다).

## 번역 대상 텍스트
- `LOCAL.TXT` (UI, ID 최대 2048개, 버퍼 64KB 제한 — `005dcef0`)
- `Quests\E1P\e6q.txt` (본편 대사 6,337줄, ID < 0x4000, 버퍼 2MB — `006a7290`)
- `BlueSun.gen/.cht` 인라인 문자열 (Blue Sun 미션 대사)
- `TIPS.TXT`, `INI\SUBTITLES.INI`, `INI\CONFIGLOCAL.INI`, 캐릭터 `Biography`, 섹터 `Name/Desc`
- 아이템 이름: INI에서 **식별자로도 쓰임** → 파일에서 바꾸면 참조가 깨짐. 표시 단계에서 치환 필요.

## 핵심 난관: 한글 출력
- 폰트는 0x20~0xFF 224글자를 텍스처 1장에 담는 1바이트 비트맵 폰트(`SFont::LoadFont` `0068a500`).
- 한글(CP949 2바이트)을 그리려면 엔진 텍스트 그리기 함수를 DLL로 후킹해야 함:
  1. 프록시 DLL(로드 방법 선정 필요)로 EB.exe에 주입
  2. 텍스트 그리기/폭 계산 함수 후킹 → CP949 선행 바이트 처리
  3. 한글 글리프 텍스처(KS X 1001 2,350자 또는 11,172자)를 런타임 생성 또는 미리 구움
  4. 같은 DLL에서 아이템 이름·Blue Sun 대사 치환 테이블 적용 (바이트코드 수정 회피)

## 단계
1. [x] 정찰·포맷 분석, AZP/텍스트 복호화 도구
2. [x] 텍스트 그리기 함수 찾기 → 프록시 DLL로 메뉴에 "한글" 표시 (2026-10-25 확인, HLA.dll 로드 포함)
2b. [ ] 줄바꿈·자르기 함수 2바이트 안전 처리, 제목용 큰 폰트 품질, 메인 메뉴 버튼 이미지(E6B) 한글화
3. [ ] 텍스트 추출기 (LOCAL/e6q/BlueSun/INI → 번역 시트)
4. [ ] 번역 (본편 + Blue Sun)
5. [ ] 재패킹: `Korean.azp`를 vfs.ini 최상단에 추가 (원본 팩 수정 없음)
6. [ ] 게임 내 검증, 설치/제거 스크립트
