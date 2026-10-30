# MODLOG — 7.62 한글 패치

## 2026-10-25 정찰
- 게임 위치 확인, Blue Sun(Steam판) 설치 상태. EB.exe = 실제 엔진 (1.11 b286).
- REA는 Ghidra 미설정 → 로컬 Ghidra 12.1.4 + JDK 21 로 직접 헤드리스 실행.
  - 프로젝트: `analysis/ghidra_proj/EB`, 문자열 덤프 `analysis/out/strings.tsv`
  - 디컴파일: `tools/decomp.ps1 <addr...>` → `analysis/decomp/<addr>.c`
- 주요 함수: AZP 로더 `006904b0`, 구형 팩 `00690a30`, AZP 작성기 `00690200`, xcrypt `006af9b0`,
  TextParser `006ae0d0`/`006ad3c0`(암호화 플래그), LOCAL `005dcef0`, 퀘스트 텍스트 `006a7290`,
  퀘스트 모듈 `0069a200`, 퀘스트 문자열 복호 `00698ef0`/`006994b0`(키 0x82549171),
  폰트 `00684250`(해상도별 Fonts_*.fnt), `0068a500`(SFont::LoadFont)
- `tools/azp.py list/x` 로 모든 팩 목록·추출 확인 (`analysis/lists/*.txt`).
- 텍스트 파일·Blue Sun 인라인 대사 복호화 성공.
- 원본 게임 파일은 아무것도 수정하지 않음.

## 2026-10-25 한글 출력 DLL — 메인 메뉴 한글 확인
- Defender가 19:46에 `E6.exe`(Blue Sun Steam 런처 = HLA.exe)를 `Program:Win32/Ymacco!rfn`으로 격리.
  복원은 사용자 판단. 그 런처 없이 EB.exe 직접 실행하면 아이템 한도 초과로 크래시(0x482FEB).
- HLA.dll(Hard Life 확장): EB.exe MD5 확인 후 아이템/무기/애드온/탄창 한도 패치. `LibMain(param)`이 다른 스레드를
  멈추고 패치 → d3d9 프록시 DllMain에서 동기 호출로 재현 (HLA.log에 Arrays 출력 확인). `kor_nohla.txt`로 끌 수 있음.
- 텍스트 경로: `SManager2D::AddString`(006844e0) → 큐 → 플러시 `00686310` → `00686030` → `DrawString 00685cd0`
  (item {str,x,y,color,font}, fonts = *(mgr+font*4), mgr=*0x7FCE94, FVF 0x144, VB = mgr+0x64 실제 IDirect3DVertexBuffer9).
  폭 `00684060` cdecl(str,font) = (int)(texW*Σ(u1-u0)). 디바이스 래퍼(0x7DAF24)는 D3D9 vtable과 다른 자체 클래스.
- `src/kor_d3d9` → `build/d3d9.dll`: DrawString/폭 함수 후킹, 1바이트 구간은 원본 호출, KS X 1001 2바이트는 GDI로
  1024² 글리프 캐시(맑은 고딕, 셀높이×0.85, framed 폰트는 1px 외곽선) 후 DrawPrimitiveUP, 스트림소스 복원.
  - CP949 확장 범위는 영어 `’s`(0x92 0x73)를 `뭩`으로 오인 → EUC-KR 범위만 한글로 판정. 번역문에 확장 음절 금지.
  - `kor_strings.txt`(UTF-8 원문\t번역) 표시 단계 치환 — 코드에서 조립되는 문자열·아이템 이름용.
  - `kor_debug.txt` 있으면 그려지는 문자열을 `kor_d3d9.log`에 기록.
- `tools/azp.py build/pack` 추가(patch_1_10 왕복 동일). `tools/make_test_pack.py` → 테스트 `Korean.azp`(LOCAL.TXT 11개 항목 한글).
- 설치(테스트): 게임 폴더에 d3d9.dll, Korean.azp, kor_strings.txt 복사, `INI\vfs.ini` 맨 위에 Korean.azp
  (원본 `vfs.ini.kor_bak`). 되돌리기: `tools/uninstall_test.ps1`.
- 확인: 메인 메뉴 버전 문구 한글(치환표), 캐릭터 생성 화면 체력/기력/속사/남은 포인트(LOCAL.TXT) — 스크린샷 `shot_*_korean.png`.
- 메인 메뉴 버튼(NEW GAME 등)은 텍스트가 아니라 `BMP\HUD\E6_MAINMENU\MAIN_*.E6B` 이미지 → 별도 이미지 작업 필요.
- 아직 미검증: 줄바꿈/자르기 함수(00684cc0~00685a10, TruncateString 00684160)가 2바이트 중간을 자를 가능성, 큰 제목 폰트.
- 게임이 실행 직후 저절로 캐릭터 생성 화면까지 진행되는 경우가 두 번 있었음(원인 미상, 입력 잔류 추정).

## 2026-10-26 — quest text in game, Blue Sun hook, HUD bug
- e6q 052/052 translated. Engine VFS opens loose files (game dir + name) before packs, so e6q can't
  live in Korean.azp. DLL now hooks fopen (0x6BDC5A -> _fsopen 0x6BDBFE) and serves `<game>\Korean\X`
  when it exists. install_test.ps1 copies build/e6q.txt to Korean\Quests\E1P\. Verified in game.
- Blue Sun literals: DLL hooks both script node loaders (0x698EF0 file, 0x6994B0 memory; 6-byte
  trampolines) and swaps type-0x23 node text from kor_quest.txt, allocating like the game
  (pool 0x6AB6D0 thiscall(*0xA11BFC) below 0xDD, operator new 0x6BD299 above).
- bsq 000-016 translated (1985 literals). Skipped script-value-looking lines (AI places, " reached X",
  debug lines).
- BUG found by bisect: bsq 006 line 104 "Loaded Sector " is used by the script as a key; translating it
  leaves the HUD hidden after the character-creation dialog closes. Kept English.
- Edge spaces: editor drops trailing spaces; raw2jsonl now copies EN edge whitespace onto KO.
- Test harness: tools/test_flow.ps1 (log-driven new game -> class -> close; checks HUD pixels),
  tools/quest_subset.py (subset kor_quest.txt for bisecting). Needs kor_debug.txt during the run.
- Known: weapon tooltip "탄창:" garbled (other draw path); bottom-left skill list lines overlap.

## 2026-10-26 (b) — tips/sectors/actors/subtitles
- Translated and packed into Korean.azp: TIPS.TXT 41, SUBTITLES.INI 1595, actor Biography/Default_Hint_Name 474 (464 files), sector Desc 62. build_kor: 11051 translations, 0 problems.
- Verified: test_flow PASS hud=70; loading screen shows the Korean sector Desc and tip (analysis\load1.png).
- Not translated: item names/descriptions (user excluded), actor Name (identifier), sector title ("Arrival" shown in the loading header).

## 2026-10-30 — NPC name labels and tooltips
- NPC labels over heads and small tooltips don't use DrawString. They render into a bitmap through
  DrawTextToBitmapMF 0x683C10, cdecl(x, y, str, color, Bitmap*, font). Each glyph is copied from the font
  texture as (A*cov, RGB*shade). The DLL hooks it (7-byte trampoline): single-byte runs go to the
  original, and Korean pairs are rendered with GDI and written into the bitmap's texture
  (0x6893D0 thiscall -> IDirect3DTexture9*; w/h at +0x28/+0x2C; dirty flag +0x1D = *0x712C2C).
- Tooltip text 0x428910 thiscall(bmp, str, x, y, font) sends one byte at a time to 0x683C10 and splits
  Korean pairs. Hooked (6-byte trampoline): Korean text is drawn line by line through the bitmap hook,
  line height = (int)(0x6840D0(0x6EE7FC, font) * *0x6EE7F8), clip at bmp+0x40.
- Debug-only logging: single-char AddText callers (0x6866A0 wrapper hook) and single-char bitmap callers.
- Verified: bar NPC labels (바텐더, 상인 ...) shown in Korean; user confirmed tooltips are in Korean.
- tools/click.ps1 now has -move (hover without clicking).

## 2026-10-30 (b) — item names and descriptions
- ITEMINFO (INI\ITEMS\ITEMINFO, BlueSun pack) translated: 34 batches, build: ITEMINFO 1234 names, 1669 descriptions;
  total translations 13460, problems 0. Packed into Korean.azp; ITEM "key" lines untouched (engine identifiers).
- build_kor.item_file(): rewrites RealName value and description body per ITEM block; desc lines end with "  " like the original.
  Round-trip with en->en mapping is byte-identical except trailing spaces.
- Names that are only model/brand (+colour) stay English by rule (glossary "아이템" section); generic words translated.
- tools/item_auto.py: pattern translations for repetitive lines (ammo boxes, magazines, uniforms, manuals, bipods, spare barrels,
  "Modified X", "w/ Foregrip"); hand drafts (scratchpad hNNN.txt) win. tools/item_todo.py lists lines the patterns miss.
- Verified: game boots and runs with the new ITEMINFO (test_flow PASS hud=70); built file checked. In-game shop/tooltip view
  of item text not yet seen (test runs skipped the shop).

## 2026-10-30 (c) — release v1.0 packaged
- dist/762_Korean_Patch_v1.0.zip (1.5 MB, sha256 36a130a4...a3f): d3d9.dll, Korean.azp, kor_strings.txt, kor_quest.txt,
  Korean\Quests\E1P\e6q.txt, install_korean.bat + kor_install.ps1 (prepends Korean.azp to INI\vfs.ini, backup vfs.ini.kor_bak),
  uninstall_korean.bat + kor_uninstall.ps1, README_한글패치.txt (UTF-8 BOM; credits, AI disclosure, troubleshooting).
- um publish check: PASS 0 failures 0 warnings (after removing the test install, which made built files look like game files).
- Clean test: extract zip into game folder -> install -> test_flow PASS, Korean UI; uninstall restores vfs.ini and removes files;
  reinstalled release build left in the game folder.
- dist/post_draft.md: release post draft. Upload target not chosen yet.
