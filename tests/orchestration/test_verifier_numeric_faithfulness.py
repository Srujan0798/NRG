from src.orchestration.nodes.verifier import verifier_node


def test_verifier_rejects_unsupported_numeric_claim_from_sql_rows():
    result = verifier_node(
        {
            "synthesized_response": "The total grant amount is 45 crore.",
            "sql_results": [{"total_grants": 12_000_000}],
            "verification_retries": 0,
        }
    )

    assert result["verification_status"] == "fail"
    assert any("45 crore" in claim for claim in result["unsupported_claims"])


def test_verifier_accepts_crore_scaled_numeric_claim_from_sql_rows():
    result = verifier_node(
        {
            "synthesized_response": "The total grant amount is 4.5 crore.",
            "sql_results": [{"total_grants": 45_000_000}],
            "verification_retries": 0,
        }
    )

    assert result["verification_status"] == "ok"
    assert result["unsupported_claims"] == []
