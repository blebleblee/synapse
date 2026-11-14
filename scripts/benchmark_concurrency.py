#!/usr/bin/env python3
"""
Endpoint Concurrency Benchmark Suite
Empirically tests saturation limits and safe concurrency headroom
for configured AI API gateways without guesswork.
"""

import os
import sys
import time
import threading
from pathlib import Path
from typing import List, Dict, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, load_env_file
load_env_file()

PROMPT = "Write a concise, 80-word technical explanation of write-ahead logging (WAL) in database storage engines."

def run_concurrency_test(name: str, base_url: str, api_key: str, model: str, concurrency_levels: List[int]) -> List[Dict[str, Any]]:
    print(f"\n{'='*70}")
    print(f" 🚀 BENCHMARKING ENDPOINT: {name}")
    print(f" URL:   {base_url}")
    print(f" Model: {model}")
    print(f"{'='*70}")

    results = []

    for c in concurrency_levels:
        print(f"\n[*] Testing Concurrency Level: {c} Simultaneous Stream(s)...", flush=True)
        provider = AnthropicProvider(base_url=base_url, api_key=api_key, model=model)
        
        batch_results = []
        threads = []
        barrier = threading.Barrier(c)

        def worker(w_id):
            barrier.wait()
            t0 = time.time()
            try:
                resp = provider.generate(f"{PROMPT} [Worker ID: {w_id}]", max_tokens=150)
                elapsed = time.time() - t0
                words = len(resp.split())
                batch_results.append({
                    "worker": w_id,
                    "success": True,
                    "elapsed": elapsed,
                    "words": words,
                    "error": None
                })
            except Exception as e:
                elapsed = time.time() - t0
                batch_results.append({
                    "worker": w_id,
                    "success": False,
                    "elapsed": elapsed,
                    "words": 0,
                    "error": str(e)
                })

        batch_t0 = time.time()
        for i in range(1, c + 1):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        batch_elapsed = time.time() - batch_t0
        success_count = sum(1 for r in batch_results if r["success"])
        success_rate = (success_count / c) * 100
        latencies = [r["elapsed"] for r in batch_results if r["success"]]
        avg_lat = sum(latencies) / len(latencies) if latencies else 0
        min_lat = min(latencies) if latencies else 0
        max_lat = max(latencies) if latencies else 0

        errors = [r["error"] for r in batch_results if not r["success"]]
        unique_errors = list(set(errors))

        status_badge = "🟢 PERFECT" if success_rate == 100 else "🟡 PARTIAL" if success_rate > 0 else "🔴 SATURATED / BLOCKED"
        print(f"    Status:       {status_badge} ({success_count}/{c} successful - {success_rate:.0f}%)")
        print(f"    Batch Time:   {batch_elapsed:.2f}s (Avg per stream: {avg_lat:.2f}s, Min: {min_lat:.2f}s, Max: {max_lat:.2f}s)")
        if unique_errors:
            print(f"    Error Signature: {unique_errors[0][:100]}")

        results.append({
            "concurrency": c,
            "success_rate": success_rate,
            "success_count": success_count,
            "batch_time": batch_elapsed,
            "avg_latency": avg_lat,
            "max_latency": max_lat,
            "errors": unique_errors
        })

        # Polite delay between concurrency tiers to allow proxy connection drains
        time.sleep(3)

    return results

def main():
    vnaipro_key = os.environ.get("VNAIPRO_API_KEY")
    vnaipro_url = os.environ.get("VNAIPRO_BASE_URL", "https://apikey.vnaipro.app")
    
    aiapiflow_key = os.environ.get("ANTHROPIC_API_KEY")
    aiapiflow_url = os.environ.get("ANTHROPIC_BASE_URL", "https://aiapiflow.com")

    all_benchmarks = {}

    # 1. Benchmark VNAIPRO (testing 1, 2, 3, 4, 5, 6 streams)
    if vnaipro_key:
        all_benchmarks["VNAIPRO"] = run_concurrency_test(
            name="VNAIPRO Gateway",
            base_url=vnaipro_url,
            api_key=vnaipro_key,
            model="claude-sonnet-5",
            concurrency_levels=[1, 2, 3, 4, 5, 6]
        )

    # 2. Benchmark AIAPIFLOW (testing 1, 2, 3, 4 streams)
    if aiapiflow_key:
        all_benchmarks["AIAPIFLOW"] = run_concurrency_test(
            name="AIAPIFLOW Gateway",
            base_url=aiapiflow_url,
            api_key=aiapiflow_key,
            model="claude-sonnet-5",
            concurrency_levels=[1, 2, 3, 4]
        )

    # Print Executive Synthesis Table
    print(f"\n{'='*70}")
    print(" 📊 EXECUTIVE SYNTHESIS: CONCURRENCY CAPACITY REPORT")
    print(f"{'='*70}")
    print(f"{'Gateway':<12} | {'Streams':<8} | {'Success':<8} | {'Avg Lat':<10} | {'Max Lat':<10} | {'Verdict'}")
    print(f"{'-'*12}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*15}")

    recommended_pool = {}

    for name, bench_list in all_benchmarks.items():
        max_100_stream = 0
        for b in bench_list:
            c = b["concurrency"]
            sr = f"{b['success_rate']:.0f}%"
            avg = f"{b['avg_latency']:.2f}s"
            mx = f"{b['max_latency']:.2f}s"
            verdict = "✅ Supported" if b["success_rate"] == 100 else "❌ Rate-Limited"
            if b["success_rate"] == 100 and c > max_100_stream:
                max_100_stream = c
            print(f"{name:<12} | {c:<8} | {sr:<8} | {avg:<10} | {mx:<10} | {verdict}")
        recommended_pool[name] = max_100_stream

    print(f"{'='*70}")
    print(" 🎯 RECOMMENDED OPTIMAL WORKER ALLOCATION:")
    total_safe_workers = sum(recommended_pool.values())
    for name, safe_c in recommended_pool.items():
        print(f"   • {name:<12}: {safe_c} concurrent workers")
    print(f"   ----------------------------------------")
    print(f"   Total Parallel Concurrency: {total_safe_workers} simultaneous streams")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
