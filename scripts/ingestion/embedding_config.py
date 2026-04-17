#!/usr/bin/env python3
"""
Embedding Model Configuration and Management
"""

import logging
from typing import Dict, Any, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingModelConfig:
    """Configuration for embedding models"""

    DEFAULT_CONFIG = {
        "model_name": "sentence-transformers/all-mpnet-base-v2",
        "dimension": 768,
        "max_seq_length": 512,
        "batch_size": 256,
        "normalize": True,
        "device": "cpu",
        "precision": "float32",
    }

    AVAILABLE_MODELS = {
        "all-mpnet-base-v2": {
            "dimension": 768,
            "max_seq_length": 512,
            "description": "General purpose, high quality",
        },
        "all-MiniLM-L6-v2": {
            "dimension": 384,
            "max_seq_length": 256,
            "description": "Faster, smaller dimension",
        },
        "multi-qa-mpnet-base-dot-v1": {
            "dimension": 768,
            "max_seq_length": 512,
            "description": "Optimized for semantic search",
        },
        "e5-large-v2": {
            "dimension": 1024,
            "max_seq_length": 512,
            "description": "High quality, larger dimension",
        },
    }

    def __init__(self, model_name: str = None, **kwargs):
        self.config = self.DEFAULT_CONFIG.copy()

        if model_name:
            self.config["model_name"] = model_name

        # Update with any provided kwargs
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
            else:
                logger.warning(f"Unknown config parameter: {key}")

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config

    def set_batch_size(self, batch_size: int) -> None:
        """Set batch size for embedding"""
        if batch_size > 0:
            self.config["batch_size"] = batch_size
        else:
            logger.error(f"Invalid batch size: {batch_size}")

    def set_device(self, device: str) -> None:
        """Set device for embedding (cpu/cuda)"""
        if device in ["cpu", "cuda"]:
            self.config["device"] = device
        else:
            logger.error(f"Invalid device: {device}")

    def enable_normalization(self, normalize: bool) -> None:
        """Enable/disable embedding normalization"""
        self.config["normalize"] = normalize

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        model_name = self.config["model_name"].split("/")[-1]
        return self.AVAILABLE_MODELS.get(model_name, {})

    def to_json(self) -> str:
        """Export configuration to JSON"""
        return json.dumps(self.config, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "EmbeddingModelConfig":
        """Load configuration from JSON"""
        config = json.loads(json_str)
        return cls(**config)


if __name__ == "__main__":
    # Test configuration
    config = EmbeddingModelConfig("all-mpnet-base-v2", batch_size=128)

    logger.info("Current configuration:")
    logger.info(config.to_json())

    logger.info("\nModel info:")
    logger.info(json.dumps(config.get_model_info(), indent=2))
