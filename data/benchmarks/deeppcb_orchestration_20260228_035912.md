# DeepPCB Benchmark Summary (2026-02-28T03:59:12.544215+00:00)

- Total cases: 6
- Success cases: 6
- Failed cases: 0
- Avg latency (sec): 54.43
- Model usage: {'gemini-2.5-flash': 6}

## Metrics (IoU >= 0.33)

- Localization P/R/F1: 0.143 / 0.026 / 0.043
- Class-aware P/R/F1: 0.000 / 0.000 / 0.000

## Cases

- 20085204 [open]: model=gemini-2.5-flash loc(tp/fp/fn)=0/1/7 cls(tp/fp/fn)=0/1/7 latency=53.97s
- 13000046 [short]: model=gemini-2.5-flash loc(tp/fp/fn)=0/2/7 cls(tp/fp/fn)=0/2/7 latency=56.65s
- 44000072 [mousebite]: model=gemini-2.5-flash loc(tp/fp/fn)=0/1/7 cls(tp/fp/fn)=0/1/7 latency=51.11s
- 50600046 [spur]: model=gemini-2.5-flash loc(tp/fp/fn)=0/1/6 cls(tp/fp/fn)=0/1/6 latency=48.93s
- 13000116 [copper]: model=gemini-2.5-flash loc(tp/fp/fn)=1/0/4 cls(tp/fp/fn)=0/1/5 latency=50.91s
- 00041002 [pin-hole]: model=gemini-2.5-flash loc(tp/fp/fn)=0/1/7 cls(tp/fp/fn)=0/1/7 latency=65.02s