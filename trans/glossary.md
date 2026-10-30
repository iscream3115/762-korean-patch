# 7.62 한글화 용어집 · 원칙

## 기술 규칙 (빌드 검사 대상)
- `%s %d %02d %i %f %%` 등 서식 지정자는 개수·순서 그대로 유지 (어순상 순서를 바꿔야 하면 문장을 재구성).
- `^` = 줄바꿈. 개수와 위치(문단 구분)를 유지.
- 앞뒤 공백 유지: 조각 문자열(`" eldos "`, `"Garrison from sector "`)은 코드에서 이어 붙임.
  조각은 한국어 어순이 깨지지 않게 중립적으로 번역 (예: `" to "` → `" → "` 같은 기호 활용 가능).
- 큰따옴표 `"` 금지 → `“ ”` 사용. 탭 금지.
- KS X 1001(완성형 2,350자) 밖의 음절 금지 (예: 똠, 쌰, 햏, 뷁). 빌드 스크립트가 검사.
- `[` `]` 안의 지문(행동 묘사)은 대괄호 유지.
- 대화 선택지 태그: `(end conversation)` → `(대화 종료)`, `(accept mission)` → `(임무 수락)`,
  `(decline mission)` → `(임무 거절)`, `(leave)` → `(떠난다)`, `(Cost: 2)` → `(비용: 2)`.

## 말투
- 내레이션·시스템 메시지·일지: 평서체 (~다).
- UI: 명사형·짧게 (불러오기, 설정, 사격 모드).
- 플레이어(주인공) 대사: 기본 해요체, 적대·거친 상황에선 반말 허용.
- NPC: 성격 반영. 군인·갱단·용병은 반말/거친 말투, 관리·상인·의사는 존댓말, 장군·고위층은 하오체 가능.
- 욕설은 순화하되 뉘앙스 유지 (fuck → 젠장/빌어먹을, puto → 개자식).
- 스페인어 감탄사(amigo, señor, puto, muchos gracias)는 음차 유지 가능: 아미고, 세뇨르.

## 고유명사
| 원문 | 번역 |
|---|---|
| Algeira | 알헤이라 |
| Algeirian | 알헤이라인/알헤이라의 |
| Palinero | 팔리네로 |
| Palinerian | 팔리네로인/팔리네로의 |
| Sagrada | 사그라다 |
| Santa Maria / Santa-Maria | 산타마리아 |
| Puerto Viejo | 푸에르토비에호 |
| Fuerte Calderon | 푸에르테칼데론 |
| Ciudad de Oro | 시우다드데오로 |
| Campecino / Kampesino | 캄페시노 |
| Artrigo | 아르트리고 |
| El Vertigo | 엘베르티고 |
| Cali Cantinos / Cali-Cantinos | 칼리칸티노스 |
| Las Vacasiones | 라스바카시오네스 |
| Fortalesa | 포르탈레사 |
| Olvega | 올베가 |
| Jungle Camp | 정글 캠프 |
| Airfield | 비행장 |
| Arulco | 아룰코 |
| General (Alvaro) Sosa | (알바로) 소사 장군 |
| Tanya Tormens | 타냐 토르멘스 |
| General Tormens | 토르멘스 장군 |
| (Emiliano) Calderon / Baron Calderon | (에밀리아노) 칼데론 / 칼데론 남작 |
| Juan Rebenga | 후안 레벵가 |
| Vittori de Castigo | 비토리 데 카스티고 |
| Amaranta Felicidad | 아마란타 펠리시다드 |
| Ippolit Bashirov | 이폴리트 바시로프 |
| Eberto Lim | 에베르토 림 |
| Arturo Bon | 아르투로 본 |
| Koan(s) | 코안(족) |
| Paquito | 파키토 |
| Ramon Lazaro Marquez | 라몬 라사로 마르케스 |
| Sebastian Pereira | 세바스티안 페레이라 |
| Miguel | 미겔 |
| Weaver Rail | 위버 레일 |
| Camacho Muaro | 카마초 무아로 |
| Willi Krauf | 빌리 크라우프 |
| Mateo Matti | 마테오 마티 |
| Daniel Querano | 다니엘 케라노 |
| Pedro Nu(nez) | 페드로 누 |
| Raul Mangosta | 라울 망고스타 |
| Javier Cruz | 하비에르 크루스 |
| Servulo Urbano | 세르불로 우르바노 |
| Diego Alvarez | 디에고 알바레스 |
| Manuel Vargas | 마누엘 바르가스 |
| Carlos Montega | 카를로스 몬테가 |
| Ramon Franco | 라몬 프랑코 |
| Billy-Bob | 빌리밥 |
| Crazy Bob | 크레이지 밥 |
| Sergeant Taco | 타코 상사 |
| Tartera | 타르테라 |

## 조직·용어
| 원문 | 번역 |
|---|---|
| eldos (화폐) | 엘도스 |
| Algeira Liberation Army | 알헤이라 해방군 |
| Algeira Security Subdivision | 알헤이라 보안국 |
| Interior Minister / Ministry | 내무장관 / 내무부 |
| Civil Guard | 민병대 |
| Militia | 민병대 |
| Garrison | 수비대 |
| Rebels / rebel | 반군 |
| Guerillas | 게릴라 |
| Brigade | 여단 |
| Brigade Leader / Senior/Junior Attack Leader | 여단장 / 선임·후임 돌격대장 |
| mercenary / merc | 용병 |
| A.I.M. | A.I.M. |
| sector | 섹터 |
| global map | 전략 지도 |
| Snapshot / Aimed shot | 속사 / 조준 사격 |
| Health / Energy / Strength / Stamina | 체력 / 기력 / 근력 / 지구력 |
| Dexterity / Reaction / Agility / Intellect | 손재주 / 반응 / 민첩 / 지능 |
| Experience / Eyesight / Hearing | 경험 / 시력 / 청력 |
| Shooting / Sniping / Heavy weapons / Throwing | 사격 / 저격 / 중화기 / 투척 |
| Melee / Camouflage / Sapper / Doctor | 근접전 / 위장 / 공병 / 의술 |
| magazine (탄창) / clip | 탄창 / 클립 |
| scope / silencer / suppressor | 조준경 / 소음기 / 소염·소음기 |
| grenade launcher | 유탄 발사기 |
| body armor | 방탄복 |
| med kit | 구급상자 |
| FMJ / HP / AP | 완전피갑탄 / 할로포인트탄 / 철갑탄 |

총기 모델명(AK-74, M4A1, Glock 17, Desert Eagle 등)과 탄약 규격(5.56mm, .45 ACP)은 원문 유지.

## 아이템 (ITEMINFO RealName/설명)
- 제조사·모델명·구경 표기는 원문 유지: `Beretta 92FS (9x19 mm)`, `AK 5.45/30`, `M16`, `FN F2000`. 모델명만 있는 이름은 번역하지 않음.
- 일반 명사만 번역, 이름은 짧게: Big Ammo box → 대형 탄약 상자, Ammo box → 탄약 상자, Magazine → 탄창,
  Box Magazine → 상자형 탄창, Drum Magazine → 드럼 탄창, Clip → 클립, Belt → 탄띠,
  Pistol → 권총, Revolver → 리볼버, Rifle → 소총, Assault rifle → 돌격소총, Sniper rifle → 저격소총,
  Submachine gun/SMG → 기관단총, Machine gun → 기관총, Shotgun → 산탄총, Grenade launcher → 유탄발사기,
  Grenade → 수류탄, Knife → 나이프, Scope → 조준경, Collimator/red dot sight → 도트 조준기,
  Silencer/Suppressor → 소음기, Flashlight → 전술 조명, Laser (LAM) → 레이저, Frontgrip/foregrip → 앞손잡이,
  Stock/butt → 개머리판, folded → 접은, Bipod → 양각대, Rail → 레일, Tactical → 택티컬,
  Vest → 조끼, Body armor → 방탄복, Plate → 방탄판, Helmet → 헬멧, Backpack → 배낭, Pouch → 파우치,
  색: 일반 물품 이름에서만 Black/Tan/Olive/Desert/Camo → 검은색/탄색/올리브색/사막색/위장. 모델명+색 이름(HK G36K WR Tan)은 통째로 원문 유지.
- `w/ X` → `+ X` (예: FN F2000 Tactical w/ Frontgrip → FN F2000 택티컬 + 앞손잡이 (5.56x45 mm)).
- 탄종: FMJ/Full Metal Jacket → 완전피갑(FMJ), Hollow Point/HP → 할로포인트(HP), Soft Point/SP → 소프트포인트(SP),
  AP/Armor Piercing → 철갑(AP), Tracer → 예광탄, Buckshot → 벅샷, Slug → 슬러그. 약어는 괄호로 함께.
- 설명: 평서체(~다). 단위·숫자 원문 유지. `\n` 줄 구분 유지.
