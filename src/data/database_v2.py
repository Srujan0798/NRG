"""Database Management for National Research Graph - Supports SQLite and PostgreSQL.

Full schema for 50K-record NRG database.
Auto-detects dialect from DATABASE_URL.
"""

import os
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text, Column, String, Integer, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, UTC

Base: Any = declarative_base()


class Institution(Base):
    __tablename__ = "institutions"

    institution_id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=True)
    state = Column(String(50), nullable=False)
    country = Column(String(10), nullable=True, default="IN")
    founded_year = Column(Integer, nullable=True)
    website = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class Researcher(Base):
    __tablename__ = "researchers"

    researcher_id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.institution_id"), nullable=True)
    department = Column(String(100), nullable=True)
    state = Column(String(50), nullable=False)
    research_area = Column(String(100), nullable=True)
    secondary_research_areas = Column(Text, nullable=True)
    years_experience = Column(Integer, nullable=True)
    year_joined = Column(Integer, nullable=True)
    h_index = Column(Integer, nullable=True)
    total_funding_received_inr_crores = Column(Float, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    orcid = Column(String(50), nullable=True)
    access_tier = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_researchers_state", "state"),
        Index("idx_researchers_research_area", "research_area"),
        Index("idx_researchers_department", "department"),
        Index("idx_researchers_h_index", "h_index"),
        Index("idx_researchers_tier", "access_tier"),
    )


class Publication(Base):
    __tablename__ = "publications"

    publication_id = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)
    researcher_ids = Column(Text, nullable=True)
    venue = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    volume = Column(String(50), nullable=True)
    issue = Column(String(50), nullable=True)
    pages = Column(String(50), nullable=True)
    doi = Column(String(255), nullable=True)
    pmid = Column(String(50), nullable=True)
    citations = Column(Integer, nullable=True)
    impact_factor = Column(Float, nullable=True)
    publication_type = Column(String(100), nullable=True)
    research_area = Column(String(100), nullable=True)
    access_tier = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_publications_year", "year"),
        Index("idx_publications_citations", "citations"),
        Index("idx_publications_research_area", "research_area"),
        Index("idx_publications_tier", "access_tier"),
    )


class Keyword(Base):
    __tablename__ = "keywords"

    keyword_id = Column(Integer, primary_key=True)
    keyword = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ResearcherPublication(Base):
    __tablename__ = "researcher_publications"

    researcher_id = Column(String(36), ForeignKey("researchers.researcher_id"), primary_key=True)
    publication_id = Column(String(36), ForeignKey("publications.publication_id"), primary_key=True)
    author_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class PublicationKeyword(Base):
    __tablename__ = "publication_keywords"

    publication_id = Column(String(36), ForeignKey("publications.publication_id"), primary_key=True)
    keyword_id = Column(Integer, ForeignKey("keywords.keyword_id"), primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Lab(Base):
    __tablename__ = "labs"

    lab_id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.institution_id"), nullable=True)
    research_area = Column(String(100), nullable=True)
    research_focus_areas = Column(Text, nullable=True)
    established_year = Column(Integer, nullable=True)
    location_state = Column(String(50), nullable=True)
    director_researcher_id = Column(String(36), ForeignKey("researchers.researcher_id"), nullable=True)
    website = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_labs_institution", "institution_id"),
        Index("idx_labs_research_area", "research_area"),
        Index("idx_labs_location_state", "location_state"),
        Index("idx_labs_director", "director_researcher_id"),
    )


class ResearcherLab(Base):
    __tablename__ = "researcher_labs"

    researcher_id = Column(String(36), ForeignKey("researchers.researcher_id"), primary_key=True)
    lab_id = Column(String(36), ForeignKey("labs.lab_id"), primary_key=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    role = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    principal_investigator_id = Column(String(36), ForeignKey("researchers.researcher_id"), nullable=False)
    co_pis = Column(Text, nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    funding_agency = Column(String(255), nullable=True)
    sanctioned_amount_inr_crores = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    research_area = Column(String(100), nullable=True)
    access_tier = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_projects_pi", "principal_investigator_id"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_agency", "funding_agency"),
        Index("idx_projects_research_area", "research_area"),
        Index("idx_projects_tier", "access_tier"),
    )


class FundingRecord(Base):
    __tablename__ = "funding_records"

    funding_id = Column(String(36), primary_key=True)
    researcher_id = Column(String(36), ForeignKey("researchers.researcher_id"), nullable=True)
    institution_id = Column(String(36), ForeignKey("institutions.institution_id"), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=True)
    agency = Column(String(255), nullable=True)
    amount = Column(Float, nullable=True)
    fiscal_year = Column(String(20), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    title = Column(String(500), nullable=True)
    access_tier = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_funding_researcher", "researcher_id"),
        Index("idx_funding_institution", "institution_id"),
        Index("idx_funding_project", "project_id"),
        Index("idx_funding_agency", "agency"),
        Index("idx_funding_fiscal_year", "fiscal_year"),
        Index("idx_funding_tier", "access_tier"),
    )


class Patent(Base):
    __tablename__ = "patents"

    patent_id = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    inventor_ids = Column(Text, nullable=True)
    applicant_institution = Column(String(255), nullable=True)
    patent_office = Column(String(100), nullable=True)
    application_number = Column(String(100), nullable=True)
    filing_date = Column(String(50), nullable=True)
    grant_date = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    research_area = Column(String(100), nullable=True)
    patent_type = Column(String(100), nullable=True)
    claims_count = Column(Integer, nullable=True)
    access_tier = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_patents_status", "status"),
        Index("idx_patents_research_area", "research_area"),
        Index("idx_patents_tier", "access_tier"),
    )


class Collaboration(Base):
    __tablename__ = "collaborations"

    collaboration_id = Column(String(36), primary_key=True)
    researcher_ids = Column(Text, nullable=True)
    partner_institution = Column(String(255), nullable=True)
    partner_country = Column(String(100), nullable=True)
    collaboration_type = Column(String(100), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    nature_of_work = Column(String(255), nullable=True)
    funding_amount_inr_crores = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    research_area = Column(String(100), nullable=True)
    access_tier = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_collaborations_partner", "partner_institution"),
        Index("idx_collaborations_type", "collaboration_type"),
        Index("idx_collaborations_status", "status"),
        Index("idx_collaborations_tier", "access_tier"),
    )


class ResearchDocument(Base):
    __tablename__ = "research_documents"

    document_id = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    researcher_ids = Column(Text, nullable=True)
    affiliation = Column(String(255), nullable=True)
    publication_year = Column(Integer, nullable=True)
    abstract = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    research_area_tags = Column(Text, nullable=True)
    access_tier = Column(Integer, nullable=False, default=1)
    category = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_research_docs_year", "publication_year"),
        Index("idx_research_docs_category", "category"),
        Index("idx_research_docs_tier", "access_tier"),
    )


POOL_CONFIG = {
    "sqlite": {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    },
    "postgresql": {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    },
}


class NRGDatabase:
    """Unified database manager supporting SQLite and PostgreSQL with optimized pooling."""

    def __init__(self, url: Optional[str] = None):
        self.url: str = url or os.getenv("DATABASE_URL", "sqlite:///nrg_research.db") or "sqlite:///nrg_research.db"
        self.dialect = "sqlite" if self.url.startswith("sqlite") else "postgresql"
        pool_config = POOL_CONFIG.get(self.dialect, POOL_CONFIG["sqlite"])

        pool_kwargs: dict[str, Any] = {
            "pool_size": pool_config["pool_size"],
            "max_overflow": pool_config["max_overflow"],
            "pool_timeout": pool_config["pool_timeout"],
            "pool_recycle": pool_config["pool_recycle"],
            "pool_pre_ping": pool_config["pool_pre_ping"],
        }

        if self.dialect == "sqlite":
            pool_kwargs = {
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,
                },
                "pool_pre_ping": pool_config["pool_pre_ping"],
            }

        self.engine = create_engine(self.url, future=True, **pool_kwargs)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._setup_query_logging()

    def _setup_query_logging(self) -> None:
        if hasattr(self.engine, "execution_options"):
            self.engine.execution_options(
                logging_token="slow_query",
                echo=False,
            )

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Any, None, None]:
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_health_check_session(self) -> Generator[Any, None, None]:
        session = self.Session()
        try:
            session.execute(text("SELECT 1"))
            yield session
        finally:
            session.close()

    def execute(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        start = datetime.now()
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result]
            execution_time = (datetime.now() - start).total_seconds() * 1000
            self._log_query(query, execution_time, len(rows))
            return rows

    def _log_query(self, query: str, execution_time_ms: float, row_count: int) -> None:
        import logging
        _logger = logging.getLogger(__name__)
        if execution_time_ms > 1000:
            _logger.warning(
                "Slow query detected: %.2fms, %d rows: %s",
                execution_time_ms,
                row_count,
                query[:200],
            )

    def get_pool_status(self) -> Dict[str, Any]:
        pool = self.engine.pool
        if self.dialect == "sqlite":
            return {
                "pool_type": "sqlite",
                "pool_size": 0,
                "checked_in": 0,
                "overflow": 0,
            }
        try:
            return {
                "pool_type": "postgresql",
                "pool_size": getattr(pool, "size", lambda: 0)(),
                "checked_in": getattr(pool, "checkedin", lambda: 0)(),
                "overflow": getattr(pool, "overflow", lambda: 0)(),
                "total": getattr(pool, "size", lambda: 0)() + getattr(pool, "overflow", lambda: 0)(),
            }
        except Exception:
            return {
                "pool_type": "postgresql",
                "pool_size": 0,
                "checked_in": 0,
                "overflow": 0,
                "total": 0,
            }

    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        try:
            with self.get_session() as session:
                stats["researchers"] = session.query(Researcher).count()
                stats["publications"] = session.query(Publication).count()
                stats["institutions"] = session.query(Institution).count()
                stats["labs"] = session.query(Lab).count()
                stats["funding_records"] = session.query(FundingRecord).count()
                stats["projects"] = session.query(Project).count()
                stats["patents"] = session.query(Patent).count()
                stats["collaborations"] = session.query(Collaboration).count()
                stats["research_documents"] = session.query(ResearchDocument).count()

                result = session.execute(
                    text(
                        """SELECT research_area, COUNT(*) as count
                           FROM researchers
                           WHERE research_area IS NOT NULL
                           GROUP BY research_area
                           ORDER BY count DESC LIMIT 10"""
                    )
                )
                stats["research_areas"] = [
                    {"area": row[0], "count": row[1]} for row in result
                ]

                result = session.execute(
                    text(
                        """SELECT state, COUNT(*) as count
                           FROM researchers
                           WHERE state IS NOT NULL
                           GROUP BY state
                           ORDER BY count DESC LIMIT 10"""
                    )
                )
                stats["state_distribution"] = [
                    {"state": row[0], "count": row[1]} for row in result
                ]
        except Exception:
            # Fallback to raw SQL if ORM schema mismatch
            for table in [
                "researchers", "publications", "institutions", "labs",
                "funding_records", "projects", "patents", "collaborations", "research_documents"
            ]:
                try:
                    rows = self.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = int(next(iter(rows[0].values()))) if rows else 0
                except Exception:
                    stats[table] = 0
            stats["research_areas"] = []
            stats["state_distribution"] = []
        return stats

    def query_researchers(
        self,
        state: Optional[str] = None,
        research_area: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        try:
            with self.get_session() as session:
                query = session.query(Researcher)
                if state:
                    query = query.filter(Researcher.state == state)
                if research_area:
                    query = query.filter(Researcher.research_area.ilike(f"%{research_area}%"))
                query = query.limit(limit).offset(offset)
                return [
                    {
                        "researcher_id": r.researcher_id,
                        "name": r.name,
                        "institution_id": r.institution_id,
                        "department": r.department,
                        "state": r.state,
                        "research_area": r.research_area,
                        "secondary_research_areas": r.secondary_research_areas,
                        "years_experience": r.years_experience,
                        "year_joined": r.year_joined,
                        "h_index": r.h_index,
                        "total_funding_received_inr_crores": r.total_funding_received_inr_crores,
                        "email": r.email,
                        "phone": r.phone,
                        "orcid": r.orcid,
                    }
                    for r in query.all()
                ]
        except Exception:
            return self._query_researchers_raw(
                state=state,
                research_area=research_area,
                limit=limit,
                offset=offset,
            )

    def _query_researchers_raw(
        self,
        state: Optional[str] = None,
        research_area: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Return researcher rows when deployed DB columns drift from the ORM model."""
        inspector = inspect(self.engine)
        available_columns = {
            column["name"]
            for column in inspector.get_columns("researchers")
        }

        expected_columns = [
            "researcher_id",
            "name",
            "institution_id",
            "department",
            "state",
            "research_area",
            "secondary_research_areas",
            "years_experience",
            "year_joined",
            "h_index",
            "total_funding_received_inr_crores",
            "email",
            "phone",
            "orcid",
        ]
        select_columns = [
            column if column in available_columns else f"NULL AS {column}"
            for column in expected_columns
        ]
        predicates = []
        params: Dict[str, Any] = {
            "limit": max(1, min(int(limit), 500)),
            "offset": max(0, int(offset)),
        }

        if state and "state" in available_columns:
            predicates.append("state = :state")
            params["state"] = state
        if research_area and "research_area" in available_columns:
            predicates.append("LOWER(research_area) LIKE LOWER(:research_area)")
            params["research_area"] = f"%{research_area}%"

        where_clause = f" WHERE {' AND '.join(predicates)}" if predicates else ""
        order_clause = " ORDER BY name" if "name" in available_columns else ""
        query = (
            f"SELECT {', '.join(select_columns)} "
            f"FROM researchers{where_clause}{order_clause} "
            "LIMIT :limit OFFSET :offset"
        )
        return self.execute(query, params)

    def query_publications(
        self, year: Optional[int] = None, limit: int = 10, offset: int = 0
    ) -> List[Dict]:
        try:
            with self.get_session() as session:
                query = session.query(Publication)
                if year:
                    query = query.filter(Publication.year == year)
                query = query.order_by(Publication.year.desc()).limit(limit).offset(offset)
                return [
                    {
                        "publication_id": p.publication_id,
                        "title": p.title,
                        "year": p.year,
                        "venue": p.venue,
                        "authors": p.authors,
                        "researcher_ids": p.researcher_ids,
                        "citations": p.citations,
                        "impact_factor": p.impact_factor,
                        "publication_type": p.publication_type,
                        "volume": p.volume,
                        "issue": p.issue,
                        "pages": p.pages,
                        "research_area": p.research_area,
                    }
                    for p in query.all()
                ]
        except Exception:
            where_clause = "WHERE year = :year" if year else ""
            params: Dict[str, Any] = {"limit": limit, "offset": offset}
            if year:
                params["year"] = year
            return self.execute(
                f"""
                SELECT
                    CAST(publication_id AS TEXT) AS publication_id,
                    title,
                    year,
                    venue,
                    NULL AS authors,
                    NULL AS researcher_ids,
                    NULL AS citations,
                    NULL AS impact_factor,
                    NULL AS publication_type,
                    NULL AS volume,
                    NULL AS issue,
                    NULL AS pages,
                    NULL AS research_area
                FROM publications
                {where_clause}
                ORDER BY year DESC NULLS LAST
                LIMIT :limit OFFSET :offset
                """,
                params,
            )

    def query_projects(
        self,
        status: Optional[str] = None,
        research_area: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        with self.get_session() as session:
            query = session.query(Project)
            if status:
                query = query.filter(Project.status.ilike(f"%{status}%"))
            if research_area:
                query = query.filter(Project.research_area.ilike(f"%{research_area}%"))
            query = query.order_by(Project.start_date.desc()).limit(limit).offset(offset)
            return [
                {
                    "project_id": p.project_id,
                    "title": p.title,
                    "principal_investigator_id": p.principal_investigator_id,
                    "co_pis": p.co_pis,
                    "start_date": p.start_date,
                    "end_date": p.end_date,
                    "funding_agency": p.funding_agency,
                    "sanctioned_amount_inr_crores": p.sanctioned_amount_inr_crores,
                    "status": p.status,
                    "research_area": p.research_area,
                }
                for p in query.all()
            ]

    def query_patents(
        self,
        status: Optional[str] = None,
        research_area: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        with self.get_session() as session:
            query = session.query(Patent)
            if status:
                query = query.filter(Patent.status.ilike(f"%{status}%"))
            if research_area:
                query = query.filter(Patent.research_area.ilike(f"%{research_area}%"))
            query = query.order_by(Patent.filing_date.desc()).limit(limit).offset(offset)
            return [
                {
                    "patent_id": p.patent_id,
                    "title": p.title,
                    "inventor_ids": p.inventor_ids,
                    "applicant_institution": p.applicant_institution,
                    "patent_office": p.patent_office,
                    "application_number": p.application_number,
                    "filing_date": p.filing_date,
                    "grant_date": p.grant_date,
                    "status": p.status,
                    "research_area": p.research_area,
                    "patent_type": p.patent_type,
                    "claims_count": p.claims_count,
                }
                for p in query.all()
            ]

    def query_collaborations(
        self,
        partner_country: Optional[str] = None,
        collaboration_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        with self.get_session() as session:
            query = session.query(Collaboration)
            if partner_country:
                query = query.filter(Collaboration.partner_country.ilike(f"%{partner_country}%"))
            if collaboration_type:
                query = query.filter(Collaboration.collaboration_type.ilike(f"%{collaboration_type}%"))
            query = query.limit(limit).offset(offset)
            return [
                {
                    "collaboration_id": c.collaboration_id,
                    "researcher_ids": c.researcher_ids,
                    "partner_institution": c.partner_institution,
                    "partner_country": c.partner_country,
                    "collaboration_type": c.collaboration_type,
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                    "nature_of_work": c.nature_of_work,
                    "funding_amount_inr_crores": c.funding_amount_inr_crores,
                    "status": c.status,
                    "research_area": c.research_area,
                }
                for c in query.all()
            ]

    def query_funding_records(
        self,
        agency: Optional[str] = None,
        fiscal_year: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        with self.get_session() as session:
            query = session.query(FundingRecord)
            if agency:
                query = query.filter(FundingRecord.agency.ilike(f"%{agency}%"))
            if fiscal_year:
                query = query.filter(FundingRecord.fiscal_year == fiscal_year)
            query = query.order_by(FundingRecord.fiscal_year.desc()).limit(limit).offset(offset)
            return [
                {
                    "funding_id": f.funding_id,
                    "researcher_id": f.researcher_id,
                    "institution_id": f.institution_id,
                    "project_id": f.project_id,
                    "agency": f.agency,
                    "amount": f.amount,
                    "fiscal_year": f.fiscal_year,
                    "start_date": f.start_date,
                    "end_date": f.end_date,
                    "title": f.title,
                }
                for f in query.all()
            ]

    def query_labs(
        self,
        state: Optional[str] = None,
        research_area: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        with self.get_session() as session:
            query = session.query(Lab)
            if state:
                query = query.filter(Lab.location_state.ilike(f"%{state}%"))
            if research_area:
                query = query.filter(Lab.research_area.ilike(f"%{research_area}%"))
            query = query.limit(limit).offset(offset)
            return [
                {
                    "lab_id": lab.lab_id,
                    "name": lab.name,
                    "institution_id": lab.institution_id,
                    "research_area": lab.research_area,
                    "research_focus_areas": lab.research_focus_areas,
                    "location_state": lab.location_state,
                    "director_researcher_id": lab.director_researcher_id,
                }
                for lab in query.all()
            ]

    def query_research_documents(
        self,
        year: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        with self.get_session() as session:
            query = session.query(ResearchDocument)
            if year:
                query = query.filter(ResearchDocument.publication_year == year)
            if category:
                query = query.filter(ResearchDocument.category.ilike(f"%{category}%"))
            query = query.order_by(ResearchDocument.publication_year.desc()).limit(limit).offset(offset)
            return [
                {
                    "document_id": d.document_id,
                    "title": d.title,
                    "researcher_ids": d.researcher_ids,
                    "affiliation": d.affiliation,
                    "publication_year": d.publication_year,
                    "abstract": d.abstract,
                    "keywords": d.keywords,
                    "research_area_tags": d.research_area_tags,
                    "category": d.category,
                }
                for d in query.all()
            ]

    def refresh_materialized_views(self) -> Dict[str, str]:
        """Refresh all materialized views. Call after data changes."""
        views = [
            "mv_researchers_per_state",
            "mv_researchers_per_area",
            "mv_publications_per_year",
            "mv_publications_per_area",
            "mv_funding_per_agency",
            "mv_researcher_stats",
        ]
        results = {}
        for view in views:
            try:
                self.execute(f"REFRESH MATERIALIZED VIEW {view}")
                results[view] = "success"
            except Exception as e:
                results[view] = f"error: {str(e)}"
        return results

    def query_materialized_view(self, view_name: str, limit: int = 100) -> List[Dict]:
        """Query a materialized view directly."""
        return self.execute(f"SELECT * FROM {view_name} LIMIT {limit}")

    def get_researchers_per_state(self, state: Optional[str] = None) -> List[Dict]:
        """Get researcher counts per state from materialized view."""
        if state:
            return self.execute(
                "SELECT * FROM mv_researchers_per_state WHERE state = ?",
                {"state": state},
            )
        return self.query_materialized_view("mv_researchers_per_state")

    def get_publications_per_year(self, year: Optional[int] = None) -> List[Dict]:
        """Get publication counts per year from materialized view."""
        if year:
            return self.execute(
                "SELECT * FROM mv_publications_per_year WHERE year = ?",
                {"year": year},
            )
        return self.query_materialized_view("mv_publications_per_year")

    def get_researcher_stats(self, researcher_id: str) -> Dict:
        """Get aggregated stats for a researcher from materialized view."""
        results = self.execute(
            "SELECT * FROM mv_researcher_stats WHERE researcher_id = ?",
            {"researcher_id": researcher_id},
        )
        return results[0] if results else {}

    def normalize_institution_name(self, name: str) -> Optional[Dict]:
        """Get canonical institution name from alternate name."""
        results = self.execute(
            """
            SELECT canonical_name, institution_type, state
            FROM institution_name_normalization
            WHERE alternate_name = ?
            """,
            {"name": name},
        )
        return results[0] if results else None

    def get_deduplication_candidates(self, status: str = "pending") -> List[Dict]:
        """Get researcher deduplication candidates."""
        return self.execute(
            """
            SELECT dc.*,
                   r1.name as researcher_1_name,
                   r2.name as researcher_2_name,
                   r1.email as researcher_1_email,
                   r2.email as researcher_2_email
            FROM researcher_dedup_candidates dc
            JOIN researchers r1 ON dc.researcher_id_1 = r1.researcher_id
            JOIN researchers r2 ON dc.researcher_id_2 = r2.researcher_id
            WHERE dc.status = ?
            ORDER BY dc.similarity_score DESC
            """,
            {"status": status},
        )

    def resolve_researcher_duplicates(self, canonical_id: str, duplicate_ids: List[str]) -> Dict:
        """Merge duplicate researchers into canonical record."""
        results = {"updated": [], "errors": []}
        for dup_id in duplicate_ids:
            try:
                self.execute(
                    """
                    UPDATE researcher_publications
                    SET researcher_id = ?
                    WHERE researcher_id = ?
                    """,
                    {"canonical": canonical_id, "duplicate": dup_id},
                )
                self.execute(
                    """
                    UPDATE funding_records
                    SET researcher_id = ?
                    WHERE researcher_id = ?
                    """,
                    {"canonical": canonical_id, "duplicate": dup_id},
                )
                self.execute(
                    """
                    UPDATE researcher_labs
                    SET researcher_id = ?
                    WHERE researcher_id = ?
                    """,
                    {"canonical": canonical_id, "duplicate": dup_id},
                )
                self.execute(
                    """
                    INSERT INTO researcher_id_mapping (original_id, canonical_id, match_type)
                    VALUES (?, ?, 'manual_merge')
                    """,
                    {"original": dup_id, "canonical": canonical_id},
                )
                self.execute(
                    "DELETE FROM researchers WHERE researcher_id = ?",
                    {"researcher_id": dup_id},
                )
                results["updated"].append(dup_id)
            except Exception as e:
                results["errors"].append({"id": dup_id, "error": str(e)})
        return results

    def explain_query(self, query: str) -> Dict:
        """Get query execution plan for optimization."""
        if self.dialect == "sqlite":
            results = self.execute(f"EXPLAIN QUERY PLAN {query}")
        else:
            results = self.execute(f"EXPLAIN (ANALYZE, BUFFERS) {query}")
        return {"plan": results, "query": query}

    def get_slow_queries(self, threshold_ms: float = 1000.0) -> List[Dict]:
        """Get slow queries from performance log."""
        return self.execute(
            """
            SELECT query_hash, query_text, execution_time_ms, row_count, executed_at
            FROM query_performance_log
            WHERE execution_time_ms > ?
            ORDER BY execution_time_ms DESC
            LIMIT 50
            """,
            {"threshold": threshold_ms},
        )

    def get_unused_indexes(self) -> List[Dict]:
        """Get indexes that haven't been used recently (for potential drop)."""
        return self.execute(
            """
            SELECT index_name, table_name, scans_since_last_vacuum, is_recommended_drop
            FROM index_usage_stats
            WHERE is_recommended_drop = 1
               OR scans_since_last_vacuum = 0
            ORDER BY scans_since_last_vacuum ASC
            """
        )

    def analyze_table(self, table_name: str) -> Dict:
        """Run ANALYZE on a table to update query planner statistics."""
        try:
            self.execute(f"ANALYZE {table_name}")
            return {"status": "success", "table": table_name}
        except Exception as e:
            return {"status": "error", "table": table_name, "error": str(e)}

    def vacuum_database(self) -> Dict:
        """Run VACUUM to reclaim space and optimize database."""
        try:
            if self.dialect == "sqlite":
                self.execute("VACUUM")
            else:
                self.execute("VACUUM ANALYZE")
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
