import pytest

from src.skills.text_to_sql.skill import MAX_LIMIT, TierAwareSqlRewriter


def test_rewriter_rejects_non_select_and_multi_statement_sql():
    rewriter = TierAwareSqlRewriter()

    attacks = [
        "DROP TABLE researchers",
        "SELECT * FROM researchers; DROP TABLE researchers",
        "SELECT * FROM researchers -- hide the rest",
        "ATTACH DATABASE '/tmp/evil.db' AS evil",
        "SELECT * FROM researchers UNION SELECT * FROM funding_records",
    ]

    for sql in attacks:
        with pytest.raises(PermissionError):
            rewriter.rewrite(sql, user_tier=1)


def test_rewriter_injects_tier_filter_and_limit_for_tier_aware_tables():
    rewritten = TierAwareSqlRewriter().rewrite(
        "SELECT * FROM researchers WHERE state = 'Gujarat'",
        user_tier=2,
    )

    normalized = rewritten.lower()
    assert "access_tier <= 2" in normalized
    assert "state = 'gujarat'" in normalized
    assert f"limit {MAX_LIMIT}" in normalized


def test_rewriter_clamps_existing_limit_to_maximum():
    rewritten = TierAwareSqlRewriter().rewrite(
        "SELECT * FROM publications LIMIT 500",
        user_tier=1,
    )

    assert f"LIMIT {MAX_LIMIT}" in rewritten.upper()
    assert "500" not in rewritten


def test_rewriter_does_not_duplicate_existing_tier_filter():
    rewritten = TierAwareSqlRewriter().rewrite(
        "SELECT * FROM labs WHERE access_tier <= 1 LIMIT 20",
        user_tier=1,
    )

    assert rewritten.lower().count("access_tier") == 1
