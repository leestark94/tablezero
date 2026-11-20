# BUG-0001 — 개발 PC GPU 드라이버 리셋 (nvlddmkm Event 153)

- 발생: 2026-11-21 03:33~03:48, Ollama CUDA 추론 중 반복 (Unity 실행 여부와 무관하게 재현)
- 증상: llama-server 0xc0000409 종료, Unity Editor D3D12 장치 손실로 크래시, 4B 모델 GPU 속도가 비정상적으로 느림(4.9 tok/s)
- 환경: RTX 2070 SUPER 8GB, 드라이버 610.88, Windows 11
- 판단: 하드웨어/드라이버 수준 문제. 시스템 설정(TDR, 드라이버) 변경은 사용자 승인 사항이라 손대지 않음
- 우회: 개발 서버는 CPU 추론(TABLEZERO_OLLAMA_NUM_GPU=0)으로 고정. CPU 측정: qwen3:4b 14.8 tok/s, gemma3:4b 14.8 tok/s, qwen3:8b 7.3 tok/s
- 사용자 권장 조치: NVIDIA 드라이버 클린 재설치(DDU), GPU 오버클럭/언더볼트 해제 여부 확인, 이벤트 뷰어 시스템 로그 nvlddmkm 확인
