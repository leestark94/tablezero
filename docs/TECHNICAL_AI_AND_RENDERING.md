# 엔진·AI·물리·영화형 연출 기술 선택

## 권장 런타임 분리

```text
Unity HDRP PC Client
  - FPS / 손 리그 / 증거 조사 / Cinemachine / Timeline / Animation Rigging
  - 고품질 사운드 / 실시간 소품 물리 / UI Toolkit / HDRP 조명
  - 범인 정답 또는 비공개 세계상태를 직접 보관하지 않음
          │ HTTPS authenticated commands / event stream
          ▼
Authoritative game server
  - CASE001 locked truth / evidence custody / knowledge partitions
  - Statement ledger / story beat gate / action resolver / outcome reviewer
  - Per-character context provider; model isolation and content review
          │ provider adapter (JSON schema)
          ▼
   Ollama (local dev) / optional OpenAI remote API (explicit opt-in)
```

## AI 동작 품질

- 서버 `prompt_context()`에는 **해당 인물이 알고 있는 사실만** 주입, 정답 식별 키는 모델로 전달 금지
- 모델은 `utterance`, `reply_mode`, `motion_id`, `asserted_claim_ids`, `new_unsupported_assertion`, `request_external_action`을 생성
- 새 대사는 미검증 주장. AI가 말한 '봤다'가 현장에 새 영상을 생성하지 않음
- AI가 `contact_acquaintance` 제안해도 서버가 관계·시간·위치·구속·연락 가능 여부 검증한 다음 커밋
- 한국어 어색한 설명체/동일 문구 반복/근거 없는 자백/지나친 욕설을 AI 평가 지표로 관리
- AI 발화 전에 격양·침묵 등 연출을 확정하면 모델과 행동이 분리되므로 서버 응답 후 결정
- 네트워크 지연의 경우 2~3초까지만 자연스러운 대기 동작 후 평범한 정지, 무한 반복 연기 금지
- API 실패는 롤백 가능한 상태로 처리, 성공하지 않은 행동에 수사 자원 차감 금지
- 상업판: 지연·안전 필터·동시접속·악성 질문·비용·녹음 동의·데이터 보관 정책 수립 필요

### 모델 추천 후보(실측 전 잠정)
- 1순위는 한국어 자연스러움·추론과 JSON 유효성을 **실제 평가한 모델**, 특정 이름 고정 금지
- 로컬 테스트: Ollama qwen3:4b(약 2.5GB 모델 다운로드) 또는 qwen3:8b(약 5.2GB) 등 후보
- RTX 2070 SUPER VRAM 8GB 환경에서는 렌더와 로컬 LLM을 동시에 고화질로 실행하기 어려울 수 있음
- 20b 모델은 VRAM 8GB에서 실시간 성능이 떨어질 가능성이 크므로 자동 추천 금지
- 출시 단계는 LLM 응답 품질·비용·운영 안정성 평가 뒤 선택
- Ollama 구조화 출력: https://docs.ollama.com/capabilities/structured-outputs
- OpenAI 구조화 출력: https://developers.openai.com/api/docs/guides/structured-outputs
- Ollama qwen3 모델: https://ollama.com/library/qwen3

### 실제 테스트 매트릭스
- 3인 × 20질문 × 3회 × 서로 다른 증거 공개순서 4조합
- 고정 진실 위반, 타인 비밀 유출, 사실-진술 혼합, 존댓말 일관성, 비현실적 문장, 동일 문구 반복 측정
- 단어 폭력/욕설 등장 빈도는 연출 상황에 따른 제한
- LLM 응답 P50/P95, 타임아웃, schema 오류율, replay 오버헤드 기록
- 보고서 작성 때 유죄 여부 아니라 확보된 증거의 4개 축 판정만 사용

## PC 렌더링 선택
- 현 개발 프로젝트가 Unity 6 URP라면 **HDRP로 즉시 덮어쓰지 말고 별도 브랜치에서 마이그레이션 비용 측정**
- HDRP: 물리 조명, screen-space 반사, volumetric fog, high fidelity shading 등 사실감 유리
- Unity 공식 HDRP 비교 자료: https://docs.unity.com/en-us/engine/6000.6/manual/render-pipelines/choose-a-render-pipeline/feature-comparison
- Unity 6.6 이후 최신 렌더 파이프라인 지원 수명과 유지보수 정책 검토
- VRAM 8GB 기준 1080p/60FPS를 성능 **목표**로만 사용. 실측 보장 아님
- HDRP ray tracing 필수 아님; 품질과 FPS에 따라 SSR, probe, baked GI 대안 선택
- Blender에서 고품질 제작 → FBX/GLB (Khronos glTF Blender I/O: https://github.com/KhronosGroup/glTF-Blender-IO) → Unity 재질·리그 검증

## 모션과 카메라
- Cinemachine Impulse: 사용 강도 제한, 강제 카메라 제어보다 물체 충격과 호흡 중심
  - https://github.com/Unity-Technologies/com.unity.cinemachine/blob/main/com.unity.cinemachine/Documentation~/CinemachineImpulse.md
- Animation Rigging: Multi-Aim / Two-Bone IK / RigBuilder로 손과 눈을 실제 대상에 정합
  - https://docs.unity.cn/Packages/com.unity.animation.rigging%401.3/manual/index.html
- Unity UI Toolkit runtime: 정보 계층·버튼·포커스·한글 폰트; 기존 화면을 가리는 대형 SF 패널 금지
  - https://docs.unity.com/en-us/engine/6000.3/manual/uitoolkits/uielements/uie-support-for-runtime-ui/uie-get-started-with-runtime-ui
- Unity Physics: Rigidbody, collider, fixed timestep, animation contact events
- Timeline: 실제 PlayableDirector authoring으로 카메라/사운드/애니메이션 비트 연결

## 법규·현장 고증 자료
- 형사소송법 피의자신문 관련 권리 및 변호인 참여: https://www.law.go.kr/LSW/lsInfoP.do?efYd=20260701&lsiSeq=281865
- 경찰청 범죄수사규칙 현장 보존/증거물 보존: https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000285818&chrClsCd=010201
- 국가법령정보센터 자료는 법률/절차 자문 대체 아님. 상업 배포 전 시점에 맞는 검토 필요
