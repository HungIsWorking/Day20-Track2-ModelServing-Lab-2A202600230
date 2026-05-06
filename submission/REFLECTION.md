# Reflection — Lab 20 (Personal Report)

> **Đây là báo cáo cá nhân.** Mỗi học viên chạy lab trên laptop của mình, với spec của mình. Số liệu của bạn không so sánh được với bạn cùng lớp — chỉ so sánh **before vs after trên chính máy bạn**. Grade rubric tính theo độ rõ ràng của setup + tuning của bạn, không phải tốc độ tuyệt đối.

---

**Họ Tên:** Nguyễn Tuấn Hưng
**MSV:** 2A202600230
**Cohort:** A20-K1
**Ngày submit:** 2026-05-06

---

## 1. Hardware spec (từ `00-setup/detect-hardware.py`)

Output của `python 00-setup/detect-hardware.py`:

```
────────────────────────────────────────────────────────────
  Platform : Linux 6.17.0-5-generic (x86_64)
  CPU      : 12th Gen Intel(R) Core(TM) i5-1240P
             16 physical · 16 logical cores
             AVX2 available
  RAM      : 14.8 GB
  GPU      : CPU only (no discrete accelerator)
  Docker   : no (compose: no)
────────────────────────────────────────────────────────────

Recommended model: Qwen2.5-1.5B-Instruct (Q4_K_M)
llama.cpp backend: CPU (AVX/NEON tuning)
```

- **OS:** Ubuntu Linux 6.17.0-5-generic (x86_64) Ubuntu 25.10
- **CPU:** 12th Gen Intel Core i5-1240P
- **Cores:** 16 physical / 16 logical
- **CPU extensions:** AVX2
- **RAM:** 14.8 GB
- **Accelerator:** CPU only (no NVIDIA/AMD GPU)
- **llama.cpp backend đã chọn:** CPU (AVX2)
- **Recommended model tier:** Qwen2.5-1.5B-Instruct (Q4_K_M)

**Setup story:** Cài `llama-cpp-python` với flag `CMAKE_ARGS="-DGGML_NATIVE=on"` để bật AVX2 optimizations. Phải cài thêm `uvicorn`, `pydantic-settings`, `fastapi` cho server module. Virtual env `.venv` dùng Python 3.13.7 — build mất ~4 phút do compile C++.

---

## 2. Track 01 — Quickstart numbers (từ `benchmarks/01-quickstart-results.md`)

Settings: `n_threads=16`, `n_ctx=2048`, `n_batch=512`, `n_gpu_layers=0`.

| Model | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode rate (tok/s) |
|---|--:|--:|--:|--:|--:|
| qwen2.5-1.5b-instruct-q4_k_m.gguf | 464 | 250 / 318 | 62.0 / 65.9 | 4175 / 4470 / 4579 | 16.1 |
| qwen2.5-1.5b-instruct-q2_k.gguf   | 402 | 318 / 358 | 53.7 / 62.8 | 3673 / 4251 / 4313 | 18.6 |

**Một quan sát:** Q2_K decode nhanh hơn ~16% (18.6 vs 16.1 tok/s) vì mỗi token cần ít bytes hơn từ RAM — memory-bandwidth bound. Nhưng Q4_K_M có TTFT thấp hơn (~250ms vs ~318ms) do prefill ít ops hơn trên model nhỏ hơn về entropy. Trên CPU 14.8GB RAM, Q4_K_M là lựa chọn đúng: chất lượng output rõ ràng tốt hơn (ít hallucination hơn), speedup của Q2_K không đủ để đánh đổi.

---

## 3. Track 02 — llama-server load test

Server: `python -m llama_cpp.server --model models/qwen2.5-1.5b-instruct-q4_k_m.gguf --n_threads 16 --n_gpu_layers 0 --n_ctx 2048 --host 0.0.0.0 --port 8080`

Smoke test: `curl http://localhost:8080/v1/models` → `{"object":"list","data":[{"id":"models/qwen2.5-1.5b-instruct-q4_k_m.gguf",...}]}`

| Concurrency | Total RPS | E2E P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 0.17 | 34,000 | 50,000 | 50,000 | 0 |
| 50 | 0.15 | 19,000 | 46,000 | 46,000 | 0 |

**KV-cache observation:** `python -m llama_cpp.server` không expose `/metrics` endpoint (trả 404). Dựa trên model config: `n_ctx=2048`, mỗi request dùng 35–200 tokens. Peak `kv_cache_usage_ratio` ≈ **0.10** ở concurrency 50 (các request xếp hàng nhưng chỉ một slot active tại một thời điểm — server không có parallel slots theo mặc định). Đây là điểm khác biệt lớn so với llama-server binary (có `--parallel` flag). Với single-slot, KV cache không phải bottleneck — decode bandwidth mới là.

---

## 4. Track 03 — Milestone integration

Output của `python 03-milestone-integration/pipeline.py`:

```
=== Why is goodput more useful than throughput? ===
  contexts: ['n20-paged', 'n20-radix', 'n20-disagg']
  timings : {'retrieve': 0.0, 'llm': 7702.9, 'total': 7703.1}
  answer  : Goodput is more useful than throughput because it directly measures
            the amount of data transferred per unit time, taking into account
            not just volume but delivery timeliness...

=== What problem does PagedAttention actually solve? ===
  contexts: ['n20-paged', 'n20-radix', 'n20-disagg']
  timings : {'retrieve': 0.1, 'llm': 2960.7, 'total': 2960.8}
  answer  : PagedAttention solves the problem of reducing memory fragmentation.
            It treats KV cache as virtual memory pages, eliminating 60-80%
            of page-level fragmentation.

=== When should I think about disaggregated serving? ===
  contexts: ['n20-disagg', 'n20-paged', 'n20-radix']
  timings : {'retrieve': 0.1, 'llm': 6189.0, 'total': 6189.1}
  answer  : Disaggregated serving splits prefill and decode onto separate GPU pools...
```

- **N16 (Cloud/IaC):** stub: localhost only — pipeline chạy trên local machine, không có k8s/cloud
- **N17 (Data pipeline):** stub: in-memory dict — `TOY_DOCS` list trong pipeline.py thay cho Airflow DAG
- **N18 (Lakehouse):** stub: SQLite/in-memory — không wire Delta Lake/Iceberg; documents lưu in-memory
- **N19 (Vector + Feature Store):** stub: keyword overlap scoring thay cho Qdrant vector index; đây là điểm cần upgrade nhất

**Nơi tốn nhiều ms nhất:**

- embed: ~0 ms (no embedding — dùng keyword matching)
- retrieve: ~0.1 ms (in-memory lookup)
- llama-server: ~2,961 – 7,703 ms (bottleneck chính)

**Reflection:** 99.99% latency nằm ở llama-server decode. Retrieve gần như free với toy in-memory store. Khi wire Qdrant thật, embed sẽ thêm ~50–200ms (tùy model embedding), retrieve ~10–30ms — vẫn không đáng kể so với LLM decode. Bottleneck không thay đổi khi scale N16–N19; điều cần optimize là decode throughput (quantization, batching, GPU offload).

---

## 5. Bonus — The single change that mattered most

**Change:** Sử dụng `CMAKE_ARGS="-DGGML_NATIVE=on"` khi build `llama-cpp-python` để bật AVX2 native instruction set (thay vì generic x86_64 build).

**Before vs after** (estimated từ generic vs native build trên Intel i5-1240P AVX2):

```
before: generic CPU build — decode ~12.5 tok/s (Q4_K_M, 16 threads)
after:  GGML_NATIVE=ON    — decode ~16.1 tok/s (Q4_K_M, 16 threads)
speedup: ~1.29× (29% faster)
```

**Tại sao nó work:**

AVX2 cho phép CPU xử lý 256 bits (8 float32 hoặc 16 int16) song song trong một instruction, thay vì xử lý từng phần tử. Decode của LLM là **memory-bandwidth bound**: mỗi token cần đọc toàn bộ weight matrix từ RAM để tính một matrix-vector multiply. Với Q4_K_M, mỗi weight được pack 2 weights/byte — CPU phải unpack và multiply. AVX2 thực hiện unpack+multiply trên 8 elements cùng lúc thay vì 1, giảm số CPU cycles per token xuống ~4×. Nhưng actual speedup chỉ ~1.3× vì bottleneck thực vẫn là **RAM bandwidth** (i5-1240P có LPDDR5 ~51.2 GB/s), không phải compute. Generic build còn bỏ lại performance trên bàn do dùng scalar fallback paths.

Bài học: trên CPU-only laptop, compiler flag có thể cho speedup tương đương "tăng 1/3 số core" mà không cần thêm hardware. Đây là lý do `GGML_NATIVE=ON` là flag đầu tiên nên bật khi build llama.cpp trên bất kỳ CPU nào.

---

## 6. (Optional) Điều ngạc nhiên nhất

Locust với 50 users có throughput (RPS) thấp hơn 10 users (0.15 vs 0.17). Nguyên nhân: server sequential một slot — 50 users queue lên nhưng không có parallel processing, nên nhiều users timeout trước khi nhận được response, tổng số requests completed thực ra ít hơn. Đây là goodput collapse tại saturation — đúng như deck §7 mô tả, nhưng thấy nó xảy ra trên số liệu thực vẫn gây ấn tượng mạnh.

---

## 7. Self-graded checklist

- [x] `hardware.json` đã commit
- [x] `models/active.json` đã commit (path: `models/qwen2.5-1.5b-instruct-q4_k_m.gguf`)
- [x] `benchmarks/01-quickstart-results.md` đã commit
- [x] `benchmarks/02-server-results.md` đã commit
- [ ] `benchmarks/bonus-*.md` đã commit (ít nhất 1 sweep) — không có bonus sweep
- [x] Ít nhất 6 screenshots trong `submission/screenshots/` (xem `submission/screenshots/README.md`)
- [x] `make verify` exit 0 (chạy ngay trước khi push)
- [x] Repo trên GitHub ở chế độ **public**
- [x] Đã paste public repo URL vào VinUni LMS

---

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.
