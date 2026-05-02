# B1-01 Backend Query Fast-Path Reconciliation

Date: 2026-05-02

Compared `src/api/main.py` against `src/api/query_helpers.py` with AST-scoped
function extraction. `main.py` is the active runtime path; `query_helpers.py`
is currently dormant for query execution.

## Delta Matrix

| Function / Area | `main.py` lines | `query_helpers.py` lines | Behavioral Delta | Classification | Response Shape Impact |
| --- | ---: | ---: | --- | --- | --- |
| `_fast_query_response` route ordering | 3953-4187 | 1004-1155 | `main.py` checks final golden responses, funding-policy hybrid responses, C4 read-model responses, bounded local query responses, generic funding policy responses, and generic funding ranking before falling back. `query_helpers.py` skips all of those branches. | Accidental drift. Helper is stale. | Yes. Different `routing_decision`, citations, `sql_results`, provenance, and warnings can be returned for the same query. |
| `_fast_query_response` Tier 3 messaging | 4112-4126 | 1102-1113 | `main.py` explicitly states researcher names, contacts, personal identifiers, and exact values are hidden. Helper keeps shorter aggregate-only wording. | Intentional in runtime; stale helper. | Yes. Warning and response text differ. |
| `_fast_query_response` citation/provenance text | 4141-4187 | 1130-1155 | `main.py` says fallback seed data may be used when local tables are empty; helper only says runtime DB. | Intentional in runtime; stale helper. | Yes. Citation `chunk_text` and provenance differ. |
| `_query_researchers_for_topic` cache wrapper | 823-833 plus 873-1071 | 327-523 | `main.py` wraps the researcher query path in `_researcher_topic_cache`; helper contains the uncached body directly. The uncached query body is otherwise equivalent apart from declaration order and local imports. | Intentional runtime optimization. | No payload change when cache is fresh; latency and DB load differ. |
| `_researcher_lookup_fast_response` citation set | 1074-1260 | 526-685 | `main.py` emits two citations (`nrg-researchers:<topic>` and `nrg-institutions:<topic>`) and provenance entries for both. Helper emits only the researcher citation. | Accidental drift. Runtime has stronger source support. | Yes. `citations` and `provenance` differ. |
| `_publication_count_fast_response` citation metadata | 1933-2046 | 890-992 | `main.py` includes `paper_id` and provenance binding for `publications:<year>`. Helper omits those fields. | Accidental drift. | Yes. Citation/provenance shape differs. |
| `_release_seed_graph` formatting | 1833-1913 | 834-887 | Same graph payload semantics; `main.py` includes a docstring/local import and multi-line objects. | Intentional/no-op formatting drift. | No. |
| `_seeded_institution_funding` formatting | 1785-1830 | 789-831 | Same seed-file behavior; `main.py` includes docstring/local import. | Intentional/no-op formatting drift. | No. |
| `_academic_follow_up_response` SQL string indentation | 4246-4344 | 1158-1254 | Same follow-up SQL and payload; only indentation and conversation-history formatting differ. | No-op formatting drift. | No. |
| `_advanced_adversarial_sql` salary/FDI/PhD formatting | 4347-4511 | 1257-1403 | Same SQL semantics for salary/FDI/PhD branches; formatting differs. | No-op formatting drift. | No. |
| `_advanced_adversarial_sql` open-access branch | 4481-4501 | 1381-1396 | `main.py` uses `advance_search_data`, `institution_type`, `open_access_status`, and `total_citations`; helper uses `publications`, `open_access_type`, and `citation_count`. | Accidental drift. Runtime aligns with Dhairya/source schema. | Yes. Different SQL, table, columns, row labels, and possible execution status. |
| `_advanced_adversarial_sql` innovation-stage branch | 4503-4511 | absent | `main.py` handles "innovation stage grouped per institute" through `vw_innovations_trl`; helper lacks the branch. | Accidental drift. | Yes. Helper would fall through to no fast SQL. |
| `_killer_query_response` Tier 3 answer text | 4576-4686 | 1720-1819 | `main.py` says exact internal metrics are hidden; helper only says aggregate bands. | Intentional in runtime; stale helper. | Yes. Response text differs. |
| `_fixed_structured_acceptance_sql` cost-per-patent query | 4809-4847 | 1586-1618 | `main.py` wraps the cost-per-patent calculation in `scored`; helper returns directly from the join. Ordering semantics are equivalent for current columns. | No-op SQL refactor drift. | No expected shape change. |
| `_restricted_structured_rows` | 4921-4947 | 1694-1717 | Same Tier 3 restricted row fields; formatting/docstring differ. | No-op formatting drift. | No. |
| `_needs_query_clarification` | 632-679 | 141-180 | Same condition set; `main.py` stores the profanity/sexual regex match in a temporary variable. | No-op formatting drift. | No. |
| `_extract_institute_hint` / `_extract_year_hint` | 4194-4215 | 43-60 | Same behavior; `main.py` uses local imports while helper uses module imports. | No-op import drift. | No. |
| `_has_aggregate_topic_intent` | 622-625 | 133-134 | Same boolean expression; formatting differs. | No-op formatting drift. | No. |
| Shared helper import shadowing | helper imports 23-28 and redefines 43-72 | 23-72 | `query_helpers.py` imports `_extract_institute_hint`, `_extract_year_hint`, and `_previous_financial_year` from `_shared_sql_domain`, then redefines the same names locally. | Accidental maintainability drift. | No current runtime impact because local definitions shadow imports. |
| Main-only C4/read-model fast path | 2089-3298, 341-363 | absent | `main.py` contains C4 read-model routing, single-flight cache, state/topic filters, and payload builders absent from helper. | Intentional runtime addition not reconciled into helper. | Yes. Major route, latency, citation, and payload differences. |
| Main-only funding-policy/golden fast paths | 1364-1782, 3336-3950 | absent | `main.py` contains generic funding ranking, policy hybrid, final golden, and bounded local response branches absent from helper. | Intentional runtime addition not reconciled into helper. | Yes. Major route, latency, citation, and payload differences. |

## Verdict

`src/api/query_helpers.py` is not safe as a behavioral substitute for the
active `src/api/main.py` fast path. The active runtime has additional C4,
funding, golden-query, citation, provenance, and Tier 3 safety behavior. The
next implementation pass should either delete the dormant helper copy or make
`main.py` import the helper functions after moving the main-only runtime
branches into a single canonical helper module.
