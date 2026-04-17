#!/usr/bin/env python3
"""
Metadata Enrichment for Vector Embeddings
Adds access control and contextual metadata to embeddings
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetadataEnricher:
    """Enrich embedding metadata with access control and context"""

    def __init__(self):
        self.access_tier_rules = {"public": 3, "internal": 2, "restricted": 1}

    def enrich_with_access_tier(
        self, metadata: Dict[str, Any], access_level: str = "public"
    ) -> Dict[str, Any]:
        """Add access tier to metadata"""
        tier = self.access_tier_rules.get(access_level, 3)
        metadata["access_tier"] = tier
        metadata["access_level"] = access_level
        return metadata

    def enrich_with_source_info(
        self,
        metadata: Dict[str, Any],
        source_id: str,
        source_table: str,
        source_field: str,
    ) -> Dict[str, Any]:
        """Add source information to metadata"""
        metadata["source_id"] = source_id
        metadata["source_table"] = source_table
        metadata["source_field"] = source_field
        metadata["ingestion_timestamp"] = datetime.utcnow().isoformat()
        return metadata

    def enrich_with_institution_context(
        self, metadata: Dict[str, Any], institution: str, state: str
    ) -> Dict[str, Any]:
        """Add institution context to metadata"""
        metadata["institution"] = institution
        metadata["state"] = state
        return metadata

    def enrich_with_research_context(
        self, metadata: Dict[str, Any], research_area: str, year: int
    ) -> Dict[str, Any]:
        """Add research context to metadata"""
        metadata["research_area"] = research_area
        metadata["year"] = year
        return metadata

    def create_full_metadata(
        self,
        source_id: str,
        source_table: str,
        source_field: str,
        institution: str,
        state: str,
        research_area: str,
        year: int,
        access_level: str = "public",
        chunk_index: int = 0,
    ) -> Dict[str, Any]:
        """Create complete metadata for an embedding"""
        metadata = {}

        # Add access tier
        metadata = self.enrich_with_access_tier(metadata, access_level)

        # Add source info
        metadata = self.enrich_with_source_info(
            metadata, source_id, source_table, source_field
        )

        # Add institution context
        metadata = self.enrich_with_institution_context(metadata, institution, state)

        # Add research context
        metadata = self.enrich_with_research_context(metadata, research_area, year)

        # Add chunk index
        metadata["chunk_index"] = chunk_index

        # Add version
        metadata["metadata_version"] = "1.0"

        return metadata


if __name__ == "__main__":
    enricher = MetadataEnricher()

    # Test metadata enrichment
    metadata = enricher.create_full_metadata(
        source_id="res_001",
        source_table="researchers",
        source_field="bio",
        institution="MIT",
        state="MA",
        research_area="Machine Learning",
        year=2023,
        access_level="internal",
        chunk_index=0,
    )

    logger.info(f"Enriched metadata: {json.dumps(metadata, indent=2)}")
