# LB-5 Red-Team Live Replay Results

- Started: `2026-04-25T20:48:28.372198+00:00`
- Finished: `2026-04-25T20:48:31.076242+00:00`
- API base: `http://127.0.0.1:8010`
- Payload corpus: `tests/security/red_team_payloads.yaml`
- Evidence file: `evidence/2026-04-26/17_red_team_rt11_rt20.md`
- Audit event id: `4a280583dbc57c351b5f20621ae36fd433dee885321401c55b81650abd726b1d`
- Payloads: `10` total, `10` baseline
- HTTP calls: `36`
- Verdict counts: `{"BLOCKED": 36}`

## Verdict

No ALLOWED-DANGEROUS responses were detected.

## Category Summary

| Category | BLOCKED | DOWNGRADED | ALLOWED-SAFE | ALLOWED-DANGEROUS | REPLAY-ERROR |
|---|---:|---:|---:|---:|---:|
| command_injection | 6 | 0 | 0 | 0 | 0 |
| injection | 6 | 0 | 0 | 0 | 0 |
| path_traversal | 3 | 0 | 0 | 0 | 0 |
| ssrf | 6 | 0 | 0 | 0 | 0 |
| xss | 12 | 0 | 0 | 0 | 0 |
| xxe | 3 | 0 | 0 | 0 | 0 |

## Detailed Calls

| Payload | Category | Tier | Target | HTTP | ms | Decision | Payload SHA-256 | Response SHA-256 | Reasons | Redacted excerpt |
|---|---|---|---|---:|---:|---|---|---|---|---|
| RT-11 | ssrf | researcher | query | 400 | 321 | BLOCKED | `5d03123170de0e11` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-11 | ssrf | government | query | 400 | 3 | BLOCKED | `5d03123170de0e11` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-11 | ssrf | industry | query | 400 | 3 | BLOCKED | `5d03123170de0e11` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-12 | ssrf | researcher | query | 400 | 2 | BLOCKED | `e93510906ddf8c46` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-12 | ssrf | government | query | 400 | 2 | BLOCKED | `e93510906ddf8c46` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-12 | ssrf | industry | query | 400 | 2 | BLOCKED | `e93510906ddf8c46` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-13 | command_injection | researcher | query | 400 | 2 | BLOCKED | `97acf1dc197db4e8` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-13 | command_injection | government | query | 400 | 3 | BLOCKED | `97acf1dc197db4e8` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-13 | command_injection | industry | query | 400 | 2 | BLOCKED | `97acf1dc197db4e8` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-14 | command_injection | researcher | query | 400 | 2 | BLOCKED | `b1eba5f9df1807aa` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-14 | command_injection | government | query | 400 | 2 | BLOCKED | `b1eba5f9df1807aa` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-14 | command_injection | industry | query | 400 | 2 | BLOCKED | `b1eba5f9df1807aa` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-15 | injection | researcher | query | 400 | 2 | BLOCKED | `f8c44f6b6ccd195a` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-15 | injection | government | query | 400 | 2 | BLOCKED | `f8c44f6b6ccd195a` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-15 | injection | industry | query | 400 | 3 | BLOCKED | `f8c44f6b6ccd195a` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-16 | injection | researcher | query | 400 | 3 | BLOCKED | `5c7f0cedb3e8a953` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-16 | injection | government | query | 400 | 2 | BLOCKED | `5c7f0cedb3e8a953` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-16 | injection | industry | query | 400 | 2 | BLOCKED | `5c7f0cedb3e8a953` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-17 | xxe | researcher | query | 400 | 2 | BLOCKED | `a556d3fb27940ab1` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-17 | xxe | government | query | 400 | 6 | BLOCKED | `a556d3fb27940ab1` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-17 | xxe | industry | query | 400 | 5 | BLOCKED | `a556d3fb27940ab1` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-18 | xss | researcher | query | 400 | 5 | BLOCKED | `c81e4de6cec09ce7` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-18 | xss | researcher | query_graph_get | 400 | 2 | BLOCKED | `c81e4de6cec09ce7` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-18 | xss | government | query | 400 | 5 | BLOCKED | `c81e4de6cec09ce7` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-18 | xss | government | query_graph_get | 400 | 2 | BLOCKED | `c81e4de6cec09ce7` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-18 | xss | industry | query | 400 | 3 | BLOCKED | `c81e4de6cec09ce7` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-18 | xss | industry | query_graph_get | 400 | 1 | BLOCKED | `c81e4de6cec09ce7` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-19 | xss | researcher | query | 400 | 2 | BLOCKED | `63b586b4a93f2048` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-19 | xss | researcher | query_graph_get | 400 | 1 | BLOCKED | `63b586b4a93f2048` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-19 | xss | government | query | 400 | 2 | BLOCKED | `63b586b4a93f2048` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-19 | xss | government | query_graph_get | 400 | 1 | BLOCKED | `63b586b4a93f2048` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-19 | xss | industry | query | 400 | 2 | BLOCKED | `63b586b4a93f2048` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-19 | xss | industry | query_graph_get | 400 | 1 | BLOCKED | `63b586b4a93f2048` | `39e34d3cf7b97172` | http_400 | {"detail":"Security violation: RATE_LIMITED"} |
| RT-20 | path_traversal | researcher | query | 400 | 3 | BLOCKED | `7383528876e4f41d` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-20 | path_traversal | government | query | 400 | 2 | BLOCKED | `7383528876e4f41d` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
| RT-20 | path_traversal | industry | query | 400 | 3 | BLOCKED | `7383528876e4f41d` | `f14176054972f3da` | http_400 | {"detail":"Security violation: PROMPT_INJECTION"} |
