import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Setup env
load_dotenv('.env.production', override=True)
os.environ['DATABASE_URL'] = 'postgresql://nrg_user:nrg_password@localhost:5432/nrg_research'
sys.path.insert(0, str(Path(os.getcwd())))

from src.orchestration.graph import NRGWorkflow

def run_benchmark():
    wf = NRGWorkflow()
    query = "Find robotics researchers in Gujarat"
    
    print(f"Benchmarking query: '{query}'")
    
    # First run (Cache MISS)
    start = time.time()
    result1 = wf.run(query, user_tier=1)
    end = time.time()
    first_run_ms = (end - start) * 1000
    print(f"First run (MISS): {first_run_ms:.2f}ms")
    
    # Second run (Cache HIT)
    start = time.time()
    result2 = wf.run(query, user_tier=1)
    end = time.time()
    second_run_ms = (end - start) * 1000
    print(f"Second run (HIT): {second_run_ms:.2f}ms")
    
    # Verification
    assert result1['synthesized_response'] == result2['synthesized_response']
    print(f"Speedup: {first_run_ms / second_run_ms:.1f}x")
    
    if second_run_ms < 200:
        print("✅ Performance requirement met (<200ms for cached queries)")
    else:
        print("❌ Performance requirement NOT met (>200ms for cached queries)")

if __name__ == "__main__":
    run_benchmark()
