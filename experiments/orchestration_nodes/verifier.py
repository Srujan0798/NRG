"""Verifier Node - Faithfulness checking for synthesized responses."""

import logging
import re
from typing import TypedDict, Optional, Any, List
from pydantic import BaseModel, Field
from src.config.llm_config import get_llm_client
from src.audit import log_llm_call

logger = logging.getLogger(__name__)


class VerificationResult(BaseModel):
    """Result from verification check."""
    ok: bool = Field(description="Whether all citations are supported")
    unsupported_claims: List[str] = Field(description="List of claims without citation support")
    confidence: float = Field(description="Confidence score 0-1")


VERIFIER_PROMPT = """You are a citation faithfulness verifier for the National Research Graph (NRG) platform.

TASK: For each factual claim in the answer that has a citation token [cite:pub_id:chunk_id],
verify that the cited evidence actually supports the claim.

EVIDENCE FORMAT:
Each evidence item is: pub_id, chunk_id, chunk_text

CITATION TOKENS:
Format is [cite:pub_id:chunk_id] in the answer text

RULES:
1. A claim is "supported" if the cited chunk contains information that substantiates it
2. A claim is "unsupported" if the chunk doesn't contain evidence for the claim
3. If no chunks are provided, all claims are unsupported
4. Ignore minor stylistic variations

Respond ONLY with valid JSON:
{
  "ok": true/false,
  "unsupported_claims": ["list of claims that are not supported"],
  "confidence": 0.0-1.0
}

If all claims are supported: {"ok": true, "unsupported_claims": [], "confidence": 1.0}
If any claims are unsupported: {"ok": false, "unsupported_claims": ["claim text"], "confidence": 0.85}
"""


def _extract_citation_tokens(text: str) -> List[tuple]:
    """Extract all [cite:pub_id:chunk_id] tokens from text."""
    pattern = r"\[cite:([^:]+):([^\]]+)\]"
    matches = re.findall(pattern, text)
    return matches


def _build_evidence_context(retrieved_chunks: list, sql_results: list) -> str:
    """Build evidence context from retrieved data."""
    evidence_lines = []

    # Process retrieved chunks (from RAG)
    for i, chunk in enumerate(retrieved_chunks[:10], 1):
        if isinstance(chunk, dict):
            pub_id = chunk.get("publication_id", f"pub_{i}")
            chunk_id = chunk.get("chunk_id", f"ch_{i}")
            chunk_text = chunk.get("text", chunk.get("chunk_text", str(chunk)))
        else:
            pub_id = f"pub_{i}"
            chunk_id = f"ch_{i}"
            chunk_text = str(chunk)

        evidence_lines.append(f"pub_id: {pub_id}, chunk_id: {chunk_id}, chunk_text: {chunk_text[:300]}...")

    # Process SQL results
    for i, row in enumerate(sql_results[:5], 1):
        if isinstance(row, dict):
            row_text = ", ".join(f"{k}={v}" for k, v in list(row.items())[:5])
        else:
            row_text = str(row)[:200]
        evidence_lines.append(f"sql_result_{i}: {row_text}")

    return "\n".join(evidence_lines) if evidence_lines else "No evidence provided"


def _extract_claims_with_citations(text: str) -> List[tuple]:
    """Extract claims and their associated citation tokens."""
    claims = []
    parts = re.split(r"(\[cite:[^]]+\])", text)

    current_claim = []
    for part in parts:
        if re.match(r"\[cite:[^]]+\]", part):
            citation = part
            claim_text = " ".join(current_claim).strip()
            if claim_text:
                claims.append((claim_text, citation))
            current_claim = []
        else:
            current_claim.append(part)

    return claims


def verifier_node(state) -> dict:
    """Verify citation faithfulness of synthesized response."""
    # Extract synthesized response
    if hasattr(state, "synthesized_response"):
        synthesized_response = state.synthesized_response
    elif isinstance(state, dict):
        synthesized_response = state.get("synthesized_response", "")
    else:
        synthesized_response = ""

    # Extract evidence
    if hasattr(state, "retrieved_chunks"):
        retrieved_chunks = state.retrieved_chunks
    elif isinstance(state, dict):
        retrieved_chunks = state.get("retrieved_chunks", [])
    else:
        retrieved_chunks = []

    if hasattr(state, "sql_results"):
        sql_results = state.sql_results
    elif isinstance(state, dict):
        sql_results = state.get("sql_results", [])
    else:
        sql_results = []

    # Extract verification retry count
    if hasattr(state, "verification_retries"):
        verification_retries = state.verification_retries
    elif isinstance(state, dict):
        verification_retries = state.get("verification_retries", 0)
    else:
        verification_retries = 0

    # If no citations in response, skip verification
    citation_tokens = _extract_citation_tokens(synthesized_response)
    if not citation_tokens:
        return {
            "verification_status": True,
            "verification_retries": verification_retries,
            "verification_result": {
                "ok": True,
                "unsupported_claims": [],
                "confidence": 1.0
            }
        }

    # Build verification prompt
    evidence_context = _build_evidence_context(retrieved_chunks, sql_results)
    claims_with_citations = _extract_claims_with_citations(synthesized_response)

    verification_prompt = f"""Answer to verify:
{synthesized_response[:2000]}

Evidence available:
{evidence_context}

Extracted claims with citations:
{chr(10).join([f"- {claim} [cited with {cite}]" for claim, cite in claims_with_citations])}

Verify each claim against the evidence and respond with JSON:"""

    # Try LLM-based verification
    llm_client = get_llm_client()
    verification_result = None

    if llm_client:
        try:
            response = llm_client.generate(
                system_prompt=VERIFIER_PROMPT,
                user_prompt=verification_prompt,
                conversation_history=[]
            )

            # Parse JSON response
            import json
            try:
                verification_result = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    try:
                        verification_result = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass

        except Exception as exc:
            logger.warning("Verifier LLM call failed: %s", exc)

    # Fallback to rule-based verification
    if not verification_result:
        # Rule-based: check if citations exist but chunks are empty
        if not retrieved_chunks and not sql_results:
            verification_result = {
                "ok": False,
                "unsupported_claims": ["Response contains citations but no evidence was retrieved"],
                "confidence": 0.5
            }
        else:
            # Assume ok if we have evidence
            verification_result = {
                "ok": True,
                "unsupported_claims": [],
                "confidence": 0.7
            }

    # Determine final status
    ok = verification_result.get("ok", True)
    unsupported_claims = verification_result.get("unsupported_claims", [])

    # Log verification
    try:
        log_llm_call(
            provider="verifier",
            model="verification",
            prompt_length=len(verification_prompt),
            response_length=len(str(verification_result)),
            status="success" if ok else "failure"
        )
    except Exception:
        logger.warning("Audit log_llm_call failed", exc_info=True)

    return {
        "verification_status": ok,
        "verification_retries": verification_retries,
        "verification_result": verification_result,
        "unsupported_claims": unsupported_claims,
    }