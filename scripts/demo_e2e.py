"""End-to-End Zero-Leakage Demonstration Script."""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.graph import NRGWorkflow


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_demo_query(query: str, user_tier: int = 1) -> dict:
    """
    Run a complex multi-hop query end-to-end.

    Returns structured output with verification.
    """
    logger.info(f"Starting E2E demo for query: {query}")

    workflow = NRGWorkflow(test_mode=True)

    result = workflow.run(query, user_tier=user_tier)

    # Handle None values safely
    intent = result.get("intent") if result.get("intent") is not None else ""
    routing = (
        result.get("routing_decision")
        if result.get("routing_decision") is not None
        else ""
    )
    sql_query = result.get("sql_query") if result.get("sql_query") is not None else ""
    sql_results = (
        result.get("sql_results", []) if result.get("sql_results") is not None else []
    )
    retrieved_chunks = (
        result.get("retrieved_chunks", [])
        if result.get("retrieved_chunks") is not None
        else []
    )
    synthesized_response = (
        result.get("synthesized_response")
        if result.get("synthesized_response") is not None
        else ""
    )
    verification_status = (
        result.get("verification_status")
        if result.get("verification_status") is not None
        else False
    )
    trace = result.get("trace", []) if result.get("trace") is not None else []
    errors = result.get("errors", []) if result.get("errors") is not None else []

    return {
        "query": query,
        "user_tier": user_tier,
        "intent": intent,
        "routing": routing,
        "sql_query": sql_query,
        "sql_results_count": len(sql_results),
        "retrieved_chunks": retrieved_chunks,
        "synthesized_response": synthesized_response,
        "verification_status": verification_status,
        "trace": trace,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="NRG End-to-End Demo")
    parser.add_argument(
        "--query",
        type=str,
        default="Find robotics researchers",
        help="Query to test",
    )
    parser.add_argument("--tier", type=int, default=1, help="User access tier")

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("NRG Phase 1 End-to-End Zero-Leakage Demonstration")
    logger.info("=" * 60)

    result = run_demo_query(args.query, args.tier)

    output_file = Path("docs/demo/phase1_demo_output.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write("# Phase 1 Demo Output\n\n")
        f.write(f"## Query: {result['query']}\n\n")
        f.write(f"**User Tier**: {result['user_tier']}\n\n")
        f.write(f"**Timestamp**: {result['timestamp']}\n\n")
        f.write("## Processing\n\n")
        f.write(f"- **Intent Classification**: {result['intent']}\n")
        f.write(f"- **Routing Decision**: {result['routing']}\n\n")
        f.write("## Results\n\n")
        f.write(f"- **SQL Results**: {result['sql_results_count']} records\n")
        f.write(f"- **Retrieved Chunks**: {len(result.get('retrieved_chunks', []))}\n")
        f.write(f"- **Verification Status**: {result['verification_status']}\n\n")
        f.write("## Synthesized Response\n\n")
        f.write("```\n")
        f.write(str(result.get("synthesized_response", "N/A")))
        f.write("\n```\n\n")
        f.write("## Trace\n\n")
        f.write("No trace data available\n")

    logger.info(f"Demo output written to: {output_file}")

    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(json.dumps(result, indent=2, default=str))
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
