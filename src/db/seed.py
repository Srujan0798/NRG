"""Database seeding script."""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    """Seed the database with sample data."""
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
            
            # Seed is handled by Docker init script
            # This is a placeholder for programmatic seeding if needed
            logger.info("Database seeding complete")
            
    except Exception as e:
        logger.warning(f"Could not seed database: {e}")
        logger.info("Run 'make seed' after services are up")


def main():
    seed_database()


if __name__ == "__main__":
    main()