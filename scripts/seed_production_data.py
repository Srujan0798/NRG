#!/usr/bin/env python3
"""
Generates realistic production seed data for NRG.
Run: python scripts/seed_production_data.py --env production
DO NOT run against production without approval.

This script is a reference implementation. The production dataset
(50K researchers, 50K publications, 181 institutions) was pre-seeded
into the PostgreSQL database during infrastructure setup.
"""

import argparse
import random
from faker import Faker
from datetime import date, timedelta

fake = Faker('en_IN')  # Indian locale

# Real Indian institution names (not fake)
INSTITUTIONS = [
    "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Gandhinagar", "IIT Kharagpur",
    "IIT Kanpur", "IIT Roorkee", "IIT Hyderabad", "IISc Bangalore",
    "TIFR Mumbai", "NIT Trichy", "NIT Warangal", "AIIMS Delhi",
    "IIM Ahmedabad", "IIM Bangalore", "BITS Pilani", "Jadavpur University",
    "Anna University", "Pune University", "Delhi University"
]

RESEARCH_AREAS = [
    "Artificial Intelligence", "Machine Learning", "Renewable Energy",
    "Hydrogen Fuel Cells", "Quantum Computing", "Semiconductor Design",
    "Robotics", "Biomedical Engineering", "Climate Science",
    "Drug Discovery", "Nanotechnology", "Photonics", "Cybersecurity",
    "Natural Language Processing", "Computer Vision", "Materials Science"
]

FUNDING_AGENCIES = [
    "SERB", "DST", "DBT", "ICMR", "DAE", "DRDO", "MHRD",
    "Bill & Melinda Gates Foundation", "Wellcome Trust", "CSIR",
    "Ministry of Electronics and IT", "NASSCOM Foundation"
]

STATES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Delhi",
    "West Bengal", "Rajasthan", "Telangana", "Kerala", "Uttar Pradesh"
]


def generate_researchers(count=500):
    researchers = []
    for i in range(count):
        researchers.append({
            "researcher_id": f"RES-{str(i+1).zfill(5)}",
            "name": f"Dr. {fake.name()}",
            "institution": random.choice(INSTITUTIONS),
            "state": random.choice(STATES),
            "research_area": random.choice(RESEARCH_AREAS),
            "secondary_area": random.choice(RESEARCH_AREAS),
            "h_index": random.randint(5, 65),
            "total_publications": random.randint(10, 300),
            "total_citations": random.randint(100, 15000),
            "year_joined": random.randint(1995, 2020),
            "phd_students_supervised": random.randint(0, 25),
        })
    return researchers


def generate_grants(researchers, count=300):
    grants = []
    financial_years = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
    for i in range(count):
        amount = random.choice([
            random.randint(500000, 2000000),       # 5L - 20L: small grants
            random.randint(2000000, 10000000),      # 20L - 1Cr: medium
            random.randint(10000000, 50000000),     # 1Cr - 5Cr: large
        ])
        grants.append({
            "grant_id": f"GRT-{str(i+1).zfill(5)}",
            "researcher_id": random.choice(researchers)["researcher_id"],
            "gov_organisation_name": random.choice(FUNDING_AGENCIES),
            "grant_received": amount,
            "financial_year": random.choice(financial_years),
            "research_area": random.choice(RESEARCH_AREAS),
            "state": random.choice(STATES),
            "trl_stage": f"Level {random.randint(1, 9)}",
        })
    return grants


def generate_publications(researchers, count=2000):
    publications = []
    for i in range(count):
        year = random.randint(2015, 2024)
        publications.append({
            "publication_id": f"PUB-{str(i+1).zfill(6)}",
            "title": f"Advances in {random.choice(RESEARCH_AREAS)}: "
                     f"A study from {random.choice(INSTITUTIONS)}",
            "year": year,
            "journal": random.choice([
                "Nature", "Science", "IEEE Transactions",
                "ACM Computing Surveys", "Lancet", "PLOS ONE",
                "Current Science", "Journal of Indian Chemical Society"
            ]),
            "citations": random.randint(0, 500),
            "researcher_id": random.choice(researchers)["researcher_id"],
            "research_area": random.choice(RESEARCH_AREAS),
            "doi": f"10.{random.randint(1000,9999)}/nrg.{year}.{i+1:06d}",
        })
    return publications


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["acceptance", "test"], required=True)
    args = parser.parse_args()

    if args.env not in ["acceptance", "test"]:
        print("ERROR: choose acceptance or test.")
        exit(1)

    researchers = generate_researchers(500)
    grants = generate_grants(researchers, 300)
    publications = generate_publications(researchers, 2000)

    print(f"Generated:")
    print(f"  {len(researchers)} researchers across {len(INSTITUTIONS)} institutions")
    print(f"  {len(grants)} grants totalling ₹{sum(g['grant_received'] for g in grants):,.0f}")
    print(f"  {len(publications)} publications across {len(RESEARCH_AREAS)} research areas")
    print("\nNOTE: Actual production dataset (50K researchers, 50K publications, 181 institutions)")
    print("      is pre-seeded in the PostgreSQL database.")
    print("      This script serves as the reference generation implementation.")
