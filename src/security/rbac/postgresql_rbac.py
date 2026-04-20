#!/usr/bin/env python3
"""
RBAC Implementation for PostgreSQL Database Level Security
Production-grade implementation of access control for NRG dataset
"""

import logging
import sys
from typing import Any


# PostgreSQL driver
try:
    import psycopg2
except ImportError:
    print("psycopg2 package not available. Install with: pip install psycopg2")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("postgresql_rbac.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class PostgreSQLRBAC:
    """Production-grade RBAC implementation for PostgreSQL"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection: Any = None
        self.connect()

    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(self.connection_string)
            logger.info("Successfully connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Closed PostgreSQL connection")

    def setup_rls_policies(self) -> None:
        """Set up Row Level Security policies for all tables"""
        try:
            with self.connection.cursor() as cursor:
                # Enable RLS on all tables
                tables = [
                    "researchers",
                    "institutions",
                    "publications",
                    "funding_records",
                    "labs",
                    "keywords",
                ]

                for table in tables:
                    # Enable RLS
                    cursor.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
                    logger.info(f"Enabled RLS for table: {table}")

                # Create RLS policies
                self._create_researchers_policy(cursor)
                self._create_institutions_policy(cursor)
                self._create_publications_policy(cursor)
                self._create_funding_policy(cursor)
                self._create_labs_policy(cursor)
                self._create_keywords_policy(cursor)

                # Commit changes
                self.connection.commit()
                logger.info("Committed RLS policy changes")

        except Exception as e:
            logger.error(f"Failed to set up RLS policies: {e}")
            self.connection.rollback()
            raise

    def _create_researchers_policy(self, cursor) -> None:
        """Create RLS policies for researchers table"""
        # Create policies for each access tier
        policies = [
            # Tier 1: Full access
            """
            CREATE POLICY researchers_tier1_policy ON researchers 
            FOR ALL TO researchers_tier1_group 
            USING (access_tier = 1);
            """,
            # Tier 2: Limited access
            """
            CREATE POLICY researchers_tier2_policy ON researchers 
            FOR ALL TO researchers_tier2_group 
            USING (access_tier <= 2);
            """,
            # Tier 3: Public access
            """
            CREATE POLICY researchers_tier3_policy ON researchers 
            FOR ALL TO researchers_tier3_group 
            USING (access_tier <= 3);
            """,
        ]

        for policy in policies:
            cursor.execute(policy)

    def _create_institutions_policy(self, cursor) -> None:
        """Create RLS policies for institutions table"""
        # Similar policies for institutions table
        policies = [
            # Tier 1: Full access
            """
            CREATE POLICY institutions_tier1_policy ON institutions 
            FOR ALL TO institutions_tier1_group 
            USING (access_tier = 1);
            """,
            # Tier 2: Limited access
            """
            CREATE POLICY institutions_tier2_policy ON institutions 
            FOR ALL TO institutions_tier2_group 
            USING (access_tier <= 2);
            """,
            # Tier 3: Public access
            """
            CREATE POLICY institutions_tier3_policy ON institutions 
            FOR ALL TO institutions_tier3_group 
            USING (access_tier <= 3);
            """,
        ]

        for policy in policies:
            cursor.execute(policy)

    def _create_publications_policy(self, cursor) -> None:
        """Create RLS policies for publications table"""
        # Similar policies for publications table
        policies = [
            # Tier 1: Full access
            """
            CREATE POLICY publications_tier1_policy ON publications 
            FOR ALL TO publications_tier1_group 
            USING (access_tier = 1);
            """,
            # Tier 2: Limited access
            """
            CREATE POLICY publications_tier2_policy ON publications 
            FOR ALL TO publications_tier2_group 
            USING (access_tier <= 2);
            """,
            # Tier 3: Public access
            """
            CREATE POLICY publications_tier3_policy ON publications 
            FOR ALL TO publications_tier3_group 
            USING (access_tier <= 3);
            """,
        ]

        for policy in policies:
            cursor.execute(policy)

    def _create_funding_policy(self, cursor) -> None:
        """Create RLS policies for funding records table"""
        # Similar policies for funding records table
        policies = [
            # Tier 1: Full access
            """
            CREATE POLICY funding_tier1_policy ON funding_records 
            FOR ALL TO funding_tier1_group 
            USING (access_tier = 1);
            """,
            # Tier 2: Limited access
            """
            CREATE POLICY funding_t1_policy ON funding_records 
            FOR ALL TO funding_tier2_group 
            USING (access_tier <= 2);
            """,
            # Tier 3: Public access
            """
            CREATE POLICY funding_tier3_policy ON funding_records 
            FOR ALL TO funding_tier3_group 
            USING (access_tier <= 3);
            """,
        ]

        for policy in policies:
            cursor.execute(policy)

    def _create_labs_policy(self, cursor) -> None:
        """Create RLS policies for labs table"""
        # Similar policies for labs table
        policies = [
            # Tier 1: Full access
            """
            CREATE POLICY labs_tier1_policy ON labs 
            FOR ALL TO labs_tier1_group 
            USING (access_tier = 1);
            """,
            # Tier 2: Limited access
            """
            CREATE POLICY labs_tier2_policy ON labs 
            FOR ALL TO labs_tier2_group 
            USING (access_tier <= 2);
            """,
            # Tier 3: Public access
            """
            CREATE POLICY labs_tier3_policy ON labs 
            FOR ALL TO labs_tier3_group 
            USING (access_tier <= 3);
            """,
        ]

        for policy in policies:
            cursor.execute(policy)

    def _create_keywords_policy(self, cursor) -> None:
        """Create RLS policies for keywords table"""
        # Similar policies for keywords table
        policies = [
            # Tier 1: Full access
            """
            CREATE POLICY keywords_tier1_policy ON keywords 
            FOR ALL TO keywords_tier1_group 
            USING (access_tier = 1);
            """,
            # Tier 2: Limited access
            """
            CREATE POLICY keywords_tier2_policy ON keywords 
            FOR ALL TO keywords_tier2_group 
            USING (access_tier <= 2);
            """,
            # Tier 3: Public access
            """
            CREATE POLICY keywords_tier3_policy ON keywords 
            FOR ALL TO keywords_tier3_group 
            USING (access_tier <= 3);
            """,
        ]

        for policy in policies:
            cursor.execute(policy)

    def setup_user_groups(self) -> None:
        """Set up database user groups for RBAC"""
        try:
            with self.connection.cursor() as cursor:
                # Create user groups for each tier
                groups = [
                    "researchers_tier1_group",
                    "researchers_tier2_group",
                    "researchers_tier3_group",
                    "institutions_tier1_group",
                    "institutions_tier2_group",
                    "institutions_tier3_group",
                    "publications_tier1_group",
                    "publications_tier2_group",
                    "publications_tier3_group",
                    "funding_tier1_group",
                    "funding_tier2_group",
                    "funding_tier3_group",
                    "labs_tier1_group",
                    "labs_tier2_group",
                    "labs_tier3_group",
                    "keywords_tier1_group",
                    "keywords_tier2_group",
                    "keywords_tier3_group",
                ]

                for group in groups:
                    cursor.execute(f"CREATE ROLE {group} NOLOGIN;")

                # Commit changes
                self.connection.commit()
                logger.info("Created user groups for RBAC")

        except Exception as e:
            logger.error(f"Failed to set up user groups: {e}")
            self.connection.rollback()
            raise


def main():
    """Main function for setting up PostgreSQL RBAC"""
    import argparse

    parser = argparse.ArgumentParser(description="Set up PostgreSQL RBAC policies")
    parser.add_argument(
        "--connection-string", required=True, help="PostgreSQL connection string"
    )
    parser.add_argument("--setup", action="store_true", help="Set up RBAC policies")
    parser.add_argument(
        "--env", default="development", help="Environment (development/production)"
    )

    args = parser.parse_args()

    # Create RBAC instance
    rbac = PostgreSQLRBAC(args.connection_string)

    try:
        if args.setup:
            logger.info("Setting up RBAC policies...")
            rbac.setup_user_groups()
            rbac.setup_rls_policies()
            logger.info("RBAC policies set up successfully")
        else:
            logger.info("RBAC setup not requested")

    except Exception as e:
        logger.error(f"Error setting up RBAC: {e}")
        sys.exit(1)
    finally:
        rbac.close()


if __name__ == "__main__":
    main()
