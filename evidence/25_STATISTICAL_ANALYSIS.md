# Statistical Analysis Evidence

**Skill**: statistical-analysis
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/25_STATISTICAL_ANALYSIS.md`

---

## Statistical Analysis: NRG System Metrics

### 1. Audit Chain Statistics

**Chain Length**: 382,653 events
**Chain Status**: Valid (per `verify_chain()`)
**Event Rate**: Unknown (no timestamp of first/last event provided)

**Distribution Analysis**:
- Chain is append-only: events are sequenced by hash
- No distribution to analyze (continuous event stream)
- Hash values: uniformly distributed (HMAC-SHA256 output)

**Temporal Analysis**: Unknown without timestamp extraction from events.

**Outlier Detection**: Would require extracting event timestamps. Currently no dashboard shows event rate over time.

---

### 2. Dhairya Benchmark: 41% Accuracy

**Data**: 17 queries evaluated, 7 correct, 10 failed
**Success Rate**: 7/17 = 41.2%
**Failure Breakdown**:
- Wrong (zzz): 5/17 = 29.4%
- Error (000): 3/17 = 17.6%
- Format Mismatch (yyy): 2/17 = 11.8%

**Binomial Confidence Interval (95%)**:
- p̂ = 0.4118
- n = 17
- 95% CI: [17.8%, 64.6%]

**Interpretation**: With only 17 samples, the true accuracy could plausibly be anywhere from 18% to 65%. The 41% point estimate has wide uncertainty.

**Recommendation**: Need 50+ queries to get a precise accuracy estimate (±10%). Current sample is too small.

**Response Time Statistics**:
- Mean: 7.2s
- Range: 5.92s – 8.61s
- SLO Target: 3s
- Current is 2.4x over target

With n=17, assuming roughly normal distribution:
- StdDev ≈ (8.61 - 5.92) / 4 = 0.67s (quick estimate)
- 95% CI for mean: 7.2 ± 1.96*(0.67/√17) = 7.2 ± 0.32s → [6.88s, 7.52s]
- Even the lower bound (6.88s) is 2.3x over the 3s SLO

**Practical Significance**: All 17 queries exceed the 3s SLO. This is a systemic issue, not random noise.

---

### 3. Test Suite Timing

**Collection**: 1503 tests in 28.12s
**Execution**: Times out at 120s (truncated)

**Pass Rate**: Unknown (execution incomplete)

**Parallelization Potential**:
- If tests were parallelized across 4 workers, estimated time: 30-40s
- Current timeout suggests some tests are very slow (>30s each)

**Outlier Detection**: Likely 1-5 tests that hang or timeout, blocking the full suite.

---

### 4. Database Performance

**Query Latency** (from evidence/02_PERFORMANCE.md):
- All DB queries < 3.5ms (healthy)
- No slow queries detected

**Schema Size**:
- Dev SQLite: 18 tables
- Prod PostgreSQL: 58 tables
- Schema drift: 40 tables missing in dev

---

### 5. Tier Distribution (Hypothetical)

Based on the three-tier model (Tier 1: Researcher, Tier 2: Government, Tier 3: Industry):

**Assumed Distribution** (no data available):
- Tier 1: ~80% (researchers are primary users)
- Tier 2: ~15% (government agencies)
- Tier 3: ~5% (industry partners)

**Metric Imbalance**: If actual distribution differs significantly, tier-specific metrics will be skewed.

---

## Common Statistical Traps Identified

### Trap 1: Small Sample Size (Benchmark)
**Issue**: 17 queries to estimate accuracy is insufficient.
**Impact**: 41% accuracy could be anywhere from 18% to 65%.
**Fix**: Run 50+ queries for meaningful accuracy estimate.

### Trap 2: No Time Series Analysis (Audit Chain)
**Issue**: Chain length (382,653) is tracked but event rate over time is not.
**Impact**: Can't detect if chain growth has slowed or stalled.
**Fix**: Plot daily event count from `daily_merkle_roots` table.

### Trap 3: Average of Averages (Tier Metrics)
**Issue**: If computing "average query time" across tiers, need weighted average.
**Impact**: Simple mean would overweight low-volume tiers.
**Fix**: Use weighted average: Σ(tier_time × tier_count) / Σ(tier_count).

---

## Skill Deliverable

**Status**: COMPLETED

Statistical analysis of NRG metrics. Key findings:
- Audit chain: 382,653 events, no temporal analysis possible without timestamps
- Benchmark: 41% accuracy with wide CI [18%, 65%] — small sample
- Response time: 2.4x over SLO, all queries affected — systemic issue
- Test suite: Likely 1-5 blocking tests causing 120s timeout
- DB performance: All queries <3.5ms — healthy
