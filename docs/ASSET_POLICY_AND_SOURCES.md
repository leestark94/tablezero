# 검수 통과 후보만 — 고품질·상업 이용 에셋 조사

조사일 2026-11-21. 실제 다운로드·유니티 import·게임 내 카메라 검증은 미완료

## 실제로 후보로 남길 수 있는 자료

| 자료 | 링크 | 면허·조건 | 게임에서 맡길 역할 | 심사 |
|---|---|---|---|---|
| Poly Haven Concrete Floor | https://polyhaven.com/a/concrete_floor | Poly Haven CC0 | 복도 또는 물건의 낡은 시멘트 표면 | 고해상도 PBR 질감만 참고, 실내 스케일/색상 검증 |
| Poly Haven Smooth Concrete Floor | https://polyhaven.com/a/smooth_concrete_floor | Poly Haven CC0 | 오래된 빌라 계단실 바닥·도장재 | 실내에 부합하는지 테스트 |
| Poly Haven Fabric Leather 01 | https://polyhaven.com/a/fabric_leather_01 | Poly Haven CC0 | 실제 목재/철재 의자에 일부 낡은 패드 소재 | 한국 낡은 조사실 의자 맞춤 제작 시 한정 |
| Poly Haven Old Apartments Walkway HDRI | https://polyhaven.com/a/old_apartments_walkway | Poly Haven CC0 | 조명 테스트 참고만 | **한국 외부 배경 그대로 사용 금지**, 건축양식 부적절 가능 |
| Poly Haven 공식 라이선스 | https://polyhaven.com/license | CC0 상업 이용 가능 | 위 사용권 검증 | 링크 보관 및 도입 시 파일 해시 기록 |
| Fab Standard license | https://dev.epicgames.com/documentation/fab/licenses-and-pricing-in-fab | 에셋별 Standard/CC-BY/구 UE 라이선스 존재 | 무조건 채택 금지 | 개별 에셋 라이선스 검증 후 검수 |

**중요:** 위 자료는 '후보'임. ZIP에 실제 에셋 원본은 포함하지 않음. 무단으로 상용 게임에 적용하지 않음

## 이 프로젝트에서 현재 '적합한 무료 3D 에셋 없음' 처리할 것

- 한국형 빌라 302호 전체 구조물, 신발장·현관문·창호·인터폰·도어락·보일러·분전반
- 한국형 사법경찰 조사실 탁자·의자·녹음 장비·서류철·기록 표지
- 한국인 용의자 고급 인간 모델 3인 및 자연스러운 표정·손·입 근육·리깅
- 형사의 손·소매·장갑과 1인칭 정교한 증거 조작 애니메이션
- 편의점·택배·계좌 화면·휴대전화 화면처럼 실제 한국 정서를 결정하는 오브젝트

단지 무료라는 이유로 서양식 주차장, 미국식 경찰 배지, 외국 과자, 서구 얼굴, 로우폴리 가구, 폴리곤 실루엣, 카툰 NPC 등을 집어넣지 않는다

## 직접 제작해야 할 핵심 자산과 품질 기준

| 우선순위 | 제작물 | 기준 |
|---|---|---|
| P0 | 손 리그 | 사람의 실제 비율, 네일·관절·손등, 검사용 장갑, 포착·회전·봉인 각 애니메이션 |
| P0 | 한국형 302호 / 복도 | 계단 폭, 소형 현관, 신발장, 문턱, 방 크기, 몰딩과 벽지 스케일이 현실적 |
| P0 | 용의자 3명 | 각기 다른 신체비율·헤어·의복·눈동자·시선·기다림 모션, 고품질 페이셜 모프 |
| P0 | 조사실 테이블 세트 | 실제 물건 무게, 의자 다리 마찰, 머그컵 충격, 마이크, 서류, 의자 간격 |
| P0 | 경찰서 소형 업무 공간 | 한국어 표기, 파일 정리, 야간광, 모니터 반사; 번쩍이는 SF 레이아웃 금지 |
| P0 | 음향 | 한국형 복도 소리, 문, 센서등, 냉장고 모터, 보일러, 실제 컵·종이·의자, 한국어 성우 |
| P1 | 실사 혈흔/감식 세트 | 현실적 규모와 분포, 근거 없는 자극적 연출 금지 |
| P1 | 풍부한 생활 소품 | 배달 봉투, 전기세 고지서, 냉장고 자석, 슬리퍼, 우편함, 이불, 정리되지 않은 서랍 |

## Blender/Unity 고급 제작 프로세스
1. 실제 국내 빌라·원룸 건축 사진의 저작권·활용권을 확보하고 현지 문화감수
2. Blender에서 m 단위로 정규화, 실측형 비율, 형태·사용 흔적·PBR 재질 분리
3. Mesh/UV/normal/roughness/albedo/metallic 검수, 임의의 도형 조합 최종 사용 금지
4. 고급 모델 한 개를 만들 때마다 정면·후면·상면·측면 + 실제 조명에서 턴어라운드 검토
5. 인간 모델은 관절 연동, 손가락 분절, 포즈 연결, BlendShape 및 대화 중 호흡 리그 확인
6. Unity HDRP 광원은 현실적인 휘도와 색온도에서 시작, 과도한 색보정/필름그레인 금지
7. 플레이어 시야로 20초 이상 조작하고 스크린샷을 저장하여 품질을 검토
8. `tools/blender_asset_audit.py` + Unity `TZProductionArtAudit`가 구조적 문제를 거르되, 스타일 평가는 사람/비전 검수로

## 법적 주의
Poly Haven은 CC0지만 다른 사이트의 개별 에셋은 CC0가 아닐 수 있다
Fab는 무료라도 라이선스 유형이 다를 수 있고 레거시 Unreal 라이선스가 남아 있을 수 있다
CC-BY는 출처 표기를 요구한다. 배포 직전 라이선스·상표·인물상 복제권·音원 이용권 재확인
`https://polyhaven.com/license` · `https://dev.epicgames.com/documentation/fab/licenses-and-pricing-in-fab`
