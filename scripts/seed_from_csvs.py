"""Comprehensive CSV-based database seeding script.

This script can rebuild the entire NRG database from CSV files.
It supports:
- Full rebuild from CSV files
- Incremental updates
- Data validation and normalization
- Progress tracking
- Transaction safety

Usage:
    python scripts/seed_from_csvs.py --rebuild
    python scripts/seed_from_csvs.py --rebuild --csv-dir ./data/csvs
    python scripts/seed_from_csvs.py --incremental --since 2024-01-01
    python scripts/seed_from_csvs.py --validate
"""

import argparse
import csv
import hashlib
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


CSV_COLUMNS = {
    "institutions": [
        "institution_id", "name", "type", "state", "country",
        "founded_year", "website"
    ],
    "researchers": [
        "researcher_id", "name", "institution_id", "department", "state",
        "research_area", "secondary_research_areas", "years_experience",
        "year_joined", "h_index", "total_funding_received_inr_crores",
        "email", "phone", "orcid", "access_tier"
    ],
    "publications": [
        "publication_id", "title", "abstract", "authors", "researcher_ids",
        "venue", "year", "volume", "issue", "pages", "doi", "pmid",
        "citations", "impact_factor", "publication_type", "research_area", "access_tier"
    ],
    "labs": [
        "lab_id", "name", "institution_id", "research_area",
        "research_focus_areas", "established_year", "location_state",
        "director_researcher_id", "website", "access_tier"
    ],
    "funding_records": [
        "funding_id", "researcher_id", "institution_id", "project_id",
        "fiscal_year", "agency", "amount", "start_date", "end_date",
        "title", "access_tier"
    ],
    "projects": [
        "project_id", "title", "principal_investigator_id", "co_pis",
        "start_date", "end_date", "funding_agency", "sanctioned_amount_inr_crores",
        "status", "research_area", "access_tier"
    ],
    "patents": [
        "patent_id", "title", "inventor_ids", "applicant_institution",
        "patent_office", "application_number", "filing_date", "grant_date",
        "status", "research_area", "patent_type", "claims_count", "access_tier"
    ],
    "collaborations": [
        "collaboration_id", "researcher_ids", "partner_institution",
        "partner_country", "collaboration_type", "start_date", "end_date",
        "nature_of_work", "funding_amount_inr_crores", "status", "research_area", "access_tier"
    ],
    "researcher_publications": [
        "researcher_id", "publication_id", "author_order"
    ],
    "researcher_labs": [
        "researcher_id", "lab_id", "start_date", "end_date", "role"
    ],
}

DEFAULT_CSV_DIR = Path(__file__).resolve().parents[1] / "data" / "csvs"


class SeedProgress:
    def __init__(self):
        self.tables = {}
        self.start_time = datetime.now()
        self.errors = []

    def start_table(self, table: str, total_rows: int):
        self.tables[table] = {"total": total_rows, "current": 0, "errors": 0}

    def update(self, table: str, count: int = 1):
        if table in self.tables:
            self.tables[table]["current"] += count

    def add_error(self, table: str, error: str):
        if table in self.tables:
            self.tables[table]["errors"] += 1
        self.errors.append({"table": table, "error": error})

    def report(self) -> Dict:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            "elapsed_seconds": elapsed,
            "tables": self.tables,
            "total_errors": len(self.errors),
            "errors": self.errors[:100],
        }


class CSVSeeder:
    """Comprehensive CSV-based database seeder."""

    def __init__(self, db_url: str, csv_dir: Path, batch_size: int = 1000):
        self.db_url = db_url
        self.csv_dir = csv_dir
        self.batch_size = batch_size
        self.progress = SeedProgress()
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self._validate_csvs()

    def _validate_csvs(self) -> None:
        missing = []
        for table in CSV_COLUMNS.keys():
            csv_path = self.csv_dir / f"{table}.csv"
            if not csv_path.exists():
                missing.append(table)
        if missing:
            print(f"Warning: Missing CSV files for: {missing}")

    def _generate_id(self, prefix: str, source: str = "") -> str:
        if source:
            hash_input = f"{prefix}:{source}"
        else:
            hash_input = f"{prefix}:{uuid.uuid4()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def _normalize_row(self, table: str, row: Dict[str, str]) -> Dict[str, Any]:
        normalized = {}

        for col in CSV_COLUMNS.get(table, []):
            value = row.get(col, "").strip() if row.get(col) else None

            if value == "" or value == "NULL":
                value = None

            if col == "institution_id" and not value:
                value = self._generate_id("inst", row.get("name", ""))
            elif col == "researcher_id" and not value:
                value = self._generate_id("res", row.get("name", ""))
            elif col == "publication_id" and not value:
                value = self._generate_id("pub", row.get("title", ""))
            elif col == "lab_id" and not value:
                value = self._generate_id("lab", row.get("name", ""))
            elif col == "funding_id" and not value:
                value = self._generate_id("fund", row.get("title", ""))
            elif col == "project_id" and not value:
                value = self._generate_id("proj", row.get("title", ""))
            elif col == "patent_id" and not value:
                value = self._generate_id("pat", row.get("title", ""))
            elif col == "collaboration_id" and not value:
                value = self._generate_id("collab", row.get("title", ""))

            if col.endswith("_id") and value:
                value = str(value)[:36]

            if col in ("h_index", "years_experience", "year_joined", "citations",
                       "claims_count", "founded_year", "established_year", "fiscal_year"):
                if value is not None:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = None

            if col in ("amount", "total_funding_received_inr_crores",
                       "sanctioned_amount_inr_crores", "funding_amount_inr_crores",
                       "impact_factor"):
                if value is not None:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = None

            if col == "access_tier":
                if value is None:
                    value = 1
                else:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = 1

            normalized[col] = value

        normalized["created_at"] = datetime.now().isoformat()
        normalized["updated_at"] = datetime.now().isoformat()

        return normalized

    def _read_csv(self, table: str) -> Iterator[Dict[str, Any]]:
        csv_path = self.csv_dir / f"{table}.csv"
        if not csv_path.exists():
            return

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield self._normalize_row(table, row)

    def _create_tables(self) -> None:
        schema_sql = """
        CREATE TABLE IF NOT EXISTS institutions (
            institution_id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50),
            state VARCHAR(50) NOT NULL,
            country VARCHAR(10) DEFAULT 'IN',
            founded_year INTEGER,
            website VARCHAR(255),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS researchers (
            researcher_id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            institution_id VARCHAR(36),
            department VARCHAR(100),
            state VARCHAR(50) NOT NULL,
            research_area VARCHAR(100),
            secondary_research_areas TEXT,
            years_experience INTEGER,
            year_joined INTEGER,
            h_index INTEGER,
            total_funding_received_inr_crores REAL,
            email VARCHAR(255),
            phone VARCHAR(20),
            orcid VARCHAR(50),
            access_tier INTEGER DEFAULT 1,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS publications (
            publication_id VARCHAR(36) PRIMARY KEY,
            title TEXT NOT NULL,
            abstract TEXT,
            authors TEXT,
            researcher_ids TEXT,
            venue VARCHAR(255),
            year INTEGER,
            volume VARCHAR(50),
            issue VARCHAR(50),
            pages VARCHAR(50),
            doi VARCHAR(255),
            pmid VARCHAR(50),
            citations INTEGER,
            impact_factor REAL,
            publication_type VARCHAR(100),
            research_area VARCHAR(100),
            access_tier INTEGER DEFAULT 1,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS labs (
            lab_id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            institution_id VARCHAR(36),
            research_area VARCHAR(100),
            research_focus_areas TEXT,
            established_year INTEGER,
            location_state VARCHAR(50),
            director_researcher_id VARCHAR(36),
            website VARCHAR(255),
            access_tier INTEGER DEFAULT 1,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS funding_records (
            funding_id VARCHAR(36) PRIMARY KEY,
            researcher_id VARCHAR(36),
            institution_id VARCHAR(36),
            project_id VARCHAR(36),
            fiscal_year VARCHAR(20),
            agency VARCHAR(255),
            amount REAL,
            start_date VARCHAR(50),
            end_date VARCHAR(50),
            title VARCHAR(500),
            access_tier INTEGER DEFAULT 1,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projects (
            project_id VARCHAR(36) PRIMARY KEY,
            title TEXT NOT NULL,
            principal_investigator_id VARCHAR(36),
            co_pis TEXT,
            start_date VARCHAR(50),
            end_date VARCHAR(50),
            funding_agency VARCHAR(255),
            sanctioned_amount_inr_crores REAL,
            status VARCHAR(50),
            research_area VARCHAR(100),
            access_tier INTEGER DEFAULT 1,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS patents (
            patent_id VARCHAR(36) PRIMARY KEY,
            title TEXT NOT NULL,
            inventor_ids TEXT,
            applicant_institution VARCHAR(255),
            patent_office VARCHAR(100),
            application_number VARCHAR(100),
            filing_date VARCHAR(50),
            grant_date VARCHAR(50),
            status VARCHAR(50),
            research_area VARCHAR(100),
            patent_type VARCHAR(100),
            claims_count INTEGER,
            access_tier INTEGER DEFAULT 1,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS collaborations (
            collaboration_id VARCHAR(36) PRIMARY KEY,
            researcher_ids TEXT,
            partner_institution VARCHAR(255),
            partner_country VARCHAR(100),
            collaboration_type VARCHAR(100),
            start_date VARCHAR(50),
            end_date VARCHAR(50),
            nature_of_work VARCHAR(255),
            funding_amount_inr_crores REAL,
            status VARCHAR(50),
            research_area VARCHAR(100),
            access_tier INTEGER DEFAULT 1,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS researcher_publications (
            researcher_id VARCHAR(36),
            publication_id VARCHAR(36),
            author_order INTEGER,
            PRIMARY KEY (researcher_id, publication_id)
        );

        CREATE TABLE IF NOT EXISTS researcher_labs (
            researcher_id VARCHAR(36),
            lab_id VARCHAR(36),
            start_date VARCHAR(50),
            end_date VARCHAR(50),
            role VARCHAR(100),
            PRIMARY KEY (researcher_id, lab_id)
        );
        """
        with self.engine.begin() as conn:
            for stmt in schema_sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))

    def _create_indexes(self) -> None:
        indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_researchers_state ON researchers(state);
        CREATE INDEX IF NOT EXISTS idx_researchers_research_area ON researchers(research_area);
        CREATE INDEX IF NOT EXISTS idx_researchers_institution ON researchers(institution_id);
        CREATE INDEX IF NOT EXISTS idx_researchers_h_index ON researchers(h_index);
        CREATE INDEX IF NOT EXISTS idx_researchers_tier ON researchers(access_tier);
        CREATE INDEX IF NOT EXISTS idx_researchers_state_area ON researchers(state, research_area);

        CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(year);
        CREATE INDEX IF NOT EXISTS idx_publications_citations ON publications(citations);
        CREATE INDEX IF NOT EXISTS idx_publications_research_area ON publications(research_area);
        CREATE INDEX IF NOT EXISTS idx_publications_tier ON publications(access_tier);
        CREATE INDEX IF NOT EXISTS idx_publications_year_area ON publications(year, research_area);

        CREATE INDEX IF NOT EXISTS idx_labs_institution ON labs(institution_id);
        CREATE INDEX IF NOT EXISTS idx_labs_research_area ON labs(research_area);
        CREATE INDEX IF NOT EXISTS idx_labs_tier ON labs(access_tier);

        CREATE INDEX IF NOT EXISTS idx_funding_researcher ON funding_records(researcher_id);
        CREATE INDEX IF NOT EXISTS idx_funding_agency ON funding_records(agency);
        CREATE INDEX IF NOT EXISTS idx_funding_fiscal_year ON funding_records(fiscal_year);
        CREATE INDEX IF NOT EXISTS idx_funding_tier ON funding_records(access_tier);

        CREATE INDEX IF NOT EXISTS idx_projects_pi ON projects(principal_investigator_id);
        CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
        CREATE INDEX IF NOT EXISTS idx_projects_research_area ON projects(research_area);

        CREATE INDEX IF NOT EXISTS idx_patents_status ON patents(status);
        CREATE INDEX IF NOT EXISTS idx_patents_research_area ON patents(research_area);

        CREATE INDEX IF NOT EXISTS idx_collaborations_country ON collaborations(partner_country);
        CREATE INDEX IF NOT EXISTS idx_collaborations_type ON collaborations(collaboration_type);
        """
        with self.engine.begin() as conn:
            for stmt in indexes_sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))

    def _insert_batch(self, table: str, rows: List[Dict]) -> Tuple[int, int]:
        if not rows:
            return 0, 0

        columns = CSV_COLUMNS.get(table, list(rows[0].keys()))
        cols_with_placeholders = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])

        insert_sql = f"""
            INSERT OR REPLACE INTO {table} ({cols_with_placeholders})
            VALUES ({placeholders})
        """

        success = 0
        errors = 0

        with self.engine.begin() as conn:
            for row in rows:
                try:
                    conn.execute(text(insert_sql), row)
                    success += 1
                except Exception as e:
                    errors += 1
                    self.progress.add_error(table, str(e))

        return success, errors

    def seed_table(self, table: str, truncate: bool = False) -> Dict:
        if truncate:
            with self.engine.begin() as conn:
                conn.execute(text(f"DELETE FROM {table}"))

        rows = list(self._read_csv(table))
        total = len(rows)
        self.progress.start_table(table, total)

        if total == 0:
            return {"table": table, "inserted": 0, "errors": 0, "skipped": True}

        for i in range(0, total, self.batch_size):
            batch = rows[i:i + self.batch_size]
            success, errors = self._insert_batch(table, batch)
            self.progress.update(table, len(batch))

        return {
            "table": table,
            "inserted": total - self.progress.tables[table]["errors"],
            "errors": self.progress.tables[table]["errors"],
        }

    def rebuild(self) -> Dict:
        print("Starting database rebuild from CSV files...")
        print(f"CSV directory: {self.csv_dir}")
        print(f"Database: {self.db_url}")

        print("\nCreating tables...")
        self._create_tables()

        print("Creating indexes...")
        self._create_indexes()

        results = {"tables": {}}
        for table in CSV_COLUMNS.keys():
            print(f"\nSeeding {table}...")
            result = self.seed_table(table, truncate=False)
            results["tables"][table] = result
            print(f"  Inserted: {result['inserted']}, Errors: {result['errors']}")

        results["progress"] = self.progress.report()
        return results

    def incremental_seed(self, since: datetime) -> Dict:
        print(f"Incremental seed since {since.isoformat()}...")
        results = {"tables": {}, "skipped": 0}

        for table in CSV_COLUMNS.keys():
            result = self.seed_table(table, truncate=False)
            if result["inserted"] > 0:
                results["tables"][table] = result
            else:
                results["skipped"] += 1

        return results

    def validate(self) -> Dict:
        print("Validating database integrity...")

        checks = {
            "institutions": "SELECT COUNT(*) FROM institutions",
            "researchers": "SELECT COUNT(*) FROM researchers",
            "publications": "SELECT COUNT(*) FROM publications",
            "labs": "SELECT COUNT(*) FROM labs",
            "funding_records": "SELECT COUNT(*) FROM funding_records",
        }

        results = {}
        with self.engine.begin() as conn:
            for name, sql in checks.items():
                count = conn.execute(text(sql)).scalar()
                results[name] = {"count": count, "status": "ok" if count > 0 else "empty"}

        orphan_checks = [
            ("researchers.institution_id", "institutions", """
                SELECT COUNT(*) FROM researchers r
                LEFT JOIN institutions i ON r.institution_id = i.institution_id
                WHERE r.institution_id IS NOT NULL AND i.institution_id IS NULL
            """),
        ]

        for name, sql in orphan_checks:
            count = conn.execute(text(sql)).scalar()
            results[f"orphan_{name}"] = {"count": count, "status": "ok" if count == 0 else "orphans_found"}

        return results


def generate_sample_csvs(csv_dir: Path) -> None:
    """Generate sample CSV files for testing."""
    import random

    csv_dir.mkdir(parents=True, exist_ok=True)

    indian_states = [
        "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Gujarat",
        "Uttar Pradesh", "West Bengal", "Telangana", "Kerala", "Rajasthan"
    ]

    research_areas = [
        "Artificial Intelligence", "Machine Learning", "Robotics", "Computer Vision",
        "Data Science", "Cybersecurity", "Software Engineering", "Information Systems",
        "Bioinformatics", "Material Science", "Physics", "Chemistry", "Mathematics"
    ]

    institutions = []
    for i in range(100):
        inst_id = f"inst-{i:04d}"
        name = random.choice([
            "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kanpur",
            "NIT Calicut", "NIT Warangal", "IISc Bangalore",
            "Anna University", "Jadavpur University", "IIT Guwahati"
        ])
        institutions.append({
            "institution_id": inst_id,
            "name": name,
            "type": "IIT" if "IIT" in name else ("NIT" if "NIT" in name else "University"),
            "state": random.choice(indian_states),
            "country": "IN",
            "founded_year": str(random.randint(1950, 2020)),
            "website": f"www.{name.lower().replace(' ', '')}.ac.in"
        })

    with open(csv_dir / "institutions.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS["institutions"])
        writer.writeheader()
        writer.writerows(institutions)

    researchers = []
    for i in range(1000):
        researchers.append({
            "researcher_id": f"res-{i:05d}",
            "name": f"Researcher {i}",
            "institution_id": random.choice(institutions)["institution_id"],
            "department": "Computer Science",
            "state": random.choice(indian_states),
            "research_area": random.choice(research_areas),
            "secondary_research_areas": random.choice(research_areas),
            "years_experience": str(random.randint(1, 40)),
            "year_joined": str(random.randint(2000, 2024)),
            "h_index": str(random.randint(1, 100)),
            "total_funding_received_inr_crores": str(random.randint(1, 500)),
            "email": f"researcher{i}@example.edu",
            "phone": f"+91-98765{i:05d}",
            "orcid": f"0000-0002-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "access_tier": str(random.choice([1, 1, 1, 2, 3])),
        })

    with open(csv_dir / "researchers.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS["researchers"])
        writer.writeheader()
        writer.writerows(researchers)

    publications = []
    for i in range(2000):
        year = random.randint(2015, 2024)
        publications.append({
            "publication_id": f"pub-{i:06d}",
            "title": f"Research Paper on {random.choice(research_areas)} - {i}",
            "abstract": f"This paper discusses {random.choice(research_areas)} with focus on methodology and results.",
            "authors": f"Researcher {random.randint(0, 999)}, et al.",
            "researcher_ids": f"res-{random.randint(0, 999):05d}",
            "venue": random.choice(["IEEE", "ACM", "Nature", "Science", "Springer"]),
            "year": str(year),
            "volume": str(random.randint(1, 50)),
            "issue": str(random.randint(1, 12)),
            "pages": f"{random.randint(1, 500)}-{random.randint(501, 1000)}",
            "doi": f"10.1000/xyz{str(random.randint(100, 999))}",
            "pmid": f"PMID{str(random.randint(10000000, 99999999))}",
            "citations": str(random.randint(0, 500)),
            "impact_factor": str(round(random.uniform(0.5, 15.0), 2)),
            "publication_type": random.choice(["Journal", "Conference", "Workshop"]),
            "research_area": random.choice(research_areas),
            "access_tier": str(random.choice([1, 1, 2, 3])),
        })

    with open(csv_dir / "publications.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS["publications"])
        writer.writeheader()
        writer.writerows(publications)

    for table in ["labs", "funding_records", "projects", "patents", "collaborations",
                  "researcher_publications", "researcher_labs"]:
        with open(csv_dir / f"{table}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS[table])
            writer.writeheader()

    print(f"Sample CSV files generated in: {csv_dir}")


def main():
    parser = argparse.ArgumentParser(description="NRG CSV Database Seeder")
    parser.add_argument("--rebuild", action="store_true", help="Full rebuild from CSVs")
    parser.add_argument("--incremental", action="store_true", help="Incremental update")
    parser.add_argument("--validate", action="store_true", help="Validate database")
    parser.add_argument("--generate-samples", action="store_true", help="Generate sample CSV files")
    parser.add_argument("--csv-dir", type=Path, default=DEFAULT_CSV_DIR, help="CSV directory")
    parser.add_argument("--db-url", default="sqlite:///nrg_research.db", help="Database URL")
    parser.add_argument("--since", type=lambda s: datetime.fromisoformat(s),
                        help="ISO datetime for incremental updates")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch insert size")

    args = parser.parse_args()

    if args.generate_samples:
        generate_sample_csvs(args.csv_dir)
        return

    if not args.rebuild and not args.incremental and not args.validate:
        parser.print_help()
        return

    seeder = CSVSeeder(args.db_url, args.csv_dir, args.batch_size)

    if args.validate:
        results = seeder.validate()
        print("\nValidation Results:")
        for name, result in results.items():
            print(f"  {name}: {result['count']} ({result['status']})")
        return

    if args.rebuild:
        results = seeder.rebuild()
        print("\nRebuild Complete!")
        print(f"Elapsed: {results['progress']['elapsed_seconds']:.2f}s")
        for table, result in results["tables"].items():
            print(f"  {table}: {result['inserted']} inserted, {result['errors']} errors")

    if args.incremental:
        since = args.since or datetime.now()
        results = seeder.incremental_seed(since)
        print("\nIncremental Seed Complete!")
        print(f"Tables updated: {len(results['tables'])}")
        print(f"Tables skipped: {results['skipped']}")


if __name__ == "__main__":
    main()