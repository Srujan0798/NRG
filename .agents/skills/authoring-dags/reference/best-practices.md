# Airflow DAG Best Practices

Use this as a quick reference when writing DAGs with the `authoring-dags` skill.

## Structure

- Keep DAG files import-safe: no network calls, large data reads, or runtime side effects at module import time.
- Put reusable task logic in normal Python modules, then call it from operators or TaskFlow tasks.
- Use explicit `dag_id`, `owner`, `start_date`, `catchup`, `schedule`, tags, and retries.
- Keep task IDs stable and descriptive because they become operational identifiers.

## Scheduling

- Prefer fixed schedules or data-aware timetables over ad hoc clock logic inside tasks.
- Set `catchup=False` unless historical backfills are intentional and tested.
- Use pools, concurrency, and max-active-run settings for external systems with rate limits.

## Dependencies

- Make dependencies explicit with `>>`, `chain()`, or TaskGroup boundaries.
- Avoid hidden dependencies through shared local files or mutable global state.
- Keep branches and sensors bounded with timeouts and clear failure behavior.

## Reliability

- Make tasks idempotent: reruns should not duplicate rows, files, notifications, or side effects.
- Use retries only for transient failures; validate inputs early for permanent failures.
- Emit enough structured logs to diagnose the failing system, key identifiers, and retry decision.

## Configuration

- Store secrets in Airflow connections or secret backends, not DAG code or variables.
- Use Airflow Variables only for non-secret runtime configuration.
- Validate required connections and variables during deployment checks.

## Validation

- Run `af dags errors` first after editing.
- Run `af dags get <dag_id>` to confirm the DAG is registered with the expected schedule.
- Run `af dags warnings` and resolve deprecations before handoff.
- Use the `testing-dags` skill before triggering runs or debugging task failures.
