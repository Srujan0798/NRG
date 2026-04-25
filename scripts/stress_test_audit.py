#!/usr/bin/env python3
"""ADR-006 concurrent stress test - writes to file to avoid stdin issue."""
import sys
import os
import time
import threading
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audit import ImmutableAuditLog, AuditEvent

BASE_PATH = ".audit_stress_test"

def verify_chain_events(events):
    """Verify hash chaining for a list of events."""
    import hmac
    import hashlib
    prev_hash = "0" * 64
    for i, evt in enumerate(events):
        data = json.loads(evt) if isinstance(evt, str) else evt
        stored_hash = data.get("hash", "")
        expected_hash = hmac.new(
            b"nrg-audit-chain-dev-key",
            (prev_hash + json.dumps(data, sort_keys=True, default=str)).encode(),
            hashlib.sha256
        ).hexdigest()
        if stored_hash != expected_hash:
            return False, i, stored_hash[:16], expected_hash[:16]
        prev_hash = stored_hash
    return True, 0, "", ""

def worker_events(worker_id, count, results, idx):
    """Each thread writes N events."""
    ImmutableAuditLog._reset()
    log = ImmutableAuditLog(storage_path=BASE_PATH)
    for i in range(count):
        event = AuditEvent(
            event_type="test_concurrent",
            user_id=f"thread_{worker_id}",
            query=f"concurrent test event {i}"
        )
        try:
            log.append(event)
        except Exception as e:
            results[idx] = (0, 1, str(e))
            return
    results[idx] = (count, 0, "")

def run_stress_test(num_threads=8, events_per_thread=25):
    """Run concurrent stress test using threads (file locking works across threads)."""
    import shutil
    if os.path.exists(BASE_PATH):
        shutil.rmtree(BASE_PATH)

    ImmutableAuditLog._reset()
    log = ImmutableAuditLog(storage_path=BASE_PATH)
    initial_count = log.event_count
    print(f"Initial: {initial_count} events")

    results = [None] * num_threads
    threads = []
    start = time.time()

    for t in range(num_threads):
        th = threading.Thread(target=worker_events, args=(t, events_per_thread, results, t))
        threads.append(th)
        th.start()

    for th in threads:
        th.join()

    elapsed = time.time() - start
    total_success = sum(r[0] for r in results if r)
    total_errors = sum(r[1] for r in results if r)

    ImmutableAuditLog._reset()
    log2 = ImmutableAuditLog(storage_path=BASE_PATH)
    final_count = log2.event_count
    expected_new = num_threads * events_per_thread
    actual_new = final_count - initial_count

    print(f"\nResults: {num_threads} threads x {events_per_thread} events")
    print(f"  Success: {total_success}, Errors: {total_errors}")
    print(f"  Expected new: {expected_new}, Actual new: {actual_new}")
    print(f"  Elapsed: {elapsed:.2f}s ({total_success/elapsed:.1f} events/sec)")

    # Verify first 100 events chain correctly
    chain_file = os.path.join(BASE_PATH, "chain.jsonl")
    events = []
    with open(chain_file) as f:
        for i, line in enumerate(f):
            if i < 100:
                events.append(line.strip())
            else:
                break

    valid, bad_idx, stored, expected = verify_chain_events(events)
    print(f"  Chain integrity (first 100): {'PASS' if valid else f'FAIL at event {bad_idx} (stored={stored}, expected={expected})'}")

    return total_success, total_errors, actual_new == expected_new and valid

if __name__ == "__main__":
    print("=== ADR-006 fcntl.flock Stress Test ===\n")
    success, errors, passed = run_stress_test(num_threads=8, events_per_thread=25)
    print(f"\n{'PASS' if passed else 'FAIL'}")
    sys.exit(0 if passed else 1)
