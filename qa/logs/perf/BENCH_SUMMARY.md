# Room 302 player-build benchmark (2026-11-21, RTX 2070 SUPER, 1920x1080 windowed, vsync off, 30 s path walk)
Unity Editor open during all runs. Variant switches are runtime flags in TZBenchmark (not yet applied in the scene builder).

| variant | avg FPS | 1% low | 0.1% low | max ms |
|---|---|---|---|---|
| baseline (run 1, 40 s) | 36.7 | 17.7 | 13.7 | 72.8 |
| baseline (run 2) | 55.4 | 28.0 | 24.1 | 41.5 |
| static reflection probes (render once) | 97.4 | 54.1 | 22.1 | 57.6 |
| realtime shadows on flashlight only | 110.9 | 51.6 | 15.1 | 85.4 |
| TAA -> SMAA | 97.9 | 66.3 | 62.4 | 16.0 |
| all three | 176.6 | 105.7 | 56.5 | 36.3 |

Bottlenecks: EveryFrame reflection probes (6 faces x N probes), multiple shadowed point lights, TAA pass.
AI-load run (qwen3:4b CPU concurrently): NOT YET MEASURED.
