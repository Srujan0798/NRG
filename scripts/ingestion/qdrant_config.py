#!/usr/bin/env python3
"""
Qdrant Collection Manager for Production Deployment
"""

import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantCollectionManager:
    """Manage Qdrant collections for production"""

    def __init__(self):
        self.collections = {}

    def create_collection_config(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: str = "Cosine",
        shard_number: int = 4,
        replication_factor: int = 2,
    ) -> Dict[str, Any]:
        """Create configuration for Qdrant collection"""
        config = {
            "collection_name": collection_name,
            "vectors": {"size": vector_size, "distance": distance},
            "shard_number": shard_number,
            "replication_factor": replication_factor,
            "optimizers_config": {
                "indexing_threshold": 10000,
                "memmap_threshold": 50000,
            },
            "hnsw_config": {"m": 16, "ef_construct": 100},
        }

        self.collections[collection_name] = config
        return config

    def optimize_for_read_heavy(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize collection for read-heavy workloads"""
        config["hnsw_config"]["ef_construct"] = 200
        config["hnsw_config"]["m"] = 32
        config["optimizers_config"]["indexing_threshold"] = 5000
        return config

    def optimize_for_write_heavy(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize collection for write-heavy workloads"""
        config["hnsw_config"]["ef_construct"] = 50
        config["hnsw_config"]["m"] = 8
        config["optimizers_config"]["indexing_threshold"] = 20000
        return config

    def get_collection_config(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a collection"""
        return self.collections.get(collection_name)

    def list_collections(self) -> List[str]:
        """List all configured collections"""
        return list(self.collections.keys())


if __name__ == "__main__":
    manager = QdrantCollectionManager()

    # Create collection config
    config = manager.create_collection_config(
        collection_name="nrip_production", vector_size=768, shard_number=4
    )

    logger.info("Collection configuration:")
    import json

    logger.info(json.dumps(config, indent=2))
