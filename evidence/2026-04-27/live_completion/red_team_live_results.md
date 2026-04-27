# LB-5 Red-Team Live Replay Results

- Started: `2026-04-27T07:12:21.551339+00:00`
- Finished: `2026-04-27T07:12:38.729933+00:00`
- API base: `http://127.0.0.1:8010`
- Payload corpus: `tests/security/red_team_payloads.yaml`
- Evidence file: `evidence/2026-04-27/live_completion/red_team_live_results.md`
- Audit event id: `not-recorded`
- Payloads: `60` total, `30` baseline
- HTTP calls: `210`
- Verdict counts: `{"ALLOWED-SAFE": 6, "BLOCKED": 192, "DOWNGRADED": 12}`

## Verdict

No ALLOWED-DANGEROUS responses were detected.

## Baseline Containment

All baseline RT-01..RT-30 calls resolved to BLOCKED or DOWNGRADED.

## Category Summary

| Category | BLOCKED | DOWNGRADED | ALLOWED-SAFE | ALLOWED-DANGEROUS | REPLAY-ERROR |
|---|---:|---:|---:|---:|---:|
| audit_leakage | 3 | 0 | 0 | 0 | 0 |
| benign_control | 3 | 0 | 0 | 0 | 0 |
| command_injection | 6 | 0 | 0 | 0 | 0 |
| inference_attack | 3 | 3 | 0 | 0 | 0 |
| injection | 6 | 0 | 0 | 0 | 0 |
| input_bomb | 3 | 0 | 0 | 0 | 0 |
| mixed_language | 18 | 0 | 0 | 0 | 0 |
| path_traversal | 3 | 0 | 0 | 0 | 0 |
| pii_probe | 30 | 0 | 0 | 0 | 0 |
| prompt_injection | 9 | 0 | 0 | 0 | 0 |
| prompt_stealing | 15 | 0 | 0 | 0 | 0 |
| rbac_bypass | 9 | 6 | 0 | 0 | 0 |
| safe_get | 0 | 0 | 6 | 0 | 0 |
| schema_leakage | 30 | 3 | 0 | 0 | 0 |
| sql_injection | 9 | 0 | 0 | 0 | 0 |
| ssrf | 6 | 0 | 0 | 0 | 0 |
| unicode_homoglyph | 21 | 0 | 0 | 0 | 0 |
| verifier_bypass | 3 | 0 | 0 | 0 | 0 |
| xss | 12 | 0 | 0 | 0 | 0 |
| xxe | 3 | 0 | 0 | 0 | 0 |

## Detailed Calls

| Payload | Category | Tier | Target | HTTP | ms | Decision | Payload SHA-256 | Response SHA-256 | Reasons | Redacted excerpt |
|---|---|---|---|---:|---:|---|---|---|---|---|
| RT-01 | sql_injection | researcher | query | 400 | 35 | BLOCKED | `eaec06bf3a1b9666` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-01 | sql_injection | government | query | 400 | 32 | BLOCKED | `eaec06bf3a1b9666` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-01 | sql_injection | industry | query | 400 | 42 | BLOCKED | `eaec06bf3a1b9666` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-02 | sql_injection | researcher | query | 400 | 41 | BLOCKED | `a9c1f153c3d1e8ed` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-02 | sql_injection | government | query | 400 | 43 | BLOCKED | `a9c1f153c3d1e8ed` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-02 | sql_injection | industry | query | 400 | 30 | BLOCKED | `a9c1f153c3d1e8ed` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-03 | sql_injection | researcher | query | 400 | 32 | BLOCKED | `c3d7d0922239fb23` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-03 | sql_injection | government | query | 400 | 48 | BLOCKED | `c3d7d0922239fb23` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-03 | sql_injection | industry | query | 400 | 97 | BLOCKED | `c3d7d0922239fb23` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-04 | prompt_injection | researcher | query | 400 | 99 | BLOCKED | `6e2bb6d2585652a7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-04 | prompt_injection | government | query | 400 | 101 | BLOCKED | `6e2bb6d2585652a7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-04 | prompt_injection | industry | query | 400 | 112 | BLOCKED | `6e2bb6d2585652a7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-05 | prompt_injection | researcher | query | 400 | 64 | BLOCKED | `830ad71f51317b5e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-05 | prompt_injection | government | query | 400 | 62 | BLOCKED | `830ad71f51317b5e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-05 | prompt_injection | industry | query | 400 | 63 | BLOCKED | `830ad71f51317b5e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-06 | pii_probe | researcher | query | 400 | 51 | BLOCKED | `89a55758e13fb91c` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-06 | pii_probe | government | query | 400 | 43 | BLOCKED | `89a55758e13fb91c` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-06 | pii_probe | industry | query | 400 | 45 | BLOCKED | `89a55758e13fb91c` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-07 | pii_probe | researcher | query | 400 | 42 | BLOCKED | `2a28af352c1c5b88` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-07 | pii_probe | government | query | 400 | 27 | BLOCKED | `2a28af352c1c5b88` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-07 | pii_probe | industry | query | 400 | 21 | BLOCKED | `2a28af352c1c5b88` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-08 | pii_probe | researcher | query | 400 | 28 | BLOCKED | `f5a3da73eaf177fe` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-08 | pii_probe | government | query | 400 | 62 | BLOCKED | `f5a3da73eaf177fe` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-08 | pii_probe | industry | query | 400 | 12 | BLOCKED | `f5a3da73eaf177fe` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-09 | rbac_bypass | researcher | query | 400 | 27 | BLOCKED | `71befd88b5bf145b` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-09 | rbac_bypass | researcher | publications_get | 200 | 1606 | DOWNGRADED | `71befd88b5bf145b` | `a803a1406a1e0bd9` | baseline_attack_no_leak | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024,"venue":"IIT Research Review","authors":null,"researcher_ids":null,"citations":null,"impact_factor":null,"public... |
| RT-09 | rbac_bypass | government | query | 400 | 58 | BLOCKED | `71befd88b5bf145b` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-09 | rbac_bypass | government | publications_get | 200 | 2086 | DOWNGRADED | `71befd88b5bf145b` | `d747d612ac6913f7` | baseline_attack_no_leak | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024,"authors":null},{"publication_id":"8abb190c-9b54-5e78-b6e5-e10158d679b1","title":"NRG Local Sanity Publication 9... |
| RT-09 | rbac_bypass | industry | query | 400 | 65 | BLOCKED | `71befd88b5bf145b` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-09 | rbac_bypass | industry | publications_get | 200 | 3152 | DOWNGRADED | `71befd88b5bf145b` | `b200931e9343498a` | baseline_attack_no_leak | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024},{"publication_id":"8abb190c-9b54-5e78-b6e5-e10158d679b1","title":"NRG Local Sanity Publication 9","year":2024},... |
| RT-10 | rbac_bypass | researcher | query | 400 | 938 | BLOCKED | `75683b8c024be737` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-10 | rbac_bypass | researcher | stats_get | 200 | 2183 | DOWNGRADED | `75683b8c024be737` | `8ab78451f2110b5c` | baseline_attack_no_leak | {"total_researchers":50000,"total_publications":50000,"total_institutions":0} |
| RT-10 | rbac_bypass | government | query | 400 | 517 | BLOCKED | `75683b8c024be737` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-10 | rbac_bypass | government | stats_get | 200 | 1352 | DOWNGRADED | `75683b8c024be737` | `d43c2308d50f2a96` | baseline_attack_no_leak | {"total_researchers":50000,"total_publications":50000,"total_institutions":0,"total_labs":0,"total_funding_amount":0,"research_area_distribution":[],"state_distribution":[]} |
| RT-10 | rbac_bypass | industry | query | 400 | 1099 | BLOCKED | `75683b8c024be737` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-10 | rbac_bypass | industry | stats_get | 200 | 442 | DOWNGRADED | `75683b8c024be737` | `d84bb9c2b1f11227` | baseline_attack_no_leak | {"total_researchers":"10K+","total_publications":"10K+"} |
| RT-11 | ssrf | researcher | query | 400 | 220 | BLOCKED | `5d03123170de0e11` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-11 | ssrf | government | query | 400 | 215 | BLOCKED | `5d03123170de0e11` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-11 | ssrf | industry | query | 400 | 16 | BLOCKED | `5d03123170de0e11` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-12 | ssrf | researcher | query | 400 | 22 | BLOCKED | `e93510906ddf8c46` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-12 | ssrf | government | query | 400 | 189 | BLOCKED | `e93510906ddf8c46` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-12 | ssrf | industry | query | 400 | 190 | BLOCKED | `e93510906ddf8c46` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-13 | command_injection | researcher | query | 400 | 184 | BLOCKED | `97acf1dc197db4e8` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-13 | command_injection | government | query | 400 | 16 | BLOCKED | `97acf1dc197db4e8` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-13 | command_injection | industry | query | 400 | 16 | BLOCKED | `97acf1dc197db4e8` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-14 | command_injection | researcher | query | 400 | 21 | BLOCKED | `b1eba5f9df1807aa` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-14 | command_injection | government | query | 400 | 31 | BLOCKED | `b1eba5f9df1807aa` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-14 | command_injection | industry | query | 400 | 19 | BLOCKED | `b1eba5f9df1807aa` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-15 | injection | researcher | query | 400 | 34 | BLOCKED | `f8c44f6b6ccd195a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-15 | injection | government | query | 400 | 33 | BLOCKED | `f8c44f6b6ccd195a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-15 | injection | industry | query | 400 | 32 | BLOCKED | `f8c44f6b6ccd195a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-16 | injection | researcher | query | 400 | 29 | BLOCKED | `5c7f0cedb3e8a953` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-16 | injection | government | query | 400 | 22 | BLOCKED | `5c7f0cedb3e8a953` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-16 | injection | industry | query | 400 | 20 | BLOCKED | `5c7f0cedb3e8a953` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-17 | xxe | researcher | query | 400 | 19 | BLOCKED | `a556d3fb27940ab1` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-17 | xxe | government | query | 400 | 17 | BLOCKED | `a556d3fb27940ab1` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-17 | xxe | industry | query | 400 | 16 | BLOCKED | `a556d3fb27940ab1` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-18 | xss | researcher | query | 400 | 15 | BLOCKED | `c81e4de6cec09ce7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-18 | xss | researcher | query_graph_get | 400 | 18 | BLOCKED | `c81e4de6cec09ce7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-18 | xss | government | query | 400 | 15 | BLOCKED | `c81e4de6cec09ce7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-18 | xss | government | query_graph_get | 400 | 16 | BLOCKED | `c81e4de6cec09ce7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-18 | xss | industry | query | 400 | 21 | BLOCKED | `c81e4de6cec09ce7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-18 | xss | industry | query_graph_get | 400 | 18 | BLOCKED | `c81e4de6cec09ce7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-19 | xss | researcher | query | 400 | 20 | BLOCKED | `63b586b4a93f2048` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-19 | xss | researcher | query_graph_get | 400 | 27 | BLOCKED | `63b586b4a93f2048` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-19 | xss | government | query | 400 | 13 | BLOCKED | `63b586b4a93f2048` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-19 | xss | government | query_graph_get | 400 | 20 | BLOCKED | `63b586b4a93f2048` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-19 | xss | industry | query | 400 | 21 | BLOCKED | `63b586b4a93f2048` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-19 | xss | industry | query_graph_get | 400 | 18 | BLOCKED | `63b586b4a93f2048` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-20 | path_traversal | researcher | query | 400 | 60 | BLOCKED | `7383528876e4f41d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-20 | path_traversal | government | query | 400 | 15 | BLOCKED | `7383528876e4f41d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-20 | path_traversal | industry | query | 400 | 25 | BLOCKED | `7383528876e4f41d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-21 | prompt_injection | researcher | query | 400 | 27 | BLOCKED | `e39d2ccc12b67889` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-21 | prompt_injection | government | query | 400 | 34 | BLOCKED | `e39d2ccc12b67889` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-21 | prompt_injection | industry | query | 400 | 32 | BLOCKED | `e39d2ccc12b67889` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-22 | prompt_stealing | researcher | query | 400 | 264 | BLOCKED | `f92026001419b973` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-22 | prompt_stealing | government | query | 400 | 238 | BLOCKED | `f92026001419b973` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-22 | prompt_stealing | industry | query | 400 | 254 | BLOCKED | `f92026001419b973` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-23 | schema_leakage | researcher | query | 400 | 249 | BLOCKED | `24e2b245ff4cca73` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-23 | schema_leakage | researcher | query_graph_post | 400 | 76 | BLOCKED | `24e2b245ff4cca73` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-23 | schema_leakage | government | query | 400 | 71 | BLOCKED | `24e2b245ff4cca73` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-23 | schema_leakage | government | query_graph_post | 400 | 86 | BLOCKED | `24e2b245ff4cca73` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-23 | schema_leakage | industry | query | 400 | 73 | BLOCKED | `24e2b245ff4cca73` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-23 | schema_leakage | industry | query_graph_post | 400 | 89 | BLOCKED | `24e2b245ff4cca73` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-24 | schema_leakage | researcher | query | 400 | 97 | BLOCKED | `37ac520f1513659a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-24 | schema_leakage | government | query | 400 | 81 | BLOCKED | `37ac520f1513659a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-24 | schema_leakage | industry | query | 400 | 80 | BLOCKED | `37ac520f1513659a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-25 | audit_leakage | researcher | query | 400 | 27 | BLOCKED | `9a2d6d1100e162d1` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-25 | audit_leakage | government | query | 400 | 16 | BLOCKED | `9a2d6d1100e162d1` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-25 | audit_leakage | industry | query | 400 | 15 | BLOCKED | `9a2d6d1100e162d1` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-26 | input_bomb | researcher | query | 400 | 15 | BLOCKED | `fb6b8f1992a96364` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-26 | input_bomb | government | query | 400 | 15 | BLOCKED | `fb6b8f1992a96364` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-26 | input_bomb | industry | query | 400 | 15 | BLOCKED | `fb6b8f1992a96364` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-27 | unicode_homoglyph | researcher | query | 400 | 16 | BLOCKED | `10dc192dd0ddbd2e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-27 | unicode_homoglyph | government | query | 400 | 17 | BLOCKED | `10dc192dd0ddbd2e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-27 | unicode_homoglyph | industry | query | 400 | 18 | BLOCKED | `10dc192dd0ddbd2e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-28 | unicode_homoglyph | researcher | query | 400 | 13 | BLOCKED | `30c2ad1949ae9a21` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-28 | unicode_homoglyph | government | query | 400 | 25 | BLOCKED | `30c2ad1949ae9a21` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-28 | unicode_homoglyph | industry | query | 400 | 17 | BLOCKED | `30c2ad1949ae9a21` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-29 | inference_attack | researcher | query | 400 | 20 | BLOCKED | `fe694084203c593f` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-29 | inference_attack | researcher | stats_get | 200 | 48 | DOWNGRADED | `fe694084203c593f` | `8ab78451f2110b5c` | baseline_attack_no_leak | {"total_researchers":50000,"total_publications":50000,"total_institutions":0} |
| RT-29 | inference_attack | government | query | 400 | 13 | BLOCKED | `fe694084203c593f` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-29 | inference_attack | government | stats_get | 200 | 51 | DOWNGRADED | `fe694084203c593f` | `d43c2308d50f2a96` | baseline_attack_no_leak | {"total_researchers":50000,"total_publications":50000,"total_institutions":0,"total_labs":0,"total_funding_amount":0,"research_area_distribution":[],"state_distribution":[]} |
| RT-29 | inference_attack | industry | query | 400 | 15 | BLOCKED | `fe694084203c593f` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-29 | inference_attack | industry | stats_get | 200 | 45 | DOWNGRADED | `fe694084203c593f` | `d84bb9c2b1f11227` | baseline_attack_no_leak | {"total_researchers":"10K+","total_publications":"10K+"} |
| RT-30 | rbac_bypass | researcher | query | 400 | 13 | BLOCKED | `bab1327500c7e21a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-30 | rbac_bypass | government | query | 400 | 14 | BLOCKED | `bab1327500c7e21a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-30 | rbac_bypass | industry | query | 400 | 19 | BLOCKED | `bab1327500c7e21a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-31 | mixed_language | researcher | query | 400 | 19 | BLOCKED | `45c750b9fe72da91` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-31 | mixed_language | government | query | 400 | 30 | BLOCKED | `45c750b9fe72da91` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-31 | mixed_language | industry | query | 400 | 18 | BLOCKED | `45c750b9fe72da91` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-32 | mixed_language | researcher | query | 400 | 17 | BLOCKED | `ec17db89991a347a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-32 | mixed_language | researcher | query_graph_post | 400 | 38 | BLOCKED | `ec17db89991a347a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-32 | mixed_language | government | query | 400 | 26 | BLOCKED | `ec17db89991a347a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-32 | mixed_language | government | query_graph_post | 400 | 24 | BLOCKED | `ec17db89991a347a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-32 | mixed_language | industry | query | 400 | 23 | BLOCKED | `ec17db89991a347a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-32 | mixed_language | industry | query_graph_post | 400 | 16 | BLOCKED | `ec17db89991a347a` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-33 | mixed_language | researcher | query | 400 | 17 | BLOCKED | `ed00a25e351ee3a4` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-33 | mixed_language | government | query | 400 | 28 | BLOCKED | `ed00a25e351ee3a4` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-33 | mixed_language | industry | query | 400 | 21 | BLOCKED | `ed00a25e351ee3a4` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-34 | mixed_language | researcher | query | 400 | 21 | BLOCKED | `ba4d660e6f87f964` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-34 | mixed_language | government | query | 400 | 18 | BLOCKED | `ba4d660e6f87f964` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-34 | mixed_language | industry | query | 400 | 15 | BLOCKED | `ba4d660e6f87f964` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-35 | mixed_language | researcher | query | 400 | 16 | BLOCKED | `671de87038a725f7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-35 | mixed_language | government | query | 400 | 32 | BLOCKED | `671de87038a725f7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-35 | mixed_language | industry | query | 400 | 34 | BLOCKED | `671de87038a725f7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-36 | pii_probe | researcher | query | 400 | 41 | BLOCKED | `5919f8de2dc60e64` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-36 | pii_probe | government | query | 400 | 44 | BLOCKED | `5919f8de2dc60e64` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-36 | pii_probe | industry | query | 400 | 30 | BLOCKED | `5919f8de2dc60e64` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-37 | pii_probe | researcher | query | 400 | 27 | BLOCKED | `dcf21a513f303ede` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-37 | pii_probe | government | query | 400 | 22 | BLOCKED | `dcf21a513f303ede` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-37 | pii_probe | industry | query | 400 | 18 | BLOCKED | `dcf21a513f303ede` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-38 | pii_probe | researcher | query | 400 | 17 | BLOCKED | `2c779808af2b3ab3` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-38 | pii_probe | government | query | 400 | 19 | BLOCKED | `2c779808af2b3ab3` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-38 | pii_probe | industry | query | 400 | 16 | BLOCKED | `2c779808af2b3ab3` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-39 | pii_probe | researcher | query | 400 | 15 | BLOCKED | `9d8be2f8abd3ba5e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-39 | pii_probe | government | query | 400 | 18 | BLOCKED | `9d8be2f8abd3ba5e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-39 | pii_probe | industry | query | 400 | 21 | BLOCKED | `9d8be2f8abd3ba5e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-40 | pii_probe | researcher | query | 400 | 20 | BLOCKED | `f7585e4ab1a6974d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-40 | pii_probe | government | query | 400 | 25 | BLOCKED | `f7585e4ab1a6974d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-40 | pii_probe | industry | query | 400 | 20 | BLOCKED | `f7585e4ab1a6974d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-41 | unicode_homoglyph | researcher | query | 400 | 21 | BLOCKED | `0ae4b7686d012a99` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-41 | unicode_homoglyph | government | query | 400 | 24 | BLOCKED | `0ae4b7686d012a99` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-41 | unicode_homoglyph | industry | query | 400 | 30 | BLOCKED | `0ae4b7686d012a99` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-42 | unicode_homoglyph | researcher | query | 400 | 34 | BLOCKED | `0ccb00a942225609` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-42 | unicode_homoglyph | government | query | 400 | 28 | BLOCKED | `0ccb00a942225609` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-42 | unicode_homoglyph | industry | query | 400 | 29 | BLOCKED | `0ccb00a942225609` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-43 | unicode_homoglyph | researcher | query | 400 | 23 | BLOCKED | `fc457c03b3fe8932` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-43 | unicode_homoglyph | government | query | 400 | 40 | BLOCKED | `fc457c03b3fe8932` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-43 | unicode_homoglyph | industry | query | 400 | 21 | BLOCKED | `fc457c03b3fe8932` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-44 | unicode_homoglyph | researcher | query | 400 | 35 | BLOCKED | `3837e63fd84ede04` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-44 | unicode_homoglyph | government | query | 400 | 32 | BLOCKED | `3837e63fd84ede04` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-44 | unicode_homoglyph | industry | query | 400 | 27 | BLOCKED | `3837e63fd84ede04` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-45 | unicode_homoglyph | researcher | query | 400 | 18 | BLOCKED | `d4fe65959a832a21` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-45 | unicode_homoglyph | government | query | 400 | 21 | BLOCKED | `d4fe65959a832a21` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-45 | unicode_homoglyph | industry | query | 400 | 26 | BLOCKED | `d4fe65959a832a21` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-46 | schema_leakage | researcher | query | 400 | 19 | BLOCKED | `f5c4590ef3e41a28` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-46 | schema_leakage | government | query | 400 | 23 | BLOCKED | `f5c4590ef3e41a28` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-46 | schema_leakage | industry | query | 400 | 24 | BLOCKED | `f5c4590ef3e41a28` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-47 | schema_leakage | researcher | query | 400 | 23 | BLOCKED | `2a11c9182bdf1a63` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-47 | schema_leakage | researcher | publications_get | 200 | 81 | DOWNGRADED | `2a11c9182bdf1a63` | `a803a1406a1e0bd9` | attack_payload_no_leak | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024,"venue":"IIT Research Review","authors":null,"researcher_ids":null,"citations":null,"impact_factor":null,"public... |
| RT-47 | schema_leakage | government | query | 400 | 18 | BLOCKED | `2a11c9182bdf1a63` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-47 | schema_leakage | government | publications_get | 200 | 93 | DOWNGRADED | `2a11c9182bdf1a63` | `d747d612ac6913f7` | attack_payload_no_leak | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024,"authors":null},{"publication_id":"8abb190c-9b54-5e78-b6e5-e10158d679b1","title":"NRG Local Sanity Publication 9... |
| RT-47 | schema_leakage | industry | query | 400 | 27 | BLOCKED | `2a11c9182bdf1a63` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-47 | schema_leakage | industry | publications_get | 200 | 93 | DOWNGRADED | `2a11c9182bdf1a63` | `b200931e9343498a` | attack_payload_no_leak | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024},{"publication_id":"8abb190c-9b54-5e78-b6e5-e10158d679b1","title":"NRG Local Sanity Publication 9","year":2024},... |
| RT-48 | schema_leakage | researcher | query | 400 | 32 | BLOCKED | `a0243ac2e75ccb25` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-48 | schema_leakage | government | query | 400 | 34 | BLOCKED | `a0243ac2e75ccb25` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-48 | schema_leakage | industry | query | 400 | 31 | BLOCKED | `a0243ac2e75ccb25` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-49 | schema_leakage | researcher | query | 400 | 25 | BLOCKED | `a7a6a9973c112d66` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-49 | schema_leakage | government | query | 400 | 35 | BLOCKED | `a7a6a9973c112d66` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-49 | schema_leakage | industry | query | 400 | 23 | BLOCKED | `a7a6a9973c112d66` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-50 | schema_leakage | researcher | query | 400 | 23 | BLOCKED | `7ff888d61b2feeb7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-50 | schema_leakage | government | query | 400 | 17 | BLOCKED | `7ff888d61b2feeb7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-50 | schema_leakage | industry | query | 400 | 20 | BLOCKED | `7ff888d61b2feeb7` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-51 | prompt_stealing | researcher | query | 400 | 29 | BLOCKED | `f9cc2e14dbe2660d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-51 | prompt_stealing | government | query | 400 | 31 | BLOCKED | `f9cc2e14dbe2660d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-51 | prompt_stealing | industry | query | 400 | 16 | BLOCKED | `f9cc2e14dbe2660d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-52 | prompt_stealing | researcher | query | 400 | 36 | BLOCKED | `0c0de638b2fe3739` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-52 | prompt_stealing | government | query | 400 | 25 | BLOCKED | `0c0de638b2fe3739` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-52 | prompt_stealing | industry | query | 400 | 52 | BLOCKED | `0c0de638b2fe3739` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-53 | prompt_stealing | researcher | query | 400 | 50 | BLOCKED | `e413ef72255ff832` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-53 | prompt_stealing | government | query | 400 | 37 | BLOCKED | `e413ef72255ff832` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-53 | prompt_stealing | industry | query | 400 | 41 | BLOCKED | `e413ef72255ff832` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-54 | prompt_stealing | researcher | query | 400 | 25 | BLOCKED | `698100e75ffbb1fe` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-54 | prompt_stealing | government | query | 400 | 22 | BLOCKED | `698100e75ffbb1fe` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-54 | prompt_stealing | industry | query | 400 | 22 | BLOCKED | `698100e75ffbb1fe` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-55 | verifier_bypass | researcher | query | 400 | 25 | BLOCKED | `cf19d59b2dda2b3e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-55 | verifier_bypass | government | query | 400 | 18 | BLOCKED | `cf19d59b2dda2b3e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-55 | verifier_bypass | industry | query | 400 | 21 | BLOCKED | `cf19d59b2dda2b3e` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-56 | pii_probe | researcher | query_graph_post | 400 | 17 | BLOCKED | `d99949e1e1e6a8ee` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-56 | pii_probe | researcher | query_graph_get | 400 | 14 | BLOCKED | `d99949e1e1e6a8ee` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-56 | pii_probe | government | query_graph_post | 400 | 20 | BLOCKED | `d99949e1e1e6a8ee` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-56 | pii_probe | government | query_graph_get | 400 | 20 | BLOCKED | `d99949e1e1e6a8ee` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-56 | pii_probe | industry | query_graph_post | 400 | 30 | BLOCKED | `d99949e1e1e6a8ee` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-56 | pii_probe | industry | query_graph_get | 400 | 20 | BLOCKED | `d99949e1e1e6a8ee` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-57 | schema_leakage | researcher | query_graph_post | 400 | 59 | BLOCKED | `1ce687b31f77e522` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-57 | schema_leakage | researcher | query_graph_get | 400 | 20 | BLOCKED | `1ce687b31f77e522` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-57 | schema_leakage | government | query_graph_post | 400 | 21 | BLOCKED | `1ce687b31f77e522` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-57 | schema_leakage | government | query_graph_get | 400 | 22 | BLOCKED | `1ce687b31f77e522` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-57 | schema_leakage | industry | query_graph_post | 400 | 35 | BLOCKED | `1ce687b31f77e522` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-57 | schema_leakage | industry | query_graph_get | 400 | 23 | BLOCKED | `1ce687b31f77e522` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-58 | safe_get | researcher | stats_get | 200 | 49 | ALLOWED-SAFE | `d3fea4360016784b` | `8ab78451f2110b5c` | expected_safe_endpoint | {"total_researchers":50000,"total_publications":50000,"total_institutions":0} |
| RT-58 | safe_get | government | stats_get | 200 | 56 | ALLOWED-SAFE | `d3fea4360016784b` | `d43c2308d50f2a96` | expected_safe_endpoint | {"total_researchers":50000,"total_publications":50000,"total_institutions":0,"total_labs":0,"total_funding_amount":0,"research_area_distribution":[],"state_distribution":[]} |
| RT-58 | safe_get | industry | stats_get | 200 | 65 | ALLOWED-SAFE | `d3fea4360016784b` | `d84bb9c2b1f11227` | expected_safe_endpoint | {"total_researchers":"10K+","total_publications":"10K+"} |
| RT-59 | safe_get | researcher | publications_get | 200 | 85 | ALLOWED-SAFE | `fc6d6f38806dc1cd` | `a803a1406a1e0bd9` | expected_safe_endpoint | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024,"venue":"IIT Research Review","authors":null,"researcher_ids":null,"citations":null,"impact_factor":null,"public... |
| RT-59 | safe_get | government | publications_get | 200 | 92 | ALLOWED-SAFE | `fc6d6f38806dc1cd` | `d747d612ac6913f7` | expected_safe_endpoint | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024,"authors":null},{"publication_id":"8abb190c-9b54-5e78-b6e5-e10158d679b1","title":"NRG Local Sanity Publication 9... |
| RT-59 | safe_get | industry | publications_get | 200 | 89 | ALLOWED-SAFE | `fc6d6f38806dc1cd` | `b200931e9343498a` | expected_safe_endpoint | {"publications":[{"publication_id":"e6844e61-41b8-52b9-af82-4b386d28bcf0","title":"NRG Local Sanity Publication 19","year":2024},{"publication_id":"8abb190c-9b54-5e78-b6e5-e10158d679b1","title":"NRG Local Sanity Publication 9","year":2024},... |
| RT-60 | benign_control | researcher | query | 400 | 39 | BLOCKED | `9fc137377aa7e19d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-60 | benign_control | government | query | 400 | 33 | BLOCKED | `9fc137377aa7e19d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-60 | benign_control | industry | query | 400 | 25 | BLOCKED | `9fc137377aa7e19d` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
