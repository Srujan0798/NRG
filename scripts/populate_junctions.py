"""Populate empty junction/relationship tables in nrg_research.db."""

import random
from datetime import date

from src.data.database import get_sqlite_connection

DB_PATH = "nrg_research.db"

KEYWORDS = [
    "Machine Learning", "Robotics", "Natural Language Processing",
    "Quantum Computing", "Computer Vision", "Deep Learning",
    "Reinforcement Learning", "Neural Networks", "Data Mining",
    "Cybersecurity", "Blockchain", "Cloud Computing",
    "Edge Computing", "Internet of Things", "5G Networks",
    "Bioinformatics", "Genomics", "Drug Discovery",
    "Materials Science", "Nanotechnology", "Renewable Energy",
    "Electric Vehicles", "Autonomous Systems", "Signal Processing",
    "Graph Neural Networks", "Federated Learning", "Transfer Learning",
    "Explainable AI", "Generative Models", "Large Language Models",
    "Speech Recognition", "Image Segmentation", "Object Detection",
    "Time Series Analysis", "Optimization", "Bayesian Inference",
    "Climate Modeling", "Semiconductor Design", "Photonics",
    "Human-Computer Interaction", "Distributed Systems",
    "High Performance Computing", "Computational Biology",
    "Protein Folding", "Smart Grid",
]

# Map researcher research_area to relevant keyword indices for realistic links
AREA_KEYWORD_MAP = {
    "AI": [0, 5, 6, 7, 27, 28, 29],
    "Machine Learning": [0, 5, 6, 7, 8, 26, 27, 35],
    "Robotics": [1, 22, 23, 40],
    "NLP": [2, 29, 30],
    "Quantum Computing": [3, 34, 35],
    "Computer Vision": [4, 5, 32, 33],
    "Data Science": [0, 8, 34, 41],
    "Cybersecurity": [9, 10, 11, 41],
}


def main():
    random.seed(42)
    conn = get_sqlite_connection(DB_PATH)
    cur = conn.cursor()

    # ---------------------------------------------------------------
    # 1. Load existing IDs
    # ---------------------------------------------------------------
    researcher_rows = cur.execute(
        "SELECT researcher_id, research_area, institution_id FROM researchers"
    ).fetchall()
    publication_ids = [
        r[0] for r in cur.execute("SELECT publication_id FROM publications").fetchall()
    ]
    lab_rows = cur.execute(
        "SELECT lab_id, institution_id FROM labs"
    ).fetchall()

    print(f"Researchers: {len(researcher_rows)}, Publications: {len(publication_ids)}, Labs: {len(lab_rows)}")

    # ---------------------------------------------------------------
    # 2. Populate keywords
    # ---------------------------------------------------------------
    cur.execute("DELETE FROM publication_keywords")
    cur.execute("DELETE FROM keywords")
    cur.execute("DELETE FROM sqlite_sequence WHERE name='keywords'")

    for kw in KEYWORDS:
        cur.execute("INSERT INTO keywords (keyword) VALUES (?)", (kw,))
    conn.commit()

    keyword_count = cur.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    keyword_ids = [
        r[0] for r in cur.execute("SELECT keyword_id FROM keywords").fetchall()
    ]
    print(f"Inserted {keyword_count} keywords")

    # ---------------------------------------------------------------
    # 3. Populate researcher_publications
    #    Each researcher gets 2-5 publications; publications can have
    #    multiple authors (realistic).
    # ---------------------------------------------------------------
    cur.execute("DELETE FROM researcher_publications")

    pub_pool = list(publication_ids)  # copy
    random.shuffle(pub_pool)
    pub_idx = 0

    rp_rows = []
    for res_id, _, _ in researcher_rows:
        n_pubs = random.randint(2, 5)
        for order in range(1, n_pubs + 1):
            pub_id = pub_pool[pub_idx % len(pub_pool)]
            pub_idx += 1
            rp_rows.append((res_id, pub_id, order))

    cur.executemany(
        "INSERT OR IGNORE INTO researcher_publications (researcher_id, publication_id, author_order) VALUES (?, ?, ?)",
        rp_rows,
    )
    conn.commit()

    rp_count = cur.execute("SELECT COUNT(*) FROM researcher_publications").fetchone()[0]
    print(f"Inserted {rp_count} researcher-publication links")

    # ---------------------------------------------------------------
    # 4. Populate researcher_labs
    #    Each researcher belongs to 1-2 labs, preferring labs at the
    #    same institution.
    # ---------------------------------------------------------------
    cur.execute("DELETE FROM researcher_labs")

    # Build institution -> labs map
    inst_labs = {}
    for lab_id, inst_id in lab_rows:
        inst_labs.setdefault(inst_id, []).append(lab_id)

    all_lab_ids = [r[0] for r in lab_rows]
    roles = ["PI", "Co-PI", "Postdoc", "PhD Student", "Research Associate", "Visiting Researcher"]

    rl_rows = []
    for res_id, _, res_inst in researcher_rows:
        n_labs = random.randint(1, 2)
        # Prefer labs at same institution
        candidate_labs = inst_labs.get(res_inst, [])
        if not candidate_labs:
            candidate_labs = all_lab_ids

        chosen = random.sample(candidate_labs, min(n_labs, len(candidate_labs)))
        # If we need more, pick from the full pool
        if len(chosen) < n_labs:
            extras = [l for l in all_lab_ids if l not in chosen]
            chosen += random.sample(extras, n_labs - len(chosen))

        for lab_id in chosen:
            start_year = random.randint(2015, 2024)
            start_dt = f"{start_year}-{random.randint(1,12):02d}-01"
            # 70% still active (no end_date)
            end_dt = None
            if random.random() < 0.3:
                end_year = random.randint(start_year + 1, 2026)
                end_dt = f"{end_year}-{random.randint(1,12):02d}-01"
            role = random.choice(roles)
            rl_rows.append((res_id, lab_id, start_dt, end_dt, role))

    cur.executemany(
        "INSERT OR IGNORE INTO researcher_labs (researcher_id, lab_id, start_date, end_date, role) VALUES (?, ?, ?, ?, ?)",
        rl_rows,
    )
    conn.commit()

    rl_count = cur.execute("SELECT COUNT(*) FROM researcher_labs").fetchone()[0]
    print(f"Inserted {rl_count} researcher-lab links")

    # ---------------------------------------------------------------
    # 5. Populate publication_keywords
    #    Each publication gets 2-4 keywords.
    # ---------------------------------------------------------------
    pk_rows = []
    for pub_id in publication_ids:
        n_kw = random.randint(2, 4)
        chosen_kw = random.sample(keyword_ids, n_kw)
        for kw_id in chosen_kw:
            pk_rows.append((pub_id, kw_id))

    cur.executemany(
        "INSERT OR IGNORE INTO publication_keywords (publication_id, keyword_id) VALUES (?, ?)",
        pk_rows,
    )
    conn.commit()

    pk_count = cur.execute("SELECT COUNT(*) FROM publication_keywords").fetchone()[0]
    print(f"Inserted {pk_count} publication-keyword links")

    # ---------------------------------------------------------------
    # 6. Summary
    # ---------------------------------------------------------------
    print("\n=== Final counts ===")
    for table in ["researcher_publications", "researcher_labs", "keywords", "publication_keywords"]:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
