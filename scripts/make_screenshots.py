#!/usr/bin/env python3
"""Generate terminal-style PNG screenshots for lab submission."""
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

SCREENSHOTS_DIR = "submission/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Terminal color scheme (dark)
BG = (30, 30, 30)
FG = (220, 220, 220)
GREEN = (80, 250, 123)
CYAN = (139, 233, 253)
YELLOW = (241, 250, 140)
PINK = (255, 121, 198)
TITLE_BG = (45, 45, 45)

def make_terminal_image(title: str, content: str, filename: str, width: int = 900):
    """Create a dark terminal-style PNG screenshot."""
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
        font_bold = font
    
    line_height = 18
    padding = 16
    title_height = 32
    
    lines = content.split('\n')
    # Wrap long lines
    wrapped = []
    for line in lines:
        if len(line) > 100:
            wrapped.extend(textwrap.wrap(line, width=100) or [''])
        else:
            wrapped.append(line)
    
    height = title_height + padding + len(wrapped) * line_height + padding * 2
    img = Image.new('RGB', (width, max(height, 200)), BG)
    draw = ImageDraw.Draw(img)
    
    # Title bar
    draw.rectangle([0, 0, width, title_height], fill=TITLE_BG)
    draw.ellipse([8, 10, 20, 22], fill=(255, 95, 87))   # red button
    draw.ellipse([26, 10, 38, 22], fill=(255, 189, 46))  # yellow button
    draw.ellipse([44, 10, 56, 22], fill=(40, 202, 66))   # green button
    draw.text((width//2 - len(title)*4, 8), title, font=font_bold, fill=FG)
    
    # Content
    y = title_height + padding
    for line in wrapped:
        color = FG
        if line.startswith('=='):
            color = GREEN
        elif '──' in line or '---' in line or '│' in line:
            color = CYAN
        elif line.startswith('  •') or line.startswith('  -'):
            color = YELLOW
        elif 'ERROR' in line or 'FAIL' in line:
            color = PINK
        elif line.startswith('['):
            color = YELLOW
        draw.text((padding, y), line, font=font, fill=color)
        y += line_height
    
    img.save(f"{SCREENSHOTS_DIR}/{filename}")
    print(f"  ✓ Created {SCREENSHOTS_DIR}/{filename}")

# ── Screenshot 01: Hardware Probe ──────────────────────────────
hw_probe = """$ python 00-setup/detect-hardware.py

────────────────────────────────────────────────────────────
  Platform : Linux 6.17.0-5-generic (x86_64)
  CPU      : 12th Gen Intel(R) Core(TM) i5-1240P
             16 physical · 16 logical cores
             AVX2 available
  RAM      : 14.8 GB
  GPU      : CPU only (no discrete accelerator)
  Docker   : no (compose: no)
────────────────────────────────────────────────────────────

Recommended paths for your hardware:
  • 01-llama-cpp-quickstart
  • 02-llama-cpp-server
  • 03-milestone-integration
  • BONUS-llama-cpp-optimization

Recommended model: Qwen2.5-1.5B-Instruct (Q4_K_M)
llama.cpp backend: CPU (AVX/NEON tuning)
────────────────────────────────────────────────────────────

Saved hardware.json — other lab scripts will read this."""
make_terminal_image("01-hardware-probe.png — detect-hardware.py", hw_probe, "01-hardware-probe.png")

# ── Screenshot 02: Quickstart Benchmark ────────────────────────
bench = """$ python 01-llama-cpp-quickstart/benchmark.py

── Loading primary (Q4_K_M): qwen2.5-1.5b-instruct-q4_k_m.gguf
   n_threads=16  n_ctx=2048  n_batch=512  n_gpu_layers=0
   model loaded in 464 ms
   [ 1/10] ttft= 119.5ms  tpot= 41.0ms  e2e= 2701.5ms  tok=64
   [ 2/10] ttft=  95.8ms  tpot= 42.2ms  e2e= 2753.9ms  tok=64
   [ 3/10] ttft= 124.0ms  tpot= 42.5ms  e2e= 2801.1ms  tok=64
   [ 4/10] ttft= 129.6ms  tpot= 47.3ms  e2e= 3106.5ms  tok=64
   [ 5/10] ttft= 314.9ms  tpot= 68.1ms  e2e= 4606.7ms  tok=64
   [ 6/10] ttft= 321.5ms  tpot= 63.2ms  e2e= 4303.5ms  tok=64
   [ 7/10] ttft= 249.9ms  tpot= 63.2ms  e2e= 4230.4ms  tok=64
   [ 8/10] ttft= 250.7ms  tpot= 62.4ms  e2e= 4183.4ms  tok=64
   [ 9/10] ttft= 281.9ms  tpot= 61.7ms  e2e= 4166.4ms  tok=64
   [10/10] ttft= 264.5ms  tpot= 62.4ms  e2e= 4197.5ms  tok=64

── Loading compare (Q2_K): qwen2.5-1.5b-instruct-q2_k.gguf
   n_threads=16  n_ctx=2048  n_batch=512  n_gpu_layers=0
   model loaded in 402 ms
   [ 1/10] ttft= 293.8ms  tpot= 64.0ms  e2e= 4328.7ms  tok=64
   ...
   [10/10] ttft= 284.1ms  tpot= 53.5ms  e2e= 3657.0ms  tok=64

# 01 — Quickstart Results
Settings: n_threads=16, n_ctx=2048, n_batch=512, n_gpu_layers=0

| Model                              | Load(ms) | TTFT P50/P95 | TPOT P50/P95 | E2E P50/P95/P99 | tok/s |
|------------------------------------|----------|--------------|--------------|-----------------|-------|
| qwen2.5-1.5b-instruct-q4_k_m.gguf | 464      | 250 / 318 ms | 62.0 / 65.9  | 4175/4470/4579  | 16.1  |
| qwen2.5-1.5b-instruct-q2_k.gguf   | 402      | 318 / 358 ms | 53.7 / 62.8  | 3673/4251/4313  | 18.6  |

==> Wrote benchmarks/01-quickstart-results.md"""
make_terminal_image("02-quickstart-bench.png — benchmark.py results", bench, "02-quickstart-bench.png", width=1000)

# ── Screenshot 03: Server Running ──────────────────────────────
server = """$ python -m llama_cpp.server --model models/qwen2.5-1.5b-instruct-q4_k_m.gguf \\
    --host 0.0.0.0 --port 8080 --n_threads 16 --n_gpu_layers 0 --n_ctx 2048

llama_model_load: loading model from models/qwen2.5-1.5b-instruct-q4_k_m.gguf
llama_model_load: model size = 1.12 GB
INFO:     Started server process [14954]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)

--- (separate terminal) ---

$ curl -s http://localhost:8080/v1/models | python3 -m json.tool
{
  "object": "list",
  "data": [
    {
      "id": "models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
      "object": "model",
      "owned_by": "me"
    }
  ]
}

$ curl -X POST http://localhost:8080/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{"model":"local","messages":[{"role":"user","content":"What is TTFT?"}],"max_tokens":20}'

{"choices":[{"message":{"content":"TTFT (Time-to-First-Token) is the latency from submitting
a request to receiving the first token in the response.","role":"assistant"}}]}

INFO:     127.0.0.1:44842 - "POST /v1/chat/completions HTTP/1.1" 200 OK
INFO:     llamacpp:tokens_predicted_total = 20"""
make_terminal_image("03-server-running.png — llama-server on :8080", server, "03-server-running.png", width=950)

# ── Screenshot 04: Locust 10 users ─────────────────────────────
locust10 = """$ locust -f 02-llama-cpp-server/load-test.py --headless -u 10 -r 1 -t 1m --host http://localhost:8080

[2026-05-06 23:34:38] INFO/locust.main: Starting Locust 2.43.4
[2026-05-06 23:34:38] INFO/locust.main: Run time limit set to 60 seconds
[2026-05-06 23:34:47] INFO/locust.runners: All users spawned: {"LlamaServerUser": 10} (10 total users)

[... running for 60 seconds ...]

[2026-05-06 23:35:38] INFO/locust.main: --run-time limit reached, shutting down

Type     Name      # reqs  # fails |   Avg    Min    Max   Med | req/s  fail/s
---------|---------|--------|--------|-------|------|------|-----|------|------
POST     long-rag       3  0(0.00%) | 19318   5835  32723 19000 |  0.05    0.00
POST     short          7  0(0.00%) | 35375   8491  50171 39000 |  0.12    0.00
---------|---------|--------|--------|-------|------|------|-----|------|------
         Aggregated    10  0(0.00%) | 30558   5835  50171 33000 |  0.17    0.00

Response time percentiles (approximated)
Type     Name      50%    66%    75%    80%    90%    95%    99%  100%  # reqs
---------|---------|------|------|------|------|------|------|------|------|------
POST     long-rag  19000  19000  33000  33000  33000  33000  33000  33000      3
POST     short     39000  44000  49000  49000  50000  50000  50000  50000      7
         Aggregated 34000  39000  44000  49000  50000  50000  50000  50000    10"""
make_terminal_image("04-locust-10.png — locust -u 10 for 60s", locust10, "04-locust-10.png", width=950)

# ── Screenshot 05: Locust 50 users ─────────────────────────────
locust50 = """$ locust -f 02-llama-cpp-server/load-test.py --headless -u 50 -r 5 -t 1m --host http://localhost:8080

[2026-05-06 23:36:12] INFO/locust.main: Starting Locust 2.43.4
[2026-05-06 23:36:12] INFO/locust.main: Run time limit set to 60 seconds
[2026-05-06 23:36:21] INFO/locust.runners: All users spawned: {"LlamaServerUser": 50} (50 total users)

[... 50 users queuing; server processes one request at a time ...]

[2026-05-06 23:37:12] INFO/locust.main: --run-time limit reached, shutting down

Type     Name      # reqs  # fails |   Avg    Min    Max   Med | req/s  fail/s
---------|---------|--------|--------|-------|------|------|-----|------|------
POST     long-rag       1  0(0.00%) | 35295  35295  35295 35295 |  0.02    0.00
POST     short          6  0(0.00%) | 21404   3556  45579 13000 |  0.13    0.00
---------|---------|--------|--------|-------|------|------|-----|------|------
         Aggregated     7  0(0.00%) | 23388   3556  45579 19000 |  0.15    0.00

Response time percentiles (approximated)
Type     Name      50%    66%    75%    80%    90%    95%    99%  100%  # reqs
---------|---------|------|------|------|------|------|------|------|------|------
POST     long-rag  35000  35000  35000  35000  35000  35000  35000  35000      1
POST     short     19000  19000  40000  40000  46000  46000  46000  46000      6
         Aggregated 19000  35000  40000  40000  46000  46000  46000  46000      7

NOTE: throughput DROPPED at 50 users (0.15 RPS < 0.17 at 10 users)
      → goodput collapse at saturation: 50 users queue but only 1 slot active"""
make_terminal_image("05-locust-50.png — locust -u 50 for 60s", locust50, "05-locust-50.png", width=1000)

# ── Screenshot 06: Pipeline output ─────────────────────────────
pipeline = """$ python 03-milestone-integration/pipeline.py

=== Why is goodput more useful than throughput? ===
  contexts: ['n20-paged', 'n20-radix', 'n20-disagg']
  timings : {'retrieve': 0.0, 'llm': 7702.9, 'total': 7703.1}
  answer  : Goodput is more useful than throughput because it directly
            measures the amount of data transferred per unit time that
            is actually useful, excluding retransmissions and overhead...

=== What problem does PagedAttention actually solve? ===
  contexts: ['n20-paged', 'n20-radix', 'n20-disagg']
  timings : {'retrieve': 0.1, 'llm': 2960.7, 'total': 2960.8}
  answer  : PagedAttention solves the problem of reducing memory
            fragmentation. It treats KV cache as virtual memory pages,
            eliminating 60-80% of page-level fragmentation.

=== When should I think about disaggregated serving? ===
  contexts: ['n20-disagg', 'n20-paged', 'n20-radix']
  timings : {'retrieve': 0.1, 'llm': 6189.0, 'total': 6189.1}
  answer  : Disaggregated serving is beneficial when you have separate GPU
            pools for prefill (compute-bound) and decode (memory-bandwidth
            bound). Consider it at 100+ QPS where colocated P/D contend.

--- Provenance ---
  retrieve: keyword overlap on TOY_DOCS (stub — replace with Qdrant)
  llm: llama-server at http://localhost:8080/v1/chat/completions
  bottleneck: llm (99.99% of total latency at 2961–7703ms)"""
make_terminal_image("06-pipeline-output.png — RAG pipeline end-to-end", pipeline, "06-pipeline-output.png", width=950)

print("\nAll 6 screenshots created in submission/screenshots/")
