# 확인한 공식 기술·무료 에셋·한국 수사 절차 자료 (2026-11 조사)

## 기술 선택
- Unity 6 HDRP는 고품질 PBR 재질과 실제 조명에 적합하지만, **프로젝트 렌더 파이프라인을 먼저 확인**. 기존 URP에서 예고 없이 바꾸지 말고 기존 씬/Shader/Asset 호환성 실험과 성능 측정 후 결정. https://docs.unity.com/en-us/engine/6000.6/manual/render-pipelines/high-definition-render-pipeline
- Unity 6 UI Toolkit은 런타임 UI·USS 스타일·디자이너 UI Builder를 지원. 원본 V10 UXML/USS 재사용 및 현재 엔진 버전에서 실제 테스트. https://docs.unity.com/en-us/engine/6000.6/manual/uitoolkits/uielements/introduction-ui-toolkit
- Unity Cinemachine Impulse는 실제 소품 접촉과 카메라 반응 신호에 적합. 하지만 매번 흔들면 싸보임. https://github.com/Unity-Technologies/com.unity.cinemachine/blob/main/com.unity.cinemachine/Documentation~/CinemachineImpulse.md
- 손/팔: Animation Rigging Two Bone IK + Blender의 실제 인체/손 리그 + 접촉 AnimationEvent, 아이템별 그립 보정. https://academy.unity.com/courses/animation-rigging-overview
- 물리: Rigidbody/Collider/Joint를 사용하고 물리 엔진 교체보다 사운드/모션/충돌 동기화 먼저. https://docs.unity.com/en-us/engine/6000.3/manual/physics-section/physics-overview/rigidbody/rigidbodies-overview
- 마이크: UnityEngine.Microphone.Start/End/데이터 추출. 인식은 서버의 승인된 STT 모델. https://docs.unity3d.com/kr/6000.0/ScriptReference/Microphone.html
- 실제 AI: Ollama 공식 JSON Schema 출력 또는 OpenAI Structured Outputs. 두 경우 모두 서버에서 필드 검증과 게임 상태 검증 필수. https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx ; https://developers.openai.com/api/docs/guides/structured-outputs
- 실시간 음성은 OpenAI 실시간 대화/트랜스크립션 문서를 참고 가능하나, 품질/비용/개인정보/AI 행동 검증 때문에 게임 세계 상태가 AI 모델에 넘어가선 안 됨. https://developers.openai.com/api/docs/guides/realtime-conversations ; https://developers.openai.com/api/docs/guides/transcription

## 무료 리소스 중 조건부 사용 권장 (상업 가능, CC0 라이선스 공식 표기)
**중요: 아래는 고품질 재질 후보이지 최종 한국형 3D 공간/캐릭터 모델이 아니다. 실제 레퍼런스보다 못하면 사용 금지.**

| 대상 | 검증된 후보 페이지 | 라이선스 | 인게임 적용 주의 |
|---|---|---|---|
| 닳은 페인트 콘크리트 | https://polyhaven.com/a/concrete_wall_001 | Poly Haven CC0 | 복도 일부 벽에만 사용, 한국 빌라 벽지 전부 대체 금지 |
| 실내 오래된 회벽 | https://polyhaven.com/a/plastered_wall | Poly Haven CC0 | 과장된 폐허 느낌이면 제외 |
| 실내 오래된 타일 | https://polyhaven.com/a/interior_tiles | Poly Haven CC0 | 원본 이미지의 타일 크기/시대와 일치할 때만 |
| 거실/현관 낡은 타일 | https://polyhaven.com/a/worn_tile_floor | Poly Haven CC0 | 지나치게 황폐하면 배제 |
| 욕실 베이지 타일 | https://ambientcg.com/view?id=Tiles139 | ambientCG CC0 | 타일 크기, 패턴, 법선 강도 맞춤 |
| 욕실 거친 타일 | https://ambientcg.com/view?id=Tiles141 | ambientCG CC0 | 지나친 얼룩·결함은 사용 금지 |

공식 라이선스: https://polyhaven.com/license 및 https://docs.ambientcg.com/license/
- 사용 전에 개별 파일과 텍스처가 실제 제공되고 라이선스가 동일한지 재확인, 파일별 URL·작가·다운로드 날짜·버전·게임 사용 위치 기록
- 무료 CC0라고 해도 **비주얼 조합 적합성은 완전히 별개**. 나쁜 모델을 번들에 섞지 말라
- 한국형 도어락, 2010년대 빌라, 소형 냉장고, 오래된 원룸 식탁, 고품질 한국인 NPC: 여기서 채택한 만족스러운 무료 3D 모델은 없음. 반드시 **직접 제작·사용자 승인** 경로
- 이미지 참조 화면의 경찰 문장/기관 상징은 허위 실제 기관 로고로 오인되지 않도록 가상 게임 기관 표기로 바꿀 것. 사용 권리와 실재 로고 유사성 검수
- 게임에서 특정 배달앱/식품 브랜드의 로고를 쓰려면 상표/저작권 검토. 직접 만든 가상 브랜드가 안전

## 한국 경찰 현실성 관련 법·절차 참고
- 대한민국 피의자신문에는 진술거부권 고지, 변호인의 참여, 조사 과정 기록 등 절차가 있다. 설정 연도 기준의 규정을 다시 확인하고 전문가 감수. https://www.law.go.kr/LSW/lsInfoP.do?efYd=20261002&lsiSeq=290189
- 경찰수사규칙 및 수사준칙의 조사시간, 변호인 참여, 임의동행 등은 개정될 수 있어 **현재 조문을 설정 연도에 기계적으로 소급 적용하지 말 것**. https://www.law.go.kr/lsInfoP.do?efYd=20261002&lsiSeq=290929
- ‘책상을 치면 용의자 자백 증가’ 같은 룰은 절차와 게임 재미 양쪽에서 설득력이 부족. 불이익·조사중단 가능성을 반드시 보여줄 것

## Steam 출시 주의
Steamworks의 Content Survey에는 게임의 생성형 AI 사용과 실시간 생성 AI 가드레일 관련 항목이 존재. 적법성·신고 체계·오픈AI/서드파티 API 약관·연령 등 실제 출시 시 검토. https://partner.steamgames.com/doc/gettingstarted/contentsurvey?language=english

## 확인 한계
라이선스 페이지와 공식 기술 문서를 확인한 것이며, 개별 3D 리소스를 실제 Unity로 가져와 렌더/성능/재질 품질을 최종 통과시킨 것은 아니다. 특정 자산을 자동으로 다운로드하거나 ZIP에 섞지 않았다
