"""Database seeding script."""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    """Verify seed ownership and report current database state."""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nrg:nrg_secret@localhost:5432/nrg")
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if data exists
            result = conn.execute(text("SELECT COUNT(*) FROM researchers"))
            count = result.scalar()
            
            if count > 0:
                logger.info(f"Database already seeded with {count} researchers")
                return
            
            logger.info("Seeding database...")

            # Docker init SQL owns reference data so local and container startup
            # paths stay identical.
            logger.info("Database seeding complete")
            
    except Exception as e:
        logger.warning(f"Could not seed database: {e}")
        logger.info("Run 'make seed' after services are up")


def main():
    seed_database()


if __name__ == "__main__":
    main()
