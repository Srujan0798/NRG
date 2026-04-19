#!/usr/bin/env python3
"""
Database Seeding Script
Seeds the database with sample research data for testing and demo.
Matches the existing schema in nrg_research.db.
"""

import random
from datetime import datetime, timezone
from faker import Faker

from src.data.database import get_sqlite_connection

fake = Faker("en_IN")

# Indian institutions
INSTITUTIONS = [
    ("IIT Bombay", "Maharashtra", "IIT"),
    ("IIT Delhi", "Delhi", "IIT"),
    ("IIT Madras", "Tamil Nadu", "IIT"),
    ("IIT Kharagpur", "West Bengal", "IIT"),
    ("IIT Kanpur", "Uttar Pradesh", "IIT"),
    ("IIT Roorkee", "Uttarakhand", "IIT"),
    ("IIT Guwahati", "Assam", "IIT"),
    ("IIT Hyderabad", "Telangana", "IIT"),
    ("IIT Bangalore", "Karnataka", "IIT"),
    ("IIT Gandhinagar", "Gujarat", "IIT"),
    ("IIT Ropar", "Punjab", "IIT"),
    ("IIT Indore", "Madhya Pradesh", "IIT"),
    ("IIT Bhubaneswar", "Odisha", "IIT"),
    ("IIT Tirupati", "Andhra Pradesh", "IIT"),
    ("IIT Palakkad", "Kerala", "IIT"),
    ("IIT Jammu", "Jammu & Kashmir", "IIT"),
    ("NIT Trichy", "Tamil Nadu", "NIT"),
    ("NIT Surathkal", "Karnataka", "NIT"),
    ("NIT Warangal", "Telangana", "NIT"),
    ("NIT Calicut", "Kerala", "NIT"),
    ("IISc Bangalore", "Karnataka", "Institute"),
    ("JNCASR Bangalore", "Karnataka", "Institute"),
    ("TIFR Mumbai", "Maharashtra", "Institute"),
    ("IIIT Hyderabad", "Telangana", "IIIT"),
]

RESEARCH_AREAS = [
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "Quantum Computing",
    "Computer Vision",
    "Natural Language Processing",
    "Robotics",
    "Cybersecurity",
    "Blockchain",
    "Internet of Things",
    "5G Communications",
    "Cloud Computing",
    "Edge Computing",
    "Data Science",
    "Big Data Analytics",
    "Bioinformatics",
    "Materials Science",
    "Nanotechnology",
    "Renewable Energy",
    "Electric Vehicles",
    "Aerospace Engineering",
    "Biomedical Engineering",
    "Climate Science",
    "Water Resources",
    "Transportation Engineering",
]


def seed_institutions(conn):
    """Seed institutions."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    for inst_id, (name, state, inst_type) in enumerate(INSTITUTIONS, 1):
        institution_id = f"INST{inst_id:03d}"
        founded_year = random.randint(1950, 2020)
        website = f"www.{name.lower().replace(' ', '').replace('.', '')}.ac.in"

        cursor.execute(
            """
            INSERT OR IGNORE INTO institutions 
            (institution_id, name, state, type, founded_year, website, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (institution_id, name, state, inst_type, founded_year, website, now, now),
        )

    conn.commit()
    print(f"✅ Seeded {len(INSTITUTIONS)} institutions")


def seed_researchers(conn, count=200):
    """Seed researchers."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    # Get institution IDs
    cursor.execute("SELECT institution_id FROM institutions")
    institution_ids = [row[0] for row in cursor.fetchall()]

    if not institution_ids:
        print("⚠️ No institutions found - seed institutions first")
        return

    seeded = 0
    for i in range(count):
        researcher_id = f"RES{1000 + i}"
        name = fake.name()
        institution_id = random.choice(institution_ids)
        state = random.choice([inst[1] for inst in INSTITUTIONS])
        research_area = random.choice(RESEARCH_AREAS)
        year_joined = random.randint(2000, 2024)
        email = f"{name.lower().replace(' ', '.')}@{random.choice(['iit.ac.in', 'nit.ac.in'])}"
        phone = f"+91{random.randint(6000000000, 9999999999)}"
        orcid = f"0000-000{random.randint(10000000, 99999999)}"

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO researchers
                (researcher_id, name, institution_id, state, research_area, 
                 year_joined, email, phone, orcid, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    researcher_id,
                    name,
                    institution_id,
                    state,
                    research_area,
                    year_joined,
                    email,
                    phone,
                    orcid,
                    now,
                    now,
                ),
            )
            seeded += 1
        except Exception:
            pass

    conn.commit()
    print(f"✅ Seeded {seeded} researchers")


def seed_publications(conn, count=500):
    """Seed publications."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT institution_id FROM institutions")
    institution_ids = [row[0] for row in cursor.fetchall()]

    seeded = 0
    for i in range(count):
        publication_id = f"PUB{i + 1000}"
        title = f"Research on {random.choice(RESEARCH_AREAS)}: {fake.catch_phrase()}"
        year = random.randint(2018, 2024)
        doi = f"10.1234/{fake.word()}.{random.randint(1000, 9999)}"
        abstract = fake.paragraph(nb_sentences=3)
        venue = random.choice(["IEEE Conference", "ACM Journal", "Nature", "Science"])

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO publications
                (publication_id, title, abstract, venue, year, doi, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    publication_id,
                    title,
                    abstract,
                    venue,
                    year,
                    doi,
                    now,
                    now,
                ),
            )
            seeded += 1
        except Exception:
            pass

    conn.commit()
    print(f"✅ Seeded {seeded} publications")


def seed_labs(conn, count=50):
    """Seed research labs."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT institution_id FROM institutions")
    institution_ids = [row[0] for row in cursor.fetchall()]

    lab_names = [
        "AI & Machine Learning Lab",
        "Quantum Computing Lab",
        "Robotics Lab",
        "Cybersecurity Lab",
        "Data Science Lab",
        "Blockchain Lab",
        "IoT Lab",
        "5G Communications Lab",
        "Cloud Computing Lab",
        "Biomedical Engineering Lab",
        "Renewable Energy Lab",
        "Materials Science Lab",
    ]

    seeded = 0
    for i in range(count):
        lab_id = f"LAB{i + 100}"
        name = random.choice(lab_names)
        institution_id = random.choice(institution_ids) if institution_ids else None
        research_area = random.choice(RESEARCH_AREAS)
        established_year = random.randint(2000, 2020)

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO labs
                (lab_id, name, institution_id, research_area, established_year, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (lab_id, name, institution_id, research_area, established_year, now, now),
            )
            seeded += 1
        except Exception:
            pass

    conn.commit()
    print(f"✅ Seeded {seeded} labs")


def seed_funding(conn, count=100):
    """Seed funding data."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT institution_id FROM institutions")
    institution_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT researcher_id FROM researchers LIMIT 30")
    researcher_ids = [row[0] for row in cursor.fetchall()]

    agencies = ["DST", "DBT", "DRDO", "ISRO", "ICMR", "CSIR", "UGC", "AICTE"]
    statuses = ["active", "completed", "ongoing"]

    seeded = 0
    for i in range(count):
        funding_id = f"FUN{i + 1000}"
        project_title = f"Project on {random.choice(RESEARCH_AREAS)}"
        researcher_id = random.choice(researcher_ids) if researcher_ids else None
        institution_id = random.choice(institution_ids) if institution_ids else None
        funding_amount = random.randint(10, 500) * 100000
        funding_agency = random.choice(agencies)
        start_date = f"{random.randint(2018, 2023)}-01-01"
        end_date = f"{random.randint(2020, 2026)}-12-31"
        status = random.choice(statuses)

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO funding_records 
                (funding_id, researcher_id, institution_id, agency, amount, 
                 start_date, end_date, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    funding_id,
                    researcher_id,
                    institution_id,
                    funding_agency,
                    funding_amount,
                    start_date,
                    end_date,
                    project_title,
                    now,
                    now,
                ),
            )
            seeded += 1
        except Exception:
            pass

    conn.commit()
    print(f"✅ Seeded {seeded} funding records")


def get_stats(conn):
    """Get database statistics."""
    cursor = conn.cursor()

    tables = ["researchers", "institutions", "publications", "labs", "funding_records"]

    print("\n📊 Database Statistics:")
    print("-" * 40)
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  {table}: {count:,}")
        except:
            pass


def main(db_path="nrg_research.db"):
    """Main seeding function."""
    print(f"🌱 Starting database seeding: {db_path}")
    print("=" * 50)

    conn = get_sqlite_connection(db_path)

    try:
        seed_institutions(conn)
        seed_researchers(conn, count=200)
        seed_publications(conn, count=500)
        seed_labs(conn, count=50)
        seed_funding(conn, count=100)

        get_stats(conn)

        print("\n✅ Database seeding complete!")

    except Exception as e:
        print(f"❌ Seeding error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "nrg_research.db"
    main(db_path)
