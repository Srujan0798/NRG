# Demo Dashboard Scale Evidence

Date: 2026-04-25  
API under test: `http://127.0.0.1:8017`

## Researcher Tier `/stats`

```json
{
  "total_researchers": 5615,
  "total_publications": 12000,
  "total_institutions": 181
}
```

## Government Tier `/stats`

```json
{
  "total_researchers": 5615,
  "total_publications": 12000,
  "total_institutions": 181,
  "total_labs": 890,
  "total_funding_amount": 15436,
  "state_distribution": [
    {"state": "Gujarat", "count": 886},
    {"state": "Delhi", "count": 710},
    {"state": "Maharashtra", "count": 625}
  ]
}
```

## Industry Tier `/stats`

```json
{
  "total_researchers": "5K-10K",
  "total_publications": "10K+"
}
```

## Conclusion

GAP-6 is already resolved in the current local DB/API: dashboard counts are in the thousands and Tier 3 receives bucketed aggregate values rather than exact full counts.
