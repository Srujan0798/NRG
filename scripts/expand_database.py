#!/usr/bin/env python3
"""Expand database to full 2,500 researcher dataset."""

import random
from datetime import datetime, timezone
from faker import Faker

from src.data.database import get_sqlite_connection

fake = Faker("en_IN")

# Extended data
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Jammu & Kashmir", "Ladakh", "Puducherry",
]

RESEARCH_AREAS = [
    "AI", "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "Robotics", "Quantum Computing", "Cybersecurity", "Blockchain",
    "IoT", "Data Science", "Bioinformatics", "Cloud Computing",
    "Edge Computing", "5G", "Renewable Energy", "Electric Vehicles",
    "Materials Science", "Nanotechnology", "Biomedical Engineering",
]

INSTITUTIONS = [
    "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kharagpur", "IIT Kanpur",
    "IIT Roorkee", "IIT Guwahati", "IIT Hyderabad", "IIT Indore", "IIT Bhubaneswar",
    "IIT Gandhinagar", "IIT Ropar", "IIT Patna", "IIT Jodhpur", "IIT Mandi",
    "IIT Indore", "IIT Varanasi", "IIT Dharwad", "IIT Palakkad", "IIT Tirupati",
    "IIT Bhilai", "IIT Goa", "IIT Jammu", "IIT Dhanbad", 
    "NIT Trichy", "NIT Surathkal", "NIT Warangal", "NIT Calicut", "NIT Rourkela",
    "NIT Kurukshetra", "NIT Durgapur", "NIT Jaipur", "NIT Allahabad", "NIT Nagpur",
    "IISc Bangalore", "JNCASR Bangalore", "TIFR Mumbai", "TIFR Bangalore",
    "IIIT Hyderabad", "IIIT Bangalore", "IIIT Delhi", "IIIT Allahabad",
]


def get_institution_state(inst_name):
    """Get state for institution."""
    state_map = {
        "Bombay": "Maharashtra", "Delhi": "Delhi", "Madras": "Tamil Nadu",
        "Kharagpur": "West Bengal", "Kanpur": "Uttar Pradesh", "Roorkee": "Uttarakhand",
        "Guwahati": "Assam", "Hyderabad": "Telangana", "Indore": "Madhya Pradesh",
        "Bhubaneswar": "Odisha", "Gandhinagar": "Gujarat", "Ropar": "Punjab",
        "Patna": "Bihar", "Jodhpur": "Rajasthan", "Mandi": "Himachal Pradesh",
        "Varanasi": "Uttar Pradesh", "Dharwad": "Karnataka", "Palakkad": "Kerala",
        "Tirupati": "Andhra Pradesh", "Bhilai": "Chhattisgarh", "Goa": "Goa",
        "Jammu": "Jammu & Kashmir", "Dhanbad": "Jharkhand", "Trichy": "Tamil Nadu",
        "Surathkal": "Karnataka", "Warangal": "Telangana", "Calicut": "Kerala",
        "Rourkela": "Odisha", "Kurukshetra": "Haryana", "Durgapur": "West Bengal",
        "Jaipur": "Rajasthan", "Allahabad": "Uttar Pradesh", "Nagpur": "Maharashtra",
        "Bangalore": "Karnataka", "Mumbai": "Maharashtra",
    }
    for key, state in state_map.items():
        if key in inst_name:
            return state
    return random.choice(INDIAN_STATES)


def expand_researchers(conn, target_count=2500):
    """Expand researchers to target count."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    # Get current count
    cursor.execute("SELECT COUNT(*) FROM researchers")
    current_count = cursor.fetchone()[0]
    
    if current_count >= target_count:
        print(f"✅ Already have {current_count} researchers (target: {target_count})")
        return
    
    # Get institution IDs
    cursor.execute("SELECT institution_id FROM institutions")
    inst_ids = [row[0] for row in cursor.fetchall()]
    
    if not inst_ids:
        print("⚠️ No institutions found")
        return
    
    # Generate additional researchers
    to_add = target_count - current_count
    added = 0
    
    for i in range(to_add):
        researcher_id = f"RES{current_count + i + 1000}"
        name = fake.name()
        institution_id = random.choice(inst_ids)
        state = random.choice(INDIAN_STATES)
        research_area = random.choice(RESEARCH_AREAS)
        year_joined = random.randint(1990, 2024)
        email = f"{name.lower().replace(' ', '.').replace('.', '')}@{random.choice(['iit.ac.in', 'nit.ac.in', 'iisc.ac.in'])}"
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
                (researcher_id, name, institution_id, state, research_area,
                 year_joined, email, phone, orcid, now, now),
            )
            added += 1
            if added % 500 == 0:
                print(f"  Added {added}/{to_add} researchers...")
        except Exception as e:
            print(f"  Error adding researcher: {e}")
    
    conn.commit()
    print(f"✅ Added {added} researchers")


def expand_publications(conn, target_count=2500):
    """Expand publications to target count."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("SELECT COUNT(*) FROM publications")
    current_count = cursor.fetchone()[0]
    
    if current_count >= target_count:
        print(f"✅ Already have {current_count} publications")
        return
    
    to_add = target_count - current_count
    added = 0
    
    for i in range(to_add):
        publication_id = f"PUB{current_count + i + 1000}"
        title = f"{fake.catch_phrase()}: {random.choice(RESEARCH_AREAS)} Research"
        year = random.randint(2015, 2024)
        doi = f"10.{random.randint(1000, 9999)}/{fake.word()}.{random.randint(1000, 9999)}"
        abstract = fake.paragraph(nb_sentences=3)
        venue = random.choice(["IEEE", "ACM", "Nature", "Science", "Springer", "Elsevier"])
        
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO publications
                (publication_id, title, abstract, venue, year, doi, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (publication_id, title, abstract, venue, year, doi, now, now),
            )
            added += 1
            if added % 500 == 0:
                print(f"  Added {added}/{to_add} publications...")
        except Exception as e:
            pass
    
    conn.commit()
    print(f"✅ Added {added} publications")


def expand_funding(conn, target_count=1000):
    """Expand funding records to target count."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("SELECT COUNT(*) FROM funding_records")
    current_count = cursor.fetchone()[0]
    
    if current_count >= target_count:
        print(f"✅ Already have {current_count} funding records")
        return
    
    # Get IDs
    cursor.execute("SELECT institution_id FROM institutions")
    inst_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT researcher_id FROM researchers LIMIT 100")
    researcher_ids = [row[0] for row in cursor.fetchall()]
    
    agencies = ["DST", "DBT", "DRDO", "ISRO", "ICMR", "CSIR", "UGC", "AICTE", "SERB"]
    statuses = ["active", "completed", "ongoing"]
    
    to_add = target_count - current_count
    added = 0
    
    for i in range(to_add):
        funding_id = f"FUN{current_count + i + 1000}"
        title = f"{random.choice(RESEARCH_AREAS)} Research Project"
        researcher_id = random.choice(researcher_ids) if researcher_ids else None
        institution_id = random.choice(inst_ids) if inst_ids else None
        amount = random.randint(10, 500) * 100000
        agency = random.choice(agencies)
        start = f"{random.randint(2015, 2023)}-01-01"
        end = f"{random.randint(2018, 2026)}-12-31"
        status = random.choice(statuses)
        
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO funding_records
                (funding_id, researcher_id, institution_id, agency, amount,
                 start_date, end_date, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (funding_id, researcher_id, institution_id, agency, amount,
                 start, end, title, now, now),
            )
            added += 1
        except Exception:
            pass
    
    conn.commit()
    print(f"✅ Added {added} funding records")


def get_stats(conn):
    """Get database statistics."""
    cursor = conn.cursor()
    tables = ["researchers", "institutions", "publications", "labs", "funding_records"]
    
    print("\n📊 Database Statistics:")
    print("-" * 40)
    total = 0
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,}")
            total += count
        except:
            pass
    print(f"  TOTAL: {total:,} records")


def main(db_path="nrg_research.db"):
    """Main expansion function."""
    print(f"🌱 Expanding database: {db_path}")
    print("=" * 50)
    
    conn = get_sqlite_connection(db_path)
    
    try:
        expand_researchers(conn, target_count=2500)
        expand_publications(conn, target_count=2500)
        expand_funding(conn, target_count=1000)
        get_stats(conn)
        
        print("\n✅ Database expansion complete!")
        
    except Exception as e:
        print(f"❌ Expansion error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "nrg_research.db"
    main(db_path)
