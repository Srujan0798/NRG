"""
Access Control Labels for NRG Dataset
Defines access tiers and labeling logic for data elements
"""

from enum import IntEnum
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AccessTier(IntEnum):
    """Access tiers for NRG dataset"""

    TIER_1 = 1  # Full access - approved researchers, collaborators
    TIER_2 = 2  # Limited access - institutional members, verified users
    TIER_3 = 3  # Public access - aggregated data, metadata only


class AccessControlLabeler:
    """Labels data elements with appropriate access tiers"""

    def __init__(self):
        # Rules for determining access tier based on data characteristics
        self.tier_rules = {
            "sensitive_pii": ["email", "phone", "orcid", "home_address"],
            "restricted_contact": ["personal_email", "personal_phone"],
            "public_info": ["name", "affiliation", "publication_title", "abstract"],
            "aggregated_only": ["salary", "grant_amount_details", "personal_funding"],
        }

        # Default tiers for data types
        self.default_tiers: dict[str, AccessTier] = {
            "researcher_id": AccessTier.TIER_1,
            "institution": AccessTier.TIER_1,
            "name": AccessTier.TIER_2,
            "state": AccessTier.TIER_3,
            "research_area": AccessTier.TIER_3,
            "year_joined": AccessTier.TIER_2,
            "email": AccessTier.TIER_1,
            "phone": AccessTier.TIER_1,
            "orcid": AccessTier.TIER_1,
            "publication_title": AccessTier.TIER_3,
            "abstract": AccessTier.TIER_3,
            "venue": AccessTier.TIER_3,
            "year": AccessTier.TIER_3,
            "doi": AccessTier.TIER_3,
            "pmid": AccessTier.TIER_3,
            "funding_agency": AccessTier.TIER_3,
            "funding_amount": AccessTier.TIER_2,  # Aggregated amounts OK for tier 2
            "keyword": AccessTier.TIER_3,
            "lab_name": AccessTier.TIER_2,
            "lab_research_area": AccessTier.TIER_3,
        }

    def label_researcher_field(self, field_name: str, field_value: Any) -> AccessTier:
        """
        Determine access tier for a researcher field

        Args:
            field_name: Name of the field
            field_value: Value of the field

        Returns:
            Appropriate AccessTier
        """
        # Check if field contains sensitive PII
        if any(
            sensitive in field_name.lower()
            for sensitive in self.tier_rules["sensitive_pii"]
        ):
            return AccessTier.TIER_1

        # Check if field is restricted contact info
        if any(
            restricted in field_name.lower()
            for restricted in self.tier_rules["restricted_contact"]
        ):
            return AccessTier.TIER_1

        # Check default tier
        if field_name in self.default_tiers:
            return self.default_tiers[field_name]

        # Default to tier 1 for unknown fields (conservative approach)
        logger.warning(
            f"No access tier rule for field '{field_name}', defaulting to TIER_1"
        )
        return AccessTier.TIER_1

    def label_publication_field(self, field_name: str, field_value: Any) -> AccessTier:
        """
        Determine access tier for a publication field

        Args:
            field_name: Name of the field
            field_value: Value of the field

        Returns:
            Appropriate AccessTier
        """
        # Most publication metadata is public
        if field_name in ["title", "abstract", "venue", "year", "doi", "pmid"]:
            return AccessTier.TIER_3

        # Author information might be restricted
        if "author" in field_name.lower():
            return AccessTier.TIER_2

        # Default to public
        return AccessTier.TIER_3

    def label_funding_field(self, field_name: str, field_value: Any) -> AccessTier:
        """
        Determine access tier for a funding field

        Args:
            field_name: Name of the field
            field_value: Value of the field

        Returns:
            Appropriate AccessTier
        """
        # Agency and high-level info is public
        if field_name in ["agency", "title"]:
            return AccessTier.TIER_3

        # Amount details might be restricted
        if "amount" in field_name.lower():
            # Exact amounts restricted, but ranges OK for tier 2
            return AccessTier.TIER_2

        # Dates are generally OK
        if "date" in field_name.lower():
            return AccessTier.TIER_2

        # Default to restricted for unknown funding fields
        return AccessTier.TIER_2

    def create_access_label(
        self, source_table: str, field_name: str, field_value: Any = None
    ) -> Dict[str, Any]:
        """
        Create complete access label for a data element

        Args:
            source_table: Table name where data originates
            field_name: Field name
            field_value: Optional field value for context-based labeling

        Returns:
            Dictionary with access tier and labeling metadata
        """
        # Determine tier based on source table
        if source_table == "researchers":
            tier = self.label_researcher_field(field_name, field_value)
        elif source_table == "publications":
            tier = self.label_publication_field(field_name, field_value)
        elif source_table == "funding_records":
            tier = self.label_funding_field(field_name, field_value)
        elif source_table in ["institutions", "labs", "keywords"]:
            # Most institutional/lab info is tier 2 or 3
            tier = (
                AccessTier.TIER_2
                if field_name in ["name", "website"]
                else AccessTier.TIER_3
            )
        else:
            # Conservative default
            tier = AccessTier.TIER_1

        return {
            "access_tier": int(tier),
            "tier_name": tier.name,
            "source_table": source_table,
            "field_name": field_name,
            "labeling_rules_version": "1.0",
        }


def get_access_tier_description(tier: int) -> str:
    """Get human-readable description of access tier"""
    descriptions = {
        1: "Full access - approved researchers with data use agreements",
        2: "Limited access - institutional members, verified users, no PII",
        3: "Public access - aggregated statistics, metadata only",
    }
    return descriptions.get(tier, "Unknown access tier")


def validate_access_tier(tier: int) -> bool:
    """Validate that access tier is within valid range"""
    return tier in [1, 2, 3]


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    labeler = AccessControlLabeler()

    # Test researcher fields
    print("Researcher field labeling:")
    for field in ["researcher_id", "name", "email", "phone", "orcid", "state"]:
        tier = labeler.label_researcher_field(field, "test_value")
        print(f"  {field}: TIER_{tier} ({get_access_tier_description(tier)})")

    # Test publication fields
    print("\nPublication field labeling:")
    for field in ["title", "abstract", "year", "doi", "author_order"]:
        tier = labeler.label_publication_field(field, "test_value")
        print(f"  {field}: TIER_{tier} ({get_access_tier_description(tier)})")

    # Test funding fields
    print("\nFunding field labeling:")
    for field in ["agency", "amount", "title", "start_date"]:
        tier = labeler.label_funding_field(field, "test_value")
        print(f"  {field}: TIER_{tier} ({get_access_tier_description(tier)})")
