import csv
from pathlib import Path

from scripts.verify_db_merge import CSV_HEADERS, read_logical_csv_rows


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_project_source_reader_repairs_title_commas_and_glued_rows(tmp_path):
    _write_csv(
        tmp_path / "projects.csv",
        CSV_HEADERS["projects"],
        [
            [
                "PRJ_5026",
                "High-pressure-temperature Behavior of (Mg",
                " Fe)2GeO4",
                "RES_1081",
                "RES_1009",
                "2024-01-01",
                "2026-12-31",
                "SERB",
                "0.30",
                "Ongoing",
                "Earth Sciences",
            ],
            [
                "PRJ_5050",
                "Rock Fall Impact",
                "RES_1054",
                "RES_1055",
                "2024-10-09",
                "2027-10-08",
                "NMHS",
                "0.49",
                "Ongoing",
                "Earth SciencesPRJ-00001",
                "Novel Wearable Water Resources",
                "RES-01189",
                "RES-02239;RES-00984",
                "2025-09-03",
                "2026-12-31",
                "ANRF",
                "25.14",
                "Completed",
                "Water Resources",
            ],
        ],
    )

    source = read_logical_csv_rows(tmp_path, "projects")

    assert [row["project_id"] for row in source.rows] == [
        "PRJ_5026",
        "PRJ_5050",
        "PRJ-00001",
    ]
    assert source.rows[0]["title"] == "High-pressure-temperature Behavior of (Mg, Fe)2GeO4"
    assert source.rows[1]["research_area"] == "Earth Sciences"
    assert source.rows[2]["funding_agency"] == "ANRF"
    assert len(source.repairs) == 2
    assert source.malformed == []


def test_lab_and_funding_source_readers_split_glued_records(tmp_path):
    _write_csv(
        tmp_path / "labs_institutions.csv",
        CSV_HEADERS["labs"],
        [
            [
                "LAB_040",
                "Institute of Microbial Technology",
                "CSIR",
                "Chandigarh",
                "Biotechnology|Microbiology",
                "RES_1122LAB-0001",
                "DRDO Centre of Excellence in Wind Energy",
                "DRDO",
                "Delhi",
                "Sustainable Energy",
                "RES-02113",
            ]
        ],
    )
    _write_csv(
        tmp_path / "funding_transactions.csv",
        CSV_HEADERS["funding_records"],
        [
            [
                "TXN_9098",
                "PRJ_5050",
                "2024-2025",
                "0.25",
                "NMHSTXN-000001",
                "PRJ-00001",
                "FY2025-26",
                "9.56",
                "ANRF",
            ]
        ],
    )

    labs = read_logical_csv_rows(tmp_path, "labs")
    funding = read_logical_csv_rows(tmp_path, "funding_records")

    assert [row["lab_id"] for row in labs.rows] == ["LAB_040", "LAB-0001"]
    assert labs.rows[0]["director_researcher_id"] == "RES_1122"
    assert labs.rows[1]["affiliation"] == "DRDO"
    assert [row["transaction_id"] for row in funding.rows] == ["TXN_9098", "TXN-000001"]
    assert funding.rows[0]["agency"] == "NMHS"
    assert funding.rows[1]["amount_released_inr_crores"] == "9.56"
