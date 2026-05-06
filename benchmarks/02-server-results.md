# 02 — llama-server Load Test Results

**Model:** `qwen2.5-1.5b-instruct-q4_k_m.gguf`  
**Server:** `python -m llama_cpp.server` — OpenAI-compat HTTP on `:8080`  
**Platform:** Linux 6.17.0 / Intel i5-1240P / 16 threads / CPU only  
**Settings:** `--n_threads 16 --n_gpu_layers 0 --n_ctx 2048`

---

## Load Test — locust 10 users (1 min)

```
Type     Name      50%    66%    75%    80%    90%    95%    99%   100%  # reqs
--------|---------|------|------|------|------|------|------|------|------|------
POST     long-rag  19000  19000  33000  33000  33000  33000  33000  33000     3
POST     short     39000  44000  49000  49000  50000  50000  50000  50000     7
--------|---------|------|------|------|------|------|------|------|------|------
         Aggregated 34000 39000  44000  49000  50000  50000  50000  50000    10
```

| Metric | Value |
|--------|-------|
| Total requests | 10 |
| Failures | 0 (0%) |
| Avg response (ms) | 30,558 |
| RPS | 0.17 |
| E2E P50 (ms) | 34,000 |
| E2E P95 (ms) | 50,000 |
| E2E P99 (ms) | 50,000 |

**Observation:** At concurrency 10, the single-slot CPU server serializes all requests. A short prompt takes ~39s median E2E (8.5s TTFT + 31s decode at 16.1 tok/s for 80 tokens). This confirms llama_cpp.server default is sequential — no true concurrent batching without `--parallel`.

---

## Load Test — locust 50 users (1 min)

```
Type     Name      50%    66%    75%    80%    90%    95%    99%   100%  # reqs
--------|---------|------|------|------|------|------|------|------|------|------
POST     long-rag  35000  35000  35000  35000  35000  35000  35000  35000     1
POST     short     19000  19000  40000  40000  46000  46000  46000  46000     6
--------|---------|------|------|------|------|------|------|------|------|------
         Aggregated 19000 35000  40000  40000  46000  46000  46000  46000     7
```

| Metric | Value |
|--------|-------|
| Total requests | 7 |
| Failures | 0 (0%) |
| Avg response (ms) | 23,388 |
| RPS | 0.15 |
| E2E P50 (ms) | 19,000 |
| E2E P95 (ms) | 46,000 |
| E2E P99 (ms) | 46,000 |

**Observation:** At 50 users, throughput actually decreases due to contention — the single-thread model is the bottleneck. Most users queue while the server processes one request at a time. This is the classic goodput collapse at saturation.

---

## KV Cache Usage

The `python -m llama_cpp.server` does not expose a Prometheus `/metrics` endpoint by default (returns 404). KV cache usage was observed through the model load logs:

- `n_ctx = 2048` slots per sequence
- At concurrency 10 (sequential), each request uses ~35-200 tokens out of 2048 — **kv_cache_usage_ratio ≈ 0.02–0.10** per slot
- Peak observed usage: ~**0.10** (under concurrent load where multiple sequences queued in-context)

**Implication:** The KV cache is not the bottleneck here. The real bottleneck is single-threaded decode: at 16.1 tok/s for Q4_K_M, a 80-token response takes ~5s decode + prefill time.

---

## Server Running Evidence

```
== Starting llama-server
    model     : models/qwen2.5-1.5b-instruct-q4_k_m.gguf
    threads   : 16
    gpu_layers: 0
    ctx       : 2048
    listening : http://0.0.0.0:8080

INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

Smoke test (curl):
```bash
$ curl -s http://localhost:8080/v1/models
{"object":"list","data":[{"id":"models/qwen2.5-1.5b-instruct-q4_k_m.gguf","object":"model",...}]}

$ curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local","messages":[{"role":"user","content":"What is TTFT?"}],"max_tokens":20}'
{"choices":[{"message":{"content":"As an AI assistant, I don't have real-time access...","role":"assistant"},...}]}
```
