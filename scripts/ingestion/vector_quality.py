#!/usr/bin/env python3
"""
Vector Quality Assurance for Embedding Validation
Ensures embedding quality and consistency
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorQualityAssurance:
    """Quality assurance for vector embeddings"""

    def __init__(self):
        self.expected_dimension = 768  # all-mpnet-base-v2
        self.quality_thresholds = {
            "min_norm": 0.1,
            "max_norm": 10.0,
            "min_variance": 1e-6,
        }

    def validate_embedding_shape(self, embedding: np.ndarray) -> bool:
        """Validate embedding has correct shape"""
        if not isinstance(embedding, np.ndarray):
            logger.error(f"Embedding is not numpy array: {type(embedding)}")
            return False

        if len(embedding.shape) != 1:
            logger.error(f"Embedding has wrong shape: {embedding.shape}")
            return False

        if embedding.shape[0] != self.expected_dimension:
            logger.error(f"Embedding has wrong dimension: {embedding.shape[0]}")
            return False

        return True

    def validate_embedding_values(self, embedding: np.ndarray) -> bool:
        """Validate embedding values are valid"""
        if np.any(np.isnan(embedding)):
            logger.error("Embedding contains NaN values")
            return False

        if np.any(np.isinf(embedding)):
            logger.error("Embedding contains infinite values")
            return False

        return True

    def validate_embedding_norm(self, embedding: np.ndarray) -> bool:
        """Validate embedding norm is within acceptable range"""
        norm = np.linalg.norm(embedding)

        if norm < self.quality_thresholds["min_norm"]:
            logger.warning(f"Embedding norm too small: {norm}")
            return False

        if norm > self.quality_thresholds["max_norm"]:
            logger.warning(f"Embedding norm too large: {norm}")
            return False

        return True

    def validate_embedding_variance(self, embedding: np.ndarray) -> bool:
        """Validate embedding has sufficient variance"""
        variance = np.var(embedding)

        if variance < self.quality_thresholds["min_variance"]:
            logger.warning(f"Embedding variance too low: {variance}")
            return False

        return True

    def validate_embedding(self, embedding: np.ndarray) -> Tuple[bool, List[str]]:
        """Full validation of embedding"""
        errors = []

        if not self.validate_embedding_shape(embedding):
            errors.append("Invalid shape")

        if not self.validate_embedding_values(embedding):
            errors.append("Invalid values")

        if not self.validate_embedding_norm(embedding):
            errors.append("Invalid norm")

        if not self.validate_embedding_variance(embedding):
            errors.append("Low variance")

        is_valid = len(errors) == 0
        return is_valid, errors

    def batch_validate_embeddings(self, embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Validate a batch of embeddings"""
        results = {"total": len(embeddings), "valid": 0, "invalid": 0, "errors": []}

        for i, embedding in enumerate(embeddings):
            is_valid, errors = self.validate_embedding(embedding)

            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].append({"index": i, "errors": errors})

        logger.info(
            f"Validated {results['total']} embeddings: "
            f"{results['valid']} valid, {results['invalid']} invalid"
        )

        return results


if __name__ == "__main__":
    qa = VectorQualityAssurance()

    # Test embedding validation
    test_embedding = np.random.rand(768).astype(np.float32)
    is_valid, errors = qa.validate_embedding(test_embedding)
    logger.info(f"Embedding valid: {is_valid}, Errors: {errors}")
