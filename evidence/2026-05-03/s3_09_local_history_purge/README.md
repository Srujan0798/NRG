# S3-09 Local History Purge Evidence

Date: 2026-05-03
Status: PASS in local rewritten clone, remote coordination pending

## Scope

This evidence records a local Git history purge for runtime `.env*` files that
previously triggered S3-09. A bare mirror backup was created before rewriting:

`/Users/srujansai/Desktop/NRG_HISTORY_BACKUP_BEFORE_S3_09_PURGE_20260502T201321Z.git`

No remote force-push is recorded in this evidence. Remote closure still needs
repository-owner approval, contributor coordination, and credential rotation.

## Verification

| Check | Result | Evidence |
|---|---:|---|
| Head before purge | Recorded | `01_head_before_purge.txt` |
| Remotes before purge | Recorded | `02_remotes_before_purge.txt` |
| Head after purge | Recorded | `07_head_after_purge.txt` |
| Remotes after purge | Recorded | `09_remotes_after_purge.txt` |
| Environment history after purge | Empty | `10_env_history_after_purge.txt` |
| S3-09 scanner after purge | PASS, 0 findings | `11_s3_09_env_history_secret_scan_after_purge.json` |
| Leftover rewritten refs | Empty | `12_rewrite_leftover_refs.txt` |
| Current tracked env files | Empty | `14_current_tracked_env_files.txt` |
| Initial security suite after purge | FAIL, live API worker disconnect | `16_security_suite_after_purge.log` |
| API restart health | PASS, `/health/all` healthy | `23_health_all_after_api_restart.json` |
| RT05 live retry with 60s timeout | PASS | `25_rt05_live_timeout_after_api_restart.log` |
| RT13-RT15 PII live recheck | PASS, 3 tests | `29_rt13_rt15_pii_live_recheck.log` |
| Full security suite after RT14 recheck | PASS, 619 passed / 13 skipped | `30_security_suite_live_timeout_after_rt14_recheck.log` |
| Docker service status after security pass | PASS, services healthy | `31_docker_compose_ps_after_security_pass.log` |
| Docker logs after security pass | Captured | `32_docker_compose_logs_tail20_after_security_pass.log` |
| Final S3-09 scanner after evidence sync | PASS, 0 findings | `36_s3_09_env_history_secret_scan_final.json` |

## Boundaries

- Local scanner pass does not prove the GitHub remote has been rewritten.
- Credential rotation remains required because old values were historically
  exposed before this local rewrite.
- The earlier RT05 timeout was resolved by rerunning the live red-team path with
  the same 60 second timeout used by the full security suite.
