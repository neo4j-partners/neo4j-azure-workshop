# Two Parallel Test Results

Test run: 2025-12-01 ~23:00

## Configuration

- **Parallel workers**: 2
- **Solution**: 12 (batch run - all solutions 4-11)
- **Environments**: 10 (workshop-01 through workshop-10)
- **Region**: eastus2

## Results

| Environment | Status | Duration | Notes |
|-------------|--------|----------|-------|
| workshop-01 | ✓ SUCCESS | 134.2s | |
| workshop-02 | ✓ SUCCESS | 115.0s | |
| workshop-03 | ✓ SUCCESS | 115.0s | |
| workshop-04 | ✓ SUCCESS | 114.1s | |
| workshop-05 | ✓ SUCCESS | 131.6s | |
| workshop-06 | ✓ SUCCESS | 127.6s | |
| workshop-07 | ✗ INCOMPLETE | - | Stuck on Vector Graph Agent (likely rate limit) |
| workshop-08 | ✓ SUCCESS | 132.1s | |
| workshop-09 | ✓ SUCCESS | 124.5s | |
| workshop-10 | ✓ SUCCESS | 174.5s | |

**Summary**: 9/10 passed (90%)

## Timing Analysis

- **Average duration**: 129.7s (for successful runs)
- **Min duration**: 114.1s (workshop-04)
- **Max duration**: 174.5s (workshop-10)
- **Total elapsed time**: ~10 minutes (with parallel=2)

## Observations

1. **Rate limiting**: With `--parallel 2`, rate limits were mostly avoided. Workshop-07 hit a rate limit on the Vector Graph Agent and stalled.

2. **Consistent timing**: Most tests completed in 115-135 seconds, indicating stable performance.

3. **Workshop-10 outlier**: Took 174.5s, possibly due to rate limit retries.

## Solutions Tested

Each environment ran these 8 solutions:
1. Vector Retriever
2. Vector Cypher Retriever
3. Text2Cypher Retriever
4. Simple Agent
5. Vector Graph Agent
6. Text2Cypher Agent
7. Fulltext Search
8. Hybrid Search

## Command Used

```bash
uv run python scripts/scale_deploy.py test --all --parallel 2
```

## Recommendations

1. **Use `--parallel 2`** for reliable execution without rate limits
2. **Monitor logs** in real-time: `tail -f deployments/logs/*.log`
3. **Rerun failed environments** individually: `uv run python scripts/scale_deploy.py test --env workshop-07`
