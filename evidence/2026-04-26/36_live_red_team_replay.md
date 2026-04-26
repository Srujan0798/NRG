# LB-5 Red-Team Live Replay Results

- Started: `2026-04-26T17:50:43.385064+00:00`
- Finished: `2026-04-26T17:53:52.364948+00:00`
- API base: `http://127.0.0.1:8041`
- Payload corpus: `tests/security/red_team_payloads.yaml`
- Evidence file: `evidence/2026-04-26/36_live_red_team_replay.md`
- Audit event id: `3f84b9fcc753376cb369e1bc848f543ffe666bf728c89a395cd7cd46848da08f`
- Payloads validated: `60` total, `30` baseline
- Replay status: `BLOCKED`

## Blocker

Live replay could not begin because the API setup phase failed before authenticated requests were available.

```text
RuntimeError('API did not become reachable within 180 seconds')
```

## Corpus Hashes

| Payload | Category | Baseline | Targets | Payload SHA-256 |
|---|---|---:|---|---|
| RT-01 | sql_injection | true | query | `eaec06bf3a1b9666` |
| RT-02 | sql_injection | true | query | `a9c1f153c3d1e8ed` |
| RT-03 | sql_injection | true | query | `c3d7d0922239fb23` |
| RT-04 | prompt_injection | true | query | `6e2bb6d2585652a7` |
| RT-05 | prompt_injection | true | query | `830ad71f51317b5e` |
| RT-06 | pii_probe | true | query | `89a55758e13fb91c` |
| RT-07 | pii_probe | true | query | `2a28af352c1c5b88` |
| RT-08 | pii_probe | true | query | `f5a3da73eaf177fe` |
| RT-09 | rbac_bypass | true | query, publications_get | `71befd88b5bf145b` |
| RT-10 | rbac_bypass | true | query, stats_get | `75683b8c024be737` |
| RT-11 | ssrf | true | query | `5d03123170de0e11` |
| RT-12 | ssrf | true | query | `e93510906ddf8c46` |
| RT-13 | command_injection | true | query | `97acf1dc197db4e8` |
| RT-14 | command_injection | true | query | `b1eba5f9df1807aa` |
| RT-15 | injection | true | query | `f8c44f6b6ccd195a` |
| RT-16 | injection | true | query | `5c7f0cedb3e8a953` |
| RT-17 | xxe | true | query | `a556d3fb27940ab1` |
| RT-18 | xss | true | query, query_graph_get | `c81e4de6cec09ce7` |
| RT-19 | xss | true | query, query_graph_get | `63b586b4a93f2048` |
| RT-20 | path_traversal | true | query | `7383528876e4f41d` |
| RT-21 | prompt_injection | true | query | `e39d2ccc12b67889` |
| RT-22 | prompt_stealing | true | query | `f92026001419b973` |
| RT-23 | schema_leakage | true | query, query_graph_post | `24e2b245ff4cca73` |
| RT-24 | schema_leakage | true | query | `37ac520f1513659a` |
| RT-25 | audit_leakage | true | query | `9a2d6d1100e162d1` |
| RT-26 | input_bomb | true | query | `fb6b8f1992a96364` |
| RT-27 | unicode_homoglyph | true | query | `10dc192dd0ddbd2e` |
| RT-28 | unicode_homoglyph | true | query | `30c2ad1949ae9a21` |
| RT-29 | inference_attack | true | query, stats_get | `fe694084203c593f` |
| RT-30 | rbac_bypass | true | query | `bab1327500c7e21a` |
| RT-31 | mixed_language | false | query | `45c750b9fe72da91` |
| RT-32 | mixed_language | false | query, query_graph_post | `ec17db89991a347a` |
| RT-33 | mixed_language | false | query | `ed00a25e351ee3a4` |
| RT-34 | mixed_language | false | query | `ba4d660e6f87f964` |
| RT-35 | mixed_language | false | query | `671de87038a725f7` |
| RT-36 | pii_probe | false | query | `5919f8de2dc60e64` |
| RT-37 | pii_probe | false | query | `dcf21a513f303ede` |
| RT-38 | pii_probe | false | query | `2c779808af2b3ab3` |
| RT-39 | pii_probe | false | query | `9d8be2f8abd3ba5e` |
| RT-40 | pii_probe | false | query | `f7585e4ab1a6974d` |
| RT-41 | unicode_homoglyph | false | query | `0ae4b7686d012a99` |
| RT-42 | unicode_homoglyph | false | query | `0ccb00a942225609` |
| RT-43 | unicode_homoglyph | false | query | `fc457c03b3fe8932` |
| RT-44 | unicode_homoglyph | false | query | `3837e63fd84ede04` |
| RT-45 | unicode_homoglyph | false | query | `d4fe65959a832a21` |
| RT-46 | schema_leakage | false | query | `f5c4590ef3e41a28` |
| RT-47 | schema_leakage | false | query, publications_get | `2a11c9182bdf1a63` |
| RT-48 | schema_leakage | false | query | `a0243ac2e75ccb25` |
| RT-49 | schema_leakage | false | query | `a7a6a9973c112d66` |
| RT-50 | schema_leakage | false | query | `7ff888d61b2feeb7` |
| RT-51 | prompt_stealing | false | query | `f9cc2e14dbe2660d` |
| RT-52 | prompt_stealing | false | query | `0c0de638b2fe3739` |
| RT-53 | prompt_stealing | false | query | `e413ef72255ff832` |
| RT-54 | prompt_stealing | false | query | `698100e75ffbb1fe` |
| RT-55 | verifier_bypass | false | query | `cf19d59b2dda2b3e` |
| RT-56 | pii_probe | false | query_graph_get, query_graph_post | `d99949e1e1e6a8ee` |
| RT-57 | schema_leakage | false | query_graph_get, query_graph_post | `1ce687b31f77e522` |
| RT-58 | safe_get | false | stats_get | `d3fea4360016784b` |
| RT-59 | safe_get | false | publications_get | `fc6d6f38806dc1cd` |
| RT-60 | benign_control | false | query | `9fc137377aa7e19d` |
