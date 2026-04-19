#!/usr/bin/env python3
"""Seed relationship tables for nrg_research.db (SQLite MVP)."""

import random
from datetime import datetime, timezone

from src.data.database import get_sqlite_connection

# Curated keywords from ML/Physics/Bio/Chem/CS/SS ontologies
KEYWORDS = [
    "Machine Learning", "Deep Learning", "Neural Networks", "Computer Vision",
    "Natural Language Processing", "Reinforcement Learning", "Transfer Learning",
    "Supervised Learning", "Unsupervised Learning", "Generative AI",
    "Transformer", "BERT", "GPT", "LLM", "AI Ethics", "Explainable AI",
    "Quantum Computing", "Quantum Mechanics", "Condensed Matter Physics",
    "Particle Physics", "Optics", "Photonics", "Astrophysics", "Cosmology",
    "Bioinformatics", "Computational Biology", "Genomics", "Proteomics",
    "Systems Biology", "Synthetic Biology", "Biophysics", "Neuroscience",
    "Computational Chemistry", "Materials Science", "Nanotechnology",
    "Algorithms", "Distributed Systems", "Computer Networks", "Cybersecurity",
    "Cryptography", "Software Engineering", "Human-Computer Interaction",
    "Computational Social Science", "Digital Humanities", "Science Communication",
    "Robotics", "Control Systems", "Signal Processing", "VLSI Design",
    "IoT", "Smart Grid", "Renewable Energy", "Applied Mathematics",
    "Statistics", "Optimization", "Graph Theory", "Data Science",
    "Big Data", "Cloud Computing", "Edge Computing", "Blockchain",
    "Medical Imaging", "Health Informatics", "Biomedical Engineering",
]


def seed_relations(db_path: str = "nrg_research.db"):
    """Seed all relationship tables."""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    print("🌱 Seeding relationship tables...")

    # 1. Clear existing data
    print("  Clearing existing relations...")
    cursor.execute("DELETE FROM researcher_publications")
    cursor.execute("DELETE FROM publication_keywords")
    cursor.execute("DELETE FROM researcher_labs")
    cursor.execute("DELETE FROM keywords")
    conn.commit()

    # 2. Insert keywords
    print(f"  Inserting {len(KEYWORDS)} keywords...")
    for i, keyword in enumerate(KEYWORDS, 1):
        cursor.execute(
            "INSERT INTO keywords (keyword, created_at) VALUES (?, ?)",
            (keyword, now)
        )
    conn.commit()
    print(f"  ✅ Inserted {len(KEYWORDS)} keywords")

    # 3. Get all IDs
    cursor.execute("SELECT researcher_id FROM researchers")
    researcher_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT publication_id FROM publications")
    publication_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT lab_id FROM labs")
    lab_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT keyword_id FROM keywords")
    keyword_ids = [row[0] for row in cursor.fetchall()]

    print(f"  Found {len(researcher_ids)} researchers, {len(publication_ids)} publications, {len(lab_ids)} labs")

    # 4. Seed researcher_publications
    print("  Seeding researcher_publications...")
    rp_count = 0
    for researcher_id in researcher_ids:
        num_pubs = random.randint(2, min(5, len(publication_ids)))
        selected_pubs = random.sample(publication_ids, num_pubs)

        for pos, pub_id in enumerate(selected_pubs, 1):
            cursor.execute(
                "INSERT INTO researcher_publications (researcher_id, publication_id, author_order, created_at) VALUES (?, ?, ?, ?)",
                (researcher_id, pub_id, pos, now)
            )
            rp_count += 1

    conn.commit()
    print(f"  ✅ Inserted {rp_count} researcher_publications")

    # 5. Seed publication_keywords
    print("  Seeding publication_keywords...")
    pk_count = 0
    for pub_id in publication_ids:
        num_kw = random.randint(1, min(4, len(keyword_ids)))
        selected_kw = random.sample(keyword_ids, num_kw)

        for kw_id in selected_kw:
            cursor.execute(
                "INSERT INTO publication_keywords (publication_id, keyword_id, created_at) VALUES (?, ?, ?)",
                (pub_id, kw_id, now)
            )
            pk_count += 1

    conn.commit()
    print(f"  ✅ Inserted {pk_count} publication_keywords")

    # 6. Seed researcher_labs
    print("  Seeding researcher_labs...")
    rl_count = 0

    for lab_id in lab_ids:
        num_members = random.randint(3, min(8, len(researcher_ids)))
        members = random.sample(researcher_ids, num_members)

        for i, member_id in enumerate(members):
            role = "PI" if i == 0 else random.choice(["Researcher", "PhD Student", "Postdoc"])
            cursor.execute(
                "INSERT INTO researcher_labs (researcher_id, lab_id, start_date, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (member_id, lab_id, now, role, now)
            )
            rl_count += 1

    conn.commit()
    print(f"  ✅ Inserted {rl_count} researcher_labs")

    # 7. Verify counts
    print("\n📊 Final counts:")
    cursor.execute("SELECT COUNT(*) FROM researcher_publications")
    print(f"  researcher_publications: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM keywords")
    print(f"  keywords: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM publication_keywords")
    print(f"  publication_keywords: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM researcher_labs")
    print(f"  researcher_labs: {cursor.fetchone()[0]}")

    # 8. Mark as seeded
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT
        )
    """)
    cursor.execute(
        "INSERT OR REPLACE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        ("seed_relations_001", now)
    )
    conn.commit()

    conn.close()
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    seed_relations()
